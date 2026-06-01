from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.paper_route_controlled_routing_smoke_measured_runner import metadata_missing_rows
from autodrift.paper_route_outcome_supported_decisive_public_gate_core_measured_execution_repair import (
    run_measured_execution_repair,
)


def _spec(index: int) -> dict[str, object]:
    env_config = env_config_to_dict(
        env_config_for_hook_spec(
            source_family="t4_staged_warmup_capability",
            capability_pair="routing_smoke_proxy",
            reveal_step=60 + index,
        )
    )
    return {
        "task_source_id": f"m2104-test-{index}",
        "panel_source_id": f"osd_v0_test_{index:04d}",
        "candidate_id": f"osd_v0_test_{index:04d}",
        "source_reference": f"osd_v0_test_{index:04d}",
        "task_role_semantics": "active_diagnostic_warmup_before_obstacle_reveal",
        "panel_task_family": "T3_active_diagnostic_warmup",
        "source_split": "public_gate",
        "source_origin": "m2060_no_rollout_outcome_supported_decisive_generator",
        "source_kind": "warmup_yaw_authority_probe",
        "source_edge": "edge",
        "window_tag": "window",
        "materialization_semantics": "smoke_proxy",
        "proxy_template_family": "t4_staged_warmup_capability",
        "generated_source_row": True,
        "paper_validity_claim": False,
        "env_config": env_config,
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    specs = [_spec(0), _spec(1)]
    workloads = []
    for spec_index in range(2):
        for profile_index in range(2):
            spec = specs[spec_index]
            workloads.append(
                {
                    "workload_id": f"m2104-test-{spec_index}::P{profile_index}",
                    "task_source_id": spec["task_source_id"],
                    "panel_source_id": spec["panel_source_id"],
                    "candidate_id": spec["candidate_id"],
                    "panel_task_family": spec["panel_task_family"],
                    "source_split": spec["source_split"],
                    "source_origin": spec["source_origin"],
                    "source_kind": spec["source_kind"],
                    "source_edge": spec["source_edge"],
                    "window_tag": spec["window_tag"],
                    "source_reference": spec["source_reference"],
                    "materialization_semantics": spec["materialization_semantics"],
                    "proxy_template_family": spec["proxy_template_family"],
                    "generated_source_row": spec["generated_source_row"],
                    "paper_validity_claim": spec["paper_validity_claim"],
                    "profile_name": f"P{profile_index}",
                    "profile_config_path": f"configs/P{profile_index}.json",
                    "checkpoint_path": f"checkpoints/P{profile_index}.pt",
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    reset_rows = [
        {
            "task_source_id": "m2104-test-0",
            "eval_seed": "101",
            "reset_success": "True",
            "reset_sampled_obstacle_label": "drift_required",
        },
        {
            "task_source_id": "m2104-test-1",
            "eval_seed": "202",
            "reset_success": "True",
            "reset_sampled_obstacle_label": "unavoidable",
        },
    ]
    failure_rows = [
        {
            "workload_id": "m2104-test-1::P0",
            "task_source_id": "m2104-test-1",
            "profile_name": "P0",
            "error_type": "RuntimeError",
            "error_message": "failed to sample",
        }
    ]
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    reset_path = tmp_path / "reset_rows.csv"
    failure_path = tmp_path / "failure_rows.csv"
    write_json(specs_path, {"executable_task_specs": specs})
    write_csv_rows(workload_path, workloads)
    write_csv_rows(reset_path, reset_rows)
    write_csv_rows(failure_path, failure_rows)
    return specs_path, workload_path, reset_path, failure_path


def test_measured_execution_repair_fills_metadata_and_seed_overrides(tmp_path: Path) -> None:
    specs_path, workload_path, reset_path, failure_path = _inputs(tmp_path)

    summary = run_measured_execution_repair(
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        reset_rows_path=reset_path,
        failure_rows_path=failure_path,
        output_dir=tmp_path / "out",
        target_spec_count=2,
        target_workload_count=4,
        target_profile_count=2,
        target_eval_seed_override_count=1,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "public_gate_core_measured_execution_repair_pass"
    assert summary["metadata_missing_count"] == 0
    assert summary["validation_failure_count"] == 0
    assert summary["eval_seed_override_count"] == 1
    assert summary["env_config_changed_count"] == 0
    assert summary["environment_rollout_started"] is False

    payload = read_json(tmp_path / "out" / "public_gate_core_measured_repaired_executable_task_specs.json")
    workload_rows = [
        row
        for row in csv.DictReader(
            (tmp_path / "out" / "public_gate_core_measured_repaired_workload.csv").open(newline="", encoding="utf-8")
        )
    ]
    assert metadata_missing_rows(executable_specs=payload["executable_task_specs"], workload_rows=workload_rows) == []
    override_rows = [row for row in workload_rows if row["eval_seed_override"]]
    assert override_rows[0]["workload_id"] == "m2104-test-1::P0"
    assert override_rows[0]["eval_seed_override"] == "202"
