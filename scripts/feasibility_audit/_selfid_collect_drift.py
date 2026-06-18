"""Collect DRIFT oracle demos as per-episode SEQUENCES on Chrono, per vehicle (feasible drift cells).
Mirrors _selfid_collect.py but drift: cells=_vehicle_drift_cells, scenario=_drift_scenario, oracle=_drift_teacher."""
import sys, json, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
RUN=Path('runs/feasibility_audit/phase4_f2'); OUT=RUN/'selfid_drift_seqs'; OUT.mkdir(exist_ok=True)
N_SEED=4
pv=json.load(open('runs/feasibility_audit/spectrum_s1/feasibility_precheck_per_vehicle.json'))

def collect_vehicle(clients, v):
    d3v._install_vehicle(v)
    cells=INT._vehicle_drift_cells(v, pv)
    specs=[]
    for ci,cell in enumerate(cells):
        for i in range(N_SEED):
            seed=int(f2._seed_for("selfiddrift", v, "drift", ci, i, round(cell["mu"],3), round(cell["beta"],3)))
            specs.append({"cell":cell, "seed":seed, "scenario":INT._drift_scenario(v, cell, seed)})
    eps=[None]*len(specs); nxt=0; lock=threading.Lock()
    def worker(wi):
        nonlocal nxt; c=clients[wi]
        while True:
            with lock:
                if nxt>=len(specs): return
                i=nxt; nxt+=1
            sp=specs[i]; cell=sp["cell"]
            oracle=INT._drift_teacher(cell)
            res=f2.run_episode(c, sp["scenario"], "drift", oracle, seed=int(sp["seed"]),
                               mu=float(cell["mu"]), reveal=0.0, collect="bc")
            obs=np.asarray(res.get("bc_frames"),np.float32); act=np.asarray(res.get("bc_targets"),np.float32)
            eps[i]={"obs":obs,"act":act,"mu":float(cell["mu"]),"beta":float(cell["beta"]),
                    "success":bool(res["success"]),"sustain":int(res["longest_controlled_drift_run"]),"T":int(obs.shape[0])}
    with ThreadPoolExecutor(max_workers=len(clients)) as ex:
        for fut in [ex.submit(worker,w) for w in range(len(clients))]: fut.result()
    return [e for e in eps if e and e["T"]>0]

clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_sidd_w{w}_stderr.log') for w in range(8)]
meta={}; t0=time.time()
try:
    for v in INT.VEHICLES:
        eps=collect_vehicle(clients, v)
        np.savez(OUT/f'drift_{v}.npz',
                 obs=np.array([e["obs"] for e in eps],dtype=object), act=np.array([e["act"] for e in eps],dtype=object),
                 mu=np.array([e["mu"] for e in eps],np.float32), beta=np.array([e["beta"] for e in eps],np.float32),
                 success=np.array([e["success"] for e in eps],bool), sustain=np.array([e["sustain"] for e in eps],np.int32),
                 allow_pickle=True)
        succ=float(np.mean([e["success"] for e in eps])) if eps else 0.0
        meta[v]={"episodes":len(eps),"frames":int(sum(e["T"] for e in eps)),"oracle_success":succ,"cells":len(INT._vehicle_drift_cells(v,pv))}
        print(f"  {v}: {len(eps)} drift episodes ({meta[v]['cells']} cells), {meta[v]['frames']} frames, oracle_success={succ:.3f}", flush=True)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(OUT/'meta.json').write_text(json.dumps(meta,indent=2))
print(f"DONE {time.time()-t0:.0f}s. {json.dumps(meta)}")
