"""Measured execution for the off-track repair panel subset."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_execution import (
    FORBIDDEN_GUARDRAILS,
    aggregate_outcome_rows,
    calibration_executable_specs,
)
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
from autodrift.controller_family_off_track_repair_panel_preflight import (
    DEFAULT_OUTPUT_DIR as DEFAULT_M1721_OUTPUT_DIR,
    REPAIR_VARIANT_PANEL,
)


DEFAULT_REPAIR_PANEL_SPECS = DEFAULT_M1721_OUTPUT_DIR / "repair_panel_specs.json"
DEFAULT_REPAIR_PANEL_MATRIX = DEFAULT_M1721_OUTPUT_DIR / "repair_panel_matrix.csv"
DEFAULT_RUN_DIR = Path("runs/m1724_off_track_repair_panel_execution")
DEFAULT_EVAL_SEED_BASE = 172400
TARGET_EPISODE_COUNT = 864
TARGET_PROFILE_COUNT = 12
TARGET_REPAIR_PANEL_SPEC_COUNT = 72
TARGET_SELECTED_BASE_SPEC_COUNT = 18
TARGET_REPAIR_VARIANT_COUNT = 4
EXPECTED_REPAIR_VARIANT_LABELS = tuple(str(row["repair_variant_label"]) for row in REPAIR_VARIANT_PANEL)
REPAIR_PANEL_FAILURE_FIELDNAMES = [
    "workload_id",
    "repair_panel_workload_id",
    "calibration_workload_id",
    "calibration_spec_id",
    "repair_variant_label",
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
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]


def load_repair_panel_specs(path: Path | str = DEFAULT_REPAIR_PANEL_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return list(payload["repair_panel_specs"])


def repair_panel_executable_specs(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return calibration_executable_specs(specs)


def repair_panel_workload_rows(path: Path | str = DEFAULT_REPAIR_PANEL_MATRIX) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    converted: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["workload_id"] = str(row["repair_panel_workload_id"])
        item["task_source_id"] = str(row["calibration_spec_id"])
        item["strata"] = ";".join(
            [
                "off_track_repair_panel",
                f"task_family_{row['task_family']}",
                f"variant_{row['repair_variant_label']}",
                f"track_width_{row['track_width_scale']}",
                f"finish_{row['finish_variant']}",
                f"max_steps_{row['max_steps_scale']}",
            ]
        )
        converted.append(item)
    return sorted(converted, key=lambda row: str(row["workload_id"]))


def _run_repair_panel_workload_cell(
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
            "repair_panel_workload_id": str(workload_row["repair_panel_workload_id"]),
            "calibration_workload_id": str(workload_row["calibration_workload_id"]),
            "calibration_spec_id": str(workload_row["calibration_spec_id"]),
            "repair_variant_label": str(workload_row["repair_variant_label"]),
            "base_task_source_id": str(workload_row["base_task_source_id"]),
            "track_width_scale": str(workload_row["track_width_scale"]),
            "finish_variant": str(workload_row["finish_variant"]),
            "max_steps_scale": str(workload_row["max_steps_scale"]),
            "off_track_repair_panel_execution": True,
            "calibrated_scale_up_execution": False,
            "bounded_calibration_smoke_execution": False,
            "full_rollout_execution": False,
            "controller_family_ranking_claim_made": False,
        }
    )
    return row


def _write_repair_panel_aggregates(output_dir: Path, episode_rows: list[dict[str, Any]]) -> dict[str, int]:
    profile_aggregate = aggregate_outcome_rows(episode_rows, ("profile_name",))
    repair_variant_aggregate = aggregate_outcome_rows(episode_rows, ("repair_variant_label",))
    task_family_aggregate = aggregate_outcome_rows(episode_rows, ("task_family",))
    source_edge_aggregate = aggregate_outcome_rows(episode_rows, ("source_edge",))
    outcome_aggregate = aggregate_outcome_rows(episode_rows, ("outcome_bucket",))
    termination_reason_aggregate = aggregate_outcome_rows(episode_rows, ("termination_reason",))
    profile_outcome_aggregate = aggregate_outcome_rows(episode_rows, ("profile_name", "outcome_bucket"))
    write_csv_rows(output_dir / "profile_aggregate.csv", profile_aggregate)
    write_csv_rows(output_dir / "repair_variant_aggregate.csv", repair_variant_aggregate)
    write_csv_rows(output_dir / "task_family_aggregate.csv", task_family_aggregate)
    write_csv_rows(output_dir / "source_edge_aggregate.csv", source_edge_aggregate)
    write_csv_rows(output_dir / "outcome_aggregate.csv", outcome_aggregate)
    write_csv_rows(output_dir / "termination_reason_aggregate.csv", termination_reason_aggregate)
    write_csv_rows(output_dir / "profile_outcome_aggregate.csv", profile_outcome_aggregate)
    return {
        "profile_aggregate_rows": len(profile_aggregate),
        "repair_variant_aggregate_rows": len(repair_variant_aggregate),
        "task_family_aggregate_rows": len(task_family_aggregate),
        "source_edge_aggregate_rows": len(source_edge_aggregate),
        "outcome_aggregate_rows": len(outcome_aggregate),
        "termination_reason_aggregate_rows": len(termination_reason_aggregate),
        "profile_outcome_aggregate_rows": len(profile_outcome_aggregate),
    }


def finalize_repair_panel_outputs(
    *,
    output_dir: Path,
    target_workload_count: int,
    next_blocker: str = "m1725-paper-route-controller-family-off-track-repair-panel-result-audit",
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=REPAIR_PANEL_FAILURE_FIELDNAMES)
    aggregate_counts = _write_repair_panel_aggregates(output_dir, episode_rows)
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    repair_variant_labels = {str(row["repair_variant_label"]) for row in episode_rows} if episode_rows else set()
    result_passes = (
        len(episode_rows) == target_workload_count
        and not failure_rows
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and repair_variant_labels == set(EXPECTED_REPAIR_VARIANT_LABELS)
        and aggregate_counts["repair_variant_aggregate_rows"] == TARGET_REPAIR_VARIANT_COUNT
        and aggregate_counts["outcome_aggregate_rows"] > 0
        and aggregate_counts["termination_reason_aggregate_rows"] > 0
    )
    summary = {
        "result_class": (
            "controller_family_off_track_repair_panel_execution_pass"
            if result_passes
            else "controller_family_off_track_repair_panel_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": target_workload_count,
        "profile_count": len({row["profile_name"] for row in episode_rows}) if episode_rows else 0,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "repair_panel_spec_count": len({row["calibration_spec_id"] for row in episode_rows}) if episode_rows else 0,
        "target_repair_panel_spec_count": TARGET_REPAIR_PANEL_SPEC_COUNT,
        "selected_base_spec_count": len({row["base_task_source_id"] for row in episode_rows}) if episode_rows else 0,
        "target_selected_base_spec_count": TARGET_SELECTED_BASE_SPEC_COUNT,
        "repair_variant_count": len(repair_variant_labels),
        "target_repair_variant_count": TARGET_REPAIR_VARIANT_COUNT,
        "expected_repair_variant_labels": list(EXPECTED_REPAIR_VARIANT_LABELS),
        "observed_repair_variant_labels": sorted(repair_variant_labels),
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
            "repair_variant_aggregate": str(output_dir / "repair_variant_aggregate.csv"),
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


def run_off_track_repair_panel_execution(
    *,
    output_dir: Path | str = DEFAULT_RUN_DIR,
    repair_panel_specs_path: Path | str = DEFAULT_REPAIR_PANEL_SPECS,
    workload_path: Path | str = DEFAULT_REPAIR_PANEL_MATRIX,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = "m1725-paper-route-controller-family-off-track-repair-panel-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = repair_panel_executable_specs(load_repair_panel_specs(repair_panel_specs_path))
    spec_by_id = {str(spec["calibration_spec_id"]): spec for spec in executable_specs}
    workload_rows = repair_panel_workload_rows(workload_path)
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
            output / "repair_variant_aggregate.csv",
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
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=REPAIR_PANEL_FAILURE_FIELDNAMES)

    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in completed:
            continue
        profile_name = str(workload_row["profile_name"])
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            profile_config, model = profile_cache[profile_name]
            row = _run_repair_panel_workload_cell(
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
                "repair_panel_workload_id": str(workload_row.get("repair_panel_workload_id", "")),
                "calibration_workload_id": str(workload_row.get("calibration_workload_id", "")),
                "calibration_spec_id": str(workload_row.get("calibration_spec_id", "")),
                "repair_variant_label": str(workload_row.get("repair_variant_label", "")),
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
                "controller_family_ranking_claim_made": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
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

    return finalize_repair_panel_outputs(output_dir=output, target_workload_count=len(workload_rows), next_blocker=next_blocker)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run measured off-track repair panel execution.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--repair-panel-specs", type=Path, default=DEFAULT_REPAIR_PANEL_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_REPAIR_PANEL_MATRIX)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default="m1725-paper-route-controller-family-off-track-repair-panel-result-audit")
    args = parser.parse_args()

    summary = run_off_track_repair_panel_execution(
        output_dir=args.output_dir,
        repair_panel_specs_path=args.repair_panel_specs,
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
