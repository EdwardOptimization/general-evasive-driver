import csv

import torch

from autodrift.engineering_controller_route_a_hf0_parity_runtime_materialization import (
    ACTION_MAPPING_FIELDNAMES,
    ACTOR_INFERENCE_FIELDNAMES,
    PARITY_FIELDNAMES,
    RUNTIME_SCHEMA_FIELDNAMES,
    build_action_mapping_checks,
    build_hf0_p0_parity_checks,
    build_runtime_report_schema_rows,
    materialize_route_a_hf0_parity_runtime,
)
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    POLICY_SUBJECT_IDS,
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


def _write_checkpoint(path):
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
        action_sequence_horizon=1,
    )
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _model_config(),
        },
        path,
    )


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_build_hf0_p0_parity_and_action_mapping_checks_pass():
    parity_rows = build_hf0_p0_parity_checks()
    action_rows = build_action_mapping_checks()
    schema_rows = build_runtime_report_schema_rows()

    assert len(parity_rows) == 5
    assert set(parity_rows[0]) == set(PARITY_FIELDNAMES)
    assert {row["observed_observation_shape"] for row in parity_rows} == {P0_OBSERVATION_DIM}
    assert {row["status_pass"] for row in parity_rows} == {True}
    assert {row["hidden_or_oracle_actor_input_detected"] for row in parity_rows} == {False}

    assert len(action_rows) == 7
    assert set(action_rows[0]) == set(ACTION_MAPPING_FIELDNAMES)
    assert {row["status_pass"] for row in action_rows} == {True}
    assert {
        row["invalid_input_rejected"]
        for row in action_rows
        if row["check_id"] in {"invalid_shape_rejected", "non_finite_rejected"}
    } == {True}

    assert [row["field_name"] for row in schema_rows] == ACTOR_INFERENCE_FIELDNAMES
    assert set(schema_rows[0]) == set(RUNTIME_SCHEMA_FIELDNAMES)


def test_materialize_route_a_hf0_parity_runtime_writes_expected_artifacts(tmp_path):
    checkpoints = {}
    for subject_id in POLICY_SUBJECT_IDS:
        checkpoint = tmp_path / f"{subject_id}.pt"
        _write_checkpoint(checkpoint)
        checkpoints[subject_id] = checkpoint
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2548.md"

    summary = materialize_route_a_hf0_parity_runtime(
        output_dir,
        policy_checkpoints=checkpoints,
        batch_sizes=(1,),
        warmup_iterations=0,
        measured_iterations=1,
        seed=123,
        milestone="m2548-test",
        next_blocker="m2549-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_hf0_parity_runtime_materialization_pass"
    )
    assert summary["hf0_p0_parity_check_count"] == 5
    assert summary["hf0_p0_parity_checks_all_pass"] is True
    assert summary["action_mapping_check_count"] == 7
    assert summary["action_mapping_checks_all_pass"] is True
    assert summary["runtime_schema_field_count"] == len(ACTOR_INFERENCE_FIELDNAMES)
    assert summary["actor_inference_cost_row_count"] == 3
    assert summary["expected_actor_inference_cost_row_count"] == 3
    assert summary["all_policy_checkpoints_admitted"] is True
    assert summary["all_runtime_observation_shape_72"] is True
    assert summary["all_runtime_action_shape_3"] is True
    assert summary["all_runtime_actions_finite"] is True
    assert summary["all_runtime_actions_within_bounds"] is True
    assert summary["all_runtime_forward_times_positive"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["external_high_fidelity_simulation_included"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False

    parity_rows = _read_csv(output_dir / "hf0_p0_parity_checks.csv")
    action_rows = _read_csv(output_dir / "action_mapping_checks.csv")
    schema_rows = _read_csv(output_dir / "runtime_report_schema.csv")
    runtime_rows = _read_csv(output_dir / "actor_inference_cost_rows.csv")
    gate_rows = _read_csv(output_dir / "materialization_gate_matrix.csv")

    assert len(parity_rows) == 5
    assert len(action_rows) == 7
    assert len(schema_rows) == len(ACTOR_INFERENCE_FIELDNAMES)
    assert len(runtime_rows) == 3
    assert len(gate_rows) == summary["materialization_gate_count"]
    assert {row["subject_id"] for row in runtime_rows} == set(POLICY_SUBJECT_IDS)
    assert {row["batch_size"] for row in runtime_rows} == {"1"}
    assert {row["observation_shape"] for row in runtime_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in runtime_rows} == {str(ACTION_DIM)}
    assert {row["action_outputs_interpreted_as_control"] for row in runtime_rows} == {"False"}
    assert {row["ranking_or_winner_field_emitted"] for row in runtime_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
