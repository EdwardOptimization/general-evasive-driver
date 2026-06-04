import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_history_vs_current_response_comparison_protocol_materialization import (
    REQUIRED_CONTROLLER_IDS,
)
from autodrift.paper_route_history_vs_current_response_runtime_enforcement_materialization import (
    build_claim_boundary_rows,
    build_protocol_to_runtime_profile_rows,
    materialize_runtime_enforcement,
    read_protocol_controller_rows,
    runtime_profile_specs,
)


PROTOCOL_DIR = Path("runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization")


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2673_runtime_mapping_covers_required_protocol_controller_families() -> None:
    protocol_rows = read_protocol_controller_rows(PROTOCOL_DIR / "controller_family_rows.csv")
    runtime_rows = build_protocol_to_runtime_profile_rows(protocol_rows, seed=2673)

    assert len(runtime_rows) == len(runtime_profile_specs())
    assert {row["protocol_controller_family_id"] for row in runtime_rows} == REQUIRED_CONTROLLER_IDS
    assert {row["runtime_enforcement_status_pass"] for row in runtime_rows} == {True}
    assert {row["hidden_oracle_actor_input_detected"] for row in runtime_rows} == {False}
    assert {row["policy_rollout_run"] for row in runtime_rows} == {False}
    assert {row["success_rate_computed"] for row in runtime_rows} == {False}

    tiled_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L2-current-tiled"]
    assert len(tiled_rows) == 4
    assert {row["history_transform"] for row in tiled_rows} == {"current_tiled"}
    assert {row["current_tiled_runtime_observed"] for row in tiled_rows} == {True}

    reset_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L3-reset-truncated-control"]
    assert len(reset_rows) == 1
    assert reset_rows[0]["reset_hidden_policy"] == "every_step_control"
    assert reset_rows[0]["reset_policy_routing_ok"] is True


def test_m2673_claim_boundary_blocks_result_claims() -> None:
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=True)
    allowed_claims = {row["claim_id"] for row in claim_rows if row["allowed_in_m2673"]}

    assert allowed_claims == {
        "runtime_enforcement_materialization",
        "protocol_to_runtime_profile_rows_materialized",
        "runtime_enforcement_gate_rows_materialized",
        "claim_boundary_rows_materialized",
        "gate_matrix_materialized",
        "follow_up_audit_registered",
    }
    assert {row["allowed_in_m2673"] for row in claim_rows if row["claim_id"] == "finite_window_vs_gru_result"} == {
        False
    }
    assert {row["allowed_in_m2673"] for row in claim_rows if row["claim_id"] == "level3_self_identification"} == {
        False
    }


def test_m2673_runtime_enforcement_materialization_writes_expected_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2673.md"
    follow_up_manifest = tmp_path / "m2674.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_runtime_enforcement(
        PROTOCOL_DIR,
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        seed=2673,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "paper_route_history_vs_current_response_runtime_enforcement_materialization_pass"
    )
    assert summary["m2671_status_pass"] is True
    assert summary["runtime_profile_row_count"] == 12
    assert summary["runtime_profile_mapping_count"] == 9
    assert summary["required_protocol_ids_runtime_mapped"] is True
    assert summary["current_tiled_runtime_profile_count"] == 4
    assert summary["current_tiled_runtime_observed"] is True
    assert summary["reset_truncated_policy_routing_ok"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["private_holdout_used"] is False
    assert summary["environment_reset_run"] is True
    assert summary["environment_step_run"] is True
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ppo_run"] is False
    assert summary["success_rate_computed"] is False
    assert summary["finite_window_vs_gru_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False
    assert summary["selected_next_action"] == (
        "m2674-paper-route-history-vs-current-response-runtime-enforcement-materialization-result-audit"
    )

    runtime_rows = _read_csv(output_dir / "protocol_to_runtime_profile_rows.csv")
    runtime_gate_rows = _read_csv(output_dir / "runtime_enforcement_gate_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["protocol_controller_family_id"] for row in runtime_rows} == REQUIRED_CONTROLLER_IDS
    assert {row["runtime_enforcement_status_pass"] for row in runtime_rows} == {"True"}
    assert {row["status_pass"] for row in runtime_gate_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["allowed_in_m2673"] for row in claim_rows if row["claim_id"] == "driver_performance"} == {
        "False"
    }
    assert {row["allowed_in_m2673"] for row in claim_rows if row["claim_id"] == "paper_level_evidence"} == {
        "False"
    }
    assert read_json(output_dir / "summary.json") == summary
    assert doc_path.read_text(encoding="utf-8").strip()
