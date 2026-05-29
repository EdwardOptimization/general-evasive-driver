from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_task_source_generation_preflight import (
    TARGET_TOTAL_SPECS,
    key_violations,
    run_generation_preflight,
)
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES


def test_key_violations_recurses_into_nested_specs() -> None:
    violations = key_violations(
        [
            {
                "task_source_id": "bad",
                "mapping_lineage": {"action_target": [0.0, 0.0, 0.0]},
            }
        ]
    )

    assert violations == ["bad.mapping_lineage::action_target"]


def test_run_generation_preflight_writes_budgeted_specs(tmp_path: Path) -> None:
    summary = run_generation_preflight(output_dir=tmp_path)

    specs_payload = read_json(tmp_path / "task_source_specs.json")
    persisted_summary = read_json(tmp_path / "summary.json")

    assert summary["passes_public_smoke_gates"] is True
    assert persisted_summary["spec_count"] == TARGET_TOTAL_SPECS
    assert persisted_summary["all_caps_pass"] is True
    assert persisted_summary["hidden_action_target_key_violation_count"] == 0
    assert persisted_summary["guardrail_violation_count"] == 0
    assert persisted_summary["environment_rollout_started"] is False
    assert persisted_summary["training_started"] is False
    assert persisted_summary["all_controller_profiles_covered"] is True
    assert (tmp_path / "source_budget_summary.csv").exists()

    specs = specs_payload["task_source_specs"]
    assert len(specs) == TARGET_TOTAL_SPECS
    assert all(spec["controller_profiles_required"] == list(EXPECTED_PROFILE_NAMES) for spec in specs)
    assert all(spec["mapping_lineage"]["fresh_generation_required"] is True for spec in specs)
    assert all(spec["mapping_lineage"]["direct_benchmark_row"] is False for spec in specs)
