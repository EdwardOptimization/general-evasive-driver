import pandas as pd

from autodrift.causal_history_candidate_outcome_probe import (
    classify_outcome_probe_result,
    select_candidate_rows,
    source_diversity,
)


def test_select_candidate_rows_caps_fault_pairs_by_ranked_reset_gap():
    rows = pd.DataFrame(
        [
            {"fault_pair": "a->b", "reset_margin_gap": 0.1, "reset_action_l2_gap": 0.3},
            {"fault_pair": "a->b", "reset_margin_gap": 0.4, "reset_action_l2_gap": 0.1},
            {"fault_pair": "a->b", "reset_margin_gap": 0.2, "reset_action_l2_gap": 0.2},
            {"fault_pair": "c->d", "reset_margin_gap": 0.3, "reset_action_l2_gap": 0.4},
        ]
    )

    selected = select_candidate_rows(rows, max_candidate_rows=3, per_fault_pair_cap=2)

    assert len(selected) == 3
    assert selected[selected["fault_pair"] == "a->b"]["reset_margin_gap"].tolist() == [0.4, 0.2]


def test_classify_outcome_probe_result_prioritizes_self_id_positive():
    assert (
        classify_outcome_probe_result(
            total_rows=300,
            normal_failed_rows=0,
            accepted_self_id_rows=48,
            accepted_reset_rows=4,
            accepted_zero_current_rows=4,
            action_critical_rows=100,
            accepted_self_id_seeds=12,
            accepted_self_id_fault_pairs=8,
        )
        == "causal_history_outcome_positive_public"
    )
    assert (
        classify_outcome_probe_result(
            total_rows=300,
            normal_failed_rows=0,
            accepted_self_id_rows=0,
            accepted_reset_rows=12,
            accepted_zero_current_rows=0,
            action_critical_rows=100,
            accepted_self_id_seeds=0,
            accepted_self_id_fault_pairs=0,
        )
        == "causal_history_outcome_reset_or_current_only"
    )


def test_source_diversity_counts_rows_and_variants():
    rows = [
        {"seed": 1, "fault_pair": "a->b", "variant": "delayed_history_4"},
        {"seed": 2, "fault_pair": "a->b", "variant": "wrong_same_current_history"},
        {"seed": 2, "fault_pair": "c->d", "variant": "wrong_same_current_history"},
    ]

    summary = source_diversity(rows)

    assert summary["rows"] == 3
    assert summary["unique_source_seeds"] == 2
    assert summary["unique_fault_pairs"] == 2
    assert summary["unique_variants"] == 2
