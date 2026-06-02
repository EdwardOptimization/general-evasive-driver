"""Reindex existing measured rows by M2426 repair-candidate memberships."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_scenario_task_family_measured_execution as base_runner
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_RESET_DIR = Path(
    "runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence"
)
DEFAULT_SOURCE_MEASURED_DIR = Path(
    "runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex"
)
DEFAULT_NEXT_BLOCKER = (
    "m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit"
)
RESULT_PASS = "current_sim_dual_axis_source_linked_repair_candidate_measured_reindex_pass"
RESULT_FAIL = "current_sim_dual_axis_source_linked_repair_candidate_measured_reindex_incomplete_or_fail"
EXCLUDED_CANDIDATE_ID = "c04_source_linked_outcome_failure_surface_containment"

EXTRA_MEMBERSHIP_FIELDS = [
    "candidate_id",
    "candidate_family",
    "candidate_profile_key",
    "candidate_pack_key",
    "source_linked_repair_candidate_measured_reindex",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    return base_runner._bool(value, default=default)


def _int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _rate(count: int, total: int) -> float:
    return float(count / total) if total else 0.0


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "source_linked_repair_candidate_measured_reindex",
            "admissible": True,
            "reason": "M2428 may claim non-ranking reindex of existing M2413 measured rows by matched M2426 candidate memberships",
        },
        {
            "claim": "new_measured_rollout",
            "admissible": False,
            "reason": "M2428 only reuses existing measured rows",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2428 does not execute repair levers",
        },
        {
            "claim": "candidate_family_ranking",
            "admissible": False,
            "reason": "M2428 aggregates are diagnostic-only",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2428 cannot select a winner",
        },
        {
            "claim": "c04_measured_evidence",
            "admissible": False,
            "reason": "M2426 c04 has zero matched effective candidates and must remain excluded",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2428 is a matched-subset reindex, not a current-sim verdict",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2428 is diagnostic reanalysis only",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2428 does not compare finite-window and GRU policies",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2428 does not run history interventions",
        },
    ]


def _candidate_membership_by_reset_key(
    scenario_rows: Sequence[Mapping[str, Any]],
    family_rows: Sequence[Mapping[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    matched_family_ids = {
        str(row.get("candidate_id", ""))
        for row in family_rows
        if _int(row.get("matched_effective_candidate_count")) > 0
    }
    by_reset: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in scenario_rows:
        candidate_id = str(row.get("candidate_id", ""))
        reset_key = str(row.get("reset_target_key", ""))
        if not reset_key or candidate_id not in matched_family_ids:
            continue
        if candidate_id == EXCLUDED_CANDIDATE_ID:
            continue
        by_reset[reset_key][candidate_id] = {
            "candidate_id": candidate_id,
            "candidate_family": str(row.get("candidate_family", "")),
        }
    return {key: [members[cid] for cid in sorted(members)] for key, members in sorted(by_reset.items())}


def _membership_rows(
    episode_rows: Sequence[Mapping[str, Any]],
    membership_by_reset: Mapping[str, Sequence[Mapping[str, str]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        reset_key = str(episode.get("reset_target_key", ""))
        for member in membership_by_reset.get(reset_key, []):
            candidate_id = str(member.get("candidate_id", ""))
            row = dict(episode)
            row.update(
                {
                    "candidate_id": candidate_id,
                    "candidate_family": str(member.get("candidate_family", "")),
                    "candidate_profile_key": f"{candidate_id}|{episode.get('profile_name', '')}",
                    "candidate_pack_key": f"{candidate_id}|{episode.get('pack_id', '')}",
                    "source_linked_repair_candidate_measured_reindex": True,
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
            rows.append(row)
    return rows


def _aggregate_by_two_keys(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_axis: str,
    key_a: str,
    key_b: str,
) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        value = f"{row.get(key_a, '')}|{row.get(key_b, '')}"
        groups.setdefault(value, []).append(row)
    return [
        base_runner.aggregate_row(group, group_axis=group_axis, group_key=f"{key_a}+{key_b}", group_value=value)
        for value, group in sorted(groups.items())
    ]


def _write_aggregate(
    *,
    output_dir: Path,
    artifacts: dict[str, str],
    rows: Sequence[Mapping[str, Any]],
    artifact_key: str,
    filename: str,
    group_key: str,
) -> list[dict[str, Any]]:
    aggregate = base_runner.aggregate_rows(rows, group_axis=group_key, group_key=group_key)
    path = output_dir / filename
    write_csv_rows(path, aggregate, fieldnames=base_runner.AGGREGATE_FIELDNAMES)
    artifacts[artifact_key] = str(path)
    return aggregate


def run_source_linked_repair_candidate_measured_reindex(
    *,
    source_reset_dir: Path | str = DEFAULT_SOURCE_RESET_DIR,
    source_measured_dir: Path | str = DEFAULT_SOURCE_MEASURED_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_reset = Path(source_reset_dir)
    source_measured = Path(source_measured_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_reset_summary = read_json(source_reset / "summary.json")
    source_measured_summary = read_json(source_measured / "summary.json")
    family_rows = read_csv_rows(source_reset / "source_linked_family_rows.csv")
    scenario_rows = read_csv_rows(source_reset / "source_linked_scenario_rows.csv")
    reset_target_rows = read_csv_rows(source_reset / "reset_target_rows.csv")
    episode_rows = read_csv_rows(source_measured / "episode_rows.csv")

    reset_keys = {str(row.get("reset_target_key", "")) for row in reset_target_rows}
    measured_reset_keys = {str(row.get("reset_target_key", "")) for row in episode_rows}
    reset_keys_not_in_measured = sorted(reset_keys - measured_reset_keys)
    measured_keys_not_in_reset = sorted(measured_reset_keys - reset_keys)
    exact_reset_key_coverage = not reset_keys_not_in_measured and not measured_keys_not_in_reset

    membership_by_reset = _candidate_membership_by_reset_key(scenario_rows, family_rows)
    membership_rows = _membership_rows(episode_rows, membership_by_reset)
    measured_candidate_ids = {str(row.get("candidate_id", "")) for row in membership_rows}
    c04_included_as_measured = EXCLUDED_CANDIDATE_ID in measured_candidate_ids

    membership_fieldnames = base_runner._extend_unique(
        list(episode_rows[0].keys()) if episode_rows else [],
        EXTRA_MEMBERSHIP_FIELDS,
    )
    write_csv_rows(output / "reindexed_episode_membership_rows.csv", membership_rows, fieldnames=membership_fieldnames)
    write_csv_rows(
        output / "excluded_candidate_rows.csv",
        [row for row in family_rows if str(row.get("candidate_id", "")) == EXCLUDED_CANDIDATE_ID],
    )
    write_csv_rows(
        output / "reset_key_coverage_failure_rows.csv",
        [{"reset_target_key": key, "failure_type": "m2426_not_in_m2413"} for key in reset_keys_not_in_measured]
        + [{"reset_target_key": key, "failure_type": "m2413_not_in_m2426"} for key in measured_keys_not_in_reset],
        fieldnames=["reset_target_key", "failure_type"],
    )
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    artifacts: dict[str, str] = {
        "summary": str(output / "summary.json"),
        "reindexed_episode_membership_rows": str(output / "reindexed_episode_membership_rows.csv"),
        "excluded_candidate_rows": str(output / "excluded_candidate_rows.csv"),
        "reset_key_coverage_failure_rows": str(output / "reset_key_coverage_failure_rows.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }
    aggregate_by_candidate = _write_aggregate(
        output_dir=output,
        artifacts=artifacts,
        rows=membership_rows,
        artifact_key="aggregate_by_candidate",
        filename="aggregate_by_candidate.csv",
        group_key="candidate_id",
    )
    aggregate_by_candidate_profile = _aggregate_by_two_keys(
        membership_rows,
        group_axis="candidate_profile",
        key_a="candidate_id",
        key_b="profile_name",
    )
    write_csv_rows(
        output / "aggregate_by_candidate_profile.csv",
        aggregate_by_candidate_profile,
        fieldnames=base_runner.AGGREGATE_FIELDNAMES,
    )
    artifacts["aggregate_by_candidate_profile"] = str(output / "aggregate_by_candidate_profile.csv")
    aggregate_by_candidate_pack = _aggregate_by_two_keys(
        membership_rows,
        group_axis="candidate_pack",
        key_a="candidate_id",
        key_b="pack_id",
    )
    write_csv_rows(
        output / "aggregate_by_candidate_pack.csv",
        aggregate_by_candidate_pack,
        fieldnames=base_runner.AGGREGATE_FIELDNAMES,
    )
    artifacts["aggregate_by_candidate_pack"] = str(output / "aggregate_by_candidate_pack.csv")

    matched_candidate_count = len(measured_candidate_ids)
    expected_matched_candidate_count = sum(
        _int(row.get("matched_effective_candidate_count")) > 0
        and str(row.get("candidate_id", "")) != EXCLUDED_CANDIDATE_ID
        for row in family_rows
    )
    selected_checkpoint_count = len({str(row.get("selected_checkpoint_path", "")) for row in episode_rows})
    reindexed_reset_target_count = len({str(row.get("reset_target_key", "")) for row in membership_rows})
    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in membership_rows)
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in membership_rows)
    guardrail_flags = {
        "reset_rerun_started": False,
        "new_measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "candidate_family_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "c04_included_as_measured": c04_included_as_measured,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    failure_types_observed = [
        name
        for name, count in [
            ("lineage_invalid", len(reset_keys_not_in_measured) + len(measured_keys_not_in_reset)),
            ("metric_artifact", int(c04_included_as_measured)),
            ("candidate_membership_missing", int(matched_candidate_count != expected_matched_candidate_count)),
            ("forbidden_ranking_failure", ranking_admissible_count + winner_selected_count),
        ]
        if count
    ]
    passes = (
        exact_reset_key_coverage
        and len(episode_rows) > 0
        and len(membership_rows) > 0
        and matched_candidate_count == expected_matched_candidate_count
        and expected_matched_candidate_count > 0
        and len(aggregate_by_candidate) == expected_matched_candidate_count
        and not c04_included_as_measured
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "source_reset_dir": str(source_reset),
        "source_measured_dir": str(source_measured),
        "output_dir": str(output),
        "source_reset_result_class": source_reset_summary.get("result_class", ""),
        "source_measured_result_class": source_measured_summary.get("result_class", ""),
        "source_reset_target_count": len(reset_keys),
        "source_measured_reset_target_count": len(measured_reset_keys),
        "exact_reset_key_coverage": exact_reset_key_coverage,
        "reset_keys_not_in_measured_count": len(reset_keys_not_in_measured),
        "measured_keys_not_in_reset_count": len(measured_keys_not_in_reset),
        "source_episode_count": len(episode_rows),
        "selected_checkpoint_count": selected_checkpoint_count,
        "reindexed_membership_row_count": len(membership_rows),
        "reindexed_reset_target_count": reindexed_reset_target_count,
        "matched_candidate_family_count": matched_candidate_count,
        "expected_matched_candidate_family_count": expected_matched_candidate_count,
        "excluded_candidate_id": EXCLUDED_CANDIDATE_ID,
        "excluded_candidate_count": int(any(str(row.get("candidate_id", "")) == EXCLUDED_CANDIDATE_ID for row in family_rows)),
        "c04_included_as_measured": c04_included_as_measured,
        "aggregate_by_candidate_row_count": len(aggregate_by_candidate),
        "aggregate_by_candidate_profile_row_count": len(aggregate_by_candidate_profile),
        "aggregate_by_candidate_pack_row_count": len(aggregate_by_candidate_pack),
        "membership_rows_by_candidate": _count_by(membership_rows, "candidate_id"),
        "reset_targets_by_candidate": {
            candidate_id: len({str(row.get("reset_target_key", "")) for row in membership_rows if str(row.get("candidate_id", "")) == candidate_id})
            for candidate_id in sorted(measured_candidate_ids)
        },
        "diagnostic_only": True,
        "reset_rerun_started": False,
        "new_measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types_observed,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-reset-dir", type=Path, default=DEFAULT_SOURCE_RESET_DIR)
    parser.add_argument("--source-measured-dir", type=Path, default=DEFAULT_SOURCE_MEASURED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_source_linked_repair_candidate_measured_reindex(
        source_reset_dir=args.source_reset_dir,
        source_measured_dir=args.source_measured_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_episode_count={summary['source_episode_count']}")
    print(f"reindexed_membership_row_count={summary['reindexed_membership_row_count']}")
    print(f"matched_candidate_family_count={summary['matched_candidate_family_count']}")
    print(f"excluded_candidate_id={summary['excluded_candidate_id']}")
    print(f"exact_reset_key_coverage={summary['exact_reset_key_coverage']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
