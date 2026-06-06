from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_post_scaffold_integration_contract_materialization_preflight as m2951


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_post_scaffold_integration_contract_materialization_writes_claim_safe_rows(tmp_path: Path) -> None:
    m2948_doc = tmp_path / "m2948.md"
    m2949_audit = tmp_path / "m2949.md"
    m2950_design = tmp_path / "m2950.md"
    output_dir = tmp_path / "m2951"
    doc_path = tmp_path / "m2951.md"
    follow_up = tmp_path / "m2952.json"
    m2948_doc.write_text("bounded_actor_head_delta_scaffold_tests_pass\n", encoding="utf-8")
    m2949_audit.write_text(
        "accept_m2948_scaffold_claim_safe_route_to_m2950_post_scaffold_integration_design\n",
        encoding="utf-8",
    )
    m2950_design.write_text(
        "admit_m2951_post_scaffold_integration_contract_materialization_preflight\n",
        encoding="utf-8",
    )

    summary = m2951.run_post_scaffold_integration_contract_materialization_preflight(
        m2948_doc=m2948_doc,
        m2949_audit=m2949_audit,
        m2950_design=m2950_design,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["integration_surface_row_count"] == 1
    assert summary["actor_binding_row_count"] == 5
    assert summary["residual_initialization_row_count"] == 4
    assert summary["residual_bound_row_count"] == 4
    assert summary["input_guard_row_count"] == len(m2951.FORBIDDEN_ACTOR_INPUT_KEYS)
    assert summary["side_effect_guard_row_count"] == 12
    assert summary["implementation_run"] is False
    assert summary["checkpoint_modification_run"] is False
    assert summary["environment_reset_run"] is False
    assert summary["training_run"] is False
    assert summary["repair_success_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2951.NEXT_ID

    integration_rows = _read_csv(output_dir / "integration_surface_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_binding_rows.csv")
    input_rows = _read_csv(output_dir / "input_guard_rows.csv")
    side_effect_rows = _read_csv(output_dir / "side_effect_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert integration_rows[0]["execution_scheduled"] == "False"
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {row["actor_visible"] for row in input_rows} == {"False"}
    assert {row["scheduled_or_run"] for row in side_effect_rows} == {"False"}
    assert all(row["claim_made"] == "False" for row in claim_rows if row["allowed_in_m2951"] == "False")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
