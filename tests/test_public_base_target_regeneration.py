import numpy as np

from autodrift.public_base_target_regeneration import (
    action_delta_set,
    classify_target_regeneration,
    select_source_rows,
    _candidate_metrics,
)


def test_select_source_rows_respects_caps():
    rows = []
    for index in range(10):
        rows.append(
            {
                "contrast_group_id": f"g{index}",
                "source_index": index,
                "variant": "zero",
                "horizon": "6",
                "gap_deficit": 1.0 - index * 0.01,
                "normal_intervention_gap": 0.01,
                "fault_family_pair": "a->b",
                "seed": "1",
            }
        )
    selected = select_source_rows(rows, max_rows=10, per_fault_pair_cap=3, per_seed_cap=2)
    assert len(selected) == 2
    assert selected[0]["contrast_group_id"] == "g0"


def test_candidate_metrics_primary_accepts_gap_improvement():
    metrics = _candidate_metrics(
        base_action=np.asarray([0.0, 0.0, 0.0], dtype=np.float32),
        intervention_action=np.asarray([-0.01, 0.0, 0.0], dtype=np.float32),
        target_gap=0.04,
        delta_name="steer_+0.08",
        delta=np.asarray([0.08, 0.0, 0.0], dtype=np.float32),
    )
    assert metrics["accepted"] is True
    assert metrics["acceptance_class"] == "primary"
    assert metrics["low_tail_after"] is False


def test_action_delta_set_has_expected_deltas():
    names = {name for name, _delta in action_delta_set()}
    assert "steer_+0.08" in names
    assert "brake_+0.08" in names
    assert "steer_-0.08_brake_+0.08" in names


def test_classify_target_regeneration():
    assert (
        classify_target_regeneration(
            actor_parameters_changed=False,
            accepted_targets=80,
            distinct_fault_family_pairs=8,
            distinct_seeds=24,
            max_fault_family_pair_fraction=0.25,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_target_regeneration_pass"
    )
    assert (
        classify_target_regeneration(
            actor_parameters_changed=False,
            accepted_targets=10,
            distinct_fault_family_pairs=8,
            distinct_seeds=24,
            max_fault_family_pair_fraction=0.1,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_target_regeneration_too_few_targets"
    )
