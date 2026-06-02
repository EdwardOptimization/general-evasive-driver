"""Metric-selected validation preflight under the soft-boundary task metric."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift import paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation as m2413
from autodrift import paper_route_current_sim_scenario_task_family_measured_execution as base_runner
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv


DEFAULT_SOURCE_RESET_DIR = m2413.DEFAULT_SOURCE_RESET_DIR
DEFAULT_SOURCE_EFFECTIVE_DIR = m2413.DEFAULT_SOURCE_EFFECTIVE_DIR
DEFAULT_SELECTED_ROWS = m2413.DEFAULT_SELECTED_ROWS
DEFAULT_CONFIG_ROOT = m2413.DEFAULT_CONFIG_ROOT
DEFAULT_M2413_EPISODE_ROWS = Path(
    "runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight")
DEFAULT_EVAL_SEED_BASE = 244300
DEFAULT_SOFT_OFFTRACK_TOLERANCE_M = 0.20
TARGET_RESET_TARGET_COUNT = 350
TARGET_SELECTED_CHECKPOINT_COUNT = 15
TARGET_EPISODE_COUNT = TARGET_RESET_TARGET_COUNT * TARGET_SELECTED_CHECKPOINT_COUNT
DEFAULT_NEXT_BLOCKER = "m2444-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-result-audit"

RESULT_PASS = "current_sim_dual_axis_metric_selected_validation_preflight_pass"
RESULT_FAIL = "current_sim_dual_axis_metric_selected_validation_preflight_incomplete_or_fail"
ROUTE_RECOMMENDATION = "route_to_metric_selected_validation_preflight_result_audit"

WORKLOAD_FIELDNAMES = [
    "workload_id",
    "selected_checkpoint_index",
    "reset_target_index",
    "eval_seed",
    "selected_key",
    "matrix_id",
    "profile_name",
    "seed_id",
    "profile_config_path",
    "selected_checkpoint_path",
    "selected_checkpoint_step",
    "selected_checkpoint_kind",
    "original_reset_target_key",
    "metric_selected_reset_target_key",
    "original_env_config_hash",
    "metric_selected_env_config_hash",
    "pack_id",
    "scenario_spec_id",
    "family_ids",
    "family_count",
    "effective_candidate_ids",
    "effective_candidate_count",
    "scenario_reference_count",
    "soft_offtrack_metric_enabled",
    "soft_offtrack_tolerance_m",
    "sensitivity_thresholds_m",
    "environment_rollout_started",
    "environment_step_count",
    "policy_action_executed",
    "ranking_admissible",
    "winner_selected",
]

RESET_TARGET_FIELDNAMES = [
    "reset_target_index",
    "original_reset_target_key",
    "metric_selected_reset_target_key",
    "original_env_config_hash",
    "metric_selected_env_config_hash",
    "pack_id",
    "scenario_spec_id",
    "soft_offtrack_metric_enabled",
    "soft_offtrack_tolerance_m",
    "sensitivity_thresholds_m",
    "actor_contract_guardrail_pass",
]

RESET_FIELDNAMES = [
    "reset_target_index",
    "original_reset_target_key",
    "metric_selected_reset_target_key",
    "environment_load_attempted",
    "environment_reset_attempted",
    "environment_reset_success",
    "original_observation_shape",
    "metric_selected_observation_shape",
    "actor_observation_shape_unchanged",
    "observation_length",
    "observation_finite",
    "soft_offtrack_metric_enabled",
    "soft_offtrack_tolerance_m",
    "environment_step_count",
    "policy_action_executed",
    "failure_reason",
]

DECISION_FIELDNAMES = ["decision_key", "decision_value", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    return base_runner._bool(value, default=default)


def _json_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _observation_shape_text(shape: tuple[int, ...]) -> str:
    return "x".join(str(int(item)) for item in shape)


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


def _metric_selected_env_config(
    env_config: Mapping[str, Any],
    *,
    soft_offtrack_tolerance_m: float,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(dict(env_config)))
    updated["soft_offtrack_metric_enabled"] = True
    updated["soft_offtrack_tolerance_m"] = float(soft_offtrack_tolerance_m)
    return updated


def _metric_selected_reset_target_key(
    *,
    pack_id: str,
    scenario_spec_id: str,
    env_config: Mapping[str, Any],
) -> str:
    return f"{pack_id}|{scenario_spec_id}|{_json_hash(env_config)[:16]}"


def _selected_key(selected: Mapping[str, Any], index: int) -> str:
    return base_runner._selected_key(selected) or f"selected_{index:03d}"


def _profile_config_path(config_root: Path, selected: Mapping[str, Any]) -> str:
    return str(base_runner._config_path(config_root, selected))


def _sensitivity_threshold_text() -> str:
    return "0.02|0.05|0.10|0.20"


def soft_reset_target_rows(
    *,
    reset_target_specs: Sequence[Mapping[str, Any]],
    soft_offtrack_tolerance_m: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in reset_target_specs:
        env_config = spec.get("env_config") if isinstance(spec.get("env_config"), Mapping) else {}
        metric_env_config = _metric_selected_env_config(
            env_config,
            soft_offtrack_tolerance_m=soft_offtrack_tolerance_m,
        )
        rows.append(
            {
                "reset_target_index": int(spec.get("reset_target_index", 0) or 0),
                "original_reset_target_key": str(spec.get("reset_target_key", "")),
                "metric_selected_reset_target_key": _metric_selected_reset_target_key(
                    pack_id=str(spec.get("pack_id", "")),
                    scenario_spec_id=str(spec.get("scenario_spec_id", "")),
                    env_config=metric_env_config,
                ),
                "original_env_config_hash": str(spec.get("env_config_hash", "")),
                "metric_selected_env_config_hash": _json_hash(metric_env_config)[:16],
                "pack_id": str(spec.get("pack_id", "")),
                "scenario_spec_id": str(spec.get("scenario_spec_id", "")),
                "soft_offtrack_metric_enabled": True,
                "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
                "sensitivity_thresholds_m": _sensitivity_threshold_text(),
                "actor_contract_guardrail_pass": _bool(spec.get("actor_contract_guardrail_pass"), default=False),
            }
        )
    return sorted(rows, key=lambda row: int(row["reset_target_index"]))


def workload_rows(
    *,
    reset_target_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    config_root: Path | str,
    eval_seed_base: int,
    soft_offtrack_tolerance_m: float,
) -> list[dict[str, Any]]:
    root = Path(config_root)
    target_rows = {int(row["reset_target_index"]): row for row in soft_reset_target_rows(
        reset_target_specs=reset_target_specs,
        soft_offtrack_tolerance_m=soft_offtrack_tolerance_m,
    )}
    rows: list[dict[str, Any]] = []
    for selected_index, selected in enumerate(selected_rows):
        selected_key = _selected_key(selected, selected_index)
        for spec in reset_target_specs:
            reset_index = int(spec.get("reset_target_index", 0) or 0)
            target = target_rows[reset_index]
            eval_seed = m2413.eval_seed_for_cell(
                eval_seed_base=int(eval_seed_base),
                selected_index=int(selected_index),
                reset_target_index=int(reset_index),
            )
            rows.append(
                {
                    "workload_id": f"{selected_key}::{target['metric_selected_reset_target_key']}",
                    "selected_checkpoint_index": int(selected_index),
                    "reset_target_index": int(reset_index),
                    "eval_seed": int(eval_seed),
                    "selected_key": selected_key,
                    "matrix_id": str(selected.get("matrix_id", "")),
                    "profile_name": str(selected.get("profile_name", "")),
                    "seed_id": str(selected.get("seed_id", "")),
                    "profile_config_path": _profile_config_path(root, selected),
                    "selected_checkpoint_path": str(selected.get("selected_checkpoint_path", "")),
                    "selected_checkpoint_step": str(selected.get("selected_checkpoint_step", "")),
                    "selected_checkpoint_kind": str(selected.get("selected_checkpoint_kind", "")),
                    "original_reset_target_key": str(target["original_reset_target_key"]),
                    "metric_selected_reset_target_key": str(target["metric_selected_reset_target_key"]),
                    "original_env_config_hash": str(target["original_env_config_hash"]),
                    "metric_selected_env_config_hash": str(target["metric_selected_env_config_hash"]),
                    "pack_id": str(spec.get("pack_id", "")),
                    "scenario_spec_id": str(spec.get("scenario_spec_id", "")),
                    "family_ids": str(spec.get("family_ids", "")),
                    "family_count": int(spec.get("family_count", 0) or 0),
                    "effective_candidate_ids": str(spec.get("effective_candidate_ids", "")),
                    "effective_candidate_count": int(spec.get("effective_candidate_count", 0) or 0),
                    "scenario_reference_count": int(spec.get("scenario_reference_count", 0) or 0),
                    "soft_offtrack_metric_enabled": True,
                    "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
                    "sensitivity_thresholds_m": _sensitivity_threshold_text(),
                    "environment_rollout_started": False,
                    "environment_step_count": 0,
                    "policy_action_executed": False,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
    return rows


def reset_metric_selected_target(
    *,
    spec: Mapping[str, Any],
    target_row: Mapping[str, Any],
    eval_seed: int,
    soft_offtrack_tolerance_m: float,
) -> dict[str, Any]:
    original_key = str(target_row.get("original_reset_target_key", ""))
    metric_key = str(target_row.get("metric_selected_reset_target_key", ""))
    try:
        env_config = spec.get("env_config") if isinstance(spec.get("env_config"), Mapping) else {}
        original_config = build_env_config(dict(env_config))
        metric_config = build_env_config(
            _metric_selected_env_config(env_config, soft_offtrack_tolerance_m=soft_offtrack_tolerance_m)
        )
        original_env = AutoDriftEnv(original_config)
        metric_env = AutoDriftEnv(metric_config)
        try:
            original_shape = tuple(int(item) for item in original_env.observation_space.shape)
            metric_shape = tuple(int(item) for item in metric_env.observation_space.shape)
            obs, info = metric_env.reset(seed=int(eval_seed))
        finally:
            for env in (original_env, metric_env):
                close = getattr(env, "close", None)
                if callable(close):
                    close()
        return {
            "reset_target_index": int(spec.get("reset_target_index", 0) or 0),
            "original_reset_target_key": original_key,
            "metric_selected_reset_target_key": metric_key,
            "environment_load_attempted": True,
            "environment_reset_attempted": True,
            "environment_reset_success": True,
            "original_observation_shape": _observation_shape_text(original_shape),
            "metric_selected_observation_shape": _observation_shape_text(metric_shape),
            "actor_observation_shape_unchanged": original_shape == metric_shape,
            "observation_length": _observation_length(obs),
            "observation_finite": _finite_observation(obs),
            "soft_offtrack_metric_enabled": bool(info.get("soft_offtrack_metric_enabled", False)),
            "soft_offtrack_tolerance_m": float(info.get("soft_offtrack_tolerance_m", soft_offtrack_tolerance_m)),
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": "",
        }
    except Exception as exc:  # noqa: BLE001 - preflight records exact failure text.
        return {
            "reset_target_index": int(spec.get("reset_target_index", 0) or 0),
            "original_reset_target_key": original_key,
            "metric_selected_reset_target_key": metric_key,
            "environment_load_attempted": True,
            "environment_reset_attempted": True,
            "environment_reset_success": False,
            "original_observation_shape": "",
            "metric_selected_observation_shape": "",
            "actor_observation_shape_unchanged": False,
            "observation_length": 0,
            "observation_finite": False,
            "soft_offtrack_metric_enabled": False,
            "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": str(exc),
        }


def _source_episode_coverage(
    rows: Sequence[Mapping[str, Any]],
    *,
    expected_reset_keys: Sequence[str],
    expected_selected_indices: Sequence[int],
) -> dict[str, Any]:
    reset_keys = {str(row.get("reset_target_key", "")) for row in rows if str(row.get("reset_target_key", ""))}
    selected_indices = {
        str(row.get("selected_checkpoint_index", "")) for row in rows if str(row.get("selected_checkpoint_index", ""))
    }
    cells = {
        (str(row.get("reset_target_key", "")), str(row.get("selected_checkpoint_index", "")))
        for row in rows
        if str(row.get("reset_target_key", "")) and str(row.get("selected_checkpoint_index", ""))
    }
    expected_reset_key_set = {str(key) for key in expected_reset_keys if str(key)}
    expected_selected_index_set = {str(index) for index in expected_selected_indices}
    expected_cells = {
        (reset_key, selected_index)
        for reset_key in expected_reset_key_set
        for selected_index in expected_selected_index_set
    }
    return {
        "source_m2413_episode_count": len(rows),
        "source_m2413_reset_target_count": len(reset_keys),
        "source_m2413_selected_checkpoint_count": len(selected_indices),
        "source_m2413_unique_cell_count": len(cells),
        "source_m2413_duplicate_cell_count": max(0, len(rows) - len(cells)),
        "missing_source_target_count": len(expected_reset_key_set - reset_keys),
        "missing_source_selected_checkpoint_count": len(expected_selected_index_set - selected_indices),
        "missing_source_cell_count": len(expected_cells - cells),
    }


def _decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "measured_policy_rollout_started",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2443 stops at reset/config preflight and never calls policy actions.",
        },
        {
            "decision_key": "policy_action_executed",
            "decision_value": "false",
            "admissible": True,
            "reason": "Reset preflight creates environments and resets only.",
        },
        {
            "decision_key": "actual_success_claim",
            "decision_value": "false",
            "admissible": True,
            "reason": "Reset/config readiness is not executed driving success.",
        },
        {
            "decision_key": "current_sim_verdict",
            "decision_value": "blocked",
            "admissible": False,
            "reason": "A current-sim verdict requires fresh measured rollout and later audit.",
        },
        {
            "decision_key": "next_route",
            "decision_value": ROUTE_RECOMMENDATION,
            "admissible": True,
            "reason": "Audit preflight before any full metric-selected measured validation.",
        },
    ]


def run_metric_selected_validation_preflight(
    *,
    source_reset_dir: Path | str = DEFAULT_SOURCE_RESET_DIR,
    source_effective_dir: Path | str = DEFAULT_SOURCE_EFFECTIVE_DIR,
    selected_rows_path: Path | str = DEFAULT_SELECTED_ROWS,
    config_root: Path | str = DEFAULT_CONFIG_ROOT,
    m2413_episode_rows_path: Path | str = DEFAULT_M2413_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    soft_offtrack_tolerance_m: float = DEFAULT_SOFT_OFFTRACK_TOLERANCE_M,
    target_reset_target_count: int = TARGET_RESET_TARGET_COUNT,
    target_selected_checkpoint_count: int = TARGET_SELECTED_CHECKPOINT_COUNT,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    reset_target_specs: Sequence[Mapping[str, Any]] | None = None,
    selected_rows: Sequence[Mapping[str, Any]] | None = None,
    source_episode_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    specs = list(reset_target_specs) if reset_target_specs is not None else m2413.load_source_linked_reset_target_specs(
        source_reset_dir=source_reset_dir,
        source_effective_dir=source_effective_dir,
    )
    selected = list(selected_rows) if selected_rows is not None else m2413.load_selected_rows(selected_rows_path)
    source_rows = (
        list(source_episode_rows)
        if source_episode_rows is not None
        else read_csv_rows(m2413_episode_rows_path)
    )

    target_rows = soft_reset_target_rows(
        reset_target_specs=specs,
        soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
    )
    target_rows_by_index = {int(row["reset_target_index"]): row for row in target_rows}
    workload = workload_rows(
        reset_target_specs=specs,
        selected_rows=selected,
        config_root=config_root,
        eval_seed_base=int(eval_seed_base),
        soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
    )
    reset_rows = [
        reset_metric_selected_target(
            spec=spec,
            target_row=target_rows_by_index[int(spec.get("reset_target_index", 0) or 0)],
            eval_seed=int(eval_seed_base) + int(spec.get("reset_target_index", 0) or 0),
            soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
        )
        for spec in specs
    ]
    decision_rows = _decision_rows()
    source_coverage = _source_episode_coverage(
        source_rows,
        expected_reset_keys=[str(row.get("original_reset_target_key", "")) for row in target_rows],
        expected_selected_indices=list(range(len(selected))),
    )

    duplicate_workload_count = len(workload) - len({str(row.get("workload_id", "")) for row in workload})
    reset_success_count = sum(_bool(row.get("environment_reset_success")) for row in reset_rows)
    reset_failure_count = len(reset_rows) - reset_success_count
    shape_changed_count = sum(not _bool(row.get("actor_observation_shape_unchanged")) for row in reset_rows)
    finite_observation_count = sum(_bool(row.get("observation_finite")) for row in reset_rows)
    soft_enabled_count = sum(_bool(row.get("soft_offtrack_metric_enabled")) for row in reset_rows)
    environment_step_count = sum(int(row.get("environment_step_count", 0) or 0) for row in reset_rows)
    policy_action_count = sum(_bool(row.get("policy_action_executed")) for row in reset_rows)
    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in workload)
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in workload)
    contract_guardrail_pass_count = sum(_bool(row.get("actor_contract_guardrail_pass")) for row in target_rows)
    missing_source_target_count = int(source_coverage["missing_source_target_count"])
    missing_source_selected_checkpoint_count = int(source_coverage["missing_source_selected_checkpoint_count"])
    missing_source_cell_count = int(source_coverage["missing_source_cell_count"])
    duplicate_source_cell_count = int(source_coverage["source_m2413_duplicate_cell_count"])

    guardrail_flags = {
        "environment_rollout_started": False,
        "measured_policy_rollout_started": False,
        "policy_action_executed": bool(policy_action_count),
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "active_config_overwritten": False,
        "actor_input_contract_changed": bool(shape_changed_count),
        "hidden_oracle_feature_injection": False,
        "actual_success_improvement_claim_made": False,
        "candidate_family_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": bool(winner_selected_count),
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    failure_types_observed = []
    if (
        len(specs) != int(target_reset_target_count)
        or len(selected) != int(target_selected_checkpoint_count)
        or len(workload) != int(target_episode_count)
        or missing_source_target_count
        or missing_source_selected_checkpoint_count
        or missing_source_cell_count
        or duplicate_source_cell_count
        or duplicate_workload_count
    ):
        failure_types_observed.append("scenario_sampling_failure")
    if reset_failure_count or shape_changed_count or soft_enabled_count != len(reset_rows):
        failure_types_observed.append("metric_artifact")
    if (
        contract_guardrail_pass_count != len(target_rows)
        or environment_step_count
        or policy_action_count
        or ranking_admissible_count
        or winner_selected_count
    ):
        failure_types_observed.append("contract_violation")

    passes = (
        len(specs) == int(target_reset_target_count)
        and len(selected) == int(target_selected_checkpoint_count)
        and len(workload) == int(target_episode_count)
        and source_coverage["source_m2413_episode_count"] == int(target_episode_count)
        and source_coverage["source_m2413_reset_target_count"] == int(target_reset_target_count)
        and source_coverage["source_m2413_selected_checkpoint_count"] == int(target_selected_checkpoint_count)
        and source_coverage["source_m2413_unique_cell_count"] == int(target_episode_count)
        and missing_source_target_count == 0
        and missing_source_selected_checkpoint_count == 0
        and missing_source_cell_count == 0
        and duplicate_source_cell_count == 0
        and duplicate_workload_count == 0
        and contract_guardrail_pass_count == len(target_rows)
        and reset_success_count == len(reset_rows)
        and reset_failure_count == 0
        and shape_changed_count == 0
        and finite_observation_count == len(reset_rows)
        and soft_enabled_count == len(reset_rows)
        and environment_step_count == 0
        and policy_action_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )
    artifacts = {
        "summary": str(output / "summary.json"),
        "workload_rows": str(output / "workload_rows.csv"),
        "soft_reset_target_rows": str(output / "soft_reset_target_rows.csv"),
        "reset_validation_rows": str(output / "reset_validation_rows.csv"),
        "decision_rows": str(output / "decision_rows.csv"),
    }
    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "soft_offtrack_metric_enabled": True,
        "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
        "sensitivity_thresholds_m": [0.02, 0.05, 0.10, 0.20],
        "reset_target_count": len(specs),
        "target_reset_target_count": int(target_reset_target_count),
        "selected_checkpoint_count": len(selected),
        "target_selected_checkpoint_count": int(target_selected_checkpoint_count),
        "workload_row_count": len(workload),
        "target_episode_count": int(target_episode_count),
        **source_coverage,
        "duplicate_workload_count": duplicate_workload_count,
        "contract_guardrail_pass_count": contract_guardrail_pass_count,
        "reset_validation_row_count": len(reset_rows),
        "environment_reset_success_count": reset_success_count,
        "environment_reset_failure_count": reset_failure_count,
        "actor_observation_shape_changed_count": shape_changed_count,
        "finite_observation_count": finite_observation_count,
        "soft_enabled_reset_count": soft_enabled_count,
        "environment_step_count": environment_step_count,
        "policy_action_count": policy_action_count,
        "measured_policy_rollout_started": False,
        "actual_success_claim_made": False,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types_observed,
        "route_recommendation": ROUTE_RECOMMENDATION,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }

    write_csv_rows(output / "workload_rows.csv", workload, fieldnames=WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "soft_reset_target_rows.csv", target_rows, fieldnames=RESET_TARGET_FIELDNAMES)
    write_csv_rows(output / "reset_validation_rows.csv", reset_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decision_rows, fieldnames=DECISION_FIELDNAMES)
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-reset-dir", type=Path, default=DEFAULT_SOURCE_RESET_DIR)
    parser.add_argument("--source-effective-dir", type=Path, default=DEFAULT_SOURCE_EFFECTIVE_DIR)
    parser.add_argument("--selected-rows", type=Path, default=DEFAULT_SELECTED_ROWS)
    parser.add_argument("--config-root", type=Path, default=DEFAULT_CONFIG_ROOT)
    parser.add_argument("--m2413-episode-rows", type=Path, default=DEFAULT_M2413_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--soft-offtrack-tolerance-m", type=float, default=DEFAULT_SOFT_OFFTRACK_TOLERANCE_M)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_metric_selected_validation_preflight(
        source_reset_dir=args.source_reset_dir,
        source_effective_dir=args.source_effective_dir,
        selected_rows_path=args.selected_rows,
        config_root=args.config_root,
        m2413_episode_rows_path=args.m2413_episode_rows,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        soft_offtrack_tolerance_m=float(args.soft_offtrack_tolerance_m),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"workload_row_count={summary['workload_row_count']}")
    print(f"reset_target_count={summary['reset_target_count']}")
    print(f"selected_checkpoint_count={summary['selected_checkpoint_count']}")
    print(f"environment_reset_success_count={summary['environment_reset_success_count']}")
    print(f"actor_observation_shape_changed_count={summary['actor_observation_shape_changed_count']}")
    print(f"policy_action_count={summary['policy_action_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == RESULT_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
