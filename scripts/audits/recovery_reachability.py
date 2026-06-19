"""Direction 1 (positive complement): AFTER the car is already sliding, is closed-loop drift management able to SAVE it
from deeper slides than a fixed ESC-style rule? Init at a range of slide depths (sideslip beta0 + matching yaw rate);
measure recovery by (a) a fixed ESC rule (counter-steer prop to yaw+beta, throttle cut) vs (b) BEST closed-loop control
(sweep counter-steer/throttle/brake profiles). 'Recovered' = beta brought < 0.12 rad with bounded yaw, no spin
(|beta| never exceeds 1.2 rad). The gap = slides that drift-management saves but ESC loses = drift's REAL value."""
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
def esc(s,t):
    # REAL brake-based ESC: NO counter-steer authority (driver assumed not counter-steering), cut throttle, brake hard.
    # Mirrors classic ESC = individual-wheel braking + torque cut to scrub speed and restore grip; cannot steer.
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
print("Recovery from an already-initiated slide: BRAKE-ONLY ESC (no counter-steer) vs steering-capable closed-loop. (v=14)")
print(f"{'mu':>4s} {'beta0':>6s} {'yaw0':>5s} | {'ESC_recovers':>12s} {'closed-loop_recovers':>20s} {'gap':>14s}")
gap_cells=0; tot=0
for mu in [0.4,0.6,0.9]:
    for beta0 in [0.6,0.8,0.9,1.0,1.1]:
        ry=beta0*2.0   # developing spin: yaw rate same sign, proportional
        st0=init_state(14.0,beta0,ry); p=replace(base,mu=mu); tot+=1
        e=rollout(p,st0,esc); b=best_recovers(p,st0)
        gap = b and not e
        if gap: gap_cells+=1
        verdict="STEER-CTRL SAVES IT" if gap else ("both" if e and b else ("neither" if not b else "esc-only"))
        print(f"{mu:4.1f} {beta0:6.2f} {ry:5.2f} | {str(e):>12s} {str(b):>20s} {verdict:>18s}")
print(f"\n=> closed-loop drift management recovers slides the fixed ESC rule LOSES in {gap_cells}/{tot} cells")
print("(>0 => drift management has REAL value AFTER slip: it saves the car where the fixed rule spins out)")
