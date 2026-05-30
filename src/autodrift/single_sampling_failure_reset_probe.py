"""Reset-only probe for a localized scenario-taxonomy sampling failure."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import env_config_for_executable_profile, read_csv_rows
from autodrift.controller_profile_runtime import wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.task_quality_scenario_taxonomy_execution import (
    load_scenario_specs,
    scenario_taxonomy_workload_rows,
)


DEFAULT_OUTPUT_DIR = Path("runs/m1758_single_sampling_failure_reset_only_probe")
DEFAULT_SCENARIO_SPECS = Path(
    "runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json"
)
DEFAULT_EXECUTABLE_SCENARIO_SPECS = Path(
    "runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json"
)
DEFAULT_WORKLOAD = Path(
    "runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv"
)
DEFAULT_FAILED_WORKLOAD_ID = "m1728-s4-02::L2_window_13_current_tiled"
DEFAULT_EXACT_SEED = 175761
DEFAULT_NEIGHBOR_RADIUS = 50

PROBE_CLASSIFICATIONS = (
    "exact_seed_infeasible",
    "seed_fragile_but_feasible",
    "spec_filter_infeasible",
    "probe_inconclusive",
)

GUARDRAIL_FIELDS = (
    "policy_rollout_started",
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
    "unsupported_faults_treated_as_covered",
)


def neighboring_seed_schedule(*, exact_seed: int, neighbor_radius: int) -> list[tuple[int, str, int]]:
    """Return exact seed first, then a symmetric bounded neighbor window."""

    schedule = [(int(exact_seed), "exact", 0)]
    radius = max(0, int(neighbor_radius))
    for offset in range(1, radius + 1):
        schedule.append((int(exact_seed) - offset, "neighbor", -offset))
        schedule.append((int(exact_seed) + offset, "neighbor", offset))
    return schedule


def classify_probe_rows(rows: list[Mapping[str, Any]], *, neighbor_radius: int) -> str:
    exact_rows = [row for row in rows if str(row.get("seed_role", "")) == "exact"]
    if len(exact_rows) != 1:
        return "probe_inconclusive"
    exact_success = bool(exact_rows[0].get("reset_success", False))
    if exact_success:
        return "probe_inconclusive"
    neighbor_rows = [row for row in rows if str(row.get("seed_role", "")) == "neighbor"]
    if any(bool(row.get("reset_success", False)) for row in neighbor_rows):
        return "seed_fragile_but_feasible"
    if int(neighbor_radius) <= 0:
        return "exact_seed_infeasible"
    if neighbor_rows and all(not bool(row.get("reset_success", False)) for row in neighbor_rows):
        return "spec_filter_infeasible"
    return "probe_inconclusive"


def _range_string(values: Any) -> str:
    if values is None:
        return ""
    if isinstance(values, (list, tuple)):
        return ",".join(str(value) for value in values)
    return str(values)


def _find_single(rows: list[Mapping[str, Any]], *, key: str, value: str) -> Mapping[str, Any]:
    matched = [row for row in rows if str(row.get(key, "")) == str(value)]
    if len(matched) != 1:
        raise ValueError(f"expected exactly one row for {key}={value}, found {len(matched)}")
    return matched[0]


def _base_probe_row(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    eval_seed: int,
    seed_role: str,
    seed_offset: int,
) -> dict[str, Any]:
    env_config = dict(executable_spec["env_config"])
    obstacle_config = dict(env_config.get("obstacle") or {})
    return {
        "workload_id": str(workload_row["workload_id"]),
        "scenario_workload_id": str(workload_row.get("scenario_workload_id", "")),
        "scenario_spec_id": str(workload_row.get("scenario_spec_id", "")),
        "m1728_scenario_spec_id": str(workload_row.get("m1728_scenario_spec_id", "")),
        "scenario_family_id": str(workload_row.get("scenario_family_id", "")),
        "scenario_family": str(workload_row.get("scenario_family", "")),
        "evaluation_role": str(workload_row.get("evaluation_role", "")),
        "primary_metric_family": str(workload_row.get("primary_metric_family", "")),
        "profile_name": str(workload_row.get("profile_name", "")),
        "eval_seed": int(eval_seed),
        "seed_role": str(seed_role),
        "seed_offset": int(seed_offset),
        "obstacle_timing_bucket": str(workload_row.get("obstacle_timing_bucket", "")),
        "obstacle_lateral_bucket": str(workload_row.get("obstacle_lateral_bucket", "")),
        "road_boundary_bucket": str(workload_row.get("road_boundary_bucket", "")),
        "hidden_dynamics_bucket": str(workload_row.get("hidden_dynamics_bucket", "")),
        "template_source_family": str(workload_row.get("template_source_family", "")),
        "sampling_repair_source": str(workload_row.get("sampling_repair_source", "")),
        "sampling_repair_variant_id": str(workload_row.get("sampling_repair_variant_id", "")),
        "sampling_repair_applied": bool(workload_row.get("sampling_repair_applied", False)),
        "allowed_labels_config": "|".join(str(label) for label in obstacle_config.get("allowed_labels", [])),
        "require_aeb_infeasible": bool(obstacle_config.get("require_aeb_infeasible", False)),
        "max_sample_attempts": int(obstacle_config.get("max_sample_attempts", 0)),
        "distance_range": _range_string(obstacle_config.get("distance_range")),
        "half_width_range": _range_string(obstacle_config.get("half_width_range")),
        "max_threshold_score": obstacle_config.get("max_threshold_score", ""),
        "min_time_after_friction_step": float(obstacle_config.get("min_time_after_friction_step", 0.0)),
        "reset_success": False,
        "error_type": "",
        "error_message": "",
        "sampled_obstacle_label": "",
        "initial_mu": "",
        "mu": "",
        "speed_ref": "",
        "beta_target": "",
        "obstacle_distance": "",
        "obstacle_lateral_offset": "",
        "obstacle_required_lateral_offset": "",
        "active_obstacle_half_width": "",
        "obstacle_threshold_score": "",
        "obstacle_time_after_friction_step": "",
        "friction_step_at": "",
        "track_width": "",
        **{field: False for field in GUARDRAIL_FIELDS},
    }


def probe_reset_seed(
    *,
    workload_row: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    eval_seed: int,
    seed_role: str,
    seed_offset: int,
) -> dict[str, Any]:
    row = _base_probe_row(
        workload_row=workload_row,
        executable_spec=executable_spec,
        eval_seed=eval_seed,
        seed_role=seed_role,
        seed_offset=seed_offset,
    )
    env = None
    try:
        env_config = env_config_for_executable_profile(
            executable_spec=executable_spec,
            profile_config=profile_config,
        )
        env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), dict(profile_config))
        _obs, info = env.reset(seed=int(eval_seed))
        row.update(
            {
                "reset_success": True,
                "sampled_obstacle_label": str(info.get("obstacle_label", "")),
                "initial_mu": float(info.get("initial_mu", float("nan"))),
                "mu": float(info.get("mu", float("nan"))),
                "speed_ref": float(info.get("speed_ref", float("nan"))),
                "beta_target": float(info.get("beta_target", float("nan"))),
                "obstacle_distance": float(info.get("obstacle_distance", float("nan"))),
                "obstacle_lateral_offset": float(info.get("obstacle_lateral_offset", float("nan"))),
                "obstacle_required_lateral_offset": float(
                    info.get("obstacle_required_lateral_offset", float("nan"))
                ),
                "active_obstacle_half_width": float(info.get("active_obstacle_half_width", float("nan"))),
                "obstacle_threshold_score": float(info.get("obstacle_threshold_score", float("nan"))),
                "obstacle_time_after_friction_step": float(
                    info.get("obstacle_time_after_friction_step", float("nan"))
                ),
                "friction_step_at": info.get("friction_step_at", ""),
                "track_width": float(info.get("track_width", float("nan"))),
            }
        )
    except Exception as exc:  # noqa: BLE001 - probe preserves reset failures as data.
        row.update(
            {
                "reset_success": False,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        )
    finally:
        if env is not None:
            env.close()
    return row


def run_single_sampling_failure_reset_probe(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    scenario_specs_path: Path | str = DEFAULT_SCENARIO_SPECS,
    executable_scenario_specs_path: Path | str = DEFAULT_EXECUTABLE_SCENARIO_SPECS,
    workload_path: Path | str = DEFAULT_WORKLOAD,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    workload_id: str = DEFAULT_FAILED_WORKLOAD_ID,
    exact_seed: int = DEFAULT_EXACT_SEED,
    neighbor_radius: int = DEFAULT_NEIGHBOR_RADIUS,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

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
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    profile_row = _find_single(profile_rows, key="profile_name", value=str(workload_row["profile_name"]))
    profile_config = read_json(profile_row["config_path"])

    probe_rows = [
        probe_reset_seed(
            workload_row=workload_row,
            executable_spec=executable_spec,
            profile_config=profile_config,
            eval_seed=seed,
            seed_role=seed_role,
            seed_offset=seed_offset,
        )
        for seed, seed_role, seed_offset in neighboring_seed_schedule(
            exact_seed=exact_seed,
            neighbor_radius=neighbor_radius,
        )
    ]
    failure_rows = [row for row in probe_rows if not bool(row["reset_success"])]
    classification = classify_probe_rows(probe_rows, neighbor_radius=neighbor_radius)
    exact_rows = [row for row in probe_rows if str(row["seed_role"]) == "exact"]
    neighbor_rows = [row for row in probe_rows if str(row["seed_role"]) == "neighbor"]
    success_rows = [row for row in probe_rows if bool(row["reset_success"])]

    write_csv_rows(output / "probe_rows.csv", probe_rows)
    write_csv_rows(output / "failed_probe_rows.csv", failure_rows, fieldnames=list(probe_rows[0].keys()))

    sampled_label_counts: dict[str, int] = {}
    for row in success_rows:
        label = str(row.get("sampled_obstacle_label", ""))
        sampled_label_counts[label] = sampled_label_counts.get(label, 0) + 1

    summary = {
        "generated_at_utc": utc_timestamp(),
        "result_class": classification,
        "workload_id": str(workload_row["workload_id"]),
        "scenario_spec_id": str(workload_row["scenario_spec_id"]),
        "profile_name": str(workload_row["profile_name"]),
        "exact_seed": int(exact_seed),
        "neighbor_radius": int(neighbor_radius),
        "probe_seed_count": len(probe_rows),
        "success_count": len(success_rows),
        "failure_count": len(failure_rows),
        "exact_reset_success": bool(exact_rows and exact_rows[0]["reset_success"]),
        "neighbor_success_count": sum(1 for row in neighbor_rows if bool(row["reset_success"])),
        "neighbor_failure_count": sum(1 for row in neighbor_rows if not bool(row["reset_success"])),
        "sampled_label_counts": sampled_label_counts,
        "probe_rows_csv": str(output / "probe_rows.csv"),
        "failed_probe_rows_csv": str(output / "failed_probe_rows.csv"),
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
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scenario-specs", type=Path, default=DEFAULT_SCENARIO_SPECS)
    parser.add_argument("--executable-scenario-specs", type=Path, default=DEFAULT_EXECUTABLE_SCENARIO_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_WORKLOAD)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--workload-id", default=DEFAULT_FAILED_WORKLOAD_ID)
    parser.add_argument("--exact-seed", type=int, default=DEFAULT_EXACT_SEED)
    parser.add_argument("--neighbor-radius", type=int, default=DEFAULT_NEIGHBOR_RADIUS)
    args = parser.parse_args()
    summary = run_single_sampling_failure_reset_probe(
        output_dir=args.output_dir,
        scenario_specs_path=args.scenario_specs,
        executable_scenario_specs_path=args.executable_scenario_specs,
        workload_path=args.workload,
        m1674_run_dir=args.m1674_run_dir,
        workload_id=args.workload_id,
        exact_seed=args.exact_seed,
        neighbor_radius=args.neighbor_radius,
    )
    print(f"result_class={summary['result_class']}")
    print(f"probe_seed_count={summary['probe_seed_count']}")
    print(f"success_count={summary['success_count']}")
    print(f"failure_count={summary['failure_count']}")


if __name__ == "__main__":
    main()
