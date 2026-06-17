"""gpu_sim — multi-fidelity GPU vehicle simulator sub-project.

Public interface (everything a consumer needs; concrete physics stays behind the resolver):

    from autodrift.gpu_sim import (
        FidelityConfig, FidelityCertificate, Model, build_model, available_rungs, PLANAR_SUBSTATE,
    )

Design spec: docs/multi-fidelity-gpu-rewrite-design-2026-06.md.
Software design + interface contracts: src/autodrift/gpu_sim/README.md and contracts.py.
"""
from .contracts import (  # noqa: F401
    FidelityConfig, FidelityCertificate, Model, PLANAR_SUBSTATE, validate_state_contract,
)
from .resolver import build_model, available_rungs  # noqa: F401

__all__ = [
    "FidelityConfig", "FidelityCertificate", "Model", "PLANAR_SUBSTATE",
    "validate_state_contract", "build_model", "available_rungs",
]
