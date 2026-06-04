import csv

import torch

from autodrift.engineering_controller_bounded_measured_behavior_panel import (
    MITIGATION_REFERENCE_SUBJECT,
)
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    OPEN_LOOP_SUBJECT_IDS,
    POLICY_SUBJECT_IDS,
)
from autodrift.engineering_controller_route_a_source_only_fresh_generalization_panel import (
    DEFAULT_FRESH_SEED_COUNT,
    DYNAMICS_AXES,
    ROLE_FAMILIES,
    build_fresh_generalization_panel_specs,
    materialize_route_a_source_only_fresh_generalization_panel,
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


def test_fresh_generalization_panel_specs_cover_roles_seeds_and_axes():
    run_items, seed_rows, axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=DEFAULT_FRESH_SEED_COUNT
    )

    assert len(run_items) == 32
    assert len(seed_rows) == 32
    assert len(axis_rows) == 32
    assert {row["role_family"] for row in seed_rows} == set(ROLE_FAMILIES)
    assert {row["dynamics_axis_id"] for row in seed_rows} == set(DYNAMICS_AXES)
    assert {
        len({row["seed"] for row in seed_rows if row["role_family"] == role})
        for role in ROLE_FAMILIES
    } == {4}
    assert {row["source_only_fault_axis_applied"] for row in axis_rows} == {False, True}
    assert {row["actor_visible_allowed"] for row in axis_rows} == {False}


def test_materialize_fresh_generalization_panel_writes_axis_complete_rows(tmp_path):
    checkpoints = {}
    for subject_id in POLICY_SUBJECT_IDS:
        checkpoint = tmp_path / f"{subject_id}.pt"
        _write_checkpoint(checkpoint)
        checkpoints[subject_id] = checkpoint
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2641.md"

    summary = materialize_route_a_source_only_fresh_generalization_panel(
        output_dir,
        policy_checkpoints=checkpoints,
        fresh_seed_count=DEFAULT_FRESH_SEED_COUNT,
        horizon_steps=1,
        milestone="m2641-test",
        next_blocker="m2642-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_fresh_generalization_panel_preflight_pass"
    )
    assert summary["role_family_count"] == 4
    assert summary["fresh_seed_count_per_role"] == 4
    assert summary["dynamics_axis_count"] == 2
    assert summary["comparison_subject_count"] == 5
    assert summary["policy_checkpoint_subject_count"] == 3
    assert summary["open_loop_subject_count"] == 2
    assert summary["seed_panel_spec_row_count"] == 32
    assert summary["dynamics_axis_row_count"] == 32
    assert summary["measured_behavior_row_count"] == 160
    assert summary["measured_event_row_count"] == 160
    assert summary["telemetry_row_count"] == 160
    assert summary["expected_telemetry_rows"] == 160
    assert summary["all_policy_checkpoints_admitted"] is True
    assert summary["all_attempted_subject_role_seed_axis_rows_retained"] is True
    assert summary["role_seed_axis_matrix_complete"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["actor_visibility_guard_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["mitigation_reference_subject"] == MITIGATION_REFERENCE_SUBJECT
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["delay_noise_diagnostic_metadata_only"] is True
    assert summary["actuator_delay_applied_to_backend"] is False
    assert summary["sensor_noise_applied_to_actor_input"] is False

    subject_rows = _read_csv(output_dir / "subject_registry.csv")
    seed_rows = _read_csv(output_dir / "seed_panel_spec.csv")
    axis_rows = _read_csv(output_dir / "dynamics_axis_rows.csv")
    guard_rows = _read_csv(output_dir / "actor_visibility_guard_rows.csv")
    telemetry_rows = _read_csv(output_dir / "telemetry_rows.csv")
    behavior_rows = _read_csv(output_dir / "measured_behavior_rows.csv")
    event_rows = _read_csv(output_dir / "measured_event_rows.csv")
    completeness_rows = _read_csv(output_dir / "metric_completeness_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert len(subject_rows) == 5
    assert len(seed_rows) == 32
    assert len(axis_rows) == 32
    assert len(guard_rows) >= 10
    assert len(telemetry_rows) == 160
    assert len(behavior_rows) == 160
    assert len(event_rows) == 160
    assert len(completeness_rows) == 40
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["subject_id"] for row in subject_rows} == set(POLICY_SUBJECT_IDS) | set(
        OPEN_LOOP_SUBJECT_IDS
    )
    assert {row["scenario_role"] for row in behavior_rows} == set(ROLE_FAMILIES)
    assert {row["dynamics_axis_id"] for row in behavior_rows} == set(DYNAMICS_AXES)
    assert {row["dynamics_axis_id"] for row in telemetry_rows} == set(DYNAMICS_AXES)
    assert {row["observation_shape"] for row in behavior_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in behavior_rows} == {str(ACTION_DIM)}
    assert {row["evidence_layer"] for row in behavior_rows} == {"source_only_diagnostic"}
    assert {row["attempted_row_retained"] for row in behavior_rows} == {"True"}
    assert {row["denominator_gap_reason"] for row in behavior_rows} == {""}
    assert {row["ranking_or_winner_field_emitted"] for row in behavior_rows} == {"False"}
    assert {row["diagnostic_only"] for row in telemetry_rows} == {"True"}
    assert {row["missing_row_count"] for row in completeness_rows} == {"0"}
    assert {row["actor_visible_allowed"] for row in guard_rows} == {"False"}
    assert doc_path.exists()
