from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from autodrift.grounded_capability_action_target_miner import (
    SurfaceConfig,
    candidate_acceptance,
    parse_surface_config,
    request_steps_for_target_rows,
    risk_score,
    select_best_candidate,
    select_grounding_source_rows,
    source_diversity_weights,
    write_target_corpus,
)


def test_risk_score_penalizes_failures_and_rewards_margin():
    safe = {"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": 0.5}
    collision = {"collision": True, "off_road": False, "spin_out": False, "min_clearance_margin": 0.5}
    low_margin = {"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": -0.2}

    assert risk_score(safe) < risk_score(low_margin)
    assert risk_score(collision) > risk_score(safe)


def test_candidate_acceptance_requires_trust_region_and_grounded_improvement():
    baseline = {"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": 0.1}
    improved = {"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": 0.13}

    accepted, reason = candidate_acceptance(
        candidate=improved,
        baseline=baseline,
        action_l2=0.04,
        min_margin_improvement=0.02,
        min_risk_improvement=0.05,
        max_action_l2=0.10,
    )

    assert accepted
    assert reason == "margin_improved"

    accepted, reason = candidate_acceptance(
        candidate=improved,
        baseline=baseline,
        action_l2=0.11,
        min_margin_improvement=0.02,
        min_risk_improvement=0.05,
        max_action_l2=0.10,
    )

    assert not accepted
    assert reason == "outside_action_trust_region"


def test_candidate_acceptance_allows_baseline_collision_avoidance():
    baseline = {"collision": True, "off_road": False, "spin_out": False, "min_clearance_margin": -0.5}
    recovered = {"collision": False, "off_road": False, "spin_out": False, "min_clearance_margin": -0.4}

    accepted, reason = candidate_acceptance(
        candidate=recovered,
        baseline=baseline,
        action_l2=0.02,
        min_margin_improvement=0.2,
        min_risk_improvement=20.0,
        max_action_l2=0.10,
    )

    assert accepted
    assert reason == "baseline_collision_avoided"


def test_select_grounding_source_rows_filters_supported_candidates_and_caps_groups():
    rows = pd.DataFrame(
        [
            _source_row(surface="ood", variant="wrong_matched_history", target="future_yaw_response", z=3.0, gap=2.0),
            _source_row(surface="ood", variant="wrong_matched_history", target="future_yaw_response", z=2.0, gap=5.0),
            _source_row(surface="fresh", variant="delayed_history", target="future_braking_deceleration", z=4.0, gap=1.0),
            _source_row(surface="fresh", variant="shuffled_history", target="future_yaw_response", z=10.0, gap=10.0),
            {
                **_source_row(
                    surface="ood",
                    variant="wrong_matched_history",
                    target="future_lateral_accel_response",
                    z=99.0,
                    gap=99.0,
                ),
                "candidate_for_grounding": False,
            },
        ]
    )

    selected = select_grounding_source_rows(
        rows,
        include_variants=("wrong_matched_history", "delayed_history"),
        max_rows_per_surface_variant_target=1,
        max_total_rows=4,
    )

    assert selected["variant"].tolist() == ["wrong_matched_history", "delayed_history"]
    assert selected["surface"].tolist() == ["ood", "fresh"]
    assert selected["capability_z_distance"].tolist() == [3.0, 4.0]


def test_request_steps_for_target_rows_includes_variant_sources():
    rows = pd.DataFrame(
        [
            _source_row("fresh", "wrong_matched_history", "future_yaw_response", 1.0, 1.0, left_step=7, right_step=4),
            _source_row("fresh", "delayed_history", "future_yaw_response", 1.0, 1.0, left_step=2, right_step=9),
        ]
    )

    requests = request_steps_for_target_rows(rows, delay_steps=3)

    assert requests[100] == {0, 2, 7}
    assert requests[200] == {4}


def test_select_best_candidate_prefers_accepted_margin_then_small_action():
    best = select_best_candidate(
        [
            {"accepted": False, "margin_improvement": 10.0, "risk_improvement": 10.0, "action_l2": 0.01},
            {"accepted": True, "margin_improvement": 0.02, "risk_improvement": 0.1, "action_l2": 0.02},
            {"accepted": True, "margin_improvement": 0.05, "risk_improvement": 0.0, "action_l2": 0.08},
        ]
    )

    assert best is not None
    assert best["margin_improvement"] == 0.05


def test_source_diversity_weights_downweights_duplicate_source_group():
    rows = [
        {"source_index": 0, "left_seed": 1, "variant": "wrong_matched_history", "target": "future_yaw_response"},
        {"source_index": 1, "left_seed": 1, "variant": "wrong_matched_history", "target": "future_yaw_response"},
        {"source_index": 2, "left_seed": 2, "variant": "delayed_history", "target": "future_yaw_response"},
    ]

    weights = source_diversity_weights(rows)

    assert weights[0] == pytest.approx(1.0 / np.sqrt(2.0))
    assert weights[1] == pytest.approx(1.0 / np.sqrt(2.0))
    assert weights[2] == pytest.approx(1.0)


def test_write_target_corpus_writes_expected_arrays(tmp_path: Path):
    output = tmp_path / "target_corpus.npz"

    write_target_corpus(
        output_npz=output,
        observations=[np.zeros(72, dtype=np.float32)],
        normal_hidden=[np.ones(16, dtype=np.float32)],
        variant_hidden=[np.full(16, 2.0, dtype=np.float32)],
        target_actions=[np.asarray([0.1, 0.0, 0.2], dtype=np.float32)],
        normal_base_actions=[np.zeros(3, dtype=np.float32)],
        variant_base_actions=[np.ones(3, dtype=np.float32)],
        weights=[1.5],
        row_ids=[7],
        source_indices=[9],
    )

    data = np.load(output)
    assert data["observation"].shape == (1, 72)
    assert data["normal_hidden"].shape == (1, 16)
    assert data["target_action"].tolist() == [[pytest.approx(0.1), 0.0, pytest.approx(0.2)]]
    assert data["weight"].tolist() == [pytest.approx(1.5)]
    assert data["row_id"].tolist() == [7]
    assert data["source_index"].tolist() == [9]


def test_parse_surface_config_requires_surface_name_and_path():
    parsed = parse_surface_config("ood=configs/eval.json")

    assert parsed == SurfaceConfig(surface="ood", env_config_path=Path("configs/eval.json"))
    with pytest.raises(Exception, match="SURFACE=PATH"):
        parse_surface_config("configs/eval.json")


def _source_row(
    surface: str,
    variant: str,
    target: str,
    z: float,
    gap: float,
    *,
    left_step: int = 5,
    right_step: int = 6,
) -> dict[str, object]:
    return {
        "candidate_for_grounding": True,
        "surface": surface,
        "variant": variant,
        "target": target,
        "capability_z_distance": z,
        "action_distance": 0.001,
        "coupling_gap": gap,
        "left_seed": 100,
        "left_step": left_step,
        "right_seed": 200,
        "right_step": right_step,
    }
