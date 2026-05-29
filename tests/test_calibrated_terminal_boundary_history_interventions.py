from autodrift.calibrated_terminal_boundary_history_interventions import (
    AcceptedCalibratedSource,
    CalibratedMeasuredPair,
    CalibratedMeasuredSnapshot,
    CalibratedMeasuredTraceAttempt,
    accepted_specs_by_id,
    build_calibrated_pair_candidates,
    build_summary,
    load_accepted_calibrated_sources,
)


def test_load_accepted_calibrated_sources(tmp_path):
    path = tmp_path / "accepted.csv"
    path.write_text(
        "\n".join(
            [
                "calibration_id,trace_id,source_row_id,source_family,seed,mode_name,window_kind,decision_margin,post_decision_margin,terminal_margin,decision_window_hit,preferred_decision_window_hit,post_decision_window_hit,terminal_window_hit,terminal_reason,collision,obstacle_completed,candidate_materialized,training_corpus_exported",
                "calib-a,trace-a,source-a,t5_boundary_axis_retarget,1,mode,decision,0.05,,0.02,True,False,False,True,collision,True,False,False,False",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rows = load_accepted_calibrated_sources(path)

    assert len(rows) == 1
    assert rows[0].calibration_id == "calib-a"
    assert rows[0].decision_window_hit is True
    assert rows[0].collision is True


def test_accepted_specs_by_id_rebuilds_m1544_ids():
    accepted = load_accepted_calibrated_sources(
        "runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv"
    )

    specs = accepted_specs_by_id(accepted, seed=1843, seed_count=2, max_base_rows=20, max_calibration_specs=160)

    assert len(specs) == len(accepted)
    assert set(specs) == {row.calibration_id for row in accepted}
    assert all(spec.hook_spec.labels_enter_actor_input is False for spec in specs.values())


def _snapshot(
    calibration_id: str,
    family: str,
    *,
    response_x: float,
    context_x: float,
    action: tuple[float, float, float],
    margin: float,
) -> CalibratedMeasuredSnapshot:
    return CalibratedMeasuredSnapshot(
        calibration_id=calibration_id,
        trace_id=f"trace-{calibration_id}",
        source_family=family,
        seed=1,
        snapshot_kind="decision",
        window_kind="decision",
        anchor_step=30,
        response_vector=(response_x,) + (0.0,) * 11,
        context_vector=(context_x,) + (0.0,) * 59,
        action_vector=action,
        hidden_norm=1.0,
        hidden_checksum=1.0,
        min_clearance_margin=margin,
        terminal_margin=margin,
        collision=False,
        obstacle_completed=True,
        terminal_reason="obstacle_completed",
    )


def test_build_calibrated_pair_candidates_requires_match_and_divergence():
    snapshots = [
        _snapshot("a", "t5_boundary_axis_retarget", response_x=0.0, context_x=0.0, action=(0.0, 0.0, 0.0), margin=0.05),
        _snapshot("b", "curved_boundary_obstacle", response_x=0.01, context_x=0.01, action=(0.2, 0.0, 0.0), margin=0.09),
        _snapshot("c", "t5_boundary_axis_retarget", response_x=1.0, context_x=1.0, action=(0.0, 0.0, 0.0), margin=0.05),
    ]

    pairs = build_calibrated_pair_candidates(snapshots, max_pairs=4)

    assert len(pairs) == 1
    assert pairs[0].left_calibration_id == "a"
    assert pairs[0].right_calibration_id == "b"
    assert pairs[0].first_action_l2 >= 0.04


def _accepted(index: int, family: str) -> AcceptedCalibratedSource:
    return AcceptedCalibratedSource(
        calibration_id=f"calib-{index}",
        trace_id=f"trace-{index}",
        source_row_id=f"source-{index}",
        source_family=family,
        seed=index,
        mode_name="mode",
        window_kind="decision",
        decision_margin=0.04,
        post_decision_margin=0.04,
        terminal_margin=0.04,
        decision_window_hit=True,
        post_decision_window_hit=False,
        terminal_reason="obstacle_completed",
        collision=False,
        obstacle_completed=True,
    )


def _attempt(index: int, family: str) -> CalibratedMeasuredTraceAttempt:
    return CalibratedMeasuredTraceAttempt(
        calibration_id=f"calib-{index}",
        trace_id=f"trace-{index}",
        source_family=family,
        seed=index,
        rows=40,
        reached_decision=True,
        reached_post_decision=True,
        accepted_snapshot_count=2,
        terminal_reason="obstacle_completed",
        failure_type="none",
    )


def _pair(index: int, left_family: str, right_family: str) -> CalibratedMeasuredPair:
    return CalibratedMeasuredPair(
        pair_id=f"pair-{index}",
        left_calibration_id=f"left-{index}",
        right_calibration_id=f"right-{index}",
        left_source_family=left_family,
        right_source_family=right_family,
        left_window_kind="decision",
        right_window_kind="decision",
        left_anchor_step=30,
        right_anchor_step=30,
        scene_context_distance=0.01,
        current_ego_distance=0.01,
        first_action_l2=0.2,
        terminal_margin_gap=0.03,
        window_pair_kind="decision|decision",
    )


def test_build_summary_reports_gate_pass_with_synthetic_history_effect():
    families = ["a", "b", "c", "d"]
    accepted = [_accepted(i, families[i % 4]) for i in range(8)]
    attempts = [_attempt(i, families[i % 4]) for i in range(8)]
    snapshots = [
        _snapshot(f"calib-{i}", families[i % 4], response_x=0.0, context_x=0.0, action=(0.0, 0.0, 0.0), margin=0.04)
        for i in range(16)
    ]
    pairs = [_pair(i, families[i % 4], families[(i + 1) % 4]) for i in range(4)]
    rows = []
    for pair in pairs:
        rows.extend(
            [
                {
                    "pair_id": pair.pair_id,
                    "target_side": "left",
                    "anchor_name": "left_calibrated_anchor",
                    "variant": "normal",
                    "target_replay_status": "ok",
                    "terminal_margin_gap_from_normal": 0.0,
                    "success_drop_from_normal": False,
                },
                {
                    "pair_id": pair.pair_id,
                    "target_side": "left",
                    "anchor_name": "left_calibrated_anchor",
                    "variant": "wrong_history_donor_hidden_at_anchor",
                    "target_replay_status": "ok",
                    "terminal_margin_gap_from_normal": 0.03,
                    "success_drop_from_normal": False,
                },
            ]
        )

    summary = build_summary(
        accepted_sources=accepted,
        snapshots=snapshots,
        attempts=attempts,
        pairs=pairs,
        rows=rows,
        continuation_steps=64,
    )

    assert summary["passes_measured_trace_gates"] is True
    assert summary["passes_pair_gates"] is True
    assert summary["passes_history_positive_gates"] is True
    assert summary["passes_public_smoke_gates"] is True
    assert summary["passes_evidence_quality_targets"] is True
    assert summary["candidate_materialized"] is False
