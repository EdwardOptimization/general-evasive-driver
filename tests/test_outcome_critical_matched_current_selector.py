import pandas as pd

from autodrift.outcome_critical_matched_current_selector import (
    build_outcome_critical_candidates,
    select_compact_outcome_critical_rows,
    summarize_selection,
)


def _pairs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "checkpoint_label": "m399",
                "probe_seed": 9600,
                "target": "future_yaw_response",
                "left_seed": 10,
                "right_seed": 20,
                "left_step": 5,
                "right_step": 7,
                "target_z_delta": 1.5,
                "visible_distance": 0.1,
                "left_obstacle_label": "drift_required",
                "left_obstacle_distance": 12.0,
                "left_obstacle_lateral_offset": -1.0,
            }
        ]
    )


def _action(distance: float = 0.12) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "target": "future_yaw_response",
                "variant": "zero_current_response",
                "left_seed": 10,
                "right_seed": 20,
                "left_step": 5,
                "right_step": 7,
                "normal_pair_action_distance": 0.03,
                "action_distance": distance,
                "variant_to_right_action_distance": 0.1,
                "wrong_history_closer_to_right_action": False,
                "abs_steer_delta": 0.1,
                "abs_throttle_delta": 0.1,
                "abs_brake_delta": 0.1,
            }
        ]
    )


def _outcome(*, margin_gap: float, success_drop: bool = False) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "checkpoint_label": "m399",
                "target": "future_yaw_response",
                "variant": "normal",
                "left_seed": 10,
                "right_seed": 20,
                "left_step": 5,
                "right_step": 7,
                "target_z_delta": 1.5,
                "visible_distance": 0.1,
                "normal_success": True,
                "variant_success": True,
                "success_drop": False,
                "normal_margin": 0.4,
                "variant_margin": 0.4,
                "margin_gap": 0.0,
                "collision": False,
                "obstacle_completed": True,
                "return": 5.0,
                "min_clearance_margin": 0.4,
            },
            {
                "checkpoint_label": "m399",
                "target": "future_yaw_response",
                "variant": "zero_current_response",
                "left_seed": 10,
                "right_seed": 20,
                "left_step": 5,
                "right_step": 7,
                "target_z_delta": 1.5,
                "visible_distance": 0.1,
                "normal_success": True,
                "variant_success": not success_drop,
                "success_drop": success_drop,
                "normal_margin": 0.4,
                "variant_margin": 0.4 - margin_gap,
                "margin_gap": margin_gap,
                "collision": success_drop,
                "obstacle_completed": not success_drop,
                "return": 4.0,
                "min_clearance_margin": 0.4 - margin_gap,
            },
        ]
    )


def _candidates(*, margin_gap: float, success_drop: bool = False, action_distance: float = 0.12) -> pd.DataFrame:
    return build_outcome_critical_candidates(
        pairs=_pairs(),
        action_rows=_action(action_distance),
        outcome_rows=_outcome(margin_gap=margin_gap, success_drop=success_drop),
        max_pairs_per_checkpoint_target=60,
        min_margin_gap=0.02,
        min_action_distance=0.05,
        max_normal_pair_action_distance=0.08,
        min_target_z_delta=1.0,
        max_visible_distance=None,
        require_action_prefilter=True,
    )


def test_action_only_row_is_not_accepted_as_outcome_critical():
    candidates = _candidates(margin_gap=0.0, success_drop=False, action_distance=0.2)
    row = candidates.iloc[0]

    assert bool(row["action_prefilter_pass"])
    assert bool(row["action_only"])
    assert not bool(row["outcome_critical"])
    assert not bool(row["accepted"])


def test_margin_gap_row_is_accepted_when_action_prefilter_passes():
    candidates = _candidates(margin_gap=0.05, success_drop=False, action_distance=0.2)
    row = candidates.iloc[0]

    assert bool(row["positive_margin_gap"])
    assert bool(row["outcome_critical"])
    assert bool(row["accepted"])


def test_success_drop_row_is_accepted():
    candidates = _candidates(margin_gap=0.0, success_drop=True, action_distance=0.2)
    row = candidates.iloc[0]

    assert bool(row["success_drop"])
    assert bool(row["collision_gap"])
    assert bool(row["obstacle_completion_drop"])
    assert bool(row["accepted"])


def test_compact_selection_applies_probe_seed_cap():
    rows = []
    for index in range(4):
        row = _candidates(margin_gap=0.05, action_distance=0.2).iloc[0].to_dict()
        row["probe_seed"] = 9600
        row["left_seed"] = 10 + index
        row["right_seed"] = 20 + index
        row["left_step"] = 5 + index
        row["right_step"] = 7 + index
        row["target_z_delta"] = 2.0 - index * 0.1
        rows.append(row)
    frame = pd.DataFrame(rows)

    compact = select_compact_outcome_critical_rows(
        frame,
        max_rows=10,
        max_per_probe_seed=2,
        max_per_target=10,
        max_per_variant=10,
        max_per_obstacle_bucket=10,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )
    summary = summarize_selection(frame, compact, min_accepted_rows=2)

    assert len(compact) == 2
    assert summary["compact_row_count"] == 2
    assert summary["selector_pass"]
