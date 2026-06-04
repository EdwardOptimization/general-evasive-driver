from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight as m2716


def _write_m2714_source(root: Path, *, candidate_count: int = 4, protected_count: int = 2) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "exact_executable_candidate_row_count": candidate_count,
            "m2710_protected_proposal_exclusion_row_count": protected_count,
            "gate_matrix_pass": True,
        },
    )
    candidates = []
    profiles = ["L0_current_masked", "L3_online_gru"]
    for index in range(1, candidate_count + 1):
        profile = profiles[(index - 1) % len(profiles)]
        anchor = f"m1680-spec-{((index - 1) // 2) + 1:04d}"
        candidates.append(
            {
                "candidate_id": f"m2714-exact-executable-candidate-{index:04d}",
                "anchor_task_source_id": anchor,
                "anchor_workload_id": f"{anchor}::L3_online_gru",
                "workload_id": f"{anchor}::{profile}",
                "task_source_id": anchor,
                "profile_name": profile,
                "profile_role": "test_role",
                "task_family": "T4",
                "source_edge": f"edge-{index}",
                "window_tag": "reveal_plus_4",
                "executable_source_family": "capability_step_up",
                "env_template_family": "t4_capability_step_temporal",
                "strata": "test",
                "profile_config_path": "config.json",
                "checkpoint_path": "checkpoint.pt",
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
                "exact_executable_reentry_status": m2716.ADMITTED_EXISTING_STATUS,
                "existing_m1690_workload_id_source_backed": True,
                "execution_candidate": True,
                "execution_run": False,
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "target_labels_actor_visible": False,
                "protected_labels_actor_visible": False,
                "protected_rows_in_success_denominator": False,
            }
        )
    write_csv_rows(root / "exact_executable_candidate_rows.csv", candidates)
    write_csv_rows(
        root / "profile_context_rows.csv",
        [
            {
                "profile_context_id": f"profile-context-{index:04d}",
                "candidate_id": row["candidate_id"],
                "profile_name": row["profile_name"],
                "comparison_or_ranking_claim_allowed": False,
            }
            for index, row in enumerate(candidates, start=1)
        ],
    )
    write_csv_rows(
        root / "protected_proposal_exclusion_rows.csv",
        [
            {
                "exclusion_id": f"m2714-protected-proposal-exclusion-{index:04d}",
                "workload_fixture_proposal_id": f"proposal-{index:04d}",
                "support_candidate_id": f"support-{index:04d}",
                "proposed_workload_id": f"protected-{index:04d}::L3_online_gru",
                "profile_name": "L3_online_gru",
                "workload_fixture_support_status": "workload_fixture_support_proposed_new_current_m1690_row",
                "exact_match_status": "proposed_new_current_m1690_workload_row_not_existing_match",
                "blocker_type": "workload_fixture_support_blocker_existing_m1690_match_absent",
                "exclusion_status": m2716.PROTECTED_EXCLUSION_STATUS,
                "execution_admitted": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible": False,
                "protected_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
            }
            for index in range(1, protected_count + 1)
        ],
    )
    write_csv_rows(root / "actor_contract_guard_rows.csv", [{"guard_id": "obs", "status_pass": True}])
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])


def test_m2716_wrapper_accepts_bounded_execution_artifacts_without_overclaim(monkeypatch, tmp_path: Path) -> None:
    m2714_dir = tmp_path / "m2714"
    output_dir = tmp_path / "m2716"
    doc_path = tmp_path / "m2716.md"
    m2715_audit = tmp_path / "m2715.md"
    specs = tmp_path / "specs.json"
    follow_up = tmp_path / "m2717.json"
    _write_m2714_source(m2714_dir)
    m2715_audit.write_text(
        "accept_m2714_route_to_current_m1690_exact_executable_reentry_bounded_execution_preflight\n",
        encoding="utf-8",
    )
    write_json(specs, {"executable_task_specs": []})
    write_json(follow_up, {"id": "m2717"})

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        candidates = m2716.read_csv_rows(Path(kwargs["m2714_dir"]) / "exact_executable_candidate_rows.csv")
        episode_rows = []
        for index, candidate in enumerate(candidates):
            episode_rows.append(
                {
                    **candidate,
                    "seed": 271600 + index,
                    "steps": 80,
                    "collision": False,
                    "success": index % 2 == 0,
                    "termination_reason": "" if index % 2 == 0 else "off_track",
                    "min_clearance_margin": 0.2,
                    "return": 1.0,
                    "action_rate_mean": 0.1,
                    "high_sideslip_fraction": 0.0,
                    "m2716_eval_seed": 271600 + index,
                    "bounded_exact_executable_reentry_execution": True,
                    "protected_proposal_execution": False,
                    "protected_rows_in_success_denominator": False,
                    "hidden_oracle_actor_input_required": False,
                    "target_labels_actor_visible": False,
                    "protected_labels_actor_visible": False,
                    "profile_labels_actor_visible": False,
                    "blocker_labels_actor_visible": False,
                    "route_labels_actor_visible": False,
                    "verdict_labels_actor_visible": False,
                    "training_started": False,
                    "replay_started": False,
                    "ppo_used": False,
                    "private_holdout_used": False,
                    "profile_specific_tuning": False,
                    "ranking_run": False,
                    "success_rate_verdict_claim_made": False,
                    "driver_performance_claim_made": False,
                    "paper_claim_made": False,
                    "current_sim_verdict_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
        write_csv_rows(output / "exact_execution_rows.csv", episode_rows)
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=m2716.FAILURE_FIELDNAMES)
        return m2716.finalize_candidate_panel_outputs(
            output_dir=output,
            candidate_rows=candidates,
            next_blocker="m2717",
        )

    monkeypatch.setattr(m2716, "run_candidate_panel_execution", fake_execution)
    monkeypatch.setattr(m2716, "EXPECTED_CANDIDATE_COUNT", 4)
    monkeypatch.setattr(m2716, "EXPECTED_PROTECTED_EXCLUSION_COUNT", 2)

    summary = m2716.run_current_m1690_exact_executable_reentry_bounded_execution_preflight(
        m2714_dir=m2714_dir,
        m2715_audit=m2715_audit,
        executable_specs=specs,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["candidate_count"] == 4
    assert summary["exact_execution_row_count"] == 4
    assert summary["failure_row_count"] == 0
    assert summary["profile_aggregate_row_count"] == 2
    assert summary["anchor_aggregate_row_count"] == 2
    assert summary["protected_proposal_exclusion_audit_row_count"] == 2
    assert summary["protected_execution_row_count"] == 0
    assert summary["protected_proposal_execution"] is False
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["actor_contract_join_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary
    assert doc_path.read_text(encoding="utf-8").strip()

    protected_rows = m2716.read_csv_rows(output_dir / "protected_proposal_exclusion_audit_rows.csv")
    assert {row["m2716_execution_run"] for row in protected_rows} == {"False"}
    assert {row["m2716_execution_admitted"] for row in protected_rows} == {"False"}
    claim_rows = m2716.read_csv_rows(output_dir / "claim_boundary_rows.csv")
    assert {row["claim_made"] for row in claim_rows if row["claim_family"] == "driver_performance"} == {"False"}
    gate_rows = m2716.read_csv_rows(output_dir / "gate_matrix.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
