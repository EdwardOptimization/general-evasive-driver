from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import engineering_controller_route_a_post_package_source_diverse_closed_loop_evidence_expansion_preflight as m2828


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m1690 = root / "m1690.csv"
    workload_rows = []
    for selected in m2828.SELECTED_TASK_SOURCES:
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
    m2807_dir = root / "m2807"
    m2816_dir = root / "m2816"
    m2824_dir = root / "m2824"
    m2737_dir.mkdir()
    m2807_dir.mkdir()
    m2816_dir.mkdir()
    m2824_dir.mkdir()

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
    m2737_rows = [
        {
            "task_source_id": task_source_id,
            "workload_id": f"{task_source_id}::L3_online_gru",
            "profile_name": "L3_online_gru",
            "termination_reason": "off_track",
        }
        for task_source_id in m2737_sources
    ]
    m2807_rows = [
        {
            "task_source_id": task_source_id,
            "workload_id": f"{task_source_id}::L3_online_gru",
            "profile_name": "L3_online_gru",
            "termination_reason": "off_track",
        }
        for task_source_id in m2807_sources
    ]
    write_csv_rows(m2737_dir / "candidate_execution_rows.csv", m2737_rows)
    write_csv_rows(m2807_dir / "candidate_execution_rows.csv", m2807_rows)
    write_csv_rows(m2816_dir / "instrumented_execution_rows.csv", m2807_rows)

    write_json(m2824_dir / "summary.json", {"status_pass": True})
    write_csv_rows(
        m2824_dir / "known_blocker_disclosure_rows.csv",
        [
            {
                "blocker_id": f"blocker_{index}",
                "source_milestone": "m2824",
                "blocker_status": "active",
                "blocked_claims": "driver performance",
            }
            for index in range(5)
        ],
    )
    write_csv_rows(
        m2824_dir / "recoverability_limitations_rows.csv",
        [
            {
                "limitation_id": f"limitation_{index}",
                "source_milestone": "m2816",
                "observed_value": index,
                "blocked_interpretation": "recoverability success",
            }
            for index in range(7)
        ],
    )
    write_csv_rows(m2824_dir / "actor_action_contract_rows.csv", [{"guard": "actor_72_action_3"}])
    write_csv_rows(m2824_dir / "claim_boundary_rows.csv", [{"claim": "no_performance_claim"}])

    specs = root / "specs.json"
    write_json(specs, {"executable_task_specs": [{"task_source_id": row["task_source_id"], "env_config": {}} for row in workload_rows]})
    design = root / "m2827.md"
    design.write_text("M2827 design\n", encoding="utf-8")
    follow_up = root / "m2829.json"
    follow_up.write_text('{"id": "m2829"}\n', encoding="utf-8")
    return {
        "m1690": m1690,
        "m2737_dir": m2737_dir,
        "m2807_dir": m2807_dir,
        "m2816_dir": m2816_dir,
        "m2824_dir": m2824_dir,
        "specs": specs,
        "design": design,
        "follow_up": follow_up,
    }


def test_m2828_selects_fresh_post_package_surface_and_blocks_overclaims(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2828"
    doc_path = tmp_path / "m2828.md"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"]):
            collision = index % 7 == 0
            obstacle_completed = index % 4 == 0
            success = obstacle_completed and not collision
            row = {
                "seed": 282800 + index,
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
            row.update(m2828.candidate_execution_metadata(resolution, eval_seed=282800 + index))
            rows.append(row)
        write_csv_rows(output / "candidate_execution_rows.csv", rows)
        write_csv_rows(output / "candidate_execution_failure_rows.csv", [], fieldnames=m2828.FAILURE_FIELDNAMES)
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return {
            "result_class": "engineering_controller_route_a_post_package_source_diverse_closed_loop_evidence_expansion_pass",
            "all_selected_metrics_finite": True,
        }

    monkeypatch.setattr(m2828, "run_candidate_execution", fake_execution)
    summary = m2828.run_post_package_source_diverse_closed_loop_evidence_expansion_preflight(
        m1690_workload=paths["m1690"],
        m2827_design=paths["design"],
        m2824_dir=paths["m2824_dir"],
        m2737_dir=paths["m2737_dir"],
        m2807_dir=paths["m2807_dir"],
        m2816_dir=paths["m2816_dir"],
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
    assert summary["prior_surface_unique_task_source_count"] == 21
    assert summary["source_family_aggregate_row_count"] == 5
    assert summary["scenario_role_metric_row_count"] == 16
    assert summary["failure_taxonomy_row_count"] == 16
    assert summary["package_limitation_guard_row_count"] == 12
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["claim_boundary_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["prior_surface_execution"] is False
    assert summary["same_recoverability_execution"] is False
    assert summary["package_limitation_execution"] is False
    assert summary["protected_blocker_execution"] is False
    assert summary["hf3_blocker_execution"] is False
    assert summary["ordinary_success_denominator_allowed"] is False
    assert summary["hidden_oracle_actor_input_required"] is False
    assert summary["package_labels_actor_visible"] is False
    assert summary["recoverability_labels_actor_visible"] is False
    assert summary["scenario_role_labels_actor_visible"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    candidate_rows = _read_csv(output_dir / "post_package_candidate_rows.csv")
    prior_rows = _read_csv(output_dir / "prior_surface_exclusion_rows.csv")
    assert {row["candidate_admitted"] for row in candidate_rows} == {"True"}
    assert {row["prior_surface_excluded"] for row in candidate_rows} == {"False"}
    assert {row["profile_name"] for row in candidate_rows} == {"L3_online_gru"}
    assert len({row["task_source_id"] for row in candidate_rows}) == 16
    assert not {row["task_source_id"] for row in candidate_rows} & {row["task_source_id"] for row in prior_rows}

    resolution_rows = _read_csv(output_dir / "execution_candidate_resolution_rows.csv")
    assert {row["resolution_status"] for row in resolution_rows} == {"resolved_to_m1690_l3_workload"}
    assert {row["execution_admitted"] for row in resolution_rows} == {"True"}

    package_rows = _read_csv(output_dir / "package_limitation_guard_rows.csv")
    assert {row["execution_run"] for row in package_rows} == {"False"}
    assert {row["ordinary_success_denominator_allowed"] for row in package_rows} == {"False"}

    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    blocked_claims = [row for row in claim_rows if row["allowed_in_m2828"] == "False"]
    allowed_claims = [row for row in claim_rows if row["allowed_in_m2828"] == "True"]
    assert blocked_claims
    assert allowed_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
