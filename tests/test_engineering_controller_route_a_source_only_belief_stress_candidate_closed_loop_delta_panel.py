import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel import (
    DEFAULT_NEXT_BLOCKER,
    run_belief_stress_candidate_closed_loop_delta_panel,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.train_ppo import ActorCritic


def _model_config(**overrides):
    config = {
        "device": "cpu",
        "actor_encoder": "human_view_online_gru",
        "actor_history_length": 1,
        "action_sequence_horizon": 1,
        "response_prediction_dim": 0,
        "response_prediction_horizon": 1,
        "log_std_init": -1.0,
        "log_std_min": -5.0,
        "log_std_max": -0.5,
    }
    config.update(overrides)
    return config


def _write_checkpoint(path: Path, *, bias_delta: float = 0.0):
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
        action_sequence_horizon=1,
    )
    with torch.no_grad():
        model.actor_mean.bias[0].add_(bias_delta)
        model.actor_mean.bias[1].sub_(bias_delta)
        model.actor_mean.bias[2].add_(bias_delta)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _model_config(),
        },
        path,
    )


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_belief_stress_candidate_closed_loop_delta_panel_writes_claim_safe_pairs(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2784.md"
    follow_up_manifest = tmp_path / "m2785.json"
    m2783_audit = tmp_path / "m2783.md"
    m2783_audit.write_text("# audit\n", encoding="utf-8")
    source_checkpoint = tmp_path / "source.pt"
    candidate_checkpoint = tmp_path / "candidate.pt"
    _write_checkpoint(source_checkpoint, bias_delta=0.0)
    _write_checkpoint(candidate_checkpoint, bias_delta=0.05)

    summary = run_belief_stress_candidate_closed_loop_delta_panel(
        output_dir,
        m2783_audit=m2783_audit,
        source_checkpoint=source_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
        device="cpu",
        seed_count=2,
        horizon_steps=2,
        milestone="m2784-test",
        next_blocker="m2785-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel_preflight_pass"
    )
    assert summary["m2782_status_pass"] is True
    assert summary["source_checkpoint_hash"] != summary["candidate_checkpoint_hash"]
    assert summary["curriculum_row_count"] == 18
    assert summary["paired_execution_row_count"] == 72
    assert summary["paired_delta_row_count"] == 36
    assert summary["proof_gate_row_count"] == 12
    assert summary["generalization_gate_row_count"] == 6
    assert summary["promotion_guard_row_count"] == 4
    assert summary["actor_guard_row_count"] == 7
    assert summary["mitigation_reference_guard_row_count"] == 8
    assert summary["claim_boundary_row_count"] == 11
    assert summary["gate_matrix_row_count"] == 22
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["actor_visible_stress_admission_curriculum_labels_detected"] is False
    assert summary["paired_rows_complete"] is True
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["m2785_follow_up_manifest_registered"] is True

    execution_rows = _read_csv(output_dir / "paired_execution_rows.csv")
    delta_rows = _read_csv(output_dir / "paired_delta_rows.csv")
    proof_rows = _read_csv(output_dir / "proof_retention_gate_rows.csv")
    generalization_rows = _read_csv(output_dir / "generalization_delta_gate_rows.csv")
    promotion_rows = _read_csv(output_dir / "promotion_guard_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    mitigation_rows = _read_csv(output_dir / "mitigation_reference_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    m2785 = json.loads(follow_up_manifest.read_text())

    assert len(execution_rows) == 72
    assert len(delta_rows) == 36
    assert len(gate_rows) == 22
    assert {row["checkpoint_subject"] for row in execution_rows} == {"source", "candidate"}
    assert {row["observation_shape"] for row in execution_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in execution_rows} == {str(ACTION_DIM)}
    assert {row["actor_visible_label"] for row in execution_rows} == {"False"}
    assert {row["hidden_or_oracle_actor_inputs_required"] for row in execution_rows} == {"False"}
    assert {row["diagnostic_only"] for row in execution_rows} == {"True"}
    assert {row["paired_row_complete"] for row in delta_rows} == {"True"}
    assert {row["diagnostic_only"] for row in delta_rows} == {"True"}
    assert {row["ranking_admissible"] for row in delta_rows} == {"False"}
    assert {row["winner_selected"] for row in delta_rows} == {"False"}
    assert {row["success_rate_verdict_computed"] for row in delta_rows} == {"False"}
    assert all(row["status_pass"] == "True" for row in proof_rows)
    assert all(row["status_pass"] == "True" for row in generalization_rows)
    assert all(row["status_pass"] == "True" for row in promotion_rows)
    assert all(row["status_pass"] == "True" for row in actor_rows)
    assert {row["ordinary_denominator_allowed"] for row in mitigation_rows} == {"False"}
    assert {row["included_in_paired_execution_rows"] for row in mitigation_rows} == {"False"}
    assert {row["included_in_delta_rows"] for row in mitigation_rows} == {"False"}
    assert {
        row["claim_id"]: row["claim_made"]
        for row in claim_rows
        if row["claim_id"] in {"validation_result", "ranking_result", "checkpoint_promotion"}
    } == {
        "validation_result": "False",
        "ranking_result": "False",
        "checkpoint_promotion": "False",
    }
    assert m2785["id"] == DEFAULT_NEXT_BLOCKER
    assert m2785["training_stage"]["stage"] == "process"
    assert doc_path.exists()
