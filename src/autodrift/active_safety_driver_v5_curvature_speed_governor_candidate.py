"""Candidate v5 driver: M3105 v4 incumbent + curvature-feasibility speed governor overlay.

Status: CANDIDATE ONLY. This module does not modify the deployable
``ActiveSafetyReflexDriver`` (M3105 v4 incumbent) or any of its policy configs;
promotion is a separate human decision.

Motivation (see ``experiments/feasibility_audit/v5_offtrack_diagnosis_summary.json``):
all five known feasible-row failures of the incumbent are 0-collision offtracks.

1. High-speed tracking offtracks (specs 0008/0010/0014, 14-19 m/s on the r=18 m
   circle): the v4 stack brakes only *reactively* to edge urgency (which collapses
   back to 0 while the car is still sliding outward), so the car never decelerates
   to the friction-limited cornering speed. Deceleration is always available; the
   missing piece is a *feedforward* curvature-feasibility speed target.
2. Low-speed stability offtrack (spec-0005 row, ~5 m/s, mu~0.34): the v2 base
   saturates steer (road_center_error clips at 1.0 on the r=18 circle) while
   braking hard, provoking a slow spin (yaw rate 3-7x the path demand, |beta| ->
   pi/2) that slides the car off inward. More braking cannot fix this; a small
   anti-spin (yaw-surplus) trim layer can.

The v5 overlay therefore adds, on top of the *unchanged* v4 action:

A. Curvature-feasibility grip-priority governor (high-speed only,
   ``min_speed_mps`` floor keeps low-speed rows untouched): estimates the signed
   path curvature ahead from the 32-dim boundary lookahead block of obs72 (Menger
   curvature over centerline triplets; exact on the circle track), derives a
   feasible cornering speed from a conservative assumed lateral-acceleration
   budget (mu is NOT observable and is never used), and computes a closed-loop
   activation from the overspeed plus tracking distress (edge urgency + steering
   near saturation + yaw-rate deficit vs the curvature demand). When active it
   cuts drive (throttle -> no drive) AND *releases* the v4 reactive edge/
   stability brake. Direction of action is empirically grounded (see
   ``v5_constant_action_probe`` results in the validation doc): with the
   obstacle pass point only ~20-25 m ahead, friction spent on braking is
   friction taken from cornering, and a zero-brake/no-drive coast strictly
   dominates every braking schedule on all four high-speed failure rows
   (probe sweep over constant and burst brake/steer/drift schedules). When
   obstacle urgency is high the governor *yields* to the v4 obstacle
   arbitration (avoidance has priority over track-keeping grip management).
B. Anti-spin (ESC-style) trim (low/mid speed band): when the yaw rate is in
   *surplus* of the curvature demand while sideslip grows, the into-turn steer is
   scaled down, brake is partially released and throttle capped, so the v2
   speed-floor boost cannot keep pumping energy into a developing spin. Also
   yields to obstacle urgency.

All inputs are actor-visible obs72 quantities only (ego response block, boundary
lookahead block, obstacle slots). No mu, mass, TTC, labels, or any privileged
value is read. Pure functions + a frozen-config driver class, deterministic.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import numpy as np

from autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight import (
    V4_POLICY_CONFIG,
    _clip01,
    _float,
    _hard_safety_features,
    v4_v2_fallback_no_regression_hard_safety_direct_action,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM

ACTION_COMPONENTS = ("steer", "throttle", "brake")
OUTPUT_SEMANTICS = "direct_action_clipped"
POLICY_ID = "v5_curvature_speed_governor_candidate"
DRIVER_ID = "active_safety_driver_v5_curvature_speed_governor_candidate"

V5_GOVERNOR_CONFIG: dict[str, Any] = {
    # --- A. curvature-feasibility grip-priority governor ---
    "enabled": True,
    "min_speed_mps": 9.0,  # never trigger below this speed (low-speed rows untouched)
    "kappa_min_1pm": 1.0 / 60.0,  # ignore near-straight road ahead
    "curvature_points": 6,  # centerline lookahead points used (5..30 m ahead)
    "a_lat_budget_mps2": 4.2,  # assumed available lateral acceleration (mu not observable)
    "overspeed_full_scale_mps": 4.0,
    "overspeed_trigger": 0.5,  # activation starts above this normalized overspeed
    "grip_priority_brake_release_gain": 1.0,  # brake_phys *= 1 - gain * activation
    "grip_priority_brake_cap": 0.10,  # residual brake allowed at full activation
    "governor_throttle_suppression": 1.0,  # throttle <= -suppression * activation (cuts drive)
    "distress_weight_edge": 0.6,
    "distress_weight_steer_saturation": 0.6,
    "distress_weight_yaw_deficit": 0.4,
    "distress_steer_saturation_start": 0.55,
    "distress_steer_saturation_scale": 0.35,
    "distress_activation_boost": 0.25,  # closed-loop distress lowers the activation threshold
    "obstacle_yield_start": 0.50,  # governor yields to v4 obstacle arbitration above this urgency
    "obstacle_yield_full": 0.85,
    # --- B. anti-spin (yaw-surplus) trim ---
    "esc_enabled": True,
    "esc_min_speed_mps": 1.5,
    "esc_max_speed_mps": 12.0,
    "esc_yaw_surplus_margin_radps": 0.25,
    "esc_yaw_surplus_scale_radps": 0.60,
    "esc_sideslip_ratio_start": 0.18,
    "esc_sideslip_ratio_scale": 0.25,
    "esc_steer_cut_gain": 0.80,
    "esc_brake_release_gain": 0.80,
    "esc_throttle_cap": 0.05,
    "esc_spin_risk_floor": 0.05,  # ignore negligible risk
}

V5_POLICY_CONFIG: dict[str, Any] = deepcopy(V4_POLICY_CONFIG)
V5_POLICY_CONFIG.update(
    {
        "policy_id": POLICY_ID,
        "repair_route": "v5_curvature_feasibility_speed_governor_overlay_on_v4",
        "repair_scope": "candidate_only_no_promotion_claim",
        "base_policy_id": str(V4_POLICY_CONFIG.get("policy_id", "")),
        "output_components": list(ACTION_COMPONENTS),
        "output_semantics": OUTPUT_SEMANTICS,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "governor": deepcopy(V5_GOVERNOR_CONFIG),
    }
)


def _gov_value(config: Mapping[str, Any], key: str) -> float:
    return _float(config.get("governor", {}).get(key), _float(V5_GOVERNOR_CONFIG[key]))


def _gov_flag(config: Mapping[str, Any], key: str) -> bool:
    value = config.get("governor", {}).get(key, V5_GOVERNOR_CONFIG[key])
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def curvature_corridor_features(
    observation: np.ndarray, config: Mapping[str, Any] | None = None
) -> dict[str, float]:
    """Obs72-only road geometry + ego response features for the v5 overlay.

    Returns signed Menger curvature of the centerline ahead (max-|kappa| triplet
    over the first ``curvature_points`` lookahead points; positive = left turn),
    the corridor half width, and rescaled ego quantities. Uses only the boundary
    lookahead block (obs[12:44]) and the ego response block (obs[0:6]).
    """
    cfg: Mapping[str, Any] = config or V5_POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    points = int(_gov_value(cfg, "curvature_points"))
    points = min(max(points, 3), 8)
    left = obs[12:28].reshape(8, 2).astype(np.float64)
    right = obs[28:44].reshape(8, 2).astype(np.float64)
    cx = 0.5 * (left[:, 0] + right[:, 0]) * 80.0
    cy = 0.5 * (left[:, 1] + right[:, 1]) * 20.0
    pts = np.stack([cx, cy], axis=1)[:points]
    kappa_signed = 0.0
    for index in range(points - 2):
        a, b, c = pts[index], pts[index + 1], pts[index + 2]
        ab = b - a
        bc = c - b
        ca = a - c
        cross = float(ab[0] * bc[1] - ab[1] * bc[0])
        denom = float(np.linalg.norm(ab) * np.linalg.norm(bc) * np.linalg.norm(ca))
        if denom < 1e-9:
            continue
        kappa = 2.0 * cross / denom
        if abs(kappa) > abs(kappa_signed):
            kappa_signed = kappa
    corridor_halfwidth_m = float(np.min(np.abs(left[:4, 1] - right[:4, 1])) * 0.5 * 20.0)
    return {
        "kappa_signed_1pm": float(kappa_signed),
        "kappa_abs_1pm": float(abs(kappa_signed)),
        "corridor_halfwidth_m": corridor_halfwidth_m,
        "vx_body_mps": float(obs[0] * 20.0),
        "vy_body_mps": float(obs[1] * 12.0),
        "yaw_rate_radps": float(obs[2] * 2.5),
        "steer_state_norm": float(obs[5]),
    }


def v5_governor_terms(
    observation: np.ndarray, config: Mapping[str, Any] | None = None
) -> dict[str, float]:
    """Compute the v5 overlay activation terms (diagnostic helper, pure function)."""
    cfg: Mapping[str, Any] = config or V5_POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    geo = curvature_corridor_features(obs, cfg)
    hard = _hard_safety_features(obs, cfg)
    v = geo["vx_body_mps"]
    kappa_abs = geo["kappa_abs_1pm"]
    yaw = geo["yaw_rate_radps"]

    # --- governor (A) ---
    overspeed = 0.0
    v_feas = float("inf")
    distress = 0.0
    yaw_deficit = 0.0
    activation = 0.0
    if (
        _gov_flag(cfg, "enabled")
        and v > _gov_value(cfg, "min_speed_mps")
        and kappa_abs >= _gov_value(cfg, "kappa_min_1pm")
    ):
        v_feas = float(np.sqrt(_gov_value(cfg, "a_lat_budget_mps2") / max(kappa_abs, 1e-9)))
        yaw_demand = v * kappa_abs
        yaw_aligned = yaw * np.sign(geo["kappa_signed_1pm"]) if geo["kappa_signed_1pm"] != 0.0 else abs(yaw)
        yaw_deficit = _clip01((yaw_demand - float(yaw_aligned)) / max(yaw_demand, 1e-6))
        steer_saturation = _clip01(
            (abs(geo["steer_state_norm"]) - _gov_value(cfg, "distress_steer_saturation_start"))
            / max(_gov_value(cfg, "distress_steer_saturation_scale"), 1e-6)
        )
        distress = _clip01(
            _gov_value(cfg, "distress_weight_edge") * hard["edge_urgency"]
            + _gov_value(cfg, "distress_weight_steer_saturation") * steer_saturation
            + _gov_value(cfg, "distress_weight_yaw_deficit") * yaw_deficit
        )
        overspeed = _clip01((v - v_feas) / max(_gov_value(cfg, "overspeed_full_scale_mps"), 1e-6))
        trigger = _gov_value(cfg, "overspeed_trigger")
        activation = _clip01(
            (overspeed + _gov_value(cfg, "distress_activation_boost") * distress - trigger)
            / max(1.0 - trigger, 1e-6)
        )

    # obstacle yield factor (shared by A and B): avoidance has priority
    yield_start = _gov_value(cfg, "obstacle_yield_start")
    yield_full = _gov_value(cfg, "obstacle_yield_full")
    obstacle_yield = 1.0 - _clip01(
        (hard["obstacle_urgency"] - yield_start) / max(yield_full - yield_start, 1e-6)
    )

    # --- anti-spin (B) ---
    spin_risk = 0.0
    yaw_surplus = 0.0
    sideslip = 0.0
    if (
        _gov_flag(cfg, "esc_enabled")
        and _gov_value(cfg, "esc_min_speed_mps") < v < _gov_value(cfg, "esc_max_speed_mps")
    ):
        yaw_surplus = _clip01(
            (abs(yaw) - v * kappa_abs - _gov_value(cfg, "esc_yaw_surplus_margin_radps"))
            / max(_gov_value(cfg, "esc_yaw_surplus_scale_radps"), 1e-6)
        )
        sideslip = _clip01(
            (abs(geo["vy_body_mps"]) / max(v, 1.0) - _gov_value(cfg, "esc_sideslip_ratio_start"))
            / max(_gov_value(cfg, "esc_sideslip_ratio_scale"), 1e-6)
        )
        spin_risk = yaw_surplus * sideslip
        if spin_risk < _gov_value(cfg, "esc_spin_risk_floor"):
            spin_risk = 0.0

    return {
        **geo,
        "edge_urgency": hard["edge_urgency"],
        "obstacle_urgency": hard["obstacle_urgency"],
        "yaw_deficit": float(yaw_deficit),
        "distress": float(distress),
        "v_feasible_mps": float(v_feas),
        "overspeed": float(overspeed),
        "activation": float(activation),
        "obstacle_yield": float(obstacle_yield),
        "yaw_surplus": float(yaw_surplus),
        "sideslip": float(sideslip),
        "spin_risk": float(spin_risk),
    }


def v5_curvature_speed_governor_direct_action(
    observation: np.ndarray,
    config: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Compute the v5 candidate direct [steer, throttle, brake] from obs72 only.

    Calls the unchanged v4 incumbent action function first, then applies the
    governor (A) and anti-spin (B) overlays.
    """
    cfg: Mapping[str, Any] = config or V5_POLICY_CONFIG
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")

    action = np.asarray(
        v4_v2_fallback_no_regression_hard_safety_direct_action(obs, config=cfg), dtype=np.float32
    ).copy()
    terms = v5_governor_terms(obs, cfg)

    # A. grip-priority governor: cut drive and release the v4 reactive brake so the
    # full friction budget serves cornering; leave steer to v4.
    governor_drive = terms["activation"] * terms["obstacle_yield"]
    if governor_drive > 0.0:
        brake_physical = _clip01((float(action[2]) + 1.0) / 2.0)
        released = brake_physical * (
            1.0 - _clip01(_gov_value(cfg, "grip_priority_brake_release_gain") * governor_drive)
        )
        cap = _gov_value(cfg, "grip_priority_brake_cap")
        floor_at_full = min(brake_physical, cap)
        brake_physical = max(released, floor_at_full * governor_drive)
        action[2] = -1.0 + 2.0 * _clip01(brake_physical)
        action[1] = min(
            float(action[1]),
            -_gov_value(cfg, "governor_throttle_suppression") * governor_drive,
        )

    # B. anti-spin trim: cut into-turn steer, release brake, cap throttle.
    spin_drive = terms["spin_risk"] * terms["obstacle_yield"]
    if spin_drive > 0.0:
        action[0] = float(action[0]) * (1.0 - _clip01(_gov_value(cfg, "esc_steer_cut_gain") * spin_drive))
        brake_physical = _clip01((float(action[2]) + 1.0) / 2.0)
        brake_physical *= 1.0 - _clip01(_gov_value(cfg, "esc_brake_release_gain") * spin_drive)
        action[2] = -1.0 + 2.0 * brake_physical
        if spin_drive > 0.5:
            action[1] = min(float(action[1]), _gov_value(cfg, "esc_throttle_cap"))

    action = np.clip(action, -1.0, 1.0).astype(np.float32)
    if action.shape != (ACTION_DIM,) or not np.all(np.isfinite(action)):
        raise ValueError("internal v5 action invalid")
    return action


class ActiveSafetyDriverV5Candidate:
    """Callable obs72-to-action3 v5 candidate (v4 incumbent + governor overlay).

    Candidate runtime only: accepts the actor-visible P0 observation vector and
    returns direct normalized [steer, throttle, brake]. No base policy, model
    checkpoint, recurrent state, or privileged input. Does not replace the
    deployable ``ActiveSafetyReflexDriver``.
    """

    def __init__(self, policy_config: Mapping[str, Any] | None = None):
        self.policy_config = deepcopy(dict(policy_config or V5_POLICY_CONFIG))
        self.driver_id = DRIVER_ID

    def act(self, observation: np.ndarray | list[float] | tuple[float, ...]) -> np.ndarray:
        obs = np.asarray(observation, dtype=np.float32)
        return v5_curvature_speed_governor_direct_action(obs, config=self.policy_config)

    def act_dict(self, observation: np.ndarray | list[float] | tuple[float, ...]) -> dict[str, float]:
        action = self.act(observation)
        return {component: float(action[index]) for index, component in enumerate(ACTION_COMPONENTS)}
