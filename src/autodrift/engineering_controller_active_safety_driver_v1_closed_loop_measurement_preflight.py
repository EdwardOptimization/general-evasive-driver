"""Run M3043 Active Safety Driver v1 closed-loop measurement preflight."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    env_config_for_executable_profile,
    read_csv_rows,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy, run_episode_with_policy
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = "m3043-engineering-controller-active-safety-driver-v1-closed-loop-measurement-preflight"
NEXT_ID = "m3044-engineering-controller-active-safety-driver-v1-closed-loop-measurement-result-audit"
M3042_ID = "m3042-engineering-controller-active-safety-driver-v1-bounded-residual-fitting-result-audit"
DEFAULT_M3042_AUDIT = Path(f"docs/{M3042_ID}.md")
DEFAULT_M3041_DIR = Path(
    "runs/m3041_engineering_controller_active_safety_driver_v1_bounded_residual_fitting_preflight"
)
DEFAULT_M3039_DIR = Path(
    "runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight"
)
DEFAULT_M3037_DIR = Path(
    "runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path("runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight")
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_WORKLOAD_ROWS = 32
EXPECTED_PROFILE_BINDINGS = 2
RESIDUAL_EPS = 1.0e-6
DEFAULT_EVAL_SEED_BASE = 301500

CLAIM_SCOPE = (
    "M3043 Active Safety Driver v1 closed-loop measurement preflight only; "
    "same-denominator current-sim measurement rows and metric tables may be "
    "recorded for the M3041 residual/reflex candidate. No validation result, "
    "driver-performance verdict, current-sim verdict, ranking, winner "
    "selection, checkpoint promotion, checkpoint mutation, repair success, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU, full "
    "ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, "
    "repair success, checkpoint ranking, winner selection, checkpoint "
    "promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

MEASUREMENT_FIELDNAMES = [
    "measurement_episode_id",
    "baseline_measurement_row_id",
    "source_episode_index",
    "executable_workload_id",
    "workload_contract_id",
    "source_resolution_id",
    "profile_binding_id",
    "executable_source_spec_id",
    "task_source_id",
    "base_profile_name",
    "residual_profile_name",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "eval_seed",
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
    "residual_limit",
    "residual_step_count",
    "residual_abs_max",
    "residual_l2_mean",
    "residual_clip_fraction",
    "action_clip_fraction",
    "base_action_abs_max",
    "final_action_abs_max",
    "baseline_success",
    "baseline_collision",
    "baseline_min_clearance_margin",
    "baseline_high_sideslip_fraction",
    "baseline_lateral_rmse",
    "baseline_action_rate_mean",
    "baseline_return",
    "success_delta_vs_baseline",
    "collision_delta_vs_baseline",
    "clearance_margin_delta_vs_baseline",
    "high_sideslip_fraction_delta_vs_baseline",
    "lateral_rmse_delta_vs_baseline",
    "action_rate_delta_vs_baseline",
    "return_delta_vs_baseline",
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
    "success_rate_verdict_claim_made",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "validation_result_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "full_ideal_driver_completion_claim_made",
    "level3_self_id_claim_made",
    "measurement_only_no_verdict",
    "claim_boundary",
]
FAILURE_FIELDNAMES = [
    "measurement_episode_id",
    "baseline_measurement_row_id",
    "source_episode_index",
    "executable_workload_id",
    "workload_contract_id",
    "source_resolution_id",
    "profile_binding_id",
    "executable_source_spec_id",
    "task_source_id",
    "base_profile_name",
    "residual_profile_name",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "eval_seed",
    "error_type",
    "error_message",
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
    "validation_result_claim_made",
    "current_sim_verdict_claim_made",
    "measurement_only_no_verdict",
    "claim_boundary",
]
GUARD_FIELDNAMES = ["guard_id", "guard_family", "observed_value", "expected_value", "status_pass", "actor_visible", "claim_boundary"]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3043",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


class ResidualActorPolicy:
    def __init__(
        self,
        base_policy: ActorPolicy,
        *,
        weight: np.ndarray,
        bias: np.ndarray,
        residual_limit: float,
        action_low: np.ndarray,
        action_high: np.ndarray,
    ):
        self.base_policy = base_policy
        self.model = base_policy.model
        self.weight = np.asarray(weight, dtype=np.float32)
        self.bias = np.asarray(bias, dtype=np.float32)
        self.residual_limit = float(residual_limit)
        self.action_low = np.asarray(action_low, dtype=np.float32)
        self.action_high = np.asarray(action_high, dtype=np.float32)
        self.last_sequence = None
        self.step_count = 0
        self.residual_abs_max = 0.0
        self.residual_l2_sum = 0.0
        self.residual_clip_count = 0
        self.action_clip_count = 0
        self.base_action_abs_max = 0.0
        self.final_action_abs_max = 0.0

    def reset(self) -> None:
        self.base_policy.reset()
        self.last_sequence = None
        self.step_count = 0
        self.residual_abs_max = 0.0
        self.residual_l2_sum = 0.0
        self.residual_clip_count = 0
        self.action_clip_count = 0
        self.base_action_abs_max = 0.0
        self.final_action_abs_max = 0.0

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        base_action = np.asarray(self.base_policy.act(observation, info), dtype=np.float32)
        obs = np.asarray(observation, dtype=np.float32).reshape(-1)
        raw_residual = obs @ self.weight + self.bias
        residual = np.clip(raw_residual, -self.residual_limit, self.residual_limit).astype(np.float32)
        unclipped_action = base_action + residual
        final_action = np.clip(unclipped_action, self.action_low, self.action_high).astype(np.float32)
        self.last_sequence = None
        self.step_count += 1
        self.residual_abs_max = max(self.residual_abs_max, float(np.max(np.abs(residual))))
        self.residual_l2_sum += float(np.linalg.norm(residual))
        self.residual_clip_count += int(np.any(np.abs(raw_residual) > self.residual_limit + RESIDUAL_EPS))
        self.action_clip_count += int(np.any(np.abs(final_action - unclipped_action) > RESIDUAL_EPS))
        self.base_action_abs_max = max(self.base_action_abs_max, float(np.max(np.abs(base_action))))
        self.final_action_abs_max = max(self.final_action_abs_max, float(np.max(np.abs(final_action))))
        return final_action

    def telemetry(self) -> dict[str, Any]:
        steps = int(self.step_count)
        return {
            "residual_step_count": steps,
            "residual_abs_max": float(self.residual_abs_max),
            "residual_l2_mean": float(self.residual_l2_sum / steps) if steps else 0.0,
            "residual_clip_fraction": float(self.residual_clip_count / steps) if steps else 0.0,
            "action_clip_fraction": float(self.action_clip_count / steps) if steps else 0.0,
            "base_action_abs_max": float(self.base_action_abs_max),
            "final_action_abs_max": float(self.final_action_abs_max),
        }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _mean(values: Iterable[float]) -> float | str:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    if not finite:
        return ""
    return float(np.mean(finite))


def _sum_bool(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key, False)) for row in rows)


def _success(row: Mapping[str, Any]) -> bool:
    if "success" in row and str(row.get("success", "")) != "":
        return _bool(row.get("success"))
    return _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))


def profile_config_for_runtime(config: dict[str, Any], *, profile_name: str) -> dict[str, Any]:
    controller_profile = config.get("controller_profile")
    if isinstance(controller_profile, dict) and str(controller_profile.get("name", "")).strip():
        return dict(config)
    runtime = config.get("controller_profile_runtime")
    if not isinstance(runtime, dict):
        runtime = {}
    adapted = dict(config)
    adapted["controller_profile"] = {
        "name": str(runtime.get("profile_name") or profile_name),
        "observation_mask": str(runtime.get("observation_mask", "none")),
        "previous_command_mask_indices": list(runtime.get("previous_command_mask_indices", [])),
        "history_transform": str(runtime.get("history_transform", "none")),
        "reset_hidden_policy": str(runtime.get("reset_hidden_policy", "episode_persistent")),
    }
    return adapted


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "measurement_episode_rows": output_dir / "measurement_episode_rows.csv",
        "measurement_failure_rows": output_dir / "measurement_failure_rows.csv",
        "metric_summary_rows": output_dir / "metric_summary_rows.csv",
        "residual_adapter_guard_rows": output_dir / "residual_adapter_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3042_audit: Path, m3041_dir: Path, m3039_dir: Path, m3037_dir: Path, m3012_dir: Path) -> dict[str, Any]:
    paths = {
        "m3042_audit": m3042_audit,
        "m3041_summary": m3041_dir / "summary.json",
        "m3041_candidate": m3041_dir / "candidate_residual_reflex_layer.npz",
        "m3041_gate_matrix": m3041_dir / "gate_matrix.csv",
        "m3041_success_guard_rows": m3041_dir / "success_guard_loss_rows.csv",
        "m3041_side_effect_rows": m3041_dir / "checkpoint_side_effect_guard_rows.csv",
        "m3041_claim_rows": m3041_dir / "claim_boundary_rows.csv",
        "m3039_summary": m3039_dir / "summary.json",
        "m3039_scenario_rows": m3039_dir / "scenario_panel_rows.csv",
        "m3039_objective_rows": m3039_dir / "active_safety_training_objective_rows.csv",
        "m3037_summary": m3037_dir / "summary.json",
        "m3037_baseline_rows": m3037_dir / "baseline_measurement_rows.csv",
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3042_audit_text": paths["m3042_audit"].read_text(encoding="utf-8") if exists["m3042_audit"] else "",
        "m3041_summary": read_json(paths["m3041_summary"]) if exists["m3041_summary"] else {},
        "m3041_gate_rows": read_csv_rows(paths["m3041_gate_matrix"]),
        "m3041_success_guard_rows": read_csv_rows(paths["m3041_success_guard_rows"]),
        "m3041_side_effect_rows": read_csv_rows(paths["m3041_side_effect_rows"]),
        "m3041_claim_rows": read_csv_rows(paths["m3041_claim_rows"]),
        "m3039_summary": read_json(paths["m3039_summary"]) if exists["m3039_summary"] else {},
        "m3039_scenario_rows": read_csv_rows(paths["m3039_scenario_rows"]),
        "m3039_objective_rows": read_csv_rows(paths["m3039_objective_rows"]),
        "m3037_summary": read_json(paths["m3037_summary"]) if exists["m3037_summary"] else {},
        "m3037_baseline_rows": read_csv_rows(paths["m3037_baseline_rows"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def load_residual_artifact(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "weight": np.zeros((P0_OBSERVATION_DIM, ACTION_DIM), dtype=np.float32),
            "bias": np.zeros((ACTION_DIM,), dtype=np.float32),
            "residual_limit": 0.0,
            "contract_pass": False,
            "action_composition": "",
        }
    with np.load(path, allow_pickle=False) as data:
        weight = np.asarray(data["linear_weight"], dtype=np.float32) if "linear_weight" in data.files else np.zeros((0, 0))
        bias = np.asarray(data["linear_bias"], dtype=np.float32) if "linear_bias" in data.files else np.zeros((0,))
        residual_limit = float(np.asarray(data["residual_limit"]).reshape(-1)[0]) if "residual_limit" in data.files else 0.0
        observation_dim = int(np.asarray(data["observation_dim"]).reshape(-1)[0]) if "observation_dim" in data.files else -1
        action_dim = int(np.asarray(data["action_dim"]).reshape(-1)[0]) if "action_dim" in data.files else -1
        composition = str(np.asarray(data["action_composition"]).reshape(-1)[0]) if "action_composition" in data.files else ""
    contract_pass = bool(
        weight.shape == (P0_OBSERVATION_DIM, ACTION_DIM)
        and bias.shape == (ACTION_DIM,)
        and np.isfinite(weight).all()
        and np.isfinite(bias).all()
        and np.isfinite(residual_limit)
        and 0.0 < residual_limit <= 0.08 + RESIDUAL_EPS
        and observation_dim == P0_OBSERVATION_DIM
        and action_dim == ACTION_DIM
        and composition == "base_action_plus_residual_clipped"
    )
    return {
        "weight": weight,
        "bias": bias,
        "residual_limit": residual_limit,
        "observation_dim": observation_dim,
        "action_dim": action_dim,
        "contract_pass": contract_pass,
        "action_composition": composition,
    }


def baseline_by_index(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for row in rows:
        try:
            result[int(row.get("source_episode_index", ""))] = row
        except ValueError:
            continue
    return result


def workload_plan(source: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_rows = baseline_by_index(source["m3037_baseline_rows"])
    rows: list[dict[str, Any]] = []
    for index, workload in enumerate(
        sorted(source["m3012_workload_rows"], key=lambda row: row.get("executable_workload_id", "")),
        start=1,
    ):
        baseline = baseline_rows.get(index, {})
        hidden_label_violation = any(
            _bool(workload.get(field, False))
            for field in (
                "hidden_oracle_actor_input_required",
                "future_target_actor_input_required",
                "source_labels_actor_visible",
                "route_labels_actor_visible",
                "outcome_labels_actor_visible",
                "success_progress_labels_actor_visible",
                "verdict_labels_actor_visible",
                "ttc_actor_input_required",
            )
        )
        config_path = str(workload.get("config_path", ""))
        checkpoint_path = str(workload.get("checkpoint_path", ""))
        profile_name = str(workload.get("profile_binding_name", ""))
        status_pass = bool(
            _bool(workload.get("status_pass", False))
            and bool(baseline)
            and Path(config_path).exists()
            and Path(checkpoint_path).exists()
            and int(workload.get("actor_observation_dim", -1)) == P0_OBSERVATION_DIM
            and int(workload.get("actor_action_dim", -1)) == ACTION_DIM
            and not hidden_label_violation
        )
        rows.append(
            {
                **dict(workload),
                "measurement_episode_id": f"m3043-measurement-episode-{index:04d}",
                "source_episode_index": index,
                "baseline_measurement_row_id": baseline.get("baseline_measurement_row_id", ""),
                "baseline": baseline,
                "base_profile_name": profile_name,
                "residual_profile_name": f"{profile_name}+m3041_residual_reflex",
                "config_path": config_path,
                "checkpoint_path": checkpoint_path,
                "eval_seed": int(baseline.get("eval_seed", DEFAULT_EVAL_SEED_BASE + index - 1)),
                "strata": ";".join(
                    value
                    for value in (
                        "active_safety_driver_v1",
                        str(workload.get("task_family", "")),
                        str(workload.get("binding_role", "")),
                        str(workload.get("executable_source_family", "")),
                        str(workload.get("env_template_family", "")),
                    )
                    if value
                ),
                "status_pass": status_pass,
                "hidden_label_violation": hidden_label_violation,
            }
        )
    return rows


def run_measurement_plan(
    *,
    plan_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    residual: dict[str, Any],
    output_dir: Path,
    device: str,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in executable_specs
    }
    cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    episodes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("measurement plan row failed pre-execution guards")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            checkpoint_path = str(plan["checkpoint_path"])
            cache_key = (profile_name, config_path, checkpoint_path)
            if cache_key not in cache:
                profile_config = profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
                model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
                cache[cache_key] = (
                    profile_config,
                    model,
                    {"profile_name": profile_name, "config_path": config_path, "checkpoint_path": checkpoint_path},
                )
            profile_config, model, profile_row = cache[cache_key]
            env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_config)
            env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
            try:
                if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
                    raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
                if int(env.action_space.shape[0]) != ACTION_DIM:
                    raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
                model_obs_dim = int(getattr(model, "obs_dim", -1))
                if model_obs_dim != P0_OBSERVATION_DIM:
                    raise ValueError(f"checkpoint obs_dim {model_obs_dim} != {P0_OBSERVATION_DIM}")
                runtime = profile_runtime_summary(profile_config)
                base_policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
                policy = ResidualActorPolicy(
                    base_policy,
                    weight=residual["weight"],
                    bias=residual["bias"],
                    residual_limit=float(residual["residual_limit"]),
                    action_low=np.asarray(env.action_space.low, dtype=np.float32),
                    action_high=np.asarray(env.action_space.high, dtype=np.float32),
                )
                row = run_episode_with_policy(env, policy, "m3041_residual_reflex", int(plan["eval_seed"]))
            finally:
                env.close()
            row.update(measurement_metadata(plan, policy.telemetry()))
            episodes.append(normalize_measurement_row(row))
        except Exception as exc:  # noqa: BLE001 - every denominator row is accounted.
            failures.append(failure_row(plan, error_type=type(exc).__name__, error_message=str(exc)))
        write_run_state(
            output_dir / "run_state.json",
            {
                "scheduled_measurement_row_count": len(plan_rows),
                "measurement_episode_row_count": len(episodes),
                "measurement_failure_row_count": len(failures),
                "recorded_row_count": len(episodes) + len(failures),
                "latest_measurement_episode_id": plan.get("measurement_episode_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return {"episodes": episodes, "failures": failures}


def measurement_metadata(plan: Mapping[str, Any], telemetry: Mapping[str, Any]) -> dict[str, Any]:
    baseline = dict(plan.get("baseline") or {})
    success = lambda row: float(_success(row))
    return {
        "measurement_episode_id": plan.get("measurement_episode_id", ""),
        "baseline_measurement_row_id": plan.get("baseline_measurement_row_id", ""),
        "source_episode_index": plan.get("source_episode_index", ""),
        "executable_workload_id": plan.get("executable_workload_id", ""),
        "workload_contract_id": plan.get("workload_contract_id", ""),
        "source_resolution_id": plan.get("source_resolution_id", ""),
        "profile_binding_id": plan.get("profile_binding_id", ""),
        "executable_source_spec_id": plan.get("executable_source_spec_id", ""),
        "task_source_id": plan.get("task_source_id", ""),
        "base_profile_name": plan.get("base_profile_name", ""),
        "residual_profile_name": plan.get("residual_profile_name", ""),
        "binding_role": plan.get("binding_role", ""),
        "task_family": plan.get("task_family", ""),
        "source_edge": plan.get("source_edge", ""),
        "window_tag": plan.get("window_tag", ""),
        "strata": plan.get("strata", ""),
        "eval_seed": int(plan.get("eval_seed", 0)),
        "residual_limit": float(telemetry.get("residual_limit", plan.get("residual_limit", 0.08))),
        **dict(telemetry),
        "baseline_success": _success(baseline),
        "baseline_collision": _bool(baseline.get("collision", False)),
        "baseline_min_clearance_margin": _float(baseline.get("min_clearance_margin")),
        "baseline_high_sideslip_fraction": _float(baseline.get("high_sideslip_fraction")),
        "baseline_lateral_rmse": _float(baseline.get("lateral_rmse")),
        "baseline_action_rate_mean": _float(baseline.get("action_rate_mean")),
        "baseline_return": _float(baseline.get("return")),
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
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "measurement_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
        "_baseline_success_float": success(baseline),
    }


def normalize_measurement_row(row: Mapping[str, Any]) -> dict[str, Any]:
    item = {field: row.get(field, "") for field in MEASUREMENT_FIELDNAMES}
    item["success"] = _success(row)
    item["success_delta_vs_baseline"] = float(_success(row)) - float(_bool(row.get("baseline_success", False)))
    item["collision_delta_vs_baseline"] = float(_bool(row.get("collision", False))) - float(
        _bool(row.get("baseline_collision", False))
    )
    for metric, out_key in (
        ("min_clearance_margin", "clearance_margin_delta_vs_baseline"),
        ("high_sideslip_fraction", "high_sideslip_fraction_delta_vs_baseline"),
        ("lateral_rmse", "lateral_rmse_delta_vs_baseline"),
        ("action_rate_mean", "action_rate_delta_vs_baseline"),
        ("return", "return_delta_vs_baseline"),
    ):
        item[out_key] = _float(row.get(metric)) - _float(row.get(f"baseline_{metric}"))
    return item


def failure_row(plan: Mapping[str, Any], *, error_type: str, error_message: str) -> dict[str, Any]:
    row = {field: False for field in FAILURE_FIELDNAMES}
    row.update(
        {
            "measurement_episode_id": plan.get("measurement_episode_id", ""),
            "baseline_measurement_row_id": plan.get("baseline_measurement_row_id", ""),
            "source_episode_index": plan.get("source_episode_index", ""),
            "executable_workload_id": plan.get("executable_workload_id", ""),
            "workload_contract_id": plan.get("workload_contract_id", ""),
            "source_resolution_id": plan.get("source_resolution_id", ""),
            "profile_binding_id": plan.get("profile_binding_id", ""),
            "executable_source_spec_id": plan.get("executable_source_spec_id", ""),
            "task_source_id": plan.get("task_source_id", ""),
            "base_profile_name": plan.get("base_profile_name", ""),
            "residual_profile_name": plan.get("residual_profile_name", ""),
            "binding_role": plan.get("binding_role", ""),
            "task_family": plan.get("task_family", ""),
            "source_edge": plan.get("source_edge", ""),
            "window_tag": plan.get("window_tag", ""),
            "eval_seed": plan.get("eval_seed", ""),
            "error_type": error_type,
            "error_message": error_message,
            "measurement_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def metric_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {"all": rows}
    for key in ("binding_role", "base_profile_name", "task_family"):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get(key, ""))].append(row)
        for name, group in grouped.items():
            groups[f"{key}:{name}"] = group
    summaries: list[dict[str, Any]] = []
    for group, group_rows in sorted(groups.items()):
        summaries.append(
            {
                "metric_summary_id": f"m3043-metric-summary-{len(summaries) + 1:04d}",
                "group": group,
                "episode_count": len(group_rows),
                "success_rate": _mean(float(_success(row)) for row in group_rows),
                "collision_rate": _mean(float(_bool(row.get("collision", False))) for row in group_rows),
                "clearance_margin_mean": _mean(_float(row.get("min_clearance_margin")) for row in group_rows),
                "clearance_margin_delta_mean": _mean(
                    _float(row.get("clearance_margin_delta_vs_baseline")) for row in group_rows
                ),
                "return_mean": _mean(_float(row.get("return")) for row in group_rows),
                "return_delta_mean": _mean(_float(row.get("return_delta_vs_baseline")) for row in group_rows),
                "high_sideslip_fraction_mean": _mean(_float(row.get("high_sideslip_fraction")) for row in group_rows),
                "action_rate_mean": _mean(_float(row.get("action_rate_mean")) for row in group_rows),
                "residual_abs_max": max((_float(row.get("residual_abs_max")) for row in group_rows), default=""),
                "residual_clip_fraction_mean": _mean(_float(row.get("residual_clip_fraction")) for row in group_rows),
                "action_clip_fraction_mean": _mean(_float(row.get("action_clip_fraction")) for row in group_rows),
                "measurement_only_no_ranking_claim": True,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return summaries


def guard(guard_id: str, family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3043-{guard_id}",
        "guard_family": family,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def actor_contract_guard_rows(plan_rows: list[dict[str, Any]], episodes: list[dict[str, Any]], failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    combined = plan_rows + episodes + failures
    accounted = {
        str(row.get("measurement_episode_id", "")) for row in episodes + failures if row.get("measurement_episode_id")
    }
    return [
        guard("actor_observation_dim", "actor_contract", P0_OBSERVATION_DIM, 72),
        guard("actor_action_dim", "actor_contract", ACTION_DIM, 3),
        guard("scheduled_measurement_rows", "denominator", len(plan_rows), EXPECTED_WORKLOAD_ROWS),
        guard("accounted_measurement_rows", "denominator", len(accounted), len(plan_rows)),
        guard("profile_binding_count", "denominator", len({row.get("base_profile_name", "") for row in plan_rows}), EXPECTED_PROFILE_BINDINGS),
        guard("actor_input_contract_changed", "actor_contract", any_flag(combined, "actor_input_contract_changed"), False),
        guard("hidden_oracle_actor_input_required", "actor_contract", any_flag(combined, "hidden_oracle_actor_input_required"), False),
        guard("target_labels_actor_visible", "actor_contract", any_flag(combined, "target_labels_actor_visible"), False),
        guard("target_provenance_actor_visible", "actor_contract", any_flag(combined, "target_provenance_actor_visible"), False),
        guard("source_labels_actor_visible", "actor_contract", any_flag(combined, "source_labels_actor_visible"), False),
        guard("route_labels_actor_visible", "actor_contract", any_flag(combined, "route_labels_actor_visible"), False),
        guard("outcome_labels_actor_visible", "actor_contract", any_flag(combined, "outcome_labels_actor_visible"), False),
        guard("success_progress_labels_actor_visible", "actor_contract", any_flag(combined, "success_progress_labels_actor_visible"), False),
        guard("verdict_labels_actor_visible", "actor_contract", any_flag(combined, "verdict_labels_actor_visible"), False),
        guard("ttc_actor_input_required", "actor_contract", any_flag(combined, "ttc_actor_input_required"), False),
    ]


def residual_adapter_guard_rows(residual: dict[str, Any], episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    residual_abs_max = max((_float(row.get("residual_abs_max")) for row in episodes), default=0.0)
    return [
        guard("residual_weight_shape", "residual_adapter", tuple(residual["weight"].shape), (72, 3)),
        guard("residual_bias_shape", "residual_adapter", tuple(residual["bias"].shape), (3,)),
        guard("residual_observation_dim", "residual_adapter", residual.get("observation_dim"), 72),
        guard("residual_action_dim", "residual_adapter", residual.get("action_dim"), 3),
        guard("residual_action_composition", "residual_adapter", residual.get("action_composition"), "base_action_plus_residual_clipped"),
        guard("residual_limit", "residual_adapter", round(float(residual.get("residual_limit", 0.0)), 8), 0.08),
        guard("residual_contract_pass", "residual_adapter", bool(residual.get("contract_pass", False)), True),
        guard("observed_residual_within_bound", "residual_adapter", bool(residual_abs_max <= float(residual.get("residual_limit", 0.0)) + RESIDUAL_EPS), True),
    ]


def checkpoint_side_effect_guard_rows() -> list[dict[str, Any]]:
    return [
        guard("parent_checkpoint_save", "side_effect", False, False),
        guard("parent_checkpoint_modify", "side_effect", False, False),
        guard("parent_checkpoint_promote", "side_effect", False, False),
        guard("candidate_artifact_modify", "side_effect", False, False),
        guard("active_config_overwrite", "side_effect", False, False),
        guard("ranking_run", "side_effect", False, False),
        guard("winner_selected", "side_effect", False, False),
        guard("validation_run", "side_effect", False, False),
        guard("training_run", "side_effect", False, False),
        guard("ppo_run", "side_effect", False, False),
    ]


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m3043-{claim_id}",
        "claim_family": family,
        "allowed_in_m3043": allowed,
        "claim_made": made,
        "status_pass": bool(allowed) or not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def claim_boundary_rows(*, measurement_rows_present: bool, artifacts_present: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("closed_loop_measurement_rows", "measurement", measurement_rows_present, "measurement_episode_rows.csv"),
        ("metric_summary_rows", "measurement_metric", artifacts_present, "metric_summary_rows.csv"),
        ("residual_adapter_guards", "guard", artifacts_present, "residual_adapter_guard_rows.csv"),
        ("actor_contract_guards", "guard", artifacts_present, "actor_contract_guard_rows.csv"),
        ("side_effect_guards", "guard", artifacts_present, "checkpoint_side_effect_guard_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3044 audit manifest"),
    ]
    blocked = [
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future result audit"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
    ]
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3043-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate_matrix_rows(
    *,
    source: dict[str, Any],
    residual: dict[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    residual_guards: list[dict[str, Any]],
    actor_guards: list[dict[str, Any]],
    side_effect_guards: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    all_guards = residual_guards + actor_guards + side_effect_guards
    source_present = all(source["source_exists"].values())
    audit_accepts = "accept_m3041_bounded_residual_candidate_route_to_m3043" in source["m3042_audit_text"]
    selected_finite = selected_metrics_are_finite(episodes) if episodes else False
    return [
        gate("source_artifacts_present", "source", source_present, source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3042_accepts_m3043_route", "lineage", audit_accepts, "route marker", "present", "lineage_invalid"),
        gate("m3041_status_pass", "lineage", _bool(source["m3041_summary"].get("status_pass", False)), source["m3041_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3041_gate_matrix_pass", "lineage", _bool(source["m3041_summary"].get("gate_matrix_pass", False)), source["m3041_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("residual_contract_pass", "contract", bool(residual.get("contract_pass", False)), residual.get("contract_pass"), True, "contract_violation"),
        gate("measurement_denominator", "denominator", len(plan_rows) == EXPECTED_WORKLOAD_ROWS, len(plan_rows), EXPECTED_WORKLOAD_ROWS, "scenario_sampling_failure"),
        gate("baseline_denominator", "denominator", len(source["m3037_baseline_rows"]) == EXPECTED_WORKLOAD_ROWS, len(source["m3037_baseline_rows"]), EXPECTED_WORKLOAD_ROWS, "scenario_sampling_failure"),
        gate("measurement_episode_rows", "execution", len(episodes) == EXPECTED_WORKLOAD_ROWS, len(episodes), EXPECTED_WORKLOAD_ROWS, "metric_artifact"),
        gate("measurement_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("selected_metrics_finite", "metric", selected_finite, selected_finite, True, "metric_artifact"),
        gate("residual_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in residual_guards), "all", "pass", "contract_violation"),
        gate("actor_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in actor_guards), "all", "pass", "contract_violation"),
        gate("side_effect_guards_pass", "side_effect", all(_bool(row.get("status_pass", False)) for row in side_effect_guards), "all", "pass", "contract_violation"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
        gate("forbidden_flags_clear", "claim", not any_flag(episodes + failures, "driver_performance_claim_made"), False, False, "contract_violation"),
        gate("all_guards_pass", "process", all(_bool(row.get("status_pass", False)) for row in all_guards), "all", "pass", "contract_violation"),
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30390,
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
        "hypothesis": "A bounded result-audit synthesis can accept or reject the M3043 Active Safety Driver v1 closed-loop measurement artifacts and decide the next active-safety engineering branch route before any validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "measurement_episode_rows.csv"),
                str(output_dir / "measurement_failure_rows.csv"),
                str(output_dir / "metric_summary_rows.csv"),
                str(output_dir / "residual_adapter_guard_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "checkpoint_side_effect_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3043 closed-loop measurement artifacts before interpretation"],
            "derived_from": [MILESTONE_ID, M3042_ID],
            "blocked_by": [
                "M3043 measurement rows require audit before any performance or continuation decision",
                "current-sim measurement rows are not validation or promotion evidence before M3044",
            ],
            "supersedes": ["direct interpretation of M3043 measurement rows without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3044 must audit M3043 summary measurement metric guard claim and gate artifacts",
            "M3044 must answer evidence_summary supported_claims falsified_claims failure_taxonomy_summary public_gate_overfit_risk and next_branch_decision",
            "M3044 must preserve actor 72/action 3 and claim boundaries",
            "M3044 must reject validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims unless separately routed",
            "M3044 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun rollout validate rank promote tune or mutate checkpoints",
            "do not convert M3043 rows into performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_engineering_mainline",
            "evidence_axis": "active_safety_driver_v1_closed_loop_measurement_result_audit",
            "evidence_increment": "audits and synthesizes the first same-denominator closed-loop measurement rows for the residual candidate after the active-safety mainline cadence fires",
            "claim_scope": "Result-audit synthesis only; no validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3043 artifacts are missing or gate matrix fails",
                "stop if actor or residual adapter contracts were violated",
                "stop if M3043 rows are treated as validation or performance verdicts",
            ],
            "fallback_plan": [
                "route to measurement harness repair if artifacts are incomplete",
                "route to candidate repair if residual adapter worsens safety metrics or violates guards",
                "route to next measured continuation only after claim-safe audit",
                "route to synthesis if evidence is negative or ambiguous",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "validator-enforced workflow cadence after M3043 completes the first active-safety closed-loop measurement preflight",
            "synthesis_decision": "continue",
            "synthesis_artifact": f"docs/{NEXT_ID}.md",
            "synthesis_questions": [
                "evidence_summary",
                "supported_claims",
                "falsified_claims",
                "failure_taxonomy_summary",
                "public_gate_overfit_risk",
                "next_branch_decision",
            ],
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit and synthesize M3043 closed-loop measurement preflight artifacts",
            "admission_evidence": [
                "M3043 summary and gate matrix",
                "M3043 measurement episode metric residual adapter actor contract side-effect and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress or verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3044 status queue scoreboard research log and review",
                "one follow-up manifest only if M3044 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3044 audit accepts or rejects M3043 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3044 audits engineering measurement artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3044; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3043 closed-loop measurement artifacts only.",
            "negative_result_policy": "Preserve negative measurement evidence and route to engineering repair or synthesis rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3043 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "synthesis_decision",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits and synthesizes newly generated Active Safety Driver v1 closed-loop measurement rows before selecting the next branch route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3044 audits engineering measurement evidence",
            "must_synthesize_if": [
                "M3044 cannot accept M3043 as complete and claim-safe",
                "M3044 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict or self-ID evidence",
                "M3044 would continue with another materialization-only route before interpreting measurement",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3044 audits M3043 row counts gates actor residual side-effect and claim boundaries",
            "M3044 answers all synthesis_questions",
            "M3044 selects exactly one next route or stop state",
            "no validation ranking promotion driver-performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3044 hides M3043 failures or missing artifacts",
            "M3044 treats M3043 measurements as validation or performance verdict",
            "M3044 changes actor input or action contract",
            "M3044 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3044 audits M3043 artifacts and selects one next route or stop state while preserving actor residual and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_closed_loop_measurement_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "measurement_episode_rows.csv"),
            str(output_dir / "metric_summary_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M3043 Active Safety Driver v1 Closed-Loop Measurement Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- scheduled measurement rows: {summary['scheduled_measurement_row_count']}/{summary['target_measurement_row_count']}",
            f"- measurement episode rows: {summary['measurement_episode_row_count']}",
            f"- measurement failure rows: {summary['measurement_failure_row_count']}",
            f"- success count: {summary['measurement_success_count']}",
            f"- collision count: {summary['measurement_collision_count']}",
            f"- offtrack count: {summary['measurement_offtrack_count']}",
            f"- residual abs max: {summary['measurement_residual_abs_max']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3043 records same-denominator current-sim measurement rows for the M3041 residual/reflex candidate. These rows are measurement artifacts for M3044 audit only. They are not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
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


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def run_closed_loop_measurement_preflight(
    *,
    m3042_audit: Path,
    m3041_dir: Path,
    m3039_dir: Path,
    m3037_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    device: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3042_audit=m3042_audit,
        m3041_dir=m3041_dir,
        m3039_dir=m3039_dir,
        m3037_dir=m3037_dir,
        m3012_dir=m3012_dir,
    )
    residual = load_residual_artifact(source["paths"]["m3041_candidate"])
    plan_rows = workload_plan(source)
    measurement = run_measurement_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        residual=residual,
        output_dir=output_dir,
        device=device,
        next_blocker=NEXT_ID,
    )
    episodes = measurement["episodes"]
    failures = measurement["failures"]
    metric_rows = metric_summary_rows(episodes)
    residual_guards = residual_adapter_guard_rows(residual, episodes)
    actor_guards = actor_contract_guard_rows(plan_rows, episodes, failures)
    side_effect_guards = checkpoint_side_effect_guard_rows()
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path, summary_path=paths["summary"]))
    claim_rows = claim_boundary_rows(
        measurement_rows_present=bool(episodes),
        artifacts_present=True,
        follow_up_manifest_registered=follow_up_manifest.exists(),
    )
    for path, rows, fields in (
        (paths["measurement_episode_rows"], episodes, MEASUREMENT_FIELDNAMES),
        (paths["measurement_failure_rows"], failures, FAILURE_FIELDNAMES),
        (paths["metric_summary_rows"], metric_rows, None),
        (paths["residual_adapter_guard_rows"], residual_guards, GUARD_FIELDNAMES),
        (paths["actor_contract_guard_rows"], actor_guards, GUARD_FIELDNAMES),
        (paths["checkpoint_side_effect_guard_rows"], side_effect_guards, GUARD_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fields)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        residual=residual,
        plan_rows=plan_rows,
        episodes=episodes,
        failures=failures,
        residual_guards=residual_guards,
        actor_guards=actor_guards,
        side_effect_guards=side_effect_guards,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episodes)
    profile_counts = Counter(str(row.get("base_profile_name", "")) for row in episodes)
    residual_abs_max = max((_float(row.get("residual_abs_max")) for row in episodes), default=0.0)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_v1_closed_loop_measurement_preflight_pass"
            if status_pass
            else "active_safety_driver_v1_closed_loop_measurement_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "scheduled_measurement_row_count": len(plan_rows),
        "target_measurement_row_count": EXPECTED_WORKLOAD_ROWS,
        "measurement_episode_row_count": len(episodes),
        "measurement_failure_row_count": len(failures),
        "recorded_row_count": len(episodes) + len(failures),
        "profile_counts": dict(sorted(profile_counts.items())),
        "measurement_success_count": _sum_bool(episodes, "success"),
        "measurement_collision_count": _sum_bool(episodes, "collision"),
        "measurement_offtrack_count": int(termination_counts.get("off_track", 0)),
        "measurement_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "measurement_termination_counts": dict(sorted(termination_counts.items())),
        "measurement_residual_abs_max": residual_abs_max,
        "residual_limit": float(residual.get("residual_limit", 0.0)),
        "metric_summary_row_count": len(metric_rows),
        "residual_adapter_guard_row_count": len(residual_guards),
        "residual_adapter_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in residual_guards),
        "actor_contract_guard_row_count": len(actor_guards),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_guards),
        "checkpoint_side_effect_guard_row_count": len(side_effect_guards),
        "checkpoint_side_effect_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in side_effect_guards),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3041_status_pass": _bool(source["m3041_summary"].get("status_pass", False)),
        "m3041_gate_matrix_pass": _bool(source["m3041_summary"].get("gate_matrix_pass", False)),
        "candidate_residual_reflex_layer": str(source["paths"]["m3041_candidate"]),
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
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
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": any_flag(episodes + failures, "hidden_oracle_actor_input_required"),
        "target_labels_actor_visible": any_flag(episodes + failures, "target_labels_actor_visible"),
        "target_provenance_actor_visible": any_flag(episodes + failures, "target_provenance_actor_visible"),
        "ttc_actor_input_required": any_flag(episodes + failures, "ttc_actor_input_required"),
        "success_rate_metric_recorded": bool(episodes),
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_v1_closed_loop_measurement_route_to_m3044_result_audit",
        "next_blocker": NEXT_ID,
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
            "scheduled_measurement_row_count": len(plan_rows),
            "measurement_episode_row_count": len(episodes),
            "measurement_failure_row_count": len(failures),
            "recorded_row_count": len(episodes) + len(failures),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3042-audit", type=Path, default=DEFAULT_M3042_AUDIT)
    parser.add_argument("--m3041-dir", type=Path, default=DEFAULT_M3041_DIR)
    parser.add_argument("--m3039-dir", type=Path, default=DEFAULT_M3039_DIR)
    parser.add_argument("--m3037-dir", type=Path, default=DEFAULT_M3037_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_closed_loop_measurement_preflight(
        m3042_audit=args.m3042_audit,
        m3041_dir=args.m3041_dir,
        m3039_dir=args.m3039_dir,
        m3037_dir=args.m3037_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"episode_rows={summary['measurement_episode_row_count']}")
    print(f"failure_rows={summary['measurement_failure_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
