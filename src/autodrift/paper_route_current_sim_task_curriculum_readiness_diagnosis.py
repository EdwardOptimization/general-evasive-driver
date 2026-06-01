"""Artifact-only readiness diagnosis for current-sim matched-budget training."""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_SHORT_RUN_DIR = Path("runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution")
DEFAULT_MEDIUM_RUN_DIR = Path("runs/m2234_paper_route_current_sim_matched_budget_medium_training_execution")
DEFAULT_OUTPUT_DIR = Path("runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis")
DEFAULT_NEXT_BLOCKER = "m2239-paper-route-current-sim-task-curriculum-readiness-diagnosis-result-audit"
RETURN_FLOOR = 50.0
TERMINATION_FLOOR = 0.4
NEAR_RETURN_GAP = 5.0
NEAR_TERMINATION_GAP = 0.1
LATE_RETURN_REGRESSION = 10.0
LATE_TERMINATION_REGRESSION = 0.25

ROW_FIELDNAMES = [
    "budget_label",
    "total_steps",
    "matrix_id",
    "profile_name",
    "seed_id",
    "status",
    "selected_metrics_finite",
    "readiness_floor_pass",
    "eval_return_mean",
    "eval_termination_rate",
    "eval_steps_mean",
    "eval_lateral_rmse_mean",
    "eval_beta_abs_error_mean",
    "return_floor_margin",
    "termination_floor_margin",
    "return_gap_to_floor",
    "termination_excess_above_floor",
    "floor_fail_reason",
    "near_floor_flag",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

SEED_FIELDNAMES = [
    "budget_label",
    "seed_id",
    "row_count",
    "passing_row_count",
    "readiness_floor_pass_rate",
    "mean_eval_return",
    "mean_eval_termination_rate",
    "mean_return_gap_to_floor",
    "mean_termination_excess_above_floor",
    "dominant_floor_fail_reason",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

BUDGET_DELTA_FIELDNAMES = [
    "profile_name",
    "seed_id",
    "short_total_steps",
    "medium_total_steps",
    "short_eval_return_mean",
    "medium_eval_return_mean",
    "delta_eval_return_mean",
    "short_eval_termination_rate",
    "medium_eval_termination_rate",
    "delta_eval_termination_rate",
    "short_readiness_floor_pass",
    "medium_readiness_floor_pass",
    "floor_transition",
    "return_improved",
    "termination_improved",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

PLATEAU_FIELDNAMES = [
    "budget_label",
    "total_steps",
    "profile_name",
    "seed_id",
    "train_metrics_path",
    "train_metrics_exists",
    "train_metric_row_count",
    "best_rollout_return_mean",
    "best_rollout_return_step",
    "final_rollout_return_mean",
    "last_quarter_rollout_return_mean",
    "best_termination_rate",
    "best_termination_rate_step",
    "final_termination_rate",
    "last_quarter_termination_rate_mean",
    "final_minus_best_return",
    "final_minus_best_termination",
    "late_return_regression",
    "late_termination_regression",
    "plateau_or_late_regression",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _int_or_none(value: Any) -> int | None:
    parsed = _float_or_none(value)
    if parsed is None:
        return None
    return int(parsed)


def _mean(values: Iterable[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not finite:
        return None
    return sum(finite) / len(finite)


def _counter_mode(values: Iterable[str]) -> str:
    counter = Counter(value for value in values if value)
    if not counter:
        return ""
    return counter.most_common(1)[0][0]


def _floor_fail_reason(
    *,
    status: str,
    selected_metrics_finite: bool,
    readiness_floor_pass: bool,
    return_gap: float | None,
    termination_excess: float | None,
) -> str:
    if status != "completed" or not selected_metrics_finite:
        return "incomplete_or_nonfinite"
    if readiness_floor_pass:
        return "pass"
    return_failed = return_gap is None or return_gap > 0.0
    termination_failed = termination_excess is None or termination_excess > 0.0
    if return_failed and termination_failed:
        return "return_and_termination"
    if return_failed:
        return "return_only"
    if termination_failed:
        return "termination_only"
    return "floor_boolean_mismatch"


def _row_diagnosis(
    *,
    row: Mapping[str, Any],
    budget_label: str,
    total_steps: int,
) -> dict[str, Any]:
    ret = _float_or_none(row.get("eval_return_mean"))
    termination = _float_or_none(row.get("eval_termination_rate"))
    return_floor_margin = None if ret is None else ret - RETURN_FLOOR
    termination_floor_margin = None if termination is None else TERMINATION_FLOOR - termination
    return_gap = None if ret is None else max(0.0, RETURN_FLOOR - ret)
    termination_excess = None if termination is None else max(0.0, termination - TERMINATION_FLOOR)
    status = str(row.get("status", ""))
    selected_metrics_finite = _bool(row.get("selected_metrics_finite"))
    readiness_floor_pass = _bool(row.get("readiness_floor_pass"))
    fail_reason = _floor_fail_reason(
        status=status,
        selected_metrics_finite=selected_metrics_finite,
        readiness_floor_pass=readiness_floor_pass,
        return_gap=return_gap,
        termination_excess=termination_excess,
    )
    near_floor = bool(
        fail_reason != "pass"
        and return_gap is not None
        and termination_excess is not None
        and return_gap <= NEAR_RETURN_GAP
        and termination_excess <= NEAR_TERMINATION_GAP
    )
    return {
        "budget_label": budget_label,
        "total_steps": int(total_steps),
        "matrix_id": row.get("matrix_id", ""),
        "profile_name": row.get("profile_name", ""),
        "seed_id": _int_or_none(row.get("seed_id")),
        "status": status,
        "selected_metrics_finite": selected_metrics_finite,
        "readiness_floor_pass": readiness_floor_pass,
        "eval_return_mean": ret,
        "eval_termination_rate": termination,
        "eval_steps_mean": _float_or_none(row.get("eval_steps_mean")),
        "eval_lateral_rmse_mean": _float_or_none(row.get("eval_lateral_rmse_mean")),
        "eval_beta_abs_error_mean": _float_or_none(row.get("eval_beta_abs_error_mean")),
        "return_floor_margin": return_floor_margin,
        "termination_floor_margin": termination_floor_margin,
        "return_gap_to_floor": return_gap,
        "termination_excess_above_floor": termination_excess,
        "floor_fail_reason": fail_reason,
        "near_floor_flag": near_floor,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _seed_diagnosis(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("budget_label", "")), int(row.get("seed_id", -1)))].append(row)
    output: list[dict[str, Any]] = []
    for (budget_label, seed_id), group in sorted(grouped.items()):
        row_count = len(group)
        passing = sum(1 for row in group if _bool(row.get("readiness_floor_pass")))
        output.append(
            {
                "budget_label": budget_label,
                "seed_id": seed_id,
                "row_count": row_count,
                "passing_row_count": passing,
                "readiness_floor_pass_rate": passing / row_count if row_count else 0.0,
                "mean_eval_return": _mean(_float_or_none(row.get("eval_return_mean")) for row in group),
                "mean_eval_termination_rate": _mean(
                    _float_or_none(row.get("eval_termination_rate")) for row in group
                ),
                "mean_return_gap_to_floor": _mean(
                    _float_or_none(row.get("return_gap_to_floor")) for row in group
                ),
                "mean_termination_excess_above_floor": _mean(
                    _float_or_none(row.get("termination_excess_above_floor")) for row in group
                ),
                "dominant_floor_fail_reason": _counter_mode(str(row.get("floor_fail_reason", "")) for row in group),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def _budget_delta(short_rows: Sequence[Mapping[str, Any]], medium_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    short_by_key = {(str(row.get("profile_name", "")), int(row.get("seed_id", -1))): row for row in short_rows}
    medium_by_key = {(str(row.get("profile_name", "")), int(row.get("seed_id", -1))): row for row in medium_rows}
    keys = sorted(set(short_by_key) | set(medium_by_key))
    output: list[dict[str, Any]] = []
    for profile_name, seed_id in keys:
        short = short_by_key.get((profile_name, seed_id), {})
        medium = medium_by_key.get((profile_name, seed_id), {})
        short_return = _float_or_none(short.get("eval_return_mean"))
        medium_return = _float_or_none(medium.get("eval_return_mean"))
        short_term = _float_or_none(short.get("eval_termination_rate"))
        medium_term = _float_or_none(medium.get("eval_termination_rate"))
        short_floor = _bool(short.get("readiness_floor_pass"))
        medium_floor = _bool(medium.get("readiness_floor_pass"))
        if short_floor and medium_floor:
            floor_transition = "unchanged_pass"
        elif short_floor and not medium_floor:
            floor_transition = "pass_to_fail"
        elif not short_floor and medium_floor:
            floor_transition = "fail_to_pass"
        else:
            floor_transition = "unchanged_fail"
        output.append(
            {
                "profile_name": profile_name,
                "seed_id": seed_id,
                "short_total_steps": _int_or_none(short.get("total_steps")),
                "medium_total_steps": _int_or_none(medium.get("total_steps")),
                "short_eval_return_mean": short_return,
                "medium_eval_return_mean": medium_return,
                "delta_eval_return_mean": None if short_return is None or medium_return is None else medium_return - short_return,
                "short_eval_termination_rate": short_term,
                "medium_eval_termination_rate": medium_term,
                "delta_eval_termination_rate": None if short_term is None or medium_term is None else medium_term - short_term,
                "short_readiness_floor_pass": short_floor,
                "medium_readiness_floor_pass": medium_floor,
                "floor_transition": floor_transition,
                "return_improved": bool(short_return is not None and medium_return is not None and medium_return > short_return),
                "termination_improved": bool(short_term is not None and medium_term is not None and medium_term < short_term),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def _metric_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv_rows(path)


def _best_by(rows: Sequence[Mapping[str, Any]], key: str, *, reverse: bool) -> tuple[float | None, int | None]:
    best_value: float | None = None
    best_step: int | None = None
    for row in rows:
        value = _float_or_none(row.get(key))
        if value is None:
            continue
        if best_value is None or (value > best_value if reverse else value < best_value):
            best_value = value
            best_step = _int_or_none(row.get("step"))
    return best_value, best_step


def _training_plateau_row(*, run_row: Mapping[str, Any], budget_label: str, total_steps: int) -> dict[str, Any]:
    profile_name = str(run_row.get("profile_name", ""))
    seed_id = _int_or_none(run_row.get("seed_id"))
    run_dir = Path(str(run_row.get("run_dir", "")))
    metrics_path = run_dir / "train_metrics.csv"
    metric_rows = _metric_rows(metrics_path)
    final = metric_rows[-1] if metric_rows else {}
    quarter_count = max(1, len(metric_rows) // 4) if metric_rows else 0
    last_quarter = metric_rows[-quarter_count:] if quarter_count else []
    best_return, best_return_step = _best_by(metric_rows, "rollout_return_mean", reverse=True)
    best_term, best_term_step = _best_by(metric_rows, "termination_rate", reverse=False)
    final_return = _float_or_none(final.get("rollout_return_mean"))
    final_term = _float_or_none(final.get("termination_rate"))
    final_minus_best_return = None if final_return is None or best_return is None else final_return - best_return
    final_minus_best_term = None if final_term is None or best_term is None else final_term - best_term
    late_return_regression = bool(final_minus_best_return is not None and final_minus_best_return <= -LATE_RETURN_REGRESSION)
    late_term_regression = bool(final_minus_best_term is not None and final_minus_best_term >= LATE_TERMINATION_REGRESSION)
    return {
        "budget_label": budget_label,
        "total_steps": int(total_steps),
        "profile_name": profile_name,
        "seed_id": seed_id,
        "train_metrics_path": str(metrics_path),
        "train_metrics_exists": metrics_path.exists(),
        "train_metric_row_count": len(metric_rows),
        "best_rollout_return_mean": best_return,
        "best_rollout_return_step": best_return_step,
        "final_rollout_return_mean": final_return,
        "last_quarter_rollout_return_mean": _mean(
            _float_or_none(row.get("rollout_return_mean")) for row in last_quarter
        ),
        "best_termination_rate": best_term,
        "best_termination_rate_step": best_term_step,
        "final_termination_rate": final_term,
        "last_quarter_termination_rate_mean": _mean(
            _float_or_none(row.get("termination_rate")) for row in last_quarter
        ),
        "final_minus_best_return": final_minus_best_return,
        "final_minus_best_termination": final_minus_best_term,
        "late_return_regression": late_return_regression,
        "late_termination_regression": late_term_regression,
        "plateau_or_late_regression": late_return_regression or late_term_regression,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _profile_pass_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"row_count": 0, "passing_row_count": 0})
    for row in rows:
        profile = str(row.get("profile_name", ""))
        grouped[profile]["row_count"] += 1
        grouped[profile]["passing_row_count"] += int(_bool(row.get("readiness_floor_pass")))
    return {key: dict(value) for key, value in sorted(grouped.items())}


def _route_classification(
    *,
    missing_artifact_count: int,
    row_diagnosis: Sequence[Mapping[str, Any]],
    seed_diagnosis: Sequence[Mapping[str, Any]],
    budget_delta: Sequence[Mapping[str, Any]],
    training_plateau: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if missing_artifact_count:
        return {
            "primary": "insufficient_existing_artifacts",
            "secondary": [],
            "reason": "At least one required input artifact is missing.",
        }

    medium_rows = [row for row in row_diagnosis if row.get("budget_label") == "medium_v1"]
    medium_failed = [row for row in medium_rows if not _bool(row.get("readiness_floor_pass"))]
    medium_fail_count = len(medium_failed)
    medium_near_count = sum(1 for row in medium_failed if _bool(row.get("near_floor_flag")))
    medium_return_fail_count = sum(
        1 for row in medium_failed if _float_or_none(row.get("return_gap_to_floor")) not in (None, 0.0)
    )
    medium_term_fail_count = sum(
        1 for row in medium_failed if _float_or_none(row.get("termination_excess_above_floor")) not in (None, 0.0)
    )
    plateau_count = sum(1 for row in training_plateau if _bool(row.get("plateau_or_late_regression")))
    plateau_ratio = plateau_count / len(training_plateau) if training_plateau else 0.0
    fail_to_pass_count = sum(1 for row in budget_delta if row.get("floor_transition") == "fail_to_pass")
    pass_to_fail_count = sum(1 for row in budget_delta if row.get("floor_transition") == "pass_to_fail")
    improved_return_count = sum(1 for row in budget_delta if _bool(row.get("return_improved")))
    improved_term_count = sum(1 for row in budget_delta if _bool(row.get("termination_improved")))
    seed_pass_counts = [int(row.get("passing_row_count", 0)) for row in seed_diagnosis if row.get("budget_label") == "medium_v1"]
    seed_pass_range = max(seed_pass_counts) - min(seed_pass_counts) if seed_pass_counts else 0

    secondary: list[str] = []
    if seed_pass_range >= 3:
        secondary.append("task_seed_heterogeneity")
    if medium_near_count >= max(1, medium_fail_count // 2):
        secondary.append("readiness_floor_calibration")
    if medium_term_fail_count > medium_return_fail_count:
        secondary.append("reward_or_termination_repair")
    if fail_to_pass_count <= pass_to_fail_count and improved_return_count >= len(budget_delta) // 2:
        secondary.append("task_curriculum_repair")

    if plateau_ratio >= 0.5:
        primary = "training_plateau_or_late_regression"
        reason = (
            f"{plateau_count}/{len(training_plateau)} training traces show late return or termination regression; "
            "another blind budget increase is not an admissible next step."
        )
    elif seed_pass_range >= 3:
        primary = "task_seed_heterogeneity"
        reason = "Medium-v1 readiness pass counts are concentrated by seed."
    elif medium_near_count >= max(1, medium_fail_count // 2):
        primary = "readiness_floor_calibration"
        reason = "Most failing medium-v1 rows are near the readiness floor."
    elif medium_term_fail_count > medium_return_fail_count:
        primary = "reward_or_termination_repair"
        reason = "Medium-v1 failures are more termination-driven than return-driven."
    else:
        primary = "task_curriculum_repair"
        reason = "Repeated matched-budget failures remain broad after short-to-medium budget increase."

    return {
        "primary": primary,
        "secondary": sorted(set(item for item in secondary if item != primary)),
        "reason": reason,
        "diagnostic_counts": {
            "medium_fail_count": medium_fail_count,
            "medium_near_floor_count": medium_near_count,
            "medium_return_fail_count": medium_return_fail_count,
            "medium_termination_fail_count": medium_term_fail_count,
            "training_plateau_count": plateau_count,
            "training_plateau_ratio": plateau_ratio,
            "fail_to_pass_count": fail_to_pass_count,
            "pass_to_fail_count": pass_to_fail_count,
            "improved_return_count": improved_return_count,
            "improved_termination_count": improved_term_count,
            "medium_seed_pass_range": seed_pass_range,
        },
    }


def _claim_rows(route: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_readiness_diagnosis",
            "admissible": True,
            "reason": f"Route classification is {route.get('primary')}.",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2238 diagnoses below-floor training artifacts and does not compare admissible deployed controllers.",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "All profiles remain below readiness floor; M2238 does not select a winner.",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2238 runs no history-necessity intervention.",
        },
    ]


def run_readiness_diagnosis(
    *,
    short_run_dir: Path | str = DEFAULT_SHORT_RUN_DIR,
    medium_run_dir: Path | str = DEFAULT_MEDIUM_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    short_dir = Path(short_run_dir)
    medium_dir = Path(medium_run_dir)

    budget_dirs = {
        "short_v0": short_dir,
        "medium_v1": medium_dir,
    }
    budget_steps = {
        "short_v0": 8192,
        "medium_v1": 32768,
    }

    missing_artifacts: list[str] = []
    row_diagnosis: list[dict[str, Any]] = []
    raw_run_rows: dict[str, list[dict[str, str]]] = {}
    for budget_label, run_dir in budget_dirs.items():
        run_rows_path = run_dir / "run_rows.csv"
        if not run_rows_path.exists():
            missing_artifacts.append(str(run_rows_path))
            raw_run_rows[budget_label] = []
            continue
        raw_run_rows[budget_label] = read_csv_rows(run_rows_path)
        for row in raw_run_rows[budget_label]:
            row_diagnosis.append(
                _row_diagnosis(row=row, budget_label=budget_label, total_steps=budget_steps[budget_label])
            )

    short_rows = [row for row in row_diagnosis if row["budget_label"] == "short_v0"]
    medium_rows = [row for row in row_diagnosis if row["budget_label"] == "medium_v1"]
    seed_rows = _seed_diagnosis(row_diagnosis)
    delta_rows = _budget_delta(short_rows, medium_rows)

    plateau_rows: list[dict[str, Any]] = []
    for budget_label, run_rows in raw_run_rows.items():
        for row in run_rows:
            plateau_row = _training_plateau_row(
                run_row=row,
                budget_label=budget_label,
                total_steps=budget_steps[budget_label],
            )
            plateau_rows.append(plateau_row)
            if not plateau_row["train_metrics_exists"]:
                missing_artifacts.append(str(plateau_row["train_metrics_path"]))

    route = _route_classification(
        missing_artifact_count=len(missing_artifacts),
        row_diagnosis=row_diagnosis,
        seed_diagnosis=seed_rows,
        budget_delta=delta_rows,
        training_plateau=plateau_rows,
    )
    claim_rows = _claim_rows(route)
    floor_counts = {
        "short_v0": _profile_pass_counts(short_rows),
        "medium_v1": _profile_pass_counts(medium_rows),
    }
    late_regression_row_count = sum(1 for row in plateau_rows if _bool(row.get("plateau_or_late_regression")))
    profile_floor_pass_count = {
        budget: sum(1 for value in counts.values() if value["passing_row_count"] >= 2)
        for budget, counts in floor_counts.items()
    }
    floor_fail_reason_counts = Counter(str(row.get("floor_fail_reason", "")) for row in row_diagnosis)
    floor_transition_counts = Counter(str(row.get("floor_transition", "")) for row in delta_rows)

    result_class = (
        "current_sim_task_curriculum_readiness_diagnosis_artifact_gap"
        if missing_artifacts
        else "current_sim_task_curriculum_readiness_diagnosis_pass"
    )
    summary = {
        "result_class": result_class,
        "created_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "short_run_dir": str(short_dir),
        "medium_run_dir": str(medium_dir),
        "row_diagnosis_count": len(row_diagnosis),
        "seed_diagnosis_count": len(seed_rows),
        "budget_delta_count": len(delta_rows),
        "training_plateau_row_count": len(plateau_rows),
        "late_regression_row_count": late_regression_row_count,
        "missing_artifact_count": len(missing_artifacts),
        "missing_artifacts": missing_artifacts,
        "floor_thresholds": {
            "return_floor": RETURN_FLOOR,
            "termination_floor": TERMINATION_FLOOR,
            "near_return_gap": NEAR_RETURN_GAP,
            "near_termination_gap": NEAR_TERMINATION_GAP,
        },
        "profile_floor_pass_count": profile_floor_pass_count,
        "profile_floor_pass_counts_by_budget": floor_counts,
        "floor_fail_reason_counts": dict(sorted(floor_fail_reason_counts.items())),
        "floor_transition_counts": dict(sorted(floor_transition_counts.items())),
        "route_classification": route,
        "guardrail": {
            "training_started": False,
            "rollout_started": False,
            "environment_reset_started": False,
            "ppo_started": False,
            "ranking_admissible": False,
            "winner_selected": False,
            "controller_family_ranking_claim_made": False,
            "finite_window_vs_gru_conclusion_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        },
    }

    write_csv_rows(output / "row_diagnosis.csv", row_diagnosis, fieldnames=ROW_FIELDNAMES)
    write_csv_rows(output / "seed_diagnosis.csv", seed_rows, fieldnames=SEED_FIELDNAMES)
    write_csv_rows(output / "budget_delta.csv", delta_rows, fieldnames=BUDGET_DELTA_FIELDNAMES)
    write_csv_rows(output / "training_plateau.csv", plateau_rows, fieldnames=PLATEAU_FIELDNAMES)
    write_csv_rows(output / "claim_audit.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "status": "completed" if not missing_artifacts else "failed",
            "task_id": "m2238-paper-route-current-sim-task-curriculum-readiness-diagnosis-implementation",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--short-run-dir", type=Path, default=DEFAULT_SHORT_RUN_DIR)
    parser.add_argument("--medium-run-dir", type=Path, default=DEFAULT_MEDIUM_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = run_readiness_diagnosis(
        short_run_dir=args.short_run_dir,
        medium_run_dir=args.medium_run_dir,
        output_dir=args.output_dir,
        next_blocker=args.next_blocker,
    )
    print(
        "M2238 readiness diagnosis:",
        summary["result_class"],
        "route=",
        summary["route_classification"]["primary"],
    )
    return 0 if summary["missing_artifact_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
