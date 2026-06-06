from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight as m2838


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _prior_rows(task_source_ids: list[str]) -> list[dict[str, str]]:
    return [
        {
            "task_source_id": task_source_id,
            "workload_id": f"{task_source_id}::L3_online_gru",
            "profile_name": "L3_online_gru",
            "termination_reason": "off_track",
        }
        for task_source_id in task_source_ids
    ]


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m1690 = root / "m1690.csv"
    workload_rows = []
    for selected in m2838.SELECTED_TASK_SOURCES:
        task_source_id, task_family, source_edge, window_tag, *_rest = selected
        workload_rows.append(
            {
                "workload_id": f"{task_source_id}::L3_online_gru",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": task_family,
                "source_edge": source_edge,
                "window_tag": window_tag,
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

    m2737_dir = root / "m2737"
    m2759_dir = root / "m2759"
    m2807_dir = root / "m2807"
    m2816_dir = root / "m2816"
    m2828_dir = root / "m2828"
    for directory in (m2737_dir, m2759_dir, m2807_dir, m2816_dir, m2828_dir):
        directory.mkdir()

    m2737_sources = [
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
    m2759_sources = [
        "m1680-spec-0001",
        "m1680-spec-0003",
        "m1680-spec-0008",
        "m1680-spec-0010",
        "m1680-spec-0037",
        "m1680-spec-0039",
        "m1680-spec-0042",
        "m1680-spec-0043",
        "m1680-spec-0044",
        "m1680-spec-0045",
        "m1680-spec-0046",
        "m1680-spec-0047",
    ]
    m2807_sources = [
        "m1680-spec-0014",
        "m1680-spec-0016",
        "m1680-spec-0018",
        "m1680-spec-0022",
        "m1680-spec-0026",
        "m1680-spec-0032",
        "m1680-spec-0048",
        "m1680-spec-0051",
        "m1680-spec-0052",
        "m1680-spec-0053",
        "m1680-spec-0058",
        "m1680-spec-0063",
    ]
    m2828_sources = [
        "m1680-spec-0007",
        "m1680-spec-0009",
        "m1680-spec-0011",
        "m1680-spec-0013",
        "m1680-spec-0015",
        "m1680-spec-0017",
        "m1680-spec-0021",
        "m1680-spec-0023",
        "m1680-spec-0037",
        "m1680-spec-0039",
        "m1680-spec-0042",
        "m1680-spec-0044",
        "m1680-spec-0046",
        "m1680-spec-0047",
        "m1680-spec-0049",
        "m1680-spec-0050",
    ]
    write_csv_rows(m2737_dir / "candidate_execution_rows.csv", _prior_rows(m2737_sources))
    write_csv_rows(m2759_dir / "probe_execution_rows.csv", _prior_rows(m2759_sources))
    write_csv_rows(m2807_dir / "candidate_execution_rows.csv", _prior_rows(m2807_sources))
    write_csv_rows(m2816_dir / "instrumented_execution_rows.csv", _prior_rows(m2807_sources))
    write_csv_rows(m2828_dir / "candidate_execution_rows.csv", _prior_rows(m2828_sources))

    specs = root / "specs.json"
    write_json(specs, {"executable_task_specs": [{"task_source_id": row["task_source_id"], "env_config": {}} for row in workload_rows]})
    design = root / "m2837.md"
    design.write_text("M2837 design\n", encoding="utf-8")
    follow_up = root / "m2839.json"
    follow_up.write_text('{"id": "m2839"}\n', encoding="utf-8")
    return {
        "m1690": m1690,
        "m2737_dir": m2737_dir,
        "m2759_dir": m2759_dir,
        "m2807_dir": m2807_dir,
        "m2816_dir": m2816_dir,
        "m2828_dir": m2828_dir,
        "specs": specs,
        "design": design,
        "follow_up": follow_up,
    }


def test_m2838_selects_post_hf3_stop_fresh_surface_and_blocks_overclaims(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2838"
    doc_path = tmp_path / "m2838.md"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"]):
            collision = index % 9 == 0
            obstacle_completed = index % 5 == 0
            success = obstacle_completed and not collision
            row = {
                "seed": 283800 + index,
                "policy": "checkpoint",
                "steps": 90 + index,
                "collision": collision,
                "obstacle_completed": obstacle_completed,
                "success": success,
                "termination_reason": "obstacle_completed" if success else "off_track",
                "min_clearance_margin": 0.15,
                "return": 1.0,
                "action_rate_mean": 0.1,
                "high_sideslip_fraction": 0.0,
                "task_family": resolution["task_family"],
                "source_edge": resolution["source_edge"],
                "candidate_id": resolution["candidate_id"],
                "resolution_id": resolution["resolution_id"],
                "task_source_id": resolution["task_source_id"],
            }
            row.update(m2838.candidate_execution_metadata(resolution, eval_seed=283800 + index))
            rows.append(row)
        write_csv_rows(output / "candidate_execution_rows.csv", rows)
        write_csv_rows(output / "candidate_execution_failure_rows.csv", [], fieldnames=m2838.FAILURE_FIELDNAMES)
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return {
            "result_class": "engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight_pass",
            "all_selected_metrics_finite": True,
        }

    monkeypatch.setattr(m2838, "run_candidate_execution", fake_execution)
    summary = m2838.run_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight(
        m1690_workload=paths["m1690"],
        m2837_design=paths["design"],
        m2737_dir=paths["m2737_dir"],
        m2759_dir=paths["m2759_dir"],
        m2807_dir=paths["m2807_dir"],
        m2816_dir=paths["m2816_dir"],
        m2828_dir=paths["m2828_dir"],
        executable_specs=paths["specs"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=paths["follow_up"],
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["candidate_count"] == 16
    assert summary["resolved_candidate_count"] == 16
    assert summary["candidate_execution_row_count"] == 16
    assert summary["candidate_execution_failure_row_count"] == 0
    assert summary["prior_surface_unique_task_source_count"] == 43
    assert summary["scenario_role_metric_row_count"] == 16
    assert summary["failure_taxonomy_row_count"] == 16
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["claim_boundary_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["prior_surface_execution"] is False
    assert summary["protected_blocker_execution"] is False
    assert summary["hf3_blocker_execution"] is False
    assert summary["ordinary_success_denominator_allowed"] is False
    assert summary["hidden_oracle_actor_input_required"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    selected_rows = _read_csv(output_dir / "selected_candidate_rows.csv")
    prior_rows = _read_csv(output_dir / "prior_surface_exclusion_rows.csv")
    assert len(selected_rows) == 16
    assert {row["task_source_id"] for row in selected_rows}.isdisjoint(
        {row["task_source_id"] for row in prior_rows}
    )
