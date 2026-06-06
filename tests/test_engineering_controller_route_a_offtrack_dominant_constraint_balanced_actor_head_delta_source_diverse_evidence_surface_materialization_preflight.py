from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_source_diverse_evidence_surface_materialization_preflight
    as m2953,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2951_fixture(root: Path) -> Path:
    m2951_dir = root / "m2951"
    m2951_dir.mkdir()
    write_json(
        m2951_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "actor_contract_shape_72_action_3": True,
            "hidden_or_oracle_actor_inputs_required": False,
            "future_target_actor_inputs_required": False,
        },
    )
    write_csv_rows(
        m2951_dir / "integration_surface_rows.csv",
        [
            {
                "integration_surface_id": "m2951-integration-surface-0001",
                "combination_rule": "parent_action + bounded_residual_delta then action clamp",
                "zero_delta_identity_required": True,
                "residual_bound_required": True,
                "execution_scheduled": False,
            }
        ],
    )
    write_csv_rows(
        m2951_dir / "actor_binding_rows.csv",
        [
            {
                "actor_binding_id": "m2951-actor-binding-0001",
                "contract_field": "actor_observation_dim",
                "observed_value": 72,
                "expected_value": 72,
                "status_pass": True,
                "actor_visible": False,
            },
            {
                "actor_binding_id": "m2951-actor-binding-0002",
                "contract_field": "action_dim",
                "observed_value": 3,
                "expected_value": 3,
                "status_pass": True,
                "actor_visible": False,
            },
            {
                "actor_binding_id": "m2951-actor-binding-0003",
                "contract_field": "action_mapping",
                "observed_value": "steer/throttle/brake",
                "expected_value": "steer/throttle/brake",
                "status_pass": True,
                "actor_visible": False,
            },
            {
                "actor_binding_id": "m2951-actor-binding-0004",
                "contract_field": "parent_distribution_path",
                "observed_value": "tanh(mean)",
                "expected_value": "tanh(mean)",
                "status_pass": True,
                "actor_visible": False,
            },
            {
                "actor_binding_id": "m2951-actor-binding-0005",
                "contract_field": "mapping_extra_keys_allowed",
                "observed_value": False,
                "expected_value": False,
                "status_pass": True,
                "actor_visible": False,
            },
        ],
    )
    write_csv_rows(
        m2951_dir / "residual_initialization_rows.csv",
        [
            {
                "residual_initialization_id": f"m2951-residual-initialization-{index:04d}",
                "contract_field": field,
                "status_pass": True,
            }
            for index, field in enumerate(
                [
                    "zero_delta_parent_identity",
                    "residual_head_observation_only_input",
                    "zero_initialized_final_output_supported",
                    "parent_trunk_mutation",
                ],
                1,
            )
        ],
    )
    write_csv_rows(
        m2951_dir / "residual_bound_rows.csv",
        [
            {
                "residual_bound_id": f"m2951-residual-bound-{index:04d}",
                "contract_field": field,
                "status_pass": True,
            }
            for index, field in enumerate(
                [
                    "residual_delta_bound_before_combination",
                    "combined_action_range_clamp",
                    "bound_values_materialized_before_candidate_build",
                    "residual_bound_used_as_performance_claim",
                ],
                1,
            )
        ],
    )
    write_csv_rows(
        m2951_dir / "input_guard_rows.csv",
        [
            {
                "input_guard_id": f"m2951-input-guard-{index:04d}",
                "forbidden_key": f"forbidden_key_{index}",
                "actor_visible": False,
                "status_pass": True,
            }
            for index in range(1, 36)
        ],
    )
    write_csv_rows(
        m2951_dir / "side_effect_guard_rows.csv",
        [
            {
                "side_effect_guard_id": f"m2951-side-effect-guard-{index:04d}",
                "side_effect": f"side_effect_{index}",
                "scheduled_or_run": False,
                "status_pass": True,
            }
            for index in range(1, 13)
        ],
    )
    write_csv_rows(
        m2951_dir / "claim_boundary_rows.csv",
        [
            {
                "claim_id": f"m2951_claim_{index:04d}",
                "claim_family": f"claim_family_{index}",
                "allowed_in_m2951": index <= 2,
                "claim_made": index <= 2,
                "status_pass": True,
            }
            for index in range(1, 16)
        ],
    )
    write_csv_rows(
        m2951_dir / "gate_matrix.csv",
        [
            {
                "gate_id": f"m2951_gate_{index:04d}",
                "gate_family": f"gate_family_{index}",
                "status_pass": True,
            }
            for index in range(1, 13)
        ],
    )
    return m2951_dir


def test_m2953_materializes_source_diverse_panel_and_traceability_without_execution(tmp_path: Path) -> None:
    m2951_dir = _write_m2951_fixture(tmp_path)
    m2952_audit = tmp_path / "m2952.md"
    m2952_audit.write_text(
        "accept_m2951_materialization_claim_safe_route_to_m2953_source_diverse_evidence_surface_materialization\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "m2953"
    doc_path = tmp_path / "m2953.md"
    follow_up = tmp_path / "m2954.json"

    summary = m2953.run_source_diverse_evidence_surface_materialization_preflight(
        m2951_dir=m2951_dir,
        m2952_audit=m2952_audit,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["evidence_source_row_count"] == 10
    assert summary["source_diversity_row_count"] == 4
    assert summary["panel_spec_row_count"] == 8
    assert summary["contract_traceability_row_count"] == 88
    assert summary["actor_contract_guard_row_count"] == 8
    assert summary["side_effect_guard_row_count"] == 12
    assert summary["claim_boundary_row_count"] == 19
    assert summary["candidate_execution_admitted_in_m2953"] is False
    assert summary["environment_reset_run"] is False
    assert summary["training_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2953.NEXT_ID

    source_rows = _read_csv(output_dir / "evidence_source_rows.csv")
    diversity_rows = _read_csv(output_dir / "source_diversity_rows.csv")
    panel_rows = _read_csv(output_dir / "panel_spec_rows.csv")
    trace_rows = _read_csv(output_dir / "contract_traceability_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    side_effect_rows = _read_csv(output_dir / "side_effect_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["status_pass_or_present"] for row in source_rows} == {"True"}
    assert {row["same_public_gate_repair_loop"] for row in diversity_rows} == {"False"}
    assert {row["candidate_execution_admitted_in_m2953"] for row in panel_rows} == {"False"}
    assert {row["hidden_oracle_actor_input_required"] for row in panel_rows} == {"False"}
    assert {row["actor_visible"] for row in trace_rows} == {"False"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {row["scheduled_or_run"] for row in side_effect_rows} == {"False"}
    assert all(row["claim_made"] == "False" for row in claim_rows if row["allowed_in_m2953"] == "False")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
