"""Source-step boundary retarget proposal generator."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.warmup_latched_outcome_probe import WARMUP_HISTORY_VARIANTS, source_diversity


DEFAULT_BOUNDARY_MARGIN_HIGH = 1.0
DEFAULT_MIN_HALF_WIDTH = 0.05


def _finite(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if math.isfinite(result) else float(default)


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(float(value) != 0.0) if math.isfinite(float(value)) else False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def classify_boundary_pressure(
    *,
    normal_success: bool,
    normal_margin: float,
    boundary_margin_high: float = DEFAULT_BOUNDARY_MARGIN_HIGH,
) -> str:
    if bool(normal_success) and math.isfinite(float(normal_margin)) and 0.0 <= float(normal_margin) <= float(boundary_margin_high):
        return "normal_boundary"
    if bool(normal_success) and math.isfinite(float(normal_margin)) and float(normal_margin) > float(boundary_margin_high):
        return "too_easy"
    return "too_hard"


def _center_direction(y: float) -> float:
    if not math.isfinite(float(y)) or abs(float(y)) < 1e-9:
        return 0.0
    return -1.0 if float(y) > 0.0 else 1.0


def _away_direction(y: float) -> float:
    if not math.isfinite(float(y)) or abs(float(y)) < 1e-9:
        return 0.0
    return 1.0 if float(y) > 0.0 else -1.0


def retarget_delta_grid(retarget_class: str, *, relocated_body_y: float) -> list[dict[str, float]]:
    toward_center = _center_direction(relocated_body_y)
    away = _away_direction(relocated_body_y)
    if retarget_class == "normal_boundary":
        return [
            {"body_longitudinal_delta": dx, "body_lateral_delta": dy, "half_width_delta": dw}
            for dx in (-1.0, 0.0, 1.0)
            for dy in (-0.2, 0.0, 0.2)
            for dw in (0.0, 0.2)
        ]
    if retarget_class == "too_easy":
        return [
            {"body_longitudinal_delta": dx, "body_lateral_delta": toward_center * dy, "half_width_delta": dw}
            for dx in (-2.0, -1.0)
            for dy in (0.0, 0.2, 0.4)
            for dw in (0.2, 0.4)
        ]
    return [
        {"body_longitudinal_delta": dx, "body_lateral_delta": away * dy, "half_width_delta": dw}
        for dx in (2.0, 4.0)
        for dy in (0.0, 0.2, 0.4)
        for dw in (-0.2, 0.0)
    ]


def _base_offsets(row: dict[str, Any]) -> dict[str, float]:
    source_body_x = _finite(row.get("source_body_x"))
    source_body_y = _finite(row.get("source_body_y"))
    source_half_width = _finite(row.get("source_half_width"))
    return {
        "body_longitudinal_offset": _finite(row.get("raw_relocated_body_x")) - source_body_x,
        "body_lateral_offset": _finite(row.get("relocated_body_y")) - source_body_y,
        "half_width_inflation": _finite(row.get("raw_relocated_half_width")) - source_half_width,
    }


def _proposal_from_delta(row: dict[str, Any], delta: dict[str, float], *, retarget_class: str, rank: int) -> dict[str, Any]:
    base = _base_offsets(row)
    source_half_width = _finite(row.get("source_half_width"))
    half_width_floor = DEFAULT_MIN_HALF_WIDTH - source_half_width
    body_longitudinal_offset = base["body_longitudinal_offset"] + float(delta["body_longitudinal_delta"])
    body_lateral_offset = base["body_lateral_offset"] + float(delta["body_lateral_delta"])
    half_width_inflation = max(
        half_width_floor,
        base["half_width_inflation"] + float(delta["half_width_delta"]),
    )
    source_step = int(_finite(row.get("candidate_step"), _finite(row.get("source_step"), _finite(row.get("reveal_step"), 0.0))))
    output = {
        "retarget_rank": int(rank),
        "retarget_class": str(retarget_class),
        "base_selected_index": int(_finite(row.get("selected_index"), rank)),
        "source_index": int(_finite(row.get("source_index"), rank)),
        "seed": int(_finite(row.get("seed"), 0)),
        "reveal_step": int(_finite(row.get("reveal_step"), source_step)),
        "source_step": int(source_step),
        "candidate_step": int(source_step),
        "candidate_step_column": "source_step",
        "preferred_fault": str(row.get("preferred_fault", "")),
        "wrong_fault": str(row.get("wrong_fault", "")),
        "capability_pair": str(row.get("capability_pair", "")),
        "preferred_reveal_bucket": str(row.get("preferred_reveal_bucket", "")),
        "variant": str(row.get("variant", "")),
        "sequence_action_l2_mean": _finite(row.get("sequence_action_l2_mean"), 0.0),
        "margin_gap": _finite(row.get("margin_gap"), 0.0),
        "normal_success": bool(_bool_value(row.get("normal_success", False))),
        "normal_margin": _finite(row.get("normal_margin")),
        "variant_success": bool(_bool_value(row.get("variant_success", False))),
        "variant_margin": _finite(row.get("variant_margin")),
        "source_body_x": _finite(row.get("source_body_x")),
        "source_body_y": _finite(row.get("source_body_y")),
        "source_half_width": source_half_width,
        "base_body_longitudinal_offset": base["body_longitudinal_offset"],
        "base_body_lateral_offset": base["body_lateral_offset"],
        "base_half_width_inflation": base["half_width_inflation"],
        "body_longitudinal_delta": float(delta["body_longitudinal_delta"]),
        "body_lateral_delta": float(delta["body_lateral_delta"]),
        "half_width_delta": float(delta["half_width_delta"]),
        "body_longitudinal_offset": float(body_longitudinal_offset),
        "body_lateral_offset": float(body_lateral_offset),
        "half_width_inflation": float(half_width_inflation),
    }
    output["retarget_source_key"] = "|".join(
        str(output[key])
        for key in ("seed", "source_step", "preferred_fault", "wrong_fault", "variant", "retarget_class")
    )
    return output


def history_variant_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    rows = frame[frame["variant"].astype(str).isin(WARMUP_HISTORY_VARIANTS)].copy()
    rows = rows.sort_values(["selected_index", "sequence_action_l2_mean"], ascending=[True, False])
    return rows.drop_duplicates(subset=["selected_index"], keep="first").reset_index(drop=True)


def generate_retarget_proposals(
    replay_rows: pd.DataFrame,
    *,
    boundary_margin_high: float = DEFAULT_BOUNDARY_MARGIN_HIGH,
) -> pd.DataFrame:
    history_rows = history_variant_rows(replay_rows)
    proposals: list[dict[str, Any]] = []
    for _, row in history_rows.iterrows():
        row_dict = row.to_dict()
        retarget_class = classify_boundary_pressure(
            normal_success=_bool_value(row_dict.get("normal_success", False)),
            normal_margin=_finite(row_dict.get("normal_margin")),
            boundary_margin_high=boundary_margin_high,
        )
        for delta in retarget_delta_grid(retarget_class, relocated_body_y=_finite(row_dict.get("relocated_body_y"))):
            proposals.append(
                _proposal_from_delta(
                    row_dict,
                    delta,
                    retarget_class=retarget_class,
                    rank=len(proposals),
                )
            )
    return pd.DataFrame(proposals)


def select_retarget_candidates(
    proposals: pd.DataFrame,
    *,
    max_candidates: int,
    per_class_cap: int,
    per_seed_cap: int,
    per_capability_pair_cap: int,
    per_variant_cap: int,
) -> pd.DataFrame:
    if proposals.empty:
        return proposals.copy()
    frame = proposals.copy()
    class_priority = {"normal_boundary": 0, "too_easy": 1, "too_hard": 2}
    frame["_class_priority"] = frame["retarget_class"].map(class_priority).fillna(9).astype(int)
    frame["_abs_margin_to_boundary"] = (pd.to_numeric(frame["normal_margin"], errors="coerce").fillna(-999.0) - DEFAULT_BOUNDARY_MARGIN_HIGH).abs()
    frame = frame.sort_values(
        ["_class_priority", "_abs_margin_to_boundary", "sequence_action_l2_mean", "retarget_rank"],
        ascending=[True, True, False, True],
    )
    counts: dict[str, Counter] = {
        "class": Counter(),
        "seed": Counter(),
        "pair": Counter(),
        "variant": Counter(),
    }
    selected: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        klass = str(row["retarget_class"])
        seed = str(row["seed"])
        pair = str(row["capability_pair"])
        variant = str(row["variant"])
        if per_class_cap > 0 and counts["class"][klass] >= per_class_cap:
            continue
        if per_seed_cap > 0 and counts["seed"][seed] >= per_seed_cap:
            continue
        if per_capability_pair_cap > 0 and counts["pair"][pair] >= per_capability_pair_cap:
            continue
        if per_variant_cap > 0 and counts["variant"][variant] >= per_variant_cap:
            continue
        output = row.drop(labels=[c for c in ("_class_priority", "_abs_margin_to_boundary") if c in row.index]).to_dict()
        output["selected_retarget_rank"] = len(selected)
        selected.append(output)
        counts["class"][klass] += 1
        counts["seed"][seed] += 1
        counts["pair"][pair] += 1
        counts["variant"][variant] += 1
        if max_candidates > 0 and len(selected) >= max_candidates:
            break
    return pd.DataFrame(selected)


def build_retarget_summary(*, replay_rows: pd.DataFrame, proposals: pd.DataFrame, selected: pd.DataFrame) -> dict[str, Any]:
    class_counts = proposals["retarget_class"].value_counts().to_dict() if "retarget_class" in proposals else {}
    selected_class_counts = selected["retarget_class"].value_counts().to_dict() if "retarget_class" in selected else {}
    return {
        "run_type": "source_step_replay_boundary_retarget",
        "input_replay_rows": int(len(replay_rows)),
        "history_variant_groups": int(len(history_variant_rows(replay_rows))),
        "proposal_rows": int(len(proposals)),
        "selected_retarget_rows": int(len(selected)),
        "proposal_class_counts": {str(k): int(v) for k, v in class_counts.items()},
        "selected_class_counts": {str(k): int(v) for k, v in selected_class_counts.items()},
        "selected_diversity": source_diversity(selected.to_dict("records") if not selected.empty else []),
        "candidate_step_column": "source_step",
        "source_preflight_started": False,
        "replay_started": False,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_input_contract_changed": False,
    }


def run_retarget_generation(
    *,
    actual_replay_rows: Path,
    run_dir: Path,
    boundary_margin_high: float = DEFAULT_BOUNDARY_MARGIN_HIGH,
    max_candidates: int = 128,
    per_class_cap: int = 64,
    per_seed_cap: int = 32,
    per_capability_pair_cap: int = 24,
    per_variant_cap: int = 64,
) -> dict[str, Any]:
    replay = pd.read_csv(actual_replay_rows)
    proposals = generate_retarget_proposals(replay, boundary_margin_high=boundary_margin_high)
    selected = select_retarget_candidates(
        proposals,
        max_candidates=max_candidates,
        per_class_cap=per_class_cap,
        per_seed_cap=per_seed_cap,
        per_capability_pair_cap=per_capability_pair_cap,
        per_variant_cap=per_variant_cap,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(run_dir / "retarget_proposal_rows.csv", proposals.to_dict("records") if not proposals.empty else [])
    write_csv_rows(run_dir / "retarget_candidate_rows.csv", selected.to_dict("records") if not selected.empty else [])
    summary = build_retarget_summary(replay_rows=replay, proposals=proposals, selected=selected)
    summary["actual_replay_rows"] = str(actual_replay_rows)
    summary["retarget_proposal_rows_csv"] = str(run_dir / "retarget_proposal_rows.csv")
    summary["retarget_candidate_rows_csv"] = str(run_dir / "retarget_candidate_rows.csv")
    summary["summary_json"] = str(run_dir / "summary.json")
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-replay-rows", type=Path, required=True)
    parser.add_argument("--boundary-margin-high", type=float, default=DEFAULT_BOUNDARY_MARGIN_HIGH)
    parser.add_argument("--max-candidates", type=int, default=128)
    parser.add_argument("--per-class-cap", type=int, default=64)
    parser.add_argument("--per-seed-cap", type=int, default=32)
    parser.add_argument("--per-capability-pair-cap", type=int, default=24)
    parser.add_argument("--per-variant-cap", type=int, default=64)
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    run_dir = args.run_dir or make_run_dir(prefix="source_step_replay_boundary_retarget")
    summary = run_retarget_generation(
        actual_replay_rows=args.actual_replay_rows,
        run_dir=run_dir,
        boundary_margin_high=args.boundary_margin_high,
        max_candidates=args.max_candidates,
        per_class_cap=args.per_class_cap,
        per_seed_cap=args.per_seed_cap,
        per_capability_pair_cap=args.per_capability_pair_cap,
        per_variant_cap=args.per_variant_cap,
    )
    print(f"summary_json={run_dir / 'summary.json'}")
    print(f"proposal_rows={summary['proposal_rows']}")
    print(f"selected_retarget_rows={summary['selected_retarget_rows']}")


if __name__ == "__main__":
    main()
