import numpy as np
import pytest
import torch

from autodrift.outcome_intervention_eval import (
    evaluate_exact_source_reports,
    evaluate_policies,
    match_source_rows,
    parse_checkpoint_policy,
    parse_source_npz,
)
from autodrift.train_ppo import ActorCritic


def _write_checkpoint(path, *, hidden_bias: float = 0.0):
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    with torch.no_grad():
        model.actor_mean.bias.fill_(hidden_bias)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {
                "actor_encoder": "human_view_online_gru",
                "actor_history_length": 1,
                "action_sequence_horizon": 1,
                "response_prediction_dim": 0,
                "response_prediction_horizon": 1,
                "log_std_init": -1.0,
                "log_std_min": -5.0,
                "log_std_max": -0.5,
            },
        },
        path,
    )


def test_parse_checkpoint_policy_requires_name_and_path():
    name, path = parse_checkpoint_policy("base=/tmp/model.pt")
    assert name == "base"
    assert str(path) == "/tmp/model.pt"


def test_parse_source_npz_requires_name_and_path():
    name, path = parse_source_npz("m223=/tmp/source.npz")
    assert name == "m223"
    assert str(path) == "/tmp/source.npz"


def test_evaluate_policies_writes_fixed_batch_comparable_summary(tmp_path):
    snippet_path = tmp_path / "snippets.npz"
    np.savez_compressed(
        snippet_path,
        observation=np.zeros((4, 72), dtype=np.float32),
        preferred_hidden=np.zeros((4, 8), dtype=np.float32),
        rejected_hidden=np.ones((4, 8), dtype=np.float32) * 0.2,
        preferred_action=np.zeros((4, 3), dtype=np.float32),
        weight=np.ones(4, dtype=np.float32),
    )
    checkpoint_a = tmp_path / "a.pt"
    checkpoint_b = tmp_path / "b.pt"
    _write_checkpoint(checkpoint_a, hidden_bias=0.0)
    _write_checkpoint(checkpoint_b, hidden_bias=0.1)

    summary, batch_losses = evaluate_policies(
        checkpoint_policies=[("a", checkpoint_a), ("b", checkpoint_b)],
        snippet_npz=snippet_path,
        device="cpu",
        batch_size=2,
        batches=3,
        seed=7,
        logprob_margin=0.05,
    )

    assert list(summary["policy"]) == ["a", "b"]
    assert set(batch_losses["policy"]) == {"a", "b"}
    assert len(batch_losses) == 6
    assert (summary["loss_mean"] >= 0.0).all()
    assert set(summary["mode"]) == {"sampled"}
    assert set(batch_losses["mode"]) == {"sampled"}


def test_evaluate_policies_exact_full_corpus_is_deterministic(tmp_path):
    snippet_path = tmp_path / "snippets.npz"
    np.savez_compressed(
        snippet_path,
        observation=np.zeros((4, 72), dtype=np.float32),
        preferred_hidden=np.zeros((4, 8), dtype=np.float32),
        rejected_hidden=np.ones((4, 8), dtype=np.float32) * 0.2,
        preferred_action=np.zeros((4, 3), dtype=np.float32),
        weight=np.ones(4, dtype=np.float32),
    )
    checkpoint = tmp_path / "model.pt"
    _write_checkpoint(checkpoint, hidden_bias=0.05)

    summary_a, batch_losses_a = evaluate_policies(
        checkpoint_policies=[("model", checkpoint)],
        snippet_npz=snippet_path,
        device="cpu",
        batch_size=2,
        batches=3,
        seed=7,
        logprob_margin=0.05,
        exact=True,
    )
    summary_b, batch_losses_b = evaluate_policies(
        checkpoint_policies=[("model", checkpoint)],
        snippet_npz=snippet_path,
        device="cpu",
        batch_size=2,
        batches=3,
        seed=999,
        logprob_margin=0.05,
        exact=True,
    )

    assert list(summary_a["policy"]) == ["model"]
    assert summary_a.loc[0, "mode"] == "exact"
    assert summary_a.loc[0, "batch_size"] == 4
    assert summary_a.loc[0, "batches"] == 1
    assert len(batch_losses_a) == 1
    assert batch_losses_a.loc[0, "mode"] == "exact"
    np.testing.assert_allclose(summary_a["loss_mean"], summary_b["loss_mean"])
    np.testing.assert_allclose(batch_losses_a["loss"], batch_losses_b["loss"])


def test_exact_source_reports_match_rows_and_use_clamped_denominator(tmp_path):
    snippet_path = tmp_path / "combined.npz"
    observation = np.zeros((3, 72), dtype=np.float32)
    observation[:, 0] = np.arange(3, dtype=np.float32)
    preferred_hidden = np.zeros((3, 8), dtype=np.float32)
    preferred_hidden[:, 0] = np.arange(3, dtype=np.float32) * 0.1
    rejected_hidden = np.ones((3, 8), dtype=np.float32) * 0.2
    rejected_hidden[:, 1] = np.arange(3, dtype=np.float32) * 0.2
    preferred_action = np.zeros((3, 3), dtype=np.float32)
    preferred_action[:, 0] = np.asarray([0.0, 0.1, -0.1], dtype=np.float32)
    weight = np.asarray([0.1, 0.2, 0.3], dtype=np.float32)
    np.savez_compressed(
        snippet_path,
        observation=observation,
        preferred_hidden=preferred_hidden,
        rejected_hidden=rejected_hidden,
        preferred_action=preferred_action,
        weight=weight,
    )
    source_a = tmp_path / "source_a.npz"
    source_b = tmp_path / "source_b.npz"
    np.savez_compressed(
        source_a,
        observation=observation[:2],
        preferred_hidden=preferred_hidden[:2],
        rejected_hidden=rejected_hidden[:2],
        preferred_action=preferred_action[:2],
        weight=weight[:2],
    )
    np.savez_compressed(
        source_b,
        observation=observation[2:],
        preferred_hidden=preferred_hidden[2:],
        rejected_hidden=rejected_hidden[2:],
        preferred_action=preferred_action[2:],
        weight=weight[2:],
    )
    checkpoint = tmp_path / "model.pt"
    _write_checkpoint(checkpoint, hidden_bias=0.05)

    aggregate, _ = evaluate_policies(
        checkpoint_policies=[("model", checkpoint)],
        snippet_npz=snippet_path,
        device="cpu",
        batch_size=2,
        batches=3,
        seed=7,
        logprob_margin=0.05,
        exact=True,
    )
    per_row, source_summary = evaluate_exact_source_reports(
        checkpoint_policies=[("model", checkpoint)],
        snippet_npz=snippet_path,
        source_npzs=[("a", source_a), ("b", source_b)],
        device="cpu",
        logprob_margin=0.05,
    )

    assert list(match_source_rows(snippet_path, [("a", source_a), ("b", source_b)])["source"]) == [
        "a",
        "a",
        "b",
    ]
    assert set(per_row["source"]) == {"a", "b"}
    assert set(source_summary["source"]) == {"a", "b"}
    assert set(source_summary["combined_denominator"]) == {1.0}
    assert set(source_summary["source_denominator_clamped"]) == {1.0}
    np.testing.assert_allclose(
        source_summary["combined_objective_component"].sum(),
        aggregate.loc[0, "loss_mean"],
    )


def test_exact_source_reports_reject_unmatched_combined_rows(tmp_path):
    snippet_path = tmp_path / "combined.npz"
    observation = np.zeros((2, 72), dtype=np.float32)
    observation[:, 0] = np.arange(2, dtype=np.float32)
    preferred_hidden = np.zeros((2, 8), dtype=np.float32)
    rejected_hidden = np.ones((2, 8), dtype=np.float32) * 0.2
    preferred_action = np.zeros((2, 3), dtype=np.float32)
    weight = np.ones(2, dtype=np.float32)
    np.savez_compressed(
        snippet_path,
        observation=observation,
        preferred_hidden=preferred_hidden,
        rejected_hidden=rejected_hidden,
        preferred_action=preferred_action,
        weight=weight,
    )
    source = tmp_path / "source.npz"
    np.savez_compressed(
        source,
        observation=observation[:1],
        preferred_hidden=preferred_hidden[:1],
        rejected_hidden=rejected_hidden[:1],
        preferred_action=preferred_action[:1],
        weight=weight[:1],
    )

    with pytest.raises(ValueError, match="did not match any source"):
        match_source_rows(snippet_path, [("partial", source)])
