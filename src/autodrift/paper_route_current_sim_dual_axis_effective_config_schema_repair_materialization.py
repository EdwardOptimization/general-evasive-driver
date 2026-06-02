"""Run-dir effective candidate pack materialization from overlay candidates."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_CANDIDATE_SOURCE_DIR = Path(
    "runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation"
)
DEFAULT_BASE_PACK_MANIFEST = Path(
    "runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization"
)
DEFAULT_TARGET_CANDIDATE_CONFIG_COUNT = 54
DEFAULT_TARGET_BASE_PACK_COUNT = 5
DEFAULT_TARGET_BASE_SCENARIO_SPECS_PER_PACK = 72
DEFAULT_NEXT_BLOCKER = (
    "m2392-paper-route-current-sim-dual-axis-effective-config-materialization-branch-synthesis"
)
RESULT_PASS = "current_sim_dual_axis_effective_config_schema_repair_materialization_pass"
RESULT_FAIL = "current_sim_dual_axis_effective_config_schema_repair_materialization_fail"
ACTOR_CONTRACT_ID = "P0_human_view_no_wheel_no_oracle"

EFFECTIVE_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "repair_family",
    "source_slice_axis",
    "source_slice_value",
    "source_candidate_config_path",
    "effective_candidate_config_path",
    "static_validation_pass",
    "effective_candidate_config_written",
    "effective_candidate_config_inside_run_dir",
    "selected_scenario_count",
    "selected_base_pack_count",
    "candidate_without_matching_scenarios",
    "candidate_without_env_config",
    "actor_contract_violation_count",
    "active_config_overwritten",
    "environment_load_attempted",
    "environment_reset_attempted",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
    "failure_reasons",
]
SCENARIO_FIELDNAMES = [
    "candidate_id",
    "pack_id",
    "pack_path",
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "source_slice_axis",
    "source_slice_value",
    "actor_contract_id",
    "include_privileged_params",
    "wheel_observation_mode",
    "obstacle_relative_velocity_mode",
    "history_length",
    "env_config_present",
    "actor_contract_guardrail_pass",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_filename(candidate_id: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in candidate_id).strip("_")


def _effective_candidate_path(output_dir: Path, candidate_id: str) -> Path:
    return output_dir / "effective_candidate_configs" / f"{_safe_filename(candidate_id)}.json"


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _claim_boundary_forbids_execution(payload: Mapping[str, Any]) -> bool:
    boundary = payload.get("claim_boundary")
    if not isinstance(boundary, Mapping):
        return False
    forbidden_true_keys = [
        "active_config_overwritten",
        "loaded_into_environment",
        "environment_reset_started",
        "repair_execution_started",
        "training_started",
        "ranking_admissible",
        "winner_selected",
    ]
    return not any(_bool(boundary.get(key)) for key in forbidden_true_keys)


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_effective_candidate_pack_materialization",
            "admissible": True,
            "reason": "M2391 may claim only run-dir effective candidate pack artifact materialization",
        },
        {
            "claim": "environment_load_or_reset",
            "admissible": False,
            "reason": "M2391 does not construct or reset environments",
        },
        {
            "claim": "active_config_overwrite",
            "admissible": False,
            "reason": "M2391 writes only under its run directory",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2391 does not execute reward, curriculum, guardrail, or training repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2391 does not train or evaluate a repaired driver",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "effective candidate pack materialization does not rank controller families",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "effective candidate pack materialization does not rank support policies",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2391 does not select a winning candidate",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2391 is infrastructure, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2391 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2391 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2391 does not run validation needed for a current-sim verdict",
        },
    ]


def load_base_packs(base_pack_manifest_path: Path | str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_path = Path(base_pack_manifest_path)
    manifest = read_json(manifest_path)
    loaded: list[dict[str, Any]] = []
    for pack_row in manifest.get("packs", []):
        pack_path = Path(str(pack_row.get("pack_path", "")))
        pack_payload = read_json(pack_path)
        loaded.append(
            {
                "pack_id": str(pack_row.get("pack_id", pack_payload.get("config_pack_id", ""))),
                "pack_path": str(pack_path),
                "manifest_row": dict(pack_row),
                "payload": pack_payload,
                "scenario_specs": list(pack_payload.get("scenario_specs", [])),
            }
        )
    return manifest, loaded


def _axis_value_pairs(axis_text: str, value_text: str) -> tuple[list[tuple[str, str]], list[str]]:
    axes = [axis.strip() for axis in str(axis_text).split("+") if axis.strip()]
    values = [value.strip() for value in str(value_text).split("|") if value.strip()]
    failures: list[str] = []
    if not axes or not values:
        failures.append("empty_slice_axis_or_value")
    if len(axes) != len(values):
        failures.append("slice_axis_value_arity_mismatch")
    return list(zip(axes, values)), failures


def _scenario_matches(spec: Mapping[str, Any], pairs: Sequence[tuple[str, str]]) -> bool:
    return all(str(spec.get(axis, "")) == value for axis, value in pairs)


def _env_config(spec: Mapping[str, Any]) -> Mapping[str, Any] | None:
    env_config = spec.get("env_config")
    return env_config if isinstance(env_config, Mapping) else None


def _actor_contract_pass(spec: Mapping[str, Any]) -> bool:
    env_config = _env_config(spec)
    if env_config is None:
        return False
    return (
        str(spec.get("actor_contract_id", "")) == ACTOR_CONTRACT_ID
        and str(env_config.get("include_privileged_params", "")).lower() == "false"
        and str(env_config.get("wheel_observation_mode", "")) == "none"
        and str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero"
        and int(env_config.get("history_length", -1)) == 1
    )


def _selected_scenario_payload(
    *,
    candidate_id: str,
    source_slice_axis: str,
    source_slice_value: str,
    pack: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    env_config = _env_config(spec)
    return {
        "candidate_id": candidate_id,
        "pack_id": str(pack.get("pack_id", "")),
        "pack_path": str(pack.get("pack_path", "")),
        "scenario_spec_id": str(spec.get("scenario_spec_id", "")),
        "scenario_family_id": str(spec.get("scenario_family_id", "")),
        "role_family": str(spec.get("role_family", "")),
        "sampled_obstacle_label": str(spec.get("sampled_obstacle_label", "")),
        "hidden_dynamics_bucket": str(spec.get("hidden_dynamics_bucket", "")),
        "obstacle_longitudinal_timing_bucket": str(spec.get("obstacle_longitudinal_timing_bucket", "")),
        "obstacle_lateral_offset_bucket": str(spec.get("obstacle_lateral_offset_bucket", "")),
        "source_slice_axis": source_slice_axis,
        "source_slice_value": source_slice_value,
        "env_config": dict(env_config or {}),
        "actor_contract_id": str(spec.get("actor_contract_id", "")),
        "include_privileged_params": bool(env_config and _bool(env_config.get("include_privileged_params"))),
        "wheel_observation_mode": str((env_config or {}).get("wheel_observation_mode", "")),
        "obstacle_relative_velocity_mode": str((env_config or {}).get("obstacle_relative_velocity_mode", "")),
        "history_length": int((env_config or {}).get("history_length", -1)),
        "actor_contract_guardrail_pass": _actor_contract_pass(spec),
    }


def _scenario_row(selected: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": str(selected.get("candidate_id", "")),
        "pack_id": str(selected.get("pack_id", "")),
        "pack_path": str(selected.get("pack_path", "")),
        "scenario_spec_id": str(selected.get("scenario_spec_id", "")),
        "scenario_family_id": str(selected.get("scenario_family_id", "")),
        "role_family": str(selected.get("role_family", "")),
        "source_slice_axis": str(selected.get("source_slice_axis", "")),
        "source_slice_value": str(selected.get("source_slice_value", "")),
        "actor_contract_id": str(selected.get("actor_contract_id", "")),
        "include_privileged_params": bool(selected.get("include_privileged_params")),
        "wheel_observation_mode": str(selected.get("wheel_observation_mode", "")),
        "obstacle_relative_velocity_mode": str(selected.get("obstacle_relative_velocity_mode", "")),
        "history_length": int(selected.get("history_length", -1)),
        "env_config_present": bool(selected.get("env_config")),
        "actor_contract_guardrail_pass": bool(selected.get("actor_contract_guardrail_pass")),
    }


def materialize_effective_candidate(
    *,
    source_dir: Path,
    output_dir: Path,
    candidate_row: Mapping[str, Any],
    base_pack_manifest_path: Path,
    base_reset_summary_path: str,
    base_measured_summary_path: str,
    base_packs: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidate_id = str(candidate_row.get("candidate_id", ""))
    candidate_path = Path(str(candidate_row.get("candidate_config_path", "")))
    effective_path = _effective_candidate_path(output_dir, candidate_id)
    failures: list[str] = []
    payload: dict[str, Any] | None = None
    if not candidate_path.exists():
        failures.append("missing_candidate_config")
    elif not _inside_dir(candidate_path, source_dir):
        failures.append("candidate_config_path_outside_source_dir")
    else:
        payload = dict(read_json(candidate_path))

    if payload is None:
        payload = {}
    if str(payload.get("candidate_id", "")) != candidate_id:
        failures.append("candidate_id_mismatch")
    if not str(payload.get("source_repair_spec_id", "")).strip():
        failures.append("missing_source_repair_spec_id")
    if not str(payload.get("repair_family", "")).strip():
        failures.append("missing_repair_family")
    if len(payload.get("reward_overlay", [])) != 3:
        failures.append("reward_overlay_count_not_3")
    if len(payload.get("curriculum_overlay", [])) != 1:
        failures.append("curriculum_overlay_count_not_1")
    guardrail_overlay = payload.get("guardrail_overlay", {})
    if not isinstance(guardrail_overlay, Mapping) or guardrail_overlay.get("scope_id") != "global_guardrail_scope":
        failures.append("guardrail_scope_not_global")
    if not isinstance(guardrail_overlay, Mapping) or int(guardrail_overlay.get("guardrail_patch_count", -1)) != 284:
        failures.append("guardrail_patch_count_not_284")
    if not _claim_boundary_forbids_execution(payload):
        failures.append("claim_boundary_allows_execution")

    source_slice_axis = str(payload.get("source_slice_axis", ""))
    source_slice_value = str(payload.get("source_slice_value", ""))
    pairs, pair_failures = _axis_value_pairs(source_slice_axis, source_slice_value)
    failures.extend(pair_failures)

    selected: list[dict[str, Any]] = []
    if not pair_failures:
        for pack in base_packs:
            for spec in pack.get("scenario_specs", []):
                if isinstance(spec, Mapping) and _scenario_matches(spec, pairs):
                    selected.append(
                        _selected_scenario_payload(
                            candidate_id=candidate_id,
                            source_slice_axis=source_slice_axis,
                            source_slice_value=source_slice_value,
                            pack=pack,
                            spec=spec,
                        )
                    )

    selected_count = len(selected)
    candidate_without_matching = selected_count == 0
    candidate_without_env_config = any(not bool(item.get("env_config")) for item in selected)
    actor_contract_violation_count = sum(not bool(item.get("actor_contract_guardrail_pass")) for item in selected)
    if candidate_without_matching:
        failures.append("no_matching_scenario_specs")
    if candidate_without_env_config:
        failures.append("selected_scenario_missing_env_config")
    if actor_contract_violation_count:
        failures.append("actor_contract_guardrail_violation")

    static_pass = not failures
    written = False
    inside = False
    if static_pass:
        selected_by_pack = Counter(str(item.get("pack_id", "")) for item in selected)
        effective_payload = {
            "schema_version": "effective_candidate_pack_v1",
            "candidate_id": candidate_id,
            "source_repair_spec_id": str(payload.get("source_repair_spec_id", "")),
            "repair_family": str(payload.get("repair_family", "")),
            "priority_tier": str(payload.get("priority_tier", "")),
            "source_slice_axis": source_slice_axis,
            "source_slice_value": source_slice_value,
            "source_candidate_config_path": str(candidate_path),
            "base_pack_manifest_path": str(base_pack_manifest_path),
            "base_reset_validation_summary_path": str(base_reset_summary_path),
            "base_measured_execution_summary_path": str(base_measured_summary_path),
            "matching_rule": {
                "axis_value_pairs": [{"axis": axis, "value": value} for axis, value in pairs],
                "source": "scenario_spec_metadata",
                "actor_input_used_for_matching": False,
            },
            "selected_scenario_specs": selected,
            "selected_scenario_count": selected_count,
            "selected_scenario_count_by_pack": dict(sorted(selected_by_pack.items())),
            "reward_overlay": payload.get("reward_overlay", []),
            "curriculum_overlay": payload.get("curriculum_overlay", []),
            "guardrail_overlay": payload.get("guardrail_overlay", {}),
            "mixed_guarded_requirements": payload.get("mixed_guarded_requirements", {}),
            "claim_boundary": {
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "environment_reset_started": False,
                "environment_step_count": 0,
                "policy_action_executed": False,
                "rollout_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            },
            "guardrail_flags": {
                "actor_input_contract_changed": False,
                "hidden_oracle_feature_injection": False,
                "profile_specific_tuning": False,
                "active_config_overwritten": False,
                "environment_load_attempted": False,
                "environment_reset_attempted": False,
                "policy_action_executed": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            },
        }
        write_json(effective_path, effective_payload)
        written = True
        inside = _inside_dir(effective_path, output_dir)
        if not inside:
            failures.append("effective_candidate_config_outside_run_dir")

    row = {
        "candidate_id": candidate_id,
        "source_repair_spec_id": str(payload.get("source_repair_spec_id", "")),
        "repair_family": str(payload.get("repair_family", "")),
        "source_slice_axis": source_slice_axis,
        "source_slice_value": source_slice_value,
        "source_candidate_config_path": str(candidate_path),
        "effective_candidate_config_path": str(effective_path) if written else "",
        "static_validation_pass": static_pass,
        "effective_candidate_config_written": written,
        "effective_candidate_config_inside_run_dir": inside,
        "selected_scenario_count": selected_count,
        "selected_base_pack_count": len({str(item.get("pack_id", "")) for item in selected}),
        "candidate_without_matching_scenarios": candidate_without_matching,
        "candidate_without_env_config": candidate_without_env_config,
        "actor_contract_violation_count": actor_contract_violation_count,
        "active_config_overwritten": False,
        "environment_load_attempted": False,
        "environment_reset_attempted": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "failure_reasons": ";".join(failures),
    }
    return row, [_scenario_row(item) for item in selected]


def run_effective_config_schema_repair_materialization(
    *,
    candidate_source_dir: Path | str = DEFAULT_CANDIDATE_SOURCE_DIR,
    base_pack_manifest_path: Path | str = DEFAULT_BASE_PACK_MANIFEST,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_candidate_config_count: int = DEFAULT_TARGET_CANDIDATE_CONFIG_COUNT,
    target_base_pack_count: int = DEFAULT_TARGET_BASE_PACK_COUNT,
    target_base_scenario_specs_per_pack: int = DEFAULT_TARGET_BASE_SCENARIO_SPECS_PER_PACK,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(candidate_source_dir)
    base_manifest_path = Path(base_pack_manifest_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(source / "summary.json")
    source_manifest = read_json(source / "candidate_config_generation_manifest.json")
    candidate_rows = read_csv_rows(source / "candidate_config_rows.csv")
    base_manifest, base_packs = load_base_packs(base_manifest_path)

    base_reset_summary_path = str(
        base_manifest.get(
            "base_reset_validation_summary_path",
            "runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/summary.json",
        )
    )
    base_measured_summary_path = str(
        base_manifest.get(
            "base_measured_execution_summary_path",
            "runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json",
        )
    )
    effective_rows: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []
    for candidate_row in candidate_rows:
        effective_row, selected_rows = materialize_effective_candidate(
            source_dir=source,
            output_dir=output,
            candidate_row=candidate_row,
            base_pack_manifest_path=base_manifest_path,
            base_reset_summary_path=base_reset_summary_path,
            base_measured_summary_path=base_measured_summary_path,
            base_packs=base_packs,
        )
        effective_rows.append(effective_row)
        scenario_rows.extend(selected_rows)

    claim_rows = claim_boundary_rows()
    source_candidate_count = len(candidate_rows)
    static_pass_count = sum(_bool(row.get("static_validation_pass")) for row in effective_rows)
    static_failure_count = source_candidate_count - static_pass_count
    effective_written_count = sum(_bool(row.get("effective_candidate_config_written")) for row in effective_rows)
    outside_count = sum(
        _bool(row.get("effective_candidate_config_written"))
        and not _bool(row.get("effective_candidate_config_inside_run_dir"))
        for row in effective_rows
    )
    without_matching_count = sum(_bool(row.get("candidate_without_matching_scenarios")) for row in effective_rows)
    without_env_config_count = sum(_bool(row.get("candidate_without_env_config")) for row in effective_rows)
    actor_contract_violation_count = sum(int(row.get("actor_contract_violation_count", 0)) for row in effective_rows)
    selected_scenario_reference_count = len(scenario_rows)
    base_pack_count = len(base_packs)
    base_scenario_counts_by_pack = {
        str(pack.get("pack_id", "")): len(pack.get("scenario_specs", [])) for pack in base_packs
    }
    base_scenario_specs_per_pack_count = (
        min(base_scenario_counts_by_pack.values()) if base_scenario_counts_by_pack else 0
    )
    active_config_overwrite_count = 0
    environment_load_attempt_count = 0
    environment_reset_attempt_count = 0
    environment_step_count = 0
    policy_action_executed = False
    guardrail_flags = {
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "environment_load_started": False,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    failure_types_observed = [
        name
        for name, count in [
            ("static_schema_failure", static_failure_count),
            ("effective_config_materialization_failure", without_matching_count + without_env_config_count),
            ("contract_violation", actor_contract_violation_count),
            ("path_safety_failure", outside_count),
        ]
        if count
    ]
    passes = (
        source_summary.get("result_class") == "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"
        and source_manifest.get("result_class")
        == "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"
        and source_candidate_count == int(target_candidate_config_count)
        and static_pass_count == int(target_candidate_config_count)
        and static_failure_count == 0
        and effective_written_count == int(target_candidate_config_count)
        and outside_count == 0
        and without_matching_count == 0
        and without_env_config_count == 0
        and actor_contract_violation_count == 0
        and base_pack_count == int(target_base_pack_count)
        and all(count == int(target_base_scenario_specs_per_pack) for count in base_scenario_counts_by_pack.values())
        and selected_scenario_reference_count > 0
        and active_config_overwrite_count == 0
        and environment_load_attempt_count == 0
        and environment_reset_attempt_count == 0
        and environment_step_count == 0
        and not policy_action_executed
        and guardrail_violation_count == 0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL

    write_csv_rows(output / "effective_candidate_config_rows.csv", effective_rows, fieldnames=EFFECTIVE_FIELDNAMES)
    write_csv_rows(output / "effective_candidate_scenario_rows.csv", scenario_rows, fieldnames=SCENARIO_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)
    manifest = {
        "result_class": result_class,
        "source_artifacts": {
            "candidate_source_dir": str(source),
            "base_pack_manifest": str(base_manifest_path),
            "base_reset_validation_summary": base_reset_summary_path,
            "base_measured_execution_summary": base_measured_summary_path,
        },
        "output_artifacts": {
            "summary": str(output / "summary.json"),
            "effective_candidate_config_rows": str(output / "effective_candidate_config_rows.csv"),
            "effective_candidate_scenario_rows": str(output / "effective_candidate_scenario_rows.csv"),
            "effective_candidate_configs_dir": str(output / "effective_candidate_configs"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "schema_version": "effective_candidate_pack_materialization_v1",
        "environment_loading_allowed": False,
        "active_config_overwrite_allowed": False,
        "repair_execution_allowed": False,
        "guardrail_flags": guardrail_flags,
    }
    write_json(output / "effective_candidate_config_materialization_manifest.json", manifest)
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "candidate_source_dir": str(source),
        "base_pack_manifest": str(base_manifest_path),
        "output_dir": str(output),
        "source_result_class": source_summary.get("result_class", ""),
        "source_candidate_config_count": source_candidate_count,
        "target_candidate_config_count": int(target_candidate_config_count),
        "static_validation_pass_count": static_pass_count,
        "static_validation_failure_count": static_failure_count,
        "effective_candidate_config_written_count": effective_written_count,
        "effective_candidate_config_outside_run_dir_count": outside_count,
        "candidate_without_matching_scenarios_count": without_matching_count,
        "candidate_without_env_config_count": without_env_config_count,
        "actor_contract_violation_count": actor_contract_violation_count,
        "base_pack_count": base_pack_count,
        "target_base_pack_count": int(target_base_pack_count),
        "base_scenario_specs_per_pack_count": base_scenario_specs_per_pack_count,
        "target_base_scenario_specs_per_pack_count": int(target_base_scenario_specs_per_pack),
        "base_scenario_counts_by_pack": base_scenario_counts_by_pack,
        "selected_scenario_reference_count": selected_scenario_reference_count,
        "min_selected_scenario_count": min((int(row.get("selected_scenario_count", 0)) for row in effective_rows), default=0),
        "max_selected_scenario_count": max((int(row.get("selected_scenario_count", 0)) for row in effective_rows), default=0),
        "candidate_repair_family_counts": _count_by(effective_rows, "repair_family"),
        "source_slice_axis_counts": _count_by(effective_rows, "source_slice_axis"),
        "claim_boundary_row_count": len(claim_rows),
        "active_config_overwrite_count": active_config_overwrite_count,
        "active_config_overwritten": False,
        "environment_load_attempt_count": environment_load_attempt_count,
        "environment_load_started": False,
        "environment_reset_attempt_count": environment_reset_attempt_count,
        "environment_reset_started": False,
        "environment_step_count": environment_step_count,
        "policy_action_executed": policy_action_executed,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "ranking_admissible_count": 0,
        "winner_selected_count": 0,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types_observed,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "effective_candidate_config_materialization_manifest": str(
                output / "effective_candidate_config_materialization_manifest.json"
            ),
            "effective_candidate_config_rows": str(output / "effective_candidate_config_rows.csv"),
            "effective_candidate_scenario_rows": str(output / "effective_candidate_scenario_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "effective_candidate_configs_dir": str(output / "effective_candidate_configs"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-source-dir", type=Path, default=DEFAULT_CANDIDATE_SOURCE_DIR)
    parser.add_argument("--base-pack-manifest", type=Path, default=DEFAULT_BASE_PACK_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-candidate-config-count", type=int, default=DEFAULT_TARGET_CANDIDATE_CONFIG_COUNT)
    parser.add_argument("--target-base-pack-count", type=int, default=DEFAULT_TARGET_BASE_PACK_COUNT)
    parser.add_argument(
        "--target-base-scenario-specs-per-pack",
        type=int,
        default=DEFAULT_TARGET_BASE_SCENARIO_SPECS_PER_PACK,
    )
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_effective_config_schema_repair_materialization(
        candidate_source_dir=args.candidate_source_dir,
        base_pack_manifest_path=args.base_pack_manifest,
        output_dir=args.output_dir,
        target_candidate_config_count=int(args.target_candidate_config_count),
        target_base_pack_count=int(args.target_base_pack_count),
        target_base_scenario_specs_per_pack=int(args.target_base_scenario_specs_per_pack),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_candidate_config_count={summary['source_candidate_config_count']}")
    print(f"static_validation_pass_count={summary['static_validation_pass_count']}")
    print(f"effective_candidate_config_written_count={summary['effective_candidate_config_written_count']}")
    print(f"candidate_without_matching_scenarios_count={summary['candidate_without_matching_scenarios_count']}")
    print(f"selected_scenario_reference_count={summary['selected_scenario_reference_count']}")
    print(f"environment_load_attempt_count={summary['environment_load_attempt_count']}")
    print(f"environment_reset_attempt_count={summary['environment_reset_attempt_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
