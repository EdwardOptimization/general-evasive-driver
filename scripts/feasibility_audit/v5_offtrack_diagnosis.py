"""B1 diagnosis: replay the 5 known feasible-row offtrack failures of the M3105 incumbent.

Target rows (all 0-collision, pure tracking/stability offtracks):
- feasible-only panel (base 601500, experiments/feasibility_audit/feasible_only_panel_rows.csv):
  rows 0010 / 0013 / 0024 / 0029 (specs 0008/0010/0014, high-speed 14-15 m/s @ r=18 m).
- fresh retest panel (base 501500): fa-fresh-retest-episode-0053 (seed 501820, spec-0005,
  low-speed ~4.9 m/s stability offtrack, min obstacle clearance 20.77 m).

For each row the script rebuilds the measurement env through the exact same code path as
scripts/feasibility_audit/fresh_panel_retest.py (M3088/M3090 helpers), then rolls out the
incumbent ActiveSafetyReflexDriver (M3105 v4) step by step while logging:
- env truth (diagnosis only, never fed to the controller): lateral_error, speed, beta,
  yaw_rate, mu, curvature, off_track_overshoot;
- the controller's own actor-visible internals: v2 base action, v4 final action,
  edge_urgency, obstacle_urgency, v4 local_speed_risk / edge_excess / obstacle_excess /
  local_risk, speed-floor recovery branch state (speed_deficit, recovery_allowed);
- an obs72-only curvature/feasible-speed estimate (the candidate v5 governor signal),
  validated against the privileged info["curvature"].

Outputs:
- runs/feasibility_audit/v5_offtrack_diagnosis_traces.json (full per-step traces)
- experiments/feasibility_audit/v5_offtrack_diagnosis_summary.json (per-row mechanism summary)

Deterministic, CPU-only. Usage:
    PYTHONPATH=src python scripts/feasibility_audit/v5_offtrack_diagnosis.py
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import fresh_panel_retest as fpr  # noqa: E402  (shared env/rollout recipe)

from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver  # noqa: E402
from autodrift.artifacts import read_json, utc_timestamp, write_json  # noqa: E402
from autodrift.controller_family_full_rollout_execution import read_csv_rows  # noqa: E402
from autodrift.engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight import (  # noqa: E402
    V2_POLICY_CONFIG,
    speed_floor_aware_direct_action,
)
from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (  # noqa: E402
    V4_POLICY_CONFIG,
    _clip01,
    _config_value,
    _hard_safety_features,
)

REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_TRACES_JSON = REPO_ROOT / "runs/feasibility_audit/v5_offtrack_diagnosis_traces.json"
DEFAULT_SUMMARY_JSON = REPO_ROOT / "experiments/feasibility_audit/v5_offtrack_diagnosis_summary.json"
FEASIBLE_PANEL_CSV = REPO_ROOT / "experiments/feasibility_audit/feasible_only_panel_rows.csv"
FRESH_PANEL_CSV = REPO_ROOT / "experiments/feasibility_audit/fresh_panel_retest_rows.csv"

# (panel, episode_id) -> replayed failure row
TARGET_ROWS = [
    ("feasible_only_panel", "fa-feasible-panel-episode-0010"),
    ("feasible_only_panel", "fa-feasible-panel-episode-0013"),
    ("feasible_only_panel", "fa-feasible-panel-episode-0024"),
    ("feasible_only_panel", "fa-feasible-panel-episode-0029"),
    ("fresh_panel", "fa-fresh-retest-episode-0053"),
]

CLAIM_BOUNDARY = (
    "Diagnosis replay of 5 known incumbent failure rows only; privileged env info is logged "
    "for analysis and is never fed to the controller. No repair-success, validation, ranking, "
    "promotion, or driver-performance claim is made."
)


def estimate_curvature_obs72(obs: np.ndarray, points: int = 6) -> tuple[float, float]:
    """Obs72-only signed curvature estimate from the 8x2 boundary lookahead points.

    Returns (kappa_signed_1pm, corridor_halfwidth_m). Uses Menger curvature over
    centerline triplets within the first `points` lookahead points (5..30 m ahead).
    Positive kappa = left turn (body +y).
    """
    left = obs[12:28].reshape(8, 2).astype(np.float64)
    right = obs[28:44].reshape(8, 2).astype(np.float64)
    cx = 0.5 * (left[:, 0] + right[:, 0]) * 80.0
    cy = 0.5 * (left[:, 1] + right[:, 1]) * 20.0
    pts = np.stack([cx, cy], axis=1)[:points]
    best = 0.0
    for i in range(points - 2):
        a, b, c = pts[i], pts[i + 1], pts[i + 2]
        ab = b - a
        bc = c - b
        ca = a - c
        cross = float(ab[0] * bc[1] - ab[1] * bc[0])
        denom = float(np.linalg.norm(ab) * np.linalg.norm(bc) * np.linalg.norm(ca))
        if denom < 1e-9:
            continue
        kappa = 2.0 * cross / denom
        if abs(kappa) > abs(best):
            best = kappa
    corridor = float(np.min(np.abs(left[:4, 1] - right[:4, 1])) * 0.5 * 20.0)
    return float(best), corridor


class DiagnosisRecorder:
    """Re-computes v2/v4 actor-visible internals per step (pure functions, no state)."""

    def __init__(self) -> None:
        self.driver = ActiveSafetyReflexDriver()

    def step_record(self, obs: np.ndarray, info: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
        v2_action = speed_floor_aware_direct_action(obs, V2_POLICY_CONFIG)
        v4_action = self.driver.act(obs)
        feats = _hard_safety_features(obs, V4_POLICY_CONFIG)
        thresholds = V4_POLICY_CONFIG["thresholds"]
        speed_body = feats["vx_body"]
        local_speed_risk = _clip01((speed_body - float(thresholds["local_hard_safety_speed_mps"])) / 6.0)
        obstacle_excess = _clip01(
            (feats["obstacle_urgency"] - float(thresholds["local_obstacle_urgency_trigger"])) / 0.5
        )
        edge_excess = _clip01((feats["edge_urgency"] - float(thresholds["local_edge_urgency_trigger"])) / 0.28)
        local_risk = local_speed_risk * max(obstacle_excess, edge_excess)
        # v2 speed-floor branch state
        speed_floor_mps = _config_value(V2_POLICY_CONFIG, "thresholds", "speed_floor_mps")
        speed_deficit = _clip01((speed_floor_mps - speed_body) / max(speed_floor_mps, 1e-6))
        recovery_allowed = bool(
            feats["obstacle_urgency"]
            <= _config_value(V2_POLICY_CONFIG, "thresholds", "speed_floor_recovery_obstacle_urgency_cap")
            and feats["edge_urgency"]
            <= _config_value(V2_POLICY_CONFIG, "thresholds", "speed_floor_recovery_edge_urgency_cap")
        )
        kappa_est, corridor = estimate_curvature_obs72(obs)
        record = {
            "step": int(info.get("step", -1)),
            # env truth (diagnosis only)
            "speed": float(info.get("speed", float("nan"))),
            "lateral_error": float(info.get("lateral_error", float("nan"))),
            "off_track_overshoot": float(info.get("off_track_overshoot", float("nan"))),
            "beta": float(info.get("beta", float("nan"))),
            "yaw_rate": float(info.get("yaw_rate", float("nan"))),
            "mu": float(info.get("mu", float("nan"))),
            "curvature_true": float(info.get("curvature", float("nan"))),
            "obstacle_distance": float(info.get("obstacle_distance", float("nan"))),
            # actor-visible internals
            "vx_body_obs": speed_body,
            "steer_state_obs5": float(obs[5]),
            "edge_urgency": feats["edge_urgency"],
            "obstacle_urgency": feats["obstacle_urgency"],
            "road_center_error": feats["road_center_error"],
            "v4_local_speed_risk": local_speed_risk,
            "v4_edge_excess": edge_excess,
            "v4_obstacle_excess": obstacle_excess,
            "v4_local_risk": local_risk,
            "v2_speed_deficit": speed_deficit,
            "v2_recovery_allowed": recovery_allowed,
            "v2_steer": float(v2_action[0]),
            "v2_throttle": float(v2_action[1]),
            "v2_brake_norm": float(v2_action[2]),
            "v4_steer": float(v4_action[0]),
            "v4_throttle": float(v4_action[1]),
            "v4_brake_norm": float(v4_action[2]),
            "v4_brake_physical": float((float(v4_action[2]) + 1.0) / 2.0),
            # obs72-only v5 governor signal candidates
            "kappa_est_obs72": kappa_est,
            "corridor_halfwidth_est_m": corridor,
            "v_feasible_est_at_6p5": math.sqrt(6.5 / max(abs(kappa_est), 1e-6)) if abs(kappa_est) > 1e-6 else 1e9,
        }
        return v4_action, record


def replay_row(plan: dict, seed: int, specs: dict, profile_cache: dict) -> tuple[dict, list[dict]]:
    env = fpr.build_env_for_plan_row(plan, specs, profile_cache)
    recorder = DiagnosisRecorder()
    trace: list[dict] = []
    try:
        obs, info = env.reset(seed=int(seed))
        terminated = truncated = False
        while not (terminated or truncated):
            action, record = recorder.step_record(np.asarray(obs, dtype=np.float32), info)
            obs, _reward, terminated, truncated, info = env.step(action)
            record["post_step_lateral_error"] = float(info.get("lateral_error", float("nan")))
            record["post_step_speed"] = float(info.get("speed", float("nan")))
            trace.append(record)
        outcome = {
            "steps": int(info.get("step", len(trace))),
            "termination_reason": str(info.get("termination_reason", "")),
            "collision": bool(info.get("collision", False)),
            "obstacle_completed": bool(info.get("obstacle_completed", False)),
            "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
            "final_mu": float(info.get("mu", float("nan"))),
            "initial_mu": float(info.get("initial_mu", float("nan"))),
            "truncated": bool(truncated),
        }
    finally:
        env.close()
    return outcome, trace


def summarize_trace(trace: list[dict], outcome: dict) -> dict[str, Any]:
    speeds = np.array([r["speed"] for r in trace])
    lat = np.array([r["post_step_lateral_error"] for r in trace])
    kappa_true = np.array([r["curvature_true"] for r in trace])
    kappa_est = np.array([r["kappa_est_obs72"] for r in trace])
    brake_phys = np.array([r["v4_brake_physical"] for r in trace])
    throttle = np.array([r["v4_throttle"] for r in trace])
    edge = np.array([r["edge_urgency"] for r in trace])
    risk = np.array([r["v4_local_risk"] for r in trace])
    steer_state = np.array([abs(r["steer_state_obs5"]) for r in trace])
    recovery = np.array([bool(r["v2_recovery_allowed"]) for r in trace])
    deficit = np.array([r["v2_speed_deficit"] for r in trace])
    mu = np.array([r["mu"] for r in trace])
    last = trace[-1]
    # last 25 steps before termination
    tail = slice(max(0, len(trace) - 25), len(trace))
    valid = np.abs(kappa_true) > 1e-4
    kappa_relerr = (
        float(np.median(np.abs(kappa_est[valid] - kappa_true[valid]) / np.abs(kappa_true[valid])))
        if bool(np.any(valid))
        else float("nan")
    )
    return {
        "outcome": outcome,
        "speed_mean": float(np.mean(speeds)),
        "speed_at_termination": float(last["post_step_speed"]),
        "mu_initial": float(mu[0]),
        "mu_final": float(mu[-1]),
        "mu_step_change": bool(abs(mu[0] - mu[-1]) > 1e-9),
        "abs_lateral_error_max": float(np.max(np.abs(lat))),
        "abs_lateral_error_final": float(abs(lat[-1])),
        "kappa_true_at_termination": float(kappa_true[-1]),
        "kappa_est_median_relative_error": kappa_relerr,
        "mu_g_speed_limit_final": float(math.sqrt(mu[-1] * 9.81 / max(abs(kappa_true[-1]), 1e-9))),
        "v4_brake_physical_max": float(np.max(brake_phys)),
        "v4_brake_physical_mean_tail25": float(np.mean(brake_phys[tail])),
        "v4_throttle_mean_tail25": float(np.mean(throttle[tail])),
        "edge_urgency_max": float(np.max(edge)),
        "edge_urgency_mean_tail25": float(np.mean(edge[tail])),
        "v4_local_risk_max": float(np.max(risk)),
        "steer_state_abs_max": float(np.max(steer_state)),
        "steer_state_abs_mean_tail25": float(np.mean(steer_state[tail])),
        "v2_recovery_allowed_fraction": float(np.mean(recovery)),
        "v2_recovery_allowed_fraction_tail25": float(np.mean(recovery[tail])),
        "v2_speed_deficit_mean_tail25": float(np.mean(deficit[tail])),
        "first_step_edge_urgency_above_v4_trigger": (
            int(np.argmax(edge > float(V4_POLICY_CONFIG["thresholds"]["local_edge_urgency_trigger"])))
            if bool(np.any(edge > float(V4_POLICY_CONFIG["thresholds"]["local_edge_urgency_trigger"])))
            else -1
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces-json", type=Path, default=DEFAULT_TRACES_JSON)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    args = parser.parse_args()

    source = {
        "m3084_measurement_rows": read_csv_rows(fpr.DEFAULT_M3084_DIR / "measurement_episode_rows.csv"),
        "m3012_workload_rows": read_csv_rows(fpr.DEFAULT_M3012_DIR / "executable_workload_rows.csv"),
    }
    plan_rows = fpr.m3090.full_fresh_plan(source)
    plan_by_row_id = {str(p["fresh_panel_row_id"]): p for p in plan_rows}
    payload = read_json(fpr.DEFAULT_M3012_DIR / "executable_source_specs.json")
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in payload["executable_source_specs"]
    }
    panel_rows = {
        "feasible_only_panel": {str(r["retest_episode_id"]): r for r in read_csv_rows(FEASIBLE_PANEL_CSV)},
        "fresh_panel": {str(r["retest_episode_id"]): r for r in read_csv_rows(FRESH_PANEL_CSV)},
    }

    profile_cache: dict[tuple[str, str], dict] = {}
    traces: dict[str, Any] = {}
    summaries: dict[str, Any] = {}
    for panel, episode_id in TARGET_ROWS:
        row = panel_rows[panel][episode_id]
        plan = plan_by_row_id[str(row["fresh_panel_row_id"])]
        seed = int(row["eval_seed"])
        outcome, trace = replay_row(plan, seed, specs, profile_cache)
        if str(outcome["termination_reason"]) != "off_track":
            raise RuntimeError(
                f"{episode_id}: expected off_track on replay, got {outcome['termination_reason']!r} "
                "(recipe drift; diagnosis invalid)"
            )
        if str(row["termination_reason"]) and str(row["termination_reason"]) != outcome["termination_reason"]:
            raise RuntimeError(f"{episode_id}: recorded vs replayed termination mismatch")
        summary = summarize_trace(trace, outcome)
        summary.update(
            {
                "panel": panel,
                "episode_id": episode_id,
                "fresh_panel_row_id": str(row["fresh_panel_row_id"]),
                "eval_seed": seed,
                "spec": str(row["spec"]),
                "label": str(row["label"]),
                "recorded_outcome": str(row["outcome"]),
            }
        )
        traces[episode_id] = {"meta": {k: summary[k] for k in ("panel", "eval_seed", "spec", "label")}, "trace": trace}
        summaries[episode_id] = summary
        print(
            f"{episode_id} seed={seed} spec={summary['spec']} steps={outcome['steps']} "
            f"reason={outcome['termination_reason']} speed_term={summary['speed_at_termination']:.2f} "
            f"mu_g_limit={summary['mu_g_speed_limit_final']:.2f} brake_max={summary['v4_brake_physical_max']:.3f} "
            f"edge_max={summary['edge_urgency_max']:.3f} local_risk_max={summary['v4_local_risk_max']:.3f} "
            f"kappa_relerr={summary['kappa_est_median_relative_error']:.4f}"
        )

    args.traces_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.traces_json, {"generated_at_utc": utc_timestamp(), "claim_boundary": CLAIM_BOUNDARY, "traces": traces})
    write_json(
        args.summary_json,
        {"generated_at_utc": utc_timestamp(), "claim_boundary": CLAIM_BOUNDARY, "rows": summaries},
    )
    print(f"traces_json: {args.traces_json}")
    print(f"summary_json: {args.summary_json}")


if __name__ == "__main__":
    main()
