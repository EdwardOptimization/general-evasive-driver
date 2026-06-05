from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight as m2759,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2756_dir = root / "m2756"
    m2753_dir = root / "m2753"
    m2756_dir.mkdir()
    m2753_dir.mkdir()
    localization_rows = []
    m2753_candidate_rows = []
    m2753_resolution_rows = []
    m1690_rows = []
    for index in range(12):
        collision = index in {0, 7, 8}
        task_source_id = f"m1680-spec-{index + 1:04d}"
        candidate_id = f"m2753-cross-axis-candidate-{index + 1:04d}"
        resolution_id = f"m2753-resolution-{index + 1:04d}"
        failure_family = "collision_negative_clearance" if collision else "offtrack_positive_clearance"
        localization_rows.append(
            {
                "localization_id": f"m2756-localization-{index + 1:04d}",
                "candidate_id": candidate_id,
                "resolution_id": resolution_id,
                "task_source_id": task_source_id,
                "workload_id": f"{task_source_id}::L3_online_gru",
                "profile_name": "L3_online_gru",
                "task_family": "T4" if index < 4 else "T5",
                "source_edge": "edge_a|edge_b",
                "stress_axis_primary": "actuator_delay_or_response" if index < 4 else "brake_or_drive_authority",
                "stress_axis_tags": "actuator_delay_or_response",
                "termination_reason": "obstacle_collision" if collision else "off_track",
                "outcome_bucket": "collision_failure" if collision else "off_track_noncollision_noncompletion",
                "failure_family": failure_family,
                "clearance_sign": "negative" if collision else "positive",
                "min_clearance_margin": -0.1 if collision else 4.0 + index,
                "return": 10.0 + index,
                "success": False,
                "collision": collision,
                "obstacle_completed": False,
                "candidate_admitted": True,
                "prior_panel_excluded": False,
                "localization_role": "negative_execution_row_failure_localization",
                "diagnostic_only_no_verdict": True,
                "ranking_run": False,
                "winner_selected": False,
                "checkpoint_promoted": False,
                "protected_rows_in_success_denominator": False,
                "hidden_oracle_actor_input_required": False,
                "localization_labels_actor_visible": False,
                "stress_axis_labels_actor_visible": False,
                "source_edge_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
                "actor_visible_allowed": False,
            }
        )
        m2753_candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "task_source_id": task_source_id,
                "workload_id": f"{task_source_id}::L3_online_gru",
                "profile_name": "L3_online_gru",
                "task_family": "T4" if index < 4 else "T5",
                "source_edge": "edge_a|edge_b",
                "window_tag": "window",
                "strata": "strata",
                "stress_axis_primary": "actuator_delay_or_response" if index < 4 else "brake_or_drive_authority",
                "stress_axis_tags": "actuator_delay_or_response",
                "profile_config_path": str(root / "config.json"),
                "checkpoint_path": str(root / "checkpoint.pt"),
                "executable_source_family": "source_family",
                "env_template_family": "template",
            }
        )
        m1690_rows.append(
            {
                **m2753_candidate_rows[-1],
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        )
        m2753_resolution_rows.append(
            {
                **m2753_candidate_rows[-1],
                "resolution_id": resolution_id,
                "resolution_status": "resolved",
                "execution_admitted": True,
                "execution_planned": True,
            }
        )
    write_json(
        m2756_dir / "summary.json",
        {
            "status_pass": True,
            "failure_localization_row_count": 12,
            "collision_negative_clearance_count": 3,
            "offtrack_positive_clearance_count": 9,
            "guardrail_context_row_count": 31,
        },
    )
    write_csv_rows(m2756_dir / "failure_localization_rows.csv", localization_rows)
    write_csv_rows(
        m2756_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_context_id": f"m2756-guardrail-{index + 1:04d}",
                "guardrail_source": "prior_panel" if index < 25 else "blocker",
                "guardrail_source_id": f"guard-{index + 1:04d}",
                "task_source_id": f"guard-task-{index + 1:04d}",
                "blocker_id": "",
                "route": "Route A",
                "evidence_family": "guardrail",
                "row_count": 1,
                "blocking_count": 0,
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "guardrail_role": "non_executed_guardrail_context",
            }
            for index in range(31)
        ],
    )
    write_csv_rows(
        m2756_dir / "actor_contract_guard_rows.csv",
        [
            {"guard_id": "obs", "guard_family": "p0_observation_dim", "observed": 72, "expected": 72, "status_pass": True},
            {"guard_id": "act", "guard_family": "action_dim", "observed": 3, "expected": 3, "status_pass": True},
        ],
    )
    write_csv_rows(m2756_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2756_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    write_csv_rows(m2753_dir / "cross_axis_candidate_rows.csv", m2753_candidate_rows)
    write_csv_rows(m2753_dir / "execution_candidate_resolution_rows.csv", m2753_resolution_rows)
    m1690_workload = root / "m1690.csv"
    write_csv_rows(m1690_workload, m1690_rows)
    (root / "config.json").write_text('{"env": {"history_length": 8}}\n', encoding="utf-8")
    (root / "checkpoint.pt").write_text("checkpoint placeholder\n", encoding="utf-8")
    specs = root / "specs.json"
    write_json(specs, {"executable_task_specs": [{"task_source_id": row["task_source_id"], "env_config": {}} for row in m2753_candidate_rows]})
    design = root / "m2758.md"
    design.write_text("M2758 admits M2759 bounded probe\n", encoding="utf-8")
    follow_up = root / "m2760.json"
    follow_up.write_text('{"id": "m2760"}\n', encoding="utf-8")
    return {
        "m2756_dir": m2756_dir,
        "m2753_dir": m2753_dir,
        "m1690_workload": m1690_workload,
        "specs": specs,
        "design": design,
        "follow_up": follow_up,
    }


def test_m2759_probe_execution_preserves_actor_and_claim_boundaries(monkeypatch, tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2759"
    doc_path = tmp_path / "m2759.md"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"]):
            collision = resolution["failure_family"] == "collision_negative_clearance"
            rows.append(
                {
                    "seed": 275900 + index,
                    "policy": "checkpoint",
                    "steps": 80 + index,
                    "collision": collision,
                    "obstacle_completed": False,
                    "success": False,
                    "termination_reason": "obstacle_collision" if collision else "off_track",
                    "min_clearance_margin": -0.2 if collision else 5.0,
                    "return": 1.0,
                    "action_rate_mean": 0.1,
                    "plan_action_rate_mean": 0.05,
                    "plan_first_action_error_mean": 0.02,
                    "high_sideslip_fraction": 0.0,
                    "speed_mean": 12.0,
                    "max_abs_yaw_rate": 0.3,
                    "beta_abs_peak": 0.2,
                    "max_off_track_overshoot": 0.0 if collision else 1.0,
                    "time_to_first_off_track_s": 1.5,
                    "off_track_severity_proxy": 0.4,
                    "impact_speed_proxy": 8.0 if collision else 0.0,
                    "impact_severity_proxy": 0.3 if collision else 0.0,
                    "recoverability_window_success": False,
                    "post_event_speed_mps": 4.0,
                    "post_event_yaw_rate_abs": 0.2,
                    "post_event_offtrack_overshoot": 0.0 if collision else 1.2,
                    "task_source_id": resolution["task_source_id"],
                    "workload_id": resolution["workload_id"],
                    "profile_name": resolution["profile_name"],
                    "task_family": resolution["task_family"],
                    "source_edge": resolution["source_edge"],
                    "training_started": False,
                    "replay_started": False,
                    "ppo_used": False,
                    "source_build_run": False,
                    "adapter_probe_run": False,
                    "external_simulation_run": False,
                    "actor_input_contract_changed": False,
                    "private_holdout_used": False,
                    "profile_specific_tuning": False,
                    "ranking_run": False,
                    "winner_selected": False,
                    "checkpoint_promoted": False,
                    "success_rate_verdict_claim_made": False,
                    "driver_performance_claim_made": False,
                    "paper_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
            rows[-1].update(m2759.probe_execution_metadata(resolution, eval_seed=275900 + index))
        write_csv_rows(output / "probe_execution_rows.csv", rows)
        write_csv_rows(output / "probe_execution_failure_rows.csv", [], fieldnames=m2759.FAILURE_FIELDNAMES)
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return {
            "result_class": "engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_execution_pass",
            "all_selected_metrics_finite": True,
        }

    monkeypatch.setattr(m2759, "run_probe_execution", fake_execution)
    summary = m2759.run_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight(
        m2756_dir=paths["m2756_dir"],
        m2758_design=paths["design"],
        m2753_dir=paths["m2753_dir"],
        m1690_workload=paths["m1690_workload"],
        executable_specs=paths["specs"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=paths["follow_up"],
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["localized_candidate_count"] == 12
    assert summary["resolved_candidate_count"] == 12
    assert summary["probe_execution_row_count"] == 12
    assert summary["probe_execution_failure_row_count"] == 0
    assert summary["collision_negative_clearance_count"] == 3
    assert summary["offtrack_positive_clearance_count"] == 9
    assert summary["guardrail_context_row_count"] == 31
    assert summary["action_response_probe_row_count"] == 12
    assert summary["containment_probe_row_count"] == 12
    assert summary["mechanism_context_row_count"] >= 24
    assert summary["guardrail_execution"] is False
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["diagnostic_labels_actor_visible"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    resolution_rows = _read_csv(output_dir / "probe_candidate_resolution_rows.csv")
    assert {row["execution_admitted"] for row in resolution_rows} == {"True"}
    assert {row["failure_family"] for row in resolution_rows} == {
        "collision_negative_clearance",
        "offtrack_positive_clearance",
    }

    guardrail_rows = _read_csv(output_dir / "guardrail_context_rows.csv")
    assert {row["execution_run"] for row in guardrail_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in guardrail_rows} == {"False"}

    action_rows = _read_csv(output_dir / "action_response_probe_rows.csv")
    containment_rows = _read_csv(output_dir / "containment_probe_rows.csv")
    mechanism_rows = _read_csv(output_dir / "mechanism_context_rows.csv")
    assert len(action_rows) == 12
    assert len(containment_rows) == 12
    assert {row["action_response_labels_actor_visible"] for row in action_rows} == {"False"}
    assert {row["containment_labels_actor_visible"] for row in containment_rows} == {"False"}
    assert {row["mechanism_tag_actor_visible"] for row in mechanism_rows} == {"False"}

    blocked_claims = [row for row in _read_csv(output_dir / "claim_boundary_rows.csv") if row["allowed_in_m2759"] == "False"]
    assert blocked_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
