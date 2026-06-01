from __future__ import annotations

import csv
from pathlib import Path

from autodrift import paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory as inventory
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _panel_row(source_kind: str) -> dict[str, object]:
    return {
        "panel_unit_id": f"panel_{source_kind}",
        "source_kind": source_kind,
        "comparison_support_intent": "collision_relief_probe",
        "generated_proxy_boundary_only": True,
    }


def _support_row(source_kind: str, profile: str, *, supported: bool) -> dict[str, object]:
    return {
        "panel_unit_id": f"panel_{source_kind}",
        "source_kind": source_kind,
        "comparison_support_intent": "collision_relief_probe",
        "profile_label": profile,
        "observed_success_support": supported,
        "absence_semantics": "observed_success_support"
        if supported
        else "no_success_support_observed_in_m2134_aggregate",
    }


def _source_row(source_kind: str, profile: str, *, finite: bool = True) -> dict[str, object]:
    return {
        "profile_name": profile,
        "source_kind": source_kind,
        "slice_kind": "outcome_by_profile_source_kind",
        "support_label": "comparison_ready_candidate",
        "episode_count": 10,
        "success_count": 2,
        "collision_count": 1,
        "offtrack_outcome_count": 7,
        "success_rate": 0.2,
        "collision_rate": 0.1,
        "offtrack_outcome_rate": 0.7,
        "clearance_margin_mean": 1.25,
        "return_mean": 3.5,
        "steps_mean": 90,
        "all_selected_metrics_finite": finite,
        "success_obstacle_pass": 2,
        "collision_failure": 1,
        "off_track_noncollision_noncompletion": 7,
        "termination_off_track": 7,
        "termination_obstacle_collision": 1,
        "termination_empty": 2,
    }


def _write_inputs(
    tmp_path: Path,
    *,
    source_rows: list[dict[str, object]] | None = None,
    claim_admissible: bool = False,
) -> tuple[Path, Path, Path, Path, Path, Path, Path, Path]:
    protocol_summary = tmp_path / "protocol_summary.json"
    panel_units = tmp_path / "panel_units.csv"
    support_matrix = tmp_path / "support_matrix.csv"
    protocol_claim = tmp_path / "protocol_claim.csv"
    profile_source = tmp_path / "profile_source.csv"
    measured_summary = tmp_path / "measured_summary.json"
    profile_aggregate = tmp_path / "profile_aggregate.csv"
    measured_claim = tmp_path / "measured_claim.csv"

    panel = [_panel_row("source_a"), _panel_row("source_b")]
    profiles = ["L0_current_masked", "L1_one_step", "L2_window_50"]
    write_json(protocol_summary, {"result_class": "comparison_support_comparison_protocol_materialization_pass"})
    write_json(measured_summary, {"result_class": "comparison_support_measured_execution_pass"})
    write_csv_rows(panel_units, panel)
    write_csv_rows(
        support_matrix,
        [
            _support_row("source_a", "L0_current_masked", supported=True),
            _support_row("source_a", "L1_one_step", supported=True),
            _support_row("source_b", "L0_current_masked", supported=False),
            _support_row("source_b", "L1_one_step", supported=True),
        ],
    )
    write_csv_rows(profile_aggregate, [{"key": profile} for profile in profiles])
    if source_rows is None:
        source_rows = [_source_row(source, profile) for source in ("source_a", "source_b") for profile in profiles]
    write_csv_rows(profile_source, source_rows)
    claim_rows = [
        {
            "claim": "controller_family_ranking",
            "admissible": claim_admissible,
            "reason": "test boundary",
        }
    ]
    write_csv_rows(protocol_claim, claim_rows, ["claim", "admissible", "reason"])
    write_csv_rows(measured_claim, [], ["claim", "admissible", "reason"])
    return (
        protocol_summary,
        panel_units,
        support_matrix,
        protocol_claim,
        profile_source,
        measured_summary,
        profile_aggregate,
        measured_claim,
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materializes_complete_denominator_inventory(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)

    summary = inventory.materialize_denominator_inventory(
        protocol_summary_path=inputs[0],
        panel_units_path=inputs[1],
        support_matrix_path=inputs[2],
        protocol_claim_boundary_path=inputs[3],
        profile_source_kind_path=inputs[4],
        measured_summary_path=inputs[5],
        profile_aggregate_path=inputs[6],
        measured_claim_boundary_path=inputs[7],
        output_dir=tmp_path / "out",
        expected_panel_units=2,
        expected_profile_count=3,
        expected_denominator_count=6,
    )

    assert summary["result_class"] == "comparison_support_denominator_source_inventory_pass"
    assert summary["denominator_inventory_row_count"] == 6
    assert summary["available_denominator_row_count"] == 6
    rows = _read_csv(tmp_path / "out" / "denominator_inventory_rows.csv")
    l2_rows = [row for row in rows if row["profile_label"] == "L2_window_50"]
    assert l2_rows
    assert set(row["support_absence_semantics"] for row in l2_rows) == {
        "profile_not_in_m2138_success_support_union"
    }
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["winner_or_rank_computed"] is False


def test_materialization_records_missing_denominator(tmp_path: Path) -> None:
    source_rows = [
        _source_row("source_a", "L0_current_masked"),
        _source_row("source_a", "L1_one_step"),
        _source_row("source_a", "L2_window_50"),
    ]
    inputs = _write_inputs(tmp_path, source_rows=source_rows)

    summary = inventory.materialize_denominator_inventory(
        protocol_summary_path=inputs[0],
        panel_units_path=inputs[1],
        support_matrix_path=inputs[2],
        protocol_claim_boundary_path=inputs[3],
        profile_source_kind_path=inputs[4],
        measured_summary_path=inputs[5],
        profile_aggregate_path=inputs[6],
        measured_claim_boundary_path=inputs[7],
        output_dir=tmp_path / "out",
        expected_panel_units=2,
        expected_profile_count=3,
        expected_denominator_count=6,
    )

    assert summary["result_class"] == "comparison_support_denominator_source_inventory_fail"
    assert summary["missing_denominator_row_count"] == 3


def test_materialization_fails_on_claim_boundary_violation(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path, claim_admissible=True)

    summary = inventory.materialize_denominator_inventory(
        protocol_summary_path=inputs[0],
        panel_units_path=inputs[1],
        support_matrix_path=inputs[2],
        protocol_claim_boundary_path=inputs[3],
        profile_source_kind_path=inputs[4],
        measured_summary_path=inputs[5],
        profile_aggregate_path=inputs[6],
        measured_claim_boundary_path=inputs[7],
        output_dir=tmp_path / "out",
        expected_panel_units=2,
        expected_profile_count=3,
        expected_denominator_count=6,
    )

    assert summary["result_class"] == "comparison_support_denominator_source_inventory_fail"
    assert summary["claim_boundary_violation_count"] == 1
