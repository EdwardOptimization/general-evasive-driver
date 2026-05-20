import pandas as pd

from autodrift.env import DriftEnvConfig, FrictionStepConfig, ObstacleTaskConfig
from autodrift.near_threshold_corpus import collect_candidate_rows, select_near_threshold_rows
from autodrift.paired_perturbation_gate import (
    build_pair_summary,
    condition_config,
    load_seed_csv,
    parse_randomization_overrides,
    parse_range,
)


def test_condition_config_changes_only_friction_step_mu_range():
    base = DriftEnvConfig(friction_step=FrictionStepConfig(enabled=True, mu_range=(0.4, 0.8)))

    changed = condition_config(base, (0.2, 0.3))

    assert changed.friction_step.enabled
    assert changed.friction_step.mu_range == (0.2, 0.3)
    assert changed.friction_step.resample_speed_ref is False
    assert changed.obstacle == base.obstacle


def test_condition_config_can_override_randomization_ranges():
    base = DriftEnvConfig(friction_step=FrictionStepConfig(enabled=True, mu_range=(0.4, 0.8)))

    changed = condition_config(
        base,
        friction_mu_range=(0.25, 0.35),
        randomization_overrides={
            "actuator_tau_scale_range": (2.0, 3.0),
            "brake_scale_range": (0.5, 0.7),
        },
    )

    assert changed.friction_step.mu_range == (0.25, 0.35)
    assert changed.randomization.actuator_tau_scale_range == (2.0, 3.0)
    assert changed.randomization.brake_scale_range == (0.5, 0.7)
    assert base.randomization.actuator_tau_scale_range != changed.randomization.actuator_tau_scale_range


def test_parse_randomization_overrides_requires_known_key():
    assert parse_randomization_overrides(["drive_scale_range=0.5,0.8"]) == {
        "drive_scale_range": (0.5, 0.8)
    }

    try:
        parse_randomization_overrides(["unknown_range=0.5,0.8"])
    except ValueError as exc:
        assert "unknown randomization" in str(exc)
    else:
        raise AssertionError("unknown randomization override should be rejected")


def test_build_pair_summary_reports_success_drop_and_return_delta():
    frame = pd.DataFrame(
        [
            {"condition": "nominal", "policy": "driver", "seed": 1, "success": True, "return": 10.0},
            {"condition": "perturbed", "policy": "driver", "seed": 1, "success": False, "return": 3.0},
            {"condition": "nominal", "policy": "driver", "seed": 2, "success": True, "return": 8.0},
            {"condition": "perturbed", "policy": "driver", "seed": 2, "success": True, "return": 7.0},
        ]
    )

    summary = build_pair_summary(frame)

    assert summary.loc[0, "pairs"] == 2
    assert summary.loc[0, "nominal_success"] == 1.0
    assert summary.loc[0, "perturbed_success"] == 0.5
    assert summary.loc[0, "success_drop"] == 0.5
    assert summary.loc[0, "return_delta"] == -4.0


def test_parse_range_requires_low_high_pair():
    assert parse_range("0.25,0.55") == (0.25, 0.55)


def test_load_seed_csv_reads_ordered_seeds(tmp_path):
    path = tmp_path / "seeds.csv"
    path.write_text("seed\n42\n44\n", encoding="utf-8")

    assert load_seed_csv(path) == [42, 44]


def test_select_near_threshold_rows_filters_and_sorts():
    rows = [
        {"seed": 1, "obstacle_label": "unavoidable", "threshold_score": 0.10, "time_after_step": 0.5},
        {"seed": 2, "obstacle_label": "drift_required", "threshold_score": 0.03, "time_after_step": 0.2},
        {"seed": 3, "obstacle_label": "aeb_feasible", "threshold_score": 0.01, "time_after_step": 0.5},
        {"seed": 4, "obstacle_label": "drift_required", "threshold_score": 0.02, "time_after_step": 0.05},
    ]

    selected = select_near_threshold_rows(
        rows,
        count=2,
        labels=("drift_required", "unavoidable"),
        max_threshold_score=0.20,
        min_time_after_step=0.10,
    )

    assert [row["seed"] for row in selected] == [2, 1]


def test_collect_near_threshold_candidates_include_bucket_columns():
    config = DriftEnvConfig(
        friction_step=FrictionStepConfig(enabled=True, step_range=(2, 2)),
        obstacle=ObstacleTaskConfig(enabled=True),
    )

    rows = collect_candidate_rows(config, seed_start=10, max_candidates=2)

    assert rows
    assert "terminated" in rows[0]
    assert "threshold_score" in rows[0]
    assert "time_after_step" in rows[0]
