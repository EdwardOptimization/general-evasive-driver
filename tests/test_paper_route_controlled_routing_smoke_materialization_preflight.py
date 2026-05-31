from __future__ import annotations

import csv
from pathlib import Path

from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.paper_route_controlled_routing_smoke_materialization_preflight import (
    proxy_template_for_source,
    run_materialization_preflight,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _source(family: str, source_id: str, kind: str, *, generated: bool = False) -> dict[str, object]:
    origin = "m2029_t2_t3_source_generation_preflight" if generated else "test"
    return {
        "panel_source_id": source_id,
        "panel_task_family": family,
        "source_origin": origin,
        "source_kind": kind,
        "source_edge": f"{kind}|edge",
        "window_tag": "test_window",
        "source_role_semantics": "test_role",
        "parent_feasibility_tier_id": "test_tier",
        "normalized_surface_variant": kind,
        "sampled_obstacle_label": "test_label",
        "source_reference": source_id,
    }


def _profile_tree(root: Path) -> None:
    for profile in EXPECTED_PROFILE_NAMES:
        config_path = root / "configs" / f"{profile}_seed167400.json"
        checkpoint_path = root / "profile_runs" / profile / "seed_167400" / "checkpoint.pt"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{}", encoding="utf-8")
        checkpoint_path.write_text("checkpoint", encoding="utf-8")


def test_routing_smoke_materialization_preflight_writes_bounded_workload(tmp_path: Path) -> None:
    panel_sources = tmp_path / "merged_panel_sources.csv"
    generated_specs = tmp_path / "generated_source_specs.csv"
    profile_run_dir = tmp_path / "profiles"
    output_dir = tmp_path / "out"
    rows: list[dict[str, object]] = []
    for family, prefix, count in (
        ("T1_reactive_active_safety", "t1", 4),
        ("T2_same_current_different_older_history", "t2", 10),
        ("T3_active_diagnostic_warmup", "t3", 10),
        ("T4_variable_diagnostic_delay", "t4", 4),
        ("T5_source_rich_extreme_dynamics", "t5", 8),
    ):
        for i in range(count):
            rows.append(_source(family, f"{prefix}-{i}", f"{prefix}_kind_{i}", generated=prefix in {"t2", "t3"}))
            rows.append(_source(family, f"{prefix}-{i}-duplicate", f"{prefix}_kind_{i}", generated=prefix in {"t2", "t3"}))
    _write_csv(panel_sources, rows)
    _write_csv(generated_specs, [{"source_spec_id": f"t2-{i}"} for i in range(10)] + [{"source_spec_id": f"t3-{i}"} for i in range(10)])
    _profile_tree(profile_run_dir)

    summary = run_materialization_preflight(
        panel_sources_path=panel_sources,
        generated_source_specs_path=generated_specs,
        profile_run_dir=profile_run_dir,
        output_dir=output_dir,
    )

    assert summary["result_class"] == "controlled_routing_smoke_materialization_preflight_pass"
    assert summary["selected_source_count"] == 36
    assert summary["planned_workload_count"] == 36 * len(EXPECTED_PROFILE_NAMES)
    assert summary["guardrail_violation_count"] == 0
    assert (output_dir / "selected_smoke_sources.csv").exists()
    assert (output_dir / "executable_task_specs.json").exists()
    assert (output_dir / "planned_workload.csv").exists()
    with (output_dir / "executable_task_specs.csv").open(newline="", encoding="utf-8") as handle:
        spec_rows = list(csv.DictReader(handle))
    assert spec_rows
    assert {row["materialization_semantics"] for row in spec_rows} == {"smoke_proxy"}
    assert {row["paper_validity_claim"] for row in spec_rows} == {"false"}


def test_proxy_template_mapping_preserves_source_semantics() -> None:
    assert (
        proxy_template_for_source(
            _source(
                "T2_same_current_different_older_history",
                "actuator",
                "actuator_delay_proxy",
            )
        )
        == "t4_actuator_delay_response"
    )
    assert (
        proxy_template_for_source(
            _source(
                "T2_same_current_different_older_history",
                "capability",
                "capability_step_proxy",
            )
        )
        == "t4_staged_warmup_capability"
    )
