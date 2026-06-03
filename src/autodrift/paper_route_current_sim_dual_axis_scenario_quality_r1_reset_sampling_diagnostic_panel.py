"""Reset-only diagnostic panel for R1 stable-AES scenario sampling."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.env import AutoDriftEnv


DEFAULT_M2464_DIR = Path(
    "runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2466_paper_route_current_sim_dual_axis_scenario_quality_r1_reset_sampling_diagnostic_panel"
)
DEFAULT_TARGET_OVERLAY_FAMILY = "R1_aeb_infeasible_stable_aes"
DEFAULT_EVAL_SEED_BASE = 246600
DEFAULT_RESET_SEED_COUNT = 24
DEFAULT_EXPECTED_OBSERVATION_DIM = 72
DEFAULT_NEXT_BLOCKER = (
    "m2467-paper-route-current-sim-dual-axis-scenario-quality-r1-reset-sampling-diagnostic-panel-result-audit"
)

RESULT_COMPLETE = "scenario_quality_r1_reset_sampling_diagnostic_panel_complete"
RESULT_FAIL = "scenario_quality_r1_reset_sampling_diagnostic_panel_fail"

FALSE_SUMMARY_FLAGS = [
    "policy_action_executed",
    "environment_rollout_started",
    "measured_rollout_started",
    "repair_execution_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed_claim_made",
    "training_repair_success_claim_made",
    "current_sim_verdict_claim_made",
]

RANDOMIZATION_NOMINAL = {
    "mu_range": [0.9, 0.9],
    "mass_scale_range": [1.0, 1.0],
    "cg_shift_range": [0.0, 0.0],
    "inertia_scale_range": [1.0, 1.0],
    "tire_stiffness_scale_range": [1.0, 1.0],
    "drive_scale_range": [1.0, 1.0],
    "brake_scale_range": [1.0, 1.0],
    "actuator_tau_scale_range": [1.0, 1.0],
}

DIAGNOSTIC_ROW_FIELDNAMES = [
    "variant_id",
    "variant_class",
    "diagnostic_only",
    "reset_attempt_id",
    "reset_seed_index",
    "eval_seed",
    "target_overlay_family",
    "source_overlay_hash",
    "source_reset_target_ids",
    "source_candidate_ids",
    "effective_env_config_path",
    "environment_load_attempted",
    "environment_reset_attempted",
    "reset_success",
    "observation_length",
    "expected_observation_length",
    "observation_dimension_matches_expected",
    "observation_finite",
    "obstacle_initialized",
    "obstacle_label",
    "initial_mu",
    "mu",
    "mass_scale",
    "tire_stiffness_scale",
    "brake_scale",
    "steer_tau_scale",
    "drive_tau_scale",
    "speed_ref",
    "obstacle_distance",
    "obstacle_lateral_offset",
    "obstacle_half_width",
    "obstacle_threshold_score",
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

VARIANT_FIELDNAMES = [
    "variant_id",
    "variant_class",
    "diagnostic_only",
    "source_variant_id",
    "effective_env_config_path",
    "mutation_summary",
    "actor_contract_guardrail_pass",
    "active_config_overwritten",
    "repair_candidate",
    "ranking_admissible",
    "winner_selected",
    "promoted",
]

VARIANT_SUMMARY_FIELDNAMES = [
    "variant_id",
    "variant_class",
    "diagnostic_only",
    "reset_attempt_count",
    "reset_success_count",
    "reset_failure_count",
    "reset_success_rate",
    "observation_dimension_failure_count",
    "obstacle_initialized_count",
    "failure_type_counts",
    "obstacle_label_counts",
]

CLASSIFICATION_FIELDNAMES = ["classification_key", "classification_value", "admissible", "reason"]
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


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def _as_float(value: Any) -> float | str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return number if np.isfinite(number) else ""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _json_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _config_to_dict(config: Any, fallback: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return env_config_to_dict(config)
    except TypeError:
        data = getattr(config, "data", None)
        if isinstance(data, Mapping):
            return dict(data)
        return dict(fallback)


def _actor_contract_guardrail_pass(config: Mapping[str, Any]) -> bool:
    obstacle = config.get("obstacle", {})
    return (
        int(config.get("history_length", -1)) == 1
        and str(config.get("action_history_mode", "")) == "full"
        and not _bool(config.get("include_privileged_params"), default=True)
        and str(config.get("wheel_observation_mode", "")) == "none"
        and str(config.get("obstacle_relative_velocity_mode", "")) == "zero"
        and isinstance(obstacle, Mapping)
        and _bool(obstacle.get("enabled"))
    )


def _inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _resolve_source_path(source_dir: Path, path_value: Any) -> Path:
    raw = Path(str(path_value))
    if raw.is_absolute() or raw.exists():
        return raw
    candidate = source_dir / raw
    if candidate.exists():
        return candidate
    return raw


def _effective_config_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    config = payload.get("effective_env_config", {})
    return dict(config) if isinstance(config, Mapping) else {}


def _load_r1_sources(m2464_dir: Path, target_overlay_family: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    target_rows = read_csv_rows(m2464_dir / "reset_target_rows.csv")
    r1_rows = [row for row in target_rows if str(row.get("overlay_family", "")) == str(target_overlay_family)]
    configs: dict[str, Any] = {}
    for row in r1_rows:
        path = _resolve_source_path(m2464_dir, row.get("effective_env_config_path", ""))
        configs[str(row.get("reset_target_id", ""))] = read_json(path)
    return r1_rows, configs


def _variant_specs(baseline_config: Mapping[str, Any]) -> list[dict[str, Any]]:
    baseline = deepcopy(dict(baseline_config))

    nominal_hidden = deepcopy(baseline)
    nominal_hidden["randomization"] = deepcopy(RANDOMIZATION_NOMINAL)

    threshold_relaxed = deepcopy(baseline)
    threshold_relaxed.setdefault("obstacle", {})
    threshold_relaxed["obstacle"]["max_threshold_score"] = None

    geometry_wider = deepcopy(baseline)
    geometry_wider.setdefault("obstacle", {})
    geometry_wider["obstacle"]["distance_range"] = [18.0, 38.0]
    geometry_wider["obstacle"]["lateral_offset_range"] = [-0.60, 0.60]
    geometry_wider["obstacle"]["half_width_range"] = [0.45, 0.85]

    threshold_geometry_relaxed = deepcopy(geometry_wider)
    threshold_geometry_relaxed["obstacle"]["max_threshold_score"] = None

    return [
        {
            "variant_id": "baseline_r1_original",
            "variant_class": "baseline",
            "config": baseline,
            "mutation_summary": "M2464 R1 effective config unchanged",
            "source_variant_id": "",
        },
        {
            "variant_id": "nominal_hidden_dynamics",
            "variant_class": "hidden_dynamics_randomization_diagnostic",
            "config": nominal_hidden,
            "mutation_summary": "collapse hidden dynamics randomization ranges to nominal deterministic values",
            "source_variant_id": "baseline_r1_original",
        },
        {
            "variant_id": "threshold_relaxed",
            "variant_class": "threshold_strictness_diagnostic",
            "config": threshold_relaxed,
            "mutation_summary": "set obstacle.max_threshold_score to null for diagnostic sampling only",
            "source_variant_id": "baseline_r1_original",
        },
        {
            "variant_id": "geometry_wider_same_threshold",
            "variant_class": "geometry_range_fragility_diagnostic",
            "config": geometry_wider,
            "mutation_summary": "widen R1 obstacle distance/lateral/half-width sampling ranges while preserving threshold",
            "source_variant_id": "baseline_r1_original",
        },
        {
            "variant_id": "threshold_and_geometry_relaxed",
            "variant_class": "coupled_threshold_geometry_diagnostic",
            "config": threshold_geometry_relaxed,
            "mutation_summary": "widen R1 geometry ranges and remove max_threshold_score for diagnostic sampling only",
            "source_variant_id": "baseline_r1_original",
        },
    ]


def _write_variant_config(
    *,
    output_dir: Path,
    variant: Mapping[str, Any],
    source_rows: Sequence[Mapping[str, Any]],
    source_overlay_hash: str,
    effective_config: Mapping[str, Any],
) -> Path:
    path = output_dir / "diagnostic_env_configs" / f"{variant['variant_id']}.json"
    write_json(
        path,
        {
            "variant_id": str(variant["variant_id"]),
            "variant_class": str(variant["variant_class"]),
            "diagnostic_only": True,
            "repair_candidate": False,
            "ranking_admissible": False,
            "winner_selected": False,
            "promoted": False,
            "source_overlay_hash": source_overlay_hash,
            "source_reset_target_ids": [str(row.get("reset_target_id", "")) for row in source_rows],
            "source_candidate_ids": [str(row.get("source_candidate_id", "")) for row in source_rows],
            "mutation_summary": str(variant["mutation_summary"]),
            "effective_env_config": dict(effective_config),
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
        },
    )
    return path


def _reset_row(
    *,
    variant: Mapping[str, Any],
    config: Any,
    effective_config_path: Path,
    eval_seed: int,
    reset_seed_index: int,
    expected_observation_dim: int,
    target_overlay_family: str,
    source_overlay_hash: str,
    source_reset_target_ids: str,
    source_candidate_ids: str,
) -> dict[str, Any]:
    failure_type = ""
    failure_reason = ""
    environment_load_attempted = False
    environment_reset_attempted = False
    reset_success = False
    observation_length = 0
    observation_finite = False
    dimension_matches = False
    obstacle_initialized = False
    obstacle_label = ""
    environment_step_count = 0
    info: Mapping[str, Any] = {}
    env: Any | None = None
    try:
        environment_load_attempted = True
        env = AutoDriftEnv(config)
        environment_reset_attempted = True
        obs, reset_info = env.reset(seed=int(eval_seed))
        info = reset_info if isinstance(reset_info, Mapping) else {}
        observation_length = _observation_length(obs)
        observation_finite = _finite_observation(obs)
        dimension_matches = observation_length == int(expected_observation_dim)
        obstacle_scenario = getattr(env, "obstacle_scenario", None)
        obstacle_initialized = obstacle_scenario is not None
        obstacle_label = str(getattr(obstacle_scenario, "label", "") or info.get("obstacle_label", ""))
        environment_step_count = int(getattr(env, "step_count", 0))
        failures: list[str] = []
        if not observation_finite:
            failures.append("observation_non_finite")
        if not dimension_matches:
            failures.append(f"observation_length_{observation_length}_not_{expected_observation_dim}")
        if not obstacle_initialized:
            failures.append("obstacle_initialized_false")
        if environment_step_count != 0:
            failures.append("environment_step_count_nonzero")
        if failures:
            failure_type = "behavior_regression"
            failure_reason = "|".join(failures)
        else:
            reset_success = True
    except Exception as exc:  # noqa: BLE001 - reset diagnostics preserve exact exception text.
        failure_type = "scenario_sampling_failure"
        failure_reason = f"{type(exc).__name__}:{exc}"
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()

    return {
        "variant_id": str(variant["variant_id"]),
        "variant_class": str(variant["variant_class"]),
        "diagnostic_only": True,
        "reset_attempt_id": f"{variant['variant_id']}_seed_{reset_seed_index:03d}",
        "reset_seed_index": int(reset_seed_index),
        "eval_seed": int(eval_seed),
        "target_overlay_family": str(target_overlay_family),
        "source_overlay_hash": str(source_overlay_hash),
        "source_reset_target_ids": source_reset_target_ids,
        "source_candidate_ids": source_candidate_ids,
        "effective_env_config_path": str(effective_config_path),
        "environment_load_attempted": environment_load_attempted,
        "environment_reset_attempted": environment_reset_attempted,
        "reset_success": reset_success,
        "observation_length": observation_length,
        "expected_observation_length": int(expected_observation_dim),
        "observation_dimension_matches_expected": dimension_matches,
        "observation_finite": observation_finite,
        "obstacle_initialized": obstacle_initialized,
        "obstacle_label": obstacle_label,
        "initial_mu": _as_float(info.get("initial_mu")),
        "mu": _as_float(info.get("mu", info.get("initial_mu"))),
        "mass_scale": _as_float(info.get("mass_scale")),
        "tire_stiffness_scale": _as_float(info.get("tire_stiffness_scale")),
        "brake_scale": _as_float(info.get("brake_scale")),
        "steer_tau_scale": _as_float(info.get("steer_tau_scale")),
        "drive_tau_scale": _as_float(info.get("drive_tau_scale")),
        "speed_ref": _as_float(info.get("speed_ref")),
        "obstacle_distance": _as_float(info.get("obstacle_distance")),
        "obstacle_lateral_offset": _as_float(info.get("obstacle_lateral_offset")),
        "obstacle_half_width": _as_float(info.get("active_obstacle_half_width")),
        "obstacle_threshold_score": _as_float(info.get("obstacle_threshold_score")),
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


def _variant_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for variant_id in sorted({str(row.get("variant_id", "")) for row in rows}):
        variant_rows = [row for row in rows if str(row.get("variant_id", "")) == variant_id]
        success_count = sum(_bool(row.get("reset_success")) for row in variant_rows)
        attempt_count = len(variant_rows)
        summaries.append(
            {
                "variant_id": variant_id,
                "variant_class": str(variant_rows[0].get("variant_class", "")) if variant_rows else "",
                "diagnostic_only": True,
                "reset_attempt_count": attempt_count,
                "reset_success_count": success_count,
                "reset_failure_count": attempt_count - success_count,
                "reset_success_rate": success_count / attempt_count if attempt_count else 0.0,
                "observation_dimension_failure_count": sum(
                    _bool(row.get("reset_success")) and not _bool(row.get("observation_dimension_matches_expected"))
                    for row in variant_rows
                ),
                "obstacle_initialized_count": sum(_bool(row.get("obstacle_initialized")) for row in variant_rows),
                "failure_type_counts": dict(_count_by([row for row in variant_rows if str(row.get("failure_type", ""))], "failure_type")),
                "obstacle_label_counts": dict(_count_by([row for row in variant_rows if str(row.get("obstacle_label", ""))], "obstacle_label")),
            }
        )
    return summaries


def _rate_by_variant(summary_rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    return {str(row.get("variant_id", "")): float(row.get("reset_success_rate", 0.0) or 0.0) for row in summary_rows}


def _classification_rows(summary_rows: Sequence[Mapping[str, Any]], *, complete: bool) -> tuple[str, list[dict[str, Any]]]:
    rates = _rate_by_variant(summary_rows)
    baseline = rates.get("baseline_r1_original", 0.0)
    nominal = rates.get("nominal_hidden_dynamics", 0.0)
    threshold = rates.get("threshold_relaxed", 0.0)
    geometry = rates.get("geometry_wider_same_threshold", 0.0)
    coupled = rates.get("threshold_and_geometry_relaxed", 0.0)
    rows: list[dict[str, Any]] = []

    def add(key: str, value: str, admissible: bool, reason: str) -> None:
        rows.append({"classification_key": key, "classification_value": value, "admissible": admissible, "reason": reason})

    if not complete:
        add("panel_complete", "false", False, "diagnostic panel did not satisfy source or execution guardrails")
        return "diagnostic_incomplete", rows

    if baseline >= 1.0:
        add("baseline_blocker_reproduced", "false", True, "baseline R1 reset success rate is 1.0 across the diagnostic seed panel")
        return "no_blocker_reproduced", rows
    if baseline <= 0.0 and max(nominal, threshold, geometry, coupled) <= 0.0:
        add("broad_scenario_spec_incompatibility", "true", True, "all baseline and diagnostic-only variants failed reset sampling")
        return "broader_scenario_spec_incompatibility", rows

    signals: list[str] = []
    if 0.0 < baseline < 1.0:
        signals.append("seed_fragility")
        add("seed_fragility", "true", True, "baseline R1 reset success rate is partial across the diagnostic seed panel")
    if nominal - baseline >= 0.25:
        signals.append("hidden_dynamics_randomization_fragility")
        add(
            "hidden_dynamics_randomization_fragility",
            "true",
            True,
            "nominal hidden-dynamics diagnostic improves reset success rate by at least 0.25 over baseline",
        )
    if threshold - baseline >= 0.25:
        signals.append("threshold_strictness_signal")
        add(
            "threshold_strictness_signal",
            "true",
            True,
            "relaxing obstacle.max_threshold_score improves reset success rate by at least 0.25 over baseline",
        )
    if geometry - baseline >= 0.25:
        signals.append("geometry_range_fragility_signal")
        add(
            "geometry_range_fragility_signal",
            "true",
            True,
            "widening obstacle geometry ranges improves reset success rate by at least 0.25 over baseline",
        )
    if coupled - max(baseline, threshold, geometry) >= 0.25:
        signals.append("coupled_threshold_geometry_fragility")
        add(
            "coupled_threshold_geometry_fragility",
            "true",
            True,
            "combined threshold and geometry relaxation improves beyond individual diagnostics",
        )
    if not signals:
        signals.append("mixed_or_inconclusive")
        add("mixed_or_inconclusive", "true", True, "diagnostic variants did not isolate a dominant failure mode")
    return "|".join(signals), rows


def _guardrail_rows(
    *,
    source_admission_failure_count: int,
    r1_target_count: int,
    source_overlay_hash_count: int,
    source_unique_effective_config_count: int,
    variant_count: int,
    expected_variant_count: int,
    diagnostic_attempt_count: int,
    expected_attempt_count: int,
    actor_contract_failure_count: int,
    active_config_overwrite_count: int,
    environment_step_count: int,
    policy_action_executed: bool,
    environment_rollout_started: bool,
    measured_rollout_started: bool,
    repair_execution_started: bool,
    training_started: bool,
    replay_started: bool,
    ppo_used: bool,
    promoted: bool,
    private_holdout_used: bool,
    ranking_admissible_count: int,
    winner_selected_count: int,
    verdict_claim_count: int,
) -> list[dict[str, Any]]:
    specs = [
        (
            "m2466_source_admission",
            "lineage",
            "m2464_summary",
            "lineage_invalid",
            "source_admission_failure_count",
            source_admission_failure_count,
            source_admission_failure_count != 0,
            "M2466 requires the M2464 reset-only failure artifact as parent evidence.",
        ),
        (
            "m2466_r1_target_count",
            "target_selection",
            "m2464_reset_target_rows",
            "lineage_invalid",
            "r1_target_count",
            r1_target_count,
            r1_target_count != 3,
            "M2466 diagnoses exactly the three M2464 R1 stable-AES targets.",
        ),
        (
            "m2466_single_r1_overlay_hash",
            "target_selection",
            "m2464_reset_target_rows",
            "lineage_invalid",
            "source_overlay_hash_count",
            source_overlay_hash_count,
            source_overlay_hash_count != 1,
            "The three R1 targets must share one source overlay hash for a family-level diagnostic.",
        ),
        (
            "m2466_single_r1_effective_config",
            "target_selection",
            "m2464_effective_env_configs",
            "lineage_invalid",
            "source_unique_effective_config_count",
            source_unique_effective_config_count,
            source_unique_effective_config_count != 1,
            "The three R1 targets must share one effective env config before family-level diagnostics.",
        ),
        (
            "m2466_variant_count",
            "diagnostic_design",
            "variant_rows",
            "lineage_invalid",
            "variant_count",
            variant_count,
            variant_count != expected_variant_count,
            "M2466 expects the baseline plus four diagnostic-only variants.",
        ),
        (
            "m2466_diagnostic_attempt_count",
            "diagnostic_execution",
            "diagnostic_rows",
            "lineage_invalid",
            "diagnostic_attempt_count",
            diagnostic_attempt_count,
            diagnostic_attempt_count != expected_attempt_count,
            "Every diagnostic variant must run the requested reset seed panel.",
        ),
        (
            "m2466_actor_contract_clear",
            "actor_contract",
            "diagnostic_env_configs",
            "contract_violation",
            "actor_contract_failure_count",
            actor_contract_failure_count,
            actor_contract_failure_count != 0,
            "All diagnostic variants must preserve the P0 human-view actor contract.",
        ),
        (
            "m2466_no_active_config_overwrite",
            "execution_boundary",
            "variant_rows",
            "lineage_invalid",
            "active_config_overwrite_count",
            active_config_overwrite_count,
            active_config_overwrite_count != 0,
            "M2466 must write only run-dir diagnostic configs.",
        ),
        (
            "m2466_no_environment_steps",
            "execution_boundary",
            "diagnostic_rows",
            "contract_violation",
            "environment_step_count",
            environment_step_count,
            environment_step_count != 0,
            "M2466 must stop after reset.",
        ),
        (
            "m2466_no_policy_or_rollout",
            "execution_boundary",
            "diagnostic_rows",
            "contract_violation",
            "policy_or_rollout",
            int(policy_action_executed or environment_rollout_started or measured_rollout_started),
            policy_action_executed or environment_rollout_started or measured_rollout_started,
            "M2466 must not execute policy actions or rollouts.",
        ),
        (
            "m2466_no_repair_training_replay_promotion",
            "execution_boundary",
            "summary",
            "contract_violation",
            "repair_training_replay_promotion",
            int(repair_execution_started or training_started or replay_started or ppo_used or promoted),
            repair_execution_started or training_started or replay_started or ppo_used or promoted,
            "Diagnostic variants are not repair execution, training, replay, PPO, or promotion.",
        ),
        (
            "m2466_no_private_holdout",
            "execution_boundary",
            "summary",
            "contract_violation",
            "private_holdout_used",
            private_holdout_used,
            private_holdout_used,
            "M2466 does not use private holdout data.",
        ),
        (
            "m2466_no_ranking_or_winner",
            "claim_boundary",
            "summary",
            "metric_artifact",
            "ranking_or_winner_count",
            ranking_admissible_count + winner_selected_count,
            ranking_admissible_count != 0 or winner_selected_count != 0,
            "M2466 must not rank diagnostic variants or select winners.",
        ),
        (
            "m2466_no_verdict_claims",
            "claim_boundary",
            "summary",
            "metric_artifact",
            "verdict_claim_count",
            verdict_claim_count,
            verdict_claim_count != 0,
            "M2466 may not claim paper, self-ID, scenario-redesign, training-repair, or current-sim verdicts.",
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


def _claim_boundary_rows(*, result_class: str, diagnostic_classification: str) -> list[dict[str, Any]]:
    complete = result_class == RESULT_COMPLETE
    return [
        {
            "claim_key": "r1_reset_sampling_diagnostic_classification",
            "claim_value": diagnostic_classification,
            "admissible": complete,
            "reason": "M2466 may classify reset-sampling diagnostics for the R1 stable-AES overlay family only.",
        },
        {
            "claim_key": "diagnostic_variant_repair_or_promotion",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "Diagnostic-only variants are not repaired overlays, rankings, winners, or promoted configs.",
        },
        {"claim_key": "environment_step_or_policy_action", "claim_value": "false", "admissible": True, "reason": "M2466 stops after reset."},
        {"claim_key": "measured_rollout_started", "claim_value": "false", "admissible": True, "reason": "No rollout is run."},
        {"claim_key": "repair_training_started", "claim_value": "false", "admissible": True, "reason": "No repair or training is executed."},
        {
            "claim_key": "actual_success_improvement",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "Reset-only diagnostics do not measure driver performance.",
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
            "reason": "M2466 is a reset diagnostic panel, not a current-sim verdict.",
        },
    ]


def _decision_rows(*, result_class: str, diagnostic_classification: str, next_blocker: str) -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "r1_reset_sampling_diagnostic_complete",
            "decision_value": "true" if result_class == RESULT_COMPLETE else "false",
            "admissible": result_class == RESULT_COMPLETE,
            "reason": "The diagnostic panel wrote reset-only evidence and classification rows.",
        },
        {
            "decision_key": "diagnostic_classification",
            "decision_value": diagnostic_classification,
            "admissible": result_class == RESULT_COMPLETE,
            "reason": "Classification is diagnostic only and must be audited before repair or measured execution.",
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
            "reason": "Route diagnostic output to result audit.",
        },
    ]


def run_r1_reset_sampling_diagnostic_panel(
    *,
    m2464_dir: Path | str = DEFAULT_M2464_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_overlay_family: str = DEFAULT_TARGET_OVERLAY_FAMILY,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    reset_seed_count: int = DEFAULT_RESET_SEED_COUNT,
    expected_observation_dim: int = DEFAULT_EXPECTED_OBSERVATION_DIM,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_dir = Path(m2464_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    config_dir = output / "diagnostic_env_configs"
    config_dir.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(source_dir / "summary.json")
    source_failures: list[str] = []
    if str(source_summary.get("result_class", "")) != "scenario_quality_concrete_overlay_reset_validation_fail":
        source_failures.append("m2464_result_class_not_expected_fail")
    if int(source_summary.get("target_reset_count", -1)) != 6:
        source_failures.append("m2464_target_reset_count_not_6")
    if int(source_summary.get("static_validation_pass_count", -1)) != 6:
        source_failures.append("m2464_static_validation_pass_count_not_6")
    if int(source_summary.get("effective_env_config_written_count", -1)) != 6:
        source_failures.append("m2464_effective_env_config_written_count_not_6")
    if int(source_summary.get("environment_reset_attempt_count", -1)) != 6:
        source_failures.append("m2464_reset_attempt_count_not_6")
    if int(source_summary.get("environment_reset_success_count", -1)) != 4:
        source_failures.append("m2464_reset_success_count_not_4")
    if int(source_summary.get("environment_reset_failure_count", -1)) != 2:
        source_failures.append("m2464_reset_failure_count_not_2")
    if "scenario_sampling_failure" not in set(str(item) for item in source_summary.get("failure_types_observed", [])):
        source_failures.append("m2464_missing_scenario_sampling_failure")

    r1_rows, config_payloads = _load_r1_sources(source_dir, target_overlay_family)
    source_overlay_hashes = sorted({str(row.get("env_config_overlay_hash", "")) for row in r1_rows})
    r1_effective_configs = [
        _effective_config_from_payload(payload) for payload in config_payloads.values() if isinstance(payload, Mapping)
    ]
    unique_effective_config_hashes = sorted({_json_hash(config) for config in r1_effective_configs if config})
    if r1_rows and len(unique_effective_config_hashes) != 1:
        source_failures.append("m2464_r1_effective_configs_not_identical")
    source_overlay_hash = source_overlay_hashes[0] if len(source_overlay_hashes) == 1 else ""
    source_reset_target_ids = "|".join(str(row.get("reset_target_id", "")) for row in r1_rows)
    source_candidate_ids = "|".join(str(row.get("source_candidate_id", "")) for row in r1_rows)
    baseline_payload = next(iter(config_payloads.values()), {})
    baseline_config = _effective_config_from_payload(baseline_payload) if isinstance(baseline_payload, Mapping) else {}
    variants = _variant_specs(baseline_config) if baseline_config else []

    variant_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    effective_configs: dict[str, Any] = {}
    effective_config_paths: dict[str, Path] = {}
    actor_contract_failure_count = 0
    for variant in variants:
        config_data = dict(variant["config"])
        config = build_env_config(config_data)
        effective_config = _config_to_dict(config, config_data)
        actor_contract_pass = _actor_contract_guardrail_pass(effective_config)
        if not actor_contract_pass:
            actor_contract_failure_count += 1
        path = _write_variant_config(
            output_dir=output,
            variant=variant,
            source_rows=r1_rows,
            source_overlay_hash=source_overlay_hash,
            effective_config=effective_config,
        )
        effective_configs[str(variant["variant_id"])] = config
        effective_config_paths[str(variant["variant_id"])] = path
        variant_rows.append(
            {
                "variant_id": str(variant["variant_id"]),
                "variant_class": str(variant["variant_class"]),
                "diagnostic_only": True,
                "source_variant_id": str(variant["source_variant_id"]),
                "effective_env_config_path": str(path),
                "mutation_summary": str(variant["mutation_summary"]),
                "actor_contract_guardrail_pass": actor_contract_pass,
                "active_config_overwritten": False,
                "repair_candidate": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "promoted": False,
            }
        )

    source_clean = (
        not source_failures
        and len(r1_rows) == 3
        and len(source_overlay_hashes) == 1
        and len(unique_effective_config_hashes) == 1
        and bool(variants)
    )
    if source_clean and actor_contract_failure_count == 0:
        for variant in variants:
            variant_id = str(variant["variant_id"])
            for seed_index in range(int(reset_seed_count)):
                eval_seed = int(eval_seed_base) + seed_index
                diagnostic_rows.append(
                    _reset_row(
                        variant=variant,
                        config=effective_configs[variant_id],
                        effective_config_path=effective_config_paths[variant_id],
                        eval_seed=eval_seed,
                        reset_seed_index=seed_index,
                        expected_observation_dim=expected_observation_dim,
                        target_overlay_family=target_overlay_family,
                        source_overlay_hash=source_overlay_hash,
                        source_reset_target_ids=source_reset_target_ids,
                        source_candidate_ids=source_candidate_ids,
                    )
                )

    variant_summary_rows = _variant_summary_rows(diagnostic_rows)
    expected_variant_count = 5
    expected_attempt_count = expected_variant_count * int(reset_seed_count)
    environment_step_count = sum(int(row.get("environment_step_count", 0) or 0) for row in diagnostic_rows)
    active_config_overwrite_count = sum(
        not _inside_dir(Path(str(row.get("effective_env_config_path", ""))), output) for row in variant_rows
    ) + sum(_bool(row.get("active_config_overwritten")) for row in diagnostic_rows)
    policy_action_executed = any(_bool(row.get("policy_action_executed")) for row in diagnostic_rows)
    environment_rollout_started = any(_bool(row.get("environment_rollout_started")) for row in diagnostic_rows)
    measured_rollout_started = any(_bool(row.get("measured_rollout_started")) for row in diagnostic_rows)
    repair_execution_started = any(_bool(row.get("repair_execution_started")) for row in diagnostic_rows)
    training_started = any(_bool(row.get("training_started")) for row in diagnostic_rows)
    replay_started = any(_bool(row.get("replay_started")) for row in diagnostic_rows)
    ppo_used = any(_bool(row.get("ppo_used")) for row in diagnostic_rows)
    promoted = any(_bool(row.get("promoted")) for row in diagnostic_rows) or any(_bool(row.get("promoted")) for row in variant_rows)
    private_holdout_used = any(_bool(row.get("private_holdout_used")) for row in diagnostic_rows)
    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in diagnostic_rows) + sum(
        _bool(row.get("ranking_admissible")) for row in variant_rows
    )
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in diagnostic_rows) + sum(
        _bool(row.get("winner_selected")) for row in variant_rows
    )
    verdict_claim_count = sum(any(_bool(row.get(flag)) for flag in FALSE_SUMMARY_FLAGS[-6:]) for row in diagnostic_rows)

    guards = _guardrail_rows(
        source_admission_failure_count=len(source_failures),
        r1_target_count=len(r1_rows),
        source_overlay_hash_count=len(source_overlay_hashes),
        source_unique_effective_config_count=len(unique_effective_config_hashes),
        variant_count=len(variant_rows),
        expected_variant_count=expected_variant_count,
        diagnostic_attempt_count=len(diagnostic_rows),
        expected_attempt_count=expected_attempt_count,
        actor_contract_failure_count=actor_contract_failure_count,
        active_config_overwrite_count=active_config_overwrite_count,
        environment_step_count=environment_step_count,
        policy_action_executed=policy_action_executed,
        environment_rollout_started=environment_rollout_started,
        measured_rollout_started=measured_rollout_started,
        repair_execution_started=repair_execution_started,
        training_started=training_started,
        replay_started=replay_started,
        ppo_used=ppo_used,
        promoted=promoted,
        private_holdout_used=private_holdout_used,
        ranking_admissible_count=ranking_admissible_count,
        winner_selected_count=winner_selected_count,
        verdict_claim_count=verdict_claim_count,
    )
    guardrail_violation_count = sum(_bool(row.get("violation")) for row in guards)
    panel_complete_for_classification = guardrail_violation_count == 0
    diagnostic_classification, classification_rows = _classification_rows(
        variant_summary_rows,
        complete=panel_complete_for_classification,
    )
    result_class = RESULT_COMPLETE if guardrail_violation_count == 0 else RESULT_FAIL
    claim_rows = _claim_boundary_rows(result_class=result_class, diagnostic_classification=diagnostic_classification)
    decision_rows = _decision_rows(result_class=result_class, diagnostic_classification=diagnostic_classification, next_blocker=next_blocker)

    reset_success_count = sum(_bool(row.get("reset_success")) for row in diagnostic_rows)
    reset_failure_rows = [dict(row) for row in diagnostic_rows if not _bool(row.get("reset_success"))]
    baseline_summary = next((row for row in variant_summary_rows if row.get("variant_id") == "baseline_r1_original"), {})
    failure_types = sorted(
        {
            str(row.get("failure_mode_to_preserve", ""))
            for row in guards
            if _bool(row.get("violation")) and str(row.get("failure_mode_to_preserve", ""))
        }
        | {str(row.get("failure_type", "")) for row in diagnostic_rows if str(row.get("failure_type", ""))}
    )
    if "seed_fragility" in diagnostic_classification:
        failure_types.append("seed_fragility")
    failure_types = sorted(set(item for item in failure_types if item))

    write_csv_rows(output / "diagnostic_rows.csv", diagnostic_rows, fieldnames=DIAGNOSTIC_ROW_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", reset_failure_rows, fieldnames=DIAGNOSTIC_ROW_FIELDNAMES)
    write_csv_rows(output / "variant_rows.csv", variant_rows, fieldnames=VARIANT_FIELDNAMES)
    write_csv_rows(output / "variant_summary_rows.csv", variant_summary_rows, fieldnames=VARIANT_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "classification_rows.csv", classification_rows, fieldnames=CLASSIFICATION_FIELDNAMES)
    write_csv_rows(output / "guardrail_rows.csv", guards, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decision_rows, fieldnames=DECISION_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_artifacts": {
            "m2464_summary": str(source_dir / "summary.json"),
            "m2464_reset_target_rows": str(source_dir / "reset_target_rows.csv"),
            "m2464_reset_validation_rows": str(source_dir / "reset_validation_rows.csv"),
            "m2464_reset_failure_rows": str(source_dir / "reset_failure_rows.csv"),
        },
        "source_result_class": str(source_summary.get("result_class", "")),
        "source_admission_failure_count": len(source_failures),
        "source_admission_failures": source_failures,
        "target_overlay_family": str(target_overlay_family),
        "r1_source_target_count": len(r1_rows),
        "source_overlay_hash_count": len(source_overlay_hashes),
        "source_overlay_hash": source_overlay_hash,
        "source_unique_effective_config_count": len(unique_effective_config_hashes),
        "source_effective_config_hashes": unique_effective_config_hashes,
        "source_reset_target_ids": [str(row.get("reset_target_id", "")) for row in r1_rows],
        "source_candidate_ids": [str(row.get("source_candidate_id", "")) for row in r1_rows],
        "eval_seed_base": int(eval_seed_base),
        "reset_seed_count": int(reset_seed_count),
        "expected_observation_dim": int(expected_observation_dim),
        "variant_count": len(variant_rows),
        "expected_variant_count": expected_variant_count,
        "diagnostic_attempt_count": len(diagnostic_rows),
        "expected_diagnostic_attempt_count": expected_attempt_count,
        "reset_success_count": reset_success_count,
        "reset_failure_count": len(reset_failure_rows),
        "baseline_reset_success_count": int(baseline_summary.get("reset_success_count", 0) or 0),
        "baseline_reset_failure_count": int(baseline_summary.get("reset_failure_count", 0) or 0),
        "baseline_reset_success_rate": float(baseline_summary.get("reset_success_rate", 0.0) or 0.0),
        "variant_success_rates": _rate_by_variant(variant_summary_rows),
        "diagnostic_classification": diagnostic_classification,
        "actor_contract_failure_count": actor_contract_failure_count,
        "active_config_overwrite_count": active_config_overwrite_count,
        "environment_step_count": environment_step_count,
        "policy_action_executed": policy_action_executed,
        "environment_rollout_started": environment_rollout_started,
        "measured_rollout_started": measured_rollout_started,
        "repair_execution_started": repair_execution_started,
        "training_started": training_started,
        "replay_started": replay_started,
        "ppo_used": ppo_used,
        "promoted": promoted,
        "private_holdout_used": private_holdout_used,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "diagnostic_rows": str(output / "diagnostic_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "variant_rows": str(output / "variant_rows.csv"),
            "variant_summary_rows": str(output / "variant_summary_rows.csv"),
            "classification_rows": str(output / "classification_rows.csv"),
            "guardrail_rows": str(output / "guardrail_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "decision_rows": str(output / "decision_rows.csv"),
            "diagnostic_env_configs": str(config_dir),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2466-paper-route-current-sim-dual-axis-scenario-quality-r1-reset-sampling-diagnostic-panel",
            "status": "completed" if result_class == RESULT_COMPLETE else "failed",
            "result_class": result_class,
            "diagnostic_classification": diagnostic_classification,
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2464-dir", type=Path, default=DEFAULT_M2464_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-overlay-family", default=DEFAULT_TARGET_OVERLAY_FAMILY)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--reset-seed-count", type=int, default=DEFAULT_RESET_SEED_COUNT)
    parser.add_argument("--expected-observation-dim", type=int, default=DEFAULT_EXPECTED_OBSERVATION_DIM)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_r1_reset_sampling_diagnostic_panel(
        m2464_dir=args.m2464_dir,
        output_dir=args.output_dir,
        target_overlay_family=args.target_overlay_family,
        eval_seed_base=args.eval_seed_base,
        reset_seed_count=args.reset_seed_count,
        expected_observation_dim=args.expected_observation_dim,
        next_blocker=args.next_blocker,
    )
    print(f"summary: {summary['artifacts']['summary']}")
    print(f"result_class: {summary['result_class']}")
    print(f"diagnostic_attempt_count: {summary['diagnostic_attempt_count']}")
    print(f"reset_success_count: {summary['reset_success_count']}")
    print(f"reset_failure_count: {summary['reset_failure_count']}")
    print(f"baseline_reset_success_rate: {summary['baseline_reset_success_rate']}")
    print(f"diagnostic_classification: {summary['diagnostic_classification']}")
    print(f"guardrail_violation_count: {summary['guardrail_violation_count']}")
    print(f"next_blocker: {summary['next_blocker']}")
    return 0 if summary["result_class"] == RESULT_COMPLETE else 1


if __name__ == "__main__":
    raise SystemExit(main())
