"""WP0 extended degradation modes: AR(1) noise, frame dropout, time-varying delay.

Pre-registered acceptance criteria (M3214 extension, Phase-2 WP0 week-1):

1. Loud ValueError validation for every new parameter, through both the config
   schema (``build_env_config``) and direct wrapper construction.
2. Clean-anchor bit reproduction: parameter defaults run the original code
   path (structural guarantee asserted by poisoning the extended branch), and
   the legacy (delay_steps, noise_std) stream stays pinned to the documented
   ``[stream, seed_root, episode]`` derivation bit for bit.
3. AR(1): rho=0 is bit-identical to the existing iid ``noise_std`` path; the
   recursion matches the documented form bitwise; measured lag-1
   autocorrelation is within 0.05 of rho.
4. Dropout: hold-last-degraded-value semantics bitwise, frame 0 never dropped,
   deterministic per-episode mask on a disjoint substream.
5. Time-varying delay: "episode_random" episodes are bitwise equal to the
   matching constant-delay wrapper; "piecewise" segments are bitwise aligned
   with the matching constant-delay wrappers; schedules are seed-derived and
   exposed via ``episode_delay_schedule``.
6. Config round trip (config -> dict -> config equal) for all new fields;
   geometry channels (per-frame indices 9+) and reward/termination streams
   bitwise untouched by every new mode.

These tests verify infrastructure correctness only; no capability or
self-identification claim may be derived from them.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from autodrift.config import build_env_config, env_config_to_dict, merge_env_config
from autodrift.env import AutoDriftEnv, DriftEnvConfig, EGO_OBS_DIM, ObservationDegradationConfig
from autodrift.observation_degradation_wrapper import (
    DEFAULT_NOISE_SEED_STREAM,
    DELAY_PROFILE_SEED_SUBSTREAM,
    DROPOUT_SEED_SUBSTREAM,
    ObservationDegradationWrapper,
    make_env_from_config,
    make_observation_degradation_env,
)

GEOMETRY_SLICE = slice(EGO_OBS_DIM, None)


def _base_config(**overrides) -> DriftEnvConfig:
    return replace(DriftEnvConfig(), **overrides)


def _action_sequence(steps: int, seed: int = 7, scale: float = 0.4) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.uniform(-scale, scale, 3).astype(np.float64) for _ in range(steps)]


def _rollout(env, seed: int, actions: list[np.ndarray]):
    obs, _ = env.reset(seed=seed)
    frames = [np.asarray(obs, dtype=np.float32).copy()]
    rewards: list[float] = []
    for action in actions:
        obs, reward, terminated, truncated, _ = env.step(action)
        frames.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        if terminated or truncated:
            break
    return frames, rewards


# ---------------------------------------------------------------------------
# 1. loud validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("block", "match"),
    [
        ({"ar1_rho": 1.0, "ar1_sigma": 0.05}, "ar1_rho must satisfy"),
        ({"ar1_rho": -0.1, "ar1_sigma": 0.05}, "ar1_rho must satisfy"),
        ({"ar1_rho": float("nan"), "ar1_sigma": 0.05}, "ar1_rho must satisfy"),
        ({"ar1_rho": "high"}, "ar1_rho must be a number"),
        ({"ar1_rho": 0.5}, "requires a positive ar1_sigma"),
        ({"ar1_sigma": -0.1}, "finite and non-negative"),
        ({"ar1_sigma": [0.1, 0.1]}, f"length-{EGO_OBS_DIM}"),
        ({"ar1_sigma": "high"}, "ar1_sigma must be a number"),
        ({"noise_std": 0.05, "ar1_sigma": 0.05}, "mutually exclusive"),
        ({"dropout_prob": 1.0}, "dropout_prob must satisfy"),
        ({"dropout_prob": -0.01}, "dropout_prob must satisfy"),
        ({"dropout_prob": "often"}, "dropout_prob must be a number"),
        ({"delay_profile": "linear"}, "delay_profile must be one of"),
        ({"delay_lo": 3}, "require delay_profile"),
        ({"delay_hi": 3}, "require delay_profile"),
        (
            {"delay_profile": "episode_random", "delay_steps": 5, "delay_lo": 1, "delay_hi": 5},
            "must stay 0",
        ),
        (
            {"delay_profile": "episode_random", "delay_lo": 5, "delay_hi": 2},
            "delay_hi must be >= delay_lo",
        ),
        (
            {"delay_profile": "episode_random", "delay_lo": 0, "delay_hi": 0},
            "requires delay_hi > 0",
        ),
        ({"delay_profile": "piecewise", "delay_lo": 5, "delay_hi": 5}, "delay_hi > delay_lo"),
        (
            {"delay_profile": "episode_random", "delay_lo": 1.5, "delay_hi": 5},
            "delay_lo must be an integer",
        ),
        (
            {"delay_profile": "episode_random", "delay_lo": 1, "delay_hi": -2},
            "delay_hi must be non-negative",
        ),
    ],
)
def test_build_env_config_rejects_invalid_extended_values(block: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        build_env_config({"observation_degradation": block})


def test_build_env_config_rejects_unknown_extended_key() -> None:
    with pytest.raises(ValueError, match="unknown observation_degradation config key"):
        build_env_config({"observation_degradation": {"ar1_rh": 0.5}})


def test_wrapper_kwargs_are_validated_loudly() -> None:
    config = _base_config()
    with pytest.raises(ValueError, match="ar1_rho"):
        make_observation_degradation_env(config, ar1_rho=0.95)
    with pytest.raises(ValueError, match="ar1_sigma"):
        make_observation_degradation_env(config, ar1_sigma=[0.1, 0.1])
    with pytest.raises(ValueError, match="dropout_prob"):
        make_observation_degradation_env(config, dropout_prob=1.0)
    with pytest.raises(ValueError, match="delay_profile"):
        make_observation_degradation_env(config, delay_profile="weekly")
    with pytest.raises(ValueError, match="mutually exclusive"):
        make_observation_degradation_env(config, noise_std=0.05, ar1_rho=0.5, ar1_sigma=0.05)
    with pytest.raises(ValueError, match="max_steps >= 4"):
        make_observation_degradation_env(
            _base_config(max_steps=3), delay_profile="piecewise", delay_lo=1, delay_hi=5
        )


# ---------------------------------------------------------------------------
# 2. clean-anchor bit reproduction
# ---------------------------------------------------------------------------


def test_default_and_legacy_parameters_never_enter_extended_path() -> None:
    config = _base_config()
    actions = _action_sequence(15)

    defaults = make_observation_degradation_env(config)
    assert defaults._extended is False

    legacy = make_observation_degradation_env(config, delay_steps=12, noise_std=0.05)
    assert legacy._extended is False

    def _boom() -> np.ndarray:
        raise AssertionError("extended degradation path entered for a legacy configuration")

    legacy._extended_degraded_value = _boom  # type: ignore[method-assign]
    frames, _ = _rollout(legacy, seed=17, actions=actions)
    assert len(frames) >= 2

    extended = make_observation_degradation_env(config, ar1_rho=0.5, ar1_sigma=0.05)
    assert extended._extended is True


def test_legacy_delay_noise_stream_pinned_to_documented_derivation() -> None:
    """Bit-level pin of the pre-WP0 behavior: delay + iid noise from [stream, seed, 0]."""

    config = _base_config()
    delay, std, seed = 12, 0.05, 606
    actions = _action_sequence(40, seed=3)
    raw_frames, raw_rewards = _rollout(AutoDriftEnv(config), seed=seed, actions=actions)
    degraded_frames, degraded_rewards = _rollout(
        make_observation_degradation_env(config, delay_steps=delay, noise_std=std),
        seed=seed,
        actions=actions,
    )
    assert degraded_rewards == raw_rewards
    rng = np.random.default_rng([DEFAULT_NOISE_SEED_STREAM, seed, 0])
    for t, frame in enumerate(degraded_frames):
        noise = rng.normal(0.0, 1.0, EGO_OBS_DIM) * np.full(EGO_OBS_DIM, std, dtype=np.float64)
        expected = raw_frames[max(t - delay, 0)][:EGO_OBS_DIM].astype(np.float64) + noise
        np.testing.assert_array_equal(frame[:EGO_OBS_DIM], expected.astype(np.float32))
        np.testing.assert_array_equal(frame[GEOMETRY_SLICE], raw_frames[t][GEOMETRY_SLICE])


# ---------------------------------------------------------------------------
# 3. AR(1) correlated noise
# ---------------------------------------------------------------------------


def test_ar1_rho_zero_is_bitwise_equal_to_iid_noise_path() -> None:
    config = _base_config()
    actions = _action_sequence(30, seed=21)
    iid_frames, iid_rewards = _rollout(
        make_observation_degradation_env(config, delay_steps=4, noise_std=0.05),
        seed=99,
        actions=actions,
    )
    ar1_frames, ar1_rewards = _rollout(
        make_observation_degradation_env(config, delay_steps=4, ar1_rho=0.0, ar1_sigma=0.05),
        seed=99,
        actions=actions,
    )
    assert iid_rewards == ar1_rewards
    assert len(iid_frames) == len(ar1_frames)
    for frame_iid, frame_ar1 in zip(iid_frames, ar1_frames, strict=True):
        np.testing.assert_array_equal(frame_iid, frame_ar1)


def test_ar1_noise_matches_documented_recursion_bitwise() -> None:
    config = _base_config()
    delay, rho, seed = 3, 0.6, 2024
    sigma = tuple(0.01 * (index + 1) for index in range(EGO_OBS_DIM))
    actions = _action_sequence(35, seed=13)
    raw_frames, _ = _rollout(AutoDriftEnv(config), seed=seed, actions=actions)
    degraded_frames, _ = _rollout(
        make_observation_degradation_env(
            config, delay_steps=delay, ar1_rho=rho, ar1_sigma=sigma
        ),
        seed=seed,
        actions=actions,
    )
    rng = np.random.default_rng([DEFAULT_NOISE_SEED_STREAM, seed, 0])
    sigma_vec = np.asarray(sigma, dtype=np.float64)
    state = np.zeros(EGO_OBS_DIM, dtype=np.float64)
    for t, frame in enumerate(degraded_frames):
        eps = rng.normal(0.0, 1.0, EGO_OBS_DIM)
        state = rho * state + eps * sigma_vec
        expected = raw_frames[max(t - delay, 0)][:EGO_OBS_DIM].astype(np.float64) + state
        np.testing.assert_array_equal(frame[:EGO_OBS_DIM], expected.astype(np.float32))
        np.testing.assert_array_equal(frame[GEOMETRY_SLICE], raw_frames[t][GEOMETRY_SLICE])


def _collect_noise_series(rho: float, sigma: float, min_frames: int) -> list[np.ndarray]:
    """Extract per-episode AR(1) noise series (burn-in trimmed) from real rollouts."""

    config = _base_config()
    series: list[np.ndarray] = []
    total = 0
    for seed in range(40):
        actions = _action_sequence(240, seed=seed + 1000, scale=0.25)
        raw_frames, _ = _rollout(AutoDriftEnv(config), seed=seed, actions=actions)
        degraded_frames, _ = _rollout(
            make_observation_degradation_env(config, ar1_rho=rho, ar1_sigma=sigma),
            seed=seed,
            actions=actions,
        )
        noise = np.asarray(
            [
                degraded[:EGO_OBS_DIM].astype(np.float64) - raw[:EGO_OBS_DIM].astype(np.float64)
                for degraded, raw in zip(degraded_frames, raw_frames, strict=True)
            ]
        )
        if noise.shape[0] <= 50:
            continue
        trimmed = noise[20:]  # burn-in past the zero-initialized transient
        series.append(trimmed)
        total += trimmed.shape[0]
        if total >= min_frames:
            break
    assert total >= min_frames, f"only collected {total} noise frames"
    return series


def _pooled_lag1_autocorr(series: list[np.ndarray]) -> float:
    """Zero-mean lag-1 autocorrelation pooled over episodes and channels."""

    numerator = 0.0
    denominator = 0.0
    for block in series:
        numerator += float(np.sum(block[1:] * block[:-1]))
        denominator += float(np.sum(np.square(block)))
    return numerator / denominator


def test_ar1_measured_autocorrelation_matches_rho() -> None:
    sigma = 0.05
    series_correlated = _collect_noise_series(rho=0.8, sigma=sigma, min_frames=1200)
    autocorr = _pooled_lag1_autocorr(series_correlated)
    assert abs(autocorr - 0.8) < 0.05, f"measured lag-1 autocorr {autocorr:.4f}, expected ~0.8"

    series_iid = _collect_noise_series(rho=0.0, sigma=sigma, min_frames=1200)
    autocorr_iid = _pooled_lag1_autocorr(series_iid)
    assert abs(autocorr_iid) < 0.05, f"measured lag-1 autocorr {autocorr_iid:.4f}, expected ~0"
    pooled_std = float(
        np.sqrt(
            sum(float(np.sum(np.square(block))) for block in series_iid)
            / sum(block.size for block in series_iid)
        )
    )
    assert 0.9 * sigma < pooled_std < 1.1 * sigma
    # rho=0.8 stationary std is sigma / sqrt(1 - rho^2) = 1.667 sigma: variance inflation visible
    pooled_std_correlated = float(
        np.sqrt(
            sum(float(np.sum(np.square(block))) for block in series_correlated)
            / sum(block.size for block in series_correlated)
        )
    )
    assert pooled_std_correlated > 1.3 * sigma
    print(
        f"AR1 stats: autocorr(rho=0.8)={autocorr:.4f} autocorr(rho=0)={autocorr_iid:.4f} "
        f"std(rho=0)={pooled_std:.5f} std(rho=0.8)={pooled_std_correlated:.5f} (sigma={sigma})"
    )


# ---------------------------------------------------------------------------
# 4. frame dropout (hold-last-degraded-value)
# ---------------------------------------------------------------------------


def test_dropout_holds_last_degraded_value_bitwise() -> None:
    config = _base_config()
    delay, prob, seed = 2, 0.5, 314
    actions = _action_sequence(50, seed=11)
    raw_frames, raw_rewards = _rollout(AutoDriftEnv(config), seed=seed, actions=actions)
    degraded_frames, degraded_rewards = _rollout(
        make_observation_degradation_env(config, delay_steps=delay, dropout_prob=prob),
        seed=seed,
        actions=actions,
    )
    assert degraded_rewards == raw_rewards
    dropout_rng = np.random.default_rng(
        [DEFAULT_NOISE_SEED_STREAM, seed, 0, DROPOUT_SEED_SUBSTREAM]
    )
    expected: list[np.ndarray] = []
    mask: list[bool] = []
    for t, frame in enumerate(degraded_frames):
        dropped = bool(float(dropout_rng.uniform()) < prob) and t > 0
        if dropped:
            value = expected[t - 1]
            # hold-last-value also means bitwise equality with the previous frame
            np.testing.assert_array_equal(
                frame[:EGO_OBS_DIM], degraded_frames[t - 1][:EGO_OBS_DIM]
            )
        else:
            value = raw_frames[max(t - delay, 0)][:EGO_OBS_DIM].astype(np.float64)
        expected.append(value)
        mask.append(dropped)
        np.testing.assert_array_equal(frame[:EGO_OBS_DIM], value.astype(np.float32))
        np.testing.assert_array_equal(frame[GEOMETRY_SLICE], raw_frames[t][GEOMETRY_SLICE])
    assert mask[0] is False, "frame 0 must never be dropped"
    assert any(mask), "test must observe at least one dropped frame"
    assert not all(mask[1:]), "test must observe at least one delivered frame"
    assert any(mask[i] and mask[i + 1] for i in range(len(mask) - 1)), (
        "test must observe a consecutive hold-through"
    )


def test_dropout_mask_is_deterministic_and_stream_separated() -> None:
    config = _base_config()
    actions = _action_sequence(40, seed=29)
    frames_a, _ = _rollout(
        make_observation_degradation_env(config, dropout_prob=0.5, delay_steps=2),
        seed=808,
        actions=actions,
    )
    frames_b, _ = _rollout(
        make_observation_degradation_env(config, dropout_prob=0.5, delay_steps=2),
        seed=808,
        actions=actions,
    )
    for frame_a, frame_b in zip(frames_a, frames_b, strict=True):
        np.testing.assert_array_equal(frame_a, frame_b)

    # different substream root => different mask on identical raw trajectories
    frames_c, _ = _rollout(
        make_observation_degradation_env(
            config, dropout_prob=0.5, delay_steps=2, noise_seed_stream=777
        ),
        seed=808,
        actions=actions,
    )
    assert any(
        not np.array_equal(frame_a[:EGO_OBS_DIM], frame_c[:EGO_OBS_DIM])
        for frame_a, frame_c in zip(frames_a, frames_c, strict=True)
    )


# ---------------------------------------------------------------------------
# 5. time-varying delay profiles
# ---------------------------------------------------------------------------


def test_episode_random_delay_is_bitwise_equal_to_matching_constant_delay() -> None:
    config = _base_config()
    actions = _action_sequence(60, seed=5)
    env = make_observation_degradation_env(
        config, delay_profile="episode_random", delay_lo=2, delay_hi=20
    )
    frames, rewards = _rollout(env, seed=2026, actions=actions)
    schedule = env.episode_delay_schedule
    assert schedule is not None
    assert schedule.shape == (config.max_steps + 1,)
    assert len(set(schedule.tolist())) == 1, "episode_random must hold one delay per episode"
    delay = int(schedule[0])
    assert 2 <= delay <= 20

    constant_frames, constant_rewards = _rollout(
        make_observation_degradation_env(config, delay_steps=delay), seed=2026, actions=actions
    )
    assert rewards == constant_rewards
    for frame, constant in zip(frames, constant_frames, strict=True):
        np.testing.assert_array_equal(frame, constant)


def test_episode_random_delay_varies_across_episodes_and_is_seed_derived() -> None:
    config = _base_config()
    actions = _action_sequence(5, seed=41)

    def _episode_delays(env) -> list[int]:
        delays = []
        env.reset(seed=777)
        delays.append(int(env.episode_delay_schedule[0]))
        for _ in range(4):
            env.reset()  # unseeded: episode index advances, seed_root retained
            delays.append(int(env.episode_delay_schedule[0]))
        return delays

    env_a = make_observation_degradation_env(
        config, delay_profile="episode_random", delay_lo=2, delay_hi=30
    )
    env_b = make_observation_degradation_env(
        config, delay_profile="episode_random", delay_lo=2, delay_hi=30
    )
    delays_a = _episode_delays(env_a)
    delays_b = _episode_delays(env_b)
    assert delays_a == delays_b, "episode delay sequence must be seed-derived"
    assert len(set(delays_a)) >= 2, "delays must vary across episodes"
    assert all(2 <= delay <= 30 for delay in delays_a)

    # rollout determinism after the schedule probing above
    frames_a1, _ = _rollout(env_a, seed=777, actions=actions)
    frames_b1, _ = _rollout(env_b, seed=777, actions=actions)
    for frame_a, frame_b in zip(frames_a1, frames_b1, strict=True):
        np.testing.assert_array_equal(frame_a, frame_b)


def test_piecewise_delay_segments_align_bitwise_with_constant_delay() -> None:
    config = _base_config(max_steps=120)
    seed = 4444
    actions = _action_sequence(120, seed=9, scale=0.2)
    env = make_observation_degradation_env(
        config, delay_profile="piecewise", delay_lo=0, delay_hi=12
    )
    frames, rewards = _rollout(env, seed=seed, actions=actions)
    schedule = env.episode_delay_schedule
    assert schedule is not None
    assert schedule.shape == (config.max_steps + 1,)

    # parse segments (runs of constant delay)
    change_points = [0] + [t for t in range(1, len(schedule)) if schedule[t] != schedule[t - 1]]
    segments = [
        (start, (change_points + [len(schedule)])[index + 1], int(schedule[start]))
        for index, start in enumerate(change_points)
    ]
    assert 2 <= len(segments) <= 3, f"expected 2-3 segments, got {len(segments)}"
    assert all(0 <= delay <= 12 for _, _, delay in segments)
    for (_, _, left), (_, _, right) in zip(segments, segments[1:]):
        assert left != right, "adjacent piecewise segments must carry different delays"
    assert len(frames) > segments[0][1] + 5, "episode must reach beyond the first cut point"

    raw_frames, raw_rewards = _rollout(AutoDriftEnv(config), seed=seed, actions=actions)
    assert rewards == raw_rewards
    for t, frame in enumerate(frames):
        source = raw_frames[max(t - int(schedule[t]), 0)]
        np.testing.assert_array_equal(frame[:EGO_OBS_DIM], source[:EGO_OBS_DIM])
        np.testing.assert_array_equal(frame[GEOMETRY_SLICE], raw_frames[t][GEOMETRY_SLICE])

    # per-segment bitwise alignment against the matching constant-delay wrapper
    observed_segments = 0
    for start, end, delay in segments:
        if start >= len(frames):
            continue
        constant_frames, _ = _rollout(
            make_observation_degradation_env(config, delay_steps=delay), seed=seed, actions=actions
        )
        for t in range(start, min(end, len(frames))):
            np.testing.assert_array_equal(
                frames[t][:EGO_OBS_DIM], constant_frames[t][:EGO_OBS_DIM]
            )
        observed_segments += 1
    assert observed_segments >= 2, "at least two segments must be exercised by the episode"

    # seed-derived determinism of the schedule
    env_repeat = make_observation_degradation_env(
        config, delay_profile="piecewise", delay_lo=0, delay_hi=12
    )
    env_repeat.reset(seed=seed)
    np.testing.assert_array_equal(env_repeat.episode_delay_schedule, schedule)


def test_delay_profile_substreams_do_not_shift_noise_draws() -> None:
    """Enabling a delay profile must not perturb the iid noise stream alignment."""

    config = _base_config()
    seed = 31415
    actions = _action_sequence(40, seed=23)
    raw_frames, _ = _rollout(AutoDriftEnv(config), seed=seed, actions=actions)
    env = make_observation_degradation_env(
        config, noise_std=0.05, delay_profile="episode_random", delay_lo=1, delay_hi=10
    )
    frames, _ = _rollout(env, seed=seed, actions=actions)
    delay = int(env.episode_delay_schedule[0])
    rng = np.random.default_rng([DEFAULT_NOISE_SEED_STREAM, seed, 0])
    for t, frame in enumerate(frames):
        noise = rng.normal(0.0, 1.0, EGO_OBS_DIM) * np.full(EGO_OBS_DIM, 0.05, dtype=np.float64)
        expected = raw_frames[max(t - delay, 0)][:EGO_OBS_DIM].astype(np.float64) + noise
        np.testing.assert_array_equal(frame[:EGO_OBS_DIM], expected.astype(np.float32))


# ---------------------------------------------------------------------------
# 6. composition, history stacks, config plumbing
# ---------------------------------------------------------------------------


def test_composed_modes_leave_geometry_rewards_and_termination_untouched() -> None:
    env_config = build_env_config(
        {
            "observation_degradation": {
                "ar1_rho": 0.8,
                "ar1_sigma": 0.05,
                "dropout_prob": 0.2,
                "delay_profile": "episode_random",
                "delay_lo": 1,
                "delay_hi": 10,
            }
        }
    )
    env = make_env_from_config(env_config)
    assert isinstance(env, ObservationDegradationWrapper)
    assert env.ar1_rho == 0.8
    assert env.dropout_prob == 0.2
    assert env.delay_profile == "episode_random"
    assert (env.delay_lo, env.delay_hi) == (1, 10)

    actions = _action_sequence(60, seed=37)
    raw_frames, raw_rewards = _rollout(AutoDriftEnv(env_config), seed=515, actions=actions)
    frames, rewards = _rollout(env, seed=515, actions=actions)
    assert rewards == raw_rewards
    assert len(frames) == len(raw_frames)
    for frame, raw in zip(frames, raw_frames, strict=True):
        np.testing.assert_array_equal(frame[GEOMETRY_SLICE], raw[GEOMETRY_SLICE])
        assert np.all(np.isfinite(frame))
    assert any(
        not np.array_equal(frame[:EGO_OBS_DIM], raw[:EGO_OBS_DIM])
        for frame, raw in zip(frames, raw_frames, strict=True)
    )

    # determinism of the full composition
    frames_repeat, _ = _rollout(make_env_from_config(env_config), seed=515, actions=actions)
    for frame, repeat in zip(frames, frames_repeat, strict=True):
        np.testing.assert_array_equal(frame, repeat)


def test_history_stack_frames_are_degraded_per_frame_in_extended_modes() -> None:
    config = _base_config(history_length=3)
    base_dim = AutoDriftEnv(config).base_obs_dim
    env = make_observation_degradation_env(
        config, ar1_rho=0.7, ar1_sigma=0.02, dropout_prob=0.3
    )
    actions = _action_sequence(10, seed=53)
    frames, _ = _rollout(env, seed=777, actions=actions)
    for t in range(1, len(frames)):
        for slot in range(1, 3):
            reference_t = max(t - slot, 0)
            start = slot * base_dim
            np.testing.assert_array_equal(
                frames[t][start : start + EGO_OBS_DIM],
                frames[reference_t][:EGO_OBS_DIM],
            )


def test_extended_config_round_trips_through_dict() -> None:
    blocks = [
        {"ar1_rho": 0.7, "ar1_sigma": 0.05},
        {"ar1_rho": 0.7, "ar1_sigma": [0.01 * (index + 1) for index in range(EGO_OBS_DIM)]},
        {"dropout_prob": 0.25, "delay_steps": 12},
        {"delay_profile": "episode_random", "delay_lo": 2, "delay_hi": 20},
        {"delay_profile": "piecewise", "delay_lo": 0, "delay_hi": 12, "dropout_prob": 0.1},
    ]
    for block in blocks:
        config = build_env_config({"observation_degradation": block})
        assert build_env_config(env_config_to_dict(config)) == config

    defaults = ObservationDegradationConfig()
    assert defaults.ar1_rho == 0.0
    assert defaults.ar1_sigma == 0.0
    assert defaults.dropout_prob == 0.0
    assert defaults.delay_profile == "constant"
    assert (defaults.delay_lo, defaults.delay_hi) == (0, 0)


def test_merge_env_config_layers_extended_keys() -> None:
    merged = merge_env_config(
        {"observation_degradation": {"delay_steps": 5}},
        {"observation_degradation": {"delay_steps": 0, "delay_profile": "episode_random",
                                      "delay_lo": 1, "delay_hi": 9}},
    )
    assert merged["observation_degradation"] == {
        "delay_steps": 0,
        "delay_profile": "episode_random",
        "delay_lo": 1,
        "delay_hi": 9,
    }
    config = build_env_config(merged)
    assert config.observation_degradation.delay_profile == "episode_random"


def test_substream_constants_are_distinct() -> None:
    assert DROPOUT_SEED_SUBSTREAM != DELAY_PROFILE_SEED_SUBSTREAM
