"""Read-only load validation adapter for source-linked repair candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization as candidates
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_DIR = Path(
    "runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2424_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter"
)
DEFAULT_TARGET_CANDIDATE_COUNT = 4
DEFAULT_NEXT_BLOCKER = "m2425-paper-route-current-sim-dual-axis-source-linked-repair-plan-materialization-branch-synthesis"
RESULT_PASS = "current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter_pass"
RESULT_FAIL = "current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter_incomplete_or_fail"

VALIDATION_FIELDNAMES = [
    "candidate_id",
    "candidate_family",
    "overlay_path",
    "overlay_load_pass",
    "overlay_schema_pass",
    "overlay_under_run_dir",
    "table_payload_match",
    "source_row_key_count",
    "source_plan_row_count",
    "collision_guardrail_source_count",
    "r4_mitigation_source_count",
    "max_step_noncompletion_source_count",
    "speed_too_low_source_count",
    "diagnostic_monitoring_source_count",
    "family_membership_diagnostic_source_count",
    "diagnostic_rows_monitoring_only",
    "family_rows_monitoring_only",
    "source_linked_family_ranking_allowed",
    "support_policy_ranking_allowed",
    "artifact_only",
    "run_dir_only",
    "source_linked",
    "active_config_overwrite",
    "repair_execution_allowed",
    "training_allowed",
    "ranking_admissible",
    "winner_selected",
    "actor_input_contract_changed",
    "hidden_oracle_feature_injection",
]
GUARDRAIL_VALIDATION_FIELDNAMES = [
    "candidate_id",
    "guardrail_type",
    "artifact_ref",
    "artifact_exists",
    "source_row_count",
    "monitoring_only",
    "monitoring_only_expected",
    "monitoring_only_match",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_VALIDATION_FIELDNAMES = [
    "claim",
    "expected_admissible",
    "actual_admissible",
    "claim_boundary_pass",
]

REQUIRED_OVERLAY_KEYS = {
    "candidate_id",
    "candidate_family",
    "artifact_only",
    "run_dir_only",
    "source_linked",
    "active_config_overwrite",
    "repair_execution_allowed",
    "training_allowed",
    "ranking_admissible",
    "winner_selected",
    "source_lever_families",
    "source_plan_row_count",
    "source_row_keys",
    "candidate_levers",
    "acceptance_gates",
    "stop_rules",
    "guardrails",
}
REQUIRED_GUARDRAIL_TYPES = {
    "collision_non_regression": False,
    "r4_mitigation_semantics": False,
    "max_step_noncompletion": False,
    "speed_too_low": False,
    "diagnostic_monitoring": True,
    "source_linked_family_membership_diagnostic": True,
}
EXPECTED_FALSE_CLAIMS = {
    "active_config_overwrite",
    "candidate_ranking",
    "current_sim_verdict",
    "repair_execution",
    "scenario_redesign_executed",
    "source_linked_family_ranking",
    "support_policy_ranking",
    "training_repair_success",
}


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return candidates.read_csv_rows(path)


def _bool(value: Any, *, default: bool = False) -> bool:
    return candidates._bool(value, default=default)


def _int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _load_overlay(path: Path) -> tuple[dict[str, Any] | None, bool]:
    try:
        data = read_json(path)
    except (OSError, ValueError):
        return None, False
    return data if isinstance(data, dict) else None, isinstance(data, dict)


def _guardrail_dict(data: Mapping[str, Any] | None) -> Mapping[str, Any]:
    guardrails = (data or {}).get("guardrails", {})
    return guardrails if isinstance(guardrails, Mapping) else {}


def validate_candidate_row(row: Mapping[str, Any], *, source_dir: Path) -> dict[str, Any]:
    overlay_path = Path(str(row.get("overlay_path", "")))
    payload, load_pass = _load_overlay(overlay_path)
    guardrails = _guardrail_dict(payload)
    schema_pass = bool(payload) and REQUIRED_OVERLAY_KEYS.issubset(payload.keys())
    table_payload_match = bool(payload) and (
        str(payload.get("candidate_id")) == str(row.get("candidate_id"))
        and str(payload.get("candidate_family")) == str(row.get("candidate_family"))
        and _int(payload.get("source_plan_row_count")) == _int(row.get("source_plan_row_count"))
    )
    source_row_keys = payload.get("source_row_keys", []) if payload else []
    source_row_key_count = len(source_row_keys) if isinstance(source_row_keys, list) else 0
    return {
        "candidate_id": str(row.get("candidate_id", "")),
        "candidate_family": str(row.get("candidate_family", "")),
        "overlay_path": str(overlay_path),
        "overlay_load_pass": load_pass,
        "overlay_schema_pass": schema_pass,
        "overlay_under_run_dir": _is_under(overlay_path, source_dir),
        "table_payload_match": table_payload_match,
        "source_row_key_count": source_row_key_count,
        "source_plan_row_count": _int(row.get("source_plan_row_count")),
        "collision_guardrail_source_count": _int(guardrails.get("collision_guardrail_source_count")),
        "r4_mitigation_source_count": _int(guardrails.get("r4_mitigation_source_count")),
        "max_step_noncompletion_source_count": _int(guardrails.get("max_step_noncompletion_source_count")),
        "speed_too_low_source_count": _int(guardrails.get("speed_too_low_source_count")),
        "diagnostic_monitoring_source_count": _int(guardrails.get("diagnostic_monitoring_source_count")),
        "family_membership_diagnostic_source_count": _int(
            guardrails.get("family_membership_diagnostic_source_count")
        ),
        "diagnostic_rows_monitoring_only": _bool(guardrails.get("diagnostic_rows_monitoring_only")),
        "family_rows_monitoring_only": _bool(guardrails.get("family_rows_monitoring_only")),
        "source_linked_family_ranking_allowed": _bool(guardrails.get("source_linked_family_ranking_allowed")),
        "support_policy_ranking_allowed": _bool(guardrails.get("support_policy_ranking_allowed")),
        "artifact_only": _bool((payload or {}).get("artifact_only")),
        "run_dir_only": _bool((payload or {}).get("run_dir_only")),
        "source_linked": _bool((payload or {}).get("source_linked")),
        "active_config_overwrite": _bool((payload or {}).get("active_config_overwrite")),
        "repair_execution_allowed": _bool((payload or {}).get("repair_execution_allowed")),
        "training_allowed": _bool((payload or {}).get("training_allowed")),
        "ranking_admissible": _bool((payload or {}).get("ranking_admissible")) or _bool(row.get("ranking_admissible")),
        "winner_selected": _bool((payload or {}).get("winner_selected")) or _bool(row.get("winner_selected")),
        "actor_input_contract_changed": _bool(guardrails.get("actor_input_contract_changed")),
        "hidden_oracle_feature_injection": _bool(guardrails.get("hidden_oracle_feature_injection")),
    }


def validate_guardrail_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        guardrail_type = str(row.get("guardrail_type", ""))
        artifact_ref = Path(str(row.get("artifact_ref", "")))
        expected_monitoring = REQUIRED_GUARDRAIL_TYPES.get(guardrail_type, False)
        actual_monitoring = _bool(row.get("monitoring_only"))
        out.append(
            {
                "candidate_id": str(row.get("candidate_id", "")),
                "guardrail_type": guardrail_type,
                "artifact_ref": str(artifact_ref),
                "artifact_exists": artifact_ref.exists(),
                "source_row_count": _int(row.get("source_row_count")),
                "monitoring_only": actual_monitoring,
                "monitoring_only_expected": expected_monitoring,
                "monitoring_only_match": actual_monitoring == expected_monitoring,
                "ranking_admissible": _bool(row.get("ranking_admissible")),
                "winner_selected": _bool(row.get("winner_selected")),
            }
        )
    return out


def validate_claim_boundary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_claim = {str(row.get("claim", "")): row for row in rows}
    out = [
        {
            "claim": "artifact_only_source_linked_repair_candidate_materialization",
            "expected_admissible": True,
            "actual_admissible": _bool(
                by_claim.get("artifact_only_source_linked_repair_candidate_materialization", {}).get("admissible")
            ),
            "claim_boundary_pass": _bool(
                by_claim.get("artifact_only_source_linked_repair_candidate_materialization", {}).get("admissible")
            ),
        }
    ]
    for claim in sorted(EXPECTED_FALSE_CLAIMS):
        actual = _bool(by_claim.get(claim, {}).get("admissible"), default=True)
        out.append(
            {
                "claim": claim,
                "expected_admissible": False,
                "actual_admissible": actual,
                "claim_boundary_pass": not actual,
            }
        )
    return out


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _missing_guardrail_type_count(rows: Sequence[Mapping[str, Any]], target_candidate_count: int) -> int:
    counts = Counter(str(row.get("guardrail_type", "")) for row in rows)
    return sum(counts.get(guardrail_type, 0) != target_candidate_count for guardrail_type in REQUIRED_GUARDRAIL_TYPES)


def run_source_linked_candidate_reset_load_validation_adapter(
    *,
    source_dir: Path | str = DEFAULT_SOURCE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_candidate_count: int = DEFAULT_TARGET_CANDIDATE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(source_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    summary_path = source / "summary.json"
    overlay_rows_path = source / "repair_candidate_overlays.csv"
    guardrail_rows_path = source / "candidate_guardrail_metadata.csv"
    claim_boundary_path = source / "claim_boundary.csv"
    source_summary = read_json(summary_path)
    overlay_rows = read_csv_rows(overlay_rows_path)
    guardrail_rows = read_csv_rows(guardrail_rows_path)
    claim_rows = read_csv_rows(claim_boundary_path)

    validation_rows = [validate_candidate_row(row, source_dir=source) for row in overlay_rows]
    guardrail_validation_rows = validate_guardrail_rows(guardrail_rows)
    claim_validation_rows = validate_claim_boundary(claim_rows)

    overlay_load_pass_count = _flag_count(validation_rows, "overlay_load_pass")
    overlay_schema_failure_count = len(validation_rows) - _flag_count(validation_rows, "overlay_schema_pass")
    table_payload_mismatch_count = len(validation_rows) - _flag_count(validation_rows, "table_payload_match")
    source_row_key_count_mismatch_count = sum(
        _int(row.get("source_row_key_count")) != _int(row.get("source_plan_row_count")) for row in validation_rows
    )
    candidate_overlay_outside_run_dir_count = len(validation_rows) - _flag_count(validation_rows, "overlay_under_run_dir")
    guardrail_metadata_failure_count = (
        len(guardrail_validation_rows)
        - _flag_count(guardrail_validation_rows, "artifact_exists")
        + _flag_count(guardrail_validation_rows, "ranking_admissible")
        + _flag_count(guardrail_validation_rows, "winner_selected")
        + (len(guardrail_validation_rows) - _flag_count(guardrail_validation_rows, "monitoring_only_match"))
        + sum(_int(row.get("source_row_count")) <= 0 for row in guardrail_validation_rows)
        + _missing_guardrail_type_count(guardrail_validation_rows, int(target_candidate_count))
    )
    claim_boundary_failure_count = len(claim_validation_rows) - _flag_count(claim_validation_rows, "claim_boundary_pass")
    active_config_overwrite_count = _flag_count(validation_rows, "active_config_overwrite")
    repair_execution_allowed_count = _flag_count(validation_rows, "repair_execution_allowed")
    training_allowed_count = _flag_count(validation_rows, "training_allowed")
    ranking_admissible_count = _flag_count(validation_rows, "ranking_admissible") + _flag_count(
        guardrail_validation_rows, "ranking_admissible"
    )
    winner_selected_count = _flag_count(validation_rows, "winner_selected") + _flag_count(
        guardrail_validation_rows, "winner_selected"
    )
    actor_input_contract_change_count = _flag_count(validation_rows, "actor_input_contract_changed")
    hidden_oracle_feature_injection_count = _flag_count(validation_rows, "hidden_oracle_feature_injection")
    missing_collision_guardrail_count = sum(_int(row.get("collision_guardrail_source_count")) <= 0 for row in validation_rows)
    missing_r4_guardrail_count = sum(_int(row.get("r4_mitigation_source_count")) <= 0 for row in validation_rows)
    missing_max_step_guardrail_count = sum(
        _int(row.get("max_step_noncompletion_source_count")) <= 0 for row in validation_rows
    )
    missing_speed_too_low_guardrail_count = sum(_int(row.get("speed_too_low_source_count")) <= 0 for row in validation_rows)
    missing_diagnostic_guardrail_count = sum(
        _int(row.get("diagnostic_monitoring_source_count")) <= 0 for row in validation_rows
    )
    missing_family_diagnostic_guardrail_count = sum(
        _int(row.get("family_membership_diagnostic_source_count")) <= 0 for row in validation_rows
    )
    diagnostic_family_metadata_failure_count = (
        len(validation_rows)
        - _flag_count(validation_rows, "diagnostic_rows_monitoring_only")
        + len(validation_rows)
        - _flag_count(validation_rows, "family_rows_monitoring_only")
        + _flag_count(validation_rows, "source_linked_family_ranking_allowed")
        + _flag_count(validation_rows, "support_policy_ranking_allowed")
        + missing_diagnostic_guardrail_count
        + missing_family_diagnostic_guardrail_count
    )

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "controller_family_ranking_claim_made": False,
        "source_linked_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "candidate_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        str(source_summary.get("result_class", "")).endswith("_pass")
        and len(validation_rows) == int(target_candidate_count)
        and overlay_load_pass_count == int(target_candidate_count)
        and overlay_schema_failure_count == 0
        and table_payload_mismatch_count == 0
        and source_row_key_count_mismatch_count == 0
        and candidate_overlay_outside_run_dir_count == 0
        and guardrail_metadata_failure_count == 0
        and claim_boundary_failure_count == 0
        and active_config_overwrite_count == 0
        and repair_execution_allowed_count == 0
        and training_allowed_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and actor_input_contract_change_count == 0
        and hidden_oracle_feature_injection_count == 0
        and missing_collision_guardrail_count == 0
        and missing_r4_guardrail_count == 0
        and missing_max_step_guardrail_count == 0
        and missing_speed_too_low_guardrail_count == 0
        and missing_diagnostic_guardrail_count == 0
        and missing_family_diagnostic_guardrail_count == 0
        and diagnostic_family_metadata_failure_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "candidate_validation_rows.csv", validation_rows, fieldnames=VALIDATION_FIELDNAMES)
    write_csv_rows(output / "guardrail_validation_rows.csv", guardrail_validation_rows, fieldnames=GUARDRAIL_VALIDATION_FIELDNAMES)
    write_csv_rows(output / "claim_boundary_validation_rows.csv", claim_validation_rows, fieldnames=CLAIM_VALIDATION_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_dir": str(source),
        "source_summary": str(summary_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_overlay_rows": str(overlay_rows_path),
        "source_guardrail_metadata": str(guardrail_rows_path),
        "source_claim_boundary": str(claim_boundary_path),
        "candidate_count": len(validation_rows),
        "target_candidate_count": int(target_candidate_count),
        "overlay_load_pass_count": overlay_load_pass_count,
        "overlay_schema_failure_count": overlay_schema_failure_count,
        "table_payload_mismatch_count": table_payload_mismatch_count,
        "source_row_key_count_mismatch_count": source_row_key_count_mismatch_count,
        "candidate_overlay_outside_run_dir_count": candidate_overlay_outside_run_dir_count,
        "guardrail_metadata_row_count": len(guardrail_validation_rows),
        "guardrail_metadata_failure_count": guardrail_metadata_failure_count,
        "claim_boundary_failure_count": claim_boundary_failure_count,
        "diagnostic_family_metadata_failure_count": diagnostic_family_metadata_failure_count,
        "missing_collision_guardrail_count": missing_collision_guardrail_count,
        "missing_r4_guardrail_count": missing_r4_guardrail_count,
        "missing_max_step_guardrail_count": missing_max_step_guardrail_count,
        "missing_speed_too_low_guardrail_count": missing_speed_too_low_guardrail_count,
        "missing_diagnostic_guardrail_count": missing_diagnostic_guardrail_count,
        "missing_family_diagnostic_guardrail_count": missing_family_diagnostic_guardrail_count,
        "active_config_overwrite_count": active_config_overwrite_count,
        "repair_execution_allowed_count": repair_execution_allowed_count,
        "training_allowed_count": training_allowed_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "actor_input_contract_change_count": actor_input_contract_change_count,
        "hidden_oracle_feature_injection_count": hidden_oracle_feature_injection_count,
        "candidate_family_counts": _count_by(validation_rows, "candidate_family"),
        "guardrail_type_counts": _count_by(guardrail_validation_rows, "guardrail_type"),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "controller_family_ranking_claim_made": False,
        "source_linked_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "candidate_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "candidate_validation_rows": str(output / "candidate_validation_rows.csv"),
            "guardrail_validation_rows": str(output / "guardrail_validation_rows.csv"),
            "claim_boundary_validation_rows": str(output / "claim_boundary_validation_rows.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-candidate-count", type=int, default=DEFAULT_TARGET_CANDIDATE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_source_linked_candidate_reset_load_validation_adapter(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        target_candidate_count=int(args.target_candidate_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"overlay_load_pass_count={summary['overlay_load_pass_count']}")
    print(f"overlay_schema_failure_count={summary['overlay_schema_failure_count']}")
    print(f"guardrail_metadata_failure_count={summary['guardrail_metadata_failure_count']}")
    print(f"diagnostic_family_metadata_failure_count={summary['diagnostic_family_metadata_failure_count']}")
    print(f"candidate_overlay_outside_run_dir_count={summary['candidate_overlay_outside_run_dir_count']}")
    print(f"active_config_overwrite_count={summary['active_config_overwrite_count']}")
    print(f"ranking_admissible_count={summary['ranking_admissible_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
