"""Source/variant traceability preflight before policy-target materialization."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE


DEFAULT_CANDIDATE_RUN_DIR = Path("runs/m1615_contour_aware_candidate_corpus")
DEFAULT_REPLAY_RUN_DIR = Path("runs/m1609_diagnostic_complete_bounded_replay")
DEFAULT_RUN_DIR = Path("runs/m1623_contour_aware_policy_target_traceability_preflight")
REQUIRED_VARIANTS = (
    "normal",
    "wrong_history_hidden",
    "donor_response_action_plus_hidden",
)
SOURCE_RUN_DIRS = {
    "m1588_selector": Path("runs/m1588_history_vs_control_active_set_selector"),
    "m1592_clean_repair": Path("runs/m1592_clean_history_control_source_generation_repair_smoke"),
    "m1595_balanced_repair": Path("runs/m1595_selector_balanced_clean_source_repair_smoke"),
}
FORBIDDEN_GUARDRAILS = {
    "tensor_target_materialized": False,
    "training_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "level3_self_id_claim_made": False,
    "loss_constructed": False,
    "objective_constructed": False,
}


def _variant_index(intervention_rows: Sequence[Mapping[str, Any]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = defaultdict(set)
    for row in intervention_rows:
        index[str(row.get("pair_id", ""))].add(str(row.get("variant", "")))
    return index


def _source_dir(source_run: str) -> Path | None:
    return SOURCE_RUN_DIRS.get(source_run)


def _traceability_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    role: str,
    replay_pair_ids: set[str],
    variants_by_pair: Mapping[str, set[str]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        pair_id = str(row.get("pair_id", ""))
        source_run = str(row.get("source_run", ""))
        source_dir = _source_dir(source_run)
        variant_flags = {f"{variant}_variant_match": variant in variants_by_pair.get(pair_id, set()) for variant in REQUIRED_VARIANTS}
        replay_match = pair_id in replay_pair_ids
        source_resolved = source_dir is not None and source_dir.exists()
        output.append(
            {
                "pair_id": pair_id,
                "corpus_role": role,
                "source_run": source_run,
                "source_run_dir": str(source_dir) if source_dir is not None else "",
                "source_run_resolved": bool(source_resolved),
                "replay_pair_match": bool(replay_match),
                **variant_flags,
                "all_required_variants_match": all(variant_flags.values()),
                "diagnostic_rows_used_as_positive": False if role == DIAGNOSTIC_ROLE else "",
                "used_as_positive": role == POSITIVE_ROLE,
                "source_edge": str(row.get("source_edge", "")),
                "contour_pair_id": str(row.get("contour_pair_id", "")),
                "selected_pair_id": str(row.get("selected_pair_id", "")),
                "original_pair_id": str(row.get("original_pair_id", "")),
                "target_anchor_id": str(row.get("target_anchor_id", "")),
                "donor_anchor_id": str(row.get("donor_anchor_id", "")),
            }
        )
    return output


def _source_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("source_run", "")) for row in rows)
    output: list[dict[str, Any]] = []
    for source_run, count in sorted(counts.items()):
        source_dir = _source_dir(source_run)
        output.append(
            {
                "source_run": source_run,
                "source_run_dir": str(source_dir) if source_dir is not None else "",
                "row_count": count,
                "source_run_resolved": bool(source_dir is not None and source_dir.exists()),
            }
        )
    return output


def _variant_summary(rows: Sequence[Mapping[str, Any]], *, role: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for variant in REQUIRED_VARIANTS:
        key = f"{variant}_variant_match"
        count = sum(bool(row.get(key, False)) for row in rows)
        output.append(
            {
                "corpus_role": role,
                "variant": variant,
                "row_count": len(rows),
                "match_count": count,
                "match_fraction": count / len(rows) if rows else 0.0,
            }
        )
    return output


def _missing_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for row in rows:
        reasons = []
        if not bool(row.get("source_run_resolved", False)):
            reasons.append("source_run_unresolved")
        if not bool(row.get("replay_pair_match", False)):
            reasons.append("replay_pair_missing")
        for variant in REQUIRED_VARIANTS:
            if not bool(row.get(f"{variant}_variant_match", False)):
                reasons.append(f"{variant}_missing")
        if reasons:
            missing.append(
                {
                    "pair_id": row.get("pair_id", ""),
                    "corpus_role": row.get("corpus_role", ""),
                    "source_run": row.get("source_run", ""),
                    "missing_reasons": "|".join(reasons),
                }
            )
    return missing


def run_contour_aware_policy_target_traceability_preflight(
    *,
    candidate_run_dir: Path | str,
    replay_run_dir: Path | str,
    run_dir: Path | str,
) -> dict[str, Any]:
    """Run a no-materialization source/variant traceability preflight."""

    candidate_dir = Path(candidate_run_dir)
    replay_dir = Path(replay_run_dir)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)

    positive_rows = read_csv_rows(candidate_dir / "positive_candidate_rows.csv")
    diagnostic_rows = read_csv_rows(candidate_dir / "diagnostic_guardrail_rows.csv")
    replay_pair_rows = read_csv_rows(replay_dir / "replay_pair_rows.csv")
    intervention_rows = read_csv_rows(replay_dir / "intervention_rows.csv")
    replay_pair_ids = {str(row.get("pair_id", "")) for row in replay_pair_rows}
    variants_by_pair = _variant_index(intervention_rows)

    positive_trace = _traceability_rows(
        positive_rows,
        role=POSITIVE_ROLE,
        replay_pair_ids=replay_pair_ids,
        variants_by_pair=variants_by_pair,
    )
    diagnostic_trace = _traceability_rows(
        diagnostic_rows,
        role=DIAGNOSTIC_ROLE,
        replay_pair_ids=replay_pair_ids,
        variants_by_pair=variants_by_pair,
    )
    all_trace_rows = positive_trace + diagnostic_trace
    source_rows = _source_summary(all_trace_rows)
    variant_rows = _variant_summary(positive_trace, role=POSITIVE_ROLE) + _variant_summary(
        diagnostic_trace,
        role=DIAGNOSTIC_ROLE,
    )
    missing_rows = _missing_rows(all_trace_rows)

    diagnostic_ids = {str(row.get("pair_id", "")) for row in diagnostic_rows}
    positive_ids = {str(row.get("pair_id", "")) for row in positive_rows}
    diagnostic_rows_used_as_positive = bool(positive_ids & diagnostic_ids) or any(
        str(row.get("corpus_role", "")) == POSITIVE_ROLE for row in diagnostic_rows
    )
    source_run_resolution_failure_count = sum(not bool(row.get("source_run_resolved", False)) for row in all_trace_rows)
    positive_replay_pair_match_count = sum(bool(row.get("replay_pair_match", False)) for row in positive_trace)
    diagnostic_replay_pair_match_count = sum(bool(row.get("replay_pair_match", False)) for row in diagnostic_trace)
    positive_variant_counts = {
        f"positive_{variant}_variant_match_count": sum(
            bool(row.get(f"{variant}_variant_match", False)) for row in positive_trace
        )
        for variant in REQUIRED_VARIANTS
    }
    diagnostic_variant_counts = {
        f"diagnostic_{variant}_variant_match_count": sum(
            bool(row.get(f"{variant}_variant_match", False)) for row in diagnostic_trace
        )
        for variant in REQUIRED_VARIANTS
    }
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "contour_aware_policy_target_traceability_preflight",
        "candidate_run_dir": str(candidate_dir),
        "replay_run_dir": str(replay_dir),
        "positive_candidate_count": len(positive_rows),
        "diagnostic_guardrail_count": len(diagnostic_rows),
        "source_run_resolution_failure_count": int(source_run_resolution_failure_count),
        "positive_replay_pair_match_count": int(positive_replay_pair_match_count),
        "diagnostic_replay_pair_match_count": int(diagnostic_replay_pair_match_count),
        **positive_variant_counts,
        **diagnostic_variant_counts,
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "missing_traceability_row_count": len(missing_rows),
        "guardrail_violation_count": int(guardrail_violation_count),
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["positive_candidate_count"]) == 39
        and int(summary["diagnostic_guardrail_count"]) == 232
        and int(summary["source_run_resolution_failure_count"]) == 0
        and int(summary["positive_replay_pair_match_count"]) == 39
        and int(summary["positive_normal_variant_match_count"]) == 39
        and int(summary["positive_wrong_history_hidden_variant_match_count"]) == 39
        and int(summary["positive_donor_response_action_plus_hidden_variant_match_count"]) == 39
        and not bool(summary["diagnostic_rows_used_as_positive"])
        and not bool(summary["tensor_target_materialized"])
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["level3_self_id_claim_made"])
    )
    if int(summary["source_run_resolution_failure_count"]) > 0:
        null_class = "source_run_resolution_failure"
    elif int(summary["positive_replay_pair_match_count"]) != 39:
        null_class = "positive_replay_pair_traceability_failure"
    elif any(int(summary[f"positive_{variant}_variant_match_count"]) != 39 for variant in REQUIRED_VARIANTS):
        null_class = "positive_variant_traceability_failure"
    elif bool(summary["diagnostic_rows_used_as_positive"]):
        null_class = "diagnostic_positive_leakage"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_policy_target_traceability_preflight_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class

    write_csv_rows(output / "positive_traceability_rows.csv", positive_trace)
    write_csv_rows(output / "diagnostic_traceability_rows.csv", diagnostic_trace)
    write_csv_rows(output / "source_run_resolution_summary.csv", source_rows)
    write_csv_rows(output / "variant_availability_summary.csv", variant_rows)
    write_csv_rows(
        output / "missing_traceability_rows.csv",
        missing_rows,
        fieldnames=["pair_id", "corpus_role", "source_run", "missing_reasons"],
    )
    guardrail_rows = [{"guardrail": key, "violated": value, "value": value} for key, value in FORBIDDEN_GUARDRAILS.items()]
    guardrail_rows.append({"guardrail": "diagnostic_rows_used_as_positive", "violated": diagnostic_rows_used_as_positive, "value": diagnostic_rows_used_as_positive})
    write_csv_rows(output / "guardrail_summary.csv", guardrail_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contour-aware policy target traceability preflight.")
    parser.add_argument("--candidate-run-dir", type=Path, default=DEFAULT_CANDIDATE_RUN_DIR)
    parser.add_argument("--replay-run-dir", type=Path, default=DEFAULT_REPLAY_RUN_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    summary = run_contour_aware_policy_target_traceability_preflight(
        candidate_run_dir=args.candidate_run_dir,
        replay_run_dir=args.replay_run_dir,
        run_dir=args.run_dir,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"positive_candidate_count={summary['positive_candidate_count']}")
    print(f"diagnostic_guardrail_count={summary['diagnostic_guardrail_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
