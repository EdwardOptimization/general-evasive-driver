"""Integration tests for the observation-degradation pipeline (D1) and G2 entry-point retest.

Covers the four real entry points that previously constructed bare AutoDriftEnv:

1. train_ppo.make_vector_env (Sync and Parallel, including fork workers)
2. train_ppo.evaluate_actor
3. evaluate.evaluate_policy
4. hidden_swap_gate.collect_decision_snapshot / replay_continuation

It also asserts backward compatibility: when the env config carries no
``observation_degradation`` block, every entry point builds a bare AutoDriftEnv
and the observation/reward streams are bit-for-bit identical to a manually
constructed AutoDriftEnv driven with the same seed schedule.

These tests verify infrastructure correctness only; no self-identification or
capability claim may be derived from them.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

import autodrift.evaluate as evaluate_module
import autodrift.train_ppo as train_ppo_module
from autodrift.config import build_env_config, env_config_to_dict, merge_env_config
from autodrift.env import AutoDriftEnv, DriftEnvConfig, EGO_OBS_DIM, ObservationDegradationConfig
from autodrift.evaluate import evaluate_policy
from autodrift.hidden_swap_gate import collect_decision_snapshot, replay_continuation
from autodrift.observation_degradation_wrapper import (
    DEFAULT_NOISE_SEED_STREAM,
    ObservationDegradationWrapper,
)
from autodrift.train_ppo import ActorCritic, PPOConfig, evaluate_actor, make_vector_env, train
from autodrift.vector_env import ParallelAutoDriftVectorEnv, SyncAutoDriftVectorEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
P0_CONFIG = REPO_ROOT / "configs" / "selfid_positive_control_p0_smoke.json"

GEOMETRY_SLICE = slice(EGO_OBS_DIM, None)  # per-frame indices 9-71 (prev command + geometry)


def _p0_env_data() -> dict:
    return json.loads(P0_CONFIG.read_text(encoding="utf-8"))["env"]


def _p0_env_config(degradation: dict | None = None) -> DriftEnvConfig:
    data = _p0_env_data()
    if degradation is not None:
        data["observation_degradation"] = degradation
    return build_env_config(data)


def _tiny_recurrent_model(obs_dim: int = 72, seed: int = 20260611) -> ActorCritic:
    torch.manual_seed(seed)
    return ActorCritic(obs_dim=obs_dim, act_dim=3, hidden_size=32, actor_encoder="online_gru")


def _action_plan(steps: int, num_envs: int, seed: int = 99) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.uniform(-0.4, 0.4, size=(steps, num_envs, 3)).astype(np.float32)


def _drive_vector_env(env, actions: np.ndarray):
    """Step a vector env with a fixed action plan; tag each frame with (episode, t)."""

    num_envs = env.num_envs
    obs, _ = env.reset()
    episode_index = [0] * num_envs
    episode_time = [0] * num_envs
    frames = [[(episode_index[i], episode_time[i], obs[i].copy())] for i in range(num_envs)]
    rewards: list[np.ndarray] = []
    dones: list[np.ndarray] = []
    for step_actions in actions:
        result = env.step(step_actions)
        rewards.append(result.rewards.copy())
        done = np.logical_or(result.terminated, result.truncated)
        dones.append(done.copy())
        for i in range(num_envs):
            if done[i]:
                episode_index[i] += 1
                episode_time[i] = 0
            else:
                episode_time[i] += 1
            frames[i].append((episode_index[i], episode_time[i], result.observations[i].copy()))
    return frames, np.asarray(rewards), np.asarray(dones)


# ---------------------------------------------------------------------------
# 1. config schema: whitelist, validation, round trip
# ---------------------------------------------------------------------------


def test_build_env_config_accepts_and_round_trips_degradation_block() -> None:
    config = build_env_config({"observation_degradation": {"delay_steps": 12, "noise_std": 0.05}})
    assert config.observation_degradation == ObservationDegradationConfig(delay_steps=12, noise_std=0.05)
    assert config.observation_degradation.noise_seed_stream == DEFAULT_NOISE_SEED_STREAM
    # asdict -> rebuild round trip (checkpoint metadata path)
    assert build_env_config(env_config_to_dict(config)) == config

    per_channel = build_env_config({"observation_degradation": {"noise_std": [0.1] * EGO_OBS_DIM}})
    assert per_channel.observation_degradation.noise_std == tuple([0.1] * EGO_OBS_DIM)
    assert build_env_config(env_config_to_dict(per_channel)) == per_channel

    clean = build_env_config(_p0_env_data())
    assert clean.observation_degradation is None
    assert env_config_to_dict(clean)["observation_degradation"] is None
    assert build_env_config(env_config_to_dict(clean)) == clean


def test_build_env_config_rejects_invalid_degradation_values() -> None:
    with pytest.raises(ValueError, match="unknown env config key"):
        build_env_config({"observation_degradationn": {}})
    with pytest.raises(ValueError, match="unknown observation_degradation config key"):
        build_env_config({"observation_degradation": {"delay": 3}})
    with pytest.raises(ValueError, match="delay_steps must be non-negative"):
        build_env_config({"observation_degradation": {"delay_steps": -1}})
    with pytest.raises(ValueError, match="delay_steps must be an integer"):
        build_env_config({"observation_degradation": {"delay_steps": 1.5}})
    with pytest.raises(ValueError, match="finite and non-negative"):
        build_env_config({"observation_degradation": {"noise_std": -0.1}})
    with pytest.raises(ValueError, match=f"length-{EGO_OBS_DIM}"):
        build_env_config({"observation_degradation": {"noise_std": [0.1, 0.1]}})
    with pytest.raises(ValueError, match="number or a sequence"):
        build_env_config({"observation_degradation": {"noise_std": "high"}})
    with pytest.raises(ValueError, match="mapping or null"):
        build_env_config({"observation_degradation": 5})


def test_merge_env_config_handles_degradation_block() -> None:
    merged = merge_env_config({"dt": 0.02}, {"observation_degradation": {"delay_steps": 5}})
    assert merged["observation_degradation"] == {"delay_steps": 5}
    merged = merge_env_config(merged, {"observation_degradation": {"noise_std": 0.01}})
    assert merged["observation_degradation"] == {"delay_steps": 5, "noise_std": 0.01}
    merged = merge_env_config(merged, {"observation_degradation": None})
    assert merged["observation_degradation"] is None


# ---------------------------------------------------------------------------
# 2. entry point (a): train_ppo.make_vector_env mounts the wrapper
# ---------------------------------------------------------------------------


def test_sync_vector_env_mounts_wrapper_only_when_configured() -> None:
    ppo = PPOConfig(num_envs=2, vector_env_mode="sync")
    degraded = make_vector_env(ppo, _p0_env_config({"delay_steps": 12}), seed=11, seed_sequence=None)
    assert isinstance(degraded, SyncAutoDriftVectorEnv)
    assert all(isinstance(env, ObservationDegradationWrapper) for env in degraded.envs)
    assert all(env.delay_steps == 12 for env in degraded.envs)

    clean = make_vector_env(ppo, _p0_env_config(), seed=11, seed_sequence=None)
    assert all(isinstance(env, AutoDriftEnv) for env in clean.envs)
    assert not any(isinstance(env, ObservationDegradationWrapper) for env in clean.envs)


def test_g2_delay12_semantics_through_real_training_entry() -> None:
    """G2 core: bit-level delay semantics measured through train_ppo.make_vector_env."""

    delay = 12
    steps = 200
    ppo = PPOConfig(num_envs=1, vector_env_mode="sync")
    actions = _action_plan(steps, num_envs=1)

    clean_env = make_vector_env(ppo, _p0_env_config(), seed=4242, seed_sequence=None)
    degraded_env = make_vector_env(ppo, _p0_env_config({"delay_steps": delay}), seed=4242, seed_sequence=None)
    clean_frames, clean_rewards, clean_dones = _drive_vector_env(clean_env, actions)
    degraded_frames, degraded_rewards, degraded_dones = _drive_vector_env(degraded_env, actions)

    # Degradation must not touch dynamics: rewards and done flags bitwise identical.
    np.testing.assert_array_equal(clean_rewards, degraded_rewards)
    np.testing.assert_array_equal(clean_dones, degraded_dones)
    assert int(clean_dones.sum()) >= 2, "test needs at least 2 episode boundaries to exercise auto-reset"

    clean_by_key = {(episode, t): frame for episode, t, frame in clean_frames[0]}
    ego_mismatch = 0
    geometry_mismatch = 0
    current_diff_steps = []
    max_abs_current_diff = 0.0
    for index, (episode, t, frame) in enumerate(degraded_frames[0]):
        clean_now = clean_by_key[(episode, t)]
        clean_then = clean_by_key[(episode, max(t - delay, 0))]
        # channels 9-71 bitwise identical to the clean stream at the same step
        if not np.array_equal(frame[GEOMETRY_SLICE], clean_now[GEOMETRY_SLICE]):
            geometry_mismatch += 1
        # ego channels 0-8 bitwise equal to the clean stream delay steps earlier
        if not np.array_equal(frame[:EGO_OBS_DIM], clean_then[:EGO_OBS_DIM]):
            ego_mismatch += 1
        if not np.array_equal(frame[:EGO_OBS_DIM], clean_now[:EGO_OBS_DIM]):
            current_diff_steps.append(index)
            max_abs_current_diff = max(
                max_abs_current_diff,
                float(np.max(np.abs(frame[:EGO_OBS_DIM] - clean_now[:EGO_OBS_DIM]))),
            )
    assert ego_mismatch == 0, f"{ego_mismatch} frames violated the t-{delay} delay semantics"
    assert geometry_mismatch == 0, f"{geometry_mismatch} frames had non-ego channel deviations"
    # the delay must actually bite: most frames differ from the clean current frame
    assert len(current_diff_steps) > steps // 2
    assert current_diff_steps[0] >= 1  # frame 0 of each episode is clamped, so identical
    assert max_abs_current_diff > 0.0
    print(
        "G2 delay-12 via make_vector_env: frames_compared="
        f"{len(degraded_frames[0])} ego_t_minus_12_mismatch=0 geometry_mismatch=0 "
        f"rewards_bitwise_identical=True first_current_diff_frame={current_diff_steps[0]} "
        f"current_diff_frames={len(current_diff_steps)} max_abs_current_diff={max_abs_current_diff:.6f} "
        f"episodes_crossed={int(clean_dones.sum())}"
    )


def test_parallel_vector_env_fork_workers_apply_identical_degradation() -> None:
    """Parallel fork workers must produce the same degraded stream as sync envs."""

    steps = 60
    env_config = _p0_env_config({"delay_steps": 12, "noise_std": 0.05})
    actions = _action_plan(steps, num_envs=2, seed=7)
    sync_env = make_vector_env(
        PPOConfig(num_envs=2, vector_env_mode="sync"), env_config, seed=900, seed_sequence=None
    )
    parallel_env = make_vector_env(
        PPOConfig(num_envs=2, vector_env_mode="parallel", vector_env_start_method="fork"),
        env_config,
        seed=900,
        seed_sequence=None,
    )
    assert isinstance(parallel_env, ParallelAutoDriftVectorEnv)
    try:
        sync_frames, sync_rewards, _ = _drive_vector_env(sync_env, actions)
        parallel_frames, parallel_rewards, _ = _drive_vector_env(parallel_env, actions)
    finally:
        parallel_env.close()
    np.testing.assert_array_equal(sync_rewards, parallel_rewards)
    for env_index in range(2):
        for (se, st, sf), (pe, pt, pf) in zip(sync_frames[env_index], parallel_frames[env_index], strict=True):
            assert (se, st) == (pe, pt)
            np.testing.assert_array_equal(sf, pf)

    # and the degraded parallel stream must differ from a clean parallel stream
    clean_parallel = make_vector_env(
        PPOConfig(num_envs=2, vector_env_mode="parallel", vector_env_start_method="fork"),
        _p0_env_config(),
        seed=900,
        seed_sequence=None,
    )
    try:
        clean_frames, _, _ = _drive_vector_env(clean_parallel, actions)
    finally:
        clean_parallel.close()
    assert any(
        not np.array_equal(cf[:EGO_OBS_DIM], pf[:EGO_OBS_DIM])
        for (_, _, cf), (_, _, pf) in zip(clean_frames[0], parallel_frames[0], strict=True)
    )


def test_sync_vector_env_without_key_matches_bare_env_bitwise() -> None:
    """Backward compatibility: no degradation key => stream identical to bare AutoDriftEnv."""

    steps = 120
    seed = 31337
    env_config = _p0_env_config()
    actions = _action_plan(steps, num_envs=1, seed=3)
    vec = make_vector_env(PPOConfig(num_envs=1, vector_env_mode="sync"), env_config, seed=seed, seed_sequence=None)
    frames, rewards, dones = _drive_vector_env(vec, actions)

    # replicate the historical code path: bare AutoDriftEnv + the vector seed schedule
    env = AutoDriftEnv(env_config)
    reset_count = 0
    obs, _ = env.reset(seed=seed + reset_count)
    reset_count += 1
    reference_frames = [obs.copy()]
    reference_rewards = []
    for step_actions in actions:
        obs, reward, terminated, truncated, _ = env.step(step_actions[0])
        reference_rewards.append(reward)
        if terminated or truncated:
            obs, _ = env.reset(seed=seed + reset_count)
            reset_count += 1
        reference_frames.append(obs.copy())
    np.testing.assert_array_equal(
        np.asarray([frame for _, _, frame in frames[0]], dtype=np.float32),
        np.asarray(reference_frames, dtype=np.float32),
    )
    np.testing.assert_array_equal(rewards[:, 0], np.asarray(reference_rewards, dtype=np.float32))


# ---------------------------------------------------------------------------
# 3. entry point (b): train_ppo.evaluate_actor
# ---------------------------------------------------------------------------


def test_evaluate_actor_mounts_wrapper_and_stays_clean_without_key(monkeypatch) -> None:
    model = _tiny_recurrent_model()
    created: list[str] = []
    real_factory = train_ppo_module.make_env_from_config

    def spy(config):
        env = real_factory(config)
        created.append(type(env).__name__)
        return env

    monkeypatch.setattr(train_ppo_module, "make_env_from_config", spy)
    evaluate_actor(model, episodes=1, seed=0, env_config=_p0_env_config({"delay_steps": 25}))
    evaluate_actor(model, episodes=1, seed=0, env_config=_p0_env_config())
    assert created == ["ObservationDegradationWrapper", "AutoDriftEnv"]


def test_evaluate_actor_degradation_changes_trajectories_and_clean_is_deterministic() -> None:
    model = _tiny_recurrent_model()
    clean_a = evaluate_actor(model, episodes=2, seed=123, env_config=_p0_env_config())
    clean_b = evaluate_actor(model, episodes=2, seed=123, env_config=_p0_env_config())
    assert clean_a == clean_b  # bitwise repeatable without the key
    degraded = evaluate_actor(model, episodes=2, seed=123, env_config=_p0_env_config({"delay_steps": 25}))
    assert degraded != clean_a  # the delayed ego stream must change closed-loop behavior


# ---------------------------------------------------------------------------
# 4. entry point (c): evaluate.evaluate_policy
# ---------------------------------------------------------------------------


def test_evaluate_policy_mounts_wrapper_and_stays_clean_without_key(monkeypatch) -> None:
    created: list[str] = []
    real_factory = evaluate_module.make_env_from_config

    def spy(config):
        env = real_factory(config)
        created.append(type(env).__name__)
        return env

    monkeypatch.setattr(evaluate_module, "make_env_from_config", spy)
    rows_degraded, _ = evaluate_policy(
        "heuristic", episodes=1, seed=5, env_config=_p0_env_config({"delay_steps": 12, "noise_std": 0.05})
    )
    rows_clean, _ = evaluate_policy("heuristic", episodes=1, seed=5, env_config=_p0_env_config())
    assert created == ["ObservationDegradationWrapper", "AutoDriftEnv"]
    assert np.isfinite(rows_degraded[0]["return"])
    assert np.isfinite(rows_clean[0]["return"])


def _rows_equal_bitwise(row_a: dict, row_b: dict) -> bool:
    if row_a.keys() != row_b.keys():
        return False
    for key in row_a:
        a, b = row_a[key], row_b[key]
        if isinstance(a, float) and isinstance(b, float) and np.isnan(a) and np.isnan(b):
            continue  # NaN placeholders count as identical
        if a != b:
            return False
    return True


def test_evaluate_policy_backward_compatible_rows_without_key() -> None:
    rows_a, summary_a = evaluate_policy("heuristic", episodes=2, seed=77, env_config=_p0_env_config())
    rows_b, summary_b = evaluate_policy("heuristic", episodes=2, seed=77, env_config=_p0_env_config())
    assert _rows_equal_bitwise(summary_a, summary_b)
    for row_a, row_b in zip(rows_a, rows_b, strict=True):
        assert _rows_equal_bitwise(row_a, row_b)


# ---------------------------------------------------------------------------
# 5. entry point (d): hidden_swap_gate snapshot + replay
# ---------------------------------------------------------------------------


def _find_snapshot(model, env_config, seeds=range(995600, 995620)):
    for seed in seeds:
        snapshot = collect_decision_snapshot(model, env_config, "nominal", seed)
        if snapshot is not None:
            return snapshot
    raise AssertionError("no decision snapshot found in the audit seed range")


def test_hidden_swap_gate_snapshot_and_replay_use_wrapped_env() -> None:
    model = _tiny_recurrent_model()
    degraded_config = _p0_env_config({"delay_steps": 12})
    snapshot = _find_snapshot(model, degraded_config)
    assert isinstance(snapshot.env, ObservationDegradationWrapper)
    assert snapshot.env.delay_steps == 12
    # replay path deep-copies the snapshot env, so the wrapper (and its ring
    # buffer state) must survive into the continuation
    for variant in ("normal", "reset"):
        row, actions = replay_continuation(
            model,
            snapshot,
            env_config=degraded_config,
            variant=variant,
            max_continuation_steps=10,
        )
        assert np.isfinite(row["return"])
        assert len(actions) >= 1

    clean_snapshot = _find_snapshot(model, _p0_env_config())
    assert isinstance(clean_snapshot.env, AutoDriftEnv)
    assert not isinstance(clean_snapshot.env, ObservationDegradationWrapper)


# ---------------------------------------------------------------------------
# 6. 1024-step smoke trainings through the real train() entry
# ---------------------------------------------------------------------------


def _smoke_ppo_config() -> PPOConfig:
    raw = json.loads(P0_CONFIG.read_text(encoding="utf-8"))["ppo"]
    valid = {field for field in PPOConfig.__dataclass_fields__}
    ppo = PPOConfig(**{key: value for key, value in raw.items() if key in valid})
    return replace(ppo, total_steps=1024, rollout_steps=128, num_envs=2, minibatch_size=128, device="cpu")


@pytest.mark.parametrize(
    "degradation",
    [
        {"delay_steps": 0, "noise_std": 0.0},  # wrapped clean cell (T1)
        {"delay_steps": 25, "noise_std": 0.0},  # T4
    ],
    ids=["clean_wrapped", "delay_25"],
)
def test_smoke_training_1024_steps_with_degradation(tmp_path: Path, degradation: dict) -> None:
    env_config = _p0_env_config(degradation)
    model = train(
        _smoke_ppo_config(),
        save_path=tmp_path / "checkpoint.pt",
        metrics_csv_path=tmp_path / "metrics.csv",
        env_config=env_config,
    )
    assert (tmp_path / "checkpoint.pt").exists()
    summary = evaluate_actor(model, episodes=1, seed=424242, env_config=env_config)
    assert all(np.isfinite(value) for value in summary.values()), summary
