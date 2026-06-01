from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_outcome_supported_decisive_comparison_support_controlled_panel as panel
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _qualified(
    *,
    source_kind: str,
    slice_kind: str = "outcome_by_intent_source_kind",
    intent: str = "collision_relief_probe",
    success_count: int = 8,
    collision_rate: float = 0.1,
    offtrack_rate: float = 0.6,
) -> dict[str, object]:
    return {
        "candidate_key": f"{slice_kind}|{intent}|{source_kind}",
        "qualification_label": "qualified_candidate",
        "slice_kind": slice_kind,
        "support_label": "comparison_ready_candidate",
        "episode_count": 50,
        "success_count": success_count,
        "collision_count": 5,
        "offtrack_outcome_count": 37,
        "success_rate": success_count / 50.0,
        "collision_rate": collision_rate,
        "offtrack_outcome_rate": offtrack_rate,
        "success_profile_count": 3,
        "profiles_with_success": "L1_one_step;L3_online_gru;L3_reset_control_corrected",
        "success_source_count": 6,
        "sources_with_success": "s1;s2;s3;s4;s5;s6",
        "comparison_support_intent": intent,
        "target_support_tier": "collision_dominance_relief_support",
        "source_kind": source_kind,
        "proxy_template_family": "",
        "generated_proxy_boundary_only": True,
    }


def _write_inputs(tmp_path: Path, rows: list[dict[str, object]], *, summary_count: int | None = None) -> tuple[Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    qualified_path = tmp_path / "qualified.csv"
    claim_path = tmp_path / "claim_boundary.csv"
    write_json(
        summary_path,
        {
            "result_class": "comparison_support_candidate_qualification_pass",
            "qualified_candidate_count": len(rows) if summary_count is None else summary_count,
        },
    )
    write_csv_rows(qualified_path, rows)
    write_csv_rows(
        claim_path,
        [
            {
                "claim": "paper_level_benchmark_result",
                "admissible": False,
                "reason": "generated comparison-support rows remain smoke proxies",
            }
        ],
        ["claim", "admissible", "reason"],
    )
    return summary_path, qualified_path, claim_path


def _full_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(6):
        source_kind = f"source_kind_{index}"
        rows.append(_qualified(source_kind=source_kind, slice_kind="outcome_by_intent_source_kind"))
        rows.append(
            _qualified(
                source_kind=source_kind,
                slice_kind="outcome_by_source_kind",
                intent="",
                success_count=20,
                collision_rate=0.01,
                offtrack_rate=0.2,
            )
        )
    rows.extend(
        [
            _qualified(source_kind="", slice_kind="outcome_by_proxy_template", intent=""),
            _qualified(source_kind="", slice_kind="outcome_by_intent", intent="collision_relief_probe"),
            _qualified(source_kind="", slice_kind="outcome_by_target_support_tier", intent=""),
        ]
    )
    return rows


def test_controlled_panel_constructs_non_overlapping_source_units(tmp_path: Path) -> None:
    rows = _full_rows()
    summary_path, qualified_path, claim_path = _write_inputs(tmp_path, rows)

    summary = panel.construct_controlled_panel(
        summary_path=summary_path,
        qualified_candidates_path=qualified_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_panel_units=6,
    )

    assert summary["result_class"] == "comparison_support_controlled_panel_construction_pass"
    assert summary["controlled_panel_unit_count"] == 6
    assert summary["panel_source_kind_count"] == 6
    assert summary["panel_duplicate_source_kind_count"] == 0
    assert summary["panel_broad_aggregate_exclusion_count"] == 3
    assert summary["excluded_reason_counts"]["duplicate_source_kind_lower_priority"] == 6
    assert (tmp_path / "out" / "controlled_panel_units.csv").exists()
    assert (tmp_path / "out" / "excluded_qualified_candidates.csv").exists()
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["controller_family_ranking_claim_made"] is False
    assert persisted["paper_level_claim_made"] is False


def test_controlled_panel_prefers_intent_source_kind_over_better_source_kind(tmp_path: Path) -> None:
    rows = [
        _qualified(source_kind="same_source", slice_kind="outcome_by_intent_source_kind", success_count=6),
        _qualified(source_kind="same_source", slice_kind="outcome_by_source_kind", intent="", success_count=40),
    ]
    summary_path, qualified_path, claim_path = _write_inputs(tmp_path, rows, summary_count=panel.TARGET_QUALIFIED_COUNT)

    summary = panel.construct_controlled_panel(
        summary_path=summary_path,
        qualified_candidates_path=qualified_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_panel_units=1,
    )

    panel_csv = (tmp_path / "out" / "controlled_panel_units.csv").read_text(encoding="utf-8")
    assert "outcome_by_intent_source_kind" in panel_csv
    assert summary["panel_duplicate_source_kind_count"] == 0


def test_controlled_panel_fails_when_source_count_mismatches_summary(tmp_path: Path) -> None:
    rows = _full_rows()
    summary_path, qualified_path, claim_path = _write_inputs(tmp_path, rows, summary_count=panel.TARGET_QUALIFIED_COUNT + 1)

    summary = panel.construct_controlled_panel(
        summary_path=summary_path,
        qualified_candidates_path=qualified_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_panel_units=6,
    )

    assert summary["result_class"] == "comparison_support_controlled_panel_construction_incomplete_or_fail"
    assert summary["qualified_count_matches_source"] is False
