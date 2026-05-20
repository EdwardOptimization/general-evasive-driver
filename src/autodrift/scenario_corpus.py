"""Build deterministic scenario seed corpora for AutoDrift benchmarks."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.benchmark import add_buckets
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config


DEFAULT_LABELS = ("aes_feasible", "drift_required", "unavoidable")


def collect_candidate_rows(env_config: DriftEnvConfig, seed_start: int, max_candidates: int) -> list[dict]:
    env = AutoDriftEnv(env_config)
    rows = []
    for offset in range(max_candidates):
        seed = seed_start + offset
        _, info = env.reset(seed=seed)
        rows.append(
            {
                "seed": seed,
                "terminated": False,
                "obstacle_label": str(info.get("obstacle_label", "")),
                "mu": float(info["mu"]),
                "mass_scale": float(info.get("mass_scale", float("nan"))),
                "inertia_scale": float(info.get("inertia_scale", float("nan"))),
                "cg_shift": float(info.get("cg_shift", float("nan"))),
                "brake_scale": float(info.get("brake_scale", float("nan"))),
                "drive_scale": float(info.get("drive_scale", float("nan"))),
                "tire_stiffness_scale": float(info.get("tire_stiffness_scale", float("nan"))),
                "steer_tau_scale": float(info.get("steer_tau_scale", float("nan"))),
                "drive_tau_scale": float(info.get("drive_tau_scale", float("nan"))),
                "obstacle_distance": float(info.get("obstacle_distance", float("nan"))),
                "obstacle_required_lateral_offset": float(
                    info.get("obstacle_required_lateral_offset", float("nan"))
                ),
                "speed_ref": float(info.get("speed_ref", float("nan"))),
                "beta_target": float(info.get("beta_target", float("nan"))),
            }
        )
    return rows


def select_label_balanced_rows(rows: list[dict], per_label: int, labels: tuple[str, ...]) -> list[dict]:
    counts = {label: 0 for label in labels}
    selected = []
    for row in rows:
        label = str(row.get("obstacle_label", ""))
        if label not in counts or counts[label] >= per_label:
            continue
        selected.append(row)
        counts[label] += 1
        if all(count >= per_label for count in counts.values()):
            break
    return selected


def label_counts(rows: list[dict]) -> dict[str, int]:
    return dict(Counter(str(row.get("obstacle_label", "")) for row in rows))


def write_corpus(run_dir: Path, selected_rows: list[dict], candidates: int, labels: tuple[str, ...]) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = add_buckets(pd.DataFrame(selected_rows))
    corpus_csv = run_dir / "scenario_corpus.csv"
    label_summary_csv = run_dir / "label_summary.csv"
    vehicle_road_summary_csv = run_dir / "vehicle_road_summary.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"

    frame.to_csv(corpus_csv, index=False)
    label_summary = frame.groupby("obstacle_label", observed=True).agg(episodes=("seed", "count")).reset_index()
    label_summary.to_csv(label_summary_csv, index=False)
    vehicle_columns = [
        column
        for column in ["obstacle_label", "mu_bucket", "mass_bucket", "brake_bucket", "steering_tau_bucket"]
        if column in frame
    ]
    if len(vehicle_columns) > 1:
        vehicle_summary = frame.groupby(vehicle_columns, observed=True).agg(episodes=("seed", "count")).reset_index()
        vehicle_summary.to_csv(vehicle_road_summary_csv, index=False)

    counts = label_counts(selected_rows)
    summary = {
        "selected": int(len(selected_rows)),
        "candidates": int(candidates),
        "labels": list(labels),
        "label_counts": counts,
        "complete": all(counts.get(label, 0) > 0 for label in labels),
    }
    write_json(summary_json, summary)
    write_json(
        manifest_json,
        {
            "run_type": "scenario_corpus",
            "summary": summary,
            "artifacts": {
                "scenario_corpus_csv": corpus_csv,
                "label_summary_csv": label_summary_csv,
                "vehicle_road_summary_csv": vehicle_road_summary_csv,
                "summary_json": summary_json,
            },
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic AutoDrift scenario corpus.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=1300)
    parser.add_argument("--max-candidates", type=int, default=2000)
    parser.add_argument("--per-label", type=int, default=20)
    parser.add_argument("--label", action="append", default=None, help="Obstacle label to include. Repeat as needed.")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    labels = tuple(args.label or DEFAULT_LABELS)
    env_config = load_env_config(args.env_config)
    candidate_rows = collect_candidate_rows(env_config, seed_start=args.seed_start, max_candidates=args.max_candidates)
    selected_rows = select_label_balanced_rows(candidate_rows, per_label=args.per_label, labels=labels)
    counts = label_counts(selected_rows)
    missing = [label for label in labels if counts.get(label, 0) < args.per_label]
    if missing:
        raise RuntimeError(
            "failed to build a complete label-balanced corpus: "
            f"missing quotas for {missing}, counts={counts}, candidates={args.max_candidates}"
        )

    run_dir = args.run_dir or make_run_dir(prefix="scenario_corpus", seed=args.seed_start)
    summary = write_corpus(run_dir, selected_rows, candidates=len(candidate_rows), labels=labels)
    print(pd.DataFrame([summary]).to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
