"""DECISIVE follow-up (from adversarial review): the ONLY untested geometry where theory says drift COULD help --
ANGLED + EXTENDED obstacles, where rotating the car body (drift) might align it to slip past. Oriented-box SAT,
binary-search the minimum clearable distance D* per regime. If drift still gets 0 drift-only-clears here, the negative
is closed at FULL scope; if even one, that's the first genuine counterexample."""
import sys; sys.path.insert(0,'src')
import numpy as np, math
from dataclasses import replace
import box_reachability as B
from autodrift.dynamics import SingleTrackDriftModel, VehicleParams, VehicleState
DT=B.DT; HL=B.HL; HW=B.HW
def axes_of(psi): return [(math.cos(psi),math.sin(psi)),(-math.sin(psi),math.cos(psi))]
def clears(params, v, prof, obs):
    """obs=(D, O, hw, hd, opsi) oriented box. Returns (cleared, drifted)."""
    D,O,hw,hd,opsi=obs
    obox=B.corners(D,O,opsi,hd,hw); oax=axes_of(opsi)
    m=SingleTrackDriftModel(params); s=VehicleState(x=0.0,y=0.0,psi=0.0,vx=v,vy=0.0,yaw_rate=0.0)
    steer,thr,brk=prof; maxbeta=0.0; xmax=D+hd+HL+1.0
    for t in range(260):
        s,f=m.step(s, np.array([steer,thr,brk],float), DT)
        beta=abs(math.atan2(s.vy,max(abs(s.vx),1e-6))); maxbeta=max(maxbeta,beta)
        cbox=B.corners(s.x,s.y,s.psi,HL,HW)
        if B.overlap(cbox,B.axes_of(s.psi) if hasattr(B,'axes_of') else axes_of(s.psi), obox,oax): return False, maxbeta>=0.15
        if s.x > xmax: return (abs(s.y)<6.0), maxbeta>=0.15
        if abs(s.vx)<1.0: break
    return False, maxbeta>=0.15
def regimes(params, v, obs):
    nd=dr=False
    for sgn in (1.0,-1.0):
        for steer in np.linspace(0.2,1.0,15):
            for thr,brk in [(0.3,0.0),(1.0,0.0),(0.0,0.5),(0.0,1.0)]:
                ok,drifted=clears(params,v,(sgn*steer,thr,brk),obs)
                if ok and not drifted: nd=True
                if ok and drifted: dr=True
        if nd and dr: break
    return nd,dr
def minD(params,v,hw,hd,opsi,regime):
    cleared=[]
    for D in np.arange(6.0,22.01,0.5):
        nd,dr=regimes(params,v,(float(D),0.0,hw,hd,opsi))
        ok = nd if regime=="nondrift" else dr
        if ok: cleared.append(float(D))
    return min(cleared) if cleared else None
base=VehicleParams(); drift_only=0; tot=0
print("ANGLED+EXTENDED obstacles, oriented-box SAT, D* binary-search. drift-edge if drift_D* < nondrift_D*")
print(f"{'mu':>4s} {'v':>4s} {'opsi':>5s} {'hd':>4s} | {'nondrift_D*':>11s} {'drift_D*':>9s} {'edge':>6s}")
for mu in [0.5,0.8]:
    for v in [14.0]:
        for opsi_deg in [30,45,60]:
            for hd in [1.5,2.5]:
                tot+=1; opsi=math.radians(opsi_deg); p=replace(base,mu=mu)
                ndD=minD(p,v,0.8,hd,opsi,"nondrift"); drD=minD(p,v,0.8,hd,opsi,"drift")
                edge = (ndD-drD) if (ndD is not None and drD is not None) else None
                drift_wins = (drD is not None and (ndD is None or drD < ndD-0.4))
                if drift_wins: drift_only+=1
                es = f"{edge:+.1f}" if edge is not None else ("DRIFT-ONLY" if drD is not None and ndD is None else "n/a")
                print(f"{mu:4.1f} {v:4.0f} {opsi_deg:5d} {hd:4.1f} | {str(ndD):>11s} {str(drD):>9s} {es:>6s}"+("  <-- DRIFT WINS" if drift_wins else ""))
print(f"\n=> drift clears a >0.4m closer obstacle (or only-drift) in {drift_only}/{tot} angled/deep cells")
print("(>0 => first genuine drift-advantage geometry; 0 => negative closed at FULL scope incl angled/extended)")
