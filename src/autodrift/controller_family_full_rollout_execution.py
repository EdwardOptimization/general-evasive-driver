"""Resumable full public rollout execution for controller-family profiles."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_measured_routing_smoke import (
    SELECTED_METRICS,
    assert_human_view_env_contract,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import ActorPolicy, run_episode_with_policy


DEFAULT_EXECUTABLE_SPECS = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json"
)
DEFAULT_EXECUTABLE_WORKLOAD = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv"
)
DEFAULT_RUN_DIR = Path("runs/m1693_controller_family_full_rollout_execution")
DEFAULT_EVAL_SEED_BASE = 169300
TARGET_EPISODE_COUNT = 864
TARGET_PROFILE_COUNT = 12
TARGET_SPEC_COUNT = 72
SUMMARY_SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
FAILURE_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "error_type",
    "error_message",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
]
FORBIDDEN_GUARDRAILS = (
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_csv_row(path: Path | str, row: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        with output.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            try:
                fieldnames = next(reader)
            except StopIteration:
                fieldnames = list(row.keys())
            if not fieldnames:
                fieldnames = list(row.keys())
                mode = "w"
                write_header = True
            else:
                mode = "a"
                write_header = False
    else:
        fieldnames = list(row.keys())
        mode = "w"
        write_header = True
    with output.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def load_executable_specs(path: Path | str = DEFAULT_EXECUTABLE_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    specs = list(payload["executable_task_specs"])
    return sorted(specs, key=lambda row: str(row["task_source_id"]))


def load_executable_workload(path: Path | str = DEFAULT_EXECUTABLE_WORKLOAD) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    return sorted(rows, key=lambda row: str(row["workload_id"]))


def env_config_for_executable_profile(
    *,
    executable_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
) -> DriftEnvConfig:
    env_data = dict(executable_spec["env_config"])
    profile_env = dict(profile_config.get("env") or {})
    env_data["history_length"] = int(profile_env.get("history_length", env_data["history_length"]))
    env_data["action_history_mode"] = "full"
    env_data["include_privileged_params"] = False
    env_data["obstacle_relative_velocity_mode"] = "zero"
    env_data["wheel_observation_mode"] = "none"
    env_config = build_env_config(env_data)
    assert_human_view_env_contract(env_config)
    return env_config


def profile_index(profile_name: str, profile_rows: list[Mapping[str, Any]]) -> int:
    names = [str(row["profile_name"]) for row in profile_rows]
    return names.index(profile_name)


def _load_profile_cache(profile_rows: list[Mapping[str, Any]], *, device: str) -> dict[str, tuple[dict[str, Any], Any]]:
    cache: dict[str, tuple[dict[str, Any], Any]] = {}
    for row in profile_rows:
        config = read_json(row["config_path"])
        model, _ = load_actor_critic_checkpoint(row["checkpoint_path"], device=device)
        cache[str(row["profile_name"])] = (config, model)
    return cache


def run_workload_cell(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: dict[str, Any],
    model: Any,
    profile_row: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_config)
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    target_obs_dim = int(env.observation_space.shape[0])
    model_obs_dim = int(getattr(model, "obs_dim", -1))
    if model_obs_dim != target_obs_dim:
        env.close()
        raise ValueError(
            f"profile {workload_row['profile_name']} checkpoint obs_dim {model_obs_dim} "
            f"does not match task env obs_dim {target_obs_dim}"
        )
    runtime = profile_runtime_summary(profile_config)
    policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
    try:
        row = run_episode_with_policy(env, policy, "checkpoint", int(eval_seed))
    finally:
        env.close()

    row.update(
        {
            "workload_id": str(workload_row["workload_id"]),
            "task_source_id": str(workload_row["task_source_id"]),
            "profile_name": str(workload_row["profile_name"]),
            "task_family": str(workload_row["task_family"]),
            "source_edge": str(workload_row["source_edge"]),
            "window_tag": str(workload_row["window_tag"]),
            "strata": str(workload_row["strata"]),
            "executable_source_family": str(workload_row["executable_source_family"]),
            "env_template_family": str(workload_row["env_template_family"]),
            "profile_config_path": str(profile_row["config_path"]),
            "checkpoint_path": str(profile_row["checkpoint_path"]),
            "profile_env_history_length": int(env_config.history_length),
            "eval_seed": int(eval_seed),
            "routing_smoke_only": False,
            "full_rollout_execution": True,
            "private_holdout_used": False,
            "promoted": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
            "actor_input_contract_changed": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }
    )
    row["success"] = bool(row.get("obstacle_completed", False)) and not bool(row.get("collision", False))
    return row


def _float_values(rows: Iterable[Mapping[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        try:
            value = float(row.get(key, float("nan")))
        except (TypeError, ValueError):
            value = float("nan")
        if np.isfinite(value):
            values.append(value)
    return values


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _episode_success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool_value(row.get("success"))
    return _bool_value(row.get("obstacle_completed", False)) and not _bool_value(row.get("collision", False))


def _metric_value(row: Mapping[str, Any], metric: str) -> float:
    if metric == "success":
        return float(_episode_success(row))
    if metric == "collision":
        return float(_bool_value(row.get("collision", False)))
    try:
        return float(row.get(metric, float("nan")))
    except (TypeError, ValueError):
        return float("nan")


def selected_metrics_are_finite(rows: Iterable[Mapping[str, Any]]) -> bool:
    for row in rows:
        for metric in SELECTED_METRICS:
            if not np.isfinite(_metric_value(row, metric)):
                return False
    return True


def aggregate_rows(rows: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[group_key])].append(row)

    aggregates: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        margins = [_metric_value(row, "min_clearance_margin") for row in group]
        aggregate = {
            group_key: key,
            "episode_count": len(group),
            "success_rate": float(np.mean([_metric_value(row, "success") for row in group])),
            "collision_rate": float(np.mean([_metric_value(row, "collision") for row in group])),
            "clearance_margin_mean": float(np.mean(margins)),
            "clearance_margin_p10": float(np.percentile(margins, 10.0)),
            "return_mean": float(np.mean([_metric_value(row, "return") for row in group])),
            "steps_mean": float(np.mean([_metric_value(row, "steps") for row in group])),
            "control_smoothness": float(np.mean([_metric_value(row, "action_rate_mean") for row in group])),
            "spin_or_unstable_rate": float(
                np.mean([_metric_value(row, "high_sideslip_fraction") > 0.5 for row in group])
            ),
            "failure_rate": 0.0,
            "all_selected_metrics_finite": selected_metrics_are_finite(group),
        }
        if group_key != "profile_name":
            aggregate["task_family"] = group[0].get("task_family", "")
            aggregate["source_family"] = group[0].get("executable_source_family", "")
        aggregates.append(aggregate)
    return aggregates


def aggregate_stratum_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for row in rows:
        for stratum in str(row.get("strata", "")).split(";"):
            if not stratum:
                continue
            item = dict(row)
            item["stratum"] = stratum
            expanded.append(item)
    return aggregate_rows(expanded, "stratum")


def aggregate_profile_outcome_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["profile_outcome"] = f"{row.get('profile_name', '')}::{row.get('outcome_bucket', '')}"
        expanded.append(item)
    return aggregate_rows(expanded, "profile_outcome")


def metric_summary(rows: list[Mapping[str, Any]], label: str) -> dict[str, Any]:
    margins = _float_values(rows, "min_clearance_margin")
    return {
        "group": label,
        "episode_count": len(rows),
        "success_rate": float(np.mean([_episode_success(row) for row in rows])) if rows else float("nan"),
        "collision_rate": float(np.mean([_bool_value(row.get("collision", False)) for row in rows])) if rows else float("nan"),
        "clearance_margin_mean": float(np.mean(margins)) if margins else float("nan"),
        "return_mean": float(np.mean(_float_values(rows, "return"))) if rows else float("nan"),
    }


def comparison_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def by_profile(name: str) -> list[dict[str, Any]]:
        return [row for row in rows if row.get("profile_name") == name]

    def diff_row(
        name: str,
        left_label: str,
        left: list[dict[str, Any]],
        right_label: str,
        right: list[dict[str, Any]],
    ) -> dict:
        left_summary = metric_summary(left, left_label)
        right_summary = metric_summary(right, right_label)
        return {
            "comparison": name,
            "left_group": left_label,
            "right_group": right_label,
            "left_episode_count": left_summary["episode_count"],
            "right_episode_count": right_summary["episode_count"],
            "success_rate_delta": float(left_summary["success_rate"]) - float(right_summary["success_rate"]),
            "collision_rate_delta": float(left_summary["collision_rate"]) - float(right_summary["collision_rate"]),
            "clearance_margin_mean_delta": float(left_summary["clearance_margin_mean"])
            - float(right_summary["clearance_margin_mean"]),
            "return_mean_delta": float(left_summary["return_mean"]) - float(right_summary["return_mean"]),
            "diagnostic_only_no_ranking_claim": True,
        }

    def stratum_rows(name: str) -> list[dict[str, Any]]:
        return [row for row in rows if name in str(row.get("strata", "")).split(";")]

    comparisons: list[dict[str, Any]] = []
    for window in ("13", "25", "50", "100"):
        comparisons.append(
            diff_row(
                f"L2_window_{window}_normal_minus_current_tiled",
                f"L2_window_{window}",
                by_profile(f"L2_window_{window}"),
                f"L2_window_{window}_current_tiled",
                by_profile(f"L2_window_{window}_current_tiled"),
            )
        )
    comparisons.append(
        diff_row(
            "L3_online_minus_L3_reset_control",
            "L3_online_gru",
            by_profile("L3_online_gru"),
            "L3_reset_control_corrected",
            by_profile("L3_reset_control_corrected"),
        )
    )
    l2_profiles = [row for row in rows if str(row.get("profile_name", "")).startswith("L2_window_")]
    l2_normal_names = ("L2_window_13", "L2_window_25", "L2_window_50", "L2_window_100")
    l2_normal_groups = [(name, by_profile(name)) for name in l2_normal_names]
    best_l2_name, best_l2_rows = max(
        l2_normal_groups,
        key=lambda item: (
            metric_summary(item[1], item[0])["success_rate"],
            metric_summary(item[1], item[0])["clearance_margin_mean"],
            metric_summary(item[1], item[0])["return_mean"],
        ),
    )
    l1_rows = by_profile("L1_one_step")
    l3_rows = by_profile("L3_online_gru")
    comparisons.append(
        diff_row("L3_online_minus_best_L2_normal", "L3_online_gru", l3_rows, best_l2_name, best_l2_rows)
    )
    comparisons.append(diff_row("L3_online_minus_all_L2", "L3_online_gru", l3_rows, "all_L2", l2_profiles))
    comparisons.append(diff_row("L1_one_step_minus_history_capable", "L1_one_step", l1_rows, "L2_L3", l2_profiles + l3_rows))
    comparisons.append(
        diff_row(
            "task_family_T4_minus_T5",
            "T4",
            [row for row in rows if row.get("task_family") == "T4"],
            "T5",
            [row for row in rows if row.get("task_family") == "T5"],
        )
    )
    comparisons.append(
        diff_row(
            "explicit_window_subset_minus_all_72_specs",
            "explicit_window_subset",
            stratum_rows("explicit_window_subset"),
            "all_72_specs",
            stratum_rows("all_72_specs"),
        )
    )
    comparisons.append(
        diff_row(
            "mapping_window_unspecified_minus_all_72_specs",
            "mapping_window_unspecified",
            stratum_rows("mapping_window_unspecified"),
            "all_72_specs",
            stratum_rows("all_72_specs"),
        )
    )
    return comparisons


def completed_workload_ids(episode_rows_path: Path | str) -> set[str]:
    return {str(row["workload_id"]) for row in read_csv_rows(episode_rows_path) if row.get("workload_id")}


def write_run_state(path: Path | str, state: Mapping[str, Any]) -> None:
    write_json(path, {**dict(state), "updated_at_utc": utc_timestamp()})


def finalize_outputs(
    *,
    output_dir: Path,
    target_workload_count: int,
    next_blocker: str = "m1694-paper-route-controller-family-full-rollout-result-audit",
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)

    profile_aggregate = aggregate_rows(episode_rows, "profile_name") if episode_rows else []
    spec_aggregate = aggregate_rows(episode_rows, "task_source_id") if episode_rows else []
    stratum_aggregate = aggregate_stratum_rows(episode_rows) if episode_rows else []
    outcome_aggregate = aggregate_rows(episode_rows, "outcome_bucket") if episode_rows and "outcome_bucket" in episode_rows[0] else []
    termination_reason_aggregate = (
        aggregate_rows(episode_rows, "termination_reason")
        if episode_rows and "termination_reason" in episode_rows[0]
        else []
    )
    profile_outcome_aggregate = (
        aggregate_profile_outcome_rows(episode_rows)
        if episode_rows and "outcome_bucket" in episode_rows[0]
        else []
    )
    comparisons = comparison_rows(episode_rows) if episode_rows else []
    write_csv_rows(output_dir / "profile_aggregate.csv", profile_aggregate)
    write_csv_rows(output_dir / "spec_aggregate.csv", spec_aggregate)
    write_csv_rows(output_dir / "stratum_aggregate.csv", stratum_aggregate)
    write_csv_rows(output_dir / "outcome_aggregate.csv", outcome_aggregate)
    write_csv_rows(output_dir / "termination_reason_aggregate.csv", termination_reason_aggregate)
    write_csv_rows(output_dir / "profile_outcome_aggregate.csv", profile_outcome_aggregate)
    write_csv_rows(output_dir / "comparison_aggregate.csv", comparisons)

    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    summary = {
        "result_class": "controller_family_full_rollout_execution_pass"
        if (
            len(episode_rows) == target_workload_count
            and not failure_rows
            and all_selected_metrics_finite
            and guardrail_violation_count == 0
        )
        else "controller_family_full_rollout_execution_incomplete_or_fail",
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": target_workload_count,
        "profile_count": len({row["profile_name"] for row in episode_rows}) if episode_rows else 0,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "spec_count": len({row["task_source_id"] for row in episode_rows}) if episode_rows else 0,
        "target_spec_count": TARGET_SPEC_COUNT,
        "failure_count": len(failure_rows),
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        "profile_aggregate_rows": len(profile_aggregate),
        "spec_aggregate_rows": len(spec_aggregate),
        "stratum_aggregate_rows": len(stratum_aggregate),
        "comparison_aggregate_rows": len(comparisons),
        "outcome_aggregate_rows": len(outcome_aggregate),
        "termination_reason_aggregate_rows": len(termination_reason_aggregate),
        "profile_outcome_aggregate_rows": len(profile_outcome_aggregate),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": bool(episode_rows or failure_rows),
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output_dir / "summary.json"),
            "episode_rows": str(output_dir / "episode_rows.csv"),
            "profile_aggregate": str(output_dir / "profile_aggregate.csv"),
            "spec_aggregate": str(output_dir / "spec_aggregate.csv"),
            "stratum_aggregate": str(output_dir / "stratum_aggregate.csv"),
            "comparison_aggregate": str(output_dir / "comparison_aggregate.csv"),
            "outcome_aggregate": str(output_dir / "outcome_aggregate.csv"),
            "termination_reason_aggregate": str(output_dir / "termination_reason_aggregate.csv"),
            "profile_outcome_aggregate": str(output_dir / "profile_outcome_aggregate.csv"),
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_workload_count": target_workload_count,
            "completed_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "complete": len(episode_rows) == target_workload_count and not failure_rows,
        },
    )
    return summary


def run_full_rollout_execution(
    *,
    output_dir: Path | str = DEFAULT_RUN_DIR,
    executable_specs_path: Path | str = DEFAULT_EXECUTABLE_SPECS,
    workload_path: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = "m1694-paper-route-controller-family-full-rollout-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in executable_specs}
    workload_rows = load_executable_workload(workload_path)
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    profile_by_name = {str(row["profile_name"]): row for row in profile_rows}
    profile_cache = _load_profile_cache(profile_rows, device=device)
    completed = completed_workload_ids(output / "episode_rows.csv") if resume else set()
    if not resume:
        for path in (
            output / "episode_rows.csv",
            output / "failure_rows.csv",
            output / "summary.json",
            output / "run_state.json",
            output / "profile_aggregate.csv",
            output / "spec_aggregate.csv",
            output / "stratum_aggregate.csv",
            output / "comparison_aggregate.csv",
            output / "outcome_aggregate.csv",
            output / "termination_reason_aggregate.csv",
            output / "profile_outcome_aggregate.csv",
        ):
            if path.exists():
                path.unlink()
        completed = set()

    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)

    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in completed:
            continue
        profile_name = str(workload_row["profile_name"])
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            profile_config, model = profile_cache[profile_name]
            row = run_workload_cell(
                workload_row=workload_row,
                executable_spec=spec_by_id[str(workload_row["task_source_id"])],
                profile_config=profile_config,
                model=model,
                profile_row=profile_by_name[profile_name],
                eval_seed=eval_seed,
            )
            append_csv_row(output / "episode_rows.csv", row)
            completed.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - rollout must preserve failures as rows.
            failure_row = {
                "workload_id": workload_id,
                "task_source_id": str(workload_row.get("task_source_id", "")),
                "profile_name": profile_name,
                "task_family": str(workload_row.get("task_family", "")),
                "source_edge": str(workload_row.get("source_edge", "")),
                "window_tag": str(workload_row.get("window_tag", "")),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "training_started": False,
                "replay_started": False,
                "ppo_used": False,
                "promoted": False,
                "private_holdout_used": False,
                "actor_input_contract_changed": False,
            }
            append_csv_row(output / "failure_rows.csv", failure_row)
        write_run_state(
            output / "run_state.json",
            {
                "target_workload_count": len(workload_rows),
                "completed_count": len(completed_workload_ids(output / "episode_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "latest_workload_id": workload_id,
                "complete": False,
            },
        )

    return finalize_outputs(output_dir=output, target_workload_count=len(workload_rows), next_blocker=next_blocker)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run resumable full controller-family public rollout.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default="m1694-paper-route-controller-family-full-rollout-result-audit")
    args = parser.parse_args()

    summary = run_full_rollout_execution(
        output_dir=args.output_dir,
        executable_specs_path=args.executable_specs,
        workload_path=args.workload,
        m1674_run_dir=args.m1674_run_dir,
        eval_seed_base=int(args.eval_seed_base),
        device=str(args.device),
        resume=not bool(args.no_resume),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
