"""Provenance helpers for one-cell seed-repair completion artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.task_quality_scenario_taxonomy_execution import (
    SCENARIO_FAILURE_FIELDNAMES,
    finalize_scenario_taxonomy_outputs,
)


DEFAULT_FAILED_WORKLOAD_ID = "m1728-s4-02::L2_window_13_current_tiled"
DEFAULT_ORIGINAL_EVAL_SEED = 175761
DEFAULT_EXPECTED_LABEL = "unavoidable"
DEFAULT_SEED_REPAIR_RULE = "nearest_successful_neighbor_tie_lower"
DEFAULT_SEED_REPAIR_SOURCE = "m1758_single_sampling_failure_reset_only_probe"
DEFAULT_REPLACEMENT_EVAL_SEED = 175760
DEFAULT_REPLACEMENT_SEED_OFFSET = -1

SEED_REPAIR_PROVENANCE_FIELDS = (
    "seed_repair_applied",
    "seed_repair_source",
    "seed_repair_rule",
    "original_eval_seed",
    "replacement_eval_seed",
    "replacement_seed_offset",
    "original_failure_error_type",
    "original_failure_error_message",
    "original_workload_id",
)


@dataclass(frozen=True)
class SeedRepairPlan:
    """Traceable seed-repair plan selected before completion execution."""

    workload_id: str = DEFAULT_FAILED_WORKLOAD_ID
    original_eval_seed: int = DEFAULT_ORIGINAL_EVAL_SEED
    replacement_eval_seed: int = DEFAULT_REPLACEMENT_EVAL_SEED
    replacement_seed_offset: int = DEFAULT_REPLACEMENT_SEED_OFFSET
    expected_sampled_obstacle_label: str = DEFAULT_EXPECTED_LABEL
    seed_repair_rule: str = DEFAULT_SEED_REPAIR_RULE
    seed_repair_source: str = DEFAULT_SEED_REPAIR_SOURCE

    def provenance_for_copied_row(self) -> dict[str, Any]:
        return {
            "seed_repair_applied": False,
            "seed_repair_source": "",
            "seed_repair_rule": "",
            "original_eval_seed": "",
            "replacement_eval_seed": "",
            "replacement_seed_offset": "",
            "original_failure_error_type": "",
            "original_failure_error_message": "",
            "original_workload_id": "",
        }

    def provenance_for_repaired_row(self, failure_row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "seed_repair_applied": True,
            "seed_repair_source": self.seed_repair_source,
            "seed_repair_rule": self.seed_repair_rule,
            "original_eval_seed": int(self.original_eval_seed),
            "replacement_eval_seed": int(self.replacement_eval_seed),
            "replacement_seed_offset": int(self.replacement_seed_offset),
            "original_failure_error_type": str(failure_row.get("error_type", "")),
            "original_failure_error_message": str(failure_row.get("error_message", "")),
            "original_workload_id": str(failure_row.get("workload_id", self.workload_id)),
        }


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def _int_value(value: Any) -> int:
    return int(float(value))


def select_seed_repair_plan(
    probe_rows: list[Mapping[str, Any]],
    *,
    workload_id: str = DEFAULT_FAILED_WORKLOAD_ID,
    original_eval_seed: int = DEFAULT_ORIGINAL_EVAL_SEED,
    expected_sampled_obstacle_label: str = DEFAULT_EXPECTED_LABEL,
    seed_repair_rule: str = DEFAULT_SEED_REPAIR_RULE,
    seed_repair_source: str = DEFAULT_SEED_REPAIR_SOURCE,
) -> SeedRepairPlan:
    """Select the nearest successful neighbor, breaking ties toward lower seed."""

    candidates: list[Mapping[str, Any]] = []
    for row in probe_rows:
        if str(row.get("workload_id", "")) != str(workload_id):
            continue
        if str(row.get("seed_role", "")) != "neighbor":
            continue
        if not _as_bool(row.get("reset_success")):
            continue
        if str(row.get("sampled_obstacle_label", "")) != str(expected_sampled_obstacle_label):
            continue
        candidates.append(row)
    if not candidates:
        raise ValueError("no successful neighbor seed candidates match the repair rule")

    selected = sorted(
        candidates,
        key=lambda row: (abs(_int_value(row.get("seed_offset", 0))), _int_value(row.get("eval_seed", 0))),
    )[0]
    return SeedRepairPlan(
        workload_id=str(workload_id),
        original_eval_seed=int(original_eval_seed),
        replacement_eval_seed=_int_value(selected["eval_seed"]),
        replacement_seed_offset=_int_value(selected["seed_offset"]),
        expected_sampled_obstacle_label=str(expected_sampled_obstacle_label),
        seed_repair_rule=str(seed_repair_rule),
        seed_repair_source=str(seed_repair_source),
    )


def require_single_failure_row(
    failure_rows: list[Mapping[str, Any]],
    *,
    workload_id: str = DEFAULT_FAILED_WORKLOAD_ID,
) -> Mapping[str, Any]:
    if len(failure_rows) != 1:
        raise ValueError(f"expected exactly one failure row, found {len(failure_rows)}")
    failure_row = failure_rows[0]
    if str(failure_row.get("workload_id", "")) != str(workload_id):
        raise ValueError(f"unexpected failure workload_id: {failure_row.get('workload_id', '')}")
    return failure_row


def augment_episode_rows_with_seed_repair(
    *,
    source_episode_rows: list[Mapping[str, Any]],
    repaired_row: Mapping[str, Any],
    failure_row: Mapping[str, Any],
    plan: SeedRepairPlan,
) -> list[dict[str, Any]]:
    source_workloads = {str(row.get("workload_id", "")) for row in source_episode_rows}
    if plan.workload_id in source_workloads:
        raise ValueError(f"source rows already contain repaired workload: {plan.workload_id}")
    if str(repaired_row.get("workload_id", "")) != plan.workload_id:
        raise ValueError(f"repaired row workload_id does not match plan: {repaired_row.get('workload_id', '')}")
    if str(repaired_row.get("sampled_obstacle_label", "")) != plan.expected_sampled_obstacle_label:
        raise ValueError(
            "repaired row sampled_obstacle_label does not match expected label: "
            f"{repaired_row.get('sampled_obstacle_label', '')}"
        )

    rows: list[dict[str, Any]] = []
    copied_provenance = plan.provenance_for_copied_row()
    for row in source_episode_rows:
        item = dict(row)
        item.update(copied_provenance)
        rows.append(item)

    repaired = dict(repaired_row)
    repaired.update(plan.provenance_for_repaired_row(failure_row))
    rows.append(repaired)
    return rows


def seed_repair_provenance_rows(plan: SeedRepairPlan, failure_row: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "workload_id": plan.workload_id,
            "seed_repair_applied": True,
            "seed_repair_source": plan.seed_repair_source,
            "seed_repair_rule": plan.seed_repair_rule,
            "original_eval_seed": int(plan.original_eval_seed),
            "replacement_eval_seed": int(plan.replacement_eval_seed),
            "replacement_seed_offset": int(plan.replacement_seed_offset),
            "expected_sampled_obstacle_label": plan.expected_sampled_obstacle_label,
            "original_failure_error_type": str(failure_row.get("error_type", "")),
            "original_failure_error_message": str(failure_row.get("error_message", "")),
        }
    ]


def write_seed_repair_completion_outputs(
    *,
    output_dir: Path | str,
    source_episode_rows: list[Mapping[str, Any]],
    source_failure_rows: list[Mapping[str, Any]],
    repaired_row: Mapping[str, Any],
    plan: SeedRepairPlan,
    unsupported_features_path: Path | str,
    target_workload_count: int,
    next_blocker: str,
) -> dict[str, Any]:
    """Write a fresh completed output directory after a repaired row is produced."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    failure_row = require_single_failure_row(source_failure_rows, workload_id=plan.workload_id)
    completed_rows = augment_episode_rows_with_seed_repair(
        source_episode_rows=source_episode_rows,
        repaired_row=repaired_row,
        failure_row=failure_row,
        plan=plan,
    )
    write_csv_rows(output / "episode_rows.csv", completed_rows)
    write_csv_rows(output / "failure_rows.csv", [], fieldnames=SCENARIO_FAILURE_FIELDNAMES)
    write_csv_rows(output / "original_failure_rows.csv", [dict(failure_row)], fieldnames=SCENARIO_FAILURE_FIELDNAMES)
    write_csv_rows(output / "seed_repair_provenance.csv", seed_repair_provenance_rows(plan, failure_row))
    summary = finalize_scenario_taxonomy_outputs(
        output_dir=output,
        target_workload_count=target_workload_count,
        unsupported_features_path=unsupported_features_path,
        next_blocker=next_blocker,
    )
    summary["seed_repair_completion"] = {
        "seed_repair_applied_row_count": 1,
        "seed_repair_source": plan.seed_repair_source,
        "seed_repair_rule": plan.seed_repair_rule,
        "original_eval_seed": int(plan.original_eval_seed),
        "replacement_eval_seed": int(plan.replacement_eval_seed),
        "replacement_seed_offset": int(plan.replacement_seed_offset),
        "original_failure_rows": str(output / "original_failure_rows.csv"),
        "seed_repair_provenance": str(output / "seed_repair_provenance.csv"),
    }
    write_json(output / "summary.json", summary)
    return summary


def load_seed_repair_plan_from_probe_rows(
    path: Path | str,
    *,
    workload_id: str = DEFAULT_FAILED_WORKLOAD_ID,
    original_eval_seed: int = DEFAULT_ORIGINAL_EVAL_SEED,
    expected_sampled_obstacle_label: str = DEFAULT_EXPECTED_LABEL,
) -> SeedRepairPlan:
    return select_seed_repair_plan(
        read_csv_rows(path),
        workload_id=workload_id,
        original_eval_seed=original_eval_seed,
        expected_sampled_obstacle_label=expected_sampled_obstacle_label,
    )
