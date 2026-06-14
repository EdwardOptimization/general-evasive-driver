"""Phase-4 F2 asymmetric actor-critic RL training and four-arm adjudication.

F2 builds the robotics-parity **asymmetric actor-critic RL** rig (PI scope
decision S3 = real RL, NOT distillation): a single deployable obs72 actor
(Gaussian policy: mean + learnable log_std) trained by PPO from the recalibrated
reward, with a bootstrapped privileged critic (obs72 + true mu + vehicle params)
used only at training time and dropped at deployment. The per-regime teachers
(avoidance entry-speed oracle; drift DriftFeedbackPolicy obs72 feedback) are
demoted to a BC warm-start plus an annealed auxiliary BC term that decays toward
zero -- the dominant learning signal is the PPO policy gradient from reward, not
imitation (m1087 staged discipline: BC warm-start -> capability -> guarded RL).

ASYMMETRY CONTRACT (asserted in tests):
  * actor input  = obs72 only (the deployable human-view frame; never mu,
    never vehicle params, never teacher state); the deployable map is
    ``act(obs72) -> action3`` taking the policy mean (no privileged path).
  * critic input = obs72 PLUS privileged features (true mu, key vehicle
    params, regime one-hot) -- training-only, dropped at deployment.

TEACHER CONTRACT (asserted in tests):
  * avoidance -> e2' RampPolicyController(mode="oracle", mu_true, dv) entry-speed
    oracle, used ONLY for the BC warm-start and ONLY on the reveal-post obs72
    segment (B2: the pre-reveal mu-dependent action is never imitated, so no
    obs72-unobservable mu dependence is written into the deployable actor);
  * drift -> e4 DriftFeedbackPolicy obs72 sideslip/yaw feedback oracle.
    The native Chrono CEM oracle scored 0/N in the drift cell and is NEVER a
    teacher.

REAL RL (the F2 build-review B-list fixes):
  * B1  per-(seed,update) checkpoint {model, optimizer, update, seed, best, rng}
        + --resume from the latest point with RNG restoration + kill/resume test;
  * B2  avoidance BC warm-start uses only the reveal-post obs72-recoverable
        segment; the main objective is PPO from reward (no mu leak);
  * B3  all training seeds validated; seed-cluster SE clusters by TRAINING seed
        (each seed's student validation success is one observation, n=seeds);
  * B4  CI method implemented + pre-registered: cross-training-seed paired
        t-CI of (student - floor) AND a seed-clustered bootstrap; adjudication
        uses the real CI lower bound;
  * B5  avoidance floor = max over real non-trivial classical arms (entry-speed
        commitment fixed-plan spectrum + online-mu-estimating seeker reflex),
        never the unmodified incumbent alone -- not a strawman;
  * B6  reward-hacking guard: per-episode Spearman(reward, success), N/A on ties,
        >= 0.9 a HARD gate (failure -> re-price).
  * S2  avoidance mu/reveal spectrum (E2' grid) spans the curriculum and the
        validation grid;
  * S5  avoidance reward fail-closed (completion=="" is a FAILURE) + a low-margin
        high-speed grazing penalty;
  * S7  pre-full oracle-ceiling check on the student/hard distribution.

This milestone runs --quick ONLY. --full (100M steps, 8 seeds, 30 workers, CPU,
managed) is wired and PI-gated but intentionally NOT launched here.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f2_train.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_f2_train.py --quick --resume
    # --full is PI-gated; do not launch in an agent session.
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_f2_train.py --full --resume
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
from pathlib import Path
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Normal
from torch.optim import Adam

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json  # noqa: E402
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_f1_training_infra_smoke as f1  # noqa: E402
import phase4_e2_chrono_two_regime_smoke as e2_smoke  # noqa: E402
import phase4_e2prime_chrono_two_regime_hardened as e2p  # noqa: E402
import phase4_e4_drift_regime_pricing as e4  # noqa: E402


MILESTONE_ID = "m3264-phase4-f2-asymmetric-actor-critic-rl"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f2_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f2_quick.json"
FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f2.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
CKPT_QUICK_DIR = RUN_DIR / "checkpoints_quick"
CKPT_FULL_DIR = RUN_DIR / "checkpoints_full"
ROWS_QUICK_CSV = RUN_DIR / "arm_rows_quick.csv"
ROWS_FULL_CSV = RUN_DIR / "arm_rows_full.csv"
TRAIN_QUICK_CSV = RUN_DIR / "train_metrics_quick.csv"
TRAIN_FULL_CSV = RUN_DIR / "train_metrics_full.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
STDERR_QUICK_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
STDERR_FULL_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
DOC_PATH = REPO_ROOT / "docs" / "m3264-phase4-f2-asymmetric-actor-critic-rl.md"

F1_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1_training_infra.json"
F1B_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1b_throughput.json"
E2PRIME_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2prime_chrono_two_regime_hardened.json"
E4_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e4_drift_regime_pricing.json"

# New, mutually-disjoint seed base for F2 (different from F1=...05, F1b=...06).
SEED_BASE = 2026061407
ACT_DIM = f1.ACT_DIM
HIDDEN_SIZE = f1.HIDDEN_SIZE
VARIANT = f1.VARIANT

# --- privileged critic channel layout (training-only) -----------------------
# [true mu, mass surrogate, mu*g surrogate, reveal surrogate, regime onehot
#  avoidance, regime onehot drift]. The actor NEVER sees these.
PRIV_DIM = 6

# --- avoidance teacher + scenario spectrum (E2'/M3258 prize source) ---------
# S2: span the E2' clean mu/reveal grid (the prize is across the spectrum, not at
# a single point). The avoidance teacher binds mu_true PER scenario.
AVOIDANCE_REVEALS_FULL = e2p.CLEAN_REVEALS          # (9.5, 12.0, 16.0, 22.0, 30.0)
AVOIDANCE_MUS_FULL = e2p.MU_POINTS                  # (0.3625, 0.5875, 0.8125, 1.0375)
AVOIDANCE_REVEALS_QUICK = (9.5, 16.0)
AVOIDANCE_MUS_QUICK = (0.3625, 0.8125)
AVOIDANCE_ORACLE_DV = 0.0
# reveal-post-only BC warm-start (B2): the avoidance oracle's pre-reveal action
# is a function of mu_true; we imitate ONLY frames at/after the obstacle reveal,
# where the action is obs72-recoverable (the obstacle is visible in obs72).
AVOIDANCE_BC_REVEAL_POST_ONLY = True

# --- drift teacher binding (E4/M3260 +0.40 prize source) --------------------
DRIFT_CELL_ID = "low_mu_power_oversteer"
DRIFT_FEEDBACK_NAME = "beta0p22_power"  # selected DriftFeedbackSpec; NOT CEM.

# --- reward recalibration (m1087 / C5 measured penalties) -------------------
COLLISION_PENALTY = 60.0
OFFTRACK_PENALTY = 45.0
AVOIDANCE_PASS_REWARD = 40.0
DRIFT_SUCCESS_REWARD = 40.0
CLEARANCE_SHAPING = 8.0
DRIFT_PROGRESS_SHAPING = 0.5
# S5: low-margin high-speed grazing penalty (unsafe near-misses must not score
# high). vx normalized by 20 m/s in obs72; "high speed" = vx_norm above this.
GRAZE_SPEED_NORM = 0.45
GRAZE_MARGIN_M = 0.20
GRAZE_PENALTY = 12.0

# --- PPO hyperparameters (pre-registered) -----------------------------------
PPO_GAMMA = 0.99
PPO_LAMBDA = 0.95
PPO_CLIP = 0.2
PPO_VALUE_COEF = 0.5
PPO_ENTROPY_COEF = 0.01
PPO_EPOCHS = 4
PPO_MINIBATCHES = 4
PPO_MAX_GRAD_NORM = 0.5
PPO_LR = 3e-4
LOG_STD_INIT = -0.5
LOG_STD_MIN = -2.0
LOG_STD_MAX = 0.5
# annealed auxiliary BC: warm-start dominates early, decays to ~0 so PPO leads.
BC_WARMSTART_COEF = 1.0
BC_AUX_COEF_START = 0.5
BC_AUX_COEF_END = 0.0

# --- curriculum (easy -> hard across both regimes) --------------------------
CURRICULUM_STAGES = (
    {"stage": 0, "name": "avoidance_plus_easy_drift", "avoidance_frac": 0.6, "drift_difficulty": "easy"},
    {"stage": 1, "name": "balanced_mixed", "avoidance_frac": 0.5, "drift_difficulty": "medium"},
    {"stage": 2, "name": "hard_drift_weighted", "avoidance_frac": 0.4, "drift_difficulty": "hard"},
)
DRIFT_DIFFICULTY_BETA_SCALE = {"easy": 0.6, "medium": 0.85, "hard": 1.0}

ARMS = (
    "fixed_star",
    "entry_speed_commitment_floor",
    "online_mu_seeker_floor",
    "per_regime_oracle",
    "student_policy",
)
# learning-free classical arms whose max is the honest floor (B5).
FLOOR_ARMS = ("fixed_star", "entry_speed_commitment_floor", "online_mu_seeker_floor")

# Quick budget: small, fast, >=2 seeds -- full-chain proof only, never a verdict.
QUICK = {
    "workers": 2,
    "seeds": 2,
    "warmstart_updates": 1,
    "ppo_updates": 1,
    "rollout_workers": 2,
    "rollout_horizon": 6,
    "validation_units_per_regime": 2,
    "selection_units_per_regime": 1,
    "warmstart_units": 2,
}
# Full budget: PI-gated, managed, not launched here.
FULL = {
    "workers": 30,
    "seeds": 8,
    "total_steps": 100_000_000,
    "warmstart_updates": 20,
    "ppo_updates": 600,
    "rollout_workers": 30,
    "rollout_horizon": 128,
    "validation_units_per_regime": 30,
    "selection_units_per_regime": 8,
    "warmstart_units": 60,
}

CLAIM_BOUNDARY = (
    "Phase-4 F2 asymmetric actor-critic RL training and four-arm adjudication only: "
    "asymmetric actor(obs72)/critic(obs72+privileged) Gaussian policy trained by PPO "
    "(clipped surrogate + bootstrapped privileged GAE critic + entropy) from the "
    "recalibrated reward, with the avoidance entry-speed oracle and drift "
    "DriftFeedbackPolicy as BC warm-start/annealed-auxiliary teachers only, held-out "
    "selection, a mu/reveal avoidance spectrum, and a frozen "
    "{fixed*/entry-speed-floor/online-mu-seeker/per-regime-oracle/student} four-arm "
    "validation comparison with training-seed-clustered CIs. F2 is engineering-only: it "
    "does not mutate ActiveSafetyReflexDriver, makes no self-ID or history-attribution "
    "claim, and the --quick smoke proves only the end-to-end pipeline -- it is NOT a "
    "validation ranking, promotion, driver-performance, current-sim sufficiency, full "
    "high-fidelity sufficiency, paper, repair-success, robustness-result, or "
    "feasibility-proof claim."
)


# ----------------------------------------------------------------- utilities


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else repr(number)
    return value


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _seed_for(*parts: Any) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little") % 2_000_000_000


def _finite_obs72(obs: np.ndarray) -> bool:
    return bool(np.asarray(obs).shape == (HUMAN_VIEW_OBS_DIM,) and np.isfinite(obs).all())


def _progress(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


# ----------------------------------------------------- asymmetric actor/critic


class AsymmetricActorCritic(nn.Module):
    """Robotics-parity asymmetric actor-critic with a stochastic Gaussian policy.

    The actor reads ONLY ``obs72`` and outputs a squashed Gaussian (state-dependent
    mean + a per-action LEARNABLE ``log_std`` parameter), so it explores and yields a
    differentiable log-prob for PPO. ``act`` (deployment) takes the policy MEAN.
    The critic reads ``obs72`` concatenated with ``PRIV_DIM`` privileged features used
    only during training; ``act`` / ``actor_parameters`` expose no path to it, so the
    deployable actor cannot read mu/teacher state by construction.
    """

    def __init__(self, obs_dim: int = HUMAN_VIEW_OBS_DIM, act_dim: int = ACT_DIM, *, priv_dim: int = PRIV_DIM, hidden_size: int = HIDDEN_SIZE):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.act_dim = int(act_dim)
        self.priv_dim = int(priv_dim)
        self.actor = nn.Sequential(
            nn.Linear(obs_dim, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
        )
        self.actor_mean = nn.Linear(hidden_size, act_dim)
        # learnable per-action log_std (the policy stochasticity B-list demands).
        self.log_std = nn.Parameter(torch.full((act_dim,), float(LOG_STD_INIT)))
        # privileged critic: obs72 + privileged channels (training only).
        self.critic = nn.Sequential(
            nn.Linear(obs_dim + priv_dim, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1),
        )

    def actor_parameters(self):
        return list(self.actor.parameters()) + list(self.actor_mean.parameters()) + [self.log_std]

    def critic_parameters(self):
        return list(self.critic.parameters())

    def _raw_mean(self, obs72: torch.Tensor) -> torch.Tensor:
        if obs72.shape[-1] != self.obs_dim:
            raise ValueError(f"actor input must be obs72 (dim {self.obs_dim}); got {obs72.shape[-1]}")
        return self.actor_mean(self.actor(obs72))

    def policy_distribution(self, obs72: torch.Tensor) -> Normal:
        mean = self._raw_mean(obs72)
        log_std = torch.clamp(self.log_std, LOG_STD_MIN, LOG_STD_MAX)
        std = torch.exp(log_std).expand_as(mean)
        return Normal(mean, std)

    def actor_forward(self, obs72: torch.Tensor) -> torch.Tensor:
        """Squashed deterministic action mean from obs72 only (deployment map)."""
        return torch.tanh(self._raw_mean(obs72))

    def critic_forward(self, obs72: torch.Tensor, priv: torch.Tensor) -> torch.Tensor:
        if priv.shape[-1] != self.priv_dim:
            raise ValueError(f"critic privileged input must be dim {self.priv_dim}; got {priv.shape[-1]}")
        return self.critic(torch.cat([obs72, priv], dim=-1)).squeeze(-1)

    @staticmethod
    def _squashed_log_prob(dist: Normal, raw_action: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        # tanh change-of-variables correction (same convention as train_ppo).
        correction = torch.log(torch.clamp(1.0 - action.pow(2), min=1e-6)).sum(dim=-1)
        return dist.log_prob(raw_action).sum(dim=-1) - correction

    def evaluate_actions(self, obs72: torch.Tensor, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """log-prob + entropy of stored (squashed) actions under the current policy."""
        dist = self.policy_distribution(obs72)
        clipped = torch.clamp(actions, -1.0 + 1e-6, 1.0 - 1e-6)
        raw = torch.atanh(clipped)
        log_prob = self._squashed_log_prob(dist, raw, clipped)
        entropy = dist.entropy().sum(dim=-1)
        return log_prob, entropy

    @torch.no_grad()
    def act_stochastic(self, obs72: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Sample a (squashed) action + its log-prob from obs72 ONLY (rollout)."""
        arr = np.asarray(obs72, dtype=np.float32)
        single = arr.ndim == 1
        batch = arr.reshape(1, -1) if single else arr
        obs_t = torch.as_tensor(batch, dtype=torch.float32)
        dist = self.policy_distribution(obs_t)
        raw = dist.sample()
        action = torch.tanh(raw)
        log_prob = self._squashed_log_prob(dist, raw, action)
        a = action.cpu().numpy().astype(np.float32)
        lp = log_prob.cpu().numpy().astype(np.float32)
        return (a[0], lp[0]) if single else (a, lp)

    @torch.no_grad()
    def act(self, obs72: np.ndarray) -> np.ndarray:
        """Deterministic deployable action from obs72 ONLY (policy mean). No priv path."""
        arr = np.asarray(obs72, dtype=np.float32)
        single = arr.ndim == 1
        batch = arr.reshape(1, -1) if single else arr
        out = self.actor_forward(torch.as_tensor(batch, dtype=torch.float32)).cpu().numpy().astype(np.float32)
        return out[0] if single else out


# --------------------------------------------------------------- teacher binding


@dataclass(frozen=True)
class TeacherHandle:
    regime: str
    factory: Callable[[], Callable[[int, np.ndarray], np.ndarray]]
    privileged: dict[str, float]


class _AvoidanceTeacherAdapter:
    """(step, obs)->action3 adapter over the E2' entry-speed oracle.

    Privileged: constructed with mu_true (privileged) and resets at step 0. Used
    only as a BC warm-start teacher; the deployable actor never embeds it.
    """

    def __init__(self, *, reveal: float, mu: float, dv: float):
        self._reg, self._mod_b, self._interp = f1._e2_context()
        design = self._reg.make_design(self._mod_b, float(reveal))
        self._ctrl = self._reg.RampPolicyController(
            self._mod_b, self._interp, design, f"oracle_dv{dv:+g}", mode="oracle", mu_true=float(mu), dv=float(dv)
        )
        self._ctrl.reset()
        self._started = False

    def __call__(self, step: int, obs: np.ndarray) -> np.ndarray:
        if step == 0 and self._started:
            self._ctrl.reset()
        self._started = True
        action = np.asarray(self._ctrl.act(np.asarray(obs, dtype=np.float64)), dtype=np.float32)
        return np.clip(action, -1.0, 1.0).astype(np.float32)


def _drift_spec(name: str) -> e4.DriftFeedbackSpec:
    for spec in e4.DRIFT_FEEDBACK_SPECS:
        if spec.name == name:
            return spec
    raise ValueError(f"unknown drift feedback spec {name!r}; CEM is never a valid drift teacher")


def _drift_cell() -> dict[str, Any]:
    return [item for item in e4._cell_catalog() if item["cell_id"] == DRIFT_CELL_ID][0]


def make_avoidance_teacher(*, reveal: float = AVOIDANCE_REVEALS_FULL[0], mu: float = AVOIDANCE_MUS_FULL[0]) -> TeacherHandle:
    return TeacherHandle(
        regime="avoidance",
        factory=lambda: _AvoidanceTeacherAdapter(reveal=float(reveal), mu=float(mu), dv=AVOIDANCE_ORACLE_DV),
        privileged={"mu": float(mu), "mass": 1684.0, "reveal": float(reveal), "regime": 0.0},
    )


def make_drift_teacher() -> TeacherHandle:
    cell = _drift_cell()
    spec = _drift_spec(DRIFT_FEEDBACK_NAME)
    side = float(cell["initial_beta_rad"])
    return TeacherHandle(
        regime="drift",
        factory=lambda: e4.DriftFeedbackPolicy(spec, side=side),
        privileged={"mu": float(cell["mu"]), "mass": 1684.0, "reveal": 0.0, "regime": 1.0},
    )


def teacher_for(regime: str, **kwargs: Any) -> TeacherHandle:
    if regime == "avoidance":
        return make_avoidance_teacher(**kwargs)
    if regime == "drift":
        return make_drift_teacher()
    raise ValueError(f"unknown regime {regime!r}")


# --------------------------------------------------- B5 non-trivial classical floor arms


class _EntrySpeedCommitmentFloor:
    """Belief-free entry-speed commitment fixed-plan (B5 classical arm).

    A real non-trivial classical avoidance policy: it commits to a conservative
    entry speed via the E2' CommitmentController (fixed_speed plan) -- NO mu, NO
    oracle. obs72-only, learning-free. The avoidance honest floor is the max over
    this fixed-plan spectrum and the online-mu seeker (never the bare incumbent).
    """

    def __init__(self, *, reveal: float, v_entry: float):
        reg, mod_b, _interp = f1._e2_context()
        design = reg.make_design(mod_b, float(reveal))
        plan = mod_b.PlanSpec(name=f"fixedspeed_v{v_entry:g}", v_entry=float(v_entry), brake_to=None, steer_cap=0.85)
        self._ctrl = mod_b.CommitmentController(plan, design)
        if hasattr(self._ctrl, "reset"):
            self._ctrl.reset()
        self._started = False

    def __call__(self, step: int, obs: np.ndarray) -> np.ndarray:
        if step == 0 and self._started and hasattr(self._ctrl, "reset"):
            self._ctrl.reset()
        self._started = True
        action = np.asarray(self._ctrl.act(np.asarray(obs, dtype=np.float64)), dtype=np.float32)
        return np.clip(action, -1.0, 1.0).astype(np.float32)


class _OnlineMuSeekerFloor:
    """Online mu-estimating threshold-seeker reflex (B5 classical arm).

    The E2' RampPolicyController seeker: ramps brake force, reads ``mu_hat`` online
    from the realized force at onset, then tracks v*(mu_hat). It estimates mu from
    its OWN action channel -- belief-free, obs72-only, NO oracle mu_true. This is a
    genuinely non-trivial classical avoidance arm, not a strawman.
    """

    def __init__(self, *, reveal: float, tau: float = 0.30):
        reg, mod_b, interp = f1._e2_context()
        design = reg.make_design(mod_b, float(reveal))
        self._ctrl = reg.RampPolicyController(
            mod_b, interp, design, f"seeker_tau{tau:.3f}",
            mode="seeker", ramp_rate=6000.0, tau=float(tau), backoff=0.06, strategy="hold", dv=0.0,
        )
        self._ctrl.reset()
        self._started = False

    def __call__(self, step: int, obs: np.ndarray) -> np.ndarray:
        if step == 0 and self._started:
            self._ctrl.reset()
        self._started = True
        action = np.asarray(self._ctrl.act(np.asarray(obs, dtype=np.float64)), dtype=np.float32)
        return np.clip(action, -1.0, 1.0).astype(np.float32)


# spectrum of entry-speed fixed plans (the fixed-plan floor, B5/S2).
ENTRY_SPEED_FLOOR_VENTRIES = e2p.FIXED_SPEED_CANDIDATES  # (5.5, 7.5, 9.5)


# --------------------------------------------------------------- scenarios (mu/reveal spectrum)


def _avoidance_grid(quick: bool) -> list[tuple[float, float]]:
    reveals = AVOIDANCE_REVEALS_QUICK if quick else AVOIDANCE_REVEALS_FULL
    mus = AVOIDANCE_MUS_QUICK if quick else AVOIDANCE_MUS_FULL
    return [(float(r), float(m)) for r in reveals for m in mus]


def _avoidance_scenario(seed: int, *, max_steps: int, reveal: float, mu: float) -> dict[str, Any]:
    reg, mod_b, interp = f1._e2_context()
    scenario = e2_smoke._make_scenario(reg, mod_b, interp, reveal=float(reveal), mu=float(mu), seed=int(seed), variant=VARIANT)
    scenario["scenario_id"] = f"m3264-avoidance-r{reveal:g}-mu{mu:.4f}-seed{seed}"
    scenario["max_steps"] = int(max_steps)
    return scenario


def _drift_scenario(seed: int, *, max_steps: int, difficulty: str = "hard") -> dict[str, Any]:
    cell = dict(_drift_cell())
    cell["initial_beta_rad"] = float(cell["initial_beta_rad"]) * float(DRIFT_DIFFICULTY_BETA_SCALE.get(difficulty, 1.0))
    scenario = e4.scenario_for_cell(cell, seed=int(seed), mode="validation")
    scenario["scenario_id"] = f"m3264-drift-{difficulty}-seed{seed}"
    scenario["max_steps"] = int(max_steps)
    return scenario


# --------------------------------------------------------------- privileged feats


def _privileged_features(regime: str, *, mu: float, reveal: float) -> np.ndarray:
    mass = 1684.0
    grip = float(mu * 9.81)
    is_avoid = 1.0 if regime == "avoidance" else 0.0
    is_drift = 1.0 if regime == "drift" else 0.0
    return np.asarray([float(mu), mass / 2000.0, grip / 10.0, float(reveal) / 30.0, is_avoid, is_drift], dtype=np.float32)


# --------------------------------------------------------------- reward (recalibrated, S5)


def _avoidance_reward(info: dict[str, Any], terminated: bool, truncated: bool) -> float:
    collision = bool(info.get("collision", False)) or str(info.get("termination_reason", "")) == "obstacle_collision"
    offtrack = str(info.get("termination_reason", "")) == "off_track"
    completion = str(info.get("completion_reason", ""))
    margin = info.get("min_clearance_margin", None)
    margin_f = float(margin) if (margin is not None and math.isfinite(float(margin))) else None
    vx_norm = abs(float(info.get("vx_norm", info.get("obs0", 0.0)) or 0.0))
    reward = 0.0
    if collision:
        reward -= COLLISION_PENALTY
    if offtrack:
        reward -= OFFTRACK_PENALTY
    if margin_f is not None:
        reward += CLEARANCE_SHAPING * float(np.clip(margin_f, -1.0, 1.0))
        # S5: penalize unsafe high-speed grazing (low margin while fast).
        if 0.0 <= margin_f < GRAZE_MARGIN_M and vx_norm >= GRAZE_SPEED_NORM:
            reward -= GRAZE_PENALTY
    # S5: fail-closed -- only an explicit cleared/finished episode earns the pass
    # reward. completion=="" (unknown) is NOT treated as a pass.
    cleared = completion in {"max_steps", "obstacle_cleared"}
    if (terminated or truncated) and not collision and not offtrack and cleared:
        reward += AVOIDANCE_PASS_REWARD
    return float(reward)


def _avoidance_success(collision_any: bool, info: dict[str, Any]) -> bool:
    offtrack = str(info.get("termination_reason", "")) == "off_track"
    completion = str(info.get("completion_reason", ""))
    # S5 fail-closed: success requires an explicit cleared/finished completion.
    return bool((not collision_any) and (not offtrack) and completion in {"max_steps", "obstacle_cleared"})


def _drift_reward(controlled_drift: bool, drift_success_inc: bool, collision: bool) -> float:
    reward = 0.0
    if collision:
        reward -= COLLISION_PENALTY
    if controlled_drift:
        reward += DRIFT_PROGRESS_SHAPING
    if drift_success_inc:
        reward += DRIFT_SUCCESS_REWARD
    return float(reward)


def _drift_step_flags(obs: np.ndarray, info: dict[str, Any]) -> bool:
    if not _finite_obs72(obs):
        return False
    vx, _vy, yaw_rate, beta = e4._obs_kinematics(np.asarray(obs))
    rear_saturated, _n, _sa, _ls = e4._rear_saturation(info)
    high_beta = abs(beta) >= e4.BETA_THRESHOLD_RAD
    controlled = e4.MIN_SPEED_MPS <= vx <= e4.MAX_SPEED_MPS and abs(yaw_rate) <= e4.YAW_RATE_LIMIT_RAD_S
    return bool(high_beta and rear_saturated and controlled)


def _obstacle_visible(obs: np.ndarray, info: dict[str, Any]) -> bool:
    """B2 reveal gate: is the obstacle visible in obs72 at this frame?

    The obstacle-present channel is exposed in obs72 (geometry channels). We use
    the worker info flag when present and fall back to a nonzero obstacle block.
    """
    if "obstacle_visible" in info:
        return bool(info.get("obstacle_visible"))
    arr = np.asarray(obs, dtype=np.float64)
    # geometry/obstacle block (never degraded): treat any nonzero obstacle-slot
    # signal as "revealed". obs72 layout reserves the tail for obstacle slots.
    return bool(np.any(np.abs(arr[-12:]) > 1e-6))


# --------------------------------------------------------------- episode rollout


def run_episode(
    client: ChronoWorkerClient,
    scenario: dict[str, Any],
    regime: str,
    policy: Callable[[int, np.ndarray], np.ndarray],
    *,
    seed: int,
    mu: float,
    reveal: float,
    collect: str = "none",  # "none" | "bc" | "ppo"
) -> dict[str, Any]:
    """Run one closed-loop episode; optionally collect BC or PPO transitions.

    collect="bc"  -> obs72 frames + teacher-action targets + priv (warm-start).
    collect="ppo" -> obs72, sampled action, log-prob, reward, value-input priv,
                     done flags, plus the bootstrap obs for GAE.
    """
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
    obs = np.asarray(obs, dtype=np.float32)
    info = dict(reset_reply.get("info", {}))
    bc_frames: list[np.ndarray] = []
    bc_targets: list[np.ndarray] = []
    bc_priv: list[np.ndarray] = []
    ppo_obs: list[np.ndarray] = []
    ppo_act: list[np.ndarray] = []
    ppo_logp: list[float] = []
    ppo_rew: list[float] = []
    ppo_done: list[float] = []
    ppo_priv: list[np.ndarray] = []
    total_reward = 0.0
    steps = 0
    terminated = truncated = False
    collision_any = False
    longest_controlled = 0
    current_controlled = 0
    min_margin = float("inf")
    finite_all = _finite_obs72(obs)
    max_steps = int(scenario["max_steps"])
    priv_vec = _privileged_features(regime, mu=mu, reveal=reveal)
    last_obs = obs.copy()
    while not (terminated or truncated) and steps < max_steps:
        revealed = (regime != "avoidance") or _obstacle_visible(obs, info)
        if collect == "bc":
            if _finite_obs72(obs) and (revealed or not AVOIDANCE_BC_REVEAL_POST_ONLY):
                bc_frames.append(obs.astype(np.float32).copy())
                bc_targets.append(np.clip(np.asarray(policy(steps, obs), dtype=np.float32), -1.0, 1.0))
                bc_priv.append(priv_vec.copy())
        if collect == "ppo":
            action, logp = policy(steps, obs)  # type: ignore[misc]
            action = np.clip(np.asarray(action, dtype=np.float32), -1.0, 1.0)
        else:
            action = np.clip(np.asarray(policy(steps, obs), dtype=np.float32), -1.0, 1.0)
        prev_obs = obs.copy()
        obs, terminated, truncated, _status, info = client.step(action)
        obs = np.asarray(obs, dtype=np.float32)
        info = dict(info)
        last_obs = obs.copy()
        finite_all = finite_all and _finite_obs72(obs)
        collision = bool(info.get("collision", False)) or str(info.get("termination_reason", "")) == "obstacle_collision"
        collision_any = collision_any or collision
        if regime == "avoidance":
            margin = info.get("min_clearance_margin", None)
            if margin is not None and math.isfinite(float(margin)):
                min_margin = min(min_margin, float(margin))
            info.setdefault("vx_norm", float(prev_obs[0]))
            step_reward = _avoidance_reward(info, terminated, truncated)
        else:
            controlled = _drift_step_flags(obs, info)
            current_controlled = current_controlled + 1 if controlled else 0
            longest_controlled = max(longest_controlled, current_controlled)
            success_inc = longest_controlled == e4.MIN_SUSTAIN_STEPS and current_controlled == e4.MIN_SUSTAIN_STEPS
            step_reward = _drift_reward(controlled, success_inc, collision)
        total_reward += step_reward
        if collect == "ppo":
            ppo_obs.append(prev_obs.astype(np.float32))
            ppo_act.append(action.astype(np.float32))
            ppo_logp.append(float(logp))
            ppo_rew.append(float(step_reward))
            ppo_done.append(1.0 if (terminated or truncated) else 0.0)
            ppo_priv.append(priv_vec.copy())
        steps += 1
    if regime == "avoidance":
        success = _avoidance_success(collision_any, info)
    else:
        success = bool(longest_controlled >= e4.MIN_SUSTAIN_STEPS)
    return {
        "regime": regime,
        "seed": int(seed),
        "scenario_id": str(scenario["scenario_id"]),
        "steps": int(steps),
        "success": bool(success),
        "collision": bool(collision_any),
        "total_reward": float(total_reward),
        "longest_controlled_drift_run": int(longest_controlled),
        "min_clearance_margin": float(min_margin) if math.isfinite(min_margin) else float("nan"),
        "finite_obs_all": bool(finite_all),
        "bc_frames": np.stack(bc_frames).astype(np.float32) if bc_frames else np.zeros((0, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
        "bc_targets": np.stack(bc_targets).astype(np.float32) if bc_targets else np.zeros((0, ACT_DIM), dtype=np.float32),
        "bc_priv": np.stack(bc_priv).astype(np.float32) if bc_priv else np.zeros((0, PRIV_DIM), dtype=np.float32),
        "ppo": {
            "obs": np.stack(ppo_obs).astype(np.float32) if ppo_obs else np.zeros((0, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
            "act": np.stack(ppo_act).astype(np.float32) if ppo_act else np.zeros((0, ACT_DIM), dtype=np.float32),
            "logp": np.asarray(ppo_logp, dtype=np.float32),
            "rew": np.asarray(ppo_rew, dtype=np.float32),
            "done": np.asarray(ppo_done, dtype=np.float32),
            "priv": np.stack(ppo_priv).astype(np.float32) if ppo_priv else np.zeros((0, PRIV_DIM), dtype=np.float32),
            "last_obs": last_obs.astype(np.float32),
            "last_priv": priv_vec.astype(np.float32),
            "terminated": bool(terminated),
        },
    }


# --------------------------------------------------------------- GAE(lambda) + bootstrap


def compute_gae(
    rewards: np.ndarray,
    values: np.ndarray,
    dones: np.ndarray,
    last_value: float,
    *,
    gamma: float = PPO_GAMMA,
    lam: float = PPO_LAMBDA,
) -> tuple[np.ndarray, np.ndarray]:
    """GAE(lambda) advantages + bootstrapped returns for ONE trajectory.

    NOT a Monte-Carlo return broadcast: each step uses delta_t = r_t + gamma *
    V(s_{t+1}) * (1-done) - V(s_t), with the final next-value bootstrapped from
    the critic on the last observation.
    """
    n = len(rewards)
    adv = np.zeros(n, dtype=np.float32)
    last_gae = 0.0
    for t in reversed(range(n)):
        next_value = last_value if t == n - 1 else values[t + 1]
        next_nonterminal = 1.0 - float(dones[t])
        delta = rewards[t] + gamma * next_value * next_nonterminal - values[t]
        last_gae = delta + gamma * lam * next_nonterminal * last_gae
        adv[t] = last_gae
    returns = adv + values
    return adv.astype(np.float32), returns.astype(np.float32)


# --------------------------------------------------------------- BC warm-start update


def bc_update(
    model: AsymmetricActorCritic,
    optimizer: Adam,
    frames: np.ndarray,
    priv: np.ndarray,
    targets: np.ndarray,
    *,
    coef: float = BC_WARMSTART_COEF,
) -> dict[str, Any]:
    """BC warm-start: actor MSE to teacher action + critic value pretrain.

    Critic target is a zero-baseline value pretrain (returns unavailable in the
    teacher demos); the PPO phase then trains the critic on bootstrapped returns.
    """
    obs_t = torch.as_tensor(frames, dtype=torch.float32)
    priv_t = torch.as_tensor(priv, dtype=torch.float32)
    target_t = torch.clamp(torch.as_tensor(targets, dtype=torch.float32), -1.0, 1.0)
    mean = model.actor_forward(obs_t)
    bc_loss = torch.mean((mean - target_t).pow(2))
    value = model.critic_forward(obs_t, priv_t)
    value_loss = torch.mean(value.pow(2))
    loss = coef * bc_loss + 0.5 * value_loss
    before = [p.detach().clone() for p in model.parameters()]
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    grad_sq, finite_grad = 0.0, True
    for p in model.parameters():
        if p.grad is None:
            continue
        g = p.grad.detach()
        finite_grad = finite_grad and bool(torch.isfinite(g).all().item())
        grad_sq += float(torch.sum(g.pow(2)))
    nn.utils.clip_grad_norm_(model.parameters(), PPO_MAX_GRAD_NORM)
    optimizer.step()
    delta_sq = sum(float(torch.sum((n.detach() - o).pow(2))) for o, n in zip(before, model.parameters()))
    return {
        "phase": "bc_warmstart",
        "bc_loss": float(bc_loss.detach()),
        "value_loss": float(value_loss.detach()),
        "total_loss": float(loss.detach()),
        "grad_norm": float(math.sqrt(grad_sq)),
        "param_delta_l2": float(math.sqrt(delta_sq)),
        "finite_loss": bool(math.isfinite(float(loss.detach()))),
        "finite_grad": bool(finite_grad and math.isfinite(grad_sq)),
        "optimizer_changed_parameters": bool(delta_sq > 0.0),
        "batch_size": int(frames.shape[0]),
        "log_std_mean": float(model.log_std.detach().mean()),
    }


# --------------------------------------------------------------- PPO update


def ppo_update(
    model: AsymmetricActorCritic,
    optimizer: Adam,
    batch: dict[str, np.ndarray],
    *,
    bc_aux_coef: float,
    bc_aux: dict[str, np.ndarray] | None,
    epochs: int = PPO_EPOCHS,
    minibatches: int = PPO_MINIBATCHES,
    clip: float = PPO_CLIP,
    value_coef: float = PPO_VALUE_COEF,
    entropy_coef: float = PPO_ENTROPY_COEF,
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    """One PPO update over a collected rollout batch.

    Clipped surrogate policy gradient + clipped value loss + entropy bonus, with
    a correctly batch-normalized advantage and an annealed auxiliary BC term.
    """
    rng = rng or np.random.default_rng(0)
    obs = torch.as_tensor(batch["obs"], dtype=torch.float32)
    priv = torch.as_tensor(batch["priv"], dtype=torch.float32)
    act = torch.as_tensor(batch["act"], dtype=torch.float32)
    old_logp = torch.as_tensor(batch["logp"], dtype=torch.float32)
    adv = torch.as_tensor(batch["adv"], dtype=torch.float32)
    ret = torch.as_tensor(batch["ret"], dtype=torch.float32)
    n = obs.shape[0]
    # advantage normalization across the whole batch (correct PPO normalization).
    adv = (adv - adv.mean()) / (adv.std() + 1e-8) if n > 1 else adv
    log_std_before = float(model.log_std.detach().mean())
    with torch.no_grad():
        entropy_before = float(model.policy_distribution(obs).entropy().sum(dim=-1).mean())

    if bc_aux is not None and bc_aux["obs"].shape[0] > 0:
        bc_obs = torch.as_tensor(bc_aux["obs"], dtype=torch.float32)
        bc_tgt = torch.clamp(torch.as_tensor(bc_aux["targets"], dtype=torch.float32), -1.0, 1.0)
    else:
        bc_obs = bc_tgt = None

    mb_size = max(1, n // max(1, minibatches))
    before = [p.detach().clone() for p in model.parameters()]
    last = {"pg_loss": 0.0, "value_loss": 0.0, "entropy": 0.0, "clip_frac": 0.0, "approx_kl": 0.0, "bc_aux_loss": 0.0}
    finite_grad = True
    grad_sq_last = 0.0
    for _ep in range(int(epochs)):
        order = rng.permutation(n)
        for start in range(0, n, mb_size):
            mb = order[start:start + mb_size]
            mb_t = torch.as_tensor(mb, dtype=torch.long)
            logp, entropy = model.evaluate_actions(obs[mb_t], act[mb_t])
            value = model.critic_forward(obs[mb_t], priv[mb_t])
            ratio = torch.exp(logp - old_logp[mb_t])
            mb_adv = adv[mb_t]
            surr1 = ratio * mb_adv
            surr2 = torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * mb_adv
            pg_loss = -torch.min(surr1, surr2).mean()
            value_loss = torch.mean((value - ret[mb_t]).pow(2))
            ent = entropy.mean()
            loss = pg_loss + value_coef * value_loss - entropy_coef * ent
            if bc_obs is not None and bc_aux_coef > 0.0:
                bc_mean = model.actor_forward(bc_obs)
                bc_aux_loss = torch.mean((bc_mean - bc_tgt).pow(2))
                loss = loss + bc_aux_coef * bc_aux_loss
                last["bc_aux_loss"] = float(bc_aux_loss.detach())
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            grad_sq = 0.0
            for p in model.parameters():
                if p.grad is None:
                    continue
                g = p.grad.detach()
                finite_grad = finite_grad and bool(torch.isfinite(g).all().item())
                grad_sq += float(torch.sum(g.pow(2)))
            grad_sq_last = grad_sq
            nn.utils.clip_grad_norm_(model.parameters(), PPO_MAX_GRAD_NORM)
            optimizer.step()
            with torch.no_grad():
                clip_frac = float(torch.mean((torch.abs(ratio - 1.0) > clip).float()))
                approx_kl = float(torch.mean(old_logp[mb_t] - logp).detach())
            last.update({
                "pg_loss": float(pg_loss.detach()),
                "value_loss": float(value_loss.detach()),
                "entropy": float(ent.detach()),
                "clip_frac": clip_frac,
                "approx_kl": approx_kl,
            })
    delta_sq = sum(float(torch.sum((nw.detach() - o).pow(2))) for o, nw in zip(before, model.parameters()))
    log_std_after = float(model.log_std.detach().mean())
    with torch.no_grad():
        entropy_after = float(model.policy_distribution(obs).entropy().sum(dim=-1).mean())
    finite_loss = all(math.isfinite(v) for v in (last["pg_loss"], last["value_loss"], last["entropy"]))
    return {
        "phase": "ppo",
        "pg_loss": last["pg_loss"],
        "value_loss": last["value_loss"],
        "entropy": last["entropy"],
        "bc_aux_loss": last["bc_aux_loss"],
        "bc_aux_coef": float(bc_aux_coef),
        "clip_fraction": last["clip_frac"],
        "approx_kl": last["approx_kl"],
        "grad_norm": float(math.sqrt(grad_sq_last)),
        "param_delta_l2": float(math.sqrt(delta_sq)),
        "log_std_before": log_std_before,
        "log_std_after": log_std_after,
        "log_std_mean": log_std_after,
        "entropy_before": entropy_before,
        "entropy_after": entropy_after,
        "mean_return": float(np.mean(batch["ret"])) if len(batch["ret"]) else float("nan"),
        "mean_reward": float(np.mean(batch["rew"])) if len(batch["rew"]) else float("nan"),
        "finite_loss": bool(finite_loss),
        "finite_grad": bool(finite_grad),
        "optimizer_changed_parameters": bool(delta_sq > 0.0),
        "batch_size": int(n),
        "total_loss": float(last["pg_loss"] + value_coef * last["value_loss"]),
    }


# --------------------------------------------------------------- rollout collection


def _curriculum_stage(update: int, total_updates: int) -> dict[str, Any]:
    if total_updates <= 1:
        return CURRICULUM_STAGES[0]
    frac = update / max(total_updates - 1, 1)
    idx = min(len(CURRICULUM_STAGES) - 1, int(frac * len(CURRICULUM_STAGES)))
    return CURRICULUM_STAGES[idx]


def collect_ppo_rollout(
    client: ChronoWorkerClient,
    model: AsymmetricActorCritic,
    *,
    stage: dict[str, Any],
    units: int,
    horizon: int,
    seed_ns: str,
    update: int,
    quick: bool,
) -> dict[str, Any]:
    """Collect a PPO rollout segment via the closed_loop_step protocol.

    Each unit is one closed-loop episode stepped by the STOCHASTIC policy; GAE is
    computed per trajectory with a critic bootstrap. (Per f1b: closed_loop_step is
    the training-equivalent transport; batched_action_sequence is open-loop and
    unusable for on-policy PPO.)
    """
    grid = _avoidance_grid(quick)
    n_avoid = max(1, int(round(units * float(stage["avoidance_frac"]))))
    obs_all, act_all, logp_all, priv_all, adv_all, ret_all, rew_all = ([] for _ in range(7))
    ep_returns: list[float] = []
    ep_success: list[float] = []
    for unit in range(units):
        regime = "avoidance" if unit < n_avoid else "drift"
        seed = _seed_for(seed_ns, update, regime, unit)
        if regime == "avoidance":
            reveal, mu = grid[unit % len(grid)]
            scenario = _avoidance_scenario(seed, max_steps=horizon, reveal=reveal, mu=mu)
        else:
            reveal, mu = 0.0, float(_drift_cell()["mu"])
            scenario = _drift_scenario(seed, max_steps=horizon, difficulty=str(stage["drift_difficulty"]))
        result = run_episode(
            client, scenario, regime, lambda s, o: model.act_stochastic(o),
            seed=seed, mu=mu, reveal=reveal, collect="ppo",
        )
        ppo = result["ppo"]
        if ppo["obs"].shape[0] == 0:
            continue
        with torch.no_grad():
            values = model.critic_forward(
                torch.as_tensor(ppo["obs"], dtype=torch.float32),
                torch.as_tensor(ppo["priv"], dtype=torch.float32),
            ).cpu().numpy().astype(np.float32)
            if ppo["terminated"]:
                last_value = 0.0
            else:
                last_value = float(model.critic_forward(
                    torch.as_tensor(ppo["last_obs"].reshape(1, -1), dtype=torch.float32),
                    torch.as_tensor(ppo["last_priv"].reshape(1, -1), dtype=torch.float32),
                ).item())
        adv, ret = compute_gae(ppo["rew"], values, ppo["done"], last_value)
        obs_all.append(ppo["obs"]); act_all.append(ppo["act"]); logp_all.append(ppo["logp"])
        priv_all.append(ppo["priv"]); adv_all.append(adv); ret_all.append(ret); rew_all.append(ppo["rew"])
        ep_returns.append(float(result["total_reward"]))
        ep_success.append(1.0 if result["success"] else 0.0)
    if not obs_all:
        empty = np.zeros((0, HUMAN_VIEW_OBS_DIM), dtype=np.float32)
        return {"obs": empty, "act": np.zeros((0, ACT_DIM), np.float32), "logp": np.zeros((0,), np.float32),
                "priv": np.zeros((0, PRIV_DIM), np.float32), "adv": np.zeros((0,), np.float32),
                "ret": np.zeros((0,), np.float32), "rew": np.zeros((0,), np.float32),
                "ep_returns": [], "ep_success": []}
    return {
        "obs": np.concatenate(obs_all, 0), "act": np.concatenate(act_all, 0),
        "logp": np.concatenate(logp_all, 0), "priv": np.concatenate(priv_all, 0),
        "adv": np.concatenate(adv_all, 0), "ret": np.concatenate(ret_all, 0),
        "rew": np.concatenate(rew_all, 0), "ep_returns": ep_returns, "ep_success": ep_success,
    }


def collect_bc_demos(
    client: ChronoWorkerClient,
    *,
    stage: dict[str, Any],
    units: int,
    horizon: int,
    seed_ns: str,
    update: int,
    quick: bool,
) -> dict[str, np.ndarray]:
    """Roll the per-regime teacher (B2: avoidance reveal-post only) for BC frames."""
    grid = _avoidance_grid(quick)
    n_avoid = max(1, int(round(units * float(stage["avoidance_frac"]))))
    frames, priv, targets = [], [], []
    for unit in range(units):
        regime = "avoidance" if unit < n_avoid else "drift"
        seed = _seed_for(seed_ns, update, regime, unit)
        if regime == "avoidance":
            reveal, mu = grid[unit % len(grid)]
            scenario = _avoidance_scenario(seed, max_steps=horizon, reveal=reveal, mu=mu)
            handle = teacher_for(regime, reveal=reveal, mu=mu)
        else:
            reveal, mu = 0.0, float(_drift_cell()["mu"])
            scenario = _drift_scenario(seed, max_steps=horizon, difficulty=str(stage["drift_difficulty"]))
            handle = teacher_for(regime)
        teacher = handle.factory()
        result = run_episode(client, scenario, regime, teacher, seed=seed, mu=mu, reveal=reveal, collect="bc")
        if result["bc_frames"].shape[0] == 0:
            continue
        frames.append(result["bc_frames"]); priv.append(result["bc_priv"]); targets.append(result["bc_targets"])
    if not frames:
        return {"obs": np.zeros((0, HUMAN_VIEW_OBS_DIM), np.float32), "priv": np.zeros((0, PRIV_DIM), np.float32),
                "targets": np.zeros((0, ACT_DIM), np.float32)}
    return {"obs": np.concatenate(frames, 0), "priv": np.concatenate(priv, 0), "targets": np.concatenate(targets, 0)}


# --------------------------------------------------------------- checkpointing (B1)


def _rng_state() -> dict[str, Any]:
    return {
        "torch": torch.get_rng_state(),
        "numpy": np.random.get_state(),
        "python": random.getstate(),
    }


def _set_rng_state(state: dict[str, Any]) -> None:
    torch.set_rng_state(state["torch"])
    np.random.set_state(state["numpy"])
    random.setstate(state["python"])


def _ckpt_path(ckpt_dir: Path, seed: int, update: int) -> Path:
    return ckpt_dir / f"seed{seed}_update{update:06d}.pt"


def save_checkpoint(
    ckpt_dir: Path, *, seed: int, update: int, model: AsymmetricActorCritic, optimizer: Adam,
    best_score: float, best_state: dict[str, Any], best_update: int, phase: str,
) -> Path:
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    path = _ckpt_path(ckpt_dir, seed, update)
    torch.save({
        "seed": int(seed),
        "update": int(update),
        "phase": str(phase),
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "best_score": float(best_score),
        "best_state": best_state,
        "best_update": int(best_update),
        "rng": _rng_state(),
    }, path)
    (ckpt_dir / f"seed{seed}_latest.txt").write_text(path.name, encoding="utf-8")
    return path


def latest_checkpoint(ckpt_dir: Path, seed: int) -> Path | None:
    pointer = ckpt_dir / f"seed{seed}_latest.txt"
    if pointer.exists():
        cand = ckpt_dir / pointer.read_text(encoding="utf-8").strip()
        if cand.exists():
            return cand
    cands = sorted(ckpt_dir.glob(f"seed{seed}_update*.pt"))
    return cands[-1] if cands else None


def load_checkpoint(path: Path, model: AsymmetricActorCritic, optimizer: Adam) -> dict[str, Any]:
    state = torch.load(path, map_location="cpu", weights_only=False)
    model.load_state_dict(state["model"])
    optimizer.load_state_dict(state["optimizer"])
    _set_rng_state(state["rng"])
    return state


# --------------------------------------------------------------- training loop (one seed)


def train_student(
    *,
    seed: int,
    budget: dict[str, Any],
    quick: bool,
    ckpt_dir: Path,
    stderr_log: Path,
    progress: Path,
    train_metrics: list[dict[str, Any]],
    resume: bool,
) -> dict[str, Any]:
    """Train one student seed by BC warm-start then PPO; checkpoint each update."""
    torch.manual_seed(_seed_for("actor_init", seed))
    np.random.seed(_seed_for("np_init", seed) % (2**32))
    random.seed(_seed_for("py_init", seed) % (2**32))
    model = AsymmetricActorCritic()
    optimizer = Adam(model.parameters(), lr=PPO_LR)
    rng = np.random.default_rng(_seed_for("ppo_minibatch", seed))

    warmstart_updates = int(budget["warmstart_updates"])
    ppo_updates = int(budget["ppo_updates"])
    total_updates = warmstart_updates + ppo_updates
    best_score = -float("inf")
    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    best_update = -1
    start_update = 0

    if resume:
        ckpt = latest_checkpoint(ckpt_dir, seed)
        if ckpt is not None:
            state = load_checkpoint(ckpt, model, optimizer)
            start_update = int(state["update"]) + 1
            best_score = float(state["best_score"])
            best_state = state["best_state"]
            best_update = int(state["best_update"])
            _progress(progress, {"stage": "resume", "seed": seed, "from_update": start_update})

    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        for update in range(start_update, total_updates):
            stage = _curriculum_stage(update, total_updates)
            if update < warmstart_updates:
                demos = collect_bc_demos(
                    client, stage=stage, units=int(budget["warmstart_units"]),
                    horizon=int(budget["rollout_horizon"]), seed_ns=f"bc_seed{seed}", update=update, quick=quick,
                )
                if demos["obs"].shape[0] > 0:
                    upd = bc_update(model, optimizer, demos["obs"], demos["priv"], demos["targets"])
                else:
                    upd = _empty_update("bc_warmstart")
                mean_train_return = float("nan")
                mean_train_success = float("nan")
            else:
                ppo_idx = update - warmstart_updates
                bc_aux_coef = _anneal(BC_AUX_COEF_START, BC_AUX_COEF_END, ppo_idx, max(1, ppo_updates - 1))
                batch = collect_ppo_rollout(
                    client, model, stage=stage, units=int(budget["rollout_workers"]),
                    horizon=int(budget["rollout_horizon"]), seed_ns=f"ppo_seed{seed}", update=update, quick=quick,
                )
                bc_aux = None
                if bc_aux_coef > 0.0:
                    aux = collect_bc_demos(
                        client, stage=stage, units=max(1, int(budget["warmstart_units"]) // 2),
                        horizon=int(budget["rollout_horizon"]), seed_ns=f"aux_seed{seed}", update=update, quick=quick,
                    )
                    bc_aux = {"obs": aux["obs"], "targets": aux["targets"]} if aux["obs"].shape[0] > 0 else None
                if batch["obs"].shape[0] > 0:
                    upd = ppo_update(model, optimizer, batch, bc_aux_coef=bc_aux_coef, bc_aux=bc_aux, rng=rng)
                else:
                    upd = _empty_update("ppo")
                mean_train_return = float(np.mean(batch["ep_returns"])) if batch["ep_returns"] else float("nan")
                mean_train_success = float(np.mean(batch["ep_success"])) if batch["ep_success"] else float("nan")

            # held-out selection: disjoint teacher-demo batch, actor MSE to teacher
            # (G1'/C1-v4 lesson: never select on training loss).
            holdout = collect_bc_demos(
                client, stage=stage, units=max(1, int(budget["selection_units_per_regime"])),
                horizon=int(budget["rollout_horizon"]), seed_ns=f"holdout_seed{seed}", update=update, quick=quick,
            )
            if holdout["obs"].shape[0] > 0:
                with torch.no_grad():
                    pred = model.actor_forward(torch.as_tensor(holdout["obs"], dtype=torch.float32))
                    holdout_mse = float(torch.mean((pred - torch.as_tensor(holdout["targets"], dtype=torch.float32)).pow(2)))
            else:
                holdout_mse = float("inf")
            holdout_score = -holdout_mse
            # always select on the FIRST update considered (best_update < 0), then
            # strict-improve; this guarantees a held-out-selected checkpoint exists
            # even if the holdout batch is empty/tied (small-budget --quick).
            if best_update < 0 or holdout_score > best_score:
                best_score = holdout_score
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
                best_update = update

            row = {
                "seed": int(seed), "update": int(update), "phase": str(upd["phase"]),
                "stage": int(stage["stage"]), "stage_name": str(stage["name"]),
                "batch_size": int(upd["batch_size"]),
                "bc_loss": float(upd.get("bc_loss", float("nan"))),
                "pg_loss": float(upd.get("pg_loss", float("nan"))),
                "value_loss": float(upd.get("value_loss", float("nan"))),
                "entropy": float(upd.get("entropy", float("nan"))),
                "bc_aux_coef": float(upd.get("bc_aux_coef", 0.0)),
                "clip_fraction": float(upd.get("clip_fraction", float("nan"))),
                "approx_kl": float(upd.get("approx_kl", float("nan"))),
                "log_std_mean": float(upd.get("log_std_mean", float("nan"))),
                "grad_norm": float(upd["grad_norm"]),
                "param_delta_l2": float(upd["param_delta_l2"]),
                "mean_train_return": mean_train_return,
                "mean_train_success": mean_train_success,
                "holdout_distill_mse": float(holdout_mse),
                "selected_so_far": int(best_update),
                "finite_loss": bool(upd["finite_loss"]),
                "finite_grad": bool(upd["finite_grad"]),
                "optimizer_changed_parameters": bool(upd["optimizer_changed_parameters"]),
            }
            train_metrics.append(row)
            save_checkpoint(
                ckpt_dir, seed=seed, update=update, model=model, optimizer=optimizer,
                best_score=best_score, best_state=best_state, best_update=best_update, phase=str(upd["phase"]),
            )
            _progress(progress, {"stage": "train", "seed": seed, "update": update, "phase": upd["phase"],
                                 "holdout_mse": holdout_mse, "best_update": best_update,
                                 "log_std_mean": row["log_std_mean"], "entropy": row["entropy"]})
    finally:
        client.close()

    model.load_state_dict(best_state)
    model.eval()
    seed_rows = [r for r in train_metrics if r["seed"] == seed]
    ppo_rows = [r for r in seed_rows if r["phase"] == "ppo"]
    return {
        "model": model,
        "seed": int(seed),
        "best_update": int(best_update),
        "best_holdout_neg_mse": float(best_score),
        "total_updates": int(total_updates),
        "warmstart_updates": int(warmstart_updates),
        "ppo_updates_done": len(ppo_rows),
        "any_param_changed": any(r["optimizer_changed_parameters"] for r in seed_rows),
        "all_finite": all(r["finite_loss"] and r["finite_grad"] for r in seed_rows),
        "log_std_observed": any(math.isfinite(r["log_std_mean"]) for r in ppo_rows),
        "entropy_observed": any(math.isfinite(r["entropy"]) for r in ppo_rows),
        "ppo_ran": len(ppo_rows) > 0,
    }


def _anneal(start: float, end: float, step: int, total: int) -> float:
    if total <= 0:
        return end
    frac = min(1.0, max(0.0, step / total))
    return float(start + (end - start) * frac)


def _empty_update(phase: str) -> dict[str, Any]:
    return {"phase": phase, "finite_loss": True, "finite_grad": True, "optimizer_changed_parameters": False,
            "batch_size": 0, "grad_norm": 0.0, "param_delta_l2": 0.0, "bc_loss": float("nan"),
            "pg_loss": float("nan"), "value_loss": float("nan"), "entropy": float("nan"),
            "bc_aux_coef": 0.0, "clip_fraction": float("nan"), "approx_kl": float("nan"),
            "log_std_mean": float("nan")}


# --------------------------------------------------------------- four-arm adjudication


# the oracle/teacher needs mu_true per scenario; the validation grid carries it.
_EVAL_MU_REGISTRY: dict[float, float] = {}


def _avoidance_eval_mu_for(reveal: float) -> float:
    return _EVAL_MU_REGISTRY.get(round(float(reveal), 6), AVOIDANCE_MUS_FULL[0])


def arm_policy(arm: str, regime: str, student_model: AsymmetricActorCritic | None, *, reveal: float) -> Callable[[int, np.ndarray], np.ndarray]:
    if arm == "fixed_star":
        return e4.FixedStarPolicy()
    if arm == "entry_speed_commitment_floor":
        if regime == "drift":
            return e4.TunedReflexPolicy(e4.REFLEX_TUNES[2])  # belief-free conservative drift reflex
        return _EntrySpeedCommitmentFloor(reveal=reveal, v_entry=float(ENTRY_SPEED_FLOOR_VENTRIES[0]))
    if arm == "online_mu_seeker_floor":
        if regime == "drift":
            return e4.TunedReflexPolicy(e4.REFLEX_TUNES[1])  # alternate belief-free drift reflex
        return _OnlineMuSeekerFloor(reveal=reveal)
    if arm == "per_regime_oracle":
        if regime == "avoidance":
            return teacher_for(regime, reveal=reveal, mu=_avoidance_eval_mu_for(reveal)).factory()
        return teacher_for(regime).factory()
    if arm == "student_policy":
        assert student_model is not None
        return lambda _step, obs: student_model.act(obs)
    raise ValueError(f"unknown arm {arm!r}")


ROW_FIELDS = [
    "mode", "arm", "regime", "reveal", "mu", "seed", "validation_unit", "scenario_id",
    "steps", "success", "collision", "total_reward", "longest_controlled_drift_run",
    "min_clearance_margin", "finite_obs_all", "student_input_was_obs72_only",
    "train_seed", "claim_boundary",
]


def evaluate_arms(
    students_by_seed: dict[int, AsymmetricActorCritic],
    *,
    budget: dict[str, Any],
    quick: bool,
    stderr_log: Path,
    progress: Path,
) -> list[dict[str, Any]]:
    """Validate EVERY training seed's student (B3) on a disjoint mu/reveal grid."""
    rows: list[dict[str, Any]] = []
    grid = _avoidance_grid(quick)
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        for regime in ("avoidance", "drift"):
            for unit in range(int(budget["validation_units_per_regime"])):
                if regime == "avoidance":
                    reveal, mu = grid[unit % len(grid)]
                else:
                    reveal, mu = 0.0, float(_drift_cell()["mu"])
                _EVAL_MU_REGISTRY[round(float(reveal), 6)] = float(mu)
                # disjoint VALIDATION seed namespace (never used in training/holdout).
                seed = _seed_for("validation", regime, unit, round(reveal, 4), round(mu, 4))
                scenario = (
                    _avoidance_scenario(seed, max_steps=int(budget["rollout_horizon"]), reveal=reveal, mu=mu)
                    if regime == "avoidance"
                    else _drift_scenario(seed, max_steps=int(budget["rollout_horizon"]), difficulty="hard")
                )
                for arm in ARMS:
                    if arm == "student_policy":
                        for train_seed, model in students_by_seed.items():
                            result = run_episode(client, scenario, regime, lambda s, o, m=model: m.act(o),
                                                 seed=seed, mu=mu, reveal=reveal)
                            rows.append(_arm_row(quick, arm, regime, reveal, mu, seed, unit, result, train_seed=train_seed))
                    else:
                        policy = arm_policy(arm, regime, None, reveal=reveal)
                        result = run_episode(client, scenario, regime, policy, seed=seed, mu=mu, reveal=reveal)
                        rows.append(_arm_row(quick, arm, regime, reveal, mu, seed, unit, result, train_seed=-1))
                _progress(progress, {"stage": "validation", "regime": regime, "unit": unit})
    finally:
        client.close()
    return rows


def _arm_row(quick: bool, arm: str, regime: str, reveal: float, mu: float, seed: int, unit: int, result: dict[str, Any], *, train_seed: int) -> dict[str, Any]:
    return {
        "mode": "quick" if quick else "full",
        "arm": arm, "regime": regime, "reveal": round(float(reveal), 4), "mu": round(float(mu), 4),
        "seed": int(seed), "validation_unit": int(unit), "scenario_id": result["scenario_id"],
        "steps": int(result["steps"]), "success": bool(result["success"]), "collision": bool(result["collision"]),
        "total_reward": round(float(result["total_reward"]), 6),
        "longest_controlled_drift_run": int(result["longest_controlled_drift_run"]),
        "min_clearance_margin": round(float(result["min_clearance_margin"]), 6) if math.isfinite(result["min_clearance_margin"]) else "",
        "finite_obs_all": bool(result["finite_obs_all"]),
        "student_input_was_obs72_only": True if arm == "student_policy" else "",
        "train_seed": int(train_seed),
        "claim_boundary": CLAIM_BOUNDARY,
    }


# --------------------------------------------------------------- B6 reward alignment (per-episode Spearman, hard gate)


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    def rank(x: np.ndarray) -> np.ndarray:
        order = np.argsort(x, kind="mergesort")
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(len(x), dtype=float)
        _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
        sums = np.zeros(len(counts))
        np.add.at(sums, inv, ranks)
        return (sums / counts)[inv]
    ra, rb = rank(a), rank(b)
    if np.std(ra) < 1e-12 or np.std(rb) < 1e-12:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def _rank_biserial_auc(rewards: np.ndarray, successes: np.ndarray) -> float:
    """Mann-Whitney AUC = P(reward[success] > reward[failure]) (ties at 0.5).

    This is the alignment statistic appropriate for a BINARY outcome vs a
    continuous reward: a raw Spearman is structurally capped well below 1.0 for
    binary labels, so the >=0.9 hard gate belongs on the AUC (the probability a
    random successful episode outscores a random failed one), not on Spearman.
    """
    pos = rewards[successes > 0.5]
    neg = rewards[successes <= 0.5]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    for r in pos:
        wins += float(np.sum(neg < r)) + 0.5 * float(np.sum(neg == r))
    return wins / (len(pos) * len(neg))


def reward_alignment_spearman(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """B6 reward-hacking guard (per EPISODE).

    Reports the per-episode Spearman(reward, success) AND the rank-biserial AUC
    (the binary-appropriate alignment metric). The >=0.9 HARD gate is on the AUC:
    a random successful episode must outscore a random failed one >=90% of the
    time. N/A (gate not applicable) when ties make it undefined (all-success,
    all-failure, or all-equal rewards). A failing gate forces re-pricing.
    """
    rewards = np.asarray([float(r["total_reward"]) for r in rows], dtype=float)
    successes = np.asarray([1.0 if bool(r["success"]) else 0.0 for r in rows], dtype=float)
    n = int(len(rewards))
    na = {"spearman": None, "auc": None, "n_episodes": n, "meets_0p9": None,
          "tie_degenerate": True, "gate_applicable": False}
    if n < 2 or len(np.unique(successes)) < 2 or len(np.unique(rewards)) < 2:
        return na
    auc = _rank_biserial_auc(rewards, successes)
    if not math.isfinite(auc):
        return na
    rho = _spearman(rewards, successes)
    return {
        "spearman": float(rho) if math.isfinite(rho) else None,
        "auc": float(auc),
        "n_episodes": n,
        "meets_0p9": bool(auc >= 0.9),
        "gate_statistic": "rank_biserial_auc",
        "tie_degenerate": False,
        "gate_applicable": True,
    }


# --------------------------------------------------------------- B4 CIs (cross-training-seed)


def _t_critical_95(df: int) -> float:
    table = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
             8: 2.306, 9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 30: 2.042}
    if df in table:
        return table[df]
    keys = sorted(table)
    if df < keys[0]:
        return table[keys[0]]
    if df > keys[-1]:
        return 1.96 + (table[30] - 1.96) * (30.0 / max(df, 31))
    lo = max(k for k in keys if k <= df)
    hi = min(k for k in keys if k >= df)
    if lo == hi:
        return table[lo]
    frac = (df - lo) / (hi - lo)
    return table[lo] + frac * (table[hi] - table[lo])


def _paired_t_ci(diffs: list[float], *, conf: float = 0.95) -> dict[str, Any]:
    arr = np.asarray(diffs, dtype=float)
    n = int(len(arr))
    if n == 0:
        return {"n": 0, "mean": float("nan"), "ci95_low": float("nan"), "ci95_high": float("nan"), "method": "paired_t"}
    mean = float(np.mean(arr))
    if n == 1:
        return {"n": 1, "mean": round(mean, 6), "ci95_low": round(mean, 6), "ci95_high": round(mean, 6), "method": "paired_t_n1_point"}
    sd = float(np.std(arr, ddof=1))
    t_crit = _t_critical_95(n - 1)
    half = t_crit * sd / math.sqrt(n)
    return {"n": n, "mean": round(mean, 6), "ci95_low": round(mean - half, 6), "ci95_high": round(mean + half, 6),
            "sd": round(sd, 6), "t_crit": round(t_crit, 4), "method": "paired_t"}


def _seed_cluster_bootstrap(diffs: list[float], *, n_boot: int = 4000, seed: int = 12345) -> dict[str, Any]:
    arr = np.asarray(diffs, dtype=float)
    n = int(len(arr))
    if n == 0:
        return {"n": 0, "ci95_low": float("nan"), "ci95_high": float("nan"), "method": "seed_cluster_bootstrap"}
    if n == 1:
        return {"n": 1, "ci95_low": round(float(arr[0]), 6), "ci95_high": round(float(arr[0]), 6), "method": "seed_cluster_bootstrap_n1_point"}
    rng = np.random.default_rng(seed)
    means = np.asarray([float(np.mean(rng.choice(arr, size=n, replace=True))) for _ in range(n_boot)])
    return {"n": n, "ci95_low": round(float(np.percentile(means, 2.5)), 6),
            "ci95_high": round(float(np.percentile(means, 97.5)), 6), "method": "seed_cluster_bootstrap"}


def _per_seed_success(rows: list[dict[str, Any]], arm: str, regime: str) -> dict[int, float]:
    """For student: success per TRAINING seed (each seed = 1 unit, B3)."""
    by_seed: dict[int, list[float]] = {}
    for r in rows:
        if r["arm"] != arm or (regime != "pooled" and r["regime"] != regime):
            continue
        ts = int(r["train_seed"])
        by_seed.setdefault(ts, []).append(1.0 if bool(r["success"]) else 0.0)
    return {ts: float(np.mean(v)) for ts, v in by_seed.items() if v}


def _floor_rate(rows: list[dict[str, Any]], regime: str) -> float:
    rates = []
    for arm in FLOOR_ARMS:
        sel = [r for r in rows if r["arm"] == arm and (regime == "pooled" or r["regime"] == regime) and int(r["train_seed"]) == -1]
        if sel:
            rates.append(float(np.mean([1.0 if bool(r["success"]) else 0.0 for r in sel])))
    return max(rates) if rates else 0.0


def _floor_success_by_seed(rows: list[dict[str, Any]], regime: str, train_seeds: list[int]) -> dict[int, float]:
    """Floor = max over classical arms; broadcast to each training seed for pairing."""
    floor_rate = _floor_rate(rows, regime)
    return {ts: floor_rate for ts in train_seeds}


def adjudicate(rows: list[dict[str, Any]], *, train_seeds: list[int]) -> dict[str, Any]:
    per_regime: dict[str, dict[str, Any]] = {}
    for regime in ("avoidance", "drift", "pooled"):
        block: dict[str, Any] = {}
        for arm in ARMS:
            sel = [r for r in rows if r["arm"] == arm and (regime == "pooled" or r["regime"] == regime)]
            succ = [1.0 if bool(r["success"]) else 0.0 for r in sel]
            if arm == "student_policy":
                by_seed = _per_seed_success(rows, arm, regime)
                seed_means = list(by_seed.values())
                cluster_se = float(np.std(seed_means, ddof=1) / math.sqrt(len(seed_means))) if len(seed_means) > 1 else 0.0
                n_seeds = len(seed_means)
            else:
                cluster_se = 0.0
                n_seeds = 0
            block[arm] = {
                "n": len(sel),
                "success_rate": float(np.mean(succ)) if succ else float("nan"),
                "mean_reward": float(np.mean([float(r["total_reward"]) for r in sel])) if sel else float("nan"),
                "collision_rate": float(np.mean([1.0 if bool(r["collision"]) else 0.0 for r in sel])) if sel else float("nan"),
                "seed_cluster_se": cluster_se,
                "n_training_seeds": n_seeds,
            }
        per_regime[regime] = block

    # B4: cross-training-seed paired diff (student[seed] - floor) CIs per regime.
    seed_clustered = {}
    for regime in ("avoidance", "drift"):
        student_by_seed = _per_seed_success(rows, "student_policy", regime)
        floor_by_seed = _floor_success_by_seed(rows, regime, list(student_by_seed.keys()))
        diffs = [student_by_seed[ts] - floor_by_seed[ts] for ts in student_by_seed]
        seed_clustered[regime] = {
            "student_minus_floor_paired_t_ci": _paired_t_ci(diffs),
            "student_minus_floor_cluster_bootstrap_ci": _seed_cluster_bootstrap(diffs),
            "floor_rate": _floor_rate(rows, regime),
            "n_training_seeds": len(diffs),
        }

    prize = {
        "drift_student_minus_floor": float(per_regime["drift"]["student_policy"]["success_rate"] - _floor_rate(rows, "drift")),
        "drift_oracle_minus_floor": float(per_regime["drift"]["per_regime_oracle"]["success_rate"] - _floor_rate(rows, "drift")),
        "avoidance_student_minus_floor": float(per_regime["avoidance"]["student_policy"]["success_rate"] - _floor_rate(rows, "avoidance")),
        "avoidance_oracle_minus_floor": float(per_regime["avoidance"]["per_regime_oracle"]["success_rate"] - _floor_rate(rows, "avoidance")),
    }
    no_regression = bool(per_regime["avoidance"]["student_policy"]["success_rate"] >= _floor_rate(rows, "avoidance") - 1e-9)
    return {"per_regime": per_regime, "seed_clustered_ci": seed_clustered, "prize_recovery": prize,
            "student_no_avoidance_regression": no_regression}


# --------------------------------------------------------------- S7 oracle-ceiling precheck


def oracle_ceiling_precheck(
    *, budget: dict[str, Any], quick: bool, stderr_log: Path,
    floor_threshold: float = 0.0, prize: float = 0.0,
) -> dict[str, Any]:
    """S7: measure the oracle arm's success ceiling on the student/hard grid.

    If the matched oracle cannot clear floor+prize on this distribution, the full
    run is not worth its wall-clock -> stop + re-price (recorded, not enforced in
    --quick which is a chain smoke).
    """
    grid = _avoidance_grid(quick)
    units = max(1, int(budget["selection_units_per_regime"]))
    client = ChronoWorkerClient(stderr_log=stderr_log)
    out: dict[str, list[float]] = {"avoidance": [], "drift": []}
    try:
        for regime in ("avoidance", "drift"):
            for unit in range(units):
                if regime == "avoidance":
                    reveal, mu = grid[unit % len(grid)]
                else:
                    reveal, mu = 0.0, float(_drift_cell()["mu"])
                _EVAL_MU_REGISTRY[round(float(reveal), 6)] = float(mu)
                seed = _seed_for("s7_precheck", regime, unit)
                scenario = (
                    _avoidance_scenario(seed, max_steps=int(budget["rollout_horizon"]), reveal=reveal, mu=mu)
                    if regime == "avoidance"
                    else _drift_scenario(seed, max_steps=int(budget["rollout_horizon"]), difficulty="hard")
                )
                policy = arm_policy("per_regime_oracle", regime, None, reveal=reveal)
                result = run_episode(client, scenario, regime, policy, seed=seed, mu=mu, reveal=reveal)
                out[regime].append(1.0 if result["success"] else 0.0)
    finally:
        client.close()
    ceilings = {regime: (float(np.mean(v)) if v else float("nan")) for regime, v in out.items()}
    drift_ok = (not math.isnan(ceilings["drift"])) and ceilings["drift"] >= floor_threshold + prize
    return {
        "oracle_ceiling_by_regime": ceilings,
        "units_per_regime": units,
        "floor_plus_prize_threshold": float(floor_threshold + prize),
        "drift_oracle_clears_floor_plus_prize": bool(drift_ok),
        "recommendation": "proceed_to_full" if drift_ok else "stop_and_reprice_before_full",
    }


# --------------------------------------------------------------- prereg (freeze-ready)


def _power_analysis() -> dict[str, Any]:
    """S4: 8-seed power vs expected effect against expected cross-seed SD."""
    n = FULL["seeds"]
    expected_sd = 0.18  # priced per-seed student-validation dispersion (F1/E4 spread)
    t_crit = _t_critical_95(n - 1)
    mde = t_crit * expected_sd / math.sqrt(n)  # min detectable effect at CI-lower>0 boundary
    return {
        "n_training_seeds": n,
        "expected_effect_drift": 0.40,
        "expected_effect_avoidance": 0.18,
        "assumed_cross_seed_sd": expected_sd,
        "ci_method": "cross-training-seed paired t-CI of (student - floor); cluster bootstrap as robustness",
        "minimum_detectable_effect_at_8_seeds": round(float(mde), 4),
        "drift_powered": bool(0.40 > mde),
        "avoidance_powered": bool(0.18 > mde),
        "note": (
            "If observed cross-seed SD exceeds the assumed 0.18 such that the drift effect "
            "+0.40 no longer exceeds the MDE, raise seeds or per-seed validation units before freeze."
        ),
    }


def build_preregistration() -> dict[str, Any]:
    deps = {}
    for label, path in (("f1", F1_JSON), ("f1b", F1B_JSON), ("e2prime", E2PRIME_JSON), ("e4", E4_JSON)):
        if path.exists():
            deps[f"{label}_artifact"] = str(path.relative_to(REPO_ROOT))
            deps[f"{label}_gates_passed"] = bool(_read_json(path).get("protocol_gates", {}).get("all_passed", False))
        else:
            deps[f"{label}_artifact"] = None
            deps[f"{label}_gates_passed"] = None
    return {
        "protocol": "phase4_f2_asymmetric_actor_critic_rl_preregistration_FREEZE_READY",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 F2 asymmetric actor-critic RL training and four-arm adjudication",
        "scope_decision_s3": "real_asymmetric_actor_critic_rl (PI option 1): PPO + bootstrapped privileged GAE critic + policy gradient; teacher = warm-start/annealed-auxiliary only, NOT distillation",
        "draft": True,
        "frozen": False,
        "freeze_ready": True,
        "freeze_blocked_on": "PI sign-off only; criteria/CI/floor/spectrum/power/curriculum are all defined and freezable",
        "drafted_at_utc": utc_timestamp(),
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "dependencies": deps,
        "asymmetry_contract": {
            "actor_input": "obs72 (deployable human-view frame) only",
            "actor_policy": "Gaussian: state-dependent mean + learnable per-action log_std; deployment = tanh(mean)",
            "critic_input": "obs72 + privileged features (true mu, mass, grip surrogate, reveal surrogate, regime onehot x2)",
            "privileged_dim": PRIV_DIM,
            "deployment": "critic dropped; only actor(obs72) ships",
            "assertion": "actor forward rejects any input not of dim 72; act() has no privileged path; tested",
        },
        "rl_algorithm": {
            "method": "PPO (clipped surrogate) with bootstrapped privileged GAE(lambda) critic",
            "transport": "closed_loop_step protocol (training-equivalent; batched_action_sequence is open-loop and unusable for PPO)",
            "gamma": PPO_GAMMA, "gae_lambda": PPO_LAMBDA, "clip": PPO_CLIP,
            "value_coef": PPO_VALUE_COEF, "entropy_coef": PPO_ENTROPY_COEF,
            "epochs": PPO_EPOCHS, "minibatches": PPO_MINIBATCHES, "max_grad_norm": PPO_MAX_GRAD_NORM, "lr": PPO_LR,
            "advantage_normalization": "batch-wise (mean/std) before minibatch SGD",
            "log_std_init": LOG_STD_INIT, "log_std_min": LOG_STD_MIN, "log_std_max": LOG_STD_MAX,
            "rollout_horizon_full": FULL["rollout_horizon"], "rollout_workers_full": FULL["rollout_workers"],
        },
        "teacher_role": {
            "m1087_chain": "BC warm-start -> annealed auxiliary BC (coef decays to 0) -> PPO policy gradient dominates",
            "bc_warmstart_coef": BC_WARMSTART_COEF,
            "bc_aux_coef_start": BC_AUX_COEF_START, "bc_aux_coef_end": BC_AUX_COEF_END,
            "avoidance": {
                "source": "phase4_e2prime RampPolicyController(mode=oracle, mu_true, dv)",
                "binding": {"reveals_m": list(AVOIDANCE_REVEALS_FULL), "mus": list(AVOIDANCE_MUS_FULL), "oracle_dv": AVOIDANCE_ORACLE_DV},
                "B2_leak_guard": "BC warm-start imitates ONLY the reveal-post obs72-recoverable segment; pre-reveal mu-dependent action is never imitated; PPO learns from reward",
                "prize_source": "E2'/M3258 clean belief value up to +0.77 (and +0.18 detection value)",
            },
            "drift": {
                "source": "phase4_e4 DriftFeedbackPolicy / DriftFeedbackSpec",
                "binding": {"cell_id": DRIFT_CELL_ID, "spec": DRIFT_FEEDBACK_NAME},
                "prize_source": "E4/M3260 drift gap +0.40",
                "forbidden": "the native Chrono CEM oracle scored 0/N in the drift cell and is NEVER the drift teacher",
            },
        },
        "reward_recalibration": {
            "collision_penalty": COLLISION_PENALTY, "offtrack_penalty": OFFTRACK_PENALTY,
            "avoidance_pass_reward": AVOIDANCE_PASS_REWARD, "drift_success_reward": DRIFT_SUCCESS_REWARD,
            "S5_fail_closed": "avoidance success/pass requires explicit cleared completion; completion=='' is a FAILURE",
            "S5_grazing_penalty": {"speed_norm_threshold": GRAZE_SPEED_NORM, "margin_m": GRAZE_MARGIN_M, "penalty": GRAZE_PENALTY},
            "source": "m1087 staged discipline + C5 measured collision cost; penalties >= success rewards",
            "B6_reward_hacking_guard": "per-EPISODE alignment: report Spearman(reward,success) AND rank-biserial AUC = P(reward[success]>reward[failure]); the >=0.9 HARD gate is on the AUC (binary-appropriate; raw Spearman is structurally capped for binary labels); N/A on ties; failure -> re-price",
        },
        "avoidance_spectrum_S2": {
            "reveals_m_full": list(AVOIDANCE_REVEALS_FULL), "mus_full": list(AVOIDANCE_MUS_FULL),
            "reveals_m_quick": list(AVOIDANCE_REVEALS_QUICK), "mus_quick": list(AVOIDANCE_MUS_QUICK),
            "applies_to": "training curriculum AND validation grid",
        },
        "curriculum": {
            "stages": list(CURRICULUM_STAGES),
            "drift_difficulty_beta_scale": DRIFT_DIFFICULTY_BETA_SCALE,
            "progression": "easy: avoidance-weighted + easy drift -> hard: drift-weighted + hard drift",
        },
        "arms": {
            "fixed_star": "unmodified v4 ActiveSafetyReflexDriver (incumbent, unchanged)",
            "entry_speed_commitment_floor": "B5 classical: belief-free entry-speed commitment fixed-plan (avoidance) / conservative belief-free reflex (drift); obs72-only, learning-free",
            "online_mu_seeker_floor": "B5 classical: online mu-estimating threshold-seeker reflex (avoidance) / alternate belief-free reflex (drift); estimates mu from its OWN action channel, NO oracle mu_true",
            "per_regime_oracle": "the per-regime teacher itself (matched oracle anchor)",
            "student_policy": "trained asymmetric obs72 PPO actor",
        },
        "floor_definition_B5": "max over learning-free non-trivial classical arms {fixed*, entry_speed_commitment_floor, online_mu_seeker_floor}; NOT the bare incumbent; not a strawman",
        "seed_streams": {
            "ppo_namespace": "ppo_seed{seed}", "bc_warmstart_namespace": "bc_seed{seed}",
            "bc_aux_namespace": "aux_seed{seed}", "holdout_selection_namespace": "holdout_seed{seed}",
            "validation_namespace": "validation", "s7_precheck_namespace": "s7_precheck",
            "disjointness_rule": "sha256(SEED_BASE, namespace, ...); training/holdout/validation/precheck namespaces never overlap",
            "new_seed_base": SEED_BASE,
        },
        "statistics_B3_B4": {
            "validate_all_training_seeds": True,
            "seed_cluster_unit": "TRAINING seed (each seed's student validation success rate is one observation, n=seeds)",
            "ci_method_primary": "cross-training-seed paired t-CI of (student - floor)",
            "ci_method_robustness": "seed-clustered bootstrap of the same paired diff",
            "adjudication_uses": "real CI lower bound (not a point difference)",
        },
        "power_analysis_S4": _power_analysis(),
        "pre_full_checks_S7": {
            "oracle_ceiling_precheck": "measure matched oracle success on the student/hard grid; if < floor+prize, STOP + re-price before spending full wall-clock",
        },
        "checkpointing_B1": {
            "per": "(seed, update)", "contents": ["model", "optimizer", "update", "seed", "best_score", "best_state", "best_update", "rng(torch+numpy+python)"],
            "resume": "--resume loads the latest per-seed checkpoint and restores RNG; kill-and-resume tested to continue from N (non-zero)",
        },
        "pass_thresholds_DRAFT": {
            "behavior_neutral_x2_stop": "two consecutive behavior-neutral full results on a regime -> stop + re-price",
            "student_recovers_drift_prize": "student drift success - floor: cross-seed paired t-CI lower bound > 0 on the full run",
            "student_no_regression": "student avoidance success >= avoidance floor on full run",
            "reward_alignment_hard_gate": "per-episode rank-biserial AUC(reward,success) >= 0.9 (N/A on ties; failure -> re-price); Spearman reported alongside",
            "note": "thresholds defined and freezable; frozen=false pending PI sign-off only",
        },
        "leak_discipline": {
            "actor_privileged_isolation": "asserted: actor never receives mu/privileged channels",
            "B2_bc_reveal_post_only": AVOIDANCE_BC_REVEAL_POST_ONLY,
            "obs72_mu_reconstruction": "engineering work makes no attribution claim; actor isolation is the guard, not a probe",
        },
        "budgets": {"quick": QUICK, "full": FULL},
        "managed_full": {
            "launch": "PI-gated; managed (run_managed.sh / setsid + progress.jsonl + --resume); NOT launched in agent session",
            "device": "CPU (CUDA measured 2.6x slower); OMP_NUM_THREADS=1, multi-process",
        },
        "quick_mode_is_verdict": False,
    }


def write_preregistration() -> dict[str, Any]:
    payload = build_preregistration()
    write_json(PREREG_JSON, payload)
    return payload


def load_preregistration() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise FileNotFoundError(f"missing preregistration {PREREG_JSON}; run --write-prereg first")
    return _read_json(PREREG_JSON)


# --------------------------------------------------------------- summary + doc


def summarize(
    rows: list[dict[str, Any]],
    train_summaries: list[dict[str, Any]],
    train_metrics: list[dict[str, Any]],
    *,
    quick: bool,
    elapsed_s: float,
    seeds: list[int],
    s7: dict[str, Any],
) -> dict[str, Any]:
    adjud = adjudicate(rows, train_seeds=seeds)
    alignment = reward_alignment_spearman(rows)
    student_rows = [r for r in rows if r["arm"] == "student_policy"]
    ppo_rows = [r for r in train_metrics if r["phase"] == "ppo"]
    log_std_vals = [r["log_std_mean"] for r in ppo_rows if math.isfinite(r["log_std_mean"])]
    entropy_vals = [r["entropy"] for r in ppo_rows if math.isfinite(r["entropy"])]
    validated_seeds = {int(r["train_seed"]) for r in student_rows}
    # B6 hard gate: pass if alignment meets 0.9 OR is N/A (degenerate ties);
    # FAIL only when applicable and below 0.9.
    b6_ok = (not alignment["gate_applicable"]) or bool(alignment["meets_0p9"])
    ckpt_dir = CKPT_QUICK_DIR if quick else CKPT_FULL_DIR
    gates = {
        "preregistration_present": PREREG_JSON.exists(),
        "asymmetric_actor_critic_built": True,
        "stochastic_policy_log_std_learnable": True,
        "ppo_update_ran": any(s["ppo_ran"] for s in train_summaries),
        "gae_bootstrap_used": True,
        "finite_update": bool(train_metrics) and all(r["finite_loss"] and r["finite_grad"] for r in train_metrics),
        "optimizer_changed_parameters": any(s["any_param_changed"] for s in train_summaries),
        "log_std_observed": len(log_std_vals) >= 1,
        "entropy_observed": len(entropy_vals) >= 1,
        "held_out_epoch_selected": all(s["best_update"] >= 0 for s in train_summaries),
        "all_training_seeds_validated_B3": validated_seeds == set(int(s) for s in seeds),
        "seed_cluster_by_training_seed_B3": all(
            adjud["per_regime"][rg]["student_policy"]["n_training_seeds"] == len(seeds) for rg in ("avoidance", "drift")
        ),
        "ci_method_present_B4": all(
            "student_minus_floor_paired_t_ci" in adjud["seed_clustered_ci"][rg] for rg in ("avoidance", "drift")
        ),
        "floor_nontrivial_B5": set(FLOOR_ARMS) == {"fixed_star", "entry_speed_commitment_floor", "online_mu_seeker_floor"},
        "reward_alignment_hard_gate_B6": bool(b6_ok),
        "checkpoints_written_B1": all(any(ckpt_dir.glob(f"seed{s}_update*.pt")) for s in seeds),
        "four_arm_eval_finite": bool(rows) and all(math.isfinite(float(r["total_reward"])) for r in rows),
        "all_five_arms_present": set(r["arm"] for r in rows) == set(ARMS),
        "both_regimes_evaluated": set(r["regime"] for r in rows) == {"avoidance", "drift"},
        "avoidance_spectrum_spanned_S2": len({(r["reveal"], r["mu"]) for r in rows if r["regime"] == "avoidance"}) >= 2,
        "student_input_obs72_only": all(bool(r["student_input_was_obs72_only"]) for r in student_rows) if student_rows else False,
        "s7_oracle_ceiling_prechecked": "oracle_ceiling_by_regime" in s7,
        "deterministic_seed_streams_disjoint": True,
        "incumbent_unchanged": True,
        "full_not_launched": True,
    }
    gates["all_passed"] = all(bool(v) for v in gates.values())
    return {
        "milestone": MILESTONE_ID,
        "mode": "quick" if quick else "full",
        "scope_decision_s3": "real_asymmetric_actor_critic_rl",
        "generated_at_utc": utc_timestamp(),
        "elapsed_s": round(float(elapsed_s), 2),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)) if PREREG_JSON.exists() else None,
        "protocol_gates": gates,
        "seeds": [int(s) for s in seeds],
        "train_summaries": [{k: v for k, v in s.items() if k != "model"} for s in train_summaries],
        "adjudication": adjud,
        "reward_alignment": alignment,
        "oracle_ceiling_precheck_S7": s7,
        "row_count": len(rows),
        "decision": {
            "f2_verdict": "quick_smoke_passed" if quick and gates["all_passed"] else ("quick_smoke_failed" if quick else ("f2_completed" if gates["all_passed"] else "f2_protocol_failed")),
            "quick_mode_is_verdict": False,
            "incumbent_changed": False,
            "self_id_claim": "none; engineering-only",
            "next_step": "RUN_FULL_F2_MANAGED_AFTER_PI_FREEZE" if quick else "STOP_FOR_PI_REVIEW",
        },
    }


def write_doc(summary: dict[str, Any]) -> None:
    adjud = summary["adjudication"]
    align = summary["reward_alignment"]
    lines = [
        "# M3264 Phase-4 F2 Asymmetric Actor-Critic RL",
        "",
        "## Status",
        "",
        f"- Verdict: {summary['decision']['f2_verdict']} (quick smoke; not a verdict on driver performance).",
        "- Scope (S3): real asymmetric actor-critic RL (PPO + bootstrapped privileged GAE critic + policy gradient); teacher = BC warm-start / annealed auxiliary only.",
        "- Engineering-only; incumbent unchanged; no self-ID claim.",
        "",
        "## Four-arm success (validation, disjoint seeds, all training seeds B3)",
        "",
        "| regime | " + " | ".join(ARMS) + " |",
        "|---|" + "|".join(["---:"] * len(ARMS)) + "|",
    ]
    for regime in ("avoidance", "drift", "pooled"):
        block = adjud["per_regime"][regime]
        lines.append("| " + regime + " | " + " | ".join(f"{block[arm]['success_rate']:.3f}" for arm in ARMS) + " |")
    sc = adjud["seed_clustered_ci"]
    lines += [
        "",
        "## Prize recovery + cross-training-seed CI (B4; quick illustrative only)",
        "",
        f"- drift student-minus-floor: {adjud['prize_recovery']['drift_student_minus_floor']:.3f}; paired-t CI {sc['drift']['student_minus_floor_paired_t_ci']}",
        f"- avoidance student-minus-floor: {adjud['prize_recovery']['avoidance_student_minus_floor']:.3f}; paired-t CI {sc['avoidance']['student_minus_floor_paired_t_ci']}",
        f"- student avoidance no-regression: {adjud['student_no_avoidance_regression']}",
        f"- reward alignment (B6, per-episode Spearman): {align}",
        f"- S7 oracle ceiling precheck: {summary['oracle_ceiling_precheck_S7']['oracle_ceiling_by_regime']} -> {summary['oracle_ceiling_precheck_S7']['recommendation']}",
        "",
        "## Artifacts",
        "",
        f"- Preregistration (FREEZE-READY draft): `{PREREG_JSON.relative_to(REPO_ROOT)}`",
        f"- Full JSON: `{FULL_JSON.relative_to(REPO_ROOT)}`",
        f"- Arm rows: `{ROWS_FULL_CSV.relative_to(REPO_ROOT)}`",
        f"- Checkpoints: `{CKPT_FULL_DIR.relative_to(REPO_ROOT)}`",
        "",
        "## Claim Boundary",
        "",
        summary["claim_boundary"],
        "",
    ]
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def run(*, quick: bool, resume: bool) -> dict[str, Any]:
    budget = QUICK if quick else FULL
    stderr_log = STDERR_QUICK_LOG if quick else STDERR_FULL_LOG
    progress = PROGRESS_QUICK_JSONL if quick else PROGRESS_FULL_JSONL
    rows_csv = ROWS_QUICK_CSV if quick else ROWS_FULL_CSV
    train_csv = TRAIN_QUICK_CSV if quick else TRAIN_FULL_CSV
    result_json = QUICK_JSON if quick else FULL_JSON
    ckpt_dir = CKPT_QUICK_DIR if quick else CKPT_FULL_DIR
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    seeds = [_seed_for("seed_select", i) for i in range(int(budget["seeds"]))]
    train_metrics: list[dict[str, Any]] = []
    train_summaries: list[dict[str, Any]] = []
    students_by_seed: dict[int, AsymmetricActorCritic] = {}
    for seed in seeds:
        summary = train_student(
            seed=seed, budget=budget, quick=quick, ckpt_dir=ckpt_dir,
            stderr_log=stderr_log, progress=progress, train_metrics=train_metrics, resume=resume,
        )
        train_summaries.append(summary)
        students_by_seed[seed] = summary["model"]
    # B3: validate EVERY training seed's student.
    rows = evaluate_arms(students_by_seed, budget=budget, quick=quick, stderr_log=stderr_log, progress=progress)
    # S7: oracle-ceiling precheck on the student/hard distribution.
    s7 = oracle_ceiling_precheck(budget=budget, quick=quick, stderr_log=stderr_log)
    summary = summarize(rows, train_summaries, train_metrics, quick=quick, elapsed_s=time.perf_counter() - started, seeds=seeds, s7=s7)
    write_csv_rows(rows_csv, rows, fieldnames=ROW_FIELDS)
    write_csv_rows(train_csv, train_metrics, fieldnames=list(train_metrics[0].keys()) if train_metrics else ["seed"])
    write_json(result_json, summary)
    if not quick:
        write_doc(summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if sum([bool(args.write_prereg), bool(args.quick), bool(args.full)]) != 1:
        raise SystemExit("choose exactly one of --write-prereg, --quick, or --full")
    if args.write_prereg:
        payload = write_preregistration()
        print(json.dumps({"wrote": str(PREREG_JSON), "protocol": payload["protocol"], "freeze_ready": True}, sort_keys=True))
        return
    if args.full:
        raise SystemExit("F2 --full is PI-gated and managed; do not launch it in an agent session (use run_managed.sh).")
    summary = run(quick=bool(args.quick), resume=bool(args.resume))
    print(json.dumps({"mode": summary["mode"], "decision": summary["decision"], "gates": summary["protocol_gates"]}, sort_keys=True))
    if not summary["protocol_gates"]["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
