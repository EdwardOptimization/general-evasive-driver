import pandas as pd

from autodrift.source_step_replay_boundary_retarget import (
    classify_boundary_pressure,
    generate_retarget_proposals,
    retarget_delta_grid,
    select_retarget_candidates,
)


def _row(*, selected_index: int, normal_success: bool, normal_margin: float, variant: str = "warmup_removed"):
    return {
        "selected_index": selected_index,
        "source_index": 100 + selected_index,
        "seed": 10 + selected_index,
        "reveal_step": 48,
        "candidate_step": 24,
        "candidate_step_column": "source_step",
        "preferred_fault": "preferred",
        "wrong_fault": "wrong",
        "capability_pair": f"pair-{selected_index}",
        "preferred_reveal_bucket": f"bucket-{selected_index}",
        "variant": variant,
        "normal_success": normal_success,
        "variant_success": normal_success,
        "normal_margin": normal_margin,
        "variant_margin": normal_margin - 0.01,
        "sequence_action_l2_mean": 0.2 + 0.01 * selected_index,
        "margin_gap": 0.01,
        "source_body_x": 10.0,
        "source_body_y": -2.0,
        "source_half_width": 1.0,
        "raw_relocated_body_x": 14.0,
        "relocated_body_x": 14.0,
        "relocated_body_y": -2.4,
        "raw_relocated_half_width": 1.2,
        "relocated_half_width": 1.2,
    }


def test_classify_boundary_pressure():
    assert classify_boundary_pressure(normal_success=True, normal_margin=0.5) == "normal_boundary"
    assert classify_boundary_pressure(normal_success=True, normal_margin=2.0) == "too_easy"
    assert classify_boundary_pressure(normal_success=False, normal_margin=2.0) == "too_hard"
    assert classify_boundary_pressure(normal_success=True, normal_margin=-0.1) == "too_hard"


def test_retarget_delta_grid_moves_pressure_by_class():
    easy = retarget_delta_grid("too_easy", relocated_body_y=-2.0)
    hard = retarget_delta_grid("too_hard", relocated_body_y=-2.0)
    boundary = retarget_delta_grid("normal_boundary", relocated_body_y=-2.0)

    assert any(row["body_longitudinal_delta"] < 0.0 for row in easy)
    assert any(row["half_width_delta"] > 0.0 for row in easy)
    assert any(row["body_lateral_delta"] > 0.0 for row in easy)
    assert any(row["body_longitudinal_delta"] > 0.0 for row in hard)
    assert any(row["half_width_delta"] < 0.0 for row in hard)
    assert any(row["body_lateral_delta"] < 0.0 for row in hard)
    assert len(boundary) > len(easy) // 2


def test_generate_retarget_proposals_preserves_source_step_and_classes():
    frame = pd.DataFrame(
        [
            _row(selected_index=0, normal_success=True, normal_margin=0.8, variant="warmup_removed"),
            _row(selected_index=0, normal_success=True, normal_margin=0.8, variant="reset_hidden"),
            _row(selected_index=1, normal_success=True, normal_margin=3.0, variant="delayed_warmup_history_16"),
            _row(selected_index=2, normal_success=False, normal_margin=-0.1, variant="warmup_shortened_8"),
        ]
    )

    proposals = generate_retarget_proposals(frame)

    assert set(proposals["retarget_class"]) == {"normal_boundary", "too_easy", "too_hard"}
    assert set(proposals["candidate_step_column"]) == {"source_step"}
    assert set(proposals["source_step"]) == {24}
    assert "reset_hidden" not in set(proposals["variant"])


def test_select_retarget_candidates_applies_caps_and_priority():
    proposals = generate_retarget_proposals(
        pd.DataFrame(
            [
                _row(selected_index=0, normal_success=True, normal_margin=0.8),
                _row(selected_index=1, normal_success=True, normal_margin=3.0, variant="delayed_warmup_history_16"),
                _row(selected_index=2, normal_success=False, normal_margin=-0.1, variant="warmup_shortened_8"),
            ]
        )
    )

    selected = select_retarget_candidates(
        proposals,
        max_candidates=6,
        per_class_cap=2,
        per_seed_cap=4,
        per_capability_pair_cap=4,
        per_variant_cap=4,
    )

    assert len(selected) == 6
    assert selected["retarget_class"].value_counts().max() <= 2
    assert selected.iloc[0]["retarget_class"] == "normal_boundary"
