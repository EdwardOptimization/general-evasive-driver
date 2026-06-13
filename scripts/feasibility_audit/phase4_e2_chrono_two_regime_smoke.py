"""Phase-4 E2 Chrono two-regime-law protocol smoke.

M3251 is the first E2 milestone after E1 closed negative. It ports the
current-sim threshold-seeker / shortfall-detector controller family from
``ramp_policy_voi_regime.py`` onto the Chrono worker interface and exercises a
tiny clean + degraded spot panel. Quick mode is protocol evidence only; it is
not the Chrono two-regime-law verdict.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e2_chrono_two_regime_smoke.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_e2_chrono_two_regime_smoke.py --quick --resume
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
from autodrift.config import build_env_config  # noqa: E402
from autodrift.env import AutoDriftEnv  # noqa: E402
from autodrift.chrono_vehicle_backend import scenario_from_env  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_e1_spread_revival_pricing as e1_smoke  # noqa: E402


MILESTONE_ID = "m3251-phase4-e2-chrono-two-regime-smoke"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2_chrono_two_regime_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2_chrono_two_regime_quick.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e2_chrono_two_regime"
ROWS_QUICK_CSV = RUN_DIR / "episode_rows_quick.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
DOC_PATH = REPO_ROOT / "docs" / "m3251-phase4-e2-chrono-two-regime-smoke.md"

TASK_B_SCRIPT = REPO_ROOT / "scripts" / "feasibility_audit" / "voi_commitment_task_design.py"
COND_SCRIPT = REPO_ROOT / "scripts" / "feasibility_audit" / "voi_conditional_prior.py"
REGIME_SCRIPT = REPO_ROOT / "scripts" / "feasibility_audit" / "ramp_policy_voi_regime.py"

E0_JSON = e1_smoke.E0_JSON
E1_FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1_spread_revival_full.json"

SEED_BASE = 2026061303
QUICK_VARIANTS = ("sedan_tmeasy",)
QUICK_REVEALS = (9.5, 30.0)
QUICK_MUS = (0.3625, 0.8125)
QUICK_CLEAN_CELLS = (
    {"cell_id": "clean", "delay_steps": 0, "noise_std": 0.0, "reveals": QUICK_REVEALS},
)
QUICK_DEGRADED_SPOTS = (
    {"cell_id": "delay25_tight", "delay_steps": 25, "noise_std": 0.0, "reveals": (9.5,)},
)
QUICK_ARMS = ("oracle_ramp", "threshold_seeker", "fixed_ramp")
CALIBRATION_MU = 0.8125
CALIBRATION_REVEAL = 30.0
CALIBRATION_STEPS = 90

CLAIM_BOUNDARY = (
    "Phase-4 E2 Chrono two-regime-law protocol smoke only: the current-sim "
    "threshold-seeker / shortfall-detector controller family is ported to the "
    "Chrono worker interface and exercised on a tiny clean plus degraded spot "
    "panel. Quick mode is not a clean VoI(belief) or degraded revival verdict; "
    "it makes no training, validation ranking, promotion, driver-performance, "
    "full high-fidelity sufficiency, paper, repair-success, robustness-result, "
    "feasibility-proof, or self-ID claim."
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


def load_e0_envelope() -> dict[str, Any]:
    if not E0_JSON.exists():
        raise FileNotFoundError(f"missing E0 artifact {E0_JSON}")
    e0 = _read_json(E0_JSON)
    if not e0.get("decision", {}).get("e1_preregistration_admitted"):
        raise RuntimeError("E0 did not admit the Phase-4 Chrono vehicle fixture envelope")
    return e0


def load_e1_full_decision() -> dict[str, Any]:
    if not E1_FULL_JSON.exists():
        raise FileNotFoundError(f"missing E1 full artifact {E1_FULL_JSON}")
    e1 = _read_json(E1_FULL_JSON)
    if e1.get("decision", {}).get("track_f_admitted") is not False:
        raise RuntimeError("E1 artifact does not keep Track F blocked")
    return e1


def build_preregistration() -> dict[str, Any]:
    e0 = load_e0_envelope()
    e1 = load_e1_full_decision()
    allowed = tuple(e0["e1_spread_envelope"]["recommended_e1_population_panel"]["vehicle_variants"])
    for variant in QUICK_VARIANTS:
        if variant not in allowed:
            raise RuntimeError(f"quick variant {variant!r} is outside the E0-admitted envelope")
    cells = list(QUICK_CLEAN_CELLS) + list(QUICK_DEGRADED_SPOTS)
    return {
        "protocol": "phase4_e2_chrono_two_regime_smoke_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 E2 Chrono two-regime law protocol smoke",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_e2_chrono_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "e0_artifact": str(E0_JSON.relative_to(REPO_ROOT)),
        "e0_axis_table_sha256": e0["axis_table_sha256"],
        "e1_full_artifact": str(E1_FULL_JSON.relative_to(REPO_ROOT)),
        "e1_full_verdict": e1["decision"]["e1_full_verdict"],
        "quick_mode_is_verdict": False,
        "quick_variants": list(QUICK_VARIANTS),
        "quick_reveals": list(QUICK_REVEALS),
        "quick_mu_points": list(QUICK_MUS),
        "quick_cells": cells,
        "quick_arms": list(QUICK_ARMS),
        "calibration": {
            "variant_scope": "per quick Chrono vehicle variant",
            "mu": CALIBRATION_MU,
            "reveal_m": CALIBRATION_REVEAL,
            "steps": CALIBRATION_STEPS,
            "tau_rule": "tau = max(1.2 * max_shortfall_on_sublimit_fixed_ramp, 0.08)",
        },
        "degradation_filter": {
            "channels": "ego channels 0-8 only",
            "geometry_channels": "unchanged",
            "command_history_channels": "unchanged",
            "spot_cell": "delay25_tight applies 25-step delay to the policy observation only",
        },
        "runtime_gates": [
            "E0 artifact admits the Chrono vehicle fixture envelope",
            "E1 full artifact exists and keeps Track F blocked",
            "the quick panel writes oracle_ramp, threshold_seeker, and fixed_ramp rows",
            "clean rows cover both quick reveal tiers",
            "the degraded spot writes delay25_tight rows at reveal 9.5 m",
            "reset obs are finite obs72 and backend_info variant ids match",
            "the artifact labels quick mode as non-verdict",
        ],
        "full_e2_placeholder": {
            "status": "not_registered_by_M3251",
            "needed_next": (
                "A separate full E2 milestone must freeze Chrono variants, clean reveal tiers, "
                "mu points, selection/validation seeds, degraded spot cells, paired CIs, and "
                "pass/negative thresholds before any two-regime-law verdict."
            ),
        },
        "decision_rule": (
            "M3251 PASS iff the preregistered quick Chrono panel runs, all protocol gates pass, "
            "and the JSON/doc explicitly refuse a two-regime-law verdict. M3251 never opens Track F."
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
    if not payload.get("frozen_before_any_e2_chrono_rollout"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_e2_chrono_rollout")
    return payload


class EgoDegradationFilter:
    """Apply E2 degraded-sensing cells to policy observations.

    The Chrono backend always receives the true action and returns true obs72.
    Only the controller's input observation is degraded; ego channels 0-8 can
    be delayed/noised, while geometry and command-history channels remain exact.
    """

    def __init__(self, *, delay_steps: int, noise_std: float, seed: int):
        self.delay_steps = int(delay_steps)
        self.noise_std = float(noise_std)
        self.rng = np.random.default_rng(int(seed))
        self.buffer: list[np.ndarray] = []

    def reset(self, obs: np.ndarray) -> np.ndarray:
        self.buffer = []
        return self.step(obs)

    def step(self, obs: np.ndarray) -> np.ndarray:
        raw = np.asarray(obs, dtype=np.float32).copy()
        self.buffer.append(raw.copy())
        source = self.buffer[0] if len(self.buffer) <= self.delay_steps else self.buffer[-self.delay_steps - 1]
        out = raw.copy()
        out[:9] = source[:9]
        if self.noise_std > 0.0:
            out[:9] += self.rng.normal(0.0, self.noise_std, size=9).astype(np.float32)
        return out


def _outcome_from_info(info: dict[str, Any]) -> str:
    collision = bool(info.get("collision", False))
    completed = bool(info.get("obstacle_completed", False))
    reason = str(info.get("termination_reason", "") or "")
    if completed and not collision:
        return "success"
    if collision or reason == "obstacle_collision":
        return "collision"
    if reason == "off_track":
        return "offtrack"
    if reason == "speed_too_low":
        return "speed_too_low"
    if reason == "speed_too_high":
        return "speed_too_high"
    if reason == "yaw_rate_limit":
        return "yaw_rate_limit"
    return "timeout_other"


def _finite_obs(obs: np.ndarray) -> bool:
    return bool(obs.shape == (72,) and np.isfinite(obs).all())


def _seed_for(*parts: Any) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little") % 2_000_000_000


def _make_scenario(reg, mod_b, interp, *, reveal: float, mu: float, seed: int, variant: str) -> dict[str, Any]:
    design = reg.make_design(mod_b, float(reveal))
    distance = reg.jittered_distance(interp, float(mu), int(seed))
    level = mod_b.LevelSpec(mu=float(mu), d_lo=distance, d_hi=distance, entry_speed=reg.v_star(interp, float(mu)))
    env = AutoDriftEnv(build_env_config(mod_b.level_env_config(design, level)))
    try:
        env.reset(seed=int(seed))
        scenario = scenario_from_env(env)
    finally:
        env.close()
    scenario["scenario_id"] = f"e2-{variant}-r{reveal:g}-mu{mu:.4f}-seed{seed}"
    scenario["chrono_vehicle_variant"] = variant
    scenario["e2_source"] = {
        "reveal_m": float(reveal),
        "mu": float(mu),
        "seed": int(seed),
        "distance_m": round(float(distance), 4),
    }
    return scenario


def _disable_obstacle(scenario: dict[str, Any], *, max_steps: int) -> dict[str, Any]:
    clone = json.loads(json.dumps(_jsonable(scenario)))
    clone["scenario_id"] = f"{scenario['scenario_id']}-cal"
    clone["max_steps"] = int(max_steps)
    clone["obstacle"] = {"enabled": False}
    return clone


def _controller_builder(reg, mod_b, interp, *, reveal: float, arm: str, mu: float, tau: float) -> Callable[[], Any]:
    design = reg.make_design(mod_b, float(reveal))
    if arm == "oracle_ramp":
        return lambda: reg.RampPolicyController(
            mod_b,
            interp,
            design,
            "chrono_oracle_dv0",
            mode="oracle",
            mu_true=float(mu),
            dv=0.0,
        )
    if arm == "threshold_seeker":
        return lambda: reg.RampPolicyController(
            mod_b,
            interp,
            design,
            f"chrono_seeker_tau{tau:.3f}",
            mode="seeker",
            ramp_rate=6000.0,
            tau=float(tau),
            backoff=0.06,
            strategy="hold",
            dv=0.0,
        )
    if arm == "fixed_ramp":
        return lambda: reg.RampPolicyController(
            mod_b,
            interp,
            design,
            "chrono_fixedramp_f0.35_h1",
            mode="fixed_ramp",
            fixed_frac=0.35,
            fixed_hold_s=1.0,
        )
    raise ValueError(f"unknown E2 arm {arm!r}")


def run_controller_episode(
    client: ChronoWorkerClient,
    scenario: dict[str, Any],
    controller: Any,
    *,
    variant: str,
    delay_steps: int,
    noise_std: float,
    seed: int,
) -> dict[str, Any]:
    if hasattr(controller, "reset"):
        controller.reset()
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
    backend_info = dict(reset_reply.get("backend_info", {}))
    reset_obs_finite = _finite_obs(obs)
    variant_match = backend_info.get("chrono_vehicle_variant") == variant
    obs_filter = EgoDegradationFilter(delay_steps=delay_steps, noise_std=noise_std, seed=seed + 991)
    policy_obs = obs_filter.reset(obs)
    true_signature = float(np.sum(obs, dtype=np.float64))
    policy_signature = float(np.sum(policy_obs, dtype=np.float64))
    terminated = truncated = False
    info: dict[str, Any] = dict(reset_reply.get("info", {}))
    status = "reset"
    steps = 0
    visible_step: int | None = 0 if float(obs[44]) > 0.5 else None
    max_steps = int(scenario["max_steps"]) + 5
    while not (terminated or truncated) and steps < max_steps:
        action = np.asarray(controller.act(policy_obs), dtype=np.float32)
        obs, terminated, truncated, status, info = client.step(action)
        if not _finite_obs(obs):
            break
        policy_obs = obs_filter.step(obs)
        true_signature += float(np.sum(obs, dtype=np.float64))
        policy_signature += float(np.sum(policy_obs, dtype=np.float64))
        if visible_step is None and float(obs[44]) > 0.5:
            visible_step = steps + 1
        steps += 1
    telemetry = {}
    if hasattr(controller, "telemetry_row"):
        telemetry = dict(controller.telemetry_row())
    margin = info.get("min_clearance_margin")
    return {
        "outcome": _outcome_from_info(info),
        "success": _outcome_from_info(info) == "success",
        "steps": int(steps),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "backend_status": status,
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "completion_reason": str(info.get("completion_reason", "") or ""),
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "obstacle_visible_step": visible_step,
        "min_clearance_margin": float(margin) if isinstance(margin, (int, float)) else float("nan"),
        "reset_obs_finite": reset_obs_finite,
        "variant_match": variant_match,
        "true_trace_signature": repr(true_signature),
        "policy_trace_signature": repr(policy_signature),
        "backend_info": {
            key: backend_info.get(key)
            for key in (
                "backend_id",
                "chrono_vehicle_variant",
                "chrono_vehicle_model",
                "chrono_tire_model",
                "vehicle_total_mass",
                "target_mass",
            )
        },
        "telemetry": telemetry,
    }


def calibrate_tau_for_variant(client: ChronoWorkerClient, reg, mod_b, interp, *, variant: str) -> dict[str, Any]:
    seed = _seed_for("calibration", variant)
    scenario = _make_scenario(reg, mod_b, interp, reveal=CALIBRATION_REVEAL, mu=CALIBRATION_MU, seed=seed, variant=variant)
    scenario = _disable_obstacle(scenario, max_steps=CALIBRATION_STEPS)
    controller = reg.RampPolicyController(
        mod_b,
        interp,
        reg.make_design(mod_b, CALIBRATION_REVEAL),
        "chrono_calibration_fixedramp",
        mode="fixed_ramp",
        tau=1e9,
        fixed_frac=0.25,
        fixed_hold_s=1.0,
    )
    result = run_controller_episode(
        client,
        scenario,
        controller,
        variant=variant,
        delay_steps=0,
        noise_std=0.0,
        seed=seed,
    )
    max_shortfall = float(result.get("telemetry", {}).get("max_shortfall", 0.0))
    tau = max(1.2 * max_shortfall, 0.08)
    return {
        "variant": variant,
        "seed": seed,
        "mu": CALIBRATION_MU,
        "reveal_m": CALIBRATION_REVEAL,
        "max_shortfall": round(max_shortfall, 6),
        "tau": round(float(tau), 6),
        "outcome": result["outcome"],
        "reset_obs_finite": result["reset_obs_finite"],
        "variant_match": result["variant_match"],
    }


FIELDNAMES = [
    "role",
    "variant",
    "cell_id",
    "delay_steps",
    "noise_std",
    "reveal_m",
    "mu",
    "seed",
    "arm",
    "outcome",
    "success",
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


def _done_keys(path: Path) -> set[tuple[str, str, str, str, str, str]]:
    keys: set[tuple[str, str, str, str, str, str]] = set()
    for row in _read_csv_rows(path):
        if row.get("role") != "quick_eval":
            continue
        keys.add((row["variant"], row["cell_id"], row["reveal_m"], row["mu"], row["seed"], row["arm"]))
    return keys


def _progress(payload: dict[str, Any]) -> None:
    PROGRESS_QUICK_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_QUICK_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def _episode_row(
    *,
    variant: str,
    cell: dict[str, Any],
    reveal: float,
    mu: float,
    seed: int,
    arm: str,
    tau: float,
    result: dict[str, Any],
) -> dict[str, Any]:
    telemetry = result.get("telemetry", {})
    backend = result.get("backend_info", {})
    return {
        "role": "quick_eval",
        "variant": variant,
        "cell_id": cell["cell_id"],
        "delay_steps": int(cell["delay_steps"]),
        "noise_std": float(cell["noise_std"]),
        "reveal_m": float(reveal),
        "mu": float(mu),
        "seed": int(seed),
        "arm": arm,
        "outcome": result["outcome"],
        "success": bool(result["success"]),
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


def expected_quick_units(prereg: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for variant in prereg["quick_variants"]:
        for cell in prereg["quick_cells"]:
            for reveal in cell["reveals"]:
                for mu in prereg["quick_mu_points"]:
                    seed = _seed_for("quick", variant, cell["cell_id"], reveal, mu)
                    for arm in prereg["quick_arms"]:
                        units.append(
                            {
                                "variant": variant,
                                "cell": cell,
                                "reveal": float(reveal),
                                "mu": float(mu),
                                "seed": seed,
                                "arm": arm,
                            }
                        )
    return units


def run_quick(*, resume: bool) -> dict[str, Any]:
    prereg = load_preregistration()
    reg = _load_module(REGIME_SCRIPT, "ramp_policy_voi_regime")
    mod_b = _load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = _load_module(COND_SCRIPT, "voi_conditional_prior")
    interp = mod_c.interp_lin
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not resume:
        for path in (ROWS_QUICK_CSV, METRICS_QUICK_CSV, PROGRESS_QUICK_JSONL, QUICK_JSON, DOC_PATH):
            if path.exists():
                path.unlink()

    started = time.time()
    done = _done_keys(ROWS_QUICK_CSV) if resume else set()
    units = expected_quick_units(prereg)
    calibration: dict[str, dict[str, Any]] = {}
    completed = 0
    client = ChronoWorkerClient(stderr_log=STDERR_LOG)
    try:
        for variant in prereg["quick_variants"]:
            calibration[variant] = calibrate_tau_for_variant(client, reg, mod_b, interp, variant=variant)
            _progress({"stage": "calibration_done", "variant": variant, **calibration[variant]})
        for unit in units:
            cell = unit["cell"]
            key = (
                unit["variant"],
                cell["cell_id"],
                str(unit["reveal"]),
                str(unit["mu"]),
                str(unit["seed"]),
                unit["arm"],
            )
            if key in done:
                completed += 1
                continue
            tau = float(calibration[unit["variant"]]["tau"])
            scenario = _make_scenario(
                reg,
                mod_b,
                interp,
                reveal=unit["reveal"],
                mu=unit["mu"],
                seed=unit["seed"],
                variant=unit["variant"],
            )
            builder = _controller_builder(
                reg,
                mod_b,
                interp,
                reveal=unit["reveal"],
                arm=unit["arm"],
                mu=unit["mu"],
                tau=tau,
            )
            result = run_controller_episode(
                client,
                scenario,
                builder(),
                variant=unit["variant"],
                delay_steps=int(cell["delay_steps"]),
                noise_std=float(cell["noise_std"]),
                seed=int(unit["seed"]),
            )
            _append_row(
                ROWS_QUICK_CSV,
                _episode_row(
                    variant=unit["variant"],
                    cell=cell,
                    reveal=unit["reveal"],
                    mu=unit["mu"],
                    seed=unit["seed"],
                    arm=unit["arm"],
                    tau=tau,
                    result=result,
                ),
            )
            completed += 1
            _progress(
                {
                    "stage": "quick_unit_done",
                    "completed": completed,
                    "total": len(units),
                    "variant": unit["variant"],
                    "cell_id": cell["cell_id"],
                    "reveal_m": unit["reveal"],
                    "mu": unit["mu"],
                    "arm": unit["arm"],
                    "outcome": result["outcome"],
                    "elapsed_s": round(time.time() - started, 1),
                }
            )
    finally:
        client.close()

    rows = _read_csv_rows(ROWS_QUICK_CSV)
    summary = summarize_quick(rows, prereg, calibration=calibration, elapsed_s=time.time() - started)
    write_json(QUICK_JSON, summary)
    write_metrics(summary)
    write_markdown(summary)
    return summary


def _success_rate(rows: list[dict[str, str]]) -> float:
    if not rows:
        return float("nan")
    return float(np.mean([1.0 if str(row.get("success")) == "True" else 0.0 for row in rows]))


def summarize_quick(
    rows: list[dict[str, str]],
    prereg: dict[str, Any],
    *,
    calibration: dict[str, dict[str, Any]],
    elapsed_s: float,
) -> dict[str, Any]:
    expected = expected_quick_units(prereg)
    expected_keys = {
        (
            unit["variant"],
            unit["cell"]["cell_id"],
            str(unit["reveal"]),
            str(unit["mu"]),
            str(unit["seed"]),
            unit["arm"],
        )
        for unit in expected
    }
    actual_keys = {
        (row["variant"], row["cell_id"], row["reveal_m"], row["mu"], row["seed"], row["arm"])
        for row in rows
        if row.get("role") == "quick_eval"
    }
    clean_rows = [row for row in rows if row.get("cell_id") == "clean"]
    degraded_rows = [row for row in rows if row.get("cell_id") != "clean"]
    reset_obs_finite_all = all(str(row.get("reset_obs_finite")) == "True" for row in rows)
    variant_match_all = all(str(row.get("variant_match")) == "True" for row in rows)
    quick_mode_is_verdict = bool(prereg.get("quick_mode_is_verdict", True))
    by_cell: dict[str, Any] = {}
    for cell in prereg["quick_cells"]:
        cell_rows = [row for row in rows if row.get("cell_id") == cell["cell_id"]]
        by_reveal: dict[str, Any] = {}
        for reveal in cell["reveals"]:
            reveal_rows = [row for row in cell_rows if float(row.get("reveal_m", "nan")) == float(reveal)]
            rates = {
                arm: round(_success_rate([row for row in reveal_rows if row.get("arm") == arm]), 4)
                for arm in prereg["quick_arms"]
            }
            by_reveal[f"{float(reveal):g}"] = {
                "success_rates": rates,
                "indicative_voi_oracle_minus_seeker": (
                    None
                    if any(math.isnan(rates[arm]) for arm in ("oracle_ramp", "threshold_seeker"))
                    else round(rates["oracle_ramp"] - rates["threshold_seeker"], 4)
                ),
                "indicative_detection_value_seeker_minus_fixed": (
                    None
                    if any(math.isnan(rates[arm]) for arm in ("threshold_seeker", "fixed_ramp"))
                    else round(rates["threshold_seeker"] - rates["fixed_ramp"], 4)
                ),
                "rows": len(reveal_rows),
            }
        by_cell[cell["cell_id"]] = {"delay_steps": cell["delay_steps"], "noise_std": cell["noise_std"], "by_reveal": by_reveal}
    protocol_gates = {
        "all_expected_rows_written": actual_keys == expected_keys,
        "clean_rows_present": len(clean_rows) > 0,
        "degraded_spot_rows_present": len(degraded_rows) > 0,
        "reset_obs_finite_all": reset_obs_finite_all,
        "variant_match_all": variant_match_all,
        "quick_mode_is_not_verdict": not quick_mode_is_verdict,
        "calibration_written": set(calibration) == set(prereg["quick_variants"]),
    }
    protocol_gates["all_passed"] = all(protocol_gates.values())
    return {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": "quick",
        "created_at_utc": utc_timestamp(),
        "elapsed_s": round(float(elapsed_s), 1),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "e0_artifact": prereg["e0_artifact"],
        "e1_full_artifact": prereg["e1_full_artifact"],
        "rows_csv": str(ROWS_QUICK_CSV.relative_to(REPO_ROOT)),
        "metrics_csv": str(METRICS_QUICK_CSV.relative_to(REPO_ROOT)),
        "quick_mode_is_verdict": False,
        "calibration": calibration,
        "protocol_gates": protocol_gates,
        "row_count": len(rows),
        "expected_row_count": len(expected),
        "quick_readouts": by_cell,
        "decision": {
            "e2_quick_verdict": "protocol_smoke_passed" if protocol_gates["all_passed"] else "protocol_smoke_failed",
            "two_regime_law_verdict": "not_decided_by_quick_mode",
            "track_f_admitted": False,
            "next_admitted_step": "Register full E2 pricing with frozen variants/reveals/mu/seeds/CIs, or proceed to E3 only after E2 disposition per roadmap.",
        },
    }


def write_metrics(summary: dict[str, Any]) -> None:
    rows = [
        {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
        {"metric": "quick_mode_is_verdict", "value": 1.0 if summary["quick_mode_is_verdict"] else 0.0},
        {"metric": "row_count", "value": float(summary["row_count"])},
        {"metric": "expected_row_count", "value": float(summary["expected_row_count"])},
        {"metric": "reset_obs_finite_all", "value": 1.0 if summary["protocol_gates"]["reset_obs_finite_all"] else 0.0},
        {"metric": "variant_match_all", "value": 1.0 if summary["protocol_gates"]["variant_match_all"] else 0.0},
    ]
    METRICS_QUICK_CSV.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_QUICK_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary: dict[str, Any]) -> None:
    gates = summary["protocol_gates"]
    clean = summary["quick_readouts"].get("clean", {}).get("by_reveal", {})
    degraded = {k: v for k, v in summary["quick_readouts"].items() if k != "clean"}
    lines = [
        "# M3251 Phase-4 E2 Chrono Two-Regime Smoke",
        "",
        "Status: completed. This is a protocol smoke only; it is not the Chrono two-regime-law verdict and does not admit Track F.",
        "",
        "## Verdict",
        "",
        f"- E2 quick verdict: **{summary['decision']['e2_quick_verdict']}**.",
        f"- Protocol gates passed: **{str(gates['all_passed']).lower()}**.",
        "- Two-regime-law verdict: **not decided by quick mode**.",
        "",
        "## Measured",
        "",
        f"- Rows: {summary['row_count']} / expected {summary['expected_row_count']}.",
        f"- Rows CSV: `{summary['rows_csv']}`.",
        f"- Metrics CSV: `{summary['metrics_csv']}`.",
        "",
        "| cell | reveal m | oracle | seeker | fixed | indicative oracle-seeker | indicative seeker-fixed | rows |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for reveal, payload in clean.items():
        rates = payload["success_rates"]
        lines.append(
            f"| clean | {reveal} | {rates['oracle_ramp']:.4f} | {rates['threshold_seeker']:.4f} | "
            f"{rates['fixed_ramp']:.4f} | {payload['indicative_voi_oracle_minus_seeker']} | "
            f"{payload['indicative_detection_value_seeker_minus_fixed']} | {payload['rows']} |"
        )
    for cell_id, cell_payload in degraded.items():
        for reveal, payload in cell_payload["by_reveal"].items():
            rates = payload["success_rates"]
            lines.append(
                f"| {cell_id} | {reveal} | {rates['oracle_ramp']:.4f} | {rates['threshold_seeker']:.4f} | "
                f"{rates['fixed_ramp']:.4f} | {payload['indicative_voi_oracle_minus_seeker']} | "
                f"{payload['indicative_detection_value_seeker_minus_fixed']} | {payload['rows']} |"
            )
    lines += [
        "",
        "Calibration:",
        "",
    ]
    for variant, cal in sorted(summary["calibration"].items()):
        lines.append(
            f"- `{variant}`: tau={cal['tau']}, max_shortfall={cal['max_shortfall']}, "
            f"outcome={cal['outcome']}, reset_finite={cal['reset_obs_finite']}, variant_match={cal['variant_match']}."
        )
    lines += [
        "",
        "## Inferred",
        "",
        "The quick panel proves only that the E2 controller family and degraded observation filter execute through the Chrono worker. Indicative success-rate differences are not effect-size claims and must not be used as the full E2 verdict.",
        "",
        "Track F remains blocked until Track E completes and CP-3 confirms targets and budget.",
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
        print(json.dumps({"preregistration": str(PREREG_JSON), "quick_rows": len(expected_quick_units(payload))}, sort_keys=True))
    if args.quick:
        summary = run_quick(resume=args.resume)
        print(json.dumps(summary["decision"], sort_keys=True))
    if not args.write_prereg and not args.quick:
        raise SystemExit("nothing to do; pass --write-prereg and/or --quick")


if __name__ == "__main__":
    main()
