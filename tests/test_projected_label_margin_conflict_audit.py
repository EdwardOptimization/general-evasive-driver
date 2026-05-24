import pandas as pd

from autodrift.projected_label_margin_conflict_audit import (
    build_label_margin_rows,
    build_margin_bucket_rows,
    summarize_label_margin_conflict,
)


def _rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "projected_obstacle_label": "unavoidable",
                "probe_seed": 1,
                "target": "future_yaw_response",
                "config": "short",
                "normal_min_clearance_margin": 0.4,
                "first_action_distance": 0.03,
                "action_trajectory_distance_mean": 0.04,
                "action_trajectory_distance_max": 0.05,
                "projection_l2": 1.0,
                "half_width_delta_abs": 0.1,
            },
            {
                "projected_obstacle_label": "drift_required",
                "probe_seed": 2,
                "target": "future_braking_deceleration",
                "config": "warmup",
                "normal_min_clearance_margin": 1.5,
                "first_action_distance": 0.04,
                "action_trajectory_distance_mean": 0.05,
                "action_trajectory_distance_max": 0.06,
                "projection_l2": 2.0,
                "half_width_delta_abs": 0.2,
            },
            {
                "projected_obstacle_label": "aeb_feasible",
                "probe_seed": 3,
                "target": "future_lateral_accel_response",
                "config": "short",
                "normal_min_clearance_margin": 9.0,
                "first_action_distance": 0.01,
                "action_trajectory_distance_mean": 0.01,
                "action_trajectory_distance_max": 0.01,
                "projection_l2": 9.0,
                "half_width_delta_abs": 0.3,
            },
        ]
    )


def test_build_label_margin_rows_reports_low_margin_soft_counts() -> None:
    rows = build_label_margin_rows(_rows())
    by_label = {row["projected_obstacle_label"]: row for row in rows}

    assert by_label["drift_required"]["margin_le_2_count"] == 1
    assert by_label["drift_required"]["soft_margin_le_2_count"] == 1
    assert by_label["aeb_feasible"]["margin_le_8_count"] == 0


def test_build_margin_bucket_rows_counts_labels_per_margin_bucket() -> None:
    rows = build_margin_bucket_rows(_rows())
    bucket = next(row for row in rows if row["margin_bucket"] == "(1,2]")

    assert bucket["by_projected_obstacle_label"] == {"drift_required": 1}
    assert bucket["soft_action_count"] == 1


def test_summarize_label_margin_conflict_recommends_selector_when_overlap_exists() -> None:
    summary = summarize_label_margin_conflict(
        source_pairs=_rows(),
        projected_pairs=_rows(),
        scored_pairs=_rows(),
        low_margin_threshold=2.0,
        non_unavoidable_label="unavoidable",
    )

    assert summary["low_margin_non_unavoidable_exists"]
    assert summary["soft_low_margin_non_unavoidable_count"] == 1
    assert summary["recommended_next_path"] == "selector_family_from_low_margin_non_unavoidable_rows"


def test_summarize_label_margin_conflict_recommends_gate_split_when_no_overlap() -> None:
    frame = _rows()
    frame.loc[frame["projected_obstacle_label"] != "unavoidable", "normal_min_clearance_margin"] = 9.0
    summary = summarize_label_margin_conflict(
        source_pairs=frame,
        projected_pairs=frame,
        scored_pairs=frame,
        low_margin_threshold=2.0,
        non_unavoidable_label="unavoidable",
    )

    assert not summary["low_margin_non_unavoidable_exists"]
    assert summary["recommended_next_path"] == "pre_register_proof_scenario_gate_split"
