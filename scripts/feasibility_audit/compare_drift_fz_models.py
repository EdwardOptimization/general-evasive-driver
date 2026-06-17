"""Compare Chrono per-wheel Fz (instrumented) vs planar quasi-static vs Tier-a dynamic.

Loads the instrumented Chrono drift transient (drift_fz_instrumented.npz) and, at the SAME
measured Chrono states (ax, ay) / replayed actions, computes:
  (a) PLANAR quasi-static per-wheel Fz via gpu_physics_pwr._normal_loads(ax,ay)   [exact pwr law]
  (b) TIER-A dynamic per-wheel Fz by running gpu_vehicle_tier_a along the SAME action sequence
      and reading its per-corner load each step.

Then quantifies, at the drift-entry steps, whether Chrono's actual REAR load (and its transient
RATE) is closer to the planar quasi-static or the Tier-a dynamic, and decomposes the Tier-a roll
load transfer (its roll-stiffness / roll angle vs Chrono's) to test the ARB / roll-center / tyre
hypotheses.

Run in base env (torch + autodrift):  PYTHONPATH=src python scripts/feasibility_audit/compare_drift_fz_models.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from autodrift import gpu_physics_pwr as pwr
from autodrift import gpu_vehicle_tier_a as tier_a

INSTR = ROOT / "runs/feasibility_audit/phase4_f2/drift_fz_instrumented.npz"
DT = 0.02
MU = 0.48


def planar_qs_loads(ax, ay):
    """Planar quasi-static per-wheel Fz at body accelerations ax,ay [N,] -> 4 arrays [N]."""
    P = pwr.make_phys_param_batch(pwr.PhysParams(), n=len(ax), mu=MU)
    axt = torch.tensor(ax, dtype=torch.float32)
    ayt = torch.tensor(ay, dtype=torch.float32)
    fl, fr, rl, rr = pwr._normal_loads(axt, ayt, P)
    return (fl.numpy(), fr.numpy(), rl.numpy(), rr.numpy())


def tier_a_rollout(actions, vx0, vy0, w0):
    """Run the Tier-a model along the action sequence; return per-step per-corner Fz + roll/pitch."""
    P = tier_a.make_tier_a_param_batch(tier_a.TierAParams(), n=1, mu=MU)
    vx = torch.tensor([vx0], dtype=torch.float32)
    vy = torch.tensor([vy0], dtype=torch.float32)
    w = torch.tensor([w0], dtype=torch.float32)
    st, gear = tier_a.init_state(vx, vy, w, P)
    fz_log, roll_log, pitch_log, vx_log, vy_log = [], [], [], [], []
    for k in range(len(actions)):
        a = torch.tensor(actions[k:k+1], dtype=torch.float32)
        st, gear, diag = tier_a.physics_step(st, a, gear, P, DT)
        fz = diag["fz"][0].numpy()  # [4] FL,FR,RL,RR
        fz_log.append(fz)
        roll_log.append(float(st[0, tier_a.IDX["roll"]]))
        pitch_log.append(float(st[0, tier_a.IDX["pitch"]]))
        vx_log.append(float(st[0, tier_a.IDX["vx"]]))
        vy_log.append(float(st[0, tier_a.IDX["vy"]]))
    return (np.array(fz_log), np.array(roll_log), np.array(pitch_log),
            np.array(vx_log), np.array(vy_log))


def main():
    d = np.load(INSTR, allow_pickle=True)
    cols = [str(c) for c in d["columns"]]
    ci = {c: i for i, c in enumerate(cols)}
    scenarios = [k for k in d.files if k.startswith("sc")]

    # load init from drift data for tier-a rollout seeding
    drift = np.load(ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz", allow_pickle=True)
    init_all = drift["init"]
    actions_all = drift["actions"]

    print("=" * 100)
    print("PER-WHEEL Fz: Chrono (measured) vs Planar quasi-static vs Tier-a dynamic, at drift entry")
    print("mu =", MU, " (rear axle static ~4030 N/wheel)")
    print("=" * 100)

    # aggregate over scenarios
    agg = {"rear_total": {"chrono": [], "planar": [], "tiera": []},
           "rear_split": {"chrono": [], "planar": [], "tiera": []},  # |Fz_RL - Fz_RR|
           "roll": {"chrono_proxy": [], "tiera": []}}
    rate_agg = {"chrono": [], "planar": [], "tiera": []}  # d(rear_split)/dt over steps 0..8

    for sk in scenarios:
        si = int(sk[2:])
        arr = d[sk]
        T = arr.shape[0]
        ax = arr[:, ci["ax"]]
        ay = arr[:, ci["ay"]]
        roll = arr[:, ci["roll"]]
        # Chrono measured loads
        c_FL, c_FR = arr[:, ci["Fz_FL"]], arr[:, ci["Fz_FR"]]
        c_RL, c_RR = arr[:, ci["Fz_RL"]], arr[:, ci["Fz_RR"]]
        # planar quasi-static at Chrono's ax,ay
        p_FL, p_FR, p_RL, p_RR = planar_qs_loads(ax, ay)
        # tier-a rollout
        vx0, vy0, w0 = float(init_all[si][0]), float(init_all[si][1]), float(init_all[si][2])
        ta_fz, ta_roll, ta_pitch, ta_vx, ta_vy = tier_a_rollout(np.asarray(actions_all[si], float), vx0, vy0, w0)
        t_FL, t_FR, t_RL, t_RR = ta_fz[:, 0], ta_fz[:, 1], ta_fz[:, 2], ta_fz[:, 3]

        # rear split (lateral load transfer at rear axle) = |RL - RR|
        c_split = np.abs(c_RL - c_RR)
        p_split = np.abs(p_RL - p_RR)
        t_split = np.abs(t_RL - t_RR)
        c_rtot = c_RL + c_RR
        p_rtot = p_RL + p_RR
        t_rtot = t_RL + t_RR

        # collect drift-entry window steps 0..11 + step 24
        win = list(range(0, 12)) + [24]
        for k in win:
            if k >= T:
                continue
            agg["rear_total"]["chrono"].append(c_rtot[k])
            agg["rear_total"]["planar"].append(p_rtot[k])
            agg["rear_total"]["tiera"].append(t_rtot[k])
            agg["rear_split"]["chrono"].append(c_split[k])
            agg["rear_split"]["planar"].append(p_split[k])
            agg["rear_split"]["tiera"].append(t_split[k])
            agg["roll"]["chrono_proxy"].append(np.degrees(roll[k]))
            agg["roll"]["tiera"].append(np.degrees(ta_roll[k]))

        # transient RATE: rear-split build rate over the first 8 steps (N per step)
        rate_agg["chrono"].append((c_split[8] - c_split[0]) / 8.0)
        rate_agg["planar"].append((p_split[8] - p_split[0]) / 8.0)
        rate_agg["tiera"].append((t_split[8] - t_split[0]) / 8.0)

        if si == int(scenarios[0][2:]):
            print(f"\n--- scenario {si}: per-step rear lateral load split |Fz_RL - Fz_RR| [N] ---")
            print("step |  ax    ay   | Chrono  Planar  Tier-a | Chrono_roll  Tiera_roll [deg]")
            for k in win:
                if k >= T:
                    continue
                print(f"{k:4d} | {ax[k]:5.2f} {ay[k]:5.2f} | {c_split[k]:6.0f} {p_split[k]:7.0f} {t_split[k]:7.0f} |"
                      f" {np.degrees(roll[k]):10.2f} {np.degrees(ta_roll[k]):11.2f}")

    def stats(x):
        x = np.array(x)
        return x.mean(), x.std()

    print("\n" + "=" * 100)
    print("AGGREGATE over %d scenarios, drift-entry window (steps 0-11 + 24)" % len(scenarios))
    print("=" * 100)
    for metric in ("rear_total", "rear_split"):
        cm, cs = stats(agg[metric]["chrono"])
        pm, ps = stats(agg[metric]["planar"])
        tm, ts = stats(agg[metric]["tiera"])
        print(f"\n{metric}:")
        print(f"  Chrono : {cm:8.0f} +/- {cs:6.0f} N")
        print(f"  Planar : {pm:8.0f} +/- {ps:6.0f} N   (err vs Chrono: {pm-cm:+8.0f} N, {100*(pm-cm)/cm:+.1f}%)")
        print(f"  Tier-a : {tm:8.0f} +/- {ts:6.0f} N   (err vs Chrono: {tm-cm:+8.0f} N, {100*(tm-cm)/cm:+.1f}%)")
        # which is closer (per-sample MAE)
        c = np.array(agg[metric]["chrono"])
        pe = np.abs(np.array(agg[metric]["planar"]) - c).mean()
        te = np.abs(np.array(agg[metric]["tiera"]) - c).mean()
        print(f"  MAE vs Chrono:  Planar={pe:.0f} N   Tier-a={te:.0f} N   -> {'PLANAR' if pe<te else 'TIER-A'} closer")

    print("\nrear-split TRANSIENT RATE (build rate over steps 0->8, N/step):")
    cm, cs = stats(rate_agg["chrono"])
    pm, ps = stats(rate_agg["planar"])
    tm, ts = stats(rate_agg["tiera"])
    print(f"  Chrono : {cm:+8.1f} +/- {cs:5.1f} N/step")
    print(f"  Planar : {pm:+8.1f} +/- {ps:5.1f} N/step")
    print(f"  Tier-a : {tm:+8.1f} +/- {ts:5.1f} N/step")

    rm, rs = stats(agg["roll"]["chrono_proxy"])
    trm, trs = stats(agg["roll"]["tiera"])
    print("\nroll angle [deg]:")
    print(f"  Chrono : {rm:+.3f} +/- {rs:.3f}")
    print(f"  Tier-a : {trm:+.3f} +/- {trs:.3f}  (ratio Tiera/Chrono = {trm/rm if rm!=0 else float('nan'):.2f})")


if __name__ == "__main__":
    main()
