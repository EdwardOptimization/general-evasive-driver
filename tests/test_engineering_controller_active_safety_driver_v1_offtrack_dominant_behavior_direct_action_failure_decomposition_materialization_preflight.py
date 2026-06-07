from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_failure_decomposition_materialization_preflight as m3069


def _episode_row(index: int, *, binding: str, task: str, termination: str, success: bool, collision: bool) -> dict[str, object]:
    clip = 0.02 + (0.01 if binding == "candidate" else 0.0)
    raw_action = 1.25 + index * 0.01
    offtrack = termination == "off_track"
    return {
        "measurement_episode_id": f"unit-episode-{index:04d}",
        "baseline_measurement_row_id": f"baseline-{index:04d}",
        "source_episode_index": index,
        "base_profile_name": f"route_a_{binding}",
        "binding_role": binding,
        "task_family": task,
        "window_tag": "unit_window",
        "outcome_bucket": "success" if success else ("collision_failure" if collision else f"{termination}_failure"),
        "termination_reason": termination,
        "success": success,
        "collision": collision,
        "min_clearance_margin": 5.0 + index * 0.1,
        "clearance_margin_delta_vs_baseline": 0.5,
        "return_delta_vs_baseline": -index,
        "high_sideslip_fraction": 0.6 if offtrack else 0.1,
        "lateral_rmse": 1.5 if offtrack else 0.4,
        "action_rate_mean": 0.01,
        "raw_action_abs_max": raw_action,
        "raw_action_l2_mean": raw_action * 0.6,
        "action_clip_fraction": clip,
        "final_action_abs_max": 1.0,
        "baseline_success": False,
        "baseline_collision": False,
        "success_delta_vs_baseline": 1.0 if success else 0.0,
        "collision_delta_vs_baseline": -1.0 if collision else 0.0,
        "recoverability_window_success_available": offtrack,
        "recoverability_window_success": False,
        "off_track_severity_proxy": 0.03 if offtrack else 0.0,
        "max_off_track_overshoot": 0.04 if offtrack else 0.0,
        "time_to_first_off_track_s": 3.0 if offtrack else "",
        "beta_abs_error_mean": 0.2,
        "speed_mean": 3.0,
        "runtime_base_policy_required": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "measurement_only_no_verdict": True,
        "claim_boundary": "unit",
    }


def _source_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(1, 9):
        rows.append(
            _episode_row(
                index,
                binding="candidate" if index % 2 else "parent",
                task="T4" if index <= 4 else "T5",
                termination="",
                success=True,
                collision=False,
            )
        )
    for index in range(9, 12):
        rows.append(_episode_row(index, binding="parent", task="T5", termination="obstacle_collision", success=False, collision=True))
    rows.append(_episode_row(12, binding="candidate", task="T5", termination="off_track", success=False, collision=True))
    for index in range(13, 28):
        rows.append(
            _episode_row(
                index,
                binding="candidate" if index % 2 else "parent",
                task="T4" if index % 3 else "T5",
                termination="off_track",
                success=False,
                collision=False,
            )
        )
    for index in range(28, 33):
        rows.append(
            _episode_row(
                index,
                binding="candidate" if index % 2 else "parent",
                task="T4",
                termination="speed_too_low",
                success=False,
                collision=False,
            )
        )
    return rows


def _write_m3067_source(path: Path) -> None:
    path.mkdir(parents=True)
    write_json(
        path / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "required_artifacts_present": True,
            "observation_shape": 72,
            "action_shape": 3,
            "direct_action_contract_pass": True,
            "direct_action_adapter_guard_rows_pass": True,
            "actor_contract_guard_rows_pass": True,
            "checkpoint_side_effect_guard_rows_pass": True,
            "claim_boundary_rows_pass": True,
            "runtime_base_policy_required": False,
            "base_policy_required_at_runtime": False,
            "candidate_output_semantics": "direct_action_clipped",
            "candidate_output_components": ["steer", "throttle", "brake"],
        },
    )
    write_csv_rows(path / "measurement_episode_rows.csv", _source_rows())
    write_csv_rows(path / "measurement_failure_rows.csv", [], fieldnames=["measurement_failure_id"])
    write_csv_rows(path / "metric_summary_rows.csv", [{"metric_summary_id": "metric-1", "group": "all"}])
    write_csv_rows(path / "gate_matrix.csv", [{"gate_id": "gate-1", "status_pass": True}])
    guard_row = {"guard_id": "guard-1", "status_pass": True}
    write_csv_rows(path / "direct_action_adapter_guard_rows.csv", [guard_row])
    write_csv_rows(path / "actor_contract_guard_rows.csv", [guard_row])
    write_csv_rows(path / "checkpoint_side_effect_guard_rows.csv", [guard_row])
    write_csv_rows(path / "claim_boundary_rows.csv", [{"claim_id": "claim-1", "status_pass": True}])


def test_materialize_direct_action_failure_decomposition_preserves_rows_and_claims(tmp_path: Path) -> None:
    m3067_dir = tmp_path / "m3067"
    output_dir = tmp_path / "m3069"
    follow_up_manifest = tmp_path / "m3070.json"
    doc_path = tmp_path / "m3069.md"
    audit_path = tmp_path / "m3068.md"
    audit_path.write_text("# audit\n", encoding="utf-8")
    _write_m3067_source(m3067_dir)

    summary = m3069.materialize(
        m3068_audit=audit_path,
        m3067_dir=m3067_dir,
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["measurement_episode_row_count"] == 32
    assert summary["measurement_success_count"] == 8
    assert summary["measurement_collision_count"] == 4
    assert summary["measurement_offtrack_count"] == 16
    assert summary["measurement_speed_too_low_count"] == 5
    assert summary["runtime_base_policy_required"] is False
    assert summary["repair_success_claim_made"] is False

    failure_rows = read_csv_rows(output_dir / "direct_action_failure_mode_rows.csv")
    all_failure = next(row for row in failure_rows if row["group_key"] == "all")
    assert all_failure["episode_count"] == "32"
    assert all_failure["offtrack_count"] == "16"
    assert all_failure["runtime_base_policy_required"] == "False"

    actuation_rows = read_csv_rows(output_dir / "direct_action_actuation_pressure_rows.csv")
    all_actuation = next(row for row in actuation_rows if row["group_key"] == "all")
    assert int(all_actuation["raw_out_of_bounds_row_count"]) == 32
    assert int(all_actuation["any_action_clip_row_count"]) == 32

    repair_rows = read_csv_rows(output_dir / "direct_action_repair_requirement_rows.csv")
    assert {row["requirement_family"] for row in repair_rows} >= {
        "offtrack_containment_recovery",
        "t5_collision_guard",
        "speed_floor_recovery",
        "direct_action_actuation_pressure",
        "claim_boundary_guard",
    }

    claim_rows = read_csv_rows(output_dir / "claim_boundary_rows.csv")
    assert all(row["status_pass"] == "True" for row in claim_rows)
    assert next(row for row in claim_rows if row["claim_id"] == "m3069-validation_result")["claim_made"] == "False"

    gate_rows = read_csv_rows(output_dir / "gate_matrix.csv")
    assert all(row["status_pass"] == "True" for row in gate_rows)

    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"] == m3069.NEXT_ID
    assert follow_up["status"] == "pending"
    assert follow_up["commands"][0]["command"] == "true"
