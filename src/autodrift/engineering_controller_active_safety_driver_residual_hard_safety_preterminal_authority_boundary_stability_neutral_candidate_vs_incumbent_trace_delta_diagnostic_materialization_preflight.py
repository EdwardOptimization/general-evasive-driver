"""Materialize M3199 candidate-vs-incumbent residual trace-delta diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.controller_profile_runtime import wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_blocker_axis_trace_execution_materialization_preflight as m3189
from autodrift.engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_candidate_implementation_materialization_preflight import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
    POLICY_CONFIG,
    POLICY_ID,
    preterminal_authority_boundary_stability_candidate_action,
)
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight as m3075
from autodrift.controller_family_full_rollout_execution import env_config_for_executable_profile


MILESTONE_ID = (
    "m3199-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-neutral-candidate-vs-incumbent-"
    "trace-delta-diagnostic-materialization-preflight"
)
NEXT_ID = (
    "m3200-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-neutral-candidate-vs-incumbent-"
    "trace-delta-diagnostic-result-audit"
)
M3198_ID = (
    "m3198-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-neutral-result-synthesis"
)
M3194_ID = (
    "m3194-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-candidate-implementation-materialization-preflight"
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

DEFAULT_M3198_SYNTHESIS = Path(f"docs/{M3198_ID}.md")
DEFAULT_M3194_DIR = Path(
    "runs/m3194_engineering_controller_active_safety_driver_residual_hard_safety_"
    "preterminal_authority_boundary_stability_candidate_implementation_materialization_preflight"
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
    "runs/m3199_engineering_controller_active_safety_driver_residual_hard_safety_"
    "preterminal_authority_boundary_stability_neutral_candidate_vs_incumbent_"
    "trace_delta_diagnostic_materialization_preflight"
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
CLAIM_SCOPE = (
    "M3199 Active Safety Driver residual hard-safety preterminal authority and "
    "boundary-stability neutral candidate-vs-incumbent trace-delta diagnostic "
    "materialization only; the seven accepted residual blocker trace bindings may "
    "be executed through the M3194 deterministic obs72-to-action3 candidate and "
    "compared offline against M3189 incumbent trace-step telemetry. Artifacts may "
    "include candidate trace rows, trace-step rows, trace-delta rows, summary rows, "
    "guards, claims, gates, doc, and M3200 audit manifest. No repair implementation, "
    "validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "public driver default mutation, driver-performance verdict, current-sim verdict, "
    "repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, "
    "high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU "
    "conclusion, full ideal driver completion, or level3 self-identification"
)
FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)

CANDIDATE_TRACE_EXECUTION_FIELDNAMES = [
    *m3189.TRACE_EXECUTION_FIELDNAMES,
    "incumbent_trace_execution_id",
]
CANDIDATE_TRACE_STEP_FIELDNAMES = [
    *m3189.TRACE_STEP_FIELDNAMES,
    "incumbent_trace_execution_id",
]
TRACE_DELTA_FIELDNAMES = [
    "trace_delta_id",
    "candidate_trace_execution_id",
    "incumbent_trace_execution_id",
    "trace_source_binding_id",
    "step_index",
    "evidence_axis",
    "fresh_panel_row_id",
    "source_measurement_episode_id",
    "blocker_family",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "candidate_step_present",
    "incumbent_step_present",
    "obs72_sha256_match",
    "candidate_steer",
    "incumbent_steer",
    "steer_delta",
    "candidate_throttle",
    "incumbent_throttle",
    "throttle_delta",
    "candidate_brake",
    "incumbent_brake",
    "brake_delta",
    "action_delta_l2",
    "abs_steer_delta",
    "abs_throttle_delta",
    "abs_brake_delta",
    "candidate_clip_hit",
    "incumbent_clip_hit",
    "clip_delta",
    "candidate_terminal_window",
    "incumbent_terminal_window",
    "terminal_window_step",
    "delta_timing_bucket",
    "steer_delta_sign",
    "throttle_delta_sign",
    "brake_delta_sign",
    "candidate_post_speed",
    "incumbent_post_speed",
    "post_speed_delta",
    "candidate_relative_clearance_proxy",
    "incumbent_relative_clearance_proxy",
    "relative_clearance_delta",
    "candidate_post_lateral_error",
    "incumbent_post_lateral_error",
    "lateral_error_delta",
    "candidate_terminated",
    "incumbent_terminated",
    "candidate_termination_reason",
    "incumbent_termination_reason",
    "validation_run",
    "repair_success_claim_made",
    "claim_boundary",
]
TRACE_DELTA_SUMMARY_FIELDNAMES = [
    "trace_delta_summary_id",
    "trace_source_binding_id",
    "candidate_trace_execution_id",
    "incumbent_trace_execution_id",
    "evidence_axis",
    "blocker_family",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "candidate_steps",
    "incumbent_steps",
    "aligned_step_count",
    "obs_hash_match_count",
    "meaningful_delta_step_count",
    "preterminal_delta_step_count",
    "terminal_window_delta_step_count",
    "max_action_delta_l2",
    "mean_action_delta_l2",
    "terminal_window_mean_delta_l2",
    "final_delta_l2",
    "candidate_success",
    "incumbent_success",
    "candidate_collision",
    "incumbent_collision",
    "candidate_offtrack",
    "incumbent_offtrack",
    "candidate_termination_reason",
    "incumbent_termination_reason",
    "outcome_changed",
    "candidate_min_clearance_margin",
    "incumbent_min_clearance_margin",
    "clearance_margin_delta",
    "diagnostic_classification",
    "claim_boundary",
]
GUARD_FIELDNAMES = m3189.GUARD_FIELDNAMES
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3199",
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


def _sign(value: float) -> str:
    if value > DELTA_EPS:
        return "positive"
    if value < -DELTA_EPS:
        return "negative"
    return "zero"


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "candidate_trace_execution_rows": output_dir / "candidate_trace_execution_rows.csv",
        "candidate_trace_step_rows": output_dir / "candidate_trace_step_rows.csv",
        "trace_failure_rows": output_dir / "trace_failure_rows.csv",
        "trace_delta_rows": output_dir / "trace_delta_rows.csv",
        "trace_delta_summary_rows": output_dir / "trace_delta_summary_rows.csv",
        "contract_guard_rows": output_dir / "contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3198_synthesis: Path,
    m3194_dir: Path,
    m3189_dir: Path,
    m3187_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3198_synthesis": m3198_synthesis,
        "m3194_summary": m3194_dir / "summary.json",
        "m3194_gate_rows": m3194_dir / "gate_matrix.csv",
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
        "m3198_synthesis_text": paths["m3198_synthesis"].read_text(encoding="utf-8") if exists["m3198_synthesis"] else "",
        "m3194_summary": read_json(paths["m3194_summary"]) if exists["m3194_summary"] else {},
        "m3194_gate_rows": read_csv_rows(paths["m3194_gate_rows"]),
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
    rows = sorted(
        (dict(row) for row in source["m3189_trace_execution_rows"]),
        key=lambda row: str(row.get("trace_execution_id", "")),
    )
    plan: list[dict[str, Any]] = []
    for index, incumbent in enumerate(rows, start=1):
        binding = bindings.get(str(incumbent.get("trace_source_binding_id", "")), {})
        workload = workloads.get(str(incumbent.get("executable_workload_id", "")), {})
        config_path = str(workload.get("config_path", ""))
        eval_seed = _int(incumbent.get("eval_seed"), 0)
        hidden_label_violation = _hidden_label_violation(binding, incumbent, workload)
        status_pass = bool(
            _bool(source["m3194_summary"].get("status_pass", False))
            and _bool(source["m3189_summary"].get("status_pass", False))
            and _bool(incumbent.get("scheduled_status_pass", False))
            and _bool(workload.get("status_pass", False))
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
                "trace_execution_id": f"m3199-candidate-trace-execution-{index:04d}",
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


class M3199CandidateTraceDriver:
    def act(self, observation: np.ndarray) -> np.ndarray:
        return preterminal_authority_boundary_stability_candidate_action(observation, POLICY_CONFIG)


def failure_row(plan: Mapping[str, Any], *, error_type: str, error_message: str) -> dict[str, Any]:
    row = m3189.failure_row(plan, error_type=error_type, error_message=error_message)
    row.update(
        {
            "trace_failure_id": f"m3199-trace-failure-{plan.get('trace_execution_id', '')}",
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
    driver = M3199CandidateTraceDriver()
    executions: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("M3199 trace execution plan row failed pre-execution guards")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            cache_key = (profile_name, config_path)
            if cache_key not in profile_cache:
                profile_cache[cache_key] = m3075.profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
            # Preserve M3189's public rollout accounting while replacing the action source.
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


def _step_key(row: Mapping[str, Any]) -> tuple[str, int]:
    return str(row.get("trace_source_binding_id", "")), _int(row.get("step_index"), 0)


def trace_delta_rows(
    *,
    candidate_steps: list[dict[str, Any]],
    incumbent_steps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cand_by_key = {_step_key(row): dict(row) for row in candidate_steps}
    inc_by_key = {_step_key(row): dict(row) for row in incumbent_steps}
    candidate_counts = Counter(str(row.get("trace_source_binding_id", "")) for row in candidate_steps)
    incumbent_counts = Counter(str(row.get("trace_source_binding_id", "")) for row in incumbent_steps)
    keys = sorted(set(cand_by_key) | set(inc_by_key), key=lambda item: (item[0], item[1]))
    rows: list[dict[str, Any]] = []
    for key in keys:
        source_binding_id, step_index = key
        candidate = cand_by_key.get(key, {})
        incumbent = inc_by_key.get(key, {})
        context = candidate or incumbent
        candidate_present = bool(candidate)
        incumbent_present = bool(incumbent)
        c_action = np.asarray(
            [
                _float(candidate.get("final_steer")),
                _float(candidate.get("final_throttle")),
                _float(candidate.get("final_brake")),
            ],
            dtype=np.float32,
        )
        i_action = np.asarray(
            [
                _float(incumbent.get("final_steer")),
                _float(incumbent.get("final_throttle")),
                _float(incumbent.get("final_brake")),
            ],
            dtype=np.float32,
        )
        delta = c_action - i_action
        delta_l2 = float(np.linalg.norm(delta)) if candidate_present and incumbent_present else 0.0
        candidate_terminal = bool(candidate_present and step_index >= max(candidate_counts[source_binding_id] - 5, 0))
        incumbent_terminal = bool(incumbent_present and step_index >= max(incumbent_counts[source_binding_id] - 5, 0))
        terminal_window = candidate_terminal or incumbent_terminal
        meaningful = candidate_present and incumbent_present and delta_l2 > DELTA_EPS
        if not candidate_present:
            timing = "missing_candidate"
        elif not incumbent_present:
            timing = "candidate_extra"
        elif not meaningful:
            timing = "none"
        elif terminal_window:
            timing = "terminal_window"
        else:
            timing = "preterminal"
        rows.append(
            {
                "trace_delta_id": f"m3199-trace-delta-{len(rows) + 1:04d}",
                "candidate_trace_execution_id": candidate.get("trace_execution_id", ""),
                "incumbent_trace_execution_id": incumbent.get("trace_execution_id", candidate.get("incumbent_trace_execution_id", "")),
                "trace_source_binding_id": source_binding_id,
                "step_index": step_index,
                "evidence_axis": context.get("evidence_axis", ""),
                "fresh_panel_row_id": context.get("fresh_panel_row_id", ""),
                "source_measurement_episode_id": context.get("source_measurement_episode_id", ""),
                "blocker_family": context.get("blocker_family", ""),
                "axis_id": context.get("axis_id", ""),
                "binding_role": context.get("binding_role", ""),
                "task_family": context.get("task_family", ""),
                "eval_seed": context.get("eval_seed", ""),
                "candidate_step_present": candidate_present,
                "incumbent_step_present": incumbent_present,
                "obs72_sha256_match": bool(
                    candidate_present
                    and incumbent_present
                    and str(candidate.get("obs72_sha256", "")) == str(incumbent.get("obs72_sha256", ""))
                ),
                "candidate_steer": float(c_action[0]) if candidate_present else "",
                "incumbent_steer": float(i_action[0]) if incumbent_present else "",
                "steer_delta": float(delta[0]) if candidate_present and incumbent_present else "",
                "candidate_throttle": float(c_action[1]) if candidate_present else "",
                "incumbent_throttle": float(i_action[1]) if incumbent_present else "",
                "throttle_delta": float(delta[1]) if candidate_present and incumbent_present else "",
                "candidate_brake": float(c_action[2]) if candidate_present else "",
                "incumbent_brake": float(i_action[2]) if incumbent_present else "",
                "brake_delta": float(delta[2]) if candidate_present and incumbent_present else "",
                "action_delta_l2": delta_l2,
                "abs_steer_delta": float(abs(delta[0])) if candidate_present and incumbent_present else "",
                "abs_throttle_delta": float(abs(delta[1])) if candidate_present and incumbent_present else "",
                "abs_brake_delta": float(abs(delta[2])) if candidate_present and incumbent_present else "",
                "candidate_clip_hit": _bool(candidate.get("action_clip_hit", False)),
                "incumbent_clip_hit": _bool(incumbent.get("action_clip_hit", False)),
                "clip_delta": int(_bool(candidate.get("action_clip_hit", False))) - int(_bool(incumbent.get("action_clip_hit", False))),
                "candidate_terminal_window": candidate_terminal,
                "incumbent_terminal_window": incumbent_terminal,
                "terminal_window_step": terminal_window,
                "delta_timing_bucket": timing,
                "steer_delta_sign": _sign(float(delta[0])) if candidate_present and incumbent_present else "missing",
                "throttle_delta_sign": _sign(float(delta[1])) if candidate_present and incumbent_present else "missing",
                "brake_delta_sign": _sign(float(delta[2])) if candidate_present and incumbent_present else "missing",
                "candidate_post_speed": _float(candidate.get("post_speed")) if candidate_present else "",
                "incumbent_post_speed": _float(incumbent.get("post_speed")) if incumbent_present else "",
                "post_speed_delta": _float(candidate.get("post_speed")) - _float(incumbent.get("post_speed")) if candidate_present and incumbent_present else "",
                "candidate_relative_clearance_proxy": _float(candidate.get("relative_clearance_proxy")) if candidate_present else "",
                "incumbent_relative_clearance_proxy": _float(incumbent.get("relative_clearance_proxy")) if incumbent_present else "",
                "relative_clearance_delta": _float(candidate.get("relative_clearance_proxy")) - _float(incumbent.get("relative_clearance_proxy")) if candidate_present and incumbent_present else "",
                "candidate_post_lateral_error": _float(candidate.get("post_lateral_error")) if candidate_present else "",
                "incumbent_post_lateral_error": _float(incumbent.get("post_lateral_error")) if incumbent_present else "",
                "lateral_error_delta": _float(candidate.get("post_lateral_error")) - _float(incumbent.get("post_lateral_error")) if candidate_present and incumbent_present else "",
                "candidate_terminated": _bool(candidate.get("terminated", False)),
                "incumbent_terminated": _bool(incumbent.get("terminated", False)),
                "candidate_termination_reason": candidate.get("termination_reason", ""),
                "incumbent_termination_reason": incumbent.get("termination_reason", ""),
                "validation_run": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def trace_delta_summary_rows(
    *,
    candidate_executions: list[dict[str, Any]],
    incumbent_executions: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidate_by_binding = {str(row.get("trace_source_binding_id", "")): dict(row) for row in candidate_executions}
    incumbent_by_binding = {str(row.get("trace_source_binding_id", "")): dict(row) for row in incumbent_executions}
    rows: list[dict[str, Any]] = []
    for binding_id in sorted(set(candidate_by_binding) | set(incumbent_by_binding)):
        candidate = candidate_by_binding.get(binding_id, {})
        incumbent = incumbent_by_binding.get(binding_id, {})
        subset = [row for row in deltas if str(row.get("trace_source_binding_id", "")) == binding_id]
        aligned = [row for row in subset if _bool(row.get("candidate_step_present")) and _bool(row.get("incumbent_step_present"))]
        meaningful = [row for row in aligned if _float(row.get("action_delta_l2")) > DELTA_EPS]
        preterminal = [row for row in meaningful if str(row.get("delta_timing_bucket")) == "preterminal"]
        terminal = [row for row in meaningful if _bool(row.get("terminal_window_step"))]
        terminal_all = [row for row in aligned if _bool(row.get("terminal_window_step"))]
        outcome_changed = (
            _bool(candidate.get("collision", False)) != _bool(incumbent.get("collision", False))
            or _offtrack(candidate) != _offtrack(incumbent)
            or _bool(candidate.get("success", False)) != _bool(incumbent.get("success", False))
        )
        if not meaningful:
            classification = "no_meaningful_action_delta"
        elif not preterminal and terminal:
            classification = "terminal_only_action_delta"
        elif outcome_changed:
            classification = "action_delta_with_outcome_change"
        else:
            classification = "preterminal_action_delta_outcome_neutral"
        rows.append(
            {
                "trace_delta_summary_id": f"m3199-trace-delta-summary-{len(rows) + 1:04d}",
                "trace_source_binding_id": binding_id,
                "candidate_trace_execution_id": candidate.get("trace_execution_id", ""),
                "incumbent_trace_execution_id": incumbent.get("trace_execution_id", ""),
                "evidence_axis": (candidate or incumbent).get("evidence_axis", ""),
                "blocker_family": (candidate or incumbent).get("blocker_family", ""),
                "axis_id": (candidate or incumbent).get("axis_id", ""),
                "binding_role": (candidate or incumbent).get("binding_role", ""),
                "task_family": (candidate or incumbent).get("task_family", ""),
                "eval_seed": (candidate or incumbent).get("eval_seed", ""),
                "candidate_steps": _int(candidate.get("steps")),
                "incumbent_steps": _int(incumbent.get("steps")),
                "aligned_step_count": len(aligned),
                "obs_hash_match_count": sum(_bool(row.get("obs72_sha256_match")) for row in aligned),
                "meaningful_delta_step_count": len(meaningful),
                "preterminal_delta_step_count": len(preterminal),
                "terminal_window_delta_step_count": len(terminal),
                "max_action_delta_l2": max((_float(row.get("action_delta_l2")) for row in aligned), default=0.0),
                "mean_action_delta_l2": _mean(_float(row.get("action_delta_l2")) for row in aligned),
                "terminal_window_mean_delta_l2": _mean(_float(row.get("action_delta_l2")) for row in terminal_all),
                "final_delta_l2": _float(aligned[-1].get("action_delta_l2")) if aligned else 0.0,
                "candidate_success": _bool(candidate.get("success", False)),
                "incumbent_success": _bool(incumbent.get("success", False)),
                "candidate_collision": _bool(candidate.get("collision", False)),
                "incumbent_collision": _bool(incumbent.get("collision", False)),
                "candidate_offtrack": _offtrack(candidate),
                "incumbent_offtrack": _offtrack(incumbent),
                "candidate_termination_reason": candidate.get("termination_reason", ""),
                "incumbent_termination_reason": incumbent.get("termination_reason", ""),
                "outcome_changed": outcome_changed,
                "candidate_min_clearance_margin": _float(candidate.get("min_clearance_margin")),
                "incumbent_min_clearance_margin": _float(incumbent.get("min_clearance_margin")),
                "clearance_margin_delta": _float(candidate.get("min_clearance_margin")) - _float(incumbent.get("min_clearance_margin")),
                "diagnostic_classification": classification,
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
    item["guard_id"] = str(item["guard_id"]).replace("m3189-", "m3199-", 1)
    item["claim_boundary"] = CLAIM_SCOPE
    return item


def contract_guard_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sample_action = preterminal_authority_boundary_stability_candidate_action(
        np.zeros(P0_OBSERVATION_DIM, dtype=np.float32),
        POLICY_CONFIG,
    )
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
    return [
        guard("source_artifacts_present", "source", all(source["source_exists"].values()), True),
        guard("trace_binding_plan_rows", "source", len(plan_rows), EXPECTED_TRACE_BINDINGS),
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
        guard("delta_rows_present", "diagnostic", len(deltas) > 0, True),
        guard("trace_failures", "execution", len(failures), 0),
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("candidate_trace_execution_rows", "trace_execution_artifact", True, True, "candidate_trace_execution_rows.csv"),
        ("candidate_trace_step_rows", "trace_execution_artifact", True, True, "candidate_trace_step_rows.csv"),
        ("trace_delta_rows", "diagnostic_artifact", True, True, "trace_delta_rows.csv"),
        ("trace_delta_summary_rows", "diagnostic_artifact", True, True, "trace_delta_summary_rows.csv"),
        ("contract_guard_rows", "contract", True, True, "contract_guard_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("repair_implementation", "forbidden", False, False, "later implementation admission after audit and synthesis"),
        ("validation_result", "forbidden", False, False, "separate validation execution route"),
        ("driver_performance_verdict", "forbidden", False, False, "future proof generalization and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "future audited result synthesis"),
        ("repair_success", "forbidden", False, False, "accepted measurement improvement plus validation route"),
        ("ranking_or_winner_selection", "forbidden", False, False, "future audited ranking route"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("public_driver_default_mutation", "forbidden", False, False, "future admitted implementation route"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3199"),
    ]
    return [
        {
            "claim_id": f"m3199-{claim_id}",
            "claim_family": family,
            "allowed_in_m3199": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3199-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _m3198_selects_m3199(text: str) -> bool:
    return (
        "m3199-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-neutral-candidate-vs-incumbent-trace-delta-diagnostic-materialization-preflight"
        in text
        or "candidate-vs-incumbent residual trace-delta diagnostic" in text
    )


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    delta_summaries: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    binding_ids = {str(row.get("trace_source_binding_id", "")) for row in plan_rows}
    executed_binding_ids = {str(row.get("trace_source_binding_id", "")) for row in executions}
    delta_summary_binding_ids = {str(row.get("trace_source_binding_id", "")) for row in delta_summaries}
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
        for row in executions + steps + failures + deltas
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
        gate("m3198_selects_m3199_route", "lineage", _m3198_selects_m3199(source["m3198_synthesis_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3194_status_pass", "lineage", _bool(source["m3194_summary"].get("status_pass")), source["m3194_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3189_status_pass", "lineage", _bool(source["m3189_summary"].get("status_pass")), source["m3189_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("scheduled_trace_bindings", "execution", len(plan_rows) == EXPECTED_TRACE_BINDINGS, len(plan_rows), EXPECTED_TRACE_BINDINGS, "scenario_sampling_failure"),
        gate("candidate_trace_execution_rows", "execution", len(executions) == EXPECTED_TRACE_BINDINGS, len(executions), EXPECTED_TRACE_BINDINGS, "metric_artifact"),
        gate("candidate_trace_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("candidate_trace_step_rows", "execution", len(steps) > 0, len(steps), ">0", "metric_artifact"),
        gate("binding_ids_preserved", "execution", binding_ids == executed_binding_ids, sorted(executed_binding_ids), sorted(binding_ids), "metric_artifact"),
        gate("trace_axes_present", "evidence", EXPECTED_TRACE_AXES.issubset(set(axis_counts)), dict(axis_counts), sorted(EXPECTED_TRACE_AXES), "metric_artifact"),
        gate("trace_delta_rows", "diagnostic", len(deltas) > 0, len(deltas), ">0", "metric_artifact"),
        gate("trace_delta_summary_rows", "diagnostic", delta_summary_binding_ids == binding_ids, sorted(delta_summary_binding_ids), sorted(binding_ids), "metric_artifact"),
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
        "priority": 32000,
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
        "hypothesis": "A bounded result audit can accept or reject M3199 candidate-vs-incumbent trace-delta diagnostic artifacts before any implementation admission validation or stop.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "candidate_trace_execution_rows.csv"),
                str(output_dir / "candidate_trace_step_rows.csv"),
                str(output_dir / "trace_delta_rows.csv"),
                str(output_dir / "trace_delta_summary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3199 candidate-vs-incumbent residual trace-delta diagnostics"],
            "derived_from": [MILESTONE_ID, M3198_ID, M3194_ID, M3189_ID, M3187_ID, M3012_ID],
            "blocked_by": [
                "M3199 diagnostics require audit before implementation admission",
                "M3199 trace deltas are diagnostic only and not validation or repair success",
            ],
            "supersedes": ["unreviewed candidate-vs-incumbent trace-delta interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3200 must audit M3199 candidate trace rows step rows delta rows guards claims and gates",
            "M3200 must preserve obs72-only actor runtime and direct [steer throttle brake] action contract",
            "M3200 must reject implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3200 must select implementation-admission artifact-repair synthesis or stop as exactly one route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun tune rank promote or mutate checkpoints in M3200",
            "do not convert M3199 trace deltas into validation repair-success performance current-sim robustness-result high-fidelity paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_candidate_vs_incumbent_trace_delta_diagnostic",
            "evidence_axis": "candidate_vs_incumbent_residual_trace_delta_result_audit",
            "evidence_increment": "audits step-level candidate-vs-incumbent residual trace-delta artifacts",
            "claim_scope": "Result audit only; no implementation validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3199 artifacts are missing or gate matrix fails",
                "stop if any trace execution used hidden runtime labels",
                "synthesize if trace deltas do not identify an implementation-admissible actor-visible failure mode",
            ],
            "fallback_plan": [
                "route to M3199 artifact repair if rows or guards fail",
                "route to synthesis if candidate deltas are absent or terminal-only",
                "preserve M3105/M3103 incumbent until later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3199 materializes candidate-vs-incumbent residual trace-delta artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3199 trace-delta diagnostic artifacts",
            "admission_evidence": [
                "M3199 summary candidate trace rows step rows trace delta rows contract guards claim rows and gate matrix"
            ],
            "blocked_shortcuts": [
                "no repair implementation validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or public driver mutation",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3200 status queue scoreboard research log and review",
                "one follow-up manifest only if M3200 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3200 accepts or rejects M3199 as complete and claim-safe",
                "next implementation-admission synthesis artifact-repair or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3200 audits engineering trace-delta artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3200; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3199 trace-delta artifacts only.",
            "negative_result_policy": "Preserve engineering trace-delta evidence and route implementation admission synthesis or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3199 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 1,
            "evidence_expansion": "audits trace-delta diagnostics before implementation admission or synthesis",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3200 audits engineering trace-delta evidence",
            "must_synthesize_if": [
                "M3200 cannot select implementation-admission synthesis artifact-repair or stop",
                "M3200 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3200 audits M3199 row counts gates actor contract and claim boundaries",
            "M3200 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3200 hides missing M3199 artifacts or failed gates",
            "M3200 treats M3199 traces as repair success or performance verdict",
            "M3200 changes actor input action contract or public driver default",
            "M3200 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3200 audits M3199 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_neutral_candidate_vs_incumbent_trace_delta_diagnostic_result_audit_doc",
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
            "# M3199 Candidate-vs-Incumbent Residual Trace-Delta Diagnostic Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- scheduled trace bindings: {summary['scheduled_trace_execution_row_count']}",
            f"- candidate trace execution rows: {summary['candidate_trace_execution_row_count']}",
            f"- candidate trace step rows: {summary['candidate_trace_step_row_count']}",
            f"- trace delta rows: {summary['trace_delta_row_count']}",
            f"- trace delta summary rows: {summary['trace_delta_summary_row_count']}",
            f"- meaningful delta steps: {summary['meaningful_delta_step_count']}",
            f"- preterminal delta steps: {summary['preterminal_delta_step_count']}",
            f"- terminal-window delta steps: {summary['terminal_window_delta_step_count']}",
            f"- outcome-changed traces: {summary['outcome_changed_trace_count']}",
            f"- hidden actor inputs used: {summary['hidden_actor_inputs_used']}",
            f"- validation run: {summary['validation_run']}",
            f"- repair implementation admitted: {summary['repair_implementation_admitted']}",
            f"- public driver default mutated: {summary['public_driver_default_mutated']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3199 executes the seven residual blocker trace bindings through the M3194 candidate and compares step-level public action telemetry against the M3189 incumbent traces. This is diagnostic trace-delta evidence only, not validation, repair success, ranking, promotion, or a deployable-driver verdict.",
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


def run_trace_delta_diagnostic_materialization_preflight(
    *,
    m3198_synthesis: Path,
    m3194_dir: Path,
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
        m3198_synthesis=m3198_synthesis,
        m3194_dir=m3194_dir,
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
    deltas = trace_delta_rows(candidate_steps=steps, incumbent_steps=source["m3189_trace_step_rows"])
    delta_summaries = trace_delta_summary_rows(
        candidate_executions=executions,
        incumbent_executions=source["m3189_trace_execution_rows"],
        deltas=deltas,
    )
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    guards = contract_guard_rows(
        source=source,
        plan_rows=plan_rows,
        executions=executions,
        steps=steps,
        failures=failures,
        deltas=deltas,
    )
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["candidate_trace_execution_rows"], executions, fieldnames=CANDIDATE_TRACE_EXECUTION_FIELDNAMES)
    write_csv_rows(paths["candidate_trace_step_rows"], steps, fieldnames=CANDIDATE_TRACE_STEP_FIELDNAMES)
    write_csv_rows(paths["trace_failure_rows"], failures, fieldnames=m3189.TRACE_FAILURE_FIELDNAMES)
    write_csv_rows(paths["trace_delta_rows"], deltas, fieldnames=TRACE_DELTA_FIELDNAMES)
    write_csv_rows(paths["trace_delta_summary_rows"], delta_summaries, fieldnames=TRACE_DELTA_SUMMARY_FIELDNAMES)
    write_csv_rows(paths["contract_guard_rows"], guards, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        executions=executions,
        steps=steps,
        failures=failures,
        deltas=deltas,
        delta_summaries=delta_summaries,
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
    meaningful_count = sum(_float(row.get("action_delta_l2")) > DELTA_EPS for row in deltas)
    preterminal_count = sum(str(row.get("delta_timing_bucket")) == "preterminal" for row in deltas)
    terminal_count = sum(
        _float(row.get("action_delta_l2")) > DELTA_EPS and _bool(row.get("terminal_window_step"))
        for row in deltas
    )
    status_pass = bool(gate_matrix_pass and len(executions) == EXPECTED_TRACE_BINDINGS and len(failures) == 0)
    summary = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": utc_timestamp(),
        "result_class": "trace_delta_diagnostic_materialized" if status_pass else "trace_delta_diagnostic_incomplete",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "source_artifacts_present": all(source["source_exists"].values()),
        "scheduled_trace_execution_row_count": len(plan_rows),
        "candidate_trace_execution_row_count": len(executions),
        "candidate_trace_step_row_count": len(steps),
        "trace_failure_row_count": len(failures),
        "trace_delta_row_count": len(deltas),
        "trace_delta_summary_row_count": len(delta_summaries),
        "meaningful_delta_step_count": meaningful_count,
        "preterminal_delta_step_count": preterminal_count,
        "terminal_window_delta_step_count": terminal_count,
        "outcome_changed_trace_count": sum(_bool(row.get("outcome_changed")) for row in delta_summaries),
        "candidate_success_count": sum(_bool(row.get("success", False)) for row in executions),
        "candidate_collision_count": sum(_bool(row.get("collision", False)) for row in executions),
        "candidate_offtrack_count": sum(_offtrack(row) for row in executions),
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
        "repair_implementation_admitted": False,
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
            "trace_delta_row_count": len(deltas),
            "trace_failure_row_count": len(failures),
            "complete": True,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3198-synthesis", type=Path, default=DEFAULT_M3198_SYNTHESIS)
    parser.add_argument("--m3194-dir", type=Path, default=DEFAULT_M3194_DIR)
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
    summary = run_trace_delta_diagnostic_materialization_preflight(
        m3198_synthesis=args.m3198_synthesis,
        m3194_dir=args.m3194_dir,
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
