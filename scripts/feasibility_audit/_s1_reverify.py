"""Independent re-verification of the S1 full-scenario driver on a SUBSET of cells (a few drift + base
avoid + 2 of the claimed missed high-mu avoid). Reuses the module's validate_per_cell + spec builders."""
import sys, json, torch
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/"src")); sys.path.insert(0,str(REPO/"scripts/feasibility_audit"))
import distill_both_fullscenario as F
import phase4_f2_train as f2
from chrono_worker_client import ChronoWorkerClient

POL=REPO/"runs/feasibility_audit/phase4_f2/distill_s1_fullscenario_policy.pt"
RUN=REPO/"runs/feasibility_audit/phase4_f2"
ck=torch.load(POL, map_location="cpu")
sd=ck["model"] if isinstance(ck,dict) and "model" in ck else (ck.get("state_dict",ck) if isinstance(ck,dict) else ck)
m=f2.AsymmetricActorCritic(gated=True); m.load_state_dict(sd); m.eval()
print("policy loaded OK")

dc=F._load_drift_cells(); ac=F._load_avoid_cells()
# subset: 3 drift cells (lo/mid/hi mu at beta 0.28/0.45) + avoid: 2 base-easy + 2 claimed-MISS high-mu
dc_sub=[c for c in dc if (c["mu"],round(c["beta"],2)) in {(0.35,0.28),(0.45,0.45),(0.55,0.36)}]
def amatch(c,r,mu): return abs(c["reveal"]-r)<0.1 and abs(c["mu"]-mu)<0.01 and not c.get("geom","").startswith(("offset","width","knife"))
ac_sub=[c for c in ac if amatch(c,9.5,0.3625) or amatch(c,12.0,0.3625)  # base easy -> should clear
        or amatch(c,30.0,1.0375) or amatch(c,22.0,0.8125)]              # claimed MISSES -> should miss
print("subset:",len(dc_sub),"drift +",len(ac_sub),"avoid")
specs=F._val_specs(dc_sub, ac_sub, n_drift=6, n_avoid=6, namespace="reverify")
clients=[ChronoWorkerClient(stderr_log=RUN/f"_s1rev_w{w}_stderr.log", read_timeout_s=600.0) for w in range(12)]
try:
    rows=F.validate_per_cell(clients, m, specs, label="REVERIFY")
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
print("\n=== RE-VERIFY per-cell ===")
for r in rows:
    print("  %-40s success=%.2f"%(r.get("cell_id",r.get("scenario_id","?")), r.get("success",-1)))
