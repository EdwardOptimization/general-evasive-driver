from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5prime_c1_v3_residual_rl_smoke as smoke  # noqa: E402
import c5prime_c1_v4_distill_stage_a as stage_a  # noqa: E402
import c5prime_c1_v4_stage_b_guarded_rl as stage_b  # noqa: E402


def test_stage_b_training_rows_are_balanced_and_disjoint() -> None:
    train_rows = stage_b.sample_training_rows(rows_per_level=2)
    validation_rows = stage_a.validation_rows(limit_per_level=3)

    assert [row["level"] for row in train_rows] == ["S1", "S1", "S2", "S2", "S3", "S3"]
    assert all(row["surface"] == "T_limit" for row in train_rows)
    assert all(int(row["eval_seed"]) >= 9_000_000 for row in train_rows)

    train_eval_seeds = {int(row["eval_seed"]) for row in train_rows}
    validation_eval_seeds = {int(row["eval_seed"]) for row in validation_rows}
    assert train_eval_seeds.isdisjoint(validation_eval_seeds)
    assert {smoke.row_id(row) for row in train_rows}.isdisjoint({smoke.row_id(row) for row in validation_rows})


def test_warm_start_model_copies_distiller_outputs(tmp_path: Path) -> None:
    torch.manual_seed(123)
    distiller = stage_a.ResidualDistiller()
    checkpoint = tmp_path / "distiller.pt"
    torch.save({"model_state": distiller.state_dict()}, checkpoint)

    warm = stage_b.init_model_from_distiller_checkpoint(checkpoint, seed=456)
    obs = torch.randn(5, smoke.OBS_DIM)

    with torch.no_grad():
        distiller_out = distiller(obs)
        dist, _value = warm.forward(obs)
        warm_out = torch.tanh(dist.mean)

    torch.testing.assert_close(warm_out, distiller_out)
    assert warm.log_std.requires_grad is False


def test_aggregate_stage_b_recapture_and_extension_rules() -> None:
    val_rows: list[dict[str, str]] = []
    candidate_rows: list[dict[str, object]] = []
    seeds = [101, 102]
    for level_index, level in enumerate(stage_b.TARGET_LEVELS):
        for row_index in range(4):
            val_row = {
                "level": level,
                "surface": "T_limit",
                "instance": str(row_index),
                "eval_seed": str(2000 + 100 * level_index + row_index),
                "fixed_v4_incumbent_outcome": "collision",
                "v4_pertuned_outcome": "success" if row_index < 2 else "collision",
                "oracle_solved": "True",
            }
            val_rows.append(val_row)
            for seed in seeds:
                candidate_rows.append(
                    {
                        "training_seed": seed,
                        "row_id": smoke.row_id(val_row),
                        "level": level,
                        "v4_stage_b_outcome": "success" if row_index < 3 else "collision",
                    }
                )

    aggregate = stage_b.aggregate_results(candidate_rows, val_rows)

    assert aggregate["stage_b_pass"] is True
    assert aggregate["extension_admitted"] is False
    assert aggregate["n_pass_cells"] == 3
    for cell in aggregate["cells"].values():
        assert cell["candidate_minus_pertuned"] == 0.25
        assert cell["cell_pass"] is True


def test_aggregate_stage_b_admits_extension_on_movement_only() -> None:
    val_rows: list[dict[str, str]] = []
    candidate_rows: list[dict[str, object]] = []
    seeds = [101, 102]
    for level_index, level in enumerate(stage_b.TARGET_LEVELS):
        for row_index in range(12):
            val_row = {
                "level": level,
                "surface": "T_limit",
                "instance": str(row_index),
                "eval_seed": str(3000 + 100 * level_index + row_index),
                "fixed_v4_incumbent_outcome": "collision",
                "v4_pertuned_outcome": "success" if row_index < 6 else "collision",
                "oracle_solved": "True",
            }
            val_rows.append(val_row)
            candidate_success = level == "S1" and row_index < 7
            for seed in seeds:
                candidate_rows.append(
                    {
                        "training_seed": seed,
                        "row_id": smoke.row_id(val_row),
                        "level": level,
                        "v4_stage_b_outcome": "success" if candidate_success else val_row["v4_pertuned_outcome"],
                    }
                )

    aggregate = stage_b.aggregate_results(candidate_rows, val_rows)

    assert aggregate["stage_b_pass"] is False
    assert aggregate["extension_admitted"] is True
    assert aggregate["movement_cells"] == ["S1/T_limit"]
