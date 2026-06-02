"""Metric-selected measured validation under the soft-boundary task metric."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift import paper_route_current_sim_dual_axis_metric_selected_validation_preflight as m2443
from autodrift import paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation as m2413
from autodrift import paper_route_current_sim_scenario_task_family_measured_execution as base_runner
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import append_csv_row, completed_workload_ids, write_run_state


DEFAULT_PREFLIGHT_DIR = Path("runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight")
DEFAULT_PREFLIGHT_WORKLOAD_ROWS = DEFAULT_PREFLIGHT_DIR / "workload_rows.csv"
DEFAULT_PREFLIGHT_SUMMARY = DEFAULT_PREFLIGHT_DIR / "summary.json"
DEFAULT_SOURCE_RESET_DIR = m2413.DEFAULT_SOURCE_RESET_DIR
DEFAULT_SOURCE_EFFECTIVE_DIR = m2413.DEFAULT_SOURCE_EFFECTIVE_DIR
DEFAULT_SELECTED_ROWS = m2413.DEFAULT_SELECTED_ROWS
DEFAULT_CONFIG_ROOT = m2413.DEFAULT_CONFIG_ROOT
DEFAULT_OUTPUT_DIR = Path("runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation")
DEFAULT_SOFT_OFFTRACK_TOLERANCE_M = m2443.DEFAULT_SOFT_OFFTRACK_TOLERANCE_M
TARGET_RESET_TARGET_COUNT = m2443.TARGET_RESET_TARGET_COUNT
TARGET_SELECTED_CHECKPOINT_COUNT = m2443.TARGET_SELECTED_CHECKPOINT_COUNT
TARGET_EPISODE_COUNT = m2443.TARGET_EPISODE_COUNT
DEFAULT_NEXT_BLOCKER = (
    "m2446-paper-route-current-sim-dual-axis-metric-selected-measured-validation-result-audit"
)

RESULT_PASS = "current_sim_dual_axis_metric_selected_measured_validation_pass"
RESULT_FAIL = "current_sim_dual_axis_metric_selected_measured_validation_incomplete_or_fail"

METRIC_SELECTED_FIELDS = [
    "original_reset_target_key",
    "metric_selected_reset_target_key",
    "original_env_config_hash",
    "metric_selected_env_config_hash",
    "soft_offtrack_metric_enabled",
    "soft_offtrack_tolerance_m",
    "sensitivity_thresholds_m",
    "metric_selected_actual_success",
    "metric_selected_hard_offtrack_failure",
    "metric_selected_soft_offtrack_violation",
    "metric_selected_boundary_tolerated_success",
    "metric_selected_max_offtrack_overshoot_m",
    "metric_selected_measured_validation",
]
EPISODE_FIELDNAMES = base_runner._extend_unique(m2413.EPISODE_FIELDNAMES, METRIC_SELECTED_FIELDS)
FAILURE_FIELDNAMES = base_runner._extend_unique(m2413.FAILURE_FIELDNAMES, METRIC_SELECTED_FIELDS)
VALIDATION_FAILURE_FIELDNAMES = m2413.VALIDATION_FAILURE_FIELDNAMES
WORKLOAD_FIELDNAMES = base_runner._extend_unique(m2443.WORKLOAD_FIELDNAMES, ["scenario_index", "profile_seed"])
AGGREGATE_FIELDNAMES = m2413.AGGREGATE_FIELDNAMES
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]
DECISION_FIELDNAMES = ["decision_key", "decision_value", "admissible", "reason"]
RolloutFunction = m2413.RolloutFunction


def _bool(value: Any, *, default: bool = False) -> bool:
    return m2413._bool(value, default=default)


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if np.isfinite(result) else float(default)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return m2413.read_csv_rows(path)


def _preflight_summary_pass(path: Path | str) -> bool:
    payload = read_json(path)
    return (
        str(payload.get("result_class", "")) == m2443.RESULT_PASS
        and int(payload.get("workload_row_count", 0) or 0) == TARGET_EPISODE_COUNT
        and int(payload.get("policy_action_count", 0) or 0) == 0
        and int(payload.get("guardrail_violation_count", 0) or 0) == 0
    )


def metric_selected_reset_target_specs(
    reset_target_specs: Sequence[Mapping[str, Any]],
    *,
    soft_offtrack_tolerance_m: float,
) -> list[dict[str, Any]]:
    target_rows = {
        int(row["reset_target_index"]): row
        for row in m2443.soft_reset_target_rows(
            reset_target_specs=reset_target_specs,
            soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
        )
    }
    specs: list[dict[str, Any]] = []
    for spec in reset_target_specs:
        reset_index = int(spec.get("reset_target_index", 0) or 0)
        target = target_rows[reset_index]
        env_config = spec.get("env_config") if isinstance(spec.get("env_config"), Mapping) else {}
        metric_env_config = m2443._metric_selected_env_config(
            env_config,
            soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
        )
        metric_spec = dict(spec)
        metric_spec.update(
            {
                "env_config": metric_env_config,
                "original_reset_target_key": str(target.get("original_reset_target_key", "")),
                "metric_selected_reset_target_key": str(target.get("metric_selected_reset_target_key", "")),
                "reset_target_key": str(target.get("metric_selected_reset_target_key", "")),
                "original_env_config_hash": str(target.get("original_env_config_hash", "")),
                "metric_selected_env_config_hash": str(target.get("metric_selected_env_config_hash", "")),
                "env_config_hash": str(target.get("metric_selected_env_config_hash", "")),
                "soft_offtrack_metric_enabled": True,
                "soft_offtrack_tolerance_m": float(soft_offtrack_tolerance_m),
                "sensitivity_thresholds_m": str(target.get("sensitivity_thresholds_m", "")),
                "actor_contract_guardrail_pass": m2413._actor_contract_pass({**dict(spec), "env_config": metric_env_config}),
            }
        )
        specs.append(metric_spec)
    return specs


def _metric_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "original_reset_target_key": str(spec.get("original_reset_target_key", "")),
        "metric_selected_reset_target_key": str(spec.get("metric_selected_reset_target_key", "")),
        "original_env_config_hash": str(spec.get("original_env_config_hash", "")),
        "metric_selected_env_config_hash": str(spec.get("metric_selected_env_config_hash", "")),
        "soft_offtrack_metric_enabled": bool(spec.get("soft_offtrack_metric_enabled", False)),
        "soft_offtrack_tolerance_m": float(spec.get("soft_offtrack_tolerance_m", DEFAULT_SOFT_OFFTRACK_TOLERANCE_M)),
        "sensitivity_thresholds_m": str(spec.get("sensitivity_thresholds_m", "")),
    }


def metric_selected_workload_rows(
    *,
    preflight_workload_rows: Sequence[Mapping[str, Any]],
    metric_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    specs_by_index = {int(spec.get("reset_target_index", 0) or 0): spec for spec in metric_specs}
    rows: list[dict[str, Any]] = []
    for row in preflight_workload_rows:
        reset_index = int(row.get("reset_target_index", 0) or 0)
        selected_index = int(row.get("selected_checkpoint_index", 0) or 0)
        spec = specs_by_index[reset_index]
        selected = selected_rows[selected_index]
        output = dict(row)
        output.update(
            {
                "scenario_index": reset_index,
                "profile_seed": base_runner._profile_seed(selected),
                "selected_key": base_runner._selected_key(selected),
                "reset_target_key": str(spec.get("reset_target_key", "")),
                "env_config_hash": str(spec.get("env_config_hash", "")),
                "metric_selected_reset_target_key": str(spec.get("metric_selected_reset_target_key", "")),
                "metric_selected_env_config_hash": str(spec.get("metric_selected_env_config_hash", "")),
            }
        )
        rows.append(output)
    return sorted(rows, key=lambda item: (int(item["selected_checkpoint_index"]), int(item["reset_target_index"])))


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "metric_selected_measured_validation_completed",
            "admissible": True,
            "reason": "episode rows are measured rollout artifacts when M2445 completes",
        },
        {
            "claim": "actual_success_improvement",
            "admissible": False,
            "reason": "M2445 requires a later result audit before interpreting improvement",
        },
        {
            "claim": "candidate_family_ranking",
            "admissible": False,
            "reason": "family membership remains overlapping diagnostic metadata",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2445 executes a measured panel and does not rank controllers",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2445 does not select or promote a checkpoint",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2445 does not execute repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2445 does not train",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2445 is a measured-validation artifact, not a paper-level verdict",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2445 does not execute a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2445 does not run wrong-history, reset-hidden, or zero-history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2445 must be audited before a current-sim verdict",
        },
    ]


def decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "measured_policy_rollout_started",
            "decision_value": "true_if_episode_rows_exist",
            "admissible": True,
            "reason": "M2445 is the bounded measured-validation execution milestone.",
        },
        {
            "decision_key": "repair_training_ranking",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2445 measures existing selected checkpoints only.",
        },
        {
            "decision_key": "actual_success_claim",
            "decision_value": "blocked_until_result_audit",
            "admissible": False,
            "reason": "Executed rows require M2446 audit before interpretation.",
        },
        {
            "decision_key": "current_sim_verdict",
            "decision_value": "blocked_until_result_audit",
            "admissible": False,
            "reason": "M2445 does not make a current-sim verdict.",
        },
        {
            "decision_key": "next_route",
            "decision_value": DEFAULT_NEXT_BLOCKER,
            "admissible": True,
            "reason": "Audit measured-validation result before any conclusion.",
        },
    ]


def _metric_outcome_fields(row: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    tolerance = float(spec.get("soft_offtrack_tolerance_m", DEFAULT_SOFT_OFFTRACK_TOLERANCE_M))
    overshoot = max(_finite_float(row.get("max_off_track_overshoot"), default=0.0), 0.0)
    hard_offtrack = str(row.get("termination_reason", "") or "") == "off_track" or overshoot > tolerance
    actual_success = _bool(row.get("success"), default=False)
    soft_violation = bool(overshoot > 0.0 and not hard_offtrack)
    return {
        **_metric_metadata(spec),
        "metric_selected_actual_success": actual_success,
        "metric_selected_hard_offtrack_failure": hard_offtrack,
        "metric_selected_soft_offtrack_violation": soft_violation,
        "metric_selected_boundary_tolerated_success": bool(actual_success and soft_violation),
        "metric_selected_max_offtrack_overshoot_m": float(overshoot),
        "metric_selected_measured_validation": True,
    }


def measured_episode_row(
    *,
    workload_row: Mapping[str, Any],
    reset_target_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    rollout_metrics: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = m2413.measured_episode_row(
        workload_row=workload_row,
        reset_target_spec=reset_target_spec,
        selected_row=selected_row,
        rollout_metrics=rollout_metrics,
        eval_seed=int(eval_seed),
    )
    row.update(_metric_outcome_fields(row, reset_target_spec))
    row.update(
        {
            "support_policy_ranking_claim_made": False,
            "scenario_redesign_executed_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "training_repair_success_claim_made": False,
            "candidate_family_ranking_claim_made": False,
        }
    )
    return row


def measured_failure_row(
    *,
    workload_row: Mapping[str, Any],
    reset_target_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    eval_seed: int,
    error: BaseException,
) -> dict[str, Any]:
    row = m2413.measured_failure_row(
        workload_row=workload_row,
        reset_target_spec=reset_target_spec,
        selected_row=selected_row,
        eval_seed=int(eval_seed),
        error=error,
    )
    row.update(_metric_metadata(reset_target_spec))
    row["metric_selected_measured_validation"] = True
    return row


def _soft_metric_summary(episode_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(episode_rows)
    actual_success_count = sum(_bool(row.get("metric_selected_actual_success")) for row in episode_rows)
    hard_offtrack_count = sum(_bool(row.get("metric_selected_hard_offtrack_failure")) for row in episode_rows)
    soft_violation_count = sum(_bool(row.get("metric_selected_soft_offtrack_violation")) for row in episode_rows)
    boundary_tolerated_success_count = sum(
        _bool(row.get("metric_selected_boundary_tolerated_success")) for row in episode_rows
    )
    overshoots = [_finite_float(row.get("metric_selected_max_offtrack_overshoot_m")) for row in episode_rows]
    finite_overshoots = [value for value in overshoots if np.isfinite(value)]
    return {
        "metric_selected_actual_success_count": actual_success_count,
        "metric_selected_actual_success_rate": _rate(actual_success_count, total),
        "metric_selected_hard_offtrack_failure_count": hard_offtrack_count,
        "metric_selected_hard_offtrack_failure_rate": _rate(hard_offtrack_count, total),
        "metric_selected_soft_offtrack_violation_count": soft_violation_count,
        "metric_selected_soft_offtrack_violation_rate": _rate(soft_violation_count, total),
        "metric_selected_boundary_tolerated_success_count": boundary_tolerated_success_count,
        "metric_selected_boundary_tolerated_success_rate": _rate(boundary_tolerated_success_count, total),
        "metric_selected_max_offtrack_overshoot_mean": (
            float(np.mean(finite_overshoots)) if finite_overshoots else float("nan")
        ),
        "metric_selected_max_offtrack_overshoot_max": (
            float(np.max(finite_overshoots)) if finite_overshoots else float("nan")
        ),
    }


def _write_global_aggregate(output_dir: Path, episode_rows: Sequence[Mapping[str, Any]]) -> str:
    path = output_dir / "aggregate_rows.csv"
    row = m2413.base_runner.aggregate_row(episode_rows, group_axis="global", group_key="global", group_value="all")
    row.update(_soft_metric_summary(episode_rows))
    write_csv_rows(path, [row], fieldnames=list(row.keys()))
    return str(path)


def finalize_outputs(
    *,
    output_dir: Path,
    reset_target_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    workload: Sequence[Mapping[str, Any]],
    target_reset_target_count: int,
    target_selected_checkpoint_count: int,
    target_episode_count: int,
    next_blocker: str,
) -> dict[str, Any]:
    summary = m2413.finalize_outputs(
        output_dir=output_dir,
        reset_target_specs=reset_target_specs,
        selected_rows=selected_rows,
        workload=workload,
        target_reset_target_count=int(target_reset_target_count),
        target_selected_checkpoint_count=int(target_selected_checkpoint_count),
        target_episode_count=int(target_episode_count),
        next_blocker=str(next_blocker),
    )
    episode_rows = read_csv_rows(output_dir / "episode_rows.csv")
    write_csv_rows(output_dir / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(output_dir / "decision_rows.csv", decision_rows(), fieldnames=DECISION_FIELDNAMES)
    write_csv_rows(output_dir / "workload_rows.csv", workload, fieldnames=WORKLOAD_FIELDNAMES)
    aggregate_rows_path = _write_global_aggregate(output_dir, episode_rows)
    base_pass = str(summary.get("result_class", "")).endswith("_pass")
    soft_tolerance = (
        float(reset_target_specs[0].get("soft_offtrack_tolerance_m", DEFAULT_SOFT_OFFTRACK_TOLERANCE_M))
        if reset_target_specs
        else DEFAULT_SOFT_OFFTRACK_TOLERANCE_M
    )
    summary.update(
        {
            "result_class": RESULT_PASS if base_pass else RESULT_FAIL,
            "generated_at_utc": utc_timestamp(),
            "metric_selected_measured_validation": True,
            "soft_offtrack_metric_enabled": True,
            "soft_offtrack_tolerance_m": soft_tolerance,
            "source_preflight_summary": str(DEFAULT_PREFLIGHT_SUMMARY),
            "source_preflight_workload_rows": str(DEFAULT_PREFLIGHT_WORKLOAD_ROWS),
            "failure_types_observed": [] if base_pass else ["metric_artifact"],
            "actual_success_improvement_claim_made": False,
            "candidate_family_ranking_claim_made": False,
            "controller_family_ranking_claim_made": False,
            "support_policy_ranking_claim_made": False,
            "scenario_redesign_executed_claim_made": False,
            "training_repair_success_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "next_blocker": str(next_blocker),
            **_soft_metric_summary(episode_rows),
        }
    )
    artifacts = dict(summary.get("artifacts", {}))
    artifacts.update(
        {
            "workload_rows": str(output_dir / "workload_rows.csv"),
            "aggregate_rows": aggregate_rows_path,
            "decision_rows": str(output_dir / "decision_rows.csv"),
        }
    )
    summary["artifacts"] = artifacts
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_episode_count": int(target_episode_count),
            "completed_count": int(summary.get("episode_count", 0) or 0),
            "failure_count": int(summary.get("failure_count", 0) or 0),
            "complete": bool(base_pass),
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def run_metric_selected_measured_validation(
    *,
    preflight_summary_path: Path | str = DEFAULT_PREFLIGHT_SUMMARY,
    preflight_workload_rows_path: Path | str = DEFAULT_PREFLIGHT_WORKLOAD_ROWS,
    source_reset_dir: Path | str = DEFAULT_SOURCE_RESET_DIR,
    source_effective_dir: Path | str = DEFAULT_SOURCE_EFFECTIVE_DIR,
    selected_rows_path: Path | str = DEFAULT_SELECTED_ROWS,
    config_root: Path | str = DEFAULT_CONFIG_ROOT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    soft_offtrack_tolerance_m: float = DEFAULT_SOFT_OFFTRACK_TOLERANCE_M,
    target_reset_target_count: int = TARGET_RESET_TARGET_COUNT,
    target_selected_checkpoint_count: int = TARGET_SELECTED_CHECKPOINT_COUNT,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    reset_target_specs: Sequence[Mapping[str, Any]] | None = None,
    selected_rows: Sequence[Mapping[str, Any]] | None = None,
    preflight_workload_rows: Sequence[Mapping[str, Any]] | None = None,
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if preflight_workload_rows is None and not _preflight_summary_pass(preflight_summary_path):
        raise ValueError("M2443 preflight summary is not a pass")

    source_specs = (
        list(reset_target_specs)
        if reset_target_specs is not None
        else m2413.load_source_linked_reset_target_specs(
            source_reset_dir=source_reset_dir,
            source_effective_dir=source_effective_dir,
        )
    )
    selected = list(selected_rows) if selected_rows is not None else m2413.load_selected_rows(selected_rows_path)
    preflight_workload = (
        list(preflight_workload_rows)
        if preflight_workload_rows is not None
        else read_csv_rows(preflight_workload_rows_path)
    )
    metric_specs = metric_selected_reset_target_specs(
        source_specs,
        soft_offtrack_tolerance_m=float(soft_offtrack_tolerance_m),
    )
    workload = metric_selected_workload_rows(
        preflight_workload_rows=preflight_workload,
        metric_specs=metric_specs,
        selected_rows=selected,
    )

    if not resume:
        for path in output.glob("*.csv"):
            path.unlink()
        for path in (output / "summary.json", output / "run_state.json"):
            if path.exists():
                path.unlink()

    validation_failures = m2413.validation_failure_rows(
        reset_target_specs=metric_specs,
        selected_rows=selected,
        workload=workload,
        config_root=config_root,
        require_checkpoint_paths=rollout_fn is None,
    )
    if validation_failures:
        write_csv_rows(output / "validation_failure_rows.csv", validation_failures, fieldnames=VALIDATION_FAILURE_FIELDNAMES)
        write_csv_rows(output / "episode_rows.csv", [], fieldnames=EPISODE_FIELDNAMES)
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
        return finalize_outputs(
            output_dir=output,
            reset_target_specs=metric_specs,
            selected_rows=selected,
            workload=workload,
            target_reset_target_count=int(target_reset_target_count),
            target_selected_checkpoint_count=int(target_selected_checkpoint_count),
            target_episode_count=int(target_episode_count),
            next_blocker=str(next_blocker),
        )

    write_csv_rows(output / "validation_failure_rows.csv", [], fieldnames=VALIDATION_FAILURE_FIELDNAMES)
    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
    if not (output / "episode_rows.csv").exists():
        write_csv_rows(output / "episode_rows.csv", [], fieldnames=EPISODE_FIELDNAMES)

    completed = completed_workload_ids(output / "episode_rows.csv") if resume else set()
    profile_config_cache: dict[str, dict[str, Any]] = {}
    model_cache: dict[tuple[str, int], Any] = {}
    for row in workload:
        workload_id = str(row["workload_id"])
        if workload_id in completed:
            continue
        reset_target = metric_specs[int(row["reset_target_index"])]
        selected_row = selected[int(row["selected_checkpoint_index"])]
        eval_seed = int(row["eval_seed"])
        try:
            if rollout_fn is None:
                config_key = str(row["profile_config_path"])
                profile_config = profile_config_cache.get(config_key)
                if profile_config is None:
                    profile_config = read_json(config_key)
                    profile_config_cache[config_key] = profile_config
                rollout_metrics = m2413.base_runner._real_rollout_metrics(
                    workload_row=row,
                    scenario_spec=reset_target,
                    selected_row=selected_row,
                    profile_config=profile_config,
                    model_cache=model_cache,
                    device=str(device),
                    eval_seed=int(eval_seed),
                )
            else:
                rollout_metrics = dict(rollout_fn(row, reset_target, int(eval_seed)))
            episode_row = measured_episode_row(
                workload_row=row,
                reset_target_spec=reset_target,
                selected_row=selected_row,
                rollout_metrics=rollout_metrics,
                eval_seed=int(eval_seed),
            )
            append_csv_row(output / "episode_rows.csv", episode_row)
            completed.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - row failures must be preserved.
            append_csv_row(
                output / "failure_rows.csv",
                measured_failure_row(
                    workload_row=row,
                    reset_target_spec=reset_target,
                    selected_row=selected_row,
                    eval_seed=int(eval_seed),
                    error=exc,
                ),
            )
        write_run_state(
            output / "run_state.json",
            {
                "target_episode_count": int(target_episode_count),
                "completed_count": len(completed_workload_ids(output / "episode_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "latest_workload_id": workload_id,
                "complete": False,
            },
        )

    return finalize_outputs(
        output_dir=output,
        reset_target_specs=metric_specs,
        selected_rows=selected,
        workload=workload,
        target_reset_target_count=int(target_reset_target_count),
        target_selected_checkpoint_count=int(target_selected_checkpoint_count),
        target_episode_count=int(target_episode_count),
        next_blocker=str(next_blocker),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-summary", type=Path, default=DEFAULT_PREFLIGHT_SUMMARY)
    parser.add_argument("--preflight-workload-rows", type=Path, default=DEFAULT_PREFLIGHT_WORKLOAD_ROWS)
    parser.add_argument("--source-reset-dir", type=Path, default=DEFAULT_SOURCE_RESET_DIR)
    parser.add_argument("--source-effective-dir", type=Path, default=DEFAULT_SOURCE_EFFECTIVE_DIR)
    parser.add_argument("--selected-rows", type=Path, default=DEFAULT_SELECTED_ROWS)
    parser.add_argument("--config-root", type=Path, default=DEFAULT_CONFIG_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--soft-offtrack-tolerance-m", type=float, default=DEFAULT_SOFT_OFFTRACK_TOLERANCE_M)
    parser.add_argument("--target-reset-target-count", type=int, default=TARGET_RESET_TARGET_COUNT)
    parser.add_argument("--target-selected-checkpoint-count", type=int, default=TARGET_SELECTED_CHECKPOINT_COUNT)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_metric_selected_measured_validation(
        preflight_summary_path=args.preflight_summary,
        preflight_workload_rows_path=args.preflight_workload_rows,
        source_reset_dir=args.source_reset_dir,
        source_effective_dir=args.source_effective_dir,
        selected_rows_path=args.selected_rows,
        config_root=args.config_root,
        output_dir=args.output_dir,
        soft_offtrack_tolerance_m=float(args.soft_offtrack_tolerance_m),
        target_reset_target_count=int(args.target_reset_target_count),
        target_selected_checkpoint_count=int(args.target_selected_checkpoint_count),
        target_episode_count=int(args.target_episode_count),
        device=str(args.device),
        resume=not bool(args.no_resume),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"source_reset_target_count={summary['source_reset_target_count']}")
    print(f"selected_checkpoint_count={summary['selected_checkpoint_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"validation_failure_count={summary['validation_failure_count']}")
    print(f"metric_completeness_failure_count={summary['metric_completeness_failure_count']}")
    print(f"actor_contract_violation_count={summary['actor_contract_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    print(f"metric_selected_actual_success_rate={summary['metric_selected_actual_success_rate']}")
    print(f"metric_selected_hard_offtrack_failure_rate={summary['metric_selected_hard_offtrack_failure_rate']}")
    print(f"metric_selected_soft_offtrack_violation_rate={summary['metric_selected_soft_offtrack_violation_rate']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
