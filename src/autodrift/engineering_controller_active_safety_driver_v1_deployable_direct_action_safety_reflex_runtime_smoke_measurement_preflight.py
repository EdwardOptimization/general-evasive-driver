"""Run M3088 deployable safety-reflex runtime-smoke measurement preflight."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.active_safety_reflex_driver import ACTION_COMPONENTS, DRIVER_ID, OUTPUT_SEMANTICS, ActiveSafetyReflexDriver
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    env_config_for_executable_profile,
    read_csv_rows,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.controller_profile_runtime import wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import run_episode_with_policy
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight as m3075


MILESTONE_ID = (
    "m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-smoke-measurement-preflight"
)
NEXT_ID = (
    "m3089-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-smoke-measurement-result-audit"
)
M3087_ID = (
    "m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-contract-materialization-result-audit"
)
M3086_ID = (
    "m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-contract-materialization-preflight"
)
M3084_ID = (
    "m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-fresh-robustness-measurement-preflight"
)

DEFAULT_M3087_AUDIT = Path(f"docs/{M3087_ID}.md")
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
    "runs/m3088_engineering_controller_active_safety_driver_v1_deployable_direct_action_"
    "safety_reflex_runtime_smoke_measurement_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_SMOKE_ROWS = 8
EXPECTED_AXIS_COUNT = 4
EXPECTED_BINDING_ROLE_COUNT = 2
CLAIM_SCOPE = (
    "M3088 Active Safety Driver v1 deployable direct-action safety-reflex runtime-smoke "
    "measurement preflight only; a small pre-registered current-sim smoke panel may be "
    "executed through ActiveSafetyReflexDriver.act as the full obs72-to-action3 action "
    "source and measurement, contract, claim, gate, doc, and M3089 audit artifacts may be "
    "written. No validation, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, driver-performance verdict, current-sim verdict, repair success, "
    "robustness-result, high-fidelity validation, paper evidence, finite-window-vs-GRU "
    "evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, "
    "high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU "
    "conclusion, full ideal driver completion, or level3 self-identification"
)

CONTEXT_FIELDNAMES = [
    "runtime_smoke_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "axis_family",
    "scenario_family",
    "fresh_scenario_distribution",
    "binding_role",
    "task_family",
    "executable_workload_id",
    "executable_source_spec_id",
    "task_source_id",
    "base_profile_name",
    "eval_seed",
]
EPISODE_FIELDNAMES = [
    *CONTEXT_FIELDNAMES,
    "policy",
    "steps",
    "terminated",
    "truncated",
    "success",
    "collision",
    "obstacle_completed",
    "termination_reason",
    "outcome_bucket",
    "min_obstacle_clearance",
    "obstacle_collision_radius",
    "min_clearance_margin",
    "high_sideslip_fraction",
    "beta_abs_error_mean",
    "lateral_rmse",
    "action_rate_mean",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "off_track_severity_proxy",
    "recoverability_window_success_available",
    "recoverability_window_success",
    "return",
    "speed_mean",
    "candidate_output_semantics",
    "runtime_driver_id",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "direct_action_step_count",
    "raw_action_abs_max",
    "raw_action_l2_mean",
    "action_clip_fraction",
    "final_action_abs_max",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_mutated",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "robustness_result_claim_made",
    "validation_result_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "full_ideal_driver_completion_claim_made",
    "level3_self_id_claim_made",
    "runtime_smoke_only_no_verdict",
    "claim_boundary",
]
FAILURE_FIELDNAMES = [
    *CONTEXT_FIELDNAMES,
    "error_type",
    "error_message",
    "runtime_driver_id",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "validation_run",
    "ranking_run",
    "driver_performance_claim_made",
    "runtime_smoke_only_no_verdict",
    "claim_boundary",
]
METRIC_FIELDNAMES = [
    "metric_summary_id",
    "group",
    "episode_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
    "speed_too_low_rate",
    "clearance_margin_mean",
    "return_mean",
    "high_sideslip_fraction_mean",
    "lateral_rmse_mean",
    "action_rate_mean",
    "raw_action_abs_max",
    "raw_action_l2_mean",
    "action_clip_fraction_mean",
    "final_action_abs_max",
    "runtime_base_policy_required",
    "driver_performance_claim_made",
    "claim_boundary",
]
GUARD_FIELDNAMES = ["guard_id", "guard_family", "observed_value", "expected_value", "status_pass", "actor_visible", "claim_boundary"]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3088",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _mean(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else ""


def _success(row: Mapping[str, Any]) -> bool:
    return bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


class DeployableRuntimeSmokePolicy:
    """Policy adapter that calls the packaged deployable driver API."""

    def __init__(self, driver: ActiveSafetyReflexDriver):
        self.driver = driver
        self.last_sequence = None
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0
        self.final_action_abs_max = 0.0

    def reset(self) -> None:
        self.last_sequence = None
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0
        self.final_action_abs_max = 0.0

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        del info
        action = self.driver.act(observation)
        self.last_sequence = None
        self.step_count += 1
        self.raw_action_abs_max = max(self.raw_action_abs_max, float(np.max(np.abs(action))))
        self.raw_action_l2_sum += float(np.linalg.norm(action))
        self.final_action_abs_max = max(self.final_action_abs_max, float(np.max(np.abs(action))))
        return action

    def telemetry(self) -> dict[str, Any]:
        steps = int(self.step_count)
        return {
            "runtime_driver_id": DRIVER_ID,
            "candidate_output_semantics": OUTPUT_SEMANTICS,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
            "direct_action_step_count": steps,
            "raw_action_abs_max": float(self.raw_action_abs_max),
            "raw_action_l2_mean": float(self.raw_action_l2_sum / steps) if steps else 0.0,
            "action_clip_fraction": 0.0,
            "final_action_abs_max": float(self.final_action_abs_max),
        }


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "runtime_smoke_episode_rows": output_dir / "runtime_smoke_episode_rows.csv",
        "runtime_smoke_failure_rows": output_dir / "runtime_smoke_failure_rows.csv",
        "runtime_smoke_metric_summary_rows": output_dir / "runtime_smoke_metric_summary_rows.csv",
        "runtime_smoke_contract_guard_rows": output_dir / "runtime_smoke_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3087_audit: Path, m3086_dir: Path, m3084_dir: Path, m3012_dir: Path) -> dict[str, Any]:
    paths = {
        "m3087_audit": m3087_audit,
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
        "m3087_audit_text": paths["m3087_audit"].read_text(encoding="utf-8") if exists["m3087_audit"] else "",
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


def smoke_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in sorted(source["m3084_measurement_rows"], key=lambda item: item.get("measurement_episode_id", "")):
        grouped[(str(row.get("axis_id", "")), str(row.get("binding_role", "")))].append(row)
    workloads = {str(row.get("executable_workload_id", "")): row for row in source["m3012_workload_rows"]}
    plan: list[dict[str, Any]] = []
    for axis_id, binding_role in sorted(grouped):
        source_row = grouped[(axis_id, binding_role)][0]
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
                "runtime_smoke_episode_id": f"m3088-runtime-smoke-episode-{len(plan) + 1:04d}",
                "source_measurement_episode_id": source_row.get("measurement_episode_id", ""),
                "config_path": config_path,
                "base_profile_name": workload.get("profile_binding_name", source_row.get("base_profile_name", "")),
                "eval_seed": eval_seed,
                "hidden_label_violation": hidden_label_violation,
                "status_pass": status_pass,
            }
        )
    return plan


def context_fields(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {field: plan.get(field, "") for field in CONTEXT_FIELDNAMES}


def normalize_episode_row(plan: Mapping[str, Any], row: Mapping[str, Any], telemetry: Mapping[str, Any]) -> dict[str, Any]:
    item = {field: "" for field in EPISODE_FIELDNAMES}
    item.update(context_fields(plan))
    item.update({field: row.get(field, "") for field in EPISODE_FIELDNAMES if field in row})
    item.update(dict(telemetry))
    item.update(
        {
            "success": _success(row),
            "environment_reset_run": True,
            "environment_step_run": True,
            "policy_action_run": True,
            "policy_rollout_run": True,
            "validation_run": False,
            "training_run": False,
            "replay_run": False,
            "ppo_run": False,
            "ranking_run": False,
            "winner_selected": False,
            "checkpoint_mutated": False,
            "checkpoint_promoted": False,
            "actor_input_contract_changed": False,
            "hidden_oracle_actor_input_required": False,
            "target_labels_actor_visible": False,
            "target_provenance_actor_visible": False,
            "source_labels_actor_visible": False,
            "route_labels_actor_visible": False,
            "outcome_labels_actor_visible": False,
            "success_progress_labels_actor_visible": False,
            "verdict_labels_actor_visible": False,
            "ttc_actor_input_required": False,
            "driver_performance_claim_made": False,
            "repair_success_claim_made": False,
            "robustness_result_claim_made": False,
            "validation_result_claim_made": False,
            "paper_claim_made": False,
            "finite_window_vs_gru_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "high_fidelity_validation_claim_made": False,
            "full_ideal_driver_completion_claim_made": False,
            "level3_self_id_claim_made": False,
            "runtime_smoke_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return item


def failure_row(plan: Mapping[str, Any], *, error_type: str, error_message: str) -> dict[str, Any]:
    row = {field: "" for field in FAILURE_FIELDNAMES}
    row.update(context_fields(plan))
    row.update(
        {
            "error_type": error_type,
            "error_message": error_message,
            "runtime_driver_id": DRIVER_ID,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "validation_run": False,
            "ranking_run": False,
            "driver_performance_claim_made": False,
            "runtime_smoke_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def run_smoke_plan(
    *,
    plan_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    contract: Mapping[str, Any],
    output_dir: Path,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    del contract
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in executable_specs
    }
    profile_cache: dict[tuple[str, str], dict[str, Any]] = {}
    driver = ActiveSafetyReflexDriver()
    episodes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("runtime-smoke plan row failed pre-execution guards")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            cache_key = (profile_name, config_path)
            if cache_key not in profile_cache:
                profile_cache[cache_key] = m3075.profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
            profile_config = profile_cache[cache_key]
            env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_config)
            env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
            policy = DeployableRuntimeSmokePolicy(driver)
            try:
                if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
                    raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
                if int(env.action_space.shape[0]) != ACTION_DIM:
                    raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
                row = run_episode_with_policy(env, policy, "active_safety_reflex_driver_v1_runtime_smoke", int(plan["eval_seed"]))
            finally:
                env.close()
            episodes.append(normalize_episode_row(plan, row, policy.telemetry()))
        except Exception as exc:  # noqa: BLE001 - every scheduled row must be accounted.
            failures.append(failure_row(plan, error_type=type(exc).__name__, error_message=str(exc)))
        write_run_state(
            output_dir / "run_state.json",
            {
                "scheduled_runtime_smoke_row_count": len(plan_rows),
                "runtime_smoke_episode_row_count": len(episodes),
                "runtime_smoke_failure_row_count": len(failures),
                "recorded_row_count": len(episodes) + len(failures),
                "latest_runtime_smoke_episode_id": plan.get("runtime_smoke_episode_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return {"episodes": episodes, "failures": failures}


def metric_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {"all": rows}
    for key in ("axis_id", "binding_role", "task_family"):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(key, ""))].append(row)
        for name, group_rows in grouped.items():
            groups[f"{key}:{name}"] = group_rows
    summaries: list[dict[str, Any]] = []
    for group, group_rows in sorted(groups.items()):
        summaries.append(
            {
                "metric_summary_id": f"m3088-metric-summary-{len(summaries) + 1:04d}",
                "group": group,
                "episode_count": len(group_rows),
                "success_rate": _mean(float(_bool(row.get("success", False))) for row in group_rows),
                "collision_rate": _mean(float(_bool(row.get("collision", False))) for row in group_rows),
                "offtrack_rate": _mean(float(str(row.get("termination_reason", "")) == "off_track") for row in group_rows),
                "speed_too_low_rate": _mean(float(str(row.get("termination_reason", "")) == "speed_too_low") for row in group_rows),
                "clearance_margin_mean": _mean(_float(row.get("min_clearance_margin")) for row in group_rows),
                "return_mean": _mean(_float(row.get("return")) for row in group_rows),
                "high_sideslip_fraction_mean": _mean(_float(row.get("high_sideslip_fraction")) for row in group_rows),
                "lateral_rmse_mean": _mean(_float(row.get("lateral_rmse")) for row in group_rows),
                "action_rate_mean": _mean(_float(row.get("action_rate_mean")) for row in group_rows),
                "raw_action_abs_max": max((_float(row.get("raw_action_abs_max")) for row in group_rows), default=""),
                "raw_action_l2_mean": _mean(_float(row.get("raw_action_l2_mean")) for row in group_rows),
                "action_clip_fraction_mean": _mean(_float(row.get("action_clip_fraction")) for row in group_rows),
                "final_action_abs_max": max((_float(row.get("final_action_abs_max")) for row in group_rows), default=""),
                "runtime_base_policy_required": any_flag(group_rows, "runtime_base_policy_required"),
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return summaries


def guard(guard_id: str, family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3088-{guard_id}",
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
        guard("scheduled_smoke_rows", "smoke_denominator", len(plan_rows), EXPECTED_SMOKE_ROWS),
        guard("accounted_smoke_rows", "smoke_denominator", len(episodes) + len(failures), len(plan_rows)),
        guard("axis_count", "smoke_denominator", len({row.get("axis_id", "") for row in plan_rows}), EXPECTED_AXIS_COUNT),
        guard("binding_role_count", "smoke_denominator", len({row.get("binding_role", "") for row in plan_rows}), EXPECTED_BINDING_ROLE_COUNT),
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
        ("runtime_smoke_rows", "measurement", True, "runtime_smoke_episode_rows.csv"),
        ("metric_summary_rows", "measurement_metric", True, "runtime_smoke_metric_summary_rows.csv"),
        ("contract_guards", "guard", True, "runtime_smoke_contract_guard_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3089 audit manifest"),
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
            "claim_id": f"m3088-{claim_id}",
            "claim_family": family,
            "allowed_in_m3088": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3088-{claim_id}",
            "claim_family": family,
            "allowed_in_m3088": False,
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
        "priority": 30840,
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
        "hypothesis": "A bounded result audit can accept or reject the M3088 deployable runtime-smoke measurement artifacts before any broader runtime measurement, validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, repair-success, robustness-result, or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), "runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight/deployable_driver_contract.json"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "runtime_smoke_episode_rows.csv"),
                str(output_dir / "runtime_smoke_failure_rows.csv"),
                str(output_dir / "runtime_smoke_metric_summary_rows.csv"),
                str(output_dir / "runtime_smoke_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit deployable runtime-smoke measurement before broader runtime verification"],
            "derived_from": [MILESTONE_ID, M3087_ID, M3086_ID, M3084_ID],
            "blocked_by": [
                "M3088 runtime-smoke rows require audit before broader runtime measurement",
                "runtime-smoke rows are not validation or promotion evidence before M3089",
            ],
            "supersedes": ["direct interpretation of runtime-smoke rows without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3089 must audit M3088 summary smoke metric guard claim and gate artifacts",
            "M3089 must preserve obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3089 must reject validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3089 must select exactly one broader runtime measurement repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun expand tune rank promote validate or mutate checkpoints",
            "do not convert M3088 smoke rows into driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_deployable_direct_action_reflex",
            "evidence_axis": "deployable_runtime_smoke_measurement_result_audit",
            "evidence_increment": "audits runtime-smoke closed-loop rows from the packaged deployable safety-reflex driver",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3088 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize if M3089 cannot select a broader runtime measurement repair or stop route",
            ],
            "fallback_plan": [
                "route to runtime package repair if artifacts are incomplete",
                "route to broader runtime measurement if M3088 is complete and claim-safe",
                "route to branch synthesis or stop if runtime smoke fails deployment boundary",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3088 completes deployable runtime-smoke measurement preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3088 deployable runtime-smoke measurement artifacts",
            "admission_evidence": ["M3088 summary and gate matrix", "M3088 smoke episode metric contract and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3089 status queue scoreboard research log and review",
                "one follow-up manifest only if M3089 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3089 accepts or rejects M3088 as complete and claim-safe",
                "next broader runtime measurement, repair, synthesis, or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3089 audits engineering runtime-smoke artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3089; finite-window and GRU comparison remains a later same-case engineering ablation."],
            "temporal_evidence_window": "M3088 deployable runtime-smoke measurement artifacts only.",
            "negative_result_policy": "Preserve negative runtime-smoke evidence and route to engineering repair, synthesis, or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3088 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits first environment-loop smoke evidence through the deployable runtime API",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3089 audits engineering runtime smoke evidence",
            "must_synthesize_if": [
                "M3089 cannot accept M3088 as complete and claim-safe",
                "M3089 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result or self-ID evidence",
                "M3089 cannot select a broader runtime measurement repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3089 audits M3088 row counts gates actor contract and claim boundaries",
            "M3089 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3089 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3089 hides M3088 failures or missing artifacts",
            "M3089 treats M3088 runtime-smoke as validation or performance verdict",
            "M3089 changes actor input or action contract",
            "M3089 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3089 audits M3088 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_runtime_smoke_measurement_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3088-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    contract: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    audit_accepts = "accept_m3086_runtime_contract_route_to_m3088_runtime_smoke_measurement_preflight" in str(
        source.get("m3087_audit_text", "")
    )
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3087_accepts_m3088_route", "lineage", audit_accepts, "route marker", "present", "lineage_invalid"),
        gate("m3086_status_pass", "lineage", _bool(source["m3086_summary"].get("status_pass", False)), source["m3086_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3086_gate_matrix_pass", "lineage", _bool(source["m3086_summary"].get("gate_matrix_pass", False)), source["m3086_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3086_interface_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_interface_rows", [])), len(source.get("m3086_interface_rows", [])), "all pass", "lineage_invalid"),
        gate("m3086_action_probe_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_probe_rows", [])), len(source.get("m3086_probe_rows", [])), "all pass", "lineage_invalid"),
        gate("m3086_actor_input_exclusion_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_exclusion_rows", [])), len(source.get("m3086_exclusion_rows", [])), "all pass", "lineage_invalid"),
        gate("m3086_claim_boundary_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3086_claim_rows", [])), len(source.get("m3086_claim_rows", [])), "all pass", "lineage_invalid"),
        gate("m3084_status_pass", "lineage", _bool(source["m3084_summary"].get("status_pass", False)), source["m3084_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("contract_observation_shape", "contract", int(contract.get("observation_shape", -1)) == P0_OBSERVATION_DIM, contract.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("contract_action_shape", "contract", int(contract.get("action_shape", -1)) == ACTION_DIM, contract.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("contract_output_semantics", "contract", str(contract.get("output_semantics", "")) == OUTPUT_SEMANTICS, contract.get("output_semantics"), OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(contract.get("runtime_base_policy_required", True)), contract.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("smoke_denominator", "smoke", len(plan_rows) == EXPECTED_SMOKE_ROWS, len(plan_rows), EXPECTED_SMOKE_ROWS, "scenario_sampling_failure"),
        gate("smoke_plan_rows_pass", "smoke", all(_bool(row.get("status_pass", False)) for row in plan_rows), "all", "pass", "scenario_sampling_failure"),
        gate("smoke_accounted_rows", "execution", len(episodes) + len(failures) == len(plan_rows), len(episodes) + len(failures), len(plan_rows), "metric_artifact"),
        gate("smoke_episode_rows", "execution", len(episodes) == EXPECTED_SMOKE_ROWS, len(episodes), EXPECTED_SMOKE_ROWS, "metric_artifact"),
        gate("smoke_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("selected_metrics_finite", "metric", selected_metrics_are_finite(episodes) if episodes else False, "finite" if episodes else "none", "finite", "metric_artifact"),
        gate("metric_summary_rows", "metric", bool(metric_rows), len(metric_rows), "nonempty", "metric_artifact"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in guard_rows), "all", "pass", "contract_violation"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3088 Active Safety Driver v1 Deployable Runtime-Smoke Measurement Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- scheduled smoke rows: {summary['scheduled_runtime_smoke_row_count']}/{summary['target_runtime_smoke_row_count']}",
            f"- runtime-smoke episode rows: {summary['runtime_smoke_episode_row_count']}",
            f"- runtime-smoke failure rows: {summary['runtime_smoke_failure_row_count']}",
            f"- success count: {summary['runtime_smoke_success_count']}",
            f"- collision count: {summary['runtime_smoke_collision_count']}",
            f"- offtrack count: {summary['runtime_smoke_offtrack_count']}",
            f"- speed-too-low count: {summary['runtime_smoke_speed_too_low_count']}",
            f"- clearance margin mean: {summary['runtime_smoke_clearance_margin_mean']}",
            f"- action clip fraction mean: {summary['runtime_smoke_action_clip_fraction_mean']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3088 records bounded runtime-smoke current-sim rows through the packaged ActiveSafetyReflexDriver API. These rows are integration smoke artifacts for M3089 audit only. They are not validation, ranking, promotion, repair-success, robustness-result, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
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


def run_runtime_smoke_measurement_preflight(
    *,
    m3087_audit: Path,
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
    source = load_sources(m3087_audit=m3087_audit, m3086_dir=m3086_dir, m3084_dir=m3084_dir, m3012_dir=m3012_dir)
    contract = source["m3086_contract"]
    plan_rows = smoke_plan(source)
    measurement = run_smoke_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        contract=contract,
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    episodes = measurement["episodes"]
    failures = measurement["failures"]
    metric_rows = metric_summary_rows(episodes)
    guard_rows = contract_guard_rows(source=source, contract=contract, plan_rows=plan_rows, episodes=episodes, failures=failures)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["runtime_smoke_episode_rows"], episodes, EPISODE_FIELDNAMES),
        (paths["runtime_smoke_failure_rows"], failures, FAILURE_FIELDNAMES),
        (paths["runtime_smoke_metric_summary_rows"], metric_rows, METRIC_FIELDNAMES),
        (paths["runtime_smoke_contract_guard_rows"], guard_rows, GUARD_FIELDNAMES),
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
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episodes)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight_pass"
            if status_pass
            else "active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "runtime_driver_id": DRIVER_ID,
        "scheduled_runtime_smoke_row_count": len(plan_rows),
        "target_runtime_smoke_row_count": EXPECTED_SMOKE_ROWS,
        "runtime_smoke_episode_row_count": len(episodes),
        "runtime_smoke_failure_row_count": len(failures),
        "recorded_row_count": len(episodes) + len(failures),
        "runtime_smoke_success_count": sum(1 for row in episodes if _bool(row.get("success", False))),
        "runtime_smoke_collision_count": sum(1 for row in episodes if _bool(row.get("collision", False))),
        "runtime_smoke_offtrack_count": int(termination_counts.get("off_track", 0)),
        "runtime_smoke_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "runtime_smoke_termination_counts": dict(sorted(termination_counts.items())),
        "runtime_smoke_clearance_margin_mean": _mean(_float(row.get("min_clearance_margin")) for row in episodes),
        "runtime_smoke_high_sideslip_fraction_mean": _mean(_float(row.get("high_sideslip_fraction")) for row in episodes),
        "runtime_smoke_lateral_rmse_mean": _mean(_float(row.get("lateral_rmse")) for row in episodes),
        "runtime_smoke_action_clip_fraction_mean": _mean(_float(row.get("action_clip_fraction")) for row in episodes),
        "runtime_smoke_raw_action_abs_max": max((_float(row.get("raw_action_abs_max")) for row in episodes), default=0.0),
        "runtime_smoke_final_action_abs_max": max((_float(row.get("final_action_abs_max")) for row in episodes), default=0.0),
        "metric_summary_row_count": len(metric_rows),
        "contract_guard_row_count": len(guard_rows),
        "contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
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
        "decision": "active_safety_driver_v1_runtime_smoke_measurement_route_to_m3089_result_audit",
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
    write_json(
        paths["run_state"],
        {
            "scheduled_runtime_smoke_row_count": len(plan_rows),
            "runtime_smoke_episode_row_count": len(episodes),
            "runtime_smoke_failure_row_count": len(failures),
            "recorded_row_count": len(episodes) + len(failures),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3087-audit", type=Path, default=DEFAULT_M3087_AUDIT)
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
    summary = run_runtime_smoke_measurement_preflight(
        m3087_audit=args.m3087_audit,
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
    print(f"runtime_smoke_rows={summary['runtime_smoke_episode_row_count']}")
    print(f"runtime_smoke_failures={summary['runtime_smoke_failure_row_count']}")
    print(f"success_count={summary['runtime_smoke_success_count']}")
    print(f"collision_count={summary['runtime_smoke_collision_count']}")
    print(f"offtrack_count={summary['runtime_smoke_offtrack_count']}")
    print(f"speed_too_low_count={summary['runtime_smoke_speed_too_low_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
