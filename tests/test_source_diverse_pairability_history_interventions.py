from __future__ import annotations

from autodrift.source_diverse_pairability_history_interventions import (
    CONTROL_VARIANTS,
    HISTORY_VARIANTS,
    VARIANTS,
    build_directed_pairs,
    build_summary,
    select_pairability_rows,
)


def _pair(index: int, edge: tuple[str, str], window: str = "reveal", *, same_window: bool = True) -> dict[str, object]:
    left, right = edge
    return {
        "pair_id": f"pair-{index:04d}",
        "left_anchor_id": f"{left}-{index}-l",
        "right_anchor_id": f"{right}-{index}-r",
        "left_source_family": left,
        "right_source_family": right,
        "source_edge": "|".join(sorted(edge)),
        "left_anchor_window": window,
        "right_anchor_window": window if same_window else "decision_minus_24",
        "left_anchor_step": 20 + index,
        "right_anchor_step": 20 + index if same_window else 36 + index,
        "same_window": same_window,
        "same_outcome": False,
        "tier_a_strict": True,
        "context_ok": True,
        "response_action_l2": 0.2 + 0.001 * index,
        "context_l2": 1.0,
        "hidden_l2": 4.0 + 0.01 * index,
    }


def test_select_pairability_rows_balances_source_edges_and_prefers_same_window() -> None:
    edges = [
        ("a", "b"),
        ("a", "c"),
        ("a", "d"),
        ("b", "c"),
        ("b", "d"),
        ("c", "d"),
    ]
    rows = []
    for index in range(60):
        rows.append(_pair(index, edges[index % len(edges)], same_window=index < 42))

    selected = select_pairability_rows(
        rows,
        target_pairs=18,
        max_pairs_per_source_edge=4,
        max_pairs_per_endpoint_family=20,
        max_pairs_per_anchor_window=20,
    )

    assert len(selected) == 18
    assert len({row["source_edge"] for row in selected}) >= 5
    assert sum(1 for row in selected if row["selection_source"] == "same_window_preferred") >= 12
    assert max(sum(1 for row in selected if row["source_edge"] == edge) for edge in {row["source_edge"] for row in selected}) <= 4


def test_build_directed_pairs_uses_both_directions() -> None:
    selected = [_pair(0, ("a", "b")) | {"selected_pair_id": "selected-0000"}]

    directed = build_directed_pairs(selected)

    assert len(directed) == 2
    assert {pair.target_source_family for pair in directed} == {"a", "b"}
    assert {pair.donor_source_family for pair in directed} == {"a", "b"}
    assert all(pair.target_anchor_id != pair.donor_anchor_id for pair in directed)


def test_build_summary_passes_synthetic_history_positive_case() -> None:
    selected = []
    families = ["a", "b", "c", "d", "e", "f"]
    edges = [
        ("a", "b"),
        ("a", "c"),
        ("a", "d"),
        ("b", "c"),
        ("b", "e"),
        ("c", "f"),
        ("d", "e"),
        ("d", "f"),
        ("e", "f"),
    ]
    windows = ["reveal", "reveal_plus_4", "decision_minus_32", "decision_minus_24"]
    for index in range(72):
        edge = edges[index % len(edges)]
        selected.append(_pair(index, edge, window=windows[index % len(windows)]) | {"selected_pair_id": f"selected-{index:04d}"})
    directed = build_directed_pairs(selected)
    rows = []
    for pair in directed:
        for variant in VARIANTS:
            gap = 0.0
            success_drop = False
            collision = False
            if variant in HISTORY_VARIANTS and pair.target_source_family in {"a", "b", "c", "d"}:
                gap = 0.06
                success_drop = pair.target_source_family == "a"
                collision = success_drop
            if variant in CONTROL_VARIANTS:
                gap = 0.01
            rows.append(
                {
                    **pair.__dict__,
                    "source_edge": "|".join(sorted((pair.target_source_family, pair.donor_source_family))),
                    "variant": variant,
                    "target_replay_status": "ok",
                    "terminal_margin_gap_from_normal": gap,
                    "success_drop_from_normal": success_drop,
                    "collision_increase_from_normal": collision,
                }
            )

    summary = build_summary(selected_rows=selected, directed_pairs=directed, rows=rows, continuation_steps=64)

    assert summary["selected_pair_count"] == 72
    assert summary["selected_source_edge_count"] >= 8
    assert summary["selected_endpoint_source_family_count"] == 6
    assert summary["directed_pair_count"] == 144
    assert summary["intervention_row_count"] == 144 * len(VARIANTS)
    assert summary["passes_public_smoke_gates"] is True
    assert summary["passes_evidence_quality_targets"] is True
