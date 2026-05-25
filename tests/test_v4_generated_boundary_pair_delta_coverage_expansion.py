from __future__ import annotations

from autodrift.v4_generated_boundary_pair_delta_coverage_expansion import (
    balance_coverage_pair_delta_rows,
    classify_coverage_expansion,
    retarget_candidate_rows,
    select_target_weak_seed_rows,
)


def test_select_target_weak_seed_rows_keeps_best_per_pair_and_seed() -> None:
    rows = []
    for index, seed in enumerate(["78048", "78055", "78057", "78058"]):
        for pair in range(3):
            rows.append(
                {
                    "pair_id": str(index * 10 + pair),
                    "left_seed": seed,
                    "normal_success": "True",
                    "normal_collision": "False",
                    "normal_margin": "0.01",
                    "abs_margin_delta": str(0.001 * (pair + 1)),
                    "direction": "pair_delta_negative",
                    "hold_steps": "6",
                    "epsilon_l2": "0.075",
                }
            )

    selected = select_target_weak_seed_rows(rows, max_targets_per_seed=2, max_normal_margin=0.03)

    assert len(selected) == 6
    assert {row["left_seed"] for row in selected} == {"78048", "78055", "78057"}
    assert all(row["target_best_direction"] == "pair_delta_negative" for row in selected)


def test_retarget_candidate_rows_generates_bounded_axis_variants() -> None:
    pairs = [
        {
            "pair_id": 7,
            "left_plan": {
                "target_obstacle_body_x": "14.0",
                "target_obstacle_body_y": "-0.5",
                "target_obstacle_half_width": "1.0",
            },
            "right_plan": {},
        }
    ]

    rows = retarget_candidate_rows(
        pairs,
        lateral_deltas=(-0.1, 0.1),
        timing_deltas=(-0.5,),
        half_width_deltas=(0.2,),
        max_retargets_per_target=4,
    )

    assert len(rows) == 4
    assert {row["retarget_axis"] for row in rows} == {"obstacle_lateral_offset", "obstacle_timing", "obstacle_half_width"}
    assert all(float(row["retarget_target_body_x"]) >= 1.0 for row in rows)


def test_balance_coverage_pair_delta_rows_balances_seed_direction_and_axis() -> None:
    rows = []
    for index in range(24):
        rows.append(
            {
                "pair_id": str(index),
                "left_seed": str(index % 3),
                "left_source_group_id": str(index % 6),
                "left_fault_family": f"fault_{index % 4}",
                "right_fault_family": f"right_{index % 5}",
                "left_boundary_axis": "obstacle_timing" if index % 4 == 0 else "obstacle_lateral_offset",
                "right_boundary_axis": "obstacle_lateral_offset",
                "direction": "pair_delta_positive" if index % 2 else "pair_delta_negative",
                "abs_margin_delta": str(0.05 - index * 0.001),
            }
        )

    balanced = balance_coverage_pair_delta_rows(
        rows,
        max_rows=18,
        max_rows_per_left_seed=6,
        max_rows_per_left_source_group=8,
        max_rows_per_fault_family_pair=8,
        max_rows_per_direction=9,
        max_rows_per_axis_pair=12,
    )

    assert len(balanced) == 18
    assert {row["left_seed"] for row in balanced} == {"0", "1", "2"}
    assert {row["direction"] for row in balanced} == {"pair_delta_positive", "pair_delta_negative"}


def test_classify_coverage_expansion_source_limited() -> None:
    target_rows = [{"left_seed": seed} for seed in ["78048", "78055", "78057"] for _ in range(8)]
    balanced = []
    for index in range(32):
        balanced.append(
            {
                "left_seed": str(index % 2),
                "left_source_group_id": str(index % 5),
                "left_fault_family": f"fault_{index % 5}",
                "right_fault_family": f"right_{index % 5}",
                "direction": "pair_delta_negative",
                "left_boundary_axis": "obstacle_lateral_offset",
                "right_boundary_axis": "obstacle_lateral_offset",
            }
        )

    result = classify_coverage_expansion(
        actor_changed=False,
        residual_changed=False,
        target_weak_seed_rows=target_rows,
        retarget_candidate_rows_count=120,
        retarget_replay_rows_count=240,
        pair_delta_sequence_rows=[{"abs_margin_delta": "0.02", "success_flip": "False", "collision_flip": "False"}],
        accepted_pair_delta_rows=balanced,
        balanced_pair_delta_rows=balanced,
        margin_delta_threshold=0.01,
        min_target_rows=24,
        min_target_seeds=3,
        min_retarget_candidates=96,
        min_accepted_rows=60,
        min_balanced_rows=36,
        min_balanced_seeds=3,
        min_balanced_sources=6,
        min_balanced_fault_families=5,
        min_balanced_fault_pairs=8,
        max_seed_dominance=0.45,
        max_direction_dominance=0.65,
        max_axis_pair_dominance=0.85,
    )

    assert result == "v4_generated_boundary_pair_delta_coverage_expansion_source_limited"
