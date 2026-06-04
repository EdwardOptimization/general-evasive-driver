import csv
from pathlib import Path

from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.paper_route_history_vs_current_response_comparison_protocol_materialization import (
    REQUIRED_CONTROLLER_IDS,
    REQUIRED_TASK_IDS,
    build_claim_boundary_rows,
    build_controller_family_rows,
    build_fairness_gate_rows,
    build_task_family_rows,
    materialize_protocol_pack,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2671_protocol_builders_preserve_fair_comparison_controls():
    controller_rows = build_controller_family_rows()
    task_rows = build_task_family_rows()
    fairness_rows = build_fairness_gate_rows()
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=True)

    assert {row["controller_family_id"] for row in controller_rows} == REQUIRED_CONTROLLER_IDS
    assert {row["task_family_id"] for row in task_rows} == REQUIRED_TASK_IDS
    assert {row["actor_contract_shape_72_action_3"] for row in controller_rows} == {True}
    assert {row["observation_shape"] for row in controller_rows} == {P0_OBSERVATION_DIM}
    assert {row["action_shape"] for row in controller_rows} == {ACTION_DIM}
    assert {row["hidden_oracle_actor_input_allowed"] for row in controller_rows} == {False}

    controls = {row["controller_family_id"]: row for row in controller_rows}
    assert controls["L2-current-tiled"]["current_tiled_control"] is True
    assert controls["L3-reset-truncated-control"]["reset_or_truncated_control"] is True
    assert controls["L3-online-GRU"]["uses_online_recurrent_state"] is True

    fairness_gate_ids = {row["gate_id"] for row in fairness_rows}
    assert {
        "same_actor_boundary",
        "same_action_contract",
        "no_private_holdout_tuning",
        "current_tiled_runtime_transform_enforced",
        "reset_truncated_runtime_semantics_enforced",
        "claim_boundary_blocks_protocol_overclaim",
    }.issubset(fairness_gate_ids)
    assert {row["status_pass"] for row in fairness_rows} == {True}

    allowed_claims = {row["claim_id"] for row in claim_rows if row["allowed_in_m2671"]}
    assert allowed_claims == {
        "protocol_materialization",
        "controller_family_rows_materialized",
        "task_family_rows_materialized",
        "fairness_gate_rows_materialized",
        "claim_boundary_rows_materialized",
        "follow_up_audit_registered",
    }
    assert {row["allowed_in_m2671"] for row in claim_rows if row["claim_id"] == "finite_window_vs_gru_result"} == {
        False
    }
    assert {row["allowed_in_m2671"] for row in claim_rows if row["claim_id"] == "level3_self_identification"} == {
        False
    }


def test_m2671_protocol_materialization_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2671.md"
    follow_up_manifest = tmp_path / "m2672.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_protocol_pack(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "paper_route_history_vs_current_response_comparison_protocol_materialization_pass"
    assert summary["protocol_materialization_only"] is True
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["controller_family_row_count"] == 9
    assert summary["required_controller_families_present"] is True
    assert summary["task_family_row_count"] == 5
    assert summary["required_task_families_present"] is True
    assert summary["fairness_gate_row_count"] >= 15
    assert summary["claim_boundary_row_count"] >= 20
    assert summary["gate_matrix_pass"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["private_holdout_used"] is False
    assert summary["current_tiled_control_present"] is True
    assert summary["reset_truncated_control_present"] is True
    assert summary["training_run"] is False
    assert summary["ppo_run"] is False
    assert summary["ranking_run"] is False
    assert summary["success_rate_computed"] is False
    assert summary["finite_window_vs_gru_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False
    assert summary["selected_next_action"] == (
        "m2672-paper-route-history-vs-current-response-comparison-protocol-materialization-result-audit"
    )

    controller_rows = _read_csv(output_dir / "controller_family_rows.csv")
    task_rows = _read_csv(output_dir / "task_family_rows.csv")
    fairness_rows = _read_csv(output_dir / "fairness_gate_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["controller_family_id"] for row in controller_rows} == REQUIRED_CONTROLLER_IDS
    assert {row["task_family_id"] for row in task_rows} == REQUIRED_TASK_IDS
    assert {row["hidden_oracle_actor_input_allowed"] for row in controller_rows} == {"False"}
    assert {row["actor_visible_labels_allowed"] for row in task_rows} == {"False"}
    assert {row["status_pass"] for row in fairness_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert "L2-current-tiled" in {row["controller_family_id"] for row in controller_rows}
    assert "L3-reset-truncated-control" in {row["controller_family_id"] for row in controller_rows}

    allowed_claims = {row["claim_id"] for row in claim_rows if row["allowed_in_m2671"] == "True"}
    assert "follow_up_audit_registered" in allowed_claims
    assert {row["allowed_in_m2671"] for row in claim_rows if row["claim_id"] == "driver_performance"} == {
        "False"
    }
    assert {row["allowed_in_m2671"] for row in claim_rows if row["claim_id"] == "paper_level_evidence"} == {
        "False"
    }
    assert doc_path.read_text(encoding="utf-8").strip()
