"""Smoke: build_env(rung=0) produces a working batched env through the gpu_sim interface — resets from a
real drift scenario, steps the injected pwr3 (gear-seed) model, returns obs72/reward. Proves the training
bridge for the pretrain rung."""
from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from test_gpu_env_physics import _drift_env, _scenario_from_env  # noqa: E402  (reuse the test scenario)

from autodrift.gpu_sim import FidelityConfig  # noqa: E402
from autodrift.gpu_sim.env import build_env  # noqa: E402


def main():
    cpu_env = _drift_env(); cpu_env.reset(seed=1)
    sc = _scenario_from_env(cpu_env, "drift")
    gpu = build_env(FidelityConfig(rung=0, vehicle_variant="sedan_tmeasy"), device="cpu")
    N = 8
    obs = gpu.reset([sc for _ in range(N)])
    print("model injected   :", gpu._model.name, " state-by-name vx col:", gpu._idx["vx"])
    print("reset obs72 shape:", tuple(obs.shape))
    act = torch.zeros(N, 3)
    for _ in range(10):
        obs, rew, term, trunc, info = gpu.step(act)
    print("after 10 steps   : obs", tuple(obs.shape), " reward mean %.4f" % float(rew.mean()),
          " term", int(term.sum().item()))
    assert obs.shape == (N, 72)
    print("\nBUILD_ENV PASS: rung-0 framework env (pwr3 gear-seed injected) resets+steps+obs72 — the")
    print("pretrain training bridge works through build_model->build_env, state read by name.")


if __name__ == "__main__":
    main()
