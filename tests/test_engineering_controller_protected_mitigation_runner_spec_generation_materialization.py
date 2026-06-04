from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import engineering_controller_protected_mitigation_runner_spec_generation_materialization as m2697


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2695_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "exact_current_runner_match_count": 0,
            "unbridgeable_target_row_count": 5,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    rows = [
        _target("target-role", "scenario_role", "unavoidable_mitigation"),
        _target("target-subject", "subject", "policy_a"),
        _target("target-axis", "dynamics_axis", "axis_a"),
        _target("target-metric", "metric", "minimum_obstacle_clearance_m"),
        _target("target-unmatched", "unknown_axis", "unmatched"),
    ]
    write_csv_rows(root / "unbridgeable_target_rows.csv", rows)
    write_csv_rows(root / "protected_bridge_rows.csv", rows)
    write_csv_rows(root / "actor_contract_guard_rows.csv", [{"guard_id": "ok", "status_pass": True}])
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "ok", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "ok", "status_pass": True}])


def _target(target_id: str, taxonomy_axis: str, value: str) -> dict[str, object]:
    return {
        "target_id": target_id,
        "target_family": "protected_mitigation_preservation",
        "source_key": f"boundary_{target_id}",
        "task_family": "route_a_protected",
        "source_edge_or_axis": taxonomy_axis,
        "taxonomy_axis": taxonomy_axis,
        "role_semantics_proxy": value,
        "unbridgeable_reason": "no exact current executable workload row",
        "parent_failure_type": "source_not_executable_in_current_runner",
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "materialization_only_no_execution": True,
        "claim_boundary": "test",
    }


def _write_m2662_source(root: Path) -> None:
    root.mkdir()
    write_json(root / "summary.json", {"status_pass": True, "panel_spec_row_count": 4})
    panel_rows = []
    for seed in (100, 101):
        for axis in ("axis_a", "axis_b"):
            panel_rows.append(
                {
                    "panel_spec_id": f"panel_{seed}_{axis}",
                    "role_family": "unavoidable_mitigation",
                    "role_class": "protected",
                    "seed_index": seed - 100,
                    "seed": seed,
                    "base_fixture_id": "hf0_four_wheel_unavoidable_mitigation_fixture",
                    "fixture_id": f"fixture_{seed}_{axis}",
                    "surface_id": "source_only_four_wheel_hf0",
                    "fixture_variant_digest": f"digest_{seed}_{axis}",
                    "initial_state_digest": f"initial_{seed}",
                    "fault_scale_digest": f"fault_{axis}",
                    "road_digest": f"road_{seed}",
                    "obstacle_digest": f"obstacle_{seed}",
                    "dynamics_axis_id": axis,
                    "dynamics_axis_family": axis,
                    "axis_index": 0 if axis == "axis_a" else 1,
                    "axis_family": axis,
                    "actor_visible_allowed": False,
                    "actor_input_contract_changed": False,
                    "hidden_diagnostics_metadata_only": True,
                    "claim_scope": "test",
                }
            )
    write_csv_rows(root / "panel_spec_rows.csv", panel_rows)
    write_csv_rows(root / "protected_mitigation_gate_rows.csv", [{"gate_id": "g", "gate_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "g", "status_pass": True}])


def _write_m2664_source(root: Path) -> None:
    root.mkdir()
    write_json(root / "summary.json", {"status_pass": True})
    write_csv_rows(
        root / "combined_failure_taxonomy_rows.csv",
        [
            {
                "taxonomy_id": "tax_policy_a_axis_a",
                "subject_id": "policy_a",
                "dynamics_axis_id": "axis_a",
                "blocking_metrics": "minimum_obstacle_clearance_m;severity_proxy",
                "primary_failure_family": "mixed_protected_blocker",
                "protected_blocker_preserved": True,
            },
            {
                "taxonomy_id": "tax_policy_a_axis_b",
                "subject_id": "policy_a",
                "dynamics_axis_id": "axis_b",
                "blocking_metrics": "minimum_obstacle_clearance_m",
                "primary_failure_family": "saturated_protected_blocker",
                "protected_blocker_preserved": True,
            },
        ],
    )


def _write_m2667_source(root: Path) -> None:
    root.mkdir()
    write_json(root / "summary.json", {"status_pass": True})
    write_csv_rows(
        root / "known_failure_boundary_rows.csv",
        [
            {
                "boundary_id": "boundary_target-unmatched",
                "failure_family": "unknown",
                "taxonomy_axis": "unknown_axis",
                "subject_or_axis_or_metric": "unmatched",
                "protected_blocker_preserved": True,
            }
        ],
    )


def test_m2697_materializes_protected_runner_specs_and_visible_unmaterialized_rows(tmp_path: Path) -> None:
    m2695_dir = tmp_path / "m2695"
    m2662_dir = tmp_path / "m2662"
    m2664_dir = tmp_path / "m2664"
    m2667_dir = tmp_path / "m2667"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2697.md"
    m2696_doc = tmp_path / "m2696.md"
    follow_up_manifest = tmp_path / "m2698.json"
    executable_specs = tmp_path / "specs.json"
    executable_workload = tmp_path / "workload.csv"
    config_path = tmp_path / "L3_online_gru.json"
    checkpoint_path = tmp_path / "policy.pt"
    reference_checkpoint = tmp_path / "reference.pt"
    m2696_doc.write_text("audit\n", encoding="utf-8")
    follow_up_manifest.write_text("{}\n", encoding="utf-8")
    config_path.write_text("{}\n", encoding="utf-8")
    checkpoint_path.write_text("checkpoint\n", encoding="utf-8")
    reference_checkpoint.write_text("reference\n", encoding="utf-8")
    _write_m2695_source(m2695_dir)
    _write_m2662_source(m2662_dir)
    _write_m2664_source(m2664_dir)
    _write_m2667_source(m2667_dir)
    write_json(executable_specs, {"executable_task_specs": [{"task_source_id": "m1690-ref"}]})
    write_csv_rows(
        executable_workload,
        [
            {
                "workload_id": "m1690-ref::L3_online_gru",
                "task_source_id": "m1690-ref",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": "source_edge",
                "profile_config_path": str(config_path),
                "checkpoint_path": str(reference_checkpoint),
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        ],
    )

    summary = m2697.materialize_protected_mitigation_runner_spec_generation(
        m2695_dir=m2695_dir,
        m2662_dir=m2662_dir,
        m2664_dir=m2664_dir,
        m2667_dir=m2667_dir,
        executable_specs=executable_specs,
        executable_workload=executable_workload,
        m2696_audit_doc=m2696_doc,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        checkpoint_path=checkpoint_path,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "engineering_controller_protected_mitigation_runner_spec_generation_materialization_pass"
    )
    assert summary["protected_target_count"] == 5
    assert summary["protected_runner_spec_row_count"] == 4
    assert summary["protected_workload_candidate_row_count"] == 4
    assert summary["traceability_target_count"] == 4
    assert summary["unmaterialized_bridge_row_count"] == 1
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

    runner_rows = _read_csv(output_dir / "protected_runner_spec_rows.csv")
    workload_rows = _read_csv(output_dir / "protected_workload_candidate_rows.csv")
    trace_rows = _read_csv(output_dir / "spec_traceability_rows.csv")
    unmaterialized_rows = _read_csv(output_dir / "unmaterialized_bridge_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["protected_task_family"] for row in runner_rows} == {"route_a_protected"}
    assert {row["environment_rollout_scheduled"] for row in runner_rows + workload_rows} == {"False"}
    assert {row["training_scheduled"] for row in runner_rows + workload_rows} == {"False"}
    assert {row["m1690_exact_workload_match"] for row in workload_rows} == {"False"}
    assert {row["target_id"] for row in trace_rows} == {
        "target-role",
        "target-subject",
        "target-axis",
        "target-metric",
    }
    assert unmaterialized_rows[0]["target_id"] == "target-unmatched"
    assert {row["protected_rows_in_success_denominator"] for row in runner_rows + workload_rows + trace_rows + unmaterialized_rows} == {
        "False"
    }
    assert {row["target_labels_actor_visible"] for row in runner_rows + workload_rows + trace_rows + unmaterialized_rows} == {
        "False"
    }
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {
        row["allowed_in_m2697"]
        for row in claim_rows
        if row["claim_family"] in {"driver_performance", "paper", "validation"}
    } == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
