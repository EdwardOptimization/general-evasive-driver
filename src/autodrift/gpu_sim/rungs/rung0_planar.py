"""Rung 0 — PLANAR single-track (wraps gpu_physics_pwr3). The fast/coarse PRETRAIN rung.
17-state explicit ODE, branchless gear FSM, exact TMeasy tyre, sigma slip-relaxation, FWD traction
cap + gear-SEED fix. Satisfies the StateContract directly (its IDX has all 9 canonical names)."""
from __future__ import annotations

from . import ModuleModel
from ...gpu_physics_pwr3 import (  # noqa: E402
    PhysParams, make_phys_param_batch, physics_step, init_state, IDX, PHYS_STATE_DIM,
)


def make(cfg) -> ModuleModel:
    return ModuleModel(
        name="rung0_planar_pwr3",
        idx=IDX,
        state_dim=PHYS_STATE_DIM,
        deterministic_switches=False,   # gear dead-band lands in T0; certificate emission blocked til then
        param_cls=PhysParams,
        make_batch=make_phys_param_batch,
        init_fn=init_state,
        step_fn=physics_step,
    )
