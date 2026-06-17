"""Rung adapters: wrap the existing flat physics modules (pwr3 / tier_a style — module-level
init_state / physics_step / make_*_param_batch / IDX + a *Params dataclass) behind the Model
protocol from gpu_sim.contracts, threading a FidelityConfig into the right *Params dataclass.

A rung may carry extra DOFs in any layout; `idx_aliases` maps the canonical StateContract names onto
the rung's own names (e.g. tier_a stores the yaw angle as `yaw` and the yaw rate as `wz`), so the
single by-name obs72/reward/certificate readers work across rungs (design §3.4)."""
from __future__ import annotations

from dataclasses import fields

from ..contracts import FidelityConfig, validate_state_contract


class ModuleModel:
    """Adapts a flat physics module to the Model protocol. Holds no state beyond the function refs."""

    def __init__(self, *, name, idx, state_dim, deterministic_switches, param_cls,
                 make_batch, init_fn, step_fn, idx_aliases=None):
        eff_idx = dict(idx)
        for canon, actual in (idx_aliases or {}).items():
            if actual in idx and canon not in eff_idx:
                eff_idx[canon] = idx[actual]
        validate_state_contract(eff_idx, name)        # raises if a canonical name is still missing
        self.name = name
        self.IDX = eff_idx
        self.state_dim = int(state_dim)
        self.deterministic_switches = bool(deterministic_switches)
        self._param_cls = param_cls
        self._make_batch = make_batch
        self._init = init_fn
        self._step = step_fn

    def build_phys(self, cfg: FidelityConfig):
        """Construct the rung's *Params dataclass from the config (sigma_scale + param_overrides)."""
        valid = {f.name for f in fields(self._param_cls)}
        kw = {}
        if "sigma_scale" in valid:
            kw["sigma_scale"] = cfg.sigma_scale
        for k, v in cfg.param_overrides:
            if k in valid:
                kw[k] = v
        return self._param_cls(**kw)

    def make_param_batch(self, phys, n, mu, device, dtype):
        return self._make_batch(phys, n, mu=mu, device=device, dtype=dtype)

    def init_state(self, vx0, vy0, yaw0, P):
        return self._init(vx0, vy0, yaw0, P)

    def physics_step(self, state, action, gear, P, dt):
        return self._step(state, action, gear, P, dt)
