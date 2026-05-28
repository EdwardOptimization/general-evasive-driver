"""Replay-aware retained source-history update probe for M1355."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.exact_post_ppo_repair import exact_trajectory_action_anchor_loss
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.materialized_source_history_objective_evaluator import (
    DEFAULT_CORRECT_MARGIN,
    DEFAULT_WRONG_COEF,
    DEFAULT_WRONG_MARGIN,
    evaluate_materialized_source_history_objective,
)
from autodrift.materialized_source_history_pair_group_metrics import run_pair_group_metrics
from autodrift.materialized_source_history_pair_group_update import (
    DEFAULT_EVAL_FOLD,
    DEFAULT_GROUP_BALANCE_COEF,
    DEFAULT_GROUP_MARGIN,
    DEFAULT_GROUP_MIN_COEF,
    DEFAULT_TRAIN_FOLDS,
    DEFAULT_TRAINABLE_SCOPE,
    ALLOWED_PARAMETER_NAMES,
    _clone_state_dict,
    _copy_objective_outputs,
    _finite_float,
    _finite_summary,
    _fold_group_min_mean,
    _load_materialized_pair_group_batch,
    _pair_group_losses,
    _parameter_counts,
    _parse_folds,
    _run_group_metrics,
    _save_checkpoint,
    _set_trainable_scope,
    _state_delta,
)
from autodrift.source_history_policy_gate import _checkpoint_contract
from autodrift.terminal_margin_retention_surface import SurfaceSpec, export_retention_surface
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_BASE_CHECKPOINT = Path("runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt")
DEFAULT_ALPHA005_CHECKPOINT = Path(
    "runs/m1352_materialized_source_history_interpolation_preflight/checkpoints/alpha_0_005.pt"
)
DEFAULT_CORPUS_RUN_DIR = Path("runs/m1336_materialized_source_history_objective_corpus_export")
DEFAULT_ALPHA_SUMMARY = Path("runs/m1352_materialized_source_history_interpolation_preflight/alpha_summary.csv")
DEFAULT_M267_REPLAY_ROWS = Path(
    "runs/m1352_materialized_source_history_interpolation_preflight/replay/m1352_alpha_0_005/"
    "m267_m264/boundary_replay_rows.csv"
)
DEFAULT_M183_REPLAY_ROWS = Path(
    "runs/m1352_materialized_source_history_interpolation_preflight/replay/m1352_alpha_0_005/"
    "m183_m170/boundary_replay_rows.csv"
)
DEFAULT_M267_CORPUS = Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")
DEFAULT_M183_CORPUS = Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")
DEFAULT_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_RUN_DIR = Path("runs/m1355_materialized_source_history_replay_aware_retention_probe")
BASE_LABEL = "m1154_base"
CANDIDATE_LABEL = "m1355_retained"
DEFAULT_FORCE_ROWS = "m183_m170:1,m183_m170:4,m183_m170:12,m183_m170:14,m183_m170:16"


def parse_force_keys(text: str) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    if not str(text).strip():
        return keys
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise argparse.ArgumentTypeError(f"force row must be SURFACE:ROW_ID, got {item!r}")
        surface, row_id = item.split(":", 1)
        surface = surface.strip()
        if not surface:
            raise argparse.ArgumentTypeError(f"force row has empty surface: {item!r}")
        keys.add((surface, int(row_id)))
    return keys


def _read_alpha005_metrics(alpha_summary_csv: Path) -> dict[str, float]:
    import csv

    with Path(alpha_summary_csv).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if abs(float(row["alpha"]) - 0.005) <= 1e-12:
                return {
                    "combined_loss_delta_vs_base": float(row["combined_loss_delta_vs_base"]),
                    "group_min_joint_margin_delta_vs_base": float(row["group_min_joint_margin_delta_vs_base"]),
                    "eval_fold_4_group_min_joint_margin_delta_vs_base": float(
                        row["eval_fold_4_group_min_joint_margin_delta_vs_base"]
                    ),
                }
    raise ValueError(f"missing alpha 0.005 row in {alpha_summary_csv}")


def _hidden_size(model: ActorCritic) -> int:
    return int(model.actor_mean.in_features)


def _trajectory_anchor_loss(model: ActorCritic, anchor: Any) -> torch.Tensor:
    return exact_trajectory_action_anchor_loss(model, anchor)


def _run_replay(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    corpus_csv: Path,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> dict[str, Any]:
    return run_boundary_outcome_replay_gate(
        checkpoint_specs=(
            CheckpointSpec(label=BASE_LABEL, path=base_checkpoint),
            CheckpointSpec(label=CANDIDATE_LABEL, path=candidate_checkpoint),
        ),
        corpus_csv=corpus_csv,
        env_config_path=env_config_path,
        max_rows=0,
        max_continuation_steps=max_continuation_steps,
        baseline_policy=BASE_LABEL,
        candidate_policy=CANDIDATE_LABEL,
        max_normal_success_drop=0.0,
        max_normal_margin_regression=0.005,
        max_margin_gap_regression=0.001,
        max_success_drop_count_regression=0,
        device=device,
        run_dir=run_dir,
    )


def classify_retention_probe(
    *,
    contract_failure: bool,
    exact_improved: bool,
    m267_pass: bool,
    m183_ran: bool,
    m183_pass: bool,
    beat_alpha005: bool,
) -> str:
    if contract_failure:
        return "materialized_source_history_replay_aware_retention_contract_artifact"
    if not exact_improved:
        return "materialized_source_history_replay_aware_retention_no_exact_lift"
    if not m267_pass:
        return "materialized_source_history_replay_aware_retention_m267_proof_washout"
    if not m183_ran or not m183_pass:
        return "materialized_source_history_replay_aware_retention_m183_proof_washout"
    if not beat_alpha005:
        return "materialized_source_history_replay_aware_retention_replay_pass_but_weak"
    return "materialized_source_history_replay_aware_retention_probe_pass"


def failure_types_for_result(result_class: str) -> list[str]:
    if result_class.endswith("_pass"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_no_exact_lift") or result_class.endswith("_replay_pass_but_weak"):
        return ["objective_overfit"]
    if result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    return ["metric_artifact"]


def run_materialized_source_history_replay_aware_retention_probe(
    *,
    checkpoint_path: Path,
    alpha005_checkpoint: Path,
    corpus_run_dir: Path,
    alpha_summary_csv: Path,
    m267_replay_rows: Path,
    m183_replay_rows: Path,
    m267_corpus: Path,
    m183_corpus: Path,
    env_config_path: Path,
    run_dir: Path,
    device: str = "auto",
    train_folds: str = DEFAULT_TRAIN_FOLDS,
    eval_fold: int = DEFAULT_EVAL_FOLD,
    steps: int = 120,
    lr: float = 5e-5,
    correct_margin: float = DEFAULT_CORRECT_MARGIN,
    wrong_margin: float = DEFAULT_WRONG_MARGIN,
    wrong_coef: float = DEFAULT_WRONG_COEF,
    group_margin: float = DEFAULT_GROUP_MARGIN,
    group_min_coef: float = DEFAULT_GROUP_MIN_COEF,
    group_balance_coef: float = DEFAULT_GROUP_BALANCE_COEF,
    trust_coef: float = 1e-3,
    retention_coef: float = 1000.0,
    retention_max_normal_margin: float = 0.007,
    retention_allowed_regression: float = 5e-7,
    retention_max_weight: float = 50.0,
    retention_weight_epsilon: float = 1e-6,
    force_rows: set[tuple[str, int]] = parse_force_keys(DEFAULT_FORCE_ROWS),
    max_continuation_steps: int = 60,
) -> dict[str, Any]:
    checkpoint_path = Path(checkpoint_path)
    alpha005_checkpoint = Path(alpha005_checkpoint)
    corpus_run_dir = Path(corpus_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    if int(steps) < 1:
        raise ValueError("steps must be positive")
    if float(lr) <= 0.0:
        raise ValueError("lr must be positive")
    train_fold_values = _parse_folds(train_folds)
    resolved_device = resolve_device(device)
    alpha005_metrics = _read_alpha005_metrics(Path(alpha_summary_csv))

    before_eval_dir = run_dir / "before_eval"
    before_summary = evaluate_materialized_source_history_objective(
        checkpoint_path=checkpoint_path,
        corpus_run_dir=corpus_run_dir,
        run_dir=before_eval_dir,
        device=str(resolved_device),
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )
    before_summary = _copy_objective_outputs(before_eval_dir, run_dir, "before")
    before_group_summary = _run_group_metrics(before_eval_dir, run_dir, "before")

    model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    contract_ok, contract_reason = _checkpoint_contract(model, checkpoint_data)
    if not contract_ok:
        raise ValueError(f"checkpoint contract violation: {contract_reason}")
    model.eval()
    trainable_parameters = _set_trainable_scope(model, DEFAULT_TRAINABLE_SCOPE)
    trainable_count, frozen_count = _parameter_counts(model)
    base_state = _clone_state_dict(model)
    batch = _load_materialized_pair_group_batch(
        model=model,
        corpus_run_dir=corpus_run_dir,
        device=resolved_device,
        train_folds=train_fold_values,
    )

    retention_summary = export_retention_surface(
        checkpoint_spec=CheckpointSpec(label=BASE_LABEL, path=checkpoint_path),
        candidate_policy=BASE_LABEL,
        surfaces=[
            SurfaceSpec(name="m183_m170", replay_rows_csv=Path(m183_replay_rows)),
            SurfaceSpec(name="m267_m264", replay_rows_csv=Path(m267_replay_rows)),
        ],
        env_config_path=Path(env_config_path),
        max_normal_margin=float(retention_max_normal_margin),
        force_keys=set(force_rows),
        allowed_regression=float(retention_allowed_regression),
        max_weight=float(retention_max_weight),
        weight_epsilon=float(retention_weight_epsilon),
        max_continuation_steps=int(max_continuation_steps),
        device=str(resolved_device),
        run_dir=run_dir / "retention_surface",
    )
    anchor = load_trajectory_action_anchor(
        Path(str(retention_summary["retention_trajectory_anchor_npz"])),
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=_hidden_size(model),
        act_dim=int(model.act_dim),
    )

    optimizer = torch.optim.Adam(trainable_parameters, lr=float(lr))
    trace_rows: list[dict[str, Any]] = []
    for step in range(int(steps)):
        optimizer.zero_grad()
        source_losses = _pair_group_losses(
            model,
            batch,
            correct_margin=correct_margin,
            wrong_margin=wrong_margin,
            wrong_coef=wrong_coef,
            group_margin=group_margin,
            group_min_coef=group_min_coef,
            group_balance_coef=group_balance_coef,
            trust_coef=trust_coef,
            base_state=base_state,
        )
        retention_loss = _trajectory_anchor_loss(model, anchor)
        loss = source_losses["loss"] + float(retention_coef) * retention_loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable_parameters, max_norm=1.0)
        optimizer.step()
        trace_rows.append(
            {
                "step": int(step + 1),
                "loss": float(loss.detach().cpu().item()),
                "source_loss": float(source_losses["loss"].detach().cpu().item()),
                "retention_loss": float(retention_loss.detach().cpu().item()),
                "weighted_retention_loss": float((float(retention_coef) * retention_loss).detach().cpu().item()),
                "train_row_loss": float(source_losses["train_row_loss"].detach().cpu().item()),
                "train_group_min_margin_mean": float(source_losses["train_group_min_margin_mean"].detach().cpu().item()),
                "group_min_loss": float(source_losses["group_min_loss"].detach().cpu().item()),
                "group_balance_loss": float(source_losses["group_balance_loss"].detach().cpu().item()),
                "trust_loss": float(source_losses["trust_loss"].detach().cpu().item()),
            }
        )

    updated_state = _clone_state_dict(model)
    parameter_delta = _state_delta(base_state, updated_state)
    write_csv_rows(run_dir / "train_trace.csv", trace_rows)
    write_csv_rows(run_dir / "parameter_delta_rows.csv", parameter_delta["per_parameter_rows"])
    write_json(
        run_dir / "parameter_delta.json",
        {key: value for key, value in parameter_delta.items() if key != "per_parameter_rows"}
        | {
            "trainable_scope": DEFAULT_TRAINABLE_SCOPE,
            "trainable_parameter_count": int(trainable_count),
            "frozen_parameter_count": int(frozen_count),
        },
    )

    checkpoint_out = run_dir / "checkpoints" / "raw_replay_aware_retention_update.pt"
    _save_checkpoint(
        checkpoint_data=checkpoint_data,
        model=model,
        path=checkpoint_out,
        metadata={
            "materialized_source_history_replay_aware_retention_probe": {
                "run_dir": str(run_dir),
                "base_checkpoint": str(checkpoint_path),
                "steps": int(steps),
                "lr": float(lr),
                "retention_coef": float(retention_coef),
            }
        },
    )

    after_eval_dir = run_dir / "after_eval"
    after_summary = evaluate_materialized_source_history_objective(
        checkpoint_path=checkpoint_out,
        corpus_run_dir=corpus_run_dir,
        run_dir=after_eval_dir,
        device=str(resolved_device),
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )
    after_summary = _copy_objective_outputs(after_eval_dir, run_dir, "after")
    after_group_summary = _run_group_metrics(after_eval_dir, run_dir, "after")

    before_group_mean = _finite_float(before_group_summary.get("group_min_joint_margin_mean"))
    after_group_mean = _finite_float(after_group_summary.get("group_min_joint_margin_mean"))
    before_eval_fold_mean = _fold_group_min_mean(run_dir / "fold_group_summary_before.csv", int(eval_fold))
    after_eval_fold_mean = _fold_group_min_mean(run_dir / "fold_group_summary_after.csv", int(eval_fold))
    combined_delta = float(
        _finite_float(after_summary.get("combined_loss_mean"))
        - _finite_float(before_summary.get("combined_loss_mean"))
    )
    group_delta = float(after_group_mean - before_group_mean)
    eval_fold_delta = float(after_eval_fold_mean - before_eval_fold_mean)
    exact_improved = bool(
        bool(before_summary.get("exact_objective_finite", False))
        and bool(after_summary.get("exact_objective_finite", False))
        and _finite_summary(before_group_summary, ["group_min_joint_margin_mean"])
        and _finite_summary(after_group_summary, ["group_min_joint_margin_mean"])
        and combined_delta < 0.0
        and group_delta > 0.0
        and after_eval_fold_mean + 1e-12 >= before_eval_fold_mean
    )
    beat_alpha005 = bool(
        combined_delta < float(alpha005_metrics["combined_loss_delta_vs_base"])
        and group_delta > float(alpha005_metrics["group_min_joint_margin_delta_vs_base"])
        and eval_fold_delta >= float(alpha005_metrics["eval_fold_4_group_min_joint_margin_delta_vs_base"]) - 1e-12
    )

    m267_summary = _run_replay(
        base_checkpoint=checkpoint_path,
        candidate_checkpoint=checkpoint_out,
        corpus_csv=Path(m267_corpus),
        env_config_path=Path(env_config_path),
        device=str(resolved_device),
        run_dir=run_dir / "replay" / "m267_m264",
        max_continuation_steps=max_continuation_steps,
    )
    m183_summary: dict[str, Any] | None = None
    if bool(m267_summary.get("gate_pass", False)):
        m183_summary = _run_replay(
            base_checkpoint=checkpoint_path,
            candidate_checkpoint=checkpoint_out,
            corpus_csv=Path(m183_corpus),
            env_config_path=Path(env_config_path),
            device=str(resolved_device),
            run_dir=run_dir / "replay" / "m183_m170",
            max_continuation_steps=max_continuation_steps,
        )

    contract_failure = bool(
        parameter_delta["forbidden_parameter_mutation_detected"]
        or float(parameter_delta["log_std_l2"]) != 0.0
    )
    result_class = classify_retention_probe(
        contract_failure=contract_failure,
        exact_improved=exact_improved,
        m267_pass=bool(m267_summary.get("gate_pass", False)),
        m183_ran=m183_summary is not None,
        m183_pass=bool(m183_summary.get("gate_pass", False)) if m183_summary is not None else False,
        beat_alpha005=beat_alpha005,
    )
    failure_types = failure_types_for_result(result_class)

    summary = {
        "run_type": "materialized_source_history_replay_aware_retention_probe",
        "result_class": result_class,
        "failure_types": failure_types,
        "checkpoint": str(checkpoint_path),
        "alpha005_checkpoint": str(alpha005_checkpoint),
        "checkpoint_out": str(checkpoint_out),
        "corpus_run_dir": str(corpus_run_dir),
        "device": str(resolved_device),
        "checkpoint_contract": contract_reason,
        "trainable_scope": DEFAULT_TRAINABLE_SCOPE,
        "allowed_trainable_parameters": sorted(ALLOWED_PARAMETER_NAMES),
        "train_folds": [int(fold) for fold in train_fold_values],
        "eval_fold": int(eval_fold),
        "steps": int(steps),
        "lr": float(lr),
        "retention_coef": float(retention_coef),
        "retention_summary": retention_summary,
        "retention_fragile_rows": int(retention_summary.get("fragile_rows", 0)),
        "retention_trajectory_rows": int(retention_summary.get("trajectory_rows", 0)),
        "retention_force_rows": [f"{surface}:{row_id}" for surface, row_id in sorted(force_rows)],
        "base_combined_loss_mean": _finite_float(before_summary.get("combined_loss_mean")),
        "after_combined_loss_mean": _finite_float(after_summary.get("combined_loss_mean")),
        "combined_loss_delta": combined_delta,
        "base_group_min_joint_margin_mean": before_group_mean,
        "after_group_min_joint_margin_mean": after_group_mean,
        "full_group_min_joint_margin_delta": group_delta,
        "eval_fold_group_min_joint_margin_mean_before": before_eval_fold_mean,
        "eval_fold_group_min_joint_margin_mean_after": after_eval_fold_mean,
        "eval_fold_group_min_joint_margin_delta": eval_fold_delta,
        "alpha005_combined_loss_delta_vs_base": float(alpha005_metrics["combined_loss_delta_vs_base"]),
        "alpha005_group_min_joint_margin_delta_vs_base": float(
            alpha005_metrics["group_min_joint_margin_delta_vs_base"]
        ),
        "alpha005_eval_fold_4_group_min_joint_margin_delta_vs_base": float(
            alpha005_metrics["eval_fold_4_group_min_joint_margin_delta_vs_base"]
        ),
        "exact_improved_vs_base": bool(exact_improved),
        "beat_alpha005_exact_lift": bool(beat_alpha005),
        "m267_m264_gate_pass": bool(m267_summary.get("gate_pass", False)),
        "m267_m264_normal_success_delta": float(m267_summary.get("normal_success_delta", float("nan"))),
        "m267_m264_success_drop_count_delta": int(m267_summary.get("success_drop_count_delta", 0)),
        "m267_m264_normal_margin_mean_delta": float(m267_summary.get("normal_margin_mean_delta", float("nan"))),
        "m267_m264_margin_gap_mean_delta": float(m267_summary.get("margin_gap_mean_delta", float("nan"))),
        "m183_m170_ran": bool(m183_summary is not None),
        "m183_m170_gate_pass": bool(m183_summary.get("gate_pass", False)) if m183_summary is not None else False,
        "m183_m170_normal_success_delta": (
            float(m183_summary.get("normal_success_delta", float("nan"))) if m183_summary is not None else None
        ),
        "m183_m170_success_drop_count_delta": (
            int(m183_summary.get("success_drop_count_delta", 0)) if m183_summary is not None else None
        ),
        "m183_m170_normal_margin_mean_delta": (
            float(m183_summary.get("normal_margin_mean_delta", float("nan"))) if m183_summary is not None else None
        ),
        "m183_m170_margin_gap_mean_delta": (
            float(m183_summary.get("margin_gap_mean_delta", float("nan"))) if m183_summary is not None else None
        ),
        "trainable_parameter_count": int(trainable_count),
        "frozen_parameter_count": int(frozen_count),
        "allowed_parameter_l2": float(parameter_delta["allowed_parameter_l2"]),
        "allowed_parameter_max_abs": float(parameter_delta["allowed_parameter_max_abs"]),
        "forbidden_parameter_l2": float(parameter_delta["forbidden_parameter_l2"]),
        "forbidden_parameter_max_abs": float(parameter_delta["forbidden_parameter_max_abs"]),
        "log_std_l2": float(parameter_delta["log_std_l2"]),
        "forbidden_parameter_mutation_detected": bool(parameter_delta["forbidden_parameter_mutation_detected"]),
        "changed_parameter_names": parameter_delta["changed_parameter_names"],
        "labels_enter_actor_input": False,
        "objective_update_started": True,
        "actor_update_used": True,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "next_blocker": "m1356 materialized source-history pair-group branch synthesis",
        "summary_before_json": run_dir / "objective_before.json",
        "summary_after_json": run_dir / "objective_after.json",
        "group_summary_before_json": run_dir / "group_metrics_before.json",
        "group_summary_after_json": run_dir / "group_metrics_after.json",
        "retention_surface_summary_json": run_dir / "retention_surface" / "summary.json",
        "train_trace_csv": run_dir / "train_trace.csv",
        "parameter_delta_json": run_dir / "parameter_delta.json",
        "parameter_delta_rows_csv": run_dir / "parameter_delta_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--alpha005-checkpoint", type=Path, default=DEFAULT_ALPHA005_CHECKPOINT)
    parser.add_argument("--corpus-run-dir", type=Path, default=DEFAULT_CORPUS_RUN_DIR)
    parser.add_argument("--alpha-summary-csv", type=Path, default=DEFAULT_ALPHA_SUMMARY)
    parser.add_argument("--m267-replay-rows", type=Path, default=DEFAULT_M267_REPLAY_ROWS)
    parser.add_argument("--m183-replay-rows", type=Path, default=DEFAULT_M183_REPLAY_ROWS)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--m183-corpus", type=Path, default=DEFAULT_M183_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--train-folds", type=str, default=DEFAULT_TRAIN_FOLDS)
    parser.add_argument("--eval-fold", type=int, default=DEFAULT_EVAL_FOLD)
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--retention-coef", type=float, default=1000.0)
    parser.add_argument("--retention-max-normal-margin", type=float, default=0.007)
    parser.add_argument("--force-rows", type=parse_force_keys, default=parse_force_keys(DEFAULT_FORCE_ROWS))
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_materialized_source_history_replay_aware_retention_probe(
        checkpoint_path=args.checkpoint,
        alpha005_checkpoint=args.alpha005_checkpoint,
        corpus_run_dir=args.corpus_run_dir,
        alpha_summary_csv=args.alpha_summary_csv,
        m267_replay_rows=args.m267_replay_rows,
        m183_replay_rows=args.m183_replay_rows,
        m267_corpus=args.m267_corpus,
        m183_corpus=args.m183_corpus,
        env_config_path=args.env_config,
        run_dir=args.run_dir,
        device=args.device,
        train_folds=args.train_folds,
        eval_fold=args.eval_fold,
        steps=args.steps,
        lr=args.lr,
        retention_coef=args.retention_coef,
        retention_max_normal_margin=args.retention_max_normal_margin,
        force_rows=set(args.force_rows),
        max_continuation_steps=args.max_continuation_steps,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
