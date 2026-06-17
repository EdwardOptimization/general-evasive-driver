"""env — build a batched PPO environment on a fidelity config (design §5.3).

    build_env(cfg) -> GPUPhysicsAutoDriftEnv   (then env.reset(scenarios); env.step(action))

The env steps the rung's Model (injected step/init/IDX) and builds obs72 BY NAME (StateContract), so the
SAME env runs any rung. Wired for rung-0 (pwr3): its PhysParams construction matches the live env's
scenario->params mapping. rung-1+ needs that mapping generalized off PhysParams (the obs72/step/init/idx
seam is already rung-agnostic — see README build status).
"""
from __future__ import annotations

from .contracts import FidelityConfig


def build_env(cfg: FidelityConfig, *, device: str = "cuda", **env_kw):
    from ..gpu_env_physics import GPUPhysicsAutoDriftEnv
    from .resolver import build_model
    if cfg.rung != 0:
        raise NotImplementedError(
            f"build_env: rung {cfg.rung} not wired — the live env's scenario->PhysParams construction is "
            f"PhysParams-coupled; rung-1+ needs that mapping generalized. rung-0 (pretrain) works now."
        )
    model = build_model(cfg)
    return GPUPhysicsAutoDriftEnv(device=device, sigma_scale=cfg.sigma_scale, model=model, **env_kw)
