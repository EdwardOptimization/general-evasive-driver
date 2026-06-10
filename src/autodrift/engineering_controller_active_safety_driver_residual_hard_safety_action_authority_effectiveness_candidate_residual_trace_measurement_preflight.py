"""Run M3205 action-authority/effectiveness candidate residual-trace measurement."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    env_config_for_executable_profile,
    read_csv_rows,
    write_run_state,
)
from autodrift.controller_profile_runtime import wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_blocker_axis_trace_execution_materialization_preflight as m3189
import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_neutral_candidate_vs_incumbent_trace_delta_diagnostic_materialization_preflight as m3199
from autodrift.engineering_controller_active_safety_driver_residual_hard_safety_action_authority_effectiveness_candidate_implementation_materialization_preflight import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
    POLICY_CONFIG,
    POLICY_ID,
    action_authority_effectiveness_candidate_action,
)
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight as m3075


MILESTONE_ID = (
    "m3205-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-candidate-residual-trace-measurement-preflight"
)
NEXT_ID = (
    "m3206-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-candidate-residual-trace-measurement-result-audit"
)
M3204_ID = (
    "m3204-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-candidate-implementation-result-audit"
)
M3203_ID = (
    "m3203-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-candidate-implementation-materialization-preflight"
)
M3199_ID = (
    "m3199-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-neutral-candidate-vs-incumbent-"
    "trace-delta-diagnostic-materialization-preflight"
)
M3189_ID = (
    "m3189-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-execution-materialization-preflight"
)
M3187_ID = (
    "m3187-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-spec-materialization-preflight"
)
M3012_ID = "m3012-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-preflight"

DEFAULT_M3204_AUDIT = Path(f"docs/{M3204_ID}.md")
DEFAULT_M3203_DIR = Path(
    "runs/m3203_engineering_controller_active_safety_driver_residual_hard_safety_"
    "action_authority_effectiveness_candidate_implementation_materialization_preflight"
)
DEFAULT_M3199_DIR = Path(
    "runs/m3199_engineering_controller_active_safety_driver_residual_hard_safety_"
    "preterminal_authority_boundary_stability_neutral_candidate_vs_incumbent_"
    "trace_delta_diagnostic_materialization_preflight"
)
DEFAULT_M3189_DIR = Path(
    "runs/m3189_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_trace_execution_materialization_preflight"
)
DEFAULT_M3187_DIR = Path(
    "runs/m3187_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_trace_spec_materialization_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3205_engineering_controller_active_safety_driver_residual_hard_safety_"
    "action_authority_effectiveness_candidate_residual_trace_measurement_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TRACE_BINDINGS = 7
EXPECTED_TRACE_AXES = {
    "clearance_timing_axis",
    "boundary_recovery_collision_axis",
    "boundary_recovery_stability_axis",
}
DELTA_EPS = 1.0e-5
FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)
CLAIM_SCOPE = (
    "M3205 Active Safety Driver residual hard-safety action-authority/effectiveness "
    "candidate residual-trace measurement preflight only; the seven accepted residual "
    "blocker trace bindings may be executed through the M3203 deterministic obs72-to-action3 "
    "candidate and compared offline against same-trace M3199/M3194 candidate and M3189 "
    "incumbent evidence. Artifacts may include candidate trace rows, trace-step rows, "
    "same-trace comparison rows, guards, claims, gates, doc, and M3206 audit manifest. "
    "No validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "public driver default mutation, driver-performance verdict, current-sim verdict, "
    "repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint "
    "promotion, public driver default replacement, high-fidelity validation readiness or "
    "result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, "
    "or level3 self-identification"
)

CANDIDATE_TRACE_EXECUTION_FIELDNAMES = [
    *m3189.TRACE_EXECUTION_FIELDNAMES,
    "m3194_trace_execution_id",
    "incumbent_trace_execution_id",
]
CANDIDATE_TRACE_STEP_FIELDNAMES = [
    *m3189.TRACE_STEP_FIELDNAMES,
    "m3194_trace_execution_id",
    "incumbent_trace_execution_id",
]
TRACE_FAILURE_FIELDNAMES = m3189.TRACE_FAILURE_FIELDNAMES
COMPARISON_FIELDNAMES = [
    "comparison_id",
    "trace_source_binding_id",
    "evidence_axis",
    "fresh_panel_row_id",
    "source_measurement_episode_id",
    "blocker_family",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "m3205_trace_execution_id",
    "m3199_m3194_trace_execution_id",
    "m3189_incumbent_trace_execution_id",
    "m3205_success",
    "m3194_success",
    "incumbent_success",
    "m3205_collision",
    "m3194_collision",
    "incumbent_collision",
    "m3205_offtrack",
    "m3194_offtrack",
    "incumbent_offtrack",
    "m3205_termination_reason",
    "m3194_termination_reason",
    "incumbent_termination_reason",
    "m3205_min_clearance_margin",
    "m3194_min_clearance_margin",
    "incumbent_min_clearance_margin",
    "m3205_vs_m3194_clearance_margin_delta",
    "m3205_vs_incumbent_clearance_margin_delta",
    "m3205_return",
    "m3194_return",
    "incumbent_return",
    "m3205_vs_m3194_return_delta",
    "m3205_vs_incumbent_return_delta",
    "m3205_speed_mean",
    "m3194_speed_mean",
    "incumbent_speed_mean",
    "m3205_vs_m3194_speed_mean_delta",
    "m3205_vs_incumbent_speed_mean_delta",
    "aligned_step_count_vs_m3194",
    "obs_hash_match_count_vs_m3194",
    "meaningful_action_delta_step_count_vs_m3194",
    "preterminal_action_delta_step_count_vs_m3194",
    "terminal_window_action_delta_step_count_vs_m3194",
    "mean_action_delta_l2_vs_m3194",
    "max_action_delta_l2_vs_m3194",
    "aligned_step_count_vs_incumbent",
    "obs_hash_match_count_vs_incumbent",
    "meaningful_action_delta_step_count_vs_incumbent",
    "preterminal_action_delta_step_count_vs_incumbent",
    "terminal_window_action_delta_step_count_vs_incumbent",
    "mean_action_delta_l2_vs_incumbent",
    "max_action_delta_l2_vs_incumbent",
    "outcome_changed_vs_m3194",
    "outcome_changed_vs_incumbent",
    "hard_safety_delta_vs_m3194",
    "hard_safety_delta_vs_incumbent",
    "hard_safety_improved_vs_m3194",
    "hard_safety_improved_vs_incumbent",
    "hard_safety_regressed_vs_m3194",
    "hard_safety_regressed_vs_incumbent",
    "validation_run",
    "repair_success_claim_made",
    "claim_boundary",
]
GUARD_FIELDNAMES = m3189.GUARD_FIELDNAMES
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3205",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = m3189.GATE_FIELDNAMES


def _bool(value: Any) -> bool:
    return m3189._bool(value)


def _float(value: Any, default: float = 0.0) -> float:
    return m3189._float(value, default)


def _int(value: Any, default: int = 0) -> int:
    return m3189._int(value, default)


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return float(np.mean(items)) if items else 0.0


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _bad_count(row: Mapping[str, Any]) -> int:
    return int(_bool(row.get("collision", False))) + int(_offtrack(row))


def _outcome_changed(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return (
        _bool(left.get("success", False)) != _bool(right.get("success", False))
        or _bool(left.get("collision", False)) != _bool(right.get("collision", False))
        or _offtrack(left) != _offtrack(right)
    )


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "candidate_trace_execution_rows": output_dir / "candidate_trace_execution_rows.csv",
        "candidate_trace_step_rows": output_dir / "candidate_trace_step_rows.csv",
        "trace_failure_rows": output_dir / "trace_failure_rows.csv",
        "same_trace_comparison_rows": output_dir / "same_trace_comparison_rows.csv",
        "contract_guard_rows": output_dir / "contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3204_audit: Path,
    m3203_dir: Path,
    m3199_dir: Path,
    m3189_dir: Path,
    m3187_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3204_audit": m3204_audit,
        "m3203_summary": m3203_dir / "summary.json",
        "m3203_gate_rows": m3203_dir / "gate_matrix.csv",
        "m3203_runtime_contract_rows": m3203_dir / "runtime_contract_rows.csv",
        "m3199_summary": m3199_dir / "summary.json",
        "m3199_candidate_trace_execution_rows": m3199_dir / "candidate_trace_execution_rows.csv",
        "m3199_candidate_trace_step_rows": m3199_dir / "candidate_trace_step_rows.csv",
        "m3199_gate_rows": m3199_dir / "gate_matrix.csv",
        "m3189_summary": m3189_dir / "summary.json",
        "m3189_trace_execution_rows": m3189_dir / "trace_execution_rows.csv",
        "m3189_trace_step_rows": m3189_dir / "trace_step_rows.csv",
        "m3189_gate_rows": m3189_dir / "gate_matrix.csv",
        "m3187_summary": m3187_dir / "summary.json",
        "m3187_trace_source_bindings": m3187_dir / "trace_source_binding_rows.csv",
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3204_audit_text": paths["m3204_audit"].read_text(encoding="utf-8") if exists["m3204_audit"] else "",
        "m3203_summary": read_json(paths["m3203_summary"]) if exists["m3203_summary"] else {},
        "m3203_gate_rows": read_csv_rows(paths["m3203_gate_rows"]),
        "m3203_runtime_contract_rows": read_csv_rows(paths["m3203_runtime_contract_rows"]),
        "m3199_summary": read_json(paths["m3199_summary"]) if exists["m3199_summary"] else {},
        "m3199_candidate_trace_execution_rows": read_csv_rows(paths["m3199_candidate_trace_execution_rows"]),
        "m3199_candidate_trace_step_rows": read_csv_rows(paths["m3199_candidate_trace_step_rows"]),
        "m3199_gate_rows": read_csv_rows(paths["m3199_gate_rows"]),
        "m3189_summary": read_json(paths["m3189_summary"]) if exists["m3189_summary"] else {},
        "m3189_trace_execution_rows": read_csv_rows(paths["m3189_trace_execution_rows"]),
        "m3189_trace_step_rows": read_csv_rows(paths["m3189_trace_step_rows"]),
        "m3189_gate_rows": read_csv_rows(paths["m3189_gate_rows"]),
        "m3187_summary": read_json(paths["m3187_summary"]) if exists["m3187_summary"] else {},
        "m3187_trace_source_bindings": read_csv_rows(paths["m3187_trace_source_bindings"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def _hidden_label_violation(*rows: Mapping[str, Any]) -> bool:
    fields = (
        "hidden_oracle_actor_input_required",
        "target_labels_actor_visible",
        "target_provenance_actor_visible",
        "source_labels_actor_visible",
        "route_labels_actor_visible",
        "outcome_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
        "ttc_actor_input_required",
        "runtime_label_inputs_used",
    )
    return any(_bool(row.get(field, False)) for row in rows for field in fields)


def trace_execution_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    workloads = {
        str(row.get("executable_workload_id", "")): dict(row)
        for row in source["m3012_workload_rows"]
    }
    bindings = {
        str(row.get("trace_source_binding_id", "")): dict(row)
        for row in source["m3187_trace_source_bindings"]
    }
    m3194_by_binding = {
        str(row.get("trace_source_binding_id", "")): dict(row)
        for row in source["m3199_candidate_trace_execution_rows"]
    }
    rows = sorted(
        (dict(row) for row in source["m3189_trace_execution_rows"]),
        key=lambda row: str(row.get("trace_execution_id", "")),
    )
    plan: list[dict[str, Any]] = []
    for index, incumbent in enumerate(rows, start=1):
        binding = bindings.get(str(incumbent.get("trace_source_binding_id", "")), {})
        m3194 = m3194_by_binding.get(str(incumbent.get("trace_source_binding_id", "")), {})
        workload = workloads.get(str(incumbent.get("executable_workload_id", "")), {})
        config_path = str(workload.get("config_path", ""))
        eval_seed = _int(incumbent.get("eval_seed"), 0)
        hidden_label_violation = _hidden_label_violation(binding, incumbent, workload)
        status_pass = bool(
            _bool(source["m3203_summary"].get("status_pass", False))
            and _bool(source["m3199_summary"].get("status_pass", False))
            and _bool(source["m3189_summary"].get("status_pass", False))
            and _bool(incumbent.get("scheduled_status_pass", False))
            and _bool(workload.get("status_pass", False))
            and bool(m3194)
            and Path(config_path).exists()
            and eval_seed > 0
            and str(incumbent.get("output_semantics", "")) == OUTPUT_SEMANTICS
            and not _bool(incumbent.get("runtime_base_policy_required", True))
            and not hidden_label_violation
        )
        plan.append(
            {
                **incumbent,
                **workload,
                "trace_execution_id": f"m3205-candidate-trace-execution-{index:04d}",
                "m3194_trace_execution_id": m3194.get("trace_execution_id", ""),
                "incumbent_trace_execution_id": incumbent.get("trace_execution_id", ""),
                "trace_source_binding_id": incumbent.get("trace_source_binding_id", ""),
                "evidence_axis": incumbent.get("evidence_axis", ""),
                "source_measurement_episode_id": incumbent.get("source_measurement_episode_id", ""),
                "fresh_panel_row_id": incumbent.get("fresh_panel_row_id", ""),
                "blocker_family": incumbent.get("blocker_family", ""),
                "axis_id": incumbent.get("axis_id", ""),
                "binding_role": incumbent.get("binding_role", ""),
                "task_family": incumbent.get("task_family", ""),
                "base_profile_name": workload.get("profile_binding_name", incumbent.get("base_profile_name", "")),
                "config_path": config_path,
                "eval_seed": eval_seed,
                "hidden_label_violation": hidden_label_violation,
                "status_pass": status_pass,
            }
        )
    return plan


class M3205CandidateTraceDriver:
    def act(self, observation: np.ndarray) -> np.ndarray:
        return action_authority_effectiveness_candidate_action(observation, POLICY_CONFIG)


def failure_row(plan: Mapping[str, Any], *, error_type: str, error_message: str) -> dict[str, Any]:
    row = m3189.failure_row(plan, error_type=error_type, error_message=error_message)
    row.update(
        {
            "trace_failure_id": f"m3205-trace-failure-{plan.get('trace_execution_id', '')}",
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def _rewrite_candidate_execution(plan: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(row)
    item.update(
        {
            "runtime_driver_id": POLICY_ID,
            "claim_boundary": CLAIM_SCOPE,
            "m3194_trace_execution_id": plan.get("m3194_trace_execution_id", ""),
            "incumbent_trace_execution_id": plan.get("incumbent_trace_execution_id", ""),
            "public_driver_default_mutated": False,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
        }
    )
    return item


def _rewrite_candidate_steps(plan: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item.update(
            {
                "claim_boundary": CLAIM_SCOPE,
                "m3194_trace_execution_id": plan.get("m3194_trace_execution_id", ""),
                "incumbent_trace_execution_id": plan.get("incumbent_trace_execution_id", ""),
            }
        )
        updated.append(item)
    return updated


def run_candidate_trace_execution_plan(
    *,
    plan_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    output_dir: Path,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): dict(row)
        for row in executable_specs
    }
    profile_cache: dict[tuple[str, str], dict[str, Any]] = {}
    driver = M3205CandidateTraceDriver()
    executions: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("M3205 trace execution plan row failed pre-execution guards")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            cache_key = (profile_name, config_path)
            if cache_key not in profile_cache:
                profile_cache[cache_key] = m3075.profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
            env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_cache[cache_key])
            wrapped = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_cache[cache_key])
            wrapped.close()
            execution, trace_rows = m3189.run_trace_execution(
                plan=plan,
                executable_spec=executable_spec,
                profile_config=profile_cache[cache_key],
                driver=driver,
            )
            executions.append(_rewrite_candidate_execution(plan, execution))
            steps.extend(_rewrite_candidate_steps(plan, trace_rows))
        except Exception as exc:  # noqa: BLE001
            failures.append(failure_row(plan, error_type=type(exc).__name__, error_message=str(exc)))
        write_run_state(
            output_dir / "run_state.json",
            {
                "scheduled_trace_execution_row_count": len(plan_rows),
                "candidate_trace_execution_row_count": len(executions),
                "candidate_trace_step_row_count": len(steps),
                "trace_failure_row_count": len(failures),
                "latest_trace_execution_id": plan.get("trace_execution_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return {"executions": executions, "steps": steps, "failures": failures}


def _steps_by_binding(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("trace_source_binding_id", "")), []).append(dict(row))
    for binding_id in grouped:
        grouped[binding_id].sort(key=lambda row: _int(row.get("step_index"), 0))
    return grouped


def _step_delta_stats(
    candidate_steps: list[dict[str, Any]],
    baseline_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_by_step = {_int(row.get("step_index"), 0): row for row in candidate_steps}
    baseline_by_step = {_int(row.get("step_index"), 0): row for row in baseline_steps}
    candidate_count = len(candidate_steps)
    baseline_count = len(baseline_steps)
    deltas: list[float] = []
    terminal_deltas: list[float] = []
    preterminal_count = 0
    terminal_count = 0
    obs_match_count = 0
    aligned_count = 0
    for step_index in sorted(set(candidate_by_step) & set(baseline_by_step)):
        candidate = candidate_by_step[step_index]
        baseline = baseline_by_step[step_index]
        aligned_count += 1
        obs_match_count += int(str(candidate.get("obs72_sha256", "")) == str(baseline.get("obs72_sha256", "")))
        candidate_action = np.asarray(
            [
                _float(candidate.get("final_steer")),
                _float(candidate.get("final_throttle")),
                _float(candidate.get("final_brake")),
            ],
            dtype=np.float32,
        )
        baseline_action = np.asarray(
            [
                _float(baseline.get("final_steer")),
                _float(baseline.get("final_throttle")),
                _float(baseline.get("final_brake")),
            ],
            dtype=np.float32,
        )
        delta_l2 = float(np.linalg.norm(candidate_action - baseline_action))
        deltas.append(delta_l2)
        if delta_l2 <= DELTA_EPS:
            continue
        terminal_window = step_index >= max(candidate_count - 5, 0) or step_index >= max(baseline_count - 5, 0)
        if terminal_window:
            terminal_count += 1
            terminal_deltas.append(delta_l2)
        else:
            preterminal_count += 1
    return {
        "aligned_step_count": aligned_count,
        "obs_hash_match_count": obs_match_count,
        "meaningful_action_delta_step_count": sum(value > DELTA_EPS for value in deltas),
        "preterminal_action_delta_step_count": preterminal_count,
        "terminal_window_action_delta_step_count": terminal_count,
        "mean_action_delta_l2": _mean(deltas),
        "max_action_delta_l2": max(deltas, default=0.0),
        "terminal_window_mean_action_delta_l2": _mean(terminal_deltas),
    }


def same_trace_comparison_rows(
    *,
    m3205_executions: list[dict[str, Any]],
    m3205_steps: list[dict[str, Any]],
    m3194_executions: list[dict[str, Any]],
    m3194_steps: list[dict[str, Any]],
    incumbent_executions: list[dict[str, Any]],
    incumbent_steps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m3205_by_binding = {str(row.get("trace_source_binding_id", "")): dict(row) for row in m3205_executions}
    m3194_by_binding = {str(row.get("trace_source_binding_id", "")): dict(row) for row in m3194_executions}
    incumbent_by_binding = {str(row.get("trace_source_binding_id", "")): dict(row) for row in incumbent_executions}
    m3205_steps_by_binding = _steps_by_binding(m3205_steps)
    m3194_steps_by_binding = _steps_by_binding(m3194_steps)
    incumbent_steps_by_binding = _steps_by_binding(incumbent_steps)
    rows: list[dict[str, Any]] = []
    for binding_id in sorted(set(m3205_by_binding) | set(m3194_by_binding) | set(incumbent_by_binding)):
        candidate = m3205_by_binding.get(binding_id, {})
        m3194 = m3194_by_binding.get(binding_id, {})
        incumbent = incumbent_by_binding.get(binding_id, {})
        context = candidate or m3194 or incumbent
        stats_m3194 = _step_delta_stats(m3205_steps_by_binding.get(binding_id, []), m3194_steps_by_binding.get(binding_id, []))
        stats_incumbent = _step_delta_stats(
            m3205_steps_by_binding.get(binding_id, []),
            incumbent_steps_by_binding.get(binding_id, []),
        )
        delta_vs_m3194 = _bad_count(m3194) - _bad_count(candidate)
        delta_vs_incumbent = _bad_count(incumbent) - _bad_count(candidate)
        rows.append(
            {
                "comparison_id": f"m3205-same-trace-comparison-{len(rows) + 1:04d}",
                "trace_source_binding_id": binding_id,
                "evidence_axis": context.get("evidence_axis", ""),
                "fresh_panel_row_id": context.get("fresh_panel_row_id", ""),
                "source_measurement_episode_id": context.get("source_measurement_episode_id", ""),
                "blocker_family": context.get("blocker_family", ""),
                "axis_id": context.get("axis_id", ""),
                "binding_role": context.get("binding_role", ""),
                "task_family": context.get("task_family", ""),
                "eval_seed": context.get("eval_seed", ""),
                "m3205_trace_execution_id": candidate.get("trace_execution_id", ""),
                "m3199_m3194_trace_execution_id": m3194.get("trace_execution_id", ""),
                "m3189_incumbent_trace_execution_id": incumbent.get("trace_execution_id", ""),
                "m3205_success": _bool(candidate.get("success", False)),
                "m3194_success": _bool(m3194.get("success", False)),
                "incumbent_success": _bool(incumbent.get("success", False)),
                "m3205_collision": _bool(candidate.get("collision", False)),
                "m3194_collision": _bool(m3194.get("collision", False)),
                "incumbent_collision": _bool(incumbent.get("collision", False)),
                "m3205_offtrack": _offtrack(candidate),
                "m3194_offtrack": _offtrack(m3194),
                "incumbent_offtrack": _offtrack(incumbent),
                "m3205_termination_reason": candidate.get("termination_reason", ""),
                "m3194_termination_reason": m3194.get("termination_reason", ""),
                "incumbent_termination_reason": incumbent.get("termination_reason", ""),
                "m3205_min_clearance_margin": _float(candidate.get("min_clearance_margin")),
                "m3194_min_clearance_margin": _float(m3194.get("min_clearance_margin")),
                "incumbent_min_clearance_margin": _float(incumbent.get("min_clearance_margin")),
                "m3205_vs_m3194_clearance_margin_delta": _float(candidate.get("min_clearance_margin")) - _float(m3194.get("min_clearance_margin")),
                "m3205_vs_incumbent_clearance_margin_delta": _float(candidate.get("min_clearance_margin")) - _float(incumbent.get("min_clearance_margin")),
                "m3205_return": _float(candidate.get("return")),
                "m3194_return": _float(m3194.get("return")),
                "incumbent_return": _float(incumbent.get("return")),
                "m3205_vs_m3194_return_delta": _float(candidate.get("return")) - _float(m3194.get("return")),
                "m3205_vs_incumbent_return_delta": _float(candidate.get("return")) - _float(incumbent.get("return")),
                "m3205_speed_mean": _float(candidate.get("speed_mean")),
                "m3194_speed_mean": _float(m3194.get("speed_mean")),
                "incumbent_speed_mean": _float(incumbent.get("speed_mean")),
                "m3205_vs_m3194_speed_mean_delta": _float(candidate.get("speed_mean")) - _float(m3194.get("speed_mean")),
                "m3205_vs_incumbent_speed_mean_delta": _float(candidate.get("speed_mean")) - _float(incumbent.get("speed_mean")),
                "aligned_step_count_vs_m3194": stats_m3194["aligned_step_count"],
                "obs_hash_match_count_vs_m3194": stats_m3194["obs_hash_match_count"],
                "meaningful_action_delta_step_count_vs_m3194": stats_m3194["meaningful_action_delta_step_count"],
                "preterminal_action_delta_step_count_vs_m3194": stats_m3194["preterminal_action_delta_step_count"],
                "terminal_window_action_delta_step_count_vs_m3194": stats_m3194["terminal_window_action_delta_step_count"],
                "mean_action_delta_l2_vs_m3194": stats_m3194["mean_action_delta_l2"],
                "max_action_delta_l2_vs_m3194": stats_m3194["max_action_delta_l2"],
                "aligned_step_count_vs_incumbent": stats_incumbent["aligned_step_count"],
                "obs_hash_match_count_vs_incumbent": stats_incumbent["obs_hash_match_count"],
                "meaningful_action_delta_step_count_vs_incumbent": stats_incumbent["meaningful_action_delta_step_count"],
                "preterminal_action_delta_step_count_vs_incumbent": stats_incumbent["preterminal_action_delta_step_count"],
                "terminal_window_action_delta_step_count_vs_incumbent": stats_incumbent["terminal_window_action_delta_step_count"],
                "mean_action_delta_l2_vs_incumbent": stats_incumbent["mean_action_delta_l2"],
                "max_action_delta_l2_vs_incumbent": stats_incumbent["max_action_delta_l2"],
                "outcome_changed_vs_m3194": _outcome_changed(candidate, m3194),
                "outcome_changed_vs_incumbent": _outcome_changed(candidate, incumbent),
                "hard_safety_delta_vs_m3194": delta_vs_m3194,
                "hard_safety_delta_vs_incumbent": delta_vs_incumbent,
                "hard_safety_improved_vs_m3194": delta_vs_m3194 > 0,
                "hard_safety_improved_vs_incumbent": delta_vs_incumbent > 0,
                "hard_safety_regressed_vs_m3194": delta_vs_m3194 < 0,
                "hard_safety_regressed_vs_incumbent": delta_vs_incumbent < 0,
                "validation_run": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def guard(
    guard_id: str,
    family: str,
    observed: Any,
    expected: Any,
    *,
    actor_runtime_allowed: bool = False,
) -> dict[str, Any]:
    item = m3189.guard(guard_id, family, observed, expected, actor_runtime_allowed=actor_runtime_allowed)
    item["guard_id"] = str(item["guard_id"]).replace("m3189-", "m3205-", 1)
    item["claim_boundary"] = CLAIM_SCOPE
    return item


def contract_guard_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sample_action = action_authority_effectiveness_candidate_action(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32), POLICY_CONFIG)
    hidden_inputs_used = any(
        _bool(row.get("hidden_oracle_actor_input_required", False))
        or _bool(row.get("source_labels_actor_visible", False))
        or _bool(row.get("route_labels_actor_visible", False))
        or _bool(row.get("outcome_labels_actor_visible", False))
        or _bool(row.get("success_progress_labels_actor_visible", False))
        or _bool(row.get("verdict_labels_actor_visible", False))
        or _bool(row.get("ttc_actor_input_required", False))
        or _bool(row.get("runtime_label_inputs_used", False))
        for row in plan_rows + executions + steps + failures
    )
    executed_bindings = {str(row.get("trace_source_binding_id", "")) for row in executions}
    comparison_bindings = {str(row.get("trace_source_binding_id", "")) for row in comparisons}
    return [
        guard("source_artifacts_present", "source", all(source["source_exists"].values()), True),
        guard("trace_binding_plan_rows", "source", len(plan_rows), EXPECTED_TRACE_BINDINGS),
        guard("candidate_trace_execution_rows", "execution", len(executions), EXPECTED_TRACE_BINDINGS),
        guard("same_trace_comparison_rows", "comparison", len(comparisons), EXPECTED_TRACE_BINDINGS),
        guard("binding_ids_preserved", "comparison", sorted(comparison_bindings), sorted(executed_bindings)),
        guard("observation_shape", "contract", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, actor_runtime_allowed=True),
        guard("action_shape", "contract", ACTION_DIM, ACTION_DIM, actor_runtime_allowed=True),
        guard("action_components", "contract", "|".join(ACTION_COMPONENTS), "steer|throttle|brake", actor_runtime_allowed=True),
        guard("output_semantics", "contract", OUTPUT_SEMANTICS, "direct_action_clipped", actor_runtime_allowed=True),
        guard("sample_action_shape", "runtime_api", tuple(sample_action.shape), (ACTION_DIM,), actor_runtime_allowed=True),
        guard("sample_action_finite", "runtime_api", bool(np.all(np.isfinite(sample_action))), True, actor_runtime_allowed=True),
        guard("sample_action_bounded", "runtime_api", bool(np.max(np.abs(sample_action)) <= 1.0), True, actor_runtime_allowed=True),
        guard("actor_runtime_inputs", "contract", {row.get("actor_runtime_inputs") for row in steps} if steps else set(), {"obs72"}),
        guard("hidden_runtime_inputs_used", "contract", hidden_inputs_used, False),
        guard("terminal_status_offline_only", "contract", all(_bool(row.get("terminal_status_offline_only", False)) for row in executions + steps), True),
        guard("trace_failures", "execution", len(failures), 0),
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("candidate_trace_execution_rows", "trace_execution_artifact", True, True, "candidate_trace_execution_rows.csv"),
        ("candidate_trace_step_rows", "trace_execution_artifact", True, True, "candidate_trace_step_rows.csv"),
        ("same_trace_comparison_rows", "measurement_artifact", True, True, "same_trace_comparison_rows.csv"),
        ("contract_guard_rows", "contract", True, True, "contract_guard_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("validation_result", "forbidden", False, False, "separate validation execution route"),
        ("driver_performance_verdict", "forbidden", False, False, "future proof generalization and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "future audited result synthesis"),
        ("robustness_result", "forbidden", False, False, "future robustness panel measurement"),
        ("repair_success", "forbidden", False, False, "accepted measurement improvement plus validation route"),
        ("ranking_or_winner_selection", "forbidden", False, False, "future audited ranking route"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("public_driver_default_mutation", "forbidden", False, False, "future admitted implementation route"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3205"),
    ]
    return [
        {
            "claim_id": f"m3205-{claim_id}",
            "claim_family": family,
            "allowed_in_m3205": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3205-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _m3204_selects_m3205(text: str) -> bool:
    return (
        "m3205-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-effectiveness-candidate-residual-trace-measurement-preflight"
        in text
        or "routes to M3205 residual-trace measurement" in text
    )


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    binding_ids = {str(row.get("trace_source_binding_id", "")) for row in plan_rows}
    executed_binding_ids = {str(row.get("trace_source_binding_id", "")) for row in executions}
    comparison_binding_ids = {str(row.get("trace_source_binding_id", "")) for row in comparisons}
    axis_counts = Counter(str(row.get("evidence_axis", "")) for row in executions)
    hidden_inputs_used = any(
        _bool(row.get("hidden_oracle_actor_input_required", False))
        or _bool(row.get("source_labels_actor_visible", False))
        or _bool(row.get("route_labels_actor_visible", False))
        or _bool(row.get("outcome_labels_actor_visible", False))
        or _bool(row.get("success_progress_labels_actor_visible", False))
        or _bool(row.get("verdict_labels_actor_visible", False))
        or _bool(row.get("ttc_actor_input_required", False))
        or _bool(row.get("runtime_label_inputs_used", False))
        for row in plan_rows + executions + steps + failures
    )
    overclaim_made = any(
        _bool(row.get(key, False))
        for row in executions + steps + failures + comparisons
        for key in (
            "driver_performance_claim_made",
            "repair_success_claim_made",
            "robustness_result_claim_made",
            "validation_result_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "full_ideal_driver_completion_claim_made",
            "feasibility_proof_claim_made",
            "level3_self_id_claim_made",
        )
    )
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3204_selects_m3205_route", "lineage", _m3204_selects_m3205(source["m3204_audit_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3203_status_pass", "lineage", _bool(source["m3203_summary"].get("status_pass")), source["m3203_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3203_gate_matrix_pass", "lineage", _bool(source["m3203_summary"].get("gate_matrix_pass")), source["m3203_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3199_status_pass", "lineage", _bool(source["m3199_summary"].get("status_pass")), source["m3199_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3199_gate_matrix_pass", "lineage", _bool(source["m3199_summary"].get("gate_matrix_pass")), source["m3199_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3189_status_pass", "lineage", _bool(source["m3189_summary"].get("status_pass")), source["m3189_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3189_gate_matrix_pass", "lineage", _bool(source["m3189_summary"].get("gate_matrix_pass")), source["m3189_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("scheduled_trace_bindings", "execution", len(plan_rows) == EXPECTED_TRACE_BINDINGS, len(plan_rows), EXPECTED_TRACE_BINDINGS, "scenario_sampling_failure"),
        gate("candidate_trace_execution_rows", "execution", len(executions) == EXPECTED_TRACE_BINDINGS, len(executions), EXPECTED_TRACE_BINDINGS, "metric_artifact"),
        gate("candidate_trace_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("candidate_trace_step_rows", "execution", len(steps) > 0, len(steps), ">0", "metric_artifact"),
        gate("binding_ids_preserved", "execution", binding_ids == executed_binding_ids == comparison_binding_ids, sorted(comparison_binding_ids), sorted(binding_ids), "metric_artifact"),
        gate("trace_axes_present", "evidence", EXPECTED_TRACE_AXES.issubset(set(axis_counts)), dict(axis_counts), sorted(EXPECTED_TRACE_AXES), "metric_artifact"),
        gate("same_trace_comparison_rows", "measurement", len(comparisons) == EXPECTED_TRACE_BINDINGS, len(comparisons), EXPECTED_TRACE_BINDINGS, "metric_artifact"),
        gate("actor_runtime_obs72_only", "contract", all(str(row.get("actor_runtime_inputs", "")) == "obs72" for row in steps), "all", "obs72", "contract_violation"),
        gate("action3_direct_components", "contract", all(str(row.get("action_components", "")) == "steer|throttle|brake" for row in executions), "all", "steer|throttle|brake", "contract_violation"),
        gate("hidden_inputs_not_used", "contract", not hidden_inputs_used, hidden_inputs_used, False, "contract_violation"),
        gate("runtime_base_policy_not_required", "contract", not any(_bool(row.get("runtime_base_policy_required", False)) for row in executions + failures), "none", "required", "contract_violation"),
        gate("public_driver_not_mutated", "contract", not any(_bool(row.get("public_driver_default_mutated", False)) for row in executions), "none", "mutated", "contract_violation"),
        gate("terminal_status_offline_only", "contract", all(_bool(row.get("terminal_status_offline_only", False)) for row in executions + steps), "all", "offline_only", "contract_violation"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass")) for row in guards), "all", "pass", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claims) and not overclaim_made, "all", "pass", "proof_washout"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 32060,
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
        "hypothesis": "A bounded result audit can accept or reject M3205 residual-trace measurement artifacts before full-fresh measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "candidate_trace_execution_rows.csv"),
                str(output_dir / "candidate_trace_step_rows.csv"),
                str(output_dir / "same_trace_comparison_rows.csv"),
                str(output_dir / "contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3205 residual-trace measurement before full-fresh measurement or synthesis"],
            "derived_from": [MILESTONE_ID, M3204_ID, M3203_ID, M3199_ID, M3189_ID, M3187_ID, M3012_ID],
            "blocked_by": [
                "M3205 measurement artifacts require audit before interpretation",
                "M3205 is measurement only and not validation repair success or public default replacement",
            ],
            "supersedes": ["unreviewed M3205 residual-trace measurement interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3206 must audit M3205 candidate trace rows step rows same-trace comparison rows guards claims and gates",
            "M3206 must preserve obs72-only actor runtime and direct [steer throttle brake] action contract",
            "M3206 must reject validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3206 must select full-fresh measurement artifact-repair synthesis or stop as exactly one route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune rank promote or mutate checkpoints in M3206",
            "do not convert M3205 residual-trace measurement into validation repair-success performance current-sim robustness-result high-fidelity paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_action_authority_effectiveness",
            "evidence_axis": "action_authority_effectiveness_residual_trace_measurement_result_audit",
            "evidence_increment": "audits same-seven residual-trace closed-loop measurement for the M3203 candidate",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3205 artifacts are missing or gate matrix fails",
                "stop if any trace execution used hidden runtime labels",
                "synthesize if residual traces show no closed-loop benefit or a behavior regression",
            ],
            "fallback_plan": [
                "route to M3205 artifact repair if rows or guards fail",
                "route to synthesis if residual-trace measurement is behavior-negative or inconclusive",
                "route to full-fresh measurement only if M3206 accepts a non-regressive residual-trace result",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3205 materializes residual-trace measurement artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3205 residual-trace measurement artifacts",
            "admission_evidence": [
                "M3205 summary candidate trace rows step rows same-trace comparison rows contract guards claim rows and gate matrix"
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or public driver mutation",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3206 status queue scoreboard research log and review",
                "one follow-up manifest only if M3206 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3206 accepts or rejects M3205 as complete and claim-safe",
                "next full-fresh measurement synthesis artifact-repair or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3206 audits engineering residual-trace measurement and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3206; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3205 residual-trace measurement artifacts only.",
            "negative_result_policy": "Preserve engineering measurement evidence and route full-fresh measurement synthesis or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3205 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 1,
            "evidence_expansion": "audits same-seven residual-trace closed-loop evidence before full-fresh measurement or synthesis",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3206 audits engineering measurement evidence",
            "must_synthesize_if": [
                "M3206 cannot select full-fresh measurement synthesis artifact-repair or stop",
                "M3206 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3206 audits M3205 row counts gates actor contract and claim boundaries",
            "M3206 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3206 hides missing M3205 artifacts or failed gates",
            "M3206 treats M3205 traces as repair success or performance verdict",
            "M3206 changes actor input action contract or public driver default",
            "M3206 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3206 audits M3205 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_action_authority_effectiveness_candidate_residual_trace_measurement_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3205 Action-Authority/Effectiveness Candidate Residual-Trace Measurement Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- scheduled trace bindings: {summary['scheduled_trace_execution_row_count']}",
            f"- candidate trace execution rows: {summary['candidate_trace_execution_row_count']}",
            f"- candidate trace step rows: {summary['candidate_trace_step_row_count']}",
            f"- same-trace comparison rows: {summary['same_trace_comparison_row_count']}",
            f"- M3205 success/collision/offtrack: {summary['m3205_success_count']}/{summary['m3205_collision_count']}/{summary['m3205_offtrack_count']}",
            f"- M3194 success/collision/offtrack: {summary['m3194_success_count']}/{summary['m3194_collision_count']}/{summary['m3194_offtrack_count']}",
            f"- incumbent success/collision/offtrack: {summary['incumbent_success_count']}/{summary['incumbent_collision_count']}/{summary['incumbent_offtrack_count']}",
            f"- outcome changed vs M3194/incumbent: {summary['outcome_changed_vs_m3194_count']}/{summary['outcome_changed_vs_incumbent_count']}",
            f"- hidden actor inputs used: {summary['hidden_actor_inputs_used']}",
            f"- validation run: {summary['validation_run']}",
            f"- public driver default mutated: {summary['public_driver_default_mutated']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3205 executes the same seven residual blocker trace bindings through the M3203 candidate and compares same-trace outcomes and public action telemetry against M3199/M3194 and M3189 incumbent artifacts. This is measurement preflight evidence only, not validation, repair success, ranking, promotion, or a deployable-driver verdict.",
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


def run_residual_trace_measurement_preflight(
    *,
    m3204_audit: Path,
    m3203_dir: Path,
    m3199_dir: Path,
    m3189_dir: Path,
    m3187_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    device: str = "cpu",
) -> dict[str, Any]:
    del device
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3204_audit=m3204_audit,
        m3203_dir=m3203_dir,
        m3199_dir=m3199_dir,
        m3189_dir=m3189_dir,
        m3187_dir=m3187_dir,
        m3012_dir=m3012_dir,
    )
    plan_rows = trace_execution_plan(source)
    result = run_candidate_trace_execution_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    executions = result["executions"]
    steps = result["steps"]
    failures = result["failures"]
    comparisons = same_trace_comparison_rows(
        m3205_executions=executions,
        m3205_steps=steps,
        m3194_executions=source["m3199_candidate_trace_execution_rows"],
        m3194_steps=source["m3199_candidate_trace_step_rows"],
        incumbent_executions=source["m3189_trace_execution_rows"],
        incumbent_steps=source["m3189_trace_step_rows"],
    )
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    guards = contract_guard_rows(
        source=source,
        plan_rows=plan_rows,
        executions=executions,
        steps=steps,
        failures=failures,
        comparisons=comparisons,
    )
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["candidate_trace_execution_rows"], executions, fieldnames=CANDIDATE_TRACE_EXECUTION_FIELDNAMES)
    write_csv_rows(paths["candidate_trace_step_rows"], steps, fieldnames=CANDIDATE_TRACE_STEP_FIELDNAMES)
    write_csv_rows(paths["trace_failure_rows"], failures, fieldnames=TRACE_FAILURE_FIELDNAMES)
    write_csv_rows(paths["same_trace_comparison_rows"], comparisons, fieldnames=COMPARISON_FIELDNAMES)
    write_csv_rows(paths["contract_guard_rows"], guards, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        executions=executions,
        steps=steps,
        failures=failures,
        comparisons=comparisons,
        guards=guards,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    hidden_actor_inputs_used = any(
        _bool(row.get("hidden_oracle_actor_input_required", False))
        or _bool(row.get("source_labels_actor_visible", False))
        or _bool(row.get("route_labels_actor_visible", False))
        or _bool(row.get("outcome_labels_actor_visible", False))
        or _bool(row.get("success_progress_labels_actor_visible", False))
        or _bool(row.get("verdict_labels_actor_visible", False))
        or _bool(row.get("ttc_actor_input_required", False))
        or _bool(row.get("runtime_label_inputs_used", False))
        for row in plan_rows + executions + steps + failures
    )
    status_pass = bool(gate_matrix_pass and len(executions) == EXPECTED_TRACE_BINDINGS and len(failures) == 0)
    summary = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": utc_timestamp(),
        "result_class": "residual_trace_measurement_materialized" if status_pass else "residual_trace_measurement_incomplete",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "source_artifacts_present": all(source["source_exists"].values()),
        "scheduled_trace_execution_row_count": len(plan_rows),
        "candidate_trace_execution_row_count": len(executions),
        "candidate_trace_step_row_count": len(steps),
        "trace_failure_row_count": len(failures),
        "same_trace_comparison_row_count": len(comparisons),
        "outcome_changed_vs_m3194_count": sum(_bool(row.get("outcome_changed_vs_m3194")) for row in comparisons),
        "outcome_changed_vs_incumbent_count": sum(_bool(row.get("outcome_changed_vs_incumbent")) for row in comparisons),
        "hard_safety_improved_vs_m3194_count": sum(_bool(row.get("hard_safety_improved_vs_m3194")) for row in comparisons),
        "hard_safety_improved_vs_incumbent_count": sum(_bool(row.get("hard_safety_improved_vs_incumbent")) for row in comparisons),
        "hard_safety_regressed_vs_m3194_count": sum(_bool(row.get("hard_safety_regressed_vs_m3194")) for row in comparisons),
        "hard_safety_regressed_vs_incumbent_count": sum(_bool(row.get("hard_safety_regressed_vs_incumbent")) for row in comparisons),
        "m3205_success_count": sum(_bool(row.get("success", False)) for row in executions),
        "m3205_collision_count": sum(_bool(row.get("collision", False)) for row in executions),
        "m3205_offtrack_count": sum(_offtrack(row) for row in executions),
        "m3194_success_count": sum(_bool(row.get("success", False)) for row in source["m3199_candidate_trace_execution_rows"]),
        "m3194_collision_count": sum(_bool(row.get("collision", False)) for row in source["m3199_candidate_trace_execution_rows"]),
        "m3194_offtrack_count": sum(_offtrack(row) for row in source["m3199_candidate_trace_execution_rows"]),
        "incumbent_success_count": sum(_bool(row.get("success", False)) for row in source["m3189_trace_execution_rows"]),
        "incumbent_collision_count": sum(_bool(row.get("collision", False)) for row in source["m3189_trace_execution_rows"]),
        "incumbent_offtrack_count": sum(_offtrack(row) for row in source["m3189_trace_execution_rows"]),
        "actor_runtime_input_contract": "obs72_only_direct_action3",
        "runtime_driver_id": POLICY_ID,
        "output_semantics": OUTPUT_SEMANTICS,
        "action_components": list(ACTION_COMPONENTS),
        "hidden_actor_inputs_used": hidden_actor_inputs_used,
        "runtime_base_policy_required": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ranking_run": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "robustness_result_claim_made": False,
        "public_driver_default_mutated": False,
        "self_id_claim_made": False,
        "forbidden_runtime_inputs": FORBIDDEN_RUNTIME_INPUTS,
        "claim_scope": CLAIM_SCOPE,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "next_blocker": NEXT_ID,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "scheduled_trace_execution_row_count": len(plan_rows),
            "candidate_trace_execution_row_count": len(executions),
            "candidate_trace_step_row_count": len(steps),
            "same_trace_comparison_row_count": len(comparisons),
            "trace_failure_row_count": len(failures),
            "complete": True,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3204-audit", type=Path, default=DEFAULT_M3204_AUDIT)
    parser.add_argument("--m3203-dir", type=Path, default=DEFAULT_M3203_DIR)
    parser.add_argument("--m3199-dir", type=Path, default=DEFAULT_M3199_DIR)
    parser.add_argument("--m3189-dir", type=Path, default=DEFAULT_M3189_DIR)
    parser.add_argument("--m3187-dir", type=Path, default=DEFAULT_M3187_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_residual_trace_measurement_preflight(
        m3204_audit=args.m3204_audit,
        m3203_dir=args.m3203_dir,
        m3199_dir=args.m3199_dir,
        m3189_dir=args.m3189_dir,
        m3187_dir=args.m3187_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(summary)


if __name__ == "__main__":
    main()
