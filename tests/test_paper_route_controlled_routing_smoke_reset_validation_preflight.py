from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_json
from autodrift.config import env_config_to_dict
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.paper_route_controlled_routing_smoke_reset_validation_preflight import (
    run_controlled_routing_smoke_reset_validation_preflight,
)


def _spec(index: int, *, generated: bool, paper_validity_claim: object = "false") -> dict[str, object]:
    env_config = env_config_for_hook_spec(
        source_family="t4_staged_warmup_capability",
        capability_pair="routing_smoke_proxy",
        reveal_step=60 + index,
    )
    return {
        "task_source_id": f"m2036-test-{index}",
        "panel_source_id": f"panel-{index}",
        "panel_task_family": "T2_same_current_different_older_history" if generated else "T1_reactive_active_safety",
        "source_origin": "test",
        "source_kind": "same_current_brake_authority_older_history_proxy" if generated else "anchor_neighborhood",
        "source_edge": "edge",
        "window_tag": "window",
        "source_role_semantics": "role",
        "parent_feasibility_tier_id": "tier",
        "normalized_surface_variant": "surface",
        "sampled_obstacle_label": "label",
        "source_reference": f"ref-{index}",
        "materialization_semantics": "smoke_proxy",
        "proxy_template_family": "t4_staged_warmup_capability",
        "generated_source_row": generated,
        "paper_validity_claim": paper_validity_claim,
        "contract_checks": {
            "history_length_is_positive": True,
            "action_history_mode_full": True,
            "include_privileged_params_false": True,
            "wheel_observation_mode_none": True,
            "obstacle_relative_velocity_mode_zero": True,
        },
        "contract_violation_count": 0,
        "env_config": env_config_to_dict(env_config),
    }


def test_controlled_routing_smoke_reset_validation_preserves_metadata(tmp_path: Path) -> None:
    specs_path = tmp_path / "executable_task_specs.json"
    output_dir = tmp_path / "reset"
    write_json(
        specs_path,
        {
            "protocol": "test",
            "executable_task_specs": [_spec(0, generated=False), _spec(1, generated=True)],
        },
    )

    summary = run_controlled_routing_smoke_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=203600,
        target_spec_count=2,
        expected_observation_dim=72,
    )

    assert summary["result_class"] == "controlled_routing_smoke_reset_validation_preflight_pass"
    assert summary["reset_attempt_count"] == 2
    assert summary["reset_success_count"] == 2
    assert summary["metadata_missing_count"] == 0
    assert summary["contract_violation_count"] == 0
    assert summary["generated_proxy_quota_pass"] is True
    assert summary["guardrail_violation_count"] == 0
    with (output_dir / "reset_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[1]["panel_task_family"] == "T2_same_current_different_older_history"
    assert rows[1]["generated_source_row"] == "true"
    assert rows[1]["materialization_semantics"] == "smoke_proxy"
    assert rows[1]["paper_validity_claim"] == "false"


def test_controlled_routing_smoke_reset_validation_canonicalizes_generated_proxy_claim_keys(tmp_path: Path) -> None:
    specs_path = tmp_path / "executable_task_specs.json"
    output_dir = tmp_path / "reset"
    write_json(
        specs_path,
        {
            "protocol": "test",
            "executable_task_specs": [
                _spec(0, generated=False, paper_validity_claim="False"),
                _spec(1, generated=True, paper_validity_claim="False"),
            ],
        },
    )

    summary = run_controlled_routing_smoke_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=203600,
        target_spec_count=2,
        expected_observation_dim=72,
    )

    assert summary["result_class"] == "controlled_routing_smoke_reset_validation_preflight_pass"
    assert summary["expected_generated_proxy_counts"] == summary["generated_proxy_counts"]
    assert summary["generated_proxy_quota_pass"] is True
    assert summary["expected_generated_proxy_counts"] == {
        "generated=false|semantics=smoke_proxy|paper_claim=false": 1,
        "generated=true|semantics=smoke_proxy|paper_claim=false": 1,
    }
