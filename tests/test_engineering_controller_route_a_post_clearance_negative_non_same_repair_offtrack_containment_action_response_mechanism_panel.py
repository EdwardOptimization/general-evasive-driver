from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel as m2813,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2807_dir = root / "m2807"
    m2810_dir = root / "m2810"
    m2807_dir.mkdir()
    m2810_dir.mkdir()
    write_json(
        m2810_dir / "summary.json",
        {
            "status_pass": True,
            "hidden_oracle_actor_input_detected": False,
            "diagnostic_success_count": 2,
            "diagnostic_collision_count": 0,
            "diagnostic_offtrack_count": 10,
        },
    )
    localization_rows = []
    execution_rows = []
    offtrack_rows = []
    for index in range(12):
        candidate_id = f"m2807-cross-axis-candidate-{index + 1:04d}"
        success = index >= 10
        family = "success_obstacle_pass" if success else "offtrack_positive_clearance"
        localization_rows.append(
            {
                "localization_id": f"m2810-localization-{index + 1:04d}",
                "candidate_id": candidate_id,
                "resolution_id": f"m2807-resolution-{index + 1:04d}",
                "task_source_id": f"m1680-spec-{index + 1:04d}",
                "task_family": "T5" if index >= 6 else "T4",
                "source_edge": "edge_a|edge_b",
                "stress_axis_primary": "actuator_delay_or_response",
                "failure_family": family,
                "min_clearance_margin": 1.0 + index,
                "success": success,
                "collision": False,
            }
        )
        execution_rows.append(
            {
                "candidate_id": candidate_id,
                "resolution_id": f"m2807-resolution-{index + 1:04d}",
                "task_source_id": f"m1680-spec-{index + 1:04d}",
                "task_family": "T5" if index >= 6 else "T4",
                "source_edge": "edge_a|edge_b",
                "stress_axis_primary": "actuator_delay_or_response",
                "speed_mean": 7.5 + index,
                "action_rate_mean": 0.001 + index / 10000.0,
                "previous_command_norm_mean": 0.20 + index / 100.0,
                "previous_command_norm_peak": 0.23 + index / 100.0,
                "current_action_norm_mean": 0.21 + index / 100.0,
                "current_action_norm_peak": 0.24 + index / 100.0,
                "action_trace_delta_mean": 0.003 + index / 1000.0,
                "action_trace_delta_peak": 0.16 + index / 1000.0,
                "previous_command_bootstrap_count": 1,
                "previous_command_source": "policy_action_trace_zero_bootstrap",
                "action_trace_delta_source": "current_action_minus_previous_command",
                "plan_action_rate_mean": "",
                "plan_first_action_error_mean": "",
                "time_to_first_off_track_s": "" if success else 1.1 + index / 10.0,
                "off_track_severity_proxy": "" if success else 0.05 + index / 100.0,
                "max_off_track_overshoot": "" if success else 0.05 + index / 100.0,
                "recoverability_window_success": success,
                "recoverability_window_success_available": success,
                "success": success,
                "collision": False,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "stress_axis_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
            }
        )
        if not success:
            offtrack_rows.append({"containment_id": f"m2810-offtrack-{index + 1:04d}", "candidate_id": candidate_id})
    write_csv_rows(m2810_dir / "failure_localization_rows.csv", localization_rows)
    write_csv_rows(m2810_dir / "offtrack_containment_rows.csv", offtrack_rows)
    write_csv_rows(
        m2810_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_context_id": f"m2810-guardrail-{index + 1:04d}",
                "guardrail_source": "prior_panel_exclusion" if index < 37 else "blocker_guard",
                "guardrail_source_id": f"guard-{index + 1:04d}",
                "task_source_id": f"prior-{index + 1:04d}",
                "blocker_id": "",
                "route": "Route A",
                "evidence_family": "prior_surface",
                "row_count": 1,
                "blocking_count": 0,
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "guardrail_role": "outside_denominator",
            }
            for index in range(44)
        ],
    )
    write_csv_rows(
        m2810_dir / "actor_contract_guard_rows.csv",
        [
            {"guard_id": "obs", "guard_family": "p0_observation_dim", "observed": 72, "expected": 72, "status_pass": True},
            {"guard_id": "act", "guard_family": "action_dim", "observed": 3, "expected": 3, "status_pass": True},
        ],
    )
    write_csv_rows(m2810_dir / "gate_matrix.csv", [{"gate_id": "m2810-gate", "status_pass": True}])
    write_csv_rows(m2807_dir / "candidate_execution_rows.csv", execution_rows)
    write_csv_rows(m2807_dir / "gate_matrix.csv", [{"gate_id": "m2807-gate", "status_pass": True}])
    docs = {}
    for name in ["m2812.md", "m2811.md", "route.md", "m2814.json"]:
        path = root / name
        path.write_text("present\n", encoding="utf-8")
        docs[name] = path
    return {
        "m2807_dir": m2807_dir,
        "m2810_dir": m2810_dir,
        "m2812": docs["m2812.md"],
        "m2811": docs["m2811.md"],
        "route_plan": docs["route.md"],
        "follow_up": docs["m2814.json"],
    }


def test_m2813_materializes_action_response_mechanism_context_without_overclaims(tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2813"
    doc_path = tmp_path / "m2813.md"

    summary = m2813.materialize_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel(
        output_dir,
        m2807_dir=paths["m2807_dir"],
        m2810_dir=paths["m2810_dir"],
        m2812_synthesis=paths["m2812"],
        m2811_audit=paths["m2811"],
        route_plan=paths["route_plan"],
        doc_path=doc_path,
        follow_up_manifest=paths["follow_up"],
    )

    assert summary["status_pass"] is True
    assert summary["mechanism_row_count"] == 12
    assert summary["offtrack_mechanism_row_count"] == 10
    assert summary["success_mechanism_row_count"] == 2
    assert summary["collision_mechanism_row_count"] == 0
    assert summary["contrast_row_count"] == 2
    assert summary["action_response_metrics_available"] is True
    assert summary["offtrack_timing_available_count"] == 10
    assert summary["guardrail_context_row_count"] == 44
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["gate_matrix_pass"] is True

    mechanism_rows = _read_csv(output_dir / "action_response_mechanism_rows.csv")
    assert len(mechanism_rows) == 12
    assert {row["diagnostic_only_no_verdict"] for row in mechanism_rows} == {"True"}
    assert {row["ranking_claim_made"] for row in mechanism_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in mechanism_rows} == {"False"}
    assert sum(row["offtrack_noncollision"] == "True" for row in mechanism_rows) == 10
    assert {row["metric_context_available"] for row in mechanism_rows} == {"True"}

    contrast_rows = _read_csv(output_dir / "success_offtrack_contrast_rows.csv")
    assert {row["outcome_family"] for row in contrast_rows} == {"offtrack_positive_clearance", "success_obstacle_pass"}
    assert {row["ranking_claim_made"] for row in contrast_rows} == {"False"}
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    blocked_claims = [row for row in claim_rows if row["allowed_in_m2813"] == "False"]
    assert blocked_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
