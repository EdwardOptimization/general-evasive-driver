import pandas as pd

from autodrift.guarded_capability_action_coupling_evaluator import (
    build_coupling_rows,
    coupling_class,
    summarize_coupling_rows,
)


def _base_row(variant: str, capability_distance: float, action_distance: float) -> tuple[dict, dict]:
    common = {
        "pair_id": 1,
        "checkpoint_label": "bc5660",
        "source_checkpoint_label": "bc5660",
        "surface": "fresh",
        "probe_seed": 1,
        "target": "future_yaw_response",
        "variant": variant,
        "left_seed": 10,
        "right_seed": 20,
        "left_step": 5,
        "right_step": 6,
        "visible_distance": 0.1,
        "target_z_delta": 1.2,
    }
    capability = {
        **common,
        "variant_kind": "real_history",
        "capability_z_distance": capability_distance,
        "normal_future_braking_deceleration": 1.0,
        "variant_future_braking_deceleration": 1.1,
        "normal_future_yaw_response": 0.2,
        "variant_future_yaw_response": 0.4,
        "normal_future_lateral_accel_response": 2.0,
        "variant_future_lateral_accel_response": 2.2,
    }
    action = {
        **common,
        "action_distance": action_distance,
        "normal_steer": 0.1,
        "normal_throttle": -0.2,
        "normal_brake": 0.3,
        "variant_steer": 0.11,
        "variant_throttle": -0.19,
        "variant_brake": 0.31,
    }
    return capability, action


def test_coupling_class_threshold_cases():
    assert (
        coupling_class(
            capability_z_distance=0.3,
            action_distance=0.01,
            capability_threshold=0.25,
            action_threshold=0.02,
        )
        == "belief_only_gap"
    )
    assert (
        coupling_class(
            capability_z_distance=0.3,
            action_distance=0.03,
            capability_threshold=0.25,
            action_threshold=0.02,
        )
        == "action_and_belief"
    )
    assert (
        coupling_class(
            capability_z_distance=0.1,
            action_distance=0.03,
            capability_threshold=0.25,
            action_threshold=0.02,
        )
        == "action_without_belief"
    )
    assert (
        coupling_class(
            capability_z_distance=0.1,
            action_distance=0.01,
            capability_threshold=0.25,
            action_threshold=0.02,
        )
        == "inactive"
    )


def test_build_coupling_rows_marks_real_history_belief_only_gap():
    capability, action = _base_row("wrong_matched_history", 0.4, 0.001)

    rows = build_coupling_rows(
        capability_rows=pd.DataFrame([capability]),
        action_rows=pd.DataFrame([action]),
        capability_threshold=0.25,
        action_threshold=0.02,
    )

    assert len(rows) == 1
    assert rows[0]["coupling_class"] == "belief_only_gap"
    assert rows[0]["candidate_for_grounding"] is True
    assert rows[0]["grounding_status"] == "requires_grounding"


def test_summarize_coupling_rows_counts_classes():
    cap1, act1 = _base_row("wrong_matched_history", 0.4, 0.001)
    cap2, act2 = _base_row("delayed_history", 0.1, 0.03)
    cap2["pair_id"] = 2
    act2["pair_id"] = 2
    rows = build_coupling_rows(
        capability_rows=pd.DataFrame([cap1, cap2]),
        action_rows=pd.DataFrame([act1, act2]),
        capability_threshold=0.25,
        action_threshold=0.02,
    )

    by_target, aggregate = summarize_coupling_rows(rows)

    assert sum(row["belief_only_gap_count"] for row in by_target) == 1
    assert sum(row["action_without_belief_count"] for row in aggregate) == 1
