"""FINAL CERTIFICATION of the robustified capstone (the strongest most general driver).
Pre-registered full feasible grid x 3 vehicles, n=5 seeds/cell, CLEAN sensing. Per vehicle x regime:
mean success + seed-CLUSTERED 95% CI (cells are the resampling unit; bootstrap 4000x). Drift sustain reported too."""
import sys, json, time
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle_film as film
import distill_both_3vehicle as d3v
RUN=Path('runs/feasibility_audit/phase4_f2')
N_SEED=5; N_BOOT=4000
ck=torch.load(RUN/'distill_final_robustified_capstone.pt', map_location='cpu')
m=film.FiLMAvoidActorCritic(obs_dim=75); m.load_state_dict(ck['state_dict']); m.eval()
pv=json.load(open('runs/feasibility_audit/spectrum_s1/feasibility_precheck_per_vehicle.json'))
avoid_all=INT._load_avoid_cells()

def cluster_ci(cell_rates, rng):
    """Cluster bootstrap over cells: resample cells w/ replacement, mean of per-cell success."""
    cr=np.asarray(cell_rates,float)
    if len(cr)==0: return (float('nan'),float('nan'),float('nan'))
    boots=np.array([cr[rng.integers(0,len(cr),len(cr))].mean() for _ in range(N_BOOT)])
    return float(cr.mean()), float(np.percentile(boots,2.5)), float(np.percentile(boots,97.5))

clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_cert_w{w}_stderr.log') for w in range(8)]
rng=np.random.default_rng([12345,1])
cert={}
t0=time.time()
try:
    for v in INT.VEHICLES:
        d3v._install_vehicle(v)
        dcells=INT._vehicle_drift_cells(v, pv)
        specs=INT._select_specs(v, dcells, avoid_all, n_drift=N_SEED, n_avoid=N_SEED, namespace="cert")
        print(f"\n=== CERT {v}: {len(dcells)} drift + {len(avoid_all)} avoid cells x{N_SEED} = {len(specs)} ep ===", flush=True)
        rows=INT._eval_cells(clients, m, v, specs, label=f"CERT[{v}]")
        dr=[r for r in rows if r["regime"]=="drift"]; av=[r for r in rows if r["regime"]=="avoidance"]
        dmean,dlo,dhi=cluster_ci([r["success"] for r in dr], rng)
        amean,alo,ahi=cluster_ci([r["success"] for r in av], rng)
        sust=[r.get("mean_sustain",0) for r in dr if r["success"]>0]
        cert[v]={"drift":{"cells":len(dr),"cleared":sum(1 for r in dr if r["success"]>=0.999),"mean":dmean,"ci":[dlo,dhi],
                          "mean_sustain":float(np.mean(sust)) if sust else 0.0},
                 "avoid":{"cells":len(av),"cleared":sum(1 for r in av if r["success"]>=0.999),"mean":amean,"ci":[alo,ahi]}}
        print(f"  {v}: drift {cert[v]['drift']['cleared']}/{len(dr)} mean={dmean:.3f} CI[{dlo:.3f},{dhi:.3f}] sustain={cert[v]['drift']['mean_sustain']:.0f}  | "
              f"avoid {cert[v]['avoid']['cleared']}/{len(av)} mean={amean:.3f} CI[{alo:.3f},{ahi:.3f}]", flush=True)
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
# pooled grand totals
all_dr_cells=sum(cert[v]["drift"]["cells"] for v in cert); all_dr_clr=sum(cert[v]["drift"]["cleared"] for v in cert)
all_av_cells=sum(cert[v]["avoid"]["cells"] for v in cert); all_av_clr=sum(cert[v]["avoid"]["cleared"] for v in cert)
cert["_grand"]={"drift_cells":all_dr_cells,"drift_cleared":all_dr_clr,"avoid_cells":all_av_cells,"avoid_cleared":all_av_clr,
                "total_cells":all_dr_cells+all_av_cells,"total_cleared":all_dr_clr+all_av_clr,
                "n_seed":N_SEED,"n_boot":N_BOOT,"wall_s":round(time.time()-t0,0)}
Path(RUN/'_s3_certification.json').write_text(json.dumps(cert,indent=2))
print("\n================= CERTIFICATION (robustified capstone, clean sensing, seed-clustered 95% CI) =================")
print(f"{'vehicle':8s} | {'DRIFT cleared':>14s}  {'mean[95%CI]':>22s} {'sust':>5s} | {'AVOID cleared':>14s}  {'mean[95%CI]':>22s}")
for v in INT.VEHICLES:
    d=cert[v]["drift"]; a=cert[v]["avoid"]
    print(f"{v:8s} | {d['cleared']:>4d}/{d['cells']:<9d}  {d['mean']:.3f}[{d['ci'][0]:.3f},{d['ci'][1]:.3f}] {d['mean_sustain']:>5.0f} | "
          f"{a['cleared']:>4d}/{a['cells']:<9d}  {a['mean']:.3f}[{a['ci'][0]:.3f},{a['ci'][1]:.3f}]")
g=cert["_grand"]
print(f"\nGRAND TOTAL: {g['total_cleared']}/{g['total_cells']} cells cleared  "
      f"(drift {g['drift_cleared']}/{g['drift_cells']}, avoid {g['avoid_cleared']}/{g['avoid_cells']})  "
      f"n={N_SEED}/cell, bootstrap={N_BOOT}, wall={g['wall_s']:.0f}s")
