from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5prime_c1_v3_residual_rl_stage1 as stage1  # noqa: E402
import c5prime_c1_v3_residual_rl_smoke as smoke  # noqa: E402


def test_training_rows_are_balanced_and_disjoint_from_validation_stream() -> None:
    train_rows = stage1.sample_training_rows(rows_per_level=2)
    validation_rows = stage1.validation_rows(limit_per_level=3)

    assert [row["level"] for row in train_rows] == ["S1", "S1", "S2", "S2", "S3", "S3"]
    assert all(row["surface"] == "T_limit" for row in train_rows)
    assert all(row["gen_label"] in {"aeb_feasible", "aes_feasible"} for row in train_rows)
    assert all(row["instance_label"] in {"aeb", "aes", "drift"} for row in train_rows)

    train_eval_seeds = {int(row["eval_seed"]) for row in train_rows}
    validation_eval_seeds = {int(row["eval_seed"]) for row in validation_rows}
    assert train_eval_seeds.isdisjoint(validation_eval_seeds)
    assert {smoke.row_id(row) for row in train_rows}.isdisjoint({smoke.row_id(row) for row in validation_rows})


def test_aggregate_results_applies_recapture_gate_per_cell() -> None:
    val_rows: list[dict[str, str]] = []
    candidate_rows: list[dict[str, object]] = []
    training_seeds = [101, 102]
    for level_index, level in enumerate(stage1.TARGET_LEVELS):
        for row_index in range(4):
            val_row = {
                "level": level,
                "surface": "T_limit",
                "instance": str(row_index),
                "eval_seed": str(1000 + 100 * level_index + row_index),
                "fixed_v4_incumbent_outcome": "success" if row_index == 0 else "collision",
                "v4_pertuned_outcome": "success" if row_index < 2 else "collision",
                "oracle_solved": "True",
            }
            val_rows.append(val_row)
            row_id = smoke.row_id(val_row)
            for seed in training_seeds:
                candidate_rows.append(
                    {
                        "training_seed": seed,
                        "row_id": row_id,
                        "level": level,
                        "v4_residual_outcome": "success" if row_index < 3 else "collision",
                    }
                )

    aggregate = stage1.aggregate_results(candidate_rows, val_rows)

    assert aggregate["stage1_pass"] is True
    assert aggregate["n_pass_cells"] == 3
    assert aggregate["pass_cells"] == ["S1/T_limit", "S2/T_limit", "S3/T_limit"]
    for cell_summary in aggregate["cells"].values():
        assert cell_summary["v4_pertuned_success"] == 0.5
        assert cell_summary["v4_residual_success"] == 0.75
        assert cell_summary["candidate_minus_pertuned"] == 0.25
        assert cell_summary["cell_pass"] is True
