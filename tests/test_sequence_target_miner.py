from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from autodrift.sequence_target_miner import (
    build_sequence_candidates,
    parse_int_list,
    sequence_acceptance,
    sequence_scales,
    sequence_trust_metrics,
    select_best_sequence,
    write_sequence_target_corpus,
)


def test_sequence_scales_defines_design_lengths():
    assert sequence_scales(3, "decay_pulse").tolist() == [1.0, 0.5, 0.25]
    assert sequence_scales(5, "decay_pulse").tolist() == [1.0, 0.699999988079071, 0.44999998807907104, 0.25, 0.0]
    assert sequence_scales(4, "constant_delta").tolist() == [1.0, 1.0, 1.0, 1.0]


def test_sequence_trust_metrics_reports_mean_max_and_smoothness():
    base = np.zeros((3, 3), dtype=np.float32)
    actions = np.asarray(
        [
            [0.04, 0.0, 0.0],
            [0.04, 0.0, 0.04],
            [0.0, 0.0, 0.04],
        ],
        dtype=np.float32,
    )

    mean_l2, max_l2, max_delta_delta = sequence_trust_metrics(
        action_sequence=actions,
        base_action_sequence=base,
    )

    assert mean_l2 == pytest.approx((0.04 + np.sqrt(0.04**2 + 0.04**2) + 0.04) / 3)
    assert max_l2 == pytest.approx(np.sqrt(0.04**2 + 0.04**2))
    assert max_delta_delta == pytest.approx(0.04)


def test_build_sequence_candidates_marks_trust_region():
    base = np.zeros((3, 3), dtype=np.float32)

    candidates = build_sequence_candidates(
        base,
        steer_deltas=(0.08,),
        throttle_deltas=(0.0,),
        brake_deltas=(0.0,),
        families=("constant_delta", "decay_pulse"),
        per_step_action_l2=0.10,
        sequence_mean_l2_limit=0.08,
        sequence_max_l2_limit=0.10,
        max_delta_delta_l2_limit=0.08,
    )

    assert len(candidates) == 2
    assert {candidate.family for candidate in candidates} == {"constant_delta", "decay_pulse"}
    assert all(candidate.trust_region_ok for candidate in candidates)


def test_build_sequence_candidates_includes_structured_families():
    base = np.zeros((5, 3), dtype=np.float32)

    candidates = build_sequence_candidates(
        base,
        steer_deltas=(-0.04, 0.0, 0.04),
        throttle_deltas=(0.0,),
        brake_deltas=(-0.04, 0.0, 0.04),
        families=("brake_release_then_steer", "steer_then_brake"),
        per_step_action_l2=0.10,
        sequence_mean_l2_limit=0.08,
        sequence_max_l2_limit=0.10,
        max_delta_delta_l2_limit=0.08,
    )

    families = {candidate.family for candidate in candidates}
    assert families == {"brake_release_then_steer", "steer_then_brake"}
    assert all(candidate.action_sequence.shape == (5, 3) for candidate in candidates)


def test_sequence_acceptance_rejects_trust_and_accepts_margin():
    baseline = {"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": 0.1}
    improved = {"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": 0.13}

    accepted, reason = sequence_acceptance(
        candidate=improved,
        baseline=baseline,
        trust_region_ok=True,
        min_margin_improvement=0.02,
        min_risk_improvement=0.05,
    )
    assert accepted
    assert reason == "margin_improved"

    accepted, reason = sequence_acceptance(
        candidate=improved,
        baseline=baseline,
        trust_region_ok=False,
        min_margin_improvement=0.02,
        min_risk_improvement=0.05,
    )
    assert not accepted
    assert reason == "outside_sequence_trust_region"


def test_sequence_acceptance_allows_collision_avoidance():
    baseline = {"collision": True, "off_road": False, "spin_out": False, "min_clearance_margin": -0.2}
    recovered = {"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": -0.3}

    accepted, reason = sequence_acceptance(
        candidate=recovered,
        baseline=baseline,
        trust_region_ok=True,
        min_margin_improvement=1.0,
        min_risk_improvement=100.0,
    )

    assert accepted
    assert reason == "baseline_collision_avoided"


def test_select_best_sequence_prefers_accepted_margin():
    best = select_best_sequence(
        [
            {"accepted": False, "margin_improvement": 1.0, "risk_improvement": 1.0, "sequence_mean_l2": 0.01},
            {"accepted": True, "margin_improvement": 0.02, "risk_improvement": 0.0, "sequence_mean_l2": 0.01},
            {"accepted": True, "margin_improvement": 0.05, "risk_improvement": 0.0, "sequence_mean_l2": 0.03},
        ]
    )

    assert best is not None
    assert best["margin_improvement"] == 0.05


def test_write_sequence_target_corpus_pads_variable_lengths(tmp_path: Path):
    output = tmp_path / "sequence_target_corpus.npz"

    write_sequence_target_corpus(
        output_npz=output,
        observations=[np.zeros(72, dtype=np.float32), np.ones(72, dtype=np.float32)],
        normal_hidden=[np.zeros(16, dtype=np.float32), np.ones(16, dtype=np.float32)],
        variant_hidden=[np.ones(16, dtype=np.float32), np.full(16, 2.0, dtype=np.float32)],
        target_action_sequences=[
            np.ones((3, 3), dtype=np.float32),
            np.full((5, 3), 2.0, dtype=np.float32),
        ],
        normal_base_action_sequences=[
            np.zeros((3, 3), dtype=np.float32),
            np.ones((5, 3), dtype=np.float32),
        ],
        variant_base_actions=[np.zeros(3, dtype=np.float32), np.ones(3, dtype=np.float32)],
        weights=[1.0, 2.0],
        row_ids=[0, 1],
        source_indices=[10, 11],
        sequence_lengths=[3, 5],
    )

    data = np.load(output)
    assert data["target_action_sequence"].shape == (2, 5, 3)
    assert data["normal_base_action_sequence"].shape == (2, 5, 3)
    assert data["sequence_mask"].tolist() == [[1, 1, 1, 0, 0], [1, 1, 1, 1, 1]]
    assert data["sequence_length"].tolist() == [3, 5]


def test_parse_int_list_rejects_empty():
    assert parse_int_list("3,5") == (3, 5)
    with pytest.raises(Exception, match="at least one"):
        parse_int_list("")
