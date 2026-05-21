import numpy as np
import pandas as pd

from autodrift.margin_critical_corpus import (
    add_margin_critical_features,
    build_margin_critical_corpus,
    build_source_seed_delta,
    load_episode_sources,
    summarize_policy_margins,
    write_margin_critical_corpus,
)
from autodrift.seed_delta_audit import build_policy_delta


def _episodes_frame() -> pd.DataFrame:
    rows = []
    for seed, base_success, base_margin, cand_success, cand_margin, obstacle_label in [
        (1, True, 0.10, True, 0.015, "drift_required"),
        (2, False, -0.015, True, 0.006, "unavoidable"),
        (3, True, 0.20, True, 0.196, "drift_required"),
        (4, True, 4.00, True, 3.80, "drift_required"),
    ]:
        rows.append(
            {
                "seed": seed,
                "policy": "base",
                "success": base_success,
                "return": 10.0 if base_success else 1.0,
                "steps": 20,
                "min_clearance_margin": base_margin,
                "min_obstacle_clearance": base_margin + 1.7,
                "obstacle_collision_radius": 1.7,
                "obstacle_label": obstacle_label,
                "mu_bucket": "low" if seed != 3 else "medium",
            }
        )
        rows.append(
            {
                "seed": seed,
                "policy": "candidate",
                "success": cand_success,
                "return": 10.5 if cand_success else 1.5,
                "steps": 20,
                "min_clearance_margin": cand_margin,
                "min_obstacle_clearance": cand_margin + 1.7,
                "obstacle_collision_radius": 1.7,
                "obstacle_label": obstacle_label,
                "mu_bucket": "low" if seed != 3 else "medium",
            }
        )
    return pd.DataFrame(rows)


def test_add_margin_critical_features_flags_near_and_regressed_cases():
    deltas = build_policy_delta(_episodes_frame(), "base", "candidate")
    output = add_margin_critical_features(deltas, near_margin=0.02, min_abs_margin_delta=0.01)

    seed1 = output[output["seed"] == 1].iloc[0]
    seed2 = output[output["seed"] == 2].iloc[0]
    seed3 = output[output["seed"] == 3].iloc[0]

    assert seed1["candidate_margin_bucket"] == "success_near"
    assert bool(seed1["margin_regressed"])
    assert bool(seed1["near_margin_regressed"])
    assert bool(seed1["success_preserved_margin_regressed"])
    assert "near_margin_regressed" in seed1["critical_reason"]
    assert bool(seed2["binary_outcome_changed"])
    assert bool(seed2["near_boundary"])
    assert seed3["critical_reason"] == ""
    seed4 = output[output["seed"] == 4].iloc[0]
    assert bool(seed4["margin_regressed"])
    assert not bool(seed4["near_margin_regressed"])
    assert seed4["critical_reason"] == ""


def test_build_margin_critical_corpus_selects_only_critical_rows():
    deltas, corpus, policy_summary, bucket_summary = build_margin_critical_corpus(
        _episodes_frame(),
        baseline_policy="base",
        candidate_policies=["candidate"],
        near_margin=0.02,
        min_abs_margin_delta=0.01,
        top_k=10,
    )

    assert deltas["seed"].tolist() == [2, 1, 3, 4]
    assert set(corpus["seed"].tolist()) == {1, 2}
    summary = policy_summary.iloc[0]
    assert int(summary["critical_seeds"]) == 2
    assert int(summary["margin_regressed_seeds"]) == 2
    assert int(summary["near_margin_regressed_seeds"]) == 1
    assert np.isclose(summary["margin_delta_mean"], (-0.085 + 0.021 - 0.004 - 0.2) / 4.0)
    assert "candidate_margin_bucket" in set(bucket_summary["group_column"])


def test_write_margin_critical_corpus_writes_manifest_and_csvs(tmp_path):
    episodes_csv = tmp_path / "episodes.csv"
    _episodes_frame().to_csv(episodes_csv, index=False)

    manifest = write_margin_critical_corpus(
        tmp_path / "corpus",
        episodes_csvs=[episodes_csv],
        baseline_policy="base",
        candidate_policies=["candidate"],
        near_margin=0.02,
        min_abs_margin_delta=0.01,
        top_k=10,
    )

    assert manifest["summary"]["selected_count"] == 2
    assert (tmp_path / "corpus" / "seed_margin_deltas.csv").exists()
    assert (tmp_path / "corpus" / "scenario_corpus.csv").exists()
    assert (tmp_path / "corpus" / "policy_margin_summary.csv").exists()
    assert (tmp_path / "corpus" / "margin_bucket_summary.csv").exists()


def test_load_episode_sources_adds_parent_directory_source(tmp_path):
    run_dir = tmp_path / "benchmark_run"
    run_dir.mkdir()
    episodes_csv = run_dir / "episodes.csv"
    _episodes_frame().to_csv(episodes_csv, index=False)

    frame = load_episode_sources([episodes_csv])

    assert frame["source"].unique().tolist() == ["benchmark_run"]


def test_build_source_seed_delta_allows_overlapping_seed_ids_across_sources():
    first = _episodes_frame().copy()
    first["source"] = "first"
    second = _episodes_frame().copy()
    second["source"] = "second"

    delta = build_source_seed_delta(
        pd.concat([first, second], ignore_index=True),
        baseline_policy="base",
        candidate_policies=["candidate"],
    )

    assert len(delta) == 8
    assert set(delta["source"]) == {"first", "second"}
