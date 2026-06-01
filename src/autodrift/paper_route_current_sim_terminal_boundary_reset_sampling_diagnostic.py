"""Reset-only diagnostic for the current-sim terminal-boundary sampling failure."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import forbidden_key_violations
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.paper_route_current_sim_controlled_comparison_reset_validation_preflight import (
    CLAIM_FIELDNAMES,
    CONTRACT_FIELDNAMES,
    METADATA_MISSING_FIELDNAMES,
    RESET_FIELDNAMES,
    _bool_value,
    _guardrail_flags,
    contract_row_for_spec,
    current_sim_metadata,
    load_executable_task_specs,
    metadata_missing_rows,
    reset_current_sim_spec,
)


DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic")
DEFAULT_TARGET_TASK_SOURCE_ID = "m2151-current-sim-t5-03"
DEFAULT_EVAL_SEEDS = (215335, 219103)
DEFAULT_ATTEMPT_BUDGETS = (200, 800, 1600)
DEFAULT_EXPECTED_OBSERVATION_DIM = 72
DEFAULT_NEXT_BLOCKER = "m2159-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-result-audit"

DIAGNOSTIC_FIELDNAMES = [
    *RESET_FIELDNAMES,
    "diagnostic_attempt_id",
    "target_task_source_id",
    "diagnostic_eval_seed",
    "attempt_budget",
    "original_max_sample_attempts",
    "attempt_budget_applied",
]
CLASSIFICATION_FIELDNAMES = ["diagnostic_classification", "admissible", "reason"]


def _parse_int_list(value: str | Iterable[int]) -> list[int]:
    if isinstance(value, str):
        return [int(item.strip()) for item in value.split(",") if item.strip()]
    return [int(item) for item in value]


def _target_specs(specs: Iterable[Mapping[str, Any]], target_task_source_id: str) -> list[dict[str, Any]]:
    return [dict(spec) for spec in specs if str(spec.get("task_source_id", "")) == str(target_task_source_id)]


def _spec_with_attempt_budget(spec: Mapping[str, Any], attempt_budget: int) -> dict[str, Any]:
    copied = dict(spec)
    env_config = dict(copied.get("env_config") or {})
    obstacle = dict(env_config.get("obstacle") or {})
    obstacle["max_sample_attempts"] = int(attempt_budget)
    env_config["obstacle"] = obstacle
    copied["env_config"] = env_config
    return copied


def _diagnostic_classification(
    rows: list[Mapping[str, Any]],
    *,
    original_seed: int,
    materialized_seed: int,
    original_attempt_budget: int,
) -> str:
    successes = {
        (int(row.get("diagnostic_eval_seed", 0)), int(row.get("attempt_budget", 0))): _bool_value(
            row.get("reset_success")
        )
        for row in rows
    }
    original_at_base = successes.get((int(original_seed), int(original_attempt_budget)), False)
    if original_at_base:
        return "original_seed_passes_at_200"
    original_higher_success = any(
        success
        for (seed, budget), success in successes.items()
        if int(seed) == int(original_seed) and int(budget) > int(original_attempt_budget)
    )
    if original_higher_success:
        return "attempt_budget_limited"
    materialized_at_base = successes.get((int(materialized_seed), int(original_attempt_budget)), False)
    if materialized_at_base:
        return "seed_local_sampling_failure"
    if not any(successes.values()):
        return "terminal_boundary_template_brittle"
    return "mixed_or_inconclusive"


def classification_rows(classification: str) -> list[dict[str, Any]]:
    reasons = {
        "original_seed_passes_at_200": "the original frozen seed passed under the original 200-attempt budget",
        "attempt_budget_limited": "the original frozen seed failed at 200 attempts but passed at a larger bounded budget",
        "seed_local_sampling_failure": "the original frozen seed failed but the materialized eval seed passed at 200 attempts",
        "terminal_boundary_template_brittle": "all bounded diagnostic attempts failed",
        "mixed_or_inconclusive": "diagnostic outcomes did not match a single clean failure class",
    }
    return [
        {
            "diagnostic_classification": classification,
            "admissible": True,
            "reason": reasons.get(classification, "classification is explicit"),
        }
    ]


def claim_boundary_rows(*, diagnostic_complete: bool) -> list[dict[str, Any]]:
    return [
        {
            "claim": "terminal_boundary_reset_sampling_classification",
            "admissible": diagnostic_complete,
            "reason": "classification is admissible only for the single diagnosed terminal-boundary row",
        },
        {
            "claim": "full_panel_reset_validity",
            "admissible": False,
            "reason": "diagnostic is not a repaired 40-spec reset-validation rerun",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "policy actions and measured rollout remain blocked",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "reset diagnostic does not compare controller-family outcomes",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "reset diagnostic does not compare controller-family outcomes",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "reset diagnostic does not test history necessity",
        },
    ]


def run_terminal_boundary_reset_sampling_diagnostic(
    *,
    executable_task_specs_path: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    target_task_source_id: str = DEFAULT_TARGET_TASK_SOURCE_ID,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seeds: str | Iterable[int] = DEFAULT_EVAL_SEEDS,
    attempt_budgets: str | Iterable[int] = DEFAULT_ATTEMPT_BUDGETS,
    expected_observation_dim: int | None = DEFAULT_EXPECTED_OBSERVATION_DIM,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    seeds = _parse_int_list(eval_seeds)
    budgets = _parse_int_list(attempt_budgets)
    specs = load_executable_task_specs(executable_task_specs_path)
    targets = _target_specs(specs, target_task_source_id)
    diagnostic_rows: list[dict[str, Any]] = []
    contract_rows: list[dict[str, Any]] = []
    if len(targets) == 1:
        target = targets[0]
        original_budget = int(dict(dict(target.get("env_config") or {}).get("obstacle") or {}).get("max_sample_attempts", 0))
        attempt_id = 0
        for seed in seeds:
            for budget in budgets:
                attempt_spec = _spec_with_attempt_budget(target, int(budget))
                reset_row = reset_current_sim_spec(
                    spec=attempt_spec,
                    eval_seed=int(seed),
                    expected_observation_dim=expected_observation_dim,
                )
                diagnostic_rows.append(
                    {
                        **reset_row,
                        "diagnostic_attempt_id": f"diag-{attempt_id:02d}",
                        "target_task_source_id": str(target_task_source_id),
                        "diagnostic_eval_seed": int(seed),
                        "attempt_budget": int(budget),
                        "original_max_sample_attempts": int(original_budget),
                        "attempt_budget_applied": int(budget),
                    }
                )
                contract_rows.append(contract_row_for_spec(attempt_spec))
                attempt_id += 1
    else:
        original_budget = 0

    failure_rows = [dict(row) for row in diagnostic_rows if not _bool_value(row.get("reset_success"))]
    missing_rows = metadata_missing_rows(targets)
    forbidden_key_hits = forbidden_key_violations(targets)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in contract_rows)
    observed_eval_seed_count = len({int(row.get("diagnostic_eval_seed", 0)) for row in diagnostic_rows})
    observed_attempt_budget_count = len({int(row.get("attempt_budget", 0)) for row in diagnostic_rows})
    expected_attempt_count = len(seeds) * len(budgets) if len(targets) == 1 else 0
    classification = (
        _diagnostic_classification(
            diagnostic_rows,
            original_seed=int(seeds[0]) if seeds else 0,
            materialized_seed=int(seeds[1]) if len(seeds) > 1 else int(seeds[0]) if seeds else 0,
            original_attempt_budget=int(budgets[0]) if budgets else 0,
        )
        if diagnostic_rows
        else "mixed_or_inconclusive"
    )
    diagnostic_complete = (
        len(targets) == 1
        and len(diagnostic_rows) == expected_attempt_count
        and observed_eval_seed_count == len(seeds)
        and observed_attempt_budget_count == len(budgets)
        and contract_violation_count == 0
        and not missing_rows
        and not forbidden_key_hits
        and guardrail_violation_count == 0
    )
    result_class = "current_sim_terminal_boundary_reset_sampling_diagnostic_complete" if diagnostic_complete else (
        "current_sim_terminal_boundary_reset_sampling_diagnostic_fail"
    )

    write_csv_rows(output / "diagnostic_rows.csv", diagnostic_rows, fieldnames=DIAGNOSTIC_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", failure_rows, fieldnames=DIAGNOSTIC_FIELDNAMES)
    write_csv_rows(output / "contract_rows.csv", contract_rows, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(output / "metadata_missing_rows.csv", missing_rows, fieldnames=METADATA_MISSING_FIELDNAMES)
    write_csv_rows(output / "classification_rows.csv", classification_rows(classification), CLASSIFICATION_FIELDNAMES)
    write_csv_rows(
        output / "claim_boundary.csv",
        claim_boundary_rows(diagnostic_complete=bool(diagnostic_complete)),
        CLAIM_FIELDNAMES,
    )

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "executable_task_specs_path": str(executable_task_specs_path),
        "target_task_source_id": str(target_task_source_id),
        "target_spec_count": len(targets),
        "eval_seeds": seeds,
        "attempt_budgets": budgets,
        "observed_eval_seed_count": int(observed_eval_seed_count),
        "observed_attempt_budget_count": int(observed_attempt_budget_count),
        "diagnostic_attempt_count": len(diagnostic_rows),
        "expected_diagnostic_attempt_count": int(expected_attempt_count),
        "reset_success_count": int(sum(_bool_value(row.get("reset_success")) for row in diagnostic_rows)),
        "reset_failure_count": len(failure_rows),
        "observation_finite_count": int(sum(_bool_value(row.get("observation_finite")) for row in diagnostic_rows)),
        "observation_dimension_failure_count": int(
            sum(
                _bool_value(row.get("reset_success")) and not _bool_value(row.get("observation_dimension_matches"))
                for row in diagnostic_rows
            )
        ),
        "obstacle_initialized_count": int(sum(_bool_value(row.get("obstacle_initialized")) for row in diagnostic_rows)),
        "contract_violation_count": int(contract_violation_count),
        "metadata_missing_count": len(missing_rows),
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "diagnostic_classification": classification,
        "original_max_sample_attempts": int(original_budget),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": bool(diagnostic_rows),
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
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "diagnostic_rows": str(output / "diagnostic_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "contract_rows": str(output / "contract_rows.csv"),
            "metadata_missing_rows": str(output / "metadata_missing_rows.csv"),
            "classification_rows": str(output / "classification_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2158-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-implementation-and-run",
            "status": "completed" if diagnostic_complete else "failed",
            "result_class": result_class,
            "diagnostic_classification": classification,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--target-task-source-id", default=DEFAULT_TARGET_TASK_SOURCE_ID)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seeds", default=",".join(str(seed) for seed in DEFAULT_EVAL_SEEDS))
    parser.add_argument("--attempt-budgets", default=",".join(str(budget) for budget in DEFAULT_ATTEMPT_BUDGETS))
    parser.add_argument("--expected-observation-dim", type=int, default=DEFAULT_EXPECTED_OBSERVATION_DIM)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    summary = run_terminal_boundary_reset_sampling_diagnostic(
        executable_task_specs_path=args.executable_task_specs,
        target_task_source_id=str(args.target_task_source_id),
        output_dir=args.output_dir,
        eval_seeds=str(args.eval_seeds),
        attempt_budgets=str(args.attempt_budgets),
        expected_observation_dim=args.expected_observation_dim,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"diagnostic_attempt_count={summary['diagnostic_attempt_count']}")
    print(f"reset_success_count={summary['reset_success_count']}")
    print(f"reset_failure_count={summary['reset_failure_count']}")
    print(f"diagnostic_classification={summary['diagnostic_classification']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())
