import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_source_localized_repair_admission_materialization_preflight as m3168


def _source():
    rows = []
    for index in range(1, 8):
        family = "collision" if index in {1, 2, 5, 6, 7} else "offtrack"
        rows.append(
            {
                "source_localization_row_id": f"m3166-source-localization-{index:04d}",
                "source_measurement_episode_id": f"m3084-measurement-episode-{index:04d}",
                "blocker_family": family,
                "source_localization_label": (
                    "collision_clearance_unresolved_despite_visible_obstacle_and_action_response"
                    if family == "collision"
                    else "boundary_recovery_unresolved_despite_visible_edge_and_stability_stress"
                ),
            }
        )
    return {
        "source_exists": {
            "m3167_audit": True,
            "m3166_summary": True,
            "m3166_source_localization_rows": True,
            "m3166_repair_admission_rows": True,
            "m3166_gate_rows": True,
        },
        "m3167_audit_text": "accept_m3166_source_localization_route_to_m3168_source_localized_repair_admission_materialization",
        "m3166_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3166_source_localization_rows": rows,
        "m3166_repair_admission_rows": [
            {
                "route_name": "local_action_delta_tuning",
                "required_before_repair": False,
                "admission_decision": "blocked_until_source_localization_changes_repair_hypothesis",
            }
        ],
    }


def test_repair_hypotheses_admit_bounded_implementation_but_not_validation():
    rows = m3168.repair_hypothesis_rows(_source())
    by_name = {row["repair_hypothesis_name"]: row for row in rows}

    assert len(rows) == 2
    assert by_name["collision_clearance_observation_timeline_reflex"]["source_localization_row_count"] == 5
    assert by_name["boundary_recovery_stability_reflex"]["source_localization_row_count"] == 2
    assert all(row["admitted_for_repair_implementation_materialization"] is True for row in rows)
    assert all(row["admitted_for_validation"] is False for row in rows)
    assert all(row["repair_success_claim_made"] is False for row in rows)
    assert all("hidden" in row["forbidden_actor_inputs"] for row in rows)


def test_actor_contract_and_measurement_readiness_rows_are_claim_safe():
    actor_rows = m3168.actor_contract_guard_rows()
    measurement_rows = m3168.measurement_readiness_rows()

    assert actor_rows
    assert measurement_rows
    assert all(row["status_pass"] for row in actor_rows)
    assert all(row["status_pass"] for row in measurement_rows)
    assert any("runtime base policy" in row["forbidden_runtime_surface"] for row in actor_rows)
    assert any(row["required_before"] == "driver_performance_claim" for row in measurement_rows)


def test_gate_matrix_accepts_complete_repair_admission_pack():
    source = _source()
    hypothesis_rows = m3168.repair_hypothesis_rows(source)
    actor_rows = m3168.actor_contract_guard_rows()
    measurement_rows = m3168.measurement_readiness_rows()
    claim_rows = m3168.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3168.gate_matrix_rows(
        source=source,
        hypothesis_rows=hypothesis_rows,
        actor_rows=actor_rows,
        measurement_rows=measurement_rows,
        claim_rows=claim_rows,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert gates
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_audit_not_repair(tmp_path):
    manifest = m3168.build_follow_up_manifest(output_dir=tmp_path / "m3168", doc_path=tmp_path / "m3168.md")

    assert manifest["id"] == m3168.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_hard_safety_source_localized_repair_admission_result_audit_doc",
            "command": "true",
        }
    ]
