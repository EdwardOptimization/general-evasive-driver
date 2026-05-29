from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import write_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_full_target_materialization import (
    run_contour_aware_full_target_materialization,
)
from autodrift.contour_aware_tensor_capture_dry_run import CapturedTensorRow, REQUIRED_VARIANTS


def _row(index: int, *, role: str, source_run: str) -> dict[str, object]:
    pair_id = f"{source_run}::selected-{index:04d}|left_target"
    return {
        "pair_id": pair_id,
        "label": "history_control_separated" if role == POSITIVE_ROLE else "history_positive_control_dominated",
        "missing_variants": "",
        "source_edge": "a|b",
        "target_anchor_id": f"{pair_id}|target",
        "donor_anchor_id": f"{pair_id}|donor",
        "target_source_family": "a",
        "donor_source_family": "b",
        "target_anchor_window": "decision",
        "donor_anchor_window": "decision",
        "selected_pair_id": f"selected-{index:04d}",
        "original_pair_id": f"pair-{index:04d}",
        "source_run": source_run,
        "corpus_role": role,
        "role_weight": 1.0 if role == POSITIVE_ROLE else 0.0,
        "public_proof_artifact": True,
        "training_ready": False,
    }


def _make_package(tmp_path: Path, *, positive_count: int, diagnostic_count: int) -> tuple[Path, Path, Path]:
    candidate_dir = tmp_path / "candidate"
    replay_dir = tmp_path / "replay"
    candidate_dir.mkdir()
    replay_dir.mkdir()
    positives = [_row(index, role=POSITIVE_ROLE, source_run="m1592_clean_repair") for index in range(positive_count)]
    diagnostics = [
        _row(index + positive_count, role=DIAGNOSTIC_ROLE, source_run="m1595_balanced_repair")
        for index in range(diagnostic_count)
    ]
    replay_rows: list[dict[str, object]] = []
    intervention_rows: list[dict[str, object]] = []
    for row in positives + diagnostics:
        pair_id = str(row["pair_id"])
        replay_rows.append(
            {
                "pair_id": pair_id,
                "target_anchor_id": row["target_anchor_id"],
                "donor_anchor_id": row["donor_anchor_id"],
                "target_source_family": row["target_source_family"],
                "donor_source_family": row["donor_source_family"],
                "target_anchor_window": row["target_anchor_window"],
                "donor_anchor_window": row["donor_anchor_window"],
                "target_anchor_step": 3,
                "donor_anchor_step": 4,
                "same_window": True,
                "step_distance": 1,
                "contrasting_normal_outcome": False,
                "diagnostic_late_reveal": False,
                "donor_rank": 1,
                "source_run": row["source_run"],
                "rule_bucket": "primary" if row["corpus_role"] == POSITIVE_ROLE else "diagnostic",
                "rule_reason": "test",
            }
        )
        for variant in REQUIRED_VARIANTS:
            intervention_rows.append(
                {
                    "pair_id": pair_id,
                    "variant": variant,
                    "first_action_steer": 0.1,
                    "first_action_throttle": 0.2,
                    "first_action_brake": 0.3,
                }
            )
    write_csv_rows(candidate_dir / "positive_candidate_rows.csv", positives)
    write_csv_rows(candidate_dir / "diagnostic_guardrail_rows.csv", diagnostics)
    write_csv_rows(replay_dir / "replay_pair_rows.csv", replay_rows)
    write_csv_rows(replay_dir / "intervention_rows.csv", intervention_rows)
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"stable checkpoint bytes")
    return candidate_dir, replay_dir, checkpoint


def _fake_capture(selected_rows, replay_rows_by_id, variants_by_pair, checkpoint, device):
    del replay_rows_by_id, variants_by_pair, checkpoint, device
    captured = []
    trace_rows = []
    for index, row in enumerate(selected_rows):
        obs = np.full((72,), index + 1, dtype=np.float32)
        correct_hidden = np.full((6,), index + 0.25, dtype=np.float32)
        wrong_hidden = np.full((6,), -index - 0.5, dtype=np.float32)
        preferred = np.asarray([0.1, 0.2, 0.3], dtype=np.float32)
        wrong = np.asarray([0.2, 0.3, 0.4], dtype=np.float32)
        donor_plus = np.asarray([0.3, 0.4, 0.5], dtype=np.float32)
        metadata = {
            "target_id": row["pair_id"],
            "pair_id": row["pair_id"],
            "corpus_role": row["corpus_role"],
            "source_run": row["source_run"],
            "source_run_dir": f"runs/{row['source_run']}",
            "source_edge": row["source_edge"],
            "target_anchor_id": row["target_anchor_id"],
            "donor_anchor_id": row["donor_anchor_id"],
            "selected_pair_id": row["selected_pair_id"],
            "original_pair_id": row["original_pair_id"],
            "normal_variant_found": True,
            "wrong_history_variant_found": True,
            "donor_plus_hidden_variant_found": True,
            "tensor_index": index,
            "used_as_positive": row["corpus_role"] == POSITIVE_ROLE,
            "role_weight": 1.0 if row["corpus_role"] == POSITIVE_ROLE else 0.0,
            "public_proof_artifact": True,
            "training_ready": False,
            "source_preferred_action_l2": 0.0,
            "source_wrong_history_action_l2": 0.0,
            "source_donor_plus_hidden_action_l2": 0.0,
        }
        captured.append(
            CapturedTensorRow(
                metadata=metadata,
                observation=obs,
                correct_hidden=correct_hidden,
                wrong_hidden=wrong_hidden,
                preferred_action=preferred,
                wrong_history_action=wrong,
                donor_plus_hidden_action=donor_plus,
            )
        )
        for variant in REQUIRED_VARIANTS:
            trace_rows.append({"pair_id": row["pair_id"], "corpus_role": row["corpus_role"], "variant": variant})
    return captured, trace_rows, []


def test_full_target_materialization_writes_split_arrays(tmp_path: Path) -> None:
    candidate_dir, replay_dir, checkpoint = _make_package(tmp_path, positive_count=3, diagnostic_count=2)

    run_dir = tmp_path / "run"
    summary = run_contour_aware_full_target_materialization(
        candidate_run_dir=candidate_dir,
        replay_run_dir=replay_dir,
        checkpoint=checkpoint,
        run_dir=run_dir,
        expected_positive_count=3,
        expected_diagnostic_count=2,
        capture_fn=_fake_capture,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["positive_policy_target_count"] == 3
    assert summary["diagnostic_policy_guardrail_count"] == 2
    assert summary["positive_observation_shape"] == [3, 72]
    assert summary["diagnostic_observation_shape"] == [2, 72]
    assert summary["positive_preferred_action_shape"] == [3, 3]
    assert summary["diagnostic_preferred_action_shape"] == [2, 3]
    assert summary["hidden_dim"] == 6
    assert summary["diagnostic_rows_used_as_positive"] is False
    assert summary["diagnostic_positive_weight_sum"] == 0.0
    assert summary["training_ready"] is False
    assert summary["loss_constructed"] is False

    positive_arrays = np.load(run_dir / "positive_policy_targets.npz")
    diagnostic_arrays = np.load(run_dir / "diagnostic_policy_guardrails.npz")
    assert positive_arrays["observation"].shape == (3, 72)
    assert positive_arrays["correct_hidden"].shape == (3, 6)
    assert positive_arrays["donor_plus_hidden_action"].shape == (3, 3)
    assert diagnostic_arrays["observation"].shape == (2, 72)
    assert diagnostic_arrays["wrong_hidden"].shape == (2, 6)

    with (run_dir / "diagnostic_policy_guardrail_rows.csv").open(newline="", encoding="utf-8") as handle:
        diagnostics = list(csv.DictReader(handle))
    assert len(diagnostics) == 2
    assert all(row["used_as_positive"] == "False" for row in diagnostics)
    assert all(float(row["role_weight"]) == 0.0 for row in diagnostics)


def test_full_target_materialization_reports_missing_capture(tmp_path: Path) -> None:
    candidate_dir, replay_dir, checkpoint = _make_package(tmp_path, positive_count=3, diagnostic_count=2)

    def missing_capture(selected_rows, replay_rows_by_id, variants_by_pair, checkpoint, device):
        del selected_rows, replay_rows_by_id, variants_by_pair, checkpoint, device
        return [], [], [{"pair_id": "missing", "missing_reasons": "target_anchor_replay_missing"}]

    run_dir = tmp_path / "run"
    summary = run_contour_aware_full_target_materialization(
        candidate_run_dir=candidate_dir,
        replay_run_dir=replay_dir,
        checkpoint=checkpoint,
        run_dir=run_dir,
        expected_positive_count=3,
        expected_diagnostic_count=2,
        capture_fn=missing_capture,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["null_result_classification"] == "tensor_capture_missing_rows"
    assert summary["missing_capture_row_count"] == 1
    assert not (run_dir / "positive_policy_targets.npz").exists()
    assert not (run_dir / "diagnostic_policy_guardrails.npz").exists()
    assert (run_dir / "missing_capture_rows.csv").exists()
