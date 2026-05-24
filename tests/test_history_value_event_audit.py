import pandas as pd

from autodrift.history_value_event_audit import (
    classify_event_audit,
    select_event_rows,
)


def test_select_event_rows_keeps_l0_events_only() -> None:
    frame = pd.DataFrame(
        [
            {
                "history_level": "L3_online_gru",
                "success_drop_vs_l3": False,
                "collision_gap_vs_l3": False,
                "obstacle_completion_drop_vs_l3": True,
            },
            {
                "history_level": "L0_reset_hidden_each_step",
                "success_drop_vs_l3": False,
                "collision_gap_vs_l3": False,
                "obstacle_completion_drop_vs_l3": True,
            },
        ]
    )

    events = select_event_rows(frame)

    assert len(events) == 1
    assert events.iloc[0]["event_type"] == "obstacle_completion_drop"


def test_classify_event_audit_accepts_source_diverse_completion_events() -> None:
    rows = []
    for index in range(12):
        rows.append(
            {
                "surface_name": "m497" if index < 6 else "m487",
                "probe_seed": 100 + index,
                "target": "future_yaw_response" if index % 2 else "future_braking_deceleration",
                "tail_offset": index % 3,
                "left_seed": 200 + index,
                "left_tail_step": 10 + index,
                "success_drop_vs_l3": False,
                "collision_gap_vs_l3": False,
                "obstacle_completion_drop_vs_l3": True,
            }
        )
    events = pd.DataFrame(rows)
    duplicate_rows = [
        {
            "key_name": "left_state",
            "unique_key_count": 12,
            "duplicate_share": 0.0,
        }
    ]

    summary = classify_event_audit(events, duplicate_rows)

    assert summary["classification"] == "source_diverse_history_value_events"
    assert summary["obstacle_completion_drop_event_count"] == 12
