from __future__ import annotations

from autodrift.v4_near_boundary_wrong_history_pair_mining import (
    build_near_boundary_pairs,
    margin_band,
    source_requests_from_plan_rows,
)


def test_source_requests_deduplicate_group_step() -> None:
    rows = [
        {"source_group_id": "1", "step": "20"},
        {"source_group_id": "1", "step": "20"},
        {"source_group_id": "2", "step": "23"},
    ]

    requests = source_requests_from_plan_rows(rows, max_source_snapshots=8)

    assert [(row["left_source_group_id"], row["left_step"]) for row in requests] == [(1, 20), (2, 23)]
    assert requests[0]["right_source_group_id"] == 1


def test_margin_band_thresholds() -> None:
    assert margin_band(0.003, strict_margin_threshold=0.02, boundary_margin_threshold=0.05) == "ultra_strict_0_005"
    assert margin_band(0.015, strict_margin_threshold=0.02, boundary_margin_threshold=0.05) == "strict"
    assert margin_band(0.04, strict_margin_threshold=0.02, boundary_margin_threshold=0.05) == "boundary"
    assert margin_band(0.2, strict_margin_threshold=0.02, boundary_margin_threshold=0.05) == "wide"


def _boundary_row(candidate_id: int, *, fault: str, seed: int, source: int, steer: float, margin: float) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source_group_id": source,
        "source_index": source,
        "seed": seed,
        "step": 25,
        "warmup_mode": "natural_policy",
        "preferred_fault_family": fault,
        "preferred_fidelity_class": "current_model_fault",
        "fault_onset_bucket": "pre_emergency",
        "boundary_axis": "obstacle_lateral_offset",
        "target_obstacle_body_x": 12.0,
        "target_obstacle_body_y": -1.0,
        "target_obstacle_half_width": 0.7,
        "ego_vx_norm": 0.8,
        "ego_vy_norm": 0.02,
        "ego_yaw_rate_norm": 0.1,
        "first_steer": steer,
        "first_throttle": 0.0,
        "first_brake": 0.1,
        "success": True,
        "collision": False,
        "min_clearance_margin": margin,
    }


def test_build_near_boundary_pairs_filters_wide_and_same_fault() -> None:
    rows = [
        _boundary_row(1, fault="brake_authority_drop", seed=10, source=1, steer=0.10, margin=0.01),
        _boundary_row(2, fault="steering_fault", seed=11, source=2, steer=0.14, margin=0.02),
        _boundary_row(3, fault="steering_fault", seed=12, source=3, steer=0.50, margin=0.20),
    ]

    selected, rejected = build_near_boundary_pairs(
        rows,
        max_pairs=8,
        max_ego_distance=0.25,
        max_obstacle_distance=0.08,
        min_first_action_l2=0.014,
        strict_margin_threshold=0.02,
        boundary_margin_threshold=0.05,
        max_rows_per_seed=8,
        max_rows_per_source_group=8,
        max_rows_per_fault_pair=8,
    )

    assert len(selected) == 1
    assert selected[0]["left_fault_family"] == "brake_authority_drop"
    assert selected[0]["right_fault_family"] == "steering_fault"
    assert all(row["right_candidate_id"] != 3 for row in selected)
    assert rejected == []
