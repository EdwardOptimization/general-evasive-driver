"""Reset-only evidence for source-linked repair-candidate overlays.

M2426 links the four M2422 source-linked repair-candidate overlays to the
M2391 reset-valid effective candidate scenario specs, then resets each unique
concrete env config. It intentionally stops before any environment step or
policy action.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift import paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence as base
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_OVERLAY_DIR = Path(
    "runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization"
)
DEFAULT_SOURCE_EFFECTIVE_DIR = Path(
    "runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence"
)
DEFAULT_TARGET_CANDIDATE_COUNT = 4
DEFAULT_EVAL_SEED_BASE = 242600
DEFAULT_NEXT_BLOCKER = (
    "m2427-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-result-audit"
)
EXPECTED_SOURCE_OVERLAY_RESULT_CLASS = "current_sim_dual_axis_source_linked_repair_candidate_materialization_pass"
EXPECTED_EFFECTIVE_RESULT_CLASS = "current_sim_dual_axis_effective_config_schema_repair_materialization_pass"
RESULT_PASS = "current_sim_dual_axis_source_linked_repair_candidate_reset_evidence_pass"
RESULT_FAIL = "current_sim_dual_axis_source_linked_repair_candidate_reset_evidence_fail_closed"


def _bool(value: Any, *, default: bool = False) -> bool:
    return base._bool(value, default=default)


def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _source_keys_for_effective_row(row: Mapping[str, Any]) -> set[str]:
    axis = str(row.get("source_slice_axis", ""))
    value = str(row.get("source_slice_value", ""))
    if not axis or not value:
        return set()
    keys = {
        f"{axis}:{value}",
        f"source_slice_axis+source_slice_value:{axis}|{value}",
        f"episode_rows:{axis}:{value}",
        f"episode_rows:source_slice_axis+source_slice_value:{axis}|{value}",
    }
    return keys


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "source_linked_repair_candidate_reset_evidence",
            "admissible": True,
            "reason": "M2426 may claim reset-only source-linked repair-candidate evidence if gates pass or fail closed with unmatched-key diagnostics",
        },
        {
            "claim": "environment_step_or_policy_action",
            "admissible": False,
            "reason": "M2426 stops immediately after reset",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "M2426 does not roll out a policy",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2426 does not execute source-linked repair-candidate levers",
        },
        {
            "claim": "candidate_or_family_ranking",
            "admissible": False,
            "reason": "M2426 records reset coverage only and cannot rank candidates or families",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2426 does not overwrite or activate repaired scenario configs",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2426 does not train or evaluate a repaired driver",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2426 is reset preflight evidence, not paper-level evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2426 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2426 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2426 does not run measured validation needed for a verdict",
        },
    ]


def load_effective_candidates(source_effective_dir: Path) -> list[dict[str, Any]]:
    rows = base.read_csv_rows(source_effective_dir / "effective_candidate_config_rows.csv")
    loaded: list[dict[str, Any]] = []
    for row in rows:
        path = Path(str(row.get("effective_candidate_config_path", "")))
        payload = read_json(path)
        loaded.append(
            {
                "row": row,
                "path": path,
                "payload": payload,
                "source_keys": _source_keys_for_effective_row(row),
            }
        )
    return loaded


def run_source_linked_repair_candidate_reset_evidence(
    *,
    source_overlay_dir: Path | str = DEFAULT_SOURCE_OVERLAY_DIR,
    source_effective_dir: Path | str = DEFAULT_SOURCE_EFFECTIVE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_candidate_count: int = DEFAULT_TARGET_CANDIDATE_COUNT,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_overlay = Path(source_overlay_dir)
    source_effective = Path(source_effective_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_overlay_summary = read_json(source_overlay / "summary.json")
    source_effective_summary = read_json(source_effective / "summary.json")
    families = base.load_family_overlays(source_overlay)
    effective_candidates = load_effective_candidates(source_effective)

    family_rows, scenario_rows, unmatched_rows, target_rows, target_env_configs = base.build_source_linked_rows(
        source_overlay_dir=source_overlay,
        source_effective_dir=source_effective,
        families=families,
        effective_candidates=effective_candidates,
    )
    static_failure_count = sum(not _bool(row.get("static_validation_pass")) for row in scenario_rows)

    reset_rows: list[dict[str, Any]] = []
    if static_failure_count == 0:
        for index, target_row in enumerate(target_rows):
            env_config = target_env_configs.get(str(target_row.get("reset_target_key", "")), {})
            reset_rows.append(
                base.reset_target(
                    target_row=target_row,
                    env_config=env_config,
                    eval_seed=int(eval_seed_base) + index,
                )
            )
    family_rows = base.attach_family_reset_results(
        family_rows=family_rows,
        scenario_rows=scenario_rows,
        reset_rows=reset_rows,
    )

    reset_failure_rows = [row for row in reset_rows if not _bool(row.get("environment_reset_success"))]
    family_count = len(family_rows)
    matched_family_count = sum(int(row.get("matched_effective_candidate_count", 0)) > 0 for row in family_rows)
    family_without_match_count = family_count - matched_family_count
    family_reset_pass_count = sum(_bool(row.get("family_reset_pass")) for row in family_rows)
    family_reset_failure_count = family_count - family_reset_pass_count
    environment_load_attempt_count = sum(_bool(row.get("environment_load_attempted")) for row in reset_rows)
    environment_reset_attempt_count = sum(_bool(row.get("environment_reset_attempted")) for row in reset_rows)
    environment_reset_success_count = sum(_bool(row.get("environment_reset_success")) for row in reset_rows)
    environment_step_count = sum(int(row.get("environment_step_count", 0)) for row in reset_rows)
    policy_action_executed = any(_bool(row.get("policy_action_executed")) for row in reset_rows)
    active_config_overwrite_count = 0
    ranking_admissible_count = 0
    winner_selected_count = 0
    fail_closed_unmatched_source_key_result_recorded = family_without_match_count > 0 and len(unmatched_rows) > 0

    guardrail_flags = {
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "policy_action_executed": policy_action_executed,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "candidate_family_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    failure_types_observed = [
        name
        for name, count in [
            ("family_source_link_failure", family_without_match_count),
            ("static_schema_failure", static_failure_count),
            ("scenario_sampling_failure", len(reset_failure_rows)),
            ("forbidden_execution_failure", environment_step_count + int(policy_action_executed)),
        ]
        if count
    ]

    passes = (
        source_overlay_summary.get("result_class") == EXPECTED_SOURCE_OVERLAY_RESULT_CLASS
        and source_effective_summary.get("result_class") == EXPECTED_EFFECTIVE_RESULT_CLASS
        and family_count == int(target_candidate_count)
        and matched_family_count == int(target_candidate_count)
        and family_without_match_count == 0
        and len(scenario_rows) > 0
        and len(target_rows) > 0
        and static_failure_count == 0
        and environment_load_attempt_count == len(target_rows)
        and environment_reset_attempt_count == len(target_rows)
        and environment_reset_success_count == len(target_rows)
        and not reset_failure_rows
        and family_reset_pass_count == int(target_candidate_count)
        and family_reset_failure_count == 0
        and environment_step_count == 0
        and not policy_action_executed
        and active_config_overwrite_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL

    write_csv_rows(output / "source_linked_family_rows.csv", family_rows, fieldnames=base.FAMILY_FIELDNAMES)
    write_csv_rows(output / "source_linked_scenario_rows.csv", scenario_rows, fieldnames=base.SCENARIO_FIELDNAMES)
    write_csv_rows(output / "unmatched_source_key_rows.csv", unmatched_rows, fieldnames=base.UNMATCHED_FIELDNAMES)
    write_csv_rows(output / "reset_target_rows.csv", target_rows, fieldnames=base.RESET_TARGET_FIELDNAMES)
    write_csv_rows(output / "reset_validation_rows.csv", reset_rows, fieldnames=base.RESET_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", reset_failure_rows, fieldnames=base.RESET_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=base.CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "source_overlay_dir": str(source_overlay),
        "source_effective_dir": str(source_effective),
        "output_dir": str(output),
        "source_overlay_result_class": source_overlay_summary.get("result_class", ""),
        "source_effective_result_class": source_effective_summary.get("result_class", ""),
        "candidate_overlay_load_count": len(families),
        "candidate_family_count": family_count,
        "target_candidate_count": int(target_candidate_count),
        "matched_family_count": matched_family_count,
        "family_without_match_count": family_without_match_count,
        "fail_closed_unmatched_source_key_result_recorded": fail_closed_unmatched_source_key_result_recorded,
        "source_effective_candidate_count": len(effective_candidates),
        "matched_effective_candidate_count": len(
            {str(row.get("effective_candidate_id", "")) for row in scenario_rows}
        ),
        "source_linked_scenario_reference_count": len(scenario_rows),
        "unique_reset_target_count": len(target_rows),
        "unmatched_source_key_count": len(unmatched_rows),
        "static_validation_failure_count": static_failure_count,
        "environment_load_attempt_count": environment_load_attempt_count,
        "environment_reset_attempt_count": environment_reset_attempt_count,
        "environment_reset_success_count": environment_reset_success_count,
        "environment_reset_failure_count": len(reset_failure_rows),
        "environment_reset_started": environment_reset_attempt_count > 0,
        "environment_step_count": environment_step_count,
        "policy_action_executed": policy_action_executed,
        "family_reset_pass_count": family_reset_pass_count,
        "family_reset_failure_count": family_reset_failure_count,
        "active_config_overwrite_count": active_config_overwrite_count,
        "active_config_overwritten": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "candidate_family_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types_observed,
        "matched_effective_candidates_by_family": {
            str(row.get("candidate_id", "")): int(row.get("matched_effective_candidate_count", 0))
            for row in family_rows
        },
        "source_linked_scenarios_by_family": {
            str(row.get("candidate_id", "")): int(row.get("source_linked_scenario_reference_count", 0))
            for row in family_rows
        },
        "unique_reset_targets_by_family": {
            str(row.get("candidate_id", "")): int(row.get("unique_reset_target_count", 0))
            for row in family_rows
        },
        "unmatched_source_keys_by_family": {
            str(row.get("candidate_id", "")): int(row.get("unmatched_source_key_count", 0))
            for row in family_rows
        },
        "reset_target_counts_by_pack": _count_by(target_rows, "pack_id"),
        "artifacts": {
            "summary": str(output / "summary.json"),
            "source_linked_family_rows": str(output / "source_linked_family_rows.csv"),
            "source_linked_scenario_rows": str(output / "source_linked_scenario_rows.csv"),
            "unmatched_source_key_rows": str(output / "unmatched_source_key_rows.csv"),
            "reset_target_rows": str(output / "reset_target_rows.csv"),
            "reset_validation_rows": str(output / "reset_validation_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-overlay-dir", type=Path, default=DEFAULT_SOURCE_OVERLAY_DIR)
    parser.add_argument("--source-effective-dir", type=Path, default=DEFAULT_SOURCE_EFFECTIVE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-candidate-count", type=int, default=DEFAULT_TARGET_CANDIDATE_COUNT)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_source_linked_repair_candidate_reset_evidence(
        source_overlay_dir=args.source_overlay_dir,
        source_effective_dir=args.source_effective_dir,
        output_dir=args.output_dir,
        target_candidate_count=int(args.target_candidate_count),
        eval_seed_base=int(args.eval_seed_base),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_family_count={summary['candidate_family_count']}")
    print(f"matched_family_count={summary['matched_family_count']}")
    print(f"family_without_match_count={summary['family_without_match_count']}")
    print(f"source_linked_scenario_reference_count={summary['source_linked_scenario_reference_count']}")
    print(f"unique_reset_target_count={summary['unique_reset_target_count']}")
    print(f"environment_reset_attempt_count={summary['environment_reset_attempt_count']}")
    print(f"environment_reset_success_count={summary['environment_reset_success_count']}")
    print(f"unmatched_source_key_count={summary['unmatched_source_key_count']}")
    print(f"environment_step_count={summary['environment_step_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
