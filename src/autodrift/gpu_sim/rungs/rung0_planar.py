"""Rung 0 — PLANAR single-track. 17-state explicit ODE, branchless gear FSM, exact TMeasy tyre, sigma
slip-relaxation, FWD traction cap + gear-SEED fix. Satisfies the StateContract directly (its IDX has all
9 canonical names). dof_flag "t2_longitudinal" -> the pwrBD config (measured engine-scale B + clean front
brake D), which closes 53% of the avoid gap (0.520->0.369) while holding drift — strictly more faithful, so
it is the recommended carried/posttrain config; plain pwr3 is the bare pretrain rung."""
from __future__ import annotations

from . import ModuleModel


def make(cfg) -> ModuleModel:
    if "t2_longitudinal" in cfg.dof_flags:
        from ...gpu_physics_pwrBD import (  # noqa: E402  engine-scale + clean brake (T2 DELIVERED)
            PhysParams, make_phys_param_batch, physics_step, init_state, IDX, PHYS_STATE_DIM)
        name = "rung0_planar_pwrBD"
    else:
        from ...gpu_physics_pwr3 import (  # noqa: E402  the bare gear-seed pretrain model
            PhysParams, make_phys_param_batch, physics_step, init_state, IDX, PHYS_STATE_DIM)
        name = "rung0_planar_pwr3"
    return ModuleModel(
        name=name, idx=IDX, state_dim=PHYS_STATE_DIM,
        deterministic_switches=False,   # gear dead-band lands in T0; certify runs eager (deterministic)
        param_cls=PhysParams, make_batch=make_phys_param_batch, init_fn=init_state, step_fn=physics_step,
    )
