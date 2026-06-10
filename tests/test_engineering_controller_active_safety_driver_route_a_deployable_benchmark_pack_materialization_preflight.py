import numpy as np

import autodrift.engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_materialization_preflight as m3156
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _source():
    return {
        "m3139_contract": {
            "driver_id": "active_safety_reflex_driver_m3105_incumbent_v4_no_regression",
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
        },
        "m3139_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3105_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "measurement_episode_row_count": 64,
            "measurement_success_count": 57,
            "measurement_collision_count": 5,
            "measurement_offtrack_count": 2,
            "measurement_speed_too_low_count": 0,
            "measurement_clearance_margin_mean": 10.9,
            "measurement_high_sideslip_fraction_mean": 0.05,
            "measurement_lateral_rmse_mean": 1.1,
            "measurement_action_clip_fraction_mean": 0.0,
            "measurement_raw_action_abs_max": 1.0,
        },
        "m3153_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "counterfactual_replay_comparison_row_count": 21,
            "action_channel_sensitive_comparison_count": 0,
        },
        "m3139_residual_blocker_rows": [
            {
                "blocker_id": "m3139-residual-blocker-0001",
                "source_measurement_episode_id": "m3084-measurement-episode-0007",
                "fresh_panel_row_id": "m3082-fresh-panel-0007",
                "axis_id": "collision_lateral_intrusion",
                "binding_role": "candidate",
                "task_family": "T5",
                "eval_seed": "401530",
                "blocker_family": "collision",
                "collision": "True",
                "offtrack": "False",
                "speed_too_low": "False",
                "termination_reason": "obstacle_collision",
                "outcome_bucket": "collision_failure",
                "min_clearance_margin": "-0.1",
                "high_sideslip_fraction": "0.0",
                "lateral_rmse": "0.6",
                "return": "10.0",
                "speed_mean": "17.0",
            },
            {
                "blocker_id": "m3139-residual-blocker-0002",
                "source_measurement_episode_id": "m3084-measurement-episode-0012",
                "fresh_panel_row_id": "m3082-fresh-panel-0012",
                "axis_id": "edge_exit",
                "binding_role": "candidate",
                "task_family": "T5",
                "eval_seed": "401540",
                "blocker_family": "offtrack",
                "collision": "False",
                "offtrack": "True",
                "speed_too_low": "False",
                "termination_reason": "off_track",
                "outcome_bucket": "offtrack_failure",
                "min_clearance_margin": "12.0",
                "high_sideslip_fraction": "0.2",
                "lateral_rmse": "2.0",
                "return": "8.0",
                "speed_mean": "15.0",
            },
        ],
        "m3153_comparison_rows": [
            {
                "source_measurement_episode_id": "m3084-measurement-episode-0007",
                "counterfactual_diagnostic_label": "counterfactual_terminal_outcome_unchanged_diagnostic",
                "action_channel_sensitive_diagnostic": "False",
            },
            {
                "source_measurement_episode_id": "m3084-measurement-episode-0007",
                "counterfactual_diagnostic_label": "counterfactual_terminal_outcome_unchanged_diagnostic",
                "action_channel_sensitive_diagnostic": "False",
            },
            {
                "source_measurement_episode_id": "m3084-measurement-episode-0012",
                "counterfactual_diagnostic_label": "counterfactual_terminal_outcome_unchanged_diagnostic",
                "action_channel_sensitive_diagnostic": "False",
            },
        ],
    }


def test_deployable_contract_snapshot_is_obs72_action3_bounded():
    snapshot = m3156.deployable_driver_contract_snapshot(_source())

    assert snapshot["observation_shape"] == P0_OBSERVATION_DIM
    assert snapshot["action_shape"] == ACTION_DIM
    assert snapshot["sample_action_finite"] is True
    assert snapshot["sample_action_bounded"] is True
    assert np.asarray(snapshot["sample_zero_observation_action"]).shape == (ACTION_DIM,)
    assert snapshot["runtime_base_policy_required"] is False
    assert snapshot["validation_run"] is False


def test_benchmark_metric_rows_include_counts_rates_and_negative_replay():
    rows = m3156.benchmark_metric_rows(_source())
    by_name = {row["metric_name"]: row for row in rows}

    assert by_name["measurement_episode_count"]["value"] == 64
    assert by_name["success_count"]["value"] == 57
    assert by_name["success_rate"]["value"] == 57 / 64
    assert by_name["collision_count"]["value"] == 5
    assert by_name["offtrack_count"]["value"] == 2
    assert by_name["m3153_comparison_count"]["value"] == 21
    assert by_name["m3153_action_channel_sensitive_count"]["value"] == 0
    assert all(row["validation_run"] is False for row in rows)
    assert all(row["driver_performance_claim_made"] is False for row in rows)


def test_known_failure_taxonomy_preserves_blockers_and_terminal_invariance():
    rows = m3156.known_failure_taxonomy_rows(_source())

    assert [row["blocker_family"] for row in rows] == ["collision", "offtrack"]
    assert rows[0]["m3153_comparison_count"] == 2
    assert rows[0]["m3153_action_channel_sensitive_count"] == 0
    assert rows[0]["m3153_terminal_invariant"] is True
    assert rows[0]["m3153_dominant_counterfactual_label"] == "counterfactual_terminal_outcome_unchanged_diagnostic"


def test_claim_boundary_blocks_validation_and_performance_claims():
    rows = m3156.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3156-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3156-new_environment_execution"]["allowed_in_m3156"] is False
    assert by_id["m3156-validation_result"]["claim_made"] is False
    assert by_id["m3156-driver_performance_verdict"]["claim_made"] is False
    assert by_id["m3156-repair_success"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3156.build_follow_up_manifest(output_dir=tmp_path / "m3156", doc_path=tmp_path / "m3156.md")

    assert manifest["id"] == m3156.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_route_a_deployable_benchmark_pack_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
