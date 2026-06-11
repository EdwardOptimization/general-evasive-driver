"""A2 observation-normalization audit for population work.

This is a zero-training measurement. It samples nominal and population-stress
vehicle instances, runs fixed scripted profiles, and reports obs72 channel
range/saturation against the current normalization constants. It proposes
normalization changes only; it does not apply them.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/obs_normalization_audit.py [--quick]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv
import autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight as m4


REPO = Path(__file__).resolve().parents[2]
PREREG = REPO / "experiments/feasibility_audit/obs_normalization_prereg.json"
RESULTS_JSON = REPO / "experiments/feasibility_audit/obs_normalization_audit.json"
RUN_DIR = REPO / "runs/feasibility_audit/obs_normalization_audit"
BASE = 20260813

TRACK_R = 60.0
GRAV = 9.81

CLAIM_BOUNDARY = (
    "Observation-normalization audit only. Zero training, no driver mutation, no "
    "driver-performance, validation ranking, promotion, high-fidelity sufficiency, "
    "paper, repair-success, robustness-result, feasibility-proof, or self-ID claim."
)

NICE_SCALES = np.array([1, 2, 2.5, 4, 5, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 160], dtype=float)

TIER_RANGES = {
    "S0_nominal": {
        "mass": (1.0, 1.0), "brake": (1.0, 1.0), "drive": (1.0, 1.0),
        "stiff": (1.0, 1.0), "tau": (1.0, 1.0), "cg": (0.0, 0.0),
        "inertia": (1.0, 1.0), "mu": (0.25, 1.15),
    },
    "C5_wide_current": {
        "mass": (0.70, 1.50), "brake": (0.60, 1.30), "drive": (0.60, 1.30),
        "stiff": (0.50, 1.50), "tau": (0.75, 2.50), "cg": (-0.42, 0.42),
        "inertia": (0.60, 1.60), "mu": (0.25, 1.15),
    },
    "S4_proxy_stress": {
        "mass": (0.62, 2.20), "brake": (0.55, 1.50), "drive": (0.55, 1.50),
        "stiff": (0.45, 1.60), "tau": (0.50, 3.00), "cg": (-0.42, 0.42),
        "inertia": (0.50, 2.00), "mu": (0.25, 1.15),
    },
}

PROFILES = {
    "mid_obstacle_arc": {
        "track_kind": "circle", "track_radius": 60.0, "speed": 16.0, "max_steps": 220,
        "obstacle": True, "s_arc": 30.0, "half_width": 1.0,
    },
    "high_speed_arc": {
        "track_kind": "circle", "track_radius": 250.0, "speed": 28.0, "max_steps": 220,
        "obstacle": False,
    },
    "figure8_context": {
        "track_kind": "figure_eight", "track_radius": 45.0, "speed": 14.0, "max_steps": 220,
        "obstacle": False,
    },
}


@dataclass(frozen=True)
class ChannelSpec:
    index: int
    name: str
    group: str
    divisor: float | None


def channel_specs() -> list[ChannelSpec]:
    specs = [
        ChannelSpec(0, "ego_vx", "ego_speed", 20.0),
        ChannelSpec(1, "ego_vy", "ego_speed", 12.0),
        ChannelSpec(2, "ego_yaw_rate", "ego_yaw", 2.5),
        ChannelSpec(3, "ego_ax", "ego_accel", 15.0),
        ChannelSpec(4, "ego_ay", "ego_accel", 15.0),
        ChannelSpec(5, "steer_angle", "actuator_state", 1.0),
        ChannelSpec(6, "steer_rate", "actuator_state", 1.0),
        ChannelSpec(7, "throttle_state", "actuator_state", None),
        ChannelSpec(8, "brake_state", "actuator_state", None),
        ChannelSpec(9, "prev_steer_cmd", "last_action", 1.0),
        ChannelSpec(10, "prev_throttle_cmd", "last_action", None),
        ChannelSpec(11, "prev_brake_cmd", "last_action", None),
    ]
    idx = 12
    for side in ("left", "right"):
        for point in range(8):
            specs.append(ChannelSpec(idx, f"road_{side}_{point}_x", "road_x", 80.0))
            specs.append(ChannelSpec(idx + 1, f"road_{side}_{point}_y", "road_y", 20.0))
            idx += 2
    for slot in range(4):
        specs.extend([
            ChannelSpec(idx, f"obs{slot}_present", "obstacle_present", None),
            ChannelSpec(idx + 1, f"obs{slot}_x", "obstacle_x", 80.0),
            ChannelSpec(idx + 2, f"obs{slot}_y", "obstacle_y", 20.0),
            ChannelSpec(idx + 3, f"obs{slot}_rel_vx", "obstacle_rel_speed", 20.0),
            ChannelSpec(idx + 4, f"obs{slot}_rel_vy", "obstacle_rel_speed", 12.0),
            ChannelSpec(idx + 5, f"obs{slot}_half_width", "obstacle_size", 5.0),
            ChannelSpec(idx + 6, f"obs{slot}_half_length", "obstacle_size", 5.0),
        ])
        idx += 7
    assert len(specs) == 72
    return specs


SPECS = channel_specs()


def sample_instance(tier: str, instance: int) -> dict[str, float]:
    rng = np.random.default_rng([BASE, 11, list(TIER_RANGES).index(tier), instance])
    ranges = TIER_RANGES[tier]
    return {key: float(rng.uniform(*ranges[key])) for key in ranges}


def obstacle_block(profile: dict[str, Any]) -> dict[str, Any]:
    if not profile.get("obstacle"):
        return {"enabled": False}
    s_arc = float(profile["s_arc"])
    phi = s_arc / TRACK_R
    dt_comp = TRACK_R * math.sin(phi)
    c_comp = TRACK_R * (1.0 - math.cos(phi))
    return {
        "enabled": True,
        "distance_range": [dt_comp, dt_comp],
        "lateral_offset_range": [c_comp, c_comp],
        "half_width_range": [float(profile["half_width"]), float(profile["half_width"])],
        "allowed_labels": ["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"],
        "max_sample_attempts": 50,
        "finish_on_pass": False,
        "perception_reveal_step": 0,
    }


def env_config(profile_name: str, inst: dict[str, float]):
    profile = PROFILES[profile_name]
    speed = float(profile["speed"])
    track_radius = float(profile["track_radius"])
    return build_env_config({
        "max_steps": int(profile["max_steps"]),
        "track_kind": profile["track_kind"],
        "track_radius": track_radius,
        "track_width": 5.0,
        "speed_range": [speed, speed],
        "friction_limited_speed": True,
        "friction_speed_margin": 0.92,
        "history_length": 1,
        "include_privileged_params": False,
        "obstacle_relative_velocity_mode": "ego",
        "obstacle": obstacle_block(profile),
        "randomization": {
            "mu_range": [inst["mu"], inst["mu"]],
            "mass_scale_range": [inst["mass"], inst["mass"]],
            "brake_scale_range": [inst["brake"], inst["brake"]],
            "drive_scale_range": [inst["drive"], inst["drive"]],
            "tire_stiffness_scale_range": [inst["stiff"], inst["stiff"]],
            "actuator_tau_scale_range": [inst["tau"], inst["tau"]],
            "cg_shift_range": [inst["cg"], inst["cg"]],
            "inertia_scale_range": [inst["inertia"], inst["inertia"]],
        },
    })


def collect_profile(tier: str, profile_name: str, instance: int, inst: dict[str, float]) -> dict[str, Any]:
    cfg = env_config(profile_name, inst)
    env = AutoDriftEnv(cfg)
    observations: list[np.ndarray] = []
    terminated = truncated = False
    steps = 0
    seed = 8_000_000 + list(TIER_RANGES).index(tier) * 100_000 + list(PROFILES).index(profile_name) * 10_000 + instance * 17
    try:
        obs, _ = env.reset(seed=seed)
        observations.append(np.asarray(obs, dtype=np.float64))
        while not (terminated or truncated):
            action = m4.v4_v2_fallback_no_regression_hard_safety_direct_action(
                np.asarray(obs, dtype=np.float32), m4.V4_POLICY_CONFIG
            )
            obs, _reward, terminated, truncated, _info = env.step(action)
            observations.append(np.asarray(obs, dtype=np.float64))
            steps += 1
    finally:
        env.close()
    arr = np.vstack(observations)
    return {
        "tier": tier,
        "profile": profile_name,
        "instance": instance,
        "seed": seed,
        "steps": steps,
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "vehicle": inst,
        "observations": arr,
    }


def stats(values: np.ndarray) -> dict[str, float]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {
            "n": 0, "min": float("nan"), "max": float("nan"), "mean": float("nan"),
            "p01": float("nan"), "p50": float("nan"), "p99": float("nan"),
            "max_abs": float("nan"), "p99_abs": float("nan"),
            "frac_abs_gt_0_8": float("nan"), "frac_abs_gt_1": float("nan"),
            "frac_abs_gt_1_5": float("nan"), "frac_abs_gt_2": float("nan"),
        }
    abs_values = np.abs(finite)
    return {
        "n": int(finite.size),
        "min": round(float(np.min(finite)), 6),
        "max": round(float(np.max(finite)), 6),
        "mean": round(float(np.mean(finite)), 6),
        "p01": round(float(np.percentile(finite, 1)), 6),
        "p50": round(float(np.percentile(finite, 50)), 6),
        "p99": round(float(np.percentile(finite, 99)), 6),
        "max_abs": round(float(np.max(abs_values)), 6),
        "p99_abs": round(float(np.percentile(abs_values, 99)), 6),
        "frac_abs_gt_0_8": round(float(np.mean(abs_values > 0.8)), 6),
        "frac_abs_gt_1": round(float(np.mean(abs_values > 1.0)), 6),
        "frac_abs_gt_1_5": round(float(np.mean(abs_values > 1.5)), 6),
        "frac_abs_gt_2": round(float(np.mean(abs_values > 2.0)), 6),
    }


def nice_scale(value: float) -> float:
    candidates = NICE_SCALES[NICE_SCALES >= value]
    if len(candidates):
        return float(candidates[0])
    return float(math.ceil(value / 20.0) * 20.0)


def recommended_divisor(spec: ChannelSpec, p99_abs: float) -> float | None:
    if spec.divisor is None or not math.isfinite(p99_abs):
        return None
    if p99_abs <= 0.8:
        return spec.divisor
    return nice_scale(spec.divisor * p99_abs / 0.8)


def write_channel_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    quick = bool(args.quick)
    n_inst = 3 if quick else 16
    tiers = ["S0_nominal", "C5_wide_current"] if quick else list(TIER_RANGES)
    profiles = ["mid_obstacle_arc", "high_speed_arc"] if quick else list(PROFILES)

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    result_path = RESULTS_JSON.with_name("obs_normalization_audit_quick.json") if quick else RESULTS_JSON
    channel_csv = RUN_DIR / ("channel_stats_quick.csv" if quick else "channel_stats.csv")
    episode_csv = RUN_DIR / ("episode_summary_quick.csv" if quick else "episode_summary.csv")

    prereg = json.loads(PREREG.read_text(encoding="utf-8"))

    runs = []
    for tier in tiers:
        for profile_name in profiles:
            for instance in range(n_inst):
                inst = sample_instance(tier, instance)
                runs.append(collect_profile(tier, profile_name, instance, inst))

    all_obs = np.vstack([run["observations"] for run in runs])
    channel_rows: list[dict[str, Any]] = []
    for spec in SPECS:
        st = stats(all_obs[:, spec.index])
        rec = recommended_divisor(spec, st["p99_abs"])
        channel_rows.append({
            "scope": "overall",
            "tier": "all",
            "profile": "all",
            "index": spec.index,
            "channel": spec.name,
            "group": spec.group,
            "current_divisor": "" if spec.divisor is None else spec.divisor,
            "recommended_divisor": "" if rec is None else rec,
            **st,
        })
    for tier in tiers:
        for profile_name in profiles:
            sub = np.vstack([
                run["observations"] for run in runs
                if run["tier"] == tier and run["profile"] == profile_name
            ])
            for spec in SPECS:
                st = stats(sub[:, spec.index])
                rec = recommended_divisor(spec, st["p99_abs"])
                channel_rows.append({
                    "scope": "tier_profile",
                    "tier": tier,
                    "profile": profile_name,
                    "index": spec.index,
                    "channel": spec.name,
                    "group": spec.group,
                    "current_divisor": "" if spec.divisor is None else spec.divisor,
                    "recommended_divisor": "" if rec is None else rec,
                    **st,
                })

    write_channel_csv(channel_csv, channel_rows)
    episode_rows = []
    for run in runs:
        inst = run["vehicle"]
        episode_rows.append({
            "tier": run["tier"], "profile": run["profile"], "instance": run["instance"],
            "seed": run["seed"], "steps": run["steps"], "terminated": run["terminated"],
            "truncated": run["truncated"], **{f"veh_{k}": round(v, 6) for k, v in inst.items()},
        })
    write_channel_csv(episode_csv, episode_rows)

    overall_rows = [row for row in channel_rows if row["scope"] == "overall"]
    conditional_rows = [row for row in channel_rows if row["scope"] == "tier_profile"]
    worst_by_abs = sorted(conditional_rows, key=lambda row: (-float(row["p99_abs"]), int(row["index"])))[:20]
    saturated = [
        row for row in conditional_rows
        if float(row["frac_abs_gt_1"]) > 0.01 or float(row["p99_abs"]) > 0.9
    ]

    group_summary: dict[str, dict[str, Any]] = {}
    for group in sorted({spec.group for spec in SPECS}):
        group_rows = [row for row in conditional_rows if row["group"] == group]
        group_summary[group] = {
            "max_p99_abs": max(float(row["p99_abs"]) for row in group_rows),
            "max_frac_abs_gt_1": max(float(row["frac_abs_gt_1"]) for row in group_rows),
            "worst_channel": max(group_rows, key=lambda row: float(row["p99_abs"]))["channel"],
            "worst_scope": {
                "tier": max(group_rows, key=lambda row: float(row["p99_abs"]))["tier"],
                "profile": max(group_rows, key=lambda row: float(row["p99_abs"]))["profile"],
            },
        }

    preview = {}
    for name, profile in PROFILES.items():
        max_preview_m = 8 * 5.0
        speed = float(profile["speed"])
        preview[name] = {
            "speed_mps": speed,
            "road_preview_m": max_preview_m,
            "road_preview_time_s": round(max_preview_m / speed, 3),
            "preview_m_for_2_5s": round(2.5 * speed, 1),
        }

    recommendation = {
        "population_training": "blocked on a follow-up normalization/design implementation if it uses the audited population-stress or high-speed envelopes; M3221 only measures and recommends",
        "current_c5_f1_like_tasks": "road_y/20 and obstacle relative-vy/12 show conditional saturation even below 20 m/s on curved obstacle profiles; do not assume obs72 is population-ready from the old nominal panels",
        "high_speed_or_B2_training": "do not train before changing speed/acceleration normalization and preview design; ego_vx/20, ego_vy/12, ax/15, and ay/15 saturate in the high_speed_arc profile",
        "candidate_changes_not_applied": [
            "change ego_vx divisor from 20 toward 40 and ego_vy divisor from 12 toward 30 for >20 m/s work",
            "change ax/ay divisors from 15 toward 40 for high-speed maneuvers or add robust clipping",
            "change road_y divisor from 20 toward 50 or redesign road geometry encoding for curved tracks",
            "change obstacle relative-vy divisor from 12 toward 25 when obstacle_relative_velocity_mode=ego is used",
            "make road lookahead distance speed-aware; 40 m gives only 1.43 s at 28 m/s and 1.11 s at 36 m/s",
        ],
    }

    payload = {
        "protocol": "obs_normalization_audit",
        "generated_by": "scripts/feasibility_audit/obs_normalization_audit.py",
        "quick_mode": quick,
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration_echo": {
            "file": str(PREREG),
            "decision_rule": prereg["preregistered_readouts"]["decision_rule"],
        },
        "seed_base": BASE,
        "tiers": tiers,
        "profiles": profiles,
        "instances_per_tier_profile": n_inst,
        "episodes": len(runs),
        "observations": int(all_obs.shape[0]),
        "channel_count": int(all_obs.shape[1]),
        "channel_csv": str(channel_csv),
        "episode_csv": str(episode_csv),
        "worst_channels_by_p99_abs": worst_by_abs,
        "saturated_channel_profiles": saturated,
        "overall_channel_summary": overall_rows,
        "group_summary": group_summary,
        "preview_time_summary": preview,
        "recommendation": recommendation,
        "budget": {"elapsed_s": round(time.time() - t0, 1)},
    }
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({
        "result": str(result_path),
        "quick": quick,
        "episodes": len(runs),
        "observations": int(all_obs.shape[0]),
        "elapsed_s": payload["budget"]["elapsed_s"],
        "saturated_channel_profiles": [
            f"{row['tier']}/{row['profile']}/{row['channel']}" for row in saturated[:10]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
