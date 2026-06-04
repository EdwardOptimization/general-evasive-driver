from __future__ import annotations

import csv
from pathlib import Path

from autodrift import engineering_controller_protected_runner_simulator_workload_support_materialization as m2706
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2703_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "result_class": "engineering_controller_protected_runner_execution_admission_materialization_pass",
            "gate_matrix_pass": True,
            "execution_admission_candidate_row_count": 2,
            "execution_admission_rejection_row_count": 2,
            "execution_admission_traceability_row_count": 2,
            "execution_admission_admitted_count": 0,
            "execution_admission_blocked_no_current_m1690_workload_count": 2,
            "m1690_exact_workload_match_count_source": 0,
            "m1690_exact_workload_match_count_execution_admission": 0,
            "protected_target_count": 2,
            "execution_admission_traceability_target_count": 2,
        },
    )
    write_csv_rows(
        root / "execution_admission_input_source_rows.csv",
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
    candidates = [
        _execution_candidate("m2703-execution-admission-candidate-0001", "m2700-adapter-candidate-0001", "runner-a"),
        _execution_candidate("m2703-execution-admission-candidate-0002", "m2700-adapter-candidate-0002", "runner-b"),
    ]
    write_csv_rows(root / "execution_admission_candidate_rows.csv", candidates)
    write_csv_rows(
        root / "execution_admission_rejection_rows.csv",
        [
            _rejection("m2703-rejection-0001", "m2700-adapter-candidate-0001"),
            _rejection("m2703-rejection-0002", "m2700-adapter-candidate-0002"),
        ],
    )
    write_csv_rows(
        root / "execution_admission_traceability_rows.csv",
        [
            _trace("m2703-execution-admission-trace-0001", "m2703-execution-admission-candidate-0001", "target-a"),
            _trace("m2703-execution-admission-trace-0002", "m2703-execution-admission-candidate-0002", "target-b"),
        ],
    )
    write_csv_rows(root / "actor_contract_guard_rows.csv", [{"guard_id": "ok", "status_pass": True}])
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "ok", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "ok", "status_pass": True}])


def _write_m2700_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "result_class": "engineering_controller_protected_runner_adapter_contract_materialization_pass",
            "adapter_candidate_mapping_row_count": 2,
            "adapter_traceability_row_count": 2,
            "adapter_execution_admitted_count": 0,
            "adapter_contract_materialized_not_execution_admitted_count": 2,
            "m1690_exact_workload_match_count_adapter": 0,
        },
    )
    write_csv_rows(
        root / "adapter_candidate_mapping_rows.csv",
        [
            {"adapter_candidate_id": "m2700-adapter-candidate-0001", "runner_spec_id": "runner-a"},
            {"adapter_candidate_id": "m2700-adapter-candidate-0002", "runner_spec_id": "runner-b"},
        ],
    )
    write_csv_rows(
        root / "adapter_traceability_rows.csv",
        [
            {"adapter_trace_id": "m2700-adapter-trace-0001", "target_id": "target-a"},
            {"adapter_trace_id": "m2700-adapter-trace-0002", "target_id": "target-b"},
        ],
    )


def _execution_candidate(candidate_id: str, adapter_id: str, runner_id: str) -> dict[str, object]:
    return {
        "execution_admission_candidate_id": candidate_id,
        "adapter_candidate_id": adapter_id,
        "workload_candidate_id": f"{runner_id}::L3_online_gru",
        "runner_spec_id": runner_id,
        "source_panel_spec_id": f"panel-{runner_id}",
        "profile_name": "L3_online_gru",
        "policy_subject_id": "m2655_mitigation_preserving_policy",
        "policy_checkpoint_path": "policy.pt",
        "policy_checkpoint_exists": True,
        "reference_profile_config_path": "profile.json",
        "reference_profile_config_exists": True,
        "adapter_admission_status": "adapter_contract_materialized_not_execution_admitted",
        "m1690_exact_workload_match": False,
        "m1690_reference_workload_id": "m1680-ref::L3_online_gru",
        "protected_task_family": "route_a_protected",
        "protected_source_edge": "unavoidable_mitigation|fresh_protected_nominal",
        "execution_admission_status": "execution_admission_blocked_no_current_m1690_workload",
        "execution_rejection_status": "execution_admission_blocked_no_current_m1690_workload",
        "execution_admission_rule": "m2700_adapter_row_to_no_execution_admission_classification",
        "required_follow_up": "materialize simulator/workload support or branch synthesis before protected execution",
        "environment_reset_admitted": False,
        "environment_rollout_scheduled": False,
        "measured_validation_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "protected_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_scope": "m2703",
    }


def _rejection(rejection_id: str, adapter_id: str) -> dict[str, object]:
    return {
        "rejection_id": rejection_id,
        "candidate_or_source_id": adapter_id,
        "rejection_type": "execution_admission_blocked_no_current_m1690_workload",
        "rejection_reason": "adapter row has no exact current M1690 executable workload match",
        "required_follow_up": "materialize simulator/workload support or branch synthesis before protected execution",
        "actor_visible": False,
        "claim_scope": "m2703",
    }


def _trace(trace_id: str, candidate_id: str, target_id: str) -> dict[str, object]:
    adapter_id = candidate_id.replace("m2703-execution-admission", "m2700-adapter")
    return {
        "execution_admission_trace_id": trace_id,
        "adapter_trace_id": trace_id.replace("m2703-execution-admission", "m2700-adapter"),
        "source_trace_id": trace_id.replace("m2703-execution-admission", "source"),
        "execution_admission_candidate_id": candidate_id,
        "adapter_candidate_id": adapter_id,
        "workload_candidate_id": f"workload-{target_id}",
        "runner_spec_id": f"runner-{target_id}",
        "target_id": target_id,
        "target_family": "protected_mitigation_preservation",
        "source_key": f"source-{target_id}",
        "taxonomy_axis": "scenario_role",
        "source_panel_spec_id": f"panel-{target_id}",
        "join_status": "materialized",
        "execution_admission_trace_status": "execution_admission_trace_materialized",
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "actor_input_contract_changed": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_scope": "m2703",
    }


def test_m2706_materializes_no_execution_support_rows(tmp_path: Path) -> None:
    m2703_dir = tmp_path / "m2703"
    m2700_dir = tmp_path / "m2700"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2706.md"
    m2704_audit = tmp_path / "m2704.md"
    m2705_design = tmp_path / "m2705.md"
    route_plan = tmp_path / "route.md"
    follow_up_manifest = tmp_path / "m2707.json"
    executable_specs = tmp_path / "specs.json"
    executable_workload = tmp_path / "workload.csv"
    _write_m2703_source(m2703_dir)
    _write_m2700_source(m2700_dir)
    m2704_audit.write_text("accept_m2703_route_to_simulator_workload_support_design\n", encoding="utf-8")
    m2705_design.write_text(
        "admit_protected_runner_simulator_workload_support_materialization_preflight\n",
        encoding="utf-8",
    )
    route_plan.write_text("# Post-M2470\n\n## Route A: Engineering Controller Mainline\n", encoding="utf-8")
    follow_up_manifest.write_text("{}\n", encoding="utf-8")
    write_json(executable_specs, {"executable_task_specs": [{"task_source_id": "m1680-ref"}]})
    write_csv_rows(
        executable_workload,
        [
            {
                "workload_id": "m1680-ref::L3_online_gru",
                "task_source_id": "m1680-ref",
                "profile_name": "L3_online_gru",
            }
        ],
    )

    summary = m2706.materialize_protected_runner_simulator_workload_support(
        m2703_dir=m2703_dir,
        m2700_dir=m2700_dir,
        m2704_audit=m2704_audit,
        m2705_design=m2705_design,
        executable_specs=executable_specs,
        executable_workload=executable_workload,
        route_plan=route_plan,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_protected_runner_simulator_workload_support_materialization_pass"
    assert summary["support_candidate_row_count"] == 2
    assert summary["support_blocker_row_count"] == 2
    assert summary["support_traceability_row_count"] == 2
    assert summary["support_ready_existing_m1690_workload_count"] == 0
    assert summary["support_materialized_candidate_requires_new_workload_row_count"] == 2
    assert summary["m2703_execution_admission_admitted_count"] == 0
    assert summary["m1690_exact_workload_match_count_support"] == 0
    assert summary["support_ready_rows_zero_without_exact_m1690_match"] is True
    assert summary["all_candidates_classified"] is True
    assert summary["all_non_ready_rows_have_blockers"] is True
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

    source_rows = _read_csv(output_dir / "support_input_source_rows.csv")
    candidate_rows = _read_csv(output_dir / "support_candidate_rows.csv")
    blocker_rows = _read_csv(output_dir / "support_blocker_rows.csv")
    trace_rows = _read_csv(output_dir / "support_traceability_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["source_exists"] for row in source_rows} == {"True"}
    assert {row["support_status"] for row in candidate_rows} == {
        "support_materialized_candidate_requires_new_workload_row"
    }
    assert {row["candidate_can_be_represented_in_current_runner"] for row in candidate_rows} == {"False"}
    assert {row["candidate_requires_new_workload_row"] for row in candidate_rows} == {"True"}
    assert {row["candidate_requires_simulator_fixture"] for row in candidate_rows} == {"True"}
    assert {row["environment_reset_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["environment_rollout_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["measured_validation_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["training_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in candidate_rows + trace_rows} == {"False"}
    assert {row["protected_labels_actor_visible"] for row in candidate_rows + trace_rows} == {"False"}
    assert {row["blocker_type"] for row in blocker_rows} == {"support_blocker_new_workload_row_required"}
    assert {row["protected_target_id"] for row in trace_rows} == {"target-a", "target-b"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {
        row["allowed_in_m2706"]
        for row in claim_rows
        if row["claim_family"] in {"driver_performance", "paper", "validation"}
    } == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
