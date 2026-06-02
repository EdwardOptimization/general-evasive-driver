from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_materialization_preflight import (
    DEFAULT_NEXT_BLOCKER,
    RESULT_FAIL,
    RESULT_PASS,
    read_csv_rows,
    run_overlay_materialization_preflight,
)


def _candidate(candidate_id: str, group: str, index: int) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "candidate_group": group,
        "source_panel_id": f"panel_{index}",
        "source_panel_class": "scenario_quality_blocker",
        "source_panel_scope": "stable_or_aes_quality",
        "role_family": "",
        "sampled_obstacle_label": "",
        "hidden_dynamics_bucket": "",
        "obstacle_longitudinal_timing_bucket": "",
        "obstacle_lateral_offset_bucket": "",
        "geometry_lever_class": "stable_recovery_corridor_and_reaction_distance",
        "boundary_protocol_class": "road_containment_actual_success_required",
        "split": "public_debug",
        "episode_count": 900,
        "actual_success_rate": 0.0,
        "hard_offtrack_rate": 1.0,
        "collision_rate": 0.0,
        "labels_enter_actor_input": False,
        "actor_input_contract_changed": False,
        "scenario_redesign_executed": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "reason": "test protocol row",
    }


def _role(group: str, scope: str) -> dict[str, Any]:
    return {
        "role_protocol_id": f"role_{group}",
        "candidate_group": group,
        "role_scope": scope,
        "sampled_obstacle_label_scope": "metadata_only",
    }


def _write_inputs(tmp_path: Path, *, include_all_targets: bool = True) -> dict[str, Path]:
    base = tmp_path / "source"
    base.mkdir()
    paths = {
        "summary": base / "summary.json",
        "candidate_rows": base / "candidate_rows.csv",
        "role_protocol_rows": base / "role_protocol_rows.csv",
        "geometry_lever_rows": base / "geometry_lever_rows.csv",
        "guardrail_rows": base / "guardrail_rows.csv",
        "claim_boundary": base / "claim_boundary.csv",
        "preflight_work_items": base / "preflight_work_items.csv",
    }
    write_json(
        paths["summary"],
        {"result_class": "current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight_pass"},
    )
    candidates = [
        _candidate("stable_1", "stable_feasibility_support", 1),
        _candidate("stable_2", "stable_feasibility_support", 2),
        _candidate("stable_3", "stable_feasibility_support", 3),
        _candidate("aes_1", "stable_aes_support", 4),
        _candidate("aes_2", "stable_aes_support", 5),
        _candidate("aes_3", "stable_aes_support", 6),
        _candidate("guard_1", "geometry_timing_guardrail", 7),
    ]
    write_csv_rows(paths["candidate_rows"], candidates)
    write_csv_rows(
        paths["role_protocol_rows"],
        [
            _role("stable_feasibility_support", "R0_stable_avoidable"),
            _role("stable_aes_support", "R1_aeb_infeasible_stable_aes"),
            _role("geometry_timing_guardrail", "geometry_timing_guardrail"),
        ],
    )
    write_csv_rows(
        paths["geometry_lever_rows"],
        [
            {
                "lever_id": "lever0",
                "geometry_lever_class": "stable_recovery_corridor_and_reaction_distance",
                "candidate_group": "stable_feasibility_support",
                "bounded": True,
            }
        ],
    )
    write_csv_rows(
        paths["guardrail_rows"],
        [
            {
                "guardrail_id": "source_guard",
                "guardrail_class": "claim_boundary",
                "source_role_or_axis": "candidate_rows",
                "failure_mode_to_preserve": "contract_violation",
                "metric_to_watch": "violation",
                "value": 0,
                "violation": False,
                "reason": "source guard",
            }
        ],
    )
    write_csv_rows(
        paths["claim_boundary"],
        [
            {
                "claim_key": "actual_success_improvement",
                "claim_value": "blocked",
                "admissible": False,
                "reason": "blocked",
            },
            {
                "claim_key": "paper_or_self_id_verdict",
                "claim_value": "blocked",
                "admissible": False,
                "reason": "blocked",
            },
            {
                "claim_key": "current_sim_verdict",
                "claim_value": "blocked",
                "admissible": False,
                "reason": "blocked",
            },
        ],
    )
    target_ids = ["stable_1", "stable_2", "stable_3", "aes_1", "aes_2", "aes_3"]
    if not include_all_targets:
        target_ids = target_ids[:-1]
    preflight_rows = []
    for index, candidate_id in enumerate(target_ids, start=1):
        group = "stable_feasibility_support" if candidate_id.startswith("stable") else "stable_aes_support"
        preflight_rows.append(
            {
                "preflight_id": f"m2458_preflight_{index:03d}",
                "source_candidate_id": candidate_id,
                "source_panel_id": f"panel_{index}",
                "candidate_group": group,
                "role_scope": "",
                "sampled_obstacle_label_scope": "",
                "split": "public_debug",
                "preflight_lane": "reset_blocked",
                "intended_evidence_role": "test",
                "geometry_lever_class": "stable_recovery_corridor_and_reaction_distance",
                "boundary_protocol_class": "road_containment_actual_success_required",
                "static_check_required": True,
                "reset_check_required": True,
                "concrete_overlay_required": True,
                "concrete_overlay_available": False,
                "concrete_overlay_source": "",
                "env_config_overlay_json": "",
                "blocked_reason": "reset_blocked_missing_concrete_overlay",
                "labels_enter_actor_input": False,
                "actor_input_contract_changed": False,
                "scenario_redesign_executed": False,
                "policy_action_executed": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    write_csv_rows(paths["preflight_work_items"], preflight_rows)
    return paths


def _run(tmp_path: Path, paths: dict[str, Path]) -> dict[str, Any]:
    return run_overlay_materialization_preflight(
        m2455_summary_path=paths["summary"],
        candidate_rows_path=paths["candidate_rows"],
        role_protocol_rows_path=paths["role_protocol_rows"],
        geometry_lever_rows_path=paths["geometry_lever_rows"],
        source_guardrail_rows_path=paths["guardrail_rows"],
        source_claim_boundary_path=paths["claim_boundary"],
        preflight_work_items_path=paths["preflight_work_items"],
        output_dir=tmp_path / "out",
    )


def test_overlay_materialization_attaches_six_overlays_and_keeps_preflight_only(tmp_path: Path) -> None:
    summary = _run(tmp_path, _write_inputs(tmp_path))

    assert summary["result_class"] == RESULT_PASS
    assert summary["target_preflight_row_count"] == 6
    assert summary["concrete_overlay_row_count"] == 6
    assert summary["candidate_rows_with_overlay_count"] == 6
    assert summary["adapter_concrete_overlay_available_count"] == 6
    assert summary["adapter_static_check_fail_count"] == 0
    assert summary["adapter_reset_attempted_count"] == 0
    assert summary["adapter_reset_blocked_missing_concrete_overlay_count"] == 0
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["actor_input_contract_changed_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["scenario_redesign_executed"] is False
    assert summary["policy_action_executed"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["next_blocker"] == DEFAULT_NEXT_BLOCKER

    overlays = read_csv_rows(tmp_path / "out" / "concrete_overlay_rows.csv")
    assert {row["overlay_family"] for row in overlays} == {
        "R0_stable_avoidable",
        "R1_aeb_infeasible_stable_aes",
    }
    candidates = read_csv_rows(tmp_path / "out" / "candidate_rows_with_overlays.csv")
    assert sum(bool(row["env_config_overlay_json"]) for row in candidates) == 6
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["adapter_summary"].endswith("adapter_summary.json")


def test_overlay_materialization_fails_if_target_count_is_not_six(tmp_path: Path) -> None:
    summary = _run(tmp_path, _write_inputs(tmp_path, include_all_targets=False))

    assert summary["result_class"] == RESULT_FAIL
    assert summary["target_preflight_row_count"] == 5
    assert summary["concrete_overlay_row_count"] == 5
    assert summary["guardrail_violation_count"] > 0
    assert "scenario_sampling_failure" in summary["failure_types_observed"]
