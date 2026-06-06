from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_per_step_telemetry_panel_materialization as m2857,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class _FakeModel:
    obs_dim = 72
    act_dim = 3
    actor_encoder = "human_view_online_gru"


def _source_artifacts(root: Path) -> dict[str, Path]:
    design = root / "m2856.md"
    design.write_text("M2856 design\n", encoding="utf-8")
    summary = root / "m2854-summary.json"
    write_json(
        summary,
        {
            "status_pass": True,
            "diagnostic_success_count": 0,
            "requires_step_trace_row_count": 2,
        },
    )
    localization = root / "m2854-localization.csv"
    write_csv_rows(
        localization,
        [
            {
                "pair_id": "m2850-pair-0001-m1680-spec-0000",
                "task_source_id": "m1680-spec-0000",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_family_tag": "t4_family_a",
                "scenario_role_primary": "capability_step_up",
                "localization_bucket": "clearance_progress_tradeoff",
                "training_recipe_signal": "progress_preserving_clearance_objective",
            },
            {
                "pair_id": "m2850-pair-0002-m1680-spec-0001",
                "task_source_id": "m1680-spec-0001",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_family_tag": "t4_family_b",
                "scenario_role_primary": "capability_step_down",
                "localization_bucket": "low_speed_invariant_noncompletion",
                "training_recipe_signal": "low_speed_guard_and_recovery_loss",
            },
        ],
    )
    workload = root / "m1690.csv"
    rows = []
    specs = []
    for index in range(3):
        task_source_id = f"m1680-spec-000{index}"
        config = root / f"{task_source_id}.json"
        write_json(config, {"env": {"history_length": 1}, "runtime": {}})
        rows.append(
            {
                "workload_id": f"{task_source_id}::L3_online_gru",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": f"source_family_{index}|role_{index}",
                "window_tag": "mapping_window_unspecified",
                "strata": "all_72_specs",
                "executable_source_family": f"source_family_{index}",
                "env_template_family": "template",
                "profile_config_path": str(config),
                "config_exists": True,
                "profile_specific_tuning": False,
            }
        )
        specs.append({"task_source_id": task_source_id, "env_config": {"history_length": 1, "max_steps": 12}})
    write_csv_rows(workload, rows)
    executable_specs = root / "specs.json"
    write_json(executable_specs, {"executable_task_specs": specs})
    baseline = root / "baseline.pt"
    candidate = root / "candidate.pt"
    baseline.write_text("baseline", encoding="utf-8")
    candidate.write_text("candidate", encoding="utf-8")
    return {
        "design": design,
        "summary": summary,
        "localization": localization,
        "workload": workload,
        "specs": executable_specs,
        "baseline": baseline,
        "candidate": candidate,
    }


def _fake_subject_registry(*, baseline_checkpoint: Path, candidate_checkpoint: Path, device: str):
    del device
    return {
        "baseline": {
            "subject": "baseline",
            "checkpoint_path": baseline_checkpoint,
            "checkpoint_hash": "baseline-hash",
            "model_state_hash": "baseline-state",
            "actor_encoder": "human_view_online_gru",
            "model": _FakeModel(),
        },
        "candidate": {
            "subject": "candidate",
            "checkpoint_path": candidate_checkpoint,
            "checkpoint_hash": "candidate-hash",
            "model_state_hash": "candidate-state",
            "actor_encoder": "human_view_online_gru",
            "model": _FakeModel(),
        },
    }


def _full_trace(surface: dict[str, object], subject: dict[str, object], step: int) -> dict[str, object]:
    row = {field: "" for field in m2857.PER_STEP_FIELDNAMES}
    row.update(
        {
            "trace_id": f"{surface['pair_id']}-{subject['subject']}-{step}",
            "surface_id": surface["surface_id"],
            "pair_id": surface["pair_id"],
            "task_source_id": surface["task_source_id"],
            "profile_name": surface["profile_name"],
            "checkpoint_subject": subject["subject"],
            "checkpoint_path": str(subject["checkpoint_path"]),
            "eval_seed": 285700,
            "step_index": step,
            "horizon_steps": 3,
            "terminated": step == 2,
            "truncated": False,
            "termination_reason": "speed_too_low" if step == 2 else "",
            "success_diagnostic": False,
            "collision_diagnostic": False,
            "obstacle_completed_diagnostic": False,
            "ego_vx": 2.0 - step * 0.4,
            "ego_vy": 0.1,
            "yaw_rate": 0.0,
            "ax": -0.1,
            "ay": 0.0,
            "steer_actuator": 0.0,
            "steer_rate": 0.0,
            "throttle_actuator": 0.1,
            "brake_actuator": 0.2,
            "previous_steer_command": 0.0,
            "previous_throttle_command": 0.0,
            "previous_brake_command": 0.0,
            "current_steer_command": 0.05 * step,
            "current_throttle_command": 0.1,
            "current_brake_command": -0.1,
            "action_delta_norm": 0.3 if step == 1 else 0.0,
            "speed_scalar": 2.0 - step * 0.6,
            "speed_delta_from_previous": -0.6 if step else 0.0,
            "min_obstacle_clearance": 1.0 + step * 0.1,
            "clearance_margin": 0.1 + step * 0.05,
            "clearance_delta_from_previous": 0.05 if step else 0.0,
            "return_increment": -0.1 if step == 1 else 0.0,
            "cumulative_return": -0.1 if step >= 1 else 0.0,
            "offtrack_margin_proxy": 0.0,
            "high_sideslip_proxy": 0.1,
            "response_prediction_available": False,
            "response_prediction_error_norm": "",
            "response_prediction_error_source": "not_computed_actor_invisible_instrumentation_gap",
            "diagnostic_only": True,
            "actor_visible_allowed": False,
            "hidden_oracle_actor_input_required": False,
        }
    )
    return row


def _fake_per_step_trace(**kwargs: object):
    surface = kwargs["surface_row"]
    subject = kwargs["subject_entry"]
    traces = [_full_trace(surface, subject, step) for step in range(3)]
    episode = {field: "" for field in m2857.EPISODE_FIELDNAMES}
    episode.update(
        {
            "surface_id": surface["surface_id"],
            "pair_id": surface["pair_id"],
            "task_source_id": surface["task_source_id"],
            "checkpoint_subject": subject["subject"],
            "steps": 3,
            "execution_status": "completed",
            "error_type": "",
            "error_message": "",
            "success_diagnostic": False,
            "collision_diagnostic": False,
            "termination_reason": "speed_too_low",
            "outcome_bucket": "speed_too_low_noncollision_noncompletion",
            "first_clearance_improvement_step": 1,
            "first_speed_drop_step": 1,
            "first_progress_loss_step": 1,
            "first_large_action_delta_step": 1,
            "first_low_speed_step": "",
            "clearance_improvement_before_speed_drop": False,
            "speed_drop_before_clearance_improvement": False,
            "low_speed_recovery_window_available": False,
            "candidate_minus_baseline_clearance_improvement_step_delta": "",
            "candidate_minus_baseline_speed_drop_step_delta": "",
            "candidate_minus_baseline_progress_loss_step_delta": "",
            "requires_training_recipe_redesign": True,
            "requires_fresh_panel_audit": surface["surface_id"] == "fresh_disjoint",
            "diagnostic_only": True,
            "ranking_admissible": False,
            "ordinary_success_denominator_allowed": False,
        }
    )
    return traces, episode


def test_m2857_materializes_per_step_artifacts_and_blocks_overclaims(monkeypatch, tmp_path: Path) -> None:
    paths = _source_artifacts(tmp_path)
    output_dir = tmp_path / "m2857"
    doc_path = tmp_path / "m2857.md"
    follow_up = tmp_path / "m2858.json"
    monkeypatch.setattr(m2857, "DEFAULT_PRIOR_SUMMARIES", ())
    monkeypatch.setattr(m2857, "DEFAULT_PRIOR_ROW_FILES", ())
    monkeypatch.setattr(m2857, "load_subject_registry", _fake_subject_registry)
    monkeypatch.setattr(m2857, "run_single_subject_per_step_trace", _fake_per_step_trace)

    summary = m2857.run_response_predictive_recurrent_belief_per_step_telemetry_panel_materialization(
        m2856_design=paths["design"],
        m2854_summary=paths["summary"],
        m2854_localization_rows=paths["localization"],
        m1690_workload=paths["workload"],
        executable_specs=paths["specs"],
        baseline_checkpoint=paths["baseline"],
        candidate_checkpoint=paths["candidate"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        eval_seed_base=285700,
        m2850_row_count=2,
        fresh_row_count=1,
        horizon_steps=3,
        device="cpu",
    )

    assert summary["status_pass"] is True
    assert summary["surface_row_count"] == 3
    assert summary["m2850_explanatory_surface_row_count"] == 2
    assert summary["fresh_disjoint_surface_row_count"] == 1
    assert summary["per_step_trace_row_count"] == 18
    assert summary["episode_trace_summary_row_count"] == 6
    assert summary["telemetry_localization_row_count"] == 3
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["ordinary_success_denominator_allowed"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_verdict_computed"] is False
    assert summary["training_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    surface_rows = _read_csv(output_dir / "telemetry_surface_rows.csv")
    trace_rows = _read_csv(output_dir / "per_step_trace_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert {row["surface_id"] for row in surface_rows} == {"m2850_explanatory", "fresh_disjoint"}
    assert all(row["diagnostic_only"] == "True" for row in trace_rows)
    assert all(row["actor_visible_allowed"] == "False" for row in trace_rows)
    assert any(row["claim_id"] == "m2857-claim-follow_up_result_audit_registered" for row in claim_rows)
    assert all(row["status_pass"] == "True" for row in gate_rows)
    assert follow_up.exists()
    assert doc_path.exists()
