from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.paper_route_history_vs_current_response_bounded_comparison_execution_preflight import (
    EXPECTED_EPISODE_COUNT,
    EXPECTED_SPEC_COUNT,
    build_runtime_enforcement_join_rows,
    read_csv_rows,
    run_bounded_comparison_execution_preflight,
)
from autodrift.paper_route_history_vs_current_response_comparison_protocol_materialization import (
    REQUIRED_CONTROLLER_IDS,
)


RUNTIME_ENFORCEMENT_DIR = Path(
    "runs/m2673_paper_route_history_vs_current_response_runtime_enforcement_materialization"
)
M1674_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")


def _synthetic_episode_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for profile_name in EXPECTED_PROFILE_NAMES:
        for spec_index in range(EXPECTED_SPEC_COUNT):
            rows.append(
                {
                    "profile_name": profile_name,
                    "task_source_id": f"m1686-spec-{spec_index:04d}",
                }
            )
    return rows


def test_m2675_runtime_join_preserves_route_b_controls() -> None:
    runtime_rows = read_csv_rows(RUNTIME_ENFORCEMENT_DIR / "protocol_to_runtime_profile_rows.csv")

    join_rows = build_runtime_enforcement_join_rows(
        runtime_rows=runtime_rows,
        episode_rows=_synthetic_episode_rows(),
    )

    assert len(join_rows) == len(EXPECTED_PROFILE_NAMES)
    assert {row["protocol_controller_family_id"] for row in join_rows} == REQUIRED_CONTROLLER_IDS
    assert {row["runtime_join_status_pass"] for row in join_rows} == {True}
    assert {row["bounded_policy_rollout_run"] for row in join_rows} == {True}
    assert {row["policy_rollout_allowed"] for row in join_rows} == {True}
    assert {row["success_rate_metric_recorded"] for row in join_rows} == {True}
    assert {row["success_rate_verdict_claim_made"] for row in join_rows} == {False}

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


def test_m2675_bounded_execution_preflight_writes_expected_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "m2675"
    doc_path = tmp_path / "m2675.md"
    follow_up_manifest = tmp_path / "m2676.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = run_bounded_comparison_execution_preflight(
        runtime_enforcement_dir=RUNTIME_ENFORCEMENT_DIR,
        m1674_run_dir=M1674_RUN_DIR,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        eval_seed_base=267500,
        device="cpu",
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "paper_route_history_vs_current_response_bounded_comparison_execution_preflight_pass"
    )
    assert summary["episode_count"] == EXPECTED_EPISODE_COUNT
    assert summary["profile_count"] == len(EXPECTED_PROFILE_NAMES)
    assert summary["spec_count"] == EXPECTED_SPEC_COUNT
    assert summary["profile_aggregate_rows"] == len(EXPECTED_PROFILE_NAMES)
    assert summary["spec_aggregate_rows"] == EXPECTED_SPEC_COUNT
    assert summary["all_selected_metrics_finite"] is True
    assert summary["runtime_enforcement_join_row_count"] == len(EXPECTED_PROFILE_NAMES)
    assert summary["runtime_join_rows_pass"] is True
    assert summary["required_protocol_ids_runtime_mapped"] is True
    assert summary["current_tiled_runtime_profile_count"] == 4
    assert summary["current_tiled_runtime_observed"] is True
    assert summary["reset_truncated_runtime_profile_count"] == 1
    assert summary["reset_truncated_policy_routing_ok"] is True
    assert summary["environment_rollout_run"] is True
    assert summary["bounded_policy_rollout_run"] is True
    assert summary["policy_rollout_allowed"] is True
    assert summary["training_run"] is False
    assert summary["replay_run"] is False
    assert summary["ppo_run"] is False
    assert summary["private_holdout_used"] is False
    assert summary["profile_specific_tuning"] is False
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["winner_selected"] is False
    assert summary["promoted"] is False
    assert summary["success_rate_metric_recorded"] is True
    assert summary["success_rate_verdict_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["finite_window_vs_gru_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False
    assert summary["level3_self_id_claim_made"] is False

    for path in summary["paths"].values():
        assert Path(path).exists()
    assert read_json(output_dir / "summary.json") == summary
    assert read_json(output_dir / "measured_routing_smoke_summary.json")["episode_count"] == EXPECTED_EPISODE_COUNT
    assert doc_path.read_text(encoding="utf-8").strip()

    runtime_join_rows = read_csv_rows(output_dir / "runtime_enforcement_join_rows.csv")
    claim_rows = read_csv_rows(output_dir / "claim_boundary_rows.csv")
    gate_rows = read_csv_rows(output_dir / "gate_matrix.csv")
    profile_aggregate = read_csv_rows(output_dir / "profile_aggregate.csv")

    assert {row["runtime_join_status_pass"] for row in runtime_join_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["allowed_in_m2675"] for row in claim_rows if row["claim_id"] == "success_rate_verdict"} == {
        "False"
    }
    assert {row["claim_made"] for row in claim_rows if row["claim_id"] == "success_rate_verdict"} == {
        "False"
    }
    assert {row["allowed_in_m2675"] for row in claim_rows if row["claim_id"] == "paper_level_evidence"} == {
        "False"
    }
    assert all(row["success_rate"] != "" for row in profile_aggregate)
