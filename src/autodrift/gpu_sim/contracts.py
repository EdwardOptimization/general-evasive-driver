"""gpu_sim — interface contracts for the multi-fidelity GPU vehicle simulator.

This module is the SOFTWARE-DESIGN HEART of the GPU-rewrite sub-project: it defines the interfaces
every fidelity rung, the resolver, the env, and the certificate harness agree on. Concrete physics
lives in `rungs/`; this file is pure contract (no Chrono, no heavy torch ops) so it can be imported
cheaply and tested in isolation.

Design spec: docs/multi-fidelity-gpu-rewrite-design-2026-06.md (§3.4 config schema, §5.1 certificate).

THE THREE CONTRACTS
  1. StateContract  — the canonical planar sub-state names every rung MUST expose by NAME (so a single
                      obs72 reader works across rungs whose full state layouts differ).
  2. Model          — the runtime stepping interface (init_state / physics_step / IDX / state_dim).
                      pwr3 (17-dim) and tier_a (30-dim) already satisfy the CALL signature; the
                      adapters in `rungs/` make them satisfy this typed contract + the StateContract.
  3. FidelityConfig — the (vehicle x rung x knobs) selector; `resolver.build_model(cfg)` maps it to a
                      Model, and `certify.certify(cfg)` attaches a measured FidelityCertificate.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Protocol, runtime_checkable

import torch

# --------------------------------------------------------------------------------------------------
# 1. StateContract — the canonical planar sub-state every rung exposes BY NAME.
# --------------------------------------------------------------------------------------------------
# The obs72 reader, reward, termination and the certificate gates address state ONLY through these
# names (never raw integer columns), so a rung may carry any extra DOFs (roll/pitch/corner-travel/...)
# in any layout as long as it maps these 9 names in its IDX. This is the seam that makes the rungs a
# coherent ladder rather than three incompatible models (design §3.4 — the obs72-by-name invariant).
PLANAR_SUBSTATE: tuple[str, ...] = (
    "x", "y", "psi", "vx", "vy", "yaw_rate", "steer", "throttle", "brake",
)


def validate_state_contract(idx: dict, model_name: str) -> None:
    """Raise if a rung's IDX is missing any canonical planar sub-state name."""
    missing = [k for k in PLANAR_SUBSTATE if k not in idx]
    if missing:
        raise ValueError(
            f"{model_name}: IDX violates StateContract, missing {missing}. Every rung must expose the "
            f"canonical planar sub-state {PLANAR_SUBSTATE} by name (design §3.4)."
        )


# --------------------------------------------------------------------------------------------------
# 2. Model — the runtime stepping interface every fidelity rung implements.
# --------------------------------------------------------------------------------------------------
@runtime_checkable
class Model(Protocol):
    """A batched, branchless GPU vehicle model at one fidelity rung.

    The call contract (already shared verbatim by gpu_physics_pwr3 and gpu_vehicle_tier_a):
        init_state(vx0, vy0, yaw0, P) -> (state[N, state_dim], gear[N] int64)
        physics_step(state, action[N,3], gear, P, dt) -> (next_state, next_gear, diag: dict)
    plus introspection: `state_dim`, `IDX` (name->col, must satisfy the StateContract), and
    `make_param_batch(phys, N, mu, device, dtype) -> P` to build the per-env param batch.
    `deterministic_switches` reports whether discrete switches (gear FSM) are round-off-robust under
    op-reorder (design §2.6); the certificate refuses to certify a rung with it False (gate emission
    is blocked until the gear dead-band lands).
    """

    name: str
    state_dim: int
    IDX: dict
    deterministic_switches: bool

    def make_param_batch(self, phys, n: int, mu, device, dtype):  # -> ParamBatch
        ...

    def init_state(self, vx0: torch.Tensor, vy0: torch.Tensor, yaw0: torch.Tensor, P):
        ...  # -> (state, gear)

    def physics_step(self, state: torch.Tensor, action: torch.Tensor, gear: torch.Tensor, P, dt: float):
        ...  # -> (next_state, next_gear, diag)


# --------------------------------------------------------------------------------------------------
# 3a. FidelityConfig — the (vehicle x rung x knobs) selector (design §3.4).
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class FidelityConfig:
    # --- axis 1: vehicle (reuses the Chrono variant registry; cross-vehicle) ---
    vehicle_variant: str = "sedan_tmeasy"          # -> CHRONO_VEHICLE_VARIANTS key
    param_overrides: tuple = ()                     # tuple of (key, value) — frozen/hashable
    # --- axis 2: fidelity rung (which GPU module / DISTINCT layout) ---
    rung: int = 0                                   # 0=planar pwr3, 1=kinematic tier_a, 2=full-DAE
    # --- axis 3: numerical knobs (order within the rung) ---
    substeps: int = 4
    tyre_transient: str = "relax"                   # {algebraic, relax}
    sigma_scale: float = 0.165
    n_iter: int = 0                                 # rung-2 constraint sweeps (the fidelity dial)
    dof_flags: frozenset = frozenset()              # {driveline_inertia, front_slip, four_wheel_brake, geometric_fz}

    @property
    def config_id(self) -> str:
        ov = ",".join(f"{k}={v}" for k, v in self.param_overrides)
        fl = "+".join(sorted(self.dof_flags))
        return (f"r{self.rung}|{self.vehicle_variant}|ss{self.substeps}|{self.tyre_transient}"
                f"|sig{self.sigma_scale}|it{self.n_iter}|{fl}|{ov}")

    def with_overrides(self, **kw) -> "FidelityConfig":
        return replace(self, **kw)


# --------------------------------------------------------------------------------------------------
# 3b. FidelityCertificate — the MEASURED accuracy-vs-Chrono a config earns (design §5.1).
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class FidelityCertificate:
    """Filled by certify.certify(cfg), NEVER by the model author. The arbiter for pretrain/posttrain
    config selection is this measured certificate — NEVER DOF count (the dig showed higher order does
    not monotonically help: tier_a regressed drift 0.028->0.076)."""
    config_id: str
    # accuracy vs frozen Chrono (lower is better; None = not yet measured)
    drift_beta24_p90: float | None = None       # gate <= 0.03
    drift_beta24_truevx_p90: float | None = None  # the HONEST check (true Chrono vx)
    avoid_vx_rmse: float | None = None          # floor ~0.235
    collision_bal_acc: float | None = None      # higher better, target >= 0.75
    # speed
    throughput_st_per_s: float | None = None    # measured env-steps/s at the bench batch
    bench_batch: int | None = None
    # provenance / validity
    deterministic_switches: bool = False        # gate emission requires True
    agrees_with_rung_below: bool | None = None  # the agree-within-tolerance ladder check
    notes: str = ""

    @property
    def drift_passes(self) -> bool:
        v = self.drift_beta24_truevx_p90 if self.drift_beta24_truevx_p90 is not None else self.drift_beta24_p90
        return v is not None and v <= 0.03

    def dominates(self, other: "FidelityCertificate") -> bool:
        """True if self is at least as accurate on EVERY measured axis and strictly better on one —
        the only basis on which a higher rung may be chosen for posttrain (design §5.2)."""
        axes = ("drift_beta24_truevx_p90", "avoid_vx_rmse")
        better = False
        for a in axes:
            s, o = getattr(self, a), getattr(other, a)
            if s is None or o is None:
                return False
            if s > o + 1e-6:
                return False
            if s < o - 1e-6:
                better = True
        # collision higher-is-better
        if self.collision_bal_acc is not None and other.collision_bal_acc is not None:
            if self.collision_bal_acc < other.collision_bal_acc - 1e-6:
                return False
            if self.collision_bal_acc > other.collision_bal_acc + 1e-6:
                better = True
        return better
