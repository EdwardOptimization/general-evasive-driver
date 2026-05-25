from __future__ import annotations

from autodrift.v4_generated_boundary_pair_delta_refresh import (
    balance_generated_pair_delta_rows,
    build_generated_boundary_pair_candidates,
    classify_generated_boundary_pair_delta_refresh,
)


def _generated_row(
    index: int,
    source_group: int,
    seed: int,
    fault: str,
    steer: float,
    lateral: float,
    *,
    axis: str = "obstacle_lateral_offset",
    accepted_primary: str = "",
) -> dict[str, str]:
    return {
        "candidate_id": "",
        "source_group_id": str(source_group),
        "seed": str(seed),
        "step": "21",
        "warmup_mode": "steer_pulse_left_right",
        "preferred_fault_family": fault,
        "preferred_fidelity_class": "current_model_proxy",
        "fault_onset_bucket": "pre_emergency",
        "boundary_axis": axis,
        "margin_band": "strict",
        "success": "True",
        "collision": "False",
        "accepted_primary": accepted_primary,
        "boundary_source_status": "boundary_new_to_m844",
        "min_clearance_margin": "0.012",
        "first_steer": str(steer),
        "first_throttle": "0.0",
        "first_brake": "0.0",
        "target_obstacle_body_x": "14.0",
        "target_obstacle_body_y": str(lateral),
        "target_obstacle_half_width": "1.0",
        "m867_fixture_index": str(index),
    }


def test_build_generated_boundary_pairs_handles_blank_candidate_and_accepted_primary() -> None:
    rows = [
        _generated_row(0, 10, 78050, "global_mu_drop", 0.10, -1.0),
        _generated_row(1, 11, 78051, "steering_fault", 0.13, -1.01),
        _generated_row(2, 10, 78050, "global_mu_drop", 0.16, -1.02),
    ]

    candidates, selected, rejected = build_generated_boundary_pair_candidates(
        rows,
        max_pairs=8,
        boundary_margin_threshold=0.05,
        min_first_action_l2=0.014,
        primary_max_obstacle_distance=0.10,
        diagnostic_max_obstacle_distance=0.20,
        max_pairs_per_left_source_group=8,
        max_pairs_per_right_source_group=8,
        max_pairs_per_left_seed=8,
        max_pairs_per_fault_family_pair=8,
        max_pairs_per_left_fault_family=8,
        max_pairs_per_boundary_axis_pair=8,
    )

    assert candidates
    assert selected
    assert all(pair["left_candidate_id"] >= 0 for pair in selected)
    assert all(pair["left_source_group_id"] != pair["right_source_group_id"] for pair in selected)
    assert all(pair["pairability_tier"] == "primary_0_10" for pair in selected)
    assert any(row.get("rejection_reason") == "same_source_group" for row in rejected)


def test_balance_generated_pair_delta_rows_caps_axis_pair_and_direction() -> None:
    rows = []
    for index in range(10):
        rows.append(
            {
                "pair_id": str(index),
                "left_source_group_id": str(index),
                "left_seed": str(index % 4),
                "left_fault_family": f"fault_{index % 3}",
                "right_fault_family": f"right_{index % 4}",
                "left_boundary_axis": "obstacle_lateral_offset",
                "right_boundary_axis": "obstacle_lateral_offset",
                "direction": "pair_delta_positive",
                "abs_margin_delta": str(0.04 - 0.001 * index),
            }
        )

    balanced = balance_generated_pair_delta_rows(
        rows,
        max_rows_per_left_source_group=8,
        max_rows_per_left_seed=8,
        max_rows_per_left_fault_family=8,
        max_rows_per_fault_family_pair=8,
        max_rows_per_direction=8,
        max_rows_per_axis_pair=3,
    )

    assert len(balanced) == 3


def test_classify_generated_boundary_pair_delta_refresh_sparse_positive() -> None:
    rows = []
    for index in range(32):
        rows.append(
            {
                "left_source_group_id": str(index % 5),
                "left_seed": str(index % 3),
                "left_fault_family": f"fault_{index % 3}",
                "right_fault_family": f"right_{index % 6}",
                "left_warmup_mode": "warmup",
                "right_warmup_mode": "warmup",
                "left_onset_bucket": "pre",
                "right_onset_bucket": "mid",
                "left_boundary_axis": "obstacle_lateral_offset",
                "right_boundary_axis": "obstacle_lateral_offset",
                "direction_family": "pair_delta",
                "direction": "pair_delta_positive" if index % 2 else "pair_delta_negative",
                "hold_steps": str(4 + 2 * (index % 2)),
                "abs_margin_delta": "0.02",
            }
        )

    result = classify_generated_boundary_pair_delta_refresh(
        actor_changed=False,
        residual_changed=False,
        pair_candidate_rows=140,
        selected_replay_pairs=90,
        pair_delta_sequence_rows=rows,
        accepted_pair_delta_rows=rows,
        balanced_pair_delta_rows=rows,
        margin_delta_threshold=0.01,
        strong_min_rows=60,
        sparse_min_rows=30,
        min_pair_candidate_rows=120,
        min_selected_replay_pairs=80,
        min_left_sources=8,
        min_left_seeds=4,
        min_left_fault_families=5,
        min_fault_pairs=10,
        min_hold_steps=2,
        max_left_source_dominance=0.30,
        max_left_seed_dominance=0.40,
        max_direction_dominance=0.60,
    )

    assert result == "v4_generated_boundary_pair_delta_refresh_sparse_pair_delta_positive"


def test_classify_generated_boundary_pair_delta_refresh_all_weak() -> None:
    result = classify_generated_boundary_pair_delta_refresh(
        actor_changed=False,
        residual_changed=False,
        pair_candidate_rows=140,
        selected_replay_pairs=90,
        pair_delta_sequence_rows=[
            {"abs_margin_delta": "0.002", "success_flip": "False", "collision_flip": "False", "direction_family": "pair_delta"}
        ],
        accepted_pair_delta_rows=[],
        balanced_pair_delta_rows=[],
        margin_delta_threshold=0.01,
        strong_min_rows=60,
        sparse_min_rows=30,
        min_pair_candidate_rows=120,
        min_selected_replay_pairs=80,
        min_left_sources=8,
        min_left_seeds=4,
        min_left_fault_families=5,
        min_fault_pairs=10,
        min_hold_steps=2,
        max_left_source_dominance=0.30,
        max_left_seed_dominance=0.40,
        max_direction_dominance=0.60,
    )

    assert result == "v4_generated_boundary_pair_delta_refresh_all_weak"
