from __future__ import annotations

from autodrift.clean_history_control_source_generation_repair import (
    build_repair_summary,
    select_clean_source_repair_pairability_rows,
)


def _pair(pair_id: str, edge: str, left: str, right: str, *, response: float = 0.1, hidden: float = 3.5) -> dict[str, object]:
    left_window = "reveal_plus_4"
    right_window = "reveal_plus_4"
    if "curved_boundary_obstacle" in edge:
        left_window = "decision_minus_32"
        right_window = "decision_minus_32"
    return {
        "pair_id": pair_id,
        "source_edge": edge,
        "left_source_family": left,
        "right_source_family": right,
        "left_anchor_window": left_window,
        "right_anchor_window": right_window,
        "same_window": True,
        "context_ok": True,
        "tier_a_strict": True,
        "response_action_l2": response,
        "context_l2": 0.1,
        "hidden_l2": hidden,
    }


def test_selector_prioritizes_clean_edges_and_tags_sources() -> None:
    clean_rows = [
        {
            "source_edge": "actuator_delay_step|t5_near_boundary_warmup",
            "target_source_family": "actuator_delay_step",
            "donor_source_family": "t5_near_boundary_warmup",
            "target_anchor_window": "reveal_plus_4",
            "donor_anchor_window": "reveal_plus_4",
        }
    ]
    pair_rows = [
        _pair("fallback", "drive_loss_proxy|t5_near_boundary_warmup", "drive_loss_proxy", "t5_near_boundary_warmup", response=0.01),
        _pair(
            "clean",
            "actuator_delay_step|t5_near_boundary_warmup",
            "actuator_delay_step",
            "t5_near_boundary_warmup",
            response=0.2,
        ),
    ]

    selected = select_clean_source_repair_pairability_rows(pair_rows, clean_rows, max_selected_pairs=2)

    assert selected[0]["pair_id"] == "clean"
    assert selected[0]["selection_source"] == "clean_edge_window"
    assert selected[0]["selected_pair_id"] == "selected-0000"


def test_selector_round_robins_source_edges_under_cap() -> None:
    clean_rows = [
        {
            "source_edge": "actuator_delay_step|t5_near_boundary_warmup",
            "target_source_family": "actuator_delay_step",
            "donor_source_family": "t5_near_boundary_warmup",
            "target_anchor_window": "reveal_plus_4",
            "donor_anchor_window": "reveal_plus_4",
        }
    ]
    pair_rows = []
    for index in range(6):
        pair_rows.append(
            _pair(
                f"clean-{index}",
                "actuator_delay_step|t5_near_boundary_warmup",
                "actuator_delay_step",
                "t5_near_boundary_warmup",
                response=0.01 + index * 0.001,
            )
        )
        pair_rows.append(
            _pair(
                f"neighbor-{index}",
                "capability_step_up|t5_near_boundary_warmup",
                "capability_step_up",
                "t5_near_boundary_warmup",
                response=0.02 + index * 0.001,
            )
        )

    selected = select_clean_source_repair_pairability_rows(
        pair_rows,
        clean_rows,
        max_selected_pairs=4,
        max_pairs_per_source_edge=2,
        min_selected_source_edges=2,
    )

    assert [row["source_edge"] for row in selected].count("actuator_delay_step|t5_near_boundary_warmup") == 2
    assert [row["source_edge"] for row in selected].count("capability_step_up|t5_near_boundary_warmup") == 2


def test_build_repair_summary_passes_clean_targets() -> None:
    classified = []
    for index in range(12):
        classified.append(
            {
                "pair_id": f"clean-{index}",
                "label": "history_control_separated",
                "source_edge": f"edge-{index % 5}",
                "target_source_family": f"fam-{index % 6}",
                "donor_source_family": f"fam-{(index + 1) % 6}",
                "history_max_gap": 0.03,
                "control_max_gap": 0.005,
            }
        )
    for index in range(116):
        classified.append(
            {
                "pair_id": f"null-{index}",
                "label": "history_null_all_controls_null",
                "source_edge": f"null-edge-{index % 8}",
                "target_source_family": "n0",
                "donor_source_family": "n1",
                "history_max_gap": 0.0,
                "control_max_gap": 0.0,
            }
        )
    selected = [_pair(f"pair-{index}", f"edge-{index % 8}", f"fam-{index % 6}", f"fam-{(index + 1) % 6}") for index in range(64)]
    intervention = [{"pair_id": f"directed-{index // 8}", "variant": str(index % 8)} for index in range(1024)]

    summary = build_repair_summary(
        source_spec_count=480,
        selected_rows=selected,
        intervention_rows=intervention,
        classified_rows=classified,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["null_result_classification"] == "clean_source_repair_public_pass"


def test_build_repair_summary_rejects_clean_shortfall() -> None:
    classified = [
        {
            "pair_id": f"clean-{index}",
            "label": "history_control_separated",
            "source_edge": f"edge-{index % 4}",
            "target_source_family": "a",
            "donor_source_family": "b",
            "history_max_gap": 0.03,
            "control_max_gap": 0.005,
        }
        for index in range(7)
    ]
    selected = [_pair(f"pair-{index}", f"edge-{index % 8}", "a", "b") for index in range(64)]

    summary = build_repair_summary(
        source_spec_count=480,
        selected_rows=selected,
        intervention_rows=[{"pair_id": f"directed-{index // 8}", "variant": str(index % 8)} for index in range(1024)],
        classified_rows=classified,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["null_result_classification"] == "clean_count_shortfall"
