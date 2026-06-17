"""resolver — the single entry point that maps a FidelityConfig to a runtime Model.

    from autodrift.gpu_sim import FidelityConfig, build_model
    model = build_model(FidelityConfig(rung=0, vehicle_variant="sedan_tmeasy"))
    P = model.make_param_batch(model.build_phys(cfg), N, mu=0.48, device="cuda", dtype=torch.float32)
    st, gear = model.init_state(vx0, vy0, yaw0, P)
    st, gear, diag = model.physics_step(st, action, gear, P, dt)

This is the seam the env (build_env), the training loop, and certify.certify all go through, so adding
a vehicle or a rung never touches the consumers — only the registry below (design §3.4)."""
from __future__ import annotations

from .contracts import FidelityConfig, Model
from .rungs import rung0_planar, rung1_kinematic

# rung index -> maker(cfg) -> Model. Rung 2 (full-DAE) is intentionally absent: it is GATED on the
# T3a falsification (scripts/feasibility_audit/gpu_tier_a_geom_gate.py) and built only on GO.
_RUNG_MAKERS = {
    0: rung0_planar.make,
    1: rung1_kinematic.make,
}


def build_model(cfg: FidelityConfig) -> Model:
    maker = _RUNG_MAKERS.get(cfg.rung)
    if maker is None:
        raise NotImplementedError(
            f"rung {cfg.rung} is not built. rung-2 (full-linkage DAE) is GATED on the T3a falsification "
            f"test (design §6 T3a). Available rungs: {sorted(_RUNG_MAKERS)}."
        )
    model = maker(cfg)
    assert isinstance(model, Model), f"{model} does not satisfy the Model protocol"
    return model


def available_rungs() -> list[int]:
    return sorted(_RUNG_MAKERS)
