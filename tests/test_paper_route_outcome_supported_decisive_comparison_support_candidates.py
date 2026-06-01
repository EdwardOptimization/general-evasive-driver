from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_outcome_supported_decisive_comparison_support_candidates import (
    INTENT_TARGETS,
    build_candidates,
    generate_comparison_support_candidates,
    summarize_candidates,
)


def test_comparison_support_candidate_generator_writes_expected_quotas(tmp_path: Path) -> None:
    output = tmp_path / "candidates.json"

    payload = generate_comparison_support_candidates(output_path=output, next_blocker="next-audit")

    assert payload["result_class"] == "comparison_support_candidate_generation_pass"
    assert payload["candidate_count"] == 240
    assert payload["intent_counts"] == INTENT_TARGETS
    assert payload["quota_pass"] is True
    assert payload["duplicate_candidate_id_count"] == 0
    assert payload["paper_validity_claim_true_count"] == 0
    assert payload["profile_specific_tuning_true_count"] == 0
    assert payload["actor_input_forbidden_key_count"] == 0
    assert payload["guardrail_violation_count"] == 0
    assert payload["environment_reset_started"] is False
    assert payload["environment_rollout_started"] is False
    assert payload["policy_action_executed"] is False
    assert payload["controller_family_ranking_claim_made"] is False
    assert payload["paper_level_claim_made"] is False
    assert payload["level3_self_id_claim_made"] is False
    assert all(row["paper_validity_claim"] is False for row in payload["candidates"])
    assert all(row["profile_specific_tuning"] is False for row in payload["candidates"])

    persisted = read_json(output)
    assert persisted["next_blocker"] == "next-audit"
    assert persisted["candidate_count"] == 240


def test_comparison_support_candidate_generator_has_required_intent_fields() -> None:
    candidates = build_candidates()

    assert {row["comparison_support_intent"] for row in candidates} == set(INTENT_TARGETS)
    assert all(row["scenario_redesign_branch"] for row in candidates)
    assert all(row["target_support_tier"] for row in candidates)
    assert all(row["difficulty_axis"] for row in candidates)
    assert all(row["materialization_semantics"] == "comparison_support_smoke_proxy" for row in candidates)
    assert all(row["generated_source_row"] is True for row in candidates)


def test_comparison_support_candidate_guardrail_detects_tamper() -> None:
    candidates = build_candidates()
    candidates[0]["paper_validity_claim"] = True
    candidates[1]["actor_input_fields"].append("mu")

    payload = summarize_candidates(candidates=candidates)

    assert payload["result_class"] == "comparison_support_candidate_generation_incomplete_or_fail"
    assert payload["paper_validity_claim_true_count"] == 1
    assert payload["actor_input_forbidden_key_count"] == 1
