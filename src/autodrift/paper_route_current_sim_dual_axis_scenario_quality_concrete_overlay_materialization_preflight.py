"""Materialize M2460 concrete overlays and rerun adapter preflight."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter import (
    ALLOWED_OVERLAY_KEYS,
    DEFAULT_CLAIM_BOUNDARY,
    DEFAULT_CANDIDATE_ROWS,
    DEFAULT_GEOMETRY_LEVER_ROWS,
    DEFAULT_GUARDRAIL_ROWS,
    DEFAULT_M2455_SUMMARY,
    DEFAULT_ROLE_PROTOCOL_ROWS,
    read_csv_rows,
    run_reset_static_preflight_adapter,
)


DEFAULT_M2458_DIR = Path(
    "runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter"
)
DEFAULT_M2458_PREFLIGHT_WORK_ITEMS = DEFAULT_M2458_DIR / "preflight_work_items.csv"
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2462-paper-route-current-sim-dual-axis-scenario-quality-discriminant-branch-synthesis"
)

RESULT_PASS = "scenario_quality_concrete_overlay_materialization_preflight_pass"
RESULT_FAIL = "scenario_quality_concrete_overlay_materialization_preflight_fail"

TARGET_GROUPS = {"stable_feasibility_support", "stable_aes_support"}

CONCRETE_OVERLAY_FIELDNAMES = [
    "overlay_id",
    "preflight_id",
    "source_candidate_id",
    "candidate_group",
    "overlay_family",
    "env_config_overlay_json",
    "allowed_overlay_keys",
    "allowed_labels_metadata_only",
    "labels_enter_actor_input",
    "actor_input_contract_changed",
    "scenario_redesign_executed",
    "policy_action_executed",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]

GUARDRAIL_FIELDNAMES = [
    "guardrail_id",
    "guardrail_class",
    "source_role_or_axis",
    "failure_mode_to_preserve",
    "metric_to_watch",
    "value",
    "violation",
    "reason",
]

CLAIM_FIELDNAMES = [
    "claim_key",
    "claim_value",
    "admissible",
    "reason",
]

DECISION_FIELDNAMES = [
    "decision_key",
    "decision_value",
    "admissible",
    "reason",
]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _canonical_overlay_json(overlay: Mapping[str, Any]) -> str:
    return json.dumps(dict(overlay), sort_keys=True)


def _stable_avoidable_overlay() -> dict[str, Any]:
    return {
        "track_width": 7.5,
        "speed_range": [8.0, 12.0],
        "friction_limited_speed": False,
        "soft_offtrack_metric_enabled": True,
        "soft_offtrack_tolerance_m": 0.20,
        "obstacle": {
            "enabled": True,
            "distance_range": [34.0, 52.0],
            "lateral_offset_range": [-0.25, 0.25],
            "half_width_range": [0.45, 0.65],
            "allowed_labels": ["aeb_feasible"],
            "require_aeb_infeasible": False,
            "max_sample_attempts": 10000,
            "perception_reveal_step": 0,
            "perception_reveal_distance": 70.0,
            "finish_on_pass": True,
            "finish_pass_distance": 1.0,
        },
    }


def _stable_aes_overlay() -> dict[str, Any]:
    return {
        "track_width": 7.5,
        "speed_range": [10.0, 14.0],
        "friction_limited_speed": False,
        "soft_offtrack_metric_enabled": True,
        "soft_offtrack_tolerance_m": 0.20,
        "obstacle": {
            "enabled": True,
            "distance_range": [20.0, 34.0],
            "lateral_offset_range": [-0.40, 0.40],
            "half_width_range": [0.55, 0.80],
            "allowed_labels": ["aes_feasible"],
            "require_aeb_infeasible": True,
            "max_threshold_score": 0.35,
            "max_sample_attempts": 10000,
            "perception_reveal_step": 0,
            "perception_reveal_distance": 55.0,
            "finish_on_pass": True,
            "finish_pass_distance": 1.0,
        },
    }


def overlay_for_group(candidate_group: str) -> tuple[str, dict[str, Any]]:
    if candidate_group == "stable_feasibility_support":
        return "R0_stable_avoidable", _stable_avoidable_overlay()
    if candidate_group == "stable_aes_support":
        return "R1_aeb_infeasible_stable_aes", _stable_aes_overlay()
    raise ValueError(f"no M2460 concrete overlay family for {candidate_group!r}")


def _flatten_overlay_keys(data: Mapping[str, Any], prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in data.items():
        flat_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            keys.update(_flatten_overlay_keys(value, flat_key))
        else:
            keys.add(flat_key)
    return keys


def _target_preflight_rows(preflight_rows: Sequence[Mapping[str, str]]) -> list[Mapping[str, str]]:
    return [
        row
        for row in preflight_rows
        if str(row.get("candidate_group", "")) in TARGET_GROUPS
        and _bool(row.get("concrete_overlay_required"))
        and str(row.get("blocked_reason", "")) == "reset_blocked_missing_concrete_overlay"
    ]


def materialize_candidate_rows(
    *,
    candidate_rows: Sequence[Mapping[str, str]],
    preflight_rows: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    targets = _target_preflight_rows(preflight_rows)
    candidate_by_id = {str(row.get("candidate_id", "")): dict(row) for row in candidate_rows}
    overlay_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    overlay_by_candidate_id: dict[str, str] = {}

    for index, preflight in enumerate(targets, start=1):
        source_candidate_id = str(preflight.get("source_candidate_id", ""))
        candidate = candidate_by_id.get(source_candidate_id)
        if candidate is None:
            errors.append(f"missing source candidate row for {source_candidate_id}")
            continue
        group = str(preflight.get("candidate_group", ""))
        try:
            overlay_family, overlay = overlay_for_group(group)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        unknown_keys = sorted(_flatten_overlay_keys(overlay) - ALLOWED_OVERLAY_KEYS)
        if unknown_keys:
            errors.append(f"{source_candidate_id} unknown overlay keys: {'|'.join(unknown_keys)}")
            continue
        overlay_json = _canonical_overlay_json(overlay)
        overlay_by_candidate_id[source_candidate_id] = overlay_json
        overlay_rows.append(
            {
                "overlay_id": f"m2461_overlay_{index:03d}",
                "preflight_id": str(preflight.get("preflight_id", "")),
                "source_candidate_id": source_candidate_id,
                "candidate_group": group,
                "overlay_family": overlay_family,
                "env_config_overlay_json": overlay_json,
                "allowed_overlay_keys": "|".join(sorted(ALLOWED_OVERLAY_KEYS)),
                "allowed_labels_metadata_only": True,
                "labels_enter_actor_input": False,
                "actor_input_contract_changed": False,
                "scenario_redesign_executed": False,
                "policy_action_executed": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )

    augmented_candidates: list[dict[str, Any]] = []
    for row in candidate_rows:
        augmented = dict(row)
        candidate_id = str(row.get("candidate_id", ""))
        if candidate_id in overlay_by_candidate_id:
            augmented["env_config_overlay_json"] = overlay_by_candidate_id[candidate_id]
        else:
            augmented.setdefault("env_config_overlay_json", "")
        augmented_candidates.append(augmented)

    return overlay_rows, augmented_candidates, errors


def guardrail_rows(
    *,
    overlay_rows: Sequence[Mapping[str, Any]],
    target_preflight_count: int,
    adapter_summary: Mapping[str, Any],
    materialization_errors: Sequence[str],
) -> list[dict[str, Any]]:
    overlay_key_violation_count = 0
    for row in overlay_rows:
        overlay = json.loads(str(row.get("env_config_overlay_json", "{}")))
        overlay_key_violation_count += len(_flatten_overlay_keys(overlay) - ALLOWED_OVERLAY_KEYS)
    guards = [
        (
            "m2461_exact_six_overlay_targets",
            "overlay_materialization",
            "stable_aes_reset_blocked_work_items",
            "scenario_sampling_failure",
            "overlay_row_count",
            len(overlay_rows),
            len(overlay_rows) != 6 or target_preflight_count != 6,
            "Exactly six M2458 stable/AES reset-blocked work items must receive overlays.",
        ),
        (
            "m2461_overlay_keys_allowed",
            "overlay_schema",
            "concrete_overlay_rows",
            "contract_violation",
            "unknown_overlay_key_count",
            overlay_key_violation_count,
            overlay_key_violation_count != 0,
            "Concrete overlays may only use M2460 allowed overlay keys.",
        ),
        (
            "m2461_no_materialization_errors",
            "lineage",
            "candidate_rows",
            "lineage_invalid",
            "materialization_error_count",
            len(materialization_errors),
            len(materialization_errors) != 0,
            "Every target preflight row must map to a source candidate and overlay family.",
        ),
        (
            "m2461_adapter_static_checks_pass",
            "adapter_preflight",
            "adapter_static_check_rows",
            "contract_violation",
            "adapter_static_check_fail_count",
            adapter_summary.get("static_check_fail_count", ""),
            int(adapter_summary.get("static_check_fail_count", 999999)) != 0,
            "Overlay-augmented adapter preflight must preserve static checks.",
        ),
        (
            "m2461_adapter_sees_six_concrete_overlays",
            "adapter_preflight",
            "adapter_summary",
            "scenario_sampling_failure",
            "adapter_concrete_overlay_available_count",
            adapter_summary.get("concrete_overlay_available_count", ""),
            int(adapter_summary.get("concrete_overlay_available_count", -1)) != 6,
            "Adapter must classify all six reset-required stable/AES rows as having concrete overlays.",
        ),
        (
            "m2461_no_reset_execution",
            "claim_boundary",
            "adapter_reset_rows",
            "contract_violation",
            "adapter_reset_attempted_count",
            adapter_summary.get("reset_attempted_count", ""),
            int(adapter_summary.get("reset_attempted_count", 999999)) != 0,
            "M2461 materialization/preflight must not execute environment reset.",
        ),
        (
            "m2461_no_policy_action_or_rollout",
            "claim_boundary",
            "adapter_summary",
            "contract_violation",
            "policy_action_or_rollout_started",
            f"{adapter_summary.get('policy_action_executed')}|"
            f"{adapter_summary.get('environment_rollout_started')}|"
            f"{adapter_summary.get('measured_policy_rollout_started')}",
            bool(adapter_summary.get("policy_action_executed"))
            or bool(adapter_summary.get("environment_rollout_started"))
            or bool(adapter_summary.get("measured_policy_rollout_started")),
            "M2461 must remain preflight-only.",
        ),
        (
            "m2461_no_ranking_winner_or_verdict",
            "claim_boundary",
            "adapter_summary",
            "metric_artifact",
            "ranking_winner_or_verdict_claim",
            f"{adapter_summary.get('ranking_admissible_count')}|"
            f"{adapter_summary.get('winner_selected_count')}|"
            f"{adapter_summary.get('paper_level_claim_made')}|"
            f"{adapter_summary.get('current_sim_verdict_claim_made')}",
            int(adapter_summary.get("ranking_admissible_count", 0)) != 0
            or int(adapter_summary.get("winner_selected_count", 0)) != 0
            or bool(adapter_summary.get("paper_level_claim_made"))
            or bool(adapter_summary.get("current_sim_verdict_claim_made")),
            "No ranking, winner selection, paper verdict, or current-sim verdict is allowed.",
        ),
    ]
    return [
        {
            "guardrail_id": guardrail_id,
            "guardrail_class": guardrail_class,
            "source_role_or_axis": axis,
            "failure_mode_to_preserve": failure_mode,
            "metric_to_watch": metric,
            "value": value,
            "violation": violation,
            "reason": reason,
        }
        for guardrail_id, guardrail_class, axis, failure_mode, metric, value, violation, reason in guards
    ]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_key": "concrete_overlay_materialized",
            "claim_value": "true",
            "admissible": True,
            "reason": "M2461 materializes bounded env_config_overlay_json rows.",
        },
        {
            "claim_key": "reset_validation_started",
            "claim_value": "false",
            "admissible": True,
            "reason": "M2461 does not execute environment reset.",
        },
        {"claim_key": "measured_rollout_started", "claim_value": "false", "admissible": True, "reason": "No rollout is run."},
        {"claim_key": "policy_action_executed", "claim_value": "false", "admissible": True, "reason": "No policy action is executed."},
        {
            "claim_key": "scenario_redesign_executed",
            "claim_value": "false",
            "admissible": True,
            "reason": "Attaching predesigned overlays is materialization/preflight, not scenario redesign execution.",
        },
        {"claim_key": "repair_training_started", "claim_value": "false", "admissible": True, "reason": "No repair or training is executed."},
        {"claim_key": "ranking_or_winner", "claim_value": "false", "admissible": True, "reason": "No ranking or winner is selected."},
        {
            "claim_key": "actual_success_improvement",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "No measured rollout is produced.",
        },
        {
            "claim_key": "paper_or_self_id_verdict",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "No controller-family or history-necessity test is run.",
        },
        {
            "claim_key": "current_sim_verdict",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "This is not a final current-sim verdict.",
        },
    ]


def decision_rows(*, next_blocker: str, result_class: str) -> list[dict[str, Any]]:
    passed = result_class == RESULT_PASS
    return [
        {
            "decision_key": "overlay_materialization_complete",
            "decision_value": "true" if passed else "false",
            "admissible": passed,
            "reason": "Six stable/AES reset-blocked rows have concrete overlays." if passed else "Overlay materialization failed.",
        },
        {
            "decision_key": "reset_validation_started",
            "decision_value": "false",
            "admissible": True,
            "reason": "Reset validation remains blocked until a later audit admits it.",
        },
        {
            "decision_key": "repair_training_ranking_or_winner_selection",
            "decision_value": "false",
            "admissible": True,
            "reason": "No repair, training, ranking, or winner selection is executed.",
        },
        {
            "decision_key": "next_route",
            "decision_value": next_blocker if passed else "m2461_overlay_materialization_repair_or_stop",
            "admissible": True,
            "reason": "Route to result audit before reset validation." if passed else "Audit failure before further execution.",
        },
    ]


def _copy_adapter_artifacts(adapter_dir: Path, output_dir: Path) -> dict[str, str]:
    mapping = {
        "adapter_summary": "summary.json",
        "adapter_preflight_work_items": "preflight_work_items.csv",
        "adapter_static_check_rows": "static_check_rows.csv",
        "adapter_reset_check_rows": "reset_check_rows.csv",
        "adapter_overlay_requirement_rows": "overlay_requirement_rows.csv",
        "adapter_guardrail_rows": "guardrail_rows.csv",
        "adapter_claim_boundary": "claim_boundary.csv",
        "adapter_decision_rows": "decision_rows.csv",
    }
    copied: dict[str, str] = {}
    for artifact_key, filename in mapping.items():
        source = adapter_dir / filename
        suffix = ".json" if filename.endswith(".json") else ".csv"
        destination = output_dir / f"{artifact_key}{suffix}"
        shutil.copyfile(source, destination)
        copied[artifact_key] = str(destination)
    return copied


def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def run_overlay_materialization_preflight(
    *,
    m2455_summary_path: Path | str = DEFAULT_M2455_SUMMARY,
    candidate_rows_path: Path | str = DEFAULT_CANDIDATE_ROWS,
    role_protocol_rows_path: Path | str = DEFAULT_ROLE_PROTOCOL_ROWS,
    geometry_lever_rows_path: Path | str = DEFAULT_GEOMETRY_LEVER_ROWS,
    source_guardrail_rows_path: Path | str = DEFAULT_GUARDRAIL_ROWS,
    source_claim_boundary_path: Path | str = DEFAULT_CLAIM_BOUNDARY,
    preflight_work_items_path: Path | str = DEFAULT_M2458_PREFLIGHT_WORK_ITEMS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidates = read_csv_rows(candidate_rows_path)
    preflight_rows = read_csv_rows(preflight_work_items_path)
    target_preflight_rows = _target_preflight_rows(preflight_rows)
    overlay_rows, augmented_candidates, materialization_errors = materialize_candidate_rows(
        candidate_rows=candidates,
        preflight_rows=preflight_rows,
    )

    candidate_fieldnames = list(candidates[0].keys()) if candidates else []
    if "env_config_overlay_json" not in candidate_fieldnames:
        candidate_fieldnames.append("env_config_overlay_json")
    write_csv_rows(output / "concrete_overlay_rows.csv", overlay_rows, fieldnames=CONCRETE_OVERLAY_FIELDNAMES)
    write_csv_rows(output / "candidate_rows_with_overlays.csv", augmented_candidates, fieldnames=candidate_fieldnames)

    adapter_dir = output / "adapter"
    adapter_summary = run_reset_static_preflight_adapter(
        m2455_summary_path=m2455_summary_path,
        candidate_rows_path=output / "candidate_rows_with_overlays.csv",
        role_protocol_rows_path=role_protocol_rows_path,
        geometry_lever_rows_path=geometry_lever_rows_path,
        source_guardrail_rows_path=source_guardrail_rows_path,
        source_claim_boundary_path=source_claim_boundary_path,
        output_dir=adapter_dir,
        next_blocker=next_blocker,
    )
    adapter_artifacts = _copy_adapter_artifacts(adapter_dir, output)
    guards = guardrail_rows(
        overlay_rows=overlay_rows,
        target_preflight_count=len(target_preflight_rows),
        adapter_summary=adapter_summary,
        materialization_errors=materialization_errors,
    )
    guardrail_violation_count = sum(_bool(row.get("violation")) for row in guards)
    result_class = RESULT_PASS if guardrail_violation_count == 0 else RESULT_FAIL
    claims = claim_boundary_rows()
    decisions = decision_rows(next_blocker=next_blocker, result_class=result_class)

    failure_types = sorted(
        {
            str(row.get("failure_mode_to_preserve", ""))
            for row in guards
            if _bool(row.get("violation")) and str(row.get("failure_mode_to_preserve", ""))
        }
        | set(str(item) for item in adapter_summary.get("failure_types_observed", []))
    )
    if not failure_types and result_class == RESULT_FAIL:
        failure_types = ["scenario_sampling_failure"]

    write_csv_rows(output / "guardrail_rows.csv", guards, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decisions, fieldnames=DECISION_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_artifacts": {
            "m2455_summary": str(m2455_summary_path),
            "candidate_rows": str(candidate_rows_path),
            "role_protocol_rows": str(role_protocol_rows_path),
            "geometry_lever_rows": str(geometry_lever_rows_path),
            "source_guardrail_rows": str(source_guardrail_rows_path),
            "source_claim_boundary": str(source_claim_boundary_path),
            "m2458_preflight_work_items": str(preflight_work_items_path),
        },
        "source_candidate_row_count": len(candidates),
        "source_preflight_work_item_count": len(preflight_rows),
        "target_preflight_row_count": len(target_preflight_rows),
        "concrete_overlay_row_count": len(overlay_rows),
        "candidate_rows_with_overlay_count": sum(bool(str(row.get("env_config_overlay_json", "")).strip()) for row in augmented_candidates),
        "overlay_family_counts": _count_by(overlay_rows, "overlay_family"),
        "candidate_group_counts": _count_by(overlay_rows, "candidate_group"),
        "materialization_error_count": len(materialization_errors),
        "materialization_errors": list(materialization_errors),
        "adapter_result_class": adapter_summary.get("result_class", ""),
        "adapter_concrete_overlay_available_count": adapter_summary.get("concrete_overlay_available_count", 0),
        "adapter_static_check_fail_count": adapter_summary.get("static_check_fail_count", 0),
        "adapter_guardrail_violation_count": adapter_summary.get("guardrail_violation_count", 0),
        "adapter_reset_required_count": adapter_summary.get("reset_required_count", 0),
        "adapter_reset_attempted_count": adapter_summary.get("reset_attempted_count", 0),
        "adapter_reset_success_count": adapter_summary.get("reset_success_count", 0),
        "adapter_reset_blocked_missing_concrete_overlay_count": adapter_summary.get(
            "reset_blocked_missing_concrete_overlay_count", 0
        ),
        "labels_enter_actor_input_count": adapter_summary.get("labels_enter_actor_input_count", 0),
        "actor_input_contract_changed_count": adapter_summary.get("actor_input_contract_changed_count", 0),
        "scenario_redesign_executed": False,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "measured_policy_rollout_started": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "candidate_family_ranking_claim_made": False,
        "ranking_admissible_count": adapter_summary.get("ranking_admissible_count", 0),
        "winner_selected_count": adapter_summary.get("winner_selected_count", 0),
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "concrete_overlay_rows": str(output / "concrete_overlay_rows.csv"),
            "candidate_rows_with_overlays": str(output / "candidate_rows_with_overlays.csv"),
            "guardrail_rows": str(output / "guardrail_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "decision_rows": str(output / "decision_rows.csv"),
            **adapter_artifacts,
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2455-summary", type=Path, default=DEFAULT_M2455_SUMMARY)
    parser.add_argument("--candidate-rows", type=Path, default=DEFAULT_CANDIDATE_ROWS)
    parser.add_argument("--role-protocol-rows", type=Path, default=DEFAULT_ROLE_PROTOCOL_ROWS)
    parser.add_argument("--geometry-lever-rows", type=Path, default=DEFAULT_GEOMETRY_LEVER_ROWS)
    parser.add_argument("--source-guardrail-rows", type=Path, default=DEFAULT_GUARDRAIL_ROWS)
    parser.add_argument("--source-claim-boundary", type=Path, default=DEFAULT_CLAIM_BOUNDARY)
    parser.add_argument("--preflight-work-items", type=Path, default=DEFAULT_M2458_PREFLIGHT_WORK_ITEMS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_overlay_materialization_preflight(
        m2455_summary_path=args.m2455_summary,
        candidate_rows_path=args.candidate_rows,
        role_protocol_rows_path=args.role_protocol_rows,
        geometry_lever_rows_path=args.geometry_lever_rows,
        source_guardrail_rows_path=args.source_guardrail_rows,
        source_claim_boundary_path=args.source_claim_boundary,
        preflight_work_items_path=args.preflight_work_items,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"concrete_overlay_row_count={summary['concrete_overlay_row_count']}")
    print(f"adapter_concrete_overlay_available_count={summary['adapter_concrete_overlay_available_count']}")
    print(f"adapter_static_check_fail_count={summary['adapter_static_check_fail_count']}")
    print(f"adapter_reset_attempted_count={summary['adapter_reset_attempted_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    print(f"next_blocker={summary['next_blocker']}")
    return 0 if summary["result_class"] == RESULT_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
