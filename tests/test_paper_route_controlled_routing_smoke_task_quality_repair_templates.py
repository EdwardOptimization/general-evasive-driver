from __future__ import annotations

from pathlib import Path

import pytest

from autodrift import paper_route_controlled_routing_smoke_task_quality_repair_templates as templates
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _write_localization_fixture(tmp_path: Path, *, result_class: str = "controlled_routing_smoke_outcome_localization_pass") -> Path:
    out = tmp_path / "localization"
    out.mkdir()
    offtrack_rows: list[dict[str, object]] = []
    for profile in [
        "L2_window_13",
        "L2_window_25",
        "L2_window_50",
        "L2_window_100",
        "L2_window_13_current_tiled",
        "L2_window_25_current_tiled",
        "L2_window_50_current_tiled",
        "L2_window_100_current_tiled",
    ]:
        offtrack_rows.append(
            {
                "slice_kind": "outcome_by_profile",
                "profile_name": profile,
                "episode_count": 36,
                "success_count": 0,
                "collision_count": 0,
                "offtrack_outcome_count": 36,
                "offtrack_outcome_rate": 1.0,
                "support_label": "no_support",
            }
        )
    for family in ["T1", "T2", "T3", "T4", "T5"]:
        offtrack_rows.append(
            {
                "slice_kind": "outcome_by_family",
                "panel_task_family": family,
                "episode_count": 48,
                "success_count": 1,
                "collision_count": 0,
                "offtrack_outcome_count": 47,
                "offtrack_outcome_rate": 0.98,
                "support_label": "weak_support",
            }
        )
    for index in range(6):
        offtrack_rows.append(
            {
                "slice_kind": "outcome_by_source_kind",
                "source_kind": f"zero_success_kind_{index}",
                "episode_count": 12,
                "success_count": 0,
                "collision_count": 0,
                "offtrack_outcome_count": 12,
                "offtrack_outcome_rate": 1.0,
                "support_label": "no_support",
            }
        )
    success_rows = [
        {
            "workload_id": f"success_{index}",
            "task_source_id": f"source_{index}",
            "panel_source_id": f"panel_{index}",
            "panel_task_family": "T2",
            "source_kind": "success_kind",
            "proxy_template_family": "success_template",
            "generated_source_row": index % 2 == 0,
            "paper_validity_claim": False,
            "profile_name": "L3_online_gru",
            "outcome_bucket": "success_obstacle_pass",
            "termination_reason": "",
        }
        for index in range(20)
    ]
    generated_rows = [
        {
            "slice_kind": "outcome_by_generated_proxy",
            "generated_source_row": True,
            "materialization_semantics": "smoke_proxy",
            "paper_validity_claim": False,
            "episode_count": 144,
            "success_count": 6,
            "collision_count": 4,
            "offtrack_outcome_count": 134,
            "offtrack_outcome_rate": 0.93,
            "support_label": "weak_support",
        }
    ]
    write_csv_rows(out / "offtrack_dominance_slices.csv", offtrack_rows)
    write_csv_rows(out / "success_rows.csv", success_rows)
    write_csv_rows(out / "outcome_by_generated_proxy.csv", generated_rows)
    summary_path = out / "summary.json"
    write_json(
        summary_path,
        {
            "result_class": result_class,
            "artifacts": {
                "offtrack_dominance_slices": str(out / "offtrack_dominance_slices.csv"),
                "success_rows": str(out / "success_rows.csv"),
                "outcome_by_generated_proxy": str(out / "outcome_by_generated_proxy.csv"),
            },
        },
    )
    return summary_path


def test_repair_template_generator_writes_registered_quotas(tmp_path: Path) -> None:
    summary_path = _write_localization_fixture(tmp_path)
    output_path = tmp_path / "templates.json"

    payload = templates.generate_routing_smoke_task_quality_repair_templates(
        localization_summary_path=summary_path,
        output_path=output_path,
        next_blocker="next",
    )

    assert payload["result_class"] == "controlled_routing_smoke_task_quality_repair_templates_pass"
    assert payload["candidate_source_count"] == 192
    assert payload["repair_axis_counts"] == templates.REPAIR_AXIS_TARGETS
    assert payload["source_split_counts"] == templates.SPLIT_TARGETS
    assert payload["guardrail_violation_count"] == 0
    assert all(not row["paper_level_claim_made"] for row in payload["candidates"])
    assert all(not row["profile_specific_tuning"] for row in payload["candidates"])
    assert all(not row["target_paper_validity_claim"] for row in payload["candidates"])
    assert output_path.exists()
    persisted = read_json(output_path)
    assert persisted["next_blocker"] == "next"


def test_repair_template_generator_rejects_wrong_localization_result_class(tmp_path: Path) -> None:
    summary_path = _write_localization_fixture(
        tmp_path,
        result_class="controlled_routing_smoke_outcome_localization_incomplete_or_fail",
    )

    with pytest.raises(ValueError, match="localization summary"):
        templates.generate_routing_smoke_task_quality_repair_templates(
            localization_summary_path=summary_path,
            output_path=tmp_path / "templates.json",
        )


def test_repair_template_generator_fails_on_missing_axis_support(tmp_path: Path) -> None:
    summary_path = _write_localization_fixture(tmp_path)
    summary = read_json(summary_path)
    Path(summary["artifacts"]["success_rows"]).write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="success_neighborhood_expansion"):
        templates.generate_routing_smoke_task_quality_repair_templates(
            localization_summary_path=summary_path,
            output_path=tmp_path / "templates.json",
        )
