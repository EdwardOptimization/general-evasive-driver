from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis as diagnosis
from autodrift.artifacts import read_json, write_csv_rows


def _episode(
    scenario_id: str,
    *,
    role: str = "R0_stable_avoidable",
    policy: str = "aeb",
    termination: str = "speed_too_low",
    outcome: str = "speed_too_low_noncollision_noncompletion",
    margin: float = 8.0,
    collision: bool = False,
    success: bool = False,
) -> dict[str, Any]:
    return {
        "workload_id": f"{scenario_id}::{policy}",
        "scenario_spec_id": scenario_id,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "role_family": role,
        "sampled_obstacle_label": "aeb_feasible" if role == "R0_stable_avoidable" else "drift_required",
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "support_policy_name": policy,
        "seed_repeat_index": 0,
        "eval_seed": 123,
        "termination_reason": termination,
        "outcome_bucket": outcome,
        "min_clearance_margin": margin,
        "collision": collision,
        "success": success,
    }


def _scenario_label(
    scenario_id: str,
    *,
    role: str = "R0_stable_avoidable",
    support_label: str = "metric_conflict",
) -> dict[str, Any]:
    return {
        "scenario_spec_id": scenario_id,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "role_family": role,
        "sampled_obstacle_label": "aeb_feasible" if role == "R0_stable_avoidable" else "drift_required",
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "support_label": support_label,
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    episodes = [
        _episode("r0_a", margin=12.0),
        _episode("r0_b", margin=9.0),
        _episode(
            "r4_a",
            role="R4_unavoidable_mitigation",
            policy="envelope_aes",
            termination="obstacle_collision",
            outcome="collision_failure",
            margin=-0.2,
            collision=True,
        ),
    ]
    labels = [
        _scenario_label("r0_a"),
        _scenario_label("r0_b"),
        _scenario_label("r4_a", role="R4_unavoidable_mitigation", support_label="support_blocked"),
    ]
    roles = [
        {"role_family": "R0_stable_avoidable", "scenario_count": 2},
        {"role_family": "R4_unavoidable_mitigation", "scenario_count": 1},
    ]
    episode_path = tmp_path / "episodes.csv"
    labels_path = tmp_path / "labels.csv"
    roles_path = tmp_path / "roles.csv"
    write_csv_rows(episode_path, episodes)
    write_csv_rows(labels_path, labels)
    write_csv_rows(roles_path, roles)
    return episode_path, labels_path, roles_path


def test_metric_semantics_diagnosis_separates_safe_stop_from_support_blocked(tmp_path: Path) -> None:
    episodes, labels, roles = _write_inputs(tmp_path)

    summary = diagnosis.run_metric_semantics_conflict_diagnosis(
        episode_rows=episodes,
        scenario_support_labels=labels,
        role_support_summary=roles,
        output_dir=tmp_path / "out",
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_metric_semantics_conflict_diagnosis_pass"
    assert summary["input_episode_count"] == 3
    assert summary["metric_conflict_scenario_count"] == 2
    assert summary["residual_support_blocked_scenario_count"] == 1
    assert summary["safe_stop_metric_conflict_episode_count"] == 2
    assert summary["r0_aeb_safe_stop_episode_count"] == 2
    assert summary["r0_safe_stop_scenario_count"] == 2
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["next_blocker"] == "next"

    scenario_rows = diagnosis.read_csv_rows(tmp_path / "out" / "scenario_metric_semantics_diagnosis.csv")
    labels_by_id = {row["scenario_spec_id"]: row["metric_semantics_label"] for row in scenario_rows}
    assert labels_by_id["r0_a"] == "safe_stop_success_semantics_conflict"
    assert labels_by_id["r4_a"] == "residual_support_blocked"
    role_rows = diagnosis.read_csv_rows(tmp_path / "out" / "role_metric_semantics_summary.csv")
    role_labels = {row["role_family"]: row["role_metric_semantics_label"] for row in role_rows}
    assert role_labels["R0_stable_avoidable"] == "role_safe_stop_success_semantics_repair_required"
    assert (tmp_path / "out" / "safe_stop_metric_conflict_rows.csv").exists()
    assert (tmp_path / "out" / "claim_boundary.csv").exists()

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["next_blocker"] == "next"


def test_metric_semantics_diagnosis_fails_without_r0_safe_stop_evidence(tmp_path: Path) -> None:
    episodes, labels, roles = _write_inputs(tmp_path)
    write_csv_rows(episodes, [_episode("r0_a", termination="off_track", outcome="off_track_noncollision_noncompletion", margin=0.5)])

    summary = diagnosis.run_metric_semantics_conflict_diagnosis(
        episode_rows=episodes,
        scenario_support_labels=labels,
        role_support_summary=roles,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_metric_semantics_conflict_diagnosis_fail"
    assert summary["safe_stop_metric_conflict_episode_count"] == 0
