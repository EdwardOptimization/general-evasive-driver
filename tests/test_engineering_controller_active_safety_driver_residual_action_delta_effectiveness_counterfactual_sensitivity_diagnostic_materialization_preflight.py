import autodrift.engineering_controller_active_safety_driver_residual_action_delta_effectiveness_counterfactual_sensitivity_diagnostic_materialization_preflight as m3150


def _base_coverage(**updates):
    row = {
        "residual_failure_id": "m3147-residual-failure-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "fresh_panel_row_id": "m3082-fresh-panel-0007",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "target_failure_kind": "collision",
        "terminal_termination_reason": "obstacle_collision",
        "trace_step_count": "12",
        "candidate_saturation_fraction": "0.0",
        "fallback_saturation_fraction": "0.0",
    }
    row.update(updates)
    return row


def _step(step_index: int, **updates):
    row = {
        "step_index": str(step_index),
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "fallback_steer": "0.1",
        "fallback_throttle": "0.2",
        "fallback_brake": "-0.2",
        "candidate_steer": "0.1",
        "candidate_throttle": "0.19",
        "candidate_brake": "-0.18",
        "delta_steer": "0.0",
        "delta_throttle": "-0.01",
        "delta_brake": "0.02",
        "delta_max_abs": "0.02",
        "candidate_action_saturated": "False",
        "min_clearance_margin_m_after_step": "0.1",
        "speed_mps_after_step": "16.0",
        "beta_after_step": "0.1",
    }
    row.update(updates)
    return row


def test_effectiveness_row_labels_collision_terminal_delta_low_with_headroom():
    coverage = _base_coverage()
    steps = [_step(index) for index in range(1, 13)]

    row = m3150.effectiveness_row_from_trace(1, coverage, steps)

    assert row["terminal_window_step_count"] == 10
    assert row["terminal_window_start_step"] == 3
    assert row["terminal_window_end_step"] == 12
    assert row["candidate_brake_headroom_to_max_mean"] > 1.0
    assert row["candidate_throttle_drop_headroom_mean"] > 1.0
    assert row["counterfactual_sensitivity_label"] == "collision_terminal_delta_low_headroom_available"
    assert row["environment_reset_run"] is False
    assert row["validation_run"] is False
    assert row["repair_success_claim_made"] is False
    assert row["claim_boundary"] == m3150.CLAIM_SCOPE


def test_effectiveness_row_labels_collision_saturation_before_low_delta():
    coverage = _base_coverage(candidate_saturation_fraction="0.36")
    steps = [_step(index, candidate_brake="1.0", candidate_action_saturated="True") for index in range(1, 13)]

    row = m3150.effectiveness_row_from_trace(1, coverage, steps)

    assert row["counterfactual_sensitivity_label"] == "collision_action_saturation_limited"
    assert row["terminal_window_candidate_saturation_fraction"] == 1.0


def test_residual_delta_effectiveness_rows_preserve_source_identity():
    source = {
        "m3147_coverage_rows": [
            _base_coverage(source_measurement_episode_id="m3084-measurement-episode-0007"),
            _base_coverage(
                residual_failure_id="m3147-residual-failure-0002",
                source_measurement_episode_id="m3084-measurement-episode-0013",
                target_failure_kind="offtrack",
                terminal_termination_reason="off_track",
            ),
        ],
        "m3147_step_rows": [
            _step(1, source_measurement_episode_id="m3084-measurement-episode-0007"),
            _step(2, source_measurement_episode_id="m3084-measurement-episode-0007"),
            _step(
                1,
                source_measurement_episode_id="m3084-measurement-episode-0013",
                delta_steer="0.01",
                candidate_steer="0.1",
            ),
        ],
    }

    rows = m3150.residual_delta_effectiveness_rows(source)

    assert [row["source_measurement_episode_id"] for row in rows] == [
        "m3084-measurement-episode-0007",
        "m3084-measurement-episode-0013",
    ]
    assert rows[0]["effectiveness_row_id"] == "m3150-residual-delta-effectiveness-0001"
    assert rows[1]["target_failure_kind"] == "offtrack"


def test_claim_boundary_blocks_execution_validation_and_feasibility_proof():
    rows = m3150.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3150-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3150-new_environment_execution"]["allowed_in_m3150"] is False
    assert by_id["m3150-validation_result"]["claim_made"] is False
    assert by_id["m3150-repair_success"]["claim_made"] is False
    assert by_id["m3150-feasibility_proof"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3150.build_follow_up_manifest(output_dir=tmp_path / "m3150", doc_path=tmp_path / "m3150.md")

    assert manifest["id"] == m3150.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_action_delta_sensitivity_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
