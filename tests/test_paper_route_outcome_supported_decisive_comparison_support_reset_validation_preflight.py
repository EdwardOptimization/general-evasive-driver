from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_json
from autodrift.paper_route_outcome_supported_decisive_comparison_support_candidates import build_candidates
from autodrift.paper_route_outcome_supported_decisive_comparison_support_materialization_preflight import (
    materialize_executable_specs,
)
from autodrift.paper_route_outcome_supported_decisive_comparison_support_reset_validation_preflight import (
    contract_row_for_spec,
    run_comparison_support_reset_validation_preflight,
)


def _write_specs(path: Path, count: int = 2) -> list[dict[str, object]]:
    candidates = build_candidates()[:count]
    specs, failures = materialize_executable_specs(candidates)
    assert len(specs) == count
    assert failures == []
    write_json(path, {"protocol": "test", "executable_task_specs": specs})
    return specs


def test_comparison_support_reset_validation_preflight_runs_reset_only(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    output_dir = tmp_path / "out"
    _write_specs(specs_path, count=2)

    summary = run_comparison_support_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=212100,
        target_spec_count=2,
        expected_observation_dim=72,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "comparison_support_reset_validation_preflight_pass"
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
    assert summary["intent_quota_pass"] is True
    assert summary["source_kind_quota_pass"] is True
    assert summary["proxy_template_quota_pass"] is True
    assert summary["generated_proxy_quota_pass"] is True
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


def test_comparison_support_contract_rejects_old_smoke_proxy_semantics(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    spec = _write_specs(specs_path, count=1)[0]
    assert contract_row_for_spec(spec)["contract_violation_count"] == 0

    old_semantics = dict(spec)
    old_semantics["materialization_semantics"] = "smoke_proxy"
    row = contract_row_for_spec(old_semantics)

    assert row["materialization_semantics_comparison_support_smoke_proxy"] is False
    assert row["contract_violation_count"] >= 1
