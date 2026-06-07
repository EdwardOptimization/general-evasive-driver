from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight as m3086
import autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight as m3078


def _write_sources(tmp_path: Path) -> tuple[Path, Path, Path]:
    m3085_audit = tmp_path / "m3085.md"
    m3084_dir = tmp_path / "m3084"
    m3078_dir = tmp_path / "m3078"
    m3084_dir.mkdir()
    m3078_dir.mkdir()
    m3085_audit.write_text(
        "accept_m3084_measurement_route_to_m3086_deployable_runtime_contract_materialization_preflight\n",
        encoding="utf-8",
    )
    write_json(
        m3084_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "measurement_episode_row_count": 64,
            "measurement_failure_row_count": 0,
            "measurement_success_count": 43,
            "measurement_collision_count": 5,
            "measurement_offtrack_count": 5,
            "measurement_speed_too_low_count": 11,
            "measurement_clearance_margin_mean": 11.3,
            "measurement_action_clip_fraction_mean": 0.0,
        },
    )
    write_csv_rows(m3084_dir / "metric_summary_rows.csv", [{"group": "all", "status_pass": True}])
    write_csv_rows(m3084_dir / "actor_contract_guard_rows.csv", [{"guard_id": "guard", "status_pass": True}])
    write_csv_rows(m3084_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m3084_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    write_json(
        m3078_dir / "summary.json",
        {"status_pass": True, "gate_matrix_pass": True, "runtime_base_policy_required": False},
    )
    write_json(m3078_dir / "direct_action_policy_config.json", m3078.DEFAULT_POLICY_CONFIG)
    write_csv_rows(
        m3078_dir / "actor_input_exclusion_rows.csv",
        [
            {
                "actor_input_family": "hidden_oracle",
                "materialized_in_actor_input": False,
                "status_pass": True,
                "rationale": "hidden state forbidden",
            },
            {
                "actor_input_family": "ttc",
                "materialized_in_actor_input": False,
                "status_pass": True,
                "rationale": "TTC shortcut forbidden",
            },
        ],
    )
    write_csv_rows(m3078_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    return m3085_audit, m3084_dir, m3078_dir


def test_runtime_contract_materialization_writes_deployable_package(tmp_path: Path) -> None:
    m3085_audit, m3084_dir, m3078_dir = _write_sources(tmp_path)
    output_dir = tmp_path / "m3086"
    doc_path = tmp_path / "m3086.md"
    follow_up_manifest = tmp_path / "m3087.json"

    summary = m3086.run_runtime_contract_materialization_preflight(
        m3085_audit=m3085_audit,
        m3084_dir=m3084_dir,
        m3078_dir=m3078_dir,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["observation_shape"] == 72
    assert summary["action_shape"] == 3
    assert summary["action_components"] == ["steer", "throttle", "brake"]
    assert summary["runtime_base_policy_required"] is False
    assert summary["checkpoint_model_required"] is False
    assert summary["driver_action_probe_row_count"] == 5

    contract = read_json(output_dir / "deployable_driver_contract.json")
    assert contract["output_semantics"] == "direct_action_clipped"
    assert contract["runtime_base_policy_required"] is False
    assert contract["action_components"] == ["steer", "throttle", "brake"]

    probe_rows = read_csv_rows(output_dir / "driver_action_probe_rows.csv")
    assert len(probe_rows) == 5
    assert all(row["status_pass"] == "True" for row in probe_rows)
    assert all(row["action_bounded"] == "True" for row in probe_rows)

    claim_rows = read_csv_rows(output_dir / "claim_boundary_rows.csv")
    forbidden_rows = [row for row in claim_rows if row["allowed_in_m3086"] == "False"]
    assert forbidden_rows
    assert all(row["claim_made"] == "False" for row in forbidden_rows)

    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"] == m3086.NEXT_ID
    assert follow_up["status"] == "pending"
    assert doc_path.exists()
