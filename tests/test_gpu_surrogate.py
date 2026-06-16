"""GPU surrogate (Path B) — analytic backbone parity with the numpy single-track model."""
import numpy as np
import torch

from autodrift.dynamics import SingleTrackDriftModel, VehicleState, sample_vehicle_params
from autodrift.gpu_surrogate import make_param_batch, analytic_step, PARAM_KEYS, STATE_DIM


def test_analytic_matches_numpy():
    """The torch batched analytic_step must be bit-faithful to dynamics.SingleTrackDriftModel."""
    torch.set_default_dtype(torch.float64)
    rng = np.random.default_rng(0)
    N, dt = 256, 0.02
    plist = [sample_vehicle_params(rng) for _ in range(N)]
    states, acts, np_next, np_fx_rear = [], [], [], []
    for p in plist:
        m = SingleTrackDriftModel(p)
        st = VehicleState(
            x=rng.normal() * 5, y=rng.normal() * 5, psi=rng.uniform(-3, 3),
            vx=rng.uniform(1, 12), vy=rng.uniform(-3, 3), yaw_rate=rng.uniform(-1.5, 1.5),
            steer=rng.uniform(-0.6, 0.6), drive_force=rng.uniform(-6000, 8000))
        a = rng.uniform(-1, 1, size=3)
        ns, forces = m.step(st, a, dt)
        states.append(st.as_array()); acts.append(a); np_next.append(ns.as_array())
        np_fx_rear.append(forces.fx_rear)
    state = torch.tensor(np.stack(states)); action = torch.tensor(np.stack(acts))
    pdict = {k: torch.tensor(np.array([getattr(p, k) for p in plist])) for k in PARAM_KEYS}
    P = make_param_batch(pdict, N, dtype=torch.float64)
    t_next, forces = analytic_step(state, action, P, dt)
    assert t_next.shape == (N, STATE_DIM)
    assert np.abs(t_next.numpy() - np.stack(np_next)).max() < 1e-8  # fp64 roundoff only
    # rear tyre force (needed for the drift-saturation criterion) is exposed and matches
    assert np.abs(forces["fx_rear"].numpy() - np.array(np_fx_rear)).max() < 1e-8


def test_batched_step_runs_and_is_finite():
    torch.set_default_dtype(torch.float32)
    from autodrift.dynamics import VehicleParams
    N = 1024
    P = make_param_batch(VehicleParams(), N, dtype=torch.float32)
    s = torch.zeros(N, STATE_DIM); s[:, 3] = 8.0
    a = torch.zeros(N, 3)
    for _ in range(50):
        s, f = analytic_step(s, a, P, 0.02)
    assert torch.isfinite(s).all() and s.shape == (N, STATE_DIM)
