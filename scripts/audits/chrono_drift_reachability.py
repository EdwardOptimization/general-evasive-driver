"""Direction 3: validate the no-drift-advantage finding on the FAITHFUL Chrono multibody backend (closes the planar
friction-circle caveat). Open-loop steering sweeps; measure max lateral displacement over a fixed horizon, conventional
(max sideslip<0.10) vs drift (>=0.10). Also logs tire lateral-force utilization + normal-load transfer (the multibody
effects the planar model omits)."""
import sys, threading, math
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import numpy as np
import distill_both_final_integrated as INT
import phase4_f2_train as f2
ONSET=8; HORIZON=40   # steer onset step, measure displacement HORIZON steps later
def run_profile(client, mu, prof, V=16.0):
    steer,thr,brk=prof
    sc=f2._avoidance_scenario(777, max_steps=ONSET+HORIZON+5, reveal=30.0, mu=mu)
    sc["speed_ref"]=V; sc["track_width"]=30.0
    ist=sc["initial_state"]; ist["vx"]=V; ist["vy"]=0.0; ist["yaw_rate"]=0.0
    obs,reply=client.reset(sc, episode_id=f"reach-mu{mu}-{steer}-{thr}-{brk}", seed=2)
    lat0=None; maxbeta=0.0; lat_at_h=0.0; util=0.0; load_spread=0.0
    for t in range(ONSET+HORIZON):
        a = np.array([0.0,0.3,0.0],np.float32) if t<ONSET else np.array([steer,thr,brk],np.float32)
        obs,term,trunc,status,info=client.step(a)
        vx=float(info.get("vx_body",obs[0]*20)); vy=float(info.get("vy_body",obs[1]*12))
        beta=abs(math.atan2(vy,max(abs(vx),1e-6)));
        if t>=ONSET: maxbeta=max(maxbeta,beta)
        le=info.get("lateral_error")
        if t==ONSET-1 and le is not None: lat0=float(le)
        if le is not None and lat0 is not None: lat_at_h=abs(float(le)-lat0)
        nl_max=info.get("max_tire_normal_load_n"); nl_min=info.get("min_tire_normal_load_n")
        lf=info.get("max_abs_tire_lateral_force_n")
        if nl_max and nl_min and nl_max>0: load_spread=max(load_spread,(float(nl_max)-float(nl_min))/float(nl_max))
        if lf and nl_max: util=max(util, float(lf)/max(float(nl_max)*mu,1e-6))
        if term or trunc: break
    return maxbeta, lat_at_h, util, load_spread
def measure(clients, mu):
    profiles=[(s,th,br) for s in (0.6,0.8,1.0) for (th,br) in [(0.3,0.0),(1.0,0.0),(0.0,0.6),(0.0,1.0)]]  # steer / power-oversteer / trail-brake
    steers=profiles
    res=[None]*len(steers); ctr={'i':0}; lock=threading.Lock()
    def worker(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(steers): return
                i=ctr['i']; ctr['i']+=1
            res[i]=run_profile(c, mu, steers[i])
    with ThreadPoolExecutor(max_workers=len(clients)) as ex:
        for fut in [ex.submit(worker,w) for w in range(len(clients))]: fut.result()
    conv=[(d,u,ls) for (b,d,u,ls) in res if b<0.10]; drift=[(d,u,ls) for (b,d,u,ls) in res if b>=0.10]
    cmax=max([d for d,u,ls in conv],default=0.0); dmax=max([d for d,u,ls in drift],default=0.0)
    cu=max([u for d,u,ls in conv],default=0.0); du=max([u for d,u,ls in drift],default=0.0)
    lspread=max([ls for b,d,u,ls in res],default=0.0)
    return cmax,dmax,cu,du,lspread,len(conv),len(drift)
clients=[INT.ResilientChronoClient(stderr_log=None) for _ in range(8)]
try:
    print("CHRONO (faithful multibody): max lateral displacement over horizon, conventional vs drift")
    print(f"{'mu':>5s} | {'conv_disp':>9s} {'drift_disp':>10s} {'drift_edge':>10s} | {'conv_util':>9s} {'drift_util':>10s} {'loadXfer':>9s}")
    for mu in [0.35,0.6,0.9]:
        cmax,dmax,cu,du,ls,nc,nd=measure(clients,mu)
        edge=(dmax-cmax)/max(cmax,1e-6)*100
        flag="  <-- drift wins" if dmax>cmax*1.02 else ""
        print(f"{mu:5.2f} | {cmax:9.2f} {dmax:10.2f} {edge:+9.1f}%{flag} | {cu:9.2f} {du:10.2f} {ls:9.2f}  (nconv={nc} ndrift={nd})")
finally:
    for c in clients:
        try: c.close()
        except Exception: pass
