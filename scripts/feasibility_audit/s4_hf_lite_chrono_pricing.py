"""D1 S4-HF-lite Chrono multi-vehicle direction-pricing rollout.

This is a small high-fidelity pricing measurement, not a driver-performance
or high-fidelity-sufficiency claim.  It replays a frozen subset of A3 C5-prime
structural-gap rows through the Chrono worker across the Sedan/BMW/UAZBUS
variant selector.  The only accepted readout is direction preservation:
does a reproducible structured-oracle tail still beat the per-instance tuned
reflex floor on the same rows for each Chrono vehicle variant?

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/s4_hf_lite_chrono_pricing.py --write-prereg
    PYTHONPATH=src python scripts/feasibility_audit/s4_hf_lite_chrono_pricing.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/s4_hf_lite_chrono_pricing.py --resume
"""

from __future__ import annotations

import argparse
import ast
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

import c5_reflex_degradation as c5  # noqa: E402
from autodrift.artifacts import utc_timestamp  # noqa: E402
from autodrift.chrono_vehicle_backend import (  # noqa: E402
    BACKEND_ID,
    CHRONO_VEHICLE_VARIANTS,
    KNOWN_DIFFERENCES,
    scenario_from_env,
)
from autodrift.env import AutoDriftEnv  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "s4_hf_lite_chrono_pricing_prereg.json"
RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "s4_hf_lite_chrono_pricing.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "s4_hf_lite_chrono_pricing"
SOURCE_ROWS_CSV = REPO_ROOT / "runs" / "feasibility_audit" / "c5prime_target_consolidation" / "episode_rows.csv"
SOURCE_RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "c5prime_target_consolidation.json"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr.log"

SEED_BASE = 20260816
TARGET_LEVELS = ("S1", "S2", "S3")
VARIANTS = ("sedan_tmeasy", "bmw_e90_tmeasy", "uazbus_tmeasy")
FULL_ROWS_PER_LEVEL = 4
QUICK_ROWS_PER_LEVEL = 1
ARMS = ("fixed_star", "v4_pertuned", "structured_oracle_tail")

CLAIM_BOUNDARY = (
    "D1 S4-HF-lite Chrono direction-pricing only: frozen A3 C5-prime structured "
    "gap rows are replayed through whitelisted Chrono vehicle variants with "
    "scripted fixed/per-tuned reflex floors and a reproducible structured-oracle "
    "tail. Absolute success rates are not claims. No training, incumbent driver "
    "mutation, validation ranking, promotion, paper, repair-success, robustness "
    "result, feasibility-proof, high-fidelity sufficiency, or self-ID claim."
)


@dataclass(frozen=True)
class SelectedRow:
    row_id: str
    level: str
    instance: int
    eval_seed: int
    oracle_by: str
    pertuned_grid: tuple[float, float, float]
    source_fixed_star_outcome: str
    source_pertuned_outcome: str
    source_oracle_solved: bool


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else repr(number)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stable_score(row: dict[str, str]) -> str:
    key = f"{SEED_BASE}:{row['level']}:{row['instance']}:{row['eval_seed']}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _eligible_source_rows() -> list[dict[str, str]]:
    rows = _read_csv_rows(SOURCE_ROWS_CSV)
    eligible = [
        row
        for row in rows
        if row.get("level") in TARGET_LEVELS
        and row.get("surface") == "T_limit"
        and row.get("oracle_solved") == "True"
        and row.get("v4_pertuned_outcome") != "success"
        and str(row.get("oracle_by", "")).startswith("structured:")
    ]
    if not eligible:
        raise RuntimeError(f"no eligible structured A3 gap rows found in {SOURCE_ROWS_CSV}")
    return eligible


def select_prereg_rows(rows_per_level: int = FULL_ROWS_PER_LEVEL) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for level in TARGET_LEVELS:
        candidates = [row for row in _eligible_source_rows() if row["level"] == level]
        candidates.sort(key=lambda row: (_stable_score(row), int(row["instance"]), int(row["eval_seed"])))
        if len(candidates) < rows_per_level:
            raise RuntimeError(f"{level} has {len(candidates)} eligible rows, need {rows_per_level}")
        for rank, row in enumerate(candidates[:rows_per_level], start=1):
            selected.append(
                {
                    "row_id": f"{level}-inst{int(row['instance']):02d}-seed{int(row['eval_seed'])}",
                    "level": level,
                    "instance": int(row["instance"]),
                    "eval_seed": int(row["eval_seed"]),
                    "selection_rank_within_level": rank,
                    "selection_score_sha256": _stable_score(row),
                    "oracle_by": row["oracle_by"],
                    "pertuned_grid": list(ast.literal_eval(row["pertuned_grid"])),
                    "source_fixed_star_outcome": row["fixed_star_outcome"],
                    "source_pertuned_outcome": row["v4_pertuned_outcome"],
                    "source_oracle_solved": row["oracle_solved"] == "True",
                }
            )
    return selected


def build_preregistration() -> dict[str, Any]:
    selected_rows = select_prereg_rows(FULL_ROWS_PER_LEVEL)
    eligible_counts = {
        level: sum(1 for row in _eligible_source_rows() if row["level"] == level)
        for level in TARGET_LEVELS
    }
    return {
        "protocol": "s4_hf_lite_chrono_direction_pricing_preregistration",
        "roadmap_unit": "D1 S4 multi-vehicle Chrono pricing",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_chrono_pricing_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_artifacts": {
            "a3_results_json": str(SOURCE_RESULTS_JSON),
            "a3_episode_rows_csv": str(SOURCE_ROWS_CSV),
            "chrono_variant_selector_smoke": "experiments/feasibility_audit/s4_hf_lite_variant_selector_smoke.json",
        },
        "source_row_filter": {
            "levels": list(TARGET_LEVELS),
            "surface": "T_limit",
            "oracle_solved": True,
            "pertuned_outcome": "not success",
            "oracle_by_prefix": "structured:",
            "cem_rows": "excluded because A3 did not persist CEM action sequences",
            "eligible_counts_by_level": eligible_counts,
            "selection_rule": (
                f"for each level, sort eligible rows by sha256('{SEED_BASE}:<level>:<instance>:<eval_seed>'), "
                f"then take the first {FULL_ROWS_PER_LEVEL} rows"
            ),
        },
        "selected_rows": selected_rows,
        "chrono_vehicle_variants": list(VARIANTS),
        "arms": {
            "fixed_star": "A3 pooled S0/T-limit fixed 27-grid reflex config replayed on Chrono observations",
            "v4_pertuned": "A3 per (level,T_limit,instance) 27-grid winner replayed on Chrono observations",
            "structured_oracle_tail": (
                "A3 selected structured oracle action family, with fixed_star prefix until the obstacle-present "
                "obs72 bit is visible in the Chrono rollout; CEM oracles excluded"
            ),
        },
        "unmapped_lateral_channel_handling": {
            "lf_lr_cg_shift": (
                "A3 scenario carries lf/lr/cg_shift in params, but Chrono backend does not continuously map "
                "them. D1 therefore treats vehicle selection as a discrete geometry/inertia/tire-fixture "
                "bracket and does not claim continuous lf/lr pricing."
            ),
            "iz_inertia_scale": (
                "A3 iz/inertia_scale is carried in scenario params for provenance but selected Chrono vehicle "
                "inertia tensors remain the backend fixture. backend_info is recorded per reset."
            ),
            "cf_cr_tire_curve_family": (
                "continuous cf/cr and tire-curve-family scales are not mapped; all D1 variants use TMeasy "
                "tires. Tire-fixture differences are discrete vehicle-model differences only."
            ),
            "mass_brake_drive_tau": (
                "scenario mass, drive/brake force scales, and control-layer lags remain the frozen A3 row "
                "values. Chrono matches total mass by chassis-mass override and clips command scaling as "
                "documented in KNOWN_DIFFERENCES."
            ),
        },
        "preregistered_readouts": {
            "primary_per_vehicle": (
                "direction_delta = success_rate(structured_oracle_tail) - success_rate(v4_pertuned) on "
                "the frozen selected rows for that Chrono variant"
            ),
            "verdicts": {
                "direction_preserved": "direction_delta > 0",
                "neutral": "direction_delta == 0",
                "reversed": "direction_delta < 0",
            },
            "secondary_context": [
                "structured_oracle_tail - fixed_star direction delta",
                "backend_info variant/model/tire/mass/wheelbase/wheeltrack/inertia emitted at reset",
                "outcome failure-mode composition per arm",
            ],
            "absolute_success_rates_are_claims": False,
        },
        "runtime_gates": [
            "all reset observations are finite obs72",
            "backend_info chrono_vehicle_variant matches the requested variant",
            "only structured oracle rows from the frozen selected_rows set are executed",
            "quick mode must exercise all requested Chrono variants before full rollout",
        ],
        "decision_rule": (
            "D1 reports one direction-preservation verdict per Chrono vehicle. The D1 question is fully "
            "preserved only if all three variants are direction_preserved; partial/neutral/reversed verdicts "
            "are accepted negative or mixed results at full fidelity."
        ),
    }


def _load_prereg(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing preregistration {path}; run with --write-prereg first")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("frozen_before_any_chrono_pricing_rollout"):
        raise ValueError(f"{path} is not marked frozen before rollout")
    return data


def _as_selected(row: dict[str, Any]) -> SelectedRow:
    grid = tuple(float(x) for x in row["pertuned_grid"])
    if len(grid) != 3:
        raise ValueError(f"bad pertuned_grid for {row.get('row_id')}: {row.get('pertuned_grid')}")
    return SelectedRow(
        row_id=str(row["row_id"]),
        level=str(row["level"]),
        instance=int(row["instance"]),
        eval_seed=int(row["eval_seed"]),
        oracle_by=str(row["oracle_by"]),
        pertuned_grid=grid,
        source_fixed_star_outcome=str(row["source_fixed_star_outcome"]),
        source_pertuned_outcome=str(row["source_pertuned_outcome"]),
        source_oracle_solved=bool(row["source_oracle_solved"]),
    )


def _configure_c5prime_globals() -> None:
    c5.BASE = c5.BASE_C5PRIME
    c5.LEVELS = c5.LEVELS_MAIN


def _exact_row_params(selected: SelectedRow) -> tuple[dict[str, float], dict[str, Any]]:
    _configure_c5prime_globals()
    vehicle = c5.sample_vehicle(selected.level, selected.instance)
    rows = c5.sample_rows(selected.level, "T_limit", selected.instance, vehicle, "val", 12)
    matches = [row for row in rows if int(row["eval_seed"]) == selected.eval_seed]
    if len(matches) != 1:
        raise RuntimeError(f"could not reconstruct A3 row {selected.row_id} exactly")
    return vehicle, matches[0]


def _scenario_for(selected: SelectedRow, variant: str) -> dict[str, Any]:
    vehicle, row = _exact_row_params(selected)
    env = AutoDriftEnv(c5.row_env_config("T_limit", row["v"], row["mu"], row["s_arc"], row["hw"], vehicle))
    try:
        env.reset(seed=selected.eval_seed)
        scenario = scenario_from_env(env)
    finally:
        env.close()
    scenario["scenario_id"] = f"d1-{variant}-{selected.row_id}"
    scenario["chrono_vehicle_variant"] = variant
    scenario["d1_source"] = {
        "row_id": selected.row_id,
        "level": selected.level,
        "instance": selected.instance,
        "eval_seed": selected.eval_seed,
        "oracle_by": selected.oracle_by,
        "source_fixed_star_outcome": selected.source_fixed_star_outcome,
        "source_pertuned_outcome": selected.source_pertuned_outcome,
    }
    return scenario


def _tail_action(oracle_by: str, rel_step: int) -> np.ndarray:
    name = oracle_by.removeprefix("structured:")
    if name == "full_brake":
        return np.array([0.0, -1.0, 1.0], dtype=np.float32)
    if name.startswith("brake_steer_"):
        steer = float(name.removeprefix("brake_steer_"))
        return np.array([steer, -1.0, 1.0], dtype=np.float32)
    if name.startswith("coast_steer_"):
        steer = float(name.removeprefix("coast_steer_"))
        return np.array([steer, -1.0, -1.0], dtype=np.float32)
    if name.startswith("swerve_"):
        # A3 names are swerve_{+/-1}_n{10|20}: steer+brake for n steps, then full brake.
        parts = name.split("_")
        if len(parts) != 3 or not parts[2].startswith("n"):
            raise ValueError(f"unsupported structured oracle name: {oracle_by}")
        steer = float(parts[1])
        n_steps = int(parts[2][1:])
        if rel_step < n_steps:
            return np.array([steer, -1.0, 1.0], dtype=np.float32)
        return np.array([0.0, -1.0, 1.0], dtype=np.float32)
    raise ValueError(f"unsupported structured oracle name: {oracle_by}")


def _fixed_grid_policy(grid: tuple[float, float, float]) -> Callable[[int, np.ndarray], np.ndarray]:
    v2_cfg, v4_cfg = c5.grid_cfgs(*grid)

    def policy(_step: int, obs: np.ndarray) -> np.ndarray:
        return c5.composed_action(np.asarray(obs, dtype=np.float32), v2_cfg, v4_cfg)

    return policy


class StructuredOraclePolicy:
    def __init__(self, oracle_by: str, prefix_grid: tuple[float, float, float]):
        self.oracle_by = oracle_by
        self.prefix = _fixed_grid_policy(prefix_grid)
        self.switched = False
        self.rel_step = 0

    def __call__(self, step: int, obs: np.ndarray) -> np.ndarray:
        obstacle_present = bool(float(np.asarray(obs)[44]) > 0.5)
        if obstacle_present:
            self.switched = True
        if not self.switched:
            return self.prefix(step, obs)
        action = _tail_action(self.oracle_by, self.rel_step)
        self.rel_step += 1
        return action


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


def run_chrono_episode(
    client: ChronoWorkerClient,
    scenario: dict[str, Any],
    policy: Callable[[int, np.ndarray], np.ndarray],
    *,
    requested_variant: str,
) -> dict[str, Any]:
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]))
    backend_info = dict(reset_reply.get("backend_info", {}))
    reset_obs_finite = _finite_obs(obs)
    variant_match = backend_info.get("chrono_vehicle_variant") == requested_variant
    speeds: list[float] = []
    signature = float(np.sum(obs, dtype=np.float64))
    visible_step: int | None = 0 if float(obs[44]) > 0.5 else None
    terminated = truncated = False
    info: dict[str, Any] = dict(reset_reply.get("info", {}))
    status = "reset"
    steps = 0
    max_steps = int(scenario["max_steps"]) + 5
    while not (terminated or truncated) and steps < max_steps:
        action = policy(steps, obs)
        obs, terminated, truncated, status, info = client.step(action)
        if visible_step is None and float(obs[44]) > 0.5:
            visible_step = steps + 1
        if not _finite_obs(obs):
            break
        signature += float(np.sum(obs, dtype=np.float64))
        if "speed" in info:
            speeds.append(float(info["speed"]))
        steps += 1
    margin = info.get("min_clearance_margin")
    return {
        "outcome": _outcome_from_info(info),
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
        "speed_mean": float(np.mean(speeds)) if speeds else float("nan"),
        "trace_signature": repr(signature),
        "reset_obs_finite": reset_obs_finite,
        "variant_match": variant_match,
        "backend_info": {
            key: backend_info.get(key)
            for key in (
                "backend_id",
                "chrono_vehicle_variant",
                "chrono_vehicle_model",
                "chrono_tire_model",
                "vehicle_total_mass",
                "target_mass",
                "chrono_base_vehicle_mass",
                "chrono_max_steer_rad",
                "chrono_wheelbase_m",
                "chrono_wheeltrack_m",
                "chrono_chassis_inertia_xx_kgm2",
            )
        },
    }


class RestartingClient:
    def __init__(self, restart_every: int):
        self.restart_every = max(1, int(restart_every))
        self.count = 0
        self.client: ChronoWorkerClient | None = None

    def _ensure(self) -> ChronoWorkerClient:
        if self.client is None:
            self.client = ChronoWorkerClient(stderr_log=STDERR_LOG)
            self.count = 0
        return self.client

    def restart(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def run(self, scenario: dict[str, Any], policy: Callable[[int, np.ndarray], np.ndarray], variant: str) -> dict[str, Any]:
        if self.count >= self.restart_every:
            self.restart()
        try:
            result = run_chrono_episode(self._ensure(), scenario, policy, requested_variant=variant)
        except Exception as exc:
            self.restart()
            result = run_chrono_episode(self._ensure(), scenario, policy, requested_variant=variant)
            result["restart_after_error"] = f"{type(exc).__name__}: {exc}"
        self.count += 1
        return result

    def close(self) -> None:
        self.restart()


FIELDNAMES = [
    "variant",
    "row_id",
    "level",
    "instance",
    "eval_seed",
    "arm",
    "source_fixed_star_outcome",
    "source_pertuned_outcome",
    "source_oracle_by",
    "chrono_outcome",
    "chrono_steps",
    "termination_reason",
    "completion_reason",
    "obstacle_visible_step",
    "min_clearance_margin",
    "speed_mean",
    "reset_obs_finite",
    "variant_match",
    "backend_model",
    "backend_tire",
    "target_mass",
    "vehicle_total_mass",
    "wheelbase_m",
    "wheeltrack_m",
    "trace_signature",
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


def _done_keys(path: Path) -> set[tuple[str, str, str]]:
    if not path.exists():
        return set()
    return {
        (str(row["variant"]), str(row["row_id"]), str(row["arm"]))
        for row in _read_csv_rows(path)
    }


def _summarize(rows: list[dict[str, str]], prereg: dict[str, Any], *, quick: bool) -> dict[str, Any]:
    per_vehicle: dict[str, Any] = {}
    for variant in VARIANTS:
        variant_rows = [row for row in rows if row["variant"] == variant]
        arm_rows = {arm: [row for row in variant_rows if row["arm"] == arm] for arm in ARMS}
        arm_success = {
            arm: sum(1 for row in arm_rows[arm] if row["chrono_outcome"] == "success")
            for arm in ARMS
        }
        arm_n = {arm: len(arm_rows[arm]) for arm in ARMS}
        pertuned_rate = arm_success["v4_pertuned"] / max(arm_n["v4_pertuned"], 1)
        oracle_rate = arm_success["structured_oracle_tail"] / max(arm_n["structured_oracle_tail"], 1)
        fixed_rate = arm_success["fixed_star"] / max(arm_n["fixed_star"], 1)
        delta_vs_pertuned = oracle_rate - pertuned_rate
        if delta_vs_pertuned > 0.0:
            verdict = "direction_preserved"
        elif delta_vs_pertuned < 0.0:
            verdict = "reversed"
        else:
            verdict = "neutral"
        failure_modes = {
            arm: {
                outcome: sum(1 for row in arm_rows[arm] if row["chrono_outcome"] == outcome)
                for outcome in sorted({row["chrono_outcome"] for row in arm_rows[arm]})
            }
            for arm in ARMS
        }
        per_vehicle[variant] = {
            "n_rows": arm_n["v4_pertuned"],
            "arm_success_counts": arm_success,
            "arm_n": arm_n,
            "success_rates_context_not_claims": {
                "fixed_star": round(fixed_rate, 4),
                "v4_pertuned": round(pertuned_rate, 4),
                "structured_oracle_tail": round(oracle_rate, 4),
            },
            "direction_delta_oracle_minus_pertuned": round(delta_vs_pertuned, 4),
            "direction_delta_oracle_minus_fixed_star": round(oracle_rate - fixed_rate, 4),
            "direction_verdict": verdict,
            "failure_modes": failure_modes,
            "reset_obs_finite_all": all(row["reset_obs_finite"] == "True" for row in variant_rows),
            "variant_match_all": all(row["variant_match"] == "True" for row in variant_rows),
        }
    return {
        "protocol": "s4_hf_lite_chrono_direction_pricing",
        "generated_at_utc": utc_timestamp(),
        "quick_mode": quick,
        "claim_boundary": CLAIM_BOUNDARY,
        "backend_id": BACKEND_ID,
        "chrono_known_differences": list(KNOWN_DIFFERENCES),
        "preregistration_echo": {
            "file": str(PREREG_JSON),
            "decision_rule": prereg["decision_rule"],
            "selected_rows": prereg["selected_rows"],
            "unmapped_lateral_channel_handling": prereg["unmapped_lateral_channel_handling"],
        },
        "variants": list(VARIANTS),
        "arms": list(ARMS),
        "row_count": len(rows),
        "rows_csv": str(RUN_DIR / ("episode_rows_quick.csv" if quick else "episode_rows.csv")),
        "per_vehicle": per_vehicle,
        "decision": {
            "all_vehicle_direction_preserved": all(
                block["direction_verdict"] == "direction_preserved" for block in per_vehicle.values()
            ),
            "vehicle_verdicts": {
                variant: block["direction_verdict"] for variant, block in per_vehicle.items()
            },
            "absolute_numbers_are_claims": False,
            "interpretation": (
                "Direction-preservation only. Mixed, neutral, or reversed vehicles are accepted as "
                "negative/mixed D1 evidence and do not invalidate A3 current-sim pricing by themselves."
            ),
        },
    }


def run_rollout(*, prereg: dict[str, Any], quick: bool, resume: bool, restart_every: int) -> dict[str, Any]:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows_csv = RUN_DIR / ("episode_rows_quick.csv" if quick else "episode_rows.csv")
    progress_jsonl = RUN_DIR / ("progress_quick.jsonl" if quick else "progress.jsonl")
    results_json = RESULTS_JSON.with_name("s4_hf_lite_chrono_pricing_quick.json") if quick else RESULTS_JSON
    if not resume and rows_csv.exists():
        rows_csv.unlink()
    selected = [_as_selected(row) for row in prereg["selected_rows"]]
    if quick:
        quick_selected: list[SelectedRow] = []
        for level in TARGET_LEVELS:
            quick_selected.extend([row for row in selected if row.level == level][:QUICK_ROWS_PER_LEVEL])
        selected = quick_selected
    fixed_star_grid = tuple(float(x) for x in json.loads(SOURCE_RESULTS_JSON.read_text(encoding="utf-8"))["fixed_star"]["grid"])
    if len(fixed_star_grid) != 3:
        raise RuntimeError(f"bad fixed_star grid: {fixed_star_grid}")

    done = _done_keys(rows_csv) if resume else set()
    total = len(selected) * len(VARIANTS) * len(ARMS)
    completed = len(done)
    chrono = RestartingClient(restart_every=restart_every)
    t0 = time.time()
    try:
        for variant in VARIANTS:
            if variant not in CHRONO_VEHICLE_VARIANTS:
                raise RuntimeError(f"unknown Chrono variant in prereg: {variant}")
            for selected_row in selected:
                scenario = _scenario_for(selected_row, variant)
                policies: dict[str, Callable[[int, np.ndarray], np.ndarray]] = {
                    "fixed_star": _fixed_grid_policy(fixed_star_grid),
                    "v4_pertuned": _fixed_grid_policy(selected_row.pertuned_grid),
                    "structured_oracle_tail": StructuredOraclePolicy(selected_row.oracle_by, fixed_star_grid),
                }
                for arm in ARMS:
                    key = (variant, selected_row.row_id, arm)
                    if key in done:
                        continue
                    result = chrono.run(scenario, policies[arm], variant)
                    backend = result["backend_info"]
                    record = {
                        "variant": variant,
                        "row_id": selected_row.row_id,
                        "level": selected_row.level,
                        "instance": selected_row.instance,
                        "eval_seed": selected_row.eval_seed,
                        "arm": arm,
                        "source_fixed_star_outcome": selected_row.source_fixed_star_outcome,
                        "source_pertuned_outcome": selected_row.source_pertuned_outcome,
                        "source_oracle_by": selected_row.oracle_by,
                        "chrono_outcome": result["outcome"],
                        "chrono_steps": result["steps"],
                        "termination_reason": result["termination_reason"],
                        "completion_reason": result["completion_reason"],
                        "obstacle_visible_step": result["obstacle_visible_step"],
                        "min_clearance_margin": result["min_clearance_margin"],
                        "speed_mean": result["speed_mean"],
                        "reset_obs_finite": result["reset_obs_finite"],
                        "variant_match": result["variant_match"],
                        "backend_model": backend.get("chrono_vehicle_model"),
                        "backend_tire": backend.get("chrono_tire_model"),
                        "target_mass": backend.get("target_mass"),
                        "vehicle_total_mass": backend.get("vehicle_total_mass"),
                        "wheelbase_m": backend.get("chrono_wheelbase_m"),
                        "wheeltrack_m": json.dumps(_jsonable(backend.get("chrono_wheeltrack_m"))),
                        "trace_signature": result["trace_signature"],
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                    _append_row(rows_csv, record)
                    completed += 1
                    with progress_jsonl.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(_jsonable({
                            "completed": completed,
                            "total": total,
                            "elapsed_s": round(time.time() - t0, 1),
                            "variant": variant,
                            "row_id": selected_row.row_id,
                            "arm": arm,
                            "outcome": result["outcome"],
                        }), sort_keys=True) + "\n")
                    print(
                        f"[{completed}/{total}] {variant} {selected_row.row_id} {arm} -> {result['outcome']} "
                        f"steps={result['steps']}",
                        flush=True,
                    )
    finally:
        chrono.close()

    rows = _read_csv_rows(rows_csv)
    summary = _summarize(rows, prereg, quick=quick)
    summary["budget"] = {
        "elapsed_s": round(time.time() - t0, 1),
        "selected_source_rows": len(selected),
        "chrono_episodes": len(rows),
    }
    summary["progress_jsonl"] = str(progress_jsonl)
    _write_json(results_json, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-prereg", action="store_true", help="write the frozen preregistration and exit")
    parser.add_argument("--quick", action="store_true", help="run a small protocol smoke using the frozen prereg")
    parser.add_argument("--resume", action="store_true", help="resume by skipping existing rows in the rows CSV")
    parser.add_argument("--restart-every", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.write_prereg:
        if PREREG_JSON.exists():
            raise SystemExit(f"{PREREG_JSON} already exists; remove it explicitly before regenerating")
        payload = build_preregistration()
        _write_json(PREREG_JSON, payload)
        print(json.dumps({"wrote": str(PREREG_JSON), "selected_rows": len(payload["selected_rows"])}, sort_keys=True))
        return
    prereg = _load_prereg(PREREG_JSON)
    summary = run_rollout(prereg=prereg, quick=bool(args.quick), resume=bool(args.resume), restart_every=args.restart_every)
    print(json.dumps(summary["decision"], sort_keys=True))


if __name__ == "__main__":
    main()
