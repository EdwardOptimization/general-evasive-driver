import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight import (
    DEFAULT_NEXT_BLOCKER,
    run_guardrailed_multi_objective_training_preflight,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
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


def _write_m2787_sources(path: Path):
    path.mkdir(parents=True)
    (path / "summary.json").write_text(
        json.dumps(
            {
                "status_pass": True,
                "required_artifacts_present": True,
                "gate_matrix_pass": True,
                "seed_start_index": 4,
                "seed_count": 2,
                "horizon_steps": 2,
                "paired_delta_row_count": 4,
            }
        ),
        encoding="utf-8",
    )
    fieldnames = [
        "pair_id",
        "role_family",
        "dynamics_axis",
        "stress_family",
        "seed_index",
        "candidate_minus_source_minimum_obstacle_clearance_m",
        "candidate_minus_source_minimum_road_margin_m",
        "candidate_minus_source_final_speed_mps",
        "candidate_minus_source_max_abs_yaw_rate",
        "candidate_minus_source_throttle_brake_conflict_proxy",
        "mean_action_delta_l1",
    ]
    rows = [
        ("a", "stable_avoidable", "fresh_nominal_or_role_default", "recurrent_hidden_reset_stress", 4, -0.003, 0.002, 0.001, -0.0004, 0.0, 0.0004),
        ("b", "stable_aes", "fresh_nominal_or_role_default", "previous_command_history_stress", 5, 0.002, 0.003, 0.002, -0.0002, 0.0, 0.0003),
        ("c", "drift_required_recovery", "fresh_fault_delay_noise", "held_actuator_history_stress", 4, -0.001, 0.004, 0.003, -0.0001, 0.0, 0.0005),
        ("d", "stable_avoidable", "fresh_fault_delay_noise", "held_actuator_history_stress", 5, 0.001, 0.002, 0.001, -0.0003, 0.0, 0.0004),
    ]
    with (path / "paired_delta_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(zip(fieldnames, row)))
    (path / "gate_matrix.csv").write_text("gate_id,status_pass\nm2787_gate,True\n", encoding="utf-8")


def test_guardrailed_multi_objective_training_preflight_writes_guarded_candidate_and_gates(tmp_path):
    source_checkpoint = tmp_path / "source.pt"
    _write_checkpoint(source_checkpoint)

    m2782_dir = tmp_path / "m2782"
    run_belief_stress_short_training_continuation_preflight(
        m2782_dir,
        source_checkpoint=source_checkpoint,
        follow_up_manifest=tmp_path / "m2783.json",
        doc_path=tmp_path / "m2782.md",
        device="cpu",
        training_seeds_per_bucket=3,
        proof_seeds_per_bucket=1,
        max_updates=1,
        milestone="m2782-test",
        next_blocker="m2783-test",
    )

    m2787_dir = tmp_path / "m2787"
    _write_m2787_sources(m2787_dir)
    m2790_design = tmp_path / "m2790.md"
    m2789_synthesis = tmp_path / "m2789.md"
    m2790_design.write_text("# design\n", encoding="utf-8")
    m2789_synthesis.write_text("# synthesis\n", encoding="utf-8")

    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2791.md"
    follow_up_manifest = tmp_path / "m2792.json"
    base_candidate_checkpoint = (
        m2782_dir / "checkpoints" / "m2782_belief_stress_short_training_candidate.pt"
    )
    summary = run_guardrailed_multi_objective_training_preflight(
        output_dir,
        m2790_design=m2790_design,
        m2789_synthesis=m2789_synthesis,
        m2787_dir=m2787_dir,
        m2782_dir=m2782_dir,
        source_checkpoint=source_checkpoint,
        base_candidate_checkpoint=base_candidate_checkpoint,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
        device="cpu",
        training_seeds_per_bucket=3,
        proof_seeds_per_bucket=2,
        behavior_retention_seed_count=4,
        max_updates=1,
        milestone="m2791-test",
        next_blocker="m2792-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight_pass"
    )
    assert summary["m2787_status_pass"] is True
    assert summary["m2782_status_pass"] is True
    assert summary["training_run"] is True
    assert summary["source_only_backend_reset_run"] is True
    assert summary["source_only_backend_step_run"] is True
    assert summary["policy_action_run"] is True
    assert summary["training_objective_row_count"] == 18
    assert summary["training_run_row_count"] == 54
    assert summary["proof_holdout_probe_row_count"] == 36
    assert summary["proof_gate_row_count"] == 13
    assert summary["generalization_gate_row_count"] == 6
    assert summary["behavior_retention_gate_row_count"] == 7
    assert summary["promotion_guard_row_count"] == 4
    assert summary["gate_matrix_row_count"] == 30
    assert summary["candidate_checkpoint_written"] is True
    assert summary["checkpoint_behavior_changed"] is True
    assert summary["candidate_checkpoint_hash"] != summary["base_candidate_checkpoint_hash"]
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["actor_visible_stress_admission_curriculum_labels_detected"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["obstacle_clearance_regression_guard_required"] is True
    assert summary["obstacle_clearance_guard_hard_before_objectives"] is True
    assert summary["m2787_obstacle_clearance_negative_count"] == 2
    assert summary["checkpoint_promoted"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["m2792_follow_up_manifest_registered"] is True

    checkpoint_manifest = json.loads((output_dir / "checkpoint_manifest.json").read_text())
    objective_rows = _read_csv(output_dir / "training_objective_rows.csv")
    training_rows = _read_csv(output_dir / "training_run_rows.csv")
    proof_rows = _read_csv(output_dir / "proof_gate_rows.csv")
    generalization_rows = _read_csv(output_dir / "generalization_gate_rows.csv")
    behavior_rows = _read_csv(output_dir / "behavior_retention_gate_rows.csv")
    promotion_rows = _read_csv(output_dir / "promotion_guard_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    mitigation_rows = _read_csv(output_dir / "mitigation_reference_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    m2792 = json.loads(follow_up_manifest.read_text())

    assert Path(checkpoint_manifest["candidate_checkpoint"]).exists()
    assert checkpoint_manifest["behavior_changed"] is True
    assert checkpoint_manifest["checkpoint_promoted"] is False
    assert checkpoint_manifest["obstacle_clearance_regression_guard_required"] is True
    assert checkpoint_manifest["road_margin_objective_subordinate_to_clearance"] is True
    assert checkpoint_manifest["yaw_rate_objective_subordinate_to_clearance"] is True
    assert len(objective_rows) == 18
    assert len(training_rows) == 54
    assert len(proof_rows) == 13
    assert len(generalization_rows) == 6
    assert len(behavior_rows) == 7
    assert len(promotion_rows) == 4
    assert len(actor_rows) == 6
    assert len(mitigation_rows) == 8
    assert len(gate_rows) == 30
    assert {row["observation_shape"] for row in training_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in training_rows} == {str(ACTION_DIM)}
    assert {row["actor_visible_label"] for row in training_rows} == {"False"}
    assert {row["hidden_or_oracle_actor_inputs_required"] for row in training_rows} == {"False"}
    assert {row["obstacle_clearance_guard_required"] for row in objective_rows} == {"True"}
    assert {row["ordinary_denominator_allowed"] for row in mitigation_rows} == {"False"}
    assert {row["included_in_training_rows"] for row in mitigation_rows} == {"False"}
    assert {row["included_in_proof_denominator"] for row in mitigation_rows} == {"False"}
    assert all(row["status_pass"] == "True" for row in proof_rows)
    assert all(row["status_pass"] == "True" for row in generalization_rows)
    assert all(row["status_pass"] == "True" for row in behavior_rows)
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
    assert m2792["id"] == DEFAULT_NEXT_BLOCKER
    assert m2792["training_stage"]["stage"] == "process"
    assert doc_path.exists()
