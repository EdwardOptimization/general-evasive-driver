from __future__ import annotations

from types import SimpleNamespace

import pytest

from autodrift.decisive_history_bounded_runner import (
    SourceAttemptSummary,
    SourceTraceRow,
    assert_p0_env_contract,
    assert_p0_model_contract,
    build_runner_summary,
    build_snapshot_rows,
    phase_for_step,
    select_bounded_specs,
)
from autodrift.env import DriftEnvConfig
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


def _trace_row(step: int, *, terminated: bool = False) -> SourceTraceRow:
    return SourceTraceRow(
        trace_id="trace",
        source_family="family",
        task_family="T4",
        candidate_id="candidate",
        seed=1,
        capability_pair="a|b",
        geometry_key="geometry",
        reveal_step=4,
        decision_step=8,
        step=step,
        phase=phase_for_step(step, 4, 8, terminal=terminated),
        terminated=terminated,
        truncated=False,
        reward=0.0,
        action_steer=0.1,
        action_throttle=0.2,
        action_brake=0.3,
        hidden_norm=1.0 + step,
        hidden_checksum=2.0 + step,
        observation_dim=72,
        info_obstacle_label="aeb_feasible",
        info_obstacle_distance=10.0,
        info_obstacle_lateral_offset=0.5,
        info_active_obstacle_body_x=8.0,
        info_active_obstacle_body_y=0.5,
        info_min_clearance_margin=0.1,
        info_collision=False,
        info_obstacle_completed=False,
        info_warmup_gate_visible=False,
        info_warmup_gate_clearance_margin=0.0,
        info_friction_step_at=None,
        info_friction_step_applied=False,
        info_mu=0.8,
        info_initial_mu=0.9,
        info_brake_scale=1.0,
        info_drive_scale=1.0,
        info_steer_tau_scale=1.0,
    )


def test_phase_for_step_marks_reveal_decision_terminal() -> None:
    assert phase_for_step(3, 4, 8) == "pre_reveal"
    assert phase_for_step(4, 4, 8) == "reveal"
    assert phase_for_step(6, 4, 8) == "between_reveal_and_decision"
    assert phase_for_step(8, 4, 8) == "decision"
    assert phase_for_step(9, 4, 8) == "post_decision"
    assert phase_for_step(9, 4, 8, terminal=True) == "terminal"


def test_p0_env_contract_rejects_privileged_or_wheel_inputs() -> None:
    assert_p0_env_contract(
        DriftEnvConfig(history_length=1, action_history_mode="full", obstacle_relative_velocity_mode="zero")
    )
    with pytest.raises(ValueError, match="privileged"):
        assert_p0_env_contract(DriftEnvConfig(include_privileged_params=True))
    with pytest.raises(ValueError, match="wheel"):
        assert_p0_env_contract(DriftEnvConfig(wheel_observation_mode="front_rear"))
    with pytest.raises(ValueError, match="relative velocity"):
        assert_p0_env_contract(DriftEnvConfig(obstacle_relative_velocity_mode="ego"))


def test_p0_model_contract_rejects_noncanonical_actor() -> None:
    valid = SimpleNamespace(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        actor_encoder="human_view_online_gru",
        is_online_recurrent=True,
    )
    assert_p0_model_contract(valid)
    with pytest.raises(ValueError, match="72-value"):
        assert_p0_model_contract(SimpleNamespace(obs_dim=85, actor_encoder="human_view_online_gru"))
    with pytest.raises(ValueError, match="human-view online GRU"):
        assert_p0_model_contract(SimpleNamespace(obs_dim=HUMAN_VIEW_OBS_DIM, actor_encoder="mlp"))


def test_select_bounded_specs_caps_each_source_family() -> None:
    specs = select_bounded_specs(seed_count=2, source_family_cap=1)
    families = [spec.source_family for spec in specs]
    assert len(specs) == 6
    assert len(set(families)) == 6
    assert all(spec.env_config.history_length == 1 for spec in specs)
    assert all(not spec.labels_enter_actor_input for spec in specs)


def test_build_snapshot_rows_uses_reveal_decision_post_and_terminal() -> None:
    rows = [_trace_row(step) for step in range(18)]
    rows.append(_trace_row(18, terminated=True))
    summary = SourceAttemptSummary(
        trace_id="trace",
        source_family="family",
        task_family="T4",
        candidate_id="candidate",
        seed=1,
        rows=len(rows),
        reached_reveal=True,
        reached_decision=True,
        reached_post_decision=True,
        terminated=True,
        truncated=False,
        terminal_reason="terminated",
        failure_type="none",
    )
    snapshots = build_snapshot_rows(rows, summary)
    kinds = {row.snapshot_kind for row in snapshots}
    assert {"reveal_step", "decision_step", "decision_plus_8", "terminal"} <= kinds
    assert all(row.terminal_reason == "terminated" for row in snapshots)


def test_build_runner_summary_keeps_guardrails_false() -> None:
    specs = select_bounded_specs(seed_count=1, source_family_cap=1)[:1]
    rows = [_trace_row(step) for step in range(10)]
    attempt = SourceAttemptSummary(
        trace_id="trace",
        source_family=specs[0].source_family,
        task_family=specs[0].task_family,
        candidate_id=specs[0].candidate_id,
        seed=specs[0].seed,
        rows=len(rows),
        reached_reveal=True,
        reached_decision=True,
        reached_post_decision=True,
        terminated=False,
        truncated=False,
        terminal_reason="max_rollout_steps",
        failure_type="none",
    )
    snapshots = build_snapshot_rows(rows, attempt)
    summary = build_runner_summary(
        checkpoint="checkpoint.pt",
        specs=specs,
        traces=rows,
        snapshots=snapshots,
        attempts=[attempt],
        max_rollout_steps=96,
    )
    assert summary["trace_row_count"] == len(rows)
    assert summary["rollout_failure_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_materialized"] is False
    assert summary["training_started"] is False
    assert summary["labels_enter_actor_input"] is False
