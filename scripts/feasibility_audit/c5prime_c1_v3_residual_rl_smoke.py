"""C1-v3 residual-RL smoke on the frozen v4 reflex base.

This is a protocol smoke for the PI-reopened nonlocal C1 route. It does not
attempt a stage-1 result. The only claim is that a bounded residual policy can
be trained for one PPO update on frozen C5-prime rows while the incumbent v4
reflex remains frozen and unmodified.

Run:
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v3_residual_rl_smoke.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v3_residual_rl_smoke.py --quick
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import json
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.optim import Adam

REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5_reflex_degradation as c5  # noqa: E402
import c5prime_c1_oracle_bc_warmstart as c1  # noqa: E402
from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver  # noqa: E402
from autodrift.artifacts import utc_timestamp, write_json  # noqa: E402
from autodrift.env import AutoDriftEnv  # noqa: E402
from autodrift.evaluate import outcome_bucket_from_info  # noqa: E402
from autodrift.train_ppo import ActorCritic, compute_gae_vectorized  # noqa: E402


MILESTONE_ID = "m3244-c1-v3-residual-rl-smoke"
PREREG_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v3_residual_rl_smoke_prereg.json"
RESULTS_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v3_residual_rl_smoke.json"
RUN_DIR = REPO / "runs" / "feasibility_audit" / "c5prime_c1_v3_residual_rl_smoke" / "quick"
SOURCE_ROWS_CSV = REPO / "runs" / "feasibility_audit" / "c5prime_target_consolidation" / "episode_rows.csv"
SOURCE_PRICING_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_target_consolidation.json"

OBS_DIM = 72
ACT_DIM = 3
SEED_BASE = 20260901
TARGET_LEVELS = ("S1", "S2", "S3")
SURFACE = "T_limit"
DELTA_MAX = np.array([0.35, 0.45, 0.45], dtype=np.float32)
PASS_REWARD = 40.0
COLLISION_PENALTY = 60.0
QUICK_TOTAL_STEPS = 1024

CLAIM_BOUNDARY = (
    "C1-v3 residual-RL smoke only: a bounded residual policy is trained for one "
    "short PPO update on frozen C5-prime rows, with action=clip(frozen_v4(obs)+delta). "
    "No incumbent mutation, validation ranking, driver-performance claim, "
    "high-fidelity sufficiency claim, repair-success claim, feasibility-proof, "
    "paper claim, or self-ID claim."
)


def read_source_rows() -> list[dict[str, str]]:
    with SOURCE_ROWS_CSV.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def row_id(row: dict[str, str]) -> str:
    return f"{row['level']}-inst{int(row['instance']):02d}-seed{int(row['eval_seed'])}"


def select_smoke_rows(rows_per_level: int = 2) -> list[dict[str, str]]:
    rows = read_source_rows()
    selected: list[dict[str, str]] = []
    for level in TARGET_LEVELS:
        candidates = [
            row
            for row in rows
            if row["level"] == level
            and row["surface"] == SURFACE
            and row["oracle_solved"] == "True"
            and row["v4_pertuned_outcome"] != "success"
            and row["oracle_by"].startswith("structured:")
        ]
        candidates.sort(key=lambda row: (int(row["instance"]), int(row["eval_seed"])))
        if len(candidates) < rows_per_level:
            raise RuntimeError(f"not enough C5-prime structural-gap rows for {level}: {len(candidates)}")
        selected.extend(candidates[:rows_per_level])
    return selected


def env_from_source_row(row: dict[str, str]) -> AutoDriftEnv:
    cfg = c5.row_env_config(
        row["surface"],
        float(row["v"]),
        float(row["mu"]),
        float(row["s_arc"]),
        float(row["hw"]),
        c1._veh_from_row(row),
    )
    obstacle = replace(
        cfg.obstacle,
        pass_reward=PASS_REWARD,
        collision_penalty=COLLISION_PENALTY,
    )
    return AutoDriftEnv(replace(cfg, obstacle=obstacle))


def compose_residual_action(
    base_action: np.ndarray,
    residual_unit_action: np.ndarray,
    delta_max: np.ndarray = DELTA_MAX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    base = np.asarray(base_action, dtype=np.float32)
    residual = np.asarray(residual_unit_action, dtype=np.float32)
    delta_scale = np.asarray(delta_max, dtype=np.float32)
    if base.shape != (ACT_DIM,):
        raise ValueError(f"base action shape must be {(ACT_DIM,)}, got {base.shape}")
    if residual.shape != (ACT_DIM,):
        raise ValueError(f"residual action shape must be {(ACT_DIM,)}, got {residual.shape}")
    if delta_scale.shape != (ACT_DIM,):
        raise ValueError(f"delta_max shape must be {(ACT_DIM,)}, got {delta_scale.shape}")
    clipped_residual = np.clip(residual, -1.0, 1.0).astype(np.float32)
    delta = clipped_residual * delta_scale
    final = np.clip(base + delta, -1.0, 1.0).astype(np.float32)
    return base.astype(np.float32), delta.astype(np.float32), final


class C5PrimeResidualPool:
    def __init__(self, rows: list[dict[str, str]]):
        if not rows:
            raise ValueError("rows cannot be empty")
        self.rows = rows
        self.index = 0
        self.env: AutoDriftEnv | None = None
        self.current_row: dict[str, str] | None = None

    def reset(self) -> tuple[np.ndarray, dict[str, Any]]:
        self.close()
        self.current_row = self.rows[self.index % len(self.rows)]
        self.index += 1
        self.env = env_from_source_row(self.current_row)
        obs, info = self.env.reset(seed=int(self.current_row["eval_seed"]))
        info = dict(info)
        info["row_id"] = row_id(self.current_row)
        info["level"] = self.current_row["level"]
        info["eval_seed"] = int(self.current_row["eval_seed"])
        return np.asarray(obs, dtype=np.float32), info

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if self.env is None or self.current_row is None:
            raise RuntimeError("pool.step called before reset")
        obs, reward, terminated, truncated, info = self.env.step(action)
        info = dict(info)
        info["row_id"] = row_id(self.current_row)
        info["level"] = self.current_row["level"]
        info["eval_seed"] = int(self.current_row["eval_seed"])
        return np.asarray(obs, dtype=np.float32), float(reward), bool(terminated), bool(truncated), info

    def close(self) -> None:
        if self.env is not None:
            self.env.close()
            self.env = None


def preregistration_payload() -> dict[str, Any]:
    return {
        "protocol": "c5prime_c1_v3_residual_rl_smoke",
        "milestone_id": MILESTONE_ID,
        "roadmap_unit": "C1-v3 residual RL on the reflex base",
        "frozen_at_utc": "2026-06-12T00:00:00Z",
        "frozen_before_any_c1_v3_rollout": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "pricing_basis": {
            "primary_artifact": str(SOURCE_PRICING_JSON.relative_to(REPO)),
            "priced_gap_floor": 0.1597,
            "threshold": 0.15,
            "gap_meets_threshold": True,
            "qualified_cells": ["S1/T_limit", "S2/T_limit", "S3/T_limit"],
            "secondary_chrono_direction": "M3231 D1b direction-positive; CP-2 precondition met",
        },
        "seed_discipline": {
            "smoke_seed_base": SEED_BASE,
            "training_rollout_rows": "first two deterministic A3 structural-gap rows per qualified level S1/S2/S3",
            "stage1_training_seeds": "not used in smoke; future stage-1 must use >=8 seeds disjoint from this smoke base",
        },
        "residual_architecture": {
            "base_policy": "ActiveSafetyReflexDriver incumbent v4, frozen",
            "action_rule": "clip(base_action + delta_max * tanh(policy_raw_action), -1, 1)",
            "delta_max": DELTA_MAX.tolist(),
            "hidden_size": 64,
            "actor_encoder": "mlp",
            "recoverable_set_gating": "not enabled in M3244 smoke; must be separately priced/smoked before deployable use",
        },
        "reward_recalibration": {
            "pass_reward": PASS_REWARD,
            "collision_penalty": COLLISION_PENALTY,
            "source": "P1 reward recalibration 40/60 from the earlier task-spec measurements",
        },
        "quick_gates": [
            "run exactly 1024 environment steps on frozen C5-prime rows",
            "exercise all three qualified T-limit levels S1/S2/S3",
            "all observations, base actions, residual deltas, final actions, rewards, advantages, and losses finite",
            "final actions remain inside the original action bounds",
            "at least one PPO optimizer update changes model parameters by a finite nonzero amount",
            "write checkpoint and metrics artifacts",
        ],
        "future_stage1_not_admitted_by_smoke": [
            "stage-1 must pre-register fixed v4, v4_pertuned, v4+residual, and oracle readouts before full run",
            "stage-1 primary remains v4+residual minus v4_pertuned per cell with paired CIs",
            "PASS requires recapturing >=50 percent of the A3 gap in >=2 of 3 qualified T-limit cells",
            "behavior-neutral x2 triggers stop and synthesis",
        ],
    }


def write_preregistration() -> dict[str, Any]:
    payload = preregistration_payload()
    write_json(PREREG_JSON, payload)
    return payload


def load_preregistration() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise FileNotFoundError(f"missing preregistration {PREREG_JSON}")
    payload = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    if not payload.get("frozen_before_any_c1_v3_rollout"):
        raise ValueError(f"{PREREG_JSON} is not marked frozen_before_any_c1_v3_rollout")
    return payload


def _parameters_l2_delta(before: list[torch.Tensor], model: nn.Module) -> float:
    total = 0.0
    for old, new in zip(before, model.parameters(), strict=True):
        diff = new.detach().cpu() - old
        total += float(torch.square(diff).sum().item())
    return float(total ** 0.5)


def _evaluate_loss(
    model: ActorCritic,
    obs_t: torch.Tensor,
    act_t: torch.Tensor,
    old_logp_t: torch.Tensor,
    adv_t: torch.Tensor,
    ret_t: torch.Tensor,
    clip_coef: float,
    vf_coef: float,
    ent_coef: float,
) -> torch.Tensor:
    logp, entropy_values, value = model.evaluate_actions(obs_t, act_t)
    ratio = torch.exp(logp - old_logp_t)
    pg_loss_1 = -adv_t * ratio
    pg_loss_2 = -adv_t * torch.clamp(ratio, 1.0 - clip_coef, 1.0 + clip_coef)
    pg_loss = torch.max(pg_loss_1, pg_loss_2).mean()
    value_loss = 0.5 * torch.square(value - ret_t).mean()
    entropy = entropy_values.mean()
    return pg_loss + vf_coef * value_loss - ent_coef * entropy


def run_quick() -> dict[str, Any]:
    prereg = load_preregistration()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    np.random.seed(SEED_BASE)
    torch.manual_seed(SEED_BASE)
    t0 = time.time()

    rows = select_smoke_rows(rows_per_level=2)
    pool = C5PrimeResidualPool(rows)
    base_driver = ActiveSafetyReflexDriver()
    device = torch.device("cpu")
    model = ActorCritic(
        obs_dim=OBS_DIM,
        act_dim=ACT_DIM,
        hidden_size=64,
        log_std_init=-1.2,
        log_std_min=-5.0,
        log_std_max=-0.6,
        actor_encoder="mlp",
    ).to(device)
    optimizer = Adam(model.parameters(), lr=3e-4)
    before_params = [param.detach().cpu().clone() for param in model.parameters()]

    obs, reset_info = pool.reset()
    obs_rows = np.zeros((QUICK_TOTAL_STEPS, OBS_DIM), dtype=np.float32)
    residual_rows = np.zeros((QUICK_TOTAL_STEPS, ACT_DIM), dtype=np.float32)
    base_rows = np.zeros((QUICK_TOTAL_STEPS, ACT_DIM), dtype=np.float32)
    delta_rows = np.zeros((QUICK_TOTAL_STEPS, ACT_DIM), dtype=np.float32)
    final_rows = np.zeros((QUICK_TOTAL_STEPS, ACT_DIM), dtype=np.float32)
    logp_rows = np.zeros(QUICK_TOTAL_STEPS, dtype=np.float32)
    reward_rows = np.zeros(QUICK_TOTAL_STEPS, dtype=np.float32)
    done_rows = np.zeros(QUICK_TOTAL_STEPS, dtype=np.float32)
    value_rows = np.zeros(QUICK_TOTAL_STEPS, dtype=np.float32)

    episode_return = 0.0
    episode_length = 0
    episode_rows: list[dict[str, Any]] = []
    row_ids_seen = {str(reset_info["row_id"])}
    levels_seen = {str(reset_info["level"])}

    try:
        for step in range(QUICK_TOTAL_STEPS):
            if obs.shape != (OBS_DIM,) or not np.all(np.isfinite(obs)):
                raise RuntimeError(f"bad observation at step {step}: shape={obs.shape}")
            residual_action, logp, value = model.act(obs)
            base_action = base_driver.act(obs)
            base_action, delta_action, final_action = compose_residual_action(base_action, residual_action)
            next_obs, reward, terminated, truncated, info = pool.step(final_action)
            done = terminated or truncated

            obs_rows[step] = obs
            residual_rows[step] = residual_action
            base_rows[step] = base_action
            delta_rows[step] = delta_action
            final_rows[step] = final_action
            logp_rows[step] = logp
            reward_rows[step] = reward
            done_rows[step] = float(done)
            value_rows[step] = value

            row_ids_seen.add(str(info["row_id"]))
            levels_seen.add(str(info["level"]))
            episode_return += reward
            episode_length += 1
            if done:
                bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
                episode_rows.append(
                    {
                        "row_id": str(info["row_id"]),
                        "level": str(info["level"]),
                        "eval_seed": int(info["eval_seed"]),
                        "outcome_bucket": bucket,
                        "termination_reason": str(info.get("termination_reason", "") or ""),
                        "return": float(episode_return),
                        "length": int(episode_length),
                    }
                )
                obs, reset_info = pool.reset()
                row_ids_seen.add(str(reset_info["row_id"]))
                levels_seen.add(str(reset_info["level"]))
                episode_return = 0.0
                episode_length = 0
            else:
                obs = next_obs
    finally:
        pool.close()

    with torch.no_grad():
        _, last_value_t = model.forward(torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0))
    advantages, returns = compute_gae_vectorized(
        reward_rows[:, None],
        done_rows[:, None],
        value_rows[:, None],
        last_value_t.detach().cpu().numpy().astype(np.float32),
        gamma=0.99,
        gae_lambda=0.95,
    )
    advantages = advantages[:, 0]
    returns = returns[:, 0]
    advantages = (advantages - float(advantages.mean())) / (float(advantages.std()) + 1e-8)

    obs_t = torch.as_tensor(obs_rows, dtype=torch.float32, device=device)
    act_t = torch.as_tensor(residual_rows, dtype=torch.float32, device=device)
    old_logp_t = torch.as_tensor(logp_rows, dtype=torch.float32, device=device)
    adv_t = torch.as_tensor(advantages, dtype=torch.float32, device=device)
    ret_t = torch.as_tensor(returns, dtype=torch.float32, device=device)

    loss_values: list[float] = []
    indices = np.arange(QUICK_TOTAL_STEPS)
    for _ in range(2):
        np.random.shuffle(indices)
        for start in range(0, QUICK_TOTAL_STEPS, 256):
            mb = indices[start : start + 256]
            loss = _evaluate_loss(
                model,
                obs_t[mb],
                act_t[mb],
                old_logp_t[mb],
                adv_t[mb],
                ret_t[mb],
                clip_coef=0.2,
                vf_coef=0.5,
                ent_coef=0.003,
            )
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 0.5)
            optimizer.step()
            loss_values.append(float(loss.detach().cpu().item()))

    param_delta_l2 = _parameters_l2_delta(before_params, model)
    metrics_csv = RUN_DIR / "metrics.csv"
    checkpoint_path = RUN_DIR / "checkpoint.pt"
    episode_csv = RUN_DIR / "episode_rows.csv"
    npz_path = RUN_DIR / "rollout_arrays.npz"

    with metrics_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "total_steps",
                "episodes_completed",
                "reward_mean",
                "advantage_std",
                "loss_initial",
                "loss_final",
                "param_delta_l2",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "total_steps": QUICK_TOTAL_STEPS,
                "episodes_completed": len(episode_rows),
                "reward_mean": float(np.mean(reward_rows)),
                "advantage_std": float(np.std(advantages)),
                "loss_initial": loss_values[0] if loss_values else float("nan"),
                "loss_final": loss_values[-1] if loss_values else float("nan"),
                "param_delta_l2": param_delta_l2,
            }
        )
    with episode_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "row_id",
                "level",
                "eval_seed",
                "outcome_bucket",
                "termination_reason",
                "return",
                "length",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(episode_rows)
    np.savez_compressed(
        npz_path,
        obs=obs_rows,
        residual=residual_rows,
        base=base_rows,
        delta=delta_rows,
        final=final_rows,
        rewards=reward_rows,
        dones=done_rows,
        values=value_rows,
        advantages=advantages.astype(np.float32),
        returns=returns.astype(np.float32),
    )
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "model_config": {
                "obs_dim": OBS_DIM,
                "act_dim": ACT_DIM,
                "hidden_size": 64,
                "actor_encoder": "mlp",
                "base_policy": "ActiveSafetyReflexDriver incumbent v4 frozen",
                "delta_max": DELTA_MAX.tolist(),
            },
            "preregistration": str(PREREG_JSON.relative_to(REPO)),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        checkpoint_path,
    )

    finite_checks = {
        "obs": bool(np.all(np.isfinite(obs_rows))),
        "residual": bool(np.all(np.isfinite(residual_rows))),
        "base": bool(np.all(np.isfinite(base_rows))),
        "delta": bool(np.all(np.isfinite(delta_rows))),
        "final": bool(np.all(np.isfinite(final_rows))),
        "rewards": bool(np.all(np.isfinite(reward_rows))),
        "advantages": bool(np.all(np.isfinite(advantages))),
        "losses": bool(all(np.isfinite(loss) for loss in loss_values)),
    }
    quick_gates = {
        "total_steps_1024": QUICK_TOTAL_STEPS == 1024,
        "all_target_levels_exercised": set(TARGET_LEVELS).issubset(levels_seen),
        "finite_arrays": all(finite_checks.values()),
        "final_actions_in_bounds": bool(np.max(np.abs(final_rows)) <= 1.0 + 1e-6),
        "residual_delta_bounded": bool(np.all(np.abs(delta_rows) <= DELTA_MAX + 1e-6)),
        "optimizer_changed_parameters": bool(np.isfinite(param_delta_l2) and param_delta_l2 > 0.0),
        "checkpoint_written": checkpoint_path.exists(),
        "metrics_written": metrics_csv.exists() and episode_csv.exists() and npz_path.exists(),
    }
    passed = all(quick_gates.values())
    result = {
        "protocol": "c5prime_c1_v3_residual_rl_smoke",
        "generated_by": "scripts/feasibility_audit/c5prime_c1_v3_residual_rl_smoke.py",
        "generated_at_utc": utc_timestamp(),
        "preregistration": str(PREREG_JSON.relative_to(REPO)),
        "claim_boundary": CLAIM_BOUNDARY,
        "pricing_basis": prereg["pricing_basis"],
        "residual_architecture": prereg["residual_architecture"],
        "reward_recalibration": prereg["reward_recalibration"],
        "selected_rows": [
            {
                "row_id": row_id(row),
                "level": row["level"],
                "instance": int(row["instance"]),
                "eval_seed": int(row["eval_seed"]),
                "v4_pertuned_outcome": row["v4_pertuned_outcome"],
                "oracle_by": row["oracle_by"],
            }
            for row in rows
        ],
        "quick_gates": quick_gates,
        "finite_checks": finite_checks,
        "passed_quick_gates": passed,
        "metrics": {
            "total_steps": QUICK_TOTAL_STEPS,
            "episodes_completed": len(episode_rows),
            "levels_seen": sorted(levels_seen),
            "row_ids_seen": sorted(row_ids_seen),
            "reward_mean": float(np.mean(reward_rows)),
            "episode_return_mean": float(np.mean([row["return"] for row in episode_rows])) if episode_rows else float("nan"),
            "loss_initial": loss_values[0] if loss_values else float("nan"),
            "loss_final": loss_values[-1] if loss_values else float("nan"),
            "param_delta_l2": param_delta_l2,
            "wall_time_s": round(time.time() - t0, 3),
        },
        "artifacts": {
            "checkpoint": str(checkpoint_path.relative_to(REPO)),
            "metrics_csv": str(metrics_csv.relative_to(REPO)),
            "episode_rows_csv": str(episode_csv.relative_to(REPO)),
            "rollout_arrays_npz": str(npz_path.relative_to(REPO)),
        },
        "stage1_admission": (
            "not admitted by M3244 smoke alone; future stage-1 requires a separate preregistered "
            "four-arm judging run and CP-2 budget approval before any >1h run"
        ),
    }
    write_json(RESULTS_JSON, result)
    if not passed:
        raise RuntimeError(f"C1-v3 residual-RL smoke gates failed: {quick_gates}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the C1-v3 residual-RL smoke.")
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    if args.write_prereg:
        payload = write_preregistration()
        print(f"wrote_prereg={PREREG_JSON} gates={len(payload['quick_gates'])}")
        if not args.quick:
            return
    if not args.quick:
        raise SystemExit("pass --quick for M3244 smoke execution")
    result = run_quick()
    print(
        "passed_quick_gates="
        f"{result['passed_quick_gates']} total_steps={result['metrics']['total_steps']} "
        f"episodes={result['metrics']['episodes_completed']} wall_time_s={result['metrics']['wall_time_s']}"
    )


if __name__ == "__main__":
    main()
