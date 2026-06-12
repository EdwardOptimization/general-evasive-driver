from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path("scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("c5prime_c1_oracle_bc_warmstart", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_structured_tail_action_parses_supported_a3_candidates():
    mod = _load_module()

    np.testing.assert_allclose(
        mod.structured_tail_action("structured:full_brake", 0),
        np.array([0.0, -1.0, 1.0], dtype=np.float32),
    )
    np.testing.assert_allclose(
        mod.structured_tail_action("structured:brake_steer_-0.4", 0),
        np.array([-0.4, -1.0, 1.0], dtype=np.float32),
    )
    np.testing.assert_allclose(
        mod.structured_tail_action("structured:coast_steer_+0.7", 0),
        np.array([0.7, -1.0, -1.0], dtype=np.float32),
    )
    np.testing.assert_allclose(
        mod.structured_tail_action("structured:swerve_+1_n10", 9),
        np.array([1.0, -1.0, 1.0], dtype=np.float32),
    )
    np.testing.assert_allclose(
        mod.structured_tail_action("structured:swerve_+1_n10", 10),
        np.array([0.0, -1.0, 1.0], dtype=np.float32),
    )


def test_c1_prereg_selects_one_structured_row_per_target_instance():
    mod = _load_module()
    payload = mod.build_preregistration()
    rows = payload["selected_rows"]

    assert len(rows) == 36
    assert {row["level"] for row in rows} == {"S1", "S2", "S3"}
    assert all(row["oracle_by"].startswith("structured:") for row in rows)
    assert all(row["surface"] == "T_limit" for row in rows)
    assert all(row["bc_role"] in {"train", "selection", "validation"} for row in rows)

    keys = {(row["level"], row["instance"]) for row in rows}
    assert len(keys) == 36
    for level in ("S1", "S2", "S3"):
        assert {instance for row_level, instance in keys if row_level == level} == set(range(12))

    role_counts = payload["selection_rule"]["role_counts"]
    assert role_counts["train"] > role_counts["selection"] >= 1
    assert role_counts["validation"] >= 1


def test_c1_v2_tail_balanced_prereg_adds_train_support_for_heldout_oracles():
    mod = _load_module()
    payload = mod.build_preregistration(revision=mod.REVISION_V2)
    rows = payload["selected_rows"]

    assert payload["revision"] == "v2_tail_balanced"
    assert payload["seed_base"] != mod.SEED_BASE
    assert len(rows) >= 36

    train_oracles = {row["oracle_by"] for row in rows if row["bc_role"] == "train"}
    heldout_oracles = {
        row["oracle_by"]
        for row in rows
        if row["bc_role"] in {"selection", "validation"}
    }
    support_rows = [
        row
        for row in rows
        if row.get("selection_source") in {"heldout_oracle_family_support", "rare_tail_train_support"}
    ]
    validation_probes = [
        row for row in rows if row.get("selection_source") == "rare_tail_validation_probe"
    ]

    assert heldout_oracles <= train_oracles
    assert support_rows
    assert all(row["bc_role"] == "train" for row in support_rows)
    assert {
        row["oracle_by"]
        for row in support_rows
    } <= heldout_oracles
    assert {
        "structured:coast_steer_+0.7",
        "structured:coast_steer_-0.7",
    } <= train_oracles
    assert {
        "structured:coast_steer_+0.7",
        "structured:coast_steer_-0.7",
    } <= {row["oracle_by"] for row in validation_probes}
