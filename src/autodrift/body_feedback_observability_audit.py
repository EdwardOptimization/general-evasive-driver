"""M146 body-feedback observability audit.

This probe separates passenger-like current slip detection from driver-like
future envelope prediction before any PPO input profile is promoted.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import load_env_config
from autodrift.input_observability_audit import (
    HISTORY_MODES,
    TARGETS,
    RegressionProbeResult,
    build_history_window_features,
    future_envelope_targets,
    parse_history_windows,
    regression_probe_results_to_rows,
    split_by_episode,
    train_ridge_regression_probe,
)
from autodrift.policies import make_policy
from autodrift.train_ppo import WHEEL_HUMAN_VIEW_OBS_DIM, WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM


PASSENGER_BODY_RESPONSE = "passenger_body_response"
PASSENGER_BODY_SCENE = "passenger_body_scene"
H1_BODY_ONLY = "h1_body_only"
P0_CURRENT_BASELINE = "p0_current_baseline"
BODY_FEEDBACK_PROFILE_ORDER = (
    PASSENGER_BODY_RESPONSE,
    PASSENGER_BODY_SCENE,
    H1_BODY_ONLY,
    P0_CURRENT_BASELINE,
)


@dataclass(frozen=True)
class BodyFeedbackProfileSpec:
    name: str
    description: str
    per_frame_indices: tuple[int, ...]
    role: str


@dataclass(frozen=True)
class BinaryProbeResult:
    target: str
    feature_set: str
    train_samples: int
    test_samples: int
    positive_rate_train: float
    positive_rate_test: float
    train_accuracy: float
    test_accuracy: float
    train_balanced_accuracy: float
    test_balanced_accuracy: float
    test_auc: float
    status: str = "ok"
    history_window_steps: int = 1
    history_mode: str = "raw"


def body_feedback_profile_specs() -> tuple[BodyFeedbackProfileSpec, ...]:
    context_indices = tuple(range(WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM, WHEEL_HUMAN_VIEW_OBS_DIM))
    passenger_body = (2, 3, 4)  # yaw_rate, ax, ay
    h1_body_only = (
        2,  # yaw_rate
        3,  # ax
        4,  # ay
        5,  # steering actuator state
        7,  # throttle actuator state
        8,  # brake actuator state
        9,  # previous steering command
        10,  # previous physical throttle command
        11,  # previous physical brake command
    )
    current_p0 = tuple(range(0, 12))
    return (
        BodyFeedbackProfileSpec(
            name=PASSENGER_BODY_RESPONSE,
            description="passenger-style continuous yaw/IMU body response only",
            per_frame_indices=passenger_body,
            role="post_slip_detection_baseline",
        ),
        BodyFeedbackProfileSpec(
            name=PASSENGER_BODY_SCENE,
            description="passenger body response plus road/obstacle geometry history",
            per_frame_indices=passenger_body + context_indices,
            role="visual_body_detection_baseline",
        ),
        BodyFeedbackProfileSpec(
            name=H1_BODY_ONLY,
            description="driver-like H1: commands, actuator actuals, yaw/IMU body response, and scene",
            per_frame_indices=h1_body_only + context_indices,
            role="driver_like_body_feedback",
        ),
        BodyFeedbackProfileSpec(
            name=P0_CURRENT_BASELINE,
            description="current human-view no-wheel baseline: H1 plus deployable vx/vy and steer-rate proxy",
            per_frame_indices=current_p0 + context_indices,
            role="current_actor_contract_reference",
        ),
    )


def body_feedback_profile_spec_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in body_feedback_profile_specs():
        rows.append(
            {
                "profile": spec.name,
                "feature_count_per_frame": len(spec.per_frame_indices),
                "indices": " ".join(str(index) for index in spec.per_frame_indices),
                "description": spec.description,
                "role": spec.role,
            }
        )
    return rows


def body_feedback_spec_by_name() -> dict[str, BodyFeedbackProfileSpec]:
    return {spec.name: spec for spec in body_feedback_profile_specs()}


def body_feedback_history_sequence(frames: np.ndarray, profile: str) -> np.ndarray:
    frames = np.asarray(frames, dtype=np.float32)
    if frames.ndim != 3 or frames.shape[2] != WHEEL_HUMAN_VIEW_OBS_DIM:
        raise ValueError(
            "body-feedback history sequences require frames with shape "
            f"(samples, steps, {WHEEL_HUMAN_VIEW_OBS_DIM})"
        )
    specs = body_feedback_spec_by_name()
    if profile not in specs:
        raise ValueError("unknown body-feedback profile: " + profile)
    return frames[:, :, list(specs[profile].per_frame_indices)].astype(np.float32)


def build_body_feedback_feature_profiles(observations: np.ndarray) -> dict[str, np.ndarray]:
    observations = np.asarray(observations, dtype=np.float32)
    if observations.ndim != 2:
        raise ValueError("observations must be a 2D array")
    if observations.shape[1] % WHEEL_HUMAN_VIEW_OBS_DIM != 0:
        raise ValueError(
            "body-feedback audit requires one or more concatenated "
            f"{WHEEL_HUMAN_VIEW_OBS_DIM}-value wheel-response frames"
        )
    frame_count = observations.shape[1] // WHEEL_HUMAN_VIEW_OBS_DIM
    frames = observations.reshape(observations.shape[0], frame_count, WHEEL_HUMAN_VIEW_OBS_DIM)
    return {
        spec.name: body_feedback_history_sequence(frames, spec.name)
        .reshape(observations.shape[0], -1)
        .astype(np.float32)
        for spec in body_feedback_profile_specs()
    }


def collect_body_feedback_dataset(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    history_windows: tuple[int, ...] = (1,),
    history_mode: str = "raw",
    post_slip_beta_threshold: float | None = None,
) -> tuple[dict[int, np.ndarray], dict[str, np.ndarray], np.ndarray, list[dict[str, Any]]]:
    env_config = load_env_config(env_config_path)
    if env_config.history_length != 1:
        raise ValueError("body-feedback audit history windows require env history_length=1")
    if env_config.obstacle_relative_velocity_mode != "zero":
        raise ValueError("body-feedback audit requires obstacle_relative_velocity_mode='zero'")
    if not history_windows:
        raise ValueError("at least one history window is required")
    if history_mode not in HISTORY_MODES:
        raise ValueError("history_mode must be one of: " + ", ".join(HISTORY_MODES))
    history_windows = tuple(sorted({int(window) for window in history_windows}))
    if any(window < 1 for window in history_windows):
        raise ValueError("history windows must be positive step counts")

    env = AutoDriftEnv(env_config)
    slip_threshold = (
        float(post_slip_beta_threshold)
        if post_slip_beta_threshold is not None
        else float(env_config.obstacle.stable_aes_beta_limit)
    )
    policy = make_policy(policy_name, env, seed=seed)
    observations_by_window: dict[int, list[np.ndarray]] = {window: [] for window in history_windows}
    targets: dict[str, list[float]] = {name: [] for name in TARGETS}
    post_slip_labels: list[bool] = []
    rows: list[dict[str, Any]] = []

    for episode in range(episodes):
        episode_seed = seed + episode
        obs, info = env.reset(seed=episode_seed)
        episode_observations: list[np.ndarray] = []
        policy.reset()
        terminated = False
        truncated = False
        while not (terminated or truncated):
            episode_observations.append(obs.astype(np.float32))
            if int(info["step"]) % sample_stride == 0:
                target_values = future_envelope_targets(env, horizon_steps=horizon_steps)
                beta = float(info["beta"])
                yaw_rate = float(env.state.yaw_rate)
                post_slip = abs(beta) >= slip_threshold
                for window in history_windows:
                    frames: list[np.ndarray] = []
                    for offset in range(window - 1, -1, -1):
                        index = max(0, len(episode_observations) - 1 - offset)
                        frames.append(episode_observations[index])
                    observations_by_window[window].append(
                        build_history_window_features(np.asarray(frames, dtype=np.float32), history_mode)
                    )
                for name in TARGETS:
                    targets[name].append(float(target_values[name]))
                post_slip_labels.append(post_slip)
                rows.append(
                    {
                        "episode": episode,
                        "seed": episode_seed,
                        "step": int(info["step"]),
                        "policy": policy_name,
                        "sample_phase": "post_slip" if post_slip else "pre_limit_nonpost",
                        "post_slip": bool(post_slip),
                        "beta": beta,
                        "abs_beta": abs(beta),
                        "post_slip_beta_threshold": slip_threshold,
                        "yaw_rate": yaw_rate,
                        "abs_yaw_rate": abs(yaw_rate),
                        "obstacle_label": str(info.get("obstacle_label", "")),
                        **target_values,
                    }
                )
                if max_samples is not None and len(rows) >= max_samples:
                    return (
                        {
                            window: np.asarray(values, dtype=np.float32)
                            for window, values in observations_by_window.items()
                        },
                        {name: np.asarray(values, dtype=np.float32) for name, values in targets.items()},
                        np.asarray(post_slip_labels, dtype=bool),
                        rows,
                    )
            action = policy.act(obs, info)
            obs, _, terminated, truncated, info = env.step(action)

    return (
        {
            window: np.asarray(values, dtype=np.float32)
            for window, values in observations_by_window.items()
        },
        {name: np.asarray(values, dtype=np.float32) for name, values in targets.items()},
        np.asarray(post_slip_labels, dtype=bool),
        rows,
    )


def _r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = float(np.sum(np.square(y_true - np.mean(y_true))))
    if denom <= 1e-12:
        return float("nan")
    return float(1.0 - float(np.sum(np.square(y_true - y_pred))) / denom)


def _balanced_accuracy(labels: np.ndarray, pred_labels: np.ndarray) -> float:
    labels = labels.astype(bool)
    pred_labels = pred_labels.astype(bool)
    positives = labels
    negatives = ~labels
    if positives.sum() == 0 or negatives.sum() == 0:
        return float("nan")
    tpr = float(np.mean(pred_labels[positives]))
    tnr = float(np.mean(~pred_labels[negatives]))
    return 0.5 * (tpr + tnr)


def _auc_score(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = labels.astype(bool)
    positives = int(labels.sum())
    negatives = int((~labels).sum())
    if positives == 0 or negatives == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=np.float64)
    pos_rank_sum = float(np.sum(ranks[labels]))
    return float((pos_rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives))


def train_ridge_binary_probe(
    features: np.ndarray,
    labels: np.ndarray,
    train_mask: np.ndarray,
    target_name: str,
    feature_set: str,
    ridge: float = 0.1,
    history_window_steps: int = 1,
    history_mode: str = "raw",
) -> BinaryProbeResult:
    train_x = features[train_mask].astype(np.float64)
    test_x = features[~train_mask].astype(np.float64)
    train_y = labels[train_mask].astype(np.float64)
    test_y = labels[~train_mask].astype(np.float64)
    if len(train_y) < 2 or len(test_y) == 0 or len(np.unique(train_y)) < 2:
        return BinaryProbeResult(
            target=target_name,
            feature_set=feature_set,
            train_samples=int(len(train_y)),
            test_samples=int(len(test_y)),
            positive_rate_train=float(np.mean(train_y)) if len(train_y) else float("nan"),
            positive_rate_test=float(np.mean(test_y)) if len(test_y) else float("nan"),
            train_accuracy=float("nan"),
            test_accuracy=float("nan"),
            train_balanced_accuracy=float("nan"),
            test_balanced_accuracy=float("nan"),
            test_auc=float("nan"),
            status="skipped_insufficient_class_balance",
            history_window_steps=history_window_steps,
            history_mode=history_mode,
        )

    mean = train_x.mean(axis=0, keepdims=True)
    std = train_x.std(axis=0, keepdims=True) + 1e-6
    train_x = (train_x - mean) / std
    test_x = (test_x - mean) / std
    train_design = np.concatenate([train_x, np.ones((train_x.shape[0], 1), dtype=np.float64)], axis=1)
    test_design = np.concatenate([test_x, np.ones((test_x.shape[0], 1), dtype=np.float64)], axis=1)
    gram = train_design.T @ train_design
    penalty = ridge * np.eye(gram.shape[0], dtype=np.float64)
    penalty[-1, -1] = 0.0
    weights = np.linalg.solve(gram + penalty, train_design.T @ train_y)
    train_scores = train_design @ weights
    test_scores = test_design @ weights
    train_pred = train_scores >= 0.5
    test_pred = test_scores >= 0.5
    return BinaryProbeResult(
        target=target_name,
        feature_set=feature_set,
        train_samples=int(len(train_y)),
        test_samples=int(len(test_y)),
        positive_rate_train=float(np.mean(train_y)),
        positive_rate_test=float(np.mean(test_y)),
        train_accuracy=float(np.mean(train_pred == train_y.astype(bool))),
        test_accuracy=float(np.mean(test_pred == test_y.astype(bool))),
        train_balanced_accuracy=_balanced_accuracy(train_y.astype(bool), train_pred),
        test_balanced_accuracy=_balanced_accuracy(test_y.astype(bool), test_pred),
        test_auc=_auc_score(test_y.astype(bool), test_scores),
        history_window_steps=history_window_steps,
        history_mode=history_mode,
    )


def binary_probe_results_to_rows(results: list[BinaryProbeResult]) -> list[dict[str, Any]]:
    return [result.__dict__ for result in results]


def summarize_slip_detection_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int, str], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["target"]), int(row["history_window_steps"]), str(row["history_mode"]))
        by_key.setdefault(key, {})[str(row["feature_set"])] = row

    def delta(profiles: dict[str, dict[str, Any]], left: str, right: str, metric: str) -> float:
        if left not in profiles or right not in profiles:
            return float("nan")
        return float(profiles[left][metric]) - float(profiles[right][metric])

    delta_rows: list[dict[str, Any]] = []
    for (target, history_window_steps, history_mode), profiles in sorted(by_key.items()):
        status_ok = all(
            profile in profiles and str(profiles[profile].get("status", "ok")) == "ok"
            for profile in BODY_FEEDBACK_PROFILE_ORDER
        )
        delta_rows.append(
            {
                "target": target,
                "history_window_steps": history_window_steps,
                "history_mode": history_mode,
                "passenger_scene_minus_body_auc": delta(
                    profiles, PASSENGER_BODY_SCENE, PASSENGER_BODY_RESPONSE, "test_auc"
                ),
                "passenger_scene_minus_body_balanced_accuracy": delta(
                    profiles, PASSENGER_BODY_SCENE, PASSENGER_BODY_RESPONSE, "test_balanced_accuracy"
                ),
                "h1_minus_passenger_scene_auc": delta(profiles, H1_BODY_ONLY, PASSENGER_BODY_SCENE, "test_auc"),
                "h1_minus_passenger_scene_balanced_accuracy": delta(
                    profiles, H1_BODY_ONLY, PASSENGER_BODY_SCENE, "test_balanced_accuracy"
                ),
                "p0_minus_h1_auc": delta(profiles, P0_CURRENT_BASELINE, H1_BODY_ONLY, "test_auc"),
                "p0_minus_h1_balanced_accuracy": delta(
                    profiles, P0_CURRENT_BASELINE, H1_BODY_ONLY, "test_balanced_accuracy"
                ),
                "status": "ok" if status_ok else "skipped",
            }
        )
    return delta_rows


def summarize_pre_limit_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int, str], dict[str, dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["target"]), int(row["history_window_steps"]), str(row["history_mode"]))
        by_key.setdefault(key, {})[str(row["feature_set"])] = row

    def delta(profiles: dict[str, dict[str, Any]], left: str, right: str, metric: str) -> float:
        if left not in profiles or right not in profiles:
            return float("nan")
        return float(profiles[left][metric]) - float(profiles[right][metric])

    delta_rows: list[dict[str, Any]] = []
    for (target, history_window_steps, history_mode), profiles in sorted(by_key.items()):
        status_ok = all(
            profile in profiles and str(profiles[profile].get("status", "ok")) == "ok"
            for profile in BODY_FEEDBACK_PROFILE_ORDER
        )
        delta_rows.append(
            {
                "target": target,
                "history_window_steps": history_window_steps,
                "history_mode": history_mode,
                "passenger_scene_minus_body_test_r2": delta(
                    profiles, PASSENGER_BODY_SCENE, PASSENGER_BODY_RESPONSE, "test_r2"
                ),
                "passenger_scene_minus_body_mae_improvement": delta(
                    profiles, PASSENGER_BODY_SCENE, PASSENGER_BODY_RESPONSE, "mae_improvement"
                ),
                "h1_minus_passenger_scene_test_r2": delta(
                    profiles, H1_BODY_ONLY, PASSENGER_BODY_SCENE, "test_r2"
                ),
                "h1_minus_passenger_scene_mae_improvement": delta(
                    profiles, H1_BODY_ONLY, PASSENGER_BODY_SCENE, "mae_improvement"
                ),
                "p0_minus_h1_test_r2": delta(profiles, P0_CURRENT_BASELINE, H1_BODY_ONLY, "test_r2"),
                "p0_minus_h1_mae_improvement": delta(
                    profiles, P0_CURRENT_BASELINE, H1_BODY_ONLY, "mae_improvement"
                ),
                "status": "ok" if status_ok else "skipped",
            }
        )
    return delta_rows


def _mean_metric(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([float(row[metric]) for row in rows if row.get("status") == "ok"], dtype=np.float64)
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if len(finite) else float("nan")


def aggregate_body_feedback_deltas(
    slip_delta_rows: list[dict[str, Any]],
    pre_limit_delta_rows: list[dict[str, Any]],
) -> dict[str, float]:
    aggregate: dict[str, float] = {}
    for metric in (
        "passenger_scene_minus_body_auc",
        "passenger_scene_minus_body_balanced_accuracy",
        "h1_minus_passenger_scene_auc",
        "h1_minus_passenger_scene_balanced_accuracy",
        "p0_minus_h1_auc",
        "p0_minus_h1_balanced_accuracy",
    ):
        aggregate[f"mean_slip_{metric}"] = _mean_metric(slip_delta_rows, metric)
    for metric in (
        "passenger_scene_minus_body_test_r2",
        "passenger_scene_minus_body_mae_improvement",
        "h1_minus_passenger_scene_test_r2",
        "h1_minus_passenger_scene_mae_improvement",
        "p0_minus_h1_test_r2",
        "p0_minus_h1_mae_improvement",
    ):
        aggregate[f"mean_pre_limit_{metric}"] = _mean_metric(pre_limit_delta_rows, metric)
    return aggregate


def sample_phase_summary(sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    phases: dict[str, int] = {}
    labels: dict[str, int] = {}
    for row in sample_rows:
        phase = str(row["sample_phase"])
        label = str(row.get("obstacle_label", ""))
        phases[phase] = phases.get(phase, 0) + 1
        labels[label] = labels.get(label, 0) + 1
    return {
        "samples": len(sample_rows),
        "phase_counts": phases,
        "obstacle_label_counts": labels,
    }


def find_ambiguous_body_history_pairs(
    features: np.ndarray,
    targets: np.ndarray,
    sample_rows: list[dict[str, Any]],
    seed: int,
    max_search_samples: int = 450,
    feature_quantile: float = 0.05,
    target_quantile: float = 0.90,
    max_pairs: int = 50,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(sample_rows) != features.shape[0] or targets.shape[0] != features.shape[0]:
        raise ValueError("features, targets, and sample_rows must have matching sample counts")
    if features.shape[0] < 2:
        return [], {"searched_samples": int(features.shape[0]), "pairs_found": 0}

    rng = np.random.default_rng(seed)
    if features.shape[0] > max_search_samples:
        selected = np.sort(rng.choice(features.shape[0], size=max_search_samples, replace=False))
    else:
        selected = np.arange(features.shape[0])

    x = features[selected].astype(np.float64)
    y = targets[selected].astype(np.float64)
    x = (x - x.mean(axis=0, keepdims=True)) / (x.std(axis=0, keepdims=True) + 1e-6)
    y = (y - y.mean(axis=0, keepdims=True)) / (y.std(axis=0, keepdims=True) + 1e-6)
    x_sq = np.sum(np.square(x), axis=1, keepdims=True)
    y_sq = np.sum(np.square(y), axis=1, keepdims=True)
    feature_dist = np.sqrt(np.maximum(x_sq + x_sq.T - 2.0 * (x @ x.T), 0.0) / max(x.shape[1], 1))
    target_dist = np.sqrt(np.maximum(y_sq + y_sq.T - 2.0 * (y @ y.T), 0.0) / max(y.shape[1], 1))
    episodes = np.asarray([int(sample_rows[int(index)]["episode"]) for index in selected], dtype=np.int64)
    valid = np.triu(np.ones_like(feature_dist, dtype=bool), k=1)
    valid &= episodes[:, None] != episodes[None, :]
    if not np.any(valid):
        return [], {"searched_samples": int(len(selected)), "pairs_found": 0}

    feature_threshold = float(np.quantile(feature_dist[valid], feature_quantile))
    target_threshold = float(np.quantile(target_dist[valid], target_quantile))
    candidate = valid & (feature_dist <= feature_threshold) & (target_dist >= target_threshold)
    candidate_indices = np.argwhere(candidate)
    if len(candidate_indices) == 0:
        return [], {
            "searched_samples": int(len(selected)),
            "pairs_found": 0,
            "feature_distance_threshold": feature_threshold,
            "target_distance_threshold": target_threshold,
        }

    scores = target_dist[candidate] / (feature_dist[candidate] + 1e-6)
    order = np.argsort(-scores)
    pair_rows: list[dict[str, Any]] = []
    for rank, candidate_index in enumerate(order[:max_pairs], start=1):
        local_i, local_j = candidate_indices[int(candidate_index)]
        global_i = int(selected[int(local_i)])
        global_j = int(selected[int(local_j)])
        row_i = sample_rows[global_i]
        row_j = sample_rows[global_j]
        pair_rows.append(
            {
                "rank": rank,
                "sample_i": global_i,
                "sample_j": global_j,
                "seed_i": int(row_i["seed"]),
                "seed_j": int(row_j["seed"]),
                "episode_i": int(row_i["episode"]),
                "episode_j": int(row_j["episode"]),
                "step_i": int(row_i["step"]),
                "step_j": int(row_j["step"]),
                "phase_i": str(row_i["sample_phase"]),
                "phase_j": str(row_j["sample_phase"]),
                "phase_mismatch": str(row_i["sample_phase"]) != str(row_j["sample_phase"]),
                "feature_distance": float(feature_dist[local_i, local_j]),
                "target_distance": float(target_dist[local_i, local_j]),
                "future_braking_i": float(row_i["future_braking_deceleration"]),
                "future_braking_j": float(row_j["future_braking_deceleration"]),
                "future_yaw_i": float(row_i["future_yaw_response"]),
                "future_yaw_j": float(row_j["future_yaw_response"]),
                "future_lateral_i": float(row_i["future_lateral_accel_response"]),
                "future_lateral_j": float(row_j["future_lateral_accel_response"]),
            }
        )

    return pair_rows, {
        "searched_samples": int(len(selected)),
        "pairs_found": int(len(candidate_indices)),
        "pairs_exported": int(len(pair_rows)),
        "feature_distance_threshold": feature_threshold,
        "target_distance_threshold": target_threshold,
        "feature_quantile": feature_quantile,
        "target_quantile": target_quantile,
        "profile": H1_BODY_ONLY,
    }


def run_body_feedback_observability_audit(
    env_config_path: Path,
    episodes: int,
    seed: int,
    policy_name: str,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    train_fraction: float,
    ridge: float,
    history_windows: tuple[int, ...],
    history_mode: str,
    post_slip_beta_threshold: float | None = None,
    max_ambiguous_search_samples: int = 450,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, float],
    list[dict[str, Any]],
    dict[str, Any],
]:
    observations_by_window, targets, post_slip_labels, sample_rows = collect_body_feedback_dataset(
        env_config_path=env_config_path,
        episodes=episodes,
        seed=seed,
        policy_name=policy_name,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        history_windows=history_windows,
        history_mode=history_mode,
        post_slip_beta_threshold=post_slip_beta_threshold,
    )
    if len(sample_rows) == 0:
        raise ValueError("body-feedback observability dataset is empty")
    train_mask = split_by_episode(sample_rows, train_fraction=train_fraction, seed=seed + 31)
    pre_limit_mask = ~post_slip_labels
    slip_results: list[BinaryProbeResult] = []
    pre_limit_results: list[RegressionProbeResult] = []
    for history_window_steps, observations in observations_by_window.items():
        feature_profiles = build_body_feedback_feature_profiles(observations)
        for profile_name in BODY_FEEDBACK_PROFILE_ORDER:
            slip_results.append(
                train_ridge_binary_probe(
                    features=feature_profiles[profile_name],
                    labels=post_slip_labels,
                    train_mask=train_mask,
                    target_name="post_slip",
                    feature_set=profile_name,
                    ridge=ridge,
                    history_window_steps=history_window_steps,
                    history_mode=history_mode,
                )
            )
            for target_name, target_values in targets.items():
                pre_limit_results.append(
                    train_ridge_regression_probe(
                        features=feature_profiles[profile_name][pre_limit_mask],
                        targets=target_values[pre_limit_mask],
                        train_mask=train_mask[pre_limit_mask],
                        target_name=target_name,
                        feature_set=profile_name,
                        ridge=ridge,
                        history_window_steps=history_window_steps,
                        history_mode=history_mode,
                    )
                )

    slip_rows = binary_probe_results_to_rows(slip_results)
    pre_limit_rows = regression_probe_results_to_rows(pre_limit_results)
    slip_delta_rows = summarize_slip_detection_deltas(slip_rows)
    pre_limit_delta_rows = summarize_pre_limit_deltas(pre_limit_rows)
    aggregate = aggregate_body_feedback_deltas(slip_delta_rows, pre_limit_delta_rows)

    ambiguity_window = max(observations_by_window)
    ambiguity_profiles = build_body_feedback_feature_profiles(observations_by_window[ambiguity_window])
    target_matrix = np.stack([targets[name] for name in TARGETS], axis=1).astype(np.float32)
    ambiguous_pairs, ambiguous_summary = find_ambiguous_body_history_pairs(
        features=ambiguity_profiles[H1_BODY_ONLY],
        targets=target_matrix,
        sample_rows=sample_rows,
        seed=seed + 47,
        max_search_samples=max_ambiguous_search_samples,
    )
    ambiguous_summary["history_window_steps"] = int(ambiguity_window)
    return (
        sample_rows,
        slip_rows,
        slip_delta_rows,
        pre_limit_rows,
        pre_limit_delta_rows,
        body_feedback_profile_spec_rows(),
        aggregate,
        ambiguous_pairs,
        ambiguous_summary,
    )


def write_body_feedback_artifacts(
    run_dir: Path,
    args: argparse.Namespace,
    sample_rows: list[dict[str, Any]],
    slip_rows: list[dict[str, Any]],
    slip_delta_rows: list[dict[str, Any]],
    pre_limit_rows: list[dict[str, Any]],
    pre_limit_delta_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    aggregate: dict[str, float],
    ambiguous_pairs: list[dict[str, Any]],
    ambiguous_summary: dict[str, Any],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    slip_summary_csv = run_dir / "post_slip_detection_summary.csv"
    slip_delta_csv = run_dir / "post_slip_delta_summary.csv"
    pre_limit_summary_csv = run_dir / "pre_limit_envelope_summary.csv"
    pre_limit_delta_csv = run_dir / "pre_limit_delta_summary.csv"
    profile_spec_csv = run_dir / "profile_spec.csv"
    ambiguous_pairs_csv = run_dir / "ambiguous_body_history_pairs.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    write_csv_rows(samples_csv, sample_rows)
    write_csv_rows(slip_summary_csv, slip_rows)
    write_csv_rows(slip_delta_csv, slip_delta_rows)
    write_csv_rows(pre_limit_summary_csv, pre_limit_rows)
    write_csv_rows(pre_limit_delta_csv, pre_limit_delta_rows)
    write_csv_rows(profile_spec_csv, profile_rows)
    write_csv_rows(ambiguous_pairs_csv, ambiguous_pairs)
    write_json(
        summary_json,
        {
            "run_type": "body_feedback_observability_audit",
            "env_config": args.env_config,
            "episodes": args.episodes,
            "samples": len(sample_rows),
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "history_windows": args.history_windows,
            "history_mode": args.history_mode,
            "targets": TARGETS,
            "feature_profiles": BODY_FEEDBACK_PROFILE_ORDER,
            "phase_summary": sample_phase_summary(sample_rows),
            "post_slip_delta_summary": slip_delta_rows,
            "pre_limit_delta_summary": pre_limit_delta_rows,
            "aggregate_body_feedback_deltas": aggregate,
            "ambiguous_history_summary": ambiguous_summary,
            "input_exclusions": (
                "mu, slip_ratio, v_parallel, tire_force, TTC, path_error, "
                "heading_error, feasibility labels, required clearance"
            ),
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "body_feedback_observability_audit",
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "policy": args.policy,
            "horizon_steps": args.horizon_steps,
            "sample_stride": args.sample_stride,
            "artifacts": {
                "samples_csv": samples_csv,
                "post_slip_detection_summary_csv": slip_summary_csv,
                "post_slip_delta_summary_csv": slip_delta_csv,
                "pre_limit_envelope_summary_csv": pre_limit_summary_csv,
                "pre_limit_delta_summary_csv": pre_limit_delta_csv,
                "profile_spec_csv": profile_spec_csv,
                "ambiguous_body_history_pairs_csv": ambiguous_pairs_csv,
                "summary_json": summary_json,
            },
        },
    )


def aggregate_body_feedback_summaries(summary_paths: tuple[Path, ...]) -> dict[str, Any]:
    summaries = [read_json(path) for path in summary_paths]
    if not summaries:
        raise ValueError("at least one summary path is required")

    def collect_aggregate_metric(metric: str) -> float:
        values = np.asarray(
            [
                float(summary["aggregate_body_feedback_deltas"].get(metric, float("nan")))
                for summary in summaries
            ],
            dtype=np.float64,
        )
        finite = values[np.isfinite(values)]
        return float(np.mean(finite)) if len(finite) else float("nan")

    metrics = sorted({metric for summary in summaries for metric in summary["aggregate_body_feedback_deltas"]})
    aggregate_metrics = {metric: collect_aggregate_metric(metric) for metric in metrics}
    phase_counts: dict[str, int] = {}
    ambiguous_pairs_found = 0
    for summary in summaries:
        for phase, count in summary["phase_summary"]["phase_counts"].items():
            phase_counts[phase] = phase_counts.get(phase, 0) + int(count)
        ambiguous_pairs_found += int(summary["ambiguous_history_summary"].get("pairs_found", 0))
    return {
        "run_type": "body_feedback_observability_audit_multiseed",
        "seed_count": len(summaries),
        "seeds": [int(summary["seed"]) for summary in summaries],
        "summary_paths": [str(path) for path in summary_paths],
        "phase_counts": phase_counts,
        "ambiguous_pairs_found_total": ambiguous_pairs_found,
        "aggregate_metric_means": aggregate_metrics,
    }


def write_body_feedback_multiseed_artifacts(run_dir: Path, summary_paths: tuple[Path, ...]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    summary = aggregate_body_feedback_summaries(summary_paths)
    metric_rows = [
        {"metric": metric, "mean_value": value}
        for metric, value in sorted(summary["aggregate_metric_means"].items())
    ]
    write_csv_rows(run_dir / "aggregate_metric_summary.csv", metric_rows)
    write_json(run_dir / "summary.json", summary)


def parse_summary_paths(value: str) -> tuple[Path, ...]:
    paths = tuple(Path(item.strip()) for item in value.split(",") if item.strip())
    if not paths:
        raise argparse.ArgumentTypeError("summary path list cannot be empty")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M146 body-feedback observability audit.")
    parser.add_argument("--mode", choices=("run", "aggregate"), default="run")
    parser.add_argument("--env-config", type=Path, default=Path("configs/m143_driver_like_profile_audit.json"))
    parser.add_argument("--episodes", type=int, default=40)
    parser.add_argument("--seed", type=int, default=9480)
    parser.add_argument("--policy", default="heuristic")
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--ridge", type=float, default=0.1)
    parser.add_argument("--history-windows", type=parse_history_windows, default=(1, 10, 25))
    parser.add_argument("--history-mode", choices=HISTORY_MODES, default="raw")
    parser.add_argument("--post-slip-beta-threshold", type=float, default=None)
    parser.add_argument("--max-ambiguous-search-samples", type=int, default=450)
    parser.add_argument("--summary-jsons", type=parse_summary_paths, default=())
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "aggregate":
        if not args.summary_jsons:
            raise SystemExit("--summary-jsons is required for aggregate mode")
        run_dir = args.run_dir or Path("runs/m146_body_feedback_observability_multiseed")
        write_body_feedback_multiseed_artifacts(run_dir, args.summary_jsons)
        print(pd.DataFrame(read_json(run_dir / "summary.json")["aggregate_metric_means"], index=[0]).to_string(index=False))
        return

    (
        sample_rows,
        slip_rows,
        slip_delta_rows,
        pre_limit_rows,
        pre_limit_delta_rows,
        profile_rows,
        aggregate,
        ambiguous_pairs,
        ambiguous_summary,
    ) = run_body_feedback_observability_audit(
        env_config_path=args.env_config,
        episodes=args.episodes,
        seed=args.seed,
        policy_name=args.policy,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        train_fraction=args.train_fraction,
        ridge=args.ridge,
        history_windows=args.history_windows,
        history_mode=args.history_mode,
        post_slip_beta_threshold=args.post_slip_beta_threshold,
        max_ambiguous_search_samples=args.max_ambiguous_search_samples,
    )
    run_dir = args.run_dir or make_run_dir(prefix="m146_body_feedback_observability", seed=args.seed)
    write_body_feedback_artifacts(
        run_dir,
        args,
        sample_rows,
        slip_rows,
        slip_delta_rows,
        pre_limit_rows,
        pre_limit_delta_rows,
        profile_rows,
        aggregate,
        ambiguous_pairs,
        ambiguous_summary,
    )
    print("post-slip deltas")
    print(pd.DataFrame(slip_delta_rows).to_string(index=False))
    print("pre-limit deltas")
    print(pd.DataFrame(pre_limit_delta_rows).to_string(index=False))
    print("ambiguous history")
    print(pd.DataFrame([ambiguous_summary]).to_string(index=False))


if __name__ == "__main__":
    main()
