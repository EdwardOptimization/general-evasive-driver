from __future__ import annotations

import csv
from pathlib import Path

from autodrift import (
    engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight as m2877,
)
from autodrift.artifacts import write_csv_rows, write_json


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_prior_rows(path: Path, task_source_ids: list[str]) -> None:
    write_csv_rows(
        path,
        [
            {
                "task_source_id": task_source_id,
                "workload_id": f"{task_source_id}::L3_online_gru",
                "profile_name": "L3_online_gru",
                "termination_reason": "off_track",
            }
            for task_source_id in task_source_ids
        ],
    )


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m1690 = root / "m1690.csv"
    workload_rows = []
    for selected in m2877.SELECTED_TASK_SOURCES:
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

    selected_ids = {row[0] for row in m2877.SELECTED_TASK_SOURCES}
    prior_ids = [f"m1680-spec-{index:04d}" for index in range(67) if f"m1680-spec-{index:04d}" not in selected_ids]
    assert len(prior_ids) == 61

    m2737_dir = root / "m2737"
    m2807_dir = root / "m2807"
    m2816_dir = root / "m2816"
    m2828_dir = root / "m2828"
    m2838_dir = root / "m2838"
    m2868_dir = root / "m2868"
    for directory in (m2737_dir, m2807_dir, m2816_dir, m2828_dir, m2838_dir, m2868_dir):
        directory.mkdir()
    _write_prior_rows(m2737_dir / "candidate_execution_rows.csv", prior_ids[:9])
    _write_prior_rows(m2807_dir / "candidate_execution_rows.csv", prior_ids[9:21])
    _write_prior_rows(m2816_dir / "instrumented_execution_rows.csv", prior_ids[21:33])
    _write_prior_rows(m2828_dir / "candidate_execution_rows.csv", prior_ids[33:49])
    _write_prior_rows(m2838_dir / "candidate_execution_rows.csv", prior_ids[49:57])
    _write_prior_rows(m2868_dir / "paired_execution_rows.csv", prior_ids[57:])

    m2873_dir = root / "m2873"
    m2873_dir.mkdir()
    write_json(m2873_dir / "summary.json", {"status_pass": True})
    write_csv_rows(
        m2873_dir / "latest_negative_evidence_rows.csv",
        [
            {
                "negative_evidence_id": "protected_mitigation_blocker",
                "source_milestone": "m2667",
                "evidence_status": "active_limitation",
                "observed_value": "25 protected rows",
                "blocked_claims": "repair success; driver performance",
            }
        ],
    )
    write_csv_rows(
        m2873_dir / "known_blocker_disclosure_rows.csv",
        [
            {
                "blocker_id": "hf3_source_dependency",
                "source_milestone": "m2836",
                "blocker_status": "active",
                "blocked_claims": "high fidelity validation",
            }
        ],
    )
    write_csv_rows(
        m2873_dir / "actor_action_contract_rows.csv",
        [{"contract_row_id": "actor", "contract_field": "observation_shape", "status_pass": True}],
    )
    write_csv_rows(
        m2873_dir / "claim_boundary_rows.csv",
        [
            {
                "claim_id": "m2873_claim_boundary_local_package_refresh_materialized",
                "claim_family": "local_package_refresh_materialized",
                "allowed_in_m2873": True,
                "status_pass": True,
                "evidence_required_before_claim": "M2873 local package refresh rows",
            },
            {
                "claim_id": "m2873_claim_boundary_driver_performance",
                "claim_family": "driver_performance",
                "allowed_in_m2873": False,
                "status_pass": True,
                "evidence_required_before_claim": "future validation gate",
            },
        ],
    )
    write_csv_rows(
        m2873_dir / "package_gate_matrix.csv",
        [{"gate_id": "m2873_gate", "gate_family": "artifact", "status_pass": True}],
    )

    specs = root / "specs.json"
    write_json(
        specs,
        {"executable_task_specs": [{"task_source_id": row["task_source_id"], "env_config": {}} for row in workload_rows]},
    )
    design = root / "m2876.md"
    design.write_text("M2876 fixed 11-row design\n", encoding="utf-8")
    follow_up = root / "m2878.json"
    follow_up.write_text('{"id": "m2878"}\n', encoding="utf-8")
    return {
        "m1690": m1690,
        "m2876_design": design,
        "m2873_dir": m2873_dir,
        "m2737_dir": m2737_dir,
        "m2807_dir": m2807_dir,
        "m2816_dir": m2816_dir,
        "m2828_dir": m2828_dir,
        "m2838_dir": m2838_dir,
        "m2868_dir": m2868_dir,
        "specs": specs,
        "follow_up": follow_up,
    }


def test_m2877_executes_fixed_11_row_fresh_surface_and_blocks_overclaims(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2877"
    doc_path = tmp_path / "m2877.md"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"]):
            collision = index % 5 == 0
            obstacle_completed = index % 3 == 0
            success = obstacle_completed and not collision
            row = {
                "seed": 287700 + index,
                "policy": "checkpoint",
                "steps": 80 + index,
                "collision": collision,
                "obstacle_completed": obstacle_completed,
                "success": success,
                "termination_reason": "obstacle_completed" if success else "off_track",
                "min_clearance_margin": 0.12,
                "return": 1.0,
                "action_rate_mean": 0.1,
                "high_sideslip_fraction": 0.0,
                "task_family": resolution["task_family"],
                "source_edge": resolution["source_edge"],
                "candidate_id": resolution["candidate_id"],
                "resolution_id": resolution["resolution_id"],
                "task_source_id": resolution["task_source_id"],
            }
            row.update(m2877.candidate_execution_metadata(resolution, eval_seed=287700 + index))
            rows.append(row)
        write_csv_rows(output / "candidate_execution_rows.csv", rows)
        write_csv_rows(output / "candidate_execution_failure_rows.csv", [], fieldnames=m2877.FAILURE_FIELDNAMES)
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return {
            "result_class": "engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight_pass",
            "all_selected_metrics_finite": True,
        }

    monkeypatch.setattr(m2877, "run_candidate_execution", fake_execution)
    summary = m2877.run_post_package_refresh_fresh_closed_loop_evidence_preflight(
        m1690_workload=paths["m1690"],
        m2876_design=paths["m2876_design"],
        m2873_dir=paths["m2873_dir"],
        m2737_dir=paths["m2737_dir"],
        m2807_dir=paths["m2807_dir"],
        m2816_dir=paths["m2816_dir"],
        m2828_dir=paths["m2828_dir"],
        m2838_dir=paths["m2838_dir"],
        m2868_dir=paths["m2868_dir"],
        executable_specs=paths["specs"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=paths["follow_up"],
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["candidate_count"] == 11
    assert summary["resolved_candidate_count"] == 11
    assert summary["candidate_execution_row_count"] == 11
    assert summary["candidate_execution_failure_row_count"] == 0
    assert summary["prior_surface_unique_task_source_count"] == 61
    assert summary["scenario_role_metric_row_count"] == 11
    assert summary["failure_taxonomy_row_count"] == 11
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["claim_boundary_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["prior_surface_execution"] is False
    assert summary["package_limitation_execution"] is False
    assert summary["protected_blocker_execution"] is False
    assert summary["hf3_blocker_execution"] is False
    assert summary["ordinary_success_denominator_allowed"] is False
    assert summary["hidden_oracle_actor_input_required"] is False
    assert summary["package_labels_actor_visible"] is False
    assert summary["blocker_labels_actor_visible"] is False
    assert summary["route_labels_actor_visible"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    candidate_rows = _read_csv(output_dir / "fresh_candidate_rows.csv")
    prior_rows = _read_csv(output_dir / "prior_surface_exclusion_rows.csv")
    assert {row["candidate_admitted"] for row in candidate_rows} == {"True"}
    assert {row["prior_surface_excluded"] for row in candidate_rows} == {"False"}
    assert {row["profile_name"] for row in candidate_rows} == {"L3_online_gru"}
    assert [row["task_source_id"] for row in candidate_rows] == [row[0] for row in m2877.SELECTED_TASK_SOURCES]
    assert len({row["task_source_id"] for row in prior_rows}) == 61
    assert not {row["task_source_id"] for row in candidate_rows} & {row["task_source_id"] for row in prior_rows}

    resolution_rows = _read_csv(output_dir / "execution_candidate_resolution_rows.csv")
    assert {row["resolution_status"] for row in resolution_rows} == {"resolved_to_m1690_l3_workload"}
    assert {row["execution_admitted"] for row in resolution_rows} == {"True"}

    package_rows = _read_csv(output_dir / "package_limitation_guard_rows.csv")
    assert {row["execution_run"] for row in package_rows} == {"False"}
    assert {row["ordinary_success_denominator_allowed"] for row in package_rows} == {"False"}

    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    blocked_claims = [row for row in claim_rows if row["allowed_in_m2877"] == "False"]
    allowed_claims = [row for row in claim_rows if row["allowed_in_m2877"] == "True"]
    assert blocked_claims
    assert allowed_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
