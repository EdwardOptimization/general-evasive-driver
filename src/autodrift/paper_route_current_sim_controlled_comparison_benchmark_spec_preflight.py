"""No-rollout current-sim controlled comparison benchmark spec preflight."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.controller_profile_runtime import profile_runtime_summary


DEFAULT_PROFILE_CONFIGS = (
    Path("configs/paper_route_profiles/m1190_l0_current_masked_smoke.json"),
    Path("configs/paper_route_profiles/m1190_l1_one_step_smoke.json"),
    Path("configs/paper_route_profiles/m1190_l2_window_13_smoke.json"),
    Path("configs/paper_route_profiles/m1190_l2_window_25_smoke.json"),
    Path("configs/paper_route_profiles/m1190_l2_window_50_smoke.json"),
    Path("configs/paper_route_profiles/m1190_l2_window_100_smoke.json"),
    Path("configs/paper_route_profiles/m1190_l3_online_gru_smoke.json"),
    Path("configs/paper_route_profiles/m1190_l3_reset_control_smoke.json"),
)
DEFAULT_CONFIG_OUTPUT = Path("configs/paper_route_current_sim_controlled_comparison_benchmark_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight")
DEFAULT_NEXT_BLOCKER = "m2149-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-audit"

PROFILE_ORDER = (
    "L0_current_masked",
    "L1_one_step",
    "L2_window_13",
    "L2_window_25",
    "L2_window_50",
    "L2_window_100",
    "L3_online_gru",
    "L3_reset_control",
)
TASK_FAMILY_SPECS = (
    {
        "task_family": "T1_reactive_emergency_avoidance",
        "claim_level_target": "Claim_A_deployable_feedback_driver",
        "scenario_source": "current_sim_benchmark_contract",
        "source_kind": "reactive_avoidance",
        "difficulty_band": "ordinary_to_near_boundary",
        "dynamics_band": "randomized_hidden_dynamics",
        "obstacle_timing_band": "immediate_or_short_notice",
        "road_geometry_band": "current_sim_road_geometry",
        "history_requirement": "current_response_expected_strong",
        "primary_metrics": "success_rate;collision_rate;road_departure_rate;clearance_margin_tail;control_smoothness",
        "mechanism_metrics": "none_primary_engineering_family",
    },
    {
        "task_family": "T2_delayed_actuator_response",
        "claim_level_target": "Claim_B_history_conditioned_output_feedback",
        "scenario_source": "current_sim_benchmark_contract",
        "source_kind": "delayed_response",
        "difficulty_band": "delayed_or_weak_response",
        "dynamics_band": "actuator_delay_and_hidden_dynamics",
        "obstacle_timing_band": "short_to_medium_notice",
        "road_geometry_band": "current_sim_road_geometry",
        "history_requirement": "multi_step_command_response_may_help",
        "primary_metrics": "success_rate;collision_rate;road_departure_rate;terminal_margin_tail",
        "mechanism_metrics": "adaptation_latency;first_critical_action_gap",
    },
    {
        "task_family": "T3_diagnostic_warmup_obstacle_reveal",
        "claim_level_target": "Claim_B_or_C_history_value",
        "scenario_source": "current_sim_benchmark_contract",
        "source_kind": "diagnostic_warmup",
        "difficulty_band": "warmup_then_reveal",
        "dynamics_band": "hidden_dynamics_randomized_before_reveal",
        "obstacle_timing_band": "late_reveal_after_warmup",
        "road_geometry_band": "current_sim_road_geometry",
        "history_requirement": "warmup_response_history_available",
        "primary_metrics": "success_rate;collision_rate;recovery_after_maneuver;terminal_margin_tail",
        "mechanism_metrics": "future_braking_authority_prediction;future_yaw_authority_prediction;adaptation_latency",
    },
    {
        "task_family": "T4_same_current_different_older_history",
        "claim_level_target": "Claim_C_recurrent_belief_advantage",
        "scenario_source": "current_sim_benchmark_contract",
        "source_kind": "same_current_older_history",
        "difficulty_band": "matched_current_different_history",
        "dynamics_band": "history_ambiguous_hidden_dynamics",
        "obstacle_timing_band": "decision_after_alignment",
        "road_geometry_band": "current_sim_road_geometry",
        "history_requirement": "older_history_must_matter_beyond_recent_window",
        "primary_metrics": "terminal_margin_tail;first_critical_action_gap;short_horizon_maneuver_gap",
        "mechanism_metrics": "wrong_history_margin_gap;delayed_history_margin_gap;source_diversity;max_single_source_share",
    },
    {
        "task_family": "T5_terminal_boundary_near_constraint",
        "claim_level_target": "Claim_D_strong_self_identification",
        "scenario_source": "current_sim_benchmark_contract",
        "source_kind": "terminal_boundary",
        "difficulty_band": "near_constraint",
        "dynamics_band": "hidden_dynamics_terminal_boundary",
        "obstacle_timing_band": "critical_decision_window",
        "road_geometry_band": "current_sim_road_geometry",
        "history_requirement": "history_intervention_must_change_outcome",
        "primary_metrics": "terminal_margin_tail;collision_rate;road_departure_rate;recovery_after_maneuver",
        "mechanism_metrics": "wrong_history_margin_gap;reset_or_truncated_history_margin_gap;source_diversity;max_single_source_share",
    },
)
METRIC_SUPPORT_ROWS = (
    ("success_rate", True, "episode outcome rows can support this after measured execution"),
    ("collision_rate", True, "episode outcome rows can support this after measured execution"),
    ("road_departure_rate", True, "offtrack outcome rows can support this after measured execution"),
    ("spin_rate", False, "requires explicit spin metric support or terminal reason audit before paper use"),
    ("clearance_margin_tail", True, "min_clearance_margin rows can support tails after measured execution"),
    ("terminal_margin_tail", False, "requires terminal-margin logging or explicit mapping before paper use"),
    ("recovery_after_maneuver", True, "M1746 instrumentation adds recovery hooks; still requires measured audit"),
    ("control_smoothness", True, "action-rate metrics can support this after measured execution"),
    ("first_critical_action_gap", False, "requires teacher/local target or paired-action artifact"),
    ("short_horizon_maneuver_gap", False, "requires trajectory-intent or short-horizon target artifact"),
    ("future_braking_authority_prediction", False, "requires auxiliary probe or authority-label artifact"),
    ("future_yaw_authority_prediction", False, "requires auxiliary probe or authority-label artifact"),
    ("adaptation_latency", False, "requires timed response/intervention instrumentation"),
    ("wrong_history_margin_gap", False, "requires wrong-history intervention execution"),
    ("delayed_history_margin_gap", False, "requires delayed-history intervention execution"),
    ("reset_or_truncated_history_margin_gap", False, "requires reset/truncation intervention execution"),
    ("source_diversity", True, "source metadata can support this after spec materialization and measured execution"),
    ("max_single_source_share", True, "source metadata can support this after spec materialization and measured execution"),
)
CLAIM_BOUNDARY_ROWS = (
    (
        "current_sim_controlled_comparison_benchmark_spec_preflight_completed",
        True,
        "M2148 writes no-rollout benchmark contract artifacts only",
    ),
    ("controller_family_ranking", False, "preflight does not execute or rank controllers"),
    ("winner_selection", False, "preflight does not choose a winning profile"),
    ("finite_window_vs_gru_conclusion", False, "preflight defines controls but does not execute comparison"),
    ("paper_level_benchmark_result", False, "preflight is not measured evidence"),
    ("level3_self_identification", False, "preflight does not run history interventions"),
)
FORBIDDEN_PROFILE_FLAGS = (
    "uses_hidden_oracle_actor_inputs",
    "uses_wheel_or_slip_inputs",
    "uses_reference_or_ttc_inputs",
)
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
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
PROFILE_MATRIX_FIELDNAMES = [
    "profile_name",
    "profile_level",
    "history_representation",
    "history_window_steps",
    "history_window_seconds",
    "uses_recurrent_state",
    "uses_finite_window",
    "reset_or_truncated_control",
    "observation_dim",
    "action_contract",
    "input_contract",
    "actor_encoder",
    "env_history_length",
    "observation_mask",
    "history_transform",
    "reset_hidden_policy",
    "profile_specific_tuning",
    "forbidden_actor_input_violation",
]
TASK_FIELDNAMES = [
    "benchmark_spec_id",
    "task_family",
    "claim_level_target",
    "scenario_source",
    "source_kind",
    "difficulty_band",
    "dynamics_band",
    "obstacle_timing_band",
    "road_geometry_band",
    "history_requirement",
    "primary_metrics",
    "mechanism_metrics",
    "paper_validity_status",
    "generated_proxy_source",
    "profile_specific_tuning",
    "forbidden_actor_input_flags",
    "reset_validation_required",
    "measured_execution_required",
    "private_holdout_policy",
]
METRIC_FIELDNAMES = ["metric", "supported_after_measured_execution", "support_status", "reason"]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _profile_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    name = str(row.get("profile_name", ""))
    try:
        return (PROFILE_ORDER.index(name), name)
    except ValueError:
        return (len(PROFILE_ORDER), name)


def _history_representation(profile: dict[str, Any]) -> str:
    if bool(profile.get("uses_recurrent_hidden")):
        return "online_recurrent_hidden"
    if bool(profile.get("uses_finite_window")):
        return "explicit_finite_window"
    if str(profile.get("history_baseline_level", "")).startswith("L1"):
        return "one_step_command_response"
    return "current_response"


def _is_reset_or_truncated(profile: dict[str, Any]) -> bool:
    policy = str(profile.get("reset_hidden_policy", ""))
    return bool(profile.get("uses_recurrent_hidden", False)) and (
        "reset" in str(profile.get("name", "")).lower()
        or policy
        not in {
            "episode_persistent",
            "not_applicable",
            "",
        }
    )


def _profile_row(path: Path | str) -> dict[str, Any]:
    config = read_json(path)
    profile = dict(config.get("controller_profile", {}))
    runtime = profile_runtime_summary(config)
    forbidden_violation = any(bool(profile.get(flag, False)) for flag in FORBIDDEN_PROFILE_FLAGS)
    return {
        "profile_name": str(profile.get("name", "")),
        "profile_level": str(profile.get("level", profile.get("history_baseline_level", ""))),
        "history_representation": _history_representation(profile),
        "history_window_steps": int(profile.get("window_steps", profile.get("actor_history_length", 0))),
        "history_window_seconds": float(profile.get("window_seconds", 0.0)),
        "uses_recurrent_state": bool(profile.get("uses_recurrent_hidden", False)),
        "uses_finite_window": bool(profile.get("uses_finite_window", False)),
        "reset_or_truncated_control": _is_reset_or_truncated(profile),
        "observation_dim": int(profile.get("observation_dim", 0)),
        "action_contract": "steer_throttle_brake",
        "input_contract": str(profile.get("input_contract", "")),
        "actor_encoder": str(profile.get("actor_encoder", "")),
        "env_history_length": int(profile.get("env_history_length", config.get("env", {}).get("history_length", 0))),
        "observation_mask": str(runtime.get("observation_mask", profile.get("observation_mask", ""))),
        "history_transform": str(runtime.get("history_transform", "none")),
        "reset_hidden_policy": str(runtime.get("reset_hidden_policy", profile.get("reset_hidden_policy", ""))),
        "profile_specific_tuning": False,
        "forbidden_actor_input_violation": forbidden_violation,
    }


def _task_rows() -> list[dict[str, Any]]:
    rows = []
    for index, spec in enumerate(TASK_FAMILY_SPECS, start=1):
        rows.append(
            {
                "benchmark_spec_id": f"current_sim_benchmark_v0_t{index}",
                **spec,
                "paper_validity_status": "current_sim_benchmark_candidate_not_executed",
                "generated_proxy_source": False,
                "profile_specific_tuning": False,
                "forbidden_actor_input_flags": "none",
                "reset_validation_required": True,
                "measured_execution_required": True,
                "private_holdout_policy": "promotion_only_after_public_audit",
            }
        )
    return rows


def _metric_rows() -> list[dict[str, Any]]:
    rows = []
    for metric, supported, reason in METRIC_SUPPORT_ROWS:
        rows.append(
            {
                "metric": metric,
                "supported_after_measured_execution": bool(supported),
                "support_status": "supported_after_measured_audit" if supported else "deferred_explicit_gap",
                "reason": reason,
            }
        )
    return rows


def _claim_rows() -> list[dict[str, Any]]:
    return [{"claim": claim, "admissible": admissible, "reason": reason} for claim, admissible, reason in CLAIM_BOUNDARY_ROWS]


def materialize_spec_preflight(
    *,
    profile_config_paths: list[Path] | tuple[Path, ...] = DEFAULT_PROFILE_CONFIGS,
    config_output_path: Path | str = DEFAULT_CONFIG_OUTPUT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    config_output = Path(config_output_path)

    profile_rows = sorted([_profile_row(path) for path in profile_config_paths], key=_profile_sort_key)
    task_rows = _task_rows()
    metric_rows = _metric_rows()
    claim_rows = _claim_rows()

    profile_names = [str(row["profile_name"]) for row in profile_rows]
    missing_profiles = [profile for profile in PROFILE_ORDER if profile not in profile_names]
    extra_profiles = [profile for profile in profile_names if profile not in PROFILE_ORDER]
    task_families = [str(row["task_family"]) for row in task_rows]
    unsupported_metric_gap_count = sum(1 for row in metric_rows if not bool(row["supported_after_measured_execution"]))
    forbidden_profile_violation_count = sum(1 for row in profile_rows if bool(row["forbidden_actor_input_violation"]))
    profile_specific_tuning_count = sum(1 for row in profile_rows + task_rows if bool(row["profile_specific_tuning"]))

    guardrail_flags = {flag: False for flag in FORBIDDEN_GUARDRAILS}
    guardrail_flags["profile_specific_tuning"] = bool(profile_specific_tuning_count)
    guardrail_flags["actor_input_contract_changed"] = bool(forbidden_profile_violation_count)
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))

    result_class = (
        "current_sim_controlled_comparison_benchmark_spec_preflight_pass"
        if not missing_profiles and not extra_profiles and len(task_rows) == 5 and guardrail_violation_count == 0
        else "current_sim_controlled_comparison_benchmark_spec_preflight_fail"
    )

    benchmark_config = {
        "benchmark_id": "paper_route_current_sim_controlled_comparison_benchmark_v0",
        "generated_at_utc": utc_timestamp(),
        "source_milestone": "m2148-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-implementation",
        "profile_order": list(PROFILE_ORDER),
        "task_families": task_rows,
        "profile_matrix": profile_rows,
        "metric_support": metric_rows,
        "claim_boundary": claim_rows,
        "guardrails": guardrail_flags,
        "claim_scope": "no_rollout_benchmark_spec_preflight_only",
    }
    write_json(config_output, benchmark_config)
    write_csv_rows(output / "profile_matrix.csv", profile_rows, fieldnames=PROFILE_MATRIX_FIELDNAMES)
    write_csv_rows(output / "task_family_specs.csv", task_rows, fieldnames=TASK_FIELDNAMES)
    write_csv_rows(output / "metric_support.csv", metric_rows, fieldnames=METRIC_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "profile_count": len(profile_rows),
        "expected_profile_count": len(PROFILE_ORDER),
        "missing_profile_count": len(missing_profiles),
        "missing_profiles": missing_profiles,
        "extra_profile_count": len(extra_profiles),
        "extra_profiles": extra_profiles,
        "task_family_count": len(task_rows),
        "task_families": task_families,
        "metric_count": len(metric_rows),
        "unsupported_metric_gap_count": unsupported_metric_gap_count,
        "claim_boundary_row_count": len(claim_rows),
        "forbidden_profile_violation_count": forbidden_profile_violation_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "reset_validation_started": False,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "required_files_written": True,
        "config_output_path": str(config_output),
        "artifacts": {
            "summary": str(output / "summary.json"),
            "profile_matrix": str(output / "profile_matrix.csv"),
            "task_family_specs": str(output / "task_family_specs.csv"),
            "metric_support": str(output / "metric_support.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
            "benchmark_config": str(config_output),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2148-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-implementation",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile-config",
        action="append",
        dest="profile_configs",
        default=None,
        help="Profile config path. Repeat to override the default 8-profile matrix.",
    )
    parser.add_argument("--config-output", type=Path, default=DEFAULT_CONFIG_OUTPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    profile_paths = [Path(path) for path in args.profile_configs] if args.profile_configs else list(DEFAULT_PROFILE_CONFIGS)
    summary = materialize_spec_preflight(
        profile_config_paths=profile_paths,
        config_output_path=args.config_output,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
