from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_task_source_mapping_preflight import (
    infer_task_family,
    mapping_key_violations,
    run_mapping_preflight,
)


def test_infer_task_family_uses_explicit_then_terminal_names() -> None:
    assert infer_task_family(["actuator_delay_step"], "T4") == "T4"
    assert infer_task_family(["capability_step_down", "t5_near_boundary_warmup"]) == "T5"
    assert infer_task_family(["capability_step_up", "actuator_delay_step"]) == "T4"


def test_mapping_key_violations_rejects_hidden_or_action_target_keys() -> None:
    violations = mapping_key_violations(
        [
            {
                "mapping_id": "bad",
                "preferred_action_target": [0.1, 0.0, 0.0],
            }
        ]
    )

    assert violations == ["bad::preferred_action_target"]


def test_run_mapping_preflight_writes_metadata_only_artifacts(tmp_path: Path) -> None:
    summary = run_mapping_preflight(output_dir=tmp_path)

    mapping = read_json(tmp_path / "task_source_mapping.json")
    persisted_summary = read_json(tmp_path / "summary.json")

    assert summary["passes_public_smoke_gates"] is True
    assert persisted_summary["candidate_source_family_count"] >= 5
    assert persisted_summary["candidate_task_family_count"] >= 2
    assert persisted_summary["candidate_edge_count"] >= 8
    assert persisted_summary["guardrail_violation_count"] == 0
    assert persisted_summary["training_started"] is False
    assert persisted_summary["environment_rollout_started"] is False
    assert mapping["m1615_use_policy"] == "diagnostic_metadata_only_no_hidden_tensor_or_action_targets"
    assert mapping["key_violation_count"] == 0
    assert "L3_reset_control_corrected" in mapping["control_profile_requirements"]
    assert all(
        "preferred_action" not in key and "hidden_tensor" not in key
        for row in mapping["candidate_rows"]
        for key in row
    )
