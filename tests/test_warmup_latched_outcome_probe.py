import pandas as pd

from autodrift.warmup_latched_outcome_probe import (
    classify_warmup_outcome_probe_result,
    is_broad_near_boundary,
    is_preferred_near_boundary,
    normal_margin_band,
    select_warmup_candidate_rows,
    source_diversity,
    summarize_normal_margin_bands,
)


def test_select_warmup_candidate_rows_filters_and_caps_by_capability_pair():
    rows = pd.DataFrame(
        [
            {
                "seed": 1,
                "capability_pair": "a->b",
                "matched_or_bucketed_reveal_pass": True,
                "matched_current_pass": True,
                "current_hidden_l2": 0.1,
                "warmup_history_l2": 0.1,
            },
            {
                "seed": 2,
                "capability_pair": "a->b",
                "matched_or_bucketed_reveal_pass": True,
                "matched_current_pass": False,
                "current_hidden_l2": 0.3,
                "warmup_history_l2": 0.1,
            },
            {
                "seed": 3,
                "capability_pair": "c->d",
                "matched_or_bucketed_reveal_pass": False,
                "matched_current_pass": True,
                "current_hidden_l2": 0.9,
                "warmup_history_l2": 0.1,
            },
        ]
    )

    selected = select_warmup_candidate_rows(rows, max_candidate_rows=10, per_capability_pair_cap=1)

    assert len(selected) == 1
    assert bool(selected.iloc[0]["matched_current_pass"])
    assert selected.iloc[0]["capability_pair"] == "a->b"


def test_source_diversity_counts_reveal_buckets_and_variants():
    rows = [
        {"seed": 1, "capability_pair": "a->b", "preferred_reveal_bucket": "x", "variant": "reset_hidden"},
        {"seed": 2, "capability_pair": "a->b", "preferred_reveal_bucket": "y", "variant": "warmup_removed"},
        {"seed": 2, "capability_pair": "c->d", "preferred_reveal_bucket": "y", "variant": "warmup_removed"},
    ]

    summary = source_diversity(rows)

    assert summary["unique_source_seeds"] == 2
    assert summary["unique_capability_pairs"] == 2
    assert summary["unique_reveal_buckets"] == 2
    assert summary["unique_variants"] == 2


def test_normal_margin_band_and_near_boundary_flags():
    assert normal_margin_band(float("nan")) == "nonfinite"
    assert normal_margin_band(-0.1) == "negative"
    assert normal_margin_band(0.01) == "viable_0p00_0p02"
    assert normal_margin_band(0.10) == "preferred_0p02_0p25"
    assert normal_margin_band(0.40) == "broad_0p25_0p50"
    assert normal_margin_band(1.0) == "high_gt_0p50"
    assert is_broad_near_boundary(0.40)
    assert not is_broad_near_boundary(0.60)
    assert is_preferred_near_boundary(0.10)
    assert not is_preferred_near_boundary(0.40)


def test_summarize_normal_margin_bands_counts_candidates_and_outcomes():
    candidates = [
        {"selected_index": 1, "seed": 1, "capability_pair": "a->b", "preferred_reveal_bucket": "x", "normal_margin_band": "preferred_0p02_0p25"},
        {"selected_index": 2, "seed": 2, "capability_pair": "a->b", "preferred_reveal_bucket": "y", "normal_margin_band": "high_gt_0p50"},
    ]
    outcomes = [
        {"normal_margin_band": "preferred_0p02_0p25", "outcome_critical": True, "warmup_history_positive": True},
        {"normal_margin_band": "preferred_0p02_0p25", "outcome_critical": False, "warmup_history_positive": False},
        {"normal_margin_band": "high_gt_0p50", "outcome_critical": True, "warmup_history_positive": False},
    ]

    summary = summarize_normal_margin_bands(candidates, outcomes)
    by_band = {row["normal_margin_band"]: row for row in summary}

    assert by_band["preferred_0p02_0p25"]["candidate_rows"] == 1
    assert by_band["preferred_0p02_0p25"]["outcome_critical_rows"] == 1
    assert by_band["preferred_0p02_0p25"]["warmup_history_positive_rows"] == 1
    assert by_band["high_gt_0p50"]["candidate_rows"] == 1


def test_classify_warmup_outcome_probe_result_thresholds():
    assert (
        classify_warmup_outcome_probe_result(
            total_rows=100,
            normal_failed_rows=0,
            warmup_history_positive_rows=48,
            accepted_reset_rows=0,
            accepted_zero_current_rows=0,
            action_critical_rows=80,
            accepted_history_seeds=12,
            accepted_history_capability_pairs=6,
            accepted_history_reveal_buckets=4,
        )
        == "warmup_latched_outcome_positive_public"
    )
    assert (
        classify_warmup_outcome_probe_result(
            total_rows=100,
            normal_failed_rows=0,
            warmup_history_positive_rows=47,
            accepted_reset_rows=3,
            accepted_zero_current_rows=0,
            action_critical_rows=80,
            accepted_history_seeds=12,
            accepted_history_capability_pairs=6,
            accepted_history_reveal_buckets=4,
        )
        == "warmup_latched_outcome_history_sparse"
    )
    assert (
        classify_warmup_outcome_probe_result(
            total_rows=100,
            normal_failed_rows=0,
            warmup_history_positive_rows=0,
            accepted_reset_rows=3,
            accepted_zero_current_rows=0,
            action_critical_rows=80,
            accepted_history_seeds=0,
            accepted_history_capability_pairs=0,
            accepted_history_reveal_buckets=0,
        )
        == "warmup_latched_outcome_reset_or_current_only"
    )
