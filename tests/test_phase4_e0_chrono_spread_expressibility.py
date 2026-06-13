from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import chrono_spread_expressibility_audit as e0  # noqa: E402


def test_axis_table_admits_vehicle_fixture_and_blocks_cg_height() -> None:
    table = e0.build_axis_table()
    by_axis = {row["axis"]: row for row in table}

    assert by_axis["vehicle_model_fixture"]["current_status"] == "admitted_for_e1_primary_population_axis"
    assert by_axis["vehicle_model_fixture"]["control_class"] == "discrete_reset_time_selector"
    assert by_axis["payload_position_or_cg_height"]["current_status"] == "blocked_requires_connector"
    assert "mass" in by_axis["payload_position_or_cg_height"]["forbidden_interpretation"].lower()
    assert by_axis["target_total_mass"]["current_status"] == "admitted_with_limits"


def test_e0_decision_requires_variant_probe_passes() -> None:
    table = e0.build_axis_table()
    passing_rows = [
        {"variant_id": variant, "pass": True}
        for variant in e0.FULL_VARIANTS
    ]
    failing_rows = [
        {"variant_id": e0.FULL_VARIANTS[0], "pass": True},
        {"variant_id": e0.FULL_VARIANTS[1], "pass": False},
    ]

    assert e0.evaluate_decision(table, passing_rows)["status_pass"] is True
    failed = e0.evaluate_decision(table, failing_rows)
    assert failed["status_pass"] is False
    assert failed["all_variants_pass"] is False


def test_e1_envelope_lists_blocked_axes() -> None:
    table = e0.build_axis_table()
    rows = [{"variant_id": variant, "pass": True} for variant in e0.FULL_VARIANTS]
    envelope = e0.build_e1_envelope(table, rows)
    blocked = {row["axis"] for row in envelope["blocked_without_new_connector"]}

    assert "payload_position_or_cg_height" in blocked
    assert "continuous_lf_lr_iz_cf_cr" in blocked
    assert "tire_model_family" in blocked
    assert envelope["recommended_e1_population_panel"]["vehicle_variants"] == list(e0.FULL_VARIANTS)
