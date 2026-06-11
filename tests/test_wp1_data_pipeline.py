"""WP1 data pipeline: determinism, mu-decoupling, prefix fixture, and C3
excitation-gap telemetry (Phase-2 plan WP1.1/WP1.5; stage-1 infrastructure
tests).

Pre-registered acceptance criteria (frozen before implementation):

1. Determinism: the same (cell, mu, seed, variant) episode produces
   bit-identical observation arrays, decision tick, and telemetry on repeated
   runs.
2. mu-decoupling: the behavior schedule drawn for a given episode seed is
   identical across different mu values (behavior parameters never read mu).
3. Familiarization prefix (standard fixture): 5 s = 250 steps; truth-frame
   rear utilization stays sub-limit (< 0.5) during the prefix; the reveal
   never occurs inside the prefix; the prefix vehicle-RLS runs and returns
   kappa estimates near 1 on the nominal vehicle.
4. C3 telemetry: decision time >= 3.5 s after task start; truth excitation
   events confined to t < 1.0 s of the task segment; last-excitation ->
   decision gap > 2.5 s; the c3_telemetry_gate passes on a small batch.

Infrastructure tests only; no capability claim.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
PIPELINE = REPO / "scripts/feasibility_audit/wp1_data_pipeline.py"


def load_module(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def pipe():
    return load_module(PIPELINE, "wp1_data_pipeline")


@pytest.fixture(scope="module")
def mods(pipe):
    return pipe.load_stack()


@pytest.fixture(scope="module")
def cells(pipe, mods):
    return pipe.cells_by_id(mods["wp0"])


def test_episode_determinism(pipe, mods, cells):
    cell = cells["delay5"]
    seed = pipe.episode_seed(0, "train", 0)
    a = pipe.run_episode(mods, cell, 0.7, seed, "standard", "train", False)
    b = pipe.run_episode(mods, cell, 0.7, seed, "standard", "train", False)
    assert np.array_equal(a["frames"], b["frames"])
    assert a["decision_tick"] == b["decision_tick"]
    assert a["last_excitation_step"] == b["last_excitation_step"]
    assert a["behavior_params"] == b["behavior_params"]
    assert a["kappa_b_hat"] == b["kappa_b_hat"]


def test_behavior_schedule_is_mu_decoupled(pipe, mods):
    seed = pipe.episode_seed(0, "train", 3)
    b_low = pipe.BehaviorScript(mods, "standard", seed)
    b_high = pipe.BehaviorScript(mods, "standard", seed)
    assert b_low.params == b_high.params  # schedule depends on seed only
    # and across the full pipeline: two episodes, same seed, different mu
    cell = {"cell_id": "delay5", "degradation": {"delay_steps": 5}}
    a = pipe.run_episode(mods, cell, 0.30, seed, "standard", "train", False)
    b = pipe.run_episode(mods, cell, 1.10, seed, "standard", "train", False)
    assert a["behavior_params"] == b["behavior_params"]


def test_prefix_fixture_and_decision_tick(pipe, mods, cells):
    cell = cells["delay5"]
    rec = pipe.run_episode(mods, cell, 0.55, pipe.episode_seed(0, "train", 7),
                           "standard", "train", False)
    assert pipe.PREFIX_STEPS == 250  # 5 s at dt=0.02 (standard fixture)
    assert rec["decision_tick"] > pipe.PREFIX_STEPS  # reveal never inside the prefix
    assert rec["prefix_max_util"] < 0.5  # sub-limit familiarization (commanded segment,
    # post the policy-independent env initialization transient, accounted separately)
    assert rec["initial_transient_max_util"] >= 0.0
    assert rec["rls_frames"] > 0
    assert abs(rec["kappa_b_hat"] - 1.0) < 0.25  # nominal vehicle, prefix RLS sane
    assert abs(rec["kappa_d_hat"] - 1.0) < 0.25
    assert len(rec["frames"]) == rec["decision_tick"] + 1 + pipe.POST_DECISION_FRAMES
    # the decision frame is the first obstacle-present frame
    assert rec["frames"][rec["decision_tick"]][44] > 0.5
    assert not np.any(rec["frames"][: rec["decision_tick"], 44] > 0.5)


@pytest.mark.parametrize("mu", [0.30, 0.70, 1.10])
def test_c3_gap_telemetry(pipe, mods, cells, mu):
    cell = cells["delay5"]
    rec = pipe.run_episode(mods, cell, mu, pipe.episode_seed(0, "train", 100_000 + int(mu * 10)),
                           "c3", "train", False)
    assert rec["decision_tick"] > 0
    assert rec["decision_time_task_s"] >= pipe.C3_DECISION_MIN_S
    if rec["has_excitation"]:
        # excitation confined to t < 1.0 s of the task segment
        assert rec["last_excitation_step"] * pipe.DT <= pipe.PREFIX_S + pipe.C3_EXCITE_END_S
        assert rec["excitation_to_decision_gap_s"] > pipe.C3_GAP_BAR_S
    gate = pipe.c3_telemetry_gate([rec])
    assert gate["gate_pass"] is True


def test_c3_low_mu_has_excitation_contact(pipe, mods, cells):
    """At low mu the full-brake C3 ramp must actually touch saturation (the
    mu-informative event the variant exists to time-isolate)."""
    cell = cells["delay5"]
    rec = pipe.run_episode(mods, cell, 0.35, pipe.episode_seed(0, "train", 100_999),
                           "c3", "train", False)
    assert rec["has_excitation"]


def test_c3_gate_flags_violation(pipe):
    fake = {
        "variant": "c3", "decision_tick": 400, "seed": 1, "mu": 0.5,
        "decision_time_task_s": 2.0,  # < 3.5 s bar -> must be flagged
        "has_excitation": True,
        "last_excitation_step": 280,
        "excitation_to_decision_gap_s": 2.4,
    }
    gate = pipe.c3_telemetry_gate([fake])
    assert gate["gate_pass"] is False
    assert len(gate["violations"]) == 1
