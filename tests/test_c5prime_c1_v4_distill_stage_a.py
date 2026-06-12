from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5_reflex_degradation as c5  # noqa: E402
import c5prime_c1_v4_distill_stage_a as stage_a  # noqa: E402
import c5prime_c1_v3_residual_rl_smoke as smoke  # noqa: E402


def test_training_rows_use_new_balanced_disjoint_seed_stream() -> None:
    train_rows = stage_a.sample_training_rows(rows_per_level=2)
    validation_rows = stage_a.validation_rows(limit_per_level=3)

    assert [row["level"] for row in train_rows] == ["S1", "S1", "S2", "S2", "S3", "S3"]
    assert all(row["surface"] == "T_limit" for row in train_rows)
    assert all(int(row["eval_seed"]) >= 8_800_000 for row in train_rows)
    assert all("pertuned_grid" in row for row in train_rows)

    train_eval_seeds = {int(row["eval_seed"]) for row in train_rows}
    validation_eval_seeds = {int(row["eval_seed"]) for row in validation_rows}
    assert train_eval_seeds.isdisjoint(validation_eval_seeds)
    assert {smoke.row_id(row) for row in train_rows}.isdisjoint({smoke.row_id(row) for row in validation_rows})


def test_pertuned_grid_parser_accepts_a3_grid() -> None:
    row = stage_a.validation_rows(limit_per_level=1)[0]

    grid = stage_a.pertuned_grid(row)

    assert grid in c5.GRID
    assert isinstance(grid[0], float)


def test_exploratory_delta_widens_only_overbound_channels() -> None:
    dataset = {
        "delta": np.asarray(
            [
                [0.10, 0.20, 0.30],
                [0.30, 0.10, 0.70],
            ],
            dtype=np.float32,
        )
    }

    widened = stage_a.exploratory_delta_max_from_dataset(dataset)

    np.testing.assert_allclose(widened[:2], stage_a.PRIMARY_DELTA_MAX[:2])
    assert widened[2] > stage_a.PRIMARY_DELTA_MAX[2]
    np.testing.assert_allclose(widened[2], np.float32(0.70 * stage_a.EXPLORATORY_MARGIN))


def test_aggregate_stage_a_gate_requires_all_cells_within_0p05() -> None:
    val_rows: list[dict[str, str]] = []
    candidate_rows: list[dict[str, object]] = []
    for level_index, level in enumerate(stage_a.TARGET_LEVELS):
        for row_index in range(4):
            pertuned_success = row_index < 3
            candidate_success = row_index < 3 if level != "S3" else row_index < 2
            val_row = {
                "level": level,
                "surface": "T_limit",
                "instance": str(row_index),
                "eval_seed": str(1000 + 100 * level_index + row_index),
                "fixed_v4_incumbent_outcome": "collision",
                "v4_pertuned_outcome": "success" if pertuned_success else "collision",
                "oracle_solved": "True",
            }
            val_rows.append(val_row)
            candidate_rows.append(
                {
                    "arm": "primary",
                    "row_id": smoke.row_id(val_row),
                    "level": level,
                    "candidate_outcome": "success" if candidate_success else "collision",
                }
            )

    aggregate = stage_a.aggregate_candidate(candidate_rows, val_rows, arm_name="primary")

    assert aggregate["stage_a_pass"] is False
    assert aggregate["n_pass_cells"] == 2
    assert aggregate["cells"]["S1/T_limit"]["cell_pass"] is True
    assert aggregate["cells"]["S2/T_limit"]["cell_pass"] is True
    assert aggregate["cells"]["S3/T_limit"]["cell_pass"] is False
