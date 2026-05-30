"""Reset-only sampling repair preflight for the task-quality scenario taxonomy."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import env_config_for_executable_profile, read_csv_rows
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.env import AutoDriftEnv
from autodrift.task_quality_scenario_taxonomy_execution import (
    DEFAULT_EVAL_SEED_BASE as DEFAULT_M1731_EVAL_SEED_BASE,
    DEFAULT_SCENARIO_MATRIX,
    DEFAULT_SCENARIO_SPECS,
    DEFAULT_UNSUPPORTED_FEATURES,
    TARGET_EPISODE_COUNT,
    TARGET_PROFILE_COUNT,
    TARGET_SCENARIO_FAMILY_COUNT,
    TARGET_SCENARIO_SPEC_COUNT,
    TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT,
    load_scenario_specs,
    load_unsupported_feature_rows,
)
from autodrift.task_quality_scenario_taxonomy_preflight import scenario_spec_csv_row


DEFAULT_OUTPUT_DIR = Path("runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight")
TARGET_RESET_STRESS_ROW_COUNT = TARGET_EPISODE_COUNT
REPAIR_RULE_SOURCE = "m1733_family_repair_v1"
FAMILY_REPAIR_RULES: dict[str, dict[str, Any]] = {
    "aeb_infeasible_stable_aes": {
        "sampling_repair_variant_id": "stable_aes_sampling_window_v1",
        "sampling_repair_reason": "M1731 S2 failed all cells; use high-speed stable-AES feasible window.",
        "updates": {
            "speed_range": (16.0, 24.0),
            "friction_limited_speed": False,
            "obstacle": {
                "distance_range": (12.0, 34.0),
                "half_width_range": (0.35, 0.80),
                "max_sample_attempts": 1000,
            },
        },
    },
    "drift_required_avoidance": {
        "sampling_repair_variant_id": "drift_required_sampling_window_v1",
        "sampling_repair_reason": "M1731 S3 had seed-sensitive failures; use high-speed drift-required feasible window.",
        "updates": {
            "speed_range": (14.0, 22.0),
            "friction_limited_speed": False,
            "obstacle": {
                "distance_range": (10.0, 28.0),
                "half_width_range": (0.45, 0.90),
                "max_sample_attempts": 1000,
            },
        },
    },
    "off_track_boundary_stress": {
        "sampling_repair_variant_id": "boundary_stress_sampling_window_v1",
        "sampling_repair_reason": "M1731 S5 failed all cells; use high-speed boundary-stress AES/drift window.",
        "updates": {
            "speed_range": (14.0, 22.0),
            "friction_limited_speed": False,
            "obstacle": {
                "distance_range": (10.0, 28.0),
                "half_width_range": (0.45, 0.90),
                "max_sample_attempts": 1000,
            },
        },
    },
    "hidden_dynamics_stress": {
        "sampling_repair_variant_id": "hidden_dynamics_sampling_window_v1",
        "sampling_repair_reason": "M1731 S6 failed all cells; use high-speed supported hidden-dynamics stress window.",
        "updates": {
            "speed_range": (14.0, 22.0),
            "friction_limited_speed": False,
            "obstacle": {
                "distance_range": (10.0, 28.0),
                "half_width_range": (0.45, 0.90),
                "max_sample_attempts": 1000,
            },
        },
    },
}


def _value_at_path(data: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = data
    for key in path:
        if not isinstance(value, Mapping):
            return None
        value = value.get(key)
    return value


def _set_nested(data: dict[str, Any], key: str, updates: Mapping[str, Any]) -> None:
    nested = deepcopy(dict(data.get(key) or {}))
    nested.update(dict(updates))
    data[key] = nested


def _apply_updates(env_config: dict[str, Any], updates: Mapping[str, Any]) -> None:
    for key, value in updates.items():
        if key in {"obstacle", "randomization", "friction_step", "warmup_gate"}:
            _set_nested(env_config, key, value)
        else:
            env_config[key] = value


def repair_scenario_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    repaired = deepcopy(dict(spec))
    family = str(repaired["scenario_family"])
    rule = FAMILY_REPAIR_RULES.get(family)
    repaired["m1728_scenario_spec_id"] = str(repaired["scenario_spec_id"])
    if rule is None:
        repaired["sampling_repair_source"] = "m1728_original"
        repaired["sampling_repair_variant_id"] = "no_sampling_repair_needed"
        repaired["sampling_repair_reason"] = "M1731 completed this family without sampling failures."
        repaired["sampling_repair_applied"] = False
        return repaired

    env_config = deepcopy(dict(repaired["env_config"]))
    _apply_updates(env_config, rule["updates"])
    repaired["env_config"] = env_config
    repaired["sampling_repair_source"] = REPAIR_RULE_SOURCE
    repaired["sampling_repair_variant_id"] = str(rule["sampling_repair_variant_id"])
    repaired["sampling_repair_reason"] = str(rule["sampling_repair_reason"])
    repaired["sampling_repair_applied"] = True
    return repaired


def repaired_scenario_specs(
    specs_path: Path | str = DEFAULT_SCENARIO_SPECS,
) -> list[dict[str, Any]]:
    return [repair_scenario_spec(spec) for spec in load_scenario_specs(specs_path)]


def _flatten_update_paths(updates: Mapping[str, Any], prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    paths: list[tuple[str, ...]] = []
    for key, value in updates.items():
        current = (*prefix, str(key))
        if isinstance(value, Mapping):
            paths.extend(_flatten_update_paths(value, current))
        else:
            paths.append(current)
    return paths


def sampling_repair_delta_rows(
    *,
    original_specs: list[Mapping[str, Any]],
    repaired_specs: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    original_by_id = {str(spec["scenario_spec_id"]): spec for spec in original_specs}
    rows: list[dict[str, Any]] = []
    for repaired in repaired_specs:
        scenario_spec_id = str(repaired["scenario_spec_id"])
        original = original_by_id[scenario_spec_id]
        family = str(repaired["scenario_family"])
        rule = FAMILY_REPAIR_RULES.get(family)
        if rule is None:
            rows.append(
                {
                    "scenario_spec_id": scenario_spec_id,
                    "scenario_family": family,
                    "sampling_repair_variant_id": repaired["sampling_repair_variant_id"],
                    "config_path": "",
                    "original_value": "",
                    "repaired_value": "",
                    "repair_applied": False,
                }
            )
            continue
        for path in _flatten_update_paths(rule["updates"]):
            original_path = ("env_config", *path)
            rows.append(
                {
                    "scenario_spec_id": scenario_spec_id,
                    "scenario_family": family,
                    "sampling_repair_variant_id": repaired["sampling_repair_variant_id"],
                    "config_path": ".".join(original_path),
                    "original_value": _value_at_path(original, original_path),
                    "repaired_value": _value_at_path(repaired, original_path),
                    "repair_applied": True,
                }
            )
    return rows


def repaired_scenario_matrix_rows(
    *,
    repaired_specs: list[Mapping[str, Any]],
    matrix_path: Path | str = DEFAULT_SCENARIO_MATRIX,
) -> list[dict[str, Any]]:
    specs_by_id = {str(spec["scenario_spec_id"]): spec for spec in repaired_specs}
    rows = read_csv_rows(matrix_path)
    repaired_rows: list[dict[str, Any]] = []
    for row in rows:
        spec = specs_by_id[str(row["scenario_spec_id"])]
        item = dict(row)
        item.update(
            {
                "m1728_scenario_spec_id": str(spec["m1728_scenario_spec_id"]),
                "sampling_repair_source": str(spec["sampling_repair_source"]),
                "sampling_repair_variant_id": str(spec["sampling_repair_variant_id"]),
                "sampling_repair_applied": bool(spec["sampling_repair_applied"]),
                "reset_stress_scheduled": True,
                "policy_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        )
        repaired_rows.append(item)
    return repaired_rows


def _repaired_spec_csv_row(spec: Mapping[str, Any]) -> dict[str, Any]:
    row = scenario_spec_csv_row(spec)
    row.update(
        {
            "m1728_scenario_spec_id": str(spec["m1728_scenario_spec_id"]),
            "sampling_repair_source": str(spec["sampling_repair_source"]),
            "sampling_repair_variant_id": str(spec["sampling_repair_variant_id"]),
            "sampling_repair_applied": bool(spec["sampling_repair_applied"]),
            "sampling_repair_reason": str(spec["sampling_repair_reason"]),
            "reset_stress_scheduled": True,
            "policy_rollout_scheduled": False,
        }
    )
    return row


def contract_violation_rows(repaired_specs: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in repaired_specs:
        try:
            assert_human_view_env_contract(build_env_config(dict(spec["env_config"])))
        except Exception as exc:  # noqa: BLE001 - preflight must preserve violations as rows.
            rows.append(
                {
                    "scenario_spec_id": str(spec["scenario_spec_id"]),
                    "scenario_family": str(spec["scenario_family"]),
                    "violation": str(exc),
                }
            )
    return rows


def run_reset_stress_cell(
    *,
    matrix_row: Mapping[str, Any],
    repaired_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    base = {
        "scenario_workload_id": str(matrix_row["scenario_workload_id"]),
        "scenario_spec_id": str(matrix_row["scenario_spec_id"]),
        "m1728_scenario_spec_id": str(matrix_row["m1728_scenario_spec_id"]),
        "scenario_family_id": str(matrix_row["scenario_family_id"]),
        "scenario_family": str(matrix_row["scenario_family"]),
        "scenario_role": str(matrix_row["scenario_role"]),
        "profile_name": str(matrix_row["profile_name"]),
        "eval_seed": int(eval_seed),
        "obstacle_timing_bucket": str(repaired_spec["obstacle_timing_bucket"]),
        "obstacle_lateral_bucket": str(repaired_spec["obstacle_lateral_bucket"]),
        "road_boundary_bucket": str(repaired_spec["road_boundary_bucket"]),
        "hidden_dynamics_bucket": str(repaired_spec["hidden_dynamics_bucket"]),
        "template_source_family": str(repaired_spec["template_source_family"]),
        "allowed_labels_metadata_only": str(repaired_spec["allowed_labels_metadata_only"]),
        "labels_enter_actor_input": bool(repaired_spec["labels_enter_actor_input"]),
        "require_aeb_infeasible": bool(dict(repaired_spec["env_config"]).get("obstacle", {}).get("require_aeb_infeasible", False)),
        "sampling_repair_source": str(matrix_row["sampling_repair_source"]),
        "sampling_repair_variant_id": str(matrix_row["sampling_repair_variant_id"]),
        "sampling_repair_applied": bool(matrix_row["sampling_repair_applied"]),
        "policy_rollout_started": False,
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
        "unsupported_faults_treated_as_covered": False,
    }
    try:
        env_config = env_config_for_executable_profile(
            executable_spec=repaired_spec,
            profile_config=dict(profile_config),
        )
        env = AutoDriftEnv(env_config)
        try:
            _obs, info = env.reset(seed=int(eval_seed))
        finally:
            env.close()
        base.update(
            {
                "reset_success": True,
                "error_type": "",
                "error_message": "",
                "sampled_obstacle_label": str(info.get("obstacle_label", "")),
                "initial_mu": float(info.get("initial_mu", float("nan"))),
                "speed_ref": float(info.get("speed_ref", float("nan"))),
                "obstacle_distance": float(info.get("obstacle_distance", float("nan"))),
                "obstacle_half_width": float(info.get("active_obstacle_half_width", float("nan"))),
                "obstacle_threshold_score": float(info.get("obstacle_threshold_score", float("nan"))),
                "obstacle_time_after_friction_step": float(info.get("obstacle_time_after_friction_step", float("nan"))),
            }
        )
    except Exception as exc:  # noqa: BLE001 - preflight must preserve sampling failures.
        base.update(
            {
                "reset_success": False,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "sampled_obstacle_label": "",
                "initial_mu": "",
                "speed_ref": "",
                "obstacle_distance": "",
                "obstacle_half_width": "",
                "obstacle_threshold_score": "",
                "obstacle_time_after_friction_step": "",
            }
        )
    return base


def _aggregate_count_rows(rows: list[Mapping[str, Any]], keys: tuple[str, ...], value_key: str) -> list[dict[str, Any]]:
    counts: dict[tuple[str, ...], int] = {}
    for row in rows:
        key = tuple(str(row.get(item, "")) for item in keys)
        counts[key] = counts.get(key, 0) + 1
    output: list[dict[str, Any]] = []
    for key in sorted(counts):
        item = {keys[index]: key[index] for index in range(len(keys))}
        item[value_key] = counts[key]
        output.append(item)
    return output


def _guardrail_flags() -> dict[str, bool]:
    return {
        "policy_rollout_started": False,
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
        "unsupported_faults_treated_as_covered": False,
    }


def run_sampling_repair_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    scenario_specs_path: Path | str = DEFAULT_SCENARIO_SPECS,
    matrix_path: Path | str = DEFAULT_SCENARIO_MATRIX,
    unsupported_features_path: Path | str = DEFAULT_UNSUPPORTED_FEATURES,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_M1731_EVAL_SEED_BASE,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    original_specs = load_scenario_specs(scenario_specs_path)
    repaired_specs = repaired_scenario_specs(scenario_specs_path)
    repaired_matrix = repaired_scenario_matrix_rows(repaired_specs=repaired_specs, matrix_path=matrix_path)
    repaired_by_id = {str(spec["scenario_spec_id"]): spec for spec in repaired_specs}
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    profile_config_by_name = {str(row["profile_name"]): read_json(row["config_path"]) for row in profile_rows}
    contract_violations = contract_violation_rows(repaired_specs)

    reset_rows: list[dict[str, Any]] = []
    for cell_index, matrix_row in enumerate(repaired_matrix):
        reset_rows.append(
            run_reset_stress_cell(
                matrix_row=matrix_row,
                repaired_spec=repaired_by_id[str(matrix_row["scenario_spec_id"])],
                profile_config=profile_config_by_name[str(matrix_row["profile_name"])],
                eval_seed=int(eval_seed_base) + int(cell_index),
            )
        )

    sampling_failure_rows = [dict(row) for row in reset_rows if not bool(row["reset_success"])]
    unsupported_rows = load_unsupported_feature_rows(unsupported_features_path)
    silent_unsupported_count = sum(
        str(row.get("silently_approximated", "")).strip().lower() in {"true", "1", "yes"}
        for row in unsupported_rows
    )
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    repaired_spec_count = len(repaired_specs)
    repaired_matrix_count = len(repaired_matrix)
    reset_success_count = len(reset_rows) - len(sampling_failure_rows)
    repaired_family_count = len({str(spec["scenario_family"]) for spec in repaired_specs})
    profile_count = len({str(row["profile_name"]) for row in repaired_matrix})
    result_passes = (
        repaired_spec_count == TARGET_SCENARIO_SPEC_COUNT
        and repaired_matrix_count == TARGET_EPISODE_COUNT
        and len(reset_rows) == TARGET_RESET_STRESS_ROW_COUNT
        and reset_success_count == TARGET_RESET_STRESS_ROW_COUNT
        and not sampling_failure_rows
        and not contract_violations
        and repaired_family_count == TARGET_SCENARIO_FAMILY_COUNT
        and profile_count == TARGET_PROFILE_COUNT
        and len(unsupported_rows) == TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT
        and silent_unsupported_count == 0
        and guardrail_violation_count == 0
        and not guardrail_flags["unsupported_faults_treated_as_covered"]
    )

    label_by_spec = _aggregate_count_rows(reset_rows, ("scenario_spec_id", "sampled_obstacle_label"), "reset_count")
    label_by_family = _aggregate_count_rows(reset_rows, ("scenario_family", "sampled_obstacle_label"), "reset_count")
    repair_delta_rows = sampling_repair_delta_rows(original_specs=original_specs, repaired_specs=repaired_specs)

    write_json(
        output / "repaired_scenario_specs.json",
        {
            "generated_at_utc": utc_timestamp(),
            "source_scenario_specs": str(scenario_specs_path),
            "repair_rule_source": REPAIR_RULE_SOURCE,
            "repaired_scenario_specs": repaired_specs,
        },
    )
    write_csv_rows(output / "repaired_scenario_specs.csv", [_repaired_spec_csv_row(row) for row in repaired_specs])
    write_csv_rows(output / "repaired_scenario_matrix.csv", repaired_matrix)
    write_csv_rows(output / "sampling_repair_delta.csv", repair_delta_rows)
    write_csv_rows(output / "reset_stress_rows.csv", reset_rows)
    write_csv_rows(output / "sampling_failure_rows.csv", sampling_failure_rows, fieldnames=list(reset_rows[0].keys()) if reset_rows else None)
    write_csv_rows(output / "label_distribution_by_spec.csv", label_by_spec)
    write_csv_rows(output / "label_distribution_by_family.csv", label_by_family)
    write_csv_rows(
        output / "contract_violations.csv",
        contract_violations,
        fieldnames=["scenario_spec_id", "scenario_family", "violation"],
    )
    write_csv_rows(output / "unsupported_scenario_features.csv", unsupported_rows)

    summary = {
        "result_class": (
            "task_quality_scenario_taxonomy_sampling_repair_preflight_pass"
            if result_passes
            else "task_quality_scenario_taxonomy_sampling_repair_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_scenario_specs": str(scenario_specs_path),
        "source_scenario_matrix": str(matrix_path),
        "repaired_scenario_spec_count": repaired_spec_count,
        "target_repaired_scenario_spec_count": TARGET_SCENARIO_SPEC_COUNT,
        "repaired_scenario_family_count": repaired_family_count,
        "target_repaired_scenario_family_count": TARGET_SCENARIO_FAMILY_COUNT,
        "repaired_matrix_cell_count": repaired_matrix_count,
        "target_repaired_matrix_cell_count": TARGET_EPISODE_COUNT,
        "profile_count": profile_count,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "reset_stress_row_count": len(reset_rows),
        "target_reset_stress_row_count": TARGET_RESET_STRESS_ROW_COUNT,
        "reset_success_count": reset_success_count,
        "sampling_failure_count": len(sampling_failure_rows),
        "contract_violation_count": len(contract_violations),
        "sampling_repair_delta_row_count": len(repair_delta_rows),
        "repaired_spec_count_by_variant": {
            row["sampling_repair_variant_id"]: sum(
                str(spec["sampling_repair_variant_id"]) == str(row["sampling_repair_variant_id"])
                for spec in repaired_specs
            )
            for row in repair_delta_rows
        },
        "label_distribution_by_family_rows": len(label_by_family),
        "label_distribution_by_spec_rows": len(label_by_spec),
        "unsupported_scenario_feature_count": len(unsupported_rows),
        "target_unsupported_scenario_feature_count": TARGET_UNSUPPORTED_SCENARIO_FEATURE_COUNT,
        "silent_unsupported_approximation_count": silent_unsupported_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": True,
        "policy_rollout_started": False,
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
        "unsupported_faults_treated_as_covered": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repaired_scenario_specs_json": str(output / "repaired_scenario_specs.json"),
            "repaired_scenario_specs": str(output / "repaired_scenario_specs.csv"),
            "repaired_scenario_matrix": str(output / "repaired_scenario_matrix.csv"),
            "sampling_repair_delta": str(output / "sampling_repair_delta.csv"),
            "reset_stress_rows": str(output / "reset_stress_rows.csv"),
            "sampling_failure_rows": str(output / "sampling_failure_rows.csv"),
            "label_distribution_by_spec": str(output / "label_distribution_by_spec.csv"),
            "label_distribution_by_family": str(output / "label_distribution_by_family.csv"),
            "contract_violations": str(output / "contract_violations.csv"),
            "unsupported_scenario_features": str(output / "unsupported_scenario_features.csv"),
        },
        "next_blocker": "m1735-paper-route-task-quality-scenario-taxonomy-sampling-repair-preflight-result-audit",
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reset-only sampling repair preflight.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scenario-specs", type=Path, default=DEFAULT_SCENARIO_SPECS)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_SCENARIO_MATRIX)
    parser.add_argument("--unsupported-features", type=Path, default=DEFAULT_UNSUPPORTED_FEATURES)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_M1731_EVAL_SEED_BASE)
    args = parser.parse_args()

    summary = run_sampling_repair_preflight(
        output_dir=args.output_dir,
        scenario_specs_path=args.scenario_specs,
        matrix_path=args.matrix,
        unsupported_features_path=args.unsupported_features,
        m1674_run_dir=args.m1674_run_dir,
        eval_seed_base=int(args.eval_seed_base),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"reset_stress_row_count={summary['reset_stress_row_count']}")
    print(f"reset_success_count={summary['reset_success_count']}")
    print(f"sampling_failure_count={summary['sampling_failure_count']}")


if __name__ == "__main__":
    main()
