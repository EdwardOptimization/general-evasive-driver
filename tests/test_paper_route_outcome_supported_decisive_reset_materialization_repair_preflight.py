from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.paper_route_outcome_supported_decisive_reset_materialization_repair_preflight import (
    repair_warmup_gate,
    run_repair_preflight,
    zero_step_warmup_gate_invalid,
)


def _spec(index: int) -> dict[str, object]:
    env_config = env_config_to_dict(
        env_config_for_hook_spec(
            source_family="t4_staged_warmup_capability",
            capability_pair="routing_smoke_proxy",
            reveal_step=60 + index,
        )
    )
    env_config["warmup_gate"]["enabled"] = False
    env_config["warmup_gate"]["max_active_steps"] = 0
    env_config["obstacle"]["distance_range"] = [70.0, 70.0]
    env_config["obstacle"]["half_width_range"] = [1.25, 1.25]
    return {
        "task_source_id": f"m2070-test-{index}",
        "candidate_id": f"osd_v0_test_{index:04d}",
        "candidate_set_id": "paper_route_outcome_supported_decisive_task_candidates_v0",
        "branch_id": "paper_route_outcome_supported_decisive_task_distribution",
        "panel_task_family": "T1_reactive_active_safety",
        "source_split": "public_debug",
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


def _payload_path(tmp_path: Path) -> Path:
    specs = [_spec(0), _spec(1)]
    path = tmp_path / "specs.json"
    write_json(path, {"protocol": "test", "executable_task_specs": specs})
    return path


def _failure_rows_path(tmp_path: Path) -> Path:
    rows = [
        {
            "task_source_id": "m2070-test-0",
            "eval_seed": 207000,
            "error_type": "ValueError",
            "error_message": "warmup_gate max_active_steps must be positive",
        },
        {
            "task_source_id": "m2070-test-1",
            "eval_seed": 207001,
            "error_type": "RuntimeError",
            "error_message": "failed to sample an obstacle scenario matching the configured filters",
        },
    ]
    path = tmp_path / "failures.csv"
    write_csv_rows(path, rows, ["task_source_id", "eval_seed", "error_type", "error_message"])
    return path


def test_repair_warmup_gate_removes_zero_step_disabled_gate() -> None:
    spec = _spec(0)

    assert zero_step_warmup_gate_invalid(spec["env_config"])

    env_config, repair = repair_warmup_gate(spec)

    assert repair["warmup_gate_repaired"] is True
    assert repair["repaired_warmup_gate_enabled"] is False
    assert repair["repaired_warmup_gate_max_active_steps"] > 0
    assert zero_step_warmup_gate_invalid(env_config) is False


def test_repair_preflight_writes_repaired_specs_without_reset(tmp_path: Path) -> None:
    output_dir = tmp_path / "repair"

    summary = run_repair_preflight(
        executable_task_specs_path=_payload_path(tmp_path),
        reset_failure_rows_path=_failure_rows_path(tmp_path),
        output_dir=output_dir,
        next_blocker="next-audit",
    )

    assert summary["input_executable_spec_count"] == 2
    assert summary["repaired_executable_spec_count"] == 2
    assert summary["zero_step_warmup_gate_invalid_count_after"] == 0
    assert summary["scenario_filter_feasible_after_count"] == 2
    assert summary["scenario_filter_infeasible_after_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["policy_action_executed"] is False
    assert read_json(output_dir / "repaired_executable_task_specs.json")["executable_task_specs"]
