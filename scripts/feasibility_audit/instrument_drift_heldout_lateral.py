"""DIAGNOSIS: instrument the EXACT held-out drift scenarios (idx[130:]) in real Chrono and log
the FULL lateral/yaw force-balance terms, to root-cause the honest drift beta@24 residual.

This extends instrument_drift_fz_chrono.py to the held-out split (np.random.default_rng(0).
permutation(160)[130:], the same split gpu_pwr3_gate.py uses), and adds the FRONT per-wheel slip
angle + the per-axle lateral force + the yaw moment (lf*Fy_f - lr*Fy_r) so the pwr3-vs-Chrono
lateral balance can be decomposed term-by-term at the saddle (steps 10-30).

Output: runs/feasibility_audit/phase4_f2/drift_heldout_lateral_chrono.npz
  per scenario/step: chrono vx,vy,wz,ax,ay,roll,pitch, replayed steer/throttle/brake,
  per-wheel Fz [FL,FR,RL,RR], per-wheel Fy [FL,FR,RL,RR], per-wheel slip angle [FL,FR,RL,RR],
  per-wheel longitudinal slip [FL,FR,RL,RR].

Run in the pinned chrono env:
  conda run --no-capture-output -n chrono python \
      scripts/feasibility_audit/instrument_drift_heldout_lateral.py
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
OUT = ROOT / "runs/feasibility_audit/phase4_f2/drift_heldout_lateral_chrono.npz"

DT = 0.02
INTERNAL_STEP = 1e-3
SUBSTEPS = int(round(DT / INTERNAL_STEP))
SPINUP_TERRAIN_MU = 1.0
INIT_CHASSIS_Z = 0.23
SPINUP_SETTLE_STEPS = 300

MU = 0.48
MASS = 1684.0
MAX_STEER = 0.62
MAX_STEER_RATE = 3.5
STEER_TAU = 0.06
DRIVE_TAU = 0.08
MAX_DRIVE_FORCE = 8200.0
MAX_BRAKE_FORCE = 6000.0

CORNERS = (("FL", 0, veh.LEFT), ("FR", 0, veh.RIGHT),
           ("RL", 1, veh.LEFT), ("RR", 1, veh.RIGHT))


def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def _move_towards(cur, tgt, max_delta):
    d = tgt - cur
    if d > max_delta:
        d = max_delta
    elif d < -max_delta:
        d = -max_delta
    return cur + d


class Replay:
    def __init__(self):
        veh.SetDataPath(chrono.GetChronoDataPath() + "vehicle/")
        self.car = None
        self.vehicle = None
        self.body = None
        self.terrain = None
        self.d_ref_local = None
        self.time = 0.0

    def build(self, init_vx, init_vy, init_w):
        target_speed = math.hypot(init_vx, init_vy)
        car = veh.Sedan()
        car.SetContactMethod(chrono.ChContactMethod_NSC)
        car.SetChassisFixed(False)
        car.SetChassisCollisionType(veh.CollisionType_NONE)
        car.SetInitPosition(chrono.ChCoordsysd(chrono.ChVector3d(0.0, 0.0, INIT_CHASSIS_Z), chrono.QUNIT))
        car.SetTireType(veh.TireModelType_TMEASY)
        car.SetTireStepSize(INTERNAL_STEP)
        car.Initialize()
        self.car = car
        self.vehicle = car.GetVehicle()
        self.body = self.vehicle.GetChassisBody()
        ref_pos = self.vehicle.GetPos()
        cog_pos = self.body.GetPos()
        self.d_ref_local = self.body.GetRot().RotateBack(ref_pos - cog_pos)

        base_vmass = float(self.vehicle.GetMass())
        base_cmass = float(self.body.GetMass())
        non_chassis = base_vmass - base_cmass
        self.body.SetMass(max(MASS - non_chassis, 50.0))

        spin_terrain = veh.FlatTerrain(0.0, SPINUP_TERRAIN_MU)
        self.time = 0.0
        inp = veh.DriverInputs()
        inp.m_steering = 0.0
        inp.m_throttle = 0.0
        inp.m_braking = 0.0
        body = self.body
        n = 0
        while n < 40000:
            if n >= SPINUP_SETTLE_STEPS:
                v_now = body.GetRot().RotateBack(body.GetPosDt()).x
                if v_now >= target_speed:
                    break
                inp.m_throttle = float(_clamp(0.5 * (target_speed - v_now), 0.05, 0.85))
            car.Synchronize(self.time, inp, spin_terrain)
            spin_terrain.Synchronize(self.time)
            car.Advance(INTERNAL_STEP)
            spin_terrain.Advance(INTERNAL_STEP)
            self.time += INTERNAL_STEP
            n += 1

        self._teleport_boost(70.0, 0.0, 1.4806710500291282, init_vx, init_vy, init_w)
        self.terrain = veh.FlatTerrain(0.0, MU)

    def _teleport_boost(self, x, y, psi, vx, vy, yaw_rate):
        body = self.body
        system = self.vehicle.GetSystem()
        bodies = list(system.GetBodies())
        e = body.GetRot().Rotate(chrono.ChVector3d(1.0, 0.0, 0.0))
        psi_cur = math.atan2(e.y, e.x)
        qd = chrono.QuatFromAngleZ(psi - psi_cur)
        ref_cur = body.GetPos() + body.GetRot().Rotate(self.d_ref_local)
        ref_tgt = chrono.ChVector3d(x, y, ref_cur.z)
        for b in bodies:
            rel = b.GetPos() - ref_cur
            b.SetPos(ref_tgt + qd.Rotate(rel))
            b.SetRot(qd * b.GetRot())
            b.SetPosDt(qd.Rotate(b.GetPosDt()))
            b.SetAngVelParent(qd.Rotate(b.GetAngVelParent()))
        rot_new = body.GetRot()
        v_des = rot_new.Rotate(chrono.ChVector3d(vx, vy, 0.0))
        v_cur = body.GetPosDt()
        dv = chrono.ChVector3d(v_des.x - v_cur.x, v_des.y - v_cur.y, 0.0)
        w_cur = body.GetAngVelParent()
        dw = chrono.ChVector3d(0.0, 0.0, yaw_rate - w_cur.z)
        pivot = body.GetPos()
        for b in bodies:
            r = b.GetPos() - pivot
            b.SetPosDt(b.GetPosDt() + dv + dw.Cross(r))
            b.SetAngVelParent(b.GetAngVelParent() + dw)

    def read_planar(self):
        body = self.body
        rot = body.GetRot()
        v_loc = rot.RotateBack(body.GetPosDt())
        wz = float(body.GetAngVelLocal().z)
        ex = rot.Rotate(chrono.ChVector3d(1, 0, 0))
        ey = rot.Rotate(chrono.ChVector3d(0, 1, 0))
        ez = rot.Rotate(chrono.ChVector3d(0, 0, 1))
        pitch = math.asin(max(-1.0, min(1.0, -ex.z)))
        roll = math.atan2(ey.z, ez.z)
        return float(v_loc.x), float(v_loc.y), wz, roll, pitch

    def read_tires(self):
        """Per-wheel (Fz, Fy_wheel_local, slip_angle, long_slip) for FL,FR,RL,RR."""
        out = {}
        for name, axle, side in CORNERS:
            tire = self.vehicle.GetTire(axle, side)
            fr = tire.ReportTireForce(self.terrain)
            f = fr.force
            wheel = self.vehicle.GetWheel(axle, side)
            ws = wheel.GetState()
            lf = ws.rot.RotateBack(f)  # wheel-local force
            out[name] = (
                float(abs(f.z)),
                float(lf.y),
                float(tire.GetSlipAngle()),
                float(tire.GetLongitudinalSlip()),
            )
        return out


def main():
    d = np.load(DATA, allow_pickle=True)
    actions_all = d["actions"]
    chrono_v_all = d["chrono_v"]
    init_all = d["init"]

    # the EXACT held-out split the gate uses
    idx = np.random.default_rng(0).permutation(len(actions_all))
    sel = idx[130:]
    print("held-out scenarios (%d):" % len(sel), list(int(s) for s in sel), flush=True)

    results = {}
    repro_err = []
    for si in sel:
        si = int(si)
        actions = np.asarray(actions_all[si], dtype=float)
        cv = np.asarray(chrono_v_all[si], dtype=float)
        T = actions.shape[0]
        vx0, vy0, w0 = float(init_all[si][0]), float(init_all[si][1]), float(init_all[si][2])

        rep = Replay()
        rep.build(vx0, vy0, w0)

        steer_state = 0.0
        drive_force_state = 0.0
        rows = []
        for k in range(T):
            a = actions[k]
            steer_cmd = _clamp(float(a[0]), -1.0, 1.0) * MAX_STEER
            throttle_cmd = 0.5 * (_clamp(float(a[1]), -1.0, 1.0) + 1.0)
            brake_cmd = 0.5 * (_clamp(float(a[2]), -1.0, 1.0) + 1.0)
            steer_rate_limit = MAX_STEER_RATE * DT
            steer_lag = _clamp(DT / max(STEER_TAU, DT), 0.0, 1.0)
            steer_target = steer_state + (steer_cmd - steer_state) * steer_lag
            steer_state = _move_towards(steer_state, steer_target, steer_rate_limit)
            force_target = throttle_cmd * MAX_DRIVE_FORCE - brake_cmd * MAX_BRAKE_FORCE
            drive_alpha = _clamp(DT / max(DRIVE_TAU, DT), 0.0, 1.0)
            drive_force_state += (force_target - drive_force_state) * drive_alpha

            inp = veh.DriverInputs()
            inp.m_steering = float(_clamp(steer_state / MAX_STEER, -1.0, 1.0))
            if drive_force_state >= 0.0:
                inp.m_throttle = float(_clamp(drive_force_state / MAX_DRIVE_FORCE, 0.0, 1.0))
                inp.m_braking = 0.0
            else:
                inp.m_throttle = 0.0
                inp.m_braking = float(_clamp(-drive_force_state / MAX_BRAKE_FORCE, 0.0, 1.0))

            prev_vx, prev_vy, _, _, _ = rep.read_planar()
            for _ in range(SUBSTEPS):
                rep.car.Synchronize(rep.time, inp, rep.terrain)
                rep.terrain.Synchronize(rep.time)
                rep.car.Advance(INTERNAL_STEP)
                rep.terrain.Advance(INTERNAL_STEP)
                rep.time += INTERNAL_STEP

            vx, vy, wz, roll, pitch = rep.read_planar()
            ax = (vx - prev_vx) / DT
            ay = (vy - prev_vy) / DT
            tr = rep.read_tires()
            rows.append((
                vx, vy, wz, ax, ay, roll, pitch,
                inp.m_steering * MAX_STEER, inp.m_throttle, inp.m_braking,
                tr["FL"][0], tr["FR"][0], tr["RL"][0], tr["RR"][0],   # Fz
                tr["FL"][1], tr["FR"][1], tr["RL"][1], tr["RR"][1],   # Fy (wheel-local)
                tr["FL"][2], tr["FR"][2], tr["RL"][2], tr["RR"][2],   # slip angle
                tr["FL"][3], tr["FR"][3], tr["RL"][3], tr["RR"][3],   # long slip
            ))
        arr = np.array(rows, dtype=np.float64)
        results[f"sc{si}"] = arr
        vx_err = np.abs(arr[:, 0] - cv[:, 0]).mean()
        vy_err = np.abs(arr[:, 1] - cv[:, 1]).mean()
        repro_err.append((int(si), vx_err, vy_err))
        print(f"sc{si}: T={T}  vx_MAE={vx_err:.4f}  vy_MAE={vy_err:.4f}", flush=True)
        rep.car.GetSystem().Clear()
        rep.car = None

    cols = ("vx", "vy", "wz", "ax", "ay", "roll", "pitch",
            "steer", "throttle", "brake",
            "Fz_FL", "Fz_FR", "Fz_RL", "Fz_RR",
            "Fy_FL", "Fy_FR", "Fy_RL", "Fy_RR",
            "alpha_FL", "alpha_FR", "alpha_RL", "alpha_RR",
            "sx_FL", "sx_FR", "sx_RL", "sx_RR")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, columns=np.array(cols), repro_err=np.array(repro_err),
             held_out=np.array(list(int(s) for s in sel)), mu=MU, mass=MASS, **results)
    print(f"\nsaved {OUT}", flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
