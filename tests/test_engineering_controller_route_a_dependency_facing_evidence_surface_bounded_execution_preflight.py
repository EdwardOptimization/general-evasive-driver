from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight as m2919


def _candidate_row(
    *,
    candidate_id: str = "m2916-execution-admission-candidate-0001",
    source_milestone: str = "m2737",
    status: str = m2919.ADMITTED_STATUS,
    checkpoint_path: str = "checkpoint.pt",
    profile_config_path: str = "config.json",
) -> dict[str, str]:
    return {
        "execution_admission_candidate_id": candidate_id,
        "source_milestone": source_milestone,
        "source_artifact": "source.csv",
        "source_row_id": "source-row-1",
        "source_family": "source_diverse_current_sim_offtrack",
        "task_family": "T4",
        "workload_id": "task-1::L3_online_gru",
        "task_source_id": "task-1",
        "profile_name": "L3_online_gru",
        "checkpoint_path": checkpoint_path,
        "profile_config_path": profile_config_path,
        "candidate_family_id": "candidate-family-001-C1",
        "candidate_family_name": "route_a_source_diverse_closed_loop_diagnostics",
        "execution_admission_status": status,
        "execution_rejection_status": "",
        "required_follow_up": "separate bounded execution manifest",
        "environment_reset_admitted": "False",
        "environment_rollout_scheduled": "False",
        "measured_validation_scheduled": "False",
        "training_scheduled": "False",
        "dependency_execution_scheduled": "False",
        "profile_specific_tuning": "False",
        "actor_observation_dim": "72",
        "actor_action_dim": "3",
        "actor_input_contract_changed": "False",
        "hidden_oracle_actor_input_required": "False",
        "future_target_actor_input_required": "False",
        "route_labels_actor_visible": "False",
        "source_labels_actor_visible": "False",
        "diagnostic_labels_actor_visible": "False",
        "success_progress_labels_actor_visible": "False",
        "verdict_labels_actor_visible": "False",
        "ordinary_engineering_denominator_allowed_after_audit": "True",
        "validation_denominator_allowed": "False",
        "paper_denominator_allowed": "False",
        "high_fidelity_readiness_allowed": "False",
        "self_id_claim_allowed": "False",
        "diagnostic_only_no_verdict": "True",
        "materialization_only_no_execution": "True",
        "claim_boundary": "m2916 boundary",
    }


def _workload_row() -> dict[str, str]:
    return {
        "workload_id": "task-1::L3_online_gru",
        "task_source_id": "task-1",
        "profile_name": "L3_online_gru",
        "task_family": "T4",
        "source_edge": "capability_step_up",
        "window_tag": "reveal_plus_4",
        "executable_source_family": "capability_step_up",
        "env_template_family": "t4_capability_step_temporal",
        "strata": "task_family_T4",
        "profile_config_path": "old-config.json",
        "checkpoint_path": "old-checkpoint.pt",
        "config_exists": "True",
        "checkpoint_exists": "True",
        "environment_rollout_scheduled": "False",
        "training_scheduled": "False",
        "profile_specific_tuning": "False",
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_candidate_resolution_excludes_m2877_and_uses_candidate_checkpoint(tmp_path: Path) -> None:
    checkpoint = tmp_path / "candidate.pt"
    config = tmp_path / "candidate.json"
    checkpoint.write_text("checkpoint", encoding="utf-8")
    write_json(config, {"env": {}})
    admitted = _candidate_row(checkpoint_path=str(checkpoint), profile_config_path=str(config))
    guard = _candidate_row(
        candidate_id="m2916-execution-admission-candidate-0067",
        source_milestone="m2877",
        status=m2919.BLOCKED_STALE_STATUS,
        checkpoint_path=str(checkpoint),
        profile_config_path=str(config),
    )

    candidate_rows = m2919.build_execution_candidate_rows([admitted, guard])
    assert [row["execution_admission_candidate_id"] for row in candidate_rows] == [
        "m2916-execution-admission-candidate-0001"
    ]
    source = {"executable_workload_rows": [_workload_row()]}
    resolution_rows, resolved = m2919.build_resolution_rows(source, candidate_rows)

    assert len(resolution_rows) == 1
    assert resolution_rows[0]["resolution_status"] == "resolved_to_m1690_workload"
    assert resolution_rows[0]["execution_admitted"] is True
    assert resolved["m2919-resolution-0001"]["checkpoint_path"] == str(checkpoint)
    assert resolved["m2919-resolution-0001"]["profile_config_path"] == str(config)
    assert resolved["m2919-resolution-0001"]["source_edge"] == "capability_step_up"


def test_run_preflight_mock_execution_writes_gates_and_follow_up(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2919, "EXPECTED_TOTAL_CANDIDATE_COUNT", 1)
    monkeypatch.setattr(m2919, "EXPECTED_ADMITTED_COUNT", 1)
    monkeypatch.setattr(m2919, "EXPECTED_M2877_GUARD_COUNT", 0)
    monkeypatch.setattr(m2919, "EXPECTED_SOURCE_MILESTONE_COUNTS", {"m2737": 1})

    checkpoint = tmp_path / "candidate.pt"
    config = tmp_path / "candidate.json"
    checkpoint.write_text("checkpoint", encoding="utf-8")
    write_json(config, {"env": {}})

    m2916_dir = tmp_path / "m2916"
    write_json(m2916_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(
        m2916_dir / "execution_admission_candidate_rows.csv",
        [_candidate_row(checkpoint_path=str(checkpoint), profile_config_path=str(config))],
    )
    write_csv_rows(
        m2916_dir / "execution_admission_rejection_rows.csv",
        [],
        fieldnames=[
            "rejection_id",
            "candidate_or_source_id",
            "source_milestone",
            "rejection_type",
            "rejection_reason",
            "required_follow_up",
            "actor_visible",
            "claim_scope",
        ],
    )
    write_csv_rows(
        m2916_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_id": "g1",
                "guardrail_source": "m2913_denominator_policy_rows",
                "guardrail_family": "route_b_context_only",
                "source_row_id": "route-b",
                "guardrail_reason": "context only",
                "execution_allowed": "False",
                "ordinary_engineering_denominator_allowed": "False",
                "validation_denominator_allowed": "False",
                "paper_denominator_allowed": "False",
                "high_fidelity_readiness_allowed": "False",
                "self_id_claim_allowed": "False",
                "actor_visible": "False",
                "claim_scope": "boundary",
            },
            {
                "guardrail_id": "g2",
                "guardrail_source": "m2913_denominator_policy_rows",
                "guardrail_family": "route_c_dependency_context_only",
                "source_row_id": "route-c",
                "guardrail_reason": "context only",
                "execution_allowed": "False",
                "ordinary_engineering_denominator_allowed": "False",
                "validation_denominator_allowed": "False",
                "paper_denominator_allowed": "False",
                "high_fidelity_readiness_allowed": "False",
                "self_id_claim_allowed": "False",
                "actor_visible": "False",
                "claim_scope": "boundary",
            },
        ],
    )
    for name in ["actor_contract_guard_rows.csv", "claim_boundary_rows.csv", "gate_matrix.csv"]:
        write_csv_rows(m2916_dir / name, [{"id": "placeholder"}])

    m2917_audit = tmp_path / "m2917.md"
    m2918_design = tmp_path / "m2918.md"
    m2917_audit.write_text("M2917 audit accepts M2916 complete claim-safe surface", encoding="utf-8")
    m2918_design.write_text(m2919.MILESTONE_ID, encoding="utf-8")

    workload = tmp_path / "workload.csv"
    write_csv_rows(workload, [_workload_row()])
    specs = tmp_path / "specs.json"
    write_json(specs, {"executable_task_specs": [{"task_source_id": "task-1", "env_config": {}}]})

    class FakeModel:
        obs_dim = 72

    monkeypatch.setattr(m2919, "load_actor_critic_checkpoint", lambda *args, **kwargs: (FakeModel(), {}))
    monkeypatch.setattr(
        m2919,
        "run_workload_cell",
        lambda **kwargs: {
            "seed": kwargs["eval_seed"],
            "policy": "checkpoint",
            "steps": 12,
            "terminated": True,
            "truncated": False,
            "collision": False,
            "obstacle_completed": True,
            "min_clearance_margin": 1.25,
            "termination_reason": "completed",
            "return": 3.5,
            "action_rate_mean": 0.2,
            "high_sideslip_fraction": 0.0,
            "success": True,
            "workload_id": "task-1::L3_online_gru",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "task_family": "T4",
            "source_edge": "capability_step_up",
            "window_tag": "reveal_plus_4",
            "strata": "task_family_T4",
            "executable_source_family": "capability_step_up",
            "env_template_family": "t4_capability_step_temporal",
            "profile_config_path": str(config),
            "checkpoint_path": str(checkpoint),
            "profile_env_history_length": 4,
        },
    )

    output_dir = tmp_path / "out"
    doc_path = tmp_path / "doc.md"
    follow_up = tmp_path / "m2920.json"
    summary = m2919.run_dependency_facing_bounded_execution_preflight(
        m2916_dir=m2916_dir,
        m2917_audit=m2917_audit,
        m2918_design=m2918_design,
        executable_specs=specs,
        executable_workload=workload,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        eval_seed_base=291900,
        device="cpu",
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["bounded_execution_row_count"] == 1
    assert summary["bounded_execution_failure_row_count"] == 0
    assert summary["gate_matrix_pass"] is True
    assert follow_up.exists()
    assert read_json(follow_up)["id"] == m2919.NEXT_ID
    assert doc_path.exists()
    assert _read_csv(output_dir / "source_milestone_aggregate.csv")[0]["aggregate_value"] == "m2737"
