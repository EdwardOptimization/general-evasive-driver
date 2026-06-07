"""Run M3080 deterministic direct-action safety-reflex measurement preflight."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    env_config_for_executable_profile,
    read_csv_rows,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.controller_profile_runtime import wrap_env_with_profile_mask
from autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight import (
    actor_visible_safety_reflex_action,
)
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import run_episode_with_policy
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight as m3075


MILESTONE_ID = (
    "m3080-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-closed-loop-measurement-preflight"
)
NEXT_ID = (
    "m3081-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-closed-loop-measurement-result-audit"
)
M3079_ID = (
    "m3079-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-materialization-result-audit"
)

DEFAULT_M3079_AUDIT = Path(f"docs/{M3079_ID}.md")
DEFAULT_M3078_DIR = Path(
    "runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_materialization_preflight"
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
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3080_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_closed_loop_measurement_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_WORKLOAD_ROWS = 32
EXPECTED_PROFILE_BINDINGS = 2
DIRECT_ACTION_SEMANTICS = "direct_action_clipped"
DIRECT_ACTION_COMPONENTS = ("steer", "throttle", "brake")

MEASUREMENT_FIELDNAMES = m3075.MEASUREMENT_FIELDNAMES
FAILURE_FIELDNAMES = m3075.FAILURE_FIELDNAMES
GUARD_FIELDNAMES = m3075.GUARD_FIELDNAMES
GATE_FIELDNAMES = m3075.GATE_FIELDNAMES
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3080",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]

CLAIM_SCOPE = (
    "M3080 Active Safety Driver v1 actor-visible deterministic direct-action safety-reflex "
    "closed-loop measurement preflight only; same-denominator current-sim measurement rows "
    "and metric tables may be recorded for the M3078 deterministic direct-action safety-reflex "
    "candidate. The candidate is executed as final_action = actor_visible_safety_reflex_action(obs72). "
    "No runtime base policy, hidden oracle, TTC, target, provenance, source, route, outcome, "
    "progress, or verdict actor input is used. No validation result, driver-performance verdict, "
    "current-sim verdict, ranking, winner selection, checkpoint promotion, checkpoint mutation, "
    "repair success, high-fidelity validation, paper evidence, finite-window-vs-GRU, full ideal "
    "driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, repair success, "
    "checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation "
    "readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver "
    "completion, or level3 self-identification"
)


def _bool(value: Any) -> bool:
    return m3075._bool(value)


def _float(value: Any) -> float:
    return m3075._float(value)


def _mean(values: Iterable[float]) -> float | str:
    return m3075._mean(values)


def _success(row: Mapping[str, Any]) -> bool:
    return m3075._success(row)


def _sum_bool(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return m3075._sum_bool(rows, key)


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return m3075.any_flag(rows, key)


class DeterministicSafetyReflexPolicy:
    """Full obs72-to-action3 deterministic safety-reflex actor."""

    def __init__(self, *, policy_config: Mapping[str, Any]):
        self.model = None
        self.policy_config = dict(policy_config)
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
        action = actor_visible_safety_reflex_action(observation, config=self.policy_config).astype(np.float32)
        self.last_sequence = None
        self.step_count += 1
        self.raw_action_abs_max = max(self.raw_action_abs_max, float(np.max(np.abs(action))))
        self.raw_action_l2_sum += float(np.linalg.norm(action))
        self.final_action_abs_max = max(self.final_action_abs_max, float(np.max(np.abs(action))))
        return action

    def telemetry(self) -> dict[str, Any]:
        steps = int(self.step_count)
        return {
            "candidate_output_semantics": DIRECT_ACTION_SEMANTICS,
            "runtime_base_policy_required": False,
            "direct_action_step_count": steps,
            "raw_action_abs_max": float(self.raw_action_abs_max),
            "raw_action_l2_mean": float(self.raw_action_l2_sum / steps) if steps else 0.0,
            "action_clip_fraction": 0.0,
            "final_action_abs_max": float(self.final_action_abs_max),
        }


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "measurement_episode_rows": output_dir / "measurement_episode_rows.csv",
        "measurement_failure_rows": output_dir / "measurement_failure_rows.csv",
        "metric_summary_rows": output_dir / "metric_summary_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3079_audit: Path,
    m3078_dir: Path,
    m3039_dir: Path,
    m3037_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3079_audit": m3079_audit,
        "m3078_summary": m3078_dir / "summary.json",
        "m3078_policy_config": m3078_dir / "direct_action_policy_config.json",
        "m3078_feature_rows": m3078_dir / "actor_visible_feature_contract_rows.csv",
        "m3078_rule_rows": m3078_dir / "safety_reflex_rule_rows.csv",
        "m3078_exclusion_rows": m3078_dir / "actor_input_exclusion_rows.csv",
        "m3078_admission_rows": m3078_dir / "measurement_admission_gate_rows.csv",
        "m3078_claim_rows": m3078_dir / "claim_boundary_rows.csv",
        "m3078_gate_rows": m3078_dir / "gate_matrix.csv",
        "m3039_summary": m3039_dir / "summary.json",
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
        "m3079_audit_text": paths["m3079_audit"].read_text(encoding="utf-8") if exists["m3079_audit"] else "",
        "m3078_summary": read_json(paths["m3078_summary"]) if exists["m3078_summary"] else {},
        "m3078_policy_config": read_json(paths["m3078_policy_config"]) if exists["m3078_policy_config"] else {},
        "m3078_feature_rows": read_csv_rows(paths["m3078_feature_rows"]),
        "m3078_rule_rows": read_csv_rows(paths["m3078_rule_rows"]),
        "m3078_exclusion_rows": read_csv_rows(paths["m3078_exclusion_rows"]),
        "m3078_admission_rows": read_csv_rows(paths["m3078_admission_rows"]),
        "m3078_claim_rows": read_csv_rows(paths["m3078_claim_rows"]),
        "m3078_gate_rows": read_csv_rows(paths["m3078_gate_rows"]),
        "m3039_summary": read_json(paths["m3039_summary"]) if exists["m3039_summary"] else {},
        "m3037_summary": read_json(paths["m3037_summary"]) if exists["m3037_summary"] else {},
        "m3037_baseline_rows": read_csv_rows(paths["m3037_baseline_rows"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def policy_contract_pass(policy_config: Mapping[str, Any]) -> bool:
    return bool(
        int(policy_config.get("observation_shape", -1)) == P0_OBSERVATION_DIM
        and int(policy_config.get("action_shape", -1)) == ACTION_DIM
        and tuple(policy_config.get("output_components", [])) == DIRECT_ACTION_COMPONENTS
        and str(policy_config.get("output_semantics", "")) == DIRECT_ACTION_SEMANTICS
        and not _bool(policy_config.get("runtime_base_policy_required", True))
    )


def workload_plan(source: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_rows = m3075.baseline_by_index(source["m3037_baseline_rows"])
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
        profile_name = str(workload.get("profile_binding_name", ""))
        status_pass = bool(
            _bool(workload.get("status_pass", False))
            and bool(baseline)
            and Path(config_path).exists()
            and int(workload.get("actor_observation_dim", -1)) == P0_OBSERVATION_DIM
            and int(workload.get("actor_action_dim", -1)) == ACTION_DIM
            and not hidden_label_violation
        )
        rows.append(
            {
                **dict(workload),
                "measurement_episode_id": f"m3080-measurement-episode-{index:04d}",
                "source_episode_index": index,
                "baseline_measurement_row_id": baseline.get("baseline_measurement_row_id", ""),
                "baseline": baseline,
                "base_profile_name": profile_name,
                "direct_action_profile_name": f"{profile_name}+m3078_deterministic_safety_reflex",
                "config_path": config_path,
                "eval_seed": int(baseline.get("eval_seed", 301500 + index - 1)),
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
                "runtime_base_policy_required": False,
            }
        )
    return rows


def measurement_metadata(plan: Mapping[str, Any], telemetry: Mapping[str, Any]) -> dict[str, Any]:
    baseline = dict(plan.get("baseline") or {})
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
        "direct_action_profile_name": plan.get("direct_action_profile_name", ""),
        "binding_role": plan.get("binding_role", ""),
        "task_family": plan.get("task_family", ""),
        "source_edge": plan.get("source_edge", ""),
        "window_tag": plan.get("window_tag", ""),
        "strata": plan.get("strata", ""),
        "eval_seed": int(plan.get("eval_seed", 0)),
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
    }


def normalize_measurement_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return m3075.normalize_measurement_row(row)


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
            "direct_action_profile_name": plan.get("direct_action_profile_name", ""),
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


def run_measurement_plan(
    *,
    plan_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    policy_config: Mapping[str, Any],
    output_dir: Path,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in executable_specs
    }
    cache: dict[tuple[str, str], dict[str, Any]] = {}
    episodes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    contract_pass = policy_contract_pass(policy_config)
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("measurement plan row failed pre-execution guards")
            if not contract_pass:
                raise ValueError("M3078 deterministic safety-reflex policy config failed actor contract")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            cache_key = (profile_name, config_path)
            if cache_key not in cache:
                cache[cache_key] = m3075.profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
            profile_config = cache[cache_key]
            env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_config)
            env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
            policy = DeterministicSafetyReflexPolicy(policy_config=policy_config)
            try:
                if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
                    raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
                if int(env.action_space.shape[0]) != ACTION_DIM:
                    raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
                row = run_episode_with_policy(env, policy, "m3078_deterministic_safety_reflex", int(plan["eval_seed"]))
            finally:
                env.close()
            row.update(measurement_metadata(plan, policy.telemetry()))
            episodes.append(normalize_measurement_row(row))
        except Exception as exc:  # noqa: BLE001 - every scheduled row must be accounted.
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
                "metric_summary_id": f"m3080-metric-summary-{len(summaries) + 1:04d}",
                "group": group,
                "episode_count": len(group_rows),
                "success_rate": _mean(float(_success(row)) for row in group_rows),
                "collision_rate": _mean(float(_bool(row.get("collision", False))) for row in group_rows),
                "offtrack_rate": _mean(float(str(row.get("termination_reason", "")) == "off_track") for row in group_rows),
                "speed_too_low_rate": _mean(
                    float(str(row.get("termination_reason", "")) == "speed_too_low") for row in group_rows
                ),
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
                "measurement_only_no_ranking_claim": True,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return summaries


def guard(guard_id: str, family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3080-{guard_id}",
        "guard_family": family,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def actor_contract_guard_rows(
    *,
    policy_config: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = plan_rows + episodes + failures
    accounted = {
        str(row.get("measurement_episode_id", "")) for row in episodes + failures if row.get("measurement_episode_id")
    }
    sample_action = actor_visible_safety_reflex_action(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32), config=policy_config)
    return [
        guard("actor_observation_dim", "actor_contract", P0_OBSERVATION_DIM, 72),
        guard("actor_action_dim", "actor_contract", ACTION_DIM, 3),
        guard("policy_config_contract_pass", "actor_contract", policy_contract_pass(policy_config), True),
        guard("sample_action_shape", "actor_contract", tuple(sample_action.shape), (3,)),
        guard("sample_action_finite", "actor_contract", bool(np.all(np.isfinite(sample_action))), True),
        guard("sample_action_bounded", "actor_contract", bool(np.max(np.abs(sample_action)) <= 1.0), True),
        guard("scheduled_measurement_rows", "denominator", len(plan_rows), EXPECTED_WORKLOAD_ROWS),
        guard("accounted_measurement_rows", "denominator", len(accounted), len(plan_rows)),
        guard("profile_binding_count", "denominator", len({row.get("base_profile_name", "") for row in plan_rows}), EXPECTED_PROFILE_BINDINGS),
        guard("runtime_base_policy_required", "actor_contract", any_flag(combined, "runtime_base_policy_required"), False),
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


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m3080-{claim_id}",
        "claim_family": family,
        "allowed_in_m3080": allowed,
        "claim_made": made,
        "status_pass": bool(allowed) or not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def claim_boundary_rows(*, measurement_rows_present: bool, artifacts_present: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("closed_loop_measurement_rows", "measurement", measurement_rows_present, "measurement_episode_rows.csv"),
        ("metric_summary_rows", "measurement_metric", artifacts_present, "metric_summary_rows.csv"),
        ("actor_contract_guards", "guard", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_guards", "guard", artifacts_present, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3081 audit manifest"),
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
        ("runtime_base_policy_dependency", "contract", "M3078 direct-action actor forbids runtime base policy use"),
    ]
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3080-{gate_id}",
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
    policy_config: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    actor_guards: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    source_present = all(source["source_exists"].values())
    audit_accepts = (
        "accept_m3078_safety_reflex_materialization_route_to_m3080_same_denominator_measurement_preflight"
        in source["m3079_audit_text"]
    )
    selected_finite = selected_metrics_are_finite(episodes) if episodes else False
    runtime_base_policy_required = any_flag(episodes + failures, "runtime_base_policy_required")
    return [
        gate("source_artifacts_present", "source", source_present, source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3079_accepts_m3080_route", "lineage", audit_accepts, "route marker", "present", "lineage_invalid"),
        gate("m3078_status_pass", "lineage", _bool(source["m3078_summary"].get("status_pass", False)), source["m3078_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3078_gate_matrix_pass", "lineage", _bool(source["m3078_summary"].get("gate_matrix_pass", False)), source["m3078_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("policy_config_contract_pass", "contract", policy_contract_pass(policy_config), policy_contract_pass(policy_config), True, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not runtime_base_policy_required, runtime_base_policy_required, False, "contract_violation"),
        gate("measurement_denominator", "denominator", len(plan_rows) == EXPECTED_WORKLOAD_ROWS, len(plan_rows), EXPECTED_WORKLOAD_ROWS, "scenario_sampling_failure"),
        gate("baseline_denominator", "denominator", len(source["m3037_baseline_rows"]) == EXPECTED_WORKLOAD_ROWS, len(source["m3037_baseline_rows"]), EXPECTED_WORKLOAD_ROWS, "scenario_sampling_failure"),
        gate("measurement_episode_rows", "execution", len(episodes) == EXPECTED_WORKLOAD_ROWS, len(episodes), EXPECTED_WORKLOAD_ROWS, "metric_artifact"),
        gate("measurement_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("selected_metrics_finite", "metric", selected_finite, selected_finite, True, "metric_artifact"),
        gate("actor_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in actor_guards), "all", "pass", "contract_violation"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
        gate(
            "forbidden_flags_clear",
            "claim",
            not any_flag(episodes + failures, "driver_performance_claim_made")
            and not any_flag(episodes + failures, "validation_result_claim_made")
            and not any_flag(episodes + failures, "current_sim_verdict_claim_made"),
            "forbidden claim flags",
            "clear",
            "contract_violation",
        ),
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30760,
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
        "hypothesis": "A bounded result audit can accept or reject the M3080 same-denominator deterministic safety-reflex closed-loop measurement artifacts before any validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, repair-success, or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(DEFAULT_M3078_DIR / "direct_action_policy_config.json"), str(doc_path)],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "measurement_episode_rows.csv"),
                str(output_dir / "measurement_failure_rows.csv"),
                str(output_dir / "metric_summary_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit deterministic safety-reflex same-denominator measurement before interpretation"],
            "derived_from": [MILESTONE_ID, M3079_ID],
            "blocked_by": [
                "M3080 measurement rows require audit before any continuation or stop decision",
                "current-sim measurement rows are not validation or promotion evidence before M3081",
            ],
            "supersedes": ["direct interpretation of M3080 measurement rows without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3081 must audit M3080 summary measurement metric guard claim and gate artifacts",
            "M3081 must compare M3080 to M3067/M3075 on the same-denominator safety surface without making a validation or performance claim",
            "M3081 must preserve actor 72/action 3, direct-action/base-policy-free runtime, and claim boundaries",
            "M3081 must reject validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims unless separately routed",
            "M3081 must select exactly one continuation repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun rollout validate rank promote tune or mutate checkpoints",
            "do not convert M3080 rows into performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_deployable_direct_action_reflex",
            "evidence_axis": "actor_visible_deterministic_direct_action_safety_reflex_closed_loop_measurement_result_audit",
            "evidence_increment": "audits same-denominator closed-loop measurement rows for the deterministic safety-reflex candidate",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success or self-ID claim",
            "stop_condition": [
                "stop if M3080 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize if M3080 is negative on primary safety counts relative to M3067/M3075",
            ],
            "fallback_plan": [
                "route to measurement harness repair if artifacts are incomplete",
                "route to deterministic policy repair if actor behavior is negative but mechanism is clear",
                "route to branch synthesis or stop if deterministic safety-reflex behavior is clearly negative",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3080 completes deterministic safety-reflex closed-loop measurement preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3080 deterministic direct-action safety-reflex closed-loop measurement artifacts",
            "admission_evidence": ["M3080 summary and gate matrix", "M3080 measurement episode metric actor contract and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3081 status queue scoreboard research log and review",
                "one follow-up manifest only if M3081 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3081 accepts or rejects M3080 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3081 audits engineering measurement artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3081; finite-window and GRU comparison remains a later same-case engineering ablation."],
            "temporal_evidence_window": "M3080 deterministic safety-reflex measurement artifacts only.",
            "negative_result_policy": "Preserve negative measurement evidence and route to engineering repair, synthesis, or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3080 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the first deterministic safety-reflex same-denominator behavior measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3081 audits engineering measurement evidence",
            "must_synthesize_if": [
                "M3081 cannot accept M3080 as complete and claim-safe",
                "M3081 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict or self-ID evidence",
                "M3081 cannot select a repair continuation synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3081 audits M3080 row counts gates actor contract and claim boundaries",
            "M3081 compares M3080 against M3067/M3075 same-denominator safety counts without overclaiming",
            "M3081 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3081 hides M3080 failures or missing artifacts",
            "M3081 treats M3080 measurements as validation or performance verdict",
            "M3081 changes actor input or action contract",
            "M3081 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3081 audits M3080 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_deterministic_safety_reflex_measurement_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(DEFAULT_M3078_DIR / "direct_action_policy_config.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M3080 Active Safety Driver v1 Deterministic Direct-Action Safety-Reflex Closed-Loop Measurement Preflight",
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
            f"- speed-too-low count: {summary['measurement_speed_too_low_count']}",
            f"- clearance margin mean: {summary['measurement_clearance_margin_mean']}",
            f"- high sideslip fraction mean: {summary['measurement_high_sideslip_fraction_mean']}",
            f"- raw action abs max: {summary['measurement_raw_action_abs_max']}",
            f"- action clip fraction mean: {summary['measurement_action_clip_fraction_mean']}",
            f"- final action abs max: {summary['measurement_final_action_abs_max']}",
            f"- runtime base policy required: {summary['runtime_base_policy_required']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3080 records same-denominator current-sim measurement rows for the M3078 deterministic direct-action safety-reflex candidate. These rows are measurement artifacts for M3081 audit only. They are not validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.",
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
    m3079_audit: Path,
    m3078_dir: Path,
    m3039_dir: Path,
    m3037_dir: Path,
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
        m3079_audit=m3079_audit,
        m3078_dir=m3078_dir,
        m3039_dir=m3039_dir,
        m3037_dir=m3037_dir,
        m3012_dir=m3012_dir,
    )
    policy_config = source["m3078_policy_config"]
    plan_rows = workload_plan(source)
    measurement = run_measurement_plan(
        plan_rows=plan_rows,
        executable_specs=source["m3012_executable_specs"],
        policy_config=policy_config,
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    episodes = measurement["episodes"]
    failures = measurement["failures"]
    metric_rows = metric_summary_rows(episodes)
    actor_guards = actor_contract_guard_rows(
        policy_config=policy_config,
        plan_rows=plan_rows,
        episodes=episodes,
        failures=failures,
    )
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
        (paths["actor_contract_guard_rows"], actor_guards, GUARD_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fields)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        policy_config=policy_config,
        plan_rows=plan_rows,
        episodes=episodes,
        failures=failures,
        actor_guards=actor_guards,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episodes)
    profile_counts = Counter(str(row.get("base_profile_name", "")) for row in episodes)
    raw_action_abs_max = max((_float(row.get("raw_action_abs_max")) for row in episodes), default=0.0)
    final_action_abs_max = max((_float(row.get("final_action_abs_max")) for row in episodes), default=0.0)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_closed_loop_measurement_preflight_pass"
            if status_pass
            else "active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_closed_loop_measurement_preflight_fail"
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
        "measurement_clearance_margin_mean": _mean(_float(row.get("min_clearance_margin")) for row in episodes),
        "measurement_high_sideslip_fraction_mean": _mean(_float(row.get("high_sideslip_fraction")) for row in episodes),
        "measurement_lateral_rmse_mean": _mean(_float(row.get("lateral_rmse")) for row in episodes),
        "measurement_raw_action_abs_max": raw_action_abs_max,
        "measurement_raw_action_l2_mean": _mean(_float(row.get("raw_action_l2_mean")) for row in episodes),
        "measurement_action_clip_fraction_mean": _mean(_float(row.get("action_clip_fraction")) for row in episodes),
        "measurement_final_action_abs_max": final_action_abs_max,
        "metric_summary_row_count": len(metric_rows),
        "actor_contract_guard_row_count": len(actor_guards),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_guards),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3078_status_pass": _bool(source["m3078_summary"].get("status_pass", False)),
        "m3078_gate_matrix_pass": _bool(source["m3078_summary"].get("gate_matrix_pass", False)),
        "policy_config_contract_pass": policy_contract_pass(policy_config),
        "candidate_output_semantics": DIRECT_ACTION_SEMANTICS,
        "candidate_output_components": list(DIRECT_ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "base_policy_required_at_runtime": False,
        "direct_action_formula": "final_action = actor_visible_safety_reflex_action(obs72)",
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
        "decision": "active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_measurement_route_to_m3081_result_audit",
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
    parser.add_argument("--m3079-audit", type=Path, default=DEFAULT_M3079_AUDIT)
    parser.add_argument("--m3078-dir", type=Path, default=DEFAULT_M3078_DIR)
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
        m3079_audit=args.m3079_audit,
        m3078_dir=args.m3078_dir,
        m3039_dir=args.m3039_dir,
        m3037_dir=args.m3037_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"measurement_rows={summary['measurement_episode_row_count']}")
    print(f"measurement_failures={summary['measurement_failure_row_count']}")
    print(f"success_count={summary['measurement_success_count']}")
    print(f"collision_count={summary['measurement_collision_count']}")
    print(f"offtrack_count={summary['measurement_offtrack_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
