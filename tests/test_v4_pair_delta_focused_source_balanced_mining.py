from __future__ import annotations

from autodrift.v4_pair_delta_focused_source_balanced_mining import (
    balance_pair_delta_rows,
    classify_pair_delta_focused_mining,
    pair_rows_from_candidate_rows,
)


def _boundary_row(candidate_id: int, source_group: int) -> dict[str, str]:
    return {
        "candidate_id": str(candidate_id),
        "source_group_id": str(source_group),
        "seed": "78052",
        "step": "21",
        "target_obstacle_body_x": "14.0",
        "target_obstacle_body_y": "-1.0",
        "target_obstacle_half_width": "1.0",
    }


def test_pair_rows_from_candidate_rows_hydrates_boundary_plans() -> None:
    candidates = [
        {
            "pair_id": "1",
            "left_candidate_id": "10",
            "right_candidate_id": "11",
            "left_source_group_id": "3",
            "right_source_group_id": "4",
            "left_seed": "78052",
            "right_seed": "78053",
            "left_fault_family": "global_mu_drop",
            "right_fault_family": "steering_fault",
            "first_action_l2": "0.02",
            "obstacle_geometry_distance": "0.01",
            "normal_margin_gap_abs": "0.0",
        }
    ]

    selected, rejected = pair_rows_from_candidate_rows(
        candidates,
        [_boundary_row(10, 3), _boundary_row(11, 4)],
        max_replay_pairs=8,
        min_first_action_l2=0.014,
        max_pairs_per_left_source_group=8,
        max_pairs_per_right_source_group=8,
        max_pairs_per_left_seed=8,
        max_pairs_per_fault_family_pair=8,
    )

    assert len(selected) == 1
    assert not rejected
    assert selected[0]["left_plan"]["candidate_id"] == "10"
    assert selected[0]["right_step"] == 21


def test_balance_pair_delta_rows_caps_dominant_source() -> None:
    rows = []
    for i in range(10):
        rows.append(
            {
                "pair_id": str(i),
                "left_source_group_id": "dominant",
                "left_seed": str(i % 2),
                "left_fault_family": "global_mu_drop",
                "right_fault_family": "steering_fault",
                "direction": "pair_delta_negative",
                "abs_margin_delta": str(0.02 - i * 0.001),
            }
        )

    balanced = balance_pair_delta_rows(
        rows,
        max_rows_per_left_source_group=3,
        max_rows_per_left_seed=10,
        max_rows_per_left_fault_family=10,
        max_rows_per_fault_family_pair=10,
        max_rows_per_direction=10,
    )

    assert len(balanced) == 3


def test_classify_pair_delta_focused_mining_sparse_positive() -> None:
    rows = []
    for i in range(32):
        rows.append(
            {
                "left_source_group_id": str(i % 5),
                "left_seed": str(i % 3),
                "left_fault_family": f"fault_{i % 3}",
                "right_fault_family": f"right_{i % 6}",
                "left_warmup_mode": "warmup",
                "right_warmup_mode": "same",
                "left_onset_bucket": "onset",
                "right_onset_bucket": "same",
                "direction_family": "pair_delta",
                "direction": "pair_delta_positive" if i % 2 else "pair_delta_negative",
                "hold_steps": str(4 + 2 * (i % 2)),
                "abs_margin_delta": "0.02",
            }
        )

    result = classify_pair_delta_focused_mining(
        actor_changed=False,
        residual_changed=False,
        accepted_pair_delta_rows=rows,
        balanced_pair_delta_rows=rows,
        all_pair_delta_rows=rows,
        margin_delta_threshold=0.01,
        strong_min_rows=60,
        sparse_min_rows=30,
        min_left_sources=8,
        min_left_seeds=4,
        min_left_fault_families=5,
        min_fault_pairs=10,
        min_hold_steps=2,
        max_left_source_dominance=0.30,
        max_left_seed_dominance=0.35,
        max_direction_dominance=0.60,
    )

    assert result == "v4_pair_delta_focused_source_balanced_mining_sparse_pair_delta_positive"
