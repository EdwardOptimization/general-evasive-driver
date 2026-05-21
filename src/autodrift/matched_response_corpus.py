"""Mine matched response-critical seeds from hidden-swap gate artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json


DEFAULT_ABLATION_VARIANTS = ("reset", "zero_response", "hidden_swap")


def build_variant_edges(
    replays: pd.DataFrame,
    *,
    normal_variant: str = "normal",
    ablation_variants: tuple[str, ...] = DEFAULT_ABLATION_VARIANTS,
) -> pd.DataFrame:
    required = {"seed", "source_condition", "variant", "success", "return", "first_action_distance"}
    missing = required.difference(replays.columns)
    if missing:
        raise ValueError(f"replays CSV is missing columns: {sorted(missing)}")

    normals = replays[replays["variant"] == normal_variant][
        ["seed", "source_condition", "success", "return"]
    ].rename(columns={"success": "normal_success", "return": "normal_return"})
    ablations = replays[replays["variant"].isin(ablation_variants)][
        ["seed", "source_condition", "variant", "success", "return", "first_action_distance"]
    ].rename(columns={"success": "ablation_success", "return": "ablation_return"})
    edges = ablations.merge(normals, on=["seed", "source_condition"], how="inner")
    edges["success_changed"] = edges["ablation_success"].astype(bool) != edges["normal_success"].astype(bool)
    edges["return_delta"] = edges["ablation_return"].astype(float) - edges["normal_return"].astype(float)
    edges["abs_return_delta"] = edges["return_delta"].abs()
    return edges


def build_seed_candidates(pairs: pd.DataFrame, replays: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    required_pairs = {
        "seed",
        "accepted_match",
        "observation_distance",
        "context_observation_distance",
        "hidden_state_distance",
    }
    missing_pairs = required_pairs.difference(pairs.columns)
    if missing_pairs:
        raise ValueError(f"pairs CSV is missing columns: {sorted(missing_pairs)}")

    normal_success = (
        replays[replays["variant"] == "normal"]
        .pivot_table(index="seed", columns="source_condition", values="success", aggfunc="first")
        .reset_index()
    )
    for column in ["nominal", "perturbed"]:
        if column not in normal_success:
            normal_success[column] = np.nan
    normal_success = normal_success.rename(
        columns={
            "nominal": "nominal_normal_success",
            "perturbed": "perturbed_normal_success",
        }
    )
    edge_summary = edges.groupby("seed", observed=True).agg(
        success_changed_variants=("success_changed", "sum"),
        max_abs_return_delta=("abs_return_delta", "max"),
        mean_abs_return_delta=("abs_return_delta", "mean"),
        max_first_action_distance=("first_action_distance", "max"),
    )
    candidates = pairs.merge(normal_success, on="seed", how="left").merge(edge_summary, on="seed", how="left")
    for column in [
        "success_changed_variants",
        "max_abs_return_delta",
        "mean_abs_return_delta",
        "max_first_action_distance",
    ]:
        candidates[column] = candidates[column].fillna(0.0)
    candidates["normal_condition_change"] = (
        candidates["nominal_normal_success"].astype(bool) != candidates["perturbed_normal_success"].astype(bool)
    )
    candidates["perturbed_failed"] = ~candidates["perturbed_normal_success"].astype(bool)
    candidates["response_critical_score"] = (
        10.0 * candidates["success_changed_variants"].astype(float)
        + 4.0 * candidates["normal_condition_change"].astype(float)
        + 3.0 * candidates["perturbed_failed"].astype(float)
        + candidates["hidden_state_distance"].astype(float)
        - candidates["context_observation_distance"].astype(float)
        + candidates["max_first_action_distance"].astype(float)
        + 0.25 * candidates["max_abs_return_delta"].astype(float)
    )
    return candidates.sort_values(
        [
            "success_changed_variants",
            "normal_condition_change",
            "perturbed_failed",
            "response_critical_score",
        ],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


def select_seed_corpus(
    candidates: pd.DataFrame,
    *,
    top_k: int,
    require_accepted: bool = True,
    min_hidden_state_distance: float = 0.0,
    max_context_observation_distance: float | None = None,
) -> pd.DataFrame:
    selected = candidates.copy()
    if require_accepted:
        selected = selected[selected["accepted_match"].astype(bool)]
    selected = selected[selected["hidden_state_distance"].astype(float) >= min_hidden_state_distance]
    if max_context_observation_distance is not None:
        selected = selected[
            selected["context_observation_distance"].astype(float) <= max_context_observation_distance
        ]
    return selected.head(max(0, int(top_k))).reset_index(drop=True)


def build_summary(candidates: pd.DataFrame, corpus: pd.DataFrame, edges: pd.DataFrame) -> dict[str, Any]:
    accepted = candidates[candidates["accepted_match"].astype(bool)]
    return {
        "candidate_count": int(len(candidates)),
        "accepted_count": int(len(accepted)),
        "selected_count": int(len(corpus)),
        "success_changed_seed_count": int((candidates["success_changed_variants"] > 0).sum()),
        "condition_changed_seed_count": int(candidates["normal_condition_change"].sum()),
        "perturbed_failed_seed_count": int(candidates["perturbed_failed"].sum()),
        "edge_success_changed_count": int(edges["success_changed"].sum()) if not edges.empty else 0,
        "accepted_hidden_state_distance_mean": (
            float(accepted["hidden_state_distance"].mean()) if not accepted.empty else float("nan")
        ),
        "accepted_observation_distance_mean": (
            float(accepted["observation_distance"].mean()) if not accepted.empty else float("nan")
        ),
        "selected_score_mean": float(corpus["response_critical_score"].mean()) if not corpus.empty else float("nan"),
    }


def write_matched_response_corpus(
    run_dir: Path,
    candidates: pd.DataFrame,
    corpus: pd.DataFrame,
    edges: pd.DataFrame,
    summary: dict[str, Any],
) -> dict[str, Path]:
    run_dir.mkdir(parents=True, exist_ok=True)
    candidate_csv = run_dir / "candidate_pairs.csv"
    corpus_csv = run_dir / "scenario_corpus.csv"
    edges_csv = run_dir / "variant_edges.csv"
    summary_json = run_dir / "summary.json"
    candidates.to_csv(candidate_csv, index=False)
    corpus.to_csv(corpus_csv, index=False)
    edges.to_csv(edges_csv, index=False)
    write_json(summary_json, summary)
    return {
        "candidate_csv": candidate_csv,
        "corpus_csv": corpus_csv,
        "edges_csv": edges_csv,
        "summary_json": summary_json,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine a matched response-critical seed corpus.")
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--replays-csv", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--allow-unaccepted", action="store_true")
    parser.add_argument("--min-hidden-state-distance", type=float, default=0.0)
    parser.add_argument("--max-context-observation-distance", type=float, default=None)
    parser.add_argument("--normal-variant", default="normal")
    parser.add_argument("--ablation-variant", action="append", default=list(DEFAULT_ABLATION_VARIANTS))
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="matched_response_corpus")
    pairs = pd.read_csv(args.pairs_csv)
    replays = pd.read_csv(args.replays_csv)
    ablation_variants = tuple(dict.fromkeys(args.ablation_variant))
    edges = build_variant_edges(
        replays,
        normal_variant=args.normal_variant,
        ablation_variants=ablation_variants,
    )
    candidates = build_seed_candidates(pairs, replays, edges)
    corpus = select_seed_corpus(
        candidates,
        top_k=args.top_k,
        require_accepted=not args.allow_unaccepted,
        min_hidden_state_distance=args.min_hidden_state_distance,
        max_context_observation_distance=args.max_context_observation_distance,
    )
    summary = build_summary(candidates, corpus, edges)
    artifacts = write_matched_response_corpus(run_dir, candidates, corpus, edges, summary)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "matched_response_corpus",
            "pairs_csv": args.pairs_csv,
            "replays_csv": args.replays_csv,
            "top_k": args.top_k,
            "require_accepted": not args.allow_unaccepted,
            "min_hidden_state_distance": args.min_hidden_state_distance,
            "max_context_observation_distance": args.max_context_observation_distance,
            "normal_variant": args.normal_variant,
            "ablation_variants": ablation_variants,
            "artifacts": artifacts,
            "summary": summary,
        },
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
