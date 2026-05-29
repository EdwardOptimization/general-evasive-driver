from autodrift.source_diverse_flip_anchor_history_interventions import (
    CONTROL_VARIANTS,
    HISTORY_VARIANTS,
    InterventionAnchor,
    VARIANTS,
    build_donor_pairs,
    build_summary,
    finalize_rows,
)


def _anchor(index: int, family: str, window: str, *, success: bool = False, collision: bool = True, diagnostic: bool = False):
    return InterventionAnchor(
        anchor_id=f"anchor-{index}",
        calibration_id=f"calib-{index}",
        source_family=family,
        anchor_window=window,
        anchor_step=10 + index,
        normal_success=success,
        normal_collision=collision,
        normal_terminal_margin=-0.01,
        max_abs_terminal_margin_gap=0.05,
        success_flip_count=1,
        collision_flip_count=1,
        diagnostic_late_reveal=diagnostic,
    )


def test_build_donor_pairs_uses_different_source_family():
    anchors = [
        _anchor(0, "t5_boundary_axis_retarget", "decision_minus_24"),
        _anchor(1, "t5_high_speed_close_obstacle", "decision_minus_24"),
        _anchor(2, "t5_near_boundary_warmup", "decision_minus_16", success=True, collision=False),
    ]

    pairs = build_donor_pairs(anchors, donors_per_target=2)

    assert len(pairs) == 6
    assert all(pair.target_anchor_id != pair.donor_anchor_id for pair in pairs)
    assert all(pair.target_source_family != pair.donor_source_family for pair in pairs)
    assert any(pair.same_window for pair in pairs)


def test_finalize_rows_adds_normal_relative_fields():
    rows = [
        {
            "pair_id": "pair-0",
            "target_anchor_id": "anchor-0",
            "variant": "normal",
            "target_replay_status": "ok",
            "first_action_steer": 0.0,
            "first_action_throttle": 0.0,
            "first_action_brake": 0.0,
            "terminal_margin": 0.10,
            "success": True,
            "collision": False,
        },
        {
            "pair_id": "pair-0",
            "target_anchor_id": "anchor-0",
            "variant": "wrong_history_donor_hidden_at_anchor",
            "target_replay_status": "ok",
            "first_action_steer": 0.1,
            "first_action_throttle": 0.0,
            "first_action_brake": 0.0,
            "terminal_margin": 0.06,
            "success": False,
            "collision": True,
        },
    ]

    finalized = finalize_rows(rows)
    wrong = [row for row in finalized if row["variant"] == "wrong_history_donor_hidden_at_anchor"][0]

    assert wrong["first_action_l2_vs_normal"] > 0.0
    assert abs(wrong["terminal_margin_gap_from_normal"] - 0.04) < 1e-9
    assert wrong["success_drop_from_normal"] is True
    assert wrong["collision_increase_from_normal"] is True


def test_build_summary_passes_synthetic_history_positive_case():
    anchors = []
    families = ["t5_boundary_axis_retarget", "t5_high_speed_close_obstacle", "t5_near_boundary_warmup"]
    windows = ["decision_minus_24", "decision_minus_16", "reveal", "reveal_plus_4"]
    for index in range(14):
        anchors.append(_anchor(index, families[index % 3], windows[index % 4], success=index % 5 == 0, collision=index % 5 != 0))
    pairs = build_donor_pairs(anchors, donors_per_target=2)
    rows = []
    for pair in pairs:
        for variant in VARIANTS:
            gap = 0.0
            success = True
            collision = False
            if variant in HISTORY_VARIANTS and pair.target_source_family == "t5_high_speed_close_obstacle":
                gap = 0.03
                success = False
                collision = True
            if variant in CONTROL_VARIANTS:
                gap = 0.04
            rows.append(
                {
                    **pair.__dict__,
                    "variant": variant,
                    "target_replay_status": "ok",
                    "terminal_margin_gap_from_normal": gap,
                    "success_drop_from_normal": not success,
                    "collision_increase_from_normal": collision,
                }
            )

    summary = build_summary(anchors=anchors, pairs=pairs, rows=rows, continuation_steps=64)

    assert summary["target_anchor_count"] == 14
    assert summary["target_source_family_count"] == 3
    assert summary["target_window_count"] == 4
    assert summary["high_speed_target_anchor_count"] >= 4
    assert summary["intervention_row_count"] >= 240
    assert summary["wrong_history_row_count"] >= 20
    assert summary["donor_response_action_row_count"] >= 40
    assert summary["reset_zero_control_row_count"] >= 80
    assert summary["passes_public_smoke_gates"] is True
    assert summary["passes_evidence_quality_targets"] is True
