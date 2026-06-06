from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.engineering_controller_route_a_dependency_facing_evidence_surface_execution_admission_materialization_preflight import (
    ADMITTED_STATUS,
    BLOCKED_STALE_STATUS,
    DECISION_FAIL,
    DECISION_PASS,
    NEXT_ID,
    materialize_dependency_facing_execution_admission,
    route_a_source_specs,
)
from autodrift.engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight import (
    write_preflight_artifacts as write_m2913_artifacts,
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_parent_docs(tmp_path: Path) -> dict[str, Path]:
    docs = {
        "m2912_design": tmp_path / "docs" / "m2912.md",
        "m2911_synthesis": tmp_path / "docs" / "m2911.md",
        "m2910_synthesis": tmp_path / "docs" / "m2910.md",
        "m2879_synthesis": tmp_path / "docs" / "m2879.md",
        "m2883_design": tmp_path / "docs" / "m2883.md",
    }
    for name, path in docs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{name} fixture\n", encoding="utf-8")
    return docs


def _write_m2913_fixture(tmp_path: Path) -> Path:
    docs = _write_parent_docs(tmp_path)
    m2913_dir = tmp_path / "runs" / "m2913"
    write_m2913_artifacts(
        output_dir=m2913_dir,
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2914.json",
        **docs,
    )
    return m2913_dir


def _source_row(source_key: str, index: int) -> dict[str, object]:
    spec = route_a_source_specs()[source_key]
    milestone = spec["milestone"]
    return {
        "candidate_id": f"{milestone}-candidate-{index:04d}",
        "resolution_id": f"{milestone}-resolution-{index:04d}",
        "source_milestone": milestone,
        "source_family": f"{milestone}-source-family",
        "source_family_tag": f"{milestone}-source-tag",
        "source_key": f"{milestone}-source-key-{index:04d}",
        "workload_id": f"workload-{index:04d}",
        "task_source_id": f"task-{index:04d}",
        "task_family": "T4" if index % 2 else "T5",
        "profile_name": "L3_online_gru",
        "checkpoint_path": "checkpoint.pt",
        "profile_config_path": "profile.json",
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "route_labels_actor_visible": False,
        "source_edge_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "guardrail_rows_in_success_denominator": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "level3_self_id_claim_made": False,
        "diagnostic_only_no_verdict": True,
    }


def _write_source_csvs(tmp_path: Path, *, omit_key: str | None = None) -> dict[str, Path]:
    overrides: dict[str, Path] = {}
    for source_key, spec in route_a_source_specs().items():
        path = tmp_path / "sources" / f"{source_key}.csv"
        overrides[source_key] = path
        if source_key == omit_key:
            continue
        rows = [
            _source_row(source_key, index)
            for index in range(1, int(spec["expected_row_count"]) + 1)
        ]
        write_csv_rows(path, rows)
    return overrides


def test_m2916_materializes_no_execution_admission_rows(tmp_path: Path) -> None:
    m2913_dir = _write_m2913_fixture(tmp_path)
    source_overrides = _write_source_csvs(tmp_path)
    m2914_audit = tmp_path / "docs" / "m2914.md"
    m2915_design = tmp_path / "docs" / "m2915.md"
    m2914_audit.write_text(
        "accept_m2913_dependency_facing_evidence_surface_materialization_claim_safe_route_to_m2915_execution_design\n",
        encoding="utf-8",
    )
    m2915_design.write_text(
        "admit_m2916_dependency_facing_execution_admission_materialization_preflight\n",
        encoding="utf-8",
    )

    summary = materialize_dependency_facing_execution_admission(
        m2913_dir=m2913_dir,
        m2914_audit=m2914_audit,
        m2915_design=m2915_design,
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "docs" / "m2916.md",
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2917.json",
        source_overrides=source_overrides,
    )

    assert summary["status_pass"] is True
    assert summary["decision"] == DECISION_PASS
    assert summary["execution_admission_source_row_count"] == 67
    assert summary["execution_admission_candidate_row_count"] == 67
    assert summary["execution_admission_admitted_count"] == 56
    assert summary["execution_admission_blocked_stale_fixed_surface_count"] == 11
    assert summary["execution_admission_rejection_row_count"] == 11
    assert summary["m2877_guard_row_count"] == 11
    assert summary["reset_or_rollout_executed"] is False
    assert summary["validation_executed"] is False
    assert summary["training_executed"] is False
    assert summary["dependency_execution_performed"] is False
    assert summary["performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["self_id_claim_made"] is False
    assert read_json(tmp_path / "out" / "summary.json") == summary
    assert read_json(tmp_path / "experiments" / "manifests" / "m2917.json")["id"] == NEXT_ID

    candidate_rows = _read_rows(tmp_path / "out" / "execution_admission_candidate_rows.csv")
    rejection_rows = _read_rows(tmp_path / "out" / "execution_admission_rejection_rows.csv")
    guard_rows = _read_rows(tmp_path / "out" / "guardrail_context_rows.csv")
    actor_rows = _read_rows(tmp_path / "out" / "actor_contract_guard_rows.csv")
    claim_rows = _read_rows(tmp_path / "out" / "claim_boundary_rows.csv")
    gate_rows = _read_rows(tmp_path / "out" / "gate_matrix.csv")

    assert {ADMITTED_STATUS, BLOCKED_STALE_STATUS} <= {
        row["execution_admission_status"] for row in candidate_rows
    }
    assert {row["environment_reset_admitted"] for row in candidate_rows} == {"False"}
    assert {row["environment_rollout_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["measured_validation_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["dependency_execution_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["paper_denominator_allowed"] for row in candidate_rows} == {"False"}
    assert {row["high_fidelity_readiness_allowed"] for row in candidate_rows} == {"False"}
    assert {row["self_id_claim_allowed"] for row in candidate_rows} == {"False"}
    assert {row["rejection_type"] for row in rejection_rows} == {BLOCKED_STALE_STATUS}
    assert any(row["guardrail_family"] == "route_b_context_only" for row in guard_rows)
    assert any(row["guardrail_family"] == "route_c_dependency_context_only" for row in guard_rows)
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {row["claim_made"] for row in claim_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}


def test_m2916_fails_closed_when_required_source_missing(tmp_path: Path) -> None:
    m2913_dir = _write_m2913_fixture(tmp_path)
    source_overrides = _write_source_csvs(tmp_path, omit_key="m2746_candidate_execution_rows")
    m2914_audit = tmp_path / "docs" / "m2914.md"
    m2915_design = tmp_path / "docs" / "m2915.md"
    m2914_audit.write_text(
        "accept_m2913_dependency_facing_evidence_surface_materialization_claim_safe_route_to_m2915_execution_design\n",
        encoding="utf-8",
    )
    m2915_design.write_text(
        "admit_m2916_dependency_facing_execution_admission_materialization_preflight\n",
        encoding="utf-8",
    )

    summary = materialize_dependency_facing_execution_admission(
        m2913_dir=m2913_dir,
        m2914_audit=m2914_audit,
        m2915_design=m2915_design,
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "docs" / "m2916.md",
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2917.json",
        source_overrides=source_overrides,
    )

    assert summary["status_pass"] is False
    assert summary["decision"] == DECISION_FAIL
    assert summary["route_a_source_artifact_missing_count"] == 1
    rejection_rows = _read_rows(tmp_path / "out" / "execution_admission_rejection_rows.csv")
    assert any(
        row["candidate_or_source_id"] == "m2746_candidate_execution_rows"
        and row["rejection_type"] == "execution_admission_rejected_source_artifact_missing"
        for row in rejection_rows
    )
    gate_rows = _read_rows(tmp_path / "out" / "gate_matrix.csv")
    missing_gate = [row for row in gate_rows if row["gate_family"] == "route_a_source_inventory_exists"][0]
    assert missing_gate["status_pass"] == "False"
