import numpy as np
import pandas as pd

from autodrift.seed_delta_audit import (
    build_policy_delta,
    build_seed_delta_audit,
    load_episodes,
    summarize_group_deltas,
    summarize_policy_deltas,
    write_audit,
)


def _episodes_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "seed": 1,
                "policy": "base",
                "success": True,
                "return": 10.0,
                "steps": 20,
                "lateral_rmse": 0.2,
                "obstacle_label": "drift_required",
                "mu_bucket": "low",
            },
            {
                "seed": 1,
                "policy": "candidate",
                "success": False,
                "return": 5.0,
                "steps": 14,
                "lateral_rmse": 0.4,
                "obstacle_label": "drift_required",
                "mu_bucket": "low",
            },
            {
                "seed": 2,
                "policy": "base",
                "success": False,
                "return": 2.0,
                "steps": 9,
                "lateral_rmse": 1.1,
                "obstacle_label": "unavoidable",
                "mu_bucket": "medium",
            },
            {
                "seed": 2,
                "policy": "candidate",
                "success": True,
                "return": 7.0,
                "steps": 18,
                "lateral_rmse": 0.6,
                "obstacle_label": "unavoidable",
                "mu_bucket": "medium",
            },
            {
                "seed": 3,
                "policy": "base",
                "success": True,
                "return": 11.0,
                "steps": 21,
                "lateral_rmse": 0.3,
                "obstacle_label": "drift_required",
                "mu_bucket": "high",
            },
            {
                "seed": 3,
                "policy": "candidate",
                "success": True,
                "return": 12.0,
                "steps": 21,
                "lateral_rmse": 0.25,
                "obstacle_label": "drift_required",
                "mu_bucket": "high",
            },
        ]
    )


def test_build_policy_delta_classifies_seed_outcomes():
    delta = build_policy_delta(_episodes_frame(), "base", "candidate")

    assert delta["seed"].tolist() == [1, 2, 3]
    assert delta["outcome"].tolist() == ["regressed", "improved", "unchanged_success"]
    assert delta["success_delta"].tolist() == [-1, 1, 0]
    assert np.isclose(delta.loc[delta["seed"] == 1, "return_delta"].iloc[0], -5.0)
    assert np.isclose(delta.loc[delta["seed"] == 2, "lateral_rmse_delta"].iloc[0], -0.5)


def test_summarize_policy_deltas_counts_improvements_and_regressions():
    delta = build_seed_delta_audit(_episodes_frame(), baseline_policy="base", candidate_policies=["candidate"])
    summary = summarize_policy_deltas(delta).iloc[0]

    assert int(summary["pairs"]) == 3
    assert np.isclose(summary["baseline_success_rate"], 2.0 / 3.0)
    assert np.isclose(summary["candidate_success_rate"], 2.0 / 3.0)
    assert int(summary["improved_seeds"]) == 1
    assert int(summary["regressed_seeds"]) == 1
    assert int(summary["unchanged_success_seeds"]) == 1
    assert np.isclose(summary["return_delta_mean"], 1.0 / 3.0)


def test_summarize_group_deltas_reports_context_buckets():
    delta = build_policy_delta(_episodes_frame(), "base", "candidate")
    group_summary = summarize_group_deltas(delta, ["obstacle_label", "mu_bucket"])

    drift = group_summary[
        (group_summary["group_column"] == "obstacle_label")
        & (group_summary["group_value"] == "drift_required")
    ].iloc[0]
    assert int(drift["pairs"]) == 2
    assert np.isclose(drift["success_delta_rate"], -0.5)
    assert int(drift["regressed_seeds"]) == 1


def test_load_episodes_derives_success_from_terminated(tmp_path):
    path = tmp_path / "episodes.csv"
    path.write_text("seed,policy,terminated,return\n1,a,False,1.0\n2,a,True,0.0\n", encoding="utf-8")

    frame = load_episodes(path)

    assert frame["success"].tolist() == [True, False]


def test_write_audit_writes_manifest_and_csvs(tmp_path):
    episodes_csv = tmp_path / "episodes.csv"
    _episodes_frame().to_csv(episodes_csv, index=False)

    manifest = write_audit(
        tmp_path / "audit",
        episodes_csv=episodes_csv,
        baseline_policy="base",
        candidate_policies=["candidate"],
        group_columns=["obstacle_label"],
    )

    assert (tmp_path / "audit" / "seed_deltas.csv").exists()
    assert (tmp_path / "audit" / "policy_delta_summary.csv").exists()
    assert (tmp_path / "audit" / "group_delta_summary.csv").exists()
    assert manifest["baseline_policy"] == "base"
    assert manifest["candidate_policies"] == ["candidate"]
