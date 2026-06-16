"""GPU-batched, torch-vectorised AutoDrift environment on the grey-box surrogate.

This is the large-batch PPO backbone: thousands of AutoDrift environments stepped
in parallel on one GPU. The *dynamics* are the grey-box surrogate
(``autodrift.gpu_surrogate.grey_box_step`` — analytic single-track + learned
residual, with ``residual_mlp_phaseB.pt``); the *observation / reward / termination*
contract is a byte-faithful, fully-batched reimplementation of the analytic
``autodrift.env.AutoDriftEnv`` obs72 frame (cross-checked against the CPU env by
``tests/test_gpu_env.py`` via state injection) and the F2 trainer's reward / success
/ termination logic (``scripts/feasibility_audit/phase4_f2_train.py``).

Why a separate file (env.py / gpu_surrogate.py / gpu_physics.py / phase4_f2_train.py
are read-only here): this module composes those frozen pieces into a batched env.

------------------------------------------------------------------- obs72 layout
The 72-d actor frame this builds (verified against
``high_fidelity_interface.py:290-327`` and ``env.py:1212-1237/1022-1079``):

  [0]  vx/20          [1]  vy/12        [2] yaw_rate/2.5
  [3]  ax/15          [4]  ay/15        (ax=(vx-prev_vx)/dt, ay=(vy-prev_vy)/dt)
  [5]  steer/max_steer
  [6]  steer_rate/max_steer_rate        (steer_rate=(steer-prev_steer)/dt)
  [7]  throttle_state (drive_force>=0 -> drive_force/max_drive_force)
  [8]  brake_state    (drive_force<0  -> -drive_force/max_brake_force)
  [9]  prev_steer_cmd = clip(prev_action[0], -1, 1)
  [10] prev_throttle  = 0.5*(prev_action[1]+1)
  [11] prev_brake     = 0.5*(prev_action[2]+1)
  [12..27] LEFT  road-edge 8 pts (x/80, y/20), body frame
  [28..43] RIGHT road-edge 8 pts (x/80, y/20), body frame
  [44..71] 4 obstacle slots x 7 = [present, x/80, y/20, relvx/20, relvy/12,
                                   half_width/5, half_length/5]; only slot 0 filled.

The road edges are the body-frame centerline lookahead at long distances
5,10,...,40 m, +/- half_width along the left normal, computed closed-form from a
CIRCLE track of radius ``track_radius`` (``tasks.CircleTrack.lookahead_centerline``,
counter-clockwise). Obstacle slot 0 is ``present`` iff
``step >= reveal_step AND (reveal_dist is None OR obstacle_long_body <= reveal_dist)``
where ``obstacle_long_body`` is the obstacle's body-frame x. Relative velocity mode
"ego": ``relvx = -vx + yaw*y_body``, ``relvy = -vy - yaw*x_body`` (static obstacle).

NOTE on ax/ay: the canonical obs72 contract (chrono backend + this env) defines
``ax/ay`` by the finite-difference ``(v - prev_v)/dt`` of the body velocities. The
analytic ``env.py`` instead emits a *force-based* body acceleration in those two
channels; that is the ONLY obs72 dim where env.py and this env disagree by
construction. ``obs72_from_state`` therefore takes ``ax``/``ay`` as injected
scalars so the parity test can feed env.py's exact values and isolate the builder;
``step`` computes them by finite difference per the canonical contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import torch

from autodrift.gpu_surrogate import (
    ParamBatch,
    ResidualDynamicsMLP,
    grey_box_step,
    make_param_batch,
)

OBS_DIM = 72
ACT_DIM = 3
STATE_DIM = 8  # [x, y, psi, vx, vy, yaw_rate, steer, drive_force]
ROAD_LOOKAHEAD_COUNT = 8
ROAD_LOOKAHEAD_SPACING = 5.0
OBSTACLE_SLOTS = 4

# obs72 normalisers (env.py ObservationScaleConfig defaults; the canonical frame).
EGO_VX_SCALE = 20.0
EGO_VY_SCALE = 12.0
EGO_YAW_SCALE = 2.5
EGO_AX_SCALE = 15.0
EGO_AY_SCALE = 15.0
ROAD_X_SCALE = 80.0
ROAD_Y_SCALE = 20.0
OBS_X_SCALE = 80.0
OBS_Y_SCALE = 20.0
OBS_RELVX_SCALE = 20.0
OBS_RELVY_SCALE = 12.0
OBS_HALF_W_SCALE = 5.0
OBS_HALF_L_SCALE = 5.0

# --- F2 trainer reward / threshold constants (phase4_e4 + phase4_f2_train) ---
COLLISION_PENALTY = 60.0
OFFTRACK_PENALTY = 45.0
AVOIDANCE_PASS_REWARD = 40.0
DRIFT_SUCCESS_REWARD = 40.0
CLEARANCE_SHAPING = 0.1
DRIFT_PROGRESS_SHAPING = 0.5
GRAZE_SPEED_NORM = 0.45
GRAZE_MARGIN_M = 0.20
GRAZE_PENALTY = 12.0
PPO_GAMMA = 0.99
PPO_LAMBDA = 0.95

# drift controlled-drift thresholds (phase4_e4_drift_regime_pricing)
BETA_THRESHOLD_RAD = 0.10
REAR_SLIP_ANGLE_THRESHOLD_RAD = 0.10
YAW_RATE_LIMIT_RAD_S = 2.7
MIN_SPEED_MPS = 2.0
MAX_SPEED_MPS = 28.0
MIN_SUSTAIN_STEPS = 24

# termination contract (env.py / chrono backend)
COLLISION_CLEARANCE = 2.15  # ego_half_width(0.90) + obstacle.half_width(1.25)
SPEED_MIN = 1.0
SPEED_MAX = 32.0
YAW_HARD_LIMIT = 6.0
EGO_HALF_WIDTH = 0.90
OBSTACLE_HALF_WIDTH = 1.25

# scenario_type codes
SCENARIO_DRIFT = 0
SCENARIO_AVOIDANCE = 1

_DEFAULT_RESIDUAL = "runs/feasibility_audit/phase4_f2/residual_mlp_phaseB.pt"
_DEFAULT_REARSAT = "runs/feasibility_audit/phase4_f2/rear_sat_head.pt"

# default vehicle params not present in scenario["params"] (VehicleParams defaults).
_DRAG_COEFF = 0.34
_ROLLING_RESISTANCE = 75.0
_GRAVITY = 9.81

_PARAM_FROM_SCENARIO = (
    "mass", "iz", "lf", "lr", "mu", "cf", "cr", "max_steer", "max_steer_rate",
    "max_drive_force", "max_brake_force", "drive_tau", "steer_tau",
)


class RearSaturationHead(torch.nn.Module):
    """Learned rear-saturation head (mirror of surrogate_saturation_head.RearSaturationHead).

    Feature vector (8): [vx, vy, yaw, beta, alpha_rear, steer_state,
    drive_state/1e4, |alpha_rear|]. Returns the logit; saturation = logit > 0.
    """

    def __init__(self, in_dim: int = 8, hidden: int = 64):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(in_dim, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, hidden), torch.nn.SiLU(), torch.nn.Linear(hidden, 1))
        self.register_buffer("mean", torch.zeros(in_dim))
        self.register_buffer("std", torch.ones(in_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net((x - self.mean) / self.std).squeeze(-1)


def _wrap_pi(a: torch.Tensor) -> torch.Tensor:
    return (a + torch.pi) % (2.0 * torch.pi) - torch.pi


class GPUAutoDriftEnv:
    """Batched AutoDrift env: N parallel environments stepped on the GPU.

    Holds per-env tensors. ``reset`` materialises the batch from a list of scenario
    dicts (the canonical ``scenario_from_env`` format); ``step`` advances the
    grey-box surrogate and emits (obs72, reward, terminated, truncated, info).
    ``obs72_from_state`` is the pure, dynamics-free obs72 builder used by the parity
    test (state injection).

    Drift scenarios (``scenario_type == "drift"``) set ``terminate_on_failure=False``
    -> off-track / spin / speed never halt the episode; it runs to ``max_steps``
    (the canonical drift contract). Avoidance scenarios terminate on failure.
    """

    def __init__(
        self,
        *,
        device: torch.device | str = "cuda",
        dtype: torch.dtype = torch.float32,
        residual_mlp_path: str | Path | None = None,
        rear_sat_head_path: str | Path | None = None,
        repo_root: str | Path | None = None,
        use_rear_sat_head: bool = True,
    ) -> None:
        self.device = torch.device(device)
        self.dtype = dtype
        root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]

        res_path = Path(residual_mlp_path) if residual_mlp_path is not None else root / _DEFAULT_RESIDUAL
        self.residual_mlp = ResidualDynamicsMLP().to(device=self.device, dtype=dtype)
        self.residual_mlp.load_state_dict(torch.load(res_path, map_location=self.device))
        self.residual_mlp.eval()

        self.use_rear_sat_head = bool(use_rear_sat_head)
        self.rear_sat_head: RearSaturationHead | None = None
        if self.use_rear_sat_head:
            head_path = Path(rear_sat_head_path) if rear_sat_head_path is not None else root / _DEFAULT_REARSAT
            head = RearSaturationHead().to(device=self.device, dtype=dtype)
            head.load_state_dict(torch.load(head_path, map_location=self.device))
            head.eval()
            self.rear_sat_head = head

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

        # --- per-env static scenario tensors ---
        self.scenario_type = torch.zeros(n, dtype=torch.long, device=dev)
        self.track_radius = self._z(n)
        self.track_width = self._z(n)
        self.max_steps = torch.zeros(n, dtype=torch.long, device=dev)
        self.dt = self._z(n)

        params: dict[str, list[float]] = {k: [] for k in _PARAM_FROM_SCENARIO}
        params["drag_coeff"] = []
        params["rolling_resistance"] = []
        params["gravity"] = []

        # obstacle static
        self.obs_enabled = torch.zeros(n, dtype=torch.bool, device=dev)
        self.obs_x = self._z(n)
        self.obs_y = self._z(n)
        self.obs_half_width = self._z(n)
        self.obs_ego_half_width = torch.full((n,), EGO_HALF_WIDTH, device=dev, dtype=dt)
        self.obs_reveal_step = torch.zeros(n, dtype=torch.long, device=dev)
        self.obs_reveal_dist = self._z(n)               # value only meaningful where mask set
        self.obs_reveal_dist_set = torch.zeros(n, dtype=torch.bool, device=dev)
        self.obs_finish_on_pass = torch.zeros(n, dtype=torch.bool, device=dev)
        self.obs_finish_pass_distance = self._z(n)

        init = torch.zeros(n, STATE_DIM, device=dev, dtype=dt)
        priv6 = torch.zeros(n, 6, device=dev, dtype=dt)

        for i, sc in enumerate(scenarios):
            stype = str(sc.get("scenario_type", "drift")).lower()
            self.scenario_type[i] = SCENARIO_AVOIDANCE if stype.startswith("avoid") else SCENARIO_DRIFT
            self.track_radius[i] = float(sc["track_radius"])
            self.track_width[i] = float(sc["track_width"])
            self.max_steps[i] = int(sc["max_steps"])
            self.dt[i] = float(sc.get("dt", 0.02))
            p = sc["params"]
            for k in _PARAM_FROM_SCENARIO:
                params[k].append(float(p[k]))
            params["drag_coeff"].append(float(p.get("drag_coeff", _DRAG_COEFF)))
            params["rolling_resistance"].append(float(p.get("rolling_resistance", _ROLLING_RESISTANCE)))
            params["gravity"].append(float(p.get("gravity", _GRAVITY)))

            istate = sc["initial_state"]
            init[i, 0] = float(istate["x"])
            init[i, 1] = float(istate["y"])
            init[i, 2] = float(istate["psi"])
            init[i, 3] = float(istate["vx"])
            init[i, 4] = float(istate["vy"])
            init[i, 5] = float(istate["yaw_rate"])
            init[i, 6] = float(istate.get("steer", 0.0))
            init[i, 7] = float(istate.get("drive_force", 0.0))

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
        pdict = {k: torch.tensor(v, device=dev, dtype=dt) for k, v in params.items()}
        self.P: ParamBatch = make_param_batch(pdict, n, device=dev, dtype=dt)
        # grey_box_step takes a scalar dt; cache it host-side once (avoids a per-step
        # device->host sync). All envs in a batch must share dt (the surrogate integrates
        # one scalar dt); assert that here so a mixed-dt batch fails loudly.
        dt_vals = {round(float(sc.get("dt", 0.02)), 9) for sc in scenarios}
        if len(dt_vals) != 1:
            raise ValueError(f"all envs in a batch must share dt; got {sorted(dt_vals)}")
        self._dt_scalar = float(next(iter(dt_vals)))

        # --- per-env dynamics + counters ---
        self.state = init
        self.prev_vx = init[:, 3].clone()
        self.prev_vy = init[:, 4].clone()
        self.prev_steer = init[:, 6].clone()
        self.prev_action = torch.tensor([0.0, -1.0, -1.0], device=dev, dtype=dt).expand(n, 3).clone()

        self.step_count = torch.zeros(n, dtype=torch.long, device=dev)
        self.min_clearance = torch.full((n,), float("inf"), device=dev, dtype=dt)
        self.current_controlled = torch.zeros(n, dtype=torch.long, device=dev)
        self.longest_controlled = torch.zeros(n, dtype=torch.long, device=dev)
        self.collision_any = torch.zeros(n, dtype=torch.bool, device=dev)
        self.offtrack_any = torch.zeros(n, dtype=torch.bool, device=dev)
        self.passed_any = torch.zeros(n, dtype=torch.bool, device=dev)  # obstacle_pass completion (sticky)
        self.done = torch.zeros(n, dtype=torch.bool, device=dev)
        self._allocated = True

        # at reset, env.py's ax/ay are force-based; here the finite-difference is 0
        # (prev_v == v). The reset obs is rarely consumed for reward, but we return a
        # well-formed frame for completeness.
        ax = self._z(n)
        ay = self._z(n)
        return self.obs72_from_state(
            self.state, self._static_view(), self.prev_steer, self.prev_action,
            self.step_count, ax=ax, ay=ay,
        )

    def _static_view(self) -> dict[str, torch.Tensor]:
        return {
            "track_radius": self.track_radius,
            "track_width": self.track_width,
            "dt": self.dt,
            "max_steer": self.P["max_steer"],
            "max_steer_rate": self.P["max_steer_rate"],
            "max_drive_force": self.P["max_drive_force"],
            "max_brake_force": self.P["max_brake_force"],
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
    ) -> torch.Tensor:
        """Pure, batched obs72 builder. No dynamics; everything is state-injected.

        state[N,8] = [x, y, psi, vx, vy, yaw_rate, steer_state, drive_force]
        scenario: dict of [N] static tensors (see ``_static_view``).
        prev_steer[N], prev_action[N,3], step[N] (int).
        ax[N], ay[N]: body accelerations to place in obs[3]/obs[4] (injected so the
            builder is independent of how ax/ay were produced).
        Returns obs72[N,72].
        """
        dev = state.device
        dt_ = state.dtype
        n = state.shape[0]
        x = state[:, 0]; y = state[:, 1]; psi = state[:, 2]
        vx = state[:, 3]; vy = state[:, 4]; yaw = state[:, 5]
        steer = state[:, 6]; drive_force = state[:, 7]

        track_radius = scenario["track_radius"]
        track_width = scenario["track_width"]
        dt = scenario["dt"]
        max_steer = scenario["max_steer"]
        max_steer_rate = scenario["max_steer_rate"]
        max_drive = scenario["max_drive_force"]
        max_brake = scenario["max_brake_force"]

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
        # throttle / brake state from the signed drive-force state
        throttle_state = torch.where(
            drive_force >= 0.0, drive_force / torch.clamp(max_drive, min=1e-6), torch.zeros_like(drive_force))
        brake_state = torch.where(
            drive_force < 0.0, -drive_force / torch.clamp(max_brake, min=1e-6), torch.zeros_like(drive_force))
        obs[:, 7] = throttle_state
        obs[:, 8] = brake_state

        # --- previous-action echo [9..11] ---
        obs[:, 9] = torch.clamp(prev_action[:, 0], -1.0, 1.0)
        obs[:, 10] = 0.5 * (torch.clamp(prev_action[:, 1], -1.0, 1.0) + 1.0)
        obs[:, 11] = 0.5 * (torch.clamp(prev_action[:, 2], -1.0, 1.0) + 1.0)

        # --- road boundary [12..43] ---
        # CircleTrack.lookahead_centerline (counter-clockwise, sign=+1):
        #   angle = atan2(y, x); point_angle = angle + dist/R;
        #   tangent_heading = point_angle + pi/2; centerpoint = R*(cos,sin)(point_angle);
        #   left  = center + half_width*normal_left;  right = center - half_width*normal_left
        # then body frame about (x, y, psi).
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
            nlx = -torch.sin(tangent_heading)   # normal_left = (-tangent_y, tangent_x)
            nly = torch.cos(tangent_heading)
            # left point in world
            lpx = cpx + nlx * half_width
            lpy = cpy + nly * half_width
            rpx = cpx - nlx * half_width
            rpy = cpy - nly * half_width
            # body frame: rotate (p - ego) by -psi
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
        obx = cos_psi * odx + sin_psi * ody     # obstacle body-frame x (longitudinal)
        oby = -sin_psi * odx + cos_psi * ody
        visible = (
            obs_enabled
            & (step >= reveal_step)
            & (~reveal_dist_set | (obx <= reveal_dist))
        )
        # relative velocity, ego mode (static obstacle): relvx=-vx+yaw*by, relvy=-vy-yaw*bx
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
        """Batched rear-saturation: learned head if available, else |alpha_rear|>=0.10 proxy."""
        vx = state[:, 3]; vy = state[:, 4]; yaw = state[:, 5]
        steer = state[:, 6]; drive = state[:, 7]
        lr = self.P["lr"]
        absvx = vx.abs().clamp_min(1e-6)
        beta = torch.atan2(vy, absvx)
        alpha_rear = torch.atan2(vy - lr * yaw, absvx)
        if self.rear_sat_head is not None:
            feat = torch.stack(
                [vx, vy, yaw, beta, alpha_rear, steer, drive / 1e4, alpha_rear.abs()], dim=1)
            with torch.no_grad():
                return self.rear_sat_head(feat) > 0.0
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
        dt_scalar = self._dt_scalar  # grey_box_step takes a scalar dt (cached host-side)

        prev_state = self.state
        prev_vx = prev_state[:, 3]
        prev_vy = prev_state[:, 4]
        prev_steer = prev_state[:, 6]

        # --- dynamics (grey-box surrogate) ---
        with torch.no_grad():
            nxt, _forces = grey_box_step(prev_state, action, self.P, dt_scalar, self.residual_mlp)
        self.state = nxt
        vx = nxt[:, 3]; vy = nxt[:, 4]; yaw = nxt[:, 5]
        psi = nxt[:, 2]; x = nxt[:, 0]; y = nxt[:, 1]

        self.step_count = self.step_count + 1

        # --- ax/ay finite-difference (canonical obs72 contract) ---
        ax = (vx - prev_vx) / dt0
        ay = (vy - prev_vy) / dt0

        # --- obstacle clearance / collision (env.py _update_obstacle_status) ---
        clearance = torch.hypot(self.obs_x - x, self.obs_y - y)
        collision_radius = self.obs_ego_half_width + self.obs_half_width
        # only meaningful where obstacle enabled
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

        # termination reason gating (env.py _termination_reason order):
        # non_finite > off_track > collision > speed_lo > speed_hi > spin.
        term_failure = non_finite | offtrack_now | collision_now | speed_lo | speed_hi | spin
        # DRIFT: terminate_on_failure=False -> only non_finite halts? In env.py the drift
        # scenario sets terminate_on_failure=False and the chrono backend converts a
        # termination into a non-terminating "first_failure_event" -> drift episodes run
        # to max_steps (only obs/flags update). We mirror that: drift never terminates on
        # failure; it truncates at max_steps. (non_finite still produces non-finite obs but
        # does not set terminated, matching the backend's terminate_on_failure=False path.)
        terminated = torch.where(is_avoid, term_failure, torch.zeros_like(term_failure))

        # obstacle pass truncation (finish_on_pass and obstacle_longitudinal <= -finish_pass_distance)
        cos_psi = torch.cos(psi); sin_psi = torch.sin(psi)
        # frame tangent for a circle: tangent_heading = atan2(y,x)+pi/2
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
        # eval target is fixed 24; the F2 trainer RAMPS this 6->24 over training (_DRIFT_SUSTAIN_TARGET)
        # for the BC->PPO curriculum. A4 should expose a settable sustain target for training-curriculum
        # parity (eval stays 24). Also: drift envs that go non_finite keep stepping here (terminate_on_
        # failure=False); A4 should mask/freeze non-finite envs so NaN doesn't poison the PPO batch.
        drift_success_inc = (self.longest_controlled == MIN_SUSTAIN_STEPS) & (self.current_controlled == MIN_SUSTAIN_STEPS)

        # --- reward (trainer-computed, per step) ---
        margin = self.min_clearance - collision_radius  # env.py min_clearance_margin
        margin_finite = self.obs_enabled & torch.isfinite(margin)
        clipped_margin = torch.clamp(margin, -1.0, 1.0)
        vx_norm = (prev_vx / EGO_VX_SCALE).abs()

        # avoidance reward
        completion_done = terminated | truncated
        cleared = at_max | obstacle_completed  # completion in {max_steps, obstacle_pass}
        avoid_reward = (
            -COLLISION_PENALTY * collision_now.to(self.dtype)
            - OFFTRACK_PENALTY * offtrack_now.to(self.dtype)
            + CLEARANCE_SHAPING * torch.where(margin_finite, clipped_margin, torch.zeros_like(clipped_margin))
        )
        graze = margin_finite & (margin >= 0.0) & (margin < GRAZE_MARGIN_M) & (vx_norm >= GRAZE_SPEED_NORM)
        avoid_reward = avoid_reward - GRAZE_PENALTY * graze.to(self.dtype)
        pass_bonus = completion_done & ~collision_now & ~offtrack_now & cleared
        avoid_reward = avoid_reward + AVOIDANCE_PASS_REWARD * pass_bonus.to(self.dtype)

        # drift reward
        drift_reward = (
            -COLLISION_PENALTY * collision_now.to(self.dtype)
            + DRIFT_PROGRESS_SHAPING * controlled.to(self.dtype) * torch.clamp(self.current_controlled, min=1).to(self.dtype)
            + DRIFT_SUCCESS_REWARD * drift_success_inc.to(self.dtype)
        )
        reward = torch.where(is_avoid, avoid_reward, drift_reward)

        # --- update prev_* and done ---
        self.prev_vx = vx.detach().clone()
        self.prev_vy = vy.detach().clone()
        self.prev_steer = nxt[:, 6].detach().clone()
        self.prev_action = torch.clamp(action, -1.0, 1.0)
        self.done = self.done | terminated | truncated

        obs = self.obs72_from_state(
            self.state, self._static_view(), prev_steer, self.prev_action,
            self.step_count, ax=ax, ay=ay,
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
        # completion in {max_steps, obstacle_pass}: passed_any is the sticky obstacle-pass flag
        avoid_cleared = (self.step_count >= self.max_steps) | self.passed_any
        avoid_succ = (~self.collision_any) & (~self.offtrack_any) & avoid_cleared
        is_avoid = self.scenario_type == SCENARIO_AVOIDANCE
        return torch.where(is_avoid, avoid_succ, drift_succ)
