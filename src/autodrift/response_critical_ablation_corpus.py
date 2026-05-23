"""Export response-critical ablation rows from benchmark episodes."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import math

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json


DEPENDENCY_BY_POLICY = {
    "m399_reset": "recurrent_hidden_sensitive",
    "m399_zero_current": "current_response_sensitive",
    "m399_zero_all": "current_response_sensitive",
    "m399_noact": "action_history_sensitive",
}

OUTPUT_COLUMNS = [
    "source_config",
    "source_run",
    "source_seed_block",
    "seed",
    "ablation_policy",
    "ablation_family",
    "dependency_class",
    "failure_class",
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
    "base_lateral_peak",
    "candidate_lateral_peak",
    "delta_lateral_peak",
    "base_beta_peak",
    "candidate_beta_peak",
    "obstacle_label",
    "mu",
    "mu_bucket",
    "initial_mu",
    "initial_mu_bucket",
    "mass_scale",
    "brake_scale",
    "tire_stiffness_scale",
    "steer_tau_scale",
]


@dataclass(frozen=True)
class SourceSpec:
    episodes_csv: Path
    source_config: str
    track_width: float = 8.0


@dataclass(frozen=True)
class ResponseCriticalConfig:
    baseline_policy: str
    candidate_policies: tuple[str, ...]
    margin_delta_threshold: float = 0.01
    large_margin_delta_threshold: float = 0.05
    near_boundary_abs: float = 0.25
    return_delta_threshold: float = 1.0
    lateral_delta_threshold: float = 0.25
    beta_delta_threshold: float = 0.05
    beta_peak_threshold: float = 0.18
    max_rows: int = 96
    max_rows_per_seed: int = 2
    max_rows_per_policy: int = 24
    max_rows_per_config: int = 48
    max_rows_per_obstacle_label: int = 32
    max_rows_per_mu_bucket: int = 32
    max_rows_per_failure_class: int = 32


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
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


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


def _bucket(frame: pd.DataFrame, column: str, target: str, bins: list[float], labels: list[str]) -> None:
    if column in frame and target not in frame:
        frame[target] = pd.cut(frame[column], bins=bins, labels=labels, include_lowest=True)


def prepare_episode_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if "success" not in output:
        if "terminated" not in output:
            raise ValueError("episodes CSV must contain either 'success' or 'terminated'")
        output["success"] = ~output["terminated"].map(_bool_value)
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


def _ablation_family(policy: str) -> str:
    if "zero_current" in policy or "zero_all" in policy:
        return "zero_response"
    if "reset" in policy:
        return "reset_hidden"
    if "noact" in policy or "no_action" in policy:
        return "zero_action_history"
    return policy


def _base_dependency_class(policy: str) -> str:
    if policy in DEPENDENCY_BY_POLICY:
        return DEPENDENCY_BY_POLICY[policy]
    family = _ablation_family(policy)
    if family == "zero_response":
        return "current_response_sensitive"
    if family == "reset_hidden":
        return "recurrent_hidden_sensitive"
    if family == "zero_action_history":
        return "action_history_sensitive"
    return "weak_behavior_shift"


def _divergence_types(
    *,
    base_success: bool,
    candidate_success: bool,
    base_collision: bool,
    candidate_collision: bool,
    base_margin: float,
    candidate_margin: float,
    delta_margin: float,
    delta_return: float,
    base_lateral_peak: float,
    candidate_lateral_peak: float,
    delta_lateral_peak: float,
    base_beta_peak: float,
    candidate_beta_peak: float,
    track_width: float,
    config: ResponseCriticalConfig,
) -> tuple[list[str], float]:
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
    if (
        math.isfinite(base_lateral_peak)
        and math.isfinite(candidate_lateral_peak)
        and (base_lateral_peak < track_width <= candidate_lateral_peak)
    ):
        divergence_types.append("lateral_boundary_flip")
    elif math.isfinite(delta_lateral_peak) and abs(delta_lateral_peak) >= config.lateral_delta_threshold:
        divergence_types.append("lateral_peak_delta")
    if (
        math.isfinite(base_beta_peak)
        and math.isfinite(candidate_beta_peak)
        and candidate_beta_peak >= config.beta_peak_threshold
        and candidate_beta_peak - base_beta_peak >= config.beta_delta_threshold
    ):
        divergence_types.append("beta_peak_delta")

    score = 0.0
    score += 100.0 if "success_flip" in divergence_types else 0.0
    score += 80.0 if "collision_flip" in divergence_types else 0.0
    score += 60.0 if "margin_sign_flip" in divergence_types else 0.0
    score += 50.0 if "lateral_boundary_flip" in divergence_types else 0.0
    score += 40.0 if "near_boundary_margin_delta" in divergence_types else 0.0
    score += 15.0 if "beta_peak_delta" in divergence_types else 0.0
    if math.isfinite(delta_margin):
        score += 20.0 * min(abs(delta_margin) / max(config.large_margin_delta_threshold, 1e-12), 5.0)
    if math.isfinite(delta_return):
        score += 5.0 * min(abs(delta_return) / 5.0, 5.0)
    score += 2.0 if near_boundary else 0.0
    return divergence_types, float(score)


def _failure_class(
    *,
    base_success: bool,
    candidate_success: bool,
    base_collision: bool,
    candidate_collision: bool,
    base_margin: float,
    candidate_margin: float,
    delta_margin: float,
    delta_return: float,
    candidate_lateral_peak: float,
    base_beta_peak: float,
    candidate_beta_peak: float,
    track_width: float,
    config: ResponseCriticalConfig,
) -> str:
    if not base_success and candidate_success:
        return "ablation_rescue"
    margin_crosses = math.isfinite(base_margin) and math.isfinite(candidate_margin) and (base_margin >= 0.0) != (
        candidate_margin >= 0.0
    )
    near_boundary = math.isfinite(base_margin) and math.isfinite(candidate_margin) and (
        min(abs(base_margin), abs(candidate_margin)) <= config.near_boundary_abs
    )
    if base_success and not candidate_success:
        if candidate_collision or (not base_collision and candidate_collision):
            return "obstacle_collision_margin_crossing"
        if margin_crosses:
            return "near_boundary_obstacle_margin"
        if math.isfinite(candidate_lateral_peak) and candidate_lateral_peak >= track_width:
            return "road_boundary_failure"
        if (
            math.isfinite(base_beta_peak)
            and math.isfinite(candidate_beta_peak)
            and candidate_beta_peak >= config.beta_peak_threshold
            and candidate_beta_peak > base_beta_peak
        ):
            return "stability_failure"
        return "stability_failure"
    if margin_crosses or (near_boundary and math.isfinite(delta_margin) and abs(delta_margin) >= config.margin_delta_threshold):
        return "near_boundary_obstacle_margin"
    if math.isfinite(delta_margin) and abs(delta_margin) >= config.large_margin_delta_threshold:
        return "clearance_margin_shift"
    if math.isfinite(delta_return) and abs(delta_return) >= config.return_delta_threshold:
        return "return_only_shift"
    return "weak_behavior_shift"


def _candidate_row(
    *,
    base: pd.Series,
    candidate: pd.Series,
    source: SourceSpec,
    config: ResponseCriticalConfig,
) -> dict[str, Any] | None:
    base_success = _bool_value(base["success"])
    candidate_success = _bool_value(candidate["success"])
    base_collision = _bool_value(base.get("collision", False))
    candidate_collision = _bool_value(candidate.get("collision", False))
    base_margin = _float_value(base.get("min_clearance_margin", float("nan")))
    candidate_margin = _float_value(candidate.get("min_clearance_margin", float("nan")))
    delta_margin = _finite_delta(candidate_margin, base_margin)
    base_return = _float_value(base.get("return", float("nan")))
    candidate_return = _float_value(candidate.get("return", float("nan")))
    delta_return = _finite_delta(candidate_return, base_return)
    base_lateral_peak = _float_value(base.get("lateral_peak", float("nan")))
    candidate_lateral_peak = _float_value(candidate.get("lateral_peak", float("nan")))
    delta_lateral_peak = _finite_delta(candidate_lateral_peak, base_lateral_peak)
    base_beta_peak = _float_value(base.get("beta_abs_peak", float("nan")))
    candidate_beta_peak = _float_value(candidate.get("beta_abs_peak", float("nan")))
    divergence_types, score = _divergence_types(
        base_success=base_success,
        candidate_success=candidate_success,
        base_collision=base_collision,
        candidate_collision=candidate_collision,
        base_margin=base_margin,
        candidate_margin=candidate_margin,
        delta_margin=delta_margin,
        delta_return=delta_return,
        base_lateral_peak=base_lateral_peak,
        candidate_lateral_peak=candidate_lateral_peak,
        delta_lateral_peak=delta_lateral_peak,
        base_beta_peak=base_beta_peak,
        candidate_beta_peak=candidate_beta_peak,
        track_width=source.track_width,
        config=config,
    )
    if not divergence_types:
        return None
    policy = str(candidate["policy"])
    failure_class = _failure_class(
        base_success=base_success,
        candidate_success=candidate_success,
        base_collision=base_collision,
        candidate_collision=candidate_collision,
        base_margin=base_margin,
        candidate_margin=candidate_margin,
        delta_margin=delta_margin,
        delta_return=delta_return,
        candidate_lateral_peak=candidate_lateral_peak,
        base_beta_peak=base_beta_peak,
        candidate_beta_peak=candidate_beta_peak,
        track_width=source.track_width,
        config=config,
    )
    seed = int(candidate["seed"])
    return {
        "source_config": source.source_config,
        "source_run": str(source.episodes_csv),
        "source_seed_block": int(seed // 100) * 100,
        "seed": seed,
        "ablation_policy": policy,
        "ablation_family": _ablation_family(policy),
        "dependency_class": _base_dependency_class(policy),
        "failure_class": failure_class,
        "divergence_types": ";".join(divergence_types),
        "score": score,
        "base_success": base_success,
        "candidate_success": candidate_success,
        "base_collision": base_collision,
        "candidate_collision": candidate_collision,
        "base_margin": base_margin,
        "candidate_margin": candidate_margin,
        "delta_margin": delta_margin,
        "base_return": base_return,
        "candidate_return": candidate_return,
        "delta_return": delta_return,
        "base_lateral_peak": base_lateral_peak,
        "candidate_lateral_peak": candidate_lateral_peak,
        "delta_lateral_peak": delta_lateral_peak,
        "base_beta_peak": base_beta_peak,
        "candidate_beta_peak": candidate_beta_peak,
        "obstacle_label": _label(_metadata(base, "obstacle_label", "")),
        "mu": _float_value(_metadata(base, "mu", float("nan"))),
        "mu_bucket": _label(_metadata(base, "mu_bucket", "")),
        "initial_mu": _float_value(_metadata(base, "initial_mu", float("nan"))),
        "initial_mu_bucket": _label(_metadata(base, "initial_mu_bucket", "")),
        "mass_scale": _float_value(_metadata(base, "mass_scale", float("nan"))),
        "brake_scale": _float_value(_metadata(base, "brake_scale", float("nan"))),
        "tire_stiffness_scale": _float_value(_metadata(base, "tire_stiffness_scale", float("nan"))),
        "steer_tau_scale": _float_value(_metadata(base, "steer_tau_scale", float("nan"))),
    }


def _mark_mixed_dependencies(rows: list[dict[str, Any]]) -> None:
    by_source_seed: defaultdict[tuple[str, int], set[str]] = defaultdict(set)
    for row in rows:
        by_source_seed[(str(row["source_config"]), int(row["seed"]))].add(str(row["dependency_class"]))
    for row in rows:
        classes = by_source_seed[(str(row["source_config"]), int(row["seed"]))]
        if len(classes) > 1:
            row["dependency_class"] = "mixed_dependency"


def mine_response_critical_rows(
    frame: pd.DataFrame,
    *,
    source: SourceSpec,
    config: ResponseCriticalConfig,
) -> pd.DataFrame:
    episodes = prepare_episode_frame(frame)
    if "seed" not in episodes or "policy" not in episodes:
        raise ValueError("episodes CSV must contain 'seed' and 'policy' columns")
    baseline = episodes[episodes["policy"] == config.baseline_policy].copy()
    if baseline.empty:
        raise ValueError(f"baseline policy {config.baseline_policy!r} not found")
    if baseline["seed"].duplicated().any():
        raise ValueError(f"baseline policy {config.baseline_policy!r} has duplicate seeds")
    baseline_by_seed = baseline.set_index("seed", drop=False)
    rows: list[dict[str, Any]] = []
    for policy in config.candidate_policies:
        policy_rows = episodes[episodes["policy"] == policy].copy()
        if policy_rows.empty:
            raise ValueError(f"candidate policy {policy!r} not found")
        for _, candidate in policy_rows.iterrows():
            seed = candidate["seed"]
            if seed not in baseline_by_seed.index:
                continue
            row = _candidate_row(base=baseline_by_seed.loc[seed], candidate=candidate, source=source, config=config)
            if row is not None:
                rows.append(row)
    _mark_mixed_dependencies(rows)
    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS).sort_values(
        ["score", "source_config", "seed", "ablation_policy"],
        ascending=[False, True, True, True],
    )


def select_compact_corpus(candidates: pd.DataFrame, config: ResponseCriticalConfig) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    selected_rows: list[dict[str, Any]] = []
    per_source_seed: defaultdict[tuple[str, int], int] = defaultdict(int)
    per_policy: defaultdict[str, int] = defaultdict(int)
    per_config: defaultdict[str, int] = defaultdict(int)
    per_obstacle: defaultdict[str, int] = defaultdict(int)
    per_mu_bucket: defaultdict[str, int] = defaultdict(int)
    per_failure: defaultdict[str, int] = defaultdict(int)

    for _, row in candidates.sort_values(["score", "source_config", "seed"], ascending=[False, True, True]).iterrows():
        source_seed = (str(row["source_config"]), int(row["seed"]))
        policy = str(row["ablation_policy"])
        source_config = str(row["source_config"])
        obstacle = _label(row.get("obstacle_label", ""))
        mu_bucket = _label(row.get("mu_bucket", ""))
        failure_class = _label(row.get("failure_class", ""))
        if len(selected_rows) >= config.max_rows:
            break
        if per_source_seed[source_seed] >= config.max_rows_per_seed:
            continue
        if per_policy[policy] >= config.max_rows_per_policy:
            continue
        if per_config[source_config] >= config.max_rows_per_config:
            continue
        if obstacle and per_obstacle[obstacle] >= config.max_rows_per_obstacle_label:
            continue
        if mu_bucket and per_mu_bucket[mu_bucket] >= config.max_rows_per_mu_bucket:
            continue
        if failure_class and per_failure[failure_class] >= config.max_rows_per_failure_class:
            continue
        selected_rows.append({column: row.get(column, "") for column in OUTPUT_COLUMNS})
        per_source_seed[source_seed] += 1
        per_policy[policy] += 1
        per_config[source_config] += 1
        if obstacle:
            per_obstacle[obstacle] += 1
        if mu_bucket:
            per_mu_bucket[mu_bucket] += 1
        if failure_class:
            per_failure[failure_class] += 1
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


def summarize_corpus(
    *,
    candidates: pd.DataFrame,
    selected: pd.DataFrame,
    sources: list[SourceSpec],
    config: ResponseCriticalConfig,
) -> dict[str, Any]:
    selected_rows = int(len(selected))
    accepted_rows = int(len(candidates))
    dependency_counts = _counter_dict(candidates["dependency_class"].astype(str).tolist()) if not candidates.empty else {}
    failure_counts = _counter_dict(candidates["failure_class"].astype(str).tolist()) if not candidates.empty else {}
    selected_dependency_counts = (
        _counter_dict(selected["dependency_class"].astype(str).tolist()) if not selected.empty else {}
    )
    selected_failure_counts = _counter_dict(selected["failure_class"].astype(str).tolist()) if not selected.empty else {}
    selected_config_counts = _counter_dict(selected["source_config"].astype(str).tolist()) if not selected.empty else {}
    selected_policy_counts = _counter_dict(selected["ablation_policy"].astype(str).tolist()) if not selected.empty else {}
    selected_obstacle_counts = _counter_dict(selected["obstacle_label"].astype(str).tolist()) if not selected.empty else {}
    selected_mu_counts = _counter_dict(selected["mu_bucket"].astype(str).tolist()) if not selected.empty else {}
    return {
        "actor_inputs_changed": False,
        "checkpoint_promoted": False,
        "ppo_or_actor_update_run": False,
        "baseline_policy": config.baseline_policy,
        "candidate_policies": list(config.candidate_policies),
        "sources": [
            {"episodes_csv": str(source.episodes_csv), "source_config": source.source_config, "track_width": source.track_width}
            for source in sources
        ],
        "rows_total": int(sum(source_row_count(source.episodes_csv, config.candidate_policies) for source in sources)),
        "accepted_rows": accepted_rows,
        "selected_rows": selected_rows,
        "accepted_by_dependency_class": dependency_counts,
        "accepted_by_failure_class": failure_counts,
        "accepted_by_divergence_type": _divergence_counter(candidates),
        "selected_by_dependency_class": selected_dependency_counts,
        "selected_by_failure_class": selected_failure_counts,
        "selected_by_divergence_type": _divergence_counter(selected),
        "selected_by_source_config": selected_config_counts,
        "selected_by_policy": selected_policy_counts,
        "selected_by_obstacle_label": selected_obstacle_counts,
        "selected_by_mu_bucket": selected_mu_counts,
        "max_config_dominance": _max_dominance(selected_config_counts, selected_rows),
        "max_policy_dominance": _max_dominance(selected_policy_counts, selected_rows),
        "max_failure_class_dominance": _max_dominance(selected_failure_counts, selected_rows),
        "max_obstacle_label_dominance": _max_dominance(selected_obstacle_counts, selected_rows),
        "thresholds": {
            "margin_delta_threshold": config.margin_delta_threshold,
            "large_margin_delta_threshold": config.large_margin_delta_threshold,
            "near_boundary_abs": config.near_boundary_abs,
            "return_delta_threshold": config.return_delta_threshold,
            "lateral_delta_threshold": config.lateral_delta_threshold,
            "beta_delta_threshold": config.beta_delta_threshold,
            "beta_peak_threshold": config.beta_peak_threshold,
        },
    }


def source_row_count(episodes_csv: Path, candidate_policies: tuple[str, ...]) -> int:
    frame = pd.read_csv(episodes_csv, usecols=["policy"])
    return int(sum((frame["policy"] == policy).sum() for policy in candidate_policies))


def run_response_critical_export(
    sources: list[SourceSpec],
    run_dir: Path,
    config: ResponseCriticalConfig,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    for source in sources:
        frame = pd.read_csv(source.episodes_csv)
        frames.append(mine_response_critical_rows(frame, source=source, config=config))
    candidates = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=OUTPUT_COLUMNS)
    if not candidates.empty:
        candidates = candidates.sort_values(["score", "source_config", "seed"], ascending=[False, True, True])
    selected = select_compact_corpus(candidates, config)
    summary = summarize_corpus(candidates=candidates, selected=selected, sources=sources, config=config)
    summary["artifacts"] = {
        "candidates_csv": str(run_dir / "candidates.csv"),
        "compact_corpus_csv": str(run_dir / "compact_corpus.csv"),
        "summary_json": str(run_dir / "summary.json"),
    }
    write_csv_rows(run_dir / "candidates.csv", candidates.to_dict(orient="records"), fieldnames=OUTPUT_COLUMNS)
    write_csv_rows(run_dir / "compact_corpus.csv", selected.to_dict(orient="records"), fieldnames=OUTPUT_COLUMNS)
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_sources(episodes_csvs: list[Path], source_configs: list[str], track_widths: list[float]) -> list[SourceSpec]:
    if len(episodes_csvs) != len(source_configs):
        raise ValueError("--episodes-csv and --source-config must be supplied the same number of times")
    if track_widths and len(track_widths) != len(episodes_csvs):
        raise ValueError("--track-width must be omitted or supplied once for each --episodes-csv")
    widths = track_widths or [8.0 for _ in episodes_csvs]
    return [
        SourceSpec(episodes_csv=episodes_csv, source_config=source_config, track_width=track_width)
        for episodes_csv, source_config, track_width in zip(episodes_csvs, source_configs, widths)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export response-critical ablation corpus rows.")
    parser.add_argument("--episodes-csv", type=Path, action="append", required=True)
    parser.add_argument("--source-config", action="append", required=True)
    parser.add_argument("--track-width", type=float, action="append", default=[])
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--candidate-policy", action="append", required=True)
    parser.add_argument("--margin-delta-threshold", type=float, default=0.01)
    parser.add_argument("--large-margin-delta-threshold", type=float, default=0.05)
    parser.add_argument("--near-boundary-abs", type=float, default=0.25)
    parser.add_argument("--return-delta-threshold", type=float, default=1.0)
    parser.add_argument("--lateral-delta-threshold", type=float, default=0.25)
    parser.add_argument("--beta-delta-threshold", type=float, default=0.05)
    parser.add_argument("--beta-peak-threshold", type=float, default=0.18)
    parser.add_argument("--max-rows", type=int, default=96)
    parser.add_argument("--max-rows-per-seed", type=int, default=2)
    parser.add_argument("--max-rows-per-policy", type=int, default=24)
    parser.add_argument("--max-rows-per-config", type=int, default=48)
    parser.add_argument("--max-rows-per-obstacle-label", type=int, default=32)
    parser.add_argument("--max-rows-per-mu-bucket", type=int, default=32)
    parser.add_argument("--max-rows-per-failure-class", type=int, default=32)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()

    sources = _parse_sources(args.episodes_csv, args.source_config, args.track_width)
    config = ResponseCriticalConfig(
        baseline_policy=args.baseline_policy,
        candidate_policies=tuple(args.candidate_policy),
        margin_delta_threshold=args.margin_delta_threshold,
        large_margin_delta_threshold=args.large_margin_delta_threshold,
        near_boundary_abs=args.near_boundary_abs,
        return_delta_threshold=args.return_delta_threshold,
        lateral_delta_threshold=args.lateral_delta_threshold,
        beta_delta_threshold=args.beta_delta_threshold,
        beta_peak_threshold=args.beta_peak_threshold,
        max_rows=args.max_rows,
        max_rows_per_seed=args.max_rows_per_seed,
        max_rows_per_policy=args.max_rows_per_policy,
        max_rows_per_config=args.max_rows_per_config,
        max_rows_per_obstacle_label=args.max_rows_per_obstacle_label,
        max_rows_per_mu_bucket=args.max_rows_per_mu_bucket,
        max_rows_per_failure_class=args.max_rows_per_failure_class,
    )
    summary = run_response_critical_export(sources, args.run_dir, config)
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
