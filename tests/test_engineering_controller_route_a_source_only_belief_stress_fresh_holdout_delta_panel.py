import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel import (
    DEFAULT_NEXT_BLOCKER,
    run_belief_stress_fresh_holdout_delta_panel,
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


def _write_m2784_sources(path: Path):
    path.mkdir(parents=True)
    (path / "summary.json").write_text(
        json.dumps(
            {
                "status_pass": True,
                "seed_count": 4,
                "horizon_steps": 1,
                "paired_delta_row_count": 2,
            }
        ),
        encoding="utf-8",
    )
    (path / "paired_delta_rows.csv").write_text(
        "pair_id,seed_index\nm2784_pair_a,0\nm2784_pair_b,3\n",
        encoding="utf-8",
    )
    (path / "gate_matrix.csv").write_text("gate_id,status_pass\nm2784_gate,True\n", encoding="utf-8")


def test_belief_stress_fresh_holdout_delta_panel_writes_claim_safe_holdout_pairs(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2787.md"
    follow_up_manifest = tmp_path / "m2788.json"
    m2786_synthesis = tmp_path / "m2786.md"
    m2785_audit = tmp_path / "m2785.md"
    m2784_dir = tmp_path / "m2784"
    m2786_synthesis.write_text("# synthesis\n", encoding="utf-8")
    m2785_audit.write_text("# audit\n", encoding="utf-8")
    _write_m2784_sources(m2784_dir)
    source_checkpoint = tmp_path / "source.pt"
    candidate_checkpoint = tmp_path / "candidate.pt"
    _write_checkpoint(source_checkpoint, bias_delta=0.0)
    _write_checkpoint(candidate_checkpoint, bias_delta=0.05)

    summary = run_belief_stress_fresh_holdout_delta_panel(
        output_dir,
        m2786_synthesis=m2786_synthesis,
        m2785_audit=m2785_audit,
        m2784_dir=m2784_dir,
        source_checkpoint=source_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
        device="cpu",
        seed_start_index=4,
        seed_count=2,
        horizon_steps=2,
        milestone="m2787-test",
        next_blocker="m2788-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel_preflight_pass"
    )
    assert summary["m2784_status_pass"] is True
    assert summary["m2782_status_pass"] is True
    assert summary["source_checkpoint_hash"] != summary["candidate_checkpoint_hash"]
    assert summary["seed_start_index"] == 4
    assert summary["seed_count"] == 2
    assert summary["fresh_holdout_seed_indices"] == [4, 5]
    assert summary["m2784_seed_indices"] == [0, 3]
    assert summary["fresh_holdout_seed_indices_disjoint_from_m2784"] is True
    assert summary["horizon_longer_than_m2784"] is True
    assert summary["curriculum_row_count"] == 18
    assert summary["paired_execution_row_count"] == 72
    assert summary["paired_delta_row_count"] == 36
    assert summary["proof_gate_row_count"] == 13
    assert summary["generalization_gate_row_count"] == 8
    assert summary["promotion_guard_row_count"] == 4
    assert summary["gate_matrix_row_count"] == 25
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["actor_visible_stress_admission_curriculum_labels_detected"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["m2788_follow_up_manifest_registered"] is True

    execution_rows = _read_csv(output_dir / "paired_execution_rows.csv")
    delta_rows = _read_csv(output_dir / "paired_delta_rows.csv")
    generalization_rows = _read_csv(output_dir / "generalization_holdout_gate_rows.csv")
    mitigation_rows = _read_csv(output_dir / "mitigation_reference_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    m2788 = json.loads(follow_up_manifest.read_text())

    assert len(execution_rows) == 72
    assert len(delta_rows) == 36
    assert len(gate_rows) == 25
    assert {row["checkpoint_subject"] for row in execution_rows} == {"source", "candidate"}
    assert {row["seed_index"] for row in execution_rows} == {"4", "5"}
    assert {row["seed_index"] for row in delta_rows} == {"4", "5"}
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
    assert all(row["status_pass"] == "True" for row in generalization_rows)
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
    assert m2788["id"] == DEFAULT_NEXT_BLOCKER
    assert m2788["training_stage"]["stage"] == "process"
    assert doc_path.exists()
