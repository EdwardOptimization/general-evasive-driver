"""Reset-only feasibility adapter for executable v2 panel specs."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import env_config_for_executable_profile
from autodrift.env import AutoDriftEnv


DEFAULT_EXECUTABLE_V2_PANEL_SPECS = Path(
    "runs/m1790_executable_v2_panel_spec_materialization_preflight/executable_v2_panel_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1793_executable_v2_reset_feasibility_preflight")
DEFAULT_EVAL_SEED_BASE = 179300
TARGET_V2_PANEL_SPEC_COUNT = 312
TARGET_PROFILE_COUNT = 12
TARGET_ROLE_SURFACE_COUNT = 6
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


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"true", "1", "yes", "y"}:
            return True
        if stripped in {"false", "0", "no", "n", ""}:
            return False
    return default


def load_executable_v2_panel_specs(path: Path | str = DEFAULT_EXECUTABLE_V2_PANEL_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return sorted(
        [dict(row) for row in payload["executable_v2_panel_specs"]],
        key=lambda row: str(row["v2_panel_spec_id"]),
    )


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


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


def reset_executable_v2_panel_spec(
    *,
    executable_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    base = {
        "v2_panel_spec_id": str(executable_spec["v2_panel_spec_id"]),
        "source_v1_bounded_panel_spec_id": str(executable_spec.get("source_v1_bounded_panel_spec_id", "")),
        "source_v1_role_panel_id": str(executable_spec.get("source_v1_role_panel_id", "")),
        "source_scenario_spec_id": str(executable_spec.get("source_scenario_spec_id", "")),
        "v2_role_surface_id": str(executable_spec["v2_role_surface_id"]),
        "role_panel_id": str(executable_spec.get("role_panel_id", executable_spec["v2_role_surface_id"])),
        "profile_name": str(executable_spec["profile_name"]),
        "eval_seed": int(eval_seed),
        "v2_task_label": str(executable_spec["v2_task_label"]),
        "allowed_labels_metadata_only": str(executable_spec.get("allowed_labels_metadata_only", "")),
        "labels_enter_actor_input": _bool(executable_spec.get("labels_enter_actor_input", False)),
        "hidden_dynamics_bucket": str(executable_spec["hidden_dynamics_bucket"]),
        "road_boundary_bucket": str(executable_spec.get("road_boundary_bucket", "")),
        "obstacle_timing_bucket": str(executable_spec.get("obstacle_timing_bucket", "")),
        "obstacle_lateral_bucket": str(executable_spec.get("obstacle_lateral_bucket", "")),
        "v2_primary_metric": str(executable_spec["v2_primary_metric"]),
        "v2_primary_metric_direction": str(executable_spec.get("v2_primary_metric_direction", "")),
        "v2_admissibility_gate": str(executable_spec["v2_admissibility_gate"]),
        "reset_ready_spec": _bool(executable_spec.get("reset_ready_spec", False)),
        "diagnostic_only_no_ranking_claim": _bool(executable_spec.get("diagnostic_only_no_ranking_claim", True)),
        "v2_ranking_admissible_by_default": _bool(executable_spec.get("v2_ranking_admissible_by_default", False)),
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
            executable_spec=executable_spec,
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
    except Exception as exc:  # noqa: BLE001 - reset preflight must preserve sampling failures.
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


def run_executable_v2_reset_feasibility_preflight(
    *,
    executable_v2_panel_specs_path: Path | str = DEFAULT_EXECUTABLE_V2_PANEL_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_spec_count: int | None = TARGET_V2_PANEL_SPEC_COUNT,
    target_profile_count: int | None = TARGET_PROFILE_COUNT,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    next_blocker: str = "m1794-executable-v2-reset-feasibility-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_executable_v2_panel_specs(executable_v2_panel_specs_path)
    profile_config_by_name = {
        str(row["profile_name"]): read_json(row["profile_config_path"])
        for row in executable_specs
    }

    reset_rows: list[dict[str, Any]] = []
    for spec_index, executable_spec in enumerate(executable_specs):
        reset_rows.append(
            reset_executable_v2_panel_spec(
                executable_spec=executable_spec,
                profile_config=profile_config_by_name[str(executable_spec["profile_name"])],
                eval_seed=int(eval_seed_base) + int(spec_index),
            )
        )

    sampling_failure_rows = [dict(row) for row in reset_rows if not bool(row["reset_success"])]
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    reset_success_count = len(reset_rows) - len(sampling_failure_rows)
    profile_count = len({str(row["profile_name"]) for row in executable_specs})
    role_surface_count = len({str(row["v2_role_surface_id"]) for row in executable_specs})
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input", False)) for row in executable_specs)
    ranking_admissible_by_default_count = sum(
        _bool(row.get("v2_ranking_admissible_by_default", False)) for row in executable_specs
    )
    reset_ready_spec_count = sum(_bool(row.get("reset_ready_spec", False)) for row in executable_specs)
    metadata_join_incomplete_count = sum(
        not str(row.get("v2_role_surface_id", "")) or not str(row.get("v2_primary_metric", ""))
        for row in reset_rows
    )
    target_spec_matches = target_spec_count is None or len(executable_specs) == int(target_spec_count)
    target_profile_matches = target_profile_count is None or profile_count == int(target_profile_count)
    target_surface_matches = target_role_surface_count is None or role_surface_count == int(target_role_surface_count)
    result_passes = (
        target_spec_matches
        and len(reset_rows) == len(executable_specs)
        and reset_success_count == len(executable_specs)
        and not sampling_failure_rows
        and target_profile_matches
        and target_surface_matches
        and reset_ready_spec_count == len(executable_specs)
        and labels_enter_actor_input_count == 0
        and ranking_admissible_by_default_count == 0
        and metadata_join_incomplete_count == 0
        and guardrail_violation_count == 0
    )

    label_by_surface = _aggregate_count_rows(reset_rows, ("v2_role_surface_id", "sampled_obstacle_label"), "reset_count")
    label_by_profile = _aggregate_count_rows(reset_rows, ("profile_name", "sampled_obstacle_label"), "reset_count")
    label_by_hidden_bucket = _aggregate_count_rows(
        reset_rows,
        ("v2_role_surface_id", "hidden_dynamics_bucket", "sampled_obstacle_label"),
        "reset_count",
    )

    write_csv_rows(output / "reset_stress_rows.csv", reset_rows)
    write_csv_rows(
        output / "sampling_failure_rows.csv",
        sampling_failure_rows,
        fieldnames=list(reset_rows[0].keys()) if reset_rows else None,
    )
    write_csv_rows(output / "label_distribution_by_surface.csv", label_by_surface)
    write_csv_rows(output / "label_distribution_by_profile.csv", label_by_profile)
    write_csv_rows(output / "label_distribution_by_hidden_bucket.csv", label_by_hidden_bucket)

    summary = {
        "result_class": (
            "executable_v2_reset_feasibility_preflight_pass"
            if result_passes
            else "executable_v2_reset_feasibility_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "executable_v2_panel_specs_path": str(executable_v2_panel_specs_path),
        "attempted_spec_count": len(reset_rows),
        "target_attempted_spec_count": target_spec_count,
        "reset_success_count": reset_success_count,
        "sampling_failure_count": len(sampling_failure_rows),
        "profile_count": profile_count,
        "target_profile_count": target_profile_count,
        "role_surface_count": role_surface_count,
        "target_role_surface_count": target_role_surface_count,
        "reset_ready_spec_count": reset_ready_spec_count,
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "ranking_admissible_by_default_count": ranking_admissible_by_default_count,
        "metadata_join_incomplete_count": metadata_join_incomplete_count,
        "role_surface_counts": _count_by_key(reset_rows, "v2_role_surface_id"),
        "sampled_label_counts": _count_by_key(reset_rows, "sampled_obstacle_label"),
        "hidden_bucket_counts": _count_by_key(reset_rows, "hidden_dynamics_bucket"),
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
            "label_distribution_by_surface": str(output / "label_distribution_by_surface.csv"),
            "label_distribution_by_profile": str(output / "label_distribution_by_profile.csv"),
            "label_distribution_by_hidden_bucket": str(output / "label_distribution_by_hidden_bucket.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reset-only executable v2 panel feasibility preflight.")
    parser.add_argument("--executable-v2-panel-specs", type=Path, default=DEFAULT_EXECUTABLE_V2_PANEL_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-spec-count", type=int, default=TARGET_V2_PANEL_SPEC_COUNT)
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--target-role-surface-count", type=int, default=TARGET_ROLE_SURFACE_COUNT)
    parser.add_argument("--next-blocker", default="m1794-executable-v2-reset-feasibility-result-audit")
    args = parser.parse_args()

    summary = run_executable_v2_reset_feasibility_preflight(
        executable_v2_panel_specs_path=args.executable_v2_panel_specs,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        target_spec_count=int(args.target_spec_count),
        target_profile_count=int(args.target_profile_count),
        target_role_surface_count=int(args.target_role_surface_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"attempted_spec_count={summary['attempted_spec_count']}")
    print(f"reset_success_count={summary['reset_success_count']}")
    print(f"sampling_failure_count={summary['sampling_failure_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
