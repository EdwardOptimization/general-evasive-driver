from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_controlled_comparison_executable_spec_materialization as materialization
from autodrift.artifacts import read_json, write_json
from autodrift.paper_route_current_sim_controlled_comparison_reset_validation_preflight import (
    contract_row_for_spec,
    run_current_sim_reset_validation_preflight,
)


def _write_specs(path: Path, count: int = 2) -> list[dict[str, object]]:
    summary = materialization.materialize_executable_specs(output_dir=path.parent / "materialization")
    assert summary["result_class"] == "current_sim_controlled_comparison_executable_spec_materialization_pass"
    specs = read_json(path.parent / "materialization" / "executable_task_specs.json")["executable_task_specs"][:count]
    write_json(path, {"protocol": "test", "executable_task_specs": specs})
    return specs


def test_current_sim_reset_validation_preflight_runs_reset_only(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    output_dir = tmp_path / "out"
    _write_specs(specs_path, count=2)

    summary = run_current_sim_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=215300,
        target_spec_count=2,
        expected_observation_dim=72,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_reset_validation_preflight_pass"
    assert summary["input_executable_spec_count"] == 2
    assert summary["reset_attempt_count"] == 2
    assert summary["reset_success_count"] == 2
    assert summary["reset_failure_count"] == 0
    assert summary["observation_dimension_failure_count"] == 0
    assert summary["observation_finite_count"] == 2
    assert summary["obstacle_initialized_count"] == 2
    assert summary["contract_violation_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["forbidden_key_violation_count"] == 0
    assert summary["task_family_quota_pass"] is True
    assert summary["source_family_template_quota_pass"] is True
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is True
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    persisted = read_json(output_dir / "summary.json")
    assert persisted["next_blocker"] == "next-audit"
    assert (output_dir / "reset_rows.csv").exists()
    assert (output_dir / "reset_failure_rows.csv").exists()
    assert (output_dir / "contract_rows.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()
    assert (output_dir / "run_state.json").exists()


def test_current_sim_contract_rejects_wrong_materialization_semantics(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    spec = _write_specs(specs_path, count=1)[0]
    assert contract_row_for_spec(spec)["contract_violation_count"] == 0

    wrong_semantics = dict(spec)
    wrong_semantics["materialization_semantics"] = "comparison_support_smoke_proxy"
    row = contract_row_for_spec(wrong_semantics)

    assert row["materialization_semantics_current_sim_executable_spec_v0"] is False
    assert row["contract_violation_count"] >= 1


def test_current_sim_reset_validation_fails_closed_on_metadata_gap(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    specs = _write_specs(specs_path, count=1)
    broken = dict(specs[0])
    broken["task_family"] = ""
    write_json(specs_path, {"protocol": "test", "executable_task_specs": [broken]})

    summary = run_current_sim_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=tmp_path / "out",
        eval_seed_base=215300,
        target_spec_count=1,
        expected_observation_dim=72,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_reset_validation_preflight_fail"
    assert summary["metadata_missing_count"] == 1
