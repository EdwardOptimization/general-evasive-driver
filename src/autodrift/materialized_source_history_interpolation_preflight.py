"""Exact plus replay preflight for materialized source-history interpolation."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.candidate_b_temporal_safe_projection_probe import interpolate_full_state
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.materialized_source_history_objective_evaluator import (
    DEFAULT_CORRECT_MARGIN,
    DEFAULT_WRONG_COEF,
    DEFAULT_WRONG_MARGIN,
    evaluate_materialized_source_history_objective,
)
from autodrift.materialized_source_history_pair_group_metrics import run_pair_group_metrics
from autodrift.materialized_source_history_pair_group_update import (
    ALLOWED_PARAMETER_NAMES,
    _fold_group_min_mean,
    _state_delta,
)
from autodrift.outcome_intervention_optimize import save_checkpoint_like
from autodrift.source_history_policy_gate import _checkpoint_contract
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_ALPHAS = "0.005,0.01,0.02,0.05,0.1,0.2"
DEFAULT_BASE_CHECKPOINT = Path("runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt")
DEFAULT_RAW_CHECKPOINT = Path("runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt")
DEFAULT_CORPUS_RUN_DIR = Path("runs/m1336_materialized_source_history_objective_corpus_export")
DEFAULT_M267_M264_CORPUS = Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")
DEFAULT_M183_M170_CORPUS = Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")
DEFAULT_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_RUN_DIR = Path("runs/m1352_materialized_source_history_interpolation_preflight")
BASE_POLICY_LABEL = "m1154_base"
CANDIDATE_POLICY_PREFIX = "m1352_alpha"


def parse_alphas(text: str) -> tuple[float, ...]:
    values = tuple(float(item.strip()) for item in str(text).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one alpha")
    if any(value <= 0.0 or value > 1.0 for value in values):
        raise argparse.ArgumentTypeError("candidate alphas must be in (0, 1]")
    if len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("candidate alphas must be unique")
    return tuple(sorted(values))


def _clone_state_dict(model: ActorCritic) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def _alpha_label(alpha: float) -> str:
    text = f"{float(alpha):g}".replace(".", "_")
    return f"{CANDIDATE_POLICY_PREFIX}_{text}"


def _config_signature(model: ActorCritic, checkpoint: dict[str, Any]) -> dict[str, Any]:
    config = checkpoint.get("config", {})
    return {
        "obs_dim": int(model.obs_dim),
        "act_dim": int(model.act_dim),
        "actor_encoder": str(getattr(model, "actor_encoder", "")),
        "actor_history_length": int(getattr(model, "actor_history_length", 1)),
        "action_sequence_horizon": int(getattr(model, "action_sequence_horizon", 1)),
        "config_actor_encoder": str(config.get("actor_encoder", "")),
    }


def _actor_inputs_changed(
    base_model: ActorCritic,
    base_checkpoint: dict[str, Any],
    candidate_model: ActorCritic,
    candidate_checkpoint: dict[str, Any],
) -> bool:
    return _config_signature(base_model, base_checkpoint) != _config_signature(candidate_model, candidate_checkpoint)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _exact_group_metrics(*, exact_dir: Path, run_dir: Path) -> dict[str, Any]:
    return run_pair_group_metrics(
        rows_path=exact_dir / "materialized_source_history_objective_rows.csv",
        run_dir=run_dir,
    )


def _eval_exact_for_checkpoint(
    *,
    checkpoint_path: Path,
    corpus_run_dir: Path,
    run_dir: Path,
    device: str,
    correct_margin: float,
    wrong_margin: float,
    wrong_coef: float,
) -> tuple[dict[str, Any], dict[str, Any], float]:
    exact_dir = run_dir / "exact"
    group_dir = run_dir / "group_metrics"
    exact = evaluate_materialized_source_history_objective(
        checkpoint_path=checkpoint_path,
        corpus_run_dir=corpus_run_dir,
        run_dir=exact_dir,
        device=device,
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )
    group = _exact_group_metrics(exact_dir=exact_dir, run_dir=group_dir)
    eval_fold_value = _fold_group_min_mean(group_dir / "fold_group_summary.csv", 4)
    return exact, group, eval_fold_value


def _make_alpha_row(
    *,
    alpha: float,
    checkpoint: Path,
    label: str,
    exact: dict[str, Any],
    group: dict[str, Any],
    eval_fold_group_min: float,
    parameter_delta: dict[str, Any],
    actor_inputs_changed: bool,
    base_exact: dict[str, Any],
    base_group: dict[str, Any],
    base_eval_fold_group_min: float,
) -> dict[str, Any]:
    combined = float(exact.get("combined_loss_mean", float("nan")))
    group_min = float(group.get("group_min_joint_margin_mean", float("nan")))
    exact_admitted = bool(
        not actor_inputs_changed
        and not bool(parameter_delta["forbidden_parameter_mutation_detected"])
        and float(parameter_delta["log_std_l2"]) == 0.0
        and bool(exact.get("exact_objective_finite", False))
        and combined < float(base_exact.get("combined_loss_mean", float("nan")))
        and group_min > float(base_group.get("group_min_joint_margin_mean", float("nan")))
        and float(eval_fold_group_min) + 1e-12 >= float(base_eval_fold_group_min)
    )
    return {
        "alpha": float(alpha),
        "label": label,
        "checkpoint": str(checkpoint),
        "exact_admitted": bool(exact_admitted),
        "actor_inputs_changed": bool(actor_inputs_changed),
        "forbidden_parameter_mutation_detected": bool(parameter_delta["forbidden_parameter_mutation_detected"]),
        "log_std_l2": float(parameter_delta["log_std_l2"]),
        "allowed_parameter_l2": float(parameter_delta["allowed_parameter_l2"]),
        "allowed_parameter_max_abs": float(parameter_delta["allowed_parameter_max_abs"]),
        "combined_loss_mean": combined,
        "combined_loss_delta_vs_base": combined - float(base_exact.get("combined_loss_mean", float("nan"))),
        "group_min_joint_margin_mean": group_min,
        "group_min_joint_margin_delta_vs_base": group_min
        - float(base_group.get("group_min_joint_margin_mean", float("nan"))),
        "eval_fold_4_group_min_joint_margin_mean": float(eval_fold_group_min),
        "eval_fold_4_group_min_joint_margin_delta_vs_base": float(eval_fold_group_min)
        - float(base_eval_fold_group_min),
        "group_one_sided_conflict_count": int(group.get("group_one_sided_conflict_count", 0)),
        "group_all_rows_both_directional_count": int(group.get("group_all_rows_both_directional_count", 0)),
        "group_both_negative_count": int(group.get("group_both_negative_count", 0)),
        "m267_m264_ran": False,
        "m267_m264_gate_pass": False,
        "m267_m264_normal_success_delta": "",
        "m267_m264_success_drop_count_delta": "",
        "m267_m264_normal_margin_mean_delta": "",
        "m267_m264_margin_gap_mean_delta": "",
        "m183_m170_ran": False,
        "m183_m170_gate_pass": False,
        "m183_m170_normal_success_delta": "",
        "m183_m170_success_drop_count_delta": "",
        "m183_m170_normal_margin_mean_delta": "",
        "m183_m170_margin_gap_mean_delta": "",
        "preflight_pass": False,
    }


def _attach_replay_result(row: dict[str, Any], *, prefix: str, summary: dict[str, Any]) -> None:
    row[f"{prefix}_ran"] = True
    row[f"{prefix}_gate_pass"] = bool(summary.get("gate_pass", False))
    row[f"{prefix}_normal_success_delta"] = float(summary.get("normal_success_delta", float("nan")))
    row[f"{prefix}_success_drop_count_delta"] = int(summary.get("success_drop_count_delta", 0))
    row[f"{prefix}_normal_margin_mean_delta"] = float(summary.get("normal_margin_mean_delta", float("nan")))
    row[f"{prefix}_margin_gap_mean_delta"] = float(summary.get("margin_gap_mean_delta", float("nan")))


def _run_replay(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    candidate_label: str,
    corpus_csv: Path,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> dict[str, Any]:
    return run_boundary_outcome_replay_gate(
        checkpoint_specs=(
            CheckpointSpec(label=BASE_POLICY_LABEL, path=base_checkpoint),
            CheckpointSpec(label=candidate_label, path=candidate_checkpoint),
        ),
        corpus_csv=corpus_csv,
        env_config_path=env_config_path,
        max_rows=0,
        max_continuation_steps=max_continuation_steps,
        baseline_policy=BASE_POLICY_LABEL,
        candidate_policy=candidate_label,
        max_normal_success_drop=0.0,
        max_normal_margin_regression=0.005,
        max_margin_gap_regression=0.001,
        max_success_drop_count_regression=0,
        device=device,
        run_dir=run_dir,
    )


def _classify_result(
    *,
    exact_candidate_count: int,
    m267_pass_count: int,
    selected_alpha: float | None,
    contract_failure: bool,
) -> str:
    if contract_failure:
        return "materialized_source_history_interpolation_preflight_contract_artifact"
    if exact_candidate_count <= 0:
        return "materialized_source_history_interpolation_preflight_no_exact_candidate"
    if m267_pass_count <= 0:
        return "materialized_source_history_interpolation_preflight_m267_proof_washout"
    if selected_alpha is None:
        return "materialized_source_history_interpolation_preflight_m183_proof_washout"
    return "materialized_source_history_interpolation_preflight_pass"


def _failure_types(result_class: str) -> list[str]:
    if result_class.endswith("_pass"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_no_exact_candidate"):
        return ["objective_overfit"]
    if result_class.endswith("_m267_proof_washout") or result_class.endswith("_m183_proof_washout"):
        return ["proof_washout"]
    return ["metric_artifact"]


def _next_blocker(result_class: str) -> str:
    if result_class.endswith("_pass"):
        return "m1353 materialized source-history interpolation replay result audit"
    if result_class.endswith("_no_exact_candidate"):
        return "m1353 materialized source-history interpolation no-exact-candidate audit"
    if result_class.endswith("_m267_proof_washout"):
        return "m1353 materialized source-history replay-aware active-set repair design"
    if result_class.endswith("_m183_proof_washout"):
        return "m1353 materialized source-history boundary-cliff repair design"
    return "m1353 materialized source-history interpolation contract audit"


def run_materialized_source_history_interpolation_preflight(
    *,
    base_checkpoint: Path,
    raw_checkpoint: Path,
    corpus_run_dir: Path,
    run_dir: Path,
    device: str = "auto",
    alphas: tuple[float, ...] = parse_alphas(DEFAULT_ALPHAS),
    m267_m264_corpus: Path = DEFAULT_M267_M264_CORPUS,
    m183_m170_corpus: Path = DEFAULT_M183_M170_CORPUS,
    env_config_path: Path = DEFAULT_ENV_CONFIG,
    max_continuation_steps: int = 60,
    correct_margin: float = DEFAULT_CORRECT_MARGIN,
    wrong_margin: float = DEFAULT_WRONG_MARGIN,
    wrong_coef: float = DEFAULT_WRONG_COEF,
) -> dict[str, Any]:
    base_checkpoint = Path(base_checkpoint)
    raw_checkpoint = Path(raw_checkpoint)
    corpus_run_dir = Path(corpus_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    resolved_device = resolve_device(device)
    base_model, base_data = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    raw_model, raw_data = load_actor_critic_checkpoint(raw_checkpoint, device=str(resolved_device))
    base_contract_ok, base_contract_reason = _checkpoint_contract(base_model, base_data)
    raw_contract_ok, raw_contract_reason = _checkpoint_contract(raw_model, raw_data)
    base_state = _clone_state_dict(base_model)
    raw_state = _clone_state_dict(raw_model)
    raw_delta = _state_delta(base_state, raw_state)
    raw_actor_inputs_changed = _actor_inputs_changed(base_model, base_data, raw_model, raw_data)

    base_exact, base_group, base_eval_fold = _eval_exact_for_checkpoint(
        checkpoint_path=base_checkpoint,
        corpus_run_dir=corpus_run_dir,
        run_dir=run_dir / "alpha_0_0",
        device=str(resolved_device),
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        wrong_coef=wrong_coef,
    )

    alpha_rows: list[dict[str, Any]] = []
    checkpoint_rows: list[dict[str, Any]] = []
    parameter_rows: list[dict[str, Any]] = []
    model = base_model
    checkpoint_dir = run_dir / "checkpoints"
    for alpha in alphas:
        state = interpolate_full_state(base_state, raw_state, alpha)
        model.load_state_dict({name: tensor.to(device=resolved_device) for name, tensor in state.items()})
        checkpoint_path = checkpoint_dir / f"alpha_{str(float(alpha)).replace('.', '_')}.pt"
        label = _alpha_label(alpha)
        save_checkpoint_like(
            model=model,
            source_checkpoint=base_data,
            path=checkpoint_path,
            metadata={
                "run_type": "materialized_source_history_interpolation_preflight",
                "base_checkpoint": str(base_checkpoint),
                "raw_checkpoint": str(raw_checkpoint),
                "alpha": float(alpha),
                "ppo_used": False,
                "promoted": False,
            },
        )
        candidate_model, candidate_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
        candidate_state = _clone_state_dict(candidate_model)
        parameter_delta = _state_delta(base_state, candidate_state)
        actor_inputs_changed = _actor_inputs_changed(base_model, base_data, candidate_model, candidate_data)
        for row in parameter_delta["per_parameter_rows"]:
            parameter_rows.append(
                {
                    "alpha": float(alpha),
                    "label": label,
                    **row,
                }
            )
        exact, group, eval_fold = _eval_exact_for_checkpoint(
            checkpoint_path=checkpoint_path,
            corpus_run_dir=corpus_run_dir,
            run_dir=run_dir / f"alpha_{str(float(alpha)).replace('.', '_')}",
            device=str(resolved_device),
            correct_margin=correct_margin,
            wrong_margin=wrong_margin,
            wrong_coef=wrong_coef,
        )
        row = _make_alpha_row(
            alpha=alpha,
            checkpoint=checkpoint_path,
            label=label,
            exact=exact,
            group=group,
            eval_fold_group_min=eval_fold,
            parameter_delta=parameter_delta,
            actor_inputs_changed=actor_inputs_changed,
            base_exact=base_exact,
            base_group=base_group,
            base_eval_fold_group_min=base_eval_fold,
        )
        alpha_rows.append(row)
        checkpoint_rows.append(
            {
                "alpha": float(alpha),
                "label": label,
                "checkpoint": str(checkpoint_path),
                "exact_admitted": bool(row["exact_admitted"]),
                "actor_inputs_changed": bool(actor_inputs_changed),
                "forbidden_parameter_mutation_detected": bool(
                    parameter_delta["forbidden_parameter_mutation_detected"]
                ),
                "log_std_l2": float(parameter_delta["log_std_l2"]),
            }
        )

    for row in alpha_rows:
        if not bool(row["exact_admitted"]):
            continue
        checkpoint_path = Path(str(row["checkpoint"]))
        label = str(row["label"])
        m267_summary = _run_replay(
            base_checkpoint=base_checkpoint,
            candidate_checkpoint=checkpoint_path,
            candidate_label=label,
            corpus_csv=Path(m267_m264_corpus),
            env_config_path=Path(env_config_path),
            device=str(resolved_device),
            run_dir=run_dir / "replay" / label / "m267_m264",
            max_continuation_steps=max_continuation_steps,
        )
        _attach_replay_result(row, prefix="m267_m264", summary=m267_summary)
        if bool(m267_summary.get("gate_pass", False)):
            m183_summary = _run_replay(
                base_checkpoint=base_checkpoint,
                candidate_checkpoint=checkpoint_path,
                candidate_label=label,
                corpus_csv=Path(m183_m170_corpus),
                env_config_path=Path(env_config_path),
                device=str(resolved_device),
                run_dir=run_dir / "replay" / label / "m183_m170",
                max_continuation_steps=max_continuation_steps,
            )
            _attach_replay_result(row, prefix="m183_m170", summary=m183_summary)
            row["preflight_pass"] = bool(m183_summary.get("gate_pass", False))

    selected_rows = [row for row in alpha_rows if bool(row["preflight_pass"])]
    selected = max(selected_rows, key=lambda item: float(item["alpha"])) if selected_rows else None
    exact_count = sum(bool(row["exact_admitted"]) for row in alpha_rows)
    m267_pass_count = sum(bool(row["m267_m264_gate_pass"]) for row in alpha_rows)
    contract_failure = bool(
        not base_contract_ok
        or not raw_contract_ok
        or raw_actor_inputs_changed
        or bool(raw_delta["forbidden_parameter_mutation_detected"])
    )
    result_class = _classify_result(
        exact_candidate_count=exact_count,
        m267_pass_count=m267_pass_count,
        selected_alpha=None if selected is None else float(selected["alpha"]),
        contract_failure=contract_failure,
    )

    write_csv_rows(run_dir / "alpha_summary.csv", alpha_rows)
    write_csv_rows(run_dir / "candidate_checkpoints.csv", checkpoint_rows)
    write_csv_rows(run_dir / "parameter_delta_rows.csv", parameter_rows)
    summary = {
        "run_type": "materialized_source_history_interpolation_preflight",
        "result_class": result_class,
        "failure_types": _failure_types(result_class),
        "base_checkpoint": str(base_checkpoint),
        "raw_checkpoint": str(raw_checkpoint),
        "corpus_run_dir": str(corpus_run_dir),
        "device": str(resolved_device),
        "base_checkpoint_contract": base_contract_reason,
        "raw_checkpoint_contract": raw_contract_reason,
        "base_contract_ok": bool(base_contract_ok),
        "raw_contract_ok": bool(raw_contract_ok),
        "raw_actor_inputs_changed": bool(raw_actor_inputs_changed),
        "raw_forbidden_parameter_mutation_detected": bool(raw_delta["forbidden_parameter_mutation_detected"]),
        "raw_log_std_l2": float(raw_delta["log_std_l2"]),
        "alphas": [float(alpha) for alpha in alphas],
        "alpha_count": int(len(alpha_rows)),
        "exact_candidate_count": int(exact_count),
        "m267_m264_ran_count": int(sum(bool(row["m267_m264_ran"]) for row in alpha_rows)),
        "m267_m264_pass_count": int(m267_pass_count),
        "m183_m170_ran_count": int(sum(bool(row["m183_m170_ran"]) for row in alpha_rows)),
        "m183_m170_pass_count": int(sum(bool(row["m183_m170_gate_pass"]) for row in alpha_rows)),
        "selected_alpha": None if selected is None else float(selected["alpha"]),
        "selected_checkpoint": None if selected is None else str(selected["checkpoint"]),
        "preflight_pass": bool(selected is not None),
        "next_blocker": _next_blocker(result_class),
        "base_combined_loss_mean": float(base_exact.get("combined_loss_mean", float("nan"))),
        "base_group_min_joint_margin_mean": float(base_group.get("group_min_joint_margin_mean", float("nan"))),
        "base_eval_fold_4_group_min_joint_margin_mean": float(base_eval_fold),
        "m267_m264_corpus": str(m267_m264_corpus),
        "m183_m170_corpus": str(m183_m170_corpus),
        "env_config": str(env_config_path),
        "max_continuation_steps": int(max_continuation_steps),
        "training_started": False,
        "objective_update_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "labels_enter_actor_input": False,
        "alpha_summary_csv": run_dir / "alpha_summary.csv",
        "candidate_checkpoints_csv": run_dir / "candidate_checkpoints.csv",
        "parameter_delta_rows_csv": run_dir / "parameter_delta_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--raw-checkpoint", type=Path, default=DEFAULT_RAW_CHECKPOINT)
    parser.add_argument("--corpus-run-dir", type=Path, default=DEFAULT_CORPUS_RUN_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--alphas", type=parse_alphas, default=parse_alphas(DEFAULT_ALPHAS))
    parser.add_argument("--m267-m264-corpus", type=Path, default=DEFAULT_M267_M264_CORPUS)
    parser.add_argument("--m183-m170-corpus", type=Path, default=DEFAULT_M183_M170_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--correct-margin", type=float, default=DEFAULT_CORRECT_MARGIN)
    parser.add_argument("--wrong-margin", type=float, default=DEFAULT_WRONG_MARGIN)
    parser.add_argument("--wrong-coef", type=float, default=DEFAULT_WRONG_COEF)
    args = parser.parse_args()
    summary = run_materialized_source_history_interpolation_preflight(
        base_checkpoint=args.base_checkpoint,
        raw_checkpoint=args.raw_checkpoint,
        corpus_run_dir=args.corpus_run_dir,
        run_dir=args.run_dir,
        device=args.device,
        alphas=tuple(args.alphas),
        m267_m264_corpus=args.m267_m264_corpus,
        m183_m170_corpus=args.m183_m170_corpus,
        env_config_path=args.env_config,
        max_continuation_steps=args.max_continuation_steps,
        correct_margin=args.correct_margin,
        wrong_margin=args.wrong_margin,
        wrong_coef=args.wrong_coef,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
