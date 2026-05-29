"""Bounded calibrated terminal-boundary history interventions."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract, hidden_stats, phase_for_step
from autodrift.decisive_history_t5_interventions import _clone_hidden
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy
from autodrift.fresh_ambiguity_history_interventions import (
    VARIANTS,
    build_pair_summary,
    build_variant_summary,
    finalize_rows,
)
from autodrift.terminal_boundary_task_sampling_calibration import (
    CalibrationSpec,
    build_calibration_specs,
    terminal_calibration_source_rows,
)


DEFAULT_ACCEPTED_CALIBRATED_ROWS = Path(
    "runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv"
)
DEFAULT_RUN_DIR = Path("runs/m1547_calibrated_terminal_boundary_history_intervention_smoke")
WINDOWS = {
    "decision": (-0.03, 0.12),
    "post_decision": (-0.05, 0.10),
}
GUARDRAILS = {
    "candidate_materialized": False,
    "training_started": False,
    "evaluation_started": False,
    "replay_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "training_corpus_exported": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}
TERMINAL_MARGIN_GAP_THRESHOLD = 0.02
CONTROL_TO_HISTORY_RATIO_MAX = 4.0


@dataclass(frozen=True)
class AcceptedCalibratedSource:
    """Accepted M1544 calibration row used as a source for interventions."""

    calibration_id: str
    trace_id: str
    source_row_id: str
    source_family: str
    seed: int
    mode_name: str
    window_kind: str
    decision_margin: float
    post_decision_margin: float
    terminal_margin: float
    decision_window_hit: bool
    post_decision_window_hit: bool
    terminal_reason: str
    collision: bool
    obstacle_completed: bool


@dataclass(frozen=True)
class CalibratedMeasuredSnapshot:
    """Measured snapshot with response/context vectors for pair construction."""

    calibration_id: str
    trace_id: str
    source_family: str
    seed: int
    snapshot_kind: str
    window_kind: str
    anchor_step: int
    response_vector: tuple[float, ...]
    context_vector: tuple[float, ...]
    action_vector: tuple[float, float, float]
    hidden_norm: float
    hidden_checksum: float
    min_clearance_margin: float
    terminal_margin: float
    collision: bool
    obstacle_completed: bool
    terminal_reason: str


@dataclass(frozen=True)
class CalibratedMeasuredTraceAttempt:
    """One calibrated measured trace attempt summary."""

    calibration_id: str
    trace_id: str
    source_family: str
    seed: int
    rows: int
    reached_decision: bool
    reached_post_decision: bool
    accepted_snapshot_count: int
    terminal_reason: str
    failure_type: str
    error_type: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class CalibratedMeasuredPair:
    """One accepted measured pair over calibrated terminal-boundary snapshots."""

    pair_id: str
    left_calibration_id: str
    right_calibration_id: str
    left_source_family: str
    right_source_family: str
    left_window_kind: str
    right_window_kind: str
    left_anchor_step: int
    right_anchor_step: int
    scene_context_distance: float
    current_ego_distance: float
    first_action_l2: float
    terminal_margin_gap: float
    window_pair_kind: str


@dataclass
class AnchorReplayState:
    """Replay state immediately before one calibrated anchor action."""

    pair_id: str
    side: str
    spec: CalibrationSpec
    anchor_step: int
    env: AutoDriftEnv | None
    observation: np.ndarray | None
    info: dict[str, Any]
    hidden: torch.Tensor | None
    hidden_by_step: dict[int, torch.Tensor]
    response_action_frame: np.ndarray | None
    first_failure: str = "none"
    error_type: str = ""
    error_message: str = ""

    @property
    def reached_anchor(self) -> bool:
        return self.env is not None and self.observation is not None and self.first_failure == "none"


def _to_bool(value: Any) -> bool:
    return str(value).lower() == "true" if isinstance(value, str) else bool(value)


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def load_accepted_calibrated_sources(path: Path | str = DEFAULT_ACCEPTED_CALIBRATED_ROWS) -> list[AcceptedCalibratedSource]:
    """Load accepted M1544 calibrated rows."""

    rows: list[AcceptedCalibratedSource] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                AcceptedCalibratedSource(
                    calibration_id=str(row["calibration_id"]),
                    trace_id=str(row["trace_id"]),
                    source_row_id=str(row["source_row_id"]),
                    source_family=str(row["source_family"]),
                    seed=int(row["seed"]),
                    mode_name=str(row["mode_name"]),
                    window_kind=str(row["window_kind"]),
                    decision_margin=_to_float(row.get("decision_margin")),
                    post_decision_margin=_to_float(row.get("post_decision_margin")),
                    terminal_margin=_to_float(row.get("terminal_margin")),
                    decision_window_hit=_to_bool(row.get("decision_window_hit")),
                    post_decision_window_hit=_to_bool(row.get("post_decision_window_hit")),
                    terminal_reason=str(row.get("terminal_reason", "")),
                    collision=_to_bool(row.get("collision")),
                    obstacle_completed=_to_bool(row.get("obstacle_completed")),
                )
            )
    return rows


def accepted_specs_by_id(
    accepted: Sequence[AcceptedCalibratedSource],
    *,
    seed: int = 1843,
    seed_count: int = 2,
    max_base_rows: int = 20,
    max_calibration_specs: int = 160,
) -> dict[str, CalibrationSpec]:
    """Rebuild M1544 calibration specs and keep accepted ids."""

    source_rows = terminal_calibration_source_rows(seed=seed, seed_count=seed_count, max_base_rows=max_base_rows)
    specs = build_calibration_specs(source_rows, max_calibration_specs=max_calibration_specs)
    wanted = {row.calibration_id for row in accepted}
    return {spec.artifact_row.calibration_id: spec for spec in specs if spec.artifact_row.calibration_id in wanted}


def _checksum(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    return float(np.sum(np.round(values.astype(np.float64, copy=False), 6)))


def _terminal_reason(info: Mapping[str, Any], terminated: bool, truncated: bool, exhausted: bool) -> str:
    if bool(info.get("collision", False)):
        return "collision"
    if bool(info.get("obstacle_completed", False)):
        return "obstacle_completed"
    if truncated:
        return "truncated"
    if terminated:
        return "terminated"
    if exhausted:
        return "max_rollout_steps"
    return "running"


def _snapshot_kind_for_step(step: int, decision_step: int) -> str:
    if step == decision_step:
        return "decision"
    if step == decision_step + 8:
        return "post_decision_8"
    if step == decision_step + 16:
        return "post_decision_16"
    return f"step_{step}"


def _window_kind(snapshot_kind: str, margin: float) -> str | None:
    if snapshot_kind == "decision" and WINDOWS["decision"][0] <= margin <= WINDOWS["decision"][1]:
        return "decision"
    if snapshot_kind.startswith("post_decision") and WINDOWS["post_decision"][0] <= margin <= WINDOWS["post_decision"][1]:
        return "post_decision"
    return None


def run_calibrated_measured_trace(
    accepted: AcceptedCalibratedSource,
    spec: CalibrationSpec,
    policy: ActorPolicy,
    *,
    max_rollout_steps: int = 128,
) -> tuple[list[dict[str, Any]], list[CalibratedMeasuredSnapshot], CalibratedMeasuredTraceAttempt]:
    """Run one calibrated trace and collect measured response/context snapshots."""

    hook = spec.hook_spec
    trace_id = f"{hook.source_family}|{hook.seed}|{hook.candidate_id}"
    trace_rows: list[dict[str, Any]] = []
    snapshots: list[CalibratedMeasuredSnapshot] = []
    target_steps = {int(hook.decision_step), int(hook.decision_step) + 8, int(hook.decision_step) + 16}
    try:
        env = AutoDriftEnv(hook.env_config)
        observation, info = env.reset(seed=int(hook.seed))
        policy.env_config = hook.env_config
        policy.reset()
        terminated = False
        truncated = False
        for _ in range(int(max_rollout_steps)):
            obs = np.asarray(observation, dtype=np.float64)
            if not np.all(np.isfinite(obs)):
                raise ValueError("nonfinite_observation")
            step = int(info.get("step", len(trace_rows)))
            action = np.asarray(policy.act(observation, info), dtype=np.float64)
            if not np.all(np.isfinite(action)):
                raise ValueError("nonfinite_action")
            hidden_norm, hidden_checksum = hidden_stats(policy.hidden)
            next_observation, reward, terminated, truncated, next_info = env.step(action)
            terminal = _terminal_reason(next_info, bool(terminated), bool(truncated), exhausted=False)
            margin = float(next_info.get("min_clearance_margin", float("nan")))
            row = {
                "calibration_id": accepted.calibration_id,
                "trace_id": trace_id,
                "source_family": hook.source_family,
                "seed": int(hook.seed),
                "step": step,
                "phase": phase_for_step(step, int(hook.reveal_step), int(hook.decision_step), terminal=terminated or truncated),
                "reward": float(reward),
                "action_steer": float(action[0]),
                "action_throttle": float(action[1]),
                "action_brake": float(action[2]),
                "hidden_norm": float(hidden_norm),
                "hidden_checksum": float(hidden_checksum),
                "min_clearance_margin": margin,
                "collision": bool(next_info.get("collision", False)),
                "obstacle_completed": bool(next_info.get("obstacle_completed", False)),
                "terminal_reason": terminal,
            }
            trace_rows.append(row)
            if step in target_steps and np.isfinite(margin):
                snapshot_kind = _snapshot_kind_for_step(step, int(hook.decision_step))
                window_kind = _window_kind(snapshot_kind, margin)
                if window_kind is not None:
                    snapshots.append(
                        CalibratedMeasuredSnapshot(
                            calibration_id=accepted.calibration_id,
                            trace_id=trace_id,
                            source_family=hook.source_family,
                            seed=int(hook.seed),
                            snapshot_kind=snapshot_kind,
                            window_kind=window_kind,
                            anchor_step=step,
                            response_vector=tuple(float(value) for value in obs[:12]),
                            context_vector=tuple(float(value) for value in obs[12:]),
                            action_vector=(float(action[0]), float(action[1]), float(action[2])),
                            hidden_norm=float(hidden_norm),
                            hidden_checksum=float(hidden_checksum),
                            min_clearance_margin=margin,
                            terminal_margin=margin,
                            collision=bool(next_info.get("collision", False)),
                            obstacle_completed=bool(next_info.get("obstacle_completed", False)),
                            terminal_reason=terminal,
                        )
                    )
            observation = next_observation
            info = next_info
            if terminated or truncated:
                break
    except Exception as exc:
        return trace_rows, snapshots, CalibratedMeasuredTraceAttempt(
            calibration_id=accepted.calibration_id,
            trace_id=trace_id,
            source_family=hook.source_family,
            seed=int(hook.seed),
            rows=len(trace_rows),
            reached_decision=any(int(row["step"]) >= hook.decision_step for row in trace_rows),
            reached_post_decision=any(int(row["step"]) > hook.decision_step for row in trace_rows),
            accepted_snapshot_count=len(snapshots),
            terminal_reason=trace_rows[-1]["terminal_reason"] if trace_rows else "exception",
            failure_type="rollout_exception" if trace_rows else "reset_failure",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    exhausted = bool(trace_rows) and not bool(trace_rows[-1].get("terminal_reason") in {"collision", "obstacle_completed", "terminated", "truncated"})
    terminal = str(trace_rows[-1]["terminal_reason"]) if trace_rows else "empty"
    failure = "none"
    if not any(int(row["step"]) >= hook.decision_step for row in trace_rows):
        failure = "did_not_reach_decision_step"
    return trace_rows, snapshots, CalibratedMeasuredTraceAttempt(
        calibration_id=accepted.calibration_id,
        trace_id=trace_id,
        source_family=hook.source_family,
        seed=int(hook.seed),
        rows=len(trace_rows),
        reached_decision=any(int(row["step"]) >= hook.decision_step for row in trace_rows),
        reached_post_decision=any(int(row["step"]) > hook.decision_step for row in trace_rows),
        accepted_snapshot_count=len(snapshots),
        terminal_reason="max_rollout_steps" if exhausted else terminal,
        failure_type=failure,
    )


def _vector_distance(left: Sequence[float], right: Sequence[float]) -> float:
    left_arr = np.asarray(left, dtype=np.float64)
    right_arr = np.asarray(right, dtype=np.float64)
    if left_arr.size == 0 or right_arr.size == 0 or left_arr.shape != right_arr.shape:
        return float("inf")
    return float(np.linalg.norm(left_arr - right_arr) / np.sqrt(float(left_arr.size)))


def _action_distance(left: Sequence[float], right: Sequence[float]) -> float:
    return float(np.linalg.norm(np.asarray(left, dtype=np.float64) - np.asarray(right, dtype=np.float64)))


def build_calibrated_pair_candidates(
    snapshots: Sequence[CalibratedMeasuredSnapshot],
    *,
    max_pairs: int = 12,
) -> list[CalibratedMeasuredPair]:
    """Build accepted calibrated measured pairs with scene/current gates."""

    pairs: list[CalibratedMeasuredPair] = []
    seen: set[tuple[str, str, int, int]] = set()
    for left in snapshots:
        candidates = [
            right
            for right in snapshots
            if right.calibration_id != left.calibration_id and right.source_family != left.source_family
        ]
        if not candidates:
            continue
        right = min(
            candidates,
            key=lambda item: _vector_distance(left.context_vector, item.context_vector)
            + _vector_distance(left.response_vector, item.response_vector),
        )
        key = tuple(sorted((left.calibration_id, right.calibration_id))) + tuple(sorted((left.anchor_step, right.anchor_step)))
        if key in seen:
            continue
        seen.add(key)
        scene_distance = _vector_distance(left.context_vector, right.context_vector)
        current_distance = _vector_distance(left.response_vector, right.response_vector)
        action_l2 = _action_distance(left.action_vector, right.action_vector)
        margin_gap = abs(float(left.min_clearance_margin) - float(right.min_clearance_margin))
        if scene_distance > 0.12 or current_distance > 0.12 or action_l2 < 0.04 or margin_gap < 0.02:
            continue
        pairs.append(
            CalibratedMeasuredPair(
                pair_id=f"pair-{len(pairs):04d}",
                left_calibration_id=left.calibration_id,
                right_calibration_id=right.calibration_id,
                left_source_family=left.source_family,
                right_source_family=right.source_family,
                left_window_kind=left.window_kind,
                right_window_kind=right.window_kind,
                left_anchor_step=int(left.anchor_step),
                right_anchor_step=int(right.anchor_step),
                scene_context_distance=scene_distance,
                current_ego_distance=current_distance,
                first_action_l2=action_l2,
                terminal_margin_gap=margin_gap,
                window_pair_kind=f"{left.window_kind}|{right.window_kind}",
            )
        )
        if len(pairs) >= int(max_pairs):
            break
    return pairs


def replay_to_anchor(
    *,
    pair_id: str,
    side: str,
    spec: CalibrationSpec,
    anchor_step: int,
    model: Any,
) -> AnchorReplayState:
    """Replay fixed actor until just before a calibrated anchor action."""

    hook = spec.hook_spec
    hidden_by_step: dict[int, torch.Tensor] = {}
    policy = ActorPolicy(model, hook.env_config)
    try:
        env = AutoDriftEnv(hook.env_config)
        observation, info = env.reset(seed=int(hook.seed))
        policy.reset()
        while int(info.get("step", 0)) < int(anchor_step):
            if not np.all(np.isfinite(observation)):
                raise ValueError("nonfinite_observation")
            step = int(info.get("step", len(hidden_by_step)))
            action = policy.act(observation, info)
            if not np.all(np.isfinite(action)):
                raise ValueError("nonfinite_action")
            hidden_by_step[step] = _clone_hidden(policy.hidden)
            observation, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                return AnchorReplayState(
                    pair_id=pair_id,
                    side=side,
                    spec=spec,
                    anchor_step=anchor_step,
                    env=None,
                    observation=None,
                    info=info,
                    hidden=_clone_hidden(policy.hidden),
                    hidden_by_step=hidden_by_step,
                    response_action_frame=None,
                    first_failure="did_not_reach_anchor_step",
                )
        return AnchorReplayState(
            pair_id=pair_id,
            side=side,
            spec=spec,
            anchor_step=anchor_step,
            env=env,
            observation=np.asarray(observation, dtype=np.float32),
            info=info,
            hidden=_clone_hidden(policy.hidden),
            hidden_by_step=hidden_by_step,
            response_action_frame=np.asarray(observation[:12], dtype=np.float32).copy(),
        )
    except Exception as exc:
        return AnchorReplayState(
            pair_id=pair_id,
            side=side,
            spec=spec,
            anchor_step=anchor_step,
            env=None,
            observation=None,
            info={},
            hidden=_clone_hidden(policy.hidden),
            hidden_by_step=hidden_by_step,
            response_action_frame=None,
            first_failure="target_replay_exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


def _success(info: Mapping[str, Any], terminal_margin: float) -> bool:
    return bool(info.get("obstacle_completed", False)) and not bool(info.get("collision", False)) and terminal_margin > 0.0


def _continuation_reason(info: Mapping[str, Any], terminated: bool, truncated: bool, exhausted: bool) -> str:
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


def _policy_for_variant(model: Any, spec: CalibrationSpec, variant: str) -> ActorPolicy:
    ablation = "none"
    reset_hidden_policy = "episode_persistent"
    if variant == "zero_current_response_from_anchor":
        ablation = "zero_current_response"
    elif variant == "zero_action_history_from_anchor":
        ablation = "zero_action_history"
    elif variant == "reset_hidden_every_step_from_anchor":
        reset_hidden_policy = "every_step_control"
    return ActorPolicy(model, spec.hook_spec.env_config, ablation=ablation, reset_hidden_policy=reset_hidden_policy)


def _hidden_for_variant(variant: str, target: AnchorReplayState, donor: AnchorReplayState | None) -> tuple[torch.Tensor | None, str]:
    if variant == "normal":
        return _clone_hidden(target.hidden), "not_applicable"
    if variant in {"zero_current_response_from_anchor", "zero_action_history_from_anchor", "donor_response_action_stream_from_anchor"}:
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


def _failure_row(
    *,
    pair: CalibratedMeasuredPair,
    target_side: str,
    donor_side: str,
    variant: str,
    target: AnchorReplayState | None,
    target_status: str,
    donor_status: str,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    return {
        "pair_id": pair.pair_id,
        "target_side": target_side,
        "donor_side": donor_side,
        "anchor_name": f"{target_side}_calibrated_anchor",
        "anchor_step": target.anchor_step if target is not None else "",
        "variant": variant,
        "target_source_family": target.spec.source_row.source_family if target is not None else "",
        "donor_source_family": "",
        "target_replay_status": target_status,
        "donor_replay_status": donor_status,
        "error_type": error_type,
        "error_message": error_message,
        "first_action_steer": "",
        "first_action_throttle": "",
        "first_action_brake": "",
        "normal_first_action_l2": "",
        "terminal_margin": "",
        "normal_terminal_margin": "",
        "terminal_margin_gap_from_normal": "",
        "success": False,
        "success_drop_from_normal": False,
        "collision": False,
        "obstacle_completed": False,
        "terminal_reason": target_status,
        "continuation_steps": 0,
    }


def run_intervention_variant(
    *,
    pair: CalibratedMeasuredPair,
    target_side: str,
    target_spec: CalibrationSpec,
    target_anchor_step: int,
    donor_side: str,
    donor_spec: CalibrationSpec,
    donor_anchor_step: int,
    variant: str,
    model: Any,
    continuation_steps: int = 64,
) -> dict[str, Any]:
    """Run one calibrated history intervention continuation."""

    target = replay_to_anchor(pair_id=pair.pair_id, side=target_side, spec=target_spec, anchor_step=target_anchor_step, model=model)
    donor = replay_to_anchor(pair_id=pair.pair_id, side=donor_side, spec=donor_spec, anchor_step=donor_anchor_step, model=model)
    if not target.reached_anchor:
        return _failure_row(
            pair=pair,
            target_side=target_side,
            donor_side=donor_side,
            variant=variant,
            target=target,
            target_status=target.first_failure,
            donor_status="not_run",
            error_type=target.error_type,
            error_message=target.error_message,
        )
    hidden, donor_status = _hidden_for_variant(variant, target, donor)
    if donor_status == "missing_donor":
        return _failure_row(
            pair=pair,
            target_side=target_side,
            donor_side=donor_side,
            variant=variant,
            target=target,
            target_status="ok",
            donor_status=donor_status,
        )
    if donor_status == "ok" and hidden is None and variant.startswith("delayed_hidden"):
        return _failure_row(
            pair=pair,
            target_side=target_side,
            donor_side=donor_side,
            variant=variant,
            target=target,
            target_status="ok",
            donor_status="missing_delayed_hidden",
        )
    assert target.env is not None
    assert target.observation is not None
    policy = _policy_for_variant(model, target_spec, variant)
    policy.hidden = _clone_hidden(hidden)
    observation = target.observation
    if variant in {"donor_response_action_stream_from_anchor", "donor_response_action_plus_hidden_from_anchor"}:
        observation = _inject_donor_response(observation, donor)
    info = target.info
    min_margin = float(info.get("min_clearance_margin", float("nan")))
    first_action: np.ndarray | None = None
    terminated = False
    truncated = False
    steps = 0
    for _ in range(int(continuation_steps)):
        if not np.all(np.isfinite(observation)):
            raise ValueError("nonfinite_observation")
        action = policy.act(observation, info)
        if not np.all(np.isfinite(action)):
            raise ValueError("nonfinite_action")
        if first_action is None:
            first_action = np.asarray(action, dtype=np.float64)
        observation, _, terminated, truncated, info = target.env.step(action)
        steps += 1
        margin = float(info.get("min_clearance_margin", float("nan")))
        if np.isfinite(margin):
            min_margin = min(min_margin, margin) if np.isfinite(min_margin) else margin
        if terminated or truncated:
            break
    terminal_margin = float(info.get("min_clearance_margin", min_margin))
    first = first_action if first_action is not None else np.zeros(3, dtype=np.float64)
    return {
        "pair_id": pair.pair_id,
        "target_side": target_side,
        "donor_side": donor_side,
        "anchor_name": f"{target_side}_calibrated_anchor",
        "anchor_step": target.anchor_step,
        "variant": variant,
        "target_source_family": target_spec.source_row.source_family,
        "donor_source_family": donor_spec.source_row.source_family,
        "target_replay_status": "ok",
        "donor_replay_status": donor_status,
        "error_type": "",
        "error_message": "",
        "first_action_steer": float(first[0]),
        "first_action_throttle": float(first[1]),
        "first_action_brake": float(first[2]),
        "normal_first_action_l2": None,
        "terminal_margin": terminal_margin,
        "normal_terminal_margin": None,
        "terminal_margin_gap_from_normal": None,
        "success": _success(info, terminal_margin),
        "success_drop_from_normal": None,
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "terminal_reason": _continuation_reason(info, bool(terminated), bool(truncated), exhausted=not (terminated or truncated)),
        "continuation_steps": steps,
    }


def _source_edge_count(pairs: Sequence[CalibratedMeasuredPair]) -> int:
    return len({(pair.left_source_family, pair.right_source_family) for pair in pairs})


def _positive_count(rows: Sequence[dict[str, Any]], *, variant: str) -> int:
    return sum(
        1
        for row in rows
        if str(row.get("variant", "")) == variant
        and float(row.get("terminal_margin_gap_from_normal") or 0.0) >= TERMINAL_MARGIN_GAP_THRESHOLD
    )


def _max_gap(rows: Sequence[dict[str, Any]], variants: set[str]) -> float:
    return max(
        (float(row.get("terminal_margin_gap_from_normal") or 0.0) for row in rows if str(row.get("variant", "")) in variants),
        default=0.0,
    )


def build_summary(
    *,
    accepted_sources: Sequence[AcceptedCalibratedSource],
    snapshots: Sequence[CalibratedMeasuredSnapshot],
    attempts: Sequence[CalibratedMeasuredTraceAttempt],
    pairs: Sequence[CalibratedMeasuredPair],
    rows: Sequence[dict[str, Any]],
    continuation_steps: int,
) -> dict[str, Any]:
    """Build calibrated intervention smoke summary."""

    guardrails = dict(GUARDRAILS)
    history_max = max(
        _max_gap(rows, {"wrong_history_donor_hidden_at_anchor", "donor_response_action_plus_hidden_from_anchor"}),
        0.0,
    )
    control_max = _max_gap(
        rows,
        {
            "reset_hidden_once_at_anchor",
            "reset_hidden_every_step_from_anchor",
            "zero_current_response_from_anchor",
            "zero_action_history_from_anchor",
        },
    )
    ratio = None if history_max <= 0.0 else control_max / history_max
    success_drop = sum(
        1
        for row in rows
        if str(row.get("variant", "")) in {"wrong_history_donor_hidden_at_anchor", "donor_response_action_plus_hidden_from_anchor"}
        and bool(row.get("success_drop_from_normal", False))
    )
    source_edge_count = _source_edge_count(pairs)
    pair_edges = Counter((pair.left_source_family, pair.right_source_family) for pair in pairs)
    max_edge_share = max((count / max(1, len(pairs)) for count in pair_edges.values()), default=0.0)
    summary = {
        "result_class": "calibrated_terminal_boundary_history_intervention_smoke",
        "accepted_calibrated_source_count": len(accepted_sources),
        "measured_trace_count": len(attempts),
        "measured_snapshot_count": len(snapshots),
        "measured_trace_family_count": len({row.source_family for row in attempts}),
        "accepted_pair_count": len(pairs),
        "accepted_source_family_edge_count": source_edge_count,
        "max_single_pair_source_edge_share": max_edge_share,
        "intervention_row_count": len(rows),
        "variant_count": len(VARIANTS),
        "continuation_steps": int(continuation_steps),
        "anchor_replay_failure_count": sum(1 for row in rows if row.get("target_replay_status") != "ok"),
        "terminal_wrong_history_positive_target_sides": _positive_count(rows, variant="wrong_history_donor_hidden_at_anchor"),
        "terminal_donor_plus_hidden_positive_target_sides": _positive_count(
            rows,
            variant="donor_response_action_plus_hidden_from_anchor",
        ),
        "terminal_donor_stream_positive_target_sides": _positive_count(
            rows,
            variant="donor_response_action_stream_from_anchor",
        ),
        "terminal_wrong_or_donor_success_drop_count": success_drop,
        "terminal_max_history_margin_gap": history_max,
        "terminal_max_control_margin_gap": control_max,
        "terminal_control_to_history_gap_ratio": ratio,
        "window_pair_kind_counts": dict(sorted(Counter(pair.window_pair_kind for pair in pairs).items())),
        "failure_type_counts": dict(sorted(Counter(row.failure_type for row in attempts).items())),
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        **guardrails,
    }
    summary["passes_measured_trace_gates"] = (
        int(summary["accepted_calibrated_source_count"]) >= 8
        and int(summary["measured_trace_count"]) >= 8
        and int(summary["measured_snapshot_count"]) >= 16
        and int(summary["measured_trace_family_count"]) >= 4
        and int(summary["guardrail_violation_count"]) == 0
    )
    summary["passes_pair_gates"] = (
        int(summary["accepted_pair_count"]) >= 4
        and int(summary["accepted_source_family_edge_count"]) >= 3
        and float(summary["max_single_pair_source_edge_share"]) <= 0.50
        and int(summary["anchor_replay_failure_count"]) <= max(1, int(len(rows) * 0.05))
    )
    summary["passes_history_positive_gates"] = (
        int(summary["terminal_wrong_history_positive_target_sides"]) >= 2
        or int(summary["terminal_donor_plus_hidden_positive_target_sides"]) >= 2
        or int(summary["terminal_wrong_or_donor_success_drop_count"]) >= 1
    )
    summary["passes_control_gate"] = ratio is None or ratio <= CONTROL_TO_HISTORY_RATIO_MAX
    summary["passes_public_smoke_gates"] = (
        bool(summary["passes_measured_trace_gates"])
        and bool(summary["passes_pair_gates"])
        and int(summary["guardrail_violation_count"]) == 0
    )
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and bool(summary["passes_history_positive_gates"])
        and bool(summary["passes_control_gate"])
    )
    return summary


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row) for row in rows]


def run_calibrated_terminal_boundary_history_intervention_smoke(
    output_dir: Path | str,
    *,
    accepted_calibrated_rows: Path | str = DEFAULT_ACCEPTED_CALIBRATED_ROWS,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 2,
    max_base_rows: int = 20,
    max_calibration_specs: int = 160,
    max_pairs: int = 12,
    max_rollout_steps: int = 128,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded calibrated history intervention smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    accepted_sources = load_accepted_calibrated_sources(accepted_calibrated_rows)
    spec_by_id = accepted_specs_by_id(
        accepted_sources,
        seed=seed,
        seed_count=seed_count,
        max_base_rows=max_base_rows,
        max_calibration_specs=max_calibration_specs,
    )
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    policy = ActorPolicy(model, next(iter(spec_by_id.values())).hook_spec.env_config) if spec_by_id else None
    trace_rows: list[dict[str, Any]] = []
    snapshots: list[CalibratedMeasuredSnapshot] = []
    attempts: list[CalibratedMeasuredTraceAttempt] = []
    for accepted in accepted_sources:
        spec = spec_by_id.get(accepted.calibration_id)
        if spec is None or policy is None:
            continue
        rows, snapshot_rows, attempt = run_calibrated_measured_trace(
            accepted,
            spec,
            policy,
            max_rollout_steps=max_rollout_steps,
        )
        trace_rows.extend(rows)
        snapshots.extend(snapshot_rows)
        attempts.append(attempt)
    pairs = build_calibrated_pair_candidates(snapshots, max_pairs=max_pairs)
    intervention_rows: list[dict[str, Any]] = []
    for pair in pairs:
        left_spec = spec_by_id[pair.left_calibration_id]
        right_spec = spec_by_id[pair.right_calibration_id]
        for target_side, target_spec, target_anchor, donor_side, donor_spec, donor_anchor in (
            ("left", left_spec, pair.left_anchor_step, "right", right_spec, pair.right_anchor_step),
            ("right", right_spec, pair.right_anchor_step, "left", left_spec, pair.left_anchor_step),
        ):
            for variant in VARIANTS:
                intervention_rows.append(
                    run_intervention_variant(
                        pair=pair,
                        target_side=target_side,
                        target_spec=target_spec,
                        target_anchor_step=target_anchor,
                        donor_side=donor_side,
                        donor_spec=donor_spec,
                        donor_anchor_step=donor_anchor,
                        variant=variant,
                        model=model,
                        continuation_steps=continuation_steps,
                    )
                )
    finalized = finalize_rows(intervention_rows)
    pair_summary = build_pair_summary(finalized)
    variant_summary = build_variant_summary(finalized)
    summary = build_summary(
        accepted_sources=accepted_sources,
        snapshots=snapshots,
        attempts=attempts,
        pairs=pairs,
        rows=finalized,
        continuation_steps=continuation_steps,
    )
    write_csv_rows(output / "accepted_calibrated_source_rows.csv", _asdict_rows(accepted_sources))
    write_csv_rows(output / "measured_trace_rows.csv", trace_rows)
    write_csv_rows(output / "measured_snapshot_rows.csv", _asdict_rows(snapshots))
    write_csv_rows(output / "measured_trace_attempt_rows.csv", _asdict_rows(attempts))
    write_csv_rows(output / "measured_pair_candidates.csv", _asdict_rows(pairs))
    write_csv_rows(output / "accepted_pair_rows.csv", _asdict_rows(pairs))
    write_csv_rows(output / "intervention_rows.csv", finalized)
    write_csv_rows(output / "pair_summary.csv", pair_summary)
    write_csv_rows(output / "variant_summary.csv", variant_summary)
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run calibrated terminal-boundary history intervention smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--accepted-calibrated-rows", type=Path, default=DEFAULT_ACCEPTED_CALIBRATED_ROWS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=2)
    parser.add_argument("--max-base-rows", type=int, default=20)
    parser.add_argument("--max-calibration-specs", type=int, default=160)
    parser.add_argument("--max-pairs", type=int, default=12)
    parser.add_argument("--max-rollout-steps", type=int, default=128)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_calibrated_terminal_boundary_history_intervention_smoke(
        args.output_dir,
        accepted_calibrated_rows=args.accepted_calibrated_rows,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_base_rows=int(args.max_base_rows),
        max_calibration_specs=int(args.max_calibration_specs),
        max_pairs=int(args.max_pairs),
        max_rollout_steps=int(args.max_rollout_steps),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"accepted_pair_count={summary['accepted_pair_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
