import torch

from autodrift.v4_adaptive_primary_residual_calibration import (
    classify_v4_adaptive_primary_residual_calibration,
    make_source_heldout_split,
    train_identity_calibrator,
)


def _row(index: int, *, axis: str = "obstacle_lateral_offset", fault_pair: str = "pair0"):
    return {
        "candidate_id": str(index),
        "source_group_id": str(index),
        "seed": str(78048 + index % 6),
        "fault_family_pair": fault_pair,
        "boundary_axis": axis,
        "warmup_mode": "natural_policy" if index % 2 == 0 else "brake_tap",
        "source_index": str(index),
        "min_clearance_margin": "0.00002",
    }


def test_make_source_heldout_split_is_source_group_disjoint_and_diverse():
    rows = []
    axes = ["obstacle_lateral_offset", "obstacle_timing", "obstacle_half_width"]
    pairs = ["pair0", "pair1", "pair2", "pair3"]
    for index in range(36):
        rows.append(_row(index, axis=axes[index % len(axes)], fault_pair=pairs[index % len(pairs)]))

    split_rows, summary = make_source_heldout_split(
        rows,
        holdout_fraction=0.3,
        min_holdout_rows=8,
        min_holdout_axes=2,
        min_holdout_fault_pairs=3,
    )
    assert summary["split_valid"] is True
    train_groups = {row["source_group_id"] for row in split_rows if row["split"] == "train"}
    holdout_groups = {row["source_group_id"] for row in split_rows if row["split"] == "holdout"}
    assert train_groups
    assert holdout_groups
    assert train_groups.isdisjoint(holdout_groups)
    assert summary["holdout"]["unique_boundary_axes"] >= 2
    assert summary["holdout"]["unique_fault_family_pairs"] >= 3


def test_train_identity_calibrator_stays_near_target_gate():
    features = torch.randn(12, 5)
    calibrator, history = train_identity_calibrator(
        features,
        output_dim=1,
        initial_gate=0.99,
        target_gate=0.99,
        epochs=4,
        lr=1e-3,
        seed=1,
    )
    with torch.no_grad():
        gate = calibrator(features)
    assert history
    assert float(gate.mean()) > 0.98
    assert gate.shape == (12, 1)


def test_classify_calibration_candidate_and_failures():
    assert (
        classify_v4_adaptive_primary_residual_calibration(
            split_valid=True,
            actor_changed=False,
            residual_changed=False,
            optimizer_updates_only_calibrator=True,
            train_normal_pass=True,
            holdout_normal_pass=True,
            train_intervention_pass=True,
            holdout_intervention_pass=True,
            old_behavior_pass=True,
            ppo_used=False,
            promoted=False,
        )
        == "v4_adaptive_primary_residual_calibration_candidate"
    )
    assert (
        classify_v4_adaptive_primary_residual_calibration(
            split_valid=True,
            actor_changed=False,
            residual_changed=False,
            optimizer_updates_only_calibrator=True,
            train_normal_pass=True,
            holdout_normal_pass=False,
            train_intervention_pass=True,
            holdout_intervention_pass=True,
            old_behavior_pass=True,
            ppo_used=False,
            promoted=False,
        )
        == "v4_adaptive_primary_residual_calibration_objective_overfit"
    )
    assert (
        classify_v4_adaptive_primary_residual_calibration(
            split_valid=True,
            actor_changed=True,
            residual_changed=False,
            optimizer_updates_only_calibrator=True,
            train_normal_pass=True,
            holdout_normal_pass=True,
            train_intervention_pass=True,
            holdout_intervention_pass=True,
            old_behavior_pass=True,
            ppo_used=False,
            promoted=False,
        )
        == "v4_adaptive_primary_residual_calibration_contract_violation"
    )
