"""Pairability-first source miner for public P0 history evidence."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_terminal_boundary_history_interventions import AnchorReplayState, replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract, hidden_stats, phase_for_step
from autodrift.fresh_ambiguity_source_mining import default_source_specs, expand_source_specs
from autodrift.high_speed_late_history_source_repair import (
    high_speed_history_pressure_modes,
    late_history_pressure_modes,
)
from autodrift.recoverable_active_set_generator import anchor_result_row, run_hold_continuation
from autodrift.temporal_active_set_anchor_sensitivity_miner import AnchorCandidate, _asdict_rows, _finite_float, _max_share
from autodrift.terminal_boundary_task_sampling_calibration import CalibrationMode, calibration_modes, _retarget_hook_spec


DEFAULT_RUN_DIR = Path("runs/m1582_history_pairability_source_miner_smoke")
PAIRABILITY_SOURCE_FAMILIES = {
    "t5_near_boundary_warmup",
    "t5_boundary_axis_retarget",
    "t5_high_speed_close_obstacle",
    "late_reveal_boundary",
    "curved_boundary_obstacle",
    "grip_loss_proxy",
    "brake_fade_or_loss_proxy",
    "drive_loss_proxy",
    "actuator_delay_step",
    "capability_step_down",
    "capability_step_up",
}
PAIRABILITY_WINDOWS = (
    "reveal",
    "reveal_plus_4",
    "reveal_plus_8",
    "decision_minus_32",
    "decision_minus_24",
    "decision_minus_16",
    "decision_minus_8",
    "decision",
)
CONTEXT_L2_MAX = 4.0
TIER_A_RESPONSE_ACTION_L2_MAX = 0.55
TIER_A_HIDDEN_L2_MIN = 3.0
TIER_B_RESPONSE_ACTION_L2_MAX = 0.75
TIER_B_HIDDEN_L2_MIN = 2.0
TIER_C_RESPONSE_ACTION_L2_MAX = 1.00
TIER_C_HIDDEN_L2_MIN = 2.5
HIGH_SPEED_LATE_FAMILIES = {"t5_high_speed_close_obstacle", "late_reveal_boundary"}
FORBIDDEN_GUARDRAILS = {
    "candidate_materialized": False,
    "training_started": False,
    "evaluation_started": False,
    "history_interventions_executed": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "training_corpus_exported": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


def pairability_modes_for_source_family(source_family: str) -> tuple[CalibrationMode, ...]:
    """Return bounded retarget modes for pairability source mining."""

    base = calibration_modes()
    if source_family == "t5_high_speed_close_obstacle":
        return (*high_speed_history_pressure_modes(), *base)
    if source_family == "late_reveal_boundary":
        return (*late_history_pressure_modes(), *base)
    return base


def pairability_source_specs(*, seed: int, seed_count: int, max_source_specs: int) -> list[Any]:
    """Build source-family balanced P0 calibration specs for pairability mining."""

    rows = [
        row
        for row in expand_source_specs(default_source_specs(seed=seed, seed_count=seed_count))
        if str(row.source_family) in PAIRABILITY_SOURCE_FAMILIES
    ]
    grouped: dict[str, list[tuple[Any, CalibrationMode]]] = defaultdict(list)
    for row in rows:
        for mode in pairability_modes_for_source_family(str(row.source_family)):
            grouped[str(row.source_family)].append((row, mode))
    selected: list[Any] = []
    families = sorted(grouped)
    while families and len(selected) < int(max_source_specs):
        progressed = False
        for family in list(families):
            bucket = grouped[family]
            if not bucket:
                families.remove(family)
                continue
            row, mode = bucket.pop(0)
            selected.append(_retarget_hook_spec(row, mode, calibration_index=len(selected)))
            progressed = True
            if len(selected) >= int(max_source_specs):
                break
        if not progressed:
            break
    return selected[: max(0, int(max_source_specs))]


def pairability_anchor_step_for_window(spec: Any, window: str) -> int:
    """Map pairability windows to simulator steps."""

    hook = spec.hook_spec
    reveal = int(hook.reveal_step)
    decision = int(hook.decision_step)
    max_step = max(0, int(hook.env_config.max_steps) - 1)
    if window == "reveal":
        step = reveal
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
        raise ValueError(f"unknown pairability window: {window}")
    return int(min(max(step, 0), max_step))


def build_pairability_anchor_candidates(
    specs: Sequence[Any],
    *,
    max_anchors: int,
    windows: Sequence[str] = PAIRABILITY_WINDOWS,
) -> list[AnchorCandidate]:
    """Build source/window balanced pairability anchors."""

    grouped: dict[tuple[str, str], list[AnchorCandidate]] = defaultdict(list)
    for spec in specs:
        artifact = spec.artifact_row
        seen_steps: set[int] = set()
        for window in windows:
            step = pairability_anchor_step_for_window(spec, window)
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
    selected: list[AnchorCandidate] = []
    keys = sorted(grouped)
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


def _array_l2(left: np.ndarray | None, right: np.ndarray | None) -> float:
    if left is None or right is None:
        return float("nan")
    left_arr = np.asarray(left, dtype=np.float64).reshape(-1)
    right_arr = np.asarray(right, dtype=np.float64).reshape(-1)
    if left_arr.shape != right_arr.shape:
        return float("nan")
    return float(np.linalg.norm(left_arr - right_arr))


def _hidden_l2(left: Any, right: Any) -> float:
    if left is None or right is None:
        return float("nan")
    left_arr = left.detach().cpu().numpy().astype(np.float64).reshape(-1)
    right_arr = right.detach().cpu().numpy().astype(np.float64).reshape(-1)
    if left_arr.shape != right_arr.shape:
        return float("nan")
    return float(np.linalg.norm(left_arr - right_arr))


def _response_action_frame(replay: AnchorReplayState) -> np.ndarray | None:
    if replay.response_action_frame is not None:
        return np.asarray(replay.response_action_frame, dtype=np.float64)
    if replay.observation is not None:
        return np.asarray(replay.observation[:12], dtype=np.float64)
    return None


def _context_frame(replay: AnchorReplayState) -> np.ndarray | None:
    if replay.observation is None:
        return None
    return np.asarray(replay.observation[12:], dtype=np.float64)


def tier_flags(*, response_action_l2: float, hidden_l2: float, context_l2: float) -> dict[str, bool]:
    """Return inclusive pairability tier flags with context guard."""

    response = _finite_float(response_action_l2, default=float("inf"))
    hidden = _finite_float(hidden_l2, default=0.0)
    context = _finite_float(context_l2, default=float("inf"))
    context_ok = context <= CONTEXT_L2_MAX
    return {
        "context_ok": context_ok,
        "tier_a_strict": context_ok and response <= TIER_A_RESPONSE_ACTION_L2_MAX and hidden >= TIER_A_HIDDEN_L2_MIN,
        "tier_b_moderate": context_ok and response <= TIER_B_RESPONSE_ACTION_L2_MAX and hidden >= TIER_B_HIDDEN_L2_MIN,
        "tier_c_diagnostic": context_ok and response <= TIER_C_RESPONSE_ACTION_L2_MAX and hidden >= TIER_C_HIDDEN_L2_MIN,
        "raw_tier_b_no_context_guard": response <= TIER_B_RESPONSE_ACTION_L2_MAX and hidden >= TIER_B_HIDDEN_L2_MIN,
    }


def tier_label(*, response_action_l2: float, hidden_l2: float, context_l2: float) -> str:
    """Classify one pair into the strongest pre-registered pairability tier."""

    flags = tier_flags(response_action_l2=response_action_l2, hidden_l2=hidden_l2, context_l2=context_l2)
    if flags["tier_a_strict"]:
        return "tier_a_strict"
    if flags["tier_b_moderate"]:
        return "tier_b_moderate"
    if flags["tier_c_diagnostic"]:
        return "tier_c_diagnostic"
    if flags["raw_tier_b_no_context_guard"]:
        return "context_mismatch_dominated"
    return "not_pairable"


def _source_edge(left: AnchorCandidate, right: AnchorCandidate) -> str:
    return "|".join(sorted((str(left.source_family), str(right.source_family))))


def _same_outcome(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return (
        bool(left.get("normal_success", False)) == bool(right.get("normal_success", False))
        and bool(left.get("normal_collision", False)) == bool(right.get("normal_collision", False))
    )


def build_pairability_pair_rows(
    candidates: Sequence[AnchorCandidate],
    replays: Mapping[str, AnchorReplayState],
    anchor_rows: Sequence[Mapping[str, Any]],
    *,
    max_pairs: int,
) -> list[dict[str, Any]]:
    """Build ranked cross-source pairability rows."""

    row_by_anchor = {str(row.get("anchor_id", "")): row for row in anchor_rows}
    replay_ok = [candidate for candidate in candidates if str(row_by_anchor.get(candidate.anchor_id, {}).get("normal_replay_status", "")) == "ok"]
    rows: list[dict[str, Any]] = []
    for left_index, left in enumerate(replay_ok):
        left_replay = replays.get(left.anchor_id)
        left_row = row_by_anchor.get(left.anchor_id, {})
        if left_replay is None:
            continue
        for right in replay_ok[left_index + 1 :]:
            if right.source_family == left.source_family:
                continue
            right_replay = replays.get(right.anchor_id)
            right_row = row_by_anchor.get(right.anchor_id, {})
            if right_replay is None:
                continue
            response_l2 = _array_l2(_response_action_frame(left_replay), _response_action_frame(right_replay))
            context_l2 = _array_l2(_context_frame(left_replay), _context_frame(right_replay))
            hidden_l2 = _hidden_l2(left_replay.hidden, right_replay.hidden)
            flags = tier_flags(response_action_l2=response_l2, hidden_l2=hidden_l2, context_l2=context_l2)
            label = tier_label(response_action_l2=response_l2, hidden_l2=hidden_l2, context_l2=context_l2)
            rows.append(
                {
                    "pair_id": f"pair-{len(rows):06d}",
                    "left_anchor_id": left.anchor_id,
                    "right_anchor_id": right.anchor_id,
                    "left_source_family": left.source_family,
                    "right_source_family": right.source_family,
                    "source_edge": _source_edge(left, right),
                    "left_task_family": left.task_family,
                    "right_task_family": right.task_family,
                    "left_anchor_window": left.anchor_window,
                    "right_anchor_window": right.anchor_window,
                    "left_anchor_step": int(left.anchor_step),
                    "right_anchor_step": int(right.anchor_step),
                    "anchor_step_distance": abs(int(left.anchor_step) - int(right.anchor_step)),
                    "same_window": left.anchor_window == right.anchor_window,
                    "same_task_family": left.task_family == right.task_family,
                    "same_outcome": _same_outcome(left_row, right_row),
                    "left_normal_terminal_margin": left_row.get("normal_terminal_margin", ""),
                    "right_normal_terminal_margin": right_row.get("normal_terminal_margin", ""),
                    "response_action_l2": response_l2,
                    "context_l2": context_l2,
                    "hidden_l2": hidden_l2,
                    "context_ok": flags["context_ok"],
                    "tier_a_strict": flags["tier_a_strict"],
                    "tier_b_moderate": flags["tier_b_moderate"],
                    "tier_c_diagnostic": flags["tier_c_diagnostic"],
                    "raw_tier_b_no_context_guard": flags["raw_tier_b_no_context_guard"],
                    "tier_label": label,
                    "high_speed_or_late_pair": left.source_family in HIGH_SPEED_LATE_FAMILIES or right.source_family in HIGH_SPEED_LATE_FAMILIES,
                }
            )
    def score(row: Mapping[str, Any]) -> tuple[Any, ...]:
        label = str(row.get("tier_label", ""))
        tier_rank = {
            "tier_a_strict": 0,
            "tier_b_moderate": 1,
            "tier_c_diagnostic": 2,
            "context_mismatch_dominated": 3,
            "not_pairable": 4,
        }.get(label, 5)
        return (
            tier_rank,
            _finite_float(row.get("response_action_l2"), default=1e9),
            -_finite_float(row.get("hidden_l2"), default=0.0),
            _finite_float(row.get("context_l2"), default=1e9),
            str(row.get("source_edge", "")),
            str(row.get("pair_id", "")),
        )

    rows.sort(key=score)
    return rows[: max(0, int(max_pairs))]


def _pairable_rows(rows: Sequence[Mapping[str, Any]], tier: str = "tier_b_moderate") -> list[Mapping[str, Any]]:
    return [row for row in rows if bool(row.get(tier, False))]


def _endpoint_families(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        result.add(str(row.get("left_source_family", "")))
        result.add(str(row.get("right_source_family", "")))
    return {item for item in result if item}


def _endpoint_windows(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        result.add(str(row.get("left_anchor_window", "")))
        result.add(str(row.get("right_anchor_window", "")))
    return {item for item in result if item}


def group_pairability_summary(rows: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    result: list[dict[str, Any]] = []
    for value, group in sorted(grouped.items()):
        result.append(
            {
                key: value,
                "pair_count": len(group),
                "tier_a_pair_count": sum(1 for row in group if bool(row.get("tier_a_strict", False))),
                "tier_b_pair_count": sum(1 for row in group if bool(row.get("tier_b_moderate", False))),
                "tier_c_pair_count": sum(1 for row in group if bool(row.get("tier_c_diagnostic", False))),
                "context_mismatch_count": sum(1 for row in group if row.get("tier_label") == "context_mismatch_dominated"),
                "min_response_action_l2": min((_finite_float(row.get("response_action_l2"), default=float("inf")) for row in group), default=float("nan")),
                "max_hidden_l2": max((_finite_float(row.get("hidden_l2")) for row in group), default=0.0),
            }
        )
    return result


def source_family_endpoint_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("left_source_family", ""))].append(row)
        grouped[str(row.get("right_source_family", ""))].append(row)
    result: list[dict[str, Any]] = []
    for family, group in sorted(grouped.items()):
        result.append(
            {
                "source_family": family,
                "endpoint_pair_count": len(group),
                "tier_a_endpoint_pair_count": sum(1 for row in group if bool(row.get("tier_a_strict", False))),
                "tier_b_endpoint_pair_count": sum(1 for row in group if bool(row.get("tier_b_moderate", False))),
                "tier_c_endpoint_pair_count": sum(1 for row in group if bool(row.get("tier_c_diagnostic", False))),
                "high_speed_or_late_family": family in HIGH_SPEED_LATE_FAMILIES,
            }
        )
    return result


def threshold_sweep_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    thresholds = (
        ("tier_a_strict", TIER_A_RESPONSE_ACTION_L2_MAX, TIER_A_HIDDEN_L2_MIN, True),
        ("tier_b_moderate", TIER_B_RESPONSE_ACTION_L2_MAX, TIER_B_HIDDEN_L2_MIN, True),
        ("tier_c_diagnostic", TIER_C_RESPONSE_ACTION_L2_MAX, TIER_C_HIDDEN_L2_MIN, True),
        ("raw_tier_b_no_context_guard", TIER_B_RESPONSE_ACTION_L2_MAX, TIER_B_HIDDEN_L2_MIN, False),
    )
    result: list[dict[str, Any]] = []
    for name, response_max, hidden_min, context_guard in thresholds:
        group = [row for row in rows if bool(row.get(name, False))]
        edge_counts = Counter(str(row.get("source_edge", "")) for row in group)
        result.append(
            {
                "tier": name,
                "response_action_l2_max": response_max,
                "hidden_l2_min": hidden_min,
                "context_guard": context_guard,
                "pair_count": len(group),
                "source_edge_count": len(edge_counts),
                "endpoint_source_family_count": len(_endpoint_families(group)),
                "window_count": len(_endpoint_windows(group)),
                "high_speed_or_late_pair_count": sum(1 for row in group if bool(row.get("high_speed_or_late_pair", False))),
                "max_single_source_edge_share": _max_share(edge_counts),
            }
        )
    return result


def build_summary(
    *,
    specs: Sequence[Any],
    candidates: Sequence[AnchorCandidate],
    anchor_rows: Sequence[Mapping[str, Any]],
    pair_rows: Sequence[Mapping[str, Any]],
    max_source_specs: int,
    max_anchor_candidates: int,
    max_pairs: int,
) -> dict[str, Any]:
    replay_ok = [row for row in anchor_rows if str(row.get("normal_replay_status", "")) == "ok"]
    tier_a = _pairable_rows(pair_rows, "tier_a_strict")
    tier_b = _pairable_rows(pair_rows, "tier_b_moderate")
    tier_c = _pairable_rows(pair_rows, "tier_c_diagnostic")
    edge_counts = Counter(str(row.get("source_edge", "")) for row in tier_b)
    high_late_tier_b = [row for row in tier_b if bool(row.get("high_speed_or_late_pair", False))]
    raw_tier_b = _pairable_rows(pair_rows, "raw_tier_b_no_context_guard")
    context_mismatch = [row for row in pair_rows if row.get("tier_label") == "context_mismatch_dominated"]
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "history_pairability_source_miner_smoke",
        "source_spec_count": len(specs),
        "max_source_specs": int(max_source_specs),
        "anchor_candidate_count": len(candidates),
        "max_anchor_candidates": int(max_anchor_candidates),
        "replay_ok_anchor_count": len(replay_ok),
        "pair_screen_candidate_count": len(pair_rows),
        "max_pairs": int(max_pairs),
        "tier_a_pair_count": len(tier_a),
        "tier_b_pair_count": len(tier_b),
        "tier_c_pair_count": len(tier_c),
        "raw_tier_b_no_context_guard_pair_count": len(raw_tier_b),
        "context_mismatch_pair_count": len(context_mismatch),
        "pairable_source_edge_count": len(edge_counts),
        "pairable_target_source_family_count": len(_endpoint_families(tier_b)),
        "pairable_window_count": len(_endpoint_windows(tier_b)),
        "high_speed_or_late_pair_count": len(high_late_tier_b),
        "max_single_pairable_source_edge_share": _max_share(edge_counts),
        "classification_counts": dict(sorted(Counter(str(row.get("tier_label", "")) for row in pair_rows).items())),
        "pairable_source_edge_counts": dict(sorted(edge_counts.items())),
        "guardrail_violation_count": guardrail_violation_count,
        "history_interventions_executed": False,
        "replay_started": True,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["source_spec_count"]) >= 360
        and int(summary["anchor_candidate_count"]) >= 512
        and int(summary["replay_ok_anchor_count"]) >= 256
        and int(summary["pair_screen_candidate_count"]) >= 10000
        and int(summary["tier_b_pair_count"]) >= 64
        and int(summary["tier_a_pair_count"]) >= 8
        and int(summary["pairable_source_edge_count"]) >= 4
        and int(summary["pairable_target_source_family_count"]) >= 3
        and int(summary["pairable_window_count"]) >= 3
        and int(summary["high_speed_or_late_pair_count"]) >= 8
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["history_interventions_executed"])
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
        and int(summary["tier_b_pair_count"]) >= 160
        and int(summary["tier_a_pair_count"]) >= 24
        and int(summary["pairable_source_edge_count"]) >= 8
        and int(summary["pairable_target_source_family_count"]) >= 4
        and int(summary["pairable_window_count"]) >= 4
        and float(summary["max_single_pairable_source_edge_share"]) <= 0.35
        and int(summary["high_speed_or_late_pair_count"]) >= 24
    )
    if guardrail_violation_count > 0:
        null_class = "replay_or_contract_failure"
    elif int(summary["tier_b_pair_count"]) == 0:
        null_class = "context_mismatch_dominated" if raw_tier_b else "pairability_absent"
    elif int(summary["tier_a_pair_count"]) == 0:
        null_class = "strict_pairability_absent"
    elif float(summary["max_single_pairable_source_edge_share"]) > 0.50:
        null_class = "source_singleton_pairability"
    elif int(summary["high_speed_or_late_pair_count"]) == 0:
        null_class = "high_speed_late_pairability_absent"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "pairability_public_pass"
    else:
        null_class = "public_gate_shortfall"
    summary["null_result_classification"] = null_class
    return summary


def run_history_pairability_source_miner_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1901,
    seed_count: int = 6,
    max_source_specs: int = 480,
    max_anchor_candidates: int = 640,
    max_pairs: int = 20000,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded public pairability source mining."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = pairability_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    specs_by_id = {spec.artifact_row.calibration_id: spec for spec in specs}
    candidates = build_pairability_anchor_candidates(specs, max_anchors=max_anchor_candidates)
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
        row = anchor_result_row(candidate, normal)
        hidden_norm, hidden_checksum = hidden_stats(replay.hidden)
        row.update(
            {
                "anchor_reached": bool(replay.reached_anchor),
                "replay_hidden_norm": hidden_norm,
                "replay_hidden_checksum": hidden_checksum,
                "response_action_available": _response_action_frame(replay) is not None,
                "context_available": _context_frame(replay) is not None,
            }
        )
        anchor_rows.append(row)

    pair_rows = build_pairability_pair_rows(candidates, replays, anchor_rows, max_pairs=max_pairs)
    summary = build_summary(
        specs=specs,
        candidates=candidates,
        anchor_rows=anchor_rows,
        pair_rows=pair_rows,
        max_source_specs=max_source_specs,
        max_anchor_candidates=max_anchor_candidates,
        max_pairs=max_pairs,
    )

    write_csv_rows(output / "source_spec_rows.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "anchor_candidate_rows.csv", anchor_rows)
    write_csv_rows(output / "pairability_pair_rows.csv", pair_rows)
    write_csv_rows(output / "pairability_source_edge_summary.csv", group_pairability_summary(pair_rows, "source_edge"))
    write_csv_rows(output / "pairability_source_family_summary.csv", source_family_endpoint_summary(pair_rows))
    write_csv_rows(output / "pairability_window_summary.csv", group_pairability_summary(pair_rows, "left_anchor_window"))
    write_csv_rows(output / "threshold_sweep_summary.csv", threshold_sweep_summary(pair_rows))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in FORBIDDEN_GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run history pairability source miner smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1901)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=480)
    parser.add_argument("--max-anchor-candidates", type=int, default=640)
    parser.add_argument("--max-pairs", type=int, default=20000)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_history_pairability_source_miner_smoke(
        args.output_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchor_candidates=int(args.max_anchor_candidates),
        max_pairs=int(args.max_pairs),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"pair_screen_candidate_count={summary['pair_screen_candidate_count']}")
    print(f"tier_a_pair_count={summary['tier_a_pair_count']}")
    print(f"tier_b_pair_count={summary['tier_b_pair_count']}")
    print(f"pairable_source_edge_count={summary['pairable_source_edge_count']}")
    print(f"high_speed_or_late_pair_count={summary['high_speed_or_late_pair_count']}")
    print(f"null_result_classification={summary['null_result_classification']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"passes_evidence_quality_targets={summary['passes_evidence_quality_targets']}")


if __name__ == "__main__":
    main()
