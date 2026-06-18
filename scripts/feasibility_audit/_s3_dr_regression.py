"""Regression check: the perception-DR Sedan head must NOT have traded clean full-spectrum Sedan avoid.
Re-validate Sedan avoid on the FULL 36-cell avoid catalog (CLEAN sensing) with the robustified policy."""
import sys, json, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle_film as film
import distill_both_3vehicle as d3v
from pathlib import Path
RUN=Path('runs/feasibility_audit/phase4_f2')
ck=torch.load(RUN/'distill_final_perceptionDR_policy.pt', map_location='cpu')
m=film.FiLMAvoidActorCritic(obs_dim=75); m.load_state_dict(ck['state_dict']); m.eval()
avoid_all=INT._load_avoid_cells()
d3v._install_vehicle("sedan")
specs=INT._select_specs("sedan", [], avoid_all, n_drift=0, n_avoid=3, namespace="s3drreg")
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_s3drreg_w{w}_stderr.log') for w in range(8)]
try:
    rows=INT._eval_cells(clients, m, "sedan", specs, label="DRreg-clean-avoid")
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
av=[r for r in rows if r["regime"]=="avoidance"]
ncells=len(av); nclear=sum(1 for r in av if r["success"]>=0.999)
mean=sum(r["success"] for r in av)/max(1,len(av))
print(f"\n=== Sedan CLEAN full-spectrum avoid (perception-DR head) ===")
print(f"  cells fully cleared: {nclear}/{ncells}   mean success: {mean:.3f}   (capstone was 34/36 = 0.896 mean ~0.94 per-cell)")
miss=[(r['cell_id'],round(r['reveal'],1),round(r['mu'],2),round(r['success'],2)) for r in av if r['success']<0.999]
print("  non-perfect cells:", miss)
Path(RUN/'_s3_dr_regression.json').write_text(json.dumps({"n_cells":ncells,"n_cleared":nclear,"mean":mean,"misses":miss},indent=2))
