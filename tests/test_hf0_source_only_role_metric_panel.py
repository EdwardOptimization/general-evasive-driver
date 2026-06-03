import csv

import torch

from autodrift.hf0_source_only_role_metric_panel import (
    ROLE_FAMILIES,
    PANEL_FIELDNAMES,
    TELEMETRY_FIELDNAMES,
    run_preflight,
    run_source_only_role_metric_panel,
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


def test_run_source_only_role_metric_panel_records_nonverdict_role_metrics(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    telemetry_rows, panel_rows, summary = run_source_only_role_metric_panel(
        checkpoint_path,
        horizon_steps=2,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_source_only_role_metric_panel_pass"
    assert summary["parameterized_role_fixtures"] is False
    assert summary["no_rows_use_parameterized_fixtures"] is True
    assert summary["checkpoint_admitted"] is True
    assert summary["fixture_count"] == 3
    assert summary["reset_count"] == 3
    assert summary["step_count"] == 6
    assert summary["role_metric_panel_row_count"] == 3
    assert summary["role_panel_covers_expected_roles"] is True
    assert summary["panel_rows_are_diagnostic_only"] is True
    assert summary["diagnostic_only_panel"] is True
    assert summary["success_rate_computed"] is False
    assert summary["controller_family_verdict_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["verdict_claim_made"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["all_step_observations_shape_72"] is True
    assert summary["all_action_shapes_3"] is True
    assert summary["all_actions_finite"] is True
    assert summary["all_actions_within_bounds"] is True
    assert summary["all_backend_statuses_running"] is True
    assert summary["all_diagnostic_wheel_force_counts_4"] is True
    assert summary["fixture_labels_enter_actor_input"] is False
    assert summary["hidden_values_enter_actor_input"] is False
    assert len(telemetry_rows) == 6
    assert {row.role_family for row in telemetry_rows} == set(ROLE_FAMILIES)
    assert {row.role_family for row in panel_rows} == set(ROLE_FAMILIES)
    assert all(row.step_count == 2 for row in panel_rows)
    assert all(row.backend_alive_fraction == 1.0 for row in panel_rows)
    assert all(row.bounded_action_fraction == 1.0 for row in panel_rows)
    assert all(row.diagnostic_only for row in panel_rows)
    assert all(not row.success_rate_computed for row in panel_rows)
    assert all(not row.verdict_claim_made for row in panel_rows)


def test_run_source_only_role_metric_panel_uses_parameterized_fixtures(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    telemetry_rows, panel_rows, summary = run_source_only_role_metric_panel(
        checkpoint_path,
        horizon_steps=2,
        use_parameterized_role_fixtures=True,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_parameterized_source_only_role_metric_panel_pass"
    )
    assert summary["parameterized_role_fixtures"] is True
    assert summary["all_rows_use_parameterized_fixtures"] is True
    assert summary["unique_role_reset_observation_digest_count"] == 3
    assert summary["role_reset_observation_digests_differentiated"] is True
    assert summary["checkpoint_admitted"] is True
    assert summary["step_count"] == 6
    assert summary["role_metric_panel_row_count"] == 3
    assert summary["role_panel_covers_expected_roles"] is True
    assert summary["success_rate_computed"] is False
    assert summary["verdict_claim_made"] is False
    assert len(telemetry_rows) == 6
    assert {row.role_family for row in telemetry_rows} == set(ROLE_FAMILIES)
    assert {row.role_family for row in panel_rows} == set(ROLE_FAMILIES)
    assert all(row.parameterized_fixture for row in telemetry_rows)
    assert len({row.reset_observation_digest for row in telemetry_rows}) == 3
    assert all(row.backend_alive_fraction == 1.0 for row in panel_rows)
    assert all(row.bounded_action_fraction == 1.0 for row in panel_rows)


def test_run_preflight_writes_summary_telemetry_and_panel(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    summary = run_preflight(
        tmp_path / "run",
        checkpoint_path=checkpoint_path,
        horizon_steps=1,
        next_blocker="m2494-engineering-controller-source-only-role-metric-panel-result-audit",
    )

    assert summary["status_pass"] is True
    assert summary["milestone"] == "m2493-engineering-controller-source-only-role-metric-panel"
    assert summary["step_count"] == 3
    assert summary["telemetry_rows"] == str(tmp_path / "run" / "telemetry_rows.csv")
    assert summary["role_metric_panel"] == str(tmp_path / "run" / "role_metric_panel.csv")

    with (tmp_path / "run" / "telemetry_rows.csv").open(newline="", encoding="utf-8") as handle:
        telemetry_rows = list(csv.DictReader(handle))
    with (tmp_path / "run" / "role_metric_panel.csv").open(newline="", encoding="utf-8") as handle:
        panel_rows = list(csv.DictReader(handle))

    assert len(telemetry_rows) == 3
    assert len(panel_rows) == 3
    assert set(telemetry_rows[0]) == set(TELEMETRY_FIELDNAMES)
    assert set(panel_rows[0]) == set(PANEL_FIELDNAMES)
    assert {row["observation_shape"] for row in telemetry_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in telemetry_rows} == {str(ACTION_DIM)}
    assert {row["policy_action"] for row in telemetry_rows} == {"True"}
    assert {row["parameterized_fixture"] for row in telemetry_rows} == {"False"}
    assert {row["diagnostic_only"] for row in panel_rows} == {"True"}
    assert {row["success_rate_computed"] for row in panel_rows} == {"False"}
    assert {row["verdict_claim_made"] for row in panel_rows} == {"False"}


def test_run_preflight_writes_parameterized_fixture_panel(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    _write_checkpoint(checkpoint_path)

    summary = run_preflight(
        tmp_path / "run",
        checkpoint_path=checkpoint_path,
        horizon_steps=1,
        next_blocker="m2499-parameterized-source-only-role-metric-panel-result-audit",
        use_parameterized_role_fixtures=True,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_parameterized_source_only_role_metric_panel_pass"
    )
    assert summary["parameterized_role_fixtures"] is True
    assert summary["unique_role_reset_observation_digest_count"] == 3
    assert summary["role_reset_observation_digests_differentiated"] is True

    with (tmp_path / "run" / "telemetry_rows.csv").open(newline="", encoding="utf-8") as handle:
        telemetry_rows = list(csv.DictReader(handle))
    with (tmp_path / "run" / "role_metric_panel.csv").open(newline="", encoding="utf-8") as handle:
        panel_rows = list(csv.DictReader(handle))

    assert len(telemetry_rows) == 3
    assert len(panel_rows) == 3
    assert set(telemetry_rows[0]) == set(TELEMETRY_FIELDNAMES)
    assert {row["parameterized_fixture"] for row in telemetry_rows} == {"True"}
    assert len({row["reset_observation_digest"] for row in telemetry_rows}) == 3
    assert {row["diagnostic_only"] for row in panel_rows} == {"True"}
    assert {row["success_rate_computed"] for row in panel_rows} == {"False"}
