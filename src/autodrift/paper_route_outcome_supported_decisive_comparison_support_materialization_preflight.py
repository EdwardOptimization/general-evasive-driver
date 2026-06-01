"""No-reset materialization preflight for comparison-support candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec


DEFAULT_CANDIDATES = Path("configs/paper_route_outcome_supported_decisive_comparison_support_candidates_v0.json")
DEFAULT_PROFILE_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight")
DEFAULT_NEXT_BLOCKER = (
    "m2119-paper-route-outcome-supported-decisive-comparison-support-materialization-preflight-result-audit"
)
PROTOCOL_NAME = "paper_route_outcome_supported_decisive_comparison_support_materialization_preflight_v0"
TARGET_CANDIDATE_COUNT = 240
PROFILE_SUBSET = (
    "L0_current_masked",
    "L1_one_step",
    "L2_window_50",
    "L3_online_gru",
    "L3_reset_control_corrected",
)
TARGET_WORKLOAD_COUNT = TARGET_CANDIDATE_COUNT * len(PROFILE_SUBSET)

SPEC_FIELDNAMES = [
    "task_source_id",
    "panel_source_id",
    "candidate_id",
    "candidate_set_id",
    "scenario_redesign_branch",
    "comparison_support_intent",
    "target_support_tier",
    "panel_task_family",
    "source_origin",
    "source_kind",
    "source_edge",
    "window_tag",
    "source_role_semantics",
    "source_reference",
    "dynamics_band",
    "obstacle_timing_band",
    "road_width_band",
    "initial_speed_band",
    "materialization_semantics",
    "proxy_template_family",
    "reveal_step",
    "capability_pair",
    "actor_input_contract",
    "generated_source_row",
    "paper_validity_claim",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "contract_violation_count",
    "history_length_is_positive",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
]
WORKLOAD_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "panel_source_id",
    "candidate_id",
    "candidate_set_id",
    "scenario_redesign_branch",
    "comparison_support_intent",
    "target_support_tier",
    "panel_task_family",
    "profile_name",
    "profile_config_path",
    "checkpoint_path",
    "source_origin",
    "source_kind",
    "source_edge",
    "window_tag",
    "source_role_semantics",
    "source_reference",
    "dynamics_band",
    "obstacle_timing_band",
    "road_width_band",
    "initial_speed_band",
    "materialization_semantics",
    "proxy_template_family",
    "generated_source_row",
    "paper_validity_claim",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
PROFILE_FIELDNAMES = ["profile_name", "config_path", "checkpoint_path", "config_exists", "checkpoint_exists"]
FAILURE_FIELDNAMES = ["candidate_id", "comparison_support_intent", "failure_type", "reason"]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]
AGGREGATE_FIELDNAMES = ["key", "count"]


def _bool_string(value: Any) -> str:
    return "true" if bool(value) else "false"


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _field(row: Mapping[str, Any], key: str, default: str = "") -> str:
    value = str(row.get(key, "")).strip()
    return value if value else default


def _profile_artifact_rows(*, profile_run_dir: Path | str, profile_seed: int = 167400) -> list[dict[str, Any]]:
    root = Path(profile_run_dir)
    rows: list[dict[str, Any]] = []
    for profile_name in PROFILE_SUBSET:
        config_path = root / "configs" / f"{profile_name}_seed{int(profile_seed)}.json"
        checkpoint_path = root / "profile_runs" / profile_name / f"seed_{int(profile_seed)}" / "checkpoint.pt"
        rows.append(
            {
                "profile_name": profile_name,
                "config_path": str(config_path),
                "checkpoint_path": str(checkpoint_path),
                "config_exists": config_path.exists(),
                "checkpoint_exists": checkpoint_path.exists(),
            }
        )
    return rows


def proxy_template_for_candidate(candidate: Mapping[str, Any]) -> str:
    source_kind = _field(candidate, "source_kind").lower()
    intent = _field(candidate, "comparison_support_intent").lower()
    text = f"{source_kind}|{intent}"
    if "actuator_delay" in text:
        return "t4_actuator_delay_response"
    if "boundary" in text or "near_zero_margin" in text:
        return "t5_boundary_axis_retarget"
    if intent == "collision_relief_probe":
        return "t5_near_boundary_warmup"
    if intent == "discriminative_boundary":
        return "t5_near_boundary_warmup"
    return "t4_staged_warmup_capability"


def reveal_step_for_candidate(candidate: Mapping[str, Any], index: int) -> int:
    base = {
        "early": 72,
        "medium": 96,
        "late": 120,
    }.get(_field(candidate, "obstacle_timing_band"), 96)
    return int(base + 4 * (int(index) % 5))


def _track_width_for_band(value: str) -> float:
    return {
        "generous": 8.0,
        "nominal": 6.0,
        "tight": 4.5,
    }.get(value, 6.0)


def _speed_range_for_band(value: str) -> tuple[float, float]:
    return {
        "low": (6.0, 10.0),
        "nominal": (8.0, 14.0),
        "high": (12.0, 18.0),
    }.get(value, (8.0, 14.0))


def _with_candidate_bands(env_config: Any, candidate: Mapping[str, Any]) -> Any:
    randomization = env_config.randomization
    dynamics_band = _field(candidate, "dynamics_band")
    if dynamics_band == "nominal_mu":
        randomization = replace(
            randomization,
            mu_range=(0.75, 1.05),
            brake_scale_range=(0.85, 1.15),
            drive_scale_range=(0.85, 1.15),
            tire_stiffness_scale_range=(0.85, 1.15),
            actuator_tau_scale_range=(0.90, 1.60),
        )
    elif dynamics_band == "mixed_mu":
        randomization = replace(randomization, mu_range=(0.45, 1.05))
    elif dynamics_band == "low_mu":
        randomization = replace(randomization, mu_range=(0.28, 0.65))
    elif dynamics_band == "actuator_delay":
        randomization = replace(randomization, actuator_tau_scale_range=(1.50, 4.20))

    return replace(
        env_config,
        track_width=_track_width_for_band(_field(candidate, "road_width_band")),
        speed_range=_speed_range_for_band(_field(candidate, "initial_speed_band")),
        randomization=randomization,
    )


def contract_checks(env_config: Any) -> dict[str, bool]:
    return {
        "history_length_is_positive": int(env_config.history_length) >= 1,
        "action_history_mode_full": env_config.action_history_mode == "full",
        "include_privileged_params_false": not bool(env_config.include_privileged_params),
        "wheel_observation_mode_none": env_config.wheel_observation_mode == "none",
        "obstacle_relative_velocity_mode_zero": env_config.obstacle_relative_velocity_mode == "zero",
    }


def load_candidates(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("candidates", []) if isinstance(payload, Mapping) else []
    return [dict(row) for row in rows]


def materialize_executable_specs(candidates: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        candidate_id = _field(candidate, "candidate_id", f"candidate-{index:04d}")
        intent = _field(candidate, "comparison_support_intent")
        try:
            proxy_template = proxy_template_for_candidate(candidate)
            reveal_step = reveal_step_for_candidate(candidate, index)
            capability_pair = "comparison_support_proxy"
            env_config = env_config_for_hook_spec(
                source_family=proxy_template,
                capability_pair=capability_pair,
                reveal_step=reveal_step,
            )
            env_config = _with_candidate_bands(env_config, candidate)
            assert_human_view_env_contract(env_config)
            checks = contract_checks(env_config)
            contract_violation_count = sum(1 for value in checks.values() if not bool(value))
            if _is_true(candidate.get("paper_validity_claim", False)):
                raise ValueError("candidate paper_validity_claim must remain false")
            if _is_true(candidate.get("profile_specific_tuning", False)):
                raise ValueError("profile_specific_tuning must remain false")
            specs.append(
                {
                    "task_source_id": f"m2118-cs-{candidate_id}",
                    "panel_source_id": candidate_id,
                    "candidate_id": candidate_id,
                    "candidate_set_id": _field(candidate, "candidate_set_id"),
                    "scenario_redesign_branch": _field(candidate, "scenario_redesign_branch"),
                    "comparison_support_intent": intent,
                    "target_support_tier": _field(candidate, "target_support_tier"),
                    "panel_task_family": _field(candidate, "source_family"),
                    "source_origin": "m2115_comparison_support_candidate_generation",
                    "source_kind": _field(candidate, "source_kind"),
                    "source_edge": _field(candidate, "difficulty_axis"),
                    "window_tag": intent,
                    "source_role_semantics": _field(candidate, "target_support_tier"),
                    "source_reference": candidate_id,
                    "dynamics_band": _field(candidate, "dynamics_band"),
                    "obstacle_timing_band": _field(candidate, "obstacle_timing_band"),
                    "road_width_band": _field(candidate, "road_width_band"),
                    "initial_speed_band": _field(candidate, "initial_speed_band"),
                    "materialization_semantics": _field(candidate, "materialization_semantics"),
                    "proxy_template_family": proxy_template,
                    "reveal_step": reveal_step,
                    "capability_pair": capability_pair,
                    "actor_input_contract": _field(candidate, "actor_input_contract"),
                    "generated_source_row": True,
                    "paper_validity_claim": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                    "contract_checks": checks,
                    "contract_violation_count": contract_violation_count,
                    "env_config": env_config_to_dict(env_config),
                }
            )
        except Exception as exc:  # pragma: no cover - fail-closed path for real candidate artifacts.
            failures.append(
                {
                    "candidate_id": candidate_id,
                    "comparison_support_intent": intent,
                    "failure_type": type(exc).__name__,
                    "reason": str(exc),
                }
            )
    return specs, failures


def executable_spec_csv_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        checks = dict(spec.get("contract_checks", {}))
        rows.append(
            {
                **{field: spec.get(field, "") for field in SPEC_FIELDNAMES if field not in checks},
                **checks,
            }
        )
    return rows


def planned_workload_rows(
    executable_specs: list[Mapping[str, Any]],
    *,
    profile_run_dir: Path | str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profiles = _profile_artifact_rows(profile_run_dir=profile_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in executable_specs:
        for profile in profiles:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "panel_source_id": spec["panel_source_id"],
                    "candidate_id": spec["candidate_id"],
                    "candidate_set_id": spec["candidate_set_id"],
                    "scenario_redesign_branch": spec["scenario_redesign_branch"],
                    "comparison_support_intent": spec["comparison_support_intent"],
                    "target_support_tier": spec["target_support_tier"],
                    "panel_task_family": spec["panel_task_family"],
                    "profile_name": profile["profile_name"],
                    "profile_config_path": profile["config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "source_origin": spec["source_origin"],
                    "source_kind": spec["source_kind"],
                    "source_edge": spec["source_edge"],
                    "window_tag": spec["window_tag"],
                    "source_role_semantics": spec["source_role_semantics"],
                    "source_reference": spec["source_reference"],
                    "dynamics_band": spec["dynamics_band"],
                    "obstacle_timing_band": spec["obstacle_timing_band"],
                    "road_width_band": spec["road_width_band"],
                    "initial_speed_band": spec["initial_speed_band"],
                    "materialization_semantics": spec["materialization_semantics"],
                    "proxy_template_family": spec["proxy_template_family"],
                    "generated_source_row": spec["generated_source_row"],
                    "paper_validity_claim": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return rows, profiles


def _duplicate_count(values: Iterable[str]) -> int:
    counts = Counter(str(value) for value in values)
    return sum(1 for count in counts.values() if count > 1)


def _count_true(rows: Iterable[Mapping[str, Any]], field: str) -> int:
    return sum(1 for row in rows if _is_true(row.get(field, False)))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    return [{"key": key_value, "count": count} for key_value, count in sorted(Counter(str(row[key]) for row in rows).items())]


def _claim_boundary_rows(pass_conditions: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "comparison_support_materialization_preflight_completed",
            "admissible": pass_conditions,
            "reason": "M2118 writes reset-free executable spec and workload artifacts when all preflight gates pass",
        },
        {
            "claim": "reset_validity",
            "admissible": False,
            "reason": "M2118 does not run environment reset",
        },
        {
            "claim": "measured_execution_or_profile_comparison",
            "admissible": False,
            "reason": "M2118 does not execute policy actions or compare outcomes",
        },
        {
            "claim": "paper_valid_task_semantics",
            "admissible": False,
            "reason": "comparison-support candidates are smoke-proxy tasks until later validation",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2118 materializes a panel only",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2118 does not run history intervention outcome tests",
        },
    ]


def run_materialization_preflight(
    *,
    candidates_path: Path | str = DEFAULT_CANDIDATES,
    profile_run_dir: Path | str = DEFAULT_PROFILE_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidates = load_candidates(candidates_path)
    executable_specs, materialization_failures = materialize_executable_specs(candidates)
    workload_rows, profile_rows = planned_workload_rows(executable_specs, profile_run_dir=profile_run_dir)

    profile_count = len(profile_rows)
    missing_profile_artifact_count = sum(1 for row in profile_rows if not (row["config_exists"] and row["checkpoint_exists"]))
    duplicate_task_source_id_count = _duplicate_count(str(row["task_source_id"]) for row in executable_specs)
    duplicate_workload_id_count = _duplicate_count(str(row["workload_id"]) for row in workload_rows)
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in executable_specs)
    forbidden_key_violation_rows = forbidden_key_violations(executable_specs)
    paper_validity_claim_true_count = _count_true(executable_specs, "paper_validity_claim") + _count_true(
        workload_rows, "paper_validity_claim"
    )
    profile_specific_tuning_true_count = _count_true(executable_specs, "profile_specific_tuning") + _count_true(
        workload_rows, "profile_specific_tuning"
    )

    guardrail_flags = {
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
        "profile_specific_tuning": profile_specific_tuning_true_count > 0,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)
    pass_conditions = (
        len(candidates) == TARGET_CANDIDATE_COUNT
        and len(executable_specs) == TARGET_CANDIDATE_COUNT
        and len(workload_rows) == TARGET_WORKLOAD_COUNT
        and profile_count == len(PROFILE_SUBSET)
        and len(materialization_failures) == 0
        and missing_profile_artifact_count == 0
        and duplicate_task_source_id_count == 0
        and duplicate_workload_id_count == 0
        and contract_violation_count == 0
        and not forbidden_key_violation_rows
        and paper_validity_claim_true_count == 0
        and profile_specific_tuning_true_count == 0
        and guardrail_violation_count == 0
    )
    if pass_conditions:
        result_class = "comparison_support_materialization_preflight_pass"
    elif executable_specs or workload_rows:
        result_class = "comparison_support_materialization_preflight_partial"
    else:
        result_class = "comparison_support_materialization_preflight_fail_closed"

    artifacts = {
        "summary": output / "summary.json",
        "executable_task_specs_json": output / "executable_task_specs.json",
        "executable_task_specs_csv": output / "executable_task_specs.csv",
        "planned_workload": output / "planned_workload.csv",
        "profile_artifacts": output / "profile_artifacts.csv",
        "materialization_failures": output / "materialization_failures.csv",
        "aggregate_by_intent": output / "aggregate_by_intent.csv",
        "aggregate_by_proxy_template_family": output / "aggregate_by_proxy_template_family.csv",
        "claim_boundary": output / "claim_boundary.csv",
    }
    write_json(
        artifacts["executable_task_specs_json"],
        {
            "protocol": PROTOCOL_NAME,
            "executable_task_specs": executable_specs,
        },
    )
    write_csv_rows(artifacts["executable_task_specs_csv"], executable_spec_csv_rows(executable_specs), SPEC_FIELDNAMES)
    write_csv_rows(artifacts["planned_workload"], workload_rows, WORKLOAD_FIELDNAMES)
    write_csv_rows(artifacts["profile_artifacts"], profile_rows, PROFILE_FIELDNAMES)
    write_csv_rows(artifacts["materialization_failures"], materialization_failures, FAILURE_FIELDNAMES)
    write_csv_rows(artifacts["aggregate_by_intent"], _count_by(executable_specs, "comparison_support_intent"), AGGREGATE_FIELDNAMES)
    write_csv_rows(
        artifacts["aggregate_by_proxy_template_family"],
        _count_by(executable_specs, "proxy_template_family"),
        AGGREGATE_FIELDNAMES,
    )
    write_csv_rows(artifacts["claim_boundary"], _claim_boundary_rows(pass_conditions), CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "protocol": PROTOCOL_NAME,
        "candidates_path": str(candidates_path),
        "profile_run_dir": str(profile_run_dir),
        "candidate_count": len(candidates),
        "target_candidate_count": TARGET_CANDIDATE_COUNT,
        "executable_spec_count": len(executable_specs),
        "target_executable_spec_count": TARGET_CANDIDATE_COUNT,
        "workload_row_count": len(workload_rows),
        "target_workload_row_count": TARGET_WORKLOAD_COUNT,
        "profile_count": profile_count,
        "target_profile_count": len(PROFILE_SUBSET),
        "profile_names": list(PROFILE_SUBSET),
        "materialization_failure_count": len(materialization_failures),
        "missing_profile_artifact_count": missing_profile_artifact_count,
        "duplicate_task_source_id_count": duplicate_task_source_id_count,
        "duplicate_workload_id_count": duplicate_workload_id_count,
        "contract_violation_count": contract_violation_count,
        "forbidden_key_violation_count": len(forbidden_key_violation_rows),
        "forbidden_key_violation_rows": forbidden_key_violation_rows,
        "paper_validity_claim_true_count": paper_validity_claim_true_count,
        "profile_specific_tuning_true_count": profile_specific_tuning_true_count,
        "intent_counts": dict(sorted(Counter(str(row["comparison_support_intent"]) for row in executable_specs).items())),
        "proxy_template_family_counts": dict(sorted(Counter(str(row["proxy_template_family"]) for row in executable_specs).items())),
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
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "next_blocker": str(next_blocker),
    }
    write_json(artifacts["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--profile-run-dir", type=Path, default=DEFAULT_PROFILE_RUN_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_materialization_preflight(
        candidates_path=args.candidates,
        output_dir=args.output_dir,
        profile_run_dir=args.profile_run_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"executable_spec_count={summary['executable_spec_count']}")
    print(f"workload_row_count={summary['workload_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
