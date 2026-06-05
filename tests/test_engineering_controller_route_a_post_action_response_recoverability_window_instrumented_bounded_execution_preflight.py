from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight import (
    run_post_action_response_recoverability_window_instrumented_bounded_execution_preflight,
)


def _touch(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _source_tree(tmp_path: Path) -> dict[str, Path]:
    m2813_dir = tmp_path / "m2813"
    m2807_dir = tmp_path / "m2807"
    m2810_dir = tmp_path / "m2810"
    for directory in (m2813_dir, m2807_dir, m2810_dir):
        directory.mkdir()

    mechanism_rows = []
    m2807_rows = []
    m2810_rows = []
    for index in range(1, 13):
        candidate_id = f"m2807-cross-axis-candidate-{index:04d}"
        resolution_id = f"m2807-resolution-{index:04d}"
        task_source_id = f"m1680-spec-{index:04d}"
        source_family = "offtrack_positive_clearance" if index <= 10 else "success_obstacle_pass"
        mechanism_rows.append(
            {
                "mechanism_id": f"m2813-action-response-mechanism-{index:04d}",
                "localization_id": f"m2810-localization-{index:04d}",
                "candidate_id": candidate_id,
                "resolution_id": resolution_id,
                "task_source_id": task_source_id,
                "task_family": "T4" if index <= 6 else "T5",
                "source_edge": "edge",
                "stress_axis_primary": "axis",
                "stress_axis_tags": "axis",
                "outcome_family": source_family,
                "success": index > 10,
                "collision": False,
                "offtrack_noncollision": index <= 10,
                "min_clearance_margin": 1.0,
                "metric_context_available": True,
                "diagnostic_only_no_verdict": True,
            }
        )
        m2807_rows.append(
            {
                "candidate_id": candidate_id,
                "resolution_id": resolution_id,
                "task_source_id": task_source_id,
                "workload_id": f"{task_source_id}::L3_online_gru",
                "profile_name": "L3_online_gru",
                "task_family": "T4" if index <= 6 else "T5",
                "source_edge": "edge",
                "window_tag": "window",
                "strata": "strata",
                "executable_source_family": "source",
                "env_template_family": "template",
                "profile_config_path": str(tmp_path / "config.json"),
                "checkpoint_path": str(tmp_path / "checkpoint.pt"),
                "eval_seed": 280700 + index,
                "outcome_bucket": "off_track_noncollision_noncompletion" if index <= 10 else "success_obstacle_pass",
                "termination_reason": "off_track" if index <= 10 else "",
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "stress_axis_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
            }
        )
        m2810_rows.append(
            {
                "localization_id": f"m2810-localization-{index:04d}",
                "candidate_id": candidate_id,
                "resolution_id": resolution_id,
                "task_source_id": task_source_id,
                "workload_id": f"{task_source_id}::L3_online_gru",
                "profile_name": "L3_online_gru",
            }
        )

    guardrail_rows = [
        {
            "guardrail_context_id": f"m2813-guardrail-context-{index:04d}",
            "guardrail_source": "prior_surface",
            "guardrail_source_id": f"prior-{index:04d}",
            "task_source_id": "",
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
            "guardrail_role": "protected",
        }
        for index in range(1, 45)
    ]
    actor_rows = [
        {
            "guard_id": "actor",
            "guard_family": "shape",
            "observed": True,
            "expected": True,
            "status_pass": True,
            "actor_visible_allowed": False,
            "claim_boundary": "test",
        }
    ]
    gate_rows = [
        {
            "gate_id": "gate",
            "gate_family": "test",
            "status_pass": True,
            "observed": True,
            "expected": True,
            "failure_type": "",
            "claim_boundary": "test",
        }
    ]

    write_json(m2813_dir / "summary.json", {"status_pass": True})
    write_csv_rows(m2813_dir / "action_response_mechanism_rows.csv", mechanism_rows)
    write_csv_rows(m2813_dir / "success_offtrack_contrast_rows.csv", [{"contrast_id": "a"}, {"contrast_id": "b"}])
    write_csv_rows(m2813_dir / "guardrail_context_rows.csv", guardrail_rows)
    write_csv_rows(m2813_dir / "actor_contract_guard_rows.csv", actor_rows)
    write_csv_rows(m2813_dir / "claim_boundary_rows.csv", [{"status_pass": True}])
    write_csv_rows(m2813_dir / "gate_matrix.csv", gate_rows)

    write_csv_rows(m2807_dir / "candidate_execution_rows.csv", m2807_rows)
    write_csv_rows(m2807_dir / "candidate_execution_failure_rows.csv", [])
    write_csv_rows(m2807_dir / "execution_candidate_resolution_rows.csv", [])
    write_csv_rows(m2807_dir / "gate_matrix.csv", gate_rows)

    write_json(m2810_dir / "summary.json", {"status_pass": True})
    write_csv_rows(m2810_dir / "failure_localization_rows.csv", m2810_rows)
    write_csv_rows(m2810_dir / "guardrail_context_rows.csv", guardrail_rows)
    write_csv_rows(m2810_dir / "actor_contract_guard_rows.csv", actor_rows)
    write_csv_rows(m2810_dir / "gate_matrix.csv", gate_rows)

    _touch(tmp_path / "m2815.md", "synthesis")
    _touch(tmp_path / "route.md", "route")
    _touch(tmp_path / "source.pt", "checkpoint")
    _touch(tmp_path / "specs.json", "{}")
    _touch(tmp_path / "follow_up.json", "{}")
    _touch(tmp_path / "config.json", "{}")
    _touch(tmp_path / "checkpoint.pt", "checkpoint")
    return {
        "m2815_synthesis": tmp_path / "m2815.md",
        "m2813_dir": m2813_dir,
        "m2807_dir": m2807_dir,
        "m2810_dir": m2810_dir,
        "source_checkpoint": tmp_path / "source.pt",
        "executable_specs": tmp_path / "specs.json",
        "route_plan": tmp_path / "route.md",
        "follow_up_manifest": tmp_path / "follow_up.json",
    }


def test_m2816_runner_builds_claim_safe_recoverability_artifacts(tmp_path, monkeypatch) -> None:
    paths = _source_tree(tmp_path)

    def fake_execution(**kwargs):
        rows = []
        for index, mechanism in enumerate(kwargs["mechanism_rows"], start=1):
            offtrack_source = index <= 10
            rows.append(
                {
                    "mechanism_id": mechanism["mechanism_id"],
                    "localization_id": mechanism["localization_id"],
                    "candidate_id": mechanism["candidate_id"],
                    "resolution_id": mechanism["resolution_id"],
                    "task_source_id": mechanism["task_source_id"],
                    "workload_id": mechanism["workload_id"],
                    "profile_name": mechanism["profile_name"],
                    "task_family": mechanism["task_family"],
                    "source_edge": mechanism["source_edge"],
                    "stress_axis_primary": mechanism["stress_axis_primary"],
                    "stress_axis_tags": mechanism["stress_axis_tags"],
                    "source_outcome_family": mechanism["outcome_family"],
                    "success": not offtrack_source,
                    "collision": False,
                    "obstacle_completed": not offtrack_source,
                    "termination_reason": "max_steps" if offtrack_source else "",
                    "outcome_bucket": "max_steps_noncompletion" if offtrack_source else "success_obstacle_pass",
                    "steps": 180,
                    "return": 10.0,
                    "min_clearance_margin": 1.0,
                    "speed_mean": 8.0,
                    "action_rate_mean": 0.01,
                    "previous_command_norm_mean": 0.2,
                    "previous_command_norm_peak": 0.3,
                    "current_action_norm_mean": 0.21,
                    "current_action_norm_peak": 0.31,
                    "action_trace_delta_mean": 0.02,
                    "action_trace_delta_peak": 0.04,
                    "high_sideslip_fraction": 0.0,
                    "time_to_first_off_track_s": 2.0 if offtrack_source else "",
                    "max_off_track_overshoot": 0.1 if offtrack_source else 0.0,
                    "off_track_severity_proxy": 0.1 if offtrack_source else 0.0,
                    "post_event_speed_mps": 7.8 if offtrack_source else "",
                    "post_event_speed_mps_available": offtrack_source,
                    "post_event_yaw_rate_abs": 0.2 if offtrack_source else "",
                    "post_event_yaw_rate_abs_available": offtrack_source,
                    "post_event_offtrack_overshoot": 0.0 if offtrack_source else "",
                    "post_event_offtrack_overshoot_available": offtrack_source,
                    "recoverability_window_success": False,
                    "recoverability_window_success_available": False,
                    "soft_offtrack_metric_enabled": True,
                    "soft_offtrack_tolerance_m": 1.0,
                    "m2816_eval_seed": 281600 + index,
                    "actor_input_contract_changed": False,
                    "hidden_oracle_actor_input_required": False,
                    "stress_axis_labels_actor_visible": False,
                    "success_progress_labels_actor_visible": False,
                    "verdict_labels_actor_visible": False,
                    "training_run": False,
                    "ranking_run": False,
                    "driver_performance_claim_made": False,
                    "paper_claim_made": False,
                    "current_sim_verdict_claim_made": False,
                    "level3_self_id_claim_made": False,
                    "protected_rows_in_success_denominator": False,
                }
            )
        return rows, [], {"status_pass": True, "all_selected_metrics_finite": True}

    monkeypatch.setattr(
        "autodrift.engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight.run_recoverability_panel_execution",
        fake_execution,
    )

    summary = run_post_action_response_recoverability_window_instrumented_bounded_execution_preflight(
        **paths,
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "m2816.md",
        seed_start_index=281600,
        horizon_steps=180,
        recoverability_window_steps=40,
    )

    assert summary["status_pass"] is True
    assert summary["mechanism_row_count"] == 12
    assert summary["source_offtrack_mechanism_row_count"] == 10
    assert summary["source_success_mechanism_row_count"] == 2
    assert summary["episode_count"] == 12
    assert summary["failure_count"] == 0
    assert summary["post_event_available_count"] == 10
    assert summary["recoverability_available_count"] == 0
    assert summary["recoverability_success_count"] == 0
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["claim_boundary_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert (tmp_path / "out" / "recoverability_window_rows.csv").exists()
    assert (tmp_path / "out" / "post_offtrack_action_response_rows.csv").exists()
