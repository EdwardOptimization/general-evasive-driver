from __future__ import annotations

import csv
import json
from pathlib import Path

from autodrift.paper_route_controlled_comparison_panel_preflight import run_panel_preflight


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_panel_preflight_writes_protocol_workload_coverage_and_claim_boundary(tmp_path: Path) -> None:
    task_specs = tmp_path / "task_source_specs.json"
    candidate_support = tmp_path / "candidate_support.csv"
    m1683_summary = tmp_path / "m1683_summary.json"
    output_dir = tmp_path / "out"

    task_specs.write_text(
        json.dumps(
            {
                "task_source_specs": [
                    {
                        "task_source_id": "spec-t4",
                        "task_family": "T4",
                        "source_edge": "actuator_delay_step|capability_step_up",
                        "window_tag": "reveal_plus_4",
                        "source_metadata_roles": ["role_a"],
                        "source_family_left": "capability_step_up",
                        "source_family_right": "actuator_delay_step",
                        "mapping_lineage": {"source_mapping_id": "map-t4"},
                    },
                    {
                        "task_source_id": "spec-warmup",
                        "task_family": "T5",
                        "source_edge": "near_boundary_warmup|capability_step_down",
                        "window_tag": "decision_minus_24",
                        "source_metadata_roles": ["role_b"],
                        "source_family_left": "near_boundary_warmup",
                        "source_family_right": "capability_step_down",
                        "mapping_lineage": {"source_mapping_id": "map-warmup"},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    _write_csv(
        candidate_support,
        [
            {
                "candidate_key": "candidate-a",
                "repair_source_kind": "success_stabilizer",
                "source_role_semantics": "stable_aes_only",
                "parent_feasibility_tier_id": "tier_b",
                "normalized_surface_variant": "post_friction_step",
                "sampled_obstacle_label": "aes_feasible",
            }
        ],
    )
    m1683_summary.write_text(json.dumps({"guardrail_violation_count": 0}), encoding="utf-8")

    summary = run_panel_preflight(
        task_specs_path=task_specs,
        candidate_support_path=candidate_support,
        m1683_summary_path=m1683_summary,
        output_dir=output_dir,
    )

    assert summary["guardrail_violation_count"] == 0
    assert summary["profile_count"] == 12
    assert summary["workload_cell_count"] == summary["panel_source_count"] * 12
    assert (output_dir / "panel_protocol.json").exists()
    assert (output_dir / "workload_matrix.csv").exists()
    assert (output_dir / "source_coverage.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()
