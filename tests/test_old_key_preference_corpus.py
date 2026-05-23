import numpy as np
import pytest

from autodrift.old_key_preference_corpus import (
    old_key_preference_arrays,
    old_key_preference_metadata,
    old_key_preference_weight,
    validate_old_key_preference_arrays,
    write_old_key_preference_corpus,
)


def _example(row_id=0, target_index=0):
    return {
        "row_id": row_id,
        "key": f"case-{row_id}",
        "seed": 9900 + row_id,
        "source_condition": "perturbed",
        "source_step": 28,
        "paired_step": 28,
        "target_obstacle_distance": 8.0,
        "relocated_obstacle_body_y": 1.5,
        "relocated_obstacle_half_width": 1.0,
        "target_key": f"target-{target_index}",
        "target_index": target_index,
        "group_index": row_id,
        "normal_margin": 0.01,
        "wrong_history_margin": -0.02,
        "margin_floor": -0.02,
        "preferred_score": 1.01,
        "rejected_score": -0.02,
        "score_delta": 1.03,
        "weight": 2.0,
        "student_input_contract": "observation plus deployable recurrent hidden states",
        "observation": np.full(72, row_id, dtype=np.float32),
        "preferred_hidden": np.full(4, row_id + 1, dtype=np.float32),
        "rejected_hidden": np.full(4, -row_id - 1, dtype=np.float32),
        "preferred_action": np.asarray([0.2, 0.0, -0.1], dtype=np.float32),
        "rejected_action": np.asarray([-0.2, 0.0, 0.1], dtype=np.float32),
    }


def test_old_key_weight_emphasizes_regressions_and_boundary():
    base = old_key_preference_weight(
        reference_margin_gap=0.02,
        reference_normal_margin=0.1,
    )
    stressed = old_key_preference_weight(
        reference_margin_gap=0.02,
        reference_normal_margin=0.001,
        direct_candidate_regression=True,
        alpha_0005_regression=True,
    )

    assert stressed > base
    assert base >= 1.0


def test_arrays_validate_and_preserve_contract():
    arrays = old_key_preference_arrays([_example(0, 0), _example(1, 1)])
    contract = validate_old_key_preference_arrays(arrays, obs_dim=72, hidden_dim=4, act_dim=3)

    assert contract.rows == 2
    assert contract.groups == 2
    assert contract.targets == 2
    assert contract.student_input_arrays == ("observation", "preferred_hidden", "rejected_hidden")


def test_metadata_drops_tensor_payloads():
    metadata = old_key_preference_metadata([_example()])

    assert "observation" not in metadata.columns
    assert "preferred_hidden" not in metadata.columns
    assert metadata.loc[0, "student_input_contract"] == "observation plus deployable recurrent hidden states"


def test_write_old_key_preference_corpus(tmp_path):
    summary = write_old_key_preference_corpus(
        examples=[_example(0, 0), _example(1, 1)],
        run_dir=tmp_path,
        obs_dim=72,
        hidden_dim=4,
        act_dim=3,
    )

    assert (tmp_path / "old_key_preference_corpus.npz").exists()
    assert (tmp_path / "old_key_preference_corpus.csv").exists()
    assert summary["contract"]["rows"] == 2
    assert summary["actor_inputs_changed"] is False
    assert summary["ppo_or_actor_update_run"] is False


def test_validation_rejects_nonfinite_actor_input():
    arrays = old_key_preference_arrays([_example()])
    arrays["observation"][0, 0] = np.nan

    with pytest.raises(ValueError, match="observation must be finite"):
        validate_old_key_preference_arrays(arrays, obs_dim=72, hidden_dim=4, act_dim=3)
