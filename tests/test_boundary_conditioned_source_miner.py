import pandas as pd
import pytest

from autodrift.boundary_conditioned_source_miner import (
    boundary_acceptance,
    boundary_score,
    classify_source_rollouts,
    diversity_summary,
    request_left_snapshots,
    select_source_pool,
)


def test_select_source_pool_filters_deduplicates_and_keeps_indices():
    rows = pd.DataFrame(
        [
            _row(surface="ood", variant="wrong_matched_history", z=0.4, gap=2.0),
            _row(surface="ood", variant="wrong_matched_history", z=0.3, gap=1.0),
            _row(surface="ood", variant="shuffled_history", z=1.0, gap=1.0),
            _row(surface="fresh", variant="delayed_history", z=0.09, gap=9.0),
            {**_row(surface="fresh", variant="delayed_history", z=0.2, gap=1.0), "candidate_for_grounding": False},
        ]
    )

    selected = select_source_pool(
        rows,
        include_variants=("wrong_matched_history", "delayed_history"),
        min_capability_z_distance=0.10,
    )

    assert len(selected) == 1
    assert selected.loc[0, "source_index"] == 0
    assert selected.loc[0, "coupling_row_index"] == 0
    assert selected.loc[0, "capability_z_distance"] == 0.4


def test_request_left_snapshots_uses_unique_left_steps():
    rows = pd.DataFrame(
        [
            _row("ood", "wrong_matched_history", z=0.2, gap=1.0, left_seed=1, left_step=4),
            _row("ood", "delayed_history", z=0.2, gap=1.0, left_seed=1, left_step=6),
            _row("fresh", "delayed_history", z=0.2, gap=1.0, left_seed=2, left_step=6),
        ]
    )

    assert request_left_snapshots(rows) == {1: {4, 6}, 2: {6}}


def test_boundary_acceptance_prefers_collision_margin_or_high_risk():
    accepted, reason = boundary_acceptance(
        baseline={"collision": True, "off_road": False, "spin_out": False, "min_clearance_margin": -0.2},
        risk_threshold=1.0,
        margin_window=0.5,
    )
    assert accepted
    assert reason == "baseline_collision"

    accepted, reason = boundary_acceptance(
        baseline={"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": 0.4},
        risk_threshold=1.0,
        margin_window=0.5,
    )
    assert accepted
    assert reason == "baseline_margin_window"

    accepted, reason = boundary_acceptance(
        baseline={"collision": False, "off_road": True, "spin_out": False, "min_clearance_margin": -1.0},
        risk_threshold=1.0,
        margin_window=0.5,
    )
    assert not accepted
    assert reason == "baseline_off_road"


def test_boundary_score_increases_near_margin_and_high_risk():
    far = boundary_score(
        capability_z_distance=0.2,
        baseline_margin=2.0,
        baseline_risk_score=0.0,
        risk_min=0.0,
        risk_max=10.0,
        source_count=1,
        margin_window=0.5,
    )
    near = boundary_score(
        capability_z_distance=0.2,
        baseline_margin=-0.1,
        baseline_risk_score=10.0,
        risk_min=0.0,
        risk_max=10.0,
        source_count=1,
        margin_window=0.5,
    )
    duplicate = boundary_score(
        capability_z_distance=0.2,
        baseline_margin=-0.1,
        baseline_risk_score=10.0,
        risk_min=0.0,
        risk_max=10.0,
        source_count=4,
        margin_window=0.5,
    )

    assert near > far
    assert duplicate < near


def test_classify_source_rollouts_marks_boundary_and_far_rows():
    rows = pd.DataFrame(
        [
            _rollout_row(source_index=0, margin=2.0, risk=-2.0),
            _rollout_row(source_index=1, margin=0.4, risk=-0.4),
            _rollout_row(source_index=2, margin=1.0, risk=10.0),
        ]
    )

    boundary_rows, rejected_rows, threshold = classify_source_rollouts(
        rows,
        risk_quantile=0.75,
        margin_window=0.5,
    )

    assert threshold == pytest.approx(4.8)
    assert {row["source_index"] for row in boundary_rows} == {1, 2}
    assert {row["source_index"] for row in rejected_rows} == {0}


def test_diversity_summary_requires_source_diverse_boundary_rows():
    rows = pd.DataFrame(
        [
            {
                "left_seed": index,
                "left_step": index % 3,
                "right_seed": 100 + index,
                "right_step": index % 5,
                "surface": "ood" if index % 2 else "fresh",
                "variant": "wrong_matched_history" if index % 2 else "delayed_history",
                "target": "future_yaw_response" if index % 3 else "future_lateral_accel_response",
            }
            for index in range(24)
        ]
    )

    summary = diversity_summary(rows)

    assert summary.rows == 24
    assert summary.unique_physical_pairs == 24
    assert summary.unique_left_seeds == 24
    assert summary.surfaces == 2
    assert summary.variants == 2
    assert summary.targets == 2
    assert summary.pass_diversity


def _row(
    surface: str,
    variant: str,
    *,
    z: float,
    gap: float,
    left_seed: int = 10,
    left_step: int = 3,
    right_seed: int = 20,
    right_step: int = 4,
) -> dict[str, object]:
    return {
        "candidate_for_grounding": True,
        "surface": surface,
        "variant": variant,
        "target": "future_yaw_response",
        "capability_z_distance": z,
        "action_distance": 0.001,
        "coupling_gap": gap,
        "left_seed": left_seed,
        "left_step": left_step,
        "right_seed": right_seed,
        "right_step": right_step,
    }


def _rollout_row(source_index: int, margin: float, risk: float) -> dict[str, object]:
    return {
        "source_index": source_index,
        "coupling_row_index": source_index,
        "surface": "ood",
        "variant": "wrong_matched_history",
        "target": "future_yaw_response",
        "left_seed": source_index,
        "left_step": 3,
        "right_seed": 100 + source_index,
        "right_step": 4,
        "capability_z_distance": 0.2 + source_index,
        "action_distance": 0.001,
        "coupling_gap": 1.0,
        "baseline_collision": False,
        "baseline_off_road": False,
        "baseline_spin_out": False,
        "baseline_margin": margin,
        "baseline_risk_score": risk,
    }
