from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_source_only_belief_stress_training_admission_pack_materialization import (
    STRESS_FAMILY_BY_CONDITION,
    classify_belief_signal,
    materialize_source_only_belief_stress_training_admission_pack,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2779_materializes_complete_source_only_admission_pack_from_live_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    doc = tmp_path / "m2779.md"
    follow_up = tmp_path / "m2780.json"

    summary = materialize_source_only_belief_stress_training_admission_pack(
        output_dir,
        follow_up_manifest=follow_up,
        doc_path=doc,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["source_delta_row_count"] == 96
    assert summary["ordinary_delta_row_count"] == 72
    assert summary["mitigation_reference_delta_row_count"] == 24
    assert summary["source_candidate_row_count"] == 32
    assert summary["ordinary_candidate_row_count"] == 24
    assert summary["mitigation_reference_candidate_row_count"] == 8
    assert summary["intervention_condition_count"] == 3
    assert summary["admission_row_count"] == 96
    assert summary["stress_curriculum_row_count"] == 24
    assert summary["m2773_intervention_execution_row_count"] == 128
    assert summary["m2773_action_response_trace_row_count"] == 10240
    assert summary["m2773_collision_diagnostic_row_count"] == 32
    assert summary["m2773_road_departure_diagnostic_row_count"] == 68
    assert summary["m2775_matched_trace_pair_row_count"] == 7680
    assert summary["m2775_road_departure_removed_delta_row_count"] == 4
    assert summary["m2775_road_departure_added_delta_row_count"] == 0
    assert summary["m2775_collision_changed_delta_row_count"] == 0
    assert summary["behavior_outcome_sensitive_count"] == 4
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["actor_visible_label_detected"] is False
    assert summary["actor_visible_stress_admission_curriculum_labels_detected"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["new_execution_run"] is False
    assert summary["training_run"] is False
    assert summary["ppo_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_verdict_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    admission_rows = _read_csv(output_dir / "belief_stress_admission_rows.csv")
    assert len(admission_rows) == 96
    assert {row["stress_family"] for row in admission_rows} == set(STRESS_FAMILY_BY_CONDITION.values())
    assert {row["diagnostic_only"] for row in admission_rows} == {"True"}
    assert {row["ranking_admissible"] for row in admission_rows} == {"False"}
    assert {row["winner_selected"] for row in admission_rows} == {"False"}
    assert {row["actor_visible_label"] for row in admission_rows} == {"False"}
    behavior_rows = [row for row in admission_rows if row["belief_signal_class"] == "behavior_outcome_sensitive"]
    assert len(behavior_rows) == 4
    assert {row["road_departure_removed"] for row in behavior_rows} == {"True"}
    mitigation_rows = [row for row in admission_rows if row["mitigation_reference"] == "True"]
    assert len(mitigation_rows) == 24
    assert {row["belief_signal_class"] for row in mitigation_rows} == {"weak_or_context"}
    assert {row["admission_action"] for row in mitigation_rows} == {"mitigation_reference_guard"}
    assert {row["future_training_allowed"] for row in mitigation_rows} == {"False"}
    assert {row["future_execution_allowed"] for row in mitigation_rows} == {"False"}

    curriculum_rows = _read_csv(output_dir / "stress_curriculum_rows.csv")
    assert len(curriculum_rows) == 24
    assert sum(int(row["ordinary_candidate_count"]) for row in curriculum_rows) == 72
    assert sum(int(row["mitigation_reference_count"]) for row in curriculum_rows) == 24
    assert {row["ranking_admissible"] for row in curriculum_rows} == {"False"}

    guard_rows = _read_csv(output_dir / "mitigation_reference_guard_rows.csv")
    assert len(guard_rows) == 8
    assert {row["ordinary_denominator_allowed"] for row in guard_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in guard_rows} == {"False"}
    assert {row["future_training_allowed"] for row in guard_rows} == {"False"}
    assert {row["future_execution_allowed"] for row in guard_rows} == {"False"}
    assert {row["admission_row_count"] for row in guard_rows} == {"3"}

    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    assert len(actor_rows) == 7
    assert {row["actor_observation_shape"] for row in actor_rows} == {"72"}
    assert {row["action_shape"] for row in actor_rows} == {"3"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}

    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert gate_rows
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert follow_up.exists()
    assert read_json(follow_up)["id"].startswith("m2780-")
    assert doc.exists()


def test_m2779_belief_signal_classification_is_deterministic() -> None:
    assert classify_belief_signal({"mitigation_reference": True, "road_departure_removed": True}) == "weak_or_context"
    assert classify_belief_signal({"road_departure_removed": True}) == "behavior_outcome_sensitive"
    assert classify_belief_signal({"collision_delta": 1}) == "behavior_outcome_sensitive"
    assert classify_belief_signal({"action_l1_mean": 0.03}) == "action_response_sensitive"
    assert classify_belief_signal({"ego_response_l2_mean": 0.10}) == "action_response_sensitive"
    assert classify_belief_signal({"trace_delta_proxy_delta": -1.0}) == "trace_sensitive"
    assert classify_belief_signal({"command_response_proxy_delta": 0.04}) == "trace_sensitive"
    assert classify_belief_signal({"action_l1_mean": 0.01}) == "weak_or_context"
