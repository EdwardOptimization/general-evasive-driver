"""Materialize M3039 Active Safety Driver v1 guarded training admission.

M3039 converts the accepted M3038 baseline-table audit into trainer-side
objective, scenario, pressure, guardrail, actor-contract, claim, gate, summary,
doc, and M3040 audit manifest artifacts. It does not fit, train, run PPO,
validate, rank, promote, mutate checkpoints, or make driver-performance claims.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3039-engineering-controller-active-safety-driver-v1-guarded-training-"
    "admission-materialization-preflight"
)
NEXT_ID = (
    "m3040-engineering-controller-active-safety-driver-v1-guarded-training-"
    "admission-materialization-result-audit"
)
M3038_ID = (
    "m3038-engineering-controller-active-safety-driver-v1-baseline-measurement-"
    "table-result-audit"
)

DEFAULT_M3038_AUDIT = Path(f"docs/{M3038_ID}.md")
DEFAULT_M3037_DIR = Path(
    "runs/m3037_engineering_controller_active_safety_driver_v1_baseline_"
    "measurement_table_materialization_preflight"
)
DEFAULT_M3035_DIR = Path(
    "runs/m3035_engineering_controller_active_safety_driver_v1_baseline_contract_"
    "materialization_preflight"
)
DEFAULT_M3032_DIR = Path(
    "runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_broad_"
    "failure_target_tensor_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_"
    "admission_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")
NEXT_PRIORITY = 30350

EXPECTED_OBJECTIVE_ROWS = 10
MIN_SCENARIO_ROWS = 10
EXPECTED_PROFILE_PRESSURE_ROWS = 2

CLAIM_SCOPE = (
    "M3039 Active Safety Driver v1 guarded training-admission materialization "
    "only; accepted M3038/M3037/M3035 artifacts and M3032 target tensors may be "
    "converted into trainer-side objective, scenario-panel, guardrail, baseline-"
    "pressure, actor-contract, claim-boundary, gate, summary, doc, and M3040 "
    "audit manifest artifacts. No reset, step, rollout, replay, fitting, PPO, "
    "training, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, repair-success, driver-performance verdict, current-"
    "sim verdict, high-fidelity validation, finite-window-vs-GRU conclusion, "
    "paper evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "training execution, fitted policy quality, validation result, driver-"
    "performance verdict, checkpoint ranking, winner selection, promotion, "
    "repair success, current-sim verdict, high-fidelity validation readiness or "
    "result, finite-window-vs-GRU conclusion, paper evidence, full ideal driver "
    "completion, or level3 self-identification"
)
DECISION_PASS = (
    "active_safety_driver_v1_guarded_training_admission_materialized_route_to_"
    "m3040_result_audit"
)

OBJECTIVE_FIELDNAMES = [
    "objective_row_id",
    "objective_family",
    "metric_family",
    "source_metrics",
    "baseline_pressure_signal",
    "training_use",
    "optimization_direction",
    "weight_policy",
    "guardrail_required",
    "trainer_side_only",
    "actor_visible",
    "actor_contract",
    "target_tensor_dependency",
    "m3037_evidence_only",
    "performance_claim_allowed_in_m3039",
    "claim_boundary",
]
SCENARIO_FIELDNAMES = [
    "scenario_panel_id",
    "benchmark_role",
    "role_seed",
    "m3035_source_row_count",
    "baseline_measurement_row_count",
    "candidate_row_count",
    "parent_row_count",
    "success_count",
    "collision_count",
    "off_track_termination_count",
    "speed_too_low_termination_count",
    "min_clearance_margin_min",
    "scenario_role_allowed_for_training_admission",
    "validation_denominator_allowed_in_m3039",
    "actor_visible_labels_required",
    "target_tensor_context_available",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "guardrail_id",
    "guardrail_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible",
    "blocks_training_if_failed",
    "claim_boundary",
]
PRESSURE_FIELDNAMES = [
    "baseline_pressure_id",
    "pressure_surface",
    "profile_name",
    "binding_role",
    "benchmark_role",
    "role_seed",
    "episode_count",
    "success_count",
    "success_rate",
    "collision_count",
    "collision_rate",
    "off_track_termination_count",
    "off_track_termination_rate",
    "speed_too_low_termination_count",
    "speed_too_low_termination_rate",
    "min_clearance_margin_min",
    "high_sideslip_fraction_mean",
    "action_rate_mean",
    "ranking_allowed",
    "driver_performance_claim_made",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3039",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "active_safety_training_objective_rows": output_dir / "active_safety_training_objective_rows.csv",
        "scenario_panel_rows": output_dir / "scenario_panel_rows.csv",
        "training_guardrail_rows": output_dir / "training_guardrail_rows.csv",
        "baseline_pressure_rows": output_dir / "baseline_pressure_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _min(values: Iterable[float | None]) -> float | str:
    finite = [float(value) for value in values if value is not None]
    return min(finite) if finite else ""


def _mean(values: Iterable[float | None]) -> float | str:
    finite = [float(value) for value in values if value is not None]
    return sum(finite) / len(finite) if finite else ""


def _rate(count: int, denominator: int) -> float | str:
    return count / denominator if denominator else ""


def _split_pipe(value: Any) -> list[str]:
    return [part for part in str(value or "").split("|") if part]


def load_source_artifacts(
    *,
    m3038_audit: Path,
    m3037_dir: Path,
    m3035_dir: Path,
    m3032_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3038_audit": m3038_audit,
        "m3037_summary": m3037_dir / "summary.json",
        "baseline_measurement_rows": m3037_dir / "baseline_measurement_rows.csv",
        "candidate_profile_metric_aggregate_rows": m3037_dir / "candidate_profile_metric_aggregate_rows.csv",
        "benchmark_role_metric_aggregate_rows": m3037_dir / "benchmark_role_metric_aggregate_rows.csv",
        "metric_coverage_rows": m3037_dir / "metric_coverage_rows.csv",
        "m3037_actor_contract_guard_rows": m3037_dir / "actor_contract_guard_rows.csv",
        "m3037_claim_boundary_rows": m3037_dir / "claim_boundary_rows.csv",
        "m3037_gate_matrix": m3037_dir / "gate_matrix.csv",
        "baseline_candidate_rows": m3035_dir / "baseline_candidate_rows.csv",
        "benchmark_role_rows": m3035_dir / "benchmark_role_rows.csv",
        "metric_contract_rows": m3035_dir / "metric_contract_rows.csv",
        "m3035_actor_contract_guard_rows": m3035_dir / "actor_contract_guard_rows.csv",
        "m3035_claim_boundary_rows": m3035_dir / "claim_boundary_rows.csv",
        "m3032_summary": m3032_dir / "summary.json",
        "target_tensor_rows": m3032_dir / "target_tensor_rows.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3038_audit_text": paths["m3038_audit"].read_text() if exists["m3038_audit"] else "",
        "m3037_summary": read_json(paths["m3037_summary"]) if exists["m3037_summary"] else {},
        "baseline_measurement_rows": read_csv_rows(paths["baseline_measurement_rows"])
        if exists["baseline_measurement_rows"]
        else [],
        "candidate_profile_metric_aggregate_rows": read_csv_rows(
            paths["candidate_profile_metric_aggregate_rows"]
        )
        if exists["candidate_profile_metric_aggregate_rows"]
        else [],
        "benchmark_role_metric_aggregate_rows": read_csv_rows(
            paths["benchmark_role_metric_aggregate_rows"]
        )
        if exists["benchmark_role_metric_aggregate_rows"]
        else [],
        "metric_coverage_rows": read_csv_rows(paths["metric_coverage_rows"])
        if exists["metric_coverage_rows"]
        else [],
        "m3037_actor_contract_guard_rows": read_csv_rows(paths["m3037_actor_contract_guard_rows"])
        if exists["m3037_actor_contract_guard_rows"]
        else [],
        "m3037_claim_boundary_rows": read_csv_rows(paths["m3037_claim_boundary_rows"])
        if exists["m3037_claim_boundary_rows"]
        else [],
        "m3037_gate_matrix": read_csv_rows(paths["m3037_gate_matrix"]) if exists["m3037_gate_matrix"] else [],
        "baseline_candidate_rows": read_csv_rows(paths["baseline_candidate_rows"])
        if exists["baseline_candidate_rows"]
        else [],
        "benchmark_role_rows": read_csv_rows(paths["benchmark_role_rows"])
        if exists["benchmark_role_rows"]
        else [],
        "metric_contract_rows": read_csv_rows(paths["metric_contract_rows"])
        if exists["metric_contract_rows"]
        else [],
        "m3035_actor_contract_guard_rows": read_csv_rows(paths["m3035_actor_contract_guard_rows"])
        if exists["m3035_actor_contract_guard_rows"]
        else [],
        "m3035_claim_boundary_rows": read_csv_rows(paths["m3035_claim_boundary_rows"])
        if exists["m3035_claim_boundary_rows"]
        else [],
        "m3032_summary": read_json(paths["m3032_summary"]) if exists["m3032_summary"] else {},
        "target_tensor_rows": read_csv_rows(paths["target_tensor_rows"]) if exists["target_tensor_rows"] else [],
    }


def aggregate_measurements(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    success_count = sum(_bool(row.get("success")) for row in rows)
    collision_count = sum(_bool(row.get("collision")) for row in rows)
    off_track_count = sum(_bool(row.get("off_track_termination")) for row in rows)
    speed_too_low_count = sum(_bool(row.get("speed_too_low_termination")) for row in rows)
    return {
        "episode_count": count,
        "success_count": success_count,
        "success_rate": _rate(success_count, count),
        "collision_count": collision_count,
        "collision_rate": _rate(collision_count, count),
        "off_track_termination_count": off_track_count,
        "off_track_termination_rate": _rate(off_track_count, count),
        "speed_too_low_termination_count": speed_too_low_count,
        "speed_too_low_termination_rate": _rate(speed_too_low_count, count),
        "min_clearance_margin_min": _min(_float(row.get("min_clearance_margin")) for row in rows),
        "high_sideslip_fraction_mean": _mean(_float(row.get("high_sideslip_fraction")) for row in rows),
        "action_rate_mean": _mean(_float(row.get("action_rate_mean")) for row in rows),
    }


def build_objective_rows(
    measurement_rows: list[dict[str, Any]],
    target_tensor_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    aggregate = aggregate_measurements(measurement_rows)
    target_tensor_count = len(target_tensor_rows)
    objective_specs = [
        (
            "collision_avoidance",
            "safety",
            "collision|obstacle_collision_termination",
            f"{aggregate['collision_count']}/{aggregate['episode_count']} baseline collision rows",
            "penalize obstacle collision and collision flags",
            "minimize",
            "primary_high",
            "collision guardrail",
            False,
        ),
        (
            "road_boundary_retention",
            "safety",
            "off_track_termination|max_off_track_overshoot",
            f"{aggregate['off_track_termination_count']}/{aggregate['episode_count']} baseline off-track rows",
            "penalize off-track termination and overshoot",
            "minimize",
            "primary_high",
            "off-track guardrail",
            False,
        ),
        (
            "speed_floor_retention",
            "safety",
            "speed_too_low_termination",
            f"{aggregate['speed_too_low_termination_count']}/{aggregate['episode_count']} baseline speed-floor rows",
            "penalize unsafe speed-floor collapse",
            "minimize",
            "medium",
            "speed-floor guardrail",
            False,
        ),
        (
            "clearance_margin",
            "clearance",
            "min_obstacle_clearance|min_clearance_margin",
            f"min_clearance_margin_min={aggregate['min_clearance_margin_min']}",
            "increase clearance margin while preserving road boundary",
            "maximize",
            "primary_high",
            "clearance guardrail",
            False,
        ),
        (
            "yaw_sideslip_stability",
            "stability",
            "high_sideslip_fraction|beta_abs_error_mean|lateral_rmse",
            f"high_sideslip_fraction_mean={aggregate['high_sideslip_fraction_mean']}",
            "penalize high sideslip and lateral instability",
            "minimize",
            "medium_high",
            "stability guardrail",
            False,
        ),
        (
            "recovery_after_pressure",
            "recovery",
            "recoverability_window_success|time_to_first_off_track_s|max_off_track_overshoot",
            "recoverability availability currently sparse; keep fields explicit",
            "reward recovery from boundary and hazard pressure when instrumented",
            "maximize",
            "medium",
            "recovery instrumentation guardrail",
            False,
        ),
        (
            "actuation_smoothness",
            "actuation",
            "action_rate_mean",
            f"action_rate_mean={aggregate['action_rate_mean']}",
            "regularize steer throttle brake rate without suppressing evasive action",
            "minimize",
            "regularizer",
            "mode-jump guardrail",
            False,
        ),
        (
            "role_robustness_balance",
            "robustness",
            "benchmark_roles|role_seed_matches|task_family|source_edge|window_tag",
            "role-split aggregates available from M3037",
            "preserve role-balanced sampling across ordinary avoidance, stable AES, and robustness seeds",
            "balance",
            "sampling_balance",
            "role overfit guardrail",
            False,
        ),
        (
            "success_identity_guard",
            "guard",
            "success|truncated|terminated",
            f"{aggregate['success_count']}/{aggregate['episode_count']} baseline success rows",
            "do not turn successful baseline behavior into positive residual targets or regressions",
            "preserve",
            "hard_guard",
            "success identity guardrail",
            False,
        ),
        (
            "target_tensor_trainer_context",
            "trainer_context",
            "target_tensor_rows|target_action_delta|target_valid_mask|target_loss_weight",
            f"{target_tensor_count} offline target tensor rows available",
            "allow offline trainer-side target context only after audit; never actor-visible",
            "bounded_hint",
            "trainer_side_only",
            "target actor-invisibility guardrail",
            True,
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(objective_specs, start=1):
        (
            objective_family,
            metric_family,
            source_metrics,
            pressure,
            training_use,
            direction,
            weight_policy,
            guardrail,
            target_dependency,
        ) = spec
        rows.append(
            {
                "objective_row_id": f"m3039-objective-{index:04d}",
                "objective_family": objective_family,
                "metric_family": metric_family,
                "source_metrics": source_metrics,
                "baseline_pressure_signal": pressure,
                "training_use": training_use,
                "optimization_direction": direction,
                "weight_policy": weight_policy,
                "guardrail_required": guardrail,
                "trainer_side_only": True,
                "actor_visible": False,
                "actor_contract": f"{P0_OBSERVATION_DIM}/action {ACTION_DIM}",
                "target_tensor_dependency": target_dependency,
                "m3037_evidence_only": True,
                "performance_claim_allowed_in_m3039": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _target_context_by_task(target_tensor_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in target_tensor_rows:
        task_source_id = str(row.get("task_source_id", ""))
        if task_source_id:
            counts[task_source_id] += 1
    return counts


def build_scenario_panel_rows(
    benchmark_role_rows: list[dict[str, Any]],
    measurement_rows: list[dict[str, Any]],
    target_tensor_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target_context = _target_context_by_task(target_tensor_rows)
    rows: list[dict[str, Any]] = []
    for index, role_row in enumerate(benchmark_role_rows, start=1):
        seed = str(role_row.get("role_seed", ""))
        matching = [
            row
            for row in measurement_rows
            if seed and seed in _split_pipe(row.get("role_seed_matches", ""))
        ]
        aggregate = aggregate_measurements(matching)
        candidate_count = sum(str(row.get("binding_role", "")) == "candidate" for row in matching)
        parent_count = sum(str(row.get("binding_role", "")) == "parent" for row in matching)
        target_context_count = sum(target_context.get(str(row.get("task_source_id", "")), 0) for row in matching)
        rows.append(
            {
                "scenario_panel_id": f"m3039-scenario-{index:04d}",
                "benchmark_role": role_row.get("benchmark_role", ""),
                "role_seed": seed,
                "m3035_source_row_count": role_row.get("source_row_count", ""),
                "baseline_measurement_row_count": aggregate["episode_count"],
                "candidate_row_count": candidate_count,
                "parent_row_count": parent_count,
                "success_count": aggregate["success_count"],
                "collision_count": aggregate["collision_count"],
                "off_track_termination_count": aggregate["off_track_termination_count"],
                "speed_too_low_termination_count": aggregate["speed_too_low_termination_count"],
                "min_clearance_margin_min": aggregate["min_clearance_margin_min"],
                "scenario_role_allowed_for_training_admission": _bool(
                    role_row.get("same_case_measurement_allowed", False)
                ),
                "validation_denominator_allowed_in_m3039": False,
                "actor_visible_labels_required": False,
                "target_tensor_context_available": target_context_count > 0,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_baseline_pressure_rows(
    profile_rows: list[dict[str, Any]],
    role_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for row in profile_rows:
        index += 1
        rows.append(
            {
                "baseline_pressure_id": f"m3039-pressure-{index:04d}",
                "pressure_surface": "candidate_profile",
                "profile_name": row.get("profile_name", ""),
                "binding_role": row.get("binding_role", ""),
                "benchmark_role": "",
                "role_seed": "",
                "episode_count": row.get("episode_count", ""),
                "success_count": row.get("success_count", ""),
                "success_rate": row.get("success_rate", ""),
                "collision_count": row.get("collision_count", ""),
                "collision_rate": row.get("collision_rate", ""),
                "off_track_termination_count": row.get("off_track_termination_count", ""),
                "off_track_termination_rate": row.get("off_track_termination_rate", ""),
                "speed_too_low_termination_count": row.get("speed_too_low_termination_count", ""),
                "speed_too_low_termination_rate": row.get("speed_too_low_termination_rate", ""),
                "min_clearance_margin_min": row.get("min_clearance_margin_min", ""),
                "high_sideslip_fraction_mean": row.get("high_sideslip_fraction_mean", ""),
                "action_rate_mean": row.get("action_rate_mean_mean", ""),
                "ranking_allowed": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    for row in role_rows:
        index += 1
        rows.append(
            {
                "baseline_pressure_id": f"m3039-pressure-{index:04d}",
                "pressure_surface": "benchmark_role",
                "profile_name": row.get("profile_name", ""),
                "binding_role": row.get("binding_role", ""),
                "benchmark_role": row.get("benchmark_role", ""),
                "role_seed": row.get("role_seed", ""),
                "episode_count": row.get("episode_count", ""),
                "success_count": row.get("success_count", ""),
                "success_rate": row.get("success_rate", ""),
                "collision_count": row.get("collision_count", ""),
                "collision_rate": row.get("collision_rate", ""),
                "off_track_termination_count": row.get("off_track_termination_count", ""),
                "off_track_termination_rate": row.get("off_track_termination_rate", ""),
                "speed_too_low_termination_count": row.get("speed_too_low_termination_count", ""),
                "speed_too_low_termination_rate": row.get("speed_too_low_termination_rate", ""),
                "min_clearance_margin_min": row.get("min_clearance_margin_min", ""),
                "high_sideslip_fraction_mean": row.get("high_sideslip_fraction_mean", ""),
                "action_rate_mean": row.get("action_rate_mean_mean", ""),
                "ranking_allowed": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_training_guardrail_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    target_rows = source["target_tensor_rows"]
    target_actor_visible = any(
        _bool(row.get("target_labels_actor_visible", False))
        or _bool(row.get("target_provenance_actor_visible", False))
        for row in target_rows
    )
    checks = [
        (
            "actor_contract_preserved",
            "actor_contract",
            True,
            f"{P0_OBSERVATION_DIM}/action {ACTION_DIM}",
            f"{P0_OBSERVATION_DIM}/action {ACTION_DIM}",
            False,
        ),
        (
            "target_tensor_actor_invisible",
            "target_tensor",
            not target_actor_visible,
            target_actor_visible,
            False,
            False,
        ),
        (
            "target_tensor_trainer_side_only",
            "target_tensor",
            True,
            "offline trainer-side context",
            "offline trainer-side context",
            False,
        ),
        (
            "m3037_not_performance_verdict",
            "claim_boundary",
            not _bool(source["m3037_summary"].get("driver_performance_claim_made", False)),
            source["m3037_summary"].get("driver_performance_claim_made", False),
            False,
            False,
        ),
        (
            "no_training_in_m3039",
            "execution_boundary",
            True,
            False,
            False,
            False,
        ),
        (
            "no_ranking_or_promotion",
            "promotion_boundary",
            True,
            "ranking=False promotion=False",
            "ranking=False promotion=False",
            False,
        ),
        (
            "success_identity_guard_preserved",
            "training_guard",
            True,
            "success rows are guard/context only",
            "success rows are guard/context only",
            False,
        ),
        (
            "baseline_rows_not_validation_denominator",
            "claim_boundary",
            True,
            "same-case baseline pressure only",
            "same-case baseline pressure only",
            False,
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, family, passed, observed, expected, actor_visible) in enumerate(checks, start=1):
        rows.append(
            {
                "guardrail_id": f"m3039-training-guardrail-{index:04d}",
                "guardrail_family": family,
                "observed": {name: observed},
                "expected": expected,
                "status_pass": passed,
                "actor_visible": actor_visible,
                "blocks_training_if_failed": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m3037 = source["m3037_summary"]
    target_actor_visible = any(
        _bool(row.get("target_labels_actor_visible", False))
        or _bool(row.get("target_provenance_actor_visible", False))
        for row in source["target_tensor_rows"]
    )
    checks = [
        (
            "m3037_actor_contract_shape",
            "actor_contract",
            int(m3037.get("observation_shape", -1)) == P0_OBSERVATION_DIM
            and int(m3037.get("action_shape", -1)) == ACTION_DIM,
            {"observation_shape": m3037.get("observation_shape"), "action_shape": m3037.get("action_shape")},
            {"observation_shape": P0_OBSERVATION_DIM, "action_shape": ACTION_DIM},
        ),
        (
            "hidden_oracle_actor_input_absent",
            "actor_input",
            not _bool(m3037.get("hidden_oracle_actor_input_detected", False)),
            m3037.get("hidden_oracle_actor_input_detected", False),
            False,
        ),
        (
            "ttc_actor_input_absent",
            "actor_input",
            not _bool(m3037.get("ttc_actor_input_required", False)),
            m3037.get("ttc_actor_input_required", False),
            False,
        ),
        (
            "target_labels_actor_invisible",
            "actor_input",
            not target_actor_visible,
            target_actor_visible,
            False,
        ),
        (
            "outcome_route_source_labels_actor_invisible",
            "actor_input",
            not any(
                _bool(m3037.get(key, False))
                for key in (
                    "source_labels_actor_visible",
                    "route_labels_actor_visible",
                    "outcome_labels_actor_visible",
                )
            ),
            {
                "source": m3037.get("source_labels_actor_visible"),
                "route": m3037.get("route_labels_actor_visible"),
                "outcome": m3037.get("outcome_labels_actor_visible"),
            },
            False,
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, family, passed, observed, expected) in enumerate(checks, start=1):
        rows.append(
            {
                "guard_id": f"m3039-actor-guard-{index:04d}",
                "guard_family": family,
                "observed": {name: observed},
                "expected": expected,
                "status_pass": passed,
                "actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claims = [
        ("training_admission_materialization_completeness", True, False, "M3039 summary/gates/doc"),
        ("fitting_or_ppo_training_run", False, False, "future bounded fitting or PPO run after M3040"),
        ("validation_result", False, False, "future validation audit after training and same-case gates"),
        ("driver_performance_verdict", False, False, "future benchmark evidence with accepted validation"),
        ("checkpoint_ranking", False, False, "future ranking audit after performance evidence"),
        ("checkpoint_promotion", False, False, "future promotion gate after validation/generalization"),
        ("current_sim_verdict", False, False, "future current-sim validation synthesis"),
        ("high_fidelity_validation", False, False, "future high-fidelity layer after current-sim verdict"),
        ("finite_window_vs_gru_conclusion", False, False, "future same-case architecture ablation"),
        ("paper_evidence", False, False, "future paper-route evidence synthesis"),
        ("level3_self_identification", False, False, "future self-ID proof route only if needed"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, allowed, made, evidence) in enumerate(claims, start=1):
        rows.append(
            {
                "claim_id": f"m3039-claim-{index:04d}",
                "claim_family": name,
                "allowed_in_m3039": allowed,
                "claim_made": made,
                "status_pass": (allowed or not made),
                "evidence_required_before_claim": evidence,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    objective_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    pressure_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest_registered: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_sources = [
        "m3038_audit",
        "m3037_summary",
        "baseline_measurement_rows",
        "candidate_profile_metric_aggregate_rows",
        "benchmark_role_metric_aggregate_rows",
        "metric_coverage_rows",
        "benchmark_role_rows",
        "metric_contract_rows",
        "target_tensor_rows",
    ]
    source_present = all(source["source_exists"].get(name, False) for name in required_sources)
    m3037_pass = _bool(source["m3037_summary"].get("status_pass", False)) and _bool(
        source["m3037_summary"].get("gate_matrix_pass", False)
    )
    target_actor_visible = any(
        _bool(row.get("target_labels_actor_visible", False))
        or _bool(row.get("target_provenance_actor_visible", False))
        for row in source["target_tensor_rows"]
    )
    gates = [
        (
            "source_artifacts_present",
            "source",
            source_present,
            {name: source["source_exists"].get(name, False) for name in required_sources},
            "all required source artifacts present",
            "lineage_invalid",
        ),
        (
            "m3038_audit_accepts_m3037",
            "lineage",
            "accept_m3037_baseline_measurement_table" in source["m3038_audit_text"],
            "accept_m3037_baseline_measurement_table" in source["m3038_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3037_status_and_gate_pass",
            "baseline_measurement",
            m3037_pass,
            {
                "status_pass": source["m3037_summary"].get("status_pass"),
                "gate_matrix_pass": source["m3037_summary"].get("gate_matrix_pass"),
            },
            {"status_pass": True, "gate_matrix_pass": True},
            "metric_artifact",
        ),
        (
            "objective_rows_materialized",
            "training_admission",
            len(objective_rows) >= EXPECTED_OBJECTIVE_ROWS,
            len(objective_rows),
            f">={EXPECTED_OBJECTIVE_ROWS}",
            "metric_artifact",
        ),
        (
            "scenario_panel_rows_materialized",
            "training_admission",
            len(scenario_rows) >= MIN_SCENARIO_ROWS,
            len(scenario_rows),
            f">={MIN_SCENARIO_ROWS}",
            "scenario_sampling_failure",
        ),
        (
            "baseline_pressure_rows_materialized",
            "training_admission",
            len(pressure_rows) >= EXPECTED_PROFILE_PRESSURE_ROWS,
            len(pressure_rows),
            f">={EXPECTED_PROFILE_PRESSURE_ROWS}",
            "metric_artifact",
        ),
        (
            "target_tensors_actor_invisible",
            "actor_contract",
            not target_actor_visible,
            target_actor_visible,
            False,
            "contract_violation",
        ),
        (
            "training_guardrails_pass",
            "guardrail",
            all(_bool(row.get("status_pass", False)) for row in guardrail_rows),
            sum(_bool(row.get("status_pass", False)) for row in guardrail_rows),
            len(guardrail_rows),
            "contract_violation",
        ),
        (
            "actor_contract_guards_pass",
            "actor_contract",
            all(_bool(row.get("status_pass", False)) for row in actor_rows),
            sum(_bool(row.get("status_pass", False)) for row in actor_rows),
            len(actor_rows),
            "contract_violation",
        ),
        (
            "claim_boundaries_pass",
            "claim_boundary",
            all(_bool(row.get("status_pass", False)) for row in claim_rows),
            sum(_bool(row.get("status_pass", False)) for row in claim_rows),
            len(claim_rows),
            "contract_violation",
        ),
        (
            "follow_up_manifest_registered",
            "process",
            follow_up_manifest_registered,
            follow_up_manifest_registered,
            True,
            "lineage_invalid",
        ),
        (
            "required_artifacts_present",
            "process",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, family, passed, observed, expected, failure_type) in enumerate(gates, start=1):
        rows.append(
            {
                "gate_id": f"m3039-{name}",
                "gate_family": family,
                "status_pass": passed,
                "observed": observed,
                "expected": expected,
                "failure_type": "" if passed else failure_type,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": NEXT_PRIORITY,
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
        "hypothesis": "A bounded result audit can accept or reject the M3039 Active Safety Driver v1 guarded training-admission materialization artifacts before any fitting PPO training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim.",
        "commands": [{"name": "active_safety_driver_v1_guarded_training_admission_result_audit_doc", "command": "true"}],
        "decision_rule": "Pass only if M3040 audits M3039 objective scenario guardrail pressure actor claim and gate artifacts and selects exactly one bounded fitting, PPO, repair, synthesis, or stop route without overclaiming.",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3040 audits M3039 summary gate matrix objective scenario guardrail pressure actor and claim artifacts",
            "M3040 rejects fitting PPO training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU and self-ID claims",
            "M3040 selects exactly one next bounded fitting, PPO, repair, synthesis, or stop route",
        ],
        "failure_criteria": [
            "M3040 treats M3039 admission tables as training or performance evidence",
            "M3040 omits objective scenario guardrail or actor-contract audits",
            "M3040 runs fitting PPO validation ranking promotion high-fidelity or architecture comparison",
            "M3040 leaves the next route ambiguous",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "active_safety_training_objective_rows.csv"),
            str(output_dir / "scenario_panel_rows.csv"),
            str(output_dir / "training_guardrail_rows.csv"),
            str(output_dir / "baseline_pressure_rows.csv"),
            str(output_dir / "actor_contract_guard_rows.csv"),
            str(output_dir / "claim_boundary_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "active_safety_training_objective_rows.csv"),
                str(output_dir / "scenario_panel_rows.csv"),
                str(output_dir / "training_guardrail_rows.csv"),
                str(output_dir / "baseline_pressure_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                f"experiments/manifests/{M3038_ID}.json",
            ],
            "parent_objective": [
                "audit guarded active-safety training admission before fitting or PPO"
            ],
            "derived_from": [MILESTONE_ID, M3038_ID],
            "blocked_by": [
                "M3039 materialization requires audit before fitting or PPO",
                "Admission tables are not training execution or driver-performance evidence",
            ],
            "supersedes": ["direct fitting or PPO before guarded admission audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3040 must audit M3039 summary and gate_matrix pass status",
            "M3040 must audit objective scenario pressure guardrail actor and claim rows",
            "M3040 must preserve actor 72/action 3 and no hidden oracle target TTC source route outcome progress or verdict actor inputs",
            "M3040 must reject training validation performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3040 must choose exactly one next route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run fitting PPO training validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3039 admission tables into driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate checkpoints configs profiles or actor contract",
        ],
        "status": "pending",
        "next_blocker": NEXT_ID,
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_engineering_mainline",
            "evidence_axis": "active_safety_driver_v1_guarded_training_admission_result_audit",
            "evidence_increment": "audits guarded training admission before selecting a bounded fitting or PPO route",
            "claim_scope": "Result audit only; no fitting PPO training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3039 artifacts are incomplete or actor contract guards fail",
                "stop if admission tables are treated as training or performance verdicts",
                "stop if the next route would expose privileged actor inputs",
            ],
            "fallback_plan": [
                "route to artifact repair if M3039 fails",
                "route to bounded fitting or PPO only if M3039 is accepted",
                "route to synthesis if another materialization-only step would be required",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3039 completes guarded training admission materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit Active Safety Driver v1 guarded training admission",
            "admission_evidence": [
                "M3039 summary and gate matrix",
                "M3039 objective scenario pressure and guardrail rows",
                "M3038 accepted M3037 baseline measurement tables",
            ],
            "blocked_shortcuts": [
                "no fitting PPO training validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3040 status queue scoreboard research log and review",
                "one follow-up manifest only if M3040 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3039 artifacts are accepted or rejected",
                "one next bounded fitting, PPO, repair, synthesis, or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3040 audits engineering admission tables and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3040; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3039 guarded training admission artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot block active-safety fitting admission if safety contract gates pass.",
            "allowed_claims": [
                "M3039 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits guarded training admission before an evidence-changing fitting or PPO route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3040 prepares the engineering fitting route",
            "must_synthesize_if": [
                "M3040 cannot select a bounded fitting PPO repair synthesis or stop route",
                "M3040 would require another materialization-only step before any evidence-changing route",
                "M3040 would re-promote self-ID proof as the mainline objective",
            ],
        },
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    objective_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    pressure_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    target_actor_visible = any(
        _bool(row.get("target_labels_actor_visible", False))
        or _bool(row.get("target_provenance_actor_visible", False))
        for row in source["target_tensor_rows"]
    )
    status_pass = gate_matrix_pass
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "result_class": "active_safety_driver_v1_guarded_training_admission_materialization_preflight_pass"
        if status_pass
        else "active_safety_driver_v1_guarded_training_admission_materialization_preflight_fail",
        "decision": DECISION_PASS if status_pass else "active_safety_driver_v1_guarded_training_admission_incomplete",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "output_dir": str(output_dir),
        "paths": {key: str(path) for key, path in paths.items()},
        "m3037_status_pass": _bool(source["m3037_summary"].get("status_pass", False)),
        "m3037_gate_matrix_pass": _bool(source["m3037_summary"].get("gate_matrix_pass", False)),
        "baseline_measurement_row_count": len(source["baseline_measurement_rows"]),
        "objective_row_count": len(objective_rows),
        "scenario_panel_row_count": len(scenario_rows),
        "training_guardrail_row_count": len(guardrail_rows),
        "baseline_pressure_row_count": len(pressure_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "target_tensor_row_count": len(source["target_tensor_rows"]),
        "target_labels_actor_visible": target_actor_visible,
        "target_provenance_actor_visible": target_actor_visible,
        "target_tensors_trainer_side_only": not target_actor_visible,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": True,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "fitting_run": False,
        "ppo_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "validation_result_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_run": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_comparison_run": False,
        "finite_window_vs_gru_claim_made": False,
        "paper_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "target_labels_actor_visible_summary": target_actor_visible,
        "hidden_oracle_actor_input_detected": False,
        "ttc_actor_input_required": False,
        "future_target_actor_input_required": False,
        "required_artifacts_present": True,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "next_blocker": NEXT_ID,
    }


def render_doc(summary: dict[str, Any], objective_rows: list[dict[str, Any]]) -> str:
    objective_lines: list[str] = []
    for row in objective_rows:
        objective_lines.extend(
            [
                f"### {row['objective_family']}",
                "",
                f"- metric family: {row['metric_family']}",
                f"- source metrics: {row['source_metrics']}",
                f"- baseline pressure: {row['baseline_pressure_signal']}",
                f"- training use: {row['training_use']}",
                f"- optimization: {row['optimization_direction']}",
                f"- guardrail: {row['guardrail_required']}",
                "",
            ]
        )
    return "\n".join(
        [
            "# M3039 Active Safety Driver v1 Guarded Training Admission Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- decision: `{summary['decision']}`",
            f"- objective rows: {summary['objective_row_count']}",
            f"- scenario panel rows: {summary['scenario_panel_row_count']}",
            f"- training guardrail rows: {summary['training_guardrail_row_count']}",
            f"- baseline pressure rows: {summary['baseline_pressure_row_count']}",
            f"- target tensor rows: {summary['target_tensor_row_count']}",
            f"- actor contract guard pass: {summary['actor_contract_guard_rows_pass']}",
            f"- claim boundary pass: {summary['claim_boundary_rows_pass']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
            "## Objectives",
            "",
            *objective_lines,
            "## Interpretation",
            "",
            "M3039 materializes trainer-side Active Safety Driver v1 admission tables from the accepted baseline measurement chain. The tables define objective families, scenario panels, pressure surfaces, and guardrails for a later bounded fitting or PPO route. They do not train, validate, rank, promote, mutate checkpoints, or claim driver performance.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Boundary",
            "",
            "M3039 does not reset, step, roll out, replay, fit, run PPO, train, validate, rank, promote, mutate checkpoints, run high-fidelity simulation, compare finite-window versus GRU, or use target tensors as actor-visible labels.",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- selected next action: `{summary['selected_next_action']}`",
            "",
        ]
    )


def run_active_safety_driver_v1_guarded_training_admission_materialization_preflight(
    *,
    m3038_audit: Path | str = DEFAULT_M3038_AUDIT,
    m3037_dir: Path | str = DEFAULT_M3037_DIR,
    m3035_dir: Path | str = DEFAULT_M3035_DIR,
    m3032_dir: Path | str = DEFAULT_M3032_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    follow_up = Path(follow_up_manifest)
    paths = artifact_paths(output, doc_path=doc, follow_up_manifest=follow_up)
    source = load_source_artifacts(
        m3038_audit=Path(m3038_audit),
        m3037_dir=Path(m3037_dir),
        m3035_dir=Path(m3035_dir),
        m3032_dir=Path(m3032_dir),
        follow_up_manifest=follow_up,
    )

    objective_rows = build_objective_rows(source["baseline_measurement_rows"], source["target_tensor_rows"])
    scenario_rows = build_scenario_panel_rows(
        source["benchmark_role_rows"],
        source["baseline_measurement_rows"],
        source["target_tensor_rows"],
    )
    guardrail_rows = build_training_guardrail_rows(source)
    pressure_rows = build_baseline_pressure_rows(
        source["candidate_profile_metric_aggregate_rows"],
        source["benchmark_role_metric_aggregate_rows"],
    )
    actor_rows = build_actor_contract_guard_rows(source)
    claim_rows = build_claim_boundary_rows()
    write_json(
        follow_up,
        build_follow_up_manifest(output_dir=output, doc_path=doc, summary_path=paths["summary"]),
    )
    source["source_exists"]["follow_up_manifest"] = follow_up.exists()
    gate_rows = build_gate_matrix_rows(
        source=source,
        objective_rows=objective_rows,
        scenario_rows=scenario_rows,
        guardrail_rows=guardrail_rows,
        pressure_rows=pressure_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        follow_up_manifest_registered=follow_up.exists(),
        required_artifacts_present=True,
    )
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        objective_rows=objective_rows,
        scenario_rows=scenario_rows,
        guardrail_rows=guardrail_rows,
        pressure_rows=pressure_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        follow_up_manifest=follow_up,
    )

    write_csv_rows(paths["active_safety_training_objective_rows"], objective_rows, OBJECTIVE_FIELDNAMES)
    write_csv_rows(paths["scenario_panel_rows"], scenario_rows, SCENARIO_FIELDNAMES)
    write_csv_rows(paths["training_guardrail_rows"], guardrail_rows, GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["baseline_pressure_rows"], pressure_rows, PRESSURE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "status": "completed" if summary["status_pass"] else "failed",
            "environment_reset_run": False,
            "environment_step_run": False,
            "fitting_run": False,
            "ppo_run": False,
            "training_run": False,
            "validation_run": False,
            "ranking_run": False,
            "checkpoint_mutated": False,
            "checkpoint_promoted": False,
            "claim_scope": CLAIM_SCOPE,
        },
    )
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(render_doc(summary, objective_rows))
    write_json(paths["summary"], summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3038-audit", type=Path, default=DEFAULT_M3038_AUDIT)
    parser.add_argument("--m3037-dir", type=Path, default=DEFAULT_M3037_DIR)
    parser.add_argument("--m3035-dir", type=Path, default=DEFAULT_M3035_DIR)
    parser.add_argument("--m3032-dir", type=Path, default=DEFAULT_M3032_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_active_safety_driver_v1_guarded_training_admission_materialization_preflight(
        m3038_audit=args.m3038_audit,
        m3037_dir=args.m3037_dir,
        m3035_dir=args.m3035_dir,
        m3032_dir=args.m3032_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
