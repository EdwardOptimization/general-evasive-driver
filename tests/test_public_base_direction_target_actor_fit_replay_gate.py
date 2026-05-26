from pathlib import Path

from autodrift.public_base_direction_target_actor_fit_replay_gate import (
    DirectionTargetCandidate,
    classify_direction_target_actor_fit_replay_gate,
    failure_types_for_result_class,
    load_direction_target_candidates,
    select_preflight_candidate,
)


def test_direction_target_replay_gate_classifier_flags_contract_artifact() -> None:
    result = classify_direction_target_actor_fit_replay_gate(
        actor_inputs_changed=True,
        candidate_preflight_pass_count=1,
        selected_candidate=DirectionTargetCandidate(alpha=1.0, checkpoint=Path("candidate.pt")),
        six_public_replay_gates_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "direction_target_actor_fit_replay_gate_contract_artifact"
    assert failure_types_for_result_class(result) == ["contract_violation"]


def test_direction_target_replay_gate_classifier_requires_preflight_candidate() -> None:
    result = classify_direction_target_actor_fit_replay_gate(
        actor_inputs_changed=False,
        candidate_preflight_pass_count=0,
        selected_candidate=None,
        six_public_replay_gates_pass=False,
        behavior_pass=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "direction_target_actor_fit_replay_gate_no_preflight_candidate"
    assert failure_types_for_result_class(result) == ["proof_washout"]


def test_direction_target_replay_gate_classifier_routes_public_replay_failure() -> None:
    result = classify_direction_target_actor_fit_replay_gate(
        actor_inputs_changed=False,
        candidate_preflight_pass_count=1,
        selected_candidate=DirectionTargetCandidate(alpha=0.5, checkpoint=Path("candidate.pt")),
        six_public_replay_gates_pass=False,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "direction_target_actor_fit_replay_gate_proof_washout"
    assert failure_types_for_result_class(result) == ["proof_washout"]


def test_direction_target_replay_gate_classifier_accepts_pass() -> None:
    result = classify_direction_target_actor_fit_replay_gate(
        actor_inputs_changed=False,
        candidate_preflight_pass_count=2,
        selected_candidate=DirectionTargetCandidate(alpha=1.0, checkpoint=Path("candidate.pt")),
        six_public_replay_gates_pass=True,
        behavior_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "direction_target_actor_fit_replay_gate_pass"
    assert failure_types_for_result_class(result) == ["none"]


def test_load_direction_target_candidates_sorts_descending(tmp_path: Path) -> None:
    csv_path = tmp_path / "candidates.csv"
    csv_path.write_text(
        "alpha,checkpoint\n"
        "0.05,runs/a.pt\n"
        "1.0,runs/c.pt\n"
        "0.5,runs/b.pt\n",
        encoding="utf-8",
    )
    candidates = load_direction_target_candidates(csv_path)
    assert [candidate.alpha for candidate in candidates] == [1.0, 0.5, 0.05]
    assert [candidate.checkpoint for candidate in candidates] == [Path("runs/c.pt"), Path("runs/b.pt"), Path("runs/a.pt")]


def test_select_preflight_candidate_uses_highest_ranked_pass() -> None:
    candidates = [
        DirectionTargetCandidate(alpha=1.0, checkpoint=Path("a.pt")),
        DirectionTargetCandidate(alpha=0.5, checkpoint=Path("b.pt")),
        DirectionTargetCandidate(alpha=0.2, checkpoint=Path("c.pt")),
    ]
    selected = select_preflight_candidate(
        candidates,
        [
            {"alpha": 1.0, "gate_pass": False},
            {"alpha": 0.5, "gate_pass": True},
            {"alpha": 0.2, "gate_pass": True},
        ],
    )
    assert selected == candidates[1]
