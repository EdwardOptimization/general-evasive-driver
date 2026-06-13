"""Phase-4 E2' hardened Chrono two-regime-law confirmation.

M3258 is the Track-E' E2' hardening unit after M3257 reconciled the detector
onset definition. It re-runs E2 at higher validation power on Sedan/TMeasy and
UAZBUS/TMeasy, keeps the clean five-reveal panel plus the delay25 tight
degraded spot, and applies the CP-3 frozen flip-confirmation gate. It is
zero-training pricing evidence and cannot admit Track F by itself.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened.py --quick --resume
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened.py --full --resume --workers 8
"""

from __future__ import annotations

import atexit
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import hashlib
import importlib.util
import json
import math
import os
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
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_e2_chrono_two_regime_smoke as e2_smoke  # noqa: E402


MILESTONE_ID = "m3258-phase4-e2prime-chrono-two-regime-hardening"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2prime_chrono_two_regime_hardened_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2prime_chrono_two_regime_hardened_quick.json"
RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2prime_chrono_two_regime_hardened.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e2prime_chrono_two_regime_hardened"
ROWS_QUICK_CSV = RUN_DIR / "episode_rows_quick.csv"
ROWS_FULL_CSV = RUN_DIR / "episode_rows_full.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
METRICS_FULL_CSV = RUN_DIR / "metrics_full.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
STDERR_QUICK_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
STDERR_FULL_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
DOC_PATH = REPO_ROOT / "docs" / "m3258-phase4-e2prime-chrono-two-regime-hardening.md"

TASK_B_SCRIPT = e2_smoke.TASK_B_SCRIPT
COND_SCRIPT = e2_smoke.COND_SCRIPT
REGIME_SCRIPT = e2_smoke.REGIME_SCRIPT
E0_JSON = e2_smoke.E0_JSON
E1_FULL_JSON = e2_smoke.E1_FULL_JSON
E2_QUICK_JSON = e2_smoke.QUICK_JSON
M3252_FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2_chrono_two_regime_full.json"
M3257_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e3_detector_onset_reconciliation.json"

SEED_BASE = 2026061312
FULL_VARIANTS = ("sedan_tmeasy", "uazbus_tmeasy")
CLEAN_REVEALS = (9.5, 12.0, 16.0, 22.0, 30.0)
TIGHT_REVEALS = (9.5, 12.0)
MU_POINTS = (0.3625, 0.5875, 0.8125, 1.0375)
SEL_SEEDS = (0,)
VAL_SEEDS = tuple(range(30))
QUICK_REVEALS = (9.5,)
QUICK_MUS = (0.3625,)
QUICK_VAL_SEEDS = (0,)
DEGRADED_SPOTS = (
    {"cell_id": "delay25_tight", "delay_steps": 25, "noise_std": 0.0, "reveals": (9.5,)},
)
ORACLE_DVS = (-0.5, 0.0, 0.5)
SEEKER_CANDIDATES = (
    {"ramp_rate": 2000.0, "tau_mult": 1.0, "backoff": 0.06, "strategy": "hold", "dv": 0.0},
    {"ramp_rate": 6000.0, "tau_mult": 1.0, "backoff": 0.06, "strategy": "hold", "dv": 0.0},
    {"ramp_rate": 20000.0, "tau_mult": 1.0, "backoff": 0.06, "strategy": "hold", "dv": 0.0},
    {"ramp_rate": 6000.0, "tau_mult": 0.75, "backoff": 0.06, "strategy": "hold", "dv": 0.0},
    {"ramp_rate": 6000.0, "tau_mult": 1.25, "backoff": 0.15, "strategy": "hold", "dv": 0.0},
    {"ramp_rate": 20000.0, "tau_mult": 1.25, "backoff": 0.15, "strategy": "hold", "dv": 0.0},
)
FIXED_RAMP_CANDIDATES = (
    {"fixed_frac": 0.35, "fixed_hold_s": 1.0},
    {"fixed_frac": 0.70, "fixed_hold_s": 1.0},
)
FIXED_SPEED_CANDIDATES = (5.5, 7.5, 9.5)
BOOTSTRAP_SAMPLES = 4000
POSITIVE_EFFECT_THRESHOLD = 0.15

CLAIM_BOUNDARY = (
    "Phase-4 E2' hardened Chrono two-regime-law confirmation only: scripted "
    "oracle, threshold-seeker, and fixed belief-free controller families are "
    "compared on Sedan/TMeasy and UAZBUS/TMeasy over frozen clean reveal tiers "
    "plus one delay25 tight degraded spot, after M3257 froze the reconciled "
    "detector-onset definition. This is zero-training pricing evidence; it "
    "makes no incumbent mutation, validation ranking, promotion, driver-"
    "performance, full high-fidelity sufficiency, paper, repair-success, "
    "robustness-result, feasibility-proof, Track-F-admission, or self-ID claim."
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


def _candidate_name(candidate: dict[str, Any]) -> str:
    kind = candidate["kind"]
    if kind == "oracle":
        return f"oracle_dv{candidate['dv']:+g}"
    if kind == "seeker":
        return (
            f"seeker_r{candidate['ramp_rate']:g}_tm{candidate['tau_mult']:g}_"
            f"b{candidate['backoff']:g}_{candidate['strategy']}"
        )
    if kind == "fixed_ramp":
        return f"fixedramp_f{candidate['fixed_frac']:g}_h{candidate['fixed_hold_s']:g}"
    if kind == "fixed_speed":
        return f"fixedspeed_v{candidate['v_entry']:g}"
    raise ValueError(f"unknown candidate kind: {kind}")


def controller_candidates() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for dv in ORACLE_DVS:
        out.append({"kind": "oracle", "group": "oracle", "dv": float(dv)})
    for params in SEEKER_CANDIDATES:
        out.append({"kind": "seeker", "group": "seeker", **params})
    for params in FIXED_RAMP_CANDIDATES:
        out.append({"kind": "fixed_ramp", "group": "fixed", **params})
    for v_entry in FIXED_SPEED_CANDIDATES:
        out.append({"kind": "fixed_speed", "group": "fixed", "v_entry": float(v_entry)})
    for candidate in out:
        candidate["name"] = _candidate_name(candidate)
    return out


def build_preregistration() -> dict[str, Any]:
    e0 = e2_smoke.load_e0_envelope()
    e1 = e2_smoke.load_e1_full_decision()
    if not E2_QUICK_JSON.exists():
        raise FileNotFoundError(f"missing E2 quick artifact {E2_QUICK_JSON}")
    if not M3252_FULL_JSON.exists():
        raise FileNotFoundError(f"missing M3252 full artifact {M3252_FULL_JSON}")
    if not M3257_JSON.exists():
        raise FileNotFoundError(f"missing M3257 detector reconciliation artifact {M3257_JSON}")
    quick = _read_json(E2_QUICK_JSON)
    if quick.get("decision", {}).get("e2_quick_verdict") != "protocol_smoke_passed":
        raise RuntimeError("E2 quick protocol smoke did not pass")
    m3252 = _read_json(M3252_FULL_JSON)
    if m3252.get("decision", {}).get("e2_full_verdict") != "chrono_clean_belief_value_positive":
        raise RuntimeError("M3252 did not provide the positive E2 flip that E2' hardens")
    m3257 = _read_json(M3257_JSON)
    if m3257.get("decision", {}).get("e2_prime_dependency_ready") is not True:
        raise RuntimeError("M3257 did not mark the E2' detector-definition dependency ready")
    m3257_prereg = _read_json(REPO_ROOT / str(m3257["preregistration"]))
    allowed = tuple(e0["e1_spread_envelope"]["recommended_e1_population_panel"]["vehicle_variants"])
    for variant in FULL_VARIANTS:
        if variant not in allowed:
            raise RuntimeError(f"full variant {variant!r} is outside the E0-admitted envelope")
    return {
        "protocol": "phase4_e2prime_chrono_two_regime_hardened_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 Track E' E2' hardened two-regime-law confirmation",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_e2prime_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "dependencies": {
            "e0_artifact": str(E0_JSON.relative_to(REPO_ROOT)),
            "e0_axis_table_sha256": e0["axis_table_sha256"],
            "e1_full_artifact": str(E1_FULL_JSON.relative_to(REPO_ROOT)),
            "e1_full_verdict": e1["decision"]["e1_full_verdict"],
            "e2_quick_artifact": str(E2_QUICK_JSON.relative_to(REPO_ROOT)),
            "m3252_full_artifact": str(M3252_FULL_JSON.relative_to(REPO_ROOT)),
            "m3252_positive_reveals_m": m3252.get("decision", {}).get("qualifying_clean_reveals_m", []),
            "m3257_detector_reconciliation_artifact": str(M3257_JSON.relative_to(REPO_ROOT)),
            "m3257_detector_reconciliation_prereg": m3257["preregistration"],
            "m3257_e2_prime_dependency_ready": True,
        },
        "chrono_variants": list(FULL_VARIANTS),
        "required_non_sedan_variant_count": 1,
        "clean_reveal_tiers_m": list(CLEAN_REVEALS),
        "tight_reveal_tiers_m": list(TIGHT_REVEALS),
        "mu_points": list(MU_POINTS),
        "selection_seeds": list(SEL_SEEDS),
        "validation_seeds": list(VAL_SEEDS),
        "min_validation_seeds_per_cell": 30,
        "quick_smoke": {
            "mode_is_verdict": False,
            "reveal_tiers_m": list(QUICK_REVEALS),
            "mu_points": list(QUICK_MUS),
            "validation_seeds": list(QUICK_VAL_SEEDS),
            "required_before_full": True,
        },
        "seed_streams": {
            "selection_namespace": "selection",
            "validation_namespace": "validation",
            "disjointness_rule": (
                "rollout seeds are sha256(seed_base, namespace, variant/cell/reveal/mu, seed_index); "
                "selection and validation use different namespaces even when seed_index labels overlap"
            ),
        },
        "degraded_spots": list(DEGRADED_SPOTS),
        "controller_candidates": controller_candidates(),
        "calibration": {
            "source": "phase4_e2_chrono_two_regime_smoke.calibrate_tau_for_variant",
            "variant_scope": "per E2' Chrono vehicle variant",
            "tau_rule": "tau = max(1.2 * max_shortfall_on_sublimit_fixed_ramp, 0.08)",
        },
        "detector_onset_rule": m3257_prereg["onset_definitions"]["reconciled_actor_visible_onset"],
        "runtime_gates": [
            "E2 quick artifact exists and passed before E2'",
            "M3252 positive full E2 artifact exists before E2'",
            "M3257 detector-onset reconciliation artifact exists and marks E2' dependency ready",
            "quick smoke runs before the managed full E2' harness run",
            "selection and validation seed streams are disjoint",
            "validation seed count per cell is >= 30",
            "at least two Chrono vehicle variants are included and at least one is non-Sedan",
            "clean selection rows cover every candidate/reveal/mu/selection seed",
            "clean validation rows cover oracle, best_seeker, best_fixed, and best_floor logical arms",
            "delay25_tight degraded spot rows are written as secondary non-gating readouts",
            "reset obs are finite obs72 and backend_info variant ids match",
            "paired CIs are reported per variant and reveal for oracle minus best_floor",
            "Track F remains blocked regardless of the E2' verdict until a later GPU-days checkpoint",
        ],
        "preregistered_readouts": {
            "primary_clean_per_variant_reveal": (
                "success_rate(oracle) - success_rate(best_floor), paired on validation mu x seed units "
                "within each vehicle variant and reveal tier"
            ),
            "secondary_clean_oracle_minus_seeker": "success_rate(oracle) - success_rate(best_seeker), paired within variant/reveal",
            "detection_value_clean": "success_rate(best_seeker) - success_rate(best_fixed), paired within variant/reveal",
            "degraded_spot_secondary": "same readouts on delay25_tight using the clean-selected arms",
            "positive_rule": (
                "A variant/reveal clean cell is positive when oracle - best_floor has paired "
                "CI95 lower > 0. E2' confirms the Phase-4 flip only if >=2 tight reveal "
                "cells are positive within each of >=2 vehicle variants."
            ),
            "legacy_effect_size_reference": (
                "M3252's +0.15 effect-size threshold is still reported for continuity but is "
                "not the CP-3 flip-confirmation gate; CP-3 froze CI95 lower > 0 in >=2 tight "
                "reveal cells on >=2 variants."
            ),
        },
        "decision_rule": (
            "M3258 completes when the quick smoke and full panel run under this preregistration, "
            "write JSON/CSV/doc artifacts, report per-variant paired CIs, apply the frozen "
            "flip-confirmation rule, and keep Track F blocked. A confirmed flip only routes to "
            "a later GPU-days checkpoint; it does not open Track F directly."
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
    if not payload.get("frozen_before_any_e2prime_rollout"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_e2prime_rollout")
    return payload


def _make_controller(reg, mod_b, interp, *, reveal: float, mu: float, tau: float, candidate: dict[str, Any]) -> Any:
    design = reg.make_design(mod_b, float(reveal))
    kind = candidate["kind"]
    name = candidate["name"]
    if kind == "oracle":
        return reg.RampPolicyController(
            mod_b,
            interp,
            design,
            name,
            mode="oracle",
            mu_true=float(mu),
            dv=float(candidate["dv"]),
        )
    if kind == "seeker":
        return reg.RampPolicyController(
            mod_b,
            interp,
            design,
            name,
            mode="seeker",
            ramp_rate=float(candidate["ramp_rate"]),
            tau=float(tau) * float(candidate["tau_mult"]),
            backoff=float(candidate["backoff"]),
            strategy=str(candidate["strategy"]),
            dv=float(candidate.get("dv", 0.0)),
        )
    if kind == "fixed_ramp":
        return reg.RampPolicyController(
            mod_b,
            interp,
            design,
            name,
            mode="fixed_ramp",
            fixed_frac=float(candidate["fixed_frac"]),
            fixed_hold_s=float(candidate["fixed_hold_s"]),
        )
    if kind == "fixed_speed":
        plan = mod_b.PlanSpec(name=name, v_entry=float(candidate["v_entry"]), brake_to=None, steer_cap=0.85)
        return mod_b.CommitmentController(plan, design)
    raise ValueError(f"unknown candidate kind: {kind}")


FIELDNAMES = [
    "phase",
    "variant",
    "cell_id",
    "delay_steps",
    "noise_std",
    "reveal_m",
    "mu",
    "seed_index",
    "seed",
    "logical_arm",
    "candidate_group",
    "candidate_name",
    "candidate_json",
    "outcome",
    "success",
    "score",
    "steps",
    "termination_reason",
    "completion_reason",
    "obstacle_visible_step",
    "min_clearance_margin",
    "reset_obs_finite",
    "variant_match",
    "tau",
    "mu_hat",
    "censored",
    "id_step",
    "max_shortfall",
    "overshoot_events",
    "n_onsets",
    "backend_model",
    "backend_tire",
    "vehicle_total_mass",
    "target_mass",
    "true_trace_signature",
    "policy_trace_signature",
    "claim_boundary",
]


def _append_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        if new_file:
            writer.writeheader()
        writer.writerow({key: _jsonable(row.get(key, "")) for key in FIELDNAMES})


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _score(result: dict[str, Any]) -> float:
    margin = result.get("min_clearance_margin")
    clipped_margin = float(np.clip(float(margin), -2.0, 2.0)) if isinstance(margin, (int, float)) else 0.0
    return (1000.0 if result["success"] else 0.0) + 10.0 * clipped_margin + 0.01 * float(result["steps"])


def _row(
    *,
    phase: str,
    variant: str,
    cell: dict[str, Any],
    reveal: float,
    mu: float,
    seed_index: int,
    seed: int,
    logical_arm: str,
    candidate: dict[str, Any],
    tau: float,
    result: dict[str, Any],
) -> dict[str, Any]:
    telemetry = result.get("telemetry", {})
    backend = result.get("backend_info", {})
    return {
        "phase": phase,
        "variant": variant,
        "cell_id": cell["cell_id"],
        "delay_steps": int(cell["delay_steps"]),
        "noise_std": float(cell["noise_std"]),
        "reveal_m": float(reveal),
        "mu": float(mu),
        "seed_index": int(seed_index),
        "seed": int(seed),
        "logical_arm": logical_arm,
        "candidate_group": candidate["group"],
        "candidate_name": candidate["name"],
        "candidate_json": json.dumps(_jsonable(candidate), sort_keys=True, separators=(",", ":")),
        "outcome": result["outcome"],
        "success": bool(result["success"]),
        "score": round(float(_score(result)), 6),
        "steps": int(result["steps"]),
        "termination_reason": result["termination_reason"],
        "completion_reason": result["completion_reason"],
        "obstacle_visible_step": result["obstacle_visible_step"],
        "min_clearance_margin": result["min_clearance_margin"],
        "reset_obs_finite": bool(result["reset_obs_finite"]),
        "variant_match": bool(result["variant_match"]),
        "tau": round(float(tau), 6),
        "mu_hat": telemetry.get("mu_hat", ""),
        "censored": telemetry.get("censored", ""),
        "id_step": telemetry.get("id_step", ""),
        "max_shortfall": telemetry.get("max_shortfall", ""),
        "overshoot_events": telemetry.get("overshoot_events", ""),
        "n_onsets": telemetry.get("n_onsets", ""),
        "backend_model": backend.get("chrono_vehicle_model", ""),
        "backend_tire": backend.get("chrono_tire_model", ""),
        "vehicle_total_mass": backend.get("vehicle_total_mass", ""),
        "target_mass": backend.get("target_mass", ""),
        "true_trace_signature": result["true_trace_signature"],
        "policy_trace_signature": result["policy_trace_signature"],
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _selection_units(prereg: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = prereg["controller_candidates"]
    cell = {"cell_id": "clean", "delay_steps": 0, "noise_std": 0.0}
    units = []
    for variant in prereg["chrono_variants"]:
        for reveal in prereg["clean_reveal_tiers_m"]:
            for mu in prereg["mu_points"]:
                for seed_index in prereg["selection_seeds"]:
                    seed = _seed_for("selection", variant, reveal, mu, seed_index)
                    for candidate in candidates:
                        units.append(
                            {
                                "phase": "selection",
                                "variant": variant,
                                "cell": cell,
                                "reveal": float(reveal),
                                "mu": float(mu),
                                "seed_index": int(seed_index),
                                "seed": seed,
                                "logical_arm": candidate["group"],
                                "candidate": candidate,
                            }
                        )
    return units


def _done_keys(path: Path) -> set[tuple[str, str, str, str, str, str, str, str]]:
    keys = set()
    for row in _read_csv_rows(path):
        keys.add(
            (
                row["phase"],
                row["variant"],
                row["cell_id"],
                row["reveal_m"],
                row["mu"],
                row["seed"],
                row["logical_arm"],
                row["candidate_name"],
            )
        )
    return keys


def _unit_key(unit: dict[str, Any]) -> tuple[str, str, str, str, str, str, str, str]:
    cell = unit["cell"]
    candidate = unit["candidate"]
    return (
        unit["phase"],
        unit["variant"],
        cell["cell_id"],
        str(unit["reveal"]),
        str(unit["mu"]),
        str(unit["seed"]),
        unit["logical_arm"],
        candidate["name"],
    )


def _progress(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def _mean_success_score(rows: list[dict[str, str]]) -> tuple[float, float]:
    if not rows:
        return (float("-inf"), float("-inf"))
    success = float(np.mean([1.0 if row["success"] == "True" else 0.0 for row in rows]))
    score = float(np.mean([float(row["score"]) for row in rows]))
    return success, score


def select_arms(rows: list[dict[str, str]], prereg: dict[str, Any]) -> dict[str, Any]:
    selections: dict[str, Any] = {}
    clean_selection = [row for row in rows if row["phase"] == "selection" and row["cell_id"] == "clean"]
    candidates = {candidate["name"]: candidate for candidate in prereg["controller_candidates"]}
    for variant in prereg["chrono_variants"]:
        for reveal in prereg["clean_reveal_tiers_m"]:
            key = f"{variant}|{float(reveal):g}"
            reveal_rows = [row for row in clean_selection if row["variant"] == variant and float(row["reveal_m"]) == float(reveal)]
            by_name = {
                name: [row for row in reveal_rows if row["candidate_name"] == name]
                for name in candidates
            }
            seeker_names = [name for name, cand in candidates.items() if cand["group"] == "seeker"]
            fixed_names = [name for name, cand in candidates.items() if cand["group"] == "fixed"]
            best_seeker = max(seeker_names, key=lambda name: _mean_success_score(by_name[name]))
            best_fixed = max(fixed_names, key=lambda name: _mean_success_score(by_name[name]))
            best_floor = max((best_seeker, best_fixed), key=lambda name: _mean_success_score(by_name[name]))
            oracle_by_mu = {}
            for mu in prereg["mu_points"]:
                mu_rows = [row for row in reveal_rows if float(row["mu"]) == float(mu)]
                oracle_names = [name for name, cand in candidates.items() if cand["group"] == "oracle"]
                best_oracle = max(
                    oracle_names,
                    key=lambda name: _mean_success_score([row for row in mu_rows if row["candidate_name"] == name]),
                )
                oracle_by_mu[f"{float(mu):g}"] = best_oracle
            selections[key] = {
                "best_seeker": best_seeker,
                "best_fixed": best_fixed,
                "best_floor": best_floor,
                "oracle_by_mu": oracle_by_mu,
                "selection_scores": {
                    "best_seeker": _mean_success_score(by_name[best_seeker]),
                    "best_fixed": _mean_success_score(by_name[best_fixed]),
                    "best_floor": _mean_success_score(by_name[best_floor]),
                },
            }
    return selections


def _validation_units(prereg: dict[str, Any], selections: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = {candidate["name"]: candidate for candidate in prereg["controller_candidates"]}
    units = []
    clean_cell = {"cell_id": "clean", "delay_steps": 0, "noise_std": 0.0}
    cells = [clean_cell] + prereg["degraded_spots"]
    for variant in prereg["chrono_variants"]:
        for cell in cells:
            reveals = prereg["clean_reveal_tiers_m"] if cell["cell_id"] == "clean" else cell["reveals"]
            for reveal in reveals:
                sel = selections[f"{variant}|{float(reveal):g}"]
                for mu in prereg["mu_points"]:
                    logical = {
                        "oracle": sel["oracle_by_mu"][f"{float(mu):g}"],
                        "best_seeker": sel["best_seeker"],
                        "best_fixed": sel["best_fixed"],
                        "best_floor": sel["best_floor"],
                    }
                    for seed_index in prereg["validation_seeds"]:
                        seed = _seed_for("validation", variant, cell["cell_id"], reveal, mu, seed_index)
                        for logical_arm, name in logical.items():
                            units.append(
                                {
                                    "phase": "validation",
                                    "variant": variant,
                                    "cell": cell,
                                    "reveal": float(reveal),
                                    "mu": float(mu),
                                    "seed_index": int(seed_index),
                                    "seed": seed,
                                    "logical_arm": logical_arm,
                                    "candidate": candidates[name],
                                }
                            )
    return units


def _run_units(
    *,
    client: ChronoWorkerClient,
    reg,
    mod_b,
    interp,
    units: list[dict[str, Any]],
    calibration: dict[str, dict[str, Any]],
    done: set[tuple[str, str, str, str, str, str, str, str]],
    started: float,
    stage: str,
    rows_csv: Path,
    progress_jsonl: Path,
) -> int:
    completed = 0
    for unit in units:
        cell = unit["cell"]
        candidate = unit["candidate"]
        if _unit_key(unit) in done:
            completed += 1
            continue
        tau = float(calibration[unit["variant"]]["tau"])
        scenario = e2_smoke._make_scenario(
            reg,
            mod_b,
            interp,
            reveal=unit["reveal"],
            mu=unit["mu"],
            seed=unit["seed"],
            variant=unit["variant"],
        )
        controller = _make_controller(
            reg,
            mod_b,
            interp,
            reveal=unit["reveal"],
            mu=unit["mu"],
            tau=tau,
            candidate=candidate,
        )
        result = e2_smoke.run_controller_episode(
            client,
            scenario,
            controller,
            variant=unit["variant"],
            delay_steps=int(cell["delay_steps"]),
            noise_std=float(cell["noise_std"]),
            seed=int(unit["seed"]),
        )
        _append_row(
            rows_csv,
            _row(
                phase=unit["phase"],
                variant=unit["variant"],
                cell=cell,
                reveal=unit["reveal"],
                mu=unit["mu"],
                seed_index=unit["seed_index"],
                seed=unit["seed"],
                logical_arm=unit["logical_arm"],
                candidate=candidate,
                tau=tau,
                result=result,
            ),
        )
        completed += 1
        _progress(
            progress_jsonl,
            {
                "stage": stage,
                "completed": completed,
                "total": len(units),
                "phase": unit["phase"],
                "variant": unit["variant"],
                "cell_id": cell["cell_id"],
                "reveal_m": unit["reveal"],
                "mu": unit["mu"],
                "logical_arm": unit["logical_arm"],
                "candidate": candidate["name"],
                "outcome": result["outcome"],
                "elapsed_s": round(time.time() - started, 1),
            }
        )
    return completed


_WORKER_STATE: dict[str, Any] = {}


def _worker_stderr_path(stderr_log: str) -> Path:
    base = Path(stderr_log)
    return base.with_name(f"{base.stem}_worker_{os.getpid()}{base.suffix}")


def _worker_context(stderr_log: str):
    if not _WORKER_STATE:
        reg = _load_module(REGIME_SCRIPT, f"ramp_policy_voi_regime_worker_{os.getpid()}")
        mod_b = _load_module(TASK_B_SCRIPT, f"voi_commitment_task_design_worker_{os.getpid()}")
        mod_c = _load_module(COND_SCRIPT, f"voi_conditional_prior_worker_{os.getpid()}")
        client = ChronoWorkerClient(stderr_log=_worker_stderr_path(stderr_log))
        _WORKER_STATE.update({"reg": reg, "mod_b": mod_b, "interp": mod_c.interp_lin, "client": client})
        atexit.register(client.close)
    return _WORKER_STATE["client"], _WORKER_STATE["reg"], _WORKER_STATE["mod_b"], _WORKER_STATE["interp"]


def _run_unit_worker(unit: dict[str, Any], calibration: dict[str, dict[str, Any]], stderr_log: str) -> dict[str, Any]:
    client, reg, mod_b, interp = _worker_context(stderr_log)
    cell = unit["cell"]
    candidate = unit["candidate"]
    tau = float(calibration[unit["variant"]]["tau"])
    scenario = e2_smoke._make_scenario(
        reg,
        mod_b,
        interp,
        reveal=unit["reveal"],
        mu=unit["mu"],
        seed=unit["seed"],
        variant=unit["variant"],
    )
    controller = _make_controller(
        reg,
        mod_b,
        interp,
        reveal=unit["reveal"],
        mu=unit["mu"],
        tau=tau,
        candidate=candidate,
    )
    result = e2_smoke.run_controller_episode(
        client,
        scenario,
        controller,
        variant=unit["variant"],
        delay_steps=int(cell["delay_steps"]),
        noise_std=float(cell["noise_std"]),
        seed=int(unit["seed"]),
    )
    return {
        "row": _row(
            phase=unit["phase"],
            variant=unit["variant"],
            cell=cell,
            reveal=unit["reveal"],
            mu=unit["mu"],
            seed_index=unit["seed_index"],
            seed=unit["seed"],
            logical_arm=unit["logical_arm"],
            candidate=candidate,
            tau=tau,
            result=result,
        ),
        "progress": {
            "phase": unit["phase"],
            "variant": unit["variant"],
            "cell_id": cell["cell_id"],
            "reveal_m": unit["reveal"],
            "mu": unit["mu"],
            "logical_arm": unit["logical_arm"],
            "candidate": candidate["name"],
            "outcome": result["outcome"],
        },
    }


def _run_units_parallel(
    *,
    units: list[dict[str, Any]],
    calibration: dict[str, dict[str, Any]],
    done: set[tuple[str, str, str, str, str, str, str, str]],
    started: float,
    stage: str,
    rows_csv: Path,
    progress_jsonl: Path,
    stderr_log: Path,
    workers: int,
) -> int:
    pending = [unit for unit in units if _unit_key(unit) not in done]
    completed = len(units) - len(pending)
    if not pending:
        return len(units)
    with ProcessPoolExecutor(max_workers=max(1, int(workers))) as pool:
        futures = [pool.submit(_run_unit_worker, unit, calibration, str(stderr_log)) for unit in pending]
        for future in as_completed(futures):
            payload = future.result()
            _append_row(rows_csv, payload["row"])
            completed += 1
            progress = {
                "stage": stage,
                "completed": completed,
                "total": len(units),
                "elapsed_s": round(time.time() - started, 1),
                **payload["progress"],
            }
            _progress(progress_jsonl, progress)
    return completed


def _quick_prereg(prereg: dict[str, Any]) -> dict[str, Any]:
    quick = json.loads(json.dumps(_jsonable(prereg)))
    quick["clean_reveal_tiers_m"] = list(QUICK_REVEALS)
    quick["mu_points"] = list(QUICK_MUS)
    quick["validation_seeds"] = list(QUICK_VAL_SEEDS)
    quick["degraded_spots"] = [
        {**cell, "reveals": [float(reveal) for reveal in cell["reveals"] if float(reveal) in QUICK_REVEALS]}
        for cell in prereg["degraded_spots"]
    ]
    quick["degraded_spots"] = [cell for cell in quick["degraded_spots"] if cell["reveals"]]
    return quick


def _calibrate_variants(
    prereg: dict[str, Any],
    *,
    reg,
    mod_b,
    interp,
    stderr_log: Path,
    progress_jsonl: Path,
) -> dict[str, dict[str, Any]]:
    calibration: dict[str, dict[str, Any]] = {}
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        for variant in prereg["chrono_variants"]:
            calibration[variant] = e2_smoke.calibrate_tau_for_variant(client, reg, mod_b, interp, variant=variant)
            _progress(progress_jsonl, {"stage": "calibration_done", "variant": variant, **calibration[variant]})
    finally:
        client.close()
    return calibration


def run_quick(*, resume: bool) -> dict[str, Any]:
    prereg = load_preregistration()
    reg = _load_module(REGIME_SCRIPT, "ramp_policy_voi_regime")
    mod_b = _load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = _load_module(COND_SCRIPT, "voi_conditional_prior")
    interp = mod_c.interp_lin
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not resume:
        for path in (ROWS_QUICK_CSV, METRICS_QUICK_CSV, PROGRESS_QUICK_JSONL, QUICK_JSON):
            if path.exists():
                path.unlink()
    started = time.time()
    quick_prereg = _quick_prereg(prereg)
    done = _done_keys(ROWS_QUICK_CSV) if resume else set()
    calibration = _calibrate_variants(
        quick_prereg,
        reg=reg,
        mod_b=mod_b,
        interp=interp,
        stderr_log=STDERR_QUICK_LOG,
        progress_jsonl=PROGRESS_QUICK_JSONL,
    )
    client = ChronoWorkerClient(stderr_log=STDERR_QUICK_LOG)
    try:
        selection_units = _selection_units(quick_prereg)
        _run_units(
            client=client,
            reg=reg,
            mod_b=mod_b,
            interp=interp,
            units=selection_units,
            calibration=calibration,
            done=done,
            started=started,
            stage="selection_unit_done",
            rows_csv=ROWS_QUICK_CSV,
            progress_jsonl=PROGRESS_QUICK_JSONL,
        )
        rows = _read_csv_rows(ROWS_QUICK_CSV)
        selections = select_arms(rows, quick_prereg)
        validation_units = _validation_units(quick_prereg, selections)
        done = _done_keys(ROWS_QUICK_CSV)
        _run_units(
            client=client,
            reg=reg,
            mod_b=mod_b,
            interp=interp,
            units=validation_units,
            calibration=calibration,
            done=done,
            started=started,
            stage="validation_unit_done",
            rows_csv=ROWS_QUICK_CSV,
            progress_jsonl=PROGRESS_QUICK_JSONL,
        )
    finally:
        client.close()
    rows = _read_csv_rows(ROWS_QUICK_CSV)
    selections = select_arms(rows, quick_prereg)
    summary = summarize_panel(
        rows,
        quick_prereg,
        selections=selections,
        calibration=calibration,
        elapsed_s=time.time() - started,
        mode="quick",
        rows_csv=ROWS_QUICK_CSV,
        metrics_csv=METRICS_QUICK_CSV,
        require_full_power=False,
    )
    summary["quick_mode_is_verdict"] = False
    summary["decision"]["e2prime_quick_verdict"] = "protocol_smoke_passed" if summary["protocol_gates"]["all_passed"] else "protocol_smoke_failed"
    summary["decision"]["flip_confirmation_verdict"] = "not_decided_by_quick_mode"
    write_json(QUICK_JSON, summary)
    write_metrics(summary, METRICS_QUICK_CSV)
    return summary


def run_full(*, resume: bool, workers: int) -> dict[str, Any]:
    prereg = load_preregistration()
    if not QUICK_JSON.exists():
        raise FileNotFoundError(f"missing E2' quick artifact {QUICK_JSON}; run --quick before --full")
    quick = _read_json(QUICK_JSON)
    if quick.get("decision", {}).get("e2prime_quick_verdict") != "protocol_smoke_passed":
        raise RuntimeError("E2' quick protocol smoke did not pass")
    reg = _load_module(REGIME_SCRIPT, "ramp_policy_voi_regime")
    mod_b = _load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = _load_module(COND_SCRIPT, "voi_conditional_prior")
    interp = mod_c.interp_lin
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not resume:
        for path in (ROWS_FULL_CSV, METRICS_FULL_CSV, PROGRESS_FULL_JSONL, RESULTS_JSON, DOC_PATH):
            if path.exists():
                path.unlink()
    started = time.time()
    done = _done_keys(ROWS_FULL_CSV) if resume else set()
    calibration = _calibrate_variants(
        prereg,
        reg=reg,
        mod_b=mod_b,
        interp=interp,
        stderr_log=STDERR_FULL_LOG,
        progress_jsonl=PROGRESS_FULL_JSONL,
    )
    selection_units = _selection_units(prereg)
    if workers > 1:
        _run_units_parallel(
            units=selection_units,
            calibration=calibration,
            done=done,
            started=started,
            stage="selection_unit_done",
            rows_csv=ROWS_FULL_CSV,
            progress_jsonl=PROGRESS_FULL_JSONL,
            stderr_log=STDERR_FULL_LOG,
            workers=workers,
        )
    else:
        client = ChronoWorkerClient(stderr_log=STDERR_FULL_LOG)
        try:
            _run_units(
                client=client,
                reg=reg,
                mod_b=mod_b,
                interp=interp,
                units=selection_units,
                calibration=calibration,
                done=done,
                started=started,
                stage="selection_unit_done",
                rows_csv=ROWS_FULL_CSV,
                progress_jsonl=PROGRESS_FULL_JSONL,
            )
        finally:
            client.close()
    rows = _read_csv_rows(ROWS_FULL_CSV)
    selections = select_arms(rows, prereg)
    validation_units = _validation_units(prereg, selections)
    done = _done_keys(ROWS_FULL_CSV)
    if workers > 1:
        _run_units_parallel(
            units=validation_units,
            calibration=calibration,
            done=done,
            started=started,
            stage="validation_unit_done",
            rows_csv=ROWS_FULL_CSV,
            progress_jsonl=PROGRESS_FULL_JSONL,
            stderr_log=STDERR_FULL_LOG,
            workers=workers,
        )
    else:
        client = ChronoWorkerClient(stderr_log=STDERR_FULL_LOG)
        try:
            _run_units(
                client=client,
                reg=reg,
                mod_b=mod_b,
                interp=interp,
                units=validation_units,
                calibration=calibration,
                done=done,
                started=started,
                stage="validation_unit_done",
                rows_csv=ROWS_FULL_CSV,
                progress_jsonl=PROGRESS_FULL_JSONL,
            )
        finally:
            client.close()
    rows = _read_csv_rows(ROWS_FULL_CSV)
    selections = select_arms(rows, prereg)
    summary = summarize_panel(
        rows,
        prereg,
        selections=selections,
        calibration=calibration,
        elapsed_s=time.time() - started,
        mode="full",
        rows_csv=ROWS_FULL_CSV,
        metrics_csv=METRICS_FULL_CSV,
        require_full_power=True,
    )
    write_json(RESULTS_JSON, summary)
    write_metrics(summary, METRICS_FULL_CSV)
    write_markdown(summary)
    return summary


def _paired_values(
    rows: list[dict[str, str]],
    *,
    cell_id: str,
    reveal: float,
    left: str,
    right: str,
    variant: str | None = None,
) -> list[float]:
    keyed: dict[tuple[str, str, str, str], dict[str, float]] = {}
    for row in rows:
        if row["phase"] != "validation" or row["cell_id"] != cell_id or float(row["reveal_m"]) != float(reveal):
            continue
        if variant is not None and row["variant"] != variant:
            continue
        if row["logical_arm"] not in (left, right):
            continue
        key = (row["variant"], row["mu"], row["seed"], row["cell_id"])
        keyed.setdefault(key, {})[row["logical_arm"]] = 1.0 if row["success"] == "True" else 0.0
    vals = []
    for pair in keyed.values():
        if left in pair and right in pair:
            vals.append(pair[left] - pair[right])
    return vals


def _paired_readout(
    rows: list[dict[str, str]],
    *,
    cell_id: str,
    reveal: float,
    left: str,
    right: str,
    variant: str | None = None,
) -> dict[str, Any]:
    vals = _paired_values(rows, cell_id=cell_id, reveal=reveal, left=left, right=right, variant=variant)
    if not vals:
        return {"value": None, "paired_bootstrap_ci95": [None, None], "n_pairs": 0}
    arr = np.asarray(vals, dtype=np.float64)
    rng = np.random.default_rng(_seed_for("bootstrap", variant or "pooled", cell_id, reveal, left, right))
    boots = [float(np.mean(arr[rng.integers(0, len(arr), size=len(arr))])) for _ in range(BOOTSTRAP_SAMPLES)]
    return {
        "value": round(float(np.mean(arr)), 4),
        "paired_bootstrap_ci95": [round(float(np.quantile(boots, 0.025)), 4), round(float(np.quantile(boots, 0.975)), 4)],
        "n_pairs": int(len(arr)),
        "raw_differences": [round(float(v), 4) for v in vals],
    }


def _readout_qualifies_ci_lower(readout: dict[str, Any]) -> bool:
    return (
        readout["value"] is not None
        and readout["paired_bootstrap_ci95"][0] is not None
        and float(readout["paired_bootstrap_ci95"][0]) > 0.0
    )


def summarize_panel(
    rows: list[dict[str, str]],
    prereg: dict[str, Any],
    *,
    selections: dict[str, Any],
    calibration: dict[str, dict[str, Any]],
    elapsed_s: float,
    mode: str,
    rows_csv: Path,
    metrics_csv: Path,
    require_full_power: bool,
) -> dict[str, Any]:
    selection_expected = len(_selection_units(prereg))
    validation_expected = len(_validation_units(prereg, selections))
    selection_rows = [row for row in rows if row["phase"] == "selection"]
    validation_rows = [row for row in rows if row["phase"] == "validation"]
    reset_obs_finite_all = all(row["reset_obs_finite"] == "True" for row in rows)
    variant_match_all = all(row["variant_match"] == "True" for row in rows)
    non_sedan_variants = [variant for variant in prereg["chrono_variants"] if not str(variant).startswith("sedan")]
    clean_readouts: dict[str, Any] = {}
    clean_readouts_by_variant: dict[str, Any] = {}
    qualifying_by_variant: dict[str, list[float]] = {}
    legacy_effect_qualifying_by_variant: dict[str, list[float]] = {}
    for reveal in prereg["clean_reveal_tiers_m"]:
        primary = _paired_readout(rows, cell_id="clean", reveal=float(reveal), left="oracle", right="best_floor")
        oracle_minus_seeker = _paired_readout(rows, cell_id="clean", reveal=float(reveal), left="oracle", right="best_seeker")
        seeker_minus_fixed = _paired_readout(rows, cell_id="clean", reveal=float(reveal), left="best_seeker", right="best_fixed")
        legacy_qualifies = (
            primary["value"] is not None
            and float(primary["value"]) >= POSITIVE_EFFECT_THRESHOLD
            and primary["paired_bootstrap_ci95"][0] is not None
            and float(primary["paired_bootstrap_ci95"][0]) > 0.0
        )
        clean_readouts[f"{float(reveal):g}"] = {
            "oracle_minus_best_floor": primary,
            "oracle_minus_best_seeker": oracle_minus_seeker,
            "best_seeker_minus_best_fixed": seeker_minus_fixed,
            "qualifies_legacy_effect_positive": legacy_qualifies,
        }
    for variant in prereg["chrono_variants"]:
        variant_readouts: dict[str, Any] = {}
        qualifying_by_variant[str(variant)] = []
        legacy_effect_qualifying_by_variant[str(variant)] = []
        for reveal in prereg["clean_reveal_tiers_m"]:
            primary = _paired_readout(
                rows,
                cell_id="clean",
                reveal=float(reveal),
                left="oracle",
                right="best_floor",
                variant=str(variant),
            )
            oracle_minus_seeker = _paired_readout(
                rows,
                cell_id="clean",
                reveal=float(reveal),
                left="oracle",
                right="best_seeker",
                variant=str(variant),
            )
            seeker_minus_fixed = _paired_readout(
                rows,
                cell_id="clean",
                reveal=float(reveal),
                left="best_seeker",
                right="best_fixed",
                variant=str(variant),
            )
            qualifies_ci = _readout_qualifies_ci_lower(primary)
            qualifies_legacy = (
                primary["value"] is not None
                and float(primary["value"]) >= POSITIVE_EFFECT_THRESHOLD
                and qualifies_ci
            )
            if qualifies_ci:
                qualifying_by_variant[str(variant)].append(float(reveal))
            if qualifies_legacy:
                legacy_effect_qualifying_by_variant[str(variant)].append(float(reveal))
            variant_readouts[f"{float(reveal):g}"] = {
                "oracle_minus_best_floor": primary,
                "oracle_minus_best_seeker": oracle_minus_seeker,
                "best_seeker_minus_best_fixed": seeker_minus_fixed,
                "qualifies_ci_lower_positive": qualifies_ci,
                "qualifies_legacy_effect_positive": qualifies_legacy,
            }
        clean_readouts_by_variant[str(variant)] = variant_readouts
    degraded_readouts: dict[str, Any] = {}
    for cell in prereg["degraded_spots"]:
        by_variant = {}
        for variant in prereg["chrono_variants"]:
            by_reveal = {}
            for reveal in cell["reveals"]:
                by_reveal[f"{float(reveal):g}"] = {
                    "oracle_minus_best_floor": _paired_readout(
                        rows,
                        cell_id=cell["cell_id"],
                        reveal=float(reveal),
                        left="oracle",
                        right="best_floor",
                        variant=str(variant),
                    ),
                    "oracle_minus_best_seeker": _paired_readout(
                        rows,
                        cell_id=cell["cell_id"],
                        reveal=float(reveal),
                        left="oracle",
                        right="best_seeker",
                        variant=str(variant),
                    ),
                    "best_seeker_minus_best_fixed": _paired_readout(
                        rows,
                        cell_id=cell["cell_id"],
                        reveal=float(reveal),
                        left="best_seeker",
                        right="best_fixed",
                        variant=str(variant),
                    ),
                }
            by_variant[str(variant)] = by_reveal
        degraded_readouts[cell["cell_id"]] = {
            "delay_steps": cell["delay_steps"],
            "noise_std": cell["noise_std"],
            "by_variant": by_variant,
        }
    tight_reveals = {float(reveal) for reveal in prereg["tight_reveal_tiers_m"]}
    variants_confirming_flip = [
        variant
        for variant, reveals in qualifying_by_variant.items()
        if len([reveal for reveal in reveals if float(reveal) in tight_reveals]) >= 2
    ]
    tight_positive_cell_count = sum(
        1
        for reveals in qualifying_by_variant.values()
        for reveal in reveals
        if float(reveal) in tight_reveals
    )
    flip_confirmed = len(variants_confirming_flip) >= 2
    min_validation_seed_count = len(prereg["validation_seeds"])
    protocol_gates = {
        "selection_rows_complete": len(selection_rows) == selection_expected,
        "validation_rows_complete": len(validation_rows) == validation_expected,
        "reset_obs_finite_all": reset_obs_finite_all,
        "variant_match_all": variant_match_all,
        "calibration_written": set(calibration) == set(prereg["chrono_variants"]),
        "paired_clean_readouts_present": all(
            clean_readouts_by_variant[str(variant)][f"{float(r):g}"]["oracle_minus_best_floor"]["n_pairs"] > 0
            for variant in prereg["chrono_variants"]
            for r in prereg["clean_reveal_tiers_m"]
        ),
        "min_validation_seeds_per_cell": (not require_full_power) or min_validation_seed_count >= int(prereg["min_validation_seeds_per_cell"]),
        "vehicle_variant_count": len(prereg["chrono_variants"]) >= 2,
        "non_sedan_variant_present": len(non_sedan_variants) >= int(prereg["required_non_sedan_variant_count"]),
        "track_f_not_admitted": True,
    }
    protocol_gates["all_passed"] = all(protocol_gates.values())
    max_clean = max(
        (
            float(payload["oracle_minus_best_floor"]["value"])
            for variant in clean_readouts_by_variant.values()
            for payload in variant.values()
            if payload["oracle_minus_best_floor"]["value"] is not None
        ),
        default=float("nan"),
    )
    verdict = "e2prime_flip_confirmed" if flip_confirmed else "e2prime_flip_not_confirmed"
    return {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": mode,
        "created_at_utc": utc_timestamp(),
        "elapsed_s": round(float(elapsed_s), 1),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "rows_csv": str(rows_csv.relative_to(REPO_ROOT)),
        "metrics_csv": str(metrics_csv.relative_to(REPO_ROOT)),
        "selection_row_count": len(selection_rows),
        "selection_row_count_expected": selection_expected,
        "validation_row_count": len(validation_rows),
        "validation_row_count_expected": validation_expected,
        "validation_seed_count_per_cell": min_validation_seed_count,
        "vehicle_variant_count": len(prereg["chrono_variants"]),
        "non_sedan_variants": non_sedan_variants,
        "calibration": calibration,
        "selections": selections,
        "protocol_gates": protocol_gates,
        "clean_readouts_pooled": clean_readouts,
        "clean_readouts_by_variant": clean_readouts_by_variant,
        "degraded_spot_readouts": degraded_readouts,
        "decision": {
            "e2prime_full_verdict": verdict,
            "flip_confirmed": flip_confirmed,
            "variants_confirming_flip": variants_confirming_flip,
            "qualifying_clean_reveals_by_variant_m": qualifying_by_variant,
            "legacy_effect_qualifying_reveals_by_variant_m": legacy_effect_qualifying_by_variant,
            "tight_positive_cell_count": tight_positive_cell_count,
            "max_clean_oracle_minus_floor": round(float(max_clean), 4) if math.isfinite(max_clean) else None,
            "positive_rule": prereg["preregistered_readouts"]["positive_rule"],
            "track_f_admitted": False,
            "next_admitted_step": (
                "If full E2' confirms the flip, route only to the later Track-F GPU-days checkpoint; "
                "Track F remains blocked here."
            ),
        },
    }


def write_metrics(summary: dict[str, Any], path: Path) -> None:
    rows = [
        {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
        {"metric": "flip_confirmed", "value": 1.0 if summary["decision"]["flip_confirmed"] else 0.0},
        {"metric": "flip_confirming_variant_count", "value": float(len(summary["decision"]["variants_confirming_flip"]))},
        {"metric": "tight_positive_cell_count", "value": float(summary["decision"]["tight_positive_cell_count"])},
        {"metric": "max_clean_oracle_minus_floor", "value": summary["decision"]["max_clean_oracle_minus_floor"]},
        {"metric": "validation_seed_count_per_cell", "value": float(summary["validation_seed_count_per_cell"])},
        {"metric": "vehicle_variant_count", "value": float(summary["vehicle_variant_count"])},
        {"metric": "track_f_admitted", "value": 1.0 if summary["decision"]["track_f_admitted"] else 0.0},
        {"metric": "selection_row_count", "value": float(summary["selection_row_count"])},
        {"metric": "selection_row_count_expected", "value": float(summary["selection_row_count_expected"])},
        {"metric": "validation_row_count", "value": float(summary["validation_row_count"])},
        {"metric": "validation_row_count_expected", "value": float(summary["validation_row_count_expected"])},
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary: dict[str, Any]) -> None:
    lines = [
        "# M3258 Phase-4 E2' Chrono Two-Regime Hardening",
        "",
        "Status: completed. This is the frozen full E2' Chrono hardening verdict; it is zero-training pricing and does not admit Track F.",
        "",
        "## Verdict",
        "",
        f"- E2' full verdict: **{summary['decision']['e2prime_full_verdict']}**.",
        f"- Flip confirmed: **{str(summary['decision']['flip_confirmed']).lower()}**.",
        f"- Variants confirming flip: {summary['decision']['variants_confirming_flip']}.",
        f"- Qualifying clean reveals by variant: {summary['decision']['qualifying_clean_reveals_by_variant_m']}.",
        f"- Protocol gates passed: **{str(summary['protocol_gates']['all_passed']).lower()}**.",
        "",
        "## Measured",
        "",
        f"- Vehicle variants: {summary['vehicle_variant_count']} (`{', '.join(summary['clean_readouts_by_variant'].keys())}`).",
        f"- Validation seeds per cell: {summary['validation_seed_count_per_cell']}.",
        f"- Selection rows: {summary['selection_row_count']} / expected {summary['selection_row_count_expected']}.",
        f"- Validation rows: {summary['validation_row_count']} / expected {summary['validation_row_count_expected']}.",
        f"- Rows CSV: `{summary['rows_csv']}`.",
        "",
        "| variant | clean reveal m | oracle - floor | CI95 | n | flip cell | oracle - seeker | seeker - fixed |",
        "|---|---:|---:|---|---:|---|---:|---:|",
    ]
    for variant, by_reveal in summary["clean_readouts_by_variant"].items():
        for reveal, payload in by_reveal.items():
            primary = payload["oracle_minus_best_floor"]
            secondary = payload["oracle_minus_best_seeker"]
            detect = payload["best_seeker_minus_best_fixed"]
            lines.append(
                f"| {variant} | {reveal} | {primary['value']} | {primary['paired_bootstrap_ci95']} | {primary['n_pairs']} | "
                f"{payload['qualifies_ci_lower_positive']} | {secondary['value']} | {detect['value']} |"
            )
    lines += [
        "",
        "Secondary degraded spot:",
        "",
        "| variant | cell | reveal m | oracle - floor | CI95 | n |",
        "|---|---|---:|---:|---|---:|",
    ]
    for cell_id, cell in summary["degraded_spot_readouts"].items():
        for variant, by_reveal in cell["by_variant"].items():
            for reveal, payload in by_reveal.items():
                primary = payload["oracle_minus_best_floor"]
                lines.append(
                    f"| {variant} | {cell_id} | {reveal} | {primary['value']} | {primary['paired_bootstrap_ci95']} | {primary['n_pairs']} |"
                )
    lines += [
        "",
        "## Inferred",
        "",
        "The verdict is scoped to the frozen Sedan/TMeasy and UAZBUS/TMeasy fixtures and this scripted controller grid. It does not cover BMW_E90 E2, independent payload-position/h_cg, tire-family, split-mu, or learned-policy performance.",
        "",
        "Track F remains blocked here; a confirmed flip only routes to a later GPU-days checkpoint.",
        "",
        "## Claim Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Artifacts",
        "",
        f"- Preregistration: `{summary['preregistration']}`",
        f"- Full JSON: `{str(RESULTS_JSON.relative_to(REPO_ROOT))}`",
        f"- Episode rows: `{summary['rows_csv']}`",
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
    parser.add_argument("--workers", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.write_prereg:
        payload = write_preregistration()
        print(
            json.dumps(
                {
                    "preregistration": str(PREREG_JSON),
                    "selection_rows": len(_selection_units(payload)),
                    "clean_reveals": list(CLEAN_REVEALS),
                    "variants": list(FULL_VARIANTS),
                },
                sort_keys=True,
            )
        )
    if args.quick:
        summary = run_quick(resume=args.resume)
        print(json.dumps(summary["decision"], sort_keys=True))
    if args.full:
        summary = run_full(resume=args.resume, workers=args.workers)
        print(json.dumps(summary["decision"], sort_keys=True))
    if not args.write_prereg and not args.quick and not args.full:
        raise SystemExit("nothing to do; pass --write-prereg, --quick, and/or --full")


if __name__ == "__main__":
    main()
