"""No-rollout executable spec materialization for the current-sim comparison benchmark."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec


DEFAULT_BENCHMARK_CONFIG = Path("configs/paper_route_current_sim_controlled_comparison_benchmark_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization")
DEFAULT_NEXT_BLOCKER = "m2152-paper-route-current-sim-controlled-comparison-executable-spec-materialization-audit"
DEFAULT_PROFILE_CONFIGS = {
    "L0_current_masked": "configs/paper_route_profiles/m1190_l0_current_masked_smoke.json",
    "L1_one_step": "configs/paper_route_profiles/m1190_l1_one_step_smoke.json",
    "L2_window_13": "configs/paper_route_profiles/m1190_l2_window_13_smoke.json",
    "L2_window_25": "configs/paper_route_profiles/m1190_l2_window_25_smoke.json",
    "L2_window_50": "configs/paper_route_profiles/m1190_l2_window_50_smoke.json",
    "L2_window_100": "configs/paper_route_profiles/m1190_l2_window_100_smoke.json",
    "L3_online_gru": "configs/paper_route_profiles/m1190_l3_online_gru_smoke.json",
    "L3_reset_control": "configs/paper_route_profiles/m1190_l3_reset_control_smoke.json",
}
SPECS_PER_FAMILY = 8
TASK_FAMILY_ORDER = (
    "T1_reactive_emergency_avoidance",
    "T2_delayed_actuator_response",
    "T3_diagnostic_warmup_obstacle_reveal",
    "T4_same_current_different_older_history",
    "T5_terminal_boundary_near_constraint",
)
TASK_FAMILY_TEMPLATE = {
    "T1_reactive_emergency_avoidance": ("t5_boundary_axis_retarget", "reactive_current_response", 24),
    "T2_delayed_actuator_response": ("t4_actuator_delay_response", "delayed_actuator_response", 72),
    "T3_diagnostic_warmup_obstacle_reveal": ("t4_staged_warmup_capability", "diagnostic_warmup", 112),
    "T4_same_current_different_older_history": ("t4_capability_step_temporal", "older_history_ambiguity", 120),
    "T5_terminal_boundary_near_constraint": ("t5_high_speed_close_obstacle", "terminal_boundary", 52),
}
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
SPEC_FIELDNAMES = [
    "task_source_id",
    "benchmark_spec_id",
    "task_family",
    "claim_level_target",
    "scenario_source",
    "source_kind",
    "source_reference",
    "source_index",
    "source_seed",
    "eval_seed_override",
    "materialization_semantics",
    "paper_validity_status",
    "generated_proxy_source",
    "profile_specific_tuning",
    "actor_input_contract",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "metric_gap_policy",
    "source_family_template",
    "capability_pair",
    "reveal_step",
    "contract_violation_count",
    "history_length_is_positive",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "obstacle_enabled",
    "obstacle_max_sample_attempts_at_least_200",
]
WORKLOAD_FIELDNAMES = [
    "workload_id",
    "task_source_id",
    "benchmark_spec_id",
    "profile_name",
    "profile_level",
    "profile_config_path",
    "checkpoint_path",
    "checkpoint_required_for_measured_execution",
    "task_family",
    "history_representation",
    "history_window_steps",
    "reset_or_truncated_control",
    "environment_reset_scheduled",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
PROFILE_FIELDNAMES = [
    "profile_name",
    "profile_level",
    "history_representation",
    "history_window_steps",
    "reset_or_truncated_control",
    "profile_config_path",
    "profile_config_exists",
    "input_contract",
    "action_contract",
    "profile_specific_tuning",
    "forbidden_actor_input_violation",
]
FAILURE_FIELDNAMES = ["item_id", "item_type", "failure_type", "reason"]
AGGREGATE_FIELDNAMES = ["key", "count"]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _contract_checks(env_config: Any) -> dict[str, bool]:
    obstacle = env_config.obstacle
    return {
        "history_length_is_positive": int(env_config.history_length) >= 1,
        "action_history_mode_full": env_config.action_history_mode == "full",
        "include_privileged_params_false": not bool(env_config.include_privileged_params),
        "wheel_observation_mode_none": env_config.wheel_observation_mode == "none",
        "obstacle_relative_velocity_mode_zero": env_config.obstacle_relative_velocity_mode == "zero",
        "obstacle_enabled": bool(obstacle.enabled),
        "obstacle_max_sample_attempts_at_least_200": int(obstacle.max_sample_attempts) >= 200,
    }


def _reveal_step(task_family: str, source_index: int) -> int:
    _, _, base = TASK_FAMILY_TEMPLATE[task_family]
    return int(base + 4 * (int(source_index) % 4))


def _task_family_index(task_family: str) -> int:
    return TASK_FAMILY_ORDER.index(task_family)


def _source_seed(task_family: str, source_index: int) -> int:
    return 215100 + 100 * _task_family_index(task_family) + int(source_index)


def _eval_seed(task_family: str, source_index: int) -> int:
    return 215100 + 1000 * _task_family_index(task_family) + int(source_index)


def _profile_matrix_rows(benchmark_config: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in benchmark_config.get("profile_matrix", []):
        profile_name = str(row.get("profile_name", ""))
        config_path = DEFAULT_PROFILE_CONFIGS.get(profile_name, "")
        rows.append(
            {
                "profile_name": profile_name,
                "profile_level": str(row.get("profile_level", "")),
                "history_representation": str(row.get("history_representation", "")),
                "history_window_steps": int(row.get("history_window_steps", 0)),
                "reset_or_truncated_control": _bool(row.get("reset_or_truncated_control")),
                "profile_config_path": config_path,
                "profile_config_exists": Path(config_path).exists() if config_path else False,
                "input_contract": str(row.get("input_contract", "")),
                "action_contract": str(row.get("action_contract", "")),
                "profile_specific_tuning": _bool(row.get("profile_specific_tuning")),
                "forbidden_actor_input_violation": _bool(row.get("forbidden_actor_input_violation")),
            }
        )
    return rows


def _task_contract_rows(benchmark_config: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_family = {str(row.get("task_family")): dict(row) for row in benchmark_config.get("task_families", [])}
    return [by_family[family] for family in TASK_FAMILY_ORDER if family in by_family]


def _spec_rows(task_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for task_row in task_rows:
        task_family = str(task_row.get("task_family", ""))
        if task_family not in TASK_FAMILY_TEMPLATE:
            failures.append(
                {
                    "item_id": task_family,
                    "item_type": "task_family",
                    "failure_type": "unknown_task_family",
                    "reason": "no executable template mapping exists",
                }
            )
            continue
        source_family_template, capability_pair, _ = TASK_FAMILY_TEMPLATE[task_family]
        family_index = _task_family_index(task_family)
        for source_index in range(SPECS_PER_FAMILY):
            reveal_step = _reveal_step(task_family, source_index)
            env_config = env_config_for_hook_spec(
                source_family=source_family_template,
                capability_pair=capability_pair,
                reveal_step=reveal_step,
            )
            checks = _contract_checks(env_config)
            contract_violation_count = sum(1 for value in checks.values() if not bool(value))
            task_source_id = f"m2151-current-sim-t{family_index + 1}-{source_index:02d}"
            try:
                assert_human_view_env_contract(env_config)
            except Exception as exc:  # pragma: no cover - defensive failure artifact
                contract_violation_count += 1
                failures.append(
                    {
                        "item_id": task_source_id,
                        "item_type": "executable_spec",
                        "failure_type": type(exc).__name__,
                        "reason": str(exc),
                    }
                )
            rows.append(
                {
                    "task_source_id": task_source_id,
                    "benchmark_spec_id": str(task_row.get("benchmark_spec_id", "")),
                    "task_family": task_family,
                    "claim_level_target": str(task_row.get("claim_level_target", "")),
                    "scenario_source": "current_sim_executable_materialization_v0",
                    "source_kind": str(task_row.get("source_kind", "")),
                    "source_reference": f"{task_family}:{source_index}",
                    "source_index": source_index,
                    "source_seed": _source_seed(task_family, source_index),
                    "eval_seed_override": _eval_seed(task_family, source_index),
                    "materialization_semantics": "current_sim_executable_spec_v0",
                    "paper_validity_status": "current_sim_executable_candidate_not_reset_validated",
                    "generated_proxy_source": False,
                    "profile_specific_tuning": False,
                    "actor_input_contract": "P0_human_view_no_wheel_no_oracle",
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                    "metric_gap_policy": "preserve_explicit_deferred_gaps",
                    "source_family_template": source_family_template,
                    "capability_pair": capability_pair,
                    "reveal_step": reveal_step,
                    "env_config": env_config_to_dict(env_config),
                    "contract_checks": checks,
                    "contract_violation_count": contract_violation_count,
                    **checks,
                }
            )
    return rows, failures


def _workload_rows(spec_rows: list[dict[str, Any]], profile_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        for profile in profile_rows:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "benchmark_spec_id": spec["benchmark_spec_id"],
                    "profile_name": profile["profile_name"],
                    "profile_level": profile["profile_level"],
                    "profile_config_path": profile["profile_config_path"],
                    "checkpoint_path": "",
                    "checkpoint_required_for_measured_execution": True,
                    "task_family": spec["task_family"],
                    "history_representation": profile["history_representation"],
                    "history_window_steps": profile["history_window_steps"],
                    "reset_or_truncated_control": profile["reset_or_truncated_control"],
                    "environment_reset_scheduled": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return rows


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "current_sim_controlled_comparison_executable_spec_materialized",
            "admissible": True,
            "reason": "M2151 writes no-rollout executable specs and planned workload rows only",
        },
        {"claim": "reset_validity", "admissible": False, "reason": "M2151 does not run environment reset"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "M2151 does not execute or compare controllers"},
        {"claim": "winner_selection", "admissible": False, "reason": "M2151 does not choose a winning profile"},
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2151 materializes comparison inputs but does not execute comparison",
        },
        {"claim": "paper_level_benchmark_result", "admissible": False, "reason": "M2151 is not measured evidence"},
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2151 preserves T4/T5 metadata but does not run history interventions",
        },
    ]


def _aggregate_rows(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts = Counter(str(row.get(key, "")) for row in rows)
    return [{"key": name, "count": count} for name, count in sorted(counts.items())]


def materialize_executable_specs(
    *,
    benchmark_config_path: Path | str = DEFAULT_BENCHMARK_CONFIG,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    benchmark_config = read_json(benchmark_config_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    profile_rows = _profile_matrix_rows(benchmark_config)
    task_rows = _task_contract_rows(benchmark_config)
    spec_rows, failure_rows = _spec_rows(task_rows)
    workload_rows = _workload_rows(spec_rows, profile_rows)
    claim_rows = _claim_boundary_rows()
    metric_rows = list(benchmark_config.get("metric_support", []))

    materialization_failure_count = len(failure_rows)
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in spec_rows)
    forbidden_key_violation_count = sum(
        1
        for row in spec_rows
        if any(
            _bool(row.get(key))
            for key in (
                "generated_proxy_source",
                "profile_specific_tuning",
                "controller_family_ranking_claim_made",
                "finite_window_vs_gru_conclusion_made",
                "paper_level_claim_made",
                "level3_self_id_claim_made",
            )
        )
    )
    profile_specific_tuning_count = sum(1 for row in profile_rows + workload_rows if _bool(row.get("profile_specific_tuning")))
    guardrail_flags = {flag: False for flag in FORBIDDEN_GUARDRAILS}
    guardrail_flags["actor_input_contract_changed"] = bool(contract_violation_count)
    guardrail_flags["profile_specific_tuning"] = bool(profile_specific_tuning_count)
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    task_family_count = len({row["task_family"] for row in spec_rows})
    profile_count = len({row["profile_name"] for row in profile_rows})
    expected_workload_count = len(spec_rows) * len(profile_rows)

    result_class = (
        "current_sim_controlled_comparison_executable_spec_materialization_pass"
        if len(spec_rows) == 40
        and len(workload_rows) == 320
        and task_family_count == 5
        and profile_count == 8
        and materialization_failure_count == 0
        and contract_violation_count == 0
        and forbidden_key_violation_count == 0
        and profile_specific_tuning_count == 0
        and guardrail_violation_count == 0
        else "current_sim_controlled_comparison_executable_spec_materialization_fail"
    )

    specs_payload = {
        "protocol": "paper_route_current_sim_controlled_comparison_executable_spec_materialization_v0",
        "generated_at_utc": utc_timestamp(),
        "benchmark_config_path": str(benchmark_config_path),
        "executable_task_specs": spec_rows,
        "claim_scope": "no_rollout_executable_spec_materialization_only",
    }
    write_json(output / "executable_task_specs.json", specs_payload)
    write_csv_rows(output / "executable_task_specs.csv", spec_rows, fieldnames=SPEC_FIELDNAMES)
    write_csv_rows(output / "planned_workload.csv", workload_rows, fieldnames=WORKLOAD_FIELDNAMES)
    write_csv_rows(output / "profile_matrix.csv", profile_rows, fieldnames=PROFILE_FIELDNAMES)
    write_csv_rows(output / "materialization_failures.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    write_csv_rows(output / "aggregate_by_task_family.csv", _aggregate_rows(spec_rows, "task_family"), fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "metric_support.csv", metric_rows)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "benchmark_config_path": str(benchmark_config_path),
        "executable_spec_count": len(spec_rows),
        "expected_executable_spec_count": 40,
        "task_family_count": task_family_count,
        "profile_count": profile_count,
        "planned_workload_row_count": len(workload_rows),
        "expected_workload_row_count": expected_workload_count,
        "materialization_failure_count": materialization_failure_count,
        "contract_violation_count": contract_violation_count,
        "forbidden_key_violation_count": forbidden_key_violation_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "metric_count": len(metric_rows),
        "claim_boundary_row_count": len(claim_rows),
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
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "required_files_written": True,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "executable_task_specs": str(output / "executable_task_specs.json"),
            "executable_task_specs_csv": str(output / "executable_task_specs.csv"),
            "planned_workload": str(output / "planned_workload.csv"),
            "profile_matrix": str(output / "profile_matrix.csv"),
            "materialization_failures": str(output / "materialization_failures.csv"),
            "aggregate_by_task_family": str(output / "aggregate_by_task_family.csv"),
            "metric_support": str(output / "metric_support.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2151-paper-route-current-sim-controlled-comparison-executable-spec-materialization-implementation",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-config", type=Path, default=DEFAULT_BENCHMARK_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_executable_specs(
        benchmark_config_path=args.benchmark_config,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
