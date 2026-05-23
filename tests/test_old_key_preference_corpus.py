import numpy as np
import pytest

from autodrift.old_key_preference_corpus import (
    load_hard_row_overlay,
    old_key_case_id,
    old_key_preference_arrays,
    old_key_preference_metadata,
    old_key_preference_weight,
    validate_old_key_preference_arrays,
    write_old_key_preference_corpus,
)


def _example(row_id=0, target_index=0):
    return {
        "row_id": row_id,
        "case_id": f"case-{row_id}|8.000000|1.500000|1.000000",
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
    assert "hard_row" not in arrays
    assert "gap_tail_row" not in arrays


def test_hard_row_arrays_are_optional_and_validated():
    hard = _example(1, 0)
    hard.update(
        {
            "hard_row": True,
            "hard_weight_multiplier": 8.0,
            "preferred_branch_weight_multiplier": 1.0,
            "wrong_branch_weight_multiplier": 16.0,
        }
    )
    arrays = old_key_preference_arrays([_example(0, 0), hard])
    contract = validate_old_key_preference_arrays(arrays, obs_dim=72, hidden_dim=4, act_dim=3)

    assert contract.rows == 2
    assert arrays["hard_row"].tolist() == [0, 1]
    assert arrays["gap_tail_row"].tolist() == [0, 0]
    assert arrays["preferred_branch_weight"].tolist() == [1.0, 1.0]
    assert arrays["wrong_branch_weight"].tolist() == [1.0, 16.0]


def test_gap_tail_arrays_are_optional_and_validated():
    tail = _example(1, 0)
    tail.update(
        {
            "gap_tail_row": True,
            "gap_weight_multiplier": 4.0,
            "preferred_branch_weight_multiplier": 7.4,
            "wrong_branch_weight_multiplier": 4.0,
        }
    )
    arrays = old_key_preference_arrays([_example(0, 0), tail])
    contract = validate_old_key_preference_arrays(arrays, obs_dim=72, hidden_dim=4, act_dim=3)

    assert contract.rows == 2
    assert arrays["hard_row"].tolist() == [0, 0]
    assert arrays["gap_tail_row"].tolist() == [0, 1]
    assert arrays["preferred_branch_weight"].tolist() == pytest.approx([1.0, 7.4])
    assert arrays["wrong_branch_weight"].tolist() == [1.0, 4.0]


def test_metadata_drops_tensor_payloads():
    metadata = old_key_preference_metadata([_example()])

    assert "observation" not in metadata.columns
    assert "preferred_hidden" not in metadata.columns
    assert metadata.loc[0, "student_input_contract"] == "observation plus deployable recurrent hidden states"


def test_hard_row_overlay_loader_and_case_id(tmp_path):
    overlay = tmp_path / "overlay.csv"
    overlay.write_text(
        "\n".join(
            [
                "case_id,hard_row,hard_row_reason,hard_weight_multiplier,wrong_branch_weight_multiplier,preferred_branch_weight_multiplier,reference_wrong_history_margin,candidate_wrong_history_margin,candidate_accepted_regression",
                "case-1|8.000000|1.500000|1.000000,true,wrong_history_margin_sign_crossing,8,16,1,-0.1,0.01,true",
            ]
        )
        + "\n"
    )

    loaded = load_hard_row_overlay(overlay)

    assert old_key_case_id(_example(1)) == "case-1|8.000000|1.500000|1.000000"
    assert loaded["case-1|8.000000|1.500000|1.000000"]["hard_row"] is True
    assert loaded["case-1|8.000000|1.500000|1.000000"]["wrong_branch_weight_multiplier"] == 16.0


def test_gap_tail_overlay_loader_accepts_gap_only_schema(tmp_path):
    overlay = tmp_path / "overlay.csv"
    overlay.write_text(
        "\n".join(
            [
                "case_id,gap_tail_row,gap_tail_reason,gap_weight_multiplier,normal_branch_weight_multiplier,wrong_branch_weight_multiplier,reference_policy,candidate_policy,reference_margin_gap,candidate_margin_gap,candidate_gap_delta,candidate_normal_delta,candidate_wrong_delta,target_gap_delta_floor,target_gap_delta_buffer,candidate_gap_p10_regression",
                "case-1|8.000000|1.500000|1.000000,true,gap_p10_tail,4,7.4,4,m369hr_a400,m369hr_a600,0.021,0.020,-0.001,-0.0008,0.0002,-0.0005,0.0001,true",
            ]
        )
        + "\n"
    )

    loaded = load_hard_row_overlay(overlay)
    row = loaded["case-1|8.000000|1.500000|1.000000"]

    assert row["hard_row"] is False
    assert row["gap_tail_row"] is True
    assert row["gap_weight_multiplier"] == 4.0
    assert row["preferred_branch_weight_multiplier"] == 7.4
    assert row["wrong_branch_weight_multiplier"] == 4.0
    assert row["candidate_gap_p10_regression"] is True


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
