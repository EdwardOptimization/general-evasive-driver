"""S3 STEP 2: EXTEROCEPTIVE (obstacle-perception) degradation on the capstone driver — the axis that
should actually bite AVOID. Adds Gaussian noise to obstacle continuous channels (x,y,rel_vx,rel_vy),
only on PRESENT obstacles (present-bit + size untouched), client-side on the policy's VIEW. Avoid-focused."""
import sys, json, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle_film as film
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
from autodrift.observation_degradation_wrapper import DEFAULT_NOISE_SEED_STREAM, GEOMETRY_NOISE_SEED_SUBSTREAM
RUN=Path('runs/feasibility_audit/phase4_f2')
OBST_PRESENT=[44,51,58,65]
OBST_CONT=[45,46,47,48, 52,53,54,55, 59,60,61,62, 66,67,68,69]

ck=torch.load(RUN/'distill_final_integrated_policy.pt', map_location='cpu')
sd = ck['state_dict'] if isinstance(ck,dict) and 'state_dict' in ck else (ck.get('model',ck) if isinstance(ck,dict) else ck)
model=film.FiLMAvoidActorCritic(obs_dim=75); model.load_state_dict(sd); model.eval()
pv=json.load(open('runs/feasibility_audit/spectrum_s1/feasibility_precheck_per_vehicle.json'))

class PerceptionDegradingView:
    """Per-episode obstacle-perception degrader: iid Gaussian on present-obstacle continuous channels."""
    def __init__(self, base, *, geom_noise, seed):
        self.base=base; self.gn=float(geom_noise)
        self.rng=np.random.default_rng([DEFAULT_NOISE_SEED_STREAM,int(seed),0,GEOMETRY_NOISE_SEED_SUBSTREAM])
        self.cont=np.array(OBST_CONT); self.present=OBST_PRESENT
    def __call__(self, step, obs):
        obs=np.asarray(obs,np.float32).copy()
        if self.gn>0:
            noise=self.rng.normal(0.0,self.gn,len(self.cont)).astype(np.float32)
            # zero the noise for absent obstacle slots (present bit <= 0.5)
            for si,pb in enumerate(self.present):
                if obs[pb]<=0.5: noise[si*4:si*4+4]=0.0
            obs[self.cont]+=noise
        return self.base(step, obs)

def eval_perc(clients, model, vehicle, specs, gn, label):
    results=[None]*len(specs); nW=min(len(clients),len(specs)) if specs else 0
    nxt=0; lock=threading.Lock()
    def worker(wi):
        nonlocal nxt; client=clients[wi]
        while True:
            with lock:
                if nxt>=len(specs): return
                i=nxt; nxt+=1
            sp=specs[i]; cell=sp["cell"]; reveal,mu=cell["reveal"],cell["mu"]
            base=INT._cond_policy(model, vehicle)
            pol=PerceptionDegradingView(base, geom_noise=gn, seed=int(sp["seed"]))
            res=f2.run_episode(client, sp["scenario"], "avoidance", pol,
                               seed=int(sp["seed"]), mu=float(mu), reveal=float(reveal))
            results[i]={"success":bool(res["success"]),"collision":bool(res["collision"]),
                        "reveal":reveal,"mu":mu}
    t0=time.time()
    if nW>0:
        with ThreadPoolExecutor(max_workers=nW) as ex:
            for fut in [ex.submit(worker,w) for w in range(nW)]: fut.result()
    av=[r["success"] for r in results if r]; coll=[r["collision"] for r in results if r]
    # per-reveal breakdown
    byrev={}
    for r in results:
        if r: byrev.setdefault(round(r["reveal"],1),[]).append(r["success"])
    brk=" ".join(f"r{k}={np.mean(v):.2f}" for k,v in sorted(byrev.items()))
    print(f"  [{label}] {len(specs)}ep {time.time()-t0:.0f}s  avoid={np.mean(av):.3f}({sum(av)}/{len(av)})  "
          f"coll={np.mean(coll):.2f}  | {brk}", flush=True)
    return {"avoid":float(np.mean(av)),"collision":float(np.mean(coll)),"n":len(av),"by_reveal":{str(k):float(np.mean(v)) for k,v in byrev.items()}}

avoid_all=INT._load_avoid_cells()
allmu=sorted(c['mu'] for c in avoid_all); midmu=allmu[len(allmu)//2]
# one cell per reveal at mid mu (6 cells), n=4 seeds
av_sub=[]
for rv in sorted(set(c['reveal'] for c in avoid_all)):
    cs=[c for c in avoid_all if abs(c['reveal']-rv)<1e-6]
    if cs: av_sub.append(min(cs, key=lambda c: abs(c['mu']-midmu)))
print(f"avoid cells (mid-mu {midmu:.3f}): {[(round(c['reveal'],1),round(c['mu'],2)) for c in av_sub]}", flush=True)

LADDER=[("P1_clean",0.0),("P2_mild",0.02),("P3_moderate",0.04),("P4_harsh",0.08)]
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_s3p_w{w}_stderr.log') for w in range(8)]
out={}
try:
    for v in INT.VEHICLES:
        d3v._install_vehicle(v)
        specs=INT._select_specs(v, [], av_sub, n_drift=0, n_avoid=4, namespace="s3perc")
        print(f"\n=== {v}: {len(av_sub)} avoid cells x4 = {len(specs)} ep/rung ===", flush=True)
        out[v]={}
        for name,gn in LADDER:
            out[v][name]=eval_perc(clients, model, v, specs, gn, f"{v}/{name}(gn={gn})")
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(RUN/'_s3_perception.json').write_text(json.dumps(out,indent=2))
print("\n=== S3 PERCEPTION-DEGRADATION SUMMARY (avoid; capstone, no retrain) ===")
print(f"{'vehicle':8s} {'P1_clean':>9s} {'P2_mild':>9s} {'P3_mod':>9s} {'P4_harsh':>9s}")
for v in INT.VEHICLES:
    r=out[v]
    print(f"{v:8s} {r['P1_clean']['avoid']:9.3f} {r['P2_mild']['avoid']:9.3f} {r['P3_moderate']['avoid']:9.3f} {r['P4_harsh']['avoid']:9.3f}")
