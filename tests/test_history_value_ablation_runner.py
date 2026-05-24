import pandas as pd

from autodrift.history_value_ablation_runner import (
    build_history_value_rows,
    classify_history_value,
    parse_level_variant,
    parse_surface_outcomes,
    summarize_history_value_rows,
)


def _base_row(variant: str, *, success: bool, margin: float) -> dict:
    return {
        "pair_id": 1,
        "checkpoint_label": "m399",
        "probe_seed": 10,
        "config": "boundary",
        "target": "future_yaw_response",
        "tail_offset": 2,
        "left_seed": 101,
        "right_seed": 102,
        "left_step": 20,
        "right_step": 20,
        "left_tail_step": 22,
        "right_tail_step": 22,
        "variant": variant,
        "success": success,
        "collision": False,
        "obstacle_completed": True,
        "min_clearance_margin": margin,
        "first_action_distance": 0.0 if variant == "normal_projected" else 0.12,
        "action_trajectory_distance_mean": 0.0 if variant == "normal_projected" else 0.15,
        "action_trajectory_distance_max": 0.0 if variant == "normal_projected" else 0.22,
        "projected_obstacle_bucket": "bucket_a",
        "projection_bucket": "proj_a",
        "projected_obstacle_label": "unavoidable",
        "proof_surface_type": "projection",
    }


def test_build_history_value_rows_maps_normal_to_l3_and_reset_to_l0() -> None:
    frame = pd.DataFrame(
        [
            _base_row("normal_projected", success=True, margin=0.20),
            _base_row("reset_projected", success=True, margin=0.10),
        ]
    )

    rows = build_history_value_rows(frame, surface_name="m520", min_margin_gap=0.02)

    assert {row["history_level"] for row in rows} == {
        "L3_online_gru",
        "L0_reset_hidden_each_step",
    }
    l0 = next(row for row in rows if row["history_level"] == "L0_reset_hidden_each_step")
    assert l0["history_value_candidate"] is True
    assert l0["margin_gap_l3_minus_level"] == 0.10


def test_summarize_history_value_rows_counts_margin_only_candidates() -> None:
    frame = pd.DataFrame(
        [
            _base_row("normal_projected", success=True, margin=0.20),
            _base_row("reset_projected", success=True, margin=0.10),
        ]
    )
    rows = build_history_value_rows(frame, surface_name="m520", min_margin_gap=0.02)

    summary = summarize_history_value_rows(rows)
    l0 = next(row for row in summary if row["history_level"] == "L0_reset_hidden_each_step")

    assert l0["history_value_candidate_count"] == 1
    assert l0["event_row_count"] == 0
    assert l0["success_drop_count"] == 0


def test_classify_history_value_detects_event_signal() -> None:
    rows = [
        {
            "history_level": "L0_reset_hidden_each_step",
            "history_value_candidate": True,
            "success_drop_vs_l3": True,
            "collision_gap_vs_l3": False,
            "obstacle_completion_drop_vs_l3": False,
            "probe_seed": 1,
            "config": "short",
            "target": "future_yaw_response",
        }
    ]

    summary = classify_history_value(rows)

    assert summary["classification"] == "event_history_value_signal"
    assert summary["l0_event_row_count"] == 1


def test_build_history_value_rows_accepts_tail_variant_mapping() -> None:
    normal = _base_row("normal_tail", success=True, margin=0.20)
    reset = _base_row("reset_tail", success=False, margin=-0.05)
    normal["variant_success"] = True
    reset["variant_success"] = False
    frame = pd.DataFrame([normal, reset])

    rows = build_history_value_rows(
        frame,
        surface_name="natural",
        min_margin_gap=0.02,
        level_variants={
            "L3_online_gru": "normal_tail",
            "L0_reset_hidden_each_step": "reset_tail",
        },
    )

    l0 = next(row for row in rows if row["history_level"] == "L0_reset_hidden_each_step")
    assert l0["success_drop_vs_l3"] is True
    assert l0["history_value_candidate"] is True


def test_parse_mapping_helpers() -> None:
    assert parse_level_variant("L3_online_gru=normal_tail") == ("L3_online_gru", "normal_tail")
    surface, path = parse_surface_outcomes("m497=runs/outcomes.csv")
    assert surface == "m497"
    assert str(path) == "runs/outcomes.csv"
