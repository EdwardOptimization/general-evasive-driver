"""GPU physics model (physics rewrite) — runs, finite, batched, branchless.

Parity-style smoke tests for ``autodrift.gpu_physics``: the branchless 4-wheel physics
model must step a large batch on the active device, stay finite, keep the gear state in
range, and produce the expected state shape. Mirrors the spirit of test_gpu_surrogate.py
(no python loop over N, fully vectorised)."""
import torch

from autodrift.gpu_physics import (
    PhysParams, make_phys_param_batch, physics_step, init_state, PHYS_STATE_DIM,
)


def _device():
    return "cuda" if torch.cuda.is_available() else "cpu"


def test_physics_step_runs_and_finite():
    torch.set_default_dtype(torch.float32)
    dev = _device()
    n = 1024
    P = make_phys_param_batch(PhysParams(), n, mu=0.48, device=dev, dtype=torch.float32)
    vx0 = torch.full((n,), 9.0, device=dev)
    vy0 = torch.full((n,), 1.5, device=dev)
    yaw0 = torch.full((n,), 0.15, device=dev)
    st, gear = init_state(vx0, vy0, yaw0, P)
    assert st.shape == (n, PHYS_STATE_DIM)
    assert gear.dtype == torch.int64
    assert torch.isfinite(st).all()

    act = torch.zeros(n, 3, device=dev)
    act[:, 0] = -0.3   # steer
    act[:, 1] = 0.2    # throttle (raw in [-1,1])
    act[:, 2] = -0.5   # brake (raw)
    for _ in range(50):
        st, gear, diag = physics_step(st, act, gear, P, 0.02)
    assert torch.isfinite(st).all(), "state went non-finite"
    assert (gear >= 0).all() and (gear <= 5).all(), "gear out of range"
    assert diag["motor_rpm"].shape == (n,)


def test_physics_batched_independence():
    """Batched envs must be independent: running env i alone equals env i inside a big batch."""
    torch.set_default_dtype(torch.float64)
    dev = _device()
    n = 64
    torch.manual_seed(0)
    P = make_phys_param_batch(PhysParams(), n, mu=0.48, device=dev, dtype=torch.float64)
    vx0 = torch.empty(n, device=dev).uniform_(7.0, 10.0)
    vy0 = torch.empty(n, device=dev).uniform_(-2.0, 2.5)
    yaw0 = torch.empty(n, device=dev).uniform_(-0.4, 0.5)
    st, gear = init_state(vx0, vy0, yaw0, P)
    act = torch.empty(n, 3, device=dev).uniform_(-1.0, 1.0)

    full = st.clone(); fg = gear.clone()
    for _ in range(10):
        full, fg, _ = physics_step(full, act, fg, P, 0.02)

    # run env 5 in isolation (batch of 1) and compare
    j = 5
    P1 = make_phys_param_batch(PhysParams(), 1, mu=0.48, device=dev, dtype=torch.float64)
    st1 = st[j:j + 1].clone(); g1 = gear[j:j + 1].clone(); a1 = act[j:j + 1].clone()
    for _ in range(10):
        st1, g1, _ = physics_step(st1, a1, g1, P1, 0.02)
    assert torch.allclose(full[j], st1[0], atol=1e-9), "env not independent of batch"
    assert int(fg[j]) == int(g1[0])


def test_gear_fsm_branchless_shifts():
    """The automatic gearbox is an int tensor updated by masked shifts (no python branch)."""
    torch.set_default_dtype(torch.float32)
    dev = _device()
    n = 256
    P = make_phys_param_batch(PhysParams(), n, mu=0.48, device=dev, dtype=torch.float32)
    # high speed should seed a higher gear than low speed
    st_lo, g_lo = init_state(torch.full((n,), 4.0, device=dev),
                             torch.zeros(n, device=dev), torch.zeros(n, device=dev), P)
    st_hi, g_hi = init_state(torch.full((n,), 12.0, device=dev),
                             torch.zeros(n, device=dev), torch.zeros(n, device=dev), P)
    assert (g_hi >= g_lo).all()
    assert (g_lo >= 0).all() and (g_hi <= 5).all()
