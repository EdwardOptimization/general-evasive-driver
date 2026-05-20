"""Latent self-identification probes for frozen AutoDrift policies."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import ActorPolicy, load_env_config
from autodrift.train_ppo import ActorCritic


@dataclass(frozen=True)
class BucketSpec:
    source: str
    bins: tuple[float, ...]
    labels: tuple[str, ...]


@dataclass(frozen=True)
class ProbeDataset:
    observations: np.ndarray
    labels: dict[str, np.ndarray]
    rows: list[dict]


@dataclass(frozen=True)
class ProbeResult:
    target: str
    feature_set: str
    train_samples: int
    test_samples: int
    classes: str
    train_accuracy: float
    test_accuracy: float
    majority_accuracy: float
    accuracy_lift: float
    status: str = "ok"


TARGET_SPECS: dict[str, BucketSpec] = {
    "mu_bucket": BucketSpec("mu", (0.0, 0.45, 0.80, float("inf")), ("low", "medium", "high")),
    "mass_bucket": BucketSpec("mass_scale", (0.0, 0.95, 1.05, float("inf")), ("light", "nominal", "heavy")),
    "cg_bucket": BucketSpec("cg_shift", (-float("inf"), -0.04, 0.04, float("inf")), ("rear", "nominal", "front")),
    "brake_bucket": BucketSpec("brake_scale", (0.0, 0.90, 1.05, float("inf")), ("weak", "nominal", "strong")),
    "tire_bucket": BucketSpec(
        "tire_stiffness_scale",
        (0.0, 0.85, 1.15, float("inf")),
        ("weak", "nominal", "strong"),
    ),
    "steering_tau_bucket": BucketSpec(
        "steer_tau_scale",
        (0.0, 0.90, 1.20, float("inf")),
        ("fast", "nominal", "slow"),
    ),
}


def bucket_label(value: float, spec: BucketSpec) -> str:
    if not np.isfinite(value):
        raise ValueError(f"cannot bucket non-finite value {value!r} for {spec.source}")
    for index, label in enumerate(spec.labels):
        lower = spec.bins[index]
        upper = spec.bins[index + 1]
        if index == len(spec.labels) - 1:
            matches = lower <= value <= upper
        else:
            matches = lower <= value < upper
        if matches:
            return label
    return spec.labels[-1]


def target_labels_from_info(info: dict) -> dict[str, str]:
    missing = [spec.source for spec in TARGET_SPECS.values() if spec.source not in info]
    if missing:
        raise KeyError(f"probe target source fields are missing from env info: {missing}")
    return {
        name: bucket_label(float(info[spec.source]), spec)
        for name, spec in TARGET_SPECS.items()
    }


def encode_target_labels(label_rows: list[dict[str, str]]) -> dict[str, np.ndarray]:
    encoded: dict[str, np.ndarray] = {}
    for target, spec in TARGET_SPECS.items():
        index_by_label = {label: index for index, label in enumerate(spec.labels)}
        encoded[target] = np.asarray([index_by_label[row[target]] for row in label_rows], dtype=np.int64)
    return encoded


def extract_model_features(model: ActorCritic, observations: np.ndarray) -> np.ndarray:
    device = next(model.parameters()).device
    with torch.no_grad():
        obs_t = torch.as_tensor(observations, dtype=torch.float32, device=device)
        features = model.features_tensor(obs_t)
    return features.cpu().numpy().astype(np.float32)


def shuffled_history_observations(observations: np.ndarray, env_config: DriftEnvConfig, seed: int) -> np.ndarray:
    history_length = env_config.history_length
    if history_length <= 1:
        return observations.copy()
    rng = np.random.default_rng(seed)
    base_dim = observations.shape[1] // history_length
    shuffled = observations.reshape(observations.shape[0], history_length, base_dim).copy()
    for index in range(shuffled.shape[0]):
        shuffled[index] = shuffled[index, rng.permutation(history_length)]
    return shuffled.reshape(observations.shape).astype(np.float32)


def build_feature_sets(
    model: ActorCritic,
    observations: np.ndarray,
    env_config: DriftEnvConfig,
    seed: int,
) -> dict[str, np.ndarray]:
    base_dim = observations.shape[1] // env_config.history_length
    shuffled_observations = shuffled_history_observations(observations, env_config, seed)
    return {
        "latent": extract_model_features(model, observations),
        "full_observation": observations.astype(np.float32),
        "single_frame": observations[:, :base_dim].astype(np.float32),
        "shuffled_history_latent": extract_model_features(model, shuffled_observations),
    }


def collect_probe_dataset(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    episodes: int,
    seed: int,
    checkpoint_ablation: str = "none",
    max_samples: int | None = None,
) -> ProbeDataset:
    env = AutoDriftEnv(env_config)
    policy = ActorPolicy(model, env_config, ablation=checkpoint_ablation)
    observations: list[np.ndarray] = []
    rows: list[dict] = []
    label_rows: list[dict[str, str]] = []

    for episode in range(episodes):
        episode_seed = seed + episode
        obs, info = env.reset(seed=episode_seed)
        policy.reset()
        terminated = False
        truncated = False
        while not (terminated or truncated):
            transformed_obs = policy._transform_observation(obs)
            labels = target_labels_from_info(info)
            observations.append(transformed_obs.astype(np.float32))
            label_rows.append(labels)
            rows.append(
                {
                    "episode": episode,
                    "seed": episode_seed,
                    "step": int(info["step"]),
                    "obstacle_label": str(info.get("obstacle_label", "")),
                    **labels,
                }
            )
            if max_samples is not None and len(observations) >= max_samples:
                return ProbeDataset(
                    observations=np.asarray(observations, dtype=np.float32),
                    labels=encode_target_labels(label_rows),
                    rows=rows,
                )
            action = policy.act(obs, info)
            obs, _, terminated, truncated, info = env.step(action)

    return ProbeDataset(
        observations=np.asarray(observations, dtype=np.float32),
        labels=encode_target_labels(label_rows),
        rows=rows,
    )


def split_by_episode(rows: list[dict], train_fraction: float, seed: int) -> np.ndarray:
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")
    episodes = np.asarray(sorted({int(row["episode"]) for row in rows}), dtype=np.int64)
    if len(episodes) < 2:
        raise ValueError("at least two episodes are required for an episode-disjoint probe split")
    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(episodes)
    train_count = int(round(len(shuffled) * train_fraction))
    train_count = min(max(train_count, 1), max(len(shuffled) - 1, 1))
    train_episodes = set(int(item) for item in shuffled[:train_count])
    return np.asarray([int(row["episode"]) in train_episodes for row in rows], dtype=bool)


def _accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    prediction = torch.argmax(logits, dim=1)
    return float((prediction == labels).float().mean().item())


def train_linear_probe(
    features: np.ndarray,
    labels: np.ndarray,
    train_mask: np.ndarray,
    target_name: str,
    feature_set: str,
    seed: int,
    epochs: int = 300,
    learning_rate: float = 0.03,
    weight_decay: float = 1e-4,
) -> ProbeResult:
    train_labels = labels[train_mask]
    test_labels = labels[~train_mask]
    spec = TARGET_SPECS[target_name]
    present_classes = sorted(set(int(value) for value in labels.tolist()))
    present_train_classes = sorted(set(int(value) for value in train_labels.tolist()))
    class_names = ",".join(spec.labels[index] for index in present_classes)
    if len(present_train_classes) < 2 or len(test_labels) == 0:
        return ProbeResult(
            target=target_name,
            feature_set=feature_set,
            train_samples=int(train_mask.sum()),
            test_samples=int((~train_mask).sum()),
            classes=class_names,
            train_accuracy=float("nan"),
            test_accuracy=float("nan"),
            majority_accuracy=float("nan"),
            accuracy_lift=float("nan"),
            status="skipped_insufficient_classes",
        )

    train_x = features[train_mask].astype(np.float32)
    test_x = features[~train_mask].astype(np.float32)
    mean = train_x.mean(axis=0, keepdims=True)
    std = train_x.std(axis=0, keepdims=True) + 1e-6
    train_x = (train_x - mean) / std
    test_x = (test_x - mean) / std

    torch.manual_seed(seed)
    classifier = nn.Linear(train_x.shape[1], len(spec.labels))
    optimizer = torch.optim.AdamW(classifier.parameters(), lr=learning_rate, weight_decay=weight_decay)
    train_x_t = torch.as_tensor(train_x, dtype=torch.float32)
    test_x_t = torch.as_tensor(test_x, dtype=torch.float32)
    train_y_t = torch.as_tensor(train_labels, dtype=torch.long)
    test_y_t = torch.as_tensor(test_labels, dtype=torch.long)

    for _ in range(epochs):
        optimizer.zero_grad()
        loss = nn.functional.cross_entropy(classifier(train_x_t), train_y_t)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        train_accuracy = _accuracy(classifier(train_x_t), train_y_t)
        test_accuracy = _accuracy(classifier(test_x_t), test_y_t)
    counts = np.bincount(train_labels, minlength=len(spec.labels))
    majority_class = int(np.argmax(counts))
    majority_accuracy = float(np.mean(test_labels == majority_class))
    return ProbeResult(
        target=target_name,
        feature_set=feature_set,
        train_samples=int(train_mask.sum()),
        test_samples=int((~train_mask).sum()),
        classes=class_names,
        train_accuracy=train_accuracy,
        test_accuracy=test_accuracy,
        majority_accuracy=majority_accuracy,
        accuracy_lift=test_accuracy - majority_accuracy,
    )


def run_probe(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    episodes: int,
    seed: int,
    feature_set_names: list[str],
    checkpoint_ablation: str = "none",
    max_samples: int | None = None,
    train_fraction: float = 0.70,
    epochs: int = 300,
    learning_rate: float = 0.03,
) -> tuple[ProbeDataset, list[ProbeResult]]:
    dataset = collect_probe_dataset(
        model=model,
        env_config=env_config,
        episodes=episodes,
        seed=seed,
        checkpoint_ablation=checkpoint_ablation,
        max_samples=max_samples,
    )
    if len(dataset.rows) == 0:
        raise ValueError("probe dataset is empty")
    features = build_feature_sets(model, dataset.observations, env_config, seed=seed + 17)
    unknown = sorted(set(feature_set_names) - set(features))
    if unknown:
        raise ValueError(f"unknown feature sets: {unknown}")
    train_mask = split_by_episode(dataset.rows, train_fraction=train_fraction, seed=seed + 31)
    results = []
    for target_name, labels in dataset.labels.items():
        for feature_set in feature_set_names:
            results.append(
                train_linear_probe(
                    features=features[feature_set],
                    labels=labels,
                    train_mask=train_mask,
                    target_name=target_name,
                    feature_set=feature_set,
                    seed=seed + len(results),
                    epochs=epochs,
                    learning_rate=learning_rate,
                )
            )
    return dataset, results


def probe_results_to_rows(results: list[ProbeResult]) -> list[dict]:
    return [result.__dict__ for result in results]


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe hidden-condition information in a frozen AutoDrift actor.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=1100)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=0.03)
    parser.add_argument(
        "--checkpoint-ablation",
        choices=["none", "zero_action_history", "single_frame_history", "shuffled_history"],
        default="none",
    )
    parser.add_argument(
        "--feature-set",
        action="append",
        default=None,
        choices=["latent", "full_observation", "single_frame", "shuffled_history_latent"],
        help="Feature set to probe. Repeat to select several; defaults to latent, single_frame, shuffled_history_latent.",
    )
    args = parser.parse_args()

    env_config = load_env_config(args.env_config)
    env = AutoDriftEnv(env_config)
    model, _ = load_actor_critic_checkpoint(
        args.checkpoint,
        device=args.device,
        obs_dim=int(env.observation_space.shape[0]),
    )
    feature_sets = args.feature_set or ["latent", "single_frame", "shuffled_history_latent"]
    dataset, results = run_probe(
        model=model,
        env_config=env_config,
        episodes=args.episodes,
        seed=args.seed,
        feature_set_names=feature_sets,
        checkpoint_ablation=args.checkpoint_ablation,
        max_samples=args.max_samples,
        train_fraction=args.train_fraction,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
    )

    run_dir = args.run_dir or make_run_dir(prefix="latent_probe", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    summary_csv = run_dir / "probe_summary.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"

    write_csv_rows(samples_csv, dataset.rows)
    result_rows = probe_results_to_rows(results)
    write_csv_rows(summary_csv, result_rows)
    write_json(
        summary_json,
        {
            "episodes": args.episodes,
            "samples": int(len(dataset.rows)),
            "feature_sets": feature_sets,
            "checkpoint_ablation": args.checkpoint_ablation,
            "results": result_rows,
        },
    )
    write_json(
        manifest_json,
        {
            "run_type": "latent_probe",
            "checkpoint": args.checkpoint,
            "env_config": args.env_config,
            "episodes": args.episodes,
            "seed": args.seed,
            "device": args.device,
            "checkpoint_ablation": args.checkpoint_ablation,
            "feature_sets": feature_sets,
            "artifacts": {
                "samples_csv": samples_csv,
                "probe_summary_csv": summary_csv,
                "summary_json": summary_json,
            },
        },
    )
    print(pd.DataFrame(result_rows).to_string(index=False))


if __name__ == "__main__":
    main()
