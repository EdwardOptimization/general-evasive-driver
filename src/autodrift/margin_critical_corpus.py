"""Mine margin-critical obstacle seeds from shared-seed benchmark outputs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.seed_delta_audit import build_seed_delta_audit, load_episodes


DEFAULT_GROUP_COLUMNS = [
    "obstacle_label",
    "mu_bucket",
    "initial_mu_bucket",
    "mass_bucket",
    "cg_bucket",
    "brake_bucket",
    "tire_bucket",
    "steering_tau_bucket",
]


def load_episode_sources(paths: list[Path | str]) -> pd.DataFrame:
    if not paths:
        raise ValueError("at least one episodes CSV is required")
    frames = []
    for path_like in paths:
        path = Path(path_like)
        frame = load_episodes(path)
        frame = frame.copy()
        frame["source"] = path.parent.name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def build_source_seed_delta(
    frame: pd.DataFrame,
    *,
    baseline_policy: str,
    candidate_policies: list[str],
) -> pd.DataFrame:
    if "source" not in frame:
        return build_seed_delta_audit(
            frame,
            baseline_policy=baseline_policy,
            candidate_policies=candidate_policies,
        )
    deltas = []
    for source, group in frame.groupby("source", sort=False, observed=True):
        source_delta = build_seed_delta_audit(
            group.drop(columns=["source"]),
            baseline_policy=baseline_policy,
            candidate_policies=candidate_policies,
        )
        source_delta.insert(0, "source", source)
        deltas.append(source_delta)
    if not deltas:
        raise ValueError("episodes frame is empty")
    return pd.concat(deltas, ignore_index=True)


def _margin_bucket(series: pd.Series, near_margin: float) -> pd.Series:
    near = max(float(near_margin), 1e-9)
    values = series.astype(float)
    labels = np.full(len(values), "missing", dtype=object)
    finite = np.isfinite(values)
    labels[finite & (values < -near)] = "collision_deep"
    labels[finite & (values >= -near) & (values < 0.0)] = "collision_near"
    labels[finite & (values >= 0.0) & (values <= near)] = "success_near"
    labels[finite & (values > near)] = "success_clear"
    return pd.Series(labels, index=series.index)


def _critical_reasons(row: pd.Series) -> str:
    reasons: list[str] = []
    if bool(row["binary_outcome_changed"]):
        reasons.append("binary_outcome_changed")
    if bool(row["near_boundary"]):
        reasons.append("near_boundary")
    if bool(row["near_margin_regressed"]):
        reasons.append("near_margin_regressed")
    if bool(row["success_preserved_margin_regressed"]):
        reasons.append("success_preserved_margin_regressed")
    if bool(row["low_margin_success"]):
        reasons.append("low_margin_success")
    if bool(row["small_penetration_collision"]):
        reasons.append("small_penetration_collision")
    return ";".join(reasons)


def add_margin_critical_features(
    deltas: pd.DataFrame,
    *,
    near_margin: float,
    min_abs_margin_delta: float,
) -> pd.DataFrame:
    required = {
        "baseline_min_clearance_margin",
        "candidate_min_clearance_margin",
        "min_clearance_margin_delta",
        "baseline_success",
        "candidate_success",
        "outcome",
    }
    missing = sorted(required.difference(deltas.columns))
    if missing:
        raise ValueError(f"seed deltas are missing margin columns: {missing}")

    output = deltas.copy()
    near = max(float(near_margin), 0.0)
    min_delta = max(float(min_abs_margin_delta), 0.0)
    baseline_margin = output["baseline_min_clearance_margin"].astype(float)
    candidate_margin = output["candidate_min_clearance_margin"].astype(float)
    margin_delta = output["min_clearance_margin_delta"].astype(float)
    output["baseline_margin_bucket"] = _margin_bucket(baseline_margin, near)
    output["candidate_margin_bucket"] = _margin_bucket(candidate_margin, near)
    output["worst_margin"] = np.minimum(baseline_margin, candidate_margin)
    output["worst_margin_bucket"] = _margin_bucket(output["worst_margin"], near)
    output["min_abs_margin"] = np.minimum(baseline_margin.abs(), candidate_margin.abs())
    output["binary_outcome_changed"] = output["outcome"].isin(["improved", "regressed"])
    output["near_boundary"] = output["min_abs_margin"] <= near
    output["margin_regressed"] = margin_delta <= -min_delta
    output["margin_improved"] = margin_delta >= min_delta
    output["near_margin_regressed"] = output["margin_regressed"].astype(bool) & output["near_boundary"].astype(bool)
    output["success_preserved_margin_regressed"] = (
        output["baseline_success"].astype(bool)
        & output["candidate_success"].astype(bool)
        & output["near_margin_regressed"].astype(bool)
    )
    output["low_margin_success"] = output["candidate_success"].astype(bool) & (candidate_margin >= 0.0) & (candidate_margin <= near)
    output["small_penetration_collision"] = (
        ~output["candidate_success"].astype(bool)
        & (candidate_margin < 0.0)
        & (candidate_margin >= -near)
    )
    output["critical_reason"] = output.apply(_critical_reasons, axis=1)
    near_scale = max(near, 1e-9)
    delta_scale = max(min_delta, 1e-9)
    boundary_score = np.clip((near - output["min_abs_margin"].astype(float)) / near_scale, 0.0, None)
    output["margin_critical_score"] = (
        10.0 * output["binary_outcome_changed"].astype(float)
        + 6.0 * output["near_margin_regressed"].astype(float)
        + 4.0 * output["success_preserved_margin_regressed"].astype(float)
        + 3.0 * output["low_margin_success"].astype(float)
        + 3.0 * output["small_penetration_collision"].astype(float)
        + boundary_score
        + 0.5 * (margin_delta.abs() / delta_scale)
    )
    return output


def select_margin_critical_corpus(deltas: pd.DataFrame, *, top_k: int) -> pd.DataFrame:
    critical = deltas[deltas["critical_reason"].astype(str) != ""].copy()
    critical = critical.sort_values(
        ["margin_critical_score", "binary_outcome_changed", "near_margin_regressed", "seed", "candidate_policy"],
        ascending=[False, False, False, True, True],
    )
    return critical.head(max(0, int(top_k))).reset_index(drop=True)


def summarize_policy_margins(deltas: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_policy, group in deltas.groupby("candidate_policy", observed=True):
        rows.append(
            {
                "baseline_policy": str(group["baseline_policy"].iloc[0]),
                "candidate_policy": candidate_policy,
                "pairs": int(len(group)),
                "critical_seeds": int((group["critical_reason"].astype(str) != "").sum()),
                "near_boundary_seeds": int(group["near_boundary"].sum()),
                "binary_outcome_changed_seeds": int(group["binary_outcome_changed"].sum()),
                "margin_regressed_seeds": int(group["margin_regressed"].sum()),
                "near_margin_regressed_seeds": int(group["near_margin_regressed"].sum()),
                "margin_improved_seeds": int(group["margin_improved"].sum()),
                "success_preserved_margin_regressed_seeds": int(
                    group["success_preserved_margin_regressed"].sum()
                ),
                "baseline_success_rate": float(group["baseline_success"].mean()),
                "candidate_success_rate": float(group["candidate_success"].mean()),
                "baseline_margin_mean": float(group["baseline_min_clearance_margin"].mean()),
                "candidate_margin_mean": float(group["candidate_min_clearance_margin"].mean()),
                "margin_delta_mean": float(group["min_clearance_margin_delta"].mean()),
                "worst_margin_min": float(group["worst_margin"].min()),
                "critical_score_max": float(group["margin_critical_score"].max()),
            }
        )
    return pd.DataFrame(rows).sort_values("candidate_policy").reset_index(drop=True)


def summarize_margin_buckets(deltas: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    columns = ["candidate_margin_bucket", "worst_margin_bucket", *group_columns]
    for column in columns:
        if column not in deltas:
            continue
        valid = deltas[~deltas[column].isna()].copy()
        if valid.empty:
            continue
        valid[column] = valid[column].astype(str)
        for (candidate_policy, group_value), group in valid.groupby(["candidate_policy", column], observed=True):
            rows.append(
                {
                    "candidate_policy": candidate_policy,
                    "group_column": column,
                    "group_value": group_value,
                    "pairs": int(len(group)),
                    "critical_seeds": int((group["critical_reason"].astype(str) != "").sum()),
                    "near_boundary_seeds": int(group["near_boundary"].sum()),
                    "margin_regressed_seeds": int(group["margin_regressed"].sum()),
                    "near_margin_regressed_seeds": int(group["near_margin_regressed"].sum()),
                    "binary_outcome_changed_seeds": int(group["binary_outcome_changed"].sum()),
                    "baseline_success_rate": float(group["baseline_success"].mean()),
                    "candidate_success_rate": float(group["candidate_success"].mean()),
                    "margin_delta_mean": float(group["min_clearance_margin_delta"].mean()),
                    "candidate_margin_mean": float(group["candidate_min_clearance_margin"].mean()),
                    "worst_margin_min": float(group["worst_margin"].min()),
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "candidate_policy",
                "group_column",
                "group_value",
                "pairs",
                "critical_seeds",
                "near_boundary_seeds",
                "margin_regressed_seeds",
                "near_margin_regressed_seeds",
                "binary_outcome_changed_seeds",
                "baseline_success_rate",
                "candidate_success_rate",
                "margin_delta_mean",
                "candidate_margin_mean",
                "worst_margin_min",
            ]
        )
    output = pd.DataFrame(rows)
    return output.sort_values(
        ["candidate_policy", "critical_seeds", "near_margin_regressed_seeds", "near_boundary_seeds", "group_column"],
        ascending=[True, False, False, False, True],
    ).reset_index(drop=True)


def build_margin_critical_corpus(
    frame: pd.DataFrame,
    *,
    baseline_policy: str,
    candidate_policies: list[str],
    near_margin: float,
    min_abs_margin_delta: float,
    top_k: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw_deltas = build_source_seed_delta(
        frame,
        baseline_policy=baseline_policy,
        candidate_policies=candidate_policies,
    )
    deltas = add_margin_critical_features(
        raw_deltas,
        near_margin=near_margin,
        min_abs_margin_delta=min_abs_margin_delta,
    )
    corpus = select_margin_critical_corpus(deltas, top_k=top_k)
    policy_summary = summarize_policy_margins(deltas)
    bucket_summary = summarize_margin_buckets(deltas, DEFAULT_GROUP_COLUMNS)
    return deltas, corpus, policy_summary, bucket_summary


def write_margin_critical_corpus(
    run_dir: Path,
    *,
    episodes_csvs: list[Path | str],
    baseline_policy: str,
    candidate_policies: list[str],
    near_margin: float,
    min_abs_margin_delta: float,
    top_k: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = load_episode_sources(episodes_csvs)
    deltas, corpus, policy_summary, bucket_summary = build_margin_critical_corpus(
        frame,
        baseline_policy=baseline_policy,
        candidate_policies=candidate_policies,
        near_margin=near_margin,
        min_abs_margin_delta=min_abs_margin_delta,
        top_k=top_k,
    )
    seed_delta_csv = run_dir / "seed_margin_deltas.csv"
    corpus_csv = run_dir / "scenario_corpus.csv"
    policy_summary_csv = run_dir / "policy_margin_summary.csv"
    bucket_summary_csv = run_dir / "margin_bucket_summary.csv"
    deltas.to_csv(seed_delta_csv, index=False)
    corpus.to_csv(corpus_csv, index=False)
    policy_summary.to_csv(policy_summary_csv, index=False)
    bucket_summary.to_csv(bucket_summary_csv, index=False)
    manifest = {
        "run_type": "margin_critical_corpus",
        "episodes_csvs": [str(path) for path in episodes_csvs],
        "baseline_policy": baseline_policy,
        "candidate_policies": candidate_policies,
        "near_margin": float(near_margin),
        "min_abs_margin_delta": float(min_abs_margin_delta),
        "top_k": int(top_k),
        "artifacts": {
            "seed_delta_csv": str(seed_delta_csv),
            "corpus_csv": str(corpus_csv),
            "policy_summary_csv": str(policy_summary_csv),
            "bucket_summary_csv": str(bucket_summary_csv),
        },
        "summary": {
            "pairs": int(len(deltas)),
            "selected_count": int(len(corpus)),
            "critical_count": int((deltas["critical_reason"].astype(str) != "").sum()),
            "near_boundary_count": int(deltas["near_boundary"].sum()),
            "margin_regressed_count": int(deltas["margin_regressed"].sum()),
            "binary_outcome_changed_count": int(deltas["binary_outcome_changed"].sum()),
        },
    }
    write_json(run_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine margin-critical obstacle seeds.")
    parser.add_argument("--episodes-csv", action="append", type=Path, required=True)
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--candidate-policy", action="append", default=[])
    parser.add_argument("--near-margin", type=float, default=0.02)
    parser.add_argument("--min-abs-margin-delta", type=float, default=0.01)
    parser.add_argument("--top-k", type=int, default=80)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    if not args.candidate_policy:
        raise ValueError("at least one --candidate-policy is required")

    run_dir = args.run_dir or make_run_dir(prefix="margin_critical_corpus")
    manifest = write_margin_critical_corpus(
        run_dir,
        episodes_csvs=args.episodes_csv,
        baseline_policy=args.baseline_policy,
        candidate_policies=args.candidate_policy,
        near_margin=args.near_margin,
        min_abs_margin_delta=args.min_abs_margin_delta,
        top_k=args.top_k,
    )
    print(pd.Series(manifest["summary"]).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
