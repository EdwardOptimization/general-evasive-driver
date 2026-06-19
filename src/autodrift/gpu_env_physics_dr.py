"""DOMAIN-RANDOMIZED variant of ``GPUPhysicsAutoDriftEnv`` (the avoid-fix experiment).

WHY THIS EXISTS
---------------
The physics-env-trained full-scenario driver (``gpu_physics_policy_seed0.pt``) hit
drift=1.0 / avoid=1.0 on the PWR-TMeasy surrogate but **avoid=0.000 on real Chrono**
(drift held at 1.0). That is the classic sim-to-sim OVERFIT signature: the policy tuned
itself to the surrogate's exact residual dynamics — most decisively the vx / powertrain
TIMING (the partial-throttle traction cap, the load-transfer split, the cruise resistance)
— which is precisely the dimension where the faithful rewrite still differs from Chrono.
Drift survives because the drift equilibrium is a saddle with low sensitivity to
friction/speed (Velenis 2010 / Goh-Gerdes 2020), so it transfers; avoidance is a
boundary/timing problem and does not.

THE FIX (this module): DOMAIN RANDOMIZATION on the DYNAMICS (NOT the task).
Per ENV, **re-randomised on every episode reset**, we sample the physics parameters within
physically-plausible ranges *around the measured values*, so the policy cannot tune to any
single surrogate operating point. The randomization deliberately SPANS the Chrono operating
point (especially the longitudinal/powertrain timing dimension it overfit), so a policy that
is robust to the whole band must be robust to Chrono too. This is the hand-tuned-range
domain-randomization recipe from the robotics synthesis (docs/robotics-recipes-for-autodrift
Part 3: "take only the *idea* — widen a randomization range — as a hand-tuned schedule";
do NOT adopt full ADR at this scale).

CRITICALLY: the obstacle / track / task geometry stays FIXED — DR is on DYNAMICS only. The
reward, termination contract, obs72 builder, success criterion, and the per-env terrain mu
(which already varies across the scenario grid) are all UNCHANGED.

WHAT IS RANDOMIZED (per env, per episode; ranges around the measured/scenario values)
-------------------------------------------------------------------------------------
  * mass               x U(0.85, 1.15)         (around scenario mass)
  * izz                x U(0.85, 1.15)         (around scenario yaw inertia)
  * front_axle_share   + U(-0.05, +0.05)       (additive, clamped to [0.40, 0.60])
  * sigma_scale        ~ U(0.10, 0.25)         (the measured-physical relaxation band; this
                                                REPLACES the env's fixed 0.165 per env)
  * tyre grip scale    x U(0.85, 1.15)         (front_grip_scale & rear_grip_scale, shared
                                                per env so the axle balance is preserved)
  * drive/long. bias   x U(0.7, 1.3)           (drive_scale — the per-env longitudinal
                                                force/accel multiplier; THE KEY dimension,
                                                covers the vx-timing/powertrain gap it overfit)
  * rolling resistance x U(0.7, 1.3)           (rolling_resist_coeff — the other half of the
                                                longitudinal-timing band: cruise/coast decel)
  * per-STEP process noise on body accel: vx,vy each get a small multiplicative jitter
                                          x (1 +/- ~3%) applied to the per-step velocity
                                          INCREMENT (dv) each control step (a stochastic
                                          accel disturbance, NOT a static bias).

  terrain ``mu`` is left to the scenario grid (already varies) — NOT re-randomised here.

The longitudinal pair (drive_scale, rolling_resist_coeff) is the over-randomized dimension on
purpose: it is what the policy overfit. With drive_scale spanning [0.7, 1.3] the policy sees
both faster- and slower-accelerating surrogates than the nominal one, so it cannot exploit
the nominal vx-timing — it must avoid robustly across the band, and the Chrono operating point
lies inside that band.

IMPLEMENTATION
--------------
A thin subclass of ``GPUPhysicsAutoDriftEnv``. It calls the parent ``reset`` (which builds the
nominal per-env ``PhysParamBatch`` from the scenarios), then **multiplies/offsets the per-env
parameter tensors in place** with freshly sampled DR factors — so every other behaviour (state
seeding, obs, reward, termination, success) is byte-identical to the parent. ``step`` calls the
parent step, then adds the per-step body-accel process noise by perturbing the post-step vx/vy
increment (and refreshing prev_vx/prev_vy so the ax/ay finite-difference and drift flag stay
self-consistent). The DR is on DYNAMICS only; the parent's frozen contract is untouched.

This file is NEW; it does not modify gpu_env_physics.py / gpu_physics_pwr.py. The trainer
variant is ``scripts/feasibility_audit/phase4_f2_gpu_train_dr.py``.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import torch

from autodrift.gpu_env_physics import GPUPhysicsAutoDriftEnv, IDX


# ----------------------------------------------------------------------- DR ranges
# All ranges are around the MEASURED / scenario values and physically plausible. The
# longitudinal pair (drive_scale, rolling_resist_coeff) is the widest on purpose: it is the
# vx-timing/powertrain dimension the no-DR policy overfit, and it must span the Chrono point.
DR_RANGES: dict[str, tuple[float, float]] = {
    "mass_mult": (0.85, 1.15),            # x mass
    "izz_mult": (0.85, 1.15),             # x izz
    "front_share_offset": (-0.05, 0.05),  # + front_axle_share (additive)
    "sigma_scale": (0.10, 0.25),          # sigma_scale absolute band (measured-physical)
    "grip_mult": (0.85, 1.15),            # x front_grip_scale & rear_grip_scale (shared)
    "drive_mult": (0.70, 1.30),           # x drive_scale  (THE key longitudinal-timing knob)
    "roll_mult": (0.70, 1.30),            # x rolling_resist_coeff (cruise/coast longitudinal)
}
# clamp bounds for the additive front-share so it stays a sane load split.
FRONT_SHARE_CLAMP = (0.40, 0.60)
# per-step multiplicative process noise on the body-accel (velocity increment): 1 +/- this.
ACCEL_PROCESS_NOISE = 0.03   # ~3% std on dvx/dvy each control step


class GPUPhysicsDRAutoDriftEnv(GPUPhysicsAutoDriftEnv):
    """``GPUPhysicsAutoDriftEnv`` with per-env / per-episode DYNAMICS domain randomization.

    Drop-in for the parent (same reset/step/success/.priv6/.scenario_type/.done API). DR is
    applied to the per-env physics parameters at reset (re-sampled each episode) and as a
    small per-step body-accel process noise; the task geometry, reward, termination, and
    success criterion are UNCHANGED.
    """

    def __init__(
        self,
        *args: Any,
        dr_ranges: Mapping[str, tuple[float, float]] | None = None,
        accel_process_noise: float = ACCEL_PROCESS_NOISE,
        dr_seed: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.dr_ranges: dict[str, tuple[float, float]] = dict(DR_RANGES)
        if dr_ranges is not None:
            self.dr_ranges.update(dr_ranges)
        self.accel_process_noise = float(accel_process_noise)
        # dedicated generator so DR sampling is reproducible and independent of the global RNG
        # used by the policy/rollout (the env is re-reset every PPO update & every eval).
        self._dr_gen = torch.Generator(device=self.device)
        if dr_seed is not None:
            self._dr_gen.manual_seed(int(dr_seed))
        else:
            # seed from the global RNG so torch.manual_seed(cfg.seed) still makes runs reproducible
            self._dr_gen.manual_seed(int(torch.randint(0, 2**31 - 1, (1,)).item()))

    # ------------------------------------------------------------------ DR samplers
    def _u(self, lo: float, hi: float, n: int) -> torch.Tensor:
        """Per-env U(lo, hi) [n] on-device, from the dedicated DR generator."""
        r = torch.rand(n, generator=self._dr_gen, device=self.device, dtype=self.dtype)
        return lo + (hi - lo) * r

    def _apply_dr(self, n: int) -> dict[str, torch.Tensor]:
        """Sample DR factors for n envs and multiply/offset the per-env PhysParamBatch in place.

        Returns the sampled factor tensors (for logging / inspection). Called AFTER the parent
        reset has built the nominal ``self.P`` from the scenarios, so it modifies the measured
        per-env values rather than replacing them."""
        rg = self.dr_ranges
        t = self.P.t  # the per-env scalar tensor dict (mutated in place)

        mass_mult = self._u(*rg["mass_mult"], n)
        izz_mult = self._u(*rg["izz_mult"], n)
        front_off = self._u(*rg["front_share_offset"], n)
        sigma_abs = self._u(*rg["sigma_scale"], n)
        grip_mult = self._u(*rg["grip_mult"], n)
        drive_mult = self._u(*rg["drive_mult"], n)
        roll_mult = self._u(*rg["roll_mult"], n)

        t["mass"] = t["mass"] * mass_mult
        t["izz"] = t["izz"] * izz_mult
        t["front_axle_share"] = torch.clamp(
            t["front_axle_share"] + front_off, FRONT_SHARE_CLAMP[0], FRONT_SHARE_CLAMP[1]
        )
        # sigma_scale is an ABSOLUTE band (the measured-physical relaxation band), not a mult:
        # it replaces the env's fixed 0.165 per env.
        t["sigma_scale"] = sigma_abs
        # tyre grip: shared front/rear multiplier so the axle BALANCE is preserved (we randomize
        # the overall grip level, not the front/rear bias — bias is what makes drift transfer).
        t["front_grip_scale"] = t["front_grip_scale"] * grip_mult
        t["rear_grip_scale"] = t["rear_grip_scale"] * grip_mult
        # longitudinal-timing band (the overfit dimension): drive force scale + cruise resistance.
        t["drive_scale"] = t["drive_scale"] * drive_mult
        t["rolling_resist_coeff"] = t["rolling_resist_coeff"] * roll_mult

        return {
            "mass_mult": mass_mult, "izz_mult": izz_mult, "front_off": front_off,
            "sigma_scale": sigma_abs, "grip_mult": grip_mult,
            "drive_mult": drive_mult, "roll_mult": roll_mult,
        }

    # ------------------------------------------------------------------ reset
    def reset(self, scenarios: Sequence[Mapping[str, Any]]) -> torch.Tensor:
        """Parent reset (nominal PhysParamBatch from scenarios) + per-episode DR on the dynamics.

        The DR factors are re-sampled every reset, so each PPO rollout / eval episode sees a
        FRESH per-env dynamics draw. The initial state is seeded by the parent from the
        scenario (DR does not move the task), so we re-seed it after DR ONLY if DR changed a
        param the seed depends on. ``init_state`` uses r_eff / final_drive / shift tables (all
        un-randomized) for the wheel-omega + gear seed and wheelbase for the slip-lag seed; we
        do randomize wheelbase? — NO (wheelbase is not in DR_RANGES), so the parent's seed
        stays exactly consistent and no re-seed is needed."""
        obs = super().reset(scenarios)
        self._last_dr = self._apply_dr(self.N)
        # the obs72 returned by the parent is from the seeded state (ax=ay=0, pose/vel from the
        # scenario) and does NOT depend on the physics params, so it is still correct after DR.
        return obs

    # ------------------------------------------------------------------ step
    def step(self, action: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        """Parent physics step + per-step body-accel process noise (a stochastic disturbance).

        After the parent advances ``physics_step`` and computes everything, we perturb the
        per-step velocity INCREMENT (dvx, dvy) by a small multiplicative jitter ~ (1 +/- 3%):
        this is an additive accel disturbance on top of the dynamics (it makes the policy robust
        to small unmodelled per-step accel errors — the residual the surrogate cannot capture),
        NOT a static bias. We then refresh the obs72 ego/obstacle channels and the
        prev_vx/prev_vy / drift state so the ax/ay finite-difference, the controlled-drift flag,
        and the next step's slip all stay self-consistent with the perturbed velocity. The
        reward/termination already computed by the parent are KEPT (the noise is a tiny vx/vy
        perturbation; perturbing reward/clearance too would double-count it and is unnecessary
        for the robustness goal — we want robust *dynamics*, the reward contract stays frozen).

        The pre-step steer (needed to rebuild obs72's steer_rate channel) is captured BEFORE the
        parent step, since the parent overwrites self.prev_steer with the post-step value."""
        sigma = self.accel_process_noise
        # capture the pre-step steer for the steer_rate obs channel (parent uses the local
        # pre-step value; after super().step it stores the POST-step steer in self.prev_steer).
        pre_step_steer = self.state[:, IDX["steer"]].clone() if self._allocated else None

        obs, reward, terminated, truncated, info = super().step(action)
        if sigma <= 0.0:
            return obs, reward, terminated, truncated, info

        n = self.N
        dt0 = self.dt  # [N]
        # parent set prev_vx/prev_vy to the NEW (post-step) vx/vy; pre-step values come from the
        # finite-difference ax/ay it just reported (ax = (vx_new - vx_old)/dt0).
        vx_new = self.state[:, IDX["vx"]]
        vy_new = self.state[:, IDX["vy"]]
        vx_old = vx_new - info["ax"] * dt0
        vy_old = vy_new - info["ay"] * dt0
        dvx = vx_new - vx_old
        dvy = vy_new - vy_old
        # multiplicative jitter on the increment: dv *= (1 + N(0, sigma)), clamped to keep it a
        # small, bounded disturbance (no sign flips on the increment).
        jx = torch.randn(n, generator=self._dr_gen, device=self.device, dtype=self.dtype)
        jy = torch.randn(n, generator=self._dr_gen, device=self.device, dtype=self.dtype)
        fx = torch.clamp(1.0 + sigma * jx, 1.0 - 3.0 * sigma, 1.0 + 3.0 * sigma)
        fy = torch.clamp(1.0 + sigma * jy, 1.0 - 3.0 * sigma, 1.0 + 3.0 * sigma)
        vx_p = vx_old + dvx * fx
        vy_p = vy_old + dvy * fy

        # write the perturbed velocities back into the state + refresh the dependent fields so the
        # NEXT step's dynamics (and the controlled-drift flag, read off self.state) are consistent.
        self.state[:, IDX["vx"]] = vx_p
        self.state[:, IDX["vy"]] = vy_p
        new_ax = (vx_p - vx_old) / dt0
        new_ay = (vy_p - vy_old) / dt0
        self.prev_vx = vx_p.detach().clone()
        self.prev_vy = vy_p.detach().clone()
        info["ax"] = new_ax
        info["ay"] = new_ay

        # rebuild obs72 from the perturbed state, using the PRE-step steer (so steer_rate is
        # unchanged from what the parent produced) and the refreshed ax/ay. All other channels
        # (road geometry, obstacle present/pos, throttle/brake) recompute identically; the only
        # deltas vs the parent obs are the vx/vy/ax/ay ego channels and the obstacle rel-vel.
        prev_steer = pre_step_steer if pre_step_steer is not None else self.prev_steer
        obs = self.obs72_from_state(
            self.state, self._static_view(), prev_steer, self.prev_action,
            self.step_count, ax=new_ax, ay=new_ay,
            throttle=self.state[:, IDX["throttle"]], brake=self.state[:, IDX["brake"]],
        )
        return obs, reward, terminated, truncated, info
