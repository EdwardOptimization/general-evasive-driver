from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel import (
    RESULT_FAIL,
    RESULT_PASS,
    read_csv_rows,
    run_scenario_quality_discriminant_panel,
)


def _episode(
    *,
    role: str,
    label: str,
    hidden: str = "nominal",
    timing: str = "mid",
    lateral: str = "centerline",
    success: bool = False,
    hard_offtrack: bool = True,
    collision: bool = False,
    soft: bool = False,
    outcome: str = "off_track_noncollision_noncompletion",
) -> dict[str, Any]:
    return {
        "role_family": role,
        "sampled_obstacle_label": label,
        "hidden_dynamics_bucket": hidden,
        "obstacle_longitudinal_timing_bucket": timing,
        "obstacle_lateral_offset_bucket": lateral,
        "metric_selected_actual_success": success,
        "metric_selected_hard_offtrack_failure": hard_offtrack,
        "metric_selected_soft_offtrack_violation": soft,
        "metric_selected_boundary_tolerated_success": False,
        "collision": collision,
        "outcome_bucket": outcome,
        "steps": 100,
        "min_clearance_margin": -0.1 if collision else 1.0,
        "metric_selected_max_offtrack_overshoot_m": 0.2 if hard_offtrack else 0.0,
    }


def _consolidated(
    *,
    row_id: str,
    axis: str,
    value: str,
    episodes: int,
    hard: int,
    collision: int = 0,
    success: int = 0,
    repair: bool = True,
    collision_guardrail: bool = False,
    soft: int = 0,
) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "row_class": "hard_offtrack_target" if repair else "collision_guardrail",
        "axis": axis,
        "value": value,
        "episode_count": episodes,
        "actual_success_count": success,
        "actual_success_rate": success / episodes if episodes else 0.0,
        "hard_offtrack_count": hard,
        "hard_offtrack_rate": hard / episodes if episodes else 0.0,
        "soft_offtrack_violation_count": soft,
        "soft_offtrack_violation_rate": soft / episodes if episodes else 0.0,
        "boundary_tolerated_success_count": 0,
        "boundary_tolerated_success_rate": 0.0,
        "collision_count": collision,
        "collision_rate": collision / episodes if episodes else 0.0,
        "max_step_noncompletion_count": 0,
        "max_step_noncompletion_rate": 0.0,
        "other_count": max(0, episodes - hard - collision - success - soft),
        "other_rate": max(0, episodes - hard - collision - success - soft) / episodes if episodes else 0.0,
        "mean_min_clearance_margin": 1.0,
        "min_min_clearance_margin": -0.1 if collision else 1.0,
        "mean_overshoot_m": 0.2,
        "max_overshoot_m": 0.3,
        "mean_steps": 100.0,
        "diagnostic_pattern": "hard_offtrack_dominated" if hard >= collision else "collision_dominated",
        "actionability_class": "diagnostic_monitoring" if axis in {"profile_name", "pack_id"} else axis,
        "repair_target_admissible": repair,
        "collision_guardrail_required": collision_guardrail,
        "soft_boundary_diagnostic": bool(soft),
        "monitoring_only": axis in {"profile_name", "pack_id"},
        "diagnostic_only": not repair,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }


def _write_inputs(tmp_path: Path, *, source_pass: bool = True) -> dict[str, Path]:
    episode_rows: list[dict[str, Any]] = []
    episode_rows.extend(
        _episode(role="R0_stable_avoidable", label="aeb_feasible", hidden="nominal", collision=False)
        for _ in range(10)
    )
    episode_rows.extend(
        _episode(role="R1_aeb_infeasible_stable_aes", label="aes_feasible", hidden="nominal", collision=False)
        for _ in range(10)
    )
    episode_rows.extend(
        _episode(
            role="R2_handling_limit_drift_capable_avoidance",
            label="drift_required",
            hidden="low_mu",
            collision=True,
            outcome="collision_failure",
        )
        for _ in range(10)
    )
    episode_rows.extend(
        _episode(
            role="R4_unavoidable_mitigation",
            label="unavoidable",
            hidden="weak_brake",
            hard_offtrack=False,
            collision=True,
            outcome="collision_failure",
        )
        for _ in range(10)
    )
    target_rows = [
        _consolidated(row_id="r0", axis="role_family", value="R0_stable_avoidable", episodes=10, hard=10),
        _consolidated(row_id="aeb", axis="sampled_obstacle_label", value="aeb_feasible", episodes=10, hard=10),
        _consolidated(row_id="r1", axis="role_family", value="R1_aeb_infeasible_stable_aes", episodes=10, hard=10),
        _consolidated(row_id="aes", axis="sampled_obstacle_label", value="aes_feasible", episodes=10, hard=10),
        _consolidated(
            row_id="drift",
            axis="sampled_obstacle_label",
            value="drift_required",
            episodes=10,
            hard=10,
            collision=10,
            collision_guardrail=True,
            soft=1,
        ),
        _consolidated(
            row_id="lowmu",
            axis="hidden_dynamics_bucket",
            value="low_mu",
            episodes=10,
            hard=10,
            collision=10,
            collision_guardrail=True,
        ),
        _consolidated(
            row_id="timing",
            axis="obstacle_longitudinal_timing_bucket",
            value="mid",
            episodes=40,
            hard=30,
            collision=10,
            collision_guardrail=True,
        ),
    ]
    guardrail_rows = [
        *target_rows,
        _consolidated(
            row_id="unavoidable",
            axis="sampled_obstacle_label",
            value="unavoidable",
            episodes=10,
            hard=0,
            collision=10,
            repair=False,
            collision_guardrail=True,
        ),
        _consolidated(
            row_id="profile",
            axis="profile_name",
            value="L3_online_gru",
            episodes=40,
            hard=30,
            collision=10,
            repair=False,
            collision_guardrail=True,
        ),
    ]
    diagnostic_rows = [
        guardrail_rows[-1],
        _consolidated(
            row_id="pack",
            axis="pack_id",
            value="baseline_reference_pack",
            episodes=40,
            hard=30,
            collision=10,
            repair=False,
            collision_guardrail=True,
        ),
    ]
    source_summary = {"result_class": "source_pass" if source_pass else "source_fail"}
    m2449_summary = {"result_class": "m2449_pass"}

    paths = {
        "source_summary": tmp_path / "source_summary.json",
        "episode_rows": tmp_path / "episode_rows.csv",
        "m2449_summary": tmp_path / "m2449_summary.json",
        "target_rows": tmp_path / "target_rows.csv",
        "guardrail_rows": tmp_path / "guardrail_rows.csv",
        "diagnostic_rows": tmp_path / "diagnostic_rows.csv",
    }
    write_json(paths["source_summary"], source_summary)
    write_json(paths["m2449_summary"], m2449_summary)
    write_csv_rows(paths["episode_rows"], episode_rows)
    write_csv_rows(paths["target_rows"], target_rows)
    write_csv_rows(paths["guardrail_rows"], guardrail_rows)
    write_csv_rows(paths["diagnostic_rows"], diagnostic_rows)
    return paths


def test_discriminant_panel_separates_quality_candidates_guardrails_and_monitoring(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    summary = run_scenario_quality_discriminant_panel(
        source_summary_path=paths["source_summary"],
        episode_rows_path=paths["episode_rows"],
        m2449_summary_path=paths["m2449_summary"],
        target_rows_path=paths["target_rows"],
        guardrail_rows_path=paths["guardrail_rows"],
        diagnostic_rows_path=paths["diagnostic_rows"],
        output_dir=tmp_path / "out",
        target_episode_count=40,
        target_row_count=7,
        guardrail_row_count=9,
    )

    assert summary["result_class"] == RESULT_PASS
    assert summary["scenario_quality_blocker_count"] >= 2
    assert summary["possible_repair_plan_candidate_count"] >= 2
    assert summary["collision_mitigation_guardrail_count"] >= 2
    assert summary["monitoring_only_count"] >= 1
    assert summary["route_supported"] is True
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["training_started"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    panel_rows = read_csv_rows(tmp_path / "out" / "panel_rows.csv")
    r0 = next(row for row in panel_rows if row["panel_id"] == "m2452_stable_avoidable_task_quality")
    assert r0["scenario_quality_blocker"] == "True"
    assert r0["possible_repair_plan_candidate"] == "False"
    drift = next(row for row in panel_rows if row["panel_id"] == "m2452_handling_limit_drift_candidate")
    assert drift["possible_repair_plan_candidate"] == "True"
    unavoidable = next(row for row in panel_rows if row["panel_id"] == "m2452_unavoidable")
    assert unavoidable["collision_mitigation_guardrail"] == "True"
    profile = next(row for row in panel_rows if row["panel_id"] == "m2452_profile")
    assert profile["monitoring_only"] == "True"
    assert profile["ranking_admissible"] == "False"

    decisions = (tmp_path / "out" / "decision_rows.csv").read_text(encoding="utf-8")
    assert "profile_pack_checkpoint_axes,monitoring_only_non_ranking,True" in decisions
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["panel_rows"].endswith("panel_rows.csv")


def test_discriminant_panel_fails_closed_on_source_failure(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path, source_pass=False)

    summary = run_scenario_quality_discriminant_panel(
        source_summary_path=paths["source_summary"],
        episode_rows_path=paths["episode_rows"],
        m2449_summary_path=paths["m2449_summary"],
        target_rows_path=paths["target_rows"],
        guardrail_rows_path=paths["guardrail_rows"],
        diagnostic_rows_path=paths["diagnostic_rows"],
        output_dir=tmp_path / "out",
        target_episode_count=40,
        target_row_count=7,
        guardrail_row_count=9,
    )

    assert summary["result_class"] == RESULT_FAIL
    assert "lineage_invalid" in summary["failure_types_observed"]
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False


def test_discriminant_panel_fails_closed_on_row_count_mismatch(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)

    summary = run_scenario_quality_discriminant_panel(
        source_summary_path=paths["source_summary"],
        episode_rows_path=paths["episode_rows"],
        m2449_summary_path=paths["m2449_summary"],
        target_rows_path=paths["target_rows"],
        guardrail_rows_path=paths["guardrail_rows"],
        diagnostic_rows_path=paths["diagnostic_rows"],
        output_dir=tmp_path / "out",
        target_episode_count=41,
        target_row_count=8,
        guardrail_row_count=9,
    )

    assert summary["result_class"] == RESULT_FAIL
    assert "metric_artifact" in summary["failure_types_observed"]
    assert summary["episode_count"] == 40
