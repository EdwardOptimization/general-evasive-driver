"""Phase-4 E3-fix Chrono detector-onset reconciliation.

M3257 is the first Track-E' hardening unit after CP-3 disposition A. It
re-runs Measurement-A only, records full per-step traces, and reconciles the
obs72 shortfall-detector fire time against the M3255 Chrono tire-slip truth
onset. The goal is a documented onset definition for E2', not training,
promotion, or Track-F admission.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e3_detector_onset_reconciliation.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e3_detector_onset_reconciliation.py --quick --resume
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e3_detector_onset_reconciliation.py --full --resume
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
import phase4_e3_chrono_measurement_ac_full as full_e3  # noqa: E402
import phase4_e3_chrono_measurement_ac_smoke as ac_smoke  # noqa: E402


MILESTONE_ID = "m3257-phase4-e3-detector-onset-reconciliation"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_detector_onset_reconciliation_prereg.json"
FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_detector_onset_reconciliation.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_detector_onset_reconciliation_quick.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e3_detector_onset_reconciliation"
CASE_ROWS_FULL_CSV = RUN_DIR / "case_rows_full.csv"
CASE_ROWS_QUICK_CSV = RUN_DIR / "case_rows_quick.csv"
TRACE_ROWS_FULL_CSV = RUN_DIR / "trace_rows_full.csv"
TRACE_ROWS_QUICK_CSV = RUN_DIR / "trace_rows_quick.csv"
METRICS_FULL_CSV = RUN_DIR / "metrics_full.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
STDERR_FULL_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
STDERR_QUICK_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
DOC_PATH = REPO_ROOT / "docs" / "m3257-phase4-e3-detector-onset-reconciliation.md"

M3255_FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_full.json"
M3255_LATENCY_CSV = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e3_chrono_measurement_ac_full" / "latency_rows_full.csv"
CP3_ESCALATION = REPO_ROOT / "docs" / "escalations" / "2026-06-13-phase4-cp3-track-f-pi-checkpoint.md"

SEED_BASE = 2026061311
CORROBORATION_MAX_LEAD_STEPS = 150

CLAIM_BOUNDARY = (
    "Phase-4 E3-fix detector-onset reconciliation only: scripted Chrono "
    "Measurement-A brake/steer ramps compare the obs72 shortfall detector "
    "against M3255 tire-slip truth and a pre-registered detector-corroborated "
    "onset rule. This is zero training and makes no incumbent mutation, "
    "validation ranking, promotion, driver-performance, full high-fidelity "
    "sufficiency, paper, repair-success, robustness-result, feasibility-proof, "
    "Track-F-admission, or self-ID claim."
)

CASE_FIELDNAMES = [
    "case_id",
    "axis",
    "mu",
    "rate",
    "seed_index",
    "seed",
    "truth_threshold",
    "original_truth_onset_step",
    "detector_fired_step",
    "detector_armed_step",
    "original_latency_steps",
    "original_latency_s",
    "original_missed_detection",
    "original_early_fire",
    "reconciled_onset_step",
    "reconciled_latency_steps",
    "reconciled_latency_s",
    "reconciled_missed_detection",
    "reconciled_early_fire",
    "detector_corroborated_by_later_tire_truth",
    "uncorroborated_detector_fire",
    "reconciliation_label",
    "truth_signal_peak",
    "obs_signal_peak",
    "steps",
    "outcome",
    "reset_obs_finite",
    "runtime_obs_finite_all",
    "variant_match",
    "telemetry_available_all",
    "wheel_count_all_four",
    "claim_boundary",
]

TRACE_FIELDNAMES = [
    "case_id",
    "axis",
    "step",
    "detector_signal",
    "detector_pred",
    "detector_y",
    "detector_armed",
    "detector_fired",
    "detector_gain",
    "truth_signal",
    "max_abs_tire_longitudinal_slip",
    "max_abs_tire_slip_angle_rad",
    "max_abs_tire_longitudinal_force_n",
    "max_abs_tire_lateral_force_n",
    "min_tire_normal_load_n",
    "max_tire_normal_load_n",
    "speed",
    "obs_finite",
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


def _write_metrics(summary: dict[str, Any], path: Path) -> None:
    rows = [
        {"metric": "case_row_count", "value": float(summary["case_row_count"])},
        {"metric": "expected_case_row_count", "value": float(summary["expected_case_row_count"])},
        {"metric": "trace_row_count", "value": float(summary["trace_row_count"])},
        {"metric": "original_early_fire_rate", "value": float(summary["original"]["early_fire_rate"])},
        {"metric": "original_detector_miss_rate", "value": float(summary["original"]["detector_miss_rate"])},
        {"metric": "reconciled_early_fire_rate", "value": float(summary["reconciled"]["early_fire_rate"])},
        {"metric": "reconciled_detector_miss_rate", "value": float(summary["reconciled"]["detector_miss_rate"])},
        {"metric": "corroborated_early_fire_rate", "value": float(summary["reconciled"]["corroborated_early_fire_rate"])},
        {"metric": "reconciled_p90_latency_s", "value": float(summary["reconciled"]["p90_latency_s"])},
        {"metric": "protocol_gates_passed", "value": float(summary["protocol_gates"]["all_passed"])},
    ]
    _write_csv(path, rows, ["metric", "value"])


def build_preregistration() -> dict[str, Any]:
    m3255 = _read_json(M3255_FULL_JSON)
    full_prereg = full_e3.build_preregistration()
    original = m3255.get("measurement_a_summary", {})
    if m3255.get("decision", {}).get("full_e3_verdict") != "chrono_safety_measurement_completed":
        raise RuntimeError("M3255 full E3 verdict is not available")
    cases = full_prereg["measurement_a"]["cases"]
    quick_cases = full_prereg["measurement_a"]["quick_cases"]
    return {
        "protocol": "phase4_e3_detector_onset_reconciliation_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 Track E' E3-fix detector-onset reconciliation",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_m3257_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "dependencies": {
            "m3255_full_artifact": str(M3255_FULL_JSON.relative_to(REPO_ROOT)),
            "m3255_latency_rows": str(M3255_LATENCY_CSV.relative_to(REPO_ROOT)),
            "cp3_disposition": str(CP3_ESCALATION.relative_to(REPO_ROOT)),
        },
        "baseline_anomaly": {
            "m3255_original_early_fire_rate": original.get("early_fire_rate"),
            "m3255_detector_miss_rate": original.get("detector_miss_rate"),
            "m3255_p90_latency_s": original.get("p90_latency_s"),
            "m3255_by_axis": original.get("by_axis", {}),
        },
        "chrono_variant": full_e3.VARIANT,
        "dt": full_e3.DT,
        "cases": cases,
        "quick_cases": quick_cases,
        "expected_full_case_rows": len(cases),
        "expected_quick_case_rows": len(quick_cases),
        "onset_definitions": {
            "original_m3255_tire_truth": full_prereg["measurement_a"]["truth_definitions"],
            "obs72_detector": {
                "class": "scripts/feasibility_audit/slip_onset_detectability.py::SlipOnsetDetector",
                "tau_by_axis": dict(full_e3.A_TAU),
                "persist_steps": ac_smoke.SlipOnsetDetector.PERSIST_K,
                "input": "obs72 only; no tire telemetry or hidden parameter input",
            },
            "reconciled_actor_visible_onset": {
                "rule": (
                    "Use the detector fire step as the corrected onset when it occurs before "
                    "the M3255 tire-slip truth onset and that tire truth later occurs within "
                    "CORROBORATION_MAX_LEAD_STEPS; otherwise keep the M3255 tire-slip truth "
                    "onset. If the detector fires and no tire truth follows inside the window, "
                    "report an uncorroborated early detector fire."
                ),
                "corroboration_max_lead_steps": CORROBORATION_MAX_LEAD_STEPS,
                "corroboration_max_lead_s": CORROBORATION_MAX_LEAD_STEPS * full_e3.DT,
            },
        },
        "runtime_gates": [
            "full M3255 anomaly artifact exists before M3257",
            "all frozen Measurement-A rows are rerun and traced",
            "trace rows include obs72 detector signal and Chrono tire-slip truth fields",
            "one reconciled onset definition is documented in the preregistration",
            "early-fire rate is reported under both original and reconciled definitions",
            "corrected latency and miss tables are written",
            "Track F remains blocked pending E2' flip confirmation plus a later GPU-days checkpoint",
        ],
        "decision_rule": (
            "M3257 completes iff row-count, trace, finite obs, variant, telemetry, wheel-count, "
            "definition, early-fire reporting, and corrected-table gates pass. The resulting "
            "detector definition may feed E2', but does not admit Track F or training."
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
    if not payload.get("frozen_before_any_m3257_rollout"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_m3257_rollout")
    return payload


def reconcile_onset_steps(
    *,
    original_truth_onset_step: int,
    detector_fired_step: int,
    max_lead_steps: int = CORROBORATION_MAX_LEAD_STEPS,
) -> dict[str, Any]:
    truth = int(original_truth_onset_step)
    fired = int(detector_fired_step)
    if truth < 0:
        return {
            "reconciled_onset_step": -1,
            "reconciled_latency_steps": "",
            "reconciled_missed_detection": False,
            "reconciled_early_fire": False,
            "detector_corroborated_by_later_tire_truth": False,
            "uncorroborated_detector_fire": fired >= 0,
            "reconciliation_label": "no_tire_truth_onset_observed",
        }
    if fired < 0:
        return {
            "reconciled_onset_step": truth,
            "reconciled_latency_steps": "",
            "reconciled_missed_detection": True,
            "reconciled_early_fire": False,
            "detector_corroborated_by_later_tire_truth": False,
            "uncorroborated_detector_fire": False,
            "reconciliation_label": "detector_missed_tire_truth",
        }
    if fired < truth and (truth - fired) <= int(max_lead_steps):
        return {
            "reconciled_onset_step": fired,
            "reconciled_latency_steps": 0,
            "reconciled_missed_detection": False,
            "reconciled_early_fire": False,
            "detector_corroborated_by_later_tire_truth": True,
            "uncorroborated_detector_fire": False,
            "reconciliation_label": "detector_fire_corroborated_by_later_tire_truth",
        }
    return {
        "reconciled_onset_step": truth,
        "reconciled_latency_steps": fired - truth,
        "reconciled_missed_detection": False,
        "reconciled_early_fire": fired < truth,
        "detector_corroborated_by_later_tire_truth": False,
        "uncorroborated_detector_fire": fired < truth,
        "reconciliation_label": "m3255_tire_truth_retained",
    }


def _finite_obs(obs: np.ndarray) -> bool:
    return obs.shape == (72,) and bool(np.all(np.isfinite(obs)))


def _scenario_a(case: dict[str, Any]) -> dict[str, Any]:
    return ac_smoke.base_scenario(
        case_id=f"m3257-{case['case_id']}",
        mu=float(case["mu"]),
        speed_mps=full_e3.SPEED_MPS,
        max_steps=full_e3.MAX_STEPS_A,
        track_width=full_e3.TRACK_WIDTH_A,
    )


def _truth_signal(axis: str, info: dict[str, Any]) -> float:
    return full_e3._truth_signal(axis, info)


def _trace_row(case: dict[str, Any], step: int, det: dict[str, Any], info: dict[str, Any], obs_ok: bool) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "axis": case["axis"],
        "step": int(step),
        "detector_signal": float(det["signal"]),
        "detector_pred": float(det["pred"]),
        "detector_y": float(det["y"]),
        "detector_armed": bool(det["armed"]),
        "detector_fired": bool(det["fired"]),
        "detector_gain": float(det["gain"]),
        "truth_signal": _truth_signal(str(case["axis"]), info),
        "max_abs_tire_longitudinal_slip": info.get("max_abs_tire_longitudinal_slip", ""),
        "max_abs_tire_slip_angle_rad": info.get("max_abs_tire_slip_angle_rad", ""),
        "max_abs_tire_longitudinal_force_n": info.get("max_abs_tire_longitudinal_force_n", ""),
        "max_abs_tire_lateral_force_n": info.get("max_abs_tire_lateral_force_n", ""),
        "min_tire_normal_load_n": info.get("min_tire_normal_load_n", ""),
        "max_tire_normal_load_n": info.get("max_tire_normal_load_n", ""),
        "speed": info.get("speed", ""),
        "obs_finite": bool(obs_ok),
    }


def run_case(client: ChronoWorkerClient, case: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    axis = str(case["axis"])
    scenario = _scenario_a(case)
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(case["seed"]))
    controller: Any = (
        ac_smoke.BrakeRampController(float(case["rate"]))
        if axis == "long"
        else ac_smoke.SteerRampController(float(case["rate"]), full_e3.SPEED_MPS)
    )
    detector = ac_smoke.SlipOnsetDetector(axis, float(case["tau"]))
    reset_finite = _finite_obs(obs)
    variant_match = reset_reply.get("backend_info", {}).get("chrono_vehicle_variant") == full_e3.VARIANT
    runtime_obs_finite_all = reset_finite
    telemetry_available_all = bool(reset_reply.get("info", {}).get("tire_telemetry_available", False))
    wheel_count_all_four = int(reset_reply.get("info", {}).get("tire_telemetry_wheel_count", 0)) == 4
    info = dict(reset_reply.get("info", {}))
    truth_onset_step: int | None = None
    truth_run = 0
    truth_signal_peak = _truth_signal(axis, info)
    det = detector.step(obs)
    obs_signal_peak = float(det["signal"])
    trace_rows = [_trace_row(case, 0, det, info, reset_finite)]
    status = "reset"
    terminated = truncated = False
    steps = 0
    while not (terminated or truncated) and steps < full_e3.MAX_STEPS_A:
        action = controller.act(obs)
        obs, terminated, truncated, status, info = client.step(action)
        obs_ok = _finite_obs(obs)
        runtime_obs_finite_all = runtime_obs_finite_all and obs_ok
        telemetry_available_all = telemetry_available_all and bool(info.get("tire_telemetry_available", False))
        wheel_count_all_four = wheel_count_all_four and int(info.get("tire_telemetry_wheel_count", 0)) == 4
        signal = _truth_signal(axis, info)
        truth_signal_peak = max(truth_signal_peak, signal)
        if steps + 1 >= full_e3.A_TRUTH_MIN_STEP and signal >= float(case["truth_threshold"]):
            truth_run += 1
            if truth_onset_step is None and truth_run >= full_e3.A_TRUTH_PERSIST_STEPS:
                truth_onset_step = steps + 2 - full_e3.A_TRUTH_PERSIST_STEPS
        else:
            truth_run = 0
        if obs_ok:
            det = detector.step(obs)
            obs_signal_peak = max(obs_signal_peak, float(det["signal"]))
        trace_rows.append(_trace_row(case, steps + 1, det, info, obs_ok))
        steps += 1
        if not obs_ok:
            break
    fired_step = -1 if detector.fired_step is None else int(detector.fired_step)
    onset_step = -1 if truth_onset_step is None else int(truth_onset_step)
    original_latency_steps = "" if onset_step < 0 or fired_step < 0 else fired_step - onset_step
    reconciled = reconcile_onset_steps(
        original_truth_onset_step=onset_step,
        detector_fired_step=fired_step,
    )
    reconciled_latency = reconciled["reconciled_latency_steps"]
    row = {
        "case_id": case["case_id"],
        "axis": axis,
        "mu": float(case["mu"]),
        "rate": float(case["rate"]),
        "seed_index": int(case["seed_index"]),
        "seed": int(case["seed"]),
        "truth_threshold": float(case["truth_threshold"]),
        "original_truth_onset_step": onset_step,
        "detector_fired_step": fired_step,
        "detector_armed_step": -1 if detector.armed_step is None else int(detector.armed_step),
        "original_latency_steps": original_latency_steps,
        "original_latency_s": "" if original_latency_steps == "" else float(original_latency_steps) * full_e3.DT,
        "original_missed_detection": bool(onset_step >= 0 and fired_step < 0),
        "original_early_fire": bool(onset_step >= 0 and fired_step >= 0 and fired_step < onset_step),
        "reconciled_onset_step": reconciled["reconciled_onset_step"],
        "reconciled_latency_steps": reconciled_latency,
        "reconciled_latency_s": "" if reconciled_latency == "" else float(reconciled_latency) * full_e3.DT,
        "reconciled_missed_detection": reconciled["reconciled_missed_detection"],
        "reconciled_early_fire": reconciled["reconciled_early_fire"],
        "detector_corroborated_by_later_tire_truth": reconciled["detector_corroborated_by_later_tire_truth"],
        "uncorroborated_detector_fire": reconciled["uncorroborated_detector_fire"],
        "reconciliation_label": reconciled["reconciliation_label"],
        "truth_signal_peak": round(float(truth_signal_peak), 6),
        "obs_signal_peak": round(float(obs_signal_peak), 6),
        "steps": int(steps),
        "outcome": str(info.get("completion_reason") or info.get("termination_reason") or status),
        "reset_obs_finite": bool(reset_finite),
        "runtime_obs_finite_all": bool(runtime_obs_finite_all),
        "variant_match": bool(variant_match),
        "telemetry_available_all": bool(telemetry_available_all),
        "wheel_count_all_four": bool(wheel_count_all_four),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return row, trace_rows


def _row_keys(rows: Iterable[dict[str, Any]]) -> set[str]:
    return {str(row.get("case_id", "")) for row in rows}


def _rate(rows: list[dict[str, Any]], field: str) -> float:
    if not rows:
        return float("nan")
    return sum(1 for row in rows if _is_true(row.get(field))) / len(rows)


def _latencies(rows: list[dict[str, Any]], field: str) -> list[float]:
    return [_as_float(row.get(field, "")) for row in rows if math.isfinite(_as_float(row.get(field, "")))]


def _axis_summary(rows: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for axis in ("long", "lat"):
        axis_rows = [row for row in rows if row.get("axis") == axis]
        latencies = _latencies(axis_rows, f"{prefix}_latency_steps")
        out[axis] = {
            "row_count": len(axis_rows),
            "detector_miss_rate": _rate(axis_rows, f"{prefix}_missed_detection"),
            "early_fire_rate": _rate(axis_rows, f"{prefix}_early_fire"),
            "median_latency_steps": median(latencies) if latencies else float("nan"),
            "p90_latency_steps": percentile(latencies, 0.90),
        }
    return out


def summarize(
    case_rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    prereg: dict[str, Any],
    *,
    mode: str,
    elapsed_s: float,
    case_path: Path,
    trace_path: Path,
    metrics_path: Path,
) -> dict[str, Any]:
    expected = prereg[f"expected_{mode}_case_rows"]
    original_latencies = _latencies(case_rows, "original_latency_steps")
    reconciled_latencies = _latencies(case_rows, "reconciled_latency_steps")
    gates = {
        "case_row_count_complete": len(case_rows) == expected,
        "trace_rows_written": len(trace_rows) >= len(case_rows),
        "obs_finite_all": all(_is_true(row.get("reset_obs_finite")) and _is_true(row.get("runtime_obs_finite_all")) for row in case_rows),
        "variant_match_all": all(_is_true(row.get("variant_match")) for row in case_rows),
        "telemetry_available_all": all(_is_true(row.get("telemetry_available_all")) for row in case_rows),
        "wheel_count_all_four": all(_is_true(row.get("wheel_count_all_four")) for row in case_rows),
        "single_onset_definition_documented": bool(prereg.get("onset_definitions", {}).get("reconciled_actor_visible_onset")),
        "early_fire_rate_reported": True,
        "corrected_latency_table_written": all("reconciled_latency_steps" in row for row in case_rows),
    }
    gates["all_passed"] = all(bool(value) for value in gates.values())
    summary = {
        "milestone": MILESTONE_ID,
        "mode": mode,
        "generated_at_utc": utc_timestamp(),
        "elapsed_s": elapsed_s,
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "case_rows_csv": str(case_path.relative_to(REPO_ROOT)),
        "trace_rows_csv": str(trace_path.relative_to(REPO_ROOT)),
        "metrics_csv": str(metrics_path.relative_to(REPO_ROOT)),
        "case_row_count": len(case_rows),
        "expected_case_row_count": expected,
        "trace_row_count": len(trace_rows),
        "protocol_gates": gates,
        "original": {
            "detector_miss_rate": _rate(case_rows, "original_missed_detection"),
            "early_fire_rate": _rate(case_rows, "original_early_fire"),
            "median_latency_steps": median(original_latencies) if original_latencies else float("nan"),
            "p90_latency_steps": percentile(original_latencies, 0.90),
            "median_latency_s": (median(original_latencies) * full_e3.DT) if original_latencies else float("nan"),
            "p90_latency_s": percentile(original_latencies, 0.90) * full_e3.DT,
            "by_axis": _axis_summary(case_rows, "original"),
        },
        "reconciled": {
            "definition": prereg["onset_definitions"]["reconciled_actor_visible_onset"],
            "detector_miss_rate": _rate(case_rows, "reconciled_missed_detection"),
            "early_fire_rate": _rate(case_rows, "reconciled_early_fire"),
            "corroborated_early_fire_rate": _rate(case_rows, "detector_corroborated_by_later_tire_truth"),
            "uncorroborated_detector_fire_rate": _rate(case_rows, "uncorroborated_detector_fire"),
            "median_latency_steps": median(reconciled_latencies) if reconciled_latencies else float("nan"),
            "p90_latency_steps": percentile(reconciled_latencies, 0.90),
            "median_latency_s": (median(reconciled_latencies) * full_e3.DT) if reconciled_latencies else float("nan"),
            "p90_latency_s": percentile(reconciled_latencies, 0.90) * full_e3.DT,
            "by_axis": _axis_summary(case_rows, "reconciled"),
        },
        "decision": {
            "quick_verdict": (
                "onset_reconciliation_protocol_smoke_passed"
                if mode == "quick" and gates["all_passed"]
                else "onset_reconciliation_protocol_smoke_failed"
                if mode == "quick"
                else "not_applicable"
            ),
            "full_verdict": (
                "detector_onset_reconciliation_completed"
                if mode == "full" and gates["all_passed"]
                else "detector_onset_reconciliation_failed"
                if mode == "full"
                else "not_decided_by_quick_mode"
            ),
            "e2_prime_dependency_ready": bool(mode == "full" and gates["all_passed"]),
            "track_f_admitted": False,
            "next_admitted_step": (
                "E2' hardened two-regime-law preregistration can use the reconciled detector definition."
                if mode == "full" and gates["all_passed"]
                else "Run full M3257 before E2'."
            ),
        },
    }
    return summary


def write_markdown(summary: dict[str, Any]) -> None:
    original = summary["original"]
    reconciled = summary["reconciled"]
    lines = [
        "# M3257 Phase-4 E3 Detector-Onset Reconciliation",
        "",
        f"Status: {'completed' if summary['mode'] == 'full' and summary['protocol_gates']['all_passed'] else summary['mode']}.",
        "",
        "## Verdict",
        "",
        f"- Full verdict: **{summary['decision']['full_verdict']}**.",
        f"- Protocol gates passed: **{str(summary['protocol_gates']['all_passed']).lower()}**.",
        f"- E2' dependency ready: **{str(summary['decision']['e2_prime_dependency_ready']).lower()}**.",
        f"- Track F admitted: **{str(summary['decision']['track_f_admitted']).lower()}**.",
        "",
        "## Measured",
        "",
        "| readout | value |",
        "|---|---:|",
        f"| Case rows | {summary['case_row_count']} / {summary['expected_case_row_count']} |",
        f"| Trace rows | {summary['trace_row_count']} |",
        f"| Original early-fire rate | {_format_float(original['early_fire_rate'])} |",
        f"| Original detector miss rate | {_format_float(original['detector_miss_rate'])} |",
        f"| Original p90 latency | {_format_float(original['p90_latency_s'])} s |",
        f"| Reconciled early-fire rate | {_format_float(reconciled['early_fire_rate'])} |",
        f"| Reconciled detector miss rate | {_format_float(reconciled['detector_miss_rate'])} |",
        f"| Corroborated early-fire rate | {_format_float(reconciled['corroborated_early_fire_rate'])} |",
        f"| Uncorroborated detector-fire rate | {_format_float(reconciled['uncorroborated_detector_fire_rate'])} |",
        f"| Reconciled p90 latency | {_format_float(reconciled['p90_latency_s'])} s |",
        "",
        "## Reconciled Definition",
        "",
        str(reconciled["definition"]["rule"]),
        "",
        "## Reconciled By Axis",
        "",
        "| axis | rows | miss rate | early-fire rate | median latency | p90 latency |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for axis, row in reconciled["by_axis"].items():
        lines.append(
            f"| {axis} | {row['row_count']} | {_format_float(row['detector_miss_rate'])} | "
            f"{_format_float(row['early_fire_rate'])} | {_format_float(row['median_latency_steps'])} steps | "
            f"{_format_float(row['p90_latency_steps'])} steps |"
        )
    lines.extend(
        [
            "",
            "## Inferred",
            "",
            "M3257 reconciles the M3255 longitudinal early-fire anomaly by treating detector fires as actor-visible onset only when later corroborated by the frozen M3255 tire-slip event inside the pre-registered window. This makes the E2' detector definition explicit, but does not admit Track F or any training budget.",
            "",
            "## Claim Boundary",
            "",
            CLAIM_BOUNDARY,
            "",
            "## Artifacts",
            "",
            f"- Preregistration: `{summary['preregistration']}`",
            f"- Full JSON: `{str(FULL_JSON.relative_to(REPO_ROOT))}`",
            f"- Case rows: `{summary['case_rows_csv']}`",
            f"- Trace rows: `{summary['trace_rows_csv']}`",
            f"- Metrics: `{summary['metrics_csv']}`",
            f"- Script: `{str(Path(__file__).relative_to(REPO_ROOT))}`",
            "",
        ]
    )
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_panel(*, mode: str, resume: bool) -> dict[str, Any]:
    prereg = load_preregistration()
    quick = mode == "quick"
    case_path = CASE_ROWS_QUICK_CSV if quick else CASE_ROWS_FULL_CSV
    trace_path = TRACE_ROWS_QUICK_CSV if quick else TRACE_ROWS_FULL_CSV
    metrics_path = METRICS_QUICK_CSV if quick else METRICS_FULL_CSV
    summary_path = QUICK_JSON if quick else FULL_JSON
    progress_path = PROGRESS_QUICK_JSONL if quick else PROGRESS_FULL_JSONL
    stderr_log = STDERR_QUICK_LOG if quick else STDERR_FULL_LOG
    if not resume:
        for path in (case_path, trace_path, metrics_path, summary_path, progress_path):
            if path.exists():
                path.unlink()
        if not quick and DOC_PATH.exists():
            DOC_PATH.unlink()
    cases = prereg["quick_cases" if quick else "cases"]
    done = _row_keys(_read_csv(case_path))
    started = time.time()
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        for case in cases:
            if str(case["case_id"]) in done:
                continue
            row, traces = run_case(client, case)
            _append_csv(case_path, row, CASE_FIELDNAMES)
            for trace in traces:
                _append_csv(trace_path, trace, TRACE_FIELDNAMES)
            _progress(
                progress_path,
                {
                    "stage": "case_done",
                    "case_id": row["case_id"],
                    "original_latency_steps": row["original_latency_steps"],
                    "reconciled_latency_steps": row["reconciled_latency_steps"],
                    "reconciliation_label": row["reconciliation_label"],
                },
            )
    finally:
        client.close()
    summary = summarize(
        _read_csv(case_path),
        _read_csv(trace_path),
        prereg,
        mode=mode,
        elapsed_s=time.time() - started,
        case_path=case_path,
        trace_path=trace_path,
        metrics_path=metrics_path,
    )
    write_json(summary_path, summary)
    _write_metrics(summary, metrics_path)
    write_markdown(summary)
    return summary


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
                    "expected_full_case_rows": payload["expected_full_case_rows"],
                    "expected_quick_case_rows": payload["expected_quick_case_rows"],
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
