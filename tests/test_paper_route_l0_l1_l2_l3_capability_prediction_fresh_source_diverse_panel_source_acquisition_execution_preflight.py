from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_source_acquisition_execution_preflight as m2908,
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _fixture_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    acquisition_rows: list[dict[str, object]] = []
    repair_rows: list[dict[str, object]] = []
    workload_rows: list[dict[str, object]] = []
    for index in range(1, 35):
        task_source_id = f"task-{index:03d}"
        if index <= 17:
            missing = "candidate_artifact_count>=2"
            required = "additional_independent_candidate_artifact"
            candidate_required = True
            source_required = False
            candidate_count = 1
            source_count = 2
            lane = "candidate_support_acquisition"
        elif index <= 27:
            missing = "source_family_tag_count>=2"
            required = "additional_independent_source_family"
            candidate_required = False
            source_required = True
            candidate_count = 2
            source_count = 1
            lane = "source_family_acquisition"
        else:
            missing = "candidate_artifact_count>=2;source_family_tag_count>=2"
            required = "additional_independent_candidate_artifact;additional_independent_source_family"
            candidate_required = True
            source_required = True
            candidate_count = 1
            source_count = 1
            lane = "dual_candidate_and_source_family_acquisition"
        task_family = "T4" if index <= 15 else "T5"
        family = f"family-{(index % 3) + 1}"
        env_family = f"env-{(index % 6) + 1}"
        acquisition_rows.append(
            {
                "acquisition_required_id": f"acquisition-{index:03d}",
                "seed_gap_row_id": f"seed-gap-{index:03d}",
                "candidate_id": f"candidate-{index:03d}",
                "task_source_id": task_source_id,
                "task_family": task_family,
                "env_template_family": env_family,
                "missing_requirement": missing,
                "required_acquisition": required,
                "candidate_support_acquisition_required": candidate_required,
                "source_family_acquisition_required": source_required,
                "may_seed_future_panel": True,
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": "fixture",
            }
        )
        repair_rows.append(
            {
                "repair_row_id": f"repair-{index:03d}",
                "seed_gap_row_id": f"seed-gap-{index:03d}",
                "candidate_id": f"candidate-{index:03d}",
                "task_source_id": task_source_id,
                "task_family": task_family,
                "source_edge": "fixture_edge",
                "env_template_family": env_family,
                "executable_source_family": family,
                "profile_count": 12,
                "missing_requirement": missing,
                "candidate_support_gap": candidate_required,
                "source_family_gap": source_required,
                "dual_gap": candidate_required and source_required,
                "observed_candidate_artifact_count": candidate_count,
                "observed_source_family_tag_count": source_count,
                "observed_diagnostic_artifact_count": 3,
                "existing_repo_local_support_sufficient": False,
                "acquisition_required": True,
                "projected_fresh_candidate_after_existing_support": False,
                "repair_lane": lane,
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": "fixture",
            }
        )
        workload_rows.append(
            {
                "workload_id": f"{task_source_id}::L3_online_gru",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": task_family,
                "source_edge": "fixture_edge",
                "window_tag": "fixture_window",
                "executable_source_family": family,
                "env_template_family": env_family,
                "strata": "fixture",
                "profile_config_path": "config.json",
                "checkpoint_path": "checkpoint.pt",
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        )
    return acquisition_rows, repair_rows, workload_rows


def _write_fixture_inputs(tmp_path: Path) -> dict[str, Path]:
    docs = tmp_path / "docs"
    docs.mkdir()
    m2907 = docs / "m2907.md"
    m2906 = docs / "m2906.md"
    m2907.write_text("m2907 fixture\n", encoding="utf-8")
    m2906.write_text("m2906 fixture\n", encoding="utf-8")
    m2905_dir = tmp_path / "runs" / "m2905"
    m2905_dir.mkdir(parents=True)
    acquisition_rows, repair_rows, workload_rows = _fixture_rows()
    write_csv_rows(m2905_dir / "acquisition_required_rows.csv", acquisition_rows)
    write_csv_rows(m2905_dir / "seed_gap_repair_rows.csv", repair_rows)
    write_json(m2905_dir / "summary.json", {"status_pass": True})
    workload = tmp_path / "m1690.csv"
    write_csv_rows(workload, workload_rows)
    specs = tmp_path / "specs.json"
    write_json(
        specs,
        {"executable_task_specs": [{"task_source_id": row["task_source_id"], "env_config": {}} for row in workload_rows]},
    )
    return {
        "m2907": m2907,
        "m2906": m2906,
        "m2905_dir": m2905_dir,
        "workload": workload,
        "specs": specs,
    }


def test_m2908_materializes_claim_safe_source_acquisition_execution_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    inputs = _write_fixture_inputs(tmp_path)
    output_dir = tmp_path / "runs" / "m2908"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2909.json"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"], start=1):
            rows.append(
                {
                    "source_acquisition_execution_id": f"source-acquisition-execution-{index:03d}",
                    "resolution_id": resolution["resolution_id"],
                    "source_acquisition_input_id": resolution["source_acquisition_input_id"],
                    "acquisition_required_id": resolution["acquisition_required_id"],
                    "seed_gap_row_id": resolution["seed_gap_row_id"],
                    "candidate_id": resolution["candidate_id"],
                    "task_source_id": resolution["task_source_id"],
                    "workload_id": resolution["workload_id"],
                    "profile_name": "L3_online_gru",
                    "executable_source_family": resolution["workload_executable_source_family"],
                    "env_template_family": resolution["workload_env_template_family"],
                    "eval_seed": 290800 + index - 1,
                    "success": index % 5 == 0,
                    "collision": False,
                    "obstacle_completed": index % 5 == 0,
                    "termination_reason": "obstacle_completed" if index % 5 == 0 else "off_track",
                    "steps": 90 + index,
                    "return": 1.0,
                    "min_clearance_margin": 0.1,
                    "paper_proof_allowed": False,
                    "validation_denominator_allowed": False,
                    "ordinary_success_denominator_allowed": False,
                    "hidden_oracle_actor_input_required": False,
                    "future_target_actor_input_required": False,
                    "evaluator_targets_actor_visible": False,
                    "ranking_run": False,
                    "model_quality_claim_made": False,
                    "paper_claim_made": False,
                    "finite_window_vs_gru_claim_made": False,
                    "level3_self_id_claim_made": False,
                    "driver_performance_claim_made": False,
                    "current_sim_verdict_claim_made": False,
                    "high_fidelity_validation_claim_made": False,
                    "full_ideal_driver_gate_passed": False,
                    "claim_boundary": m2908.CLAIM_SCOPE,
                }
            )
        write_csv_rows(output / "source_acquisition_execution_rows.csv", rows)
        write_csv_rows(output / "acquisition_failure_rows.csv", [], fieldnames=list(m2908.FAILURE_FIELDNAMES))
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return {
            "execution_row_count": len(rows),
            "failure_row_count": 0,
            "accounted_row_count": len(rows),
            "all_selected_metrics_finite": True,
        }

    monkeypatch.setattr(m2908, "run_source_acquisition_execution", fake_execution)
    summary = m2908.write_preflight_artifacts(
        m2907_synthesis=inputs["m2907"],
        m2905_dir=inputs["m2905_dir"],
        m2906_audit=inputs["m2906"],
        m1690_workload=inputs["workload"],
        executable_specs=inputs["specs"],
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["fixed_m2905_acquisition_required_row_count"] == 34
    assert summary["source_acquisition_execution_row_count"] == 34
    assert summary["acquisition_failure_row_count"] == 0
    assert summary["candidate_support_required_count"] == 24
    assert summary["candidate_support_evidence_added_count"] == 24
    assert summary["source_family_required_count"] == 17
    assert summary["independent_source_family_evidence_added_count"] == 0
    assert summary["source_family_evidence_rejection_counts"] == {
        "same_executable_source_family_not_independent": 17
    }
    assert summary["repaired_candidate_projection_count"] == 17
    assert summary["projected_design_targets_satisfied"] is False
    assert summary["model_quality_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    claim_rows = _read_rows(output_dir / "claim_rows.csv")
    split_rows = _read_rows(output_dir / "split_boundary_rows.csv")
    gate_rows = _read_rows(output_dir / "gate_rows.csv")
    source_rows = _read_rows(output_dir / "source_family_evidence_rows.csv")
    projection_rows = _read_rows(output_dir / "repaired_candidate_projection_rows.csv")

    assert {row["claim_made"] for row in claim_rows} == {"False"}
    assert {row["validation_denominator_allowed"] for row in split_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["independent_source_family_evidence_added"] for row in source_rows} == {"False"}
    assert len(projection_rows) == 17
    assert read_json(follow_up_manifest)["id"] == m2908.NEXT_ID


def test_m2908_fails_closed_when_execution_surface_is_not_resolved(
    monkeypatch,
    tmp_path: Path,
) -> None:
    inputs = _write_fixture_inputs(tmp_path)
    output_dir = tmp_path / "runs" / "m2908"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2909.json"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        write_csv_rows(output / "source_acquisition_execution_rows.csv", [], fieldnames=list(m2908.EXECUTION_FIELDNAMES))
        failures = [
            m2908.failure_row(
                resolution,
                eval_seed=290800 + index,
                failure_index=index + 1,
                error_type="ValueError",
                error_message="resolution not admitted",
                failure_stage="source_acquisition_execution",
            )
            for index, resolution in enumerate(kwargs["resolution_rows"])
        ]
        write_csv_rows(output / "acquisition_failure_rows.csv", failures, fieldnames=list(m2908.FAILURE_FIELDNAMES))
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(failures)})
        return {
            "execution_row_count": 0,
            "failure_row_count": len(failures),
            "accounted_row_count": len(failures),
            "all_selected_metrics_finite": False,
        }

    monkeypatch.setattr(m2908, "run_source_acquisition_execution", fake_execution)
    inputs["workload"].write_text("workload_id,task_source_id,profile_name\n", encoding="utf-8")
    summary = m2908.write_preflight_artifacts(
        m2907_synthesis=inputs["m2907"],
        m2905_dir=inputs["m2905_dir"],
        m2906_audit=inputs["m2906"],
        m1690_workload=inputs["workload"],
        executable_specs=inputs["specs"],
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        resume=False,
    )

    assert summary["status_pass"] is False
    assert summary["decision"] == "source_acquisition_execution_preflight_incomplete"
    assert summary["source_acquisition_execution_row_count"] == 0
    assert summary["acquisition_failure_row_count"] == 34
    failed_gates = [row for row in _read_rows(output_dir / "gate_rows.csv") if row["status_pass"] == "False"]
    assert {row["gate_id"] for row in failed_gates} >= {
        "gate-005-any_closed_loop_execution_rows",
        "gate-006-all_selected_metrics_finite_for_execution_rows",
    }
