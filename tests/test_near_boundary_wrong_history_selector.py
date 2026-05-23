import pandas as pd

from autodrift.near_boundary_wrong_history_selector import (
    classify_near_boundary_wrong_history,
    summarize_near_boundary_selection,
)


def _row(
    *,
    normal_margin: float,
    margin_gap: float,
    success_drop: bool = False,
    collision_gap: bool = False,
    obstacle_completion_drop: bool = False,
    return_gap: float = 0.0,
    action_prefilter: bool = True,
    probe_seed: int = 100,
    label: str = "drift_required",
    target: str = "future_yaw_response",
) -> dict:
    return {
        "variant": "wrong_matched_history",
        "matched_current_pass": True,
        "normal_success": True,
        "normal_margin": normal_margin,
        "margin_gap": margin_gap,
        "success_drop": success_drop,
        "collision_gap": collision_gap,
        "obstacle_completion_drop": obstacle_completion_drop,
        "return_gap": return_gap,
        "action_prefilter_pass": action_prefilter,
        "probe_seed": probe_seed,
        "left_obstacle_label": label,
        "target": target,
    }


def test_near_boundary_margin_degradation_is_proof_candidate():
    frame = pd.DataFrame([_row(normal_margin=0.3, margin_gap=0.04)])

    classified = classify_near_boundary_wrong_history(
        frame,
        normal_margin_ceiling=0.75,
        min_margin_gap=0.02,
        min_return_gap_for_completion_drop=1.0,
        require_action_prefilter=True,
    )
    row = classified.iloc[0]

    assert bool(row["near_boundary_candidate"])
    assert bool(row["margin_degradation"])
    assert bool(row["proof_candidate"])
    assert not bool(row["high_slack_diagnostic"])


def test_high_slack_margin_row_is_diagnostic_not_proof():
    frame = pd.DataFrame([_row(normal_margin=4.0, margin_gap=0.10)])

    classified = classify_near_boundary_wrong_history(
        frame,
        normal_margin_ceiling=0.75,
        min_margin_gap=0.02,
        min_return_gap_for_completion_drop=1.0,
        require_action_prefilter=True,
    )
    row = classified.iloc[0]

    assert not bool(row["near_boundary_candidate"])
    assert not bool(row["proof_candidate"])
    assert bool(row["high_slack_diagnostic"])


def test_near_boundary_no_effect_is_kept_separate():
    frame = pd.DataFrame([_row(normal_margin=0.2, margin_gap=0.0, action_prefilter=False)])

    classified = classify_near_boundary_wrong_history(
        frame,
        normal_margin_ceiling=0.75,
        min_margin_gap=0.02,
        min_return_gap_for_completion_drop=1.0,
        require_action_prefilter=True,
    )
    row = classified.iloc[0]

    assert bool(row["near_boundary_candidate"])
    assert bool(row["near_boundary_no_effect"])
    assert not bool(row["proof_candidate"])


def test_summary_requires_source_diverse_outcome_degradation():
    rows = [
        _row(normal_margin=0.3, margin_gap=0.04, probe_seed=100, label="drift_required", target="future_yaw_response"),
        _row(normal_margin=0.4, margin_gap=0.03, probe_seed=200, label="unavoidable", target="future_yaw_response"),
        _row(
            normal_margin=0.5,
            margin_gap=0.00,
            collision_gap=True,
            probe_seed=300,
            label="drift_required",
            target="future_braking_deceleration",
        ),
        _row(
            normal_margin=0.6,
            margin_gap=0.00,
            success_drop=True,
            probe_seed=200,
            label="unavoidable",
            target="future_braking_deceleration",
        ),
    ]
    classified = classify_near_boundary_wrong_history(
        pd.DataFrame(rows),
        normal_margin_ceiling=0.75,
        min_margin_gap=0.02,
        min_return_gap_for_completion_drop=1.0,
        require_action_prefilter=True,
    )

    summary = summarize_near_boundary_selection(
        classified,
        min_proof_rows=4,
        min_probe_seed_count=3,
        min_obstacle_label_count=2,
        min_target_count=2,
        min_success_or_collision_or_completion_rows=2,
        max_single_seed_share=0.5,
        max_single_label_share=0.6,
    )

    assert summary["proof_candidate_count"] == 4
    assert summary["proof_success_or_collision_or_completion_rows"] == 2
    assert summary["wrong_history_gate_pass"]
