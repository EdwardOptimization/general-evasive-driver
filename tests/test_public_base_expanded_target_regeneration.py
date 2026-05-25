import numpy as np

from autodrift.public_base_expanded_target_regeneration import (
    build_expanded_source_candidates,
    classify_expanded_target_regeneration,
    select_expanded_source_rows,
    _expanded_candidate_metrics,
)


def _row(index, *, seed="1", pair="a->b", alpha="0.02", gap="0.02", deficit="0.02"):
    return {
        "contrast_group_id": f"g{index}",
        "source_index": str(index),
        "variant": "zero_command_obs",
        "horizon": "6",
        "seed": str(seed),
        "fault_family_pair": pair,
        "alpha": alpha,
        "normal_intervention_gap": gap,
        "gap_deficit": deficit,
    }


def test_build_expanded_source_candidates_labels_strict_and_near_tail():
    objective_rows = [
        _row(0, seed=1, gap="0.010", deficit="0.020"),
        _row(1, seed=2, gap="0.050", deficit="0.013"),
        _row(2, seed=3, gap="0.050", deficit="0.001"),
    ]
    low_tail_rows = [_row(0, seed=1)]
    candidates, rejected = build_expanded_source_candidates(objective_rows=objective_rows, low_tail_rows=low_tail_rows)
    assert len(candidates) == 2
    labels = {row["contrast_group_id"]: row["source_label"] for row in candidates}
    assert labels["g0"] == "strict_low_tail"
    assert labels["g1"] == "near_tail_coverage"
    assert rejected[0]["source_rejection_reason"] == "not_strict_or_near_tail"


def test_select_expanded_source_rows_preserves_seed_and_pair_caps():
    rows = []
    for index in range(20):
        rows.append(
            {
                **_row(index, seed=index // 2, pair=f"p{index % 3}", deficit=str(1.0 - index * 0.01)),
                "strict_low_tail": index < 8,
                "source_label": "strict_low_tail" if index < 8 else "near_tail_coverage",
            }
        )
    selected = select_expanded_source_rows(rows, max_rows=12, per_fault_pair_cap=5, per_seed_soft_cap=2)
    assert len(selected) == 12
    assert len({row["seed"] for row in selected}) >= 6
    assert max(sum(1 for row in selected if row["fault_family_pair"] == pair) for pair in {"p0", "p1", "p2"}) <= 5


def test_expanded_candidate_metrics_accepts_near_tail_no_worse_deficit():
    metrics = _expanded_candidate_metrics(
        base_action=np.asarray([0.0, 0.0, 0.0], dtype=np.float32),
        intervention_action=np.asarray([-0.01, 0.0, 0.0], dtype=np.float32),
        target_gap=0.04,
        delta_name="steer_+0.08",
        delta=np.asarray([0.08, 0.0, 0.0], dtype=np.float32),
        source_label="near_tail_coverage",
    )
    assert metrics["accepted"] is True
    assert metrics["acceptance_class"] == "expanded_primary"


def test_classify_expanded_target_regeneration():
    assert (
        classify_expanded_target_regeneration(
            actor_parameters_changed=False,
            accepted_targets=96,
            strict_low_tail_accepted_targets=60,
            distinct_fault_family_pairs=10,
            distinct_seeds=24,
            max_fault_family_pair_fraction=0.25,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_expanded_target_regeneration_pass"
    )
    assert (
        classify_expanded_target_regeneration(
            actor_parameters_changed=False,
            accepted_targets=96,
            strict_low_tail_accepted_targets=20,
            distinct_fault_family_pairs=10,
            distinct_seeds=24,
            max_fault_family_pair_fraction=0.25,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_expanded_target_regeneration_strict_low_tail_sparse"
    )
