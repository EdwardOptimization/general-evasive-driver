"""No-update evaluator for margin-weighted wrong-branch trust metrics."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.branch_preserving_temporal_repair_evaluator import (
    DEFAULT_ACTIVE_ROWS,
    DEFAULT_BASE_CHECKPOINT,
    DEFAULT_CANDIDATE_CHECKPOINTS,
    DEFAULT_M267_CORPUS,
    PRIMARY_ACTIVE_ROWS,
    SECONDARY_ACTIVE_ROWS,
    EvaluatedCheckpoint,
    _parse_active_rows,
    branch_weight_for_row,
    build_branch_examples,
    load_candidate_checkpoints,
)
from autodrift.capability_step_temporal_sequence_update_probe import clone_state_dict, state_checksum
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_M1004_REPLAY_ROWS = Path(
    "runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/"
    "candidate_preflight/m1002_temporal_a0_01/boundary_replay_rows.csv"
)
DEFAULT_RUN_DIR = Path("runs/m1011_v4_public_base_margin_weighted_branch_trust_region_evaluator")
DEFAULT_MARGIN_FLOOR = 1e-4
DEFAULT_ACTIVE_THRESHOLD = 1e-10
# M1010 pre-registered qualitative dominance rather than a fixed threshold.
# M1011 is the calibration milestone, so use a clear majority with slack.
DEFAULT_PRIMARY_DOMINANCE_MIN = 0.60


def margin_slack(base_wrong_margin: float, *, margin_floor: float) -> float:
    slack = max(abs(float(base_wrong_margin)), float(margin_floor))
    if not np.isfinite(slack) or slack <= 0.0:
        raise ValueError(f"invalid margin slack for margin={base_wrong_margin!r}, floor={margin_floor!r}")
    return slack


def source_normalized_weight(row_id: int, total_source_weight: float) -> float:
    if float(total_source_weight) <= 0.0:
        raise ValueError("total source weight must be positive")
    return float(branch_weight_for_row(row_id)) / float(total_source_weight)


def margin_scaled_contribution(
    *,
    row_id: int,
    action_l2_sq: float,
    base_wrong_margin: float,
    margin_floor: float,
    total_source_weight: float,
) -> float:
    slack = margin_slack(base_wrong_margin, margin_floor=margin_floor)
    return float(source_normalized_weight(row_id, total_source_weight)) * float(action_l2_sq) / (slack * slack)


def load_base_wrong_margins(
    replay_rows_csv: Path,
    *,
    active_rows: tuple[int, ...],
    base_policy: str = "m974_base",
) -> dict[int, float]:
    frame = pd.read_csv(replay_rows_csv)
    missing = [column for column in ("policy", "row_id", "wrong_history_margin") if column not in frame.columns]
    if missing:
        raise ValueError("replay rows CSV is missing columns: " + ", ".join(missing))
    selected = frame[frame["policy"].astype(str) == str(base_policy)].copy()
    selected["row_id"] = selected["row_id"].astype(int)
    selected = selected[selected["row_id"].isin({int(row_id) for row_id in active_rows})]
    duplicates = selected[selected["row_id"].duplicated(keep=False)]["row_id"].astype(int).tolist()
    if duplicates:
        raise ValueError(f"duplicate base replay rows for row_id(s): {sorted(set(duplicates))}")
    margins = {int(row["row_id"]): float(row["wrong_history_margin"]) for _, row in selected.iterrows()}
    missing_rows = sorted(set(int(row_id) for row_id in active_rows) - set(margins))
    if missing_rows:
        raise ValueError(f"base replay rows missing active row margins: {missing_rows}")
    return margins


def evaluate_margin_weighted_trust_for_checkpoint(
    *,
    model: ActorCritic,
    checkpoint: EvaluatedCheckpoint,
    examples: list[Any],
    base_wrong_margins: dict[int, float],
    margin_floor: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    total_source_weight = float(sum(branch_weight_for_row(example.row_id) for example in examples))
    rows: list[dict[str, Any]] = []
    action_l2_values: list[float] = []
    action_l2_sq_values: list[float] = []
    contributions: list[float] = []
    primary_contributions: list[float] = []
    finite_values: list[float] = []
    for example in examples:
        wrong_action, _ = deterministic_action_from_hidden(
            model,
            example.observation,
            example.wrong_hidden.to(device=device).reshape(1, -1),
            device,
        )
        delta = np.asarray(wrong_action, dtype=np.float64) - np.asarray(example.base_wrong_action, dtype=np.float64)
        action_l2_sq = float(np.dot(delta, delta))
        action_l2 = float(np.sqrt(action_l2_sq))
        row_id = int(example.row_id)
        base_margin = float(base_wrong_margins[row_id])
        slack = margin_slack(base_margin, margin_floor=margin_floor)
        contribution = margin_scaled_contribution(
            row_id=row_id,
            action_l2_sq=action_l2_sq,
            base_wrong_margin=base_margin,
            margin_floor=margin_floor,
            total_source_weight=total_source_weight,
        )
        source_weight = float(branch_weight_for_row(row_id))
        normalized_source_weight = source_normalized_weight(row_id, total_source_weight)
        margin_weight = source_weight / (slack * slack)
        action_l2_values.append(action_l2)
        action_l2_sq_values.append(action_l2_sq)
        contributions.append(contribution)
        if row_id in PRIMARY_ACTIVE_ROWS:
            primary_contributions.append(contribution)
        finite_values.extend(
            [
                action_l2,
                action_l2_sq,
                contribution,
                slack,
                margin_weight,
                float(wrong_action[0]),
                float(wrong_action[1]),
                float(wrong_action[2]),
            ]
        )
        rows.append(
            {
                "checkpoint_label": checkpoint.label,
                "alpha": "" if checkpoint.alpha is None else float(checkpoint.alpha),
                "checkpoint": str(checkpoint.path),
                "row_id": row_id,
                "target": example.target,
                "physical_pair_key": example.physical_pair_key,
                "source_weight": source_weight,
                "normalized_source_weight": normalized_source_weight,
                "base_wrong_margin": base_margin,
                "margin_floor": float(margin_floor),
                "margin_slack": slack,
                "margin_scaled_weight": margin_weight,
                "candidate_wrong_steer": float(wrong_action[0]),
                "candidate_wrong_throttle": float(wrong_action[1]),
                "candidate_wrong_brake": float(wrong_action[2]),
                "base_wrong_steer": float(example.base_wrong_action[0]),
                "base_wrong_throttle": float(example.base_wrong_action[1]),
                "base_wrong_brake": float(example.base_wrong_action[2]),
                "delta_steer": float(delta[0]),
                "delta_throttle": float(delta[1]),
                "delta_brake": float(delta[2]),
                "action_l2": action_l2,
                "action_l2_sq": action_l2_sq,
                "weighted_trust_contribution": contribution,
            }
        )
    total_loss = float(np.sum(np.asarray(contributions, dtype=np.float64)))
    primary_loss = float(np.sum(np.asarray(primary_contributions, dtype=np.float64)))
    primary_fraction = 0.0 if total_loss <= 0.0 else float(primary_loss / total_loss)
    action_l2_arr = np.asarray(action_l2_values, dtype=np.float64)
    action_l2_sq_arr = np.asarray(action_l2_sq_values, dtype=np.float64)
    contribution_arr = np.asarray(contributions, dtype=np.float64)
    finite_arr = np.asarray(finite_values, dtype=np.float64)
    summary = {
        "checkpoint_label": checkpoint.label,
        "alpha": "" if checkpoint.alpha is None else float(checkpoint.alpha),
        "checkpoint": checkpoint.path,
        "branch_row_count": int(len(rows)),
        "weighted_branch_trust_loss": total_loss,
        "primary_weighted_branch_trust_loss": primary_loss,
        "primary_contribution_fraction": primary_fraction,
        "action_l2_mean": float(np.mean(action_l2_arr)),
        "action_l2_max": float(np.max(action_l2_arr)),
        "action_l2_sq_mean": float(np.mean(action_l2_sq_arr)),
        "weighted_trust_contribution_max": float(np.max(contribution_arr)),
        "finite_branch_metrics": bool(np.isfinite(finite_arr).all()),
    }
    return summary, rows


def classify_margin_weighted_branch_trust_evaluator(
    *,
    finite_metrics: bool,
    base_trust_zero: bool,
    alpha_0_01_active: bool,
    alpha_0_2_increases: bool,
    primary_rows_dominate: bool,
    actor_parameters_changed: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_parameters_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "margin_weighted_branch_trust_region_evaluator_contract_artifact"
    if not bool(finite_metrics):
        return "margin_weighted_branch_trust_region_evaluator_nonfinite"
    if not bool(base_trust_zero):
        return "margin_weighted_branch_trust_region_evaluator_base_not_zero"
    if not bool(alpha_0_01_active):
        return "margin_weighted_branch_trust_region_evaluator_not_sensitive"
    if not bool(alpha_0_2_increases):
        return "margin_weighted_branch_trust_region_evaluator_not_monotone"
    if not bool(primary_rows_dominate):
        return "margin_weighted_branch_trust_region_evaluator_primary_not_dominant"
    return "margin_weighted_branch_trust_region_evaluator_pass"


def failure_types_for_result_class(result_class: str) -> list[str]:
    if result_class.endswith("_pass"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_nonfinite"):
        return ["training_instability"]
    if result_class.endswith("_base_not_zero") or result_class.endswith("_primary_not_dominant"):
        return ["objective_overfit"]
    if result_class.endswith("_not_sensitive") or result_class.endswith("_not_monotone"):
        return ["metric_artifact"]
    return ["metric_artifact"]


def run_margin_weighted_branch_trust_region_evaluator(
    *,
    base_checkpoint: Path,
    candidate_checkpoints_csv: Path,
    m267_corpus_csv: Path,
    m1004_replay_rows_csv: Path,
    run_dir: Path,
    device: str,
    env_config_path: Path,
    active_rows: tuple[int, ...],
    max_continuation_steps: int,
    margin_floor: float,
    active_threshold: float,
    primary_dominance_min: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    base_model, _ = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    base_model.eval()
    base_checksum_before = state_checksum(clone_state_dict(base_model))
    candidates = [EvaluatedCheckpoint(label="m974_base", path=base_checkpoint, alpha=None)]
    candidates.extend(load_candidate_checkpoints(candidate_checkpoints_csv))
    examples, example_rows = build_branch_examples(
        base_model=base_model,
        m267_corpus_csv=m267_corpus_csv,
        env_config_path=env_config_path,
        active_rows=active_rows,
        max_continuation_steps=max_continuation_steps,
        device=resolved_device,
        epsilon_logp=0.0,
        d_min_fraction=0.0,
        d_min_absolute=0.0,
    )
    base_wrong_margins = load_base_wrong_margins(
        m1004_replay_rows_csv,
        active_rows=active_rows,
        base_policy="m974_base",
    )
    margin_input_rows = [
        {
            "row_id": int(example.row_id),
            "target": example.target,
            "physical_pair_key": example.physical_pair_key,
            "source_weight": float(branch_weight_for_row(example.row_id)),
            "base_wrong_margin": float(base_wrong_margins[int(example.row_id)]),
            "margin_floor": float(margin_floor),
            "margin_slack": margin_slack(float(base_wrong_margins[int(example.row_id)]), margin_floor=margin_floor),
        }
        for example in examples
    ]
    branch_summary_rows: list[dict[str, Any]] = []
    branch_detail_rows: list[dict[str, Any]] = []
    actor_parameters_changed = False
    for checkpoint in candidates:
        model, _ = load_actor_critic_checkpoint(checkpoint.path, device=str(resolved_device))
        model.eval()
        checksum_before = state_checksum(clone_state_dict(model))
        summary, rows = evaluate_margin_weighted_trust_for_checkpoint(
            model=model,
            checkpoint=checkpoint,
            examples=examples,
            base_wrong_margins=base_wrong_margins,
            margin_floor=margin_floor,
            device=resolved_device,
        )
        checksum_after = state_checksum(clone_state_dict(model))
        summary["actor_parameters_changed"] = bool(checksum_before != checksum_after)
        actor_parameters_changed = bool(actor_parameters_changed or checksum_before != checksum_after)
        branch_summary_rows.append(summary)
        branch_detail_rows.extend(rows)
    base_checksum_after = state_checksum(clone_state_dict(base_model))
    actor_parameters_changed = bool(actor_parameters_changed or base_checksum_before != base_checksum_after)
    by_label = {str(row["checkpoint_label"]): row for row in branch_summary_rows}
    base_trust_loss = float(by_label["m974_base"]["weighted_branch_trust_loss"])
    alpha_0_01_loss = float(by_label["alpha_0_01"]["weighted_branch_trust_loss"])
    alpha_0_2_loss = float(by_label["alpha_0_2"]["weighted_branch_trust_loss"])
    alpha_0_01_primary_fraction = float(by_label["alpha_0_01"]["primary_contribution_fraction"])
    finite_metrics = bool(all(bool(row["finite_branch_metrics"]) for row in branch_summary_rows))
    base_trust_zero = bool(base_trust_loss <= 1e-14)
    alpha_0_01_active = bool(alpha_0_01_loss > float(active_threshold))
    alpha_0_2_increases = bool(alpha_0_2_loss > alpha_0_01_loss)
    primary_rows_dominate = bool(alpha_0_01_primary_fraction >= float(primary_dominance_min))
    result_class = classify_margin_weighted_branch_trust_evaluator(
        finite_metrics=finite_metrics,
        base_trust_zero=base_trust_zero,
        alpha_0_01_active=alpha_0_01_active,
        alpha_0_2_increases=alpha_0_2_increases,
        primary_rows_dominate=primary_rows_dominate,
        actor_parameters_changed=actor_parameters_changed,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "branch_examples.csv", example_rows)
    write_csv_rows(run_dir / "branch_margin_inputs.csv", margin_input_rows)
    write_csv_rows(run_dir / "margin_weighted_branch_summary.csv", branch_summary_rows)
    write_csv_rows(run_dir / "margin_weighted_branch_rows.csv", branch_detail_rows)
    summary = {
        "run_type": "margin_weighted_branch_trust_region_evaluator",
        "base_checkpoint": base_checkpoint,
        "candidate_checkpoints_csv": candidate_checkpoints_csv,
        "m267_corpus": m267_corpus_csv,
        "m1004_replay_rows": m1004_replay_rows_csv,
        "env_config": env_config_path,
        "active_rows": list(active_rows),
        "primary_active_rows": list(PRIMARY_ACTIVE_ROWS),
        "secondary_active_rows": list(SECONDARY_ACTIVE_ROWS),
        "max_continuation_steps": int(max_continuation_steps),
        "margin_floor": float(margin_floor),
        "active_threshold": float(active_threshold),
        "primary_dominance_min": float(primary_dominance_min),
        "evaluated_checkpoints": [row["checkpoint_label"] for row in branch_summary_rows],
        "branch_row_count": int(len(examples)),
        "finite_metrics": bool(finite_metrics),
        "base_trust_zero": bool(base_trust_zero),
        "alpha_0_01_active": bool(alpha_0_01_active),
        "alpha_0_2_increases": bool(alpha_0_2_increases),
        "primary_rows_dominate": bool(primary_rows_dominate),
        "base_weighted_branch_trust_loss": base_trust_loss,
        "alpha_0_01_weighted_branch_trust_loss": alpha_0_01_loss,
        "alpha_0_2_weighted_branch_trust_loss": alpha_0_2_loss,
        "alpha_0_01_primary_contribution_fraction": alpha_0_01_primary_fraction,
        "alpha_0_2_primary_contribution_fraction": float(by_label["alpha_0_2"]["primary_contribution_fraction"]),
        "actor_parameters_changed": bool(actor_parameters_changed),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_result_class(result_class),
        "next_blocker": (
            "margin-weighted branch repaired actor_mean update design"
            if result_class.endswith("_pass")
            else "margin-weighted branch trust-region evaluator audit"
        ),
        "branch_examples_csv": run_dir / "branch_examples.csv",
        "branch_margin_inputs_csv": run_dir / "branch_margin_inputs.csv",
        "margin_weighted_branch_summary_csv": run_dir / "margin_weighted_branch_summary.csv",
        "margin_weighted_branch_rows_csv": run_dir / "margin_weighted_branch_rows.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate margin-weighted wrong-branch trust metrics without actor updates.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoints", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINTS)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--m1004-replay-rows", type=Path, default=DEFAULT_M1004_REPLAY_ROWS)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--active-rows", type=_parse_active_rows, default=",".join(str(row) for row in DEFAULT_ACTIVE_ROWS))
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--margin-floor", type=float, default=DEFAULT_MARGIN_FLOOR)
    parser.add_argument("--active-threshold", type=float, default=DEFAULT_ACTIVE_THRESHOLD)
    parser.add_argument("--primary-dominance-min", type=float, default=DEFAULT_PRIMARY_DOMINANCE_MIN)
    args = parser.parse_args()
    summary = run_margin_weighted_branch_trust_region_evaluator(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoints_csv=args.candidate_checkpoints,
        m267_corpus_csv=args.m267_corpus,
        m1004_replay_rows_csv=args.m1004_replay_rows,
        run_dir=args.run_dir,
        device=args.device,
        env_config_path=args.env_config,
        active_rows=tuple(args.active_rows),
        max_continuation_steps=args.max_continuation_steps,
        margin_floor=args.margin_floor,
        active_threshold=args.active_threshold,
        primary_dominance_min=args.primary_dominance_min,
    )
    print(f"result_class={summary['result_class']}")
    print(f"base_trust_zero={summary['base_trust_zero']}")
    print(f"alpha_0_01_active={summary['alpha_0_01_active']}")
    print(f"alpha_0_2_increases={summary['alpha_0_2_increases']}")
    print(f"primary_rows_dominate={summary['primary_rows_dominate']}")
    print(f"alpha_0_01_weighted_branch_trust_loss={summary['alpha_0_01_weighted_branch_trust_loss']}")
    print(f"alpha_0_2_weighted_branch_trust_loss={summary['alpha_0_2_weighted_branch_trust_loss']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
