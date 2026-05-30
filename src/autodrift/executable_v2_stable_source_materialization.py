"""No-reset materializer for executable v2 stable source-label gaps."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_NEW_MATERIALIZATION_NEEDS = Path(
    "runs/m1805_executable_v2_stable_source_label_topup_preflight/stable_new_materialization_need_rows.csv"
)
DEFAULT_TOPUP_CANDIDATES = Path(
    "runs/m1805_executable_v2_stable_source_label_topup_preflight/stable_topup_candidate_rows.csv"
)
DEFAULT_BOUNDED_PANEL_SPECS = Path("runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json")
DEFAULT_BOUNDED_PANEL_MATRIX = Path("runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_matrix.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1809_executable_v2_stable_source_materialization")
STABLE_SURFACE = "stable_avoidance_aes"
SAMPLER_REPAIR_VARIANT_ID = "stable_source_label_materialization_v1"
MATERIALIZATION_STRATEGY = "label_specific_stable_sampler_repair_v1"
TARGET_KEYS = (
    "v2_role_surface_id",
    "v2_task_label",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
)
PROFILE_FIELDS = (
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "evaluation_role",
    "primary_metric_family",
)
SPEC_CSV_FIELDNAMES = [
    "stable_materialization_spec_id",
    "target_topup_id",
    "target_bounded_panel_spec_id",
    "target_source_scenario_spec_id",
    "target_v2_task_label",
    "v2_role_surface_id",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
    "stable_materialization_key",
    "materialized_source_scenario_spec_id",
    "materialized_bounded_panel_spec_id",
    "source_basis_bounded_panel_spec_id",
    "source_basis_type",
    "source_basis_support_status",
    "near_candidate_ids",
    "materialization_strategy",
    "sampler_repair_variant_id",
    "env_config_source",
    "env_config_delta_json",
    "profile_control_count",
    "profile_controls_preserved",
    "labels_enter_actor_input",
    "reset_validation_required",
    "measured_execution_admissible",
    "controller_family_ranking_admissible",
    "diagnostic_only_no_ranking_claim",
    "duplicate_key_detected",
    "materialization_executed",
    "environment_reset_started",
    "environment_rollout_started",
]
DUPLICATE_FIELDNAMES = [
    "stable_materialization_key",
    "duplicate_count",
    "target_topup_ids",
    "target_bounded_panel_spec_ids",
]
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


def _read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _stable_key(row: Mapping[str, Any]) -> str:
    return "|".join(str(row.get(key, "")) for key in TARGET_KEYS)


def _json_string(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def load_new_materialization_needs(path: Path | str = DEFAULT_NEW_MATERIALIZATION_NEEDS) -> list[dict[str, Any]]:
    rows = _read_csv_rows(path)
    return [
        dict(row)
        for row in rows
        if str(row.get("v2_role_surface_id", "")) == STABLE_SURFACE
        and _bool(row.get("requires_new_materialization"), default=True)
    ]


def load_topup_candidate_rows(path: Path | str = DEFAULT_TOPUP_CANDIDATES) -> list[dict[str, Any]]:
    if not Path(path).exists():
        return []
    return _read_csv_rows(path)


def load_bounded_panel_specs(path: Path | str = DEFAULT_BOUNDED_PANEL_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return [dict(row) for row in payload["bounded_panel_specs"]]


def load_profile_rows(path: Path | str = DEFAULT_BOUNDED_PANEL_MATRIX) -> list[dict[str, Any]]:
    rows = _read_csv_rows(path)
    by_profile: dict[str, dict[str, Any]] = {}
    for row in rows:
        profile_name = str(row.get("profile_name", ""))
        if profile_name and profile_name not in by_profile:
            by_profile[profile_name] = {key: row.get(key, "") for key in PROFILE_FIELDS}
    return [by_profile[key] for key in sorted(by_profile)]


def materialization_targets(needs: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for index, row in enumerate(needs):
        target = {
            "stable_materialization_target_id": f"stable-source-target-{index:03d}",
            "target_topup_id": str(row.get("topup_target_id", f"stable-topup-{index:03d}")),
            "target_bounded_panel_spec_id": str(row.get("source_scenario_spec_id", "")),
            "target_source_scenario_spec_id": str(row.get("source_scenario_spec_id", "")),
            "target_v2_task_label": str(row.get("v2_task_label", "")),
            "v2_role_surface_id": str(row.get("v2_role_surface_id", STABLE_SURFACE)),
            "hidden_dynamics_bucket": str(row.get("hidden_dynamics_bucket", "")),
            "road_boundary_bucket": str(row.get("road_boundary_bucket", "")),
            "obstacle_timing_bucket": str(row.get("obstacle_timing_bucket", "")),
            "obstacle_lateral_bucket": str(row.get("obstacle_lateral_bucket", "")),
            "missing_profile_count": int(row.get("missing_profile_count", 0) or 0),
            "stable_materialization_key": _stable_key(
                {
                    "v2_role_surface_id": str(row.get("v2_role_surface_id", STABLE_SURFACE)),
                    "v2_task_label": str(row.get("v2_task_label", "")),
                    "hidden_dynamics_bucket": str(row.get("hidden_dynamics_bucket", "")),
                    "road_boundary_bucket": str(row.get("road_boundary_bucket", "")),
                    "obstacle_timing_bucket": str(row.get("obstacle_timing_bucket", "")),
                    "obstacle_lateral_bucket": str(row.get("obstacle_lateral_bucket", "")),
                }
            ),
        }
        targets.append(target)
    return targets


def duplicate_key_rows(targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, list[Mapping[str, Any]]] = {}
    for target in targets:
        by_key.setdefault(str(target["stable_materialization_key"]), []).append(target)
    rows: list[dict[str, Any]] = []
    for key, grouped in sorted(by_key.items()):
        if len(grouped) <= 1:
            continue
        rows.append(
            {
                "stable_materialization_key": key,
                "duplicate_count": len(grouped),
                "target_topup_ids": ";".join(str(row.get("target_topup_id", "")) for row in grouped),
                "target_bounded_panel_spec_ids": ";".join(str(row.get("target_bounded_panel_spec_id", "")) for row in grouped),
            }
        )
    return rows


def _near_candidate_ids(target: Mapping[str, Any], candidate_rows: list[Mapping[str, Any]]) -> str:
    ids = [
        str(row.get("candidate_bounded_panel_spec_id", ""))
        for row in candidate_rows
        if str(row.get("topup_target_id", "")) == str(target.get("target_topup_id", ""))
        and str(row.get("candidate_class", "")) == "near_existing_candidate"
    ]
    return ";".join(item for item in ids if item)


def _basis_support_status(target: Mapping[str, Any], candidate_rows: list[Mapping[str, Any]]) -> str:
    for row in candidate_rows:
        if (
            str(row.get("topup_target_id", "")) == str(target.get("target_topup_id", ""))
            and str(row.get("candidate_bounded_panel_spec_id", "")) == str(target.get("target_bounded_panel_spec_id", ""))
        ):
            return str(row.get("observed_reset_support_status", "unobserved"))
    return "unsupported_systematic"


def _patched_env_config(env_config: Mapping[str, Any], label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    patched = deepcopy(dict(env_config))
    obstacle = dict(patched.get("obstacle", {}))
    obstacle["allowed_labels"] = [label]
    obstacle["max_sample_attempts"] = max(int(obstacle.get("max_sample_attempts", 0) or 0), 1000)
    if label == "aes_feasible":
        obstacle["require_aeb_infeasible"] = True
    elif label == "aeb_feasible":
        obstacle["require_aeb_infeasible"] = False
    patched["obstacle"] = obstacle
    delta = {
        "obstacle.allowed_labels": [label],
        "obstacle.max_sample_attempts": obstacle["max_sample_attempts"],
        "obstacle.require_aeb_infeasible": obstacle.get("require_aeb_infeasible"),
        "sampler_repair_variant_id": SAMPLER_REPAIR_VARIANT_ID,
    }
    return patched, delta


def materialization_specs(
    *,
    targets: list[Mapping[str, Any]],
    bounded_panel_specs: list[Mapping[str, Any]],
    candidate_rows: list[Mapping[str, Any]],
    profile_control_count: int,
    id_prefix: str = "m1809",
) -> list[dict[str, Any]]:
    specs_by_bounded_id = {str(row.get("bounded_panel_spec_id", row.get("scenario_spec_id", ""))): dict(row) for row in bounded_panel_specs}
    duplicates = {str(row["stable_materialization_key"]) for row in duplicate_key_rows(targets)}
    specs: list[dict[str, Any]] = []
    for index, target in enumerate(targets):
        target_bounded_id = str(target["target_bounded_panel_spec_id"])
        if target_bounded_id not in specs_by_bounded_id:
            raise KeyError(f"missing bounded panel source basis {target_bounded_id}")
        basis = deepcopy(specs_by_bounded_id[target_bounded_id])
        label = str(target["target_v2_task_label"])
        materialized_source_id = f"{id_prefix}-stable-src-{index:03d}"
        materialized_bounded_id = f"{id_prefix}-stable-bp-{index:03d}"
        env_config, env_delta = _patched_env_config(dict(basis.get("env_config", {})), label)
        row = {
            **basis,
            "scenario_spec_id": materialized_bounded_id,
            "bounded_panel_spec_id": materialized_bounded_id,
            "source_scenario_spec_id": materialized_source_id,
            "stable_materialization_spec_id": f"{id_prefix}-stable-mat-{index:03d}",
            "target_topup_id": str(target["target_topup_id"]),
            "target_bounded_panel_spec_id": target_bounded_id,
            "target_source_scenario_spec_id": str(target["target_source_scenario_spec_id"]),
            "target_v2_task_label": label,
            "v2_role_surface_id": str(target["v2_role_surface_id"]),
            "hidden_dynamics_bucket": str(target["hidden_dynamics_bucket"]),
            "road_boundary_bucket": str(target["road_boundary_bucket"]),
            "obstacle_timing_bucket": str(target["obstacle_timing_bucket"]),
            "obstacle_lateral_bucket": str(target["obstacle_lateral_bucket"]),
            "stable_materialization_key": str(target["stable_materialization_key"]),
            "materialized_source_scenario_spec_id": materialized_source_id,
            "materialized_bounded_panel_spec_id": materialized_bounded_id,
            "source_basis_bounded_panel_spec_id": target_bounded_id,
            "source_basis_type": "target_env_config_clone",
            "source_basis_support_status": _basis_support_status(target, candidate_rows),
            "near_candidate_ids": _near_candidate_ids(target, candidate_rows),
            "materialization_strategy": MATERIALIZATION_STRATEGY,
            "sampler_repair_variant_id": SAMPLER_REPAIR_VARIANT_ID,
            "sampling_repair_variant_id": SAMPLER_REPAIR_VARIANT_ID,
            "sampling_repair_source": "m1809_stable_source_materialization",
            "sampling_repair_applied": True,
            "allowed_labels_metadata_only": label,
            "env_config_source": f"{target_bounded_id}.env_config",
            "env_config_delta_json": _json_string(env_delta),
            "env_config": env_config,
            "profile_control_count": profile_control_count,
            "profile_controls_preserved": True,
            "labels_enter_actor_input": False,
            "reset_validation_required": True,
            "measured_execution_admissible": False,
            "controller_family_ranking_admissible": False,
            "diagnostic_only_no_ranking_claim": True,
            "ranking_eligible_after_audit": False,
            "duplicate_key_detected": str(target["stable_materialization_key"]) in duplicates,
            "materialization_executed": False,
            "environment_reset_started": False,
            "environment_rollout_started": False,
            "environment_reset_scheduled": False,
            "environment_rollout_scheduled": False,
            "training_scheduled": False,
            "profile_specific_tuning": False,
        }
        specs.append(row)
    return specs


def spec_csv_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: row.get(key, "") for key in SPEC_CSV_FIELDNAMES}


def materialization_matrix_rows(
    *,
    specs: list[Mapping[str, Any]],
    profile_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        for profile in profile_rows:
            profile_name = str(profile.get("profile_name", ""))
            rows.append(
                {
                    "stable_materialization_workload_id": f"{spec['materialized_bounded_panel_spec_id']}::{profile_name}",
                    "scenario_workload_id": f"{spec['materialized_bounded_panel_spec_id']}::{profile_name}",
                    "scenario_spec_id": str(spec["materialized_bounded_panel_spec_id"]),
                    "bounded_panel_spec_id": str(spec["materialized_bounded_panel_spec_id"]),
                    "source_scenario_spec_id": str(spec["materialized_source_scenario_spec_id"]),
                    "target_bounded_panel_spec_id": str(spec["target_bounded_panel_spec_id"]),
                    "target_v2_task_label": str(spec["target_v2_task_label"]),
                    "v2_role_surface_id": str(spec["v2_role_surface_id"]),
                    "stable_materialization_key": str(spec["stable_materialization_key"]),
                    "role_panel_id": str(spec.get("role_panel_id", STABLE_SURFACE)),
                    "hidden_dynamics_bucket": str(spec["hidden_dynamics_bucket"]),
                    "road_boundary_bucket": str(spec["road_boundary_bucket"]),
                    "obstacle_timing_bucket": str(spec["obstacle_timing_bucket"]),
                    "obstacle_lateral_bucket": str(spec["obstacle_lateral_bucket"]),
                    "profile_name": profile_name,
                    "profile_config_path": str(profile.get("profile_config_path", "")),
                    "checkpoint_path": str(profile.get("checkpoint_path", "")),
                    "config_exists": profile.get("config_exists", ""),
                    "checkpoint_exists": profile.get("checkpoint_exists", ""),
                    "evaluation_role": str(profile.get("evaluation_role", "")),
                    "primary_metric_family": str(profile.get("primary_metric_family", "")),
                    "labels_enter_actor_input": False,
                    "reset_validation_required": True,
                    "measured_execution_admissible": False,
                    "controller_family_ranking_admissible": False,
                    "diagnostic_only_no_ranking_claim": True,
                    "environment_reset_scheduled": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                }
            )
    return rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "stable_source_materialization_plan",
            "admissible": True,
            "reason": "no-reset materialization artifacts can guide later reset validation",
        },
        {
            "claim": "reset_feasibility_repaired",
            "admissible": False,
            "reason": "materialized sources still require reset-only validation",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "measured execution remains blocked until reset support is observed",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "source materialization is task-quality infrastructure, not ranking evidence",
        },
    ]


def run_executable_v2_stable_source_materialization(
    *,
    new_materialization_needs_path: Path | str = DEFAULT_NEW_MATERIALIZATION_NEEDS,
    topup_candidates_path: Path | str = DEFAULT_TOPUP_CANDIDATES,
    bounded_panel_specs_path: Path | str = DEFAULT_BOUNDED_PANEL_SPECS,
    bounded_panel_matrix_path: Path | str = DEFAULT_BOUNDED_PANEL_MATRIX,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_materialization_count: int | None = None,
    target_profile_count: int | None = None,
    id_prefix: str = "m1809",
    next_blocker: str = "m1810-executable-v2-stable-source-materialization-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    needs = load_new_materialization_needs(new_materialization_needs_path)
    candidates = load_topup_candidate_rows(topup_candidates_path)
    panel_specs = load_bounded_panel_specs(bounded_panel_specs_path)
    profiles = load_profile_rows(bounded_panel_matrix_path)
    targets = materialization_targets(needs)
    duplicates = duplicate_key_rows(targets)
    specs = materialization_specs(
        targets=targets,
        bounded_panel_specs=panel_specs,
        candidate_rows=candidates,
        profile_control_count=len(profiles),
        id_prefix=id_prefix,
    )
    matrix_rows = materialization_matrix_rows(specs=specs, profile_rows=profiles)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    target_matches = target_materialization_count is None or len(specs) == int(target_materialization_count)
    profile_matches = target_profile_count is None or len(profiles) == int(target_profile_count)
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in specs)
    reset_validation_required_count = sum(_bool(row.get("reset_validation_required")) for row in specs)
    measured_execution_admissible_count = sum(_bool(row.get("measured_execution_admissible")) for row in specs)
    ranking_admissible_count = sum(_bool(row.get("controller_family_ranking_admissible")) for row in specs)
    result_passes = (
        target_matches
        and profile_matches
        and not duplicates
        and labels_enter_actor_input_count == 0
        and measured_execution_admissible_count == 0
        and ranking_admissible_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "stable_source_materialization_targets.csv", targets)
    write_csv_rows(output / "stable_source_materialization_specs.csv", [spec_csv_row(row) for row in specs], SPEC_CSV_FIELDNAMES)
    write_json(output / "stable_source_materialization_specs.json", {"stable_source_materialization_specs": specs})
    write_csv_rows(output / "stable_source_materialization_matrix.csv", matrix_rows)
    write_csv_rows(output / "stable_source_materialization_duplicate_keys.csv", duplicates, DUPLICATE_FIELDNAMES)
    write_csv_rows(output / "stable_source_materialization_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "executable_v2_stable_source_materialization_pass"
            if result_passes
            else "executable_v2_stable_source_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "new_materialization_needs_path": str(new_materialization_needs_path),
        "topup_candidates_path": str(topup_candidates_path),
        "bounded_panel_specs_path": str(bounded_panel_specs_path),
        "bounded_panel_matrix_path": str(bounded_panel_matrix_path),
        "stable_materialization_target_count": len(targets),
        "target_materialization_count": target_materialization_count,
        "stable_materialization_spec_count": len(specs),
        "stable_materialization_matrix_row_count": len(matrix_rows),
        "profile_control_count": len(profiles),
        "target_profile_count": target_profile_count,
        "materialization_strategy_counts": _count_by_key(specs, "materialization_strategy"),
        "duplicate_key_count": len(duplicates),
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "reset_validation_required_count": reset_validation_required_count,
        "measured_execution_admissible_count": measured_execution_admissible_count,
        "controller_family_ranking_admissible_count": ranking_admissible_count,
        "source_materialization_executed": False,
        "measured_execution_admissible": False,
        "controller_family_ranking_admissible": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
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
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build no-reset stable source materialization planning artifacts.")
    parser.add_argument("--new-materialization-needs", type=Path, default=DEFAULT_NEW_MATERIALIZATION_NEEDS)
    parser.add_argument("--topup-candidates", type=Path, default=DEFAULT_TOPUP_CANDIDATES)
    parser.add_argument("--bounded-panel-specs", type=Path, default=DEFAULT_BOUNDED_PANEL_SPECS)
    parser.add_argument("--bounded-panel-matrix", type=Path, default=DEFAULT_BOUNDED_PANEL_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-materialization-count", type=int, default=None)
    parser.add_argument("--target-profile-count", type=int, default=None)
    parser.add_argument("--id-prefix", default="m1809")
    parser.add_argument("--next-blocker", default="m1810-executable-v2-stable-source-materialization-execution-design")
    args = parser.parse_args()

    summary = run_executable_v2_stable_source_materialization(
        new_materialization_needs_path=args.new_materialization_needs,
        topup_candidates_path=args.topup_candidates,
        bounded_panel_specs_path=args.bounded_panel_specs,
        bounded_panel_matrix_path=args.bounded_panel_matrix,
        output_dir=args.output_dir,
        target_materialization_count=args.target_materialization_count,
        target_profile_count=args.target_profile_count,
        id_prefix=args.id_prefix,
        next_blocker=args.next_blocker,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"stable_materialization_spec_count={summary['stable_materialization_spec_count']}")
    print(f"stable_materialization_matrix_row_count={summary['stable_materialization_matrix_row_count']}")
    print(f"duplicate_key_count={summary['duplicate_key_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
