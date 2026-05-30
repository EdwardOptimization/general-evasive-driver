"""Reset-only feasibility preflight for the metric-specific bounded panel."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import env_config_for_executable_profile, read_csv_rows
from autodrift.env import AutoDriftEnv
from autodrift.metric_specific_bounded_panel_materialization_preflight import DEFAULT_OUTPUT_DIR as DEFAULT_M1771_OUTPUT_DIR


DEFAULT_BOUNDED_PANEL_SPECS = DEFAULT_M1771_OUTPUT_DIR / "bounded_panel_specs.json"
DEFAULT_BOUNDED_PANEL_MATRIX = DEFAULT_M1771_OUTPUT_DIR / "bounded_panel_matrix.csv"
DEFAULT_OUTPUT_DIR = Path("runs/m1773_metric_specific_bounded_panel_reset_feasibility_preflight")
DEFAULT_EVAL_SEED_BASE = 177300
TARGET_PANEL_CELL_COUNT = 288
TARGET_PROFILE_COUNT = 12
TARGET_ROLE_PANEL_COUNT = 4
FORBIDDEN_GUARDRAILS = (
    "policy_action_executed",
    "measured_rollout_started",
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
)


def load_bounded_panel_specs(path: Path | str = DEFAULT_BOUNDED_PANEL_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return [dict(row) for row in payload["bounded_panel_specs"]]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def reset_bounded_panel_cell(
    *,
    matrix_row: Mapping[str, Any],
    panel_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    base = {
        "bounded_panel_workload_id": str(matrix_row["bounded_panel_workload_id"]),
        "scenario_workload_id": str(matrix_row["scenario_workload_id"]),
        "scenario_spec_id": str(matrix_row["scenario_spec_id"]),
        "bounded_panel_spec_id": str(matrix_row["bounded_panel_spec_id"]),
        "source_scenario_spec_id": str(matrix_row["source_scenario_spec_id"]),
        "m1728_scenario_spec_id": str(matrix_row["m1728_scenario_spec_id"]),
        "role_panel_id": str(matrix_row["role_panel_id"]),
        "role_panel_label": str(matrix_row["role_panel_label"]),
        "scenario_family_id": str(matrix_row["scenario_family_id"]),
        "scenario_family": str(matrix_row["scenario_family"]),
        "scenario_role": str(matrix_row["scenario_role"]),
        "profile_name": str(matrix_row["profile_name"]),
        "eval_seed": int(eval_seed),
        "evaluation_role": str(matrix_row["evaluation_role"]),
        "primary_metric_family": str(matrix_row["primary_metric_family"]),
        "panel_evaluation_role": str(matrix_row["panel_evaluation_role"]),
        "panel_primary_metric_family": str(matrix_row["panel_primary_metric_family"]),
        "allowed_labels_metadata_only": str(matrix_row["allowed_labels_metadata_only"]),
        "labels_enter_actor_input": _bool(matrix_row.get("labels_enter_actor_input", False)),
        "hidden_dynamics_bucket": str(matrix_row["hidden_dynamics_bucket"]),
        "road_boundary_bucket": str(matrix_row["road_boundary_bucket"]),
        "obstacle_timing_bucket": str(matrix_row["obstacle_timing_bucket"]),
        "obstacle_lateral_bucket": str(matrix_row["obstacle_lateral_bucket"]),
        "sampling_repair_source": str(matrix_row["sampling_repair_source"]),
        "sampling_repair_variant_id": str(matrix_row["sampling_repair_variant_id"]),
        "sampling_repair_applied": _bool(matrix_row.get("sampling_repair_applied", False)),
        "environment_reset_started": True,
        "policy_action_executed": False,
        "measured_rollout_started": False,
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
    try:
        env_config = env_config_for_executable_profile(
            executable_spec=panel_spec,
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
    except Exception as exc:  # noqa: BLE001 - preflight must preserve every sampling failure.
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


def _count_by_key(rows: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def run_metric_specific_bounded_panel_reset_feasibility_preflight(
    *,
    bounded_panel_specs_path: Path | str = DEFAULT_BOUNDED_PANEL_SPECS,
    bounded_panel_matrix_path: Path | str = DEFAULT_BOUNDED_PANEL_MATRIX,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    panel_specs = load_bounded_panel_specs(bounded_panel_specs_path)
    matrix_rows = [dict(row) for row in read_csv_rows(bounded_panel_matrix_path)]
    spec_by_id = {str(spec["bounded_panel_spec_id"]): spec for spec in panel_specs}
    profile_config_by_name = {
        str(row["profile_name"]): read_json(row["profile_config_path"])
        for row in matrix_rows
    }

    reset_rows: list[dict[str, Any]] = []
    for cell_index, matrix_row in enumerate(matrix_rows):
        reset_rows.append(
            reset_bounded_panel_cell(
                matrix_row=matrix_row,
                panel_spec=spec_by_id[str(matrix_row["bounded_panel_spec_id"])],
                profile_config=profile_config_by_name[str(matrix_row["profile_name"])],
                eval_seed=int(eval_seed_base) + int(cell_index),
            )
        )

    sampling_failure_rows = [dict(row) for row in reset_rows if not bool(row["reset_success"])]
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    reset_success_count = len(reset_rows) - len(sampling_failure_rows)
    profile_count = len({str(row["profile_name"]) for row in matrix_rows})
    role_panel_count = len({str(row["role_panel_id"]) for row in matrix_rows})
    metadata_join_incomplete_count = sum(
        not str(row.get("role_panel_id", "")) or not str(row.get("panel_primary_metric_family", ""))
        for row in reset_rows
    )
    result_passes = (
        len(matrix_rows) == TARGET_PANEL_CELL_COUNT
        and len(reset_rows) == TARGET_PANEL_CELL_COUNT
        and reset_success_count == TARGET_PANEL_CELL_COUNT
        and not sampling_failure_rows
        and profile_count == TARGET_PROFILE_COUNT
        and role_panel_count == TARGET_ROLE_PANEL_COUNT
        and metadata_join_incomplete_count == 0
        and guardrail_violation_count == 0
    )

    label_by_spec = _aggregate_count_rows(reset_rows, ("bounded_panel_spec_id", "sampled_obstacle_label"), "reset_count")
    label_by_role = _aggregate_count_rows(reset_rows, ("role_panel_id", "sampled_obstacle_label"), "reset_count")
    label_by_family = _aggregate_count_rows(reset_rows, ("scenario_family", "sampled_obstacle_label"), "reset_count")

    write_csv_rows(output / "reset_stress_rows.csv", reset_rows)
    write_csv_rows(output / "sampling_failure_rows.csv", sampling_failure_rows, fieldnames=list(reset_rows[0].keys()) if reset_rows else None)
    write_csv_rows(output / "label_distribution_by_spec.csv", label_by_spec)
    write_csv_rows(output / "label_distribution_by_role.csv", label_by_role)
    write_csv_rows(output / "label_distribution_by_family.csv", label_by_family)

    summary = {
        "result_class": (
            "metric_specific_bounded_panel_reset_feasibility_preflight_pass"
            if result_passes
            else "metric_specific_bounded_panel_reset_feasibility_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "bounded_panel_specs_path": str(bounded_panel_specs_path),
        "bounded_panel_matrix_path": str(bounded_panel_matrix_path),
        "attempted_cell_count": len(reset_rows),
        "target_attempted_cell_count": TARGET_PANEL_CELL_COUNT,
        "matrix_cell_count": len(matrix_rows),
        "target_matrix_cell_count": TARGET_PANEL_CELL_COUNT,
        "reset_success_count": reset_success_count,
        "sampling_failure_count": len(sampling_failure_rows),
        "profile_count": profile_count,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "role_panel_count": role_panel_count,
        "target_role_panel_count": TARGET_ROLE_PANEL_COUNT,
        "metadata_join_incomplete_count": metadata_join_incomplete_count,
        "role_panel_counts": _count_by_key(matrix_rows, "role_panel_id"),
        "sampled_label_counts": _count_by_key(reset_rows, "sampled_obstacle_label"),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": True,
        "policy_action_executed": False,
        "measured_rollout_started": False,
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
            "summary": str(output / "summary.json"),
            "reset_stress_rows": str(output / "reset_stress_rows.csv"),
            "sampling_failure_rows": str(output / "sampling_failure_rows.csv"),
            "label_distribution_by_spec": str(output / "label_distribution_by_spec.csv"),
            "label_distribution_by_role": str(output / "label_distribution_by_role.csv"),
            "label_distribution_by_family": str(output / "label_distribution_by_family.csv"),
        },
        "next_blocker": "m1774-paper-route-metric-specific-bounded-panel-reset-result-audit",
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reset-only bounded panel feasibility preflight.")
    parser.add_argument("--bounded-panel-specs", type=Path, default=DEFAULT_BOUNDED_PANEL_SPECS)
    parser.add_argument("--bounded-panel-matrix", type=Path, default=DEFAULT_BOUNDED_PANEL_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    args = parser.parse_args()

    summary = run_metric_specific_bounded_panel_reset_feasibility_preflight(
        bounded_panel_specs_path=args.bounded_panel_specs,
        bounded_panel_matrix_path=args.bounded_panel_matrix,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"attempted_cell_count={summary['attempted_cell_count']}")
    print(f"reset_success_count={summary['reset_success_count']}")
    print(f"sampling_failure_count={summary['sampling_failure_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
