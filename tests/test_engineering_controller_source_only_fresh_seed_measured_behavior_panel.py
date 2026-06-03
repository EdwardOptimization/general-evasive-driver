import csv

import torch

from autodrift.engineering_controller_bounded_measured_behavior_panel import (
    MITIGATION_REFERENCE_SUBJECT,
)
from autodrift.engineering_controller_source_only_fresh_seed_measured_behavior_panel import (
    DEFAULT_SEED_COUNT,
    build_seed_panel_specs,
    materialize_source_only_fresh_seed_measured_behavior_panel,
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


def test_build_seed_panel_specs_expands_roles_with_distinct_fresh_seeds():
    run_items, rows = build_seed_panel_specs(seed_count=DEFAULT_SEED_COUNT)

    assert len(run_items) == 15
    assert len(rows) == 15
    assert {row["role_family"] for row in rows} == {
        "stable_aes",
        "drift_required_recovery",
        "unavoidable_mitigation",
    }
    assert {row["actor_input_contract_changed"] for row in rows} == {False}
    assert len({row["seed"] for row in rows}) == 15
    assert len({row["fixture_variant_digest"] for row in rows}) == 15


def test_materialize_fresh_seed_measured_behavior_panel_writes_denominator_rows(tmp_path):
    checkpoint = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint)
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2523.md"

    summary = materialize_source_only_fresh_seed_measured_behavior_panel(
        output_dir,
        checkpoint_path=checkpoint,
        seed_count=DEFAULT_SEED_COUNT,
        horizon_steps=1,
        milestone="m2523-test",
        next_blocker="m2524-test",
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_source_only_fresh_seed_measured_behavior_panel_preflight_pass"
    )
    assert summary["seed_count_per_role"] == DEFAULT_SEED_COUNT
    assert summary["seed_panel_spec_row_count"] == 15
    assert summary["measured_behavior_row_count"] == 45
    assert summary["measured_event_row_count"] == 45
    assert summary["metric_completeness_row_count"] == 40
    assert summary["telemetry_row_count"] == 45
    assert summary["expected_telemetry_row_count"] == 45
    assert summary["all_attempted_subject_role_seed_rows_retained"] is True
    assert summary["denominator_gap_count"] == 0
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["seed_lineage_explicit"] is True
    assert summary["mitigation_reference_subject"] == MITIGATION_REFERENCE_SUBJECT
    assert summary["mitigation_delta_supported_row_count"] == 45
    assert summary["all_metrics_supported"] is True
    assert summary["ranking_or_winner_fields_emitted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False

    seed_panel_rows = _read_csv(output_dir / "seed_panel_spec.csv")
    behavior_rows = _read_csv(output_dir / "measured_behavior_rows.csv")
    event_rows = _read_csv(output_dir / "measured_event_rows.csv")
    completeness_rows = _read_csv(output_dir / "metric_completeness_rows.csv")

    assert len(seed_panel_rows) == 15
    assert len(behavior_rows) == 45
    assert len(event_rows) == 45
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
    assert {row["denominator_gap_reason"] for row in behavior_rows} == {""}
    assert {row["ranking_or_winner_field_emitted"] for row in behavior_rows} == {"False"}
    assert {row["missing_row_count"] for row in completeness_rows} == {"0"}
    assert {row["support_status"] for row in completeness_rows} == {
        "supported_by_m2523_source_only_fresh_seed_measured_behavior_panel"
    }
    assert doc_path.exists()
