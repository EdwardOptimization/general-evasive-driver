from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction import (
    run_reset_valid_core_panel_reduction,
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
        "task_source_id": f"m2088-test-{index}",
        "candidate_id": f"osd_v0_test_{index:04d}",
        "candidate_set_id": "paper_route_outcome_supported_decisive_task_candidates_v0",
        "branch_id": "paper_route_outcome_supported_decisive_task_distribution",
        "panel_task_family": "T1_reactive_active_safety",
        "source_split": source_split,
        "source_kind": "ordinary_reactive_stable_aes",
        "source_edge": "edge",
        "window_tag": "window",
        "source_reference": f"osd_v0_test_{index:04d}",
        "task_role_semantics": "reactive_evasive_driving_current_response_allowed",
        "obstacle_distance_band": "early",
        "road_width_band": "nominal",
        "curvature_band": "moderate",
        "dynamics_band": "mixed_mu",
        "initial_speed_band": "nominal",
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
        _spec(1, source_split="public_debug"),
        _spec(2, source_split="public_debug"),
    ]
    path = tmp_path / "specs.json"
    write_json(path, {"protocol": "test", "executable_task_specs": specs})
    return path


def _reset_rows_path(tmp_path: Path) -> Path:
    rows = [
        {"task_source_id": "m2088-test-0", "eval_seed": 10, "reset_success": True},
        {"task_source_id": "m2088-test-1", "eval_seed": 11, "reset_success": True},
        {"task_source_id": "m2088-test-2", "eval_seed": 12, "reset_success": False},
    ]
    path = tmp_path / "reset_rows.csv"
    write_csv_rows(path, rows, ["task_source_id", "eval_seed", "reset_success"])
    return path


def _reset_failure_rows_path(tmp_path: Path) -> Path:
    rows = [{"task_source_id": "m2088-test-2", "eval_seed": 12, "reset_success": False}]
    path = tmp_path / "reset_failure_rows.csv"
    write_csv_rows(path, rows, ["task_source_id", "eval_seed", "reset_success"])
    return path


def test_reset_valid_core_panel_reduction_preserves_public_gate_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "reduced"

    summary = run_reset_valid_core_panel_reduction(
        density_aware_executable_task_specs_path=_specs_path(tmp_path),
        reset_rows_path=_reset_rows_path(tmp_path),
        reset_failure_rows_path=_reset_failure_rows_path(tmp_path),
        output_dir=output_dir,
        target_input_spec_count=3,
        target_reduced_spec_count=2,
        target_excluded_spec_count=1,
        target_public_gate_preserved_count=1,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "outcome_supported_decisive_reset_valid_core_panel_reduction_pass"
    assert summary["reduced_executable_spec_count"] == 2
    assert summary["excluded_spec_count"] == 1
    assert summary["public_gate_preserved_count"] == 1
    assert summary["public_gate_excluded_count"] == 0
    assert summary["env_config_changed_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["policy_action_executed"] is False

    payload = read_json(output_dir / "reset_valid_core_executable_task_specs.json")
    task_ids = {row["task_source_id"] for row in payload["executable_task_specs"]}
    assert task_ids == {"m2088-test-0", "m2088-test-1"}
