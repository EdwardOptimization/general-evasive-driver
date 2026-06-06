from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_repair_execution_preflight as m2931


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path, *, checkpoint: Path, profile_config: Path) -> dict[str, Path]:
    m2925_dir = root / "m2925"
    m2928_dir = root / "m2928"
    m2919_dir = root / "m2919"
    specs_path = root / "executable_task_specs.json"
    workload_path = root / "executable_workload_matrix.csv"
    m2929_audit = root / "m2929.md"
    m2930_design = root / "m2930.md"

    offtrack_rows = [
        {
            "offtrack_slice_id": "offtrack-1",
            "source_milestone": "m2737",
            "source_family": "source_family_a",
            "source_edge": "edge-a",
            "source_row_id": "source-row-1",
            "task_family": "T4",
            "task_source_id": "spec-0",
            "workload_id": "spec-0::L3_online_gru",
            "profile_name": "L3_online_gru",
            "checkpoint_context": "public_pilot_l3_checkpoint",
            "checkpoint_path": "old-public.pt",
            "env_template_family": "env-a",
            "window_tag": "window-a",
            "profile_env_history_length": "1",
            "offtrack_severity_band": "low_overshoot_le_0p02",
            "time_to_offtrack_band": "early_le_1p75s",
            "execution_candidate_id": "m2919-execution-candidate-0001",
            "resolution_id": "m2919-resolution-0001",
            "m2925_execution_performed": False,
            "ranking_claim_made": False,
            "success_rate_verdict_claim_made": False,
            "actor_visible": False,
            "diagnostic_only_no_verdict": True,
        },
        {
            "offtrack_slice_id": "offtrack-2",
            "source_milestone": "m2746",
            "source_family": "source_family_b",
            "source_edge": "edge-b",
            "source_row_id": "source-row-2",
            "task_family": "T5",
            "task_source_id": "spec-1",
            "workload_id": "spec-1::L3_online_gru",
            "profile_name": "L3_online_gru",
            "checkpoint_context": "m2655_mitigation_preserving_checkpoint",
            "checkpoint_path": str(checkpoint),
            "env_template_family": "env-b",
            "window_tag": "window-b",
            "profile_env_history_length": "1",
            "offtrack_severity_band": "medium_overshoot_le_0p08",
            "time_to_offtrack_band": "mid_le_2p5s",
            "execution_candidate_id": "m2919-execution-candidate-0002",
            "resolution_id": "m2919-resolution-0002",
            "m2925_execution_performed": False,
            "ranking_claim_made": False,
            "success_rate_verdict_claim_made": False,
            "actor_visible": False,
            "diagnostic_only_no_verdict": True,
        },
    ]
    context_rows = [
        {
            "context_row_id": "context-1",
            "outcome_family": "speed_too_low",
            "termination_reason": "speed_too_low",
            "success": False,
            "collision": False,
            "source_milestone": "m2737",
            "task_family": "T4",
            "checkpoint_context": "m2655_mitigation_preserving_checkpoint",
            "checkpoint_path": str(checkpoint),
            "env_template_family": "env-c",
            "window_tag": "window-c",
            "source_row_id": "source-row-3",
            "execution_candidate_id": "m2919-execution-candidate-0003",
            "resolution_id": "m2919-resolution-0003",
            "ordinary_engineering_denominator_allowed": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "high_fidelity_readiness_allowed": False,
            "self_id_claim_allowed": False,
            "m2925_execution_performed": False,
            "ranking_claim_made": False,
            "actor_visible": False,
            "diagnostic_only_no_verdict": True,
        }
    ]
    guardrail_rows = [
        {"guardrail_family": "m2877_fixed_post_package_rows", "execution_run": False},
        {"guardrail_family": "route_b_context_only", "execution_run": False},
        {"guardrail_family": "route_c_source_unavailable_rows", "execution_run": False},
    ]
    write_json(
        m2925_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "offtrack_row_count": 2,
            "non_offtrack_context_row_count": 1,
            "guardrail_context_row_count": 3,
        },
    )
    write_csv_rows(m2925_dir / "offtrack_slice_rows.csv", offtrack_rows)
    write_csv_rows(m2925_dir / "non_offtrack_context_rows.csv", context_rows)
    write_csv_rows(m2925_dir / "guardrail_context_rows.csv", guardrail_rows)

    m2919_rows = [
        {
            "execution_candidate_id": "m2919-execution-candidate-0003",
            "resolution_id": "m2919-resolution-0003",
            "source_milestone": "m2737",
            "source_family": "source_family_context",
            "source_edge": "edge-c",
            "source_row_id": "source-row-3",
            "task_family": "T4",
            "task_source_id": "spec-2",
            "workload_id": "spec-2::L3_online_gru",
            "profile_name": "L3_online_gru",
            "checkpoint_path": str(checkpoint),
            "profile_config_path": str(profile_config),
            "env_template_family": "env-c",
            "window_tag": "window-c",
            "profile_env_history_length": "1",
            "termination_reason": "speed_too_low",
            "success": False,
            "collision": False,
        }
    ]
    write_csv_rows(m2919_dir / "bounded_execution_rows.csv", m2919_rows)

    coverage_rows = [
        {
            "coverage_constraint_id": "coverage-total",
            "coverage_family": "denominator",
            "coverage_value": "total_m2925_rows",
            "observed_row_count": 3,
            "expected_row_count": 3,
            "source_scope": "m2925_offtrack_plus_context_rows",
            "coverage_constraint_status_pass": True,
            "ranking_claim_made": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "high_fidelity_readiness_allowed": False,
            "self_id_claim_allowed": False,
            "actor_visible": False,
            "diagnostic_only_no_verdict": True,
        },
        {
            "coverage_constraint_id": "coverage-offtrack",
            "coverage_family": "denominator",
            "coverage_value": "offtrack_rows",
            "observed_row_count": 2,
            "expected_row_count": 2,
            "source_scope": "m2925_offtrack_slice_rows",
            "coverage_constraint_status_pass": True,
            "ranking_claim_made": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "high_fidelity_readiness_allowed": False,
            "self_id_claim_allowed": False,
            "actor_visible": False,
            "diagnostic_only_no_verdict": True,
        },
        {
            "coverage_constraint_id": "coverage-context",
            "coverage_family": "denominator",
            "coverage_value": "context_rows",
            "observed_row_count": 1,
            "expected_row_count": 1,
            "source_scope": "m2925_non_offtrack_context_rows",
            "coverage_constraint_status_pass": True,
            "ranking_claim_made": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "high_fidelity_readiness_allowed": False,
            "self_id_claim_allowed": False,
            "actor_visible": False,
            "diagnostic_only_no_verdict": True,
        },
    ]
    shortcut_rows = [
        {"shortcut_family": family, "status_pass": True, "claim_made": False}
        for family in sorted(m2931.REQUIRED_SHORTCUT_FAMILIES)
    ]
    write_json(
        m2928_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "offtrack_row_count": 2,
            "non_offtrack_context_row_count": 1,
            "coverage_constraint_row_count": 3,
            "shortcut_exclusion_row_count": 7,
        },
    )
    write_csv_rows(m2928_dir / "repair_hypothesis_rows.csv", [{"repair_hypothesis_id": "hypothesis"}])
    write_csv_rows(m2928_dir / "coverage_constraint_rows.csv", coverage_rows)
    write_csv_rows(m2928_dir / "shortcut_exclusion_rows.csv", shortcut_rows)
    write_csv_rows(m2928_dir / "actor_contract_guard_rows.csv", [{"guard_id": "obs", "status_pass": True}])
    write_csv_rows(m2928_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2928_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])

    workload_rows = [
        {
            "workload_id": f"spec-{index}::L3_online_gru",
            "task_source_id": f"spec-{index}",
            "profile_name": "L3_online_gru",
            "task_family": "T4" if index != 1 else "T5",
            "source_edge": f"edge-{index}",
            "window_tag": f"window-{index}",
            "executable_source_family": f"family-{index}",
            "env_template_family": f"env-{index}",
            "strata": "test",
            "profile_config_path": str(profile_config),
            "checkpoint_path": str(checkpoint),
            "config_exists": True,
            "checkpoint_exists": True,
            "environment_rollout_scheduled": False,
            "training_scheduled": False,
            "profile_specific_tuning": False,
        }
        for index in range(3)
    ]
    write_json(specs_path, {"executable_task_specs": [{"task_source_id": f"spec-{index}"} for index in range(3)]})
    write_csv_rows(workload_path, workload_rows)

    m2929_audit.write_text("M2929 accepts M2928 complete and claim-safe.\n", encoding="utf-8")
    m2930_design.write_text(f"next: {m2931.MILESTONE_ID}\n", encoding="utf-8")
    return {
        "m2925_dir": m2925_dir,
        "m2928_dir": m2928_dir,
        "m2919_dir": m2919_dir,
        "m2929_audit": m2929_audit,
        "m2930_design": m2930_design,
        "executable_specs": specs_path,
        "executable_workload": workload_path,
    }


def test_candidate_rows_enrich_context_from_m2919(tmp_path: Path, monkeypatch) -> None:
    checkpoint = tmp_path / "repair.pt"
    profile_config = tmp_path / "profile.json"
    checkpoint.write_bytes(b"checkpoint")
    write_json(profile_config, {"env": {"history_length": 1}})
    monkeypatch.setattr(m2931, "DEFAULT_REPAIR_CANDIDATE_CHECKPOINT", checkpoint)
    monkeypatch.setattr(m2931, "DEFAULT_REPAIR_PROFILE_CONFIG", profile_config)
    paths = _write_source_artifacts(tmp_path, checkpoint=checkpoint, profile_config=profile_config)
    source = m2931.load_source_artifacts(
        m2925_dir=paths["m2925_dir"],
        m2928_dir=paths["m2928_dir"],
        m2919_dir=paths["m2919_dir"],
        m2929_audit=paths["m2929_audit"],
        m2930_design=paths["m2930_design"],
        executable_specs=paths["executable_specs"],
        executable_workload=paths["executable_workload"],
        repair_candidate_checkpoint=checkpoint,
        repair_profile_config=profile_config,
        follow_up_manifest=tmp_path / "m2932.json",
    )

    rows = m2931.build_repair_execution_candidate_rows(source)

    assert len(rows) == 3
    context = [row for row in rows if row["panel_row_family"] == "non_offtrack_context_regression"][0]
    assert context["workload_id"] == "spec-2::L3_online_gru"
    assert context["task_source_id"] == "spec-2"
    assert context["repair_candidate_checkpoint_path"] == str(checkpoint)
    assert {row["validation_denominator_allowed"] for row in rows} == {False}
    assert {row["ranking_run"] for row in rows} == {False}


def test_run_repair_execution_preflight_writes_claim_safe_artifacts(tmp_path: Path, monkeypatch) -> None:
    checkpoint = tmp_path / "repair.pt"
    profile_config = tmp_path / "profile.json"
    checkpoint.write_bytes(b"checkpoint")
    write_json(profile_config, {"env": {"history_length": 1}})
    monkeypatch.setattr(m2931, "DEFAULT_REPAIR_CANDIDATE_CHECKPOINT", checkpoint)
    monkeypatch.setattr(m2931, "DEFAULT_REPAIR_PROFILE_CONFIG", profile_config)
    monkeypatch.setattr(m2931, "EXPECTED_TOTAL_ROW_COUNT", 3)
    monkeypatch.setattr(m2931, "EXPECTED_OFFTRACK_COUNT", 2)
    monkeypatch.setattr(m2931, "EXPECTED_NON_OFFTRACK_CONTEXT_COUNT", 1)
    monkeypatch.setattr(m2931, "EXPECTED_COVERAGE_CONSTRAINT_COUNT", 3)
    monkeypatch.setattr(m2931, "EXPECTED_SOURCE_MILESTONE_COUNTS", {"m2737": 1, "m2746": 1})
    monkeypatch.setattr(m2931, "EXPECTED_TASK_FAMILY_COUNTS", {"T4": 1, "T5": 1})
    monkeypatch.setattr(m2931, "load_actor_critic_checkpoint", lambda *args, **kwargs: (object(), {}))

    def fake_execute_repair_candidate_row(*, workload, executable_spec, profile_config, model, profile_row, eval_seed):
        return {
            "seed": eval_seed,
            "policy": "checkpoint",
            "steps": 12,
            "terminated": True,
            "truncated": False,
            "collision": False,
            "obstacle_completed": False,
            "min_obstacle_clearance": 5.0,
            "obstacle_collision_radius": 1.0,
            "min_clearance_margin": 4.0,
            "termination_reason": "off_track" if workload["task_source_id"] == "spec-1" else "speed_too_low",
            "completion_reason": "diagnostic",
            "outcome_bucket": "diagnostic",
            "return": 1.5,
            "mean_reward": 0.1,
            "lateral_rmse": 0.2,
            "beta_abs_error_mean": 0.3,
            "high_sideslip_fraction": 0.0,
            "speed_mean": 4.5,
            "action_rate_mean": 0.01,
            "max_off_track_overshoot": 0.03,
            "time_to_first_off_track_s": 1.5,
            "off_track_severity_proxy": 0.03,
            "recoverability_window_success": False,
            "recoverability_window_success_available": False,
            "success": False,
            "workload_id": workload["workload_id"],
            "task_source_id": workload["task_source_id"],
            "profile_name": workload["profile_name"],
            "task_family": workload["task_family"],
            "source_edge": workload["source_edge"],
            "window_tag": workload["window_tag"],
            "strata": workload["strata"],
            "executable_source_family": workload["executable_source_family"],
            "env_template_family": workload["env_template_family"],
            "profile_config_path": workload["profile_config_path"],
            "checkpoint_path": workload["checkpoint_path"],
            "profile_env_history_length": 1,
            "eval_seed": eval_seed,
        }

    monkeypatch.setattr(m2931, "execute_repair_candidate_row", fake_execute_repair_candidate_row)
    paths = _write_source_artifacts(tmp_path, checkpoint=checkpoint, profile_config=profile_config)
    output_dir = tmp_path / "m2931"
    doc_path = tmp_path / "m2931.md"
    follow_up = tmp_path / "m2932.json"

    summary = m2931.run_offtrack_dominant_repair_execution_preflight(
        m2925_dir=paths["m2925_dir"],
        m2928_dir=paths["m2928_dir"],
        m2919_dir=paths["m2919_dir"],
        m2929_audit=paths["m2929_audit"],
        m2930_design=paths["m2930_design"],
        executable_specs=paths["executable_specs"],
        executable_workload=paths["executable_workload"],
        repair_candidate_checkpoint=checkpoint,
        repair_profile_config=profile_config,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        device="cpu",
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["candidate_count"] == 3
    assert summary["offtrack_candidate_count"] == 2
    assert summary["non_offtrack_context_candidate_count"] == 1
    assert summary["resolved_candidate_count"] == 3
    assert summary["repair_execution_row_count"] == 3
    assert summary["repair_execution_failure_row_count"] == 0
    assert summary["accounted_candidate_count"] == 3
    assert summary["source_milestone_counts"] == {"m2737": 1, "m2746": 1}
    assert summary["panel_source_milestone_counts"] == {"m2737": 2, "m2746": 1}
    assert summary["repair_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["validation_readiness_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2931.NEXT_ID

    candidates = _read_csv(output_dir / "repair_execution_candidate_rows.csv")
    resolutions = _read_csv(output_dir / "repair_execution_resolution_rows.csv")
    executions = _read_csv(output_dir / "repair_execution_rows.csv")
    failures = _read_csv(output_dir / "repair_execution_failure_rows.csv")
    target_rows = _read_csv(output_dir / "repair_target_context_rows.csv")
    coverage_rows = _read_csv(output_dir / "coverage_constraint_audit_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")

    assert len(candidates) == 3
    assert len(resolutions) == 3
    assert len(executions) == 3
    assert len(failures) == 0
    assert len(target_rows) == 3
    assert len(coverage_rows) == 3
    assert {row["repair_candidate_checkpoint_path"] for row in candidates} == {str(checkpoint)}
    assert {row["resolution_status"] for row in resolutions} == {"resolved_to_m1690_workload"}
    assert {row["ranking_run"] for row in executions} == {"False"}
    assert {row["repair_success_claim_made"] for row in executions} == {"False"}
    assert {row["m2931_audit_status_pass"] for row in coverage_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    blocked_claims = [row for row in claim_rows if row["allowed_in_m2931"] == "False"]
    assert blocked_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
