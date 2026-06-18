"""Fix the fragile z-conditioning: retrain the C1 teacher with Z-JITTER (Gaussian noise on z per frame,
matching phi's inference error band) so the policy is ROBUST to the z_hat band phi produces (the project's own
DR philosophy applied to the conditioning variable). Then re-validate C1 with BOTH phi-inferred z_hat AND true z."""
import sys, json, time, threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
import selfid_models as M
RUN=Path('runs/feasibility_audit/phase4_f2'); SEQ=RUN/'selfid_avoid_seqs'; VEH=["sedan","uazbus","bmw"]
W=M.AdaptationMLP().window
JITTER=0.12   # z-jitter std (~ phi's per-dim error band)

def load():
    eps=[]
    for v in VEH:
        d=np.load(SEQ/f'avoid_{v}.npz', allow_pickle=True)
        for obs,act,succ in zip(d["obs"],d["act"],d["success"]):
            obs=np.asarray(obs,np.float32); act=np.asarray(act,np.float32)
            if obs.shape[0]>=2 and bool(succ): eps.append((obs,act,v))
    return eps

eps=load()
# frame pool with per-frame z (jittered each minibatch draw)
OBS=[]; ACT=[]; Zc=[]
for obs,act,v in eps:
    OBS.append(obs); ACT.append(act); Zc.append(np.tile(M.vehicle_extrinsics(v),(obs.shape[0],1)))
OBS=torch.tensor(np.concatenate(OBS,0)); ACT=torch.tensor(np.concatenate(ACT,0)); Zc=torch.tensor(np.concatenate(Zc,0).astype(np.float32))
N=OBS.shape[0]
m=M.FiLMZActorCritic(); opt=torch.optim.Adam(m.parameters(), lr=1e-3); t0=time.time(); m.train()
print(f"z-jitter teacher BC: {N} frames, jitter_std={JITTER}", flush=True)
for ep in range(1200):
    idx=torch.randint(0,N,(512,))
    zj = Zc[idx] + JITTER*torch.randn(512, M.Z_DIM)     # JITTER the conditioning z each draw
    X=torch.cat([OBS[idx], zj], 1)
    loss=((m.actor_forward(X)-ACT[idx])**2).mean()
    opt.zero_grad(); loss.backward(); opt.step()
    if ep%300==0 or ep==1199: print(f"  ep {ep:4d} bc_mse={loss.item():.4e} ({time.time()-t0:.0f}s)", flush=True)
m.eval(); torch.save({"state_dict":m.state_dict()}, RUN/'selfid_c1_teacher_jitter_policy.pt')

# --- re-validate: C1-phi (jitter teacher + existing phi) and C1-truez (jitter teacher + true z) ---
PHI=M.AdaptationMLP(); PHI.load_state_dict(torch.load(RUN/'selfid_c1_phi.pt',map_location='cpu')['state_dict']); PHI.eval()
avoid_all=INT._load_avoid_cells(); mus=sorted(set(round(c['mu'],3) for c in avoid_all)); pick={mus[1],mus[2]}
av_sub=[c for c in avoid_all if round(c['mu'],3) in pick]
class C1Phi:
    def __init__(self): self.hist=deque(maxlen=W); self.prev=np.zeros(3,np.float32)
    def __call__(self,s,obs):
        obs=np.asarray(obs,np.float32); self.hist.append(np.concatenate([obs,self.prev]))
        win=list(self.hist); pad=W-len(win)
        flat=np.concatenate(([np.zeros(75,np.float32)]*pad)+win) if pad>0 else np.concatenate(win)
        with torch.no_grad(): zhat=PHI(torch.tensor(flat.astype(np.float32)).unsqueeze(0)).numpy()[0]
        a=m.act(np.concatenate([obs,zhat.astype(np.float32)])); self.prev=a; return a
def truez(v):
    z=M.vehicle_extrinsics(v).astype(np.float32)
    return lambda s,obs,_z=z: m.act(np.concatenate([np.asarray(obs,np.float32),_z]))
def evalv(clients, vehicle, builder, kind):
    specs=INT._select_specs(vehicle, [], av_sub, n_drift=0, n_avoid=3, namespace="c1jit")
    res=[None]*len(specs); ctr={'i':0}; lock=threading.Lock()
    shared=builder(vehicle) if kind=="stateless" else None
    def worker(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(specs): return
                i=ctr['i']; ctr['i']+=1
            sp=specs[i]; cell=sp["cell"]; pol=shared if kind=="stateless" else builder(vehicle)
            r=f2.run_episode(c, sp["scenario"], "avoidance", pol, seed=int(sp["seed"]), mu=float(cell["mu"]), reveal=float(cell["reveal"]))
            res[i]=bool(r["success"])
    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in [ex.submit(worker,w) for w in range(8)]: fut.result()
    return float(np.mean([x for x in res if x is not None]))
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_c1jit_w{w}_stderr.log') for w in range(8)]
out={}
try:
    for v in VEH:
        d3v._install_vehicle(v)
        phi_s=evalv(clients, v, lambda vv: C1Phi(), "perep")
        tz_s =evalv(clients, v, truez, "stateless")
        out[v]={"C1jit_phi":phi_s, "C1jit_truez":tz_s}
        print(f"  {v:7s} C1jit_phi={phi_s:.3f}  C1jit_truez={tz_s:.3f}", flush=True)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(RUN/'_selfid_c1_jitter.json').write_text(json.dumps(out,indent=2))
print("\nz-jitter C1:", json.dumps(out))
