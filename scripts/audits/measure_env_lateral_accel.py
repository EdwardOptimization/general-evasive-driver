"""Foundational audit v2: peak lateral accel the env's car achieves, conventional(no drift) vs drifting,
with mu PROPERLY pinned. Tests the label's conventional=0.42 / drift=0.85 mu-fraction assumptions."""
import sys; sys.path.insert(0,'src')
import numpy as np, math
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.config import RandomizationConfig
def measure(mu, speed):
    cfg=DriftEnvConfig(track_kind="circle", track_radius=80.0, track_width=30.0, history_length=1,
                       speed_range=(speed,speed), friction_limited_speed=False,
                       randomization=RandomizationConfig(mu_range=(mu,mu), mass_scale_range=(1.0,1.0),
                                                         cg_shift_range=(0.0,0.0), tire_stiffness_scale_range=(1.0,1.0)))
    env=AutoDriftEnv(cfg); obs,info=env.reset(seed=3)
    true_mu=float(info.get("mu",mu)); g=9.81; mug=true_mu*g
    best={"conv":0.0,"drift":0.0}
    # sweep a range of fixed steering magnitudes; for each, hold a few steps with throttle to keep speed, record ay vs beta
    for steer_mag in np.linspace(0.1,1.0,19):
        obs,info=env.reset(seed=3)
        for t in range(60):
            # light throttle to hold speed; pure steer (no brake) = conventional cornering attempt
            obs,r,term,trunc,info=env.step(np.array([steer_mag,0.15,0.0],np.float32))
            vx=float(obs[0]*20.0); vy=float(obs[1]*12.0); ay=abs(float(obs[4]*15.0))
            beta=abs(math.atan2(vy,max(abs(vx),1e-6)))
            if abs(vx)<2.0: break
            if beta<0.10: best["conv"]=max(best["conv"],ay)
            else:         best["drift"]=max(best["drift"],ay)
            if term or trunc: break
    return true_mu, best["conv"], best["conv"]/mug, best["drift"], best["drift"]/mug
print(f"{'mu':>5s} {'spd':>5s} | {'conv_ay':>8s} {'conv/μg':>8s} | {'drift_ay':>9s} {'drift/μg':>9s}   (label: conv=0.42, drift=0.85)")
for mu in [0.35,0.6,0.9]:
    for sp in [12.0,16.0]:
        tmu,ca,cf,da,df=measure(mu,sp)
        print(f"{tmu:5.2f} {sp:5.1f} | {ca:8.2f} {cf:8.3f} | {da:9.2f} {df:9.3f}")
