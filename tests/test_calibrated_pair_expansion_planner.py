from autodrift.calibrated_pair_expansion_planner import (
    PairExpansionCandidate,
    build_pair_candidates,
    build_summary,
    expanded_terminal_source_rows,
    pairability_score,
    select_diverse_pairs,
)
from autodrift.calibrated_terminal_boundary_history_interventions import CalibratedMeasuredSnapshot


class _Spec:
    def __init__(self, mode_name: str):
        self.artifact_row = type("Artifact", (), {"mode_name": mode_name})()


def _snapshot(
    calibration_id: str,
    family: str,
    *,
    response_x: float,
    context_x: float,
    action_x: float,
    margin: float,
    window: str = "decision",
) -> CalibratedMeasuredSnapshot:
    return CalibratedMeasuredSnapshot(
        calibration_id=calibration_id,
        trace_id=f"trace-{calibration_id}",
        source_family=family,
        seed=1,
        snapshot_kind=window,
        window_kind=window,
        anchor_step=30,
        response_vector=(response_x,) + (0.0,) * 11,
        context_vector=(context_x,) + (0.0,) * 59,
        action_vector=(action_x, 0.0, 0.0),
        hidden_norm=1.0,
        hidden_checksum=1.0,
        min_clearance_margin=margin,
        terminal_margin=margin,
        collision=False,
        obstacle_completed=True,
        terminal_reason="obstacle_completed",
    )


def test_pairability_score_prefers_action_and_margin_gap():
    weak = pairability_score(
        scene_context_distance=0.01,
        current_ego_distance=0.01,
        anchor_window_distance=0,
        first_action_l2=0.04,
        terminal_margin_gap=0.02,
    )
    strong = pairability_score(
        scene_context_distance=0.01,
        current_ego_distance=0.01,
        anchor_window_distance=0,
        first_action_l2=0.10,
        terminal_margin_gap=0.05,
    )

    assert strong > weak


def test_expanded_terminal_source_rows_over_samples_before_cap():
    rows = expanded_terminal_source_rows(seed=1843, seed_count=3, max_base_rows=12)

    assert len(rows) >= 10
    assert len({row.source_family for row in rows}) >= 4


def test_build_pair_candidates_filters_and_scores_pairs():
    snapshots = [
        _snapshot("a", "family_a", response_x=0.0, context_x=0.0, action_x=0.0, margin=0.02),
        _snapshot("b", "family_b", response_x=0.01, context_x=0.01, action_x=0.08, margin=0.07),
        _snapshot("c", "family_a", response_x=1.0, context_x=1.0, action_x=0.0, margin=0.02),
    ]
    specs = {"a": _Spec("mode_a"), "b": _Spec("mode_b"), "c": _Spec("mode_c")}

    pairs = build_pair_candidates(snapshots, specs, max_pair_candidates=8)

    assert len(pairs) == 1
    assert pairs[0].left_calibration_id == "a"
    assert pairs[0].right_calibration_id == "b"
    assert pairs[0].source_family_edge == "family_a|family_b"
    assert pairs[0].pairability_score > 0.0


def _candidate(index: int, left: str, right: str, *, score: float = 1.0) -> PairExpansionCandidate:
    return PairExpansionCandidate(
        pair_id=f"candidate-{index}",
        left_calibration_id=f"left-{index}",
        right_calibration_id=f"right-{index}",
        left_source_family=left,
        right_source_family=right,
        left_mode_name="mode",
        right_mode_name="mode",
        left_window_kind="decision",
        right_window_kind="post_decision" if index % 2 else "decision",
        left_anchor_step=30,
        right_anchor_step=30,
        source_family_edge="|".join(sorted((left, right))),
        window_pair_kind="decision|post_decision" if index % 2 else "decision|decision",
        scene_context_distance=0.01,
        current_ego_distance=0.01,
        anchor_window_distance=0,
        first_action_l2=0.10,
        terminal_margin_gap=0.04,
        pairability_score=score,
    )


def test_select_diverse_pairs_round_robins_source_edges():
    candidates = []
    edges = [("a", "b"), ("a", "c"), ("a", "d"), ("b", "c"), ("c", "d")]
    for index in range(20):
        left, right = edges[index % len(edges)]
        candidates.append(_candidate(index, left, right, score=10.0 - index * 0.1))

    pairs = select_diverse_pairs(candidates, max_accepted_pairs=10)

    assert len(pairs) == 10
    assert len({pair.source_family_edge for pair in pairs}) == 5
    assert max(pairs.count(pair) for pair in pairs) == 1


def test_build_summary_reports_pair_gate_pass_with_synthetic_rows():
    snapshots = [
        _snapshot(f"s{i}", f"family_{i % 4}", response_x=0.0, context_x=0.0, action_x=0.0, margin=0.03)
        for i in range(24)
    ]
    attempts = [
        type(
            "Attempt",
            (),
            {"source_family": f"family_{i % 4}", "failure_type": "none"},
        )()
        for i in range(24)
    ]
    edges = [("family_0", "family_1"), ("family_0", "family_2"), ("family_0", "family_3"), ("family_1", "family_2"), ("family_2", "family_3")]
    accepted_pairs = [_candidate(i, *edges[i % len(edges)]) for i in range(10)]
    candidates = accepted_pairs + [_candidate(100 + i, *edges[i % len(edges)]) for i in range(10)]

    summary = build_summary(
        source_rows=[object() for _ in range(10)],
        specs=[object() for _ in range(40)],
        attempts=attempts,
        snapshots=snapshots,
        candidates=candidates,
        accepted_pairs=accepted_pairs,
        max_pair_candidates=256,
    )

    assert summary["passes_trace_gates"] is True
    assert summary["passes_pair_gates"] is True
    assert summary["passes_public_smoke_gates"] is True
    assert summary["history_interventions_executed"] is False
