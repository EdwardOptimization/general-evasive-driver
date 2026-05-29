import pandas as pd

from autodrift.neighbor_viability_calibration import (
    build_neighbor_viability_audit,
    calibration_delta_grid,
    classify_viability,
    generate_neighbor_viability_proposals,
    original_source_families,
    select_neighbor_viability_candidates,
)


def _row(
    seed: int,
    pair: str,
    variant: str,
    *,
    history_positive: bool = False,
    control_positive: bool = False,
    normal_success: bool = True,
    normal_margin: float = 0.5,
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
        "normal_success": normal_success,
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
        "relocation_key": "x=15.500|y=-0.800|w=1.100",
        "history_positive": history_positive,
        "control_positive": control_positive,
    }


def test_original_source_families_excludes_controls():
    history = pd.DataFrame(
        [
            _row(141901, "brake_authority_drop->mass_cg_shift", "warmup_removed", history_positive=True),
            _row(
                141901,
                "brake_authority_drop->mass_cg_shift",
                "zero_current_response",
                history_positive=True,
                control_positive=True,
            ),
        ]
    )

    families = original_source_families(history)

    assert len(families) == 1
    assert next(iter(families)).endswith("brake_authority_drop->mass_cg_shift|bucket-141901")


def test_classify_viability_classes():
    assert classify_viability(normal_success=False, normal_margin=0.5, margin_gap=0.1) == "too_hard"
    assert classify_viability(normal_success=True, normal_margin=-0.1, margin_gap=0.1) == "too_hard"
    assert classify_viability(normal_success=True, normal_margin=0.5, margin_gap=0.1) == "near_boundary"
    assert classify_viability(normal_success=True, normal_margin=0.5, margin_gap=-0.1) == "too_easy"
    assert classify_viability(normal_success=True, normal_margin=3.0, margin_gap=0.1) == "too_easy"


def test_delta_grid_eases_too_hard_and_tightens_too_easy():
    too_hard = calibration_delta_grid("too_hard", relocated_body_y=-0.8)
    too_easy = calibration_delta_grid("too_easy", relocated_body_y=-0.8)

    assert any(row["body_longitudinal_delta"] > 0.0 for row in too_hard)
    assert any(row["half_width_delta"] < 0.0 for row in too_hard)
    assert any(row["body_longitudinal_delta"] < 0.0 for row in too_easy)
    assert any(row["half_width_delta"] > 0.0 for row in too_easy)


def test_audit_separates_original_neighbor_and_controls():
    original = _row(141901, "brake_authority_drop->mass_cg_shift", "warmup_removed", history_positive=True)
    control = _row(141901, "brake_authority_drop->mass_cg_shift", "zero_current_response", control_positive=True)
    neighbor_hard = _row(
        141902,
        "steering_fault->front_lateral_authority_drop",
        "warmup_removed",
        normal_success=False,
        normal_margin=-0.1,
    )
    neighbor_easy = _row(
        141903,
        "global_mu_drop->front_lateral_authority_drop",
        "warmup_shortened_8",
        normal_margin=3.0,
    )
    audit = build_neighbor_viability_audit(
        actual_replay_rows=pd.DataFrame([original, control, neighbor_hard, neighbor_easy]),
        history_positive_rows=pd.DataFrame([original]),
        control_positive_rows=pd.DataFrame([control]),
    )

    assert set(audit["source_group"]) == {"original_source", "control_diagnostic", "neighbor_source"}
    assert set(audit[audit["source_group"] == "neighbor_source"]["viability_class"]) == {"too_hard", "too_easy"}
    assert len(audit[audit["calibration_candidate"]]) == 2


def test_proposals_preserve_source_step_and_offsets():
    original = _row(141901, "brake_authority_drop->mass_cg_shift", "warmup_removed", history_positive=True)
    neighbor = _row(141902, "steering_fault->front_lateral_authority_drop", "warmup_removed")
    audit = build_neighbor_viability_audit(
        actual_replay_rows=pd.DataFrame([original, neighbor]),
        history_positive_rows=pd.DataFrame([original]),
        control_positive_rows=pd.DataFrame(),
    )

    proposals = generate_neighbor_viability_proposals(audit, include_original_diagnostics=False)

    assert len(proposals) > 0
    assert set(proposals["source_group"]) == {"neighbor_source"}
    assert set(proposals["candidate_step_column"]) == {"source_step"}
    assert set(proposals["source_step"]) == {24}
    assert {"body_longitudinal_offset", "body_lateral_offset", "half_width_inflation"}.issubset(proposals.columns)


def test_selection_caps_original_controls_and_deduplicates():
    original = _row(141901, "brake_authority_drop->mass_cg_shift", "warmup_removed", history_positive=True)
    control = _row(141901, "brake_authority_drop->mass_cg_shift", "zero_current_response", control_positive=True)
    neighbors = [
        _row(141902, "steering_fault->front_lateral_authority_drop", "warmup_removed", normal_margin=0.4),
        _row(141903, "global_mu_drop->front_lateral_authority_drop", "warmup_removed", normal_margin=3.0),
        _row(141904, "front_lateral_authority_drop->steering_fault", "delayed_warmup_history_16", normal_success=False, normal_margin=-0.1),
    ]
    audit = build_neighbor_viability_audit(
        actual_replay_rows=pd.DataFrame([original, control, *neighbors]),
        history_positive_rows=pd.DataFrame([original]),
        control_positive_rows=pd.DataFrame([control]),
    )
    proposals = generate_neighbor_viability_proposals(audit)

    selected = select_neighbor_viability_candidates(
        proposals,
        max_candidates=30,
        per_seed_cap=10,
        per_capability_pair_cap=10,
        per_reveal_bucket_cap=10,
        per_viability_class_cap=12,
        per_variant_cap=20,
        original_source_cap=2,
        control_diagnostic_cap=3,
    )

    assert len(selected) == selected["neighbor_viability_key"].nunique()
    assert (selected["source_group"] == "original_source").sum() <= 2
    assert (selected["source_group"] == "control_diagnostic").sum() <= 3
    assert (selected["source_group"] == "neighbor_source").sum() > 0
    assert selected["seed"].value_counts().max() <= 10
