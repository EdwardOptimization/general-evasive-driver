import argparse

import numpy as np
import pandas as pd
import pytest

from autodrift.m183_row16_active_set_anchor_export import (
    parse_row_ids,
    save_trajectory_anchor,
    select_required_rows,
)


def _corpus_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "row_id": 15,
                "target": "future_braking_deceleration",
                "physical_pair_key": "a",
                "left_seed": 1,
                "right_seed": 2,
                "left_step": 3,
                "right_step": 4,
                "relocated_obstacle_body_x": 9.0,
                "relocated_obstacle_body_y": 0.5,
                "relocated_obstacle_half_width": 0.7,
            },
            {
                "row_id": 16,
                "target": "future_braking_deceleration",
                "physical_pair_key": "b",
                "left_seed": 5,
                "right_seed": 6,
                "left_step": 7,
                "right_step": 8,
                "relocated_obstacle_body_x": 10.0,
                "relocated_obstacle_body_y": -0.5,
                "relocated_obstacle_half_width": 0.8,
            },
        ]
    )


def test_parse_row_ids_validates_nonempty() -> None:
    assert parse_row_ids("16, 17") == (16, 17)

    with pytest.raises(argparse.ArgumentTypeError):
        parse_row_ids("")


def test_select_required_rows_requires_present_row_ids() -> None:
    selected = select_required_rows(_corpus_frame(), row_ids=(16,))

    assert selected["row_id"].tolist() == [16]

    with pytest.raises(ValueError):
        select_required_rows(_corpus_frame(), row_ids=(99,))


def test_save_trajectory_anchor_rejects_empty_and_writes_arrays(tmp_path) -> None:
    path = tmp_path / "anchor.npz"
    with pytest.raises(ValueError):
        save_trajectory_anchor(
            path,
            observation=np.zeros((0, 72), dtype=np.float32),
            hidden=np.zeros((0, 128), dtype=np.float32),
            reference_action=np.zeros((0, 3), dtype=np.float32),
            source_index=np.zeros((0,), dtype=np.int64),
            step_index=np.zeros((0,), dtype=np.int64),
            weight=np.zeros((0,), dtype=np.float32),
        )

    save_trajectory_anchor(
        path,
        observation=np.zeros((2, 72), dtype=np.float32),
        hidden=np.zeros((2, 128), dtype=np.float32),
        reference_action=np.zeros((2, 3), dtype=np.float32),
        source_index=np.asarray([0, 0], dtype=np.int64),
        step_index=np.asarray([0, 1], dtype=np.int64),
        weight=np.ones((2,), dtype=np.float32),
    )

    arrays = np.load(path)
    assert arrays["observation"].shape == (2, 72)
    assert arrays["hidden"].shape == (2, 128)
    assert arrays["reference_action"].shape == (2, 3)
