"""History-sensitive active-set miner for public P0 anchors."""

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
from autodrift.recoverable_active_set_generator import (
    ANCHOR_WINDOWS,
    anchor_result_row,
    build_anchor_candidates,
    run_hold_continuation,
)
from autodrift.source_diverse_flip_anchor_history_interventions import (
    CONTROL_VARIANTS,
    VARIANTS,
    DONOR_RESPONSE_ACTION_VARIANTS,
    DonorPair,
    _failure_row,
    _response_l2,
    _tensor_l2,
    build_variant_summary,
    finalize_rows,
    run_intervention_variant,
)
from autodrift.targeted_third_source_flip_anchor import targeted_source_specs
from autodrift.temporal_active_set_anchor_sensitivity_miner import AnchorCandidate, _asdict_rows, _finite_float, _max_share


DEFAULT_RUN_DIR = Path("runs/m1576_history_sensitive_active_set_miner_smoke")
PRIMARY_HISTORY_VARIANTS = {
    "wrong_history_donor_hidden_at_anchor",
    "donor_response_action_plus_hidden_from_anchor",
}
SECONDARY_HISTORY_VARIANTS = {
    "delayed_hidden_8_at_anchor",
    "delayed_hidden_16_at_anchor",
}
M1576_CONTROL_VARIANTS = set(CONTROL_VARIANTS) | {"donor_response_action_stream_from_anchor"}
HISTORY_GAP_THRESHOLD = 0.02
HIDDEN_SPECIFIC_GAP_THRESHOLD = 0.01
CONTROL_RATIO_THRESHOLD = 1.25
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


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _safe_gap(row: Mapping[str, Any]) -> float:
    return _finite_float(row.get("terminal_margin_gap_from_normal"))


def _has_outcome_drop(row: Mapping[str, Any]) -> bool:
    return bool(row.get("success_drop_from_normal", False)) or bool(row.get("collision_increase_from_normal", False))


def _row_positive(row: Mapping[str, Any]) -> bool:
    return _safe_gap(row) >= HISTORY_GAP_THRESHOLD or _has_outcome_drop(row)


def _max_gap(rows: Sequence[Mapping[str, Any]], variants: set[str]) -> float:
    return max((_safe_gap(row) for row in rows if str(row.get("variant", "")) in variants), default=0.0)


def _any_outcome_drop(rows: Sequence[Mapping[str, Any]], variants: set[str]) -> bool:
    return any(str(row.get("variant", "")) in variants and _has_outcome_drop(row) for row in rows)


def _variant_gap(rows: Sequence[Mapping[str, Any]], variant: str) -> float:
    return max((_safe_gap(row) for row in rows if str(row.get("variant", "")) == variant), default=0.0)


def _normal_outcome(row: Mapping[str, Any]) -> tuple[bool, bool]:
    return (_bool_value(row.get("normal_success", False)), _bool_value(row.get("normal_collision", False)))


def _source_family(row: Mapping[str, Any]) -> str:
    return str(row.get("source_family", ""))


def select_target_candidates(
    candidates: Sequence[AnchorCandidate],
    anchor_rows: Sequence[Mapping[str, Any]],
    *,
    max_target_anchors: int,
) -> list[AnchorCandidate]:
    """Select replay-ok targets balanced by source family and window."""

    rows_by_id = {str(row.get("anchor_id", "")): row for row in anchor_rows}
    grouped: dict[tuple[str, str], list[AnchorCandidate]] = defaultdict(list)
    for candidate in candidates:
        row = rows_by_id.get(candidate.anchor_id, {})
        if str(row.get("normal_replay_status", "")) != "ok":
            continue
        grouped[(str(candidate.source_family), str(candidate.anchor_window))].append(candidate)
    keys = sorted(grouped)
    selected: list[AnchorCandidate] = []
    while keys and len(selected) < int(max_target_anchors):
        progressed = False
        for key in list(keys):
            bucket = grouped[key]
            if not bucket:
                keys.remove(key)
                continue
            selected.append(bucket.pop(0))
            progressed = True
            if len(selected) >= int(max_target_anchors):
                break
        if not progressed:
            break
    return selected


def build_history_sensitive_donor_pairs(
    targets: Sequence[AnchorCandidate],
    donor_pool: Sequence[AnchorCandidate],
    replays: Mapping[str, AnchorReplayState],
    anchor_rows: Sequence[Mapping[str, Any]],
    *,
    donors_per_target: int,
) -> list[DonorPair]:
    """Build bounded source-diverse donors for history-sensitive screening."""

    rows_by_id = {str(row.get("anchor_id", "")): row for row in anchor_rows}
    result: list[DonorPair] = []
    for target in targets:
        target_row = rows_by_id.get(target.anchor_id, {})
        target_replay = replays.get(target.anchor_id)
        candidates: list[tuple[tuple[Any, ...], AnchorCandidate]] = []
        for donor in donor_pool:
            if donor.anchor_id == target.anchor_id:
                continue
            if donor.source_family == target.source_family:
                continue
            donor_row = rows_by_id.get(donor.anchor_id, {})
            if str(donor_row.get("normal_replay_status", "")) != "ok":
                continue
            donor_replay = replays.get(donor.anchor_id)
            hidden_l2 = _tensor_l2(target_replay.hidden if target_replay is not None else None, donor_replay.hidden if donor_replay is not None else None)
            response_l2 = _response_l2(target_replay, donor_replay)
            contrasting = _normal_outcome(target_row) != _normal_outcome(donor_row)
            same_window = donor.anchor_window == target.anchor_window
            score = (
                0 if same_window else 1,
                abs(int(donor.anchor_step) - int(target.anchor_step)),
                0 if contrasting else 1,
                _finite_float(response_l2, default=1e9),
                _finite_float(hidden_l2, default=1e9),
                str(donor.source_family),
                str(donor.anchor_id),
            )
            candidates.append((score, donor))
        candidates.sort(key=lambda item: item[0])
        selected: list[AnchorCandidate] = []
        seen_families: set[str] = set()
        for _, donor in candidates:
            if donor.source_family in seen_families and len(seen_families) < int(donors_per_target):
                continue
            selected.append(donor)
            seen_families.add(str(donor.source_family))
            if len(selected) >= int(donors_per_target):
                break
        if len(selected) < int(donors_per_target):
            for _, donor in candidates:
                if donor.anchor_id in {item.anchor_id for item in selected}:
                    continue
                selected.append(donor)
                if len(selected) >= int(donors_per_target):
                    break
        for donor_rank, donor in enumerate(selected, start=1):
            donor_row = rows_by_id.get(donor.anchor_id, {})
            pair = DonorPair(
                pair_id=f"pair-{len(result):04d}",
                target_anchor_id=str(target.anchor_id),
                donor_anchor_id=str(donor.anchor_id),
                target_source_family=str(target.source_family),
                donor_source_family=str(donor.source_family),
                target_anchor_window=str(target.anchor_window),
                donor_anchor_window=str(donor.anchor_window),
                target_anchor_step=int(target.anchor_step),
                donor_anchor_step=int(donor.anchor_step),
                same_window=donor.anchor_window == target.anchor_window,
                step_distance=abs(int(donor.anchor_step) - int(target.anchor_step)),
                contrasting_normal_outcome=_normal_outcome(target_row) != _normal_outcome(donor_row),
                diagnostic_late_reveal=str(target.source_family) == "late_reveal_boundary",
                donor_rank=donor_rank,
            )
            result.append(pair)
    return result


def classify_history_sensitive_pair(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Classify one target-donor intervention group."""

    primary_history_gap = _max_gap(rows, PRIMARY_HISTORY_VARIANTS)
    secondary_history_gap = _max_gap(rows, SECONDARY_HISTORY_VARIANTS)
    best_control_gap = _max_gap(rows, M1576_CONTROL_VARIANTS)
    primary_outcome_drop = _any_outcome_drop(rows, PRIMARY_HISTORY_VARIANTS)
    best_control_outcome_drop = _any_outcome_drop(rows, M1576_CONTROL_VARIANTS)
    donor_plus_gap = _variant_gap(rows, "donor_response_action_plus_hidden_from_anchor")
    donor_stream_gap = _variant_gap(rows, "donor_response_action_stream_from_anchor")
    hidden_specific_gap = donor_plus_gap - donor_stream_gap
    history_positive = primary_history_gap >= HISTORY_GAP_THRESHOLD or primary_outcome_drop
    control_dominates = best_control_gap > primary_history_gap and best_control_outcome_drop >= primary_outcome_drop
    hidden_specific = hidden_specific_gap >= HIDDEN_SPECIFIC_GAP_THRESHOLD
    clean = bool(
        history_positive
        and (
            primary_history_gap >= CONTROL_RATIO_THRESHOLD * max(best_control_gap, 1e-6)
            or hidden_specific
            or (primary_outcome_drop and not best_control_outcome_drop)
        )
    )
    if clean:
        label = "history_sensitive_clean"
    elif history_positive and control_dominates:
        label = "history_sensitive_control_overlap"
    elif history_positive:
        label = "history_sensitive_control_overlap"
    elif best_control_gap >= HISTORY_GAP_THRESHOLD or best_control_outcome_drop:
        label = "control_substitution_dominated"
    else:
        label = "history_null"
    normal = next((row for row in rows if str(row.get("variant", "")) == "normal"), {})
    first = rows[0] if rows else {}
    return {
        "pair_id": str(first.get("pair_id", "")),
        "target_anchor_id": str(first.get("target_anchor_id", "")),
        "donor_anchor_id": str(first.get("donor_anchor_id", "")),
        "target_source_family": str(first.get("target_source_family", "")),
        "donor_source_family": str(first.get("donor_source_family", "")),
        "target_anchor_window": str(first.get("target_anchor_window", "")),
        "donor_anchor_window": str(first.get("donor_anchor_window", "")),
        "target_anchor_step": int(float(first.get("target_anchor_step") or 0)),
        "donor_anchor_step": int(float(first.get("donor_anchor_step") or 0)),
        "same_window": _bool_value(first.get("same_window", False)),
        "contrasting_normal_outcome": _bool_value(first.get("contrasting_normal_outcome", False)),
        "primary_history_gap": primary_history_gap,
        "secondary_history_gap": secondary_history_gap,
        "best_control_gap": best_control_gap,
        "donor_plus_hidden_gap": donor_plus_gap,
        "donor_response_action_stream_gap": donor_stream_gap,
        "hidden_specific_gap": hidden_specific_gap,
        "primary_history_outcome_drop": primary_outcome_drop,
        "best_control_outcome_drop": best_control_outcome_drop,
        "history_positive": history_positive,
        "history_sensitive_clean": clean,
        "control_dominates": bool(control_dominates),
        "classification": label,
        "normal_terminal_margin": _finite_float(normal.get("terminal_margin"), default=float("nan")),
        "normal_success": _bool_value(normal.get("success", False)),
        "normal_collision": _bool_value(normal.get("collision", False)),
        "target_donor_hidden_l2": _finite_float(first.get("target_donor_hidden_l2"), default=float("nan")),
        "target_donor_response_action_l2": _finite_float(first.get("target_donor_response_action_l2"), default=float("nan")),
    }


def history_sensitive_pair_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("pair_id", ""))].append(row)
    return [classify_history_sensitive_pair(group) for _, group in sorted(grouped.items())]


def _group_summary(pair_rows: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in pair_rows:
        grouped[str(row.get(key, ""))].append(row)
    result: list[dict[str, Any]] = []
    for value, group in sorted(grouped.items()):
        clean = [row for row in group if bool(row.get("history_sensitive_clean", False))]
        positive = [row for row in group if bool(row.get("history_positive", False))]
        result.append(
            {
                key: value,
                "pair_count": len(group),
                "target_anchor_count": len({row.get("target_anchor_id") for row in group}),
                "history_positive_pair_count": len(positive),
                "clean_history_sensitive_pair_count": len(clean),
                "clean_history_sensitive_anchor_count": len({row.get("target_anchor_id") for row in clean}),
                "max_primary_history_gap": max((_finite_float(row.get("primary_history_gap")) for row in group), default=0.0),
                "max_control_gap": max((_finite_float(row.get("best_control_gap")) for row in group), default=0.0),
                "control_substitution_dominated_count": sum(1 for row in group if row.get("classification") == "control_substitution_dominated"),
            }
        )
    return result


def build_control_substitution_summary(pair_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    labels = Counter(str(row.get("classification", "")) for row in pair_rows)
    return [{"classification": label, "pair_count": count} for label, count in sorted(labels.items())]


def build_summary(
    *,
    specs: Sequence[Any],
    candidates: Sequence[AnchorCandidate],
    anchor_rows: Sequence[Mapping[str, Any]],
    targets: Sequence[AnchorCandidate],
    pairs: Sequence[DonorPair],
    rows: Sequence[Mapping[str, Any]],
    pair_rows: Sequence[Mapping[str, Any]],
    max_source_specs: int,
    max_anchor_candidates: int,
    max_target_anchors: int,
    continuation_steps: int,
) -> dict[str, Any]:
    """Build M1576 summary and gates."""

    replay_ok = [row for row in anchor_rows if str(row.get("normal_replay_status", "")) == "ok"]
    history_positive_pairs = [row for row in pair_rows if bool(row.get("history_positive", False))]
    clean_pairs = [row for row in pair_rows if bool(row.get("history_sensitive_clean", False))]
    clean_anchor_ids = {str(row.get("target_anchor_id", "")) for row in clean_pairs}
    positive_anchor_ids = {str(row.get("target_anchor_id", "")) for row in history_positive_pairs}
    clean_families = Counter(str(row.get("target_source_family", "")) for row in clean_pairs)
    clean_windows = Counter(str(row.get("target_anchor_window", "")) for row in clean_pairs)
    non_near_clean = [
        row for row in clean_pairs if str(row.get("target_source_family", "")) != "t5_near_boundary_warmup"
    ]
    high_speed_clean = [
        row for row in clean_pairs if str(row.get("target_source_family", "")) == "t5_high_speed_close_obstacle"
    ]
    late_clean = [row for row in clean_pairs if str(row.get("target_source_family", "")) == "late_reveal_boundary"]
    control_dominated = [
        row
        for row in pair_rows
        if str(row.get("classification", "")) in {"history_sensitive_control_overlap", "control_substitution_dominated"}
    ]
    summary = {
        "result_class": "history_sensitive_active_set_miner_smoke",
        "source_spec_count": len(specs),
        "max_source_specs": int(max_source_specs),
        "anchor_candidate_count": len(candidates),
        "max_anchor_candidates": int(max_anchor_candidates),
        "replay_ok_anchor_count": len(replay_ok),
        "target_anchor_count": len(targets),
        "max_target_anchors": int(max_target_anchors),
        "donor_pair_count": len(pairs),
        "variant_count": len(VARIANTS),
        "primary_history_variant_count": len(PRIMARY_HISTORY_VARIANTS),
        "secondary_history_variant_count": len(SECONDARY_HISTORY_VARIANTS),
        "control_variant_count": len(M1576_CONTROL_VARIANTS),
        "intervention_row_count": len(rows),
        "history_positive_pair_count": len(history_positive_pairs),
        "history_sensitive_pair_count": len(history_positive_pairs),
        "clean_history_sensitive_pair_count": len(clean_pairs),
        "history_sensitive_anchor_count": len(positive_anchor_ids),
        "clean_history_sensitive_anchor_count": len(clean_anchor_ids),
        "history_sensitive_source_family_count": len(clean_families),
        "history_sensitive_window_count": len(clean_windows),
        "non_near_family_history_sensitive_count": len({row.get("target_anchor_id") for row in non_near_clean}),
        "high_speed_history_sensitive_count": len({row.get("target_anchor_id") for row in high_speed_clean}),
        "late_reveal_history_sensitive_count": len({row.get("target_anchor_id") for row in late_clean}),
        "max_single_history_sensitive_family_share": _max_share(clean_families),
        "max_single_history_sensitive_window_share": _max_share(clean_windows),
        "control_substitution_dominated_pair_count": len(control_dominated),
        "control_substitution_dominated_share": len(control_dominated) / max(1, len(pair_rows)),
        "max_primary_history_gap": max((_finite_float(row.get("primary_history_gap")) for row in pair_rows), default=0.0),
        "max_secondary_history_gap": max((_finite_float(row.get("secondary_history_gap")) for row in pair_rows), default=0.0),
        "max_control_gap": max((_finite_float(row.get("best_control_gap")) for row in pair_rows), default=0.0),
        "max_hidden_specific_gap": max((_finite_float(row.get("hidden_specific_gap")) for row in pair_rows), default=0.0),
        "classification_counts": dict(sorted(Counter(str(row.get("classification", "")) for row in pair_rows).items())),
        "clean_source_family_counts": dict(sorted(clean_families.items())),
        "clean_window_counts": dict(sorted(clean_windows.items())),
        "continuation_steps": int(continuation_steps),
        "history_interventions_executed": True,
        "replay_started": True,
        "guardrail_violation_count": sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value)),
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["source_spec_count"]) >= 240
        and int(summary["anchor_candidate_count"]) >= 192
        and int(summary["replay_ok_anchor_count"]) >= 96
        and int(summary["donor_pair_count"]) >= 128
        and int(summary["intervention_row_count"]) >= 768
        and int(summary["history_sensitive_anchor_count"]) >= 12
        and int(summary["clean_history_sensitive_anchor_count"]) >= 8
        and int(summary["history_sensitive_source_family_count"]) >= 2
        and int(summary["history_sensitive_window_count"]) >= 3
        and int(summary["non_near_family_history_sensitive_count"]) >= 4
        and int(summary["high_speed_history_sensitive_count"]) >= 1
        and int(summary["guardrail_violation_count"]) == 0
        and bool(summary["history_interventions_executed"])
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
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and int(summary["history_sensitive_anchor_count"]) >= 24
        and int(summary["clean_history_sensitive_anchor_count"]) >= 16
        and int(summary["history_sensitive_source_family_count"]) >= 3
        and int(summary["history_sensitive_window_count"]) >= 4
        and float(summary["max_single_history_sensitive_family_share"]) <= 0.50
        and int(summary["non_near_family_history_sensitive_count"]) >= 8
        and (int(summary["high_speed_history_sensitive_count"]) >= 4 or int(summary["late_reveal_history_sensitive_count"]) >= 2)
        and float(summary["control_substitution_dominated_share"]) <= 0.40
    )
    if int(summary["guardrail_violation_count"]) > 0:
        null_class = "guardrail_or_contract_failure"
    elif int(summary["history_sensitive_anchor_count"]) == 0:
        null_class = "no_history_signal"
    elif int(summary["history_sensitive_source_family_count"]) <= 1:
        null_class = "source_singleton_history_signal"
    elif float(summary["control_substitution_dominated_share"]) > 0.40:
        null_class = "control_substitution_dominated"
    elif int(summary["high_speed_history_sensitive_count"]) == 0 and int(summary["late_reveal_history_sensitive_count"]) == 0:
        null_class = "high_speed_late_null"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "source_diverse_history_sensitive_pass"
    else:
        null_class = "public_gate_shortfall"
    summary["null_result_classification"] = null_class
    return summary


def run_history_sensitive_active_set_miner_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1861,
    seed_count: int = 6,
    max_source_specs: int = 480,
    max_anchor_candidates: int = 512,
    max_target_anchors: int = 96,
    donors_per_target: int = 2,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded public history-sensitive active-set mining."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = targeted_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    specs_by_id = {spec.artifact_row.calibration_id: spec for spec in specs}
    candidates = build_anchor_candidates(specs, max_anchors=max_anchor_candidates, windows=ANCHOR_WINDOWS)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)

    replays: dict[str, AnchorReplayState] = {}
    anchor_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        spec = specs_by_id[candidate.calibration_id]
        replay = replay_to_anchor(
            pair_id=candidate.anchor_id,
            side="target",
            spec=spec,
            anchor_step=int(candidate.anchor_step),
            model=model,
        )
        replays[candidate.anchor_id] = replay
        normal = run_hold_continuation(
            replay=replay,
            spec=spec,
            model=model,
            continuation_steps=continuation_steps,
        )
        anchor_rows.append(anchor_result_row(candidate, normal))

    targets = select_target_candidates(candidates, anchor_rows, max_target_anchors=max_target_anchors)
    replay_ok_candidates = [
        candidate
        for candidate in candidates
        if str(next((row.get("normal_replay_status", "") for row in anchor_rows if row.get("anchor_id") == candidate.anchor_id), "")) == "ok"
    ]
    pairs = build_history_sensitive_donor_pairs(
        targets,
        replay_ok_candidates,
        replays,
        anchor_rows,
        donors_per_target=donors_per_target,
    )
    intervention_rows: list[dict[str, Any]] = []
    for pair in pairs:
        target = replays.get(pair.target_anchor_id)
        donor = replays.get(pair.donor_anchor_id)
        if target is None:
            for variant in VARIANTS:
                intervention_rows.append(
                    _failure_row(pair=pair, variant=variant, target_status="missing_target_replay", donor_status="not_run")
                )
            continue
        for variant in VARIANTS:
            intervention_rows.append(
                run_intervention_variant(
                    pair=pair,
                    target=target,
                    donor=donor,
                    variant=variant,
                    model=model,
                    continuation_steps=continuation_steps,
                )
            )
    finalized = finalize_rows(intervention_rows)
    pair_rows = history_sensitive_pair_rows(finalized)
    summary = build_summary(
        specs=specs,
        candidates=candidates,
        anchor_rows=anchor_rows,
        targets=targets,
        pairs=pairs,
        rows=finalized,
        pair_rows=pair_rows,
        max_source_specs=max_source_specs,
        max_anchor_candidates=max_anchor_candidates,
        max_target_anchors=max_target_anchors,
        continuation_steps=continuation_steps,
    )

    write_csv_rows(output / "source_spec_rows.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "anchor_candidate_rows.csv", anchor_rows)
    write_csv_rows(output / "target_anchor_rows.csv", _asdict_rows(targets))
    write_csv_rows(output / "donor_pair_rows.csv", [asdict(pair) for pair in pairs])
    write_csv_rows(output / "history_intervention_rows.csv", finalized)
    write_csv_rows(output / "history_sensitive_anchor_rows.csv", pair_rows)
    write_csv_rows(output / "history_sensitive_source_family_summary.csv", _group_summary(pair_rows, "target_source_family"))
    write_csv_rows(output / "history_sensitive_window_summary.csv", _group_summary(pair_rows, "target_anchor_window"))
    write_csv_rows(output / "history_intervention_variant_summary.csv", build_variant_summary(finalized))
    write_csv_rows(output / "control_substitution_summary.csv", build_control_substitution_summary(pair_rows))
    write_csv_rows(
        output / "guardrail_summary.csv",
        [{"guardrail": key, "violated": value} for key, value in {**FORBIDDEN_GUARDRAILS, "history_interventions_executed": False}.items()],
    )
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run history-sensitive active-set miner smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1861)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=480)
    parser.add_argument("--max-anchor-candidates", type=int, default=512)
    parser.add_argument("--max-target-anchors", "--max-anchors", dest="max_target_anchors", type=int, default=96)
    parser.add_argument("--donors-per-target", type=int, default=2)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_history_sensitive_active_set_miner_smoke(
        args.output_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchor_candidates=int(args.max_anchor_candidates),
        max_target_anchors=int(args.max_target_anchors),
        donors_per_target=int(args.donors_per_target),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"history_sensitive_anchor_count={summary['history_sensitive_anchor_count']}")
    print(f"clean_history_sensitive_anchor_count={summary['clean_history_sensitive_anchor_count']}")
    print(f"history_sensitive_source_family_count={summary['history_sensitive_source_family_count']}")
    print(f"null_result_classification={summary['null_result_classification']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"passes_evidence_quality_targets={summary['passes_evidence_quality_targets']}")


if __name__ == "__main__":
    main()
