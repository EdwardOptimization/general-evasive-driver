import csv

import torch

from autodrift.hf0_source_only_baseline_comparison_panel import (
    COMPARISON_SUBJECTS,
    PANEL_FIELDNAMES,
    ROLE_FAMILIES,
    TELEMETRY_FIELDNAMES,
    comparison_subjects,
    run_preflight,
    run_source_only_baseline_comparison,
    subject_physical_control,
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


def test_comparison_subjects_define_deployed_action_baselines():
    subjects = {subject.subject_id: subject for subject in comparison_subjects()}

    assert set(subjects) == {
        "m1154_policy_actor",
        "coast_open_loop",
        "straight_full_brake_open_loop",
    }
    assert subjects["m1154_policy_actor"].policy_action is True
    assert subjects["m1154_policy_actor"].fixed_action is None
    assert subject_physical_control(subjects["coast_open_loop"]) == (0.0, 0.0, 0.0)
    assert subject_physical_control(subjects["straight_full_brake_open_loop"]) == (
        0.0,
        0.0,
        1.0,
    )


def test_run_source_only_baseline_comparison_records_diagnostic_subject_rows(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    telemetry_rows, panel_rows, summary = run_source_only_baseline_comparison(
        checkpoint_path,
        horizon_steps=2,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_source_only_baseline_comparison_preflight_pass"
    )
    assert summary["checkpoint_admitted"] is True
    assert summary["comparison_subject_count"] == len(COMPARISON_SUBJECTS)
    assert summary["role_count"] == len(ROLE_FAMILIES)
    assert summary["reset_count"] == 9
    assert summary["telemetry_row_count"] == 18
    assert summary["expected_telemetry_row_count"] == 18
    assert summary["role_subject_panel_row_count"] == 9
    assert summary["role_subject_panel_covers_expected"] is True
    assert summary["role_reset_digests_match_across_subjects"] is True
    assert summary["role_reset_digests_differentiated"] is True
    assert summary["all_reset_observations_shape_72"] is True
    assert summary["all_step_observations_shape_72"] is True
    assert summary["all_action_shapes_3"] is True
    assert summary["all_actions_finite"] is True
    assert summary["all_actions_within_bounds"] is True
    assert summary["all_backend_statuses_running"] is True
    assert summary["all_diagnostic_wheel_force_counts_4"] is True
    assert summary["panel_rows_are_diagnostic_only"] is True
    assert summary["success_rate_computed"] is False
    assert summary["controller_family_verdict_computed"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["verdict_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["fixture_labels_enter_actor_input"] is False
    assert summary["hidden_values_enter_actor_input"] is False

    assert len(telemetry_rows) == 18
    assert len(panel_rows) == 9
    assert {row.comparison_subject for row in telemetry_rows} == {
        subject.subject_id for subject in COMPARISON_SUBJECTS
    }
    assert {row.role_family for row in telemetry_rows} == set(ROLE_FAMILIES)
    assert all(row.parameterized_fixture for row in telemetry_rows)
    assert all(row.diagnostic_only for row in telemetry_rows)
    assert all(row.diagnostic_only for row in panel_rows)
    assert all(not row.success_rate_computed for row in panel_rows)
    assert all(not row.verdict_claim_made for row in panel_rows)

    coast_rows = [row for row in telemetry_rows if row.comparison_subject == "coast_open_loop"]
    brake_rows = [
        row
        for row in telemetry_rows
        if row.comparison_subject == "straight_full_brake_open_loop"
    ]
    assert {row.physical_throttle for row in coast_rows} == {0.0}
    assert {row.physical_brake for row in coast_rows} == {0.0}
    assert {row.physical_throttle for row in brake_rows} == {0.0}
    assert {row.physical_brake for row in brake_rows} == {1.0}


def test_run_preflight_writes_summary_telemetry_and_controller_role_panel(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    summary = run_preflight(
        tmp_path / "run",
        checkpoint_path=checkpoint_path,
        horizon_steps=1,
        next_blocker="m2502-engineering-controller-source-only-baseline-comparison-result-audit",
    )

    assert summary["status_pass"] is True
    assert (
        summary["milestone"]
        == "m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight"
    )
    assert summary["telemetry_row_count"] == 9
    assert summary["role_subject_panel_row_count"] == 9
    assert summary["telemetry_rows"] == str(tmp_path / "run" / "telemetry_rows.csv")
    assert summary["controller_role_metric_panel"] == str(
        tmp_path / "run" / "controller_role_metric_panel.csv"
    )

    with (tmp_path / "run" / "telemetry_rows.csv").open(newline="", encoding="utf-8") as handle:
        telemetry_rows = list(csv.DictReader(handle))
    with (tmp_path / "run" / "controller_role_metric_panel.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        panel_rows = list(csv.DictReader(handle))

    assert len(telemetry_rows) == 9
    assert len(panel_rows) == 9
    assert set(telemetry_rows[0]) == set(TELEMETRY_FIELDNAMES)
    assert set(panel_rows[0]) == set(PANEL_FIELDNAMES)
    assert {row["observation_shape"] for row in telemetry_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in telemetry_rows} == {str(ACTION_DIM)}
    assert {row["parameterized_fixture"] for row in telemetry_rows} == {"True"}
    assert {row["diagnostic_only"] for row in telemetry_rows} == {"True"}
    assert {row["diagnostic_only"] for row in panel_rows} == {"True"}
    assert {row["success_rate_computed"] for row in panel_rows} == {"False"}
    assert {row["verdict_claim_made"] for row in panel_rows} == {"False"}
