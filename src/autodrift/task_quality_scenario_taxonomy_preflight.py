"""No-rollout preflight for the paper-route task-quality scenario taxonomy."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec


DEFAULT_OUTPUT_DIR = Path("runs/m1728_task_quality_scenario_taxonomy_preflight")
EXPECTED_SCENARIO_FAMILY_COUNT = 6
EXPECTED_SCENARIO_SPECS_PER_FAMILY = 12
EXPECTED_SCENARIO_SPEC_COUNT = EXPECTED_SCENARIO_FAMILY_COUNT * EXPECTED_SCENARIO_SPECS_PER_FAMILY
EXPECTED_PROFILE_COUNT = 12
EXPECTED_SCENARIO_MATRIX_CELL_COUNT = EXPECTED_SCENARIO_SPEC_COUNT * EXPECTED_PROFILE_COUNT
SCENARIO_FAMILIES = (
    {
        "scenario_family_id": "S1",
        "scenario_family": "ordinary_stable_avoidance",
        "scenario_role": "normal avoidable obstacle baseline",
        "template_source_family": "t4_staged_warmup_capability",
        "allowed_labels": ("aeb_feasible", "aes_feasible"),
        "obstacle_timing_buckets": ("medium", "medium_late", "late"),
        "obstacle_lateral_buckets": ("center", "mild_offset", "wide_offset", "mixed"),
        "road_boundary_buckets": ("nominal", "nominal", "moderate", "moderate"),
        "hidden_dynamics_buckets": ("nominal", "mild_randomization", "friction_step"),
    },
    {
        "scenario_family_id": "S2",
        "scenario_family": "aeb_infeasible_stable_aes",
        "scenario_role": "braking infeasible but stable steering avoidance expected",
        "template_source_family": "t4_capability_step_temporal",
        "allowed_labels": ("aes_feasible",),
        "require_aeb_infeasible": True,
        "obstacle_timing_buckets": ("late", "close", "close"),
        "obstacle_lateral_buckets": ("mild_offset", "wide_offset", "mixed", "center"),
        "road_boundary_buckets": ("moderate", "moderate", "wide", "wide"),
        "hidden_dynamics_buckets": ("nominal", "friction_step", "brake_variation"),
    },
    {
        "scenario_family_id": "S3",
        "scenario_family": "drift_required_avoidance",
        "scenario_role": "handling-limit avoidance where high yaw may be useful",
        "template_source_family": "t5_high_speed_close_obstacle",
        "allowed_labels": ("drift_required",),
        "require_aeb_infeasible": True,
        "obstacle_timing_buckets": ("close", "very_close", "late"),
        "obstacle_lateral_buckets": ("center", "mild_offset", "wide_offset", "mixed"),
        "road_boundary_buckets": ("wide", "moderate", "wide", "moderate"),
        "hidden_dynamics_buckets": ("low_mu", "friction_step", "tire_stiffness"),
    },
    {
        "scenario_family_id": "S4",
        "scenario_family": "unavoidable_mitigation",
        "scenario_role": "unavoidable or near-unavoidable obstacle mitigation",
        "template_source_family": "t5_high_speed_close_obstacle",
        "allowed_labels": ("unavoidable",),
        "require_aeb_infeasible": True,
        "obstacle_timing_buckets": ("very_close", "very_close", "close"),
        "obstacle_lateral_buckets": ("center", "center", "mild_offset", "mixed"),
        "road_boundary_buckets": ("moderate", "wide", "moderate", "wide"),
        "hidden_dynamics_buckets": ("low_mu", "brake_variation", "actuator_delay"),
    },
    {
        "scenario_family_id": "S5",
        "scenario_family": "off_track_boundary_stress",
        "scenario_role": "road-boundary stress without making every hard case off-track dominated",
        "template_source_family": "t5_boundary_axis_retarget",
        "allowed_labels": ("aes_feasible", "drift_required"),
        "require_aeb_infeasible": True,
        "obstacle_timing_buckets": ("late", "close", "medium"),
        "obstacle_lateral_buckets": ("wide_offset", "mixed", "mild_offset", "center"),
        "road_boundary_buckets": ("narrow", "moderate", "narrow", "moderate"),
        "hidden_dynamics_buckets": ("nominal", "friction_step", "tire_stiffness"),
    },
    {
        "scenario_family_id": "S6",
        "scenario_family": "hidden_dynamics_stress",
        "scenario_role": "hidden dynamics and supported fault-like stress",
        "template_source_family": "t4_actuator_delay_response",
        "allowed_labels": ("aes_feasible", "drift_required", "unavoidable"),
        "require_aeb_infeasible": True,
        "obstacle_timing_buckets": ("medium", "late", "close"),
        "obstacle_lateral_buckets": ("mixed", "center", "mild_offset", "wide_offset"),
        "road_boundary_buckets": ("moderate", "wide", "narrow", "moderate"),
        "hidden_dynamics_buckets": ("actuator_delay", "brake_drive_variation", "mass_cg_shift"),
    },
)
UNSUPPORTED_SCENARIO_FEATURES = (
    {
        "feature": "single_wheel_blowout_or_puncture",
        "planned_family": "hidden_dynamics_stress",
        "support_status": "unsupported_current_single_track_model",
        "reason": "current dynamics model has front/rear lumped tire forces, not per-wheel tire state",
    },
    {
        "feature": "wheel_specific_grip_loss",
        "planned_family": "hidden_dynamics_stress",
        "support_status": "unsupported_current_single_track_model",
        "reason": "current env randomizes vehicle-level friction, not wheel-specific friction patches",
    },
    {
        "feature": "half_shaft_or_single_side_drive_torque_loss",
        "planned_family": "hidden_dynamics_stress",
        "support_status": "unsupported_current_single_track_model",
        "reason": "current RWD model exposes a single longitudinal drive/brake force state",
    },
    {
        "feature": "brake_side_imbalance",
        "planned_family": "hidden_dynamics_stress",
        "support_status": "unsupported_current_single_track_model",
        "reason": "current brake scale is vehicle-level, not side-specific",
    },
    {
        "feature": "steering_deadzone_or_partial_actuator_fault",
        "planned_family": "hidden_dynamics_stress",
        "support_status": "unsupported_current_actuator_model",
        "reason": "current actuator stress supports delay scaling, not deadzone or partial lock",
    },
)


def _replace_nested(data: dict[str, Any], key: str, updates: Mapping[str, Any]) -> None:
    nested = deepcopy(dict(data.get(key) or {}))
    nested.update(dict(updates))
    data[key] = nested


def _geometry_overrides(family: Mapping[str, Any], spec_index: int) -> dict[str, Any]:
    timing = str(family["obstacle_timing_buckets"][spec_index % len(family["obstacle_timing_buckets"])])
    lateral = str(family["obstacle_lateral_buckets"][spec_index % len(family["obstacle_lateral_buckets"])])
    boundary = str(family["road_boundary_buckets"][spec_index % len(family["road_boundary_buckets"])])
    distance_by_timing = {
        "medium": (18.0, 42.0),
        "medium_late": (16.0, 36.0),
        "late": (13.0, 30.0),
        "close": (10.0, 24.0),
        "very_close": (8.0, 18.0),
    }
    width_by_lateral = {
        "center": (0.55, 1.10),
        "mild_offset": (0.60, 1.20),
        "wide_offset": (0.70, 1.35),
        "mixed": (0.55, 1.35),
    }
    track_width_by_boundary = {
        "narrow": 4.25,
        "moderate": 5.25,
        "nominal": 6.00,
        "wide": 8.00,
    }
    finish_distance_by_boundary = {
        "narrow": 0.75,
        "moderate": 1.0,
        "nominal": 1.5,
        "wide": 2.0,
    }
    return {
        "obstacle_timing_bucket": timing,
        "obstacle_lateral_bucket": lateral,
        "road_boundary_bucket": boundary,
        "distance_range": distance_by_timing[timing],
        "half_width_range": width_by_lateral[lateral],
        "track_width": track_width_by_boundary[boundary],
        "finish_pass_distance": finish_distance_by_boundary[boundary],
    }


def _dynamics_overrides(family: Mapping[str, Any], spec_index: int) -> dict[str, Any]:
    bucket = str(family["hidden_dynamics_buckets"][(spec_index // 4) % len(family["hidden_dynamics_buckets"])])
    randomization: dict[str, tuple[float, float]] = {}
    friction_step: dict[str, Any] = {}
    speed_range: tuple[float, float] | None = None
    if bucket == "nominal":
        randomization.update(
            {
                "mu_range": (0.55, 1.10),
                "brake_scale_range": (0.85, 1.15),
                "drive_scale_range": (0.85, 1.15),
                "tire_stiffness_scale_range": (0.85, 1.15),
                "actuator_tau_scale_range": (0.85, 1.30),
            }
        )
    elif bucket == "mild_randomization":
        randomization.update({"mu_range": (0.40, 1.10), "actuator_tau_scale_range": (0.85, 1.75)})
    elif bucket == "friction_step":
        randomization.update({"mu_range": (0.35, 1.10)})
        friction_step.update({"enabled": True, "step_range": (18, 34), "mu_range": (0.25, 1.05), "resample_speed_ref": False})
    elif bucket == "brake_variation":
        randomization.update({"brake_scale_range": (0.45, 1.25), "mu_range": (0.35, 1.05)})
    elif bucket == "brake_drive_variation":
        randomization.update({"brake_scale_range": (0.45, 1.25), "drive_scale_range": (0.45, 1.25), "mu_range": (0.35, 1.05)})
    elif bucket == "tire_stiffness":
        randomization.update({"tire_stiffness_scale_range": (0.45, 1.50), "mu_range": (0.30, 1.05)})
    elif bucket == "low_mu":
        randomization.update({"mu_range": (0.25, 0.75), "tire_stiffness_scale_range": (0.55, 1.25)})
        speed_range = (10.0, 17.0)
    elif bucket == "actuator_delay":
        randomization.update({"actuator_tau_scale_range": (1.50, 4.20), "mu_range": (0.40, 1.05)})
    elif bucket == "mass_cg_shift":
        randomization.update(
            {
                "mass_scale_range": (0.85, 1.25),
                "inertia_scale_range": (0.85, 1.30),
                "cg_shift_range": (-0.14, 0.14),
                "mu_range": (0.35, 1.05),
            }
        )
    else:
        raise ValueError(f"unknown hidden dynamics bucket: {bucket}")
    return {
        "hidden_dynamics_bucket": bucket,
        "randomization": randomization,
        "friction_step": friction_step,
        "speed_range": speed_range,
    }


def scenario_taxonomy_payload() -> dict[str, Any]:
    return {
        "taxonomy_name": "paper_route_task_quality_scenario_taxonomy",
        "scenario_families": [
            {
                "scenario_family_id": str(family["scenario_family_id"]),
                "scenario_family": str(family["scenario_family"]),
                "scenario_role": str(family["scenario_role"]),
                "planned_specs": EXPECTED_SCENARIO_SPECS_PER_FAMILY,
                "template_source_family": str(family["template_source_family"]),
                "allowed_labels_metadata_only": list(family["allowed_labels"]),
            }
            for family in SCENARIO_FAMILIES
        ],
        "claim_scope": "no-rollout taxonomy metadata only",
        "labels_enter_actor_input": False,
    }


def _env_config_for_scenario(family: Mapping[str, Any], spec_index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    reveal_step = 24 + 4 * (spec_index % 4)
    env = env_config_to_dict(
        env_config_for_hook_spec(
            source_family=str(family["template_source_family"]),
            capability_pair="taxonomy_pair",
            reveal_step=reveal_step,
        )
    )
    geometry = _geometry_overrides(family, spec_index)
    dynamics = _dynamics_overrides(family, spec_index)
    env["track_width"] = float(geometry["track_width"])
    if dynamics["speed_range"] is not None:
        env["speed_range"] = dynamics["speed_range"]
    obstacle_updates = {
        "allowed_labels": tuple(str(label) for label in family["allowed_labels"]),
        "distance_range": geometry["distance_range"],
        "half_width_range": geometry["half_width_range"],
        "finish_pass_distance": geometry["finish_pass_distance"],
        "require_aeb_infeasible": bool(family.get("require_aeb_infeasible", False)),
        "max_sample_attempts": 240,
    }
    _replace_nested(env, "obstacle", obstacle_updates)
    if dynamics["randomization"]:
        _replace_nested(env, "randomization", dynamics["randomization"])
    if dynamics["friction_step"]:
        _replace_nested(env, "friction_step", dynamics["friction_step"])
    env["history_length"] = 1
    env["action_history_mode"] = "full"
    env["include_privileged_params"] = False
    env["obstacle_relative_velocity_mode"] = "zero"
    env["wheel_observation_mode"] = "none"
    metadata = {
        "reveal_step": reveal_step,
        "obstacle_timing_bucket": geometry["obstacle_timing_bucket"],
        "obstacle_lateral_bucket": geometry["obstacle_lateral_bucket"],
        "road_boundary_bucket": geometry["road_boundary_bucket"],
        "hidden_dynamics_bucket": dynamics["hidden_dynamics_bucket"],
    }
    return env, metadata


def materialize_scenario_specs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for family_index, family in enumerate(SCENARIO_FAMILIES, start=1):
        for spec_index in range(EXPECTED_SCENARIO_SPECS_PER_FAMILY):
            env_config, metadata = _env_config_for_scenario(family, spec_index)
            scenario_spec_id = f"m1728-{family['scenario_family_id'].lower()}-{spec_index:02d}"
            violation_messages: list[str] = []
            try:
                assert_human_view_env_contract(build_env_config(env_config))
            except Exception as exc:  # noqa: BLE001 - preflight must record every contract failure.
                violation_messages.append(str(exc))
            row = {
                "scenario_spec_id": scenario_spec_id,
                "scenario_family_id": str(family["scenario_family_id"]),
                "scenario_family": str(family["scenario_family"]),
                "scenario_role": str(family["scenario_role"]),
                "geometry_seed": 172800 + family_index * 100 + spec_index,
                "dynamics_seed": 172800 + family_index * 1000 + spec_index,
                "template_source_family": str(family["template_source_family"]),
                "allowed_labels_metadata_only": ";".join(str(label) for label in family["allowed_labels"]),
                "labels_enter_actor_input": False,
                "obstacle_timing_bucket": metadata["obstacle_timing_bucket"],
                "obstacle_lateral_bucket": metadata["obstacle_lateral_bucket"],
                "road_boundary_bucket": metadata["road_boundary_bucket"],
                "hidden_dynamics_bucket": metadata["hidden_dynamics_bucket"],
                "reveal_step": int(metadata["reveal_step"]),
                "contract_violation_count": len(violation_messages),
                "environment_rollout_scheduled": False,
                "profile_specific_tuning": False,
                "env_config": env_config,
            }
            rows.append(row)
            for message in violation_messages:
                violations.append(
                    {
                        "scenario_spec_id": scenario_spec_id,
                        "scenario_family": str(family["scenario_family"]),
                        "violation": message,
                    }
                )
    return rows, violations


def scenario_spec_csv_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "scenario_spec_id": row["scenario_spec_id"],
        "scenario_family_id": row["scenario_family_id"],
        "scenario_family": row["scenario_family"],
        "scenario_role": row["scenario_role"],
        "geometry_seed": row["geometry_seed"],
        "dynamics_seed": row["dynamics_seed"],
        "template_source_family": row["template_source_family"],
        "allowed_labels_metadata_only": row["allowed_labels_metadata_only"],
        "labels_enter_actor_input": row["labels_enter_actor_input"],
        "obstacle_timing_bucket": row["obstacle_timing_bucket"],
        "obstacle_lateral_bucket": row["obstacle_lateral_bucket"],
        "road_boundary_bucket": row["road_boundary_bucket"],
        "hidden_dynamics_bucket": row["hidden_dynamics_bucket"],
        "reveal_step": row["reveal_step"],
        "contract_violation_count": row["contract_violation_count"],
        "environment_rollout_scheduled": False,
        "profile_specific_tuning": False,
    }


def scenario_matrix_rows(
    scenario_specs: list[Mapping[str, Any]],
    *,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
) -> list[dict[str, Any]]:
    profiles = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in scenario_specs:
        for profile in profiles:
            rows.append(
                {
                    "scenario_workload_id": f"{spec['scenario_spec_id']}::{profile['profile_name']}",
                    "scenario_spec_id": spec["scenario_spec_id"],
                    "scenario_family_id": spec["scenario_family_id"],
                    "scenario_family": spec["scenario_family"],
                    "scenario_role": spec["scenario_role"],
                    "profile_name": profile["profile_name"],
                    "profile_config_path": profile["config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "config_exists": profile["config_exists"],
                    "checkpoint_exists": profile["checkpoint_exists"],
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                }
            )
    return rows


def unsupported_scenario_feature_rows() -> list[dict[str, Any]]:
    return [
        {
            **dict(row),
            "silently_approximated": False,
            "covered_by_current_preflight": False,
        }
        for row in UNSUPPORTED_SCENARIO_FEATURES
    ]


def _counts_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[key]) for row in rows).items()))


def run_scenario_taxonomy_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    scenario_specs, contract_violations = materialize_scenario_specs()
    matrix_rows = scenario_matrix_rows(scenario_specs, m1674_run_dir=m1674_run_dir)
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    unsupported_rows = unsupported_scenario_feature_rows()

    family_counts = _counts_by_key(scenario_specs, "scenario_family")
    profiles_per_spec = _counts_by_key(matrix_rows, "scenario_spec_id")
    missing_profile_count = sum(1 for count in profiles_per_spec.values() if count != EXPECTED_PROFILE_COUNT)
    missing_config_count = sum(row.get("config_exists") != True for row in matrix_rows)
    missing_checkpoint_count = sum(row.get("checkpoint_exists") != True for row in matrix_rows)
    silent_approximation_count = sum(bool(row["silently_approximated"]) for row in unsupported_rows)
    guardrail_flags = {
        "environment_rollout_started": False,
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
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        len(family_counts) == EXPECTED_SCENARIO_FAMILY_COUNT
        and len(scenario_specs) == EXPECTED_SCENARIO_SPEC_COUNT
        and all(count == EXPECTED_SCENARIO_SPECS_PER_FAMILY for count in family_counts.values())
        and len(matrix_rows) == EXPECTED_SCENARIO_MATRIX_CELL_COUNT
        and len({row["profile_name"] for row in matrix_rows}) == EXPECTED_PROFILE_COUNT
        and missing_profile_count == 0
        and missing_config_count == 0
        and missing_checkpoint_count == 0
        and len(contract_violations) == 0
        and silent_approximation_count == 0
        and guardrail_violation_count == 0
    )
    generated_at = utc_timestamp()
    artifacts = {
        "summary": str(output / "summary.json"),
        "scenario_taxonomy": str(output / "scenario_taxonomy.json"),
        "scenario_specs": str(output / "scenario_specs.csv"),
        "scenario_specs_json": str(output / "scenario_specs.json"),
        "scenario_matrix": str(output / "scenario_matrix.csv"),
        "profile_artifacts": str(output / "profile_artifacts.csv"),
        "contract_violations": str(output / "contract_violations.csv"),
        "unsupported_scenario_features": str(output / "unsupported_scenario_features.csv"),
    }
    summary = {
        "result_class": (
            "task_quality_scenario_taxonomy_preflight_pass"
            if passes
            else "task_quality_scenario_taxonomy_preflight_fail"
        ),
        "generated_at_utc": generated_at,
        "output_dir": str(output),
        "scenario_family_count": len(family_counts),
        "target_scenario_family_count": EXPECTED_SCENARIO_FAMILY_COUNT,
        "scenario_spec_count": len(scenario_specs),
        "target_scenario_spec_count": EXPECTED_SCENARIO_SPEC_COUNT,
        "scenario_specs_per_family": family_counts,
        "target_scenario_specs_per_family": EXPECTED_SCENARIO_SPECS_PER_FAMILY,
        "scenario_matrix_cell_count": len(matrix_rows),
        "target_scenario_matrix_cell_count": EXPECTED_SCENARIO_MATRIX_CELL_COUNT,
        "profile_count": len({row["profile_name"] for row in matrix_rows}),
        "target_profile_count": EXPECTED_PROFILE_COUNT,
        "profile_artifact_count": len(profile_rows),
        "missing_profile_count": missing_profile_count,
        "missing_config_count": missing_config_count,
        "missing_checkpoint_count": missing_checkpoint_count,
        "contract_violation_count": len(contract_violations),
        "unsupported_scenario_feature_count": len(unsupported_rows),
        "silent_unsupported_approximation_count": silent_approximation_count,
        "hidden_dynamics_bucket_counts": _counts_by_key(scenario_specs, "hidden_dynamics_bucket"),
        "road_boundary_bucket_counts": _counts_by_key(scenario_specs, "road_boundary_bucket"),
        "obstacle_timing_bucket_counts": _counts_by_key(scenario_specs, "obstacle_timing_bucket"),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": False,
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
        "passes_public_preflight_gates": bool(passes),
        "artifacts": artifacts,
        "next_blocker": "m1729-paper-route-task-quality-scenario-taxonomy-preflight-result-audit",
    }
    write_json(output / "scenario_taxonomy.json", scenario_taxonomy_payload())
    write_json(
        output / "scenario_specs.json",
        {
            "generated_at_utc": generated_at,
            "scenario_specs": scenario_specs,
        },
    )
    write_csv_rows(output / "scenario_specs.csv", [scenario_spec_csv_row(row) for row in scenario_specs])
    write_csv_rows(output / "scenario_matrix.csv", matrix_rows)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows)
    write_csv_rows(
        output / "contract_violations.csv",
        contract_violations,
        fieldnames=["scenario_spec_id", "scenario_family", "violation"],
    )
    write_csv_rows(output / "unsupported_scenario_features.csv", unsupported_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-rollout task-quality scenario taxonomy.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    args = parser.parse_args()

    summary = run_scenario_taxonomy_preflight(output_dir=args.output_dir, m1674_run_dir=args.m1674_run_dir)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"scenario_family_count={summary['scenario_family_count']}")
    print(f"scenario_spec_count={summary['scenario_spec_count']}")
    print(f"scenario_matrix_cell_count={summary['scenario_matrix_cell_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")


if __name__ == "__main__":
    main()
