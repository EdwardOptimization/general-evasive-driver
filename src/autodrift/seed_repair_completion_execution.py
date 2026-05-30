"""One-cell seed-repair completion execution CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.seed_repair_completion import (
    DEFAULT_EXPECTED_LABEL,
    DEFAULT_FAILED_WORKLOAD_ID,
    DEFAULT_ORIGINAL_EVAL_SEED,
    DEFAULT_REPLACEMENT_EVAL_SEED,
    SeedRepairPlan,
    load_seed_repair_plan_from_probe_rows,
    write_seed_repair_completion_outputs,
)
from autodrift.task_quality_scenario_taxonomy_execution import (
    TARGET_EPISODE_COUNT,
    _run_scenario_workload_cell,
    load_scenario_specs,
    scenario_taxonomy_workload_rows,
)


DEFAULT_OUTPUT_DIR = Path("runs/m1764_revised_scenario_taxonomy_single_seed_completion")
DEFAULT_SOURCE_RUN_DIR = Path("runs/m1756_revised_scenario_taxonomy_execution_after_wrapper_repair")
DEFAULT_PROBE_ROWS = Path("runs/m1758_single_sampling_failure_reset_only_probe/probe_rows.csv")
DEFAULT_SCENARIO_SPECS = Path(
    "runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json"
)
DEFAULT_EXECUTABLE_SCENARIO_SPECS = Path(
    "runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json"
)
DEFAULT_WORKLOAD = Path(
    "runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv"
)
DEFAULT_UNSUPPORTED_FEATURES = Path(
    "runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/unsupported_scenario_features.csv"
)


def _find_single(rows: list[Mapping[str, Any]], *, key: str, value: str) -> Mapping[str, Any]:
    matched = [row for row in rows if str(row.get(key, "")) == str(value)]
    if len(matched) != 1:
        raise ValueError(f"expected exactly one row for {key}={value}, found {len(matched)}")
    return matched[0]


def _load_required_profile(profile_name: str, *, m1674_run_dir: Path | str, device: str) -> tuple[dict[str, Any], Any, Mapping[str, Any]]:
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    profile_row = _find_single(profile_rows, key="profile_name", value=profile_name)
    profile_config = read_json(profile_row["config_path"])
    model, _ = load_actor_critic_checkpoint(profile_row["checkpoint_path"], device=device)
    return profile_config, model, profile_row


def _validate_fixed_plan(plan: SeedRepairPlan, *, replacement_eval_seed: int) -> None:
    if int(plan.replacement_eval_seed) != int(replacement_eval_seed):
        raise ValueError(
            f"replacement seed mismatch: plan={plan.replacement_eval_seed}, expected={replacement_eval_seed}"
        )


def run_seed_repair_completion_execution(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    source_run_dir: Path | str = DEFAULT_SOURCE_RUN_DIR,
    probe_rows_path: Path | str = DEFAULT_PROBE_ROWS,
    scenario_specs_path: Path | str = DEFAULT_SCENARIO_SPECS,
    executable_scenario_specs_path: Path | str = DEFAULT_EXECUTABLE_SCENARIO_SPECS,
    workload_path: Path | str = DEFAULT_WORKLOAD,
    unsupported_features_path: Path | str = DEFAULT_UNSUPPORTED_FEATURES,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    workload_id: str = DEFAULT_FAILED_WORKLOAD_ID,
    original_eval_seed: int = DEFAULT_ORIGINAL_EVAL_SEED,
    replacement_eval_seed: int = DEFAULT_REPLACEMENT_EVAL_SEED,
    expected_sampled_obstacle_label: str = DEFAULT_EXPECTED_LABEL,
    device: str = "cpu",
    next_blocker: str = "m1765-single-cell-seed-repair-completion-result-audit",
) -> dict[str, Any]:
    source_run = Path(source_run_dir)
    source_episode_rows = read_csv_rows(source_run / "episode_rows.csv")
    source_failure_rows = read_csv_rows(source_run / "failure_rows.csv")
    plan = load_seed_repair_plan_from_probe_rows(
        probe_rows_path,
        workload_id=workload_id,
        original_eval_seed=original_eval_seed,
        expected_sampled_obstacle_label=expected_sampled_obstacle_label,
    )
    _validate_fixed_plan(plan, replacement_eval_seed=replacement_eval_seed)

    workload_rows = scenario_taxonomy_workload_rows(
        scenario_specs_path=scenario_specs_path,
        workload_path=workload_path,
    )
    workload_row = _find_single(workload_rows, key="workload_id", value=workload_id)
    executable_specs = load_scenario_specs(executable_scenario_specs_path)
    executable_spec = _find_single(
        executable_specs,
        key="scenario_spec_id",
        value=str(workload_row["scenario_spec_id"]),
    )
    profile_config, model, profile_row = _load_required_profile(
        str(workload_row["profile_name"]),
        m1674_run_dir=m1674_run_dir,
        device=device,
    )
    repaired_row = _run_scenario_workload_cell(
        workload_row=workload_row,
        executable_spec=executable_spec,
        profile_config=profile_config,
        model=model,
        profile_row=profile_row,
        eval_seed=int(plan.replacement_eval_seed),
    )
    if str(repaired_row.get("sampled_obstacle_label", "")) != str(expected_sampled_obstacle_label):
        raise ValueError(
            "repaired row sampled_obstacle_label does not match expected label: "
            f"{repaired_row.get('sampled_obstacle_label', '')}"
        )
    return write_seed_repair_completion_outputs(
        output_dir=output_dir,
        source_episode_rows=source_episode_rows,
        source_failure_rows=source_failure_rows,
        repaired_row=repaired_row,
        plan=plan,
        unsupported_features_path=unsupported_features_path,
        target_workload_count=TARGET_EPISODE_COUNT,
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-run-dir", type=Path, default=DEFAULT_SOURCE_RUN_DIR)
    parser.add_argument("--probe-rows", type=Path, default=DEFAULT_PROBE_ROWS)
    parser.add_argument("--scenario-specs", type=Path, default=DEFAULT_SCENARIO_SPECS)
    parser.add_argument("--executable-scenario-specs", type=Path, default=DEFAULT_EXECUTABLE_SCENARIO_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_WORKLOAD)
    parser.add_argument("--unsupported-features", type=Path, default=DEFAULT_UNSUPPORTED_FEATURES)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--workload-id", default=DEFAULT_FAILED_WORKLOAD_ID)
    parser.add_argument("--original-eval-seed", type=int, default=DEFAULT_ORIGINAL_EVAL_SEED)
    parser.add_argument("--replacement-eval-seed", type=int, default=DEFAULT_REPLACEMENT_EVAL_SEED)
    parser.add_argument("--expected-sampled-obstacle-label", default=DEFAULT_EXPECTED_LABEL)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--next-blocker", default="m1765-single-cell-seed-repair-completion-result-audit")
    args = parser.parse_args()
    summary = run_seed_repair_completion_execution(
        output_dir=args.output_dir,
        source_run_dir=args.source_run_dir,
        probe_rows_path=args.probe_rows,
        scenario_specs_path=args.scenario_specs,
        executable_scenario_specs_path=args.executable_scenario_specs,
        workload_path=args.workload,
        unsupported_features_path=args.unsupported_features,
        m1674_run_dir=args.m1674_run_dir,
        workload_id=args.workload_id,
        original_eval_seed=args.original_eval_seed,
        replacement_eval_seed=args.replacement_eval_seed,
        expected_sampled_obstacle_label=args.expected_sampled_obstacle_label,
        device=args.device,
        next_blocker=args.next_blocker,
    )
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"failure_count={summary['failure_count']}")


if __name__ == "__main__":
    main()
