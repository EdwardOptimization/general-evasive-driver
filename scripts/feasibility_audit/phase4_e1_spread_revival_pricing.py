"""Phase-4 E1 Chrono spread-revival pricing protocol.

M3249 uses this script in ``--quick`` mode as a protocol smoke. It exercises
the four E1 arms in Chrono against the M3248 E0 expressibility envelope:
global fixed* retune, RLS-retuned, per-instance tuned, and native Chrono
oracle. Quick mode is not a spread-revival verdict.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e1_spread_revival_pricing.py --write-prereg
    PYTHONPATH=src python scripts/feasibility_audit/phase4_e1_spread_revival_pricing.py --quick
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

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json  # noqa: E402
import c5_reflex_degradation as c5  # noqa: E402
import chrono_native_oracle_pricing as d1b  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402


MILESTONE_ID = "m3249-phase4-e1-spread-revival-pricing-smoke"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1_spread_revival_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1_spread_revival_quick.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_e1_spread_revival"
ROWS_QUICK_CSV = RUN_DIR / "episode_rows_quick.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
STDERR_LOG = RUN_DIR / "chrono_worker_stderr.log"
DOC_PATH = REPO_ROOT / "docs" / "m3249-phase4-e1-spread-revival-pricing-smoke.md"

E0_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "chrono_spread_expressibility_audit.json"
SOURCE_ROWS_CSV = REPO_ROOT / "runs" / "feasibility_audit" / "c5prime_target_consolidation" / "episode_rows.csv"
SOURCE_RESULTS_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "c5prime_target_consolidation.json"

SEED_BASE = 20260613_01
QUICK_GRID_VALUES = (
    (1.0, 1.0, 1.0),
    (1.8, 1.45, 1.4),
    (0.6, 1.0, 1.0),
)
QUICK_ORACLE_BUDGET = d1b.SearchBudget(
    structured_limit=2,
    cem_segments=2,
    cem_segment_len=8,
    cem_population=2,
    cem_elites=1,
    cem_iterations=1,
)
ARMS = ("fixed_star", "v4_rls", "v4_pertuned", "native_oracle")

CLAIM_BOUNDARY = (
    "Phase-4 E1 Chrono spread-revival pricing protocol smoke only: exercises "
    "the fixed*, RLS-retuned, per-instance tuned, and native Chrono oracle arms "
    "inside the E0-frozen expressibility envelope. Quick mode is not a spread "
    "pricing verdict and makes no driver-performance, high-fidelity sufficiency, "
    "validation ranking, promotion, repair-success, feasibility-proof, paper, "
    "robustness, or self-ID claim."
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


def _stable_hash(payload: Any) -> str:
    text = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_e0_envelope() -> dict[str, Any]:
    if not E0_JSON.exists():
        raise FileNotFoundError(f"missing E0 artifact {E0_JSON}")
    e0 = _read_json(E0_JSON)
    decision = e0.get("decision", {})
    if not decision.get("e1_preregistration_admitted"):
        raise RuntimeError("E0 did not admit E1 preregistration")
    return e0


def selected_quick_row() -> dict[str, Any]:
    rows = d1b.select_prereg_rows(rows_per_level=1)
    return rows[0]


def build_preregistration() -> dict[str, Any]:
    e0 = load_e0_envelope()
    quick_row = selected_quick_row()
    variants = list(e0["e1_spread_envelope"]["recommended_e1_population_panel"]["vehicle_variants"])
    return {
        "protocol": "phase4_e1_spread_revival_pricing_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 E1 Spread-revival pricing",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_e1_run": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "e0_artifact": str(E0_JSON.relative_to(REPO_ROOT)),
        "e0_axis_table_sha256": e0["axis_table_sha256"],
        "e0_allowed_envelope": e0["e1_spread_envelope"],
        "quick_mode_is_verdict": False,
        "quick_variants": variants,
        "quick_selected_rows": [quick_row],
        "quick_grid_values": [list(grid) for grid in QUICK_GRID_VALUES],
        "quick_oracle_budget": QUICK_ORACLE_BUDGET.__dict__,
        "full_mode_placeholder": {
            "status": "not_registered_by_M3249",
            "needed_next": (
                "A separate M3250 full E1 milestone must freeze selection and validation rows, "
                "full grid budget, paired CIs, and stop/decision thresholds before any verdict."
            ),
        },
        "arms": {
            "fixed_star": "global Chrono mini-grid winner across quick variants (protocol smoke only)",
            "v4_rls": "C5 kappa-RLS retuning map applied to the quick fixed_star grid",
            "v4_pertuned": "per quick row/variant Chrono mini-grid winner (protocol smoke only)",
            "native_oracle": "Chrono-native reveal-constrained structured + CEM search with v4_pertuned prefix",
        },
        "blocked_by_e0_without_new_connector": [
            row["axis"] for row in e0["e1_spread_envelope"]["blocked_without_new_connector"]
        ],
        "runtime_gates": [
            "E0 artifact admits E1",
            "quick smoke exercises every quick variant",
            "fixed_star, v4_rls, v4_pertuned, and native_oracle rows are written for every quick variant",
            "native_oracle search exercises at least one structured and one CEM candidate per quick variant",
            "all reset observations are finite and backend_info variant ids match",
            "quick result explicitly refuses an E1 spread-revival verdict",
        ],
        "decision_rule": (
            "M3249 PASS iff quick mode writes rows for every quick variant and all four arms, "
            "native oracle structured/CEM candidates are exercised, reset/variant gates pass, "
            "and the artifact labels itself as protocol smoke only. M3249 never decides E1."
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
    if not payload.get("frozen_before_any_e1_run"):
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_e1_run")
    return payload


def _row_id(row: dict[str, Any]) -> str:
    return str(row["row_id"])


def _grid_key(grid: tuple[float, float, float]) -> str:
    return f"({grid[0]:.1f}, {grid[1]:.2f}, {grid[2]:.1f})"


def _make_grid_policy(grid: tuple[float, float, float]):
    return d1b._fixed_grid_policy(grid)  # reuse D1b's Chrono-compatible policy wrapper


def _rls_policy(selected: d1b.SelectedRow, fixed_grid: tuple[float, float, float]):
    d1b._configure_c5prime_globals()
    vehicle, _row = d1b._exact_row_params(selected)
    rls = c5.familiarization_rls(selected.level, selected.instance, vehicle)
    v2_cfg, v4_cfg = c5.rls_cfgs(fixed_grid, rls["kappa_b_hat"], rls["kappa_d_hat"])

    def policy(_step: int, obs: np.ndarray) -> np.ndarray:
        return c5.composed_action(np.asarray(obs, dtype=np.float32), v2_cfg, v4_cfg)

    return policy, rls


def _episode_row(
    *,
    variant: str,
    selected: d1b.SelectedRow,
    arm: str,
    candidate: str,
    grid: tuple[float, float, float] | None,
    result: dict[str, Any],
    score: float,
) -> dict[str, Any]:
    backend = result.get("backend_info", {})
    return {
        "variant": variant,
        "row_id": selected.row_id,
        "level": selected.level,
        "instance": selected.instance,
        "eval_seed": selected.eval_seed,
        "arm": arm,
        "candidate": candidate,
        "grid": "" if grid is None else str(tuple(float(x) for x in grid)),
        "chrono_outcome": result["outcome"],
        "chrono_steps": int(result["steps"]),
        "score": round(float(score), 6),
        "reset_obs_finite": bool(result["reset_obs_finite"]),
        "variant_match": bool(result["variant_match"]),
        "backend_model": backend.get("chrono_vehicle_model", ""),
        "backend_tire": backend.get("chrono_tire_model", ""),
        "target_mass": backend.get("target_mass", ""),
        "vehicle_total_mass": backend.get("vehicle_total_mass", ""),
        "wheelbase_m": backend.get("chrono_wheelbase_m", ""),
        "trace_signature": result.get("trace_signature", ""),
        "claim_boundary": CLAIM_BOUNDARY,
    }


FIELDNAMES = list(
    _episode_row(
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


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _jsonable(row.get(key, "")) for key in FIELDNAMES})


def _append_progress(payload: dict[str, Any]) -> None:
    PROGRESS_QUICK_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_QUICK_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def choose_fixed_and_pertuned(
    grid_results: dict[tuple[str, tuple[float, float, float]], dict[str, Any]],
) -> tuple[tuple[float, float, float], dict[str, tuple[float, float, float]]]:
    """Choose the global fixed* grid and per-variant tuned grids from scored results."""

    grids = sorted({grid for _variant, grid in grid_results})
    variants = sorted({variant for variant, _grid in grid_results})
    global_scores = {
        grid: sum(float(grid_results[(variant, grid)]["score"]) for variant in variants)
        for grid in grids
    }
    fixed_grid = max(grids, key=lambda grid: (global_scores[grid], -grids.index(grid)))
    pertuned = {
        variant: max(grids, key=lambda grid: (float(grid_results[(variant, grid)]["score"]), -grids.index(grid)))
        for variant in variants
    }
    return fixed_grid, pertuned


def summarize_quick(rows: list[dict[str, Any]], prereg: dict[str, Any]) -> dict[str, Any]:
    variants = list(prereg["quick_variants"])
    per_variant: dict[str, Any] = {}
    for variant in variants:
        vr = [row for row in rows if row["variant"] == variant]
        arm_rows = {arm: [row for row in vr if row["arm"] == arm] for arm in ARMS}
        candidate_rows = [row for row in vr if row["arm"] == "native_oracle_candidate"]
        per_variant[variant] = {
            "arm_rows": {arm: len(arm_rows[arm]) for arm in ARMS},
            "arm_success": {
                arm: sum(row["chrono_outcome"] == "success" for row in arm_rows[arm])
                for arm in ARMS
            },
            "structured_candidate_attempts": sum(
                str(row["candidate"]).startswith("structured:") for row in candidate_rows
            ),
            "cem_candidate_attempts": sum(str(row["candidate"]).startswith("cem_iter") for row in candidate_rows),
            "all_reset_obs_finite": all(bool(row["reset_obs_finite"]) for row in vr),
            "all_variant_match": all(bool(row["variant_match"]) for row in vr),
            "quick_deltas_context_only": {
                "pertuned_minus_fixed_star": (
                    sum(row["chrono_outcome"] == "success" for row in arm_rows["v4_pertuned"])
                    - sum(row["chrono_outcome"] == "success" for row in arm_rows["fixed_star"])
                ),
                "pertuned_minus_rls": (
                    sum(row["chrono_outcome"] == "success" for row in arm_rows["v4_pertuned"])
                    - sum(row["chrono_outcome"] == "success" for row in arm_rows["v4_rls"])
                ),
                "native_oracle_minus_pertuned": (
                    sum(row["chrono_outcome"] == "success" for row in arm_rows["native_oracle"])
                    - sum(row["chrono_outcome"] == "success" for row in arm_rows["v4_pertuned"])
                ),
            },
        }
    gates = {
        "quick_mode_not_verdict": not prereg["quick_mode_is_verdict"],
        "all_variants_exercised": all(any(row["variant"] == variant for row in rows) for variant in variants),
        "all_arms_exercised": all(
            per_variant[variant]["arm_rows"][arm] >= 1 for variant in variants for arm in ARMS
        ),
        "structured_candidates_exercised": all(
            per_variant[variant]["structured_candidate_attempts"] >= 1 for variant in variants
        ),
        "cem_candidates_exercised": all(
            per_variant[variant]["cem_candidate_attempts"] >= 1 for variant in variants
        ),
        "reset_obs_finite_all": all(block["all_reset_obs_finite"] for block in per_variant.values()),
        "variant_match_all": all(block["all_variant_match"] for block in per_variant.values()),
    }
    gates["all_passed"] = all(gates.values())
    return {
        "per_variant": per_variant,
        "quick_gates": gates,
        "decision": {
            "status_pass": gates["all_passed"],
            "e1_full_verdict": None,
            "next_admitted_step": (
                "register a separate full E1 pricing milestone with frozen selection/validation rows and paired CIs"
                if gates["all_passed"]
                else "repair the E1 protocol before full pricing"
            ),
        },
    }


def run_quick() -> dict[str, Any]:
    prereg = load_preregistration()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    for path in (ROWS_QUICK_CSV, METRICS_QUICK_CSV, PROGRESS_QUICK_JSONL, QUICK_JSON):
        if path.exists():
            path.unlink()
    selected = d1b._as_selected(prereg["quick_selected_rows"][0])
    variants = list(prereg["quick_variants"])
    grids = [tuple(float(x) for x in grid) for grid in prereg["quick_grid_values"]]
    rows: list[dict[str, Any]] = []
    grid_results: dict[tuple[str, tuple[float, float, float]], dict[str, Any]] = {}
    t0 = time.time()

    # First pass: mini Chrono retune. The same quick row is used only as a smoke
    # probe, so no E1 readout is interpreted from these scores.
    for variant in variants:
        scenario = d1b._scenario_for(selected, variant)
        with_client = ChronoWorkerClient(stderr_log=STDERR_LOG)
        try:
            for grid in grids:
                result = d1b.run_chrono_episode(with_client, scenario, _make_grid_policy(grid), requested_variant=variant)
                score = d1b._score_result(result, int(scenario["max_steps"]) + 5)
                grid_results[(variant, grid)] = {"result": result, "score": score}
        finally:
            with_client.close()
        _append_progress({"stage": "grid_probe_variant_done", "variant": variant, "elapsed_s": round(time.time() - t0, 1)})

    fixed_grid, pertuned_by_variant = choose_fixed_and_pertuned(grid_results)

    for variant in variants:
        selected_grid = pertuned_by_variant[variant]
        fixed_probe = grid_results[(variant, fixed_grid)]
        pertuned_probe = grid_results[(variant, selected_grid)]
        rows.append(
            _episode_row(
                variant=variant,
                selected=selected,
                arm="fixed_star",
                candidate="quick_global_grid",
                grid=fixed_grid,
                result=fixed_probe["result"],
                score=float(fixed_probe["score"]),
            )
        )
        rows.append(
            _episode_row(
                variant=variant,
                selected=selected,
                arm="v4_pertuned",
                candidate="quick_per_variant_grid",
                grid=selected_grid,
                result=pertuned_probe["result"],
                score=float(pertuned_probe["score"]),
            )
        )

        scenario = d1b._scenario_for(selected, variant)
        client = ChronoWorkerClient(stderr_log=STDERR_LOG)
        try:
            rls_policy, rls_info = _rls_policy(selected, fixed_grid)
            rls_result = d1b.run_chrono_episode(client, scenario, rls_policy, requested_variant=variant)
            rls_score = d1b._score_result(rls_result, int(scenario["max_steps"]) + 5)
            rls_row = _episode_row(
                variant=variant,
                selected=selected,
                arm="v4_rls",
                candidate="quick_c5_rls_map",
                grid=fixed_grid,
                result=rls_result,
                score=rls_score,
            )
            rls_row["rls_info"] = json.dumps(_jsonable(rls_info), sort_keys=True)
            rows.append(rls_row)

            oracle_best, attempts = d1b._run_native_oracle_search(
                client,
                scenario,
                selected,
                variant,
                _make_grid_policy(selected_grid),
                QUICK_ORACLE_BUDGET,
                np.random.default_rng([SEED_BASE, variants.index(variant), selected.instance]),
                require_cem_attempt=True,
            )
            for attempt in attempts:
                attempt_row = dict(attempt)
                attempt_row["arm"] = "native_oracle_candidate"
                rows.append({key: attempt_row.get(key, "") for key in FIELDNAMES})
            best_row = {key: oracle_best.get(key, "") for key in FIELDNAMES}
            best_row["arm"] = "native_oracle"
            best_row["candidate"] = "best_" + str(oracle_best.get("candidate", ""))
            rows.append(best_row)
        finally:
            client.close()
        _append_progress({"stage": "arms_variant_done", "variant": variant, "elapsed_s": round(time.time() - t0, 1)})

    _write_rows(ROWS_QUICK_CSV, rows)
    summary = summarize_quick(rows, prereg)
    write_csv_rows(
        METRICS_QUICK_CSV,
        [
            {"metric": "status_pass", "value": 1.0 if summary["decision"]["status_pass"] else 0.0},
            {"metric": "variant_count", "value": len(variants)},
            {"metric": "arm_rows_total", "value": sum(len([row for row in rows if row["arm"] == arm]) for arm in ARMS)},
            {"metric": "quick_mode_not_verdict", "value": 1.0},
            {"metric": "structured_candidates_min", "value": min(block["structured_candidate_attempts"] for block in summary["per_variant"].values())},
            {"metric": "cem_candidates_min", "value": min(block["cem_candidate_attempts"] for block in summary["per_variant"].values())},
        ],
        fieldnames=["metric", "value"],
    )
    payload = {
        "schema_version": 1,
        "milestone": MILESTONE_ID,
        "mode": "quick",
        "created_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "preregistration_sha256": _stable_hash(prereg),
        "e0_axis_table_sha256": prereg["e0_axis_table_sha256"],
        "quick_selected_rows": prereg["quick_selected_rows"],
        "quick_variants": variants,
        "quick_grid_values": prereg["quick_grid_values"],
        "fixed_star_grid": list(fixed_grid),
        "pertuned_grid_by_variant": {variant: list(grid) for variant, grid in pertuned_by_variant.items()},
        "rows_csv": str(ROWS_QUICK_CSV.relative_to(REPO_ROOT)),
        "metrics_csv": str(METRICS_QUICK_CSV.relative_to(REPO_ROOT)),
        **summary,
    }
    write_json(QUICK_JSON, payload)
    write_markdown(DOC_PATH, payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# M3249 Phase-4 E1 Spread-Revival Pricing Smoke",
        "",
        "Status: completed. This is an E1 protocol smoke, not the full spread-revival pricing verdict.",
        "",
        "## Verdict",
        "",
        f"- Quick protocol pass: **{str(payload['decision']['status_pass']).lower()}**.",
        "- E1 full verdict: **not run**.",
        f"- Next admitted step: {payload['decision']['next_admitted_step']}.",
        f"- E0 axis-table SHA256: `{payload['e0_axis_table_sha256']}`.",
        "",
        "## Measured",
        "",
        f"- Quick variants: {', '.join('`' + v + '`' for v in payload['quick_variants'])}.",
        f"- Quick selected row: `{payload['quick_selected_rows'][0]['row_id']}`.",
        f"- Fixed* quick grid: `{tuple(payload['fixed_star_grid'])}`.",
        "- Arms exercised for every variant: fixed*, v4_rls, v4_pertuned, native_oracle.",
        "",
        "| variant | fixed success | RLS success | pertuned success | native oracle success | structured attempts | CEM attempts |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for variant, block in payload["per_variant"].items():
        succ = block["arm_success"]
        lines.append(
            f"| `{variant}` | {succ['fixed_star']} | {succ['v4_rls']} | {succ['v4_pertuned']} | "
            f"{succ['native_oracle']} | {block['structured_candidate_attempts']} | {block['cem_candidate_attempts']} |"
        )
    lines.extend(
        [
            "",
            "## Inferred",
            "",
            "The E1 four-arm Chrono protocol is runnable inside the M3248 E0 envelope. The numbers above are smoke context only: the same quick row is used to exercise arm plumbing, so no spread-revival or residual conclusion is admitted.",
            "",
            "A full E1 milestone must separately freeze selection rows, validation rows, the global fixed* selection rule, per-instance tuning rule, native-oracle budget, paired CIs, and pass/negative decision thresholds before any pricing verdict.",
            "",
            "## Claim Boundary",
            "",
            CLAIM_BOUNDARY,
            "",
            "## Artifacts",
            "",
            f"- Preregistration: `{PREREG_JSON.relative_to(REPO_ROOT)}`",
            f"- Quick JSON: `{QUICK_JSON.relative_to(REPO_ROOT)}`",
            f"- Episode rows: `{ROWS_QUICK_CSV.relative_to(REPO_ROOT)}`",
            f"- Metrics: `{METRICS_QUICK_CSV.relative_to(REPO_ROOT)}`",
            f"- Script: `scripts/feasibility_audit/{Path(__file__).name}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write-prereg", action="store_true")
    group.add_argument("--quick", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.write_prereg:
        payload = write_preregistration()
        print(json.dumps({"preregistration": str(PREREG_JSON), "quick_variants": payload["quick_variants"]}))
        return
    if not args.quick:
        raise SystemExit("M3249 only supports --write-prereg or --quick; full E1 must be a separate milestone")
    payload = run_quick()
    print(json.dumps(payload["decision"], ensure_ascii=False, sort_keys=True))
    if not payload["decision"]["status_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
