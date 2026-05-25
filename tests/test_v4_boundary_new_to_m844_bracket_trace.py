from __future__ import annotations

from autodrift.v4_boundary_new_to_m844_bracket_trace import (
    classify_axis_trace,
    classify_bracket_trace_result,
    outcome_class,
    select_trace_source_rows,
    summarize_axis_trace,
)


def _trace_row(parameter: float, margin: float, *, grid: str = "initial", success: bool = True, collision: bool = False) -> dict[str, object]:
    row = {
        "parameter_value": parameter,
        "grid_family": grid,
        "reconstructed": True,
        "success": success,
        "collision": collision,
        "min_clearance_margin": margin,
        "source_group_id": 1,
        "seed": 78048,
        "step": 21,
        "preferred_fault_family": "steering_fault",
        "warmup_mode": "brake_tap",
        "source_target_class": "new_underrepresented_boundary",
        "boundary_source_status": "boundary_new_to_m844",
        "trace_role": "primary_boundary_new_to_m844",
        "boundary_axis": "obstacle_lateral_offset",
    }
    row["outcome_class"] = outcome_class(row, boundary_margin_threshold=0.05)
    return row


def test_outcome_class_separates_boundary_wide_and_negative() -> None:
    assert outcome_class(_trace_row(0.0, 0.01), boundary_margin_threshold=0.05) == "safe_boundary"
    assert outcome_class(_trace_row(0.0, 0.10), boundary_margin_threshold=0.05) == "safe_wide"
    assert outcome_class(_trace_row(0.0, -0.01, success=False, collision=True), boundary_margin_threshold=0.05) == "negative"
    assert outcome_class({"reconstructed": False}, boundary_margin_threshold=0.05) == "ambiguous"


def test_classify_axis_trace_detects_extended_acceptance() -> None:
    rows = [
        _trace_row(-0.4, 0.20, grid="initial"),
        _trace_row(0.0, 0.10, grid="initial"),
        _trace_row(0.4, 0.02, grid="extended"),
    ]

    assert classify_axis_trace(rows) == "accepted_boundary_found_extended"
    summary = summarize_axis_trace(rows)
    assert summary["cause_class"] == "accepted_boundary_found_extended"
    assert summary["recommended_next"] == "bounded_boundary_expansion"


def test_classify_axis_trace_detects_all_safe_wide() -> None:
    rows = [_trace_row(-0.4, 0.20), _trace_row(0.0, 0.10), _trace_row(0.4, 0.08)]

    assert classify_axis_trace(rows) == "all_safe_wide"


def test_select_trace_source_rows_primary_and_control() -> None:
    targets = [
        {
            "source_group_id": "1",
            "step": "21",
            "seed": "78048",
            "preferred_fault_family": "steering_fault",
            "boundary_source_status": "boundary_new_to_m844",
            "source_target_class": "new_underrepresented_boundary",
        },
        {
            "source_group_id": "2",
            "step": "21",
            "seed": "78049",
            "preferred_fault_family": "mass_cg_shift",
            "boundary_source_status": "existing_boundary_recovered",
            "source_target_class": "new_underrepresented_boundary",
        },
    ]
    accepted = [{"source_group_id": "2"}]

    selected = select_trace_source_rows(
        targets,
        accepted,
        max_primary_sources=8,
        control_existing_boundary_sources=1,
    )

    assert [row["source_group_id"] for row in selected] == ["1", "2"]
    assert selected[0]["trace_role"] == "primary_boundary_new_to_m844"
    assert selected[1]["trace_role"] == "control_existing_boundary_recovered"


def test_classify_bracket_trace_result_actionable_extended_boundary() -> None:
    rows = []
    for index in range(12):
        rows.append(
            {
                "trace_role": "primary_boundary_new_to_m844",
                "cause_class": "accepted_boundary_found_extended",
                "source_group_id": str(index % 6),
                "preferred_fault_family": f"fault_{index % 4}",
            }
        )
    for index in range(88):
        rows.append(
            {
                "trace_role": "primary_boundary_new_to_m844",
                "cause_class": "all_safe_wide",
                "source_group_id": str(index + 20),
                "preferred_fault_family": "other",
            }
        )

    assert (
        classify_bracket_trace_result(
            actor_changed=False,
            residual_changed=False,
            target_sources=40,
            traced_source_axis_rows=100,
            trace_rows=1000,
            cause_classified_share=1.0,
            axis_summary_rows=rows,
            min_target_sources=40,
            min_source_axis_rows=100,
            min_trace_rows=1000,
            min_cause_classified_share=0.95,
            min_extended_accept_axes=12,
            min_extended_accept_source_groups=6,
            min_extended_accept_fault_families=4,
            all_safe_share_threshold=0.60,
            all_collision_share_threshold=0.60,
            ambiguous_share_threshold=0.20,
        )
        == "v4_boundary_new_to_m844_bracket_trace_actionable_extended_boundary"
    )
