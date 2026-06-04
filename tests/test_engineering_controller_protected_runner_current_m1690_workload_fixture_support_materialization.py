from __future__ import annotations

import csv
from pathlib import Path

from autodrift import (
    engineering_controller_protected_runner_current_m1690_workload_fixture_support_materialization as m2710,
)
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2706_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "result_class": "engineering_controller_protected_runner_simulator_workload_support_materialization_pass",
            "gate_matrix_pass": True,
            "support_candidate_row_count": 2,
            "support_blocker_row_count": 2,
            "support_traceability_row_count": 2,
            "support_ready_existing_m1690_workload_count": 0,
            "support_materialized_candidate_requires_new_workload_row_count": 2,
            "m1690_exact_workload_match_count_support": 0,
            "m2703_execution_admission_admitted_count": 0,
            "protected_target_count": 2,
            "support_traceability_target_count": 2,
        },
    )
    write_csv_rows(root / "support_input_source_rows.csv", [{"source_artifact_id": "source", "source_exists": True}])
    write_csv_rows(
        root / "support_candidate_rows.csv",
        [
            _support_candidate("m2706-support-candidate-0001", "runner-a", "target-a"),
            _support_candidate("m2706-support-candidate-0002", "runner-b", "target-b"),
        ],
    )
    write_csv_rows(
        root / "support_blocker_rows.csv",
        [
            _support_blocker("m2706-support-blocker-0001", "m2706-support-candidate-0001"),
            _support_blocker("m2706-support-blocker-0002", "m2706-support-candidate-0002"),
        ],
    )
    write_csv_rows(
        root / "support_traceability_rows.csv",
        [
            _support_trace("m2706-support-trace-0001", "m2706-support-candidate-0001", "runner-a", "target-a"),
            _support_trace("m2706-support-trace-0002", "m2706-support-candidate-0002", "runner-b", "target-b"),
        ],
    )
    write_csv_rows(root / "actor_contract_guard_rows.csv", [{"guard_id": "ok", "status_pass": True}])
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "ok", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "ok", "status_pass": True}])


def _write_m2697_source(root: Path, checkpoint_path: Path, config_path: Path) -> None:
    root.mkdir()
    write_csv_rows(
        root / "protected_runner_spec_rows.csv",
        [
            _runner_spec("runner-a"),
            _runner_spec("runner-b"),
        ],
    )
    write_csv_rows(
        root / "protected_workload_candidate_rows.csv",
        [
            _workload_candidate("runner-a", checkpoint_path, config_path),
            _workload_candidate("runner-b", checkpoint_path, config_path),
        ],
    )


def _write_m2700_source(root: Path, checkpoint_path: Path, config_path: Path) -> None:
    root.mkdir()
    write_csv_rows(
        root / "adapter_candidate_mapping_rows.csv",
        [
            _adapter_candidate("m2700-adapter-candidate-0001", "runner-a", checkpoint_path, config_path),
            _adapter_candidate("m2700-adapter-candidate-0002", "runner-b", checkpoint_path, config_path),
        ],
    )


def _write_m2703_source(root: Path, checkpoint_path: Path, config_path: Path) -> None:
    root.mkdir()
    write_csv_rows(
        root / "execution_admission_candidate_rows.csv",
        [
            _execution_candidate("m2703-execution-admission-candidate-0001", "runner-a", checkpoint_path, config_path),
            _execution_candidate("m2703-execution-admission-candidate-0002", "runner-b", checkpoint_path, config_path),
        ],
    )


def _support_candidate(support_id: str, runner_id: str, target_id: str) -> dict[str, object]:
    index = "0001" if runner_id == "runner-a" else "0002"
    return {
        "support_candidate_id": support_id,
        "execution_admission_candidate_id": f"m2703-execution-admission-candidate-{index}",
        "adapter_candidate_id": f"m2700-adapter-candidate-{index}",
        "workload_candidate_id": f"{runner_id}::L3_online_gru",
        "runner_spec_id": runner_id,
        "source_panel_spec_id": f"panel-{target_id}",
        "profile_name": "L3_online_gru",
        "policy_subject_id": "m2655_mitigation_preserving_policy",
        "protected_task_family": "route_a_protected",
        "protected_source_edge": f"unavoidable_mitigation|{target_id}",
        "execution_admission_status": "execution_admission_blocked_no_current_m1690_workload",
        "m1690_exact_workload_match": False,
        "m1690_reference_workload_id": "m1680-ref::L3_online_gru",
        "support_status": "support_materialized_candidate_requires_new_workload_row",
        "support_blocker_status": "support_blocker_new_workload_row_required",
        "candidate_requires_new_workload_row": True,
        "candidate_requires_simulator_fixture": True,
        "candidate_requires_runtime_adapter": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "protected_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
    }


def _support_blocker(blocker_id: str, support_id: str) -> dict[str, object]:
    return {
        "blocker_id": blocker_id,
        "support_candidate_id": support_id,
        "blocker_type": "support_blocker_new_workload_row_required",
        "blocker_reason": "execution-admission candidate has no exact current M1690 executable workload row",
        "required_follow_up": "materialize a current M1690 workload row and simulator fixture before protected execution admission",
        "actor_visible": False,
    }


def _support_trace(trace_id: str, support_id: str, runner_id: str, target_id: str) -> dict[str, object]:
    index = "0001" if runner_id == "runner-a" else "0002"
    return {
        "support_traceability_id": trace_id,
        "support_candidate_id": support_id,
        "execution_admission_candidate_id": f"m2703-execution-admission-candidate-{index}",
        "adapter_candidate_id": f"m2700-adapter-candidate-{index}",
        "workload_candidate_id": f"{runner_id}::L3_online_gru",
        "runner_spec_id": runner_id,
        "source_panel_spec_id": f"panel-{target_id}",
        "protected_target_id": target_id,
        "target_family": "protected_mitigation_preservation",
        "source_key": f"source-{target_id}",
        "traceability_axis": "scenario_role",
        "target_accounted": True,
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "actor_input_contract_changed": False,
        "materialization_only_no_execution": True,
        "diagnostic_only_no_verdict": True,
    }


def _runner_spec(runner_id: str) -> dict[str, object]:
    return {
        "runner_spec_id": runner_id,
        "source_panel_spec_id": f"panel-{runner_id}",
        "protected_task_family": "route_a_protected",
        "protected_source_edge": f"unavoidable_mitigation|{runner_id}",
        "base_fixture_id": "hf0_four_wheel_unavoidable_mitigation_fixture",
        "fixture_id": f"fixture-{runner_id}",
        "surface_id": "source_only_four_wheel_hf0",
        "fixture_variant_digest": f"fixture-digest-{runner_id}",
        "initial_state_digest": f"state-digest-{runner_id}",
        "fault_scale_digest": f"fault-digest-{runner_id}",
        "road_digest": f"road-digest-{runner_id}",
        "obstacle_digest": f"obstacle-digest-{runner_id}",
        "env_template_family": "hf0_four_wheel_unavoidable_mitigation_fixture",
        "runner_backend_family": "source_only_four_wheel_hf0",
        "actor_observation_shape": 72,
        "action_shape": 3,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "actor_input_contract_changed": False,
    }


def _workload_candidate(runner_id: str, checkpoint_path: Path, config_path: Path) -> dict[str, object]:
    return {
        "workload_candidate_id": f"{runner_id}::L3_online_gru",
        "runner_spec_id": runner_id,
        "profile_name": "L3_online_gru",
        "policy_subject_id": "m2655_mitigation_preserving_policy",
        "policy_checkpoint_path": str(checkpoint_path),
        "policy_checkpoint_exists": True,
        "reference_profile_config_path": str(config_path),
        "reference_profile_config_exists": True,
        "m1690_exact_workload_match": False,
        "m1690_reference_workload_id": "m1680-ref::L3_online_gru",
    }


def _adapter_candidate(adapter_id: str, runner_id: str, checkpoint_path: Path, config_path: Path) -> dict[str, object]:
    return {
        "adapter_candidate_id": adapter_id,
        "workload_candidate_id": f"{runner_id}::L3_online_gru",
        "runner_spec_id": runner_id,
        "policy_checkpoint_path": str(checkpoint_path),
        "policy_checkpoint_exists": True,
        "reference_profile_config_path": str(config_path),
        "reference_profile_config_exists": True,
        "adapter_backend_family": "source_only_four_wheel_hf0",
        "m1690_exact_workload_match": False,
    }


def _execution_candidate(candidate_id: str, runner_id: str, checkpoint_path: Path, config_path: Path) -> dict[str, object]:
    adapter_id = candidate_id.replace("m2703-execution-admission", "m2700-adapter")
    return {
        "execution_admission_candidate_id": candidate_id,
        "adapter_candidate_id": adapter_id,
        "workload_candidate_id": f"{runner_id}::L3_online_gru",
        "runner_spec_id": runner_id,
        "policy_checkpoint_path": str(checkpoint_path),
        "policy_checkpoint_exists": True,
        "reference_profile_config_path": str(config_path),
        "reference_profile_config_exists": True,
        "execution_admission_status": "execution_admission_blocked_no_current_m1690_workload",
        "m1690_exact_workload_match": False,
    }


def test_m2710_materializes_workload_fixture_support_without_execution(tmp_path: Path) -> None:
    m2706_dir = tmp_path / "m2706"
    m2697_dir = tmp_path / "m2697"
    m2700_dir = tmp_path / "m2700"
    m2703_dir = tmp_path / "m2703"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2710.md"
    m2708_synthesis = tmp_path / "m2708.md"
    m2709_design = tmp_path / "m2709.md"
    route_plan = tmp_path / "route.md"
    follow_up_manifest = tmp_path / "m2711.json"
    executable_specs = tmp_path / "specs.json"
    executable_workload = tmp_path / "workload.csv"
    checkpoint_path = tmp_path / "policy.pt"
    config_path = tmp_path / "profile.json"
    checkpoint_path.write_text("checkpoint\n", encoding="utf-8")
    config_path.write_text("{}\n", encoding="utf-8")
    m2708_synthesis.write_text("continue_to_current_m1690_workload_fixture_support_design\n", encoding="utf-8")
    m2709_design.write_text(
        "admit_current_m1690_workload_fixture_support_materialization_preflight\n",
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
                "task_family": "T4",
                "source_edge": "actuator_delay_step|capability_step_up",
                "window_tag": "reveal_plus_4",
                "executable_source_family": "capability_step_up",
                "env_template_family": "t4_capability_step_temporal",
                "strata": "task_family_T4",
                "profile_config_path": str(config_path),
                "checkpoint_path": str(checkpoint_path),
                "config_exists": True,
                "checkpoint_exists": True,
            }
        ],
    )
    _write_m2706_source(m2706_dir)
    _write_m2697_source(m2697_dir, checkpoint_path, config_path)
    _write_m2700_source(m2700_dir, checkpoint_path, config_path)
    _write_m2703_source(m2703_dir, checkpoint_path, config_path)

    summary = m2710.materialize_protected_runner_current_m1690_workload_fixture_support(
        m2706_dir=m2706_dir,
        m2708_synthesis=m2708_synthesis,
        m2709_design=m2709_design,
        m2697_dir=m2697_dir,
        m2700_dir=m2700_dir,
        m2703_dir=m2703_dir,
        executable_specs=executable_specs,
        executable_workload=executable_workload,
        route_plan=route_plan,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_protected_runner_current_m1690_workload_fixture_support_materialization_pass"
    )
    assert summary["workload_fixture_proposal_row_count"] == 2
    assert summary["exact_match_admission_row_count"] == 2
    assert summary["workload_fixture_support_blocker_row_count"] == 2
    assert summary["workload_fixture_traceability_row_count"] == 2
    assert summary["proposed_new_current_m1690_workload_row_count"] == 2
    assert summary["ready_existing_current_m1690_workload_row_count"] == 0
    assert summary["existing_exact_m1690_match_count"] == 0
    assert summary["fabricated_existing_m1690_match_count"] == 0
    assert summary["execution_admitted_row_count"] == 0
    assert summary["environment_reset_admitted_row_count"] == 0
    assert summary["proposals_cover_support_candidates"] is True
    assert summary["exact_match_rows_cover_proposals"] is True
    assert summary["no_fabricated_existing_m1690_matches"] is True
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

    source_rows = _read_csv(output_dir / "workload_fixture_input_source_rows.csv")
    proposal_rows = _read_csv(output_dir / "protected_workload_fixture_proposal_rows.csv")
    admission_rows = _read_csv(output_dir / "exact_match_admission_rows.csv")
    blocker_rows = _read_csv(output_dir / "workload_fixture_support_blocker_rows.csv")
    trace_rows = _read_csv(output_dir / "workload_fixture_traceability_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["source_exists"] for row in source_rows} == {"True"}
    assert {row["workload_fixture_support_status"] for row in proposal_rows} == {
        "workload_fixture_support_proposed_new_current_m1690_row"
    }
    assert {row["exact_existing_m1690_match"] for row in proposal_rows} == {"False"}
    assert {row["new_current_m1690_row_required"] for row in proposal_rows} == {"True"}
    assert {row["simulator_fixture_required"] for row in proposal_rows} == {"True"}
    assert {row["environment_reset_scheduled"] for row in proposal_rows} == {"False"}
    assert {row["environment_rollout_scheduled"] for row in proposal_rows} == {"False"}
    assert {row["measured_validation_scheduled"] for row in proposal_rows} == {"False"}
    assert {row["training_scheduled"] for row in proposal_rows} == {"False"}
    assert {row["exact_match_status"] for row in admission_rows} == {
        "proposed_new_current_m1690_workload_row_not_existing_match"
    }
    assert {row["execution_admitted"] for row in admission_rows} == {"False"}
    assert {row["environment_reset_admitted"] for row in admission_rows} == {"False"}
    assert {row["blocker_type"] for row in blocker_rows} == {
        "workload_fixture_support_blocker_existing_m1690_match_absent"
    }
    assert {row["protected_rows_in_success_denominator"] for row in proposal_rows + trace_rows} == {"False"}
    assert {row["protected_labels_actor_visible"] for row in proposal_rows + trace_rows} == {"False"}
    assert {row["protected_target_id"] for row in trace_rows} == {"target-a", "target-b"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {
        row["allowed_in_m2710"]
        for row in claim_rows
        if row["claim_family"] in {"driver_performance", "paper", "validation"}
    } == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
