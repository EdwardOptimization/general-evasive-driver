"""AVOID-VX term decomposition — MODEL side (gpu_physics_pwr), TEACHER-FORCED.

Replays the SAME avoid oracle actions through gpu_physics_pwr (reparam mass=1450, izz=2300,
front_axle_share=lr/(lf+lr), wheelbase=2.776, sigma_scale=0.165 -- IDENTICAL to the pwr gate),
but instead of letting the surrogate state free-run (which drifts), it TEACHER-FORCES the body
state (vx,vy,yaw_rate) from the saved Chrono trajectory each control step before reading the
model's instantaneous per-FRONT-wheel physics. This isolates the FORCE LAW at the SAME operating
point Chrono is at, so the comparison is term-by-term (not contaminated by trajectory divergence).

Exposes, per step, the model's:
    front-wheel kappa (sx)            -- NOTE: model front wheels are FREE-ROLLING (sx=0 forced),
                                         the drive slip lives on the REAR omega states; we report
                                         the rear longitudinal slip the model actually uses to put
                                         the drive force down (since the cap is what matters) AND
                                         the front-axle traction CAP value.
    front Fz (load), rear Fz
    engine motor rpm, gear, T_driveshaft, T_axle, T_wheel (pre/post front-cap)
    the net longitudinal drive force the model applies, and ax_body

Run in the base (torch) env:
    python scripts/feasibility_audit/avoid_vx_term_decomp_model.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float64)

from autodrift.gpu_physics_pwr import (  # noqa: E402
    PhysParams, make_phys_param_batch, init_state, IDX,
    _engine_torque, _gear_ratio, _update_gear, _normal_loads, _wheel_forces,
    _sigma_at, _accel_from_forces,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
CHRONO = ROOT / "runs/feasibility_audit/phase4_f2/avoid_term_decomp_chrono.npz"
OUT = ROOT / "runs/feasibility_audit/phase4_f2/avoid_term_decomp_model.npz"
EPISODES = [72, 73, 74, 75, 76, 77]
DT = 0.02
SIGMA_SCALE = 0.165
DEV = "cpu"


def model_step_instrumented(st, action, gear, P, dt, tf_vx, tf_vy, tf_wz):
    """One pwr physics_step, but teacher-forcing vx/vy/yaw_rate to the Chrono values at the START
    of the step, and recording the internal powertrain + front-axle terms.

    Returns (next_state, next_gear, rec) where rec is a dict of the model's per-step terms
    evaluated at the (teacher-forced) operating point."""
    # overwrite body state with the Chrono truth (teacher forcing)
    st = st.clone()
    st[:, IDX["vx"]] = tf_vx
    st[:, IDX["vy"]] = tf_vy
    st[:, IDX["yaw_rate"]] = tf_wz
    # re-seed the rear wheel omega to the (forced) vx so the drive-slip state is consistent with
    # the forced speed (otherwise the carried omega encodes a stale speed and corrupts kappa/rpm)
    st[:, IDX["omega_rl"]] = tf_vx / P["r_eff"]
    st[:, IDX["omega_rr"]] = tf_vx / P["r_eff"]

    # --- replicate physics_step internals up to the point of the force/powertrain terms ---
    vx = st[:, IDX["vx"]]; vy = st[:, IDX["vy"]]; yaw_rate = st[:, IDX["yaw_rate"]]
    steer = st[:, IDX["steer"]]; throttle = st[:, IDX["throttle"]]; brake = st[:, IDX["brake"]]
    omega_rl = st[:, IDX["omega_rl"]]; omega_rr = st[:, IDX["omega_rr"]]
    ax_f = st[:, IDX["ax_f"]]; ay_f = st[:, IDX["ay_f"]]

    # actuator filters
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

    # gear update
    omega_axle = 0.5 * (omega_rl + omega_rr)
    ratio0 = _gear_ratio(gear, P)
    motor_rad = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio0.clamp_min(1e-3)
    motor_rpm = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm = torch.minimum(torch.maximum(motor_rpm, P["idle_rpm"]), P["max_engine_rpm"])
    new_gear = _update_gear(gear, motor_rpm, P)

    # ---- recompute the powertrain/force terms at this operating point (single eval, h=dt/substeps) ----
    nsub = max(int(P.substeps), 1)
    h = dt / nsub
    mu_scale = P.mu / P["mu0"]
    fz_fl, fz_fr, fz_rl, fz_rr = _normal_loads(ax_f, ay_f, P)
    fz_nom_f = P["mass"] * P["gravity"] * P["front_axle_share"] * 0.5
    fz_nom_r = P["mass"] * P["gravity"] * (1.0 - P["front_axle_share"]) * 0.5

    # front slip angle (instantaneous, used for front Fy in the cap)
    lf = 0.5 * P["wheelbase"]
    sign = torch.where(vx.abs() > 1e-6, torch.sign(vx), torch.ones_like(vx))
    vx_safe = sign * vx.abs().clamp_min(0.75)
    vy_f = vy + lf * yaw_rate
    alpha_f_inst = torch.atan2(vy_f, vx_safe.abs()) - new_steer

    zero = torch.zeros_like(vx)
    gsf = P["front_grip_scale"]
    fx_fl, fy_fl = _wheel_forces(zero, alpha_f_inst, fz_fl, fz_nom_f, mu_scale, P, gsf)
    fx_fr, fy_fr = _wheel_forces(zero, alpha_f_inst, fz_fr, fz_nom_f, mu_scale, P, gsf)

    # engine -> driveshaft -> axle -> wheel torque (the model's powertrain chain)
    ratio = _gear_ratio(new_gear, P)
    motor_rad2 = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio.clamp_min(1e-3)
    motor_rpm2 = motor_rad2.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm2 = torch.minimum(torch.maximum(motor_rpm2, P["idle_rpm"]), P["max_engine_rpm"])
    T_eng = _engine_torque(motor_rpm2, new_throttle, P) * P["drive_scale"]
    T_driveshaft = T_eng / ratio.clamp_min(1e-3)
    T_axle = T_driveshaft / P["final_drive"].clamp_min(1e-3)
    T_wheel = 0.5 * T_axle

    # front-axle traction cap (the pwr fix)
    fmu_fl = (mu_scale * P["mu0"]) * fz_fl * gsf
    fmu_fr = (mu_scale * P["mu0"]) * fz_fr * gsf
    fx_cap_l = torch.sqrt((fmu_fl * fmu_fl - fy_fl * fy_fl).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fl)
    fx_cap_r = torch.sqrt((fmu_fr * fmu_fr - fy_fr * fy_fr).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fr)
    T_cap_l = fx_cap_l * P["r_eff"]
    T_cap_r = fx_cap_r * P["r_eff"]
    T_wheel_l = torch.clamp(T_wheel, -T_cap_l, T_cap_l)
    T_wheel_r = torch.clamp(T_wheel, -T_cap_r, T_cap_r)

    # the model's EQUILIBRIUM net longitudinal drive force (post-cap), what it pushes the body with.
    # (the rear wheel-spin sheds the excess as slip; at steady state F_drive ~= T_wheel/r_eff.)
    F_drive_pre = 2.0 * (T_wheel / P["r_eff"])     # both rear wheels, pre-cap
    F_drive_post = (T_wheel_l + T_wheel_r) / P["r_eff"]  # post front-cap

    rec = {
        "vx": float(vx[0]), "thr_in": float(new_throttle[0]),
        "gear_0idx": int(new_gear[0]), "gear_chrono": int(new_gear[0]) + 1,
        "rpm": float(motor_rpm2[0]),
        "T_eng": float(T_eng[0]), "T_driveshaft": float(T_driveshaft[0]),
        "T_axle": float(T_axle[0]), "T_wheel_percw": float(T_wheel[0]),
        "ratio": float(ratio[0]),
        "fz_front_sum": float((fz_fl + fz_fr)[0]), "fz_rear_sum": float((fz_rl + fz_rr)[0]),
        "fz_fl": float(fz_fl[0]), "fy_fl": float(fy_fl[0]),
        "fmu_front_sum": float((fmu_fl + fmu_fr)[0]),
        "fx_cap_sum": float((fx_cap_l + fx_cap_r)[0]),
        "F_drive_pre": float(F_drive_pre[0]), "F_drive_post": float(F_drive_post[0]),
        "alpha_f": float(alpha_f_inst[0]),
        "ax_f_used": float(ax_f[0]),
    }
    # carry the actuator/gear forward so the next teacher-forced step is consistent
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
        cs = ch[f"ep{ep}"]  # [T, nkeys] the Chrono telemetry (teacher-forcing source)
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
