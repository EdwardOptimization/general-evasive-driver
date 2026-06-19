"""Box-to-box (OBB) avoidance reachability: does CAR-BODY ROTATION (drift) let the rectangular car clear a box
obstacle when non-drift can't -- or does the tail swing in and make it worse? SAT collision of two oriented boxes.
Car body 4.4x1.8m (half 2.2x0.9); obstacle box (half_width x half_depth). Decisive test of drift's geometric value."""
import sys; sys.path.insert(0,'src')
import numpy as np, math
from dataclasses import replace
from autodrift.dynamics import SingleTrackDriftModel, VehicleParams, VehicleState
DT=0.02; HL=2.2; HW=0.9   # car half-length, half-width

def corners(cx,cy,psi,hl,hw):
    c,s=math.cos(psi),math.sin(psi); out=[]
    for sx in (-hl,hl):
        for sy in (-hw,hw):
            out.append((cx+sx*c-sy*s, cy+sx*s+sy*c))
    return out
def overlap(A,axesA,B,axesB):
    for ax in axesA+axesB:
        amn=min(p[0]*ax[0]+p[1]*ax[1] for p in A); amx=max(p[0]*ax[0]+p[1]*ax[1] for p in A)
        bmn=min(p[0]*ax[0]+p[1]*ax[1] for p in B); bmx=max(p[0]*ax[0]+p[1]*ax[1] for p in B)
        if amx<bmn or bmx<amn: return False
    return True
def car_axes(psi): return [(math.cos(psi),math.sin(psi)),(-math.sin(psi),math.cos(psi))]
OBS_AXES=[(1.0,0.0),(0.0,1.0)]

def clears(params, v, steer, throttle, brake, obs):
    """obs=(D lateral_center_x, O center_y, hw, hd). Returns (cleared:bool, drifted:bool)."""
    D,O,hw,hd=obs
    obox=corners(D,O,0.0,hd,hw)
    m=SingleTrackDriftModel(params); s=VehicleState(x=0.0,y=0.0,psi=0.0,vx=v,vy=0.0,yaw_rate=0.0)
    maxbeta=0.0
    for t in range(220):
        s,f=m.step(s, np.array([steer,throttle,brake],float), DT)
        beta=abs(math.atan2(s.vy,max(abs(s.vx),1e-6))); maxbeta=max(maxbeta,beta)
        cbox=corners(s.x,s.y,s.psi,HL,HW)
        if overlap(cbox,car_axes(s.psi),obox,OBS_AXES): return False, maxbeta>=0.10   # collision
        if s.x > D+hd+HL: return (abs(s.y) < 5.0), maxbeta>=0.10    # fully past, within generous bound
        if abs(s.vx)<1.0: break
    return False, maxbeta>=0.10

def regimes_clear(params, v, obs):
    nd=False; dr=False
    for sgn in (1.0,-1.0):  # dodge either side
        for steer in np.linspace(0.2,1.0,17):
            for thr,brk in [(0.3,0.0),(0.0,0.0),(0.0,0.5),(0.0,1.0)]:
                ok,drifted=clears(params, v, sgn*steer, thr, brk, obs)
                if ok and not drifted: nd=True
                if ok and drifted:     dr=True
            if nd and dr: break
    return nd, dr

base=VehicleParams()
print(f"car {2*HL:.1f}x{2*HW:.1f}m vs box obstacle. For each scenario: can NON-DRIFT clear? can DRIFT clear?")
print(f"{'mu':>4s} {'v':>4s} {'D':>4s} {'O':>4s} {'hw':>4s} {'hd':>4s} | {'nondrift':>8s} {'drift':>6s}  {'verdict':>16s}")
drift_only=0; nd_only=0; both=0; neither=0
for mu in [0.4,0.7]:
    for v in [12.0,16.0]:
        for D in [8.0,12.0,16.0]:
            for hw in [0.7,1.0]:
                for hd in [0.6]:
                    obs=(D,0.0,hw,hd); nd,dr=regimes_clear(replace(base,mu=mu),v,obs)
                    verdict = "DRIFT-ONLY" if (dr and not nd) else ("nondrift-only" if (nd and not dr) else ("both" if nd else "neither"))
                    if dr and not nd: drift_only+=1
                    elif nd and not dr: nd_only+=1
                    elif nd and dr: both+=1
                    else: neither+=1
                    print(f"{mu:4.1f} {v:4.0f} {D:4.0f} {0:4.0f} {hw:4.1f} {hd:4.1f} | {str(nd):>8s} {str(dr):>6s}  {verdict:>16s}")
print(f"\nSUMMARY: drift-ONLY-clears {drift_only} | nondrift-only {nd_only} | both {both} | neither {neither}")
print("(drift-ONLY-clears > 0  =>  car-body rotation gives a GENUINE avoidance regime drift can do and non-drift can't)")
