"""No-rerun audit for current-sim repeat outcome support and seed diversity."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_ORIGINAL_OUTPUT_DIR = Path("runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution")
DEFAULT_ORIGINAL_WORKLOAD = Path("runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv")
DEFAULT_REPEAT_OUTPUT_DIR = Path("runs/m2184_paper_route_current_sim_repeat_measured_execution")
DEFAULT_REPEAT_WORKLOAD = Path("runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/combined_new_repeat_materialized_workload.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit")
ORIGINAL_REPEAT_ID = "repeat_0_existing"
TARGET_REPEAT_IDS = ("repeat_0_existing", "repeat_1_seed_21761", "repeat_2_seed_21762")
AGGREGATE_FIELDNAMES = [
    "training_repeat_id",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
    "clearance_margin_mean",
    "return_mean",
    "steps_mean",
]
PROFILE_REPEAT_FIELDNAMES = [
    "training_repeat_id",
    "profile_name",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
]
DIVERSITY_FIELDNAMES = ["check", "status", "value", "details"]
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


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: Iterable[float | None]) -> float:
    finite = [float(value) for value in values if value is not None]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _is_success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success")) or str(row.get("outcome_bucket", "")) == "success_obstacle_pass"


def _is_collision(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("collision")) or str(row.get("outcome_bucket", "")) == "collision_failure"


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "off_track_noncollision_noncompletion"


def _annotated_episode_rows(output_dir: Path | str, *, default_repeat_id: str) -> list[dict[str, str]]:
    rows = read_csv_rows(Path(output_dir) / "episode_rows.csv")
    annotated: list[dict[str, str]] = []
    for row in rows:
        copy = dict(row)
        if not str(copy.get("training_repeat_id", "")).strip():
            copy["training_repeat_id"] = default_repeat_id
        if not str(copy.get("training_seed_group", "")).strip():
            copy["training_seed_group"] = "existing" if default_repeat_id == ORIGINAL_REPEAT_ID else ""
        annotated.append(copy)
    return annotated


def _summary_guardrail_violation_count(path: Path | str) -> int:
    summary_path = Path(path) / "summary.json"
    if not summary_path.exists():
        return 1
    return int(read_json(summary_path).get("guardrail_violation_count", 1))


def _aggregate(rows: list[Mapping[str, Any]], *, repeat_id: str, profile_name: str | None = None) -> dict[str, Any]:
    count = len(rows)
    success_count = sum(1 for row in rows if _is_success(row))
    collision_count = sum(1 for row in rows if _is_collision(row))
    offtrack_count = sum(1 for row in rows if _is_offtrack(row))
    output: dict[str, Any] = {
        "training_repeat_id": repeat_id,
        "episode_count": count,
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_count": offtrack_count,
        "success_rate": float(success_count / count) if count else 0.0,
        "collision_rate": float(collision_count / count) if count else 0.0,
        "offtrack_rate": float(offtrack_count / count) if count else 0.0,
    }
    if profile_name is not None:
        output["profile_name"] = profile_name
    else:
        output.update(
            {
                "clearance_margin_mean": _mean(_float_or_none(row.get("min_clearance_margin")) for row in rows),
                "return_mean": _mean(_float_or_none(row.get("return")) for row in rows),
                "steps_mean": _mean(_float_or_none(row.get("steps")) for row in rows),
            }
        )
    return output


def combined_repeat_aggregate(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("training_repeat_id", ""))].append(row)
    return [_aggregate(grouped[repeat_id], repeat_id=repeat_id) for repeat_id in sorted(grouped)]


def profile_repeat_aggregate(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (str(row.get("training_repeat_id", "")), str(row.get("profile_name", "")))
        grouped[key].append(row)
    output: list[dict[str, Any]] = []
    for repeat_id, profile_name in sorted(grouped):
        output.append(_aggregate(grouped[(repeat_id, profile_name)], repeat_id=repeat_id, profile_name=profile_name))
    return output


def _row_signature(row: Mapping[str, Any], fields: Iterable[str]) -> tuple[Any, ...]:
    signature: list[Any] = []
    for field in fields:
        value = row.get(field, "")
        number = _float_or_none(value)
        signature.append(round(number, 12) if number is not None else str(value))
    return tuple(signature)


def _repeat_row_by_id(rows: list[Mapping[str, Any]], repeat_id: str) -> Mapping[str, Any] | None:
    for row in rows:
        if str(row.get("training_repeat_id", "")) == repeat_id:
            return row
    return None


def _profile_vector(rows: list[Mapping[str, Any]], repeat_id: str) -> tuple[tuple[Any, ...], ...]:
    fields = ("profile_name", "episode_count", "success_count", "collision_count", "offtrack_count")
    return tuple(
        _row_signature(row, fields)
        for row in rows
        if str(row.get("training_repeat_id", "")) == repeat_id
    )


def _sha256_or_missing(path_value: str) -> str:
    path = Path(path_value)
    if not path_value:
        return "missing"
    if not path.exists():
        return "not_found"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoint_hash_rows(workload_path: Path | str, *, default_repeat_id: str) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in read_csv_rows(workload_path):
        repeat_id = str(row.get("training_repeat_id", "")).strip() or default_repeat_id
        output.append(
            {
                "training_repeat_id": repeat_id,
                "profile_name": str(row.get("profile_name", "")),
                "workload_id": str(row.get("workload_id", "")),
                "base_workload_id": str(row.get("base_workload_id", row.get("workload_id", ""))),
                "checkpoint_path": str(row.get("checkpoint_path", "")),
                "checkpoint_sha256": _sha256_or_missing(str(row.get("checkpoint_path", ""))),
            }
        )
    return output


def checkpoint_duplicate_count(rows: list[Mapping[str, Any]], repeat_a: str, repeat_b: str) -> int:
    by_key: dict[tuple[str, str], str] = {}
    for row in rows:
        repeat_id = str(row.get("training_repeat_id", ""))
        profile = str(row.get("profile_name", ""))
        base_workload_id = str(row.get("base_workload_id", ""))
        by_key[(repeat_id, f"{base_workload_id}::{profile}")] = str(row.get("checkpoint_sha256", ""))
    duplicates = 0
    for repeat_id, key in list(by_key):
        if repeat_id != repeat_a:
            continue
        if by_key.get((repeat_b, key)) == by_key[(repeat_a, key)]:
            duplicates += 1
    return duplicates


def comparison_readiness_rows(*, comparison_ready: bool, outcome_support_pass: bool, seed_diversity_status: str) -> list[dict[str, Any]]:
    return [
        {
            "claim": "combined_repeat_execution_clean",
            "admissible": True,
            "reason": "M2174 and M2184 episode artifacts can be combined for audit.",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": bool(comparison_ready),
            "reason": (
                "combined support and seed diversity pass readiness checks"
                if comparison_ready
                else "ranking remains blocked until support and seed diversity pass"
            ),
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "This audit does not perform a denominator-backed comparison.",
        },
        {
            "claim": "paper_level_benchmark_evidence",
            "admissible": False,
            "reason": "This audit only decides readiness for later comparison design.",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "No history-necessity intervention is run.",
        },
        {
            "claim": "outcome_support_ready",
            "admissible": bool(outcome_support_pass),
            "reason": "support gates pass" if outcome_support_pass else "low support or high offtrack dominance",
        },
        {
            "claim": "seed_diversity_ready",
            "admissible": seed_diversity_status == "pass",
            "reason": seed_diversity_status,
        },
    ]


def run_repeat_seed_diversity_combined_outcome_audit(
    *,
    original_output_dir: Path | str = DEFAULT_ORIGINAL_OUTPUT_DIR,
    original_workload: Path | str = DEFAULT_ORIGINAL_WORKLOAD,
    repeat_output_dir: Path | str = DEFAULT_REPEAT_OUTPUT_DIR,
    repeat_workload: Path | str = DEFAULT_REPEAT_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    expected_combined_episode_count: int = 960,
    expected_repeat_count: int = 3,
    expected_per_repeat_count: int = 320,
    min_combined_success_count: int = 240,
    max_combined_offtrack_rate: float = 0.60,
    min_success_count_per_repeat: int = 80,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    original_rows = _annotated_episode_rows(original_output_dir, default_repeat_id=ORIGINAL_REPEAT_ID)
    repeat_rows = _annotated_episode_rows(repeat_output_dir, default_repeat_id="")
    combined_rows = [*original_rows, *repeat_rows]
    repeat_aggregate = combined_repeat_aggregate(combined_rows)
    profile_aggregate = profile_repeat_aggregate(combined_rows)
    checkpoint_rows = [
        *checkpoint_hash_rows(original_workload, default_repeat_id=ORIGINAL_REPEAT_ID),
        *checkpoint_hash_rows(repeat_workload, default_repeat_id=""),
    ]

    repeat_counts = {str(row["training_repeat_id"]): int(row["episode_count"]) for row in repeat_aggregate}
    combined_episode_count = len(combined_rows)
    combined_success_count = sum(int(row["success_count"]) for row in repeat_aggregate)
    combined_collision_count = sum(int(row["collision_count"]) for row in repeat_aggregate)
    combined_offtrack_count = sum(int(row["offtrack_count"]) for row in repeat_aggregate)
    combined_offtrack_rate = float(combined_offtrack_count / combined_episode_count) if combined_episode_count else 0.0
    repeat_count = len(repeat_counts)
    completeness_pass = (
        combined_episode_count == int(expected_combined_episode_count)
        and repeat_count == int(expected_repeat_count)
        and all(count == int(expected_per_repeat_count) for count in repeat_counts.values())
        and _summary_guardrail_violation_count(original_output_dir) == 0
        and _summary_guardrail_violation_count(repeat_output_dir) == 0
    )
    per_repeat_success_min = min((int(row["success_count"]) for row in repeat_aggregate), default=0)
    outcome_support_pass = (
        combined_success_count >= int(min_combined_success_count)
        and combined_offtrack_rate <= float(max_combined_offtrack_rate)
        and per_repeat_success_min >= int(min_success_count_per_repeat)
    )

    aggregate_fields = (
        "episode_count",
        "success_count",
        "collision_count",
        "offtrack_count",
        "success_rate",
        "collision_rate",
        "offtrack_rate",
        "clearance_margin_mean",
        "return_mean",
        "steps_mean",
    )
    repeat_1 = _repeat_row_by_id(repeat_aggregate, "repeat_1_seed_21761")
    repeat_2 = _repeat_row_by_id(repeat_aggregate, "repeat_2_seed_21762")
    repeat_aggregate_equal = bool(
        repeat_1 is not None
        and repeat_2 is not None
        and _row_signature(repeat_1, aggregate_fields) == _row_signature(repeat_2, aggregate_fields)
    )
    profile_vector_equal = _profile_vector(profile_aggregate, "repeat_1_seed_21761") == _profile_vector(
        profile_aggregate,
        "repeat_2_seed_21762",
    )
    duplicate_checkpoint_count = checkpoint_duplicate_count(checkpoint_rows, "repeat_1_seed_21761", "repeat_2_seed_21762")
    if duplicate_checkpoint_count:
        seed_diversity_status = "invalid_checkpoint_hash_duplicate"
    elif repeat_aggregate_equal or profile_vector_equal:
        seed_diversity_status = "suspicious_identical_repeat_outcome_vectors"
    else:
        seed_diversity_status = "pass"
    comparison_ready = bool(completeness_pass and outcome_support_pass and seed_diversity_status == "pass")
    result_class = (
        "current_sim_repeat_seed_diversity_combined_outcome_audit_comparison_ready"
        if comparison_ready
        else "current_sim_repeat_seed_diversity_combined_outcome_audit_not_comparison_ready"
    )
    diversity_flags = [
        {
            "check": "repeat_aggregate_equal_repeat_1_vs_repeat_2",
            "status": "fail" if repeat_aggregate_equal else "pass",
            "value": str(bool(repeat_aggregate_equal)).lower(),
            "details": "top-level aggregate vectors exactly match at audit precision",
        },
        {
            "check": "profile_vector_equal_repeat_1_vs_repeat_2",
            "status": "fail" if profile_vector_equal else "pass",
            "value": str(bool(profile_vector_equal)).lower(),
            "details": "per-profile outcome vectors exactly match",
        },
        {
            "check": "checkpoint_hash_duplicate_repeat_1_vs_repeat_2",
            "status": "fail" if duplicate_checkpoint_count else "pass",
            "value": str(int(duplicate_checkpoint_count)),
            "details": "matching checkpoint hashes across repeat_1 and repeat_2 by base workload/profile",
        },
        {
            "check": "outcome_support",
            "status": "pass" if outcome_support_pass else "fail",
            "value": str(bool(outcome_support_pass)).lower(),
            "details": "combined success/offtrack/per-repeat support readiness gate",
        },
        {
            "check": "comparison_ready",
            "status": "pass" if comparison_ready else "fail",
            "value": str(bool(comparison_ready)).lower(),
            "details": result_class,
        },
    ]
    write_csv_rows(output / "combined_repeat_aggregate.csv", repeat_aggregate, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "profile_repeat_outcome_aggregate.csv", profile_aggregate, fieldnames=PROFILE_REPEAT_FIELDNAMES)
    write_csv_rows(output / "checkpoint_hash_rows.csv", checkpoint_rows)
    write_csv_rows(output / "repeat_diversity_flags.csv", diversity_flags, fieldnames=DIVERSITY_FIELDNAMES)
    write_csv_rows(
        output / "comparison_readiness_claim_boundary.csv",
        comparison_readiness_rows(
            comparison_ready=comparison_ready,
            outcome_support_pass=outcome_support_pass,
            seed_diversity_status=seed_diversity_status,
        ),
        fieldnames=CLAIM_FIELDNAMES,
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "combined_episode_count": combined_episode_count,
        "expected_combined_episode_count": int(expected_combined_episode_count),
        "repeat_count": repeat_count,
        "expected_repeat_count": int(expected_repeat_count),
        "repeat_counts": repeat_counts,
        "expected_per_repeat_count": int(expected_per_repeat_count),
        "combined_success_count": combined_success_count,
        "combined_collision_count": combined_collision_count,
        "combined_offtrack_count": combined_offtrack_count,
        "combined_success_rate": float(combined_success_count / combined_episode_count) if combined_episode_count else 0.0,
        "combined_collision_rate": float(combined_collision_count / combined_episode_count) if combined_episode_count else 0.0,
        "combined_offtrack_rate": combined_offtrack_rate,
        "per_repeat_success_min": per_repeat_success_min,
        "min_combined_success_count": int(min_combined_success_count),
        "max_combined_offtrack_rate": float(max_combined_offtrack_rate),
        "min_success_count_per_repeat": int(min_success_count_per_repeat),
        "completeness_pass": completeness_pass,
        "outcome_support_pass": outcome_support_pass,
        "repeat_aggregate_equal": repeat_aggregate_equal,
        "profile_vector_equal": profile_vector_equal,
        "checkpoint_duplicate_count": duplicate_checkpoint_count,
        "seed_diversity_status": seed_diversity_status,
        "comparison_ready": comparison_ready,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "combined_repeat_aggregate": str(output / "combined_repeat_aggregate.csv"),
            "profile_repeat_outcome_aggregate": str(output / "profile_repeat_outcome_aggregate.csv"),
            "checkpoint_hash_rows": str(output / "checkpoint_hash_rows.csv"),
            "repeat_diversity_flags": str(output / "repeat_diversity_flags.csv"),
            "comparison_readiness_claim_boundary": str(output / "comparison_readiness_claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": "m2188-paper-route-current-sim-repeat-seed-diversity-and-combined-outcome-audit-result-audit",
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "complete": True,
            "combined_episode_count": combined_episode_count,
            "comparison_ready": comparison_ready,
            "result_class": result_class,
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-output-dir", type=Path, default=DEFAULT_ORIGINAL_OUTPUT_DIR)
    parser.add_argument("--original-workload", type=Path, default=DEFAULT_ORIGINAL_WORKLOAD)
    parser.add_argument("--repeat-output-dir", type=Path, default=DEFAULT_REPEAT_OUTPUT_DIR)
    parser.add_argument("--repeat-workload", type=Path, default=DEFAULT_REPEAT_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    summary = run_repeat_seed_diversity_combined_outcome_audit(
        original_output_dir=args.original_output_dir,
        original_workload=args.original_workload,
        repeat_output_dir=args.repeat_output_dir,
        repeat_workload=args.repeat_workload,
        output_dir=args.output_dir,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"combined_episode_count={summary['combined_episode_count']}")
    print(f"comparison_ready={summary['comparison_ready']}")
    print(f"seed_diversity_status={summary['seed_diversity_status']}")


if __name__ == "__main__":
    main()
