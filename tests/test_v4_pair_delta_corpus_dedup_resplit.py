from __future__ import annotations

from autodrift.v4_pair_delta_corpus_dedup_resplit import (
    classify_dedup_resplit,
    closed_loop_signature,
    deduplicate_pair_delta_rows,
    split_deduped_corpus,
)


def _row(**overrides):
    row = {
        "pair_id": "1",
        "left_source_group_id": "10",
        "right_source_group_id": "20",
        "left_step": "5",
        "right_step": "5",
        "left_seed": "78048",
        "right_seed": "78055",
        "left_fault_family": "front_lateral_authority_drop",
        "right_fault_family": "global_mu_drop",
        "retarget_target_body_x": "12.0",
        "retarget_target_body_y": "0.5",
        "retarget_target_half_width": "1.0",
        "direction": "pair_delta_positive",
        "hold_steps": "8",
        "epsilon_l2": "0.125",
        "normal_margin": "0.005",
        "sequence_margin": "-0.001",
        "abs_margin_delta": "0.006",
        "retarget_axis": "obstacle_lateral_offset",
        "coverage_source": "m873_boundary_preserving",
    }
    row.update(overrides)
    return row


def test_closed_loop_signature_ignores_retarget_axis_and_pair_id() -> None:
    first = _row(pair_id="1", retarget_axis="obstacle_lateral_offset")
    second = _row(pair_id="2", retarget_axis="obstacle_timing")

    assert closed_loop_signature(first) == closed_loop_signature(second)


def test_deduplicate_pair_delta_rows_collapses_axis_duplicates() -> None:
    rows = [
        _row(pair_id="1", retarget_axis="obstacle_lateral_offset"),
        _row(pair_id="2", retarget_axis="obstacle_timing"),
        _row(pair_id="3", retarget_axis="obstacle_half_width"),
    ]

    deduped, groups = deduplicate_pair_delta_rows(rows)

    assert len(deduped) == 1
    assert deduped[0]["duplicate_row_count"] == 3
    assert deduped[0]["duplicate_retarget_axes"] == "obstacle_half_width;obstacle_lateral_offset;obstacle_timing"
    assert groups[0]["evidence_origin"] == "new_m873"


def test_split_deduped_corpus_places_new_rows_in_train_eval_and_signature_holdout() -> None:
    rows = []
    for index in range(10):
        rows.append(_row(pair_id=str(index), left_source_group_id="33", left_seed="78057", hold_steps=str(index)))
    for index in range(3):
        rows.append(_row(pair_id=str(index + 20), left_source_group_id="12", left_seed="78048", direction="pair_delta_negative", hold_steps=str(index)))
    for index in range(12):
        rows.append(
            _row(
                pair_id=str(index + 40),
                left_source_group_id=str(100 + index),
                left_seed="78050",
                coverage_source="m867_existing",
                hold_steps=str(index),
            )
        )
    deduped, _groups = deduplicate_pair_delta_rows(rows)
    splits = split_deduped_corpus(deduped)

    assert any(row["evidence_origin"] == "new_m873" for row in splits["objective_train_public"])
    assert any(row["evidence_origin"] == "new_m873" for row in splits["objective_eval_public"])
    assert splits["source_holdout_public"]
    assert splits["new_signature_holdout_public"]


def test_classify_dedup_resplit_pass() -> None:
    result = classify_dedup_resplit(
        dedup_rows=30,
        new_dedup_rows=13,
        new_dedup_unique_left_source_group_count=2,
        new_duplicate_factor_after=1.0,
        objective_train_rows=20,
        objective_eval_rows=10,
        source_holdout_rows=5,
        objective_train_new_rows=8,
        objective_eval_new_rows=2,
        new_signature_holdout_rows=3,
        caveat_78055_recorded=True,
        max_new_duplicate_factor_after=1.25,
        min_new_dedup_rows=10,
        min_new_source_groups=2,
    )

    assert result == "v4_pair_delta_corpus_dedup_resplit_pass"


def test_classify_dedup_resplit_split_limited_without_new_train_rows() -> None:
    result = classify_dedup_resplit(
        dedup_rows=30,
        new_dedup_rows=13,
        new_dedup_unique_left_source_group_count=2,
        new_duplicate_factor_after=1.0,
        objective_train_rows=20,
        objective_eval_rows=10,
        source_holdout_rows=5,
        objective_train_new_rows=0,
        objective_eval_new_rows=2,
        new_signature_holdout_rows=3,
        caveat_78055_recorded=True,
        max_new_duplicate_factor_after=1.25,
        min_new_dedup_rows=10,
        min_new_source_groups=2,
    )

    assert result == "v4_pair_delta_corpus_dedup_resplit_split_limited"
