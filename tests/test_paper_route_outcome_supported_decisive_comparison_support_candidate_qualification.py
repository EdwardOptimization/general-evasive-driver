from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_outcome_supported_decisive_comparison_support_candidate_qualification as qual
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _candidate(
    *,
    slice_kind: str = "outcome_by_source_kind",
    support_label: str = "comparison_ready_candidate",
    success_count: int = 8,
    success_profile_count: int = 3,
    success_source_count: int = 6,
    collision_rate: float = 0.12,
    offtrack_rate: float = 0.65,
    source_kind: str = "nominal_delay_support_boundary",
    intent: str = "support_ladder_medium",
    tier: str = "multi_profile_medium_support",
) -> dict[str, object]:
    return {
        "slice_kind": slice_kind,
        "support_label": support_label,
        "episode_count": 50,
        "success_count": success_count,
        "collision_count": 6,
        "offtrack_outcome_count": 36,
        "success_rate": success_count / 50.0,
        "collision_rate": collision_rate,
        "offtrack_outcome_rate": offtrack_rate,
        "success_profile_count": success_profile_count,
        "profiles_with_success": "L1_one_step;L3_online_gru;L3_reset_control_corrected",
        "success_source_count": success_source_count,
        "sources_with_success": "s1;s2;s3;s4;s5;s6",
        "profile_name": "",
        "comparison_support_intent": intent,
        "target_support_tier": tier,
        "source_kind": source_kind,
        "proxy_template_family": "t5_boundary_axis_retarget",
        "generated_source_row": "",
        "materialization_semantics": "",
        "paper_validity_claim": "",
        "all_selected_metrics_finite": True,
    }


def _write_inputs(
    tmp_path: Path,
    *,
    ready_rows: list[dict[str, object]],
    support_rows: list[dict[str, object]],
    summary_ready_count: int | None = None,
    summary_support_count: int | None = None,
) -> tuple[Path, Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    ready_path = tmp_path / "ready.csv"
    support_path = tmp_path / "support.csv"
    claim_path = tmp_path / "claim_boundary.csv"
    write_json(
        summary_path,
        {
            "result_class": "comparison_support_outcome_localization_pass",
            "comparison_ready_candidate_count": len(ready_rows) if summary_ready_count is None else summary_ready_count,
            "comparison_support_candidate_count": len(support_rows)
            if summary_support_count is None
            else summary_support_count,
        },
    )
    write_csv_rows(ready_path, ready_rows)
    write_csv_rows(support_path, support_rows)
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
    return summary_path, ready_path, support_path, claim_path


def test_candidate_qualification_writes_qualified_panel(tmp_path: Path) -> None:
    ready_rows = [
        _candidate(source_kind=f"source_kind_{index}", intent=f"intent_{index % 3}", tier=f"tier_{index % 3}")
        for index in range(7)
    ]
    support_rows = [_candidate(support_label="candidate_support", source_kind="diagnostic")]
    summary_path, ready_path, support_path, claim_path = _write_inputs(
        tmp_path,
        ready_rows=ready_rows,
        support_rows=support_rows,
        summary_ready_count=qual.TARGET_READY_COUNT,
        summary_support_count=qual.TARGET_SUPPORT_COUNT,
    )

    summary = qual.qualify_comparison_support_candidates(
        summary_path=summary_path,
        comparison_ready_candidates_path=ready_path,
        comparison_support_candidates_path=support_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_qualified_candidates=6,
    )

    assert summary["result_class"] == "comparison_support_candidate_qualification_incomplete_or_fail"
    assert summary["ready_counts_match_source_summary"] is False
    assert summary["qualified_candidate_count"] == 7

    summary = qual.qualify_comparison_support_candidates(
        summary_path=summary_path,
        comparison_ready_candidates_path=ready_path,
        comparison_support_candidates_path=support_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out_counts_relaxed",
        min_qualified_candidates=6,
    )
    persisted = read_json(tmp_path / "out_counts_relaxed" / "summary.json")
    assert persisted["qualified_candidate_count"] == 7
    assert (tmp_path / "out_counts_relaxed" / "qualified_candidates.csv").exists()
    assert (tmp_path / "out_counts_relaxed" / "diagnostic_only_candidates.csv").exists()
    assert persisted["controller_family_ranking_claim_made"] is False
    assert persisted["paper_level_claim_made"] is False


def test_candidate_qualification_passes_when_counts_match_source_summary(tmp_path: Path) -> None:
    ready_rows = [
        _candidate(source_kind=f"source_kind_{index}", intent=f"intent_{index % 3}", tier=f"tier_{index % 3}")
        for index in range(qual.TARGET_READY_COUNT)
    ]
    support_rows = [
        _candidate(support_label="candidate_support", source_kind=f"support_{index}")
        for index in range(qual.TARGET_SUPPORT_COUNT)
    ]
    summary_path, ready_path, support_path, claim_path = _write_inputs(
        tmp_path,
        ready_rows=ready_rows,
        support_rows=support_rows,
    )

    summary = qual.qualify_comparison_support_candidates(
        summary_path=summary_path,
        comparison_ready_candidates_path=ready_path,
        comparison_support_candidates_path=support_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_qualified_candidates=6,
    )

    assert summary["result_class"] == "comparison_support_candidate_qualification_pass"
    assert summary["source_comparison_ready_candidate_count"] == qual.TARGET_READY_COUNT
    assert summary["source_comparison_support_candidate_count"] == qual.TARGET_SUPPORT_COUNT
    assert summary["qualified_candidate_count"] == qual.TARGET_READY_COUNT
    assert summary["qualified_axis_coverage_pass"] is True
    assert summary["guardrail_violation_count"] == 0


def test_candidate_qualification_records_rejection_reasons(tmp_path: Path) -> None:
    ready_rows = [
        _candidate(
            success_count=2,
            success_profile_count=1,
            success_source_count=1,
            collision_rate=0.5,
            offtrack_rate=0.8,
        )
    ]
    support_rows = [_candidate(support_label="candidate_support")]
    summary_path, ready_path, support_path, claim_path = _write_inputs(
        tmp_path,
        ready_rows=ready_rows,
        support_rows=support_rows,
    )

    summary = qual.qualify_comparison_support_candidates(
        summary_path=summary_path,
        comparison_ready_candidates_path=ready_path,
        comparison_support_candidates_path=support_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_qualified_candidates=1,
    )

    assert summary["qualified_candidate_count"] == 0
    reasons = summary["rejection_reason_counts"]
    assert reasons["insufficient_success_count"] == 1
    assert reasons["insufficient_profile_coverage"] == 1
    assert reasons["not_comparison_ready"] == 1
    rejection_csv = (tmp_path / "out" / "rejection_reasons.csv").read_text(encoding="utf-8")
    assert "collision_rate_too_high" in rejection_csv
