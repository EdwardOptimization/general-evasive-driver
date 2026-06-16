"""PARITY TEST for src/autodrift/gpu_env_physics.py — the obs72 hard gate.

Same gate as ``tests/test_gpu_env.py`` but for the FAITHFUL-PHYSICS env
(``GPUPhysicsAutoDriftEnv``): drive the analytic ``AutoDriftEnv`` (env.py) for a drift
episode AND an avoidance episode with a fixed action sequence; at every step capture the
env's raw state + obs72 + env.py's force-based ax/ay; inject the SAME raw states into
``GPUPhysicsAutoDriftEnv.obs72_from_state`` and assert ``max|gpu_obs72 - cpu_obs72| <
1e-3`` across all dims/steps. This isolates the obs72 builder from the dynamics.

THE ONE LAYOUT DIFFERENCE vs gpu_env: the physics state has SEPARATE throttle (idx 7) and
brake (idx 8) channels, so ``obs72_from_state`` takes ``throttle``/``brake`` as injected
[N] tensors instead of deriving them from a single signed ``drive_force``. To match env.py
byte-for-byte we feed env.py's EXACT throttle_state/brake_state (recovered from the
injected drive_force exactly as env.py computes them: drive_force>=0 -> throttle =
drive_force/max_drive, else brake = -drive_force/max_brake). env.py emits those same two
values in obs[7]/obs[8], so channels 7/8 must match too.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "feasibility_audit"))

from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig  # noqa: E402
from autodrift.gpu_env_physics import GPUPhysicsAutoDriftEnv  # noqa: E402

CPU = torch.device("cpu")


# ----------------------------------------------------------------- env construction
def _drift_env() -> AutoDriftEnv:
    cfg = DriftEnvConfig(
        dt=0.02, max_steps=90, track_kind="circle", track_radius=70.0, track_width=34.0,
        road_lookahead_count=8, road_lookahead_spacing=5.0, obstacle_slots=4,
        obstacle_relative_velocity_mode="ego",
        obstacle=ObstacleTaskConfig(enabled=False),
    )
    return AutoDriftEnv(cfg)


def _avoidance_env() -> AutoDriftEnv:
    cfg = DriftEnvConfig(
        dt=0.02, max_steps=120, track_kind="circle", track_radius=70.0, track_width=34.0,
        road_lookahead_count=8, road_lookahead_spacing=5.0, obstacle_slots=4,
        obstacle_relative_velocity_mode="ego",
        speed_range=(9.0, 9.0), beta_target_range=(0.10, 0.10),
        obstacle=ObstacleTaskConfig(
            enabled=True,
            distance_range=(28.0, 28.0),
            half_width_range=(1.25, 1.25),
            lateral_offset_range=(0.0, 0.0),
            ego_half_width=0.90,
            finish_on_pass=True,
            finish_pass_distance=2.0,
            perception_reveal_step=4,
            perception_reveal_distance=40.0,
            allowed_labels=("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
        ),
    )
    return AutoDriftEnv(cfg)


def _scenario_from_env(env: AutoDriftEnv, scenario_type: str) -> dict:
    """Build a gpu_env scenario dict from a freshly-reset AutoDriftEnv instance.

    Physics params need lf/lr (-> wheelbase + front_axle_share) and iz/mass/mu, all present
    in env.params, so this is the same dict shape the gpu_env parity test uses.
    """
    cfg = env.config
    ob: dict = {"enabled": bool(cfg.obstacle.enabled)}
    if cfg.obstacle.enabled and env.obstacle_position is not None and env.obstacle_scenario is not None:
        ob.update({
            "x": float(env.obstacle_position[0]),
            "y": float(env.obstacle_position[1]),
            "half_width": float(env.obstacle_scenario.obstacle_half_width),
            "ego_half_width": float(cfg.obstacle.ego_half_width),
            "perception_reveal_step": int(cfg.obstacle.perception_reveal_step),
            "perception_reveal_distance": (
                None if cfg.obstacle.perception_reveal_distance is None
                else float(cfg.obstacle.perception_reveal_distance)),
            "finish_on_pass": bool(cfg.obstacle.finish_on_pass),
            "finish_pass_distance": float(cfg.obstacle.finish_pass_distance),
        })
    return {
        "scenario_id": "parity",
        "scenario_type": scenario_type,
        "dt": float(cfg.dt),
        "max_steps": int(cfg.max_steps),
        "track_kind": "circle",
        "track_radius": float(cfg.track_radius),
        "track_width": float(cfg.track_width),
        "road_lookahead_count": int(cfg.road_lookahead_count),
        "road_lookahead_spacing": float(cfg.road_lookahead_spacing),
        "obstacle_slots": int(cfg.obstacle_slots),
        "obstacle_relative_velocity_mode": str(cfg.obstacle_relative_velocity_mode),
        "params": {
            "mass": float(env.params.mass), "mu": float(env.params.mu),
            "max_steer": float(env.params.max_steer), "max_steer_rate": float(env.params.max_steer_rate),
            "max_drive_force": float(env.params.max_drive_force), "max_brake_force": float(env.params.max_brake_force),
            "drive_tau": float(env.params.drive_tau), "steer_tau": float(env.params.steer_tau),
            "iz": float(env.params.iz), "lf": float(env.params.lf), "lr": float(env.params.lr),
            "cf": float(env.params.cf), "cr": float(env.params.cr),
            "drag_coeff": float(env.params.drag_coeff),
            "rolling_resistance": float(env.params.rolling_resistance),
            "gravity": float(env.params.gravity),
        },
        "initial_state": {
            "x": float(env.state.x), "y": float(env.state.y), "psi": float(env.state.psi),
            "vx": float(env.state.vx), "vy": float(env.state.vy), "yaw_rate": float(env.state.yaw_rate),
            "steer": float(env.state.steer), "drive_force": float(env.state.drive_force),
        },
        "obstacle": ob,
    }


def _fixed_actions(n_steps: int, kind: str) -> list[np.ndarray]:
    """A deterministic action sequence that excites drift / avoidance dynamics."""
    acts = []
    for t in range(n_steps):
        if kind == "drift":
            steer = -0.55 + 0.2 * np.sin(0.15 * t)
            thr = 0.6 + 0.2 * np.sin(0.07 * t)
            brk = -0.9
        else:
            steer = 0.4 * np.sin(0.2 * t)
            thr = 0.1
            brk = -0.5 + 0.3 * np.sin(0.1 * t)
        acts.append(np.array([steer, thr, brk], dtype=np.float64))
    return acts


def _run_cpu_episode(env: AutoDriftEnv, actions, seed: int, max_drive: float, max_brake: float):
    """Drive env.py, capturing per-step raw state + obs72 + env.py ax/ay + throttle/brake."""
    obs, _info = env.reset(seed=seed)
    records = []
    prev_action = np.array([0.0, -1.0, -1.0])
    prev_steer = 0.0
    records.append(_capture(env, obs, prev_steer, prev_action, max_drive, max_brake))
    for a in actions:
        prev_steer = float(env.state.steer)
        obs, _r, term, trunc, _info = env.step(a)
        records.append(_capture(env, obs, prev_steer, np.clip(a, -1.0, 1.0), max_drive, max_brake))
        if term or trunc:
            break
    return records


def _capture(env: AutoDriftEnv, obs: np.ndarray, prev_steer: float, prev_action: np.ndarray,
             max_drive: float, max_brake: float) -> dict:
    s = env.state
    ax = float(obs[3]) * 15.0
    ay = float(obs[4]) * 15.0
    # env.py's obs[7]/obs[8] = throttle_state/brake_state from the signed drive_force.
    # Recover them EXACTLY as env.py does (env.py:903-905) so the physics obs builder,
    # which reads throttle/brake DIRECTLY, reproduces channels 7/8 byte-for-byte.
    df = float(s.drive_force)
    throttle_state = df / max(max_drive, 1e-6) if df >= 0.0 else 0.0
    brake_state = (-df / max(max_brake, 1e-6)) if df < 0.0 else 0.0
    return {
        "state": np.array([s.x, s.y, s.psi, s.vx, s.vy, s.yaw_rate, s.steer], dtype=np.float64),
        "throttle": float(throttle_state),
        "brake": float(brake_state),
        "prev_steer": float(prev_steer),
        "prev_action": np.asarray(prev_action, dtype=np.float64),
        "step": int(env.step_count),
        "ax": ax, "ay": ay,
        "cpu_obs72": np.asarray(obs, dtype=np.float64).copy(),
    }


def _inject_and_build(gpu: GPUPhysicsAutoDriftEnv, scenario: dict, records) -> np.ndarray:
    """Run obs72_from_state on every captured CPU step (batched over all steps at once)."""
    dev = gpu.device
    n = len(records)
    # physics state is 17-dim; only 0..6 (pose+vel+steer) drive obs72. Pad the rest with 0.
    state = torch.zeros(n, gpu.state.shape[1] if gpu._allocated else 17, device=dev, dtype=gpu.dtype)
    raw = torch.tensor(np.stack([r["state"] for r in records]), device=dev, dtype=gpu.dtype)
    state[:, 0:7] = raw
    throttle = torch.tensor([r["throttle"] for r in records], device=dev, dtype=gpu.dtype)
    brake = torch.tensor([r["brake"] for r in records], device=dev, dtype=gpu.dtype)
    prev_steer = torch.tensor([r["prev_steer"] for r in records], device=dev, dtype=gpu.dtype)
    prev_action = torch.tensor(np.stack([r["prev_action"] for r in records]), device=dev, dtype=gpu.dtype)
    step = torch.tensor([r["step"] for r in records], device=dev, dtype=torch.long)
    ax = torch.tensor([r["ax"] for r in records], device=dev, dtype=gpu.dtype)
    ay = torch.tensor([r["ay"] for r in records], device=dev, dtype=gpu.dtype)

    def col(v, dt=gpu.dtype, long=False):
        return torch.full((n,), float(v), device=dev, dtype=torch.long if long else dt)

    ob = scenario.get("obstacle") or {}
    enabled = bool(ob.get("enabled"))
    static = {
        "track_radius": col(scenario["track_radius"]),
        "track_width": col(scenario["track_width"]),
        "dt": col(scenario["dt"]),
        "max_steer": col(scenario["params"]["max_steer"]),
        "max_steer_rate": col(scenario["params"]["max_steer_rate"]),
        "obs_enabled": torch.full((n,), enabled, device=dev, dtype=torch.bool),
        "obs_x": col(ob.get("x", 0.0)),
        "obs_y": col(ob.get("y", 0.0)),
        "obs_half_width": col(ob.get("half_width", 0.0)),
        "obs_reveal_step": col(ob.get("perception_reveal_step", 0), long=True),
        "obs_reveal_dist": col(ob.get("perception_reveal_distance") or 0.0),
        "obs_reveal_dist_set": torch.full(
            (n,), enabled and ob.get("perception_reveal_distance") is not None, device=dev, dtype=torch.bool),
    }
    out = GPUPhysicsAutoDriftEnv.obs72_from_state(
        state, static, prev_steer, prev_action, step, ax=ax, ay=ay, throttle=throttle, brake=brake)
    return out.cpu().numpy()


# --------------------------------------------------------------------- obs72 parity
def _make_gpu() -> GPUPhysicsAutoDriftEnv:
    return GPUPhysicsAutoDriftEnv(device=CPU, dtype=torch.float64, repo_root=ROOT)


@pytest.mark.parametrize("kind", ["drift", "avoidance"])
def test_obs72_parity(kind):
    seed = 7 if kind == "drift" else 11
    env = _drift_env() if kind == "drift" else _avoidance_env()
    env.reset(seed=seed)
    scenario = _scenario_from_env(env, kind)
    max_drive = scenario["params"]["max_drive_force"]
    max_brake = scenario["params"]["max_brake_force"]
    actions = _fixed_actions(env.config.max_steps, kind)
    records = _run_cpu_episode(
        _drift_env() if kind == "drift" else _avoidance_env(), actions, seed, max_drive, max_brake)

    gpu = _make_gpu()
    gpu_obs = _inject_and_build(gpu, scenario, records)
    cpu_obs = np.stack([r["cpu_obs72"] for r in records])

    err = np.abs(gpu_obs - cpu_obs)
    ego_err = err[:, 0:12].max()
    road_err = err[:, 12:44].max()
    obs_err = err[:, 44:72].max()
    total_err = err.max()
    print(f"\n[{kind}] obs72 parity (steps={len(records)}):")
    print(f"  ego   [0..11]  max|err| = {ego_err:.3e}")
    print(f"  road  [12..43] max|err| = {road_err:.3e}")
    print(f"  obst  [44..71] max|err| = {obs_err:.3e}")
    print(f"  TOTAL          max|err| = {total_err:.3e}")
    worst_dim = int(np.unravel_index(np.argmax(err), err.shape)[1])
    print(f"  worst dim = {worst_dim}")
    assert total_err < 1e-3, f"obs72 parity FAILED [{kind}]: max|err|={total_err:.3e} at dim {worst_dim}"


# --------------------------------------------------------------------- cuda smoke
@pytest.mark.skipif(not torch.cuda.is_available(), reason="cuda required")
def test_cuda_smoke_2048():
    env = _drift_env(); env.reset(seed=1)
    sc = _scenario_from_env(env, "drift")
    n = 2048
    gpu = GPUPhysicsAutoDriftEnv(device="cuda", dtype=torch.float32, repo_root=ROOT)
    obs = gpu.reset([sc for _ in range(n)])
    assert obs.shape == (n, 72)
    assert torch.isfinite(obs).all()

    import time
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    max_steps = int(sc["max_steps"])
    for t in range(max_steps):
        a = torch.zeros(n, 3, device="cuda")
        a[:, 0] = -0.5
        a[:, 1] = 0.4
        a[:, 2] = -0.9
        obs, reward, term, trunc, info = gpu.step(a)
        assert torch.isfinite(obs).all(), f"non-finite obs at step {t}"
        assert torch.isfinite(reward).all()
    torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    env_steps = n * max_steps
    print(f"\ncuda smoke: N={n}, {max_steps} steps, {dt:.3f}s -> {env_steps/dt:,.0f} env-steps/s")
    assert bool(trunc.all().item())


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-s", "-v"]))
