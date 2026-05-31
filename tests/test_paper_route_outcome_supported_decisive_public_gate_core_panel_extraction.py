from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.paper_route_outcome_supported_decisive_public_gate_core_panel_extraction import (
    run_public_gate_core_panel_extraction,
)


def _spec(index: int, *, source_split: str = "public_debug") -> dict[str, object]:
    env_config = env_config_to_dict(
        env_config_for_hook_spec(
            source_family="t4_staged_warmup_capability",
            capability_pair="routing_smoke_proxy",
            reveal_step=60 + index,
        )
    )
    return {
        "task_source_id": f"m2094-test-{index}",
        "candidate_id": f"osd_v0_test_{index:04d}",
        "candidate_set_id": "paper_route_outcome_supported_decisive_task_candidates_v0",
        "branch_id": "paper_route_outcome_supported_decisive_task_distribution",
        "panel_task_family": "T3_active_diagnostic_warmup",
        "source_split": source_split,
        "source_kind": "warmup_yaw_authority_probe",
        "source_edge": "edge",
        "window_tag": "window",
        "source_reference": f"osd_v0_test_{index:04d}",
        "task_role_semantics": "reactive_evasive_driving_current_response_allowed",
        "obstacle_distance_band": "medium",
        "road_width_band": "tight",
        "curvature_band": "straight_or_low",
        "dynamics_band": "mixed_mu",
        "initial_speed_band": "high",
        "same_current_constraint": False,
        "history_intervention_candidate": False,
        "warmup_mode": "none",
        "warmup_duration_seconds": 0.0,
        "obstacle_reveal_delay_seconds": 0.0,
        "recent_window_seconds": 0.0,
        "older_history_offset_seconds": 0.0,
        "diagnostic_delay_seconds": 0.0,
        "terminal_margin_bucket": "",
        "materialization_semantics": "smoke_proxy",
        "proxy_template_family": "t5_near_boundary_warmup",
        "generated_source_row": True,
        "paper_validity_claim": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "env_config": env_config,
    }


def _specs_path(tmp_path: Path) -> Path:
    specs = [
        _spec(0, source_split="public_gate"),
        _spec(1, source_split="public_gate"),
        _spec(2, source_split="public_debug"),
        _spec(3, source_split="public_debug"),
    ]
    path = tmp_path / "specs.json"
    write_json(path, {"protocol": "test", "executable_task_specs": specs})
    return path


def _reset_rows_path(tmp_path: Path) -> Path:
    rows = [
        {"task_source_id": "m2094-test-0", "eval_seed": 10, "reset_success": True},
        {"task_source_id": "m2094-test-1", "eval_seed": 11, "reset_success": True},
        {"task_source_id": "m2094-test-2", "eval_seed": 12, "reset_success": True},
        {"task_source_id": "m2094-test-3", "eval_seed": 13, "reset_success": False},
    ]
    path = tmp_path / "reset_rows.csv"
    write_csv_rows(path, rows, ["task_source_id", "eval_seed", "reset_success"])
    return path


def _reset_failure_rows_path(tmp_path: Path) -> Path:
    rows = [{"task_source_id": "m2094-test-3", "eval_seed": 13, "reset_success": False}]
    path = tmp_path / "reset_failure_rows.csv"
    write_csv_rows(path, rows, ["task_source_id", "eval_seed", "reset_success"])
    return path


def test_public_gate_core_panel_extraction_keeps_only_public_gate_success_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "public_gate_core"

    summary = run_public_gate_core_panel_extraction(
        reset_valid_core_executable_task_specs_path=_specs_path(tmp_path),
        reset_rows_path=_reset_rows_path(tmp_path),
        reset_failure_rows_path=_reset_failure_rows_path(tmp_path),
        output_dir=output_dir,
        target_input_spec_count=4,
        target_public_gate_core_spec_count=2,
        target_excluded_spec_count=2,
        target_dynamics_counts={"mixed_mu": 2},
        target_axis_count_min=2,
        target_axis_count_max=2,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "outcome_supported_decisive_public_gate_core_panel_extraction_pass"
    assert summary["public_gate_core_executable_spec_count"] == 2
    assert summary["excluded_spec_count"] == 2
    assert summary["public_gate_included_count"] == 2
    assert summary["public_gate_excluded_count"] == 0
    assert summary["public_debug_included_count"] == 0
    assert summary["env_config_changed_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["policy_action_executed"] is False

    payload = read_json(output_dir / "public_gate_core_executable_task_specs.json")
    task_ids = {row["task_source_id"] for row in payload["executable_task_specs"]}
    assert task_ids == {"m2094-test-0", "m2094-test-1"}
