from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter as adapter
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _write_source(tmp_path: Path, *, source_result_class: str | None = None) -> Path:
    source = tmp_path / "source"
    overlay_dir = source / "repair_candidate_overlays"
    overlay_dir.mkdir(parents=True)
    overlay_rows: list[dict[str, Any]] = []
    guardrail_rows: list[dict[str, Any]] = []
    guardrail_specs = [
        ("collision_non_regression", 3, False),
        ("r4_mitigation_semantics", 4, False),
        ("max_step_noncompletion", 1, False),
        ("speed_too_low", 1, False),
        ("diagnostic_monitoring", 10, True),
        ("source_linked_family_membership_diagnostic", 2, True),
    ]
    for idx in range(2):
        cid = f"c0{idx + 1}_candidate"
        overlay_path = overlay_dir / f"{cid}.json"
        payload = {
            "candidate_id": cid,
            "candidate_family": "source_linked_test_family",
            "artifact_only": True,
            "run_dir_only": True,
            "source_linked": True,
            "active_config_overwrite": False,
            "repair_execution_allowed": False,
            "training_allowed": False,
            "ranking_admissible": False,
            "winner_selected": False,
            "source_lever_families": ["test"],
            "source_plan_row_count": 2,
            "source_row_keys": ["a", "b"],
            "candidate_levers": ["test lever"],
            "acceptance_gates": "test gate",
            "stop_rules": "test stop",
            "guardrails": {
                "collision_guardrail_source_count": 3,
                "r4_mitigation_source_count": 4,
                "max_step_noncompletion_source_count": 1,
                "speed_too_low_source_count": 1,
                "diagnostic_monitoring_source_count": 10,
                "family_membership_diagnostic_source_count": 2,
                "diagnostic_rows_monitoring_only": True,
                "family_rows_monitoring_only": True,
                "source_linked_family_ranking_allowed": False,
                "support_policy_ranking_allowed": False,
                "actor_input_contract_changed": False,
                "hidden_oracle_feature_injection": False,
            },
        }
        write_json(overlay_path, payload)
        overlay_rows.append(
            {
                "candidate_id": cid,
                "candidate_family": "source_linked_test_family",
                "source_lever_families": "test",
                "source_plan_row_count": 2,
                "with_collision_guardrail_count": 1,
                "mean_offtrack_rate": 0.8,
                "mean_collision_rate": 0.1,
                "mean_max_step_noncompletion_rate": 0.0,
                "mean_speed_too_low_rate": 0.0,
                "collision_guardrail_source_count": 3,
                "r4_mitigation_source_count": 4,
                "max_step_source_count": 1,
                "speed_too_low_source_count": 1,
                "diagnostic_monitoring_source_count": 10,
                "family_membership_diagnostic_source_count": 2,
                "overlay_path": str(overlay_path),
                "run_dir_only": True,
                "active_config_overwrite": False,
                "repair_execution_allowed": False,
                "training_allowed": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "guardrail_metadata_attached": True,
                "diagnostic_rows_monitoring_only": True,
                "family_rows_monitoring_only": True,
                "candidate_levers": "test",
                "acceptance_gates": "test",
                "stop_rules": "test",
            }
        )
        for guardrail_type, count, monitoring_only in guardrail_specs:
            artifact_ref = source / f"{guardrail_type}.csv"
            write_csv_rows(artifact_ref, [{"ok": True}])
            guardrail_rows.append(
                {
                    "candidate_id": cid,
                    "guardrail_type": guardrail_type,
                    "source_row_count": count,
                    "required_gate": "gate",
                    "artifact_ref": str(artifact_ref),
                    "monitoring_only": monitoring_only,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
    write_json(
        source / "summary.json",
        {
            "result_class": source_result_class
            or "current_sim_dual_axis_source_linked_repair_candidate_materialization_pass"
        },
    )
    write_csv_rows(source / "repair_candidate_overlays.csv", overlay_rows)
    write_csv_rows(source / "candidate_guardrail_metadata.csv", guardrail_rows)
    write_csv_rows(
        source / "claim_boundary.csv",
        [
            {
                "claim": "artifact_only_source_linked_repair_candidate_materialization",
                "admissible": True,
                "reason": "allowed",
            },
            {"claim": "active_config_overwrite", "admissible": False, "reason": "blocked"},
            {"claim": "repair_execution", "admissible": False, "reason": "blocked"},
            {"claim": "scenario_redesign_executed", "admissible": False, "reason": "blocked"},
            {"claim": "training_repair_success", "admissible": False, "reason": "blocked"},
            {"claim": "source_linked_family_ranking", "admissible": False, "reason": "blocked"},
            {"claim": "support_policy_ranking", "admissible": False, "reason": "blocked"},
            {"claim": "candidate_ranking", "admissible": False, "reason": "blocked"},
            {"claim": "current_sim_verdict", "admissible": False, "reason": "blocked"},
        ],
    )
    return source


def test_source_linked_candidate_reset_load_validation_adapter_passes_clean_source(tmp_path: Path) -> None:
    source = _write_source(tmp_path)

    summary = adapter.run_source_linked_candidate_reset_load_validation_adapter(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_count=2,
    )

    assert summary["result_class"] == adapter.RESULT_PASS
    assert summary["candidate_count"] == 2
    assert summary["overlay_load_pass_count"] == 2
    assert summary["overlay_schema_failure_count"] == 0
    assert summary["table_payload_mismatch_count"] == 0
    assert summary["source_row_key_count_mismatch_count"] == 0
    assert summary["guardrail_metadata_row_count"] == 12
    assert summary["guardrail_metadata_failure_count"] == 0
    assert summary["diagnostic_family_metadata_failure_count"] == 0
    assert summary["claim_boundary_failure_count"] == 0
    assert summary["active_config_overwrite_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["guardrail_violation_count"] == 0

    rows = adapter.read_csv_rows(tmp_path / "out" / "candidate_validation_rows.csv")
    assert all(row["overlay_under_run_dir"] == "True" for row in rows)
    assert all(row["source_linked"] == "True" for row in rows)
    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == adapter.RESULT_PASS


def test_source_linked_candidate_reset_load_validation_adapter_fails_closed_on_source_failure(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        source_result_class="current_sim_dual_axis_source_linked_repair_candidate_materialization_incomplete_or_fail",
    )

    summary = adapter.run_source_linked_candidate_reset_load_validation_adapter(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_count=2,
    )

    assert summary["result_class"] == adapter.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")


def test_source_linked_candidate_reset_load_validation_adapter_fails_on_missing_guardrail_ref(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    rows = adapter.read_csv_rows(source / "candidate_guardrail_metadata.csv")
    rows[0]["artifact_ref"] = str(source / "missing.csv")
    write_csv_rows(source / "candidate_guardrail_metadata.csv", rows)

    summary = adapter.run_source_linked_candidate_reset_load_validation_adapter(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_count=2,
    )

    assert summary["result_class"] == adapter.RESULT_FAIL
    assert summary["guardrail_metadata_failure_count"] == 1


def test_source_linked_candidate_reset_load_validation_adapter_fails_on_schema_mismatch(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    first = next((source / "repair_candidate_overlays").glob("*.json"))
    payload = read_json(first)
    payload.pop("source_row_keys")
    write_json(first, payload)

    summary = adapter.run_source_linked_candidate_reset_load_validation_adapter(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_count=2,
    )

    assert summary["result_class"] == adapter.RESULT_FAIL
    assert summary["overlay_schema_failure_count"] == 1


def test_source_linked_candidate_reset_load_validation_adapter_fails_on_family_ranking_leak(
    tmp_path: Path,
) -> None:
    source = _write_source(tmp_path)
    first = next((source / "repair_candidate_overlays").glob("*.json"))
    payload = read_json(first)
    payload["guardrails"]["source_linked_family_ranking_allowed"] = True
    write_json(first, payload)

    summary = adapter.run_source_linked_candidate_reset_load_validation_adapter(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_count=2,
    )

    assert summary["result_class"] == adapter.RESULT_FAIL
    assert summary["diagnostic_family_metadata_failure_count"] == 1
