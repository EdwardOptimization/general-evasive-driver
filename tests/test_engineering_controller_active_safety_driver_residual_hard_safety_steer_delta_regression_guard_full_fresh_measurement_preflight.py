import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_steer_delta_regression_guard_full_fresh_measurement_preflight as m3181


def _source(tmp_path):
    cfg = tmp_path / "profile.json"
    cfg.write_text('{"controller_profile": {"name": "parent"}, "env": {"history_length": 1}}', encoding="utf-8")
    rows = []
    for index in range(2):
        rows.append(
            {
                "runtime_smoke_episode_id": f"m3172-measurement-episode-{index + 1:04d}",
                "source_measurement_episode_id": f"m3084-measurement-episode-{index + 1:04d}",
                "fresh_panel_row_id": f"m3082-fresh-panel-{index + 1:04d}",
                "axis_id": "offtrack_boundary_recovery",
                "binding_role": "parent",
                "task_family": "T5",
                "executable_workload_id": "workload-1",
                "executable_source_spec_id": "spec-1",
                "task_source_id": "source-1",
                "base_profile_name": "parent",
                "eval_seed": str(401600 + index),
                "candidate_output_semantics": m3181.OUTPUT_SEMANTICS,
                "runtime_base_policy_required": "False",
            }
        )
    return {
        "m3172_measurement_rows": rows,
        "m3012_workload_rows": [
            {
                "executable_workload_id": "workload-1",
                "profile_binding_name": "parent",
                "config_path": str(cfg),
                "status_pass": "True",
            }
        ],
    }


def test_full_fresh_plan_preserves_source_ids_and_contract(tmp_path):
    plan = m3181.full_fresh_plan(_source(tmp_path))

    assert len(plan) == 2
    assert plan[0]["runtime_smoke_episode_id"] == "m3181-measurement-episode-0001"
    assert plan[0]["source_measurement_episode_id"] == "m3084-measurement-episode-0001"
    assert plan[0]["status_pass"] is True
    assert plan[0]["base_profile_name"] == "parent"


def test_same_row_comparison_rows_compute_baseline_deltas():
    episodes = [
        {
            "runtime_smoke_episode_id": "m3181-measurement-episode-0001",
            "source_measurement_episode_id": "src-1",
            "fresh_panel_row_id": "panel-1",
            "axis_id": "axis",
            "binding_role": "parent",
            "task_family": "T5",
            "eval_seed": "10",
            "success": "True",
            "collision": "False",
            "termination_reason": "",
            "min_clearance_margin": "0.5",
            "return": "2.0",
            "speed_mean": "8.0",
        }
    ]
    m3105 = [
        {
            "runtime_smoke_episode_id": "m3105-measurement-episode-0001",
            "source_measurement_episode_id": "src-1",
            "eval_seed": "10",
            "success": "False",
            "collision": "True",
            "termination_reason": "obstacle_collision",
            "min_clearance_margin": "-0.1",
            "return": "1.0",
            "speed_mean": "7.0",
        }
    ]
    rows = m3181.same_row_comparison_rows(episodes, m3105_rows=m3105, m3172_rows=m3105)

    assert len(rows) == 2
    row = rows[0]
    assert row["baseline_id"] == "m3105"
    assert row["success_delta"] == 1
    assert row["collision_delta"] == -1
    assert row["clearance_margin_delta"] == 0.6
    assert row["exact_seed_match"] is True
    assert row["repair_success_claim_made"] is False


def test_gate_matrix_accepts_complete_measurement_pack(tmp_path):
    source = {
        "source_exists": {key: True for key in (
            "m3180_audit",
            "m3179_summary",
            "m3179_gate_rows",
            "m3172_summary",
            "m3172_measurement_rows",
            "m3105_summary",
            "m3105_measurement_rows",
            "m3012_summary",
            "m3012_executable_specs",
            "m3012_workload_rows",
        )},
        "m3180_audit_text": "m3181-engineering-controller-active-safety-driver-residual-hard-safety-steer-delta-regression-guard-full-fresh-measurement-preflight",
        "m3179_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3172_summary": {"status_pass": True},
        "m3105_summary": {"status_pass": True},
    }
    plan_rows = [{} for _ in range(m3181.EXPECTED_FULL_ROWS)]
    episodes = [
        {
            "success": "True",
            "collision": "False",
            "min_clearance_margin": "0.1",
            "return": "1.0",
            "steps": "100",
            "action_rate_mean": "0.1",
            "high_sideslip_fraction": "0.0",
        }
        for _ in range(m3181.EXPECTED_FULL_ROWS)
    ]
    comparisons = []
    for baseline in m3181.BASELINE_IDS:
        comparisons.extend(
            {
                "baseline_id": baseline,
                "exact_seed_match": True,
            }
            for _ in range(m3181.EXPECTED_FULL_ROWS)
        )
    guards = [{"status_pass": True}]
    claims = m3181.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3181.gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        episodes=episodes,
        failures=[],
        comparisons=comparisons,
        guards=guards,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit(tmp_path):
    manifest = m3181.build_follow_up_manifest(output_dir=tmp_path / "m3181", doc_path=tmp_path / "m3181.md")

    assert manifest["id"] == m3181.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_behavior_negative_source_repair_decomposition"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
