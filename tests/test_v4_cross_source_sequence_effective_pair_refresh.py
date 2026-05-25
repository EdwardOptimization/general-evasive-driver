from __future__ import annotations

from autodrift.v4_cross_source_sequence_effective_pair_refresh import (
    build_cross_source_pair_rows_from_boundary,
    classify_cross_source_pair_refresh,
)


def _boundary_row(candidate_id: int, source_group: int, seed: int, fault: str, steer: float, lateral: float) -> dict[str, str]:
    return {
        "candidate_id": str(candidate_id),
        "source_group_id": str(source_group),
        "seed": str(seed),
        "step": "21",
        "warmup_mode": "brake_tap",
        "preferred_fault_family": fault,
        "preferred_fidelity_class": "current_model_fault",
        "fault_onset_bucket": "pre_emergency",
        "boundary_axis": "obstacle_lateral_offset",
        "margin_band": "strict",
        "success": "True",
        "collision": "False",
        "accepted_primary": "True",
        "min_clearance_margin": "0.01",
        "first_steer": str(steer),
        "first_throttle": "0.1",
        "first_brake": "0.0",
        "target_obstacle_body_x": "14.0",
        "target_obstacle_body_y": str(lateral),
        "target_obstacle_half_width": "1.0",
    }


def test_build_cross_source_pair_rows_requires_distinct_sources_and_action_gap() -> None:
    rows = [
        _boundary_row(1, 10, 78052, "global_mu_drop", 0.10, -1.0),
        _boundary_row(2, 11, 78053, "steering_fault", 0.13, -1.02),
        _boundary_row(3, 10, 78052, "global_mu_drop", 0.12, -1.01),
    ]

    candidates, selected, rejected = build_cross_source_pair_rows_from_boundary(
        rows,
        max_pairs=8,
        boundary_margin_threshold=0.05,
        min_first_action_l2=0.014,
        max_obstacle_distance=0.1,
        max_pairs_per_left_source_group=8,
        max_pairs_per_right_source_group=8,
        max_pairs_per_left_seed=8,
        max_pairs_per_fault_family_pair=8,
        max_pairs_per_left_fault_family=8,
    )

    assert candidates
    assert selected
    assert all(pair["left_source_group_id"] != pair["right_source_group_id"] for pair in selected)
    assert all(float(pair["first_action_l2"]) >= 0.014 for pair in selected)
    assert any(row.get("rejection_reason") == "same_source_group" for row in rejected)


def test_classify_cross_source_pair_refresh_identifies_sparse_pair_positive() -> None:
    accepted = []
    for i in range(42):
        direction_family = "pair_delta" if i < 12 else f"axis_{i % 3}"
        accepted.append(
            {
                "left_source_group_id": str(i % 6),
                "left_seed": str(i % 4),
                "left_fault_family": f"fault_{i % 5}",
                "right_fault_family": f"right_{i % 4}",
                "left_warmup_mode": f"warmup_{i % 3}",
                "right_warmup_mode": "same",
                "left_onset_bucket": f"onset_{i % 5}",
                "right_onset_bucket": "same",
                "direction_family": direction_family,
                "hold_steps": str(4 + 2 * (i % 2)),
            }
        )
    pair_delta = [row for row in accepted if row["direction_family"] == "pair_delta"]

    result = classify_cross_source_pair_refresh(
        actor_changed=False,
        residual_changed=False,
        paired_candidate_rows=64,
        reconstructed_pair_rows=24,
        accepted_rows=accepted,
        accepted_pair_delta_rows=pair_delta,
        all_rows=[{"abs_margin_delta": 0.02, "success_flip": False, "collision_flip": False, "direction_family": "pair_delta"}],
        margin_delta_threshold=0.01,
        strong_min_rows=120,
        sparse_min_rows=40,
        min_pair_candidate_rows=40,
        min_reconstructed_pair_rows=20,
        min_pair_delta_rows=30,
        min_left_sources=10,
        min_left_seeds=4,
        min_left_fault_families=5,
        min_fault_pairs=8,
        min_warmup_pairs=3,
        min_onset_pairs=5,
        min_hold_steps=2,
        min_direction_families=3,
        max_left_source_dominance=0.30,
        max_left_seed_dominance=0.35,
        max_direction_family_dominance=0.55,
    )

    assert result == "v4_cross_source_sequence_effective_pair_refresh_sparse_pair_positive"


def test_classify_cross_source_pair_refresh_flags_pair_construction_failure() -> None:
    result = classify_cross_source_pair_refresh(
        actor_changed=False,
        residual_changed=False,
        paired_candidate_rows=8,
        reconstructed_pair_rows=8,
        accepted_rows=[],
        accepted_pair_delta_rows=[],
        all_rows=[],
        margin_delta_threshold=0.01,
        strong_min_rows=120,
        sparse_min_rows=40,
        min_pair_candidate_rows=40,
        min_reconstructed_pair_rows=20,
        min_pair_delta_rows=30,
        min_left_sources=10,
        min_left_seeds=4,
        min_left_fault_families=5,
        min_fault_pairs=8,
        min_warmup_pairs=3,
        min_onset_pairs=5,
        min_hold_steps=2,
        min_direction_families=3,
        max_left_source_dominance=0.30,
        max_left_seed_dominance=0.35,
        max_direction_family_dominance=0.55,
    )

    assert result == "v4_cross_source_sequence_effective_pair_refresh_pair_construction_failed"
