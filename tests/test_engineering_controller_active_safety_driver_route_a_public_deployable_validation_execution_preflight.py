import numpy as np

import autodrift.engineering_controller_active_safety_driver_route_a_public_deployable_validation_execution_preflight as m3161


def test_with_scope_marks_public_validation_execution_without_verdict():
    rows = [
        {
            "runtime_smoke_episode_id": "m3161-validation-episode-0001",
            "policy": "active_safety_reflex_driver_v1_runtime_smoke",
            "success": True,
            "validation_run": False,
            "validation_result_claim_made": True,
            "driver_performance_claim_made": True,
            "claim_boundary": "old",
        }
    ]

    scoped = m3161._with_scope(rows)

    assert scoped[0]["policy"] == "active_safety_reflex_driver_route_a_public_deployable_validation_execution"
    assert scoped[0]["runtime_driver_id"] == m3161.DRIVER_ID
    assert scoped[0]["candidate_output_semantics"] == m3161.OUTPUT_SEMANTICS
    assert scoped[0]["validation_run"] is True
    assert scoped[0]["validation_result_claim_made"] is False
    assert scoped[0]["driver_performance_claim_made"] is False
    assert scoped[0]["repair_success_claim_made"] is False
    assert scoped[0]["claim_boundary"] == m3161.CLAIM_SCOPE


def test_same_case_comparison_rows_record_m3105_alignment_without_claims():
    episode = {
        "runtime_smoke_episode_id": "m3161-validation-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "fresh_panel_row_id": "fresh-1",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "123",
        "success": False,
        "collision": True,
        "termination_reason": "obstacle_collision",
        "outcome_bucket": "collision_failure",
        "min_clearance_margin": "-0.2",
        "return": "-1.0",
        "speed_mean": "12.0",
        "action_rate_mean": "0.2",
    }
    incumbent = {
        "runtime_smoke_episode_id": "m3105-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "eval_seed": "123",
        "success": False,
        "collision": True,
        "termination_reason": "obstacle_collision",
        "outcome_bucket": "collision_failure",
        "min_clearance_margin": "-0.3",
        "return": "-2.0",
        "speed_mean": "11.5",
        "action_rate_mean": "0.25",
    }

    rows = m3161.same_case_comparison_rows([episode], [incumbent])

    assert rows[0]["comparison_id"] == "m3161-same-case-comparison-0001"
    assert rows[0]["candidate_id"] == m3161.DRIVER_ID
    assert rows[0]["baseline_id"] == "m3105_incumbent_direct_action_measurement"
    assert rows[0]["success_match"] is True
    assert rows[0]["collision_match"] is True
    assert rows[0]["termination_reason_match"] is True
    assert rows[0]["exact_seed_match"] is True
    assert rows[0]["success_delta"] == 0
    assert rows[0]["collision_delta"] == 0
    assert np.isclose(rows[0]["clearance_delta"], 0.1)
    assert rows[0]["validation_execution_run"] is True
    assert rows[0]["validation_result_claim_made"] is False
    assert rows[0]["driver_performance_claim_made"] is False


def test_known_failure_validation_rows_preserve_blocker_disclosure():
    episode = {
        "runtime_smoke_episode_id": "m3161-validation-episode-0007",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "success": False,
        "collision": True,
        "termination_reason": "obstacle_collision",
    }
    incumbent = {
        "runtime_smoke_episode_id": "m3105-measurement-episode-0007",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "success": False,
        "collision": True,
        "termination_reason": "obstacle_collision",
    }
    known = {
        "failure_taxonomy_row_id": "m3156-known-failure-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "fresh_panel_row_id": "fresh-7",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": "401530",
        "blocker_family": "collision",
    }

    rows = m3161.known_failure_validation_rows([episode], [incumbent], [known])

    assert rows[0]["source_blocker_id"] == "m3156-known-failure-0001"
    assert rows[0]["source_blocker_family"] == "collision"
    assert rows[0]["candidate_blocker_family"] == "collision"
    assert rows[0]["baseline_blocker_family"] == "collision"
    assert rows[0]["blocker_family_match"] is True
    assert rows[0]["blocker_preserved"] is True
    assert rows[0]["blocker_resolved"] is False
    assert rows[0]["validation_result_claim_made"] is False
    assert rows[0]["repair_success_claim_made"] is False


def test_follow_up_manifest_is_result_audit_and_preserves_claim_boundary(tmp_path):
    manifest = m3161.build_follow_up_manifest(
        output_dir=tmp_path / "m3161",
        doc_path=tmp_path / "m3161.md",
    )

    assert manifest["id"] == m3161.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert "validation execution rows" in manifest["forbidden_shortcuts"][1]
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_route_a_public_deployable_validation_execution_result_audit_doc",
            "command": "true",
        }
    ]


def test_runtime_contract_probes_use_obs72_action3_public_api():
    rows = m3161.runtime_contract_probe_rows()

    assert len(rows) >= 5
    assert all(row["observation_shape"] == m3161.P0_OBSERVATION_DIM for row in rows)
    assert all(row["action_shape"] == m3161.ACTION_DIM for row in rows)
    assert all(row["action_components"] == "steer|throttle|brake" for row in rows)
    assert all(row["finite"] is True for row in rows)
    assert all(row["bounded"] is True for row in rows)
    assert all(row["runtime_base_policy_required"] is False for row in rows)
    assert all(row["validation_execution_run"] is True for row in rows)
    assert all(row["validation_result_claim_made"] is False for row in rows)
