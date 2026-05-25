from autodrift.v4_adaptive_primary_calibration_grid import (
    FixedResidualGate,
    build_gate_candidates,
    classify_v4_adaptive_primary_calibration_grid,
    merge_accepted_rows_with_split,
    select_train_candidate,
)


def test_fixed_residual_gate_emits_constant_vector():
    import torch

    gate = FixedResidualGate((0.25, 0.5, 0.75))
    out = gate(torch.randn(4, 9))

    assert out.shape == (4, 3)
    assert torch.allclose(out[:, 0], torch.ones(4) * 0.25)
    assert torch.allclose(out[:, 1], torch.ones(4) * 0.5)
    assert torch.allclose(out[:, 2], torch.ones(4) * 0.75)
    assert sum(parameter.numel() for parameter in gate.parameters()) == 0


def test_build_gate_candidates_includes_identity_and_nonduplicates():
    candidates = build_gate_candidates(include_vector_grid=True)
    ids = [candidate["gate_candidate_id"] for candidate in candidates]
    tuples = [
        (candidate["steer_gate"], candidate["throttle_gate"], candidate["brake_gate"])
        for candidate in candidates
    ]

    assert ids[0] == "identity"
    assert (1.0, 1.0, 1.0) in tuples
    assert (0.0, 0.0, 1.0) in tuples
    assert len(ids) == len(set(ids))
    assert len(tuples) == len(set(tuples))


def test_merge_accepted_rows_with_split_preserves_target_fields_and_disjoint_split():
    accepted_rows = [
        {"candidate_id": "1", "source_group_id": "a", "target_obstacle_body_x": "10"},
        {"candidate_id": "2", "source_group_id": "b", "target_obstacle_body_x": "11"},
    ]
    split_rows = [
        {"candidate_id": "1", "split": "train", "split_unit": "a|seed|pair", "source_group_id": "a"},
        {"candidate_id": "2", "split": "holdout", "split_unit": "b|seed|pair", "source_group_id": "b"},
    ]

    merged, summary = merge_accepted_rows_with_split(accepted_rows, split_rows)

    assert summary["merged_rows"] == 2
    assert summary["source_group_disjoint"] is True
    assert merged[0]["target_obstacle_body_x"] == "10"
    assert merged[1]["split"] == "holdout"


def test_select_train_candidate_prefers_margin_lift_and_identity_tie_safety():
    metrics = [
        {
            "gate_candidate_id": "identity",
            "family": "identity",
            "split": "train",
            "selection_pass": True,
            "normal_margin_lift_p05": 0.0,
            "normal_margin_lift_mean": 0.0,
            "calibrated_intervention_collision_rate": 0.7,
            "action_drift_mean": 0.0,
        },
        {
            "gate_candidate_id": "scalar_low",
            "family": "fixed_scalar",
            "split": "train",
            "selection_pass": True,
            "normal_margin_lift_p05": 0.00001,
            "normal_margin_lift_mean": 0.00002,
            "calibrated_intervention_collision_rate": 0.7,
            "action_drift_mean": 0.001,
        },
    ]

    selected, updated = select_train_candidate(metrics)

    assert selected is not None
    assert selected["gate_candidate_id"] == "scalar_low"
    ranks = {row["gate_candidate_id"]: row["train_rank"] for row in updated}
    assert ranks["scalar_low"] == 1
    assert ranks["identity"] == 2


def test_classify_grid_result_classes():
    common = dict(
        actor_changed=False,
        residual_changed=False,
        trained_adaptive_calibrator=False,
        ppo_used=False,
        promoted=False,
        train_selection_pass=True,
        holdout_normal_pass=True,
        holdout_intervention_pass=True,
        holdout_old_behavior_pass=True,
        holdout_acceptance_pass=True,
        selected_strong_candidate=True,
    )

    assert (
        classify_v4_adaptive_primary_calibration_grid(
            **common,
            selected_family="fixed_scalar",
        )
        == "v4_adaptive_primary_calibration_fixed_scalar_candidate"
    )
    intervention_washout = {**common, "holdout_intervention_pass": False}
    assert (
        classify_v4_adaptive_primary_calibration_grid(
            **intervention_washout,
            selected_family="fixed_vector",
        )
        == "v4_adaptive_primary_calibration_intervention_washout"
    )
    contract_violation = {**common, "actor_changed": True}
    assert (
        classify_v4_adaptive_primary_calibration_grid(
            **contract_violation,
            selected_family="fixed_vector",
        )
        == "v4_adaptive_primary_calibration_contract_violation"
    )
    identity_only = {**common, "selected_strong_candidate": False}
    assert (
        classify_v4_adaptive_primary_calibration_grid(
            **identity_only,
            selected_family="identity",
        )
        == "v4_adaptive_primary_calibration_identity_only"
    )
