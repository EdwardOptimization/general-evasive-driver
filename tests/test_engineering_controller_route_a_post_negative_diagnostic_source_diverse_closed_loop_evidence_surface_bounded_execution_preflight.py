from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight
    as m2737,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path, follow_up_manifest: Path, design_doc: Path, specs_path: Path) -> tuple[Path, Path]:
    m2734_dir = root / "m2734"
    m2734_dir.mkdir()
    write_json(
        m2734_dir / "summary.json",
        {
            "status_pass": True,
            "evidence_surface_candidate_row_count": 18,
            "m2693_candidate_row_count": 9,
            "m2716_candidate_row_count": 9,
            "negative_diagnostic_context_row_count": 31,
            "blocked_surface_row_count": 12,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    candidate_rows = []
    for index in range(1, 10):
        candidate_rows.append(
            {
                "candidate_id": f"m2734-candidate-m2693-{index:04d}",
                "source_milestone": "m2693",
                "source_row_id": f"m2691-target-{index:04d}",
                "source_family": "source_diverse_current_sim_offtrack",
                "source_bucket": "m2693_source_diverse_target",
                "task_family": "T4" if index <= 5 else "T5",
                "source_key": f"source-key-{index}",
                "source_execution_row_count": 1,
                "diagnostic_success_count": 0,
                "collision_count": 0,
                "offtrack_count": 1,
                "speed_too_low_count": 0,
                "materialization_admitted": True,
                "same_surface_m2728_repair": False,
                "protected_or_hf3_blocked": False,
                "actor_contract_shape_72_action_3": True,
                "hidden_oracle_actor_input_detected": False,
                "diagnostic_only_no_verdict": True,
                "future_role": "future_source_diverse_execution_design_candidate_after_audit",
                "claim_scope": "scope",
                "forbidden_interpretation": "forbidden",
            }
        )
    for index in range(1, 10):
        candidate_rows.append(
            {
                "candidate_id": f"m2734-candidate-m2716-{index:04d}",
                "source_milestone": "m2716",
                "source_row_id": f"m1680-spec-{index - 1:04d}",
                "source_family": "exact_executable_reentry_baseline",
                "source_bucket": "m2716_exact_task_source",
                "task_family": "T4" if index <= 5 else "T5",
                "source_key": f"m1680-spec-{index - 1:04d}",
                "source_execution_row_count": 4,
                "diagnostic_success_count": 0,
                "collision_count": 0,
                "offtrack_count": 4,
                "speed_too_low_count": 0,
                "materialization_admitted": True,
                "same_surface_m2728_repair": False,
                "protected_or_hf3_blocked": False,
                "actor_contract_shape_72_action_3": True,
                "hidden_oracle_actor_input_detected": False,
                "diagnostic_only_no_verdict": True,
                "future_role": "future_non_same_surface_execution_design_candidate_after_audit",
                "claim_scope": "scope",
                "forbidden_interpretation": "forbidden",
            }
        )
    write_csv_rows(m2734_dir / "evidence_surface_candidate_rows.csv", candidate_rows)
    write_csv_rows(
        m2734_dir / "negative_diagnostic_context_rows.csv",
        [
            {
                "context_id": f"m2734-negative-context-{index:04d}",
                "source_row_id": str(index),
                "candidate_row_id": f"repair-{index}",
                "anchor_task_source_id": f"m1680-spec-{index % 9:04d}",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "success": index == 1,
                "collision": index in {2, 3, 4},
                "termination_reason": "collision" if index in {2, 3, 4} else "off_track",
                "outcome_bucket": "negative_context",
                "context_role": "negative_repair_context_only_not_candidate",
                "direct_same_surface_repair_execution_admitted": False,
                "diagnostic_only_no_verdict": True,
                "claim_scope": "scope",
                "forbidden_interpretation": "forbidden",
            }
            for index in range(1, 32)
        ],
    )
    blocked_rows = [
        {
            "blocked_id": "m2734-blocked-same-surface-m2728-repair",
            "blocked_family": "same_surface_repair_loop",
            "source_milestone": "m2728",
            "source_row_id": "all_m2728_repair_rows",
            "row_count": 31,
            "blocking_count": 31,
            "blocked_reason": "same surface repair blocked",
            "materialization_admitted": False,
            "protected_rows_in_success_denominator": False,
            "actor_visible_allowed": False,
            "claim_scope": "scope",
            "forbidden_interpretation": "forbidden",
        }
    ]
    blocked_rows.extend(
        {
            "blocked_id": f"m2734-blocked-protected-{index:04d}",
            "blocked_family": "protected_mitigation_blocker",
            "source_milestone": "m2667",
            "source_row_id": f"protected-{index}",
            "row_count": 1,
            "blocking_count": 1,
            "blocked_reason": "protected blocker",
            "materialization_admitted": False,
            "protected_rows_in_success_denominator": False,
            "actor_visible_allowed": False,
            "claim_scope": "scope",
            "forbidden_interpretation": "forbidden",
        }
        for index in range(1, 11)
    )
    blocked_rows.append(
        {
            "blocked_id": "m2734-blocked-hf3-source-dependency",
            "blocked_family": "hf3_source_dependency_blocker",
            "source_milestone": "m2638",
            "source_row_id": "hf3",
            "row_count": 1,
            "blocking_count": 1,
            "blocked_reason": "hf3 dependency",
            "materialization_admitted": False,
            "protected_rows_in_success_denominator": False,
            "actor_visible_allowed": False,
            "claim_scope": "scope",
            "forbidden_interpretation": "forbidden",
        }
    )
    write_csv_rows(m2734_dir / "blocked_surface_rows.csv", blocked_rows)
    write_csv_rows(m2734_dir / "actor_contract_guard_rows.csv", [{"guard_id": "obs", "status_pass": True}])
    write_csv_rows(m2734_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2734_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])

    m2693_rows = root / "m2693_rows.csv"
    write_csv_rows(
        m2693_rows,
        [
            {
                "target_id": f"m2691-target-{index:04d}",
                "workload_id": f"m1680-spec-{index - 1:04d}::L3_online_gru",
                "task_source_id": f"m1680-spec-{index - 1:04d}",
                "profile_name": "L3_online_gru",
                "task_family": "T4" if index <= 5 else "T5",
                "source_edge": f"edge-{index}",
                "window_tag": "window",
                "strata": "strata",
                "executable_source_family": "capability_step_up",
                "env_template_family": "template",
                "profile_config_path": "config.json",
                "checkpoint_path": "checkpoint.pt",
                "eval_seed": 269300 + index,
            }
            for index in range(1, 10)
        ],
    )
    m2716_rows = root / "m2716_rows.csv"
    write_csv_rows(
        m2716_rows,
        [
            {
                "candidate_id": f"m2716-candidate-{index:04d}",
                "workload_id": f"m1680-spec-{index - 1:04d}::L3_online_gru",
                "task_source_id": f"m1680-spec-{index - 1:04d}",
                "profile_name": "L3_online_gru",
                "task_family": "T4" if index <= 5 else "T5",
                "source_edge": f"edge-{index}",
                "window_tag": "window",
                "strata": "strata",
                "executable_source_family": "capability_step_up",
                "env_template_family": "template",
                "profile_config_path": "config.json",
                "checkpoint_path": "checkpoint.pt",
                "eval_seed": 271600 + index,
            }
            for index in range(1, 10)
        ],
    )
    write_json(specs_path, {"executable_task_specs": [{"task_source_id": f"m1680-spec-{index:04d}", "env_config": {}} for index in range(9)]})
    follow_up_manifest.write_text('{"id": "m2738"}\n', encoding="utf-8")
    design_doc.write_text(m2737.DEFAULT_MILESTONE + "\n", encoding="utf-8")
    return m2693_rows, m2716_rows


def test_m2737_resolves_source_diverse_candidates_executes_only_admitted_surface_and_blocks_overclaims(
    monkeypatch,
    tmp_path: Path,
) -> None:
    follow_up_manifest = tmp_path / "m2738.json"
    design_doc = tmp_path / "m2736.md"
    specs_path = tmp_path / "specs.json"
    m2693_rows, m2716_rows = _write_source_artifacts(tmp_path, follow_up_manifest, design_doc, specs_path)
    output_dir = tmp_path / "m2737"
    doc_path = tmp_path / "m2737.md"

    def fake_execution(**kwargs: object) -> dict[str, object]:
        output = Path(kwargs["output_dir"])
        rows = []
        for index, resolution in enumerate(kwargs["resolution_rows"]):
            rows.append(
                {
                    "seed": 273700 + index,
                    "policy": "checkpoint",
                    "steps": 80 + index,
                    "collision": index % 7 == 0,
                    "obstacle_completed": index % 5 == 0,
                    "success": index % 5 == 0 and index % 7 != 0,
                    "termination_reason": "collision" if index % 7 == 0 else "off_track",
                    "min_clearance_margin": 0.2,
                    "return": 1.0,
                    "action_rate_mean": 0.1,
                    "high_sideslip_fraction": 0.0,
                    "task_family": resolution["task_family"],
                    "source_milestone": resolution["source_milestone"],
                    "source_family": resolution["source_family"],
                    "candidate_id": resolution["candidate_id"],
                    "resolution_id": resolution["resolution_id"],
                    "m2737_eval_seed": 273700 + index,
                    "bounded_source_diverse_execution_preflight": True,
                    "m2728_negative_context_execution": False,
                    "same_surface_m2728_repair_execution": False,
                    "protected_blocker_execution": False,
                    "hf3_blocker_execution": False,
                    "hidden_oracle_actor_input_required": False,
                    "target_labels_actor_visible": False,
                    "protected_labels_actor_visible": False,
                    "blocker_labels_actor_visible": False,
                    "route_labels_actor_visible": False,
                    "verdict_labels_actor_visible": False,
                    "protected_rows_in_success_denominator": False,
                    "training_started": False,
                    "replay_started": False,
                    "ppo_used": False,
                    "profile_specific_tuning": False,
                    "active_config_overwritten": False,
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
        write_csv_rows(output / "candidate_execution_failure_rows.csv", [], fieldnames=m2737.FAILURE_FIELDNAMES)
        write_json(output / "run_state.json", {"complete": True, "accounted_count": len(rows)})
        return {
            "result_class": "engineering_controller_route_a_post_negative_diagnostic_source_diverse_bounded_candidate_execution_pass",
            "all_selected_metrics_finite": True,
        }

    monkeypatch.setattr(m2737, "run_candidate_execution", fake_execution)
    summary = m2737.run_post_negative_source_diverse_bounded_execution_preflight(
        m2734_dir=tmp_path / "m2734",
        m2736_design=design_doc,
        m2693_execution_rows=m2693_rows,
        m2716_execution_rows=m2716_rows,
        executable_specs=specs_path,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["candidate_count"] == 18
    assert summary["resolved_candidate_count"] == 18
    assert summary["m2693_candidate_count"] == 9
    assert summary["m2716_candidate_count"] == 9
    assert summary["candidate_execution_row_count"] == 18
    assert summary["candidate_execution_failure_row_count"] == 0
    assert summary["negative_context_guard_row_count"] == 31
    assert summary["blocked_surface_guard_row_count"] == 12
    assert summary["source_family_aggregate_row_count"] == 2
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["m2728_negative_context_execution"] is False
    assert summary["same_surface_m2728_repair_execution"] is False
    assert summary["protected_blocker_execution"] is False
    assert summary["hf3_blocker_execution"] is False
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    resolution_rows = _read_csv(output_dir / "execution_candidate_resolution_rows.csv")
    assert len(resolution_rows) == 18
    assert {row["resolution_status"] for row in resolution_rows} == {"resolved_to_current_m1690_workload"}
    assert {row["execution_admitted"] for row in resolution_rows} == {"True"}
    assert {row["profile_name"] for row in resolution_rows} == {"L3_online_gru"}

    negative_guard_rows = _read_csv(output_dir / "negative_context_guard_rows.csv")
    blocked_guard_rows = _read_csv(output_dir / "blocked_surface_guard_rows.csv")
    assert {row["execution_run"] for row in negative_guard_rows + blocked_guard_rows} == {"False"}
    assert {row["execution_admitted"] for row in negative_guard_rows + blocked_guard_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in negative_guard_rows + blocked_guard_rows} == {"False"}

    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    blocked_claims = [row for row in claim_rows if row["allowed_in_m2737"] == "False"]
    assert blocked_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
