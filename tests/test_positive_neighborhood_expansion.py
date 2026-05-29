import pandas as pd

from autodrift.positive_neighborhood_expansion import (
    anchor_target_grid,
    generate_positive_neighborhood_proposals,
    positive_anchor_rows,
    select_positive_neighborhood_candidates,
)


def _anchor():
    return {
        "source_index": 24,
        "seed": 141901,
        "reveal_step": 48,
        "candidate_step": 24,
        "candidate_step_column": "source_step",
        "preferred_fault": "brake_fade_pre_emergency",
        "wrong_fault": "heavy_front_payload_preexisting",
        "capability_pair": "brake_authority_drop->mass_cg_shift",
        "preferred_reveal_bucket": "vx6|yaw-2|steer-4|ox0|oy0",
        "variant": "warmup_removed",
        "history_positive": True,
        "control_positive": False,
        "normal_margin": 0.8,
        "variant_margin": 0.7,
        "margin_gap": 0.03,
        "sequence_action_l2_mean": 0.2,
        "source_body_x": 9.5,
        "source_body_y": -1.2,
        "source_half_width": 0.9,
        "relocated_body_x": 15.5,
        "relocated_body_y": -0.8,
        "relocated_half_width": 1.1,
        "relocation_key": "x=15.500|y=-0.800|w=1.100",
    }


def _base(seed: int, pair: str, variant: str = "warmup_removed", bucket: str | None = None):
    return {
        "source_index": seed % 100,
        "seed": seed,
        "reveal_step": 48,
        "source_step": 24,
        "candidate_step": 24,
        "candidate_step_column": "source_step",
        "preferred_fault": "brake_fade_pre_emergency",
        "wrong_fault": "heavy_front_payload_preexisting",
        "capability_pair": pair,
        "preferred_reveal_bucket": bucket or f"bucket-{seed}",
        "variant": variant,
        "sequence_action_l2_mean": 0.2 + 0.001 * (seed % 10),
        "margin_gap": 0.0,
        "source_body_x": 8.0 + (seed % 3),
        "source_body_y": -1.0,
        "source_half_width": 0.8,
    }


def test_positive_anchor_rows_excludes_control_positives():
    rows = pd.DataFrame(
        [
            _anchor(),
            {**_anchor(), "control_positive": True},
            {**_anchor(), "history_positive": False},
        ]
    )

    anchors = positive_anchor_rows(rows)

    assert len(anchors) == 1
    assert not bool(anchors.iloc[0]["control_positive"])


def test_anchor_target_grid_builds_local_offsets():
    targets = anchor_target_grid(_anchor())

    assert any(row["exact_anchor_target"] for row in targets)
    assert any(row["target_body_x"] > 15.5 for row in targets)
    assert any(row["target_body_y"] < -0.8 for row in targets)
    assert any(row["target_half_width"] > 1.1 for row in targets)


def test_generate_positive_neighborhood_proposals_preserves_source_step_and_controls():
    anchors = pd.DataFrame([_anchor()])
    controls = pd.DataFrame([{**_anchor(), "variant": "zero_current_response", "control_positive": True}])
    pool = pd.DataFrame(
        [
            _base(141901, "brake_authority_drop->mass_cg_shift", bucket="vx6|yaw-2|steer-4|ox0|oy0"),
            _base(141902, "front_lateral_authority_drop->mass_cg_shift", variant="warmup_shortened_8"),
        ]
    )

    proposals = generate_positive_neighborhood_proposals(
        history_positive_rows=anchors,
        control_positive_rows=controls,
        candidate_pool=pool,
    )

    assert len(proposals) > 0
    assert set(proposals["candidate_step_column"]) == {"source_step"}
    assert set(proposals["source_step"]) == {24}
    assert set(proposals["source_group"]) == {"anchor_source", "neighbor_source"}
    assert proposals["control_positive_source"].any()
    row = proposals[proposals["seed"] == 141902].iloc[0]
    assert row["body_longitudinal_offset"] == row["target_body_x"] - row["source_body_x"]


def test_select_positive_neighborhood_candidates_applies_diversity_caps():
    anchors = pd.DataFrame([_anchor()])
    controls = pd.DataFrame([{**_anchor(), "variant": "zero_current_response", "control_positive": True}])
    pool = pd.DataFrame(
        [
            _base(141901, "brake_authority_drop->mass_cg_shift", bucket="vx6|yaw-2|steer-4|ox0|oy0"),
            _base(141902, "front_lateral_authority_drop->mass_cg_shift"),
            _base(141903, "global_mu_drop->front_lateral_authority_drop", variant="warmup_shortened_8"),
        ]
    )
    proposals = generate_positive_neighborhood_proposals(
        history_positive_rows=anchors,
        control_positive_rows=controls,
        candidate_pool=pool,
    )

    selected = select_positive_neighborhood_candidates(
        proposals,
        max_candidates=12,
        per_seed_cap=4,
        per_capability_pair_cap=6,
        per_anchor_cap=12,
        per_variant_cap=8,
    )

    assert len(selected) == 12
    assert selected["seed"].value_counts().max() <= 4
    assert selected["capability_pair"].value_counts().max() <= 6
    assert len(set(selected["seed"])) >= 3


def test_select_positive_neighborhood_candidates_deduplicates_keys():
    anchors = pd.DataFrame([_anchor()])
    controls = pd.DataFrame([{**_anchor(), "variant": "zero_current_response", "control_positive": True}])
    duplicated = _base(
        141901,
        "brake_authority_drop->mass_cg_shift",
        bucket="vx6|yaw-2|steer-4|ox0|oy0",
    )
    pool = pd.DataFrame([duplicated, dict(duplicated)])
    proposals = generate_positive_neighborhood_proposals(
        history_positive_rows=anchors,
        control_positive_rows=controls,
        candidate_pool=pool,
    )

    selected = select_positive_neighborhood_candidates(
        proposals,
        max_candidates=16,
        per_seed_cap=16,
        per_capability_pair_cap=16,
        per_anchor_cap=16,
        per_variant_cap=16,
    )

    assert len(selected) == selected["positive_neighborhood_key"].nunique()
