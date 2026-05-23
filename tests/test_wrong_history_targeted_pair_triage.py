import pandas as pd

from autodrift.wrong_history_targeted_pair_triage import (
    build_targeted_pair_candidates,
    select_targeted_pairs,
    summarize_triage,
)


def _pairs() -> pd.DataFrame:
    rows = []
    for idx, seed in enumerate([100, 200, 300, 100, 200, 300]):
        rows.append(
            {
                "left_index": idx,
                "right_index": idx + 100,
                "target": ["future_yaw_response", "future_braking_deceleration", "future_lateral_accel_response"][
                    idx % 3
                ],
                "visible_distance": 0.10 + idx * 0.005,
                "visible_threshold": 0.20,
                "target_z_delta": 1.2 + idx * 0.2,
                "left_episode": idx,
                "right_episode": idx + 10,
                "left_seed": seed + idx,
                "right_seed": seed + idx + 50,
                "left_step": 10 + idx,
                "right_step": 20 + idx,
                "probe_seed": seed,
                "left_obstacle_label": ["drift_required", "aes_feasible", "unavoidable"][idx % 3],
                "right_obstacle_label": ["drift_required", "aes_feasible", "unavoidable"][idx % 3],
                "left_obstacle_distance": 12.0 + idx,
                "left_obstacle_lateral_offset": float(idx % 2),
                "response_hidden_minus_current_response_distance": 0.1 * idx,
                "response_hidden_more_separated_than_current_response": idx % 2 == 0,
                "accepted": idx % 2 == 0,
            }
        )
    return pd.DataFrame(rows)


def test_candidate_filter_preserves_matched_current_constraints():
    pairs = _pairs()
    pairs.loc[0, "target_z_delta"] = 0.5
    pairs.loc[1, "visible_distance"] = 0.5

    candidates = build_targeted_pair_candidates(
        pairs,
        min_target_z_delta=1.0,
        max_visible_distance=None,
        use_row_visible_threshold=True,
        exclude_same_episode=True,
        obstacle_distance_ceiling=30.0,
    )

    assert not bool(candidates.loc[0, "matched_current_pass"])
    assert not bool(candidates.loc[1, "matched_current_pass"])
    assert bool(candidates.loc[2, "matched_current_pass"])


def test_target_score_prefers_hidden_separation_and_near_boundary():
    candidates = build_targeted_pair_candidates(
        _pairs(),
        min_target_z_delta=1.0,
        max_visible_distance=None,
        use_row_visible_threshold=True,
        exclude_same_episode=True,
        obstacle_distance_ceiling=30.0,
    )

    assert candidates.loc[5, "wrong_history_target_score"] > candidates.loc[1, "wrong_history_target_score"]


def test_selection_enforces_source_caps():
    candidates = build_targeted_pair_candidates(
        _pairs(),
        min_target_z_delta=1.0,
        max_visible_distance=None,
        use_row_visible_threshold=True,
        exclude_same_episode=True,
        obstacle_distance_ceiling=30.0,
    )

    selected = select_targeted_pairs(
        candidates,
        max_rows=4,
        max_per_probe_seed=1,
        max_per_left_seed=10,
        max_per_label=2,
        max_per_target=3,
        max_per_obstacle_bucket=10,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )

    assert len(selected) == 3
    assert selected["probe_seed"].nunique() == 3


def test_summary_requires_source_diversity():
    candidates = build_targeted_pair_candidates(
        _pairs(),
        min_target_z_delta=1.0,
        max_visible_distance=None,
        use_row_visible_threshold=True,
        exclude_same_episode=True,
        obstacle_distance_ceiling=30.0,
    )
    selected = select_targeted_pairs(
        candidates,
        max_rows=6,
        max_per_probe_seed=10,
        max_per_left_seed=10,
        max_per_label=10,
        max_per_target=10,
        max_per_obstacle_bucket=10,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )

    summary = summarize_triage(
        candidates,
        selected,
        min_targeted_rows=6,
        min_probe_seed_count=3,
        min_obstacle_label_count=3,
        min_target_count=3,
        max_single_seed_share=0.5,
        max_single_label_share=0.5,
    )

    assert summary["targeted_pair_count"] == 6
    assert summary["targeted_probe_seed_count"] == 3
    assert summary["triage_pass"]
