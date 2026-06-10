"""Run M3196 preterminal authority boundary-stability candidate full-fresh measurement."""

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
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.controller_profile_runtime import wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight as m3075
from autodrift.engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_candidate_implementation_materialization_preflight import (
    ACTION_COMPONENTS,
    OUTPUT_SEMANTICS,
    POLICY_CONFIG,
    POLICY_ID,
    preterminal_authority_boundary_stability_candidate_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3196-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-candidate-full-fresh-measurement-preflight"
)
NEXT_ID = (
    "m3197-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-candidate-full-fresh-measurement-result-audit"
)
M3195_ID = (
    "m3195-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-candidate-implementation-result-audit"
)
M3194_ID = (
    "m3194-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-candidate-implementation-materialization-preflight"
)
M3181_ID = (
    "m3181-engineering-controller-active-safety-driver-residual-hard-safety-"
    "steer-delta-regression-guard-full-fresh-measurement-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3195_AUDIT = Path(f"docs/{M3195_ID}.md")
DEFAULT_M3194_DIR = Path(
    "runs/m3194_engineering_controller_active_safety_driver_residual_hard_safety_"
    "preterminal_authority_boundary_stability_candidate_implementation_materialization_preflight"
)
DEFAULT_M3181_DIR = Path(
    "runs/m3181_engineering_controller_active_safety_driver_residual_hard_safety_"
    "steer_delta_regression_guard_full_fresh_measurement_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3196_engineering_controller_active_safety_driver_residual_hard_safety_"
    "preterminal_authority_boundary_stability_candidate_full_fresh_measurement_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_FULL_ROWS = 64
BASELINE_IDS = ("m3105", "m3181")
CLAIM_SCOPE = (
    "M3196 Active Safety Driver residual hard-safety preterminal authority and boundary-stability "
    "candidate full-fresh measurement preflight only; the complete 64-row fresh denominator may "
    "be executed through the M3194 deterministic direct-action function as the full obs72-to-action3 "
    "action source and measured against same-row M3105 and M3181 artifacts. No validation, ranking, "
    "winner selection, checkpoint mutation, checkpoint promotion, public driver default mutation, "
    "driver-performance verdict, current-sim verdict, repair success, robustness-result, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full ideal driver "
    "completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint "
    "promotion, public driver default replacement, high-fidelity validation readiness or result, "
    "paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

EPISODE_FIELDNAMES = m3088.EPISODE_FIELDNAMES
FAILURE_FIELDNAMES = m3088.FAILURE_FIELDNAMES
METRIC_FIELDNAMES = m3088.METRIC_FIELDNAMES
GUARD_FIELDNAMES = m3088.GUARD_FIELDNAMES
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3196",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = m3088.GATE_FIELDNAMES
COMPARISON_FIELDNAMES = [
    "comparison_id",
    "measurement_episode_id",
    "baseline_id",
    "baseline_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "m3196_success",
    "baseline_success",
    "success_delta",
    "m3196_collision",
    "baseline_collision",
    "collision_delta",
    "m3196_offtrack",
    "baseline_offtrack",
    "offtrack_delta",
    "m3196_speed_too_low",
    "baseline_speed_too_low",
    "speed_too_low_delta",
    "m3196_min_clearance_margin",
    "baseline_min_clearance_margin",
    "clearance_margin_delta",
    "m3196_return",
    "baseline_return",
    "return_delta",
    "m3196_speed_mean",
    "baseline_speed_mean",
    "speed_mean_delta",
    "exact_seed_match",
    "validation_run",
    "repair_success_claim_made",
    "claim_boundary",
]


def _bool(value: Any) -> bool:
    return m3088._bool(value)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "measurement_episode_rows": output_dir / "measurement_episode_rows.csv",
        "measurement_failure_rows": output_dir / "measurement_failure_rows.csv",
        "measurement_metric_summary_rows": output_dir / "measurement_metric_summary_rows.csv",
        "measurement_contract_guard_rows": output_dir / "measurement_contract_guard_rows.csv",
        "same_row_comparison_rows": output_dir / "same_row_comparison_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3195_audit: Path,
    m3194_dir: Path,
    m3181_dir: Path,
    m3105_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3195_audit": m3195_audit,
        "m3194_summary": m3194_dir / "summary.json",
        "m3194_gate_rows": m3194_dir / "gate_matrix.csv",
        "m3194_runtime_contract_rows": m3194_dir / "runtime_contract_rows.csv",
        "m3181_summary": m3181_dir / "summary.json",
        "m3181_measurement_rows": m3181_dir / "measurement_episode_rows.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_measurement_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3195_audit_text": paths["m3195_audit"].read_text(encoding="utf-8") if exists["m3195_audit"] else "",
        "m3194_summary": read_json(paths["m3194_summary"]) if exists["m3194_summary"] else {},
        "m3194_gate_rows": read_csv_rows(paths["m3194_gate_rows"]),
        "m3194_runtime_contract_rows": read_csv_rows(paths["m3194_runtime_contract_rows"]),
        "m3181_summary": read_json(paths["m3181_summary"]) if exists["m3181_summary"] else {},
        "m3181_measurement_rows": read_csv_rows(paths["m3181_measurement_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_measurement_rows": read_csv_rows(paths["m3105_measurement_rows"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def full_fresh_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    workloads = {str(row.get("executable_workload_id", "")): row for row in source["m3012_workload_rows"]}
    rows = sorted(source["m3181_measurement_rows"], key=lambda row: str(row.get("runtime_smoke_episode_id", "")))
    plan: list[dict[str, Any]] = []
    for source_row in rows:
        workload = workloads.get(str(source_row.get("executable_workload_id", "")), {})
        config_path = str(workload.get("config_path", ""))
        hidden_label_violation = any(
            _bool(source_row.get(field, False)) or _bool(workload.get(field, False))
            for field in (
                "hidden_oracle_actor_input_required",
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
            and int(float(source_row.get("eval_seed", 0))) > 0
            and not hidden_label_violation
            and str(source_row.get("candidate_output_semantics", "")) == OUTPUT_SEMANTICS
        )
        plan.append(
            {
                **dict(source_row),
                **dict(workload),
                "runtime_smoke_episode_id": f"m3196-measurement-episode-{len(plan) + 1:04d}",
                "source_measurement_episode_id": source_row.get("source_measurement_episode_id", ""),
                "config_path": config_path,
                "base_profile_name": workload.get("profile_binding_name", source_row.get("base_profile_name", "")),
                "hidden_label_violation": hidden_label_violation,
                "status_pass": status_pass,
            }
        )
    return plan


class M3196MeasurementPolicy:
    def __init__(self):
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0
        self.final_action_abs_max = 0.0

    def reset(self) -> None:
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0
        self.final_action_abs_max = 0.0

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        del info
        action = preterminal_authority_boundary_stability_candidate_action(observation, POLICY_CONFIG)
        self.step_count += 1
        self.raw_action_abs_max = max(self.raw_action_abs_max, float(np.max(np.abs(action))))
        self.raw_action_l2_sum += float(np.linalg.norm(action))
        self.final_action_abs_max = max(self.final_action_abs_max, float(np.max(np.abs(action))))
        return action

    def telemetry(self) -> dict[str, Any]:
        steps = int(self.step_count)
        return {
            "runtime_driver_id": POLICY_ID,
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


def normalize_episode_row(plan: Mapping[str, Any], row: Mapping[str, Any], telemetry: Mapping[str, Any]) -> dict[str, Any]:
    item = m3088.normalize_episode_row(plan, row, telemetry)
    item.update(
        {
            "runtime_driver_id": POLICY_ID,
            "policy": "active_safety_driver_preterminal_authority_boundary_stability_candidate_measurement",
            "claim_boundary": CLAIM_SCOPE,
            "driver_performance_claim_made": False,
            "repair_success_claim_made": False,
            "robustness_result_claim_made": False,
            "validation_result_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "high_fidelity_validation_claim_made": False,
            "level3_self_id_claim_made": False,
        }
    )
    return item


def failure_row(plan: Mapping[str, Any], *, error_type: str, error_message: str) -> dict[str, Any]:
    row = m3088.failure_row(plan, error_type=error_type, error_message=error_message)
    row.update(
        {
            "runtime_driver_id": POLICY_ID,
            "claim_boundary": CLAIM_SCOPE,
            "driver_performance_claim_made": False,
        }
    )
    return row


def run_measurement_plan(
    *,
    plan_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    output_dir: Path,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in executable_specs
    }
    profile_cache: dict[tuple[str, str], dict[str, Any]] = {}
    episodes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("M3196 plan row failed pre-execution guards")
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
            policy = M3196MeasurementPolicy()
            try:
                if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
                    raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
                if int(env.action_space.shape[0]) != ACTION_DIM:
                    raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
                row = m3088.run_episode_with_policy(
                    env,
                    policy,
                    "active_safety_driver_preterminal_authority_boundary_stability_candidate_measurement",
                    int(float(plan["eval_seed"])),
                )
            finally:
                env.close()
            episodes.append(normalize_episode_row(plan, row, policy.telemetry()))
        except Exception as exc:  # noqa: BLE001
            failures.append(failure_row(plan, error_type=type(exc).__name__, error_message=str(exc)))
        write_run_state(
            output_dir / "run_state.json",
            {
                "scheduled_measurement_row_count": len(plan_rows),
                "measurement_episode_row_count": len(episodes),
                "measurement_failure_row_count": len(failures),
                "latest_measurement_episode_id": plan.get("runtime_smoke_episode_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return {"episodes": episodes, "failures": failures}


def same_row_comparison_rows(
    episodes: list[dict[str, Any]],
    *,
    m3105_rows: list[dict[str, Any]],
    m3181_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baselines = {
        "m3105": {str(row.get("source_measurement_episode_id", "")): row for row in m3105_rows},
        "m3181": {str(row.get("source_measurement_episode_id", "")): row for row in m3181_rows},
    }
    rows: list[dict[str, Any]] = []
    for episode in episodes:
        source_id = str(episode.get("source_measurement_episode_id", ""))
        for baseline_id, table in baselines.items():
            baseline = table.get(source_id, {})
            exact_seed = str(episode.get("eval_seed", "")) == str(baseline.get("eval_seed", ""))
            row = {
                "comparison_id": f"m3196-comparison-{len(rows) + 1:04d}",
                "measurement_episode_id": episode.get("runtime_smoke_episode_id", ""),
                "baseline_id": baseline_id,
                "baseline_episode_id": baseline.get("runtime_smoke_episode_id", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": episode.get("fresh_panel_row_id", ""),
                "axis_id": episode.get("axis_id", ""),
                "binding_role": episode.get("binding_role", ""),
                "task_family": episode.get("task_family", ""),
                "eval_seed": episode.get("eval_seed", ""),
                "m3196_success": _success(episode),
                "baseline_success": _success(baseline),
                "m3196_collision": _bool(episode.get("collision", False)),
                "baseline_collision": _bool(baseline.get("collision", False)),
                "m3196_offtrack": _offtrack(episode),
                "baseline_offtrack": _offtrack(baseline),
                "m3196_speed_too_low": _speed_too_low(episode),
                "baseline_speed_too_low": _speed_too_low(baseline),
                "m3196_min_clearance_margin": _float(episode.get("min_clearance_margin")),
                "baseline_min_clearance_margin": _float(baseline.get("min_clearance_margin")),
                "m3196_return": _float(episode.get("return")),
                "baseline_return": _float(baseline.get("return")),
                "m3196_speed_mean": _float(episode.get("speed_mean")),
                "baseline_speed_mean": _float(baseline.get("speed_mean")),
                "exact_seed_match": exact_seed,
                "validation_run": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
            row.update(
                {
                    "success_delta": int(row["m3196_success"]) - int(row["baseline_success"]),
                    "collision_delta": int(row["m3196_collision"]) - int(row["baseline_collision"]),
                    "offtrack_delta": int(row["m3196_offtrack"]) - int(row["baseline_offtrack"]),
                    "speed_too_low_delta": int(row["m3196_speed_too_low"]) - int(row["baseline_speed_too_low"]),
                    "clearance_margin_delta": _float(row["m3196_min_clearance_margin"]) - _float(row["baseline_min_clearance_margin"]),
                    "return_delta": _float(row["m3196_return"]) - _float(row["baseline_return"]),
                    "speed_mean_delta": _float(row["m3196_speed_mean"]) - _float(row["baseline_speed_mean"]),
                }
            )
            rows.append(row)
    return rows


def _with_scope(rows: list[dict[str, Any]], *, id_prefix: str = "m3196") -> list[dict[str, Any]]:
    updated = []
    for row in rows:
        item = dict(row)
        item["claim_boundary"] = CLAIM_SCOPE
        item["runtime_driver_id"] = POLICY_ID
        if "policy" in item:
            item["policy"] = "active_safety_driver_preterminal_authority_boundary_stability_candidate_measurement"
        for key in ("metric_summary_id", "guard_id", "gate_id", "claim_id"):
            if key in item:
                item[key] = str(item[key]).replace("m3088", id_prefix, 1)
        updated.append(item)
    return updated


def contract_guard_rows(source: Mapping[str, Any], plan_rows: list[dict[str, Any]], episodes: list[dict[str, Any]], failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sample = preterminal_authority_boundary_stability_candidate_action(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32), POLICY_CONFIG)
    hidden_runtime_inputs = any(
        _bool(row.get(field, False))
        for row in plan_rows + episodes + failures
        for field in (
            "hidden_oracle_actor_input_required",
            "source_labels_actor_visible",
            "route_labels_actor_visible",
            "outcome_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
            "ttc_actor_input_required",
        )
    )
    rows = [
        m3088.guard("contract_observation_shape", "contract", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM),
        m3088.guard("contract_action_shape", "contract", ACTION_DIM, ACTION_DIM),
        m3088.guard("contract_action_components", "contract", "|".join(ACTION_COMPONENTS), "|".join(("steer", "throttle", "brake"))),
        m3088.guard("contract_output_semantics", "contract", OUTPUT_SEMANTICS, "direct_action_clipped"),
        m3088.guard("sample_action_shape", "runtime_api", tuple(sample.shape), (ACTION_DIM,)),
        m3088.guard("sample_action_finite", "runtime_api", bool(np.all(np.isfinite(sample))), True),
        m3088.guard("sample_action_bounded", "runtime_api", bool(np.max(np.abs(sample)) <= 1.0), True),
        m3088.guard("hidden_runtime_inputs_used", "contract", hidden_runtime_inputs, False),
        m3088.guard("m3194_status_pass", "lineage", _bool(source["m3194_summary"].get("status_pass", False)), True),
        m3088.guard("m3194_gate_matrix_pass", "lineage", _bool(source["m3194_summary"].get("gate_matrix_pass", False)), True),
    ]
    return _with_scope(rows)


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("measurement_rows", "measurement_artifact", True, True, "measurement_episode_rows.csv"),
        ("same_row_comparison_rows", "measurement_artifact", True, True, "same_row_comparison_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("validation_result", "forbidden", False, False, "separate validation execution after accepted deployable candidate"),
        ("driver_performance_verdict", "forbidden", False, False, "validation and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "current-sim result synthesis after measurement audit"),
        ("repair_success", "forbidden", False, False, "accepted full-fresh improvement plus validation path"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3196"),
    ]
    return [
        {
            "claim_id": f"m3196-{claim_id}",
            "claim_family": family,
            "allowed_in_m3196": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3196-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _m3195_selects_m3196(text: str) -> bool:
    return (
        "m3196-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-candidate-full-fresh-measurement-preflight"
        in text
        or "full-fresh measurement preflight" in text
    )


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    comparison_counts = Counter(str(row.get("baseline_id", "")) for row in comparisons)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3195_selects_m3196_route", "lineage", _m3195_selects_m3196(source["m3195_audit_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3194_status_pass", "lineage", _bool(source["m3194_summary"].get("status_pass", False)), source["m3194_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3194_gate_matrix_pass", "lineage", _bool(source["m3194_summary"].get("gate_matrix_pass", False)), source["m3194_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3181_status_pass", "lineage", _bool(source["m3181_summary"].get("status_pass", False)), source["m3181_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("scheduled_measurement_rows", "execution", len(plan_rows) == EXPECTED_FULL_ROWS, len(plan_rows), EXPECTED_FULL_ROWS, "scenario_sampling_failure"),
        gate("measurement_episode_rows", "execution", len(episodes) == EXPECTED_FULL_ROWS, len(episodes), EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("measurement_failure_rows", "execution", len(failures) == 0, len(failures), 0, "metric_artifact"),
        gate("selected_metrics_finite", "metric", selected_metrics_are_finite(episodes) if episodes else False, "finite" if episodes else "none", "finite", "metric_artifact"),
        gate("same_row_comparison_rows", "metric", len(comparisons) == EXPECTED_FULL_ROWS * len(BASELINE_IDS), len(comparisons), EXPECTED_FULL_ROWS * len(BASELINE_IDS), "metric_artifact"),
        gate("same_row_comparison_baselines", "metric", all(comparison_counts.get(baseline, 0) == EXPECTED_FULL_ROWS for baseline in BASELINE_IDS), dict(comparison_counts), f"{EXPECTED_FULL_ROWS} each", "metric_artifact"),
        gate("same_row_exact_seed_matches", "metric", all(_bool(row.get("exact_seed_match", False)) for row in comparisons), "all", "match", "metric_artifact"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in guards), "all", "pass", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claims), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31970,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": ["contract_violation", "lineage_invalid", "metric_artifact", "scenario_sampling_failure", "behavior_regression", "objective_overfit", "proof_washout", "seed_fragility"],
        "hypothesis": "A bounded result audit can accept or reject M3196 preterminal authority and boundary-stability candidate full-fresh measurement artifacts before validation synthesis or stop.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "measurement_episode_rows.csv"),
                str(output_dir / "same_row_comparison_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3196 full-fresh measurement before validation or stop"],
            "derived_from": [MILESTONE_ID, M3195_ID, M3194_ID, M3181_ID, M3105_ID],
            "blocked_by": ["M3196 measurement requires audit before validation or promotion"],
            "supersedes": ["unreviewed M3194 measurement interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3197 must audit M3196 measurement rows comparisons guards claims and gates",
            "M3197 must reject validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3197 must select exactly one validation-planning synthesis artifact-repair or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run validation ranking promotion or high-fidelity simulation in M3197",
            "do not convert M3196 measurement rows into repair-success performance current-sim robustness-result paper or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability",
            "evidence_axis": "preterminal_authority_boundary_stability_full_fresh_measurement_result_audit",
            "evidence_increment": "audits full-fresh measurement evidence for the M3194 candidate",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": ["stop if M3196 is behavior-negative or contract-unsafe", "route to validation planning only after audit acceptance"],
            "fallback_plan": ["route to M3196 artifact repair if rows or gates fail", "route to synthesis if behavior-negative"],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3196 completes full-fresh measurement",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3196 full-fresh measurement artifacts",
            "admission_evidence": ["M3196 summary measurement comparison guard claim and gate artifacts"],
            "blocked_shortcuts": ["no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim"],
            "allowed_updates": [f"docs/{NEXT_ID}.md", f"docs/reviews/{NEXT_ID}.md", f"experiments/reviews/{NEXT_ID}.json", "M3197 status queue scoreboard research log and review"],
            "next_stage_criteria": ["M3197 accepts or rejects M3196 and selects next route"],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3197 audits engineering measurement artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3197; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3196 measurement artifacts only.",
            "negative_result_policy": "Preserve engineering evidence and route validation planning synthesis or stop rather than returning self-ID to mainline objective.",
            "allowed_claims": ["M3196 artifact completeness and claim-safety audit", "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim"],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits full-fresh measurement before validation or synthesis",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3197 audits engineering measurement evidence",
            "must_synthesize_if": ["M3197 cannot select validation planning synthesis artifact-repair or stop", "M3197 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence"],
        },
        "success_criteria": [f"docs/{NEXT_ID}.md exists", "M3197 audits M3196 row counts gates actor contract and claim boundaries", "M3197 selects exactly one next route or stop state"],
        "failure_criteria": ["M3197 hides missing M3196 artifacts or failed gates", "M3197 treats M3196 measurement as validation or repair success", "M3197 leaves next route ambiguous"],
        "decision_rule": "Pass only if M3197 audits M3196 artifacts and selects one next route or stop state while preserving claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_steer_delta_regression_guard_full_fresh_measurement_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3196 Preterminal Authority Boundary-Stability Candidate Full-Fresh Measurement Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- scheduled rows: {summary['scheduled_measurement_row_count']}/{summary['target_measurement_row_count']}",
            f"- measurement rows: {summary['measurement_episode_row_count']}",
            f"- failures: {summary['measurement_failure_row_count']}",
            f"- success count: {summary['measurement_success_count']}",
            f"- collision count: {summary['measurement_collision_count']}",
            f"- offtrack count: {summary['measurement_offtrack_count']}",
            f"- success delta vs M3105: {summary['success_count_delta_vs_m3105']}",
            f"- collision delta vs M3105: {summary['collision_count_delta_vs_m3105']}",
            f"- success delta vs M3181: {summary['success_count_delta_vs_m3181']}",
            f"- collision delta vs M3181: {summary['collision_count_delta_vs_m3181']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3196 is a same-denominator measurement preflight for the M3194 preterminal authority and boundary-stability candidate. It is not validation, promotion, repair success, or a deployable-driver verdict.",
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


def run_full_fresh_measurement_preflight(
    *,
    m3195_audit: Path,
    m3194_dir: Path,
    m3181_dir: Path,
    m3105_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    device: str = "cpu",
) -> dict[str, Any]:
    del device
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3195_audit=m3195_audit, m3194_dir=m3194_dir, m3181_dir=m3181_dir, m3105_dir=m3105_dir, m3012_dir=m3012_dir)
    plan_rows = full_fresh_plan(source)
    result = run_measurement_plan(plan_rows=plan_rows, executable_specs=source["m3012_executable_specs"], output_dir=output_dir, next_blocker=NEXT_ID)
    episodes = result["episodes"]
    failures = result["failures"]
    metric_rows = _with_scope(m3088.metric_summary_rows(episodes))
    comparisons = same_row_comparison_rows(episodes, m3105_rows=source["m3105_measurement_rows"], m3181_rows=source["m3181_measurement_rows"])
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    guards = contract_guard_rows(source, plan_rows, episodes, failures)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["measurement_episode_rows"], episodes, fieldnames=EPISODE_FIELDNAMES)
    write_csv_rows(paths["measurement_failure_rows"], failures, fieldnames=FAILURE_FIELDNAMES)
    write_csv_rows(paths["measurement_metric_summary_rows"], metric_rows, fieldnames=METRIC_FIELDNAMES)
    write_csv_rows(paths["measurement_contract_guard_rows"], guards, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["same_row_comparison_rows"], comparisons, fieldnames=COMPARISON_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        episodes=episodes,
        failures=failures,
        comparisons=comparisons,
        guards=guards,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    by_baseline = {baseline: [row for row in comparisons if row["baseline_id"] == baseline] for baseline in BASELINE_IDS}

    def _sum_delta(baseline: str, field: str) -> int:
        return int(sum(int(row.get(field, 0)) for row in by_baseline.get(baseline, [])))

    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_preterminal_authority_boundary_stability_candidate_full_fresh_measurement_pass"
            if status_pass
            else "active_safety_driver_preterminal_authority_boundary_stability_candidate_full_fresh_measurement_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "runtime_driver_id": POLICY_ID,
        "scheduled_measurement_row_count": len(plan_rows),
        "target_measurement_row_count": EXPECTED_FULL_ROWS,
        "measurement_episode_row_count": len(episodes),
        "measurement_failure_row_count": len(failures),
        "measurement_success_count": sum(1 for row in episodes if _success(row)),
        "measurement_collision_count": sum(1 for row in episodes if _bool(row.get("collision", False))),
        "measurement_offtrack_count": sum(1 for row in episodes if _offtrack(row)),
        "measurement_speed_too_low_count": sum(1 for row in episodes if _speed_too_low(row)),
        "measurement_clearance_margin_mean": _mean(_float(row.get("min_clearance_margin")) for row in episodes),
        "same_row_comparison_row_count": len(comparisons),
        "success_count_delta_vs_m3105": _sum_delta("m3105", "success_delta"),
        "collision_count_delta_vs_m3105": _sum_delta("m3105", "collision_delta"),
        "offtrack_count_delta_vs_m3105": _sum_delta("m3105", "offtrack_delta"),
        "speed_too_low_count_delta_vs_m3105": _sum_delta("m3105", "speed_too_low_delta"),
        "success_count_delta_vs_m3181": _sum_delta("m3181", "success_delta"),
        "collision_count_delta_vs_m3181": _sum_delta("m3181", "collision_delta"),
        "offtrack_count_delta_vs_m3181": _sum_delta("m3181", "offtrack_delta"),
        "speed_too_low_count_delta_vs_m3181": _sum_delta("m3181", "speed_too_low_delta"),
        "contract_guard_row_count": len(guards),
        "contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in guards),
        "claim_boundary_row_count": len(claims),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claims),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
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
        "public_driver_default_mutated": False,
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
        "decision": "active_safety_driver_preterminal_authority_boundary_stability_candidate_full_fresh_measurement_route_to_m3197_result_audit",
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
    write_run_state(paths["run_state"], {"complete": status_pass, "status_pass": status_pass, "next_blocker": NEXT_ID})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3195-audit", type=Path, default=DEFAULT_M3195_AUDIT)
    parser.add_argument("--m3194-dir", type=Path, default=DEFAULT_M3194_DIR)
    parser.add_argument("--m3181-dir", type=Path, default=DEFAULT_M3181_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_full_fresh_measurement_preflight(
        m3195_audit=args.m3195_audit,
        m3194_dir=args.m3194_dir,
        m3181_dir=args.m3181_dir,
        m3105_dir=args.m3105_dir,
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
    print(f"success_delta_vs_m3105={summary['success_count_delta_vs_m3105']}")
    print(f"collision_delta_vs_m3105={summary['collision_count_delta_vs_m3105']}")
    print(f"success_delta_vs_m3181={summary['success_count_delta_vs_m3181']}")
    print(f"collision_delta_vs_m3181={summary['collision_count_delta_vs_m3181']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
