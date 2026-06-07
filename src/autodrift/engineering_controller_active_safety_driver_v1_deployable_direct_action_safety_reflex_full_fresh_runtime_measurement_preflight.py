"""Run M3090 deployable safety-reflex full-fresh runtime measurement preflight."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.active_safety_reflex_driver import ACTION_COMPONENTS, DRIVER_ID, OUTPUT_SEMANTICS, ActiveSafetyReflexDriver
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088


MILESTONE_ID = (
    "m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-full-fresh-runtime-measurement-preflight"
)
NEXT_ID = (
    "m3091-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-full-fresh-runtime-measurement-result-audit"
)
M3089_ID = (
    "m3089-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-smoke-measurement-result-audit"
)
M3088_ID = (
    "m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-smoke-measurement-preflight"
)
M3086_ID = (
    "m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-contract-materialization-preflight"
)
M3084_ID = (
    "m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-fresh-robustness-measurement-preflight"
)

DEFAULT_M3089_AUDIT = Path(f"docs/{M3089_ID}.md")
DEFAULT_M3088_DIR = Path(
    "runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_"
    "safety_reflex_runtime_smoke_measurement_preflight"
)
DEFAULT_M3086_DIR = Path(
    "runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_"
    "safety_reflex_runtime_contract_materialization_preflight"
)
DEFAULT_M3084_DIR = Path(
    "runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_fresh_robustness_measurement_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3090_engineering_controller_active_safety_driver_v1_deployable_direct_action_"
    "safety_reflex_full_fresh_runtime_measurement_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_FULL_ROWS = 64
EXPECTED_AXIS_COUNT = 4
EXPECTED_BINDING_ROLE_COUNT = 2
CLAIM_SCOPE = (
    "M3090 Active Safety Driver v1 deployable direct-action safety-reflex full-fresh "
    "runtime measurement preflight only; the complete M3084 fresh current-sim denominator "
    "may be executed through ActiveSafetyReflexDriver.act as the full obs72-to-action3 "
    "action source and measurement, parity, contract, claim, gate, doc, and M3091 audit "
    "artifacts may be written. No validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, driver-performance verdict, current-sim verdict, "
    "repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, "
    "high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU "
    "conclusion, full ideal driver completion, or level3 self-identification"
)

PARITY_FIELDNAMES = [
    "parity_id",
    "runtime_smoke_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "m3084_policy",
    "runtime_policy",
    "m3084_success",
    "runtime_success",
    "success_match",
    "m3084_collision",
    "runtime_collision",
    "collision_match",
    "m3084_termination_reason",
    "runtime_termination_reason",
    "termination_reason_match",
    "m3084_outcome_bucket",
    "runtime_outcome_bucket",
    "outcome_bucket_match",
    "m3084_min_clearance_margin",
    "runtime_min_clearance_margin",
    "clearance_margin_abs_delta",
    "m3084_return",
    "runtime_return",
    "return_abs_delta",
    "m3084_action_rate_mean",
    "runtime_action_rate_mean",
    "action_rate_abs_delta",
    "m3084_raw_action_abs_max",
    "runtime_raw_action_abs_max",
    "raw_action_abs_max_delta",
    "exact_seed_match",
    "runtime_driver_id",
    "parity_result_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3090",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]


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


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "runtime_measurement_episode_rows": output_dir / "runtime_measurement_episode_rows.csv",
        "runtime_measurement_failure_rows": output_dir / "runtime_measurement_failure_rows.csv",
        "runtime_measurement_metric_summary_rows": output_dir / "runtime_measurement_metric_summary_rows.csv",
        "runtime_measurement_contract_guard_rows": output_dir / "runtime_measurement_contract_guard_rows.csv",
        "runtime_parity_rows": output_dir / "runtime_parity_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3089_audit: Path,
    m3088_dir: Path,
    m3086_dir: Path,
    m3084_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3089_audit": m3089_audit,
        "m3088_summary": m3088_dir / "summary.json",
        "m3088_gate_rows": m3088_dir / "gate_matrix.csv",
        "m3088_episode_rows": m3088_dir / "runtime_smoke_episode_rows.csv",
        "m3086_summary": m3086_dir / "summary.json",
        "m3086_contract": m3086_dir / "deployable_driver_contract.json",
        "m3086_interface_rows": m3086_dir / "driver_interface_rows.csv",
        "m3086_probe_rows": m3086_dir / "driver_action_probe_rows.csv",
        "m3086_exclusion_rows": m3086_dir / "actor_input_exclusion_rows.csv",
        "m3086_claim_rows": m3086_dir / "claim_boundary_rows.csv",
        "m3086_gate_rows": m3086_dir / "gate_matrix.csv",
        "m3084_summary": m3084_dir / "summary.json",
        "m3084_measurement_rows": m3084_dir / "measurement_episode_rows.csv",
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3089_audit_text": paths["m3089_audit"].read_text(encoding="utf-8") if exists["m3089_audit"] else "",
        "m3088_summary": read_json(paths["m3088_summary"]) if exists["m3088_summary"] else {},
        "m3088_gate_rows": read_csv_rows(paths["m3088_gate_rows"]),
        "m3088_episode_rows": read_csv_rows(paths["m3088_episode_rows"]),
        "m3086_summary": read_json(paths["m3086_summary"]) if exists["m3086_summary"] else {},
        "m3086_contract": read_json(paths["m3086_contract"]) if exists["m3086_contract"] else {},
        "m3086_interface_rows": read_csv_rows(paths["m3086_interface_rows"]),
        "m3086_probe_rows": read_csv_rows(paths["m3086_probe_rows"]),
        "m3086_exclusion_rows": read_csv_rows(paths["m3086_exclusion_rows"]),
        "m3086_claim_rows": read_csv_rows(paths["m3086_claim_rows"]),
        "m3086_gate_rows": read_csv_rows(paths["m3086_gate_rows"]),
        "m3084_summary": read_json(paths["m3084_summary"]) if exists["m3084_summary"] else {},
        "m3084_measurement_rows": read_csv_rows(paths["m3084_measurement_rows"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def full_fresh_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = sorted(source["m3084_measurement_rows"], key=lambda row: str(row.get("measurement_episode_id", "")))
    workloads = {str(row.get("executable_workload_id", "")): row for row in source["m3012_workload_rows"]}
    plan: list[dict[str, Any]] = []
    for source_row in rows:
        workload = workloads.get(str(source_row.get("executable_workload_id", "")), {})
        config_path = str(workload.get("config_path", ""))
        eval_seed = int(source_row.get("eval_seed", 0))
        hidden_label_violation = any(
            _bool(source_row.get(field, False)) or _bool(workload.get(field, False))
            for field in (
                "hidden_oracle_actor_input_required",
                "target_labels_actor_visible",
                "target_provenance_actor_visible",
                "source_labels_actor_visible",
                "route_labels_actor_visible",
                "outcome_labels_actor_visible",
                "success_progress_labels_actor_visible",
                "verdict_labels_actor_visible",
                "ttc_actor_input_required",
            )
        )
        status_pass = bool(
            workload
            and _bool(workload.get("status_pass", False))
            and Path(config_path).exists()
            and eval_seed > 0
            and str(source_row.get("candidate_output_semantics", "")) == OUTPUT_SEMANTICS
            and not _bool(source_row.get("runtime_base_policy_required", True))
            and not hidden_label_violation
        )
        plan.append(
            {
                **dict(source_row),
                **dict(workload),
                "runtime_smoke_episode_id": f"m3090-runtime-measurement-episode-{len(plan) + 1:04d}",
                "source_measurement_episode_id": source_row.get("measurement_episode_id", ""),
                "config_path": config_path,
                "base_profile_name": workload.get("profile_binding_name", source_row.get("base_profile_name", "")),
                "eval_seed": eval_seed,
                "hidden_label_violation": hidden_label_violation,
                "status_pass": status_pass,
            }
        )
    return plan


def _with_scope(rows: list[dict[str, Any]], *, id_prefix: str = "") -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["claim_boundary"] = CLAIM_SCOPE
        if "policy" in item:
            item["policy"] = "active_safety_reflex_driver_v1_full_fresh_runtime_measurement"
        for key in ("metric_summary_id", "guard_id", "gate_id", "claim_id"):
            if id_prefix and key in item:
                item[key] = str(item[key]).replace("m3088", id_prefix, 1)
        updated.append(item)
    return updated


def parity_rows(episodes: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_by_id = {str(row.get("measurement_episode_id", "")): row for row in source_rows}
    rows: list[dict[str, Any]] = []
    for episode in episodes:
        source = source_by_id.get(str(episode.get("source_measurement_episode_id", "")), {})
        clearance_delta = abs(_float(episode.get("min_clearance_margin")) - _float(source.get("min_clearance_margin")))
        return_delta = abs(_float(episode.get("return")) - _float(source.get("return")))
        action_rate_delta = abs(_float(episode.get("action_rate_mean")) - _float(source.get("action_rate_mean")))
        raw_action_abs_max_delta = abs(_float(episode.get("raw_action_abs_max")) - _float(source.get("raw_action_abs_max")))
        rows.append(
            {
                "parity_id": f"m3090-runtime-parity-{len(rows) + 1:04d}",
                "runtime_smoke_episode_id": episode.get("runtime_smoke_episode_id", ""),
                "source_measurement_episode_id": episode.get("source_measurement_episode_id", ""),
                "fresh_panel_row_id": episode.get("fresh_panel_row_id", ""),
                "axis_id": episode.get("axis_id", ""),
                "binding_role": episode.get("binding_role", ""),
                "task_family": episode.get("task_family", ""),
                "eval_seed": episode.get("eval_seed", ""),
                "m3084_policy": source.get("policy", ""),
                "runtime_policy": episode.get("policy", ""),
                "m3084_success": _success(source),
                "runtime_success": _success(episode),
                "success_match": _success(source) == _success(episode),
                "m3084_collision": _bool(source.get("collision", False)),
                "runtime_collision": _bool(episode.get("collision", False)),
                "collision_match": _bool(source.get("collision", False)) == _bool(episode.get("collision", False)),
                "m3084_termination_reason": source.get("termination_reason", ""),
                "runtime_termination_reason": episode.get("termination_reason", ""),
                "termination_reason_match": str(source.get("termination_reason", "")) == str(episode.get("termination_reason", "")),
                "m3084_outcome_bucket": source.get("outcome_bucket", ""),
                "runtime_outcome_bucket": episode.get("outcome_bucket", ""),
                "outcome_bucket_match": str(source.get("outcome_bucket", "")) == str(episode.get("outcome_bucket", "")),
                "m3084_min_clearance_margin": source.get("min_clearance_margin", ""),
                "runtime_min_clearance_margin": episode.get("min_clearance_margin", ""),
                "clearance_margin_abs_delta": clearance_delta,
                "m3084_return": source.get("return", ""),
                "runtime_return": episode.get("return", ""),
                "return_abs_delta": return_delta,
                "m3084_action_rate_mean": source.get("action_rate_mean", ""),
                "runtime_action_rate_mean": episode.get("action_rate_mean", ""),
                "action_rate_abs_delta": action_rate_delta,
                "m3084_raw_action_abs_max": source.get("raw_action_abs_max", ""),
                "runtime_raw_action_abs_max": episode.get("raw_action_abs_max", ""),
                "raw_action_abs_max_delta": raw_action_abs_max_delta,
                "exact_seed_match": str(source.get("eval_seed", "")) == str(episode.get("eval_seed", "")),
                "runtime_driver_id": DRIVER_ID,
                "parity_result_claim_made": False,
                "validation_run": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def guard(guard_id: str, family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3090-{guard_id}",
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
    contract: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = plan_rows + episodes + failures
    sample_action = ActiveSafetyReflexDriver().act(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32))
    return [
        guard("contract_observation_shape", "contract", contract.get("observation_shape"), P0_OBSERVATION_DIM),
        guard("contract_action_shape", "contract", contract.get("action_shape"), ACTION_DIM),
        guard("contract_action_components", "contract", "|".join(contract.get("action_components", [])), "|".join(ACTION_COMPONENTS)),
        guard("contract_output_semantics", "contract", contract.get("output_semantics"), OUTPUT_SEMANTICS),
        guard("m3086_interface_rows_pass", "source_contract", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_interface_rows", [])), True),
        guard("m3086_action_probe_rows_pass", "source_contract", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_probe_rows", [])), True),
        guard("m3086_actor_input_exclusion_rows_pass", "source_contract", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_exclusion_rows", [])), True),
        guard("m3086_claim_boundary_rows_pass", "source_contract", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_claim_rows", [])), True),
        guard("sample_action_shape", "runtime_api", tuple(sample_action.shape), (ACTION_DIM,)),
        guard("sample_action_finite", "runtime_api", bool(np.all(np.isfinite(sample_action))), True),
        guard("sample_action_bounded", "runtime_api", bool(np.max(np.abs(sample_action)) <= 1.0), True),
        guard("runtime_base_policy_required", "contract", any_flag(combined, "runtime_base_policy_required"), False),
        guard("checkpoint_model_required", "contract", any_flag(combined, "checkpoint_model_required"), False),
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
        ("runtime_measurement_rows", "measurement", True, "runtime_measurement_episode_rows.csv"),
        ("runtime_parity_rows", "measurement_parity", True, "runtime_parity_rows.csv"),
        ("metric_summary_rows", "measurement_metric", True, "runtime_measurement_metric_summary_rows.csv"),
        ("contract_guards", "guard", True, "runtime_measurement_contract_guard_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3091 audit manifest"),
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
        ("runtime_base_policy_dependency", "contract", "direct-action deployable driver forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3090-{claim_id}",
            "claim_family": family,
            "allowed_in_m3090": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3090-{claim_id}",
            "claim_family": family,
            "allowed_in_m3090": False,
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
        "priority": 30860,
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
        "hypothesis": "A bounded result audit can accept or reject the M3090 full-fresh deployable runtime measurement artifacts before any validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), "runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/deployable_driver_contract.json"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "runtime_measurement_episode_rows.csv"),
                str(output_dir / "runtime_measurement_failure_rows.csv"),
                str(output_dir / "runtime_measurement_metric_summary_rows.csv"),
                str(output_dir / "runtime_measurement_contract_guard_rows.csv"),
                str(output_dir / "runtime_parity_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit full-fresh deployable runtime measurement before broader validation interpretation"],
            "derived_from": [MILESTONE_ID, M3089_ID, M3088_ID, M3086_ID, M3084_ID],
            "blocked_by": [
                "M3090 full-fresh runtime rows require audit before any validation route",
                "same-row parity is an integration check, not a performance verdict before M3091",
            ],
            "supersedes": ["direct interpretation of M3090 rows without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3091 must audit M3090 summary measurement parity metric guard claim and gate artifacts",
            "M3091 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3091 must reject validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3091 must select exactly one broader validation-planning behavior-repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun expand tune rank promote validate or mutate checkpoints",
            "do not convert M3090 rows into driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_deployable_direct_action_reflex",
            "evidence_axis": "deployable_full_fresh_runtime_measurement_result_audit",
            "evidence_increment": "audits full-fresh runtime rows and same-row parity from the packaged deployable safety-reflex driver",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3090 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize if M3091 cannot select broader validation planning behavior repair synthesis or stop route",
            ],
            "fallback_plan": [
                "route to runtime package repair if artifacts are incomplete",
                "route to behavior repair synthesis if runtime behavior is negative but contract-safe",
                "route to validation planning only if M3090 is complete and claim-safe",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3090 completes full-fresh deployable runtime measurement preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3090 full-fresh deployable runtime measurement artifacts",
            "admission_evidence": ["M3090 summary gate matrix parity measurement metric contract and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3091 status queue scoreboard research log and review",
                "one follow-up manifest only if M3091 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3091 accepts or rejects M3090 as complete and claim-safe",
                "next validation-planning behavior-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3091 audits engineering runtime-measurement artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3091; finite-window and GRU comparison remains a later same-case engineering ablation."],
            "temporal_evidence_window": "M3090 full-fresh deployable runtime measurement artifacts only.",
            "negative_result_policy": "Preserve negative runtime evidence and route to engineering repair, synthesis, or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3090 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits complete fresh-denominator environment-loop evidence through the deployable runtime API",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3091 audits engineering runtime measurement evidence",
            "must_synthesize_if": [
                "M3091 cannot accept M3090 as complete and claim-safe",
                "M3091 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result or self-ID evidence",
                "M3091 cannot select validation planning behavior repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3091 audits M3090 row counts gates actor contract parity and claim boundaries",
            "M3091 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3091 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3091 hides M3090 failures or missing artifacts",
            "M3091 treats M3090 runtime measurement as validation or performance verdict",
            "M3091 changes actor input or action contract",
            "M3091 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3091 audits M3090 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_full_fresh_runtime_measurement_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3090-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _finite_parity_deltas(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        for key in ("clearance_margin_abs_delta", "return_abs_delta", "action_rate_abs_delta", "raw_action_abs_max_delta"):
            if not np.isfinite(_float(row.get(key))):
                return False
    return True


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    parity: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    audit_accepts = "accept_m3088_runtime_smoke_route_to_m3090_full_fresh_runtime_measurement_preflight" in str(
        source.get("m3089_audit_text", "")
    )
    source_present = all(source["source_exists"].values())
    parity_outcomes_match = all(
        _bool(row.get("success_match", False))
        and _bool(row.get("collision_match", False))
        and _bool(row.get("termination_reason_match", False))
        and _bool(row.get("outcome_bucket_match", False))
        and _bool(row.get("exact_seed_match", False))
        for row in parity
    )
    forbidden_flags_clear = not any_flag(episodes + failures, "driver_performance_claim_made") and not any_flag(
        episodes + failures, "validation_result_claim_made"
    )
    return [
        gate("source_artifacts_present", "source", source_present, source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3089_accepts_m3090_route", "lineage", audit_accepts, "route marker", "present", "lineage_invalid"),
        gate("m3088_status_pass", "lineage", _bool(source["m3088_summary"].get("status_pass", False)), source["m3088_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3088_gate_matrix_pass", "lineage", _bool(source["m3088_summary"].get("gate_matrix_pass", False)), source["m3088_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3086_status_pass", "lineage", _bool(source["m3086_summary"].get("status_pass", False)), source["m3086_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3086_gate_matrix_pass", "lineage", _bool(source["m3086_summary"].get("gate_matrix_pass", False)), source["m3086_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3086_interface_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_interface_rows", [])), len(source.get("m3086_interface_rows", [])), "all pass", "lineage_invalid"),
        gate("m3086_action_probe_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_probe_rows", [])), len(source.get("m3086_probe_rows", [])), "all pass", "lineage_invalid"),
        gate("m3086_actor_input_exclusion_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_exclusion_rows", [])), len(source.get("m3086_exclusion_rows", [])), "all pass", "lineage_invalid"),
        gate("m3086_claim_boundary_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_claim_rows", [])), len(source.get("m3086_claim_rows", [])), "all pass", "lineage_invalid"),
        gate("m3084_status_pass", "lineage", _bool(source["m3084_summary"].get("status_pass", False)), source["m3084_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3084_gate_matrix_pass", "lineage", _bool(source["m3084_summary"].get("gate_matrix_pass", False)), source["m3084_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("contract_observation_shape", "contract", int(contract.get("observation_shape", -1)) == P0_OBSERVATION_DIM, contract.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("contract_action_shape", "contract", int(contract.get("action_shape", -1)) == ACTION_DIM, contract.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("contract_output_semantics", "contract", str(contract.get("output_semantics", "")) == OUTPUT_SEMANTICS, contract.get("output_semantics"), OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(contract.get("runtime_base_policy_required", True)), contract.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("full_fresh_denominator", "measurement", len(plan_rows) == EXPECTED_FULL_ROWS, len(plan_rows), EXPECTED_FULL_ROWS, "scenario_sampling_failure"),
        gate("full_fresh_axis_count", "measurement", len({row.get("axis_id", "") for row in plan_rows}) == EXPECTED_AXIS_COUNT, len({row.get("axis_id", "") for row in plan_rows}), EXPECTED_AXIS_COUNT, "scenario_sampling_failure"),
        gate("full_fresh_binding_role_count", "measurement", len({row.get("binding_role", "") for row in plan_rows}) == EXPECTED_BINDING_ROLE_COUNT, len({row.get("binding_role", "") for row in plan_rows}), EXPECTED_BINDING_ROLE_COUNT, "scenario_sampling_failure"),
        gate("plan_rows_pass", "measurement", all(_bool(row.get("status_pass", False)) for row in plan_rows), "all", "pass", "scenario_sampling_failure"),
        gate("measurement_accounted_rows", "execution", len(episodes) + len(failures) == len(plan_rows), len(episodes) + len(failures), len(plan_rows), "metric_artifact"),
        gate("measurement_episode_rows", "execution", len(episodes) == EXPECTED_FULL_ROWS, len(episodes), EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("measurement_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("selected_metrics_finite", "metric", selected_metrics_are_finite(episodes) if episodes else False, "finite" if episodes else "none", "finite", "metric_artifact"),
        gate("metric_summary_rows", "metric", bool(metric_rows), len(metric_rows), "nonempty", "metric_artifact"),
        gate("parity_rows", "parity", len(parity) == EXPECTED_FULL_ROWS, len(parity), EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("parity_outcomes_match", "parity", parity_outcomes_match, parity_outcomes_match, True, "behavior_regression"),
        gate("parity_deltas_finite", "parity", _finite_parity_deltas(parity), "finite", "finite", "metric_artifact"),
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
            "# M3090 Active Safety Driver v1 Deployable Full-Fresh Runtime Measurement Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- scheduled full-fresh rows: {summary['scheduled_runtime_measurement_row_count']}/{summary['target_runtime_measurement_row_count']}",
            f"- runtime measurement episode rows: {summary['runtime_measurement_episode_row_count']}",
            f"- runtime measurement failure rows: {summary['runtime_measurement_failure_row_count']}",
            f"- parity rows: {summary['runtime_parity_row_count']}",
            f"- parity outcome matches: {summary['runtime_parity_outcome_match_count']}/{summary['runtime_parity_row_count']}",
            f"- success count: {summary['runtime_measurement_success_count']}",
            f"- collision count: {summary['runtime_measurement_collision_count']}",
            f"- offtrack count: {summary['runtime_measurement_offtrack_count']}",
            f"- speed-too-low count: {summary['runtime_measurement_speed_too_low_count']}",
            f"- clearance margin mean: {summary['runtime_measurement_clearance_margin_mean']}",
            f"- action clip fraction mean: {summary['runtime_measurement_action_clip_fraction_mean']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3090 records full-fresh current-sim rows through the packaged ActiveSafetyReflexDriver API and same-row parity against M3084 helper-path rows. These are runtime integration and parity artifacts for M3091 audit only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
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


def run_full_fresh_runtime_measurement_preflight(
    *,
    m3089_audit: Path,
    m3088_dir: Path,
    m3086_dir: Path,
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
        m3089_audit=m3089_audit,
        m3088_dir=m3088_dir,
        m3086_dir=m3086_dir,
        m3084_dir=m3084_dir,
        m3012_dir=m3012_dir,
    )
    contract = source["m3086_contract"]
    plan_rows = full_fresh_plan(source)
    measurement = m3088.run_smoke_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        contract=contract,
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    episodes = _with_scope(measurement["episodes"], id_prefix="m3090")
    failures = _with_scope(measurement["failures"], id_prefix="m3090")
    metric_rows = _with_scope(m3088.metric_summary_rows(episodes), id_prefix="m3090")
    guard_rows = contract_guard_rows(source=source, contract=contract, plan_rows=plan_rows, episodes=episodes, failures=failures)
    parity = parity_rows(episodes, source["m3084_measurement_rows"])
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["runtime_measurement_episode_rows"], episodes, m3088.EPISODE_FIELDNAMES),
        (paths["runtime_measurement_failure_rows"], failures, m3088.FAILURE_FIELDNAMES),
        (paths["runtime_measurement_metric_summary_rows"], metric_rows, m3088.METRIC_FIELDNAMES),
        (paths["runtime_measurement_contract_guard_rows"], guard_rows, m3088.GUARD_FIELDNAMES),
        (paths["runtime_parity_rows"], parity, PARITY_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        contract=contract,
        plan_rows=plan_rows,
        episodes=episodes,
        failures=failures,
        metric_rows=metric_rows,
        guard_rows=guard_rows,
        parity=parity,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=m3088.GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episodes)
    parity_outcome_match_count = sum(
        1
        for row in parity
        if _bool(row.get("success_match", False))
        and _bool(row.get("collision_match", False))
        and _bool(row.get("termination_reason_match", False))
        and _bool(row.get("outcome_bucket_match", False))
    )
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight_pass"
            if status_pass
            else "active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "runtime_driver_id": DRIVER_ID,
        "scheduled_runtime_measurement_row_count": len(plan_rows),
        "target_runtime_measurement_row_count": EXPECTED_FULL_ROWS,
        "runtime_measurement_episode_row_count": len(episodes),
        "runtime_measurement_failure_row_count": len(failures),
        "recorded_row_count": len(episodes) + len(failures),
        "runtime_measurement_success_count": sum(1 for row in episodes if _bool(row.get("success", False))),
        "runtime_measurement_collision_count": sum(1 for row in episodes if _bool(row.get("collision", False))),
        "runtime_measurement_offtrack_count": int(termination_counts.get("off_track", 0)),
        "runtime_measurement_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "runtime_measurement_termination_counts": dict(sorted(termination_counts.items())),
        "runtime_measurement_clearance_margin_mean": _mean(_float(row.get("min_clearance_margin")) for row in episodes),
        "runtime_measurement_high_sideslip_fraction_mean": _mean(_float(row.get("high_sideslip_fraction")) for row in episodes),
        "runtime_measurement_lateral_rmse_mean": _mean(_float(row.get("lateral_rmse")) for row in episodes),
        "runtime_measurement_action_clip_fraction_mean": _mean(_float(row.get("action_clip_fraction")) for row in episodes),
        "runtime_measurement_raw_action_abs_max": max((_float(row.get("raw_action_abs_max")) for row in episodes), default=0.0),
        "runtime_measurement_final_action_abs_max": max((_float(row.get("final_action_abs_max")) for row in episodes), default=0.0),
        "runtime_parity_row_count": len(parity),
        "runtime_parity_outcome_match_count": parity_outcome_match_count,
        "runtime_parity_all_outcomes_match": parity_outcome_match_count == len(parity),
        "runtime_parity_max_clearance_margin_abs_delta": max((_float(row.get("clearance_margin_abs_delta")) for row in parity), default=0.0),
        "runtime_parity_max_return_abs_delta": max((_float(row.get("return_abs_delta")) for row in parity), default=0.0),
        "metric_summary_row_count": len(metric_rows),
        "contract_guard_row_count": len(guard_rows),
        "contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3088_status_pass": _bool(source["m3088_summary"].get("status_pass", False)),
        "m3088_gate_matrix_pass": _bool(source["m3088_summary"].get("gate_matrix_pass", False)),
        "m3086_status_pass": _bool(source["m3086_summary"].get("status_pass", False)),
        "m3086_gate_matrix_pass": _bool(source["m3086_summary"].get("gate_matrix_pass", False)),
        "m3084_status_pass": _bool(source["m3084_summary"].get("status_pass", False)),
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "direct_action_formula": "action = ActiveSafetyReflexDriver.act(obs72) -> [steer, throttle, brake]",
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
        "decision": "active_safety_driver_v1_full_fresh_runtime_measurement_route_to_m3091_result_audit",
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
    write_run_state(
        paths["run_state"],
        {
            "scheduled_runtime_measurement_row_count": len(plan_rows),
            "runtime_measurement_episode_row_count": len(episodes),
            "runtime_measurement_failure_row_count": len(failures),
            "recorded_row_count": len(episodes) + len(failures),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3089-audit", type=Path, default=DEFAULT_M3089_AUDIT)
    parser.add_argument("--m3088-dir", type=Path, default=DEFAULT_M3088_DIR)
    parser.add_argument("--m3086-dir", type=Path, default=DEFAULT_M3086_DIR)
    parser.add_argument("--m3084-dir", type=Path, default=DEFAULT_M3084_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_full_fresh_runtime_measurement_preflight(
        m3089_audit=args.m3089_audit,
        m3088_dir=args.m3088_dir,
        m3086_dir=args.m3086_dir,
        m3084_dir=args.m3084_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"runtime_measurement_rows={summary['runtime_measurement_episode_row_count']}")
    print(f"runtime_measurement_failures={summary['runtime_measurement_failure_row_count']}")
    print(f"success_count={summary['runtime_measurement_success_count']}")
    print(f"collision_count={summary['runtime_measurement_collision_count']}")
    print(f"offtrack_count={summary['runtime_measurement_offtrack_count']}")
    print(f"speed_too_low_count={summary['runtime_measurement_speed_too_low_count']}")
    print(f"parity_outcome_match_count={summary['runtime_parity_outcome_match_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
