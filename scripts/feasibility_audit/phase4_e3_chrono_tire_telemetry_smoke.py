"""Phase-4 E3 Chrono tire-truth telemetry connector smoke.

M3254 is an infrastructure smoke between the M3253 E3 A/C protocol smoke and
full E3. It verifies that the Chrono worker diagnostics expose finite 4-wheel
tire slip/force telemetry without changing obs72, action3, the actor path, or
the incumbent driver.

Quick mode is connector evidence only. It is not the full Chrono E3
detection-latency table, not the full recoverable-set budget, and it cannot
open Track F.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e3_chrono_tire_telemetry_smoke.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e3_chrono_tire_telemetry_smoke.py --quick --resume
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
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.artifacts import utc_timestamp, write_json  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402


MILESTONE_ID = "m3254-phase4-e3-chrono-tire-telemetry-smoke"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_tire_telemetry_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_tire_telemetry_quick.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e3_chrono_tire_telemetry"
SAMPLE_ROWS_CSV = RUN_DIR / "sample_rows_quick.csv"
WHEEL_ROWS_CSV = RUN_DIR / "wheel_rows_quick.csv"
METRICS_CSV = RUN_DIR / "metrics_quick.csv"
PROGRESS_JSONL = RUN_DIR / "progress_quick.jsonl"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
DOC_PATH = REPO_ROOT / "docs" / "m3254-phase4-e3-chrono-tire-telemetry-smoke.md"

E0_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_spread_expressibility_audit.json"
E2_FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2_chrono_two_regime_full.json"
E3_SMOKE_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_quick.json"

SEED_BASE = 2026061306
VARIANT = "sedan_tmeasy"
DT = 0.02
TRACK_RADIUS = 900.0
TRACK_WIDTH = 30.0
MU = 0.5875
SPEED_MPS = 8.0
MAX_STEPS = 24
SAMPLE_STEPS = [0, 1, 6, 12]

CLAIM_BOUNDARY = (
    "Phase-4 E3 Chrono tire-truth telemetry connector smoke only: the Chrono "
    "worker diagnostics expose finite four-wheel tire slip, wheel speed, tire "
    "force, local-force projection, and normal-load rows on the default "
    "Sedan/TMeasy fixture. Quick mode is not a Chrono detection-latency "
    "verdict, not a full reflex recoverable-set budget, and makes no incumbent "
    "mutation, validation ranking, promotion, driver-performance, full "
    "high-fidelity sufficiency, paper, repair-success, robustness-result, "
    "feasibility-proof, Track-F-admission, or self-ID claim."
)

WHEEL_NUMERIC_FIELDS = [
    "slip_angle_rad",
    "longitudinal_slip",
    "camber_angle_rad",
    "tire_radius_m",
    "wheel_omega_rad_s",
    "force_x_n",
    "force_y_n",
    "force_z_n",
    "local_force_x_n",
    "local_force_y_n",
    "local_force_z_n",
    "normal_load_n",
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


def _is_true(value: Any) -> bool:
    return value is True or str(value) == "True"


def _format_float(value: Any) -> str:
    number = _as_float(value)
    return "nan" if not math.isfinite(number) else f"{number:.6g}"


def build_preregistration() -> dict[str, Any]:
    e0 = _read_json(E0_JSON)
    e2 = _read_json(E2_FULL_JSON)
    e3 = _read_json(E3_SMOKE_JSON)
    if not e0.get("decision", {}).get("e1_preregistration_admitted"):
        raise RuntimeError("E0 did not admit the Chrono vehicle fixture envelope")
    if e2.get("decision", {}).get("e2_full_verdict") != "chrono_clean_belief_value_positive":
        raise RuntimeError("M3252 full E2 is not available as the E3 predecessor")
    if e3.get("decision", {}).get("e3_quick_verdict") != "protocol_smoke_passed":
        raise RuntimeError("M3253 E3 A/C protocol smoke did not pass before M3254")
    return {
        "protocol": "phase4_e3_chrono_tire_telemetry_smoke_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 E3 Chrono tire-truth telemetry connector smoke",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_tire_telemetry_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "e0_artifact": str(E0_JSON.relative_to(REPO_ROOT)),
        "e2_full_artifact": str(E2_FULL_JSON.relative_to(REPO_ROOT)),
        "e3_smoke_artifact": str(E3_SMOKE_JSON.relative_to(REPO_ROOT)),
        "quick_mode_is_verdict": False,
        "chrono_variant": VARIANT,
        "sample_steps": list(SAMPLE_STEPS),
        "cases": [
            {
                "case_id": "coast_hold",
                "description": "zero steer, zero throttle, zero brake hold after reset",
                "action": [0.0, -1.0, -1.0],
                "mu": MU,
                "speed_mps": SPEED_MPS,
            },
            {
                "case_id": "brake_steer",
                "description": "moderate right steer with full braking to exercise tire-force response",
                "action": [0.25, -1.0, 1.0],
                "mu": MU,
                "speed_mps": SPEED_MPS,
            },
        ],
        "runtime_gates": [
            "E0 artifact admits the Chrono fixture envelope",
            "M3252 full E2 and M3253 E3 A/C quick artifacts exist before M3254",
            "reset and selected step samples preserve finite obs72",
            "every sample exposes tire_telemetry_available=true with four wheel rows",
            "per-wheel tire slip, wheel speed, force, local-force projection, and normal load are finite",
            "normal loads are positive at every sampled wheel",
            "quick mode is explicitly non-verdict and cannot open Track F",
        ],
        "truth_fields_frozen_for_full_e3_design": [
            "slip_angle_rad",
            "longitudinal_slip",
            "camber_angle_rad",
            "wheel_omega_rad_s",
            "local_force_x_n",
            "local_force_y_n",
            "normal_load_n",
        ],
        "full_e3_placeholder": {
            "status": "not_registered_by_M3254",
            "needed_next": (
                "Full E3 can now preregister concrete Chrono tire-truth definitions, "
                "cells, seed streams, paired detector/recovery readouts, and "
                "Track-F safety-gating thresholds before any E3 verdict."
            ),
        },
        "decision_rule": (
            "M3254 PASS iff all quick samples and wheel rows are written, obs72 remains "
            "finite, telemetry is available with four finite wheel rows per sample, "
            "normal loads are positive, and the artifact refuses a full E3 or Track-F verdict."
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
    if not payload.get("frozen_before_any_tire_telemetry_rollout"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_tire_telemetry_rollout")
    return payload


def base_scenario(*, case_id: str, mu: float, speed_mps: float) -> dict[str, Any]:
    return {
        "scenario_id": case_id,
        "dt": DT,
        "max_steps": MAX_STEPS,
        "track_kind": "circle",
        "track_radius": TRACK_RADIUS,
        "track_width": TRACK_WIDTH,
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


def _finite_obs(obs: np.ndarray) -> bool:
    return obs.shape == (72,) and bool(np.all(np.isfinite(obs)))


def _progress(payload: dict[str, Any]) -> None:
    PROGRESS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def _sample_row(
    *,
    case: dict[str, Any],
    sample_tag: str,
    sample_step: int,
    action: np.ndarray,
    obs: np.ndarray,
    info: dict[str, Any],
    terminated: bool,
    truncated: bool,
    status: str,
) -> dict[str, Any]:
    return {
        "case_id": str(case["case_id"]),
        "sample_tag": sample_tag,
        "sample_step": int(sample_step),
        "backend_step": int(info.get("step", -1)),
        "obs72_finite": _finite_obs(obs),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "status": str(status),
        "action_steer": float(action[0]),
        "action_throttle": float(action[1]),
        "action_brake": float(action[2]),
        "speed": info.get("speed", ""),
        "yaw_rate": info.get("yaw_rate", ""),
        "tire_telemetry_available": bool(info.get("tire_telemetry_available", False)),
        "tire_telemetry_wheel_count": int(info.get("tire_telemetry_wheel_count", 0)),
        "tire_telemetry_error": str(info.get("tire_telemetry_error", "")),
        "max_abs_tire_slip_angle_rad": info.get("max_abs_tire_slip_angle_rad", ""),
        "max_abs_tire_longitudinal_slip": info.get("max_abs_tire_longitudinal_slip", ""),
        "max_abs_tire_camber_angle_rad": info.get("max_abs_tire_camber_angle_rad", ""),
        "max_abs_tire_longitudinal_force_n": info.get("max_abs_tire_longitudinal_force_n", ""),
        "max_abs_tire_lateral_force_n": info.get("max_abs_tire_lateral_force_n", ""),
        "max_tire_normal_load_n": info.get("max_tire_normal_load_n", ""),
        "min_tire_normal_load_n": info.get("min_tire_normal_load_n", ""),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _wheel_rows_for_sample(
    *,
    sample_row: dict[str, Any],
    info: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for wheel_index, wheel in enumerate(info.get("tire_telemetry", []) or []):
        row = {
            "case_id": sample_row["case_id"],
            "sample_tag": sample_row["sample_tag"],
            "sample_step": sample_row["sample_step"],
            "backend_step": sample_row["backend_step"],
            "wheel_index": int(wheel_index),
            "axle_index": wheel.get("axle_index", ""),
            "axle": wheel.get("axle", ""),
            "side": wheel.get("side", ""),
            "side_index": wheel.get("side_index", ""),
        }
        for field in WHEEL_NUMERIC_FIELDS:
            row[field] = wheel.get(field, "")
        rows.append(row)
    return rows


SAMPLE_FIELDNAMES = [
    "case_id",
    "sample_tag",
    "sample_step",
    "backend_step",
    "obs72_finite",
    "terminated",
    "truncated",
    "status",
    "action_steer",
    "action_throttle",
    "action_brake",
    "speed",
    "yaw_rate",
    "tire_telemetry_available",
    "tire_telemetry_wheel_count",
    "tire_telemetry_error",
    "max_abs_tire_slip_angle_rad",
    "max_abs_tire_longitudinal_slip",
    "max_abs_tire_camber_angle_rad",
    "max_abs_tire_longitudinal_force_n",
    "max_abs_tire_lateral_force_n",
    "max_tire_normal_load_n",
    "min_tire_normal_load_n",
    "claim_boundary",
]

WHEEL_FIELDNAMES = [
    "case_id",
    "sample_tag",
    "sample_step",
    "backend_step",
    "wheel_index",
    "axle_index",
    "axle",
    "side",
    "side_index",
    *WHEEL_NUMERIC_FIELDS,
]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _jsonable(row.get(key, "")) for key in fieldnames})


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def expected_sample_count(prereg: dict[str, Any]) -> int:
    return len(prereg["cases"]) * len(prereg["sample_steps"])


def expected_wheel_count(prereg: dict[str, Any]) -> int:
    return expected_sample_count(prereg) * 4


def summarize_quick(
    sample_rows: list[dict[str, Any]],
    wheel_rows: list[dict[str, Any]],
    prereg: dict[str, Any],
    *,
    elapsed_s: float,
) -> dict[str, Any]:
    expected_samples = expected_sample_count(prereg)
    expected_wheels = expected_wheel_count(prereg)
    wheel_numeric_finite = all(
        all(math.isfinite(_as_float(row.get(field, ""))) for field in WHEEL_NUMERIC_FIELDS)
        for row in wheel_rows
    )
    normal_loads = [_as_float(row.get("normal_load_n", "")) for row in wheel_rows]
    finite_normal_loads = [value for value in normal_loads if math.isfinite(value)]
    gates = {
        "sample_row_count_complete": len(sample_rows) == expected_samples,
        "wheel_row_count_complete": len(wheel_rows) == expected_wheels,
        "obs72_finite_all": all(_is_true(row.get("obs72_finite")) for row in sample_rows),
        "telemetry_available_all": all(_is_true(row.get("tire_telemetry_available")) for row in sample_rows),
        "wheel_count_all_four": all(int(_as_float(row.get("tire_telemetry_wheel_count", -1))) == 4 for row in sample_rows),
        "telemetry_error_clear_all": all(str(row.get("tire_telemetry_error", "")) == "" for row in sample_rows),
        "finite_wheel_numeric_all": wheel_numeric_finite,
        "normal_load_positive_all": bool(finite_normal_loads) and all(value > 0.0 for value in finite_normal_loads),
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
        "sample_rows_csv": str(SAMPLE_ROWS_CSV.relative_to(REPO_ROOT)),
        "wheel_rows_csv": str(WHEEL_ROWS_CSV.relative_to(REPO_ROOT)),
        "metrics_csv": str(METRICS_CSV.relative_to(REPO_ROOT)),
        "sample_row_count": len(sample_rows),
        "expected_sample_row_count": expected_samples,
        "wheel_row_count": len(wheel_rows),
        "expected_wheel_row_count": expected_wheels,
        "min_tire_normal_load_n": min(finite_normal_loads) if finite_normal_loads else float("nan"),
        "max_tire_normal_load_n": max(finite_normal_loads) if finite_normal_loads else float("nan"),
        "protocol_gates": gates,
        "sample_rows": [dict(row) for row in sample_rows],
        "decision": {
            "telemetry_quick_verdict": "tire_telemetry_smoke_passed" if gates["all_passed"] else "tire_telemetry_smoke_failed",
            "full_e3_verdict": "not_decided_by_quick_mode",
            "track_f_admitted": False,
            "next_admitted_step": "Full E3 preregistration can now freeze tire-truth definitions if M3254 passes.",
        },
    }


def write_metrics(summary: dict[str, Any]) -> None:
    rows = [
        {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
        {"metric": "quick_mode_is_verdict", "value": 0.0},
        {"metric": "sample_row_count", "value": float(summary["sample_row_count"])},
        {"metric": "expected_sample_row_count", "value": float(summary["expected_sample_row_count"])},
        {"metric": "wheel_row_count", "value": float(summary["wheel_row_count"])},
        {"metric": "expected_wheel_row_count", "value": float(summary["expected_wheel_row_count"])},
        {"metric": "min_tire_normal_load_n", "value": float(summary["min_tire_normal_load_n"])},
        {"metric": "max_tire_normal_load_n", "value": float(summary["max_tire_normal_load_n"])},
    ]
    _write_csv(METRICS_CSV, rows, ["metric", "value"])


def write_markdown(summary: dict[str, Any]) -> None:
    lines = [
        "# M3254 Phase-4 E3 Chrono Tire Telemetry Smoke",
        "",
        "Status: completed. This is a tire-truth telemetry connector smoke only; it does not decide full E3, a detection-latency table, a recoverable-set budget, or Track F admission.",
        "",
        "## Verdict",
        "",
        f"- Telemetry quick verdict: **{summary['decision']['telemetry_quick_verdict']}**.",
        f"- Protocol gates passed: **{str(summary['protocol_gates']['all_passed']).lower()}**.",
        f"- Samples: {summary['sample_row_count']} / expected {summary['expected_sample_row_count']}.",
        f"- Wheel rows: {summary['wheel_row_count']} / expected {summary['expected_wheel_row_count']}.",
        f"- Normal load range: {_format_float(summary['min_tire_normal_load_n'])} to {_format_float(summary['max_tire_normal_load_n'])} N.",
        "",
        "## Measured",
        "",
        "| case | sample | obs72 finite | wheels | max slip angle | max lateral force | min normal load |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in summary["sample_rows"]:
        lines.append(
            "| "
            f"{row['case_id']} | {row['sample_step']} | {row['obs72_finite']} | "
            f"{row['tire_telemetry_wheel_count']} | {_format_float(row['max_abs_tire_slip_angle_rad'])} | "
            f"{_format_float(row['max_abs_tire_lateral_force_n'])} | {_format_float(row['min_tire_normal_load_n'])} |"
        )
    lines += [
        "",
        "## Inferred",
        "",
        "The current Chrono worker diagnostics can expose 4-wheel tire slip/force truth rows through reset and step samples while preserving finite obs72. Full E3 still needs a separate preregistration that freezes how these tire-truth fields define detection latency, recovery budgets, cells, seed streams, paired readouts, and safety gates.",
        "",
        "## Claim Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Artifacts",
        "",
        f"- Preregistration: `{summary['preregistration']}`",
        f"- Quick JSON: `{str(QUICK_JSON.relative_to(REPO_ROOT))}`",
        f"- Sample rows: `{summary['sample_rows_csv']}`",
        f"- Wheel rows: `{summary['wheel_rows_csv']}`",
        f"- Metrics: `{summary['metrics_csv']}`",
        f"- Script: `scripts/feasibility_audit/{Path(__file__).name}`",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_case(client: ChronoWorkerClient, case: dict[str, Any], *, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenario = base_scenario(case_id=f"m3254-{case['case_id']}-seed{seed}", mu=float(case["mu"]), speed_mps=float(case["speed_mps"]))
    action = np.asarray(case["action"], dtype=np.float32)
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
    sample_rows: list[dict[str, Any]] = []
    wheel_rows: list[dict[str, Any]] = []

    info = dict(reset_reply.get("info", {}))
    sample = _sample_row(
        case=case,
        sample_tag="reset",
        sample_step=0,
        action=action,
        obs=obs,
        info=info,
        terminated=False,
        truncated=False,
        status="reset",
    )
    sample_rows.append(sample)
    wheel_rows.extend(_wheel_rows_for_sample(sample_row=sample, info=info))
    _progress({"stage": "sample_done", "case_id": case["case_id"], "sample_step": 0, "wheel_rows": len(wheel_rows)})

    terminated = truncated = False
    status = "reset"
    for step in range(1, MAX_STEPS + 1):
        obs, terminated, truncated, status, info = client.step(action)
        if step in SAMPLE_STEPS:
            sample = _sample_row(
                case=case,
                sample_tag=f"step_{step}",
                sample_step=step,
                action=action,
                obs=obs,
                info=info,
                terminated=terminated,
                truncated=truncated,
                status=status,
            )
            sample_rows.append(sample)
            before = len(wheel_rows)
            wheel_rows.extend(_wheel_rows_for_sample(sample_row=sample, info=info))
            _progress(
                {
                    "stage": "sample_done",
                    "case_id": case["case_id"],
                    "sample_step": step,
                    "status": status,
                    "wheel_rows": len(wheel_rows) - before,
                }
            )
        if terminated or truncated:
            break
        if step >= max(SAMPLE_STEPS):
            break
    return sample_rows, wheel_rows


def run_quick(*, resume: bool) -> dict[str, Any]:
    prereg = load_preregistration()
    if not resume:
        for path in (SAMPLE_ROWS_CSV, WHEEL_ROWS_CSV, METRICS_CSV, PROGRESS_JSONL, QUICK_JSON, DOC_PATH):
            if path.exists():
                path.unlink()
    started = time.time()
    sample_rows: list[dict[str, Any]] = []
    wheel_rows: list[dict[str, Any]] = []
    client = ChronoWorkerClient(stderr_log=STDERR_LOG)
    try:
        for index, case in enumerate(prereg["cases"]):
            case_samples, case_wheels = run_case(client, case, seed=_seed_for(case["case_id"], index))
            sample_rows.extend(case_samples)
            wheel_rows.extend(case_wheels)
    finally:
        client.close()
    _write_csv(SAMPLE_ROWS_CSV, sample_rows, SAMPLE_FIELDNAMES)
    _write_csv(WHEEL_ROWS_CSV, wheel_rows, WHEEL_FIELDNAMES)
    summary = summarize_quick(_read_csv(SAMPLE_ROWS_CSV), _read_csv(WHEEL_ROWS_CSV), prereg, elapsed_s=time.time() - started)
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
        print(
            json.dumps(
                {
                    "preregistration": str(PREREG_JSON),
                    "expected_sample_rows": expected_sample_count(payload),
                    "expected_wheel_rows": expected_wheel_count(payload),
                },
                sort_keys=True,
            )
        )
    if args.quick:
        summary = run_quick(resume=args.resume)
        print(json.dumps(summary["decision"], sort_keys=True))
    if not args.write_prereg and not args.quick:
        raise SystemExit("nothing to do; pass --write-prereg and/or --quick")


if __name__ == "__main__":
    main()
