"""Mine hard response-dependence seed corpora from paired gate episodes."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json


REQUIRED_COLUMNS = {"seed", "policy", "condition", "success", "return"}
DEFAULT_METADATA_COLUMNS = (
    "obstacle_label",
    "mu",
    "initial_mu",
    "mass_scale",
    "cg_shift",
    "brake_scale",
    "drive_scale",
    "tire_stiffness_scale",
    "steer_tau_scale",
    "drive_tau_scale",
    "friction_step_at",
    "obstacle_distance",
    "min_obstacle_clearance",
)


def load_episode_frames(paths: list[Path]) -> pd.DataFrame:
    if not paths:
        raise ValueError("at least one episodes CSV is required")
    frames = []
    for path in paths:
        frame = pd.read_csv(path)
        missing = REQUIRED_COLUMNS.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
        frame = frame.copy()
        frame["source_csv"] = str(path)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _bool_success(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _condition_values(rows: pd.DataFrame, policy: str, seed: int) -> dict[str, dict[str, Any]]:
    subset = rows[(rows["policy"] == policy) & (rows["seed"] == seed)]
    values: dict[str, dict[str, Any]] = {}
    for condition, condition_rows in subset.groupby("condition", observed=True):
        first = condition_rows.iloc[0]
        values[str(condition)] = {
            "success": _bool_success(first["success"]),
            "return": float(first["return"]),
        }
    return values


def _metadata_row(rows: pd.DataFrame, seed: int, normal_policy: str) -> dict[str, Any]:
    normal_nominal = rows[
        (rows["seed"] == seed) & (rows["policy"] == normal_policy) & (rows["condition"] == "nominal")
    ]
    if normal_nominal.empty:
        normal_nominal = rows[(rows["seed"] == seed) & (rows["policy"] == normal_policy)]
    if normal_nominal.empty:
        normal_nominal = rows[rows["seed"] == seed]
    first = normal_nominal.iloc[0]
    metadata: dict[str, Any] = {"source_csv": str(first.get("source_csv", ""))}
    for column in DEFAULT_METADATA_COLUMNS:
        if column in rows.columns:
            metadata[column] = first.get(column)
    return metadata


def mine_hard_response_corpus(
    episodes: pd.DataFrame,
    normal_policy: str,
    ablation_policies: list[str],
    *,
    include_hidden_condition_changes: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not ablation_policies:
        raise ValueError("at least one ablation policy is required")
    missing = REQUIRED_COLUMNS.difference(episodes.columns)
    if missing:
        raise ValueError(f"episodes frame is missing columns: {sorted(missing)}")

    rows = episodes.copy()
    rows["success"] = rows["success"].map(_bool_success)
    seeds = sorted(int(seed) for seed in rows.loc[rows["policy"] == normal_policy, "seed"].unique())
    selected_rows: list[dict[str, Any]] = []
    hard_pair_rows: list[dict[str, Any]] = []
    for seed in seeds:
        normal = _condition_values(rows, normal_policy, seed)
        if not normal:
            continue
        normal_success_any = any(condition["success"] for condition in normal.values())
        normal_condition_change = len({condition["success"] for condition in normal.values()}) > 1
        changed_edges = 0
        max_return_loss = 0.0
        changed_policies: set[str] = set()
        changed_conditions: set[str] = set()
        seed_pair_rows: list[dict[str, Any]] = []
        for ablation_policy in ablation_policies:
            ablated = _condition_values(rows, ablation_policy, seed)
            for condition, normal_values in normal.items():
                if condition not in ablated:
                    continue
                ablated_values = ablated[condition]
                success_changed = normal_values["success"] != ablated_values["success"]
                return_loss = normal_values["return"] - ablated_values["return"]
                if success_changed:
                    changed_edges += 1
                    changed_policies.add(ablation_policy)
                    changed_conditions.add(condition)
                max_return_loss = max(max_return_loss, float(return_loss))
                seed_pair_rows.append(
                    {
                        "seed": seed,
                        "condition": condition,
                        "normal_policy": normal_policy,
                        "ablation_policy": ablation_policy,
                        "normal_success": normal_values["success"],
                        "ablation_success": ablated_values["success"],
                        "success_changed": success_changed,
                        "normal_return": normal_values["return"],
                        "ablation_return": ablated_values["return"],
                        "return_loss": float(return_loss),
                    }
                )
        is_hard = normal_success_any and changed_edges > 0
        if include_hidden_condition_changes:
            is_hard = is_hard or (normal_success_any and normal_condition_change)
        if not is_hard:
            continue
        hard_pair_rows.extend(seed_pair_rows)
        seed_row = {
            "seed": seed,
            "normal_policy": normal_policy,
            "normal_success_any": normal_success_any,
            "normal_condition_change": normal_condition_change,
            "changed_edges": changed_edges,
            "changed_policies": ",".join(sorted(changed_policies)),
            "changed_conditions": ",".join(sorted(changed_conditions)),
            "max_return_loss": max_return_loss,
        }
        seed_row.update(_metadata_row(rows, seed, normal_policy))
        selected_rows.append(seed_row)

    corpus = pd.DataFrame(selected_rows)
    hard_pairs = pd.DataFrame(hard_pair_rows)
    if not corpus.empty:
        corpus = corpus.sort_values(
            ["changed_edges", "normal_condition_change", "max_return_loss", "seed"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
    if not hard_pairs.empty:
        hard_pairs = hard_pairs.sort_values(["seed", "condition", "ablation_policy"]).reset_index(drop=True)
    return corpus, hard_pairs


def write_hard_response_run(
    run_dir: Path,
    corpus: pd.DataFrame,
    hard_pairs: pd.DataFrame,
    *,
    episodes_csvs: list[Path],
    normal_policy: str,
    ablation_policies: list[str],
    include_hidden_condition_changes: bool,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_corpus_csv = run_dir / "scenario_corpus.csv"
    hard_pairs_csv = run_dir / "hard_pairs.csv"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"
    corpus.to_csv(scenario_corpus_csv, index=False)
    hard_pairs.to_csv(hard_pairs_csv, index=False)
    summary = {
        "selected": int(len(corpus)),
        "normal_policy": normal_policy,
        "ablation_policies": ablation_policies,
        "include_hidden_condition_changes": include_hidden_condition_changes,
        "success_changed_rows": (
            int(hard_pairs["success_changed"].sum()) if "success_changed" in hard_pairs.columns else 0
        ),
        "scenario_corpus_csv": str(scenario_corpus_csv),
        "hard_pairs_csv": str(hard_pairs_csv),
    }
    write_json(summary_json, summary)
    write_json(
        manifest_json,
        {
            "run_type": "hard_response_corpus",
            "episodes_csvs": episodes_csvs,
            "normal_policy": normal_policy,
            "ablation_policies": ablation_policies,
            "include_hidden_condition_changes": include_hidden_condition_changes,
            "artifacts": {
                "scenario_corpus_csv": scenario_corpus_csv,
                "hard_pairs_csv": hard_pairs_csv,
                "summary_json": summary_json,
            },
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine a hard response-dependence corpus from paired gate outputs.")
    parser.add_argument("--episodes-csv", type=Path, action="append", required=True)
    parser.add_argument("--normal-policy", required=True)
    parser.add_argument("--ablation-policy", action="append", required=True)
    parser.add_argument("--include-hidden-condition-changes", action="store_true")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    episodes = load_episode_frames(args.episodes_csv)
    corpus, hard_pairs = mine_hard_response_corpus(
        episodes,
        normal_policy=args.normal_policy,
        ablation_policies=args.ablation_policy,
        include_hidden_condition_changes=args.include_hidden_condition_changes,
    )
    run_dir = args.run_dir or make_run_dir(prefix="hard_response_corpus")
    summary = write_hard_response_run(
        run_dir,
        corpus,
        hard_pairs,
        episodes_csvs=args.episodes_csv,
        normal_policy=args.normal_policy,
        ablation_policies=args.ablation_policy,
        include_hidden_condition_changes=args.include_hidden_condition_changes,
    )
    print(pd.DataFrame([summary]).to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
