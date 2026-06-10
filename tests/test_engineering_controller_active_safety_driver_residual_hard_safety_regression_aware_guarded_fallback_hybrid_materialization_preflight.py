from pathlib import Path

import numpy as np
import pytest

from autodrift.artifacts import write_csv_rows, write_json
import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_preflight as m3135


def _source_tree(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    audit = tmp_path / "m3134.md"
    audit.write_text(
        "accept_m3133_regression_decomposition_reject_standalone_corridor_route_to_m3135_guarded_fallback_hybrid_materialization\n",
        encoding="utf-8",
    )
    m3133_dir = tmp_path / "m3133"
    m3133_dir.mkdir()
    write_json(
        m3133_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "regression_decomposition_row_count": m3135.EXPECTED_FULL_ROWS,
            "success_delta_sum_vs_m3105": -22,
        },
    )
    write_csv_rows(
        m3133_dir / "regression_failure_decomposition_rows.csv",
        [{"source_measurement_episode_id": f"src-{idx:04d}"} for idx in range(m3135.EXPECTED_FULL_ROWS)],
    )
    write_csv_rows(m3133_dir / "gate_matrix.csv", [{"gate_id": "m3133-gate", "status_pass": True}])

    m3105_dir = tmp_path / "m3105"
    m3105_dir.mkdir()
    write_json(m3105_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m3105_dir / "gate_matrix.csv", [{"gate_id": "m3105-gate", "status_pass": True}])

    m3129_dir = tmp_path / "m3129"
    m3129_dir.mkdir()
    write_json(m3129_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_json(m3129_dir / "direct_action_policy_config.json", m3135.CORRIDOR_POLICY_CONFIG)
    write_csv_rows(m3129_dir / "gate_matrix.csv", [{"gate_id": "m3129-gate", "status_pass": True}])
    return audit, m3133_dir, m3105_dir, m3129_dir


def test_action_contract_rejects_wrong_shape_and_nonfinite_values():
    with pytest.raises(ValueError, match="expected observation shape"):
        m3135.regression_aware_guarded_fallback_hybrid_action(np.zeros(71, dtype=np.float32))

    obs = np.zeros(m3135.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        m3135.regression_aware_guarded_fallback_hybrid_action(obs)


def test_low_speed_edge_and_stability_guards_select_fallback_path():
    probes = [
        m3135._probe_observation(speed_mps=3.0),
        m3135._probe_observation(speed_mps=14.0, edge_urgency=True),
        m3135._probe_observation(speed_mps=14.0, sideslip=True),
    ]

    for obs in probes:
        diag = m3135.guarded_hybrid_diagnostics(obs)
        assert diag["corridor_mix_alpha"] == 0.0
        assert diag["fallback_path_selected"] is True
        assert np.allclose(diag["action"], diag["fallback_action"])
        assert np.max(np.abs(diag["action"])) <= 1.0


def test_urgent_obstacle_allows_small_bounded_corridor_mix():
    obs = m3135._probe_observation(speed_mps=15.0, obstacle=True, obstacle_y_m=1.0)
    diag = m3135.guarded_hybrid_diagnostics(obs)
    action = m3135.regression_aware_guarded_fallback_hybrid_action(obs)

    assert diag["corridor_mix_alpha"] > 0.0
    assert diag["fallback_path_selected"] is False
    assert np.allclose(action, diag["action"])
    assert not np.allclose(diag["action"], diag["fallback_action"])
    assert np.max(np.abs(diag["action"])) <= 1.0
    delta = diag["action"] - diag["fallback_action"]
    assert abs(float(delta[0])) <= m3135.POLICY_CONFIG["guard_thresholds"]["max_abs_steer_delta"] + 1e-6
    assert float(delta[1]) >= -m3135.POLICY_CONFIG["guard_thresholds"]["max_throttle_drop"] - 1e-6
    assert float(delta[2]) <= m3135.POLICY_CONFIG["guard_thresholds"]["max_brake_increase"] + 1e-6


def test_action_probe_rows_capture_fallback_and_bounded_mix_cases():
    rows = {row["probe_family"]: row for row in m3135.build_action_probe_rows()}

    assert rows["low_speed_floor"]["fallback_path_selected"] is True
    assert rows["urgent_edge"]["fallback_path_selected"] is True
    assert rows["sideslip_recovery"]["fallback_path_selected"] is True
    assert rows["urgent_obstacle_left"]["corridor_mix_alpha"] > 0.0
    assert all(row["action_finite"] for row in rows.values())
    assert all(row["action_bounded"] for row in rows.values())


def test_claim_boundary_blocks_measurement_and_repair_success():
    rows = m3135.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3135-follow_up_result_audit_registered"]["allowed_in_m3135"] is True
    assert by_id["m3135-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3135-measurement_result"]["allowed_in_m3135"] is False
    assert by_id["m3135-repair_success"]["claim_made"] is False
    assert by_id["m3135-feasibility_proof"]["claim_made"] is False
    assert by_id["m3135-row_label_actor_inputs"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_measurement(tmp_path):
    manifest = m3135.build_follow_up_manifest(
        output_dir=tmp_path / "m3135",
        doc_path=tmp_path / "m3135.md",
    )

    assert manifest["id"] == m3135.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_guarded_fallback_hybrid_materialization_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]


def test_run_materialization_writes_complete_artifacts_and_m3136_manifest(tmp_path):
    audit, m3133_dir, m3105_dir, m3129_dir = _source_tree(tmp_path)
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "docs" / "m3135.md"
    follow_up = tmp_path / "manifests" / "m3136.json"

    summary = m3135.run_materialization(
        m3134_audit=audit,
        m3133_dir=m3133_dir,
        m3105_dir=m3105_dir,
        m3129_dir=m3129_dir,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["runtime_base_policy_required"] is False
    assert summary["environment_step_run"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["selected_next_action"] == m3135.NEXT_ID
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "guarded_hybrid_rule_rows.csv").exists()
    assert (output_dir / "runtime_contract_rows.csv").exists()
    assert (output_dir / "actor_input_exclusion_rows.csv").exists()
    assert (output_dir / "action_probe_rows.csv").exists()
    assert (output_dir / "claim_boundary_rows.csv").exists()
    assert (output_dir / "gate_matrix.csv").exists()
    assert doc_path.exists()
    assert follow_up.exists()
