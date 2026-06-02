from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter import (
    RESULT_FAIL,
    RESULT_STATIC_PASS_RESET_BLOCKED,
    read_csv_rows,
    run_reset_static_preflight_adapter,
)


def _candidate(
    candidate_id: str,
    group: str,
    *,
    split: str = "public_debug",
    labels_enter_actor_input: bool = False,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "candidate_group": group,
        "source_panel_id": f"panel_{candidate_id}",
        "sampled_obstacle_label": "",
        "split": split,
        "geometry_lever_class": "test_lever",
        "boundary_protocol_class": "test_boundary",
        "labels_enter_actor_input": labels_enter_actor_input,
        "actor_input_contract_changed": False,
        "scenario_redesign_executed": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _role(group: str, scope: str) -> dict[str, Any]:
    return {
        "role_protocol_id": f"role_{group}",
        "candidate_group": group,
        "role_scope": scope,
        "sampled_obstacle_label_scope": "metadata_only",
    }


def _write_inputs(
    tmp_path: Path,
    *,
    source_pass: bool = True,
    label_violation: bool = False,
) -> dict[str, Path]:
    base = tmp_path / "m2455"
    base.mkdir()
    paths = {
        "summary": base / "summary.json",
        "candidate_rows": base / "candidate_rows.csv",
        "role_protocol_rows": base / "role_protocol_rows.csv",
        "geometry_lever_rows": base / "geometry_lever_rows.csv",
        "guardrail_rows": base / "guardrail_rows.csv",
        "claim_boundary": base / "claim_boundary.csv",
    }
    write_json(
        paths["summary"],
        {
            "result_class": (
                "current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight_pass"
                if source_pass
                else "current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight_fail"
            )
        },
    )
    write_csv_rows(
        paths["candidate_rows"],
        [
            _candidate("c0", "stable_feasibility_support", labels_enter_actor_input=label_violation),
            _candidate("c1", "stable_aes_support", split="public_gate"),
            _candidate("c2", "geometry_timing_guardrail"),
            _candidate("c3", "handling_limit_guardrail"),
            _candidate("c4", "hidden_dynamics_guardrail"),
            _candidate("c5", "mitigation_guardrail"),
        ],
    )
    write_csv_rows(
        paths["role_protocol_rows"],
        [
            _role("stable_feasibility_support", "R0_stable_avoidable"),
            _role("stable_aes_support", "R1_aeb_infeasible_stable_aes"),
            _role("geometry_timing_guardrail", "geometry_timing_guardrail"),
            _role("handling_limit_guardrail", "R2/R3/R5"),
            _role("hidden_dynamics_guardrail", "R5/hidden-dynamics stress"),
            _role("mitigation_guardrail", "R4_unavoidable_mitigation"),
        ],
    )
    write_csv_rows(
        paths["geometry_lever_rows"],
        [
            {
                "lever_id": "lever0",
                "geometry_lever_class": "test_lever",
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
    return paths


def _run_adapter(tmp_path: Path, paths: dict[str, Path]) -> dict[str, Any]:
    return run_reset_static_preflight_adapter(
        m2455_summary_path=paths["summary"],
        candidate_rows_path=paths["candidate_rows"],
        role_protocol_rows_path=paths["role_protocol_rows"],
        geometry_lever_rows_path=paths["geometry_lever_rows"],
        source_guardrail_rows_path=paths["guardrail_rows"],
        source_claim_boundary_path=paths["claim_boundary"],
        output_dir=tmp_path / "out",
    )


def test_adapter_static_passes_and_fails_closed_when_overlays_missing(tmp_path: Path) -> None:
    summary = _run_adapter(tmp_path, _write_inputs(tmp_path))

    assert summary["result_class"] == RESULT_STATIC_PASS_RESET_BLOCKED
    assert summary["source_candidate_row_count"] == 6
    assert summary["preflight_work_item_count"] == 6
    assert summary["static_check_fail_count"] == 0
    assert summary["reset_required_count"] == 2
    assert summary["reset_attempted_count"] == 0
    assert summary["reset_success_count"] == 0
    assert summary["reset_blocked_missing_concrete_overlay_count"] == 2
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["actor_input_contract_changed_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["scenario_redesign_executed"] is False

    work_items = read_csv_rows(tmp_path / "out" / "preflight_work_items.csv")
    lanes = {row["source_candidate_id"]: row["preflight_lane"] for row in work_items}
    assert lanes["c0"] == "reset_blocked"
    assert lanes["c1"] == "reset_blocked"
    assert lanes["c2"] == "static_only"
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["preflight_work_items"].endswith("preflight_work_items.csv")


def test_adapter_fails_on_actor_input_contract_violation(tmp_path: Path) -> None:
    summary = _run_adapter(tmp_path, _write_inputs(tmp_path, label_violation=True))

    assert summary["result_class"] == RESULT_FAIL
    assert summary["labels_enter_actor_input_count"] == 1
    assert summary["static_check_fail_count"] > 0
    assert summary["guardrail_violation_count"] > 0
    assert "contract_violation" in summary["failure_types_observed"]
    assert summary["paper_level_claim_made"] is False


def test_adapter_fails_on_source_materialization_failure(tmp_path: Path) -> None:
    summary = _run_adapter(tmp_path, _write_inputs(tmp_path, source_pass=False))

    assert summary["result_class"] == RESULT_FAIL
    assert summary["static_check_fail_count"] > 0
    assert "lineage_invalid" in summary["failure_types_observed"]
    assert summary["current_sim_verdict_claim_made"] is False
