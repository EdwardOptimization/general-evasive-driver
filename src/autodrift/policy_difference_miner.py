"""Mine fresh scenario rows where checkpoint policies diverge."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import math

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json


DIVERGENCE_TYPES = (
    "success_flip",
    "collision_flip",
    "margin_sign_flip",
    "near_boundary_margin_delta",
    "large_margin_delta",
    "return_delta",
)

OUTPUT_COLUMNS = [
    "seed",
    "candidate_policy",
    "divergence_types",
    "score",
    "base_success",
    "candidate_success",
    "base_collision",
    "candidate_collision",
    "base_margin",
    "candidate_margin",
    "delta_margin",
    "base_return",
    "candidate_return",
    "delta_return",
    "obstacle_label",
    "mu",
    "mu_bucket",
    "initial_mu",
    "initial_mu_bucket",
    "mass_scale",
    "brake_scale",
    "steer_tau_scale",
    "source_run",
]


@dataclass(frozen=True)
class PolicyDifferenceConfig:
    baseline_policy: str
    candidate_policies: tuple[str, ...] | None = None
    margin_delta_threshold: float = 0.01
    large_margin_delta_threshold: float = 0.05
    near_boundary_abs: float = 0.25
    return_delta_threshold: float = 1.0
    max_rows: int = 64
    max_rows_per_seed: int = 1
    max_rows_per_policy: int = 20
    max_rows_per_obstacle_label: int = 24
    max_rows_per_mu_bucket: int = 24
    source_run: str = ""


def _bucket(frame: pd.DataFrame, column: str, target: str, bins: list[float], labels: list[str]) -> None:
    if column in frame and target not in frame:
        frame[target] = pd.cut(frame[column], bins=bins, labels=labels, include_lowest=True)


def prepare_episode_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if "success" not in output:
        if "terminated" not in output:
            raise ValueError("episodes CSV must contain either 'success' or 'terminated'")
        output["success"] = ~output["terminated"].astype(bool)
    if "collision" not in output:
        output["collision"] = False
    _bucket(output, "mu", "mu_bucket", [0.0, 0.45, 0.80, float("inf")], ["low", "medium", "high"])
    if "initial_mu" in output:
        _bucket(
            output,
            "initial_mu",
            "initial_mu_bucket",
            [0.0, 0.45, 0.80, float("inf")],
            ["low", "medium", "high"],
        )
    return output


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    if pd.isna(value):
        return False
    return bool(value)


def _float_value(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result


def _finite_delta(left: float, right: float) -> float:
    if not (math.isfinite(left) and math.isfinite(right)):
        return float("nan")
    return left - right


def _label(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def _metadata(row: pd.Series, key: str, default: Any = "") -> Any:
    return row[key] if key in row else default


def _divergence_types_and_score(base: pd.Series, candidate: pd.Series, config: PolicyDifferenceConfig) -> tuple[list[str], float]:
    base_success = _bool_value(base["success"])
    candidate_success = _bool_value(candidate["success"])
    base_collision = _bool_value(base.get("collision", False))
    candidate_collision = _bool_value(candidate.get("collision", False))
    base_margin = _float_value(base.get("min_clearance_margin", float("nan")))
    candidate_margin = _float_value(candidate.get("min_clearance_margin", float("nan")))
    base_return = _float_value(base.get("return", float("nan")))
    candidate_return = _float_value(candidate.get("return", float("nan")))
    delta_margin = _finite_delta(candidate_margin, base_margin)
    delta_return = _finite_delta(candidate_return, base_return)

    divergence_types: list[str] = []
    if base_success != candidate_success:
        divergence_types.append("success_flip")
    if base_collision != candidate_collision:
        divergence_types.append("collision_flip")
    if math.isfinite(base_margin) and math.isfinite(candidate_margin):
        if (base_margin >= 0.0) != (candidate_margin >= 0.0):
            divergence_types.append("margin_sign_flip")
        near_boundary = min(abs(base_margin), abs(candidate_margin)) <= config.near_boundary_abs
        if near_boundary and abs(delta_margin) >= config.margin_delta_threshold:
            divergence_types.append("near_boundary_margin_delta")
        if abs(delta_margin) >= config.large_margin_delta_threshold:
            divergence_types.append("large_margin_delta")
    else:
        near_boundary = False
    if math.isfinite(delta_return) and abs(delta_return) >= config.return_delta_threshold:
        divergence_types.append("return_delta")

    score = 0.0
    score += 100.0 if "success_flip" in divergence_types else 0.0
    score += 80.0 if "collision_flip" in divergence_types else 0.0
    score += 60.0 if "margin_sign_flip" in divergence_types else 0.0
    if math.isfinite(delta_margin):
        score += 20.0 * min(abs(delta_margin) / max(config.large_margin_delta_threshold, 1e-12), 5.0)
    if math.isfinite(delta_return):
        score += 5.0 * min(abs(delta_return) / 5.0, 5.0)
    score += 2.0 if near_boundary else 0.0
    return divergence_types, float(score)


def _candidate_row(base: pd.Series, candidate: pd.Series, config: PolicyDifferenceConfig) -> dict[str, Any] | None:
    divergence_types, score = _divergence_types_and_score(base, candidate, config)
    if not divergence_types:
        return None
    base_margin = _float_value(base.get("min_clearance_margin", float("nan")))
    candidate_margin = _float_value(candidate.get("min_clearance_margin", float("nan")))
    base_return = _float_value(base.get("return", float("nan")))
    candidate_return = _float_value(candidate.get("return", float("nan")))
    return {
        "seed": int(candidate["seed"]),
        "candidate_policy": str(candidate["policy"]),
        "divergence_types": ";".join(divergence_types),
        "score": score,
        "base_success": _bool_value(base["success"]),
        "candidate_success": _bool_value(candidate["success"]),
        "base_collision": _bool_value(base.get("collision", False)),
        "candidate_collision": _bool_value(candidate.get("collision", False)),
        "base_margin": base_margin,
        "candidate_margin": candidate_margin,
        "delta_margin": _finite_delta(candidate_margin, base_margin),
        "base_return": base_return,
        "candidate_return": candidate_return,
        "delta_return": _finite_delta(candidate_return, base_return),
        "obstacle_label": _label(_metadata(base, "obstacle_label", "")),
        "mu": _float_value(_metadata(base, "mu", float("nan"))),
        "mu_bucket": _label(_metadata(base, "mu_bucket", "")),
        "initial_mu": _float_value(_metadata(base, "initial_mu", float("nan"))),
        "initial_mu_bucket": _label(_metadata(base, "initial_mu_bucket", "")),
        "mass_scale": _float_value(_metadata(base, "mass_scale", float("nan"))),
        "brake_scale": _float_value(_metadata(base, "brake_scale", float("nan"))),
        "steer_tau_scale": _float_value(_metadata(base, "steer_tau_scale", float("nan"))),
        "source_run": config.source_run,
    }


def mine_policy_differences(frame: pd.DataFrame, config: PolicyDifferenceConfig) -> pd.DataFrame:
    episodes = prepare_episode_frame(frame)
    if "seed" not in episodes or "policy" not in episodes:
        raise ValueError("episodes CSV must contain 'seed' and 'policy' columns")
    baseline = episodes[episodes["policy"] == config.baseline_policy].copy()
    if baseline.empty:
        raise ValueError(f"baseline policy {config.baseline_policy!r} not found")
    if baseline["seed"].duplicated().any():
        raise ValueError(f"baseline policy {config.baseline_policy!r} has duplicate seeds")
    baseline_by_seed = baseline.set_index("seed", drop=False)
    candidates = (
        list(config.candidate_policies)
        if config.candidate_policies is not None
        else [str(policy) for policy in sorted(episodes["policy"].unique()) if policy != config.baseline_policy]
    )

    rows: list[dict[str, Any]] = []
    for policy in candidates:
        policy_rows = episodes[episodes["policy"] == policy].copy()
        if policy_rows.empty:
            raise ValueError(f"candidate policy {policy!r} not found")
        for _, candidate in policy_rows.iterrows():
            seed = candidate["seed"]
            if seed not in baseline_by_seed.index:
                continue
            row = _candidate_row(baseline_by_seed.loc[seed], candidate, config)
            if row is not None:
                rows.append(row)
    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame(rows).sort_values(["score", "seed", "candidate_policy"], ascending=[False, True, True])


def select_compact_corpus(candidates: pd.DataFrame, config: PolicyDifferenceConfig) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    selected_rows: list[dict[str, Any]] = []
    per_seed: defaultdict[Any, int] = defaultdict(int)
    per_policy: defaultdict[str, int] = defaultdict(int)
    per_obstacle: defaultdict[str, int] = defaultdict(int)
    per_mu_bucket: defaultdict[str, int] = defaultdict(int)

    for _, row in candidates.sort_values(["score", "seed", "candidate_policy"], ascending=[False, True, True]).iterrows():
        seed = row["seed"]
        policy = str(row["candidate_policy"])
        obstacle = _label(row.get("obstacle_label", ""))
        mu_bucket = _label(row.get("mu_bucket", ""))
        if len(selected_rows) >= config.max_rows:
            break
        if per_seed[seed] >= config.max_rows_per_seed:
            continue
        if per_policy[policy] >= config.max_rows_per_policy:
            continue
        if obstacle and per_obstacle[obstacle] >= config.max_rows_per_obstacle_label:
            continue
        if mu_bucket and per_mu_bucket[mu_bucket] >= config.max_rows_per_mu_bucket:
            continue
        selected_rows.append({column: row.get(column, "") for column in OUTPUT_COLUMNS})
        per_seed[seed] += 1
        per_policy[policy] += 1
        if obstacle:
            per_obstacle[obstacle] += 1
        if mu_bucket:
            per_mu_bucket[mu_bucket] += 1

    return pd.DataFrame(selected_rows, columns=OUTPUT_COLUMNS)


def _counter_dict(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(value for value in values if value).items()))


def _divergence_counter(frame: pd.DataFrame) -> dict[str, int]:
    counts: Counter[str] = Counter()
    if frame.empty:
        return {}
    for raw in frame["divergence_types"].tolist():
        for item in str(raw).split(";"):
            if item:
                counts[item] += 1
    return dict(sorted(counts.items()))


def _max_dominance(counts: dict[str, int], total: int) -> float:
    if total <= 0 or not counts:
        return 0.0
    return float(max(counts.values()) / total)


def summarize_mining(
    *,
    frame: pd.DataFrame,
    candidates: pd.DataFrame,
    selected: pd.DataFrame,
    config: PolicyDifferenceConfig,
) -> dict[str, Any]:
    accepted_by_policy = _counter_dict(candidates["candidate_policy"].astype(str).tolist()) if not candidates.empty else {}
    selected_by_policy = _counter_dict(selected["candidate_policy"].astype(str).tolist()) if not selected.empty else {}
    selected_by_obstacle = _counter_dict(selected["obstacle_label"].astype(str).tolist()) if not selected.empty else {}
    selected_by_mu_bucket = _counter_dict(selected["mu_bucket"].astype(str).tolist()) if not selected.empty else {}
    comparison_policies = (
        list(config.candidate_policies)
        if config.candidate_policies is not None
        else [str(policy) for policy in sorted(frame["policy"].unique()) if policy != config.baseline_policy]
    )
    rows_total = int(sum((frame["policy"] == policy).sum() for policy in comparison_policies))
    selected_rows = int(len(selected))
    return {
        "actor_inputs_changed": False,
        "checkpoint_promoted": False,
        "ppo_or_actor_update_run": False,
        "baseline_policy": config.baseline_policy,
        "candidate_policies": comparison_policies,
        "rows_total": rows_total,
        "accepted_rows": int(len(candidates)),
        "selected_rows": selected_rows,
        "accepted_by_policy": accepted_by_policy,
        "accepted_by_divergence_type": _divergence_counter(candidates),
        "selected_by_policy": selected_by_policy,
        "selected_by_divergence_type": _divergence_counter(selected),
        "selected_by_obstacle_label": selected_by_obstacle,
        "selected_by_mu_bucket": selected_by_mu_bucket,
        "max_policy_dominance": _max_dominance(selected_by_policy, selected_rows),
        "max_obstacle_label_dominance": _max_dominance(selected_by_obstacle, selected_rows),
        "thresholds": {
            "margin_delta_threshold": config.margin_delta_threshold,
            "large_margin_delta_threshold": config.large_margin_delta_threshold,
            "near_boundary_abs": config.near_boundary_abs,
            "return_delta_threshold": config.return_delta_threshold,
        },
    }


def run_policy_difference_miner(
    episodes_csv: Path,
    run_dir: Path,
    config: PolicyDifferenceConfig,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(episodes_csv)
    config = PolicyDifferenceConfig(**{**config.__dict__, "source_run": config.source_run or str(episodes_csv)})
    candidates = mine_policy_differences(frame, config)
    selected = select_compact_corpus(candidates, config)
    summary = summarize_mining(frame=prepare_episode_frame(frame), candidates=candidates, selected=selected, config=config)
    summary["episodes_csv"] = str(episodes_csv)
    summary["artifacts"] = {
        "policy_difference_candidates_csv": str(run_dir / "policy_difference_candidates.csv"),
        "compact_policy_difference_corpus_csv": str(run_dir / "compact_policy_difference_corpus.csv"),
        "policy_difference_summary_json": str(run_dir / "policy_difference_summary.json"),
    }

    candidate_rows = candidates.to_dict(orient="records") if not candidates.empty else []
    selected_rows = selected.to_dict(orient="records") if not selected.empty else []
    write_csv_rows(run_dir / "policy_difference_candidates.csv", candidate_rows, fieldnames=OUTPUT_COLUMNS)
    write_csv_rows(run_dir / "compact_policy_difference_corpus.csv", selected_rows, fieldnames=OUTPUT_COLUMNS)
    write_json(run_dir / "policy_difference_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine policy differences from benchmark episodes.")
    parser.add_argument("--episodes-csv", type=Path, required=True)
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--candidate-policy", action="append", default=[])
    parser.add_argument("--margin-delta-threshold", type=float, default=0.01)
    parser.add_argument("--large-margin-delta-threshold", type=float, default=0.05)
    parser.add_argument("--near-boundary-abs", type=float, default=0.25)
    parser.add_argument("--return-delta-threshold", type=float, default=1.0)
    parser.add_argument("--max-rows", type=int, default=64)
    parser.add_argument("--max-rows-per-seed", type=int, default=1)
    parser.add_argument("--max-rows-per-policy", type=int, default=20)
    parser.add_argument("--max-rows-per-obstacle-label", type=int, default=24)
    parser.add_argument("--max-rows-per-mu-bucket", type=int, default=24)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()

    config = PolicyDifferenceConfig(
        baseline_policy=args.baseline_policy,
        candidate_policies=tuple(args.candidate_policy) if args.candidate_policy else None,
        margin_delta_threshold=args.margin_delta_threshold,
        large_margin_delta_threshold=args.large_margin_delta_threshold,
        near_boundary_abs=args.near_boundary_abs,
        return_delta_threshold=args.return_delta_threshold,
        max_rows=args.max_rows,
        max_rows_per_seed=args.max_rows_per_seed,
        max_rows_per_policy=args.max_rows_per_policy,
        max_rows_per_obstacle_label=args.max_rows_per_obstacle_label,
        max_rows_per_mu_bucket=args.max_rows_per_mu_bucket,
    )
    summary = run_policy_difference_miner(args.episodes_csv, args.run_dir, config)
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
