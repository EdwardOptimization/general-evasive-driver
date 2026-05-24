"""Offline L3 behavior cloning from L2 teacher corpora."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.nn.utils import clip_grad_norm_

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.history_baselines import (
    L3_ONLINE_GRU,
    build_history_baseline_spec,
    history_baseline_spec_to_dict,
)
from autodrift.l2_teacher_corpus import TEACHER_STACK_ARRAY_NAME
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM, PPOConfig, resolve_device, save_training_checkpoint


@dataclass(frozen=True)
class BCCorpus:
    path: Path
    student_obs: np.ndarray
    teacher_actions: np.ndarray
    done: np.ndarray
    episode_start: np.ndarray
    episode_id: np.ndarray
    step: np.ndarray

    @property
    def transition_count(self) -> int:
        return int(self.student_obs.shape[0])


def load_student_env_config(path: Path | str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "env" not in data:
        raise ValueError(f"{path} is missing required top-level 'env' config")
    return build_env_config(data["env"])


def load_bc_corpus(path: Path | str) -> BCCorpus:
    corpus_path = Path(path)
    data = np.load(corpus_path)
    if TEACHER_STACK_ARRAY_NAME in data.files:
        raise ValueError(f"{TEACHER_STACK_ARRAY_NAME} must not be present in L3 student corpus arrays")
    required = {
        "student_obs_seq",
        "teacher_action_seq",
        "done_seq",
        "episode_start_seq",
        "episode_id_seq",
        "step_seq",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"BC corpus is missing required arrays: {missing}")

    student_obs = np.asarray(data["student_obs_seq"], dtype=np.float32)
    teacher_actions = np.asarray(data["teacher_action_seq"], dtype=np.float32)
    done = np.asarray(data["done_seq"], dtype=np.bool_)
    episode_start = np.asarray(data["episode_start_seq"], dtype=np.bool_)
    episode_id = np.asarray(data["episode_id_seq"], dtype=np.int64)
    step = np.asarray(data["step_seq"], dtype=np.int64)

    if student_obs.ndim != 2 or student_obs.shape[1] != HUMAN_VIEW_OBS_DIM:
        raise ValueError(f"student_obs_seq must have shape (N, {HUMAN_VIEW_OBS_DIM}), got {student_obs.shape}")
    if teacher_actions.ndim != 2 or teacher_actions.shape[1] != 3:
        raise ValueError(f"teacher_action_seq must have shape (N, 3), got {teacher_actions.shape}")
    lengths = {array.shape[0] for array in (student_obs, teacher_actions, done, episode_start, episode_id, step)}
    if len(lengths) != 1:
        raise ValueError("all BC corpus arrays must have the same first dimension")
    if student_obs.shape[0] < 1:
        raise ValueError("BC corpus must contain at least one transition")
    if not bool(episode_start[0]):
        raise ValueError("first transition must set episode_start_seq=true")
    return BCCorpus(
        path=corpus_path,
        student_obs=student_obs,
        teacher_actions=teacher_actions,
        done=done,
        episode_start=episode_start,
        episode_id=episode_id,
        step=step,
    )


def episode_slices(corpus: BCCorpus) -> list[tuple[int, int]]:
    starts = np.flatnonzero(corpus.episode_start)
    if len(starts) == 0 or int(starts[0]) != 0:
        raise ValueError("episode_start_seq must identify the first transition")
    ends = list(starts[1:]) + [corpus.transition_count]
    slices = [(int(start), int(end)) for start, end in zip(starts, ends)]
    for start, end in slices:
        if end <= start:
            raise ValueError("empty episode slice in BC corpus")
        local_steps = corpus.step[start:end]
        expected_steps = np.arange(end - start, dtype=np.int64)
        if not np.array_equal(local_steps, expected_steps):
            raise ValueError("step_seq must restart at zero and increase by one inside each episode")
    return slices


def corpus_action_mse(model: ActorCritic, corpus: BCCorpus, *, device: torch.device) -> float:
    model.eval()
    total_squared_error = 0.0
    total_elements = 0
    with torch.no_grad():
        for start, end in episode_slices(corpus):
            hidden = model.initial_hidden(1, device)
            for index in range(start, end):
                obs = torch.as_tensor(corpus.student_obs[index], dtype=torch.float32, device=device).unsqueeze(0)
                target = torch.as_tensor(corpus.teacher_actions[index], dtype=torch.float32, device=device).unsqueeze(0)
                dist, _, hidden = model.forward_recurrent(obs, hidden)
                action = torch.tanh(dist.mean)
                squared_error = torch.square(action - target)
                total_squared_error += float(squared_error.sum().item())
                total_elements += int(target.numel())
    if total_elements == 0:
        raise ValueError("cannot compute MSE for empty corpus")
    return total_squared_error / float(total_elements)


def _episode_loss(model: ActorCritic, corpus: BCCorpus, start: int, end: int, *, device: torch.device) -> torch.Tensor:
    hidden = model.initial_hidden(1, device)
    losses: list[torch.Tensor] = []
    for index in range(start, end):
        obs = torch.as_tensor(corpus.student_obs[index], dtype=torch.float32, device=device).unsqueeze(0)
        target = torch.as_tensor(corpus.teacher_actions[index], dtype=torch.float32, device=device).unsqueeze(0)
        dist, _, hidden = model.forward_recurrent(obs, hidden)
        action = torch.tanh(dist.mean)
        losses.append(torch.mean(torch.square(action - target)))
    return torch.stack(losses).mean()


def train_l3_behavior_cloning(
    *,
    train_corpus_path: Path | str,
    val_corpus_path: Path | str,
    student_env_config: Path | str,
    output_checkpoint: Path | str,
    metrics_csv: Path | str,
    summary_json: Path | str,
    hidden_size: int = 64,
    epochs: int = 20,
    learning_rate: float = 1e-3,
    max_grad_norm: float = 0.5,
    seed: int = 5630,
    device: str = "auto",
) -> dict[str, Any]:
    if epochs < 1:
        raise ValueError("epochs must be positive")
    train_corpus = load_bc_corpus(train_corpus_path)
    val_corpus = load_bc_corpus(val_corpus_path)
    resolved_device = resolve_device(device)
    torch.manual_seed(int(seed))

    env_config = load_student_env_config(student_env_config)
    history_spec = build_history_baseline_spec(
        level=L3_ONLINE_GRU,
        actor_encoder="human_view_online_gru",
        actor_history_length=1,
        env_config=env_config,
    )
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        act_dim=3,
        hidden_size=int(hidden_size),
        actor_encoder="human_view_online_gru",
        actor_history_length=1,
    ).to(resolved_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(learning_rate))

    train_slices = episode_slices(train_corpus)
    metrics: list[dict[str, Any]] = []
    initial_train_mse = corpus_action_mse(model, train_corpus, device=resolved_device)
    initial_val_mse = corpus_action_mse(model, val_corpus, device=resolved_device)
    metrics.append(
        {
            "epoch": 0,
            "train_action_mse": initial_train_mse,
            "val_action_mse": initial_val_mse,
        }
    )

    for epoch in range(1, int(epochs) + 1):
        model.train()
        for start, end in train_slices:
            optimizer.zero_grad(set_to_none=True)
            loss = _episode_loss(model, train_corpus, start, end, device=resolved_device)
            loss.backward()
            clip_grad_norm_(model.parameters(), float(max_grad_norm))
            optimizer.step()
        metrics.append(
            {
                "epoch": epoch,
                "train_action_mse": corpus_action_mse(model, train_corpus, device=resolved_device),
                "val_action_mse": corpus_action_mse(model, val_corpus, device=resolved_device),
            }
        )

    final_train_mse = float(metrics[-1]["train_action_mse"])
    final_val_mse = float(metrics[-1]["val_action_mse"])
    ppo_config = PPOConfig(
        hidden_size=int(hidden_size),
        learning_rate=float(learning_rate),
        actor_encoder="human_view_online_gru",
        actor_history_length=1,
        history_baseline_level=L3_ONLINE_GRU,
        recurrent_sequence_training=True,
        device=str(device),
    )
    checkpoint_metadata = {
        "env": env_config,
        "history_baseline": history_baseline_spec_to_dict(history_spec),
        "training": {
            "run_type": "l3_behavior_cloning",
            "train_corpus": str(train_corpus.path),
            "val_corpus": str(val_corpus.path),
            "uses_public_frozen_source_rows": False,
            "ppo_used": False,
            "promoted": False,
        },
    }
    save_training_checkpoint(model, ppo_config, checkpoint_metadata, Path(output_checkpoint))
    write_csv_rows(Path(metrics_csv), metrics)
    summary = {
        "run_type": "l3_behavior_cloning",
        "train_corpus": str(train_corpus.path),
        "val_corpus": str(val_corpus.path),
        "student_env_config": str(student_env_config),
        "checkpoint": str(output_checkpoint),
        "metrics_csv": str(metrics_csv),
        "epochs": int(epochs),
        "hidden_size": int(hidden_size),
        "learning_rate": float(learning_rate),
        "train_transition_count": train_corpus.transition_count,
        "val_transition_count": val_corpus.transition_count,
        "initial_train_action_mse": initial_train_mse,
        "final_train_action_mse": final_train_mse,
        "train_action_mse_delta": final_train_mse - initial_train_mse,
        "initial_val_action_mse": initial_val_mse,
        "final_val_action_mse": final_val_mse,
        "val_action_mse_delta": final_val_mse - initial_val_mse,
        "student_obs_dim": HUMAN_VIEW_OBS_DIM,
        "actor_encoder": "human_view_online_gru",
        "history_baseline": history_baseline_spec_to_dict(history_spec),
        "teacher_stack_consumed_by_student": False,
        "uses_public_frozen_source_rows": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(Path(summary_json), summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train an L3 online-GRU actor by offline behavior cloning.")
    parser.add_argument("--train-corpus", type=Path, required=True)
    parser.add_argument("--val-corpus", type=Path, required=True)
    parser.add_argument("--student-env-config", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--hidden-size", type=int, default=64)
    parser.add_argument("--max-grad-norm", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=5630)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--run-name", type=str, default="m563_l3_behavior_cloning")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--metrics-csv", type=Path, default=None)
    parser.add_argument("--summary-json", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix=args.run_name, seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.checkpoint or run_dir / "checkpoint.pt"
    metrics_csv = args.metrics_csv or run_dir / "train_metrics.csv"
    summary_json = args.summary_json or run_dir / "summary.json"
    summary = train_l3_behavior_cloning(
        train_corpus_path=args.train_corpus,
        val_corpus_path=args.val_corpus,
        student_env_config=args.student_env_config,
        output_checkpoint=checkpoint,
        metrics_csv=metrics_csv,
        summary_json=summary_json,
        hidden_size=args.hidden_size,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        max_grad_norm=args.max_grad_norm,
        seed=args.seed,
        device=args.device,
    )
    print(f"summary={summary_json}")
    print(f"checkpoint={checkpoint}")
    print(f"train_action_mse_delta={summary['train_action_mse_delta']}")
    print(f"val_action_mse_delta={summary['val_action_mse_delta']}")


if __name__ == "__main__":
    main()
