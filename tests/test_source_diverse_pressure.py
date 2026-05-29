import pandas as pd

from autodrift.source_diverse_pressure import (
    build_source_pressure_audit,
    generate_source_diverse_pressure_proposals,
    history_anchor_rows,
    pressure_delta_grid,
    select_source_diverse_pressure_candidates,
)


def _row(
    seed: int,
    pair: str,
    variant: str,
    *,
    history_positive: bool = False,
    control_positive: bool = False,
    relocation_key: str = "x=15.500|y=-0.800|w=1.100",
    normal_margin: float = 0.8,
    margin_gap: float = 0.03,
    sequence_l2: float = 0.2,
):
    return {
        "selected_index": seed % 100,
        "source_index": seed % 100,
        "seed": seed,
        "reveal_step": 48,
        "source_step": 24,
        "candidate_step": 24,
        "candidate_step_column": "source_step",
        "preferred_fault": "brake_fade_pre_emergency",
        "wrong_fault": "heavy_front_payload_preexisting",
        "capability_pair": pair,
        "preferred_reveal_bucket": f"bucket-{seed}",
        "variant": variant,
        "normal_success": True,
        "variant_success": True,
        "normal_margin": normal_margin,
        "variant_margin": normal_margin - margin_gap,
        "margin_gap": margin_gap,
        "sequence_action_l2_mean": sequence_l2,
        "source_body_x": 9.5 + (seed % 3),
        "source_body_y": -1.2,
        "source_half_width": 0.9,
        "relocated_body_x": 15.5,
        "relocated_body_y": -0.8,
        "relocated_half_width": 1.1,
        "relocation_key": relocation_key,
        "history_positive": history_positive,
        "control_positive": control_positive,
    }


def test_history_anchor_rows_excludes_control_rows():
    rows = pd.DataFrame(
        [
            _row(141901, "brake_authority_drop->mass_cg_shift", "warmup_removed", history_positive=True),
            _row(
                141901,
                "brake_authority_drop->mass_cg_shift",
                "zero_current_response",
                history_positive=True,
                control_positive=True,
            ),
            _row(141902, "front_lateral_authority_drop->mass_cg_shift", "warmup_removed"),
        ]
    )

    anchors = history_anchor_rows(rows)

    assert len(anchors) == 1
    assert anchors.iloc[0]["variant"] == "warmup_removed"


def test_source_pressure_audit_separates_original_neighbor_and_control():
    anchor = _row(141901, "brake_authority_drop->mass_cg_shift", "warmup_removed", history_positive=True)
    control = _row(
        141901,
        "brake_authority_drop->mass_cg_shift",
        "zero_current_response",
        control_positive=True,
    )
    neighbor = _row(141902, "front_lateral_authority_drop->mass_cg_shift", "warmup_removed")
    actual = pd.DataFrame([anchor, control, neighbor])

    audit = build_source_pressure_audit(
        actual_replay_rows=actual,
        history_positive_rows=pd.DataFrame([anchor]),
        control_positive_rows=pd.DataFrame([control]),
    )

    assert set(audit["source_group"]) == {"original_source", "control_diagnostic", "neighbor_source"}
    assert len(audit[audit["pressure_candidate"]]) == 1
    assert audit[audit["pressure_candidate"]].iloc[0]["seed"] == 141902


def test_pressure_delta_grid_tightens_easy_rows():
    deltas = pressure_delta_grid(3.0, relocated_body_y=-0.8)

    assert any(row["body_longitudinal_delta"] < 0.0 for row in deltas)
    assert any(row["half_width_delta"] > 0.0 for row in deltas)


def test_pressure_proposals_preserve_source_step_and_required_offsets():
    anchor = _row(141901, "brake_authority_drop->mass_cg_shift", "warmup_removed", history_positive=True)
    neighbor = _row(141902, "front_lateral_authority_drop->mass_cg_shift", "warmup_removed")
    audit = build_source_pressure_audit(
        actual_replay_rows=pd.DataFrame([anchor, neighbor]),
        history_positive_rows=pd.DataFrame([anchor]),
        control_positive_rows=pd.DataFrame(),
    )

    proposals = generate_source_diverse_pressure_proposals(audit, include_original_diagnostics=False)

    assert len(proposals) > 0
    assert set(proposals["candidate_step_column"]) == {"source_step"}
    assert set(proposals["source_step"]) == {24}
    assert {"body_longitudinal_offset", "body_lateral_offset", "half_width_inflation"}.issubset(proposals.columns)
    assert set(proposals["source_group"]) == {"neighbor_source"}


def test_select_pressure_candidates_caps_original_source_and_controls():
    anchor = _row(141901, "brake_authority_drop->mass_cg_shift", "warmup_removed", history_positive=True)
    control = _row(
        141901,
        "brake_authority_drop->mass_cg_shift",
        "zero_current_response",
        control_positive=True,
    )
    rows = [
        anchor,
        control,
        _row(141902, "front_lateral_authority_drop->mass_cg_shift", "warmup_removed"),
        _row(141903, "global_mu_drop->front_lateral_authority_drop", "warmup_shortened_8", normal_margin=1.2),
        _row(141904, "steering_fault->delay_noise_fault", "warmup_removed", normal_margin=2.0),
    ]
    audit = build_source_pressure_audit(
        actual_replay_rows=pd.DataFrame(rows),
        history_positive_rows=pd.DataFrame([anchor]),
        control_positive_rows=pd.DataFrame([control]),
    )
    proposals = generate_source_diverse_pressure_proposals(audit)

    selected = select_source_diverse_pressure_candidates(
        proposals,
        max_candidates=24,
        per_seed_cap=8,
        per_capability_pair_cap=8,
        per_reveal_bucket_cap=8,
        per_relocation_key_cap=24,
        per_variant_cap=16,
        original_source_cap=2,
        control_diagnostic_cap=3,
    )

    assert len(selected) == selected["source_diverse_pressure_key"].nunique()
    assert (selected["source_group"] == "original_source").sum() <= 2
    assert (selected["source_group"] == "control_diagnostic").sum() <= 3
    assert (selected["source_group"] == "neighbor_source").sum() > 0
    assert selected["seed"].value_counts().max() <= 8
