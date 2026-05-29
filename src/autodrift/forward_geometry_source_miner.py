"""Geometry-first source mining helpers for forward obstacle replay candidates.

This module does not reconstruct traces, replay trajectories, train, or mutate
checkpoints. It filters precomputed source-geometry rows before any
action-divergence or replay stage can use them.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.bounded_relocation_replay_probe import classify_relocation_geometry
from autodrift.warmup_latched_outcome_probe import WARMUP_HISTORY_VARIANTS, source_diversity


DEFAULT_SOURCE_STEP_OFFSETS = (-32, -24, -16, -8, 0)
DEFAULT_LONGITUDINAL_OFFSETS = (0.0, 1.0, 2.0, 4.0)
DEFAULT_LATERAL_OFFSETS = (-0.4, 0.0, 0.4)
DEFAULT_HALF_WIDTH_INFLATIONS = (0.0, 0.2, 0.4)
DEFAULT_MIN_SOURCE_BODY_X = 4.0
DEFAULT_MIN_RAW_RELOCATED_BODY_X = 4.0
DEFAULT_MIN_SEQUENCE_ACTION_L2 = 0.025


@dataclass(frozen=True)
class ForwardRelocationProposal:
    body_longitudinal_offset: float
    body_lateral_offset: float
    half_width_inflation: float


def _finite(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if np.isfinite(result) else float(default)


def _bool_value(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(float(value) != 0.0) if np.isfinite(float(value)) else False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_number_list(raw: str, *, value_type: type = float) -> tuple[Any, ...]:
    values = tuple(value_type(item.strip()) for item in str(raw).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one value")
    return values


def source_steps_for_reveal(
    reveal_step: int,
    *,
    offsets: tuple[int, ...] = DEFAULT_SOURCE_STEP_OFFSETS,
) -> tuple[int, ...]:
    steps = sorted({max(0, int(reveal_step) + int(offset)) for offset in offsets})
    return tuple(steps)


def validate_forward_longitudinal_offsets(offsets: tuple[float, ...]) -> tuple[float, ...]:
    values = tuple(float(offset) for offset in offsets)
    if not values:
        raise ValueError("expected at least one longitudinal offset")
    negative = [offset for offset in values if offset < 0.0]
    if negative:
        raise ValueError(f"forward geometry source miner forbids negative longitudinal offsets: {negative}")
    return values


def forward_relocation_grid(
    *,
    longitudinal_offsets: tuple[float, ...] = DEFAULT_LONGITUDINAL_OFFSETS,
    lateral_offsets: tuple[float, ...] = DEFAULT_LATERAL_OFFSETS,
    half_width_inflations: tuple[float, ...] = DEFAULT_HALF_WIDTH_INFLATIONS,
) -> list[ForwardRelocationProposal]:
    longitudinal = validate_forward_longitudinal_offsets(longitudinal_offsets)
    return [
        ForwardRelocationProposal(float(dx), float(dy), float(inflation))
        for dx in longitudinal
        for dy in lateral_offsets
        for inflation in half_width_inflations
    ]


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"source geometry rows missing required columns: {missing}")


def prepare_source_geometry_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = (
        "seed",
        "reveal_step",
        "source_step",
        "source_body_x",
        "source_body_y",
        "source_half_width",
        "variant",
        "capability_pair",
        "preferred_reveal_bucket",
    )
    _require_columns(frame, required)
    output = frame.copy()
    for column in (
        "seed",
        "reveal_step",
        "source_step",
        "source_body_x",
        "source_body_y",
        "source_half_width",
        "sequence_action_l2_mean",
    ):
        if column in output.columns:
            output[column] = pd.to_numeric(output[column], errors="coerce")
    if "sequence_action_l2_mean" not in output.columns:
        output["sequence_action_l2_mean"] = 0.0
    if "matched_current_pass" in output.columns:
        output["matched_current_pass"] = output["matched_current_pass"].map(_bool_value)
    else:
        output["matched_current_pass"] = False
    if "bucketed_current_pass" in output.columns:
        output["bucketed_current_pass"] = output["bucketed_current_pass"].map(_bool_value)
    else:
        output["bucketed_current_pass"] = False
    output["history_variant"] = output["variant"].astype(str).isin(WARMUP_HISTORY_VARIANTS)
    output["source_to_reveal_steps"] = output["reveal_step"] - output["source_step"]
    return output


def expand_forward_geometry_sources(
    source_rows: pd.DataFrame,
    *,
    proposals: list[ForwardRelocationProposal] | None = None,
    min_source_body_x: float = DEFAULT_MIN_SOURCE_BODY_X,
    min_raw_relocated_body_x: float = DEFAULT_MIN_RAW_RELOCATED_BODY_X,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = prepare_source_geometry_frame(source_rows)
    proposal_list = proposals if proposals is not None else forward_relocation_grid()
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for source_index, row in rows.reset_index(drop=True).iterrows():
        for proposal_index, proposal in enumerate(proposal_list):
            geometry = classify_relocation_geometry(
                source_body_x=_finite(row.get("source_body_x")),
                source_body_y=_finite(row.get("source_body_y")),
                source_half_width=_finite(row.get("source_half_width")),
                body_longitudinal_offset=proposal.body_longitudinal_offset,
                body_lateral_offset=proposal.body_lateral_offset,
                half_width_inflation=proposal.half_width_inflation,
                min_source_body_x=min_source_body_x,
            )
            output = dict(row)
            output.update(
                {
                    "source_index": int(source_index),
                    "proposal_index": int(proposal_index),
                    "body_longitudinal_offset": float(proposal.body_longitudinal_offset),
                    "body_lateral_offset": float(proposal.body_lateral_offset),
                    "half_width_inflation": float(proposal.half_width_inflation),
                    **geometry,
                }
            )
            raw_forward = _finite(geometry.get("raw_relocated_body_x")) >= float(min_raw_relocated_body_x)
            output["raw_relocated_body_x_pass"] = bool(raw_forward)
            output["forward_geometry_pass"] = bool(geometry["geometry_pass"] and raw_forward)
            if output["forward_geometry_pass"]:
                accepted_rows.append(output)
            else:
                reasons = [str(geometry["geometry_rejection_reason"])]
                if not raw_forward:
                    reasons.append("raw_relocated_body_x_too_close")
                output["rejection_reason"] = "|".join(reason for reason in reasons if reason and reason != "pass")
                rejected_rows.append(output)
    return pd.DataFrame(accepted_rows), pd.DataFrame(rejected_rows)


def select_forward_geometry_source_rows(
    candidates: pd.DataFrame,
    *,
    max_candidates: int,
    per_seed_cap: int,
    per_capability_pair_cap: int,
    per_reveal_bucket_cap: int,
    per_variant_cap: int,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
    frame = candidates.copy()
    frame["sequence_action_l2_mean"] = pd.to_numeric(frame["sequence_action_l2_mean"], errors="coerce")
    frame = frame[
        frame["forward_geometry_pass"].astype(bool)
        & frame["history_variant"].astype(bool)
        & (frame["sequence_action_l2_mean"] >= float(min_sequence_action_l2))
    ].copy()
    if frame.empty:
        return frame
    frame["_matched_rank"] = frame["matched_current_pass"].astype(bool) | frame["bucketed_current_pass"].astype(bool)
    frame["_score"] = (
        frame["source_body_x"].fillna(0.0) / 10.0
        + frame["raw_relocated_body_x"].fillna(0.0) / 10.0
        + frame["sequence_action_l2_mean"].fillna(0.0) / 0.10
        + frame["_matched_rank"].astype(float)
    )
    frame = frame.sort_values(
        ["_score", "source_body_x", "raw_relocated_body_x", "seed", "source_step"],
        ascending=[False, False, False, True, True],
    )
    selected_rows: list[dict[str, Any]] = []
    counts: dict[str, dict[Any, int]] = {
        "seed": {},
        "capability_pair": {},
        "preferred_reveal_bucket": {},
        "variant": {},
    }
    caps = {
        "seed": int(per_seed_cap),
        "capability_pair": int(per_capability_pair_cap),
        "preferred_reveal_bucket": int(per_reveal_bucket_cap),
        "variant": int(per_variant_cap),
    }
    for _, row in frame.iterrows():
        values = {key: row.get(key) for key in counts}
        if any(caps[key] > 0 and counts[key].get(values[key], 0) >= caps[key] for key in counts):
            continue
        selected_rows.append(dict(row))
        for key, value in values.items():
            counts[key][value] = counts[key].get(value, 0) + 1
        if int(max_candidates) > 0 and len(selected_rows) >= int(max_candidates):
            break
    selected = pd.DataFrame(selected_rows)
    if not selected.empty:
        selected["selected_forward_geometry_rank"] = np.arange(len(selected), dtype=int)
    return selected.reset_index(drop=True)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.to_dict("records") if not frame.empty else []


def _numeric_summary(frame: pd.DataFrame, column: str) -> dict[str, float | None]:
    if column not in frame.columns:
        return {"min": None, "p50": None, "p95": None}
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return {"min": None, "p50": None, "p95": None}
    return {
        "min": float(values.min()),
        "p50": float(values.quantile(0.50)),
        "p95": float(values.quantile(0.95)),
    }


def build_forward_geometry_source_summary(
    *,
    source_rows: pd.DataFrame,
    candidates: pd.DataFrame,
    selected: pd.DataFrame,
    rejected: pd.DataFrame,
) -> dict[str, Any]:
    source_body_x = _numeric_summary(selected, "source_body_x")
    raw_relocated_body_x = _numeric_summary(selected, "raw_relocated_body_x")
    clipped_share = (
        float(selected["relocation_body_x_clipped"].astype(bool).mean())
        if not selected.empty and "relocation_body_x_clipped" in selected
        else 0.0
    )
    return {
        "run_type": "forward_geometry_source_miner",
        "source_rows": int(len(source_rows)),
        "geometry_pass_rows": int(len(candidates)),
        "selected_candidate_rows": int(len(selected)),
        "rejected_rows": int(len(rejected)),
        "selected_diversity": source_diversity(_records(selected)),
        "geometry_pass_diversity": source_diversity(_records(candidates)),
        "source_body_x_min": source_body_x["min"],
        "source_body_x_p50": source_body_x["p50"],
        "source_body_x_p95": source_body_x["p95"],
        "raw_relocated_body_x_min": raw_relocated_body_x["min"],
        "raw_relocated_body_x_p50": raw_relocated_body_x["p50"],
        "raw_relocated_body_x_p95": raw_relocated_body_x["p95"],
        "relocation_clipped_share": clipped_share,
        "source_mining_started": False,
        "source_preflight_started": False,
        "replay_started": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_input_contract_changed": False,
    }


def run_forward_geometry_source_miner_from_rows(
    *,
    source_geometry_rows_path: Path,
    run_dir: Path,
    max_candidates: int,
    per_seed_cap: int,
    per_capability_pair_cap: int,
    per_reveal_bucket_cap: int,
    per_variant_cap: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source_rows = pd.read_csv(source_geometry_rows_path)
    candidates, rejected = expand_forward_geometry_sources(source_rows)
    selected = select_forward_geometry_source_rows(
        candidates,
        max_candidates=max_candidates,
        per_seed_cap=per_seed_cap,
        per_capability_pair_cap=per_capability_pair_cap,
        per_reveal_bucket_cap=per_reveal_bucket_cap,
        per_variant_cap=per_variant_cap,
    )
    summary = build_forward_geometry_source_summary(
        source_rows=source_rows,
        candidates=candidates,
        selected=selected,
        rejected=rejected,
    )
    summary["forward_geometry_source_rows_csv"] = run_dir / "forward_geometry_source_rows.csv"
    summary["selected_candidate_rows_csv"] = run_dir / "selected_candidate_rows.csv"
    summary["rejected_rows_csv"] = run_dir / "rejected_rows.csv"
    summary["summary_json"] = run_dir / "summary.json"
    write_csv_rows(run_dir / "forward_geometry_source_rows.csv", _records(candidates))
    write_csv_rows(run_dir / "selected_candidate_rows.csv", _records(selected))
    write_csv_rows(run_dir / "rejected_rows.csv", _records(rejected))
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-geometry-rows", type=Path, required=True)
    parser.add_argument("--max-candidates", type=int, default=128)
    parser.add_argument("--per-seed-cap", type=int, default=24)
    parser.add_argument("--per-capability-pair-cap", type=int, default=12)
    parser.add_argument("--per-reveal-bucket-cap", type=int, default=12)
    parser.add_argument("--per-variant-cap", type=int, default=48)
    parser.add_argument("--run-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    summary = run_forward_geometry_source_miner_from_rows(
        source_geometry_rows_path=args.source_geometry_rows,
        run_dir=args.run_dir,
        max_candidates=args.max_candidates,
        per_seed_cap=args.per_seed_cap,
        per_capability_pair_cap=args.per_capability_pair_cap,
        per_reveal_bucket_cap=args.per_reveal_bucket_cap,
        per_variant_cap=args.per_variant_cap,
    )
    print(f"summary_json={args.run_dir / 'summary.json'}")
    print(f"geometry_pass_rows={summary['geometry_pass_rows']}")
    print(f"selected_candidate_rows={summary['selected_candidate_rows']}")


if __name__ == "__main__":
    main()
