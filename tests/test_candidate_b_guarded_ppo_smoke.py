from autodrift.candidate_b_guarded_ppo_smoke import (
    classify_candidate_b_guarded_ppo,
    failure_types_for_guarded_ppo_result,
    next_blocker_for_guarded_ppo_result,
    training_metrics_path,
)


def test_guarded_ppo_classifier_requires_training_success() -> None:
    result = classify_candidate_b_guarded_ppo(
        actor_inputs_changed=False,
        ppo_returncode=1,
        training_metrics_finite=False,
        exact_retention_pass=False,
        proof_pass=False,
        source_diverse_pass=False,
        generalization_pass=False,
        behavior_pass=False,
        promoted=False,
        private_holdout_used=False,
    )

    assert result == "candidate_b_guarded_ppo_training_instability"
    assert failure_types_for_guarded_ppo_result(result) == ["training_instability"]


def test_guarded_ppo_classifier_routes_exact_regression_before_proof() -> None:
    result = classify_candidate_b_guarded_ppo(
        actor_inputs_changed=False,
        ppo_returncode=0,
        training_metrics_finite=True,
        exact_retention_pass=False,
        proof_pass=False,
        source_diverse_pass=False,
        generalization_pass=True,
        behavior_pass=True,
        promoted=False,
        private_holdout_used=False,
    )

    assert result == "candidate_b_guarded_ppo_exact_retention_regression"
    assert failure_types_for_guarded_ppo_result(result) == ["proof_washout"]
    assert next_blocker_for_guarded_ppo_result(result) == "candidate_b_guarded_ppo_exact_repair_projection_design"


def test_guarded_ppo_classifier_accepts_raw_candidate() -> None:
    result = classify_candidate_b_guarded_ppo(
        actor_inputs_changed=False,
        ppo_returncode=0,
        training_metrics_finite=True,
        exact_retention_pass=True,
        proof_pass=True,
        source_diverse_pass=True,
        generalization_pass=True,
        behavior_pass=True,
        promoted=False,
        private_holdout_used=False,
    )

    assert result == "candidate_b_guarded_ppo_raw_candidate"
    assert failure_types_for_guarded_ppo_result(result) == ["none"]
    assert next_blocker_for_guarded_ppo_result(result) == "candidate_b_guarded_ppo_raw_candidate_full_gate_design"


def test_training_metrics_path_prefers_train_metrics(tmp_path) -> None:
    (tmp_path / "train_metrics.csv").write_text("step,loss\n1,0.0\n", encoding="utf-8")
    (tmp_path / "metrics.csv").write_text("legacy\n", encoding="utf-8")

    assert training_metrics_path(tmp_path) == tmp_path / "train_metrics.csv"


def test_training_metrics_path_falls_back_to_legacy_metrics(tmp_path) -> None:
    (tmp_path / "metrics.csv").write_text("step,loss\n1,0.0\n", encoding="utf-8")

    assert training_metrics_path(tmp_path) == tmp_path / "metrics.csv"
