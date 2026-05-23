import pandas as pd

from autodrift.adversarial_wrong_history_pair_search import (
    build_adversarial_search_candidates,
    select_adversarial_pairs,
    summarize_search,
)


def _anchors() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "variant": "wrong_matched_history",
                "probe_seed": 100,
                "target": "future_yaw_response",
                "left_seed": 10,
                "left_step": 5,
                "normal_success": True,
                "normal_margin": 0.3,
                "left_obstacle_label": "drift_required",
            },
            {
                "variant": "wrong_matched_history",
                "probe_seed": 200,
                "target": "future_braking_deceleration",
                "left_seed": 20,
                "left_step": 6,
                "normal_success": True,
                "normal_margin": 0.4,
                "left_obstacle_label": "unavoidable",
            },
        ]
    )


def _pairs() -> pd.DataFrame:
    rows = []
    for idx, seed in enumerate([100, 100, 200, 200, 300]):
        rows.append(
            {
                "probe_seed": seed,
                "target": "future_yaw_response" if seed != 200 else "future_braking_deceleration",
                "left_seed": 10 if seed == 100 else 20,
                "right_seed": 50 + idx,
                "left_step": 5 if seed == 100 else 6,
                "right_step": 10 + idx,
                "left_episode": idx,
                "right_episode": idx + 10,
                "target_z_delta": 1.1 + idx * 0.2,
                "visible_distance": 0.1,
                "visible_threshold": 0.2,
                "response_hidden_minus_current_response_distance": 0.1 * idx,
                "response_hidden_more_separated_than_current_response": idx % 2 == 0,
                "left_obstacle_label": "drift_required" if seed == 100 else "unavoidable",
                "right_obstacle_label": "aes_feasible" if idx % 2 else "drift_required",
                "left_obstacle_distance": 12.0,
                "left_obstacle_lateral_offset": 0.0,
            }
        )
    return pd.DataFrame(rows)


def test_search_candidates_anchor_on_near_boundary_left_states():
    candidates = build_adversarial_search_candidates(
        near_boundary_rows=_anchors(),
        candidate_pairs=_pairs(),
        normal_margin_ceiling=0.75,
        min_target_z_delta=1.0,
        use_row_visible_threshold=True,
        exclude_same_episode=True,
    )

    assert len(candidates) == 4
    assert set(candidates["probe_seed"]) == {100, 200}
    assert candidates["normal_margin"].max() <= 0.75


def test_selection_respects_anchor_and_source_caps():
    candidates = build_adversarial_search_candidates(
        near_boundary_rows=_anchors(),
        candidate_pairs=_pairs(),
        normal_margin_ceiling=0.75,
        min_target_z_delta=1.0,
        use_row_visible_threshold=True,
        exclude_same_episode=True,
    )
    selected = select_adversarial_pairs(
        candidates,
        max_rows=10,
        max_per_anchor=1,
        max_per_probe_seed=10,
        max_per_label=10,
        max_per_target=10,
        max_per_obstacle_bucket=10,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )

    assert len(selected) == 2
    assert selected["anchor_key"].nunique() == 2


def test_summary_rejects_small_or_imbalanced_surface():
    candidates = build_adversarial_search_candidates(
        near_boundary_rows=_anchors(),
        candidate_pairs=_pairs(),
        normal_margin_ceiling=0.75,
        min_target_z_delta=1.0,
        use_row_visible_threshold=True,
        exclude_same_episode=True,
    )
    selected = select_adversarial_pairs(
        candidates,
        max_rows=10,
        max_per_anchor=2,
        max_per_probe_seed=10,
        max_per_label=10,
        max_per_target=10,
        max_per_obstacle_bucket=10,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )

    summary = summarize_search(
        candidates,
        selected,
        min_adversarial_pairs=64,
        min_left_state_count=16,
        min_probe_seed_count=3,
        min_obstacle_label_count=2,
        min_target_count=2,
        max_single_seed_share=0.5,
        max_single_label_share=0.7,
    )

    assert summary["adversarial_pair_count"] == 4
    assert not summary["search_pass"]
