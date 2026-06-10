"""Materialize M3133 corridor-reflex regression failure decomposition artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3133-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-"
    "level-clearance-stability-corridor-reflex-regression-failure-decomposition-"
    "materialization-preflight"
)
NEXT_ID = (
    "m3134-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-"
    "level-clearance-stability-corridor-reflex-regression-failure-decomposition-result-audit"
)
M3132_ID = (
    "m3132-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-"
    "level-clearance-stability-corridor-reflex-full-fresh-measurement-result-audit"
)
M3131_ID = (
    "m3131-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-"
    "level-clearance-stability-corridor-reflex-full-fresh-measurement-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3132_AUDIT = Path(f"docs/{M3132_ID}.md")
DEFAULT_M3131_DIR = Path(
    "runs/m3131_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_"
    "clearance_stability_corridor_reflex_full_fresh_measurement_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3133_engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_"
    "clearance_stability_corridor_reflex_regression_failure_decomposition_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_FULL_ROWS = 64
EXPECTED_BASELINE_ID = "m3105"
EXPECTED_SUCCESS_DELTA_VS_M3105 = -22
EXPECTED_COLLISION_DELTA_VS_M3105 = 2
EXPECTED_OFFTRACK_DELTA_VS_M3105 = 12
EXPECTED_SPEED_TOO_LOW_DELTA_VS_M3105 = 8

POLICY_ID = "m3133_corridor_reflex_regression_failure_decomposition"
M3132_ROUTE_MARKER = "accept_m3131_artifacts_reject_behavior_regression_route_to_m3133_regression_failure_decomposition"
CLAIM_SCOPE = (
    "M3133 Active Safety Driver residual trajectory-level clearance/stability corridor "
    "reflex regression failure decomposition materialization only; existing M3131 "
    "measurement rows, M3131 same-row comparison rows against M3105, M3105 measurement "
    "rows, and M3132 audit text may be transformed into row-preserving regression "
    "decomposition, axis summary, claim, gate, doc, and M3134 audit artifacts. No reset, "
    "step, rollout, replay, fitting, PPO, training, repair materialization, validation, "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, driver-"
    "performance verdict, current-sim verdict, repair success, robustness-result, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full ideal "
    "driver completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "new execution, repair materialization, validation result, driver-performance verdict, "
    "current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint "
    "ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or "
    "result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, "
    "or level3 self-identification"
)

REGRESSION_FIELDNAMES = [
    "decomposition_id",
    "measurement_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "m3131_success",
    "m3131_collision",
    "m3131_offtrack",
    "m3131_speed_too_low",
    "m3131_termination_reason",
    "m3131_outcome_bucket",
    "m3131_min_clearance_margin",
    "m3131_return",
    "m3131_speed_mean",
    "m3131_high_sideslip_fraction",
    "m3131_lateral_rmse",
    "m3131_action_rate_mean",
    "m3131_raw_action_abs_max",
    "m3131_final_action_abs_max",
    "m3105_measurement_episode_id",
    "m3105_success",
    "m3105_collision",
    "m3105_offtrack",
    "m3105_speed_too_low",
    "m3105_termination_reason",
    "m3105_outcome_bucket",
    "m3105_min_clearance_margin",
    "m3105_return",
    "m3105_speed_mean",
    "m3105_high_sideslip_fraction",
    "m3105_lateral_rmse",
    "m3105_action_rate_mean",
    "success_delta",
    "collision_delta",
    "offtrack_delta",
    "speed_too_low_delta",
    "clearance_margin_delta",
    "return_delta",
    "speed_mean_delta",
    "high_sideslip_fraction_delta",
    "lateral_rmse_delta",
    "action_rate_delta",
    "exact_seed_match_m3105",
    "same_row_m3105_alignment_preserved",
    "success_regression",
    "success_improvement",
    "added_collision",
    "added_offtrack",
    "added_speed_too_low",
    "clearance_margin_regression",
    "return_regression",
    "stability_regression",
    "primary_regression_axis",
    "recommended_next_guard",
    "row_identity_preserved",
    "m3133_no_new_execution",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
AXIS_SUMMARY_FIELDNAMES = [
    "axis_summary_id",
    "group_key",
    "group_value",
    "row_count",
    "m3131_success_count",
    "m3105_success_count",
    "success_regression_count",
    "success_improvement_count",
    "added_collision_count",
    "added_offtrack_count",
    "added_speed_too_low_count",
    "clearance_margin_regression_count",
    "return_regression_count",
    "stability_regression_count",
    "clearance_margin_delta_mean",
    "return_delta_mean",
    "speed_mean_delta_mean",
    "high_sideslip_fraction_delta_mean",
    "lateral_rmse_delta_mean",
    "action_rate_delta_mean",
    "dominant_primary_regression_axis",
    "recommended_next_guards",
    "measurement_episode_ids",
    "m3133_no_new_execution",
    "repair_success_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3133",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _mean(rows: Iterable[Mapping[str, Any]], key: str) -> float | str:
    values = [_float(row.get(key)) for row in rows if str(row.get(key, "")).strip() != ""]
    return sum(values) / len(values) if values else ""


def _dominant(values: Iterable[str]) -> str:
    counter = Counter(str(value) if str(value) else "<blank>" for value in values)
    if not counter:
        return ""
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success"))


def _collision(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("collision"))


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _speed_too_low(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "speed_too_low"


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "regression_failure_decomposition_rows": output_dir / "regression_failure_decomposition_rows.csv",
        "regression_axis_summary_rows": output_dir / "regression_axis_summary_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3132_audit: Path, m3131_dir: Path, m3105_dir: Path) -> dict[str, Any]:
    paths = {
        "m3132_audit": m3132_audit,
        "m3131_summary": m3131_dir / "summary.json",
        "m3131_measurement_rows": m3131_dir / "measurement_episode_rows.csv",
        "m3131_comparison_rows": m3131_dir / "same_row_comparison_rows.csv",
        "m3131_claim_boundary_rows": m3131_dir / "claim_boundary_rows.csv",
        "m3131_gate_rows": m3131_dir / "gate_matrix.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_measurement_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3105_gate_rows": m3105_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3132_audit_text": paths["m3132_audit"].read_text(encoding="utf-8") if exists["m3132_audit"] else "",
        "m3131_summary": read_json(paths["m3131_summary"]) if exists["m3131_summary"] else {},
        "m3131_measurement_rows": read_csv_rows(paths["m3131_measurement_rows"]),
        "m3131_comparison_rows": read_csv_rows(paths["m3131_comparison_rows"]),
        "m3131_claim_boundary_rows": read_csv_rows(paths["m3131_claim_boundary_rows"]),
        "m3131_gate_rows": read_csv_rows(paths["m3131_gate_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_measurement_rows": read_csv_rows(paths["m3105_measurement_rows"]),
        "m3105_gate_rows": read_csv_rows(paths["m3105_gate_rows"]),
    }


def _rows_by_source(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        source_id = str(row.get("source_measurement_episode_id", ""))
        if source_id:
            output[source_id] = row
    return output


def _m3105_comparisons_by_source(comparison_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in comparison_rows:
        if str(row.get("baseline_id", "")) != EXPECTED_BASELINE_ID:
            continue
        source_id = str(row.get("source_measurement_episode_id", ""))
        if source_id:
            output[source_id] = row
    return output


def _primary_regression_axis(
    *,
    added_offtrack: bool,
    added_speed_too_low: bool,
    added_collision: bool,
    clearance_margin_regression: bool,
    return_regression: bool,
    stability_regression: bool,
    success_regression: bool,
) -> str:
    if added_offtrack:
        return "added_offtrack_regression"
    if added_speed_too_low:
        return "added_speed_floor_regression"
    if added_collision:
        return "added_collision_regression"
    if clearance_margin_regression:
        return "clearance_margin_loss"
    if stability_regression:
        return "stability_recovery_loss"
    if return_regression or success_regression:
        return "return_or_success_loss"
    return "no_regression_or_baseline_also_failed"


def _recommended_next_guard(axis: str) -> str:
    if axis == "added_offtrack_regression" or axis == "stability_recovery_loss":
        return "edge_stability_guarded_fallback_or_hybrid_before_standalone_corridor"
    if axis == "added_speed_floor_regression":
        return "speed_floor_guarded_fallback_or_hybrid_before_corridor_authority"
    if axis == "added_collision_regression":
        return "clearance_trigger_and_collision_guard_audit_before_repair"
    if axis == "clearance_margin_loss":
        return "clearance_margin_threshold_guard_before_action_authority_change"
    if axis == "return_or_success_loss":
        return "guarded_hybrid_or_fallback_not_standalone_corridor"
    return "preserve_row_for_separate_residual_or_baseline_failure_audit"


def regression_failure_decomposition_rows(
    m3131_rows: list[dict[str, str]],
    m3105_rows: list[dict[str, str]],
    comparison_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    m3105_by_source = _rows_by_source(m3105_rows)
    comparison_by_source = _m3105_comparisons_by_source(comparison_rows)
    output: list[dict[str, Any]] = []
    for index, episode in enumerate(m3131_rows, start=1):
        source_id = str(episode.get("source_measurement_episode_id", ""))
        baseline = m3105_by_source.get(source_id, {})
        comparison = comparison_by_source.get(source_id, {})

        m3131_success = _success(episode)
        m3105_success = _success(baseline)
        m3131_collision = _collision(episode)
        m3105_collision = _collision(baseline)
        m3131_offtrack = _offtrack(episode)
        m3105_offtrack = _offtrack(baseline)
        m3131_speed_too_low = _speed_too_low(episode)
        m3105_speed_too_low = _speed_too_low(baseline)

        success_delta = _int(comparison.get("success_delta"), int(m3131_success) - int(m3105_success))
        collision_delta = _int(comparison.get("collision_delta"), int(m3131_collision) - int(m3105_collision))
        offtrack_delta = _int(comparison.get("offtrack_delta"), int(m3131_offtrack) - int(m3105_offtrack))
        speed_too_low_delta = _int(
            comparison.get("speed_too_low_delta"),
            int(m3131_speed_too_low) - int(m3105_speed_too_low),
        )
        clearance_margin_delta = _float(
            comparison.get("clearance_margin_delta"),
            _float(episode.get("min_clearance_margin")) - _float(baseline.get("min_clearance_margin")),
        )
        return_delta = _float(
            comparison.get("return_delta"),
            _float(episode.get("return")) - _float(baseline.get("return")),
        )
        speed_mean_delta = _float(
            comparison.get("speed_mean_delta"),
            _float(episode.get("speed_mean")) - _float(baseline.get("speed_mean")),
        )
        high_sideslip_delta = _float(episode.get("high_sideslip_fraction")) - _float(
            baseline.get("high_sideslip_fraction")
        )
        lateral_rmse_delta = _float(episode.get("lateral_rmse")) - _float(baseline.get("lateral_rmse"))
        action_rate_delta = _float(
            comparison.get("action_rate_delta"),
            _float(episode.get("action_rate_mean")) - _float(baseline.get("action_rate_mean")),
        )

        success_regression = m3105_success and not m3131_success
        success_improvement = m3131_success and not m3105_success
        added_collision = m3131_collision and not m3105_collision
        added_offtrack = m3131_offtrack and not m3105_offtrack
        added_speed_too_low = m3131_speed_too_low and not m3105_speed_too_low
        clearance_margin_regression = clearance_margin_delta < -1.0
        return_regression = return_delta < 0.0
        stability_regression = high_sideslip_delta > 0.05 or lateral_rmse_delta > 0.25 or added_offtrack
        primary_axis = _primary_regression_axis(
            added_offtrack=added_offtrack,
            added_speed_too_low=added_speed_too_low,
            added_collision=added_collision,
            clearance_margin_regression=clearance_margin_regression,
            return_regression=return_regression,
            stability_regression=stability_regression,
            success_regression=success_regression,
        )
        row_identity_preserved = bool(source_id and source_id in m3105_by_source and source_id in comparison_by_source)
        exact_seed_match = _bool(comparison.get("exact_seed_match_m3105")) or (
            str(episode.get("eval_seed", "")) != "" and str(episode.get("eval_seed", "")) == str(baseline.get("eval_seed", ""))
        )

        output.append(
            {
                "decomposition_id": f"m3133-regression-decomposition-{index:04d}",
                "measurement_episode_id": episode.get("runtime_smoke_episode_id", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": episode.get("fresh_panel_row_id", ""),
                "axis_id": episode.get("axis_id", ""),
                "binding_role": episode.get("binding_role", ""),
                "task_family": episode.get("task_family", ""),
                "eval_seed": episode.get("eval_seed", ""),
                "m3131_success": m3131_success,
                "m3131_collision": m3131_collision,
                "m3131_offtrack": m3131_offtrack,
                "m3131_speed_too_low": m3131_speed_too_low,
                "m3131_termination_reason": episode.get("termination_reason", ""),
                "m3131_outcome_bucket": episode.get("outcome_bucket", ""),
                "m3131_min_clearance_margin": episode.get("min_clearance_margin", ""),
                "m3131_return": episode.get("return", ""),
                "m3131_speed_mean": episode.get("speed_mean", ""),
                "m3131_high_sideslip_fraction": episode.get("high_sideslip_fraction", ""),
                "m3131_lateral_rmse": episode.get("lateral_rmse", ""),
                "m3131_action_rate_mean": episode.get("action_rate_mean", ""),
                "m3131_raw_action_abs_max": episode.get("raw_action_abs_max", ""),
                "m3131_final_action_abs_max": episode.get("final_action_abs_max", ""),
                "m3105_measurement_episode_id": baseline.get("runtime_smoke_episode_id", comparison.get("baseline_episode_id", "")),
                "m3105_success": m3105_success,
                "m3105_collision": m3105_collision,
                "m3105_offtrack": m3105_offtrack,
                "m3105_speed_too_low": m3105_speed_too_low,
                "m3105_termination_reason": baseline.get("termination_reason", ""),
                "m3105_outcome_bucket": baseline.get("outcome_bucket", ""),
                "m3105_min_clearance_margin": baseline.get("min_clearance_margin", ""),
                "m3105_return": baseline.get("return", ""),
                "m3105_speed_mean": baseline.get("speed_mean", ""),
                "m3105_high_sideslip_fraction": baseline.get("high_sideslip_fraction", ""),
                "m3105_lateral_rmse": baseline.get("lateral_rmse", ""),
                "m3105_action_rate_mean": baseline.get("action_rate_mean", ""),
                "success_delta": success_delta,
                "collision_delta": collision_delta,
                "offtrack_delta": offtrack_delta,
                "speed_too_low_delta": speed_too_low_delta,
                "clearance_margin_delta": clearance_margin_delta,
                "return_delta": return_delta,
                "speed_mean_delta": speed_mean_delta,
                "high_sideslip_fraction_delta": high_sideslip_delta,
                "lateral_rmse_delta": lateral_rmse_delta,
                "action_rate_delta": action_rate_delta,
                "exact_seed_match_m3105": exact_seed_match,
                "same_row_m3105_alignment_preserved": row_identity_preserved and exact_seed_match,
                "success_regression": success_regression,
                "success_improvement": success_improvement,
                "added_collision": added_collision,
                "added_offtrack": added_offtrack,
                "added_speed_too_low": added_speed_too_low,
                "clearance_margin_regression": clearance_margin_regression,
                "return_regression": return_regression,
                "stability_regression": stability_regression,
                "primary_regression_axis": primary_axis,
                "recommended_next_guard": _recommended_next_guard(primary_axis),
                "row_identity_preserved": row_identity_preserved,
                "m3133_no_new_execution": True,
                "runtime_base_policy_required": False,
                "hidden_oracle_actor_input_required": False,
                "repair_success_claim_made": False,
                "validation_run": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def _axis_groups(rows: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    groups: list[tuple[str, str, list[dict[str, Any]]]] = [("all", "all", rows)]
    for key in ("primary_regression_axis", "axis_id", "binding_role", "task_family", "m3131_termination_reason"):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(key, ""))].append(row)
        for value in sorted(grouped):
            groups.append((key, value if value else "<blank>", grouped[value]))
    return groups


def regression_axis_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, (group_key, group_value, grouped) in enumerate(_axis_groups(rows), start=1):
        guard_values = sorted({str(row.get("recommended_next_guard", "")) for row in grouped if row.get("recommended_next_guard")})
        output.append(
            {
                "axis_summary_id": f"m3133-axis-summary-{index:04d}",
                "group_key": group_key,
                "group_value": group_value,
                "row_count": len(grouped),
                "m3131_success_count": sum(1 for row in grouped if _bool(row.get("m3131_success"))),
                "m3105_success_count": sum(1 for row in grouped if _bool(row.get("m3105_success"))),
                "success_regression_count": sum(1 for row in grouped if _bool(row.get("success_regression"))),
                "success_improvement_count": sum(1 for row in grouped if _bool(row.get("success_improvement"))),
                "added_collision_count": sum(1 for row in grouped if _bool(row.get("added_collision"))),
                "added_offtrack_count": sum(1 for row in grouped if _bool(row.get("added_offtrack"))),
                "added_speed_too_low_count": sum(1 for row in grouped if _bool(row.get("added_speed_too_low"))),
                "clearance_margin_regression_count": sum(1 for row in grouped if _bool(row.get("clearance_margin_regression"))),
                "return_regression_count": sum(1 for row in grouped if _bool(row.get("return_regression"))),
                "stability_regression_count": sum(1 for row in grouped if _bool(row.get("stability_regression"))),
                "clearance_margin_delta_mean": _mean(grouped, "clearance_margin_delta"),
                "return_delta_mean": _mean(grouped, "return_delta"),
                "speed_mean_delta_mean": _mean(grouped, "speed_mean_delta"),
                "high_sideslip_fraction_delta_mean": _mean(grouped, "high_sideslip_fraction_delta"),
                "lateral_rmse_delta_mean": _mean(grouped, "lateral_rmse_delta"),
                "action_rate_delta_mean": _mean(grouped, "action_rate_delta"),
                "dominant_primary_regression_axis": _dominant(str(row.get("primary_regression_axis", "")) for row in grouped),
                "recommended_next_guards": ";".join(guard_values),
                "measurement_episode_ids": ";".join(str(row.get("measurement_episode_id", "")) for row in grouped),
                "m3133_no_new_execution": True,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("regression_failure_decomposition_rows", "materialization", True, "regression_failure_decomposition_rows.csv"),
        ("regression_axis_summary_rows", "materialization", True, "regression_axis_summary_rows.csv"),
        ("same_row_m3105_alignment_audit", "comparison", True, "M3131 same-row comparison rows against M3105"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3134 audit manifest"),
    ]
    blocked = [
        ("new_execution", "execution", "future separately registered measurement route"),
        ("repair_materialization", "repair", "future separately registered repair route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future result audit after measurement"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("feasibility_proof", "proof", "future feasibility proof route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "direct-action driver forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3133-{claim_id}",
            "claim_family": family,
            "allowed_in_m3133": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3133-{claim_id}",
            "claim_family": family,
            "allowed_in_m3133": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31340,
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
        "hypothesis": (
            "A bounded result audit can accept or reject the M3133 corridor-reflex regression "
            "failure decomposition artifacts before any new repair materialization validation "
            "ranking promotion driver-performance current-sim high-fidelity full-driver "
            "repair-success robustness-result feasibility-proof or self-ID claim."
        ),
        "lineage": {
            "parent_checkpoint": [str(doc_path), f"docs/{M3132_ID}.md"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "regression_failure_decomposition_rows.csv"),
                str(output_dir / "regression_axis_summary_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3133 regression decomposition before selecting a guarded fallback or hybrid route"],
            "derived_from": [MILESTONE_ID, M3132_ID, M3131_ID, M3105_ID],
            "blocked_by": [
                "M3133 decomposition artifacts require audit before repair materialization or measurement",
                "M3133 is no-new-execution evidence reanalysis and cannot support repair-success claims",
            ],
            "supersedes": ["blind continuation from M3131 behavior-negative corridor reflex measurement to another gain edit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3134 must audit M3133 summary decomposition axis claim and gate artifacts",
            "M3134 must preserve M3131/M3105 row identity and same-row alignment",
            "M3134 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3134 must select exactly one guarded fallback hybridization synthesis artifact repair or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune expand rank promote validate or mutate checkpoints",
            "do not convert M3133 decomposition into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_trajectory_level_controller_architecture_diagnosis",
            "evidence_axis": "corridor_reflex_regression_failure_decomposition_result_audit",
            "evidence_increment": "audits behavior-negative regression decomposition artifacts before selecting a guarded next route",
            "claim_scope": (
                "Result audit only; no validation ranking promotion performance current-sim verdict "
                "high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim"
            ),
            "stop_condition": [
                "stop if M3133 artifacts are missing or gate matrix fails",
                "stop if row identity or same-row M3105 alignment is not preserved",
                "route to synthesis or guarded fallback before any next repair interpretation",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete or contract-unsafe",
                "route to guarded fallback or hybridization if standalone corridor reflex regression is accepted",
                "route to stop if no actor-contract-preserving next route remains",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3133 completes regression failure decomposition materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3133 corridor-reflex regression decomposition artifacts",
            "admission_evidence": ["M3133 summary gate matrix decomposition axis and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3134 status queue scoreboard research log and review",
                "one follow-up manifest only if M3134 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3134 accepts or rejects M3133 as complete and claim-safe",
                "next guarded fallback hybridization synthesis artifact repair or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3134 audits engineering regression decomposition artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3134; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3133 regression decomposition artifacts only.",
            "negative_result_policy": "Preserve behavior-negative evidence and route engineering decisions rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3133 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the M3133 regression decomposition evidence before guarded repair routing",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3134 prepares engineering guarded-route decision",
            "must_synthesize_if": [
                "M3134 cannot accept M3133 as complete and claim-safe",
                "M3134 would claim validation driver-performance paper high-fidelity current-sim verdict repair-success robustness-result feasibility-proof or self-ID evidence",
                "M3134 cannot select exactly one next route or stop state",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3134 audits M3133 artifact row counts gates actor contract and claim boundaries",
            "M3134 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3134 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3134 hides M3133 failures or missing artifacts",
            "M3134 treats M3133 decomposition as validation repair-success or performance verdict",
            "M3134 changes actor input or action contract",
            "M3134 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3134 audits M3133 artifacts and selects one next route while preserving actor and claim boundaries.",
        "commands": [
            {
                "name": "active_safety_driver_residual_hard_safety_corridor_reflex_regression_decomposition_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3133-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def _delta_sum(rows: list[dict[str, Any]], key: str) -> int:
    return sum(_int(row.get(key)) for row in rows)


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    regression_rows: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    summary = source["m3131_summary"]
    m3105_summary = source["m3105_summary"]
    audit_text = str(source.get("m3132_audit_text", ""))
    m3105_comparison_count = sum(
        1 for row in source["m3131_comparison_rows"] if str(row.get("baseline_id", "")) == EXPECTED_BASELINE_ID
    )
    exact_seed_count = sum(1 for row in regression_rows if _bool(row.get("exact_seed_match_m3105")))
    success_regressions = sum(1 for row in regression_rows if _bool(row.get("success_regression")))
    success_improvements = sum(1 for row in regression_rows if _bool(row.get("success_improvement")))
    added_collision = sum(1 for row in regression_rows if _bool(row.get("added_collision")))
    removed_collision = sum(1 for row in regression_rows if _int(row.get("collision_delta")) < 0)
    added_offtrack = sum(1 for row in regression_rows if _bool(row.get("added_offtrack")))
    removed_offtrack = sum(1 for row in regression_rows if _int(row.get("offtrack_delta")) < 0)
    added_speed = sum(1 for row in regression_rows if _bool(row.get("added_speed_too_low")))
    removed_speed = sum(1 for row in regression_rows if _int(row.get("speed_too_low_delta")) < 0)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3132_route_marker", "lineage", M3132_ROUTE_MARKER in audit_text, "route marker", "present", "lineage_invalid"),
        gate("m3131_status_pass", "lineage", _bool(summary.get("status_pass")), summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3131_gate_matrix_pass", "lineage", _bool(summary.get("gate_matrix_pass")), summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(m3105_summary.get("status_pass")), m3105_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3105_gate_matrix_pass", "lineage", _bool(m3105_summary.get("gate_matrix_pass")), m3105_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3131_full_denominator", "denominator", len(source["m3131_measurement_rows"]) == EXPECTED_FULL_ROWS, len(source["m3131_measurement_rows"]), EXPECTED_FULL_ROWS, "scenario_sampling_failure"),
        gate("m3105_full_denominator", "denominator", len(source["m3105_measurement_rows"]) == EXPECTED_FULL_ROWS, len(source["m3105_measurement_rows"]), EXPECTED_FULL_ROWS, "scenario_sampling_failure"),
        gate("m3131_no_execution_failures", "execution", _int(summary.get("measurement_failure_row_count")) == 0, summary.get("measurement_failure_row_count"), 0, "metric_artifact"),
        gate("m3105_comparison_rows", "comparison", m3105_comparison_count == EXPECTED_FULL_ROWS, m3105_comparison_count, EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("m3105_exact_seed_matches", "comparison", exact_seed_count == EXPECTED_FULL_ROWS, exact_seed_count, EXPECTED_FULL_ROWS, "seed_fragility"),
        gate("row_identity_preserved", "comparison", all(_bool(row.get("row_identity_preserved")) for row in regression_rows), "all", "preserved", "metric_artifact"),
        gate("same_row_m3105_alignment_preserved", "comparison", all(_bool(row.get("same_row_m3105_alignment_preserved")) for row in regression_rows), "all", "preserved", "metric_artifact"),
        gate("regression_decomposition_rows", "metric", len(regression_rows) == EXPECTED_FULL_ROWS, len(regression_rows), EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("axis_summary_rows", "metric", len(axis_rows) > 0, len(axis_rows), ">0", "metric_artifact"),
        gate("success_delta_sum_vs_m3105", "metric", _delta_sum(regression_rows, "success_delta") == EXPECTED_SUCCESS_DELTA_VS_M3105, _delta_sum(regression_rows, "success_delta"), EXPECTED_SUCCESS_DELTA_VS_M3105, "behavior_regression"),
        gate("collision_delta_sum_vs_m3105", "metric", _delta_sum(regression_rows, "collision_delta") == EXPECTED_COLLISION_DELTA_VS_M3105, _delta_sum(regression_rows, "collision_delta"), EXPECTED_COLLISION_DELTA_VS_M3105, "behavior_regression"),
        gate("offtrack_delta_sum_vs_m3105", "metric", _delta_sum(regression_rows, "offtrack_delta") == EXPECTED_OFFTRACK_DELTA_VS_M3105, _delta_sum(regression_rows, "offtrack_delta"), EXPECTED_OFFTRACK_DELTA_VS_M3105, "behavior_regression"),
        gate("speed_too_low_delta_sum_vs_m3105", "metric", _delta_sum(regression_rows, "speed_too_low_delta") == EXPECTED_SPEED_TOO_LOW_DELTA_VS_M3105, _delta_sum(regression_rows, "speed_too_low_delta"), EXPECTED_SPEED_TOO_LOW_DELTA_VS_M3105, "behavior_regression"),
        gate("success_regression_net_matches_delta", "metric", success_regressions - success_improvements == abs(EXPECTED_SUCCESS_DELTA_VS_M3105), {"regressions": success_regressions, "improvements": success_improvements}, "net 22 regressions", "metric_artifact"),
        gate("added_collision_net_matches_delta", "metric", added_collision - removed_collision == EXPECTED_COLLISION_DELTA_VS_M3105, {"added": added_collision, "removed": removed_collision}, "net +2", "metric_artifact"),
        gate("added_offtrack_net_matches_delta", "metric", added_offtrack - removed_offtrack == EXPECTED_OFFTRACK_DELTA_VS_M3105, {"added": added_offtrack, "removed": removed_offtrack}, "net +12", "metric_artifact"),
        gate("added_speed_too_low_net_matches_delta", "metric", added_speed - removed_speed == EXPECTED_SPEED_TOO_LOW_DELTA_VS_M3105, {"added": added_speed, "removed": removed_speed}, "net +8", "metric_artifact"),
        gate("clearance_regression_classified", "metric", any(_bool(row.get("clearance_margin_regression")) for row in regression_rows), ">=1", "classified", "metric_artifact"),
        gate("return_regression_classified", "metric", any(_bool(row.get("return_regression")) for row in regression_rows), ">=1", "classified", "metric_artifact"),
        gate("stability_regression_classified", "metric", any(_bool(row.get("stability_regression")) for row in regression_rows), ">=1", "classified", "metric_artifact"),
        gate("source_claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in source["m3131_claim_boundary_rows"]), "all", "pass", "contract_violation"),
        gate("claim_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(summary.get("runtime_base_policy_required")), summary.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("no_new_execution", "execution", True, "no reset step rollout replay fitting training validation repair", "preserved", "contract_violation"),
        gate("required_artifacts_present", "process", present, present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3133 Corridor Reflex Regression Failure Decomposition Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- source full-fresh rows: {summary['source_measurement_row_count']}",
            f"- decomposition rows: {summary['regression_decomposition_row_count']}",
            f"- exact M3105 same-row matches: {summary['same_row_exact_seed_match_count_m3105']}",
            f"- success delta vs M3105: {summary['success_delta_sum_vs_m3105']}",
            f"- collision delta vs M3105: {summary['collision_delta_sum_vs_m3105']}",
            f"- offtrack delta vs M3105: {summary['offtrack_delta_sum_vs_m3105']}",
            f"- speed-too-low delta vs M3105: {summary['speed_too_low_delta_sum_vs_m3105']}",
            f"- primary axis counts: {summary['primary_regression_axis_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3133 materializes a no-new-execution decomposition of the M3131 standalone corridor-reflex regression against M3105. It preserves the M3131 row identity and M3105 same-row alignment, and it does not run a reset, step, rollout, replay, fitting, PPO, training, repair materialization, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, feasibility proof, or self-ID test.",
            "",
            "Regression routing pressure:",
            "",
            "```text",
            f"success regressions: {summary['success_regression_count']}",
            f"success improvements: {summary['success_improvement_count']}",
            f"added collision rows: {summary['added_collision_count']}",
            f"added offtrack rows: {summary['added_offtrack_count']}",
            f"added speed-too-low rows: {summary['added_speed_too_low_count']}",
            f"clearance-margin regressions: {summary['clearance_margin_regression_count']}",
            f"return regressions: {summary['return_regression_count']}",
            f"stability regressions: {summary['stability_regression_count']}",
            "```",
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


def run_materialization(
    *,
    m3132_audit: Path,
    m3131_dir: Path,
    m3105_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3132_audit=m3132_audit, m3131_dir=m3131_dir, m3105_dir=m3105_dir)
    regression_rows = regression_failure_decomposition_rows(
        source["m3131_measurement_rows"],
        source["m3105_measurement_rows"],
        source["m3131_comparison_rows"],
    )
    axis_rows = regression_axis_summary_rows(regression_rows)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["regression_failure_decomposition_rows"], regression_rows, REGRESSION_FIELDNAMES),
        (paths["regression_axis_summary_rows"], axis_rows, AXIS_SUMMARY_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        regression_rows=regression_rows,
        axis_rows=axis_rows,
        claim_rows=claim_rows,
        present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    axis_counts = Counter(str(row.get("primary_regression_axis", "")) for row in regression_rows)
    next_guard_counts = Counter(str(row.get("recommended_next_guard", "")) for row in regression_rows)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_corridor_reflex_regression_failure_decomposition_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_corridor_reflex_regression_failure_decomposition_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_measurement_row_count": len(source["m3131_measurement_rows"]),
        "source_same_row_comparison_row_count": len(source["m3131_comparison_rows"]),
        "m3105_measurement_row_count": len(source["m3105_measurement_rows"]),
        "m3105_same_row_comparison_row_count": sum(
            1 for row in source["m3131_comparison_rows"] if str(row.get("baseline_id", "")) == EXPECTED_BASELINE_ID
        ),
        "same_row_exact_seed_match_count_m3105": sum(
            1 for row in regression_rows if _bool(row.get("exact_seed_match_m3105"))
        ),
        "row_identity_preserved": all(_bool(row.get("row_identity_preserved")) for row in regression_rows),
        "same_row_m3105_alignment_preserved": all(
            _bool(row.get("same_row_m3105_alignment_preserved")) for row in regression_rows
        ),
        "regression_decomposition_row_count": len(regression_rows),
        "regression_axis_summary_row_count": len(axis_rows),
        "success_delta_sum_vs_m3105": _delta_sum(regression_rows, "success_delta"),
        "collision_delta_sum_vs_m3105": _delta_sum(regression_rows, "collision_delta"),
        "offtrack_delta_sum_vs_m3105": _delta_sum(regression_rows, "offtrack_delta"),
        "speed_too_low_delta_sum_vs_m3105": _delta_sum(regression_rows, "speed_too_low_delta"),
        "success_regression_count": sum(1 for row in regression_rows if _bool(row.get("success_regression"))),
        "success_improvement_count": sum(1 for row in regression_rows if _bool(row.get("success_improvement"))),
        "added_collision_count": sum(1 for row in regression_rows if _bool(row.get("added_collision"))),
        "removed_collision_count": sum(1 for row in regression_rows if _int(row.get("collision_delta")) < 0),
        "added_offtrack_count": sum(1 for row in regression_rows if _bool(row.get("added_offtrack"))),
        "removed_offtrack_count": sum(1 for row in regression_rows if _int(row.get("offtrack_delta")) < 0),
        "added_speed_too_low_count": sum(1 for row in regression_rows if _bool(row.get("added_speed_too_low"))),
        "removed_speed_too_low_count": sum(1 for row in regression_rows if _int(row.get("speed_too_low_delta")) < 0),
        "clearance_margin_regression_count": sum(
            1 for row in regression_rows if _bool(row.get("clearance_margin_regression"))
        ),
        "return_regression_count": sum(1 for row in regression_rows if _bool(row.get("return_regression"))),
        "stability_regression_count": sum(1 for row in regression_rows if _bool(row.get("stability_regression"))),
        "clearance_margin_delta_mean_vs_m3105": _mean(regression_rows, "clearance_margin_delta"),
        "return_delta_mean_vs_m3105": _mean(regression_rows, "return_delta"),
        "speed_mean_delta_mean_vs_m3105": _mean(regression_rows, "speed_mean_delta"),
        "high_sideslip_fraction_delta_mean_vs_m3105": _mean(regression_rows, "high_sideslip_fraction_delta"),
        "lateral_rmse_delta_mean_vs_m3105": _mean(regression_rows, "lateral_rmse_delta"),
        "action_rate_delta_mean_vs_m3105": _mean(regression_rows, "action_rate_delta"),
        "primary_regression_axis_counts": dict(sorted(axis_counts.items())),
        "recommended_next_guard_counts": dict(sorted(next_guard_counts.items())),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "runtime_driver_id": POLICY_ID,
        "candidate_output_semantics": "direct_action_clipped",
        "candidate_output_components": ["steer", "throttle", "brake"],
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_hard_safety_corridor_reflex_regression_decomposition_route_to_m3134_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(paths["run_state"], {"complete": status_pass, "status_pass": status_pass, "next_blocker": NEXT_ID})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3132-audit", type=Path, default=DEFAULT_M3132_AUDIT)
    parser.add_argument("--m3131-dir", type=Path, default=DEFAULT_M3131_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3132_audit=args.m3132_audit,
        m3131_dir=args.m3131_dir,
        m3105_dir=args.m3105_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"regression_decomposition_rows={summary['regression_decomposition_row_count']}")
    print(f"success_delta_vs_m3105={summary['success_delta_sum_vs_m3105']}")
    print(f"collision_delta_vs_m3105={summary['collision_delta_sum_vs_m3105']}")
    print(f"offtrack_delta_vs_m3105={summary['offtrack_delta_sum_vs_m3105']}")
    print(f"speed_too_low_delta_vs_m3105={summary['speed_too_low_delta_sum_vs_m3105']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
