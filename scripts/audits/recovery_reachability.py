"""Deprecated recovery audit retained only for provenance.

This script used normalized actions as if throttle/brake were physical 0..1
commands and mislabeled uniform service braking as ESC. Its 3/15 count is not
admissible evidence. Use the preregistered M3271-M3273 artifacts instead.
"""
raise RuntimeError(
    "deprecated invalid recovery audit; use phase5_h1/h2/h3 preregistered artifacts"
)
import sys; sys.path.insert(0,'src')
import numpy as np, math
from dataclasses import replace
from autodrift.dynamics import SingleTrackDriftModel, VehicleParams, VehicleState
DT=0.02; H=90
def init_state(v, beta0, ry):
    return VehicleState(x=0.0,y=0.0,psi=0.0,vx=v*math.cos(beta0),vy=v*math.sin(beta0),yaw_rate=ry)
def rollout(params, st0, controller):
    m=SingleTrackDriftModel(params); s=replace(st0)
    spun=False
    for t in range(H):
        a=controller(s,t); s,f=m.step(s, np.asarray(a,float), DT)
        beta=math.atan2(s.vy,max(abs(s.vx),1e-6))
        if abs(beta)>1.2 or abs(s.vx)<1.0: spun=True; break
        if abs(beta)<0.12 and abs(s.yaw_rate)<0.6 and t>10:
            return True   # recovered
    return False if not spun else False
def uniform_brake(s,t):
    return [0.0, 0.0, 1.0]
def best_recovers(params, st0):
    # sweep open-loop+simple-feedback counter-steer gains/throttle/brake to see if ANY recovers (the recoverable set)
    for kg in (0.5,1.0,1.6,2.2):       # yaw feedback gain
        for kb in (1.5,2.5,3.5):       # beta feedback gain
            for thr,brk in [(0.0,0.0),(0.2,0.0),(0.0,0.4),(0.4,0.0)]:
                def ctrl(s,t,_kg=kg,_kb=kb,_th=thr,_br=brk):
                    beta=math.atan2(s.vy,max(abs(s.vx),1e-6))
                    st=float(np.clip(-(_kg*s.yaw_rate+_kb*beta),-1.0,1.0))
                    return [st,_th,_br]
                if rollout(params, st0, ctrl): return True
    return False
base=VehicleParams()
print("DEPRECATED INVALID AUDIT: zero-steer uniform brake vs steering-capable closed-loop. (v=14)")
print(f"{'mu':>4s} {'beta0':>6s} {'yaw0':>5s} | {'brake_recovers':>14s} {'closed-loop_recovers':>20s} {'gap':>14s}")
gap_cells=0; tot=0
for mu in [0.4,0.6,0.9]:
    for beta0 in [0.6,0.8,0.9,1.0,1.1]:
        ry=beta0*2.0   # developing spin: yaw rate same sign, proportional
        st0=init_state(14.0,beta0,ry); p=replace(base,mu=mu); tot+=1
        e=rollout(p,st0,uniform_brake); b=best_recovers(p,st0)
        gap = b and not e
        if gap: gap_cells+=1
        verdict="STEER-CTRL SAVES IT" if gap else ("both" if e and b else ("neither" if not b else "brake-only"))
        print(f"{mu:4.1f} {beta0:6.2f} {ry:5.2f} | {str(e):>12s} {str(b):>20s} {verdict:>18s}")
print(f"\n=> closed-loop drift management recovers slides the uniform-brake rule loses in {gap_cells}/{tot} cells")
print("(>0 => drift management has REAL value AFTER slip: it saves the car where the fixed rule spins out)")
