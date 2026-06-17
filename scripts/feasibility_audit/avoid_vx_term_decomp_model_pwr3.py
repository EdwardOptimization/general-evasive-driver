"""AVOID-VX term decomposition — MODEL side (gpu_physics_PWR3), TEACHER-FORCED. FULL force balance.

Regenerates the model-side per-step longitudinal force telemetry by replaying the SAME avoid
oracle actions through gpu_physics_pwr3 (the carried faithful model: pwr + the gear-SEED fix),
teacher-forcing the body state (vx,vy,yaw_rate) from the saved Chrono replay each control step so
the force law is read at the SAME operating point Chrono is at. Term-by-term, not contaminated by
trajectory divergence.

This is the pwr3 successor to avoid_vx_term_decomp_model.py (which used the STALE pwr / gear-2
model). pwr3 differs from pwr ONLY in the init_state gear SEED; every force/powertrain internal
(_engine_torque,_gear_ratio,_update_gear,_normal_loads,_wheel_forces,_accel_from_forces) is
byte-identical -- so the only telemetry change vs the stale file is the GEAR the FSM holds (now 3,
matching Chrono) and everything that propagates from it (rpm, T_driveshaft, drive Fx).

Beyond the old script, this logs the FULL body longitudinal force balance so it can be matched to
Chrono's measured ax:
    - gear / rpm / T_eng / T_driveshaft  (powertrain, now gear 3)
    - the model's DRIVE force the body actually feels. The Chrono Sedan is FWD; the model is RWD
      with a FRONT-axle friction-circle CAP on the drive torque. The body drive force = the REAR
      tyre Fx the model puts down (fx_rl+fx_rr), which at steady state equilibrates to the
      front-capped T_wheel/r_eff. We log BOTH the post-cap equilibrium drive (T_wheel_post/r_eff)
      AND the realised rear tyre Fx (fx_r_sum), so we can see cap vs tyre-curve effects.
    - resistance: drag (=0 for Sedan) + rolling (Crr*m*g*tanh(vx))
    - lateral/induced terms during the lane-change turn: front Fy (for the friction-circle cap),
      rear Fy, the steer angle, and the steer-rotation longitudinal loss (Fx_f*cos(steer) vs Fx_f).
    - the resulting model ax_body (= Fx_body/m) and vx_dot (= ax_body + wz*vy), to compare to
      Chrono's measured ax (which is d(vx)/dt = vx_dot).

Run in the base (torch) env (no Chrono needed; teacher-forced from the saved npz):
    python scripts/feasibility_audit/avoid_vx_term_decomp_model_pwr3.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float64)

from autodrift.gpu_physics_pwr3 import (  # noqa: E402  pwr + FAITHFUL highest-in-band gear seed
    PhysParams, make_phys_param_batch, init_state, IDX,
    _engine_torque, _gear_ratio, _update_gear, _normal_loads, _wheel_forces,
    _sigma_at,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
CHRONO = ROOT / "runs/feasibility_audit/phase4_f2/avoid_term_decomp_chrono.npz"
OUT = ROOT / "runs/feasibility_audit/phase4_f2/avoid_term_decomp_model_pwr3.npz"
EPISODES = [72, 73, 74, 75, 76, 77]
DT = 0.02
SIGMA_SCALE = 0.165
DEV = "cpu"


def model_step_instrumented(st, action, gear, P, dt, tf_vx, tf_vy, tf_wz):
    """One pwr3 physics_step (force law identical to pwr), teacher-forcing vx/vy/yaw_rate to the
    Chrono values at the START of the step, recording the FULL longitudinal force balance.

    Returns (next_state, next_gear, rec)."""
    st = st.clone()
    st[:, IDX["vx"]] = tf_vx
    st[:, IDX["vy"]] = tf_vy
    st[:, IDX["yaw_rate"]] = tf_wz
    # re-seed rear omega to the forced vx so the drive-slip state is consistent (no stale-speed kappa)
    st[:, IDX["omega_rl"]] = tf_vx / P["r_eff"]
    st[:, IDX["omega_rr"]] = tf_vx / P["r_eff"]

    vx = st[:, IDX["vx"]]; vy = st[:, IDX["vy"]]; yaw_rate = st[:, IDX["yaw_rate"]]
    steer = st[:, IDX["steer"]]; throttle = st[:, IDX["throttle"]]; brake = st[:, IDX["brake"]]
    omega_rl = st[:, IDX["omega_rl"]]; omega_rr = st[:, IDX["omega_rr"]]
    ax_f = st[:, IDX["ax_f"]]; ay_f = st[:, IDX["ay_f"]]

    # actuator filters (identical to physics_step)
    steer_cmd = torch.clamp(action[:, 0], -1, 1) * P["max_steer"]
    throttle_cmd = 0.5 * (torch.clamp(action[:, 1], -1, 1) + 1.0)
    brake_cmd = 0.5 * (torch.clamp(action[:, 2], -1, 1) + 1.0)
    steer_rate_limit = P["max_steer_rate"] * dt
    steer_lag = torch.clamp(dt / torch.clamp(P["steer_tau"], min=dt), 0, 1)
    steer_target = steer + (steer_cmd - steer) * steer_lag
    new_steer = steer + torch.clamp(steer_target - steer, -steer_rate_limit, steer_rate_limit)
    thr_alpha = torch.clamp(dt / torch.clamp(P["throttle_tau"], min=dt), 0, 1)
    new_throttle = throttle + (throttle_cmd - throttle) * thr_alpha
    brk_alpha = torch.clamp(dt / torch.clamp(P["brake_tau"], min=dt), 0, 1)
    new_brake = brake + (brake_cmd - brake) * brk_alpha

    # gear update (the pwr3 seed makes this hold gear 3 at cruise)
    omega_axle = 0.5 * (omega_rl + omega_rr)
    ratio0 = _gear_ratio(gear, P)
    motor_rad = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio0.clamp_min(1e-3)
    motor_rpm = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm = torch.minimum(torch.maximum(motor_rpm, P["idle_rpm"]), P["max_engine_rpm"])
    new_gear = _update_gear(gear, motor_rpm, P)

    mu_scale = P.mu / P["mu0"]
    fz_fl, fz_fr, fz_rl, fz_rr = _normal_loads(ax_f, ay_f, P)
    fz_nom_f = P["mass"] * P["gravity"] * P["front_axle_share"] * 0.5
    fz_nom_r = P["mass"] * P["gravity"] * (1.0 - P["front_axle_share"]) * 0.5

    # INSTANTANEOUS slip angles (teacher-forced, used as the tyre-curve operating point here:
    # this is a force-law probe at the Chrono operating point, so we use the instantaneous slips
    # rather than the carried lag state -- the cruise is quasi-steady so lag ~ instantaneous).
    lf = 0.5 * P["wheelbase"]; lr = 0.5 * P["wheelbase"]
    sign = torch.where(vx.abs() > 1e-6, torch.sign(vx), torch.ones_like(vx))
    vx_safe = sign * vx.abs().clamp_min(0.75)
    vy_f = vy + lf * yaw_rate
    vy_r = vy - lr * yaw_rate
    alpha_f_inst = torch.atan2(vy_f, vx_safe.abs()) - new_steer
    alpha_r_inst = torch.atan2(vy_r, vx_safe.abs())

    zero = torch.zeros_like(vx)
    gsf = P["front_grip_scale"]; gsr = P["rear_grip_scale"]
    # front wheels FREE-ROLLING (sx=0); lateral only
    fx_fl, fy_fl = _wheel_forces(zero, alpha_f_inst, fz_fl, fz_nom_f, mu_scale, P, gsf)
    fx_fr, fy_fr = _wheel_forces(zero, alpha_f_inst, fz_fr, fz_nom_f, mu_scale, P, gsf)

    # engine -> driveshaft -> axle -> wheel torque
    ratio = _gear_ratio(new_gear, P)
    motor_rad2 = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio.clamp_min(1e-3)
    motor_rpm2 = motor_rad2.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm2 = torch.minimum(torch.maximum(motor_rpm2, P["idle_rpm"]), P["max_engine_rpm"])
    T_eng = _engine_torque(motor_rpm2, new_throttle, P) * P["drive_scale"]
    T_driveshaft = T_eng / ratio.clamp_min(1e-3)
    T_axle = T_driveshaft / P["final_drive"].clamp_min(1e-3)
    T_wheel = 0.5 * T_axle

    # front-axle friction-circle cap on drive torque (the pwr fix)
    fmu_fl = (mu_scale * P["mu0"]) * fz_fl * gsf
    fmu_fr = (mu_scale * P["mu0"]) * fz_fr * gsf
    fx_cap_l = torch.sqrt((fmu_fl * fmu_fl - fy_fl * fy_fl).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fl)
    fx_cap_r = torch.sqrt((fmu_fr * fmu_fr - fy_fr * fy_fr).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fr)
    T_cap_l = fx_cap_l * P["r_eff"]; T_cap_r = fx_cap_r * P["r_eff"]
    T_wheel_l = torch.clamp(T_wheel, -T_cap_l, T_cap_l)
    T_wheel_r = torch.clamp(T_wheel, -T_cap_r, T_cap_r)

    F_drive_pre = 2.0 * (T_wheel / P["r_eff"])                 # pre-cap engine force
    F_drive_post = (T_wheel_l + T_wheel_r) / P["r_eff"]        # post front-cap equilibrium drive

    # --- the REAR tyre Fx the model actually puts the drive down with, at the equilibrium slip ---
    # at steady state the rear wheel omega settles so r_eff*fx_rl ~ T_wheel_l (minus brake/inertia).
    # We invert the tyre Fx curve at the equilibrium drive force to get the rear kappa, then read the
    # combined-slip rear Fx (so the lane-change rear slip-angle Fy steals from the rear Fx budget).
    # Solve fx_r(kappa, alpha_r) = F_drive_post/2 per wheel. Cheap bisection on kappa (monotone at low slip).
    def rear_kappa_for_force(F_target_per_wheel, fz_r, alpha_r):
        lo = torch.zeros_like(vx); hi = torch.full_like(vx, 0.25)
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            fx_mid, _ = _wheel_forces(mid, alpha_r, fz_r, fz_nom_r, mu_scale, P, gsr)
            too_small = fx_mid < F_target_per_wheel
            lo = torch.where(too_small, mid, lo)
            hi = torch.where(too_small, hi, mid)
        return 0.5 * (lo + hi)
    Fpw = (F_drive_post * 0.5).clamp_min(0.0)
    k_rl = rear_kappa_for_force(Fpw, fz_rl, alpha_r_inst)
    k_rr = rear_kappa_for_force(Fpw, fz_rr, alpha_r_inst)
    fx_rl, fy_rl = _wheel_forces(k_rl, alpha_r_inst, fz_rl, fz_nom_r, mu_scale, P, gsr)
    fx_rr, fy_rr = _wheel_forces(k_rr, alpha_r_inst, fz_rr, fz_nom_r, mu_scale, P, gsr)
    Fx_r_sum = fx_rl + fx_rr           # realised rear tyre Fx (drive the body feels)
    Fy_r_sum = fy_rl + fy_rr

    # front axle force rotated by steer (free-rolling: Fx_f=0 long, only the steered lateral leaks
    # a small longitudinal component): Fx_f_body = Fx_f*cos - Fy_f*sin
    Fx_f = fx_fl + fx_fr; Fy_f = fy_fl + fy_fr
    cs = torch.cos(new_steer); sn = torch.sin(new_steer)
    Fx_f_body = Fx_f * cs - Fy_f * sn          # induced-drag-like steer term on the front
    Fy_f_body = Fx_f * sn + Fy_f * cs

    # resistance (the body longitudinal opposers)
    drag = P["drag_coeff"] * vx * vx.abs()
    rolling = P["rolling_resist_coeff"] * P["mass"] * P["gravity"] * torch.tanh(vx)

    # full body longitudinal force balance (matches _accel_from_forces' Fx_body)
    Fx_body = Fx_f_body + Fx_r_sum - drag - rolling
    ax_body = Fx_body / P["mass"]
    vx_dot = ax_body + yaw_rate * vy            # what d(vx)/dt should be -> compare to Chrono ax

    rec = {
        "vx": float(vx[0]), "vy": float(vy[0]), "wz": float(yaw_rate[0]),
        "thr_in": float(new_throttle[0]), "steer": float(new_steer[0]),
        "gear_0idx": float(new_gear[0]), "gear_chrono": float(new_gear[0]) + 1,
        "rpm": float(motor_rpm2[0]),
        "T_eng": float(T_eng[0]), "T_driveshaft": float(T_driveshaft[0]),
        "ratio": float(ratio[0]),
        "fz_front_sum": float((fz_fl + fz_fr)[0]), "fz_rear_sum": float((fz_rl + fz_rr)[0]),
        # drive force terms
        "F_drive_pre": float(F_drive_pre[0]), "F_drive_post": float(F_drive_post[0]),
        "fx_cap_sum": float((fx_cap_l + fx_cap_r)[0]),
        "Fx_r_sum": float(Fx_r_sum[0]),             # realised rear tyre drive Fx
        "Fx_f_body": float(Fx_f_body[0]),           # front steer-leak longitudinal (induced)
        # lateral terms (the lane-change cornering)
        "alpha_f": float(alpha_f_inst[0]), "alpha_r": float(alpha_r_inst[0]),
        "Fy_f_sum": float(Fy_f[0]), "Fy_r_sum": float(Fy_r_sum[0]),
        "fy_fl": float(fy_fl[0]),
        # resistance
        "drag": float(drag[0]), "rolling": float(rolling[0]),
        "F_resist": float((drag + rolling)[0]),
        # net
        "Fx_body": float(Fx_body[0]), "ax_body": float(ax_body[0]), "vx_dot": float(vx_dot[0]),
    }
    st[:, IDX["steer"]] = new_steer
    st[:, IDX["throttle"]] = new_throttle
    st[:, IDX["brake"]] = new_brake
    return st, new_gear, rec


def main():
    d = np.load(AVOID, allow_pickle=True)
    pk = [str(k) for k in d["param_keys"]]
    ch = np.load(CHRONO, allow_pickle=True)
    ch_keys = list(ch["keys"])
    ki = {k: ch_keys.index(k) for k in ch_keys}

    out = {}
    rec_keys = None
    for ep in EPISODES:
        a = np.asarray(d["actions"][ep])
        init = d["init"][ep]
        mu = float(d["params"][ep][pk.index("mu")])
        mass = float(d["params"][ep][pk.index("mass")])
        cs = ch[f"ep{ep}"]
        T = cs.shape[0]

        phys = PhysParams(mass=mass, izz=float(d["params"][ep][pk.index("iz")]),
                          wheelbase=2.776,
                          front_axle_share=float(d["params"][ep][pk.index("lr")]) /
                          (float(d["params"][ep][pk.index("lf")]) + float(d["params"][ep][pk.index("lr")])),
                          sigma_scale=SIGMA_SCALE)
        P = make_phys_param_batch(phys, 1, mu=mu, device=DEV, dtype=torch.float64)
        v0 = torch.tensor(init[None, :], dtype=torch.float64)
        st, gear = init_state(v0[:, 3], v0[:, 4], v0[:, 5], P)
        st = st.clone()
        st[:, 0], st[:, 1], st[:, 2] = v0[:, 0], v0[:, 1], v0[:, 2]

        recs = []
        for k in range(T):
            tf_vx = torch.tensor([cs[k, ki["vx"]]])
            tf_vy = torch.tensor([cs[k, ki["vy"]]])
            tf_wz = torch.tensor([cs[k, ki["wz"]]])
            act = torch.tensor(a[k][None, :], dtype=torch.float64)
            st, gear, rec = model_step_instrumented(st, act, gear, P, DT, tf_vx, tf_vy, tf_wz)
            recs.append(rec)
        if rec_keys is None:
            rec_keys = list(recs[0].keys())
        arr = np.array([[r[k] for k in rec_keys] for r in recs], dtype=np.float64)
        out[f"ep{ep}"] = arr

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, keys=np.array(rec_keys), episodes=np.array(EPISODES), **out)
    print("saved", OUT)
    print("keys:", rec_keys)


if __name__ == "__main__":
    main()
