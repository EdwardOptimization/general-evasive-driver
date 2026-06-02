"""Pack-aware measured execution for repaired dual-axis current-sim packs."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_scenario_task_family_measured_execution as base_runner
from autodrift import paper_route_current_sim_dual_axis_repaired_pack_reset_validation as repaired_reset
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    append_csv_row,
    completed_workload_ids,
    write_run_state,
)


DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST = Path(
    "runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/"
    "repaired_config_pack_manifest.json"
)
DEFAULT_SELECTED_ROWS = Path(
    "runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/"
    "selected_checkpoint_rows.csv"
)
DEFAULT_CONFIG_ROOT = Path(
    "runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution")
DEFAULT_EVAL_SEED_BASE = 236200
TARGET_PACK_COUNT = 5
TARGET_SCENARIO_SPECS_PER_PACK = 72
TARGET_SELECTED_CHECKPOINT_COUNT = 15
TARGET_EPISODE_COUNT = TARGET_PACK_COUNT * TARGET_SCENARIO_SPECS_PER_PACK * TARGET_SELECTED_CHECKPOINT_COUNT
DEFAULT_NEXT_BLOCKER = "m2363-paper-route-current-sim-dual-axis-repaired-pack-measured-execution-result-audit"
RESULT_PASS = "current_sim_dual_axis_repaired_pack_measured_execution_pass"
RESULT_FAIL = "current_sim_dual_axis_repaired_pack_measured_execution_incomplete_or_fail"

PACK_METADATA_FIELDS = (
    "pack_id",
    "pack_index",
    "pack_path",
    "pack_is_baseline_reference",
    "effective_selection_count",
    "sampling_repair_fallback_count",
)
PACK_WORKLOAD_FIELDS = (
    *PACK_METADATA_FIELDS,
    "flat_scenario_index",
)
REPAIR_METADATA_FIELDS = (
    "sampling_repair_applied",
    "sampling_repair_action",
    "sampling_repair_class",
    "sampling_repair_source_candidate_id",
)
EXTRA_GUARDRAIL_FIELDS = (
    "support_policy_ranking_claim_made",
    "scenario_redesign_executed_claim_made",
)


def _extend_unique(fields: Sequence[str], extras: Sequence[str]) -> list[str]:
    output = list(fields)
    for field in extras:
        if field not in output:
            output.append(field)
    return output


WORKLOAD_METADATA_FIELDS = _extend_unique(
    base_runner.WORKLOAD_METADATA_FIELDS,
    PACK_WORKLOAD_FIELDS,
)
EPISODE_FIELDNAMES = _extend_unique(
    base_runner.EPISODE_FIELDNAMES,
    [
        *PACK_WORKLOAD_FIELDS,
        *REPAIR_METADATA_FIELDS,
        *EXTRA_GUARDRAIL_FIELDS,
        "pack_profile_key",
        "dual_axis_repaired_pack_measured_execution",
    ],
)
FAILURE_FIELDNAMES = _extend_unique(
    base_runner.FAILURE_FIELDNAMES,
    [
        *PACK_WORKLOAD_FIELDS,
        *REPAIR_METADATA_FIELDS,
        *EXTRA_GUARDRAIL_FIELDS,
        "pack_profile_key",
    ],
)
METADATA_MISSING_FIELDNAMES = ["workload_id", "missing_metadata_fields"]
VALIDATION_FAILURE_FIELDNAMES = base_runner.VALIDATION_FAILURE_FIELDNAMES
METRIC_COMPLETENESS_FIELDNAMES = base_runner.METRIC_COMPLETENESS_FIELDNAMES
AGGREGATE_FIELDNAMES = base_runner.AGGREGATE_FIELDNAMES
CLAIM_FIELDNAMES = base_runner.CLAIM_FIELDNAMES
RolloutFunction = Callable[[Mapping[str, Any], Mapping[str, Any], int], Mapping[str, Any]]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return base_runner.read_csv_rows(path)


def _bool(value: Any, *, default: bool = False) -> bool:
    return base_runner._bool(value, default=default)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return base_runner._count_by(rows, key)


def load_repaired_packs(path: Path | str = DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST) -> list[dict[str, Any]]:
    return repaired_reset.load_repaired_config_packs(path)


def load_selected_rows(path: Path | str = DEFAULT_SELECTED_ROWS) -> list[dict[str, str]]:
    return base_runner.load_selected_rows(path)


def flattened_pack_specs(packs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    flat_index = 0
    for pack_index, pack in enumerate(packs):
        pack_id = str(pack.get("pack_id", ""))
        pack_meta = {
            "pack_id": pack_id,
            "pack_index": int(pack_index),
            "pack_path": str(pack.get("pack_path", "")),
            "pack_is_baseline_reference": bool(_bool(pack.get("baseline_reference_pack"))),
            "effective_selection_count": int(pack.get("effective_selection_count", 0) or 0),
            "sampling_repair_fallback_count": int(pack.get("sampling_repair_fallback_count", 0) or 0),
        }
        for scenario_index, spec in enumerate(pack.get("scenario_specs", [])):
            spec_dict = dict(spec)
            spec_dict.update(pack_meta)
            spec_dict["scenario_index"] = int(scenario_index)
            spec_dict["flat_scenario_index"] = int(flat_index)
            spec_dict.setdefault("sampling_repair_applied", False)
            spec_dict.setdefault("sampling_repair_action", "")
            spec_dict.setdefault("sampling_repair_class", "")
            spec_dict.setdefault("sampling_repair_source_candidate_id", "")
            output.append(spec_dict)
            flat_index += 1
    return output


def eval_seed_for_cell(
    *,
    eval_seed_base: int,
    pack_index: int,
    selected_index: int,
    scenario_index: int,
) -> int:
    return (
        int(eval_seed_base)
        + int(pack_index) * 100000
        + int(selected_index) * 1000
        + int(scenario_index)
    )


def workload_rows(
    *,
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    config_root: Path | str,
    eval_seed_base: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = Path(config_root)
    for selected_index, selected in enumerate(selected_rows):
        selected_key = base_runner._selected_key(selected)
        for scenario in scenario_specs:
            pack_id = str(scenario.get("pack_id", ""))
            scenario_id = str(scenario.get("scenario_spec_id", ""))
            pack_index = int(scenario.get("pack_index", 0) or 0)
            scenario_index = int(scenario.get("scenario_index", 0) or 0)
            eval_seed = eval_seed_for_cell(
                eval_seed_base=int(eval_seed_base),
                pack_index=pack_index,
                selected_index=int(selected_index),
                scenario_index=scenario_index,
            )
            rows.append(
                {
                    "workload_id": f"{selected_key}::{pack_id}::{scenario_id}",
                    "scenario_index": scenario_index,
                    "flat_scenario_index": int(scenario.get("flat_scenario_index", 0) or 0),
                    "selected_checkpoint_index": int(selected_index),
                    "eval_seed": int(eval_seed),
                    "profile_seed": base_runner._profile_seed(selected),
                    "profile_config_path": str(base_runner._config_path(root, selected)),
                    "scenario_spec_id": scenario_id,
                    "selected_key": selected_key,
                    "pack_id": pack_id,
                    "pack_index": pack_index,
                    "pack_path": str(scenario.get("pack_path", "")),
                    "pack_is_baseline_reference": bool(_bool(scenario.get("pack_is_baseline_reference"))),
                    "effective_selection_count": int(scenario.get("effective_selection_count", 0) or 0),
                    "sampling_repair_fallback_count": int(
                        scenario.get("sampling_repair_fallback_count", 0) or 0
                    ),
                    "pack_profile_key": f"{pack_id}|{selected.get('profile_name', '')}",
                }
            )
    return rows


def _workload_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in WORKLOAD_METADATA_FIELDS}


def _pack_repair_metadata(scenario_spec: Mapping[str, Any]) -> dict[str, Any]:
    return {field: scenario_spec.get(field, "") for field in REPAIR_METADATA_FIELDS}


def merged_metadata(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        **_workload_metadata(workload_row),
        **base_runner._scenario_metadata(scenario_spec),
        **_pack_repair_metadata(scenario_spec),
        **base_runner._selected_metadata(selected_row),
        "pack_profile_key": str(workload_row.get("pack_profile_key", "")),
    }


def metadata_missing_rows(
    *,
    workload: Sequence[Mapping[str, Any]],
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    required_fields = (
        *WORKLOAD_METADATA_FIELDS,
        *base_runner.SCENARIO_METADATA_FIELDS,
        *base_runner.SELECTED_METADATA_FIELDS,
        "sampling_repair_applied",
    )
    rows: list[dict[str, Any]] = []
    for workload_row in workload:
        scenario = scenario_specs[int(workload_row["flat_scenario_index"])]
        selected = selected_rows[int(workload_row["selected_checkpoint_index"])]
        metadata = merged_metadata(
            workload_row=workload_row,
            scenario_spec=scenario,
            selected_row=selected,
        )
        missing = [field for field in required_fields if not str(metadata.get(field, "")).strip()]
        if missing:
            rows.append(
                {
                    "workload_id": str(workload_row.get("workload_id", "")),
                    "missing_metadata_fields": ";".join(missing),
                }
            )
    return rows


def validation_failure_rows(
    *,
    packs: Sequence[Mapping[str, Any]],
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    workload: Sequence[Mapping[str, Any]],
    config_root: Path | str,
    require_checkpoint_paths: bool,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    workload_ids = Counter(str(row.get("workload_id", "")) for row in workload)
    for workload_id, count in sorted(workload_ids.items()):
        if workload_id and count > 1:
            failures.append(
                {
                    "workload_id": workload_id,
                    "error_type": "duplicate_workload_id",
                    "error_message": str(count),
                }
            )
    for pack in packs:
        pack_id = str(pack.get("pack_id", ""))
        if not pack_id:
            failures.append({"workload_id": "pack", "error_type": "missing_pack_field", "error_message": "pack_id"})
        if not str(pack.get("pack_path", "")).strip():
            failures.append(
                {"workload_id": pack_id, "error_type": "missing_pack_field", "error_message": "pack_path"}
            )
    for index, scenario in enumerate(scenario_specs):
        scenario_id = str(scenario.get("scenario_spec_id", f"scenario_{index:03d}"))
        key = f"{scenario.get('pack_id', '')}::{scenario_id}"
        if not isinstance(scenario.get("env_config"), Mapping):
            failures.append({"workload_id": key, "error_type": "missing_scenario_field", "error_message": "env_config"})
        for field in base_runner.SCENARIO_METADATA_FIELDS:
            if not str(scenario.get(field, "")).strip():
                failures.append({"workload_id": key, "error_type": "missing_scenario_field", "error_message": field})
        for field in PACK_METADATA_FIELDS:
            if not str(scenario.get(field, "")).strip():
                failures.append({"workload_id": key, "error_type": "missing_scenario_field", "error_message": field})
        if str(scenario.get("actor_contract_id", "")) != "P0_human_view_no_wheel_no_oracle":
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "actor_contract_id"})
        if int(scenario.get("contract_violation_count", 0)) != 0:
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "contract_violation_count"})
        for flag in (
            "labels_enter_actor_input",
            "ranking_admissible",
            "paper_level_claim_made",
            "level3_self_id_claim_made",
            "execution_blocked_by_unsupported_capability",
            "scenario_redesign_executed_claim_made",
        ):
            if _bool(scenario.get(flag), default=False):
                failures.append({"workload_id": key, "error_type": "guardrail_violation", "error_message": flag})
    root = Path(config_root)
    for index, selected in enumerate(selected_rows):
        selected_key = base_runner._selected_key(selected) or f"selected_{index:03d}"
        for field in base_runner.SELECTED_METADATA_FIELDS:
            if not str(selected.get(field, "")).strip():
                failures.append({"workload_id": selected_key, "error_type": "missing_selected_field", "error_message": field})
        config_path = base_runner._config_path(root, selected)
        if not config_path.exists():
            failures.append({"workload_id": selected_key, "error_type": "profile_config_path_not_found", "error_message": str(config_path)})
        checkpoint_path = str(selected.get("selected_checkpoint_path", "")).strip()
        if require_checkpoint_paths:
            if not checkpoint_path:
                failures.append({"workload_id": selected_key, "error_type": "missing_checkpoint_path", "error_message": "selected_checkpoint_path"})
            elif not Path(checkpoint_path).exists():
                failures.append({"workload_id": selected_key, "error_type": "checkpoint_path_not_found", "error_message": checkpoint_path})
        if _bool(selected.get("ranking_admissible"), default=False) or _bool(selected.get("winner_selected"), default=False):
            failures.append({"workload_id": selected_key, "error_type": "guardrail_violation", "error_message": "selected_row_ranking"})
    return failures


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "dual_axis_repaired_pack_measured_execution_completed",
            "admissible": True,
            "reason": "episode rows are measured rollout artifacts when the runner completes",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2362 output is diagnostic and must be audited before comparison claims",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "M2362 does not rank support policies or controller families",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2362 does not select or promote a controller family",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2362 is a public measured-execution panel, not a paper-level statistical result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2362 does not execute a denominator-backed finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2362 does not run wrong-history, reset-hidden, or zero-history interventions",
        },
    ]


def measured_episode_row(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    rollout_metrics: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = base_runner.measured_episode_row(
        workload_row=workload_row,
        scenario_spec=scenario_spec,
        selected_row=selected_row,
        rollout_metrics=rollout_metrics,
        eval_seed=eval_seed,
    )
    row.update(
        {
            **merged_metadata(
                workload_row=workload_row,
                scenario_spec=scenario_spec,
                selected_row=selected_row,
            ),
            "support_policy_ranking_claim_made": False,
            "scenario_redesign_executed_claim_made": False,
            "dual_axis_repaired_pack_measured_execution": True,
        }
    )
    return row


def measured_failure_row(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    eval_seed: int,
    error: BaseException,
) -> dict[str, Any]:
    row = base_runner.measured_failure_row(
        workload_row=workload_row,
        scenario_spec=scenario_spec,
        selected_row=selected_row,
        eval_seed=eval_seed,
        error=error,
    )
    row.update(
        {
            **merged_metadata(
                workload_row=workload_row,
                scenario_spec=scenario_spec,
                selected_row=selected_row,
            ),
            "support_policy_ranking_claim_made": False,
            "scenario_redesign_executed_claim_made": False,
        }
    )
    return row


def _aggregate_by_two_keys(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_axis: str,
    key_a: str,
    key_b: str,
) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        value = f"{row.get(key_a, '')}|{row.get(key_b, '')}"
        groups.setdefault(value, []).append(row)
    return [
        base_runner.aggregate_row(group, group_axis=group_axis, group_key=f"{key_a}+{key_b}", group_value=value)
        for value, group in sorted(groups.items())
    ]


def finalize_outputs(
    *,
    output_dir: Path,
    packs: Sequence[Mapping[str, Any]],
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    workload: Sequence[Mapping[str, Any]],
    target_pack_count: int,
    target_scenario_specs_per_pack: int,
    target_selected_checkpoint_count: int,
    target_episode_count: int,
    next_blocker: str,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)

    validation_failures = read_csv_rows(output_dir / "validation_failure_rows.csv")
    missing_rows = metadata_missing_rows(workload=workload, scenario_specs=scenario_specs, selected_rows=selected_rows)
    metric_failures = base_runner.metric_completeness_failure_rows(episode_rows)
    write_csv_rows(output_dir / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(
        output_dir / "metric_completeness_failures.csv",
        metric_failures,
        fieldnames=METRIC_COMPLETENESS_FIELDNAMES,
    )
    write_csv_rows(output_dir / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    aggregate_paths = {
        "aggregate_by_pack": ("aggregate_by_pack.csv", "pack_id"),
        "aggregate_by_repair_class": ("aggregate_by_repair_class.csv", "sampling_repair_class"),
        "aggregate_by_role_family": ("aggregate_by_role_family.csv", "role_family"),
        "aggregate_by_scenario_family": ("aggregate_by_scenario_family.csv", "scenario_family_id"),
        "aggregate_by_profile_seed": ("aggregate_by_profile_seed.csv", "profile_seed"),
        "aggregate_by_profile": ("aggregate_by_profile.csv", "profile_name"),
        "aggregate_by_obstacle_label": ("aggregate_by_obstacle_label.csv", "sampled_obstacle_label"),
        "aggregate_by_timing_bucket": ("aggregate_by_timing_bucket.csv", "obstacle_longitudinal_timing_bucket"),
        "aggregate_by_lateral_bucket": ("aggregate_by_lateral_bucket.csv", "obstacle_lateral_offset_bucket"),
        "aggregate_by_hidden_dynamics_bucket": ("aggregate_by_hidden_dynamics_bucket.csv", "hidden_dynamics_bucket"),
    }
    artifacts: dict[str, str] = {
        "summary": str(output_dir / "summary.json"),
        "episode_rows": str(output_dir / "episode_rows.csv"),
        "failure_rows": str(output_dir / "failure_rows.csv"),
        "validation_failure_rows": str(output_dir / "validation_failure_rows.csv"),
        "metadata_missing_rows": str(output_dir / "metadata_missing_rows.csv"),
        "metric_completeness_failures": str(output_dir / "metric_completeness_failures.csv"),
        "claim_boundary": str(output_dir / "claim_boundary.csv"),
        "run_state": str(output_dir / "run_state.json"),
    }
    for artifact_key, (filename, group_key) in aggregate_paths.items():
        path = output_dir / filename
        write_csv_rows(
            path,
            base_runner.aggregate_rows(episode_rows, group_axis=group_key, group_key=group_key),
            fieldnames=AGGREGATE_FIELDNAMES,
        )
        artifacts[artifact_key] = str(path)
    pack_profile_path = output_dir / "aggregate_by_pack_profile.csv"
    write_csv_rows(
        pack_profile_path,
        _aggregate_by_two_keys(episode_rows, group_axis="pack_profile", key_a="pack_id", key_b="profile_name"),
        fieldnames=AGGREGATE_FIELDNAMES,
    )
    artifacts["aggregate_by_pack_profile"] = str(pack_profile_path)

    pack_ids = [str(pack.get("pack_id", "")) for pack in packs]
    scenario_counts_by_pack = {
        pack_id: sum(str(spec.get("pack_id", "")) == pack_id for spec in scenario_specs)
        for pack_id in pack_ids
    }
    episode_pack_ids = {str(row.get("pack_id", "")) for row in episode_rows}
    pack_count = len(pack_ids)
    episode_pack_count = len(episode_pack_ids)
    scenario_specs_per_pack_count = (
        next(iter(set(scenario_counts_by_pack.values()))) if len(set(scenario_counts_by_pack.values())) == 1 else None
    )
    selected_checkpoint_count = len({str(row.get("selected_key", "")) for row in workload})
    selected_checkpoint_count_from_rows = len({str(row.get("matrix_id", "")) for row in episode_rows})
    pack_aware_scenario_spec_count = len(
        {(str(row.get("pack_id", "")), str(row.get("scenario_spec_id", ""))) for row in episode_rows}
    )
    unique_scenario_spec_id_count = len({str(row.get("scenario_spec_id", "")) for row in episode_rows})
    label_mismatch_count = int(sum(not _bool(row.get("sampled_label_matches_spec"), default=False) for row in episode_rows))
    guardrail_flags = {key: False for key in (*base_runner.FORBIDDEN_GUARDRAILS, *EXTRA_GUARDRAIL_FIELDS)}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        len(episode_rows) == int(target_episode_count)
        and len(failure_rows) == 0
        and len(validation_failures) == 0
        and pack_count == int(target_pack_count)
        and episode_pack_count == int(target_pack_count)
        and scenario_specs_per_pack_count == int(target_scenario_specs_per_pack)
        and pack_aware_scenario_spec_count == int(target_pack_count) * int(target_scenario_specs_per_pack)
        and selected_checkpoint_count_from_rows == int(target_selected_checkpoint_count)
        and not missing_rows
        and not metric_failures
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": int(target_episode_count),
        "failure_count": len(failure_rows),
        "validation_failure_count": len(validation_failures),
        "config_pack_count": pack_count,
        "episode_pack_count": episode_pack_count,
        "target_pack_count": int(target_pack_count),
        "scenario_specs_per_pack_count": scenario_specs_per_pack_count,
        "target_scenario_specs_per_pack": int(target_scenario_specs_per_pack),
        "scenario_counts_by_pack": scenario_counts_by_pack,
        "pack_aware_scenario_spec_count": pack_aware_scenario_spec_count,
        "unique_scenario_spec_id_count": unique_scenario_spec_id_count,
        "selected_checkpoint_count": selected_checkpoint_count_from_rows,
        "planned_selected_checkpoint_count": selected_checkpoint_count,
        "target_selected_checkpoint_count": int(target_selected_checkpoint_count),
        "metadata_missing_count": len(missing_rows),
        "metric_completeness_failure_count": len(metric_failures),
        "all_selected_metrics_finite": not metric_failures,
        "label_mismatch_count": label_mismatch_count,
        "pack_counts": _count_by(episode_rows, "pack_id"),
        "repair_class_counts": _count_by(episode_rows, "sampling_repair_class"),
        "role_family_counts": _count_by(episode_rows, "role_family"),
        "scenario_family_counts": _count_by(episode_rows, "scenario_family_id"),
        "profile_counts": _count_by(episode_rows, "profile_name"),
        "profile_seed_counts": _count_by(episode_rows, "profile_seed"),
        "obstacle_label_counts": _count_by(episode_rows, "sampled_obstacle_label"),
        "timing_bucket_counts": _count_by(episode_rows, "obstacle_longitudinal_timing_bucket"),
        "lateral_bucket_counts": _count_by(episode_rows, "obstacle_lateral_offset_bucket"),
        "hidden_dynamics_bucket_counts": _count_by(episode_rows, "hidden_dynamics_bucket"),
        "outcome_counts": _count_by(episode_rows, "outcome_bucket"),
        "termination_reason_counts": _count_by(episode_rows, "termination_reason"),
        "global_outcome": base_runner.aggregate_row(
            episode_rows,
            group_axis="global",
            group_key="global",
            group_value="all",
        ),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": bool(episode_rows or failure_rows),
        "policy_action_executed": bool(episode_rows),
        "measured_rollout_started": bool(episode_rows or failure_rows),
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_episode_count": int(target_episode_count),
            "completed_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "complete": bool(passes),
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def run_dual_axis_repaired_pack_measured_execution(
    *,
    repaired_config_pack_manifest_path: Path | str = DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST,
    selected_rows_path: Path | str = DEFAULT_SELECTED_ROWS,
    config_root: Path | str = DEFAULT_CONFIG_ROOT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_pack_count: int = TARGET_PACK_COUNT,
    target_scenario_specs_per_pack: int = TARGET_SCENARIO_SPECS_PER_PACK,
    target_selected_checkpoint_count: int = TARGET_SELECTED_CHECKPOINT_COUNT,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    packs = load_repaired_packs(repaired_config_pack_manifest_path)
    scenario_specs = flattened_pack_specs(packs)
    selected_rows = load_selected_rows(selected_rows_path)
    workload = workload_rows(
        scenario_specs=scenario_specs,
        selected_rows=selected_rows,
        config_root=config_root,
        eval_seed_base=int(eval_seed_base),
    )

    if not resume:
        for path in output.glob("*.csv"):
            path.unlink()
        for path in (output / "summary.json", output / "run_state.json"):
            if path.exists():
                path.unlink()

    validation_failures = validation_failure_rows(
        packs=packs,
        scenario_specs=scenario_specs,
        selected_rows=selected_rows,
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
            packs=packs,
            scenario_specs=scenario_specs,
            selected_rows=selected_rows,
            workload=workload,
            target_pack_count=int(target_pack_count),
            target_scenario_specs_per_pack=int(target_scenario_specs_per_pack),
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
        scenario = scenario_specs[int(row["flat_scenario_index"])]
        selected = selected_rows[int(row["selected_checkpoint_index"])]
        eval_seed = int(row["eval_seed"])
        try:
            if rollout_fn is None:
                config_key = str(row["profile_config_path"])
                profile_config = profile_config_cache.get(config_key)
                if profile_config is None:
                    profile_config = read_json(config_key)
                    profile_config_cache[config_key] = profile_config
                rollout_metrics = base_runner._real_rollout_metrics(
                    workload_row=row,
                    scenario_spec=scenario,
                    selected_row=selected,
                    profile_config=profile_config,
                    model_cache=model_cache,
                    device=str(device),
                    eval_seed=int(eval_seed),
                )
            else:
                rollout_metrics = dict(rollout_fn(row, scenario, int(eval_seed)))
            episode_row = measured_episode_row(
                workload_row=row,
                scenario_spec=scenario,
                selected_row=selected,
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
                    scenario_spec=scenario,
                    selected_row=selected,
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
        packs=packs,
        scenario_specs=scenario_specs,
        selected_rows=selected_rows,
        workload=workload,
        target_pack_count=int(target_pack_count),
        target_scenario_specs_per_pack=int(target_scenario_specs_per_pack),
        target_selected_checkpoint_count=int(target_selected_checkpoint_count),
        target_episode_count=int(target_episode_count),
        next_blocker=str(next_blocker),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repaired-config-pack-manifest",
        type=Path,
        default=DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST,
    )
    parser.add_argument("--selected-rows", type=Path, default=DEFAULT_SELECTED_ROWS)
    parser.add_argument("--config-root", type=Path, default=DEFAULT_CONFIG_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-pack-count", type=int, default=TARGET_PACK_COUNT)
    parser.add_argument("--target-scenario-specs-per-pack", type=int, default=TARGET_SCENARIO_SPECS_PER_PACK)
    parser.add_argument("--target-selected-checkpoint-count", type=int, default=TARGET_SELECTED_CHECKPOINT_COUNT)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_dual_axis_repaired_pack_measured_execution(
        repaired_config_pack_manifest_path=args.repaired_config_pack_manifest,
        selected_rows_path=args.selected_rows,
        config_root=args.config_root,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        target_pack_count=int(args.target_pack_count),
        target_scenario_specs_per_pack=int(args.target_scenario_specs_per_pack),
        target_selected_checkpoint_count=int(args.target_selected_checkpoint_count),
        target_episode_count=int(args.target_episode_count),
        device=str(args.device),
        resume=not bool(args.no_resume),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"config_pack_count={summary['config_pack_count']}")
    print(f"pack_aware_scenario_spec_count={summary['pack_aware_scenario_spec_count']}")
    print(f"selected_checkpoint_count={summary['selected_checkpoint_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"metadata_missing_count={summary['metadata_missing_count']}")
    print(f"metric_completeness_failure_count={summary['metric_completeness_failure_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
