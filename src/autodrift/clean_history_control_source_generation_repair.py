"""Clean history-vs-control source-generation repair smoke."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_terminal_boundary_history_interventions import AnchorReplayState, replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.history_pairability_source_miner import build_pairability_anchor_candidates, pairability_source_specs
from autodrift.history_vs_control_active_set_selector import classify_rows, group_summary, label_summary
from autodrift.source_diverse_flip_anchor_history_interventions import (
    _failure_row,
    build_variant_summary,
    finalize_rows,
    run_intervention_variant,
)
from autodrift.source_diverse_pairability_history_interventions import (
    VARIANTS,
    _legacy_variant,
    _parse_bool,
    _selected_meta_by_directed_pair,
    _source_edge,
    _translate_finalized_rows,
    build_directed_pairs,
    read_csv_rows,
)
from autodrift.temporal_active_set_anchor_sensitivity_miner import _asdict_rows, _finite_float, _max_share


DEFAULT_RUN_DIR = Path("runs/m1592_clean_history_control_source_generation_repair_smoke")
DEFAULT_PAIR_ROWS = Path("runs/m1582_history_pairability_source_miner_smoke/pairability_pair_rows.csv")
DEFAULT_CLEAN_ROWS = Path("runs/m1588_history_vs_control_active_set_selector/clean_directed_pair_rows.csv")
CLEAN_LABEL = "history_control_separated"
CLEAN_TARGET_COUNT = 12
CLEAN_SOURCE_EDGE_TARGET = 5
CLEAN_ENDPOINT_FAMILY_TARGET = 6
MAX_CLEAN_SOURCE_EDGE_SHARE = 0.35
SOURCE_EDGE_CAP = 16
ENDPOINT_FAMILY_CAP = 56
WINDOW_CAP = 48
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
NEGATIVE_DIAGNOSTIC_EDGES = {
    "capability_step_up|t5_near_boundary_warmup",
    "capability_step_up|curved_boundary_obstacle",
    "capability_step_up|t5_boundary_axis_retarget",
    "capability_step_down|drive_loss_proxy",
    "capability_step_down|capability_step_up",
}


def _endpoint_families(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("left_source_family", "")), str(row.get("right_source_family", ""))


def _endpoint_windows(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("left_anchor_window", "")), str(row.get("right_anchor_window", ""))


def clean_source_edge_windows(clean_rows: Sequence[Mapping[str, Any]]) -> dict[str, set[str]]:
    """Return source-edge to clean endpoint-window set from selector rows."""

    result: dict[str, set[str]] = defaultdict(set)
    for row in clean_rows:
        edge = str(row.get("source_edge", ""))
        if not edge:
            continue
        for key in ("target_anchor_window", "donor_anchor_window"):
            window = str(row.get(key, ""))
            if window:
                result[edge].add(window)
    return dict(result)


def _shares_clean_endpoint(row: Mapping[str, Any], clean_families: set[str]) -> bool:
    left, right = _endpoint_families(row)
    return left in clean_families or right in clean_families


def _selection_rank(row: Mapping[str, Any], clean_windows_by_edge: Mapping[str, set[str]], clean_families: set[str]) -> tuple[Any, ...]:
    edge = _source_edge(row)
    windows = set(_endpoint_windows(row))
    clean_windows = set(clean_windows_by_edge.get(edge, set()))
    if edge in clean_windows_by_edge and windows & clean_windows:
        class_rank = 0
    elif edge in clean_windows_by_edge:
        class_rank = 1
    elif edge in NEGATIVE_DIAGNOSTIC_EDGES:
        class_rank = 2
    elif _shares_clean_endpoint(row, clean_families):
        class_rank = 3
    else:
        class_rank = 4
    return (
        class_rank,
        0 if _parse_bool(row.get("same_window", False)) else 1,
        _finite_float(row.get("response_action_l2"), default=1e9),
        -_finite_float(row.get("hidden_l2"), default=0.0),
        _finite_float(row.get("context_l2"), default=1e9),
        edge,
        str(row.get("pair_id", "")),
    )


def select_clean_source_repair_pairability_rows(
    pair_rows: Sequence[Mapping[str, Any]],
    clean_rows: Sequence[Mapping[str, Any]],
    *,
    max_selected_pairs: int = 96,
    max_pairs_per_source_edge: int = SOURCE_EDGE_CAP,
    max_pairs_per_endpoint_family: int = ENDPOINT_FAMILY_CAP,
    max_pairs_per_window: int = WINDOW_CAP,
) -> list[dict[str, Any]]:
    """Select pairability rows around clean source edges plus negative diagnostics."""

    clean_windows_by_edge = clean_source_edge_windows(clean_rows)
    clean_families = {
        str(row.get(key, ""))
        for row in clean_rows
        for key in ("target_source_family", "donor_source_family")
        if str(row.get(key, ""))
    }
    eligible = [
        dict(row)
        for row in pair_rows
        if _parse_bool(row.get("tier_a_strict", False)) and _parse_bool(row.get("context_ok", False))
    ]
    eligible.sort(key=lambda row: _selection_rank(row, clean_windows_by_edge, clean_families))
    selected: list[dict[str, Any]] = []
    source_edge_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    window_counts: Counter[str] = Counter()
    seen_pair_ids: set[str] = set()
    for row in eligible:
        if len(selected) >= int(max_selected_pairs):
            break
        pair_id = str(row.get("pair_id", ""))
        if pair_id in seen_pair_ids:
            continue
        edge = _source_edge(row)
        left_family, right_family = _endpoint_families(row)
        left_window, right_window = _endpoint_windows(row)
        if source_edge_counts[edge] >= int(max_pairs_per_source_edge):
            continue
        if family_counts[left_family] >= int(max_pairs_per_endpoint_family):
            continue
        if family_counts[right_family] >= int(max_pairs_per_endpoint_family):
            continue
        if window_counts[left_window] >= int(max_pairs_per_window):
            continue
        if window_counts[right_window] >= int(max_pairs_per_window):
            continue
        item = dict(row)
        item["selected_pair_id"] = f"selected-{len(selected):04d}"
        item["selection_rank"] = len(selected) + 1
        item["selection_source"] = _selection_source(row, clean_windows_by_edge, clean_families)
        selected.append(item)
        seen_pair_ids.add(pair_id)
        source_edge_counts[edge] += 1
        family_counts[left_family] += 1
        family_counts[right_family] += 1
        window_counts[left_window] += 1
        window_counts[right_window] += 1
    return selected


def _selection_source(row: Mapping[str, Any], clean_windows_by_edge: Mapping[str, set[str]], clean_families: set[str]) -> str:
    edge = _source_edge(row)
    windows = set(_endpoint_windows(row))
    clean_windows = set(clean_windows_by_edge.get(edge, set()))
    if edge in clean_windows_by_edge and windows & clean_windows:
        return "clean_edge_window"
    if edge in clean_windows_by_edge:
        return "clean_edge"
    if edge in NEGATIVE_DIAGNOSTIC_EDGES:
        return "negative_diagnostic_edge"
    if _shares_clean_endpoint(row, clean_families):
        return "clean_endpoint_neighbor"
    return "fallback_pairable"


def _endpoint_family_set(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        result.add(str(row.get("target_source_family", "")))
        result.add(str(row.get("donor_source_family", "")))
    return {item for item in result if item}


def build_repair_summary(
    *,
    source_spec_count: int,
    selected_rows: Sequence[Mapping[str, Any]],
    intervention_rows: Sequence[Mapping[str, Any]],
    classified_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the M1592 clean-source repair summary."""

    label_counts = Counter(str(row.get("label", "")) for row in classified_rows)
    clean_rows = [row for row in classified_rows if str(row.get("label", "")) == CLEAN_LABEL]
    clean_edge_counts = Counter(str(row.get("source_edge", "")) for row in clean_rows)
    invalid_count = label_counts.get("replay_or_metric_invalid", 0)
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "clean_history_control_source_generation_repair_smoke",
        "source_spec_count": int(source_spec_count),
        "selected_pair_count": len(selected_rows),
        "selected_source_edge_count": len({_source_edge(row) for row in selected_rows}),
        "selected_endpoint_source_family_count": len(
            {family for row in selected_rows for family in _endpoint_families(row) if family}
        ),
        "selected_window_count": len({window for row in selected_rows for window in _endpoint_windows(row) if window}),
        "directed_pair_count": len({str(row.get("pair_id", "")) for row in intervention_rows}),
        "intervention_row_count": len(intervention_rows),
        "classified_directed_pair_count": len(classified_rows),
        "required_variant_coverage_complete": invalid_count == 0,
        "clean_directed_pair_count": len(clean_rows),
        "clean_source_edge_count": len(clean_edge_counts),
        "clean_endpoint_source_family_count": len(_endpoint_family_set(clean_rows)),
        "max_clean_source_edge_share": _max_share(clean_edge_counts),
        "dominated_history_positive_directed_pair_count": label_counts.get("history_positive_control_dominated", 0),
        "control_only_positive_directed_pair_count": label_counts.get("control_only_positive", 0),
        "history_null_all_controls_null_directed_pair_count": label_counts.get("history_null_all_controls_null", 0),
        "invalid_directed_pair_count": invalid_count,
        "label_counts": dict(sorted(label_counts.items())),
        "max_history_gap": max((_finite_float(row.get("history_max_gap"), default=0.0) for row in classified_rows), default=0.0),
        "max_control_gap": max((_finite_float(row.get("control_max_gap"), default=0.0) for row in classified_rows), default=0.0),
        "history_interventions_executed": True,
        "replay_started": True,
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["source_spec_count"]) >= 360
        and int(summary["selected_pair_count"]) >= 64
        and int(summary["classified_directed_pair_count"]) >= 128
        and bool(summary["required_variant_coverage_complete"])
        and int(summary["clean_directed_pair_count"]) >= CLEAN_TARGET_COUNT
        and int(summary["clean_source_edge_count"]) >= CLEAN_SOURCE_EDGE_TARGET
        and int(summary["clean_endpoint_source_family_count"]) >= CLEAN_ENDPOINT_FAMILY_TARGET
        and float(summary["max_clean_source_edge_share"]) <= MAX_CLEAN_SOURCE_EDGE_SHARE
        and int(summary["guardrail_violation_count"]) == 0
        and bool(summary["history_interventions_executed"])
        and not bool(summary["candidate_materialized"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["training_corpus_exported"])
    )
    summary["passes_evidence_quality_targets"] = bool(summary["passes_public_smoke_gates"])
    if invalid_count:
        null_class = "metric_invalid"
    elif int(summary["clean_directed_pair_count"]) < CLEAN_TARGET_COUNT:
        null_class = "clean_count_shortfall"
    elif int(summary["clean_source_edge_count"]) < CLEAN_SOURCE_EDGE_TARGET:
        null_class = "clean_source_edge_shortfall"
    elif float(summary["max_clean_source_edge_share"]) > MAX_CLEAN_SOURCE_EDGE_SHARE:
        null_class = "source_concentrated_clean_surface"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "clean_source_repair_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    return summary


def run_clean_history_control_source_generation_repair_smoke(
    output_dir: Path | str,
    *,
    pair_rows: Path | str = DEFAULT_PAIR_ROWS,
    clean_rows: Path | str = DEFAULT_CLEAN_ROWS,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1901,
    seed_count: int = 6,
    max_source_specs: int = 480,
    max_anchor_candidates: int = 640,
    max_selected_pairs: int = 96,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run the bounded clean history-control source-generation repair smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    input_pair_rows = read_csv_rows(pair_rows)
    input_clean_rows = read_csv_rows(clean_rows)
    selected_rows = select_clean_source_repair_pairability_rows(
        input_pair_rows,
        input_clean_rows,
        max_selected_pairs=max_selected_pairs,
    )
    directed_pairs = build_directed_pairs(selected_rows)
    specs = pairability_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    specs_by_id = {str(spec.artifact_row.calibration_id): spec for spec in specs}
    candidates = build_pairability_anchor_candidates(specs, max_anchors=max_anchor_candidates)
    candidates_by_id = {candidate.anchor_id: candidate for candidate in candidates}
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    needed_anchor_ids = {pair.target_anchor_id for pair in directed_pairs} | {pair.donor_anchor_id for pair in directed_pairs}
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
    legacy_rows: list[dict[str, Any]] = []
    for pair in directed_pairs:
        target = replays.get(pair.target_anchor_id)
        donor = replays.get(pair.donor_anchor_id)
        if target is None:
            for variant in VARIANTS:
                legacy_rows.append(_failure_row(pair=pair, variant=_legacy_variant(variant), target_status="missing_target_spec", donor_status="not_run"))
            continue
        for variant in VARIANTS:
            legacy_rows.append(
                run_intervention_variant(
                    pair=pair,
                    target=target,
                    donor=donor,
                    variant=_legacy_variant(variant),
                    model=model,
                    continuation_steps=continuation_steps,
                )
            )
    intervention_rows = _translate_finalized_rows(finalize_rows(legacy_rows), _selected_meta_by_directed_pair(selected_rows))
    classified_rows = classify_rows(intervention_rows)
    clean_classified_rows = [row for row in classified_rows if row.get("label") == CLEAN_LABEL]
    summary = build_repair_summary(
        source_spec_count=len(specs),
        selected_rows=selected_rows,
        intervention_rows=intervention_rows,
        classified_rows=classified_rows,
    )

    write_csv_rows(output / "source_spec_rows.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "selected_pair_rows.csv", selected_rows)
    write_csv_rows(output / "intervention_rows.csv", intervention_rows)
    write_csv_rows(output / "classified_directed_pair_rows.csv", classified_rows)
    write_csv_rows(output / "clean_directed_pair_rows.csv", clean_classified_rows)
    write_csv_rows(output / "source_edge_summary.csv", group_summary(classified_rows, "source_edge"))
    write_csv_rows(output / "label_summary.csv", label_summary(classified_rows))
    write_csv_rows(output / "variant_summary.csv", build_variant_summary(intervention_rows))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in FORBIDDEN_GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run clean history-vs-control source-generation repair smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--pair-rows", type=Path, default=DEFAULT_PAIR_ROWS)
    parser.add_argument("--clean-rows", type=Path, default=DEFAULT_CLEAN_ROWS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1901)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=480)
    parser.add_argument("--max-anchor-candidates", type=int, default=640)
    parser.add_argument("--max-selected-pairs", type=int, default=96)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_clean_history_control_source_generation_repair_smoke(
        args.output_dir,
        pair_rows=args.pair_rows,
        clean_rows=args.clean_rows,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchor_candidates=int(args.max_anchor_candidates),
        max_selected_pairs=int(args.max_selected_pairs),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"selected_pair_count={summary['selected_pair_count']}")
    print(f"classified_directed_pair_count={summary['classified_directed_pair_count']}")
    print(f"clean_directed_pair_count={summary['clean_directed_pair_count']}")
    print(f"clean_source_edge_count={summary['clean_source_edge_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
