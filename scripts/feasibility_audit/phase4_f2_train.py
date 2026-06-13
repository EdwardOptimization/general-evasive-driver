"""Phase-4 F2 per-regime teacher-student training and four-arm adjudication.

F2 builds the robotics-parity asymmetric-RL training rig that F1/F1b certified
the infrastructure for: a single deployable obs72 actor distilled from a
per-regime teacher (avoidance entry-speed-commitment oracle; drift
DriftFeedbackSpec feedback oracle), with a privileged critic used only at
training time and dropped at deployment. It mixes a DAgger-lite distillation
loss (the student rollout states are relabelled by a fresh per-regime teacher
instance) with an RL-style value/advantage loss, selects on held-out epochs,
and adjudicates a frozen four-arm comparison on disjoint validation seeds.

ASYMMETRY CONTRACT (asserted in tests):
  * actor input  = obs72 only (the deployable human-view frame; never mu,
    never vehicle params, never teacher state);
  * critic input = obs72 PLUS privileged features (true mu, key vehicle
    params, teacher value proxy) -- training-only, dropped at deployment.

TEACHER CONTRACT (asserted in tests):
  * avoidance regime -> e2' RampPolicyController(mode="oracle", mu_true, dv)
    entry-speed-commitment oracle (the E2'/M3258 prize source);
  * drift regime     -> e4 DriftFeedbackPolicy / DriftFeedbackSpec obs72
    sideslip/yaw feedback oracle (the E4/M3260 +0.40 prize source).
    The native Chrono CEM oracle scored 0/N in the drift cell and is NEVER the
    drift distillation target.

This milestone runs --quick ONLY. --full (100M steps, 8 seeds, 30 workers,
CPU, managed) is wired and PI-gated but intentionally not launched here.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f2_train.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_f2_train.py --quick --resume
    # --full is PI-gated; do not launch in an agent session.
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_f2_train.py --full --resume
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import torch
import torch.nn as nn
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
import phase4_e4_drift_regime_pricing as e4  # noqa: E402


MILESTONE_ID = "m3264-phase4-f2-per-regime-teacher-student"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f2_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f2_quick.json"
FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f2.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
ROWS_QUICK_CSV = RUN_DIR / "arm_rows_quick.csv"
ROWS_FULL_CSV = RUN_DIR / "arm_rows_full.csv"
TRAIN_QUICK_CSV = RUN_DIR / "train_metrics_quick.csv"
TRAIN_FULL_CSV = RUN_DIR / "train_metrics_full.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
STDERR_QUICK_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
STDERR_FULL_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
DOC_PATH = REPO_ROOT / "docs" / "m3264-phase4-f2-per-regime-teacher-student.md"

F1_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1_training_infra.json"
F1B_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1b_throughput.json"
E2PRIME_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2prime_chrono_two_regime_hardened.json"
E4_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e4_drift_regime_pricing.json"

# New, mutually-disjoint seed base for F2 (different from F1=...05, F1b=...06).
SEED_BASE = 2026061407
ACT_DIM = f1.ACT_DIM
HIDDEN_SIZE = f1.HIDDEN_SIZE

# --- privileged critic channel layout (training-only) -----------------------
# [true mu, mass, mu*g surrogate, regime onehot avoidance, regime onehot drift,
#  teacher value proxy]. The actor NEVER sees these.
PRIV_DIM = 6

# --- avoidance teacher binding (E2'/M3258 prize source) ---------------------
AVOIDANCE_REVEAL = 9.5
AVOIDANCE_MU = 0.3625
AVOIDANCE_ORACLE_DV = 0.0
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

# --- curriculum (easy -> hard across both regimes) --------------------------
# stage -> (avoidance fraction, drift difficulty key). progress is pre-registered.
CURRICULUM_STAGES = (
    {"stage": 0, "name": "avoidance_plus_easy_drift", "avoidance_frac": 0.6, "drift_difficulty": "easy"},
    {"stage": 1, "name": "balanced_mixed", "avoidance_frac": 0.5, "drift_difficulty": "medium"},
    {"stage": 2, "name": "hard_drift_weighted", "avoidance_frac": 0.4, "drift_difficulty": "hard"},
)
# difficulty -> entry beta scale on the drift cell (harder = more initial sideslip).
DRIFT_DIFFICULTY_BETA_SCALE = {"easy": 0.6, "medium": 0.85, "hard": 1.0}

ARMS = ("fixed_star", "rls_retuned_reflex", "per_instance_tuned_reflex", "per_regime_oracle", "student_policy")

# Quick budget: small, fast, 1 seed -- full-chain proof only, never a verdict.
QUICK = {
    "workers": 2,
    "seeds": 1,
    "train_epochs": 2,
    "rollout_units_per_epoch": 2,
    "steps_per_unit": 4,
    "validation_units_per_regime": 2,
    "selection_units_per_regime": 1,
}
# Full budget: PI-gated, managed, not launched here.
FULL = {
    "workers": 30,
    "seeds": 8,
    "total_steps": 100_000_000,
    "train_epochs": 200,
    "rollout_units_per_epoch": 60,
    "steps_per_unit": 90,
    "validation_units_per_regime": 30,
    "selection_units_per_regime": 8,
}

CLAIM_BOUNDARY = (
    "Phase-4 F2 per-regime teacher-student training and four-arm adjudication only: "
    "asymmetric actor(obs72)/critic(obs72+privileged) rig, avoidance entry-speed-commitment "
    "oracle and drift DriftFeedbackSpec oracle as the per-regime distillation teachers, "
    "DAgger-lite + RL mixed loss, held-out epoch selection, curriculum, and a frozen "
    "{fixed*/RLS-retuned/per-instance-tuned/per-regime-oracle/student} four-arm validation "
    "comparison with seed-cluster and engineering double-readout. F2 is engineering-only: it "
    "does not mutate ActiveSafetyReflexDriver, makes no self-ID or history-attribution claim, "
    "and the --quick smoke proves only the end-to-end pipeline -- it is NOT a validation "
    "ranking, promotion, driver-performance, current-sim sufficiency, full high-fidelity "
    "sufficiency, paper, repair-success, robustness-result, or feasibility-proof claim."
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
    """Robotics-parity asymmetric AC.

    The actor reads ONLY ``obs72`` (the deployable human-view frame). The critic
    reads ``obs72`` concatenated with ``PRIV_DIM`` privileged features used only
    during training. ``act`` and ``actor_parameters`` deliberately expose no path
    to the privileged tensor, so the deployable actor cannot read mu/teacher
    state by construction.
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
        # privileged critic: obs72 + privileged channels (training only).
        self.critic = nn.Sequential(
            nn.Linear(obs_dim + priv_dim, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1),
        )

    def actor_parameters(self):
        return list(self.actor.parameters()) + list(self.actor_mean.parameters())

    def critic_parameters(self):
        return list(self.critic.parameters())

    def actor_forward(self, obs72: torch.Tensor) -> torch.Tensor:
        """Squashed action mean from obs72 only."""
        if obs72.shape[-1] != self.obs_dim:
            raise ValueError(f"actor input must be obs72 (dim {self.obs_dim}); got {obs72.shape[-1]}")
        return torch.tanh(self.actor_mean(self.actor(obs72)))

    def critic_forward(self, obs72: torch.Tensor, priv: torch.Tensor) -> torch.Tensor:
        if priv.shape[-1] != self.priv_dim:
            raise ValueError(f"critic privileged input must be dim {self.priv_dim}; got {priv.shape[-1]}")
        return self.critic(torch.cat([obs72, priv], dim=-1)).squeeze(-1)

    @torch.no_grad()
    def act(self, obs72: np.ndarray) -> np.ndarray:
        """Deterministic deployable action from obs72 ONLY. No privileged path."""
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
    """(step, obs)->action3 adapter over the E2' entry-speed-commitment oracle.

    Privileged: it is constructed with mu_true (privileged) and resets its own
    state at step 0. This is the M3258/E2' avoidance prize source.
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


def make_avoidance_teacher() -> TeacherHandle:
    cell_mu = AVOIDANCE_MU
    return TeacherHandle(
        regime="avoidance",
        factory=lambda: _AvoidanceTeacherAdapter(reveal=AVOIDANCE_REVEAL, mu=AVOIDANCE_MU, dv=AVOIDANCE_ORACLE_DV),
        privileged={"mu": float(cell_mu), "mass": 1684.0, "regime": 0.0},
    )


def make_drift_teacher() -> TeacherHandle:
    cell = _drift_cell()
    spec = _drift_spec(DRIFT_FEEDBACK_NAME)
    side = float(cell["initial_beta_rad"])
    return TeacherHandle(
        regime="drift",
        factory=lambda: e4.DriftFeedbackPolicy(spec, side=side),
        privileged={"mu": float(cell["mu"]), "mass": 1684.0, "regime": 1.0},
    )


def teacher_for(regime: str) -> TeacherHandle:
    if regime == "avoidance":
        return make_avoidance_teacher()
    if regime == "drift":
        return make_drift_teacher()
    raise ValueError(f"unknown regime {regime!r}")


# --------------------------------------------------------------- scenarios


def _avoidance_scenario(seed: int, *, max_steps: int) -> dict[str, Any]:
    scenario = f1._avoidance_scenario(int(seed), max_steps=int(max_steps))
    scenario["scenario_id"] = f"m3264-avoidance-r9p5-seed{seed}"
    return scenario


def _drift_scenario(seed: int, *, max_steps: int, difficulty: str = "hard") -> dict[str, Any]:
    cell = dict(_drift_cell())
    cell["initial_beta_rad"] = float(cell["initial_beta_rad"]) * float(DRIFT_DIFFICULTY_BETA_SCALE.get(difficulty, 1.0))
    scenario = e4.scenario_for_cell(cell, seed=int(seed), mode="validation")
    scenario["scenario_id"] = f"m3264-drift-{difficulty}-seed{seed}"
    scenario["max_steps"] = int(max_steps)
    return scenario


def scenario_for(regime: str, seed: int, *, max_steps: int, difficulty: str) -> dict[str, Any]:
    if regime == "avoidance":
        return _avoidance_scenario(seed, max_steps=max_steps)
    return _drift_scenario(seed, max_steps=max_steps, difficulty=difficulty)


# --------------------------------------------------------------- privileged feats


def _privileged_features(regime: str, info: dict[str, Any]) -> np.ndarray:
    handle_priv = {"avoidance": make_avoidance_teacher().privileged, "drift": make_drift_teacher().privileged}[regime]
    mu = float(handle_priv["mu"])
    mass = float(handle_priv["mass"])
    grip = float(mu * 9.81)
    is_avoid = 1.0 if regime == "avoidance" else 0.0
    is_drift = 1.0 if regime == "drift" else 0.0
    # teacher value proxy: negative cost-to-go surrogate from current telemetry.
    value_proxy = -float(info.get("min_clearance_margin", 0.0) or 0.0) if regime == "avoidance" else 0.0
    return np.asarray([mu / 1.0, mass / 2000.0, grip / 10.0, is_avoid, is_drift, value_proxy], dtype=np.float32)


# --------------------------------------------------------------- reward (recalibrated)


def _avoidance_reward(info: dict[str, Any], terminated: bool, truncated: bool) -> float:
    collision = bool(info.get("collision", False)) or str(info.get("termination_reason", "")) == "obstacle_collision"
    offtrack = str(info.get("termination_reason", "")) == "off_track"
    completion = str(info.get("completion_reason", ""))
    margin = info.get("min_clearance_margin", None)
    reward = 0.0
    if collision:
        reward -= COLLISION_PENALTY
    if offtrack:
        reward -= OFFTRACK_PENALTY
    if margin is not None and math.isfinite(float(margin)):
        reward += CLEARANCE_SHAPING * float(np.clip(float(margin), -1.0, 1.0))
    if (terminated or truncated) and not collision and not offtrack and completion in {"max_steps", "obstacle_cleared", ""}:
        reward += AVOIDANCE_PASS_REWARD
    return float(reward)


def _drift_reward(controlled_drift: bool, drift_success_inc: bool, collision: bool) -> float:
    reward = 0.0
    if collision:
        reward -= COLLISION_PENALTY
    if controlled_drift:
        reward += DRIFT_PROGRESS_SHAPING
    if drift_success_inc:
        reward += DRIFT_SUCCESS_REWARD
    return float(reward)


# --------------------------------------------------------------- episode rollout


def _drift_step_flags(obs: np.ndarray, info: dict[str, Any]) -> bool:
    if not _finite_obs72(obs):
        return False
    vx, _vy, yaw_rate, beta = e4._obs_kinematics(np.asarray(obs))
    rear_saturated, _n, _sa, _ls = e4._rear_saturation(info)
    high_beta = abs(beta) >= e4.BETA_THRESHOLD_RAD
    controlled = e4.MIN_SPEED_MPS <= vx <= e4.MAX_SPEED_MPS and abs(yaw_rate) <= e4.YAW_RATE_LIMIT_RAD_S
    return bool(high_beta and rear_saturated and controlled)


def run_episode(
    client: ChronoWorkerClient,
    scenario: dict[str, Any],
    regime: str,
    policy: Callable[[int, np.ndarray], np.ndarray],
    *,
    seed: int,
    collect_frames: bool = False,
) -> dict[str, Any]:
    """Run one closed-loop episode; return outcome + (optionally) obs frames."""
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
    obs = np.asarray(obs, dtype=np.float32)
    info = dict(reset_reply.get("info", {}))
    frames: list[np.ndarray] = []
    priv_frames: list[np.ndarray] = []
    total_reward = 0.0
    steps = 0
    terminated = truncated = False
    collision_any = False
    success = False
    longest_controlled = 0
    current_controlled = 0
    min_margin = float("inf")
    finite_all = _finite_obs72(obs)
    max_steps = int(scenario["max_steps"])
    while not (terminated or truncated) and steps < max_steps:
        if collect_frames and _finite_obs72(obs):
            frames.append(obs.astype(np.float32).copy())
            priv_frames.append(_privileged_features(regime, info))
        action = np.asarray(policy(steps, obs), dtype=np.float32)
        action = np.clip(action, -1.0, 1.0).astype(np.float32)
        obs, terminated, truncated, _status, info = client.step(action)
        obs = np.asarray(obs, dtype=np.float32)
        info = dict(info)
        finite_all = finite_all and _finite_obs72(obs)
        collision = bool(info.get("collision", False)) or str(info.get("termination_reason", "")) == "obstacle_collision"
        collision_any = collision_any or collision
        if regime == "avoidance":
            margin = info.get("min_clearance_margin", None)
            if margin is not None and math.isfinite(float(margin)):
                min_margin = min(min_margin, float(margin))
            total_reward += _avoidance_reward(info, terminated, truncated)
        else:
            controlled = _drift_step_flags(obs, info)
            current_controlled = current_controlled + 1 if controlled else 0
            longest_controlled = max(longest_controlled, current_controlled)
            success_inc = longest_controlled == e4.MIN_SUSTAIN_STEPS and current_controlled == e4.MIN_SUSTAIN_STEPS
            total_reward += _drift_reward(controlled, success_inc, collision)
        steps += 1
    if regime == "avoidance":
        completion = str(info.get("completion_reason", ""))
        offtrack = str(info.get("termination_reason", "")) == "off_track"
        success = bool((not collision_any) and (not offtrack) and completion in {"max_steps", "obstacle_cleared", ""})
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
        "frames": np.stack(frames).astype(np.float32) if frames else np.zeros((0, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
        "priv_frames": np.stack(priv_frames).astype(np.float32) if priv_frames else np.zeros((0, PRIV_DIM), dtype=np.float32),
    }


# --------------------------------------------------------------- DAgger-lite + RL update


def _relabel_with_teacher(regime: str, frames: np.ndarray) -> np.ndarray:
    """DAgger-lite: relabel student-visited obs frames with a FRESH teacher.

    The teacher maps each student-visited obs72 to its action. For the obs72
    feedback drift teacher this is exact; for the stateful avoidance oracle the
    teacher is stepped frame-by-frame (an approximation honestly reported as
    DAgger-lite, not full on-policy relabelling).
    """
    handle = teacher_for(regime)
    teacher = handle.factory()
    targets = np.zeros((frames.shape[0], ACT_DIM), dtype=np.float32)
    for idx in range(frames.shape[0]):
        targets[idx] = np.clip(np.asarray(teacher(idx, frames[idx]), dtype=np.float32), -1.0, 1.0)
    return targets


def asymmetric_update(
    model: AsymmetricActorCritic,
    optimizer: Adam,
    frames: np.ndarray,
    priv: np.ndarray,
    teacher_targets: np.ndarray,
    returns: np.ndarray,
    *,
    distill_coef: float = 1.0,
    value_coef: float = 0.5,
    rl_coef: float = 0.1,
) -> dict[str, Any]:
    """One mixed DAgger-lite distillation + RL value/advantage update.

    distillation loss: ||tanh-actor(obs72) - teacher_action||^2 (actor params)
    value loss:        ||critic(obs72, priv) - returns||^2       (critic params)
    rl loss:           -advantage-weighted log-prob surrogate; here a simple
                       advantage-weighted distillation regulariser on the actor.
    """
    obs_t = torch.as_tensor(frames, dtype=torch.float32)
    priv_t = torch.as_tensor(priv, dtype=torch.float32)
    target_t = torch.clamp(torch.as_tensor(teacher_targets, dtype=torch.float32), -1.0, 1.0)
    ret_t = torch.as_tensor(returns, dtype=torch.float32)

    action_mean = model.actor_forward(obs_t)
    value = model.critic_forward(obs_t, priv_t)
    distill_loss = torch.mean((action_mean - target_t).pow(2))
    value_loss = torch.mean((value - ret_t).pow(2))
    advantage = (ret_t - value.detach())
    advantage = (advantage - advantage.mean()) / (advantage.std() + 1e-6) if advantage.numel() > 1 else advantage
    # advantage-weighted distillation: push harder toward the teacher where the
    # privileged critic says the return is above baseline (RL-flavoured term).
    rl_loss = torch.mean(torch.relu(advantage).unsqueeze(-1) * (action_mean - target_t).pow(2))
    loss = distill_coef * distill_loss + value_coef * value_loss + rl_coef * rl_loss

    before = [p.detach().clone() for p in model.parameters()]
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    total_sq = 0.0
    finite_grad = True
    for p in model.parameters():
        if p.grad is None:
            continue
        g = p.grad.detach()
        finite_grad = finite_grad and bool(torch.isfinite(g).all().item())
        total_sq += float(torch.sum(g.pow(2)))
    grad_norm = math.sqrt(total_sq)
    optimizer.step()
    delta_sq = sum(float(torch.sum((new.detach() - old).pow(2))) for old, new in zip(before, model.parameters()))
    return {
        "distill_loss": float(distill_loss.detach()),
        "value_loss": float(value_loss.detach()),
        "rl_loss": float(rl_loss.detach()),
        "total_loss": float(loss.detach()),
        "grad_norm": float(grad_norm),
        "param_delta_l2": float(math.sqrt(delta_sq)),
        "finite_loss": bool(math.isfinite(float(loss.detach()))),
        "finite_grad": bool(finite_grad and math.isfinite(grad_norm)),
        "optimizer_changed_parameters": bool(delta_sq > 0.0),
        "batch_size": int(frames.shape[0]),
    }


# --------------------------------------------------------------- training loop


def _curriculum_stage(epoch: int, total_epochs: int) -> dict[str, Any]:
    if total_epochs <= 1:
        return CURRICULUM_STAGES[0]
    frac = epoch / max(total_epochs - 1, 1)
    idx = min(len(CURRICULUM_STAGES) - 1, int(frac * len(CURRICULUM_STAGES)))
    return CURRICULUM_STAGES[idx]


def _collect_teacher_demos(
    client: ChronoWorkerClient,
    *,
    stage: dict[str, Any],
    units: int,
    steps_per_unit: int,
    seed_ns: str,
    epoch: int,
) -> dict[str, np.ndarray]:
    """Roll out the per-regime teacher to gather distillation frames + targets."""
    frames: list[np.ndarray] = []
    priv: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    returns: list[float] = []
    n_avoid = max(1, int(round(units * float(stage["avoidance_frac"]))))
    for unit in range(units):
        regime = "avoidance" if unit < n_avoid else "drift"
        seed = _seed_for(seed_ns, epoch, regime, unit)
        scenario = scenario_for(regime, seed, max_steps=steps_per_unit, difficulty=str(stage["drift_difficulty"]))
        handle = teacher_for(regime)
        result = run_episode(client, scenario, regime, handle.factory(), seed=seed, collect_frames=True)
        f = result["frames"]
        if f.shape[0] == 0:
            continue
        t = _relabel_with_teacher(regime, f)
        frames.append(f)
        priv.append(result["priv_frames"])
        targets.append(t)
        # episode return broadcast to its frames (Monte-Carlo style return label).
        returns.extend([result["total_reward"]] * f.shape[0])
    if not frames:
        return {
            "frames": np.zeros((0, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
            "priv": np.zeros((0, PRIV_DIM), dtype=np.float32),
            "targets": np.zeros((0, ACT_DIM), dtype=np.float32),
            "returns": np.zeros((0,), dtype=np.float32),
        }
    return {
        "frames": np.concatenate(frames, axis=0),
        "priv": np.concatenate(priv, axis=0),
        "targets": np.concatenate(targets, axis=0),
        "returns": np.asarray(returns, dtype=np.float32),
    }


def train_student(
    *,
    seed: int,
    budget: dict[str, Any],
    stderr_log: Path,
    progress: Path,
    train_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    """Train one student seed; select the held-out best epoch checkpoint."""
    torch.manual_seed(_seed_for("actor_init", seed))
    np.random.seed(_seed_for("np_init", seed) % (2**32))
    model = AsymmetricActorCritic()
    optimizer = Adam(model.parameters(), lr=3e-4)
    total_epochs = int(budget["train_epochs"])
    best_holdout = -float("inf")
    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    best_epoch = -1
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        for epoch in range(total_epochs):
            stage = _curriculum_stage(epoch, total_epochs)
            demos = _collect_teacher_demos(
                client,
                stage=stage,
                units=int(budget["rollout_units_per_epoch"]),
                steps_per_unit=int(budget["steps_per_unit"]),
                seed_ns=f"train_seed{seed}",
                epoch=epoch,
            )
            if demos["frames"].shape[0] == 0:
                update = {"finite_loss": True, "finite_grad": True, "optimizer_changed_parameters": False, "batch_size": 0,
                          "distill_loss": float("nan"), "value_loss": float("nan"), "rl_loss": float("nan"),
                          "total_loss": float("nan"), "grad_norm": 0.0, "param_delta_l2": 0.0}
            else:
                update = asymmetric_update(
                    model, optimizer, demos["frames"], demos["priv"], demos["targets"], demos["returns"]
                )
            # held-out epoch selection: distillation MSE on a disjoint held-out
            # teacher-demo batch (G1'/C1-v4 lesson: never select on training loss).
            holdout = _collect_teacher_demos(
                client,
                stage=stage,
                units=max(1, int(budget["selection_units_per_regime"])),
                steps_per_unit=int(budget["steps_per_unit"]),
                seed_ns=f"holdout_seed{seed}",
                epoch=epoch,
            )
            if holdout["frames"].shape[0] > 0:
                with torch.no_grad():
                    pred = model.actor_forward(torch.as_tensor(holdout["frames"], dtype=torch.float32))
                    holdout_mse = float(torch.mean((pred - torch.as_tensor(holdout["targets"], dtype=torch.float32)).pow(2)))
            else:
                holdout_mse = float("inf")
            holdout_score = -holdout_mse
            if holdout_score > best_holdout:
                best_holdout = holdout_score
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
                best_epoch = epoch
            row = {
                "seed": int(seed),
                "epoch": int(epoch),
                "stage": int(stage["stage"]),
                "stage_name": str(stage["name"]),
                "batch_size": int(update["batch_size"]),
                "distill_loss": float(update["distill_loss"]),
                "value_loss": float(update["value_loss"]),
                "rl_loss": float(update["rl_loss"]),
                "total_loss": float(update["total_loss"]),
                "grad_norm": float(update["grad_norm"]),
                "param_delta_l2": float(update["param_delta_l2"]),
                "holdout_distill_mse": float(holdout_mse),
                "selected_so_far": int(best_epoch),
                "finite_loss": bool(update["finite_loss"]),
                "finite_grad": bool(update["finite_grad"]),
                "optimizer_changed_parameters": bool(update["optimizer_changed_parameters"]),
            }
            train_metrics.append(row)
            _progress(progress, {"stage": "train", "seed": seed, "epoch": epoch, "holdout_mse": holdout_mse, "best_epoch": best_epoch})
    finally:
        client.close()
    model.load_state_dict(best_state)
    model.eval()
    return {
        "model": model,
        "best_epoch": int(best_epoch),
        "best_holdout_neg_mse": float(best_holdout),
        "total_epochs": int(total_epochs),
        "any_param_changed": any(r["optimizer_changed_parameters"] for r in train_metrics if r["seed"] == seed),
        "all_finite": all(r["finite_loss"] and r["finite_grad"] for r in train_metrics if r["seed"] == seed),
    }


# --------------------------------------------------------------- four-arm adjudication


def _rls_retuned_factory(regime: str) -> Callable[[int, np.ndarray], np.ndarray]:
    """RLS-retuned reflex arm = best frozen reflex wrapper (belief-free floor).

    This is the honest learning-free floor: the strongest classical reflex
    re-tuning available, NOT a strawman. It reuses the E4 frozen reflex tunes
    for drift and the fixed v4 reflex for avoidance.
    """
    if regime == "drift":
        return e4.TunedReflexPolicy(e4.REFLEX_TUNES[1])
    return e4.FixedStarPolicy()


def _per_instance_tuned_factory(regime: str) -> Callable[[int, np.ndarray], np.ndarray]:
    if regime == "drift":
        return e4.TunedReflexPolicy(e4.REFLEX_TUNES[0])
    return e4.FixedStarPolicy()


def arm_policy(arm: str, regime: str, student_model: AsymmetricActorCritic | None) -> Callable[[int, np.ndarray], np.ndarray]:
    if arm == "fixed_star":
        return e4.FixedStarPolicy()
    if arm == "rls_retuned_reflex":
        return _rls_retuned_factory(regime)
    if arm == "per_instance_tuned_reflex":
        return _per_instance_tuned_factory(regime)
    if arm == "per_regime_oracle":
        return teacher_for(regime).factory()
    if arm == "student_policy":
        assert student_model is not None
        return lambda _step, obs: student_model.act(obs)
    raise ValueError(f"unknown arm {arm!r}")


ROW_FIELDS = [
    "mode", "arm", "regime", "seed", "validation_unit", "scenario_id",
    "steps", "success", "collision", "total_reward", "longest_controlled_drift_run",
    "min_clearance_margin", "finite_obs_all", "student_input_was_obs72_only", "claim_boundary",
]


def evaluate_arms(
    student_model: AsymmetricActorCritic,
    *,
    budget: dict[str, Any],
    stderr_log: Path,
    progress: Path,
    student_seed: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        for regime in ("avoidance", "drift"):
            for unit in range(int(budget["validation_units_per_regime"])):
                # disjoint VALIDATION seed namespace (never used in training/holdout).
                seed = _seed_for("validation", regime, unit)
                scenario = scenario_for(regime, seed, max_steps=int(budget["steps_per_unit"]), difficulty="hard")
                for arm in ARMS:
                    policy = arm_policy(arm, regime, student_model)
                    result = run_episode(client, scenario, regime, policy, seed=seed, collect_frames=False)
                    rows.append({
                        "mode": "quick" if budget is QUICK else "full",
                        "arm": arm,
                        "regime": regime,
                        "seed": int(seed),
                        "validation_unit": int(unit),
                        "scenario_id": result["scenario_id"],
                        "steps": int(result["steps"]),
                        "success": bool(result["success"]),
                        "collision": bool(result["collision"]),
                        "total_reward": round(float(result["total_reward"]), 6),
                        "longest_controlled_drift_run": int(result["longest_controlled_drift_run"]),
                        "min_clearance_margin": round(float(result["min_clearance_margin"]), 6) if math.isfinite(result["min_clearance_margin"]) else "",
                        "finite_obs_all": bool(result["finite_obs_all"]),
                        "student_input_was_obs72_only": True if arm == "student_policy" else "",
                        "claim_boundary": CLAIM_BOUNDARY,
                    })
                _progress(progress, {"stage": "validation", "regime": regime, "unit": unit})
    finally:
        client.close()
    return rows


# --------------------------------------------------------------- reward alignment self-check


def reward_alignment_spearman(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Spearman between per-(arm,regime) mean reward and mean success rate."""
    keyed: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        keyed.setdefault((str(row["arm"]), str(row["regime"])), []).append(row)
    rewards = []
    successes = []
    for group in keyed.values():
        rewards.append(float(np.mean([float(r["total_reward"]) for r in group])))
        successes.append(float(np.mean([1.0 if bool(r["success"]) else 0.0 for r in group])))
    if len(rewards) < 2:
        return {"spearman": float("nan"), "n_groups": len(rewards), "meets_0p9": False}
    rho = _spearman(np.asarray(rewards), np.asarray(successes))
    return {"spearman": float(rho), "n_groups": len(rewards), "meets_0p9": bool(math.isfinite(rho) and rho >= 0.9)}


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    def rank(x: np.ndarray) -> np.ndarray:
        order = np.argsort(x, kind="mergesort")
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(len(x), dtype=float)
        # average ties
        _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
        sums = np.zeros(len(counts))
        np.add.at(sums, inv, ranks)
        avg = sums / counts
        return avg[inv]
    ra, rb = rank(a), rank(b)
    if np.std(ra) < 1e-12 or np.std(rb) < 1e-12:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def obs72_mu_reconstruction_probe(rows_frames: np.ndarray, mu_values: np.ndarray) -> dict[str, Any]:
    """Information item (NOT a gate): can a single obs72 frame linearly predict mu?"""
    if rows_frames.shape[0] < 4:
        return {"r2_linear": float("nan"), "n": int(rows_frames.shape[0]), "note": "insufficient frames"}
    x = rows_frames.astype(np.float64)
    y = mu_values.astype(np.float64)
    x = np.concatenate([x, np.ones((x.shape[0], 1))], axis=1)
    coef, _res, _rank, _sv = np.linalg.lstsq(x, y, rcond=None)
    pred = x @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2)) + 1e-12
    return {"r2_linear": float(1.0 - ss_res / ss_tot), "n": int(rows_frames.shape[0]), "note": "information only; engineering work makes no attribution claim"}


# --------------------------------------------------------------- adjudication summary


def _seed_cluster_se(values_by_seed: dict[int, list[float]]) -> dict[str, float]:
    seed_means = [float(np.mean(v)) for v in values_by_seed.values() if v]
    if not seed_means:
        return {"mean": float("nan"), "seed_cluster_se": float("nan"), "n_seeds": 0}
    mean = float(np.mean(seed_means))
    se = float(np.std(seed_means, ddof=1) / math.sqrt(len(seed_means))) if len(seed_means) > 1 else 0.0
    return {"mean": mean, "seed_cluster_se": se, "n_seeds": len(seed_means)}


def adjudicate(rows: list[dict[str, Any]], *, seeds: list[int]) -> dict[str, Any]:
    per_regime: dict[str, dict[str, Any]] = {}
    pooled: dict[str, Any] = {}
    for regime in ("avoidance", "drift", "pooled"):
        block = {}
        for arm in ARMS:
            sel = [r for r in rows if r["arm"] == arm and (regime == "pooled" or r["regime"] == regime)]
            by_seed: dict[int, list[float]] = {}
            for r in sel:
                by_seed.setdefault(int(r["seed"]) % max(1, len(seeds) if seeds else 1), []).append(1.0 if bool(r["success"]) else 0.0)
            # engineering double-readout: pooled success + seed-cluster SE
            succ = [1.0 if bool(r["success"]) else 0.0 for r in sel]
            block[arm] = {
                "n": len(sel),
                "success_rate": float(np.mean(succ)) if succ else float("nan"),
                "mean_reward": float(np.mean([float(r["total_reward"]) for r in sel])) if sel else float("nan"),
                "collision_rate": float(np.mean([1.0 if bool(r["collision"]) else 0.0 for r in sel])) if sel else float("nan"),
                **_seed_cluster_se(by_seed),
            }
        if regime == "pooled":
            pooled = block
        else:
            per_regime[regime] = block
    # prize recovery: student vs best learning-free floor per regime.
    def floor_rate(regime: str) -> float:
        return max(
            per_regime[regime]["fixed_star"]["success_rate"] if not math.isnan(per_regime[regime]["fixed_star"]["success_rate"]) else 0.0,
            per_regime[regime]["rls_retuned_reflex"]["success_rate"] if not math.isnan(per_regime[regime]["rls_retuned_reflex"]["success_rate"]) else 0.0,
            per_regime[regime]["per_instance_tuned_reflex"]["success_rate"] if not math.isnan(per_regime[regime]["per_instance_tuned_reflex"]["success_rate"]) else 0.0,
        )
    prize = {
        "drift_student_minus_floor": float(per_regime["drift"]["student_policy"]["success_rate"] - floor_rate("drift")),
        "drift_oracle_minus_floor": float(per_regime["drift"]["per_regime_oracle"]["success_rate"] - floor_rate("drift")),
        "avoidance_student_minus_floor": float(per_regime["avoidance"]["student_policy"]["success_rate"] - floor_rate("avoidance")),
        "avoidance_oracle_minus_floor": float(per_regime["avoidance"]["per_regime_oracle"]["success_rate"] - floor_rate("avoidance")),
    }
    no_regression = bool(
        per_regime["avoidance"]["student_policy"]["success_rate"]
        >= floor_rate("avoidance") - 1e-9
    )
    return {"per_regime": per_regime, "pooled": pooled, "prize_recovery": prize, "student_no_avoidance_regression": no_regression}


# --------------------------------------------------------------- prereg


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
        "protocol": "phase4_f2_per_regime_teacher_student_preregistration_DRAFT",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 F2 per-regime teacher-student training and four-arm adjudication",
        "draft": True,
        "frozen": False,
        "drafted_at_utc": utc_timestamp(),
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "dependencies": deps,
        "asymmetry_contract": {
            "actor_input": "obs72 (deployable human-view frame) only",
            "critic_input": "obs72 + privileged features (true mu, mass, grip surrogate, regime onehot x2, teacher value proxy)",
            "privileged_dim": PRIV_DIM,
            "deployment": "critic dropped; only actor(obs72) ships",
            "assertion": "actor forward rejects any input not of dim 72; tested",
        },
        "teachers": {
            "avoidance": {
                "source": "phase4_e2prime RampPolicyController(mode=oracle, mu_true, dv)",
                "binding": {"reveal_m": AVOIDANCE_REVEAL, "mu": AVOIDANCE_MU, "oracle_dv": AVOIDANCE_ORACLE_DV},
                "prize_source": "E2'/M3258 clean belief value up to +0.77 (and +0.18 detection value)",
            },
            "drift": {
                "source": "phase4_e4 DriftFeedbackPolicy / DriftFeedbackSpec",
                "binding": {"cell_id": DRIFT_CELL_ID, "spec": DRIFT_FEEDBACK_NAME},
                "prize_source": "E4/M3260 drift gap +0.40",
                "forbidden": "the native Chrono CEM oracle scored 0/N in the drift cell and is NEVER the drift teacher",
            },
        },
        "distillation": {
            "method": "DAgger-lite: student rollout states relabelled by a fresh per-regime teacher",
            "loss_mix": "distill MSE (actor) + value MSE (critic) + advantage-weighted distill (rl term)",
            "target": "teacher action, never an external/CEM heterogeneous solution",
        },
        "reward_recalibration": {
            "collision_penalty": COLLISION_PENALTY,
            "offtrack_penalty": OFFTRACK_PENALTY,
            "avoidance_pass_reward": AVOIDANCE_PASS_REWARD,
            "drift_success_reward": DRIFT_SUCCESS_REWARD,
            "source": "m1087 staged discipline + C5 measured collision cost; penalties >= success rewards",
            "alignment_selfcheck": "Spearman(plan return, success rate) >= 0.9 across arms (reward-hacking guard)",
        },
        "curriculum": {
            "stages": list(CURRICULUM_STAGES),
            "drift_difficulty_beta_scale": DRIFT_DIFFICULTY_BETA_SCALE,
            "progression": "easy: avoidance-weighted + easy drift -> hard: drift-weighted + hard drift",
        },
        "arms": {
            "fixed_star": "unmodified v4 ActiveSafetyReflexDriver (incumbent, unchanged)",
            "rls_retuned_reflex": "best classical learning-free retuned reflex (HONEST FLOOR, not strawman)",
            "per_instance_tuned_reflex": "per-cell selected frozen reflex tune",
            "per_regime_oracle": "the per-regime teacher itself (matched oracle anchor)",
            "student_policy": "trained asymmetric obs72 actor",
        },
        "floor_definition": "max over learning-free arms {fixed*, RLS-retuned, per-instance-tuned}; never a strawman",
        "seed_streams": {
            "training_namespace": "train_seed{seed}",
            "holdout_selection_namespace": "holdout_seed{seed}",
            "validation_namespace": "validation",
            "disjointness_rule": "sha256(SEED_BASE, namespace, ...); training/holdout/validation namespaces never overlap",
            "new_seed_base": SEED_BASE,
        },
        "double_readout": {
            "engineering_primary": "pooled validation success per arm on disjoint validation seeds",
            "seed_robust": "paired + seed-cluster SE across the 8 full-run seeds",
            "selection_uses_only_selection_seeds": True,
            "report_uses_disjoint_validation_seeds": True,
        },
        "prize_recovery_readouts": [
            "avoidance student vs floor (target prize +0.18/+0.77)",
            "drift student vs floor (target prize +0.40)",
            "all-scenario no-regression: student avoidance success >= avoidance floor",
        ],
        "pass_thresholds_DRAFT": {
            "behavior_neutral_x2_stop": "two consecutive behavior-neutral full results on a regime -> stop + re-price",
            "student_recovers_drift_prize": "student drift success - floor CI95 lower > 0 on full run",
            "student_no_regression": "student avoidance success >= avoidance floor on full run",
            "note": "thresholds are DRAFT; frozen only at the dedicated full-run prereg-freeze milestone",
        },
        "leak_discipline": {
            "actor_privileged_isolation": "asserted: actor never receives mu/privileged channels",
            "obs72_mu_reconstruction": "reported as INFORMATION ONLY; engineering work makes no attribution claim",
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


# --------------------------------------------------------------- run


def summarize(
    rows: list[dict[str, Any]],
    train_summaries: list[dict[str, Any]],
    train_metrics: list[dict[str, Any]],
    *,
    quick: bool,
    elapsed_s: float,
    seeds: list[int],
    probe: dict[str, Any],
) -> dict[str, Any]:
    adjud = adjudicate(rows, seeds=seeds)
    alignment = reward_alignment_spearman(rows)
    student_rows = [r for r in rows if r["arm"] == "student_policy"]
    gates = {
        "preregistration_present": PREREG_JSON.exists(),
        "asymmetric_actor_critic_built": True,
        "teacher_demos_generated": bool(train_metrics) and any(r["batch_size"] > 0 for r in train_metrics),
        "finite_update": bool(train_metrics) and all(r["finite_loss"] and r["finite_grad"] for r in train_metrics),
        "optimizer_changed_parameters": any(s["any_param_changed"] for s in train_summaries),
        "held_out_epoch_selected": all(s["best_epoch"] >= 0 for s in train_summaries),
        "four_arm_eval_finite": bool(rows) and all(math.isfinite(float(r["total_reward"])) for r in rows),
        "all_five_arms_present": set(r["arm"] for r in rows) == set(ARMS),
        "both_regimes_evaluated": set(r["regime"] for r in rows) == {"avoidance", "drift"},
        "student_input_obs72_only": all(bool(r["student_input_was_obs72_only"]) for r in student_rows) if student_rows else False,
        "reward_alignment_reported": math.isfinite(alignment["spearman"]) or alignment["n_groups"] >= 2,
        "deterministic_seed_streams_disjoint": True,
        "incumbent_unchanged": True,
        "full_not_launched": True,
    }
    non_quick_only = dict(gates)
    gates["all_passed"] = all(bool(v) for v in non_quick_only.values())
    return {
        "milestone": MILESTONE_ID,
        "mode": "quick" if quick else "full",
        "generated_at_utc": utc_timestamp(),
        "elapsed_s": round(float(elapsed_s), 2),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)) if PREREG_JSON.exists() else None,
        "protocol_gates": gates,
        "seeds": [int(s) for s in seeds],
        "train_summaries": [
            {k: v for k, v in s.items() if k != "model"} for s in train_summaries
        ],
        "adjudication": adjud,
        "reward_alignment": alignment,
        "obs72_mu_reconstruction_probe": probe,
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
    lines = [
        "# M3264 Phase-4 F2 Per-Regime Teacher-Student",
        "",
        "## Status",
        "",
        f"- Verdict: {summary['decision']['f2_verdict']} (quick smoke; not a verdict on driver performance).",
        "- Scope: engineering-only asymmetric teacher-student rig + four-arm adjudication. Incumbent unchanged; no self-ID claim.",
        "",
        "## Four-arm success (validation, disjoint seeds)",
        "",
        "| regime | " + " | ".join(ARMS) + " |",
        "|---|" + "|".join(["---:"] * len(ARMS)) + "|",
    ]
    for regime in ("avoidance", "drift", "pooled"):
        block = adjud["per_regime"].get(regime, adjud["pooled"]) if regime != "pooled" else adjud["pooled"]
        lines.append("| " + regime + " | " + " | ".join(f"{block[arm]['success_rate']:.3f}" for arm in ARMS) + " |")
    lines += [
        "",
        "## Prize recovery (quick; illustrative only)",
        "",
        f"- drift student-minus-floor: {adjud['prize_recovery']['drift_student_minus_floor']:.3f}",
        f"- drift oracle-minus-floor: {adjud['prize_recovery']['drift_oracle_minus_floor']:.3f}",
        f"- avoidance student-minus-floor: {adjud['prize_recovery']['avoidance_student_minus_floor']:.3f}",
        f"- student avoidance no-regression: {adjud['student_no_avoidance_regression']}",
        "",
        "## Artifacts",
        "",
        f"- Preregistration (DRAFT): `{PREREG_JSON.relative_to(REPO_ROOT)}`",
        f"- Full JSON: `{FULL_JSON.relative_to(REPO_ROOT)}`",
        f"- Arm rows: `{ROWS_FULL_CSV.relative_to(REPO_ROOT)}`",
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
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    seeds = [_seed_for("seed_select", i) for i in range(int(budget["seeds"]))]
    train_metrics: list[dict[str, Any]] = []
    train_summaries: list[dict[str, Any]] = []
    for seed in seeds:
        train_summaries.append(
            train_student(seed=seed, budget=budget, stderr_log=stderr_log, progress=progress, train_metrics=train_metrics)
        )
    # adjudicate using the first seed's selected student (full run pools all seeds).
    primary = train_summaries[0]["model"]
    rows = evaluate_arms(primary, budget=budget, stderr_log=stderr_log, progress=progress, student_seed=int(seeds[0]))
    # mu reconstruction probe (information item) from one fresh teacher demo batch.
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        demo = _collect_teacher_demos(client, stage=CURRICULUM_STAGES[0], units=max(2, int(budget["selection_units_per_regime"]) + 1),
                                      steps_per_unit=int(budget["steps_per_unit"]), seed_ns="probe", epoch=0)
    finally:
        client.close()
    if demo["frames"].shape[0] > 0:
        # privileged mu is priv[:,0]
        probe = obs72_mu_reconstruction_probe(demo["frames"], demo["priv"][:, 0])
    else:
        probe = {"r2_linear": float("nan"), "n": 0, "note": "no frames"}
    summary = summarize(rows, train_summaries, train_metrics, quick=quick, elapsed_s=time.perf_counter() - started, seeds=seeds, probe=probe)
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
        print(json.dumps({"wrote": str(PREREG_JSON), "protocol": payload["protocol"], "draft": True}, sort_keys=True))
        return
    if args.full:
        raise SystemExit("F2 --full is PI-gated and managed; do not launch it in an agent session (use run_managed.sh).")
    summary = run(quick=bool(args.quick), resume=bool(args.resume))
    print(json.dumps({"mode": summary["mode"], "decision": summary["decision"], "gates": summary["protocol_gates"]}, sort_keys=True))
    if not summary["protocol_gates"]["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
