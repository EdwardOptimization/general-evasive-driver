import numpy as np
import pytest
import torch
from torch.distributions import Normal

from autodrift.exact_post_ppo_repair import (
    ExactRepairConfig,
    _add_exact_gate_fields,
    _select_best_repair_step,
    exact_outcome_intervention_loss,
    exact_rejected_history_preference_loss,
    exact_snippet_action_anchor_loss,
    load_repair_corpora,
    parameter_l2_to_reference,
    parse_alpha_list,
    repair_loss_terms,
)
from autodrift.intervention_objectives import build_snippet_action_anchor
from autodrift.rejected_history_preference_objective import PreferenceLossConfig


class _TinyRecurrentPolicy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.proj = torch.nn.Linear(4, 3, bias=False)
        with torch.no_grad():
            self.proj.weight.copy_(
                torch.tensor(
                    [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                    ]
                )
            )

    def forward_recurrent(self, observation, hidden):
        del observation
        mean = self.proj(hidden)
        scale = torch.ones_like(mean) * 0.5
        return Normal(mean, scale), None, hidden


def _write_preference_npz(path):
    np.savez(
        path,
        observation=np.zeros((3, 72), dtype=np.float32),
        preferred_hidden=np.asarray(
            [[0.7, 0.0, 0.0, 0.1], [0.6, 0.1, 0.0, 0.2], [0.5, 0.0, 0.1, 0.3]],
            dtype=np.float32,
        ),
        rejected_hidden=np.asarray(
            [[-0.7, 0.0, 0.0, 0.1], [-0.6, -0.1, 0.0, 0.2], [-0.5, 0.0, -0.1, 0.3]],
            dtype=np.float32,
        ),
        preferred_action=np.asarray([[0.5, 0.0, 0.0], [0.4, 0.1, 0.0], [0.35, 0.0, 0.1]], dtype=np.float32),
        rejected_action=np.asarray([[-0.5, 0.0, 0.0], [-0.4, -0.1, 0.0], [-0.35, 0.0, -0.1]], dtype=np.float32),
        preferred_score=np.asarray([1.02, 1.01, 1.03], dtype=np.float32),
        rejected_score=np.asarray([-0.01, -0.02, -0.03], dtype=np.float32),
        score_delta=np.asarray([1.03, 1.03, 1.06], dtype=np.float32),
        normal_margin=np.asarray([0.02, 0.01, 0.03], dtype=np.float32),
        wrong_history_margin=np.asarray([-0.01, -0.02, -0.03], dtype=np.float32),
        margin_floor=np.asarray([-0.01, -0.02, -0.03], dtype=np.float32),
        weight=np.asarray([1.0, 2.0, 3.0], dtype=np.float32),
        row_id=np.asarray([6, 11, 16], dtype=np.int64),
        group_index=np.asarray([0, 1, 2], dtype=np.int64),
        target_index=np.asarray([0, 0, 1], dtype=np.int64),
    )


def _write_outcome_npz(path):
    np.savez(
        path,
        observation=np.zeros((2, 72), dtype=np.float32),
        preferred_hidden=np.asarray([[0.7, 0.0, 0.0, 0.1], [0.6, 0.1, 0.0, 0.2]], dtype=np.float32),
        rejected_hidden=np.asarray([[-0.7, 0.0, 0.0, 0.1], [-0.6, -0.1, 0.0, 0.2]], dtype=np.float32),
        preferred_action=np.asarray([[0.5, 0.0, 0.0], [0.4, 0.1, 0.0]], dtype=np.float32),
        weight=np.asarray([1.0, 2.0], dtype=np.float32),
    )


def test_parse_alpha_list_validates_range():
    assert parse_alpha_list("0,0.1, 1") == [0.0, 0.1, 1.0]
    with pytest.raises(Exception):
        parse_alpha_list("")
    with pytest.raises(Exception):
        parse_alpha_list("1.1")


def test_best_repair_step_prefers_feasible_low_total_loss():
    config = ExactRepairConfig(exact_m297_tolerance=1e-7, exact_m270_tolerance=1e-7)
    rows = [
        _add_exact_gate_fields(
            {
                "step": 38,
                "metric_phase": "post_update",
                "total_loss": 1.0e-5,
                "param_l2_to_base": 3.0e-10,
                "exact_m297_loss": 0.9999,
                "exact_m270_loss": 0.9999,
            },
            base_m297=1.0,
            base_m270=1.0,
            config=config,
        ),
        _add_exact_gate_fields(
            {
                "step": 39,
                "metric_phase": "post_update",
                "total_loss": 3.0e-6,
                "param_l2_to_base": 4.0e-10,
                "exact_m297_loss": 0.99995,
                "exact_m270_loss": 0.99995,
            },
            base_m297=1.0,
            base_m270=1.0,
            config=config,
        ),
        _add_exact_gate_fields(
            {
                "step": 40,
                "metric_phase": "post_update",
                "total_loss": 1.0e-6,
                "param_l2_to_base": 5.0e-10,
                "exact_m297_loss": 0.9998,
                "exact_m270_loss": 1.00005,
            },
            base_m297=1.0,
            base_m270=1.0,
            config=config,
        ),
    ]

    selected = _select_best_repair_step(rows)

    assert selected["step"] == 39
    assert selected["exact_lexicographic_pass"] is True


def test_best_repair_step_falls_back_to_smallest_violation():
    config = ExactRepairConfig(exact_m297_tolerance=1e-7, exact_m270_tolerance=1e-7)
    rows = [
        _add_exact_gate_fields(
            {
                "step": 1,
                "metric_phase": "post_update",
                "total_loss": 1.0e-6,
                "param_l2_to_base": 1.0e-10,
                "exact_m297_loss": 1.0002,
                "exact_m270_loss": 1.0002,
            },
            base_m297=1.0,
            base_m270=1.0,
            config=config,
        ),
        _add_exact_gate_fields(
            {
                "step": 2,
                "metric_phase": "post_update",
                "total_loss": 5.0e-6,
                "param_l2_to_base": 2.0e-10,
                "exact_m297_loss": 1.00001,
                "exact_m270_loss": 1.00001,
            },
            base_m297=1.0,
            base_m270=1.0,
            config=config,
        ),
    ]

    selected = _select_best_repair_step(rows)

    assert selected["step"] == 2
    assert selected["exact_lexicographic_pass"] is False
    assert selected["positive_violation"] < rows[0]["positive_violation"]


def test_exact_losses_are_deterministic_full_batch(tmp_path):
    preference_npz = tmp_path / "preference.npz"
    outcome_npz = tmp_path / "outcome.npz"
    _write_preference_npz(preference_npz)
    _write_outcome_npz(outcome_npz)
    preference, outcome = load_repair_corpora(
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=4,
        act_dim=3,
    )
    model = _TinyRecurrentPolicy()
    pref_cfg = PreferenceLossConfig()

    torch.manual_seed(1)
    first_pref = exact_rejected_history_preference_loss(model, preference, pref_cfg)
    first_outcome = exact_outcome_intervention_loss(model, outcome, logprob_margin=0.05)
    torch.manual_seed(999)
    second_pref = exact_rejected_history_preference_loss(model, preference, pref_cfg)
    second_outcome = exact_outcome_intervention_loss(model, outcome, logprob_margin=0.05)

    assert torch.isclose(first_pref, second_pref)
    assert torch.isclose(first_outcome, second_outcome)
    assert float(first_pref.item()) >= 0.0
    assert float(first_outcome.item()) >= 0.0


def test_repair_loss_terms_hinge_and_base_anchor(tmp_path):
    preference_npz = tmp_path / "preference.npz"
    outcome_npz = tmp_path / "outcome.npz"
    _write_preference_npz(preference_npz)
    _write_outcome_npz(outcome_npz)
    preference, outcome = load_repair_corpora(
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        device=torch.device("cpu"),
        obs_dim=72,
        hidden_size=4,
        act_dim=3,
    )
    model = _TinyRecurrentPolicy()
    base_state = {name: value.detach().clone() for name, value in model.state_dict().items()}
    raw_state = {name: value.detach().clone() + 0.1 for name, value in model.state_dict().items()}
    anchor = build_snippet_action_anchor(model, outcome, include_rejected_hidden=True)
    config = ExactRepairConfig(exact_m297_tolerance=1e-6, exact_m270_tolerance=1e-6)
    base_m297 = float(exact_rejected_history_preference_loss(model, preference, config.preference).item())
    base_m270 = float(exact_outcome_intervention_loss(model, outcome, logprob_margin=0.05).item())

    terms = repair_loss_terms(
        model=model,
        preference=preference,
        outcome=outcome,
        anchor=anchor,
        base_m297=base_m297,
        base_m270=base_m270,
        base_state=base_state,
        raw_state=raw_state,
        trainable_names=["proj.weight"],
        config=config,
    )

    assert terms["hinge_m297"].item() == pytest.approx(0.0)
    assert terms["hinge_m270"].item() == pytest.approx(0.0)
    assert exact_snippet_action_anchor_loss(model, anchor).item() == pytest.approx(0.0)
    assert parameter_l2_to_reference(model, base_state, ["proj.weight"]).item() == pytest.approx(0.0)
    assert terms["param_l2_to_raw"].item() > 0.0
    terms["total_loss"].backward()
    assert model.proj.weight.grad is not None
