"""Phase-4 F2 LARGE-BATCH GPU PPO training harness (A4).

This is the GPU port of the F2 asymmetric-actor-critic PPO trainer
(``scripts/feasibility_audit/phase4_f2_train.py``). It trains the EXISTING gated
``AsymmetricActorCritic`` (obs72 actor + privileged obs72+priv6 critic) on the
EXISTING ``GPUAutoDriftEnv`` (``src/autodrift/gpu_env.py``) by holding thousands of
parallel environments on one GPU and stepping them in lockstep.

WHAT IS REUSED (imported, NOT reimplemented) from phase4_f2_train.py:
  * ``AsymmetricActorCritic``           -- the model (gated heads default).
  * ``compute_gae``                     -- per-trajectory GAE(lambda) + returns.
  * ``ppo_update``                      -- the clipped-surrogate PPO update with
                                            PER-REGIME advantage normalization.
  * ``bc_update``                       -- BC warm-start (actor MSE + critic pretrain).
  * ``make_drift_teacher`` / ``make_avoidance_teacher`` / ``_privileged_features``
  * ``_drift_scenario`` / ``_avoidance_scenario`` / ``_drift_cell`` / ``_avoidance_grid``
                                            -- the SAME scenario builders the CPU
                                            canonical trainer uses (drift cell mu=0.48;
                                            avoidance over the E2' reveal x mu grid).

HOW THE GPU ROLLOUT IS WIRED TO THE CPU PPO FUNCTIONS (the reuse boundary):
  The rollout is fully on GPU: a batch of N envs is reset to a fixed mix of drift +
  avoidance scenarios, then stepped H times (H = max_steps, so each env runs one full
  episode). Per step we keep tensors obs[H,N,72], act[H,N,3], logp[H,N], value[H,N],
  reward[H,N], done[H,N]. The action + log-prob are produced by REPLICATING exactly
  ``act_stochastic``'s math on GPU (policy_distribution -> sample raw -> tanh squash ->
  _squashed_log_prob), and the value by ``critic_forward(obs72, priv6)``.

  At the rollout boundary we move the buffers to numpy and call the CPU functions AS-IS:
    * ``compute_gae`` runs once PER ENV-COLUMN (each env is one trajectory of length H),
      bootstrapping ``last_value`` from the critic on the env's final obs -- byte-identical
      to what the CPU trainer does per worker trajectory.
    * the flattened (H*N) buffers are assembled into the exact ``ppo_update`` batch dict
      (keys: obs[float32], priv[float32], act[float32], logp[float32], adv, ret, rew, done,
      regime[int]) and ``ppo_update`` is called UNCHANGED. Its internal per-regime advantage
      normalization (drift==1 / avoid==0 masks) then operates on the GPU-collected batch.

WHERE THE MODEL LIVES (deliberate, faithful-reuse decision):
  The ENV (the thousands-of-parallel-dynamics step that is the whole point of the GPU
  port) runs on the GPU. The MODEL runs on the CPU. This is because the reused CPU
  functions ``bc_update`` / ``ppo_update`` build their tensors with
  ``torch.as_tensor(np_array, dtype=torch.float32)`` (no device) -- i.e. they HARDCODE a
  CPU model -- and the brief is "reuse them as-is; do NOT reimplement PPO/GAE/BC". Moving
  the model to GPU would require editing those functions. The actor/critic is a 256-wide
  2-layer MLP; its forward is microseconds and is NOT the bottleneck -- the per-step
  GPU env dynamics (grey-box surrogate + residual MLP over N envs) dominate wall-clock.
  So at the rollout boundary we move obs GPU->CPU for the NN forward and actions CPU->GPU
  for ``env.step``; the env batch stays resident on the GPU the entire rollout. If a
  future revision wants the NN on GPU too, ``ppo_update``/``bc_update`` would need a
  device argument -- a change to the frozen CPU trainer, intentionally not made here.

A4 TODOs handled (documented in gpu_env.py):
  (a) RAMPED DRIFT SUSTAIN TARGET 6->24: the env hardcodes the 24-step success bonus.
      We do NOT modify the env; instead the harness OVERRIDES the drift reward per step
      using ``info['current_controlled']`` / ``info['controlled_drift']`` with a target
      that ramps DRIFT_SUSTAIN_START(6) -> e4.MIN_SUSTAIN_STEPS(24) over
      DRIFT_SUSTAIN_RAMP_FRAC(0.7) of the PPO updates (the exact CPU-trainer schedule
      constants). See ``_recompute_drift_reward``.
  (b) NON-FINITE MASK: drift envs with terminate_on_failure=False keep stepping after a
      NaN; we read ``info['non_finite']`` (sticky per env) and ZERO those transitions'
      advantage AND drop them from the PPO batch so a NaN can never poison the gradient.
  (c) PER-REGIME ADVANTAGE NORM: handed to ``ppo_update`` via the ``regime`` batch field
      (its built-in per-regime normalization); the harness only supplies the labels.

EVAL: every K PPO updates we reset a held-out (disjoint-seed) scenario batch, roll the
DETERMINISTIC actor mean (``actor_forward``) to episode end, and read ``env.success()``
for drift_succ / avoid_succ. The learning curve is (update, drift_succ, avoid_succ, wall).

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f2_gpu_train.py --smoke
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f2_gpu_train.py --full
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from torch.optim import Adam  # noqa: E402

from autodrift.gpu_env import GPUAutoDriftEnv, SCENARIO_DRIFT, SCENARIO_AVOIDANCE  # noqa: E402

# ---- reuse the CPU canonical trainer's model / PPO / BC / teachers / scenarios ----
import phase4_f2_train as f2  # noqa: E402
from phase4_f2_train import (  # noqa: E402
    AsymmetricActorCritic,
    compute_gae,
    ppo_update,
    bc_update,
    make_drift_teacher,
    make_avoidance_teacher,
    _privileged_features,
    _drift_scenario,
    _avoidance_scenario,
    _drift_cell,
    _avoidance_grid,
    _seed_for,
    HUMAN_VIEW_OBS_DIM,
    ACT_DIM,
    PRIV_DIM,
    HIDDEN_SIZE,
    PPO_GAMMA,
    PPO_LAMBDA,
    PPO_LR,
    BC_AUX_COEF_START,
    BC_AUX_COEF_END,
    DRIFT_SUSTAIN_START,
    DRIFT_SUSTAIN_RAMP_FRAC,
)
import phase4_e4_drift_regime_pricing as e4  # noqa: E402

MIN_SUSTAIN_STEPS = int(e4.MIN_SUSTAIN_STEPS)  # 24, the eval success threshold

# Drift reward shaping constants (mirror the env / CPU trainer so the harness-computed
# drift reward matches the env's reward EXCEPT for the ramped success target).
DRIFT_COLLISION_PENALTY = 60.0
DRIFT_PROGRESS_SHAPING = 0.5
DRIFT_SUCCESS_REWARD = 40.0


# ============================================================== scenario batch builder


def _build_scenario_batch(
    *,
    n_envs: int,
    avoid_frac: float,
    drift_difficulty: str,
    drift_max_steps: int,
    avoid_max_steps: int,
    seed_ns: str,
    seed_round: int,
) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray]:
    """Build a mixed drift+avoidance scenario batch (the SAME builders the CPU trainer uses).

    Returns (scenarios, regime_codes[N] in {0=avoid,1=drift via priv convention? -> here
    we use SCENARIO_* codes}, priv6[N,6]). Regime codes follow the env's scenario_type
    convention (0=drift, 1=avoid) AND we separately return the PPO regime label
    (drift==1, avoid==0) used by ppo_update's per-regime advantage norm.

    NOTE on the two regime conventions:
      * env.scenario_type:  drift=0, avoid=1  (gpu_env.SCENARIO_*)
      * ppo_update regime:  drift=1, avoid=0  (matches the CPU trainer's _new_ppo_traj
                            label / the gated-head gate convention)
    We return the PPO regime convention; the env builds its own scenario_type from the
    scenario dict's "scenario_type" field.
    """
    grid = _avoidance_grid(quick=False)  # full E2' reveal x mu grid
    drift_mu = float(_drift_cell()["mu"])
    n_avoid = int(round(n_envs * float(avoid_frac)))
    n_avoid = max(0, min(n_envs, n_avoid))

    scenarios: list[dict[str, Any]] = []
    ppo_regime = np.zeros(n_envs, dtype=np.int64)   # drift==1, avoid==0
    priv = np.zeros((n_envs, PRIV_DIM), dtype=np.float32)

    for i in range(n_envs):
        if i < n_avoid:
            reveal, mu = grid[i % len(grid)]
            seed = _seed_for(seed_ns, seed_round, "avoid", i)
            sc = _avoidance_scenario(seed, max_steps=avoid_max_steps, reveal=float(reveal), mu=float(mu))
            sc["scenario_type"] = "avoidance"
            ppo_regime[i] = 0
            priv[i] = _privileged_features("avoidance", mu=float(mu), reveal=float(reveal))
        else:
            seed = _seed_for(seed_ns, seed_round, "drift", i)
            sc = _drift_scenario(seed, max_steps=drift_max_steps, difficulty=drift_difficulty)
            sc["scenario_type"] = "drift"
            ppo_regime[i] = 1
            priv[i] = _privileged_features("drift", mu=drift_mu, reveal=0.0)
        scenarios.append(sc)
    return scenarios, ppo_regime, priv


# ============================================================== GPU policy sampling


def _sample_cpu(model: AsymmetricActorCritic, obs_cpu: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample (squashed action, squashed log-prob) for a CPU obs batch.

    REPLICATES exactly AsymmetricActorCritic.act_stochastic's math (policy_distribution
    -> sample raw -> tanh squash -> _squashed_log_prob). The model is on CPU (see the
    module docstring's faithful-reuse note); obs is a CPU tensor. Distributionally
    identical to act_stochastic(obs72) (global-RNG dist.sample path).
    """
    with torch.no_grad():
        dist = model.policy_distribution(obs_cpu)
        raw = dist.sample()
        action = torch.tanh(raw)
        log_prob = model._squashed_log_prob(dist, raw, action)
    return action, log_prob


# ============================================================== drift reward re-pricing


def _recompute_drift_reward(
    info: dict[str, torch.Tensor],
    reward: torch.Tensor,
    is_drift: torch.Tensor,
    *,
    sustain_target: int,
    prev_longest: torch.Tensor,
) -> torch.Tensor:
    """Override the drift envs' reward with a RAMPED success target (A4(a)).

    The env hardcodes the +DRIFT_SUCCESS_REWARD bonus at longest_controlled==24. The CPU
    trainer instead ramps that bonus target 6->24 over training. We reconstruct the drift
    reward with the SAME formula the env uses (gpu_env.step), but fire the success bonus
    when the streak first reaches ``sustain_target`` (the ramped value) instead of 24:

        drift_reward = -60*collision
                       + 0.5 * controlled * max(current_controlled, 1)
                       + 40 * (first time longest_controlled reaches sustain_target)

    ``prev_longest`` is longest_controlled BEFORE this step (so we can detect the
    crossing edge exactly once, mirroring the env's drift_success_inc edge logic).
    Avoidance rewards are passed through unchanged.
    """
    controlled = info["controlled_drift"].to(reward.dtype)
    current = info["current_controlled"].to(reward.dtype)
    longest = info["longest_controlled"]
    collision = info["collision"].to(reward.dtype)
    # success bonus fires the step the streak first reaches the (ramped) target.
    reached = (current.long() == int(sustain_target)) & (longest == int(sustain_target)) & (prev_longest < int(sustain_target))
    drift_reward = (
        -DRIFT_COLLISION_PENALTY * collision
        + DRIFT_PROGRESS_SHAPING * controlled * torch.clamp(current, min=1.0)
        + DRIFT_SUCCESS_REWARD * reached.to(reward.dtype)
    )
    return torch.where(is_drift, drift_reward, reward)


def _sustain_target_for_update(ppo_idx: int, total_ppo_updates: int) -> int:
    """Ramp the drift sustain bonus target 6 -> 24 over DRIFT_SUSTAIN_RAMP_FRAC of updates."""
    if total_ppo_updates <= 1:
        return MIN_SUSTAIN_STEPS
    ramp_updates = max(1, int(DRIFT_SUSTAIN_RAMP_FRAC * total_ppo_updates))
    frac = min(1.0, ppo_idx / ramp_updates)
    target = DRIFT_SUSTAIN_START + frac * (MIN_SUSTAIN_STEPS - DRIFT_SUSTAIN_START)
    return int(round(target))


# ============================================================== rollout


@dataclass
class RolloutResult:
    obs: np.ndarray        # [H*N, 72] float32
    act: np.ndarray        # [H*N, 3]  float32
    logp: np.ndarray       # [H*N]     float32
    priv: np.ndarray       # [H*N, 6]  float32
    adv: np.ndarray        # [H*N]     float32
    ret: np.ndarray        # [H*N]     float32
    rew: np.ndarray        # [H*N]     float32
    done: np.ndarray       # [H*N]     float32
    regime: np.ndarray     # [H*N]     int64 (drift==1, avoid==0)
    valid: np.ndarray      # [H*N]     bool   (non-finite-masked transitions dropped)
    env_steps: int
    rollout_seconds: float


@torch.no_grad()
def collect_rollout(
    env: GPUAutoDriftEnv,
    model: AsymmetricActorCritic,
    scenarios: list[dict[str, Any]],
    ppo_regime: np.ndarray,
    priv: np.ndarray,
    *,
    horizon: int,
    device: torch.device,
    sustain_target: int,
) -> RolloutResult:
    """One episodic GPU rollout: reset all N envs, step ``horizon`` times, GAE per env.

    Episodic (reset all -> roll H steps -> GAE) mirrors the CPU trainer's per-worker
    fixed-horizon episode collection. Each env column is ONE trajectory of length H, so
    compute_gae runs per column with last_value bootstrapped from the critic on the env's
    final obs.
    """
    n = len(scenarios)
    priv_cpu = torch.as_tensor(priv, dtype=torch.float32)              # model is on CPU
    is_drift_ppo = torch.as_tensor(ppo_regime == 1, device=device)    # drift==1 (GPU mask)

    t0 = time.perf_counter()
    obs = env.reset(scenarios)  # [N,72] on GPU

    # NN-side buffers (CPU; the model is on CPU). Env-side buffers (GPU; reward recompute
    # reads GPU info tensors). Moved to numpy at the boundary.
    obs_buf = torch.empty(horizon, n, HUMAN_VIEW_OBS_DIM)             # CPU
    act_buf = torch.empty(horizon, n, ACT_DIM)                        # CPU
    logp_buf = torch.empty(horizon, n)                               # CPU
    val_buf = torch.empty(horizon, n)                               # CPU
    rew_buf = torch.empty(horizon, n, device=device)                 # GPU
    done_buf = torch.empty(horizon, n, device=device)                # GPU
    nonfinite_buf = torch.zeros(horizon, n, device=device, dtype=torch.bool)  # GPU

    for h in range(horizon):
        obs_cpu = obs.cpu()
        action_cpu, log_prob = _sample_cpu(model, obs_cpu)
        value = model.critic_forward(obs_cpu, priv_cpu)  # privileged critic value (CPU)
        prev_longest = env.longest_controlled.clone()    # for the ramped-bonus edge (GPU)

        obs_buf[h] = obs_cpu
        act_buf[h] = action_cpu
        logp_buf[h] = log_prob
        val_buf[h] = value

        action_gpu = action_cpu.to(device=device, dtype=env.dtype)
        nxt_obs, reward, terminated, truncated, info = env.step(action_gpu)
        reward = _recompute_drift_reward(
            info, reward, is_drift_ppo, sustain_target=sustain_target, prev_longest=prev_longest,
        )
        done = (terminated | truncated).to(reward.dtype)
        rew_buf[h] = reward
        done_buf[h] = done
        nonfinite_buf[h] = info["non_finite"]
        obs = nxt_obs

    # bootstrap value on the final obs (critic on last obs) -- one per env column.
    last_value = model.critic_forward(obs.cpu(), priv_cpu)  # [N] (CPU)
    if device.type == "cuda":
        torch.cuda.synchronize()
    rollout_seconds = time.perf_counter() - t0

    # ---- to numpy at the reuse boundary; GAE per env column via the CPU function ----
    rewards_np = rew_buf.detach().cpu().numpy().astype(np.float32)      # [H,N]
    values_np = val_buf.detach().numpy().astype(np.float32)             # [H,N]
    dones_np = done_buf.detach().cpu().numpy().astype(np.float32)       # [H,N]
    last_value_np = last_value.detach().numpy().astype(np.float32)      # [N]

    adv_cols = np.empty((horizon, n), dtype=np.float32)
    ret_cols = np.empty((horizon, n), dtype=np.float32)
    for j in range(n):
        adv_j, ret_j = compute_gae(
            rewards_np[:, j], values_np[:, j], dones_np[:, j], float(last_value_np[j]),
            gamma=PPO_GAMMA, lam=PPO_LAMBDA,
        )
        adv_cols[:, j] = adv_j
        ret_cols[:, j] = ret_j

    # non-finite mask: a transition is valid iff its env is finite at that step (sticky).
    valid = (~nonfinite_buf).detach().cpu().numpy()  # [H,N]

    # flatten [H,N,...] -> [H*N,...]
    flat = lambda a: a.reshape(-1, *a.shape[2:])
    obs_np = flat(obs_buf.detach().numpy().astype(np.float32))
    act_np = flat(act_buf.detach().numpy().astype(np.float32))
    logp_np = logp_buf.detach().numpy().astype(np.float32).reshape(-1)
    priv_rep = np.broadcast_to(priv[None, :, :], (horizon, n, PRIV_DIM)).reshape(-1, PRIV_DIM).astype(np.float32)
    regime_rep = np.broadcast_to(ppo_regime[None, :], (horizon, n)).reshape(-1).astype(np.int64)

    return RolloutResult(
        obs=obs_np,
        act=act_np,
        logp=logp_np,
        priv=priv_rep,
        adv=adv_cols.reshape(-1),
        ret=ret_cols.reshape(-1),
        rew=rewards_np.reshape(-1),
        done=dones_np.reshape(-1),
        regime=regime_rep,
        valid=valid.reshape(-1),
        env_steps=int(horizon * n),
        rollout_seconds=float(rollout_seconds),
    )


def _ppo_batch_from_rollout(roll: RolloutResult) -> dict[str, np.ndarray]:
    """Assemble the exact ppo_update batch dict, DROPPING non-finite-masked transitions.

    ppo_update consumes: obs, priv, act, logp, adv, ret, rew, done, regime (numpy).
    We drop rows where ``valid`` is False (A4(b) NaN mask) so the gradient never sees a
    non-finite transition. Per-regime advantage normalization is done INSIDE ppo_update
    from the ``regime`` field (drift==1 / avoid==0).
    """
    m = roll.valid
    return {
        "obs": roll.obs[m],
        "priv": roll.priv[m],
        "act": roll.act[m],
        "logp": roll.logp[m],
        "adv": roll.adv[m],
        "ret": roll.ret[m],
        "rew": roll.rew[m],
        "done": roll.done[m],
        "regime": roll.regime[m],
    }


# ============================================================== BC warm-start (vectorised)


def _vectorised_drift_teacher_action(obs_np: np.ndarray, spec, side: float) -> np.ndarray:
    """Vectorised DriftFeedbackPolicy over a batch of obs72 (drift teacher is obs72-only).

    Mirrors e4.DriftFeedbackPolicy.__call__ / _signed_action EXACTLY but batched:
      vx=20*obs[:,0], vy=12*obs[:,1], yaw=2.5*obs[:,2], beta=atan2(vy,max(|vx|,1e-6));
      steer = -side*steer_ff - beta_gain*(beta - side*target_beta) - yaw_gain*yaw;
      throttle01 = clip(0.18 + throttle_gain*(speed_target - vx), 0, 0.65);
      brake01 = clip(-brake_gain*(speed_target - vx), 0, 0.45);
      action = [clip(steer,-1,1), clip(2*throttle01-1,-1,1), clip(2*brake01-1,-1,1)].
    """
    s = 1.0 if side >= 0.0 else -1.0
    vx = 20.0 * obs_np[:, 0]
    vy = 12.0 * obs_np[:, 1]
    yaw = 2.5 * obs_np[:, 2]
    beta = np.arctan2(vy, np.maximum(np.abs(vx), 1e-6))
    target_beta = s * float(spec.target_beta)
    beta_err = beta - target_beta
    steer = -s * float(spec.steer_ff) - float(spec.beta_gain) * beta_err - float(spec.yaw_gain) * yaw
    speed_err = float(spec.speed_target) - vx
    throttle01 = np.clip(0.18 + float(spec.throttle_gain) * speed_err, 0.0, 0.65)
    brake01 = np.clip(-float(spec.brake_gain) * speed_err, 0.0, 0.45)
    out = np.stack(
        [np.clip(steer, -1.0, 1.0), np.clip(2.0 * throttle01 - 1.0, -1.0, 1.0), np.clip(2.0 * brake01 - 1.0, -1.0, 1.0)],
        axis=1,
    ).astype(np.float32)
    return out


def collect_bc_demos(
    env: GPUAutoDriftEnv,
    *,
    n_envs: int,
    avoid_frac: float,
    drift_difficulty: str,
    drift_max_steps: int,
    avoid_max_steps: int,
    horizon: int,
    device: torch.device,
    seed_ns: str,
) -> dict[str, np.ndarray]:
    """Collect (obs72, teacher_action, priv6) demos on the GPU env, vectorised per regime.

    The DRIFT teacher (DriftFeedbackPolicy) is a pure obs72 feedback law -> fully
    vectorised across all drift envs (one numpy op per step, no per-env loop). The
    AVOIDANCE teacher (E2' RampPolicyController oracle) is stateful + privileged + not
    cheaply vectorisable, so we run it PER avoidance env in numpy on the GPU env's obs
    (B2: only reveal-post frames where the obstacle is in obs72 are kept). Demos are
    collected by driving the GPU env with the teacher actions (on-teacher rollout).
    """
    scenarios, ppo_regime, priv = _build_scenario_batch(
        n_envs=n_envs, avoid_frac=avoid_frac, drift_difficulty=drift_difficulty,
        drift_max_steps=drift_max_steps, avoid_max_steps=avoid_max_steps,
        seed_ns=seed_ns, seed_round=0,
    )
    is_drift = ppo_regime == 1
    is_avoid = ~is_drift
    drift_idx = np.where(is_drift)[0]
    avoid_idx = np.where(is_avoid)[0]

    # drift teacher spec + side (matches make_drift_teacher's binding).
    drift_handle = make_drift_teacher()
    drift_spec = f2._drift_spec(f2.DRIFT_FEEDBACK_NAME)
    drift_side = float(_drift_cell()["initial_beta_rad"])

    # per-avoidance-env teacher instances (stateful oracle), bound to each env's mu/reveal.
    grid = _avoidance_grid(quick=False)
    avoid_teachers: dict[int, Any] = {}
    for i in avoid_idx.tolist():
        reveal, mu = grid[i % len(grid)]
        handle = make_avoidance_teacher(reveal=float(reveal), mu=float(mu))
        avoid_teachers[i] = handle.factory()

    obs = env.reset(scenarios)  # [N,72]
    obs_np_all = obs.detach().cpu().numpy().astype(np.float32)

    demo_obs: list[np.ndarray] = []
    demo_act: list[np.ndarray] = []
    demo_priv: list[np.ndarray] = []

    for h in range(horizon):
        action_np = np.zeros((n_envs, ACT_DIM), dtype=np.float32)
        # --- drift teacher: vectorised ---
        if drift_idx.size:
            action_np[drift_idx] = _vectorised_drift_teacher_action(obs_np_all[drift_idx], drift_spec, drift_side)
            demo_obs.append(obs_np_all[drift_idx].copy())
            demo_act.append(action_np[drift_idx].copy())
            demo_priv.append(priv[drift_idx].copy())
        # --- avoidance teacher: per env (stateful oracle), reveal-post frames only ---
        for i in avoid_idx.tolist():
            a = avoid_teachers[i](h, obs_np_all[i])
            action_np[i] = a
            # reveal-post: obstacle present in obs72 (obs[44] == 1). B2.
            if obs_np_all[i, 44] >= 0.5:
                demo_obs.append(obs_np_all[i][None, :])
                demo_act.append(a[None, :])
                demo_priv.append(priv[i][None, :])

        action_t = torch.as_tensor(action_np, device=device, dtype=torch.float32)
        obs, _r, _term, _trunc, _info = env.step(action_t)
        obs_np_all = obs.detach().cpu().numpy().astype(np.float32)

    if not demo_obs:
        return {
            "frames": np.zeros((0, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
            "priv": np.zeros((0, PRIV_DIM), dtype=np.float32),
            "targets": np.zeros((0, ACT_DIM), dtype=np.float32),
        }
    frames = np.concatenate(demo_obs, axis=0).astype(np.float32)
    targets = np.concatenate(demo_act, axis=0).astype(np.float32)
    priv_demo = np.concatenate(demo_priv, axis=0).astype(np.float32)
    # drop any non-finite demo rows defensively (teacher on a NaN obs).
    good = np.isfinite(frames).all(axis=1) & np.isfinite(targets).all(axis=1)
    return {"frames": frames[good], "priv": priv_demo[good], "targets": targets[good]}


# ============================================================== eval


@torch.no_grad()
def evaluate(
    env: GPUAutoDriftEnv,
    model: AsymmetricActorCritic,
    *,
    n_drift: int,
    n_avoid: int,
    drift_difficulty: str,
    drift_max_steps: int,
    avoid_max_steps: int,
    device: torch.device,
    seed_ns: str,
    seed_round: int,
) -> dict[str, float]:
    """Roll the DETERMINISTIC actor (actor_forward mean) on a held-out batch; read success().

    Drift and avoidance are evaluated at their NATIVE horizons (drift needs E4's 90-step
    episode for a 24-step sustained-drift success; avoidance at its own max_steps). We run
    two separate eval batches (one per regime) so each uses the right horizon.
    """
    out: dict[str, float] = {}
    for regime, n_reg, max_steps in (
        ("drift", n_drift, drift_max_steps),
        ("avoid", n_avoid, avoid_max_steps),
    ):
        if n_reg <= 0:
            out[f"{regime}_succ"] = float("nan")
            continue
        avoid_frac = 0.0 if regime == "drift" else 1.0
        scenarios, _ppo_regime, _priv = _build_scenario_batch(
            n_envs=n_reg, avoid_frac=avoid_frac, drift_difficulty=drift_difficulty,
            drift_max_steps=drift_max_steps, avoid_max_steps=avoid_max_steps,
            seed_ns=f"{seed_ns}-eval-{regime}", seed_round=seed_round,
        )
        obs = env.reset(scenarios)
        for _h in range(max_steps):
            action_cpu = model.actor_forward(obs.cpu())  # deterministic mean (deployment map, CPU model)
            action = action_cpu.to(device=device, dtype=env.dtype)
            obs, _r, _term, _trunc, _info = env.step(action)
        succ = env.success().float().mean().item()
        out[f"{regime}_succ"] = float(succ)
    return out


# ============================================================== training loop


@dataclass
class TrainConfig:
    n_envs: int
    avoid_frac: float
    drift_difficulty: str
    bc_units: int
    bc_epochs: int
    bc_holdout_target: float
    ppo_updates: int
    rollout_horizon: int
    eval_every: int
    eval_drift_units: int
    eval_avoid_units: int
    drift_train_max_steps: int
    avoid_train_max_steps: int
    drift_eval_max_steps: int
    avoid_eval_max_steps: int
    seed: int
    label: str
    curve: list[dict[str, Any]] = field(default_factory=list)


def train(cfg: TrainConfig, *, device: torch.device, env: GPUAutoDriftEnv, verbose: bool = True) -> dict[str, Any]:
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)
    rng = np.random.default_rng(cfg.seed)

    # The model lives on the CPU (see module docstring): the reused bc_update/ppo_update
    # build CPU tensors, and the tiny MLP forward is not the bottleneck -- the GPU env is.
    model = AsymmetricActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM, act_dim=ACT_DIM, priv_dim=PRIV_DIM, hidden_size=HIDDEN_SIZE,
    )
    optimizer = Adam(model.parameters(), lr=PPO_LR)

    wall0 = time.perf_counter()

    # ---------------------------------------------------------------- BC warm-start
    if verbose:
        print(f"[{cfg.label}] collecting BC demos (n_envs={cfg.bc_units}) ...", flush=True)
    bc = collect_bc_demos(
        env, n_envs=cfg.bc_units, avoid_frac=cfg.avoid_frac, drift_difficulty="easy",
        drift_max_steps=cfg.drift_train_max_steps, avoid_max_steps=cfg.avoid_train_max_steps,
        horizon=cfg.drift_train_max_steps, device=device, seed_ns=f"{cfg.label}-bc-{cfg.seed}",
    )
    frames, priv_demo, targets = bc["frames"], bc["priv"], bc["targets"]
    n_demo = frames.shape[0]
    # holdout split for the BC MSE gate.
    holdout_mse = float("nan")
    bc_info: dict[str, Any] = {}
    if n_demo >= 8:
        perm = rng.permutation(n_demo)
        n_hold = max(1, int(0.1 * n_demo))
        hold, tr = perm[:n_hold], perm[n_hold:]
        bc_info = bc_update(
            model, optimizer, frames[tr], priv_demo[tr], targets[tr],
            coef=1.0, epochs=cfg.bc_epochs,
        )
        with torch.no_grad():
            ho = torch.as_tensor(frames[hold], dtype=torch.float32)  # CPU model
            ht = torch.clamp(torch.as_tensor(targets[hold], dtype=torch.float32), -1.0, 1.0)
            holdout_mse = float(torch.mean((model.actor_forward(ho) - ht).pow(2)).item())
    if verbose:
        print(
            f"[{cfg.label}] BC done: demos={n_demo} bc_loss={bc_info.get('bc_loss', float('nan')):.2e} "
            f"holdout_mse={holdout_mse:.2e} (target<{cfg.bc_holdout_target:.0e})",
            flush=True,
        )

    # baseline eval (post-BC, pre-PPO) -- the BC baseline the curve must rise above.
    base = evaluate(
        env, model, n_drift=cfg.eval_drift_units, n_avoid=cfg.eval_avoid_units,
        drift_difficulty=cfg.drift_difficulty, drift_max_steps=cfg.drift_eval_max_steps,
        avoid_max_steps=cfg.avoid_eval_max_steps, device=device, seed_ns=cfg.label, seed_round=10_000,
    )
    base_wall = time.perf_counter() - wall0
    cfg.curve.append({"update": -1, "phase": "bc_baseline", **base, "wall_s": round(base_wall, 2)})
    if verbose:
        print(
            f"[{cfg.label}] BC baseline: drift_succ={base.get('drift_succ', float('nan')):.3f} "
            f"avoid_succ={base.get('avoid_succ', float('nan')):.3f}",
            flush=True,
        )

    # ---------------------------------------------------------------- PPO updates
    per_update_walls: list[float] = []
    throughputs: list[float] = []
    for upd in range(cfg.ppo_updates):
        u0 = time.perf_counter()
        sustain_target = _sustain_target_for_update(upd, cfg.ppo_updates)
        scenarios, ppo_regime, priv = _build_scenario_batch(
            n_envs=cfg.n_envs, avoid_frac=cfg.avoid_frac, drift_difficulty=cfg.drift_difficulty,
            drift_max_steps=cfg.drift_train_max_steps, avoid_max_steps=cfg.avoid_train_max_steps,
            seed_ns=f"{cfg.label}-ppo-{cfg.seed}", seed_round=upd,
        )
        roll = collect_rollout(
            env, model, scenarios, ppo_regime, priv,
            horizon=cfg.rollout_horizon, device=device, sustain_target=sustain_target,
        )
        batch = _ppo_batch_from_rollout(roll)
        # annealed auxiliary BC coefficient (warm-start dominates early, -> 0 late).
        frac = upd / max(1, cfg.ppo_updates - 1)
        bc_aux_coef = BC_AUX_COEF_START + frac * (BC_AUX_COEF_END - BC_AUX_COEF_START)
        bc_aux = None
        if frames.shape[0] > 0 and bc_aux_coef > 0.0:
            # subsample the demos for the aux term (keep it cheap).
            k = min(frames.shape[0], 4096)
            sel = rng.choice(frames.shape[0], size=k, replace=False)
            bc_aux = {"obs": frames[sel], "targets": targets[sel]}
        info = ppo_update(
            model, optimizer, batch,
            bc_aux_coef=float(bc_aux_coef), bc_aux=bc_aux, rng=rng,
        )
        u_wall = time.perf_counter() - u0
        per_update_walls.append(u_wall)
        throughputs.append(roll.env_steps / max(1e-9, roll.rollout_seconds))

        if (upd + 1) % cfg.eval_every == 0 or upd == cfg.ppo_updates - 1:
            ev = evaluate(
                env, model, n_drift=cfg.eval_drift_units, n_avoid=cfg.eval_avoid_units,
                drift_difficulty=cfg.drift_difficulty, drift_max_steps=cfg.drift_eval_max_steps,
                avoid_max_steps=cfg.avoid_eval_max_steps, device=device, seed_ns=cfg.label,
                seed_round=10_000 + upd,
            )
            wall = time.perf_counter() - wall0
            row = {
                "update": upd,
                "phase": "ppo",
                **ev,
                "sustain_target": sustain_target,
                "pg_loss": round(info["pg_loss"], 4),
                "value_loss": round(info["value_loss"], 2),
                "entropy": round(info["entropy"], 4),
                "approx_kl": round(info["approx_kl"], 5),
                "mean_reward": round(info["mean_reward"], 3),
                "finite_loss": bool(info["finite_loss"]),
                "finite_grad": bool(info["finite_grad"]),
                "n_valid": int(batch["obs"].shape[0]),
                "update_wall_s": round(u_wall, 3),
                "wall_s": round(wall, 2),
                "rollout_throughput_steps_s": round(throughputs[-1], 0),
            }
            cfg.curve.append(row)
            if verbose:
                print(
                    f"[{cfg.label}] upd {upd:4d} | drift={ev.get('drift_succ', float('nan')):.3f} "
                    f"avoid={ev.get('avoid_succ', float('nan')):.3f} | tgt={sustain_target:2d} "
                    f"pg={info['pg_loss']:+.3f} vl={info['value_loss']:.1f} kl={info['approx_kl']:+.4f} "
                    f"meanR={info['mean_reward']:+.2f} | {u_wall*1000:.0f}ms "
                    f"thr={throughputs[-1]/1e6:.2f}M st/s",
                    flush=True,
                )

    total_wall = time.perf_counter() - wall0
    final = cfg.curve[-1] if cfg.curve else {}
    return {
        "label": cfg.label,
        "seed": cfg.seed,
        "n_envs": cfg.n_envs,
        "ppo_updates": cfg.ppo_updates,
        "rollout_horizon": cfg.rollout_horizon,
        "bc_demos": int(n_demo),
        "bc_holdout_mse": holdout_mse,
        "bc_baseline_drift_succ": base.get("drift_succ", float("nan")),
        "bc_baseline_avoid_succ": base.get("avoid_succ", float("nan")),
        "final_drift_succ": final.get("drift_succ", float("nan")),
        "final_avoid_succ": final.get("avoid_succ", float("nan")),
        "mean_update_wall_s": float(np.mean(per_update_walls)) if per_update_walls else float("nan"),
        "median_update_wall_s": float(np.median(per_update_walls)) if per_update_walls else float("nan"),
        "mean_rollout_throughput_steps_s": float(np.mean(throughputs)) if throughputs else float("nan"),
        "total_wall_s": float(total_wall),
        "curve": cfg.curve,
        "model": model,
    }


# ============================================================== config presets


def smoke_config(seed: int, n_envs: int = 4096) -> TrainConfig:
    return TrainConfig(
        n_envs=n_envs,
        avoid_frac=0.5,
        drift_difficulty="hard",
        bc_units=2048,
        bc_epochs=200,
        bc_holdout_target=5e-4,
        ppo_updates=40,
        rollout_horizon=90,          # one full drift episode per rollout column
        eval_every=4,
        eval_drift_units=512,
        eval_avoid_units=512,
        drift_train_max_steps=int(e4.MAX_STEPS),   # 90
        avoid_train_max_steps=128,
        drift_eval_max_steps=int(f2.DRIFT_VALIDATION_MAX_STEPS),  # 90
        avoid_eval_max_steps=128,
        seed=seed,
        label="smoke",
    )


def full_config(seed: int, n_envs: int = 8192) -> TrainConfig:
    return TrainConfig(
        n_envs=n_envs,
        avoid_frac=0.5,
        drift_difficulty="hard",
        bc_units=4096,
        bc_epochs=400,
        bc_holdout_target=5e-4,
        ppo_updates=300,
        rollout_horizon=90,
        eval_every=10,
        eval_drift_units=1024,
        eval_avoid_units=1024,
        drift_train_max_steps=int(e4.MAX_STEPS),
        avoid_train_max_steps=128,
        drift_eval_max_steps=int(f2.DRIFT_VALIDATION_MAX_STEPS),
        avoid_eval_max_steps=128,
        seed=seed,
        label="full",
    )


# ============================================================== entrypoint


def build_env(device: torch.device) -> GPUAutoDriftEnv:
    return GPUAutoDriftEnv(device=device, dtype=torch.float32, use_rear_sat_head=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Large-batch GPU PPO trainer for the F2 gated actor-critic.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--smoke", action="store_true", help="short learning-curve smoke run")
    g.add_argument("--full", action="store_true", help="full multi-update training run")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-envs", type=int, default=None)
    ap.add_argument("--ppo-updates", type=int, default=None)
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--out", type=str, default=None, help="optional JSON path for the learning curve")
    ap.add_argument("--save-policy", type=str, default=None,
                    help="optional .pt path to save the trained actor-critic state_dict (for A5 Chrono validation)")
    args = ap.parse_args()

    device = torch.device(args.device if (args.device != "cuda" or torch.cuda.is_available()) else "cpu")
    if device.type != "cuda":
        print(f"WARNING: CUDA unavailable, running on {device} (slow).", flush=True)

    if args.full:
        cfg = full_config(args.seed, n_envs=args.n_envs or 8192)
    else:
        cfg = smoke_config(args.seed, n_envs=args.n_envs or 4096)
    if args.ppo_updates is not None:
        cfg.ppo_updates = int(args.ppo_updates)

    env = build_env(device)
    print(
        f"=== GPU F2 train [{cfg.label}] seed={cfg.seed} n_envs={cfg.n_envs} "
        f"ppo_updates={cfg.ppo_updates} horizon={cfg.rollout_horizon} device={device} ===",
        flush=True,
    )
    result = train(cfg, device=device, env=env, verbose=True)
    model = result.pop("model", None)
    if args.save_policy and model is not None:
        sp = Path(args.save_policy); sp.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "gated": bool(getattr(model, "gated", True)),
                    "seed": cfg.seed, "label": cfg.label,
                    "final_drift_succ": result["final_drift_succ"],
                    "final_avoid_succ": result["final_avoid_succ"]}, sp)
        print(f"saved trained actor-critic -> {sp}", flush=True)

    print("\n=== SUMMARY ===", flush=True)
    print(json.dumps({k: v for k, v in result.items() if k != "curve"}, indent=2, default=str), flush=True)
    print(f"\nBC baseline drift={result['bc_baseline_drift_succ']:.3f} -> "
          f"final drift={result['final_drift_succ']:.3f} "
          f"(avoid {result['bc_baseline_avoid_succ']:.3f} -> {result['final_avoid_succ']:.3f})", flush=True)
    print(f"mean update wall={result['mean_update_wall_s']*1000:.0f}ms  "
          f"total wall={result['total_wall_s']:.1f}s  "
          f"rollout throughput={result['mean_rollout_throughput_steps_s']/1e6:.2f}M steps/s", flush=True)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"wrote learning curve -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
