"""Build no-training action-divergent outcome-pressure source rows.

This module does not replay trajectories or mutate actor parameters. It turns
existing outcome-probe rows into a source-balanced set of relocation candidates
for a later separately registered source smoke.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.warmup_latched_outcome_probe import (
    CONTROL_VARIANTS,
    WARMUP_HISTORY_VARIANTS,
    normal_margin_band,
    source_diversity,
)


DEFAULT_LONGITUDINAL_OFFSETS = (-2.0, -1.0, 0.0, 1.0, 2.0)
DEFAULT_LATERAL_OFFSETS = (-0.4, -0.2, 0.0, 0.2, 0.4)
DEFAULT_HALF_WIDTH_INFLATIONS = (0.0, 0.1, 0.2, 0.3)
DEFAULT_MIN_SEQUENCE_ACTION_L2 = 0.025
DEFAULT_MIN_FIRST_ACTION_L2 = 0.0
DEFAULT_MIN_MARGIN_GAP = 0.02
DEFAULT_BROAD_MARGIN_BAND = (0.0, 0.50)
DEFAULT_PREFERRED_MARGIN_BAND = (0.02, 0.25)


@dataclass(frozen=True)
class RelocationProposal:
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


def _parse_float_list(raw: str) -> tuple[float, ...]:
    values = tuple(float(item.strip()) for item in str(raw).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one float")
    return values


def relocation_grid(
    *,
    longitudinal_offsets: tuple[float, ...] = DEFAULT_LONGITUDINAL_OFFSETS,
    lateral_offsets: tuple[float, ...] = DEFAULT_LATERAL_OFFSETS,
    half_width_inflations: tuple[float, ...] = DEFAULT_HALF_WIDTH_INFLATIONS,
) -> list[RelocationProposal]:
    return [
        RelocationProposal(float(dx), float(dy), float(inflation))
        for dx in longitudinal_offsets
        for dy in lateral_offsets
        for inflation in half_width_inflations
    ]


def variant_family(variant: Any) -> str:
    name = str(variant)
    if name in WARMUP_HISTORY_VARIANTS:
        return "history"
    if name in CONTROL_VARIANTS:
        return "control"
    return "unknown"


def _source_key(row: pd.Series | dict[str, Any]) -> str:
    if "selected_index" in row and str(row.get("selected_index", "")) != "":
        return f"selected:{row.get('selected_index')}"
    parts = (
        row.get("source_index", ""),
        row.get("seed", ""),
        row.get("reveal_step", ""),
        row.get("preferred_fault", ""),
        row.get("wrong_fault", ""),
    )
    return "|".join(str(part) for part in parts)


def _required_columns(frame: pd.DataFrame, required: tuple[str, ...]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"outcome rows missing required columns: {missing}")


def prepare_outcome_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = (
        "variant",
        "seed",
        "reveal_step",
        "normal_success",
        "variant_success",
        "normal_margin",
        "variant_margin",
        "margin_gap",
        "first_action_l2",
        "sequence_action_l2_mean",
    )
    _required_columns(frame, required)
    output = frame.copy()
    for column in (
        "normal_margin",
        "variant_margin",
        "margin_gap",
        "first_action_l2",
        "sequence_action_l2_mean",
        "sequence_action_l2_max",
    ):
        if column in output.columns:
            output[column] = pd.to_numeric(output[column], errors="coerce")
    for column in ("normal_success", "variant_success", "matched_current_pass", "bucketed_current_pass"):
        if column in output.columns:
            output[column] = output[column].map(_bool_value)
    output["variant_family"] = output["variant"].map(variant_family)
    output["source_key"] = [_source_key(row) for _, row in output.iterrows()]
    if "capability_pair" not in output.columns:
        output["capability_pair"] = output.apply(
            lambda row: f"{row.get('preferred_fault_family', '')}->{row.get('wrong_fault_family', '')}",
            axis=1,
        )
    if "preferred_reveal_bucket" not in output.columns:
        output["preferred_reveal_bucket"] = ""
    return output


def action_divergent_candidate_pool(
    outcome_frame: pd.DataFrame,
    *,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
    min_first_action_l2: float = DEFAULT_MIN_FIRST_ACTION_L2,
    require_matched_or_bucketed: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return history-variant action-divergent rows and rejected diagnostics."""

    frame = prepare_outcome_frame(outcome_frame)
    matched = pd.Series(True, index=frame.index)
    if require_matched_or_bucketed:
        matched_current = frame["matched_current_pass"] if "matched_current_pass" in frame.columns else False
        bucketed_current = frame["bucketed_current_pass"] if "bucketed_current_pass" in frame.columns else False
        matched = matched_current.astype(bool) | bucketed_current.astype(bool)
    frame["matched_or_bucketed_current"] = matched.astype(bool)
    first_action_gate = (
        frame["first_action_l2"] >= float(min_first_action_l2)
        if float(min_first_action_l2) > 0.0
        else pd.Series(False, index=frame.index)
    )
    frame["action_divergent"] = (frame["sequence_action_l2_mean"] >= float(min_sequence_action_l2)) | first_action_gate
    frame["normal_viable"] = frame["normal_success"].astype(bool) & (frame["normal_margin"] >= 0.0)
    frame["history_variant"] = frame["variant_family"] == "history"
    frame["control_variant"] = frame["variant_family"] == "control"

    accepted_mask = (
        frame["matched_or_bucketed_current"]
        & frame["normal_viable"]
        & frame["history_variant"]
        & frame["action_divergent"]
    )
    accepted = frame[accepted_mask].copy()
    accepted["candidate_reason"] = "history_action_divergent_normal_viable"

    rejected_rows: list[dict[str, Any]] = []
    for source_key, group in frame.groupby("source_key", observed=True):
        history_divergent = bool((group["history_variant"] & group["action_divergent"]).any())
        control_divergent = bool((group["control_variant"] & group["action_divergent"]).any())
        normal_viable = bool(group["normal_viable"].any())
        matched_any = bool(group["matched_or_bucketed_current"].any())
        if source_key in set(accepted["source_key"].astype(str)):
            continue
        reasons: list[str] = []
        if not matched_any:
            reasons.append("not_matched_or_bucketed_current")
        if not normal_viable:
            reasons.append("normal_not_viable")
        if not history_divergent:
            reasons.append("no_history_action_divergence")
        if control_divergent and not history_divergent:
            reasons.append("control_only_action_divergence")
        row = group.iloc[0].to_dict()
        rejected_rows.append(
            {
                **row,
                "source_key": str(source_key),
                "rejection_reason": ";".join(reasons) if reasons else "not_selected",
                "history_action_divergent_rows": int((group["history_variant"] & group["action_divergent"]).sum()),
                "control_action_divergent_rows": int((group["control_variant"] & group["action_divergent"]).sum()),
            }
        )

    return accepted.reset_index(drop=True), pd.DataFrame(rejected_rows)


def select_source_balanced_candidates(
    candidate_pool: pd.DataFrame,
    *,
    max_candidates: int,
    per_capability_pair_cap: int,
) -> pd.DataFrame:
    if candidate_pool.empty:
        return candidate_pool.copy()
    frame = candidate_pool.copy()
    frame["_normal_margin_target_distance"] = (frame["normal_margin"] - 0.10).abs()
    frame["_score"] = (
        frame["sequence_action_l2_mean"].fillna(0.0) / 0.10
        + frame["first_action_l2"].fillna(0.0) / 0.10
        + frame["margin_gap"].fillna(0.0).clip(lower=0.0) / 0.02
        - frame["_normal_margin_target_distance"].fillna(1.0)
    )
    frame = frame.sort_values(
        ["_score", "sequence_action_l2_mean", "margin_gap", "seed", "reveal_step"],
        ascending=[False, False, False, True, True],
    )
    selected: list[pd.DataFrame] = []
    for _, group in frame.groupby("capability_pair", observed=True):
        selected.append(group.head(max(1, int(per_capability_pair_cap))))
    if not selected:
        return frame.head(0)
    output = pd.concat(selected, ignore_index=True).sort_values("_score", ascending=False)
    if int(max_candidates) > 0:
        output = output.head(int(max_candidates))
    output = output.drop(columns=["_normal_margin_target_distance"], errors="ignore")
    output["selected_pressure_rank"] = np.arange(len(output), dtype=int)
    return output.reset_index(drop=True)


def relocation_pressure_proxy(
    proposal: RelocationProposal,
    *,
    lateral_pressure_scale: float = 0.25,
    closer_longitudinal_pressure_scale: float = 0.04,
) -> float:
    """Conservative scalar proxy used only to rank relocation candidates."""

    closer_pressure = max(0.0, -float(proposal.body_longitudinal_offset)) * float(
        closer_longitudinal_pressure_scale
    )
    lateral_pressure = abs(float(proposal.body_lateral_offset)) * float(lateral_pressure_scale)
    return float(proposal.half_width_inflation) + closer_pressure + lateral_pressure


def build_outcome_pressure_rows(
    candidates: pd.DataFrame,
    *,
    proposals: list[RelocationProposal],
    min_margin_gap: float = DEFAULT_MIN_MARGIN_GAP,
    broad_margin_band: tuple[float, float] = DEFAULT_BROAD_MARGIN_BAND,
    preferred_margin_band: tuple[float, float] = DEFAULT_PREFERRED_MARGIN_BAND,
    max_relocations_per_candidate: int = 6,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if candidates.empty:
        return candidates.copy(), candidates.copy()

    pressure_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    broad_min, broad_max = broad_margin_band
    preferred_min, preferred_max = preferred_margin_band
    for _, row in candidates.iterrows():
        row_proposals: list[dict[str, Any]] = []
        for proposal in proposals:
            pressure = relocation_pressure_proxy(proposal)
            normal_margin = _finite(row.get("normal_margin"))
            variant_margin = _finite(row.get("variant_margin"))
            proxy_normal_margin = normal_margin - pressure
            proxy_variant_margin = variant_margin - pressure
            proxy_margin_gap = proxy_normal_margin - proxy_variant_margin
            broad_hit = bool(broad_min <= proxy_normal_margin <= broad_max)
            preferred_hit = bool(preferred_min <= proxy_normal_margin <= preferred_max)
            proxy_success_drop = bool(proxy_normal_margin >= 0.0 and proxy_variant_margin < 0.0)
            proxy_history_positive = bool(
                row.get("variant_family") == "history"
                and broad_hit
                and (proxy_success_drop or proxy_margin_gap >= float(min_margin_gap))
            )
            item = {
                **row.to_dict(),
                "body_longitudinal_offset": float(proposal.body_longitudinal_offset),
                "body_lateral_offset": float(proposal.body_lateral_offset),
                "half_width_inflation": float(proposal.half_width_inflation),
                "relocation_pressure_proxy": pressure,
                "proxy_normal_margin": proxy_normal_margin,
                "proxy_variant_margin": proxy_variant_margin,
                "proxy_margin_gap": proxy_margin_gap,
                "proxy_normal_margin_band": normal_margin_band(proxy_normal_margin),
                "proxy_broad_normal_margin": broad_hit,
                "proxy_preferred_normal_margin": preferred_hit,
                "proxy_success_drop": proxy_success_drop,
                "proxy_history_positive": proxy_history_positive,
                "requires_replay": True,
                "proxy_only": True,
                "relocated_obstacle_geometry_used": True,
            }
            if broad_hit:
                row_proposals.append(item)
            else:
                rejected_rows.append({**item, "rejection_reason": "proxy_normal_margin_outside_broad_band"})
        row_proposals.sort(
            key=lambda item: (
                not bool(item["proxy_preferred_normal_margin"]),
                not bool(item["proxy_history_positive"]),
                abs(float(item["proxy_normal_margin"]) - 0.10),
                float(item["relocation_pressure_proxy"]),
            )
        )
        pressure_rows.extend(row_proposals[: max(1, int(max_relocations_per_candidate))])
        for item in row_proposals[max(1, int(max_relocations_per_candidate)) :]:
            rejected_rows.append({**item, "rejection_reason": "per_candidate_relocation_cap"})

    return pd.DataFrame(pressure_rows), pd.DataFrame(rejected_rows)


def summarize_variant_rows(rows: pd.DataFrame) -> list[dict[str, Any]]:
    if rows.empty:
        return []
    output: list[dict[str, Any]] = []
    for variant, group in rows.groupby("variant", observed=True):
        output.append(
            {
                "variant": str(variant),
                "variant_family": str(group["variant_family"].iloc[0]),
                "rows": int(len(group)),
                "unique_source_seeds": int(group["seed"].nunique()),
                "unique_capability_pairs": int(group["capability_pair"].nunique()),
                "unique_reveal_buckets": int(group["preferred_reveal_bucket"].nunique()),
                "proxy_history_positive_rows": int(group.get("proxy_history_positive", pd.Series(dtype=bool)).astype(bool).sum()),
                "sequence_action_l2_mean": float(group["sequence_action_l2_mean"].astype(float).mean()),
                "margin_gap_mean": float(group["margin_gap"].astype(float).mean()),
            }
        )
    return output


def _frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.to_dict("records") if not frame.empty else []


def run_action_divergent_outcome_pressure_constructor(
    *,
    outcome_rows_path: Path,
    run_dir: Path,
    max_candidates: int = 256,
    per_capability_pair_cap: int = 32,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
    min_first_action_l2: float = DEFAULT_MIN_FIRST_ACTION_L2,
    min_margin_gap: float = DEFAULT_MIN_MARGIN_GAP,
    max_relocations_per_candidate: int = 6,
    longitudinal_offsets: tuple[float, ...] = DEFAULT_LONGITUDINAL_OFFSETS,
    lateral_offsets: tuple[float, ...] = DEFAULT_LATERAL_OFFSETS,
    half_width_inflations: tuple[float, ...] = DEFAULT_HALF_WIDTH_INFLATIONS,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    outcome_frame = pd.read_csv(outcome_rows_path)
    pool, source_rejections = action_divergent_candidate_pool(
        outcome_frame,
        min_sequence_action_l2=min_sequence_action_l2,
        min_first_action_l2=min_first_action_l2,
    )
    selected = select_source_balanced_candidates(
        pool,
        max_candidates=max_candidates,
        per_capability_pair_cap=per_capability_pair_cap,
    )
    proposals = relocation_grid(
        longitudinal_offsets=longitudinal_offsets,
        lateral_offsets=lateral_offsets,
        half_width_inflations=half_width_inflations,
    )
    pressure, relocation_rejections = build_outcome_pressure_rows(
        selected,
        proposals=proposals,
        min_margin_gap=min_margin_gap,
        max_relocations_per_candidate=max_relocations_per_candidate,
    )
    history_positive = (
        pressure[pressure["proxy_history_positive"].astype(bool)].copy()
        if not pressure.empty and "proxy_history_positive" in pressure.columns
        else pressure.head(0).copy()
    )
    control_action_rows = prepare_outcome_frame(outcome_frame)
    control_action_rows = control_action_rows[
        (control_action_rows["variant_family"] == "control")
        & (
            (control_action_rows["sequence_action_l2_mean"] >= float(min_sequence_action_l2))
            | (
                (float(min_first_action_l2) > 0.0)
                & (control_action_rows["first_action_l2"] >= float(min_first_action_l2))
            )
        )
    ].copy()

    write_csv_rows(run_dir / "candidate_rows.csv", _frame_records(selected), fieldnames=list(selected.columns))
    write_csv_rows(
        run_dir / "outcome_pressure_rows.csv",
        _frame_records(pressure),
        fieldnames=list(pressure.columns),
    )
    write_csv_rows(
        run_dir / "history_positive_rows.csv",
        _frame_records(history_positive),
        fieldnames=list(history_positive.columns),
    )
    variant_summary = summarize_variant_rows(pressure)
    source_diversity_summary = [
        {"row_set": "candidate_rows", **source_diversity(_frame_records(selected))},
        {"row_set": "outcome_pressure_rows", **source_diversity(_frame_records(pressure))},
        {"row_set": "history_positive_rows", **source_diversity(_frame_records(history_positive))},
    ]
    relocation_summary = (
        pressure.groupby(["body_longitudinal_offset", "body_lateral_offset", "half_width_inflation"], observed=True)
        .size()
        .reset_index(name="rows")
        .to_dict("records")
        if not pressure.empty
        else []
    )
    rejected = pd.concat(
        [
            source_rejections.assign(rejection_stage="source_selection") if not source_rejections.empty else source_rejections,
            relocation_rejections.assign(rejection_stage="relocation_proxy")
            if not relocation_rejections.empty
            else relocation_rejections,
        ],
        ignore_index=True,
    )
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "source_diversity_summary.csv", source_diversity_summary)
    write_csv_rows(run_dir / "relocation_summary.csv", relocation_summary)
    write_csv_rows(run_dir / "rejected_rows.csv", _frame_records(rejected), fieldnames=list(rejected.columns))

    history_diversity = source_diversity(_frame_records(history_positive))
    result_class = "action_divergent_outcome_pressure_ready" if len(pressure) else "action_divergent_outcome_pressure_no_rows"
    if len(selected) and not len(history_positive):
        result_class = "action_divergent_outcome_pressure_proxy_no_history_positive"
    summary = {
        "run_type": "action_divergent_outcome_pressure_constructor",
        "outcome_rows_path": outcome_rows_path,
        "input_rows": int(len(outcome_frame)),
        "candidate_pool_rows": int(len(pool)),
        "candidate_rows": int(len(selected)),
        "outcome_pressure_rows": int(len(pressure)),
        "history_positive_rows": int(len(history_positive)),
        "control_action_divergent_rows": int(len(control_action_rows)),
        "source_rejected_rows": int(len(source_rejections)),
        "relocation_rejected_rows": int(len(relocation_rejections)),
        "min_sequence_action_l2": float(min_sequence_action_l2),
        "min_first_action_l2": float(min_first_action_l2),
        "min_margin_gap": float(min_margin_gap),
        "max_candidates": int(max_candidates),
        "per_capability_pair_cap": int(per_capability_pair_cap),
        "max_relocations_per_candidate": int(max_relocations_per_candidate),
        "relocation_grid_size": int(len(proposals)),
        "history_positive_diversity": history_diversity,
        "candidate_diversity": source_diversity(_frame_records(selected)),
        "outcome_pressure_diversity": source_diversity(_frame_records(pressure)),
        "variant_summary": variant_summary,
        "source_diversity_summary": source_diversity_summary,
        "result_class": result_class,
        "proxy_only": True,
        "requires_replay": True,
        "source_smoke_started": False,
        "outcome_probe_started": False,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_parameters_changed": False,
        "actor_input_contract_changed": False,
        "candidate_rows_csv": run_dir / "candidate_rows.csv",
        "outcome_pressure_rows_csv": run_dir / "outcome_pressure_rows.csv",
        "history_positive_rows_csv": run_dir / "history_positive_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "source_diversity_summary_csv": run_dir / "source_diversity_summary.csv",
        "relocation_summary_csv": run_dir / "relocation_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcome-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--max-candidates", type=int, default=256)
    parser.add_argument("--per-capability-pair-cap", type=int, default=32)
    parser.add_argument("--min-sequence-action-l2", type=float, default=DEFAULT_MIN_SEQUENCE_ACTION_L2)
    parser.add_argument("--min-first-action-l2", type=float, default=DEFAULT_MIN_FIRST_ACTION_L2)
    parser.add_argument("--min-margin-gap", type=float, default=DEFAULT_MIN_MARGIN_GAP)
    parser.add_argument("--max-relocations-per-candidate", type=int, default=6)
    parser.add_argument("--longitudinal-offsets", type=_parse_float_list, default=DEFAULT_LONGITUDINAL_OFFSETS)
    parser.add_argument("--lateral-offsets", type=_parse_float_list, default=DEFAULT_LATERAL_OFFSETS)
    parser.add_argument("--half-width-inflations", type=_parse_float_list, default=DEFAULT_HALF_WIDTH_INFLATIONS)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    summary = run_action_divergent_outcome_pressure_constructor(
        outcome_rows_path=args.outcome_rows,
        run_dir=args.run_dir,
        max_candidates=args.max_candidates,
        per_capability_pair_cap=args.per_capability_pair_cap,
        min_sequence_action_l2=args.min_sequence_action_l2,
        min_first_action_l2=args.min_first_action_l2,
        min_margin_gap=args.min_margin_gap,
        max_relocations_per_candidate=args.max_relocations_per_candidate,
        longitudinal_offsets=args.longitudinal_offsets,
        lateral_offsets=args.lateral_offsets,
        half_width_inflations=args.half_width_inflations,
    )
    print(f"summary_json={args.run_dir / 'summary.json'}")
    print(f"candidate_rows={summary['candidate_rows']}")
    print(f"outcome_pressure_rows={summary['outcome_pressure_rows']}")
    print(f"history_positive_rows={summary['history_positive_rows']}")
    print(f"result_class={summary['result_class']}")


if __name__ == "__main__":
    main()
