"""Run M3112 residual collision/offtrack actor-visible repair full-fresh measurement."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite, write_run_state
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight as m3090
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088
from autodrift.engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight import (
    ACTION_COMPONENTS,
    M3110_POLICY_CONFIG,
    OUTPUT_SEMANTICS,
    POLICY_ID,
    residual_collision_offtrack_actor_visible_direct_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3112-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "actor-visible-repair-full-fresh-measurement-preflight"
)
NEXT_ID = (
    "m3113-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "actor-visible-repair-full-fresh-measurement-result-audit"
)
M3111_ID = (
    "m3111-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "actor-visible-repair-materialization-result-audit"
)
M3110_ID = (
    "m3110-engineering-controller-active-safety-driver-residual-collision-offtrack-"
    "actor-visible-repair-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)
M3095_ID = (
    "m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-"
    "repair-full-fresh-measurement-preflight"
)
M3100_ID = (
    "m3100-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3111_AUDIT = Path(f"docs/{M3111_ID}.md")
DEFAULT_M3110_DIR = Path(
    "runs/m3110_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "actor_visible_repair_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3095_DIR = Path(
    "runs/m3095_engineering_controller_active_safety_driver_v2_speed_floor_aware_"
    "direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3100_DIR = Path(
    "runs/m3100_engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3090_DIR = Path(
    "runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_"
    "safety_reflex_full_fresh_runtime_measurement_preflight"
)
DEFAULT_M3084_DIR = Path(
    "runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_fresh_robustness_measurement_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3112_engineering_controller_active_safety_driver_residual_collision_offtrack_"
    "actor_visible_repair_full_fresh_measurement_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_FULL_ROWS = 64
EXPECTED_AXIS_COUNT = 4
EXPECTED_BINDING_ROLE_COUNT = 2
BASELINE_IDS = ("m3105", "m3095", "m3100", "m3090")
CLAIM_SCOPE = (
    "M3112 Active Safety Driver residual collision/offtrack actor-visible repair full-fresh "
    "measurement preflight only; the complete M3084 fresh current-sim denominator may be "
    "executed through the M3110 direct-action function as the full obs72-to-action3 action "
    "source and measurement, same-row comparison against M3105 M3095 M3100 and M3090, "
    "contract, claim, gate, doc, and M3113 audit artifacts may be written. No validation, "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, driver-performance "
    "verdict, current-sim verdict, repair success, robustness-result, high-fidelity validation, "
    "paper evidence, finite-window-vs-GRU evidence, full ideal driver completion, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal "
    "driver completion, or level3 self-identification"
)

COMPARISON_FIELDNAMES = [
    "comparison_id",
    "measurement_episode_id",
    "baseline_id",
    "baseline_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "m3112_policy",
    "baseline_policy",
    "m3112_success",
    "baseline_success",
    "success_delta",
    "m3112_collision",
    "baseline_collision",
    "collision_delta",
    "m3112_offtrack",
    "baseline_offtrack",
    "offtrack_delta",
    "m3112_speed_too_low",
    "baseline_speed_too_low",
    "speed_too_low_delta",
    "m3112_termination_reason",
    "baseline_termination_reason",
    "termination_reason_match",
    "m3112_outcome_bucket",
    "baseline_outcome_bucket",
    "outcome_bucket_match",
    "m3112_min_clearance_margin",
    "baseline_min_clearance_margin",
    "clearance_margin_delta",
    "m3112_return",
    "baseline_return",
    "return_delta",
    "m3112_speed_mean",
    "baseline_speed_mean",
    "speed_mean_delta",
    "m3112_action_rate_mean",
    "baseline_action_rate_mean",
    "action_rate_delta",
    "exact_seed_match_m3105",
    "exact_seed_match_m3095",
    "exact_seed_match_m3100",
    "exact_seed_match_m3090",
    "comparison_claim_made",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3112",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GUARD_FIELDNAMES = m3088.GUARD_FIELDNAMES
GATE_FIELDNAMES = m3088.GATE_FIELDNAMES


def _bool(value: Any) -> bool:
    return m3088._bool(value)


def _float(value: Any) -> float:
    return m3088._float(value)


def _mean(values: Iterable[float]) -> float | str:
    return m3088._mean(values)


def _success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool(row.get("success", False))
    return _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return m3088.any_flag(rows, key)


class M3112RepairMeasurementPolicy:
    """Policy adapter that calls the M3110 direct-action repair function."""

    def __init__(self):
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0
        self.final_action_abs_max = 0.0

    def reset(self) -> None:
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0
        self.final_action_abs_max = 0.0

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        del info
        action = residual_collision_offtrack_actor_visible_direct_action(observation, M3110_POLICY_CONFIG)
        self.step_count += 1
        self.raw_action_abs_max = max(self.raw_action_abs_max, float(np.max(np.abs(action))))
        self.raw_action_l2_sum += float(np.linalg.norm(action))
        self.final_action_abs_max = max(self.final_action_abs_max, float(np.max(np.abs(action))))
        return action

    def telemetry(self) -> dict[str, Any]:
        steps = int(self.step_count)
        return {
            "runtime_driver_id": POLICY_ID,
            "candidate_output_semantics": OUTPUT_SEMANTICS,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
            "direct_action_step_count": steps,
            "raw_action_abs_max": float(self.raw_action_abs_max),
            "raw_action_l2_mean": float(self.raw_action_l2_sum / steps) if steps else 0.0,
            "action_clip_fraction": 0.0,
            "final_action_abs_max": float(self.final_action_abs_max),
        }


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "measurement_episode_rows": output_dir / "measurement_episode_rows.csv",
        "measurement_failure_rows": output_dir / "measurement_failure_rows.csv",
        "measurement_metric_summary_rows": output_dir / "measurement_metric_summary_rows.csv",
        "measurement_contract_guard_rows": output_dir / "measurement_contract_guard_rows.csv",
        "same_row_comparison_rows": output_dir / "same_row_comparison_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3111_audit: Path,
    m3110_dir: Path,
    m3105_dir: Path,
    m3095_dir: Path,
    m3100_dir: Path,
    m3090_dir: Path,
    m3084_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3111_audit": m3111_audit,
        "m3110_summary": m3110_dir / "summary.json",
        "m3110_policy_config": m3110_dir / "direct_action_policy_config.json",
        "m3110_gate_rows": m3110_dir / "gate_matrix.csv",
        "m3110_residual_repair_guard_rows": m3110_dir / "residual_repair_guard_rows.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_episode_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3095_summary": m3095_dir / "summary.json",
        "m3095_episode_rows": m3095_dir / "measurement_episode_rows.csv",
        "m3100_summary": m3100_dir / "summary.json",
        "m3100_episode_rows": m3100_dir / "measurement_episode_rows.csv",
        "m3090_summary": m3090_dir / "summary.json",
        "m3090_episode_rows": m3090_dir / "runtime_measurement_episode_rows.csv",
        "m3084_summary": m3084_dir / "summary.json",
        "m3084_measurement_rows": m3084_dir / "measurement_episode_rows.csv",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3111_audit_text": paths["m3111_audit"].read_text(encoding="utf-8") if exists["m3111_audit"] else "",
        "m3110_summary": read_json(paths["m3110_summary"]) if exists["m3110_summary"] else {},
        "m3110_policy_config": read_json(paths["m3110_policy_config"]) if exists["m3110_policy_config"] else {},
        "m3110_gate_rows": read_csv_rows(paths["m3110_gate_rows"]),
        "m3110_residual_repair_guard_rows": read_csv_rows(paths["m3110_residual_repair_guard_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_episode_rows": read_csv_rows(paths["m3105_episode_rows"]),
        "m3095_summary": read_json(paths["m3095_summary"]) if exists["m3095_summary"] else {},
        "m3095_episode_rows": read_csv_rows(paths["m3095_episode_rows"]),
        "m3100_summary": read_json(paths["m3100_summary"]) if exists["m3100_summary"] else {},
        "m3100_episode_rows": read_csv_rows(paths["m3100_episode_rows"]),
        "m3090_summary": read_json(paths["m3090_summary"]) if exists["m3090_summary"] else {},
        "m3090_episode_rows": read_csv_rows(paths["m3090_episode_rows"]),
        "m3084_summary": read_json(paths["m3084_summary"]) if exists["m3084_summary"] else {},
        "m3084_measurement_rows": read_csv_rows(paths["m3084_measurement_rows"]),
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def full_fresh_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    plan = m3090.full_fresh_plan(source)
    for index, row in enumerate(plan, start=1):
        row["runtime_smoke_episode_id"] = f"m3112-measurement-episode-{index:04d}"
    return plan


def _with_scope(rows: list[dict[str, Any]], *, id_prefix: str = "m3112") -> list[dict[str, Any]]:
    updated = []
    for row in rows:
        item = dict(row)
        item["claim_boundary"] = CLAIM_SCOPE
        item["runtime_driver_id"] = POLICY_ID
        if "policy" in item:
            item["policy"] = "active_safety_driver_residual_collision_offtrack_actor_visible_repair_measurement"
        for key in ("metric_summary_id", "guard_id", "gate_id", "claim_id"):
            if id_prefix and key in item:
                item[key] = str(item[key]).replace("m3088", id_prefix, 1)
        updated.append(item)
    return updated


def run_measurement_plan(
    *,
    plan_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    output_dir: Path,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in executable_specs
    }
    profile_cache: dict[tuple[str, str], dict[str, Any]] = {}
    episodes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("M3112 plan row failed pre-execution guards")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            cache_key = (profile_name, config_path)
            if cache_key not in profile_cache:
                profile_cache[cache_key] = m3088.m3075.profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
            profile_config = profile_cache[cache_key]
            env_config = m3088.env_config_for_executable_profile(
                executable_spec=executable_spec,
                profile_config=profile_config,
            )
            env = m3088.wrap_env_with_profile_mask(m3088.AutoDriftEnv(env_config), profile_config)
            policy = M3112RepairMeasurementPolicy()
            try:
                if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
                    raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
                if int(env.action_space.shape[0]) != ACTION_DIM:
                    raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
                row = m3088.run_episode_with_policy(
                    env,
                    policy,
                    "active_safety_driver_residual_collision_offtrack_actor_visible_repair_measurement",
                    int(plan["eval_seed"]),
                )
            finally:
                env.close()
            episodes.append(m3088.normalize_episode_row(plan, row, policy.telemetry()))
        except Exception as exc:  # noqa: BLE001 - every scheduled row must be accounted.
            failures.append(
                m3088.failure_row(
                    plan,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
        write_run_state(
            output_dir / "run_state.json",
            {
                "scheduled_measurement_row_count": len(plan_rows),
                "measurement_episode_row_count": len(episodes),
                "measurement_failure_row_count": len(failures),
                "recorded_row_count": len(episodes) + len(failures),
                "latest_measurement_episode_id": plan.get("runtime_smoke_episode_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return {"episodes": episodes, "failures": failures}


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _speed_too_low(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "speed_too_low"


def same_row_comparison_rows(
    episodes: list[dict[str, Any]],
    m3105_rows: list[dict[str, Any]],
    m3095_rows: list[dict[str, Any]],
    m3100_rows: list[dict[str, Any]],
    m3090_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baselines = {
        "m3105": {str(row.get("source_measurement_episode_id", "")): row for row in m3105_rows},
        "m3095": {str(row.get("source_measurement_episode_id", "")): row for row in m3095_rows},
        "m3100": {str(row.get("source_measurement_episode_id", "")): row for row in m3100_rows},
        "m3090": {str(row.get("source_measurement_episode_id", "")): row for row in m3090_rows},
    }
    rows: list[dict[str, Any]] = []
    for episode in episodes:
        source_id = str(episode.get("source_measurement_episode_id", ""))
        episode_offtrack = _offtrack(episode)
        episode_speed_too_low = _speed_too_low(episode)
        for baseline_id in BASELINE_IDS:
            baseline = baselines[baseline_id].get(source_id, {})
            baseline_offtrack = _offtrack(baseline)
            baseline_speed_too_low = _speed_too_low(baseline)
            seed_match = str(episode.get("eval_seed", "")) == str(baseline.get("eval_seed", ""))
            rows.append(
                {
                    "comparison_id": f"m3112-same-row-comparison-{len(rows) + 1:04d}",
                    "measurement_episode_id": episode.get("runtime_smoke_episode_id", ""),
                    "baseline_id": baseline_id,
                    "baseline_episode_id": baseline.get("runtime_smoke_episode_id", ""),
                    "source_measurement_episode_id": source_id,
                    "fresh_panel_row_id": episode.get("fresh_panel_row_id", ""),
                    "axis_id": episode.get("axis_id", ""),
                    "binding_role": episode.get("binding_role", ""),
                    "task_family": episode.get("task_family", ""),
                    "eval_seed": episode.get("eval_seed", ""),
                    "m3112_policy": episode.get("policy", ""),
                    "baseline_policy": baseline.get("policy", ""),
                    "m3112_success": _success(episode),
                    "baseline_success": _success(baseline),
                    "success_delta": int(_success(episode)) - int(_success(baseline)),
                    "m3112_collision": _bool(episode.get("collision", False)),
                    "baseline_collision": _bool(baseline.get("collision", False)),
                    "collision_delta": int(_bool(episode.get("collision", False))) - int(_bool(baseline.get("collision", False))),
                    "m3112_offtrack": episode_offtrack,
                    "baseline_offtrack": baseline_offtrack,
                    "offtrack_delta": int(episode_offtrack) - int(baseline_offtrack),
                    "m3112_speed_too_low": episode_speed_too_low,
                    "baseline_speed_too_low": baseline_speed_too_low,
                    "speed_too_low_delta": int(episode_speed_too_low) - int(baseline_speed_too_low),
                    "m3112_termination_reason": episode.get("termination_reason", ""),
                    "baseline_termination_reason": baseline.get("termination_reason", ""),
                    "termination_reason_match": str(episode.get("termination_reason", ""))
                    == str(baseline.get("termination_reason", "")),
                    "m3112_outcome_bucket": episode.get("outcome_bucket", ""),
                    "baseline_outcome_bucket": baseline.get("outcome_bucket", ""),
                    "outcome_bucket_match": str(episode.get("outcome_bucket", ""))
                    == str(baseline.get("outcome_bucket", "")),
                    "m3112_min_clearance_margin": episode.get("min_clearance_margin", ""),
                    "baseline_min_clearance_margin": baseline.get("min_clearance_margin", ""),
                    "clearance_margin_delta": _float(episode.get("min_clearance_margin"))
                    - _float(baseline.get("min_clearance_margin")),
                    "m3112_return": episode.get("return", ""),
                    "baseline_return": baseline.get("return", ""),
                    "return_delta": _float(episode.get("return")) - _float(baseline.get("return")),
                    "m3112_speed_mean": episode.get("speed_mean", ""),
                    "baseline_speed_mean": baseline.get("speed_mean", ""),
                    "speed_mean_delta": _float(episode.get("speed_mean")) - _float(baseline.get("speed_mean")),
                    "m3112_action_rate_mean": episode.get("action_rate_mean", ""),
                    "baseline_action_rate_mean": baseline.get("action_rate_mean", ""),
                    "action_rate_delta": _float(episode.get("action_rate_mean"))
                    - _float(baseline.get("action_rate_mean")),
                    "exact_seed_match_m3105": baseline_id == "m3105" and seed_match,
                    "exact_seed_match_m3095": baseline_id == "m3095" and seed_match,
                    "exact_seed_match_m3100": baseline_id == "m3100" and seed_match,
                    "exact_seed_match_m3090": baseline_id == "m3090" and seed_match,
                    "comparison_claim_made": False,
                    "repair_success_claim_made": False,
                    "validation_run": False,
                    "driver_performance_claim_made": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31080,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject the M3112 residual collision/offtrack actor-visible full-fresh measurement artifacts before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                str(doc_path),
                "runs/m3110_engineering_controller_active_safety_driver_residual_collision_offtrack_actor_visible_repair_materialization_preflight/direct_action_policy_config.json",
            ],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "measurement_episode_rows.csv"),
                str(output_dir / "measurement_failure_rows.csv"),
                str(output_dir / "measurement_metric_summary_rows.csv"),
                str(output_dir / "measurement_contract_guard_rows.csv"),
                str(output_dir / "same_row_comparison_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit full-fresh M3110 residual repair measurement before broader interpretation"],
            "derived_from": [MILESTONE_ID, M3111_ID, M3110_ID, M3105_ID, M3095_ID, M3100_ID],
            "blocked_by": [
                "M3112 full-fresh measurement rows require audit before any validation or repair-success route",
                "same-row comparison against M3105 M3095 M3100 and M3090 is measurement context and not a performance verdict before M3113",
            ],
            "supersedes": ["direct interpretation of M3112 rows without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3113 must audit M3112 summary measurement comparison metric guard claim and gate artifacts",
            "M3113 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3113 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3113 must select exactly one behavior synthesis validation-planning stop or next repair route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3112 same-row deltas into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_collision_offtrack_repair",
            "evidence_axis": "residual_collision_offtrack_full_fresh_measurement_result_audit",
            "evidence_increment": "audits full-fresh current-sim measurement rows and same-row comparison from the M3110 residual direct-action repair",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3112 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize if M3113 cannot select one next route",
            ],
            "fallback_plan": [
                "route to M3110 artifact repair if artifacts are incomplete or contract-unsafe",
                "route to behavior repair synthesis if measurement is behavior-negative but contract-safe",
                "route to validation planning only after M3113 accepts artifact completeness and claim boundaries",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3112 completes full-fresh M3110 residual repair measurement preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3112 full-fresh residual collision/offtrack repair measurement artifacts",
            "admission_evidence": ["M3112 summary gate matrix comparison measurement metric contract and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3113 status queue scoreboard research log and review",
                "one follow-up manifest only if M3113 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3113 accepts or rejects M3112 as complete and claim-safe",
                "next behavior synthesis validation-planning stop or repair route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3113 audits engineering runtime-measurement artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3113; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3112 full-fresh residual repair measurement artifacts only.",
            "negative_result_policy": "Preserve runtime evidence and route to engineering repair synthesis or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3112 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits complete fresh-denominator environment-loop evidence through the M3110 residual direct-action repair",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3113 audits engineering runtime measurement evidence",
            "must_synthesize_if": [
                "M3113 cannot accept M3112 as complete and claim-safe",
                "M3113 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result or self-ID evidence",
                "M3113 cannot select behavior synthesis validation planning stop or next repair route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3113 audits M3112 row counts gates actor contract same-row comparison and claim boundaries",
            "M3113 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3113 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3113 hides M3112 failures or missing artifacts",
            "M3113 treats M3112 runtime measurement as validation repair-success or performance verdict",
            "M3113 changes actor input or action contract",
            "M3113 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3113 audits M3112 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_residual_repair_full_fresh_measurement_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3112-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _finite_comparison_deltas(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        for key in ("clearance_margin_delta", "return_delta", "speed_mean_delta", "action_rate_delta"):
            if not np.isfinite(_float(row.get(key))):
                return False
    return True


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    config = source["m3110_policy_config"]
    audit_accepts = "accept_m3110_materialization_route_to_m3112_full_fresh_measurement_preflight" in str(
        source.get("m3111_audit_text", "")
    )
    baseline_counts = Counter(str(row.get("baseline_id", "")) for row in comparison_rows)
    expected_comparison_rows = EXPECTED_FULL_ROWS * len(BASELINE_IDS)
    same_row_sources_complete = len(comparison_rows) == expected_comparison_rows and all(
        baseline_counts.get(baseline_id, 0) == EXPECTED_FULL_ROWS
        and all(
            bool(row.get("baseline_episode_id", ""))
            and _bool(row.get(f"exact_seed_match_{baseline_id}", False))
            for row in comparison_rows
            if row.get("baseline_id") == baseline_id
        )
        for baseline_id in BASELINE_IDS
    )
    forbidden_flags_clear = not any_flag(episodes + failures, "driver_performance_claim_made") and not any_flag(
        episodes + failures, "validation_result_claim_made"
    )
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3111_accepts_m3112_route", "lineage", audit_accepts, "route marker", "present", "lineage_invalid"),
        gate("m3110_status_pass", "lineage", _bool(source["m3110_summary"].get("status_pass", False)), source["m3110_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3110_gate_matrix_pass", "lineage", _bool(source["m3110_summary"].get("gate_matrix_pass", False)), source["m3110_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3110_policy_config_status", "lineage", str(config.get("policy_id", "")) == POLICY_ID, config.get("policy_id"), POLICY_ID, "lineage_invalid"),
        gate("m3110_gate_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3110_gate_rows", [])), len(source.get("m3110_gate_rows", [])), "all pass", "lineage_invalid"),
        gate("m3110_residual_repair_guard_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3110_residual_repair_guard_rows", [])), len(source.get("m3110_residual_repair_guard_rows", [])), "all pass", "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3095_status_pass", "lineage", _bool(source["m3095_summary"].get("status_pass", False)), source["m3095_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3100_status_pass", "lineage", _bool(source["m3100_summary"].get("status_pass", False)), source["m3100_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3090_status_pass", "lineage", _bool(source["m3090_summary"].get("status_pass", False)), source["m3090_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3084_status_pass", "lineage", _bool(source["m3084_summary"].get("status_pass", False)), source["m3084_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("policy_observation_shape", "contract", int(config.get("observation_shape", -1)) == P0_OBSERVATION_DIM, config.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("policy_action_shape", "contract", int(config.get("action_shape", -1)) == ACTION_DIM, config.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("policy_output_semantics", "contract", str(config.get("output_semantics", "")) == OUTPUT_SEMANTICS, config.get("output_semantics"), OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(config.get("runtime_base_policy_required", True)), config.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("full_fresh_denominator", "measurement", len(plan_rows) == EXPECTED_FULL_ROWS, len(plan_rows), EXPECTED_FULL_ROWS, "scenario_sampling_failure"),
        gate("full_fresh_axis_count", "measurement", len({row.get("axis_id", "") for row in plan_rows}) == EXPECTED_AXIS_COUNT, len({row.get("axis_id", "") for row in plan_rows}), EXPECTED_AXIS_COUNT, "scenario_sampling_failure"),
        gate("full_fresh_binding_role_count", "measurement", len({row.get("binding_role", "") for row in plan_rows}) == EXPECTED_BINDING_ROLE_COUNT, len({row.get("binding_role", "") for row in plan_rows}), EXPECTED_BINDING_ROLE_COUNT, "scenario_sampling_failure"),
        gate("plan_rows_pass", "measurement", all(_bool(row.get("status_pass", False)) for row in plan_rows), "all", "pass", "scenario_sampling_failure"),
        gate("measurement_accounted_rows", "execution", len(episodes) + len(failures) == len(plan_rows), len(episodes) + len(failures), len(plan_rows), "metric_artifact"),
        gate("measurement_episode_rows", "execution", len(episodes) == EXPECTED_FULL_ROWS, len(episodes), EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("measurement_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("selected_metrics_finite", "metric", selected_metrics_are_finite(episodes) if episodes else False, "finite" if episodes else "none", "finite", "metric_artifact"),
        gate("metric_summary_rows", "metric", bool(metric_rows), len(metric_rows), "nonempty", "metric_artifact"),
        gate("same_row_comparison_rows", "comparison", len(comparison_rows) == expected_comparison_rows, len(comparison_rows), expected_comparison_rows, "metric_artifact"),
        gate("same_row_baseline_counts", "comparison", all(baseline_counts.get(baseline_id, 0) == EXPECTED_FULL_ROWS for baseline_id in BASELINE_IDS), dict(sorted(baseline_counts.items())), "64 rows per baseline", "metric_artifact"),
        gate("same_row_sources_complete", "comparison", same_row_sources_complete, "same-row source and seed", "complete", "metric_artifact"),
        gate("same_row_comparison_deltas_finite", "comparison", _finite_comparison_deltas(comparison_rows), "finite", "finite", "metric_artifact"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in guard_rows), "all", "pass", "contract_violation"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("forbidden_flags_clear", "claim", forbidden_flags_clear, "forbidden claim flags", "clear", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3112 Residual Collision/Offtrack Actor-Visible Full-Fresh Measurement Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- scheduled full-fresh rows: {summary['scheduled_measurement_row_count']}/{summary['target_measurement_row_count']}",
            f"- measurement episode rows: {summary['measurement_episode_row_count']}",
            f"- measurement failure rows: {summary['measurement_failure_row_count']}",
            f"- same-row comparison rows: {summary['same_row_comparison_row_count']}",
            f"- success count: {summary['measurement_success_count']}",
            f"- collision count: {summary['measurement_collision_count']}",
            f"- offtrack count: {summary['measurement_offtrack_count']}",
            f"- speed-too-low count: {summary['measurement_speed_too_low_count']}",
            f"- success count delta vs M3105: {summary['success_count_delta_vs_m3105']}",
            f"- collision count delta vs M3105: {summary['collision_count_delta_vs_m3105']}",
            f"- offtrack count delta vs M3105: {summary['offtrack_count_delta_vs_m3105']}",
            f"- speed-too-low count delta vs M3105: {summary['speed_too_low_count_delta_vs_m3105']}",
            f"- clearance margin mean: {summary['measurement_clearance_margin_mean']}",
            f"- action clip fraction mean: {summary['measurement_action_clip_fraction_mean']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3112 records full-fresh current-sim rows through the M3110 residual collision/offtrack actor-visible direct-action repair function and writes same-row deltas against M3105, M3095, M3100, and M3090. These are measurement and audit-input artifacts for M3113 only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
        ]
    )


def guard(guard_id: str, family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3112-{guard_id}",
        "guard_family": family,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def contract_guard_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = plan_rows + episodes + failures
    sample_action = residual_collision_offtrack_actor_visible_direct_action(
        np.zeros(P0_OBSERVATION_DIM, dtype=np.float32),
        M3110_POLICY_CONFIG,
    )
    config = source["m3110_policy_config"]
    return [
        guard("policy_observation_shape", "contract", config.get("observation_shape"), P0_OBSERVATION_DIM),
        guard("policy_action_shape", "contract", config.get("action_shape"), ACTION_DIM),
        guard("policy_action_components", "contract", "|".join(config.get("output_components", [])), "|".join(ACTION_COMPONENTS)),
        guard("policy_output_semantics", "contract", config.get("output_semantics"), OUTPUT_SEMANTICS),
        guard("runtime_base_policy_required", "contract", any_flag(combined, "runtime_base_policy_required"), False),
        guard("checkpoint_model_required", "contract", any_flag(combined, "checkpoint_model_required"), False),
        guard("sample_action_shape", "runtime_api", tuple(sample_action.shape), (ACTION_DIM,)),
        guard("sample_action_finite", "runtime_api", bool(np.all(np.isfinite(sample_action))), True),
        guard("sample_action_bounded", "runtime_api", bool(np.max(np.abs(sample_action)) <= 1.0), True),
        guard("scheduled_full_fresh_rows", "full_fresh_denominator", len(plan_rows), EXPECTED_FULL_ROWS),
        guard("accounted_full_fresh_rows", "full_fresh_denominator", len(episodes) + len(failures), len(plan_rows)),
        guard("axis_count", "full_fresh_denominator", len({row.get("axis_id", "") for row in plan_rows}), EXPECTED_AXIS_COUNT),
        guard("binding_role_count", "full_fresh_denominator", len({row.get("binding_role", "") for row in plan_rows}), EXPECTED_BINDING_ROLE_COUNT),
        guard("actor_input_contract_changed", "contract", any_flag(combined, "actor_input_contract_changed"), False),
        guard("hidden_oracle_actor_input_required", "contract", any_flag(combined, "hidden_oracle_actor_input_required"), False),
        guard("target_labels_actor_visible", "contract", any_flag(combined, "target_labels_actor_visible"), False),
        guard("source_labels_actor_visible", "contract", any_flag(combined, "source_labels_actor_visible"), False),
        guard("route_labels_actor_visible", "contract", any_flag(combined, "route_labels_actor_visible"), False),
        guard("outcome_labels_actor_visible", "contract", any_flag(combined, "outcome_labels_actor_visible"), False),
        guard("success_progress_labels_actor_visible", "contract", any_flag(combined, "success_progress_labels_actor_visible"), False),
        guard("verdict_labels_actor_visible", "contract", any_flag(combined, "verdict_labels_actor_visible"), False),
        guard("ttc_actor_input_required", "contract", any_flag(combined, "ttc_actor_input_required"), False),
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("measurement_rows", "measurement", True, "measurement_episode_rows.csv"),
        ("same_row_comparison_rows", "measurement_comparison", True, "same_row_comparison_rows.csv"),
        ("metric_summary_rows", "measurement_metric", True, "measurement_metric_summary_rows.csv"),
        ("contract_guards", "guard", True, "measurement_contract_guard_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3113 audit manifest"),
    ]
    blocked = [
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future result audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "direct-action repair forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3112-{claim_id}",
            "claim_family": family,
            "allowed_in_m3112": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3112-{claim_id}",
            "claim_family": family,
            "allowed_in_m3112": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def run_full_fresh_measurement_preflight(
    *,
    m3111_audit: Path,
    m3110_dir: Path,
    m3105_dir: Path,
    m3095_dir: Path,
    m3100_dir: Path,
    m3090_dir: Path,
    m3084_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    device: str,
) -> dict[str, Any]:
    del device
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3111_audit=m3111_audit,
        m3110_dir=m3110_dir,
        m3105_dir=m3105_dir,
        m3095_dir=m3095_dir,
        m3100_dir=m3100_dir,
        m3090_dir=m3090_dir,
        m3084_dir=m3084_dir,
        m3012_dir=m3012_dir,
    )
    plan_rows = full_fresh_plan(source)
    measurement = run_measurement_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    episodes = _with_scope(measurement["episodes"])
    failures = _with_scope(measurement["failures"])
    metric_rows = _with_scope(m3088.metric_summary_rows(episodes))
    guard_rows = contract_guard_rows(source=source, plan_rows=plan_rows, episodes=episodes, failures=failures)
    comparison = same_row_comparison_rows(
        episodes,
        source["m3105_episode_rows"],
        source["m3095_episode_rows"],
        source["m3100_episode_rows"],
        source["m3090_episode_rows"],
    )
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["measurement_episode_rows"], episodes, m3088.EPISODE_FIELDNAMES),
        (paths["measurement_failure_rows"], failures, m3088.FAILURE_FIELDNAMES),
        (paths["measurement_metric_summary_rows"], metric_rows, m3088.METRIC_FIELDNAMES),
        (paths["measurement_contract_guard_rows"], guard_rows, GUARD_FIELDNAMES),
        (paths["same_row_comparison_rows"], comparison, COMPARISON_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        episodes=episodes,
        failures=failures,
        metric_rows=metric_rows,
        guard_rows=guard_rows,
        comparison_rows=comparison,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episodes)
    status_pass = bool(gate_matrix_pass and present)

    def _baseline_rows(baseline_id: str) -> list[dict[str, Any]]:
        return [row for row in comparison if str(row.get("baseline_id", "")) == baseline_id]

    def _sum_delta(baseline_id: str, key: str) -> int:
        return sum(int(row.get(key, 0)) for row in _baseline_rows(baseline_id))

    def _mean_delta(baseline_id: str, key: str) -> float | str:
        return _mean(_float(row.get(key)) for row in _baseline_rows(baseline_id))

    def _exact_seed_count(baseline_id: str) -> int:
        return sum(1 for row in _baseline_rows(baseline_id) if _bool(row.get(f"exact_seed_match_{baseline_id}", False)))

    baseline_counts = Counter(str(row.get("baseline_id", "")) for row in comparison)
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_preflight_pass"
            if status_pass
            else "active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "runtime_driver_id": POLICY_ID,
        "scheduled_measurement_row_count": len(plan_rows),
        "target_measurement_row_count": EXPECTED_FULL_ROWS,
        "measurement_episode_row_count": len(episodes),
        "measurement_failure_row_count": len(failures),
        "recorded_row_count": len(episodes) + len(failures),
        "measurement_success_count": sum(1 for row in episodes if _bool(row.get("success", False))),
        "measurement_collision_count": sum(1 for row in episodes if _bool(row.get("collision", False))),
        "measurement_offtrack_count": int(termination_counts.get("off_track", 0)),
        "measurement_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "measurement_termination_counts": dict(sorted(termination_counts.items())),
        "measurement_clearance_margin_mean": _mean(_float(row.get("min_clearance_margin")) for row in episodes),
        "measurement_high_sideslip_fraction_mean": _mean(_float(row.get("high_sideslip_fraction")) for row in episodes),
        "measurement_lateral_rmse_mean": _mean(_float(row.get("lateral_rmse")) for row in episodes),
        "measurement_action_clip_fraction_mean": _mean(_float(row.get("action_clip_fraction")) for row in episodes),
        "measurement_raw_action_abs_max": max((_float(row.get("raw_action_abs_max")) for row in episodes), default=0.0),
        "measurement_final_action_abs_max": max((_float(row.get("final_action_abs_max")) for row in episodes), default=0.0),
        "same_row_comparison_row_count": len(comparison),
        "same_row_comparison_baseline_counts": dict(sorted(baseline_counts.items())),
        "metric_summary_row_count": len(metric_rows),
        "contract_guard_row_count": len(guard_rows),
        "contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3110_status_pass": _bool(source["m3110_summary"].get("status_pass", False)),
        "m3110_gate_matrix_pass": _bool(source["m3110_summary"].get("gate_matrix_pass", False)),
        "m3105_status_pass": _bool(source["m3105_summary"].get("status_pass", False)),
        "m3095_status_pass": _bool(source["m3095_summary"].get("status_pass", False)),
        "m3100_status_pass": _bool(source["m3100_summary"].get("status_pass", False)),
        "m3090_status_pass": _bool(source["m3090_summary"].get("status_pass", False)),
        "m3084_status_pass": _bool(source["m3084_summary"].get("status_pass", False)),
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "direct_action_formula": "action = residual_collision_offtrack_actor_visible_direct_action(obs72) -> [steer, throttle, brake]",
        "environment_reset_run": bool(episodes),
        "environment_step_run": bool(episodes),
        "policy_action_run": bool(episodes),
        "policy_rollout_run": bool(episodes),
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_collision_offtrack_actor_visible_repair_full_fresh_measurement_route_to_m3113_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    for baseline_id in BASELINE_IDS:
        summary[f"same_row_exact_seed_match_count_{baseline_id}"] = _exact_seed_count(baseline_id)
        summary[f"success_count_delta_vs_{baseline_id}"] = _sum_delta(baseline_id, "success_delta")
        summary[f"collision_count_delta_vs_{baseline_id}"] = _sum_delta(baseline_id, "collision_delta")
        summary[f"offtrack_count_delta_vs_{baseline_id}"] = _sum_delta(baseline_id, "offtrack_delta")
        summary[f"speed_too_low_count_delta_vs_{baseline_id}"] = _sum_delta(baseline_id, "speed_too_low_delta")
        summary[f"clearance_margin_delta_mean_vs_{baseline_id}"] = _mean_delta(baseline_id, "clearance_margin_delta")
        summary[f"return_delta_mean_vs_{baseline_id}"] = _mean_delta(baseline_id, "return_delta")
        summary[f"speed_mean_delta_mean_vs_{baseline_id}"] = _mean_delta(baseline_id, "speed_mean_delta")

    write_json(paths["summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "scheduled_measurement_row_count": len(plan_rows),
            "measurement_episode_row_count": len(episodes),
            "measurement_failure_row_count": len(failures),
            "recorded_row_count": len(episodes) + len(failures),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3111-audit", type=Path, default=DEFAULT_M3111_AUDIT)
    parser.add_argument("--m3110-dir", type=Path, default=DEFAULT_M3110_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3095-dir", type=Path, default=DEFAULT_M3095_DIR)
    parser.add_argument("--m3100-dir", type=Path, default=DEFAULT_M3100_DIR)
    parser.add_argument("--m3090-dir", type=Path, default=DEFAULT_M3090_DIR)
    parser.add_argument("--m3084-dir", type=Path, default=DEFAULT_M3084_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_full_fresh_measurement_preflight(
        m3111_audit=args.m3111_audit,
        m3110_dir=args.m3110_dir,
        m3105_dir=args.m3105_dir,
        m3095_dir=args.m3095_dir,
        m3100_dir=args.m3100_dir,
        m3090_dir=args.m3090_dir,
        m3084_dir=args.m3084_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"measurement_rows={summary['measurement_episode_row_count']}")
    print(f"measurement_failures={summary['measurement_failure_row_count']}")
    print(f"success_count={summary['measurement_success_count']}")
    print(f"collision_count={summary['measurement_collision_count']}")
    print(f"offtrack_count={summary['measurement_offtrack_count']}")
    print(f"speed_too_low_count={summary['measurement_speed_too_low_count']}")
    print(f"same_row_comparison_rows={summary['same_row_comparison_row_count']}")
    print(f"success_delta_vs_m3105={summary['success_count_delta_vs_m3105']}")
    print(f"collision_delta_vs_m3105={summary['collision_count_delta_vs_m3105']}")
    print(f"offtrack_delta_vs_m3105={summary['offtrack_count_delta_vs_m3105']}")
    print(f"speed_too_low_delta_vs_m3105={summary['speed_too_low_count_delta_vs_m3105']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
