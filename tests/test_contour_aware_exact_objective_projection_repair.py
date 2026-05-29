from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_exact_objective_projection_repair import (
    run_contour_aware_exact_objective_projection_repair,
)


class TinyRecurrentActor(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.actor_mean = torch.nn.Linear(2, 3)
        with torch.no_grad():
            self.actor_mean.weight.copy_(
                torch.tensor(
                    [
                        [0.20, -0.10],
                        [-0.05, 0.15],
                        [0.10, 0.05],
                    ],
                    dtype=torch.float32,
                )
            )
            self.actor_mean.bias.copy_(torch.tensor([0.01, -0.02, 0.03], dtype=torch.float32))

    def recurrent_features_tensor(self, obs: torch.Tensor, hidden: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = obs[:, :2] + 0.5 * hidden[:, :2]
        return features, hidden


def _action_from(model: TinyRecurrentActor, observation: np.ndarray, hidden: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        obs = torch.as_tensor(observation, dtype=torch.float32).reshape(1, -1)
        hidden_t = torch.as_tensor(hidden, dtype=torch.float32).reshape(1, -1)
        features, _ = model.recurrent_features_tensor(obs, hidden_t)
        return torch.tanh(model.actor_mean(features)).cpu().numpy().reshape(3).astype(np.float32)


def _make_bundle(
    tmp_path: Path,
    *,
    model: TinyRecurrentActor,
    positive_count: int,
    diagnostic_count: int,
) -> tuple[Path, Path]:
    materialization_dir = tmp_path / "materialization"
    materialization_dir.mkdir()

    def arrays(count: int, offset: int) -> dict[str, np.ndarray]:
        observations = []
        correct_hidden = []
        wrong_hidden = []
        for index in range(count):
            obs = np.zeros((72,), dtype=np.float32)
            obs[0] = 0.2 + 0.03 * (offset + index)
            obs[1] = -0.15 + 0.02 * (offset + index)
            observations.append(obs)
            correct_hidden.append(np.asarray([0.1 + 0.02 * index, -0.05 - 0.01 * index], dtype=np.float32))
            wrong_hidden.append(np.asarray([-0.08 - 0.01 * index, 0.07 + 0.02 * index], dtype=np.float32))
        observation = np.stack(observations, axis=0)
        correct_hidden_array = np.stack(correct_hidden, axis=0)
        wrong_hidden_array = np.stack(wrong_hidden, axis=0)
        preferred = np.stack(
            [_action_from(model, observation[index], correct_hidden_array[index]) for index in range(count)],
            axis=0,
        )
        wrong = np.stack(
            [_action_from(model, observation[index], wrong_hidden_array[index]) for index in range(count)],
            axis=0,
        )
        donor_plus = wrong + np.asarray([0.01, -0.01, 0.0], dtype=np.float32)
        return {
            "observation": observation,
            "correct_hidden": correct_hidden_array,
            "wrong_hidden": wrong_hidden_array,
            "preferred_action": preferred,
            "wrong_history_action": wrong,
            "donor_plus_hidden_action": donor_plus,
        }

    positive_arrays = arrays(positive_count, 0)
    diagnostic_arrays = arrays(diagnostic_count, 100)
    np.savez_compressed(materialization_dir / "positive_policy_targets.npz", **positive_arrays)
    np.savez_compressed(materialization_dir / "diagnostic_policy_guardrails.npz", **diagnostic_arrays)

    def rows(count: int, role: str, offset: int) -> list[dict[str, object]]:
        output = []
        for index in range(count):
            pair_id = f"pair-{offset + index:04d}"
            output.append(
                {
                    "target_id": pair_id,
                    "pair_id": pair_id,
                    "corpus_role": role,
                    "source_run": "unit",
                    "used_as_positive": role == POSITIVE_ROLE,
                    "role_weight": 1.0 if role == POSITIVE_ROLE else 0.0,
                }
            )
        return output

    write_csv_rows(materialization_dir / "positive_policy_target_rows.csv", rows(positive_count, POSITIVE_ROLE, 0))
    write_csv_rows(
        materialization_dir / "diagnostic_policy_guardrail_rows.csv",
        rows(diagnostic_count, DIAGNOSTIC_ROLE, 100),
    )
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"stable checkpoint bytes")
    return materialization_dir, checkpoint


def test_projection_repair_reduces_residual_without_checkpoint(tmp_path: Path) -> None:
    base_model = TinyRecurrentActor()
    materialization_dir, checkpoint = _make_bundle(tmp_path, model=base_model, positive_count=4, diagnostic_count=2)

    def loader(path: Path, device: str) -> TinyRecurrentActor:
        del path, device
        return copy.deepcopy(base_model)

    run_dir = tmp_path / "run"
    summary = run_contour_aware_exact_objective_projection_repair(
        materialization_run_dir=materialization_dir,
        checkpoint=checkpoint,
        run_dir=run_dir,
        expected_positive_count=4,
        expected_diagnostic_count=2,
        perturb_scale=0.02,
        perturb_seed=17,
        repair_steps=80,
        learning_rate=0.01,
        load_model_fn=loader,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["initial_positive_exact_residual_mean"] > 1e-8
    assert summary["repaired_positive_exact_residual_mean"] < summary["initial_positive_exact_residual_mean"]
    assert summary["positive_exact_residual_reduction_ratio"] >= 0.50
    assert summary["repaired_actor_mean_l2_to_base"] <= summary["initial_actor_mean_l2_to_base"]
    assert summary["non_actor_mean_parameter_delta_max"] == 0.0
    assert summary["repaired_checkpoint_written"] is False
    assert not list(run_dir.rglob("*.pt"))
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "repair_summary.csv").exists()
    assert (run_dir / "guardrail_summary.csv").exists()


def test_projection_repair_reports_unreduced_zero_step_probe(tmp_path: Path) -> None:
    base_model = TinyRecurrentActor()
    materialization_dir, checkpoint = _make_bundle(tmp_path, model=base_model, positive_count=4, diagnostic_count=2)

    def loader(path: Path, device: str) -> TinyRecurrentActor:
        del path, device
        return copy.deepcopy(base_model)

    summary = run_contour_aware_exact_objective_projection_repair(
        materialization_run_dir=materialization_dir,
        checkpoint=checkpoint,
        run_dir=tmp_path / "run",
        expected_positive_count=4,
        expected_diagnostic_count=2,
        perturb_scale=0.02,
        perturb_seed=17,
        repair_steps=0,
        learning_rate=0.01,
        load_model_fn=loader,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["null_result_classification"] == "projection_residual_not_reduced"
    assert summary["positive_exact_residual_reduction_ratio"] == 0.0
    assert summary["repaired_checkpoint_written"] is False
