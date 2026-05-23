import json

import pandas as pd

from autodrift.policy_difference_miner import (
    OUTPUT_COLUMNS,
    PolicyDifferenceConfig,
    mine_policy_differences,
    run_policy_difference_miner,
    select_compact_corpus,
)


def _episode_rows():
    return [
        {
            "seed": 1,
            "policy": "base",
            "success": True,
            "collision": False,
            "min_clearance_margin": 0.02,
            "return": 10.0,
            "obstacle_label": "drift_required",
            "mu": 0.4,
            "initial_mu": 0.4,
            "mass_scale": 1.0,
            "brake_scale": 1.0,
            "steer_tau_scale": 1.0,
        },
        {
            "seed": 1,
            "policy": "cand_a",
            "success": False,
            "collision": True,
            "min_clearance_margin": -0.01,
            "return": 6.0,
            "obstacle_label": "drift_required",
            "mu": 0.4,
            "initial_mu": 0.4,
            "mass_scale": 1.0,
            "brake_scale": 1.0,
            "steer_tau_scale": 1.0,
        },
        {
            "seed": 2,
            "policy": "base",
            "success": True,
            "collision": False,
            "min_clearance_margin": 0.10,
            "return": 20.0,
            "obstacle_label": "aes_feasible",
            "mu": 0.7,
            "initial_mu": 0.7,
            "mass_scale": 1.1,
            "brake_scale": 0.8,
            "steer_tau_scale": 1.3,
        },
        {
            "seed": 2,
            "policy": "cand_a",
            "success": True,
            "collision": False,
            "min_clearance_margin": 0.13,
            "return": 20.2,
            "obstacle_label": "aes_feasible",
            "mu": 0.7,
            "initial_mu": 0.7,
            "mass_scale": 1.1,
            "brake_scale": 0.8,
            "steer_tau_scale": 1.3,
        },
        {
            "seed": 3,
            "policy": "base",
            "success": True,
            "collision": False,
            "min_clearance_margin": 1.00,
            "return": 30.0,
            "obstacle_label": "unavoidable",
            "mu": 1.0,
            "initial_mu": 1.0,
            "mass_scale": 0.9,
            "brake_scale": 1.2,
            "steer_tau_scale": 0.8,
        },
        {
            "seed": 3,
            "policy": "cand_b",
            "success": True,
            "collision": False,
            "min_clearance_margin": 1.08,
            "return": 31.5,
            "obstacle_label": "unavoidable",
            "mu": 1.0,
            "initial_mu": 1.0,
            "mass_scale": 0.9,
            "brake_scale": 1.2,
            "steer_tau_scale": 0.8,
        },
    ]


def test_policy_difference_miner_detects_outcome_and_margin_rows():
    frame = pd.DataFrame(_episode_rows())
    config = PolicyDifferenceConfig(baseline_policy="base")

    candidates = mine_policy_differences(frame, config)

    assert list(candidates.columns) == OUTPUT_COLUMNS
    assert len(candidates) == 3
    first = candidates.iloc[0]
    assert first["seed"] == 1
    assert "success_flip" in first["divergence_types"]
    assert "collision_flip" in first["divergence_types"]
    assert "margin_sign_flip" in first["divergence_types"]
    assert "return_delta" in first["divergence_types"]
    assert candidates[candidates["seed"] == 2]["divergence_types"].iloc[0] == "near_boundary_margin_delta"
    assert "large_margin_delta" in candidates[candidates["seed"] == 3]["divergence_types"].iloc[0]


def test_policy_difference_compact_selection_respects_caps():
    frame = pd.DataFrame(_episode_rows())
    config = PolicyDifferenceConfig(baseline_policy="base", max_rows=2, max_rows_per_policy=1)
    candidates = mine_policy_differences(frame, config)

    selected = select_compact_corpus(candidates, config)

    assert len(selected) == 2
    assert selected["candidate_policy"].nunique() == 2


def test_policy_difference_cli_smoke_writes_empty_artifacts(tmp_path):
    rows = [
        {"seed": 1, "policy": "base", "terminated": False, "collision": False, "min_clearance_margin": 1.0, "return": 10.0},
        {"seed": 1, "policy": "same", "terminated": False, "collision": False, "min_clearance_margin": 1.001, "return": 10.1},
    ]
    episodes_csv = tmp_path / "episodes.csv"
    pd.DataFrame(rows).to_csv(episodes_csv, index=False)
    run_dir = tmp_path / "run"

    summary = run_policy_difference_miner(
        episodes_csv,
        run_dir,
        PolicyDifferenceConfig(baseline_policy="base"),
    )

    assert summary["accepted_rows"] == 0
    assert summary["selected_rows"] == 0
    assert (run_dir / "policy_difference_candidates.csv").exists()
    assert (run_dir / "compact_policy_difference_corpus.csv").exists()
    payload = json.loads((run_dir / "policy_difference_summary.json").read_text(encoding="utf-8"))
    assert payload["actor_inputs_changed"] is False
    assert payload["checkpoint_promoted"] is False
