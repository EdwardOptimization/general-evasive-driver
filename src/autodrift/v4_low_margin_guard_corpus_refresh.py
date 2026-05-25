"""Select source-diverse low-margin guard rows from v4 reference replay."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json


ACTIVE_REFERENCE_SEED = 77025
ACTIVE_REFERENCE_SOURCE_INDEX = 12
ACTIVE_REFERENCE_STEP = 24
DEFAULT_DIAGNOSTIC_THRESHOLDS = (5e-5, 1e-4, 5e-4, 1e-3, 1e-2, 1e-1, 2e-1)

CANDIDATE_FIELDS = [
    "contrast_group_id",
    "seed",
    "source_index",
    "step",
    "fault_family_pair",
    "alpha",
    "min_clearance_margin",
    "success",
    "collision",
    "terminal_reason",
    "guard_reason",
    "active_reference",
]

BAND_FIELDS = [
    "threshold",
    "row_count",
    "fresh_row_count",
    "unique_seed_count",
    "unique_source_index_count",
    "unique_fault_pair_count",
    "max_seed_dominance",
    "max_source_index_dominance",
    "max_fault_pair_dominance",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if np.isfinite(parsed) else float(default)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y"}


def parse_float_list(value: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in value.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("at least one threshold is required")
    return values


def is_active_reference(row: dict[str, Any]) -> bool:
    return (
        int(row.get("seed", -1)) == ACTIVE_REFERENCE_SEED
        and int(row.get("source_index", -1)) == ACTIVE_REFERENCE_SOURCE_INDEX
        and int(row.get("step", -1)) == ACTIVE_REFERENCE_STEP
    )


def row_metadata_complete(row: dict[str, Any]) -> bool:
    required = ("seed", "source_index", "step", "fault_family_pair")
    return all(str(row.get(key, "")).strip() for key in required)


def max_share(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return float(max(counts.values()) / len(rows)) if counts else 0.0


def unique_count(rows: list[dict[str, Any]], key: str) -> int:
    return len({str(row.get(key, "")) for row in rows})


def normalize_replay_row(row: dict[str, str], *, reason: str) -> dict[str, Any]:
    margin = finite_float(row.get("min_clearance_margin"))
    output = {
        "contrast_group_id": str(row.get("contrast_group_id", "")),
        "seed": int(float(row.get("seed", -1))),
        "source_index": int(float(row.get("source_index", -1))),
        "step": int(float(row.get("step", -1))),
        "fault_family_pair": str(row.get("fault_family_pair", "")),
        "alpha": finite_float(row.get("alpha")),
        "min_clearance_margin": margin,
        "success": parse_bool(row.get("success", False)),
        "collision": parse_bool(row.get("collision", False)),
        "terminal_reason": str(row.get("terminal_reason", "")),
        "guard_reason": str(reason),
    }
    output["active_reference"] = is_active_reference(output)
    return output


def normal_alpha_rows(rows: list[dict[str, str]], *, alpha: float) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for row in rows:
        if str(row.get("branch", "")) != "normal":
            continue
        if abs(finite_float(row.get("alpha")) - float(alpha)) > 1e-12:
            continue
        selected.append(row)
    return selected


def candidate_rows(
    rows: list[dict[str, str]],
    *,
    alpha: float,
    max_diagnostic_threshold: float,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in normal_alpha_rows(rows, alpha=alpha):
        if not row_metadata_complete(row):
            continue
        margin = finite_float(row.get("min_clearance_margin"))
        if not np.isfinite(margin) or margin < 0.0:
            continue
        if not parse_bool(row.get("success", False)):
            continue
        if parse_bool(row.get("collision", False)):
            continue
        active = is_active_reference(row)
        if margin > float(max_diagnostic_threshold) and not active:
            continue
        reason = "active_reference" if active else "diagnostic_margin"
        if margin <= float(max_diagnostic_threshold):
            reason = "active_reference|diagnostic_margin" if active else "diagnostic_margin"
        output.append(normalize_replay_row(row, reason=reason))
    return output


def accepted_rows(
    rows: list[dict[str, Any]],
    *,
    primary_margin_threshold: float,
) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    for row in rows:
        margin = finite_float(row.get("min_clearance_margin"))
        active = bool(row.get("active_reference", False))
        if margin <= float(primary_margin_threshold) or active:
            next_row = dict(row)
            next_row["guard_reason"] = (
                "active_reference|primary_low_margin" if active and margin <= primary_margin_threshold
                else "active_reference" if active
                else "primary_low_margin"
            )
            accepted.append(next_row)
    return accepted


def fresh_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not bool(row.get("active_reference", False))]


def band_summary(
    rows: list[dict[str, Any]],
    *,
    thresholds: tuple[float, ...],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for threshold in thresholds:
        selected = [row for row in rows if finite_float(row.get("min_clearance_margin")) <= float(threshold)]
        fresh = fresh_rows(selected)
        output.append(
            {
                "threshold": float(threshold),
                "row_count": int(len(selected)),
                "fresh_row_count": int(len(fresh)),
                "unique_seed_count": unique_count(fresh, "seed"),
                "unique_source_index_count": unique_count(fresh, "source_index"),
                "unique_fault_pair_count": unique_count(fresh, "fault_family_pair"),
                "max_seed_dominance": max_share(fresh, "seed"),
                "max_source_index_dominance": max_share(fresh, "source_index"),
                "max_fault_pair_dominance": max_share(fresh, "fault_family_pair"),
            }
        )
    return output


def summarize_accepted(
    rows: list[dict[str, Any]],
    *,
    min_rows: int,
    min_seeds: int,
    min_source_indices: int,
    min_fault_pairs: int,
    max_seed_dominance: float,
    max_source_index_dominance: float,
    max_fault_pair_dominance: float,
) -> dict[str, Any]:
    fresh = fresh_rows(rows)
    summary = {
        "accepted_low_margin_guard_row_count": int(len(rows)),
        "fresh_accepted_low_margin_guard_row_count": int(len(fresh)),
        "active_reference_row_count": int(len(rows) - len(fresh)),
        "unique_seed_count": unique_count(fresh, "seed"),
        "unique_source_index_count": unique_count(fresh, "source_index"),
        "unique_fault_pair_count": unique_count(fresh, "fault_family_pair"),
        "max_seed_dominance": max_share(fresh, "seed"),
        "max_source_index_dominance": max_share(fresh, "source_index"),
        "max_fault_pair_dominance": max_share(fresh, "fault_family_pair"),
        "min_row_requirement": int(min_rows),
        "min_seed_requirement": int(min_seeds),
        "min_source_index_requirement": int(min_source_indices),
        "min_fault_pair_requirement": int(min_fault_pairs),
        "max_seed_dominance_requirement": float(max_seed_dominance),
        "max_source_index_dominance_requirement": float(max_source_index_dominance),
        "max_fault_pair_dominance_requirement": float(max_fault_pair_dominance),
    }
    pass_gate = (
        len(fresh) >= int(min_rows)
        and summary["unique_seed_count"] >= int(min_seeds)
        and summary["unique_source_index_count"] >= int(min_source_indices)
        and summary["unique_fault_pair_count"] >= int(min_fault_pairs)
        and summary["max_seed_dominance"] <= float(max_seed_dominance)
        and summary["max_source_index_dominance"] <= float(max_source_index_dominance)
        and summary["max_fault_pair_dominance"] <= float(max_fault_pair_dominance)
    )
    summary["low_margin_corpus_pass"] = bool(pass_gate)
    return summary


def classify_result(
    *,
    reference_contract_ok: bool,
    accepted_summary: dict[str, Any],
    candidates: list[dict[str, Any]],
    diagnostic_rows: int,
) -> str:
    if not bool(reference_contract_ok):
        return "v4_low_margin_guard_refresh_contract_violation"
    if not candidates:
        return "v4_low_margin_guard_refresh_low_margin_rows_absent"
    if bool(accepted_summary.get("low_margin_corpus_pass", False)):
        return "v4_low_margin_guard_refresh_source_diverse_pass"
    if int(accepted_summary.get("fresh_accepted_low_margin_guard_row_count", 0)) == 0:
        if int(diagnostic_rows) > 0:
            return "v4_low_margin_guard_refresh_diagnostic_band_only"
        return "v4_low_margin_guard_refresh_low_margin_rows_absent"
    return "v4_low_margin_guard_refresh_single_source_or_sparse"


def load_reference_summary(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def reference_contract_ok(summary: dict[str, Any]) -> bool:
    if not summary:
        return True
    return not (
        parse_bool(summary.get("actor_backbone_changed", False))
        or parse_bool(summary.get("base_residual_head_changed", False))
        or parse_bool(summary.get("optimizer_started", False))
        or parse_bool(summary.get("training_started", False))
        or parse_bool(summary.get("ppo_used", False))
        or parse_bool(summary.get("promoted", False))
        or parse_bool(summary.get("checkpoint_promoted", False))
    )


def run_low_margin_guard_corpus_refresh(
    *,
    reference_replay_rows_path: Path,
    run_dir: Path,
    reference_replay_summary_path: Path | None = None,
    alpha: float = 0.2,
    primary_margin_threshold: float = 5e-5,
    diagnostic_thresholds: tuple[float, ...] = DEFAULT_DIAGNOSTIC_THRESHOLDS,
    min_rows: int = 80,
    min_seeds: int = 8,
    min_source_indices: int = 8,
    min_fault_pairs: int = 4,
    max_seed_dominance: float = 0.25,
    max_source_index_dominance: float = 0.15,
    max_fault_pair_dominance: float = 0.40,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    replay_rows = read_csv_rows(reference_replay_rows_path)
    thresholds = tuple(sorted(float(value) for value in diagnostic_thresholds))
    max_threshold = max(thresholds) if thresholds else float(primary_margin_threshold)
    candidates = candidate_rows(replay_rows, alpha=float(alpha), max_diagnostic_threshold=max_threshold)
    accepted = accepted_rows(candidates, primary_margin_threshold=float(primary_margin_threshold))
    bands = band_summary(candidates, thresholds=thresholds)
    accepted_summary = summarize_accepted(
        accepted,
        min_rows=min_rows,
        min_seeds=min_seeds,
        min_source_indices=min_source_indices,
        min_fault_pairs=min_fault_pairs,
        max_seed_dominance=max_seed_dominance,
        max_source_index_dominance=max_source_index_dominance,
        max_fault_pair_dominance=max_fault_pair_dominance,
    )
    reference_summary = load_reference_summary(reference_replay_summary_path)
    contract_ok = reference_contract_ok(reference_summary)
    diagnostic_rows = max((int(row["fresh_row_count"]) for row in bands), default=0)
    result_class = classify_result(
        reference_contract_ok=contract_ok,
        accepted_summary=accepted_summary,
        candidates=candidates,
        diagnostic_rows=diagnostic_rows,
    )

    write_csv_rows(run_dir / "low_margin_guard_candidates.csv", candidates, fieldnames=CANDIDATE_FIELDS)
    write_csv_rows(run_dir / "accepted_low_margin_guard_rows.csv", accepted, fieldnames=CANDIDATE_FIELDS)
    write_csv_rows(run_dir / "diagnostic_margin_bands.csv", bands, fieldnames=BAND_FIELDS)
    summary = {
        "run_type": "v4_low_margin_guard_corpus_refresh",
        "reference_replay_rows": reference_replay_rows_path,
        "reference_replay_summary": reference_replay_summary_path,
        "alpha": float(alpha),
        "primary_margin_threshold": float(primary_margin_threshold),
        "diagnostic_thresholds": [float(value) for value in thresholds],
        "reference_replay_row_count": int(len(replay_rows)),
        "candidate_row_count": int(len(candidates)),
        "fresh_candidate_row_count": int(len(fresh_rows(candidates))),
        "reference_contract_ok": bool(contract_ok),
        "reference_actor_backbone_changed": bool(reference_summary.get("actor_backbone_changed", False)),
        "reference_training_started": bool(reference_summary.get("training_started", False)),
        "reference_optimizer_started": bool(reference_summary.get("optimizer_started", False)),
        "reference_ppo_used": bool(reference_summary.get("ppo_used", False)),
        "reference_promoted": bool(reference_summary.get("promoted", False)),
        **accepted_summary,
        "result_class": result_class,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "low_margin_guard_candidates_csv": run_dir / "low_margin_guard_candidates.csv",
        "accepted_low_margin_guard_rows_csv": run_dir / "accepted_low_margin_guard_rows.csv",
        "diagnostic_margin_bands_csv": run_dir / "diagnostic_margin_bands.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select source-diverse low-margin guard rows from v4 replay.")
    parser.add_argument("--reference-replay-rows", type=Path, required=True)
    parser.add_argument("--reference-replay-summary", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--primary-margin-threshold", type=float, default=5e-5)
    parser.add_argument("--diagnostic-thresholds", type=parse_float_list, default=DEFAULT_DIAGNOSTIC_THRESHOLDS)
    parser.add_argument("--min-rows", type=int, default=80)
    parser.add_argument("--min-seeds", type=int, default=8)
    parser.add_argument("--min-source-indices", type=int, default=8)
    parser.add_argument("--min-fault-pairs", type=int, default=4)
    parser.add_argument("--max-seed-dominance", type=float, default=0.25)
    parser.add_argument("--max-source-index-dominance", type=float, default=0.15)
    parser.add_argument("--max-fault-pair-dominance", type=float, default=0.40)
    args = parser.parse_args()
    summary = run_low_margin_guard_corpus_refresh(
        reference_replay_rows_path=args.reference_replay_rows,
        reference_replay_summary_path=args.reference_replay_summary,
        run_dir=args.run_dir,
        alpha=args.alpha,
        primary_margin_threshold=args.primary_margin_threshold,
        diagnostic_thresholds=tuple(args.diagnostic_thresholds),
        min_rows=args.min_rows,
        min_seeds=args.min_seeds,
        min_source_indices=args.min_source_indices,
        min_fault_pairs=args.min_fault_pairs,
        max_seed_dominance=args.max_seed_dominance,
        max_source_index_dominance=args.max_source_index_dominance,
        max_fault_pair_dominance=args.max_fault_pair_dominance,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
