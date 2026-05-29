from autodrift.fresh_ambiguity_measured_mining import (
    MeasuredInterventionRow,
    MeasuredPairCandidate,
    MeasuredSnapshotRow,
    SourceAttemptRow,
    build_intervention_rows,
    build_measured_summary,
    build_pair_candidates,
    canonical_env_family,
    source_row_to_hook_spec,
)
from autodrift.fresh_ambiguity_source_mining import default_source_specs, expand_source_specs


def _snapshot(trace_id: str, source_family: str, *, action: tuple[float, float, float]) -> MeasuredSnapshotRow:
    return MeasuredSnapshotRow(
        trace_id=trace_id,
        source_row_id=trace_id,
        source_family=source_family,
        task_family="T5",
        seed=1,
        snapshot_kind="decision",
        step=10,
        response_vector=(0.1, 0.2, 0.3),
        context_vector=(0.1, 0.2, 0.3, 0.4),
        action_vector=action,
        hidden_norm=1.0,
        hidden_checksum=2.0,
        min_clearance_margin=0.05,
        collision=False,
        obstacle_completed=False,
        terminal_reason="running",
    )


def test_canonical_env_family_maps_fresh_proxy_sources():
    assert canonical_env_family("capability_step_down") == "t4_capability_step_temporal"
    assert canonical_env_family("actuator_delay_step") == "t4_actuator_delay_response"
    assert canonical_env_family("brake_fade_or_loss_proxy") == "t5_high_speed_close_obstacle"
    assert canonical_env_family("curved_boundary_obstacle") == "t5_boundary_axis_retarget"


def test_source_row_to_hook_spec_preserves_p0_guardrails():
    row = expand_source_specs(default_source_specs(seed=1531, seed_count=1))[0]

    spec = source_row_to_hook_spec(row)

    assert spec.source_family == row.source_family
    assert spec.seed == row.seed
    assert spec.env_config.history_length == 1
    assert spec.env_config.include_privileged_params is False
    assert spec.env_config.wheel_observation_mode == "none"
    assert spec.env_config.obstacle_relative_velocity_mode == "zero"
    assert spec.labels_enter_actor_input is False
    assert spec.candidate_materialized is False


def test_build_pair_candidates_reports_measured_distances_and_rejections():
    left = _snapshot("left", "late_reveal_boundary", action=(0.0, 0.0, 0.0))
    right = _snapshot("right", "curved_boundary_obstacle", action=(0.2, 0.0, 0.0))

    pairs = build_pair_candidates((left, right))

    assert len(pairs) == 1
    assert pairs[0].first_action_l2 > 0.0
    assert pairs[0].scene_context_distance == 0.0
    assert pairs[0].current_ego_distance == 0.0
    assert pairs[0].accepted is False
    assert "terminal_margin_gap_too_small" in pairs[0].reasons


def test_build_intervention_rows_records_normal_measured_only():
    pair = MeasuredPairCandidate(
        pair_id="pair",
        left_trace_id="left",
        right_trace_id="right",
        left_source_family="a",
        right_source_family="b",
        task_family="T5",
        scene_context_distance=0.0,
        current_ego_distance=0.0,
        recent_window_distance=0.0,
        older_evidence_distance=0.2,
        hidden_capability_distance=0.2,
        first_action_l2=0.2,
        prefix_action_l2=0.2,
        terminal_margin_gap=0.03,
        accepted=True,
        reasons=(),
    )

    rows = build_intervention_rows((pair,))

    assert rows == [
        MeasuredInterventionRow(
            pair_id="pair",
            variant="normal_measured_pair",
            continuation_executed=True,
            terminal_margin_gap=0.03,
            success_drop=False,
            note="normal measured pair only; wrong-history interventions not executed in M1531 smoke",
        )
    ]


def test_build_measured_summary_keeps_guardrails_false():
    source_rows = expand_source_specs(default_source_specs(seed=1531, seed_count=1))
    attempts = [
        SourceAttemptRow(
            trace_id=f"trace-{index}",
            source_family=row.source_family,
            task_family=row.task_family,
            seed=row.seed,
            rows=8,
            reached_reveal=True,
            reached_decision=True,
            reached_post_decision=False,
            failure_type="none",
            terminal_reason="max_rollout_steps",
        )
        for index, row in enumerate(source_rows)
    ]

    summary = build_measured_summary(
        checkpoint="checkpoint.pt",
        source_rows=source_rows,
        traces=(),
        snapshots=(),
        attempts=attempts,
        pairs=(),
        interventions=(),
        max_rollout_steps=16,
    )

    assert summary["attempted_source_families"] == 14
    assert summary["reached_decision_source_families"] == 14
    assert summary["proxy_fault_family_count"] >= 3
    assert summary["passes_public_smoke_gates"] is True
    assert summary["passes_evidence_quality_targets"] is False
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_materialized"] is False
    assert summary["training_started"] is False
    assert summary["labels_enter_actor_input"] is False
