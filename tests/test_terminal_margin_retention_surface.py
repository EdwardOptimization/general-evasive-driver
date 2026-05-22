from __future__ import annotations

import pandas as pd

from autodrift.terminal_margin_retention_surface import (
    SurfaceSpec,
    _select_fragile_rows,
    parse_surface_spec,
)


def _row(**overrides):
    row = {
        "policy": "candidate",
        "row_id": 1,
        "target": "future_braking_deceleration",
        "physical_pair_key": "1:2:3:4",
        "left_seed": 1,
        "right_seed": 2,
        "left_step": 3,
        "right_step": 4,
        "relocated_obstacle_body_x": 12.0,
        "relocated_obstacle_body_y": 0.1,
        "relocated_obstacle_half_width": 0.8,
        "normal_success": True,
        "success_drop": True,
        "normal_margin": 0.0005,
        "wrong_history_margin": -0.005,
        "margin_gap": 0.0055,
    }
    row.update(overrides)
    return row


def test_parse_surface_spec():
    spec = parse_surface_spec("m183_m170=/tmp/replay.csv")
    assert spec.name == "m183_m170"
    assert str(spec.replay_rows_csv) == "/tmp/replay.csv"


def test_select_fragile_rows_includes_forced_boundary_row(tmp_path):
    csv_path = tmp_path / "replay.csv"
    pd.DataFrame(
        [
            _row(row_id=1, normal_margin=0.0005),
            _row(row_id=16, normal_margin=0.002),
            _row(policy="other", row_id=2, normal_margin=0.0001),
            _row(row_id=3, success_drop=False, normal_margin=0.0001),
        ]
    ).to_csv(csv_path, index=False)

    rows = _select_fragile_rows(
        [SurfaceSpec(name="m183_m170", replay_rows_csv=csv_path)],
        candidate_policy="candidate",
        max_normal_margin=0.001,
        force_keys={("m183_m170", 16)},
        allowed_regression=5e-7,
        max_weight=50.0,
        weight_epsilon=1e-6,
    )

    assert rows["row_id"].tolist() == [1, 16]
    forced = rows.loc[rows["row_id"].eq(16)].iloc[0]
    assert bool(forced["forced"])
    assert forced["retention_weight"] >= 1.0
    fragile = rows.loc[rows["row_id"].eq(1)].iloc[0]
    assert fragile["required_margin_floor"] == fragile["normal_margin"] - fragile["allowed_regression"]
