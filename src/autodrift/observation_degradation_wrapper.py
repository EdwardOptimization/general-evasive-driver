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

Extended degradation modes (WP0, 2026-06). All of them act on ego channels
0-8 only, exactly like delay/noise above, and all are OFF by default. When
every extended parameter is at its default the wrapper executes the original
code path verbatim, so existing (delay_steps, noise_std) configurations are
bit-for-bit unchanged.

- AR(1) correlated noise (``ar1_rho``, ``ar1_sigma``): per-channel process
  ``n_t = ar1_rho * n_{t-1} + ar1_sigma * eps_t`` with ``eps_t ~ N(0, I)``
  drawn from the SAME per-frame main-RNG slot the iid path uses, and the state
  zero-initialized at episode start. ``ar1_sigma`` is the INNOVATION std
  (scalar or length-9 per-channel); the stationary std is
  ``ar1_sigma / sqrt(1 - ar1_rho^2)``. Consequence: with ``ar1_rho = 0`` the
  produced noise is bit-identical to the iid ``noise_std`` path with
  ``noise_std = ar1_sigma``. To keep that equivalence unambiguous,
  ``noise_std`` and ``ar1_sigma`` are mutually exclusive (loud ValueError).
  The AR(1) state advances every frame, including frames later dropped by
  ``dropout_prob`` (the sensor noise process does not pause when a frame is
  lost).
- Frame dropout (``dropout_prob``): every frame after the episode's first is
  dropped independently with probability ``dropout_prob``. A dropped frame
  HOLDS THE LAST DEGRADED VALUE: the ego channels repeat the previous
  timestep's degraded ego vector (so consecutive drops keep holding the last
  delivered value). The episode's first frame (t=0) is never dropped. The
  drop sequence is deterministic per episode, drawn from the substream
  ``[noise_seed_stream, seed_root, episode, 1]`` (disjoint from the noise
  stream, so enabling dropout does not shift the noise draws).
- Time-varying delay (``delay_profile``):
  * ``"constant"`` (default): ``delay_steps`` everywhere — original behavior.
  * ``"episode_random"``: one integer delay drawn uniformly from
    ``[delay_lo, delay_hi]`` at each episode start, constant within the
    episode.
  * ``"piecewise"``: each episode is split into 2-3 segments (segment count,
    cut points, and per-segment delays all seed-derived; adjacent segments get
    different delays from ``[delay_lo, delay_hi]``); within each segment the
    ego channels are bit-identical to a constant-delay wrapper at that
    segment's delay (the raw ring buffer always spans the whole episode).
  Profile draws come from the substream
  ``[noise_seed_stream, seed_root, episode, 2]``; non-constant profiles
  require ``delay_steps == 0``. The realized per-step schedule is exposed as
  ``episode_delay_schedule`` (length ``max_steps + 1``).

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

# Sub-stream tags appended to [noise_seed_stream, seed_root, episode] so each
# extended degradation mode owns an RNG stream disjoint from the noise stream
# (and from each other). The plain noise stream keeps the original 3-element
# derivation, preserving bit-compatibility for existing configurations.
DROPOUT_SEED_SUBSTREAM = 1
DELAY_PROFILE_SEED_SUBSTREAM = 2

DELAY_PROFILES = ("constant", "episode_random", "piecewise")


def _sigma_vector(value: float | tuple | list | np.ndarray, name: str = "noise_std") -> np.ndarray:
    values = np.asarray(value, dtype=np.float64)
    if values.ndim == 0:
        values = np.full(EGO_OBS_DIM, float(values), dtype=np.float64)
    if values.shape != (EGO_OBS_DIM,):
        raise ValueError(
            f"{name} must be a scalar or a length-{EGO_OBS_DIM} per-channel sequence, "
            f"got shape {values.shape}"
        )
    if np.any(values < 0.0) or not np.all(np.isfinite(values)):
        raise ValueError(f"{name} values must be finite and non-negative")
    return values


# Backward-compatible alias (pre-WP0 name).
def _noise_std_vector(noise_std: float | tuple | list | np.ndarray) -> np.ndarray:
    return _sigma_vector(noise_std, "noise_std")


class ObservationDegradationWrapper(gym.Wrapper):
    """Delay and/or add noise to the ego-response channels of AutoDriftEnv."""

    def __init__(
        self,
        env: gym.Env,
        *,
        delay_steps: int = 0,
        noise_std: float | tuple | list | np.ndarray = 0.0,
        noise_seed_stream: int = DEFAULT_NOISE_SEED_STREAM,
        ar1_rho: float = 0.0,
        ar1_sigma: float | tuple | list | np.ndarray = 0.0,
        dropout_prob: float = 0.0,
        delay_profile: str = "constant",
        delay_lo: int = 0,
        delay_hi: int = 0,
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
        self.ar1_rho = float(ar1_rho)
        self.ar1_sigma = _sigma_vector(ar1_sigma, "ar1_sigma")
        self.dropout_prob = float(dropout_prob)
        self.delay_profile = str(delay_profile)
        self.delay_lo = int(delay_lo)
        self.delay_hi = int(delay_hi)

        # Loud validation of the full parameter set; the single source of truth
        # for value/cross-field constraints is ObservationDegradationConfig.
        ObservationDegradationConfig(
            delay_steps=self.delay_steps,
            noise_std=tuple(float(v) for v in self.noise_std),
            noise_seed_stream=self._noise_seed_stream,
            ar1_rho=self.ar1_rho,
            ar1_sigma=tuple(float(v) for v in self.ar1_sigma),
            dropout_prob=self.dropout_prob,
            delay_profile=self.delay_profile,
            delay_lo=self.delay_lo,
            delay_hi=self.delay_hi,
        )
        if self.delay_profile == "piecewise" and int(config.max_steps) < 4:
            raise ValueError(
                "delay_profile 'piecewise' requires max_steps >= 4 to place segment cut points"
            )

        # Extended-mode flag: when False, _degrade runs the original M3214 code
        # path verbatim (structural clean-anchor guarantee).
        self._ar1_active = bool(np.any(self.ar1_sigma > 0.0))
        self._extended = (
            self._ar1_active
            or self.dropout_prob > 0.0
            or self.delay_profile != "constant"
        )

        # Episode seed bookkeeping for deterministic noise derivation.
        self._seed_root = 0
        self._episode_index = -1
        self._rng = np.random.default_rng([self._noise_seed_stream, 0, 0])

        # Extended-mode per-episode state (inert when self._extended is False).
        self._ar1_state = np.zeros(EGO_OBS_DIM, dtype=np.float64)
        self._dropout_rng = np.random.default_rng(
            [self._noise_seed_stream, 0, 0, DROPOUT_SEED_SUBSTREAM]
        )
        # Realized per-step delay schedule for the current episode (length
        # max_steps + 1); None when delay_profile == "constant".
        self.episode_delay_schedule: np.ndarray | None = None

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
        if self._extended:
            self._reset_extended_episode_state()

    def _reset_extended_episode_state(self) -> None:
        """Derive per-episode AR(1)/dropout/delay-profile state from disjoint substreams."""

        self._ar1_state = np.zeros(EGO_OBS_DIM, dtype=np.float64)
        self._dropout_rng = np.random.default_rng(
            [self._noise_seed_stream, self._seed_root, self._episode_index, DROPOUT_SEED_SUBSTREAM]
        )
        if self.delay_profile == "constant":
            self.episode_delay_schedule = None
            return
        delay_rng = np.random.default_rng(
            [
                self._noise_seed_stream,
                self._seed_root,
                self._episode_index,
                DELAY_PROFILE_SEED_SUBSTREAM,
            ]
        )
        horizon = int(self._config.max_steps) + 1  # frames: reset frame + max_steps steps
        if self.delay_profile == "episode_random":
            delay = int(delay_rng.integers(self.delay_lo, self.delay_hi + 1))
            schedule = np.full(horizon, delay, dtype=np.int64)
        else:  # piecewise
            num_segments = int(delay_rng.integers(2, 4))  # 2 or 3 segments
            cut_points = np.sort(
                delay_rng.choice(np.arange(1, horizon), size=num_segments - 1, replace=False)
            )
            delays: list[int] = []
            for _ in range(num_segments):
                value = int(delay_rng.integers(self.delay_lo, self.delay_hi + 1))
                while delays and value == delays[-1]:
                    # adjacent segments must carry different delays; the redraw
                    # loop is deterministic given the substream rng and always
                    # terminates because delay_hi > delay_lo is enforced.
                    value = int(delay_rng.integers(self.delay_lo, self.delay_hi + 1))
                delays.append(value)
            schedule = np.empty(horizon, dtype=np.int64)
            boundaries = [0, *(int(c) for c in cut_points), horizon]
            for segment_index in range(num_segments):
                schedule[boundaries[segment_index] : boundaries[segment_index + 1]] = delays[
                    segment_index
                ]
        self.episode_delay_schedule = schedule

    # -- degradation core -----------------------------------------------------

    def _extended_degraded_value(self) -> np.ndarray:
        """Degraded ego vector at env time self._t for the extended modes.

        Composition order: time-varying delay -> noise (AR(1) or iid; the main
        rng draws exactly one eps per frame, same as the original path) ->
        dropout hold-last-value.
        """

        if self.episode_delay_schedule is None:
            delay_now = self.delay_steps
        else:
            schedule = self.episode_delay_schedule
            delay_now = int(schedule[min(self._t, len(schedule) - 1)])
        delayed_index = max(self._t - delay_now, 0)
        eps = self._rng.normal(0.0, 1.0, EGO_OBS_DIM)
        if self._ar1_active:
            self._ar1_state = self.ar1_rho * self._ar1_state + eps * self.ar1_sigma
            noise = self._ar1_state
        else:
            noise = eps * self.noise_std
        value = self._raw_ego[delayed_index] + noise
        if self.dropout_prob > 0.0:
            # One uniform draw per frame (including t=0) keeps the dropout
            # stream aligned with env time regardless of outcomes.
            dropped = float(self._dropout_rng.uniform()) < self.dropout_prob
            if dropped and self._t > 0:
                value = self._degraded_ego[self._t - 1].copy()
        return value

    def _degrade(self, observation: np.ndarray) -> np.ndarray:
        obs = np.asarray(observation, dtype=np.float32).copy()
        expected = self._base_obs_dim * self._history_length
        if obs.shape != (expected,):
            raise ValueError(f"expected observation shape ({expected},), got {obs.shape}")

        # Frame slot 0 is the newest base frame (env time self._t).
        raw_ego = obs[: EGO_OBS_DIM].astype(np.float64).copy()
        self._raw_ego.append(raw_ego)
        if self._extended:
            self._degraded_ego.append(self._extended_degraded_value())
        else:
            # Original M3214 code path, kept verbatim: constant delay + iid noise.
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
    ar1_rho: float = 0.0,
    ar1_sigma: float | tuple | list | np.ndarray = 0.0,
    dropout_prob: float = 0.0,
    delay_profile: str = "constant",
    delay_lo: int = 0,
    delay_hi: int = 0,
) -> ObservationDegradationWrapper:
    """Build an AutoDriftEnv wrapped as a degraded-observation task family member."""

    return ObservationDegradationWrapper(
        AutoDriftEnv(config),
        delay_steps=delay_steps,
        noise_std=noise_std,
        noise_seed_stream=noise_seed_stream,
        ar1_rho=ar1_rho,
        ar1_sigma=ar1_sigma,
        dropout_prob=dropout_prob,
        delay_profile=delay_profile,
        delay_lo=delay_lo,
        delay_hi=delay_hi,
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
        ar1_rho=degradation.ar1_rho,
        ar1_sigma=degradation.ar1_sigma,
        dropout_prob=degradation.dropout_prob,
        delay_profile=degradation.delay_profile,
        delay_lo=degradation.delay_lo,
        delay_hi=degradation.delay_hi,
    )
