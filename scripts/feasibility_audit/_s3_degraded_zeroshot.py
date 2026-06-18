"""S3 STEP 1 (build+measure, NOT assume): zero-shot sensing degradation on the VERIFIED capstone driver.
Degrades obs ego-response channels 0-8 (delay + iid Gaussian noise) EXACTLY like
ObservationDegradationWrapper, but client-side on the policy's VIEW only (success judged on TRUE physics).
Per-episode fresh DegradingView => thread-safe + seeded from the episode seed."""
import sys, json, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle_film as film
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
from autodrift.observation_degradation_wrapper import DEFAULT_NOISE_SEED_STREAM
RUN=Path('runs/feasibility_audit/phase4_f2')

# ---- load capstone ----
ck=torch.load(RUN/'distill_final_integrated_policy.pt', map_location='cpu')
sd = ck['state_dict'] if isinstance(ck,dict) and 'state_dict' in ck else (ck.get('model',ck) if isinstance(ck,dict) else ck)
model=film.FiLMAvoidActorCritic(obs_dim=75); model.load_state_dict(sd); model.eval()
pv=json.load(open('runs/feasibility_audit/spectrum_s1/feasibility_precheck_per_vehicle.json'))

class DegradingView:
    """Per-episode degrading view of obs[0:9]: delay_steps + iid Gaussian noise (normalized units)."""
    def __init__(self, base, *, delay_steps, noise_std, seed):
        self.base=base; self.delay=int(delay_steps); self.noise=float(noise_std)
        self.rng=np.random.default_rng([DEFAULT_NOISE_SEED_STREAM, int(seed), 0]); self.raw=[]
    def __call__(self, step, obs):
        obs=np.asarray(obs, np.float32).copy()
        self.raw.append(obs[:9].astype(np.float64).copy())
        di=max(len(self.raw)-1-self.delay, 0)
        n=self.rng.normal(0.0,1.0,9)*self.noise if self.noise>0 else 0.0
        obs[:9]=(self.raw[di]+n).astype(np.float32)
        return self.base(step, obs)

def eval_degraded(clients, model, vehicle, specs, deg, label):
    results=[None]*len(specs); nW=min(len(clients),len(specs)) if specs else 0
    nxt=0; lock=threading.Lock()
    def worker(wi):
        nonlocal nxt; client=clients[wi]
        while True:
            with lock:
                if nxt>=len(specs): return
                i=nxt; nxt+=1
            sp=specs[i]; cell=sp["cell"]
            reveal,mu=(0.0,cell["mu"]) if sp["regime"]=="drift" else (cell["reveal"],cell["mu"])
            base=INT._cond_policy(model, vehicle)
            pol=DegradingView(base, delay_steps=deg["delay"], noise_std=deg["noise"], seed=int(sp["seed"]))
            res=f2.run_episode(client, sp["scenario"], sp["regime"], pol,
                               seed=int(sp["seed"]), mu=float(mu), reveal=float(reveal))
            results[i]={"success":bool(res["success"]),"regime":sp["regime"],
                        "sustain":int(res["longest_controlled_drift_run"]),"collision":bool(res["collision"])}
    t0=time.time()
    if nW>0:
        with ThreadPoolExecutor(max_workers=nW) as ex:
            for fut in [ex.submit(worker,w) for w in range(nW)]: fut.result()
    dr=[r["success"] for r in results if r and r["regime"]=="drift"]
    av=[r["success"] for r in results if r and r["regime"]=="avoidance"]
    avc=[r["collision"] for r in results if r and r["regime"]=="avoidance"]
    print(f"  [{label}] {len(specs)}ep {time.time()-t0:.0f}s  drift={np.mean(dr) if dr else float('nan'):.3f}({sum(dr)}/{len(dr)})  "
          f"avoid={np.mean(av) if av else float('nan'):.3f}({sum(av)}/{len(av)})  coll={np.mean(avc) if avc else 0:.2f}", flush=True)
    return {"drift":float(np.mean(dr)) if dr else None,"avoid":float(np.mean(av)) if av else None,
            "n_drift":len(dr),"n_avoid":len(av),"avoid_collision":float(np.mean(avc)) if avc else None}

# ---- representative grid ----
avoid_all=INT._load_avoid_cells()
print(f"avoid catalog: {len(avoid_all)} cells; reveals={sorted(set(round(c['reveal'],1) for c in avoid_all))}", flush=True)
# pick a representative avoid subset spanning reveal (hard small reveal -> easy large reveal) at mid mu.
# per reveal, take the cell whose mu is CLOSEST to the catalog median raw mu (avoids round-mismatch).
allmu=sorted(c['mu'] for c in avoid_all); midmu=allmu[len(allmu)//2]
av_sub=[]
for rv in sorted(set(c['reveal'] for c in avoid_all)):
    cs=[c for c in avoid_all if abs(c['reveal']-rv)<1e-6]
    if cs: av_sub.append(min(cs, key=lambda c: abs(c['mu']-midmu)))
av_sub=av_sub[:5]
print(f"avoid subset: {[(round(c['reveal'],1),round(c['mu'],2)) for c in av_sub]}", flush=True)

LADDER=[{"name":"T1_clean","delay":0,"noise":0.0},
        {"name":"T3_moderate","delay":2,"noise":0.03},
        {"name":"T4_harsh","delay":4,"noise":0.06}]
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_s3_w{w}_stderr.log') for w in range(8)]
out={}
try:
    for v in INT.VEHICLES:
        d3v._install_vehicle(v)
        dcells=INT._vehicle_drift_cells(v, pv)[:4]
        specs=INT._select_specs(v, dcells, av_sub, n_drift=3, n_avoid=2, namespace="s3deg")
        print(f"\n=== {v}: {len(dcells)} drift + {len(av_sub)} avoid cells, {len(specs)} ep/rung ===", flush=True)
        out[v]={}
        for rung in LADDER:
            out[v][rung["name"]]=eval_degraded(clients, model, v, specs, rung, f"{v}/{rung['name']}")
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(RUN/'_s3_degraded_zeroshot.json').write_text(json.dumps(out,indent=2))
print("\n=== S3 ZERO-SHOT DEGRADATION SUMMARY (capstone, no retrain) ===")
print(f"{'vehicle':8s} {'rung':12s} {'drift':>7s} {'avoid':>7s} {'coll':>6s}")
for v in INT.VEHICLES:
    for rn,r in out[v].items():
        print(f"{v:8s} {rn:12s} {(r['drift'] if r['drift'] is not None else -1):7.3f} "
              f"{(r['avoid'] if r['avoid'] is not None else -1):7.3f} {(r['avoid_collision'] or 0):6.2f}")
