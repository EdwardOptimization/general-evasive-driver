from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import engineering_controller_protected_mitigation_target_executable_surface_bridge_materialization as m2695


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2693_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "protected_target_count": 2,
            "protected_failure_count": 2,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
            "protected_rows_in_success_denominator": False,
        },
    )
    failure_rows = []
    for target_id, task_family, source_edge in [
        ("m2691-target-0010", "T4", "edge_a"),
        ("m2691-target-0011", "route_a_protected", "subject"),
    ]:
        failure_rows.append(
            {
                "target_id": target_id,
                "target_family": "protected_mitigation_preservation",
                "source_family": "protected_mitigation",
                "source_key": f"boundary_{target_id}",
                "task_family": task_family,
                "source_edge_or_axis": source_edge,
                "role_semantics_proxy": "policy_a",
                "error_type": "source_not_executable_in_current_runner",
                "error_message": "protected target has no mapping",
                "protected_rows_in_success_denominator": False,
                "target_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
            }
        )
    write_csv_rows(root / "failure_rows.csv", failure_rows)
    write_csv_rows(root / "protected_target_aggregate.csv", [{"target_id": row["target_id"]} for row in failure_rows])
    write_csv_rows(root / "source_diversity_aggregate.csv", [{"source_family": "protected_mitigation"}])
    write_csv_rows(root / "blocker_join_rows.csv", [{"target_id": row["target_id"], "accounted": True} for row in failure_rows])
    write_csv_rows(
        root / "actor_contract_join_rows.csv",
        [
            {
                "contract_field": "observation_shape",
                "observed_value": 72,
                "expected_value": 72,
                "status_pass": True,
            },
            {
                "contract_field": "action_shape",
                "observed_value": 3,
                "expected_value": 3,
                "status_pass": True,
            },
        ],
    )
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "ok", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "ok", "status_pass": True}])


def _write_m2691_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "protected_target_row_count": 2,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    rows = [
        _target("m2691-target-0010", "boundary_m2691-target-0010", "T4", "edge_a", "dynamics_axis"),
        _target("m2691-target-0011", "boundary_m2691-target-0011", "route_a_protected", "subject", "subject"),
    ]
    write_csv_rows(root / "target_panel_rows.csv", rows)


def _target(
    target_id: str,
    source_key: str,
    task_family: str,
    source_edge_or_axis: str,
    taxonomy_axis: str,
) -> dict[str, object]:
    return {
        "target_id": target_id,
        "target_family": "protected_mitigation_preservation",
        "source_family": "protected_mitigation",
        "source_key": source_key,
        "task_family": task_family,
        "source_edge_or_axis": source_edge_or_axis,
        "role_semantics_proxy": "policy_a" if taxonomy_axis == "subject" else "fresh_protected_nominal",
        "episode_or_row_count": 2,
        "blocking_count": 2,
        "regressed_row_count": 1,
        "source_diversity_bucket": "route_a_fresh_protected_taxonomy",
        "diagnostic_only_no_verdict": True,
        "actor_input_contract_changed": False,
        "target_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "protected_rows_in_success_denominator": False,
    }


def _write_m2664_source(root: Path) -> None:
    root.mkdir()
    write_csv_rows(
        root / "combined_failure_taxonomy_rows.csv",
        [
            {
                "subject_id": "policy_a",
                "dynamics_axis_id": "fresh_protected_nominal",
                "primary_failure_family": "mixed_protected_blocker",
                "protected_blocker_preserved": True,
                "blocking_metrics": "minimum_obstacle_clearance_m",
            }
        ],
    )


def _write_m2667_source(root: Path) -> None:
    root.mkdir()
    write_csv_rows(
        root / "known_failure_boundary_rows.csv",
        [
            {
                "boundary_id": "boundary_m2691-target-0010",
                "failure_family": "mixed_protected_blocker",
                "taxonomy_axis": "dynamics_axis",
                "subject_or_axis_or_metric": "fresh_protected_nominal",
                "row_count": 2,
                "blocking_row_count": 2,
                "regressed_row_count": 1,
                "protected_blocker_preserved": True,
            },
            {
                "boundary_id": "boundary_m2691-target-0011",
                "failure_family": "saturated_protected_blocker",
                "taxonomy_axis": "subject",
                "subject_or_axis_or_metric": "policy_a",
                "row_count": 2,
                "blocking_row_count": 2,
                "regressed_row_count": 1,
                "protected_blocker_preserved": True,
            },
        ],
    )


def test_m2695_materializes_bridge_candidates_and_unbridgeable_rows(tmp_path: Path) -> None:
    m2693_dir = tmp_path / "m2693"
    m2691_dir = tmp_path / "m2691"
    m2664_dir = tmp_path / "m2664"
    m2667_dir = tmp_path / "m2667"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2695.md"
    m2694_doc = tmp_path / "m2694.md"
    follow_up_manifest = tmp_path / "m2696.json"
    executable_specs = tmp_path / "specs.json"
    executable_workload = tmp_path / "workload.csv"
    m2694_doc.write_text("audit\n", encoding="utf-8")
    follow_up_manifest.write_text("{}\n", encoding="utf-8")
    _write_m2693_source(m2693_dir)
    _write_m2691_source(m2691_dir)
    _write_m2664_source(m2664_dir)
    _write_m2667_source(m2667_dir)
    write_json(executable_specs, {"executable_task_specs": [{"task_source_id": "spec-a", "env_template_family": "env-a"}]})
    write_csv_rows(
        executable_workload,
        [
            {
                "workload_id": "spec-a::L3_online_gru",
                "task_source_id": "spec-a",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": "edge_a",
                "executable_source_family": "current_sim",
                "env_template_family": "env-a",
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        ],
    )

    summary = m2695.materialize_protected_mitigation_target_executable_surface_bridge(
        m2693_dir=m2693_dir,
        m2691_dir=m2691_dir,
        m2664_dir=m2664_dir,
        m2667_dir=m2667_dir,
        executable_specs=executable_specs,
        executable_workload=executable_workload,
        m2694_audit_doc=m2694_doc,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "engineering_controller_protected_mitigation_target_executable_surface_bridge_materialization_pass"
    )
    assert summary["protected_target_count"] == 2
    assert summary["protected_bridge_row_count"] == 2
    assert summary["executable_candidate_row_count"] == 1
    assert summary["unbridgeable_target_row_count"] == 1
    assert summary["all_protected_targets_accounted"] is True
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    bridge_rows = _read_csv(output_dir / "protected_bridge_rows.csv")
    candidate_rows = _read_csv(output_dir / "executable_candidate_rows.csv")
    unbridgeable_rows = _read_csv(output_dir / "unbridgeable_target_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["bridge_status"] for row in bridge_rows} == {"executable_candidate", "unbridgeable"}
    assert candidate_rows[0]["workload_id"] == "spec-a::L3_online_gru"
    assert "no exact current executable workload row" in unbridgeable_rows[0]["unbridgeable_reason"]
    assert {row["protected_rows_in_success_denominator"] for row in bridge_rows + candidate_rows + unbridgeable_rows} == {
        "False"
    }
    assert {row["target_labels_actor_visible"] for row in bridge_rows + candidate_rows + unbridgeable_rows} == {"False"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {
        row["allowed_in_m2695"]
        for row in claim_rows
        if row["claim_family"] in {"driver_performance", "paper", "validation"}
    } == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
