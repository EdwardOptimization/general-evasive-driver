from __future__ import annotations

import csv
from pathlib import Path

from autodrift import paper_route_outcome_supported_decisive_comparison_support_comparison_protocol as protocol
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _panel_row(
    *,
    source_kind: str,
    profiles: str,
    intent: str = "collision_relief_probe",
    generated_proxy: bool = True,
) -> dict[str, object]:
    return {
        "panel_unit_id": f"panel_unit_{source_kind}",
        "panel_role": "primary_source_kind_unit",
        "canonical_selection_reason": "preferred_intent_source_kind",
        "candidate_key": f"candidate_{source_kind}",
        "qualification_label": "qualified_candidate",
        "slice_kind": "outcome_by_intent_source_kind",
        "support_label": "comparison_ready_candidate",
        "episode_count": 50,
        "success_count": 8,
        "collision_count": 4,
        "offtrack_outcome_count": 38,
        "success_rate": 0.16,
        "collision_rate": 0.08,
        "offtrack_outcome_rate": 0.76,
        "success_profile_count": len([item for item in profiles.split(";") if item]),
        "profiles_with_success": profiles,
        "success_source_count": 6,
        "sources_with_success": "s1;s2;s3;s4;s5;s6",
        "comparison_support_intent": intent,
        "target_support_tier": "",
        "source_kind": source_kind,
        "proxy_template_family": "",
        "generated_proxy_boundary_only": generated_proxy,
    }


def _write_inputs(tmp_path: Path, rows: list[dict[str, object]], *, claim_admissible: bool = False) -> tuple[Path, Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    panel_path = tmp_path / "controlled_panel_units.csv"
    excluded_path = tmp_path / "excluded.csv"
    claim_path = tmp_path / "claim_boundary.csv"
    write_json(summary_path, {"result_class": "comparison_support_controlled_panel_construction_pass"})
    write_csv_rows(panel_path, rows)
    write_csv_rows(
        excluded_path,
        [{"candidate_key": "broad", "exclusion_reason": "broad_aggregate_candidate"}],
        ["candidate_key", "exclusion_reason"],
    )
    write_csv_rows(
        claim_path,
        [
            {
                "claim": "controller_family_ranking",
                "admissible": claim_admissible,
                "reason": "test boundary",
            }
        ],
        ["claim", "admissible", "reason"],
    )
    return summary_path, panel_path, excluded_path, claim_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materializes_support_matrix_without_ranking(tmp_path: Path) -> None:
    rows = [
        _panel_row(source_kind="source_a", profiles="L1_one_step;L3_online_gru", intent="collision_relief_probe"),
        _panel_row(source_kind="source_b", profiles="L0_current_masked;L3_online_gru", intent="discriminative_boundary"),
    ]
    summary_path, panel_path, excluded_path, claim_path = _write_inputs(tmp_path, rows)

    summary = protocol.materialize_comparison_protocol(
        summary_path=summary_path,
        controlled_panel_units_path=panel_path,
        excluded_qualified_candidates_path=excluded_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_panel_units=2,
        min_profile_labels=3,
    )

    assert summary["result_class"] == "comparison_support_comparison_protocol_materialization_pass"
    assert summary["panel_unit_count"] == 2
    assert summary["profile_label_count"] == 3
    assert summary["support_matrix_row_count"] == 6
    assert summary["winner_or_rank_computed"] is False
    matrix_rows = _read_csv(tmp_path / "out" / "profile_support_matrix.csv")
    absent_rows = [row for row in matrix_rows if row["observed_success_support"] == "False"]
    assert absent_rows
    assert absent_rows[0]["absence_semantics"] == "no_success_support_observed_in_m2134_aggregate"
    metric_rows = _read_csv(tmp_path / "out" / "metric_contract.csv")
    blocked_metrics = {row["metric"] for row in metric_rows if row["admissible"] == "False"}
    assert "per_profile_success_rate" in blocked_metrics
    assert "winner_or_rank" in blocked_metrics


def test_materialization_fails_on_claim_boundary_violation(tmp_path: Path) -> None:
    rows = [
        _panel_row(source_kind="source_a", profiles="L1_one_step;L3_online_gru"),
        _panel_row(source_kind="source_b", profiles="L0_current_masked;L3_online_gru"),
    ]
    summary_path, panel_path, excluded_path, claim_path = _write_inputs(tmp_path, rows, claim_admissible=True)

    summary = protocol.materialize_comparison_protocol(
        summary_path=summary_path,
        controlled_panel_units_path=panel_path,
        excluded_qualified_candidates_path=excluded_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_panel_units=2,
        min_profile_labels=3,
    )

    assert summary["result_class"] == "comparison_support_comparison_protocol_materialization_fail"
    assert summary["claim_boundary_violation_count"] == 1
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["ranking_claim_made"] is False


def test_materialization_fails_on_direct_broad_aggregate_unit(tmp_path: Path) -> None:
    rows = [
        _panel_row(source_kind="source_a", profiles="L1_one_step;L3_online_gru"),
        _panel_row(source_kind="", profiles="L0_current_masked;L3_online_gru"),
    ]
    rows[1]["slice_kind"] = "outcome_by_intent"
    summary_path, panel_path, excluded_path, claim_path = _write_inputs(tmp_path, rows)

    summary = protocol.materialize_comparison_protocol(
        summary_path=summary_path,
        controlled_panel_units_path=panel_path,
        excluded_qualified_candidates_path=excluded_path,
        claim_boundary_path=claim_path,
        output_dir=tmp_path / "out",
        min_panel_units=2,
        min_profile_labels=3,
    )

    assert summary["result_class"] == "comparison_support_comparison_protocol_materialization_fail"
    assert summary["direct_broad_aggregate_panel_unit_count"] == 1
