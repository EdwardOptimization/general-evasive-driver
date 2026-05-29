"""High-speed/late history-source repair for public P0 anchors."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_pair_expansion_planner import expanded_terminal_source_rows
from autodrift.calibrated_terminal_boundary_history_interventions import AnchorReplayState, replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract, phase_for_step
from autodrift.history_sensitive_active_set_miner import (
    M1576_CONTROL_VARIANTS,
    PRIMARY_HISTORY_VARIANTS,
    build_control_substitution_summary,
    history_sensitive_pair_rows,
)
from autodrift.recoverable_active_set_generator import anchor_result_row, run_hold_continuation
from autodrift.source_diverse_flip_anchor_history_interventions import (
    VARIANTS,
    DonorPair,
    _failure_row,
    _response_l2,
    _tensor_l2,
    build_variant_summary,
    finalize_rows,
    run_intervention_variant,
)
from autodrift.temporal_active_set_anchor_sensitivity_miner import AnchorCandidate, _asdict_rows, _finite_float, _max_share
from autodrift.terminal_boundary_task_sampling_calibration import CalibrationMode, _retarget_hook_spec


DEFAULT_RUN_DIR = Path("runs/m1579_high_speed_late_history_source_repair_smoke")
TARGET_FAMILIES = {"t5_high_speed_close_obstacle", "late_reveal_boundary"}
REPAIR_WINDOWS = (
    "reveal",
    "reveal_plus_2",
    "reveal_plus_4",
    "reveal_plus_8",
    "decision_minus_32",
    "decision_minus_24",
    "decision_minus_16",
    "decision_minus_8",
    "decision",
)
STRICT_RESPONSE_ACTION_L2_MAX = 0.55
STRICT_HIDDEN_L2_MIN = 3.0
FALLBACK_RESPONSE_ACTION_L2_MAX = 0.75
FALLBACK_HIDDEN_L2_MIN = 4.0
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


def high_speed_history_pressure_modes() -> tuple[CalibrationMode, ...]:
    """Return source-repair modes for high-speed history pressure."""

    return (
        CalibrationMode("hs_hist_early_reveal_low_authority", 0.78, 0.55, 4.0, -8, low_authority_band=True),
        CalibrationMode("hs_hist_early_reveal_aeb", 0.72, 0.60, 5.0, -4, require_aeb_infeasible=True),
        CalibrationMode("hs_hist_close_faster_aeb", 0.66, 0.55, 6.0, 0, require_aeb_infeasible=True),
        CalibrationMode("hs_hist_wide_boundary_pressure", 0.74, 0.75, 4.0, 0, low_authority_band=True),
        CalibrationMode("hs_hist_matched_current_low_authority", 0.82, 0.45, 4.0, 4, low_authority_band=True),
        CalibrationMode("hs_hist_reveal_to_decision_gap", 0.80, 0.50, 5.0, -4),
        CalibrationMode("hs_hist_late_low_authority", 0.70, 0.65, 5.0, 4, low_authority_band=True),
        CalibrationMode("hs_hist_aeb_low_authority", 0.68, 0.70, 6.0, 4, require_aeb_infeasible=True, low_authority_band=True),
    )


def late_history_pressure_modes() -> tuple[CalibrationMode, ...]:
    """Return source-repair modes for late-reveal history pressure."""

    return (
        CalibrationMode("late_hist_reveal_plus_window", 0.88, 0.35, 2.0, 6),
        CalibrationMode("late_hist_low_authority_moderate", 0.86, 0.40, 2.5, 8, low_authority_band=True),
        CalibrationMode("late_hist_aeb_wide", 0.78, 0.60, 3.5, 8, require_aeb_infeasible=True),
        CalibrationMode("late_hist_not_yet_fixed_boundary", 0.92, 0.30, 2.0, 10, low_authority_band=True),
        CalibrationMode("late_hist_speed_pressure", 0.80, 0.50, 5.0, 6),
        CalibrationMode("late_hist_wide_low_authority", 0.82, 0.70, 3.0, 10, low_authority_band=True),
        CalibrationMode("late_hist_aeb_low_authority", 0.78, 0.65, 4.0, 12, require_aeb_infeasible=True, low_authority_band=True),
        CalibrationMode("late_hist_reveal_gap_aeb", 0.90, 0.45, 3.0, 6, require_aeb_infeasible=True),
    )


def modes_for_source_family(source_family: str) -> tuple[CalibrationMode, ...]:
    if source_family == "t5_high_speed_close_obstacle":
        return high_speed_history_pressure_modes()
    if source_family == "late_reveal_boundary":
        return late_history_pressure_modes()
    return ()


def history_pressure_source_specs(*, seed: int, seed_count: int, max_source_specs: int) -> list[Any]:
    """Build bounded high-speed/late source repair specs."""

    specs: list[Any] = []
    round_index = 0
    while len(specs) < int(max_source_specs) and round_index < 8:
        base_rows = max(8, int(np.ceil(max_source_specs / 8.0)))
        rows = expanded_terminal_source_rows(
            seed=int(seed) + 1000 * round_index,
            seed_count=int(seed_count),
            max_base_rows=base_rows,
        )
        for row in rows:
            if str(row.source_family) not in TARGET_FAMILIES:
                continue
            for mode in modes_for_source_family(str(row.source_family)):
                if len(specs) >= int(max_source_specs):
                    break
                specs.append(_retarget_hook_spec(row, mode, calibration_index=len(specs)))
        round_index += 1
    return specs[: max(0, int(max_source_specs))]


def repair_anchor_step_for_window(spec: Any, window: str) -> int:
    hook = spec.hook_spec
    reveal = int(hook.reveal_step)
    decision = int(hook.decision_step)
    max_step = max(0, int(hook.env_config.max_steps) - 1)
    if window == "reveal":
        step = reveal
    elif window == "reveal_plus_2":
        step = reveal + 2
    elif window == "reveal_plus_4":
        step = reveal + 4
    elif window == "reveal_plus_8":
        step = reveal + 8
    elif window == "decision_minus_32":
        step = decision - 32
    elif window == "decision_minus_24":
        step = decision - 24
    elif window == "decision_minus_16":
        step = decision - 16
    elif window == "decision_minus_8":
        step = decision - 8
    elif window == "decision":
        step = decision
    else:
        raise ValueError(f"unknown repair window: {window}")
    return int(min(max(step, 0), max_step))


def build_repair_anchor_candidates(
    specs: Sequence[Any],
    *,
    max_anchors: int,
    windows: Sequence[str] = REPAIR_WINDOWS,
) -> list[AnchorCandidate]:
    """Build source/window balanced high-speed/late anchor candidates."""

    grouped: dict[tuple[str, str], list[AnchorCandidate]] = defaultdict(list)
    for spec in specs:
        artifact = spec.artifact_row
        seen_steps: set[int] = set()
        for window in windows:
            step = repair_anchor_step_for_window(spec, window)
            if step in seen_steps:
                continue
            seen_steps.add(step)
            grouped[(str(artifact.source_family), str(window))].append(
                AnchorCandidate(
                    anchor_id=f"{artifact.calibration_id}|{window}|{step}",
                    calibration_id=str(artifact.calibration_id),
                    source_row_id=str(artifact.source_row_id),
                    source_family=str(artifact.source_family),
                    task_family=str(artifact.task_family),
                    seed=int(artifact.seed),
                    mode_name=str(artifact.mode_name),
                    anchor_window=str(window),
                    anchor_step=int(step),
                    reveal_step=int(artifact.reveal_step),
                    decision_step=int(artifact.decision_step),
                    phase=phase_for_step(int(step), int(artifact.reveal_step), int(artifact.decision_step)),
                    base_distance_min=float(artifact.base_distance_min),
                    base_distance_max=float(artifact.base_distance_max),
                    retarget_distance_min=float(artifact.retarget_distance_min),
                    retarget_distance_max=float(artifact.retarget_distance_max),
                )
            )
    keys = sorted(grouped)
    selected: list[AnchorCandidate] = []
    while keys and len(selected) < int(max_anchors):
        progressed = False
        for key in list(keys):
            bucket = grouped[key]
            if not bucket:
                keys.remove(key)
                continue
            selected.append(bucket.pop(0))
            progressed = True
            if len(selected) >= int(max_anchors):
                break
        if not progressed:
            break
    return selected


def donor_screen_label(*, response_action_l2: float, hidden_l2: float) -> str:
    """Classify target-donor pairability for the M1578 matched-current screen."""

    response = _finite_float(response_action_l2, default=float("inf"))
    hidden = _finite_float(hidden_l2, default=0.0)
    if response <= STRICT_RESPONSE_ACTION_L2_MAX and hidden >= STRICT_HIDDEN_L2_MIN:
        return "strict_matched_current_hidden_divergent"
    if response <= FALLBACK_RESPONSE_ACTION_L2_MAX and hidden >= FALLBACK_HIDDEN_L2_MIN:
        return "fallback_matched_current_hidden_divergent"
    return "screen_rejected"


def build_matched_donor_pairs(
    targets: Sequence[AnchorCandidate],
    donor_pool: Sequence[AnchorCandidate],
    replays: Mapping[str, AnchorReplayState],
    anchor_rows: Sequence[Mapping[str, Any]],
    *,
    donors_per_target: int,
) -> tuple[list[DonorPair], list[dict[str, Any]]]:
    """Build matched-current hidden-divergent source repair donor pairs."""

    row_status = {str(row.get("anchor_id", "")): str(row.get("normal_replay_status", "")) for row in anchor_rows}
    pairs: list[DonorPair] = []
    pair_rows: list[dict[str, Any]] = []
    for target in targets:
        if row_status.get(target.anchor_id) != "ok":
            continue
        target_replay = replays.get(target.anchor_id)
        candidates: list[tuple[tuple[Any, ...], AnchorCandidate, str, float, float]] = []
        for donor in donor_pool:
            if donor.anchor_id == target.anchor_id:
                continue
            if donor.source_family == target.source_family:
                continue
            if row_status.get(donor.anchor_id) != "ok":
                continue
            donor_replay = replays.get(donor.anchor_id)
            hidden_l2 = _tensor_l2(target_replay.hidden if target_replay is not None else None, donor_replay.hidden if donor_replay is not None else None)
            response_l2 = _response_l2(target_replay, donor_replay)
            screen = donor_screen_label(response_action_l2=response_l2, hidden_l2=hidden_l2)
            screen_row = {
                "pair_id": "",
                "target_anchor_id": str(target.anchor_id),
                "donor_anchor_id": str(donor.anchor_id),
                "target_source_family": str(target.source_family),
                "donor_source_family": str(donor.source_family),
                "target_anchor_window": str(target.anchor_window),
                "donor_anchor_window": str(donor.anchor_window),
                "target_anchor_step": int(target.anchor_step),
                "donor_anchor_step": int(donor.anchor_step),
                "same_window": donor.anchor_window == target.anchor_window,
                "step_distance": abs(int(donor.anchor_step) - int(target.anchor_step)),
                "diagnostic_late_reveal": str(target.source_family) == "late_reveal_boundary",
                "donor_rank": "",
                "screen": screen,
                "target_donor_response_action_l2": _finite_float(response_l2, default=float("nan")),
                "target_donor_hidden_l2": _finite_float(hidden_l2, default=float("nan")),
            }
            if screen == "screen_rejected":
                pair_rows.append(screen_row)
                continue
            score = (
                0 if screen.startswith("strict") else 1,
                0 if donor.anchor_window == target.anchor_window else 1,
                abs(int(donor.anchor_step) - int(target.anchor_step)),
                _finite_float(response_l2, default=1e9),
                -_finite_float(hidden_l2, default=0.0),
                str(donor.anchor_id),
            )
            candidates.append((score, donor, screen, _finite_float(response_l2, default=float("nan")), _finite_float(hidden_l2, default=float("nan"))))
        candidates.sort(key=lambda item: item[0])
        for donor_rank, (_, donor, screen, response_l2, hidden_l2) in enumerate(candidates[: max(0, int(donors_per_target))], start=1):
            pair = DonorPair(
                pair_id=f"pair-{len(pairs):04d}",
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
                contrasting_normal_outcome=False,
                diagnostic_late_reveal=str(target.source_family) == "late_reveal_boundary",
                donor_rank=donor_rank,
            )
            pairs.append(pair)
            pair_rows.append(
                {
                    **asdict(pair),
                    "screen": screen,
                    "target_donor_response_action_l2": response_l2,
                    "target_donor_hidden_l2": hidden_l2,
                }
            )
    return pairs, pair_rows


def _enrich_pair_rows(pair_rows: Sequence[Mapping[str, Any]], screen_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    screen_by_pair = {str(row.get("pair_id", "")): row for row in screen_rows}
    result: list[dict[str, Any]] = []
    for row in pair_rows:
        item = dict(row)
        screen = screen_by_pair.get(str(row.get("pair_id", "")), {})
        item["screen"] = str(screen.get("screen", ""))
        item["screen_response_action_l2"] = screen.get("target_donor_response_action_l2", "")
        item["screen_hidden_l2"] = screen.get("target_donor_hidden_l2", "")
        result.append(item)
    return result


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
            }
        )
    return result


def build_summary(
    *,
    specs: Sequence[Any],
    candidates: Sequence[AnchorCandidate],
    anchor_rows: Sequence[Mapping[str, Any]],
    pairs: Sequence[DonorPair],
    screen_rows: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    pair_rows: Sequence[Mapping[str, Any]],
    max_source_specs: int,
    max_anchor_candidates: int,
    max_target_anchors: int,
    continuation_steps: int,
) -> dict[str, Any]:
    replay_ok = [row for row in anchor_rows if str(row.get("normal_replay_status", "")) == "ok"]
    clean_pairs = [row for row in pair_rows if bool(row.get("history_sensitive_clean", False))]
    clean_anchor_ids = {str(row.get("target_anchor_id", "")) for row in clean_pairs}
    clean_windows = Counter(str(row.get("target_anchor_window", "")) for row in clean_pairs)
    high_speed_clean = [
        row for row in clean_pairs if str(row.get("target_source_family", "")) == "t5_high_speed_close_obstacle"
    ]
    late_clean = [row for row in clean_pairs if str(row.get("target_source_family", "")) == "late_reveal_boundary"]
    clean_total = len({*{row.get("target_anchor_id") for row in high_speed_clean}, *{row.get("target_anchor_id") for row in late_clean}})
    control_dominated = [
        row
        for row in pair_rows
        if str(row.get("classification", "")) in {"history_sensitive_control_overlap", "control_substitution_dominated"}
    ]
    screen_counts = Counter(str(row.get("screen", "")) for row in screen_rows)
    summary = {
        "result_class": "high_speed_late_history_source_repair_smoke",
        "source_spec_count": len(specs),
        "max_source_specs": int(max_source_specs),
        "anchor_candidate_count": len(candidates),
        "max_anchor_candidates": int(max_anchor_candidates),
        "replay_ok_anchor_count": len(replay_ok),
        "target_anchor_count": min(int(max_target_anchors), len(replay_ok)),
        "donor_pair_count": len(pairs),
        "matched_current_hidden_divergent_pair_count": len(pairs),
        "strict_matched_pair_count": screen_counts.get("strict_matched_current_hidden_divergent", 0),
        "fallback_matched_pair_count": screen_counts.get("fallback_matched_current_hidden_divergent", 0),
        "variant_count": len(VARIANTS),
        "intervention_row_count": len(rows),
        "clean_high_speed_or_late_history_sensitive_anchor_count": clean_total,
        "high_speed_or_late_history_sensitive_anchor_count": len({row.get("target_anchor_id") for row in pair_rows if bool(row.get("history_positive", False))}),
        "high_speed_history_sensitive_count": len({row.get("target_anchor_id") for row in high_speed_clean}),
        "late_reveal_history_sensitive_count": len({row.get("target_anchor_id") for row in late_clean}),
        "history_sensitive_window_count": len(clean_windows),
        "max_single_history_sensitive_window_share": _max_share(clean_windows),
        "control_substitution_dominated_pair_count": len(control_dominated),
        "control_substitution_dominated_share": len(control_dominated) / max(1, len(pair_rows)),
        "max_primary_history_gap": max((_finite_float(row.get("primary_history_gap")) for row in pair_rows), default=0.0),
        "max_control_gap": max((_finite_float(row.get("best_control_gap")) for row in pair_rows), default=0.0),
        "max_hidden_specific_gap": max((_finite_float(row.get("hidden_specific_gap")) for row in pair_rows), default=0.0),
        "classification_counts": dict(sorted(Counter(str(row.get("classification", "")) for row in pair_rows).items())),
        "screen_counts": dict(sorted(screen_counts.items())),
        "clean_window_counts": dict(sorted(clean_windows.items())),
        "continuation_steps": int(continuation_steps),
        "history_interventions_executed": True,
        "replay_started": True,
        "guardrail_violation_count": sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value)),
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["source_spec_count"]) >= 240
        and int(summary["anchor_candidate_count"]) >= 256
        and int(summary["replay_ok_anchor_count"]) >= 128
        and int(summary["matched_current_hidden_divergent_pair_count"]) >= 96
        and int(summary["intervention_row_count"]) >= 768
        and int(summary["high_speed_or_late_history_sensitive_anchor_count"]) >= 8
        and int(summary["clean_high_speed_or_late_history_sensitive_anchor_count"]) >= 6
        and (int(summary["high_speed_history_sensitive_count"]) >= 4 or int(summary["late_reveal_history_sensitive_count"]) >= 4)
        and int(summary["history_sensitive_window_count"]) >= 3
        and float(summary["control_substitution_dominated_share"]) <= 0.40
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
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and int(summary["high_speed_or_late_history_sensitive_anchor_count"]) >= 16
        and int(summary["clean_high_speed_or_late_history_sensitive_anchor_count"]) >= 12
        and int(summary["high_speed_history_sensitive_count"]) >= 6
        and int(summary["late_reveal_history_sensitive_count"]) >= 4
        and int(summary["history_sensitive_window_count"]) >= 4
        and int(summary["matched_current_hidden_divergent_pair_count"]) >= 160
        and float(summary["control_substitution_dominated_share"]) <= 0.30
    )
    if int(summary["guardrail_violation_count"]) > 0:
        null_class = "guardrail_or_contract_failure"
    elif int(summary["matched_current_hidden_divergent_pair_count"]) < 96:
        null_class = "matched_pair_shortfall"
    elif int(summary["high_speed_or_late_history_sensitive_anchor_count"]) == 0:
        null_class = "high_speed_late_history_null"
    elif float(summary["control_substitution_dominated_share"]) > 0.40:
        null_class = "control_substitution_dominated"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "high_speed_late_history_source_repair_pass"
    else:
        null_class = "public_gate_shortfall"
    summary["null_result_classification"] = null_class
    return summary


def run_high_speed_late_history_source_repair_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1877,
    seed_count: int = 6,
    max_source_specs: int = 360,
    max_anchor_candidates: int = 384,
    max_target_anchors: int = 192,
    donors_per_target: int = 2,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded high-speed/late history-source repair smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = history_pressure_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    specs_by_id = {spec.artifact_row.calibration_id: spec for spec in specs}
    candidates = build_repair_anchor_candidates(specs, max_anchors=max_anchor_candidates)
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

    replay_ok_candidates = [
        candidate
        for candidate in candidates
        if str(next((row.get("normal_replay_status", "") for row in anchor_rows if row.get("anchor_id") == candidate.anchor_id), "")) == "ok"
    ]
    targets = replay_ok_candidates[: max(0, int(max_target_anchors))]
    pairs, screen_rows = build_matched_donor_pairs(
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
    pair_rows = _enrich_pair_rows(history_sensitive_pair_rows(finalized), screen_rows)
    summary = build_summary(
        specs=specs,
        candidates=candidates,
        anchor_rows=anchor_rows,
        pairs=pairs,
        screen_rows=screen_rows,
        rows=finalized,
        pair_rows=pair_rows,
        max_source_specs=max_source_specs,
        max_anchor_candidates=max_anchor_candidates,
        max_target_anchors=max_target_anchors,
        continuation_steps=continuation_steps,
    )

    write_csv_rows(output / "source_spec_rows.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "anchor_candidate_rows.csv", anchor_rows)
    write_csv_rows(output / "matched_donor_pair_rows.csv", screen_rows)
    write_csv_rows(output / "history_intervention_rows.csv", finalized)
    write_csv_rows(output / "history_sensitive_anchor_rows.csv", pair_rows)
    write_csv_rows(output / "history_sensitive_source_family_summary.csv", _group_summary(pair_rows, "target_source_family"))
    write_csv_rows(output / "history_sensitive_window_summary.csv", _group_summary(pair_rows, "target_anchor_window"))
    write_csv_rows(output / "control_substitution_summary.csv", build_control_substitution_summary(pair_rows))
    write_csv_rows(output / "history_intervention_variant_summary.csv", build_variant_summary(finalized))
    write_csv_rows(
        output / "guardrail_summary.csv",
        [{"guardrail": key, "violated": value} for key, value in {**FORBIDDEN_GUARDRAILS, "history_interventions_executed": False}.items()],
    )
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run high-speed/late history-source repair smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1877)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=360)
    parser.add_argument("--max-anchor-candidates", type=int, default=384)
    parser.add_argument("--max-target-anchors", "--max-anchors", dest="max_target_anchors", type=int, default=192)
    parser.add_argument("--donors-per-target", type=int, default=2)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_high_speed_late_history_source_repair_smoke(
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
    print(f"matched_current_hidden_divergent_pair_count={summary['matched_current_hidden_divergent_pair_count']}")
    print(f"high_speed_history_sensitive_count={summary['high_speed_history_sensitive_count']}")
    print(f"late_reveal_history_sensitive_count={summary['late_reveal_history_sensitive_count']}")
    print(f"null_result_classification={summary['null_result_classification']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"passes_evidence_quality_targets={summary['passes_evidence_quality_targets']}")


if __name__ == "__main__":
    main()
