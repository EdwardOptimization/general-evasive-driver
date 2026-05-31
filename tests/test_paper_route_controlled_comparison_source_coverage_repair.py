from __future__ import annotations

import csv
from pathlib import Path

from autodrift.paper_route_controlled_comparison_source_coverage_repair import run_source_coverage_repair


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _base_source(family: str, source_id: str, kind: str) -> dict[str, object]:
    return {
        "panel_source_id": source_id,
        "panel_task_family": family,
        "source_origin": "test",
        "source_kind": kind,
        "source_edge": f"{kind}|edge",
        "window_tag": "test_window",
        "source_role_semantics": "stable_aes_only",
        "parent_feasibility_tier_id": "tier_b",
        "normalized_surface_variant": "post_friction_step",
        "sampled_obstacle_label": "aes_feasible",
        "source_reference": source_id,
    }


def _candidate(index: int, kind: str) -> dict[str, object]:
    return {
        "repair_candidate_id": f"candidate-{index}",
        "repair_source_kind": kind,
        "source_support_status": "supported",
        "labels_enter_actor_input": "False",
        "profile_specific_tuning": "False",
        "controller_family_ranking_claim_made": "False",
        "paper_level_claim_made": "False",
        "level3_self_id_claim_made": "False",
        "source_role_semantics": "stable_aeb",
        "feasibility_tier_id": "tier_c",
        "normalized_surface_variant": "steady_surface",
        "sampled_obstacle_label": "aeb_feasible",
    }


def test_source_coverage_repair_adds_clean_t1_sources_and_preserves_guardrails(tmp_path: Path) -> None:
    panel_sources = tmp_path / "panel_sources.csv"
    m1983_sources = tmp_path / "m1983.csv"
    m1952_sources = tmp_path / "m1952.csv"
    output_dir = tmp_path / "out"
    base_rows = [_base_source("T1_reactive_active_safety", f"t1-{i}", "success_stabilizer") for i in range(6)]
    for family in (
        "T2_same_current_different_older_history",
        "T3_active_diagnostic_warmup",
        "T4_variable_diagnostic_delay",
        "T5_source_rich_extreme_dynamics",
    ):
        for i in range(12):
            base_rows.append(_base_source(family, f"{family}-{i}", f"kind-{i % 4}"))
    _write_csv(panel_sources, base_rows)
    _write_csv(m1983_sources, [_candidate(i, f"repair_kind_{i % 3}") for i in range(12)])
    _write_csv(m1952_sources, [_candidate(100 + i, f"repair_kind_{i % 3}") for i in range(3)])

    summary = run_source_coverage_repair(
        panel_sources_path=panel_sources,
        m1983_sources_path=m1983_sources,
        m1952_sources_path=m1952_sources,
        output_dir=output_dir,
    )

    assert summary["guardrail_violation_count"] == 0
    assert summary["added_source_count"] >= 12
    assert summary["repaired_source_count"] > summary["base_source_count"]
    assert (output_dir / "repaired_panel_sources.csv").exists()
    assert (output_dir / "repaired_source_coverage.csv").exists()
    assert (output_dir / "repair_actions.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()
    with (output_dir / "coverage_comparison.csv").open(newline="", encoding="utf-8") as handle:
        comparison = {row["panel_task_family"]: row for row in csv.DictReader(handle)}
    assert comparison["T1_reactive_active_safety"]["status"] == "passes_after_repair"
    assert comparison["T4_variable_diagnostic_delay"]["status"] == "already_ready"
