"""Build deduplicated training seed sequences from diagnostic corpora."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json


REQUIRED_COLUMNS = {"seed"}


def load_corpus(path: Path | str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"corpus CSV is missing columns: {missing}")
    return frame.copy()


def _join_unique(series: pd.Series) -> str:
    values = [str(value) for value in series.dropna().unique().tolist()]
    return ";".join(sorted(values))


def build_seed_sequence(frame: pd.DataFrame, *, top_k: int | None = None) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("corpus is empty")
    work = frame.copy()
    if "margin_critical_score" not in work:
        work["margin_critical_score"] = 0.0
    if "source" not in work:
        work["source"] = "unknown"
    if "candidate_policy" not in work:
        work["candidate_policy"] = ""
    if "critical_reason" not in work:
        work["critical_reason"] = ""
    grouped = work.groupby("seed", observed=True)
    rows: list[dict[str, Any]] = []
    for seed, group in grouped:
        rows.append(
            {
                "seed": int(seed),
                "row_count": int(len(group)),
                "source_count": int(group["source"].nunique(dropna=True)),
                "sources": _join_unique(group["source"]),
                "candidate_policies": _join_unique(group["candidate_policy"]),
                "critical_reasons": _join_unique(group["critical_reason"]),
                "max_margin_critical_score": float(group["margin_critical_score"].astype(float).max()),
                "mean_margin_critical_score": float(group["margin_critical_score"].astype(float).mean()),
            }
        )
    output = pd.DataFrame(rows).sort_values(
        ["max_margin_critical_score", "row_count", "seed"],
        ascending=[False, False, True],
    )
    if top_k is not None:
        output = output.head(max(0, int(top_k)))
    return output.reset_index(drop=True)


def summarize_sources(seed_sequence: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in seed_sequence.iterrows():
        for source in str(row["sources"]).split(";"):
            if not source:
                continue
            rows.append({"source": source, "seed": int(row["seed"])})
    if not rows:
        return pd.DataFrame(columns=["source", "seeds"])
    return (
        pd.DataFrame(rows)
        .groupby("source", observed=True)
        .agg(seeds=("seed", "nunique"))
        .reset_index()
        .sort_values(["seeds", "source"], ascending=[False, True])
        .reset_index(drop=True)
    )


def write_training_seed_corpus(
    run_dir: Path,
    *,
    corpus_csv: Path | str,
    top_k: int | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = load_corpus(corpus_csv)
    seed_sequence = build_seed_sequence(frame, top_k=top_k)
    source_summary = summarize_sources(seed_sequence)
    seed_csv = run_dir / "seed_sequence.csv"
    source_summary_csv = run_dir / "source_summary.csv"
    seed_sequence.to_csv(seed_csv, index=False)
    source_summary.to_csv(source_summary_csv, index=False)
    manifest = {
        "run_type": "training_seed_corpus",
        "corpus_csv": str(corpus_csv),
        "top_k": top_k,
        "artifacts": {
            "seed_sequence_csv": str(seed_csv),
            "source_summary_csv": str(source_summary_csv),
        },
        "summary": {
            "input_rows": int(len(frame)),
            "unique_seeds": int(len(seed_sequence)),
            "source_count": int(source_summary["source"].nunique()) if not source_summary.empty else 0,
        },
    }
    write_json(run_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deduplicated training seed sequence.")
    parser.add_argument("--corpus-csv", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="training_seed_corpus")
    manifest = write_training_seed_corpus(run_dir, corpus_csv=args.corpus_csv, top_k=args.top_k)
    print(pd.Series(manifest["summary"]).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
