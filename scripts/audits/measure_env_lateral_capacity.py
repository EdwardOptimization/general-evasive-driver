"""Clean: peak lateral SPECIFIC FORCE fy_body/m (the real tire capability, must be <= ~mu*g),
conventional(sideslip<0.10) vs drifting, from env.last_forces. Settles the 0.42-vs-0.85 label premise."""
import sys; sys.path.insert(0,'src')
import numpy as np, math
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.config import RandomizationConfig
def measure(mu, speed):
    cfg=DriftEnvConfig(track_kind="circle", track_radius=80.0, track_width=30.0, history_length=1,
                       speed_range=(speed,speed), friction_limited_speed=False,
                       randomization=RandomizationConfig(mu_range=(mu,mu), mass_scale_range=(1.0,1.0),
                                                         cg_shift_range=(0.0,0.0), tire_stiffness_scale_range=(1.0,1.0)))
    env=AutoDriftEnv(cfg)
    g=9.81; conv=0.0; drift=0.0; true_mu=mu
    for steer_mag in np.linspace(0.15,1.0,18):
        obs,info=env.reset(seed=3); true_mu=float(info.get("mu",mu))
        for t in range(80):
            obs,r,term,trunc,info=env.step(np.array([steer_mag,0.2,0.0],np.float32))
            st=env.state; f=env.last_forces
            fy_body=f.fy_front*math.cos(st.steer)+f.fy_rear
            ay_force=abs(fy_body)/env.params.mass
            beta=abs(math.atan2(st.vy,max(abs(st.vx),1e-6)))
            if abs(st.vx)<2.0: break
            if beta<0.10: conv=max(conv,ay_force)
            else:         drift=max(drift,ay_force)
            if term or trunc: break
    mug=true_mu*g
    return true_mu, conv, conv/mug, drift, drift/mug
print(f"{'mu':>5s} {'spd':>5s} | {'conv_fy/m':>9s} {'/μg':>6s} | {'drift_fy/m':>10s} {'/μg':>6s}   (label: conv=0.42, drift=0.85)")
for mu in [0.35,0.6,0.9]:
    for sp in [12.0,16.0]:
        tmu,ca,cf,da,df=measure(mu,sp)
        print(f"{tmu:5.2f} {sp:5.1f} | {ca:9.2f} {cf:6.3f} | {da:10.2f} {df:6.3f}")
