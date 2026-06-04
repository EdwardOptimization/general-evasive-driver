from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight as m2693


def _write_m2691_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "target_panel_row_count": 3,
            "offtrack_target_row_count": 2,
            "protected_target_row_count": 1,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    write_csv_rows(
        root / "target_panel_rows.csv",
        [
            _target("m2691-target-0001", "current_sim_offtrack", "current_sim_offtrack_containment", "T4", "edge_a"),
            _target("m2691-target-0002", "current_sim_offtrack", "current_sim_offtrack_containment", "T5", "edge_b"),
            _target("m2691-target-0003", "protected_mitigation", "protected_mitigation_preservation", "route_a_protected", "subject"),
        ],
        fieldnames=m2693.TARGET_METADATA_FIELDNAMES + ["claim_scope"],
    )
    write_csv_rows(
        root / "source_diversity_plan_rows.csv",
        [
            {
                "plan_id": "joint",
                "included_source_families": "current_sim_offtrack;protected_mitigation",
                "same_public_gate_repair_loop": False,
                "actor_visible_labels_required": False,
            }
        ],
    )
    write_csv_rows(
        root / "actor_contract_guard_rows.csv",
        [
            {
                "guard_id": "obs",
                "contract_field": "observation_shape",
                "observed_value": 72,
                "expected_value": 72,
                "status_pass": True,
                "actor_visible": True,
            },
            {
                "guard_id": "act",
                "contract_field": "action_shape",
                "observed_value": 3,
                "expected_value": 3,
                "status_pass": True,
                "actor_visible": True,
            },
        ],
    )
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "ok", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "ok", "status_pass": True}])


def _target(
    target_id: str,
    source_family: str,
    target_family: str,
    task_family: str,
    source_edge: str,
) -> dict[str, object]:
    return {
        "target_id": target_id,
        "target_family": target_family,
        "source_family": source_family,
        "source_key": f"{task_family}:{source_edge}",
        "task_family": task_family,
        "source_edge_or_axis": source_edge,
        "role_semantics_proxy": "hidden_dynamics_or_actuator_response",
        "episode_or_row_count": 1,
        "blocking_count": 1,
        "regressed_row_count": "",
        "existing_success_count": 0,
        "existing_collision_count": 0,
        "existing_offtrack_count": 1,
        "source_diversity_bucket": "bucket",
        "future_execution_role": "post_audit_measured_target_candidate",
        "diagnostic_only_no_verdict": True,
        "actor_input_contract_changed": False,
        "target_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "protected_rows_in_success_denominator": False,
        "claim_scope": "test",
    }


def test_m2693_workload_mapping_is_single_profile_and_current_sim_only() -> None:
    target_rows = [
        _target("m2691-target-0001", "current_sim_offtrack", "current_sim_offtrack_containment", "T4", "edge_a"),
        _target("m2691-target-0002", "protected_mitigation", "protected_mitigation_preservation", "route_a_protected", "subject"),
    ]
    workload_rows = [
        {"workload_id": "w0", "task_family": "T4", "source_edge": "edge_a", "profile_name": "L3_online_gru"},
        {"workload_id": "w1", "task_family": "T4", "source_edge": "edge_a", "profile_name": "L1_one_step"},
        {"workload_id": "w2", "task_family": "T5", "source_edge": "edge_b", "profile_name": "L3_online_gru"},
    ]

    mapped = m2693.build_workload_by_target(
        target_rows=target_rows,
        workload_rows=workload_rows,
        profile_name="L3_online_gru",
    )

    assert set(mapped) == {"m2691-target-0001"}
    assert mapped["m2691-target-0001"]["workload_id"] == "w0"


def test_m2693_wrapper_records_protected_failures_without_overclaim(monkeypatch, tmp_path: Path) -> None:
    m2691_dir = tmp_path / "m2691"
    output_dir = tmp_path / "m2693"
    doc_path = tmp_path / "m2693.md"
    follow_up_manifest = tmp_path / "m2694.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    m1674_dir = tmp_path / "m1674"
    m1674_dir.mkdir()
    write_json(specs_path, {"executable_task_specs": []})
    write_csv_rows(workload_path, [{"workload_id": "placeholder"}])
    write_json(m1674_dir / "summary.json", {"status_pass": True})
    _write_m2691_source(m2691_dir)

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        target_rows = m2693.load_target_panel_rows(Path(kwargs["m2691_dir"]))
        episode_rows = []
        failure_rows = []
        for index, target in enumerate(target_rows):
            if target["source_family"] == "current_sim_offtrack":
                episode_rows.append(
                    {
                        **m2693.target_metadata(target),
                        "seed": 269300 + index,
                        "workload_id": f"w{index}",
                        "profile_name": "L3_online_gru",
                        "runtime_profile_name": "L3_online_gru",
                        "steps": 80,
                        "collision": False,
                        "success": index == 0,
                        "termination_reason": "" if index == 0 else "off_track",
                        "min_clearance_margin": 0.2,
                        "return": 1.0,
                        "action_rate_mean": 0.1,
                        "high_sideslip_fraction": 0.0,
                        "bounded_target_panel_execution": True,
                        "training_started": False,
                        "replay_started": False,
                        "ppo_used": False,
                        "private_holdout_used": False,
                        "profile_specific_tuning": False,
                        "ranking_run": False,
                        "success_rate_verdict_claim_made": False,
                        "driver_performance_claim_made": False,
                    }
                )
            else:
                failure_rows.append(
                    m2693.failure_row(
                        target,
                        profile_name="L3_online_gru",
                        policy_subject_id="m2655_mitigation_preserving_policy",
                        checkpoint_path=Path("checkpoint.pt"),
                        workload_id="",
                        error_type="source_not_executable_in_current_runner",
                        error_message="protected test target",
                    )
                )
        write_csv_rows(output / "target_execution_rows.csv", episode_rows)
        write_csv_rows(output / "failure_rows.csv", failure_rows, fieldnames=m2693.FAILURE_FIELDNAMES)
        return m2693.finalize_target_panel_outputs(
            output_dir=output,
            target_rows=target_rows,
            profile_name="L3_online_gru",
            policy_subject_id="m2655_mitigation_preserving_policy",
            checkpoint_path=Path("checkpoint.pt"),
            next_blocker="m2694",
        )

    monkeypatch.setattr(m2693, "run_target_panel_execution", fake_execution)
    monkeypatch.setattr(m2693, "TARGET_PANEL_COUNT", 3)
    monkeypatch.setattr(m2693, "OFFTRACK_TARGET_COUNT", 2)
    monkeypatch.setattr(m2693, "PROTECTED_TARGET_COUNT", 1)

    summary = m2693.run_source_diverse_offtrack_protected_bounded_execution_preflight(
        m2691_dir=m2691_dir,
        executable_specs=specs_path,
        workload=workload_path,
        m1674_run_dir=m1674_dir,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["episode_count"] == 2
    assert summary["failure_count"] == 1
    assert summary["protected_failure_count"] == 1
    assert summary["unexpected_failure_count"] == 0
    assert summary["accounted_target_count"] == 3
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False
    assert summary["gate_matrix_pass"] is True

    for path in summary["paths"].values():
        assert Path(path).exists()
    assert read_json(output_dir / "summary.json") == summary
    assert doc_path.read_text(encoding="utf-8").strip()

    claim_rows = m2693.read_csv_rows(output_dir / "claim_boundary_rows.csv")
    failure_rows = m2693.read_csv_rows(output_dir / "failure_rows.csv")
    assert {row["claim_made"] for row in claim_rows if row["claim_id"].endswith("driver_performance")} == {"False"}
    assert {row["error_type"] for row in failure_rows} == {"source_not_executable_in_current_runner"}
