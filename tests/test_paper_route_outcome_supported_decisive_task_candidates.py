from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_outcome_supported_decisive_task_candidates import (
    DIFFICULTY_AXES,
    FAMILY_TARGETS,
    SPLIT_TARGETS,
    build_candidates,
    generate_outcome_supported_decisive_task_candidates,
    summarize_candidates,
)


def test_candidate_generator_writes_registered_quotas_and_guardrails(tmp_path: Path) -> None:
    output_path = tmp_path / "candidates.json"

    payload = generate_outcome_supported_decisive_task_candidates(
        output_path=output_path,
        next_blocker="next-audit",
    )

    assert payload["result_class"] == "outcome_supported_decisive_task_candidate_generation_pass"
    assert payload["candidate_count"] == 240
    assert payload["family_counts"] == FAMILY_TARGETS
    assert payload["source_split_counts"] == SPLIT_TARGETS
    assert payload["quota_pass"] is True
    assert payload["difficulty_axis_coverage_pass"] is True
    assert payload["guardrail_violation_count"] == 0
    assert payload["actor_input_forbidden_key_count"] == 0
    assert payload["paper_validity_claim_true_count"] == 0
    assert payload["environment_reset_started"] is False
    assert payload["environment_rollout_started"] is False
    assert payload["policy_action_executed"] is False
    assert payload["controller_family_ranking_claim_made"] is False
    assert payload["finite_window_vs_gru_conclusion_made"] is False
    assert payload["paper_level_claim_made"] is False
    assert payload["level3_self_id_claim_made"] is False

    candidate_ids = [row["candidate_id"] for row in payload["candidates"]]
    assert len(candidate_ids) == len(set(candidate_ids))
    assert all(row["materialization_semantics"] == "smoke_proxy" for row in payload["candidates"])
    assert all(row["paper_validity_claim"] is False for row in payload["candidates"])
    assert all(row["profile_specific_tuning"] is False for row in payload["candidates"])

    persisted = read_json(output_path)
    assert persisted["next_blocker"] == "next-audit"
    assert persisted["candidate_count"] == 240


def test_candidate_axis_coverage_is_complete_per_family() -> None:
    payload = summarize_candidates(candidates=build_candidates())

    for family in FAMILY_TARGETS:
        for axis, expected_values in DIFFICULTY_AXES.items():
            assert set(payload["difficulty_axis_coverage"][family][axis]) == set(expected_values)
        assert payload["source_diversity"][family]["source_kind_count"] >= 6
        assert payload["source_diversity"][family]["max_single_source_kind_share"] <= 0.20


def test_candidate_guardrail_detects_paper_claim_tamper() -> None:
    candidates = build_candidates()
    candidates[0]["paper_validity_claim"] = True

    payload = summarize_candidates(candidates=candidates)

    assert payload["result_class"] == "outcome_supported_decisive_task_candidate_generation_incomplete_or_fail"
    assert payload["paper_validity_claim_true_count"] == 1
    assert payload["guardrail_violation_count"] == 1
