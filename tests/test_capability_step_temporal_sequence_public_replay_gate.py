from pathlib import Path

from autodrift.capability_step_temporal_sequence_public_replay_gate import (
    TemporalSequenceCandidate,
    classify_temporal_sequence_public_replay_gate,
    failure_types_for_result_class,
    load_temporal_sequence_candidates,
    select_preflight_candidate,
)


def test_temporal_sequence_public_replay_classifier_flags_contract_artifact() -> None:
    result = classify_temporal_sequence_public_replay_gate(
        actor_inputs_changed=True,
        exact_contract_pass_count=5,
        candidate_preflight_pass_count=1,
        selected_candidate=TemporalSequenceCandidate(alpha=0.2, checkpoint=Path("candidate.pt")),
        six_public_replay_gates_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "temporal_sequence_public_replay_gate_contract_artifact"
    assert failure_types_for_result_class(result) == ["contract_violation"]


def test_temporal_sequence_public_replay_classifier_requires_exact_candidate() -> None:
    result = classify_temporal_sequence_public_replay_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=0,
        candidate_preflight_pass_count=0,
        selected_candidate=None,
        six_public_replay_gates_pass=False,
        behavior_pass=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "temporal_sequence_public_replay_gate_no_exact_candidate"
    assert failure_types_for_result_class(result) == ["proof_washout"]


def test_temporal_sequence_public_replay_classifier_requires_preflight_candidate() -> None:
    result = classify_temporal_sequence_public_replay_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=5,
        candidate_preflight_pass_count=0,
        selected_candidate=None,
        six_public_replay_gates_pass=False,
        behavior_pass=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "temporal_sequence_public_replay_gate_no_preflight_candidate"
    assert failure_types_for_result_class(result) == ["proof_washout"]


def test_temporal_sequence_public_replay_classifier_routes_behavior_regression() -> None:
    result = classify_temporal_sequence_public_replay_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=5,
        candidate_preflight_pass_count=1,
        selected_candidate=TemporalSequenceCandidate(alpha=0.2, checkpoint=Path("candidate.pt")),
        six_public_replay_gates_pass=True,
        behavior_pass=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "temporal_sequence_public_replay_gate_behavior_regression"
    assert failure_types_for_result_class(result) == ["behavior_regression"]


def test_temporal_sequence_public_replay_classifier_accepts_pass() -> None:
    result = classify_temporal_sequence_public_replay_gate(
        actor_inputs_changed=False,
        exact_contract_pass_count=5,
        candidate_preflight_pass_count=1,
        selected_candidate=TemporalSequenceCandidate(alpha=0.2, checkpoint=Path("candidate.pt")),
        six_public_replay_gates_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "temporal_sequence_public_replay_gate_pass"
    assert failure_types_for_result_class(result) == ["none"]


def test_load_temporal_sequence_candidates_uses_exact_metric_rank(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.csv"
    candidates.write_text(
        "alpha,checkpoint\n"
        "0.01,runs/a.pt\n"
        "0.02,runs/b.pt\n"
        "0.2,runs/c.pt\n",
        encoding="utf-8",
    )
    metrics = tmp_path / "metrics.csv"
    metrics.write_text(
        "alpha,weighted_total_loss,candidate_action_l2_mean,exact_gate_pass\n"
        "0.01,-0.88,0.001,True\n"
        "0.02,-0.90,0.002,False\n"
        "0.2,-0.91,0.008,True\n",
        encoding="utf-8",
    )

    loaded = load_temporal_sequence_candidates(candidates, metrics)

    assert [candidate.alpha for candidate in loaded] == [0.2, 0.01]
    assert [candidate.checkpoint for candidate in loaded] == [Path("runs/c.pt"), Path("runs/a.pt")]


def test_select_preflight_candidate_uses_first_ranked_pass() -> None:
    candidates = [
        TemporalSequenceCandidate(alpha=0.2, checkpoint=Path("a.pt")),
        TemporalSequenceCandidate(alpha=0.1, checkpoint=Path("b.pt")),
        TemporalSequenceCandidate(alpha=0.05, checkpoint=Path("c.pt")),
    ]
    selected = select_preflight_candidate(
        candidates,
        [
            {"alpha": 0.2, "gate_pass": False},
            {"alpha": 0.1, "gate_pass": True},
            {"alpha": 0.05, "gate_pass": True},
        ],
    )

    assert selected == candidates[1]
