import csv

from autodrift.calibrated_terminal_boundary_history_interventions import CalibratedMeasuredPair
from autodrift.pair_expanded_calibrated_history_interventions import (
    build_summary,
    input_endpoint_counts,
    load_pair_expanded_pairs,
    reconstruct_specs_by_id,
)


def test_load_pair_expanded_pairs_filters_unaccepted_rows(tmp_path):
    path = tmp_path / "pairs.csv"
    path.write_text(
        "\n".join(
            [
                "pair_id,left_calibration_id,right_calibration_id,left_source_family,right_source_family,left_window_kind,right_window_kind,left_anchor_step,right_anchor_step,scene_context_distance,current_ego_distance,first_action_l2,terminal_margin_gap,window_pair_kind,accepted",
                "p0,a,b,f0,f1,decision,post_decision,10,12,0.01,0.02,0.1,0.03,decision|post_decision,True",
                "p1,c,d,f0,f2,decision,decision,10,10,0.01,0.02,0.1,0.03,decision|decision,False",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    pairs = load_pair_expanded_pairs(path)

    assert len(pairs) == 1
    assert pairs[0].pair_id == "p0"
    assert pairs[0].left_anchor_step == 10


def test_reconstruct_specs_maps_m1550_pair_ids():
    pairs = load_pair_expanded_pairs("runs/m1550_calibrated_pair_expansion_planner_smoke/accepted_pair_rows.csv", max_pairs=4)
    specs = reconstruct_specs_by_id(seed=1843, seed_count=3, max_base_rows=24, max_calibration_specs=240)

    ids = {pair.left_calibration_id for pair in pairs} | {pair.right_calibration_id for pair in pairs}
    assert ids <= set(specs)


def _pair(index: int, left_family: str, right_family: str) -> CalibratedMeasuredPair:
    window_pair_kind = ("decision|decision", "decision|post_decision", "post_decision|post_decision")[index % 3]
    left_window, right_window = window_pair_kind.split("|")
    return CalibratedMeasuredPair(
        pair_id=f"pair-{index:04d}",
        left_calibration_id=f"left-{index}",
        right_calibration_id=f"right-{index}",
        left_source_family=left_family,
        right_source_family=right_family,
        left_window_kind=left_window,
        right_window_kind=right_window,
        left_anchor_step=30,
        right_anchor_step=32,
        scene_context_distance=0.01,
        current_ego_distance=0.01,
        first_action_l2=0.1,
        terminal_margin_gap=0.03,
        window_pair_kind=window_pair_kind,
    )


def _row(pair: CalibratedMeasuredPair, side: str, variant: str, *, gap: float = 0.0, success_drop: bool = False):
    target_family = pair.left_source_family if side == "left" else pair.right_source_family
    donor_family = pair.right_source_family if side == "left" else pair.left_source_family
    return {
        "pair_id": pair.pair_id,
        "target_side": side,
        "variant": variant,
        "target_source_family": target_family,
        "donor_source_family": donor_family,
        "target_replay_status": "ok",
        "first_action_steer": 0.1,
        "first_action_throttle": 0.0,
        "first_action_brake": 0.0,
        "terminal_margin_gap_from_normal": gap,
        "success_drop_from_normal": success_drop,
    }


def test_build_summary_reports_history_and_concentration_gates():
    edges = [("a", "b"), ("a", "c"), ("a", "d"), ("b", "c"), ("c", "d")]
    pairs = [_pair(index, *edges[index % len(edges)]) for index in range(20)]
    rows = []
    variants = [
        "normal",
        "reset_hidden_once_at_anchor",
        "reset_hidden_every_step_from_anchor",
        "zero_current_response_from_anchor",
        "zero_action_history_from_anchor",
        "delayed_hidden_8_at_anchor",
        "delayed_hidden_16_at_anchor",
        "wrong_history_donor_hidden_at_anchor",
        "donor_response_action_stream_from_anchor",
        "donor_response_action_plus_hidden_from_anchor",
    ]
    for pair in pairs:
        for side in ("left", "right"):
            for variant in variants:
                gap = 0.03 if variant in {"wrong_history_donor_hidden_at_anchor", "donor_response_action_plus_hidden_from_anchor"} else 0.0
                rows.append(_row(pair, side, variant, gap=gap))

    summary = build_summary(pairs=pairs, rows=rows, continuation_steps=64)

    assert summary["passes_input_pair_gates"] is True
    assert summary["passes_replay_gates"] is True
    assert summary["passes_history_positive_gates"] is True
    assert summary["passes_control_gate"] is True
    assert summary["passes_public_smoke_gates"] is True
    assert summary["passes_evidence_quality_targets"] is True


def test_input_endpoint_counts_counts_both_sides():
    pairs = [_pair(0, "a", "b"), _pair(1, "a", "c")]

    counts = input_endpoint_counts(pairs)

    assert sum(counts.values()) == 4
