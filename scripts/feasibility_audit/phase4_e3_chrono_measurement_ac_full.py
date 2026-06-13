"""Phase-4 E3 full Chrono measurement A/C panel.

M3255 is the full E3 safety-measurement milestone after the M3253 A/C protocol
smoke and the M3254 tire-truth telemetry connector smoke. It freezes and runs:

* measurement A: obs72 detector latency against Chrono tire-truth onset;
* measurement C: reflex recoverable-set budget from injected planar overshoot
  states, with baseline_coast and the frozen v4 incumbent measured on paired
  cells.

This is a full Track-E measurement verdict, not a training or promotion run.
It does not mutate obs72/action3, does not edit the incumbent, and cannot open
Track F without the PI CP-3 checkpoint.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_full.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_full.py --quick --resume
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_full.py --full --resume
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.artifacts import utc_timestamp, write_json  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_e3_chrono_measurement_ac_smoke as ac_smoke  # noqa: E402


MILESTONE_ID = "m3255-phase4-e3-chrono-measurement-ac-full"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_full_prereg.json"
FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_full.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_full_quick.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_full"
LATENCY_ROWS_FULL_CSV = RUN_DIR / "latency_rows_full.csv"
RECOVERY_ROWS_FULL_CSV = RUN_DIR / "recovery_rows_full.csv"
LATENCY_ROWS_QUICK_CSV = RUN_DIR / "latency_rows_quick.csv"
RECOVERY_ROWS_QUICK_CSV = RUN_DIR / "recovery_rows_quick.csv"
METRICS_FULL_CSV = RUN_DIR / "metrics_full.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
STDERR_FULL_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
STDERR_QUICK_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
DOC_PATH = REPO_ROOT / "docs" / "m3255-phase4-e3-chrono-measurement-ac-full.md"

E0_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_spread_expressibility_audit.json"
E2_FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2_chrono_two_regime_full.json"
E3_SMOKE_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_quick.json"
TIRE_SMOKE_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_tire_telemetry_quick.json"

SEED_BASE = 2026061307
VARIANT = "sedan_tmeasy"
DT = 0.02
TRACK_RADIUS = 900.0
TRACK_WIDTH_A = 30.0
TRACK_WIDTH_C = 5.0
SPEED_MPS = 8.0
MAX_STEPS_A = 180
MAX_STEPS_C = 180
STABLE_RUN_STEPS = 10

A_MU_VALUES = (0.45, 0.5875, 0.85)
A_RATES = {"long": (0.20, 0.30), "lat": (0.18, 0.25)}
A_TAU = {"long": 0.15, "lat": 0.03}
A_SEED_INDICES = (0, 1)
A_TRUTH_THRESHOLDS = {"long": 0.25, "lat": 0.05}
A_TRUTH_PERSIST_STEPS = 2
A_TRUTH_MIN_STEP = 10
A_SAFETY_MISS_RATE_MAX = 0.25
A_SAFETY_P90_LATENCY_STEPS_MAX = 150

C_MU_VALUES = (0.45, 0.5875, 0.85)
C_OVERSHOOTS = (1.05, 1.15, 1.30)
C_OFFSETS_M = (0.5, 1.5)
C_DRIVERS = ("baseline_coast", "v4_incumbent")
C_SEED_INDICES = (0, 1)
C_LOW_MID_OVERSHOOT_MAX = 1.15

CLAIM_BOUNDARY = (
    "Phase-4 E3 full Chrono measurement A/C only: measurement A compares the "
    "obs72 shortfall detector to frozen Chrono tire-truth onset definitions, "
    "and measurement C quantifies the baseline/v4 recoverable-set budget from "
    "frozen injected planar overshoot states on Sedan/TMeasy. This is zero "
    "training and makes no incumbent mutation, validation ranking, promotion, "
    "driver-performance, full high-fidelity sufficiency, paper, repair-success, "
    "robustness-result, feasibility-proof, Track-F-admission, or self-ID claim."
)

LATENCY_FIELDNAMES = [
    "case_id",
    "axis",
    "mu",
    "rate",
    "seed_index",
    "seed",
    "truth_threshold",
    "truth_onset_step",
    "detector_fired_step",
    "detector_armed_step",
    "latency_steps",
    "latency_s",
    "missed_detection",
    "early_fire",
    "truth_signal_peak",
    "obs_signal_peak",
    "steps",
    "outcome",
    "reset_obs_finite",
    "runtime_obs_finite_all",
    "variant_match",
    "telemetry_available_all",
    "wheel_count_all_four",
    "final_speed",
    "claim_boundary",
]

RECOVERY_FIELDNAMES = [
    "case_id",
    "mu",
    "overshoot",
    "offset_m",
    "driver",
    "seed_index",
    "seed",
    "recovered",
    "recovery_step",
    "recovery_time_s",
    "stable_run_max",
    "steps",
    "outcome",
    "terminated",
    "truncated",
    "status",
    "reset_obs_finite",
    "runtime_obs_finite_all",
    "variant_match",
    "telemetry_available_all",
    "wheel_count_all_four",
    "max_abs_tire_slip_angle_rad",
    "max_abs_tire_longitudinal_slip",
    "max_tire_normal_load_n",
    "min_tire_normal_load_n",
    "final_lateral_error",
    "final_speed",
    "claim_boundary",
]


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


def _stable_hash(payload: Any) -> str:
    text = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _seed_for(*parts: Any) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little") % 2_000_000_000


def _as_float(value: Any) -> float:
    try:
        number = float(value)
    except Exception:
        return float("nan")
    return number if math.isfinite(number) else float("nan")


def _as_int(value: Any, default: int = -1) -> int:
    number = _as_float(value)
    return int(number) if math.isfinite(number) else default


def _is_true(value: Any) -> bool:
    return value is True or str(value) == "True"


def _finite_obs(obs: np.ndarray) -> bool:
    return obs.shape == (72,) and bool(np.all(np.isfinite(obs)))


def _format_float(value: Any) -> str:
    number = _as_float(value)
    return "nan" if not math.isfinite(number) else f"{number:.6g}"


def percentile(values: list[float], q: float) -> float:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return float("nan")
    if len(finite) == 1:
        return finite[0]
    pos = (len(finite) - 1) * float(q)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return finite[lo]
    return finite[lo] * (hi - pos) + finite[hi] * (pos - lo)


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _jsonable(row.get(key, "")) for key in fieldnames})


def _append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({key: _jsonable(row.get(key, "")) for key in fieldnames})


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _progress(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def build_measurement_a_cases(*, quick: bool = False) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for axis in ("long", "lat"):
        mus = A_MU_VALUES[:1] if quick else A_MU_VALUES
        rates = A_RATES[axis][:1] if quick else A_RATES[axis]
        seeds = A_SEED_INDICES[:1] if quick else A_SEED_INDICES
        for mu in mus:
            for rate in rates:
                for seed_index in seeds:
                    cases.append(
                        {
                            "case_id": f"A_{axis}_mu{mu:g}_rate{rate:g}_s{seed_index}",
                            "axis": axis,
                            "mu": float(mu),
                            "rate": float(rate),
                            "tau": float(A_TAU[axis]),
                            "truth_threshold": float(A_TRUTH_THRESHOLDS[axis]),
                            "seed_index": int(seed_index),
                            "seed": _seed_for("A", axis, mu, rate, seed_index),
                        }
                    )
    return cases


def build_measurement_c_cases(*, quick: bool = False) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    mus = C_MU_VALUES[:1] if quick else C_MU_VALUES
    overshoots = C_OVERSHOOTS[:2] if quick else C_OVERSHOOTS
    offsets = C_OFFSETS_M[:1] if quick else C_OFFSETS_M
    drivers = C_DRIVERS if quick else C_DRIVERS
    seeds = C_SEED_INDICES[:1] if quick else C_SEED_INDICES
    for mu in mus:
        for overshoot in overshoots:
            for offset_m in offsets:
                for driver in drivers:
                    for seed_index in seeds:
                        cases.append(
                            {
                                "case_id": f"C_mu{mu:g}_o{overshoot:g}_off{offset_m:g}_{driver}_s{seed_index}",
                                "mu": float(mu),
                                "overshoot": float(overshoot),
                                "offset_m": float(offset_m),
                                "driver": driver,
                                "speed_mps": SPEED_MPS,
                                "seed_index": int(seed_index),
                                "seed": _seed_for("C", mu, overshoot, offset_m, driver, seed_index),
                            }
                        )
    return cases


def build_preregistration() -> dict[str, Any]:
    e0 = _read_json(E0_JSON)
    e2 = _read_json(E2_FULL_JSON)
    e3 = _read_json(E3_SMOKE_JSON)
    tire = _read_json(TIRE_SMOKE_JSON)
    if not e0.get("decision", {}).get("e1_preregistration_admitted"):
        raise RuntimeError("E0 did not admit the Chrono vehicle fixture envelope")
    if e2.get("decision", {}).get("e2_full_verdict") != "chrono_clean_belief_value_positive":
        raise RuntimeError("M3252 full E2 is not available as the E3 predecessor")
    if e3.get("decision", {}).get("e3_quick_verdict") != "protocol_smoke_passed":
        raise RuntimeError("M3253 E3 A/C protocol smoke did not pass")
    if tire.get("decision", {}).get("telemetry_quick_verdict") != "tire_telemetry_smoke_passed":
        raise RuntimeError("M3254 tire telemetry connector smoke did not pass")
    a_cases = build_measurement_a_cases()
    c_cases = build_measurement_c_cases()
    quick_a_cases = build_measurement_a_cases(quick=True)
    quick_c_cases = build_measurement_c_cases(quick=True)
    return {
        "protocol": "phase4_e3_chrono_measurement_ac_full_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 E3 full Chrono measurements A/C",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_full_e3_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "dependencies": {
            "e0_artifact": str(E0_JSON.relative_to(REPO_ROOT)),
            "e2_full_artifact": str(E2_FULL_JSON.relative_to(REPO_ROOT)),
            "e3_smoke_artifact": str(E3_SMOKE_JSON.relative_to(REPO_ROOT)),
            "tire_telemetry_smoke_artifact": str(TIRE_SMOKE_JSON.relative_to(REPO_ROOT)),
        },
        "chrono_variant": VARIANT,
        "dt": DT,
        "measurement_a": {
            "description": "obs72 SlipOnsetDetector latency against Chrono tire-truth onset",
            "cases": a_cases,
            "quick_cases": quick_a_cases,
            "truth_definitions": {
                "long": "first step >= 10 where max_abs_tire_longitudinal_slip >= 0.25 for 2 consecutive steps",
                "lat": "first step >= 10 where max_abs_tire_slip_angle_rad >= 0.05 for 2 consecutive steps",
                "truth_min_step": A_TRUTH_MIN_STEP,
                "truth_persist_steps": A_TRUTH_PERSIST_STEPS,
            },
            "safety_gating_thresholds": {
                "miss_rate_max": A_SAFETY_MISS_RATE_MAX,
                "p90_latency_steps_max": A_SAFETY_P90_LATENCY_STEPS_MAX,
                "p90_latency_s_max": A_SAFETY_P90_LATENCY_STEPS_MAX * DT,
            },
        },
        "measurement_c": {
            "description": "paired baseline_coast and v4_incumbent recovery from frozen planar overshoot states",
            "cases": c_cases,
            "quick_cases": quick_c_cases,
            "recovery_definition": {
                "stable_run_steps": STABLE_RUN_STEPS,
                "stable_beta_rad": 0.08,
                "stable_yaw_surplus_radps": 0.20,
                "stable_lateral_error_m": 2.5,
                "stable_min_speed_mps": 1.5,
                "horizon_steps": MAX_STEPS_C,
            },
            "safety_gating_readouts": [
                "baseline_coast recovery rate by overshoot tier",
                "v4_incumbent recovery rate by overshoot tier",
                "v4 minus baseline paired recovery delta for overshoot <= 1.15",
            ],
        },
        "expected_full_latency_rows": len(a_cases),
        "expected_full_recovery_rows": len(c_cases),
        "expected_quick_latency_rows": len(quick_a_cases),
        "expected_quick_recovery_rows": len(quick_c_cases),
        "runtime_gates": [
            "all frozen measurement A and C rows are written",
            "reset and runtime obs are finite obs72",
            "backend_info variant ids match Sedan/TMeasy",
            "tire telemetry is available with four wheel rows whenever sampled through diagnostics",
            "measurement A writes tire-truth onset and obs72 detector latency readouts",
            "measurement C writes paired baseline/v4 recovery readouts",
            "Track F remains blocked pending PI CP-3",
        ],
        "decision_rule": (
            "M3255 completes full E3 iff row-count and protocol gates pass. "
            "Detector-latency and recovery-budget safety readouts are reported as measured; "
            "negative safety readouts do not become protocol failures and do not admit Track F."
        ),
    }


def write_preregistration() -> dict[str, Any]:
    payload = build_preregistration()
    write_json(PREREG_JSON, payload)
    return payload


def load_preregistration() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise FileNotFoundError(f"missing preregistration {PREREG_JSON}; run --write-prereg first")
    payload = _read_json(PREREG_JSON)
    if not payload.get("frozen_before_any_full_e3_rollout"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_full_e3_rollout")
    return payload


def _truth_signal(axis: str, info: dict[str, Any]) -> float:
    if axis == "long":
        return _as_float(info.get("max_abs_tire_longitudinal_slip", "nan"))
    if axis == "lat":
        return _as_float(info.get("max_abs_tire_slip_angle_rad", "nan"))
    raise ValueError(f"unknown axis {axis!r}")


def _scenario_a(case: dict[str, Any]) -> dict[str, Any]:
    return ac_smoke.base_scenario(
        case_id=f"m3255-{case['case_id']}",
        mu=float(case["mu"]),
        speed_mps=SPEED_MPS,
        max_steps=MAX_STEPS_A,
        track_width=TRACK_WIDTH_A,
    )


def _scenario_c(case: dict[str, Any]) -> dict[str, Any]:
    scenario = ac_smoke.overshoot_scenario(
        case_id=f"m3255-{case['case_id']}",
        mu=float(case["mu"]),
        speed_mps=float(case["speed_mps"]),
        overshoot=float(case["overshoot"]),
        offset_m=float(case["offset_m"]),
    )
    scenario["max_steps"] = MAX_STEPS_C
    scenario["track_width"] = TRACK_WIDTH_C
    return scenario


def run_measurement_a_case(client: ChronoWorkerClient, case: dict[str, Any]) -> dict[str, Any]:
    axis = str(case["axis"])
    scenario = _scenario_a(case)
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(case["seed"]))
    controller: Any = (
        ac_smoke.BrakeRampController(float(case["rate"]))
        if axis == "long"
        else ac_smoke.SteerRampController(float(case["rate"]), SPEED_MPS)
    )
    detector = ac_smoke.SlipOnsetDetector(axis, float(case["tau"]))
    reset_finite = _finite_obs(obs)
    variant_match = reset_reply.get("backend_info", {}).get("chrono_vehicle_variant") == VARIANT
    runtime_obs_finite_all = reset_finite
    telemetry_available_all = bool(reset_reply.get("info", {}).get("tire_telemetry_available", False))
    wheel_count_all_four = int(reset_reply.get("info", {}).get("tire_telemetry_wheel_count", 0)) == 4
    truth_onset_step: int | None = None
    truth_run = 0
    truth_signal_peak = _truth_signal(axis, dict(reset_reply.get("info", {})))
    obs_det = detector.step(obs)
    obs_signal_peak = float(obs_det["signal"])
    info = dict(reset_reply.get("info", {}))
    status = "reset"
    terminated = truncated = False
    steps = 0
    while not (terminated or truncated) and steps < MAX_STEPS_A:
        action = controller.act(obs)
        obs, terminated, truncated, status, info = client.step(action)
        obs_ok = _finite_obs(obs)
        runtime_obs_finite_all = runtime_obs_finite_all and obs_ok
        telemetry_available_all = telemetry_available_all and bool(info.get("tire_telemetry_available", False))
        wheel_count_all_four = wheel_count_all_four and int(info.get("tire_telemetry_wheel_count", 0)) == 4
        signal = _truth_signal(axis, info)
        truth_signal_peak = max(truth_signal_peak, signal)
        if steps + 1 >= A_TRUTH_MIN_STEP and signal >= float(case["truth_threshold"]):
            truth_run += 1
            if truth_onset_step is None and truth_run >= A_TRUTH_PERSIST_STEPS:
                truth_onset_step = steps + 2 - A_TRUTH_PERSIST_STEPS
        else:
            truth_run = 0
        if obs_ok:
            obs_det = detector.step(obs)
            obs_signal_peak = max(obs_signal_peak, float(obs_det["signal"]))
        steps += 1
        if not obs_ok:
            break
    fired_step = -1 if detector.fired_step is None else int(detector.fired_step)
    onset_step = -1 if truth_onset_step is None else int(truth_onset_step)
    missed = truth_onset_step is not None and detector.fired_step is None
    latency_steps = "" if truth_onset_step is None or detector.fired_step is None else int(detector.fired_step - truth_onset_step)
    latency_s = "" if latency_steps == "" else float(latency_steps) * DT
    early_fire = bool(truth_onset_step is not None and detector.fired_step is not None and detector.fired_step < truth_onset_step)
    return {
        "case_id": case["case_id"],
        "axis": axis,
        "mu": float(case["mu"]),
        "rate": float(case["rate"]),
        "seed_index": int(case["seed_index"]),
        "seed": int(case["seed"]),
        "truth_threshold": float(case["truth_threshold"]),
        "truth_onset_step": onset_step,
        "detector_fired_step": fired_step,
        "detector_armed_step": -1 if detector.armed_step is None else int(detector.armed_step),
        "latency_steps": latency_steps,
        "latency_s": latency_s,
        "missed_detection": bool(missed),
        "early_fire": bool(early_fire),
        "truth_signal_peak": round(float(truth_signal_peak), 6),
        "obs_signal_peak": round(float(obs_signal_peak), 6),
        "steps": int(steps),
        "outcome": str(info.get("completion_reason") or info.get("termination_reason") or status),
        "reset_obs_finite": bool(reset_finite),
        "runtime_obs_finite_all": bool(runtime_obs_finite_all),
        "variant_match": bool(variant_match),
        "telemetry_available_all": bool(telemetry_available_all),
        "wheel_count_all_four": bool(wheel_count_all_four),
        "final_speed": info.get("speed", ""),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def run_measurement_c_case(client: ChronoWorkerClient, case: dict[str, Any]) -> dict[str, Any]:
    scenario = _scenario_c(case)
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(case["seed"]))
    act = ac_smoke._recovery_action(str(case["driver"]))
    reset_finite = _finite_obs(obs)
    variant_match = reset_reply.get("backend_info", {}).get("chrono_vehicle_variant") == VARIANT
    runtime_obs_finite_all = reset_finite
    info = dict(reset_reply.get("info", {}))
    telemetry_available_all = bool(info.get("tire_telemetry_available", False))
    wheel_count_all_four = int(info.get("tire_telemetry_wheel_count", 0)) == 4
    max_slip_angle = _as_float(info.get("max_abs_tire_slip_angle_rad", "nan"))
    max_long_slip = _as_float(info.get("max_abs_tire_longitudinal_slip", "nan"))
    max_normal_load = _as_float(info.get("max_tire_normal_load_n", "nan"))
    min_normal_load = _as_float(info.get("min_tire_normal_load_n", "nan"))
    stable_run = 0
    stable_run_max = 0
    recovered = False
    recovery_step = -1
    steps = 0
    terminated = truncated = False
    status = "reset"
    while not (terminated or truncated) and steps < MAX_STEPS_C:
        obs, terminated, truncated, status, info = client.step(act(obs))
        obs_ok = _finite_obs(obs)
        runtime_obs_finite_all = runtime_obs_finite_all and obs_ok
        telemetry_available_all = telemetry_available_all and bool(info.get("tire_telemetry_available", False))
        wheel_count_all_four = wheel_count_all_four and int(info.get("tire_telemetry_wheel_count", 0)) == 4
        max_slip_angle = max(max_slip_angle, _as_float(info.get("max_abs_tire_slip_angle_rad", "nan")))
        max_long_slip = max(max_long_slip, _as_float(info.get("max_abs_tire_longitudinal_slip", "nan")))
        max_normal_load = max(max_normal_load, _as_float(info.get("max_tire_normal_load_n", "nan")))
        normal_min_now = _as_float(info.get("min_tire_normal_load_n", "nan"))
        if math.isfinite(normal_min_now):
            min_normal_load = min(min_normal_load, normal_min_now) if math.isfinite(min_normal_load) else normal_min_now
        if not obs_ok:
            break
        steps += 1
        stable_run = stable_run + 1 if ac_smoke._stable_from_info(info) else 0
        stable_run_max = max(stable_run_max, stable_run)
        if stable_run >= STABLE_RUN_STEPS:
            recovered = True
            recovery_step = steps - STABLE_RUN_STEPS + 1
            break
    return {
        "case_id": case["case_id"],
        "mu": float(case["mu"]),
        "overshoot": float(case["overshoot"]),
        "offset_m": float(case["offset_m"]),
        "driver": str(case["driver"]),
        "seed_index": int(case["seed_index"]),
        "seed": int(case["seed"]),
        "recovered": bool(recovered),
        "recovery_step": int(recovery_step),
        "recovery_time_s": "" if recovery_step < 0 else float(recovery_step) * DT,
        "stable_run_max": int(stable_run_max),
        "steps": int(steps),
        "outcome": "recovered" if recovered else str(info.get("termination_reason") or info.get("completion_reason") or status),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "status": str(status),
        "reset_obs_finite": bool(reset_finite),
        "runtime_obs_finite_all": bool(runtime_obs_finite_all),
        "variant_match": bool(variant_match),
        "telemetry_available_all": bool(telemetry_available_all),
        "wheel_count_all_four": bool(wheel_count_all_four),
        "max_abs_tire_slip_angle_rad": max_slip_angle,
        "max_abs_tire_longitudinal_slip": max_long_slip,
        "max_tire_normal_load_n": max_normal_load,
        "min_tire_normal_load_n": min_normal_load,
        "final_lateral_error": info.get("lateral_error", ""),
        "final_speed": info.get("speed", ""),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _row_keys(rows: Iterable[dict[str, Any]]) -> set[str]:
    return {str(row.get("case_id", "")) for row in rows}


def run_panel(*, mode: str, resume: bool) -> dict[str, Any]:
    prereg = load_preregistration()
    quick = mode == "quick"
    latency_path = LATENCY_ROWS_QUICK_CSV if quick else LATENCY_ROWS_FULL_CSV
    recovery_path = RECOVERY_ROWS_QUICK_CSV if quick else RECOVERY_ROWS_FULL_CSV
    metrics_path = METRICS_QUICK_CSV if quick else METRICS_FULL_CSV
    summary_path = QUICK_JSON if quick else FULL_JSON
    progress_path = PROGRESS_QUICK_JSONL if quick else PROGRESS_FULL_JSONL
    stderr_log = STDERR_QUICK_LOG if quick else STDERR_FULL_LOG
    if not resume:
        for path in (latency_path, recovery_path, metrics_path, summary_path, progress_path):
            if path.exists():
                path.unlink()
        if not quick and DOC_PATH.exists():
            DOC_PATH.unlink()
    a_cases = prereg["measurement_a"]["quick_cases" if quick else "cases"]
    c_cases = prereg["measurement_c"]["quick_cases" if quick else "cases"]
    done_a = _row_keys(_read_csv(latency_path))
    done_c = _row_keys(_read_csv(recovery_path))
    started = time.time()
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        for case in a_cases:
            if str(case["case_id"]) in done_a:
                continue
            row = run_measurement_a_case(client, case)
            _append_csv(latency_path, row, LATENCY_FIELDNAMES)
            _progress(progress_path, {"stage": "measurement_a_done", "case_id": row["case_id"], "latency_steps": row["latency_steps"]})
        for case in c_cases:
            if str(case["case_id"]) in done_c:
                continue
            row = run_measurement_c_case(client, case)
            _append_csv(recovery_path, row, RECOVERY_FIELDNAMES)
            _progress(progress_path, {"stage": "measurement_c_done", "case_id": row["case_id"], "recovered": row["recovered"]})
    finally:
        client.close()
    summary = summarize_panel(
        _read_csv(latency_path),
        _read_csv(recovery_path),
        prereg,
        mode=mode,
        elapsed_s=time.time() - started,
        latency_path=latency_path,
        recovery_path=recovery_path,
        metrics_path=metrics_path,
    )
    write_json(summary_path, summary)
    write_metrics(summary, metrics_path)
    if not quick:
        write_markdown(summary)
    return summary


def _rate(rows: list[dict[str, Any]], field: str) -> float:
    if not rows:
        return float("nan")
    return sum(1 for row in rows if _is_true(row.get(field))) / len(rows)


def summarize_panel(
    latency_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
    prereg: dict[str, Any],
    *,
    mode: str,
    elapsed_s: float,
    latency_path: Path,
    recovery_path: Path,
    metrics_path: Path,
) -> dict[str, Any]:
    expected_latency = prereg[f"expected_{mode}_latency_rows"]
    expected_recovery = prereg[f"expected_{mode}_recovery_rows"]
    latency_values = [_as_float(row.get("latency_steps", "")) for row in latency_rows if not _is_true(row.get("missed_detection"))]
    latency_s_values = [value * DT for value in latency_values if math.isfinite(value)]
    truth_onset_rate = sum(1 for row in latency_rows if _as_int(row.get("truth_onset_step")) >= 0) / len(latency_rows) if latency_rows else float("nan")
    miss_rate = _rate(latency_rows, "missed_detection")
    early_fire_rate = _rate(latency_rows, "early_fire")
    a_axis_summary = {}
    for axis in ("long", "lat"):
        axis_rows = [row for row in latency_rows if row.get("axis") == axis]
        axis_latencies = [_as_float(row.get("latency_steps", "")) for row in axis_rows if not _is_true(row.get("missed_detection"))]
        a_axis_summary[axis] = {
            "row_count": len(axis_rows),
            "truth_onset_rate": (
                sum(1 for row in axis_rows if _as_int(row.get("truth_onset_step")) >= 0) / len(axis_rows)
                if axis_rows
                else float("nan")
            ),
            "detector_fire_rate": (
                sum(1 for row in axis_rows if _as_int(row.get("detector_fired_step")) >= 0) / len(axis_rows)
                if axis_rows
                else float("nan")
            ),
            "median_latency_steps": median(axis_latencies) if axis_latencies else float("nan"),
            "p90_latency_steps": percentile(axis_latencies, 0.90),
        }
    v4_rows = [row for row in recovery_rows if row.get("driver") == "v4_incumbent"]
    baseline_rows = [row for row in recovery_rows if row.get("driver") == "baseline_coast"]
    c_by_overshoot: dict[str, dict[str, Any]] = {}
    for overshoot in sorted({_as_float(row.get("overshoot")) for row in recovery_rows if math.isfinite(_as_float(row.get("overshoot")))}):
        key = f"{overshoot:g}"
        over_rows = [row for row in recovery_rows if math.isclose(_as_float(row.get("overshoot")), overshoot)]
        over_v4 = [row for row in over_rows if row.get("driver") == "v4_incumbent"]
        over_baseline = [row for row in over_rows if row.get("driver") == "baseline_coast"]
        c_by_overshoot[key] = {
            "row_count": len(over_rows),
            "v4_recovery_rate": _rate(over_v4, "recovered"),
            "baseline_recovery_rate": _rate(over_baseline, "recovered"),
            "v4_minus_baseline": _rate(over_v4, "recovered") - _rate(over_baseline, "recovered"),
        }
    low_mid_v4 = [row for row in v4_rows if _as_float(row.get("overshoot")) <= C_LOW_MID_OVERSHOOT_MAX]
    low_mid_baseline = [row for row in baseline_rows if _as_float(row.get("overshoot")) <= C_LOW_MID_OVERSHOOT_MAX]
    safety_gates = {
        "measurement_a_miss_rate_le_threshold": bool(math.isfinite(miss_rate) and miss_rate <= A_SAFETY_MISS_RATE_MAX),
        "measurement_a_p90_latency_le_threshold": bool(
            math.isfinite(percentile(latency_values, 0.90))
            and percentile(latency_values, 0.90) <= A_SAFETY_P90_LATENCY_STEPS_MAX
        ),
        "measurement_a_early_fire_rate_reported": math.isfinite(early_fire_rate),
        "measurement_c_v4_low_mid_recovery_rate": _rate(low_mid_v4, "recovered"),
        "measurement_c_baseline_low_mid_recovery_rate": _rate(low_mid_baseline, "recovered"),
        "measurement_c_v4_minus_baseline_low_mid": _rate(low_mid_v4, "recovered") - _rate(low_mid_baseline, "recovered"),
    }
    protocol_gates = {
        "latency_row_count_complete": len(latency_rows) == expected_latency,
        "recovery_row_count_complete": len(recovery_rows) == expected_recovery,
        "latency_obs_finite_all": all(_is_true(row.get("reset_obs_finite")) and _is_true(row.get("runtime_obs_finite_all")) for row in latency_rows),
        "recovery_obs_finite_all": all(_is_true(row.get("reset_obs_finite")) and _is_true(row.get("runtime_obs_finite_all")) for row in recovery_rows),
        "variant_match_all": all(_is_true(row.get("variant_match")) for row in [*latency_rows, *recovery_rows]),
        "telemetry_available_all": all(_is_true(row.get("telemetry_available_all")) for row in [*latency_rows, *recovery_rows]),
        "wheel_count_all_four": all(_is_true(row.get("wheel_count_all_four")) for row in [*latency_rows, *recovery_rows]),
        "measurement_a_truth_onsets_observed": all(_as_int(row.get("truth_onset_step")) >= 0 for row in latency_rows),
        "measurement_c_drivers_present": {row.get("driver") for row in recovery_rows} == set(C_DRIVERS),
        "track_f_not_admitted": True,
    }
    protocol_gates["all_passed"] = all(protocol_gates.values())
    if mode == "quick":
        decision = {
            "quick_protocol_verdict": "full_e3_protocol_smoke_passed"
            if protocol_gates["all_passed"]
            else "full_e3_protocol_smoke_failed",
            "full_e3_verdict": "not_decided_by_quick_mode",
            "measurement_a_verdict": "not_decided_by_quick_mode",
            "measurement_c_verdict": "not_decided_by_quick_mode",
            "cp3_evidence_ready": False,
            "track_f_admitted": False,
            "next_admitted_step": "Run the separately preregistered full E3 panel; Track F remains blocked before full E3 plus PI CP-3.",
        }
    else:
        decision = {
            "full_e3_verdict": "chrono_safety_measurement_completed"
            if protocol_gates["all_passed"]
            else "chrono_safety_measurement_protocol_failed",
            "measurement_a_verdict": "detector_latency_table_completed"
            if protocol_gates["all_passed"]
            else "detector_latency_table_failed",
            "measurement_c_verdict": "recoverable_set_budget_completed"
            if protocol_gates["all_passed"]
            else "recoverable_set_budget_failed",
            "cp3_evidence_ready": bool(protocol_gates["all_passed"]),
            "track_f_admitted": False,
            "next_admitted_step": "PI CP-3 review of E1/E2/E3 targets and budget; Track F remains blocked before CP-3.",
        }
    return {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": mode,
        "created_at_utc": utc_timestamp(),
        "elapsed_s": round(float(elapsed_s), 1),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "latency_rows_csv": str(latency_path.relative_to(REPO_ROOT)),
        "recovery_rows_csv": str(recovery_path.relative_to(REPO_ROOT)),
        "metrics_csv": str(metrics_path.relative_to(REPO_ROOT)),
        "latency_row_count": len(latency_rows),
        "expected_latency_row_count": expected_latency,
        "recovery_row_count": len(recovery_rows),
        "expected_recovery_row_count": expected_recovery,
        "protocol_gates": protocol_gates,
        "safety_gating_readouts": safety_gates,
        "measurement_a_summary": {
            "truth_onset_rate": truth_onset_rate,
            "detector_miss_rate": miss_rate,
            "early_fire_rate": early_fire_rate,
            "median_latency_steps": median(latency_values) if latency_values else float("nan"),
            "p90_latency_steps": percentile(latency_values, 0.90),
            "median_latency_s": median(latency_s_values) if latency_s_values else float("nan"),
            "p90_latency_s": percentile(latency_s_values, 0.90),
            "by_axis": a_axis_summary,
        },
        "measurement_c_summary": {
            "v4_recovery_rate": _rate(v4_rows, "recovered"),
            "baseline_recovery_rate": _rate(baseline_rows, "recovered"),
            "v4_minus_baseline": _rate(v4_rows, "recovered") - _rate(baseline_rows, "recovered"),
            "by_overshoot": c_by_overshoot,
        },
        "decision": decision,
    }


def write_metrics(summary: dict[str, Any], metrics_path: Path) -> None:
    rows = [
        {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
        {"metric": "track_f_admitted", "value": 1.0 if summary["decision"]["track_f_admitted"] else 0.0},
        {"metric": "latency_row_count", "value": float(summary["latency_row_count"])},
        {"metric": "expected_latency_row_count", "value": float(summary["expected_latency_row_count"])},
        {"metric": "recovery_row_count", "value": float(summary["recovery_row_count"])},
        {"metric": "expected_recovery_row_count", "value": float(summary["expected_recovery_row_count"])},
        {"metric": "measurement_a_detector_miss_rate", "value": float(summary["measurement_a_summary"]["detector_miss_rate"])},
        {"metric": "measurement_a_p90_latency_s", "value": float(summary["measurement_a_summary"]["p90_latency_s"])},
        {"metric": "measurement_c_v4_recovery_rate", "value": float(summary["measurement_c_summary"]["v4_recovery_rate"])},
        {"metric": "measurement_c_baseline_recovery_rate", "value": float(summary["measurement_c_summary"]["baseline_recovery_rate"])},
        {"metric": "measurement_c_v4_minus_baseline", "value": float(summary["measurement_c_summary"]["v4_minus_baseline"])},
        {"metric": "cp3_evidence_ready", "value": 1.0 if summary["decision"]["cp3_evidence_ready"] else 0.0},
    ]
    _write_csv(metrics_path, rows, ["metric", "value"])


def write_markdown(summary: dict[str, Any]) -> None:
    a = summary["measurement_a_summary"]
    c = summary["measurement_c_summary"]
    lines = [
        "# M3255 Phase-4 E3 Chrono Measurement A/C Full",
        "",
        "Status: completed. This is the full E3 Chrono safety-measurement panel; it does not admit Track F without PI CP-3.",
        "",
        "## Verdict",
        "",
        f"- Full E3 verdict: **{summary['decision']['full_e3_verdict']}**.",
        f"- Protocol gates passed: **{str(summary['protocol_gates']['all_passed']).lower()}**.",
        f"- CP-3 evidence ready: **{str(summary['decision']['cp3_evidence_ready']).lower()}**.",
        f"- Track F admitted: **{str(summary['decision']['track_f_admitted']).lower()}**.",
        "",
        "## Measured",
        "",
        "| readout | value |",
        "|---|---:|",
        f"| Measurement A rows | {summary['latency_row_count']} / {summary['expected_latency_row_count']} |",
        f"| Measurement A truth-onset rate | {_format_float(a['truth_onset_rate'])} |",
        f"| Measurement A detector miss rate | {_format_float(a['detector_miss_rate'])} |",
        f"| Measurement A p90 latency | {_format_float(a['p90_latency_s'])} s |",
        f"| Measurement C rows | {summary['recovery_row_count']} / {summary['expected_recovery_row_count']} |",
        f"| Measurement C v4 recovery rate | {_format_float(c['v4_recovery_rate'])} |",
        f"| Measurement C baseline recovery rate | {_format_float(c['baseline_recovery_rate'])} |",
        f"| Measurement C v4 minus baseline | {_format_float(c['v4_minus_baseline'])} |",
        "",
        "## Measurement A By Axis",
        "",
        "| axis | rows | truth onset | fire rate | median latency | p90 latency |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for axis, row in a["by_axis"].items():
        lines.append(
            f"| {axis} | {row['row_count']} | {_format_float(row['truth_onset_rate'])} | "
            f"{_format_float(row['detector_fire_rate'])} | {_format_float(row['median_latency_steps'])} steps | "
            f"{_format_float(row['p90_latency_steps'])} steps |"
        )
    lines += [
        "",
        "## Measurement C By Overshoot",
        "",
        "| overshoot | rows | v4 recovery | baseline recovery | v4-baseline |",
        "|---:|---:|---:|---:|---:|",
    ]
    for overshoot, row in c["by_overshoot"].items():
        lines.append(
            f"| {overshoot} | {row['row_count']} | {_format_float(row['v4_recovery_rate'])} | "
            f"{_format_float(row['baseline_recovery_rate'])} | {_format_float(row['v4_minus_baseline'])} |"
        )
    lines += [
        "",
        "## Inferred",
        "",
        "Full E3 has now measured the Sedan/TMeasy Chrono detector-latency table and paired baseline/v4 recoverable-set budget under frozen tire-truth definitions. These data make the Track-E evidence package ready for PI CP-3 review, but they do not self-approve Track F targets or budget.",
        "",
        "## Claim Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Artifacts",
        "",
        f"- Preregistration: `{summary['preregistration']}`",
        f"- Full JSON: `{str(FULL_JSON.relative_to(REPO_ROOT))}`",
        f"- Latency rows: `{summary['latency_rows_csv']}`",
        f"- Recovery rows: `{summary['recovery_rows_csv']}`",
        f"- Metrics: `{summary['metrics_csv']}`",
        f"- Script: `scripts/feasibility_audit/{Path(__file__).name}`",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.write_prereg:
        payload = write_preregistration()
        print(
            json.dumps(
                {
                    "preregistration": str(PREREG_JSON),
                    "expected_full_latency_rows": payload["expected_full_latency_rows"],
                    "expected_full_recovery_rows": payload["expected_full_recovery_rows"],
                },
                sort_keys=True,
            )
        )
    if args.quick:
        summary = run_panel(mode="quick", resume=args.resume)
        print(json.dumps(summary["decision"], sort_keys=True))
    if args.full:
        summary = run_panel(mode="full", resume=args.resume)
        print(json.dumps(summary["decision"], sort_keys=True))
    if not args.write_prereg and not args.quick and not args.full:
        raise SystemExit("nothing to do; pass --write-prereg, --quick, or --full")


if __name__ == "__main__":
    main()
