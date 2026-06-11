"""Audit 2 (pre-launch): self-ID matrix task health + manipulation-effectiveness check.

Anti-M2677 audit: measure, BEFORE any full-budget GPU run, whether the
experiment-1 task surface is interpretable and whether the observation
degradation actually bites. Everything here is minutes-scale CPU measurement;
no number is scientific evidence about the experiment hypotheses.

Phases:
  A. Task health: heuristic / random / short-PPO policies, ~50 episodes each on
     clean and delay-25 (and extra drivability conditions for heuristic),
     terminal-outcome distribution. FAIL flag if any single failure mode >70%
     in a policy x condition cell (M2677 died at 91.78% off_track).
  B. Manipulation check: same seed + same open-loop action sequence, compare
     obs streams clean vs delay-12 vs noise: ego channels 0-8 must differ,
     previous-command 9-11 and geometry 12-71 must be bitwise identical,
     rewards/termination identical (wrapper must not alter dynamics), exact
     k-step delay semantics, determinism across repeated runs.
  C. Drivability: heuristic success rate across clean / delay / noise tiers.
  D. History-information probe: random rollouts, ridge linear probe predicting
     mu / mass_scale from {current degraded frame} vs {current + past 25
     frames} (per-frame channels 0-11), episode-level train/test split,
     R^2 delta = extra information carried by history under each condition.

Output: experiments/feasibility_audit/selfid_task_health_check.json
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv
from autodrift.observation_degradation_wrapper import make_observation_degradation_env
from autodrift.policies import HeuristicPolicy, RandomPolicy

P0_CONFIG = REPO_ROOT / "configs" / "selfid_positive_control_p0_smoke.json"
OUTPUT_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "selfid_task_health_check.json"
PPO_CHECKPOINT = REPO_ROOT / "runs" / "feasibility_audit" / "selfid_task_health_ppo_short" / "checkpoint.pt"

# Design-doc task conditions (T1/T3/T4/T5 plus the extreme combined tier).
CONDITIONS: dict[str, dict[str, float | int]] = {
    "clean": {"delay_steps": 0, "noise_std": 0.0},
    "delay_12": {"delay_steps": 12, "noise_std": 0.0},
    "delay_25": {"delay_steps": 25, "noise_std": 0.0},
    "noise_05": {"delay_steps": 0, "noise_std": 0.05},
    "delay_25_noise_05": {"delay_steps": 25, "noise_std": 0.05},
}

HEALTH_EPISODES = 50
HEALTH_SEED_BASE = 91000
PROBE_SEED_BASE = 92000
PROBE_TARGET_SAMPLES = 2400
PROBE_MAX_EPISODES = 240
PROBE_SAMPLES_PER_EPISODE = 10
PROBE_ALPHAS = (0.1, 1.0, 10.0, 100.0, 1000.0)
HISTORY_FRAMES = 25  # past frames in addition to the current one
FRAME_FEATURE_DIM = 12  # per-frame channels 0-11 (ego response + prev command)
SINGLE_FAILURE_MODE_FAIL_THRESHOLD = 0.70


def load_env_config():
    raw = json.loads(P0_CONFIG.read_text(encoding="utf-8"))
    return build_env_config(raw["env"])


def make_env(env_config, condition: str):
    spec = CONDITIONS[condition]
    return make_observation_degradation_env(
        env_config,
        delay_steps=int(spec["delay_steps"]),
        noise_std=float(spec["noise_std"]),
    )


def outcome_of(info: dict[str, Any], terminated: bool, truncated: bool) -> str:
    if info.get("obstacle_completed", False):
        return "success"
    if terminated:
        return str(info.get("termination_reason") or "terminated_unknown")
    if truncated:
        return "timeout_max_steps"
    return "unknown"


# ---------------------------------------------------------------------------
# Phase A/C: terminal-outcome distributions
# ---------------------------------------------------------------------------


class PPOPolicyAdapter:
    """Deterministic recurrent rollout adapter for a train_ppo checkpoint."""

    def __init__(self, checkpoint_path: Path):
        from autodrift.checkpoints import load_actor_critic_checkpoint

        env_config = load_env_config()
        obs_dim = int(AutoDriftEnv(env_config).observation_space.shape[0])
        self.model, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu", obs_dim=obs_dim)
        self.hidden = None

    def reset(self) -> None:
        self.hidden = None

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        if self.model.is_online_recurrent:
            action, _, _, self.hidden = self.model.act_recurrent(observation, self.hidden, deterministic=True)
        else:
            action, _, _ = self.model.act(observation, deterministic=True)
        return action


def build_policy(name: str, episode_seed: int):
    if name == "heuristic":
        return HeuristicPolicy()
    if name == "random":
        return RandomPolicy(seed=episode_seed)
    if name == "ppo_short":
        policy = PPOPolicyAdapter(PPO_CHECKPOINT)
        policy.reset()
        return policy
    raise ValueError(name)


def run_health_cell(env_config, policy_name: str, condition: str, episodes: int) -> dict[str, Any]:
    env = make_env(env_config, condition)
    outcomes: Counter[str] = Counter()
    lengths: list[int] = []
    returns: list[float] = []
    margins: list[float] = []
    ppo_policy = build_policy("ppo_short", 0) if policy_name == "ppo_short" else None
    for episode in range(episodes):
        seed = HEALTH_SEED_BASE + episode
        if policy_name == "ppo_short":
            policy = ppo_policy
            policy.reset()
        else:
            policy = build_policy(policy_name, seed)
        obs, info = env.reset(seed=seed)
        terminated = truncated = False
        ep_return = 0.0
        steps = 0
        while not (terminated or truncated):
            obs, reward, terminated, truncated, info = env.step(policy.act(obs, info))
            ep_return += float(reward)
            steps += 1
        outcomes[outcome_of(info, terminated, truncated)] += 1
        lengths.append(steps)
        returns.append(ep_return)
        margin = float(info.get("min_clearance_margin", float("nan")))
        if np.isfinite(margin):
            margins.append(margin)
    distribution = {key: count / episodes for key, count in sorted(outcomes.items())}
    failure_modes = {key: value for key, value in distribution.items() if key != "success"}
    dominant_failure = max(failure_modes.items(), key=lambda item: item[1]) if failure_modes else ("none", 0.0)
    return {
        "policy": policy_name,
        "condition": condition,
        "episodes": episodes,
        "outcome_counts": dict(sorted(outcomes.items())),
        "outcome_distribution": distribution,
        "success_rate": distribution.get("success", 0.0),
        "dominant_failure_mode": dominant_failure[0],
        "dominant_failure_rate": dominant_failure[1],
        "single_failure_mode_over_70pct": dominant_failure[1] > SINGLE_FAILURE_MODE_FAIL_THRESHOLD,
        "episode_length_mean": float(np.mean(lengths)),
        "episode_length_p50": float(np.median(lengths)),
        "return_mean": float(np.mean(returns)),
        "min_clearance_margin_p10": float(np.percentile(margins, 10)) if margins else float("nan"),
    }


# ---------------------------------------------------------------------------
# Phase B: manipulation check (same seed, same open-loop action sequence)
# ---------------------------------------------------------------------------


def rollout_fixed_actions(env_config, condition: str, seed: int, actions: np.ndarray):
    env = make_env(env_config, condition)
    obs, info = env.reset(seed=seed)
    observations = [np.asarray(obs, dtype=np.float32).copy()]
    rewards: list[float] = []
    terms: list[bool] = []
    for action in actions:
        obs, reward, terminated, truncated, info = env.step(action)
        observations.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        terms.append(bool(terminated or truncated))
        if terminated or truncated:
            break
    return np.stack(observations), np.asarray(rewards, dtype=np.float64), terms


def manipulation_check(env_config) -> dict[str, Any]:
    rng = np.random.default_rng(20260611)
    # Mild open-loop actions: keep the car alive for the comparison horizon.
    n_actions = 60
    actions = np.stack(
        [
            np.clip(rng.normal(0.0, 0.35, n_actions), -1.0, 1.0),  # steer
            np.clip(rng.normal(0.2, 0.30, n_actions), -1.0, 1.0),  # throttle
            np.full(n_actions, -1.0),  # brake off
        ],
        axis=1,
    ).astype(np.float64)
    seed = 424242

    obs_clean, rew_clean, _ = rollout_fixed_actions(env_config, "clean", seed, actions)
    obs_d12, rew_d12, _ = rollout_fixed_actions(env_config, "delay_12", seed, actions)
    obs_noise, rew_noise, _ = rollout_fixed_actions(env_config, "noise_05", seed, actions)
    obs_d12_rep, _, _ = rollout_fixed_actions(env_config, "delay_12", seed, actions)
    obs_noise_rep, _, _ = rollout_fixed_actions(env_config, "noise_05", seed, actions)

    horizon = min(len(obs_clean), len(obs_d12), len(obs_noise))
    ego = slice(0, 9)
    prev_cmd = slice(9, 12)
    geometry = slice(12, 72)

    def summarize(name: str, obs_a: np.ndarray, obs_b: np.ndarray, rew_a, rew_b, rep: np.ndarray | None,
                  expect_ego_diff_from: int) -> dict[str, Any]:
        h = min(len(obs_a), len(obs_b))
        ego_diff_steps = [t for t in range(h) if not np.array_equal(obs_a[t, ego], obs_b[t, ego])]
        geometry_identical = all(np.array_equal(obs_a[t, geometry], obs_b[t, geometry]) for t in range(h))
        prev_cmd_identical = all(np.array_equal(obs_a[t, prev_cmd], obs_b[t, prev_cmd]) for t in range(h))
        rh = min(len(rew_a), len(rew_b))
        rewards_identical = bool(np.array_equal(rew_a[:rh], rew_b[:rh]))
        ego_max_abs_diff = float(max((np.max(np.abs(obs_a[t, ego] - obs_b[t, ego])) for t in range(h)), default=0.0))
        result = {
            "pair": name,
            "compared_steps": h,
            "ego_0_8_first_diff_step": ego_diff_steps[0] if ego_diff_steps else None,
            "ego_0_8_diff_step_count": len(ego_diff_steps),
            "ego_0_8_expected_diff_from_step": expect_ego_diff_from,
            "ego_0_8_max_abs_diff": ego_max_abs_diff,
            "prev_command_9_11_bitwise_identical": prev_cmd_identical,
            "geometry_12_71_bitwise_identical": geometry_identical,
            "rewards_bitwise_identical": rewards_identical,
        }
        if rep is not None:
            rh2 = min(len(obs_b), len(rep))
            result["repeat_run_bitwise_identical"] = bool(np.array_equal(obs_b[:rh2], rep[:rh2]))
        # Delay must first differ exactly at step 1 (frame 0 is clamped to
        # itself); noise must differ already at the reset frame (step 0).
        diff_ok = bool(ego_diff_steps) and ego_diff_steps[0] == expect_ego_diff_from
        result["pass"] = bool(diff_ok and geometry_identical and prev_cmd_identical and rewards_identical)
        return result

    # Exact delay semantics: degraded ego at t must equal clean raw ego at max(t-12, 0).
    delay_semantics_ok = True
    for t in range(horizon):
        expected = obs_clean[max(t - 12, 0), ego]
        if not np.array_equal(obs_d12[t, ego], expected):
            delay_semantics_ok = False
            break

    # Clean wrapper tier must be an identity on the bare env stream.
    bare_env = AutoDriftEnv(env_config)
    obs_bare, _ = bare_env.reset(seed=seed)
    bare_stream = [np.asarray(obs_bare, dtype=np.float32).copy()]
    for action in actions[: horizon - 1]:
        obs_bare, _, term, trunc, _ = bare_env.step(action)
        bare_stream.append(np.asarray(obs_bare, dtype=np.float32).copy())
        if term or trunc:
            break
    bare_stream = np.stack(bare_stream)
    hb = min(len(bare_stream), len(obs_clean))
    clean_identity = bool(np.array_equal(obs_clean[:hb], bare_stream[:hb]))

    pair_d12 = summarize("clean_vs_delay_12", obs_clean, obs_d12, rew_clean, rew_d12, obs_d12_rep, 1)
    pair_noise = summarize("clean_vs_noise_05", obs_clean, obs_noise, rew_clean, rew_noise, obs_noise_rep, 0)
    return {
        "seed": seed,
        "open_loop_actions": n_actions,
        "compared_steps": horizon,
        "clean_wrapper_identity_vs_bare_env": clean_identity,
        "delay_12_exact_k_step_semantics": delay_semantics_ok,
        "pairs": [pair_d12, pair_noise],
        "pass": bool(
            clean_identity
            and delay_semantics_ok
            and pair_d12["pass"]
            and pair_noise["pass"]
            and pair_d12.get("repeat_run_bitwise_identical", False)
            and pair_noise.get("repeat_run_bitwise_identical", False)
        ),
    }


# ---------------------------------------------------------------------------
# Phase D: linear probe of hidden params from degraded frames
# ---------------------------------------------------------------------------


def collect_probe_samples(env_config, condition: str) -> dict[str, Any]:
    env = make_env(env_config, condition)
    subsample_rng = np.random.default_rng(11)
    x_current: list[np.ndarray] = []
    x_history: list[np.ndarray] = []
    y_mu: list[float] = []
    y_mass: list[float] = []
    group: list[int] = []
    for episode in range(PROBE_MAX_EPISODES):
        seed = PROBE_SEED_BASE + episode
        policy = RandomPolicy(seed=seed)
        obs, info = env.reset(seed=seed)
        frames = [np.asarray(obs[:FRAME_FEATURE_DIM], dtype=np.float64).copy()]
        mu_values = [float(info["mu"])]
        mass_values = [float(info["mass_scale"])]
        terminated = truncated = False
        while not (terminated or truncated):
            obs, _, terminated, truncated, info = env.step(policy.act(obs, info))
            frames.append(np.asarray(obs[:FRAME_FEATURE_DIM], dtype=np.float64).copy())
            mu_values.append(float(info["mu"]))
            mass_values.append(float(info["mass_scale"]))
        usable = list(range(HISTORY_FRAMES, len(frames)))
        if not usable:
            continue
        if len(usable) > PROBE_SAMPLES_PER_EPISODE:
            usable = sorted(
                subsample_rng.choice(usable, size=PROBE_SAMPLES_PER_EPISODE, replace=False).tolist()
            )
        stacked = np.stack(frames)
        for t in usable:
            x_current.append(stacked[t])
            x_history.append(stacked[t - HISTORY_FRAMES : t + 1].reshape(-1))
            y_mu.append(mu_values[t])
            y_mass.append(mass_values[t])
            group.append(episode)
        if len(y_mu) >= PROBE_TARGET_SAMPLES:
            break
    return {
        "episodes": len(set(group)),
        "samples": len(y_mu),
        "x_current": np.stack(x_current) if x_current else np.zeros((0, FRAME_FEATURE_DIM)),
        "x_history": np.stack(x_history) if x_history else np.zeros((0, FRAME_FEATURE_DIM * (HISTORY_FRAMES + 1))),
        "y_mu": np.asarray(y_mu),
        "y_mass": np.asarray(y_mass),
        "group": np.asarray(group),
    }


def _fit_ridge(xt: np.ndarray, yt: np.ndarray, alpha: float) -> np.ndarray:
    gram = xt.T @ xt + alpha * np.eye(xt.shape[1])
    return np.linalg.solve(gram, xt.T @ yt)


def ridge_r2(x: np.ndarray, y: np.ndarray, group: np.ndarray) -> tuple[float, float]:
    """Episode-level 60/20/20 split ridge; alpha picked on validation; test R^2.

    The episode is the effective sample unit (mu / mass are constant within an
    episode except for the friction step), so splits and the alpha selection
    are done at the episode level to avoid leakage.
    """

    unique_groups = np.unique(group)
    rng = np.random.default_rng(7)
    rng.shuffle(unique_groups)
    n = len(unique_groups)
    train_groups = set(unique_groups[: int(0.6 * n)].tolist())
    val_groups = set(unique_groups[int(0.6 * n) : int(0.8 * n)].tolist())
    train_mask = np.asarray([g in train_groups for g in group])
    val_mask = np.asarray([g in val_groups for g in group])
    test_mask = ~(train_mask | val_mask)
    if test_mask.sum() < 30 or train_mask.sum() < 60 or val_mask.sum() < 30:
        return float("nan"), float("nan")
    mean = x[train_mask].mean(axis=0)
    std = x[train_mask].std(axis=0)
    std[std < 1e-9] = 1.0
    xt = (x[train_mask] - mean) / std
    xv = (x[val_mask] - mean) / std
    xs = (x[test_mask] - mean) / std
    y_mean = y[train_mask].mean()
    yt = y[train_mask] - y_mean

    def r2(pred: np.ndarray, target: np.ndarray) -> float:
        ss_res = float(np.sum((target - pred) ** 2))
        ss_tot = float(np.sum((target - target.mean()) ** 2))
        return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    best_alpha, best_val = None, -np.inf
    for alpha in PROBE_ALPHAS:
        weights = _fit_ridge(xt, yt, alpha)
        val_r2 = r2(xv @ weights + y_mean, y[val_mask])
        if np.isfinite(val_r2) and val_r2 > best_val:
            best_alpha, best_val = alpha, val_r2
    if best_alpha is None:
        return float("nan"), float("nan")
    weights = _fit_ridge(xt, yt, best_alpha)
    return r2(xs @ weights + y_mean, y[test_mask]), float(best_alpha)


def probe_condition(env_config, condition: str) -> dict[str, Any]:
    data = collect_probe_samples(env_config, condition)
    result = {
        "condition": condition,
        "episodes": data["episodes"],
        "samples": data["samples"],
        "history_frames": HISTORY_FRAMES,
        "frame_feature_channels": "per-frame indices 0-11 (ego response 0-8 + previous command 9-11)",
    }
    for target_name, y in (("mu", data["y_mu"]), ("mass_scale", data["y_mass"])):
        r2_current, alpha_current = ridge_r2(data["x_current"], y, data["group"])
        r2_history, alpha_history = ridge_r2(data["x_history"], y, data["group"])
        result[f"r2_current_{target_name}"] = r2_current
        result[f"r2_current_plus_hist25_{target_name}"] = r2_history
        result[f"alpha_current_{target_name}"] = alpha_current
        result[f"alpha_hist25_{target_name}"] = alpha_history
        result[f"r2_delta_{target_name}"] = (
            r2_history - r2_current if np.isfinite(r2_history) and np.isfinite(r2_current) else float("nan")
        )
    return result


# ---------------------------------------------------------------------------
# Phase C2: closed-loop divergence diagnostic (does degradation change the
# heuristic's actions at all, even when outcomes match?)
# ---------------------------------------------------------------------------


def closed_loop_divergence(env_config, condition_a: str, condition_b: str, episodes: int) -> dict[str, Any]:
    def run(condition: str, seed: int):
        env = make_env(env_config, condition)
        policy = HeuristicPolicy()
        obs, info = env.reset(seed=seed)
        actions = []
        terminated = truncated = False
        while not (terminated or truncated):
            action = policy.act(obs, info)
            actions.append(np.asarray(action, dtype=np.float64))
            obs, _, terminated, truncated, info = env.step(action)
        return np.stack(actions), outcome_of(info, terminated, truncated), len(actions)

    outcome_diff = 0
    length_diff = 0
    max_divergences = []
    first_diff_steps = []
    for episode in range(episodes):
        seed = HEALTH_SEED_BASE + episode
        actions_a, outcome_a, len_a = run(condition_a, seed)
        actions_b, outcome_b, len_b = run(condition_b, seed)
        h = min(len(actions_a), len(actions_b))
        diffs = np.abs(actions_a[:h] - actions_b[:h])
        max_divergences.append(float(diffs.max()) if h else 0.0)
        first = next((t for t in range(h) if diffs[t].max() > 0), None)
        if first is not None:
            first_diff_steps.append(first)
        if outcome_a != outcome_b:
            outcome_diff += 1
        if len_a != len_b:
            length_diff += 1
    return {
        "pair": f"{condition_a}_vs_{condition_b}",
        "policy": "heuristic",
        "episodes": episodes,
        "episodes_with_action_divergence": len(first_diff_steps),
        "first_action_diff_step_median": float(np.median(first_diff_steps)) if first_diff_steps else float("nan"),
        "max_action_divergence_mean": float(np.mean(max_divergences)),
        "max_action_divergence_max": float(np.max(max_divergences)),
        "episodes_with_different_outcome": outcome_diff,
        "episodes_with_different_length": length_diff,
        "note": (
            "HeuristicPolicy reads ground-truth info fields (lateral_error, heading_error, "
            "speed_ref, beta_target) that bypass the degradation by construction; only its "
            "beta/speed terms use degraded obs channels 0-1."
        ),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    started = time.time()
    env_config = load_env_config()
    report: dict[str, Any] = {
        "audit": "selfid_task_health_check",
        "stage": "pre_launch_feasibility_audit_no_scientific_claim",
        "task_config": str(P0_CONFIG),
        "conditions": {k: dict(v) for k, v in CONDITIONS.items()},
        "criteria": {
            "single_failure_mode_fail_threshold": SINGLE_FAILURE_MODE_FAIL_THRESHOLD,
            "history_probe_min_r2_delta_delay_25": 0.05,
        },
    }

    # Phase B first (cheap, decisive).
    print("[B] manipulation check ...")
    report["manipulation_check"] = manipulation_check(env_config)

    # Phase A + C.
    health_cells: list[dict[str, Any]] = []
    health_plan = [
        ("heuristic", ["clean", "delay_12", "delay_25", "noise_05", "delay_25_noise_05"]),
        ("random", ["clean", "delay_25"]),
        ("ppo_short", ["clean", "delay_25"] if PPO_CHECKPOINT.exists() else []),
    ]
    for policy_name, condition_list in health_plan:
        for condition in condition_list:
            print(f"[A] {policy_name} x {condition} x {HEALTH_EPISODES} episodes ...")
            health_cells.append(run_health_cell(env_config, policy_name, condition, HEALTH_EPISODES))
    report["task_health_cells"] = health_cells
    report["ppo_short_checkpoint_present"] = PPO_CHECKPOINT.exists()
    report["ppo_short_checkpoint"] = str(PPO_CHECKPOINT)

    # Phase C2: closed-loop action divergence for the heuristic.
    print("[C2] closed-loop divergence clean vs delay_25 ...")
    report["closed_loop_divergence"] = [
        closed_loop_divergence(env_config, "clean", "delay_25", HEALTH_EPISODES),
        closed_loop_divergence(env_config, "clean", "noise_05", HEALTH_EPISODES),
    ]

    # Phase D.
    probe_rows = []
    for condition in ["clean", "delay_12", "delay_25", "noise_05", "delay_25_noise_05"]:
        print(f"[D] probe {condition} ...")
        probe_rows.append(probe_condition(env_config, condition))
    report["history_information_probe"] = probe_rows

    report["wallclock_seconds"] = round(time.time() - started, 1)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=False), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON} in {report['wallclock_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
