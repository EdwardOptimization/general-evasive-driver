from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path("scripts/feasibility_audit/c5prime_c1_tail_family_interface_smoke.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("c5prime_c1_tail_family_interface_smoke", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_encode_interface_targets_reconstructs_tail_actions(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setattr(mod, "RUN_DIR", tmp_path)
    monkeypatch.setattr(mod, "TARGETS_NPZ", tmp_path / "interface_targets.npz")
    actions = np.asarray(
        [
            [0.1, -0.2, -0.3],
            [0.2, -0.3, -0.4],
            [0.7, -1.0, -1.0],
            [0.7, -1.0, -1.0],
        ],
        dtype=np.float32,
    )
    demos = [
        {
            "row_id": "r0",
            "obs": np.zeros((4, 72), dtype=np.float32),
            "actions": actions,
        }
    ]
    rows = [
        {
            "row_id": "r0",
            "bc_role": "validation",
            "oracle_by": "structured:coast_steer_+0.7",
            "reveal_step": 2,
        }
    ]

    payload = mod.encode_interface_targets(demos, rows)

    assert payload["tail_frames"] == 2
    assert payload["tail_reconstruction_mse"] == 0.0
    assert payload["tail_max_abs_error"] == 0.0
    assert (tmp_path / "interface_targets.npz").exists()
    data = np.load(tmp_path / "interface_targets.npz")
    assert data["tail_mask"].tolist() == [0, 0, 1, 1]
    assert data["tail_phase"].tolist() == [-1, -1, 0, 1]
    assert data["family_names"].tolist() == ["structured:coast_steer_+0.7"]


def test_encode_interface_targets_detects_tail_mismatch(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setattr(mod, "RUN_DIR", tmp_path)
    monkeypatch.setattr(mod, "TARGETS_NPZ", tmp_path / "interface_targets.npz")
    actions = np.asarray(
        [
            [0.0, 0.0, 0.0],
            [0.0, -1.0, -1.0],
        ],
        dtype=np.float32,
    )
    demos = [
        {
            "row_id": "r0",
            "obs": np.zeros((2, 72), dtype=np.float32),
            "actions": actions,
        }
    ]
    rows = [
        {
            "row_id": "r0",
            "bc_role": "validation",
            "oracle_by": "structured:full_brake",
            "reveal_step": 1,
        }
    ]

    payload = mod.encode_interface_targets(demos, rows)

    assert payload["tail_frames"] == 1
    assert payload["tail_reconstruction_mse"] > 0.0
    assert payload["tail_max_abs_error"] == 2.0
