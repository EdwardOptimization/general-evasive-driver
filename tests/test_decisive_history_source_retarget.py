from __future__ import annotations

import csv

from autodrift.decisive_history_bounded_runner import SourceAttemptSummary, SourceTraceRow, phase_for_step
from autodrift.decisive_history_source_retarget import (
    RETARGET_MODES,
    build_retarget_specs,
    build_retarget_summary,
    load_baseline_min_margins,
    retarget_hook_spec,
)
from autodrift.decisive_history_env_hooks import default_hook_specs


def _trace_row(source_family: str, margin: float, label: str = "aeb_feasible") -> SourceTraceRow:
    return SourceTraceRow(
        trace_id=f"{source_family}|trace",
        source_family=source_family,
        task_family="T5",
        candidate_id=f"{source_family}-candidate-close_wide",
        seed=1,
        capability_pair="a|b",
        geometry_key="geometry",
        reveal_step=4,
        decision_step=8,
        step=8,
        phase=phase_for_step(8, 4, 8),
        terminated=False,
        truncated=False,
        reward=0.0,
        action_steer=0.1,
        action_throttle=0.2,
        action_brake=0.3,
        hidden_norm=1.0,
        hidden_checksum=2.0,
        observation_dim=72,
        info_obstacle_label=label,
        info_obstacle_distance=10.0,
        info_obstacle_lateral_offset=0.5,
        info_active_obstacle_body_x=8.0,
        info_active_obstacle_body_y=0.5,
        info_min_clearance_margin=margin,
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


def test_retarget_specs_are_bounded_and_p0_compatible() -> None:
    retargets = build_retarget_specs(seed_count=1, source_family_cap=4)
    assert len(retargets) == 24
    assert len({item.hook_spec.source_family for item in retargets}) == 6
    assert {item.retarget_mode for item in retargets} == set(RETARGET_MODES[:4])
    assert all(item.hook_spec.env_config.history_length == 1 for item in retargets)
    assert all(item.hook_spec.env_config.wheel_observation_mode == "none" for item in retargets)
    assert all(not item.hook_spec.labels_enter_actor_input for item in retargets)
    assert all(not item.hook_spec.candidate_materialized for item in retargets)


def test_close_wide_retarget_moves_obstacle_closer_and_wider() -> None:
    base = default_hook_specs(seed_count=1)[0]
    retargeted = retarget_hook_spec(base, "close_wide").hook_spec
    assert retargeted.env_config.obstacle.distance_range[0] < base.env_config.obstacle.distance_range[0]
    assert retargeted.env_config.obstacle.distance_range[1] < base.env_config.obstacle.distance_range[1]
    assert retargeted.env_config.obstacle.half_width_range[0] > base.env_config.obstacle.half_width_range[0]
    assert retargeted.env_config.obstacle.half_width_range[1] > base.env_config.obstacle.half_width_range[1]


def test_drift_required_focus_uses_sampling_labels_without_actor_label_input() -> None:
    base = default_hook_specs(seed_count=1)[0]
    retargeted = retarget_hook_spec(base, "drift_required_focus").hook_spec
    assert "aeb_feasible" not in retargeted.env_config.obstacle.allowed_labels
    assert retargeted.env_config.obstacle.require_aeb_infeasible is True
    assert retargeted.labels_enter_actor_input is False


def test_load_baseline_min_margins(tmp_path) -> None:
    path = tmp_path / "trace.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_family", "info_min_clearance_margin"])
        writer.writeheader()
        writer.writerow({"source_family": "a", "info_min_clearance_margin": "3.0"})
        writer.writerow({"source_family": "a", "info_min_clearance_margin": "2.0"})
        writer.writerow({"source_family": "b", "info_min_clearance_margin": "5.0"})
    assert load_baseline_min_margins(path) == {"a": 2.0, "b": 5.0}


def test_build_retarget_summary_reports_margin_reduction_and_guardrails() -> None:
    retargets = build_retarget_specs(seed_count=1, source_family_cap=1)[:1]
    family = retargets[0].hook_spec.source_family
    traces = [_trace_row(family, 0.8, label="drift_required")]
    attempt = SourceAttemptSummary(
        trace_id="trace",
        source_family=family,
        task_family=retargets[0].hook_spec.task_family,
        candidate_id=retargets[0].hook_spec.candidate_id,
        seed=retargets[0].hook_spec.seed,
        rows=1,
        reached_reveal=True,
        reached_decision=True,
        reached_post_decision=False,
        terminated=False,
        truncated=False,
        terminal_reason="max_rollout_steps",
        failure_type="none",
    )
    summary = build_retarget_summary(
        checkpoint="checkpoint.pt",
        retargets=retargets,
        traces=traces,
        snapshots=[],
        attempts=[attempt],
        baseline_min_margins={family: 8.0},
        max_rollout_steps=128,
    )
    assert summary["global_min_margin"] == 0.8
    assert summary["near_boundary_proxy_count"] == 1
    assert summary["non_aeb_label_source_family_count"] == 1
    assert summary["margin_reduction_by_source_family"][family] == 7.2
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_materialized"] is False
