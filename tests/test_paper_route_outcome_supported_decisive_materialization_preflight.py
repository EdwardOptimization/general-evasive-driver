from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_json
from autodrift.paper_route_outcome_supported_decisive_materialization_preflight import (
    run_materialization_preflight,
)
from autodrift.paper_route_outcome_supported_decisive_task_candidates import (
    FAMILY_TARGETS,
    SENTINEL_PROFILES,
    SPLIT_TARGETS,
    generate_outcome_supported_decisive_task_candidates,
)


def _candidate_artifact(tmp_path: Path) -> Path:
    path = tmp_path / "candidates.json"
    generate_outcome_supported_decisive_task_candidates(output_path=path, next_blocker="audit")
    return path


def test_materialization_preflight_writes_specs_and_sentinel_workload(tmp_path: Path) -> None:
    output_dir = tmp_path / "materialized"
    summary = run_materialization_preflight(
        candidates_path=_candidate_artifact(tmp_path),
        output_dir=output_dir,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "outcome_supported_decisive_materialization_preflight_pass"
    assert summary["executable_spec_count"] == 240
    assert summary["planned_sentinel_workload_count"] == 1200
    assert summary["sentinel_profile_count"] == 5
    assert summary["sentinel_profiles"] == list(SENTINEL_PROFILES)
    assert summary["family_counts"] == FAMILY_TARGETS
    assert summary["source_split_counts"] == SPLIT_TARGETS
    assert summary["difficulty_axis_coverage_pass"] is True
    assert summary["materialization_failure_count"] == 0
    assert summary["profile_missing_count"] == 0
    assert summary["contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    for artifact_name in (
        "executable_task_specs_json",
        "executable_task_specs_csv",
        "planned_sentinel_workload",
        "profile_artifacts",
        "family_axis_aggregate",
        "source_kind_aggregate",
        "claim_boundary",
    ):
        assert Path(summary["artifacts"][artifact_name]).exists()

    specs = read_json(output_dir / "executable_task_specs.json")["executable_task_specs"]
    assert len(specs) == 240
    assert all(spec["materialization_semantics"] == "smoke_proxy" for spec in specs)
    assert all(spec["paper_validity_claim"] is False for spec in specs)
    assert all(spec["profile_specific_tuning"] is False for spec in specs)
    assert all(spec["env_config"]["wheel_observation_mode"] == "none" for spec in specs)
    assert all(spec["env_config"]["obstacle_relative_velocity_mode"] == "zero" for spec in specs)

    assert read_json(output_dir / "summary.json")["sentinel_profiles"] == list(SENTINEL_PROFILES)


def test_materialization_preflight_fails_closed_on_invalid_candidate_claim(tmp_path: Path) -> None:
    candidates_path = _candidate_artifact(tmp_path)
    payload = read_json(candidates_path)
    payload["candidates"][0]["paper_validity_claim"] = True
    write_json(candidates_path, payload)

    summary = run_materialization_preflight(
        candidates_path=candidates_path,
        output_dir=tmp_path / "bad",
    )

    assert summary["result_class"] == "outcome_supported_decisive_materialization_preflight_partial"
    assert summary["executable_spec_count"] == 239
    assert summary["materialization_failure_count"] == 1
