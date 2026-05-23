import numpy as np
import pandas as pd
import pytest

from autodrift.old_key_replay_failure_trajectory_anchor import (
    _save_anchor,
    anchor_branch_for_failed_row,
    normalize_failed_row_schema,
)
from autodrift.intervention_objectives import load_trajectory_action_anchor


def test_anchor_branch_for_failed_row_selects_normal_failure():
    row = {
        "candidate_normal_success_regression": "True",
        "candidate_normal_success": "False",
        "candidate_wrong_history_margin": "-0.1",
    }

    assert anchor_branch_for_failed_row(row) == "normal"


def test_anchor_branch_for_failed_row_selects_wrong_history_safe_branch():
    row = pd.Series(
        {
            "candidate_normal_success_regression": "False",
            "candidate_normal_success": "True",
            "candidate_wrong_history_margin": "0.01",
        }
    )

    assert anchor_branch_for_failed_row(row) == "wrong_history"


def test_normalize_failed_row_schema_maps_baseline_margins():
    frame = pd.DataFrame(
        [
            {
                "baseline_normal_margin": 0.1,
                "baseline_wrong_history_margin": -0.2,
                "baseline_margin_gap": 0.3,
            }
        ]
    )

    normalized = normalize_failed_row_schema(frame)

    assert normalized.loc[0, "reference_normal_margin"] == pytest.approx(0.1)
    assert normalized.loc[0, "reference_wrong_history_margin"] == pytest.approx(-0.2)
    assert normalized.loc[0, "reference_margin_gap"] == pytest.approx(0.3)


def test_save_old_key_anchor_loads_as_trajectory_anchor(tmp_path):
    path = tmp_path / "anchor.npz"
    _save_anchor(
        path,
        observation=np.zeros((2, 72), dtype=np.float32),
        hidden=np.zeros((2, 128), dtype=np.float32),
        reference_action=np.zeros((2, 3), dtype=np.float32),
        source_index=np.asarray([0, 1], dtype=np.int64),
        step_index=np.asarray([0, 0], dtype=np.int64),
        weight=np.asarray([1.0, 2.0], dtype=np.float32),
    )

    anchor = load_trajectory_action_anchor(
        path,
        device="cpu",
        obs_dim=72,
        hidden_size=128,
        act_dim=3,
    )

    assert anchor.size == 2
    assert anchor.weight.tolist() == pytest.approx([1.0, 2.0])
