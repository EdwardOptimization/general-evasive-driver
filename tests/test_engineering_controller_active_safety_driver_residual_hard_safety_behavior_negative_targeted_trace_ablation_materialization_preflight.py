import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_behavior_negative_targeted_trace_ablation_materialization_preflight as m3177


def _source():
    exists = {
        "m3176_audit": True,
        "m3175_summary": True,
        "m3175_regression_rows": True,
        "m3175_repair_decomposition_rows": True,
        "m3175_gate_rows": True,
        "m3172_summary": True,
        "m3172_measurement_rows": True,
        "m3170_summary": True,
        "m3170_policy_config": True,
        "m3170_gate_rows": True,
        "m3105_summary": True,
        "m3105_measurement_rows": True,
        "m3012_summary": True,
        "m3012_executable_specs": True,
        "m3012_workload_rows": True,
    }
    return {
        "source_exists": exists,
        "m3176_audit_text": "M3176 selects M3177 targeted actor-visible trace-ablation materialization.",
        "m3175_summary": {"status_pass": True},
        "m3175_regression_rows": [
            {
                "regression_row_id": "m3175-regression-row-0001",
                "measurement_episode_id": "m3172-measurement-episode-0020",
                "baseline_episode_id": "m3105-measurement-episode-0020",
                "source_measurement_episode_id": "m3084-measurement-episode-0020",
                "fresh_panel_row_id": "m3082-fresh-panel-0020",
                "axis_id": "offtrack_boundary_recovery",
                "binding_role": "parent",
                "task_family": "T5",
                "eval_seed": "401611",
                "regression_family": "new_collision_regression_vs_m3105",
                "m3172_collision": "True",
                "m3105_collision": "False",
            }
        ],
        "m3175_repair_decomposition_rows": [
            {"route_name": "new_collision_regression_actor_visible_ablation_trace"}
        ],
        "m3175_gate_rows": [{"status_pass": True}],
        "m3172_summary": {"status_pass": True},
        "m3172_measurement_rows": [
            {
                "runtime_smoke_episode_id": "m3172-measurement-episode-0020",
                "source_measurement_episode_id": "m3084-measurement-episode-0020",
                "executable_workload_id": "m3012-executable-workload-0008",
                "executable_source_spec_id": "m3012-executable-source-spec-0004",
                "task_source_id": "m3006-src-0003",
                "collision": "True",
                "steps": "79",
            }
        ],
        "m3170_summary": {"status_pass": True},
        "m3170_policy_config": {},
        "m3170_gate_rows": [{"status_pass": True}],
        "m3105_summary": {"status_pass": True},
        "m3105_measurement_rows": [
            {
                "runtime_smoke_episode_id": "m3105-measurement-episode-0020",
                "source_measurement_episode_id": "m3084-measurement-episode-0020",
                "executable_workload_id": "m3012-executable-workload-0008",
                "executable_source_spec_id": "m3012-executable-source-spec-0004",
                "task_source_id": "m3006-src-0003",
                "success": "True",
                "collision": "False",
                "steps": "104",
            }
        ],
        "m3012_summary": {"status_pass": True},
        "m3012_executable_specs": [
            {
                "executable_source_spec_id": "m3012-executable-source-spec-0004",
                "task_source_id": "m3006-src-0003",
                "env_config": {"history_length": 1},
            }
        ],
        "m3012_workload_rows": [
            {
                "executable_workload_id": "m3012-executable-workload-0008",
                "config_path": "",
            }
        ],
    }


def _active_observation():
    obs = np.zeros(m3177.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.7
    obs[12:28].reshape(8, 2)[:, 1] = 0.3
    obs[28:44].reshape(8, 2)[:, 1] = -0.3
    obs[44] = 1.0
    obs[45] = 0.1
    obs[46] = 0.0
    return obs


def _variant_row(variant_id, *, success, collision, steps, overlay=0.2):
    return {
        "variant_id": variant_id,
        "success": success,
        "collision": collision,
        "steps": steps,
        "min_clearance_margin": "0.1",
        "return": "1.0",
        "action_rate_mean": "0.01",
        "high_sideslip_fraction": "0.0",
        "overlay_activation_fraction": overlay,
        "outcome_bucket": "success_obstacle_pass" if success else "collision_failure",
        "runtime_base_policy_required": False,
        "validation_run": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
    }


def test_target_regression_rows_selects_single_new_collision():
    rows = m3177.target_regression_rows(_source())

    assert len(rows) == 1
    assert rows[0]["source_measurement_episode_id"] == "m3084-measurement-episode-0020"
    assert rows[0]["fresh_panel_row_id"] == "m3082-fresh-panel-0020"


def test_action_bundle_ablation_variants_zero_only_named_channel():
    obs = _active_observation()
    base = m3177.action_bundle(obs, "m3177_candidate_m3170")
    incumbent = base["incumbent"]
    candidate = base["candidate"]
    delta = candidate - incumbent

    assert np.linalg.norm(delta) > 0.1
    no_steer = m3177.action_bundle(obs, "m3177_ablate_steer_delta")["variant"]
    no_throttle = m3177.action_bundle(obs, "m3177_ablate_throttle_drop")["variant"]
    no_brake = m3177.action_bundle(obs, "m3177_ablate_brake_add")["variant"]

    assert np.isclose(no_steer[0], incumbent[0])
    assert np.isclose(no_steer[1], candidate[1])
    assert np.isclose(no_steer[2], candidate[2])
    assert np.isclose(no_throttle[0], candidate[0])
    assert np.isclose(no_throttle[1], incumbent[1])
    assert np.isclose(no_throttle[2], candidate[2])
    assert np.isclose(no_brake[0], candidate[0])
    assert np.isclose(no_brake[1], candidate[1])
    assert np.isclose(no_brake[2], incumbent[2])


def test_gate_matrix_accepts_complete_targeted_trace_pack():
    source = _source()
    targets = m3177.target_regression_rows(source)
    plan = {
        "status_pass": True,
        "target": targets[0],
        "m3172_row": {"collision": "True", "steps": "79"},
        "m3105_row": {"success": "True", "collision": "False", "steps": "104"},
    }
    traces = [
        {
            "variant_id": spec["variant_id"],
            "action_finite": True,
            "action_bounded": True,
            "runtime_label_inputs_used": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "validation_run": False,
            "repair_success_claim_made": False,
        }
        for spec in m3177.variant_specs()
    ]
    variants = [
        _variant_row("m3177_incumbent_m3105", success=True, collision=False, steps=104, overlay=0.0),
        _variant_row("m3177_candidate_m3170", success=False, collision=True, steps=79, overlay=0.4),
        _variant_row("m3177_ablate_steer_delta", success=False, collision=True, steps=82),
        _variant_row("m3177_ablate_throttle_drop", success=False, collision=True, steps=85),
        _variant_row("m3177_ablate_brake_add", success=True, collision=False, steps=104),
    ]
    guards = m3177.contract_guard_rows(source=source, plan=plan, targets=targets, traces=traces, variants=variants)
    claims = m3177.claim_boundary_rows(follow_up_manifest_registered=True)
    gates = m3177.gate_matrix_rows(
        source=source,
        targets=targets,
        plan=plan,
        traces=traces,
        variants=variants,
        guards=guards,
        claims=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )

    assert all(row["status_pass"] for row in guards)
    assert all(row["status_pass"] for row in claims)
    assert all(row["status_pass"] for row in gates)


def test_follow_up_manifest_is_result_audit(tmp_path):
    manifest = m3177.build_follow_up_manifest(output_dir=tmp_path / "m3177", doc_path=tmp_path / "m3177.md")

    assert manifest["id"] == m3177.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_behavior_negative_source_repair_decomposition"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_behavior_negative_targeted_trace_ablation_result_audit_doc",
            "command": "true",
        }
    ]
