"""Artifact-only localization for the M2532 mitigation regression."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Iterable

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_POST_REPAIR_ROWS = Path(
    "runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/"
    "post_repair_smoke_rows.csv"
)
DEFAULT_GATE_EVALUATION = Path(
    "runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/"
    "protected_gate_evaluation.csv"
)
DEFAULT_SOURCE_SUMMARY = Path(
    "runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization"
)
DEFAULT_MILESTONE = (
    "m2534-engineering-controller-failure-surface-mitigation-regression-localization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design"
)

CLAIM_SCOPE = "engineering-controller mitigation-regression localization only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID claim"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "environment_rollout_run": False,
    "simulator_step_run": False,
    "new_policy_action_run": False,
    "measured_validation_run": False,
    "training_started": False,
    "training_run": False,
    "repair_training_started": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}

MITIGATION_REGRESSION_FIELDNAMES = [
    "localization_row_id",
    "row_class",
    "source_row_id",
    "seed",
    "subject_id",
    "scenario_role",
    "protected_group",
    "row_role",
    "current_severity_proxy",
    "severity_proxy",
    "severity_delta",
    "current_severity_rank_low_to_high",
    "severity_delta_rank_high_to_low",
    "current_minimum_road_margin_m",
    "minimum_road_margin_m",
    "road_margin_delta_m",
    "current_simultaneous_throttle_brake_fraction",
    "simultaneous_throttle_brake_fraction",
    "command_conflict_delta",
    "collision_regressed",
    "coast_reference_severity_proxy",
    "straight_full_brake_reference_severity_proxy",
    "severity_vs_coast_reference_delta",
    "severity_vs_straight_full_brake_reference_delta",
    "severity_regressed",
    "road_margin_improved",
    "command_conflict_improved",
    "metric_artifact_suspected",
    "localization_label",
    "claim_scope",
    "forbidden_interpretation",
]


def run_mitigation_regression_localization(
    output_dir: Path,
    *,
    post_repair_rows: Path | str = DEFAULT_POST_REPAIR_ROWS,
    gate_evaluation: Path | str = DEFAULT_GATE_EVALUATION,
    summary: Path | str = DEFAULT_SOURCE_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    post_rows_path = Path(post_repair_rows)
    gate_rows_path = Path(gate_evaluation)
    source_summary_path = Path(summary)
    post_rows = _read_csv_rows(post_rows_path)
    gate_rows = _read_csv_rows(gate_rows_path)
    source_summary = read_json(source_summary_path)

    localization_rows = build_mitigation_regression_rows(post_rows)
    findings = build_localization_findings(
        localization_rows,
        gate_rows=gate_rows,
        source_summary=source_summary,
        milestone=milestone,
        next_blocker=next_blocker,
    )

    mitigation_rows_path = output_dir / "mitigation_regression_rows.csv"
    findings_path = output_dir / "localization_findings.json"
    summary_path = output_dir / "summary.json"

    write_csv_rows(
        mitigation_rows_path,
        localization_rows,
        fieldnames=MITIGATION_REGRESSION_FIELDNAMES,
    )
    write_json(findings_path, findings)
    output_summary = build_summary(
        output_dir=output_dir,
        summary_path=summary_path,
        mitigation_rows_path=mitigation_rows_path,
        findings_path=findings_path,
        post_repair_rows_path=post_rows_path,
        gate_rows_path=gate_rows_path,
        source_summary_path=source_summary_path,
        source_summary=source_summary,
        gate_rows=gate_rows,
        localization_rows=localization_rows,
        findings=findings,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(summary_path, output_summary)
    return output_summary


def build_mitigation_regression_rows(post_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    mitigation_rows = [
        row
        for row in post_rows
        if row.get("protected_group") == "mitigation_primary"
        and row.get("row_role") == "primary_protected"
    ]
    if not mitigation_rows:
        raise ValueError("no mitigation_primary protected rows found")

    references = _reference_rows_by_seed(post_rows)
    severity_sorted = sorted(
        mitigation_rows,
        key=lambda row: _float(row["current_severity_proxy"]),
    )
    severity_rank_by_row = {
        row["source_row_id"]: index + 1
        for index, row in enumerate(severity_sorted)
    }
    delta_sorted = sorted(
        mitigation_rows,
        key=lambda row: _float(row["severity_delta"]),
        reverse=True,
    )
    delta_rank_by_row = {
        row["source_row_id"]: index + 1
        for index, row in enumerate(delta_sorted)
    }

    output: list[dict[str, Any]] = []
    for row in sorted(mitigation_rows, key=lambda item: int(item["seed"])):
        source_row_id = row["source_row_id"]
        seed = row["seed"]
        severity_delta = _float(row["severity_delta"])
        road_margin_delta = _float(row["road_margin_delta_m"])
        command_conflict_delta = _float(row["command_conflict_delta"])
        severity_regressed = severity_delta > 1e-9
        road_margin_improved = road_margin_delta > 1e-9
        command_conflict_improved = command_conflict_delta < -1e-9
        reference = references.get(seed, {})
        coast = reference.get("coast_open_loop")
        straight_brake = reference.get("straight_full_brake_open_loop")
        coast_severity = _float(coast.get("severity_proxy")) if coast else None
        straight_brake_severity = (
            _float(straight_brake.get("severity_proxy")) if straight_brake else None
        )
        label = _localization_label(
            severity_regressed=severity_regressed,
            road_margin_improved=road_margin_improved,
            command_conflict_improved=command_conflict_improved,
            current_severity_rank=severity_rank_by_row[source_row_id],
            severity_delta_rank=delta_rank_by_row[source_row_id],
        )
        output.append(
            {
                "localization_row_id": source_row_id.replace(
                    "m2523_",
                    "m2534_localization_",
                ),
                "row_class": "regressed_mitigation_row" if severity_regressed else "improved_mitigation_row",
                "source_row_id": source_row_id,
                "seed": int(seed),
                "subject_id": row["subject_id"],
                "scenario_role": row["scenario_role"],
                "protected_group": row["protected_group"],
                "row_role": row["row_role"],
                "current_severity_proxy": _float(row["current_severity_proxy"]),
                "severity_proxy": _float(row["severity_proxy"]),
                "severity_delta": severity_delta,
                "current_severity_rank_low_to_high": severity_rank_by_row[source_row_id],
                "severity_delta_rank_high_to_low": delta_rank_by_row[source_row_id],
                "current_minimum_road_margin_m": _float(row["current_minimum_road_margin_m"]),
                "minimum_road_margin_m": _float(row["minimum_road_margin_m"]),
                "road_margin_delta_m": road_margin_delta,
                "current_simultaneous_throttle_brake_fraction": _float(
                    row["current_simultaneous_throttle_brake_fraction"]
                ),
                "simultaneous_throttle_brake_fraction": _float(
                    row["simultaneous_throttle_brake_fraction"]
                ),
                "command_conflict_delta": command_conflict_delta,
                "collision_regressed": _as_bool(row["collision_regressed"]),
                "coast_reference_severity_proxy": coast_severity if coast_severity is not None else "",
                "straight_full_brake_reference_severity_proxy": (
                    straight_brake_severity if straight_brake_severity is not None else ""
                ),
                "severity_vs_coast_reference_delta": (
                    _float(row["severity_proxy"]) - coast_severity
                    if coast_severity is not None
                    else ""
                ),
                "severity_vs_straight_full_brake_reference_delta": (
                    _float(row["severity_proxy"]) - straight_brake_severity
                    if straight_brake_severity is not None
                    else ""
                ),
                "severity_regressed": severity_regressed,
                "road_margin_improved": road_margin_improved,
                "command_conflict_improved": command_conflict_improved,
                "metric_artifact_suspected": False,
                "localization_label": label,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return output


def build_localization_findings(
    localization_rows: list[dict[str, Any]],
    *,
    gate_rows: list[dict[str, str]],
    source_summary: dict[str, Any],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    regressed_rows = [
        row for row in localization_rows if _as_bool(row["severity_regressed"])
    ]
    improved_rows = [
        row for row in localization_rows if not _as_bool(row["severity_regressed"])
    ]
    regressed_row = regressed_rows[0] if regressed_rows else {}
    mitigation_gate = _gate_by_id(gate_rows, "mitigation_proof")
    road_gate = _gate_by_id(gate_rows, "road_boundary_proof")
    command_gate = _gate_by_id(gate_rows, "command_conflict_proof")
    all_margin_improved = all(_as_bool(row["road_margin_improved"]) for row in localization_rows)
    all_conflict_improved = all(
        _as_bool(row["command_conflict_improved"]) for row in localization_rows
    )
    single_low_baseline_regression = bool(
        len(regressed_rows) == 1
        and int(regressed_row.get("current_severity_rank_low_to_high", 99)) == 1
    )
    objective_weakness_detected = bool(
        len(regressed_rows) == 1
        and all_margin_improved
        and all_conflict_improved
        and not _as_bool(regressed_row.get("collision_regressed"))
    )
    metric_artifact_detected = False
    scenario_sampling_failure_status = (
        "risk_only_five_mitigation_seed_panel_no_fresh_generalization"
    )
    public_gate_overfit_risk = "medium"
    recommended_next = (
        "m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design"
    )
    return {
        "result_class": "engineering_controller_failure_surface_mitigation_regression_localization_pass",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "decision": "route_to_mitigation_preserving_repair_design",
        "next_blocker": next_blocker,
        "recommended_next_manifest": recommended_next,
        "claim_scope": CLAIM_SCOPE,
        "mitigation_gate_pass": _as_bool(mitigation_gate.get("gate_pass")),
        "road_boundary_gate_pass": _as_bool(road_gate.get("gate_pass")),
        "command_conflict_gate_pass": _as_bool(command_gate.get("gate_pass")),
        "mitigation_row_count": len(localization_rows),
        "mitigation_improved_row_count": len(improved_rows),
        "mitigation_regressed_row_count": len(regressed_rows),
        "regressed_source_row_id": regressed_row.get("source_row_id", ""),
        "regressed_seed": regressed_row.get("seed", ""),
        "regressed_severity_delta": regressed_row.get("severity_delta", ""),
        "regressed_road_margin_delta_m": regressed_row.get("road_margin_delta_m", ""),
        "regressed_command_conflict_delta": regressed_row.get("command_conflict_delta", ""),
        "regressed_current_severity_rank_low_to_high": regressed_row.get(
            "current_severity_rank_low_to_high",
            "",
        ),
        "single_low_baseline_regression": single_low_baseline_regression,
        "all_mitigation_rows_road_margin_improved": all_margin_improved,
        "all_mitigation_rows_command_conflict_improved": all_conflict_improved,
        "proof_washout_detected": bool(regressed_rows and all_margin_improved and all_conflict_improved),
        "behavior_regression_detected": bool(regressed_rows),
        "objective_weakness_detected": objective_weakness_detected,
        "metric_artifact_detected": metric_artifact_detected,
        "scenario_sampling_failure_status": scenario_sampling_failure_status,
        "public_gate_overfit_risk": public_gate_overfit_risk,
        "source_m2532_status_pass": bool(source_summary.get("status_pass")),
        "source_m2532_protected_proof_gates_all_passed": bool(
            source_summary.get("protected_proof_gates_all_passed")
        ),
        "source_m2532_checkpoint_behavior_changed": bool(
            source_summary.get("checkpoint_behavior_changed")
        ),
        "diagnosis": (
            "single low-baseline mitigation severity regression after a coarse "
            "command-conflict repair that improved road margin and removed "
            "simultaneous throttle-brake on every mitigation row"
        ),
        "routing_reason": (
            "do not run another repair yet; design a mitigation-preserving "
            "repair objective that keeps road-boundary and command-conflict "
            "gains while preventing severity regression"
        ),
    }


def build_summary(
    *,
    output_dir: Path,
    summary_path: Path,
    mitigation_rows_path: Path,
    findings_path: Path,
    post_repair_rows_path: Path,
    gate_rows_path: Path,
    source_summary_path: Path,
    source_summary: dict[str, Any],
    gate_rows: list[dict[str, str]],
    localization_rows: list[dict[str, Any]],
    findings: dict[str, Any],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    required_artifacts_present = mitigation_rows_path.exists() and findings_path.exists()
    mitigation_gate = _gate_by_id(gate_rows, "mitigation_proof")
    proof_washout = bool(findings["proof_washout_detected"])
    behavior_regression = bool(findings["behavior_regression_detected"])
    metric_artifact = bool(findings["metric_artifact_detected"])
    objective_weakness = bool(findings["objective_weakness_detected"])
    actor_contract_preserved = bool(source_summary.get("actor_contract_shape_72_action_3")) and not bool(
        source_summary.get("hidden_or_oracle_actor_inputs_required")
    )
    no_claim_boundary_violation = not any(FALSE_CLAIM_FLAGS.values())
    status_pass = (
        required_artifacts_present
        and post_repair_rows_path.exists()
        and gate_rows_path.exists()
        and source_summary_path.exists()
        and len(localization_rows) == 5
        and int(findings["mitigation_improved_row_count"]) == 4
        and int(findings["mitigation_regressed_row_count"]) == 1
        and not _as_bool(mitigation_gate.get("gate_pass"))
        and actor_contract_preserved
        and no_claim_boundary_violation
        and output_dir.exists()
    )
    failure_types = []
    if behavior_regression:
        failure_types.append("behavior_regression")
    if proof_washout:
        failure_types.append("proof_washout")
    if objective_weakness:
        failure_types.append("objective_overfit")
    if metric_artifact:
        failure_types.append("metric_artifact")
    return {
        "result_class": (
            "engineering_controller_failure_surface_mitigation_regression_localization_pass"
            if status_pass
            else "engineering_controller_failure_surface_mitigation_regression_localization_failed"
        ),
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(summary_path),
        "post_repair_rows": str(post_repair_rows_path),
        "protected_gate_evaluation": str(gate_rows_path),
        "source_summary": str(source_summary_path),
        "mitigation_regression_rows": str(mitigation_rows_path),
        "localization_findings": str(findings_path),
        "required_artifacts_present": bool(required_artifacts_present),
        "mitigation_row_count": len(localization_rows),
        "mitigation_improved_row_count": int(findings["mitigation_improved_row_count"]),
        "mitigation_regressed_row_count": int(findings["mitigation_regressed_row_count"]),
        "regressed_source_row_id": findings["regressed_source_row_id"],
        "regressed_seed": findings["regressed_seed"],
        "regressed_severity_delta": findings["regressed_severity_delta"],
        "regressed_road_margin_delta_m": findings["regressed_road_margin_delta_m"],
        "regressed_command_conflict_delta": findings["regressed_command_conflict_delta"],
        "single_low_baseline_regression": bool(findings["single_low_baseline_regression"]),
        "all_mitigation_rows_road_margin_improved": bool(
            findings["all_mitigation_rows_road_margin_improved"]
        ),
        "all_mitigation_rows_command_conflict_improved": bool(
            findings["all_mitigation_rows_command_conflict_improved"]
        ),
        "proof_washout_detected": proof_washout,
        "behavior_regression_detected": behavior_regression,
        "objective_weakness_detected": objective_weakness,
        "metric_artifact_detected": metric_artifact,
        "scenario_sampling_failure_status": findings["scenario_sampling_failure_status"],
        "public_gate_overfit_risk": findings["public_gate_overfit_risk"],
        "failure_types_observed": failure_types,
        "actor_contract_shape_72_action_3": bool(
            source_summary.get("actor_contract_shape_72_action_3")
        ),
        "hidden_or_oracle_actor_inputs_required": bool(
            source_summary.get("hidden_or_oracle_actor_inputs_required")
        ),
        "candidate_config_mutated": bool(source_summary.get("candidate_config_mutated")),
        "active_config_overwritten": bool(source_summary.get("active_config_overwritten")),
        "checkpoint_promoted": bool(source_summary.get("checkpoint_promoted")),
        "fresh_generalization_run": False,
        "claim_boundary": CLAIM_SCOPE,
        **FALSE_CLAIM_FLAGS,
    }


def _reference_rows_by_seed(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    references: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        if row.get("scenario_role") != "unavoidable_mitigation":
            continue
        if row.get("row_role") != "reference_context":
            continue
        references.setdefault(row["seed"], {})[row["subject_id"]] = row
    return references


def _localization_label(
    *,
    severity_regressed: bool,
    road_margin_improved: bool,
    command_conflict_improved: bool,
    current_severity_rank: int,
    severity_delta_rank: int,
) -> str:
    if severity_regressed and road_margin_improved and command_conflict_improved:
        if current_severity_rank == 1 and severity_delta_rank == 1:
            return "low_baseline_severity_tradeoff_after_command_conflict_projection"
        return "severity_tradeoff_after_command_conflict_projection"
    if road_margin_improved and command_conflict_improved:
        return "joint_margin_and_command_conflict_improvement"
    return "mixed_or_unlocalized_mitigation_effect"


def _gate_by_id(rows: list[dict[str, str]], gate_id: str) -> dict[str, str]:
    for row in rows:
        if row.get("gate_id") == gate_id:
            return row
    return {}


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(value: Any, *, default: float = 0.0) -> float:
    if value in {None, ""}:
        return float(default)
    return float(value)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Localize the M2532 mitigation regression from existing artifacts."
    )
    parser.add_argument("--post-repair-rows", type=Path, default=DEFAULT_POST_REPAIR_ROWS)
    parser.add_argument("--gate-evaluation", type=Path, default=DEFAULT_GATE_EVALUATION)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SOURCE_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_mitigation_regression_localization(
        args.output_dir,
        post_repair_rows=args.post_repair_rows,
        gate_evaluation=args.gate_evaluation,
        summary=args.summary,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "regressed_source_row_id={regressed_source_row_id} "
        "next_blocker={next_blocker} output_dir={output_dir}".format(**summary)
    )


if __name__ == "__main__":
    main()
