import csv

import torch

from autodrift.engineering_controller_bounded_measured_behavior_panel import (
    METRIC_COMPLETENESS_FIELDNAMES,
    MEASURED_EVENT_FIELDNAMES,
    MITIGATION_REFERENCE_SUBJECT,
    build_metric_completeness_rows,
    materialize_bounded_measured_behavior_panel,
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


def test_materialize_bounded_measured_behavior_panel_writes_protocol_rows(tmp_path):
    checkpoint = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint)
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2521.md"

    summary = materialize_bounded_measured_behavior_panel(
        output_dir,
        checkpoint_path=checkpoint,
        horizon_steps=2,
        milestone="m2521-test",
        next_blocker="m2522-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_bounded_measured_behavior_panel_preflight_pass"
    )
    assert summary["measured_behavior_row_count"] == 9
    assert summary["measured_event_row_count"] == 9
    assert summary["metric_completeness_row_count"] == 40
    assert summary["telemetry_row_count"] == 18
    assert summary["expected_telemetry_row_count"] == 18
    assert summary["all_attempted_subject_role_rows_retained"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["all_actions_finite"] is True
    assert summary["all_actions_within_bounds"] is True
    assert summary["seed_lineage_explicit"] is True
    assert summary["mitigation_reference_subject"] == MITIGATION_REFERENCE_SUBJECT
    assert summary["mitigation_delta_supported_row_count"] == 9
    assert summary["all_metrics_supported"] is True
    assert summary["ranking_or_winner_fields_emitted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["success_rate_verdict_field_emitted"] is False
    assert summary["driver_performance_claim_made"] is False

    behavior_rows = _read_csv(output_dir / "measured_behavior_rows.csv")
    event_rows = _read_csv(output_dir / "measured_event_rows.csv")
    completeness_rows = _read_csv(output_dir / "metric_completeness_rows.csv")

    assert len(behavior_rows) == 9
    assert len(event_rows) == 9
    assert len(completeness_rows) == 40
    assert {row["subject_id"] for row in behavior_rows} == {
        "m1154_policy_actor",
        "coast_open_loop",
        "straight_full_brake_open_loop",
    }
    assert {row["scenario_role"] for row in behavior_rows} == {
        "stable_aes",
        "drift_required_recovery",
        "unavoidable_mitigation",
    }
    assert {row["observation_shape"] for row in behavior_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in behavior_rows} == {str(ACTION_DIM)}
    assert {row["evidence_layer"] for row in behavior_rows} == {"source_only_diagnostic"}
    assert {row["attempted_row_retained"] for row in behavior_rows} == {"True"}
    assert {row["mitigation_reference_subject"] for row in behavior_rows} == {
        MITIGATION_REFERENCE_SUBJECT
    }
    assert {row["ranking_or_winner_field_emitted"] for row in behavior_rows} == {"False"}
    assert all(row["seed"] for row in behavior_rows)
    assert all(row["mitigation_delta_against_reference"] for row in behavior_rows)
    assert set(event_rows[0]) == set(MEASURED_EVENT_FIELDNAMES)
    assert set(completeness_rows[0]) == set(METRIC_COMPLETENESS_FIELDNAMES)
    assert {row["missing_row_count"] for row in completeness_rows} == {"0"}
    assert {row["support_status"] for row in completeness_rows} == {
        "supported_by_m2521_measured_behavior_panel"
    }
    assert doc_path.exists()


def test_metric_completeness_marks_missing_values():
    metric_registry = [
        {"metric_name": "seed", "metric_family": "metadata", "actor_visible": "False"},
        {"metric_name": "collision_event", "metric_family": "avoidance", "actor_visible": "False"},
    ]
    rows = [{"seed": 2501, "collision_event": True}, {"seed": "", "collision_event": False}]

    completeness = build_metric_completeness_rows(metric_registry, rows)

    assert completeness[0]["metric_name"] == "seed"
    assert completeness[0]["supported_row_count"] == 1
    assert completeness[0]["missing_row_count"] == 1
    assert completeness[0]["support_status"] == "partial_or_missing_after_m2521"
    assert completeness[1]["supported_row_count"] == 2
    assert completeness[1]["missing_row_count"] == 0
