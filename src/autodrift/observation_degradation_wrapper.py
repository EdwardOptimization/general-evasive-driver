"""Observation-degradation task family wrapper for AutoDriftEnv.

This wrapper implements one of the two level-3 design prescriptions from
``docs/self-identification-evidence-discipline.md``: make degraded (delayed or
noisy) current ego response part of the task itself, so that the current frame
is no longer a sufficient statistic of the hidden dynamics and history-based
belief has a chance to be necessary rather than redundant.

Interpretation contract (required by the evidence-discipline rule):

- This wrapper defines a NEW TASK FAMILY. It must be applied identically at
  training time and at evaluation time. It is NOT an evaluation-time
  intervention and it is NOT a change to the deployable actor input contract:
  the actor still receives the same 72-value (or 76-value privileged) frame;
  the task simply provides a sensor stream whose ego-response channels are
  delayed and/or noisy.
- Do not mix this interpretation with eval-only ablations such as
  ``zero_current_response`` in a single claim.

Per-frame obs72 index table (P0 frame, ``action_history_mode="full"``,
``wheel_observation_mode="none"``, 8 road lookahead points, 4 obstacle slots;
see ``AutoDriftEnv._base_observation``):

====== ============================================================ =========
index  channel                                                      degraded
====== ============================================================ =========
0      vx / 20            (body longitudinal velocity)              yes
1      vy / 12            (body lateral velocity)                   yes
2      yaw_rate / 2.5                                               yes
3      ax_body / 15       (IMU-like longitudinal acceleration)      yes
4      ay_body / 15       (IMU-like lateral acceleration)           yes
5      steer / max_steer  (steering actuator state)                 yes
6      steer_rate / max_steer_rate (steering actuator rate)         yes
7      throttle actuator state (drive_force fraction, >=0 branch)   yes
8      brake actuator state (brake_force fraction)                  yes
9-11   previous physical command [steer, throttle, brake]           no
12-27  left road boundary, 8 points x (x/80, y/20) in body frame    no
28-43  right road boundary, 8 points x (x/80, y/20) in body frame   no
44-71  obstacle slots, 4 x [present, x/80, y/20, rel_vx/20,         no
       rel_vy/12, half_width/5, half_width/5]                       no
72-75  optional privileged basic channels                           no
       [mu, mass/mass0, lf/lf0, cr/cr0]
       (only when include_privileged_params=true)
====== ============================================================ =========

Rationale for the degraded set: indices 0-8 are the vehicle's RESPONSE to
commands (the channels a policy could use for current-frame substitution of
hidden-dynamics belief). Indices 9-11 are the policy's OWN previous commands,
which are known instantly on a real vehicle and are therefore never delayed.
Indices 12-71 are scene geometry: the driver can still see the road and the
obstacle perfectly; what is degraded is how clearly the car's own response is
felt. Privileged channels (72-75), when present, are deliberately untouched so
that privileged positive-control policies keep exact hidden-parameter access.

Degradation semantics:

- ``delay_steps=k``: at env time ``t`` the ego-response channels show the raw
  values from time ``t-k`` (clamped to the episode's first frame for
  ``t < k``), implemented with a per-episode ring buffer of raw ego channels.
- ``noise_std``: per-channel i.i.d. Gaussian noise added after the delay. The
  noise RNG is derived deterministically from the episode reset seed (plus an
  episode counter for unseeded resets), so identical seeds and action
  sequences reproduce identical degraded observations bit for bit.
- ``history_length > 1`` (stacked-frame tasks): every stacked frame slot ``j``
  (which corresponds to env time ``max(t-j, 0)``) is rewritten from the same
  degraded per-timestep stream, so the stack stays temporally consistent and
  each frame is degraded exactly once.

Observation shape, dtype, action space, rewards, termination, and info are
unchanged.
"""

from __future__ import annotations

from typing import Any

import gymnasium as gym
import numpy as np

from autodrift.env import AutoDriftEnv, DriftEnvConfig, EGO_OBS_DIM, ObservationDegradationConfig


# Ego response channels degraded by this task family (per stacked frame).
DEGRADED_EGO_RESPONSE_INDICES: tuple[int, ...] = tuple(range(EGO_OBS_DIM))

# Human-readable per-frame index table for the canonical P0 obs72 frame.
OBS72_INDEX_TABLE: dict[str, dict[str, Any]] = {
    "ego_response": {
        "indices": list(range(0, 9)),
        "channels": [
            "vx/20",
            "vy/12",
            "yaw_rate/2.5",
            "ax_body/15",
            "ay_body/15",
            "steer/max_steer",
            "steer_rate/max_steer_rate",
            "throttle_actuator_state",
            "brake_actuator_state",
        ],
        "degraded": True,
    },
    "previous_command": {
        "indices": list(range(9, 12)),
        "channels": ["prev_steer", "prev_throttle", "prev_brake"],
        "degraded": False,
    },
    "road_boundary_left": {"indices": list(range(12, 28)), "degraded": False},
    "road_boundary_right": {"indices": list(range(28, 44)), "degraded": False},
    "obstacle_slots": {"indices": list(range(44, 72)), "degraded": False},
    "privileged_basic_optional": {
        "indices": list(range(72, 76)),
        "channels": ["mu", "mass/mass0", "lf/lf0", "cr/cr0"],
        "degraded": False,
        "present_only_when": "include_privileged_params=true, privileged_observation_mode='basic'",
    },
}

# Fixed stream constant mixed into the noise RNG derivation so the wrapper's
# noise stream cannot collide with the env's own episode RNG stream. The
# single source of truth is the ObservationDegradationConfig default in env.py.
DEFAULT_NOISE_SEED_STREAM = ObservationDegradationConfig().noise_seed_stream


def _noise_std_vector(noise_std: float | tuple | list | np.ndarray) -> np.ndarray:
    values = np.asarray(noise_std, dtype=np.float64)
    if values.ndim == 0:
        values = np.full(EGO_OBS_DIM, float(values), dtype=np.float64)
    if values.shape != (EGO_OBS_DIM,):
        raise ValueError(
            f"noise_std must be a scalar or a length-{EGO_OBS_DIM} per-channel sequence, "
            f"got shape {values.shape}"
        )
    if np.any(values < 0.0) or not np.all(np.isfinite(values)):
        raise ValueError("noise_std values must be finite and non-negative")
    return values


class ObservationDegradationWrapper(gym.Wrapper):
    """Delay and/or add noise to the ego-response channels of AutoDriftEnv."""

    def __init__(
        self,
        env: gym.Env,
        *,
        delay_steps: int = 0,
        noise_std: float | tuple | list | np.ndarray = 0.0,
        noise_seed_stream: int = DEFAULT_NOISE_SEED_STREAM,
    ):
        super().__init__(env)
        base_env = env.unwrapped
        if not isinstance(base_env, AutoDriftEnv):
            raise TypeError("ObservationDegradationWrapper requires an AutoDriftEnv")
        config: DriftEnvConfig = base_env.config
        if config.wheel_observation_mode != "none":
            raise ValueError(
                "ObservationDegradationWrapper only supports wheel_observation_mode='none'; "
                "wheel channels are also ego response evidence and would leak undegraded "
                "current response"
            )
        if int(delay_steps) < 0:
            raise ValueError("delay_steps must be non-negative")

        self._config = config
        self._base_obs_dim = int(base_env.base_obs_dim)
        self._history_length = int(config.history_length)
        self.delay_steps = int(delay_steps)
        self.noise_std = _noise_std_vector(noise_std)
        self._noise_seed_stream = int(noise_seed_stream)

        # Episode seed bookkeeping for deterministic noise derivation.
        self._seed_root = 0
        self._episode_index = -1
        self._rng = np.random.default_rng([self._noise_seed_stream, 0, 0])

        # Per-episode raw/degraded ego-channel streams indexed by env time.
        self._raw_ego: list[np.ndarray] = []
        self._degraded_ego: list[np.ndarray] = []
        self._t = 0

    @property
    def config(self) -> DriftEnvConfig:
        """Expose the base env config (gymnasium wrappers do not forward attributes)."""

        return self._config

    # -- seed / rng -----------------------------------------------------------

    def _derive_episode_rng(self, seed: int | None) -> None:
        if seed is not None:
            self._seed_root = int(seed)
            self._episode_index = 0
        else:
            self._episode_index += 1
        self._rng = np.random.default_rng(
            [self._noise_seed_stream, self._seed_root, self._episode_index]
        )

    # -- degradation core -----------------------------------------------------

    def _degrade(self, observation: np.ndarray) -> np.ndarray:
        obs = np.asarray(observation, dtype=np.float32).copy()
        expected = self._base_obs_dim * self._history_length
        if obs.shape != (expected,):
            raise ValueError(f"expected observation shape ({expected},), got {obs.shape}")

        # Frame slot 0 is the newest base frame (env time self._t).
        raw_ego = obs[: EGO_OBS_DIM].astype(np.float64).copy()
        self._raw_ego.append(raw_ego)
        delayed_index = max(self._t - self.delay_steps, 0)
        noise = self._rng.normal(0.0, 1.0, EGO_OBS_DIM) * self.noise_std
        self._degraded_ego.append(self._raw_ego[delayed_index] + noise)

        for slot in range(self._history_length):
            time_index = max(self._t - slot, 0)
            start = slot * self._base_obs_dim
            obs[start : start + EGO_OBS_DIM] = self._degraded_ego[time_index].astype(np.float32)
        self._t += 1
        return obs

    # -- gym API ---------------------------------------------------------------

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        observation, info = self.env.reset(seed=seed, options=options)
        self._derive_episode_rng(seed)
        self._raw_ego = []
        self._degraded_ego = []
        self._t = 0
        return self._degrade(observation), info

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        observation, reward, terminated, truncated, info = self.env.step(action)
        return self._degrade(observation), reward, terminated, truncated, info


def make_observation_degradation_env(
    config: DriftEnvConfig,
    *,
    delay_steps: int = 0,
    noise_std: float | tuple | list | np.ndarray = 0.0,
    noise_seed_stream: int = DEFAULT_NOISE_SEED_STREAM,
) -> ObservationDegradationWrapper:
    """Build an AutoDriftEnv wrapped as a degraded-observation task family member."""

    return ObservationDegradationWrapper(
        AutoDriftEnv(config),
        delay_steps=delay_steps,
        noise_std=noise_std,
        noise_seed_stream=noise_seed_stream,
    )


def make_env_from_config(config: DriftEnvConfig) -> AutoDriftEnv | ObservationDegradationWrapper:
    """Unified env factory for every training/evaluation/gate entry point.

    When ``config.observation_degradation`` is absent (None) this returns a bare
    ``AutoDriftEnv`` so all existing code paths stay bit-for-bit unchanged.
    When the block is present the env is wrapped in the degraded-response task
    family wrapper, including for the T1/clean cell (delay 0, noise 0), so all
    matrix cells share an identical construction path.
    """

    degradation = config.observation_degradation
    if degradation is None:
        return AutoDriftEnv(config)
    return ObservationDegradationWrapper(
        AutoDriftEnv(config),
        delay_steps=degradation.delay_steps,
        noise_std=degradation.noise_std,
        noise_seed_stream=degradation.noise_seed_stream,
    )
