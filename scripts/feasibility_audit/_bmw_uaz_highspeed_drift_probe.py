"""VERIFY the BMW drift-blocker negative: does BMW_E90 wash out high sideslip at HIGHER entry speed too
(the de-risk only swept v5-8)? Run open-loop hard-steer+throttle at v12-24 for BMW vs UAZBUS (control,
known-drifter). If BMW washes out where UAZBUS holds -> negative confirmed; if BMW holds -> under-swept."""
from __future__ import annotations
import itertools, math, sys
from pathlib import Path
import numpy as np
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (REPO_ROOT/"src", Path(__file__).resolve().parent):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
import phase4_e4_drift_regime_pricing as e4  # noqa

DT, MAX_STEPS, TRACK_WIDTH = e4.DT, e4.MAX_STEPS, e4.TRACK_WIDTH
LOG = REPO_ROOT/"runs/feasibility_audit/cross_vehicle_bmw_derisk/highspeed_probe_stderr.log"

def scen(variant, mass, mu, speed, beta, radius, seed):
    rng=np.random.default_rng(seed); speed=speed+float(rng.normal(0,0.1))
    return {"scenario_id":f"{variant}-mu{mu:g}-v{speed:g}-s{seed}","dt":DT,"max_steps":MAX_STEPS,
        "track_kind":"circle","track_radius":radius,"track_width":TRACK_WIDTH,"road_lookahead_count":8,
        "road_lookahead_spacing":5.0,"obstacle_slots":4,"obstacle_relative_velocity_mode":"ego",
        "soft_offtrack_metric_enabled":False,"soft_offtrack_tolerance_m":0.0,"chrono_vehicle_variant":variant,
        "params":{"mass":mass,"mu":mu,"max_steer":0.62,"max_steer_rate":3.5,"max_drive_force":8200.0,
            "max_brake_force":6000.0,"drive_tau":0.08,"steer_tau":0.06,"iz":2800.0,"lf":1.30,"lr":1.48,
            "cf":110000.0,"cr":130000.0},
        "initial_state":{"x":radius,"y":0.0,"psi":math.pi/2.0-0.10,"vx":speed*math.cos(beta),
            "vy":speed*math.sin(beta),"yaw_rate":1.20*speed/radius},
        "speed_ref":speed,"obstacle":{"enabled":False},"warmup_gate":{"enabled":False},
        "friction_step":{"at":None,"new_mu":None},"terminate_on_failure":False}

def main():
    LOG.parent.mkdir(parents=True,exist_ok=True)
    runner=e4.RestartingChronoRunner(LOG)
    cases=[("bmw_e90_tmeasy",1800.0),("uazbus_tmeasy",2858.0)]
    speeds=(12.0,16.0,20.0,24.0); mus=(0.25,0.40); steer=0.62; throttle=0.65; radius=90.0; beta0=0.28
    try:
        for variant,mass in cases:
            best=(0,0.0)
            for mu,speed in itertools.product(mus,speeds):
                spec=e4.OpenLoopSpec(f"ol_s{steer:g}",((MAX_STEPS,steer,throttle,0.0),))
                seed=abs(hash((variant,mu,speed)))%2_000_000_000
                r=runner.run(scen(variant,mass,mu,speed,beta0,radius,seed),e4.OpenLoopPolicy(spec,side=beta0),seed=seed)
                lg=int(r["longest_controlled_drift_run"]); bm=round(r["max_abs_beta_rad"],3); rs=int(r["rear_saturation_steps"])
                print(f"  [{variant:16s}] mu={mu:.2f} v={speed:.0f} | sustain={lg:3d} beta_max={bm:.3f} rearsat={rs:3d}",flush=True)
                if lg>best[0]: best=(lg,bm)
            print(f"  -> {variant}: BEST sustain={best[0]} beta_max={best[1]}  HOLDS(>=24)={'YES' if best[0]>=24 else 'NO'}\n",flush=True)
    finally:
        runner.close()

if __name__=="__main__": main()
