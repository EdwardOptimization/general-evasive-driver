"""WP1 injected-belief hook: bit-level backward compatibility + decision-tick
injection semantics (Phase-2 plan WP1.3; stage-1 infrastructure tests).

Pre-registered acceptance criteria (frozen before implementation):

1. No injection (default) and a never-firing injector produce bit-identical
   action sequences and telemetry to each other, for seeker AND oracle modes,
   on clean and degraded (delay5 / noise0.05) streams -- the new code paths
   are inert unless an estimate is delivered.
2. The legacy keyword surface is unchanged: controllers built through the
   wp0/degraded machinery (degraded_regime_final.make_classes) without the
   new kwarg behave identically and their telemetry rows carry NO new keys.
3. Injection fires exactly at the decision tick (the first obstacle-present
   frame == the inner controller's reveal step) and replaces _mu_eff /
   _limit_est from that tick on (seeker detector updates no longer override).
4. Oracle + injected true mu is bit-identical to the plain oracle (the hook
   routes through the same belief consumption).
5. Pre-decision actions are bit-identical between injected and non-injected
   controllers; an injected wrong mu changes at least one post-decision
   action (the hook is live).

Infrastructure tests only; no capability claim.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts/feasibility_audit"


def load_module(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def stack():
    reg = load_module(SCRIPTS / "ramp_policy_voi_regime.py", "ramp_policy_voi_regime")
    mod_b = load_module(SCRIPTS / "voi_commitment_task_design.py", "voi_commitment_task_design")
    mod_c = load_module(SCRIPTS / "voi_conditional_prior.py", "voi_conditional_prior")
    deg = load_module(SCRIPTS / "degraded_regime_final.py", "degraded_regime_final")
    _, controller_cls = deg.make_classes(reg)
    design = reg.make_design(mod_b, 9.5)
    return {"reg": reg, "mod_b": mod_b, "interp": mod_c.interp_lin, "deg": deg,
            "controller_cls": controller_cls, "design": design}


class NeverInjector:
    """observe() everything, never deliver an estimate."""

    def __init__(self):
        self.n_observed = 0

    def observe(self, obs):
        self.n_observed += 1

    def estimate(self):
        return None


class ConstantInjector:
    def __init__(self, value: float):
        self.value = float(value)
        self.n_observed = 0

    def observe(self, obs):
        self.n_observed += 1

    def estimate(self):
        return self.value


def make_env(stack, mu: float, seed: int, degradation: dict | None):
    from autodrift.config import build_env_config
    from autodrift.env import AutoDriftEnv
    from autodrift.observation_degradation_wrapper import make_env_from_config

    reg, mod_b, interp = stack["reg"], stack["mod_b"], stack["interp"]
    d = reg.jittered_distance(interp, mu, seed)
    level = mod_b.LevelSpec(mu=mu, d_lo=d, d_hi=d, entry_speed=reg.v_star(interp, mu))
    cfg = mod_b.level_env_config(stack["design"], level)
    if degradation is None:
        return stack["deg"].EnvShim(AutoDriftEnv(build_env_config(cfg)))
    cfg["observation_degradation"] = dict(degradation)
    return stack["deg"].EnvShim(make_env_from_config(build_env_config(cfg)))


def make_controller(stack, mode: str, mu_true: float | None = None, **kw):
    reg, mod_b, interp = stack["reg"], stack["mod_b"], stack["interp"]
    base = dict(smooth_window=1, ramp_rate=20000.0, tau=0.08, backoff=0.06,
                strategy="hold", dv=0.0)
    if mode == "oracle":
        base = dict(mu_true=mu_true)
    base.update(kw)
    return stack["controller_cls"](mod_b, interp, stack["design"], f"test_{mode}",
                                   mode=mode, **base)


def rollout_actions(stack, controller, mu: float, seed: int, degradation: dict | None,
                    max_steps: int = 400):
    env = make_env(stack, mu, seed, degradation)
    controller.reset()
    actions, frames = [], []
    try:
        obs, _ = env.reset(seed=seed)
        for _ in range(max_steps):
            frames.append(np.asarray(obs, dtype=np.float64).copy())
            action = controller.act(np.asarray(obs, dtype=np.float64))
            actions.append(np.asarray(action, dtype=np.float64).copy())
            obs, _, term, trunc, _ = env.step(np.asarray(action, dtype=np.float64))
            if term or trunc:
                break
    finally:
        env.close()
    return np.asarray(actions), controller.telemetry_row()


CELLS = (None, {"delay_steps": 5}, {"noise_std": 0.05})
CELL_IDS = ("clean", "delay5", "noise0.05")


@pytest.mark.parametrize("degradation", CELLS, ids=CELL_IDS)
@pytest.mark.parametrize("mode", ["seeker", "oracle"])
def test_never_firing_injector_is_bitwise_inert(stack, degradation, mode):
    mu, seed = 0.62, 20270101
    base_actions, base_tel = rollout_actions(
        stack, make_controller(stack, mode, mu_true=mu), mu, seed, degradation)
    inj = NeverInjector()
    inj_actions, inj_tel = rollout_actions(
        stack, make_controller(stack, mode, mu_true=mu, injected_belief=inj),
        mu, seed, degradation)
    assert base_actions.shape == inj_actions.shape
    assert np.array_equal(base_actions, inj_actions)
    assert inj.n_observed == len(inj_actions)
    # telemetry: identical legacy keys/values; ONLY the injection extras differ
    extras = {"mu_injected", "injection_step"}
    assert set(inj_tel) == set(base_tel) | extras
    for k, v in base_tel.items():
        if isinstance(v, float) and np.isnan(v):
            assert np.isnan(inj_tel[k])
        else:
            assert inj_tel[k] == v
    assert inj_tel["injection_step"] == -1


def test_legacy_construction_has_no_new_telemetry_keys(stack):
    mu, seed = 0.62, 20270102
    _, tel = rollout_actions(stack, make_controller(stack, "seeker"), mu, seed,
                             {"delay_steps": 5})
    assert "mu_injected" not in tel and "injection_step" not in tel


def test_injection_fires_at_decision_tick_and_overrides_belief(stack):
    mu, seed = 0.62, 20270103
    injected_value = 0.40
    controller = make_controller(stack, "seeker",
                                 injected_belief=ConstantInjector(injected_value))
    rollout_actions(stack, controller, mu, seed, {"delay_steps": 5})
    assert controller.injection_step >= 0
    assert controller.inner.reveal_step == controller.injection_step
    assert controller.mu_injected == pytest.approx(injected_value)
    assert controller._mu_eff() == pytest.approx(injected_value)
    reg = stack["reg"]
    assert controller._limit_est() == pytest.approx(
        reg.TIRE_CAP * reg.FZR * injected_value)


def test_oracle_with_injected_true_mu_is_bitwise_identical(stack):
    mu, seed = 0.85, 20270104
    base_actions, _ = rollout_actions(
        stack, make_controller(stack, "oracle", mu_true=mu), mu, seed, {"delay_steps": 5})
    inj_actions, _ = rollout_actions(
        stack, make_controller(stack, "oracle", mu_true=mu,
                               injected_belief=ConstantInjector(mu)),
        mu, seed, {"delay_steps": 5})
    assert np.array_equal(base_actions, inj_actions)


def test_wrong_injection_changes_only_post_decision_actions(stack):
    mu, seed = 0.95, 20270105
    base_actions, _ = rollout_actions(
        stack, make_controller(stack, "oracle", mu_true=mu), mu, seed, {"delay_steps": 5})
    controller = make_controller(stack, "oracle", mu_true=mu,
                                 injected_belief=ConstantInjector(0.30))
    inj_actions, _ = rollout_actions(stack, controller, mu, seed, {"delay_steps": 5})
    k = controller.injection_step
    assert k >= 1
    n_pre = min(k, len(base_actions), len(inj_actions))
    assert np.array_equal(base_actions[:n_pre], inj_actions[:n_pre])
    n_common = min(len(base_actions), len(inj_actions))
    assert (len(base_actions) != len(inj_actions)
            or not np.array_equal(base_actions[k:n_common], inj_actions[k:n_common]))
