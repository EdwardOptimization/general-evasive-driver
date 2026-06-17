"""env — build a batched PPO environment on a fidelity config (design §5.3).

INTERFACE (to be implemented in T0):
    build_env(cfg: FidelityConfig, n_envs: int, *, device="cuda") -> GpuEnv

Wraps resolver.build_model(cfg) with the obs72 reader, reward, termination and obstacle logic from
gpu_env_physics.py — BUT refactored to read state BY NAME via model.IDX (the StateContract), so the
SAME env code runs any rung. The obs72-by-name refactor of gpu_env_physics.obs72_from_state (the ~6
hard-coded state[:,0..6] sites) is the load-bearing T0 task this depends on.
"""
from __future__ import annotations

from .contracts import FidelityConfig


def build_env(cfg: FidelityConfig, n_envs: int, *, device: str = "cuda"):
    raise NotImplementedError(
        "build_env(): T0 — refactor gpu_env_physics.obs72_from_state + reward/termination readers to "
        "IDX[name] indexing (PLANAR_SUBSTATE), then wrap build_model(cfg). See README build status."
    )
