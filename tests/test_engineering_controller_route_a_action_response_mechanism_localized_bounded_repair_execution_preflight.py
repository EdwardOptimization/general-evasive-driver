from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight as m2769,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2766_dir = root / "m2766"
    m2766_dir.mkdir()
    repair_rows = []
    mechanism_rows = []
    telemetry_rows = []
    workload_rows = []
    specs = []
    admitted_indices = {0, 1, 3, 4, 8, 9, 10, 11}
    for index in range(12):
        admitted = index in admitted_indices
        task_source_id = f"m1680-spec-{index + 1:04d}"
        source_candidate_id = f"m2753-cross-axis-candidate-{index + 1:04d}"
        mechanism_id = f"m2766-mechanism-localization-{index + 1:04d}"
        telemetry_id = f"m2766-telemetry-join-{index + 1:04d}"
        if index == 9:
            primary = "obstacle_timing_context"
            target = "obstacle_timing_or_clearance_margin_target"
        elif admitted:
            primary = "track_containment_context"
            target = "track_containment_stability_target"
        else:
            primary = "diagnostic_success_context"
            target = "context_only_no_repair_target"
        repair_rows.append(
            {
                "repair_admission_id": f"m2766-repair-admission-{index + 1:04d}",
                "mechanism_localization_id": mechanism_id,
                "candidate_id": source_candidate_id,
                "task_source_id": task_source_id,
                "primary_mechanism": primary,
                "repair_target_class": target,
                "repair_admitted_for_design": admitted,
                "repair_admission_status": "bounded_repair_design_candidate" if admitted else "context_only_no_repair_design",
                "admission_basis": "row_level_mechanism_localization_non_ranking",
                "ranking_run": False,
                "winner_selected": False,
                "success_rate_verdict_claim_made": False,
                "repair_success_claim_made": False,
                "driver_performance_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": m2769.CLAIM_SCOPE,
            }
        )
        mechanism_rows.append(
            {
                "mechanism_localization_id": mechanism_id,
                "telemetry_join_id": telemetry_id,
                "probe_resolution_id": f"m2764-probe-resolution-{index + 1:04d}",
                "candidate_id": source_candidate_id,
                "localization_id": f"m2756-localization-{index + 1:04d}",
                "task_source_id": task_source_id,
                "failure_family": "offtrack_positive_clearance",
                "termination_reason": "off_track" if admitted else "",
                "diagnostic_outcome_bucket": "offtrack_context" if admitted else "diagnostic_success_context",
                "primary_mechanism": primary,
                "secondary_mechanisms": "command_response_mismatch_context",
                "command_response_mismatch_score": 0.01,
                "track_containment_score": 1.0 if target == "track_containment_stability_target" else 0.0,
                "obstacle_timing_score": 1.0 if target == "obstacle_timing_or_clearance_margin_target" else 0.0,
                "mixed_mechanism_score": 0.0,
                "finite_telemetry": True,
                "containment_failure_flag": admitted,
                "collision_risk_flag": False,
                "repair_target_class": target,
                "repair_target_basis": "finite_telemetry_plus_containment_context",
                "mechanism_localization_labels_actor_visible": False,
                "ranking_run": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": m2769.CLAIM_SCOPE,
            }
        )
        telemetry_rows.append(
            {
                "telemetry_join_id": telemetry_id,
                "probe_id": f"m2764-action-response-probe-{index + 1:04d}",
                "probe_resolution_id": f"m2764-probe-resolution-{index + 1:04d}",
                "candidate_id": source_candidate_id,
                "localization_id": f"m2756-localization-{index + 1:04d}",
                "task_source_id": task_source_id,
                "failure_family": "offtrack_positive_clearance",
                "termination_reason": "off_track" if admitted else "",
                "diagnostic_success": not admitted,
                "collision": False,
                "min_clearance_margin": 5.0 + index,
                "previous_command": 0.2,
                "current_action": 0.3,
                "trace_delta_proxy": 0.1,
                "speed_response_proxy": 10.0,
                "yaw_response_proxy": 0.2,
                "beta_response_proxy": 0.1,
                "finite_metric": True,
                "m2762_contract_satisfied": True,
                "m2764_telemetry_coverage_improved": True,
                "m2759_row_backfilled": False,
                "actor_visible_allowed": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": m2769.CLAIM_SCOPE,
            }
        )
        workload_rows.append(
            {
                "workload_id": f"{task_source_id}::L3_online_gru",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": "T4" if index < 6 else "T5",
                "source_edge": "edge",
                "window_tag": "window",
                "executable_source_family": "family",
                "env_template_family": "template",
                "strata": "strata",
                "profile_config_path": str(root / "config.json"),
                "checkpoint_path": str(root / "checkpoint.pt"),
            }
        )
        specs.append({"task_source_id": task_source_id, "env_config": {}})
    write_json(m2766_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2766_dir / "repair_admission_rows.csv", repair_rows)
    write_csv_rows(m2766_dir / "mechanism_localization_rows.csv", mechanism_rows)
    write_csv_rows(m2766_dir / "telemetry_join_rows.csv", telemetry_rows)
    write_csv_rows(
        m2766_dir / "guardrail_context_rows.csv",
        [
            {
                "m2766_guardrail_id": f"m2766-guardrail-context-{index + 1:04d}",
                "guardrail_context_id": f"m2756-guardrail-{index + 1:04d}",
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
            }
            for index in range(31)
        ],
    )
    write_csv_rows(m2766_dir / "actor_contract_guard_rows.csv", [{"guard_id": "obs", "status_pass": True}])
    write_csv_rows(m2766_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2766_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    write_csv_rows(root / "workload.csv", workload_rows)
    write_json(root / "specs.json", {"executable_task_specs": specs})
    (root / "config.json").write_text('{"env": {"history_length": 8}}\n', encoding="utf-8")
    (root / "checkpoint.pt").write_text("checkpoint placeholder\n", encoding="utf-8")
    design = root / "m2768.md"
    design.write_text("M2768 admits M2769 bounded repair execution preflight.\n", encoding="utf-8")
    return {
        "m2766_dir": m2766_dir,
        "workload": root / "workload.csv",
        "specs": root / "specs.json",
        "checkpoint": root / "checkpoint.pt",
        "design": design,
    }


def test_m2769_bounded_repair_preflight_preserves_surface(monkeypatch, tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2769"
    doc_path = tmp_path / "m2769.md"
    follow_up = tmp_path / "m2770.json"

    def fake_checkpoints(**kwargs: object) -> list[dict[str, object]]:
        output = Path(kwargs["output_dir"])
        rows = []
        for spec in m2769.DEFAULT_REPAIR_SPECS:
            checkpoint_path = output / "checkpoints" / f"{spec['repair_candidate_id']}.pt"
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_path.write_text("fake checkpoint\n", encoding="utf-8")
            rows.append(
                {
                    "repair_candidate_id": spec["repair_candidate_id"],
                    "repair_lever_family": spec["repair_lever_family"],
                    "source_checkpoint_path": str(kwargs["source_checkpoint"]),
                    "repair_checkpoint_path": str(checkpoint_path),
                    "source_checkpoint_hash": "source",
                    "repair_checkpoint_hash": "repair",
                    "source_model_state_hash": "source-state",
                    "repair_model_state_hash": "repair-state",
                    "actor_mean_bias_before": "[0,0,0]",
                    "actor_mean_bias_after": "[0,0,0]",
                    "steer_bias_delta": spec["steer_bias_delta"],
                    "throttle_bias_delta": spec["throttle_bias_delta"],
                    "brake_bias_delta": spec["brake_bias_delta"],
                    "target_class_focus": spec["target_class_focus"],
                    "trainable_parameter_names": "actor_mean.bias[0];actor_mean.bias[1];actor_mean.bias[2]",
                    "finite_update": True,
                    "actor_contract_shape_72_action_3": True,
                    "hidden_oracle_actor_input_required": False,
                    "active_config_overwritten": False,
                    "environment_difficulty_relaxed": False,
                    "profile_specific_tuning": False,
                    "per_row_tuning": False,
                    "checkpoint_promoted": False,
                    "repair_training_started": False,
                    "ppo_used": False,
                    "ranking_run": False,
                    "winner_selected": False,
                    "claim_boundary": m2769.CLAIM_SCOPE,
                }
            )
        return rows

    def fake_execution(**kwargs: object) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"], start=1):
            row = {
                "success": False,
                "collision": False,
                "obstacle_completed": False,
                "termination_reason": "off_track",
                "min_clearance_margin": 1.0 + index,
                "return": 0.5,
                "steps": 80,
                "action_rate_mean": 0.1,
                "high_sideslip_fraction": 0.0,
                "previous_command_norm_mean": 0.2,
                "current_action_norm_mean": 0.3,
                "action_trace_delta_mean": 0.04,
                "action_trace_delta_peak": 0.08,
            }
            row.update(m2769.execution_metadata(resolution, eval_seed=276900 + index, index=index))
            rows.append(row)
        write_json(Path(kwargs["output_dir"]) / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return rows, []

    monkeypatch.setattr(m2769, "write_repair_checkpoint_rows", fake_checkpoints)
    monkeypatch.setattr(m2769, "run_repair_execution", fake_execution)
    summary = m2769.run(
        m2766_dir=paths["m2766_dir"],
        m2768_design=paths["design"],
        m1690_workload=paths["workload"],
        executable_specs=paths["specs"],
        source_checkpoint=paths["checkpoint"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["repair_candidate_row_count"] == 8
    assert summary["context_only_regression_row_count"] == 4
    assert summary["guardrail_context_row_count"] == 31
    assert summary["repair_checkpoint_row_count"] == 3
    assert summary["repair_candidate_resolution_row_count"] == 24
    assert summary["baseline_join_row_count"] == 8
    assert summary["repair_execution_row_count"] == 24
    assert summary["repair_execution_failure_row_count"] == 0
    assert summary["m2759_rows_backfilled"] is False
    assert summary["guardrail_execution"] is False
    assert summary["context_only_execution"] is False
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["diagnostic_labels_actor_visible"] is False
    assert summary["environment_difficulty_relaxed"] is False
    assert summary["active_config_overwritten"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert follow_up.exists()
    assert doc_path.exists()
    assert len(_read_csv(output_dir / "repair_candidate_rows.csv")) == 8
    assert len(_read_csv(output_dir / "context_only_regression_rows.csv")) == 4
    assert len(_read_csv(output_dir / "repair_execution_rows.csv")) == 24
