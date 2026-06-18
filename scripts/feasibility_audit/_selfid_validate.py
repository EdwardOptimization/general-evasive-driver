"""STEP D: deploy A/B/C1/C2 on Chrono per vehicle (avoid), report success. The VoI test:
  A  one-hot (robustified capstone, oracle-ID ceiling)   B  no-ID (FiLMZ z=0, floor)
  C1 RMA (teacher FiLMZ + z_hat=phi(history), NO label)  C2 GRU (history, NO label)
Per-episode FRESH stateful deploy wrappers (thread-safe). Success judged on true Chrono physics."""
import sys, json, time, threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle_film as film
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
import selfid_models as M
RUN=Path('runs/feasibility_audit/phase4_f2'); VEH=["sedan","uazbus","bmw"]

# ---- load arms ----
def _load(path, model):
    ck=torch.load(path, map_location='cpu'); model.load_state_dict(ck['state_dict']); model.eval(); return model
A=_load(RUN/'distill_final_robustified_capstone.pt', film.FiLMAvoidActorCritic(obs_dim=75))
B=_load(RUN/'selfid_b_noid_policy.pt', M.FiLMZActorCritic())
C1=_load(RUN/'selfid_c1_teacher_policy.pt', M.FiLMZActorCritic())
PHI=M.AdaptationMLP(); PHI.load_state_dict(torch.load(RUN/'selfid_c1_phi.pt',map_location='cpu')['state_dict']); PHI.eval()
C2=_load(RUN/'selfid_c2_gru_policy.pt', M.GRUSelfIDActorCritic())
W=M.AdaptationMLP().window

# ---- per-episode deploy wrappers (built fresh per episode) ----
def make_A(vehicle):
    return INT._cond_policy(A, vehicle)               # one-hot handed
def make_B(vehicle):
    z0=np.zeros(M.Z_DIM,np.float32)
    return lambda s,obs: B.act(np.concatenate([np.asarray(obs,np.float32), z0]))
class C1Deploy:
    def __init__(self): self.hist=deque(maxlen=W); self.prev=np.zeros(3,np.float32)
    def __call__(self, s, obs):
        obs=np.asarray(obs,np.float32); self.hist.append(np.concatenate([obs,self.prev]))
        win=list(self.hist); pad=W-len(win)
        flat=np.concatenate(([np.zeros(75,np.float32)]*pad)+win).astype(np.float32) if pad>0 else np.concatenate(win).astype(np.float32)
        with torch.no_grad(): zhat=PHI(torch.tensor(flat).unsqueeze(0)).numpy()[0]
        a=C1.act(np.concatenate([obs, zhat.astype(np.float32)])); self.prev=a; return a
class C2Deploy:
    def __init__(self): self.h=None; self.prev=np.zeros(3,np.float32)
    def __call__(self, s, obs):
        obs=np.asarray(obs,np.float32); a,self.h=C2.act_step(np.concatenate([obs,self.prev]), self.h); self.prev=a; return a

ARMS={"A_onehot":("stateless",make_A), "B_noID":("stateless",make_B),
      "C1_RMA":("perep",lambda v: C1Deploy()), "C2_GRU":("perep",lambda v: C2Deploy())}

# ---- avoid cell set: 12 cells (mid + low mu) x reveals, n=3 ----
avoid_all=INT._load_avoid_cells()
mus=sorted(set(round(c['mu'],3) for c in avoid_all)); pick_mus={mus[1],mus[2]}  # two representative mus
av_sub=[c for c in avoid_all if round(c['mu'],3) in pick_mus]
print(f"avoid cells: {len(av_sub)} ({sorted(set((round(c['reveal'],1)) for c in av_sub))} reveals x {len(pick_mus)} mus), n=3", flush=True)

def eval_arm(clients, vehicle, arm_name, kind, builder, specs):
    res=[None]*len(specs); nxt=0; lock=threading.Lock()
    shared = builder(vehicle) if kind=="stateless" else None
    def worker(wi):
        nonlocal nxt; c=clients[wi]
        while True:
            with lock:
                if nxt>=len(specs): return
                i=nxt; nxt+=1
            sp=specs[i]; cell=sp["cell"]
            pol = shared if kind=="stateless" else builder(vehicle)
            r=f2.run_episode(c, sp["scenario"], "avoidance", pol, seed=int(sp["seed"]),
                             mu=float(cell["mu"]), reveal=float(cell["reveal"]))
            res[i]={"s":bool(r["success"]),"rev":round(cell["reveal"],1)}
    with ThreadPoolExecutor(max_workers=len(clients)) as ex:
        for fut in [ex.submit(worker,w) for w in range(len(clients))]: fut.result()
    av=[x["s"] for x in res if x]; byr={}
    for x in res:
        if x: byr.setdefault(x["rev"],[]).append(x["s"])
    return float(np.mean(av)), {str(k):round(float(np.mean(v)),2) for k,v in sorted(byr.items())}

clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_sidv_w{w}_stderr.log') for w in range(8)]
out={}
t0=time.time()
try:
    for v in VEH:
        d3v._install_vehicle(v)
        specs=INT._select_specs(v, [], av_sub, n_drift=0, n_avoid=3, namespace="selfidval")
        out[v]={}
        for arm,(kind,builder) in ARMS.items():
            mean,byr=eval_arm(clients, v, arm, kind, builder, specs)
            out[v][arm]=mean
            print(f"  {v:7s} {arm:9s} avoid={mean:.3f}  | {byr}", flush=True)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(RUN/'_selfid_validate.json').write_text(json.dumps(out,indent=2))
print(f"\n================ SELF-ID VoI RESULT (avoid; {time.time()-t0:.0f}s) ================")
print(f"{'vehicle':8s} {'A_onehot':>9s} {'B_noID':>8s} {'C1_RMA':>8s} {'C2_GRU':>8s}")
for v in VEH:
    o=out[v]; print(f"{v:8s} {o['A_onehot']:9.3f} {o['B_noID']:8.3f} {o['C1_RMA']:8.3f} {o['C2_GRU']:8.3f}")
print("\nVoI prediction: C1,C2 (no label) ~ A (oracle label) >> B (no ID).")
