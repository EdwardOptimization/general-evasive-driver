from __future__ import annotations

import csv
from pathlib import Path

from autodrift import engineering_controller_protected_runner_execution_admission_materialization as m2703
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2700_source(root: Path, *, checkpoint_path: Path, config_path: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "result_class": "engineering_controller_protected_runner_adapter_contract_materialization_pass",
            "adapter_candidate_mapping_row_count": 2,
            "adapter_execution_admitted_count": 0,
            "adapter_contract_materialized_not_execution_admitted_count": 2,
            "m1690_exact_workload_match_count_adapter": 0,
            "protected_target_count": 2,
            "adapter_traceability_target_count": 2,
            "gate_matrix_pass": True,
        },
    )
    write_csv_rows(
        root / "adapter_input_source_rows.csv",
        [
            {
                "source_artifact_id": "source-a",
                "source_path": "source-a.csv",
                "source_exists": True,
                "required": True,
                "row_count_or_summary": "rows=2",
                "source_role": "test",
                "claim_scope": "source",
                "blocked_interpretation": "blocked",
            }
        ],
    )
    write_csv_rows(
        root / "adapter_candidate_mapping_rows.csv",
        [
            _adapter_candidate("m2700-adapter-candidate-0001", "workload-a", "runner-a", checkpoint_path, config_path),
            _adapter_candidate("m2700-adapter-candidate-0002", "workload-b", "runner-b", checkpoint_path, config_path),
        ],
    )
    write_csv_rows(root / "adapter_rejection_rows.csv", [])
    write_csv_rows(
        root / "adapter_traceability_rows.csv",
        [
            _trace("trace-a", "m2700-adapter-candidate-0001", "target-a", "runner-a"),
            _trace("trace-b", "m2700-adapter-candidate-0002", "target-b", "runner-b"),
        ],
    )
    write_csv_rows(root / "actor_contract_guard_rows.csv", [{"guard_id": "ok", "status_pass": True}])
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "ok", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "ok", "status_pass": True}])


def _adapter_candidate(
    adapter_id: str,
    workload_id: str,
    runner_id: str,
    checkpoint_path: Path,
    config_path: Path,
) -> dict[str, object]:
    return {
        "adapter_candidate_id": adapter_id,
        "workload_candidate_id": workload_id,
        "runner_spec_id": runner_id,
        "source_panel_spec_id": f"panel-{runner_id}",
        "profile_name": "L3_online_gru",
        "policy_subject_id": "m2655_mitigation_preserving_policy",
        "policy_checkpoint_path": str(checkpoint_path),
        "policy_checkpoint_exists": True,
        "reference_profile_config_path": str(config_path),
        "reference_profile_config_exists": True,
        "adapter_admission_status": "adapter_contract_materialized_not_execution_admitted",
        "m1690_exact_workload_match": False,
        "m1690_reference_workload_id": "m1680-ref::L3_online_gru",
        "protected_task_family": "route_a_protected",
        "protected_source_edge": "unavoidable_mitigation|fresh_protected_nominal",
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "protected_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
    }


def _trace(trace_id: str, adapter_id: str, target_id: str, runner_id: str) -> dict[str, object]:
    return {
        "adapter_trace_id": trace_id,
        "source_trace_id": f"source-{trace_id}",
        "adapter_candidate_id": adapter_id,
        "workload_candidate_id": f"workload-{target_id}",
        "runner_spec_id": runner_id,
        "target_id": target_id,
        "target_family": "protected_mitigation_preservation",
        "source_key": f"source-{target_id}",
        "taxonomy_axis": "scenario_role",
        "source_panel_spec_id": f"panel-{runner_id}",
        "join_status": "adapter_candidate_trace_materialized",
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "actor_input_contract_changed": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_scope": "source",
    }


def test_m2703_materializes_no_execution_admission_rows(tmp_path: Path) -> None:
    m2700_dir = tmp_path / "m2700"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2703.md"
    m2701_audit = tmp_path / "m2701.md"
    m2702_design = tmp_path / "m2702.md"
    follow_up_manifest = tmp_path / "m2704.json"
    executable_specs = tmp_path / "specs.json"
    executable_workload = tmp_path / "workload.csv"
    checkpoint_path = tmp_path / "policy.pt"
    config_path = tmp_path / "profile.json"
    checkpoint_path.write_text("checkpoint\n", encoding="utf-8")
    config_path.write_text("{}\n", encoding="utf-8")
    m2701_audit.write_text("accept_m2700_route_to_protected_runner_execution_admission_design\n", encoding="utf-8")
    m2702_design.write_text("admit_protected_runner_execution_admission_materialization_preflight\n", encoding="utf-8")
    follow_up_manifest.write_text("{}\n", encoding="utf-8")
    write_json(executable_specs, {"executable_task_specs": [{"task_source_id": "m1680-ref"}]})
    write_csv_rows(
        executable_workload,
        [
            {
                "workload_id": "m1680-ref::L3_online_gru",
                "task_source_id": "m1680-ref",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": "source-edge",
            }
        ],
    )
    _write_m2700_source(m2700_dir, checkpoint_path=checkpoint_path, config_path=config_path)

    summary = m2703.materialize_protected_runner_execution_admission(
        m2700_dir=m2700_dir,
        m2701_audit=m2701_audit,
        m2702_design=m2702_design,
        executable_specs=executable_specs,
        executable_workload=executable_workload,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_protected_runner_execution_admission_materialization_pass"
    assert summary["execution_admission_candidate_row_count"] == 2
    assert summary["execution_admission_rejection_row_count"] == 2
    assert summary["execution_admission_admitted_count"] == 0
    assert summary["execution_admission_blocked_no_current_m1690_workload_count"] == 2
    assert summary["m1690_exact_workload_match_count_execution_admission"] == 0
    assert summary["all_candidates_classified"] is True
    assert summary["all_non_admitted_rows_have_rejection"] is True
    assert summary["all_protected_targets_accounted"] is True
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["measured_validation_run"] is False
    assert summary["training_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    source_rows = _read_csv(output_dir / "execution_admission_input_source_rows.csv")
    candidate_rows = _read_csv(output_dir / "execution_admission_candidate_rows.csv")
    rejection_rows = _read_csv(output_dir / "execution_admission_rejection_rows.csv")
    trace_rows = _read_csv(output_dir / "execution_admission_traceability_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["source_exists"] for row in source_rows} == {"True"}
    assert {row["execution_admission_status"] for row in candidate_rows} == {
        "execution_admission_blocked_no_current_m1690_workload"
    }
    assert {row["environment_reset_admitted"] for row in candidate_rows} == {"False"}
    assert {row["environment_rollout_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["measured_validation_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["training_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in candidate_rows + trace_rows} == {"False"}
    assert {row["protected_labels_actor_visible"] for row in candidate_rows + trace_rows} == {"False"}
    assert {row["rejection_type"] for row in rejection_rows} == {
        "execution_admission_blocked_no_current_m1690_workload"
    }
    assert {row["target_id"] for row in trace_rows} == {"target-a", "target-b"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {
        row["allowed_in_m2703"]
        for row in claim_rows
        if row["claim_family"] in {"driver_performance", "paper", "validation"}
    } == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
