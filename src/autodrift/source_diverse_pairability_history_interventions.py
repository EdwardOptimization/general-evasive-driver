"""Source-diverse history interventions over M1582 pairability rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_terminal_boundary_history_interventions import AnchorReplayState, replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.history_pairability_source_miner import build_pairability_anchor_candidates, pairability_source_specs
from autodrift.source_diverse_flip_anchor_history_interventions import (
    DonorPair,
    _failure_row,
    build_variant_summary,
    finalize_rows,
    run_intervention_variant,
)
from autodrift.temporal_active_set_anchor_sensitivity_miner import AnchorCandidate, _finite_float, _max_share


DEFAULT_RUN_DIR = Path("runs/m1585_source_diverse_pairability_history_intervention_smoke")
DEFAULT_PAIR_ROWS = Path("runs/m1582_history_pairability_source_miner_smoke/pairability_pair_rows.csv")
M1585_VARIANT_TO_LEGACY = {
    "normal": "normal",
    "wrong_history_hidden": "wrong_history_donor_hidden_at_anchor",
    "donor_response_action_plus_hidden": "donor_response_action_plus_hidden_from_anchor",
    "donor_response_action_only": "donor_response_action_stream_from_anchor",
    "reset_hidden": "reset_hidden_once_at_anchor",
    "zero_current_response": "zero_current_response_from_anchor",
    "zero_action_history": "zero_action_history_from_anchor",
    "zero_all_response": "zero_all_response_from_anchor",
}
LEGACY_TO_M1585_VARIANT = {value: key for key, value in M1585_VARIANT_TO_LEGACY.items()}
VARIANTS = tuple(M1585_VARIANT_TO_LEGACY)
HISTORY_VARIANTS = {"wrong_history_hidden", "donor_response_action_plus_hidden"}
CONTROL_VARIANTS = {
    "donor_response_action_only",
    "reset_hidden",
    "zero_current_response",
    "zero_action_history",
    "zero_all_response",
}
HIGH_SPEED_FAMILY = "t5_high_speed_close_obstacle"
LATE_REVEAL_FAMILY = "late_reveal_boundary"
HISTORY_GAP_THRESHOLD = 0.02
CONTROL_DOMINANCE_RATIO_THRESHOLD = 0.75
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


def read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _endpoint_families(row: Mapping[str, Any]) -> tuple[str, str]:
    return (str(row.get("left_source_family", "")), str(row.get("right_source_family", "")))


def _endpoint_windows(row: Mapping[str, Any]) -> tuple[str, str]:
    return (str(row.get("left_anchor_window", "")), str(row.get("right_anchor_window", "")))


def _source_edge(row: Mapping[str, Any]) -> str:
    edge = str(row.get("source_edge", ""))
    if edge:
        return edge
    return "|".join(sorted(_endpoint_families(row)))


def _eligible_pair_row(row: Mapping[str, Any]) -> bool:
    return (
        _parse_bool(row.get("tier_a_strict", False))
        and _parse_bool(row.get("context_ok", False))
        and _finite_float(row.get("response_action_l2"), default=1e9) <= 0.55
        and _finite_float(row.get("hidden_l2"), default=0.0) >= 3.0
    )


def _pair_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        0 if _parse_bool(row.get("same_window", False)) else 1,
        _finite_float(row.get("response_action_l2"), default=1e9),
        -_finite_float(row.get("hidden_l2"), default=0.0),
        _finite_float(row.get("context_l2"), default=1e9),
        _source_edge(row),
        str(row.get("pair_id", "")),
    )


def select_pairability_rows(
    pair_rows: Sequence[Mapping[str, Any]],
    *,
    target_pairs: int = 72,
    max_pairs_per_source_edge: int = 4,
    max_pairs_per_endpoint_family: int = 20,
    max_pairs_per_anchor_window: int = 20,
) -> list[dict[str, Any]]:
    """Select a bounded source-edge/window balanced intervention subset."""

    eligible = [dict(row) for row in pair_rows if _eligible_pair_row(row)]
    eligible.sort(key=_pair_sort_key)
    passes = (
        [row for row in eligible if _parse_bool(row.get("same_window", False))],
        [row for row in eligible if not _parse_bool(row.get("same_window", False))],
    )
    selected: list[dict[str, Any]] = []
    source_edge_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    left_window_counts: Counter[str] = Counter()
    seen_pair_ids: set[str] = set()
    for pool in passes:
        for row in pool:
            if len(selected) >= int(target_pairs):
                break
            pair_id = str(row.get("pair_id", ""))
            if pair_id in seen_pair_ids:
                continue
            edge = _source_edge(row)
            if source_edge_counts[edge] >= int(max_pairs_per_source_edge):
                continue
            # The pair rows are undirected but later replay both directions.
            # Cap the listed left endpoint here so the selector can still
            # produce a source-edge-diverse directed set from the capped M1582
            # rows without double-counting each undirected pair endpoint.
            left_family, _right_family = _endpoint_families(row)
            if family_counts[left_family] >= int(max_pairs_per_endpoint_family):
                continue
            left_window = str(row.get("left_anchor_window", ""))
            if left_window_counts[left_window] >= int(max_pairs_per_anchor_window):
                continue
            item = dict(row)
            item["selected_pair_id"] = f"selected-{len(selected):04d}"
            item["selection_rank"] = len(selected) + 1
            item["selection_source"] = "same_window_preferred" if _parse_bool(row.get("same_window", False)) else "cross_window_fallback"
            selected.append(item)
            seen_pair_ids.add(pair_id)
            source_edge_counts[edge] += 1
            family_counts[left_family] += 1
            left_window_counts[left_window] += 1
        if len(selected) >= int(target_pairs):
            break
    return selected


def _endpoint_family_set(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        result.update(family for family in _endpoint_families(row) if family)
    return result


def _endpoint_window_set(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        result.update(window for window in _endpoint_windows(row) if window)
    return result


def group_selected_pairs(rows: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if key == "source_edge":
            value = _source_edge(row)
        else:
            value = str(row.get(key, ""))
        grouped[value].append(row)
    result: list[dict[str, Any]] = []
    for value, group in sorted(grouped.items()):
        result.append(
            {
                key: value,
                "selected_pair_count": len(group),
                "endpoint_source_family_count": len(_endpoint_family_set(group)),
                "endpoint_window_count": len(_endpoint_window_set(group)),
                "min_response_action_l2": min((_finite_float(row.get("response_action_l2"), default=1e9) for row in group), default=0.0),
                "max_hidden_l2": max((_finite_float(row.get("hidden_l2"), default=0.0) for row in group), default=0.0),
                "same_window_pair_count": sum(1 for row in group if _parse_bool(row.get("same_window", False))),
            }
        )
    return result


def selected_source_family_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        left, right = _endpoint_families(row)
        grouped[left].append(row)
        grouped[right].append(row)
    result: list[dict[str, Any]] = []
    for family, group in sorted(grouped.items()):
        result.append(
            {
                "source_family": family,
                "endpoint_selected_pair_count": len(group),
                "high_speed_family": family == HIGH_SPEED_FAMILY,
                "late_reveal_family": family == LATE_REVEAL_FAMILY,
            }
        )
    return result


def selected_window_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        left, right = _endpoint_windows(row)
        grouped[left].append(row)
        grouped[right].append(row)
    result: list[dict[str, Any]] = []
    for window, group in sorted(grouped.items()):
        result.append({"anchor_window": window, "endpoint_selected_pair_count": len(group)})
    return result


def build_directed_pairs(selected_rows: Sequence[Mapping[str, Any]]) -> list[DonorPair]:
    """Turn selected undirected pairability rows into two target-donor directions."""

    result: list[DonorPair] = []
    for row in selected_rows:
        selected_id = str(row.get("selected_pair_id", row.get("pair_id", f"selected-{len(result):04d}")))
        directions = (
            (
                "left_target",
                str(row.get("left_anchor_id", "")),
                str(row.get("right_anchor_id", "")),
                str(row.get("left_source_family", "")),
                str(row.get("right_source_family", "")),
                str(row.get("left_anchor_window", "")),
                str(row.get("right_anchor_window", "")),
                int(float(row.get("left_anchor_step") or 0)),
                int(float(row.get("right_anchor_step") or 0)),
            ),
            (
                "right_target",
                str(row.get("right_anchor_id", "")),
                str(row.get("left_anchor_id", "")),
                str(row.get("right_source_family", "")),
                str(row.get("left_source_family", "")),
                str(row.get("right_anchor_window", "")),
                str(row.get("left_anchor_window", "")),
                int(float(row.get("right_anchor_step") or 0)),
                int(float(row.get("left_anchor_step") or 0)),
            ),
        )
        for direction, target_id, donor_id, target_family, donor_family, target_window, donor_window, target_step, donor_step in directions:
            result.append(
                DonorPair(
                    pair_id=f"{selected_id}|{direction}",
                    target_anchor_id=target_id,
                    donor_anchor_id=donor_id,
                    target_source_family=target_family,
                    donor_source_family=donor_family,
                    target_anchor_window=target_window,
                    donor_anchor_window=donor_window,
                    target_anchor_step=target_step,
                    donor_anchor_step=donor_step,
                    same_window=target_window == donor_window,
                    step_distance=abs(target_step - donor_step),
                    contrasting_normal_outcome=not _parse_bool(row.get("same_outcome", False)),
                    diagnostic_late_reveal=target_family == LATE_REVEAL_FAMILY or donor_family == LATE_REVEAL_FAMILY,
                    donor_rank=1,
                )
            )
    return result


def _selected_meta_by_directed_pair(selected_rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    for row in selected_rows:
        selected_id = str(row.get("selected_pair_id", row.get("pair_id", "")))
        for direction in ("left_target", "right_target"):
            key = f"{selected_id}|{direction}"
            meta[key] = {
                "selected_pair_id": selected_id,
                "original_pair_id": str(row.get("pair_id", "")),
                "source_edge": _source_edge(row),
                "pair_response_action_l2": _finite_float(row.get("response_action_l2")),
                "pair_context_l2": _finite_float(row.get("context_l2")),
                "pair_hidden_l2": _finite_float(row.get("hidden_l2")),
                "selection_source": str(row.get("selection_source", "")),
            }
    return meta


def _legacy_variant(variant: str) -> str:
    return M1585_VARIANT_TO_LEGACY[variant]


def _translate_finalized_rows(rows: Sequence[dict[str, Any]], meta_by_pair: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        legacy = str(item.get("variant", ""))
        item["legacy_variant"] = legacy
        item["variant"] = LEGACY_TO_M1585_VARIANT.get(legacy, legacy)
        item.update(meta_by_pair.get(str(item.get("pair_id", "")), {}))
        result.append(item)
    return result


def _safe_gap(row: Mapping[str, Any]) -> float:
    return _finite_float(row.get("terminal_margin_gap_from_normal"), default=0.0)


def _has_outcome_drop(row: Mapping[str, Any]) -> bool:
    return bool(row.get("success_drop_from_normal", False)) or bool(row.get("collision_increase_from_normal", False))


def _positive_rows(rows: Sequence[Mapping[str, Any]], variants: set[str]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("variant", "")) in variants
        and (_safe_gap(row) >= HISTORY_GAP_THRESHOLD or _has_outcome_drop(row))
    ]


def _max_gap(rows: Sequence[Mapping[str, Any]], variants: set[str]) -> float:
    return max((_safe_gap(row) for row in rows if str(row.get("variant", "")) in variants), default=0.0)


def _source_edges(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    return {str(row.get("source_edge", "")) for row in rows if str(row.get("source_edge", ""))}


def _row_endpoint_families(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        result.add(str(row.get("target_source_family", "")))
        result.add(str(row.get("donor_source_family", "")))
    return {item for item in result if item}


def _group_by_directed_pair(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pair_id", ""))].append(row)
    return grouped


def build_source_edge_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_edge", ""))].append(row)
    result: list[dict[str, Any]] = []
    for edge, group in sorted(grouped.items()):
        history_positive = _positive_rows(group, HISTORY_VARIANTS)
        control_positive = _positive_rows(group, CONTROL_VARIANTS)
        result.append(
            {
                "source_edge": edge,
                "row_count": len(group),
                "directed_pair_count": len({row.get("pair_id") for row in group}),
                "max_history_margin_gap": _max_gap(group, HISTORY_VARIANTS),
                "max_control_margin_gap": _max_gap(group, CONTROL_VARIANTS),
                "history_positive_directed_pair_count": len({row.get("pair_id") for row in history_positive}),
                "control_positive_directed_pair_count": len({row.get("pair_id") for row in control_positive}),
            }
        )
    return result


def build_summary(
    *,
    selected_rows: Sequence[Mapping[str, Any]],
    directed_pairs: Sequence[DonorPair],
    rows: Sequence[dict[str, Any]],
    continuation_steps: int,
) -> dict[str, Any]:
    """Build M1585 source-diverse pairability intervention summary."""

    selected_edge_counts = Counter(_source_edge(row) for row in selected_rows)
    history_positive = _positive_rows(rows, HISTORY_VARIANTS)
    control_positive = _positive_rows(rows, CONTROL_VARIANTS)
    history_positive_pair_ids = {str(row.get("pair_id", "")) for row in history_positive}
    control_positive_pair_ids = {str(row.get("pair_id", "")) for row in control_positive}
    grouped = _group_by_directed_pair(rows)
    control_dominated_count = 0
    comparable_count = 0
    for group in grouped.values():
        history_gap = _max_gap(group, HISTORY_VARIANTS)
        control_gap = _max_gap(group, CONTROL_VARIANTS)
        if history_gap > 0.0 or control_gap > 0.0:
            comparable_count += 1
            if control_gap >= CONTROL_DOMINANCE_RATIO_THRESHOLD * max(history_gap, 1e-9):
                control_dominated_count += 1
    control_dominated_share = 0.0 if comparable_count == 0 else control_dominated_count / comparable_count
    max_history_gap = _max_gap(rows, HISTORY_VARIANTS)
    max_control_gap = _max_gap(rows, CONTROL_VARIANTS)
    history_success_drop_count = sum(1 for row in history_positive if bool(row.get("success_drop_from_normal", False)))
    unique_history_success_drop = any(
        bool(row.get("success_drop_from_normal", False))
        and str(row.get("pair_id", "")) not in control_positive_pair_ids
        for row in history_positive
    )
    high_speed_directed = [
        pair
        for pair in directed_pairs
        if pair.target_source_family == HIGH_SPEED_FAMILY or pair.donor_source_family == HIGH_SPEED_FAMILY
    ]
    late_directed = [
        pair
        for pair in directed_pairs
        if pair.target_source_family == LATE_REVEAL_FAMILY or pair.donor_source_family == LATE_REVEAL_FAMILY
    ]
    high_speed_positive = [
        row
        for row in history_positive
        if str(row.get("target_source_family", "")) == HIGH_SPEED_FAMILY
        or str(row.get("donor_source_family", "")) == HIGH_SPEED_FAMILY
    ]
    late_positive = [
        row
        for row in history_positive
        if str(row.get("target_source_family", "")) == LATE_REVEAL_FAMILY
        or str(row.get("donor_source_family", "")) == LATE_REVEAL_FAMILY
    ]
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "source_diverse_pairability_history_intervention_smoke",
        "selected_pair_count": len(selected_rows),
        "selected_source_edge_count": len(selected_edge_counts),
        "selected_endpoint_source_family_count": len(_endpoint_family_set(selected_rows)),
        "selected_window_count": len(_endpoint_window_set(selected_rows)),
        "max_selected_source_edge_share": _max_share(selected_edge_counts),
        "same_window_selected_pair_count": sum(1 for row in selected_rows if _parse_bool(row.get("same_window", False))),
        "cross_window_selected_pair_count": sum(1 for row in selected_rows if not _parse_bool(row.get("same_window", False))),
        "directed_pair_count": len(directed_pairs),
        "variant_count": len(VARIANTS),
        "history_variant_count": len(HISTORY_VARIANTS),
        "control_variant_count": len(CONTROL_VARIANTS),
        "intervention_row_count": len(rows),
        "anchor_replay_failure_count": sum(1 for row in rows if str(row.get("target_replay_status", "")) != "ok"),
        "wrong_history_row_count": sum(1 for row in rows if row.get("variant") == "wrong_history_hidden"),
        "donor_response_action_plus_hidden_row_count": sum(1 for row in rows if row.get("variant") == "donor_response_action_plus_hidden"),
        "donor_response_action_only_row_count": sum(1 for row in rows if row.get("variant") == "donor_response_action_only"),
        "control_row_count": sum(1 for row in rows if str(row.get("variant", "")) in CONTROL_VARIANTS),
        "history_positive_directed_pair_count": len(history_positive_pair_ids),
        "control_positive_directed_pair_count": len(control_positive_pair_ids),
        "history_positive_source_edge_count": len(_source_edges(history_positive)),
        "history_positive_endpoint_source_family_count": len(_row_endpoint_families(history_positive)),
        "history_success_drop_count": history_success_drop_count,
        "max_history_margin_gap": max_history_gap,
        "max_current_frame_control_gap": max_control_gap,
        "wrong_history_or_donor_plus_hidden_max_gap": max_history_gap,
        "control_substitution_dominated_directed_pair_count": control_dominated_count,
        "control_substitution_comparable_directed_pair_count": comparable_count,
        "control_substitution_dominated_share": control_dominated_share,
        "unique_history_success_drop": unique_history_success_drop,
        "high_speed_endpoint_directed_pair_count": len(high_speed_directed),
        "high_speed_history_positive_count": len({row.get("pair_id") for row in high_speed_positive}),
        "high_speed_endpoint_diagnostic_only": True,
        "late_reveal_endpoint_directed_pair_count": len(late_directed),
        "late_reveal_history_positive_count": len({row.get("pair_id") for row in late_positive}),
        "continuation_steps": int(continuation_steps),
        "history_interventions_executed": True,
        "replay_started": True,
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["selected_pair_count"]) >= 64
        and int(summary["selected_source_edge_count"]) >= 8
        and int(summary["selected_endpoint_source_family_count"]) >= 6
        and int(summary["selected_window_count"]) >= 4
        and float(summary["max_selected_source_edge_share"]) <= 0.20
        and int(summary["directed_pair_count"]) >= 128
        and int(summary["intervention_row_count"]) >= 896
        and int(summary["anchor_replay_failure_count"]) <= 8
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
    history_signal = int(summary["history_positive_directed_pair_count"]) >= 8
    source_signal = (
        int(summary["history_positive_source_edge_count"]) >= 3
        and int(summary["history_positive_endpoint_source_family_count"]) >= 4
    )
    outcome_or_margin = int(summary["history_success_drop_count"]) >= 1 or float(summary["max_history_margin_gap"]) >= 0.05
    control_ok = float(summary["control_substitution_dominated_share"]) <= 0.50
    hidden_ok = float(summary["wrong_history_or_donor_plus_hidden_max_gap"]) >= HISTORY_GAP_THRESHOLD
    history_dominates = float(summary["max_history_margin_gap"]) >= 1.33 * float(summary["max_current_frame_control_gap"]) or bool(
        summary["unique_history_success_drop"]
    )
    summary["passes_evidence_quality_targets"] = bool(summary["passes_public_smoke_gates"]) and history_signal and source_signal and outcome_or_margin and control_ok and hidden_ok and history_dominates
    if not bool(summary["passes_public_smoke_gates"]):
        if int(summary["selected_pair_count"]) < 64 or int(summary["selected_source_edge_count"]) < 8:
            null_class = "selection_balance_failure"
        elif int(summary["anchor_replay_failure_count"]) > 8:
            null_class = "replay_failure"
        else:
            null_class = "public_gate_failure"
    elif not history_signal:
        null_class = "history_null"
    elif not control_ok or not history_dominates:
        null_class = "control_dominated"
    elif int(summary["history_positive_source_edge_count"]) < 3:
        null_class = "source_singleton_history"
    elif int(summary["late_reveal_history_positive_count"]) > 0 and int(summary["history_positive_directed_pair_count"]) == int(summary["late_reveal_history_positive_count"]):
        null_class = "late_only_history"
    elif bool(summary["passes_evidence_quality_targets"]):
        null_class = "public_and_evidence_pass"
    else:
        null_class = "public_pass_evidence_quality_fail"
    summary["null_result_classification"] = null_class
    return summary


def run_source_diverse_pairability_history_intervention_smoke(
    output_dir: Path | str,
    *,
    pair_rows: Path | str = DEFAULT_PAIR_ROWS,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1901,
    seed_count: int = 6,
    max_source_specs: int = 480,
    max_anchor_candidates: int = 640,
    target_pairs: int = 72,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded source-diverse pairability-grounded history interventions."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    input_pair_rows = read_csv_rows(pair_rows)
    selected_rows = select_pairability_rows(input_pair_rows, target_pairs=target_pairs)
    directed_pairs = build_directed_pairs(selected_rows)
    specs = pairability_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    candidates = build_pairability_anchor_candidates(specs, max_anchors=max_anchor_candidates)
    specs_by_id = {str(spec.artifact_row.calibration_id): spec for spec in specs}
    candidates_by_id: dict[str, AnchorCandidate] = {candidate.anchor_id: candidate for candidate in candidates}
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
    finalized = _translate_finalized_rows(finalize_rows(legacy_rows), _selected_meta_by_directed_pair(selected_rows))
    summary = build_summary(
        selected_rows=selected_rows,
        directed_pairs=directed_pairs,
        rows=finalized,
        continuation_steps=continuation_steps,
    )
    write_csv_rows(output / "selected_pair_rows.csv", selected_rows)
    write_csv_rows(output / "selected_pair_source_edge_summary.csv", group_selected_pairs(selected_rows, "source_edge"))
    write_csv_rows(output / "selected_pair_source_family_summary.csv", selected_source_family_summary(selected_rows))
    write_csv_rows(output / "selected_pair_window_summary.csv", selected_window_summary(selected_rows))
    write_csv_rows(output / "intervention_rows.csv", finalized)
    write_csv_rows(output / "variant_summary.csv", build_variant_summary(finalized))
    write_csv_rows(output / "source_edge_summary.csv", build_source_edge_summary(finalized))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in FORBIDDEN_GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run source-diverse pairability history interventions.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--pair-rows", type=Path, default=DEFAULT_PAIR_ROWS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1901)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=480)
    parser.add_argument("--max-anchor-candidates", type=int, default=640)
    parser.add_argument("--target-pairs", type=int, default=72)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_source_diverse_pairability_history_intervention_smoke(
        args.output_dir,
        pair_rows=args.pair_rows,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchor_candidates=int(args.max_anchor_candidates),
        target_pairs=int(args.target_pairs),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"selected_pair_count={summary['selected_pair_count']}")
    print(f"directed_pair_count={summary['directed_pair_count']}")
    print(f"intervention_row_count={summary['intervention_row_count']}")
    print(f"max_history_margin_gap={summary['max_history_margin_gap']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"passes_evidence_quality_targets={summary['passes_evidence_quality_targets']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
