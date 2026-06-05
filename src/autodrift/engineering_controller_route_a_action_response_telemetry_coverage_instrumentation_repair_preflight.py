"""M2762 evaluator-only action-response telemetry coverage repair preflight.

This milestone reanalyzes existing M2759 artifacts only. It does not reset or
step environments, execute policy actions, roll out policies, replay,
validate, train, run PPO, build source, probe adapters, run external
simulation, rank candidates, or promote checkpoints.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2762-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-preflight"
DEFAULT_NEXT_BLOCKER = (
    "m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit"
)
DEFAULT_M2759_DIR = Path(
    "runs/m2759_engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight"
)
DEFAULT_M2761_SYNTHESIS = Path(
    "docs/m2761-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-result-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2762-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit.json"
)

EXPECTED_ACTION_RESPONSE_ROWS = 12
EXPECTED_EXECUTION_ROWS = 12
EXPECTED_GUARDRAIL_ROWS = 31
CLAIM_SCOPE = (
    "M2762 Route A action-response telemetry coverage instrumentation repair preflight only; existing M2759 "
    "probe artifacts are reanalyzed into evaluator-only coverage gap and schema-contract rows while no reset, "
    "step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, "
    "winner selection, promotion, success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, controller-family ranking, source-edge "
    "ranking, stress-axis ranking, task-family ranking, profile ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 self-identification"
)

GAP_FIELDNAMES = [
    "coverage_gap_id",
    "probe_id",
    "probe_resolution_id",
    "candidate_id",
    "localization_id",
    "task_source_id",
    "failure_family",
    "incoming_finite_metric",
    "previous_command_present",
    "previous_command_finite",
    "previous_command_source_column",
    "previous_command_repair_rule",
    "plan_first_action_error_proxy_present",
    "plan_first_action_error_proxy_finite",
    "plan_first_action_error_source_column",
    "plan_first_action_error_repair_rule",
    "current_action_finite",
    "action_rate_mean_finite",
    "speed_response_proxy_finite",
    "yaw_response_proxy_finite",
    "beta_response_proxy_finite",
    "missing_required_proxy_count",
    "gap_class",
    "repair_status",
    "future_finite_metric_admitted_by_contract",
    "m2759_row_backfilled",
    "reset_step_rollout_required",
    "actor_visible_allowed",
    "hidden_oracle_actor_input_required",
    "actor_input_contract_changed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]

SCHEMA_CONTRACT_FIELDNAMES = [
    "contract_id",
    "telemetry_field",
    "output_column",
    "field_role",
    "required_for_finite_metric",
    "m2759_existing_status",
    "repair_source_layer",
    "repair_rule",
    "fallback_rule",
    "hidden_oracle_actor_input_required",
    "actor_visible_allowed",
    "actor_input_contract_changed",
    "reset_step_rollout_required",
    "schema_status_pass",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]

ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible_allowed",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2762",
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

FALSE_EXECUTION_OR_CLAIM_FLAGS = {
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "external_simulation_run": False,
    "private_holdout_used": False,
    "profile_specific_tuning": False,
    "active_config_overwritten": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_verdict_claim_made": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "level3_self_id_claim_made": False,
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _finite(value: Any) -> bool:
    return _float(value) is not None


def _any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def _count_finite(rows: list[Mapping[str, Any]], key: str) -> int:
    return sum(1 for row in rows if _finite(row.get(key)))


def _count_present(rows: list[Mapping[str, Any]], key: str) -> int:
    return sum(1 for row in rows if str(row.get(key, "")).strip() != "")


def path_map(output_dir: Path, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "telemetry_coverage_gap_rows": output_dir / "telemetry_coverage_gap_rows.csv",
        "telemetry_schema_contract_rows": output_dir / "telemetry_schema_contract_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source(m2759_dir: Path, m2761_synthesis: Path) -> dict[str, Any]:
    paths = {
        "m2759_summary": m2759_dir / "summary.json",
        "m2759_action_response_rows": m2759_dir / "action_response_probe_rows.csv",
        "m2759_probe_execution_rows": m2759_dir / "probe_execution_rows.csv",
        "m2759_guardrail_rows": m2759_dir / "guardrail_context_rows.csv",
        "m2759_actor_rows": m2759_dir / "actor_contract_guard_rows.csv",
        "m2759_claim_rows": m2759_dir / "claim_boundary_rows.csv",
        "m2759_gate_rows": m2759_dir / "gate_matrix.csv",
        "m2761_synthesis": m2761_synthesis,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2759_summary": read_json(paths["m2759_summary"]) if paths["m2759_summary"].exists() else {},
        "m2759_action_response_rows": read_csv_rows(paths["m2759_action_response_rows"]),
        "m2759_probe_execution_rows": read_csv_rows(paths["m2759_probe_execution_rows"]),
        "m2759_guardrail_rows": read_csv_rows(paths["m2759_guardrail_rows"]),
        "m2759_actor_rows": read_csv_rows(paths["m2759_actor_rows"]),
        "m2759_claim_rows": read_csv_rows(paths["m2759_claim_rows"]),
        "m2759_gate_rows": read_csv_rows(paths["m2759_gate_rows"]),
        "m2761_synthesis_text": paths["m2761_synthesis"].read_text(encoding="utf-8")
        if paths["m2761_synthesis"].exists()
        else "",
    }


def build_telemetry_coverage_gap_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    execution_by_resolution = {
        str(row.get("probe_resolution_id", "")): row for row in source["m2759_probe_execution_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["m2759_action_response_rows"], start=1):
        resolution_id = str(row.get("probe_resolution_id", ""))
        execution = execution_by_resolution.get(resolution_id, {})
        previous_finite = _finite(row.get("previous_command"))
        plan_finite = _finite(row.get("plan_first_action_error_proxy"))
        missing_required = int(not previous_finite) + int(not plan_finite)
        if not previous_finite and not plan_finite:
            gap_class = "previous_command_and_plan_first_action_missing"
        elif not previous_finite:
            gap_class = "previous_command_missing"
        elif not plan_finite:
            gap_class = "plan_first_action_missing"
        else:
            gap_class = "no_required_proxy_gap"
        rows.append(
            {
                "coverage_gap_id": f"m2762-telemetry-coverage-gap-{index:04d}",
                "probe_id": row.get("probe_id", ""),
                "probe_resolution_id": resolution_id,
                "candidate_id": row.get("candidate_id", execution.get("candidate_id", "")),
                "localization_id": row.get("localization_id", execution.get("localization_id", "")),
                "task_source_id": row.get("task_source_id", execution.get("task_source_id", "")),
                "failure_family": row.get("failure_family", execution.get("failure_family", "")),
                "incoming_finite_metric": _bool(row.get("finite_metric", False)),
                "previous_command_present": str(row.get("previous_command", "")).strip() != "",
                "previous_command_finite": previous_finite,
                "previous_command_source_column": "action_response.previous_command_from_m2759_plan_action_rate_mean",
                "previous_command_repair_rule": (
                    "future evaluator records previous physical command from policy/action trace before the current "
                    "action; first step uses initial actuator state or explicit zero-command bootstrap marker"
                ),
                "plan_first_action_error_proxy_present": str(row.get("plan_first_action_error_proxy", "")).strip() != "",
                "plan_first_action_error_proxy_finite": plan_finite,
                "plan_first_action_error_source_column": "probe_execution.plan_first_action_error_mean",
                "plan_first_action_error_repair_rule": (
                    "future evaluator records explicit first planned action error when a planner trace exists; "
                    "otherwise records finite current_action_minus_previous_command trace-delta proxy with source marker"
                ),
                "current_action_finite": _finite(row.get("current_action")),
                "action_rate_mean_finite": _finite(row.get("action_rate_mean")),
                "speed_response_proxy_finite": _finite(row.get("speed_response_proxy")),
                "yaw_response_proxy_finite": _finite(row.get("yaw_response_proxy")),
                "beta_response_proxy_finite": _finite(row.get("beta_response_proxy")),
                "missing_required_proxy_count": missing_required,
                "gap_class": gap_class,
                "repair_status": "schema_contract_materialized_not_backfilled",
                "future_finite_metric_admitted_by_contract": True,
                "m2759_row_backfilled": False,
                "reset_step_rollout_required": False,
                "actor_visible_allowed": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_telemetry_schema_contract_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    action_rows = source["m2759_action_response_rows"]
    previous_finite_count = _count_finite(action_rows, "previous_command")
    plan_error_finite_count = _count_finite(action_rows, "plan_first_action_error_proxy")
    current_action_finite_count = _count_finite(action_rows, "current_action")
    count = len(action_rows)
    contracts = [
        (
            "previous_physical_command",
            "previous_command",
            "required finite command-response baseline before current action",
            True,
            f"finite {previous_finite_count}/{count}; blank {count - _count_present(action_rows, 'previous_command')}/{count}",
            "policy_action_trace_or_actuator_command_history",
            "record command applied immediately before current action as evaluator telemetry",
            "for first action record initial actuator state if available else explicit zero-command bootstrap marker",
        ),
        (
            "current_policy_action",
            "current_action",
            "finite current action proxy already present in M2759 rows",
            True,
            f"finite {current_action_finite_count}/{count}",
            "policy_action_trace",
            "preserve current action scalar/vector proxy as evaluator-only telemetry",
            "if action trace is absent keep finite_metric false and emit missing_reason",
        ),
        (
            "plan_first_action_or_trace_delta",
            "plan_first_action_error_proxy",
            "finite first-action change proxy needed for action-response interpretation",
            True,
            f"finite {plan_error_finite_count}/{count}; blank {count - _count_present(action_rows, 'plan_first_action_error_proxy')}/{count}",
            "planner_trace_or_policy_action_trace_delta",
            "record first planned action error when planner trace exists; otherwise record current_action_minus_previous_command trace delta",
            "if neither source exists keep finite_metric false and emit missing_reason",
        ),
        (
            "actuator_lag_proxy",
            "actuator_lag_proxy",
            "finite evaluator-only proxy derived from command/action trace and actuator state",
            False,
            f"finite {_count_finite(action_rows, 'actuator_lag_proxy')}/{count}",
            "actuator_state_and_command_trace",
            "derive lag proxy from actuator state response to finite previous/current command",
            "not required for finite_metric until actuator trace exists",
        ),
        (
            "command_response_phase_lag_proxy",
            "command_response_phase_lag_proxy",
            "derived phase-lag summary must not hide missing base fields",
            False,
            f"finite {_count_finite(action_rows, 'command_response_phase_lag_proxy')}/{count}",
            "derived_evaluator_metric",
            "compute only after previous_command and plan_first_action_error_proxy source status is explicit",
            "mark derived_from_partial_inputs if any base field is missing",
        ),
        (
            "finite_metric",
            "finite_metric",
            "aggregate coverage flag for mechanism interpretation",
            True,
            f"true {sum(1 for row in action_rows if _bool(row.get('finite_metric', False)))}/{count}",
            "schema_contract_aggregate",
            "set true only when previous_command current_action plan_first_action_error_proxy and response proxies are finite",
            "otherwise false with per-field gap rows",
        ),
    ]
    rows = []
    for index, (
        telemetry_field,
        output_column,
        field_role,
        required,
        existing_status,
        source_layer,
        repair_rule,
        fallback_rule,
    ) in enumerate(contracts, start=1):
        rows.append(
            {
                "contract_id": f"m2762-telemetry-schema-contract-{index:04d}",
                "telemetry_field": telemetry_field,
                "output_column": output_column,
                "field_role": field_role,
                "required_for_finite_metric": required,
                "m2759_existing_status": existing_status,
                "repair_source_layer": source_layer,
                "repair_rule": repair_rule,
                "fallback_rule": fallback_rule,
                "hidden_oracle_actor_input_required": False,
                "actor_visible_allowed": False,
                "actor_input_contract_changed": False,
                "reset_step_rollout_required": False,
                "schema_status_pass": True,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def actor_contract_preserved(source: dict[str, Any]) -> tuple[bool, bool]:
    obs_ok = False
    action_ok = False
    for row in source["m2759_actor_rows"]:
        if str(row.get("guard_family", "")) == "p0_observation_dim":
            obs_ok = (
                str(row.get("observed", "")) == str(P0_OBSERVATION_DIM)
                and str(row.get("expected", "")) == str(P0_OBSERVATION_DIM)
                and _bool(row.get("status_pass", False))
            )
        if str(row.get("guard_family", "")) == "action_dim":
            action_ok = (
                str(row.get("observed", "")) == str(ACTION_DIM)
                and str(row.get("expected", "")) == str(ACTION_DIM)
                and _bool(row.get("status_pass", False))
            )
    return obs_ok, action_ok


def actor_guard(guard_id: str, family: str, observed: Any, expected: Any, status: bool) -> dict[str, Any]:
    return {
        "guard_id": guard_id,
        "guard_family": family,
        "observed": observed,
        "expected": expected,
        "status_pass": bool(status),
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_actor_contract_guard_rows(
    source: dict[str, Any],
    gap_rows: list[Mapping[str, Any]],
    schema_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    obs_ok, action_ok = actor_contract_preserved(source)
    source_rows = source["m2759_action_response_rows"] + source["m2759_probe_execution_rows"]
    checks = [
        ("p0_observation_dim", P0_OBSERVATION_DIM if obs_ok else "missing_or_failed", P0_OBSERVATION_DIM, obs_ok),
        ("action_dim", ACTION_DIM if action_ok else "missing_or_failed", ACTION_DIM, action_ok),
        (
            "hidden_oracle_actor_input_detected",
            _any_flag(gap_rows + schema_rows + source_rows, "hidden_oracle_actor_input_required"),
            False,
            not _any_flag(gap_rows + schema_rows + source_rows, "hidden_oracle_actor_input_required"),
        ),
        (
            "actor_input_contract_changed",
            _any_flag(gap_rows + schema_rows + source_rows, "actor_input_contract_changed"),
            False,
            not _any_flag(gap_rows + schema_rows + source_rows, "actor_input_contract_changed"),
        ),
        (
            "telemetry_labels_actor_visible",
            _any_flag(gap_rows + schema_rows, "actor_visible_allowed"),
            False,
            not _any_flag(gap_rows + schema_rows, "actor_visible_allowed"),
        ),
        (
            "guardrails_actor_visible",
            _any_flag(source["m2759_guardrail_rows"], "actor_visible_allowed"),
            False,
            not _any_flag(source["m2759_guardrail_rows"], "actor_visible_allowed"),
        ),
    ]
    return [
        actor_guard(f"m2762-actor-guard-{index:04d}", family, observed, expected, status)
        for index, (family, observed, expected, status) in enumerate(checks, start=1)
    ]


def build_claim_boundary_rows(
    *,
    gap_rows_written: bool,
    schema_rows_written: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    claims = [
        ("telemetry_coverage_gap_materialized", True, gap_rows_written, "M2762 coverage gap rows"),
        ("telemetry_schema_contract_materialized", True, schema_rows_written, "M2762 schema contract rows"),
        ("result_audit_follow_up_registered", True, follow_up_manifest_registered, "M2763 result-audit manifest"),
        ("m2759_row_backfill", False, False, "new bounded execution with repaired evaluator telemetry"),
        ("repair_success", False, False, "separate repair design execution and audit"),
        ("driver_performance", False, False, "separate validation and promotion gates"),
        ("validation_readiness", False, False, "separate validation-readiness gate"),
        ("validation_result", False, False, "separate validation execution"),
        ("ranking_or_winner_selection", False, False, "separate controller-family comparison and ranking protocol"),
        ("checkpoint_promotion", False, False, "separate promotion gate"),
        ("paper_evidence", False, False, "separate paper route proof/generalization matrix"),
        ("finite_window_vs_gru", False, False, "separate controlled family comparison"),
        ("current_sim_verdict", False, False, "separate current-sim benchmark verdict gate"),
        ("high_fidelity_validation", False, False, "separate high-fidelity interface and validation route"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_identification", False, False, "closed-loop self-identification proof gate"),
    ]
    return [
        {
            "claim_id": f"m2762-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m2762": allowed,
            "claim_made": made,
            "status_pass": bool((allowed and made) or (not allowed and not made)),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def gate_row(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2762-gate-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    gap_rows: list[dict[str, Any]],
    schema_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest_registered: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    action_rows = source["m2759_action_response_rows"]
    execution_rows = source["m2759_probe_execution_rows"]
    guardrail_rows = source["m2759_guardrail_rows"]
    incoming_false_count = sum(1 for row in action_rows if not _bool(row.get("finite_metric", False)))
    previous_gap_count = sum(1 for row in gap_rows if not _bool(row["previous_command_finite"]))
    plan_gap_count = sum(1 for row in gap_rows if not _bool(row["plan_first_action_error_proxy_finite"]))
    forbidden_flag = any(_any_flag([row], key) for key in FALSE_EXECUTION_OR_CLAIM_FLAGS for row in gap_rows + schema_rows)
    return [
        gate_row("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "M2759 artifacts and M2761 synthesis present", "lineage_invalid"),
        gate_row("m2759_summary_status_pass", "lineage", _bool(source["m2759_summary"].get("status_pass", False)), source["m2759_summary"].get("status_pass", False), True, "lineage_invalid"),
        gate_row("m2761_synthesis_selects_m2762", "lineage", "m2762" in source["m2761_synthesis_text"], "m2762" in source["m2761_synthesis_text"], True, "lineage_invalid"),
        gate_row("action_response_rows_accounted", "telemetry", len(action_rows) == EXPECTED_ACTION_RESPONSE_ROWS, len(action_rows), EXPECTED_ACTION_RESPONSE_ROWS, "metric_artifact"),
        gate_row("execution_rows_accounted", "telemetry", len(execution_rows) == EXPECTED_EXECUTION_ROWS, len(execution_rows), EXPECTED_EXECUTION_ROWS, "lineage_invalid"),
        gate_row("coverage_gap_rows_accounted", "telemetry", len(gap_rows) == len(action_rows), len(gap_rows), len(action_rows), "metric_artifact"),
        gate_row("incoming_finite_metric_false_preserved", "telemetry", incoming_false_count == len(action_rows), incoming_false_count, len(action_rows), "metric_artifact"),
        gate_row("previous_command_gap_materialized", "telemetry", previous_gap_count == len(action_rows), previous_gap_count, len(action_rows), "metric_artifact"),
        gate_row("plan_first_action_gap_materialized", "telemetry", plan_gap_count == len(action_rows), plan_gap_count, len(action_rows), "metric_artifact"),
        gate_row("schema_contract_rows_present", "telemetry", len(schema_rows) >= 6, len(schema_rows), ">=6", "metric_artifact"),
        gate_row("schema_contract_actor_invisible", "contract", not _any_flag(schema_rows, "actor_visible_allowed"), _any_flag(schema_rows, "actor_visible_allowed"), False, "contract_violation"),
        gate_row("schema_contract_no_hidden_oracle", "contract", not _any_flag(schema_rows, "hidden_oracle_actor_input_required"), _any_flag(schema_rows, "hidden_oracle_actor_input_required"), False, "contract_violation"),
        gate_row("schema_contract_no_actor_change", "contract", not _any_flag(schema_rows, "actor_input_contract_changed"), _any_flag(schema_rows, "actor_input_contract_changed"), False, "contract_violation"),
        gate_row("schema_contract_no_reset_rollout_required", "contract", not _any_flag(schema_rows + gap_rows, "reset_step_rollout_required"), _any_flag(schema_rows + gap_rows, "reset_step_rollout_required"), False, "proof_washout"),
        gate_row("guardrail_rows_carried", "guardrail", len(guardrail_rows) == EXPECTED_GUARDRAIL_ROWS, len(guardrail_rows), EXPECTED_GUARDRAIL_ROWS, "lineage_invalid"),
        gate_row("guardrails_not_executed", "guardrail", not _any_flag(guardrail_rows, "execution_run"), _any_flag(guardrail_rows, "execution_run"), False, "proof_washout"),
        gate_row("guardrails_outside_denominator", "guardrail", not _any_flag(guardrail_rows, "ordinary_success_denominator_allowed") and not _any_flag(guardrail_rows, "protected_rows_in_success_denominator"), "ordinary_or_protected_denominator_present" if (_any_flag(guardrail_rows, "ordinary_success_denominator_allowed") or _any_flag(guardrail_rows, "protected_rows_in_success_denominator")) else False, False, "proof_washout"),
        gate_row("actor_contract_guards_pass", "contract", all(_bool(row["status_pass"]) for row in actor_guard_rows), "all_pass" if all(_bool(row["status_pass"]) for row in actor_guard_rows) else actor_guard_rows, "all_pass", "contract_violation"),
        gate_row("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all_pass" if all(_bool(row["status_pass"]) for row in claim_rows) else claim_rows, "all_pass", "proof_washout"),
        gate_row("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
        gate_row("forbidden_execution_false", "claim", not forbidden_flag, forbidden_flag, False, "proof_washout"),
        gate_row("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    gap_rows: list[dict[str, Any]],
    schema_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    action_rows = source["m2759_action_response_rows"]
    execution_rows = source["m2759_probe_execution_rows"]
    guardrail_rows = source["m2759_guardrail_rows"]
    incoming_finite_true = sum(1 for row in action_rows if _bool(row.get("finite_metric", False)))
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in execution_rows)
    status_pass = bool(required_artifacts_present and all(_bool(row["status_pass"]) for row in gate_rows))
    return {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight_fail"
        ),
        "status_pass": status_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "m2759_action_response_row_count": len(action_rows),
        "m2759_probe_execution_row_count": len(execution_rows),
        "m2759_guardrail_row_count": len(guardrail_rows),
        "m2759_incoming_finite_metric_true_count": incoming_finite_true,
        "m2759_incoming_finite_metric_false_count": len(action_rows) - incoming_finite_true,
        "previous_command_missing_count": sum(1 for row in gap_rows if not _bool(row["previous_command_finite"])),
        "plan_first_action_error_missing_count": sum(1 for row in gap_rows if not _bool(row["plan_first_action_error_proxy_finite"])),
        "telemetry_coverage_gap_row_count": len(gap_rows),
        "telemetry_schema_contract_row_count": len(schema_rows),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_row_count": len(gate_rows),
        "gate_matrix_pass": all(_bool(row["status_pass"]) for row in gate_rows),
        "required_artifacts_present": required_artifacts_present,
        "m2759_rows_backfilled": False,
        "telemetry_coverage_repair_admitted": status_pass,
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "guardrail_execution": _any_flag(guardrail_rows, "execution_run"),
        "protected_rows_in_success_denominator": _any_flag(guardrail_rows, "protected_rows_in_success_denominator"),
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "telemetry_labels_actor_visible": False,
        "reset_step_rollout_required": False,
        **FALSE_EXECUTION_OR_CLAIM_FLAGS,
        "source_exists": source["source_exists"],
        "next_blocker": next_blocker,
        "follow_up_manifest": str(follow_up_manifest),
        "artifacts": {key: str(value) for key, value in paths.items()},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def render_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2762 Engineering Controller Route A Action-Response Telemetry Coverage Instrumentation Repair Preflight",
            "",
            "## Metadata",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- M2759 action-response rows: {summary['m2759_action_response_row_count']}",
            f"- M2759 execution rows: {summary['m2759_probe_execution_row_count']}",
            f"- incoming finite_metric false rows: {summary['m2759_incoming_finite_metric_false_count']}",
            f"- previous-command missing/finite-gap rows: {summary['previous_command_missing_count']}",
            f"- plan-first-action missing/finite-gap rows: {summary['plan_first_action_error_missing_count']}",
            f"- telemetry coverage gap rows: {summary['telemetry_coverage_gap_row_count']}",
            f"- telemetry schema contract rows: {summary['telemetry_schema_contract_row_count']}",
            f"- guardrail rows preserved: {summary['m2759_guardrail_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
            "## Result",
            "",
            "M2762 materializes the M2759 telemetry coverage gap without altering",
            "M2759 rows. All 12 incoming action-response rows keep their original",
            "`finite_metric=False` interpretation. The repair is a forward schema",
            "contract: future evaluator probes must record finite previous-command",
            "and plan-first-action or trace-delta proxies as evaluator-only telemetry.",
            "",
            "## Boundary",
            "",
            "M2762 does not execute reset, step, policy action, rollout, replay,",
            "validation, training, PPO, source build, adapter probe, external",
            "simulation, ranking, winner selection, promotion, or success-rate",
            "verdict computation. It does not change actor inputs, action shape,",
            "or the deployed human-view contract. Coverage labels remain",
            "actor-invisible.",
            "",
            "## Claim Boundary",
            "",
            "```text",
            summary["claim_scope"],
            "```",
            "",
            "## Forbidden Interpretation",
            "",
            "```text",
            summary["forbidden_interpretation"],
            "```",
            "",
        ]
    )


def write_follow_up_manifest(path: Path) -> None:
    manifest_id = "m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit"
    write_json(
        path,
        {
            "id": manifest_id,
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
            ],
            "lineage": {
                "parent_checkpoint": [
                    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
                ],
                "parent_dataset": [
                    "docs/m2762-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-preflight.md",
                    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight/summary.json",
                    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight/telemetry_coverage_gap_rows.csv",
                    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight/telemetry_schema_contract_rows.csv",
                    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight/actor_contract_guard_rows.csv",
                    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight/claim_boundary_rows.csv",
                    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight/gate_matrix.csv",
                    "docs/m2761-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-result-synthesis.md",
                    "runs/m2759_engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight/action_response_probe_rows.csv",
                ],
                "parent_config": [
                    "experiments/manifests/m2762-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-preflight.json",
                    "experiments/manifests/m2761-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-result-synthesis.json",
                ],
                "parent_objective": [
                    "audit M2762 telemetry coverage instrumentation repair artifacts before another probe repair design validation ranking or performance route"
                ],
                "derived_from": [
                    "m2762-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-preflight",
                    "m2761-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-result-synthesis",
                    "m2759-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-bounded-execution-preflight",
                ],
                "blocked_by": [
                    "M2762 telemetry coverage repair artifacts require audit before future action-response probe interpretation",
                    "M2759 incoming finite_metric false rows must remain visible and not be backfilled",
                    "actor 72/action 3 no hidden-oracle and actor-invisible telemetry labels must be preserved",
                ],
                "supersedes": [
                    "direct containment repair before telemetry coverage audit",
                    "same-surface action-response mechanism ranking before finite proxy coverage is audited",
                    "success-rate performance validation paper current-sim high-fidelity full-driver or self-ID interpretation from M2762",
                ],
                "invalidates": [],
            },
            "review_artifact": "docs/reviews/m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit.md",
            "public_gates": [
                "M2763 must audit M2762 summary coverage gap schema actor claim gate and doc artifacts before selecting a follow-up",
                "M2763 must verify all 12 M2759 action-response rows remain accounted and original finite_metric False evidence is not hidden",
                "M2763 must verify telemetry schema contract rows are evaluator-only actor-invisible and require no hidden/oracle actor input",
                "M2763 must verify M2762 did not execute reset step rollout replay validation training PPO source build adapter probe external simulation ranking winner promotion or success-rate verdict computation",
                "M2763 must reject repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion and self-ID claims",
                "M2763 must select one bounded follow-up route before any new execution repair validation ranking or performance claim",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not execute reset",
                "do not step environments",
                "do not execute policy action",
                "do not execute policy rollout",
                "do not execute replay",
                "do not execute measured validation",
                "do not train",
                "do not run PPO",
                "do not execute source build",
                "do not execute adapter probe",
                "do not execute external simulation",
                "do not promote a checkpoint",
                "do not use private holdout",
                "do not change actor inputs",
                "do not expose telemetry coverage action-response containment mechanism protected blocker route progress or verdict labels to actor input",
                "do not hide M2759 finite_metric False coverage gaps",
                "do not rank controller families source edges stress axes profiles task families mechanism tags or candidates",
                "do not claim repair success driver performance validation readiness/result paper current-sim high-fidelity full ideal driver or self-ID evidence",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair",
                "evidence_axis": "route_a_action_response_telemetry_coverage_instrumentation_repair_result_audit",
                "evidence_increment": "audits evaluator-only telemetry coverage repair artifacts before another probe or containment repair route",
                "claim_scope": "Result audit only; no reset rollout replay validation training PPO ranking winner selection promotion success-rate verdict repair-success driver-performance paper finite-window-vs-GRU current-sim high-fidelity validation self-ID or full ideal driver claim",
                "stop_condition": [
                    "stop if M2762 artifacts are missing or gate matrix fails",
                    "stop if M2762 hides M2759 finite_metric False rows",
                    "stop if telemetry labels become actor-visible or require hidden/oracle actor input",
                    "stop if audit wording ranks candidates mechanism tags source edges stress axes profiles task families or controllers",
                    "stop if audit would claim validation performance paper current-sim high-fidelity full-driver or self-ID evidence",
                ],
                "fallback_plan": [
                    "route to artifact repair if M2762 outputs are incomplete",
                    "route back to instrumentation repair if schema contract is incomplete",
                    "route to bounded probe design only after M2762 artifacts are accepted as claim-safe",
                    "route to synthesis if audit cannot identify a bounded evidence-changing follow-up",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2762 writes telemetry coverage instrumentation repair artifacts and requires audit before future probe interpretation",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "evaluation_only",
                "stage_objective": "action-response telemetry coverage instrumentation repair result audit",
                "admission_evidence": [
                    "M2762 is expected to write evaluator-only telemetry coverage gap and schema contract artifacts",
                    "M2761 selected telemetry coverage repair before direct containment repair",
                    "M2759 action-response finite proxy coverage was incomplete",
                ],
                "blocked_shortcuts": [
                    "no reset step policy action rollout replay validation training PPO in M2763",
                    "no source build adapter probe external simulation",
                    "no ranking winner selection promotion success-rate verdict",
                    "no repair success driver-performance validation-readiness paper current-sim high-fidelity full ideal driver or self-ID claim",
                ],
                "allowed_updates": [
                    "docs/m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit.md",
                    "M2763 status queue scoreboard research log and review",
                    "one bounded follow-up manifest selected by the audit",
                ],
                "next_stage_criteria": [
                    "M2762 summary and gates are audited",
                    "telemetry coverage gap and schema contract artifacts are audited",
                    "actor guardrail and claim boundaries are preserved",
                    "one bounded follow-up route is selected",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": "M2763 audits Route A telemetry coverage repair artifacts and does not test history necessity or current-frame substitution.",
                "history_necessity_tests": [
                    "None in M2763; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": "M2759-M2762 Route A action-response containment probe and telemetry coverage artifacts only.",
                "negative_result_policy": "If M2762 coverage repair is incomplete preserve the blocker and route to artifact repair or synthesis rather than forcing self-ID interpretation.",
                "allowed_claims": [
                    "M2762 telemetry coverage repair artifacts are complete and claim-safe or explicitly rejected",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "medium",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 1,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits telemetry coverage repair artifacts before admitting another execution or repair route",
                "paper_verdict_delta": "no paper verdict; prevents telemetry coverage artifacts from being overinterpreted as mechanism performance or self-ID evidence",
                "must_synthesize_if": [
                    "M2763 rejects M2762 as incomplete or boundary-unsafe",
                    "M2763 accepts M2762 but no bounded evidence-changing follow-up exists",
                    "M2763 would claim repair success driver performance validation readiness paper evidence current-sim high-fidelity or self-ID",
                    "M2763 would rank controllers source edges profiles stress axes mechanism tags select a winner promote a checkpoint or compute success-rate verdict",
                ],
            },
            "hypothesis": "M2762 telemetry coverage instrumentation repair artifacts can be audited as complete and claim-safe before selecting the next Route A evidence-changing step.",
            "success_criteria": [
                "docs/m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit.md exists",
                "audit cites M2762 summary coverage gap schema actor claim and gate artifacts",
                "audit verifies all 12 M2759 action-response rows remain accounted and original finite_metric False evidence remains visible",
                "audit verifies schema contract labels are evaluator-only actor-invisible and require no hidden/oracle actor input",
                "audit rejects ranking repair success performance validation paper current-sim high-fidelity full ideal driver and self-ID claims",
                "audit registers one bounded follow-up route if continuing",
            ],
            "failure_criteria": [
                "M2763 executes reset step policy action rollout replay validation training PPO source build adapter probe external simulation or private holdout",
                "M2763 changes actor input or action contract",
                "M2763 exposes telemetry coverage action-response containment mechanism protected blocker route progress or verdict labels to actor input",
                "M2763 ranks controller families stress axes source edges profiles task families mechanism tags selects a winner promotes a checkpoint or claims driver performance",
                "M2763 fails to select a bounded next route",
            ],
            "decision_rule": "Pass only if M2763 verifies M2762 coverage repair artifacts are complete claim-safe and preserve actor guardrail and claim boundaries before any future execution or repair interpretation.",
            "commands": [
                {
                    "name": "route_a_action_response_telemetry_coverage_instrumentation_repair_result_audit",
                    "command": "true",
                }
            ],
            "required_artifacts": [
                {
                    "path": "docs/m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit.md",
                    "type": "md",
                }
            ],
            "baseline_checkpoints": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
            ],
            "baseline_artifacts": [
                "docs/m2762-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-preflight.md",
                "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight/summary.json",
            ],
        },
    )


def run(
    *,
    m2759_dir: Path = DEFAULT_M2759_DIR,
    m2761_synthesis: Path = DEFAULT_M2761_SYNTHESIS,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DEFAULT_DOC_PATH,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = path_map(output_dir, doc_path)
    source = load_source(m2759_dir, m2761_synthesis)
    write_follow_up_manifest(follow_up_manifest)
    gap_rows = build_telemetry_coverage_gap_rows(source)
    schema_rows = build_telemetry_schema_contract_rows(source)
    actor_guard_rows = build_actor_contract_guard_rows(source, gap_rows, schema_rows)
    write_csv_rows(paths["telemetry_coverage_gap_rows"], gap_rows, fieldnames=GAP_FIELDNAMES)
    write_csv_rows(paths["telemetry_schema_contract_rows"], schema_rows, fieldnames=SCHEMA_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    required_before_gate = all(
        paths[key].exists()
        for key in (
            "telemetry_coverage_gap_rows",
            "telemetry_schema_contract_rows",
            "actor_contract_guard_rows",
        )
    )
    claim_rows = build_claim_boundary_rows(
        gap_rows_written=paths["telemetry_coverage_gap_rows"].exists(),
        schema_rows_written=paths["telemetry_schema_contract_rows"].exists(),
        follow_up_manifest_registered=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    required_before_gate = required_before_gate and paths["claim_boundary_rows"].exists()
    gate_rows = build_gate_matrix_rows(
        source=source,
        gap_rows=gap_rows,
        schema_rows=schema_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        follow_up_manifest_registered=follow_up_manifest.exists(),
        required_artifacts_present=required_before_gate,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    required_for_summary = required_before_gate and paths["gate_matrix"].exists()
    summary = build_summary(
        output_dir=output_dir,
        paths=paths,
        source=source,
        gap_rows=gap_rows,
        schema_rows=schema_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_for_summary,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up_manifest,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    summary["artifacts"] = {key: str(value) for key, value in paths.items()}
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2759-dir", type=Path, default=DEFAULT_M2759_DIR)
    parser.add_argument("--m2761-synthesis", type=Path, default=DEFAULT_M2761_SYNTHESIS)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    summary = run(
        m2759_dir=args.m2759_dir,
        m2761_synthesis=args.m2761_synthesis,
        follow_up_manifest=args.follow_up_manifest,
        output_dir=args.output_dir,
        doc_path=args.doc,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['artifacts']['summary']}")


if __name__ == "__main__":
    main()
