"""Phase-4 E2 full Chrono two-regime-law pricing.

M3252 is the full E2 verdict milestone after the M3251 protocol smoke. It
measures whether clean-sensing VoI(belief) remains near zero on the default
Chrono Sedan/TMeasy fixture when the current-sim threshold-seeker and shortfall
detector are run through the Chrono worker interface. It also reports one
delay25 tight degraded spot as a secondary readout.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e2_chrono_two_regime_full.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e2_chrono_two_regime_full.py --full --resume
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
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
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_e2_chrono_two_regime_smoke as e2_smoke  # noqa: E402


MILESTONE_ID = "m3252-phase4-e2-chrono-two-regime-full"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2_chrono_two_regime_full_prereg.json"
RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2_chrono_two_regime_full.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e2_chrono_two_regime"
ROWS_FULL_CSV = RUN_DIR / "episode_rows_full.csv"
METRICS_FULL_CSV = RUN_DIR / "metrics_full.csv"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
DOC_PATH = REPO_ROOT / "docs" / "m3252-phase4-e2-chrono-two-regime-full.md"

TASK_B_SCRIPT = e2_smoke.TASK_B_SCRIPT
COND_SCRIPT = e2_smoke.COND_SCRIPT
REGIME_SCRIPT = e2_smoke.REGIME_SCRIPT
E0_JSON = e2_smoke.E0_JSON
E1_FULL_JSON = e2_smoke.E1_FULL_JSON
E2_QUICK_JSON = e2_smoke.QUICK_JSON

SEED_BASE = 2026061304
FULL_VARIANTS = ("sedan_tmeasy",)
CLEAN_REVEALS = (9.5, 12.0, 16.0, 22.0, 30.0)
MU_POINTS = (0.3625, 0.5875, 0.8125, 1.0375)
SEL_SEEDS = (0,)
VAL_SEEDS = (0, 1)
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
    "Phase-4 E2 full Chrono two-regime-law pricing only: scripted oracle, "
    "threshold-seeker, and fixed belief-free controller families are compared "
    "on the default Chrono Sedan/TMeasy fixture over frozen clean reveal tiers "
    "plus one delay25 tight degraded spot. This is zero-training pricing "
    "evidence; it makes no incumbent mutation, validation ranking, promotion, "
    "driver-performance, full high-fidelity sufficiency, paper, repair-success, "
    "robustness-result, feasibility-proof, or self-ID claim."
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
    quick = _read_json(E2_QUICK_JSON)
    if quick.get("decision", {}).get("e2_quick_verdict") != "protocol_smoke_passed":
        raise RuntimeError("E2 quick protocol smoke did not pass")
    allowed = tuple(e0["e1_spread_envelope"]["recommended_e1_population_panel"]["vehicle_variants"])
    for variant in FULL_VARIANTS:
        if variant not in allowed:
            raise RuntimeError(f"full variant {variant!r} is outside the E0-admitted envelope")
    return {
        "protocol": "phase4_e2_chrono_two_regime_full_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 E2 Chrono two-regime law full",
        "frozen_at_utc": e2_smoke.utc_timestamp(),
        "frozen_before_any_e2_full_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "e0_artifact": str(E0_JSON.relative_to(REPO_ROOT)),
        "e0_axis_table_sha256": e0["axis_table_sha256"],
        "e1_full_artifact": str(E1_FULL_JSON.relative_to(REPO_ROOT)),
        "e1_full_verdict": e1["decision"]["e1_full_verdict"],
        "e2_quick_artifact": str(E2_QUICK_JSON.relative_to(REPO_ROOT)),
        "chrono_variants": list(FULL_VARIANTS),
        "clean_reveal_tiers_m": list(CLEAN_REVEALS),
        "mu_points": list(MU_POINTS),
        "selection_seeds": list(SEL_SEEDS),
        "validation_seeds": list(VAL_SEEDS),
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
            "variant_scope": "per full Chrono vehicle variant",
            "tau_rule": "tau = max(1.2 * max_shortfall_on_sublimit_fixed_ramp, 0.08)",
        },
        "runtime_gates": [
            "E2 quick artifact exists and passed before full E2",
            "selection and validation seed streams are disjoint",
            "clean selection rows cover every candidate/reveal/mu/selection seed",
            "clean validation rows cover oracle, best_seeker, best_fixed, and best_floor logical arms",
            "delay25_tight degraded spot rows are written as secondary non-gating readouts",
            "reset obs are finite obs72 and backend_info variant ids match",
            "paired CIs are reported for oracle minus best_floor on every clean reveal tier",
            "Track F remains blocked regardless of M3252 verdict",
        ],
        "preregistered_readouts": {
            "primary_clean_per_reveal": "success_rate(oracle) - success_rate(best_floor), paired on validation mu x seed units",
            "secondary_clean_oracle_minus_seeker": "success_rate(oracle) - success_rate(best_seeker), paired on validation units",
            "detection_value_clean": "success_rate(best_seeker) - success_rate(best_fixed), paired on validation units",
            "degraded_spot_secondary": "same readouts on delay25_tight using the clean-selected arms",
            "positive_rule": (
                "Chrono clean belief value is positive iff at least one clean reveal tier has "
                "oracle - best_floor >= 0.15 and paired CI95 lower > 0. Otherwise the clean "
                "two-regime null is not rejected by this frozen panel."
            ),
        },
        "decision_rule": (
            "M3252 is completed when the full panel runs under this preregistration, writes "
            "full JSON/CSV/doc artifacts, reports paired CIs, and applies the clean positive rule. "
            "The delay25 spot is secondary and cannot open Track F by itself."
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
    if not payload.get("frozen_before_any_e2_full_rollout"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_e2_full_rollout")
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


def _progress(payload: dict[str, Any]) -> None:
    PROGRESS_FULL_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_FULL_JSONL.open("a", encoding="utf-8") as handle:
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
) -> int:
    completed = 0
    for unit in units:
        cell = unit["cell"]
        candidate = unit["candidate"]
        key = (
            unit["phase"],
            unit["variant"],
            cell["cell_id"],
            str(unit["reveal"]),
            str(unit["mu"]),
            str(unit["seed"]),
            unit["logical_arm"],
            candidate["name"],
        )
        if key in done:
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
            ROWS_FULL_CSV,
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


def run_full(*, resume: bool) -> dict[str, Any]:
    prereg = load_preregistration()
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
    calibration: dict[str, dict[str, Any]] = {}
    client = ChronoWorkerClient(stderr_log=STDERR_LOG)
    try:
        for variant in prereg["chrono_variants"]:
            calibration[variant] = e2_smoke.calibrate_tau_for_variant(client, reg, mod_b, interp, variant=variant)
            _progress({"stage": "calibration_done", "variant": variant, **calibration[variant]})
        selection_units = _selection_units(prereg)
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
        )
        rows = _read_csv_rows(ROWS_FULL_CSV)
        selections = select_arms(rows, prereg)
        validation_units = _validation_units(prereg, selections)
        done = _done_keys(ROWS_FULL_CSV)
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
        )
    finally:
        client.close()
    rows = _read_csv_rows(ROWS_FULL_CSV)
    selections = select_arms(rows, prereg)
    summary = summarize_full(rows, prereg, selections=selections, calibration=calibration, elapsed_s=time.time() - started)
    write_json(RESULTS_JSON, summary)
    write_metrics(summary)
    write_markdown(summary)
    return summary


def _paired_values(rows: list[dict[str, str]], *, cell_id: str, reveal: float, left: str, right: str) -> list[float]:
    keyed: dict[tuple[str, str, str, str], dict[str, float]] = {}
    for row in rows:
        if row["phase"] != "validation" or row["cell_id"] != cell_id or float(row["reveal_m"]) != float(reveal):
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


def _paired_readout(rows: list[dict[str, str]], *, cell_id: str, reveal: float, left: str, right: str) -> dict[str, Any]:
    vals = _paired_values(rows, cell_id=cell_id, reveal=reveal, left=left, right=right)
    if not vals:
        return {"value": None, "paired_bootstrap_ci95": [None, None], "n_pairs": 0}
    arr = np.asarray(vals, dtype=np.float64)
    rng = np.random.default_rng(_seed_for("bootstrap", cell_id, reveal, left, right))
    boots = [float(np.mean(arr[rng.integers(0, len(arr), size=len(arr))])) for _ in range(BOOTSTRAP_SAMPLES)]
    return {
        "value": round(float(np.mean(arr)), 4),
        "paired_bootstrap_ci95": [round(float(np.quantile(boots, 0.025)), 4), round(float(np.quantile(boots, 0.975)), 4)],
        "n_pairs": int(len(arr)),
        "raw_differences": [round(float(v), 4) for v in vals],
    }


def summarize_full(
    rows: list[dict[str, str]],
    prereg: dict[str, Any],
    *,
    selections: dict[str, Any],
    calibration: dict[str, dict[str, Any]],
    elapsed_s: float,
) -> dict[str, Any]:
    selection_expected = len(_selection_units(prereg))
    validation_expected = len(_validation_units(prereg, selections))
    selection_rows = [row for row in rows if row["phase"] == "selection"]
    validation_rows = [row for row in rows if row["phase"] == "validation"]
    reset_obs_finite_all = all(row["reset_obs_finite"] == "True" for row in rows)
    variant_match_all = all(row["variant_match"] == "True" for row in rows)
    clean_readouts: dict[str, Any] = {}
    qualifying = []
    for reveal in prereg["clean_reveal_tiers_m"]:
        primary = _paired_readout(rows, cell_id="clean", reveal=float(reveal), left="oracle", right="best_floor")
        oracle_minus_seeker = _paired_readout(rows, cell_id="clean", reveal=float(reveal), left="oracle", right="best_seeker")
        seeker_minus_fixed = _paired_readout(rows, cell_id="clean", reveal=float(reveal), left="best_seeker", right="best_fixed")
        qualifies = (
            primary["value"] is not None
            and float(primary["value"]) >= POSITIVE_EFFECT_THRESHOLD
            and primary["paired_bootstrap_ci95"][0] is not None
            and float(primary["paired_bootstrap_ci95"][0]) > 0.0
        )
        if qualifies:
            qualifying.append(float(reveal))
        clean_readouts[f"{float(reveal):g}"] = {
            "oracle_minus_best_floor": primary,
            "oracle_minus_best_seeker": oracle_minus_seeker,
            "best_seeker_minus_best_fixed": seeker_minus_fixed,
            "qualifies_clean_positive": qualifies,
        }
    degraded_readouts: dict[str, Any] = {}
    for cell in prereg["degraded_spots"]:
        by_reveal = {}
        for reveal in cell["reveals"]:
            by_reveal[f"{float(reveal):g}"] = {
                "oracle_minus_best_floor": _paired_readout(rows, cell_id=cell["cell_id"], reveal=float(reveal), left="oracle", right="best_floor"),
                "oracle_minus_best_seeker": _paired_readout(rows, cell_id=cell["cell_id"], reveal=float(reveal), left="oracle", right="best_seeker"),
                "best_seeker_minus_best_fixed": _paired_readout(rows, cell_id=cell["cell_id"], reveal=float(reveal), left="best_seeker", right="best_fixed"),
            }
        degraded_readouts[cell["cell_id"]] = {"delay_steps": cell["delay_steps"], "noise_std": cell["noise_std"], "by_reveal": by_reveal}
    protocol_gates = {
        "selection_rows_complete": len(selection_rows) == selection_expected,
        "validation_rows_complete": len(validation_rows) == validation_expected,
        "reset_obs_finite_all": reset_obs_finite_all,
        "variant_match_all": variant_match_all,
        "calibration_written": set(calibration) == set(prereg["chrono_variants"]),
        "paired_clean_readouts_present": all(clean_readouts[f"{float(r):g}"]["oracle_minus_best_floor"]["n_pairs"] > 0 for r in prereg["clean_reveal_tiers_m"]),
        "track_f_not_admitted": True,
    }
    protocol_gates["all_passed"] = all(protocol_gates.values())
    max_clean = max((float(v["oracle_minus_best_floor"]["value"]) for v in clean_readouts.values() if v["oracle_minus_best_floor"]["value"] is not None), default=float("nan"))
    verdict = "chrono_clean_belief_value_positive" if qualifying else "chrono_clean_threshold_seeker_null_not_rejected"
    return {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": "full",
        "created_at_utc": utc_timestamp(),
        "elapsed_s": round(float(elapsed_s), 1),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "rows_csv": str(ROWS_FULL_CSV.relative_to(REPO_ROOT)),
        "metrics_csv": str(METRICS_FULL_CSV.relative_to(REPO_ROOT)),
        "selection_row_count": len(selection_rows),
        "selection_row_count_expected": selection_expected,
        "validation_row_count": len(validation_rows),
        "validation_row_count_expected": validation_expected,
        "calibration": calibration,
        "selections": selections,
        "protocol_gates": protocol_gates,
        "clean_readouts": clean_readouts,
        "degraded_spot_readouts": degraded_readouts,
        "decision": {
            "e2_full_verdict": verdict,
            "qualifying_clean_reveals_m": qualifying,
            "max_clean_oracle_minus_floor": round(float(max_clean), 4) if math.isfinite(max_clean) else None,
            "positive_rule": prereg["preregistered_readouts"]["positive_rule"],
            "track_f_admitted": False,
            "next_admitted_step": "E3 remains open; Track F remains blocked on Track E plus CP-3.",
        },
    }


def write_metrics(summary: dict[str, Any]) -> None:
    rows = [
        {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
        {"metric": "clean_positive_reveal_count", "value": float(len(summary["decision"]["qualifying_clean_reveals_m"]))},
        {"metric": "max_clean_oracle_minus_floor", "value": summary["decision"]["max_clean_oracle_minus_floor"]},
        {"metric": "selection_row_count", "value": float(summary["selection_row_count"])},
        {"metric": "selection_row_count_expected", "value": float(summary["selection_row_count_expected"])},
        {"metric": "validation_row_count", "value": float(summary["validation_row_count"])},
        {"metric": "validation_row_count_expected", "value": float(summary["validation_row_count_expected"])},
    ]
    METRICS_FULL_CSV.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_FULL_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary: dict[str, Any]) -> None:
    lines = [
        "# M3252 Phase-4 E2 Chrono Two-Regime Full",
        "",
        "Status: completed. This is the frozen full E2 Chrono Sedan/TMeasy verdict; it is zero-training pricing and does not admit Track F.",
        "",
        "## Verdict",
        "",
        f"- E2 full verdict: **{summary['decision']['e2_full_verdict']}**.",
        f"- Qualifying clean reveals: {summary['decision']['qualifying_clean_reveals_m']}.",
        f"- Protocol gates passed: **{str(summary['protocol_gates']['all_passed']).lower()}**.",
        "",
        "## Measured",
        "",
        f"- Selection rows: {summary['selection_row_count']} / expected {summary['selection_row_count_expected']}.",
        f"- Validation rows: {summary['validation_row_count']} / expected {summary['validation_row_count_expected']}.",
        f"- Rows CSV: `{summary['rows_csv']}`.",
        "",
        "| clean reveal m | oracle - floor | CI95 | n | qualifies | oracle - seeker | seeker - fixed |",
        "|---:|---:|---|---:|---|---:|---:|",
    ]
    for reveal, payload in summary["clean_readouts"].items():
        primary = payload["oracle_minus_best_floor"]
        secondary = payload["oracle_minus_best_seeker"]
        detect = payload["best_seeker_minus_best_fixed"]
        lines.append(
            f"| {reveal} | {primary['value']} | {primary['paired_bootstrap_ci95']} | {primary['n_pairs']} | "
            f"{payload['qualifies_clean_positive']} | {secondary['value']} | {detect['value']} |"
        )
    lines += [
        "",
        "Secondary degraded spot:",
        "",
        "| cell | reveal m | oracle - floor | CI95 | n |",
        "|---|---:|---:|---|---:|",
    ]
    for cell_id, cell in summary["degraded_spot_readouts"].items():
        for reveal, payload in cell["by_reveal"].items():
            primary = payload["oracle_minus_best_floor"]
            lines.append(f"| {cell_id} | {reveal} | {primary['value']} | {primary['paired_bootstrap_ci95']} | {primary['n_pairs']} |")
    lines += [
        "",
        "## Inferred",
        "",
        "The verdict is scoped to the frozen default Chrono Sedan/TMeasy fixture and this controller grid. It does not cover BMW_E90/UAZBUS E2, independent payload-position/h_cg, tire-family, split-mu, or learned-policy performance.",
        "",
        "Track F remains blocked until E3 completes and CP-3 confirms targets and budget.",
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
                    "selection_rows": len(_selection_units(payload)),
                    "clean_reveals": list(CLEAN_REVEALS),
                },
                sort_keys=True,
            )
        )
    if args.full:
        summary = run_full(resume=args.resume)
        print(json.dumps(summary["decision"], sort_keys=True))
    if not args.write_prereg and not args.full:
        raise SystemExit("nothing to do; pass --write-prereg and/or --full")


if __name__ == "__main__":
    main()
