"""Reusable route-screen v2 runner for pre-public checkpoint filtering."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.benchmark import add_buckets, summarize
from autodrift.env import DriftEnvConfig
from autodrift.evaluate import evaluate_policy, load_env_config


@dataclass(frozen=True)
class RouteScreenPolicySpec:
    label: str
    checkpoint: Path
    env_config_path: Path
    env_config: DriftEnvConfig


Evaluator = Callable[..., tuple[list[dict[str, Any]], dict[str, float | int | str]]]


def parse_named_path(spec: str, *, option_name: str) -> tuple[str, Path]:
    """Parse NAME=PATH CLI specs."""

    if "=" not in spec:
        raise ValueError(f"{option_name} must be NAME=PATH, got {spec!r}")
    label, raw_path = spec.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"{option_name} has empty NAME: {spec!r}")
    raw_path = raw_path.strip()
    if not raw_path:
        raise ValueError(f"{option_name} has empty PATH: {spec!r}")
    return label, Path(raw_path)


def build_policy_specs(
    checkpoint_specs: list[str],
    env_config_specs: list[str],
) -> list[RouteScreenPolicySpec]:
    """Build route-screen policy specs from paired named checkpoint/config CLI args."""

    checkpoints = dict(parse_named_path(spec, option_name="--checkpoint-policy") for spec in checkpoint_specs)
    env_configs = dict(parse_named_path(spec, option_name="--env-config-policy") for spec in env_config_specs)
    if len(checkpoints) != len(checkpoint_specs):
        raise ValueError("duplicate --checkpoint-policy labels are not allowed")
    if len(env_configs) != len(env_config_specs):
        raise ValueError("duplicate --env-config-policy labels are not allowed")
    missing_configs = sorted(set(checkpoints) - set(env_configs))
    extra_configs = sorted(set(env_configs) - set(checkpoints))
    if missing_configs:
        raise ValueError(f"missing --env-config-policy for labels: {', '.join(missing_configs)}")
    if extra_configs:
        raise ValueError(f"--env-config-policy labels without checkpoint: {', '.join(extra_configs)}")
    return [
        RouteScreenPolicySpec(
            label=label,
            checkpoint=checkpoint,
            env_config_path=env_configs[label],
            env_config=load_env_config(env_configs[label]),
        )
        for label, checkpoint in checkpoints.items()
    ]


def _row_for_policy(policy_summary: pd.DataFrame, label: str) -> pd.Series:
    rows = policy_summary.loc[policy_summary["policy"].eq(label)]
    if rows.empty:
        raise ValueError(f"policy summary does not contain label {label!r}")
    return rows.iloc[0]


def compute_candidate_decision(
    policy_summary: pd.DataFrame,
    *,
    candidate_label: str,
    l0_label: str,
    l2_label: str,
    collision_tolerance: float = 0.02,
    l2_success_tolerance: float = 0.02,
    l2_margin_tolerance: float = 0.05,
) -> dict[str, Any]:
    """Apply the M551 route-screen v2 lexicographic rules for one candidate."""

    candidate = _row_for_policy(policy_summary, candidate_label)
    l0 = _row_for_policy(policy_summary, l0_label)
    l2 = _row_for_policy(policy_summary, l2_label)
    candidate_success = float(candidate["success_rate"])
    candidate_margin = float(candidate["min_clearance_margin_mean"])
    candidate_collision = float(candidate["collision_rate"])
    candidate_return = float(candidate["return_mean"])
    l0_success = float(l0["success_rate"])
    l0_margin = float(l0["min_clearance_margin_mean"])
    l0_collision = float(l0["collision_rate"])
    l2_success = float(l2["success_rate"])
    l2_margin = float(l2["min_clearance_margin_mean"])

    success_delta_l0 = candidate_success - l0_success
    margin_delta_l0 = candidate_margin - l0_margin
    collision_delta_l0 = candidate_collision - l0_collision
    success_delta_l2 = candidate_success - l2_success
    margin_delta_l2 = candidate_margin - l2_margin

    passes_l0_success = success_delta_l0 >= 0.0
    passes_l0_margin = margin_delta_l0 >= 0.0
    passes_l0_collision_tolerance = collision_delta_l0 <= collision_tolerance
    would_admit_public_eval = bool(
        passes_l0_success
        and passes_l0_margin
        and passes_l0_collision_tolerance
    )
    l2_competitive = bool(
        success_delta_l2 >= -l2_success_tolerance
        and margin_delta_l2 >= -l2_margin_tolerance
    )
    if not would_admit_public_eval:
        recommendation = "block_public_eval_below_l0"
    elif l2_competitive:
        recommendation = "admit_public_eval_l2_competitive"
    else:
        recommendation = "admit_public_eval_but_l2_gap"

    return {
        "candidate_label": candidate_label,
        "l0_label": l0_label,
        "l2_label": l2_label,
        "candidate_success_rate": candidate_success,
        "candidate_min_clearance_margin_mean": candidate_margin,
        "candidate_collision_rate": candidate_collision,
        "candidate_return_mean": candidate_return,
        "l0_success_rate": l0_success,
        "l0_min_clearance_margin_mean": l0_margin,
        "l0_collision_rate": l0_collision,
        "l2_success_rate": l2_success,
        "l2_min_clearance_margin_mean": l2_margin,
        "candidate_success_minus_l0": success_delta_l0,
        "candidate_margin_minus_l0": margin_delta_l0,
        "candidate_collision_minus_l0": collision_delta_l0,
        "candidate_success_minus_l2": success_delta_l2,
        "candidate_margin_minus_l2": margin_delta_l2,
        "passes_l0_success": passes_l0_success,
        "passes_l0_margin": passes_l0_margin,
        "passes_l0_collision_tolerance": passes_l0_collision_tolerance,
        "would_admit_public_eval": would_admit_public_eval,
        "l2_competitive": l2_competitive,
        "recommendation": recommendation,
    }


def _sort_key_for_admitted_candidate(decision: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        float(decision["candidate_success_rate"]),
        float(decision["candidate_min_clearance_margin_mean"]),
        -float(decision["candidate_collision_rate"]),
        float(decision["candidate_return_mean"]),
    )


def compute_route_screen_decision(
    policy_summary: pd.DataFrame,
    *,
    candidate_labels: list[str],
    l0_label: str,
    l2_label: str,
    collision_tolerance: float = 0.02,
    l2_success_tolerance: float = 0.02,
    l2_margin_tolerance: float = 0.05,
) -> dict[str, Any]:
    """Apply route-screen v2 to one or more candidate labels."""

    if not candidate_labels:
        raise ValueError("at least one candidate label is required")
    decisions = {
        label: compute_candidate_decision(
            policy_summary,
            candidate_label=label,
            l0_label=l0_label,
            l2_label=l2_label,
            collision_tolerance=collision_tolerance,
            l2_success_tolerance=l2_success_tolerance,
            l2_margin_tolerance=l2_margin_tolerance,
        )
        for label in candidate_labels
    }
    admitted = [
        decision
        for decision in decisions.values()
        if bool(decision["would_admit_public_eval"])
    ]
    admitted.sort(key=_sort_key_for_admitted_candidate, reverse=True)
    selected = admitted[0]["candidate_label"] if admitted else None
    return {
        "candidate_labels": list(candidate_labels),
        "l0_label": l0_label,
        "l2_label": l2_label,
        "collision_tolerance": collision_tolerance,
        "l2_success_tolerance": l2_success_tolerance,
        "l2_margin_tolerance": l2_margin_tolerance,
        "candidates": decisions,
        "admissible_candidate_labels": [str(decision["candidate_label"]) for decision in admitted],
        "selected_candidate_label": selected,
        "would_admit_public_eval": selected is not None,
    }


def run_route_screen_v2(
    policy_specs: list[RouteScreenPolicySpec],
    *,
    candidate_labels: list[str],
    l0_label: str,
    l2_label: str,
    episodes: int,
    seed: int,
    device: str = "cpu",
    run_dir: Path | None = None,
    collision_tolerance: float = 0.02,
    l2_success_tolerance: float = 0.02,
    l2_margin_tolerance: float = 0.05,
    evaluator: Evaluator = evaluate_policy,
) -> dict[str, Any]:
    """Evaluate policies on a public-neutral route distribution and write artifacts."""

    if episodes < 1:
        raise ValueError("episodes must be positive")
    labels = [spec.label for spec in policy_specs]
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if duplicates:
        raise ValueError(f"duplicate policy labels: {', '.join(duplicates)}")
    required_labels = set(candidate_labels) | {l0_label, l2_label}
    missing = sorted(required_labels - set(labels))
    if missing:
        raise ValueError(f"missing policy specs for labels: {', '.join(missing)}")

    resolved_run_dir = run_dir or make_run_dir(prefix="route_screen_v2", seed=seed)
    resolved_run_dir.mkdir(parents=True, exist_ok=True)
    seeds = [seed + index for index in range(episodes)]

    all_rows: list[dict[str, Any]] = []
    raw_policy_summaries: dict[str, dict[str, float | int | str]] = {}
    for spec in policy_specs:
        rows, raw_summary = evaluator(
            policy_name="checkpoint",
            episodes=episodes,
            seed=seed,
            checkpoint=spec.checkpoint,
            device=device,
            env_config=spec.env_config,
            seeds=seeds,
        )
        for row in rows:
            row["policy"] = spec.label
            row["route_screen_env_config"] = str(spec.env_config_path)
        raw_summary["policy"] = spec.label
        all_rows.extend(rows)
        raw_policy_summaries[spec.label] = raw_summary

    frame = add_buckets(pd.DataFrame(all_rows))
    policy_summary = summarize(frame, ["policy"])
    decision = compute_route_screen_decision(
        policy_summary,
        candidate_labels=candidate_labels,
        l0_label=l0_label,
        l2_label=l2_label,
        collision_tolerance=collision_tolerance,
        l2_success_tolerance=l2_success_tolerance,
        l2_margin_tolerance=l2_margin_tolerance,
    )

    episodes_csv = resolved_run_dir / "episodes.csv"
    policy_summary_csv = resolved_run_dir / "policy_summary.csv"
    summary_json = resolved_run_dir / "summary.json"
    frame.to_csv(episodes_csv, index=False)
    policy_summary.to_csv(policy_summary_csv, index=False)

    summary = {
        "run_type": "route_screen_v2",
        "episodes": episodes,
        "seed": seed,
        "seed_list": seeds,
        "device": device,
        "uses_public_frozen_source_rows": False,
        "public_row_source": None,
        "l0_label": l0_label,
        "l2_label": l2_label,
        "candidate_labels": list(candidate_labels),
        "policy_specs": {
            spec.label: {
                "checkpoint": spec.checkpoint,
                "env_config": spec.env_config_path,
            }
            for spec in policy_specs
        },
        "raw_policy_summaries": raw_policy_summaries,
        "decision": decision,
        "artifacts": {
            "episodes_csv": episodes_csv,
            "policy_summary_csv": policy_summary_csv,
            "summary_json": summary_json,
        },
    }
    write_json(summary_json, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint-policy",
        action="append",
        default=[],
        help="Named checkpoint in LABEL=PATH form. Repeat for L0/L2/candidates.",
    )
    parser.add_argument(
        "--env-config-policy",
        action="append",
        default=[],
        help="Named env config in LABEL=PATH form. Labels must match --checkpoint-policy.",
    )
    parser.add_argument(
        "--candidate-label",
        action="append",
        default=[],
        help="Candidate label to screen. Can be repeated.",
    )
    parser.add_argument("--l0-label", required=True)
    parser.add_argument("--l2-label", required=True)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--seed", type=int, default=14540)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--collision-tolerance", type=float, default=0.02)
    parser.add_argument("--l2-success-tolerance", type=float, default=0.02)
    parser.add_argument("--l2-margin-tolerance", type=float, default=0.05)
    args = parser.parse_args()

    policy_specs = build_policy_specs(args.checkpoint_policy, args.env_config_policy)
    summary = run_route_screen_v2(
        policy_specs,
        candidate_labels=args.candidate_label,
        l0_label=args.l0_label,
        l2_label=args.l2_label,
        episodes=args.episodes,
        seed=args.seed,
        device=args.device,
        run_dir=args.run_dir,
        collision_tolerance=args.collision_tolerance,
        l2_success_tolerance=args.l2_success_tolerance,
        l2_margin_tolerance=args.l2_margin_tolerance,
    )
    print(f"run_dir={Path(summary['artifacts']['summary_json']).parent}")
    print(f"would_admit_public_eval={summary['decision']['would_admit_public_eval']}")
    print(f"selected_candidate_label={summary['decision']['selected_candidate_label']}")


if __name__ == "__main__":
    main()
