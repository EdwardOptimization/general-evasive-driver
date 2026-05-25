from __future__ import annotations

from autodrift.v4_source_diverse_sequence_effective_corpus import (
    build_self_pair_rows_from_boundary,
    classify_source_diverse_corpus,
    split_source_aware,
)


def test_build_self_pair_rows_from_boundary_preserves_source_metadata() -> None:
    rows = [
        {
            "candidate_id": "10",
            "source_group_id": "3",
            "seed": "42",
            "step": "7",
            "warmup_mode": "brake_tap",
            "preferred_fault_family": "global_mu_drop",
            "preferred_fidelity_class": "current_model_fault",
            "fault_onset_bucket": "preexisting",
            "boundary_axis": "obstacle_timing",
            "margin_band": "strict",
            "success": "True",
            "collision": "False",
            "min_clearance_margin": "0.01",
        }
    ]

    pairs = build_self_pair_rows_from_boundary(rows, max_boundary_rows=10)

    assert len(pairs) == 1
    pair = pairs[0]
    assert pair["left_source_group_id"] == 3
    assert pair["right_source_group_id"] == 3
    assert pair["left_candidate_id"] == 10
    assert pair["left_fault_family"] == "global_mu_drop"
    assert pair["left_plan"] is rows[0]


def test_split_source_aware_keeps_groups_disjoint() -> None:
    rows = [{"left_source_group_id": str(i), "row": i} for i in range(10)]
    train, eval_rows, holdout = split_source_aware(rows)

    train_groups = {row["left_source_group_id"] for row in train}
    eval_groups = {row["left_source_group_id"] for row in eval_rows}
    holdout_groups = {row["left_source_group_id"] for row in holdout}

    assert train_groups
    assert eval_groups
    assert holdout_groups
    assert train_groups.isdisjoint(eval_groups)
    assert train_groups.isdisjoint(holdout_groups)
    assert eval_groups.isdisjoint(holdout_groups)


def test_classify_source_diverse_corpus_identifies_sparse_positive() -> None:
    accepted = []
    for i in range(42):
        accepted.append(
            {
                "left_source_group_id": str(i % 6),
                "left_seed": str(i % 4),
                "left_fault_family": f"fault_{i % 5}",
                "right_fault_family": "nominal",
                "left_warmup_mode": f"warmup_{i % 3}",
                "right_warmup_mode": "same",
                "left_onset_bucket": f"onset_{i % 5}",
                "right_onset_bucket": "same",
                "direction_family": f"dir_{i % 3}",
                "hold_steps": str(4 + 2 * (i % 2)),
            }
        )

    result = classify_source_diverse_corpus(
        actor_changed=False,
        residual_changed=False,
        accepted_rows=accepted,
        all_rows=[{"abs_margin_delta": 0.02, "success_flip": False, "collision_flip": False}],
        margin_delta_threshold=0.01,
        strong_min_rows=120,
        sparse_min_rows=40,
        min_left_sources=10,
        min_left_seeds=4,
        min_left_fault_families=5,
        min_fault_pairs=8,
        min_warmup_pairs=3,
        min_onset_pairs=5,
        min_hold_steps=2,
        min_direction_families=3,
        max_left_source_dominance=0.30,
        max_left_seed_dominance=0.35,
        max_direction_family_dominance=0.55,
    )

    assert result == "v4_source_diverse_sequence_effective_corpus_sparse_positive"
