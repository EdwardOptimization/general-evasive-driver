import pytest

from autodrift.decisive_history_rollout_candidates import (
    RolloutCandidateMeasurement,
    action_sequence_divergence,
    current_frame_distance,
    history_window_distance,
    materialize_candidate,
    run_rollout_candidate_scaffold_smoke,
)


def test_distance_helpers_are_normalized_and_shape_checked():
    assert current_frame_distance([0.0, 1.0], [0.0, 2.0]) == pytest.approx(1.0 / 2.0**0.5)
    assert history_window_distance([[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [2.0, 1.0]]) == pytest.approx(0.5)
    assert action_sequence_divergence([[0.0, 0.0, 0.0]], [[0.3, 0.4, 0.0]]) == pytest.approx(0.5 / 3.0**0.5)
    with pytest.raises(ValueError, match="distance shapes differ"):
        current_frame_distance([0.0], [0.0, 1.0])


def test_materialize_candidate_accepts_measured_t4_candidate():
    measurement = RolloutCandidateMeasurement(
        task_family="T4",
        candidate_id="good",
        seed=1,
        source_family="t4",
        capability_pair="a|b",
        reveal_step=10,
        decision_step=20,
        geometry_key="g",
        current_distance=0.02,
        recent_window_distance=0.03,
        older_history_distance=0.20,
        normal_margin=0.08,
        action_divergence=0.05,
        intervention_margins={"wrong_history": 0.01},
    )

    result = materialize_candidate(measurement)

    assert result.accepted is True
    assert result.candidate is not None
    assert result.rejection_reasons == ()


def test_materialize_candidate_rejects_reset_only_source():
    measurement = RolloutCandidateMeasurement(
        task_family="T4",
        candidate_id="reset-only",
        seed=1,
        source_family="t4",
        capability_pair="a|b",
        reveal_step=10,
        decision_step=20,
        geometry_key="g",
        current_distance=0.02,
        recent_window_distance=0.03,
        older_history_distance=0.20,
        normal_margin=0.08,
        action_divergence=0.05,
        intervention_margins={"wrong_history": 0.01},
        measured_from_rollout=False,
        reset_only_source=True,
    )

    result = materialize_candidate(measurement)

    assert result.accepted is False
    assert result.candidate is None
    assert "not_measured_from_rollout" in result.rejection_reasons
    assert "reset_only_source" in result.rejection_reasons


def test_materialize_candidate_rejects_contract_violation():
    measurement = RolloutCandidateMeasurement(
        task_family="T5",
        candidate_id="leaky",
        seed=1,
        source_family="t5",
        capability_pair="a|b",
        reveal_step=10,
        decision_step=20,
        geometry_key="g",
        current_distance=0.02,
        recent_window_distance=0.03,
        older_history_distance=0.20,
        normal_margin=0.01,
        action_divergence=0.05,
        intervention_margins={"wrong_history": -0.02},
        labels_enter_actor_input=True,
    )

    result = materialize_candidate(measurement)

    assert result.accepted is False
    assert "labels_enter_actor_input" in result.rejection_reasons


def test_rollout_candidate_scaffold_smoke_writes_guarded_artifacts(tmp_path):
    summary = run_rollout_candidate_scaffold_smoke(tmp_path / "rollout-candidates")

    assert summary["result_class"] == "decisive_history_rollout_candidate_scaffold_smoke"
    assert summary["measurement_count"] == 3
    assert summary["materialized_candidate_count"] == 2
    assert summary["rejected_count"] == 1
    assert summary["accepted_t4_count"] == 1
    assert summary["accepted_t5_count"] == 1
    assert summary["candidate_materialized_from_reset_only"] is False
    assert summary["labels_enter_actor_input"] is False
    assert summary["training_started"] is False
    assert summary["replay_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["private_holdout_used"] is False
    assert summary["actor_input_contract_changed"] is False
    assert summary["training_corpus_exported"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["harness"]["accepted_count"] == 2
    assert (tmp_path / "rollout-candidates" / "measurement_rows.csv").exists()
    assert (tmp_path / "rollout-candidates" / "materialized_candidate_rows.csv").exists()
    assert (tmp_path / "rollout-candidates" / "summary.json").exists()
