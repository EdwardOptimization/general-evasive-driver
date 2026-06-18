"""Decisive reachability test: is there ANY (speed,mu) where a DRIFT trajectory displaces the CG laterally
FARTHER (by the time-to-obstacle horizon) than the best NON-DRIFT (sideslip-bounded) trajectory? If drift never
beats non-drift on max lateral displacement, drift gives no avoidance advantage in this physics."""
import sys; sys.path.insert(0,'src')
import numpy as np, math
from dataclasses import replace
from autodrift.dynamics import SingleTrackDriftModel, VehicleParams, VehicleState
DT=0.02
def sim(params, v, steer, throttle, brake, T):
    m=SingleTrackDriftModel(params)
    s=VehicleState(x=0.0,y=0.0,psi=0.0,vx=v,vy=0.0,yaw_rate=0.0)
    maxbeta=0.0; ylat=0.0
    for t in range(T):
        a=np.array([steer,throttle,brake],float)
        s,f=m.step(s,a,DT)
        beta=abs(math.atan2(s.vy,max(abs(s.vx),1e-6))); maxbeta=max(maxbeta,beta)
        ylat=abs(s.y)   # lateral displacement perp to initial heading (psi0=0, so global y)
        if abs(s.vx)<1.0: break
    return maxbeta, ylat
def best(params, v, T):
    nd=0.0; dr=0.0  # max lateral displacement: non-drift(maxbeta<0.10) vs drift(>=0.10)
    for steer in np.linspace(0.2,1.0,17):
        for thr,brk in [(0.3,0.0),(0.0,0.0),(0.0,0.4),(0.0,0.8)]:   # no/with braking
            mb,yl=sim(params,v,steer,thr,brk,T)
            if mb<0.10: nd=max(nd,yl)
            else:       dr=max(dr,yl)
    return nd,dr
base=VehicleParams()
print(f"horizon=1.0s ({int(1.0/DT)} steps).  max LATERAL DISPLACEMENT (m): non-drift vs drift")
print(f"{'mu':>5s} {'v':>5s} | {'nondrift_max':>12s} {'drift_max':>10s} {'drift_gain':>11s}")
for mu in [0.30,0.45,0.60,0.90]:
    for v in [10.0,14.0,18.0]:
        p=replace(base, mu=mu)
        nd,dr=best(p,v,int(1.0/DT))
        gain = (dr-nd)/max(nd,1e-6)*100
        flag = "  <-- drift wins" if dr>nd*1.02 else ""
        print(f"{mu:5.2f} {v:5.1f} | {nd:12.2f} {dr:10.2f} {gain:+10.1f}%{flag}")
