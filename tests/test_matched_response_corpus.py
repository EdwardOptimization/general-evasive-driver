import numpy as np
import pandas as pd

from autodrift.matched_response_corpus import (
    build_seed_candidates,
    build_summary,
    build_variant_edges,
    select_seed_corpus,
)


def _replays() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "seed": 1,
                "source_condition": "nominal",
                "variant": "normal",
                "success": True,
                "return": 10.0,
                "first_action_distance": 0.0,
            },
            {
                "seed": 1,
                "source_condition": "nominal",
                "variant": "reset",
                "success": False,
                "return": 1.0,
                "first_action_distance": 0.4,
            },
            {
                "seed": 1,
                "source_condition": "perturbed",
                "variant": "normal",
                "success": False,
                "return": 2.0,
                "first_action_distance": 0.0,
            },
            {
                "seed": 1,
                "source_condition": "perturbed",
                "variant": "reset",
                "success": False,
                "return": 1.5,
                "first_action_distance": 0.2,
            },
            {
                "seed": 2,
                "source_condition": "nominal",
                "variant": "normal",
                "success": True,
                "return": 8.0,
                "first_action_distance": 0.0,
            },
            {
                "seed": 2,
                "source_condition": "nominal",
                "variant": "reset",
                "success": True,
                "return": 7.5,
                "first_action_distance": 0.1,
            },
            {
                "seed": 2,
                "source_condition": "perturbed",
                "variant": "normal",
                "success": True,
                "return": 7.0,
                "first_action_distance": 0.0,
            },
            {
                "seed": 2,
                "source_condition": "perturbed",
                "variant": "reset",
                "success": True,
                "return": 6.8,
                "first_action_distance": 0.1,
            },
        ]
    )


def _pairs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "seed": 1,
                "accepted_match": True,
                "observation_distance": 0.2,
                "context_observation_distance": 0.04,
                "hidden_state_distance": 2.0,
            },
            {
                "seed": 2,
                "accepted_match": True,
                "observation_distance": 0.3,
                "context_observation_distance": 0.20,
                "hidden_state_distance": 0.5,
            },
        ]
    )


def test_build_variant_edges_marks_success_and_return_changes():
    edges = build_variant_edges(_replays(), ablation_variants=("reset",))

    changed = edges[edges["success_changed"]]

    assert changed[["seed", "source_condition", "variant"]].to_dict("records") == [
        {"seed": 1, "source_condition": "nominal", "variant": "reset"}
    ]
    assert np.isclose(float(changed.iloc[0]["return_delta"]), -9.0)


def test_build_seed_candidates_scores_condition_and_ablation_changes():
    edges = build_variant_edges(_replays(), ablation_variants=("reset",))

    candidates = build_seed_candidates(_pairs(), _replays(), edges)

    assert candidates.iloc[0]["seed"] == 1
    assert int(candidates.iloc[0]["success_changed_variants"]) == 1
    assert bool(candidates.iloc[0]["normal_condition_change"])
    assert bool(candidates.iloc[0]["perturbed_failed"])
    assert candidates.iloc[0]["response_critical_score"] > candidates.iloc[1]["response_critical_score"]


def test_select_seed_corpus_filters_match_quality():
    edges = build_variant_edges(_replays(), ablation_variants=("reset",))
    candidates = build_seed_candidates(_pairs(), _replays(), edges)

    selected = select_seed_corpus(
        candidates,
        top_k=2,
        min_hidden_state_distance=1.0,
        max_context_observation_distance=0.10,
    )

    assert selected["seed"].tolist() == [1]


def test_build_summary_reports_selected_and_changed_counts():
    edges = build_variant_edges(_replays(), ablation_variants=("reset",))
    candidates = build_seed_candidates(_pairs(), _replays(), edges)
    corpus = select_seed_corpus(candidates, top_k=1)

    summary = build_summary(candidates, corpus, edges)

    assert summary["candidate_count"] == 2
    assert summary["selected_count"] == 1
    assert summary["success_changed_seed_count"] == 1
    assert summary["condition_changed_seed_count"] == 1
