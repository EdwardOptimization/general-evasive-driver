"""Mine response-history necessity seeds from paired perturbation outputs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.seed_delta_audit import load_episodes


REQUIRED_COLUMNS = {"seed", "policy", "condition", "success", "return"}
DEFAULT_MARGIN_COLUMN = "min_clearance_margin"


def load_paired_episodes(path: Path | str) -> pd.DataFrame:
    frame = load_episodes(path)
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"paired episodes CSV is missing columns: {missing}")
    duplicated = frame.duplicated(["seed", "policy", "condition"], keep=False)
    if duplicated.any():
        sample = frame.loc[duplicated, ["seed", "policy", "condition"]].head(5).to_dict("records")
        raise ValueError(f"paired episodes CSV has duplicate rows, sample={sample}")
    return frame


def _condition_policy_view(frame: pd.DataFrame, *, condition: str, policy: str) -> pd.DataFrame:
    view = frame[(frame["condition"].astype(str) == condition) & (frame["policy"].astype(str) == policy)]
    return view.drop(columns=["condition", "policy"]).set_index("seed")


def _finite_float(value: Any, default: float = np.nan) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if np.isfinite(output) else default


def _reason_list(row: dict[str, Any], *, near_margin: float) -> str:
    reasons: list[str] = []
    hard_perturbation = (
        row["baseline_nominal_success"] and not row["baseline_perturbed_success"]
    ) or row["baseline_perturbed_margin"] <= near_margin
    if row["baseline_nominal_success"] and not row["baseline_perturbed_success"]:
        reasons.append("perturbation_regression")
    if row["baseline_perturbed_margin"] <= near_margin:
        reasons.append("low_perturbed_margin")
    if hard_perturbation and row["ablation_not_worse_count"] > 0:
        reasons.append("ablation_not_worse")
    if hard_perturbation and row["ablation_worse_count"] == 0:
        reasons.append("no_ablation_success_penalty")
    return ";".join(reasons)


def build_response_necessity_features(
    frame: pd.DataFrame,
    *,
    baseline_policy: str,
    ablation_policies: list[str],
    nominal_condition: str = "nominal",
    perturbed_condition: str = "perturbed",
    near_margin: float = 0.05,
    margin_scale: float = 0.25,
) -> pd.DataFrame:
    if not ablation_policies:
        raise ValueError("at least one ablation policy is required")
    missing_columns = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"episodes frame is missing columns: {missing_columns}")
    if DEFAULT_MARGIN_COLUMN not in frame.columns:
        raise ValueError(f"episodes frame is missing {DEFAULT_MARGIN_COLUMN!r}")

    available_policies = set(frame["policy"].astype(str))
    missing_policies = sorted({baseline_policy, *ablation_policies}.difference(available_policies))
    if missing_policies:
        raise ValueError(f"missing policies in episodes frame: {missing_policies}")
    available_conditions = set(frame["condition"].astype(str))
    missing_conditions = sorted({nominal_condition, perturbed_condition}.difference(available_conditions))
    if missing_conditions:
        raise ValueError(f"missing conditions in episodes frame: {missing_conditions}")

    nominal = _condition_policy_view(frame, condition=nominal_condition, policy=baseline_policy)
    perturbed = _condition_policy_view(frame, condition=perturbed_condition, policy=baseline_policy)
    joined = nominal.join(perturbed, how="inner", lsuffix="_nominal", rsuffix="_perturbed")
    if joined.empty:
        raise ValueError("baseline policy has no shared seeds between nominal and perturbed conditions")

    ablation_views = {
        policy: _condition_policy_view(frame, condition=perturbed_condition, policy=policy) for policy in ablation_policies
    }
    near = max(float(near_margin), 0.0)
    margin_norm = max(float(margin_scale), 1e-9)
    rows: list[dict[str, Any]] = []
    for seed, row in joined.sort_index().iterrows():
        baseline_nominal_success = bool(row["success_nominal"])
        baseline_perturbed_success = bool(row["success_perturbed"])
        nominal_margin = _finite_float(row[f"{DEFAULT_MARGIN_COLUMN}_nominal"])
        perturbed_margin = _finite_float(row[f"{DEFAULT_MARGIN_COLUMN}_perturbed"])
        nominal_return = _finite_float(row["return_nominal"])
        perturbed_return = _finite_float(row["return_perturbed"])

        success_drop = int(baseline_nominal_success) - int(baseline_perturbed_success)
        margin_drop = nominal_margin - perturbed_margin
        return_drop = nominal_return - perturbed_return
        ablation_success_deltas: list[int] = []
        ablation_margin_deltas: list[float] = []
        ablation_return_deltas: list[float] = []
        missing_ablation_count = 0

        for policy, view in ablation_views.items():
            if seed not in view.index:
                missing_ablation_count += 1
                continue
            ablation = view.loc[seed]
            ablation_success_deltas.append(int(bool(ablation["success"])) - int(baseline_perturbed_success))
            ablation_margin_deltas.append(_finite_float(ablation[DEFAULT_MARGIN_COLUMN]) - perturbed_margin)
            ablation_return_deltas.append(_finite_float(ablation["return"]) - perturbed_return)

        ablation_not_worse_count = int(
            sum(
                success_delta >= 0 and margin_delta >= -near
                for success_delta, margin_delta in zip(ablation_success_deltas, ablation_margin_deltas, strict=True)
            )
        )
        ablation_worse_count = int(sum(success_delta < 0 for success_delta in ablation_success_deltas))
        row_item: dict[str, Any] = {
            "seed": int(seed),
            "baseline_policy": baseline_policy,
            "baseline_nominal_success": baseline_nominal_success,
            "baseline_perturbed_success": baseline_perturbed_success,
            "baseline_success_drop": success_drop,
            "baseline_nominal_return": nominal_return,
            "baseline_perturbed_return": perturbed_return,
            "baseline_return_drop": return_drop,
            "baseline_nominal_margin": nominal_margin,
            "baseline_perturbed_margin": perturbed_margin,
            "baseline_margin_drop": margin_drop,
            "ablation_count": len(ablation_policies),
            "missing_ablation_count": missing_ablation_count,
            "ablation_not_worse_count": ablation_not_worse_count,
            "ablation_worse_count": ablation_worse_count,
            "ablation_success_delta_min": min(ablation_success_deltas) if ablation_success_deltas else 0,
            "ablation_success_delta_max": max(ablation_success_deltas) if ablation_success_deltas else 0,
            "ablation_margin_delta_min": min(ablation_margin_deltas) if ablation_margin_deltas else 0.0,
            "ablation_margin_delta_max": max(ablation_margin_deltas) if ablation_margin_deltas else 0.0,
            "ablation_return_delta_min": min(ablation_return_deltas) if ablation_return_deltas else 0.0,
            "ablation_return_delta_max": max(ablation_return_deltas) if ablation_return_deltas else 0.0,
        }
        row_item["critical_reason"] = _reason_list(row_item, near_margin=near)
        hard_perturbation = bool(success_drop > 0 or perturbed_margin <= near)
        ablation_insensitivity_bonus = (
            2.0 * (ablation_not_worse_count / max(1, len(ablation_policies))) - 1.0 * ablation_worse_count
            if hard_perturbation
            else 0.0
        )
        row_item["response_necessity_score"] = (
            10.0 * float(success_drop > 0)
            + 3.0 * float(not baseline_perturbed_success)
            + 2.0 * float(perturbed_margin <= near)
            + max(0.0, margin_drop) / margin_norm
            + 0.05 * max(0.0, return_drop)
            + ablation_insensitivity_bonus
        )
        rows.append(row_item)

    output = pd.DataFrame(rows)
    return output.sort_values(["response_necessity_score", "seed"], ascending=[False, True]).reset_index(drop=True)


def select_response_necessity_corpus(features: pd.DataFrame, *, top_k: int) -> pd.DataFrame:
    critical = features[features["critical_reason"].astype(str) != ""].copy()
    critical = critical.sort_values(["response_necessity_score", "baseline_margin_drop", "seed"], ascending=[False, False, True])
    return critical.head(max(0, int(top_k))).reset_index(drop=True)


def build_seed_sequence(corpus: pd.DataFrame, *, repeat: int) -> pd.DataFrame:
    repeats = max(1, int(repeat))
    rows: list[dict[str, Any]] = []
    for rank, row in enumerate(corpus.itertuples(index=False), start=1):
        for _ in range(repeats):
            rows.append(
                {
                    "seed": int(row.seed),
                    "rank": rank,
                    "response_necessity_score": float(row.response_necessity_score),
                    "critical_reason": str(row.critical_reason),
                }
            )
    return pd.DataFrame(rows, columns=["seed", "rank", "response_necessity_score", "critical_reason"])


def summarize_response_necessity(features: pd.DataFrame, *, near_margin: float = 0.05) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "seeds": int(len(features)),
                "critical_seeds": int((features["critical_reason"].astype(str) != "").sum()),
                "perturbation_regressions": int(
                    (features["baseline_nominal_success"] & ~features["baseline_perturbed_success"]).sum()
                ),
                "low_perturbed_margin_seeds": int((features["baseline_perturbed_margin"] <= float(near_margin)).sum()),
                "ablation_not_worse_seeds": int((features["ablation_not_worse_count"] > 0).sum()),
                "score_mean": float(features["response_necessity_score"].mean()) if len(features) else 0.0,
                "score_max": float(features["response_necessity_score"].max()) if len(features) else 0.0,
            }
        ]
    )


def write_response_necessity_corpus(
    run_dir: Path,
    *,
    episodes_csv: Path | str,
    baseline_policy: str,
    ablation_policies: list[str],
    top_k: int,
    repeat: int,
    near_margin: float = 0.05,
    margin_scale: float = 0.25,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = load_paired_episodes(episodes_csv)
    features = build_response_necessity_features(
        frame,
        baseline_policy=baseline_policy,
        ablation_policies=ablation_policies,
        near_margin=near_margin,
        margin_scale=margin_scale,
    )
    corpus = select_response_necessity_corpus(features, top_k=top_k)
    seed_sequence = build_seed_sequence(corpus, repeat=repeat)
    summary = summarize_response_necessity(features, near_margin=near_margin)

    feature_csv = run_dir / "seed_response_necessity.csv"
    corpus_csv = run_dir / "scenario_corpus.csv"
    seed_sequence_csv = run_dir / "seed_sequence.csv"
    summary_csv = run_dir / "summary.csv"
    features.to_csv(feature_csv, index=False)
    corpus.to_csv(corpus_csv, index=False)
    seed_sequence.to_csv(seed_sequence_csv, index=False)
    summary.to_csv(summary_csv, index=False)
    manifest = {
        "run_type": "response_necessity_corpus",
        "episodes_csv": str(episodes_csv),
        "baseline_policy": baseline_policy,
        "ablation_policies": ablation_policies,
        "top_k": int(top_k),
        "repeat": int(repeat),
        "near_margin": float(near_margin),
        "margin_scale": float(margin_scale),
        "artifacts": {
            "feature_csv": str(feature_csv),
            "corpus_csv": str(corpus_csv),
            "seed_sequence_csv": str(seed_sequence_csv),
            "summary_csv": str(summary_csv),
        },
        "summary": {
            "features": int(len(features)),
            "selected_count": int(len(corpus)),
            "seed_sequence_count": int(len(seed_sequence)),
            "critical_count": int((features["critical_reason"].astype(str) != "").sum()),
            "score_max": float(features["response_necessity_score"].max()) if len(features) else 0.0,
        },
    }
    write_json(run_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine response-history necessity seeds from paired episodes.")
    parser.add_argument("--episodes-csv", type=Path, required=True)
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--ablation-policy", action="append", default=[])
    parser.add_argument("--top-k", type=int, default=80)
    parser.add_argument("--repeat", type=int, default=4)
    parser.add_argument("--near-margin", type=float, default=0.05)
    parser.add_argument("--margin-scale", type=float, default=0.25)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    if not args.ablation_policy:
        raise ValueError("at least one --ablation-policy is required")

    run_dir = args.run_dir or make_run_dir(prefix="response_necessity_corpus")
    manifest = write_response_necessity_corpus(
        run_dir,
        episodes_csv=args.episodes_csv,
        baseline_policy=args.baseline_policy,
        ablation_policies=args.ablation_policy,
        top_k=args.top_k,
        repeat=args.repeat,
        near_margin=args.near_margin,
        margin_scale=args.margin_scale,
    )
    print(pd.Series(manifest["summary"]).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
