import numpy as np

from autodrift.flip_anchor_source_generation_repair import apply_repair_override, build_flip_anchor_summary


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


def test_apply_repair_override_handles_full_brake_variants():
    action = np.asarray([0.8, 0.6, -0.4], dtype=np.float32)

    full_brake = apply_repair_override(action, "full_brake_release_throttle")
    left = apply_repair_override(action, "steer_left_full_brake")
    right = apply_repair_override(action, "steer_right_full_brake")

    assert full_brake[1] == -1.0
    assert full_brake[2] == 1.0
    assert left[0] > action[0]
    assert left[1] == -1.0
    assert left[2] == 1.0
    assert right[0] < action[0]
    assert right[1] == -1.0
    assert right[2] == 1.0


def test_build_flip_anchor_summary_passes_synthetic_source_diverse_case():
    families = [f"family_{index}" for index in range(5)]
    windows = ["reveal", "reveal_plus_4", "decision_minus_24", "decision_minus_16", "decision"]
    rows = []
    for index in range(300):
        recoverable = index < 60
        strong = index < 28
        flip = index < 20
        rows.append(
            _row(
                index,
                recoverable=recoverable,
                strong=strong,
                family=families[index % len(families)],
                window=windows[index % len(windows)],
                collision=1 if flip and index % 2 == 0 else 0,
                success=1 if flip and index % 2 == 1 else 0,
            )
        )

    summary = build_flip_anchor_summary(
        specs=[object()] * 220,
        anchor_rows=rows,
        local_rows=[],
        triage_rows=rows,
        max_source_specs=320,
        max_anchors=320,
        continuation_steps=64,
    )

    assert summary["recoverable_boundary_anchor_count"] == 60
    assert summary["strong_recoverable_boundary_anchor_count"] == 28
    assert summary["active_source_family_count"] == 5
    assert summary["active_window_count"] == 5
    assert summary["distinct_collision_flip_anchor_count"] == 10
    assert summary["distinct_success_flip_anchor_count"] == 10
    assert summary["flip_anchor_source_family_count"] == 5
    assert summary["flip_anchor_window_count"] == 5
    assert summary["guardrail_violation_count"] == 0
    assert summary["simulator_rerun_started"] is True
    assert summary["passes_public_smoke_gates"] is True


def test_build_flip_anchor_summary_flags_source_singleton_flip_failure():
    rows = []
    for index in range(300):
        recoverable = index < 60
        strong = index < 28
        flip = index < 10
        rows.append(
            _row(
                index,
                recoverable=recoverable,
                strong=strong,
                family="flip_family" if flip else f"family_{index % 5}",
                window="reveal" if flip else ["reveal", "reveal_plus_4", "decision_minus_24", "decision_minus_16", "decision"][index % 5],
                collision=1 if flip else 0,
                success=1 if flip else 0,
            )
        )

    summary = build_flip_anchor_summary(
        specs=[object()] * 220,
        anchor_rows=rows,
        local_rows=[],
        triage_rows=rows,
        max_source_specs=320,
        max_anchors=320,
        continuation_steps=64,
    )

    assert summary["distinct_collision_flip_anchor_count"] == 10
    assert summary["distinct_success_flip_anchor_count"] == 10
    assert summary["flip_anchor_source_family_count"] == 1
    assert summary["passes_public_smoke_gates"] is False
