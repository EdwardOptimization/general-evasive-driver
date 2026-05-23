"""Classify wrong-history rows with a normal-margin-aware proof filter."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


def _bool_series(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values.fillna(False)
    return values.astype(str).str.lower().isin(("true", "1", "yes"))


def _optional_bool(frame: pd.DataFrame, key: str, default: bool = False) -> pd.Series:
    if key not in frame:
        return pd.Series([default] * len(frame), index=frame.index, dtype=bool)
    return _bool_series(frame[key])


def _optional_float(frame: pd.DataFrame, key: str, default: float = 0.0) -> pd.Series:
    if key not in frame:
        return pd.Series([default] * len(frame), index=frame.index, dtype=float)
    return pd.to_numeric(frame[key], errors="coerce").fillna(default)


def _counts(frame: pd.DataFrame, key: str) -> dict[str, int]:
    if key not in frame or frame.empty:
        return {}
    return {str(k): int(v) for k, v in frame.groupby(key, observed=True).size().to_dict().items()}


def _max_share(frame: pd.DataFrame, key: str) -> float:
    if key not in frame or frame.empty:
        return 0.0
    counts = frame.groupby(key, observed=True).size()
    return float(counts.max() / len(frame)) if len(frame) else 0.0


def classify_near_boundary_wrong_history(
    candidates: pd.DataFrame,
    *,
    normal_margin_ceiling: float,
    min_margin_gap: float,
    min_return_gap_for_completion_drop: float,
    require_action_prefilter: bool,
) -> pd.DataFrame:
    frame = candidates.copy()
    if "variant" not in frame:
        frame["variant"] = ""
    frame = frame[frame["variant"].astype(str) == "wrong_matched_history"].copy()

    normal_margin = _optional_float(frame, "normal_margin")
    margin_gap = _optional_float(frame, "margin_gap")
    return_gap = _optional_float(frame, "return_gap")
    normal_success = _optional_bool(frame, "normal_success")
    matched_current = _optional_bool(frame, "matched_current_pass", default=True)
    action_prefilter = _optional_bool(frame, "action_prefilter_pass", default=True)
    success_drop = _optional_bool(frame, "success_drop")
    collision_gap = _optional_bool(frame, "collision_gap")
    completion_drop = _optional_bool(frame, "obstacle_completion_drop")

    near_boundary = matched_current & normal_success & (normal_margin > 0.0) & (
        normal_margin <= float(normal_margin_ceiling)
    )
    completion_degradation = completion_drop & (return_gap >= float(min_return_gap_for_completion_drop))
    margin_degradation = margin_gap >= float(min_margin_gap)
    outcome_degradation = success_drop | collision_gap | completion_degradation | margin_degradation
    proof_candidate = near_boundary & outcome_degradation
    if require_action_prefilter:
        proof_candidate &= action_prefilter

    high_slack_diagnostic = matched_current & normal_success & (normal_margin > float(normal_margin_ceiling)) & (
        outcome_degradation | _optional_bool(frame, "accepted")
    )

    frame["near_boundary_candidate"] = near_boundary
    frame["completion_degradation"] = completion_degradation
    frame["margin_degradation"] = margin_degradation
    frame["outcome_degradation"] = outcome_degradation
    frame["proof_candidate"] = proof_candidate
    frame["near_boundary_no_effect"] = near_boundary & ~proof_candidate
    frame["high_slack_diagnostic"] = high_slack_diagnostic
    return frame


def summarize_near_boundary_selection(
    classified: pd.DataFrame,
    *,
    min_proof_rows: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    min_success_or_collision_or_completion_rows: int,
    max_single_seed_share: float,
    max_single_label_share: float,
) -> dict[str, Any]:
    near_boundary = classified[classified["near_boundary_candidate"].astype(bool)]
    proof = classified[classified["proof_candidate"].astype(bool)]
    no_effect = classified[classified["near_boundary_no_effect"].astype(bool)]
    high_slack = classified[classified["high_slack_diagnostic"].astype(bool)]
    success_or_collision_or_completion = proof[
        proof["success_drop"].astype(bool)
        | proof["collision_gap"].astype(bool)
        | proof["completion_degradation"].astype(bool)
    ]
    proof_seed_count = int(proof["probe_seed"].nunique()) if "probe_seed" in proof else 0
    proof_label_count = int(proof["left_obstacle_label"].nunique()) if "left_obstacle_label" in proof else 0
    proof_target_count = int(proof["target"].nunique()) if "target" in proof else 0
    single_seed_share = _max_share(proof, "probe_seed")
    single_label_share = _max_share(proof, "left_obstacle_label")
    gate_pass = (
        len(proof) >= int(min_proof_rows)
        and proof_seed_count >= int(min_probe_seed_count)
        and proof_label_count >= int(min_obstacle_label_count)
        and proof_target_count >= int(min_target_count)
        and len(success_or_collision_or_completion) >= int(min_success_or_collision_or_completion_rows)
        and single_seed_share <= float(max_single_seed_share)
        and single_label_share <= float(max_single_label_share)
    )
    normal_margin = _optional_float(classified, "normal_margin")
    high_slack_margin = _optional_float(high_slack, "normal_margin") if len(high_slack) else pd.Series([], dtype=float)
    return {
        "wrong_history_row_count": int(len(classified)),
        "near_boundary_candidate_count": int(len(near_boundary)),
        "proof_candidate_count": int(len(proof)),
        "near_boundary_no_effect_count": int(len(no_effect)),
        "high_slack_diagnostic_count": int(len(high_slack)),
        "proof_success_drop_rows": int(_optional_bool(proof, "success_drop").sum()),
        "proof_collision_gap_rows": int(_optional_bool(proof, "collision_gap").sum()),
        "proof_completion_degradation_rows": int(proof["completion_degradation"].astype(bool).sum())
        if "completion_degradation" in proof
        else 0,
        "proof_margin_degradation_rows": int(proof["margin_degradation"].astype(bool).sum())
        if "margin_degradation" in proof
        else 0,
        "proof_success_or_collision_or_completion_rows": int(len(success_or_collision_or_completion)),
        "proof_probe_seed_count": proof_seed_count,
        "proof_obstacle_label_count": proof_label_count,
        "proof_target_count": proof_target_count,
        "proof_single_seed_share": single_seed_share,
        "proof_single_label_share": single_label_share,
        "proof_by_probe_seed": _counts(proof, "probe_seed"),
        "proof_by_left_obstacle_label": _counts(proof, "left_obstacle_label"),
        "proof_by_target": _counts(proof, "target"),
        "near_boundary_by_left_obstacle_label": _counts(near_boundary, "left_obstacle_label"),
        "near_boundary_by_probe_seed": _counts(near_boundary, "probe_seed"),
        "high_slack_by_left_obstacle_label": _counts(high_slack, "left_obstacle_label"),
        "normal_margin_min": float(normal_margin.min()) if len(normal_margin) else None,
        "normal_margin_max": float(normal_margin.max()) if len(normal_margin) else None,
        "high_slack_normal_margin_min": float(high_slack_margin.min()) if len(high_slack_margin) else None,
        "high_slack_normal_margin_max": float(high_slack_margin.max()) if len(high_slack_margin) else None,
        "wrong_history_gate_pass": bool(gate_pass),
    }


def run_selector(
    *,
    candidates_csv: Path,
    normal_margin_ceiling: float,
    min_margin_gap: float,
    min_return_gap_for_completion_drop: float,
    require_action_prefilter: bool,
    min_proof_rows: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    min_success_or_collision_or_completion_rows: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    candidates = pd.read_csv(candidates_csv)
    classified = classify_near_boundary_wrong_history(
        candidates,
        normal_margin_ceiling=normal_margin_ceiling,
        min_margin_gap=min_margin_gap,
        min_return_gap_for_completion_drop=min_return_gap_for_completion_drop,
        require_action_prefilter=require_action_prefilter,
    )
    near_boundary = classified[classified["near_boundary_candidate"].astype(bool)]
    proof = classified[classified["proof_candidate"].astype(bool)]
    no_effect = classified[classified["near_boundary_no_effect"].astype(bool)]
    high_slack = classified[classified["high_slack_diagnostic"].astype(bool)]
    write_csv_rows(run_dir / "wrong_history_classified.csv", classified.to_dict(orient="records"), fieldnames=list(classified.columns))
    write_csv_rows(run_dir / "near_boundary_candidates.csv", near_boundary.to_dict(orient="records"), fieldnames=list(classified.columns))
    write_csv_rows(run_dir / "proof_candidates.csv", proof.to_dict(orient="records"), fieldnames=list(classified.columns))
    write_csv_rows(
        run_dir / "near_boundary_no_effect.csv",
        no_effect.to_dict(orient="records"),
        fieldnames=list(classified.columns),
    )
    write_csv_rows(
        run_dir / "high_slack_diagnostics.csv",
        high_slack.to_dict(orient="records"),
        fieldnames=list(classified.columns),
    )
    selection_summary = summarize_near_boundary_selection(
        classified,
        min_proof_rows=min_proof_rows,
        min_probe_seed_count=min_probe_seed_count,
        min_obstacle_label_count=min_obstacle_label_count,
        min_target_count=min_target_count,
        min_success_or_collision_or_completion_rows=min_success_or_collision_or_completion_rows,
        max_single_seed_share=max_single_seed_share,
        max_single_label_share=max_single_label_share,
    )
    summary = {
        "run_type": "near_boundary_wrong_history_selector",
        "candidates_csv": candidates_csv,
        "normal_margin_ceiling": float(normal_margin_ceiling),
        "min_margin_gap": float(min_margin_gap),
        "min_return_gap_for_completion_drop": float(min_return_gap_for_completion_drop),
        "require_action_prefilter": bool(require_action_prefilter),
        "min_proof_rows": int(min_proof_rows),
        "min_probe_seed_count": int(min_probe_seed_count),
        "min_obstacle_label_count": int(min_obstacle_label_count),
        "min_target_count": int(min_target_count),
        "min_success_or_collision_or_completion_rows": int(min_success_or_collision_or_completion_rows),
        "max_single_seed_share": float(max_single_seed_share),
        "max_single_label_share": float(max_single_label_share),
        **selection_summary,
        "wrong_history_classified_csv": run_dir / "wrong_history_classified.csv",
        "near_boundary_candidates_csv": run_dir / "near_boundary_candidates.csv",
        "proof_candidates_csv": run_dir / "proof_candidates.csv",
        "near_boundary_no_effect_csv": run_dir / "near_boundary_no_effect.csv",
        "high_slack_diagnostics_csv": run_dir / "high_slack_diagnostics.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify near-boundary wrong-history proof rows.")
    parser.add_argument("--candidates-csv", type=Path, required=True)
    parser.add_argument("--normal-margin-ceiling", type=float, default=0.75)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--min-return-gap-for-completion-drop", type=float, default=1.0)
    parser.add_argument("--disable-action-prefilter", action="store_true")
    parser.add_argument("--min-proof-rows", type=int, default=16)
    parser.add_argument("--min-probe-seed-count", type=int, default=3)
    parser.add_argument("--min-obstacle-label-count", type=int, default=2)
    parser.add_argument("--min-target-count", type=int, default=2)
    parser.add_argument("--min-success-or-collision-or-completion-rows", type=int, default=4)
    parser.add_argument("--max-single-seed-share", type=float, default=0.50)
    parser.add_argument("--max-single-label-share", type=float, default=0.60)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="near_boundary_wrong_history_selector")
    summary = run_selector(
        candidates_csv=args.candidates_csv,
        normal_margin_ceiling=args.normal_margin_ceiling,
        min_margin_gap=args.min_margin_gap,
        min_return_gap_for_completion_drop=args.min_return_gap_for_completion_drop,
        require_action_prefilter=not args.disable_action_prefilter,
        min_proof_rows=args.min_proof_rows,
        min_probe_seed_count=args.min_probe_seed_count,
        min_obstacle_label_count=args.min_obstacle_label_count,
        min_target_count=args.min_target_count,
        min_success_or_collision_or_completion_rows=args.min_success_or_collision_or_completion_rows,
        max_single_seed_share=args.max_single_seed_share,
        max_single_label_share=args.max_single_label_share,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
