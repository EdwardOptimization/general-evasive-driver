import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
    DEFAULT_NEXT_BLOCKER,
    run_belief_stress_short_training_continuation_preflight,
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


def _write_checkpoint(path: Path):
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
        action_sequence_horizon=1,
    )
    torch.save(
        {
            "model_state": {
                key: value.detach().cpu() for key, value in model.state_dict().items()
            },
            "config": _model_config(),
        },
        path,
    )


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_belief_stress_short_training_preflight_writes_candidate_and_gates(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2782.md"
    follow_up_manifest = tmp_path / "m2783.json"
    source_checkpoint = tmp_path / "source.pt"
    _write_checkpoint(source_checkpoint)

    summary = run_belief_stress_short_training_continuation_preflight(
        output_dir,
        source_checkpoint=source_checkpoint,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
        device="cpu",
        training_seeds_per_bucket=3,
        proof_seeds_per_bucket=1,
        max_updates=1,
        milestone="m2782-test",
        next_blocker="m2783-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight_pass"
    )
    assert summary["m2779_status_pass"] is True
    assert summary["m2779_gate_matrix_pass"] is True
    assert summary["training_run"] is True
    assert summary["source_only_backend_reset_run"] is True
    assert summary["source_only_backend_step_run"] is True
    assert summary["policy_action_run"] is True
    assert summary["training_curriculum_row_count"] == 18
    assert summary["training_run_row_count"] == 54
    assert summary["proof_holdout_probe_row_count"] == 18
    assert summary["proof_gate_row_count"] == 8
    assert summary["generalization_gate_row_count"] == 6
    assert summary["promotion_guard_row_count"] == 4
    assert summary["candidate_checkpoint_written"] is True
    assert summary["checkpoint_behavior_changed"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["actor_visible_stress_admission_curriculum_labels_detected"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["checkpoint_promoted"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["m2783_follow_up_manifest_registered"] is True

    checkpoint_manifest = json.loads((output_dir / "checkpoint_manifest.json").read_text())
    curriculum_rows = _read_csv(output_dir / "training_curriculum_rows.csv")
    training_rows = _read_csv(output_dir / "training_run_rows.csv")
    proof_rows = _read_csv(output_dir / "proof_gate_rows.csv")
    generalization_rows = _read_csv(output_dir / "generalization_gate_rows.csv")
    promotion_rows = _read_csv(output_dir / "promotion_guard_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    mitigation_rows = _read_csv(output_dir / "mitigation_reference_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    m2783 = json.loads(follow_up_manifest.read_text())

    assert Path(checkpoint_manifest["candidate_checkpoint"]).exists()
    assert checkpoint_manifest["behavior_changed"] is True
    assert checkpoint_manifest["checkpoint_promoted"] is False
    assert checkpoint_manifest["actor_contract_shape_72_action_3"] is True
    assert checkpoint_manifest["hidden_or_oracle_actor_inputs_required"] is False
    assert len(curriculum_rows) == 18
    assert len(training_rows) == 54
    assert len(proof_rows) == 8
    assert len(generalization_rows) == 6
    assert len(promotion_rows) == 4
    assert len(actor_rows) == 6
    assert len(mitigation_rows) == 8
    assert len(gate_rows) == 18
    assert {row["observation_shape"] for row in training_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in training_rows} == {str(ACTION_DIM)}
    assert {row["actor_visible_label"] for row in training_rows} == {"False"}
    assert {row["hidden_or_oracle_actor_inputs_required"] for row in training_rows} == {"False"}
    assert {row["ordinary_denominator_allowed"] for row in mitigation_rows} == {"False"}
    assert {row["included_in_training_rows"] for row in mitigation_rows} == {"False"}
    assert {row["included_in_proof_denominator"] for row in mitigation_rows} == {"False"}
    assert all(row["status_pass"] == "True" for row in proof_rows)
    assert all(row["status_pass"] == "True" for row in generalization_rows)
    assert all(row["status_pass"] == "True" for row in promotion_rows)
    assert {
        row["claim_id"]: row["claim_made"]
        for row in claim_rows
        if row["claim_id"] in {"validation_result", "ranking_result", "checkpoint_promotion"}
    } == {
        "validation_result": "False",
        "ranking_result": "False",
        "checkpoint_promotion": "False",
    }
    assert m2783["id"] == DEFAULT_NEXT_BLOCKER
    assert m2783["training_stage"]["stage"] == "process"
    assert doc_path.exists()
