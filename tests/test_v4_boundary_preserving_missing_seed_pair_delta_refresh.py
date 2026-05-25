from __future__ import annotations

from autodrift.v4_boundary_preserving_missing_seed_pair_delta_refresh import (
    classify_boundary_preserving_refresh,
    classify_normal_boundary_row,
    make_normal_candidate_pair,
    retargeted_left_plan,
    select_normal_boundary_candidates,
)


def test_classify_normal_boundary_row() -> None:
    assert (
        classify_normal_boundary_row(success=True, collision=False, margin=0.01, boundary_margin_threshold=0.03)
        == "accepted_window"
    )
    assert (
        classify_normal_boundary_row(success=True, collision=False, margin=0.04, boundary_margin_threshold=0.03)
        == "wide_safe"
    )
    assert (
        classify_normal_boundary_row(success=False, collision=True, margin=-0.01, boundary_margin_threshold=0.03)
        == "collision_or_negative"
    )


def test_retargeted_left_plan_changes_only_selected_axis() -> None:
    pair = {
        "left_plan": {
            "target_obstacle_body_x": "12.0",
            "target_obstacle_body_y": "-0.5",
            "target_obstacle_half_width": "1.0",
        }
    }

    lateral, lateral_target = retargeted_left_plan(pair, axis="obstacle_lateral_offset", delta=0.2)
    timing, timing_target = retargeted_left_plan(pair, axis="obstacle_timing", delta=-1.0)
    width, width_target = retargeted_left_plan(pair, axis="obstacle_half_width", delta=0.1)

    assert lateral["target_obstacle_body_y"] == -0.3
    assert timing["target_obstacle_body_x"] == 11.0
    assert width["target_obstacle_half_width"] == 1.1
    assert lateral_target["retarget_target_body_x"] == 12.0
    assert timing_target["retarget_target_body_y"] == -0.5
    assert width_target["retarget_target_half_width"] == 1.1


def test_make_normal_candidate_pair_assigns_metadata() -> None:
    pair = {
        "pair_id": 3,
        "left_plan": {
            "target_obstacle_body_x": "10.0",
            "target_obstacle_body_y": "0.0",
            "target_obstacle_half_width": "1.0",
        },
    }

    candidate = make_normal_candidate_pair(
        pair,
        normal_candidate_id=7,
        axis="obstacle_timing",
        delta=-0.5,
        source="initial_grid",
    )

    assert candidate["pair_id"] == 30007
    assert candidate["normal_candidate_id"] == 7
    assert candidate["normal_boundary_source"] == "initial_grid"
    assert candidate["retarget_axis"] == "obstacle_timing"
    assert candidate["retarget_target_body_x"] == 9.5


def test_select_normal_boundary_candidates_balances_seed_and_axis() -> None:
    rows_and_pairs = []
    for index in range(18):
        row = {
            "normal_boundary_class": "accepted_window",
            "normal_margin": str(0.001 * (index + 1)),
            "left_seed": str(index % 3),
            "retarget_axis": "obstacle_lateral_offset" if index % 2 else "obstacle_timing",
            "normal_candidate_id": str(index),
        }
        rows_and_pairs.append((row, {"pair_id": index, **row}))

    selected = select_normal_boundary_candidates(
        rows_and_pairs,
        max_rows=12,
        max_rows_per_seed=4,
        max_rows_per_axis=6,
    )

    assert len(selected) == 12
    assert {row["left_seed"] for row in selected} == {"0", "1", "2"}
    assert {row["retarget_axis"] for row in selected} == {"obstacle_lateral_offset", "obstacle_timing"}


def test_classify_boundary_preserving_refresh_normal_boundary_limited() -> None:
    result = classify_boundary_preserving_refresh(
        actor_changed=False,
        residual_changed=False,
        target_weak_seed_rows=24,
        normal_boundary_candidate_rows=[{"left_seed": "78048", "retarget_axis": "obstacle_timing"}],
        pair_delta_sequence_rows=[],
        new_accepted_pair_delta_rows=[],
        balanced_pair_delta_rows=[],
        margin_delta_threshold=0.01,
        min_target_rows=24,
        min_normal_boundary_rows=24,
        min_normal_boundary_seeds=3,
        min_new_accepted_rows=24,
        min_balanced_rows=36,
        min_balanced_seeds=3,
        min_balanced_sources=6,
        min_balanced_fault_families=5,
        min_balanced_fault_pairs=8,
        max_seed_dominance=0.45,
        max_direction_dominance=0.65,
        max_axis_pair_dominance=0.85,
    )

    assert result == "v4_boundary_preserving_missing_seed_pair_delta_refresh_normal_boundary_limited"
