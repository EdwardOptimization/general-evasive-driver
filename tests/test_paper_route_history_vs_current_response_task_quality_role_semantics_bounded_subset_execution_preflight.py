from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.paper_route_history_vs_current_response_comparison_protocol_materialization import (
    REQUIRED_CONTROLLER_IDS,
)
from autodrift import (
    paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight as m2684,
)


M2682_DIR = Path(
    "runs/m2682_paper_route_history_vs_current_response_task_quality_role_semantics_repair_materialization"
)
RUNTIME_ENFORCEMENT_DIR = Path(
    "runs/m2673_paper_route_history_vs_current_response_runtime_enforcement_materialization"
)
EXECUTABLE_SPECS = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json"
)
EXECUTABLE_WORKLOAD = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv"
)
M1674_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")


def test_m2684_subset_validation_keeps_m2682_bounds() -> None:
    subset_rows = m2684.load_subset_rows(M2682_DIR)

    validation = m2684.validate_subset_rows(subset_rows)

    assert validation["subset_row_count"] == 216
    assert validation["unique_workload_count"] == 216
    assert validation["unique_task_source_count"] == 18
    assert validation["unique_profile_count"] == len(EXPECTED_PROFILE_NAMES)
    assert validation["candidate_count"] == 9
    assert validation["is_full_public_matrix"] is False
    assert validation["role_semantics_actor_visible"] is False
    assert validation["hidden_oracle_actor_input_required"] is False
    assert validation["actor_input_contract_changed"] is False
    assert validation["diagnostic_only_no_verdict"] is True
    assert validation["not_selected_from_success_only"] is True


def test_m2684_runtime_join_preserves_route_b_controls() -> None:
    subset_rows = m2684.load_subset_rows(M2682_DIR)
    runtime_rows = m2684.read_csv_rows(RUNTIME_ENFORCEMENT_DIR / "protocol_to_runtime_profile_rows.csv")

    join_rows = m2684.build_runtime_enforcement_join_rows(
        runtime_rows=runtime_rows,
        subset_rows=subset_rows,
        episode_rows=_fake_episode_rows(subset_rows),
        failure_rows=[],
    )

    assert len(join_rows) == len(EXPECTED_PROFILE_NAMES)
    assert {row["protocol_controller_family_id"] for row in join_rows} == REQUIRED_CONTROLLER_IDS
    assert {row["runtime_join_status_pass"] for row in join_rows} == {True}
    assert {row["target_subset_cell_count"] for row in join_rows} == {18}
    assert {row["executed_episode_count"] for row in join_rows} == {18}
    assert {row["failed_cell_count"] for row in join_rows} == {0}
    assert {row["bounded_subset_policy_rollout_run"] for row in join_rows} == {True}
    assert {row["role_semantics_actor_visible"] for row in join_rows} == {False}
    assert {row["success_rate_verdict_claim_made"] for row in join_rows} == {False}
    assert {row["controller_family_ranking_claim_made"] for row in join_rows} == {False}

    current_tiled_rows = [
        row for row in join_rows if row["protocol_controller_family_id"] == "L2-current-tiled"
    ]
    assert len(current_tiled_rows) == 4
    assert {row["current_tiled_runtime_observed"] for row in current_tiled_rows} == {True}

    reset_rows = [
        row
        for row in join_rows
        if row["protocol_controller_family_id"] == "L3-reset-truncated-control"
    ]
    assert len(reset_rows) == 1
    assert reset_rows[0]["reset_hidden_policy"] == "every_step_control"
    assert reset_rows[0]["reset_policy_routing_ok"] is True


def test_m2684_wrapper_writes_subset_execution_boundaries(monkeypatch, tmp_path: Path) -> None:
    output_dir = tmp_path / "m2684"
    doc_path = tmp_path / "m2684.md"
    follow_up_manifest = tmp_path / "m2685.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    def fake_subset_rollout_execution(*, m2682_dir: Path, output_dir: Path, next_blocker: str, **_: object) -> dict[str, object]:
        subset_rows = m2684.load_subset_rows(m2682_dir)
        write_csv_rows(output_dir / "episode_rows.csv", _fake_episode_rows(subset_rows))
        write_csv_rows(output_dir / "failure_rows.csv", [], fieldnames=m2684.FAILURE_FIELDNAMES)
        return m2684.finalize_subset_outputs(
            output_dir=output_dir,
            subset_rows=subset_rows,
            target_workload_count=len(subset_rows),
            next_blocker=next_blocker,
        )

    monkeypatch.setattr(m2684, "run_subset_rollout_execution", fake_subset_rollout_execution)

    summary = m2684.run_bounded_subset_execution_preflight(
        m2682_dir=M2682_DIR,
        runtime_enforcement_dir=RUNTIME_ENFORCEMENT_DIR,
        executable_specs=EXECUTABLE_SPECS,
        workload=EXECUTABLE_WORKLOAD,
        m1674_run_dir=M1674_RUN_DIR,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        eval_seed_base=268400,
        device="cpu",
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight_pass"
    )
    assert summary["episode_count"] == 216
    assert summary["target_episode_count"] == 216
    assert summary["spec_count"] == 18
    assert summary["candidate_count"] == 9
    assert summary["subset_is_full_public_matrix"] is False
    assert summary["failure_count"] == 0
    assert summary["runtime_join_rows_pass"] is True
    assert summary["current_tiled_runtime_profile_count"] == 4
    assert summary["reset_truncated_runtime_profile_count"] == 1
    assert summary["allowed_claim_boundary_row_count"] == 17
    assert summary["blocked_claim_boundary_row_count"] == 20
    assert summary["role_semantics_actor_visible"] is False
    assert summary["success_rate_metric_recorded"] is True
    assert summary["diagnostic_role_task_quality_metrics_recorded"] is True
    assert summary["success_rate_verdict_claim_made"] is False
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["required_artifacts_present"] is True

    for path in summary["paths"].values():
        assert Path(path).exists()
    assert read_json(output_dir / "summary.json") == summary
    assert read_json(output_dir / "subset_rollout_execution_summary.json")["episode_count"] == 216
    assert doc_path.read_text(encoding="utf-8").strip()

    claim_rows = m2684.read_csv_rows(output_dir / "claim_boundary_rows.csv")
    gate_rows = m2684.read_csv_rows(output_dir / "gate_matrix.csv")
    role_rows = m2684.read_csv_rows(output_dir / "role_semantics_aggregate.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["allowed_in_m2684"] for row in claim_rows if row["claim_id"] == "success_rate_verdict"} == {
        "False"
    }
    assert {
        row["allowed_in_m2684"] for row in claim_rows if row["claim_id"] == "actor_visible_role_semantics"
    } == {"False"}
    assert {row["claim_made"] for row in claim_rows if row["claim_id"] == "controller_family_ranking"} == {
        "False"
    }
    assert role_rows


def _fake_episode_rows(subset_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, subset in enumerate(subset_rows):
        success = index % 5 == 0
        rows.append(
            {
                **subset,
                "seed": 268400 + index,
                "policy": "checkpoint",
                "steps": 120,
                "terminated": True,
                "truncated": False,
                "collision": False,
                "obstacle_completed": success,
                "success": success,
                "min_clearance_margin": 0.1 + (index % 7) * 0.01,
                "termination_reason": "completed" if success else "off_track",
                "outcome_bucket": "success_obstacle_pass"
                if success
                else "off_track_noncollision_noncompletion",
                "return": float(index),
                "mean_reward": float(index) / 10.0,
                "lateral_rmse": 0.0,
                "action_rate_mean": 0.2,
                "high_sideslip_fraction": 0.0,
                "bounded_subset_execution": True,
                "routing_smoke_only": False,
                "full_rollout_execution": False,
                "private_holdout_used": False,
                "promoted": False,
                "training_started": False,
                "replay_started": False,
                "ppo_used": False,
                "actor_input_contract_changed": False,
                "profile_specific_tuning": False,
                "role_semantics_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "diagnostic_only_no_verdict": True,
                "controller_family_ranking_claim_made": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "comparison_delta_verdict_claim_made": False,
            }
        )
    return rows
