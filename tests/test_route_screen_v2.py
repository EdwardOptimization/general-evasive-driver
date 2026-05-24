from pathlib import Path

import pandas as pd

from autodrift.env import DriftEnvConfig
from autodrift.route_screen_v2 import (
    RouteScreenPolicySpec,
    build_policy_specs,
    compute_route_screen_decision,
    parse_named_path,
    run_route_screen_v2,
)


def _summary_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "policy": "l0",
                "success_rate": 0.50,
                "min_clearance_margin_mean": 0.10,
                "collision_rate": 0.25,
                "return_mean": 20.0,
            },
            {
                "policy": "l2",
                "success_rate": 0.80,
                "min_clearance_margin_mean": 0.70,
                "collision_rate": 0.10,
                "return_mean": 50.0,
            },
            {
                "policy": "candidate_bad",
                "success_rate": 0.25,
                "min_clearance_margin_mean": 0.30,
                "collision_rate": 0.20,
                "return_mean": 25.0,
            },
            {
                "policy": "candidate_good",
                "success_rate": 0.75,
                "min_clearance_margin_mean": 0.40,
                "collision_rate": 0.20,
                "return_mean": 35.0,
            },
        ]
    )


def _episode_row(seed: int, *, terminated: bool, collision: bool, margin: float, ret: float) -> dict:
    return {
        "seed": seed,
        "policy": "checkpoint",
        "steps": 10,
        "terminated": terminated,
        "truncated": False,
        "mu": 0.8,
        "initial_mu": 0.8,
        "mass_scale": 1.0,
        "cg_shift": 0.0,
        "brake_scale": 1.0,
        "tire_stiffness_scale": 1.0,
        "steer_tau_scale": 1.0,
        "return": ret,
        "lateral_rmse": 0.1,
        "lateral_peak": 0.2,
        "beta_abs_error_mean": 0.1,
        "beta_abs_peak": 0.2,
        "high_sideslip_fraction": 0.0,
        "speed_mean": 10.0,
        "action_rate_mean": 0.1,
        "collision": collision,
        "obstacle_completed": not terminated,
        "min_obstacle_clearance": 1.7 + margin,
        "obstacle_collision_radius": 1.7,
        "min_clearance_margin": margin,
        "plan_horizon": 1,
        "plan_action_rate_mean": 0.0,
    }


def test_parse_named_path_requires_named_spec():
    assert parse_named_path("l0=runs/l0.pt", option_name="--checkpoint-policy") == (
        "l0",
        Path("runs/l0.pt"),
    )

    try:
        parse_named_path("runs/l0.pt", option_name="--checkpoint-policy")
    except ValueError as exc:
        assert "NAME=PATH" in str(exc)
    else:
        raise AssertionError("expected unnamed path to fail")


def test_build_policy_specs_requires_matching_env_config_labels(tmp_path):
    config_path = tmp_path / "env.json"
    config_path.write_text('{"env": {"max_steps": 4}}', encoding="utf-8")

    specs = build_policy_specs(
        ["l0=runs/l0.pt", "l2=runs/l2.pt"],
        [f"l0={config_path}", f"l2={config_path}"],
    )

    assert [spec.label for spec in specs] == ["l0", "l2"]
    assert all(spec.env_config.max_steps == 4 for spec in specs)

    try:
        build_policy_specs(["l0=runs/l0.pt", "l2=runs/l2.pt"], [f"l0={config_path}"])
    except ValueError as exc:
        assert "missing --env-config-policy" in str(exc)
    else:
        raise AssertionError("expected missing env config label to fail")


def test_compute_route_screen_decision_rejects_below_l0_and_selects_admitted():
    decision = compute_route_screen_decision(
        _summary_frame(),
        candidate_labels=["candidate_bad", "candidate_good"],
        l0_label="l0",
        l2_label="l2",
    )

    assert decision["candidates"]["candidate_bad"]["would_admit_public_eval"] is False
    assert decision["candidates"]["candidate_bad"]["passes_l0_success"] is False
    assert decision["candidates"]["candidate_good"]["would_admit_public_eval"] is True
    assert decision["selected_candidate_label"] == "candidate_good"
    assert decision["would_admit_public_eval"] is True


def test_run_route_screen_v2_writes_no_public_row_provenance(tmp_path):
    metrics = {
        "l0": [(False, False, 0.1, 20.0), (True, True, -0.1, 5.0)],
        "l2": [(False, False, 0.7, 50.0), (False, False, 0.8, 55.0)],
        "candidate": [(True, False, 0.3, 15.0), (True, False, 0.4, 16.0)],
    }

    def fake_evaluator(**kwargs):
        label = Path(kwargs["checkpoint"]).stem
        rows = [
            _episode_row(
                seed,
                terminated=terminated,
                collision=collision,
                margin=margin,
                ret=ret,
            )
            for seed, (terminated, collision, margin, ret) in zip(kwargs["seeds"], metrics[label])
        ]
        return rows, {"episodes": len(rows), "policy": "checkpoint"}

    specs = [
        RouteScreenPolicySpec("l0", Path("l0.pt"), Path("l0_config.json"), DriftEnvConfig()),
        RouteScreenPolicySpec("l2", Path("l2.pt"), Path("l2_config.json"), DriftEnvConfig(history_length=4)),
        RouteScreenPolicySpec("candidate", Path("candidate.pt"), Path("candidate_config.json"), DriftEnvConfig()),
    ]

    summary = run_route_screen_v2(
        specs,
        candidate_labels=["candidate"],
        l0_label="l0",
        l2_label="l2",
        episodes=2,
        seed=100,
        device="cpu",
        run_dir=tmp_path,
        evaluator=fake_evaluator,
    )

    assert summary["uses_public_frozen_source_rows"] is False
    assert summary["public_row_source"] is None
    assert summary["decision"]["candidates"]["candidate"]["passes_l0_success"] is False
    assert summary["decision"]["would_admit_public_eval"] is False
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "policy_summary.csv").exists()
    episodes = pd.read_csv(tmp_path / "episodes.csv")
    assert set(episodes["route_screen_env_config"]) == {
        "l0_config.json",
        "l2_config.json",
        "candidate_config.json",
    }
