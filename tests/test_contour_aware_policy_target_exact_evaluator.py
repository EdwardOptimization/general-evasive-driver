from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import write_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_policy_target_exact_evaluator import (
    run_contour_aware_policy_target_exact_evaluator,
)


def _action_from(observation: np.ndarray, hidden: np.ndarray) -> np.ndarray:
    return np.asarray([observation[0], hidden[0], 0.25], dtype=np.float32)


def _fake_predict(model, observation, hidden):
    del model
    return _action_from(observation, hidden)


def _make_bundle(tmp_path: Path, *, positive_count: int, diagnostic_count: int) -> tuple[Path, Path]:
    materialization_dir = tmp_path / "materialization"
    materialization_dir.mkdir()

    def arrays(count: int, offset: int) -> dict[str, np.ndarray]:
        observation = np.stack([np.full((72,), offset + index + 1, dtype=np.float32) for index in range(count)], axis=0)
        correct_hidden = np.stack([np.full((6,), 0.1 + index, dtype=np.float32) for index in range(count)], axis=0)
        wrong_hidden = np.stack([np.full((6,), 0.2 + index, dtype=np.float32) for index in range(count)], axis=0)
        preferred = np.stack([_action_from(observation[index], correct_hidden[index]) for index in range(count)], axis=0)
        wrong = np.stack([_action_from(observation[index], wrong_hidden[index]) for index in range(count)], axis=0)
        donor_plus = wrong + np.asarray([0.05, 0.0, 0.0], dtype=np.float32)
        return {
            "observation": observation,
            "correct_hidden": correct_hidden,
            "wrong_hidden": wrong_hidden,
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
                    "source_run": "source",
                    "used_as_positive": role == POSITIVE_ROLE,
                    "role_weight": 1.0 if role == POSITIVE_ROLE else 0.0,
                    "source_preferred_action_l2": 0.0,
                    "source_wrong_history_action_l2": 0.0,
                    "source_donor_plus_hidden_action_l2": 0.0,
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


def test_exact_evaluator_writes_role_safe_residuals(tmp_path: Path) -> None:
    materialization_dir, checkpoint = _make_bundle(tmp_path, positive_count=3, diagnostic_count=2)

    run_dir = tmp_path / "run"
    summary = run_contour_aware_policy_target_exact_evaluator(
        materialization_run_dir=materialization_dir,
        checkpoint=checkpoint,
        run_dir=run_dir,
        expected_positive_count=3,
        expected_diagnostic_count=2,
        predict_fn=_fake_predict,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["positive_policy_target_count"] == 3
    assert summary["diagnostic_policy_guardrail_count"] == 2
    assert summary["positive_policy_action_residual_l2_max"] == 0.0
    assert summary["diagnostic_policy_action_residual_l2_max"] == 0.0
    assert summary["donor_plus_action_used_as_loss_target"] is False
    assert summary["diagnostic_rows_used_as_positive"] is False
    assert summary["loss_constructed"] is False
    assert summary["objective_config_written"] is False

    with (run_dir / "diagnostic_guardrail_rows.csv").open(newline="", encoding="utf-8") as handle:
        diagnostics = list(csv.DictReader(handle))
    assert len(diagnostics) == 2
    assert all(row["used_as_positive"] == "False" for row in diagnostics)
    assert all(float(row["role_weight"]) == 0.0 for row in diagnostics)
    assert all(row["donor_plus_action_used_as_loss_target"] == "False" for row in diagnostics)


def test_exact_evaluator_rejects_diagnostic_positive_leakage(tmp_path: Path) -> None:
    materialization_dir, checkpoint = _make_bundle(tmp_path, positive_count=3, diagnostic_count=2)
    rows = []
    with (materialization_dir / "diagnostic_policy_guardrail_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["used_as_positive"] = True
    rows[0]["role_weight"] = 1.0
    write_csv_rows(materialization_dir / "diagnostic_policy_guardrail_rows.csv", rows)

    summary = run_contour_aware_policy_target_exact_evaluator(
        materialization_run_dir=materialization_dir,
        checkpoint=checkpoint,
        run_dir=tmp_path / "run",
        expected_positive_count=3,
        expected_diagnostic_count=2,
        predict_fn=_fake_predict,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["null_result_classification"] == "diagnostic_positive_leakage"
    assert summary["diagnostic_rows_used_as_positive"] is True
    assert summary["diagnostic_positive_weight_sum"] == 1.0
