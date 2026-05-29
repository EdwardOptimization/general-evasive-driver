import pytest

from autodrift.decisive_history_tasks import (
    DecisiveHistoryTaskCandidate,
    DecisiveHistoryThresholds,
    build_harness_summary,
    classify_candidate,
    matching_diagnostics_summary,
    run_harness_smoke,
    source_diversity_summary,
)


def test_t4_accepts_same_current_different_older_history_with_wrong_history_gap():
    candidate = DecisiveHistoryTaskCandidate(
        task_family="T4",
        candidate_id="t4",
        seed=1,
        capability_pair="low|high",
        reveal_step=10,
        decision_step=12,
        geometry_key="g",
        current_distance=0.01,
        recent_window_distance=0.02,
        older_history_distance=0.30,
        normal_margin=0.08,
        action_divergence=0.05,
        intervention_margins={"wrong_history": 0.02},
    )

    result = classify_candidate(candidate)

    assert result.accepted
    assert result.reasons == ()
    assert result.max_margin_gap == pytest.approx(0.06)


def test_t4_rejects_current_mismatch_and_actor_label_shortcut():
    candidate = DecisiveHistoryTaskCandidate(
        task_family="T4",
        candidate_id="t4-bad",
        seed=1,
        capability_pair="low|high",
        reveal_step=10,
        decision_step=12,
        geometry_key="g",
        current_distance=0.20,
        recent_window_distance=0.02,
        older_history_distance=0.30,
        normal_margin=0.08,
        action_divergence=0.05,
        labels_enter_actor_input=True,
        intervention_margins={"wrong_history": 0.02},
    )

    result = classify_candidate(candidate)

    assert not result.accepted
    assert "current_distance_too_large" in result.reasons
    assert "labels_enter_actor_input" in result.reasons


def test_t5_accepts_near_boundary_success_drop():
    candidate = DecisiveHistoryTaskCandidate(
        task_family="T5",
        candidate_id="t5",
        seed=2,
        capability_pair="brake_low|brake_high",
        reveal_step=20,
        decision_step=28,
        geometry_key="terminal",
        current_distance=0.04,
        recent_window_distance=0.04,
        older_history_distance=0.20,
        normal_margin=0.012,
        action_divergence=0.02,
        intervention_margins={"wrong_history": -0.01, "reset": 0.006},
    )

    result = classify_candidate(candidate)

    assert result.accepted
    assert "wrong_history" in result.success_drop_variants


def test_t5_rejects_when_normal_margin_is_not_near_boundary():
    candidate = DecisiveHistoryTaskCandidate(
        task_family="T5",
        candidate_id="t5-too-safe",
        seed=2,
        capability_pair="brake_low|brake_high",
        reveal_step=20,
        decision_step=28,
        geometry_key="terminal",
        current_distance=0.04,
        recent_window_distance=0.04,
        older_history_distance=0.20,
        normal_margin=0.20,
        intervention_margins={"wrong_history": 0.10},
    )

    result = classify_candidate(candidate)

    assert not result.accepted
    assert "normal_margin_above_near_pass_band" in result.reasons


def test_matching_and_source_diversity_summaries_are_public_diagnostics():
    rows = [
        DecisiveHistoryTaskCandidate(
            task_family="T4",
            candidate_id=f"c{i}",
            seed=i,
            capability_pair=f"pair{i % 2}",
            reveal_step=10 + i,
            decision_step=12 + i,
            geometry_key=f"g{i % 2}",
            source_key="shared" if i < 2 else f"source{i}",
            current_distance=0.01 * i,
            recent_window_distance=0.02,
            older_history_distance=0.20 + 0.01 * i,
            normal_margin=0.05,
            action_divergence=0.05,
            intervention_margins={"wrong_history": 0.0},
        )
        for i in range(4)
    ]

    matching = matching_diagnostics_summary(rows)
    diversity = source_diversity_summary(rows)

    assert matching["total_candidates"] == 4
    assert matching["current_distance_max"] == pytest.approx(0.03)
    assert diversity["unique_seeds"] == 4
    assert diversity["unique_source_keys"] == 3
    assert diversity["max_source_share"] == pytest.approx(0.5)


def test_build_harness_summary_and_smoke_do_not_start_training(tmp_path):
    summary = run_harness_smoke(tmp_path / "smoke")

    assert summary["candidate_count"] == 3
    assert summary["accepted_count"] == 2
    assert summary["accepted_t4_count"] == 1
    assert summary["accepted_t5_count"] == 1
    assert summary["training_started"] is False
    assert summary["replay_started"] is False
    assert summary["ppo_used"] is False
    assert summary["actor_input_contract_changed"] is False
    assert (tmp_path / "smoke" / "summary.json").exists()
    assert (tmp_path / "smoke" / "candidate_rows.csv").exists()

    stricter = build_harness_summary(
        [],
        thresholds=DecisiveHistoryThresholds(max_current_distance=0.01),
    )
    assert stricter["candidate_count"] == 0
    assert stricter["accepted_count"] == 0
