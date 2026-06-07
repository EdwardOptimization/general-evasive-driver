from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
import autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_fresh_robustness_panel_materialization_preflight as m3082
import autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight as m3078


def _m3080_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(32):
        role = "candidate" if index % 2 == 0 else "parent"
        rows.append(
            {
                "measurement_episode_id": f"m3080-measurement-episode-{index + 1:04d}",
                "eval_seed": 301500 + index,
                "binding_role": role,
                "base_profile_name": f"route_a_{role}",
                "outcome_bucket": "speed_too_low_noncollision_noncompletion" if index < 7 else "success_obstacle_pass",
            }
        )
    return rows


def _write_sources(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    m3081_audit = tmp_path / "m3081.md"
    m3080_dir = tmp_path / "m3080"
    m3078_dir = tmp_path / "m3078"
    m3039_dir = tmp_path / "m3039"
    m3012_dir = tmp_path / "m3012"
    for directory in (m3080_dir, m3078_dir, m3039_dir, m3012_dir):
        directory.mkdir()
    m3081_audit.write_text("# M3081\n", encoding="utf-8")
    write_json(
        m3080_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "measurement_success_count": 19,
            "measurement_collision_count": 3,
            "measurement_offtrack_count": 3,
            "measurement_speed_too_low_count": 7,
            "measurement_clearance_margin_mean": 11.2,
        },
    )
    write_csv_rows(m3080_dir / "measurement_episode_rows.csv", _m3080_rows())
    write_json(
        m3078_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "actor_contract_shape_72_action_3": True,
            "runtime_base_policy_required": False,
        },
    )
    write_json(m3078_dir / "direct_action_policy_config.json", m3078.DEFAULT_POLICY_CONFIG)
    write_json(m3039_dir / "summary.json", {"status_pass": True})
    write_json(m3012_dir / "summary.json", {"status_pass": True})
    return m3081_audit, m3080_dir, m3078_dir, m3039_dir, m3012_dir


def test_build_fresh_panel_rows_are_fresh_and_cover_axes() -> None:
    panel_rows = m3082.build_fresh_panel_rows(_m3080_rows())

    assert len(panel_rows) == 64
    assert len({row["eval_seed"] for row in panel_rows}) == 64
    assert {row["axis_id"] for row in panel_rows} == {
        "collision_lateral_intrusion",
        "offtrack_boundary_recovery",
        "speed_floor_stress",
        "stability_action_pressure",
    }
    assert {row["binding_role"] for row in panel_rows} == {"candidate", "parent"}
    assert all(row["fresh_seed"] is True for row in panel_rows)
    assert all(row["source_denominator_reused"] is False for row in panel_rows)
    assert all(row["execution_allowed_in_m3082"] is False for row in panel_rows)
    assert all(row["runtime_base_policy_required"] is False for row in panel_rows)
    assert all(row["actor_observation_dim"] == 72 for row in panel_rows)
    assert all(row["actor_action_dim"] == 3 for row in panel_rows)


def test_materialize_fresh_robustness_panel_preserves_claim_boundary(tmp_path: Path) -> None:
    m3081_audit, m3080_dir, m3078_dir, m3039_dir, m3012_dir = _write_sources(tmp_path)
    output_dir = tmp_path / "m3082"
    doc_path = tmp_path / "m3082.md"
    follow_up_manifest = tmp_path / "m3083.json"

    summary = m3082.materialize(
        m3081_audit=m3081_audit,
        m3080_dir=m3080_dir,
        m3078_dir=m3078_dir,
        m3039_dir=m3039_dir,
        m3012_dir=m3012_dir,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["fresh_robustness_panel_row_count"] == 64
    assert summary["fresh_seed_unique_count"] == 64
    assert summary["m3080_seed_overlap_count"] == 0
    assert summary["robustness_axis_count"] == 4
    assert summary["binding_role_count"] == 2
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["validation_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    panel_rows = read_csv_rows(output_dir / "fresh_robustness_panel_rows.csv")
    assert len(panel_rows) == 64
    assert {row["fixed_denominator_row_reused"] for row in panel_rows} == {"False"}
    assert {row["hidden_oracle_actor_input_required"] for row in panel_rows} == {"False"}
    assert {row["ttc_actor_input_required"] for row in panel_rows} == {"False"}

    admission_rows = read_csv_rows(output_dir / "robustness_admission_guard_rows.csv")
    assert all(row["status_pass"] == "True" for row in admission_rows)
    assert any(row["guard_family"] == "speed_floor" for row in admission_rows)

    actor_rows = read_csv_rows(output_dir / "actor_contract_guard_rows.csv")
    assert all(row["status_pass"] == "True" for row in actor_rows)

    claim_rows = read_csv_rows(output_dir / "claim_boundary_rows.csv")
    forbidden_rows = [row for row in claim_rows if row["allowed_in_m3082"] == "False"]
    assert forbidden_rows
    assert all(row["claim_made"] == "False" for row in forbidden_rows)

    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"] == m3082.NEXT_ID
    assert follow_up["status"] == "pending"
    assert follow_up["gate_tier"] == "process"
    assert doc_path.exists()
