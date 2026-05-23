import numpy as np
import pytest
import torch
from torch.distributions import Normal

from autodrift.intervention_objectives import (
    load_rejected_history_preference_snippets,
    rejected_history_preference_loss,
)
from autodrift.rejected_history_preference_objective import build_preference_corpus


class _DummyPreferenceModel:
    def forward_recurrent(self, observation, hidden):
        del observation
        mean = hidden[:, :3]
        scale = torch.ones_like(mean) * 0.5
        return Normal(mean, scale), None, hidden


def _write_npz(path):
    np.savez(
        path,
        observation=np.zeros((2, 72), dtype=np.float32),
        preferred_hidden=np.asarray([[0.7, 0.0, 0.0, 0.1], [0.6, 0.1, 0.0, 0.2]], dtype=np.float32),
        rejected_hidden=np.asarray([[-0.7, 0.0, 0.0, 0.1], [-0.6, -0.1, 0.0, 0.2]], dtype=np.float32),
        preferred_action=np.asarray([[0.5, 0.0, 0.0], [0.4, 0.1, 0.0]], dtype=np.float32),
        rejected_action=np.asarray([[-0.5, 0.0, 0.0], [-0.4, -0.1, 0.0]], dtype=np.float32),
        preferred_score=np.asarray([1.02, 1.01], dtype=np.float32),
        rejected_score=np.asarray([-0.01, -0.02], dtype=np.float32),
        score_delta=np.asarray([1.03, 1.03], dtype=np.float32),
        normal_margin=np.asarray([0.02, 0.01], dtype=np.float32),
        wrong_history_margin=np.asarray([-0.01, -0.02], dtype=np.float32),
        margin_floor=np.asarray([-0.01, -0.02], dtype=np.float32),
        weight=np.asarray([1.0, 2.0], dtype=np.float32),
        row_id=np.asarray([6, 11], dtype=np.int64),
        group_index=np.asarray([0, 1], dtype=np.int64),
        target_index=np.asarray([0, 0], dtype=np.int64),
    )


def test_load_rejected_history_preference_snippets_validates_contract(tmp_path):
    path = tmp_path / "preference.npz"
    _write_npz(path)

    snippets = load_rejected_history_preference_snippets(
        path,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=4,
        act_dim=3,
    )

    assert snippets.size == 2
    assert snippets.rejected_action.shape == (2, 3)
    assert snippets.row_id.tolist() == [6, 11]

    broken = tmp_path / "broken.npz"
    data = dict(np.load(path))
    data.pop("rejected_action")
    np.savez(broken, **data)
    with pytest.raises(ValueError, match="missing fields"):
        load_rejected_history_preference_snippets(
            broken,
            device=torch.device("cpu"),
            obs_dim=72,
            hidden_size=4,
            act_dim=3,
        )


def test_rejected_history_preference_loss_is_finite(tmp_path):
    path = tmp_path / "preference.npz"
    _write_npz(path)
    snippets = load_rejected_history_preference_snippets(
        path,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=4,
        act_dim=3,
    )

    loss = rejected_history_preference_loss(
        _DummyPreferenceModel(),
        snippets,
        batch_size=2,
        preferred_logprob_margin=0.05,
        wrong_logprob_margin=0.05,
        wrong_preference_coef=1.0,
    )

    assert torch.isfinite(loss)
    assert float(loss.item()) >= 0.0


def test_build_preference_corpus_adds_rejected_actions_and_weights(tmp_path):
    source_npz = tmp_path / "source.npz"
    np.savez(
        source_npz,
        observation=np.zeros((2, 72), dtype=np.float32),
        preferred_hidden=np.ones((2, 4), dtype=np.float32),
        rejected_hidden=-np.ones((2, 4), dtype=np.float32),
        preferred_action=np.zeros((2, 3), dtype=np.float32),
        weight=np.asarray([0.5, 0.25], dtype=np.float32),
        preferred_score=np.ones(2, dtype=np.float32),
        rejected_score=np.zeros(2, dtype=np.float32),
        score_delta=np.ones(2, dtype=np.float32),
        group_index=np.asarray([0, 1], dtype=np.int64),
        target_index=np.asarray([0, 0], dtype=np.int64),
    )
    source_csv = tmp_path / "source.csv"
    source_csv.write_text(
        "row_id,physical_pair_key,target,left_seed,right_seed,left_step,right_step,"
        "relocated_obstacle_body_x,relocated_obstacle_body_y,relocated_obstacle_half_width\n"
        "6,1:10:2:20,brake,1,2,10,20,8.0,-0.5,0.8\n"
        "11,3:10:4:20,brake,3,4,10,20,9.0,-0.4,0.9\n",
        encoding="utf-8",
    )
    replay_csv = tmp_path / "replay.csv"
    replay_csv.write_text(
        "policy,row_id,normal_success,wrong_history_success,normal_margin,wrong_history_margin,"
        "normal_first_steer,normal_first_throttle,normal_first_brake,"
        "wrong_history_first_steer,wrong_history_first_throttle,wrong_history_first_brake,"
        "wrong_history_terminal_reason\n"
        "base,6,True,False,0.01,-0.001,0.5,0.0,0.1,-0.5,0.0,0.2,collision\n"
        "base,11,True,False,0.02,-0.01,0.4,0.0,0.2,-0.4,0.0,0.3,collision\n",
        encoding="utf-8",
    )

    summary = build_preference_corpus(
        source_npz=source_npz,
        source_csv=source_csv,
        base_replay_csv=replay_csv,
        base_policy="base",
        failed_rows={6},
        recovered_rows={11},
        failed_row_bonus=4.0,
        recovered_row_bonus=2.0,
        max_weight=100.0,
        output_npz=tmp_path / "out.npz",
        output_csv=tmp_path / "out.csv",
    )

    out = np.load(tmp_path / "out.npz")
    assert summary["rows"] == 2
    assert out["rejected_action"].shape == (2, 3)
    assert out["row_id"].tolist() == [6, 11]
    assert out["weight"][0] > out["weight"][1]
