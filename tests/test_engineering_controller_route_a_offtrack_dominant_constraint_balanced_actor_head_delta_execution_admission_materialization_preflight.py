from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_execution_admission_materialization_preflight
    as m2956,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2953_fixture(root: Path) -> Path:
    m2953_dir = root / "m2953"
    m2953_dir.mkdir()
    write_json(m2953_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(
        m2953_dir / "panel_spec_rows.csv",
        [
            {
                "panel_spec_id": f"m2953-panel-spec-{index:04d}",
                "source_family": f"source_family_{index}",
                "materialization_admitted": True,
                "evaluator_label_actor_visible": False,
                "verdict_label_actor_visible": False,
            }
            for index in range(1, 9)
        ],
    )
    write_csv_rows(
        m2953_dir / "contract_traceability_rows.csv",
        [
            {
                "trace_id": f"m2953-trace-{index:04d}",
                "status_pass": True,
                "actor_visible": False,
            }
            for index in range(1, 89)
        ],
    )
    write_csv_rows(
        m2953_dir / "actor_contract_guard_rows.csv",
        [
            {
                "guard_id": f"m2953-actor-guard-{index:04d}",
                "contract_field": field,
                "observed_value": observed,
                "expected_value": expected,
                "status_pass": True,
                "actor_visible_allowed": actor_visible,
            }
            for index, (field, observed, expected, actor_visible) in enumerate(
                [
                    ("actor_observation_dim", 72, 72, True),
                    ("action_dim", 3, 3, True),
                    ("hidden_oracle_actor_input_required", False, False, False),
                    ("future_target_actor_input_required", False, False, False),
                ],
                1,
            )
        ],
    )
    write_csv_rows(
        m2953_dir / "side_effect_guard_rows.csv",
        [
            {
                "side_effect_guard_id": f"m2953-side-effect-{index:04d}",
                "side_effect": f"side_effect_{index}",
                "scheduled_or_run": False,
                "status_pass": True,
            }
            for index in range(1, 13)
        ],
    )
    write_csv_rows(m2953_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2953_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    return m2953_dir


def _write_m2916_fixture(root: Path) -> Path:
    m2916_dir = root / "m2916"
    m2916_dir.mkdir()
    write_json(
        m2916_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "execution_admission_admitted_count": 56,
            "execution_admission_blocked_stale_fixed_surface_count": 11,
        },
    )
    candidate_rows = []
    for index in range(1, 68):
        admitted = index <= 56
        candidate_rows.append(
            {
                "execution_admission_candidate_id": f"m2916-candidate-{index:04d}",
                "source_milestone": "m2737" if admitted else "m2877",
                "source_artifact": "source.csv",
                "source_row_id": f"source-row-{index:04d}",
                "source_family": "source_diverse_current_sim_offtrack" if admitted else "fixed_weak_diagnostic",
                "task_family": "T4" if index % 2 else "T5",
                "workload_id": f"workload-{index:04d}",
                "task_source_id": f"task-{index:04d}",
                "profile_name": "L3_online_gru",
                "checkpoint_path": "checkpoint.pt",
                "profile_config_path": "profile.json",
                "execution_admission_status": (
                    m2956.M2916_ADMITTED_STATUS if admitted else m2956.M2916_STALE_STATUS
                ),
                "profile_specific_tuning": False,
                "actor_observation_dim": 72,
                "actor_action_dim": 3,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "future_target_actor_input_required": False,
                "route_labels_actor_visible": False,
                "source_labels_actor_visible": False,
                "diagnostic_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
                "ordinary_engineering_denominator_allowed_after_audit": admitted,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
            }
        )
    write_csv_rows(m2916_dir / "execution_admission_candidate_rows.csv", candidate_rows)
    write_csv_rows(
        m2916_dir / "execution_admission_rejection_rows.csv",
        [
            {
                "rejection_id": f"m2916-rejection-{index:04d}",
                "rejection_type": m2956.M2916_STALE_STATUS,
            }
            for index in range(1, 12)
        ],
    )
    write_csv_rows(
        m2916_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_id": f"m2916-guardrail-{index:04d}",
                "guardrail_family": "route_b_context_only" if index == 1 else "route_a_guardrail",
                "source_row_id": f"guard-{index:04d}",
                "guardrail_reason": "context only",
            }
            for index in range(1, 36)
        ],
    )
    write_csv_rows(m2916_dir / "actor_contract_guard_rows.csv", [{"guard_id": "actor", "status_pass": True}])
    write_csv_rows(m2916_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "claim_made": False}])
    write_csv_rows(m2916_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    return m2916_dir


def test_m2956_materializes_actor_head_delta_execution_admission_without_execution(tmp_path: Path) -> None:
    m2953_dir = _write_m2953_fixture(tmp_path)
    m2916_dir = _write_m2916_fixture(tmp_path)
    m2954_audit = tmp_path / "m2954.md"
    m2955_design = tmp_path / "m2955.md"
    m2917_audit = tmp_path / "m2917.md"
    m2954_audit.write_text("accept_m2953_source_diverse_surface_claim_safe_route_to_m2955\n", encoding="utf-8")
    m2955_design.write_text("admit_m2956_actor_head_delta_execution_admission_materialization_preflight\n", encoding="utf-8")
    m2917_audit.write_text("accept_m2916_execution_admission_materialization_claim_safe_route\n", encoding="utf-8")

    summary = m2956.materialize_actor_head_delta_execution_admission(
        m2953_dir=m2953_dir,
        m2954_audit=m2954_audit,
        m2955_design=m2955_design,
        m2916_dir=m2916_dir,
        m2917_audit=m2917_audit,
        output_dir=tmp_path / "m2956",
        doc_path=tmp_path / "m2956.md",
        follow_up_manifest=tmp_path / "m2957.json",
    )

    assert summary["status_pass"] is True
    assert summary["decision"] == m2956.DECISION_PASS
    assert summary["input_surface_row_count"] == 17
    assert summary["actor_head_delta_execution_admission_candidate_row_count"] == 56
    assert summary["actor_head_delta_execution_admission_rejection_row_count"] == 11
    assert summary["source_guardrail_row_count"] == 46
    assert summary["m2916_source_guardrail_row_count"] == 35
    assert summary["m2956_rejection_guardrail_row_count"] == 11
    assert summary["actor_head_delta_traceability_row_count"] == 88
    assert summary["environment_reset_run"] is False
    assert summary["training_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(tmp_path / "m2957.json")["id"] == m2956.NEXT_ID

    candidate_rows = _read_csv(tmp_path / "m2956" / "actor_head_delta_execution_admission_candidate_rows.csv")
    rejection_rows = _read_csv(tmp_path / "m2956" / "actor_head_delta_execution_admission_rejection_rows.csv")
    guard_rows = _read_csv(tmp_path / "m2956" / "source_guardrail_rows.csv")
    actor_rows = _read_csv(tmp_path / "m2956" / "actor_delta_contract_guard_rows.csv")
    claim_rows = _read_csv(tmp_path / "m2956" / "claim_boundary_rows.csv")
    gate_rows = _read_csv(tmp_path / "m2956" / "gate_matrix.csv")

    assert {row["execution_admission_status"] for row in candidate_rows} == {m2956.ADMITTED_STATUS}
    assert {row["environment_reset_admitted"] for row in candidate_rows} == {"False"}
    assert {row["checkpoint_mutation_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["route_labels_actor_visible"] for row in candidate_rows} == {"False"}
    assert {row["source_labels_actor_visible"] for row in candidate_rows} == {"False"}
    assert {row["validation_denominator_allowed"] for row in candidate_rows} == {"False"}
    assert {row["paper_denominator_allowed"] for row in candidate_rows} == {"False"}
    assert {row["self_id_claim_allowed"] for row in candidate_rows} == {"False"}
    assert {row["rejection_type"] for row in rejection_rows} == {m2956.BLOCKED_STALE_STATUS}
    assert len(guard_rows) == 46
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert all(row["claim_made"] == "False" for row in claim_rows if row["allowed_in_m2956"] == "False")
    assert {row["status_pass"] for row in gate_rows} == {"True"}


def test_m2956_fails_closed_without_m2917_acceptance(tmp_path: Path) -> None:
    m2953_dir = _write_m2953_fixture(tmp_path)
    m2916_dir = _write_m2916_fixture(tmp_path)
    m2954_audit = tmp_path / "m2954.md"
    m2955_design = tmp_path / "m2955.md"
    m2917_audit = tmp_path / "m2917.md"
    m2954_audit.write_text("accept_m2953_source_diverse_surface_claim_safe_route_to_m2955\n", encoding="utf-8")
    m2955_design.write_text("admit_m2956_actor_head_delta_execution_admission_materialization_preflight\n", encoding="utf-8")
    m2917_audit.write_text("audit is present but does not accept M2916\n", encoding="utf-8")

    summary = m2956.materialize_actor_head_delta_execution_admission(
        m2953_dir=m2953_dir,
        m2954_audit=m2954_audit,
        m2955_design=m2955_design,
        m2916_dir=m2916_dir,
        m2917_audit=m2917_audit,
        output_dir=tmp_path / "m2956",
        doc_path=tmp_path / "m2956.md",
        follow_up_manifest=tmp_path / "m2957.json",
    )

    assert summary["status_pass"] is False
    assert summary["decision"] == m2956.DECISION_FAIL
    gate_rows = _read_csv(tmp_path / "m2956" / "gate_matrix.csv")
    assert [row for row in gate_rows if row["gate_id"] == "m2956_m2917_accepts_m2916"][0]["status_pass"] == "False"
    assert [row for row in gate_rows if row["gate_id"] == "m2956_input_surfaces_pass"][0]["status_pass"] == "False"
