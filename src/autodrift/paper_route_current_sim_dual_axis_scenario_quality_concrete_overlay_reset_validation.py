"""Reset-only validation for M2461 concrete-overlay scenario-quality rows."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict, merge_env_config
from autodrift.env import AutoDriftEnv
from autodrift.paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter import (
    ALLOWED_OVERLAY_KEYS,
    read_csv_rows,
)


DEFAULT_M2461_DIR = Path(
    "runs/m2461_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation"
)
DEFAULT_TARGET_RESET_COUNT = 6
DEFAULT_EXPECTED_OBSERVATION_DIM = 72
DEFAULT_EVAL_SEED_BASE = 246400
DEFAULT_NEXT_BLOCKER = (
    "m2465-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-result-audit"
)

RESULT_PASS = "scenario_quality_concrete_overlay_reset_validation_pass"
RESULT_FAIL = "scenario_quality_concrete_overlay_reset_validation_fail"

TARGET_GROUPS = {"stable_feasibility_support", "stable_aes_support"}
ALLOWED_SPLITS = {"public_debug", "public_gate"}
BASE_HUMAN_VIEW_CONTRACT_ENV_CONFIG: dict[str, Any] = {
    "history_length": 1,
    "action_history_mode": "full",
    "include_privileged_params": False,
    "wheel_observation_mode": "none",
    "obstacle_relative_velocity_mode": "zero",
}

FALSE_GUARD_KEYS = [
    "labels_enter_actor_input",
    "actor_input_contract_changed",
    "scenario_redesign_executed",
    "policy_action_executed",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]

STATIC_VALIDATION_FIELDNAMES = [
    "static_scope",
    "reset_target_id",
    "preflight_id",
    "overlay_id",
    "source_candidate_id",
    "source_panel_id",
    "candidate_group",
    "split",
    "preflight_lane",
    "overlay_join_count",
    "candidate_row_present",
    "source_admission_pass",
    "target_row_contract_pass",
    "overlay_json_matches_preflight",
    "overlay_json_matches_candidate",
    "overlay_keys_allowed",
    "labels_metadata_only",
    "forbidden_execution_flags_clear",
    "static_validation_pass",
    "failure_type",
    "failure_reasons",
]

RESET_TARGET_FIELDNAMES = [
    "reset_target_id",
    "preflight_id",
    "overlay_id",
    "source_candidate_id",
    "source_panel_id",
    "candidate_group",
    "role_scope",
    "sampled_obstacle_label_scope",
    "split",
    "overlay_family",
    "env_config_overlay_hash",
    "effective_env_config_path",
    "eval_seed",
    "expected_observation_dim",
]

EFFECTIVE_CONFIG_FIELDNAMES = [
    "reset_target_id",
    "preflight_id",
    "source_candidate_id",
    "candidate_group",
    "effective_env_config_path",
    "effective_env_config_written",
    "effective_env_config_inside_run_dir",
    "base_contract_applied",
    "actor_contract_guardrail_pass",
    "obstacle_enabled",
    "env_build_success",
    "failure_type",
    "failure_reasons",
]

RESET_VALIDATION_FIELDNAMES = [
    "reset_target_id",
    "preflight_id",
    "source_candidate_id",
    "candidate_group",
    "role_scope",
    "environment_load_attempted",
    "environment_reset_attempted",
    "environment_reset_success",
    "observation_length",
    "expected_observation_length",
    "observation_dimension_matches_expected",
    "observation_finite",
    "obstacle_initialized",
    "obstacle_label",
    "environment_step_count",
    "policy_action_executed",
    "environment_rollout_started",
    "measured_rollout_started",
    "repair_execution_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "active_config_overwritten",
    "actor_input_contract_changed",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed_claim_made",
    "training_repair_success_claim_made",
    "current_sim_verdict_claim_made",
    "failure_type",
    "failure_reason",
]

RESET_FAILURE_FIELDNAMES = [
    "reset_target_id",
    "preflight_id",
    "source_candidate_id",
    "candidate_group",
    "failure_type",
    "failure_reason",
]

GUARDRAIL_FIELDNAMES = [
    "guardrail_id",
    "guardrail_class",
    "source_role_or_axis",
    "failure_mode_to_preserve",
    "metric_to_watch",
    "value",
    "violation",
    "reason",
]

CLAIM_FIELDNAMES = ["claim_key", "claim_value", "admissible", "reason"]
DECISION_FIELDNAMES = ["decision_key", "decision_value", "admissible", "reason"]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_id(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")
    return safe or "reset_target"


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"))


def _parse_overlay(raw: Any) -> dict[str, Any]:
    parsed = json.loads(str(raw))
    if not isinstance(parsed, dict):
        raise ValueError("env_config_overlay_json must decode to an object")
    return parsed


def _flatten_overlay_keys(data: Mapping[str, Any], prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in data.items():
        flat_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            keys.update(_flatten_overlay_keys(value, flat_key))
        else:
            keys.add(flat_key)
    return keys


def _overlay_hash(overlay: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(overlay).encode("utf-8")).hexdigest()


def _observation_length(obs: Any) -> int:
    array = np.asarray(obs, dtype=np.float64)
    if array.ndim == 0:
        return 0
    return int(array.size)


def _finite_observation(obs: Any) -> bool:
    try:
        array = np.asarray(obs, dtype=np.float64)
    except (TypeError, ValueError):
        return False
    return bool(array.size > 0 and np.all(np.isfinite(array)))


def _effective_env_config_path(output_dir: Path, reset_target_id: str) -> Path:
    return output_dir / "effective_env_configs" / f"{_safe_id(reset_target_id)}.json"


def _overlay_family_for_group(group: str) -> str:
    if group == "stable_feasibility_support":
        return "R0_stable_avoidable"
    if group == "stable_aes_support":
        return "R1_aeb_infeasible_stable_aes"
    return ""


def _source_admission_failures(summary: Mapping[str, Any]) -> list[str]:
    checks = [
        (
            str(summary.get("result_class", "")) == "scenario_quality_concrete_overlay_materialization_preflight_pass",
            "source_result_class_not_pass",
        ),
        (int(summary.get("target_preflight_row_count", -1)) == 6, "source_target_preflight_count_not_6"),
        (int(summary.get("concrete_overlay_row_count", -1)) == 6, "source_concrete_overlay_row_count_not_6"),
        (
            int(summary.get("adapter_concrete_overlay_available_count", -1)) == 6,
            "source_adapter_overlay_available_count_not_6",
        ),
        (int(summary.get("adapter_static_check_fail_count", -1)) == 0, "source_adapter_static_failures"),
        (int(summary.get("adapter_reset_attempted_count", -1)) == 0, "source_adapter_reset_already_attempted"),
        (int(summary.get("guardrail_violation_count", -1)) == 0, "source_guardrail_violations"),
    ]
    return [reason for passed, reason in checks if not passed]


def _target_preflight_rows(preflight_rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in preflight_rows
        if str(row.get("candidate_group", "")) in TARGET_GROUPS
        and str(row.get("preflight_lane", "")) == "static_then_reset"
        and _bool(row.get("static_check_required"))
        and _bool(row.get("reset_check_required"))
        and _bool(row.get("concrete_overlay_required"))
        and _bool(row.get("concrete_overlay_available"))
        and bool(str(row.get("env_config_overlay_json", "")).strip())
        and not str(row.get("blocked_reason", "")).strip()
    ]


def _target_row_contract_failures(row: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if str(row.get("split", "")) not in ALLOWED_SPLITS:
        failures.append("split_not_public_debug_or_public_gate")
    expected_true = [
        "static_check_required",
        "reset_check_required",
        "concrete_overlay_required",
        "concrete_overlay_available",
    ]
    for key in expected_true:
        if not _bool(row.get(key)):
            failures.append(f"{key}_not_true")
    if str(row.get("preflight_lane", "")) != "static_then_reset":
        failures.append("preflight_lane_not_static_then_reset")
    if str(row.get("blocked_reason", "")).strip():
        failures.append("blocked_reason_not_empty")
    if not str(row.get("env_config_overlay_json", "")).strip():
        failures.append("missing_env_config_overlay_json")
    for key in FALSE_GUARD_KEYS:
        if _bool(row.get(key)):
            failures.append(f"{key}_true")
    return failures


def _overlay_contract_failures(
    *,
    preflight: Mapping[str, Any],
    overlay_row: Mapping[str, Any] | None,
    candidate_row: Mapping[str, Any] | None,
) -> tuple[list[str], dict[str, Any] | None]:
    failures: list[str] = []
    overlay: dict[str, Any] | None = None
    try:
        preflight_overlay = _parse_overlay(preflight.get("env_config_overlay_json", ""))
    except (json.JSONDecodeError, ValueError) as exc:
        failures.append(f"invalid_preflight_overlay_json:{exc}")
        preflight_overlay = None

    if overlay_row is None:
        failures.append("missing_overlay_join")
    else:
        try:
            overlay = _parse_overlay(overlay_row.get("env_config_overlay_json", ""))
        except (json.JSONDecodeError, ValueError) as exc:
            failures.append(f"invalid_overlay_json:{exc}")
        expected_family = _overlay_family_for_group(str(preflight.get("candidate_group", "")))
        if expected_family and str(overlay_row.get("overlay_family", "")) != expected_family:
            failures.append("overlay_family_mismatch")
        if not _bool(overlay_row.get("allowed_labels_metadata_only")):
            failures.append("allowed_labels_not_metadata_only")
        for key in FALSE_GUARD_KEYS:
            if _bool(overlay_row.get(key)):
                failures.append(f"overlay_{key}_true")

    if overlay is not None and preflight_overlay is not None and _canonical_json(overlay) != _canonical_json(preflight_overlay):
        failures.append("overlay_json_mismatch_preflight")

    if candidate_row is None:
        failures.append("missing_candidate_row")
    else:
        try:
            candidate_overlay = _parse_overlay(candidate_row.get("env_config_overlay_json", ""))
        except (json.JSONDecodeError, ValueError) as exc:
            failures.append(f"invalid_candidate_overlay_json:{exc}")
            candidate_overlay = None
        if overlay is not None and candidate_overlay is not None and _canonical_json(overlay) != _canonical_json(candidate_overlay):
            failures.append("overlay_json_mismatch_candidate")
        if str(candidate_row.get("candidate_group", "")) != str(preflight.get("candidate_group", "")):
            failures.append("candidate_group_mismatch")
        for key in FALSE_GUARD_KEYS:
            if _bool(candidate_row.get(key)):
                failures.append(f"candidate_{key}_true")

    if overlay is not None:
        unknown_keys = sorted(_flatten_overlay_keys(overlay) - ALLOWED_OVERLAY_KEYS)
        if unknown_keys:
            failures.append(f"unknown_overlay_keys:{'|'.join(unknown_keys)}")
        obstacle = overlay.get("obstacle")
        if not isinstance(obstacle, Mapping) or not _bool(obstacle.get("enabled")):
            failures.append("obstacle_not_enabled")
    return failures, overlay


def _base_contract_applied(effective_config: Mapping[str, Any]) -> bool:
    return (
        int(effective_config.get("history_length", -1)) == 1
        and str(effective_config.get("action_history_mode", "")) == "full"
        and not _bool(effective_config.get("include_privileged_params"), default=True)
        and str(effective_config.get("wheel_observation_mode", "")) == "none"
        and str(effective_config.get("obstacle_relative_velocity_mode", "")) == "zero"
    )


def _actor_contract_pass(effective_config: Mapping[str, Any]) -> bool:
    obstacle = effective_config.get("obstacle", {})
    return _base_contract_applied(effective_config) and isinstance(obstacle, Mapping) and _bool(obstacle.get("enabled"))


def _config_to_dict(config: Any, fallback: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return env_config_to_dict(config)
    except TypeError:
        data = getattr(config, "data", None)
        if isinstance(data, Mapping):
            return dict(data)
        return dict(fallback)


def _failure_type(reasons: Sequence[str], *, default: str = "contract_violation") -> str:
    joined = "|".join(reasons)
    if any(token in joined for token in ["source_", "missing_", "mismatch", "target_reset_count", "duplicate"]):
        return "lineage_invalid"
    if any(token in joined for token in ["observation", "non_finite", "obstacle_initialized"]):
        return "behavior_regression"
    if any(token in joined for token in ["reset", "sample", "environment_load"]):
        return "scenario_sampling_failure"
    return default


def _global_static_rows(
    *,
    source_admission_failures: Sequence[str],
    target_count: int,
    expected_target_count: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if source_admission_failures:
        rows.append(
            {
                "static_scope": "global",
                "reset_target_id": "global",
                "preflight_id": "global",
                "overlay_id": "",
                "source_candidate_id": "",
                "source_panel_id": "",
                "candidate_group": "",
                "split": "",
                "preflight_lane": "",
                "overlay_join_count": "",
                "candidate_row_present": "",
                "source_admission_pass": False,
                "target_row_contract_pass": "",
                "overlay_json_matches_preflight": "",
                "overlay_json_matches_candidate": "",
                "overlay_keys_allowed": "",
                "labels_metadata_only": "",
                "forbidden_execution_flags_clear": "",
                "static_validation_pass": False,
                "failure_type": "lineage_invalid",
                "failure_reasons": "|".join(source_admission_failures),
            }
        )
    if target_count != expected_target_count:
        rows.append(
            {
                "static_scope": "global",
                "reset_target_id": "global",
                "preflight_id": "global",
                "overlay_id": "",
                "source_candidate_id": "",
                "source_panel_id": "",
                "candidate_group": "",
                "split": "",
                "preflight_lane": "",
                "overlay_join_count": target_count,
                "candidate_row_present": "",
                "source_admission_pass": not source_admission_failures,
                "target_row_contract_pass": "",
                "overlay_json_matches_preflight": "",
                "overlay_json_matches_candidate": "",
                "overlay_keys_allowed": "",
                "labels_metadata_only": "",
                "forbidden_execution_flags_clear": "",
                "static_validation_pass": False,
                "failure_type": "lineage_invalid",
                "failure_reasons": f"target_reset_count_{target_count}_not_{expected_target_count}",
            }
        )
    return rows


def _claim_boundary_rows(result_class: str) -> list[dict[str, Any]]:
    reset_claim_value = "passed" if result_class == RESULT_PASS else "failed"
    return [
        {
            "claim_key": "concrete_overlay_reset_only_validation",
            "claim_value": reset_claim_value,
            "admissible": True,
            "reason": "M2464 may claim reset-only validation over the six concrete overlay rows.",
        },
        {"claim_key": "environment_step_or_policy_action", "claim_value": "false", "admissible": True, "reason": "M2464 stops after reset."},
        {"claim_key": "measured_rollout_started", "claim_value": "false", "admissible": True, "reason": "No rollout is run."},
        {"claim_key": "scenario_redesign_executed", "claim_value": "false", "admissible": True, "reason": "M2464 validates existing overlays only."},
        {"claim_key": "repair_training_started", "claim_value": "false", "admissible": True, "reason": "No repair or training is executed."},
        {"claim_key": "ranking_or_winner", "claim_value": "false", "admissible": True, "reason": "No ranking or winner is selected."},
        {
            "claim_key": "actual_success_improvement",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "Reset-only evidence is not measured controller performance.",
        },
        {
            "claim_key": "paper_or_self_id_verdict",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "No controller-family or history-necessity verdict is run.",
        },
        {
            "claim_key": "current_sim_verdict",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "M2464 is a reset preflight, not a current-sim verdict.",
        },
    ]


def _decision_rows(*, result_class: str, next_blocker: str) -> list[dict[str, Any]]:
    passed = result_class == RESULT_PASS
    return [
        {
            "decision_key": "reset_only_validation_complete",
            "decision_value": "true" if passed else "false",
            "admissible": True,
            "reason": "Reset-only validation artifacts were written.",
        },
        {
            "decision_key": "measured_validation_or_repair",
            "decision_value": "blocked_until_m2465_audit",
            "admissible": False,
            "reason": "M2465 must audit reset evidence before any measured route.",
        },
        {
            "decision_key": "repair_training_ranking_or_winner_selection",
            "decision_value": "false",
            "admissible": True,
            "reason": "No repair, training, ranking, or winner selection is executed.",
        },
        {
            "decision_key": "next_route",
            "decision_value": next_blocker,
            "admissible": True,
            "reason": "Route both pass and fail outcomes to result audit.",
        },
    ]


def _guardrail_rows(
    *,
    target_reset_count: int,
    expected_target_count: int,
    source_admission_failure_count: int,
    static_validation_failure_count: int,
    effective_env_config_written_count: int,
    effective_env_config_outside_run_dir_count: int,
    environment_load_attempt_count: int,
    environment_reset_attempt_count: int,
    environment_reset_success_count: int,
    environment_reset_failure_count: int,
    observation_finite_count: int,
    observation_dimension_failure_count: int,
    obstacle_initialized_count: int,
    environment_step_count: int,
    policy_action_executed: bool,
    environment_rollout_started: bool,
    measured_rollout_started: bool,
    active_config_overwrite_count: int,
    repair_execution_started: bool,
    training_started: bool,
    replay_started: bool,
    ppo_used: bool,
    promoted: bool,
    private_holdout_used: bool,
    actor_input_contract_changed_count: int,
    ranking_admissible_count: int,
    winner_selected_count: int,
    paper_level_claim_made: bool,
    finite_window_vs_gru_conclusion_made: bool,
    level3_self_id_claim_made: bool,
    scenario_redesign_executed_claim_made: bool,
    training_repair_success_claim_made: bool,
    current_sim_verdict_claim_made: bool,
) -> list[dict[str, Any]]:
    specs = [
        (
            "m2464_source_admission_pass",
            "lineage",
            "m2461_summary",
            "lineage_invalid",
            "source_admission_failure_count",
            source_admission_failure_count,
            source_admission_failure_count != 0,
            "M2464 requires a passing M2461 source with no prior reset execution.",
        ),
        (
            "m2464_exact_six_reset_targets",
            "target_selection",
            "adapter_preflight_work_items",
            "lineage_invalid",
            "target_reset_count",
            target_reset_count,
            target_reset_count != expected_target_count,
            "Exactly six stable/AES concrete-overlay reset targets must be admitted.",
        ),
        (
            "m2464_static_validation_clean",
            "static_validation",
            "static_validation_rows",
            "contract_violation",
            "static_validation_failure_count",
            static_validation_failure_count,
            static_validation_failure_count != 0,
            "Static validation must pass before environment loading.",
        ),
        (
            "m2464_effective_configs_bounded",
            "effective_config",
            "effective_env_config_rows",
            "lineage_invalid",
            "effective_env_config_outside_run_dir_count",
            effective_env_config_outside_run_dir_count,
            effective_env_config_outside_run_dir_count != 0,
            "Effective env config files must stay under the M2464 run directory.",
        ),
        (
            "m2464_effective_config_count",
            "effective_config",
            "effective_env_config_rows",
            "lineage_invalid",
            "effective_env_config_written_count",
            effective_env_config_written_count,
            effective_env_config_written_count != expected_target_count,
            "One effective env config must be written for each admitted reset target.",
        ),
        (
            "m2464_environment_load_attempt_count",
            "reset",
            "reset_validation_rows",
            "scenario_sampling_failure",
            "environment_load_attempt_count",
            environment_load_attempt_count,
            environment_load_attempt_count != expected_target_count,
            "Each target must attempt environment load only after static/effective validation passes.",
        ),
        (
            "m2464_environment_reset_attempt_count",
            "reset",
            "reset_validation_rows",
            "scenario_sampling_failure",
            "environment_reset_attempt_count",
            environment_reset_attempt_count,
            environment_reset_attempt_count != expected_target_count,
            "Each target must attempt reset exactly once.",
        ),
        (
            "m2464_environment_reset_success_count",
            "reset",
            "reset_validation_rows",
            "scenario_sampling_failure",
            "environment_reset_success_count",
            environment_reset_success_count,
            environment_reset_success_count != expected_target_count or environment_reset_failure_count != 0,
            "Every target reset must succeed without repair inside M2464.",
        ),
        (
            "m2464_observation_finite",
            "reset",
            "reset_validation_rows",
            "behavior_regression",
            "observation_finite_count",
            observation_finite_count,
            environment_reset_success_count == expected_target_count and observation_finite_count != expected_target_count,
            "Every successful reset observation must be finite.",
        ),
        (
            "m2464_observation_dimension_expected",
            "actor_contract",
            "reset_validation_rows",
            "contract_violation",
            "observation_dimension_failure_count",
            observation_dimension_failure_count,
            environment_reset_success_count == expected_target_count and observation_dimension_failure_count != 0,
            "Successful reset observation length must match the expected human-view dimension.",
        ),
        (
            "m2464_obstacle_initialized",
            "scenario_sampling",
            "reset_validation_rows",
            "behavior_regression",
            "obstacle_initialized_count",
            obstacle_initialized_count,
            environment_reset_success_count == expected_target_count and obstacle_initialized_count != expected_target_count,
            "Every successful reset must initialize an obstacle scenario.",
        ),
        (
            "m2464_no_environment_steps",
            "execution_boundary",
            "reset_validation_rows",
            "contract_violation",
            "environment_step_count",
            environment_step_count,
            environment_step_count != 0,
            "M2464 must not step the environment.",
        ),
        (
            "m2464_no_policy_or_rollout",
            "execution_boundary",
            "summary",
            "contract_violation",
            "policy_or_rollout",
            int(policy_action_executed or environment_rollout_started or measured_rollout_started),
            policy_action_executed or environment_rollout_started or measured_rollout_started,
            "M2464 must not execute policy actions or rollouts.",
        ),
        (
            "m2464_no_active_config_overwrite",
            "execution_boundary",
            "summary",
            "lineage_invalid",
            "active_config_overwrite_count",
            active_config_overwrite_count,
            active_config_overwrite_count != 0,
            "M2464 must not overwrite active scenario configs.",
        ),
        (
            "m2464_no_repair_training_replay_promotion",
            "execution_boundary",
            "summary",
            "contract_violation",
            "repair_training_replay_promotion",
            int(repair_execution_started or training_started or replay_started or ppo_used or promoted),
            repair_execution_started or training_started or replay_started or ppo_used or promoted,
            "M2464 must not run repair, training, replay, PPO, or promotion.",
        ),
        (
            "m2464_no_private_holdout",
            "execution_boundary",
            "summary",
            "contract_violation",
            "private_holdout_used",
            private_holdout_used,
            private_holdout_used,
            "M2464 does not use private holdout data.",
        ),
        (
            "m2464_actor_input_contract_clear",
            "actor_contract",
            "static_validation_rows",
            "contract_violation",
            "actor_input_contract_changed_count",
            actor_input_contract_changed_count,
            actor_input_contract_changed_count != 0,
            "Labels and actor-input contract flags must remain outside actor input.",
        ),
        (
            "m2464_no_ranking_or_winner",
            "claim_boundary",
            "summary",
            "metric_artifact",
            "ranking_or_winner_count",
            ranking_admissible_count + winner_selected_count,
            ranking_admissible_count != 0 or winner_selected_count != 0,
            "M2464 must not rank candidates or select winners.",
        ),
        (
            "m2464_no_verdict_claims",
            "claim_boundary",
            "summary",
            "metric_artifact",
            "verdict_claims",
            int(
                paper_level_claim_made
                or finite_window_vs_gru_conclusion_made
                or level3_self_id_claim_made
                or scenario_redesign_executed_claim_made
                or training_repair_success_claim_made
                or current_sim_verdict_claim_made
            ),
            (
                paper_level_claim_made
                or finite_window_vs_gru_conclusion_made
                or level3_self_id_claim_made
                or scenario_redesign_executed_claim_made
                or training_repair_success_claim_made
                or current_sim_verdict_claim_made
            ),
            "M2464 may not claim paper, self-ID, scenario-redesign, training-repair, or current-sim verdicts.",
        ),
    ]
    return [
        {
            "guardrail_id": guardrail_id,
            "guardrail_class": guardrail_class,
            "source_role_or_axis": source_role_or_axis,
            "failure_mode_to_preserve": failure_mode,
            "metric_to_watch": metric,
            "value": value,
            "violation": bool(violation),
            "reason": reason,
        }
        for guardrail_id, guardrail_class, source_role_or_axis, failure_mode, metric, value, violation, reason in specs
    ]


def run_concrete_overlay_reset_validation(
    *,
    m2461_dir: Path | str = DEFAULT_M2461_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_reset_count: int = DEFAULT_TARGET_RESET_COUNT,
    expected_observation_dim: int = DEFAULT_EXPECTED_OBSERVATION_DIM,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_dir = Path(m2461_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    effective_dir = output / "effective_env_configs"
    effective_dir.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(source_dir / "summary.json")
    overlay_rows = read_csv_rows(source_dir / "concrete_overlay_rows.csv")
    candidate_rows = read_csv_rows(source_dir / "candidate_rows_with_overlays.csv")
    preflight_rows = read_csv_rows(source_dir / "adapter_preflight_work_items.csv")
    adapter_reset_rows = read_csv_rows(source_dir / "adapter_reset_check_rows.csv")

    source_failures = _source_admission_failures(source_summary)
    targets = _target_preflight_rows(preflight_rows)
    overlays_by_join: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for row in overlay_rows:
        key = (
            str(row.get("preflight_id", "")),
            str(row.get("source_candidate_id", "")),
            str(row.get("candidate_group", "")),
        )
        overlays_by_join.setdefault(key, []).append(row)
    candidates_by_id = {str(row.get("candidate_id", "")): row for row in candidate_rows}

    static_rows = _global_static_rows(
        source_admission_failures=source_failures,
        target_count=len(targets),
        expected_target_count=target_reset_count,
    )
    reset_target_rows: list[dict[str, Any]] = []
    target_overlays: dict[str, dict[str, Any]] = {}
    target_preflight_by_id: dict[str, Mapping[str, Any]] = {}
    target_overlay_row_by_id: dict[str, Mapping[str, Any]] = {}

    for index, preflight in enumerate(targets, start=1):
        reset_target_id = f"m2464_reset_target_{index:03d}"
        preflight_id = str(preflight.get("preflight_id", ""))
        source_candidate_id = str(preflight.get("source_candidate_id", ""))
        candidate_group = str(preflight.get("candidate_group", ""))
        join_key = (preflight_id, source_candidate_id, candidate_group)
        joined_overlays = overlays_by_join.get(join_key, [])
        overlay_row = joined_overlays[0] if len(joined_overlays) == 1 else None
        candidate_row = candidates_by_id.get(source_candidate_id)
        row_failures = _target_row_contract_failures(preflight)
        overlay_failures, overlay = _overlay_contract_failures(
            preflight=preflight,
            overlay_row=overlay_row,
            candidate_row=candidate_row,
        )
        row_failures.extend(overlay_failures)
        if len(joined_overlays) != 1:
            row_failures.append(f"overlay_join_count_{len(joined_overlays)}")
        source_admission_pass = not source_failures
        target_row_contract_pass = not _target_row_contract_failures(preflight)
        try:
            preflight_overlay_for_compare = _parse_overlay(preflight.get("env_config_overlay_json", ""))
        except (json.JSONDecodeError, ValueError):
            preflight_overlay_for_compare = None
        overlay_json_matches_preflight = (
            overlay is not None
            and overlay_row is not None
            and preflight_overlay_for_compare is not None
            and _canonical_json(overlay) == _canonical_json(preflight_overlay_for_compare)
        )
        overlay_json_matches_candidate = False
        if overlay is not None and candidate_row is not None:
            try:
                candidate_overlay_for_compare = _parse_overlay(candidate_row.get("env_config_overlay_json", ""))
            except (json.JSONDecodeError, ValueError):
                candidate_overlay_for_compare = None
            overlay_json_matches_candidate = (
                candidate_overlay_for_compare is not None
                and _canonical_json(overlay) == _canonical_json(candidate_overlay_for_compare)
            )
        overlay_keys_allowed = overlay is not None and not (_flatten_overlay_keys(overlay) - ALLOWED_OVERLAY_KEYS)
        labels_metadata_only = bool(overlay_row is not None and _bool(overlay_row.get("allowed_labels_metadata_only")))
        forbidden_clear = not any(reason.endswith("_true") for reason in row_failures)
        static_pass = not row_failures
        overlay_id = str(overlay_row.get("overlay_id", "")) if overlay_row is not None else ""
        overlay_hash = _overlay_hash(overlay) if overlay is not None else ""
        effective_path = _effective_env_config_path(output, reset_target_id)

        static_rows.append(
            {
                "static_scope": "target",
                "reset_target_id": reset_target_id,
                "preflight_id": preflight_id,
                "overlay_id": overlay_id,
                "source_candidate_id": source_candidate_id,
                "source_panel_id": str(preflight.get("source_panel_id", "")),
                "candidate_group": candidate_group,
                "split": str(preflight.get("split", "")),
                "preflight_lane": str(preflight.get("preflight_lane", "")),
                "overlay_join_count": len(joined_overlays),
                "candidate_row_present": candidate_row is not None,
                "source_admission_pass": source_admission_pass,
                "target_row_contract_pass": target_row_contract_pass,
                "overlay_json_matches_preflight": overlay_json_matches_preflight,
                "overlay_json_matches_candidate": overlay_json_matches_candidate,
                "overlay_keys_allowed": overlay_keys_allowed,
                "labels_metadata_only": labels_metadata_only,
                "forbidden_execution_flags_clear": forbidden_clear,
                "static_validation_pass": static_pass,
                "failure_type": "" if static_pass else _failure_type(row_failures),
                "failure_reasons": "|".join(row_failures),
            }
        )
        reset_target_rows.append(
            {
                "reset_target_id": reset_target_id,
                "preflight_id": preflight_id,
                "overlay_id": overlay_id,
                "source_candidate_id": source_candidate_id,
                "source_panel_id": str(preflight.get("source_panel_id", "")),
                "candidate_group": candidate_group,
                "role_scope": str(preflight.get("role_scope", "")),
                "sampled_obstacle_label_scope": str(preflight.get("sampled_obstacle_label_scope", "")),
                "split": str(preflight.get("split", "")),
                "overlay_family": str(overlay_row.get("overlay_family", "")) if overlay_row is not None else "",
                "env_config_overlay_hash": overlay_hash,
                "effective_env_config_path": str(effective_path),
                "eval_seed": int(eval_seed_base) + index - 1,
                "expected_observation_dim": int(expected_observation_dim),
            }
        )
        if overlay is not None and overlay_row is not None:
            target_overlays[reset_target_id] = overlay
            target_preflight_by_id[reset_target_id] = preflight
            target_overlay_row_by_id[reset_target_id] = overlay_row

    static_validation_pass_count = sum(
        1 for row in static_rows if row.get("static_scope") == "target" and _bool(row.get("static_validation_pass"))
    )
    static_validation_failure_count = sum(not _bool(row.get("static_validation_pass")) for row in static_rows)
    static_clean = (
        not source_failures
        and len(targets) == target_reset_count
        and static_validation_pass_count == target_reset_count
        and static_validation_failure_count == 0
    )

    effective_rows: list[dict[str, Any]] = []
    effective_configs: dict[str, Any] = {}
    effective_config_dicts: dict[str, dict[str, Any]] = {}
    if static_clean:
        for target in reset_target_rows:
            reset_target_id = str(target["reset_target_id"])
            preflight = target_preflight_by_id[reset_target_id]
            overlay = target_overlays[reset_target_id]
            effective_path = Path(str(target["effective_env_config_path"]))
            inside_run_dir = _inside_dir(effective_path, output)
            merged_config = merge_env_config(dict(BASE_HUMAN_VIEW_CONTRACT_ENV_CONFIG), dict(overlay))
            failures: list[str] = []
            env_build_success = False
            config: Any | None = None
            effective_config: dict[str, Any] = dict(merged_config)
            try:
                config = build_env_config(merged_config)
                effective_config = _config_to_dict(config, merged_config)
                env_build_success = True
            except Exception as exc:  # noqa: BLE001 - artifact needs the exact fail-closed reason.
                failures.append(f"build_env_config_failed:{type(exc).__name__}:{exc}")
            base_contract_applied = _base_contract_applied(effective_config)
            actor_contract_guardrail_pass = _actor_contract_pass(effective_config)
            obstacle = effective_config.get("obstacle", {})
            obstacle_enabled = isinstance(obstacle, Mapping) and _bool(obstacle.get("enabled"))
            if not inside_run_dir:
                failures.append("effective_env_config_path_outside_run_dir")
            if not base_contract_applied:
                failures.append("base_human_view_contract_not_applied")
            if not actor_contract_guardrail_pass:
                failures.append("actor_contract_guardrail_failed")
            if not obstacle_enabled:
                failures.append("obstacle_not_enabled")
            effective_written = False
            if env_build_success and inside_run_dir and actor_contract_guardrail_pass:
                payload = {
                    "reset_target_id": reset_target_id,
                    "preflight_id": str(preflight.get("preflight_id", "")),
                    "overlay_id": str(target_overlay_row_by_id[reset_target_id].get("overlay_id", "")),
                    "source_candidate_id": str(preflight.get("source_candidate_id", "")),
                    "candidate_group": str(preflight.get("candidate_group", "")),
                    "base_human_view_contract_env_config": BASE_HUMAN_VIEW_CONTRACT_ENV_CONFIG,
                    "env_config_overlay": overlay,
                    "effective_env_config": effective_config,
                    "claim_boundary": {
                        "active_config_overwritten": False,
                        "environment_step_count": 0,
                        "policy_action_executed": False,
                        "environment_rollout_started": False,
                        "measured_rollout_started": False,
                        "repair_execution_started": False,
                        "training_started": False,
                        "ranking_admissible": False,
                        "winner_selected": False,
                    },
                }
                write_json(effective_path, payload)
                effective_written = True
                effective_configs[reset_target_id] = config
                effective_config_dicts[reset_target_id] = effective_config
            effective_rows.append(
                {
                    "reset_target_id": reset_target_id,
                    "preflight_id": str(preflight.get("preflight_id", "")),
                    "source_candidate_id": str(preflight.get("source_candidate_id", "")),
                    "candidate_group": str(preflight.get("candidate_group", "")),
                    "effective_env_config_path": str(effective_path),
                    "effective_env_config_written": effective_written,
                    "effective_env_config_inside_run_dir": inside_run_dir,
                    "base_contract_applied": base_contract_applied,
                    "actor_contract_guardrail_pass": actor_contract_guardrail_pass,
                    "obstacle_enabled": obstacle_enabled,
                    "env_build_success": env_build_success,
                    "failure_type": "" if not failures else _failure_type(failures),
                    "failure_reasons": "|".join(failures),
                }
            )

    effective_env_config_written_count = sum(_bool(row.get("effective_env_config_written")) for row in effective_rows)
    effective_env_config_outside_run_dir_count = sum(
        not _bool(row.get("effective_env_config_inside_run_dir")) for row in effective_rows
    )
    effective_clean = (
        static_clean
        and effective_env_config_written_count == target_reset_count
        and effective_env_config_outside_run_dir_count == 0
        and all(_bool(row.get("env_build_success")) and _bool(row.get("actor_contract_guardrail_pass")) for row in effective_rows)
    )

    reset_rows: list[dict[str, Any]] = []
    reset_failure_rows: list[dict[str, Any]] = []
    if effective_clean:
        for target in reset_target_rows:
            reset_target_id = str(target["reset_target_id"])
            failure_type = ""
            failure_reason = ""
            environment_load_attempted = False
            environment_reset_attempted = False
            environment_reset_success = False
            observation_length = 0
            observation_finite = False
            observation_dimension_matches_expected = False
            obstacle_initialized = False
            obstacle_label = ""
            environment_step_count = 0
            env: Any | None = None
            try:
                environment_load_attempted = True
                env = AutoDriftEnv(effective_configs[reset_target_id])
                environment_reset_attempted = True
                obs, info = env.reset(seed=int(target["eval_seed"]))
                environment_reset_success = True
                observation_length = _observation_length(obs)
                observation_finite = _finite_observation(obs)
                observation_dimension_matches_expected = observation_length == expected_observation_dim
                obstacle_scenario = getattr(env, "obstacle_scenario", None)
                obstacle_initialized = obstacle_scenario is not None
                obstacle_label = str(
                    getattr(obstacle_scenario, "label", "")
                    or (info.get("obstacle_label", "") if isinstance(info, Mapping) else "")
                )
                environment_step_count = int(getattr(env, "step_count", 0))
                failures: list[str] = []
                if not observation_finite:
                    failures.append("observation_non_finite")
                if not observation_dimension_matches_expected:
                    failures.append(
                        f"observation_length_{observation_length}_not_{expected_observation_dim}"
                    )
                if not obstacle_initialized:
                    failures.append("obstacle_initialized_false")
                if environment_step_count != 0:
                    failures.append("environment_step_count_nonzero")
                if failures:
                    environment_reset_success = False
                    failure_type = _failure_type(failures, default="behavior_regression")
                    failure_reason = "|".join(failures)
            except Exception as exc:  # noqa: BLE001 - reset failures are preserved as artifacts.
                failure_type = "scenario_sampling_failure"
                failure_reason = f"{type(exc).__name__}:{exc}"
            finally:
                close = getattr(env, "close", None)
                if callable(close):
                    close()

            row = {
                "reset_target_id": reset_target_id,
                "preflight_id": str(target["preflight_id"]),
                "source_candidate_id": str(target["source_candidate_id"]),
                "candidate_group": str(target["candidate_group"]),
                "role_scope": str(target["role_scope"]),
                "environment_load_attempted": environment_load_attempted,
                "environment_reset_attempted": environment_reset_attempted,
                "environment_reset_success": environment_reset_success,
                "observation_length": observation_length,
                "expected_observation_length": int(expected_observation_dim),
                "observation_dimension_matches_expected": observation_dimension_matches_expected,
                "observation_finite": observation_finite,
                "obstacle_initialized": obstacle_initialized,
                "obstacle_label": obstacle_label,
                "environment_step_count": environment_step_count,
                "policy_action_executed": False,
                "environment_rollout_started": False,
                "measured_rollout_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "replay_started": False,
                "ppo_used": False,
                "promoted": False,
                "private_holdout_used": False,
                "active_config_overwritten": False,
                "actor_input_contract_changed": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "finite_window_vs_gru_conclusion_made": False,
                "level3_self_id_claim_made": False,
                "scenario_redesign_executed_claim_made": False,
                "training_repair_success_claim_made": False,
                "current_sim_verdict_claim_made": False,
                "failure_type": failure_type,
                "failure_reason": failure_reason,
            }
            reset_rows.append(row)
            if failure_type or failure_reason:
                reset_failure_rows.append(
                    {
                        "reset_target_id": reset_target_id,
                        "preflight_id": str(target["preflight_id"]),
                        "source_candidate_id": str(target["source_candidate_id"]),
                        "candidate_group": str(target["candidate_group"]),
                        "failure_type": failure_type,
                        "failure_reason": failure_reason,
                    }
                )

    environment_load_attempt_count = sum(_bool(row.get("environment_load_attempted")) for row in reset_rows)
    environment_reset_attempt_count = sum(_bool(row.get("environment_reset_attempted")) for row in reset_rows)
    environment_reset_success_count = sum(_bool(row.get("environment_reset_success")) for row in reset_rows)
    environment_reset_failure_count = sum(
        _bool(row.get("environment_reset_attempted")) and not _bool(row.get("environment_reset_success"))
        for row in reset_rows
    )
    observation_finite_count = sum(_bool(row.get("observation_finite")) for row in reset_rows)
    observation_dimension_failure_count = sum(
        _bool(row.get("environment_reset_success"))
        and not _bool(row.get("observation_dimension_matches_expected"))
        for row in reset_rows
    )
    obstacle_initialized_count = sum(_bool(row.get("obstacle_initialized")) for row in reset_rows)
    environment_step_count = sum(int(row.get("environment_step_count", 0) or 0) for row in reset_rows)
    active_config_overwrite_count = sum(_bool(row.get("active_config_overwritten")) for row in reset_rows)
    actor_input_contract_changed_count = sum(
        _bool(row.get("actor_input_contract_changed"))
        for row in static_rows
        if row.get("static_scope") == "target"
    ) + sum(_bool(row.get("actor_input_contract_changed")) for row in reset_rows)
    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in reset_rows)
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in reset_rows)

    policy_action_executed = any(_bool(row.get("policy_action_executed")) for row in reset_rows)
    environment_rollout_started = any(_bool(row.get("environment_rollout_started")) for row in reset_rows)
    measured_rollout_started = any(_bool(row.get("measured_rollout_started")) for row in reset_rows)
    repair_execution_started = any(_bool(row.get("repair_execution_started")) for row in reset_rows)
    training_started = any(_bool(row.get("training_started")) for row in reset_rows)
    replay_started = any(_bool(row.get("replay_started")) for row in reset_rows)
    ppo_used = any(_bool(row.get("ppo_used")) for row in reset_rows)
    promoted = any(_bool(row.get("promoted")) for row in reset_rows)
    private_holdout_used = any(_bool(row.get("private_holdout_used")) for row in reset_rows)
    paper_level_claim_made = any(_bool(row.get("paper_level_claim_made")) for row in reset_rows)
    finite_window_vs_gru_conclusion_made = any(
        _bool(row.get("finite_window_vs_gru_conclusion_made")) for row in reset_rows
    )
    level3_self_id_claim_made = any(_bool(row.get("level3_self_id_claim_made")) for row in reset_rows)
    scenario_redesign_executed_claim_made = any(
        _bool(row.get("scenario_redesign_executed_claim_made")) for row in reset_rows
    )
    training_repair_success_claim_made = any(
        _bool(row.get("training_repair_success_claim_made")) for row in reset_rows
    )
    current_sim_verdict_claim_made = any(_bool(row.get("current_sim_verdict_claim_made")) for row in reset_rows)

    guards = _guardrail_rows(
        target_reset_count=len(reset_target_rows),
        expected_target_count=target_reset_count,
        source_admission_failure_count=len(source_failures),
        static_validation_failure_count=static_validation_failure_count,
        effective_env_config_written_count=effective_env_config_written_count,
        effective_env_config_outside_run_dir_count=effective_env_config_outside_run_dir_count,
        environment_load_attempt_count=environment_load_attempt_count,
        environment_reset_attempt_count=environment_reset_attempt_count,
        environment_reset_success_count=environment_reset_success_count,
        environment_reset_failure_count=environment_reset_failure_count,
        observation_finite_count=observation_finite_count,
        observation_dimension_failure_count=observation_dimension_failure_count,
        obstacle_initialized_count=obstacle_initialized_count,
        environment_step_count=environment_step_count,
        policy_action_executed=policy_action_executed,
        environment_rollout_started=environment_rollout_started,
        measured_rollout_started=measured_rollout_started,
        active_config_overwrite_count=active_config_overwrite_count,
        repair_execution_started=repair_execution_started,
        training_started=training_started,
        replay_started=replay_started,
        ppo_used=ppo_used,
        promoted=promoted,
        private_holdout_used=private_holdout_used,
        actor_input_contract_changed_count=actor_input_contract_changed_count,
        ranking_admissible_count=ranking_admissible_count,
        winner_selected_count=winner_selected_count,
        paper_level_claim_made=paper_level_claim_made,
        finite_window_vs_gru_conclusion_made=finite_window_vs_gru_conclusion_made,
        level3_self_id_claim_made=level3_self_id_claim_made,
        scenario_redesign_executed_claim_made=scenario_redesign_executed_claim_made,
        training_repair_success_claim_made=training_repair_success_claim_made,
        current_sim_verdict_claim_made=current_sim_verdict_claim_made,
    )
    guardrail_violation_count = sum(_bool(row.get("violation")) for row in guards)
    result_class = RESULT_PASS if guardrail_violation_count == 0 else RESULT_FAIL
    claims = _claim_boundary_rows(result_class)
    decisions = _decision_rows(result_class=result_class, next_blocker=next_blocker)

    failure_types = sorted(
        {
            str(row.get("failure_mode_to_preserve", ""))
            for row in guards
            if _bool(row.get("violation")) and str(row.get("failure_mode_to_preserve", ""))
        }
        | {str(row.get("failure_type", "")) for row in static_rows if str(row.get("failure_type", ""))}
        | {str(row.get("failure_type", "")) for row in effective_rows if str(row.get("failure_type", ""))}
        | {str(row.get("failure_type", "")) for row in reset_rows if str(row.get("failure_type", ""))}
    )
    if not failure_types and result_class == RESULT_FAIL:
        failure_types = ["scenario_sampling_failure"]

    write_csv_rows(output / "static_validation_rows.csv", static_rows, fieldnames=STATIC_VALIDATION_FIELDNAMES)
    write_csv_rows(output / "reset_target_rows.csv", reset_target_rows, fieldnames=RESET_TARGET_FIELDNAMES)
    write_csv_rows(output / "effective_env_config_rows.csv", effective_rows, fieldnames=EFFECTIVE_CONFIG_FIELDNAMES)
    write_csv_rows(output / "reset_validation_rows.csv", reset_rows, fieldnames=RESET_VALIDATION_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", reset_failure_rows, fieldnames=RESET_FAILURE_FIELDNAMES)
    write_csv_rows(output / "guardrail_rows.csv", guards, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decisions, fieldnames=DECISION_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_artifacts": {
            "m2461_summary": str(source_dir / "summary.json"),
            "concrete_overlay_rows": str(source_dir / "concrete_overlay_rows.csv"),
            "candidate_rows_with_overlays": str(source_dir / "candidate_rows_with_overlays.csv"),
            "adapter_preflight_work_items": str(source_dir / "adapter_preflight_work_items.csv"),
            "adapter_reset_check_rows": str(source_dir / "adapter_reset_check_rows.csv"),
        },
        "source_result_class": str(source_summary.get("result_class", "")),
        "source_admission_failure_count": len(source_failures),
        "source_admission_failures": list(source_failures),
        "source_concrete_overlay_row_count": len(overlay_rows),
        "source_candidate_row_count": len(candidate_rows),
        "source_preflight_work_item_count": len(preflight_rows),
        "source_adapter_reset_check_row_count": len(adapter_reset_rows),
        "target_reset_count": len(reset_target_rows),
        "expected_target_reset_count": int(target_reset_count),
        "expected_observation_dim": int(expected_observation_dim),
        "eval_seed_base": int(eval_seed_base),
        "target_candidate_group_counts": _count_by(reset_target_rows, "candidate_group"),
        "target_overlay_family_counts": _count_by(reset_target_rows, "overlay_family"),
        "static_validation_pass_count": static_validation_pass_count,
        "static_validation_failure_count": static_validation_failure_count,
        "effective_env_config_written_count": effective_env_config_written_count,
        "effective_env_config_outside_run_dir_count": effective_env_config_outside_run_dir_count,
        "environment_load_attempt_count": environment_load_attempt_count,
        "environment_reset_attempt_count": environment_reset_attempt_count,
        "environment_reset_success_count": environment_reset_success_count,
        "environment_reset_failure_count": environment_reset_failure_count,
        "observation_finite_count": observation_finite_count,
        "observation_dimension_failure_count": observation_dimension_failure_count,
        "obstacle_initialized_count": obstacle_initialized_count,
        "environment_step_count": environment_step_count,
        "policy_action_executed": policy_action_executed,
        "environment_rollout_started": environment_rollout_started,
        "measured_rollout_started": measured_rollout_started,
        "measured_policy_rollout_started": measured_rollout_started,
        "active_config_overwrite_count": active_config_overwrite_count,
        "repair_execution_started": repair_execution_started,
        "training_started": training_started,
        "replay_started": replay_started,
        "ppo_used": ppo_used,
        "promoted": promoted,
        "private_holdout_used": private_holdout_used,
        "actor_input_contract_changed_count": actor_input_contract_changed_count,
        "labels_enter_actor_input_count": sum(
            _bool(row.get("labels_enter_actor_input")) for row in preflight_rows if str(row.get("candidate_group", "")) in TARGET_GROUPS
        ),
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": paper_level_claim_made,
        "finite_window_vs_gru_conclusion_made": finite_window_vs_gru_conclusion_made,
        "level3_self_id_claim_made": level3_self_id_claim_made,
        "scenario_redesign_executed": False,
        "scenario_redesign_executed_claim_made": scenario_redesign_executed_claim_made,
        "training_repair_success_claim_made": training_repair_success_claim_made,
        "current_sim_verdict_claim_made": current_sim_verdict_claim_made,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "candidate_family_ranking_claim_made": False,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "static_validation_rows": str(output / "static_validation_rows.csv"),
            "reset_target_rows": str(output / "reset_target_rows.csv"),
            "effective_env_config_rows": str(output / "effective_env_config_rows.csv"),
            "reset_validation_rows": str(output / "reset_validation_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "guardrail_rows": str(output / "guardrail_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "decision_rows": str(output / "decision_rows.csv"),
            "effective_env_configs": str(effective_dir),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2461-dir", type=Path, default=DEFAULT_M2461_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-reset-count", type=int, default=DEFAULT_TARGET_RESET_COUNT)
    parser.add_argument("--expected-observation-dim", type=int, default=DEFAULT_EXPECTED_OBSERVATION_DIM)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_concrete_overlay_reset_validation(
        m2461_dir=args.m2461_dir,
        output_dir=args.output_dir,
        target_reset_count=args.target_reset_count,
        expected_observation_dim=args.expected_observation_dim,
        eval_seed_base=args.eval_seed_base,
        next_blocker=args.next_blocker,
    )
    print(f"summary: {summary['artifacts']['summary']}")
    print(f"result_class: {summary['result_class']}")
    print(f"target_reset_count: {summary['target_reset_count']}")
    print(f"static_validation_pass_count: {summary['static_validation_pass_count']}")
    print(f"environment_reset_attempt_count: {summary['environment_reset_attempt_count']}")
    print(f"environment_reset_success_count: {summary['environment_reset_success_count']}")
    print(f"guardrail_violation_count: {summary['guardrail_violation_count']}")
    print(f"next_blocker: {summary['next_blocker']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
