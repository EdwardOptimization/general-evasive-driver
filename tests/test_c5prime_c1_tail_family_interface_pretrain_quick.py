from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path("scripts/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("c5prime_c1_tail_family_interface_pretrain_quick", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_pretrain_rows_adds_required_rare_train_support():
    mod = _load_module()
    prereg = {
        "required_rare_validation_families": [
            "structured:coast_steer_+0.7",
            "structured:coast_steer_-0.7",
        ],
        "thresholds": {"min_train_rows_per_required_rare_family": 2},
    }

    rows = mod.build_pretrain_rows(prereg)

    for family in prereg["required_rare_validation_families"]:
        train_rows = [row for row in rows if row["bc_role"] == "train" and row["oracle_by"] == family]
        validation_rows = [row for row in rows if row["bc_role"] == "validation" and row["oracle_by"] == family]
        assert len(train_rows) >= 2
        assert validation_rows
    assert any(row.get("selection_source") == "m3236_extra_rare_tail_train_support" for row in rows)


def test_compute_metrics_reports_family_floor_and_reconstruction_error():
    mod = _load_module()
    families = ["structured:full_brake", "structured:coast_steer_-0.7"]
    arrays = {
        "obs": np.zeros((4, 72), dtype=np.float32),
        "family_id": np.asarray([0, 1, 0, 1], dtype=np.int64),
        "role_id": np.asarray([0, 0, 2, 2], dtype=np.int64),
        "tail_phase": np.asarray([0, 0, 0, 0], dtype=np.int64),
        "actions": np.asarray(
            [
                [0.0, -1.0, 1.0],
                [-0.7, -1.0, -1.0],
                [0.0, -1.0, 1.0],
                [-0.7, -1.0, -1.0],
            ],
            dtype=np.float32,
        ),
    }
    predictions = np.asarray([0, 1, 0, 0], dtype=np.int64)

    metrics = mod.compute_metrics(arrays, families, predictions)

    assert metrics["accuracy_by_role"]["validation"] == 0.5
    assert metrics["validation_family_metrics"]["structured:coast_steer_-0.7"]["accuracy"] == 0.0
    assert metrics["validation_predicted_family_reconstruction_mse"] > 0.0
    assert metrics["validation_true_family_reconstruction_mse"] == 0.0
