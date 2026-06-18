"""Independently re-verify the round-1 RMA self-ID driver (selfid_rma_round1.pt) on the FULL 36-cell avoid set,
n=5 seeds, per vehicle. Deploy phi-z_hat (NO label) AND true-z. Confirms the 1.0 is robust, not a 19-cell fluke."""
import sys, json, threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
import selfid_models as M
RUN=Path('runs/feasibility_audit/phase4_f2'); VEH=["sedan","uazbus","bmw"]; W=M.AdaptationMLP().window; ZD=M.RICH_Z
ck=torch.load(RUN/'selfid_rma_round1.pt', map_location='cpu')
enc=M.ExtrinsicsEncoder(z_dim=ZD); enc.load_state_dict(ck['enc']); enc.eval()
film=M.FiLMZActorCritic(z_dim=ZD); film.load_state_dict(ck['film']); film.eval()
phi=M.AdaptationMLP(z_dim=ZD); phi.load_state_dict(ck['phi']); phi.eval()
avoid_all=INT._load_avoid_cells()
class PhiDep:
    def __init__(self): self.hist=deque(maxlen=W); self.prev=np.zeros(3,np.float32)
    def __call__(self,s,obs):
        obs=np.asarray(obs,np.float32); self.hist.append(np.concatenate([obs,self.prev]))
        win=list(self.hist); pad=W-len(win)
        flat=np.concatenate(([np.zeros(75,np.float32)]*pad)+win) if pad>0 else np.concatenate(win)
        with torch.no_grad(): zh=phi(torch.tensor(flat.astype(np.float32)).unsqueeze(0)).numpy()[0]
        a=film.act(np.concatenate([obs,zh.astype(np.float32)])); self.prev=a; return a
def truez(v):
    with torch.no_grad(): z=enc(torch.tensor(M.vehicle_extrinsics(v)).unsqueeze(0)).numpy()[0].astype(np.float32)
    return lambda s,obs,_z=z: film.act(np.concatenate([np.asarray(obs,np.float32),_z]))
def evalv(clients, v, builder, kind):
    specs=INT._select_specs(v, [], avoid_all, n_drift=0, n_avoid=5, namespace="rmarev")
    res=[None]*len(specs); ctr={'i':0}; lock=threading.Lock()
    shared=builder(v) if kind=="stateless" else None
    def worker(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(specs): return
                i=ctr['i']; ctr['i']+=1
            sp=specs[i]; cell=sp["cell"]; pol=shared if kind=="stateless" else builder(v)
            r=f2.run_episode(c, sp["scenario"],"avoidance",pol,seed=int(sp["seed"]),mu=float(cell["mu"]),reveal=float(cell["reveal"]))
            res[i]=bool(r["success"])
    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in [ex.submit(worker,w) for w in range(8)]: fut.result()
    vals=[x for x in res if x is not None]
    return float(np.mean(vals)), sum(vals), len(vals)
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_rmarev_w{w}_stderr.log') for w in range(8)]
out={}
try:
    for v in VEH:
        d3v._install_vehicle(v)
        pm,ps,pn=evalv(clients,v,lambda vv:PhiDep(),"perep")
        tm,ts,tn=evalv(clients,v,truez,"stateless")
        out[v]={"phi":pm,"phi_n":f"{ps}/{pn}","truez":tm,"truez_n":f"{ts}/{tn}"}
        print(f"  {v:7s} phi-z avoid={pm:.3f} ({ps}/{pn})   true-z avoid={tm:.3f} ({ts}/{tn})", flush=True)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(RUN/'_selfid_rma_reverify.json').write_text(json.dumps(out,indent=2))
print("\n=== RMA round-1 re-verify (full 36 cells x5, NO label = phi-z) ===")
print(f"  phi-z mean={np.mean([out[v]['phi'] for v in VEH]):.3f}   true-z mean={np.mean([out[v]['truez'] for v in VEH]):.3f}")
