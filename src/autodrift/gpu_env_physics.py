"""GPU-batched AutoDrift environment on the FAITHFUL PHYSICS rewrite (``gpu_physics_pwr``).

This is a drop-in for ``autodrift.gpu_env.GPUAutoDriftEnv`` (same public API:
``reset(scenarios)->obs72[N,72]``, ``step(action)->(obs72,reward,term,trunc,info)``,
``success()``, ``.priv6``, ``.scenario_type``, ``.done``) whose ONLY difference is the
dynamics: instead of the grey-box surrogate (``gpu_surrogate.grey_box_step``, which is
BLIND to collisions — collision bal-acc 0.503 = chance), it steps
``autodrift.gpu_physics_pwr.physics_step`` (the PWR-TMeasy faithful rewrite: EXACT Chrono
TMeasy tyre + measured slip-relaxation + FWD-corrected powertrain + measured cruise
resistance), which is collision-better (bal-acc 0.695) and lateral-faithful.

Everything OTHER than the dynamics — the obs72 builder, the reward, the termination
contract, the controlled-drift flag, the success criterion — is COPIED byte-for-byte from
``gpu_env.GPUAutoDriftEnv`` (the frozen, parity-tested contract). The one obs72 difference
is the source of the throttle/brake channels:

  * grey-box state is 8-dim ``[x,y,psi,vx,vy,yaw,steer,drive_force]`` and obs72 channels
    7/8 are derived from the single signed ``drive_force`` (>=0 -> throttle, <0 -> brake).
  * physics state is 17-dim with SEPARATE throttle (idx 7) and brake (idx 8) channels
    (the actuator-filtered commands in [0,1]); obs72 channels 7/8 read those DIRECTLY.

``obs72_from_state`` therefore takes ``throttle``/``brake`` as injected [N] tensors (the
parity test feeds env.py's exact ``throttle_state``/``brake_state`` so channels 7/8 match
env.py byte-for-byte; ``step`` feeds the physics state's idx-7/idx-8). All other obs72
channels are computed identically to ``gpu_env`` from state[:,0:7].

The physics state's pose/vel indices (0..5) and steer (6) coincide with the grey-box
indices, so the road / obstacle / kinematic obs channels are computed from the same
state slice with the same closed-form CircleTrack math as ``gpu_env``.

Per-env physics params come from the scenario ``params`` (mass, iz, lf, lr, ...) mapped
onto ``PhysParams`` fields:
  * ``mass``   <- params["mass"]            (drift 1684, avoid 1450)
  * ``izz``    <- params["iz"]              (drift 2400, avoid 2300)
  * ``wheelbase`` <- lf + lr
  * ``front_axle_share`` <- lr / (lf + lr)  (front load share ~ rear lever / wheelbase;
                                             avoid 1.45/2.80 = 0.518, drift 1.6/2.8 = 0.571)
  * ``max_steer`` / ``max_steer_rate``      <- params (steer scale matches env.py obs[5])
  * ``sigma_scale = 0.165``                 (per the consumer's brief)
  * terrain ``mu`` <- params["mu"]          (per-env friction passed to the tyre)
The throttle/brake/steer actuator-lag taus default to the PhysParams Chrono defaults;
``steer_tau`` is taken from params so the steer-state filter matches the grey-box one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import torch

from autodrift import gpu_physics_pwr as phys
from autodrift.gpu_physics_pwr import (
    PhysParams,
    PhysParamBatch,
    init_state,
    make_phys_param_batch,
    physics_step,
)

# ---- obs72 / reward / termination contract: import the FROZEN constants from gpu_env ----
from autodrift.gpu_env import (
    OBS_DIM,
    ACT_DIM,
    ROAD_LOOKAHEAD_COUNT,
    ROAD_LOOKAHEAD_SPACING,
    OBSTACLE_SLOTS,
    EGO_VX_SCALE,
    EGO_VY_SCALE,
    EGO_YAW_SCALE,
    EGO_AX_SCALE,
    EGO_AY_SCALE,
    ROAD_X_SCALE,
    ROAD_Y_SCALE,
    OBS_X_SCALE,
    OBS_Y_SCALE,
    OBS_RELVX_SCALE,
    OBS_RELVY_SCALE,
    OBS_HALF_W_SCALE,
    OBS_HALF_L_SCALE,
    COLLISION_PENALTY,
    OFFTRACK_PENALTY,
    AVOIDANCE_PASS_REWARD,
    DRIFT_SUCCESS_REWARD,
    CLEARANCE_SHAPING,
    DRIFT_PROGRESS_SHAPING,
    GRAZE_SPEED_NORM,
    GRAZE_MARGIN_M,
    GRAZE_PENALTY,
    BETA_THRESHOLD_RAD,
    REAR_SLIP_ANGLE_THRESHOLD_RAD,
    YAW_RATE_LIMIT_RAD_S,
    MIN_SPEED_MPS,
    MAX_SPEED_MPS,
    MIN_SUSTAIN_STEPS,
    SPEED_MIN,
    SPEED_MAX,
    YAW_HARD_LIMIT,
    EGO_HALF_WIDTH,
    SCENARIO_DRIFT,
    SCENARIO_AVOIDANCE,
)

# state idx (physics layout; pose/vel 0..5 + steer 6 coincide with grey-box).
PHYS_STATE_DIM = phys.PHYS_STATE_DIM  # 17
IDX = phys.IDX

# default sigma_scale for the faithful rewrite env (per the consumer's brief).
DEFAULT_SIGMA_SCALE = 0.165


def _wrap_pi(a: torch.Tensor) -> torch.Tensor:
    return (a + torch.pi) % (2.0 * torch.pi) - torch.pi


class GPUPhysicsAutoDriftEnv:
    """Batched AutoDrift env on the PWR-TMeasy faithful physics. Drop-in for GPUAutoDriftEnv.

    Same public API. ``reset`` materialises N envs (per-env ``PhysParamBatch`` + terrain
    mu from the scenario) and seeds the 17-dim physics state (init_state + injected pose).
    ``step`` advances ``physics_step``, then builds obs72 / reward / termination / success
    with the SAME logic as ``gpu_env`` (copied here), reading the throttle/brake channels
    from the physics state's separate idx-7/idx-8 (the one layout difference).
    """

    def __init__(
        self,
        *,
        device: torch.device | str = "cuda",
        dtype: torch.dtype = torch.float32,
        repo_root: str | Path | None = None,  # accepted for API parity (unused: curves auto-located)
        sigma_scale: float = DEFAULT_SIGMA_SCALE,
        curves: str | Path | dict | None = None,
        # accepted-and-ignored kwargs for drop-in compatibility with GPUAutoDriftEnv:
        residual_mlp_path: str | Path | None = None,
        rear_sat_head_path: str | Path | None = None,
        use_rear_sat_head: bool = True,
    ) -> None:
        self.device = torch.device(device)
        self.dtype = dtype
        self.sigma_scale = float(sigma_scale)
        self.curves = curves
        self.N = 0
        self._allocated = False

    # ------------------------------------------------------------------ allocation
    def _z(self, *shape: int) -> torch.Tensor:
        return torch.zeros(*shape, device=self.device, dtype=self.dtype)

    def reset(self, scenarios: Sequence[Mapping[str, Any]]) -> torch.Tensor:
        """Materialise N environments from a list of scenario dicts. Returns obs72[N,72]."""
        n = len(scenarios)
        if n == 0:
            raise ValueError("scenarios must be non-empty")
        self.N = n
        dev, dt = self.device, self.dtype

        # --- per-env static scenario tensors (identical to gpu_env) ---
        self.scenario_type = torch.zeros(n, dtype=torch.long, device=dev)
        self.track_radius = self._z(n)
        self.track_width = self._z(n)
        self.max_steps = torch.zeros(n, dtype=torch.long, device=dev)
        self.dt = self._z(n)

        # --- per-env physics params (mapped from scenario params onto PhysParams fields) ---
        defaults = PhysParams()
        mass_l: list[float] = []
        izz_l: list[float] = []
        wheelbase_l: list[float] = []
        front_share_l: list[float] = []
        max_steer_l: list[float] = []
        max_steer_rate_l: list[float] = []
        steer_tau_l: list[float] = []
        mu_l: list[float] = []

        # obstacle static (identical to gpu_env)
        self.obs_enabled = torch.zeros(n, dtype=torch.bool, device=dev)
        self.obs_x = self._z(n)
        self.obs_y = self._z(n)
        self.obs_half_width = self._z(n)
        self.obs_ego_half_width = torch.full((n,), EGO_HALF_WIDTH, device=dev, dtype=dt)
        self.obs_reveal_step = torch.zeros(n, dtype=torch.long, device=dev)
        self.obs_reveal_dist = self._z(n)
        self.obs_reveal_dist_set = torch.zeros(n, dtype=torch.bool, device=dev)
        self.obs_finish_on_pass = torch.zeros(n, dtype=torch.bool, device=dev)
        self.obs_finish_pass_distance = self._z(n)

        # initial pose+vel (drive obs72 + injected into the physics state)
        init_x = self._z(n)
        init_y = self._z(n)
        init_psi = self._z(n)
        init_vx = self._z(n)
        init_vy = self._z(n)
        init_yaw = self._z(n)
        priv6 = torch.zeros(n, 6, device=dev, dtype=dt)

        for i, sc in enumerate(scenarios):
            stype = str(sc.get("scenario_type", "drift")).lower()
            self.scenario_type[i] = SCENARIO_AVOIDANCE if stype.startswith("avoid") else SCENARIO_DRIFT
            self.track_radius[i] = float(sc["track_radius"])
            self.track_width[i] = float(sc["track_width"])
            self.max_steps[i] = int(sc["max_steps"])
            self.dt[i] = float(sc.get("dt", 0.02))
            p = sc["params"]
            lf = float(p["lf"])
            lr = float(p["lr"])
            wheelbase = lf + lr
            mass_l.append(float(p["mass"]))
            izz_l.append(float(p["iz"]))
            wheelbase_l.append(wheelbase)
            # front-axle LOAD share ~ rear lever / wheelbase (the front axle carries the
            # weight reacted at the rear lever lr). avoid 1.45/2.80 = 0.518 (matches brief).
            front_share_l.append(lr / max(wheelbase, 1e-6))
            max_steer_l.append(float(p["max_steer"]))
            max_steer_rate_l.append(float(p["max_steer_rate"]))
            steer_tau_l.append(float(p.get("steer_tau", defaults.steer_tau)))
            mu_l.append(float(p["mu"]))

            istate = sc["initial_state"]
            init_x[i] = float(istate["x"])
            init_y[i] = float(istate["y"])
            init_psi[i] = float(istate["psi"])
            init_vx[i] = float(istate["vx"])
            init_vy[i] = float(istate["vy"])
            init_yaw[i] = float(istate["yaw_rate"])

            ob = sc.get("obstacle") or {}
            if ob.get("enabled"):
                self.obs_enabled[i] = True
                self.obs_x[i] = float(ob["x"])
                self.obs_y[i] = float(ob["y"])
                self.obs_half_width[i] = float(ob["half_width"])
                self.obs_ego_half_width[i] = float(ob.get("ego_half_width", EGO_HALF_WIDTH))
                self.obs_reveal_step[i] = int(ob.get("perception_reveal_step", 0))
                rd = ob.get("perception_reveal_distance", None)
                if rd is not None:
                    self.obs_reveal_dist[i] = float(rd)
                    self.obs_reveal_dist_set[i] = True
                self.obs_finish_on_pass[i] = bool(ob.get("finish_on_pass", False))
                self.obs_finish_pass_distance[i] = float(ob.get("finish_pass_distance", 0.0))

            pv = sc.get("priv6", None)
            if pv is not None:
                priv6[i] = torch.as_tensor(pv, device=dev, dtype=dt)

        self.priv6 = priv6

        # all envs in a batch must share dt (physics_step takes a scalar dt; one substep
        # schedule). Mixed dt fails loudly (matches gpu_env's contract).
        dt_vals = {round(float(sc.get("dt", 0.02)), 9) for sc in scenarios}
        if len(dt_vals) != 1:
            raise ValueError(f"all envs in a batch must share dt; got {sorted(dt_vals)}")
        self._dt_scalar = float(next(iter(dt_vals)))

        # --- build the per-env PhysParamBatch (per-env scalars; shared LUT tables) ---
        param_src: dict[str, float | torch.Tensor] = defaults.as_dict()
        param_src["mass"] = torch.tensor(mass_l, device=dev, dtype=dt)
        param_src["izz"] = torch.tensor(izz_l, device=dev, dtype=dt)
        param_src["wheelbase"] = torch.tensor(wheelbase_l, device=dev, dtype=dt)
        param_src["front_axle_share"] = torch.tensor(front_share_l, device=dev, dtype=dt)
        param_src["max_steer"] = torch.tensor(max_steer_l, device=dev, dtype=dt)
        param_src["max_steer_rate"] = torch.tensor(max_steer_rate_l, device=dev, dtype=dt)
        param_src["steer_tau"] = torch.tensor(steer_tau_l, device=dev, dtype=dt)
        param_src["sigma_scale"] = float(self.sigma_scale)
        mu_t = torch.tensor(mu_l, device=dev, dtype=dt)
        self.P: PhysParamBatch = make_phys_param_batch(
            param_src, n, mu=mu_t, device=dev, dtype=dt, curves=self.curves,
        )
        # cache the per-env max_drive/brake for the obs builder's normalisers. The faithful
        # physics has no single "max drive force"; the obs throttle/brake channels are the
        # actuator commands in [0,1] DIRECTLY (state idx 7/8), so these are only used by the
        # parity injection path (env.py drive_force -> throttle/brake), not by step().
        self.max_steer = self.P["max_steer"]
        self.max_steer_rate = self.P["max_steer_rate"]

        # --- seed the 17-dim physics state from initial velocity, inject pose ---
        st, gear = init_state(init_vx, init_vy, init_yaw, self.P)
        st[:, IDX["x"]] = init_x
        st[:, IDX["y"]] = init_y
        st[:, IDX["psi"]] = init_psi
        self.state = st
        self.gear = gear

        # --- counters (identical to gpu_env) ---
        self.prev_vx = init_vx.clone()
        self.prev_vy = init_vy.clone()
        self.prev_steer = st[:, IDX["steer"]].clone()  # 0.0 at init (no injected steer)
        self.prev_action = torch.tensor([0.0, -1.0, -1.0], device=dev, dtype=dt).expand(n, 3).clone()

        self.step_count = torch.zeros(n, dtype=torch.long, device=dev)
        self.min_clearance = torch.full((n,), float("inf"), device=dev, dtype=dt)
        self.current_controlled = torch.zeros(n, dtype=torch.long, device=dev)
        self.longest_controlled = torch.zeros(n, dtype=torch.long, device=dev)
        self.collision_any = torch.zeros(n, dtype=torch.bool, device=dev)
        self.offtrack_any = torch.zeros(n, dtype=torch.bool, device=dev)
        self.passed_any = torch.zeros(n, dtype=torch.bool, device=dev)
        self.done = torch.zeros(n, dtype=torch.bool, device=dev)
        self._allocated = True

        # at reset, ax/ay finite-difference is 0 (prev_v == v).
        ax = self._z(n)
        ay = self._z(n)
        return self.obs72_from_state(
            self.state, self._static_view(), self.prev_steer, self.prev_action,
            self.step_count, ax=ax, ay=ay,
            throttle=self.state[:, IDX["throttle"]], brake=self.state[:, IDX["brake"]],
        )

    def _static_view(self) -> dict[str, torch.Tensor]:
        return {
            "track_radius": self.track_radius,
            "track_width": self.track_width,
            "dt": self.dt,
            "max_steer": self.P["max_steer"],
            "max_steer_rate": self.P["max_steer_rate"],
            "obs_enabled": self.obs_enabled,
            "obs_x": self.obs_x,
            "obs_y": self.obs_y,
            "obs_half_width": self.obs_half_width,
            "obs_reveal_step": self.obs_reveal_step,
            "obs_reveal_dist": self.obs_reveal_dist,
            "obs_reveal_dist_set": self.obs_reveal_dist_set,
        }

    # =============================================================== PURE obs72 builder
    @staticmethod
    def obs72_from_state(
        state: torch.Tensor,
        scenario: Mapping[str, torch.Tensor],
        prev_steer: torch.Tensor,
        prev_action: torch.Tensor,
        step: torch.Tensor,
        *,
        ax: torch.Tensor,
        ay: torch.Tensor,
        throttle: torch.Tensor,
        brake: torch.Tensor,
        idx: "Mapping[str, int] | None" = None,
    ) -> torch.Tensor:
        """Pure, batched obs72 builder for the PHYSICS state. No dynamics; state-injected.

        IDENTICAL to ``gpu_env.GPUAutoDriftEnv.obs72_from_state`` EXCEPT the throttle/brake
        channels (obs[7]/obs[8]) come from the injected ``throttle``/``brake`` [N] tensors
        (the physics state has SEPARATE throttle/brake idx 7/8, not a single signed
        drive_force). ``step`` passes state[:,7]/state[:,8]; the parity test passes env.py's
        exact throttle_state/brake_state so channels 7/8 match env.py byte-for-byte.

        state[N,>=7]: pose+vel at 0..5, steer at 6 (physics layout coincides with grey-box).
        scenario: dict of [N] static tensors (see ``_static_view``).
        prev_steer[N], prev_action[N,3], step[N] (int); ax[N], ay[N] body accelerations.
        Returns obs72[N,72].
        """
        dev = state.device
        dt_ = state.dtype
        n = state.shape[0]
        # Read the canonical planar sub-state BY NAME (gpu_sim StateContract) so this builder works on
        # ANY fidelity rung (pwr3 17-dim, tier_a 30-dim, ...). Default idx = the planar layout, so the
        # existing rung-0 call is byte-identical (cols 0..6) — verified by the obs72 parity test.
        if idx is None:
            idx = {"x": 0, "y": 1, "psi": 2, "vx": 3, "vy": 4, "yaw_rate": 5, "steer": 6}
        x = state[:, idx["x"]]; y = state[:, idx["y"]]; psi = state[:, idx["psi"]]
        vx = state[:, idx["vx"]]; vy = state[:, idx["vy"]]; yaw = state[:, idx["yaw_rate"]]
        steer = state[:, idx["steer"]]

        track_radius = scenario["track_radius"]
        track_width = scenario["track_width"]
        dt = scenario["dt"]
        max_steer = scenario["max_steer"]
        max_steer_rate = scenario["max_steer_rate"]

        obs = torch.zeros(n, OBS_DIM, device=dev, dtype=dt_)

        # --- ego channels [0..8] ---
        obs[:, 0] = vx / EGO_VX_SCALE
        obs[:, 1] = vy / EGO_VY_SCALE
        obs[:, 2] = yaw / EGO_YAW_SCALE
        obs[:, 3] = ax / EGO_AX_SCALE
        obs[:, 4] = ay / EGO_AY_SCALE
        obs[:, 5] = steer / max_steer
        steer_rate = (steer - prev_steer) / dt
        obs[:, 6] = steer_rate / torch.clamp(max_steer_rate, min=1e-6)
        # THROTTLE / BRAKE state from the physics state's separate channels (idx 7/8),
        # injected so the builder is independent of how they were produced.
        obs[:, 7] = throttle
        obs[:, 8] = brake

        # --- previous-action echo [9..11] ---
        obs[:, 9] = torch.clamp(prev_action[:, 0], -1.0, 1.0)
        obs[:, 10] = 0.5 * (torch.clamp(prev_action[:, 1], -1.0, 1.0) + 1.0)
        obs[:, 11] = 0.5 * (torch.clamp(prev_action[:, 2], -1.0, 1.0) + 1.0)

        # --- road boundary [12..43] (CircleTrack.lookahead_centerline, counter-clockwise) ---
        cos_psi = torch.cos(psi)
        sin_psi = torch.sin(psi)
        angle = torch.atan2(y, x)
        half_width = 0.5 * track_width
        for k in range(ROAD_LOOKAHEAD_COUNT):
            distance = ROAD_LOOKAHEAD_SPACING * float(k + 1)
            point_angle = angle + distance / track_radius
            tangent_heading = point_angle + (torch.pi / 2.0)
            cpx = track_radius * torch.cos(point_angle)
            cpy = track_radius * torch.sin(point_angle)
            nlx = -torch.sin(tangent_heading)
            nly = torch.cos(tangent_heading)
            lpx = cpx + nlx * half_width
            lpy = cpy + nly * half_width
            rpx = cpx - nlx * half_width
            rpy = cpy - nly * half_width
            ldx = lpx - x; ldy = lpy - y
            rdx = rpx - x; rdy = rpy - y
            lbx = cos_psi * ldx + sin_psi * ldy
            lby = -sin_psi * ldx + cos_psi * ldy
            rbx = cos_psi * rdx + sin_psi * rdy
            rby = -sin_psi * rdx + cos_psi * rdy
            obs[:, 12 + 2 * k] = lbx / ROAD_X_SCALE
            obs[:, 12 + 2 * k + 1] = lby / ROAD_Y_SCALE
            obs[:, 28 + 2 * k] = rbx / ROAD_X_SCALE
            obs[:, 28 + 2 * k + 1] = rby / ROAD_Y_SCALE

        # --- obstacle slot 0 [44..50] (slots 1-3 stay zero) ---
        obs_enabled = scenario["obs_enabled"]
        ox = scenario["obs_x"]; oy = scenario["obs_y"]
        ohw = scenario["obs_half_width"]
        reveal_step = scenario["obs_reveal_step"]
        reveal_dist = scenario["obs_reveal_dist"]
        reveal_dist_set = scenario["obs_reveal_dist_set"]

        odx = ox - x
        ody = oy - y
        obx = cos_psi * odx + sin_psi * ody
        oby = -sin_psi * odx + cos_psi * ody
        visible = (
            obs_enabled
            & (step >= reveal_step)
            & (~reveal_dist_set | (obx <= reveal_dist))
        )
        rel_vx = -vx + yaw * oby
        rel_vy = -vy - yaw * obx
        present = visible.to(dt_)
        obs[:, 44] = present
        obs[:, 45] = torch.where(visible, obx / OBS_X_SCALE, torch.zeros_like(obx))
        obs[:, 46] = torch.where(visible, oby / OBS_Y_SCALE, torch.zeros_like(oby))
        obs[:, 47] = torch.where(visible, rel_vx / OBS_RELVX_SCALE, torch.zeros_like(rel_vx))
        obs[:, 48] = torch.where(visible, rel_vy / OBS_RELVY_SCALE, torch.zeros_like(rel_vy))
        obs[:, 49] = torch.where(visible, ohw / OBS_HALF_W_SCALE, torch.zeros_like(ohw))
        obs[:, 50] = torch.where(visible, ohw / OBS_HALF_L_SCALE, torch.zeros_like(ohw))
        return obs

    # ============================================================= controlled-drift flag
    def _rear_saturated(self, state: torch.Tensor) -> torch.Tensor:
        """Rear-saturation criterion on the PHYSICS state.

        The faithful physics carries the rear tyre's actual lagged slip angle
        (``alpha_r_lag``, idx 14) — the rear slip the EXACT-TMeasy force is evaluated at.
        We use it DIRECTLY as the rear-saturation signal (|alpha_rear| >= 0.10 rad), the
        same criterion gpu_env applies to its single-track alpha_rear proxy, but here read
        off the model's real rear slip state instead of a learned head.
        """
        alpha_rear = state[:, IDX["alpha_r_lag"]]
        return alpha_rear.abs() >= REAR_SLIP_ANGLE_THRESHOLD_RAD

    def _controlled_drift(self, state: torch.Tensor) -> torch.Tensor:
        """controlled_drift = finite & |beta|>=0.10 & rear_saturated & 2<=vx<=28 & |yaw|<=2.7."""
        vx = state[:, 3]; vy = state[:, 4]; yaw = state[:, 5]
        finite = torch.isfinite(state).all(dim=1)
        absvx = vx.abs().clamp_min(1e-6)
        beta = torch.atan2(vy, absvx)
        high_beta = beta.abs() >= BETA_THRESHOLD_RAD
        rear_sat = self._rear_saturated(state)
        in_band = (vx >= MIN_SPEED_MPS) & (vx <= MAX_SPEED_MPS) & (yaw.abs() <= YAW_RATE_LIMIT_RAD_S)
        return finite & high_beta & rear_sat & in_band

    # =============================================================================== step
    def step(self, action: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, dict]:
        """Advance the batch one control step. Returns (obs72, reward, terminated, truncated, info)."""
        if not self._allocated:
            raise RuntimeError("call reset() before step()")
        action = action.to(device=self.device, dtype=self.dtype)
        n = self.N
        dt0 = self.dt  # [N]
        dt_scalar = self._dt_scalar

        prev_state = self.state
        prev_vx = prev_state[:, 3]
        prev_vy = prev_state[:, 4]
        prev_steer = prev_state[:, IDX["steer"]]

        # --- dynamics (FAITHFUL PHYSICS: gpu_physics_pwr.physics_step) ---
        with torch.no_grad():
            nxt, new_gear, _diag = physics_step(prev_state, action, self.gear, self.P, dt_scalar)
        self.state = nxt
        self.gear = new_gear
        vx = nxt[:, 3]; vy = nxt[:, 4]; yaw = nxt[:, 5]
        psi = nxt[:, 2]; x = nxt[:, 0]; y = nxt[:, 1]

        self.step_count = self.step_count + 1

        # --- ax/ay finite-difference (canonical obs72 contract) ---
        ax = (vx - prev_vx) / dt0
        ay = (vy - prev_vy) / dt0

        # --- obstacle clearance / collision (env.py _update_obstacle_status) ---
        clearance = torch.hypot(self.obs_x - x, self.obs_y - y)
        collision_radius = self.obs_ego_half_width + self.obs_half_width
        clearance = torch.where(self.obs_enabled, clearance, torch.full_like(clearance, float("inf")))
        self.min_clearance = torch.minimum(self.min_clearance, clearance)
        collision_now = self.obs_enabled & (clearance <= collision_radius)
        self.collision_any = self.collision_any | collision_now

        # --- track frame: lateral error / heading (CircleTrack.frame) ---
        distance = torch.hypot(x, y).clamp_min(1e-6)
        lateral_error = distance - self.track_radius
        overshoot = (lateral_error.abs() - self.track_width).clamp_min(0.0)
        offtrack_now = overshoot > 0.0
        self.offtrack_any = self.offtrack_any | offtrack_now

        speed = torch.hypot(vx, vy)
        non_finite = ~torch.isfinite(self.state).all(dim=1)
        spin = yaw.abs() > YAW_HARD_LIMIT
        speed_lo = speed < SPEED_MIN
        speed_hi = speed > SPEED_MAX

        is_avoid = self.scenario_type == SCENARIO_AVOIDANCE
        is_drift = ~is_avoid

        # termination: avoidance terminates on failure; drift runs to max_steps.
        term_failure = non_finite | offtrack_now | collision_now | speed_lo | speed_hi | spin
        terminated = torch.where(is_avoid, term_failure, torch.zeros_like(term_failure))

        # obstacle pass truncation (finish_on_pass and obstacle_longitudinal <= -finish_pass_distance)
        cos_psi = torch.cos(psi); sin_psi = torch.sin(psi)
        ang = torch.atan2(y, x)
        th = ang + torch.pi / 2.0
        tang_x = torch.cos(th); tang_y = torch.sin(th)
        obstacle_long = (self.obs_x - x) * tang_x + (self.obs_y - y) * tang_y
        obstacle_long = torch.where(self.obs_enabled, obstacle_long, torch.full_like(obstacle_long, float("inf")))
        obstacle_passed = self.obs_enabled & self.obs_finish_on_pass & (obstacle_long <= -self.obs_finish_pass_distance)
        obstacle_completed = obstacle_passed & ~terminated
        self.passed_any = self.passed_any | obstacle_completed
        at_max = self.step_count >= self.max_steps
        truncated = obstacle_completed | at_max

        # --- controlled drift flag + streak ---
        controlled = self._controlled_drift(self.state)
        self.current_controlled = torch.where(
            controlled, self.current_controlled + 1, torch.zeros_like(self.current_controlled))
        self.longest_controlled = torch.maximum(self.longest_controlled, self.current_controlled)
        drift_success_inc = (self.longest_controlled == MIN_SUSTAIN_STEPS) & (self.current_controlled == MIN_SUSTAIN_STEPS)

        # --- reward (trainer-computed, per step; identical to gpu_env) ---
        margin = self.min_clearance - collision_radius
        margin_finite = self.obs_enabled & torch.isfinite(margin)
        clipped_margin = torch.clamp(margin, -1.0, 1.0)
        vx_norm = (prev_vx / EGO_VX_SCALE).abs()

        completion_done = terminated | truncated
        cleared = at_max | obstacle_completed
        avoid_reward = (
            -COLLISION_PENALTY * collision_now.to(self.dtype)
            - OFFTRACK_PENALTY * offtrack_now.to(self.dtype)
            + CLEARANCE_SHAPING * torch.where(margin_finite, clipped_margin, torch.zeros_like(clipped_margin))
        )
        graze = margin_finite & (margin >= 0.0) & (margin < GRAZE_MARGIN_M) & (vx_norm >= GRAZE_SPEED_NORM)
        avoid_reward = avoid_reward - GRAZE_PENALTY * graze.to(self.dtype)
        pass_bonus = completion_done & ~collision_now & ~offtrack_now & cleared
        avoid_reward = avoid_reward + AVOIDANCE_PASS_REWARD * pass_bonus.to(self.dtype)

        drift_reward = (
            -COLLISION_PENALTY * collision_now.to(self.dtype)
            + DRIFT_PROGRESS_SHAPING * controlled.to(self.dtype) * torch.clamp(self.current_controlled, min=1).to(self.dtype)
            + DRIFT_SUCCESS_REWARD * drift_success_inc.to(self.dtype)
        )
        reward = torch.where(is_avoid, avoid_reward, drift_reward)

        # --- update prev_* and done ---
        self.prev_vx = vx.detach().clone()
        self.prev_vy = vy.detach().clone()
        self.prev_steer = nxt[:, IDX["steer"]].detach().clone()
        self.prev_action = torch.clamp(action, -1.0, 1.0)
        self.done = self.done | terminated | truncated

        obs = self.obs72_from_state(
            self.state, self._static_view(), prev_steer, self.prev_action,
            self.step_count, ax=ax, ay=ay,
            throttle=self.state[:, IDX["throttle"]], brake=self.state[:, IDX["brake"]],
        )

        info = {
            "collision": collision_now,
            "collision_any": self.collision_any,
            "offtrack": offtrack_now,
            "offtrack_any": self.offtrack_any,
            "controlled_drift": controlled,
            "current_controlled": self.current_controlled.clone(),
            "longest_controlled": self.longest_controlled.clone(),
            "drift_success_inc": drift_success_inc,
            "min_clearance_margin": margin,
            "obstacle_long": obstacle_long,
            "obstacle_completed": obstacle_completed,
            "at_max_steps": at_max,
            "non_finite": non_finite,
            "lateral_error": lateral_error,
            "speed": speed,
            "ax": ax,
            "ay": ay,
            "scenario_type": self.scenario_type,
        }
        return obs, reward, terminated, truncated, info

    # --------------------------------------------------------------------- success
    def success(self) -> torch.Tensor:
        """Per-env success: drift longest>=24; avoidance not-collision & not-offtrack & cleared."""
        drift_succ = self.longest_controlled >= MIN_SUSTAIN_STEPS
        avoid_cleared = (self.step_count >= self.max_steps) | self.passed_any
        avoid_succ = (~self.collision_any) & (~self.offtrack_any) & avoid_cleared
        is_avoid = self.scenario_type == SCENARIO_AVOIDANCE
        return torch.where(is_avoid, avoid_succ, drift_succ)
