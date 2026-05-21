import numpy as np

from autodrift.env import DriftEnvConfig
from autodrift.hidden_swap_gate import DecisionSnapshot
from autodrift.snapshot_bank_relocation import (
    _outcome_intervention_weight,
    outcome_intervention_arrays,
    outcome_intervention_metadata,
    pair_snapshot_banks,
)
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


def _snapshot(condition: str, step: int, observation: np.ndarray) -> DecisionSnapshot:
    return DecisionSnapshot(
        condition=condition,
        seed=1,
        step=step,
        observation=observation.astype(np.float32),
        hidden=None,
        env=None,
        info={"step": step},
        obstacle_distance=10.0,
        snapshot_score=0.0,
    )


def test_pair_snapshot_banks_sorts_by_visible_response_and_context_distance():
    config = DriftEnvConfig()
    base = np.zeros(HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    nominal = [_snapshot("nominal", 10, base)]
    close = base.copy()
    close[0] = 0.05
    close[20] = 0.02
    far = base.copy()
    far[0] = 0.20
    far[20] = 0.30
    perturbed = [_snapshot("perturbed", 11, far), _snapshot("perturbed", 12, close)]

    pairs = pair_snapshot_banks(nominal, perturbed, config, max_pairs=2)

    assert len(pairs) == 2
    first_meta, first_nominal, first_perturbed = pairs[0]
    assert first_nominal.step == 10
    assert first_perturbed.step == 12
    assert np.isclose(first_meta["pre_visible_response_distance"], 0.05)
    assert np.isclose(first_meta["pre_visible_context_distance"], 0.02)


def test_pair_snapshot_banks_applies_pre_distance_filters():
    config = DriftEnvConfig()
    base = np.zeros(HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    perturbed_obs = base.copy()
    perturbed_obs[0] = 0.40
    nominal = [_snapshot("nominal", 10, base)]
    perturbed = [_snapshot("perturbed", 11, perturbed_obs)]

    pairs = pair_snapshot_banks(
        nominal,
        perturbed,
        config,
        max_pairs=4,
        max_pre_response_distance=0.20,
    )

    assert pairs == []


def test_outcome_intervention_weight_favors_margin_loss_near_boundary():
    near = _outcome_intervention_weight(
        0.05,
        0.02,
        True,
        min_margin_gap=0.0,
        boundary_margin_scale=0.20,
    )
    far = _outcome_intervention_weight(
        1.00,
        0.97,
        True,
        min_margin_gap=0.0,
        boundary_margin_scale=0.20,
    )

    assert near > far
    assert _outcome_intervention_weight(0.05, 0.02, False, min_margin_gap=0.0, boundary_margin_scale=0.20) == 0.0
    assert _outcome_intervention_weight(0.05, 0.049, True, min_margin_gap=0.01, boundary_margin_scale=0.20) == 0.0


def test_outcome_intervention_arrays_and_metadata_split_tensor_payloads():
    examples = [
        {
            "seed": 1,
            "source_condition": "perturbed",
            "normal_margin": 0.05,
            "wrong_history_margin": 0.02,
            "margin_gap": 0.03,
            "weight": 0.02,
            "observation": np.zeros(3, dtype=np.float32),
            "preferred_hidden": np.zeros(4, dtype=np.float32),
            "rejected_hidden": np.ones(4, dtype=np.float32),
            "preferred_action": np.zeros(2, dtype=np.float32),
        }
    ]

    arrays = outcome_intervention_arrays(examples)
    metadata = outcome_intervention_metadata(examples)

    assert arrays["observation"].shape == (1, 3)
    assert arrays["preferred_hidden"].shape == (1, 4)
    assert arrays["preferred_action"].shape == (1, 2)
    assert "observation" not in metadata
    assert metadata.loc[0, "source_condition"] == "perturbed"
