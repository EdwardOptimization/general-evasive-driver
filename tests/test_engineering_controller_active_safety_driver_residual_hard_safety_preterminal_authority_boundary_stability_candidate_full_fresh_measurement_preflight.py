import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_candidate_full_fresh_measurement_preflight as m3196


def _source(tmp_path):
    cfg = tmp_path / "profile.json"
    cfg.write_text('{"controller_profile": {"name": "parent"}, "env": {"history_length": 1}}', encoding="utf-8")
    rows = []
    for index in range(2):
        rows.append(
            {
                "runtime_smoke_episode_id": f"m3181-measurement-episode-{index + 1:04d}",
                "source_measurement_episode_id": f"m3084-measurement-episode-{index + 1:04d}",
                "fresh_panel_row_id": f"m3082-fresh-panel-{index + 1:04d}",
                "axis_id": "collision_lateral_intrusion",
                "binding_role": "parent",
                "task_family": "T5",
                "executable_workload_id": "workload-1",
                "executable_source_spec_id": "spec-1",
                "task_source_id": "source-1",
                "base_profile_name": "parent",
                "eval_seed": str(401600 + index),
                "candidate_output_semantics": m3196.OUTPUT_SEMANTICS,
                "runtime_base_policy_required": "False",
            }
        )
    return {
        "m3181_measurement_rows": rows,
        "m3012_workload_rows": [
            {
                "executable_workload_id": "workload-1",
                "profile_binding_name": "parent",
                "config_path": str(cfg),
                "status_pass": "True",
            }
        ],
    }


def test_full_fresh_plan_preserves_m3181_denominator_and_contract(tmp_path):
    plan = m3196.full_fresh_plan(_source(tmp_path))

    assert len(plan) == 2
    assert plan[0]["runtime_smoke_episode_id"] == "m3196-measurement-episode-0001"
    assert plan[0]["source_measurement_episode_id"] == "m3084-measurement-episode-0001"
    assert plan[0]["status_pass"] is True
    assert plan[0]["base_profile_name"] == "parent"


def test_same_row_comparison_rows_compute_baseline_deltas():
    episodes = [
        {
            "runtime_smoke_episode_id": "m3196-measurement-episode-0001",
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
    baseline = [
        {
            "runtime_smoke_episode_id": "baseline-measurement-episode-0001",
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
    rows = m3196.same_row_comparison_rows(episodes, m3105_rows=baseline, m3181_rows=baseline)

    assert len(rows) == 2
    assert {row["baseline_id"] for row in rows} == {"m3105", "m3181"}
    row = rows[0]
    assert row["success_delta"] == 1
    assert row["collision_delta"] == -1
    assert row["clearance_margin_delta"] == 0.6
    assert row["exact_seed_match"] is True
    assert row["repair_success_claim_made"] is False


def test_gate_matrix_accepts_complete_measurement_pack():
    source = {
        "source_exists": {
            key: True
            for key in (
                "m3195_audit",
                "m3194_summary",
                "m3194_gate_rows",
                "m3194_runtime_contract_rows",
                "m3181_summary",
                "m3181_measurement_rows",
                "m3105_summary",
                "m3105_measurement_rows",
                "m3012_summary",
                "m3012_executable_specs",
                "m3012_workload_rows",
            )
        },
        "m3195_audit_text": "m3196-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-candidate-full-fresh-measurement-preflight",
        "m3194_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3181_summary": {"status_pass": True},
        "m3105_summary": {"status_pass": True},
    }
    plan_rows = [{} for _ in range(m3196.EXPECTED_FULL_ROWS)]
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
        for _ in range(m3196.EXPECTED_FULL_ROWS)
    ]
    comparisons = []
    for baseline in m3196.BASELINE_IDS:
        comparisons.extend(
            {
                "baseline_id": baseline,
                "exact_seed_match": True,
            }
            for _ in range(m3196.EXPECTED_FULL_ROWS)
        )
    guards = [{"status_pass": True}]
    claims = m3196.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3196.gate_matrix_rows(
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


def test_follow_up_manifest_is_m3197_result_audit(tmp_path):
    manifest = m3196.build_follow_up_manifest(output_dir=tmp_path / "m3196", doc_path=tmp_path / "m3196.md")

    assert manifest["id"] == m3196.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
