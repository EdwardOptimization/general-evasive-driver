from __future__ import annotations

from pathlib import Path

import pytest

from autodrift.artifacts import write_json
from autodrift.fusion_actor_artifact_replay_gate import run_fusion_actor_artifact_replay_gate


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    checkpoint = tmp_path / "candidate.pt"
    checkpoint.write_text("checkpoint", encoding="utf-8")
    summary = tmp_path / "artifact_summary.json"
    write_json(summary, {"artifact_sha256": "fake"})
    return checkpoint, summary


def _sanity_pass(**kwargs):
    return {
        "checkpoint_sanity_pass": True,
        "artifact_sha256_match": True,
        "p0_actor_contract_pass": True,
    }


def _sanity_fail(**kwargs):
    return {
        "checkpoint_sanity_pass": False,
        "artifact_sha256_match": False,
        "p0_actor_contract_pass": False,
    }


def _replay_pass(**kwargs):
    return {
        "run_dir": str(kwargs["run_dir"]),
        "rows": 3,
        "baseline_success_drop_count": 2,
        "candidate_success_drop_count": 2,
        "normal_success_delta": 0.0,
        "normal_margin_mean_delta": 0.0,
        "margin_gap_mean_delta": 0.0,
        "success_drop_count_delta": 0,
        "normal_success_retention_pass": True,
        "normal_margin_retention_pass": True,
        "wrong_history_gap_retention_pass": True,
        "success_drop_count_retention_pass": True,
        "gate_pass": True,
    }


def _replay_fail(**kwargs):
    output = _replay_pass(**kwargs)
    output["gate_pass"] = False
    output["wrong_history_gap_retention_pass"] = False
    return output


def test_artifact_replay_first_check_passes_when_both_surfaces_pass(tmp_path: Path) -> None:
    checkpoint, artifact_summary = _write_inputs(tmp_path)

    summary = run_fusion_actor_artifact_replay_gate(
        checkpoint=checkpoint,
        artifact_summary=artifact_summary,
        base_checkpoint=tmp_path / "base.pt",
        run_dir=tmp_path / "run",
        replay_fn=_replay_pass,
        sanity_fn=_sanity_pass,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["m183_m170_first_check_pass"] is True
    assert summary["m267_m264_first_check_pass"] is True
    assert summary["result_class"] == "fusion_actor_artifact_first_check_public_pass"
    assert (tmp_path / "run" / "checkpoint_sanity.json").exists()
    assert (tmp_path / "run" / "first_check_gate_summary.csv").exists()


def test_artifact_replay_first_check_fails_on_sanity(tmp_path: Path) -> None:
    checkpoint, artifact_summary = _write_inputs(tmp_path)

    summary = run_fusion_actor_artifact_replay_gate(
        checkpoint=checkpoint,
        artifact_summary=artifact_summary,
        base_checkpoint=tmp_path / "base.pt",
        run_dir=tmp_path / "run",
        replay_fn=_replay_pass,
        sanity_fn=_sanity_fail,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["checkpoint_sanity_pass"] is False
    assert summary["metric_artifact_count"] == 1
    assert summary["result_class"] == "fusion_actor_artifact_first_check_sanity_failure"


def test_artifact_replay_first_check_classifies_proof_washout(tmp_path: Path) -> None:
    checkpoint, artifact_summary = _write_inputs(tmp_path)

    summary = run_fusion_actor_artifact_replay_gate(
        checkpoint=checkpoint,
        artifact_summary=artifact_summary,
        base_checkpoint=tmp_path / "base.pt",
        run_dir=tmp_path / "run",
        replay_fn=_replay_fail,
        sanity_fn=_sanity_pass,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["proof_washout_count"] == 2
    assert summary["result_class"] == "fusion_actor_artifact_first_check_m183_m170_failure"


def test_artifact_replay_gate_rejects_non_first_check_mode(tmp_path: Path) -> None:
    checkpoint, artifact_summary = _write_inputs(tmp_path)

    with pytest.raises(ValueError, match="first_check"):
        run_fusion_actor_artifact_replay_gate(
            checkpoint=checkpoint,
            artifact_summary=artifact_summary,
            base_checkpoint=tmp_path / "base.pt",
            run_dir=tmp_path / "run",
            mode="full",
            replay_fn=_replay_pass,
            sanity_fn=_sanity_pass,
        )
