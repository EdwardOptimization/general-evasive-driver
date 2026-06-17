"""MODEL-side cruise force balance: drive gpu_physics_pwr at the SAME constant partial throttle at
mu=1.0 and log the SAME longitudinal force-balance terms as instrument_cruise_forcebalance.py, so
the Chrono-vs-model discrepancy can be localized to ONE term.

Drives the model in OPEN LOOP (steer=0) holding a constant throttle command. Spins up to the replay
cruise speed first (so we evaluate at the SAME operating point as the Chrono replay), then samples at
matched speeds 9.5 and 11.0 m/s and at the model's free terminal:

  vx, gear (model 0-idx + Chrono 1-idx), ratio, motor rpm, engine torque (the blend),
  driveshaft torque, axle torque, per-wheel drive force, front/rear tyre Fx, resistance,
  the FWD front-traction cap (whether it bites), net longitudinal force.

Run (autodrift env):
    /home/quyaonan/miniforge3/envs/autodrift/bin/python \
        scripts/feasibility_audit/model_cruise_forcebalance.py
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from autodrift import gpu_physics_pwr as M  # noqa: E402

DT = 0.02            # 50 Hz control step (the env uses 50 Hz)
MU = 1.0
THROTTLES = [0.08, 0.12, 0.15]
SPIN_UP_TO = 9.5
DEVICE = "cpu"


def thr_to_action(thr):
    # action[1] is mapped throttle_cmd = 0.5*(clamp(a,-1,1)+1) -> a = 2*thr - 1
    return 2.0 * thr - 1.0


def make_batch():
    p = M.PhysParams()
    return M.make_phys_param_batch(p, 1, mu=MU, device=DEVICE, dtype=torch.float32), p


def engine_torque_blend(rpm, throttle, P):
    r = torch.tensor([rpm], dtype=torch.float32)
    return float(M._engine_torque(r, torch.tensor([throttle]), P)[0])


def probe_terms(state, gear, P, p, throttle):
    """Recompute the model's longitudinal terms at the current state (mirror _continuous_derivs)."""
    s = state
    vx = s[:, M.IDX["vx"]]
    omega_rl = s[:, M.IDX["omega_rl"]]; omega_rr = s[:, M.IDX["omega_rr"]]
    # gear ratio + motor rpm
    omega_axle = 0.5 * (omega_rl + omega_rr)
    ratio = M._gear_ratio(gear, P)
    motor_rad = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio.clamp_min(1e-3)
    motor_rpm = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm = torch.minimum(torch.maximum(motor_rpm, P["idle_rpm"]), P["max_engine_rpm"])
    thr_t = torch.full_like(vx, throttle)
    T_eng = M._engine_torque(motor_rpm, thr_t, P) * P["drive_scale"]
    T_ds = T_eng / ratio.clamp_min(1e-3)
    T_axle = T_ds / P["final_drive"].clamp_min(1e-3)
    T_wheel = 0.5 * T_axle
    F_drive_per_wheel = T_wheel / P["r_eff"]            # equilibrium drive force per driven wheel
    F_drive_total = 2.0 * F_drive_per_wheel             # model applies on the 2 rear wheels

    # resistance (model)
    drag = P["drag_coeff"] * vx * vx.abs()
    rolling = P["rolling_resist_coeff"] * P["mass"] * P["gravity"] * torch.tanh(vx)
    F_res = drag + rolling

    # front-traction cap diagnostics (need fz_front + fy_front)
    ax_f = s[:, M.IDX["ax_f"]]; ay_f = s[:, M.IDX["ay_f"]]
    fz_fl, fz_fr, fz_rl, fz_rr = M._normal_loads(ax_f, ay_f, P)
    mu_scale = P.mu / P["mu0"]
    gsf = P["front_grip_scale"]
    fmu_fl = (mu_scale * P["mu0"]) * fz_fl * gsf
    fmu_fr = (mu_scale * P["mu0"]) * fz_fr * gsf
    # front lateral force ~ 0 in straight cruise; cap ~ mu*Fz_front
    fx_cap = float((fmu_fl + fmu_fr)[0])
    return dict(
        vx=float(vx[0]), gear=int(gear[0]), ratio=float(ratio[0]), rpm=float(motor_rpm[0]),
        T_eng=float(T_eng[0]), T_ds=float(T_ds[0]), T_axle=float(T_axle[0]),
        F_drive_total=float(F_drive_total[0]), F_res=float(F_res[0]),
        fz_front=float((fz_fl + fz_fr)[0]), fx_cap=fx_cap,
        F_net=float((F_drive_total - F_res)[0]),
    )


def run_throttle(thr):
    P, p = make_batch()
    vx0 = torch.tensor([2.0], dtype=torch.float32)
    state, gear = M.init_state(vx0, torch.zeros(1), torch.zeros(1), P)

    # spin up to SPIN_UP_TO with full throttle, then hold thr
    a_up = torch.tensor([[0.0, 1.0, -1.0]], dtype=torch.float32)  # steer0, full throttle, no brake
    for _ in range(2000):
        if float(state[0, M.IDX["vx"]]) >= SPIN_UP_TO:
            break
        state, gear, _ = M.physics_step(state, a_up, gear, P, DT)

    # hold thr; sample terms at matched speeds and at terminal
    act = torch.tensor([[0.0, thr_to_action(thr), -1.0]], dtype=torch.float32)
    rows = []
    matched = {9.5: None, 11.0: None}
    prev_vx = float(state[0, M.IDX["vx"]])
    terminal_terms = None
    hold = 0
    for step in range(8000):
        terms = probe_terms(state, gear, P, p, thr)
        v = terms["vx"]
        rows.append(terms)
        for vq in matched:
            if matched[vq] is None and abs(v - vq) < 0.05:
                matched[vq] = terms
        state, gear, _ = M.physics_step(state, act, gear, P, DT)
        v_new = float(state[0, M.IDX["vx"]])
        a = (v_new - v) / DT
        if abs(a) < 0.01 and v_new > 3.0:
            hold += 1
            if hold > 100:
                terminal_terms = probe_terms(state, gear, P, p, thr)
                break
        else:
            hold = 0
        prev_vx = v_new
    if terminal_terms is None:
        terminal_terms = probe_terms(state, gear, P, p, thr)
    # fill matched by nearest if not hit exactly
    for vq in matched:
        if matched[vq] is None:
            vs = np.array([r["vx"] for r in rows])
            if len(vs):
                matched[vq] = rows[int(np.argmin(np.abs(vs - vq)))]
    return matched, terminal_terms


def main():
    P, p = make_batch()
    print("=== MODEL gpu_physics_pwr cruise force balance @ mu=%.2f (DT=%.3f) ===" % (MU, DT))
    print("  GEAR_RATIOS:", M.GEAR_RATIOS, " final_drive:", p.final_drive, " r_eff:", p.r_eff)
    print("  Crr:", p.rolling_resist_coeff, " drag_coeff:", p.drag_coeff)
    print("  SHIFT_UP:", M.SHIFT_UP, " SHIFT_DOWN:", M.SHIFT_DOWN)
    for thr in THROTTLES:
        matched, term = run_throttle(thr)
        print("\n========== THROTTLE %.2f ==========" % thr)
        print("  MODEL free TERMINAL: vx=%.3f gear=%d(idx)/%d(chrono) ratio=%.3f rpm=%.0f "
              "T_eng=%.1f T_ds=%.1f F_drive=%.0f F_res=%.0f F_net=%.0f fx_cap=%.0f fz_f=%.0f" % (
            term["vx"], term["gear"], term["gear"] + 1, term["ratio"], term["rpm"],
            term["T_eng"], term["T_ds"], term["F_drive_total"], term["F_res"], term["F_net"],
            term["fx_cap"], term["fz_front"]))
        for vq in (9.5, 11.0):
            t = matched[vq]
            if t is None:
                continue
            print("  @ v=%.1f: gear=%d(idx)/%d ratio=%.3f rpm=%.0f T_eng=%.1f T_ds=%.1f "
                  "F_drive=%.0f F_res=%.0f F_net=%.0f cap=%.0f%s" % (
                vq, t["gear"], t["gear"] + 1, t["ratio"], t["rpm"], t["T_eng"], t["T_ds"],
                t["F_drive_total"], t["F_res"], t["F_net"], t["fx_cap"],
                "  CAP BITES" if t["fx_cap"] < t["F_drive_total"] else ""))


if __name__ == "__main__":
    main()
