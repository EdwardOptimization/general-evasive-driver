import argparse

import torch

from autodrift.capability_step_temporal_sequence_update_probe import (
    changed_parameter_names,
    interpolate_actor_mean_state,
    parse_alphas,
)


def test_parse_alphas_rejects_empty_and_negative():
    assert parse_alphas("0.005,0.01") == (0.005, 0.01)

    try:
        parse_alphas("")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("empty alpha list should fail")

    try:
        parse_alphas("-0.1")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("negative alpha should fail")


def test_interpolate_actor_mean_state_changes_only_actor_mean():
    base = {
        "actor_mean.weight": torch.tensor([1.0]),
        "critic.weight": torch.tensor([3.0]),
    }
    raw = {
        "actor_mean.weight": torch.tensor([5.0]),
        "critic.weight": torch.tensor([99.0]),
    }

    out = interpolate_actor_mean_state(base, raw, 0.25)

    assert torch.equal(out["actor_mean.weight"], torch.tensor([2.0]))
    assert torch.equal(out["critic.weight"], torch.tensor([3.0]))


def test_changed_parameter_names_detects_exact_tensor_changes():
    base = {
        "actor_mean.weight": torch.tensor([1.0]),
        "critic.weight": torch.tensor([3.0]),
    }
    candidate = {
        "actor_mean.weight": torch.tensor([1.0]),
        "critic.weight": torch.tensor([4.0]),
    }

    assert changed_parameter_names(base, candidate) == ["critic.weight"]
