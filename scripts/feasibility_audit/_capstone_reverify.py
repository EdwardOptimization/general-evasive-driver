import sys, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_3vehicle_film as FILM
import distill_both_3vehicle_conditioned as cond
from chrono_worker_client import ChronoWorkerClient
from pathlib import Path
RUN=Path('runs/feasibility_audit/phase4_f2')
ck=torch.load(RUN/'distill_final_integrated_policy.pt', map_location='cpu')
sd = ck['model'] if isinstance(ck,dict) and 'model' in ck else (ck.get('state_dict',ck) if isinstance(ck,dict) else ck)
m=FILM.FiLMAvoidActorCritic(obs_dim=75); m.load_state_dict(sd); m.eval()
print('FiLM policy loaded; obs_dim=75')
clients=[ChronoWorkerClient(stderr_log=RUN/f'_cap_rev_w{w}_stderr.log', read_timeout_s=600.0) for w in range(12)]
try:
    res=cond._validate_per_vehicle(clients, m, avoid_units=14, drift_units=8)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
print('\n=== RE-VERIFY CAPSTONE driver per-(vehicle,regime) ===')
for v,d in res.items():
    print('  %-8s drift=%.3f  avoid=%.3f'%(v, d.get('drift',-1), d.get('avoid',-1)))
