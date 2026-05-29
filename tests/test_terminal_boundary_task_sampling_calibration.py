from autodrift.decisive_history_bounded_runner import SourceAttemptSummary, SourceSnapshotRow
from autodrift.fresh_ambiguity_source_mining import FreshAmbiguitySourceRow
from autodrift.terminal_boundary_source_repair import TERMINAL_TARGET_FAMILIES
from autodrift.terminal_boundary_task_sampling_calibration import (
    AcceptedCalibratedRow,
    accepted_calibrated_row,
    build_calibration_specs,
    build_summary,
    terminal_calibration_source_rows,
)


def test_terminal_calibration_source_rows_are_terminal_targets_only():
    rows = terminal_calibration_source_rows(seed=1843, seed_count=2, max_base_rows=20)

    assert len(rows) >= 10
    assert {row.source_family for row in rows} <= set(TERMINAL_TARGET_FAMILIES)
    assert len({row.source_family for row in rows}) >= 5
    assert all(row.candidate_materialized is False for row in rows)
    assert all(row.training_corpus_exported is False for row in rows)


def test_build_calibration_specs_respects_cap_and_contract_flags():
    rows = terminal_calibration_source_rows(seed=1843, seed_count=1, max_base_rows=5)

    specs = build_calibration_specs(rows, max_calibration_specs=12)

    assert len(specs) == 12
    assert all(spec.artifact_row.candidate_materialized is False for spec in specs)
    assert all(spec.artifact_row.training_corpus_exported is False for spec in specs)
    assert all(spec.artifact_row.actor_input_contract_changed is False for spec in specs)
    assert all(spec.hook_spec.labels_enter_actor_input is False for spec in specs)


def _source_row(source_family: str, index: int = 0) -> FreshAmbiguitySourceRow:
    return FreshAmbiguitySourceRow(
        source_family=source_family,
        task_family="T5",
        source_index=index,
        seed=184300 + index,
        hidden_capability_pair="low_mu|high_mu",
        geometry_key="near_left",
        reveal_step=20,
        decision_step=28,
        simulator_scope="existing_public_source",
        proxy_fault_family=False,
        closed_t5_subset=False,
        scene_context_distance=0.01,
        current_ego_distance=0.01,
        recent_window_distance=0.01,
        older_evidence_distance=0.2,
        hidden_capability_distance=0.2,
        first_action_l2=0.2,
        prefix_action_l2=0.2,
        terminal_margin_gap=0.03,
        normal_margin=0.03,
    )


def _snapshot(kind: str, margin: float) -> SourceSnapshotRow:
    return SourceSnapshotRow(
        trace_id="trace",
        source_family="t5_near_boundary_warmup",
        task_family="T5",
        candidate_id="candidate",
        seed=1,
        snapshot_kind=kind,
        step=28,
        phase="decision",
        action_steer=0.0,
        action_throttle=0.0,
        action_brake=0.0,
        hidden_norm=1.0,
        min_clearance_margin=margin,
        collision=False,
        obstacle_completed=True,
        terminal_reason="obstacle_completed",
    )


def _attempt() -> SourceAttemptSummary:
    return SourceAttemptSummary(
        trace_id="trace",
        source_family="t5_near_boundary_warmup",
        task_family="T5",
        candidate_id="candidate",
        seed=1,
        rows=30,
        reached_reveal=True,
        reached_decision=True,
        reached_post_decision=True,
        terminated=True,
        truncated=False,
        terminal_reason="obstacle_completed",
        failure_type="none",
    )


def test_accepted_calibrated_row_accepts_decision_or_post_window():
    spec = build_calibration_specs([_source_row("t5_near_boundary_warmup")], max_calibration_specs=1)[0]

    decision_row = accepted_calibrated_row(
        spec,
        [_snapshot("decision_step", 0.04), _snapshot("decision_plus_8", 0.5), _snapshot("terminal", 0.5)],
        _attempt(),
    )
    post_row = accepted_calibrated_row(
        spec,
        [_snapshot("decision_step", 0.5), _snapshot("decision_plus_8", 0.04), _snapshot("terminal", 0.04)],
        _attempt(),
    )
    reject_row = accepted_calibrated_row(
        spec,
        [_snapshot("decision_step", 0.5), _snapshot("decision_plus_8", 0.5), _snapshot("terminal", 0.5)],
        _attempt(),
    )

    assert decision_row is not None
    assert decision_row.window_kind == "decision"
    assert post_row is not None
    assert post_row.window_kind == "post_decision"
    assert reject_row is None


def _accepted(family: str, index: int, *, decision: bool) -> AcceptedCalibratedRow:
    return AcceptedCalibratedRow(
        calibration_id=f"calib-{index}",
        trace_id=f"trace-{index}",
        source_row_id=f"source-{index}",
        source_family=family,
        seed=index,
        mode_name="mode",
        window_kind="decision" if decision else "post_decision",
        decision_margin=0.04 if decision else 0.5,
        post_decision_margin=0.5 if decision else 0.04,
        terminal_margin=0.04,
        decision_window_hit=decision,
        preferred_decision_window_hit=decision,
        post_decision_window_hit=not decision,
        terminal_window_hit=True,
        terminal_reason="obstacle_completed",
        collision=False,
        obstacle_completed=True,
    )


def test_build_summary_reports_public_gate_pass_with_balanced_synthetic_rows():
    families = list(TERMINAL_TARGET_FAMILIES[:4])
    source_rows = [_source_row(families[index % len(families)], index=index) for index in range(10)]
    accepted = [_accepted(families[index % len(families)], index, decision=index < 4) for index in range(8)]
    snapshots = [_snapshot("decision_step", 0.04) for _ in range(20)]
    attempts = [_attempt() for _ in range(20)]

    summary = build_summary(
        source_rows=source_rows,
        specs=[object() for _ in range(40)],
        traces=[],
        snapshots=snapshots,
        attempts=attempts,
        accepted=accepted,
        max_rollout_steps=128,
    )

    assert summary["passes_calibration_source_gates"] is True
    assert summary["passes_near_boundary_gates"] is True
    assert summary["passes_quality_gates"] is True
    assert summary["passes_public_smoke_gates"] is True
    assert summary["candidate_materialized"] is False
