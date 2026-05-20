import numpy as np

from autodrift.dynamics import SingleTrackDriftModel, VehicleParams, VehicleState, sample_vehicle_params


def test_tire_forces_respect_friction_capacity():
    params = VehicleParams(mu=0.6)
    model = SingleTrackDriftModel(params)
    forces = model.tire_forces(vx=8.0, vy=2.0, yaw_rate=0.5, steer=0.2, drive_force=1e9)

    assert abs(forces.fx_rear) <= params.mu * forces.fz_rear
    assert abs(forces.fy_front) <= params.mu * forces.fz_front + 1e-9
    assert np.hypot(forces.fx_rear, forces.fy_rear) <= params.mu * forces.fz_rear + 1e-6


def test_model_step_returns_finite_state():
    model = SingleTrackDriftModel()
    state = VehicleState(x=18.0, y=0.0, psi=1.57, vx=8.0, vy=0.0, yaw_rate=0.4)
    next_state, forces = model.step(state, np.array([0.1, 0.5]), dt=0.02)

    assert np.all(np.isfinite(next_state.as_array()))
    assert np.isfinite(forces.fy_front)
    assert next_state.x != state.x


def test_randomization_changes_hidden_parameters():
    rng = np.random.default_rng(3)
    p1 = sample_vehicle_params(rng)
    p2 = sample_vehicle_params(rng)

    assert p1.mu != p2.mu
    assert p1.mass != p2.mass
    assert abs((p1.lf + p1.lr) - VehicleParams().wheelbase) < 1e-12
