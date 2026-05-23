import json

import pandas as pd

from autodrift.response_critical_ablation_corpus import (
    OUTPUT_COLUMNS,
    ResponseCriticalConfig,
    SourceSpec,
    mine_response_critical_rows,
    run_response_critical_export,
    select_compact_corpus,
)


def _rows():
    return [
        {
            "seed": 1,
            "policy": "base",
            "success": True,
            "collision": False,
            "min_clearance_margin": 0.04,
            "return": 20.0,
            "lateral_peak": 1.0,
            "beta_abs_peak": 0.05,
            "obstacle_label": "unavoidable",
            "mu": 0.3,
            "initial_mu": 0.3,
            "mass_scale": 1.0,
            "brake_scale": 0.8,
            "tire_stiffness_scale": 0.7,
            "steer_tau_scale": 1.2,
        },
        {
            "seed": 1,
            "policy": "m399_zero_current",
            "success": False,
            "collision": True,
            "min_clearance_margin": -0.02,
            "return": 10.0,
            "lateral_peak": 0.8,
            "beta_abs_peak": 0.04,
            "obstacle_label": "unavoidable",
            "mu": 0.3,
            "initial_mu": 0.3,
            "mass_scale": 1.0,
            "brake_scale": 0.8,
            "tire_stiffness_scale": 0.7,
            "steer_tau_scale": 1.2,
        },
        {
            "seed": 2,
            "policy": "base",
            "success": True,
            "collision": False,
            "min_clearance_margin": 2.0,
            "return": 30.0,
            "lateral_peak": 7.0,
            "beta_abs_peak": 0.04,
            "obstacle_label": "aes_feasible",
            "mu": 0.9,
            "initial_mu": 0.9,
            "mass_scale": 1.1,
            "brake_scale": 1.0,
            "tire_stiffness_scale": 1.1,
            "steer_tau_scale": 1.0,
        },
        {
            "seed": 2,
            "policy": "m399_reset",
            "success": False,
            "collision": False,
            "min_clearance_margin": 1.9,
            "return": 25.0,
            "lateral_peak": 8.3,
            "beta_abs_peak": 0.06,
            "obstacle_label": "aes_feasible",
            "mu": 0.9,
            "initial_mu": 0.9,
            "mass_scale": 1.1,
            "brake_scale": 1.0,
            "tire_stiffness_scale": 1.1,
            "steer_tau_scale": 1.0,
        },
        {
            "seed": 3,
            "policy": "base",
            "success": False,
            "collision": True,
            "min_clearance_margin": -0.03,
            "return": 8.0,
            "lateral_peak": 0.5,
            "beta_abs_peak": 0.03,
            "obstacle_label": "drift_required",
            "mu": 0.6,
            "initial_mu": 0.6,
            "mass_scale": 0.9,
            "brake_scale": 1.2,
            "tire_stiffness_scale": 1.0,
            "steer_tau_scale": 0.9,
        },
        {
            "seed": 3,
            "policy": "m399_noact",
            "success": True,
            "collision": False,
            "min_clearance_margin": 0.02,
            "return": 18.0,
            "lateral_peak": 0.4,
            "beta_abs_peak": 0.03,
            "obstacle_label": "drift_required",
            "mu": 0.6,
            "initial_mu": 0.6,
            "mass_scale": 0.9,
            "brake_scale": 1.2,
            "tire_stiffness_scale": 1.0,
            "steer_tau_scale": 0.9,
        },
    ]


def test_response_critical_exporter_classifies_dependency_and_failure_modes():
    frame = pd.DataFrame(_rows())
    source = SourceSpec(episodes_csv="episodes.csv", source_config="unit", track_width=8.0)
    config = ResponseCriticalConfig(
        baseline_policy="base",
        candidate_policies=("m399_zero_current", "m399_reset", "m399_noact"),
    )

    candidates = mine_response_critical_rows(frame, source=source, config=config)

    assert list(candidates.columns) == OUTPUT_COLUMNS
    by_policy = {row["ablation_policy"]: row for _, row in candidates.iterrows()}
    assert by_policy["m399_zero_current"]["dependency_class"] == "current_response_sensitive"
    assert by_policy["m399_zero_current"]["failure_class"] == "obstacle_collision_margin_crossing"
    assert "margin_sign_flip" in by_policy["m399_zero_current"]["divergence_types"]
    assert by_policy["m399_reset"]["dependency_class"] == "recurrent_hidden_sensitive"
    assert by_policy["m399_reset"]["failure_class"] == "road_boundary_failure"
    assert "lateral_boundary_flip" in by_policy["m399_reset"]["divergence_types"]
    assert by_policy["m399_noact"]["dependency_class"] == "action_history_sensitive"
    assert by_policy["m399_noact"]["failure_class"] == "ablation_rescue"


def test_response_critical_compact_selection_respects_failure_class_cap():
    frame = pd.DataFrame(_rows())
    source = SourceSpec(episodes_csv="episodes.csv", source_config="unit", track_width=8.0)
    config = ResponseCriticalConfig(
        baseline_policy="base",
        candidate_policies=("m399_zero_current", "m399_reset", "m399_noact"),
        max_rows=2,
        max_rows_per_failure_class=1,
    )
    candidates = mine_response_critical_rows(frame, source=source, config=config)

    compact = select_compact_corpus(candidates, config)

    assert len(compact) == 2
    assert compact["failure_class"].nunique() == 2


def test_response_critical_cli_helper_writes_artifacts(tmp_path):
    episodes_csv = tmp_path / "episodes.csv"
    pd.DataFrame(_rows()).to_csv(episodes_csv, index=False)
    run_dir = tmp_path / "run"
    config = ResponseCriticalConfig(
        baseline_policy="base",
        candidate_policies=("m399_zero_current", "m399_reset", "m399_noact"),
    )

    summary = run_response_critical_export(
        [SourceSpec(episodes_csv=episodes_csv, source_config="unit", track_width=8.0)],
        run_dir,
        config,
    )

    assert summary["accepted_rows"] == 3
    assert summary["selected_rows"] == 3
    assert summary["accepted_by_dependency_class"]["current_response_sensitive"] == 1
    assert summary["accepted_by_failure_class"]["road_boundary_failure"] == 1
    assert (run_dir / "candidates.csv").exists()
    assert (run_dir / "compact_corpus.csv").exists()
    payload = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert payload["actor_inputs_changed"] is False
    assert payload["checkpoint_promoted"] is False
