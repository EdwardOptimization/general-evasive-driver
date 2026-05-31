"""No-reset adapter for support-first executable v2 reset validation specs."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUPPORT_FIRST_MATERIALIZED_SPECS = Path(
    "runs/m1861_executable_v2_support_first_materialization/"
    "support_first_materialized_executable_v2_panel_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1864_executable_v2_support_first_reset_validation_adapter")
DEFAULT_PROFILE_CONFIG_PATH = Path("configs/paper_route_corrected_profiles/m1207_l0_current_masked.json")
PRIMARY_METRIC = "reset_feasibility_sampling_success_rate"
PRIMARY_METRIC_DIRECTION = "higher_is_better"
ADMISSIBILITY_GATE = "all_specs_resettable_without_label_leakage_or_ranking"
TARGET_MATERIALIZED_SPEC_COUNT = 180
TARGET_EXECUTABLE_SPEC_COUNT = 180
TARGET_PROFILE_COUNT = 8
TARGET_ROLE_COUNT = 4
TARGET_SURFACE_COUNT = 2
TARGET_ROLE_SURFACE_COUNT = 8
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
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
REQUIRED_CONVERTED_FIELDS = (
    "v2_panel_spec_id",
    "source_v1_bounded_panel_spec_id",
    "source_v1_role_panel_id",
    "source_scenario_spec_id",
    "v2_role_surface_id",
    "role_panel_id",
    "profile_name",
    "profile_config_path",
    "v2_task_label",
    "allowed_labels_metadata_only",
    "labels_enter_actor_input",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
    "v2_primary_metric",
    "v2_primary_metric_direction",
    "v2_admissibility_gate",
    "reset_ready_spec",
    "diagnostic_only_no_ranking_claim",
    "v2_ranking_admissible_by_default",
    "reset_validation_required",
    "support_first_materialized_v2_panel_spec_id",
    "candidate_source_id",
    "source_role_semantics",
    "surface_variant",
    "cell_selection_kind",
    "env_config",
    "measured_execution_admissible",
    "controller_family_ranking_admissible",
    "environment_reset_scheduled",
    "environment_rollout_scheduled",
    "training_scheduled",
)
MISSING_FIELDNAMES = ["v2_panel_spec_id", "source_row_id", "missing_field"]
DUPLICATE_FIELDNAMES = ["v2_panel_spec_id", "duplicate_count"]


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


def _slug(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return "unknown"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace("-", "m").replace(".", "p")


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def load_support_first_materialized_specs(
    path: Path | str = DEFAULT_SUPPORT_FIRST_MATERIALIZED_SPECS,
) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_v2_panel_specs")
    if not isinstance(rows, list):
        raise ValueError("support-first materialized payload must contain executable_v2_panel_specs")
    return sorted([dict(row) for row in rows], key=lambda row: str(row.get("materialized_v2_panel_spec_id", "")))


def _reset_preflight_env_config(row: Mapping[str, Any]) -> dict[str, Any]:
    env_config = deepcopy(dict(row.get("env_config") or {}))
    if row.get("dt", "") not in (None, ""):
        env_config.setdefault("dt", row.get("dt"))
    env_config.setdefault("history_length", 1)
    env_config.setdefault("action_history_mode", "full")
    env_config.setdefault("include_privileged_params", False)
    env_config.setdefault("obstacle_relative_velocity_mode", "zero")
    env_config.setdefault("wheel_observation_mode", "none")
    return env_config


def support_first_reset_executable_row(
    row: Mapping[str, Any],
    *,
    profile_config_path: Path | str = DEFAULT_PROFILE_CONFIG_PATH,
) -> dict[str, Any]:
    spec_id = str(row.get("materialized_v2_panel_spec_id", ""))
    role = str(row.get("source_role_semantics", row.get("profile_group", "")))
    surface = str(row.get("surface_variant", row.get("source_family_id", "")))
    label = str(row.get("v2_task_label", ""))
    obstacle_half_width = row.get("obstacle_half_width", "")
    mu = row.get("mu", "")
    return {
        "v2_panel_spec_id": spec_id,
        "source_v1_bounded_panel_spec_id": str(row.get("source_v1_bounded_panel_spec_id", "")),
        "source_v1_role_panel_id": role,
        "source_scenario_spec_id": str(row.get("source_scenario_spec_id", "")),
        "v2_role_surface_id": f"{role}::{surface}",
        "role_panel_id": role,
        "profile_name": str(row.get("profile_name", "")),
        "profile_config_path": str(profile_config_path),
        "checkpoint_path": "",
        "config_exists": Path(profile_config_path).exists(),
        "checkpoint_exists": False,
        "v2_task_label": label,
        "allowed_labels_metadata_only": label,
        "labels_enter_actor_input": False,
        "hidden_dynamics_bucket": f"mu_{_slug(mu)}::{surface}",
        "road_boundary_bucket": "circle_r18",
        "obstacle_timing_bucket": surface,
        "obstacle_lateral_bucket": f"support_first_width_{_slug(obstacle_half_width)}",
        "v2_primary_metric": PRIMARY_METRIC,
        "v2_primary_metric_direction": PRIMARY_METRIC_DIRECTION,
        "v2_admissibility_gate": ADMISSIBILITY_GATE,
        "reset_ready_spec": True,
        "diagnostic_only_no_ranking_claim": True,
        "v2_ranking_admissible_by_default": False,
        "reset_validation_required": True,
        "support_first_materialized_v2_panel_spec_id": spec_id,
        "candidate_source_id": str(row.get("candidate_source_id", "")),
        "source_role_semantics": role,
        "surface_variant": surface,
        "cell_selection_kind": str(row.get("cell_selection_kind", "")),
        "support_contract_id": str(row.get("support_contract_id", "")),
        "materialization_contract_id": str(row.get("materialization_contract_id", "")),
        "profile_group": str(row.get("profile_group", "")),
        "source_family_id": str(row.get("source_family_id", "")),
        "speed_ref": row.get("speed_ref", ""),
        "mu": mu,
        "friction_step_enabled": _bool(row.get("friction_step_enabled")),
        "friction_step_at": row.get("friction_step_at", ""),
        "dt": row.get("dt", ""),
        "min_time_after_friction_step": row.get("min_time_after_friction_step", ""),
        "obstacle_distance": row.get("obstacle_distance", ""),
        "obstacle_half_width": obstacle_half_width,
        "threshold_score": row.get("threshold_score", ""),
        "env_config": _reset_preflight_env_config(row),
        "measured_execution_required": _bool(row.get("measured_execution_required")),
        "measured_execution_admissible": False,
        "controller_family_ranking_admissible": False,
        "environment_reset_scheduled": False,
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
    }


def support_first_reset_executable_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    profile_config_path: Path | str = DEFAULT_PROFILE_CONFIG_PATH,
) -> list[dict[str, Any]]:
    return sorted(
        [
            support_first_reset_executable_row(row, profile_config_path=profile_config_path)
            for row in rows
        ],
        key=lambda item: str(item["v2_panel_spec_id"]),
    )


def missing_required_field_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        spec_id = str(row.get("v2_panel_spec_id", ""))
        source_id = str(row.get("support_first_materialized_v2_panel_spec_id", spec_id))
        for field in REQUIRED_CONVERTED_FIELDS:
            value = row.get(field)
            if value is None or value == "" or (field == "env_config" and not value):
                output.append(
                    {
                        "v2_panel_spec_id": spec_id,
                        "source_row_id": source_id,
                        "missing_field": field,
                    }
                )
    return output


def duplicate_key_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("v2_panel_spec_id", "")) for row in rows)
    return [
        {"v2_panel_spec_id": spec_id, "duplicate_count": count}
        for spec_id, count in sorted(counts.items())
        if spec_id and count > 1
    ]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "support_first_reset_validation_payload_ready",
            "admissible": True,
            "reason": "adapter emits executable_v2_panel_specs-shaped artifacts for later reset-only validation",
        },
        {
            "claim": "reset_feasibility",
            "admissible": False,
            "reason": "environment reset has not been run over the converted payload",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "measured execution remains blocked until reset validation passes",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "conversion is task-quality infrastructure, not controller ranking evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "adapter artifacts do not test history necessity",
        },
    ]


def run_support_first_reset_validation_adapter(
    *,
    support_first_materialized_specs_path: Path | str = DEFAULT_SUPPORT_FIRST_MATERIALIZED_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    profile_config_path: Path | str = DEFAULT_PROFILE_CONFIG_PATH,
    target_materialized_spec_count: int | None = TARGET_MATERIALIZED_SPEC_COUNT,
    target_executable_spec_count: int | None = TARGET_EXECUTABLE_SPEC_COUNT,
    target_profile_count: int | None = TARGET_PROFILE_COUNT,
    target_role_count: int | None = TARGET_ROLE_COUNT,
    target_surface_count: int | None = TARGET_SURFACE_COUNT,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    next_blocker: str = "m1865-executable-v2-support-first-reset-validation-adapter-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    materialized_rows = load_support_first_materialized_specs(support_first_materialized_specs_path)
    executable_rows = support_first_reset_executable_rows(
        materialized_rows,
        profile_config_path=profile_config_path,
    )
    missing_rows = missing_required_field_rows(executable_rows)
    duplicate_rows = duplicate_key_rows(executable_rows)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))

    role_count = len({str(row.get("role_panel_id", "")) for row in executable_rows})
    surface_count = len({str(row.get("surface_variant", "")) for row in executable_rows})
    role_surface_count = len({str(row.get("v2_role_surface_id", "")) for row in executable_rows})
    profile_count = len({str(row.get("profile_name", "")) for row in executable_rows})
    reset_ready_spec_count = sum(_bool(row.get("reset_ready_spec")) for row in executable_rows)
    reset_validation_required_count = sum(_bool(row.get("reset_validation_required")) for row in executable_rows)
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in executable_rows)
    ranking_admissible_by_default_count = sum(_bool(row.get("v2_ranking_admissible_by_default")) for row in executable_rows)
    measured_execution_admissible_count = sum(_bool(row.get("measured_execution_admissible")) for row in executable_rows)
    controller_family_ranking_admissible_count = sum(
        _bool(row.get("controller_family_ranking_admissible")) for row in executable_rows
    )

    result_passes = (
        (target_materialized_spec_count is None or len(materialized_rows) == int(target_materialized_spec_count))
        and (target_executable_spec_count is None or len(executable_rows) == int(target_executable_spec_count))
        and (target_profile_count is None or profile_count == int(target_profile_count))
        and (target_role_count is None or role_count == int(target_role_count))
        and (target_surface_count is None or surface_count == int(target_surface_count))
        and (target_role_surface_count is None or role_surface_count == int(target_role_surface_count))
        and reset_ready_spec_count == len(executable_rows)
        and reset_validation_required_count == len(executable_rows)
        and labels_enter_actor_input_count == 0
        and ranking_admissible_by_default_count == 0
        and measured_execution_admissible_count == 0
        and controller_family_ranking_admissible_count == 0
        and not missing_rows
        and not duplicate_rows
        and guardrail_violation_count == 0
    )

    write_json(
        output / "support_first_reset_executable_v2_panel_specs.json",
        {
            "generated_at_utc": utc_timestamp(),
            "source_support_first_materialized_specs_path": str(support_first_materialized_specs_path),
            "profile_config_path": str(profile_config_path),
            "executable_v2_panel_specs": executable_rows,
        },
    )
    write_csv_rows(output / "support_first_reset_executable_v2_panel_specs.csv", executable_rows)
    write_csv_rows(output / "support_first_reset_validation_matrix.csv", executable_rows)
    write_csv_rows(
        output / "support_first_reset_missing_field_rows.csv",
        missing_rows,
        MISSING_FIELDNAMES,
    )
    write_csv_rows(
        output / "support_first_reset_duplicate_key_rows.csv",
        duplicate_rows,
        DUPLICATE_FIELDNAMES,
    )
    write_csv_rows(output / "support_first_reset_validation_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "executable_v2_support_first_reset_validation_adapter_pass"
            if result_passes
            else "executable_v2_support_first_reset_validation_adapter_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "support_first_materialized_specs_path": str(support_first_materialized_specs_path),
        "profile_config_path": str(profile_config_path),
        "input_materialized_spec_count": len(materialized_rows),
        "target_materialized_spec_count": target_materialized_spec_count,
        "targeted_reset_executable_spec_count": len(executable_rows),
        "target_executable_spec_count": target_executable_spec_count,
        "role_count": role_count,
        "target_role_count": target_role_count,
        "surface_count": surface_count,
        "target_surface_count": target_surface_count,
        "role_surface_count": role_surface_count,
        "target_role_surface_count": target_role_surface_count,
        "profile_count": profile_count,
        "target_profile_count": target_profile_count,
        "reset_ready_spec_count": reset_ready_spec_count,
        "reset_validation_required_count": reset_validation_required_count,
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "ranking_admissible_by_default_count": ranking_admissible_by_default_count,
        "measured_execution_admissible_count": measured_execution_admissible_count,
        "controller_family_ranking_admissible_count": controller_family_ranking_admissible_count,
        "missing_required_field_count": len(missing_rows),
        "duplicate_key_count": len(duplicate_rows),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "role_counts": _count_by_key(executable_rows, "role_panel_id"),
        "surface_counts": _count_by_key(executable_rows, "surface_variant"),
        "role_surface_counts": _count_by_key(executable_rows, "v2_role_surface_id"),
        "profile_counts": _count_by_key(executable_rows, "profile_name"),
        "task_label_counts": _count_by_key(executable_rows, "v2_task_label"),
        "environment_reset_started": False,
        "environment_rollout_started": False,
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
            "support_first_reset_executable_v2_panel_specs_json": str(
                output / "support_first_reset_executable_v2_panel_specs.json"
            ),
            "support_first_reset_executable_v2_panel_specs_csv": str(
                output / "support_first_reset_executable_v2_panel_specs.csv"
            ),
            "support_first_reset_validation_matrix": str(output / "support_first_reset_validation_matrix.csv"),
            "support_first_reset_missing_field_rows": str(output / "support_first_reset_missing_field_rows.csv"),
            "support_first_reset_duplicate_key_rows": str(output / "support_first_reset_duplicate_key_rows.csv"),
            "support_first_reset_validation_claim_boundary": str(
                output / "support_first_reset_validation_claim_boundary.csv"
            ),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert support-first materialized executable v2 specs into reset-validation specs without reset."
    )
    parser.add_argument("--support-first-materialized-specs", type=Path, default=DEFAULT_SUPPORT_FIRST_MATERIALIZED_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--profile-config-path", type=Path, default=DEFAULT_PROFILE_CONFIG_PATH)
    parser.add_argument("--target-materialized-spec-count", type=int, default=TARGET_MATERIALIZED_SPEC_COUNT)
    parser.add_argument("--target-executable-spec-count", type=int, default=TARGET_EXECUTABLE_SPEC_COUNT)
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--target-role-count", type=int, default=TARGET_ROLE_COUNT)
    parser.add_argument("--target-surface-count", type=int, default=TARGET_SURFACE_COUNT)
    parser.add_argument("--target-role-surface-count", type=int, default=TARGET_ROLE_SURFACE_COUNT)
    parser.add_argument("--next-blocker", default="m1865-executable-v2-support-first-reset-validation-adapter-execution-design")
    args = parser.parse_args()

    summary = run_support_first_reset_validation_adapter(
        support_first_materialized_specs_path=args.support_first_materialized_specs,
        output_dir=args.output_dir,
        profile_config_path=args.profile_config_path,
        target_materialized_spec_count=args.target_materialized_spec_count,
        target_executable_spec_count=args.target_executable_spec_count,
        target_profile_count=args.target_profile_count,
        target_role_count=args.target_role_count,
        target_surface_count=args.target_surface_count,
        target_role_surface_count=args.target_role_surface_count,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"targeted_reset_executable_spec_count={summary['targeted_reset_executable_spec_count']}")
    print(f"profile_count={summary['profile_count']}")
    print(f"role_surface_count={summary['role_surface_count']}")
    print(f"missing_required_field_count={summary['missing_required_field_count']}")
    print(f"duplicate_key_count={summary['duplicate_key_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
