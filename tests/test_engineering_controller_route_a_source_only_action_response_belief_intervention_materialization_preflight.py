import csv
import json

import torch

from autodrift.engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight import (
    build_candidate_intervention_matrix,
    build_intervention_condition_rows,
    build_source_only_candidate_rows,
    materialize_source_only_action_response_belief_intervention_preflight,
)
from autodrift.engineering_controller_route_a_source_only_fresh_generalization_panel import (
    DEFAULT_FRESH_SEED_COUNT,
    DYNAMICS_AXES,
    ROLE_FAMILIES,
    build_fresh_generalization_panel_specs,
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


def test_m2773_candidate_and_intervention_matrix_matches_design_surface(tmp_path):
    run_items, _seed_rows, _axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=DEFAULT_FRESH_SEED_COUNT
    )
    candidates = build_source_only_candidate_rows(
        run_items,
        source_checkpoint=tmp_path / "actor.pt",
        horizon_steps=80,
    )
    conditions = build_intervention_condition_rows()
    matrix = build_candidate_intervention_matrix(candidates, conditions, horizon_steps=80)

    assert len(candidates) == 32
    assert {row["role_family"] for row in candidates} == set(ROLE_FAMILIES)
    assert {row["dynamics_axis"] for row in candidates} == set(DYNAMICS_AXES)
    assert {row["actor_visible_labels"] for row in candidates} == {False}
    assert {row["intervention_condition_id"] for row in conditions} == {
        "normal_recurrent",
        "reset_hidden_each_step",
        "zero_previous_command_history",
        "held_actuator_history",
    }
    assert {row["actor_input_shape_changed"] for row in conditions} == {False}
    assert {row["actor_input_feature_added"] for row in conditions} == {False}
    assert {row["hidden_or_oracle_value_added"] for row in conditions} == {False}
    assert len(matrix) == 128
    assert {row["expected_trace_rows"] for row in matrix} == {80}
    mitigation = [row for row in candidates if row["role_family"] == "unavoidable_mitigation"]
    assert len(mitigation) == 8
    assert {row["ordinary_success_denominator_allowed"] for row in mitigation} == {False}


def test_materialize_m2773_writes_claim_safe_intervention_artifacts(tmp_path):
    checkpoint = tmp_path / "actor.pt"
    _write_checkpoint(checkpoint)
    m2641_dir = tmp_path / "m2641"
    m2655_dir = tmp_path / "m2655"
    m2641_dir.mkdir()
    m2655_dir.mkdir()
    (m2641_dir / "summary.json").write_text(json.dumps({"status_pass": True}), encoding="utf-8")
    (m2641_dir / "measured_behavior_rows.csv").write_text("row_id\n", encoding="utf-8")
    (m2641_dir / "measured_event_rows.csv").write_text("row_id\n", encoding="utf-8")
    (m2641_dir / "telemetry_rows.csv").write_text("row_id\n", encoding="utf-8")
    (m2655_dir / "summary.json").write_text(json.dumps({"status_pass": True}), encoding="utf-8")
    design = tmp_path / "m2772.md"
    design.write_text("# design\n", encoding="utf-8")
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2773.md"
    follow_up_manifest = tmp_path / "m2774.json"

    summary = materialize_source_only_action_response_belief_intervention_preflight(
        output_dir,
        m2772_design=design,
        m2641_dir=m2641_dir,
        m2655_dir=m2655_dir,
        source_checkpoint=checkpoint,
        follow_up_manifest=follow_up_manifest,
        horizon_steps=1,
        milestone="m2773-test",
        next_blocker="m2774-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["candidate_row_count"] == 32
    assert summary["intervention_condition_count"] == 4
    assert summary["candidate_intervention_row_count"] == 128
    assert summary["intervention_execution_row_count"] == 128
    assert summary["intervention_failure_row_count"] == 0
    assert summary["action_response_trace_row_count"] == 128
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["actor_visible_label_detected"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["m2774_follow_up_manifest_registered"] is True

    candidates = _read_csv(output_dir / "source_only_candidate_rows.csv")
    conditions = _read_csv(output_dir / "intervention_condition_rows.csv")
    matrix = _read_csv(output_dir / "candidate_intervention_matrix.csv")
    executions = _read_csv(output_dir / "intervention_execution_rows.csv")
    failures = _read_csv(output_dir / "intervention_failure_rows.csv")
    traces = _read_csv(output_dir / "action_response_trace_rows.csv")
    actor_guards = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gates = _read_csv(output_dir / "gate_matrix.csv")

    assert len(candidates) == 32
    assert len(conditions) == 4
    assert len(matrix) == 128
    assert len(executions) == 128
    assert len(failures) == 0
    assert len(traces) == 128
    assert {row["observation_shape"] for row in executions} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in executions} == {str(ACTION_DIM)}
    assert {row["diagnostic_only"] for row in executions} == {"True"}
    assert {row["actor_visible_allowed"] for row in actor_guards} == {"False"}
    assert {row["status_pass"] for row in actor_guards} == {"True"}
    assert {row["claim_made"] for row in claim_rows} == {"False"}
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    assert {row["status_pass"] for row in gates} == {"True"}
    assert follow_up_manifest.exists()
    assert doc_path.exists()
