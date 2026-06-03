import csv

import torch

from autodrift.engineering_controller_bounded_measured_behavior_panel import (
    MITIGATION_REFERENCE_SUBJECT,
)
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    DEFAULT_SEED_COUNT,
    OPEN_LOOP_SUBJECT_IDS,
    POLICY_SUBJECT_IDS,
    materialize_route_a_source_only_execution_readiness_panel,
    route_a_subjects,
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


def test_route_a_subjects_define_three_policy_checkpoints_and_two_references(tmp_path):
    checkpoints = {
        subject_id: tmp_path / f"{subject_id}.pt"
        for subject_id in POLICY_SUBJECT_IDS
    }
    subjects = route_a_subjects(checkpoints)
    by_id = {subject.subject_id: subject for subject in subjects}

    assert set(by_id) == set(POLICY_SUBJECT_IDS) | set(OPEN_LOOP_SUBJECT_IDS)
    assert {by_id[subject_id].policy_action for subject_id in POLICY_SUBJECT_IDS} == {True}
    assert {by_id[subject_id].fixed_action for subject_id in POLICY_SUBJECT_IDS} == {None}
    assert by_id["coast_open_loop"].fixed_action == (0.0, -1.0, -1.0)
    assert by_id["straight_full_brake_open_loop"].fixed_action == (0.0, -1.0, 1.0)
    assert by_id["m2532_guarded_repair_policy"].promotion_status == "not_promoted"
    assert by_id["m2537_mitigation_preserving_policy"].promotion_status == "not_promoted"


def test_materialize_route_a_source_only_execution_readiness_panel_writes_denominator_rows(tmp_path):
    checkpoints = {}
    for subject_id in POLICY_SUBJECT_IDS:
        checkpoint = tmp_path / f"{subject_id}.pt"
        _write_checkpoint(checkpoint)
        checkpoints[subject_id] = checkpoint
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2544.md"

    summary = materialize_route_a_source_only_execution_readiness_panel(
        output_dir,
        policy_checkpoints=checkpoints,
        seed_count=DEFAULT_SEED_COUNT,
        horizon_steps=1,
        milestone="m2544-test",
        next_blocker="m2545-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_execution_readiness_panel_preflight_pass"
    )
    assert summary["comparison_subject_count"] == 5
    assert summary["policy_checkpoint_subject_count"] == 3
    assert summary["open_loop_subject_count"] == 2
    assert summary["all_policy_checkpoints_admitted"] is True
    assert summary["seed_count_per_role"] == DEFAULT_SEED_COUNT
    assert summary["seed_panel_spec_row_count"] == 15
    assert summary["subject_registry_row_count"] == 5
    assert summary["measured_behavior_row_count"] == 75
    assert summary["measured_event_row_count"] == 75
    assert summary["metric_completeness_row_count"] == 40
    assert summary["telemetry_row_count"] == 75
    assert summary["expected_telemetry_row_count"] == 75
    assert summary["all_attempted_subject_role_seed_rows_retained"] is True
    assert summary["denominator_gap_count"] == 0
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["seed_lineage_explicit"] is True
    assert summary["mitigation_reference_subject"] == MITIGATION_REFERENCE_SUBJECT
    assert summary["mitigation_delta_supported_row_count"] == 75
    assert summary["all_metrics_supported"] is True
    assert summary["ranking_or_winner_fields_emitted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["driver_performance_claim_made"] is False

    subject_rows = _read_csv(output_dir / "subject_registry.csv")
    seed_panel_rows = _read_csv(output_dir / "seed_panel_spec.csv")
    telemetry_rows = _read_csv(output_dir / "telemetry_rows.csv")
    behavior_rows = _read_csv(output_dir / "measured_behavior_rows.csv")
    event_rows = _read_csv(output_dir / "measured_event_rows.csv")
    completeness_rows = _read_csv(output_dir / "metric_completeness_rows.csv")

    assert len(subject_rows) == 5
    assert len(seed_panel_rows) == 15
    assert len(telemetry_rows) == 75
    assert len(behavior_rows) == 75
    assert len(event_rows) == 75
    assert len(completeness_rows) == 40
    assert {row["subject_id"] for row in subject_rows} == set(POLICY_SUBJECT_IDS) | set(
        OPEN_LOOP_SUBJECT_IDS
    )
    assert {
        row["checkpoint_admitted"]
        for row in subject_rows
        if row["subject_id"] in POLICY_SUBJECT_IDS
    } == {"True"}
    assert {row["subject_id"] for row in behavior_rows} == set(POLICY_SUBJECT_IDS) | set(
        OPEN_LOOP_SUBJECT_IDS
    )
    assert {row["scenario_role"] for row in behavior_rows} == {
        "stable_aes",
        "drift_required_recovery",
        "unavoidable_mitigation",
    }
    assert {row["observation_shape"] for row in behavior_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in behavior_rows} == {str(ACTION_DIM)}
    assert {row["evidence_layer"] for row in behavior_rows} == {"source_only_diagnostic"}
    assert {row["attempted_row_retained"] for row in behavior_rows} == {"True"}
    assert {row["denominator_gap_reason"] for row in behavior_rows} == {""}
    assert {row["ranking_or_winner_field_emitted"] for row in behavior_rows} == {"False"}
    assert {row["diagnostic_only"] for row in telemetry_rows} == {"True"}
    assert {row["missing_row_count"] for row in completeness_rows} == {"0"}
    assert {row["support_status"] for row in completeness_rows} == {
        "supported_by_m2544_route_a_source_only_execution_readiness_panel"
    }
    assert doc_path.exists()
