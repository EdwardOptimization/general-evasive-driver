"""Run-dir-only source-linked repair candidate materialization."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization as repair_plan
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_DIR = Path(
    "runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization"
)
DEFAULT_TARGET_OFFTRACK_ROW_COUNT = 59
DEFAULT_MAX_CANDIDATE_COUNT = 4
DEFAULT_NEXT_BLOCKER = (
    "m2423-paper-route-current-sim-dual-axis-source-linked-repair-candidate-materialization-result-audit"
)
RESULT_PASS = "current_sim_dual_axis_source_linked_repair_candidate_materialization_pass"
RESULT_FAIL = "current_sim_dual_axis_source_linked_repair_candidate_materialization_incomplete_or_fail"

CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "candidate_family",
    "source_lever_families",
    "source_plan_row_count",
    "with_collision_guardrail_count",
    "mean_offtrack_rate",
    "mean_collision_rate",
    "mean_max_step_noncompletion_rate",
    "mean_speed_too_low_rate",
    "collision_guardrail_source_count",
    "r4_mitigation_source_count",
    "max_step_source_count",
    "speed_too_low_source_count",
    "diagnostic_monitoring_source_count",
    "family_membership_diagnostic_source_count",
    "overlay_path",
    "run_dir_only",
    "active_config_overwrite",
    "repair_execution_allowed",
    "training_allowed",
    "ranking_admissible",
    "winner_selected",
    "guardrail_metadata_attached",
    "diagnostic_rows_monitoring_only",
    "family_rows_monitoring_only",
    "candidate_levers",
    "acceptance_gates",
    "stop_rules",
]
GUARDRAIL_FIELDNAMES = [
    "candidate_id",
    "guardrail_type",
    "source_row_count",
    "required_gate",
    "artifact_ref",
    "monitoring_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]

CANDIDATE_DEFINITIONS = [
    {
        "candidate_id": "c01_source_linked_geometry_timing_containment",
        "candidate_family": "source_linked_geometry_timing_containment",
        "lever_families": ["geometry_timing_containment"],
        "candidate_levers": [
            "source-linked obstacle timing and road-boundary margin containment",
            "commitment timing and terminal offtrack threshold audit",
            "collision/R4/max-step/speed-low guardrails attached before execution",
        ],
    },
    {
        "candidate_id": "c02_source_linked_hidden_dynamics_response_containment",
        "candidate_family": "source_linked_hidden_dynamics_response_containment",
        "lever_families": ["hidden_dynamics_actuator_response_robustness"],
        "candidate_levers": [
            "hidden-dynamics bucket offtrack containment",
            "weak-brake and slow-steer response robustness audit",
            "no hidden or oracle actor input",
        ],
    },
    {
        "candidate_id": "c03_source_linked_role_conditioned_containment",
        "candidate_family": "source_linked_role_conditioned_containment",
        "lever_families": ["role_conditioned_containment", "role_semantics_containment"],
        "candidate_levers": [
            "role-conditioned road-boundary containment",
            "role semantics non-regression guardrail",
            "R2/R4/R5 source-linked family diagnostics remain non-ranking",
        ],
    },
    {
        "candidate_id": "c04_source_linked_outcome_failure_surface_containment",
        "candidate_family": "source_linked_outcome_failure_surface_containment",
        "lever_families": ["outcome_failure_surface_containment"],
        "candidate_levers": [
            "outcome-failure surface containment",
            "do not hide offtrack by increasing collision or noncompletion",
            "treat singleton outcome target as guarded diagnostic before execution",
        ],
    },
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return repair_plan.read_csv_rows(path)


def _bool(value: Any, *, default: bool = False) -> bool:
    return repair_plan._bool(value, default=default)


def _float(value: Any, *, default: float = 0.0) -> float:
    return repair_plan._float(value, default=default)


def _join(values: Iterable[str]) -> str:
    return "; ".join(value for value in values if value)


def _mean(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return sum(_float(row.get(key)) for row in rows) / float(len(rows))


def _safe_overlay_path(output: Path, candidate_id: str) -> Path:
    return output / "repair_candidate_overlays" / f"{candidate_id}.json"


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _candidate_rows(rows: Sequence[Mapping[str, Any]], lever_families: Sequence[str]) -> list[dict[str, Any]]:
    families = set(lever_families)
    return [dict(row) for row in rows if str(row.get("lever_family", "")) in families]


def _candidate_acceptance_gates(rows: Sequence[Mapping[str, Any]]) -> str:
    gates = [
        "target offtrack rate decreases or terminal road-margin tail improves",
        "collision guardrail metadata gates do not regress",
        "R4 mitigation semantics do not regress",
        "max-step noncompletion does not increase",
        "speed-too-low guardrail does not regress",
        "source-linked family diagnostics remain monitoring-only and non-ranking",
        "active config remains unchanged until a later admitted execution milestone",
    ]
    if any(str(row.get("plan_route", "")) == "offtrack_repair_plan_with_collision_guardrail" for row in rows):
        gates.append("same-row offtrack-with-collision guardrail passes")
    return _join(gates)


def _candidate_stop_rules() -> str:
    return _join(
        [
            "stop if active config overwrite is required",
            "stop if candidate/profile/family ranking is required",
            "stop if collision rises while offtrack improves",
            "stop if R4 mitigation semantics regress",
            "stop if max-step or speed-too-low failures increase to hide offtrack",
            "stop if actor input contract would change",
            "stop if hidden or oracle features are needed",
        ]
    )


def _source_row_keys(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return [
        f"{row.get('source_table', '')}:{row.get('slice_axis', '')}:{row.get('slice_value', '')}" for row in rows
    ]


def _all_monitoring_only(rows: Sequence[Mapping[str, Any]]) -> bool:
    return all(
        _bool(row.get("diagnostic_only_monitoring"))
        and not _bool(row.get("repair_execution_allowed"))
        and not _bool(row.get("training_allowed"))
        and not _bool(row.get("ranking_admissible"))
        and not _bool(row.get("winner_selected"))
        for row in rows
    )


def _source_flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def build_candidate_overlay(
    *,
    definition: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    output: Path,
    collision_guardrail_count: int,
    r4_guardrail_count: int,
    max_step_count: int,
    speed_too_low_count: int,
    diagnostic_count: int,
    family_diagnostic_count: int,
    diagnostic_rows_monitoring_only: bool,
    family_rows_monitoring_only: bool,
) -> dict[str, Any]:
    candidate_id = str(definition["candidate_id"])
    overlay_path = _safe_overlay_path(output, candidate_id)
    with_collision = sum(str(row.get("plan_route", "")) == "offtrack_repair_plan_with_collision_guardrail" for row in rows)
    metadata_attached = all(
        count > 0
        for count in [
            collision_guardrail_count,
            r4_guardrail_count,
            max_step_count,
            speed_too_low_count,
            diagnostic_count,
            family_diagnostic_count,
        ]
    )
    row = {
        "candidate_id": candidate_id,
        "candidate_family": str(definition["candidate_family"]),
        "source_lever_families": _join(str(value) for value in definition["lever_families"]),
        "source_plan_row_count": len(rows),
        "with_collision_guardrail_count": with_collision,
        "mean_offtrack_rate": _mean(rows, "offtrack_rate"),
        "mean_collision_rate": _mean(rows, "collision_rate"),
        "mean_max_step_noncompletion_rate": _mean(rows, "max_step_noncompletion_rate"),
        "mean_speed_too_low_rate": _mean(rows, "speed_too_low_rate"),
        "collision_guardrail_source_count": collision_guardrail_count,
        "r4_mitigation_source_count": r4_guardrail_count,
        "max_step_source_count": max_step_count,
        "speed_too_low_source_count": speed_too_low_count,
        "diagnostic_monitoring_source_count": diagnostic_count,
        "family_membership_diagnostic_source_count": family_diagnostic_count,
        "overlay_path": str(overlay_path),
        "run_dir_only": _is_under(overlay_path, output),
        "active_config_overwrite": False,
        "repair_execution_allowed": False,
        "training_allowed": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "guardrail_metadata_attached": metadata_attached,
        "diagnostic_rows_monitoring_only": diagnostic_rows_monitoring_only,
        "family_rows_monitoring_only": family_rows_monitoring_only,
        "candidate_levers": _join(str(value) for value in definition["candidate_levers"]),
        "acceptance_gates": _candidate_acceptance_gates(rows),
        "stop_rules": _candidate_stop_rules(),
    }
    overlay_payload = {
        "candidate_id": row["candidate_id"],
        "candidate_family": row["candidate_family"],
        "artifact_only": True,
        "run_dir_only": True,
        "source_linked": True,
        "active_config_overwrite": False,
        "repair_execution_allowed": False,
        "training_allowed": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "source_lever_families": list(definition["lever_families"]),
        "source_plan_row_count": len(rows),
        "with_collision_guardrail_count": with_collision,
        "source_row_keys": _source_row_keys(rows),
        "candidate_levers": list(definition["candidate_levers"]),
        "acceptance_gates": row["acceptance_gates"],
        "stop_rules": row["stop_rules"],
        "guardrails": {
            "collision_guardrail_source_count": collision_guardrail_count,
            "r4_mitigation_source_count": r4_guardrail_count,
            "max_step_noncompletion_source_count": max_step_count,
            "speed_too_low_source_count": speed_too_low_count,
            "diagnostic_monitoring_source_count": diagnostic_count,
            "family_membership_diagnostic_source_count": family_diagnostic_count,
            "diagnostic_rows_monitoring_only": diagnostic_rows_monitoring_only,
            "family_rows_monitoring_only": family_rows_monitoring_only,
            "source_linked_family_ranking_allowed": False,
            "support_policy_ranking_allowed": False,
            "actor_input_contract_changed": False,
            "hidden_oracle_feature_injection": False,
        },
    }
    write_json(overlay_path, overlay_payload)
    return row


def build_guardrail_rows(
    *,
    candidates: Sequence[Mapping[str, Any]],
    counts: Mapping[str, int],
    output: Path,
) -> list[dict[str, Any]]:
    definitions = [
        (
            "collision_non_regression",
            "collision_guardrail_source_row_count",
            "collision rate and clearance-tail non-regression",
            "collision_guardrail_plan_rows.csv",
            False,
        ),
        (
            "r4_mitigation_semantics",
            "r4_mitigation_source_row_count",
            "R4 mitigation semantics and impact-severity non-regression",
            "r4_mitigation_plan_rows.csv",
            False,
        ),
        (
            "max_step_noncompletion",
            "max_step_source_row_count",
            "max-step noncompletion must not increase",
            "max_step_noncompletion_plan_rows.csv",
            False,
        ),
        (
            "speed_too_low",
            "speed_too_low_source_row_count",
            "speed-too-low failures must not increase",
            "speed_too_low_plan_rows.csv",
            False,
        ),
        (
            "diagnostic_monitoring",
            "diagnostic_monitoring_source_row_count",
            "diagnostic rows remain monitoring-only and non-ranking",
            "diagnostic_monitoring_rows.csv",
            True,
        ),
        (
            "source_linked_family_membership_diagnostic",
            "family_membership_diagnostic_source_row_count",
            "overlapping family diagnostics remain monitoring-only and non-ranking",
            "family_membership_diagnostic_rows.csv",
            True,
        ),
    ]
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        for guardrail_type, count_key, required_gate, artifact_name, monitoring_only in definitions:
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "guardrail_type": guardrail_type,
                    "source_row_count": int(counts[count_key]),
                    "required_gate": required_gate,
                    "artifact_ref": str(output / artifact_name),
                    "monitoring_only": monitoring_only,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
    return rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_source_linked_repair_candidate_materialization",
            "admissible": True,
            "reason": "M2422 may claim only run-dir-only source-linked candidate overlay materialization",
        },
        {
            "claim": "active_config_overwrite",
            "admissible": False,
            "reason": "M2422 must not write outside its output run directory",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2422 does not execute repair levers",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2422 creates overlay artifacts only and does not execute redesigned scenarios",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2422 does not train, replay, or run PPO",
        },
        {
            "claim": "source_linked_family_ranking",
            "admissible": False,
            "reason": "family-membership diagnostics are overlapping and non-ranking",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "profile and support-policy diagnostics remain non-ranking",
        },
        {
            "claim": "candidate_ranking",
            "admissible": False,
            "reason": "candidate overlays are a compact non-ranking set for later audit",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2422 does not run measured validation",
        },
    ]


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _candidate_source_lever_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("source_lever_families", "")) for row in rows).items()))


def run_source_linked_repair_candidate_materialization(
    *,
    source_dir: Path | str = DEFAULT_SOURCE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_offtrack_row_count: int = DEFAULT_TARGET_OFFTRACK_ROW_COUNT,
    max_candidate_count: int = DEFAULT_MAX_CANDIDATE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(source_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "repair_candidate_overlays").mkdir(parents=True, exist_ok=True)

    summary_path = source / "summary.json"
    repair_plan_path = source / "repair_plan_rows.csv"
    offtrack_path = source / "offtrack_repair_plan_rows.csv"
    collision_path = source / "collision_guardrail_plan_rows.csv"
    r4_path = source / "r4_mitigation_plan_rows.csv"
    max_step_path = source / "max_step_noncompletion_plan_rows.csv"
    speed_too_low_path = source / "speed_too_low_plan_rows.csv"
    diagnostic_path = source / "diagnostic_monitoring_rows.csv"
    family_path = source / "family_membership_diagnostic_rows.csv"
    source_summary = read_json(summary_path)
    repair_plan_rows = read_csv_rows(repair_plan_path)
    offtrack_rows = read_csv_rows(offtrack_path)
    collision_rows = read_csv_rows(collision_path)
    r4_rows = read_csv_rows(r4_path)
    max_step_rows = read_csv_rows(max_step_path)
    speed_too_low_rows = read_csv_rows(speed_too_low_path)
    diagnostic_rows = read_csv_rows(diagnostic_path)
    family_rows = read_csv_rows(family_path)

    diagnostic_rows_monitoring_only = _all_monitoring_only(diagnostic_rows)
    family_rows_monitoring_only = _all_monitoring_only(family_rows)
    guardrail_counts = {
        "collision_guardrail_source_row_count": len(collision_rows),
        "r4_mitigation_source_row_count": len(r4_rows),
        "max_step_source_row_count": len(max_step_rows),
        "speed_too_low_source_row_count": len(speed_too_low_rows),
        "diagnostic_monitoring_source_row_count": len(diagnostic_rows),
        "family_membership_diagnostic_source_row_count": len(family_rows),
    }

    candidate_rows: list[dict[str, Any]] = []
    assigned_row_count = 0
    for definition in CANDIDATE_DEFINITIONS:
        rows = _candidate_rows(offtrack_rows, definition["lever_families"])
        assigned_row_count += len(rows)
        if not rows:
            continue
        candidate_rows.append(
            build_candidate_overlay(
                definition=definition,
                rows=rows,
                output=output,
                collision_guardrail_count=len(collision_rows),
                r4_guardrail_count=len(r4_rows),
                max_step_count=len(max_step_rows),
                speed_too_low_count=len(speed_too_low_rows),
                diagnostic_count=len(diagnostic_rows),
                family_diagnostic_count=len(family_rows),
                diagnostic_rows_monitoring_only=diagnostic_rows_monitoring_only,
                family_rows_monitoring_only=family_rows_monitoring_only,
            )
        )

    guardrail_rows = build_guardrail_rows(candidates=candidate_rows, counts=guardrail_counts, output=output)
    overlay_paths = [Path(row["overlay_path"]) for row in candidate_rows]
    outside_run_dir_count = sum(not _is_under(path, output) for path in overlay_paths)
    missing_overlay_count = sum(not path.exists() for path in overlay_paths)
    active_config_overwrite_count = _flag_count(candidate_rows, "active_config_overwrite")
    repair_execution_allowed_count = _flag_count(candidate_rows, "repair_execution_allowed")
    training_allowed_count = _flag_count(candidate_rows, "training_allowed")
    ranking_admissible_count = _flag_count(candidate_rows, "ranking_admissible") + _flag_count(
        guardrail_rows, "ranking_admissible"
    )
    winner_selected_count = _flag_count(candidate_rows, "winner_selected") + _flag_count(guardrail_rows, "winner_selected")
    guardrail_metadata_missing_count = sum(not _bool(row.get("guardrail_metadata_attached")) for row in candidate_rows)
    source_ranking_admissible_count = _source_flag_count(repair_plan_rows, "ranking_admissible")
    source_winner_selected_count = _source_flag_count(repair_plan_rows, "winner_selected")
    source_family_ranking_claim_count = _source_flag_count(repair_plan_rows, "source_linked_family_ranking_claim_made")
    source_support_policy_ranking_claim_count = _source_flag_count(repair_plan_rows, "support_policy_ranking_claim_made")

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
        and len(offtrack_rows) == int(target_offtrack_row_count)
        and assigned_row_count == len(offtrack_rows)
        and 0 < len(candidate_rows) <= int(max_candidate_count)
        and all(count > 0 for count in guardrail_counts.values())
        and len(guardrail_rows) == len(candidate_rows) * 6
        and outside_run_dir_count == 0
        and missing_overlay_count == 0
        and active_config_overwrite_count == 0
        and repair_execution_allowed_count == 0
        and training_allowed_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_metadata_missing_count == 0
        and diagnostic_rows_monitoring_only
        and family_rows_monitoring_only
        and source_ranking_admissible_count == 0
        and source_winner_selected_count == 0
        and source_family_ranking_claim_count == 0
        and source_support_policy_ranking_claim_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "repair_candidate_overlays.csv", candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(output / "candidate_guardrail_metadata.csv", guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(output / "repair_plan_rows.csv", repair_plan_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(output / "offtrack_repair_plan_rows.csv", offtrack_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(output / "collision_guardrail_plan_rows.csv", collision_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(output / "r4_mitigation_plan_rows.csv", r4_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(output / "max_step_noncompletion_plan_rows.csv", max_step_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(output / "speed_too_low_plan_rows.csv", speed_too_low_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(output / "diagnostic_monitoring_rows.csv", diagnostic_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(output / "family_membership_diagnostic_rows.csv", family_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_dir": str(source),
        "source_summary": str(summary_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_repair_plan_rows": str(repair_plan_path),
        "source_offtrack_repair_plan_rows": str(offtrack_path),
        "source_collision_guardrail_rows": str(collision_path),
        "source_r4_mitigation_rows": str(r4_path),
        "source_max_step_noncompletion_rows": str(max_step_path),
        "source_speed_too_low_rows": str(speed_too_low_path),
        "source_diagnostic_monitoring_rows": str(diagnostic_path),
        "source_family_membership_diagnostic_rows": str(family_path),
        "source_repair_plan_row_count": len(repair_plan_rows),
        "source_offtrack_repair_plan_row_count": len(offtrack_rows),
        "target_offtrack_repair_plan_row_count": int(target_offtrack_row_count),
        "assigned_offtrack_repair_plan_row_count": assigned_row_count,
        "unassigned_offtrack_repair_plan_row_count": len(offtrack_rows) - assigned_row_count,
        "candidate_count": len(candidate_rows),
        "max_candidate_count": int(max_candidate_count),
        "candidate_overlay_written_count": len(candidate_rows) - missing_overlay_count,
        "candidate_overlay_outside_run_dir_count": outside_run_dir_count,
        "collision_guardrail_source_row_count": len(collision_rows),
        "r4_mitigation_source_row_count": len(r4_rows),
        "max_step_source_row_count": len(max_step_rows),
        "speed_too_low_source_row_count": len(speed_too_low_rows),
        "diagnostic_monitoring_source_row_count": len(diagnostic_rows),
        "family_membership_diagnostic_source_row_count": len(family_rows),
        "guardrail_metadata_row_count": len(guardrail_rows),
        "guardrail_metadata_missing_count": guardrail_metadata_missing_count,
        "diagnostic_rows_monitoring_only": diagnostic_rows_monitoring_only,
        "family_rows_monitoring_only": family_rows_monitoring_only,
        "candidate_family_counts": _count_by(candidate_rows, "candidate_family"),
        "source_lever_family_counts": _candidate_source_lever_counts(candidate_rows),
        "offtrack_source_plan_route_counts": _count_by(offtrack_rows, "plan_route"),
        "offtrack_source_lever_family_counts": _count_by(offtrack_rows, "lever_family"),
        "source_ranking_admissible_count": source_ranking_admissible_count,
        "source_winner_selected_count": source_winner_selected_count,
        "source_family_ranking_claim_count": source_family_ranking_claim_count,
        "source_support_policy_ranking_claim_count": source_support_policy_ranking_claim_count,
        "active_config_overwrite_count": active_config_overwrite_count,
        "repair_execution_allowed_count": repair_execution_allowed_count,
        "training_allowed_count": training_allowed_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
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
            "repair_candidate_overlays": str(output / "repair_candidate_overlays.csv"),
            "candidate_guardrail_metadata": str(output / "candidate_guardrail_metadata.csv"),
            "repair_plan_rows": str(output / "repair_plan_rows.csv"),
            "offtrack_repair_plan_rows": str(output / "offtrack_repair_plan_rows.csv"),
            "collision_guardrail_plan_rows": str(output / "collision_guardrail_plan_rows.csv"),
            "r4_mitigation_plan_rows": str(output / "r4_mitigation_plan_rows.csv"),
            "max_step_noncompletion_plan_rows": str(output / "max_step_noncompletion_plan_rows.csv"),
            "speed_too_low_plan_rows": str(output / "speed_too_low_plan_rows.csv"),
            "diagnostic_monitoring_rows": str(output / "diagnostic_monitoring_rows.csv"),
            "family_membership_diagnostic_rows": str(output / "family_membership_diagnostic_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "overlay_dir": str(output / "repair_candidate_overlays"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-offtrack-row-count", type=int, default=DEFAULT_TARGET_OFFTRACK_ROW_COUNT)
    parser.add_argument("--max-candidate-count", type=int, default=DEFAULT_MAX_CANDIDATE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_source_linked_repair_candidate_materialization(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        target_offtrack_row_count=int(args.target_offtrack_row_count),
        max_candidate_count=int(args.max_candidate_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_offtrack_repair_plan_row_count={summary['source_offtrack_repair_plan_row_count']}")
    print(f"assigned_offtrack_repair_plan_row_count={summary['assigned_offtrack_repair_plan_row_count']}")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"candidate_overlay_written_count={summary['candidate_overlay_written_count']}")
    print(f"candidate_overlay_outside_run_dir_count={summary['candidate_overlay_outside_run_dir_count']}")
    print(f"guardrail_metadata_row_count={summary['guardrail_metadata_row_count']}")
    print(f"active_config_overwrite_count={summary['active_config_overwrite_count']}")
    print(f"repair_execution_allowed_count={summary['repair_execution_allowed_count']}")
    print(f"ranking_admissible_count={summary['ranking_admissible_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == RESULT_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
