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
