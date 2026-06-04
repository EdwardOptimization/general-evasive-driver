from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.paper_route_history_vs_current_response_comparison_protocol_materialization import (
    REQUIRED_CONTROLLER_IDS,
)
from autodrift import paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight as m2677


RUNTIME_ENFORCEMENT_DIR = Path(
    "runs/m2673_paper_route_history_vs_current_response_runtime_enforcement_materialization"
)
BOUNDED_PREFLIGHT_DIR = Path(
    "runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight"
)
EXECUTABLE_SPECS = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json"
)
EXECUTABLE_WORKLOAD = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv"
)
M1674_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")


def _synthetic_episode_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for profile_name in EXPECTED_PROFILE_NAMES:
        for spec_index in range(m2677.TARGET_SPEC_COUNT):
            rows.append(
                {
                    "workload_id": f"{profile_name}-{spec_index:04d}",
                    "profile_name": profile_name,
                    "task_source_id": f"m1690-spec-{spec_index:04d}",
                }
            )
    return rows


def test_m2677_runtime_join_preserves_route_b_full_rollout_controls() -> None:
    runtime_rows = m2677.read_csv_rows(RUNTIME_ENFORCEMENT_DIR / "protocol_to_runtime_profile_rows.csv")

    join_rows = m2677.build_runtime_enforcement_join_rows(
        runtime_rows=runtime_rows,
        episode_rows=_synthetic_episode_rows(),
        failure_rows=[],
    )

    assert len(join_rows) == len(EXPECTED_PROFILE_NAMES)
    assert {row["protocol_controller_family_id"] for row in join_rows} == REQUIRED_CONTROLLER_IDS
    assert {row["runtime_join_status_pass"] for row in join_rows} == {True}
    assert {row["full_public_policy_rollout_run"] for row in join_rows} == {True}
    assert {row["policy_rollout_allowed"] for row in join_rows} == {True}
    assert {row["success_rate_metric_recorded"] for row in join_rows} == {True}
    assert {row["comparison_delta_metric_recorded"] for row in join_rows} == {True}
    assert {row["success_rate_verdict_claim_made"] for row in join_rows} == {False}
    assert {row["controller_family_ranking_claim_made"] for row in join_rows} == {False}
    assert {row["executed_spec_count"] for row in join_rows} == {m2677.TARGET_SPEC_COUNT}
    assert {row["failed_cell_count"] for row in join_rows} == {0}

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


def test_m2677_wrapper_writes_full_execution_boundaries(monkeypatch, tmp_path: Path) -> None:
    output_dir = tmp_path / "m2677"
    doc_path = tmp_path / "m2677.md"
    follow_up_manifest = tmp_path / "m2678.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    def fake_full_rollout_execution(*, output_dir: Path, next_blocker: str, **_: object) -> dict[str, object]:
        episode_rows = _fake_episode_rows()
        profile_rows = _fake_profile_aggregate_rows()
        spec_rows = _fake_spec_aggregate_rows()
        stratum_rows = [{"stratum": "all_72_specs", "episode_count": m2677.TARGET_EPISODE_COUNT}]
        comparison_rows = [
            {
                "comparison": f"diagnostic-comparison-{index:02d}",
                "success_rate_delta": 0.0,
                "diagnostic_only_no_ranking_claim": True,
            }
            for index in range(11)
        ]
        write_csv_rows(output_dir / "episode_rows.csv", episode_rows)
        write_csv_rows(output_dir / "profile_aggregate.csv", profile_rows)
        write_csv_rows(output_dir / "spec_aggregate.csv", spec_rows)
        write_csv_rows(output_dir / "stratum_aggregate.csv", stratum_rows)
        write_csv_rows(output_dir / "comparison_aggregate.csv", comparison_rows)
        write_csv_rows(output_dir / "outcome_aggregate.csv", [{"outcome_bucket": "success", "episode_count": 1}])
        write_csv_rows(
            output_dir / "termination_reason_aggregate.csv",
            [{"termination_reason": "completed", "episode_count": 1}],
        )
        write_csv_rows(
            output_dir / "profile_outcome_aggregate.csv",
            [{"profile_outcome": "L0_current_masked::success", "episode_count": 1}],
        )
        write_csv_rows(
            output_dir / "hidden_dynamics_aggregate.csv",
            [{"hidden_dynamics_bucket": "nominal", "diagnostic_only_no_ranking_claim": True}],
        )
        write_csv_rows(
            output_dir / "profile_hidden_dynamics_worst_bucket.csv",
            [{"profile_name": "L0_current_masked", "worst_hidden_dynamics_bucket": "nominal"}],
        )
        write_csv_rows(output_dir / "failure_rows.csv", [], fieldnames=["workload_id", "profile_name"])
        write_json(output_dir / "run_state.json", {"complete": True, "completed_count": m2677.TARGET_EPISODE_COUNT})
        summary = {
            "result_class": "controller_family_full_rollout_execution_pass",
            "episode_count": m2677.TARGET_EPISODE_COUNT,
            "target_episode_count": m2677.TARGET_EPISODE_COUNT,
            "profile_count": m2677.TARGET_PROFILE_COUNT,
            "target_profile_count": m2677.TARGET_PROFILE_COUNT,
            "spec_count": m2677.TARGET_SPEC_COUNT,
            "target_spec_count": m2677.TARGET_SPEC_COUNT,
            "failure_count": 0,
            "all_selected_metrics_finite": True,
            "profile_aggregate_rows": m2677.TARGET_PROFILE_COUNT,
            "spec_aggregate_rows": m2677.TARGET_SPEC_COUNT,
            "stratum_aggregate_rows": 1,
            "comparison_aggregate_rows": len(comparison_rows),
            "outcome_aggregate_rows": 1,
            "termination_reason_aggregate_rows": 1,
            "profile_outcome_aggregate_rows": 1,
            "hidden_dynamics_aggregate_rows": 1,
            "profile_hidden_dynamics_worst_bucket_rows": 1,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
            "private_holdout_used": False,
            "actor_input_contract_changed": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
            "next_blocker": next_blocker,
            "artifacts": {
                "summary": str(output_dir / "summary.json"),
                "episode_rows": str(output_dir / "episode_rows.csv"),
            },
        }
        write_json(output_dir / "summary.json", summary)
        return summary

    monkeypatch.setattr(m2677, "run_full_rollout_execution", fake_full_rollout_execution)

    summary = m2677.run_full_t4_t5_public_comparison_execution_preflight(
        runtime_enforcement_dir=RUNTIME_ENFORCEMENT_DIR,
        bounded_preflight_dir=BOUNDED_PREFLIGHT_DIR,
        executable_specs=EXECUTABLE_SPECS,
        workload=EXECUTABLE_WORKLOAD,
        m1674_run_dir=M1674_RUN_DIR,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        eval_seed_base=267700,
        device="cpu",
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight_pass"
    )
    assert summary["episode_count"] == m2677.TARGET_EPISODE_COUNT
    assert summary["failure_count"] == 0
    assert summary["runtime_join_rows_pass"] is True
    assert summary["current_tiled_runtime_profile_count"] == 4
    assert summary["current_tiled_runtime_observed"] is True
    assert summary["reset_truncated_runtime_profile_count"] == 1
    assert summary["reset_truncated_policy_routing_ok"] is True
    assert summary["allowed_claim_boundary_row_count"] == 17
    assert summary["blocked_claim_boundary_row_count"] == 19
    assert summary["success_rate_metric_recorded"] is True
    assert summary["comparison_delta_metric_recorded"] is True
    assert summary["success_rate_verdict_claim_made"] is False
    assert summary["comparison_delta_verdict_claim_made"] is False
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["required_artifacts_present"] is True

    for path in summary["paths"].values():
        assert Path(path).exists()
    assert read_json(output_dir / "summary.json") == summary
    assert read_json(output_dir / "full_rollout_execution_summary.json")["episode_count"] == 864
    assert doc_path.read_text(encoding="utf-8").strip()

    claim_rows = m2677.read_csv_rows(output_dir / "claim_boundary_rows.csv")
    gate_rows = m2677.read_csv_rows(output_dir / "gate_matrix.csv")
    comparison_rows = m2677.read_csv_rows(output_dir / "comparison_aggregate.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["allowed_in_m2677"] for row in claim_rows if row["claim_id"] == "success_rate_verdict"} == {
        "False"
    }
    assert {
        row["allowed_in_m2677"] for row in claim_rows if row["claim_id"] == "comparison_delta_verdict"
    } == {"False"}
    assert {row["claim_made"] for row in claim_rows if row["claim_id"] == "controller_family_ranking"} == {
        "False"
    }
    assert {row["diagnostic_only_no_ranking_claim"] for row in comparison_rows} == {"True"}


def _fake_episode_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for profile_index, profile_name in enumerate(EXPECTED_PROFILE_NAMES):
        for spec_index in range(m2677.TARGET_SPEC_COUNT):
            rows.append(
                {
                    "workload_id": f"{profile_name}-{spec_index:04d}",
                    "profile_name": profile_name,
                    "task_source_id": f"m1690-spec-{spec_index:04d}",
                    "task_family": "T4" if spec_index % 2 == 0 else "T5",
                    "source_edge": "public",
                    "window_tag": "full",
                    "strata": "all_72_specs",
                    "executable_source_family": "synthetic_public",
                    "outcome_bucket": "success" if spec_index % 3 else "noncollision_noncompletion",
                    "termination_reason": "completed" if spec_index % 3 else "timeout",
                    "hidden_dynamics_bucket": "nominal",
                    "success": spec_index % 3 != 0,
                    "collision": False,
                    "min_clearance_margin": 0.1 + (profile_index * 0.001),
                    "return": float(spec_index),
                    "steps": 120,
                    "action_rate_mean": 0.2,
                    "high_sideslip_fraction": 0.0,
                    "full_rollout_execution": True,
                    "routing_smoke_only": False,
                    "training_started": False,
                    "replay_started": False,
                    "ppo_used": False,
                    "private_holdout_used": False,
                    "actor_input_contract_changed": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    return rows


def _fake_profile_aggregate_rows() -> list[dict[str, object]]:
    return [
        {
            "profile_name": profile_name,
            "episode_count": m2677.TARGET_SPEC_COUNT,
            "success_rate": 0.5,
            "collision_rate": 0.0,
            "clearance_margin_mean": 0.1,
            "return_mean": 1.0,
            "all_selected_metrics_finite": True,
        }
        for profile_name in EXPECTED_PROFILE_NAMES
    ]


def _fake_spec_aggregate_rows() -> list[dict[str, object]]:
    return [
        {
            "task_source_id": f"m1690-spec-{spec_index:04d}",
            "episode_count": m2677.TARGET_PROFILE_COUNT,
            "success_rate": 0.5,
            "collision_rate": 0.0,
            "task_family": "T4" if spec_index % 2 == 0 else "T5",
            "source_family": "synthetic_public",
            "all_selected_metrics_finite": True,
        }
        for spec_index in range(m2677.TARGET_SPEC_COUNT)
    ]
