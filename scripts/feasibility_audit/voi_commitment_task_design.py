"""Task-B: design a COMMITMENT task family with measurably positive success-VoI.

Motivation: Task A (voi_current_task_family.py) measured VoI_success = 0 on all
24 skeletons of the current task family -- knowing the hidden friction mu never
changes which plan succeeds. Structural reason (proved here as the
"dominance theorem", see docs/selfid-commitment-task-voi-design-2026-06.md):
when (a) success is monotone in mu for every fixed plan, (b) any mu_low-safe
speed profile is mu-agnostically trackable (speed is observable), and (c) the
success criterion has no mu-dependent threshold, the most-cautious feasible
plan succeeds wherever any plan succeeds, so VoI_success = 0 identically.

This script breaks assumption (c) with an ANTICIPATORY ENTRY-SPEED COMMITMENT
family ("human driver chooses corner-entry speed on an unknown-grip road"):

  - preparation segment: quasi-straight approach (large-radius circle track),
    fixed initial speed v0 (friction_limited_speed=false so the start does NOT
    leak mu); mu is inferable only from one's own command->response history.
  - late hazard reveal: obstacle becomes visible only within
    perception_reveal_distance (env-native knob), too late to change the
    arrival speed on low grip.
  - hard deadline: max_steps + finish_on_pass make "pass the obstacle in time"
    the success event; arriving slow is SAFE but (on far-hazard episodes) too
    slow to finish -> the reward/feasibility tension that makes mu worth
    knowing BEFORE the reveal.
  - scenario family: hazard distance grows with mu (mu-correlated mixture of
    env configs; each member is expressed exactly through
    autodrift.config.build_env_config). A purely independent-geometry variant
    is also measured to certify the ceiling of what a SINGLE env config can
    express (documented as the needed new env feature).

VoI definition (same as Task A): for the scenario family,
    VoI = E_theta[per-theta best plan outcome] - max_plan E_theta[outcome]
with theta = episode-constant hidden mu, outcomes measured by closed-loop
rollouts of mu-agnostic observation-only plans (entry-speed commitment +
scripted/reactive avoidance), success = outcome_bucket == success_obstacle_pass
(autodrift.evaluate.outcome_bucket_from_info, the shared measurement
semantics). Split-seed validation (plan selection on even seeds, evaluation on
odd seeds) removes the max-selection optimism of the empirical oracle.

Inferability lower bound: during the preparation segment, plans inject
throttle/brake/steer PROBE PULSES; a linear (ridge) probe maps the
observation-channel response history (per-frame indices 0-11, same channels as
the selfid_task_health_check Phase-D probe) to mu, with episode-level
train/val/test splits. Contrast conditions: no-probe steady tracking and
bounded random actions.

Hard constraints respected: pure CPU numpy, no policy training, deterministic
seeds, new files only (experiments/feasibility_audit, runs/feasibility_audit,
docs).

Run:
    PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_task_design.py
    PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_task_design.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_task_design.py --stage smoke
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import utc_timestamp, write_csv_rows
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import outcome_bucket_from_info
from autodrift.scenarios import classify_obstacle_scenario

REPO = Path(__file__).resolve().parents[2]
RESULTS_JSON = REPO / "experiments/feasibility_audit/voi_commitment_task_design.json"
RUN_DIR = REPO / "runs/feasibility_audit/voi_commitment_task_design"

DT = 0.02
V0 = 8.0  # fixed initial speed for every theta (no mu leak at reset)
EGO_HALF = 0.90
SAFETY_MARGIN = 0.30
WHEELBASE = 2.80
MAX_STEER_RAD = 0.62
SEED_BASE = 20260612

# observation layout for the configs built here (history_length=1,
# action_history_mode=full, wheel none, 8 road lookahead points, 4 obstacle
# slots, no privileged block) -- asserted at runtime via env.base_obs_dim.
OBS_DIM = 72
IDX_VX, IDX_YAW_RATE = 0, 2
IDX_OBST_PRESENT, IDX_OBST_BX, IDX_OBST_BY = 44, 45, 46
ROAD_LEFT_START, ROAD_RIGHT_START = 12, 28

CLAIM_BOUNDARY = (
    "Feasibility-audit task-DESIGN measurement only: scripted mu-agnostic commitment plans and a "
    "per-theta empirical oracle are rolled out on candidate scenario families to measure "
    "VoI(success) and probe inferability. No driver-performance verdict, repair-success, "
    "robustness-result, validation, ranking, winner selection, checkpoint mutation/promotion, "
    "high-fidelity, paper, or self-ID *capability* claim is made."
)


# --------------------------------------------------------------------- design


@dataclass(frozen=True)
class LevelSpec:
    """One theta level of a scenario family (a build_env_config-expressible member)."""

    mu: float
    d_lo: float
    d_hi: float
    entry_speed: float  # design-intended oracle entry speed for this level


@dataclass(frozen=True)
class DesignSpec:
    design_id: str
    kind: str  # "mu_correlated" | "independent"
    track_radius: float
    track_width: float
    reveal_distance: float
    max_steps: int
    obstacle_half_width: float
    pass_reward: float
    collision_penalty: float
    levels: tuple[LevelSpec, ...]
    notes: str = ""

    @property
    def deadline_s(self) -> float:
        return self.max_steps * DT

    def required_offset(self) -> float:
        return EGO_HALF + self.obstacle_half_width + SAFETY_MARGIN


def centerline_compensation(track_radius: float, d: float) -> float:
    """Lateral offset (toward circle center = normal_left) that puts an obstacle
    placed at tangent distance d back onto the track centerline."""
    return float(track_radius - math.sqrt(max(track_radius**2 - d**2, 1.0)))


def level_env_config(design: DesignSpec, level: LevelSpec) -> dict[str, Any]:
    d_mid = 0.5 * (level.d_lo + level.d_hi)
    return {
        "dt": DT,
        "max_steps": design.max_steps,
        "track_kind": "circle",
        "track_radius": design.track_radius,
        "track_width": design.track_width,
        "speed_range": [V0, V0],
        "beta_target_range": [0.40, 0.40],
        "friction_limited_speed": False,
        "history_length": 1,
        "action_history_mode": "full",
        "wheel_observation_mode": "none",
        "include_privileged_params": False,
        "randomization": {
            "mu_range": [level.mu, level.mu],
            "mass_scale_range": [1.0, 1.0],
            "cg_shift_range": [0.0, 0.0],
            "inertia_scale_range": [1.0, 1.0],
            "tire_stiffness_scale_range": [1.0, 1.0],
            "drive_scale_range": [1.0, 1.0],
            "brake_scale_range": [1.0, 1.0],
            "actuator_tau_scale_range": [1.0, 1.0],
        },
        "obstacle": {
            "enabled": True,
            "distance_range": [level.d_lo, level.d_hi],
            "half_width_range": [design.obstacle_half_width, design.obstacle_half_width],
            "lateral_offset_range": [
                centerline_compensation(design.track_radius, d_mid),
                centerline_compensation(design.track_radius, d_mid),
            ],
            "finish_on_pass": True,
            "finish_pass_distance": 2.0,
            "pass_reward": design.pass_reward,
            "collision_penalty": design.collision_penalty,
            "perception_reveal_step": 0,
            "perception_reveal_distance": design.reveal_distance,
            "require_aeb_infeasible": False,
        },
    }


def candidate_designs() -> list[DesignSpec]:
    mus = (0.30, 0.55, 0.85, 1.15)
    entry = (5.0, 7.5, 10.0, 13.0)
    return [
        DesignSpec(
            design_id="A1_independent_geometry",
            kind="independent",
            track_radius=3000.0,
            track_width=5.0,
            reveal_distance=11.0,
            max_steps=290,
            obstacle_half_width=1.15,
            pass_reward=10.0,
            collision_penalty=20.0,
            levels=tuple(LevelSpec(mu=m, d_lo=24.0, d_hi=60.0, entry_speed=v) for m, v in zip(mus, entry)),
            notes=(
                "Single-env-config expressible variant: hazard distance independent of mu. "
                "Multiplicative oracle leak (slow oracle misses deadline on far hazards) "
                "caps achievable VoI_success (analytic sup ~0.28)."
            ),
        ),
        DesignSpec(
            design_id="A2_independent_geometry_mild_deadline",
            kind="independent",
            track_radius=3000.0,
            track_width=5.0,
            reveal_distance=11.0,
            max_steps=320,
            obstacle_half_width=1.15,
            pass_reward=10.0,
            collision_penalty=20.0,
            levels=tuple(LevelSpec(mu=m, d_lo=24.0, d_hi=48.0, entry_speed=v) for m, v in zip(mus, entry)),
            notes="Independent-geometry variant tuned toward its theoretical VoI ceiling.",
        ),
        DesignSpec(
            design_id="B1_mu_correlated_hazard",
            kind="mu_correlated",
            track_radius=900.0,
            track_width=5.0,
            reveal_distance=11.0,
            max_steps=295,
            obstacle_half_width=1.15,
            pass_reward=10.0,
            collision_penalty=20.0,
            levels=tuple(
                LevelSpec(mu=m, d_lo=d, d_hi=d, entry_speed=v)
                for m, d, v in zip(mus, (24.0, 38.0, 48.0, 60.0), entry)
            ),
            notes=(
                "mu-correlated hazard distance (low grip => near hazard, high grip => far hazard "
                "+ deadline). Mixture of per-theta env configs; needs a new env feature "
                "(mu-conditional obstacle distance sampling) to live in ONE config."
            ),
        ),
        DesignSpec(
            design_id="B2_mu_correlated_hazard_tight",
            kind="mu_correlated",
            track_radius=900.0,
            track_width=5.0,
            reveal_distance=12.0,
            max_steps=285,
            obstacle_half_width=1.25,
            pass_reward=10.0,
            collision_penalty=20.0,
            levels=tuple(
                LevelSpec(mu=m, d_lo=d, d_hi=d, entry_speed=v)
                for m, d, v in zip(mus, (24.0, 38.0, 49.0, 62.0), entry)
            ),
            notes="Tighter deadline / wider obstacle variant of B1.",
        ),
    ]


# ----------------------------------------------------------------------- plans


@dataclass(frozen=True)
class PlanSpec:
    """A mu-agnostic fixed plan: entry-speed commitment + reaction parameters."""

    name: str
    v_entry: float
    brake_to: float | None  # post-reveal brake target speed (None = no brake phase)
    swerve_offset: float = 3.0
    swerve_gain: float = 3.0
    steer_cap: float = 0.85
    ladder: bool = False  # mu-agnostic position-indexed speed ladder
    probe_pulses: bool = False
    pure_brake: bool = False  # AEB-style reaction


def plan_family(design: DesignSpec) -> list[PlanSpec]:
    plans: list[PlanSpec] = []
    # level-tuned commitment plans (these double as the per-theta oracle candidates)
    caps = (1.0, 0.95, 0.85, 0.70)
    for level, cap in zip(design.levels, caps):
        plans.append(
            PlanSpec(
                name=f"commit_v{level.entry_speed:g}",
                v_entry=level.entry_speed,
                brake_to=max(level.entry_speed - 1.0, 4.0),
                steer_cap=cap,
            )
        )
    # generic no-brake variants (swerve-only reactions)
    for v in (5.0, 7.5, 10.0, 13.0):
        plans.append(PlanSpec(name=f"swerve_only_v{v:g}", v_entry=v, brake_to=None, steer_cap=0.85))
    plans.append(PlanSpec(name="always_crawl_v4.5", v_entry=4.5, brake_to=4.0, steer_cap=1.0))
    plans.append(PlanSpec(name="always_max_v14.5", v_entry=14.5, brake_to=12.0, steer_cap=0.65))
    plans.append(PlanSpec(name="ladder_adaptive", v_entry=design.levels[0].entry_speed, brake_to=None, ladder=True, steer_cap=0.85))
    plans.append(PlanSpec(name="aeb_reflex_v8", v_entry=8.0, brake_to=None, pure_brake=True))
    plans.append(PlanSpec(name="probe_then_commit_v7.5", v_entry=7.5, brake_to=6.5, probe_pulses=True, steer_cap=0.95))
    return plans


# probe pulse windows (steps): brake, throttle, steer+, steer-
PULSES = ((12, 22, "brake"), (30, 40, "throttle"), (50, 60, "steer_pos"), (68, 78, "steer_neg"))


class CommitmentController:
    """Observation-only, mu-agnostic closed-loop plan executor."""

    def __init__(self, plan: PlanSpec, design: DesignSpec):
        self.plan = plan
        self.design = design
        # mu-agnostic ladder schedule: hold each level's entry speed until the
        # earliest position at which that level's hazard would have revealed.
        self.ladder_breaks = [
            (max(level.d_lo - design.reveal_distance + 1.0, 0.0), level.entry_speed)
            for level in design.levels
        ]
        self.reset()

    def reset(self) -> None:
        self.t = 0
        self.dist = 0.0
        self.reveal_step: int | None = None
        self.speed_at_reveal = float("nan")
        self.dist_at_reveal = float("nan")
        self.passed = False
        self.last_swerve_y_aim = 3.0
        self.prep_action_sq_sum = 0.0
        self.prep_steps = 0

    # -- observation helpers ------------------------------------------------
    def _aim_point(self, obs: np.ndarray, j: int, lateral_offset_m: float) -> tuple[float, float]:
        lx = obs[ROAD_LEFT_START + 2 * j] * 80.0
        ly = obs[ROAD_LEFT_START + 2 * j + 1] * 20.0
        rx = obs[ROAD_RIGHT_START + 2 * j] * 80.0
        ry = obs[ROAD_RIGHT_START + 2 * j + 1] * 20.0
        return 0.5 * (lx + rx), 0.5 * (ly + ry) + lateral_offset_m

    def _steer(self, obs: np.ndarray, j: int, offset_m: float, gain: float, cap: float) -> float:
        xt, yt = self._aim_point(obs, j, offset_m)
        alpha = math.atan2(yt, max(xt, 1.0))
        dist = max(math.hypot(xt, yt), 2.0)
        steer_angle = math.atan2(2.0 * WHEELBASE * math.sin(alpha), dist)
        return float(np.clip(gain * steer_angle / MAX_STEER_RAD, -cap, cap))

    @staticmethod
    def _speed_actions(vx: float, v_target: float) -> tuple[float, float]:
        err = v_target - vx
        if err >= -0.15:
            throttle01 = float(np.clip(0.55 * err, 0.0, 1.0))
            brake01 = 0.0
        else:
            throttle01 = 0.0
            brake01 = float(np.clip(-0.5 * err, 0.0, 1.0))
        return 2.0 * throttle01 - 1.0, 2.0 * brake01 - 1.0

    def _swerve_steer(self, obs: np.ndarray, bx: float, by: float, vx: float, plan: PlanSpec) -> float:
        """Pure-pursuit steer toward a point swerve_offset metres to the LEFT of
        the observed obstacle; once alongside, hold a lane-offset line."""
        if bx > max(4.0, 0.45 * vx):
            y_aim = by + plan.swerve_offset
            x_aim = max(bx, 3.0)
            alpha = math.atan2(y_aim, x_aim)
            dist = max(math.hypot(x_aim, y_aim), 2.0)
            steer_angle = math.atan2(2.0 * WHEELBASE * math.sin(alpha), dist)
            return float(np.clip(plan.swerve_gain * steer_angle / MAX_STEER_RAD, -plan.steer_cap, plan.steer_cap))
        # alongside: track the avoidance line itself (stops chasing the obstacle)
        return self._steer(obs, j=1, offset_m=plan.swerve_offset, gain=1.6, cap=min(plan.steer_cap, 0.6))

    def _ladder_target(self) -> float:
        v = self.ladder_breaks[0][1]
        for break_dist, speed in self.ladder_breaks:
            if self.dist > break_dist:
                v = speed
        return v

    def _apply_pulses(self, action: list[float]) -> list[float]:
        for start, end, kind in PULSES:
            if start <= self.t < end:
                if kind == "brake":
                    return [action[0], -1.0, 1.0]
                if kind == "throttle":
                    return [action[0], 1.0, -1.0]
                if kind == "steer_pos":
                    return [float(np.clip(action[0] + 0.5, -0.9, 0.9)), action[1], action[2]]
                if kind == "steer_neg":
                    return [float(np.clip(action[0] - 0.5, -0.9, 0.9)), action[1], action[2]]
        return action

    # -- policy --------------------------------------------------------------
    def act(self, obs: np.ndarray) -> np.ndarray:
        plan = self.plan
        vx = float(obs[IDX_VX]) * 20.0
        self.dist += max(vx, 0.0) * DT
        revealed = bool(obs[IDX_OBST_PRESENT] > 0.5)
        bx = float(obs[IDX_OBST_BX]) * 80.0
        if revealed and self.reveal_step is None:
            self.reveal_step = self.t
            self.speed_at_reveal = vx
            self.dist_at_reveal = self.dist
        v_target = self._ladder_target() if plan.ladder else plan.v_entry

        if self.reveal_step is None:
            steer = self._steer(obs, j=2, offset_m=0.0, gain=1.6, cap=0.45)
            throttle, brake = self._speed_actions(vx, v_target)
            action = [steer, throttle, brake]
            if plan.probe_pulses:
                action = self._apply_pulses(action)
            self.prep_action_sq_sum += float(np.sum(np.square(action)))
            self.prep_steps += 1
        else:
            by = float(obs[IDX_OBST_BY]) * 20.0
            if revealed and bx < -0.5:
                self.passed = True
            if self.passed:
                # hold a gently decaying offset line; episode truncates at -2 m pass
                steer = self._steer(obs, j=2, offset_m=0.6 * plan.swerve_offset, gain=1.0, cap=0.35)
                throttle, brake = self._speed_actions(vx, v_target)
                action = [steer, throttle, brake]
            elif plan.pure_brake:
                steer = self._steer(obs, j=2, offset_m=0.0, gain=1.2, cap=0.2)
                action = [steer, -1.0, 1.0]
            else:
                brake_to = plan.brake_to
                if brake_to is not None and vx > brake_to + 0.2 and bx > 6.0:
                    steer = self._steer(obs, j=2, offset_m=0.0, gain=1.2, cap=0.2)
                    action = [steer, -1.0, 1.0]
                else:
                    # aim directly beside the OBSERVED obstacle: pass on the left
                    # (track-center side) with swerve_offset clearance.
                    steer = self._swerve_steer(obs, bx, by, vx, plan)
                    v_hold = brake_to if brake_to is not None else plan.v_entry
                    throttle, brake = self._speed_actions(vx, max(v_hold, 3.5))
                    action = [steer, throttle, brake]
        self.t += 1
        return np.asarray(action, dtype=np.float64)


# --------------------------------------------------------------------- rollout


def rollout(env: AutoDriftEnv, controller: CommitmentController, seed: int) -> dict[str, Any]:
    obs, info = env.reset(seed=seed)
    controller.reset()
    d0 = float(info.get("obstacle_distance", float("nan")))
    mu = float(info["mu"])
    episode_return = 0.0
    terminated = truncated = False
    while not (terminated or truncated):
        action = controller.act(np.asarray(obs, dtype=np.float64))
        obs, reward, terminated, truncated, info = env.step(action)
        episode_return += float(reward)
    bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
    return {
        "seed": seed,
        "mu": mu,
        "obstacle_distance_initial": d0,
        "outcome_bucket": bucket,
        "success": bucket == "success_obstacle_pass",
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "steps": int(info.get("step", 0)),
        "return": episode_return,
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "reveal_step": -1 if controller.reveal_step is None else int(controller.reveal_step),
        "speed_at_reveal": controller.speed_at_reveal,
        "dist_at_reveal": controller.dist_at_reveal,
        "prep_action_sq_mean": (
            controller.prep_action_sq_sum / controller.prep_steps if controller.prep_steps else float("nan")
        ),
    }


def seeds_for_level(level_index: int, n_seeds: int) -> list[int]:
    return [SEED_BASE * 10 + level_index * 1000 + k for k in range(n_seeds)]


def evaluate_design(design: DesignSpec, n_seeds: int, episode_rows: list[dict[str, Any]]) -> dict[str, Any]:
    plans = plan_family(design)
    success = np.zeros((len(plans), len(design.levels), n_seeds), dtype=np.float64)
    returns = np.zeros_like(success)
    for level_index, level in enumerate(design.levels):
        env = AutoDriftEnv(build_env_config(level_env_config(design, level)))
        assert env.base_obs_dim == OBS_DIM, f"obs layout changed: {env.base_obs_dim}"
        try:
            for plan_index, plan in enumerate(plans):
                controller = CommitmentController(plan, design)
                for k, seed in enumerate(seeds_for_level(level_index, n_seeds)):
                    row = rollout(env, controller, seed)
                    success[plan_index, level_index, k] = 1.0 if row["success"] else 0.0
                    returns[plan_index, level_index, k] = row["return"]
                    row.update(
                        {
                            "design_id": design.design_id,
                            "level_index": level_index,
                            "level_mu": level.mu,
                            "plan": plan.name,
                        }
                    )
                    episode_rows.append(row)
        finally:
            env.close()
    return {"plans": [p.name for p in plans], "success": success, "returns": returns}


def voi_from_matrix(matrix: np.ndarray) -> dict[str, Any]:
    """matrix: plans x levels x seeds. In-sample VoI + split-seed validated VoI."""
    per_cell = matrix.mean(axis=2)  # plans x levels
    oracle_in = float(per_cell.max(axis=0).mean())
    fixed_in = float(per_cell.mean(axis=1).max())
    best_fixed_in = int(per_cell.mean(axis=1).argmax())

    n_seeds = matrix.shape[2]
    train = matrix[:, :, 0::2].mean(axis=2)  # select on even-index seeds
    test = matrix[:, :, 1::2].mean(axis=2)  # evaluate on odd-index seeds
    oracle_plans = train.argmax(axis=0)
    oracle_val = float(np.mean([test[oracle_plans[level], level] for level in range(matrix.shape[1])]))
    fixed_plan = int(train.mean(axis=1).argmax())
    fixed_val = float(test[fixed_plan].mean())
    return {
        "per_plan_level_mean": per_cell,
        "oracle_in_sample": oracle_in,
        "best_fixed_in_sample": fixed_in,
        "best_fixed_plan_index": best_fixed_in,
        "voi_in_sample": oracle_in - fixed_in,
        "oracle_split_validated": oracle_val,
        "best_fixed_split_validated": fixed_val,
        "voi_split_validated": oracle_val - fixed_val,
        "oracle_plan_index_per_level": oracle_plans.tolist(),
        "fixed_plan_index_split": fixed_plan,
        "n_seeds_per_level": n_seeds,
    }


# ------------------------------------------------------------------ analytics


def analytic_design_table(design: DesignSpec) -> list[dict[str, Any]]:
    """Closed-form physics (scenarios.py model) per level -- INFERRED design aid,
    not a measurement."""
    rows = []
    for level in design.levels:
        d_mid = 0.5 * (level.d_lo + level.d_hi)
        scenario = classify_obstacle_scenario(
            speed=level.entry_speed,
            mu=level.mu,
            obstacle_distance=design.reveal_distance,
            obstacle_half_width=design.obstacle_half_width,
        )
        a_lat_drift = 0.85 * level.mu * 9.81
        t_avail = design.reveal_distance / max(level.entry_speed, 1e-6)
        rows.append(
            {
                "mu": level.mu,
                "hazard_distance_m": d_mid,
                "entry_speed_mps": level.entry_speed,
                "generator_label_at_entry_speed": scenario.label,
                "required_lateral_offset_m": scenario.required_lateral_offset,
                "drift_lateral_capacity_at_reveal_m": 0.5 * a_lat_drift * t_avail**2,
                "aeb_stop_distance_at_entry_m": scenario.aeb_stop_distance,
                "min_time_to_finish_s": d_mid / max(level.entry_speed, 1e-6),
                "deadline_s": design.deadline_s,
            }
        )
    return rows


# ---------------------------------------------------------------- inferability


def probe_env_config(design: DesignSpec) -> dict[str, Any]:
    """Continuous-mu preparation-segment env (no reveal inside the probe window)."""
    config = level_env_config(design, design.levels[-1])
    config["randomization"]["mu_range"] = [0.25, 1.15]
    config["obstacle"]["distance_range"] = [55.0, 60.0]
    config["obstacle"]["lateral_offset_range"] = [
        centerline_compensation(design.track_radius, 57.5),
        centerline_compensation(design.track_radius, 57.5),
    ]
    config["max_steps"] = 140
    return config


def _fit_ridge(xt: np.ndarray, yt: np.ndarray, alpha: float) -> np.ndarray:
    gram = xt.T @ xt + alpha * np.eye(xt.shape[1])
    return np.linalg.solve(gram, xt.T @ yt)


def episode_ridge_r2(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """60/20/20 episode-level split; alpha picked on validation; test R^2
    (same protocol as selfid_task_health_check.ridge_r2; here each row is one
    episode, so the split is directly at the episode level)."""
    n = len(y)
    order = np.random.default_rng(7).permutation(n)
    train = order[: int(0.6 * n)]
    val = order[int(0.6 * n) : int(0.8 * n)]
    test = order[int(0.8 * n) :]
    mean = x[train].mean(axis=0)
    std = x[train].std(axis=0)
    std[std < 1e-9] = 1.0
    xt = (x[train] - mean) / std
    xv = (x[val] - mean) / std
    xs = (x[test] - mean) / std
    y_mean = float(y[train].mean())
    yt = y[train] - y_mean

    def r2(pred: np.ndarray, target: np.ndarray) -> float:
        ss_res = float(np.sum((target - pred) ** 2))
        ss_tot = float(np.sum((target - target.mean()) ** 2))
        return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    best_alpha, best_val = None, -np.inf
    for alpha in (1e-2, 1e-1, 1.0, 10.0, 100.0):
        weights = _fit_ridge(xt, yt, alpha)
        val_r2 = r2(xv @ weights + y_mean, y[val])
        if np.isfinite(val_r2) and val_r2 > best_val:
            best_alpha, best_val = alpha, val_r2
    assert best_alpha is not None
    weights = _fit_ridge(xt, yt, best_alpha)
    return r2(xs @ weights + y_mean, y[test]), float(best_alpha)


PROBE_WINDOW_STEPS = 110
PROBE_FRAME_CHANNELS = 12  # per-frame indices 0-11: ego response 0-8 + previous command 9-11
PROBE_FRAME_STRIDE = 4


def run_probe_condition(design: DesignSpec, mode: str, n_episodes: int) -> dict[str, Any]:
    env = AutoDriftEnv(build_env_config(probe_env_config(design)))
    base_plan = PlanSpec(
        name=f"probe_{mode}",
        v_entry=V0,
        brake_to=None,
        probe_pulses=(mode == "probe_pulses"),
    )
    raw_features: list[np.ndarray] = []
    summary_features: list[np.ndarray] = []
    mus: list[float] = []
    terminated_early = 0
    try:
        for episode in range(n_episodes):
            seed = SEED_BASE * 100 + {"probe_pulses": 0, "no_probe": 1, "random": 2}[mode] * 10000 + episode
            controller = CommitmentController(base_plan, design)
            action_rng = np.random.default_rng(seed + 777)
            obs, info = env.reset(seed=seed)
            controller.reset()
            mus.append(float(info["mu"]))
            frames = []
            terminated = truncated = False
            for _t in range(PROBE_WINDOW_STEPS):
                if terminated or truncated:
                    terminated_early += 1
                    break
                if mode == "random":
                    action = np.array(
                        [
                            action_rng.uniform(-0.6, 0.6),
                            action_rng.uniform(-1.0, 1.0),
                            action_rng.uniform(-1.0, 0.6),
                        ]
                    )
                else:
                    action = controller.act(np.asarray(obs, dtype=np.float64))
                obs, _r, terminated, truncated, info = env.step(action)
                frames.append(np.asarray(obs[:PROBE_FRAME_CHANNELS], dtype=np.float64).copy())
            while len(frames) < PROBE_WINDOW_STEPS:  # pad early-terminated episodes
                frames.append(frames[-1].copy())
            stacked = np.stack(frames)  # steps x 12
            raw_features.append(stacked[::PROBE_FRAME_STRIDE].reshape(-1))
            summary_features.append(probe_summary_features(stacked))
    finally:
        env.close()
    x_raw = np.stack(raw_features)
    x_sum = np.stack(summary_features)
    y = np.asarray(mus)
    r2_raw, alpha_raw = episode_ridge_r2(x_raw, y)
    r2_sum, alpha_sum = episode_ridge_r2(x_sum, y)
    return {
        "mode": mode,
        "episodes": n_episodes,
        "early_terminated_episodes": terminated_early,
        "mu_min": float(y.min()),
        "mu_max": float(y.max()),
        "raw_history_features": int(x_raw.shape[1]),
        "summary_features": int(x_sum.shape[1]),
        "linear_probe_r2_raw_history": r2_raw,
        "ridge_alpha_raw": alpha_raw,
        "linear_probe_r2_summary": r2_sum,
        "ridge_alpha_summary": alpha_sum,
        "probe_protocol": (
            "episode-level 60/20/20 split, alpha on val, test R^2; channels obs[0:12] "
            f"(ego response + previous command), {PROBE_WINDOW_STEPS} prep steps, stride {PROBE_FRAME_STRIDE}"
        ),
    }


def probe_summary_features(stacked: np.ndarray) -> np.ndarray:
    """Physically interpretable window aggregates (still linear-probe features)."""
    feats: list[float] = []
    vx = stacked[:, 0] * 20.0
    ax = stacked[:, 3] * 15.0
    ay = stacked[:, 4] * 15.0
    yaw = stacked[:, 2] * 2.5
    for start, end, _kind in PULSES:
        end = min(end, len(stacked))
        window = slice(start, end)
        feats.extend(
            [
                float(np.mean(ax[window])),
                float(np.mean(np.abs(ay[window]))),
                float(np.mean(np.abs(yaw[window]))),
                float(vx[min(end - 1, len(vx) - 1)] - vx[start]),
            ]
        )
    feats.append(float(vx[-1]))
    feats.append(float(np.mean(np.abs(ay))))
    return np.asarray(feats, dtype=np.float64)


# ----------------------------------------------------------------- signatures


def behavioral_signatures(design: DesignSpec, result: dict[str, Any], voi: dict[str, Any]) -> dict[str, Any]:
    """Observable signatures a theta-aware policy must show on this family."""
    plans = result["plans"]
    oracle_idx = voi["oracle_plan_index_per_level"]
    mus = [level.mu for level in design.levels]
    oracle_entry = [plan_family(design)[i].v_entry for i in oracle_idx]
    rank_corr = spearman(mus, oracle_entry)
    return {
        "oracle_plan_per_level": [plans[i] for i in oracle_idx],
        "oracle_entry_speed_per_level_mps": oracle_entry,
        "mu_levels": mus,
        "spearman_mu_vs_oracle_entry_speed": rank_corr,
        "gate_proposal": {
            "signature_1": (
                "reveal-crossing speed rank-correlated with episode mu (Spearman >= 0.8 across the "
                "theta panel) while mu is hidden until reveal -- requires pre-reveal inference."
            ),
            "signature_2": (
                "preparation-segment action energy above the no-probe baseline (active probing "
                "pulses), measurable as prep_action_sq_mean."
            ),
            "signature_3": (
                "panel success >= best_fixed_split_validated + 0.5 * voi_split_validated "
                "(i.e., the policy realizes a meaningful share of the measured VoI)."
            ),
        },
    }


def spearman(a: list[float], b: list[float]) -> float:
    ra = np.argsort(np.argsort(np.asarray(a, dtype=np.float64)))
    rb = np.argsort(np.argsort(np.asarray(b, dtype=np.float64)))
    if np.std(ra) < 1e-12 or np.std(rb) < 1e-12:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


# ----------------------------------------------------------------------- main


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def summarize_design(design: DesignSpec, result: dict[str, Any]) -> dict[str, Any]:
    voi_success = voi_from_matrix(result["success"])
    voi_return = voi_from_matrix(result["returns"])
    plans = result["plans"]
    matrix = {
        plans[i]: {f"mu_{level.mu:g}": round(float(result['success'][i, j].mean()), 3) for j, level in enumerate(design.levels)}
        for i in range(len(plans))
    }
    return_matrix = {
        plans[i]: {f"mu_{level.mu:g}": round(float(result['returns'][i, j].mean()), 1) for j, level in enumerate(design.levels)}
        for i in range(len(plans))
    }
    return {
        "design": asdict(design),
        "deadline_s": design.deadline_s,
        "analytic_design_table_inferred": analytic_design_table(design),
        "success_matrix_measured": matrix,
        "return_matrix_measured": return_matrix,
        "voi_success": {k: v for k, v in voi_success.items() if k != "per_plan_level_mean"},
        "voi_return": {k: v for k, v in voi_return.items() if k != "per_plan_level_mean"},
        "best_fixed_plan_success": plans[voi_success["best_fixed_plan_index"]],
        "oracle_plans_success": [plans[i] for i in voi_success["oracle_plan_index_per_level"]],
        "_voi_success_obj": voi_success,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["full", "smoke"], default="full")
    parser.add_argument("--quick", action="store_true", help="small panels (CI smoke)")
    parser.add_argument("--candidate-seeds", type=int, default=6)
    parser.add_argument("--final-seeds", type=int, default=16)
    parser.add_argument("--probe-episodes", type=int, default=200)
    parser.add_argument("--results-json", type=Path, default=RESULTS_JSON)
    args = parser.parse_args()
    if args.quick:
        args.candidate_seeds, args.final_seeds, args.probe_episodes = 2, 4, 40

    started = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    if args.stage == "smoke":
        design = candidate_designs()[2]
        episode_rows: list[dict[str, Any]] = []
        for level_index, level in enumerate(design.levels):
            env = AutoDriftEnv(build_env_config(level_env_config(design, level)))
            try:
                obs, info = env.reset(seed=seeds_for_level(level_index, 1)[0])
                obstacle_lat = abs(np.linalg.norm(env.obstacle_position) - design.track_radius)
                print(
                    f"level mu={level.mu} d0={info['obstacle_distance']:.1f} label={info['obstacle_label']} "
                    f"obstacle_centerline_error={obstacle_lat:.2f} m speed_ref={info['speed_ref']:.1f}"
                )
                for plan in plan_family(design):
                    row = rollout(env, CommitmentController(plan, design), seeds_for_level(level_index, 1)[0])
                    print(
                        f"  plan={plan.name:<22} bucket={row['outcome_bucket']:<38} steps={row['steps']:>3} "
                        f"v_rev={row['speed_at_reveal']:.1f} margin={row['min_clearance_margin']:.2f} ret={row['return']:.1f}"
                    )
            finally:
                env.close()
        del episode_rows
        return

    episode_rows: list[dict[str, Any]] = []
    designs = candidate_designs()
    candidate_summaries = []
    print(f"[1/4] candidate stage: {len(designs)} designs x {args.candidate_seeds} seeds/level")
    for design in designs:
        result = evaluate_design(design, args.candidate_seeds, episode_rows)
        summary = summarize_design(design, result)
        summary.pop("_voi_success_obj")
        candidate_summaries.append(summary)
        print(
            f"  {design.design_id:<38} voi_success={summary['voi_success']['voi_in_sample']:.3f} "
            f"(val {summary['voi_success']['voi_split_validated']:.3f}) "
            f"oracle={summary['voi_success']['oracle_in_sample']:.3f} "
            f"fixed={summary['voi_success']['best_fixed_in_sample']:.3f} ({summary['best_fixed_plan_success']})"
        )

    best_index = int(
        np.argmax([s["voi_success"]["voi_split_validated"] for s in candidate_summaries])
    )
    final_design = designs[best_index]
    print(f"[2/4] final measurement on {final_design.design_id} with {args.final_seeds} seeds/level")
    final_result = evaluate_design(final_design, args.final_seeds, episode_rows)
    final_summary = summarize_design(final_design, final_result)
    final_voi_obj = final_summary.pop("_voi_success_obj")
    signatures = behavioral_signatures(final_design, final_result, final_voi_obj)

    print(f"[3/4] inferability probe ({args.probe_episodes} episodes per condition)")
    probe_results = [
        run_probe_condition(final_design, mode, args.probe_episodes)
        for mode in ("probe_pulses", "no_probe", "random")
    ]
    for probe in probe_results:
        print(
            f"  {probe['mode']:<14} R2_raw={probe['linear_probe_r2_raw_history']:.3f} "
            f"R2_summary={probe['linear_probe_r2_summary']:.3f} early_term={probe['early_terminated_episodes']}"
        )

    print("[4/4] writing artifacts")
    rows_csv = RUN_DIR / "episode_rows.csv"
    write_csv_rows(rows_csv, episode_rows)

    voi_final = final_summary["voi_success"]
    probe_main = probe_results[0]
    payload = {
        "protocol": "feasibility_audit_voi_commitment_task_design",
        "generated_by": "scripts/feasibility_audit/voi_commitment_task_design.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "hypothesis_link": (
            "Task A (experiments/feasibility_audit/voi_current_task_family.json) measured "
            "voi_success == 0 on all 24 skeletons of the CURRENT family; this script designs a "
            "commitment family where voi_success is structurally positive."
        ),
        "voi_definition": (
            "VoI = E_theta[per-theta best plan success] - max_plan E_theta[success]; theta = "
            "episode-constant hidden mu (uniform over 4 levels); plans are mu-agnostic "
            "observation-only entry-speed commitment + reaction strategies; success = "
            "outcome_bucket == success_obstacle_pass (autodrift.evaluate semantics); "
            "split-seed validation: plan selection on even seeds, evaluation on odd seeds."
        ),
        "dominance_theorem_note": (
            "With success monotone in mu for every fixed plan, mu-agnostically trackable speed "
            "profiles, and a mu-independent success threshold, the most cautious feasible plan "
            "succeeds wherever any plan succeeds => VoI_success = 0. The commitment family breaks "
            "this through the deadline (max_steps + finish_on_pass) x late reveal "
            "(perception_reveal_distance) x mu-correlated hazard distance."
        ),
        "elapsed_s": round(time.time() - started, 1),
        "panel": {
            "theta_levels_mu": [level.mu for level in final_design.levels],
            "candidate_seeds_per_level": args.candidate_seeds,
            "final_seeds_per_level": args.final_seeds,
            "seed_formula": "20260612*10 + level_index*1000 + k",
        },
        "candidate_iterations": candidate_summaries,
        "selected_design_id": final_design.design_id,
        "final_design": final_summary,
        "final_headline": {
            "voi_success_in_sample": voi_final["voi_in_sample"],
            "voi_success_split_validated": voi_final["voi_split_validated"],
            "voi_target": 0.25,
            "voi_target_met": bool(voi_final["voi_split_validated"] >= 0.25),
            "voi_return_in_sample": final_summary["voi_return"]["voi_in_sample"],
            "inferability_r2_probe_pulses_raw": probe_main["linear_probe_r2_raw_history"],
            "inferability_r2_target": 0.30,
            "inferability_target_met": bool(
                max(probe_main["linear_probe_r2_raw_history"], probe_main["linear_probe_r2_summary"]) >= 0.30
            ),
        },
        "inferability_probe": probe_results,
        "behavioral_signatures": signatures,
        "env_expressiveness_gaps": [
            (
                "mu-correlated hazard distance requires a MIXTURE of per-theta env configs; a single "
                "config cannot couple randomization.mu_range with obstacle.distance_range. Needed env "
                "feature: conditional obstacle distance sampling given the drawn mu (e.g., "
                "obstacle.distance_from_mu: [[mu_lo, mu_hi, d_lo, d_hi], ...])."
            ),
            (
                "initial speed is always speed_ref; entry-speed commitment would be cleaner with an "
                "independent initial_speed_range knob (current design works around it by giving the "
                "preparation segment enough length to reach any commitment speed from v0=8)."
            ),
            (
                "speed_ref is also the reward target (speed_cost), so slow commitments pay a reward "
                "penalty against speed_ref=8 on ALL theta; acceptable here because success-VoI is "
                "deadline-driven, but a per-plan reward target is not expressible."
            ),
        ],
        "artifacts": {
            "episode_rows_csv": str(rows_csv),
            "results_json": str(args.results_json),
        },
    }
    args.results_json.parent.mkdir(parents=True, exist_ok=True)
    args.results_json.write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")
    print(f"results -> {args.results_json}")
    print(f"episode rows -> {rows_csv} ({len(episode_rows)} rows)")
    print(
        f"HEADLINE: voi_success={voi_final['voi_in_sample']:.3f} "
        f"(split-validated {voi_final['voi_split_validated']:.3f}, target 0.25) | "
        f"probe R2 raw={probe_main['linear_probe_r2_raw_history']:.3f} (target 0.30) | "
        f"elapsed {time.time() - started:.1f}s"
    )


if __name__ == "__main__":
    main()
