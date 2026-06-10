from pathlib import Path

import numpy as np
import pytest

from autodrift.artifacts import write_csv_rows, write_json
import autodrift.engineering_controller_active_safety_driver_residual_hard_safety_trajectory_level_clearance_stability_corridor_reflex_materialization_preflight as m3129


def _source_tree(tmp_path: Path) -> tuple[Path, Path]:
    audit = tmp_path / "m3128.md"
    audit.write_text(
        "accept_m3127_architecture_diagnostics_route_to_m3129_trajectory_level_clearance_stability_corridor_reflex_materialization\n",
        encoding="utf-8",
    )
    m3127_dir = tmp_path / "m3127"
    m3127_dir.mkdir()
    write_json(
        m3127_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "architecture_candidate_row_count": m3129.EXPECTED_ARCHITECTURE_ROWS,
        },
    )
    write_csv_rows(
        m3127_dir / "architecture_candidate_rows.csv",
        [{"row_id": f"row-{idx}"} for idx in range(m3129.EXPECTED_ARCHITECTURE_ROWS)],
    )
    write_csv_rows(m3127_dir / "controller_contract_requirement_rows.csv", [{"row_id": "req-1"}])
    write_csv_rows(m3127_dir / "gate_matrix.csv", [{"gate_id": "gate-1", "status_pass": True}])
    return audit, m3127_dir


def test_action_contract_rejects_wrong_shape_and_nonfinite_values():
    with pytest.raises(ValueError, match="expected observation shape"):
        m3129.trajectory_level_clearance_stability_corridor_action(np.zeros(71, dtype=np.float32))

    obs = np.zeros(m3129.P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        m3129.trajectory_level_clearance_stability_corridor_action(obs)


def test_action_output_is_direct_finite_bounded_action3():
    obs = m3129._probe_observation(speed_mps=12.0)
    action = m3129.trajectory_level_clearance_stability_corridor_action(obs)

    assert action.shape == (m3129.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0


def test_obstacle_probe_steers_away_and_brakes():
    obs = m3129._probe_observation(speed_mps=15.0, obstacle=True, obstacle_y_m=1.0)
    steer, throttle, brake = m3129.trajectory_level_clearance_stability_corridor_action(obs)

    assert steer < -0.1
    assert throttle < -0.8
    assert brake > 0.0


def test_low_speed_clear_probe_preserves_speed_floor():
    obs = m3129._probe_observation(speed_mps=3.0)
    steer, throttle, brake = m3129.trajectory_level_clearance_stability_corridor_action(obs)

    assert abs(steer) < 1e-6
    assert throttle > 0.0
    assert brake <= -0.9


def test_edge_probe_exercises_edge_corridor():
    probe_rows = {row["probe_family"]: row for row in m3129.build_action_probe_rows()}
    edge = probe_rows["urgent_edge"]

    assert edge["action_finite"] is True
    assert edge["action_bounded"] is True
    assert abs(edge["steer"]) > 0.1
    assert edge["brake"] > -1.0


def test_actor_input_exclusions_and_claim_boundaries_are_claim_safe():
    exclusions = m3129.build_actor_input_exclusion_rows()
    claims = m3129.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_claim = {row["claim_id"]: row for row in claims}

    assert len(exclusions) >= m3129.MIN_EXCLUSION_ROWS
    assert all(row["forbidden"] is True for row in exclusions)
    assert all(row["materialized_in_actor_input"] is False for row in exclusions)
    assert all(row["status_pass"] is True for row in exclusions)
    assert by_claim["m3129-trajectory_level_corridor_rule_rows"]["claim_made"] is True
    assert by_claim["m3129-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_claim["m3129-measurement_result"]["allowed_in_m3129"] is False
    assert by_claim["m3129-repair_success"]["claim_made"] is False
    assert by_claim["m3129-feasibility_or_infeasibility_proof"]["claim_made"] is False
    assert all(row["status_pass"] for row in claims)


def test_follow_up_manifest_is_process_audit_not_measurement(tmp_path):
    manifest = m3129.build_follow_up_manifest(
        output_dir=tmp_path / "m3129",
        doc_path=tmp_path / "m3129.md",
    )

    assert manifest["id"] == m3129.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_trajectory_level_clearance_stability_corridor_reflex_materialization_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]


def test_run_materialization_writes_complete_artifacts_and_m3130_manifest(tmp_path):
    audit, m3127_dir = _source_tree(tmp_path)
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "docs" / "m3129.md"
    follow_up = tmp_path / "manifests" / "m3130.json"

    summary = m3129.run_materialization(
        m3128_audit=audit,
        m3127_dir=m3127_dir,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["runtime_base_policy_required"] is False
    assert summary["environment_step_run"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["selected_next_action"] == m3129.NEXT_ID
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "trajectory_level_corridor_rule_rows.csv").exists()
    assert (output_dir / "runtime_contract_rows.csv").exists()
    assert (output_dir / "actor_input_exclusion_rows.csv").exists()
    assert (output_dir / "claim_boundary_rows.csv").exists()
    assert (output_dir / "gate_matrix.csv").exists()
    assert doc_path.exists()
    assert follow_up.exists()
