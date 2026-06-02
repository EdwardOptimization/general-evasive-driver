"""Measured validation for source-linked offtrack containment reset targets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_scenario_task_family_measured_execution as base_runner
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import append_csv_row, completed_workload_ids, write_run_state


DEFAULT_SOURCE_RESET_DIR = Path(
    "runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence"
)
DEFAULT_SOURCE_EFFECTIVE_DIR = Path(
    "runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization"
)
DEFAULT_SELECTED_ROWS = Path(
    "runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/"
    "selected_checkpoint_rows.csv"
)
DEFAULT_CONFIG_ROOT = Path(
    "runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation"
)
DEFAULT_EVAL_SEED_BASE = 241300
TARGET_RESET_TARGET_COUNT = 350
TARGET_SELECTED_CHECKPOINT_COUNT = 15
TARGET_EPISODE_COUNT = TARGET_RESET_TARGET_COUNT * TARGET_SELECTED_CHECKPOINT_COUNT
DEFAULT_NEXT_BLOCKER = (
    "m2414-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-result-audit"
)
RESULT_PASS = "current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_pass"
RESULT_FAIL = "current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_incomplete_or_fail"
ACTOR_CONTRACT_ID = "P0_human_view_no_wheel_no_oracle"

RESET_TARGET_METADATA_FIELDS = (
    "reset_target_index",
    "reset_target_key",
    "env_config_hash",
    "pack_id",
    "scenario_spec_id",
    "family_ids",
    "family_count",
    "effective_candidate_ids",
    "effective_candidate_count",
    "scenario_reference_count",
)
PACK_METADATA_FIELDS = ("pack_index",)
EXTRA_GUARDRAIL_FIELDS = (
    "support_policy_ranking_claim_made",
    "scenario_redesign_executed_claim_made",
    "current_sim_verdict_claim_made",
    "training_repair_success_claim_made",
    "candidate_family_ranking_claim_made",
)
WORKLOAD_METADATA_FIELDS = base_runner._extend_unique(
    base_runner.WORKLOAD_METADATA_FIELDS,
    [
        "selected_key",
        "reset_target_index",
        "reset_target_key",
        "env_config_hash",
        "family_ids",
        "family_count",
        "effective_candidate_ids",
        "effective_candidate_count",
        "scenario_reference_count",
        *PACK_METADATA_FIELDS,
    ],
)
EPISODE_FIELDNAMES = base_runner._extend_unique(
    base_runner.EPISODE_FIELDNAMES,
    [
        *RESET_TARGET_METADATA_FIELDS,
        *PACK_METADATA_FIELDS,
        *EXTRA_GUARDRAIL_FIELDS,
        "source_linked_measured_validation",
    ],
)
FAILURE_FIELDNAMES = base_runner._extend_unique(
    base_runner.FAILURE_FIELDNAMES,
    [
        *RESET_TARGET_METADATA_FIELDS,
        *PACK_METADATA_FIELDS,
        *EXTRA_GUARDRAIL_FIELDS,
    ],
)
MEMBERSHIP_FIELDNAMES = base_runner._extend_unique(
    EPISODE_FIELDNAMES,
    [
        "family_id",
        "family_profile_key",
        "family_pack_key",
    ],
)
VALIDATION_FAILURE_FIELDNAMES = base_runner.VALIDATION_FAILURE_FIELDNAMES
METADATA_MISSING_FIELDNAMES = base_runner.METADATA_MISSING_FIELDNAMES
METRIC_COMPLETENESS_FIELDNAMES = base_runner.METRIC_COMPLETENESS_FIELDNAMES
AGGREGATE_FIELDNAMES = base_runner.AGGREGATE_FIELDNAMES
CLAIM_FIELDNAMES = base_runner.CLAIM_FIELDNAMES
RolloutFunction = Callable[[Mapping[str, Any], Mapping[str, Any], int], Mapping[str, Any]]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    return base_runner._bool(value, default=default)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return base_runner._count_by(rows, key)


def _json_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _reset_target_key(pack_id: str, scenario_spec_id: str, env_config: Mapping[str, Any]) -> str:
    return f"{pack_id}|{scenario_spec_id}|{_json_hash(env_config)[:16]}"


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


def _pack_index(pack_id: str) -> int:
    order = {
        "baseline_reference_pack": 0,
        "g_primary_pack": 1,
        "h_primary_pack": 2,
        "g_h_primary_pack": 3,
        "gh_minimal_pack": 4,
    }
    return int(order.get(str(pack_id), len(order)))


def _family_list(value: Any) -> list[str]:
    return [item for item in str(value or "").split("|") if item]


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


def _actor_contract_pass(spec: Mapping[str, Any]) -> bool:
    env_config = spec.get("env_config") if isinstance(spec.get("env_config"), Mapping) else {}
    return (
        str(spec.get("actor_contract_id", "")) == ACTOR_CONTRACT_ID
        and not _bool(env_config.get("include_privileged_params"))
        and str(env_config.get("wheel_observation_mode", "")) == "none"
        and str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero"
        and int(env_config.get("history_length", -1)) == 1
    )


def load_selected_rows(path: Path | str = DEFAULT_SELECTED_ROWS) -> list[dict[str, str]]:
    return base_runner.load_selected_rows(path)


def _reset_target_rows(source_reset_dir: Path | str) -> list[dict[str, str]]:
    return sorted(
        read_csv_rows(Path(source_reset_dir) / "reset_target_rows.csv"),
        key=lambda row: str(row.get("reset_target_key", "")),
    )


def _env_specs_by_reset_target(source_effective_dir: Path | str) -> dict[str, dict[str, Any]]:
    source = Path(source_effective_dir)
    rows = read_csv_rows(source / "effective_candidate_config_rows.csv")
    specs: dict[str, dict[str, Any]] = {}
    for row in rows:
        config_path = Path(str(row.get("effective_candidate_config_path", "")))
        payload = read_json(config_path)
        selected_specs = payload.get("selected_scenario_specs", [])
        if not isinstance(selected_specs, list):
            raise ValueError(f"effective candidate config has no selected_scenario_specs: {config_path}")
        for selected in selected_specs:
            env_config = selected.get("env_config")
            if not isinstance(env_config, Mapping):
                continue
            key = _reset_target_key(
                str(selected.get("pack_id", "")),
                str(selected.get("scenario_spec_id", "")),
                dict(env_config),
            )
            spec = dict(selected)
            spec["env_config"] = dict(env_config)
            spec.update(_scenario_defaults(spec))
            spec["pack_index"] = _pack_index(str(spec.get("pack_id", "")))
            existing = specs.get(key)
            if existing is not None and _json_hash(existing["env_config"]) != _json_hash(spec["env_config"]):
                raise ValueError(f"reset target env_config hash conflict: {key}")
            specs.setdefault(key, spec)
    return specs


def load_source_linked_reset_target_specs(
    *,
    source_reset_dir: Path | str = DEFAULT_SOURCE_RESET_DIR,
    source_effective_dir: Path | str = DEFAULT_SOURCE_EFFECTIVE_DIR,
) -> list[dict[str, Any]]:
    reset_rows = _reset_target_rows(source_reset_dir)
    env_specs = _env_specs_by_reset_target(source_effective_dir)
    specs: list[dict[str, Any]] = []
    for index, row in enumerate(reset_rows):
        reset_key = str(row.get("reset_target_key", ""))
        if reset_key not in env_specs:
            raise ValueError(f"missing env_config for reset target: {reset_key}")
        spec = dict(env_specs[reset_key])
        family_ids = str(row.get("family_ids", ""))
        effective_candidate_ids = str(row.get("effective_candidate_ids", ""))
        spec.update(
            {
                "reset_target_index": int(index),
                "reset_target_key": reset_key,
                "env_config_hash": str(row.get("env_config_hash", "")),
                "pack_id": str(row.get("pack_id", spec.get("pack_id", ""))),
                "scenario_spec_id": str(row.get("scenario_spec_id", spec.get("scenario_spec_id", ""))),
                "family_ids": family_ids,
                "family_count": len(_family_list(family_ids)),
                "effective_candidate_ids": effective_candidate_ids,
                "effective_candidate_count": len(_family_list(effective_candidate_ids)),
                "scenario_reference_count": int(row.get("scenario_reference_count", 0) or 0),
                "actor_contract_guardrail_pass": _actor_contract_pass(spec),
            }
        )
        specs.append(spec)
    return specs


def eval_seed_for_cell(*, eval_seed_base: int, selected_index: int, reset_target_index: int) -> int:
    return int(eval_seed_base) + int(selected_index) * 100000 + int(reset_target_index)


def workload_rows(
    *,
    reset_target_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    config_root: Path | str,
    eval_seed_base: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = Path(config_root)
    for selected_index, selected in enumerate(selected_rows):
        selected_key = base_runner._selected_key(selected)
        for spec in reset_target_specs:
            reset_index = int(spec["reset_target_index"])
            reset_key = str(spec.get("reset_target_key", ""))
            eval_seed = eval_seed_for_cell(
                eval_seed_base=int(eval_seed_base),
                selected_index=int(selected_index),
                reset_target_index=int(reset_index),
            )
            rows.append(
                {
                    "workload_id": f"{selected_key}::{reset_key}",
                    "scenario_index": int(reset_index),
                    "reset_target_index": int(reset_index),
                    "selected_checkpoint_index": int(selected_index),
                    "eval_seed": int(eval_seed),
                    "profile_seed": base_runner._profile_seed(selected),
                    "profile_config_path": str(base_runner._config_path(root, selected)),
                    "scenario_spec_id": str(spec.get("scenario_spec_id", "")),
                    "selected_key": selected_key,
                    "reset_target_key": reset_key,
                    "env_config_hash": str(spec.get("env_config_hash", "")),
                    "family_ids": str(spec.get("family_ids", "")),
                    "family_count": int(spec.get("family_count", 0) or 0),
                    "effective_candidate_ids": str(spec.get("effective_candidate_ids", "")),
                    "effective_candidate_count": int(spec.get("effective_candidate_count", 0) or 0),
                    "scenario_reference_count": int(spec.get("scenario_reference_count", 0) or 0),
                    "pack_id": str(spec.get("pack_id", "")),
                    "pack_index": int(spec.get("pack_index", 0) or 0),
                }
            )
    return rows


def _workload_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in WORKLOAD_METADATA_FIELDS}


def _reset_target_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {field: spec.get(field, "") for field in RESET_TARGET_METADATA_FIELDS}


def _pack_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {field: spec.get(field, "") for field in PACK_METADATA_FIELDS}


def merged_metadata(
    *,
    workload_row: Mapping[str, Any],
    reset_target_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        **_workload_metadata(workload_row),
        **base_runner._scenario_metadata(reset_target_spec),
        **_reset_target_metadata(reset_target_spec),
        **_pack_metadata(reset_target_spec),
        **base_runner._selected_metadata(selected_row),
    }


def metadata_missing_rows(
    *,
    workload: Sequence[Mapping[str, Any]],
    reset_target_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    required_fields = (
        *WORKLOAD_METADATA_FIELDS,
        *base_runner.SCENARIO_METADATA_FIELDS,
        *base_runner.SELECTED_METADATA_FIELDS,
        *RESET_TARGET_METADATA_FIELDS,
        *PACK_METADATA_FIELDS,
    )
    rows: list[dict[str, Any]] = []
    for workload_row in workload:
        spec = reset_target_specs[int(workload_row["reset_target_index"])]
        selected = selected_rows[int(workload_row["selected_checkpoint_index"])]
        metadata = merged_metadata(workload_row=workload_row, reset_target_spec=spec, selected_row=selected)
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
    reset_target_specs: Sequence[Mapping[str, Any]],
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
    for index, spec in enumerate(reset_target_specs):
        reset_key = str(spec.get("reset_target_key", f"reset_{index:03d}"))
        env_config = spec.get("env_config")
        if not isinstance(env_config, Mapping):
            failures.append({"workload_id": reset_key, "error_type": "missing_scenario_field", "error_message": "env_config"})
            env_config = {}
        for field in base_runner.SCENARIO_METADATA_FIELDS:
            if not str(spec.get(field, "")).strip():
                failures.append({"workload_id": reset_key, "error_type": "missing_scenario_field", "error_message": field})
        for field in RESET_TARGET_METADATA_FIELDS:
            if not str(spec.get(field, "")).strip():
                failures.append({"workload_id": reset_key, "error_type": "missing_reset_target_field", "error_message": field})
        if str(spec.get("actor_contract_id", "")) != ACTOR_CONTRACT_ID:
            failures.append({"workload_id": reset_key, "error_type": "actor_contract_violation", "error_message": "actor_contract_id"})
        if int(spec.get("contract_violation_count", 0) or 0) != 0:
            failures.append({"workload_id": reset_key, "error_type": "actor_contract_violation", "error_message": "contract_violation_count"})
        if _bool(env_config.get("include_privileged_params"), default=False):
            failures.append({"workload_id": reset_key, "error_type": "actor_contract_violation", "error_message": "include_privileged_params"})
        if str(env_config.get("wheel_observation_mode", "")) != "none":
            failures.append({"workload_id": reset_key, "error_type": "actor_contract_violation", "error_message": "wheel_observation_mode"})
        if str(env_config.get("obstacle_relative_velocity_mode", "")) != "zero":
            failures.append({"workload_id": reset_key, "error_type": "actor_contract_violation", "error_message": "obstacle_relative_velocity_mode"})
        if int(env_config.get("history_length", 0) or 0) != 1:
            failures.append({"workload_id": reset_key, "error_type": "actor_contract_violation", "error_message": "history_length"})
        if not _bool(spec.get("actor_contract_guardrail_pass"), default=True):
            failures.append({"workload_id": reset_key, "error_type": "actor_contract_violation", "error_message": "actor_contract_guardrail_pass"})
        for flag in (
            "labels_enter_actor_input",
            "ranking_admissible",
            "paper_level_claim_made",
            "level3_self_id_claim_made",
            "execution_blocked_by_unsupported_capability",
            "scenario_redesign_executed_claim_made",
        ):
            if _bool(spec.get(flag), default=False):
                failures.append({"workload_id": reset_key, "error_type": "guardrail_violation", "error_message": flag})
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
            "claim": "source_linked_measured_validation_completed",
            "admissible": True,
            "reason": "episode rows are measured rollout artifacts when the runner completes",
        },
        {
            "claim": "candidate_family_ranking",
            "admissible": False,
            "reason": "family membership is overlapping diagnostic metadata, not a ranking axis",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2413 does not rank controller families",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2413 does not select or promote a controller family or candidate",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2413 measures existing selected checkpoints and does not execute repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2413 does not train or evaluate a trained repair",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2413 is a public measured-validation panel, not a paper-level statistical result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2413 does not execute a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2413 does not run wrong-history, reset-hidden, or zero-history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2413 must be audited and compared before a current-sim verdict",
        },
    ]


def measured_episode_row(
    *,
    workload_row: Mapping[str, Any],
    reset_target_spec: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    rollout_metrics: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    row = base_runner.measured_episode_row(
        workload_row=workload_row,
        scenario_spec=reset_target_spec,
        selected_row=selected_row,
        rollout_metrics=rollout_metrics,
        eval_seed=int(eval_seed),
    )
    row.update(
        {
            **merged_metadata(workload_row=workload_row, reset_target_spec=reset_target_spec, selected_row=selected_row),
            "support_policy_ranking_claim_made": False,
            "scenario_redesign_executed_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "training_repair_success_claim_made": False,
            "candidate_family_ranking_claim_made": False,
            "source_linked_measured_validation": True,
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
    row = base_runner.measured_failure_row(
        workload_row=workload_row,
        scenario_spec=reset_target_spec,
        selected_row=selected_row,
        eval_seed=int(eval_seed),
        error=error,
    )
    row.update(
        {
            **merged_metadata(workload_row=workload_row, reset_target_spec=reset_target_spec, selected_row=selected_row),
            "support_policy_ranking_claim_made": False,
            "scenario_redesign_executed_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "training_repair_success_claim_made": False,
            "candidate_family_ranking_claim_made": False,
        }
    )
    return row


def _membership_rows(episode_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        for family_id in _family_list(episode.get("family_ids")):
            row = dict(episode)
            row["family_id"] = family_id
            row["family_profile_key"] = f"{family_id}|{episode.get('profile_name', '')}"
            row["family_pack_key"] = f"{family_id}|{episode.get('pack_id', '')}"
            rows.append(row)
    return rows


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
    reset_target_specs: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    workload: Sequence[Mapping[str, Any]],
    target_reset_target_count: int,
    target_selected_checkpoint_count: int,
    target_episode_count: int,
    next_blocker: str,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    validation_failures = read_csv_rows(output_dir / "validation_failure_rows.csv")
    missing_rows = metadata_missing_rows(workload=workload, reset_target_specs=reset_target_specs, selected_rows=selected_rows)
    metric_failures = base_runner.metric_completeness_failure_rows(episode_rows)
    membership_rows = _membership_rows(episode_rows)

    write_csv_rows(output_dir / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(output_dir / "metric_completeness_failures.csv", metric_failures, fieldnames=METRIC_COMPLETENESS_FIELDNAMES)
    write_csv_rows(output_dir / "episode_family_membership_rows.csv", membership_rows, fieldnames=MEMBERSHIP_FIELDNAMES)
    write_csv_rows(output_dir / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    artifacts: dict[str, str] = {
        "summary": str(output_dir / "summary.json"),
        "episode_rows": str(output_dir / "episode_rows.csv"),
        "episode_family_membership_rows": str(output_dir / "episode_family_membership_rows.csv"),
        "failure_rows": str(output_dir / "failure_rows.csv"),
        "validation_failure_rows": str(output_dir / "validation_failure_rows.csv"),
        "metadata_missing_rows": str(output_dir / "metadata_missing_rows.csv"),
        "metric_completeness_failures": str(output_dir / "metric_completeness_failures.csv"),
        "claim_boundary": str(output_dir / "claim_boundary.csv"),
        "run_state": str(output_dir / "run_state.json"),
    }
    aggregate_specs = {
        "aggregate_by_reset_target": ("aggregate_by_reset_target.csv", "reset_target_key"),
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
    _write_aggregate(
        output_dir=output_dir,
        artifacts=artifacts,
        rows=membership_rows,
        artifact_key="aggregate_by_family_membership",
        filename="aggregate_by_family_membership.csv",
        group_key="family_id",
    )
    family_profile_path = output_dir / "aggregate_by_family_profile.csv"
    write_csv_rows(
        family_profile_path,
        _aggregate_by_two_keys(membership_rows, group_axis="family_profile", key_a="family_id", key_b="profile_name"),
        fieldnames=AGGREGATE_FIELDNAMES,
    )
    artifacts["aggregate_by_family_profile"] = str(family_profile_path)
    family_pack_path = output_dir / "aggregate_by_family_pack.csv"
    write_csv_rows(
        family_pack_path,
        _aggregate_by_two_keys(membership_rows, group_axis="family_pack", key_a="family_id", key_b="pack_id"),
        fieldnames=AGGREGATE_FIELDNAMES,
    )
    artifacts["aggregate_by_family_pack"] = str(family_pack_path)

    reset_target_count = len({str(spec.get("reset_target_key", "")) for spec in reset_target_specs})
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
        and reset_target_count == int(target_reset_target_count)
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
        "source_reset_target_count": reset_target_count,
        "target_reset_target_count": int(target_reset_target_count),
        "selected_checkpoint_count": selected_checkpoint_count_from_rows,
        "planned_selected_checkpoint_count": selected_checkpoint_count,
        "target_selected_checkpoint_count": int(target_selected_checkpoint_count),
        "family_membership_row_count": len(membership_rows),
        "metadata_missing_count": len(missing_rows),
        "metric_completeness_failure_count": len(metric_failures),
        "all_selected_metrics_finite": not metric_failures,
        "actor_contract_violation_count": actor_contract_violation_count,
        "label_mismatch_count": label_mismatch_count,
        "reset_target_counts_by_pack": _count_by(reset_target_specs, "pack_id"),
        "family_membership_counts": _count_by(membership_rows, "family_id"),
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
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "candidate_family_ranking_claim_made": False,
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


def run_source_linked_offtrack_containment_measured_validation(
    *,
    source_reset_dir: Path | str = DEFAULT_SOURCE_RESET_DIR,
    source_effective_dir: Path | str = DEFAULT_SOURCE_EFFECTIVE_DIR,
    selected_rows_path: Path | str = DEFAULT_SELECTED_ROWS,
    config_root: Path | str = DEFAULT_CONFIG_ROOT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_reset_target_count: int = TARGET_RESET_TARGET_COUNT,
    target_selected_checkpoint_count: int = TARGET_SELECTED_CHECKPOINT_COUNT,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    reset_summary = read_json(Path(source_reset_dir) / "summary.json")
    if str(reset_summary.get("result_class", "")).endswith("_pass") is False:
        raise ValueError("source reset summary is not a pass")
    reset_target_specs = load_source_linked_reset_target_specs(
        source_reset_dir=source_reset_dir,
        source_effective_dir=source_effective_dir,
    )
    selected_rows = load_selected_rows(selected_rows_path)
    workload = workload_rows(
        reset_target_specs=reset_target_specs,
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
        reset_target_specs=reset_target_specs,
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
            reset_target_specs=reset_target_specs,
            selected_rows=selected_rows,
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
        reset_target = reset_target_specs[int(row["reset_target_index"])]
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
                    scenario_spec=reset_target,
                    selected_row=selected,
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
                    reset_target_spec=reset_target,
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
        reset_target_specs=reset_target_specs,
        selected_rows=selected_rows,
        workload=workload,
        target_reset_target_count=int(target_reset_target_count),
        target_selected_checkpoint_count=int(target_selected_checkpoint_count),
        target_episode_count=int(target_episode_count),
        next_blocker=str(next_blocker),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-reset-dir", type=Path, default=DEFAULT_SOURCE_RESET_DIR)
    parser.add_argument("--source-effective-dir", type=Path, default=DEFAULT_SOURCE_EFFECTIVE_DIR)
    parser.add_argument("--selected-rows", type=Path, default=DEFAULT_SELECTED_ROWS)
    parser.add_argument("--config-root", type=Path, default=DEFAULT_CONFIG_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-reset-target-count", type=int, default=TARGET_RESET_TARGET_COUNT)
    parser.add_argument("--target-selected-checkpoint-count", type=int, default=TARGET_SELECTED_CHECKPOINT_COUNT)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_source_linked_offtrack_containment_measured_validation(
        source_reset_dir=args.source_reset_dir,
        source_effective_dir=args.source_effective_dir,
        selected_rows_path=args.selected_rows,
        config_root=args.config_root,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
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
    print(f"family_membership_row_count={summary['family_membership_row_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"metadata_missing_count={summary['metadata_missing_count']}")
    print(f"metric_completeness_failure_count={summary['metric_completeness_failure_count']}")
    print(f"actor_contract_violation_count={summary['actor_contract_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
