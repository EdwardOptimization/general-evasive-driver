"""DIAGNOSIS: replay the held-out drift actions through pwr3 and log the SAME internal lateral/yaw
force-balance terms Chrono is instrumented for, so the two can be compared term-by-term at the saddle.

Re-implements pwr3's physics_step substep loop with full per-wheel instrumentation (the public
physics_step hides the internals). At every control step (after the substep loop) it logs the
LAST-substep internal values: per-wheel Fz (FL,FR,RL,RR incl. lateral load transfer), per-wheel
Fy, per-axle/wheel slip angles (instantaneous AND relaxation-lagged), the rear longitudinal slip,
the per-axle lateral force, the yaw moment, and the body state. Uses sigma_scale=0.165, the drift
mu, the held-out split idx[130:] -- identical to gpu_pwr3_gate.py.

Output: runs/feasibility_audit/phase4_f2/drift_heldout_lateral_pwr3.npz

Run:  PYTHONPATH=src python scripts/feasibility_audit/instrument_drift_heldout_pwr3.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import autodrift.gpu_physics_pwr3 as M  # noqa: E402
from autodrift.gpu_physics_pwr3 import (  # noqa: E402
    PhysParams, make_phys_param_batch, init_state, IDX,
    _normal_loads, _wheel_forces, _accel_from_forces, _sigma_at,
    _gear_ratio, _update_gear, _engine_torque,
)

DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
OUT = ROOT / "runs/feasibility_audit/phase4_f2/drift_heldout_lateral_pwr3.npz"
SIGMA_SCALE = 0.165
DT = 0.02
DEV = "cpu"
torch.set_default_dtype(torch.float32)


def instrumented_step(state, action, gear, P, dt, log):
    """A copy of physics_step that logs the per-wheel lateral terms (last substep)."""
    s = state
    vx = s[:, IDX["vx"]]; vy = s[:, IDX["vy"]]; yaw_rate = s[:, IDX["yaw_rate"]]
    steer = s[:, IDX["steer"]]; throttle = s[:, IDX["throttle"]]; brake = s[:, IDX["brake"]]
    omega_rl = s[:, IDX["omega_rl"]]; omega_rr = s[:, IDX["omega_rr"]]
    ax_f = s[:, IDX["ax_f"]]; ay_f = s[:, IDX["ay_f"]]
    alpha_f_lag = s[:, IDX["alpha_f_lag"]]; alpha_r_lag = s[:, IDX["alpha_r_lag"]]
    sx_rl_lag = s[:, IDX["sx_rl_lag"]]; sx_rr_lag = s[:, IDX["sx_rr_lag"]]
    psi = s[:, IDX["psi"]]

    steer_cmd = torch.clamp(action[:, 0], -1.0, 1.0) * P["max_steer"]
    throttle_cmd = 0.5 * (torch.clamp(action[:, 1], -1.0, 1.0) + 1.0)
    brake_cmd = 0.5 * (torch.clamp(action[:, 2], -1.0, 1.0) + 1.0)
    steer_rate_limit = P["max_steer_rate"] * dt
    steer_lag = torch.clamp(dt / torch.clamp(P["steer_tau"], min=dt), 0.0, 1.0)
    steer_target = steer + (steer_cmd - steer) * steer_lag
    new_steer = steer + torch.clamp(steer_target - steer, -steer_rate_limit, steer_rate_limit)
    thr_alpha = torch.clamp(dt / torch.clamp(P["throttle_tau"], min=dt), 0.0, 1.0)
    new_throttle = throttle + (throttle_cmd - throttle) * thr_alpha
    brk_alpha = torch.clamp(dt / torch.clamp(P["brake_tau"], min=dt), 0.0, 1.0)
    new_brake = brake + (brake_cmd - brake) * brk_alpha

    omega_axle = 0.5 * (omega_rl + omega_rr)
    ratio0 = _gear_ratio(gear, P)
    motor_rad = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio0.clamp_min(1e-3)
    motor_rpm = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm = torch.minimum(torch.maximum(motor_rpm, P["idle_rpm"]), P["max_engine_rpm"])
    new_gear = _update_gear(gear, motor_rpm, P)

    nsub = max(int(P.substeps), 1)
    h = dt / nsub
    last_ax, last_ay = ax_f, ay_f
    rec = {}
    for _ in range(nsub):
        mu_scale = P.mu / P["mu0"]
        fz_fl, fz_fr, fz_rl, fz_rr = _normal_loads(last_ax, last_ay, P)
        fz_nom_f = P["mass"] * P["gravity"] * P["front_axle_share"] * 0.5
        fz_nom_r = P["mass"] * P["gravity"] * (1.0 - P["front_axle_share"]) * 0.5

        lf = 0.5 * P["wheelbase"]; lr = 0.5 * P["wheelbase"]
        sign = torch.where(vx.abs() > 1e-6, torch.sign(vx), torch.ones_like(vx))
        vx_safe = sign * vx.abs().clamp_min(0.75)
        vy_f = vy + lf * yaw_rate
        vy_r = vy - lr * yaw_rate
        alpha_f_inst = torch.atan2(vy_f, vx_safe.abs()) - new_steer
        alpha_r_inst = torch.atan2(vy_r, vx_safe.abs())

        half_tr = 0.5 * P["track_r"]
        vx_rl = vx - yaw_rate * half_tr
        vx_rr = vx + yaw_rate * half_tr
        vx_rl_safe = torch.sign(vx_rl) * vx_rl.abs().clamp_min(0.75)
        vx_rr_safe = torch.sign(vx_rr) * vx_rr.abs().clamp_min(0.75)
        sx_rl_inst = (P["r_eff"] * omega_rl - vx_rl) / vx_rl_safe.abs().clamp_min(0.5)
        sx_rr_inst = (P["r_eff"] * omega_rr - vx_rr) / vx_rr_safe.abs().clamp_min(0.5)

        v_relax = vx.abs().clamp_min(1.0)
        sig_a_f = _sigma_at(0.5 * (fz_fl + fz_fr), P, "alpha")
        sig_a_r = _sigma_at(0.5 * (fz_rl + fz_rr), P, "alpha")
        sig_k_rl = _sigma_at(fz_rl, P, "kappa")
        sig_k_rr = _sigma_at(fz_rr, P, "kappa")
        af = 1.0 - torch.exp(-(v_relax / sig_a_f) * h)
        ar = 1.0 - torch.exp(-(v_relax / sig_a_r) * h)
        kl = 1.0 - torch.exp(-(v_relax / sig_k_rl) * h)
        kr = 1.0 - torch.exp(-(v_relax / sig_k_rr) * h)
        alpha_f_lag = alpha_f_lag + af * (alpha_f_inst - alpha_f_lag)
        alpha_r_lag = alpha_r_lag + ar * (alpha_r_inst - alpha_r_lag)
        sx_rl_lag = sx_rl_lag + kl * (sx_rl_inst - sx_rl_lag)
        sx_rr_lag = sx_rr_lag + kr * (sx_rr_inst - sx_rr_lag)

        zero = torch.zeros_like(vx)
        gsf = P["front_grip_scale"]; gsr = P["rear_grip_scale"]
        fx_fl, fy_fl = _wheel_forces(zero, alpha_f_lag, fz_fl, fz_nom_f, mu_scale, P, gsf)
        fx_fr, fy_fr = _wheel_forces(zero, alpha_f_lag, fz_fr, fz_nom_f, mu_scale, P, gsf)
        fx_rl, fy_rl = _wheel_forces(sx_rl_lag, alpha_r_lag, fz_rl, fz_nom_r, mu_scale, P, gsr)
        fx_rr, fy_rr = _wheel_forces(sx_rr_lag, alpha_r_lag, fz_rr, fz_nom_r, mu_scale, P, gsr)

        Fx_f = fx_fl + fx_fr; Fx_r = fx_rl + fx_rr
        Fy_f = fy_fl + fy_fr; Fy_r = fy_rl + fy_rr

        vx_dot, vy_dot, yaw_dot, ax_body, ay_body = _accel_from_forces(
            vx, vy, yaw_rate, new_steer, Fx_f, Fy_f, Fx_r, Fy_r, P)

        # ---- powertrain (rear wheel-spin) ----
        omega_axle = 0.5 * (omega_rl + omega_rr)
        ratio = _gear_ratio(new_gear, P)
        motor_rad = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio.clamp_min(1e-3)
        motor_rpm2 = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
        motor_rpm2 = torch.minimum(torch.maximum(motor_rpm2, P["idle_rpm"]), P["max_engine_rpm"])
        T_eng = _engine_torque(motor_rpm2, new_throttle, P) * P["drive_scale"]
        T_driveshaft = T_eng / ratio.clamp_min(1e-3)
        T_axle = T_driveshaft / P["final_drive"].clamp_min(1e-3)
        T_wheel = 0.5 * T_axle
        fmu_fl = (mu_scale * P["mu0"]) * fz_fl * gsf
        fmu_fr = (mu_scale * P["mu0"]) * fz_fr * gsf
        fx_cap_l = torch.sqrt((fmu_fl * fmu_fl - fy_fl * fy_fl).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fl)
        fx_cap_r = torch.sqrt((fmu_fr * fmu_fr - fy_fr * fy_fr).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fr)
        T_cap_l = fx_cap_l * P["r_eff"]; T_cap_r = fx_cap_r * P["r_eff"]
        T_wheel_l = torch.clamp(T_wheel, -T_cap_l, T_cap_l)
        T_wheel_r = torch.clamp(T_wheel, -T_cap_r, T_cap_r)
        T_brake_r = new_brake * P["max_brake_torque"]
        T_brake_rl = T_brake_r * torch.sign(omega_rl)
        T_brake_rr = T_brake_r * torch.sign(omega_rr)
        orl_dot = (T_wheel_l - P["r_eff"] * fx_rl - T_brake_rl) / P["i_wheel"]
        orr_dot = (T_wheel_r - P["r_eff"] * fx_rr - T_brake_rr) / P["i_wheel"]

        lf2 = 0.5 * P["wheelbase"]; lr2 = 0.5 * P["wheelbase"]
        cs = torch.cos(new_steer); sn = torch.sin(new_steer)
        Fy_f_body = Fx_f * sn + Fy_f * cs
        Mz = lf2 * Fy_f_body - lr2 * Fy_r

        # record the last substep's terms
        rec = dict(
            fz_fl=fz_fl, fz_fr=fz_fr, fz_rl=fz_rl, fz_rr=fz_rr,
            fy_fl=fy_fl, fy_fr=fy_fr, fy_rl=fy_rl, fy_rr=fy_rr,
            fx_fl=fx_fl, fx_fr=fx_fr, fx_rl=fx_rl, fx_rr=fx_rr,
            alpha_f_inst=alpha_f_inst, alpha_r_inst=alpha_r_inst,
            alpha_f_lag=alpha_f_lag, alpha_r_lag=alpha_r_lag,
            sx_rl_lag=sx_rl_lag, sx_rr_lag=sx_rr_lag,
            sx_rl_inst=sx_rl_inst, sx_rr_inst=sx_rr_inst,
            Fy_f=Fy_f, Fy_r=Fy_r, Fy_f_body=Fy_f_body, Mz=Mz,
            ay_body=ay_body, ax_body=ax_body,
        )

        vx = vx + h * vx_dot
        vy = vy + h * vy_dot
        yaw_rate = yaw_rate + h * yaw_dot
        omega_rl = omega_rl + h * orl_dot
        omega_rr = omega_rr + h * orr_dot
        last_ax, last_ay = ax_body, ay_body

    new_psi = psi + dt * s[:, IDX["yaw_rate"]]
    new_x = s[:, IDX["x"]] + dt * (s[:, IDX["vx"]] * torch.cos(psi) - s[:, IDX["vy"]] * torch.sin(psi))
    new_y = s[:, IDX["y"]] + dt * (s[:, IDX["vx"]] * torch.sin(psi) + s[:, IDX["vy"]] * torch.cos(psi))

    out = state.clone()
    out[:, IDX["x"]] = new_x; out[:, IDX["y"]] = new_y; out[:, IDX["psi"]] = new_psi
    out[:, IDX["vx"]] = vx; out[:, IDX["vy"]] = vy; out[:, IDX["yaw_rate"]] = yaw_rate
    out[:, IDX["steer"]] = new_steer; out[:, IDX["throttle"]] = new_throttle; out[:, IDX["brake"]] = new_brake
    out[:, IDX["omega_rl"]] = omega_rl; out[:, IDX["omega_rr"]] = omega_rr
    out[:, IDX["ax_f"]] = last_ax; out[:, IDX["ay_f"]] = last_ay
    out[:, IDX["alpha_f_lag"]] = alpha_f_lag; out[:, IDX["alpha_r_lag"]] = alpha_r_lag
    out[:, IDX["sx_rl_lag"]] = sx_rl_lag; out[:, IDX["sx_rr_lag"]] = sx_rr_lag

    for k, v in rec.items():
        log.setdefault(k, []).append(v.detach().cpu().numpy())
    return out, new_gear


def main():
    d = np.load(DATA, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)
    init = d["init"].astype(np.float32)
    mu = float(d["mu"][0])
    idx = np.random.default_rng(0).permutation(A.shape[0])
    va = idx[130:]
    Av, iv = A[va], init[va]
    R, T, _ = Av.shape

    P = make_phys_param_batch(PhysParams(sigma_scale=SIGMA_SCALE), R, mu=mu, device=DEV, dtype=torch.float32)
    A_t = torch.tensor(Av); it = torch.tensor(iv)
    st, gear = init_state(it[:, 0], it[:, 1], it[:, 2], P)

    log = {}
    vx_log = np.zeros((R, T)); vy_log = np.zeros((R, T)); wz_log = np.zeros((R, T))
    steer_log = np.zeros((R, T))
    with torch.no_grad():
        for t in range(T):
            st, gear = instrumented_step(st, A_t[:, t, :], gear, P, DT, log)
            vx_log[:, t] = st[:, IDX["vx"]].cpu().numpy()
            vy_log[:, t] = st[:, IDX["vy"]].cpu().numpy()
            wz_log[:, t] = st[:, IDX["yaw_rate"]].cpu().numpy()
            steer_log[:, t] = st[:, IDX["steer"]].cpu().numpy()

    # log dict: each key -> list of T arrays [R] -> stack to [R,T]
    out = {k: np.stack(v, axis=1) for k, v in log.items()}  # [R,T]
    out.update(vx=vx_log, vy=vy_log, wz=wz_log, steer=steer_log,
               held_out=va.astype(np.int64))
    np.savez(OUT, **out)
    print("saved", OUT, "R=%d T=%d" % (R, T))


if __name__ == "__main__":
    main()
