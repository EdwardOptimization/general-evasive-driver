import pandas as pd

from autodrift.response_necessity_corpus import (
    build_response_necessity_features,
    build_seed_sequence,
    select_response_necessity_corpus,
    write_response_necessity_corpus,
)


def _paired_frame() -> pd.DataFrame:
    rows = []
    specs = [
        (1, True, 0.50, True, 0.04, False, 0.05, "hard_low_margin"),
        (2, True, 0.60, False, -0.10, False, -0.12, "hard_failure"),
        (3, True, 0.70, True, 0.60, True, 0.58, "easy"),
    ]
    for seed, nom_success, nom_margin, pert_success, pert_margin, abl_success, abl_margin, label in specs:
        rows.append(
            {
                "seed": seed,
                "policy": "base",
                "condition": "nominal",
                "success": nom_success,
                "return": 100.0,
                "min_clearance_margin": nom_margin,
                "obstacle_label": label,
            }
        )
        rows.append(
            {
                "seed": seed,
                "policy": "base",
                "condition": "perturbed",
                "success": pert_success,
                "return": 80.0 if pert_success else 10.0,
                "min_clearance_margin": pert_margin,
                "obstacle_label": label,
            }
        )
        rows.append(
            {
                "seed": seed,
                "policy": "base_reset",
                "condition": "perturbed",
                "success": abl_success,
                "return": 81.0 if abl_success else 9.0,
                "min_clearance_margin": abl_margin,
                "obstacle_label": label,
            }
        )
    return pd.DataFrame(rows)


def test_build_response_necessity_features_scores_hard_perturbation_seeds():
    features = build_response_necessity_features(
        _paired_frame(),
        baseline_policy="base",
        ablation_policies=["base_reset"],
        near_margin=0.05,
        margin_scale=0.25,
    )

    assert features.iloc[0]["seed"] == 2
    seed2 = features[features["seed"] == 2].iloc[0]
    assert seed2["baseline_success_drop"] == 1
    assert "perturbation_regression" in seed2["critical_reason"]
    assert "low_perturbed_margin" in seed2["critical_reason"]
    seed3 = features[features["seed"] == 3].iloc[0]
    assert seed3["critical_reason"] == ""


def test_select_response_necessity_corpus_excludes_easy_seed():
    features = build_response_necessity_features(
        _paired_frame(),
        baseline_policy="base",
        ablation_policies=["base_reset"],
        near_margin=0.05,
        margin_scale=0.25,
    )

    corpus = select_response_necessity_corpus(features, top_k=10)

    assert set(corpus["seed"]) == {1, 2}


def test_build_seed_sequence_repeats_selected_seeds():
    features = build_response_necessity_features(
        _paired_frame(),
        baseline_policy="base",
        ablation_policies=["base_reset"],
    )
    corpus = select_response_necessity_corpus(features, top_k=1)

    sequence = build_seed_sequence(corpus, repeat=3)

    assert sequence["seed"].tolist() == [int(corpus.iloc[0]["seed"])] * 3
    assert set(sequence.columns) == {"seed", "rank", "response_necessity_score", "critical_reason"}


def test_write_response_necessity_corpus_writes_training_seed_sequence(tmp_path):
    episodes_csv = tmp_path / "episodes.csv"
    _paired_frame().to_csv(episodes_csv, index=False)

    manifest = write_response_necessity_corpus(
        tmp_path / "corpus",
        episodes_csv=episodes_csv,
        baseline_policy="base",
        ablation_policies=["base_reset"],
        top_k=2,
        repeat=2,
    )

    assert manifest["summary"]["selected_count"] == 2
    assert manifest["summary"]["seed_sequence_count"] == 4
    assert (tmp_path / "corpus" / "seed_response_necessity.csv").exists()
    assert (tmp_path / "corpus" / "scenario_corpus.csv").exists()
    assert (tmp_path / "corpus" / "seed_sequence.csv").exists()
    assert (tmp_path / "corpus" / "summary.csv").exists()
