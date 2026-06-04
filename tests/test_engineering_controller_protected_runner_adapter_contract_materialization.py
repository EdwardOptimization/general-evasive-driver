from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import engineering_controller_protected_runner_adapter_contract_materialization as m2700


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2697_source(root: Path, *, checkpoint_path: Path, config_path: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "protected_runner_spec_row_count": 2,
            "protected_workload_candidate_row_count": 2,
            "spec_traceability_row_count": 2,
            "unmaterialized_bridge_row_count": 1,
            "traceability_target_count": 2,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
            "protected_rows_in_success_denominator": False,
        },
    )
    write_csv_rows(
        root / "protected_runner_spec_rows.csv",
        [
            _runner("runner-a", "panel-a", "backend-a"),
            _runner("runner-b", "panel-b", "backend-b"),
        ],
    )
    write_csv_rows(
        root / "protected_workload_candidate_rows.csv",
        [
            _candidate("candidate-a", "runner-a", "panel-a", checkpoint_path, config_path, True),
            _candidate("candidate-b", "runner-b", "panel-b", checkpoint_path, config_path, False),
        ],
    )
    write_csv_rows(
        root / "spec_traceability_rows.csv",
        [
            _trace("trace-a", "target-a", "runner-a", "panel-a"),
            _trace("trace-b", "target-b", "runner-b", "panel-b"),
        ],
    )
    write_csv_rows(
        root / "unmaterialized_bridge_rows.csv",
        [
            {
                "target_id": "target-c",
                "target_family": "protected_mitigation_preservation",
                "source_key": "source-c",
                "taxonomy_axis": "unknown_axis",
                "role_semantics_proxy": "unknown",
                "protected_rows_in_success_denominator": False,
                "target_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": "source",
            }
        ],
    )
    write_csv_rows(root / "actor_contract_guard_rows.csv", [{"guard_id": "ok", "status_pass": True}])
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "ok", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "ok", "status_pass": True}])


def _runner(runner_id: str, panel_id: str, backend: str) -> dict[str, object]:
    return {
        "runner_spec_id": runner_id,
        "source_panel_spec_id": panel_id,
        "protected_task_family": "route_a_protected",
        "protected_source_edge": "unavoidable_mitigation|fresh_protected_nominal",
        "runner_backend_family": backend,
        "actor_observation_shape": 72,
        "action_shape": 3,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": "source",
    }


def _candidate(
    candidate_id: str,
    runner_id: str,
    panel_id: str,
    checkpoint_path: Path,
    config_path: Path,
    policy_checkpoint_exists: bool,
) -> dict[str, object]:
    return {
        "workload_candidate_id": candidate_id,
        "runner_spec_id": runner_id,
        "source_panel_spec_id": panel_id,
        "profile_name": "L3_online_gru",
        "policy_subject_id": "m2655_mitigation_preserving_policy",
        "policy_checkpoint_path": str(checkpoint_path),
        "policy_checkpoint_exists": policy_checkpoint_exists,
        "reference_profile_config_path": str(config_path),
        "reference_profile_config_exists": True,
        "m1690_exact_workload_match": False,
        "m1690_reference_workload_id": "m1680-ref::L3_online_gru",
        "protected_task_family": "route_a_protected",
        "protected_source_edge": "unavoidable_mitigation|fresh_protected_nominal",
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": "source",
    }


def _trace(trace_id: str, target_id: str, runner_id: str, panel_id: str) -> dict[str, object]:
    return {
        "trace_id": trace_id,
        "target_id": target_id,
        "target_family": "protected_mitigation_preservation",
        "source_key": f"source-{target_id}",
        "taxonomy_axis": "scenario_role",
        "runner_spec_id": runner_id,
        "panel_spec_id": panel_id,
        "join_status": "materialized",
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "actor_input_contract_changed": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": "source",
    }


def test_m2700_materializes_adapter_contract_rows_and_rejections(tmp_path: Path) -> None:
    m2697_dir = tmp_path / "m2697"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2700.md"
    follow_up_manifest = tmp_path / "m2701.json"
    executable_specs = tmp_path / "specs.json"
    executable_workload = tmp_path / "workload.csv"
    checkpoint_path = tmp_path / "policy.pt"
    config_path = tmp_path / "profile.json"
    checkpoint_path.write_text("checkpoint\n", encoding="utf-8")
    config_path.write_text("{}\n", encoding="utf-8")
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
    _write_m2697_source(m2697_dir, checkpoint_path=checkpoint_path, config_path=config_path)

    summary = m2700.materialize_protected_runner_adapter_contract(
        m2697_dir=m2697_dir,
        executable_specs=executable_specs,
        executable_workload=executable_workload,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_protected_runner_adapter_contract_materialization_pass"
    assert summary["adapter_candidate_mapping_row_count"] == 2
    assert summary["adapter_rejection_row_count"] == 2
    assert summary["adapter_contract_materialized_not_execution_admitted_count"] == 1
    assert summary["adapter_execution_admitted_count"] == 0
    assert summary["m1690_exact_workload_match_count_adapter"] == 0
    assert summary["all_candidates_mapped_or_rejected"] is True
    assert summary["all_protected_targets_accounted"] is True
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    source_rows = _read_csv(output_dir / "adapter_input_source_rows.csv")
    mapping_rows = _read_csv(output_dir / "adapter_candidate_mapping_rows.csv")
    rejection_rows = _read_csv(output_dir / "adapter_rejection_rows.csv")
    trace_rows = _read_csv(output_dir / "adapter_traceability_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["source_exists"] for row in source_rows} == {"True"}
    assert {row["adapter_admission_status"] for row in mapping_rows} == {
        "adapter_contract_materialized_not_execution_admitted",
        "adapter_rejected_missing_policy_checkpoint",
    }
    assert {row["environment_rollout_scheduled"] for row in mapping_rows} == {"False"}
    assert {row["training_scheduled"] for row in mapping_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in mapping_rows + trace_rows} == {"False"}
    assert {row["protected_labels_actor_visible"] for row in mapping_rows + trace_rows} == {"False"}
    assert "adapter_rejected_missing_policy_checkpoint" in {row["rejection_type"] for row in rejection_rows}
    assert "source_unmaterialized_preserved_not_adapter_candidate" in {
        row["adapter_trace_status"] for row in trace_rows
    }
    assert {row["target_id"] for row in trace_rows} == {"target-a", "target-b", "target-c"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {
        row["allowed_in_m2700"]
        for row in claim_rows
        if row["claim_family"] in {"driver_performance", "paper", "validation"}
    } == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
