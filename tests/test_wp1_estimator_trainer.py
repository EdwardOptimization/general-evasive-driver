"""WP1 estimator trainer: capacity-matching rule and incremental-injector
consistency (Phase-2 plan WP1.2; stage-1 infrastructure tests).

Pre-registered acceptance criteria (frozen before implementation):

1. Non-input-projection parameter counts of all 5 arms match within 10%
   (input projections Linear(72->h).weight / GRU weight_ih_l0 excluded;
   window arms share one per-frame encoder so the count is window-invariant).
2. The BeliefInjector's incremental GRU update produces the same estimate as
   the batch forward over the same frames (the injection-time estimator is
   exactly the trained estimator).
3. Window/L0 injector estimates equal the batch forward on the same frames.
4. One training step runs end to end on a synthetic dataset for every arm
   (shape contract with the data pipeline's npz layout).

Infrastructure tests only; no capability claim.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

REPO = Path(__file__).resolve().parents[1]
TRAINER = REPO / "scripts/feasibility_audit/wp1_estimator_trainer.py"


def load_module(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tr():
    return load_module(TRAINER, "wp1_estimator_trainer")


def test_capacity_matching_rule(tr):
    report = {arm: tr.param_counts(tr.build_arm(arm)) for arm in tr.ARMS}
    spread = tr.assert_capacity_matched(report)
    assert spread <= tr.CAPACITY_TOLERANCE
    # window arms: identical counts regardless of window length (shared encoder)
    w25 = report["L2_window_25"]["non_input_projection"]
    assert report["L2_window_50"]["non_input_projection"] == w25
    assert report["L2_window_100"]["non_input_projection"] == w25
    # the rule excludes exactly the input projections
    l0 = report["L0_frame"]
    assert l0["input_projection"] == 72 * tr.H_FRAME
    gru = report["L3_GRU"]
    assert gru["input_projection"] == 3 * tr.H_GRU * 72


def test_gru_injector_incremental_matches_batch(tr):
    torch.manual_seed(0)
    model = tr.build_arm("L3_GRU").eval()
    rng = np.random.default_rng(1)
    frames = rng.normal(0, 0.3, (40, tr.OBS_DIM)).astype(np.float32)
    inj = tr.BeliefInjector(model, "L3_GRU")
    for f in frames:
        inj.observe(f)
    est_inc = inj.estimate()
    with torch.no_grad():
        est_batch = float(model(torch.tensor(frames).unsqueeze(0),
                                torch.tensor([len(frames)])))
    assert est_inc == pytest.approx(est_batch, abs=1e-5)


@pytest.mark.parametrize("arm", ["L0_frame", "L2_window_25"])
def test_frame_window_injector_matches_batch(tr, arm):
    torch.manual_seed(0)
    model = tr.build_arm(arm).eval()
    rng = np.random.default_rng(2)
    frames = rng.normal(0, 0.3, (60, tr.OBS_DIM)).astype(np.float32)
    inj = tr.BeliefInjector(model, arm)
    for f in frames:
        inj.observe(f)
    est = inj.estimate()
    with torch.no_grad():
        if arm == "L0_frame":
            ref = float(model(torch.tensor(frames[-1]).view(1, -1)))
        else:
            ref = float(model(torch.tensor(frames[-25:]).unsqueeze(0)))
    assert est == pytest.approx(ref, abs=1e-5)


def _synthetic_dataset(n: int = 24, t: int = 60) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(3)
    mu = rng.uniform(0.25, 1.15, n).astype(np.float32)
    obs = rng.normal(0, 0.2, (n, t, 72)).astype(np.float32)
    obs[:, :, 3] += mu[:, None] * 0.1  # weak signal so the loss can move
    return {
        "obs": obs,
        "length": np.full(n, t, dtype=np.int32),
        "decision_tick": np.full(n, t - 2, dtype=np.int32),
        "mu": mu,
        "role": np.array([0] * (n - 8) + [1] * 4 + [2] * 4, dtype=np.int8),
        "variant": np.zeros(n, dtype=np.int8),
        "mu_on_grid": np.zeros(n, dtype=bool),
    }


@pytest.mark.parametrize("arm", ["L0_frame", "L2_window_25", "L3_GRU"])
def test_train_arm_runs_on_synthetic_data(tr, arm):
    data = _synthetic_dataset()
    res, model = tr.train_arm(arm, data, train_seed=0, lr_grid=(1e-3,),
                              max_epochs=2, eval_every=1, batch_size=8)
    assert res["arm"] == arm
    assert np.isfinite(res["val"]["mae"])
    assert res["n_train"] == 16 and res["n_sel"] == 4 and res["n_val"] == 4
    if arm == "L3_GRU":
        assert "val_reset_control" in res
