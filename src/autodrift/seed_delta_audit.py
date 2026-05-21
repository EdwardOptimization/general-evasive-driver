"""Seed-level policy delta audit for shared-seed benchmark outputs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json


REQUIRED_COLUMNS = {"seed", "policy"}
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
CONTEXT_COLUMNS = [
    "obstacle_label",
    "mu",
    "initial_mu",
    "mass_scale",
    "inertia_scale",
    "cg_shift",
    "brake_scale",
    "drive_scale",
    "tire_stiffness_scale",
    "steer_tau_scale",
    "drive_tau_scale",
    "friction_step_at",
    "friction_step_applied",
    "obstacle_collision_radius",
    "mu_bucket",
    "initial_mu_bucket",
    "mass_bucket",
    "cg_bucket",
    "brake_bucket",
    "tire_bucket",
    "steering_tau_bucket",
]
DELTA_COLUMNS = [
    "return",
    "steps",
    "lateral_rmse",
    "lateral_peak",
    "beta_abs_error_mean",
    "beta_abs_peak",
    "high_sideslip_fraction",
    "speed_mean",
    "action_rate_mean",
    "min_obstacle_clearance",
    "min_clearance_margin",
]
OUTCOME_ORDER = {
    "regressed": 0,
    "improved": 1,
    "unchanged_failure": 2,
    "unchanged_success": 3,
}


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(bool)
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).astype(bool)
    normalized = series.astype(str).str.strip().str.lower()
    truthy = {"true", "1", "yes", "y"}
    falsy = {"false", "0", "no", "n"}
    unknown = sorted(set(normalized).difference(truthy | falsy))
    if unknown:
        raise ValueError(f"cannot parse boolean values: {unknown}")
    return normalized.isin(truthy)


def load_episodes(path: Path | str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"episodes CSV is missing columns: {missing}")
    if "success" not in frame.columns:
        if "terminated" not in frame.columns:
            raise ValueError("episodes CSV must contain either success or terminated")
        frame = frame.copy()
        frame["success"] = ~_bool_series(frame["terminated"])
    else:
        frame = frame.copy()
        frame["success"] = _bool_series(frame["success"])
    return frame


def _validate_unique_seed_policy(frame: pd.DataFrame) -> None:
    duplicated = frame.duplicated(["seed", "policy"], keep=False)
    if duplicated.any():
        sample = frame.loc[duplicated, ["seed", "policy"]].head(5).to_dict("records")
        raise ValueError(f"episodes CSV has duplicate seed/policy rows, sample={sample}")


def _pick(joined: pd.DataFrame, column: str) -> pd.Series:
    candidate_column = f"{column}_candidate"
    baseline_column = f"{column}_baseline"
    if candidate_column in joined:
        return joined[candidate_column]
    return joined[baseline_column]


def _classify_outcome(baseline_success: bool, candidate_success: bool) -> str:
    if baseline_success and not candidate_success:
        return "regressed"
    if not baseline_success and candidate_success:
        return "improved"
    if candidate_success:
        return "unchanged_success"
    return "unchanged_failure"


def build_policy_delta(frame: pd.DataFrame, baseline_policy: str, candidate_policy: str) -> pd.DataFrame:
    _validate_unique_seed_policy(frame)
    if baseline_policy == candidate_policy:
        raise ValueError("baseline and candidate policies must be different")
    available = set(frame["policy"].astype(str))
    missing = [policy for policy in [baseline_policy, candidate_policy] if policy not in available]
    if missing:
        raise ValueError(f"missing policies in episodes CSV: {missing}")

    baseline = frame[frame["policy"] == baseline_policy].drop(columns=["policy"]).set_index("seed")
    candidate = frame[frame["policy"] == candidate_policy].drop(columns=["policy"]).set_index("seed")
    joined = baseline.join(candidate, how="inner", lsuffix="_baseline", rsuffix="_candidate")
    if joined.empty:
        raise ValueError(f"no common seeds between {baseline_policy!r} and {candidate_policy!r}")

    rows: list[dict[str, Any]] = []
    for seed, row in joined.sort_index().iterrows():
        baseline_success = bool(row["success_baseline"])
        candidate_success = bool(row["success_candidate"])
        item: dict[str, Any] = {
            "seed": int(seed),
            "baseline_policy": baseline_policy,
            "candidate_policy": candidate_policy,
            "baseline_success": baseline_success,
            "candidate_success": candidate_success,
            "success_delta": int(candidate_success) - int(baseline_success),
            "outcome": _classify_outcome(baseline_success, candidate_success),
        }
        for column in CONTEXT_COLUMNS:
            if f"{column}_candidate" in joined or f"{column}_baseline" in joined:
                item[column] = _pick(joined, column).loc[seed]
        for column in DELTA_COLUMNS:
            baseline_column = f"{column}_baseline"
            candidate_column = f"{column}_candidate"
            if baseline_column in joined and candidate_column in joined:
                baseline_value = float(row[baseline_column])
                candidate_value = float(row[candidate_column])
                item[f"baseline_{column}"] = baseline_value
                item[f"candidate_{column}"] = candidate_value
                item[f"{column}_delta"] = candidate_value - baseline_value
        rows.append(item)

    output = pd.DataFrame(rows)
    output["_outcome_rank"] = output["outcome"].map(OUTCOME_ORDER).astype(int)
    if "return_delta" in output:
        output["_abs_return_delta"] = output["return_delta"].abs()
    else:
        output["_abs_return_delta"] = 0.0
    output = output.sort_values(
        ["candidate_policy", "_outcome_rank", "_abs_return_delta", "seed"],
        ascending=[True, True, False, True],
    )
    return output.drop(columns=["_outcome_rank", "_abs_return_delta"]).reset_index(drop=True)


def build_seed_delta_audit(
    frame: pd.DataFrame,
    *,
    baseline_policy: str,
    candidate_policies: list[str],
) -> pd.DataFrame:
    if not candidate_policies:
        raise ValueError("at least one candidate policy is required")
    return pd.concat(
        [build_policy_delta(frame, baseline_policy, candidate_policy) for candidate_policy in candidate_policies],
        ignore_index=True,
    )


def summarize_policy_deltas(deltas: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_policy, group in deltas.groupby("candidate_policy", observed=True):
        item: dict[str, Any] = {
            "baseline_policy": str(group["baseline_policy"].iloc[0]),
            "candidate_policy": candidate_policy,
            "pairs": int(len(group)),
            "baseline_success_rate": float(group["baseline_success"].mean()),
            "candidate_success_rate": float(group["candidate_success"].mean()),
            "success_delta_rate": float(group["success_delta"].mean()),
            "improved_seeds": int((group["outcome"] == "improved").sum()),
            "regressed_seeds": int((group["outcome"] == "regressed").sum()),
            "unchanged_success_seeds": int((group["outcome"] == "unchanged_success").sum()),
            "unchanged_failure_seeds": int((group["outcome"] == "unchanged_failure").sum()),
        }
        for column in DELTA_COLUMNS:
            delta_column = f"{column}_delta"
            if delta_column in group:
                item[f"{delta_column}_mean"] = float(group[delta_column].mean())
                item[f"{delta_column}_median"] = float(group[delta_column].median())
        rows.append(item)
    return pd.DataFrame(rows).sort_values("candidate_policy").reset_index(drop=True)


def summarize_group_deltas(deltas: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for column in group_columns:
        if column not in deltas:
            continue
        valid = deltas[~deltas[column].isna()].copy()
        if valid.empty:
            continue
        valid[column] = valid[column].astype(str)
        for (candidate_policy, group_value), group in valid.groupby(["candidate_policy", column], observed=True):
            item: dict[str, Any] = {
                "candidate_policy": candidate_policy,
                "group_column": column,
                "group_value": group_value,
                "pairs": int(len(group)),
                "baseline_success_rate": float(group["baseline_success"].mean()),
                "candidate_success_rate": float(group["candidate_success"].mean()),
                "success_delta_rate": float(group["success_delta"].mean()),
                "improved_seeds": int((group["outcome"] == "improved").sum()),
                "regressed_seeds": int((group["outcome"] == "regressed").sum()),
            }
            if "return_delta" in group:
                item["return_delta_mean"] = float(group["return_delta"].mean())
            if "lateral_rmse_delta" in group:
                item["lateral_rmse_delta_mean"] = float(group["lateral_rmse_delta"].mean())
            rows.append(item)
    if not rows:
        return pd.DataFrame(
            columns=[
                "candidate_policy",
                "group_column",
                "group_value",
                "pairs",
                "baseline_success_rate",
                "candidate_success_rate",
                "success_delta_rate",
                "improved_seeds",
                "regressed_seeds",
            ]
        )
    output = pd.DataFrame(rows)
    output["_abs_success_delta"] = output["success_delta_rate"].abs()
    output = output.sort_values(
        ["candidate_policy", "_abs_success_delta", "regressed_seeds", "improved_seeds", "group_column", "group_value"],
        ascending=[True, False, False, False, True, True],
    )
    return output.drop(columns=["_abs_success_delta"]).reset_index(drop=True)


def write_audit(
    run_dir: Path | str,
    *,
    episodes_csv: Path | str,
    baseline_policy: str,
    candidate_policies: list[str],
    group_columns: list[str],
) -> dict[str, Any]:
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    frame = load_episodes(episodes_csv)
    deltas = build_seed_delta_audit(
        frame,
        baseline_policy=baseline_policy,
        candidate_policies=candidate_policies,
    )
    policy_summary = summarize_policy_deltas(deltas)
    group_summary = summarize_group_deltas(deltas, group_columns)

    seed_delta_csv = output / "seed_deltas.csv"
    policy_summary_csv = output / "policy_delta_summary.csv"
    group_summary_csv = output / "group_delta_summary.csv"
    manifest_json = output / "manifest.json"
    deltas.to_csv(seed_delta_csv, index=False)
    policy_summary.to_csv(policy_summary_csv, index=False)
    group_summary.to_csv(group_summary_csv, index=False)
    manifest = {
        "run_type": "seed_delta_audit",
        "episodes_csv": Path(episodes_csv),
        "baseline_policy": baseline_policy,
        "candidate_policies": candidate_policies,
        "group_columns": group_columns,
        "artifacts": {
            "seed_delta_csv": seed_delta_csv,
            "policy_summary_csv": policy_summary_csv,
            "group_summary_csv": group_summary_csv,
        },
        "policy_summary": policy_summary.to_dict("records"),
    }
    write_json(manifest_json, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit seed-level policy deltas from benchmark episodes.csv.")
    parser.add_argument("--episodes-csv", type=Path, required=True)
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--candidate-policy", action="append", required=True)
    parser.add_argument("--group-column", action="append", default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="seed_delta_audit")
    group_columns = args.group_column or DEFAULT_GROUP_COLUMNS
    manifest = write_audit(
        run_dir,
        episodes_csv=args.episodes_csv,
        baseline_policy=args.baseline_policy,
        candidate_policies=args.candidate_policy,
        group_columns=group_columns,
    )
    print(pd.DataFrame(manifest["policy_summary"]).to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
