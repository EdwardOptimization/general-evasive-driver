from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight
    as m2746,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path, follow_up_manifest: Path, design_doc: Path, specs_path: Path) -> tuple[Path, Path]:
    m2743_dir = root / "m2743"
    m2743_dir.mkdir()
    write_json(
        m2743_dir / "summary.json",
        {
            "status_pass": True,
            "target_panel_row_count": 18,
            "offtrack_target_row_count": 14,
            "collision_caution_row_count": 1,
            "diagnostic_success_context_row_count": 3,
            "negative_context_guardrail_row_count": 31,
            "blocked_same_surface_guard_row_count": 1,
            "protected_hf3_exclusion_guard_row_count": 11,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    target_rows = []
    candidate_specs = []
    for index in range(1, 8):
        candidate_specs.append(
            {
                "target_panel_id": f"m2743-target-panel-m2693-{index:04d}",
                "source_milestone": "m2693",
                "source_family": "source_diverse_current_sim_offtrack",
                "source_key": f"T4:source-edge-{index}",
                "workload_id": f"m1680-spec-{index - 1:04d}::L3_online_gru",
                "task_source_id": f"m1680-spec-{index - 1:04d}",
                "task_family": "T4" if index <= 4 else "T5",
            }
        )
    for index in range(1, 8):
        candidate_specs.append(
            {
                "target_panel_id": f"m2743-target-panel-m2716-{index:04d}",
                "source_milestone": "m2716",
                "source_family": "exact_executable_reentry_baseline",
                "source_key": f"m1680-spec-{index + 20:04d}",
                "workload_id": f"m1680-spec-{index + 20:04d}::L3_online_gru",
                "task_source_id": f"m1680-spec-{index + 20:04d}",
                "task_family": "T4" if index <= 4 else "T5",
            }
        )
    for index, spec in enumerate(candidate_specs, start=1):
        target_rows.append(
            {
                "target_panel_id": spec["target_panel_id"],
                "source_taxonomy_id": f"m2740-taxonomy-execution-{index:04d}",
                "scenario_role_id": "m2743-role-0001",
                "scenario_role": "offtrack_containment_target",
                "source_row_type": "candidate_execution",
                "source_milestone": spec["source_milestone"],
                "source_family": spec["source_family"],
                "source_key": spec["source_key"],
                "workload_id": spec["workload_id"],
                "task_source_id": spec["task_source_id"],
                "profile_name": "L3_online_gru",
                "task_family": spec["task_family"],
                "taxonomy_family": "off_track",
                "primary_failure_family": "off_track",
                "repair_signal": "offtrack_surface_needs_taxonomy_audit",
                "target_panel_admitted": True,
                "execution_scheduled": False,
                "guardrail_only": False,
                "actor_visible_allowed": False,
                "target_labels_actor_visible": False,
                "ranking_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": "scope",
            }
        )
    for index, role in enumerate(
        ["diagnostic_success_context", "collision_caution_guard", "diagnostic_success_context", "diagnostic_success_context"],
        start=1,
    ):
        target_rows.append(
            {
                "target_panel_id": f"m2743-target-panel-guard-{index:04d}",
                "source_taxonomy_id": f"m2740-taxonomy-context-{index:04d}",
                "scenario_role_id": "m2743-role-guard",
                "scenario_role": role,
                "source_row_type": "candidate_execution",
                "source_milestone": "m2693",
                "source_family": "guard_context",
                "source_key": f"guard-{index}",
                "workload_id": f"m1680-spec-guard-{index:04d}::L3_online_gru",
                "task_source_id": f"m1680-spec-guard-{index:04d}",
                "profile_name": "L3_online_gru",
                "task_family": "T5",
                "taxonomy_family": "diagnostic_context",
                "primary_failure_family": "diagnostic_context",
                "repair_signal": "guard_only",
                "target_panel_admitted": False,
                "execution_scheduled": False,
                "guardrail_only": True,
                "actor_visible_allowed": False,
                "target_labels_actor_visible": False,
                "ranking_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": "scope",
            }
        )
    write_csv_rows(m2743_dir / "target_panel_rows.csv", target_rows)
    write_csv_rows(m2743_dir / "scenario_role_rows.csv", [{"scenario_role_id": "m2743-role-0001", "status_pass": True}])
    write_csv_rows(m2743_dir / "metric_contract_rows.csv", [{"metric_contract_id": "metric", "status_pass": True}])
    write_csv_rows(
        m2743_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_context_id": "m2743-guardrail-context-0001",
                "scenario_role_id": "m2743-role-0002",
                "scenario_role": "collision_caution_guard",
                "source_taxonomy_family": "collision_failure",
                "source_row_type": "candidate_execution",
                "row_count": 1,
                "execution_run_count": 0,
                "execution_admitted_count": 0,
                "protected_denominator_count": 0,
                "actor_visible_count": 0,
                "guardrail_only": True,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": "scope",
            },
            {
                "guardrail_context_id": "m2743-guardrail-context-0002",
                "scenario_role_id": "m2743-role-0003",
                "scenario_role": "diagnostic_success_context",
                "source_taxonomy_family": "diagnostic_success_context",
                "source_row_type": "candidate_execution",
                "row_count": 3,
                "execution_run_count": 0,
                "execution_admitted_count": 0,
                "protected_denominator_count": 0,
                "actor_visible_count": 0,
                "guardrail_only": True,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": "scope",
            },
            {
                "guardrail_context_id": "m2743-guardrail-context-0003",
                "scenario_role_id": "m2743-role-0004",
                "scenario_role": "negative_context_guardrail",
                "source_taxonomy_family": "negative_context_guard",
                "source_row_type": "negative_context_guard",
                "row_count": 31,
                "execution_run_count": 0,
                "execution_admitted_count": 0,
                "protected_denominator_count": 0,
                "actor_visible_count": 0,
                "guardrail_only": True,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": "scope",
            },
            {
                "guardrail_context_id": "m2743-guardrail-context-0004",
                "scenario_role_id": "m2743-role-0005",
                "scenario_role": "blocked_same_surface_guard",
                "source_taxonomy_family": "blocked_guard",
                "source_row_type": "blocked_surface_guard",
                "row_count": 1,
                "execution_run_count": 0,
                "execution_admitted_count": 0,
                "protected_denominator_count": 0,
                "actor_visible_count": 0,
                "guardrail_only": True,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": "scope",
            },
            {
                "guardrail_context_id": "m2743-guardrail-context-0005",
                "scenario_role_id": "m2743-role-0006",
                "scenario_role": "protected_hf3_exclusion_guard",
                "source_taxonomy_family": "protected_or_hf3_blocker",
                "source_row_type": "blocked_surface_guard",
                "row_count": 11,
                "execution_run_count": 0,
                "execution_admitted_count": 0,
                "protected_denominator_count": 0,
                "actor_visible_count": 0,
                "guardrail_only": True,
                "ordinary_success_denominator_allowed": False,
                "claim_scope": "scope",
            },
        ],
    )
    write_csv_rows(m2743_dir / "actor_contract_guard_rows.csv", [{"guard_id": "obs", "status_pass": True}])
    write_csv_rows(m2743_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2743_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])

    m2693_rows = root / "m2693_rows.csv"
    write_csv_rows(
        m2693_rows,
        [
            {
                "target_id": f"m2691-target-{index:04d}",
                "workload_id": f"m1680-spec-{index - 1:04d}::L3_online_gru",
                "task_source_id": f"m1680-spec-{index - 1:04d}",
                "profile_name": "L3_online_gru",
                "task_family": "T4" if index <= 4 else "T5",
                "source_key": f"T4:source-edge-{index}",
                "source_edge": f"source-edge-{index}",
                "window_tag": "window",
                "strata": "strata",
                "executable_source_family": "capability_step_up",
                "env_template_family": "template",
                "profile_config_path": "config.json",
                "checkpoint_path": "checkpoint.pt",
                "eval_seed": 269300 + index,
            }
            for index in range(1, 8)
        ],
    )
    m2716_rows = root / "m2716_rows.csv"
    write_csv_rows(
        m2716_rows,
        [
            {
                "candidate_id": f"m2716-candidate-{index:04d}",
                "workload_id": f"m1680-spec-{index + 20:04d}::L3_online_gru",
                "task_source_id": f"m1680-spec-{index + 20:04d}",
                "profile_name": "L3_online_gru",
                "task_family": "T4" if index <= 4 else "T5",
                "source_key": f"m1680-spec-{index + 20:04d}",
                "source_edge": f"source-edge-{index + 20}",
                "window_tag": "window",
                "strata": "strata",
                "executable_source_family": "capability_step_up",
                "env_template_family": "template",
                "profile_config_path": "config.json",
                "checkpoint_path": "checkpoint.pt",
                "eval_seed": 271600 + index,
            }
            for index in range(1, 8)
        ],
    )
    write_json(
        specs_path,
        {
            "executable_task_specs": [
                {"task_source_id": f"m1680-spec-{index:04d}", "env_config": {}}
                for index in list(range(7)) + list(range(21, 28))
            ]
        },
    )
    follow_up_manifest.write_text('{"id": "m2747"}\n', encoding="utf-8")
    design_doc.write_text(m2746.DEFAULT_MILESTONE + "\n", encoding="utf-8")
    return m2693_rows, m2716_rows


def test_m2746_executes_only_offtrack_targets_and_carries_role_guardrails(monkeypatch, tmp_path: Path) -> None:
    follow_up_manifest = tmp_path / "m2747.json"
    design_doc = tmp_path / "m2745.md"
    specs_path = tmp_path / "specs.json"
    m2693_rows, m2716_rows = _write_source_artifacts(tmp_path, follow_up_manifest, design_doc, specs_path)
    output_dir = tmp_path / "m2746"
    doc_path = tmp_path / "m2746.md"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"]):
            rows.append(
                {
                    "seed": 274600 + index,
                    "policy": "checkpoint",
                    "steps": 80 + index,
                    "collision": index % 11 == 0,
                    "obstacle_completed": index % 5 == 0,
                    "success": index % 5 == 0 and index % 11 != 0,
                    "termination_reason": "collision" if index % 11 == 0 else "off_track",
                    "min_clearance_margin": 0.2,
                    "return": 1.0,
                    "action_rate_mean": 0.1,
                    "high_sideslip_fraction": 0.0,
                    "task_family": resolution["task_family"],
                    "source_milestone": resolution["source_milestone"],
                    "source_family": resolution["source_family"],
                    "candidate_id": resolution["candidate_id"],
                    "resolution_id": resolution["resolution_id"],
                    "m2746_eval_seed": 274600 + index,
                    "bounded_role_panel_execution_preflight": True,
                    "guardrail_execution": False,
                    "collision_caution_execution": False,
                    "diagnostic_success_context_execution": False,
                    "negative_context_execution": False,
                    "blocked_same_surface_execution": False,
                    "protected_hf3_execution": False,
                    "hidden_oracle_actor_input_required": False,
                    "scenario_role_labels_actor_visible": False,
                    "metric_labels_actor_visible": False,
                    "target_labels_actor_visible": False,
                    "protected_labels_actor_visible": False,
                    "blocker_labels_actor_visible": False,
                    "route_labels_actor_visible": False,
                    "success_progress_labels_actor_visible": False,
                    "verdict_labels_actor_visible": False,
                    "guardrail_rows_in_success_denominator": False,
                    "training_started": False,
                    "replay_started": False,
                    "ppo_used": False,
                    "profile_specific_tuning": False,
                    "active_config_overwritten": False,
                    "repair_overlay_applied": False,
                    "ranking_run": False,
                    "winner_selected": False,
                    "checkpoint_promoted": False,
                    "success_rate_verdict_claim_made": False,
                    "driver_performance_claim_made": False,
                    "paper_claim_made": False,
                    "current_sim_verdict_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
        write_csv_rows(output / "candidate_execution_rows.csv", rows)
        write_csv_rows(output / "candidate_execution_failure_rows.csv", [], fieldnames=m2746.FAILURE_FIELDNAMES)
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return {
            "result_class": "engineering_controller_route_a_role_panel_bounded_candidate_execution_pass",
            "all_selected_metrics_finite": True,
        }

    monkeypatch.setattr(m2746, "run_candidate_execution", fake_execution)
    summary = m2746.run_role_panel_bounded_execution_preflight(
        m2743_dir=tmp_path / "m2743",
        m2745_design=design_doc,
        m2693_execution_rows=m2693_rows,
        m2716_execution_rows=m2716_rows,
        executable_specs=specs_path,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["candidate_count"] == 14
    assert summary["resolved_candidate_count"] == 14
    assert summary["m2693_candidate_count"] == 7
    assert summary["m2716_candidate_count"] == 7
    assert summary["candidate_execution_row_count"] == 14
    assert summary["candidate_execution_failure_row_count"] == 0
    assert summary["guardrail_context_row_count"] == 5
    assert summary["collision_caution_row_count"] == 1
    assert summary["diagnostic_success_context_row_count"] == 3
    assert summary["negative_context_guardrail_row_count"] == 31
    assert summary["blocked_same_surface_guard_row_count"] == 1
    assert summary["protected_hf3_exclusion_guard_row_count"] == 11
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["guardrail_execution"] is False
    assert summary["guardrail_rows_in_success_denominator"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    candidate_rows = _read_csv(output_dir / "execution_candidate_rows.csv")
    assert len(candidate_rows) == 14
    assert {row["scenario_role"] for row in candidate_rows} == {"offtrack_containment_target"}
    assert {row["execution_scheduled_in_m2746"] for row in candidate_rows} == {"True"}

    resolution_rows = _read_csv(output_dir / "execution_candidate_resolution_rows.csv")
    assert len(resolution_rows) == 14
    assert {row["resolution_status"] for row in resolution_rows} == {"resolved_to_current_m1690_workload"}
    assert {row["execution_admitted"] for row in resolution_rows} == {"True"}
    assert {row["profile_name"] for row in resolution_rows} == {"L3_online_gru"}

    guardrail_rows = _read_csv(output_dir / "guardrail_context_rows.csv")
    assert {row["execution_run"] for row in guardrail_rows} == {"False"}
    assert {row["execution_admitted"] for row in guardrail_rows} == {"False"}
    assert {row["ordinary_success_denominator_allowed"] for row in guardrail_rows} == {"False"}

    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    blocked_claims = [row for row in claim_rows if row["allowed_in_m2746"] == "False"]
    assert blocked_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
