from pathlib import Path

import pytest

from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight
    as m2866,
)


def test_m2866_weight_rows_match_design_and_normalize_mean_one() -> None:
    rows = m2866.build_response_loss_weight_rows()
    normalized = [float(row["normalized_weight"]) for row in rows]

    assert len(rows) == 36
    assert sum(normalized) / len(normalized) == pytest.approx(1.0)
    assert m2866.weight_rows_match_m2864(rows)
    assert all(bool(row["within_allowed_range"]) for row in rows)


def test_m2866_surface_accounting_separates_public_and_fresh_rows() -> None:
    telemetry_rows = [
        {
            "surface_id": "m2850_explanatory",
            "public_diagnostic_row": "True",
            "fresh_or_disjoint": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "surface_id": "fresh_disjoint",
            "public_diagnostic_row": "False",
            "fresh_or_disjoint": "True",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
    ]

    rows = m2866.build_surface_accounting_rows(telemetry_rows, Path("surface.csv"))

    public = next(row for row in rows if row["surface_id"] == "m2850_explanatory")
    fresh = next(row for row in rows if row["surface_id"] == "fresh_disjoint")
    assert public["public_explanatory"] is True
    assert fresh["fresh_or_disjoint"] is True
    assert all(row["status_pass"] for row in rows)


def test_m2866_rollback_gate_triggers_when_fresh_surface_missing() -> None:
    weight_rows = m2866.build_response_loss_weight_rows()
    valid_mask_rows = [
        {
            "status_pass": True,
        }
    ]
    surface_rows = [
        {
            "row_count": 16,
            "public_explanatory": True,
            "fresh_or_disjoint": False,
            "status_pass": True,
        }
    ]

    rows = m2866.build_rollback_gate_rows(
        weight_rows=weight_rows,
        valid_mask_rows=valid_mask_rows,
        surface_accounting_rows=surface_rows,
    )

    public_gate = next(row for row in rows if row["rollback_gate_id"] == "rollback_public_only_improvement_fresh_regression")
    assert public_gate["triggered"] is True
    assert public_gate["status_pass"] is False
