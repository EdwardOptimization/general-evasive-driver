"""certify — measure a config's FidelityCertificate against frozen Chrono (design §5.1).

INTERFACE (to be implemented in T0 by generalizing the 3 existing gates — gpu_pwr3_gate /
gpu_tier_a_gate / the avoid+collision gate — into one config-driven harness):

    certify(cfg: FidelityConfig, *, device="cuda") -> FidelityCertificate

It builds the model via resolver.build_model(cfg), replays the frozen Chrono rollouts
(surrogate_drift_data.npz held-out split + surrogate_avoid_labels.npz + the collision grid) through
it, and fills the certificate's measured axes (drift_beta24_p90 + true-vx, avoid_vx_rmse,
collision_bal_acc, throughput). Gate emission is BLOCKED while model.deterministic_switches is False
(the gear dead-band must land first). The certificate — never DOF count — is the arbiter.
"""
from __future__ import annotations

from .contracts import FidelityConfig, FidelityCertificate
from .resolver import build_model


def certify(cfg: FidelityConfig, *, device: str = "cuda") -> FidelityCertificate:
    model = build_model(cfg)  # validates the config resolves
    if not model.deterministic_switches:
        # honest guard: refuse to emit a trustworthy certificate until discrete switches are robust
        raise NotImplementedError(
            "certify(): blocked — model.deterministic_switches is False (gear dead-band not yet landed, "
            "T0). Implement the gear dead-band + the gate harness, then emit the certificate. "
            "Until then use the standalone gates in scripts/feasibility_audit/."
        )
    raise NotImplementedError("certify(): T0 — generalize gpu_pwr3_gate/gpu_tier_a_gate into this harness.")
