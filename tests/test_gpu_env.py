"""PARITY TEST for src/autodrift/gpu_env.py — the hard gate.

obs72 parity (the whole point): drive the analytic ``AutoDriftEnv`` (env.py) for a
drift episode AND an avoidance episode with a fixed action sequence; at every step
capture the env's raw state (x,y,psi,vx,vy,yaw_rate,steer_state,drive_force,
prev_steer, prev_action, step, obstacle pose, track geometry) AND env.py's obs72.
Inject those identical raw states into ``GPUAutoDriftEnv.obs72_from_state`` and assert
``max|gpu_obs72 - cpu_obs72| < 1e-3`` across all dims/steps. This isolates the obs72
builder from the dynamics (the surrogate dynamics differ from env.py's analytic ones,
so we do NOT closed-loop — we state-inject).

ax/ay note: env.py's obs[3]/obs[4] are *force-based* body accelerations; the canonical
obs72 / GPU env uses the finite-difference (v-prev_v)/dt. ``obs72_from_state`` takes
ax/ay as injected scalars, so the parity test feeds env.py's exact ax/ay (recovered as
obs[3]*15, obs[4]*15) — isolating the builder. The finite-difference path is exercised
separately by the smoke test's closed-loop step().

Also: reward / termination / controlled-drift agreement vs the trainer's reference
functions, and a cuda smoke test (N=4096, finite, one full episode).
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
from autodrift.gpu_env import (  # noqa: E402
    GPUAutoDriftEnv,
    MIN_SUSTAIN_STEPS,
    SCENARIO_AVOIDANCE,
    SCENARIO_DRIFT,
)

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
    # An avoidance scenario with an obstacle that is revealed after a few steps and a
    # finite reveal distance, so the parity test exercises the reveal gate transition.
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
    """Build a gpu_env scenario dict from a freshly-reset AutoDriftEnv instance."""
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
    rng = np.random.default_rng(0 if kind == "drift" else 1)
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


def _run_cpu_episode(env: AutoDriftEnv, actions, seed: int):
    """Drive env.py, capturing per-step raw state + obs72 + env.py ax/ay (force-based)."""
    obs, _info = env.reset(seed=seed)
    records = []
    # capture reset frame too (prev_action = [0,-1,-1]; prev_steer=0)
    prev_action = np.array([0.0, -1.0, -1.0])
    prev_steer = 0.0
    records.append(_capture(env, obs, prev_steer, prev_action))
    for a in actions:
        prev_steer = float(env.state.steer)
        obs, _r, term, trunc, _info = env.step(a)
        records.append(_capture(env, obs, prev_steer, np.clip(a, -1.0, 1.0)))
        if term or trunc:
            break
    return records


def _capture(env: AutoDriftEnv, obs: np.ndarray, prev_steer: float, prev_action: np.ndarray) -> dict:
    s = env.state
    # env.py's obs[3]/obs[4] are force-based ax/ay; recover them to inject (so the builder
    # is exercised against env.py's exact value, isolating the builder from the ax/ay model).
    ax = float(obs[3]) * 15.0
    ay = float(obs[4]) * 15.0
    return {
        "state": np.array([s.x, s.y, s.psi, s.vx, s.vy, s.yaw_rate, s.steer, s.drive_force], dtype=np.float64),
        "prev_steer": float(prev_steer),
        "prev_action": np.asarray(prev_action, dtype=np.float64),
        "step": int(env.step_count),
        "ax": ax, "ay": ay,
        "cpu_obs72": np.asarray(obs, dtype=np.float64).copy(),
    }


def _inject_and_build(gpu: GPUAutoDriftEnv, scenario: dict, records) -> np.ndarray:
    """Run obs72_from_state on every captured CPU step (batched over all steps at once)."""
    dev = gpu.device
    n = len(records)
    state = torch.tensor(np.stack([r["state"] for r in records]), device=dev, dtype=gpu.dtype)
    prev_steer = torch.tensor([r["prev_steer"] for r in records], device=dev, dtype=gpu.dtype)
    prev_action = torch.tensor(np.stack([r["prev_action"] for r in records]), device=dev, dtype=gpu.dtype)
    step = torch.tensor([r["step"] for r in records], device=dev, dtype=torch.long)
    ax = torch.tensor([r["ax"] for r in records], device=dev, dtype=gpu.dtype)
    ay = torch.tensor([r["ay"] for r in records], device=dev, dtype=gpu.dtype)

    def col(v, dt=gpu.dtype, long=False):
        t = torch.full((n,), float(v), device=dev, dtype=torch.long if long else dt)
        return t

    ob = scenario.get("obstacle") or {}
    enabled = bool(ob.get("enabled"))
    static = {
        "track_radius": col(scenario["track_radius"]),
        "track_width": col(scenario["track_width"]),
        "dt": col(scenario["dt"]),
        "max_steer": col(scenario["params"]["max_steer"]),
        "max_steer_rate": col(scenario["params"]["max_steer_rate"]),
        "max_drive_force": col(scenario["params"]["max_drive_force"]),
        "max_brake_force": col(scenario["params"]["max_brake_force"]),
        "obs_enabled": torch.full((n,), enabled, device=dev, dtype=torch.bool),
        "obs_x": col(ob.get("x", 0.0)),
        "obs_y": col(ob.get("y", 0.0)),
        "obs_half_width": col(ob.get("half_width", 0.0)),
        "obs_reveal_step": col(ob.get("perception_reveal_step", 0), long=True),
        "obs_reveal_dist": col(ob.get("perception_reveal_distance") or 0.0),
        "obs_reveal_dist_set": torch.full(
            (n,), enabled and ob.get("perception_reveal_distance") is not None, device=dev, dtype=torch.bool),
    }
    out = GPUAutoDriftEnv.obs72_from_state(state, static, prev_steer, prev_action, step, ax=ax, ay=ay)
    return out.cpu().numpy()


# --------------------------------------------------------------------- obs72 parity
def _make_gpu() -> GPUAutoDriftEnv:
    return GPUAutoDriftEnv(device=CPU, dtype=torch.float64, repo_root=ROOT, use_rear_sat_head=True)


@pytest.mark.parametrize("kind", ["drift", "avoidance"])
def test_obs72_parity(kind):
    seed = 7 if kind == "drift" else 11
    env = _drift_env() if kind == "drift" else _avoidance_env()
    env.reset(seed=seed)
    scenario = _scenario_from_env(env, kind)
    actions = _fixed_actions(env.config.max_steps, kind)
    records = _run_cpu_episode(_drift_env() if kind == "drift" else _avoidance_env(), actions, seed)

    gpu = _make_gpu()
    gpu_obs = _inject_and_build(gpu, scenario, records)
    cpu_obs = np.stack([r["cpu_obs72"] for r in records])

    err = np.abs(gpu_obs - cpu_obs)
    # exclude obs[3],obs[4] (ax/ay) only if env.py force-based differs — but we INJECTED
    # env.py's exact ax/ay, so they must match too. Report per dim-block.
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


# ------------------------------------------------------ reward / termination / drift flag
def test_reward_termination_drift_flag_agreement():
    """Closed-loop GPU step on a drift + avoidance scenario; check reward / termination /
    controlled-drift against the trainer's reference functions on the SAME states."""
    import phase4_e4_drift_regime_pricing as e4  # noqa: E402
    import phase4_f2_train as f2  # noqa: E402

    env_d = _drift_env(); env_d.reset(seed=3)
    env_a = _avoidance_env(); env_a.reset(seed=5)
    sc_d = _scenario_from_env(env_d, "drift")
    sc_a = _scenario_from_env(env_a, "avoidance")

    gpu = _make_gpu()
    gpu.reset([sc_d, sc_a])
    n_steps = 90

    drift_reward_mismatch = 0
    drift_flag_mismatch = 0
    avoid_reward_mismatch = 0
    rng = np.random.default_rng(0)
    for t in range(n_steps):
        # mild drift-exciting action for env 0, steering for env 1
        a = torch.tensor([
            [-0.5 + 0.2 * np.sin(0.1 * t), 0.5, -0.9],
            [0.3 * np.sin(0.2 * t), 0.1, -0.4],
        ], dtype=torch.float64)
        obs, reward, term, trunc, info = gpu.step(a)

        # --- drift env (index 0): reference _drift_reward on the SAME controlled flag ---
        controlled0 = bool(info["controlled_drift"][0].item())
        cur0 = int(info["current_controlled"][0].item())
        succ0 = bool(info["drift_success_inc"][0].item())
        coll0 = bool(info["collision"][0].item())
        ref_drift = f2._drift_reward(controlled0, succ0, coll0, cur0)
        if abs(ref_drift - float(reward[0].item())) > 1e-5:
            drift_reward_mismatch += 1

        # cross-check the controlled-drift FLAG against e4's definition on the obs72/beta path:
        # rebuild beta/vx/yaw from obs0 (the GPU obs the trainer would see)
        o0 = obs[0].cpu().numpy()
        vx, vy, yaw_rate, beta = e4._obs_kinematics(o0)
        high_beta = abs(beta) >= e4.BETA_THRESHOLD_RAD
        band = e4.MIN_SPEED_MPS <= vx <= e4.MAX_SPEED_MPS and abs(yaw_rate) <= e4.YAW_RATE_LIMIT_RAD_S
        # rear_saturated is the learned head's call inside the GPU env; the e4 obs path can't
        # recompute it, so we only assert the obs-recoverable gates agree with the flag's
        # high_beta & band components.
        if controlled0 and not (high_beta and band):
            drift_flag_mismatch += 1

        # --- avoidance env (index 1): reference _avoidance_reward on a built info dict ---
        info_a = {
            "collision": bool(info["collision"][1].item()),
            "termination_reason": "off_track" if bool(info["offtrack"][1].item()) else "",
            "completion_reason": (
                "obstacle_pass" if bool(info["obstacle_completed"][1].item())
                else ("max_steps" if bool(info["at_max_steps"][1].item()) else "")),
            "min_clearance_margin": float(info["min_clearance_margin"][1].item()),
            "vx_norm": abs(float(a[1, 0].item() * 0 + (obs[1, 0].item()))),  # placeholder; replaced below
        }
        # vx_norm in the trainer is |prev_obs[0]|; reconstruct from the GPU's prev_vx echo
        info_a["vx_norm"] = abs(float(gpu.prev_vx[1].item()) / 20.0)
        ref_avoid = f2._avoidance_reward(info_a, bool(term[1].item()), bool(trunc[1].item()))
        if abs(ref_avoid - float(reward[1].item())) > 1e-4:
            avoid_reward_mismatch += 1

        if bool(term[0].item() or trunc[0].item()) and bool(term[1].item() or trunc[1].item()):
            break

    print(f"\nreward/flag agreement over {n_steps} steps:")
    print(f"  drift reward mismatches    = {drift_reward_mismatch}")
    print(f"  drift flag (obs-gate) mism = {drift_flag_mismatch}")
    print(f"  avoidance reward mismatches= {avoid_reward_mismatch}")
    assert drift_reward_mismatch == 0
    assert drift_flag_mismatch == 0
    assert avoid_reward_mismatch == 0


# --------------------------------------------------------------------- cuda smoke
@pytest.mark.skipif(not torch.cuda.is_available(), reason="cuda required")
def test_cuda_smoke_4096():
    env = _drift_env(); env.reset(seed=1)
    sc = _scenario_from_env(env, "drift")
    n = 4096
    gpu = GPUAutoDriftEnv(device="cuda", dtype=torch.float32, repo_root=ROOT)
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
    assert bool(trunc.all().item())  # full episode -> all truncated at max_steps


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-s", "-v"]))
