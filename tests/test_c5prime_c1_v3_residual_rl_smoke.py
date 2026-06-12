from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5prime_c1_v3_residual_rl_smoke as smoke  # noqa: E402


def test_compose_residual_action_scales_and_clips() -> None:
    base = np.array([0.9, -0.9, 0.8], dtype=np.float32)
    residual = np.array([1.0, -2.0, 0.5], dtype=np.float32)

    base_out, delta, final = smoke.compose_residual_action(base, residual)

    np.testing.assert_allclose(base_out, base)
    np.testing.assert_allclose(delta, np.array([0.35, -0.45, 0.225], dtype=np.float32))
    np.testing.assert_allclose(final, np.array([1.0, -1.0, 1.0], dtype=np.float32))


def test_select_smoke_rows_uses_all_qualified_levels() -> None:
    rows = smoke.select_smoke_rows(rows_per_level=1)

    assert [row["level"] for row in rows] == ["S1", "S2", "S3"]
    assert all(row["surface"] == "T_limit" for row in rows)
    assert all(row["oracle_solved"] == "True" for row in rows)
    assert all(row["v4_pertuned_outcome"] != "success" for row in rows)
    assert all(row["oracle_by"].startswith("structured:") for row in rows)
