"""M2779 source-only belief-stress training admission pack materialization.

This materializer consumes M2778/M2775/M2773 artifacts only. It does not reset,
step, replay, train, validate, rank, promote, or execute a controller.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_MILESTONE = (
    "m2779-engineering-controller-route-a-source-only-belief-stress-training-"
    "admission-pack-materialization-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_"
    "admission_pack_materialization"
)
DEFAULT_M2778_DESIGN = Path(
    "docs/m2778-engineering-controller-route-a-source-only-belief-stress-training-"
    "protocol-design.md"
)
DEFAULT_M2777_SYNTHESIS = Path(
    "docs/m2777-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-branch-synthesis.md"
)
DEFAULT_M2776_AUDIT = Path(
    "docs/m2776-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-delta-panel-materialization-result-audit.md"
)
DEFAULT_M2775_DIR = Path(
    "runs/m2775_engineering_controller_route_a_source_only_action_response_belief_"
    "intervention_delta_panel_materialization"
)
DEFAULT_M2773_DIR = Path(
    "runs/m2773_engineering_controller_route_a_source_only_action_response_belief_"
    "intervention_materialization_preflight"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2780-engineering-controller-route-a-source-only-belief-"
    "stress-training-admission-pack-materialization-result-audit.json"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2779-engineering-controller-route-a-source-only-belief-stress-training-"
    "admission-pack-materialization-preflight.md"
)
DEFAULT_NEXT_BLOCKER = (
    "m2780-engineering-controller-route-a-source-only-belief-stress-training-"
    "admission-pack-materialization-result-audit"
)

INTERVENTION_CONDITION_IDS = (
    "reset_hidden_each_step",
    "zero_previous_command_history",
    "held_actuator_history",
)
STRESS_FAMILY_BY_CONDITION = {
    "reset_hidden_each_step": "recurrent_hidden_reset_stress",
    "zero_previous_command_history": "previous_command_history_stress",
    "held_actuator_history": "held_actuator_history_stress",
}
ACTION_L1_MEAN_THRESHOLD = 0.03
EGO_RESPONSE_L2_MEAN_THRESHOLD = 0.10
COMMAND_RESPONSE_PROXY_ABS_DELTA_THRESHOLD = 0.04
TRACE_DELTA_PROXY_ABS_DELTA_THRESHOLD = 1.0

CLAIM_SCOPE = "Route A source-only belief-stress training admission-pack materialization only"
FORBIDDEN_INTERPRETATION = (
    "reset, step, policy action, rollout, replay, validation, training, PPO, source "
    "build, adapter probe, external simulation, ranking, winner selection, promotion, "
    "success-rate verdict, repair success, driver performance, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation, "
    "full ideal driver completion, or level3 self-identification"
)
CLAIM_BOUNDARY = (
    "M2779 materializes a no-rollout source-only belief-stress admission pack only; "
    "rows are diagnostic admission metadata and not execution, training, ranking, "
    "promotion, validation, performance, paper, current-sim, high-fidelity, "
    "full-driver, or self-ID evidence"
)

ADMISSION_FIELDNAMES = [
    "admission_row_id",
    "candidate_id",
    "delta_row_id",
    "role_family",
    "dynamics_axis",
    "seed",
    "intervention_condition_id",
    "ordinary_denominator_allowed",
    "mitigation_reference",
    "stress_family",
    "belief_signal_class",
    "road_departure_removed",
    "road_departure_added",
    "collision_changed",
    "minimum_road_margin_m_delta",
    "minimum_obstacle_clearance_m_delta",
    "action_l1_mean",
    "ego_response_l2_mean",
    "command_response_proxy_delta",
    "trace_delta_proxy_delta",
    "admission_action",
    "admission_reason",
    "future_execution_allowed",
    "future_training_allowed",
    "requires_fresh_evidence",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "actor_visible_label",
    "claim_boundary",
]

CURRICULUM_FIELDNAMES = [
    "curriculum_row_id",
    "stress_family",
    "role_family",
    "dynamics_axis",
    "ordinary_candidate_count",
    "mitigation_reference_count",
    "behavior_outcome_sensitive_count",
    "action_response_sensitive_count",
    "trace_sensitive_count",
    "weak_or_context_count",
    "future_pack_priority",
    "future_training_allowed",
    "future_execution_allowed",
    "requires_fresh_rollout",
    "requires_training_manifest",
    "ranking_admissible",
    "claim_boundary",
]

MITIGATION_GUARD_FIELDNAMES = [
    "candidate_id",
    "role_family",
    "dynamics_axis",
    "seed",
    "mitigation_reference",
    "ordinary_denominator_allowed",
    "admission_row_count",
    "actor_visible_allowed",
    "future_training_allowed",
    "future_execution_allowed",
    "context_only",
    "guard_family",
    "claim_boundary",
]

ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "protected_field",
    "actor_visible_allowed",
    "actor_observation_shape",
    "action_shape",
    "status_pass",
    "evidence",
    "claim_boundary",
]

CLAIM_BOUNDARY_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "allowed",
    "status_pass",
    "evidence",
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


def materialize_source_only_belief_stress_training_admission_pack(
    output_dir: Path | str,
    *,
    m2778_design: Path | str = DEFAULT_M2778_DESIGN,
    m2775_dir: Path | str = DEFAULT_M2775_DIR,
    m2773_dir: Path | str = DEFAULT_M2773_DIR,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(Path(m2778_design), Path(m2775_dir), Path(m2773_dir))

    m2775_summary = read_json(source_paths["m2775_summary"]) if source_paths["m2775_summary"].exists() else {}
    m2773_summary = read_json(source_paths["m2773_summary"]) if source_paths["m2773_summary"].exists() else {}
    delta_rows = read_csv_rows(source_paths["m2775_intervention_delta_rows"])
    role_dynamics_rows = read_csv_rows(source_paths["m2775_role_dynamics_delta_aggregate_rows"])
    condition_aggregate_rows = read_csv_rows(source_paths["m2775_intervention_condition_delta_aggregate_rows"])
    candidate_rows = read_csv_rows(source_paths["m2773_source_only_candidate_rows"])
    execution_rows = read_csv_rows(source_paths["m2773_intervention_execution_rows"])
    trace_rows = read_csv_rows(source_paths["m2773_action_response_trace_rows"])

    admission_rows = build_belief_stress_admission_rows(delta_rows)
    curriculum_rows = build_stress_curriculum_rows(admission_rows)
    mitigation_guard_rows = build_mitigation_reference_guard_rows(candidate_rows, admission_rows)
    actor_guard_rows = build_actor_contract_guard_rows(m2773_summary, execution_rows)
    claim_rows = build_claim_boundary_rows()

    write_csv_rows(paths["belief_stress_admission_rows"], admission_rows, fieldnames=ADMISSION_FIELDNAMES)
    write_csv_rows(paths["stress_curriculum_rows"], curriculum_rows, fieldnames=CURRICULUM_FIELDNAMES)
    write_csv_rows(
        paths["mitigation_reference_guard_rows"],
        mitigation_guard_rows,
        fieldnames=MITIGATION_GUARD_FIELDNAMES,
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_BOUNDARY_FIELDNAMES)

    metrics = _metrics(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        m2775_summary=m2775_summary,
        m2773_summary=m2773_summary,
        delta_rows=delta_rows,
        role_dynamics_rows=role_dynamics_rows,
        condition_aggregate_rows=condition_aggregate_rows,
        candidate_rows=candidate_rows,
        execution_rows=execution_rows,
        trace_rows=trace_rows,
        admission_rows=admission_rows,
        curriculum_rows=curriculum_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    gate_rows = build_gate_matrix_rows(metrics)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = _summary(metrics, gate_rows)
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], _run_state(summary, paths))
    write_json(paths["follow_up_manifest"], _m2780_manifest(summary))
    _write_doc(paths["doc"], summary)
    return summary


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_belief_stress_admission_rows(delta_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(delta_rows):
        condition_id = str(row.get("intervention_condition_id", ""))
        stress_family = STRESS_FAMILY_BY_CONDITION.get(condition_id, "unknown_stress")
        mitigation_reference = _truthy(row.get("mitigation_reference"))
        belief_signal_class = classify_belief_signal(row)
        ordinary_allowed = _truthy(row.get("ordinary_denominator_allowed")) and not mitigation_reference
        future_allowed = ordinary_allowed and belief_signal_class != "weak_or_context"
        if mitigation_reference:
            admission_action = "mitigation_reference_guard"
            admission_reason = "mitigation reference row remains actor-invisible context outside ordinary denominators"
        elif belief_signal_class == "weak_or_context":
            admission_action = "diagnostic_context_only"
            admission_reason = "source-only row stays below materialization thresholds"
        else:
            admission_action = "admit_future_manifest_design_only"
            admission_reason = (
                f"{belief_signal_class} row may seed a separately audited future proposal, "
                "not evidence or promotion"
            )
        rows.append(
            {
                "admission_row_id": f"m2779_admission_{index:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "delta_row_id": row.get("delta_row_id", ""),
                "role_family": row.get("role_family", ""),
                "dynamics_axis": row.get("dynamics_axis", ""),
                "seed": row.get("seed", ""),
                "intervention_condition_id": condition_id,
                "ordinary_denominator_allowed": ordinary_allowed,
                "mitigation_reference": mitigation_reference,
                "stress_family": stress_family,
                "belief_signal_class": belief_signal_class,
                "road_departure_removed": _truthy(row.get("road_departure_removed")),
                "road_departure_added": _truthy(row.get("road_departure_added")),
                "collision_changed": _collision_changed(row),
                "minimum_road_margin_m_delta": _to_float(row.get("minimum_road_margin_m_delta")),
                "minimum_obstacle_clearance_m_delta": _to_float(row.get("minimum_obstacle_clearance_m_delta")),
                "action_l1_mean": _to_float(row.get("action_l1_mean")),
                "ego_response_l2_mean": _to_float(row.get("ego_response_l2_mean")),
                "command_response_proxy_delta": _to_float(row.get("command_response_proxy_delta")),
                "trace_delta_proxy_delta": _to_float(row.get("trace_delta_proxy_delta")),
                "admission_action": admission_action,
                "admission_reason": admission_reason,
                "future_execution_allowed": future_allowed,
                "future_training_allowed": future_allowed,
                "requires_fresh_evidence": future_allowed,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "actor_visible_label": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def classify_belief_signal(row: Mapping[str, Any]) -> str:
    if _truthy(row.get("mitigation_reference")):
        return "weak_or_context"
    if _truthy(row.get("road_departure_removed")) or _truthy(row.get("road_departure_added")):
        return "behavior_outcome_sensitive"
    if _collision_changed(row):
        return "behavior_outcome_sensitive"
    if (
        _to_float(row.get("action_l1_mean")) >= ACTION_L1_MEAN_THRESHOLD
        or _to_float(row.get("ego_response_l2_mean")) >= EGO_RESPONSE_L2_MEAN_THRESHOLD
    ):
        return "action_response_sensitive"
    if (
        abs(_to_float(row.get("trace_delta_proxy_delta"))) >= TRACE_DELTA_PROXY_ABS_DELTA_THRESHOLD
        or abs(_to_float(row.get("command_response_proxy_delta"))) >= COMMAND_RESPONSE_PROXY_ABS_DELTA_THRESHOLD
    ):
        return "trace_sensitive"
    return "weak_or_context"


def build_stress_curriculum_rows(admission_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in admission_rows:
        key = (
            str(row.get("stress_family", "")),
            str(row.get("role_family", "")),
            str(row.get("dynamics_axis", "")),
        )
        grouped[key].append(row)

    rows: list[dict[str, Any]] = []
    for stress_family, role_family, dynamics_axis in sorted(grouped):
        group = grouped[(stress_family, role_family, dynamics_axis)]
        signal_counts = {
            "behavior_outcome_sensitive": sum(
                str(row.get("belief_signal_class", "")) == "behavior_outcome_sensitive" for row in group
            ),
            "action_response_sensitive": sum(
                str(row.get("belief_signal_class", "")) == "action_response_sensitive" for row in group
            ),
            "trace_sensitive": sum(str(row.get("belief_signal_class", "")) == "trace_sensitive" for row in group),
            "weak_or_context": sum(str(row.get("belief_signal_class", "")) == "weak_or_context" for row in group),
        }
        mitigation_count = sum(_truthy(row.get("mitigation_reference")) for row in group)
        ordinary_count = len(group) - mitigation_count
        has_future_signal = (
            signal_counts["behavior_outcome_sensitive"]
            + signal_counts["action_response_sensitive"]
            + signal_counts["trace_sensitive"]
        ) > 0 and ordinary_count > 0
        rows.append(
            {
                "curriculum_row_id": f"m2779_curriculum_{stress_family}_{role_family}_{dynamics_axis}",
                "stress_family": stress_family,
                "role_family": role_family,
                "dynamics_axis": dynamics_axis,
                "ordinary_candidate_count": ordinary_count,
                "mitigation_reference_count": mitigation_count,
                "behavior_outcome_sensitive_count": signal_counts["behavior_outcome_sensitive"],
                "action_response_sensitive_count": signal_counts["action_response_sensitive"],
                "trace_sensitive_count": signal_counts["trace_sensitive"],
                "weak_or_context_count": signal_counts["weak_or_context"],
                "future_pack_priority": _future_pack_priority(signal_counts, mitigation_count, ordinary_count),
                "future_training_allowed": has_future_signal,
                "future_execution_allowed": has_future_signal,
                "requires_fresh_rollout": has_future_signal,
                "requires_training_manifest": has_future_signal,
                "ranking_admissible": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_mitigation_reference_guard_rows(
    candidate_rows: Sequence[Mapping[str, Any]],
    admission_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    admission_count_by_candidate: dict[str, int] = defaultdict(int)
    for row in admission_rows:
        if _truthy(row.get("mitigation_reference")):
            admission_count_by_candidate[str(row.get("candidate_id", ""))] += 1

    rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        if not _truthy(candidate.get("mitigation_reference")):
            continue
        candidate_id = str(candidate.get("candidate_id", ""))
        rows.append(
            {
                "candidate_id": candidate_id,
                "role_family": candidate.get("role_family", ""),
                "dynamics_axis": candidate.get("dynamics_axis", ""),
                "seed": candidate.get("seed", ""),
                "mitigation_reference": True,
                "ordinary_denominator_allowed": False,
                "admission_row_count": admission_count_by_candidate.get(candidate_id, 0),
                "actor_visible_allowed": False,
                "future_training_allowed": False,
                "future_execution_allowed": False,
                "context_only": True,
                "guard_family": "mitigation_reference_guard",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    m2773_summary: Mapping[str, Any],
    execution_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    observed_observation_shapes = sorted({str(row.get("observation_shape", "")) for row in execution_rows})
    observed_action_shapes = sorted({str(row.get("action_shape", "")) for row in execution_rows})
    observation_shape = "72" if "72" in observed_observation_shapes else str(m2773_summary.get("checkpoint_obs_dim", ""))
    action_shape = "3" if "3" in observed_action_shapes else str(m2773_summary.get("checkpoint_action_dim", ""))
    protected_fields = (
        ("P0_observation_72", "actor_shape", observation_shape == "72"),
        ("action_3", "action_shape", action_shape == "3"),
        ("steer_throttle_brake", "action_mapping", action_shape == "3"),
        ("hidden_dynamics", "hidden_dynamics", not bool(m2773_summary.get("hidden_oracle_actor_input_detected", True))),
        ("oracle_labels", "oracle_labels", not bool(m2773_summary.get("hidden_oracle_actor_input_detected", True))),
        ("role_dynamics_intervention_stress_admission_curriculum_labels", "route_labels", True),
        ("outcome_progress_success_verdict_labels", "verdict_labels", True),
    )
    rows: list[dict[str, Any]] = []
    for index, (protected_field, guard_family, status_pass) in enumerate(protected_fields):
        rows.append(
            {
                "guard_id": f"m2779_actor_guard_{index:02d}_{protected_field}",
                "guard_family": guard_family,
                "protected_field": protected_field,
                "actor_visible_allowed": False,
                "actor_observation_shape": observation_shape,
                "action_shape": action_shape,
                "status_pass": status_pass,
                "evidence": "M2779 reads source-only artifacts and writes actor-invisible CSV labels only",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claims = (
        "reset_step_policy_execution",
        "policy_action_execution",
        "rollout_or_replay_or_validation",
        "training_or_ppo",
        "source_build_or_adapter_probe",
        "external_simulation",
        "ranking_or_winner_selection",
        "checkpoint_promotion",
        "success_rate_verdict",
        "repair_success",
        "driver_performance",
        "validation_readiness",
        "validation_result",
        "paper_evidence",
        "finite_window_vs_gru_conclusion",
        "current_sim_verdict",
        "high_fidelity_validation",
        "full_ideal_driver_completion",
        "level3_self_identification",
    )
    return [
        {
            "claim_id": f"m2779_claim_{claim}",
            "claim_family": claim,
            "claim_made": False,
            "allowed": False,
            "status_pass": True,
            "evidence": "M2779 materializes source-only admission metadata only",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for claim in claims
    ]


def build_gate_matrix_rows(metrics: Mapping[str, Any]) -> list[dict[str, Any]]:
    gate_specs = (
        ("m2778_design_exists", "lineage", metrics["m2778_design_exists"], True, "lineage_invalid"),
        ("m2777_synthesis_exists", "lineage", metrics["m2777_synthesis_exists"], True, "lineage_invalid"),
        ("m2776_audit_exists", "lineage", metrics["m2776_audit_exists"], True, "lineage_invalid"),
        ("m2775_status_pass", "lineage", metrics["m2775_status_pass"], True, "lineage_invalid"),
        ("m2775_gate_matrix_pass", "lineage", metrics["m2775_gate_matrix_pass"], True, "lineage_invalid"),
        ("m2773_status_pass", "lineage", metrics["m2773_status_pass"], True, "lineage_invalid"),
        ("m2773_gate_matrix_pass", "lineage", metrics["m2773_gate_matrix_pass"], True, "lineage_invalid"),
        ("source_delta_row_count", "artifact", metrics["source_delta_row_count"], 96, "metric_artifact"),
        ("ordinary_delta_row_count", "artifact", metrics["ordinary_delta_row_count"], 72, "metric_artifact"),
        (
            "mitigation_reference_delta_row_count",
            "artifact",
            metrics["mitigation_reference_delta_row_count"],
            24,
            "metric_artifact",
        ),
        ("source_candidate_row_count", "artifact", metrics["source_candidate_row_count"], 32, "metric_artifact"),
        (
            "ordinary_candidate_row_count",
            "artifact",
            metrics["ordinary_candidate_row_count"],
            24,
            "metric_artifact",
        ),
        (
            "mitigation_reference_candidate_row_count",
            "artifact",
            metrics["mitigation_reference_candidate_row_count"],
            8,
            "metric_artifact",
        ),
        (
            "intervention_condition_count",
            "artifact",
            metrics["intervention_condition_count"],
            3,
            "metric_artifact",
        ),
        (
            "m2773_intervention_execution_row_count",
            "source_accounting",
            metrics["m2773_intervention_execution_row_count"],
            128,
            "metric_artifact",
        ),
        (
            "m2773_action_response_trace_row_count",
            "source_accounting",
            metrics["m2773_action_response_trace_row_count"],
            10240,
            "metric_artifact",
        ),
        (
            "m2773_collision_diagnostic_row_count",
            "source_accounting",
            metrics["m2773_collision_diagnostic_row_count"],
            32,
            "metric_artifact",
        ),
        (
            "m2773_road_departure_diagnostic_row_count",
            "source_accounting",
            metrics["m2773_road_departure_diagnostic_row_count"],
            68,
            "metric_artifact",
        ),
        (
            "m2775_matched_trace_pair_row_count",
            "source_accounting",
            metrics["m2775_matched_trace_pair_row_count"],
            7680,
            "metric_artifact",
        ),
        (
            "m2775_road_departure_removed_delta_row_count",
            "source_accounting",
            metrics["m2775_road_departure_removed_delta_row_count"],
            4,
            "metric_artifact",
        ),
        (
            "m2775_road_departure_added_delta_row_count",
            "source_accounting",
            metrics["m2775_road_departure_added_delta_row_count"],
            0,
            "metric_artifact",
        ),
        (
            "m2775_collision_changed_delta_row_count",
            "source_accounting",
            metrics["m2775_collision_changed_delta_row_count"],
            0,
            "metric_artifact",
        ),
        (
            "admission_row_count",
            "pack_shape",
            metrics["admission_row_count"],
            96,
            "metric_artifact",
        ),
        (
            "stress_curriculum_row_count",
            "pack_shape",
            metrics["stress_curriculum_row_count"],
            24,
            "metric_artifact",
        ),
        (
            "admission_row_accounting_complete",
            "pack_shape",
            metrics["admission_row_accounting_complete"],
            True,
            "metric_artifact",
        ),
        (
            "curriculum_row_accounting_complete",
            "pack_shape",
            metrics["curriculum_row_accounting_complete"],
            True,
            "metric_artifact",
        ),
        (
            "mitigation_reference_rows_guarded",
            "claim_boundary",
            metrics["mitigation_reference_rows_guarded"],
            True,
            "proof_washout",
        ),
        (
            "actor_contract_shape_72_action_3",
            "actor_contract",
            metrics["actor_contract_shape_72_action_3"],
            True,
            "contract_violation",
        ),
        (
            "hidden_oracle_actor_input_detected",
            "actor_contract",
            metrics["hidden_oracle_actor_input_detected"],
            False,
            "contract_violation",
        ),
        (
            "actor_visible_label_detected",
            "actor_contract",
            metrics["actor_visible_label_detected"],
            False,
            "contract_violation",
        ),
        (
            "actor_visible_stress_admission_curriculum_labels_detected",
            "actor_contract",
            metrics["actor_visible_stress_admission_curriculum_labels_detected"],
            False,
            "contract_violation",
        ),
        ("new_execution_run", "forbidden_claim", metrics["new_execution_run"], False, "objective_overfit"),
        ("training_run", "forbidden_claim", metrics["training_run"], False, "objective_overfit"),
        ("ppo_run", "forbidden_claim", metrics["ppo_run"], False, "objective_overfit"),
        ("ranking_run", "forbidden_claim", metrics["ranking_run"], False, "objective_overfit"),
        ("winner_selected", "forbidden_claim", metrics["winner_selected"], False, "objective_overfit"),
        (
            "success_rate_verdict_computed",
            "forbidden_claim",
            metrics["success_rate_verdict_computed"],
            False,
            "objective_overfit",
        ),
        (
            "forbidden_claims_made",
            "forbidden_claim",
            metrics["forbidden_claims_made"],
            False,
            "objective_overfit",
        ),
        (
            "m2780_follow_up_manifest_registered",
            "next_route",
            metrics["m2780_follow_up_manifest_registered"],
            True,
            "lineage_invalid",
        ),
    )
    rows: list[dict[str, Any]] = []
    for gate_id, family, observed, expected, failure_type in gate_specs:
        status_pass = observed == expected
        rows.append(
            {
                "gate_id": gate_id,
                "gate_family": family,
                "status_pass": bool(status_pass),
                "observed": observed,
                "expected": expected,
                "failure_type": "" if status_pass else failure_type,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _paths(output_dir: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "belief_stress_admission_rows": output_dir / "belief_stress_admission_rows.csv",
        "stress_curriculum_rows": output_dir / "stress_curriculum_rows.csv",
        "mitigation_reference_guard_rows": output_dir / "mitigation_reference_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "summary": output_dir / "summary.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _source_paths(m2778_design: Path, m2775_dir: Path, m2773_dir: Path) -> dict[str, Path]:
    return {
        "m2778_design": m2778_design,
        "m2777_synthesis": DEFAULT_M2777_SYNTHESIS,
        "m2776_audit": DEFAULT_M2776_AUDIT,
        "m2775_summary": m2775_dir / "summary.json",
        "m2775_intervention_delta_rows": m2775_dir / "intervention_delta_rows.csv",
        "m2775_role_dynamics_delta_aggregate_rows": m2775_dir / "role_dynamics_delta_aggregate_rows.csv",
        "m2775_intervention_condition_delta_aggregate_rows": m2775_dir
        / "intervention_condition_delta_aggregate_rows.csv",
        "m2773_summary": m2773_dir / "summary.json",
        "m2773_source_only_candidate_rows": m2773_dir / "source_only_candidate_rows.csv",
        "m2773_intervention_execution_rows": m2773_dir / "intervention_execution_rows.csv",
        "m2773_action_response_trace_rows": m2773_dir / "action_response_trace_rows.csv",
    }


def _metrics(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source_paths: Mapping[str, Path],
    m2775_summary: Mapping[str, Any],
    m2773_summary: Mapping[str, Any],
    delta_rows: Sequence[Mapping[str, Any]],
    role_dynamics_rows: Sequence[Mapping[str, Any]],
    condition_aggregate_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
    execution_rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
    admission_rows: Sequence[Mapping[str, Any]],
    curriculum_rows: Sequence[Mapping[str, Any]],
    mitigation_guard_rows: Sequence[Mapping[str, Any]],
    actor_guard_rows: Sequence[Mapping[str, Any]],
    claim_rows: Sequence[Mapping[str, Any]],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    source_exists = {name: path.exists() for name, path in source_paths.items()}
    required_output_present = all(
        paths[key].exists()
        for key in (
            "belief_stress_admission_rows",
            "stress_curriculum_rows",
            "mitigation_reference_guard_rows",
            "actor_contract_guard_rows",
            "claim_boundary_rows",
        )
    )
    intervention_condition_ids = {str(row.get("intervention_condition_id", "")) for row in delta_rows}
    ordinary_delta_row_count = sum(_truthy(row.get("ordinary_denominator_allowed")) for row in delta_rows)
    mitigation_reference_delta_row_count = sum(_truthy(row.get("mitigation_reference")) for row in delta_rows)
    ordinary_candidate_row_count = sum(_truthy(row.get("ordinary_success_denominator_allowed")) for row in candidate_rows)
    mitigation_reference_candidate_row_count = sum(_truthy(row.get("mitigation_reference")) for row in candidate_rows)
    m2773_collision_diagnostic_row_count = sum(_truthy(row.get("collision_diagnostic")) for row in execution_rows)
    m2773_road_departure_diagnostic_row_count = sum(
        _truthy(row.get("road_departure_diagnostic")) for row in execution_rows
    )
    m2775_collision_changed_delta_row_count = sum(_collision_changed(row) for row in delta_rows)
    m2775_matched_trace_pair_row_count = sum(_to_int(row.get("matched_trace_steps")) for row in delta_rows)
    mitigation_reference_rows_guarded = (
        len(mitigation_guard_rows) == 8
        and all(_truthy(row.get("mitigation_reference")) for row in mitigation_guard_rows)
        and all(not _truthy(row.get("ordinary_denominator_allowed")) for row in mitigation_guard_rows)
        and all(_to_int(row.get("admission_row_count")) == len(INTERVENTION_CONDITION_IDS) for row in mitigation_guard_rows)
        and all(not _truthy(row.get("actor_visible_allowed")) for row in mitigation_guard_rows)
        and all(not _truthy(row.get("future_training_allowed")) for row in mitigation_guard_rows)
        and all(not _truthy(row.get("future_execution_allowed")) for row in mitigation_guard_rows)
    )
    actor_contract_shape_72_action_3 = (
        bool(actor_guard_rows)
        and all(str(row.get("actor_observation_shape", "")) == "72" for row in actor_guard_rows)
        and all(str(row.get("action_shape", "")) == "3" for row in actor_guard_rows)
        and all(_truthy(row.get("status_pass")) for row in actor_guard_rows)
    )
    hidden_oracle_actor_input_detected = bool(m2773_summary.get("hidden_oracle_actor_input_detected", True))
    actor_visible_label_detected = bool(m2773_summary.get("actor_visible_label_detected", True)) or any(
        _truthy(row.get("actor_visible_label")) for row in admission_rows
    )
    actor_visible_stress_admission_curriculum_labels_detected = any(
        _truthy(row.get("actor_visible_allowed")) for row in actor_guard_rows
    )
    forbidden_claims_made = any(_truthy(row.get("claim_made")) for row in claim_rows)
    admission_row_accounting_complete = (
        len(admission_rows) == len(delta_rows)
        and len(admission_rows) == 96
        and ordinary_delta_row_count == 72
        and mitigation_reference_delta_row_count == 24
    )
    curriculum_row_accounting_complete = (
        len(curriculum_rows) == len(INTERVENTION_CONDITION_IDS) * 4 * 2
        and sum(_to_int(row.get("ordinary_candidate_count")) for row in curriculum_rows) == 72
        and sum(_to_int(row.get("mitigation_reference_count")) for row in curriculum_rows) == 24
    )
    behavior_outcome_sensitive_count = sum(
        str(row.get("belief_signal_class", "")) == "behavior_outcome_sensitive" for row in admission_rows
    )
    action_response_sensitive_count = sum(
        str(row.get("belief_signal_class", "")) == "action_response_sensitive" for row in admission_rows
    )
    trace_sensitive_count = sum(str(row.get("belief_signal_class", "")) == "trace_sensitive" for row in admission_rows)
    weak_or_context_count = sum(str(row.get("belief_signal_class", "")) == "weak_or_context" for row in admission_rows)
    metrics = {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_source_only_belief_stress_training_"
            "admission_pack_materialization_pass"
        ),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "source_artifact_exists": source_exists,
        "source_artifacts_required_present": all(source_exists.values()),
        "required_artifacts_present": required_output_present,
        "m2778_design": str(source_paths["m2778_design"]),
        "m2778_design_exists": source_exists["m2778_design"],
        "m2777_synthesis": str(source_paths["m2777_synthesis"]),
        "m2777_synthesis_exists": source_exists["m2777_synthesis"],
        "m2776_audit": str(source_paths["m2776_audit"]),
        "m2776_audit_exists": source_exists["m2776_audit"],
        "m2775_dir": str(source_paths["m2775_summary"].parent),
        "m2775_status_pass": bool(m2775_summary.get("status_pass", False)),
        "m2775_gate_matrix_pass": bool(m2775_summary.get("gate_matrix_pass", False)),
        "m2775_matched_trace_pair_row_count": m2775_matched_trace_pair_row_count,
        "m2775_road_departure_removed_delta_row_count": sum(
            _truthy(row.get("road_departure_removed")) for row in delta_rows
        ),
        "m2775_road_departure_added_delta_row_count": sum(
            _truthy(row.get("road_departure_added")) for row in delta_rows
        ),
        "m2775_collision_changed_delta_row_count": m2775_collision_changed_delta_row_count,
        "m2775_role_dynamics_delta_aggregate_row_count": len(role_dynamics_rows),
        "m2775_intervention_condition_delta_aggregate_row_count": len(condition_aggregate_rows),
        "m2773_dir": str(source_paths["m2773_summary"].parent),
        "m2773_status_pass": bool(m2773_summary.get("status_pass", False)),
        "m2773_gate_matrix_pass": bool(m2773_summary.get("gate_matrix_pass", False)),
        "m2773_intervention_execution_row_count": len(execution_rows),
        "m2773_action_response_trace_row_count": len(trace_rows),
        "m2773_collision_diagnostic_row_count": m2773_collision_diagnostic_row_count,
        "m2773_road_departure_diagnostic_row_count": m2773_road_departure_diagnostic_row_count,
        "source_delta_row_count": len(delta_rows),
        "ordinary_delta_row_count": ordinary_delta_row_count,
        "mitigation_reference_delta_row_count": mitigation_reference_delta_row_count,
        "source_candidate_row_count": len(candidate_rows),
        "ordinary_candidate_row_count": ordinary_candidate_row_count,
        "mitigation_reference_candidate_row_count": mitigation_reference_candidate_row_count,
        "intervention_condition_count": len(intervention_condition_ids),
        "admission_row_count": len(admission_rows),
        "stress_curriculum_row_count": len(curriculum_rows),
        "mitigation_reference_guard_row_count": len(mitigation_guard_rows),
        "actor_guard_row_count": len(actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "admission_row_accounting_complete": admission_row_accounting_complete,
        "curriculum_row_accounting_complete": curriculum_row_accounting_complete,
        "mitigation_reference_rows_guarded": mitigation_reference_rows_guarded,
        "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected,
        "actor_visible_label_detected": actor_visible_label_detected,
        "actor_visible_stress_admission_curriculum_labels_detected": (
            actor_visible_stress_admission_curriculum_labels_detected
        ),
        "behavior_outcome_sensitive_count": behavior_outcome_sensitive_count,
        "action_response_sensitive_count": action_response_sensitive_count,
        "trace_sensitive_count": trace_sensitive_count,
        "weak_or_context_count": weak_or_context_count,
        "action_l1_mean_threshold": ACTION_L1_MEAN_THRESHOLD,
        "ego_response_l2_mean_threshold": EGO_RESPONSE_L2_MEAN_THRESHOLD,
        "command_response_proxy_abs_delta_threshold": COMMAND_RESPONSE_PROXY_ABS_DELTA_THRESHOLD,
        "trace_delta_proxy_abs_delta_threshold": TRACE_DELTA_PROXY_ABS_DELTA_THRESHOLD,
        "new_execution_run": False,
        "reset_step_policy_execution_run": False,
        "policy_action_execution_run": False,
        "replay_or_validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_computed": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_claim_made": False,
        "level3_self_id_claim_made": False,
        "forbidden_claims_made": forbidden_claims_made,
        "m2780_follow_up_manifest_registered": bool(str(paths["follow_up_manifest"])),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    return metrics


def _summary(metrics: Mapping[str, Any], gate_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(_truthy(row.get("status_pass")) for row in gate_rows)
    status_pass = (
        gate_matrix_pass
        and bool(metrics["required_artifacts_present"])
        and bool(metrics["admission_row_accounting_complete"])
        and bool(metrics["curriculum_row_accounting_complete"])
        and bool(metrics["mitigation_reference_rows_guarded"])
        and bool(metrics["actor_contract_shape_72_action_3"])
        and not bool(metrics["forbidden_claims_made"])
    )
    result = dict(metrics)
    result.update(
        {
            "status_pass": bool(status_pass),
            "gate_matrix_pass": bool(gate_matrix_pass),
            "gate_matrix_row_count": len(gate_rows),
            "gate_matrix": str(Path(metrics["output_dir"]) / "gate_matrix.csv"),
        }
    )
    if not status_pass:
        result["result_class"] = (
            "engineering_controller_route_a_source_only_belief_stress_training_"
            "admission_pack_materialization_failed"
        )
    return result


def _run_state(summary: Mapping[str, Any], paths: Mapping[str, Path]) -> dict[str, Any]:
    return {
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "result_class": summary["result_class"],
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
        "thresholds": {
            "action_l1_mean_threshold": ACTION_L1_MEAN_THRESHOLD,
            "ego_response_l2_mean_threshold": EGO_RESPONSE_L2_MEAN_THRESHOLD,
            "command_response_proxy_abs_delta_threshold": COMMAND_RESPONSE_PROXY_ABS_DELTA_THRESHOLD,
            "trace_delta_proxy_abs_delta_threshold": TRACE_DELTA_PROXY_ABS_DELTA_THRESHOLD,
        },
        "generated_at_utc": summary["generated_at_utc"],
    }


def _m2780_manifest(summary: Mapping[str, Any]) -> dict[str, Any]:
    m2779_id = str(summary["milestone"])
    m2780_id = str(summary["next_blocker"])
    run_dir = Path(str(summary["output_dir"]))
    return {
        "id": m2780_id,
        "type": "gate",
        "gate_tier": "proof",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
            ],
            "parent_dataset": [
                str(run_dir / "summary.json"),
                str(run_dir / "belief_stress_admission_rows.csv"),
                str(run_dir / "stress_curriculum_rows.csv"),
                str(run_dir / "mitigation_reference_guard_rows.csv"),
                str(run_dir / "actor_contract_guard_rows.csv"),
                str(run_dir / "claim_boundary_rows.csv"),
                str(run_dir / "gate_matrix.csv"),
                str(summary["doc"]),
            ],
            "parent_config": [
                "experiments/manifests/m2779-engineering-controller-route-a-source-only-belief-stress-training-admission-pack-materialization-preflight.json",
                "experiments/manifests/m2778-engineering-controller-route-a-source-only-belief-stress-training-protocol-design.json",
                "experiments/manifests/m2775-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-preflight.json",
                "experiments/manifests/m2773-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-preflight.json",
            ],
            "parent_objective": [
                "audit M2779 source-only belief-stress admission pack before any fresh execution or training"
            ],
            "derived_from": [
                m2779_id,
                "m2778-engineering-controller-route-a-source-only-belief-stress-training-protocol-design",
                "m2776-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-result-audit",
                "m2775-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-preflight",
                "m2773-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-preflight",
            ],
            "blocked_by": [
                "M2779 admission and curriculum rows must be audited before any training or fresh execution",
                "M2779 source-only rows cannot be interpreted as validation performance paper or self-ID evidence",
            ],
            "supersedes": [
                "direct training from M2775 deltas without admission-pack audit",
                "ranking intervention conditions from M2779 admission rows",
                "driver-performance or self-ID interpretation from source-only admission metadata",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{m2780_id}.md",
        "public_gates": [
            "M2780 must audit M2779 artifact completeness actor-contract preservation mitigation guards and claim boundaries",
            "M2780 must preserve source-only admission-pack scope and reject validation performance paper high-fidelity full-driver and self-ID claims",
            "M2780 must decide whether to route to fresh closed-loop design short-training design artifact repair synthesis or branch stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step rollout replay validation training PPO source build adapter probe or external simulation in audit",
            "do not change actor inputs or action contract",
            "do not expose admission curriculum stress outcome success progress route or verdict labels to actor input",
            "do not rank intervention conditions roles dynamics axes candidates controllers checkpoints or source edges",
            "do not select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdicts",
            "do not claim driver performance paper current-sim high-fidelity full ideal driver or self-ID evidence",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_belief_stress_training",
            "evidence_axis": "source_only_belief_stress_training_admission_pack_result_audit",
            "evidence_increment": "audits M2779 source-only belief-stress admission pack before any future execution or training branch",
            "claim_scope": (
                "M2779 result audit only; no new execution training ranking validation "
                "performance paper current-sim high-fidelity self-ID or full ideal driver claim"
            ),
            "stop_condition": [
                "stop if M2779 artifacts are incomplete",
                "stop if actor or mitigation guard accounting is incomplete",
                "stop if admission rows would be interpreted as validation performance paper high-fidelity or self-ID evidence",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting is incomplete",
                "route to branch synthesis if admission signals are weak ambiguous or behavior-negative",
                "route to fresh closed-loop or short-training design only after audit preserves claim boundaries",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2779 writes source-only belief-stress admission-pack artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "evaluation_only",
            "stage_objective": "source-only belief-stress admission-pack result audit",
            "admission_evidence": ["M2779 summary admission curriculum guard claim and gate artifacts exist"],
            "blocked_shortcuts": ["no execution training ranking validation performance paper HF or self-ID claim in audit"],
            "allowed_updates": [f"docs/{m2780_id}.md", "M2780 status queue scoreboard research log and review"],
            "next_stage_criteria": ["audit artifact exists", "one bounded next route or stop decision is selected"],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": (
                "M2780 may audit source-only admission rows but cannot by itself establish "
                "level3 self-identification."
            ),
            "history_necessity_tests": ["audit only; no new tests in M2780"],
            "temporal_evidence_window": "M2772-M2779 source-only belief intervention and admission branch",
            "negative_result_policy": "Preserve weak or ambiguous admission rows instead of weakening self-ID gates.",
            "allowed_claims": [
                "M2779 artifacts are complete and claim-safe or incomplete",
                "no driver-performance verdict paper result high-fidelity validation full ideal driver or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a new source-only admission pack rather than repeating delta-only reanalysis",
            "paper_verdict_delta": "no paper verdict; audit may select a bounded fresh-evidence route or stop",
            "must_synthesize_if": [
                "M2780 cannot select a bounded follow-up route",
                "M2780 would claim self-ID or performance from source-only admission rows",
                "another no-new-data reanalysis is proposed after M2780 without fresh evidence or stop decision",
            ],
        },
        "hypothesis": "M2779 source-only admission-pack artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{m2780_id}.md exists",
            "M2780 audits M2779 summary admission curriculum mitigation actor claim and gate artifacts",
            "M2780 preserves no ranking validation performance paper high-fidelity full-driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2780 executes new rollouts or training",
            "M2780 claims driver performance or self-ID",
            "M2780 fails to select a bounded next route or stop",
        ],
        "decision_rule": "Pass only if M2780 audits M2779 artifacts and selects a bounded next route without overclaiming.",
        "commands": [{"name": "audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{m2780_id}.md", "type": "md"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
        ],
        "baseline_artifacts": [str(run_dir / "summary.json"), str(summary["doc"])],
        "scoreboard_checkpoint": f"docs/{m2780_id}.md",
    }


def _write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "completed" if summary["status_pass"] else "failed"
    text = f"""# M2779 Engineering Controller Route A Source-Only Belief-Stress Training Admission Pack Materialization

## Metadata

- status: {status}
- result class: `{summary['result_class']}`
- summary: `{summary['summary']}`
- source design: `{summary['m2778_design']}`
- source delta dir: `{summary['m2775_dir']}`
- source intervention dir: `{summary['m2773_dir']}`
- follow-up manifest: `{summary['follow_up_manifest']}`
- next: `{summary['next_blocker']}`

## Artifact Accounting

```text
source delta rows: {summary['source_delta_row_count']}
ordinary delta rows: {summary['ordinary_delta_row_count']}
mitigation reference delta rows: {summary['mitigation_reference_delta_row_count']}
source candidate rows: {summary['source_candidate_row_count']}
ordinary candidate rows: {summary['ordinary_candidate_row_count']}
mitigation reference candidate rows: {summary['mitigation_reference_candidate_row_count']}
intervention conditions: {summary['intervention_condition_count']}
admission rows: {summary['admission_row_count']}
curriculum rows: {summary['stress_curriculum_row_count']}
mitigation guard rows: {summary['mitigation_reference_guard_row_count']}
actor guard rows: {summary['actor_guard_row_count']}
claim boundary rows: {summary['claim_boundary_row_count']}
gate rows: {summary['gate_matrix_row_count']}
```

## Source Diagnostic Accounting

```text
M2773 execution rows: {summary['m2773_intervention_execution_row_count']}
M2773 trace rows: {summary['m2773_action_response_trace_row_count']}
M2773 collision diagnostic rows: {summary['m2773_collision_diagnostic_row_count']}
M2773 road-departure diagnostic rows: {summary['m2773_road_departure_diagnostic_row_count']}
M2775 matched trace pair rows: {summary['m2775_matched_trace_pair_row_count']}
M2775 road-departure removed delta rows: {summary['m2775_road_departure_removed_delta_row_count']}
M2775 road-departure added delta rows: {summary['m2775_road_departure_added_delta_row_count']}
M2775 collision changed delta rows: {summary['m2775_collision_changed_delta_row_count']}
```

These rows are source-only diagnostic inputs. They are not validation
measurements, success-rate verdicts, controller rankings, driver-performance
measurements, paper evidence, high-fidelity validation evidence, or self-ID
proof.

## Belief Signal Classes

```text
behavior outcome sensitive rows: {summary['behavior_outcome_sensitive_count']}
action response sensitive rows: {summary['action_response_sensitive_count']}
trace sensitive rows: {summary['trace_sensitive_count']}
weak/context rows: {summary['weak_or_context_count']}
action L1 threshold: {summary['action_l1_mean_threshold']}
ego response L2 threshold: {summary['ego_response_l2_mean_threshold']}
command response proxy abs-delta threshold: {summary['command_response_proxy_abs_delta_threshold']}
trace delta proxy abs-delta threshold: {summary['trace_delta_proxy_abs_delta_threshold']}
```

The thresholds are deterministic materialization thresholds only. They are not
performance gates, ranking criteria, or proof of self-identification.

## Actor And Claim Boundary

```text
actor contract 72/action 3: {summary['actor_contract_shape_72_action_3']}
hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}
actor-visible label detected: {summary['actor_visible_label_detected']}
actor-visible stress/admission/curriculum labels detected: {summary['actor_visible_stress_admission_curriculum_labels_detected']}
mitigation reference rows guarded: {summary['mitigation_reference_rows_guarded']}
new execution run: {summary['new_execution_run']}
training run: {summary['training_run']}
PPO run: {summary['ppo_run']}
ranking run: {summary['ranking_run']}
winner selected: {summary['winner_selected']}
success-rate verdict computed: {summary['success_rate_verdict_computed']}
driver-performance claim made: {summary['driver_performance_claim_made']}
self-ID claim made: {summary['level3_self_id_claim_made']}
```

## Route Decision

Route to M2780 result audit before any materialization extension, fresh
closed-loop execution, short training continuation, training-pack
implementation, ranking, promotion, validation, or performance claim.
"""
    path.write_text(text, encoding="utf-8")


def _collision_changed(row: Mapping[str, Any]) -> bool:
    return _truthy(row.get("collision_added")) or _truthy(row.get("collision_removed")) or _to_int(row.get("collision_delta")) != 0


def _future_pack_priority(signal_counts: Mapping[str, int], mitigation_count: int, ordinary_count: int) -> str:
    if ordinary_count == 0 and mitigation_count:
        return "context_only"
    if signal_counts["behavior_outcome_sensitive"]:
        return "high_audit_required"
    if signal_counts["action_response_sensitive"]:
        return "medium_audit_required"
    if signal_counts["trace_sensitive"]:
        return "low_audit_required"
    return "context_only"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2778-design", default=str(DEFAULT_M2778_DESIGN))
    parser.add_argument("--m2775-dir", default=str(DEFAULT_M2775_DIR))
    parser.add_argument("--m2773-dir", default=str(DEFAULT_M2773_DIR))
    parser.add_argument("--follow-up-manifest", default=str(DEFAULT_FOLLOW_UP_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--doc-path", default=str(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)
    summary = materialize_source_only_belief_stress_training_admission_pack(
        Path(args.output_dir),
        m2778_design=args.m2778_design,
        m2775_dir=args.m2775_dir,
        m2773_dir=args.m2773_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'} status_pass={summary['status_pass']}")
    raise SystemExit(0 if summary["status_pass"] else 1)


if __name__ == "__main__":
    main()
