from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_f1b_throughput_optimization as f1b  # noqa: E402


def _fake_row(*, protocol: str, regime: str, worker_index: int, seed: int) -> dict:
    return {
        "mode": "full",
        "protocol": protocol,
        "worker_index": worker_index,
        "unit_index": worker_index,
        "regime": regime,
        "scenario_id": f"{regime}-{seed}",
        "seed": seed,
        "step_index": 0,
        "batch_index": 0,
        "batch_horizon": 1 if protocol == "closed_loop_step" else 4,
        "obs72_finite_before": True,
        "obs72_finite_after": True,
        "action3_finite": True,
        "action3_bounded": True,
        "terminated": False,
        "truncated": False,
        "status": "running",
        "termination_reason": "",
        "completion_reason": "",
        "backend_variant": f1b.VARIANT,
        "backend_model": "Sedan",
        "backend_tire": "TMeasy",
        "action_abs_max": 0.5,
        "obs_sum_before": 1.0,
        "obs_sum_after": 2.0,
        "claim_boundary": f1b.CLAIM_BOUNDARY,
    }


def test_preregistration_keeps_f2_blocked_and_records_1000_step_target() -> None:
    prereg = f1b.build_preregistration()

    assert prereg["frozen_before_any_f1b_run"] is True
    assert prereg["throughput_target"]["target_aggregate_steps_per_s"] == 1000.0
    assert prereg["optimization_axes"]["ipc_amortization"]["closed_loop_baseline_retained"] is True
    assert "F1b does not launch F2" in prereg["claim_boundary"]
    assert prereg["acceptance"]["stop_rule"].startswith("after F1b")


def test_chrono_worker_client_step_many_decodes_worker_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(ChronoWorkerClient)

    def fake_send(message: dict) -> dict:
        assert message["cmd"] == "step_many"
        np.testing.assert_allclose(message["actions"], [[0.1, 0.2, 0.3], [0.0, 0.0, 0.0]])
        return {
            "steps": [
                {
                    "obs": [1.0] * f1b.HUMAN_VIEW_OBS_DIM,
                    "terminated": False,
                    "truncated": False,
                    "status": "running",
                    "info": {"termination_reason": ""},
                },
                {
                    "obs": [2.0] * f1b.HUMAN_VIEW_OBS_DIM,
                    "terminated": True,
                    "truncated": False,
                    "status": "terminated",
                    "info": {"termination_reason": "off_track"},
                },
            ],
            "stopped_early": True,
        }

    monkeypatch.setattr(client, "_send", fake_send)

    steps, stopped_early = client.step_many(np.asarray([[0.1, 0.2, 0.3], [0.0, 0.0, 0.0]], dtype=np.float32))

    assert stopped_early is True
    assert len(steps) == 2
    assert steps[0][0].shape == (f1b.HUMAN_VIEW_OBS_DIM,)
    assert steps[1][1] is True
    assert steps[1][4]["termination_reason"] == "off_track"


def test_summarize_reports_target_miss_without_admitting_f2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prereg = {
        "dependencies": {"f1_aggregate_steps_per_s": 2.0},
        "seed_streams": {},
    }
    prereg_path = tmp_path / "phase4_f1b_throughput_prereg.json"
    quick_path = tmp_path / "phase4_f1b_throughput_quick.json"
    prereg_path.write_text("{}", encoding="utf-8")
    quick_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(f1b, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(f1b, "PREREG_JSON", prereg_path)
    monkeypatch.setattr(f1b, "QUICK_JSON", quick_path)
    monkeypatch.setattr(f1b, "_default_full_workers", lambda: 2)

    closed_rows = [
        _fake_row(protocol="closed_loop_step", regime="avoidance_clean_reveal_9p5", worker_index=0, seed=1),
        _fake_row(protocol="closed_loop_step", regime="drift_low_mu_power_oversteer", worker_index=1, seed=2),
    ]
    batched_rows = [
        _fake_row(protocol="batched_action_sequence", regime="avoidance_clean_reveal_9p5", worker_index=0, seed=3),
        _fake_row(protocol="batched_action_sequence", regime="drift_low_mu_power_oversteer", worker_index=1, seed=4),
    ]
    closed_loop = {
        "rows": closed_rows,
        "aggregate_steps_per_s": 20.0,
        "projected_100m_wall_clock_hours": 1388.9,
    }
    batched = {
        "rows": batched_rows,
        "aggregate_steps_per_s": 120.0,
        "projected_100m_wall_clock_hours": 231.5,
    }
    determinism = {"passed": True}

    summary = f1b.summarize(
        prereg,
        closed_loop,
        batched,
        determinism,
        quick=False,
        elapsed_s=1.0,
        worker_count=2,
        steps_per_unit=2,
        batch_horizon=4,
    )

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["protocol_gates"]["target_1000_steps_per_s_met"] is False
    assert summary["decision"]["f1b_verdict"] == "f1b_throughput_target_missed_reported"
    assert summary["decision"]["f2_training_admitted"] is False
