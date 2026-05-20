"""Build near-threshold obstacle seed corpora for paired perturbation gates."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.benchmark import add_buckets
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import load_env_config


def collect_candidate_rows(env_config, seed_start: int, max_candidates: int) -> list[dict]:
    env = AutoDriftEnv(env_config)
    rows: list[dict] = []
    for offset in range(max_candidates):
        seed = seed_start + offset
        _, info = env.reset(seed=seed)
        scenario = env.obstacle_scenario
        if scenario is None:
            continue
        required = max(float(scenario.required_lateral_offset), 1e-6)
        aes_margin = float(scenario.conventional_lateral_capacity - scenario.required_lateral_offset)
        drift_margin = float(scenario.drift_lateral_capacity - scenario.required_lateral_offset)
        step_time = float(env.friction_step_at * env_config.dt) if env.friction_step_at is not None else float("inf")
        time_after_step = float(scenario.time_to_obstacle - step_time)
        rows.append(
            {
                "seed": seed,
                "terminated": False,
                "obstacle_label": str(scenario.label),
                "threshold_score": min(abs(aes_margin / required), abs(drift_margin / required)),
                "aes_margin": aes_margin,
                "drift_margin": drift_margin,
                "aes_margin_ratio": aes_margin / required,
                "drift_margin_ratio": drift_margin / required,
                "time_to_obstacle": float(scenario.time_to_obstacle),
                "friction_step_at": int(env.friction_step_at) if env.friction_step_at is not None else -1,
                "friction_step_time": step_time,
                "time_after_step": time_after_step,
                "mu": float(info["mu"]),
                "mass_scale": float(info.get("mass_scale", float("nan"))),
                "brake_scale": float(info.get("brake_scale", float("nan"))),
                "tire_stiffness_scale": float(info.get("tire_stiffness_scale", float("nan"))),
                "steer_tau_scale": float(info.get("steer_tau_scale", float("nan"))),
                "obstacle_distance": float(info.get("obstacle_distance", float("nan"))),
                "obstacle_required_lateral_offset": float(
                    info.get("obstacle_required_lateral_offset", float("nan"))
                ),
                "speed_ref": float(info.get("speed_ref", float("nan"))),
            }
        )
    return rows


def select_near_threshold_rows(
    rows: list[dict],
    count: int,
    labels: tuple[str, ...],
    max_threshold_score: float,
    min_time_after_step: float,
) -> list[dict]:
    selected = [
        row
        for row in rows
        if row["obstacle_label"] in labels
        and row["threshold_score"] <= max_threshold_score
        and row["time_after_step"] >= min_time_after_step
    ]
    selected = sorted(selected, key=lambda row: (row["threshold_score"], row["seed"]))
    return selected[:count]


def write_corpus(run_dir: Path, selected_rows: list[dict], candidates: int, labels: tuple[str, ...]) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = add_buckets(pd.DataFrame(selected_rows))
    corpus_csv = run_dir / "scenario_corpus.csv"
    label_summary_csv = run_dir / "label_summary.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    frame.to_csv(corpus_csv, index=False)
    label_summary = (
        frame.groupby("obstacle_label", observed=True).agg(episodes=("seed", "count")).reset_index()
        if len(frame)
        else pd.DataFrame(columns=["obstacle_label", "episodes"])
    )
    label_summary.to_csv(label_summary_csv, index=False)
    summary = {
        "selected": int(len(selected_rows)),
        "candidates": int(candidates),
        "labels": list(labels),
        "label_counts": {
            label: int((frame["obstacle_label"] == label).sum()) if len(frame) else 0 for label in labels
        },
        "threshold_score_max": float(frame["threshold_score"].max()) if len(frame) else float("nan"),
        "threshold_score_mean": float(frame["threshold_score"].mean()) if len(frame) else float("nan"),
        "complete": len(selected_rows) > 0,
    }
    write_json(summary_json, summary)
    write_json(
        manifest_json,
        {
            "run_type": "near_threshold_corpus",
            "summary": summary,
            "artifacts": {
                "scenario_corpus_csv": corpus_csv,
                "label_summary_csv": label_summary_csv,
                "summary_json": summary_json,
            },
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a near-threshold AutoDrift seed corpus.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=3000)
    parser.add_argument("--max-candidates", type=int, default=5000)
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--label", action="append", default=None)
    parser.add_argument("--max-threshold-score", type=float, default=0.20)
    parser.add_argument("--min-time-after-step", type=float, default=0.10)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    labels = tuple(args.label or ("aes_feasible", "drift_required", "unavoidable"))
    env_config = load_env_config(args.env_config)
    candidate_rows = collect_candidate_rows(env_config, args.seed_start, args.max_candidates)
    selected_rows = select_near_threshold_rows(
        candidate_rows,
        count=args.count,
        labels=labels,
        max_threshold_score=args.max_threshold_score,
        min_time_after_step=args.min_time_after_step,
    )
    if not selected_rows:
        raise RuntimeError("failed to select any near-threshold candidate rows")
    run_dir = args.run_dir or make_run_dir(prefix="near_threshold_corpus", seed=args.seed_start)
    summary = write_corpus(run_dir, selected_rows, candidates=len(candidate_rows), labels=labels)
    print(pd.DataFrame([summary]).to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
