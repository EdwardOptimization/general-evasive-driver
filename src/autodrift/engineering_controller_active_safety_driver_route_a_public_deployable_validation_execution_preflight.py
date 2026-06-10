"""Run M3161 Route A public deployable validation execution preflight."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import time
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.active_safety_reflex_driver import ACTION_COMPONENTS, DRIVER_ID, OUTPUT_SEMANTICS, ActiveSafetyReflexDriver
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight as m3090
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088


MILESTONE_ID = (
    "m3161-engineering-controller-active-safety-driver-route-a-public-deployable-"
    "validation-execution-preflight"
)
NEXT_ID = (
    "m3162-engineering-controller-active-safety-driver-route-a-public-deployable-"
    "validation-execution-result-audit"
)
M3160_ID = (
    "m3160-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-"
    "validation-spec-result-audit"
)
M3159_ID = (
    "m3159-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-"
    "validation-spec-materialization-preflight"
)
M3156_ID = "m3156-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-materialization-preflight"
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3160_AUDIT = Path(f"docs/{M3160_ID}.md")
DEFAULT_M3159_DIR = Path(
    "runs/m3159_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_"
    "validation_spec_materialization_preflight"
)
DEFAULT_M3156_DIR = Path(
    "runs/m3156_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_"
    "materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3084_DIR = Path(
    "runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_fresh_robustness_measurement_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3161_engineering_controller_active_safety_driver_route_a_public_deployable_"
    "validation_execution_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_FULL_ROWS = 64
EXPECTED_SUCCESS_ROWS = 57
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
EXPECTED_RESIDUAL_BLOCKERS = 7
EXPECTED_AXIS_COUNT = 4
EXPECTED_BINDING_ROLE_COUNT = 2

CLAIM_SCOPE = (
    "M3161 Active Safety Driver Route A public deployable validation execution preflight only; "
    "the accepted M3159 same-case current-sim denominator may be executed through the public "
    "ActiveSafetyReflexDriver.act(obs72) API as the full obs72-to-action3 [steer throttle brake] "
    "action source, and validation execution, same-case M3105 comparison, known-failure validation, "
    "runtime contract probe, claim, gate, doc, and M3162 audit artifacts may be written. No ranking, "
    "winner selection, checkpoint mutation, checkpoint promotion, driver-performance verdict, "
    "current-sim verdict, validation-result verdict, repair success, robustness-result, high-fidelity "
    "validation result, paper evidence, finite-window-vs-GRU evidence, full ideal driver completion, "
    "feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "driver-performance verdict, current-sim verdict, validation-result verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal "
    "driver completion, feasibility proof, or level3 self-identification"
)

RUNTIME_PROBE_FIELDNAMES = [
    "probe_id",
    "observation_shape",
    "action_shape",
    "action_components",
    "finite",
    "bounded",
    "runtime_ms",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "validation_execution_run",
    "validation_result_claim_made",
    "claim_boundary",
]
SAME_CASE_FIELDNAMES = [
    "comparison_id",
    "validation_episode_id",
    "candidate_id",
    "baseline_id",
    "incumbent_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "candidate_success",
    "baseline_success",
    "success_match",
    "success_delta",
    "candidate_collision",
    "baseline_collision",
    "collision_match",
    "collision_delta",
    "candidate_offtrack",
    "baseline_offtrack",
    "offtrack_match",
    "offtrack_delta",
    "candidate_speed_too_low",
    "baseline_speed_too_low",
    "speed_too_low_match",
    "speed_too_low_delta",
    "candidate_terminal",
    "baseline_terminal",
    "termination_reason_match",
    "candidate_outcome_bucket",
    "baseline_outcome_bucket",
    "outcome_bucket_match",
    "candidate_min_clearance_margin",
    "baseline_min_clearance_margin",
    "clearance_delta",
    "candidate_return",
    "baseline_return",
    "return_delta",
    "candidate_speed_mean",
    "baseline_speed_mean",
    "speed_mean_delta",
    "candidate_action_rate_mean",
    "baseline_action_rate_mean",
    "action_rate_delta",
    "exact_seed_match",
    "validation_execution_run",
    "validation_result_claim_made",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "claim_boundary",
]
KNOWN_FAILURE_FIELDNAMES = [
    "known_failure_validation_id",
    "source_blocker_id",
    "validation_episode_id",
    "incumbent_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "source_blocker_family",
    "candidate_terminal",
    "baseline_terminal",
    "candidate_blocker_family",
    "baseline_blocker_family",
    "blocker_family_match",
    "termination_reason_match",
    "blocker_preserved",
    "blocker_resolved",
    "validation_execution_run",
    "validation_result_claim_made",
    "repair_success_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3161",
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


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _speed_too_low(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "speed_too_low"


def _blocker_family(row: Mapping[str, Any]) -> str:
    if _bool(row.get("collision", False)):
        return "collision"
    if _offtrack(row):
        return "offtrack"
    if _speed_too_low(row):
        return "speed_too_low"
    if _success(row):
        return "resolved"
    return str(row.get("termination_reason", "") or row.get("outcome_bucket", "") or "unknown")


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return m3088.any_flag(rows, key)


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "validation_execution_summary": output_dir / "validation_execution_summary.json",
        "validation_episode_rows": output_dir / "validation_episode_rows.csv",
        "validation_failure_rows": output_dir / "validation_failure_rows.csv",
        "validation_metric_summary_rows": output_dir / "validation_metric_summary_rows.csv",
        "same_case_comparison_rows": output_dir / "same_case_comparison_rows.csv",
        "known_failure_validation_rows": output_dir / "known_failure_validation_rows.csv",
        "runtime_contract_probe_rows": output_dir / "runtime_contract_probe_rows.csv",
        "validation_claim_boundary_rows": output_dir / "validation_claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3160_audit: Path,
    m3159_dir: Path,
    m3156_dir: Path,
    m3105_dir: Path,
    m3084_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3160_audit": m3160_audit,
        "m3159_summary": m3159_dir / "summary.json",
        "m3159_denominator_rows": m3159_dir / "validation_denominator_rows.csv",
        "m3159_gate_spec_rows": m3159_dir / "validation_gate_spec_rows.csv",
        "m3159_reporting_rows": m3159_dir / "validation_reporting_artifact_rows.csv",
        "m3159_claim_rows": m3159_dir / "validation_claim_boundary_rows.csv",
        "m3159_gate_rows": m3159_dir / "gate_matrix.csv",
        "m3156_summary": m3156_dir / "summary.json",
        "m3156_contract_snapshot": m3156_dir / "deployable_driver_contract_snapshot.json",
        "m3156_known_failure_rows": m3156_dir / "known_failure_taxonomy_rows.csv",
        "m3156_metric_rows": m3156_dir / "benchmark_metric_rows.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_episode_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3105_gate_rows": m3105_dir / "gate_matrix.csv",
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
        "m3160_audit_text": paths["m3160_audit"].read_text(encoding="utf-8") if exists["m3160_audit"] else "",
        "m3159_summary": read_json(paths["m3159_summary"]) if exists["m3159_summary"] else {},
        "m3159_denominator_rows": read_csv_rows(paths["m3159_denominator_rows"]),
        "m3159_gate_spec_rows": read_csv_rows(paths["m3159_gate_spec_rows"]),
        "m3159_reporting_rows": read_csv_rows(paths["m3159_reporting_rows"]),
        "m3159_claim_rows": read_csv_rows(paths["m3159_claim_rows"]),
        "m3159_gate_rows": read_csv_rows(paths["m3159_gate_rows"]),
        "m3156_summary": read_json(paths["m3156_summary"]) if exists["m3156_summary"] else {},
        "m3156_contract_snapshot": read_json(paths["m3156_contract_snapshot"]) if exists["m3156_contract_snapshot"] else {},
        "m3156_known_failure_rows": read_csv_rows(paths["m3156_known_failure_rows"]),
        "m3156_metric_rows": read_csv_rows(paths["m3156_metric_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_episode_rows": read_csv_rows(paths["m3105_episode_rows"]),
        "m3105_gate_rows": read_csv_rows(paths["m3105_gate_rows"]),
        "m3084_summary": read_json(paths["m3084_summary"]) if exists["m3084_summary"] else {},
        "m3084_measurement_rows": read_csv_rows(paths["m3084_measurement_rows"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def full_fresh_validation_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    plan = m3090.full_fresh_plan(source)
    for index, row in enumerate(plan, start=1):
        row["runtime_smoke_episode_id"] = f"m3161-validation-episode-{index:04d}"
    return plan


def _with_scope(rows: list[dict[str, Any]], *, id_prefix: str = "m3161") -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["claim_boundary"] = CLAIM_SCOPE
        item["runtime_driver_id"] = DRIVER_ID
        item["candidate_output_semantics"] = OUTPUT_SEMANTICS
        item["validation_run"] = True
        item["validation_result_claim_made"] = False
        item["driver_performance_claim_made"] = False
        item["repair_success_claim_made"] = False
        item["current_sim_verdict_claim_made"] = False
        item["runtime_smoke_only_no_verdict"] = False
        if "policy" in item:
            item["policy"] = "active_safety_reflex_driver_route_a_public_deployable_validation_execution"
        for key in ("metric_summary_id", "guard_id", "gate_id", "claim_id"):
            if id_prefix and key in item:
                item[key] = str(item[key]).replace("m3088", id_prefix, 1)
        updated.append(item)
    return updated


def runtime_contract_probe_rows() -> list[dict[str, Any]]:
    driver = ActiveSafetyReflexDriver()
    observations = [
        np.zeros(P0_OBSERVATION_DIM, dtype=np.float32),
        np.ones(P0_OBSERVATION_DIM, dtype=np.float32) * 0.25,
        np.ones(P0_OBSERVATION_DIM, dtype=np.float32) * -0.25,
        np.linspace(-1.0, 1.0, P0_OBSERVATION_DIM, dtype=np.float32),
        np.eye(1, P0_OBSERVATION_DIM, 0, dtype=np.float32).reshape(P0_OBSERVATION_DIM),
    ]
    rows: list[dict[str, Any]] = []
    for index, observation in enumerate(observations, start=1):
        started = time.perf_counter()
        action = driver.act(observation)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        rows.append(
            {
                "probe_id": f"m3161-runtime-contract-probe-{index:04d}",
                "observation_shape": int(observation.shape[0]),
                "action_shape": int(action.shape[0]),
                "action_components": "|".join(ACTION_COMPONENTS),
                "finite": bool(np.all(np.isfinite(action))),
                "bounded": bool(float(np.max(np.abs(action))) <= 1.0),
                "runtime_ms": float(elapsed_ms),
                "runtime_base_policy_required": False,
                "checkpoint_model_required": False,
                "recurrent_hidden_state_required": False,
                "hidden_oracle_actor_input_required": False,
                "ttc_actor_input_required": False,
                "validation_execution_run": True,
                "validation_result_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def same_case_comparison_rows(
    episodes: list[dict[str, Any]],
    incumbent_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    incumbent_by_source = {str(row.get("source_measurement_episode_id", "")): row for row in incumbent_rows}
    rows: list[dict[str, Any]] = []
    for episode in episodes:
        source_id = str(episode.get("source_measurement_episode_id", ""))
        baseline = incumbent_by_source.get(source_id, {})
        candidate_offtrack = _offtrack(episode)
        baseline_offtrack = _offtrack(baseline)
        candidate_speed_too_low = _speed_too_low(episode)
        baseline_speed_too_low = _speed_too_low(baseline)
        rows.append(
            {
                "comparison_id": f"m3161-same-case-comparison-{len(rows) + 1:04d}",
                "validation_episode_id": episode.get("runtime_smoke_episode_id", ""),
                "candidate_id": DRIVER_ID,
                "baseline_id": "m3105_incumbent_direct_action_measurement",
                "incumbent_episode_id": baseline.get("runtime_smoke_episode_id", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": episode.get("fresh_panel_row_id", ""),
                "axis_id": episode.get("axis_id", ""),
                "binding_role": episode.get("binding_role", ""),
                "task_family": episode.get("task_family", ""),
                "eval_seed": episode.get("eval_seed", ""),
                "candidate_success": _success(episode),
                "baseline_success": _success(baseline),
                "success_match": _success(episode) == _success(baseline),
                "success_delta": int(_success(episode)) - int(_success(baseline)),
                "candidate_collision": _bool(episode.get("collision", False)),
                "baseline_collision": _bool(baseline.get("collision", False)),
                "collision_match": _bool(episode.get("collision", False)) == _bool(baseline.get("collision", False)),
                "collision_delta": int(_bool(episode.get("collision", False))) - int(_bool(baseline.get("collision", False))),
                "candidate_offtrack": candidate_offtrack,
                "baseline_offtrack": baseline_offtrack,
                "offtrack_match": candidate_offtrack == baseline_offtrack,
                "offtrack_delta": int(candidate_offtrack) - int(baseline_offtrack),
                "candidate_speed_too_low": candidate_speed_too_low,
                "baseline_speed_too_low": baseline_speed_too_low,
                "speed_too_low_match": candidate_speed_too_low == baseline_speed_too_low,
                "speed_too_low_delta": int(candidate_speed_too_low) - int(baseline_speed_too_low),
                "candidate_terminal": episode.get("termination_reason", ""),
                "baseline_terminal": baseline.get("termination_reason", ""),
                "termination_reason_match": str(episode.get("termination_reason", "")) == str(baseline.get("termination_reason", "")),
                "candidate_outcome_bucket": episode.get("outcome_bucket", ""),
                "baseline_outcome_bucket": baseline.get("outcome_bucket", ""),
                "outcome_bucket_match": str(episode.get("outcome_bucket", "")) == str(baseline.get("outcome_bucket", "")),
                "candidate_min_clearance_margin": episode.get("min_clearance_margin", ""),
                "baseline_min_clearance_margin": baseline.get("min_clearance_margin", ""),
                "clearance_delta": _float(episode.get("min_clearance_margin")) - _float(baseline.get("min_clearance_margin")),
                "candidate_return": episode.get("return", ""),
                "baseline_return": baseline.get("return", ""),
                "return_delta": _float(episode.get("return")) - _float(baseline.get("return")),
                "candidate_speed_mean": episode.get("speed_mean", ""),
                "baseline_speed_mean": baseline.get("speed_mean", ""),
                "speed_mean_delta": _float(episode.get("speed_mean")) - _float(baseline.get("speed_mean")),
                "candidate_action_rate_mean": episode.get("action_rate_mean", ""),
                "baseline_action_rate_mean": baseline.get("action_rate_mean", ""),
                "action_rate_delta": _float(episode.get("action_rate_mean")) - _float(baseline.get("action_rate_mean")),
                "exact_seed_match": str(episode.get("eval_seed", "")) == str(baseline.get("eval_seed", "")),
                "validation_execution_run": True,
                "validation_result_claim_made": False,
                "driver_performance_claim_made": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def known_failure_validation_rows(
    episodes: list[dict[str, Any]],
    incumbent_rows: list[dict[str, Any]],
    known_failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    episodes_by_source = {str(row.get("source_measurement_episode_id", "")): row for row in episodes}
    incumbent_by_source = {str(row.get("source_measurement_episode_id", "")): row for row in incumbent_rows}
    rows: list[dict[str, Any]] = []
    for source in known_failure_rows:
        source_id = str(source.get("source_measurement_episode_id", ""))
        episode = episodes_by_source.get(source_id, {})
        baseline = incumbent_by_source.get(source_id, {})
        source_family = str(source.get("blocker_family", ""))
        candidate_family = _blocker_family(episode)
        baseline_family = _blocker_family(baseline)
        blocker_family_match = source_family == candidate_family == baseline_family
        termination_match = str(episode.get("termination_reason", "")) == str(baseline.get("termination_reason", ""))
        rows.append(
            {
                "known_failure_validation_id": f"m3161-known-failure-validation-{len(rows) + 1:04d}",
                "source_blocker_id": source.get("failure_taxonomy_row_id", ""),
                "validation_episode_id": episode.get("runtime_smoke_episode_id", ""),
                "incumbent_episode_id": baseline.get("runtime_smoke_episode_id", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": source.get("fresh_panel_row_id", ""),
                "axis_id": source.get("axis_id", ""),
                "binding_role": source.get("binding_role", ""),
                "task_family": source.get("task_family", ""),
                "eval_seed": source.get("eval_seed", ""),
                "source_blocker_family": source_family,
                "candidate_terminal": episode.get("termination_reason", ""),
                "baseline_terminal": baseline.get("termination_reason", ""),
                "candidate_blocker_family": candidate_family,
                "baseline_blocker_family": baseline_family,
                "blocker_family_match": blocker_family_match,
                "termination_reason_match": termination_match,
                "blocker_preserved": blocker_family_match and not _success(episode),
                "blocker_resolved": _success(episode),
                "validation_execution_run": True,
                "validation_result_claim_made": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("validation_execution_rows", "validation_execution", True, "validation_episode_rows.csv"),
        ("same_case_comparison_rows", "same_case_comparison", True, "same_case_comparison_rows.csv"),
        ("known_failure_validation_rows", "known_failure_disclosure", True, "known_failure_validation_rows.csv"),
        ("runtime_contract_probe_rows", "runtime_contract", True, "runtime_contract_probe_rows.csv"),
        ("metric_summary_rows", "measurement_metric", True, "validation_metric_summary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3162 audit manifest"),
    ]
    blocked = [
        ("validation_result_verdict", "validation_result", "M3162 audit and later verdict gate"),
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
        ("feasibility_proof", "feasibility", "future feasibility proof gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "public deployable reflex forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3161-{claim_id}",
            "claim_family": family,
            "allowed_in_m3161": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3161-{claim_id}",
            "claim_family": family,
            "allowed_in_m3161": False,
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
        "priority": 31620,
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
        "hypothesis": "A bounded result audit can accept or reject the M3161 public deployable validation execution artifacts before any ranking promotion driver-performance current-sim verdict high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "validation_execution_summary.json"),
                str(output_dir / "validation_episode_rows.csv"),
                str(output_dir / "validation_failure_rows.csv"),
                str(output_dir / "validation_metric_summary_rows.csv"),
                str(output_dir / "same_case_comparison_rows.csv"),
                str(output_dir / "known_failure_validation_rows.csv"),
                str(output_dir / "runtime_contract_probe_rows.csv"),
                str(output_dir / "validation_claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit Route A public deployable validation execution before broader interpretation"],
            "derived_from": [MILESTONE_ID, M3160_ID, M3159_ID, M3156_ID, M3105_ID],
            "blocked_by": [
                "M3161 validation execution rows require audit before any validation-result or performance verdict",
                "same-case public-driver versus M3105 comparison is execution evidence and not a repair-success claim before M3162",
            ],
            "supersedes": ["direct interpretation of M3161 validation execution rows without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3162 must audit M3161 summary episode comparison known-failure runtime-probe claim and gate artifacts",
            "M3162 must preserve obs72/action3 direct [steer throttle brake] public API contract",
            "M3162 must reject ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3162 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun expand tune rank promote or mutate checkpoints",
            "do not convert M3161 validation execution rows into driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_route_a_deployable_benchmark_pack",
            "evidence_axis": "route_a_public_deployable_validation_execution_result_audit",
            "evidence_increment": "audits full-fresh same-case validation execution rows through the public deployable driver API",
            "claim_scope": "Result audit only; no ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3161 artifacts are missing or gate matrix fails",
                "stop if public API actor or direct-action contracts were violated",
                "synthesize if M3162 cannot select one next route",
            ],
            "fallback_plan": [
                "route to M3161 artifact repair if execution artifacts are incomplete",
                "route to public deployable interface repair if actor contract is violated",
                "route to validation result synthesis only after M3162 accepts artifact completeness and claim boundaries",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3161 completes Route A public deployable validation execution preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3161 public deployable validation execution artifacts",
            "admission_evidence": ["M3161 validation execution summary gate matrix comparison known-failure runtime-probe and claim artifacts"],
            "blocked_shortcuts": [
                "no ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3162 status queue scoreboard research log and review",
                "one follow-up manifest only if M3162 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3162 accepts or rejects M3161 as complete and claim-safe",
                "next validation result synthesis artifact repair stop or high-fidelity-prep route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3162 audits engineering validation-execution artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3162; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3161 public deployable validation execution artifacts only.",
            "negative_result_policy": "Preserve residual blocker evidence and route to engineering validation audit rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3161 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "low",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly executed same-case validation artifacts through the public deployable driver API",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3162 audits engineering validation execution evidence",
            "must_synthesize_if": [
                "M3162 cannot accept M3161 as complete and claim-safe",
                "M3162 would claim driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result feasibility-proof or self-ID evidence",
                "M3162 cannot select validation result synthesis artifact repair stop or next route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3162 audits M3161 row counts gates actor contract same-case comparison known-failure disclosure and claim boundaries",
            "M3162 rejects ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3162 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3162 hides M3161 failures or missing artifacts",
            "M3162 treats M3161 execution rows as repair-success or performance verdict",
            "M3162 changes actor input or action contract",
            "M3162 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3162 audits M3161 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_route_a_public_deployable_validation_execution_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "validation_execution_summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3161-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _finite_same_case_deltas(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        for key in ("clearance_delta", "return_delta", "speed_mean_delta", "action_rate_delta"):
            if not np.isfinite(_float(row.get(key))):
                return False
    return True


def _same_case_delta_sum(rows: list[dict[str, Any]], key: str) -> int:
    return sum(int(row.get(key, 0)) for row in rows)


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    same_case_rows: list[dict[str, Any]],
    known_failure_rows: list[dict[str, Any]],
    runtime_probe_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    m3160_accepts = "accept_m3159_validation_specs_route_to_m3161_public_deployable_validation_execution_preflight" in str(
        source.get("m3160_audit_text", "")
    )
    m3159_summary = source["m3159_summary"]
    m3156_summary = source["m3156_summary"]
    m3105_summary = source["m3105_summary"]
    blocker_counts = Counter(str(row.get("source_blocker_family", "")) for row in known_failure_rows)
    same_case_outcomes_match = all(
        _bool(row.get("success_match", False))
        and _bool(row.get("collision_match", False))
        and _bool(row.get("offtrack_match", False))
        and _bool(row.get("speed_too_low_match", False))
        and _bool(row.get("termination_reason_match", False))
        and _bool(row.get("exact_seed_match", False))
        for row in same_case_rows
    )
    same_case_hard_safety_deltas_zero = all(
        _same_case_delta_sum(same_case_rows, key) == 0
        for key in ("success_delta", "collision_delta", "offtrack_delta", "speed_too_low_delta")
    )
    known_failures_preserved = all(_bool(row.get("blocker_preserved", False)) for row in known_failure_rows)
    runtime_probes_pass = all(
        _bool(row.get("finite", False))
        and _bool(row.get("bounded", False))
        and not _bool(row.get("runtime_base_policy_required", True))
        and not _bool(row.get("hidden_oracle_actor_input_required", True))
        and not _bool(row.get("ttc_actor_input_required", True))
        for row in runtime_probe_rows
    )
    forbidden_flags_clear = (
        not any_flag(episodes + failures, "driver_performance_claim_made")
        and not any_flag(episodes + failures, "validation_result_claim_made")
        and not any_flag(episodes + failures, "repair_success_claim_made")
        and not any_flag(episodes + failures, "current_sim_verdict_claim_made")
    )
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3160_accepts_m3161_route", "lineage", m3160_accepts, "route marker", "present", "lineage_invalid"),
        gate("m3159_status_pass", "lineage", _bool(m3159_summary.get("status_pass", False)), m3159_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3159_gate_matrix_pass", "lineage", _bool(m3159_summary.get("gate_matrix_pass", False)), m3159_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3159_denominator_rows", "validation_spec", len(source.get("m3159_denominator_rows", [])) == 5, len(source.get("m3159_denominator_rows", [])), 5, "metric_artifact"),
        gate("m3159_gate_spec_rows", "validation_spec", len(source.get("m3159_gate_spec_rows", [])) >= 20, len(source.get("m3159_gate_spec_rows", [])), ">=20", "metric_artifact"),
        gate("m3159_reporting_rows", "validation_spec", len(source.get("m3159_reporting_rows", [])) >= 7, len(source.get("m3159_reporting_rows", [])), ">=7", "metric_artifact"),
        gate("m3156_status_pass", "lineage", _bool(m3156_summary.get("status_pass", False)), m3156_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3156_gate_matrix_pass", "lineage", _bool(m3156_summary.get("gate_matrix_pass", False)), m3156_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(m3105_summary.get("status_pass", False)), m3105_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3105_gate_matrix_pass", "lineage", _bool(m3105_summary.get("gate_matrix_pass", False)), m3105_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("contract_observation_shape", "contract", int(contract.get("observation_shape", -1)) == P0_OBSERVATION_DIM, contract.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("contract_action_shape", "contract", int(contract.get("action_shape", -1)) == ACTION_DIM, contract.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("contract_action_components", "contract", "|".join(contract.get("action_components", [])) == "|".join(ACTION_COMPONENTS), contract.get("action_components", []), "|".join(ACTION_COMPONENTS), "contract_violation"),
        gate("contract_output_semantics", "contract", str(contract.get("output_semantics", "")) == OUTPUT_SEMANTICS, contract.get("output_semantics"), OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", contract.get("runtime_base_policy_required") is False, contract.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("full_fresh_denominator", "execution", len(plan_rows) == EXPECTED_FULL_ROWS, len(plan_rows), EXPECTED_FULL_ROWS, "scenario_sampling_failure"),
        gate("full_fresh_axis_count", "execution", len({row.get("axis_id", "") for row in plan_rows}) == EXPECTED_AXIS_COUNT, len({row.get("axis_id", "") for row in plan_rows}), EXPECTED_AXIS_COUNT, "scenario_sampling_failure"),
        gate("full_fresh_binding_role_count", "execution", len({row.get("binding_role", "") for row in plan_rows}) == EXPECTED_BINDING_ROLE_COUNT, len({row.get("binding_role", "") for row in plan_rows}), EXPECTED_BINDING_ROLE_COUNT, "scenario_sampling_failure"),
        gate("plan_rows_pass", "execution", all(_bool(row.get("status_pass", False)) for row in plan_rows), "all", "pass", "scenario_sampling_failure"),
        gate("validation_accounted_rows", "execution", len(episodes) + len(failures) == len(plan_rows), len(episodes) + len(failures), len(plan_rows), "metric_artifact"),
        gate("validation_episode_rows", "execution", len(episodes) == EXPECTED_FULL_ROWS, len(episodes), EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("validation_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("selected_metrics_finite", "metric", selected_metrics_are_finite(episodes) if episodes else False, "finite" if episodes else "none", "finite", "metric_artifact"),
        gate("metric_summary_rows", "metric", bool(metric_rows), len(metric_rows), "nonempty", "metric_artifact"),
        gate("runtime_contract_probe_rows", "contract", len(runtime_probe_rows) >= 5 and runtime_probes_pass, len(runtime_probe_rows), ">=5 all pass", "contract_violation"),
        gate("same_case_comparison_rows", "comparison", len(same_case_rows) == EXPECTED_FULL_ROWS, len(same_case_rows), EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("same_case_outcomes_match_m3105", "comparison", same_case_outcomes_match, same_case_outcomes_match, True, "behavior_regression"),
        gate("same_case_hard_safety_deltas_zero", "comparison", same_case_hard_safety_deltas_zero, {key: _same_case_delta_sum(same_case_rows, key) for key in ("success_delta", "collision_delta", "offtrack_delta", "speed_too_low_delta")}, "all zero", "behavior_regression"),
        gate("same_case_metric_deltas_finite", "comparison", _finite_same_case_deltas(same_case_rows), "finite", "finite", "metric_artifact"),
        gate("known_failure_rows", "known_failures", len(known_failure_rows) == EXPECTED_RESIDUAL_BLOCKERS, len(known_failure_rows), EXPECTED_RESIDUAL_BLOCKERS, "metric_artifact"),
        gate("known_failure_family_counts", "known_failures", blocker_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS and blocker_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(blocker_counts.items())), {"collision": EXPECTED_COLLISION_ROWS, "offtrack": EXPECTED_OFFTRACK_ROWS}, "metric_artifact"),
        gate("known_failures_preserved_for_audit", "known_failures", known_failures_preserved, known_failures_preserved, True, "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("forbidden_flags_clear", "claim", forbidden_flags_clear, "forbidden claim flags", "clear", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "validation_execution_summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3161 Route A Public Deployable Validation Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- validation episode rows: {summary['validation_episode_row_count']}/{summary['target_validation_episode_row_count']}",
            f"- validation failure rows: {summary['validation_failure_row_count']}",
            f"- success count: {summary['validation_success_count']}",
            f"- collision count: {summary['validation_collision_count']}",
            f"- offtrack count: {summary['validation_offtrack_count']}",
            f"- speed-too-low count: {summary['validation_speed_too_low_count']}",
            f"- same-case comparison rows: {summary['same_case_comparison_row_count']}",
            f"- same-case outcome matches: {summary['same_case_outcome_match_count']}/{summary['same_case_comparison_row_count']}",
            f"- known failure rows: {summary['known_failure_validation_row_count']}",
            f"- known failures preserved for audit: {summary['known_failure_preserved_count']}",
            f"- runtime contract probe rows: {summary['runtime_contract_probe_row_count']}",
            f"- clearance margin mean: {summary['validation_clearance_margin_mean']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3161 executes the accepted M3159 Route A same-case current-sim denominator through the public ActiveSafetyReflexDriver.act(obs72) deployable API and writes comparison rows against the M3105 incumbent measurement. This is validation execution preflight evidence for M3162 audit. It is not a validation-result verdict, ranking, promotion, repair-success, driver-performance, current-sim, high-fidelity, paper, full-driver, feasibility-proof, robustness-result, or self-ID claim.",
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


def run_validation_execution_preflight(
    *,
    m3160_audit: Path,
    m3159_dir: Path,
    m3156_dir: Path,
    m3105_dir: Path,
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
        m3160_audit=m3160_audit,
        m3159_dir=m3159_dir,
        m3156_dir=m3156_dir,
        m3105_dir=m3105_dir,
        m3084_dir=m3084_dir,
        m3012_dir=m3012_dir,
    )
    contract = ActiveSafetyReflexDriver().contract_dict()
    plan_rows = full_fresh_validation_plan(source)
    measurement = m3088.run_smoke_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        contract=contract,
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    episodes = _with_scope(measurement["episodes"], id_prefix="m3161")
    failures = _with_scope(measurement["failures"], id_prefix="m3161")
    metric_rows = _with_scope(m3088.metric_summary_rows(episodes), id_prefix="m3161")
    same_case = same_case_comparison_rows(episodes, source["m3105_episode_rows"])
    known_failures = known_failure_validation_rows(
        episodes,
        source["m3105_episode_rows"],
        source["m3156_known_failure_rows"],
    )
    runtime_probes = runtime_contract_probe_rows()
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["validation_episode_rows"], episodes, m3088.EPISODE_FIELDNAMES),
        (paths["validation_failure_rows"], failures, m3088.FAILURE_FIELDNAMES),
        (paths["validation_metric_summary_rows"], metric_rows, m3088.METRIC_FIELDNAMES),
        (paths["same_case_comparison_rows"], same_case, SAME_CASE_FIELDNAMES),
        (paths["known_failure_validation_rows"], known_failures, KNOWN_FAILURE_FIELDNAMES),
        (paths["runtime_contract_probe_rows"], runtime_probes, RUNTIME_PROBE_FIELDNAMES),
        (paths["validation_claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
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
        same_case_rows=same_case,
        known_failure_rows=known_failures,
        runtime_probe_rows=runtime_probes,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=m3088.GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episodes)
    status_pass = bool(gate_matrix_pass and present)
    same_case_outcome_match_count = sum(
        1
        for row in same_case
        if _bool(row.get("success_match", False))
        and _bool(row.get("collision_match", False))
        and _bool(row.get("offtrack_match", False))
        and _bool(row.get("speed_too_low_match", False))
        and _bool(row.get("termination_reason_match", False))
    )
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_route_a_public_deployable_validation_execution_preflight_pass"
            if status_pass
            else "active_safety_driver_route_a_public_deployable_validation_execution_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "runtime_driver_id": DRIVER_ID,
        "scheduled_validation_episode_row_count": len(plan_rows),
        "target_validation_episode_row_count": EXPECTED_FULL_ROWS,
        "validation_episode_row_count": len(episodes),
        "validation_failure_row_count": len(failures),
        "recorded_row_count": len(episodes) + len(failures),
        "validation_success_count": sum(1 for row in episodes if _success(row)),
        "validation_collision_count": sum(1 for row in episodes if _bool(row.get("collision", False))),
        "validation_offtrack_count": int(termination_counts.get("off_track", 0)),
        "validation_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "validation_termination_counts": dict(sorted(termination_counts.items())),
        "validation_success_rate": _mean(float(_success(row)) for row in episodes),
        "validation_clearance_margin_mean": _mean(_float(row.get("min_clearance_margin")) for row in episodes),
        "validation_high_sideslip_fraction_mean": _mean(_float(row.get("high_sideslip_fraction")) for row in episodes),
        "validation_lateral_rmse_mean": _mean(_float(row.get("lateral_rmse")) for row in episodes),
        "validation_action_clip_fraction_mean": _mean(_float(row.get("action_clip_fraction")) for row in episodes),
        "validation_raw_action_abs_max": max((_float(row.get("raw_action_abs_max")) for row in episodes), default=0.0),
        "validation_final_action_abs_max": max((_float(row.get("final_action_abs_max")) for row in episodes), default=0.0),
        "same_case_comparison_row_count": len(same_case),
        "same_case_outcome_match_count": same_case_outcome_match_count,
        "same_case_all_outcomes_match": same_case_outcome_match_count == len(same_case),
        "same_case_success_delta_sum": _same_case_delta_sum(same_case, "success_delta"),
        "same_case_collision_delta_sum": _same_case_delta_sum(same_case, "collision_delta"),
        "same_case_offtrack_delta_sum": _same_case_delta_sum(same_case, "offtrack_delta"),
        "same_case_speed_too_low_delta_sum": _same_case_delta_sum(same_case, "speed_too_low_delta"),
        "known_failure_validation_row_count": len(known_failures),
        "known_failure_preserved_count": sum(1 for row in known_failures if _bool(row.get("blocker_preserved", False))),
        "known_failure_resolved_count": sum(1 for row in known_failures if _bool(row.get("blocker_resolved", False))),
        "runtime_contract_probe_row_count": len(runtime_probes),
        "runtime_contract_probe_rows_pass": all(
            _bool(row.get("finite", False)) and _bool(row.get("bounded", False)) for row in runtime_probes
        ),
        "metric_summary_row_count": len(metric_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3159_status_pass": _bool(source["m3159_summary"].get("status_pass", False)),
        "m3159_gate_matrix_pass": _bool(source["m3159_summary"].get("gate_matrix_pass", False)),
        "m3156_status_pass": _bool(source["m3156_summary"].get("status_pass", False)),
        "m3105_status_pass": _bool(source["m3105_summary"].get("status_pass", False)),
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "candidate_output_components": list(ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "direct_action_formula": "action = ActiveSafetyReflexDriver.act(obs72) -> [steer, throttle, brake]",
        "environment_reset_run": bool(episodes),
        "environment_step_run": bool(episodes),
        "policy_action_run": bool(episodes),
        "policy_rollout_run": bool(episodes),
        "validation_run": bool(episodes),
        "validation_execution_run": bool(episodes),
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
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_route_a_public_deployable_validation_execution_route_to_m3162_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    write_json(paths["validation_execution_summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "scheduled_validation_episode_row_count": len(plan_rows),
            "validation_episode_row_count": len(episodes),
            "validation_failure_row_count": len(failures),
            "recorded_row_count": len(episodes) + len(failures),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3160-audit", type=Path, default=DEFAULT_M3160_AUDIT)
    parser.add_argument("--m3159-dir", type=Path, default=DEFAULT_M3159_DIR)
    parser.add_argument("--m3156-dir", type=Path, default=DEFAULT_M3156_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3084-dir", type=Path, default=DEFAULT_M3084_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_validation_execution_preflight(
        m3160_audit=args.m3160_audit,
        m3159_dir=args.m3159_dir,
        m3156_dir=args.m3156_dir,
        m3105_dir=args.m3105_dir,
        m3084_dir=args.m3084_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"validation_episode_rows={summary['validation_episode_row_count']}")
    print(f"validation_failure_rows={summary['validation_failure_row_count']}")
    print(f"success_count={summary['validation_success_count']}")
    print(f"collision_count={summary['validation_collision_count']}")
    print(f"offtrack_count={summary['validation_offtrack_count']}")
    print(f"speed_too_low_count={summary['validation_speed_too_low_count']}")
    print(f"same_case_outcome_match_count={summary['same_case_outcome_match_count']}")
    print(f"known_failure_preserved_count={summary['known_failure_preserved_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
