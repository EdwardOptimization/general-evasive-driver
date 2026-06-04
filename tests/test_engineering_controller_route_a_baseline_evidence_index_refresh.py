import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_baseline_evidence_index_refresh import (
    run_route_a_baseline_evidence_index_refresh,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_route_a_baseline_evidence_index_refresh_materializes_gap_and_admission_panel(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2639.md"

    summary = run_route_a_baseline_evidence_index_refresh(output_dir, doc_path=doc_path)

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_route_a_baseline_evidence_index_refresh_pass"
    assert summary["source_artifacts_present"] is True
    assert summary["required_artifacts_present"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["observation_shape"] == 72
    assert summary["action_shape"] == 3
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["hf3_source_dependency_paused"] is True
    assert summary["hf3_availability_blocker"] == "dependency_source_unavailable"
    assert summary["admitted_next_action_count"] == 1
    assert (
        summary["selected_next_action"]
        == "m2640_route_a_source_only_fresh_generalization_panel_design"
    )
    assert summary["policy_action_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False

    evidence_rows = _read_csv(output_dir / "evidence_index.csv")
    gap_rows = _read_csv(output_dir / "gap_matrix.csv")
    next_rows = _read_csv(output_dir / "next_action_admission.csv")
    artifact_rows = _read_csv(output_dir / "artifact_manifest.csv")

    assert {
        "m2541_baseline_checkpoint_list",
        "m2544_source_only_readiness_panel",
        "m2505_public_benchmark_pack",
        "m2548_hf0_parity_runtime",
        "m2638_hf3_source_dependency_blocker",
    }.issubset({row["evidence_id"] for row in evidence_rows})
    assert {row["hidden_oracle_actor_input_detected"] for row in evidence_rows} == {"False"}
    assert {row["source_exists"] for row in evidence_rows} == {"True"}

    hf3_gap = {
        row["gap_id"]: row for row in gap_rows
    }["hf3_selected_platform_source_dependency"]
    assert hf3_gap["current_status"] == "blocked"
    assert hf3_gap["admission_to_next_action"] == "not_admitted_until_source_supplied"

    admitted = [row for row in next_rows if row["admission_status"] == "admitted"]
    assert len(admitted) == 1
    assert admitted[0]["candidate_action_id"] == "m2640_route_a_source_only_fresh_generalization_panel_design"

    assert {row["exists"] for row in artifact_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
