"""Source-diverse history interventions over M1570 flip anchors."""

from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_terminal_boundary_history_interventions import AnchorReplayState, replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.decisive_history_t5_interventions import _clone_hidden
from autodrift.evaluate import ActorPolicy
from autodrift.targeted_third_source_flip_anchor import targeted_source_specs
from autodrift.temporal_active_set_anchor_sensitivity_miner import _finite_float


DEFAULT_RUN_DIR = Path("runs/m1573_source_diverse_flip_anchor_history_intervention_smoke")
DEFAULT_M1570_RUN_DIR = Path("runs/m1570_targeted_third_source_flip_anchor_smoke")
VARIANTS = (
    "normal",
    "wrong_history_donor_hidden_at_anchor",
    "donor_response_action_stream_from_anchor",
    "donor_response_action_plus_hidden_from_anchor",
    "delayed_hidden_8_at_anchor",
    "delayed_hidden_16_at_anchor",
    "reset_hidden_once_at_anchor",
    "reset_hidden_every_step_from_anchor",
    "zero_current_response_from_anchor",
    "zero_action_history_from_anchor",
    "zero_all_response_from_anchor",
)
HISTORY_VARIANTS = {
    "wrong_history_donor_hidden_at_anchor",
    "donor_response_action_plus_hidden_from_anchor",
    "delayed_hidden_8_at_anchor",
    "delayed_hidden_16_at_anchor",
}
DONOR_RESPONSE_ACTION_VARIANTS = {
    "donor_response_action_stream_from_anchor",
    "donor_response_action_plus_hidden_from_anchor",
}
CONTROL_VARIANTS = {
    "reset_hidden_once_at_anchor",
    "reset_hidden_every_step_from_anchor",
    "zero_current_response_from_anchor",
    "zero_action_history_from_anchor",
    "zero_all_response_from_anchor",
}
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


@dataclass(frozen=True)
class InterventionAnchor:
    """One M1570 anchor selected for history intervention."""

    anchor_id: str
    calibration_id: str
    source_family: str
    anchor_window: str
    anchor_step: int
    normal_success: bool
    normal_collision: bool
    normal_terminal_margin: float
    max_abs_terminal_margin_gap: float
    success_flip_count: int
    collision_flip_count: int
    diagnostic_late_reveal: bool = False


@dataclass(frozen=True)
class DonorPair:
    """One target-donor pairing for intervention replay."""

    pair_id: str
    target_anchor_id: str
    donor_anchor_id: str
    target_source_family: str
    donor_source_family: str
    target_anchor_window: str
    donor_anchor_window: str
    target_anchor_step: int
    donor_anchor_step: int
    same_window: bool
    step_distance: int
    contrasting_normal_outcome: bool
    diagnostic_late_reveal: bool = False
    donor_rank: int = 0


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _read_csv(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _anchor_from_row(row: Mapping[str, Any], *, diagnostic_late_reveal: bool = False) -> InterventionAnchor:
    return InterventionAnchor(
        anchor_id=str(row["anchor_id"]),
        calibration_id=str(row["calibration_id"]),
        source_family=str(row["source_family"]),
        anchor_window=str(row["anchor_window"]),
        anchor_step=int(float(row["anchor_step"])),
        normal_success=_parse_bool(row.get("normal_success", False)),
        normal_collision=_parse_bool(row.get("normal_collision", False)),
        normal_terminal_margin=float(row.get("normal_terminal_margin") or 0.0),
        max_abs_terminal_margin_gap=float(row.get("max_abs_terminal_margin_gap") or 0.0),
        success_flip_count=int(float(row.get("success_flip_count") or 0)),
        collision_flip_count=int(float(row.get("collision_flip_count") or 0)),
        diagnostic_late_reveal=bool(diagnostic_late_reveal),
    )


def load_intervention_anchors(
    *,
    m1570_run_dir: Path | str = DEFAULT_M1570_RUN_DIR,
    max_diagnostic_late_anchors: int = 8,
) -> list[InterventionAnchor]:
    """Load primary M1570 flip anchors plus bounded late-reveal diagnostics."""

    run_dir = Path(m1570_run_dir)
    primary = [_anchor_from_row(row) for row in _read_csv(run_dir / "flip_anchor_rows.csv")]
    recoverable = _read_csv(run_dir / "recoverable_active_anchor_rows.csv")
    late_rows = [
        row
        for row in recoverable
        if str(row.get("source_family", "")) == "late_reveal_boundary"
        and _parse_bool(row.get("recoverable_boundary", False))
        and int(float(row.get("success_flip_count") or 0)) == 0
        and int(float(row.get("collision_flip_count") or 0)) == 0
    ]
    late_rows.sort(
        key=lambda row: (
            _parse_bool(row.get("strong_recoverable_boundary", False)),
            float(row.get("max_abs_terminal_margin_gap") or 0.0),
        ),
        reverse=True,
    )
    diagnostics = [
        _anchor_from_row(row, diagnostic_late_reveal=True)
        for row in late_rows[: max(0, int(max_diagnostic_late_anchors))]
    ]
    return primary + diagnostics


def _outcome_signature(anchor: InterventionAnchor) -> tuple[bool, bool]:
    return (bool(anchor.normal_success), bool(anchor.normal_collision))


def build_donor_pairs(
    anchors: Sequence[InterventionAnchor],
    *,
    donors_per_target: int = 2,
) -> list[DonorPair]:
    """Build deterministic source-diverse target-donor pairs."""

    primary = [anchor for anchor in anchors if not anchor.diagnostic_late_reveal]
    result: list[DonorPair] = []
    for target in anchors:
        donor_pool = primary if target.diagnostic_late_reveal else primary
        candidates = [
            donor
            for donor in donor_pool
            if donor.anchor_id != target.anchor_id and donor.source_family != target.source_family
        ]
        candidates.sort(
            key=lambda donor: (
                0 if donor.anchor_window == target.anchor_window else 1,
                abs(int(donor.anchor_step) - int(target.anchor_step)),
                0 if _outcome_signature(donor) != _outcome_signature(target) else 1,
                donor.source_family,
                donor.anchor_id,
            )
        )
        for rank, donor in enumerate(candidates[: max(0, int(donors_per_target))], start=1):
            result.append(
                DonorPair(
                    pair_id=f"pair-{len(result):04d}",
                    target_anchor_id=target.anchor_id,
                    donor_anchor_id=donor.anchor_id,
                    target_source_family=target.source_family,
                    donor_source_family=donor.source_family,
                    target_anchor_window=target.anchor_window,
                    donor_anchor_window=donor.anchor_window,
                    target_anchor_step=int(target.anchor_step),
                    donor_anchor_step=int(donor.anchor_step),
                    same_window=donor.anchor_window == target.anchor_window,
                    step_distance=abs(int(donor.anchor_step) - int(target.anchor_step)),
                    contrasting_normal_outcome=_outcome_signature(donor) != _outcome_signature(target),
                    diagnostic_late_reveal=bool(target.diagnostic_late_reveal),
                    donor_rank=rank,
                )
            )
    return result


def _policy_for_variant(model: Any, env_config: Any, variant: str) -> ActorPolicy:
    ablation = "none"
    reset_hidden_policy = "episode_persistent"
    if variant == "zero_current_response_from_anchor":
        ablation = "zero_current_response"
    elif variant == "zero_action_history_from_anchor":
        ablation = "zero_action_history"
    elif variant == "zero_all_response_from_anchor":
        ablation = "zero_all_response"
    elif variant == "reset_hidden_every_step_from_anchor":
        reset_hidden_policy = "every_step_control"
    return ActorPolicy(model, env_config, ablation=ablation, reset_hidden_policy=reset_hidden_policy)


def _hidden_for_variant(variant: str, target: AnchorReplayState, donor: AnchorReplayState | None) -> tuple[Any, str]:
    if variant == "normal":
        return _clone_hidden(target.hidden), "not_applicable"
    if variant in {
        "zero_current_response_from_anchor",
        "zero_action_history_from_anchor",
        "zero_all_response_from_anchor",
        "donor_response_action_stream_from_anchor",
    }:
        return _clone_hidden(target.hidden), "not_applicable"
    if variant in {"reset_hidden_once_at_anchor", "reset_hidden_every_step_from_anchor"}:
        return None, "not_applicable"
    if variant == "delayed_hidden_8_at_anchor":
        return _clone_hidden(target.hidden_by_step.get(int(target.anchor_step) - 8)), "ok"
    if variant == "delayed_hidden_16_at_anchor":
        return _clone_hidden(target.hidden_by_step.get(int(target.anchor_step) - 16)), "ok"
    if variant in {"wrong_history_donor_hidden_at_anchor", "donor_response_action_plus_hidden_from_anchor"}:
        if donor is None or not donor.reached_anchor:
            return None, "missing_donor"
        return _clone_hidden(donor.hidden), "ok"
    raise ValueError(f"unknown variant: {variant}")


def _inject_donor_response(observation: np.ndarray, donor: AnchorReplayState | None) -> np.ndarray:
    result = np.asarray(observation, dtype=np.float32).copy()
    if donor is not None and donor.response_action_frame is not None:
        result[:12] = donor.response_action_frame
    return result


def _tensor_l2(left: Any, right: Any) -> float:
    if left is None or right is None:
        return float("nan")
    left_arr = left.detach().cpu().numpy().astype(np.float64).reshape(-1)
    right_arr = right.detach().cpu().numpy().astype(np.float64).reshape(-1)
    if left_arr.shape != right_arr.shape:
        return float("nan")
    return float(np.linalg.norm(left_arr - right_arr))


def _response_l2(left: AnchorReplayState | None, right: AnchorReplayState | None) -> float:
    if left is None or right is None or left.response_action_frame is None or right.response_action_frame is None:
        return float("nan")
    return float(np.linalg.norm(np.asarray(left.response_action_frame, dtype=np.float64) - np.asarray(right.response_action_frame, dtype=np.float64)))


def _success(info: Mapping[str, Any], terminal_margin: float) -> bool:
    return bool(info.get("obstacle_completed", False)) and not bool(info.get("collision", False)) and terminal_margin > 0.0


def _continuation_reason(info: Mapping[str, Any], *, terminated: bool, truncated: bool, exhausted: bool) -> str:
    if bool(info.get("collision", False)):
        return "collision"
    if bool(info.get("obstacle_completed", False)):
        return "obstacle_completed"
    if truncated:
        return "truncated"
    if terminated:
        return "terminated"
    if exhausted:
        return "continuation_steps"
    return "running"


def _failure_row(
    *,
    pair: DonorPair,
    variant: str,
    target_status: str,
    donor_status: str,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    return {
        **asdict(pair),
        "variant": variant,
        "target_replay_status": target_status,
        "donor_replay_status": donor_status,
        "error_type": error_type,
        "error_message": error_message,
        "first_action_steer": "",
        "first_action_throttle": "",
        "first_action_brake": "",
        "first_action_l2_vs_normal": "",
        "prefix_action_l2_vs_normal": "",
        "terminal_margin": "",
        "normal_terminal_margin": "",
        "terminal_margin_gap_from_normal": "",
        "success": False,
        "success_drop_from_normal": False,
        "collision": False,
        "collision_increase_from_normal": False,
        "obstacle_completed": False,
        "terminal_reason": target_status,
        "continuation_steps": 0,
        "target_hidden_norm": "",
        "donor_hidden_norm": "",
        "target_donor_hidden_l2": "",
        "target_donor_response_action_l2": "",
    }


def run_intervention_variant(
    *,
    pair: DonorPair,
    target: AnchorReplayState,
    donor: AnchorReplayState | None,
    variant: str,
    model: Any,
    continuation_steps: int,
) -> dict[str, Any]:
    """Run one source-diverse flip-anchor intervention continuation."""

    if not target.reached_anchor:
        return _failure_row(
            pair=pair,
            variant=variant,
            target_status=target.first_failure,
            donor_status="not_run",
            error_type=target.error_type,
            error_message=target.error_message,
        )
    hidden, donor_status = _hidden_for_variant(variant, target, donor)
    if donor_status == "missing_donor":
        return _failure_row(pair=pair, variant=variant, target_status="ok", donor_status=donor_status)
    if donor_status == "ok" and hidden is None and variant.startswith("delayed_hidden"):
        return _failure_row(pair=pair, variant=variant, target_status="ok", donor_status="missing_delayed_hidden")
    assert target.env is not None
    assert target.observation is not None
    env = copy.deepcopy(target.env)
    policy = _policy_for_variant(model, target.spec.hook_spec.env_config, variant)
    policy.hidden = _clone_hidden(hidden)
    observation = np.asarray(target.observation, dtype=np.float32).copy()
    if variant in DONOR_RESPONSE_ACTION_VARIANTS:
        observation = _inject_donor_response(observation, donor)
    info = dict(target.info)
    min_margin = float(info.get("min_clearance_margin", float("nan")))
    first_action: np.ndarray | None = None
    terminated = False
    truncated = False
    steps = 0
    try:
        for _ in range(int(continuation_steps)):
            if not np.all(np.isfinite(observation)):
                raise ValueError("nonfinite_observation")
            action = np.asarray(policy.act(observation, info), dtype=np.float64)
            if not np.all(np.isfinite(action)):
                raise ValueError("nonfinite_action")
            if first_action is None:
                first_action = action.copy()
            observation, _, terminated, truncated, info = env.step(action)
            steps += 1
            margin = float(info.get("min_clearance_margin", float("nan")))
            if np.isfinite(margin):
                min_margin = min(min_margin, margin) if np.isfinite(min_margin) else margin
            if terminated or truncated:
                break
    except Exception as exc:
        return _failure_row(
            pair=pair,
            variant=variant,
            target_status="continuation_exception",
            donor_status=donor_status,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    terminal_margin = float(info.get("min_clearance_margin", min_margin))
    first = first_action if first_action is not None else np.zeros(3, dtype=np.float64)
    target_hidden_norm = float(np.linalg.norm(target.hidden.detach().cpu().numpy())) if target.hidden is not None else 0.0
    donor_hidden_norm = float(np.linalg.norm(donor.hidden.detach().cpu().numpy())) if donor is not None and donor.hidden is not None else 0.0
    return {
        **asdict(pair),
        "variant": variant,
        "target_replay_status": "ok",
        "donor_replay_status": donor_status,
        "error_type": "",
        "error_message": "",
        "first_action_steer": float(first[0]),
        "first_action_throttle": float(first[1]),
        "first_action_brake": float(first[2]),
        "first_action_l2_vs_normal": None,
        "prefix_action_l2_vs_normal": None,
        "terminal_margin": terminal_margin,
        "normal_terminal_margin": None,
        "terminal_margin_gap_from_normal": None,
        "success": _success(info, terminal_margin),
        "success_drop_from_normal": None,
        "collision": bool(info.get("collision", False)),
        "collision_increase_from_normal": None,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "terminal_reason": _continuation_reason(info, terminated=bool(terminated), truncated=bool(truncated), exhausted=not (terminated or truncated)),
        "continuation_steps": steps,
        "target_hidden_norm": target_hidden_norm,
        "donor_hidden_norm": donor_hidden_norm,
        "target_donor_hidden_l2": _tensor_l2(target.hidden, donor.hidden if donor is not None else None),
        "target_donor_response_action_l2": _response_l2(target, donor),
    }


def finalize_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add normal-relative action and outcome fields."""

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("pair_id", "")), str(row.get("target_anchor_id", "")))].append(dict(row))
    result: list[dict[str, Any]] = []
    for group in grouped.values():
        normal = next((row for row in group if row.get("variant") == "normal" and row.get("target_replay_status") == "ok"), None)
        for row in group:
            item = dict(row)
            if normal is not None and row.get("target_replay_status") == "ok":
                try:
                    action = np.asarray(
                        [
                            float(row.get("first_action_steer", 0.0)),
                            float(row.get("first_action_throttle", 0.0)),
                            float(row.get("first_action_brake", 0.0)),
                        ],
                        dtype=np.float64,
                    )
                    normal_action = np.asarray(
                        [
                            float(normal.get("first_action_steer", 0.0)),
                            float(normal.get("first_action_throttle", 0.0)),
                            float(normal.get("first_action_brake", 0.0)),
                        ],
                        dtype=np.float64,
                    )
                    normal_margin = float(normal.get("terminal_margin", float("nan")))
                    terminal_margin = float(row.get("terminal_margin", float("nan")))
                    item["first_action_l2_vs_normal"] = float(np.linalg.norm(action - normal_action))
                    item["prefix_action_l2_vs_normal"] = item["first_action_l2_vs_normal"]
                    item["normal_terminal_margin"] = normal_margin
                    item["terminal_margin_gap_from_normal"] = normal_margin - terminal_margin
                    item["success_drop_from_normal"] = bool(normal.get("success", False)) and not bool(row.get("success", False))
                    item["collision_increase_from_normal"] = (not bool(normal.get("collision", False))) and bool(row.get("collision", False))
                except (TypeError, ValueError):
                    pass
            result.append(item)
    return result


def _max_gap(rows: Sequence[Mapping[str, Any]], variants: set[str]) -> float:
    return max(
        (
            _finite_float(row.get("terminal_margin_gap_from_normal"))
            for row in rows
            if str(row.get("variant", "")) in variants
        ),
        default=0.0,
    )


def _positive_rows(rows: Sequence[Mapping[str, Any]], variants: set[str]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("variant", "")) in variants
        and (_finite_float(row.get("terminal_margin_gap_from_normal")) >= 0.02 or bool(row.get("success_drop_from_normal", False)))
    ]


def build_variant_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("variant", ""))].append(row)
    result: list[dict[str, Any]] = []
    for variant, group in sorted(grouped.items()):
        result.append(
            {
                "variant": variant,
                "row_count": len(group),
                "ok_count": sum(1 for row in group if row.get("target_replay_status") == "ok"),
                "max_margin_gap_from_normal": max((_finite_float(row.get("terminal_margin_gap_from_normal")) for row in group), default=0.0),
                "max_first_action_l2_vs_normal": max((_finite_float(row.get("first_action_l2_vs_normal")) for row in group), default=0.0),
                "success_drop_count": sum(1 for row in group if bool(row.get("success_drop_from_normal", False))),
                "collision_increase_count": sum(1 for row in group if bool(row.get("collision_increase_from_normal", False))),
            }
        )
    return result


def build_group_summary(rows: Sequence[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    result: list[dict[str, Any]] = []
    for value, group in sorted(grouped.items()):
        history_pos = _positive_rows(group, HISTORY_VARIANTS)
        control_pos = _positive_rows(group, CONTROL_VARIANTS)
        result.append(
            {
                key: value,
                "row_count": len(group),
                "target_anchor_count": len({row.get("target_anchor_id") for row in group}),
                "max_history_margin_gap": _max_gap(group, HISTORY_VARIANTS),
                "max_control_margin_gap": _max_gap(group, CONTROL_VARIANTS),
                "history_positive_count": len(history_pos),
                "control_positive_count": len(control_pos),
                "history_success_drop_count": sum(
                    1 for row in group if str(row.get("variant", "")) in HISTORY_VARIANTS and bool(row.get("success_drop_from_normal", False))
                ),
            }
        )
    return result


def build_summary(
    *,
    anchors: Sequence[InterventionAnchor],
    pairs: Sequence[DonorPair],
    rows: Sequence[dict[str, Any]],
    continuation_steps: int,
) -> dict[str, Any]:
    """Build M1573 source-diverse history-intervention summary."""

    primary_anchors = [anchor for anchor in anchors if not anchor.diagnostic_late_reveal]
    diagnostic_anchors = [anchor for anchor in anchors if anchor.diagnostic_late_reveal]
    history_rows = [row for row in rows if str(row.get("variant", "")) in HISTORY_VARIANTS]
    wrong_rows = [row for row in rows if row.get("variant") == "wrong_history_donor_hidden_at_anchor"]
    donor_rows = [row for row in rows if str(row.get("variant", "")) in DONOR_RESPONSE_ACTION_VARIANTS]
    reset_zero_rows = [row for row in rows if str(row.get("variant", "")) in CONTROL_VARIANTS]
    history_positive = _positive_rows(rows, HISTORY_VARIANTS)
    control_positive = _positive_rows(rows, CONTROL_VARIANTS)
    history_max = _max_gap(rows, HISTORY_VARIANTS)
    control_max = _max_gap(rows, CONTROL_VARIANTS)
    ratio = None if history_max <= 0.0 else control_max / history_max
    history_success_drop = sum(1 for row in history_rows if bool(row.get("success_drop_from_normal", False)))
    history_positive_families = {
        str(row.get("target_source_family", ""))
        for row in history_positive
        if not bool(row.get("diagnostic_late_reveal", False))
    }
    high_speed_history_positive = sum(
        1
        for row in history_positive
        if str(row.get("target_source_family", "")) == "t5_high_speed_close_obstacle"
    )
    late_rows = [row for row in rows if str(row.get("target_source_family", "")) == "late_reveal_boundary"]
    late_history_positive = sum(1 for row in _positive_rows(late_rows, HISTORY_VARIANTS))
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "source_diverse_flip_anchor_history_intervention_smoke",
        "target_anchor_count": len(primary_anchors),
        "diagnostic_late_anchor_count": len(diagnostic_anchors),
        "all_target_anchor_count": len(anchors),
        "target_source_family_count": len({anchor.source_family for anchor in primary_anchors}),
        "target_window_count": len({anchor.anchor_window for anchor in primary_anchors}),
        "high_speed_target_anchor_count": sum(1 for anchor in primary_anchors if anchor.source_family == "t5_high_speed_close_obstacle"),
        "late_reveal_diagnostic_anchor_count": len(diagnostic_anchors),
        "donor_pair_count": len(pairs),
        "same_window_donor_pair_count": sum(1 for pair in pairs if pair.same_window),
        "contrasting_outcome_pair_count": sum(1 for pair in pairs if pair.contrasting_normal_outcome),
        "variant_count": len(VARIANTS),
        "history_variant_count": len(HISTORY_VARIANTS),
        "control_variant_count": len(CONTROL_VARIANTS),
        "intervention_row_count": len(rows),
        "wrong_history_row_count": len(wrong_rows),
        "donor_response_action_row_count": len(donor_rows),
        "reset_zero_control_row_count": len(reset_zero_rows),
        "anchor_replay_failure_count": sum(1 for row in rows if row.get("target_replay_status") != "ok"),
        "max_wrong_history_margin_gap": _max_gap(rows, {"wrong_history_donor_hidden_at_anchor"}),
        "max_donor_response_action_margin_gap": _max_gap(rows, DONOR_RESPONSE_ACTION_VARIANTS),
        "max_history_margin_gap": history_max,
        "max_control_margin_gap": control_max,
        "control_to_history_gap_ratio": ratio,
        "history_success_drop_count": history_success_drop,
        "history_positive_source_family_count": len(history_positive_families),
        "high_speed_history_positive_count": high_speed_history_positive,
        "late_reveal_intervention_row_count": len(late_rows),
        "late_reveal_history_positive_count": late_history_positive,
        "late_reveal_control_positive_count": sum(1 for row in _positive_rows(late_rows, CONTROL_VARIANTS)),
        "late_reveal_null_status": late_history_positive == 0,
        "continuation_steps": int(continuation_steps),
        "history_interventions_executed": True,
        "replay_started": True,
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["target_anchor_count"]) >= 12
        and int(summary["target_source_family_count"]) >= 3
        and int(summary["target_window_count"]) >= 3
        and int(summary["high_speed_target_anchor_count"]) >= 4
        and int(summary["history_variant_count"]) >= 3
        and int(summary["control_variant_count"]) >= 5
        and int(summary["intervention_row_count"]) >= 240
        and int(summary["anchor_replay_failure_count"]) <= 4
        and int(summary["wrong_history_row_count"]) >= 20
        and int(summary["donor_response_action_row_count"]) >= 40
        and int(summary["reset_zero_control_row_count"]) >= 80
        and int(summary["guardrail_violation_count"]) == 0
        and bool(summary["history_interventions_executed"])
        and not bool(summary["candidate_materialized"])
        and not bool(summary["training_corpus_exported"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
    )
    history_signal = (
        float(summary["max_wrong_history_margin_gap"]) >= 0.02
        or float(summary["max_donor_response_action_margin_gap"]) >= 0.02
        or int(summary["history_success_drop_count"]) >= 1
    )
    source_signal = (
        int(summary["history_positive_source_family_count"]) >= 2
        or int(summary["high_speed_history_positive_count"]) >= 1
    )
    control_ok = ratio is not None and ratio <= 6.0 or int(summary["history_success_drop_count"]) >= 1
    summary["passes_evidence_quality_targets"] = bool(summary["passes_public_smoke_gates"]) and history_signal and source_signal and control_ok
    if not history_signal and (control_positive or float(summary["max_control_margin_gap"]) >= 0.02):
        null_class = "history_null_current_control_positive"
    elif not history_signal:
        null_class = "history_null_all_controls_null"
    elif late_rows and late_history_positive == 0:
        null_class = "late_reveal_family_null"
    else:
        null_class = "history_positive"
    summary["null_result_classification"] = null_class
    return summary


def run_source_diverse_flip_anchor_history_intervention_smoke(
    output_dir: Path | str,
    *,
    m1570_run_dir: Path | str = DEFAULT_M1570_RUN_DIR,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 6,
    max_source_specs: int = 360,
    max_diagnostic_late_anchors: int = 8,
    donors_per_target: int = 2,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded history interventions over M1570 source-diverse flip anchors."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    anchors = load_intervention_anchors(m1570_run_dir=m1570_run_dir, max_diagnostic_late_anchors=max_diagnostic_late_anchors)
    pairs = build_donor_pairs(anchors, donors_per_target=donors_per_target)
    specs = targeted_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    specs_by_id = {spec.artifact_row.calibration_id: spec for spec in specs}
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    replays: dict[str, AnchorReplayState] = {}
    for anchor in anchors:
        spec = specs_by_id.get(anchor.calibration_id)
        if spec is None:
            continue
        replays[anchor.anchor_id] = replay_to_anchor(
            pair_id=anchor.anchor_id,
            side="anchor",
            spec=spec,
            anchor_step=int(anchor.anchor_step),
            model=model,
        )
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        target = replays.get(pair.target_anchor_id)
        donor = replays.get(pair.donor_anchor_id)
        if target is None:
            for variant in VARIANTS:
                rows.append(_failure_row(pair=pair, variant=variant, target_status="missing_target_spec", donor_status="not_run"))
            continue
        for variant in VARIANTS:
            rows.append(
                run_intervention_variant(
                    pair=pair,
                    target=target,
                    donor=donor,
                    variant=variant,
                    model=model,
                    continuation_steps=continuation_steps,
                )
            )
    finalized = finalize_rows(rows)
    summary = build_summary(anchors=anchors, pairs=pairs, rows=finalized, continuation_steps=continuation_steps)
    write_csv_rows(output / "target_anchor_rows.csv", [asdict(anchor) for anchor in anchors])
    write_csv_rows(output / "donor_pair_rows.csv", [asdict(pair) for pair in pairs])
    write_csv_rows(
        output / "anchor_replay_rows.csv",
        [
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
        ],
    )
    write_csv_rows(output / "history_intervention_rows.csv", finalized)
    write_csv_rows(output / "history_intervention_variant_summary.csv", build_variant_summary(finalized))
    write_csv_rows(output / "history_intervention_source_family_summary.csv", build_group_summary(finalized, "target_source_family"))
    write_csv_rows(output / "history_intervention_window_summary.csv", build_group_summary(finalized, "target_anchor_window"))
    write_csv_rows(output / "history_intervention_pair_summary.csv", build_group_summary(finalized, "pair_id"))
    write_csv_rows(output / "history_intervention_guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in {**FORBIDDEN_GUARDRAILS, "history_interventions_executed": False}.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run source-diverse flip-anchor history interventions.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--m1570-run-dir", type=Path, default=DEFAULT_M1570_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=360)
    parser.add_argument("--max-diagnostic-late-anchors", type=int, default=8)
    parser.add_argument("--donors-per-target", type=int, default=2)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_source_diverse_flip_anchor_history_intervention_smoke(
        args.output_dir,
        m1570_run_dir=args.m1570_run_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_diagnostic_late_anchors=int(args.max_diagnostic_late_anchors),
        donors_per_target=int(args.donors_per_target),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"target_anchor_count={summary['target_anchor_count']}")
    print(f"intervention_row_count={summary['intervention_row_count']}")
    print(f"max_history_margin_gap={summary['max_history_margin_gap']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"passes_evidence_quality_targets={summary['passes_evidence_quality_targets']}")


if __name__ == "__main__":
    main()
