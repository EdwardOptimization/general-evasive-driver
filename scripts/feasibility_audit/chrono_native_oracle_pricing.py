"""D1b Chrono-native oracle pricing protocol smoke.

This script prices the C5-prime structural-ceiling direction inside the Chrono
backend, instead of replaying a current-sim oracle tail. It is still
engineering-only direction pricing: no training, no incumbent mutation, and no
high-fidelity sufficiency claim.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/chrono_native_oracle_pricing.py --write-prereg
    PYTHONPATH=src python scripts/feasibility_audit/chrono_native_oracle_pricing.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/chrono_native_oracle_pricing.py --full --resume
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
from autodrift.artifacts import utc_timestamp, write_json  # noqa: E402
from autodrift.chrono_vehicle_backend import (  # noqa: E402
    BACKEND_ID,
    CHRONO_VEHICLE_VARIANTS,
    KNOWN_DIFFERENCES,
    scenario_from_env,
)
from autodrift.env import AutoDriftEnv  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402


PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_native_oracle_pricing_prereg.json"
RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_native_oracle_pricing.json"
QUICK_RESULTS_JSON = (
    REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_native_oracle_pricing_quick.json"
)
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "chrono_native_oracle_pricing"
SOURCE_ROWS_CSV = REPO_ROOT / "runs" / "feasibility_audit" / "c5prime_target_consolidation" / "episode_rows.csv"
SOURCE_RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "c5prime_target_consolidation.json"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr.log"

SEED_BASE = 20260818
TARGET_LEVELS = ("S1", "S2", "S3")
SURFACE = "T_limit"
VARIANTS = ("sedan_tmeasy", "bmw_e90_tmeasy")
FULL_ROWS_PER_LEVEL = 3
ARMS = ("v4_pertuned", "native_oracle")

CLAIM_BOUNDARY = (
    "D1b Chrono-native oracle direction-pricing only: a frozen subset of A3 "
    "C5-prime structural-gap rows is searched inside the Chrono backend with "
    "structured candidates plus reduced-budget CEM, then compared against the "
    "same-row per-instance tuned reflex floor. This is a protocol/pricing "
    "measurement only: no training, incumbent driver mutation, validation "
    "ranking, promotion, paper, repair-success, robustness-result, "
    "feasibility-proof, high-fidelity sufficiency, or self-ID claim."
)


@dataclass(frozen=True)
class SelectedRow:
    row_id: str
    level: str
    instance: int
    eval_seed: int
    oracle_by: str
    pertuned_grid: tuple[float, float, float]
    source_pertuned_outcome: str
    source_oracle_solved: bool


@dataclass(frozen=True)
class SearchBudget:
    structured_limit: int
    cem_segments: int
    cem_segment_len: int
    cem_population: int
    cem_elites: int
    cem_iterations: int


QUICK_BUDGET = SearchBudget(
    structured_limit=5,
    cem_segments=3,
    cem_segment_len=8,
    cem_population=4,
    cem_elites=2,
    cem_iterations=1,
)
FULL_BUDGET = SearchBudget(
    structured_limit=15,
    cem_segments=6,
    cem_segment_len=8,
    cem_population=8,
    cem_elites=2,
    cem_iterations=3,
)


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
    write_json(path, _jsonable(payload))


def _stable_score(row: dict[str, str]) -> str:
    key = f"{SEED_BASE}:{row['level']}:{row['surface']}:{row['instance']}:{row['eval_seed']}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _eligible_source_rows() -> list[dict[str, str]]:
    rows = _read_csv_rows(SOURCE_ROWS_CSV)
    eligible = [
        row
        for row in rows
        if row.get("level") in TARGET_LEVELS
        and row.get("surface") == SURFACE
        and row.get("oracle_solved") == "True"
        and row.get("v4_pertuned_outcome") != "success"
        and str(row.get("oracle_by", "")).startswith("structured:")
    ]
    if not eligible:
        raise RuntimeError(f"no eligible structured current-sim gap rows found in {SOURCE_ROWS_CSV}")
    return eligible


def select_prereg_rows(rows_per_level: int = FULL_ROWS_PER_LEVEL) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    eligible = _eligible_source_rows()
    for level in TARGET_LEVELS:
        candidates = [row for row in eligible if row["level"] == level]
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
                    "source_pertuned_outcome": row["v4_pertuned_outcome"],
                    "source_oracle_solved": row["oracle_solved"] == "True",
                }
            )
    return selected


def build_preregistration() -> dict[str, Any]:
    selected_rows = select_prereg_rows(FULL_ROWS_PER_LEVEL)
    eligible = _eligible_source_rows()
    eligible_counts = {level: sum(1 for row in eligible if row["level"] == level) for level in TARGET_LEVELS}
    return {
        "protocol": "d1b_chrono_native_oracle_pricing_preregistration",
        "roadmap_unit": "D1b Chrono-native oracle pricing",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_d1b_rollout": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_artifacts": {
            "a3_results_json": str(SOURCE_RESULTS_JSON),
            "a3_episode_rows_csv": str(SOURCE_ROWS_CSV),
            "d1_tail_replay_proxy": "experiments/feasibility_audit/s4_hf_lite_chrono_pricing.json",
            "chrono_variant_selector_smoke": "experiments/feasibility_audit/s4_hf_lite_variant_selector_smoke.json",
        },
        "source_row_filter": {
            "levels": list(TARGET_LEVELS),
            "surface": SURFACE,
            "oracle_solved": True,
            "pertuned_outcome": "not success",
            "oracle_by_prefix": "structured:",
            "eligible_counts_by_level": eligible_counts,
            "selection_rule": (
                f"for each level, sort eligible rows by sha256('{SEED_BASE}:<level>:"
                f"<surface>:<instance>:<eval_seed>'), then take the first {FULL_ROWS_PER_LEVEL} rows"
            ),
        },
        "selected_rows": selected_rows,
        "chrono_vehicle_variants": list(VARIANTS),
        "arms": {
            "v4_pertuned": "A3 per-instance 27-grid reflex winner replayed on Chrono observations",
            "native_oracle": (
                "Chrono-native reveal-constrained search: v4_pertuned prefix until the obstacle-present "
                "obs72 bit is visible, then structured candidates plus CEM over piecewise action segments"
            ),
        },
        "search_budget": {
            "quick": QUICK_BUDGET.__dict__,
            "full": FULL_BUDGET.__dict__,
        },
        "unmapped_channel_handling": {
            "vehicle_variants": "D1b uses sedan_tmeasy plus bmw_e90_tmeasy as the minimum CP-2 preregistered pair.",
            "lf_lr_cg_shift": "Continuous A3 lf/lr/cg_shift values are carried for provenance but not mapped into Chrono.",
            "iz_cf_cr_tire_shape": "Continuous Iz/cf/cr/tire-shape scales are not mapped; TMeasy fixture differences are discrete vehicle-model differences only.",
            "mass": "Chrono backend continues to match target total mass via the existing chassis-mass override.",
        },
        "runtime_gates": [
            "preregistration file exists and is frozen before any D1b rollout",
            "all reset observations are finite obs72",
            "backend_info chrono_vehicle_variant matches the requested variant",
            "quick mode exercises both preregistered Chrono variants",
            "native_oracle executes at least one structured candidate and one CEM sample per quick row",
        ],
        "preregistered_readouts": {
            "primary_per_vehicle_full": (
                "direction_delta = success_rate(native_oracle) - success_rate(v4_pertuned) "
                "on the frozen selected rows for that Chrono variant"
            ),
            "direction_positive": "direction_delta > 0 for each preregistered variant",
            "quick_mode": "protocol smoke only; no D1b direction verdict",
            "absolute_success_rates_are_claims": False,
        },
        "decision_rule": (
            "M3230 is only the D1b protocol smoke: it passes if quick mode writes a summary, "
            "variant/obs gates pass, and native search exercises structured and CEM candidates. "
            "The D1b CP-2 precondition itself requires a later full managed rollout with a "
            "direction verdict per preregistered vehicle."
        ),
    }


def write_preregistration() -> dict[str, Any]:
    payload = build_preregistration()
    _write_json(PREREG_JSON, payload)
    return payload


def load_preregistration() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise FileNotFoundError(f"missing preregistration {PREREG_JSON}; run --write-prereg first")
    payload = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    if not payload.get("frozen_before_any_d1b_rollout"):
        raise ValueError(f"{PREREG_JSON} is not marked frozen_before_any_d1b_rollout")
    return payload


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
        source_pertuned_outcome=str(row["source_pertuned_outcome"]),
        source_oracle_solved=bool(row["source_oracle_solved"]),
    )


def _configure_c5prime_globals() -> None:
    c5.BASE = c5.BASE_C5PRIME
    c5.LEVELS = c5.LEVELS_MAIN


def _exact_row_params(selected: SelectedRow) -> tuple[dict[str, float], dict[str, Any]]:
    _configure_c5prime_globals()
    vehicle = c5.sample_vehicle(selected.level, selected.instance)
    rows = c5.sample_rows(selected.level, SURFACE, selected.instance, vehicle, "val", 12)
    matches = [row for row in rows if int(row["eval_seed"]) == selected.eval_seed]
    if len(matches) != 1:
        raise RuntimeError(f"could not reconstruct A3 row {selected.row_id} exactly")
    return vehicle, matches[0]


def _scenario_for(selected: SelectedRow, variant: str) -> dict[str, Any]:
    vehicle, row = _exact_row_params(selected)
    env = AutoDriftEnv(c5.row_env_config(SURFACE, row["v"], row["mu"], row["s_arc"], row["hw"], vehicle))
    try:
        env.reset(seed=selected.eval_seed)
        scenario = scenario_from_env(env)
    finally:
        env.close()
    scenario["scenario_id"] = f"d1b-{variant}-{selected.row_id}"
    scenario["chrono_vehicle_variant"] = variant
    scenario["d1b_source"] = {
        "row_id": selected.row_id,
        "level": selected.level,
        "instance": selected.instance,
        "eval_seed": selected.eval_seed,
        "source_pertuned_outcome": selected.source_pertuned_outcome,
        "source_oracle_by": selected.oracle_by,
    }
    return scenario


def structured_tail_candidates(limit: int | None = None) -> list[tuple[str, Callable[[int], np.ndarray]]]:
    candidates: list[tuple[str, Callable[[int], np.ndarray]]] = [
        ("full_brake", lambda _rel: np.array([0.0, -1.0, 1.0], dtype=np.float32)),
    ]
    for steer in (0.4, 0.7, 1.0, -0.4, -0.7, -1.0):
        candidates.append(
            (f"brake_steer_{steer:+.1f}", lambda _rel, steer=steer: np.array([steer, -1.0, 1.0], dtype=np.float32))
        )
    for steer in (0.7, 1.0, -0.7, -1.0):
        candidates.append(
            (f"coast_steer_{steer:+.1f}", lambda _rel, steer=steer: np.array([steer, -1.0, -1.0], dtype=np.float32))
        )
    for steer in (1.0, -1.0):
        for n_steps in (10, 20):
            candidates.append(
                (
                    f"swerve_{steer:+.0f}_n{n_steps}",
                    lambda rel, steer=steer, n_steps=n_steps: np.array(
                        [steer, -1.0, 1.0], dtype=np.float32
                    )
                    if rel < n_steps
                    else np.array([0.0, -1.0, 1.0], dtype=np.float32),
                )
            )
    return candidates if limit is None else candidates[:limit]


def _fixed_grid_policy(grid: tuple[float, float, float]) -> Callable[[int, np.ndarray], np.ndarray]:
    v2_cfg, v4_cfg = c5.grid_cfgs(*grid)

    def policy(_step: int, obs: np.ndarray) -> np.ndarray:
        return c5.composed_action(np.asarray(obs, dtype=np.float32), v2_cfg, v4_cfg)

    return policy


class RevealSwitchPolicy:
    def __init__(self, prefix: Callable[[int, np.ndarray], np.ndarray], tail: Callable[[int], np.ndarray]):
        self.prefix = prefix
        self.tail = tail
        self.switched = False
        self.rel_step = 0

    def __call__(self, step: int, obs: np.ndarray) -> np.ndarray:
        if bool(float(np.asarray(obs)[44]) > 0.5):
            self.switched = True
        if not self.switched:
            return self.prefix(step, obs)
        action = self.tail(self.rel_step)
        self.rel_step += 1
        return np.asarray(action, dtype=np.float32)


def _segments_tail(segments: np.ndarray, segment_len: int) -> Callable[[int], np.ndarray]:
    def tail(rel: int) -> np.ndarray:
        idx = min(max(rel, 0) // segment_len, len(segments) - 1)
        return np.asarray(segments[idx], dtype=np.float32)

    return tail


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
                "chrono_wheelbase_m",
                "chrono_wheeltrack_m",
            )
        },
    }


def _score_result(result: dict[str, Any], max_steps: int) -> float:
    margin_raw = result.get("min_clearance_margin")
    margin = float(np.clip(float(margin_raw), -2.0, 2.0)) if isinstance(margin_raw, (int, float)) else 0.0
    if result["outcome"] == "success":
        return 3000.0 + 10.0 * margin
    return -1000.0 + 100.0 * (float(result["steps"]) / max(max_steps, 1)) + 50.0 * margin


def _candidate_record(
    *,
    variant: str,
    selected: SelectedRow,
    arm: str,
    candidate: str,
    result: dict[str, Any],
    score: float,
) -> dict[str, Any]:
    backend = result["backend_info"]
    return {
        "variant": variant,
        "row_id": selected.row_id,
        "level": selected.level,
        "instance": selected.instance,
        "eval_seed": selected.eval_seed,
        "arm": arm,
        "candidate": candidate,
        "chrono_outcome": result["outcome"],
        "chrono_steps": result["steps"],
        "score": round(float(score), 6),
        "termination_reason": result["termination_reason"],
        "completion_reason": result["completion_reason"],
        "obstacle_visible_step": result["obstacle_visible_step"],
        "min_clearance_margin": result["min_clearance_margin"],
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


FIELDNAMES = list(_candidate_record(
    variant="",
    selected=SelectedRow("", "", 0, 0, "", (0.0, 0.0, 0.0), "", False),
    arm="",
    candidate="",
    result={
        "outcome": "",
        "steps": 0,
        "termination_reason": "",
        "completion_reason": "",
        "obstacle_visible_step": None,
        "min_clearance_margin": float("nan"),
        "reset_obs_finite": False,
        "variant_match": False,
        "backend_info": {},
        "trace_signature": "",
    },
    score=0.0,
).keys())


def _append_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        if new_file:
            writer.writeheader()
        writer.writerow({key: _jsonable(row.get(key, "")) for key in FIELDNAMES})


def _done_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    return {(str(row["variant"]), str(row["row_id"])) for row in _read_csv_rows(path) if row["arm"] == "native_oracle"}


def _run_native_oracle_search(
    client: ChronoWorkerClient,
    scenario: dict[str, Any],
    selected: SelectedRow,
    variant: str,
    prefix_policy: Callable[[int, np.ndarray], np.ndarray],
    budget: SearchBudget,
    rng: np.random.Generator,
    *,
    require_cem_attempt: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    max_steps = int(scenario["max_steps"]) + 5
    attempts: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None

    def consider(candidate: str, tail: Callable[[int], np.ndarray], segments: np.ndarray | None = None) -> None:
        nonlocal best
        result = run_chrono_episode(
            client,
            scenario,
            RevealSwitchPolicy(prefix_policy, tail),
            requested_variant=variant,
        )
        score = _score_result(result, max_steps)
        record = _candidate_record(
            variant=variant,
            selected=selected,
            arm="native_oracle_candidate",
            candidate=candidate,
            result=result,
            score=score,
        )
        if segments is not None:
            record["segments"] = np.round(segments, 6).tolist()
        attempts.append(record)
        if best is None or score > float(best["score"]):
            best = dict(record)

    for name, tail in structured_tail_candidates(limit=budget.structured_limit):
        consider(f"structured:{name}", tail)
        if best is not None and best["chrono_outcome"] == "success" and not require_cem_attempt:
            return best, attempts

    mean = np.tile(np.array([0.0, -1.0, 1.0], dtype=np.float32), (budget.cem_segments, 1))
    std = np.full_like(mean, 0.6)
    for iteration in range(budget.cem_iterations):
        samples = np.clip(
            rng.normal(mean[None], std[None], size=(budget.cem_population, budget.cem_segments, 3)),
            -1.0,
            1.0,
        )
        scored: list[tuple[float, int]] = []
        start_index = len(attempts)
        for idx, segments in enumerate(samples):
            consider(f"cem_iter{iteration}_sample{idx}", _segments_tail(segments, budget.cem_segment_len), segments)
            scored.append((float(attempts[start_index + idx]["score"]), idx))
            if best is not None and best["chrono_outcome"] == "success" and not require_cem_attempt:
                return best, attempts
        scored.sort(key=lambda item: (-item[0], item[1]))
        elite_idx = [idx for _score, idx in scored[: budget.cem_elites]]
        elite = samples[elite_idx]
        mean = elite.mean(axis=0)
        std = np.maximum(elite.std(axis=0), 0.15)

    if best is None:
        raise RuntimeError("native oracle search produced no attempts")
    return best, attempts


def _append_progress(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def _selected_for_mode(prereg: dict[str, Any], quick: bool) -> list[SelectedRow]:
    selected = [_as_selected(row) for row in prereg["selected_rows"]]
    if not quick:
        return selected
    return selected[:1]


def _summarize(rows: list[dict[str, str]], prereg: dict[str, Any], *, quick: bool) -> dict[str, Any]:
    variants = list(prereg["chrono_vehicle_variants"])
    per_vehicle: dict[str, Any] = {}
    for variant in variants:
        variant_rows = [row for row in rows if row["variant"] == variant and row["arm"] in ARMS]
        arm_rows = {arm: [row for row in variant_rows if row["arm"] == arm] for arm in ARMS}
        arm_success = {arm: sum(row["chrono_outcome"] == "success" for row in arm_rows[arm]) for arm in ARMS}
        arm_n = {arm: len(arm_rows[arm]) for arm in ARMS}
        oracle_rate = arm_success["native_oracle"] / max(arm_n["native_oracle"], 1)
        pertuned_rate = arm_success["v4_pertuned"] / max(arm_n["v4_pertuned"], 1)
        delta = oracle_rate - pertuned_rate
        if delta > 0.0:
            verdict = "direction_positive"
        elif delta < 0.0:
            verdict = "direction_reversed"
        else:
            verdict = "direction_neutral"
        candidate_rows = [row for row in rows if row["variant"] == variant and row["arm"] == "native_oracle_candidate"]
        structured_attempts = sum(row["candidate"].startswith("structured:") for row in candidate_rows)
        cem_attempts = sum(row["candidate"].startswith("cem_iter") for row in candidate_rows)
        per_vehicle[variant] = {
            "n_pricing_rows": arm_n["native_oracle"],
            "candidate_attempts": len(candidate_rows),
            "structured_candidate_attempts": structured_attempts,
            "cem_candidate_attempts": cem_attempts,
            "arm_success_counts": arm_success,
            "arm_n": arm_n,
            "success_rates_context_not_claims": {
                "v4_pertuned": round(pertuned_rate, 4),
                "native_oracle": round(oracle_rate, 4),
            },
            "direction_delta_native_oracle_minus_pertuned": round(delta, 4),
            "direction_verdict": "quick_smoke_no_verdict" if quick else verdict,
            "reset_obs_finite_all": all(row["reset_obs_finite"] == "True" for row in variant_rows + candidate_rows),
            "variant_match_all": all(row["variant_match"] == "True" for row in variant_rows + candidate_rows),
        }
    quick_gates = {
        "summary_written": True,
        "both_variants_exercised": all(per_vehicle[v]["n_pricing_rows"] >= 1 for v in variants),
        "structured_search_exercised": all(per_vehicle[v]["structured_candidate_attempts"] >= 1 for v in variants),
        "cem_search_exercised": all(per_vehicle[v]["cem_candidate_attempts"] >= 1 for v in variants),
        "reset_obs_finite_all": all(block["reset_obs_finite_all"] for block in per_vehicle.values()),
        "variant_match_all": all(block["variant_match_all"] for block in per_vehicle.values()),
    }
    quick_gates["all_passed"] = all(quick_gates.values())
    return {
        "protocol": "d1b_chrono_native_oracle_pricing",
        "generated_at_utc": utc_timestamp(),
        "quick_mode": quick,
        "claim_boundary": CLAIM_BOUNDARY,
        "backend_id": BACKEND_ID,
        "chrono_known_differences": list(KNOWN_DIFFERENCES),
        "preregistration_echo": {
            "file": str(PREREG_JSON),
            "decision_rule": prereg["decision_rule"],
            "selected_rows": prereg["selected_rows"],
            "unmapped_channel_handling": prereg["unmapped_channel_handling"],
        },
        "variants": variants,
        "arms": list(ARMS),
        "row_count": len(rows),
        "candidate_rows_csv": str(RUN_DIR / ("candidate_rows_quick.csv" if quick else "candidate_rows.csv")),
        "per_vehicle": per_vehicle,
        "quick_gates": quick_gates,
        "decision": {
            "d1b_direction_positive_all_variants": None if quick else all(
                block["direction_verdict"] == "direction_positive" for block in per_vehicle.values()
            ),
            "vehicle_verdicts": {variant: block["direction_verdict"] for variant, block in per_vehicle.items()},
            "absolute_numbers_are_claims": False,
            "interpretation": (
                "Quick mode is a protocol smoke only. Full mode reports D1b direction pricing; "
                "mixed, neutral, or reversed vehicles are accepted negative/mixed results."
            ),
        },
    }


def run_rollout(*, prereg: dict[str, Any], quick: bool, resume: bool) -> dict[str, Any]:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows_csv = RUN_DIR / ("candidate_rows_quick.csv" if quick else "candidate_rows.csv")
    progress_jsonl = RUN_DIR / ("progress_quick.jsonl" if quick else "progress.jsonl")
    results_json = QUICK_RESULTS_JSON if quick else RESULTS_JSON
    if not resume:
        for path in (rows_csv, progress_jsonl):
            if path.exists():
                path.unlink()
    selected_rows = _selected_for_mode(prereg, quick=quick)
    budget = QUICK_BUDGET if quick else FULL_BUDGET
    fixed_done = _done_keys(rows_csv) if resume else set()
    total = len(selected_rows) * len(prereg["chrono_vehicle_variants"])
    completed = len(fixed_done)
    t0 = time.time()
    client = ChronoWorkerClient(stderr_log=STDERR_LOG)
    try:
        for variant in prereg["chrono_vehicle_variants"]:
            if variant not in CHRONO_VEHICLE_VARIANTS:
                raise RuntimeError(f"unknown Chrono variant in prereg: {variant}")
            for selected in selected_rows:
                key = (variant, selected.row_id)
                if key in fixed_done:
                    continue
                scenario = _scenario_for(selected, variant)
                pertuned_policy = _fixed_grid_policy(selected.pertuned_grid)
                baseline = run_chrono_episode(client, scenario, pertuned_policy, requested_variant=variant)
                baseline_score = _score_result(baseline, int(scenario["max_steps"]) + 5)
                _append_row(
                    rows_csv,
                    _candidate_record(
                        variant=variant,
                        selected=selected,
                        arm="v4_pertuned",
                        candidate="v4_pertuned",
                        result=baseline,
                        score=baseline_score,
                    ),
                )
                variant_seed = int(hashlib.sha256(variant.encode("utf-8")).hexdigest()[:8], 16)
                rng = np.random.default_rng([SEED_BASE, int(selected.instance), int(selected.eval_seed), variant_seed])
                best, attempts = _run_native_oracle_search(
                    client,
                    scenario,
                    selected,
                    variant,
                    pertuned_policy,
                    budget,
                    rng,
                    require_cem_attempt=quick,
                )
                for attempt in attempts:
                    _append_row(rows_csv, attempt)
                best_record = dict(best)
                best_record["arm"] = "native_oracle"
                best_record["candidate"] = f"best:{best['candidate']}"
                _append_row(rows_csv, best_record)
                completed += 1
                _append_progress(
                    progress_jsonl,
                    {
                        "completed": completed,
                        "total": total,
                        "elapsed_s": round(time.time() - t0, 1),
                        "variant": variant,
                        "row_id": selected.row_id,
                        "baseline_outcome": baseline["outcome"],
                        "best_native_oracle_outcome": best["chrono_outcome"],
                        "candidate_attempts": len(attempts),
                    },
                )
                print(
                    f"[{completed}/{total}] {variant} {selected.row_id} baseline={baseline['outcome']} "
                    f"native_best={best['chrono_outcome']} attempts={len(attempts)}",
                    flush=True,
                )
    finally:
        client.close()

    rows = _read_csv_rows(rows_csv)
    summary = _summarize(rows, prereg, quick=quick)
    summary["budget"] = {
        "elapsed_s": round(time.time() - t0, 1),
        "selected_source_rows": len(selected_rows),
        "chrono_row_variant_pairs": total,
        "search_budget": budget.__dict__,
    }
    summary["progress_jsonl"] = str(progress_jsonl)
    _write_json(results_json, summary)
    if quick and not summary["quick_gates"]["all_passed"]:
        raise RuntimeError(f"D1b quick gates failed: {summary['quick_gates']}")
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
    if args.quick and args.full:
        raise SystemExit("--quick and --full are mutually exclusive")
    if args.write_prereg:
        payload = write_preregistration()
        print(json.dumps({"wrote": str(PREREG_JSON), "selected_rows": len(payload["selected_rows"])}, sort_keys=True))
    if args.quick or args.full:
        prereg = load_preregistration()
        summary = run_rollout(prereg=prereg, quick=bool(args.quick), resume=bool(args.resume))
        print(json.dumps(summary["decision"], sort_keys=True))
    if not (args.write_prereg or args.quick or args.full):
        parser.error("choose --write-prereg, --quick, or --full")


if __name__ == "__main__":
    main()
