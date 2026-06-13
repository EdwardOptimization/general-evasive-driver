"""Phase-4 E4 Chrono drift / beyond-saturation pricing.

E4 prices whether a drift-specific Chrono regime has usable oracle headroom
after Track E' hardening, without touching the incumbent reflex driver and
without admitting Track F/F2 training.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e4_drift_regime_pricing.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e4_drift_regime_pricing.py --quick --resume
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e4_drift_regime_pricing.py --full --resume
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver  # noqa: E402
from autodrift.artifacts import utc_timestamp, write_json  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402


MILESTONE_ID = "m3260-phase4-e4-drift-regime-pricing"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e4_drift_regime_pricing_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e4_drift_regime_pricing_quick.json"
FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e4_drift_regime_pricing.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e4_drift_regime_pricing"
ROWS_QUICK_CSV = RUN_DIR / "episode_rows_quick.csv"
ROWS_FULL_CSV = RUN_DIR / "episode_rows_full.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
METRICS_FULL_CSV = RUN_DIR / "metrics_full.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr.log"
DOC_PATH = REPO_ROOT / "docs" / "m3260-phase4-e4-drift-regime-pricing.md"

E0_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_spread_expressibility_audit.json"
E1PRIME_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1prime_spread_revival_repricing.json"
E2PRIME_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2prime_chrono_two_regime_hardened.json"
E3_FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_full.json"

SEED_BASE = 2026061404
VARIANT = "sedan_tmeasy"
DT = 0.02
TRACK_RADIUS = 70.0
TRACK_WIDTH = 34.0
MAX_STEPS = 90
CHRONO_RESTART_EVERY_EPISODES = 48

BETA_THRESHOLD_RAD = 0.10
REAR_SLIP_ANGLE_THRESHOLD_RAD = 0.10
REAR_LONG_SLIP_THRESHOLD = 0.08
YAW_RATE_LIMIT_RAD_S = 2.7
MIN_SPEED_MPS = 2.0
MAX_SPEED_MPS = 28.0
MIN_ENTER_STEPS = 8
MIN_SUSTAIN_STEPS = 24
MIN_VALIDATION_UNITS_PER_CELL = 20

CLAIM_BOUNDARY = (
    "Phase-4 E4 Chrono drift / beyond-saturation pricing only: fixed v4 reflex, "
    "selection-row per-cell tuned reflex, native Chrono structured+CEM oracle, and "
    "drift-specialized feedback oracle are compared on frozen low-mu circle drift "
    "cells with obs72 sideslip/yaw and Chrono rear-tire saturation telemetry. "
    "E4 does not mutate ActiveSafetyReflexDriver, does not train, does not admit "
    "Track F/F2, and makes no validation ranking, promotion, driver-performance, "
    "current-sim sufficiency, full high-fidelity sufficiency, paper, repair-success, "
    "robustness-result, feasibility-proof, or self-ID claim."
)

ARMS = ("fixed_star", "per_instance_tuned_reflex", "native_chrono_oracle", "drift_specialized_oracle")


@dataclass(frozen=True)
class ReflexTune:
    name: str
    steer_gain: float
    speed_target: float
    beta_damping: float


@dataclass(frozen=True)
class DriftFeedbackSpec:
    name: str
    target_beta: float
    beta_gain: float
    yaw_gain: float
    steer_ff: float
    speed_target: float
    throttle_gain: float
    brake_gain: float


@dataclass(frozen=True)
class OpenLoopSpec:
    name: str
    segments: tuple[tuple[int, float, float, float], ...]


REFLEX_TUNES = (
    ReflexTune("v4_gain1p0_speed7_betadamp0", 1.0, 7.0, 0.0),
    ReflexTune("v4_gain0p7_speed7_betadamp0p25", 0.7, 7.0, 0.25),
    ReflexTune("v4_gain0p5_speed6_betadamp0p35", 0.5, 6.0, 0.35),
)

DRIFT_FEEDBACK_SPECS = (
    DriftFeedbackSpec("beta0p16_balanced", 0.16, 2.0, 0.40, 0.16, 7.0, 0.18, 0.20),
    DriftFeedbackSpec("beta0p22_power", 0.22, 2.6, 0.55, 0.22, 8.0, 0.20, 0.16),
    DriftFeedbackSpec("beta0p28_recover", 0.28, 3.2, 0.70, 0.30, 7.0, 0.14, 0.22),
)

NATIVE_STRUCTURED_SPECS = (
    OpenLoopSpec("structured_countersteer_hold", ((18, -0.38, 0.25, 0.0), (72, -0.24, 0.15, 0.0))),
    OpenLoopSpec("structured_brake_rotate_power", ((14, -0.46, 0.0, 0.18), (24, -0.30, 0.40, 0.0), (52, -0.18, 0.22, 0.0))),
    OpenLoopSpec("structured_soft_recover", ((18, -0.30, 0.10, 0.08), (72, -0.12, 0.18, 0.0))),
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else repr(number)
    return value


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _stable_hash(payload: Any) -> str:
    text = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _seed_for(*parts: Any) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little") % 2_000_000_000


def _floatish(value: Any, default: float = float("nan")) -> float:
    try:
        number = float(value)
    except Exception:
        return default
    return number if math.isfinite(number) else default


def _boolish(value: Any) -> bool:
    return value is True or str(value) == "True"


def _format_float(value: Any, digits: int = 4) -> str:
    number = _floatish(value)
    return "nan" if not math.isfinite(number) else f"{number:.{digits}f}"


def _signed_action(steer: float, throttle01: float, brake01: float) -> np.ndarray:
    return np.asarray(
        [
            float(np.clip(steer, -1.0, 1.0)),
            float(np.clip(2.0 * throttle01 - 1.0, -1.0, 1.0)),
            float(np.clip(2.0 * brake01 - 1.0, -1.0, 1.0)),
        ],
        dtype=np.float32,
    )


def _obs_kinematics(obs: np.ndarray) -> tuple[float, float, float, float]:
    vx = 20.0 * float(obs[0])
    vy = 12.0 * float(obs[1])
    yaw_rate = 2.5 * float(obs[2])
    beta = math.atan2(vy, max(abs(vx), 1e-6))
    return vx, vy, yaw_rate, beta


def _is_finite_obs(obs: np.ndarray) -> bool:
    return bool(obs.shape == (72,) and np.isfinite(obs).all())


def _cell_catalog() -> list[dict[str, Any]]:
    return [
        {
            "cell_id": "low_mu_power_oversteer",
            "description": "low-mu power-oversteer entry with moderate radius and positive initial beta",
            "mu": 0.48,
            "speed_mps": 9.0,
            "initial_beta_rad": 0.22,
            "heading_error_rad": -0.10,
            "yaw_rate_scale": 1.20,
            "track_radius": TRACK_RADIUS,
            "track_width": TRACK_WIDTH,
        },
        {
            "cell_id": "lift_off_recovery",
            "description": "lift-off recovery from larger sideslip with slightly lower entry speed",
            "mu": 0.55,
            "speed_mps": 8.0,
            "initial_beta_rad": -0.28,
            "heading_error_rad": 0.13,
            "yaw_rate_scale": 1.35,
            "track_radius": 60.0,
            "track_width": TRACK_WIDTH,
        },
    ]


def build_preregistration() -> dict[str, Any]:
    e0 = _read_json(E0_JSON)
    e1p = _read_json(E1PRIME_JSON)
    e2p = _read_json(E2PRIME_JSON)
    e3 = _read_json(E3_FULL_JSON)
    if not e0.get("decision", {}).get("e1_preregistration_admitted"):
        raise RuntimeError("E0 did not admit the Chrono fixture envelope")
    if not e1p.get("protocol_gates", {}).get("all_passed"):
        raise RuntimeError("E1' repricing artifact is not a passing predecessor")
    if not e2p.get("protocol_gates", {}).get("all_passed"):
        raise RuntimeError("E2' hardening artifact is not a passing predecessor")
    if not e3.get("protocol_gates", {}).get("all_passed"):
        raise RuntimeError("E3 full measurement artifact is not a passing predecessor")

    cells = _cell_catalog()
    selection_seeds = {
        cell["cell_id"]: [_seed_for("selection", cell["cell_id"], i) for i in range(2)]
        for cell in cells
    }
    validation_seeds = {
        cell["cell_id"]: [_seed_for("validation", cell["cell_id"], i) for i in range(MIN_VALIDATION_UNITS_PER_CELL)]
        for cell in cells
    }
    for cell in cells:
        if set(selection_seeds[cell["cell_id"]]) & set(validation_seeds[cell["cell_id"]]):
            raise RuntimeError(f"selection/validation seed overlap for {cell['cell_id']}")

    return {
        "protocol": "phase4_e4_drift_regime_pricing_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Track E4 - Chrono drift / beyond-saturation pricing",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_e4_drift_pricing_run": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "predecessor_artifacts": {
            "e0": str(E0_JSON.relative_to(REPO_ROOT)),
            "e1prime": str(E1PRIME_JSON.relative_to(REPO_ROOT)),
            "e2prime": str(E2PRIME_JSON.relative_to(REPO_ROOT)),
            "e3_full": str(E3_FULL_JSON.relative_to(REPO_ROOT)),
        },
        "chrono_vehicle_variant": VARIANT,
        "dt": DT,
        "max_steps": MAX_STEPS,
        "cells": cells,
        "selection_seeds": selection_seeds,
        "validation_seeds": validation_seeds,
        "min_validation_units_per_cell": MIN_VALIDATION_UNITS_PER_CELL,
        "quick_mode_is_verdict": False,
        "arms": {
            "fixed_star": "unmodified ActiveSafetyReflexDriver v4 incumbent action on obs72",
            "per_instance_tuned_reflex": "per-cell selection-row choice among frozen reflex wrappers; incumbent unchanged",
            "native_chrono_oracle": "per-cell selection-row choice among structured and CEM-seeded open-loop action schedules",
            "drift_specialized_oracle": "per-cell selection-row choice among frozen obs72 sideslip/yaw feedback controllers",
            "oracle": "per validation unit max(success, score) over native_chrono_oracle and drift_specialized_oracle",
        },
        "reflex_tune_candidates": [spec.__dict__ for spec in REFLEX_TUNES],
        "native_structured_candidates": [_open_loop_to_json(spec) for spec in NATIVE_STRUCTURED_SPECS],
        "drift_feedback_candidates": [spec.__dict__ for spec in DRIFT_FEEDBACK_SPECS],
        "cem_budget": {
            "iterations": 1,
            "population": 2,
            "segments": 3,
            "segment_steps": 30,
            "selection_only": True,
        },
        "thresholds": {
            "beta_threshold_rad": BETA_THRESHOLD_RAD,
            "rear_slip_angle_threshold_rad": REAR_SLIP_ANGLE_THRESHOLD_RAD,
            "rear_longitudinal_slip_threshold": REAR_LONG_SLIP_THRESHOLD,
            "yaw_rate_limit_rad_s": YAW_RATE_LIMIT_RAD_S,
            "min_speed_mps": MIN_SPEED_MPS,
            "max_speed_mps": MAX_SPEED_MPS,
            "min_enter_steps": MIN_ENTER_STEPS,
            "min_sustain_steps": MIN_SUSTAIN_STEPS,
        },
        "runtime_gates": [
            "preregistration is frozen before quick/full rows",
            "selection and validation seed streams are disjoint",
            "quick smoke runs at least one cell and all four arms while remaining non-verdict",
            "full run writes >=20 validation units per cell",
            "all validation units have fixed*, per-tuned, native oracle, and drift-specialized oracle rows",
            "obs72 sideslip/yaw and four-wheel Chrono tire telemetry are finite for interpreted rows",
            "selection-row oracle adequacy is nonnegative versus per-tuned for every cell",
            "per-cell paired CIs are reported for oracle-minus-fixed* and oracle-minus-per-tuned",
            "Track F/F2/training admission remains false",
        ],
        "decision_rule": (
            "E4 is completed when quick and full artifacts exist under this preregistration, "
            "full protocol gates pass, every cell has >=20 validation units, selection-row "
            "oracle adequacy is nonnegative, paired CIs and failure modes are reported, and "
            "Track F/F2 remains blocked. A positive drift prize is descriptive only and does "
            "not admit training."
        ),
    }


def _open_loop_to_json(spec: OpenLoopSpec) -> dict[str, Any]:
    return {"name": spec.name, "segments": [list(segment) for segment in spec.segments]}


def write_preregistration() -> dict[str, Any]:
    payload = build_preregistration()
    write_json(PREREG_JSON, payload)
    return payload


def load_preregistration() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise FileNotFoundError(f"missing preregistration {PREREG_JSON}; run --write-prereg first")
    payload = _read_json(PREREG_JSON)
    if not payload.get("frozen_before_any_e4_drift_pricing_run"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_e4_drift_pricing_run")
    return payload


def scenario_for_cell(cell: dict[str, Any], *, seed: int, mode: str) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    radius = float(cell["track_radius"])
    speed = float(cell["speed_mps"]) + float(rng.normal(0.0, 0.20 if mode == "validation" else 0.05))
    beta = float(cell["initial_beta_rad"]) + float(rng.normal(0.0, 0.015))
    heading_error = float(cell["heading_error_rad"]) + float(rng.normal(0.0, 0.010))
    yaw_rate = float(cell["yaw_rate_scale"]) * speed / radius
    return {
        "scenario_id": f"m3260-{mode}-{cell['cell_id']}-seed{seed}",
        "dt": DT,
        "max_steps": MAX_STEPS,
        "track_kind": "circle",
        "track_radius": radius,
        "track_width": float(cell["track_width"]),
        "road_lookahead_count": 8,
        "road_lookahead_spacing": 5.0,
        "obstacle_slots": 4,
        "obstacle_relative_velocity_mode": "ego",
        "soft_offtrack_metric_enabled": False,
        "soft_offtrack_tolerance_m": 0.0,
        "chrono_vehicle_variant": VARIANT,
        "params": {
            "mass": 1684.0,
            "mu": float(cell["mu"]),
            "max_steer": 0.62,
            "max_steer_rate": 3.5,
            "max_drive_force": 8200.0,
            "max_brake_force": 6000.0,
            "drive_tau": 0.08,
            "steer_tau": 0.06,
            "iz": 2400.0,
            "lf": 1.2,
            "lr": 1.6,
            "cf": 90000.0,
            "cr": 110000.0,
        },
        "initial_state": {
            "x": radius,
            "y": 0.0,
            "psi": math.pi / 2.0 + heading_error,
            "vx": speed * math.cos(beta),
            "vy": speed * math.sin(beta),
            "yaw_rate": yaw_rate,
        },
        "speed_ref": speed,
        "obstacle": {"enabled": False},
        "warmup_gate": {"enabled": False},
        "friction_step": {"at": None, "new_mu": None},
        "terminate_on_failure": False,
    }


class FixedStarPolicy:
    def __init__(self) -> None:
        self.driver = ActiveSafetyReflexDriver()

    def __call__(self, _step: int, obs: np.ndarray) -> np.ndarray:
        return np.asarray(self.driver.act(obs), dtype=np.float32)


class TunedReflexPolicy:
    def __init__(self, spec: ReflexTune) -> None:
        self.spec = spec
        self.driver = ActiveSafetyReflexDriver()

    def __call__(self, _step: int, obs: np.ndarray) -> np.ndarray:
        action = np.asarray(self.driver.act(obs), dtype=np.float32).copy()
        vx, _vy, _yaw, beta = _obs_kinematics(obs)
        action[0] = float(np.clip(self.spec.steer_gain * float(action[0]) - self.spec.beta_damping * beta, -1.0, 1.0))
        err = self.spec.speed_target - vx
        throttle01 = float(np.clip(0.12 * err, 0.0, 0.50))
        brake01 = float(np.clip(-0.10 * err, 0.0, 0.35))
        action[1] = max(float(action[1]), 2.0 * throttle01 - 1.0)
        action[2] = max(float(action[2]), 2.0 * brake01 - 1.0)
        return action


class OpenLoopPolicy:
    def __init__(self, spec: OpenLoopSpec, *, side: float) -> None:
        self.spec = spec
        self.side = 1.0 if side >= 0.0 else -1.0

    def __call__(self, step: int, _obs: np.ndarray) -> np.ndarray:
        cursor = 0
        for length, steer, throttle01, brake01 in self.spec.segments:
            cursor += int(length)
            if step < cursor:
                return _signed_action(-self.side * float(steer), float(throttle01), float(brake01))
        length, steer, throttle01, brake01 = self.spec.segments[-1]
        return _signed_action(-self.side * float(steer), float(throttle01), float(brake01))


class DriftFeedbackPolicy:
    def __init__(self, spec: DriftFeedbackSpec, *, side: float) -> None:
        self.spec = spec
        self.side = 1.0 if side >= 0.0 else -1.0

    def __call__(self, _step: int, obs: np.ndarray) -> np.ndarray:
        vx, _vy, yaw_rate, beta = _obs_kinematics(obs)
        target_beta = self.side * self.spec.target_beta
        beta_error = beta - target_beta
        steer = -self.side * self.spec.steer_ff - self.spec.beta_gain * beta_error - self.spec.yaw_gain * yaw_rate
        speed_error = self.spec.speed_target - vx
        throttle01 = float(np.clip(0.18 + self.spec.throttle_gain * speed_error, 0.0, 0.65))
        brake01 = float(np.clip(-self.spec.brake_gain * speed_error, 0.0, 0.45))
        return _signed_action(steer, throttle01, brake01)


def _native_candidates(cell: dict[str, Any], seed: int, *, quick: bool) -> list[tuple[str, Callable[[], Callable[[int, np.ndarray], np.ndarray]]]]:
    side = float(cell["initial_beta_rad"])
    candidates: list[tuple[str, Callable[[], Callable[[int, np.ndarray], np.ndarray]]]] = [
        (f"native:{spec.name}", lambda spec=spec: OpenLoopPolicy(spec, side=side))
        for spec in NATIVE_STRUCTURED_SPECS
    ]
    rng = np.random.default_rng(_seed_for("cem", cell["cell_id"], seed))
    population = 1 if quick else 2
    for idx in range(population):
        segments = []
        for _ in range(3):
            steer = float(np.clip(rng.normal(-0.26, 0.16), -0.70, 0.15))
            throttle01 = float(np.clip(rng.normal(0.24, 0.18), 0.0, 0.75))
            brake01 = float(np.clip(rng.normal(0.04, 0.10), 0.0, 0.35))
            segments.append((30, steer, throttle01, brake01))
        spec = OpenLoopSpec(f"cem_iter0_sample{idx}", tuple(segments))
        candidates.append((f"native:{spec.name}", lambda spec=spec: OpenLoopPolicy(spec, side=side)))
    return candidates


def _drift_feedback_candidates(cell: dict[str, Any]) -> list[tuple[str, Callable[[], Callable[[int, np.ndarray], np.ndarray]]]]:
    side = float(cell["initial_beta_rad"])
    return [
        (f"drift:{spec.name}", lambda spec=spec: DriftFeedbackPolicy(spec, side=side))
        for spec in DRIFT_FEEDBACK_SPECS
    ]


def _reflex_candidates() -> list[tuple[str, Callable[[], Callable[[int, np.ndarray], np.ndarray]]]]:
    return [(f"reflex:{spec.name}", lambda spec=spec: TunedReflexPolicy(spec)) for spec in REFLEX_TUNES]


def _rear_saturation(info: dict[str, Any]) -> tuple[bool, int, float, float]:
    rear_rows = [
        row for row in (info.get("tire_telemetry", []) or [])
        if str(row.get("axle", "")) == "rear" or int(_floatish(row.get("axle_index", -1), -1)) == 1
    ]
    max_slip_angle = 0.0
    max_long_slip = 0.0
    saturated = False
    for row in rear_rows:
        slip_angle = abs(_floatish(row.get("slip_angle_rad"), 0.0))
        long_slip = abs(_floatish(row.get("longitudinal_slip"), 0.0))
        max_slip_angle = max(max_slip_angle, slip_angle)
        max_long_slip = max(max_long_slip, long_slip)
        saturated = saturated or slip_angle >= REAR_SLIP_ANGLE_THRESHOLD_RAD or long_slip >= REAR_LONG_SLIP_THRESHOLD
    return saturated, len(rear_rows), max_slip_angle, max_long_slip


def _failure_mode(result: dict[str, Any]) -> str:
    if int(result["rear_saturation_steps"]) < MIN_ENTER_STEPS or int(result["high_sideslip_steps"]) < MIN_ENTER_STEPS:
        return "fail_to_enter"
    if int(result["longest_controlled_drift_run"]) < MIN_SUSTAIN_STEPS:
        return "fail_to_stabilize"
    if str(result.get("first_failure_reason", "")):
        return "fail_to_recover"
    return "controlled_drift"


def _score_result(result: dict[str, Any]) -> float:
    steps = max(1, int(result["steps"]))
    score = 100.0 * float(result["controlled_drift_steps"]) / steps
    score += 25.0 * float(result["rear_saturation_steps"]) / steps
    score += 20.0 * float(result["high_sideslip_steps"]) / steps
    score += 0.5 * float(result["longest_controlled_drift_run"])
    if result["drift_success"]:
        score += 200.0
    if str(result.get("first_failure_reason", "")):
        score -= 35.0
    if not result["variant_match"] or not result["reset_obs_finite"]:
        score -= 200.0
    return float(score)


def run_episode(
    client: ChronoWorkerClient,
    scenario: dict[str, Any],
    policy: Callable[[int, np.ndarray], np.ndarray],
    *,
    seed: int,
) -> dict[str, Any]:
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
    backend = dict(reset_reply.get("backend_info", {}))
    info = dict(reset_reply.get("info", {}))
    reset_obs_finite = _is_finite_obs(obs)
    variant_match = backend.get("chrono_vehicle_variant") == VARIANT
    steps = 0
    terminated = truncated = False
    status = "reset"
    high_sideslip_steps = 0
    rear_saturation_steps = 0
    controlled_drift_steps = 0
    longest_controlled = 0
    current_controlled = 0
    finite_obs_all = reset_obs_finite
    telemetry_samples = 0
    rear_telemetry_samples = 0
    max_abs_beta = 0.0
    max_abs_yaw_rate = 0.0
    max_rear_slip_angle = 0.0
    max_rear_long_slip = 0.0
    first_failure_reason = ""
    trace_signature = float(np.sum(obs, dtype=np.float64)) if reset_obs_finite else 0.0

    while not (terminated or truncated) and steps < int(scenario["max_steps"]):
        action = np.asarray(policy(steps, obs), dtype=np.float32)
        obs, terminated, truncated, status, info = client.step(action)
        finite = _is_finite_obs(obs)
        finite_obs_all = finite_obs_all and finite
        if finite:
            trace_signature += float(np.sum(obs, dtype=np.float64))
            vx, _vy, yaw_rate, beta = _obs_kinematics(obs)
        else:
            vx, yaw_rate, beta = 0.0, float("inf"), float("inf")
        rear_saturated, rear_count, rear_slip_angle, rear_long_slip = _rear_saturation(info)
        telemetry_samples += 1 if bool(info.get("tire_telemetry_available", False)) else 0
        rear_telemetry_samples += 1 if rear_count >= 2 else 0
        high_beta = abs(beta) >= BETA_THRESHOLD_RAD
        controlled = MIN_SPEED_MPS <= vx <= MAX_SPEED_MPS and abs(yaw_rate) <= YAW_RATE_LIMIT_RAD_S
        controlled_drift = bool(finite and high_beta and rear_saturated and controlled)
        high_sideslip_steps += int(high_beta)
        rear_saturation_steps += int(rear_saturated)
        controlled_drift_steps += int(controlled_drift)
        current_controlled = current_controlled + 1 if controlled_drift else 0
        longest_controlled = max(longest_controlled, current_controlled)
        max_abs_beta = max(max_abs_beta, abs(beta))
        max_abs_yaw_rate = max(max_abs_yaw_rate, abs(yaw_rate))
        max_rear_slip_angle = max(max_rear_slip_angle, rear_slip_angle)
        max_rear_long_slip = max(max_rear_long_slip, rear_long_slip)
        if not first_failure_reason:
            reason = str(info.get("termination_reason", "") or "")
            events = info.get("first_failure_events", []) or []
            if reason and reason not in {"timeout", "max_steps"}:
                first_failure_reason = reason
            elif events:
                first_failure_reason = str(events[0])
            elif finite and (vx < 0.5 or abs(yaw_rate) > 3.2):
                first_failure_reason = "dynamic_limit"
        steps += 1

    drift_success = bool(longest_controlled >= MIN_SUSTAIN_STEPS)
    result = {
        "steps": int(steps),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "backend_status": status,
        "reset_obs_finite": bool(reset_obs_finite),
        "finite_obs_all": bool(finite_obs_all),
        "variant_match": bool(variant_match),
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "completion_reason": str(info.get("completion_reason", "") or ""),
        "first_failure_reason": first_failure_reason,
        "high_sideslip_steps": int(high_sideslip_steps),
        "rear_saturation_steps": int(rear_saturation_steps),
        "controlled_drift_steps": int(controlled_drift_steps),
        "longest_controlled_drift_run": int(longest_controlled),
        "drift_success": drift_success,
        "telemetry_samples": int(telemetry_samples),
        "rear_telemetry_samples": int(rear_telemetry_samples),
        "max_abs_beta_rad": float(max_abs_beta),
        "max_abs_yaw_rate_rad_s": float(max_abs_yaw_rate),
        "max_rear_slip_angle_rad": float(max_rear_slip_angle),
        "max_rear_longitudinal_slip": float(max_rear_long_slip),
        "backend_info": {
            "backend_id": backend.get("backend_id", ""),
            "chrono_vehicle_variant": backend.get("chrono_vehicle_variant", ""),
            "chrono_vehicle_model": backend.get("chrono_vehicle_model", ""),
            "chrono_tire_model": backend.get("chrono_tire_model", ""),
            "vehicle_total_mass": backend.get("vehicle_total_mass", ""),
            "target_mass": backend.get("target_mass", ""),
        },
        "trace_signature": repr(trace_signature),
    }
    result["failure_mode"] = _failure_mode(result)
    result["score"] = _score_result(result)
    return result


FIELDNAMES = [
    "mode",
    "role",
    "cell_id",
    "seed",
    "validation_unit",
    "variant",
    "arm",
    "candidate",
    "selected_candidate",
    "steps",
    "drift_success",
    "score",
    "failure_mode",
    "first_failure_reason",
    "high_sideslip_steps",
    "rear_saturation_steps",
    "controlled_drift_steps",
    "longest_controlled_drift_run",
    "max_abs_beta_rad",
    "max_abs_yaw_rate_rad_s",
    "max_rear_slip_angle_rad",
    "max_rear_longitudinal_slip",
    "telemetry_samples",
    "rear_telemetry_samples",
    "reset_obs_finite",
    "finite_obs_all",
    "variant_match",
    "termination_reason",
    "completion_reason",
    "backend_model",
    "backend_tire",
    "trace_signature",
    "claim_boundary",
]


def _row(
    *,
    mode: str,
    role: str,
    cell_id: str,
    seed: int,
    validation_unit: int | str,
    arm: str,
    candidate: str,
    selected_candidate: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    backend = result.get("backend_info", {})
    return {
        "mode": mode,
        "role": role,
        "cell_id": cell_id,
        "seed": int(seed),
        "validation_unit": validation_unit,
        "variant": VARIANT,
        "arm": arm,
        "candidate": candidate,
        "selected_candidate": selected_candidate,
        "steps": int(result["steps"]),
        "drift_success": bool(result["drift_success"]),
        "score": round(float(result["score"]), 6),
        "failure_mode": str(result["failure_mode"]),
        "first_failure_reason": str(result.get("first_failure_reason", "")),
        "high_sideslip_steps": int(result["high_sideslip_steps"]),
        "rear_saturation_steps": int(result["rear_saturation_steps"]),
        "controlled_drift_steps": int(result["controlled_drift_steps"]),
        "longest_controlled_drift_run": int(result["longest_controlled_drift_run"]),
        "max_abs_beta_rad": round(float(result["max_abs_beta_rad"]), 6),
        "max_abs_yaw_rate_rad_s": round(float(result["max_abs_yaw_rate_rad_s"]), 6),
        "max_rear_slip_angle_rad": round(float(result["max_rear_slip_angle_rad"]), 6),
        "max_rear_longitudinal_slip": round(float(result["max_rear_longitudinal_slip"]), 6),
        "telemetry_samples": int(result["telemetry_samples"]),
        "rear_telemetry_samples": int(result["rear_telemetry_samples"]),
        "reset_obs_finite": bool(result["reset_obs_finite"]),
        "finite_obs_all": bool(result["finite_obs_all"]),
        "variant_match": bool(result["variant_match"]),
        "termination_reason": str(result.get("termination_reason", "")),
        "completion_reason": str(result.get("completion_reason", "")),
        "backend_model": backend.get("chrono_vehicle_model", ""),
        "backend_tire": backend.get("chrono_tire_model", ""),
        "trace_signature": str(result.get("trace_signature", "")),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _jsonable(row.get(key, "")) for key in FIELDNAMES})


def _append_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        if new_file:
            writer.writeheader()
        writer.writerow({key: _jsonable(row.get(key, "")) for key in FIELDNAMES})


def _append_progress(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


class RestartingChronoRunner:
    def __init__(self, stderr_log: Path):
        self.stderr_log = stderr_log
        self.client: ChronoWorkerClient | None = None
        self.count = 0

    def _ensure(self) -> ChronoWorkerClient:
        if self.client is None:
            self.client = ChronoWorkerClient(stderr_log=self.stderr_log)
            self.count = 0
        return self.client

    def restart(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
            self.count = 0

    def run(self, scenario: dict[str, Any], policy: Callable[[int, np.ndarray], np.ndarray], *, seed: int) -> dict[str, Any]:
        if self.count >= CHRONO_RESTART_EVERY_EPISODES:
            self.restart()
        try:
            result = run_episode(self._ensure(), scenario, policy, seed=seed)
        except Exception as exc:
            self.restart()
            result = run_episode(self._ensure(), scenario, policy, seed=seed)
            result["restart_after_error"] = f"{type(exc).__name__}: {exc}"
        self.count += 1
        return result

    def close(self) -> None:
        self.restart()


def _candidate_done(rows: list[dict[str, str]]) -> set[tuple[str, str, str, str, str]]:
    return {
        (row["role"], row["cell_id"], str(row["seed"]), row["arm"], row["candidate"])
        for row in rows
    }


def _select_best_candidates(rows: list[dict[str, str]], prereg: dict[str, Any], *, quick: bool) -> dict[str, dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    cells = prereg["cells"][:1] if quick else prereg["cells"]
    for cell in cells:
        cell_id = cell["cell_id"]
        cell_rows = [row for row in rows if row["role"] == "selection" and row["cell_id"] == cell_id]
        for arm in ("per_instance_tuned_reflex", "native_chrono_oracle", "drift_specialized_oracle"):
            arm_rows = [row for row in cell_rows if row["arm"] == arm]
            if not arm_rows:
                continue
            scores: dict[str, float] = {}
            counts: dict[str, int] = {}
            for row in arm_rows:
                candidate = row["candidate"]
                scores[candidate] = scores.get(candidate, 0.0) + _floatish(row["score"], -1e9)
                counts[candidate] = counts.get(candidate, 0) + 1
            selected.setdefault(cell_id, {})[arm] = max(
                scores,
                key=lambda candidate: (scores[candidate] / max(counts[candidate], 1), candidate),
            )
    return selected


def _selection_oracle_adequacy(rows: list[dict[str, str]], prereg: dict[str, Any], *, quick: bool) -> dict[str, bool]:
    selected = _select_best_candidates(rows, prereg, quick=quick)
    cells = prereg["cells"][:1] if quick else prereg["cells"]
    adequacy: dict[str, bool] = {}
    for cell in cells:
        cell_id = cell["cell_id"]
        chosen = selected.get(cell_id, {})
        per_candidate = chosen.get("per_instance_tuned_reflex", "")
        native_candidate = chosen.get("native_chrono_oracle", "")
        drift_candidate = chosen.get("drift_specialized_oracle", "")
        cell_rows = [row for row in rows if row["role"] == "selection" and row["cell_id"] == cell_id]

        def mean_score(arm: str, candidate: str) -> float:
            values = [
                _floatish(row["score"], -1e9)
                for row in cell_rows
                if row["arm"] == arm and row["candidate"] == candidate
            ]
            return float(np.mean(values)) if values else -1e9

        per_score = mean_score("per_instance_tuned_reflex", per_candidate)
        oracle_score = max(
            mean_score("native_chrono_oracle", native_candidate),
            mean_score("drift_specialized_oracle", drift_candidate),
        )
        adequacy[cell_id] = bool(oracle_score >= per_score and per_score > -1e8)
    return adequacy


def _policy_for_candidate(cell: dict[str, Any], arm: str, candidate: str, seed: int, *, quick: bool) -> Callable[[int, np.ndarray], np.ndarray]:
    if arm == "fixed_star":
        return FixedStarPolicy()
    if arm == "per_instance_tuned_reflex":
        specs = {f"reflex:{spec.name}": spec for spec in REFLEX_TUNES}
        return TunedReflexPolicy(specs[candidate])
    if arm == "native_chrono_oracle":
        factories = dict(_native_candidates(cell, seed, quick=quick))
        return factories[candidate]()
    if arm == "drift_specialized_oracle":
        factories = dict(_drift_feedback_candidates(cell))
        return factories[candidate]()
    raise ValueError(f"unknown arm {arm!r}")


def run_rollout(*, prereg: dict[str, Any], quick: bool, resume: bool) -> dict[str, Any]:
    rows_csv = ROWS_QUICK_CSV if quick else ROWS_FULL_CSV
    metrics_csv = METRICS_QUICK_CSV if quick else METRICS_FULL_CSV
    progress_jsonl = PROGRESS_QUICK_JSONL if quick else PROGRESS_FULL_JSONL
    result_json = QUICK_JSON if quick else FULL_JSON
    if not resume:
        for path in (rows_csv, metrics_csv, progress_jsonl, result_json):
            if path.exists():
                path.unlink()

    mode = "quick" if quick else "full"
    cells = prereg["cells"][:1] if quick else prereg["cells"]
    selection_seeds_by_cell = {
        cell["cell_id"]: list(prereg["selection_seeds"][cell["cell_id"]][:1 if quick else None])
        for cell in cells
    }
    validation_seeds_by_cell = {
        cell["cell_id"]: list(prereg["validation_seeds"][cell["cell_id"]][:1 if quick else None])
        for cell in cells
    }
    rows = _read_csv(rows_csv)
    done = _candidate_done(rows)
    runner = RestartingChronoRunner(STDERR_LOG)
    started = time.time()
    completed = len(done)

    try:
        for cell in cells:
            cell_id = cell["cell_id"]
            for seed in selection_seeds_by_cell[cell_id]:
                scenario = scenario_for_cell(cell, seed=seed, mode="selection")
                candidates: list[tuple[str, str, Callable[[], Callable[[int, np.ndarray], np.ndarray]]]] = []
                candidates.extend(("per_instance_tuned_reflex", name, factory) for name, factory in _reflex_candidates())
                candidates.extend(("native_chrono_oracle", name, factory) for name, factory in _native_candidates(cell, seed, quick=quick))
                candidates.extend(("drift_specialized_oracle", name, factory) for name, factory in _drift_feedback_candidates(cell))
                for arm, candidate, factory in candidates:
                    key = ("selection", cell_id, str(seed), arm, candidate)
                    if key in done:
                        continue
                    result = runner.run(scenario, factory(), seed=seed)
                    _append_row(
                        rows_csv,
                        _row(
                            mode=mode,
                            role="selection",
                            cell_id=cell_id,
                            seed=seed,
                            validation_unit="",
                            arm=arm,
                            candidate=candidate,
                            selected_candidate="",
                            result=result,
                        ),
                    )
                    completed += 1
                    _append_progress(progress_jsonl, {"stage": "selection", "completed": completed, "cell_id": cell_id, "arm": arm, "candidate": candidate})

        rows = _read_csv(rows_csv)
        selected = _select_best_candidates(rows, prereg, quick=quick)
        for cell in cells:
            cell_id = cell["cell_id"]
            for unit_index, seed in enumerate(validation_seeds_by_cell[cell_id]):
                scenario = scenario_for_cell(cell, seed=seed, mode="validation")
                validation_specs = [
                    ("fixed_star", "fixed_star"),
                    ("per_instance_tuned_reflex", selected[cell_id]["per_instance_tuned_reflex"]),
                    ("native_chrono_oracle", selected[cell_id]["native_chrono_oracle"]),
                    ("drift_specialized_oracle", selected[cell_id]["drift_specialized_oracle"]),
                ]
                for arm, candidate in validation_specs:
                    key = ("validation", cell_id, str(seed), arm, candidate)
                    if key in done:
                        continue
                    result = runner.run(scenario, _policy_for_candidate(cell, arm, candidate, seed, quick=quick), seed=seed)
                    _append_row(
                        rows_csv,
                        _row(
                            mode=mode,
                            role="validation",
                            cell_id=cell_id,
                            seed=seed,
                            validation_unit=unit_index,
                            arm=arm,
                            candidate=candidate,
                            selected_candidate=candidate,
                            result=result,
                        ),
                    )
                    completed += 1
                    _append_progress(progress_jsonl, {"stage": "validation", "completed": completed, "cell_id": cell_id, "arm": arm, "seed": seed})
    finally:
        runner.close()

    rows = _read_csv(rows_csv)
    summary = summarize(rows, prereg, quick=quick, elapsed_s=time.time() - started)
    write_json(result_json, summary)
    write_metrics(metrics_csv, summary)
    if not quick:
        write_markdown(summary)
    if not summary["protocol_gates"]["all_passed"]:
        raise RuntimeError(f"E4 protocol gates failed: {summary['protocol_gates']}")
    return summary


def _paired_delta_ci(rows: list[dict[str, str]], cell_id: str, arm_a: str, arm_b: str) -> dict[str, Any]:
    by_unit: dict[str, dict[str, int]] = {}
    for row in rows:
        if row["role"] != "validation" or row["cell_id"] != cell_id:
            continue
        unit = str(row["validation_unit"])
        if row["arm"] in {arm_a, arm_b}:
            by_unit.setdefault(unit, {})[row["arm"]] = int(_boolish(row["drift_success"]))
    diffs = [pair[arm_a] - pair[arm_b] for pair in by_unit.values() if arm_a in pair and arm_b in pair]
    if not diffs:
        return {"n_pairs": 0, "mean": 0.0, "ci95_low": 0.0, "ci95_high": 0.0}
    arr = np.asarray(diffs, dtype=float)
    mean = float(np.mean(arr))
    if len(arr) == 1:
        half = 0.0
    else:
        half = 1.96 * float(np.std(arr, ddof=1)) / math.sqrt(len(arr))
    return {
        "n_pairs": int(len(arr)),
        "mean": round(mean, 6),
        "ci95_low": round(max(-1.0, mean - half), 6),
        "ci95_high": round(min(1.0, mean + half), 6),
    }


def _oracle_synthetic_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    synthetic = list(rows)
    by_unit: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        if row["role"] == "validation" and row["arm"] in {"native_chrono_oracle", "drift_specialized_oracle"}:
            by_unit.setdefault((row["cell_id"], str(row["validation_unit"])), []).append(row)
    for (_cell_id, _unit), unit_rows in by_unit.items():
        best = max(
            unit_rows,
            key=lambda row: (int(_boolish(row["drift_success"])), _floatish(row["score"], -1e9), row["arm"]),
        )
        oracle_row = dict(best)
        oracle_row["arm"] = "oracle"
        oracle_row["candidate"] = f"oracle_max:{best['arm']}:{best['candidate']}"
        synthetic.append(oracle_row)
    return synthetic


def _cell_readout(rows: list[dict[str, str]], prereg: dict[str, Any], cell: dict[str, Any], *, quick: bool) -> dict[str, Any]:
    cell_id = cell["cell_id"]
    validation_rows = [row for row in rows if row["role"] == "validation" and row["cell_id"] == cell_id]
    validation_units = sorted({row["validation_unit"] for row in validation_rows if row["arm"] == "fixed_star"})
    arm_success = {
        arm: sum(_boolish(row["drift_success"]) for row in validation_rows if row["arm"] == arm)
        for arm in ARMS
    }
    arm_n = {arm: sum(1 for row in validation_rows if row["arm"] == arm) for arm in ARMS}
    selection_rows = [row for row in rows if row["role"] == "selection" and row["cell_id"] == cell_id]
    selected = _select_best_candidates(rows, prereg, quick=quick).get(cell_id, {})
    oracle_rows = _oracle_synthetic_rows(rows)
    failure_modes: dict[str, int] = {}
    for row in validation_rows:
        if row["arm"] in {"fixed_star", "per_instance_tuned_reflex"}:
            failure_modes[row["failure_mode"]] = failure_modes.get(row["failure_mode"], 0) + 1
    return {
        "cell_id": cell_id,
        "selected_candidates": selected,
        "selection_row_count": len(selection_rows),
        "validation_units": len(validation_units),
        "arm_n": arm_n,
        "arm_success": arm_success,
        "arm_success_rate": {
            arm: round(arm_success[arm] / max(arm_n[arm], 1), 6)
            for arm in ARMS
        },
        "oracle_minus_fixed_star": _paired_delta_ci(oracle_rows, cell_id, "oracle", "fixed_star"),
        "oracle_minus_per_instance_tuned_reflex": _paired_delta_ci(
            oracle_rows, cell_id, "oracle", "per_instance_tuned_reflex"
        ),
        "native_minus_per_instance_tuned_reflex": _paired_delta_ci(
            rows, cell_id, "native_chrono_oracle", "per_instance_tuned_reflex"
        ),
        "drift_specialized_minus_per_instance_tuned_reflex": _paired_delta_ci(
            rows, cell_id, "drift_specialized_oracle", "per_instance_tuned_reflex"
        ),
        "reflex_failure_modes": failure_modes,
        "max_observed_beta_rad": max((_floatish(row["max_abs_beta_rad"], 0.0) for row in validation_rows), default=0.0),
        "max_observed_rear_slip_angle_rad": max((_floatish(row["max_rear_slip_angle_rad"], 0.0) for row in validation_rows), default=0.0),
    }


def summarize(rows: list[dict[str, str]], prereg: dict[str, Any], *, quick: bool, elapsed_s: float) -> dict[str, Any]:
    cells = prereg["cells"][:1] if quick else prereg["cells"]
    cell_readouts = [_cell_readout(rows, prereg, cell, quick=quick) for cell in cells]
    validation_rows = [row for row in rows if row["role"] == "validation"]
    selection_rows = [row for row in rows if row["role"] == "selection"]
    row_cells = {row["cell_id"] for row in validation_rows}
    expected_cells = {cell["cell_id"] for cell in cells}
    expected_units = 1 if quick else int(prereg["min_validation_units_per_cell"])
    arm_cell_units_ok = all(
        readout["validation_units"] >= expected_units
        and all(readout["arm_n"].get(arm, 0) >= expected_units for arm in ARMS)
        for readout in cell_readouts
    )
    obs_telemetry_ok = bool(validation_rows) and all(
        _boolish(row["reset_obs_finite"])
        and _boolish(row["finite_obs_all"])
        and _boolish(row["variant_match"])
        and int(_floatish(row["rear_telemetry_samples"], 0)) >= max(1, int(_floatish(row["steps"], 0)) // 2)
        for row in validation_rows
    )
    selection_adequacy = _selection_oracle_adequacy(rows, prereg, quick=quick)
    gates = {
        "preregistration_frozen": prereg.get("frozen_before_any_e4_drift_pricing_run") is True,
        "quick_mode_is_nonverdict": (not quick) or prereg.get("quick_mode_is_verdict") is False,
        "cells_complete": row_cells == expected_cells,
        "selection_rows_present": bool(selection_rows),
        "validation_units_per_cell_complete": arm_cell_units_ok,
        "obs72_yaw_sideslip_tire_telemetry_complete": obs_telemetry_ok,
        "oracle_adequacy_gate_passed": all(selection_adequacy.values()) if cell_readouts else False,
        "paired_ci_readouts_present": all(
            readout["oracle_minus_fixed_star"]["n_pairs"] >= expected_units
            and readout["oracle_minus_per_instance_tuned_reflex"]["n_pairs"] >= expected_units
            for readout in cell_readouts
        ),
        "track_f_admitted_false": True,
    }
    gates["all_passed"] = all(gates.values())
    verdict = "quick_smoke_passed" if quick and gates["all_passed"] else "quick_smoke_failed" if quick else (
        "drift_pricing_completed" if gates["all_passed"] else "drift_pricing_protocol_failed"
    )
    positive_cells = [
        readout["cell_id"]
        for readout in cell_readouts
        if readout["oracle_minus_per_instance_tuned_reflex"]["ci95_low"] > 0.0
    ]
    return {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": "quick" if quick else "full",
        "created_at_utc": utc_timestamp(),
        "elapsed_s": round(float(elapsed_s), 1),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "rows_csv": str((ROWS_QUICK_CSV if quick else ROWS_FULL_CSV).relative_to(REPO_ROOT)),
        "metrics_csv": str((METRICS_QUICK_CSV if quick else METRICS_FULL_CSV).relative_to(REPO_ROOT)),
        "row_count": len(rows),
        "selection_row_count": len(selection_rows),
        "validation_row_count": len(validation_rows),
        "protocol_gates": gates,
        "selection_adequacy_by_cell": selection_adequacy,
        "cell_readouts": cell_readouts,
        "decision": {
            "e4_verdict": verdict,
            "positive_drift_prize_cells": positive_cells,
            "track_f_admitted": False,
            "f2_training_admitted": False,
            "next_admitted_step": (
                "E4 full pricing is complete; Track F/F2 still require F1 infrastructure and explicit PI approval."
                if not quick and gates["all_passed"]
                else "Quick mode is only a protocol smoke; run full E4 before interpreting drift pricing."
            ),
        },
    }


def write_metrics(path: Path, summary: dict[str, Any]) -> None:
    rows = [
        {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
        {"metric": "quick_mode_is_verdict", "value": 0.0},
        {"metric": "track_f_admitted", "value": 1.0 if summary["decision"]["track_f_admitted"] else 0.0},
        {"metric": "f2_training_admitted", "value": 1.0 if summary["decision"]["f2_training_admitted"] else 0.0},
        {"metric": "validation_row_count", "value": float(summary["validation_row_count"])},
    ]
    for readout in summary["cell_readouts"]:
        rows.extend(
            [
                {"metric": f"{readout['cell_id']}.validation_units", "value": float(readout["validation_units"])},
                {
                    "metric": f"{readout['cell_id']}.oracle_minus_fixed_star",
                    "value": float(readout["oracle_minus_fixed_star"]["mean"]),
                },
                {
                    "metric": f"{readout['cell_id']}.oracle_minus_per_tuned",
                    "value": float(readout["oracle_minus_per_instance_tuned_reflex"]["mean"]),
                },
                {
                    "metric": f"{readout['cell_id']}.oracle_minus_per_tuned_ci95_low",
                    "value": float(readout["oracle_minus_per_instance_tuned_reflex"]["ci95_low"]),
                },
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary: dict[str, Any]) -> None:
    lines = [
        "# M3260 Phase-4 E4 Drift Regime Pricing",
        "",
        "Status: completed. This is pricing evidence only; it does not open Track F/F2 and does not mutate the incumbent.",
        "",
        "## Measured",
        "",
        f"- Verdict: `{summary['decision']['e4_verdict']}`.",
        f"- Protocol gates passed: `{str(summary['protocol_gates']['all_passed']).lower()}`.",
        f"- Rows: {summary['row_count']} total, {summary['selection_row_count']} selection, {summary['validation_row_count']} validation.",
        f"- Track F admitted: `{str(summary['decision']['track_f_admitted']).lower()}`.",
        "",
        "| cell | units | fixed* success | per-tuned success | native success | drift-specialized success | oracle-fixed | oracle-per-tuned | dominant reflex failures |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for readout in summary["cell_readouts"]:
        modes = ", ".join(f"{key}:{value}" for key, value in sorted(readout["reflex_failure_modes"].items())) or "none"
        lines.append(
            "| "
            f"{readout['cell_id']} | {readout['validation_units']} | "
            f"{readout['arm_success_rate']['fixed_star']:.3f} | "
            f"{readout['arm_success_rate']['per_instance_tuned_reflex']:.3f} | "
            f"{readout['arm_success_rate']['native_chrono_oracle']:.3f} | "
            f"{readout['arm_success_rate']['drift_specialized_oracle']:.3f} | "
            f"{readout['oracle_minus_fixed_star']['mean']:.3f} "
            f"[{readout['oracle_minus_fixed_star']['ci95_low']:.3f}, {readout['oracle_minus_fixed_star']['ci95_high']:.3f}] | "
            f"{readout['oracle_minus_per_instance_tuned_reflex']['mean']:.3f} "
            f"[{readout['oracle_minus_per_instance_tuned_reflex']['ci95_low']:.3f}, {readout['oracle_minus_per_instance_tuned_reflex']['ci95_high']:.3f}] | "
            f"{modes} |"
        )
    lines += [
        "",
        "## Inferred",
        "",
        "E4 characterizes where the reflex family fails in drift-specific Chrono cells using actor-visible sideslip/yaw plus rear-tire saturation telemetry. Positive oracle gaps are only pricing signals for later PI-gated Track F/F2 planning; neutral or negative gaps remain full-fidelity negative evidence.",
        "",
        "## Claim Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Artifacts",
        "",
        f"- Preregistration: `{summary['preregistration']}`",
        f"- Full JSON: `{str(FULL_JSON.relative_to(REPO_ROOT))}`",
        f"- Rows: `{summary['rows_csv']}`",
        f"- Metrics: `{summary['metrics_csv']}`",
        f"- Script: `scripts/feasibility_audit/{Path(__file__).name}`",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_quick_smoke_decision(summary: dict[str, Any]) -> None:
    summary["quick_mode_is_verdict"] = False
    summary["decision"]["e4_verdict"] = "quick_smoke_passed" if summary["protocol_gates"]["all_passed"] else "quick_smoke_failed"
    summary["decision"]["positive_drift_prize_cells"] = []
    summary["decision"]["track_f_admitted"] = False
    summary["decision"]["f2_training_admitted"] = False
    summary["decision"]["next_admitted_step"] = "Run full E4 before interpreting drift pricing or changing Track F/F2 status."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.quick and args.full:
        raise SystemExit("--quick and --full are mutually exclusive")
    if args.write_prereg:
        payload = write_preregistration()
        print(json.dumps({"wrote": str(PREREG_JSON), "cells": len(payload["cells"])}, sort_keys=True))
    if args.quick or args.full:
        prereg = load_preregistration()
        summary = run_rollout(prereg=prereg, quick=bool(args.quick), resume=bool(args.resume))
        if args.quick:
            apply_quick_smoke_decision(summary)
            write_json(QUICK_JSON, summary)
        print(json.dumps(summary["decision"], sort_keys=True))
    if not (args.write_prereg or args.quick or args.full):
        raise SystemExit("choose --write-prereg, --quick, or --full")


if __name__ == "__main__":
    main()
