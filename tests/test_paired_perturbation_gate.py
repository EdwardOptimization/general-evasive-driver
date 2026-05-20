import pandas as pd

from autodrift.env import DriftEnvConfig, FrictionStepConfig
from autodrift.paired_perturbation_gate import build_pair_summary, condition_config, parse_range


def test_condition_config_changes_only_friction_step_mu_range():
    base = DriftEnvConfig(friction_step=FrictionStepConfig(enabled=True, mu_range=(0.4, 0.8)))

    changed = condition_config(base, (0.2, 0.3))

    assert changed.friction_step.enabled
    assert changed.friction_step.mu_range == (0.2, 0.3)
    assert changed.friction_step.resample_speed_ref is False
    assert changed.obstacle == base.obstacle


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
