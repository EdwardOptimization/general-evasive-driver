import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy import (
    materialize_readiness_index_after_protected_taxonomy,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2667_readiness_index_preserves_protected_boundary_and_route_a_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2667.md"
    follow_up_manifest = tmp_path / "m2668.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_readiness_index_after_protected_taxonomy(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "engineering_controller_route_a_baseline_readiness_index_after_protected_taxonomy_pass"
    )
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["route_a_required_artifact_count"] == 6
    assert summary["route_a_required_artifacts_covered"] == 6
    assert summary["route_a_artifact_coverage_complete"] is True
    assert summary["checkpoint_readiness_row_count"] == 3
    assert summary["protected_mitigation_blocker_preserved"] is True
    assert summary["protected_failure_blocking"] is True
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["all_policy_subjects_blocking"] is True
    assert summary["all_axes_blocking"] is True
    assert summary["all_metrics_blocking"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["admitted_next_action_count"] == 1
    assert summary["selected_next_action"] == "m2668_route_a_baseline_readiness_index_result_audit"
    assert summary["validation_readiness_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["full_ideal_driver_gate_passed"] is False

    checkpoint_rows = _read_csv(output_dir / "checkpoint_readiness_rows.csv")
    artifact_rows = _read_csv(output_dir / "artifact_coverage_rows.csv")
    failure_rows = _read_csv(output_dir / "known_failure_boundary_rows.csv")
    next_rows = _read_csv(output_dir / "next_action_admission_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["readiness_status"] for row in checkpoint_rows} == {
        "diagnostic_ready_blocked_by_protected_mitigation"
    }
    assert {row["actor_contract_shape_72_action_3"] for row in checkpoint_rows} == {"True"}
    assert {row["protected_blocker_present"] for row in checkpoint_rows} == {"True"}
    assert {row["source_exists"] for row in checkpoint_rows} == {"True"}

    required_artifacts = {row["route_a_requirement"] for row in artifact_rows if row["route_a_required"] == "True"}
    assert required_artifacts == {
        "baseline checkpoint list",
        "actor input/output contract",
        "public benchmark pack",
        "runtime/inference-cost report",
        "scenario-role metric report",
        "known failure taxonomy",
    }
    assert {row["coverage_status"] for row in artifact_rows if row["route_a_required"] == "True"} == {
        "covered_current"
    }

    assert len(failure_rows) == 10
    assert {row["protected_blocker_preserved"] for row in failure_rows} == {"True"}
    assert {row["protected_rows_in_success_denominator"] for row in failure_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in failure_rows} == {"False"}
    assert {
        "m2667_known_failure_metric_minimum_obstacle_clearance_m",
        "m2667_known_failure_metric_obstacle_penetration_proxy_m",
        "m2667_known_failure_metric_severity_proxy",
    }.issubset({row["boundary_id"] for row in failure_rows})

    admitted = [row for row in next_rows if row["admission_status"] == "admitted"]
    assert len(admitted) == 1
    assert admitted[0]["candidate_action_id"] == "m2668_route_a_baseline_readiness_index_result_audit"
    assert {
        row["admission_status"] for row in next_rows if row["candidate_action_id"] != admitted[0]["candidate_action_id"]
    } == {"defer_until_m2668_audit", "not_admitted"}

    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2667"] == "True"}
    assert allowed_claims == {
        "route_a_readiness_index_materialized",
        "route_a_artifact_coverage_indexed",
        "baseline_checkpoint_contract_indexed",
        "protected_failure_boundary_indexed",
        "follow_up_result_audit_registered",
    }
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
