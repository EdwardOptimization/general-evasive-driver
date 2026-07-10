"""Deprecated recovery audit retained only for provenance.

This script treated normalized pedal zero as physical zero, even though the
model maps it to 50 percent pedal, and directly injected body states without
valid rear-tire slip. Its 9/9 result is not admissible evidence. Use the
preregistered M3271-M3273 artifacts instead.
"""
import sys, math, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import numpy as np
import distill_both_final_integrated as INT
import phase4_f2_train as f2
def make_slide(mu,v,beta0,ry):
    sc=f2._avoidance_scenario(555,max_steps=150,reveal=30.0,mu=mu); sc["speed_ref"]=v; sc["track_width"]=60.0
    ist=sc["initial_state"]; ist["vx"]=v*math.cos(beta0); ist["vy"]=v*math.sin(beta0); ist["yaw_rate"]=ry
    return sc
def beta_vx(info,obs):
    vx=float(info.get("vx_body",obs[0]*20)); vy=float(info.get("vy_body",obs[1]*12)); return math.atan2(vy,max(abs(vx),1e-6)),vx
def outcome(c,mu,b0,ry,ctrl):
    sc=make_slide(mu,14.0,b0,ry); obs,reply=c.reset(sc,episode_id="r",seed=1); b,vx=beta_vx(reply.get("info",{}),obs); yr=float(obs[2]*2.5)
    for t in range(130):
        obs,term,trunc,status,info=c.step(np.array(ctrl(b,yr),np.float32)); b,vx=beta_vx(info,obs); yr=float(obs[2]*2.5)
        if abs(b)>1.4: return "SPIN"
        if abs(vx)<1.5: return "STOP-sideways" if abs(b)>0.25 else "stopped-ok"
        if abs(b)<0.12 and abs(yr)<0.6 and t>10: return "RECOVER"
    return "ongoing"
none_c=lambda b,yr:[0.0,0.0,0.0]; uniform_brake_c=lambda b,yr:[0.0,0.0,1.0]
def best_steer(c,mu,b0,ry):
    for kg in (0.8,1.4,2.0):
        for kb in (2.0,3.5):
            if outcome(c,mu,b0,ry,lambda b,yr,_g=kg,_k=kb:[float(np.clip(-(_g*yr+_k*b),-1,1)),0.0,0.2])=="RECOVER": return "RECOVER"
    return "fail"
def main():
    raise RuntimeError(
        "deprecated invalid recovery audit; use phase5_h1/h2/h3 preregistered artifacts"
    )
    clients=[INT.ResilientChronoClient(stderr_log=None) for _ in range(6)]
    grid=[(b0,y) for b0 in (0.6,0.8,1.0) for y in (3.0,3.5,4.0)]
    res=[None]*len(grid); ctr={'i':0}; lock=threading.Lock()
    def wk(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(grid): return
                i=ctr['i']; ctr['i']+=1
            b0,y=grid[i]; res[i]=(outcome(c,0.5,b0,y,none_c),outcome(c,0.5,b0,y,uniform_brake_c),best_steer(c,0.5,b0,y))
    try:
        with ThreadPoolExecutor(max_workers=6) as ex:
            for f in [ex.submit(wk,w) for w in range(6)]: f.result()
        print(f"{'b0(deg)':>7s} {'yaw':>4s} | {'none':>13s} {'uniform-brake':>13s} {'counter-steer':>13s}")
        so=0
        for (b0,y),(n,e,s) in zip(grid,res):
            if s=="RECOVER" and n!="RECOVER" and e!="RECOVER": so+=1
            print(f"{math.degrees(b0):7.0f} {y:4.1f} | {n:>13s} {e:>13s} {s:>13s}")
        print(f"\ncounter-steer uniquely recovers under this invalid historical audit in {so}/{len(grid)} cells")
    finally:
        for c in clients:
            try: c.close()
            except Exception: pass
if __name__=="__main__": main()
