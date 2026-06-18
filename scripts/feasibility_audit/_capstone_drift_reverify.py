"""Close the confound: re-validate the capstone integrated policy on SEDAN SPECTRUM drift cells (v12),
not the do-both v9 cell. Reuses the integration script's own _vehicle_drift_cells + _select_specs + _eval_cells."""
import sys, json, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle_film as film
from pathlib import Path
RUN=Path('runs/feasibility_audit/phase4_f2')
ck=torch.load(RUN/'distill_final_integrated_policy.pt', map_location='cpu')
sd = ck['state_dict'] if isinstance(ck,dict) and 'state_dict' in ck else (ck.get('model',ck) if isinstance(ck,dict) else ck)
m=film.FiLMAvoidActorCritic(obs_dim=75); m.load_state_dict(sd); m.eval()
pv=json.load(open('runs/feasibility_audit/spectrum_s1/feasibility_precheck_per_vehicle.json'))
sedan_cells=INT._vehicle_drift_cells('sedan', pv)[:4]
print('sedan spectrum drift cells (v12-14):', [(round(c['mu'],2),round(c['beta'],2),c.get('speed','?')) for c in sedan_cells])
specs=INT._select_specs('sedan', sedan_cells, [], n_drift=4, n_avoid=0, namespace='capreverify')
clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_capd_w{w}_stderr.log') for w in range(8)]
try:
    rows=INT._eval_cells(clients, m, 'sedan', specs, label='reverify')
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
print('\n=== SEDAN drift on SPECTRUM cells (capstone policy) ===')
for r in rows:
    print('  mu=%.2f beta=%.2f  success=%.2f  mean_sustain=%.0f'%(r.get('mu',-1),r.get('beta',-1),r['success'],r.get('mean_sustain',0)))
