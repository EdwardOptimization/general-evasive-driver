"""Smoke tests for the Tier-a chassis-6DOF + 4-corner GPU vehicle model.

Checks: it runs batched, stays finite, is shape-correct, and the NEW chassis degrees of freedom
respond physically -- roll responds to lateral acceleration and pitch responds to longitudinal
acceleration (the load-transfer machinery the planar model omitted). No Chrono fidelity is asserted
here (that is the gate's job, scripts/feasibility_audit/gpu_tier_a_gate.py); this only guards that
the model is wired up and integrable.
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autodrift.gpu_vehicle_tier_a import (  # noqa: E402
    TierAParams, CornerSpec, make_tier_a_param_batch, physics_step, init_state,
    TIER_A_STATE_DIM, IDX,
)

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def _batch(n, mu=0.8, **kw):
    P = make_tier_a_param_batch(TierAParams(**kw), n, mu=mu, device=DEV, dtype=torch.float32)
    return P


def test_runs_batched_and_finite():
    """N>=1000 envs, straight-line cruise: state stays finite and shape-correct over many steps."""
    n = 1500
    P = _batch(n)
    vx0 = torch.full((n,), 8.0, device=DEV)
    z0 = torch.zeros(n, device=DEV)
    st, gear = init_state(vx0, z0, z0, P)
    assert st.shape == (n, TIER_A_STATE_DIM)
    assert gear.shape == (n,) and gear.dtype == torch.int64
    assert torch.isfinite(st).all()
    act = torch.zeros(n, 3, device=DEV)
    act[:, 1] = 0.3                              # mild throttle
    for _ in range(60):
        st, gear, diag = physics_step(st, act, gear, P, 0.02)
    assert torch.isfinite(st).all(), "state went non-finite during cruise"
    assert torch.isfinite(diag["fz"]).all()
    # per-corner loads are positive and sum to roughly the vehicle weight (+/- transfer).
    assert (diag["fz"] > 0).all()
    total = diag["fz"].sum(dim=1)
    weight = float(P["mass"][0] * P["gravity"][0])
    assert (total > 0.7 * weight).all() and (total < 1.4 * weight).all()


def test_differentiable_single_step():
    """One step is autograd-differentiable w.r.t. the action (the model is differentiable)."""
    n = 16
    P = _batch(n)
    vx0 = torch.full((n,), 8.0, device=DEV)
    z0 = torch.zeros(n, device=DEV)
    st, gear = init_state(vx0, z0, z0, P)
    act = torch.zeros(n, 3, device=DEV, requires_grad=True)
    out, _, _ = physics_step(st, act, gear, P, 0.02)
    loss = out[:, IDX["vy"]].pow(2).sum() + out[:, IDX["wz"]].pow(2).sum()
    loss.backward()
    assert act.grad is not None and torch.isfinite(act.grad).all()


def test_roll_responds_to_lateral_accel():
    """A steering step generates lateral acceleration -> the chassis MUST roll (sign-consistent),
    and the per-corner vertical load transfers laterally (outer wheels load, inner unload)."""
    n = 64
    P = _batch(n, mu=0.9)
    vx0 = torch.full((n,), 10.0, device=DEV)
    z0 = torch.zeros(n, device=DEV)
    st, gear = init_state(vx0, z0, z0, P)
    act = torch.zeros(n, 3, device=DEV)
    act[:, 0] = 0.6                              # steer
    act[:, 1] = 0.2
    diag = None
    for _ in range(60):
        st, gear, diag = physics_step(st, act, gear, P, 0.02)
    roll = st[:, IDX["roll"]]
    ay = diag["ay_body"]
    assert torch.isfinite(roll).all()
    # non-trivial roll developed (the chassis is not rigid-flat as the planar model was).
    assert roll.abs().mean() > 1e-3, "roll did not respond to the cornering lateral accel"
    # roll sign tracks the lateral-accel sign (consistent body convention; all envs share sign).
    assert torch.sign(roll.mean()) == torch.sign(ay.mean())
    # lateral load transfer: the two left corners vs the two right corners differ (transfer occurred).
    fz = diag["fz"]                              # [n,4] FL,FR,RL,RR
    left = fz[:, 0] + fz[:, 2]
    right = fz[:, 1] + fz[:, 3]
    assert (left - right).abs().mean() > 100.0, "no lateral per-corner load transfer"


def test_pitch_responds_to_longitudinal_accel():
    """Hard braking -> longitudinal deceleration -> the chassis MUST pitch and the load transfers
    longitudinally onto the front axle (front loads, rear unloads)."""
    n = 64
    P = _batch(n, mu=0.9)
    vx0 = torch.full((n,), 14.0, device=DEV)
    z0 = torch.zeros(n, device=DEV)
    st, gear = init_state(vx0, z0, z0, P)
    fz0 = None
    act = torch.zeros(n, 3, device=DEV)
    act[:, 2] = 1.0                              # full brake
    diag = None
    for k in range(20):
        st, gear, diag = physics_step(st, act, gear, P, 0.02)
        if k == 0:
            fz0 = diag["fz"].clone()
    pitch = st[:, IDX["pitch"]]
    assert torch.isfinite(pitch).all()
    assert pitch.abs().mean() > 1e-3, "pitch did not respond to braking deceleration"
    # longitudinal transfer: front axle loads up, rear unloads, under braking.
    fz = diag["fz"]
    front = fz[:, 0] + fz[:, 1]
    rear = fz[:, 2] + fz[:, 3]
    front0 = fz0[:, 0] + fz0[:, 1]
    rear0 = fz0[:, 2] + fz0[:, 3]
    assert (front.mean() > front0.mean()) and (rear.mean() < rear0.mean()), \
        "braking did not transfer load onto the front axle"


def test_per_template_corner_spec_overridable():
    """The measured suspension dampers / corner spec are per-template config (cross-vehicle): a
    different CornerSpec builds a valid batch (generality by construction)."""
    n = 32
    cs = CornerSpec(damp_shock_front=8000.0, damp_shock_rear=12000.0)
    P = make_tier_a_param_batch(TierAParams(), n, mu=0.7, device=DEV, corner=cs)
    vx0 = torch.full((n,), 9.0, device=DEV)
    z0 = torch.zeros(n, device=DEV)
    st, gear = init_state(vx0, z0, z0, P)
    act = torch.zeros(n, 3, device=DEV); act[:, 0] = 0.4
    for _ in range(30):
        st, gear, _ = physics_step(st, act, gear, P, 0.02)
    assert torch.isfinite(st).all()


if __name__ == "__main__":
    test_runs_batched_and_finite()
    test_differentiable_single_step()
    test_roll_responds_to_lateral_accel()
    test_pitch_responds_to_longitudinal_accel()
    test_per_template_corner_spec_overridable()
    print("all tier-a smoke tests passed on", DEV)
