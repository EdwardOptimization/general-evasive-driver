"""STEP A: collect AVOID oracle demos as PER-EPISODE SEQUENCES on Chrono (the faithful arbiter), per vehicle.
Each episode -> (obs72[T], oracle_action[T]); kept as sequences (not pooled) so the GRU/adaptation history
window is available. run_episode(collect='bc') with the avoid oracle driving returns exactly these per step."""
import sys, json, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
RUN=Path('runs/feasibility_audit/phase4_f2'); OUT=RUN/'selfid_avoid_seqs'
OUT.mkdir(exist_ok=True)
N_SEED=3
avoid_all=INT._load_avoid_cells()

def collect_vehicle(clients, vehicle):
    d3v._install_vehicle(vehicle)
    specs=INT._select_specs(vehicle, [], avoid_all, n_drift=0, n_avoid=N_SEED, namespace="selfidseq")
    eps=[None]*len(specs); nxt=0; lock=threading.Lock()
    def worker(wi):
        nonlocal nxt; c=clients[wi]
        while True:
            with lock:
                if nxt>=len(specs): return
                i=nxt; nxt+=1
            sp=specs[i]; cell=sp["cell"]
            oracle=f2.make_avoidance_teacher(reveal=float(cell["reveal"]), mu=float(cell["mu"])).factory()
            res=f2.run_episode(c, sp["scenario"], "avoidance", oracle, seed=int(sp["seed"]),
                               mu=float(cell["mu"]), reveal=float(cell["reveal"]), collect="bc")
            obs=np.asarray(res.get("bc_frames"), np.float32)
            act=np.asarray(res.get("bc_targets"), np.float32)
            eps[i]={"obs":obs, "act":act, "reveal":float(cell["reveal"]), "mu":float(cell["mu"]),
                    "success":bool(res["success"]), "T":int(obs.shape[0])}
    with ThreadPoolExecutor(max_workers=len(clients)) as ex:
        for fut in [ex.submit(worker,w) for w in range(len(clients))]: fut.result()
    eps=[e for e in eps if e and e["T"]>0]
    return eps

clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_sidc_w{w}_stderr.log') for w in range(8)]
meta={}
t0=time.time()
try:
    for v in INT.VEHICLES:
        tv=time.time()
        eps=collect_vehicle(clients, v)
        # save as object array of variable-length sequences
        np.savez(OUT/f'avoid_{v}.npz',
                 obs=np.array([e["obs"] for e in eps], dtype=object),
                 act=np.array([e["act"] for e in eps], dtype=object),
                 reveal=np.array([e["reveal"] for e in eps], np.float32),
                 mu=np.array([e["mu"] for e in eps], np.float32),
                 success=np.array([e["success"] for e in eps], bool),
                 allow_pickle=True)
        succ=float(np.mean([e["success"] for e in eps])) if eps else 0.0
        tot_frames=int(sum(e["T"] for e in eps))
        meta[v]={"episodes":len(eps),"frames":tot_frames,"oracle_success":succ,"mean_T":tot_frames/max(1,len(eps))}
        print(f"  {v}: {len(eps)} episodes, {tot_frames} frames, oracle_success={succ:.3f}, mean_T={meta[v]['mean_T']:.0f} ({time.time()-tv:.0f}s)", flush=True)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
Path(OUT/'meta.json').write_text(json.dumps(meta,indent=2))
print(f"\nDONE collect in {time.time()-t0:.0f}s. meta={json.dumps(meta)}")
