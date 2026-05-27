import pandas as pd
import pytest

from autodrift.row15_promoted_unsafe_margin_projection_probe import (
    DEFAULT_FIRST_REPLAY_SURFACES,
    alpha_failed_rows_pass,
    classify_projection_result,
    group_failed_rows_by_surface,
    validate_failed_rows_frame,
)


def _failed_rows_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "surface": "m267_m264",
                "row_id": 15,
                "target": "future_braking_deceleration",
                "physical_pair_key": "9530:21:9550:21",
                "left_seed": 9530,
                "right_seed": 9550,
                "left_step": 21,
                "right_step": 21,
                "relocated_obstacle_body_x": 9.6,
                "relocated_obstacle_body_y": -0.9,
                "relocated_obstacle_half_width": 0.7,
            },
            {
                "surface": "row15_promoted_materialized",
                "row_id": 70,
                "target": "future_braking_deceleration",
                "physical_pair_key": "113201:21:113230:48",
                "left_seed": 113201,
                "right_seed": 113230,
                "left_step": 21,
                "right_step": 48,
                "relocated_obstacle_body_x": 5.5,
                "relocated_obstacle_body_y": -1.7,
                "relocated_obstacle_half_width": 1.4,
            },
        ]
    )


def test_validate_failed_rows_frame_requires_surface_and_boundary_columns():
    frame = _failed_rows_frame().drop(columns=["surface"])

    with pytest.raises(ValueError, match="surface"):
        validate_failed_rows_frame(frame)


def test_group_failed_rows_by_surface_preserves_arbitrary_surface_labels():
    groups = group_failed_rows_by_surface(_failed_rows_frame())

    assert sorted(groups) == ["m267_m264", "row15_promoted_materialized"]
    assert groups["m267_m264"].iloc[0]["row_id"] == 15
    assert groups["row15_promoted_materialized"].iloc[0]["row_id"] == 70


def test_alpha_failed_rows_pass_requires_all_failed_rows_and_nonzero_alpha():
    rows = [
        {"alpha": 0.0, "failed_row_unsafe_margin_pass": True},
        {"alpha": 0.0, "failed_row_unsafe_margin_pass": True},
        {"alpha": 0.1, "failed_row_unsafe_margin_pass": True},
        {"alpha": 0.1, "failed_row_unsafe_margin_pass": True},
        {"alpha": 0.2, "failed_row_unsafe_margin_pass": True},
        {"alpha": 0.3, "failed_row_unsafe_margin_pass": True},
        {"alpha": 0.3, "failed_row_unsafe_margin_pass": False},
    ]

    result = alpha_failed_rows_pass(rows, failed_row_count=2)

    assert result[0.0] is False
    assert result[0.1] is True
    assert result[0.2] is False
    assert result[0.3] is False


def test_classify_projection_result_matches_m1152_decision_classes():
    assert classify_projection_result(selected=None, first_replay_pass=False) == (
        "row15_promoted_unsafe_margin_projection_no_candidate",
        "terminal_margin_objective_design",
        ["proof_washout"],
    )
    assert classify_projection_result(selected={"alpha": 0.1}, first_replay_pass=False) == (
        "row15_promoted_unsafe_margin_projection_first_replay_failed",
        "row15_promoted_unsafe_margin_projection_first_replay_failure_audit",
        ["proof_washout"],
    )
    assert classify_projection_result(selected={"alpha": 0.1}, first_replay_pass=True) == (
        "row15_promoted_unsafe_margin_projection_first_replay_candidate",
        "family_intersection_and_behavior_diagnostic_design_only",
        ["none"],
    )


def test_default_first_replay_surfaces_are_m1149_scope_not_old_single_row_scope():
    labels = [label for _, label, _ in DEFAULT_FIRST_REPLAY_SURFACES]

    assert len(labels) == 10
    assert "m267_m264" in labels
    assert "row15_promoted_materialized" in labels
