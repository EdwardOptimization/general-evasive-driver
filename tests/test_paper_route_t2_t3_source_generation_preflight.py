from __future__ import annotations

import csv
from pathlib import Path

from autodrift.paper_route_t2_t3_source_generation_preflight import (
    run_t2_t3_source_generation_preflight,
)


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
        "source_role_semantics": "test_role",
        "parent_feasibility_tier_id": "test_tier",
        "normalized_surface_variant": "test_surface",
        "sampled_obstacle_label": "test_label",
        "source_reference": source_id,
    }


def test_t2_t3_source_generation_projection_passes_with_slack(tmp_path: Path) -> None:
    panel_sources = tmp_path / "panel_sources.csv"
    output_dir = tmp_path / "out"
    rows: list[dict[str, object]] = []

    for i in range(18):
        rows.append(_base_source("T1_reactive_active_safety", f"t1-{i}", f"t1_kind_{i % 4}"))
    for i in range(21):
        rows.append(
            _base_source(
                "T2_same_current_different_older_history",
                f"t2-dominant-{i}",
                "actuator_delay_proxy+capability_step_proxy",
            )
        )
    for kind in ("actuator_delay_proxy", "capability_step_proxy", "capability_step_proxy+warmup_proxy"):
        for i in range(5):
            rows.append(_base_source("T2_same_current_different_older_history", f"t2-{kind}-{i}", kind))
    for kind, count in (
        ("actuator_delay_proxy+terminal_boundary_proxy+warmup_proxy", 9),
        ("capability_step_proxy+terminal_boundary_proxy+warmup_proxy", 9),
        ("capability_step_proxy+warmup_proxy", 5),
        ("terminal_boundary_proxy+warmup_proxy", 1),
    ):
        for i in range(count):
            rows.append(_base_source("T3_active_diagnostic_warmup", f"t3-{kind}-{i}", kind))
    for i in range(33):
        rows.append(_base_source("T4_variable_diagnostic_delay", f"t4-{i}", f"t4_kind_{i % 4}"))
    for i in range(72):
        rows.append(_base_source("T5_source_rich_extreme_dynamics", f"t5-{i}", f"t5_kind_{i % 8}"))
    _write_csv(panel_sources, rows)

    summary = run_t2_t3_source_generation_preflight(panel_sources_path=panel_sources, output_dir=output_dir)

    assert summary["result_class"] == "t2_t3_source_generation_preflight_pass"
    assert summary["generated_t2_source_count"] == 36
    assert summary["generated_t3_source_count"] == 18
    assert summary["panel_projected_ready_for_routing_smoke"] is True
    assert summary["guardrail_violation_count"] == 0
    assert (output_dir / "generated_source_specs.csv").exists()
    assert (output_dir / "merged_panel_sources.csv").exists()
    assert (output_dir / "source_coverage_projection.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()
    with (output_dir / "source_coverage_comparison.csv").open(newline="", encoding="utf-8") as handle:
        comparison = {row["panel_task_family"]: row for row in csv.DictReader(handle)}
    assert comparison["T2_same_current_different_older_history"]["status"] == "passes_after_generation"
    assert comparison["T3_active_diagnostic_warmup"]["status"] == "passes_after_generation"
    with (output_dir / "generated_panel_sources.csv").open(newline="", encoding="utf-8") as handle:
        generated = list(csv.DictReader(handle))
    assert {row["panel_task_family"] for row in generated} == {
        "T2_same_current_different_older_history",
        "T3_active_diagnostic_warmup",
    }
