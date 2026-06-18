"""Diagnostic: deploy the C1 teacher with the TRUE z=extrinsics (NOT phi-inferred). This is C1's upper bound.
If ~A (one-hot) -> the C1 gap is phi's INFERENCE (fixable). If still < A on BMW -> the single z-conditioned avoid
head lacks the capacity the one-hot's 3 heads had (architecture)."""
import sys, json, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
import selfid_models as M
RUN=Path('runs/feasibility_audit/phase4_f2'); VEH=["sedan","uazbus","bmw"]
C1=M.FiLMZActorCritic(); C1.load_state_dict(torch.load(RUN/'selfid_c1_teacher_policy.pt',map_location='cpu')['state_dict']); C1.eval()
avoid_all=INT._load_avoid_cells()
mus=sorted(set(round(c['mu'],3) for c in avoid_all)); pick={mus[1],mus[2]}
av_sub=[c for c in avoid_all if round(c['mu'],3) in pick]
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_sidoz_w{w}_stderr.log') for w in range(8)]
out={}
try:
    for v in VEH:
        d3v._install_vehicle(v)
        z=M.vehicle_extrinsics(v).astype(np.float32)
        pol=lambda s,obs,_z=z: C1.act(np.concatenate([np.asarray(obs,np.float32),_z]))
        specs=INT._select_specs(v, [], av_sub, n_drift=0, n_avoid=3, namespace="selfidoz")
        res=[None]*len(specs); ctr={'i':0}; lock=threading.Lock()
        def worker(wi):
            c=clients[wi]
            while True:
                with lock:
                    if ctr['i']>=len(specs): return
                    i=ctr['i']; ctr['i']+=1
                sp=specs[i]; cell=sp["cell"]
                r=f2.run_episode(c, sp["scenario"], "avoidance", pol, seed=int(sp["seed"]),
                                 mu=float(cell["mu"]), reveal=float(cell["reveal"]))
                res[i]={"s":bool(r["success"]),"rev":round(cell["reveal"],1)}
        with ThreadPoolExecutor(max_workers=8) as ex:
            for fut in [ex.submit(worker,w) for w in range(8)]: fut.result()
        av=[x["s"] for x in res if x]; byr={}
        for x in res:
            if x: byr.setdefault(x["rev"],[]).append(x["s"])
        out[v]=float(np.mean(av))
        print(f"  {v:7s} C1_oracleZ avoid={out[v]:.3f} | { {str(k):round(float(np.mean(vv)),2) for k,vv in sorted(byr.items())} }", flush=True)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(RUN/'_selfid_oraclez.json').write_text(json.dumps(out,indent=2))
print("C1_oracleZ:", out)
