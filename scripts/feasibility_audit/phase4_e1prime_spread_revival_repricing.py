"""Phase-4 E1' oracle-adequate Chrono spread-revival repricing.

M3259 is the E1' oracle-adequate repricing milestone after M3250 exposed an
underpowered native-oracle anchor. The native oracle candidate set includes
the same-instance tuned reflex floor, so the oracle-adequacy gate proves the
anchor no longer underperforms the floor before any validation verdict is read.
It keeps the E0 expressibility envelope frozen, splits A3 source rows into
disjoint same-instance selection/validation pairs, selects fixed* and
per-instance tuned reflex grids only on selection rows, and reports paired
validation readouts in Chrono.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e1prime_spread_revival_repricing.py --write-prereg
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e1prime_spread_revival_repricing.py --quick --resume
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e1prime_spread_revival_repricing.py --full --resume
"""

from __future__ import annotations

import argparse
import ast
import copy
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

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json  # noqa: E402
import c5_reflex_degradation as c5  # noqa: E402
import chrono_native_oracle_pricing as d1b  # noqa: E402
import phase4_e1_spread_revival_pricing as e1_smoke  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402


MILESTONE_ID = "m3259-phase4-e1prime-spread-revival-repricing"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1prime_spread_revival_repricing_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1prime_spread_revival_repricing_quick.json"
RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1prime_spread_revival_repricing.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e1prime_spread_revival_repricing"
ROWS_QUICK_CSV = RUN_DIR / "episode_rows_quick.csv"
ROWS_FULL_CSV = RUN_DIR / "episode_rows_full.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
METRICS_FULL_CSV = RUN_DIR / "metrics_full.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
STDERR_QUICK_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
DOC_PATH = REPO_ROOT / "docs" / "m3259-phase4-e1prime-spread-revival-repricing.md"

E0_JSON = e1_smoke.E0_JSON
SOURCE_ROWS_CSV = e1_smoke.SOURCE_ROWS_CSV
SOURCE_RESULTS_JSON = e1_smoke.SOURCE_RESULTS_JSON

SEED_BASE = 2026061313
TARGET_LEVELS = ("S1", "S2", "S3")
SURFACE = "T_limit"
MIN_VALIDATION_UNITS_PER_VARIANT = 20
QUICK_PAIRS_PER_LEVEL = 1
FULL_GRID_VALUES = (
    (1.0, 1.0, 1.0),
    (0.6, 1.0, 1.0),
    (1.8, 1.0, 1.0),
    (1.8, 1.45, 1.4),
    (0.6, 1.45, 1.4),
)
FULL_ORACLE_BUDGET = d1b.SearchBudget(
    structured_limit=15,
    cem_segments=6,
    cem_segment_len=8,
    cem_population=8,
    cem_elites=2,
    cem_iterations=3,
)
QUICK_ORACLE_BUDGET = d1b.SearchBudget(
    structured_limit=3,
    cem_segments=3,
    cem_segment_len=8,
    cem_population=2,
    cem_elites=1,
    cem_iterations=1,
)
ARMS = ("fixed_star", "v4_rls", "v4_pertuned", "native_oracle")
CHRONO_RESTART_EVERY_EPISODES = 24

CLAIM_BOUNDARY = (
    "Phase-4 E1' oracle-adequate Chrono spread-revival repricing only: "
    "fixed*, RLS-retuned, same-instance selection-tuned reflex, and native "
    "Chrono oracle arms are compared on the E0-frozen Sedan/BMW_E90/UAZBUS "
    "fixture envelope after an oracle-adequacy gate verifies that the native "
    "oracle anchor no longer underperforms v4_pertuned on selection rows. "
    "This is zero-training pricing evidence; it makes no incumbent mutation, "
    "validation ranking, promotion, driver-performance, full high-fidelity "
    "sufficiency, paper, repair-success, robustness-result, feasibility-proof, "
    "or self-ID claim."
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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _stable_hash(payload: Any) -> str:
    text = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _score_key(*parts: Any) -> str:
    text = ":".join(str(part) for part in (SEED_BASE, *parts))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _row_id(row: dict[str, str]) -> str:
    return f"{row['level']}-inst{int(row['instance']):02d}-seed{int(row['eval_seed'])}"


def _source_to_selected(row: dict[str, str], *, rank: int, role: str) -> dict[str, Any]:
    return {
        "row_id": _row_id(row),
        "level": row["level"],
        "instance": int(row["instance"]),
        "eval_seed": int(row["eval_seed"]),
        "selection_rank_within_level": int(rank),
        "row_role": role,
        "selection_score_sha256": _score_key(role, row["level"], row["instance"], row["eval_seed"]),
        "oracle_by": row["oracle_by"],
        "pertuned_grid": list(ast.literal_eval(row["pertuned_grid"])),
        "source_pertuned_outcome": row["v4_pertuned_outcome"],
        "source_oracle_solved": row["oracle_solved"] == "True",
    }


def _eligible_source_rows() -> list[dict[str, str]]:
    rows = d1b._eligible_source_rows()
    return [row for row in rows if row.get("level") in TARGET_LEVELS and row.get("surface") == SURFACE]


def select_full_row_pairs(*, quick: bool = False) -> list[dict[str, Any]]:
    eligible = _eligible_source_rows()
    by_instance: dict[tuple[str, int], list[dict[str, str]]] = {}
    for row in eligible:
        by_instance.setdefault((row["level"], int(row["instance"])), []).append(row)

    pairs: list[dict[str, Any]] = []
    for level in TARGET_LEVELS:
        instances = [
            (instance, rows)
            for (row_level, instance), rows in by_instance.items()
            if row_level == level and len(rows) >= 2
        ]
        instances.sort(key=lambda item: (_score_key("instance", level, item[0]), item[0]))
        keep = instances[:QUICK_PAIRS_PER_LEVEL] if quick else instances
        if not keep:
            raise RuntimeError(f"{level} has no same-instance row groups")
        for rank, (instance, rows) in enumerate(keep, start=1):
            rows.sort(key=lambda row: (_score_key("row", level, instance, row["eval_seed"]), int(row["eval_seed"])))
            selection = _source_to_selected(rows[0], rank=rank, role="selection")
            validation = _source_to_selected(rows[1], rank=rank, role="validation")
            if selection["row_id"] == validation["row_id"]:
                raise RuntimeError(f"selection/validation collision for {level} instance {instance}")
            pairs.append(
                {
                    "pair_id": f"{level}-inst{instance:02d}-pair{rank}",
                    "level": level,
                    "instance": int(instance),
                    "selection_row": selection,
                    "validation_row": validation,
                }
            )
    if not quick and len(pairs) < MIN_VALIDATION_UNITS_PER_VARIANT:
        raise RuntimeError(
            f"E1' needs >= {MIN_VALIDATION_UNITS_PER_VARIANT} validation units per variant; got {len(pairs)}"
        )
    return pairs


def build_preregistration() -> dict[str, Any]:
    e0 = e1_smoke.load_e0_envelope()
    variants = list(e0["e1_spread_envelope"]["recommended_e1_population_panel"]["vehicle_variants"])
    pairs = select_full_row_pairs()
    eligible = _eligible_source_rows()
    eligible_counts = {level: sum(1 for row in eligible if row["level"] == level) for level in TARGET_LEVELS}
    same_instance_counts = {
        level: len({int(row["instance"]) for row in eligible if row["level"] == level})
        for level in TARGET_LEVELS
    }
    quick_pairs = select_full_row_pairs(quick=True)
    return {
        "protocol": "phase4_e1prime_spread_revival_repricing_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 E1' oracle-adequate spread-revival repricing",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_e1prime_run": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "e0_artifact": str(E0_JSON.relative_to(REPO_ROOT)),
        "e0_axis_table_sha256": e0["axis_table_sha256"],
        "e0_decision": e0["decision"],
        "e0_allowed_envelope": e0["e1_spread_envelope"],
        "source_artifacts": {
            "a3_results_json": str(SOURCE_RESULTS_JSON.relative_to(REPO_ROOT)),
            "a3_episode_rows_csv": str(SOURCE_ROWS_CSV.relative_to(REPO_ROOT)),
            "m3249_quick_json": "experiments/feasibility_audit/phase4_e1_spread_revival_quick.json",
            "m3250_full_json": "experiments/feasibility_audit/phase4_e1_spread_revival_full.json",
        },
        "source_row_filter": {
            "levels": list(TARGET_LEVELS),
            "surface": SURFACE,
            "oracle_solved": True,
            "pertuned_outcome": "not success",
            "oracle_by_prefix": "structured:",
            "eligible_counts_by_level": eligible_counts,
            "same_instance_counts_by_level": same_instance_counts,
            "selection_rule": (
                "within each S1/S2/S3 level, keep same-instance eligible groups with at least "
                "two rows, sort instances by a frozen sha256 seed, keep every such group, then use "
                "the first frozen row for Chrono grid selection and the second for validation"
            ),
        },
        "row_pairs": pairs,
        "quick_row_pairs": quick_pairs,
        "chrono_vehicle_variants": variants,
        "min_validation_units_per_variant": MIN_VALIDATION_UNITS_PER_VARIANT,
        "validation_units_per_variant": len(pairs),
        "full_grid_values": [list(grid) for grid in FULL_GRID_VALUES],
        "full_oracle_budget": FULL_ORACLE_BUDGET.__dict__,
        "quick_oracle_budget": QUICK_ORACLE_BUDGET.__dict__,
        "oracle_floor_candidate": "floor:v4_pertuned_full_episode",
        "arms": {
            "fixed_star": "one global Chrono grid chosen only from selection rows, pooled across variants and pairs",
            "v4_rls": "C5 kappa-RLS retuning map applied to the global fixed_star grid on validation rows",
            "v4_pertuned": "per variant/pair Chrono grid chosen only from the same-instance selection row",
            "native_oracle": "max over the v4_pertuned full-episode floor plus reveal-constrained structured + CEM search",
        },
        "blocked_by_e0_without_new_connector": [
            row["axis"] for row in e0["e1_spread_envelope"]["blocked_without_new_connector"]
        ],
        "runtime_gates": [
            "E0 artifact admits E1",
            "M3249 quick protocol smoke and M3250 full artifact exist before M3259",
            "selection and validation row_ids are disjoint",
            "full panel uses >=20 validation units per Chrono variant",
            "oracle-adequacy rows exist on selection rows before validation verdict readout",
            "selection native_oracle never underperforms selection v4_pertuned by success outcome",
            "all requested Chrono variants match backend_info",
            "all reset observations are finite obs72",
            "each validation pair has fixed_star, v4_rls, v4_pertuned, and native_oracle rows",
            "the full result reports paired CIs for pertuned-fixed, pertuned-RLS, and native-pertuned",
        ],
        "preregistered_readouts": {
            "oracle_adequacy_gate": (
                "on selection rows, success_rate(native_oracle) - success_rate(v4_pertuned) "
                "must be >= 0 for every Chrono variant before the validation spread verdict is interpreted"
            ),
            "primary_per_variant": "success_rate(v4_pertuned) - success_rate(fixed_star), paired on validation pairs",
            "classical_residual_per_variant": "success_rate(v4_pertuned) - success_rate(v4_rls), paired on validation pairs",
            "oracle_anchor_per_variant": "success_rate(native_oracle) - success_rate(v4_pertuned), paired on validation pairs",
            "pooled_readouts": "same readouts pooled across all validation variant/pair units",
            "positive_rule": (
                "E1 spread revival positive iff at least two of three Chrono variants have "
                "primary >= 0.15 with paired CI95 lower > 0 and classical residual >= 0.08. "
                "Otherwise the spread-revival thesis is not supported by this frozen full rule."
            ),
        },
        "decision_rule": (
            "M3259 is completed when quick smoke and full E1' run under this preregistration, "
            "the oracle-adequacy gate passes on selection rows, the full panel writes >=20 validation "
            "units per variant with JSON/CSV/doc artifacts, reports paired CIs, and applies the >=2 "
            "qualifying variants rule without admitting any training or driver-performance claim."
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
    if not payload.get("frozen_before_any_e1prime_run"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_e1prime_run")
    return payload


def _record(
    *,
    role: str,
    pair_id: str,
    variant: str,
    selected: d1b.SelectedRow,
    arm: str,
    candidate: str,
    grid: tuple[float, float, float] | None,
    result: dict[str, Any],
    score: float,
    selection_row_id: str = "",
    pertuned_grid_source: str = "",
) -> dict[str, Any]:
    backend = result.get("backend_info", {})
    return {
        "role": role,
        "pair_id": pair_id,
        "variant": variant,
        "row_id": selected.row_id,
        "level": selected.level,
        "instance": selected.instance,
        "eval_seed": selected.eval_seed,
        "selection_row_id": selection_row_id,
        "arm": arm,
        "candidate": candidate,
        "grid": "" if grid is None else str(tuple(float(x) for x in grid)),
        "pertuned_grid_source": pertuned_grid_source,
        "chrono_outcome": result["outcome"],
        "chrono_steps": int(result["steps"]),
        "score": round(float(score), 6),
        "termination_reason": result.get("termination_reason", ""),
        "completion_reason": result.get("completion_reason", ""),
        "obstacle_visible_step": result.get("obstacle_visible_step", ""),
        "min_clearance_margin": result.get("min_clearance_margin", ""),
        "reset_obs_finite": bool(result["reset_obs_finite"]),
        "variant_match": bool(result["variant_match"]),
        "backend_model": backend.get("chrono_vehicle_model", ""),
        "backend_tire": backend.get("chrono_tire_model", ""),
        "target_mass": backend.get("target_mass", ""),
        "vehicle_total_mass": backend.get("vehicle_total_mass", ""),
        "wheelbase_m": backend.get("chrono_wheelbase_m", ""),
        "wheeltrack_m": json.dumps(_jsonable(backend.get("chrono_wheeltrack_m")), sort_keys=True),
        "trace_signature": result.get("trace_signature", ""),
        "claim_boundary": CLAIM_BOUNDARY,
        "segments": "",
        "rls_info": "",
    }


FIELDNAMES = list(
    _record(
        role="",
        pair_id="",
        variant="",
        selected=d1b.SelectedRow("", "", 0, 0, "", (0.0, 0.0, 0.0), "", False),
        arm="",
        candidate="",
        grid=None,
        result={
            "outcome": "",
            "steps": 0,
            "reset_obs_finite": False,
            "variant_match": False,
            "backend_info": {},
            "trace_signature": "",
        },
        score=0.0,
    ).keys()
)


def _append_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        if new_file:
            writer.writeheader()
        writer.writerow({key: _jsonable(row.get(key, "")) for key in FIELDNAMES})


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _jsonable(row.get(key, "")) for key in FIELDNAMES})


def _append_progress(payload: dict[str, Any]) -> None:
    PROGRESS_FULL_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_FULL_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def _append_progress_to(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


class RestartingChronoRunner:
    def __init__(self, *, stderr_log: Path, restart_every: int = CHRONO_RESTART_EVERY_EPISODES):
        self.stderr_log = stderr_log
        self.restart_every = max(1, int(restart_every))
        self.count = 0
        self.client: ChronoWorkerClient | None = None

    def _ensure(self) -> ChronoWorkerClient:
        if self.client is None:
            self.client = ChronoWorkerClient(stderr_log=self.stderr_log)
            self.count = 0
        return self.client

    def restart(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def run(
        self,
        scenario: dict[str, Any],
        policy: Callable[[int, np.ndarray], np.ndarray],
        *,
        requested_variant: str,
    ) -> dict[str, Any]:
        if self.count >= self.restart_every:
            self.restart()
        try:
            result = d1b.run_chrono_episode(
                self._ensure(),
                scenario,
                policy,
                requested_variant=requested_variant,
            )
        except Exception as exc:
            self.restart()
            result = d1b.run_chrono_episode(
                self._ensure(),
                scenario,
                policy,
                requested_variant=requested_variant,
            )
            result["restart_after_error"] = f"{type(exc).__name__}: {exc}"
        self.count += 1
        return result

    def close(self) -> None:
        self.restart()


def _grid_tuple(value: Any) -> tuple[float, float, float]:
    if isinstance(value, tuple):
        vals = value
    elif isinstance(value, list):
        vals = tuple(value)
    else:
        vals = ast.literal_eval(str(value))
    grid = tuple(float(x) for x in vals)
    if len(grid) != 3:
        raise ValueError(f"bad grid: {value!r}")
    return grid


def _boolish(value: Any) -> bool:
    return value is True or str(value) == "True"


def _selection_complete(rows: list[dict[str, Any]], prereg: dict[str, Any]) -> bool:
    grids = {_grid_tuple(grid) for grid in prereg["full_grid_values"]}
    expected = {
        (variant, pair["pair_id"], pair["selection_row"]["row_id"], grid)
        for variant in prereg["chrono_vehicle_variants"]
        for pair in prereg["row_pairs"]
        for grid in grids
    }
    found = {
        (row["variant"], row["pair_id"], row["row_id"], _grid_tuple(row["grid"]))
        for row in rows
        if row.get("role") == "selection" and row.get("arm") == "fixed_star_selection_candidate"
    }
    return expected.issubset(found)


def _selection_done_keys(rows: list[dict[str, Any]], prereg: dict[str, Any]) -> set[tuple[str, str]]:
    grids = {_grid_tuple(grid) for grid in prereg["full_grid_values"]}
    found_by_pair: dict[tuple[str, str], set[tuple[str, str, tuple[float, float, float]]]] = {}
    selection_row_by_pair = {
        pair["pair_id"]: str(pair["selection_row"]["row_id"])
        for pair in prereg["row_pairs"]
    }
    for row in rows:
        if row.get("role") != "selection" or row.get("arm") != "fixed_star_selection_candidate":
            continue
        pair_id = str(row["pair_id"])
        key = (str(row["variant"]), pair_id)
        found_by_pair.setdefault(key, set()).add((pair_id, str(row["row_id"]), _grid_tuple(row["grid"])))
    done: set[tuple[str, str]] = set()
    for variant in prereg["chrono_vehicle_variants"]:
        for pair in prereg["row_pairs"]:
            pair_id = str(pair["pair_id"])
            row_id = selection_row_by_pair[pair_id]
            expected = {(pair_id, row_id, grid) for grid in grids}
            key = (str(variant), pair_id)
            if expected.issubset(found_by_pair.get(key, set())):
                done.add(key)
    return done


def _validation_done_keys(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {
        (row["variant"], row["pair_id"])
        for row in rows
        if row.get("role") == "validation" and row.get("arm") == "native_oracle"
    }


def _adequacy_done_keys(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {
        (row["variant"], row["pair_id"])
        for row in rows
        if row.get("role") == "oracle_adequacy" and row.get("arm") == "native_oracle"
    }


def _drop_partial_role_pair(path: Path, *, role: str, variant: str, pair_id: str) -> None:
    rows = _read_csv_rows(path)
    kept = [
        row
        for row in rows
        if not (row.get("role") == role and row.get("variant") == variant and row.get("pair_id") == pair_id)
    ]
    if len(kept) != len(rows):
        _write_rows(path, kept)


def _drop_partial_validation_pair(path: Path, *, variant: str, pair_id: str) -> None:
    _drop_partial_role_pair(path, role="validation", variant=variant, pair_id=pair_id)


def choose_grids_from_selection(
    rows: list[dict[str, Any]],
    prereg: dict[str, Any],
) -> tuple[tuple[float, float, float], dict[tuple[str, str], tuple[float, float, float]], dict[str, Any]]:
    grids = [_grid_tuple(grid) for grid in prereg["full_grid_values"]]
    variants = list(prereg["chrono_vehicle_variants"])
    pair_ids = [pair["pair_id"] for pair in prereg["row_pairs"]]

    score_by_key: dict[tuple[str, str, tuple[float, float, float]], float] = {}
    for row in rows:
        if row.get("role") != "selection" or row.get("arm") != "fixed_star_selection_candidate":
            continue
        score_by_key[(str(row["variant"]), str(row["pair_id"]), _grid_tuple(row["grid"]))] = float(row["score"])

    missing = [
        (variant, pair_id, grid)
        for variant in variants
        for pair_id in pair_ids
        for grid in grids
        if (variant, pair_id, grid) not in score_by_key
    ]
    if missing:
        raise RuntimeError(f"selection grid rows incomplete, first missing={missing[0]!r}")

    def grid_distance(grid: tuple[float, float, float]) -> float:
        return float(sum(abs(value - 1.0) for value in grid))

    global_scores = {
        grid: sum(score_by_key[(variant, pair_id, grid)] for variant in variants for pair_id in pair_ids)
        for grid in grids
    }
    fixed_grid = max(grids, key=lambda grid: (global_scores[grid], -grid_distance(grid), -grids.index(grid)))
    pertuned_by_pair = {
        (variant, pair_id): max(
            grids,
            key=lambda grid: (score_by_key[(variant, pair_id, grid)], -grid_distance(grid), -grids.index(grid)),
        )
        for variant in variants
        for pair_id in pair_ids
    }
    return fixed_grid, pertuned_by_pair, {
        "global_scores": {str(tuple(grid)): round(score, 6) for grid, score in global_scores.items()},
        "pertuned_by_variant_pair": {
            f"{variant}/{pair_id}": list(grid)
            for (variant, pair_id), grid in pertuned_by_pair.items()
        },
    }


def _candidate_to_full_row(
    attempt: dict[str, Any],
    *,
    pair: dict[str, Any],
    selected: d1b.SelectedRow,
    selection_row_id: str,
    role: str = "validation",
) -> dict[str, Any]:
    row = {key: attempt.get(key, "") for key in FIELDNAMES}
    row.update(
        {
            "role": role,
            "pair_id": pair["pair_id"],
            "row_id": selected.row_id,
            "selection_row_id": selection_row_id,
            "claim_boundary": CLAIM_BOUNDARY,
            "grid": "",
            "pertuned_grid_source": "native_oracle_attempt",
        }
    )
    if "segments" in attempt:
        row["segments"] = json.dumps(_jsonable(attempt["segments"]), sort_keys=True)
    return row


def _native_oracle_with_floor(
    client: ChronoWorkerClient,
    scenario: dict[str, Any],
    selected: d1b.SelectedRow,
    variant: str,
    pertuned_policy,
    pertuned_result: dict[str, Any],
    pertuned_score: float,
    budget: d1b.SearchBudget,
    rng: np.random.Generator,
    *,
    force_search: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    floor = d1b._candidate_record(
        variant=variant,
        selected=selected,
        arm="native_oracle_candidate",
        candidate="floor:v4_pertuned_full_episode",
        result=pertuned_result,
        score=pertuned_score,
    )
    attempts = [floor]
    best = dict(floor)
    if pertuned_result["outcome"] != "success" or force_search:
        searched_best, searched_attempts = d1b._run_native_oracle_search(
            client,
            scenario,
            selected,
            variant,
            pertuned_policy,
            budget,
            rng,
            require_cem_attempt=force_search,
        )
        attempts.extend(searched_attempts)
        if float(searched_best["score"]) > float(best["score"]):
            best = dict(searched_best)
    return best, attempts


def _native_oracle_with_floor_retrying(
    runner: RestartingChronoRunner,
    scenario: dict[str, Any],
    selected: d1b.SelectedRow,
    variant: str,
    pertuned_policy,
    pertuned_result: dict[str, Any],
    pertuned_score: float,
    budget: d1b.SearchBudget,
    rng: np.random.Generator,
    *,
    force_search: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rng_state = copy.deepcopy(rng.bit_generator.state)
    try:
        best, attempts = _native_oracle_with_floor(
            runner._ensure(),
            scenario,
            selected,
            variant,
            pertuned_policy,
            pertuned_result,
            pertuned_score,
            budget,
            rng,
            force_search=force_search,
        )
    except Exception as exc:
        runner.restart()
        rng.bit_generator.state = rng_state
        best, attempts = _native_oracle_with_floor(
            runner._ensure(),
            scenario,
            selected,
            variant,
            pertuned_policy,
            pertuned_result,
            pertuned_score,
            budget,
            rng,
            force_search=force_search,
        )
        best["restart_after_error"] = f"{type(exc).__name__}: {exc}"
    runner.count += max(0, len(attempts) - 1)
    return best, attempts


def _run_selection_if_needed(
    prereg: dict[str, Any],
    *,
    resume: bool,
    rows_csv: Path = ROWS_FULL_CSV,
    progress_jsonl: Path = PROGRESS_FULL_JSONL,
    stderr_log: Path = STDERR_LOG,
) -> None:
    rows = _read_csv_rows(rows_csv)
    if resume and rows and _selection_complete(rows, prereg):
        return
    done = _selection_done_keys(rows, prereg) if resume else set()
    if rows:
        if resume:
            pass
        else:
            return

    if done and len(done) == len(prereg["chrono_vehicle_variants"]) * len(prereg["row_pairs"]):
        return

    grids = [_grid_tuple(grid) for grid in prereg["full_grid_values"]]
    t0 = time.time()
    total = len(prereg["chrono_vehicle_variants"]) * len(prereg["row_pairs"])
    completed = len(done)
    for variant in prereg["chrono_vehicle_variants"]:
        runner = RestartingChronoRunner(stderr_log=stderr_log)
        try:
            for pair in prereg["row_pairs"]:
                key = (variant, pair["pair_id"])
                if key in done:
                    continue
                _drop_partial_role_pair(rows_csv, role="selection", variant=variant, pair_id=pair["pair_id"])
                selected = d1b._as_selected(pair["selection_row"])
                scenario = d1b._scenario_for(selected, variant)
                pair_rows = []
                for grid in grids:
                    result = runner.run(
                        scenario,
                        d1b._fixed_grid_policy(grid),
                        requested_variant=variant,
                    )
                    score = d1b._score_result(result, int(scenario["max_steps"]) + 5)
                    pair_rows.append(
                        _record(
                            role="selection",
                            pair_id=pair["pair_id"],
                            variant=variant,
                            selected=selected,
                            arm="fixed_star_selection_candidate",
                            candidate="full_grid_selection",
                            grid=grid,
                            result=result,
                            score=score,
                        ),
                    )
                for row in pair_rows:
                    _append_row(rows_csv, row)
                completed += 1
                _append_progress_to(
                    progress_jsonl,
                    {
                        "stage": "selection_pair_done",
                        "completed": completed,
                        "total": total,
                        "variant": variant,
                        "pair_id": pair["pair_id"],
                        "elapsed_s": round(time.time() - t0, 1),
                    }
                )
        finally:
            runner.close()


def _run_oracle_adequacy_if_needed(
    prereg: dict[str, Any],
    *,
    pertuned_by_pair: dict[tuple[str, str], tuple[float, float, float]],
    resume: bool,
    rows_csv: Path = ROWS_FULL_CSV,
    progress_jsonl: Path = PROGRESS_FULL_JSONL,
    stderr_log: Path = STDERR_LOG,
    force_search: bool = False,
    budget: d1b.SearchBudget = FULL_ORACLE_BUDGET,
) -> None:
    rows = _read_csv_rows(rows_csv)
    done = _adequacy_done_keys(rows) if resume else set()
    total = len(prereg["chrono_vehicle_variants"]) * len(prereg["row_pairs"])
    completed = len(done)
    t0 = time.time()
    for variant in prereg["chrono_vehicle_variants"]:
        for pair in prereg["row_pairs"]:
            key = (variant, pair["pair_id"])
            if key in done:
                continue
            _drop_partial_role_pair(rows_csv, role="oracle_adequacy", variant=variant, pair_id=pair["pair_id"])
            selected = d1b._as_selected(pair["selection_row"])
            scenario = d1b._scenario_for(selected, variant)
            pertuned_grid = pertuned_by_pair[(variant, pair["pair_id"])]
            pertuned_policy = d1b._fixed_grid_policy(pertuned_grid)
            runner = RestartingChronoRunner(stderr_log=stderr_log)
            try:
                pertuned_result = runner.run(
                    scenario,
                    pertuned_policy,
                    requested_variant=variant,
                )
                pertuned_score = d1b._score_result(pertuned_result, int(scenario["max_steps"]) + 5)
                _append_row(
                    rows_csv,
                    _record(
                        role="oracle_adequacy",
                        pair_id=pair["pair_id"],
                        variant=variant,
                        selected=selected,
                        arm="v4_pertuned",
                        candidate="selection_same_instance_grid",
                        grid=pertuned_grid,
                        result=pertuned_result,
                        score=pertuned_score,
                        selection_row_id=selected.row_id,
                        pertuned_grid_source="same_instance_selection_row",
                    ),
                )
                variant_seed = int(hashlib.sha256(variant.encode("utf-8")).hexdigest()[:8], 16)
                rng = np.random.default_rng([SEED_BASE, 17, int(selected.instance), int(selected.eval_seed), variant_seed])
                best, attempts = _native_oracle_with_floor_retrying(
                    runner,
                    scenario,
                    selected,
                    variant,
                    pertuned_policy,
                    pertuned_result,
                    pertuned_score,
                    budget,
                    rng,
                    force_search=force_search,
                )
                for attempt in attempts:
                    _append_row(
                        rows_csv,
                        _candidate_to_full_row(
                            attempt,
                            pair=pair,
                            selected=selected,
                            selection_row_id=selected.row_id,
                            role="oracle_adequacy",
                        ),
                    )
                best_row = _candidate_to_full_row(
                    best,
                    pair=pair,
                    selected=selected,
                    selection_row_id=selected.row_id,
                    role="oracle_adequacy",
                )
                best_row["arm"] = "native_oracle"
                best_row["candidate"] = "best:" + str(best.get("candidate", ""))
                _append_row(rows_csv, best_row)
                completed += 1
                _append_progress_to(
                    progress_jsonl,
                    {
                        "stage": "oracle_adequacy_pair_done",
                        "completed": completed,
                        "total": total,
                        "variant": variant,
                        "pair_id": pair["pair_id"],
                        "v4_pertuned": pertuned_result["outcome"],
                        "native_oracle": best["chrono_outcome"],
                        "candidate_attempts": len(attempts),
                        "elapsed_s": round(time.time() - t0, 1),
                    },
                )
            finally:
                runner.close()


def _run_validation_if_needed(
    prereg: dict[str, Any],
    *,
    fixed_grid: tuple[float, float, float],
    pertuned_by_pair: dict[tuple[str, str], tuple[float, float, float]],
    resume: bool,
    rows_csv: Path = ROWS_FULL_CSV,
    progress_jsonl: Path = PROGRESS_FULL_JSONL,
    stderr_log: Path = STDERR_LOG,
    budget: d1b.SearchBudget = FULL_ORACLE_BUDGET,
    force_search: bool = False,
) -> None:
    rows = _read_csv_rows(rows_csv)
    done = _validation_done_keys(rows) if resume else set()
    total = len(prereg["chrono_vehicle_variants"]) * len(prereg["row_pairs"])
    completed = len(done)
    t0 = time.time()
    for variant in prereg["chrono_vehicle_variants"]:
        for pair in prereg["row_pairs"]:
            key = (variant, pair["pair_id"])
            if key in done:
                continue
            _drop_partial_validation_pair(rows_csv, variant=variant, pair_id=pair["pair_id"])
            selected = d1b._as_selected(pair["validation_row"])
            selection_row_id = str(pair["selection_row"]["row_id"])
            scenario = d1b._scenario_for(selected, variant)
            pertuned_grid = pertuned_by_pair[(variant, pair["pair_id"])]
            runner = RestartingChronoRunner(stderr_log=stderr_log)
            try:
                fixed_result = runner.run(
                    scenario,
                    d1b._fixed_grid_policy(fixed_grid),
                    requested_variant=variant,
                )
                fixed_score = d1b._score_result(fixed_result, int(scenario["max_steps"]) + 5)
                _append_row(
                    rows_csv,
                    _record(
                        role="validation",
                        pair_id=pair["pair_id"],
                        variant=variant,
                        selected=selected,
                        arm="fixed_star",
                        candidate="full_global_selection_grid",
                        grid=fixed_grid,
                        result=fixed_result,
                        score=fixed_score,
                        selection_row_id=selection_row_id,
                        pertuned_grid_source="global_selection_rows",
                    ),
                )

                rls_policy, rls_info = e1_smoke._rls_policy(selected, fixed_grid)
                rls_result = runner.run(scenario, rls_policy, requested_variant=variant)
                rls_score = d1b._score_result(rls_result, int(scenario["max_steps"]) + 5)
                rls_row = _record(
                    role="validation",
                    pair_id=pair["pair_id"],
                    variant=variant,
                    selected=selected,
                    arm="v4_rls",
                    candidate="full_c5_rls_map",
                    grid=fixed_grid,
                    result=rls_result,
                    score=rls_score,
                    selection_row_id=selection_row_id,
                    pertuned_grid_source="global_selection_rows",
                )
                rls_row["rls_info"] = json.dumps(_jsonable(rls_info), sort_keys=True)
                _append_row(rows_csv, rls_row)

                pertuned_policy = d1b._fixed_grid_policy(pertuned_grid)
                pertuned_result = runner.run(scenario, pertuned_policy, requested_variant=variant)
                pertuned_score = d1b._score_result(pertuned_result, int(scenario["max_steps"]) + 5)
                _append_row(
                    rows_csv,
                    _record(
                        role="validation",
                        pair_id=pair["pair_id"],
                        variant=variant,
                        selected=selected,
                        arm="v4_pertuned",
                        candidate="full_same_instance_selection_grid",
                        grid=pertuned_grid,
                        result=pertuned_result,
                        score=pertuned_score,
                        selection_row_id=selection_row_id,
                        pertuned_grid_source="same_instance_selection_row",
                    ),
                )

                variant_seed = int(hashlib.sha256(variant.encode("utf-8")).hexdigest()[:8], 16)
                rng = np.random.default_rng([SEED_BASE, 23, int(selected.instance), int(selected.eval_seed), variant_seed])
                best, attempts = _native_oracle_with_floor_retrying(
                    runner,
                    scenario,
                    selected,
                    variant,
                    pertuned_policy,
                    pertuned_result,
                    pertuned_score,
                    budget,
                    rng,
                    force_search=force_search,
                )
                for attempt in attempts:
                    _append_row(
                        rows_csv,
                        _candidate_to_full_row(
                            attempt,
                            pair=pair,
                            selected=selected,
                            selection_row_id=selection_row_id,
                        ),
                    )
                best_row = _candidate_to_full_row(
                    best,
                    pair=pair,
                    selected=selected,
                    selection_row_id=selection_row_id,
                )
                best_row["arm"] = "native_oracle"
                best_row["candidate"] = "best:" + str(best.get("candidate", ""))
                _append_row(rows_csv, best_row)
                completed += 1
                _append_progress_to(
                    progress_jsonl,
                    {
                        "stage": "validation_pair_done",
                        "completed": completed,
                        "total": total,
                        "variant": variant,
                        "pair_id": pair["pair_id"],
                        "fixed_star": fixed_result["outcome"],
                        "v4_rls": rls_result["outcome"],
                        "v4_pertuned": pertuned_result["outcome"],
                        "native_oracle": best["chrono_outcome"],
                        "candidate_attempts": len(attempts),
                        "elapsed_s": round(time.time() - t0, 1),
                    },
                )
                print(
                    f"[{completed}/{total}] {variant} {pair['pair_id']} "
                    f"fixed={fixed_result['outcome']} rls={rls_result['outcome']} "
                    f"pertuned={pertuned_result['outcome']} native={best['chrono_outcome']} "
                    f"attempts={len(attempts)}",
                    flush=True,
                )
            finally:
                runner.close()


def run_full(*, resume: bool) -> dict[str, Any]:
    prereg = load_preregistration()
    required = [
        REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1_spread_revival_quick.json",
        REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1_spread_revival_full.json",
        QUICK_JSON,
    ]
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M3259 full requires prior artifacts: {missing}")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not resume:
        for path in (ROWS_FULL_CSV, METRICS_FULL_CSV, PROGRESS_FULL_JSONL, RESULTS_JSON):
            if path.exists():
                path.unlink()

    t0 = time.time()
    _run_selection_if_needed(prereg, resume=resume)
    rows = _read_csv_rows(ROWS_FULL_CSV)
    fixed_grid, pertuned_by_pair, selection_summary = choose_grids_from_selection(rows, prereg)
    _run_oracle_adequacy_if_needed(prereg, pertuned_by_pair=pertuned_by_pair, resume=resume)
    rows = _read_csv_rows(ROWS_FULL_CSV)
    _run_validation_if_needed(
        prereg,
        fixed_grid=fixed_grid,
        pertuned_by_pair=pertuned_by_pair,
        resume=resume,
    )

    rows = _read_csv_rows(ROWS_FULL_CSV)
    summary = summarize_full(rows, prereg, fixed_grid=fixed_grid, selection_summary=selection_summary)
    summary["budget"] = {
        "elapsed_s": round(time.time() - t0, 1),
        "selection_pairs": len(prereg["row_pairs"]),
        "validation_variant_pairs": len(prereg["chrono_vehicle_variants"]) * len(prereg["row_pairs"]),
        "grid_count": len(prereg["full_grid_values"]),
        "oracle_budget": prereg["full_oracle_budget"],
        "oracle_floor_candidate": prereg["oracle_floor_candidate"],
        "resume": bool(resume),
    }
    write_json(RESULTS_JSON, summary)
    write_csv_rows(
        METRICS_FULL_CSV,
        [
            {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
            {"metric": "qualifying_variant_count", "value": len(summary["decision"]["qualifying_variants"])},
            {"metric": "pooled_pertuned_minus_fixed_star", "value": summary["pooled"]["primary_prize_pertuned_minus_fixed_star"]["value"]},
            {"metric": "pooled_pertuned_minus_rls", "value": summary["pooled"]["classical_residual_pertuned_minus_rls"]["value"]},
            {"metric": "pooled_native_minus_pertuned", "value": summary["pooled"]["oracle_anchor_native_minus_pertuned"]["value"]},
            {"metric": "oracle_adequacy_gate_passed", "value": 1.0 if summary["oracle_adequacy"]["gate_passed"] else 0.0},
            {"metric": "validation_units_per_variant", "value": summary["validation_units_per_variant"]},
            {"metric": "track_f_admitted", "value": 1.0 if summary["decision"]["track_f_admitted"] else 0.0},
        ],
        fieldnames=["metric", "value"],
    )
    write_markdown(DOC_PATH, summary)
    if not summary["protocol_gates"]["all_passed"]:
        raise RuntimeError(f"M3259 protocol gates failed: {summary['protocol_gates']}")
    return summary


def _quick_preregistration(prereg: dict[str, Any]) -> dict[str, Any]:
    quick = dict(prereg)
    quick["row_pairs"] = list(prereg["quick_row_pairs"])
    quick["min_validation_units_per_variant"] = len(quick["row_pairs"])
    quick["full_oracle_budget"] = dict(QUICK_ORACLE_BUDGET.__dict__)
    return quick


def run_quick(*, resume: bool) -> dict[str, Any]:
    prereg = _quick_preregistration(load_preregistration())
    required = [
        REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1_spread_revival_quick.json",
        REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1_spread_revival_full.json",
    ]
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M3259 quick requires prior artifacts: {missing}")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not resume:
        for path in (ROWS_QUICK_CSV, METRICS_QUICK_CSV, PROGRESS_QUICK_JSONL, QUICK_JSON):
            if path.exists():
                path.unlink()

    t0 = time.time()
    _run_selection_if_needed(
        prereg,
        resume=resume,
        rows_csv=ROWS_QUICK_CSV,
        progress_jsonl=PROGRESS_QUICK_JSONL,
        stderr_log=STDERR_QUICK_LOG,
    )
    rows = _read_csv_rows(ROWS_QUICK_CSV)
    fixed_grid, pertuned_by_pair, selection_summary = choose_grids_from_selection(rows, prereg)
    _run_oracle_adequacy_if_needed(
        prereg,
        pertuned_by_pair=pertuned_by_pair,
        resume=resume,
        rows_csv=ROWS_QUICK_CSV,
        progress_jsonl=PROGRESS_QUICK_JSONL,
        stderr_log=STDERR_QUICK_LOG,
        force_search=True,
        budget=QUICK_ORACLE_BUDGET,
    )
    _run_validation_if_needed(
        prereg,
        fixed_grid=fixed_grid,
        pertuned_by_pair=pertuned_by_pair,
        resume=resume,
        rows_csv=ROWS_QUICK_CSV,
        progress_jsonl=PROGRESS_QUICK_JSONL,
        stderr_log=STDERR_QUICK_LOG,
        budget=QUICK_ORACLE_BUDGET,
        force_search=True,
    )

    rows = _read_csv_rows(ROWS_QUICK_CSV)
    summary = summarize_full(rows, prereg, fixed_grid=fixed_grid, selection_summary=selection_summary)
    summary["mode"] = "quick"
    summary["rows_csv"] = str(ROWS_QUICK_CSV.relative_to(REPO_ROOT))
    summary["metrics_csv"] = str(METRICS_QUICK_CSV.relative_to(REPO_ROOT))
    apply_quick_smoke_decision(summary)
    summary["budget"] = {
        "elapsed_s": round(time.time() - t0, 1),
        "selection_pairs": len(prereg["row_pairs"]),
        "validation_variant_pairs": len(prereg["chrono_vehicle_variants"]) * len(prereg["row_pairs"]),
        "grid_count": len(prereg["full_grid_values"]),
        "oracle_budget": dict(QUICK_ORACLE_BUDGET.__dict__),
        "oracle_floor_candidate": prereg["oracle_floor_candidate"],
        "resume": bool(resume),
    }
    write_json(QUICK_JSON, summary)
    write_csv_rows(
        METRICS_QUICK_CSV,
        [
            {"metric": "protocol_gates_passed", "value": 1.0 if summary["protocol_gates"]["all_passed"] else 0.0},
            {"metric": "oracle_adequacy_gate_passed", "value": 1.0 if summary["oracle_adequacy"]["gate_passed"] else 0.0},
            {"metric": "validation_units_per_variant", "value": summary["validation_units_per_variant"]},
            {"metric": "quick_mode_is_verdict", "value": 0.0},
        ],
        fieldnames=["metric", "value"],
    )
    if not summary["protocol_gates"]["all_passed"]:
        raise RuntimeError(f"M3259 quick gates failed: {summary['protocol_gates']}")
    return summary


def apply_quick_smoke_decision(summary: dict[str, Any]) -> None:
    summary["quick_mode_is_verdict"] = False
    summary["decision"]["e1prime_quick_verdict"] = (
        "protocol_smoke_passed" if summary["protocol_gates"]["all_passed"] else "protocol_smoke_failed"
    )
    summary["decision"]["e1prime_full_verdict"] = "not_run_quick_mode"
    summary["decision"]["track_f_admitted"] = False
    summary["decision"]["next_admitted_step"] = (
        "Run the registered E1' full repricing before marking E1' complete; "
        "Track F remains blocked on the later PI GPU-days checkpoint"
    )


def _paired_readout(
    rows_by_pair: dict[str, dict[str, dict[str, Any]]],
    pair_ids: list[str],
    arm_a: str,
    arm_b: str,
    rng: np.random.Generator,
) -> dict[str, Any]:
    complete = [pair_id for pair_id in pair_ids if arm_a in rows_by_pair.get(pair_id, {}) and arm_b in rows_by_pair.get(pair_id, {})]
    a = np.array([1.0 if rows_by_pair[pair_id][arm_a]["chrono_outcome"] == "success" else 0.0 for pair_id in complete])
    b = np.array([1.0 if rows_by_pair[pair_id][arm_b]["chrono_outcome"] == "success" else 0.0 for pair_id in complete])
    value = float(a.mean() - b.mean()) if len(complete) else float("nan")
    return {
        "value": round(value, 4) if math.isfinite(value) else value,
        "paired_bootstrap_ci95": c5.paired_bootstrap_ci(a, b, rng),
        "n_pairs": len(complete),
        "success_counts": {arm_a: int(a.sum()), arm_b: int(b.sum())},
    }


def summarize_oracle_adequacy(rows: list[dict[str, Any]], prereg: dict[str, Any]) -> dict[str, Any]:
    variants = list(prereg["chrono_vehicle_variants"])
    pair_ids = [pair["pair_id"] for pair in prereg["row_pairs"]]
    adequacy_rows = [row for row in rows if row.get("role") == "oracle_adequacy"]
    per_variant: dict[str, Any] = {}
    gate_passed = True
    for v_i, variant in enumerate(variants):
        rows_by_pair: dict[str, dict[str, dict[str, Any]]] = {}
        candidate_rows = []
        for row in adequacy_rows:
            if row.get("variant") != variant:
                continue
            if row.get("arm") in ("v4_pertuned", "native_oracle"):
                rows_by_pair.setdefault(str(row["pair_id"]), {})[str(row["arm"])] = row
            if row.get("arm") == "native_oracle_candidate":
                candidate_rows.append(row)
        complete = {pair_id: all(arm in rows_by_pair.get(pair_id, {}) for arm in ("v4_pertuned", "native_oracle")) for pair_id in pair_ids}
        readout = _paired_readout(
            rows_by_pair,
            pair_ids,
            "native_oracle",
            "v4_pertuned",
            np.random.default_rng([SEED_BASE, 44, v_i]),
        )
        per_pair_nonnegative = all(
            (
                1.0 if rows_by_pair[pair_id]["native_oracle"]["chrono_outcome"] == "success" else 0.0
            )
            >= (
                1.0 if rows_by_pair[pair_id]["v4_pertuned"]["chrono_outcome"] == "success" else 0.0
            )
            for pair_id, is_complete in complete.items()
            if is_complete
        )
        variant_gate = all(complete.values()) and readout["value"] >= 0.0 and per_pair_nonnegative
        gate_passed = gate_passed and variant_gate
        per_variant[variant] = {
            "pair_complete": complete,
            "all_pairs_complete": all(complete.values()),
            "native_minus_pertuned": readout,
            "per_pair_success_nonnegative": per_pair_nonnegative,
            "floor_candidate_rows": sum(str(row.get("candidate", "")) == "floor:v4_pertuned_full_episode" for row in candidate_rows),
            "structured_candidate_attempts": sum(str(row.get("candidate", "")).startswith("structured:") for row in candidate_rows),
            "cem_candidate_attempts": sum(str(row.get("candidate", "")).startswith("cem_iter") for row in candidate_rows),
            "gate_passed": variant_gate,
        }
    return {"gate_passed": gate_passed, "per_variant": per_variant}


def summarize_full(
    rows: list[dict[str, Any]],
    prereg: dict[str, Any],
    *,
    fixed_grid: tuple[float, float, float],
    selection_summary: dict[str, Any],
) -> dict[str, Any]:
    variants = list(prereg["chrono_vehicle_variants"])
    pair_ids = [pair["pair_id"] for pair in prereg["row_pairs"]]
    validation_units_per_variant = len(pair_ids)
    validation_rows = [row for row in rows if row.get("role") == "validation"]
    adequacy = summarize_oracle_adequacy(rows, prereg)
    per_variant: dict[str, Any] = {}
    pooled_by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    qualifying: list[str] = []

    for v_i, variant in enumerate(variants):
        rows_by_pair: dict[str, dict[str, dict[str, Any]]] = {}
        for row in validation_rows:
            if row.get("variant") != variant or row.get("arm") not in ARMS:
                continue
            rows_by_pair.setdefault(str(row["pair_id"]), {})[str(row["arm"])] = row
            pooled_by_pair.setdefault(f"{variant}/{row['pair_id']}", {})[str(row["arm"])] = row
        pair_complete = {
            pair_id: all(arm in rows_by_pair.get(pair_id, {}) for arm in ARMS)
            for pair_id in pair_ids
        }
        candidate_rows = [
            row
            for row in validation_rows
            if row.get("variant") == variant and row.get("arm") == "native_oracle_candidate"
        ]
        readouts = {
            "primary_prize_pertuned_minus_fixed_star": _paired_readout(
                rows_by_pair, pair_ids, "v4_pertuned", "fixed_star", np.random.default_rng([SEED_BASE, 88, v_i, 1])
            ),
            "classical_residual_pertuned_minus_rls": _paired_readout(
                rows_by_pair, pair_ids, "v4_pertuned", "v4_rls", np.random.default_rng([SEED_BASE, 88, v_i, 2])
            ),
            "oracle_anchor_native_minus_pertuned": _paired_readout(
                rows_by_pair, pair_ids, "native_oracle", "v4_pertuned", np.random.default_rng([SEED_BASE, 88, v_i, 3])
            ),
        }
        variant_qualifies = (
            readouts["primary_prize_pertuned_minus_fixed_star"]["value"] >= 0.15
            and readouts["primary_prize_pertuned_minus_fixed_star"]["paired_bootstrap_ci95"][0] > 0.0
            and readouts["classical_residual_pertuned_minus_rls"]["value"] >= 0.08
        )
        if variant_qualifies:
            qualifying.append(variant)
        per_variant[variant] = {
            "pair_complete": pair_complete,
            "all_pairs_complete": all(pair_complete.values()),
            "arm_success_counts": {
                arm: sum(
                    rows_by_pair.get(pair_id, {}).get(arm, {}).get("chrono_outcome") == "success"
                    for pair_id in pair_ids
                )
                for arm in ARMS
            },
            "structured_candidate_attempts": sum(str(row.get("candidate", "")).startswith("structured:") for row in candidate_rows),
            "cem_candidate_attempts": sum(str(row.get("candidate", "")).startswith("cem_iter") for row in candidate_rows),
            "readouts": readouts,
            "qualifies_spread_revival": variant_qualifies,
            "reset_obs_finite_all": all(_boolish(row.get("reset_obs_finite")) for row in validation_rows if row.get("variant") == variant),
            "variant_match_all": all(_boolish(row.get("variant_match")) for row in validation_rows if row.get("variant") == variant),
        }

    pooled_pair_ids = list(pooled_by_pair.keys())
    pooled = {
        "primary_prize_pertuned_minus_fixed_star": _paired_readout(
            pooled_by_pair, pooled_pair_ids, "v4_pertuned", "fixed_star", np.random.default_rng([SEED_BASE, 99, 1])
        ),
        "classical_residual_pertuned_minus_rls": _paired_readout(
            pooled_by_pair, pooled_pair_ids, "v4_pertuned", "v4_rls", np.random.default_rng([SEED_BASE, 99, 2])
        ),
        "oracle_anchor_native_minus_pertuned": _paired_readout(
            pooled_by_pair, pooled_pair_ids, "native_oracle", "v4_pertuned", np.random.default_rng([SEED_BASE, 99, 3])
        ),
    }
    selection_rows = [row for row in rows if row.get("role") == "selection"]
    selection_ids = {pair["selection_row"]["row_id"] for pair in prereg["row_pairs"]}
    validation_ids = {pair["validation_row"]["row_id"] for pair in prereg["row_pairs"]}
    gates = {
        "e0_admitted_e1": bool(prereg.get("e0_decision", {}).get("e1_preregistration_admitted", False)),
        "selection_validation_disjoint": selection_ids.isdisjoint(validation_ids),
        "selection_grid_complete": _selection_complete(rows, prereg),
        "min_validation_units_per_variant": validation_units_per_variant >= int(prereg["min_validation_units_per_variant"]),
        "oracle_adequacy_gate_passed": bool(adequacy["gate_passed"]),
        "validation_pairs_complete": all(block["all_pairs_complete"] for block in per_variant.values()),
        "reset_obs_finite_all": all(block["reset_obs_finite_all"] for block in per_variant.values()),
        "variant_match_all": all(block["variant_match_all"] for block in per_variant.values()),
        "full_json_not_quick": True,
    }
    gates["all_passed"] = all(gates.values())
    if not adequacy["gate_passed"]:
        verdict = "e1prime_oracle_inadequate_inconclusive"
    elif gates["all_passed"] and len(qualifying) >= 2:
        verdict = "e1prime_spread_revival_positive"
    else:
        verdict = "e1prime_spread_revival_not_supported"
    return {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": "full",
        "created_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "e0_axis_table_sha256": prereg["e0_axis_table_sha256"],
        "rows_csv": str(ROWS_FULL_CSV.relative_to(REPO_ROOT)),
        "metrics_csv": str(METRICS_FULL_CSV.relative_to(REPO_ROOT)),
        "row_pairs": prereg["row_pairs"],
        "variants": variants,
        "fixed_star_grid": list(fixed_grid),
        "selection_summary": selection_summary,
        "selection_row_count": len(selection_rows),
        "validation_row_count": len(validation_rows),
        "validation_units_per_variant": validation_units_per_variant,
        "oracle_adequacy": adequacy,
        "per_variant": per_variant,
        "pooled": pooled,
        "protocol_gates": gates,
        "decision": {
            "e1prime_full_verdict": verdict,
            "qualifying_variants": qualifying,
            "positive_rule": prereg["preregistered_readouts"]["positive_rule"],
            "track_f_admitted": False,
            "next_admitted_step": (
                "E1' is complete; Track F remains blocked on the later PI GPU-days checkpoint"
            ),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# M3259 Phase-4 E1' Oracle-Adequate Spread-Revival Repricing",
        "",
        "Status: completed. This is the frozen E1' Chrono repricing verdict with a selection-row oracle-adequacy gate; it is not training and does not admit Track F.",
        "",
        "## Verdict",
        "",
        f"- E1' full verdict: **{payload['decision']['e1prime_full_verdict']}**.",
        f"- Qualifying variants: {', '.join('`' + v + '`' for v in payload['decision']['qualifying_variants']) or 'none'}.",
        f"- Protocol gates passed: **{str(payload['protocol_gates']['all_passed']).lower()}**.",
        f"- Oracle adequacy gate passed: **{str(payload['oracle_adequacy']['gate_passed']).lower()}**.",
        f"- Fixed* grid selected on selection rows: `{tuple(payload['fixed_star_grid'])}`.",
        "",
        "## Measured",
        "",
        f"- Variants: {', '.join('`' + v + '`' for v in payload['variants'])}.",
        f"- Validation units per variant: {payload['validation_units_per_variant']}.",
        f"- Rows CSV: `{payload['rows_csv']}`.",
        "",
        "Selection-row oracle adequacy:",
        "",
        "| variant | native - pertuned | CI95 | n | floor candidates | structured | CEM | gate |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for variant, block in payload["oracle_adequacy"]["per_variant"].items():
        readout = block["native_minus_pertuned"]
        lines.append(
            f"| `{variant}` | {readout['value']:.4f} | {readout['paired_bootstrap_ci95']} | "
            f"{readout['n_pairs']} | {block['floor_candidate_rows']} | "
            f"{block['structured_candidate_attempts']} | {block['cem_candidate_attempts']} | "
            f"{block['gate_passed']} |"
        )
    lines.extend(
        [
        "",
        "Validation spread readouts:",
        "",
        "| variant | fixed | RLS | pertuned | native | pertuned-fixed | CI95 | pertuned-RLS | CI95 | native-pertuned |",
        "|---|---:|---:|---:|---:|---:|---|---:|---|---:|",
        ]
    )
    for variant, block in payload["per_variant"].items():
        counts = block["arm_success_counts"]
        primary = block["readouts"]["primary_prize_pertuned_minus_fixed_star"]
        residual = block["readouts"]["classical_residual_pertuned_minus_rls"]
        oracle = block["readouts"]["oracle_anchor_native_minus_pertuned"]
        lines.append(
            f"| `{variant}` | {counts['fixed_star']} | {counts['v4_rls']} | {counts['v4_pertuned']} | "
            f"{counts['native_oracle']} | {primary['value']:.4f} | {primary['paired_bootstrap_ci95']} | "
            f"{residual['value']:.4f} | {residual['paired_bootstrap_ci95']} | {oracle['value']:.4f} |"
        )
    pooled = payload["pooled"]
    lines.extend(
        [
            "",
            "Pooled readouts:",
            "",
            f"- `v4_pertuned - fixed_star`: {pooled['primary_prize_pertuned_minus_fixed_star']['value']:.4f}, CI95 {pooled['primary_prize_pertuned_minus_fixed_star']['paired_bootstrap_ci95']}.",
            f"- `v4_pertuned - v4_rls`: {pooled['classical_residual_pertuned_minus_rls']['value']:.4f}, CI95 {pooled['classical_residual_pertuned_minus_rls']['paired_bootstrap_ci95']}.",
            f"- `native_oracle - v4_pertuned`: {pooled['oracle_anchor_native_minus_pertuned']['value']:.4f}, CI95 {pooled['oracle_anchor_native_minus_pertuned']['paired_bootstrap_ci95']}.",
            "",
            "## Inferred",
            "",
            "The verdict above applies only to the E0-admitted Chrono fixture envelope and this frozen grid/oracle budget. It does not cover independent payload-position, h_cg, tire-family, split-mu, or continuous lf/lr/Iz/cf/cr axes.",
            "",
            "Track F remains blocked until the later PI GPU-days checkpoint.",
            "",
            "## Claim Boundary",
            "",
            CLAIM_BOUNDARY,
            "",
            "## Artifacts",
            "",
            f"- Preregistration: `{PREREG_JSON.relative_to(REPO_ROOT)}`",
            f"- Full JSON: `{RESULTS_JSON.relative_to(REPO_ROOT)}`",
            f"- Episode rows: `{ROWS_FULL_CSV.relative_to(REPO_ROOT)}`",
            f"- Metrics: `{METRICS_FULL_CSV.relative_to(REPO_ROOT)}`",
            f"- Script: `scripts/feasibility_audit/{Path(__file__).name}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        print(json.dumps({"preregistration": str(PREREG_JSON), "row_pairs": len(payload["row_pairs"])}, sort_keys=True))
    if args.quick:
        payload = run_quick(resume=bool(args.resume))
        print(json.dumps(payload["decision"], ensure_ascii=False, sort_keys=True))
    if args.full:
        payload = run_full(resume=bool(args.resume))
        print(json.dumps(payload["decision"], ensure_ascii=False, sort_keys=True))
    if not (args.write_prereg or args.quick or args.full):
        raise SystemExit("choose --write-prereg, --quick, or --full")


if __name__ == "__main__":
    main()
