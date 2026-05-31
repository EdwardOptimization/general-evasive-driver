from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_json
from autodrift.config import env_config_to_dict
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight import (
    run_outcome_supported_decisive_reset_validation_preflight,
)


def _spec(index: int) -> dict[str, object]:
    env_config = env_config_for_hook_spec(
        source_family="t4_staged_warmup_capability",
        capability_pair="routing_smoke_proxy",
        reveal_step=60 + index,
    )
    family = "T2_same_current_different_older_history" if index else "T1_reactive_active_safety"
    return {
        "task_source_id": f"m2066-test-{index}",
        "candidate_id": f"osd_v0_test_{index:04d}",
        "candidate_set_id": "paper_route_outcome_supported_decisive_task_candidates_v0",
        "branch_id": "paper_route_outcome_supported_decisive_task_distribution",
        "panel_task_family": family,
        "source_split": "public_debug",
        "source_kind": "same_current_brake_authority_older_history" if index else "ordinary_reactive_stable_aes",
        "source_edge": "edge",
        "window_tag": "window",
        "source_reference": f"osd_v0_test_{index:04d}",
        "task_role_semantics": "test_role",
        "obstacle_distance_band": "medium",
        "road_width_band": "nominal",
        "curvature_band": "moderate",
        "dynamics_band": "mixed_mu",
        "initial_speed_band": "nominal",
        "same_current_constraint": bool(index),
        "history_intervention_candidate": bool(index),
        "warmup_mode": "none",
        "warmup_duration_seconds": 0.0,
        "obstacle_reveal_delay_seconds": 0.0,
        "recent_window_seconds": 0.0,
        "older_history_offset_seconds": 0.0,
        "diagnostic_delay_seconds": 0.0,
        "terminal_margin_bucket": "",
        "materialization_semantics": "smoke_proxy",
        "proxy_template_family": "t4_staged_warmup_capability",
        "generated_source_row": True,
        "paper_validity_claim": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "env_config": env_config_to_dict(env_config),
    }


def _two_spec_payload(tmp_path: Path) -> Path:
    specs = [_spec(0), _spec(1)]
    specs_path = tmp_path / "two_specs.json"
    write_json(specs_path, {"protocol": "test", "executable_task_specs": specs})
    return specs_path


def test_outcome_supported_decisive_reset_validation_preserves_metadata(tmp_path: Path) -> None:
    output_dir = tmp_path / "reset"

    summary = run_outcome_supported_decisive_reset_validation_preflight(
        executable_task_specs_path=_two_spec_payload(tmp_path),
        output_dir=output_dir,
        eval_seed_base=206600,
        target_spec_count=2,
        expected_observation_dim=72,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "outcome_supported_decisive_reset_validation_preflight_pass"
    assert summary["reset_attempt_count"] == 2
    assert summary["reset_success_count"] == 2
    assert summary["reset_failure_count"] == 0
    assert summary["observation_finite_count"] == 2
    assert summary["observation_dimension_failure_count"] == 0
    assert summary["obstacle_initialized_count"] == 2
    assert summary["contract_violation_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["family_quota_pass"] is True
    assert summary["split_quota_pass"] is True
    assert summary["difficulty_axis_coverage_pass"] is True
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is True
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert read_json(output_dir / "summary.json")["next_blocker"] == "next-audit"

    reset_rows = (output_dir / "reset_rows.csv").read_text(encoding="utf-8")
    assert "candidate_id" in reset_rows
    assert "obstacle_distance_band" in reset_rows
    assert "paper_validity_claim" in reset_rows


def test_outcome_supported_decisive_reset_validation_fails_on_missing_required_metadata(tmp_path: Path) -> None:
    specs_path = _two_spec_payload(tmp_path)
    payload = read_json(specs_path)
    payload["executable_task_specs"][0]["candidate_id"] = ""
    write_json(specs_path, payload)

    summary = run_outcome_supported_decisive_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=tmp_path / "bad",
        eval_seed_base=206600,
        target_spec_count=2,
        expected_observation_dim=72,
    )

    assert summary["result_class"] == "outcome_supported_decisive_reset_validation_preflight_fail"
    assert summary["metadata_missing_count"] == 1
