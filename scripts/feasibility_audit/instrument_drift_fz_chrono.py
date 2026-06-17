"""Instrument the Chrono Sedan during the E4 drift maneuver: per-wheel Fz + rear Fy.

Replays the RECORDED drift-oracle action sequences (surrogate_drift_data.npz) through a
faithful reconstruction of ChronoVehicleBackend (same build / spin-up / teleport-boost /
actuator filter / substep loop, mu=0.48) and at EVERY control step reads the real Chrono
per-wheel vertical load Fz and lateral force Fy from tire.ReportTireForce(terrain), plus the
chassis state (vx,vy,wz,ax,ay,roll,pitch) needed to re-evaluate the planar quasi-static and
Tier-a per-wheel Fz at the SAME states offline.

Output: runs/feasibility_audit/phase4_f2/drift_fz_instrumented.npz  with, per scenario/step:
  chrono per-wheel Fz [FL,FR,RL,RR], chrono per-wheel Fy, rear axle Fy, slip angles,
  chassis vx,vy,wz,ax,ay,roll,pitch, and the replayed (filtered) steer/throttle/brake.

Run in the pinned chrono env:
  conda run --no-capture-output -n chrono python \
      scripts/feasibility_audit/instrument_drift_fz_chrono.py
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
OUT = ROOT / "runs/feasibility_audit/phase4_f2/drift_fz_instrumented.npz"

DT = 0.02
INTERNAL_STEP = 1e-3
SUBSTEPS = int(round(DT / INTERNAL_STEP))
SPINUP_TERRAIN_MU = 1.0
INIT_CHASSIS_Z = 0.23  # backend default (near static ride height; measured equilibrium 0.2145)
SPINUP_SETTLE_STEPS = 300  # 0.3 s suspension settle before throttle (matches backend)

# scenario params (from f2._drift_scenario, printed earlier)
MU = 0.48
MASS = 1684.0
MAX_STEER = 0.62
MAX_STEER_RATE = 3.5
STEER_TAU = 0.06
DRIVE_TAU = 0.08
MAX_DRIVE_FORCE = 8200.0
MAX_BRAKE_FORCE = 6000.0

# corner -> (axle, side)
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

        # mass override (match total vehicle mass = MASS)
        base_vmass = float(self.vehicle.GetMass())
        base_cmass = float(self.body.GetMass())
        non_chassis = base_vmass - base_cmass
        self.body.SetMass(max(MASS - non_chassis, 50.0))

        # spin-up on high-friction terrain to target speed
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

        # teleport + velocity boost to the scenario initial state
        # scenario initial planar pose: x=70,y=0,psi from the cell; but for Fz we only need
        # vx,vy,yaw_rate (loads are pose-invariant on flat terrain). Use the recorded init.
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
        # roll/pitch from the chassis rotation (body x forward, y left, z up)
        # extract roll (about x) and pitch (about y) from the quaternion
        ex = rot.Rotate(chrono.ChVector3d(1, 0, 0))
        ey = rot.Rotate(chrono.ChVector3d(0, 1, 0))
        ez = rot.Rotate(chrono.ChVector3d(0, 0, 1))
        pitch = math.asin(max(-1.0, min(1.0, -ex.z)))
        roll = math.atan2(ey.z, ez.z)
        return float(v_loc.x), float(v_loc.y), wz, roll, pitch

    def read_tires(self):
        out = {}
        for name, axle, side in CORNERS:
            tire = self.vehicle.GetTire(axle, side)
            fr = tire.ReportTireForce(self.terrain)
            f = fr.force
            wheel = self.vehicle.GetWheel(axle, side)
            ws = wheel.GetState()
            lf = ws.rot.RotateBack(f)  # wheel-local force
            out[name] = (
                float(abs(f.z)),          # Fz (normal load, global z)
                float(lf.y),              # lateral force (wheel-local y)
                float(tire.GetSlipAngle()),
                float(tire.GetLongitudinalSlip()),
            )
        return out


def main():
    d = np.load(DATA, allow_pickle=True)
    actions_all = d["actions"]
    chrono_v_all = d["chrono_v"]
    init_all = d["init"]
    sigma = d["sigma"]
    clean = np.where(sigma == 0.0)[0]
    # take 8 clean drift-entry scenarios
    sel = clean[:8]

    results = {}
    repro_err = []
    for si in sel:
        actions = np.asarray(actions_all[si], dtype=float)   # [T,3]
        cv = np.asarray(chrono_v_all[si], dtype=float)        # [T,3] (vx,vy,yaw)
        T = actions.shape[0]
        vx0, vy0, w0 = float(init_all[si][0]), float(init_all[si][1]), float(init_all[si][2])

        rep = Replay()
        rep.build(vx0, vy0, w0)

        steer_state = 0.0
        drive_force_state = 0.0

        rows = []
        for k in range(T):
            a = actions[k]
            # actuator filter (mirror backend._update_actuators)
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
            tires = rep.read_tires()
            rows.append((
                vx, vy, wz, ax, ay, roll, pitch,
                inp.m_steering * MAX_STEER, inp.m_throttle, inp.m_braking,
                tires["FL"][0], tires["FR"][0], tires["RL"][0], tires["RR"][0],   # Fz
                tires["FL"][1], tires["FR"][1], tires["RL"][1], tires["RR"][1],   # Fy
                tires["RL"][2], tires["RR"][2],                                   # rear slip ang
                tires["RL"][3], tires["RR"][3],                                   # rear long slip
            ))
        arr = np.array(rows, dtype=np.float64)
        results[f"sc{si}"] = arr
        # reproduction check vs recorded chrono_v
        vx_err = np.abs(arr[:, 0] - cv[:, 0]).mean()
        vy_err = np.abs(arr[:, 1] - cv[:, 1]).mean()
        repro_err.append((int(si), vx_err, vy_err))
        print(f"sc{si}: replayed T={T}  vx_MAE={vx_err:.4f}  vy_MAE={vy_err:.4f}", flush=True)
        rep.car.GetSystem().Clear()
        rep.car = None

    cols = ("vx", "vy", "wz", "ax", "ay", "roll", "pitch",
            "steer", "throttle", "brake",
            "Fz_FL", "Fz_FR", "Fz_RL", "Fz_RR",
            "Fy_FL", "Fy_FR", "Fy_RL", "Fy_RR",
            "alpha_RL", "alpha_RR", "sx_RL", "sx_RR")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, columns=np.array(cols), repro_err=np.array(repro_err),
             mu=MU, mass=MASS, **results)
    print(f"\nsaved {OUT}", flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
