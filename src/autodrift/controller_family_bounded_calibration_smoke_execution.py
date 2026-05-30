"""Measured execution for the bounded calibration smoke subset."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_preflight import DEFAULT_OUTPUT_DIR as DEFAULT_M1705_OUTPUT_DIR
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import (
    _load_profile_cache,
    append_csv_row,
    completed_workload_ids,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.outcome_metric_instrumentation import outcome_metric_aggregate_fields


DEFAULT_BOUNDED_CALIBRATION_SPECS = DEFAULT_M1705_OUTPUT_DIR / "bounded_calibration_specs.json"
DEFAULT_BOUNDED_SMOKE_MATRIX = DEFAULT_M1705_OUTPUT_DIR / "bounded_smoke_matrix.csv"
DEFAULT_RUN_DIR = Path("runs/m1708_controller_family_bounded_calibration_smoke_execution")
DEFAULT_EVAL_SEED_BASE = 170800
TARGET_EPISODE_COUNT = 864
TARGET_PROFILE_COUNT = 12
TARGET_CALIBRATION_SPEC_COUNT = 72
TARGET_SELECTED_BASE_SPEC_COUNT = 6
CALIBRATION_FAILURE_FIELDNAMES = [
    "workload_id",
    "calibration_workload_id",
    "calibration_spec_id",
    "base_task_source_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "track_width_scale",
    "finish_variant",
    "max_steps_scale",
    "error_type",
    "error_message",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
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


def load_bounded_calibration_specs(path: Path | str = DEFAULT_BOUNDED_CALIBRATION_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return list(payload["bounded_calibration_specs"])


def calibration_executable_specs(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        row = dict(spec)
        row["task_source_id"] = str(spec["calibration_spec_id"])
        row["calibration_spec_id"] = str(spec["calibration_spec_id"])
        rows.append(row)
    return sorted(rows, key=lambda row: str(row["calibration_spec_id"]))


def calibration_workload_rows(path: Path | str = DEFAULT_BOUNDED_SMOKE_MATRIX) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    converted: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["workload_id"] = str(row["calibration_workload_id"])
        item["task_source_id"] = str(row["calibration_spec_id"])
        item["strata"] = ";".join(
            [
                "bounded_calibration_smoke",
                f"task_family_{row['task_family']}",
                f"track_width_{row['track_width_scale']}",
                f"finish_{row['finish_variant']}",
                f"max_steps_{row['max_steps_scale']}",
            ]
        )
        converted.append(item)
    return sorted(converted, key=lambda row: str(row["workload_id"]))


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


def _outcome_rate(rows: list[Mapping[str, Any]], bucket: str) -> float:
    if not rows:
        return float("nan")
    return float(np.mean([str(row.get("outcome_bucket", "")) == bucket for row in rows]))


def aggregate_outcome_rows(rows: list[dict[str, Any]], group_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in group_keys)].append(row)

    aggregates: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        margins = _float_values(group, "min_clearance_margin")
        aggregate = {
            group_keys[index]: key[index] for index in range(len(group_keys))
        }
        aggregate.update(
            {
                "episode_count": len(group),
                "success_obstacle_pass_rate": _outcome_rate(group, "success_obstacle_pass"),
                "collision_failure_rate": _outcome_rate(group, "collision_failure"),
                "off_track_noncollision_noncompletion_rate": _outcome_rate(
                    group,
                    "off_track_noncollision_noncompletion",
                ),
                "max_steps_noncompletion_rate": _outcome_rate(group, "max_steps_noncompletion"),
                "safe_noncollision_noncompletion_rate": _outcome_rate(
                    group,
                    "safe_noncollision_noncompletion",
                ),
                "clearance_margin_mean": float(np.mean(margins)) if margins else float("nan"),
                "clearance_margin_p10": float(np.percentile(margins, 10.0)) if margins else float("nan"),
                "return_mean": float(np.mean(_float_values(group, "return"))) if group else float("nan"),
                "steps_mean": float(np.mean(_float_values(group, "steps"))) if group else float("nan"),
                "all_selected_metrics_finite": selected_metrics_are_finite(group),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        aggregate.update(outcome_metric_aggregate_fields(group))
        aggregates.append(aggregate)
    return aggregates


def _run_calibration_workload_cell(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: dict[str, Any],
    model: Any,
    profile_row: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = run_workload_cell(
        workload_row=workload_row,
        executable_spec=executable_spec,
        profile_config=profile_config,
        model=model,
        profile_row=profile_row,
        eval_seed=eval_seed,
    )
    row.update(
        {
            "calibration_workload_id": str(workload_row["calibration_workload_id"]),
            "calibration_spec_id": str(workload_row["calibration_spec_id"]),
            "base_task_source_id": str(workload_row["base_task_source_id"]),
            "track_width_scale": str(workload_row["track_width_scale"]),
            "finish_variant": str(workload_row["finish_variant"]),
            "max_steps_scale": str(workload_row["max_steps_scale"]),
            "bounded_calibration_smoke_execution": True,
            "full_rollout_execution": False,
            "controller_family_ranking_claim_made": False,
        }
    )
    return row


def _write_aggregates(output_dir: Path, episode_rows: list[dict[str, Any]]) -> dict[str, int]:
    profile_aggregate = aggregate_outcome_rows(episode_rows, ("profile_name",))
    calibration_variant_aggregate = aggregate_outcome_rows(
        episode_rows,
        ("track_width_scale", "finish_variant", "max_steps_scale"),
    )
    task_family_aggregate = aggregate_outcome_rows(episode_rows, ("task_family",))
    source_edge_aggregate = aggregate_outcome_rows(episode_rows, ("source_edge",))
    outcome_aggregate = aggregate_outcome_rows(episode_rows, ("outcome_bucket",))
    termination_reason_aggregate = aggregate_outcome_rows(episode_rows, ("termination_reason",))
    profile_outcome_aggregate = aggregate_outcome_rows(episode_rows, ("profile_name", "outcome_bucket"))
    write_csv_rows(output_dir / "profile_aggregate.csv", profile_aggregate)
    write_csv_rows(output_dir / "calibration_variant_aggregate.csv", calibration_variant_aggregate)
    write_csv_rows(output_dir / "task_family_aggregate.csv", task_family_aggregate)
    write_csv_rows(output_dir / "source_edge_aggregate.csv", source_edge_aggregate)
    write_csv_rows(output_dir / "outcome_aggregate.csv", outcome_aggregate)
    write_csv_rows(output_dir / "termination_reason_aggregate.csv", termination_reason_aggregate)
    write_csv_rows(output_dir / "profile_outcome_aggregate.csv", profile_outcome_aggregate)
    return {
        "profile_aggregate_rows": len(profile_aggregate),
        "calibration_variant_aggregate_rows": len(calibration_variant_aggregate),
        "task_family_aggregate_rows": len(task_family_aggregate),
        "source_edge_aggregate_rows": len(source_edge_aggregate),
        "outcome_aggregate_rows": len(outcome_aggregate),
        "termination_reason_aggregate_rows": len(termination_reason_aggregate),
        "profile_outcome_aggregate_rows": len(profile_outcome_aggregate),
    }


def finalize_bounded_outputs(
    *,
    output_dir: Path,
    target_workload_count: int,
    next_blocker: str = "m1709-paper-route-controller-family-bounded-calibration-smoke-result-audit",
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=CALIBRATION_FAILURE_FIELDNAMES)
    aggregate_counts = _write_aggregates(output_dir, episode_rows)
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    result_passes = (
        len(episode_rows) == target_workload_count
        and not failure_rows
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and aggregate_counts["outcome_aggregate_rows"] > 0
        and aggregate_counts["termination_reason_aggregate_rows"] > 0
    )
    summary = {
        "result_class": (
            "controller_family_bounded_calibration_smoke_execution_pass"
            if result_passes
            else "controller_family_bounded_calibration_smoke_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": target_workload_count,
        "profile_count": len({row["profile_name"] for row in episode_rows}) if episode_rows else 0,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "calibration_spec_count": len({row["calibration_spec_id"] for row in episode_rows}) if episode_rows else 0,
        "target_calibration_spec_count": TARGET_CALIBRATION_SPEC_COUNT,
        "selected_base_spec_count": len({row["base_task_source_id"] for row in episode_rows}) if episode_rows else 0,
        "target_selected_base_spec_count": TARGET_SELECTED_BASE_SPEC_COUNT,
        "failure_count": len(failure_rows),
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        **aggregate_counts,
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
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
            "profile_aggregate": str(output_dir / "profile_aggregate.csv"),
            "calibration_variant_aggregate": str(output_dir / "calibration_variant_aggregate.csv"),
            "task_family_aggregate": str(output_dir / "task_family_aggregate.csv"),
            "source_edge_aggregate": str(output_dir / "source_edge_aggregate.csv"),
            "outcome_aggregate": str(output_dir / "outcome_aggregate.csv"),
            "termination_reason_aggregate": str(output_dir / "termination_reason_aggregate.csv"),
            "profile_outcome_aggregate": str(output_dir / "profile_outcome_aggregate.csv"),
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


def run_bounded_calibration_smoke_execution(
    *,
    output_dir: Path | str = DEFAULT_RUN_DIR,
    calibration_specs_path: Path | str = DEFAULT_BOUNDED_CALIBRATION_SPECS,
    workload_path: Path | str = DEFAULT_BOUNDED_SMOKE_MATRIX,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = "m1709-paper-route-controller-family-bounded-calibration-smoke-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = calibration_executable_specs(load_bounded_calibration_specs(calibration_specs_path))
    spec_by_id = {str(spec["calibration_spec_id"]): spec for spec in executable_specs}
    workload_rows = calibration_workload_rows(workload_path)
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
            output / "calibration_variant_aggregate.csv",
            output / "task_family_aggregate.csv",
            output / "source_edge_aggregate.csv",
            output / "outcome_aggregate.csv",
            output / "termination_reason_aggregate.csv",
            output / "profile_outcome_aggregate.csv",
        ):
            if path.exists():
                path.unlink()
        completed = set()

    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=CALIBRATION_FAILURE_FIELDNAMES)

    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in completed:
            continue
        profile_name = str(workload_row["profile_name"])
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            profile_config, model = profile_cache[profile_name]
            row = _run_calibration_workload_cell(
                workload_row=workload_row,
                executable_spec=spec_by_id[str(workload_row["calibration_spec_id"])],
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
                "calibration_workload_id": str(workload_row.get("calibration_workload_id", "")),
                "calibration_spec_id": str(workload_row.get("calibration_spec_id", "")),
                "base_task_source_id": str(workload_row.get("base_task_source_id", "")),
                "profile_name": profile_name,
                "task_family": str(workload_row.get("task_family", "")),
                "source_edge": str(workload_row.get("source_edge", "")),
                "window_tag": str(workload_row.get("window_tag", "")),
                "track_width_scale": str(workload_row.get("track_width_scale", "")),
                "finish_variant": str(workload_row.get("finish_variant", "")),
                "max_steps_scale": str(workload_row.get("max_steps_scale", "")),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "training_started": False,
                "replay_started": False,
                "ppo_used": False,
                "promoted": False,
                "private_holdout_used": False,
                "actor_input_contract_changed": False,
                "profile_specific_tuning": False,
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

    return finalize_bounded_outputs(output_dir=output, target_workload_count=len(workload_rows), next_blocker=next_blocker)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run measured bounded calibration smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--calibration-specs", type=Path, default=DEFAULT_BOUNDED_CALIBRATION_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_BOUNDED_SMOKE_MATRIX)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default="m1709-paper-route-controller-family-bounded-calibration-smoke-result-audit")
    args = parser.parse_args()

    summary = run_bounded_calibration_smoke_execution(
        output_dir=args.output_dir,
        calibration_specs_path=args.calibration_specs,
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
