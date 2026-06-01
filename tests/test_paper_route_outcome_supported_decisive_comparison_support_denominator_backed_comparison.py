from __future__ import annotations

import csv
from pathlib import Path

from autodrift import paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison as comparison
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _denominator_row(source: str, profile: str, success: int, collision: int, offtrack: int) -> dict[str, object]:
    return {
        "panel_unit_id": f"panel_{source}",
        "source_kind": source,
        "comparison_support_intent": "collision_relief_probe",
        "profile_label": profile,
        "availability_label": "denominator_available_from_profile_source_kind_aggregate",
        "episode_count": 10,
        "success_count": success,
        "collision_count": collision,
        "offtrack_outcome_count": offtrack,
        "success_rate": success / 10.0,
        "collision_rate": collision / 10.0,
        "offtrack_outcome_rate": offtrack / 10.0,
        "clearance_margin_mean": success + 1.0,
        "return_mean": success + 2.0,
        "steps_mean": 90.0,
        "observed_success_support": success > 0,
        "support_absence_semantics": "observed_success_support" if success > 0 else "profile_not_in_m2138_success_support_union",
        "generated_proxy_boundary_only": True,
    }


def _write_inputs(tmp_path: Path, *, claim_admissible: bool = False) -> tuple[Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    rows_path = tmp_path / "denominator_rows.csv"
    claim_path = tmp_path / "claim_boundary.csv"
    profiles = [
        "L0_current_masked",
        "L1_one_step",
        "L2_window_50",
        "L3_online_gru",
        "L3_reset_control_corrected",
    ]
    rows = []
    for source_index in range(6):
        for profile_index, profile in enumerate(profiles):
            rows.append(
                _denominator_row(
                    f"source_{source_index}",
                    profile,
                    success=profile_index,
                    collision=1,
                    offtrack=9 - profile_index,
                )
            )
    write_json(summary_path, {"result_class": "comparison_support_denominator_source_inventory_pass"})
    write_csv_rows(rows_path, rows)
    write_csv_rows(
        claim_path,
        [{"claim": "controller_family_ranking", "admissible": claim_admissible, "reason": "test"}],
        ["claim", "admissible", "reason"],
    )
    return summary_path, rows_path, claim_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materializes_descriptive_diagnostic_comparison(tmp_path: Path) -> None:
    summary_path, rows_path, claim_path = _write_inputs(tmp_path)

    summary = comparison.materialize_diagnostic_comparison(
        inventory_summary_path=summary_path,
        denominator_rows_path=rows_path,
        inventory_claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "comparison_support_denominator_backed_diagnostic_comparison_pass"
    assert summary["profile_count"] == 5
    assert summary["source_kind_count"] == 6
    assert summary["denominator_row_count"] == 30
    assert summary["diagnostic_contrast_row_count"] == 6
    assert summary["winner_selected"] is False
    profile_rows = _read_csv(tmp_path / "out" / "profile_outcome_summary.csv")
    assert len(profile_rows) == 5
    contrast_rows = _read_csv(tmp_path / "out" / "diagnostic_contrast_rows.csv")
    assert {row["verdict_allowed"] for row in contrast_rows} == {"False"}
    assert {row["ranking_allowed"] for row in contrast_rows} == {"False"}
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["finite_window_vs_gru_conclusion_made"] is False


def test_materialization_fails_on_claim_boundary_violation(tmp_path: Path) -> None:
    summary_path, rows_path, claim_path = _write_inputs(tmp_path, claim_admissible=True)

    summary = comparison.materialize_diagnostic_comparison(
        inventory_summary_path=summary_path,
        denominator_rows_path=rows_path,
        inventory_claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "comparison_support_denominator_backed_diagnostic_comparison_fail"
    assert summary["claim_boundary_violation_count"] == 1
