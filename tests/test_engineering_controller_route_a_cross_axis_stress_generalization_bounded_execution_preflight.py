from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight as m2753


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m1690 = root / "m1690.csv"
    workload_rows = []
    for task_source_id, task_family, source_edge, _axis in m2753.SELECTED_TASK_SOURCES:
        workload_rows.append(
            {
                "workload_id": f"{task_source_id}::L3_online_gru",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": task_family,
                "source_edge": source_edge,
                "window_tag": "window",
                "executable_source_family": "source_family",
                "env_template_family": "template",
                "strata": "strata",
                "profile_config_path": "config.json",
                "checkpoint_path": "checkpoint.pt",
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        )
    write_csv_rows(m1690, workload_rows)

    m2746_dir = root / "m2746"
    m2737_dir = root / "m2737"
    m2749_dir = root / "m2749"
    m2746_dir.mkdir()
    m2737_dir.mkdir()
    m2749_dir.mkdir()
    prior_task_sources = [
        "m1680-spec-0000",
        "m1680-spec-0002",
        "m1680-spec-0004",
        "m1680-spec-0005",
        "m1680-spec-0006",
        "m1680-spec-0036",
        "m1680-spec-0038",
        "m1680-spec-0040",
        "m1680-spec-0041",
    ]
    prior_rows = [
        {
            "task_source_id": task_source_id,
            "workload_id": f"{task_source_id}::L3_online_gru",
            "profile_name": "L3_online_gru",
            "termination_reason": "off_track",
        }
        for task_source_id in prior_task_sources
    ]
    write_csv_rows(m2746_dir / "execution_candidate_rows.csv", prior_rows[:8])
    write_csv_rows(m2746_dir / "candidate_execution_rows.csv", prior_rows[:8])
    write_csv_rows(m2737_dir / "candidate_execution_rows.csv", prior_rows)
    write_csv_rows(
        m2749_dir / "blocker_matrix.csv",
        [
            {
                "blocker_id": "m2749_blocker_protected_mitigation",
                "route": "Route A",
                "evidence_family": "known_failure_boundary",
                "current_status": "active",
                "blocking_count": 10,
            },
            {
                "blocker_id": "m2749_blocker_hf3_source_dependency_unavailable",
                "route": "Route C",
                "evidence_family": "hf3_dependency",
                "current_status": "paused_by_m2638",
                "blocking_count": 1,
            },
        ],
    )
    write_csv_rows(
        m2749_dir / "next_action_admission_rows.csv",
        [{"candidate_action_id": "route_a_non_same_panel_execution_surface", "admission_status": "admitted"}],
    )
    specs = root / "specs.json"
    write_json(specs, {"executable_task_specs": [{"task_source_id": row["task_source_id"], "env_config": {}} for row in workload_rows]})
    design = root / "m2752.md"
    design.write_text("M2752 design\n", encoding="utf-8")
    follow_up = root / "m2754.json"
    follow_up.write_text('{"id": "m2754"}\n', encoding="utf-8")
    return {
        "m1690": m1690,
        "m2746_dir": m2746_dir,
        "m2737_dir": m2737_dir,
        "m2749_dir": m2749_dir,
        "specs": specs,
        "design": design,
        "follow_up": follow_up,
    }


def test_m2753_selects_non_same_panel_cross_axis_surface_and_blocks_overclaims(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2753"
    doc_path = tmp_path / "m2753.md"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"]):
            rows.append(
                {
                    "seed": 275300 + index,
                    "policy": "checkpoint",
                    "steps": 80 + index,
                    "collision": index % 5 == 0,
                    "obstacle_completed": index % 4 == 0,
                    "success": index % 4 == 0 and index % 5 != 0,
                    "termination_reason": "obstacle_completed" if index % 4 == 0 and index % 5 != 0 else "off_track",
                    "min_clearance_margin": 0.2,
                    "return": 1.0,
                    "action_rate_mean": 0.1,
                    "high_sideslip_fraction": 0.0,
                    "task_family": resolution["task_family"],
                    "source_edge": resolution["source_edge"],
                    "candidate_id": resolution["candidate_id"],
                    "resolution_id": resolution["resolution_id"],
                    "stress_axis_primary": resolution["stress_axis_primary"],
                    "stress_axis_tags": resolution["stress_axis_tags"],
                    "m2753_eval_seed": 275300 + index,
                    "prior_panel_execution": False,
                    "protected_blocker_execution": False,
                    "hf3_blocker_execution": False,
                    "hidden_oracle_actor_input_required": False,
                    "stress_axis_labels_actor_visible": False,
                    "blocker_labels_actor_visible": False,
                    "route_labels_actor_visible": False,
                    "success_progress_labels_actor_visible": False,
                    "verdict_labels_actor_visible": False,
                    "protected_rows_in_success_denominator": False,
                    "training_started": False,
                    "replay_started": False,
                    "ppo_used": False,
                    "source_build_run": False,
                    "adapter_probe_run": False,
                    "external_simulation_run": False,
                    "profile_specific_tuning": False,
                    "active_config_overwritten": False,
                    "ranking_run": False,
                    "winner_selected": False,
                    "checkpoint_promoted": False,
                    "success_rate_verdict_claim_made": False,
                    "driver_performance_claim_made": False,
                    "validation_readiness_claim_made": False,
                    "paper_claim_made": False,
                    "current_sim_verdict_claim_made": False,
                    "high_fidelity_validation_claim_made": False,
                    "full_ideal_driver_gate_passed": False,
                    "level3_self_id_claim_made": False,
                }
            )
        write_csv_rows(output / "candidate_execution_rows.csv", rows)
        write_csv_rows(output / "candidate_execution_failure_rows.csv", [], fieldnames=m2753.FAILURE_FIELDNAMES)
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return {
            "result_class": "engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_pass",
            "all_selected_metrics_finite": True,
        }

    monkeypatch.setattr(m2753, "run_candidate_execution", fake_execution)
    summary = m2753.run_cross_axis_stress_generalization_bounded_execution_preflight(
        m1690_workload=paths["m1690"],
        m2746_dir=paths["m2746_dir"],
        m2737_dir=paths["m2737_dir"],
        m2749_dir=paths["m2749_dir"],
        m2752_design=paths["design"],
        executable_specs=paths["specs"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=paths["follow_up"],
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["candidate_count"] == 12
    assert summary["resolved_candidate_count"] == 12
    assert summary["candidate_execution_row_count"] == 12
    assert summary["prior_panel_unique_task_source_count"] == 9
    assert summary["stress_axis_aggregate_row_count"] == 4
    assert summary["blocker_guard_row_count"] == 2
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["prior_panel_execution"] is False
    assert summary["protected_blocker_execution"] is False
    assert summary["hf3_blocker_execution"] is False
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["stress_axis_labels_actor_visible"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    candidate_rows = _read_csv(output_dir / "cross_axis_candidate_rows.csv")
    prior_rows = _read_csv(output_dir / "prior_panel_exclusion_rows.csv")
    assert {row["candidate_admitted"] for row in candidate_rows} == {"True"}
    assert {row["prior_panel_excluded"] for row in candidate_rows} == {"False"}
    assert {row["profile_name"] for row in candidate_rows} == {"L3_online_gru"}
    assert not {row["task_source_id"] for row in candidate_rows} & {row["task_source_id"] for row in prior_rows}

    resolution_rows = _read_csv(output_dir / "execution_candidate_resolution_rows.csv")
    assert {row["resolution_status"] for row in resolution_rows} == {"resolved_to_m1690_l3_workload"}
    assert {row["execution_admitted"] for row in resolution_rows} == {"True"}

    blocker_rows = _read_csv(output_dir / "blocker_guard_rows.csv")
    assert {row["execution_run"] for row in blocker_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in blocker_rows} == {"False"}

    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    blocked_claims = [row for row in claim_rows if row["allowed_in_m2753"] == "False"]
    assert blocked_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
