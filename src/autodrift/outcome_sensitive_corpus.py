"""Mine matched hidden-dynamics cases where wrong history changes outcome."""

from __future__ import annotations

import argparse
import copy
from dataclasses import replace
from itertools import product
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_swap_gate import (
    DecisionSnapshot,
    clone_hidden,
    collect_decision_snapshot,
    hidden_state_distance,
    replay_pair,
)
from autodrift.matched_action_corpus import visible_observation_distances
from autodrift.paired_perturbation_gate import (
    condition_config,
    load_seed_csv,
    parse_randomization_overrides,
    parse_range,
)
from autodrift.scenarios import classify_obstacle_scenario
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM


PROBE_STRATEGIES = ("none", "steer_sine", "brake_tap", "steer_brake")


class ProbeConfig(argparse.Namespace):
    strategy: str
    steer_amplitude: float
    brake_level: float
    throttle_level: float
    period_steps: int
    until_step: int | None
    until_distance: float | None


def parse_float_list(raw: str) -> list[float]:
    values = [part.strip() for part in raw.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("list must contain at least one value")
    parsed = [float(value) for value in values]
    if any(value <= 0.0 for value in parsed):
        raise argparse.ArgumentTypeError("target obstacle distances must be positive")
    return parsed


def parse_float_values(raw: str) -> list[float]:
    values = [part.strip() for part in raw.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("list must contain at least one value")
    return [float(value) for value in values]


def _bool(value: Any) -> bool:
    return bool(value)


def _finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _finite_max(values: list[float]) -> float:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return max(finite) if finite else float("nan")


def _pedal_level_to_action(level: float) -> float:
    return float(np.clip(2.0 * float(level) - 1.0, -1.0, 1.0))


def _series(frame: pd.DataFrame, name: str, default: Any) -> pd.Series:
    if name in frame:
        return frame[name]
    return pd.Series([default] * len(frame), index=frame.index)


def _bool_series(frame: pd.DataFrame, name: str, default: bool = False) -> pd.Series:
    return _series(frame, name, default).fillna(default).astype(bool)


def _variant_row(rows: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    for row in rows:
        if row.get("variant") == variant:
            return row
    raise ValueError(f"missing replay variant {variant!r}")


def probe_action(strategy: str, step: int, config: ProbeConfig) -> np.ndarray:
    if strategy not in PROBE_STRATEGIES:
        raise ValueError(f"unknown probe strategy: {strategy}")
    if strategy == "none":
        return np.array([0.0, -1.0, -1.0], dtype=np.float32)
    period = max(int(config.period_steps), 1)
    phase = 2.0 * np.pi * (int(step) % period) / float(period)
    steer = 0.0
    throttle = 0.0
    brake = 0.0
    if strategy in {"steer_sine", "steer_brake"}:
        steer = float(config.steer_amplitude) * float(np.sin(phase))
    if strategy in {"brake_tap", "steer_brake"}:
        brake = float(config.brake_level) if (int(step) // period) % 2 == 0 else 0.0
    throttle = float(config.throttle_level)
    if brake > 0.0:
        throttle = 0.0
    return np.array(
        [
            float(np.clip(steer, -1.0, 1.0)),
            _pedal_level_to_action(throttle),
            _pedal_level_to_action(brake),
        ],
        dtype=np.float32,
    )


def should_probe(info: dict[str, Any], config: ProbeConfig) -> bool:
    if config.strategy == "none":
        return False
    step = int(info.get("step", 0))
    if not bool(info.get("obstacle_perception_visible", True)):
        return True
    if config.until_step is not None and step < int(config.until_step):
        return True
    if config.until_distance is not None:
        obstacle_distance = _float(info.get("obstacle_distance", float("nan")))
        if np.isfinite(obstacle_distance) and obstacle_distance > float(config.until_distance):
            return True
    return False


def collect_probing_decision_snapshot(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    condition: str,
    seed: int,
    *,
    target_obstacle_distance: float,
    min_probe_steps: int,
    max_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
    probe_config: ProbeConfig,
) -> DecisionSnapshot | None:
    env = AutoDriftEnv(env_config)
    obs, info = env.reset(seed=seed)
    hidden = None
    best: DecisionSnapshot | None = None
    terminated = False
    truncated = False
    probe_steps = 0
    probe_steer_abs_sum = 0.0
    probe_brake_sum = 0.0

    while not (terminated or truncated):
        step = int(info.get("step", 0))
        if (
            _snapshot_candidate_for_outcome(info, min_probe_steps, require_friction_step, min_hidden_updates_after_friction)
        ):
            obstacle_distance = float(info["obstacle_distance"])
            score = abs(obstacle_distance - target_obstacle_distance)
            if best is None or score < best.snapshot_score:
                snapshot_info = dict(info)
                snapshot_info["active_probe_strategy"] = probe_config.strategy
                snapshot_info["active_probe_steps"] = probe_steps
                snapshot_info["active_probe_steer_abs_mean"] = (
                    probe_steer_abs_sum / max(probe_steps, 1)
                    if probe_steps
                    else 0.0
                )
                snapshot_info["active_probe_brake_mean"] = (
                    probe_brake_sum / max(probe_steps, 1)
                    if probe_steps
                    else 0.0
                )
                best = DecisionSnapshot(
                    condition=condition,
                    seed=seed,
                    step=step,
                    observation=np.asarray(obs, dtype=np.float32).copy(),
                    hidden=clone_hidden(hidden),
                    env=copy.deepcopy(env),
                    info=snapshot_info,
                    obstacle_distance=obstacle_distance,
                    snapshot_score=score,
                )
            if obstacle_distance <= target_obstacle_distance:
                break
        if step >= max_probe_steps:
            break
        policy_action, _, _, next_hidden = model.act_recurrent(obs, hidden, deterministic=True)
        hidden = next_hidden
        if should_probe(info, probe_config):
            action = probe_action(probe_config.strategy, step, probe_config)
            probe_steps += 1
            probe_steer_abs_sum += abs(float(action[0]))
            probe_brake_sum += max((float(action[2]) + 1.0) * 0.5, 0.0)
        else:
            action = policy_action
        obs, _, terminated, truncated, info = env.step(action)
    return best


def _snapshot_candidate_for_outcome(
    info: dict[str, Any],
    min_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
) -> bool:
    step = int(info.get("step", 0))
    if step < min_probe_steps:
        return False
    if require_friction_step:
        if not bool(info.get("friction_step_applied", False)):
            return False
        friction_step_at = info.get("friction_step_at")
        if friction_step_at is not None and step < int(friction_step_at) + min_hidden_updates_after_friction:
            return False
    obstacle_distance = _float(info.get("obstacle_distance", float("nan")))
    return bool(np.isfinite(obstacle_distance) and obstacle_distance > 0.0)


def obstacle_override_config(
    env_config: DriftEnvConfig,
    *,
    distance_range: tuple[float, float] | None,
    half_width_range: tuple[float, float] | None,
    perception_reveal_step: int | None = None,
    perception_reveal_distance: float | None = None,
) -> DriftEnvConfig:
    if (
        distance_range is None
        and half_width_range is None
        and perception_reveal_step is None
        and perception_reveal_distance is None
    ):
        return env_config
    obstacle = env_config.obstacle
    if distance_range is not None:
        obstacle = replace(obstacle, distance_range=distance_range)
    if half_width_range is not None:
        obstacle = replace(obstacle, half_width_range=half_width_range)
    if perception_reveal_step is not None:
        obstacle = replace(obstacle, perception_reveal_step=int(perception_reveal_step))
    if perception_reveal_distance is not None:
        obstacle = replace(obstacle, perception_reveal_distance=float(perception_reveal_distance))
    return replace(env_config, obstacle=obstacle)


def snapshot_relocation_grid(
    distances: list[float] | None,
    lateral_offsets: list[float] | None,
    half_widths: list[float] | None,
) -> list[tuple[float | None, float, float | None]]:
    if distances is None and lateral_offsets is None and half_widths is None:
        return [(None, 0.0, None)]
    if distances is None:
        raise ValueError("snapshot relocation requires --snapshot-relocation-distances")
    offsets = lateral_offsets if lateral_offsets is not None else [0.0]
    widths = half_widths if half_widths is not None else [None]
    if any(distance <= 0.0 for distance in distances):
        raise ValueError("snapshot relocation distances must be positive")
    if any(width is not None and width <= 0.0 for width in widths):
        raise ValueError("snapshot relocation half-widths must be positive")
    return [(float(distance), float(offset), None if width is None else float(width)) for distance, offset, width in product(distances, offsets, widths)]


def _body_to_world(env: AutoDriftEnv, body_x: float, body_y: float) -> np.ndarray:
    cos_psi = math.cos(env.state.psi)
    sin_psi = math.sin(env.state.psi)
    return np.array(
        [
            env.state.x + cos_psi * float(body_x) - sin_psi * float(body_y),
            env.state.y + sin_psi * float(body_x) + cos_psi * float(body_y),
        ],
        dtype=np.float64,
    )


def relocate_obstacle_snapshot(
    snapshot: DecisionSnapshot,
    *,
    body_longitudinal: float,
    body_lateral: float = 0.0,
    half_width: float | None = None,
) -> DecisionSnapshot:
    if body_longitudinal <= 0.0:
        raise ValueError("body_longitudinal must be positive")
    env = copy.deepcopy(snapshot.env)
    if env.obstacle_scenario is None:
        raise ValueError("cannot relocate a snapshot without an obstacle scenario")
    relocated_half_width = (
        float(env.obstacle_scenario.obstacle_half_width) if half_width is None else float(half_width)
    )
    if relocated_half_width <= 0.0:
        raise ValueError("half_width must be positive")

    speed = max(math.hypot(env.state.vx, env.state.vy), 1e-6)
    scenario = classify_obstacle_scenario(
        speed=speed,
        mu=env.params.mu,
        obstacle_distance=float(body_longitudinal),
        obstacle_half_width=relocated_half_width,
        config=env.config.obstacle.scenario_config(speed=speed, mu=env.params.mu),
    )
    env.obstacle_scenario = scenario
    env.obstacle_position = _body_to_world(env, float(body_longitudinal), float(body_lateral))
    env.min_obstacle_clearance = float("inf")
    env.collision = False
    env.obstacle_completed = False
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    env._update_obstacle_status(frame)
    relocated_base = env._base_observation()
    if env.obs_history:
        env.obs_history[0] = relocated_base.copy()
    else:
        env.obs_history = [relocated_base.copy() for _ in range(env.config.history_length)]
    relocated_observation = env._observation()
    relocated_info = env._info(frame)
    for key, value in snapshot.info.items():
        if key.startswith("active_probe_"):
            relocated_info[key] = value
    relocated_info.update(
        {
            "snapshot_relocated": True,
            "source_obstacle_distance": snapshot.info.get("obstacle_distance", float("nan")),
            "source_obstacle_lateral_offset": snapshot.info.get("obstacle_lateral_offset", float("nan")),
            "relocated_obstacle_body_x": float(body_longitudinal),
            "relocated_obstacle_body_y": float(body_lateral),
            "relocated_obstacle_half_width": relocated_half_width,
        }
    )
    return DecisionSnapshot(
        condition=snapshot.condition,
        seed=snapshot.seed,
        step=snapshot.step,
        observation=np.asarray(relocated_observation, dtype=np.float32).copy(),
        hidden=clone_hidden(snapshot.hidden),
        env=env,
        info=relocated_info,
        obstacle_distance=float(body_longitudinal),
        snapshot_score=snapshot.snapshot_score,
    )


def source_outcome_metrics(
    source_prefix: str,
    replay_rows: list[dict[str, Any]],
    *,
    min_margin_gap: float,
    min_normal_margin: float | None,
    max_normal_margin: float | None,
    require_normal_success: bool,
) -> dict[str, Any]:
    normal = _variant_row(replay_rows, "normal")
    wrong = _variant_row(replay_rows, "hidden_swap")
    normal_success = _bool(normal.get("success", False))
    wrong_success = _bool(wrong.get("success", False))
    success_drop = bool(normal_success and not wrong_success)
    normal_margin = _float(normal.get("min_clearance_margin", float("nan")))
    wrong_margin = _float(wrong.get("min_clearance_margin", float("nan")))
    margin_gap = normal_margin - wrong_margin if _finite(normal_margin) and _finite(wrong_margin) else float("nan")
    margin_gap_accept = bool(np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap))

    normal_success_ok = normal_success or not require_normal_success
    normal_margin_ok = True
    if min_normal_margin is not None and _finite(normal_margin):
        normal_margin_ok = normal_margin_ok and normal_margin >= float(min_normal_margin)
    if max_normal_margin is not None and _finite(normal_margin):
        normal_margin_ok = normal_margin_ok and normal_margin <= float(max_normal_margin)
    accepted = bool(normal_success_ok and normal_margin_ok and (success_drop or margin_gap_accept))

    return {
        f"{source_prefix}_normal_success": normal_success,
        f"{source_prefix}_wrong_history_success": wrong_success,
        f"{source_prefix}_success_drop": success_drop,
        f"{source_prefix}_normal_margin": normal_margin,
        f"{source_prefix}_wrong_history_margin": wrong_margin,
        f"{source_prefix}_margin_gap": margin_gap,
        f"{source_prefix}_normal_return": _float(normal.get("return", float("nan"))),
        f"{source_prefix}_wrong_history_return": _float(wrong.get("return", float("nan"))),
        f"{source_prefix}_wrong_history_first_action_distance": _float(
            wrong.get("first_action_distance", float("nan"))
        ),
        f"{source_prefix}_wrong_history_action_trajectory_distance_mean": _float(
            wrong.get("action_trajectory_distance_mean", float("nan"))
        ),
        f"{source_prefix}_normal_terminal_reason": str(normal.get("terminal_reason", "")),
        f"{source_prefix}_wrong_history_terminal_reason": str(wrong.get("terminal_reason", "")),
        f"{source_prefix}_margin_gap_accept": margin_gap_accept,
        f"{source_prefix}_accepted_outcome_sensitive": accepted,
    }


def build_outcome_sensitive_row(
    seed: int,
    target_obstacle_distance: float,
    nominal: DecisionSnapshot | None,
    perturbed: DecisionSnapshot | None,
    model: ActorCritic,
    nominal_config: DriftEnvConfig,
    perturbed_config: DriftEnvConfig,
    *,
    max_visible_distance: float,
    max_response_distance: float | None,
    max_context_distance: float | None,
    min_margin_gap: float,
    min_normal_margin: float | None,
    max_normal_margin: float | None,
    require_normal_success: bool,
    max_continuation_steps: int | None,
    visible_dim: int = HUMAN_VIEW_OBS_DIM,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if nominal is None or perturbed is None:
        if nominal is None and perturbed is None:
            pair_status = "missing_both"
        elif nominal is None:
            pair_status = "missing_nominal"
        else:
            pair_status = "missing_perturbed"
        return {
            "seed": int(seed),
            "target_obstacle_distance": float(target_obstacle_distance),
            "pair_status": pair_status,
            "accepted_visible_match": False,
            "accepted_outcome_sensitive": False,
            "accepted_nominal_outcome_sensitive": False,
            "accepted_perturbed_outcome_sensitive": False,
        }, []

    distances = visible_observation_distances(
        nominal.observation,
        perturbed.observation,
        nominal_config,
        visible_dim=visible_dim,
    )
    accepted_visible_total = distances["visible_observation_distance"] <= float(max_visible_distance)
    accepted_response = (
        True
        if max_response_distance is None
        else distances["visible_response_distance"] <= float(max_response_distance)
    )
    accepted_context = (
        True if max_context_distance is None else distances["visible_context_distance"] <= float(max_context_distance)
    )
    accepted_visible = bool(accepted_visible_total and accepted_response and accepted_context)
    pair_row = {
        "accepted_match": accepted_visible,
        "observation_distance": distances["visible_observation_distance"],
        "response_observation_distance": distances["visible_response_distance"],
        "context_observation_distance": distances["visible_context_distance"],
        "hidden_state_distance": hidden_state_distance(nominal.hidden, perturbed.hidden),
    }

    replays: list[dict[str, Any]] = []
    nominal_replays = replay_pair(model, nominal, perturbed, pair_row, nominal_config, max_continuation_steps)
    perturbed_replays = replay_pair(model, perturbed, nominal, pair_row, perturbed_config, max_continuation_steps)
    for replay in [*nominal_replays, *perturbed_replays]:
        replay["target_obstacle_distance"] = float(target_obstacle_distance)
        replay["visible_observation_distance"] = distances["visible_observation_distance"]
        replay["visible_response_distance"] = distances["visible_response_distance"]
        replay["visible_context_distance"] = distances["visible_context_distance"]
        replays.append(replay)

    nominal_metrics = source_outcome_metrics(
        "nominal",
        nominal_replays,
        min_margin_gap=min_margin_gap,
        min_normal_margin=min_normal_margin,
        max_normal_margin=max_normal_margin,
        require_normal_success=require_normal_success,
    )
    perturbed_metrics = source_outcome_metrics(
        "perturbed",
        perturbed_replays,
        min_margin_gap=min_margin_gap,
        min_normal_margin=min_normal_margin,
        max_normal_margin=max_normal_margin,
        require_normal_success=require_normal_success,
    )
    accepted_nominal = bool(nominal_metrics["nominal_accepted_outcome_sensitive"])
    accepted_perturbed = bool(perturbed_metrics["perturbed_accepted_outcome_sensitive"])
    accepted_outcome = bool(accepted_visible and (accepted_nominal or accepted_perturbed))
    max_margin_gap = _finite_max(
        [
            _float(nominal_metrics["nominal_margin_gap"]),
            _float(perturbed_metrics["perturbed_margin_gap"]),
        ]
    )
    success_drop_count = int(bool(nominal_metrics["nominal_success_drop"])) + int(
        bool(perturbed_metrics["perturbed_success_drop"])
    )
    visibility_penalty = distances["visible_observation_distance"] / max(float(max_visible_distance), 1e-9)
    outcome_score = max(0.0, max_margin_gap if np.isfinite(max_margin_gap) else 0.0)
    outcome_score += float(success_drop_count)
    outcome_score -= 0.05 * visibility_penalty

    row = {
        "seed": int(seed),
        "target_obstacle_distance": float(target_obstacle_distance),
        "pair_status": "paired",
        "accepted_visible_match": accepted_visible,
        "accepted_visible_total": bool(accepted_visible_total),
        "accepted_response_match": bool(accepted_response),
        "accepted_context_match": bool(accepted_context),
        "accepted_outcome_sensitive": accepted_outcome,
        "accepted_nominal_outcome_sensitive": accepted_nominal,
        "accepted_perturbed_outcome_sensitive": accepted_perturbed,
        "success_drop_count": success_drop_count,
        "max_margin_gap": max_margin_gap,
        "outcome_score": outcome_score,
        "nominal_step": int(nominal.step),
        "perturbed_step": int(perturbed.step),
        "nominal_obstacle_distance": float(nominal.obstacle_distance),
        "perturbed_obstacle_distance": float(perturbed.obstacle_distance),
        "nominal_mu": _float(nominal.info.get("mu", float("nan"))),
        "perturbed_mu": _float(perturbed.info.get("mu", float("nan"))),
        "nominal_brake_scale": _float(nominal.info.get("brake_scale", float("nan"))),
        "perturbed_brake_scale": _float(perturbed.info.get("brake_scale", float("nan"))),
        "nominal_steer_tau_scale": _float(nominal.info.get("steer_tau_scale", float("nan"))),
        "perturbed_steer_tau_scale": _float(perturbed.info.get("steer_tau_scale", float("nan"))),
        "hidden_state_distance": pair_row["hidden_state_distance"],
        **distances,
        **nominal_metrics,
        **perturbed_metrics,
    }
    return row, replays


def summarize_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            [
                {
                    "candidates": 0,
                    "paired_candidates": 0,
                    "accepted_visible_matches": 0,
                    "accepted_outcome_sensitive_pairs": 0,
                    "accepted_nominal_outcome_sensitive_pairs": 0,
                    "accepted_perturbed_outcome_sensitive_pairs": 0,
                    "visible_match_rate": 0.0,
                    "outcome_sensitive_rate": 0.0,
                    "max_margin_gap": 0.0,
                    "outcome_score_max": 0.0,
                }
            ]
        )
    paired = _series(frame, "pair_status", "").fillna("").astype(str) == "paired"
    visible = _bool_series(frame, "accepted_visible_match")
    accepted = _bool_series(frame, "accepted_outcome_sensitive")
    nominal_accepted = _bool_series(frame, "accepted_nominal_outcome_sensitive")
    perturbed_accepted = _bool_series(frame, "accepted_perturbed_outcome_sensitive")
    success_drop_count = _series(frame, "success_drop_count", 0).fillna(0).astype(float)
    nominal_margin_gap_accept = _bool_series(frame, "nominal_margin_gap_accept")
    perturbed_margin_gap_accept = _bool_series(frame, "perturbed_margin_gap_accept")
    visible_distance = _series(frame, "visible_observation_distance", float("nan")).astype(float)
    max_margin_gap = _series(frame, "max_margin_gap", float("nan")).astype(float)
    outcome_score = _series(frame, "outcome_score", float("nan")).astype(float)
    nominal_probe_steps = _series(frame, "nominal_active_probe_steps", float("nan")).astype(float)
    perturbed_probe_steps = _series(frame, "perturbed_active_probe_steps", float("nan")).astype(float)
    return pd.DataFrame(
        [
            {
                "candidates": int(len(frame)),
                "paired_candidates": int(paired.sum()),
                "accepted_visible_matches": int(visible.sum()),
                "accepted_outcome_sensitive_pairs": int(accepted.sum()),
                "accepted_nominal_outcome_sensitive_pairs": int(nominal_accepted.sum()),
                "accepted_perturbed_outcome_sensitive_pairs": int(perturbed_accepted.sum()),
                "success_drop_pairs": int((success_drop_count > 0).sum()),
                "margin_gap_accept_pairs": int((nominal_margin_gap_accept | perturbed_margin_gap_accept).sum()),
                "visible_match_rate": float(visible.mean()),
                "outcome_sensitive_rate": float(accepted.mean()),
                "visible_observation_distance_mean": float(visible_distance.mean()),
                "max_margin_gap_mean": float(max_margin_gap.mean()),
                "max_margin_gap": float(max_margin_gap.max()),
                "outcome_score_max": float(outcome_score.max()),
                "nominal_active_probe_steps_mean": float(nominal_probe_steps.mean()),
                "perturbed_active_probe_steps_mean": float(perturbed_probe_steps.mean()),
            }
        ]
    )


def outcome_physical_pair_key(row: pd.Series | dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(row["seed"]),
        int(row.get("nominal_bank_step", row.get("nominal_step", -1))),
        int(row.get("perturbed_bank_step", row.get("perturbed_step", -1))),
    )


def select_outcome_sensitive_corpus(
    frame: pd.DataFrame,
    *,
    top_k: int,
    max_rows_per_physical_pair: int = 0,
    max_rows_per_seed: int = 0,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    selected = frame[frame["accepted_outcome_sensitive"].astype(bool)].copy()
    selected = selected.sort_values(["outcome_score", "max_margin_gap", "seed"], ascending=[False, False, True])
    limit = max(0, int(top_k))
    if limit == 0:
        return selected.head(0).copy().reset_index(drop=True)
    if max_rows_per_physical_pair <= 0 and max_rows_per_seed <= 0:
        return selected.head(limit).reset_index(drop=True)

    rows: list[pd.Series] = []
    physical_counts: dict[tuple[int, int, int], int] = {}
    seed_counts: dict[int, int] = {}
    for _, row in selected.iterrows():
        physical_key = outcome_physical_pair_key(row)
        seed = int(row["seed"])
        if (
            max_rows_per_physical_pair > 0
            and physical_counts.get(physical_key, 0) >= int(max_rows_per_physical_pair)
        ):
            continue
        if max_rows_per_seed > 0 and seed_counts.get(seed, 0) >= int(max_rows_per_seed):
            continue
        rows.append(row)
        physical_counts[physical_key] = physical_counts.get(physical_key, 0) + 1
        seed_counts[seed] = seed_counts.get(seed, 0) + 1
        if len(rows) >= limit:
            break
    if not rows:
        return selected.head(0).copy().reset_index(drop=True)
    return pd.DataFrame(rows).reset_index(drop=True)


def run_outcome_sensitive_corpus(
    *,
    model: ActorCritic,
    base_config: DriftEnvConfig,
    seeds: list[int],
    nominal_friction_mu_range: tuple[float, float],
    perturbed_friction_mu_range: tuple[float, float],
    nominal_randomization: dict[str, tuple[float, float]],
    perturbed_randomization: dict[str, tuple[float, float]],
    obstacle_distance_range: tuple[float, float] | None,
    obstacle_half_width_range: tuple[float, float] | None,
    obstacle_perception_reveal_step: int | None,
    obstacle_perception_reveal_distance: float | None,
    target_obstacle_distances: list[float],
    min_probe_steps: int,
    max_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
    max_visible_distance: float,
    max_response_distance: float | None,
    max_context_distance: float | None,
    min_margin_gap: float,
    min_normal_margin: float | None,
    max_normal_margin: float | None,
    require_normal_success: bool,
    max_continuation_steps: int | None,
    top_k: int,
    probe_config: ProbeConfig | None = None,
    snapshot_relocation_distances: list[float] | None = None,
    snapshot_relocation_lateral_offsets: list[float] | None = None,
    snapshot_relocation_half_widths: list[float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_config = obstacle_override_config(
        base_config,
        distance_range=obstacle_distance_range,
        half_width_range=obstacle_half_width_range,
        perception_reveal_step=obstacle_perception_reveal_step,
        perception_reveal_distance=obstacle_perception_reveal_distance,
    )
    configs = {
        "nominal": condition_config(base_config, nominal_friction_mu_range, nominal_randomization),
        "perturbed": condition_config(base_config, perturbed_friction_mu_range, perturbed_randomization),
    }
    rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    active_probe_config = probe_config or ProbeConfig(
        strategy="none",
        steer_amplitude=0.0,
        brake_level=0.0,
        throttle_level=0.0,
        period_steps=20,
        until_step=None,
        until_distance=None,
    )
    relocation_grid = snapshot_relocation_grid(
        snapshot_relocation_distances,
        snapshot_relocation_lateral_offsets,
        snapshot_relocation_half_widths,
    )
    uses_snapshot_relocation = any(distance is not None for distance, _, _ in relocation_grid)
    for seed in seeds:
        for target_distance in target_obstacle_distances:
            snapshots: dict[str, DecisionSnapshot | None] = {}
            errors: dict[str, str] = {}
            for condition, env_config in configs.items():
                try:
                    if active_probe_config.strategy == "none":
                        snapshots[condition] = collect_decision_snapshot(
                            model,
                            env_config,
                            condition,
                            seed,
                            target_obstacle_distance=target_distance,
                            min_probe_steps=min_probe_steps,
                            max_probe_steps=max_probe_steps,
                            require_friction_step=require_friction_step,
                            min_hidden_updates_after_friction=min_hidden_updates_after_friction,
                        )
                    else:
                        snapshots[condition] = collect_probing_decision_snapshot(
                            model,
                            env_config,
                            condition,
                            seed,
                            target_obstacle_distance=target_distance,
                            min_probe_steps=min_probe_steps,
                            max_probe_steps=max_probe_steps,
                            require_friction_step=require_friction_step,
                            min_hidden_updates_after_friction=min_hidden_updates_after_friction,
                            probe_config=active_probe_config,
                        )
                except RuntimeError as exc:
                    snapshots[condition] = None
                    errors[condition] = str(exc)
            for relocation_distance, relocation_lateral, relocation_half_width in relocation_grid:
                candidate_snapshots = snapshots
                row_errors = dict(errors)
                if relocation_distance is not None:
                    candidate_snapshots = {"nominal": None, "perturbed": None}
                    for condition in ["nominal", "perturbed"]:
                        snapshot = snapshots[condition]
                        if snapshot is None:
                            continue
                        try:
                            candidate_snapshots[condition] = relocate_obstacle_snapshot(
                                snapshot,
                                body_longitudinal=relocation_distance,
                                body_lateral=relocation_lateral,
                                half_width=relocation_half_width,
                            )
                        except ValueError as exc:
                            row_errors[condition] = str(exc)
                row_target_distance = (
                    float(target_distance) if relocation_distance is None else float(relocation_distance)
                )
                row, replays = build_outcome_sensitive_row(
                    seed,
                    row_target_distance,
                    candidate_snapshots["nominal"],
                    candidate_snapshots["perturbed"],
                    model,
                    configs["nominal"],
                    configs["perturbed"],
                    max_visible_distance=max_visible_distance,
                    max_response_distance=max_response_distance,
                    max_context_distance=max_context_distance,
                    min_margin_gap=min_margin_gap,
                    min_normal_margin=min_normal_margin,
                    max_normal_margin=max_normal_margin,
                    require_normal_success=require_normal_success,
                    max_continuation_steps=max_continuation_steps,
                )
                row["source_target_obstacle_distance"] = float(target_distance)
                row["snapshot_relocated"] = uses_snapshot_relocation
                row["relocated_obstacle_body_x"] = (
                    float("nan") if relocation_distance is None else float(relocation_distance)
                )
                row["relocated_obstacle_body_y"] = float(relocation_lateral)
                row["relocated_obstacle_half_width"] = (
                    float("nan") if relocation_half_width is None else float(relocation_half_width)
                )
                row["active_probe_strategy"] = active_probe_config.strategy
                if candidate_snapshots["nominal"] is not None:
                    row["nominal_active_probe_steps"] = int(
                        candidate_snapshots["nominal"].info.get("active_probe_steps", 0)
                    )
                    row["nominal_active_probe_steer_abs_mean"] = _float(
                        candidate_snapshots["nominal"].info.get("active_probe_steer_abs_mean", float("nan"))
                    )
                    row["nominal_active_probe_brake_mean"] = _float(
                        candidate_snapshots["nominal"].info.get("active_probe_brake_mean", float("nan"))
                    )
                if candidate_snapshots["perturbed"] is not None:
                    row["perturbed_active_probe_steps"] = int(
                        candidate_snapshots["perturbed"].info.get("active_probe_steps", 0)
                    )
                    row["perturbed_active_probe_steer_abs_mean"] = _float(
                        candidate_snapshots["perturbed"].info.get("active_probe_steer_abs_mean", float("nan"))
                    )
                    row["perturbed_active_probe_brake_mean"] = _float(
                        candidate_snapshots["perturbed"].info.get("active_probe_brake_mean", float("nan"))
                    )
                row["nominal_error"] = row_errors.get("nominal", "")
                row["perturbed_error"] = row_errors.get("perturbed", "")
                rows.append(row)
                replay_rows.extend(replays)

    candidates = pd.DataFrame(rows)
    replays = pd.DataFrame(replay_rows)
    corpus = select_outcome_sensitive_corpus(candidates, top_k=top_k)
    summary = summarize_outcomes(candidates)
    return candidates, replays, corpus, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine outcome-sensitive wrong-history hidden-dynamics pairs.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=80)
    parser.add_argument("--seed", type=int, default=7100)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--nominal-friction-mu-range", type=parse_range, default=(0.85, 1.15))
    parser.add_argument("--perturbed-friction-mu-range", type=parse_range, default=(0.25, 0.35))
    parser.add_argument("--nominal-randomization", action="append", default=[])
    parser.add_argument("--perturbed-randomization", action="append", default=[])
    parser.add_argument("--obstacle-distance-range", type=parse_range, default=None)
    parser.add_argument("--obstacle-half-width-range", type=parse_range, default=None)
    parser.add_argument("--obstacle-perception-reveal-step", type=int, default=None)
    parser.add_argument("--obstacle-perception-reveal-distance", type=float, default=None)
    parser.add_argument("--target-obstacle-distances", type=parse_float_list, default=[8.0, 10.0, 12.0])
    parser.add_argument("--min-probe-steps", type=int, default=10)
    parser.add_argument("--max-probe-steps", type=int, default=180)
    parser.add_argument("--allow-pre-friction-snapshot", action="store_true")
    parser.add_argument("--min-hidden-updates-after-friction", type=int, default=2)
    parser.add_argument("--max-visible-distance", type=float, default=0.75)
    parser.add_argument("--max-response-distance", type=float, default=0.25)
    parser.add_argument("--max-context-distance", type=float, default=0.05)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--min-normal-margin", type=float, default=0.0)
    parser.add_argument("--max-normal-margin", type=float, default=None)
    parser.add_argument("--allow-normal-failure", action="store_true")
    parser.add_argument("--max-continuation-steps", type=int, default=0)
    parser.add_argument("--probe-strategy", choices=PROBE_STRATEGIES, default="none")
    parser.add_argument("--probe-steer-amplitude", type=float, default=0.12)
    parser.add_argument("--probe-brake-level", type=float, default=0.12)
    parser.add_argument("--probe-throttle-level", type=float, default=0.0)
    parser.add_argument("--probe-period-steps", type=int, default=20)
    parser.add_argument("--probe-until-step", type=int, default=None)
    parser.add_argument("--probe-until-distance", type=float, default=None)
    parser.add_argument("--snapshot-relocation-distances", type=parse_float_list, default=None)
    parser.add_argument("--snapshot-relocation-lateral-offsets", type=parse_float_values, default=None)
    parser.add_argument("--snapshot-relocation-half-widths", type=parse_float_list, default=None)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="outcome_sensitive_corpus", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_env_config(args.env_config)
    target_obs_dim = int(AutoDriftEnv(base_config).observation_space.shape[0])
    model, _ = load_actor_critic_checkpoint(args.checkpoint, device=args.device, obs_dim=target_obs_dim)
    if not model.is_online_recurrent:
        raise ValueError("outcome-sensitive corpus mining requires an online recurrent checkpoint")
    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else [args.seed + index for index in range(args.episodes)]
    nominal_randomization = parse_randomization_overrides(args.nominal_randomization)
    perturbed_randomization = parse_randomization_overrides(args.perturbed_randomization)
    probe_config = ProbeConfig(
        strategy=args.probe_strategy,
        steer_amplitude=args.probe_steer_amplitude,
        brake_level=args.probe_brake_level,
        throttle_level=args.probe_throttle_level,
        period_steps=args.probe_period_steps,
        until_step=args.probe_until_step,
        until_distance=args.probe_until_distance,
    )
    candidates, replays, corpus, summary = run_outcome_sensitive_corpus(
        model=model,
        base_config=base_config,
        seeds=seeds,
        nominal_friction_mu_range=args.nominal_friction_mu_range,
        perturbed_friction_mu_range=args.perturbed_friction_mu_range,
        nominal_randomization=nominal_randomization,
        perturbed_randomization=perturbed_randomization,
        obstacle_distance_range=args.obstacle_distance_range,
        obstacle_half_width_range=args.obstacle_half_width_range,
        obstacle_perception_reveal_step=args.obstacle_perception_reveal_step,
        obstacle_perception_reveal_distance=args.obstacle_perception_reveal_distance,
        target_obstacle_distances=args.target_obstacle_distances,
        min_probe_steps=args.min_probe_steps,
        max_probe_steps=args.max_probe_steps,
        require_friction_step=not args.allow_pre_friction_snapshot,
        min_hidden_updates_after_friction=args.min_hidden_updates_after_friction,
        max_visible_distance=args.max_visible_distance,
        max_response_distance=args.max_response_distance,
        max_context_distance=args.max_context_distance,
        min_margin_gap=args.min_margin_gap,
        min_normal_margin=args.min_normal_margin,
        max_normal_margin=args.max_normal_margin,
        require_normal_success=not args.allow_normal_failure,
        max_continuation_steps=args.max_continuation_steps,
        top_k=args.top_k,
        probe_config=probe_config,
        snapshot_relocation_distances=args.snapshot_relocation_distances,
        snapshot_relocation_lateral_offsets=args.snapshot_relocation_lateral_offsets,
        snapshot_relocation_half_widths=args.snapshot_relocation_half_widths,
    )

    candidates_csv = run_dir / "outcome_candidates.csv"
    replays_csv = run_dir / "replays.csv"
    corpus_csv = run_dir / "outcome_sensitive_snippets.csv"
    summary_csv = run_dir / "summary.csv"
    candidates.to_csv(candidates_csv, index=False)
    replays.to_csv(replays_csv, index=False)
    corpus.to_csv(corpus_csv, index=False)
    summary.to_csv(summary_csv, index=False)
    write_json(run_dir / "summary.json", summary.iloc[0].to_dict() if len(summary) else {})
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "outcome_sensitive_corpus",
            "env_config": args.env_config,
            "checkpoint": args.checkpoint,
            "episodes": len(seeds),
            "seed": args.seed,
            "seed_csv": args.seed_csv,
            "device": args.device,
            "nominal_friction_mu_range": args.nominal_friction_mu_range,
            "perturbed_friction_mu_range": args.perturbed_friction_mu_range,
            "nominal_randomization": nominal_randomization,
            "perturbed_randomization": perturbed_randomization,
            "obstacle_distance_range": args.obstacle_distance_range,
            "obstacle_half_width_range": args.obstacle_half_width_range,
            "obstacle_perception_reveal_step": args.obstacle_perception_reveal_step,
            "obstacle_perception_reveal_distance": args.obstacle_perception_reveal_distance,
            "target_obstacle_distances": args.target_obstacle_distances,
            "min_probe_steps": args.min_probe_steps,
            "max_probe_steps": args.max_probe_steps,
            "require_friction_step": not args.allow_pre_friction_snapshot,
            "min_hidden_updates_after_friction": args.min_hidden_updates_after_friction,
            "max_visible_distance": args.max_visible_distance,
            "max_response_distance": args.max_response_distance,
            "max_context_distance": args.max_context_distance,
            "min_margin_gap": args.min_margin_gap,
            "min_normal_margin": args.min_normal_margin,
            "max_normal_margin": args.max_normal_margin,
            "require_normal_success": not args.allow_normal_failure,
            "max_continuation_steps": args.max_continuation_steps,
            "probe": {
                "strategy": probe_config.strategy,
                "steer_amplitude": probe_config.steer_amplitude,
                "brake_level": probe_config.brake_level,
                "throttle_level": probe_config.throttle_level,
                "period_steps": probe_config.period_steps,
                "until_step": probe_config.until_step,
                "until_distance": probe_config.until_distance,
            },
            "snapshot_relocation": {
                "distances": args.snapshot_relocation_distances,
                "lateral_offsets": args.snapshot_relocation_lateral_offsets,
                "half_widths": args.snapshot_relocation_half_widths,
            },
            "top_k": args.top_k,
            "artifacts": {
                "outcome_candidates_csv": candidates_csv,
                "replays_csv": replays_csv,
                "outcome_sensitive_snippets_csv": corpus_csv,
                "summary_csv": summary_csv,
            },
        },
    )
    print(summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
