"""Rigorous verify of the full-scenario label-free self-ID driver (selfid_fullscenario.pt): FULL feasible drift
cells + ALL 36 avoid cells, n=5 seeds, per vehicle, phi-z (NO label). Honest robust drift+avoid numbers."""
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
pv=json.load(open('runs/feasibility_audit/spectrum_s1/feasibility_precheck_per_vehicle.json'))
ck=torch.load(RUN/'selfid_fullscenario.pt', map_location='cpu')
enc=M.ExtrinsicsEncoder(z_dim=ZD); enc.load_state_dict(ck['enc']); enc.eval()
film=M.FiLMZActorCritic(z_dim=ZD); film.load_state_dict(ck['film']); film.eval()
phi=M.AdaptationMLP(z_dim=ZD); phi.load_state_dict(ck['phi']); phi.eval()
class PhiDep:
    def __init__(self): self.hist=deque(maxlen=W); self.prev=np.zeros(3,np.float32)
    def __call__(self,s,obs):
        obs=np.asarray(obs,np.float32); self.hist.append(np.concatenate([obs,self.prev]))
        win=list(self.hist); pad=W-len(win)
        flat=np.concatenate(([np.zeros(75,np.float32)]*pad)+win) if pad>0 else np.concatenate(win)
        with torch.no_grad(): zh=phi(torch.tensor(flat.astype(np.float32)).unsqueeze(0)).numpy()[0]
        a=film.act(np.concatenate([obs,zh.astype(np.float32)])); self.prev=a; return a
def evalset(clients, specs, regime):
    res=[None]*len(specs); ctr={'i':0}; lock=threading.Lock()
    def worker(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(specs): return
                i=ctr['i']; ctr['i']+=1
            sp=specs[i]; cell=sp["cell"]; pol=PhiDep()
            rv = 0.0 if regime=="drift" else cell["reveal"]
            r=f2.run_episode(c,sp["scenario"],regime,pol,seed=int(sp["seed"]),mu=float(cell["mu"]),reveal=float(rv))
            res[i]=bool(r["success"])
    with ThreadPoolExecutor(max_workers=8) as ex:
        for fut in [ex.submit(worker,w) for w in range(8)]: fut.result()
    vals=[x for x in res if x is not None]; return float(np.mean(vals)), sum(vals), len(vals)
avoid_all=INT._load_avoid_cells()
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_fsv_w{w}_stderr.log') for w in range(8)]
out={}
try:
    for v in VEH:
        d3v._install_vehicle(v)
        dcells=INT._vehicle_drift_cells(v,pv)
        dspecs=[{"cell":c,"seed":int(f2._seed_for("fsverD",v,"drift",ci,i,round(c["mu"],3),round(c["beta"],3))),
                 "scenario":INT._drift_scenario(v,c,int(f2._seed_for("fsverD",v,"drift",ci,i,round(c["mu"],3),round(c["beta"],3))))}
                for ci,c in enumerate(dcells) for i in range(5)]
        aspecs=INT._select_specs(v,[],avoid_all,n_drift=0,n_avoid=5,namespace="fsverA")
        dm,ds,dn=evalset(clients,dspecs,"drift"); am,asu,an=evalset(clients,aspecs,"avoidance")
        out[v]={"drift":dm,"drift_n":f"{ds}/{dn}","avoid":am,"avoid_n":f"{asu}/{an}"}
        print(f"  {v:7s} DRIFT={dm:.3f} ({ds}/{dn})   AVOID={am:.3f} ({asu}/{an})", flush=True)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(RUN/'_selfid_fs_verify.json').write_text(json.dumps(out,indent=2))
print(f"\n=== FULL-SCENARIO self-ID driver (NO label), full cells x5 ===")
print(f"  DRIFT mean={np.mean([out[v]['drift'] for v in VEH]):.3f}   AVOID mean={np.mean([out[v]['avoid'] for v in VEH]):.3f}")
