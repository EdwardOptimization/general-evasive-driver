from __future__ import annotations

from autodrift.capability_separable_source_constructor import (
    build_short_sequence_candidates,
    build_trajectory_proposal_candidates,
    classify_capability_separable_result,
    evaluate_action_separability,
    fine_relocation_geometry_candidates,
    viability_band_geometry_candidates,
)
from autodrift.matched_history_outcome_gate import OutcomeSnapshot

import numpy as np
import torch


def _row(condition: str, candidate_id: int, steer: float, margin: float, success: bool = True):
    return {
        "condition": condition,
        "candidate_id": candidate_id,
        "candidate_steer": steer,
        "candidate_throttle": 0.0,
        "candidate_brake": 0.0,
        "action_l2_from_shared_base": abs(steer),
        "min_clearance_margin": margin,
        "success": success,
        "collision": not success,
    }


def test_evaluate_action_separability_accepts_cross_regret():
    result = evaluate_action_separability(
        pair_id=7,
        candidate_rows=[
            _row("A", 0, -0.2, 0.10),
            _row("A", 1, 0.2, 0.02),
            _row("B", 0, -0.2, 0.01),
            _row("B", 1, 0.2, 0.11),
        ],
        min_best_action_l2=0.25,
        min_cross_regret_margin=0.05,
    )

    assert result["accepted"]
    assert result["best_candidate_A"] == 0
    assert result["best_candidate_B"] == 1
    assert result["cross_regret_A"] > 0.05
    assert result["cross_regret_B"] > 0.05


def test_evaluate_action_separability_rejects_low_regret():
    result = evaluate_action_separability(
        pair_id=8,
        candidate_rows=[
            _row("A", 0, -0.2, 0.10),
            _row("A", 1, 0.2, 0.09),
            _row("B", 0, -0.2, 0.09),
            _row("B", 1, 0.2, 0.10),
        ],
        min_best_action_l2=0.25,
        min_cross_regret_margin=0.05,
    )

    assert not result["accepted"]
    assert result["rejection_reason"] == "insufficient_cross_regret"


def test_classify_capability_separable_result():
    assert (
        classify_capability_separable_result(
            matched_pair_count=0,
            action_rollouts=0,
            accepted_separable_pairs=0,
            best_actions_diverged_pairs=0,
            low_regret_pairs=0,
        )
        == "matched_state_empty"
    )
    assert (
        classify_capability_separable_result(
            matched_pair_count=10,
            action_rollouts=100,
            accepted_separable_pairs=1,
            best_actions_diverged_pairs=1,
            low_regret_pairs=0,
        )
        == "capability_separable_signal"
    )
    assert (
        classify_capability_separable_result(
            matched_pair_count=10,
            action_rollouts=100,
            accepted_separable_pairs=0,
            best_actions_diverged_pairs=3,
            low_regret_pairs=3,
        )
        == "action_divergent_low_regret"
    )


def test_build_short_sequence_candidates_uses_shared_base_and_deduplicates():
    candidates = build_short_sequence_candidates(
        [0.0, 0.1, 0.2],
        sequence_length=3,
        template_set="steer_brake_pulses",
    )

    assert candidates
    ids = [candidate["candidate_id"] for candidate in candidates]
    assert ids == list(range(len(ids)))
    assert len({tuple(candidate["candidate_vector"].tolist()) for candidate in candidates}) == len(candidates)
    for candidate in candidates:
        assert candidate["sequence"].shape == (3, 3)
        assert candidate["candidate_vector"].shape == (9,)
        assert candidate["action_l2_from_shared_base"] >= 0.0


class _DummyScenario:
    obstacle_half_width = 0.7


class _DummyEnv:
    obstacle_scenario = _DummyScenario()
    obstacle_position = np.asarray([10.0, 1.0], dtype=np.float64)

    def _body_point(self, point):
        return np.asarray(point, dtype=np.float64)


def test_viability_band_geometry_candidates_targets_half_width():
    snapshot = OutcomeSnapshot(
        seed=1,
        step=2,
        observation=np.zeros(72, dtype=np.float32),
        hidden=torch.zeros(1, 8),
        env=_DummyEnv(),
        info={},
    )

    candidates = viability_band_geometry_candidates(
        snapshot,
        pair_min_best_margin=2.0,
        target_min_best_margin=0.02,
        target_max_best_margin=0.5,
    )

    assert candidates
    assert any(candidate["half_width"] > 1.0 for candidate in candidates)
    assert all(candidate["body_x"] > 0.0 for candidate in candidates)


def test_fine_relocation_geometry_candidates_refines_width_and_lateral_offset():
    candidates = fine_relocation_geometry_candidates(
        {"body_x": 8.0, "body_y": -0.5, "half_width": 0.3},
        half_width_deltas=(-0.02, 0.02),
        body_y_offsets=(-0.1, 0.1),
    )

    assert candidates
    assert any(abs(candidate["half_width"] - 0.28) < 1e-6 for candidate in candidates)
    assert any(abs(candidate["body_y"] - -0.6) < 1e-6 for candidate in candidates)
    assert len({(candidate["body_x"], candidate["body_y"], candidate["half_width"]) for candidate in candidates}) == len(
        candidates
    )


def test_build_trajectory_proposal_candidates_includes_branch_origins():
    candidates = build_trajectory_proposal_candidates(
        np.asarray([0.1, 0.0, 0.2], dtype=np.float32),
        np.asarray([-0.1, 0.0, 0.4], dtype=np.float32),
        np.asarray([0.0, 0.0, 0.3], dtype=np.float32),
        sequence_length=4,
        proposal_count_per_condition=3,
        proposal_seed=7,
        steer_scale=0.2,
        throttle_scale=0.1,
        brake_scale=0.2,
    )

    assert candidates
    assert {"A", "B", "shared"}.issubset({candidate["candidate_origin"] for candidate in candidates})
    assert len({tuple(candidate["candidate_vector"].tolist()) for candidate in candidates}) == len(candidates)
    for candidate in candidates:
        assert candidate["sequence"].shape == (4, 3)
        assert candidate["candidate_vector"].shape == (12,)
        assert candidate["action_l2_from_shared_base"] >= 0.0
