import numpy as np

from autodrift.targeted_third_source_flip_anchor import (
    TARGETED_SOURCE_FAMILIES,
    apply_targeted_override,
    build_targeted_flip_anchor_summary,
    targeted_calibration_modes,
)


def _row(index: int, *, recoverable: bool, strong: bool, family: str, window: str, collision: int = 0, success: int = 0):
    return {
        "anchor_id": f"anchor-{index}",
        "source_family": family,
        "anchor_window": window,
        "normal_replay_status": "ok",
        "triage_label": "strong_recoverable_boundary" if strong else "recoverable_boundary" if recoverable else "inactive_boundary",
        "recoverable_boundary": recoverable,
        "strong_recoverable_boundary": strong,
        "collision_flip_count": collision,
        "success_flip_count": success,
        "max_abs_terminal_margin_gap": 0.08 if strong else 0.03,
    }


def test_targeted_modes_are_target_heavy():
    high_speed = targeted_calibration_modes("t5_high_speed_close_obstacle")
    late_reveal = targeted_calibration_modes("late_reveal_boundary")
    comparison = targeted_calibration_modes("t5_boundary_axis_retarget")

    assert len(high_speed) > len(comparison)
    assert len(late_reveal) > len(comparison)
    assert {mode.name.split("_", 1)[0] for mode in high_speed} == {"hs"}
    assert {mode.name.split("_", 1)[0] for mode in late_reveal} == {"lr"}


def test_apply_targeted_override_handles_targeted_variants():
    action = np.asarray([0.1, 0.4, 0.2], dtype=np.float32)

    left = apply_targeted_override(action, "steer_left_full_brake_long")
    right = apply_targeted_override(action, "steer_right_full_brake_long")
    pulse = apply_targeted_override(action, "brake_pulse_then_release")
    release = apply_targeted_override(action, "steer_left_brake_release")

    assert left[0] > action[0]
    assert right[0] < action[0]
    assert left[1] == -1.0 and left[2] == 1.0
    assert pulse[1] == -1.0 and pulse[2] == 1.0
    assert release[0] > action[0] and release[2] == -1.0


def test_build_targeted_summary_passes_with_third_source_flips():
    families = [
        "t5_boundary_axis_retarget",
        "t5_near_boundary_warmup",
        "t5_high_speed_close_obstacle",
        "late_reveal_boundary",
        "curved_boundary_obstacle",
    ]
    windows = ["reveal", "reveal_plus_4", "decision_minus_24", "decision_minus_16", "decision"]
    rows = []
    for index in range(340):
        recoverable = index < 80
        strong = index < 32
        flip = index < 24
        family = families[index % len(families)]
        rows.append(
            _row(
                index,
                recoverable=recoverable,
                strong=strong,
                family=family,
                window=windows[index % len(windows)],
                collision=1 if flip and index % 2 == 0 else 0,
                success=1 if flip and index % 2 == 1 else 0,
            )
        )

    summary = build_targeted_flip_anchor_summary(
        specs=[object()] * 320,
        anchor_rows=rows,
        local_rows=[],
        triage_rows=rows,
        max_source_specs=360,
        max_anchors=360,
        continuation_steps=64,
    )

    assert summary["third_source_flip_anchor_count"] > 0
    assert summary["targeted_family_flip_anchor_count"] > 0
    assert set(summary["targeted_flip_family_counts"]).issubset(TARGETED_SOURCE_FAMILIES)
    assert summary["passes_public_smoke_gates"] is True


def test_build_targeted_summary_fails_without_third_source_flips():
    families = ["t5_boundary_axis_retarget", "t5_near_boundary_warmup", "other_a", "other_b", "other_c"]
    windows = ["reveal", "reveal_plus_4", "decision_minus_24", "decision_minus_16", "decision"]
    rows = []
    for index in range(340):
        recoverable = index < 80
        strong = index < 32
        flip = index < 24
        family = families[index % len(families)]
        if flip:
            family = "t5_boundary_axis_retarget" if index % 2 == 0 else "t5_near_boundary_warmup"
        rows.append(
            _row(
                index,
                recoverable=recoverable,
                strong=strong,
                family=family,
                window=windows[index % len(windows)],
                collision=1 if flip and index % 2 == 0 else 0,
                success=1 if flip and index % 2 == 1 else 0,
            )
        )

    summary = build_targeted_flip_anchor_summary(
        specs=[object()] * 320,
        anchor_rows=rows,
        local_rows=[],
        triage_rows=rows,
        max_source_specs=360,
        max_anchors=360,
        continuation_steps=64,
    )

    assert summary["third_source_flip_anchor_count"] == 0
    assert summary["targeted_family_flip_anchor_count"] == 0
    assert summary["passes_public_smoke_gates"] is False
