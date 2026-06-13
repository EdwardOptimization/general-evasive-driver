"""Phase-4 E3 Chrono measurement-A/C protocol smoke.

M3253 is the first E3 milestone after M3252 completed full E2. It verifies
that the current Chrono worker interface can collect the inputs needed for:

* measurement A: obs72 slip-detector traces under scripted brake/steer ramps;
* measurement C: reflex recovery traces from injected planar overshoot states.

Quick mode is protocol evidence only. It is not the full Chrono detection-
latency table, not the full recoverable-set budget, and it cannot open Track F.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_smoke.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_smoke.py --quick --resume
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
from typing import Any, Callable

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.artifacts import utc_timestamp, write_json  # noqa: E402
from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
from slip_onset_detectability import SlipOnsetDetector, centerline_steer  # noqa: E402


MILESTONE_ID = "m3253-phase4-e3-chrono-measurement-ac-smoke"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_quick.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac"
ROWS_CSV = RUN_DIR / "episode_rows_quick.csv"
METRICS_CSV = RUN_DIR / "metrics_quick.csv"
PROGRESS_JSONL = RUN_DIR / "progress_quick.jsonl"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
DOC_PATH = REPO_ROOT / "docs" / "m3253-phase4-e3-chrono-measurement-ac-smoke.md"

E0_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_spread_expressibility_audit.json"
E2_FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2_chrono_two_regime_full.json"

SEED_BASE = 2026061305
VARIANT = "sedan_tmeasy"
DT = 0.02
TRACK_RADIUS = 900.0
TRACK_WIDTH = 30.0
MU = 0.5875
SPEED_MPS = 8.0
MAX_STEPS_A = 160
MAX_STEPS_C = 160
TAU_BY_AXIS = {"long": 0.15, "lat": 0.03}

CLAIM_BOUNDARY = (
    "Phase-4 E3 Chrono measurement-A/C protocol smoke only: scripted brake/steer "
    "ramps collect obs72 slip-detector traces, and injected planar overshoot states "
    "collect coast/v4 recovery traces on the default Chrono Sedan/TMeasy fixture. "
    "Quick mode is not a Chrono detection-latency verdict, not a full reflex "
    "recoverable-set budget, and makes no incumbent mutation, validation ranking, "
    "promotion, driver-performance, full high-fidelity sufficiency, paper, "
    "repair-success, robustness-result, feasibility-proof, Track-F-admission, or "
    "self-ID claim."
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


def _stable_hash(payload: Any) -> str:
    text = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _seed_for(*parts: Any) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little") % 2_000_000_000


def build_preregistration() -> dict[str, Any]:
    e0 = _read_json(E0_JSON)
    e2 = _read_json(E2_FULL_JSON)
    if not e0.get("decision", {}).get("e1_preregistration_admitted"):
        raise RuntimeError("E0 did not admit the Chrono vehicle fixture envelope")
    if e2.get("decision", {}).get("e2_full_verdict") != "chrono_clean_belief_value_positive":
        raise RuntimeError("M3252 full E2 is not available as the E3 predecessor")
    return {
        "protocol": "phase4_e3_chrono_measurement_ac_smoke_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 E3 Chrono measurements A/C protocol smoke",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_e3_chrono_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "e0_artifact": str(E0_JSON.relative_to(REPO_ROOT)),
        "e2_full_artifact": str(E2_FULL_JSON.relative_to(REPO_ROOT)),
        "quick_mode_is_verdict": False,
        "chrono_variant": VARIANT,
        "measurement_a_cases": [
            {"axis": "long", "rate": 0.30, "mu": MU, "speed_mps": SPEED_MPS, "tau": TAU_BY_AXIS["long"]},
            {"axis": "lat", "rate": 0.25, "mu": MU, "speed_mps": SPEED_MPS, "tau": TAU_BY_AXIS["lat"]},
        ],
        "measurement_c_cases": [
            {
                "driver": "baseline_coast",
                "mu": MU,
                "overshoot": 1.15,
                "speed_mps": SPEED_MPS,
                "offset_m": 1.5,
            },
            {
                "driver": "v4_incumbent",
                "mu": MU,
                "overshoot": 1.15,
                "speed_mps": SPEED_MPS,
                "offset_m": 1.5,
            },
        ],
        "runtime_gates": [
            "E0 artifact admits the Chrono fixture envelope",
            "M3252 full E2 artifact exists before E3 smoke",
            "measurement A writes long and lateral detector trace summaries",
            "measurement C writes baseline_coast and v4_incumbent recovery trace summaries",
            "reset obs are finite obs72 and backend_info variant ids match",
            "quick mode is explicitly non-verdict and cannot open Track F",
        ],
        "full_e3_placeholder": {
            "status": "not_registered_by_M3253",
            "needed_next": (
                "A full E3 milestone must freeze Chrono truth definitions for measurement A, "
                "overshoot-state construction for measurement C, cells, seed streams, paired "
                "readouts, and Track-F safety-gating thresholds before any E3 verdict."
            ),
        },
        "decision_rule": (
            "M3253 PASS iff all smoke rows run, detector/recovery summaries are finite, "
            "variant matches pass, and the artifact refuses a full A/C verdict or Track-F admission."
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
    if not payload.get("frozen_before_any_e3_chrono_rollout"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_e3_chrono_rollout")
    return payload


def base_scenario(*, case_id: str, mu: float, speed_mps: float, max_steps: int, track_width: float = TRACK_WIDTH) -> dict[str, Any]:
    return {
        "scenario_id": case_id,
        "dt": DT,
        "max_steps": int(max_steps),
        "track_kind": "circle",
        "track_radius": TRACK_RADIUS,
        "track_width": float(track_width),
        "road_lookahead_count": 8,
        "road_lookahead_spacing": 5.0,
        "obstacle_slots": 4,
        "obstacle_relative_velocity_mode": "ego",
        "soft_offtrack_metric_enabled": False,
        "soft_offtrack_tolerance_m": 0.0,
        "chrono_vehicle_variant": VARIANT,
        "params": {
            "mass": 1684.0,
            "mu": float(mu),
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
            "x": TRACK_RADIUS,
            "y": 0.0,
            "psi": math.pi / 2.0,
            "vx": float(speed_mps),
            "vy": 0.0,
            "yaw_rate": float(speed_mps) / TRACK_RADIUS,
        },
        "speed_ref": float(speed_mps),
        "obstacle": {"enabled": False},
        "warmup_gate": {"enabled": False},
        "friction_step": {"at": None, "new_mu": None},
        "terminate_on_failure": True,
    }


def overshoot_scenario(*, case_id: str, mu: float, speed_mps: float, overshoot: float, offset_m: float) -> dict[str, Any]:
    scenario = base_scenario(case_id=case_id, mu=mu, speed_mps=speed_mps, max_steps=MAX_STEPS_C, track_width=5.0)
    beta = -min(0.12 * float(overshoot), 0.35)
    heading_err = min(0.04 * float(overshoot), 0.18)
    yaw_rate = min(float(speed_mps) / TRACK_RADIUS + float(overshoot) * float(mu) * 9.81 / max(float(speed_mps), 1.0), 3.0)
    scenario["initial_state"] = {
        "x": TRACK_RADIUS + float(offset_m),
        "y": 0.0,
        "psi": math.pi / 2.0 + heading_err,
        "vx": float(speed_mps) * math.cos(beta),
        "vy": float(speed_mps) * math.sin(beta),
        "yaw_rate": yaw_rate,
    }
    return scenario


def _finite_obs(obs: np.ndarray) -> bool:
    return obs.shape == (72,) and bool(np.all(np.isfinite(obs)))


def _progress(payload: dict[str, Any]) -> None:
    PROGRESS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


class BrakeRampController:
    def __init__(self, rate: float):
        self.rate = float(rate)
        self.t = 0

    def act(self, obs: np.ndarray) -> np.ndarray:
        brake01 = float(np.clip(self.rate * self.t * DT, 0.0, 1.0))
        self.t += 1
        return np.asarray([centerline_steer(obs), -1.0, 2.0 * brake01 - 1.0], dtype=np.float32)


class SteerRampController:
    def __init__(self, rate: float, speed_target: float):
        self.rate = float(rate)
        self.speed_target = float(speed_target)
        self.t = 0

    def act(self, obs: np.ndarray) -> np.ndarray:
        vx = 20.0 * float(obs[0])
        err = self.speed_target - vx
        throttle01 = float(np.clip(0.5 * err, 0.0, 1.0)) if err >= -0.15 else 0.0
        brake01 = 0.0 if err >= -0.15 else float(np.clip(-0.5 * err, 0.0, 1.0))
        steer = float(np.clip(self.rate * self.t * DT, 0.0, 1.0))
        self.t += 1
        return np.asarray([steer, 2.0 * throttle01 - 1.0, 2.0 * brake01 - 1.0], dtype=np.float32)


def run_measurement_a_case(client: ChronoWorkerClient, case: dict[str, Any], *, seed: int) -> dict[str, Any]:
    axis = str(case["axis"])
    tau = float(case["tau"])
    scenario = base_scenario(
        case_id=f"m3253-A-{axis}-seed{seed}",
        mu=float(case["mu"]),
        speed_mps=float(case["speed_mps"]),
        max_steps=MAX_STEPS_A,
    )
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
    detector = SlipOnsetDetector(axis, tau)
    controller: Any = (
        BrakeRampController(float(case["rate"]))
        if axis == "long"
        else SteerRampController(float(case["rate"]), float(case["speed_mps"]))
    )
    reset_finite = _finite_obs(obs)
    variant_match = reset_reply.get("backend_info", {}).get("chrono_vehicle_variant") == VARIANT
    det = detector.step(obs)
    max_signal = float(det["signal"])
    min_signal = float(det["signal"])
    signal_half_tau_step: int | None = None
    terminated = truncated = False
    status = "reset"
    info = dict(reset_reply.get("info", {}))
    steps = 0
    while not (terminated or truncated) and steps < MAX_STEPS_A:
        action = controller.act(obs)
        obs, terminated, truncated, status, info = client.step(action)
        if not _finite_obs(obs):
            break
        det = detector.step(obs)
        max_signal = max(max_signal, float(det["signal"]))
        min_signal = min(min_signal, float(det["signal"]))
        if signal_half_tau_step is None and float(det["signal"]) > 0.5 * tau:
            signal_half_tau_step = steps + 1
        steps += 1
    return {
        "measurement": "A",
        "case_id": f"A_{axis}",
        "axis": axis,
        "driver": "",
        "seed": int(seed),
        "outcome": str(info.get("completion_reason") or info.get("termination_reason") or status),
        "steps": int(steps),
        "reset_obs_finite": reset_finite,
        "variant_match": variant_match,
        "detector_fired_step": -1 if detector.fired_step is None else int(detector.fired_step),
        "detector_armed_step": -1 if detector.armed_step is None else int(detector.armed_step),
        "signal_half_tau_step": -1 if signal_half_tau_step is None else int(signal_half_tau_step),
        "max_signal": round(max_signal, 6),
        "min_signal": round(min_signal, 6),
        "recovered": "",
        "recovery_step": "",
        "final_lateral_error": info.get("lateral_error", ""),
        "final_speed": info.get("speed", ""),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _recovery_action(driver: str) -> Callable[[np.ndarray], np.ndarray]:
    if driver == "baseline_coast":
        coast = np.asarray([0.0, -1.0, -1.0], dtype=np.float32)
        return lambda _obs: coast
    if driver == "v4_incumbent":
        v4 = ActiveSafetyReflexDriver()
        return lambda obs: np.asarray(v4.act(obs), dtype=np.float32)
    raise ValueError(f"unknown recovery driver {driver!r}")


def _stable_from_info(info: dict[str, Any]) -> bool:
    vx = float(info.get("vx_body", 0.0))
    vy = float(info.get("vy_body", 0.0))
    speed = float(info.get("speed", 0.0))
    beta = math.atan2(vy, max(vx, 1e-6))
    yaw_surplus = abs(float(info.get("yaw_rate", 0.0)) - vx / TRACK_RADIUS)
    return (
        abs(beta) <= 0.08
        and yaw_surplus <= 0.20
        and abs(float(info.get("lateral_error", 1e9))) <= 2.5
        and speed >= 1.5
    )


def run_measurement_c_case(client: ChronoWorkerClient, case: dict[str, Any], *, seed: int) -> dict[str, Any]:
    driver = str(case["driver"])
    scenario = overshoot_scenario(
        case_id=f"m3253-C-{driver}-seed{seed}",
        mu=float(case["mu"]),
        speed_mps=float(case["speed_mps"]),
        overshoot=float(case["overshoot"]),
        offset_m=float(case["offset_m"]),
    )
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
    act = _recovery_action(driver)
    reset_finite = _finite_obs(obs)
    variant_match = reset_reply.get("backend_info", {}).get("chrono_vehicle_variant") == VARIANT
    terminated = truncated = False
    status = "reset"
    info = dict(reset_reply.get("info", {}))
    stable_run = 0
    recovered = False
    recovery_step = -1
    steps = 0
    while not (terminated or truncated) and steps < MAX_STEPS_C:
        obs, terminated, truncated, status, info = client.step(act(obs))
        if not _finite_obs(obs):
            break
        steps += 1
        stable_run = stable_run + 1 if _stable_from_info(info) else 0
        if stable_run >= 10:
            recovered = True
            recovery_step = steps - 9
            break
    return {
        "measurement": "C",
        "case_id": f"C_{driver}",
        "axis": "",
        "driver": driver,
        "seed": int(seed),
        "outcome": "recovered" if recovered else str(info.get("termination_reason") or info.get("completion_reason") or status),
        "steps": int(steps),
        "reset_obs_finite": reset_finite,
        "variant_match": variant_match,
        "detector_fired_step": "",
        "detector_armed_step": "",
        "signal_half_tau_step": "",
        "max_signal": "",
        "min_signal": "",
        "recovered": bool(recovered),
        "recovery_step": int(recovery_step),
        "final_lateral_error": info.get("lateral_error", ""),
        "final_speed": info.get("speed", ""),
        "claim_boundary": CLAIM_BOUNDARY,
    }


FIELDNAMES = [
    "measurement",
    "case_id",
    "axis",
    "driver",
    "seed",
    "outcome",
    "steps",
    "reset_obs_finite",
    "variant_match",
    "detector_fired_step",
    "detector_armed_step",
    "signal_half_tau_step",
    "max_signal",
    "min_signal",
    "recovered",
    "recovery_step",
    "final_lateral_error",
    "final_speed",
    "claim_boundary",
]


def _write_rows(rows: list[dict[str, Any]]) -> None:
    ROWS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with ROWS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _jsonable(row.get(key, "")) for key in FIELDNAMES})


def _read_rows() -> list[dict[str, str]]:
    if not ROWS_CSV.exists():
        return []
    with ROWS_CSV.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def expected_case_count(prereg: dict[str, Any]) -> int:
    return len(prereg["measurement_a_cases"]) + len(prereg["measurement_c_cases"])


def summarize_quick(rows: list[dict[str, str]], prereg: dict[str, Any], *, elapsed_s: float) -> dict[str, Any]:
    a_axes = {row["axis"] for row in rows if row["measurement"] == "A"}
    c_drivers = {row["driver"] for row in rows if row["measurement"] == "C"}
    gates = {
        "row_count_complete": len(rows) == expected_case_count(prereg),
        "measurement_a_axes_covered": a_axes == {"long", "lat"},
        "measurement_c_drivers_covered": c_drivers == {"baseline_coast", "v4_incumbent"},
        "reset_obs_finite_all": all(row["reset_obs_finite"] == "True" for row in rows),
        "variant_match_all": all(row["variant_match"] == "True" for row in rows),
        "quick_mode_is_nonverdict": prereg.get("quick_mode_is_verdict") is False,
        "track_f_not_admitted": True,
    }
    gates["all_passed"] = all(gates.values())
    return {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": "quick",
        "created_at_utc": utc_timestamp(),
        "elapsed_s": round(float(elapsed_s), 1),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "rows_csv": str(ROWS_CSV.relative_to(REPO_ROOT)),
        "metrics_csv": str(METRICS_CSV.relative_to(REPO_ROOT)),
        "row_count": len(rows),
        "expected_row_count": expected_case_count(prereg),
        "protocol_gates": gates,
        "measurement_a_rows": [dict(row) for row in rows if row["measurement"] == "A"],
        "measurement_c_rows": [dict(row) for row in rows if row["measurement"] == "C"],
        "decision": {
            "e3_quick_verdict": "protocol_smoke_passed" if gates["all_passed"] else "protocol_smoke_failed",
            "measurement_a_verdict": "not_decided_by_quick_mode",
            "measurement_c_verdict": "not_decided_by_quick_mode",
            "track_f_admitted": False,
            "next_admitted_step": "Full E3 must be separately preregistered if M3253 passes.",
        },
    }


def write_metrics(summary: dict[str, Any]) -> None:
    rows = [
        {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
        {"metric": "quick_mode_is_verdict", "value": 0.0},
        {"metric": "row_count", "value": float(summary["row_count"])},
        {"metric": "expected_row_count", "value": float(summary["expected_row_count"])},
    ]
    METRICS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary: dict[str, Any]) -> None:
    lines = [
        "# M3253 Phase-4 E3 Chrono Measurement A/C Smoke",
        "",
        "Status: completed. This is an E3 protocol smoke only; it does not decide the full Chrono detection-latency table, the full recoverable-set budget, or Track F admission.",
        "",
        "## Verdict",
        "",
        f"- E3 quick verdict: **{summary['decision']['e3_quick_verdict']}**.",
        f"- Protocol gates passed: **{str(summary['protocol_gates']['all_passed']).lower()}**.",
        f"- Rows: {summary['row_count']} / expected {summary['expected_row_count']}.",
        "",
        "## Measured",
        "",
        "| measurement | case | outcome | steps | fired/recovered |",
        "|---|---|---|---:|---|",
    ]
    for row in summary["measurement_a_rows"]:
        lines.append(
            f"| A | {row['case_id']} | {row['outcome']} | {row['steps']} | fired_step={row['detector_fired_step']} |"
        )
    for row in summary["measurement_c_rows"]:
        lines.append(
            f"| C | {row['case_id']} | {row['outcome']} | {row['steps']} | recovered={row['recovered']} step={row['recovery_step']} |"
        )
    lines += [
        "",
        "## Inferred",
        "",
        "The current Chrono worker interface can execute the E3 smoke data path for obs72 detector traces and planar overshoot recovery traces. A full E3 verdict still needs a separate preregistration with frozen truth definitions, cells, seed streams, and safety-gating thresholds.",
        "",
        "## Claim Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Artifacts",
        "",
        f"- Preregistration: `{summary['preregistration']}`",
        f"- Quick JSON: `{str(QUICK_JSON.relative_to(REPO_ROOT))}`",
        f"- Episode rows: `{summary['rows_csv']}`",
        f"- Metrics: `{summary['metrics_csv']}`",
        f"- Script: `scripts/feasibility_audit/{Path(__file__).name}`",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_quick(*, resume: bool) -> dict[str, Any]:
    prereg = load_preregistration()
    if not resume:
        for path in (ROWS_CSV, METRICS_CSV, PROGRESS_JSONL, QUICK_JSON, DOC_PATH):
            if path.exists():
                path.unlink()
    started = time.time()
    rows: list[dict[str, Any]] = []
    client = ChronoWorkerClient(stderr_log=STDERR_LOG)
    try:
        for index, case in enumerate(prereg["measurement_a_cases"]):
            row = run_measurement_a_case(client, case, seed=_seed_for("A", case["axis"], index))
            rows.append(row)
            _progress({"stage": "measurement_a_done", "case_id": row["case_id"], "outcome": row["outcome"]})
        for index, case in enumerate(prereg["measurement_c_cases"]):
            row = run_measurement_c_case(client, case, seed=_seed_for("C", case["driver"], index))
            rows.append(row)
            _progress({"stage": "measurement_c_done", "case_id": row["case_id"], "outcome": row["outcome"]})
    finally:
        client.close()
    _write_rows(rows)
    summary = summarize_quick(_read_rows(), prereg, elapsed_s=time.time() - started)
    write_json(QUICK_JSON, summary)
    write_metrics(summary)
    write_markdown(summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.write_prereg:
        payload = write_preregistration()
        print(json.dumps({"preregistration": str(PREREG_JSON), "expected_rows": expected_case_count(payload)}, sort_keys=True))
    if args.quick:
        summary = run_quick(resume=args.resume)
        print(json.dumps(summary["decision"], sort_keys=True))
    if not args.write_prereg and not args.quick:
        raise SystemExit("nothing to do; pass --write-prereg and/or --quick")


if __name__ == "__main__":
    main()
