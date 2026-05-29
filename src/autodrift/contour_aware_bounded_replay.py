"""Bounded replay over contour-aware primary rows and diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_terminal_boundary_history_interventions import AnchorReplayState, replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.history_pairability_source_miner import build_pairability_anchor_candidates, pairability_source_specs
from autodrift.history_vs_control_active_set_selector import classify_rows, group_summary, label_summary
from autodrift.source_diverse_flip_anchor_history_interventions import (
    DonorPair,
    _failure_row,
    build_variant_summary,
    finalize_rows,
    run_intervention_variant,
)
from autodrift.source_diverse_pairability_history_interventions import LEGACY_TO_M1585_VARIANT, VARIANTS, _legacy_variant, read_csv_rows
from autodrift.temporal_active_set_anchor_sensitivity_miner import AnchorCandidate, _finite_float, _max_share


DEFAULT_RUN_DIR = Path("runs/m1605_contour_aware_bounded_replay")
DEFAULT_PRIMARY_ROWS = Path("runs/m1602_contour_aware_source_rule/primary_rule_rows.csv")
DEFAULT_DIAGNOSTIC_ROWS = Path("runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv")
CLEAN_LABEL = "history_control_separated"
DOMINATED_LABEL = "history_positive_control_dominated"
CONTROL_ONLY_LABEL = "control_only_positive"
MIXED_DIAGNOSTIC_REASON = "mixed_dominated_edge"
NEGATIVE_DIAGNOSTIC_REASON = "negative_diagnostic_edge"
ENDPOINT_NEIGHBOR_REASON = "endpoint_neighbor_exclusion"
DIAGNOSTIC_REASONS = (ENDPOINT_NEIGHBOR_REASON, NEGATIVE_DIAGNOSTIC_REASON, MIXED_DIAGNOSTIC_REASON)
FORBIDDEN_GUARDRAILS = {
    "candidate_materialized": False,
    "training_started": False,
    "evaluation_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "training_corpus_exported": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _int_value(value: Any) -> int:
    return int(float(value or 0))


def _source_edge(row: Mapping[str, Any]) -> str:
    return str(row.get("source_edge", ""))


def _row_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        str(row.get("rule_reason", "")),
        str(row.get("source_run", "")),
        str(row.get("source_edge", "")),
        str(row.get("pair_id", "")),
    )


def _replay_pair_id(row: Mapping[str, Any]) -> str:
    pair_id = str(row.get("pair_id", ""))
    source_run = str(row.get("source_run", ""))
    if source_run:
        return f"{source_run}::{pair_id}"
    return pair_id


def select_diagnostic_replay_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    per_reason_cap: int = 32,
) -> list[dict[str, Any]]:
    """Select bounded diagnostic controls with source-rule reason coverage."""

    selected: list[dict[str, Any]] = []
    for reason in DIAGNOSTIC_REASONS:
        group = [dict(row) for row in rows if str(row.get("rule_reason", "")) == reason]
        group.sort(key=_row_sort_key)
        selected.extend(group[: max(0, int(per_reason_cap))])
    return selected


def directed_pairs_from_rows(rows: Sequence[Mapping[str, Any]]) -> list[DonorPair]:
    """Build replay pairs from already-directed M1602 contour rows."""

    pairs: list[DonorPair] = []
    for row in rows:
        target_step = _int_value(row.get("target_anchor_step"))
        donor_step = _int_value(row.get("donor_anchor_step"))
        target_family = str(row.get("target_source_family", ""))
        donor_family = str(row.get("donor_source_family", ""))
        pairs.append(
            DonorPair(
                pair_id=_replay_pair_id(row),
                target_anchor_id=str(row.get("target_anchor_id", "")),
                donor_anchor_id=str(row.get("donor_anchor_id", "")),
                target_source_family=target_family,
                donor_source_family=donor_family,
                target_anchor_window=str(row.get("target_anchor_window", "")),
                donor_anchor_window=str(row.get("donor_anchor_window", "")),
                target_anchor_step=target_step,
                donor_anchor_step=donor_step,
                same_window=_parse_bool(row.get("same_window", False)),
                step_distance=abs(target_step - donor_step),
                contrasting_normal_outcome=False,
                diagnostic_late_reveal=target_family == "late_reveal_boundary" or donor_family == "late_reveal_boundary",
                donor_rank=1,
            )
        )
    return pairs


def _meta_by_pair(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    for row in rows:
        pair_id = _replay_pair_id(row)
        meta[pair_id] = {
            "source_run": str(row.get("source_run", "")),
            "contour_pair_id": str(row.get("pair_id", "")),
            "selected_pair_id": str(row.get("selected_pair_id", "")),
            "original_pair_id": str(row.get("original_pair_id", "")),
            "source_edge": str(row.get("source_edge", "")),
            "selection_source": str(row.get("selection_source", "")),
            "rule_bucket": str(row.get("rule_bucket", "")),
            "rule_reason": str(row.get("rule_reason", "")),
            "pair_response_action_l2": _finite_float(row.get("pair_response_action_l2")),
            "pair_context_l2": _finite_float(row.get("pair_context_l2")),
            "pair_hidden_l2": _finite_float(row.get("pair_hidden_l2")),
            "m1602_label": str(row.get("label", "")),
        }
    return meta


def _translate_rows(rows: Sequence[dict[str, Any]], meta_by_pair: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    translated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        legacy = str(item.get("variant", ""))
        item["legacy_variant"] = legacy
        item["variant"] = LEGACY_TO_M1585_VARIANT.get(legacy, legacy)
        item.update(meta_by_pair.get(str(item.get("pair_id", "")), {}))
        translated.append(item)
    return translated


def _annotate_classified_rows(rows: Sequence[dict[str, Any]], meta_by_pair: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item.update(meta_by_pair.get(str(row.get("pair_id", "")), {}))
        annotated.append(item)
    return annotated


def _label_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("label", "")) for row in rows)


def _clean_source_edge_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(_source_edge(row) for row in rows if str(row.get("label", "")) == CLEAN_LABEL and _source_edge(row))


def _rule_reason_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return len({str(row.get("rule_reason", "")) for row in rows if str(row.get("rule_reason", ""))})


def _leak_count(rows: Sequence[Mapping[str, Any]], reason: str) -> int:
    return sum(1 for row in rows if str(row.get("rule_reason", "")) == reason)


def build_summary(
    *,
    primary_replay_rows: Sequence[Mapping[str, Any]],
    diagnostic_replay_rows: Sequence[Mapping[str, Any]],
    intervention_rows: Sequence[Mapping[str, Any]],
    classified_rows: Sequence[dict[str, Any]],
    continuation_steps: int,
) -> dict[str, Any]:
    """Build the M1605 bounded replay summary."""

    primary_ids = {_replay_pair_id(row) for row in primary_replay_rows}
    diagnostic_ids = {_replay_pair_id(row) for row in diagnostic_replay_rows}
    primary_classified = [row for row in classified_rows if str(row.get("pair_id", "")) in primary_ids]
    diagnostic_classified = [row for row in classified_rows if str(row.get("pair_id", "")) in diagnostic_ids]
    primary_label_counts = _label_counts(primary_classified)
    diagnostic_label_counts = _label_counts(diagnostic_classified)
    primary_clean_source_edge_counts = _clean_source_edge_counts(primary_classified)
    diagnostic_clean_share = (
        diagnostic_label_counts.get(CLEAN_LABEL, 0) / len(diagnostic_classified)
        if diagnostic_classified
        else 0.0
    )
    invalid_count = _label_counts(classified_rows).get("replay_or_metric_invalid", 0)
    anchor_replay_failure_count = len(
        {
            str(row.get("pair_id", ""))
            for row in intervention_rows
            if str(row.get("target_replay_status", "")) != "ok"
        }
    )
    variant_set = {str(row.get("variant", "")) for row in intervention_rows}
    required_variant_coverage_complete = invalid_count == 0 and set(VARIANTS).issubset(variant_set)
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "contour_aware_bounded_replay",
        "primary_replay_directed_pair_count": len(primary_replay_rows),
        "diagnostic_replay_directed_pair_count": len(diagnostic_replay_rows),
        "diagnostic_reason_count": _rule_reason_count(diagnostic_replay_rows),
        "primary_source_run_count": len({str(row.get("source_run", "")) for row in primary_replay_rows if str(row.get("source_run", ""))}),
        "primary_source_edge_count": len({_source_edge(row) for row in primary_replay_rows if _source_edge(row)}),
        "primary_clean_directed_pair_count": primary_label_counts.get(CLEAN_LABEL, 0),
        "primary_clean_source_edge_count": len(primary_clean_source_edge_counts),
        "max_primary_clean_source_edge_share": _max_share(primary_clean_source_edge_counts),
        "endpoint_neighbor_primary_count": _leak_count(primary_classified, ENDPOINT_NEIGHBOR_REASON),
        "negative_diagnostic_primary_count": _leak_count(primary_classified, NEGATIVE_DIAGNOSTIC_REASON),
        "mixed_diagnostic_primary_count": _leak_count(primary_classified, MIXED_DIAGNOSTIC_REASON),
        "diagnostic_dominated_or_control_count": diagnostic_label_counts.get(DOMINATED_LABEL, 0) + diagnostic_label_counts.get(CONTROL_ONLY_LABEL, 0),
        "diagnostic_clean_directed_pair_count": diagnostic_label_counts.get(CLEAN_LABEL, 0),
        "diagnostic_clean_share": diagnostic_clean_share,
        "classified_directed_pair_count": len(classified_rows),
        "intervention_row_count": len(intervention_rows),
        "variant_count": len(variant_set),
        "required_variant_coverage_complete": bool(required_variant_coverage_complete),
        "anchor_replay_failure_count": anchor_replay_failure_count,
        "invalid_directed_pair_count": invalid_count,
        "primary_label_counts": dict(sorted(primary_label_counts.items())),
        "diagnostic_label_counts": dict(sorted(diagnostic_label_counts.items())),
        "continuation_steps": int(continuation_steps),
        "history_interventions_executed": True,
        "replay_started": True,
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["primary_replay_directed_pair_count"]) >= 144
        and int(summary["diagnostic_replay_directed_pair_count"]) >= 72
        and int(summary["diagnostic_reason_count"]) >= 3
        and int(summary["primary_source_run_count"]) >= 2
        and int(summary["primary_source_edge_count"]) == 4
        and int(summary["primary_clean_directed_pair_count"]) >= 39
        and int(summary["primary_clean_source_edge_count"]) >= 4
        and float(summary["max_primary_clean_source_edge_share"]) <= 0.35
        and int(summary["endpoint_neighbor_primary_count"]) == 0
        and int(summary["negative_diagnostic_primary_count"]) == 0
        and int(summary["mixed_diagnostic_primary_count"]) == 0
        and int(summary["diagnostic_dominated_or_control_count"]) >= 50
        and float(summary["diagnostic_clean_share"]) <= 0.05
        and bool(summary["required_variant_coverage_complete"])
        and int(summary["anchor_replay_failure_count"]) <= 8
        and int(summary["guardrail_violation_count"]) == 0
        and bool(summary["history_interventions_executed"])
        and bool(summary["replay_started"])
        and not bool(summary["candidate_materialized"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["training_corpus_exported"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
    )
    summary["passes_evidence_quality_targets"] = bool(summary["passes_public_smoke_gates"])
    if not required_variant_coverage_complete:
        null_class = "variant_coverage_failure"
    elif anchor_replay_failure_count > 8:
        null_class = "anchor_replay_failure"
    elif int(summary["primary_clean_directed_pair_count"]) < 39:
        null_class = "primary_clean_shortfall"
    elif float(summary["max_primary_clean_source_edge_share"]) > 0.35:
        null_class = "source_share_failure"
    elif float(summary["diagnostic_clean_share"]) > 0.05:
        null_class = "diagnostic_clean_leakage"
    elif int(summary["diagnostic_dominated_or_control_count"]) < 50:
        null_class = "diagnostic_control_failure"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_bounded_replay_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    return summary


def _run_anchor_replays(
    pairs: Sequence[DonorPair],
    *,
    checkpoint: Path | str,
    seed: int,
    seed_count: int,
    max_source_specs: int,
    max_anchor_candidates: int,
    continuation_steps: int,
    device: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    specs = pairability_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    candidates = build_pairability_anchor_candidates(specs, max_anchors=max_anchor_candidates)
    specs_by_id = {str(spec.artifact_row.calibration_id): spec for spec in specs}
    candidates_by_id: dict[str, AnchorCandidate] = {candidate.anchor_id: candidate for candidate in candidates}
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    needed_anchor_ids = {pair.target_anchor_id for pair in pairs} | {pair.donor_anchor_id for pair in pairs}
    replays: dict[str, AnchorReplayState] = {}
    for anchor_id in sorted(needed_anchor_ids):
        candidate = candidates_by_id.get(anchor_id)
        if candidate is None:
            continue
        spec = specs_by_id.get(candidate.calibration_id)
        if spec is None:
            continue
        replays[anchor_id] = replay_to_anchor(
            pair_id=anchor_id,
            side="anchor",
            spec=spec,
            anchor_step=int(candidate.anchor_step),
            model=model,
        )
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        target = replays.get(pair.target_anchor_id)
        donor = replays.get(pair.donor_anchor_id)
        if target is None:
            for variant in VARIANTS:
                rows.append(_failure_row(pair=pair, variant=_legacy_variant(variant), target_status="missing_target_spec", donor_status="not_run"))
            continue
        for variant in VARIANTS:
            rows.append(
                run_intervention_variant(
                    pair=pair,
                    target=target,
                    donor=donor,
                    variant=_legacy_variant(variant),
                    model=model,
                    continuation_steps=continuation_steps,
                )
            )
    anchor_rows = [
        {
            "anchor_id": anchor_id,
            "replay_status": "ok" if replay.reached_anchor else replay.first_failure,
            "anchor_step": replay.anchor_step,
            "source_family": replay.spec.source_row.source_family,
            "hidden_norm": float(np.linalg.norm(replay.hidden.detach().cpu().numpy())) if replay.hidden is not None else 0.0,
            "error_type": replay.error_type,
            "error_message": replay.error_message,
        }
        for anchor_id, replay in sorted(replays.items())
    ]
    spec_rows = [asdict(spec.artifact_row) for spec in specs]
    return rows, anchor_rows, spec_rows


def run_contour_aware_bounded_replay(
    output_dir: Path | str,
    *,
    primary_rows: Path | str = DEFAULT_PRIMARY_ROWS,
    diagnostic_rows: Path | str = DEFAULT_DIAGNOSTIC_ROWS,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1901,
    seed_count: int = 6,
    max_source_specs: int = 480,
    max_anchor_candidates: int = 640,
    diagnostic_per_reason_cap: int = 32,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded contour-aware replay over public primary and diagnostic rows."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    primary = read_csv_rows(primary_rows)
    diagnostics = select_diagnostic_replay_rows(read_csv_rows(diagnostic_rows), per_reason_cap=diagnostic_per_reason_cap)
    replay_rows = [dict(row, replay_bucket="primary") for row in primary] + [dict(row, replay_bucket="diagnostic") for row in diagnostics]
    pairs = directed_pairs_from_rows(replay_rows)
    meta_by_pair = _meta_by_pair(replay_rows)
    raw_rows, anchor_rows, spec_rows = _run_anchor_replays(
        pairs,
        checkpoint=checkpoint,
        seed=seed,
        seed_count=seed_count,
        max_source_specs=max_source_specs,
        max_anchor_candidates=max_anchor_candidates,
        continuation_steps=continuation_steps,
        device=device,
    )
    intervention_rows = _translate_rows(finalize_rows(raw_rows), meta_by_pair)
    classified_rows = _annotate_classified_rows(classify_rows(intervention_rows), meta_by_pair)
    primary_ids = {_replay_pair_id(row) for row in primary}
    diagnostic_ids = {_replay_pair_id(row) for row in diagnostics}
    primary_classified = [row for row in classified_rows if str(row.get("pair_id", "")) in primary_ids]
    diagnostic_classified = [row for row in classified_rows if str(row.get("pair_id", "")) in diagnostic_ids]
    summary = build_summary(
        primary_replay_rows=primary,
        diagnostic_replay_rows=diagnostics,
        intervention_rows=intervention_rows,
        classified_rows=classified_rows,
        continuation_steps=continuation_steps,
    )

    write_csv_rows(output / "replay_pair_rows.csv", [asdict(pair) | meta_by_pair.get(pair.pair_id, {}) for pair in pairs])
    write_csv_rows(output / "source_spec_rows.csv", spec_rows)
    write_csv_rows(output / "anchor_replay_rows.csv", anchor_rows)
    write_csv_rows(output / "intervention_rows.csv", intervention_rows)
    write_csv_rows(output / "classified_directed_pair_rows.csv", classified_rows)
    write_csv_rows(output / "primary_classified_rows.csv", primary_classified)
    write_csv_rows(output / "diagnostic_classified_rows.csv", diagnostic_classified)
    write_csv_rows(output / "primary_source_edge_summary.csv", group_summary(primary_classified, "source_edge"))
    write_csv_rows(output / "diagnostic_rule_reason_summary.csv", group_summary(diagnostic_classified, "rule_reason"))
    write_csv_rows(output / "label_summary.csv", label_summary(classified_rows))
    write_csv_rows(output / "variant_summary.csv", build_variant_summary(intervention_rows))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in FORBIDDEN_GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded contour-aware replay.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--primary-rows", type=Path, default=DEFAULT_PRIMARY_ROWS)
    parser.add_argument("--diagnostic-rows", type=Path, default=DEFAULT_DIAGNOSTIC_ROWS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1901)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=480)
    parser.add_argument("--max-anchor-candidates", type=int, default=640)
    parser.add_argument("--diagnostic-per-reason-cap", type=int, default=32)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_contour_aware_bounded_replay(
        args.output_dir,
        primary_rows=args.primary_rows,
        diagnostic_rows=args.diagnostic_rows,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchor_candidates=int(args.max_anchor_candidates),
        diagnostic_per_reason_cap=int(args.diagnostic_per_reason_cap),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"primary_replay_directed_pair_count={summary['primary_replay_directed_pair_count']}")
    print(f"primary_clean_directed_pair_count={summary['primary_clean_directed_pair_count']}")
    print(f"diagnostic_replay_directed_pair_count={summary['diagnostic_replay_directed_pair_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
