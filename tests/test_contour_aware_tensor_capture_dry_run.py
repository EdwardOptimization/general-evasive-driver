from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import write_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_tensor_capture_dry_run import (
    DRY_RUN_DIAGNOSTIC_IDS,
    DRY_RUN_POSITIVE_IDS,
    REQUIRED_VARIANTS,
    CapturedTensorRow,
    run_contour_aware_tensor_capture_dry_run,
)


def _row(pair_id: str, *, role: str, source_run: str) -> dict[str, object]:
    used = role == POSITIVE_ROLE
    return {
        "pair_id": pair_id,
        "label": "history_control_separated" if used else "history_positive_control_dominated",
        "missing_variants": "",
        "source_edge": "a|b",
        "target_anchor_id": f"{pair_id}|target",
        "donor_anchor_id": f"{pair_id}|donor",
        "target_source_family": "a",
        "donor_source_family": "b",
        "target_anchor_window": "decision",
        "donor_anchor_window": "decision",
        "selected_pair_id": pair_id.split("::", 1)[-1].split("|", 1)[0],
        "original_pair_id": "pair-original",
        "source_run": source_run,
        "corpus_role": role,
        "role_weight": 1.0 if used else 0.0,
        "public_proof_artifact": True,
        "training_ready": False,
    }


def _make_package(tmp_path: Path) -> tuple[Path, Path, Path]:
    candidate_dir = tmp_path / "candidate"
    replay_dir = tmp_path / "replay"
    candidate_dir.mkdir()
    replay_dir.mkdir()
    positives = [
        _row(DRY_RUN_POSITIVE_IDS[0], role=POSITIVE_ROLE, source_run="m1592_clean_repair"),
        _row(DRY_RUN_POSITIVE_IDS[1], role=POSITIVE_ROLE, source_run="m1595_balanced_repair"),
    ]
    diagnostics = [
        _row(DRY_RUN_DIAGNOSTIC_IDS[0], role=DIAGNOSTIC_ROLE, source_run="m1588_selector"),
        _row(DRY_RUN_DIAGNOSTIC_IDS[1], role=DIAGNOSTIC_ROLE, source_run="m1595_balanced_repair"),
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
        preferred = np.asarray([0.1, 0.2, 0.3], dtype=np.float32) + index * 0.01
        wrong = np.asarray([0.2, 0.3, 0.4], dtype=np.float32) + index * 0.01
        donor_plus = np.asarray([0.3, 0.4, 0.5], dtype=np.float32) + index * 0.01
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
            trace_rows.append({"pair_id": row["pair_id"], "variant": variant, "variant_found": True})
    return captured, trace_rows, []


def test_tensor_capture_dry_run_writes_expected_arrays(tmp_path: Path) -> None:
    candidate_dir, replay_dir, checkpoint = _make_package(tmp_path)
    run_dir = tmp_path / "run"

    summary = run_contour_aware_tensor_capture_dry_run(
        candidate_run_dir=candidate_dir,
        replay_run_dir=replay_dir,
        checkpoint=checkpoint,
        run_dir=run_dir,
        capture_fn=_fake_capture,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["dry_run_row_count"] == 4
    assert summary["positive_capture_count"] == 2
    assert summary["diagnostic_capture_count"] == 2
    assert summary["observation_shape"] == [4, 72]
    assert summary["preferred_action_shape"] == [4, 3]
    assert summary["hidden_dim"] == 6
    assert summary["diagnostic_rows_used_as_positive"] is False
    assert summary["full_target_corpus_materialized"] is False
    arrays = np.load(run_dir / "captured_targets.npz")
    assert arrays["observation"].shape == (4, 72)
    assert arrays["correct_hidden"].shape == (4, 6)
    assert arrays["wrong_hidden"].shape == (4, 6)
    assert arrays["donor_plus_hidden_action"].shape == (4, 3)

    with (run_dir / "captured_target_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    diagnostics = [row for row in rows if row["corpus_role"] == DIAGNOSTIC_ROLE]
    assert len(diagnostics) == 2
    assert all(row["used_as_positive"] == "False" for row in diagnostics)
    assert all(float(row["role_weight"]) == 0.0 for row in diagnostics)


def test_tensor_capture_dry_run_reports_missing_capture(tmp_path: Path) -> None:
    candidate_dir, replay_dir, checkpoint = _make_package(tmp_path)

    def missing_capture(selected_rows, replay_rows_by_id, variants_by_pair, checkpoint, device):
        del selected_rows, replay_rows_by_id, variants_by_pair, checkpoint, device
        return [], [], [{"pair_id": DRY_RUN_POSITIVE_IDS[0], "missing_reasons": "target_anchor_replay_missing"}]

    run_dir = tmp_path / "run"
    summary = run_contour_aware_tensor_capture_dry_run(
        candidate_run_dir=candidate_dir,
        replay_run_dir=replay_dir,
        checkpoint=checkpoint,
        run_dir=run_dir,
        capture_fn=missing_capture,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["null_result_classification"] == "tensor_capture_missing_rows"
    assert summary["missing_capture_row_count"] == 1
    assert not (run_dir / "captured_targets.npz").exists()
    assert (run_dir / "missing_capture_rows.csv").exists()
