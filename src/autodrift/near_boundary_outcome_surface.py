"""Select near-boundary matched-history outcome-critical rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


DEFAULT_VARIANTS = (
    "reset_hidden",
    "wrong_matched_history",
    "delayed_history",
    "zero_current_response",
    "zero_action_history",
)


def select_near_boundary_rows(
    frame: pd.DataFrame,
    *,
    variants: tuple[str, ...] = DEFAULT_VARIANTS,
    max_normal_margin: float = 0.20,
    min_normal_margin: float | None = None,
    min_margin_gap: float = 0.02,
    require_normal_success: bool = True,
    require_success_drop: bool = False,
) -> pd.DataFrame:
    required = {
        "variant",
        "normal_margin",
        "margin_gap",
        "normal_success",
        "success_drop",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"outcome intervention CSV is missing columns: {sorted(missing)}")
    selected = frame[frame["variant"].astype(str).isin(variants)].copy()
    selected = selected[np.isfinite(selected["normal_margin"].astype(float))]
    selected = selected[np.isfinite(selected["margin_gap"].astype(float))]
    selected = selected[selected["normal_margin"].astype(float) <= float(max_normal_margin)]
    if min_normal_margin is not None:
        selected = selected[selected["normal_margin"].astype(float) >= float(min_normal_margin)]
    selected = selected[selected["margin_gap"].astype(float) >= float(min_margin_gap)]
    if require_normal_success:
        selected = selected[selected["normal_success"].astype(bool)]
    if require_success_drop:
        selected = selected[selected["success_drop"].astype(bool)]
    return selected.sort_values(["margin_gap", "normal_margin"], ascending=[False, True]).reset_index(drop=True)


def summarize_near_boundary_surface(
    *,
    candidates: pd.DataFrame,
    accepted: pd.DataFrame,
    min_accepted_rows: int,
    required_variants: tuple[str, ...],
) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    group_columns = ["checkpoint_label", "target", "variant"]
    for key, group in accepted.groupby(group_columns, observed=True):
        checkpoint_label, target, variant = key
        summary_rows.append(
            {
                "checkpoint_label": str(checkpoint_label),
                "target": str(target),
                "variant": str(variant),
                "accepted_rows": int(len(group)),
                "unique_pairs": int(group["pair_id"].nunique()) if "pair_id" in group else int(len(group)),
                "normal_margin_mean": float(group["normal_margin"].astype(float).mean()),
                "normal_margin_min": float(group["normal_margin"].astype(float).min()),
                "normal_margin_max": float(group["normal_margin"].astype(float).max()),
                "variant_margin_mean": float(group["variant_margin"].astype(float).mean())
                if "variant_margin" in group
                else float("nan"),
                "margin_gap_mean": float(group["margin_gap"].astype(float).mean()),
                "margin_gap_max": float(group["margin_gap"].astype(float).max()),
                "success_drop_count": int(group["success_drop"].astype(bool).sum()),
                "normal_better_fraction": float(group["normal_better"].astype(bool).mean())
                if "normal_better" in group
                else float("nan"),
            }
        )

    required_variant_counts = {
        variant: int((accepted["variant"].astype(str) == variant).sum())
        for variant in required_variants
    }
    summary_rows.append(
        {
            "checkpoint_label": "__aggregate__",
            "target": "__all__",
            "variant": "__all__",
            "accepted_rows": int(len(accepted)),
            "unique_pairs": int(accepted["pair_id"].nunique()) if "pair_id" in accepted else int(len(accepted)),
            "normal_margin_mean": float(accepted["normal_margin"].astype(float).mean())
            if len(accepted)
            else float("nan"),
            "normal_margin_min": float(accepted["normal_margin"].astype(float).min())
            if len(accepted)
            else float("nan"),
            "normal_margin_max": float(accepted["normal_margin"].astype(float).max())
            if len(accepted)
            else float("nan"),
            "variant_margin_mean": float(accepted["variant_margin"].astype(float).mean())
            if len(accepted) and "variant_margin" in accepted
            else float("nan"),
            "margin_gap_mean": float(accepted["margin_gap"].astype(float).mean())
            if len(accepted)
            else float("nan"),
            "margin_gap_max": float(accepted["margin_gap"].astype(float).max())
            if len(accepted)
            else float("nan"),
            "success_drop_count": int(accepted["success_drop"].astype(bool).sum()) if len(accepted) else 0,
            "normal_better_fraction": float(accepted["normal_better"].astype(bool).mean())
            if len(accepted) and "normal_better" in accepted
            else float("nan"),
            "candidate_rows": int(len(candidates)),
            "min_accepted_rows": int(min_accepted_rows),
            "surface_found": bool(len(accepted) >= int(min_accepted_rows)),
            "required_variant_counts": required_variant_counts,
            "required_variants_present": bool(all(count > 0 for count in required_variant_counts.values())),
        }
    )
    return summary_rows


def run_near_boundary_outcome_surface(
    *,
    outcome_csv: Path,
    variants: tuple[str, ...],
    required_variants: tuple[str, ...],
    max_normal_margin: float,
    min_normal_margin: float | None,
    min_margin_gap: float,
    require_normal_success: bool,
    require_success_drop: bool,
    min_accepted_rows: int,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(outcome_csv)
    accepted = select_near_boundary_rows(
        frame,
        variants=variants,
        max_normal_margin=max_normal_margin,
        min_normal_margin=min_normal_margin,
        min_margin_gap=min_margin_gap,
        require_normal_success=require_normal_success,
        require_success_drop=require_success_drop,
    )
    summary_rows = summarize_near_boundary_surface(
        candidates=frame,
        accepted=accepted,
        min_accepted_rows=min_accepted_rows,
        required_variants=required_variants,
    )
    write_csv_rows(run_dir / "accepted_surface_rows.csv", accepted.to_dict("records"))
    write_csv_rows(run_dir / "surface_summary.csv", summary_rows)
    aggregate = summary_rows[-1] if summary_rows else {}
    summary = {
        "run_type": "near_boundary_outcome_surface",
        "outcome_csv": outcome_csv,
        "variants": variants,
        "required_variants": required_variants,
        "max_normal_margin": float(max_normal_margin),
        "min_normal_margin": min_normal_margin,
        "min_margin_gap": float(min_margin_gap),
        "require_normal_success": bool(require_normal_success),
        "require_success_drop": bool(require_success_drop),
        "min_accepted_rows": int(min_accepted_rows),
        "candidate_rows": int(len(frame)),
        "accepted_rows": int(len(accepted)),
        "unique_pairs": int(accepted["pair_id"].nunique()) if len(accepted) and "pair_id" in accepted else 0,
        "surface_found": bool(aggregate.get("surface_found", False)),
        "required_variants_present": bool(aggregate.get("required_variants_present", False)),
        "accepted_surface_rows_csv": run_dir / "accepted_surface_rows.csv",
        "surface_summary_csv": run_dir / "surface_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_variants(value: str) -> tuple[str, ...]:
    variants = tuple(part.strip() for part in value.split(",") if part.strip())
    if not variants:
        raise argparse.ArgumentTypeError("at least one variant is required")
    return variants


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine near-boundary outcome-critical matched-history rows.")
    parser.add_argument("--outcome-csv", type=Path, required=True)
    parser.add_argument("--variants", type=_parse_variants, default=DEFAULT_VARIANTS)
    parser.add_argument("--required-variants", type=_parse_variants, default=("reset_hidden", "wrong_matched_history"))
    parser.add_argument("--max-normal-margin", type=float, default=0.20)
    parser.add_argument("--min-normal-margin", type=float, default=None)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--allow-normal-failure", action="store_true")
    parser.add_argument("--require-success-drop", action="store_true")
    parser.add_argument("--min-accepted-rows", type=int, default=30)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="near_boundary_outcome_surface")
    summary = run_near_boundary_outcome_surface(
        outcome_csv=args.outcome_csv,
        variants=args.variants,
        required_variants=args.required_variants,
        max_normal_margin=args.max_normal_margin,
        min_normal_margin=args.min_normal_margin,
        min_margin_gap=args.min_margin_gap,
        require_normal_success=not args.allow_normal_failure,
        require_success_drop=args.require_success_drop,
        min_accepted_rows=args.min_accepted_rows,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
