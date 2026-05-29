"""Select a source-balanced diagnostic recoverable active set."""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, write_csv_rows, write_json


DEFAULT_INPUT_DIR = Path("runs/m1560_recoverable_active_set_generator_smoke")
DEFAULT_RUN_DIR = Path("runs/m1563_source_balanced_recoverable_active_set_selector")
PREDECISION_WINDOWS = {"reveal", "reveal_plus_4", "decision_minus_24", "decision_minus_16", "decision_minus_8"}
MAX_PER_SOURCE_FAMILY = 12
MAX_PER_ANCHOR_WINDOW = 12
MAX_SELECTED_ROWS = 48
MIN_SELECTED_ROWS = 40
MIN_SELECTED_STRONG_ROWS = 24
MIN_SELECTED_PREDECISION_ROWS = 32
MIN_SELECTED_SOURCE_FAMILIES = 5
MIN_SELECTED_WINDOWS = 5
MAX_SELECTED_SOURCE_FAMILY_SHARE = 0.30
MAX_SELECTED_WINDOW_SHARE = 0.35
MIN_SELECTED_COLLISION_FLIP_ANCHORS = 8
MIN_SELECTED_SUCCESS_FLIP_ANCHORS = 8
MIN_INPUT_RECOVERABLE_ROWS = 80

GUARDRAILS = {
    "candidate_materialized": False,
    "training_started": False,
    "evaluation_started": False,
    "replay_started": False,
    "simulator_rerun_started": False,
    "history_interventions_executed": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "training_corpus_exported": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _max_share(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return max((count / max(1, total) for count in counts.values()), default=0.0)


def _rank_key(
    row: Mapping[str, Any],
    *,
    source_pool_counts: Counter[str],
    window_pool_counts: Counter[str],
) -> tuple[Any, ...]:
    source_family = str(row.get("source_family", ""))
    anchor_window = str(row.get("anchor_window", ""))
    return (
        _as_bool(row.get("strong_recoverable_boundary")),
        _as_int(row.get("collision_flip_count")),
        _as_int(row.get("success_flip_count")),
        _as_float(row.get("max_abs_terminal_margin_gap")),
        anchor_window in PREDECISION_WINDOWS,
        1.0 / max(1, source_pool_counts[source_family]),
        1.0 / max(1, window_pool_counts[anchor_window]),
        -abs(_as_float(row.get("normal_terminal_margin"))),
        str(row.get("anchor_id", "")),
    )


def _selection_score(
    row: Mapping[str, Any],
    *,
    source_pool_counts: Counter[str],
    window_pool_counts: Counter[str],
) -> float:
    return (
        (1000.0 if _as_bool(row.get("strong_recoverable_boundary")) else 0.0)
        + 100.0 * _as_int(row.get("collision_flip_count"))
        + 50.0 * _as_int(row.get("success_flip_count"))
        + 10.0 * _as_float(row.get("max_abs_terminal_margin_gap"))
        + (1.0 if str(row.get("anchor_window", "")) in PREDECISION_WINDOWS else 0.0)
        + 1.0 / max(1, source_pool_counts[str(row.get("source_family", ""))])
        + 1.0 / max(1, window_pool_counts[str(row.get("anchor_window", ""))])
    )


def _selected_row(
    row: Mapping[str, Any],
    *,
    selector_order: int,
    selection_phase: str,
    source_pool_counts: Counter[str],
    window_pool_counts: Counter[str],
) -> dict[str, Any]:
    result = dict(row)
    result.update(
        {
            "selector_order": int(selector_order),
            "selector_phase": selection_phase,
            "selector_score": _selection_score(
                row,
                source_pool_counts=source_pool_counts,
                window_pool_counts=window_pool_counts,
            ),
        }
    )
    return result


def recoverable_candidates(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return rows that satisfy the M1562 recoverable-boundary candidate rule."""

    return [dict(row) for row in rows if _as_bool(row.get("recoverable_boundary"))]


def select_source_balanced_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    max_per_source_family: int = MAX_PER_SOURCE_FAMILY,
    max_per_anchor_window: int = MAX_PER_ANCHOR_WINDOW,
    max_selected_rows: int = MAX_SELECTED_ROWS,
    min_selected_rows: int = MIN_SELECTED_ROWS,
) -> list[dict[str, Any]]:
    """Select a deterministic compact active set with source/window caps."""

    candidates = recoverable_candidates(rows)
    source_pool_counts = Counter(str(row.get("source_family", "")) for row in candidates)
    window_pool_counts = Counter(str(row.get("anchor_window", "")) for row in candidates)
    if not candidates or not source_pool_counts or not window_pool_counts:
        return []

    feasible_capacity = min(
        int(max_selected_rows),
        sum(min(count, int(max_per_source_family)) for count in source_pool_counts.values()),
        sum(min(count, int(max_per_anchor_window)) for count in window_pool_counts.values()),
    )
    target_selected_rows = min(int(min_selected_rows), feasible_capacity)
    source_target = math.ceil(feasible_capacity / max(1, len(source_pool_counts)))
    window_target = math.ceil(feasible_capacity / max(1, len(window_pool_counts)))

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    source_counts: Counter[str] = Counter()
    window_counts: Counter[str] = Counter()

    def can_select(row: Mapping[str, Any]) -> bool:
        anchor_id = str(row.get("anchor_id", ""))
        source_family = str(row.get("source_family", ""))
        anchor_window = str(row.get("anchor_window", ""))
        return (
            anchor_id not in selected_ids
            and source_counts[source_family] < int(max_per_source_family)
            and window_counts[anchor_window] < int(max_per_anchor_window)
            and len(selected) < int(max_selected_rows)
        )

    def add(row: Mapping[str, Any], phase: str) -> None:
        source_family = str(row.get("source_family", ""))
        anchor_window = str(row.get("anchor_window", ""))
        selected_ids.add(str(row.get("anchor_id", "")))
        source_counts[source_family] += 1
        window_counts[anchor_window] += 1
        selected.append(
            _selected_row(
                row,
                selector_order=len(selected),
                selection_phase=phase,
                source_pool_counts=source_pool_counts,
                window_pool_counts=window_pool_counts,
            )
        )

    def best(rows_for_group: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
        options = [row for row in rows_for_group if can_select(row)]
        if not options:
            return None
        return max(
            options,
            key=lambda row: _rank_key(row, source_pool_counts=source_pool_counts, window_pool_counts=window_pool_counts),
        )

    for source_family in sorted(source_pool_counts):
        row = best([candidate for candidate in candidates if str(candidate.get("source_family", "")) == source_family])
        if row is not None:
            add(row, "source_coverage")

    for anchor_window in sorted(window_pool_counts):
        row = best([candidate for candidate in candidates if str(candidate.get("anchor_window", "")) == anchor_window])
        if row is not None:
            add(row, "window_coverage")

    def dynamic_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        source_family = str(row.get("source_family", ""))
        anchor_window = str(row.get("anchor_window", ""))
        source_needs_balance = source_counts[source_family] < min(
            int(max_per_source_family),
            source_pool_counts[source_family],
            source_target,
        )
        window_needs_balance = window_counts[anchor_window] < min(
            int(max_per_anchor_window),
            window_pool_counts[anchor_window],
            window_target,
        )
        rank = _rank_key(row, source_pool_counts=source_pool_counts, window_pool_counts=window_pool_counts)
        return (
            int(source_needs_balance) + int(window_needs_balance),
            int(source_needs_balance),
            int(window_needs_balance),
            rank,
        )

    while len(selected) < target_selected_rows:
        options = [candidate for candidate in candidates if can_select(candidate)]
        if not options:
            break
        add(max(options, key=dynamic_key), "balanced_fill")

    return selected


def _group_summary(
    rows: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    *,
    key: str,
) -> list[dict[str, Any]]:
    selected_ids = {str(row.get("anchor_id", "")) for row in selected_rows}
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    selected_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
        if str(row.get("anchor_id", "")) in selected_ids:
            selected_groups[str(row.get(key, ""))].append(row)

    result: list[dict[str, Any]] = []
    for value in sorted(groups):
        group = groups[value]
        selected = selected_groups.get(value, [])
        result.append(
            {
                key: value,
                "input_recoverable_anchor_count": len(group),
                "selected_recoverable_anchor_count": len(selected),
                "selected_strong_recoverable_anchor_count": sum(
                    1 for row in selected if _as_bool(row.get("strong_recoverable_boundary"))
                ),
                "selected_predecision_anchor_count": sum(
                    1 for row in selected if str(row.get("anchor_window", "")) in PREDECISION_WINDOWS
                ),
                "selected_collision_flip_anchor_count": sum(
                    1 for row in selected if _as_int(row.get("collision_flip_count")) > 0
                ),
                "selected_success_flip_anchor_count": sum(
                    1 for row in selected if _as_int(row.get("success_flip_count")) > 0
                ),
                "selected_collision_flip_variant_count": sum(_as_int(row.get("collision_flip_count")) for row in selected),
                "selected_success_flip_variant_count": sum(_as_int(row.get("success_flip_count")) for row in selected),
                "max_abs_terminal_margin_gap": max(
                    (_as_float(row.get("max_abs_terminal_margin_gap")) for row in selected),
                    default=0.0,
                ),
            }
        )
    return result


def _input_gate_feasibility(candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    source_counts = Counter(str(row.get("source_family", "")) for row in candidates)
    window_counts = Counter(str(row.get("anchor_window", "")) for row in candidates)
    return {
        "max_feasible_selected_recoverable_anchor_count": min(
            MAX_SELECTED_ROWS,
            sum(min(count, MAX_PER_SOURCE_FAMILY) for count in source_counts.values()),
            sum(min(count, MAX_PER_ANCHOR_WINDOW) for count in window_counts.values()),
        ),
        "input_collision_flip_anchor_count": sum(1 for row in candidates if _as_int(row.get("collision_flip_count")) > 0),
        "input_success_flip_anchor_count": sum(1 for row in candidates if _as_int(row.get("success_flip_count")) > 0),
        "input_collision_flip_variant_count": sum(_as_int(row.get("collision_flip_count")) for row in candidates),
        "input_success_flip_variant_count": sum(_as_int(row.get("success_flip_count")) for row in candidates),
    }


def build_summary(
    *,
    input_dir: Path | str,
    input_summary: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    rejected_rows: Sequence[Mapping[str, Any]],
    local_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build selector summary with public gates and guardrails."""

    guardrails = dict(GUARDRAILS)
    source_counts = Counter(str(row.get("source_family", "")) for row in selected_rows)
    window_counts = Counter(str(row.get("anchor_window", "")) for row in selected_rows)
    input_source_counts = Counter(str(row.get("source_family", "")) for row in candidates)
    input_window_counts = Counter(str(row.get("anchor_window", "")) for row in candidates)
    selected_ids = {str(row.get("anchor_id", "")) for row in selected_rows}
    selected_local_rows = [row for row in local_rows if str(row.get("anchor_id", "")) in selected_ids]
    feasibility = _input_gate_feasibility(candidates)
    summary = {
        "result_class": "source_balanced_recoverable_active_set_selector",
        "input_dir": str(input_dir),
        "input_result_class": input_summary.get("result_class", ""),
        "input_recoverable_boundary_anchor_count": len(candidates),
        "input_strong_recoverable_boundary_anchor_count": sum(
            1 for row in candidates if _as_bool(row.get("strong_recoverable_boundary"))
        ),
        "input_source_family_count": len(input_source_counts),
        "input_window_count": len(input_window_counts),
        "input_source_family_counts": dict(sorted(input_source_counts.items())),
        "input_window_counts": dict(sorted(input_window_counts.items())),
        "selected_recoverable_anchor_count": len(selected_rows),
        "rejected_recoverable_anchor_count": len(rejected_rows),
        "selected_strong_recoverable_anchor_count": sum(
            1 for row in selected_rows if _as_bool(row.get("strong_recoverable_boundary"))
        ),
        "selected_predecision_anchor_count": sum(
            1 for row in selected_rows if str(row.get("anchor_window", "")) in PREDECISION_WINDOWS
        ),
        "selected_source_family_count": len(source_counts),
        "selected_window_count": len(window_counts),
        "selected_source_family_counts": dict(sorted(source_counts.items())),
        "selected_window_counts": dict(sorted(window_counts.items())),
        "max_selected_source_family_share": _max_share(source_counts),
        "max_selected_window_share": _max_share(window_counts),
        "selected_collision_flip_anchor_count": sum(
            1 for row in selected_rows if _as_int(row.get("collision_flip_count")) > 0
        ),
        "selected_success_flip_anchor_count": sum(
            1 for row in selected_rows if _as_int(row.get("success_flip_count")) > 0
        ),
        "selected_collision_flip_variant_count": sum(_as_int(row.get("collision_flip_count")) for row in selected_rows),
        "selected_success_flip_variant_count": sum(_as_int(row.get("success_flip_count")) for row in selected_rows),
        "selected_local_hold_row_count": len(selected_local_rows),
        "max_per_source_family": MAX_PER_SOURCE_FAMILY,
        "max_per_anchor_window": MAX_PER_ANCHOR_WINDOW,
        "max_selected_rows": MAX_SELECTED_ROWS,
        "min_selected_rows": MIN_SELECTED_ROWS,
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        **feasibility,
        **guardrails,
    }
    summary["input_flip_anchor_gate_feasible"] = (
        int(summary["input_collision_flip_anchor_count"]) >= MIN_SELECTED_COLLISION_FLIP_ANCHORS
        and int(summary["input_success_flip_anchor_count"]) >= MIN_SELECTED_SUCCESS_FLIP_ANCHORS
    )
    summary["passes_public_selector_gates"] = (
        int(summary["input_recoverable_boundary_anchor_count"]) >= MIN_INPUT_RECOVERABLE_ROWS
        and int(summary["selected_recoverable_anchor_count"]) >= MIN_SELECTED_ROWS
        and int(summary["selected_strong_recoverable_anchor_count"]) >= MIN_SELECTED_STRONG_ROWS
        and int(summary["selected_predecision_anchor_count"]) >= MIN_SELECTED_PREDECISION_ROWS
        and int(summary["selected_source_family_count"]) >= MIN_SELECTED_SOURCE_FAMILIES
        and int(summary["selected_window_count"]) >= MIN_SELECTED_WINDOWS
        and float(summary["max_selected_source_family_share"]) <= MAX_SELECTED_SOURCE_FAMILY_SHARE
        and float(summary["max_selected_window_share"]) <= MAX_SELECTED_WINDOW_SHARE
        and int(summary["selected_collision_flip_anchor_count"]) >= MIN_SELECTED_COLLISION_FLIP_ANCHORS
        and int(summary["selected_success_flip_anchor_count"]) >= MIN_SELECTED_SUCCESS_FLIP_ANCHORS
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["history_interventions_executed"])
        and not bool(summary["simulator_rerun_started"])
        and not bool(summary["training_corpus_exported"])
    )
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_selector_gates"])
        and int(summary["selected_recoverable_anchor_count"]) >= 45
        and int(summary["selected_strong_recoverable_anchor_count"]) >= 28
        and float(summary["max_selected_source_family_share"]) <= 0.28
        and float(summary["max_selected_window_share"]) <= 0.32
        and int(summary["selected_source_family_count"]) == 5
        and int(summary["selected_window_count"]) == 5
    )
    failed_gates: list[str] = []
    if not bool(summary["input_flip_anchor_gate_feasible"]):
        failed_gates.append("input_flip_anchor_gate_infeasible")
    if int(summary["selected_collision_flip_anchor_count"]) < MIN_SELECTED_COLLISION_FLIP_ANCHORS:
        failed_gates.append("selected_collision_flip_anchor_count")
    if int(summary["selected_success_flip_anchor_count"]) < MIN_SELECTED_SUCCESS_FLIP_ANCHORS:
        failed_gates.append("selected_success_flip_anchor_count")
    if int(summary["selected_recoverable_anchor_count"]) < MIN_SELECTED_ROWS:
        failed_gates.append("selected_recoverable_anchor_count")
    if int(summary["selected_strong_recoverable_anchor_count"]) < MIN_SELECTED_STRONG_ROWS:
        failed_gates.append("selected_strong_recoverable_anchor_count")
    if float(summary["max_selected_source_family_share"]) > MAX_SELECTED_SOURCE_FAMILY_SHARE:
        failed_gates.append("max_selected_source_family_share")
    if float(summary["max_selected_window_share"]) > MAX_SELECTED_WINDOW_SHARE:
        failed_gates.append("max_selected_window_share")
    summary["failed_public_selector_gates"] = failed_gates
    return summary


def run_source_balanced_recoverable_active_set_selector(
    output_dir: Path | str,
    *,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
) -> dict[str, Any]:
    """Run the no-simulator, no-history-intervention selector."""

    input_path = Path(input_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_rows = _read_csv_rows(input_path / "recoverable_active_anchor_rows.csv")
    local_rows = _read_csv_rows(input_path / "local_hold_rows.csv")
    input_summary = read_json(input_path / "summary.json")
    candidates = recoverable_candidates(source_rows)
    selected_rows = select_source_balanced_rows(candidates)
    selected_ids = {str(row.get("anchor_id", "")) for row in selected_rows}
    rejected_rows = [dict(row, selector_rejected_reason="not_selected_by_rank_or_cap") for row in candidates if str(row.get("anchor_id", "")) not in selected_ids]
    summary = build_summary(
        input_dir=input_path,
        input_summary=input_summary,
        candidates=candidates,
        selected_rows=selected_rows,
        rejected_rows=rejected_rows,
        local_rows=local_rows,
    )
    write_csv_rows(output / "selected_active_anchor_rows.csv", selected_rows)
    write_csv_rows(output / "rejected_active_anchor_rows.csv", rejected_rows)
    write_csv_rows(output / "selector_source_family_summary.csv", _group_summary(candidates, selected_rows, key="source_family"))
    write_csv_rows(output / "selector_window_summary.csv", _group_summary(candidates, selected_rows, key="anchor_window"))
    write_csv_rows(output / "selector_guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select source-balanced recoverable active-set diagnostic rows.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    args = parser.parse_args()
    summary = run_source_balanced_recoverable_active_set_selector(args.output_dir, input_dir=args.input_dir)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"selected_recoverable_anchor_count={summary['selected_recoverable_anchor_count']}")
    print(f"selected_strong_recoverable_anchor_count={summary['selected_strong_recoverable_anchor_count']}")
    print(f"passes_public_selector_gates={summary['passes_public_selector_gates']}")


if __name__ == "__main__":
    main()
