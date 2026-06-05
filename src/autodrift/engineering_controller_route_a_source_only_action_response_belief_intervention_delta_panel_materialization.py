"""M2775 source-only action-response belief intervention delta panel.

This materializer consumes M2773 artifacts only. It does not reset, step,
replay, train, validate, rank, or promote a controller.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_MILESTONE = (
    "m2775-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-delta-panel-materialization-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2775_engineering_controller_route_a_source_only_action_response_belief_"
    "intervention_delta_panel_materialization"
)
DEFAULT_M2774_AUDIT = (
    "docs/m2774-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-materialization-result-audit.md"
)
DEFAULT_M2773_DIR = Path(
    "runs/m2773_engineering_controller_route_a_source_only_action_response_belief_"
    "intervention_materialization_preflight"
)
DEFAULT_FOLLOW_UP_MANIFEST = (
    "experiments/manifests/m2776-engineering-controller-route-a-source-only-action-"
    "response-belief-intervention-delta-panel-materialization-result-audit.json"
)
DEFAULT_DOC_PATH = (
    "docs/m2775-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-delta-panel-materialization-preflight.md"
)
DEFAULT_NEXT_BLOCKER = (
    "m2776-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-delta-panel-materialization-result-audit"
)

NORMAL_CONDITION_ID = "normal_recurrent"
INTERVENTION_CONDITION_IDS = (
    "reset_hidden_each_step",
    "zero_previous_command_history",
    "held_actuator_history",
)
CLAIM_SCOPE = "Route A source-only normal-vs-intervention delta-panel materialization only"
FORBIDDEN_INTERPRETATION = (
    "new rollout, replay, training, validation, ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, repair success, driver performance, "
    "paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation, full ideal driver completion, or level3 self-identification"
)
CLAIM_BOUNDARY = (
    "M2775 materializes no-new-rollout source-only normal-vs-intervention deltas only; "
    "delta rows are diagnostic reanalysis and not ranking, promotion, validation, "
    "performance, paper, current-sim, high-fidelity, full-driver, or self-ID evidence"
)

INTERVENTION_DELTA_FIELDNAMES = [
    "delta_row_id",
    "candidate_id",
    "role_family",
    "dynamics_axis",
    "seed",
    "normal_condition_id",
    "intervention_condition_id",
    "ordinary_denominator_allowed",
    "mitigation_reference",
    "matched_trace_steps",
    "trace_pair_complete",
    "normal_collision_diagnostic",
    "intervention_collision_diagnostic",
    "collision_delta",
    "collision_added",
    "collision_removed",
    "normal_road_departure_diagnostic",
    "intervention_road_departure_diagnostic",
    "road_departure_delta",
    "road_departure_added",
    "road_departure_removed",
    "normal_minimum_obstacle_clearance_m",
    "intervention_minimum_obstacle_clearance_m",
    "minimum_obstacle_clearance_m_delta",
    "normal_minimum_road_margin_m",
    "intervention_minimum_road_margin_m",
    "minimum_road_margin_m_delta",
    "trace_delta_proxy_delta",
    "command_response_proxy_delta",
    "action_l1_mean",
    "action_linf_max",
    "physical_action_l1_mean",
    "ego_response_l2_mean",
    "state_speed_abs_delta_mean",
    "finite_trace_pair_pass",
    "actor_input_shape_changed",
    "hidden_or_oracle_actor_input_added",
    "actor_visible_label",
    "no_new_execution",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "claim_boundary",
]

AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "role_family",
    "dynamics_axis",
    "intervention_condition_id",
    "delta_row_count",
    "ordinary_delta_row_count",
    "mitigation_reference_delta_row_count",
    "collision_added_count",
    "collision_removed_count",
    "road_departure_added_count",
    "road_departure_removed_count",
    "minimum_obstacle_clearance_m_delta_mean",
    "minimum_road_margin_m_delta_mean",
    "trace_delta_proxy_delta_mean",
    "command_response_proxy_delta_mean",
    "action_l1_mean_mean",
    "action_linf_max_mean",
    "physical_action_l1_mean_mean",
    "ego_response_l2_mean_mean",
    "state_speed_abs_delta_mean_mean",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "claim_boundary",
]

MITIGATION_GUARD_FIELDNAMES = [
    "candidate_id",
    "role_family",
    "mitigation_reference",
    "ordinary_success_denominator_allowed",
    "delta_panel_context_only",
    "actor_visible_allowed",
    "claim_boundary",
]

ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "source_guard_id",
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


def materialize_source_only_action_response_belief_intervention_delta_panel(
    output_dir: Path | str,
    *,
    m2774_audit: Path | str = DEFAULT_M2774_AUDIT,
    m2773_dir: Path | str = DEFAULT_M2773_DIR,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    m2773 = Path(m2773_dir)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(Path(m2774_audit), m2773)

    m2773_summary = read_json(source_paths["m2773_summary"]) if source_paths["m2773_summary"].exists() else {}
    candidate_rows = read_csv_rows(source_paths["source_only_candidate_rows"])
    condition_rows = read_csv_rows(source_paths["intervention_condition_rows"])
    matrix_rows = read_csv_rows(source_paths["candidate_intervention_matrix"])
    execution_rows = read_csv_rows(source_paths["intervention_execution_rows"])
    failure_rows = read_csv_rows(source_paths["intervention_failure_rows"])
    trace_rows = read_csv_rows(source_paths["action_response_trace_rows"])
    mitigation_source_rows = read_csv_rows(source_paths["mitigation_reference_guard_rows"])
    actor_source_rows = read_csv_rows(source_paths["actor_contract_guard_rows"])
    claim_source_rows = read_csv_rows(source_paths["claim_boundary_rows"])
    gate_source_rows = read_csv_rows(source_paths["gate_matrix"])

    delta_rows, pairing = build_intervention_delta_rows(
        candidate_rows=candidate_rows,
        condition_rows=condition_rows,
        execution_rows=execution_rows,
        trace_rows=trace_rows,
    )
    role_dynamics_rows = build_role_dynamics_delta_aggregate_rows(delta_rows)
    intervention_condition_rows = build_intervention_condition_delta_aggregate_rows(delta_rows)
    mitigation_guard_rows = build_mitigation_reference_guard_rows(mitigation_source_rows)
    actor_guard_rows = build_actor_contract_guard_rows(actor_source_rows)
    claim_rows = build_claim_boundary_rows()

    write_csv_rows(paths["intervention_delta_rows"], delta_rows, fieldnames=INTERVENTION_DELTA_FIELDNAMES)
    write_csv_rows(
        paths["role_dynamics_delta_aggregate_rows"],
        role_dynamics_rows,
        fieldnames=AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(
        paths["intervention_condition_delta_aggregate_rows"],
        intervention_condition_rows,
        fieldnames=AGGREGATE_FIELDNAMES,
    )
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
        m2773_summary=m2773_summary,
        candidate_rows=candidate_rows,
        condition_rows=condition_rows,
        matrix_rows=matrix_rows,
        execution_rows=execution_rows,
        failure_rows=failure_rows,
        trace_rows=trace_rows,
        mitigation_source_rows=mitigation_source_rows,
        actor_source_rows=actor_source_rows,
        claim_source_rows=claim_source_rows,
        gate_source_rows=gate_source_rows,
        delta_rows=delta_rows,
        role_dynamics_rows=role_dynamics_rows,
        intervention_condition_rows=intervention_condition_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        pairing=pairing,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    gate_rows = build_gate_matrix_rows(metrics)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = _summary(metrics, gate_rows)
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], _run_state(summary, paths))
    write_json(paths["follow_up_manifest"], _m2776_manifest(summary))
    _write_doc(paths["doc"], summary)
    return summary


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_intervention_delta_rows(
    *,
    candidate_rows: Sequence[Mapping[str, Any]],
    condition_rows: Sequence[Mapping[str, Any]],
    execution_rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidate_by_id = {str(row.get("candidate_id", "")): row for row in candidate_rows}
    condition_ids = {str(row.get("intervention_condition_id", "")) for row in condition_rows}
    non_normal_ids = [condition for condition in INTERVENTION_CONDITION_IDS if condition in condition_ids]
    execution_by_key = {
        (str(row.get("candidate_id", "")), str(row.get("intervention_condition_id", ""))): row
        for row in execution_rows
    }
    trace_by_key: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in trace_rows:
        key = (str(row.get("candidate_id", "")), str(row.get("intervention_condition_id", "")))
        trace_by_key[key].append(row)
    for rows in trace_by_key.values():
        rows.sort(key=lambda row: _to_int(row.get("step_index")))

    delta_rows: list[dict[str, Any]] = []
    missing_pairs: list[dict[str, str]] = []
    duplicate_pair_count = max(0, len(execution_rows) - len(execution_by_key))
    for candidate in candidate_rows:
        candidate_id = str(candidate.get("candidate_id", ""))
        normal = execution_by_key.get((candidate_id, NORMAL_CONDITION_ID))
        if normal is None:
            missing_pairs.append({"candidate_id": candidate_id, "intervention_condition_id": NORMAL_CONDITION_ID})
            continue
        for condition_id in non_normal_ids:
            intervention = execution_by_key.get((candidate_id, condition_id))
            if intervention is None:
                missing_pairs.append({"candidate_id": candidate_id, "intervention_condition_id": condition_id})
                continue
            normal_trace = trace_by_key.get((candidate_id, NORMAL_CONDITION_ID), [])
            intervention_trace = trace_by_key.get((candidate_id, condition_id), [])
            delta_rows.append(
                _delta_row(
                    candidate=candidate_by_id.get(candidate_id, candidate),
                    normal=normal,
                    intervention=intervention,
                    normal_trace=normal_trace,
                    intervention_trace=intervention_trace,
                    condition_id=condition_id,
                )
            )

    expected_delta_rows = len(candidate_rows) * len(INTERVENTION_CONDITION_IDS)
    pairing = {
        "candidate_row_count": len(candidate_rows),
        "observed_non_normal_condition_count": len(non_normal_ids),
        "expected_non_normal_condition_count": len(INTERVENTION_CONDITION_IDS),
        "expected_delta_row_count": expected_delta_rows,
        "missing_pair_count": len(missing_pairs),
        "missing_pairs": missing_pairs[:20],
        "duplicate_execution_pair_count": duplicate_pair_count,
        "trace_pair_complete_count": sum(bool(row["trace_pair_complete"]) for row in delta_rows),
        "trace_pair_incomplete_count": sum(not bool(row["trace_pair_complete"]) for row in delta_rows),
        "pairing_complete": (
            len(delta_rows) == expected_delta_rows
            and len(missing_pairs) == 0
            and duplicate_pair_count == 0
            and len(non_normal_ids) == len(INTERVENTION_CONDITION_IDS)
        ),
    }
    return delta_rows, pairing


def build_role_dynamics_delta_aggregate_rows(delta_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return _aggregate_rows(
        delta_rows,
        group_keys=("role_family", "dynamics_axis", "intervention_condition_id"),
        aggregate_prefix="role_dynamics",
    )


def build_intervention_condition_delta_aggregate_rows(delta_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = _aggregate_rows(
        delta_rows,
        group_keys=("intervention_condition_id",),
        aggregate_prefix="intervention_condition",
    )
    for row in rows:
        row["role_family"] = "ALL"
        row["dynamics_axis"] = "ALL"
    return rows


def build_mitigation_reference_guard_rows(source_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row.get("candidate_id", ""),
            "role_family": row.get("role_family", ""),
            "mitigation_reference": _truthy(row.get("mitigation_reference")),
            "ordinary_success_denominator_allowed": _truthy(row.get("ordinary_success_denominator_allowed")),
            "delta_panel_context_only": True,
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for row in source_rows
    ]


def build_actor_contract_guard_rows(source_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows):
        protected_field = str(row.get("protected_field", ""))
        rows.append(
            {
                "guard_id": f"m2775_actor_guard_{index:02d}_{protected_field}",
                "source_guard_id": row.get("guard_id", ""),
                "guard_family": row.get("guard_family", ""),
                "protected_field": protected_field,
                "actor_visible_allowed": False,
                "actor_observation_shape": row.get("actor_observation_shape", ""),
                "action_shape": row.get("action_shape", ""),
                "status_pass": _truthy(row.get("status_pass")) and not _truthy(row.get("actor_visible_allowed")),
                "evidence": "inherited M2773 actor guard; M2775 reads artifacts only and changes no actor input",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claims = (
        "new_rollout_execution",
        "reset_step_policy_execution",
        "replay_or_validation_execution",
        "training_or_ppo",
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
            "claim_id": f"m2775_claim_{claim}",
            "claim_family": claim,
            "claim_made": False,
            "allowed": False,
            "status_pass": True,
            "evidence": "M2775 is no-new-rollout delta-panel materialization only",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for claim in claims
    ]


def build_gate_matrix_rows(metrics: Mapping[str, Any]) -> list[dict[str, Any]]:
    gate_specs = (
        ("m2774_audit_exists", "lineage", metrics["m2774_audit_exists"], True, "lineage_invalid"),
        ("m2773_status_pass", "lineage", metrics["m2773_status_pass"], True, "lineage_invalid"),
        ("m2773_gate_matrix_pass", "lineage", metrics["m2773_gate_matrix_pass"], True, "lineage_invalid"),
        ("m2773_failure_rows_empty", "artifact", metrics["m2773_failure_rows_empty"], True, "metric_artifact"),
        ("source_artifacts_required_present", "artifact", metrics["source_artifacts_required_present"], True, "lineage_invalid"),
        ("normal_execution_row_count", "panel_shape", metrics["normal_execution_row_count"], 32, "metric_artifact"),
        ("evaluator_intervention_execution_row_count", "panel_shape", metrics["evaluator_intervention_execution_row_count"], 96, "metric_artifact"),
        ("intervention_delta_row_count", "panel_shape", metrics["intervention_delta_row_count"], 96, "metric_artifact"),
        ("pairing_complete", "artifact", metrics["pairing_complete"], True, "metric_artifact"),
        ("trace_pair_accounting", "artifact", metrics["trace_pair_accounting"], True, "metric_artifact"),
        ("role_dynamics_delta_aggregate_row_count", "panel_shape", metrics["role_dynamics_delta_aggregate_row_count"], 24, "metric_artifact"),
        ("intervention_condition_delta_aggregate_row_count", "panel_shape", metrics["intervention_condition_delta_aggregate_row_count"], 3, "metric_artifact"),
        ("mitigation_reference_rows_guarded", "claim_boundary", metrics["mitigation_reference_rows_guarded"], True, "proof_washout"),
        ("actor_contract_shape_72_action_3", "actor_contract", metrics["actor_contract_shape_72_action_3"], True, "contract_violation"),
        ("hidden_oracle_actor_input_detected", "actor_contract", metrics["hidden_oracle_actor_input_detected"], False, "contract_violation"),
        ("actor_visible_label_detected", "actor_contract", metrics["actor_visible_label_detected"], False, "contract_violation"),
        ("new_execution_run", "forbidden_claim", metrics["new_execution_run"], False, "objective_overfit"),
        ("training_run", "forbidden_claim", metrics["training_run"], False, "objective_overfit"),
        ("ranking_run", "forbidden_claim", metrics["ranking_run"], False, "objective_overfit"),
        ("winner_selected", "forbidden_claim", metrics["winner_selected"], False, "objective_overfit"),
        ("success_rate_verdict_computed", "forbidden_claim", metrics["success_rate_verdict_computed"], False, "objective_overfit"),
        ("driver_performance_claim_made", "forbidden_claim", metrics["driver_performance_claim_made"], False, "objective_overfit"),
        ("level3_self_id_claim_made", "forbidden_claim", metrics["level3_self_id_claim_made"], False, "objective_overfit"),
        ("m2776_follow_up_manifest_registered", "next_route", metrics["m2776_follow_up_manifest_registered"], True, "lineage_invalid"),
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


def _delta_row(
    *,
    candidate: Mapping[str, Any],
    normal: Mapping[str, Any],
    intervention: Mapping[str, Any],
    normal_trace: Sequence[Mapping[str, Any]],
    intervention_trace: Sequence[Mapping[str, Any]],
    condition_id: str,
) -> dict[str, Any]:
    normal_collision = _truthy(normal.get("collision_diagnostic"))
    intervention_collision = _truthy(intervention.get("collision_diagnostic"))
    normal_road_departure = _truthy(normal.get("road_departure_diagnostic"))
    intervention_road_departure = _truthy(intervention.get("road_departure_diagnostic"))
    matched_steps = min(len(normal_trace), len(intervention_trace))
    action_l1: list[float] = []
    action_linf: list[float] = []
    physical_action_l1: list[float] = []
    ego_response_l2: list[float] = []
    state_speed_abs_delta: list[float] = []
    finite_pairs: list[bool] = []
    for normal_row, intervention_row in zip(normal_trace, intervention_trace):
        action_deltas = [
            abs(_to_float(intervention_row.get(key)) - _to_float(normal_row.get(key)))
            for key in ("steer", "throttle", "brake")
        ]
        physical_deltas = [
            abs(_to_float(intervention_row.get(key)) - _to_float(normal_row.get(key)))
            for key in ("physical_steer", "physical_throttle", "physical_brake")
        ]
        ego_deltas = [
            _to_float(intervention_row.get(key)) - _to_float(normal_row.get(key))
            for key in ("vx_body", "vy_body", "yaw_rate", "ax_body", "ay_body")
        ]
        action_l1.append(sum(action_deltas))
        action_linf.append(max(action_deltas) if action_deltas else 0.0)
        physical_action_l1.append(sum(physical_deltas))
        ego_response_l2.append(sum(value * value for value in ego_deltas) ** 0.5)
        state_speed_abs_delta.append(
            abs(_to_float(intervention_row.get("state_speed")) - _to_float(normal_row.get("state_speed")))
        )
        finite_pairs.append(_truthy(normal_row.get("finite_metric")) and _truthy(intervention_row.get("finite_metric")))
    horizon = max(len(normal_trace), len(intervention_trace))
    trace_pair_complete = matched_steps == horizon and matched_steps == _to_int(normal.get("steps_executed"))
    return {
        "delta_row_id": f"m2775_{normal.get('candidate_id', '')}_{condition_id}",
        "candidate_id": normal.get("candidate_id", ""),
        "role_family": normal.get("role_family", candidate.get("role_family", "")),
        "dynamics_axis": normal.get("dynamics_axis", candidate.get("dynamics_axis", "")),
        "seed": normal.get("seed", candidate.get("seed", "")),
        "normal_condition_id": NORMAL_CONDITION_ID,
        "intervention_condition_id": condition_id,
        "ordinary_denominator_allowed": _truthy(candidate.get("ordinary_success_denominator_allowed")),
        "mitigation_reference": _truthy(candidate.get("mitigation_reference")),
        "matched_trace_steps": matched_steps,
        "trace_pair_complete": trace_pair_complete,
        "normal_collision_diagnostic": normal_collision,
        "intervention_collision_diagnostic": intervention_collision,
        "collision_delta": int(intervention_collision) - int(normal_collision),
        "collision_added": (not normal_collision) and intervention_collision,
        "collision_removed": normal_collision and not intervention_collision,
        "normal_road_departure_diagnostic": normal_road_departure,
        "intervention_road_departure_diagnostic": intervention_road_departure,
        "road_departure_delta": int(intervention_road_departure) - int(normal_road_departure),
        "road_departure_added": (not normal_road_departure) and intervention_road_departure,
        "road_departure_removed": normal_road_departure and not intervention_road_departure,
        "normal_minimum_obstacle_clearance_m": _to_float(normal.get("minimum_obstacle_clearance_m")),
        "intervention_minimum_obstacle_clearance_m": _to_float(intervention.get("minimum_obstacle_clearance_m")),
        "minimum_obstacle_clearance_m_delta": _to_float(intervention.get("minimum_obstacle_clearance_m"))
        - _to_float(normal.get("minimum_obstacle_clearance_m")),
        "normal_minimum_road_margin_m": _to_float(normal.get("minimum_road_margin_m")),
        "intervention_minimum_road_margin_m": _to_float(intervention.get("minimum_road_margin_m")),
        "minimum_road_margin_m_delta": _to_float(intervention.get("minimum_road_margin_m"))
        - _to_float(normal.get("minimum_road_margin_m")),
        "trace_delta_proxy_delta": _to_float(intervention.get("trace_delta_proxy"))
        - _to_float(normal.get("trace_delta_proxy")),
        "command_response_proxy_delta": _to_float(intervention.get("command_response_proxy"))
        - _to_float(normal.get("command_response_proxy")),
        "action_l1_mean": _mean(action_l1),
        "action_linf_max": max(action_linf) if action_linf else 0.0,
        "physical_action_l1_mean": _mean(physical_action_l1),
        "ego_response_l2_mean": _mean(ego_response_l2),
        "state_speed_abs_delta_mean": _mean(state_speed_abs_delta),
        "finite_trace_pair_pass": bool(finite_pairs) and all(finite_pairs),
        "actor_input_shape_changed": False,
        "hidden_or_oracle_actor_input_added": False,
        "actor_visible_label": False,
        "no_new_execution": True,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _aggregate_rows(
    delta_rows: Sequence[Mapping[str, Any]],
    *,
    group_keys: tuple[str, ...],
    aggregate_prefix: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in delta_rows:
        grouped[tuple(str(row.get(key, "")) for key in group_keys)].append(row)
    rows: list[dict[str, Any]] = []
    for key_values in sorted(grouped):
        group = grouped[key_values]
        values = dict(zip(group_keys, key_values, strict=True))
        role_family = values.get("role_family", "")
        dynamics_axis = values.get("dynamics_axis", "")
        condition_id = values.get("intervention_condition_id", "")
        if "intervention_condition_id" not in values:
            condition_id = str(group[0].get("intervention_condition_id", ""))
        rows.append(
            {
                "aggregate_id": f"{aggregate_prefix}_{'_'.join(key_values)}",
                "role_family": role_family,
                "dynamics_axis": dynamics_axis,
                "intervention_condition_id": condition_id,
                "delta_row_count": len(group),
                "ordinary_delta_row_count": sum(_truthy(row.get("ordinary_denominator_allowed")) for row in group),
                "mitigation_reference_delta_row_count": sum(_truthy(row.get("mitigation_reference")) for row in group),
                "collision_added_count": sum(_truthy(row.get("collision_added")) for row in group),
                "collision_removed_count": sum(_truthy(row.get("collision_removed")) for row in group),
                "road_departure_added_count": sum(_truthy(row.get("road_departure_added")) for row in group),
                "road_departure_removed_count": sum(_truthy(row.get("road_departure_removed")) for row in group),
                "minimum_obstacle_clearance_m_delta_mean": _mean(
                    _to_float(row.get("minimum_obstacle_clearance_m_delta")) for row in group
                ),
                "minimum_road_margin_m_delta_mean": _mean(
                    _to_float(row.get("minimum_road_margin_m_delta")) for row in group
                ),
                "trace_delta_proxy_delta_mean": _mean(_to_float(row.get("trace_delta_proxy_delta")) for row in group),
                "command_response_proxy_delta_mean": _mean(
                    _to_float(row.get("command_response_proxy_delta")) for row in group
                ),
                "action_l1_mean_mean": _mean(_to_float(row.get("action_l1_mean")) for row in group),
                "action_linf_max_mean": _mean(_to_float(row.get("action_linf_max")) for row in group),
                "physical_action_l1_mean_mean": _mean(_to_float(row.get("physical_action_l1_mean")) for row in group),
                "ego_response_l2_mean_mean": _mean(_to_float(row.get("ego_response_l2_mean")) for row in group),
                "state_speed_abs_delta_mean_mean": _mean(
                    _to_float(row.get("state_speed_abs_delta_mean")) for row in group
                ),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _paths(output_dir: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "intervention_delta_rows": output_dir / "intervention_delta_rows.csv",
        "role_dynamics_delta_aggregate_rows": output_dir / "role_dynamics_delta_aggregate_rows.csv",
        "intervention_condition_delta_aggregate_rows": output_dir / "intervention_condition_delta_aggregate_rows.csv",
        "mitigation_reference_guard_rows": output_dir / "mitigation_reference_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "summary": output_dir / "summary.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _source_paths(m2774_audit: Path, m2773_dir: Path) -> dict[str, Path]:
    return {
        "m2774_audit": m2774_audit,
        "m2773_summary": m2773_dir / "summary.json",
        "source_only_candidate_rows": m2773_dir / "source_only_candidate_rows.csv",
        "intervention_condition_rows": m2773_dir / "intervention_condition_rows.csv",
        "candidate_intervention_matrix": m2773_dir / "candidate_intervention_matrix.csv",
        "intervention_execution_rows": m2773_dir / "intervention_execution_rows.csv",
        "intervention_failure_rows": m2773_dir / "intervention_failure_rows.csv",
        "action_response_trace_rows": m2773_dir / "action_response_trace_rows.csv",
        "mitigation_reference_guard_rows": m2773_dir / "mitigation_reference_guard_rows.csv",
        "actor_contract_guard_rows": m2773_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2773_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2773_dir / "gate_matrix.csv",
    }


def _metrics(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source_paths: Mapping[str, Path],
    m2773_summary: Mapping[str, Any],
    candidate_rows: Sequence[Mapping[str, Any]],
    condition_rows: Sequence[Mapping[str, Any]],
    matrix_rows: Sequence[Mapping[str, Any]],
    execution_rows: Sequence[Mapping[str, Any]],
    failure_rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
    mitigation_source_rows: Sequence[Mapping[str, Any]],
    actor_source_rows: Sequence[Mapping[str, Any]],
    claim_source_rows: Sequence[Mapping[str, Any]],
    gate_source_rows: Sequence[Mapping[str, Any]],
    delta_rows: Sequence[Mapping[str, Any]],
    role_dynamics_rows: Sequence[Mapping[str, Any]],
    intervention_condition_rows: Sequence[Mapping[str, Any]],
    mitigation_guard_rows: Sequence[Mapping[str, Any]],
    actor_guard_rows: Sequence[Mapping[str, Any]],
    claim_rows: Sequence[Mapping[str, Any]],
    pairing: Mapping[str, Any],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    source_exists = {name: path.exists() for name, path in source_paths.items()}
    required_output_present = all(
        paths[key].exists()
        for key in (
            "intervention_delta_rows",
            "role_dynamics_delta_aggregate_rows",
            "intervention_condition_delta_aggregate_rows",
            "mitigation_reference_guard_rows",
            "actor_contract_guard_rows",
            "claim_boundary_rows",
        )
    )
    normal_execution_row_count = sum(
        str(row.get("intervention_condition_id", "")) == NORMAL_CONDITION_ID for row in execution_rows
    )
    evaluator_execution_row_count = sum(
        str(row.get("intervention_condition_id", "")) in INTERVENTION_CONDITION_IDS for row in execution_rows
    )
    expected_trace_pair_rows = int(m2773_summary.get("horizon_steps", 0) or 0) * int(
        pairing.get("expected_delta_row_count", 0)
    )
    paired_trace_row_count = sum(_to_int(row.get("matched_trace_steps")) for row in delta_rows)
    mitigation_reference_rows_guarded = (
        len(mitigation_guard_rows) == 8
        and all(_truthy(row.get("mitigation_reference")) for row in mitigation_guard_rows)
        and all(not _truthy(row.get("ordinary_success_denominator_allowed")) for row in mitigation_guard_rows)
        and all(not _truthy(row.get("actor_visible_allowed")) for row in mitigation_guard_rows)
    )
    actor_contract_shape_72_action_3 = (
        bool(actor_guard_rows)
        and all(str(row.get("actor_observation_shape", "")) == "72" for row in actor_guard_rows)
        and all(str(row.get("action_shape", "")) == "3" for row in actor_guard_rows)
        and all(_truthy(row.get("status_pass")) for row in actor_guard_rows)
    )
    hidden_oracle_actor_input_detected = bool(m2773_summary.get("hidden_oracle_actor_input_detected", True))
    actor_visible_label_detected = bool(m2773_summary.get("actor_visible_label_detected", True)) or any(
        _truthy(row.get("actor_visible_label")) for row in delta_rows
    )
    trace_pair_accounting = (
        bool(delta_rows)
        and all(_truthy(row.get("trace_pair_complete")) for row in delta_rows)
        and (expected_trace_pair_rows == 0 or paired_trace_row_count == expected_trace_pair_rows)
    )
    metrics = {
        "milestone": milestone,
        "result_class": "engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization_pass",
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "m2774_audit": str(source_paths["m2774_audit"]),
        "m2774_audit_exists": source_exists["m2774_audit"],
        "m2773_dir": str(source_paths["m2773_summary"].parent),
        "source_artifact_exists": source_exists,
        "source_artifacts_required_present": all(source_exists.values()),
        "required_artifacts_present": required_output_present,
        "m2773_status_pass": bool(m2773_summary.get("status_pass", False)),
        "m2773_gate_matrix_pass": bool(m2773_summary.get("gate_matrix_pass", False)),
        "m2773_candidate_row_count": m2773_summary.get("candidate_row_count", 0),
        "m2773_intervention_execution_row_count": m2773_summary.get("intervention_execution_row_count", 0),
        "m2773_action_response_trace_row_count": m2773_summary.get("action_response_trace_row_count", 0),
        "m2773_failure_rows_empty": len(failure_rows) == 0,
        "source_candidate_row_count": len(candidate_rows),
        "source_condition_row_count": len(condition_rows),
        "source_candidate_intervention_matrix_row_count": len(matrix_rows),
        "source_execution_row_count": len(execution_rows),
        "source_failure_row_count": len(failure_rows),
        "source_trace_row_count": len(trace_rows),
        "source_mitigation_guard_row_count": len(mitigation_source_rows),
        "source_actor_guard_row_count": len(actor_source_rows),
        "source_claim_boundary_row_count": len(claim_source_rows),
        "source_gate_row_count": len(gate_source_rows),
        "normal_execution_row_count": normal_execution_row_count,
        "evaluator_intervention_execution_row_count": evaluator_execution_row_count,
        "intervention_delta_row_count": len(delta_rows),
        "expected_intervention_delta_rows": pairing.get("expected_delta_row_count", 0),
        "missing_pair_count": pairing.get("missing_pair_count", 0),
        "missing_pairs": pairing.get("missing_pairs", []),
        "duplicate_execution_pair_count": pairing.get("duplicate_execution_pair_count", 0),
        "pairing_complete": bool(pairing.get("pairing_complete", False)),
        "matched_trace_pair_row_count": paired_trace_row_count,
        "expected_matched_trace_pair_row_count": expected_trace_pair_rows,
        "trace_pair_complete_count": pairing.get("trace_pair_complete_count", 0),
        "trace_pair_incomplete_count": pairing.get("trace_pair_incomplete_count", 0),
        "trace_pair_accounting": trace_pair_accounting,
        "role_dynamics_delta_aggregate_row_count": len(role_dynamics_rows),
        "intervention_condition_delta_aggregate_row_count": len(intervention_condition_rows),
        "mitigation_reference_guard_row_count": len(mitigation_guard_rows),
        "mitigation_reference_rows_guarded": mitigation_reference_rows_guarded,
        "actor_guard_row_count": len(actor_guard_rows),
        "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected,
        "actor_visible_label_detected": actor_visible_label_detected,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": bool(claim_rows) and all(_truthy(row.get("status_pass")) for row in claim_rows),
        "collision_added_delta_row_count": sum(_truthy(row.get("collision_added")) for row in delta_rows),
        "collision_removed_delta_row_count": sum(_truthy(row.get("collision_removed")) for row in delta_rows),
        "road_departure_added_delta_row_count": sum(_truthy(row.get("road_departure_added")) for row in delta_rows),
        "road_departure_removed_delta_row_count": sum(_truthy(row.get("road_departure_removed")) for row in delta_rows),
        "minimum_obstacle_clearance_m_delta_mean": _mean(
            _to_float(row.get("minimum_obstacle_clearance_m_delta")) for row in delta_rows
        ),
        "minimum_road_margin_m_delta_mean": _mean(
            _to_float(row.get("minimum_road_margin_m_delta")) for row in delta_rows
        ),
        "trace_delta_proxy_delta_mean": _mean(_to_float(row.get("trace_delta_proxy_delta")) for row in delta_rows),
        "command_response_proxy_delta_mean": _mean(
            _to_float(row.get("command_response_proxy_delta")) for row in delta_rows
        ),
        "action_l1_mean": _mean(_to_float(row.get("action_l1_mean")) for row in delta_rows),
        "physical_action_l1_mean": _mean(_to_float(row.get("physical_action_l1_mean")) for row in delta_rows),
        "ego_response_l2_mean": _mean(_to_float(row.get("ego_response_l2_mean")) for row in delta_rows),
        "state_speed_abs_delta_mean": _mean(_to_float(row.get("state_speed_abs_delta_mean")) for row in delta_rows),
        "new_execution_run": False,
        "reset_step_policy_execution_run": False,
        "replay_or_validation_run": False,
        "training_run": False,
        "ppo_run": False,
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
        "m2776_follow_up_manifest_registered": bool(str(paths["follow_up_manifest"])),
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
        and bool(metrics["pairing_complete"])
        and bool(metrics["trace_pair_accounting"])
        and bool(metrics["claim_boundary_rows_pass"])
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
            "engineering_controller_route_a_source_only_action_response_belief_"
            "intervention_delta_panel_materialization_failed"
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
        "generated_at_utc": summary["generated_at_utc"],
    }


def _m2776_manifest(summary: Mapping[str, Any]) -> dict[str, Any]:
    m2775_id = str(summary["milestone"])
    m2776_id = DEFAULT_NEXT_BLOCKER
    run_dir = Path(str(summary["output_dir"]))
    return {
        "id": m2776_id,
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
                str(run_dir / "intervention_delta_rows.csv"),
                str(run_dir / "role_dynamics_delta_aggregate_rows.csv"),
                str(run_dir / "intervention_condition_delta_aggregate_rows.csv"),
                str(run_dir / "mitigation_reference_guard_rows.csv"),
                str(run_dir / "actor_contract_guard_rows.csv"),
                str(run_dir / "claim_boundary_rows.csv"),
                str(run_dir / "gate_matrix.csv"),
                str(summary["doc"]),
            ],
            "parent_config": [
                "experiments/manifests/m2775-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-preflight.json",
                "experiments/manifests/m2774-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-result-audit.json",
            ],
            "parent_objective": [
                "audit M2775 no-new-rollout source-only normal-vs-intervention delta-panel artifacts before interpretation"
            ],
            "derived_from": [
                m2775_id,
                "m2774-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-result-audit",
                "m2773-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-preflight",
            ],
            "blocked_by": [
                "M2775 delta rows must be audited before synthesis or proof extension",
                "M2775 source-only deltas cannot be interpreted as ranking performance validation or self-ID evidence",
            ],
            "supersedes": [
                "direct interpretation of M2773 raw intervention rows",
                "ranking intervention conditions from delta rows",
                "driver-performance or self-ID interpretation from source-only delta rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{m2776_id}.md",
        "public_gates": [
            "M2776 must audit M2775 artifact completeness actor-contract preservation and claim boundaries",
            "M2776 must preserve M2775 source-only diagnostic reanalysis scope and reject validation performance paper high-fidelity full-driver and self-ID claims",
            "M2776 must decide whether to route to source-only intervention synthesis proof-extension design artifact repair or branch stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step rollout replay validation training PPO source build adapter probe or external simulation in audit",
            "do not change actor inputs or action contract",
            "do not rank intervention conditions roles dynamics axes candidates or controllers",
            "do not select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdicts",
            "do not claim driver performance paper current-sim high-fidelity full ideal driver or self-ID evidence",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_action_response_belief_intervention",
            "evidence_axis": "source_only_action_response_belief_intervention_delta_panel_result_audit",
            "evidence_increment": "audits M2775 source-only normal-vs-intervention delta-panel artifacts before synthesis or proof extension",
            "claim_scope": "M2775 result audit only; no new execution training ranking validation performance paper current-sim high-fidelity self-ID or full ideal driver claim",
            "stop_condition": [
                "stop if M2775 artifacts are incomplete",
                "stop if M2775 delta pairing or trace accounting is incomplete",
                "stop if delta rows would be interpreted as validation performance paper high-fidelity or self-ID evidence",
            ],
            "fallback_plan": [
                "route to artifact repair if pairing or accounting is incomplete",
                "route to branch synthesis if deltas are complete but weak ambiguous or behavior-negative",
                "route to proof-extension design only after audit and synthesis preserve claim boundaries",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2775 writes no-new-rollout source-only delta-panel artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "evaluation_only",
            "stage_objective": "source-only action-response belief intervention delta-panel result audit",
            "admission_evidence": ["M2775 summary and gate artifacts exist"],
            "blocked_shortcuts": ["no execution training ranking validation performance paper HF or self-ID claim in audit"],
            "allowed_updates": [f"docs/{m2776_id}.md", "M2776 status queue scoreboard research log and review"],
            "next_stage_criteria": ["audit artifact exists", "one bounded next route or stop decision is selected"],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2776 may audit source-only deltas but cannot by itself establish level3 self-identification.",
            "history_necessity_tests": ["audit only; no new tests in M2776"],
            "temporal_evidence_window": "M2772-M2775 source-only intervention branch",
            "negative_result_policy": "Preserve weak or ambiguous deltas instead of weakening self-ID gates.",
            "allowed_claims": [
                "M2775 artifacts are complete and claim-safe or incomplete",
                "no driver-performance verdict paper result high-fidelity validation full ideal driver or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a new source-only delta panel rather than extending same-surface repair",
            "paper_verdict_delta": "no paper verdict; audit may select whether delta artifacts justify synthesis or proof extension",
            "must_synthesize_if": [
                "M2776 cannot select a bounded follow-up route",
                "M2776 would claim self-ID or performance from source-only delta rows",
                "another no-new-data reanalysis is proposed after M2776 without synthesis",
            ],
        },
        "hypothesis": "M2775 source-only delta-panel artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{m2776_id}.md exists",
            "M2776 audits M2775 summary delta aggregate actor guard claim and gate artifacts",
            "M2776 preserves no ranking validation performance paper high-fidelity full-driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2776 executes new rollouts or training",
            "M2776 claims driver performance or self-ID",
            "M2776 fails to select a bounded next route or stop",
        ],
        "decision_rule": "Pass only if M2776 audits M2775 artifacts and selects a bounded next route without overclaiming.",
        "commands": [{"name": "audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{m2776_id}.md", "type": "md"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
        ],
        "baseline_artifacts": [str(run_dir / "summary.json"), str(summary["doc"])],
        "scoreboard_checkpoint": f"docs/{m2776_id}.md",
    }


def _write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "completed" if summary["status_pass"] else "failed"
    text = f"""# M2775 Engineering Controller Route A Source-Only Action-Response Belief Intervention Delta Panel Materialization

## Metadata

- status: {status}
- result class: `{summary['result_class']}`
- summary: `{summary['summary']}`
- source audit: `{summary['m2774_audit']}`
- source dir: `{summary['m2773_dir']}`
- follow-up manifest: `{summary['follow_up_manifest']}`
- next: `{summary['next_blocker']}`

## Artifact Accounting

```text
source candidate rows: {summary['source_candidate_row_count']}
source execution rows: {summary['source_execution_row_count']}
source trace rows: {summary['source_trace_row_count']}
normal execution rows: {summary['normal_execution_row_count']}
evaluator intervention execution rows: {summary['evaluator_intervention_execution_row_count']}
delta rows: {summary['intervention_delta_row_count']}
role/dynamics aggregate rows: {summary['role_dynamics_delta_aggregate_row_count']}
intervention-condition aggregate rows: {summary['intervention_condition_delta_aggregate_row_count']}
mitigation reference guard rows: {summary['mitigation_reference_guard_row_count']}
actor guard rows: {summary['actor_guard_row_count']}
claim boundary rows: {summary['claim_boundary_row_count']}
gate rows: {summary['gate_matrix_row_count']}
```

## Pairing Result

```text
pairing complete: {summary['pairing_complete']}
missing pair count: {summary['missing_pair_count']}
duplicate execution pair count: {summary['duplicate_execution_pair_count']}
trace pair accounting: {summary['trace_pair_accounting']}
matched trace pair rows: {summary['matched_trace_pair_row_count']}
expected matched trace pair rows: {summary['expected_matched_trace_pair_row_count']}
```

## Delta Diagnostic Summary

```text
collision added delta rows: {summary['collision_added_delta_row_count']}
collision removed delta rows: {summary['collision_removed_delta_row_count']}
road-departure added delta rows: {summary['road_departure_added_delta_row_count']}
road-departure removed delta rows: {summary['road_departure_removed_delta_row_count']}
minimum obstacle clearance delta mean: {summary['minimum_obstacle_clearance_m_delta_mean']:.6f}
minimum road margin delta mean: {summary['minimum_road_margin_m_delta_mean']:.6f}
trace delta proxy delta mean: {summary['trace_delta_proxy_delta_mean']:.6f}
command response proxy delta mean: {summary['command_response_proxy_delta_mean']:.6f}
action L1 mean: {summary['action_l1_mean']:.6f}
physical action L1 mean: {summary['physical_action_l1_mean']:.6f}
ego response L2 mean: {summary['ego_response_l2_mean']:.6f}
```

These are source-only diagnostic deltas. They are not success-rate verdicts,
controller ranking metrics, driver-performance measurements, paper evidence,
high-fidelity validation evidence, or self-ID proof.

## Actor And Claim Boundary

```text
actor contract 72/action 3: {summary['actor_contract_shape_72_action_3']}
hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}
actor-visible label detected: {summary['actor_visible_label_detected']}
mitigation reference rows guarded: {summary['mitigation_reference_rows_guarded']}
new execution run: {summary['new_execution_run']}
training run: {summary['training_run']}
ranking run: {summary['ranking_run']}
winner selected: {summary['winner_selected']}
success-rate verdict computed: {summary['success_rate_verdict_computed']}
driver-performance claim made: {summary['driver_performance_claim_made']}
self-ID claim made: {summary['level3_self_id_claim_made']}
```

## Route Decision

Route to M2776 result audit before interpreting whether these source-only
normal-vs-intervention deltas warrant synthesis, artifact repair,
proof-extension design, or branch stop.
"""
    path.write_text(text, encoding="utf-8")


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


def _mean(values: Any) -> float:
    seq = [float(value) for value in values]
    if not seq:
        return 0.0
    return float(sum(seq) / len(seq))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2774-audit", default=DEFAULT_M2774_AUDIT)
    parser.add_argument("--m2773-dir", default=str(DEFAULT_M2773_DIR))
    parser.add_argument("--follow-up-manifest", default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    args = parser.parse_args(argv)
    summary = materialize_source_only_action_response_belief_intervention_delta_panel(
        Path(args.output_dir),
        m2774_audit=args.m2774_audit,
        m2773_dir=args.m2773_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'} status_pass={summary['status_pass']}")
    raise SystemExit(0 if summary["status_pass"] else 1)


if __name__ == "__main__":
    main()
