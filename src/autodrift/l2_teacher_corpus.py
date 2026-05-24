"""Export L2 teacher targets for L3 recurrent student distillation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


TEACHER_STACK_ARRAY_NAME = "teacher_obs_stack_seq"


def load_env_config(path: Path | str) -> DriftEnvConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "env" not in data:
        raise ValueError(f"{path} is missing required top-level 'env' config")
    return build_env_config(data["env"])


def parse_seed_list(raw: str | None, *, seed_start: int | None, episodes: int | None) -> list[int]:
    if raw:
        seeds: list[int] = []
        for part in raw.split(","):
            token = part.strip()
            if not token:
                continue
            if ":" in token:
                start_text, end_text = token.split(":", 1)
                start = int(start_text)
                end = int(end_text)
                if end < start:
                    raise ValueError(f"invalid seed range {token}: end is below start")
                seeds.extend(range(start, end + 1))
            else:
                seeds.append(int(token))
        if not seeds:
            raise ValueError("--seeds did not contain any usable seed")
        return seeds
    if seed_start is None or episodes is None:
        raise ValueError("provide --seeds or both --seed-start and --episodes")
    if episodes < 1:
        raise ValueError("--episodes must be positive")
    return [int(seed_start) + offset for offset in range(int(episodes))]


def mu_bucket(mu: float) -> str:
    if mu < 0.30:
        return "low"
    if mu < 0.55:
        return "medium"
    return "high"


def extract_current_p0_frame(stacked_observation: np.ndarray, *, history_length: int) -> np.ndarray:
    observation = np.asarray(stacked_observation, dtype=np.float32)
    if observation.ndim != 1:
        raise ValueError(f"expected flat observation, got shape {observation.shape}")
    if history_length < 1:
        raise ValueError("history_length must be positive")
    if observation.size % history_length != 0:
        raise ValueError(
            f"observation length {observation.size} is not divisible by history_length {history_length}"
        )
    frame_dim = observation.size // history_length
    if frame_dim != HUMAN_VIEW_OBS_DIM:
        raise ValueError(
            f"student frame dim must be canonical {HUMAN_VIEW_OBS_DIM}, got {frame_dim}; "
            "check for wheel/privileged/profile leakage"
        )
    return observation[:frame_dim].copy()


def validate_l2_teacher_boundary(env: AutoDriftEnv) -> None:
    if env.config.history_length < 2:
        raise ValueError("L2 teacher corpus export requires a finite-window teacher env with history_length >= 2")
    if env.config.include_privileged_params:
        raise ValueError("teacher env cannot include privileged params")
    if env.config.wheel_observation_mode != "none":
        raise ValueError("teacher env cannot include wheel observations")
    if env.base_obs_dim != HUMAN_VIEW_OBS_DIM:
        raise ValueError(f"teacher base observation must be {HUMAN_VIEW_OBS_DIM}, got {env.base_obs_dim}")


def terminal_diagnostics(
    *,
    episode_id: int,
    seed: int,
    steps: int,
    return_sum: float,
    terminated: bool,
    truncated: bool,
    info: dict[str, Any],
) -> dict[str, Any]:
    initial_mu = float(info.get("initial_mu", np.nan))
    final_mu = float(info.get("mu", np.nan))
    return {
        "episode_id": int(episode_id),
        "seed": int(seed),
        "steps": int(steps),
        "return": float(return_sum),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_clearance_margin": float(info.get("min_clearance_margin", np.nan)),
        "obstacle_label": str(info.get("obstacle_label", "")),
        "friction_step_applied": bool(info.get("friction_step_applied", False)),
        "initial_mu_bucket": mu_bucket(initial_mu) if np.isfinite(initial_mu) else "",
        "final_mu_bucket": mu_bucket(final_mu) if np.isfinite(final_mu) else "",
    }


def export_l2_teacher_corpus(
    *,
    teacher_checkpoint: Path | str,
    teacher_env_config: Path | str,
    seeds: Iterable[int],
    output_npz: Path | str,
    summary_json: Path | str,
    episodes_csv: Path | str | None = None,
    device: str = "auto",
) -> dict[str, Any]:
    seed_list = [int(seed) for seed in seeds]
    if not seed_list:
        raise ValueError("at least one seed is required")

    env_config = load_env_config(teacher_env_config)
    env = AutoDriftEnv(env_config)
    validate_l2_teacher_boundary(env)

    teacher_obs_dim = int(env.observation_space.shape[0])
    model, checkpoint = load_actor_critic_checkpoint(teacher_checkpoint, device=device, obs_dim=teacher_obs_dim)
    if model.is_online_recurrent:
        raise ValueError("M562 expects a finite-window L2 teacher, not an online recurrent teacher")
    if int(model.obs_dim) != teacher_obs_dim:
        raise ValueError(f"teacher model obs_dim {model.obs_dim} does not match env obs_dim {teacher_obs_dim}")

    student_obs_rows: list[np.ndarray] = []
    teacher_action_rows: list[np.ndarray] = []
    done_rows: list[bool] = []
    episode_start_rows: list[bool] = []
    seed_rows: list[int] = []
    episode_id_rows: list[int] = []
    step_rows: list[int] = []
    episode_rows: list[dict[str, Any]] = []

    for episode_id, seed in enumerate(seed_list):
        obs, info = env.reset(seed=seed)
        terminated = False
        truncated = False
        return_sum = 0.0
        step = 0
        while not (terminated or truncated):
            student_obs = extract_current_p0_frame(obs, history_length=env.config.history_length)
            action, _, _ = model.act(obs, deterministic=True)
            next_obs, reward, terminated, truncated, info = env.step(action)

            student_obs_rows.append(student_obs.astype(np.float32, copy=False))
            teacher_action_rows.append(np.asarray(action, dtype=np.float32))
            done_rows.append(bool(terminated or truncated))
            episode_start_rows.append(step == 0)
            seed_rows.append(seed)
            episode_id_rows.append(episode_id)
            step_rows.append(step)

            return_sum += float(reward)
            step += 1
            obs = next_obs

        episode_rows.append(
            terminal_diagnostics(
                episode_id=episode_id,
                seed=seed,
                steps=step,
                return_sum=return_sum,
                terminated=terminated,
                truncated=truncated,
                info=info,
            )
        )

    output_npz_path = Path(output_npz)
    output_npz_path.parent.mkdir(parents=True, exist_ok=True)
    student_obs_seq = np.stack(student_obs_rows).astype(np.float32)
    teacher_action_seq = np.stack(teacher_action_rows).astype(np.float32)
    np.savez_compressed(
        output_npz_path,
        student_obs_seq=student_obs_seq,
        teacher_action_seq=teacher_action_seq,
        done_seq=np.asarray(done_rows, dtype=np.bool_),
        episode_start_seq=np.asarray(episode_start_rows, dtype=np.bool_),
        seed_seq=np.asarray(seed_rows, dtype=np.int64),
        episode_id_seq=np.asarray(episode_id_rows, dtype=np.int64),
        step_seq=np.asarray(step_rows, dtype=np.int64),
    )

    if episodes_csv is not None:
        write_csv_rows(Path(episodes_csv), episode_rows)

    summary = {
        "run_type": "l2_teacher_corpus_export",
        "teacher_checkpoint": str(teacher_checkpoint),
        "teacher_env_config": str(teacher_env_config),
        "checkpoint_actor_encoder": checkpoint.get("config", {}).get("actor_encoder", ""),
        "checkpoint_history_baseline": checkpoint.get("metadata", {}).get("history_baseline", {}),
        "seeds": seed_list,
        "episode_count": len(seed_list),
        "transition_count": int(student_obs_seq.shape[0]),
        "student_obs_dim": int(student_obs_seq.shape[1]),
        "teacher_action_dim": int(teacher_action_seq.shape[1]),
        "teacher_obs_dim": teacher_obs_dim,
        "teacher_history_length": int(env.config.history_length),
        "student_input_arrays": ["student_obs_seq"],
        "target_arrays": ["teacher_action_seq"],
        "mask_arrays": ["done_seq", "episode_start_seq"],
        "stored_arrays": [
            "student_obs_seq",
            "teacher_action_seq",
            "done_seq",
            "episode_start_seq",
            "seed_seq",
            "episode_id_seq",
            "step_seq",
        ],
        "teacher_stack_stored": False,
        "uses_public_frozen_source_rows": False,
        "student_obs_is_canonical_p0_frame": bool(student_obs_seq.shape[1] == HUMAN_VIEW_OBS_DIM),
        "episodes": episode_rows,
        "output_npz": str(output_npz_path),
        "episodes_csv": str(episodes_csv) if episodes_csv is not None else "",
    }
    write_json(Path(summary_json), summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export an L2 teacher corpus for L3 recurrent distillation.")
    parser.add_argument("--teacher-checkpoint", type=Path, required=True)
    parser.add_argument("--teacher-env-config", type=Path, required=True)
    parser.add_argument("--seeds", type=str, default="")
    parser.add_argument("--seed-start", type=int, default=None)
    parser.add_argument("--episodes", type=int, default=None)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--run-name", type=str, default="m562_l2_teacher_corpus")
    parser.add_argument("--output-npz", type=Path, default=None)
    parser.add_argument("--summary-json", type=Path, default=None)
    parser.add_argument("--episodes-csv", type=Path, default=None)
    args = parser.parse_args()

    seeds = parse_seed_list(args.seeds, seed_start=args.seed_start, episodes=args.episodes)
    run_dir = args.run_dir or make_run_dir(prefix=args.run_name)
    run_dir.mkdir(parents=True, exist_ok=True)
    output_npz = args.output_npz or run_dir / "l2_teacher_corpus.npz"
    summary_json = args.summary_json or run_dir / "summary.json"
    episodes_csv = args.episodes_csv or run_dir / "episodes.csv"

    summary = export_l2_teacher_corpus(
        teacher_checkpoint=args.teacher_checkpoint,
        teacher_env_config=args.teacher_env_config,
        seeds=seeds,
        output_npz=output_npz,
        summary_json=summary_json,
        episodes_csv=episodes_csv,
        device=args.device,
    )
    print(f"summary={summary_json}")
    print(f"corpus={output_npz}")
    print(f"transitions={summary['transition_count']}")


if __name__ == "__main__":
    main()
