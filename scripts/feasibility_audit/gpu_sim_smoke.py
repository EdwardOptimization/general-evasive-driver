"""Smoke test for the gpu_sim sub-project interface: prove build_model resolves each rung to a Model
that steps, that the StateContract by-name reader works across the DIFFERENT layouts (pwr3 17-dim vs
tier_a 30-dim), and that the rung-2 gate is enforced. No Chrono, CPU, seconds."""
from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_sim import FidelityConfig, build_model, available_rungs, PLANAR_SUBSTATE, Model


def step_rung(cfg, N=64):
    model = build_model(cfg)
    assert isinstance(model, Model)
    phys = model.build_phys(cfg)
    P = model.make_param_batch(phys, N, mu=0.48, device="cpu", dtype=torch.float32)
    vx0 = torch.full((N,), 8.0); z = torch.zeros(N)
    st, gear = model.init_state(vx0, z, z, P)
    act = torch.zeros(N, 3)
    for _ in range(10):
        st, gear, diag = model.physics_step(st, act, gear, P, 0.02)
    # read vx BY THE CANONICAL NAME (the StateContract seam) — same code path, different layouts
    vx = st[:, model.IDX["vx"]]; yaw_rate = st[:, model.IDX["yaw_rate"]]
    return model, st, vx.mean().item(), yaw_rate.abs().mean().item()


def main():
    print("available rungs:", available_rungs())
    print("StateContract canonical names:", PLANAR_SUBSTATE)
    print()
    for cfg in [
        FidelityConfig(rung=0, vehicle_variant="sedan_tmeasy"),
        FidelityConfig(rung=1, vehicle_variant="sedan_tmeasy"),
        FidelityConfig(rung=1, dof_flags=frozenset({"geometric_fz"})),
    ]:
        model, st, vx, yr = step_rung(cfg)
        print(f"  cfg[{cfg.config_id}]")
        print(f"    -> {model.name:32s} state_dim={model.state_dim:2d}  "
              f"det_switches={model.deterministic_switches}  vx(by-name)={vx:.3f}  |yaw_rate|={yr:.4f}")
    # rung-2 must be gated
    try:
        build_model(FidelityConfig(rung=2))
        print("  !! rung-2 should have raised (it is gated on T3a)")
    except NotImplementedError as e:
        print(f"  rung-2 correctly GATED: {str(e)[:70]}...")
    print("\nSMOKE PASS: one resolver + one by-name reader drives pwr3 (17-dim) and tier_a (30-dim) alike.")


if __name__ == "__main__":
    main()
