from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_f1_training_infra_smoke as f1  # noqa: E402


def test_preregistration_freezes_full_scenario_scope_and_disjoint_seeds() -> None:
    prereg = f1.build_preregistration()

    assert prereg["frozen_before_any_f1_infra_run"] is True
    assert prereg["full_scenario_training_target"]["one_driver"] is True
    assert prereg["full_scenario_training_target"]["avoidance_regime"]["teacher"] == "avoidance oracle"
    assert "drift-specialized" in prereg["full_scenario_training_target"]["drift_regime"]["teacher"]

    streams = prereg["seed_streams"]
    avoidance = set(streams["avoidance_smoke"])
    drift = set(streams["drift_smoke"])
    torch_seeds = set(streams["torch_update"])
    assert avoidance.isdisjoint(drift)
    assert avoidance.isdisjoint(torch_seeds)
    assert drift.isdisjoint(torch_seeds)


def test_torch_update_smoke_reports_finite_loss_gradient_and_parameter_delta() -> None:
    rng = np.random.default_rng(3261)
    observations = rng.normal(size=(8, f1.HUMAN_VIEW_OBS_DIM)).astype(np.float32)
    actions = np.tanh(rng.normal(size=(8, f1.ACT_DIM))).astype(np.float32)

    result = f1.torch_update_smoke(observations, actions, device="cpu")

    assert result["loss_finite"] is True
    assert result["finite_gradients"] is True
    assert result["optimizer_changed_parameters"] is True
    assert math.isfinite(result["grad_norm"])
    assert result["parameter_delta_l2"] > 0.0


def test_summarize_passes_full_f1_gates_and_keeps_f2_blocked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prereg = f1.build_preregistration()
    prereg_path = tmp_path / "phase4_f1_training_infra_prereg.json"
    quick_path = tmp_path / "phase4_f1_training_infra_quick.json"
    prereg_path.write_text("{}", encoding="utf-8")
    quick_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(f1, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(f1, "PREREG_JSON", prereg_path)
    monkeypatch.setattr(f1, "QUICK_JSON", quick_path)
    units = f1._smoke_units(prereg, quick=False)
    rows = []
    for worker_index, unit in enumerate(units):
        rows.append(
            {
                "mode": "full",
                "worker_index": worker_index % f1.FULL_WORKERS,
                "unit_index": unit["unit_index"],
                "regime": unit["regime"],
                "scenario_id": unit["scenario"]["scenario_id"],
                "seed": unit["seed"],
                "step_index": 0,
                "obs72_finite_before": True,
                "obs72_finite_after": True,
                "action3_finite": True,
                "action3_bounded": True,
                "terminated": False,
                "truncated": False,
                "status": "running",
                "termination_reason": "",
                "completion_reason": "",
                "backend_variant": f1.VARIANT,
                "backend_model": "Sedan",
                "backend_tire": "TMeasy",
                "action_abs_max": 0.5,
                "obs_sum_before": 1.0,
                "obs_sum_after": 2.0,
                "claim_boundary": f1.CLAIM_BOUNDARY,
            }
        )
    rollout = {
        "rows": rows,
        "observations": np.zeros((len(rows), f1.HUMAN_VIEW_OBS_DIM), dtype=np.float32),
        "actions": np.zeros((len(rows), f1.ACT_DIM), dtype=np.float32),
        "worker_launch_s": 0.1,
        "rollout_elapsed_s": 1.0,
        "worker_count": f1.FULL_WORKERS,
        "unit_count": len(units),
    }
    update = {
        "loss_before": 1.0,
        "loss_after": 0.9,
        "loss_finite": True,
        "finite_gradients": True,
        "grad_norm": 0.2,
        "parameter_delta_l2": 0.1,
        "optimizer_changed_parameters": True,
    }
    devices = {"device_recheck_complete": True, "cuda_available": False}

    summary = f1.summarize(prereg, rollout, update, devices, quick=False, elapsed_s=1.2)

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["decision"]["f1_verdict"] == "f1_training_infrastructure_completed"
    assert summary["decision"]["f2_training_admitted"] is False
    assert summary["decision"]["next_step"] == "STOP_FOR_PI_WALL_CLOCK_REVIEW"
