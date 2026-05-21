import pandas as pd

from autodrift.hard_response_corpus import mine_hard_response_corpus, write_hard_response_run


def test_mine_hard_response_corpus_selects_ablation_changed_seed():
    episodes = pd.DataFrame(
        [
            {"seed": 1, "policy": "driver", "condition": "nominal", "success": True, "return": 10.0},
            {"seed": 1, "policy": "driver", "condition": "perturbed", "success": True, "return": 9.0},
            {"seed": 1, "policy": "driver_reset", "condition": "nominal", "success": False, "return": 1.0},
            {"seed": 1, "policy": "driver_reset", "condition": "perturbed", "success": True, "return": 8.0},
            {"seed": 2, "policy": "driver", "condition": "nominal", "success": True, "return": 11.0},
            {"seed": 2, "policy": "driver", "condition": "perturbed", "success": True, "return": 10.0},
            {"seed": 2, "policy": "driver_reset", "condition": "nominal", "success": True, "return": 10.5},
            {"seed": 2, "policy": "driver_reset", "condition": "perturbed", "success": True, "return": 9.5},
        ]
    )

    corpus, hard_pairs = mine_hard_response_corpus(
        episodes,
        normal_policy="driver",
        ablation_policies=["driver_reset"],
    )

    assert corpus["seed"].tolist() == [1]
    assert int(corpus.iloc[0]["changed_edges"]) == 1
    changed = hard_pairs[hard_pairs["success_changed"]]
    assert changed[["seed", "condition", "ablation_policy"]].to_dict("records") == [
        {"seed": 1, "condition": "nominal", "ablation_policy": "driver_reset"}
    ]


def test_mine_hard_response_corpus_can_include_hidden_condition_changes():
    episodes = pd.DataFrame(
        [
            {"seed": 3, "policy": "driver", "condition": "nominal", "success": True, "return": 10.0},
            {"seed": 3, "policy": "driver", "condition": "perturbed", "success": False, "return": 0.0},
            {"seed": 3, "policy": "driver_zero", "condition": "nominal", "success": True, "return": 9.0},
            {"seed": 3, "policy": "driver_zero", "condition": "perturbed", "success": False, "return": -1.0},
        ]
    )

    strict_corpus, _ = mine_hard_response_corpus(
        episodes,
        normal_policy="driver",
        ablation_policies=["driver_zero"],
    )
    relaxed_corpus, _ = mine_hard_response_corpus(
        episodes,
        normal_policy="driver",
        ablation_policies=["driver_zero"],
        include_hidden_condition_changes=True,
    )

    assert strict_corpus.empty
    assert relaxed_corpus["seed"].tolist() == [3]
    assert bool(relaxed_corpus.iloc[0]["normal_condition_change"])


def test_write_hard_response_run_writes_seed_csv(tmp_path):
    corpus = pd.DataFrame([{"seed": 7, "changed_edges": 2}])
    hard_pairs = pd.DataFrame([{"seed": 7, "success_changed": True}])

    summary = write_hard_response_run(
        tmp_path,
        corpus,
        hard_pairs,
        episodes_csvs=[tmp_path / "episodes.csv"],
        normal_policy="driver",
        ablation_policies=["driver_reset"],
        include_hidden_condition_changes=False,
    )

    assert summary["selected"] == 1
    assert summary["success_changed_rows"] == 1
    assert (tmp_path / "scenario_corpus.csv").read_text(encoding="utf-8").startswith("seed,changed_edges")
    assert (tmp_path / "hard_pairs.csv").exists()
