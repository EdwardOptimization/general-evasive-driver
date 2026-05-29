"""Positive-neighborhood expansion candidate generator."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.source_step_replay_boundary_retarget import DEFAULT_MIN_HALF_WIDTH
from autodrift.warmup_latched_outcome_probe import source_diversity


DEFAULT_DX_GRID = (-1.0, -0.5, 0.0, 0.5, 1.0, 2.0)
DEFAULT_DY_GRID = (-0.4, -0.2, 0.0, 0.2, 0.4)
DEFAULT_DW_GRID = (-0.1, 0.0, 0.1, 0.2)


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


def _string_key(row: dict[str, Any], fields: tuple[str, ...]) -> str:
    return "|".join(str(row.get(field, "")) for field in fields)


def positive_anchor_rows(history_positive_rows: pd.DataFrame) -> pd.DataFrame:
    if history_positive_rows.empty:
        return history_positive_rows.copy()
    frame = history_positive_rows.copy()
    if "history_positive" in frame:
        frame = frame[frame["history_positive"].map(_bool_value)]
    if "control_positive" in frame:
        frame = frame[~frame["control_positive"].map(_bool_value)]
    return frame.reset_index(drop=True)


def anchor_target_grid(
    anchor: dict[str, Any],
    *,
    dx_grid: tuple[float, ...] = DEFAULT_DX_GRID,
    dy_grid: tuple[float, ...] = DEFAULT_DY_GRID,
    dw_grid: tuple[float, ...] = DEFAULT_DW_GRID,
) -> list[dict[str, float | bool]]:
    anchor_x = _finite(anchor.get("relocated_body_x"), _finite(anchor.get("raw_relocated_body_x")))
    anchor_y = _finite(anchor.get("relocated_body_y"))
    anchor_width = _finite(anchor.get("relocated_half_width"), _finite(anchor.get("raw_relocated_half_width")))
    targets: list[dict[str, float | bool]] = []
    for dx in dx_grid:
        for dy in dy_grid:
            for dw in dw_grid:
                targets.append(
                    {
                        "target_body_x": anchor_x + float(dx),
                        "target_body_y": anchor_y + float(dy),
                        "target_half_width": max(DEFAULT_MIN_HALF_WIDTH, anchor_width + float(dw)),
                        "anchor_dx": float(dx),
                        "anchor_dy": float(dy),
                        "anchor_dw": float(dw),
                        "exact_anchor_target": abs(float(dx)) < 1e-12
                        and abs(float(dy)) < 1e-12
                        and abs(float(dw)) < 1e-12,
                    }
                )
    return targets


def _source_signature(row: dict[str, Any]) -> str:
    return _string_key(
        row,
        (
            "seed",
            "candidate_step",
            "preferred_fault",
            "wrong_fault",
            "capability_pair",
            "preferred_reveal_bucket",
        ),
    )


def _source_group(base: dict[str, Any], anchor_signatures: set[str], control_signatures: set[str]) -> tuple[str, bool]:
    signature = _source_signature(base)
    control_source = signature in control_signatures
    if signature in anchor_signatures:
        return "anchor_source", control_source
    if control_source:
        return "control_source", control_source
    return "neighbor_source", control_source


def _proposal_from_base(
    *,
    base: dict[str, Any],
    anchor: dict[str, Any],
    target: dict[str, float | bool],
    anchor_index: int,
    proposal_rank: int,
    anchor_signatures: set[str],
    control_signatures: set[str],
) -> dict[str, Any]:
    source_body_x = _finite(base.get("source_body_x"))
    source_body_y = _finite(base.get("source_body_y"))
    source_half_width = _finite(base.get("source_half_width"))
    target_half_width = float(target["target_half_width"])
    half_width_inflation = max(
        DEFAULT_MIN_HALF_WIDTH - source_half_width,
        target_half_width - source_half_width,
    )
    source_step = int(_finite(base.get("source_step"), _finite(base.get("candidate_step"), _finite(base.get("reveal_step"), 0.0))))
    source_group, control_source = _source_group(base, anchor_signatures, control_signatures)
    exact_source = _source_signature(base) == _source_signature(anchor)
    exact_anchor_target = bool(target["exact_anchor_target"])
    row = {
        "proposal_rank": int(proposal_rank),
        "anchor_index": int(anchor_index),
        "source_group": source_group,
        "control_positive_source": bool(control_source),
        "exact_positive_replay_copy": bool(exact_source and exact_anchor_target),
        "source_index": int(_finite(base.get("source_index"), proposal_rank)),
        "seed": int(_finite(base.get("seed"), 0)),
        "reveal_step": int(_finite(base.get("reveal_step"), source_step)),
        "source_step": int(source_step),
        "candidate_step": int(source_step),
        "candidate_step_column": "source_step",
        "preferred_fault": str(base.get("preferred_fault", "")),
        "wrong_fault": str(base.get("wrong_fault", "")),
        "capability_pair": str(base.get("capability_pair", "")),
        "preferred_reveal_bucket": str(base.get("preferred_reveal_bucket", "")),
        "variant": str(base.get("variant", "")),
        "sequence_action_l2_mean": _finite(base.get("sequence_action_l2_mean"), 0.0),
        "margin_gap": _finite(base.get("margin_gap"), 0.0),
        "source_body_x": source_body_x,
        "source_body_y": source_body_y,
        "source_half_width": source_half_width,
        "target_body_x": float(target["target_body_x"]),
        "target_body_y": float(target["target_body_y"]),
        "target_half_width": target_half_width,
        "anchor_dx": float(target["anchor_dx"]),
        "anchor_dy": float(target["anchor_dy"]),
        "anchor_dw": float(target["anchor_dw"]),
        "body_longitudinal_offset": float(target["target_body_x"]) - source_body_x,
        "body_lateral_offset": float(target["target_body_y"]) - source_body_y,
        "half_width_inflation": float(half_width_inflation),
        "anchor_seed": int(_finite(anchor.get("seed"), 0)),
        "anchor_candidate_step": int(_finite(anchor.get("candidate_step"), _finite(anchor.get("source_step"), 0.0))),
        "anchor_variant": str(anchor.get("variant", "")),
        "anchor_relocation_key": str(anchor.get("relocation_key", "")),
        "anchor_margin_gap": _finite(anchor.get("margin_gap"), 0.0),
    }
    row["positive_neighborhood_key"] = "|".join(
        str(row[key])
        for key in (
            "anchor_index",
            "seed",
            "source_step",
            "preferred_fault",
            "wrong_fault",
            "variant",
            "target_body_x",
            "target_body_y",
            "target_half_width",
        )
    )
    return row


def generate_positive_neighborhood_proposals(
    *,
    history_positive_rows: pd.DataFrame,
    control_positive_rows: pd.DataFrame,
    candidate_pool: pd.DataFrame,
) -> pd.DataFrame:
    anchors = positive_anchor_rows(history_positive_rows)
    if anchors.empty or candidate_pool.empty:
        return pd.DataFrame()
    anchor_signatures = {_source_signature(row) for row in anchors.to_dict("records")}
    control_signatures = {_source_signature(row) for row in control_positive_rows.to_dict("records")}
    proposals: list[dict[str, Any]] = []
    bases = candidate_pool.to_dict("records")
    for anchor_index, anchor in enumerate(anchors.to_dict("records")):
        for target in anchor_target_grid(anchor):
            for base in bases:
                proposals.append(
                    _proposal_from_base(
                        base=base,
                        anchor=anchor,
                        target=target,
                        anchor_index=anchor_index,
                        proposal_rank=len(proposals),
                        anchor_signatures=anchor_signatures,
                        control_signatures=control_signatures,
                    )
                )
    return pd.DataFrame(proposals)


def select_positive_neighborhood_candidates(
    proposals: pd.DataFrame,
    *,
    max_candidates: int,
    per_seed_cap: int,
    per_capability_pair_cap: int,
    per_anchor_cap: int,
    per_variant_cap: int,
) -> pd.DataFrame:
    if proposals.empty:
        return proposals.copy()
    frame = proposals.copy()
    group_priority = {"anchor_source": 0, "neighbor_source": 1, "control_source": 2}
    frame["_group_priority"] = frame["source_group"].map(group_priority).fillna(9).astype(int)
    frame["_exact_copy_priority"] = frame["exact_positive_replay_copy"].map(lambda value: 1 if _bool_value(value) else 0)
    frame["_target_distance"] = (
        pd.to_numeric(frame["anchor_dx"], errors="coerce").abs().fillna(0.0)
        + pd.to_numeric(frame["anchor_dy"], errors="coerce").abs().fillna(0.0)
        + pd.to_numeric(frame["anchor_dw"], errors="coerce").abs().fillna(0.0)
    )
    frame = frame.sort_values(
        ["_group_priority", "_exact_copy_priority", "_target_distance", "sequence_action_l2_mean", "proposal_rank"],
        ascending=[True, True, True, False, True],
    )
    counts: dict[str, Counter] = {
        "seed": Counter(),
        "pair": Counter(),
        "anchor": Counter(),
        "variant": Counter(),
    }
    selected: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        seed = str(row["seed"])
        pair = str(row["capability_pair"])
        anchor = str(row["anchor_index"])
        variant = str(row["variant"])
        if per_seed_cap > 0 and counts["seed"][seed] >= per_seed_cap:
            continue
        if per_capability_pair_cap > 0 and counts["pair"][pair] >= per_capability_pair_cap:
            continue
        if per_anchor_cap > 0 and counts["anchor"][anchor] >= per_anchor_cap:
            continue
        if per_variant_cap > 0 and counts["variant"][variant] >= per_variant_cap:
            continue
        output = row.drop(
            labels=[
                c
                for c in ("_group_priority", "_exact_copy_priority", "_target_distance")
                if c in row.index
            ]
        ).to_dict()
        output["selected_expansion_rank"] = len(selected)
        selected.append(output)
        counts["seed"][seed] += 1
        counts["pair"][pair] += 1
        counts["anchor"][anchor] += 1
        counts["variant"][variant] += 1
        if max_candidates > 0 and len(selected) >= max_candidates:
            break
    return pd.DataFrame(selected)


def build_expansion_summary(
    *,
    anchors: pd.DataFrame,
    control_positive_rows: pd.DataFrame,
    candidate_pool: pd.DataFrame,
    proposals: pd.DataFrame,
    selected: pd.DataFrame,
) -> dict[str, Any]:
    proposal_group_counts = proposals["source_group"].value_counts().to_dict() if "source_group" in proposals else {}
    selected_group_counts = selected["source_group"].value_counts().to_dict() if "source_group" in selected else {}
    return {
        "run_type": "positive_neighborhood_expansion",
        "history_positive_anchor_rows": int(len(anchors)),
        "control_positive_rows": int(len(control_positive_rows)),
        "candidate_pool_rows": int(len(candidate_pool)),
        "proposal_rows": int(len(proposals)),
        "selected_candidate_rows": int(len(selected)),
        "proposal_source_group_counts": {str(k): int(v) for k, v in proposal_group_counts.items()},
        "selected_source_group_counts": {str(k): int(v) for k, v in selected_group_counts.items()},
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


def run_expansion_generation(
    *,
    history_positive_rows: Path,
    control_positive_rows: Path,
    candidate_pool: Path,
    run_dir: Path,
    max_candidates: int = 192,
    per_seed_cap: int = 48,
    per_capability_pair_cap: int = 32,
    per_anchor_cap: int = 96,
    per_variant_cap: int = 96,
) -> dict[str, Any]:
    anchors_raw = pd.read_csv(history_positive_rows)
    controls = pd.read_csv(control_positive_rows)
    pool = pd.read_csv(candidate_pool)
    anchors = positive_anchor_rows(anchors_raw)
    proposals = generate_positive_neighborhood_proposals(
        history_positive_rows=anchors,
        control_positive_rows=controls,
        candidate_pool=pool,
    )
    selected = select_positive_neighborhood_candidates(
        proposals,
        max_candidates=max_candidates,
        per_seed_cap=per_seed_cap,
        per_capability_pair_cap=per_capability_pair_cap,
        per_anchor_cap=per_anchor_cap,
        per_variant_cap=per_variant_cap,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(run_dir / "positive_anchor_rows.csv", anchors.to_dict("records") if not anchors.empty else [])
    write_csv_rows(run_dir / "control_positive_source_rows.csv", controls.to_dict("records") if not controls.empty else [])
    write_csv_rows(run_dir / "positive_neighborhood_proposal_rows.csv", proposals.to_dict("records") if not proposals.empty else [])
    write_csv_rows(run_dir / "positive_neighborhood_candidate_rows.csv", selected.to_dict("records") if not selected.empty else [])
    summary = build_expansion_summary(
        anchors=anchors,
        control_positive_rows=controls,
        candidate_pool=pool,
        proposals=proposals,
        selected=selected,
    )
    summary["history_positive_rows_csv"] = str(history_positive_rows)
    summary["control_positive_rows_csv"] = str(control_positive_rows)
    summary["candidate_pool_csv"] = str(candidate_pool)
    summary["positive_anchor_rows_csv"] = str(run_dir / "positive_anchor_rows.csv")
    summary["control_positive_source_rows_csv"] = str(run_dir / "control_positive_source_rows.csv")
    summary["positive_neighborhood_proposal_rows_csv"] = str(run_dir / "positive_neighborhood_proposal_rows.csv")
    summary["positive_neighborhood_candidate_rows_csv"] = str(run_dir / "positive_neighborhood_candidate_rows.csv")
    summary["summary_json"] = str(run_dir / "summary.json")
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history-positive-rows", type=Path, required=True)
    parser.add_argument("--control-positive-rows", type=Path, required=True)
    parser.add_argument("--candidate-pool", type=Path, required=True)
    parser.add_argument("--max-candidates", type=int, default=192)
    parser.add_argument("--per-seed-cap", type=int, default=48)
    parser.add_argument("--per-capability-pair-cap", type=int, default=32)
    parser.add_argument("--per-anchor-cap", type=int, default=96)
    parser.add_argument("--per-variant-cap", type=int, default=96)
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    run_dir = args.run_dir or make_run_dir(prefix="positive_neighborhood_expansion")
    summary = run_expansion_generation(
        history_positive_rows=args.history_positive_rows,
        control_positive_rows=args.control_positive_rows,
        candidate_pool=args.candidate_pool,
        run_dir=run_dir,
        max_candidates=args.max_candidates,
        per_seed_cap=args.per_seed_cap,
        per_capability_pair_cap=args.per_capability_pair_cap,
        per_anchor_cap=args.per_anchor_cap,
        per_variant_cap=args.per_variant_cap,
    )
    print(f"summary_json={run_dir / 'summary.json'}")
    print(f"proposal_rows={summary['proposal_rows']}")
    print(f"selected_candidate_rows={summary['selected_candidate_rows']}")


if __name__ == "__main__":
    main()
