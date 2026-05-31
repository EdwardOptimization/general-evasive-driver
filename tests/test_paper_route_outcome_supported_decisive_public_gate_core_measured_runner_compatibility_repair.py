from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair import (
    run_measured_runner_compatibility_repair,
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
        "task_source_id": f"m2098-test-{index}",
        "candidate_id": f"osd_v0_test_{index:04d}",
        "source_reference": f"osd_v0_test_{index:04d}",
        "panel_task_family": "T3_active_diagnostic_warmup",
        "source_split": "public_gate",
        "source_kind": "warmup_yaw_authority_probe",
        "source_edge": "edge",
        "window_tag": "window",
        "materialization_semantics": "smoke_proxy",
        "proxy_template_family": "t4_staged_warmup_capability",
        "generated_source_row": True,
        "paper_validity_claim": False,
        "env_config": env_config,
    }


def _specs_path(tmp_path: Path) -> Path:
    path = tmp_path / "specs.json"
    write_json(path, {"protocol": "test", "executable_task_specs": [_spec(0), _spec(1)]})
    return path


def _workload_path(tmp_path: Path) -> Path:
    rows = []
    for spec_index in range(2):
        for profile_index in range(2):
            rows.append(
                {
                    "workload_id": f"m2098-test-{spec_index}::P{profile_index}",
                    "task_source_id": f"m2098-test-{spec_index}",
                    "candidate_id": f"osd_v0_test_{spec_index:04d}",
                    "panel_task_family": "T3_active_diagnostic_warmup",
                    "source_split": "public_gate",
                    "profile_name": f"P{profile_index}",
                    "profile_config_path": f"configs/P{profile_index}.json",
                    "checkpoint_path": f"checkpoints/P{profile_index}.pt",
                    "source_kind": "warmup_yaw_authority_probe",
                    "source_edge": "edge",
                    "window_tag": "window",
                    "materialization_semantics": "smoke_proxy",
                    "paper_validity_claim": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "finite_window_vs_gru_conclusion_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    path = tmp_path / "workload.csv"
    write_csv_rows(path, rows)
    return path


def test_measured_runner_compatibility_repair_fills_required_metadata(tmp_path: Path) -> None:
    output_dir = tmp_path / "repair"

    summary = run_measured_runner_compatibility_repair(
        public_gate_core_executable_task_specs_path=_specs_path(tmp_path),
        public_gate_core_workload_path=_workload_path(tmp_path),
        output_dir=output_dir,
        target_spec_count=2,
        target_workload_count=4,
        target_profile_count=2,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "public_gate_core_measured_runner_compatibility_repair_pass"
    assert summary["compatible_spec_count"] == 2
    assert summary["compatible_workload_count"] == 4
    assert summary["profile_count"] == 2
    assert summary["spec_panel_source_id_missing_count"] == 0
    assert summary["workload_proxy_template_family_missing_count"] == 0
    assert summary["workload_generated_source_row_missing_count"] == 0
    assert summary["measured_runner_validation_failure_count"] == 0
    assert summary["env_config_changed_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False

    payload = read_json(output_dir / "public_gate_core_measured_compatible_executable_task_specs.json")
    repaired_spec = payload["executable_task_specs"][0]
    assert repaired_spec["panel_source_id"] == repaired_spec["source_reference"]
