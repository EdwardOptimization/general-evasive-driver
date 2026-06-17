"""ROOT-CAUSE the high-mu partial-throttle CRUISE over-acceleration: measure the FULL longitudinal
FORCE BALANCE at the cruise operating point in the REAL Chrono Sedan, term by term, at mu~=1.0.

The faithful planar rewrite (src/autodrift/gpu_physics_pwr.py) coasts to terminal vx ~11.8 m/s at
mu~=1.0, throttle~=0.12 while real Chrono plateaus ~9.5 m/s. Gear (gear 2) is verified correct,
engine PEAK-torque map +/-1.5%, brake is not it (accel phase). This script measures, at the cruise
plateau, EVERY longitudinal term so the ONE discrepant term can be isolated:

  vx_terminal, engine rpm, engine OUTPUT torque (GetOutputMotorshaftTorque),
  current gear + ratio, driveshaft torque (GetOutputDriveshaftTorque),
  driven spindle torque (GetSpindleTorque, summed over driven=FRONT wheels),
  per-wheel longitudinal tyre Fx for ALL FOUR wheels (ReportTireForce, terrain/global frame -> body
    long via the chassis yaw, which is ~0 in a straight run) + long. slip + slip angle + Fz,
  TOTAL RESISTANCE measured INDEPENDENTLY as the coast deceleration when throttle->0 at the plateau
    speed (drag+rolling+driveline-drag = m * a_coast), NOT assumed.

Run (chrono env):
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/instrument_cruise_forcebalance.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_cruise_forcebalance.npz"

MU = 1.0          # HIGH-mu cruise operating point (the residual)
DT = 1e-3
INIT_Z = 0.3266
GRAVITY = 9.81
THROTTLES = [0.08, 0.12, 0.15]
# The residual is a REPLAY operating point: the car is ALREADY cruising at ~9.5 m/s and holds a
# partial throttle. So we SPIN UP to a seed speed first, THEN hold the target throttle and let it
# settle to its terminal (which may be above OR below the seed). Launch-from-rest at thr<=0.12
# stalls (engine idles, never rolls), which is NOT the operating point of interest.
SPIN_UP_TO = 9.5         # seed the car at the replay cruise speed, then hold the target throttle
SETTLE_STEPS = 300
MAX_STEPS = 90000
TERMINAL_ACCEL = 0.02    # |a| below this for a sustained window => terminal velocity
TERMINAL_HOLD = 3000     # ~3 s of near-zero accel
SMOOTH_K = 100           # vx smoothing window for plateau detection


def build_car():
    veh.SetDataPath(chrono.GetChronoDataPath() + "vehicle/")
    car = veh.Sedan()
    car.SetContactMethod(chrono.ChContactMethod_NSC)
    car.SetChassisFixed(False)
    car.SetChassisCollisionType(veh.CollisionType_NONE)
    car.SetInitPosition(chrono.ChCoordsysd(chrono.ChVector3d(0, 0, INIT_Z), chrono.QUNIT))
    car.SetTireType(veh.TireModelType_TMEASY)
    car.SetTireStepSize(DT)
    car.Initialize()
    return car


def _body_long_vel(body):
    return float(body.GetRot().RotateBack(body.GetPosDt()).x)


def _wheel_tyre_terms(vehicle, terrain, body, axle, side):
    """Return (Fx_body, Fy_body, Fz, long_slip, slip_angle) for one wheel.

    ReportTireForce returns the contact force in the GLOBAL/terrain frame. In a straight run the
    chassis yaw ~0, so global-x ~ body-longitudinal-x; we still rotate by the body yaw to be exact."""
    tire = vehicle.GetTire(axle, side)
    tf = tire.ReportTireForce(terrain)
    fg = tf.force                      # global frame
    # rotate global force into the body (chassis) frame
    fb = body.GetRot().RotateBack(fg)  # ChVector3d in body frame
    return float(fb.x), float(fb.y), float(fg.z), float(tire.GetLongitudinalSlip()), float(tire.GetSlipAngle())


def run_throttle(thr):
    car = build_car()
    vehicle = car.GetVehicle()
    body = vehicle.GetChassisBody()
    mass = float(vehicle.GetMass())
    r_eff = float(vehicle.GetTire(0, veh.LEFT).GetRadius())
    eng = vehicle.GetEngine()
    trans = vehicle.GetTransmission()
    dl = vehicle.GetDriveline()
    driven = list(dl.GetDrivenAxleIndexes())
    driven_sides = [(ai, veh.LEFT) for ai in driven] + [(ai, veh.RIGHT) for ai in driven]
    gear_ratio_map = None  # filled from chrono if available
    terrain = veh.FlatTerrain(0.0, MU)

    inp = veh.DriverInputs()
    inp.m_steering = 0.0
    inp.m_braking = 0.0

    t = 0.0
    # settle at zero throttle
    inp.m_throttle = 0.0
    for _ in range(SETTLE_STEPS):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT

    # ---- SPIN UP to the replay cruise speed with a closed-loop throttle, THEN hold thr ----
    for _ in range(40000):
        v = _body_long_vel(body)
        if v >= SPIN_UP_TO:
            break
        inp.m_throttle = float(min(max(0.5 * (SPIN_UP_TO - v), 0.15), 1.0))
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT

    inp.m_throttle = float(thr)
    v_prev = _body_long_vel(body)
    vbuf = []
    samples = []   # (v, a, rpm, gear, T_eng_out, T_ds, T_sp_driven,
                   #  FxFL,FxFR,FxRL,FxRR, FyFL..RR, FzFL..RR, slipFL..RR, alphaFL..RR)
    terminal_v = None
    hold = 0
    for step in range(MAX_STEPS):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
        v = _body_long_vel(body)
        a = (v - v_prev) / DT
        v_prev = v
        vbuf.append(v)

        rpm = float(eng.GetMotorSpeed()) * 60.0 / (2.0 * np.pi)
        T_eng = float(eng.GetOutputMotorshaftTorque())
        gear = int(trans.GetCurrentGear())
        T_ds = float(trans.GetOutputDriveshaftTorque())
        T_sp = float(sum(dl.GetSpindleTorque(ai, sd) for ai, sd in driven_sides))
        # per-wheel tyre terms (axle 0 = front, axle 1 = rear)
        fl = _wheel_tyre_terms(vehicle, terrain, body, 0, veh.LEFT)
        fr = _wheel_tyre_terms(vehicle, terrain, body, 0, veh.RIGHT)
        rl = _wheel_tyre_terms(vehicle, terrain, body, 1, veh.LEFT)
        rr = _wheel_tyre_terms(vehicle, terrain, body, 1, veh.RIGHT)
        samples.append((
            v, a, rpm, gear, T_eng, T_ds, T_sp,
            fl[0], fr[0], rl[0], rr[0],            # Fx FL FR RL RR
            fl[1], fr[1], rl[1], rr[1],            # Fy
            fl[2], fr[2], rl[2], rr[2],            # Fz
            fl[3], fr[3], rl[3], rr[3],            # long slip
            fl[4], fr[4], rl[4], rr[4],            # slip angle
        ))

        # smoothed plateau detection
        if len(vbuf) >= SMOOTH_K:
            vsm = np.mean(vbuf[-SMOOTH_K:])
            asm = (vbuf[-1] - vbuf[-SMOOTH_K]) / (SMOOTH_K * DT)
            if abs(asm) < TERMINAL_ACCEL and vsm > 3.0:
                hold += 1
                if hold > TERMINAL_HOLD:
                    terminal_v = float(vsm)
                    break
            else:
                hold = 0

    samples = np.asarray(samples, dtype=np.float64)
    # if we never flagged terminal, take the last second
    if terminal_v is None and len(samples):
        terminal_v = float(np.mean(samples[-1000:, 0]))

    # ---- INDEPENDENT RESISTANCE: coast from the plateau (throttle->0, no brake) ----
    coast_v, coast_t = [], []
    inp.m_throttle = 0.0
    inp.m_braking = 0.0
    v0c = _body_long_vel(body)
    for _ in range(8000):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
        coast_v.append(_body_long_vel(body)); coast_t.append(t)
        if coast_v[-1] < v0c - 3.0 or coast_v[-1] < 2.0:
            break
    coast_v = np.asarray(coast_v); coast_t = np.asarray(coast_t)

    return dict(thr=thr, mass=mass, r_eff=r_eff, samples=samples, terminal_v=terminal_v,
                driven=driven, coast_v=coast_v, coast_t=coast_t, v0_coast=v0c)


def plateau_terms(s, v_target, band=0.4):
    """Median of all force-balance terms in a +/- band around v_target (the plateau)."""
    v = s["samples"][:, 0]
    win = (v >= v_target - band) & (v <= v_target + band)
    if win.sum() < 5:
        # fall back to the last 500 samples
        win = np.zeros(len(v), dtype=bool); win[-500:] = True
    S = s["samples"][win]
    med = lambda i: float(np.median(S[:, i]))
    return dict(
        n=int(win.sum()), v=med(0), a=med(1), rpm=med(2), gear=int(np.round(med(3))),
        T_eng=med(4), T_ds=med(5), T_sp=med(6),
        Fx_FL=med(7), Fx_FR=med(8), Fx_RL=med(9), Fx_RR=med(10),
        Fy_FL=med(11), Fy_FR=med(12), Fy_RL=med(13), Fy_RR=med(14),
        Fz_FL=med(15), Fz_FR=med(16), Fz_RL=med(17), Fz_RR=med(18),
        slip_FL=med(19), slip_FR=med(20), slip_RL=med(21), slip_RR=med(22),
        alpha_FL=med(23), alpha_FR=med(24), alpha_RL=med(25), alpha_RR=med(26),
    )


def coast_resistance(s, v_target, halfband=0.6):
    """Measured resistance force at v_target from the coast: F_res = m * (-dv/dt) near v_target."""
    cv = s["coast_v"]; ct = s["coast_t"]
    if len(cv) < 20:
        return None
    k = 15
    vsm = np.convolve(cv, np.ones(k) / k, mode="same")
    a = -np.gradient(vsm, ct)        # decel (positive)
    lo, hi = k, len(vsm) - k
    vsm = vsm[lo:hi]; a = a[lo:hi]
    win = (vsm >= v_target - halfband) & (vsm <= v_target + halfband) & (a > 0)
    if win.sum() < 3:
        # nearest 30 points to v_target
        idx = np.argsort(np.abs(vsm - v_target))[:30]
        win = np.zeros(len(vsm), dtype=bool); win[idx] = True
        win &= (a > 0)
    a_res = float(np.median(a[win]))
    F_res = s["mass"] * a_res
    return dict(a_res=a_res, F_res=F_res, n=int(win.sum()), v=float(np.median(vsm[win])))


def main():
    print("=== Chrono Sedan CRUISE FORCE BALANCE @ mu=%.2f (isolated veh.Sedan()+TMeasy) ===" % MU)
    car = build_car(); vehicle = car.GetVehicle()
    dl = vehicle.GetDriveline()
    driven = list(dl.GetDrivenAxleIndexes())
    fx = float(vehicle.GetWheel(0, veh.LEFT).GetPos().x); rx = float(vehicle.GetWheel(1, veh.LEFT).GetPos().x)
    print("  driveline=%s driven_axle=%s axle0_x=%.3f axle1_x=%.3f -> DRIVEN=%s" % (
        dl.GetTemplateName(), driven, fx, rx, "FRONT" if (0 in driven and fx > rx) else "REAR"))
    del car, vehicle, dl

    results = {}
    out_blobs = {}
    for thr in THROTTLES:
        s = run_throttle(thr)
        results[thr] = s
        vt = s["terminal_v"]
        P = plateau_terms(s, vt)
        R = coast_resistance(s, vt)
        results[thr]["plateau"] = P
        results[thr]["resist"] = R

        Fx_front = P["Fx_FL"] + P["Fx_FR"]
        Fx_rear = P["Fx_RL"] + P["Fx_RR"]
        Fx_total = Fx_front + Fx_rear
        Fy_front = P["Fy_FL"] + P["Fy_FR"]
        Fz_front = P["Fz_FL"] + P["Fz_FR"]
        Fz_rear = P["Fz_RL"] + P["Fz_RR"]

        print("\n========== THROTTLE %.2f  ==========" % thr)
        print("  TERMINAL vx        = %.3f m/s   (plateau accel %.4f m/s^2, n=%d)" % (vt, P["a"], P["n"]))
        print("  engine rpm         = %.0f" % P["rpm"])
        print("  engine OUT torque  = %.2f N.m   (GetOutputMotorshaftTorque)" % P["T_eng"])
        print("  gear (Chrono 1-idx)= %d" % P["gear"])
        print("  driveshaft torque  = %.2f N.m   (GetOutputDriveshaftTorque)" % P["T_ds"])
        print("  driven spindle Tq  = %.2f N.m   (sum FRONT L/R)" % P["T_sp"])
        print("  --- per-wheel longitudinal tyre Fx (body frame, N) ---")
        print("    FL=%+.1f  FR=%+.1f  RL=%+.1f  RR=%+.1f" % (P["Fx_FL"], P["Fx_FR"], P["Fx_RL"], P["Fx_RR"]))
        print("    FRONT Fx = %+.1f   REAR Fx = %+.1f   TOTAL Fx = %+.1f N" % (Fx_front, Fx_rear, Fx_total))
        print("  --- per-wheel lateral Fy / normal Fz / long-slip / slip-angle ---")
        print("    Fy: FL=%+.0f FR=%+.0f RL=%+.0f RR=%+.0f  (front sum %.0f)" % (
            P["Fy_FL"], P["Fy_FR"], P["Fy_RL"], P["Fy_RR"], Fy_front))
        print("    Fz: FL=%.0f FR=%.0f RL=%.0f RR=%.0f  (front %.0f rear %.0f)" % (
            P["Fz_FL"], P["Fz_FR"], P["Fz_RL"], P["Fz_RR"], Fz_front, Fz_rear))
        print("    long-slip kappa: FL=%.4f FR=%.4f RL=%.4f RR=%.4f" % (
            P["slip_FL"], P["slip_FR"], P["slip_RL"], P["slip_RR"]))
        print("    slip-angle alpha: FL=%.4f FR=%.4f RL=%.4f RR=%.4f" % (
            P["alpha_FL"], P["alpha_FR"], P["alpha_RL"], P["alpha_RR"]))
        if R:
            print("  --- INDEPENDENT RESISTANCE (coast decel at plateau, throttle->0) ---")
            print("    coast decel = %.4f m/s^2 @ %.2f m/s -> F_res = %.1f N (mass %.1f, n=%d)" % (
                R["a_res"], R["v"], R["F_res"], s["mass"], R["n"]))
            print("    implied Crr (a_res/g, drag=0) = %.5f" % (R["a_res"] / GRAVITY))
        print("  --- FORCE-BALANCE CHECK at terminal (should be ~0) ---")
        Fnet = Fx_total - (R["F_res"] if R else 0.0)
        print("    drive Fx_total (%.0f) - resistance (%.0f) = %.1f N  (m*a = %.1f N)" % (
            Fx_total, R["F_res"] if R else float("nan"), Fnet, s["mass"] * P["a"]))

        out_blobs[f"thr_{thr:.2f}".replace('.', 'p') + "_samples"] = s["samples"]
        out_blobs[f"thr_{thr:.2f}".replace('.', 'p') + "_coast_v"] = s["coast_v"]
        out_blobs[f"thr_{thr:.2f}".replace('.', 'p') + "_coast_t"] = s["coast_t"]

    # ---- also evaluate every throttle's force balance at MATCHED speeds 9.5 and 11.0 ----
    print("\n\n=== TERM-BY-TERM at MATCHED speeds (for Chrono-vs-model compare) ===")
    match_rows = {}
    for thr in THROTTLES:
        s = results[thr]
        for vq in (9.5, 11.0):
            P = plateau_terms(s, vq, band=0.5)
            if P["n"] < 5:
                continue
            R = coast_resistance(s, vq)
            Fxf = P["Fx_FL"] + P["Fx_FR"]; Fxr = P["Fx_RL"] + P["Fx_RR"]
            print("  thr %.2f @ v=%.1f: gear%d rpm%.0f Teng=%.1f Tds=%.1f | Fx_front=%.0f Fx_rear=%.0f Fx_tot=%.0f"
                  " | F_res=%s a=%.3f" % (
                thr, vq, P["gear"], P["rpm"], P["T_eng"], P["T_ds"], Fxf, Fxr, Fxf + Fxr,
                ("%.0f" % R["F_res"]) if R else "n/a", P["a"]))
            match_rows[f"thr{thr:.2f}_v{vq:.1f}"] = dict(P=P, R=R)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    summary = {}
    for thr in THROTTLES:
        P = results[thr]["plateau"]; R = results[thr]["resist"]
        for k, val in P.items():
            summary[f"thr{thr:.2f}_{k}"] = val
        if R:
            for k, val in R.items():
                summary[f"thr{thr:.2f}_res_{k}"] = val
        summary[f"thr{thr:.2f}_terminal_v"] = results[thr]["terminal_v"]
    np.savez(OUT, mu=MU, mass=results[THROTTLES[0]]["mass"], r_eff=results[THROTTLES[0]]["r_eff"],
             gravity=GRAVITY, throttles=np.asarray(THROTTLES),
             **{k: np.asarray(v) for k, v in summary.items()}, **out_blobs)
    print("\nsaved %s" % OUT)


if __name__ == "__main__":
    main()
