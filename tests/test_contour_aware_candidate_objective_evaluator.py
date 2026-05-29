from __future__ import annotations

import json
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_candidate_objective_evaluator import (
    diagnostic_guardrail_rows,
    positive_objective_rows,
    run_contour_aware_candidate_objective_evaluator,
)
from autodrift.contour_aware_candidate_materialization import CLEAN_LABEL


def _candidate_row(pair_id: str, *, source_edge: str = "a|b") -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "label": CLEAN_LABEL,
        "m1602_label": CLEAN_LABEL,
        "source_edge": source_edge,
        "history_max_gap": "0.10",
        "control_max_gap": "0.01",
        "donor_response_action_only_gap": "0.02",
        "hidden_specific_gap": "0.08",
        "corpus_role": POSITIVE_ROLE,
        "role_weight": "1.0",
    }


def _diagnostic_row(pair_id: str) -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "label": "control_only_positive",
        "m1602_label": "control_only_positive",
        "source_edge": "x|y",
        "rule_reason": "negative_diagnostic_edge",
        "history_max_gap": "0.01",
        "control_max_gap": "0.02",
        "donor_response_action_only_gap": "0.02",
        "hidden_specific_gap": "-0.01",
        "corpus_role": DIAGNOSTIC_ROLE,
        "role_weight": "0.0",
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.write_text(
        ",".join(keys)
        + "\n"
        + "\n".join(",".join(str(row.get(key, "")) for key in keys) for row in rows)
        + "\n",
        encoding="utf-8",
    )


def _write_candidate_package(package_dir: Path) -> None:
    package_dir.mkdir()
    positives = []
    for edge, count in zip(["a|b", "c|d", "e|f", "g|h"], [13, 12, 8, 6]):
        for index in range(count):
            positives.append(_candidate_row(f"{edge}-{index}", source_edge=edge))
    diagnostics = [_diagnostic_row(f"d-{index}") for index in range(232)]
    _write_csv(package_dir / "positive_candidate_rows.csv", positives)
    _write_csv(package_dir / "diagnostic_guardrail_rows.csv", diagnostics)
    (package_dir / "summary.json").write_text(
        json.dumps(
            {
                "result_class": "contour_aware_candidate_corpus_export",
                "positive_candidate_count": 39,
                "diagnostic_guardrail_count": 232,
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "corpus_manifest.json").write_text(
        json.dumps(
            {
                "result_class": "contour_aware_candidate_corpus_package",
                "positive_candidate_count": 39,
                "diagnostic_guardrail_count": 232,
                "roles": [POSITIVE_ROLE, DIAGNOSTIC_ROLE],
                "public_proof_artifact": True,
                "private_holdout_used": False,
                "paper_level_claim_supported": False,
                "level3_self_id_claim_supported": False,
                "training_ready": False,
                "requires_objective_design_before_training": True,
            }
        ),
        encoding="utf-8",
    )


def test_positive_objective_rows_are_finite_and_positive_only() -> None:
    rows = positive_objective_rows([_candidate_row("p0")])

    assert len(rows) == 1
    assert rows[0]["positive_objective_row"] is True
    assert rows[0]["finite"] is True
    assert rows[0]["history_control_separation_margin"] > 0.0
    assert rows[0]["candidate_objective_residual"] > 0.0


def test_diagnostic_guardrail_rows_are_never_positive() -> None:
    rows = diagnostic_guardrail_rows([_diagnostic_row("d0")])

    assert len(rows) == 1
    assert rows[0]["used_as_positive"] is False
    assert rows[0]["diagnostic_positive_weight"] == 0.0
    assert rows[0]["finite"] is True


def test_run_evaluator_writes_full_package_artifacts_without_checkpoint_mutation(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    checkpoint = tmp_path / "checkpoint.pt"
    run_dir = tmp_path / "run"
    _write_candidate_package(package_dir)
    checkpoint.write_bytes(b"checkpoint")

    summary = run_contour_aware_candidate_objective_evaluator(
        candidate_run_dir=package_dir,
        checkpoint=checkpoint,
        run_dir=run_dir,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["positive_candidate_count"] == 39
    assert summary["diagnostic_guardrail_count"] == 232
    assert summary["diagnostic_rows_used_as_positive"] is False
    assert summary["diagnostic_positive_weight_sum"] == 0.0
    assert summary["positive_rows_all_clean"] is True
    assert summary["role_metadata_verified"] is True
    assert summary["public_proof_metadata_complete"] is True
    assert summary["all_objective_metrics_finite"] is True
    assert summary["checkpoint_weights_mutated"] is False
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "positive_objective_rows.csv").exists()
    assert (run_dir / "diagnostic_guardrail_objective_rows.csv").exists()
    assert (run_dir / "role_integrity_summary.csv").exists()
    assert (run_dir / "objective_summary.csv").exists()
    written = read_json(run_dir / "summary.json")
    assert written["checkpoint_weights_mutated"] is False
