import argparse

import pytest
import torch

from autodrift.candidate_b_temporal_safe_projection_probe import (
    classify_temporal_safe_projection,
    failure_types_for_temporal_safe_projection,
    interpolate_full_state,
    next_blocker_for_temporal_safe_projection,
    parse_alphas,
    parse_repair_candidates,
    select_projection_candidate,
)


def test_parse_alphas_rejects_empty_and_out_of_range() -> None:
    assert parse_alphas("0.05, 0.1,1") == (0.05, 0.1, 1.0)

    with pytest.raises(argparse.ArgumentTypeError):
        parse_alphas("")
    with pytest.raises(argparse.ArgumentTypeError):
        parse_alphas("1.1")


def test_parse_repair_candidates_requires_label_path_pairs() -> None:
    parsed = parse_repair_candidates("raw=a.pt,base=b.pt")

    assert [(label, str(path)) for label, path in parsed] == [("raw", "a.pt"), ("base", "b.pt")]

    with pytest.raises(argparse.ArgumentTypeError):
        parse_repair_candidates("a.pt")


def test_interpolate_full_state_interpolates_float_and_preserves_nonfloat() -> None:
    base = {
        "actor.weight": torch.tensor([1.0, 3.0]),
        "counter": torch.tensor([1], dtype=torch.int64),
    }
    target = {
        "actor.weight": torch.tensor([5.0, 7.0]),
        "counter": torch.tensor([99], dtype=torch.int64),
    }

    output = interpolate_full_state(base, target, 0.25)

    assert torch.equal(output["actor.weight"], torch.tensor([2.0, 4.0]))
    assert torch.equal(output["counter"], torch.tensor([1], dtype=torch.int64))


def test_interpolate_full_state_validates_keys_and_shapes() -> None:
    with pytest.raises(ValueError):
        interpolate_full_state({"a": torch.tensor([1.0])}, {"b": torch.tensor([1.0])}, 0.5)

    with pytest.raises(ValueError):
        interpolate_full_state({"a": torch.tensor([1.0])}, {"a": torch.tensor([[1.0]])}, 0.5)


def test_select_projection_candidate_prefers_highest_useful_alpha() -> None:
    rows = [
        {
            "eligible_for_first_replay": True,
            "alpha": 0.1,
            "weighted_total_loss": -0.9,
            "exact_m297_loss": 1.0,
            "exact_m270_loss": 1.0,
            "candidate_label": "low",
        },
        {
            "eligible_for_first_replay": True,
            "alpha": 0.2,
            "weighted_total_loss": -0.8,
            "exact_m297_loss": 1.0,
            "exact_m270_loss": 1.0,
            "candidate_label": "high",
        },
        {
            "eligible_for_first_replay": False,
            "alpha": 1.0,
            "weighted_total_loss": -1.0,
            "exact_m297_loss": 0.1,
            "exact_m270_loss": 0.1,
            "candidate_label": "ineligible",
        },
    ]

    assert select_projection_candidate(rows)["candidate_label"] == "high"


def test_classifier_routes_no_temporal_candidate_before_exact() -> None:
    result = classify_temporal_safe_projection(
        actor_inputs_changed=False,
        temporal_exact_pass_count=0,
        temporal_and_exact_pass_count=0,
        eligible_candidate_count=0,
        selected_candidate=None,
        m267_m264_pass=False,
        row15_retained=False,
        m183_m170_pass=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "candidate_b_temporal_safe_projection_no_temporal_candidate"
    assert failure_types_for_temporal_safe_projection(result) == ["proof_washout"]
    assert next_blocker_for_temporal_safe_projection(result) == "candidate_b_direct_temporal_objective_integration_design"


def test_classifier_routes_base_equivalent_candidate() -> None:
    result = classify_temporal_safe_projection(
        actor_inputs_changed=False,
        temporal_exact_pass_count=2,
        temporal_and_exact_pass_count=2,
        eligible_candidate_count=0,
        selected_candidate=None,
        m267_m264_pass=False,
        row15_retained=False,
        m183_m170_pass=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "candidate_b_temporal_safe_projection_base_equivalent"
    assert failure_types_for_temporal_safe_projection(result) == ["objective_overfit"]


def test_classifier_requires_both_first_replays_and_row15() -> None:
    selected = {"checkpoint": "candidate.pt"}

    result = classify_temporal_safe_projection(
        actor_inputs_changed=False,
        temporal_exact_pass_count=1,
        temporal_and_exact_pass_count=1,
        eligible_candidate_count=1,
        selected_candidate=selected,
        m267_m264_pass=True,
        row15_retained=False,
        m183_m170_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "candidate_b_temporal_safe_projection_proof_washout"
    assert next_blocker_for_temporal_safe_projection(result) == "candidate_b_temporal_safe_projection_first_replay_failure_audit"


def test_classifier_accepts_first_replay_candidate() -> None:
    result = classify_temporal_safe_projection(
        actor_inputs_changed=False,
        temporal_exact_pass_count=1,
        temporal_and_exact_pass_count=1,
        eligible_candidate_count=1,
        selected_candidate={"checkpoint": "candidate.pt"},
        m267_m264_pass=True,
        row15_retained=True,
        m183_m170_pass=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )

    assert result == "candidate_b_temporal_safe_projection_first_replay_candidate"
    assert failure_types_for_temporal_safe_projection(result) == ["none"]
    assert next_blocker_for_temporal_safe_projection(result) == "candidate_b_temporal_safe_projection_full_public_gate_design"
