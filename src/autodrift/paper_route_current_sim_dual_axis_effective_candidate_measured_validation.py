"""Measured validation for reset-ready effective candidate artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_scenario_task_family_measured_execution as base_runner
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    append_csv_row,
    completed_workload_ids,
    write_run_state,
)


DEFAULT_SOURCE_DIR = Path("runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization")
DEFAULT_RESET_VALIDATION_DIR = Path(
    "runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter"
)
DEFAULT_SELECTED_ROWS = Path(
    "runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/"
    "selected_checkpoint_rows.csv"
)
DEFAULT_CONFIG_ROOT = Path(
    "runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation")
DEFAULT_EVAL_SEED_BASE = 239700
TARGET_CANDIDATE_COUNT = 54
TARGET_CANDIDATE_SCENARIO_REFERENCE_COUNT = 2049
TARGET_SELECTED_CHECKPOINT_COUNT = 15
TARGET_EPISODE_COUNT = TARGET_CANDIDATE_SCENARIO_REFERENCE_COUNT * TARGET_SELECTED_CHECKPOINT_COUNT
DEFAULT_NEXT_BLOCKER = "m2398-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-result-audit"
RESULT_PASS = "current_sim_dual_axis_effective_candidate_measured_validation_pass"
RESULT_FAIL = "current_sim_dual_axis_effective_candidate_measured_validation_incomplete_or_fail"

CANDIDATE_METADATA_FIELDS = (
    "effective_candidate_scenario_index",
    "candidate_id",
    "candidate_index",
    "effective_candidate_config_path",
    "source_candidate_config_path",
    "source_repair_spec_id",
    "repair_family",
    "priority_tier",
    "source_slice_axis",
    "source_slice_value",
    "selected_scenario_count",
    "selected_base_pack_count",
)
PACK_METADATA_FIELDS = (
    "pack_id",
    "pack_index",
    "pack_path",
)
EXTRA_GUARDRAIL_FIELDS = (
    "support_policy_ranking_claim_made",
    "scenario_redesign_executed_claim_made",
    "current_sim_verdict_claim_made",
    "training_repair_success_claim_made",
)
WORKLOAD_METADATA_FIELDS = base_runner._extend_unique(
    base_runner.WORKLOAD_METADATA_FIELDS,
    [
        "selected_key",
        *CANDIDATE_METADATA_FIELDS,
        *PACK_METADATA_FIELDS,
    ],
)
EPISODE_FIELDNAMES = base_runner._extend_unique(
    base_runner.EPISODE_FIELDNAMES,
    [
        *CANDIDATE_METADATA_FIELDS,
        *PACK_METADATA_FIELDS,
        *EXTRA_GUARDRAIL_FIELDS,
        "candidate_profile_key",
        "candidate_pack_key",
        "effective_candidate_measured_validation",
    ],
)
FAILURE_FIELDNAMES = base_runner._extend_unique(
    base_runner.FAILURE_FIELDNAMES,
    [
        *CANDIDATE_METADATA_FIELDS,
        *PACK_METADATA_FIELDS,
        *EXTRA_GUARDRAIL_FIELDS,
        "candidate_profile_key",
        "candidate_pack_key",
    ],
)
VALIDATION_FAILURE_FIELDNAMES = base_runner.VALIDATION_FAILURE_FIELDNAMES
METADATA_MISSING_FIELDNAMES = ["workload_id", "missing_metadata_fields"]
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


def _string_list(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    return str(value or "")


def _first_number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, list) and value:
        return float(value[0])
    if isinstance(value, tuple) and value:
        return float(value[0])
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _scenario_defaults(spec: Mapping[str, Any]) -> dict[str, Any]:
    env_config = spec.get("env_config") if isinstance(spec.get("env_config"), Mapping) else {}
    obstacle = env_config.get("obstacle") if isinstance(env_config.get("obstacle"), Mapping) else {}
    return {
        "allowed_labels_metadata_only": _string_list(obstacle.get("allowed_labels")),
        "same_scene_group_id": f"{spec.get('pack_id', '')}|{spec.get('scenario_spec_id', '')}",
        "initial_speed_mps": _first_number(env_config.get("speed_range")),
        "track_radius_m": _first_number(env_config.get("track_radius")),
        "track_width_m": _first_number(env_config.get("track_width")),
        "contract_violation_count": 0,
        "labels_enter_actor_input": False,
        "ranking_admissible": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "execution_blocked_by_unsupported_capability": False,
        "scenario_redesign_executed_claim_made": False,
    }


def _candidate_index_map(candidate_rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {candidate_id: index for index, candidate_id in enumerate(sorted(str(row["candidate_id"]) for row in candidate_rows))}


def _candidate_rows_by_id(source_dir: Path | str) -> dict[str, dict[str, Any]]:
    rows = read_csv_rows(Path(source_dir) / "effective_candidate_config_rows.csv")
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id", ""))
        if candidate_id:
            output[candidate_id] = dict(row)
    return output


def _scenario_reference_rows(source_dir: Path | str) -> list[dict[str, str]]:
    rows = read_csv_rows(Path(source_dir) / "effective_candidate_scenario_rows.csv")
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("candidate_id", "")),
            str(row.get("pack_id", "")),
            str(row.get("scenario_spec_id", "")),
        ),
    )


def _spec_key(candidate_id: str, pack_id: str, scenario_spec_id: str) -> tuple[str, str, str]:
    return (str(candidate_id), str(pack_id), str(scenario_spec_id))


def load_effective_candidate_scenario_specs(source_dir: Path | str = DEFAULT_SOURCE_DIR) -> list[dict[str, Any]]:
    source = Path(source_dir)
    candidate_rows_by_id = _candidate_rows_by_id(source)
    candidate_index_by_id = _candidate_index_map(list(candidate_rows_by_id.values()))
    specs_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}

    for candidate_id, candidate_row in sorted(candidate_rows_by_id.items()):
        config_path = Path(str(candidate_row.get("effective_candidate_config_path", "")))
        payload = read_json(config_path)
        selected_specs = payload.get("selected_scenario_specs", [])
        if not isinstance(selected_specs, list):
            raise ValueError(f"effective candidate config has no selected_scenario_specs: {config_path}")
        candidate_meta = {
            "candidate_id": candidate_id,
            "candidate_index": int(candidate_index_by_id[candidate_id]),
            "effective_candidate_config_path": str(config_path),
            "source_candidate_config_path": str(candidate_row.get("source_candidate_config_path", "")),
            "source_repair_spec_id": str(candidate_row.get("source_repair_spec_id", "")),
            "repair_family": str(candidate_row.get("repair_family", payload.get("repair_family", ""))),
            "priority_tier": str(payload.get("priority_tier", "")),
            "source_slice_axis": str(candidate_row.get("source_slice_axis", "")),
            "source_slice_value": str(candidate_row.get("source_slice_value", "")),
            "selected_scenario_count": int(candidate_row.get("selected_scenario_count", 0) or 0),
            "selected_base_pack_count": int(candidate_row.get("selected_base_pack_count", 0) or 0),
        }
        for spec in selected_specs:
            spec_dict = dict(spec)
            spec_dict.update(_scenario_defaults(spec_dict))
            spec_dict.update(candidate_meta)
            spec_dict["pack_index"] = _pack_index(str(spec_dict.get("pack_id", "")))
            specs_by_key[
                _spec_key(
                    candidate_id,
                    str(spec_dict.get("pack_id", "")),
                    str(spec_dict.get("scenario_spec_id", "")),
                )
            ] = spec_dict

    output: list[dict[str, Any]] = []
    for scenario_index, row in enumerate(_scenario_reference_rows(source)):
        key = _spec_key(str(row.get("candidate_id", "")), str(row.get("pack_id", "")), str(row.get("scenario_spec_id", "")))
        if key not in specs_by_key:
            missing = "::".join(key)
            raise ValueError(f"missing selected scenario spec for reference row: {missing}")
        spec = dict(specs_by_key[key])
        spec["effective_candidate_scenario_index"] = int(scenario_index)
        output.append(spec)
    return output


def _pack_index(pack_id: str) -> int:
    order = {
        "baseline_reference_pack": 0,
        "g_primary_pack": 1,
        "h_primary_pack": 2,
        "g_h_primary_pack": 3,
        "gh_minimal_pack": 4,
    }
    return int(order.get(str(pack_id), len(order)))


def load_selected_rows(path: Path | str = DEFAULT_SELECTED_ROWS) -> list[dict[str, str]]:
    return base_runner.load_selected_rows(path)


def eval_seed_for_cell(
    *,
    eval_seed_base: int,
    selected_index: int,
    effective_candidate_scenario_index: int,
) -> int:
    return (
        int(eval_seed_base)
        + int(selected_index) * 100000
        + int(effective_candidate_scenario_index)
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
            scenario_index = int(scenario["effective_candidate_scenario_index"])
            candidate_id = str(scenario.get("candidate_id", ""))
            pack_id = str(scenario.get("pack_id", ""))
            scenario_id = str(scenario.get("scenario_spec_id", ""))
            eval_seed = eval_seed_for_cell(
                eval_seed_base=int(eval_seed_base),
                selected_index=int(selected_index),
                effective_candidate_scenario_index=scenario_index,
            )
            rows.append(
                {
                    "workload_id": f"{selected_key}::{candidate_id}::{pack_id}::{scenario_id}",
                    "scenario_index": int(scenario_index),
                    "effective_candidate_scenario_index": int(scenario_index),
                    "selected_checkpoint_index": int(selected_index),
                    "eval_seed": int(eval_seed),
                    "profile_seed": base_runner._profile_seed(selected),
                    "profile_config_path": str(base_runner._config_path(root, selected)),
                    "scenario_spec_id": scenario_id,
                    "selected_key": selected_key,
                    "candidate_id": candidate_id,
                    "candidate_index": int(scenario.get("candidate_index", 0) or 0),
                    "effective_candidate_config_path": str(scenario.get("effective_candidate_config_path", "")),
                    "source_candidate_config_path": str(scenario.get("source_candidate_config_path", "")),
                    "source_repair_spec_id": str(scenario.get("source_repair_spec_id", "")),
                    "repair_family": str(scenario.get("repair_family", "")),
                    "priority_tier": str(scenario.get("priority_tier", "")),
                    "source_slice_axis": str(scenario.get("source_slice_axis", "")),
                    "source_slice_value": str(scenario.get("source_slice_value", "")),
                    "selected_scenario_count": int(scenario.get("selected_scenario_count", 0) or 0),
                    "selected_base_pack_count": int(scenario.get("selected_base_pack_count", 0) or 0),
                    "pack_id": pack_id,
                    "pack_index": int(scenario.get("pack_index", 0) or 0),
                    "pack_path": str(scenario.get("pack_path", "")),
                    "candidate_profile_key": f"{candidate_id}|{selected.get('profile_name', '')}",
                    "candidate_pack_key": f"{candidate_id}|{pack_id}",
                }
            )
    return rows


def _workload_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in WORKLOAD_METADATA_FIELDS}


def _candidate_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {field: spec.get(field, "") for field in CANDIDATE_METADATA_FIELDS}


def _pack_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {field: spec.get(field, "") for field in PACK_METADATA_FIELDS}


def merged_metadata(
    *,
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        **_workload_metadata(workload_row),
        **base_runner._scenario_metadata(scenario_spec),
        **_candidate_metadata(scenario_spec),
        **_pack_metadata(scenario_spec),
        **base_runner._selected_metadata(selected_row),
        "candidate_profile_key": str(workload_row.get("candidate_profile_key", "")),
        "candidate_pack_key": str(workload_row.get("candidate_pack_key", "")),
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
        *CANDIDATE_METADATA_FIELDS,
        *PACK_METADATA_FIELDS,
    )
    rows: list[dict[str, Any]] = []
    for workload_row in workload:
        scenario = scenario_specs[int(workload_row["effective_candidate_scenario_index"])]
        selected = selected_rows[int(workload_row["selected_checkpoint_index"])]
        metadata = merged_metadata(workload_row=workload_row, scenario_spec=scenario, selected_row=selected)
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
            failures.append({"workload_id": workload_id, "error_type": "duplicate_workload_id", "error_message": str(count)})
    for index, scenario in enumerate(scenario_specs):
        candidate_id = str(scenario.get("candidate_id", ""))
        pack_id = str(scenario.get("pack_id", ""))
        scenario_id = str(scenario.get("scenario_spec_id", f"scenario_{index:03d}"))
        key = f"{candidate_id}::{pack_id}::{scenario_id}"
        env_config = scenario.get("env_config")
        if not isinstance(env_config, Mapping):
            failures.append({"workload_id": key, "error_type": "missing_scenario_field", "error_message": "env_config"})
            env_config = {}
        for field in base_runner.SCENARIO_METADATA_FIELDS:
            if not str(scenario.get(field, "")).strip():
                failures.append({"workload_id": key, "error_type": "missing_scenario_field", "error_message": field})
        for field in (*CANDIDATE_METADATA_FIELDS, *PACK_METADATA_FIELDS):
            if not str(scenario.get(field, "")).strip():
                failures.append({"workload_id": key, "error_type": "missing_candidate_field", "error_message": field})
        if str(scenario.get("actor_contract_id", "")) != "P0_human_view_no_wheel_no_oracle":
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "actor_contract_id"})
        if int(scenario.get("contract_violation_count", 0) or 0) != 0:
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "contract_violation_count"})
        if _bool(env_config.get("include_privileged_params"), default=False):
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "include_privileged_params"})
        if str(env_config.get("wheel_observation_mode", "")) != "none":
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "wheel_observation_mode"})
        if str(env_config.get("obstacle_relative_velocity_mode", "")) != "zero":
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "obstacle_relative_velocity_mode"})
        if int(env_config.get("history_length", 0) or 0) != 1:
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "history_length"})
        if not _bool(scenario.get("actor_contract_guardrail_pass"), default=True):
            failures.append({"workload_id": key, "error_type": "actor_contract_violation", "error_message": "actor_contract_guardrail_pass"})
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
            "claim": "effective_candidate_measured_validation_completed",
            "admissible": True,
            "reason": "episode rows are measured rollout artifacts when the runner completes",
        },
        {
            "claim": "effective_candidate_ranking",
            "admissible": False,
            "reason": "M2397 output is diagnostic and must be audited before any candidate comparison claim",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2397 does not rank controller families",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2397 does not select or promote a controller family or candidate",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2397 is a public measured-validation panel, not a paper-level statistical result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2397 does not execute a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2397 does not run wrong-history, reset-hidden, or zero-history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2397 must be audited and compared before a current-sim verdict",
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
            **merged_metadata(workload_row=workload_row, scenario_spec=scenario_spec, selected_row=selected_row),
            "support_policy_ranking_claim_made": False,
            "scenario_redesign_executed_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "training_repair_success_claim_made": False,
            "effective_candidate_measured_validation": True,
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
            **merged_metadata(workload_row=workload_row, scenario_spec=scenario_spec, selected_row=selected_row),
            "support_policy_ranking_claim_made": False,
            "scenario_redesign_executed_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "training_repair_success_claim_made": False,
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


def _write_aggregate(
    *,
    output_dir: Path,
    artifacts: dict[str, str],
    rows: Sequence[Mapping[str, Any]],
    artifact_key: str,
    filename: str,
    group_key: str,
) -> None:
    path = output_dir / filename
    write_csv_rows(
        path,
        base_runner.aggregate_rows(rows, group_axis=group_key, group_key=group_key),
        fieldnames=AGGREGATE_FIELDNAMES,
    )
    artifacts[artifact_key] = str(path)


def _actor_contract_violation_count(validation_failures: Sequence[Mapping[str, Any]]) -> int:
    return sum(str(row.get("error_type", "")) == "actor_contract_violation" for row in validation_failures)


def finalize_outputs(
    *,
    output_dir: Path,
    scenario_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    workload: Sequence[Mapping[str, Any]],
    target_candidate_count: int,
    target_candidate_scenario_reference_count: int,
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
    aggregate_specs = {
        "aggregate_by_candidate": ("aggregate_by_candidate.csv", "candidate_id"),
        "aggregate_by_repair_family": ("aggregate_by_repair_family.csv", "repair_family"),
        "aggregate_by_source_slice_axis": ("aggregate_by_source_slice_axis.csv", "source_slice_axis"),
        "aggregate_by_source_slice_value": ("aggregate_by_source_slice_value.csv", "source_slice_value"),
        "aggregate_by_pack": ("aggregate_by_pack.csv", "pack_id"),
        "aggregate_by_role_family": ("aggregate_by_role_family.csv", "role_family"),
        "aggregate_by_scenario_family": ("aggregate_by_scenario_family.csv", "scenario_family_id"),
        "aggregate_by_profile_seed": ("aggregate_by_profile_seed.csv", "profile_seed"),
        "aggregate_by_profile": ("aggregate_by_profile.csv", "profile_name"),
        "aggregate_by_obstacle_label": ("aggregate_by_obstacle_label.csv", "sampled_obstacle_label"),
        "aggregate_by_timing_bucket": ("aggregate_by_timing_bucket.csv", "obstacle_longitudinal_timing_bucket"),
        "aggregate_by_lateral_bucket": ("aggregate_by_lateral_bucket.csv", "obstacle_lateral_offset_bucket"),
        "aggregate_by_hidden_dynamics_bucket": ("aggregate_by_hidden_dynamics_bucket.csv", "hidden_dynamics_bucket"),
    }
    for artifact_key, (filename, group_key) in aggregate_specs.items():
        _write_aggregate(
            output_dir=output_dir,
            artifacts=artifacts,
            rows=episode_rows,
            artifact_key=artifact_key,
            filename=filename,
            group_key=group_key,
        )

    candidate_profile_path = output_dir / "aggregate_by_candidate_profile.csv"
    write_csv_rows(
        candidate_profile_path,
        _aggregate_by_two_keys(episode_rows, group_axis="candidate_profile", key_a="candidate_id", key_b="profile_name"),
        fieldnames=AGGREGATE_FIELDNAMES,
    )
    artifacts["aggregate_by_candidate_profile"] = str(candidate_profile_path)
    candidate_pack_path = output_dir / "aggregate_by_candidate_pack.csv"
    write_csv_rows(
        candidate_pack_path,
        _aggregate_by_two_keys(episode_rows, group_axis="candidate_pack", key_a="candidate_id", key_b="pack_id"),
        fieldnames=AGGREGATE_FIELDNAMES,
    )
    artifacts["aggregate_by_candidate_pack"] = str(candidate_pack_path)

    candidate_count = len({str(spec.get("candidate_id", "")) for spec in scenario_specs})
    candidate_scenario_reference_count = len(
        {
            (
                str(spec.get("candidate_id", "")),
                str(spec.get("pack_id", "")),
                str(spec.get("scenario_spec_id", "")),
            )
            for spec in scenario_specs
        }
    )
    unique_pack_scenario_count = len(
        {(str(spec.get("pack_id", "")), str(spec.get("scenario_spec_id", ""))) for spec in scenario_specs}
    )
    selected_checkpoint_count = len({str(row.get("selected_key", "")) for row in workload})
    selected_checkpoint_count_from_rows = len({str(row.get("matrix_id", "")) for row in episode_rows})
    label_mismatch_count = int(sum(not _bool(row.get("sampled_label_matches_spec"), default=False) for row in episode_rows))
    guardrail_flags = {key: False for key in (*base_runner.FORBIDDEN_GUARDRAILS, *EXTRA_GUARDRAIL_FIELDS)}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    actor_contract_violation_count = _actor_contract_violation_count(validation_failures)
    passes = (
        len(episode_rows) == int(target_episode_count)
        and len(failure_rows) == 0
        and len(validation_failures) == 0
        and candidate_count == int(target_candidate_count)
        and candidate_scenario_reference_count == int(target_candidate_scenario_reference_count)
        and selected_checkpoint_count_from_rows == int(target_selected_checkpoint_count)
        and not missing_rows
        and not metric_failures
        and actor_contract_violation_count == 0
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
        "source_candidate_count": candidate_count,
        "target_candidate_count": int(target_candidate_count),
        "candidate_scenario_reference_count": candidate_scenario_reference_count,
        "target_candidate_scenario_reference_count": int(target_candidate_scenario_reference_count),
        "unique_pack_scenario_count": unique_pack_scenario_count,
        "selected_checkpoint_count": selected_checkpoint_count_from_rows,
        "planned_selected_checkpoint_count": selected_checkpoint_count,
        "target_selected_checkpoint_count": int(target_selected_checkpoint_count),
        "metadata_missing_count": len(missing_rows),
        "metric_completeness_failure_count": len(metric_failures),
        "all_selected_metrics_finite": not metric_failures,
        "actor_contract_violation_count": actor_contract_violation_count,
        "label_mismatch_count": label_mismatch_count,
        "candidate_counts": _count_by(episode_rows, "candidate_id"),
        "repair_family_counts": _count_by(episode_rows, "repair_family"),
        "source_slice_axis_counts": _count_by(episode_rows, "source_slice_axis"),
        "pack_counts": _count_by(episode_rows, "pack_id"),
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
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
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


def run_effective_candidate_measured_validation(
    *,
    source_dir: Path | str = DEFAULT_SOURCE_DIR,
    reset_validation_dir: Path | str = DEFAULT_RESET_VALIDATION_DIR,
    selected_rows_path: Path | str = DEFAULT_SELECTED_ROWS,
    config_root: Path | str = DEFAULT_CONFIG_ROOT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_candidate_count: int = TARGET_CANDIDATE_COUNT,
    target_candidate_scenario_reference_count: int = TARGET_CANDIDATE_SCENARIO_REFERENCE_COUNT,
    target_selected_checkpoint_count: int = TARGET_SELECTED_CHECKPOINT_COUNT,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    reset_summary = read_json(Path(reset_validation_dir) / "summary.json")
    if str(reset_summary.get("result_class", "")).endswith("_pass") is False:
        raise ValueError("reset validation summary is not a pass")
    scenario_specs = load_effective_candidate_scenario_specs(source_dir)
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
            scenario_specs=scenario_specs,
            selected_rows=selected_rows,
            workload=workload,
            target_candidate_count=int(target_candidate_count),
            target_candidate_scenario_reference_count=int(target_candidate_scenario_reference_count),
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
        scenario = scenario_specs[int(row["effective_candidate_scenario_index"])]
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
        scenario_specs=scenario_specs,
        selected_rows=selected_rows,
        workload=workload,
        target_candidate_count=int(target_candidate_count),
        target_candidate_scenario_reference_count=int(target_candidate_scenario_reference_count),
        target_selected_checkpoint_count=int(target_selected_checkpoint_count),
        target_episode_count=int(target_episode_count),
        next_blocker=str(next_blocker),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--reset-validation-dir", type=Path, default=DEFAULT_RESET_VALIDATION_DIR)
    parser.add_argument("--selected-rows", type=Path, default=DEFAULT_SELECTED_ROWS)
    parser.add_argument("--config-root", type=Path, default=DEFAULT_CONFIG_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-candidate-count", type=int, default=TARGET_CANDIDATE_COUNT)
    parser.add_argument(
        "--target-candidate-scenario-reference-count",
        type=int,
        default=TARGET_CANDIDATE_SCENARIO_REFERENCE_COUNT,
    )
    parser.add_argument("--target-selected-checkpoint-count", type=int, default=TARGET_SELECTED_CHECKPOINT_COUNT)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_effective_candidate_measured_validation(
        source_dir=args.source_dir,
        reset_validation_dir=args.reset_validation_dir,
        selected_rows_path=args.selected_rows,
        config_root=args.config_root,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        target_candidate_count=int(args.target_candidate_count),
        target_candidate_scenario_reference_count=int(args.target_candidate_scenario_reference_count),
        target_selected_checkpoint_count=int(args.target_selected_checkpoint_count),
        target_episode_count=int(args.target_episode_count),
        device=str(args.device),
        resume=not bool(args.no_resume),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"source_candidate_count={summary['source_candidate_count']}")
    print(f"candidate_scenario_reference_count={summary['candidate_scenario_reference_count']}")
    print(f"selected_checkpoint_count={summary['selected_checkpoint_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"metadata_missing_count={summary['metadata_missing_count']}")
    print(f"metric_completeness_failure_count={summary['metric_completeness_failure_count']}")
    print(f"actor_contract_violation_count={summary['actor_contract_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
