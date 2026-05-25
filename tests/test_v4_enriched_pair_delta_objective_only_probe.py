from __future__ import annotations

import torch

from autodrift.v4_enriched_pair_delta_objective_only_probe import (
    _candidate_summary,
    classify_enriched_pair_delta_objective_only_probe,
    interpolate_state_dict,
    pair_delta_preference_components,
)


def test_pair_delta_preference_components_prefers_override_for_improvement() -> None:
    normal = torch.tensor([0.0, 1.0])
    override = torch.tensor([1.0, 0.0])
    is_improvement = torch.tensor([True, True])
    weights = torch.ones(2)

    unweighted, weighted = pair_delta_preference_components(
        normal_logp=normal,
        override_logp=override,
        is_improvement=is_improvement,
        weights=weights,
        margin=0.05,
    )

    assert unweighted[0] < unweighted[1]
    assert torch.allclose(unweighted, weighted)


def test_pair_delta_preference_components_prefers_normal_for_degradation() -> None:
    normal = torch.tensor([1.0, 0.0])
    override = torch.tensor([0.0, 1.0])
    is_improvement = torch.tensor([False, False])
    weights = torch.tensor([1.0, 2.0])

    unweighted, weighted = pair_delta_preference_components(
        normal_logp=normal,
        override_logp=override,
        is_improvement=is_improvement,
        weights=weights,
        margin=0.05,
    )

    assert unweighted[0] < unweighted[1]
    assert torch.allclose(weighted, unweighted * weights)


def test_interpolate_state_dict_mixes_floating_tensors_only() -> None:
    base = {
        "weight": torch.tensor([1.0, 3.0]),
        "counter": torch.tensor([5], dtype=torch.long),
    }
    raw = {
        "weight": torch.tensor([3.0, 7.0]),
        "counter": torch.tensor([9], dtype=torch.long),
    }

    mixed = interpolate_state_dict(base, raw, 0.25)

    assert torch.allclose(mixed["weight"], torch.tensor([1.5, 4.0]))
    assert torch.equal(mixed["counter"], base["counter"])


def test_classify_probe_exact_admissible() -> None:
    result = classify_enriched_pair_delta_objective_only_probe(
        tensor_rows_reconstructed=10,
        expected_rows=10,
        missing_tensor_count=0,
        training_nonfinite=False,
        actor_input_contract_changed=False,
        residual_head_changed=False,
        ppo_used=False,
        promoted=False,
        exact_losses_finite=True,
        raw_train_improved=True,
        exact_admissible_alpha_count=1,
    )

    assert result == "v4_enriched_pair_delta_objective_only_probe_exact_admissible"


def test_classify_probe_holdout_regression_when_train_improves_without_admissible_alpha() -> None:
    result = classify_enriched_pair_delta_objective_only_probe(
        tensor_rows_reconstructed=10,
        expected_rows=10,
        missing_tensor_count=0,
        training_nonfinite=False,
        actor_input_contract_changed=False,
        residual_head_changed=False,
        ppo_used=False,
        promoted=False,
        exact_losses_finite=True,
        raw_train_improved=True,
        exact_admissible_alpha_count=0,
    )

    assert result == "v4_enriched_pair_delta_objective_only_probe_exact_holdout_regression"


def test_candidate_summary_does_not_admit_raw_candidate_directly() -> None:
    base = {
        "objective_train_public": {"weighted_loss_mean": 2.0},
        "objective_eval_public": {"weighted_loss_mean": 1.0},
        "source_holdout_public": {"weighted_loss_mean": 1.0},
        "new_signature_holdout_public": {"weighted_loss_mean": 1.0},
    }
    split_rows = [
        {"split": "objective_train_public", "weighted_loss_mean": 1.5, "finite": True},
        {"split": "objective_eval_public", "weighted_loss_mean": 0.9, "finite": True},
        {"split": "source_holdout_public", "weighted_loss_mean": 0.9, "finite": True},
        {"split": "new_signature_holdout_public", "weighted_loss_mean": 0.9, "finite": True},
    ]

    raw = _candidate_summary(
        candidate_name="raw_candidate",
        alpha="raw",
        split_rows=split_rows,
        base_by_split=base,
        tolerance=1e-4,
        ppo_used=False,
        promoted=False,
        actor_input_contract_changed=False,
        residual_head_changed=False,
    )
    interpolated = _candidate_summary(
        candidate_name="interpolation",
        alpha=0.1,
        split_rows=split_rows,
        base_by_split=base,
        tolerance=1e-4,
        ppo_used=False,
        promoted=False,
        actor_input_contract_changed=False,
        residual_head_changed=False,
    )

    assert raw["train_improved"] is True
    assert raw["exact_admissible"] is False
    assert interpolated["exact_admissible"] is True
