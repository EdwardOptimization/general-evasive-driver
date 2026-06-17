"""Rung 1 — KINEMATIC suspension (wraps gpu_vehicle_tier_a): chassis 6-DOF + 4 kinematic corners.
30-state. Carries the StateContract names via aliases (it stores the yaw ANGLE as `yaw` and the yaw
RATE as `wz`). Currently a RED-certificate rung (drift regressed 0.028->0.076); kept so the framework
can BLOCK a config that looks like an upgrade but regresses drift (design §6 T1).

`geometric_fz` dof_flag swaps in gpu_vehicle_tier_a_geom (the T3a instantaneous-geometric-transfer
variant) for the falsification experiment."""
from __future__ import annotations

from . import ModuleModel

_ALIASES = {"psi": "yaw", "yaw_rate": "wz"}   # canonical StateContract name -> tier_a's own name


def make(cfg) -> ModuleModel:
    if "geometric_fz" in cfg.dof_flags:
        from ...gpu_vehicle_tier_a_geom import (  # noqa: E402
            TierAParams as TP, make_tier_a_param_batch as mb, physics_step as ps,
            init_state as ini, IDX as ix, TIER_A_STATE_DIM as dim)
        name = "rung1_kinematic_tier_a_GEOM"
    else:
        from ...gpu_vehicle_tier_a import (  # noqa: E402
            TierAParams as TP, make_tier_a_param_batch as mb, physics_step as ps,
            init_state as ini, IDX as ix, TIER_A_STATE_DIM as dim)
        name = "rung1_kinematic_tier_a"
    return ModuleModel(
        name=name, idx=ix, state_dim=dim,
        deterministic_switches=False,
        param_cls=TP, make_batch=mb, init_fn=ini, step_fn=ps,
        idx_aliases=_ALIASES,
    )
