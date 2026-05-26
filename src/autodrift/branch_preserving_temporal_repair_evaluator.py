"""No-update evaluator for branch-preserving temporal repair objectives."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import validate_corpus_frame
from autodrift.capability_step_temporal_sequence_objective import load_corpus
from autodrift.capability_step_temporal_sequence_update_probe import (
    clone_state_dict,
    evaluate_state_exact,
    recurrent_logp_sums,
    state_checksum,
    tensors_from_corpus,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import collect_requested_outcome_snapshots, replay_outcome_variant
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


DEFAULT_BASE_CHECKPOINT = Path("runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt")
DEFAULT_CANDIDATE_CHECKPOINTS = Path("runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/candidate_checkpoints.csv")
DEFAULT_CORPUS = Path("runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz")
DEFAULT_BASE_SUMMARY = Path("runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json")
DEFAULT_M267_CORPUS = Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")
DEFAULT_RUN_DIR = Path("runs/m1007_v4_public_base_branch_preserving_temporal_repair_evaluator")
PRIMARY_ACTIVE_ROWS = (6, 15)
SECONDARY_ACTIVE_ROWS = (11, 16)
DEFAULT_ACTIVE_ROWS = (*PRIMARY_ACTIVE_ROWS, *SECONDARY_ACTIVE_ROWS)
DEFAULT_EPSILON_LOGP = 0.005
DEFAULT_D_MIN_FRACTION = 0.75
DEFAULT_D_MIN_ABSOLUTE = 0.02


@dataclass(frozen=True)
class EvaluatedCheckpoint:
    label: str
    path: Path
    alpha: float | None = None


@dataclass(frozen=True)
class BranchExample:
    row_id: int
    target: str
    physical_pair_key: str
    weight: float
    observation: np.ndarray
    normal_hidden: torch.Tensor
    wrong_hidden: torch.Tensor
    safe_action: np.ndarray
    base_wrong_logp: float
    base_normal_action: np.ndarray
    base_wrong_action: np.ndarray
    base_first_action_distance: float
    separation_floor: float


def branch_weight_for_row(row_id: int) -> float:
    if int(row_id) in PRIMARY_ACTIVE_ROWS:
        return 4.0
    if int(row_id) in SECONDARY_ACTIVE_ROWS:
        return 2.0
    return 1.0


def separation_floor(base_first_action_distance: float, *, fraction: float, absolute: float) -> float:
    return max(float(absolute), float(fraction) * float(base_first_action_distance))


def branch_residuals(
    *,
    candidate_wrong_logp: float,
    base_wrong_logp: float,
    candidate_separation: float,
    separation_floor_value: float,
    epsilon_logp: float,
) -> tuple[float, float, float]:
    logp_delta = float(candidate_wrong_logp) - float(base_wrong_logp)
    ceiling = max(0.0, logp_delta - float(epsilon_logp)) ** 2
    separation = max(0.0, float(separation_floor_value) - float(candidate_separation)) ** 2
    return logp_delta, ceiling, separation


def load_candidate_checkpoints(path: Path) -> list[EvaluatedCheckpoint]:
    frame = pd.read_csv(path)
    missing = [column for column in ("alpha", "checkpoint") if column not in frame.columns]
    if missing:
        raise ValueError("candidate checkpoint CSV is missing columns: " + ", ".join(missing))
    candidates = [
        EvaluatedCheckpoint(
            label=f"alpha_{float(row['alpha']):g}".replace(".", "_"),
            path=Path(str(row["checkpoint"])),
            alpha=float(row["alpha"]),
        )
        for _, row in frame.iterrows()
    ]
    return sorted(candidates, key=lambda item: float(item.alpha or 0.0))


def _requests(frame: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in frame.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
        requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
    return requests


def _action_logp(
    *,
    model: ActorCritic,
    observation: np.ndarray,
    hidden: torch.Tensor,
    action: np.ndarray,
    device: torch.device,
) -> float:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.detach().to(device=device, dtype=torch.float32).reshape(1, -1)
    action_t = torch.as_tensor(action, dtype=torch.float32, device=device).unsqueeze(0)
    with torch.no_grad():
        logp, _entropy, _value = model.evaluate_actions_recurrent(obs_t, action_t, hidden_t)
    return float(logp.squeeze(0).detach().cpu().item())


def build_branch_examples(
    *,
    base_model: ActorCritic,
    m267_corpus_csv: Path,
    env_config_path: Path,
    active_rows: tuple[int, ...],
    max_continuation_steps: int,
    device: torch.device,
    epsilon_logp: float,
    d_min_fraction: float,
    d_min_absolute: float,
) -> tuple[list[BranchExample], list[dict[str, Any]]]:
    frame = pd.read_csv(m267_corpus_csv)
    validate_corpus_frame(frame)
    selected = frame[frame["row_id"].astype(int).isin({int(row_id) for row_id in active_rows})].copy()
    selected = selected.sort_values("row_id").reset_index(drop=True)
    if len(selected) != len(set(active_rows)):
        found = set(int(row_id) for row_id in selected["row_id"].tolist())
        missing = sorted(set(int(row_id) for row_id in active_rows) - found)
        raise ValueError(f"M267/M264 corpus is missing active rows: {missing}")
    env_config = load_env_config(env_config_path)
    response_dim = response_feature_dim_for_model(base_model)
    snapshots = collect_requested_outcome_snapshots(
        model=base_model,
        env_config=env_config,
        requests=_requests(selected),
        device=device,
    )
    examples: list[BranchExample] = []
    rows: list[dict[str, Any]] = []
    for _, row in selected.iterrows():
        left = snapshots[(int(row["left_seed"]), int(row["left_step"]))]
        right = snapshots[(int(row["right_seed"]), int(row["right_step"]))]
        relocated = relocate_outcome_snapshot(
            left,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        normal, _normal_actions = replay_outcome_variant(
            model=base_model,
            snapshot=relocated,
            env_config=env_config,
            variant="normal",
            response_dim=response_dim,
            variant_hidden=None,
            normal_first_action=None,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        safe_action = np.asarray(
            [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
            dtype=np.float32,
        )
        base_normal_action, _ = deterministic_action_from_hidden(
            base_model,
            relocated.observation,
            relocated.hidden,
            device,
        )
        base_wrong_action, _ = deterministic_action_from_hidden(
            base_model,
            relocated.observation,
            right.hidden,
            device,
        )
        distance = float(np.linalg.norm(base_normal_action - base_wrong_action))
        floor = separation_floor(distance, fraction=d_min_fraction, absolute=d_min_absolute)
        base_wrong_logp = _action_logp(
            model=base_model,
            observation=relocated.observation,
            hidden=right.hidden,
            action=safe_action,
            device=device,
        )
        row_id = int(row["row_id"])
        example = BranchExample(
            row_id=row_id,
            target=str(row["target"]),
            physical_pair_key=str(row["physical_pair_key"]),
            weight=branch_weight_for_row(row_id),
            observation=np.asarray(relocated.observation, dtype=np.float32).copy(),
            normal_hidden=relocated.hidden.detach().cpu().reshape(-1).clone(),
            wrong_hidden=right.hidden.detach().cpu().reshape(-1).clone(),
            safe_action=safe_action,
            base_wrong_logp=base_wrong_logp,
            base_normal_action=base_normal_action,
            base_wrong_action=base_wrong_action,
            base_first_action_distance=distance,
            separation_floor=floor,
        )
        examples.append(example)
        rows.append(
            {
                "row_id": row_id,
                "target": str(row["target"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "weight": branch_weight_for_row(row_id),
                "base_wrong_logp": base_wrong_logp,
                "base_first_action_distance": distance,
                "separation_floor": floor,
                "epsilon_logp": float(epsilon_logp),
                "safe_steer": float(safe_action[0]),
                "safe_throttle": float(safe_action[1]),
                "safe_brake": float(safe_action[2]),
                "base_wrong_steer": float(base_wrong_action[0]),
                "base_wrong_throttle": float(base_wrong_action[1]),
                "base_wrong_brake": float(base_wrong_action[2]),
            }
        )
    return examples, rows


def evaluate_branch_examples(
    *,
    model: ActorCritic,
    checkpoint: EvaluatedCheckpoint,
    examples: list[BranchExample],
    device: torch.device,
    epsilon_logp: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    weights: list[float] = []
    ceiling_values: list[float] = []
    separation_values: list[float] = []
    logp_deltas: list[float] = []
    separations: list[float] = []
    for example in examples:
        normal_action, _ = deterministic_action_from_hidden(
            model,
            example.observation,
            example.normal_hidden.to(device=device).reshape(1, -1),
            device,
        )
        wrong_action, _ = deterministic_action_from_hidden(
            model,
            example.observation,
            example.wrong_hidden.to(device=device).reshape(1, -1),
            device,
        )
        wrong_logp = _action_logp(
            model=model,
            observation=example.observation,
            hidden=example.wrong_hidden,
            action=example.safe_action,
            device=device,
        )
        candidate_separation = float(np.linalg.norm(normal_action - wrong_action))
        logp_delta, ceiling_loss, separation_loss = branch_residuals(
            candidate_wrong_logp=wrong_logp,
            base_wrong_logp=example.base_wrong_logp,
            candidate_separation=candidate_separation,
            separation_floor_value=example.separation_floor,
            epsilon_logp=epsilon_logp,
        )
        weights.append(float(example.weight))
        ceiling_values.append(float(ceiling_loss))
        separation_values.append(float(separation_loss))
        logp_deltas.append(float(logp_delta))
        separations.append(candidate_separation)
        rows.append(
            {
                "checkpoint_label": checkpoint.label,
                "alpha": "" if checkpoint.alpha is None else float(checkpoint.alpha),
                "checkpoint": str(checkpoint.path),
                "row_id": int(example.row_id),
                "target": example.target,
                "physical_pair_key": example.physical_pair_key,
                "weight": float(example.weight),
                "candidate_wrong_logp": float(wrong_logp),
                "base_wrong_logp": float(example.base_wrong_logp),
                "wrong_logp_delta": float(logp_delta),
                "branch_ceiling_loss": float(ceiling_loss),
                "candidate_first_action_distance": candidate_separation,
                "base_first_action_distance": float(example.base_first_action_distance),
                "separation_floor": float(example.separation_floor),
                "branch_separation_loss": float(separation_loss),
                "normal_steer": float(normal_action[0]),
                "normal_throttle": float(normal_action[1]),
                "normal_brake": float(normal_action[2]),
                "wrong_steer": float(wrong_action[0]),
                "wrong_throttle": float(wrong_action[1]),
                "wrong_brake": float(wrong_action[2]),
            }
        )
    weight_arr = np.asarray(weights, dtype=np.float64)
    ceiling_arr = np.asarray(ceiling_values, dtype=np.float64)
    separation_arr = np.asarray(separation_values, dtype=np.float64)
    logp_delta_arr = np.asarray(logp_deltas, dtype=np.float64)
    distance_arr = np.asarray(separations, dtype=np.float64)
    denominator = float(np.sum(weight_arr))
    if denominator <= 0.0:
        raise ValueError("branch example weights must have positive sum")
    summary = {
        "checkpoint_label": checkpoint.label,
        "alpha": "" if checkpoint.alpha is None else float(checkpoint.alpha),
        "checkpoint": checkpoint.path,
        "branch_row_count": int(len(rows)),
        "weighted_branch_ceiling_loss": float(np.sum(weight_arr * ceiling_arr) / denominator),
        "weighted_branch_separation_loss": float(np.sum(weight_arr * separation_arr) / denominator),
        "weighted_branch_total_loss": float(np.sum(weight_arr * (ceiling_arr + separation_arr)) / denominator),
        "wrong_logp_delta_mean": float(np.mean(logp_delta_arr)),
        "wrong_logp_delta_max": float(np.max(logp_delta_arr)),
        "first_action_distance_mean": float(np.mean(distance_arr)),
        "first_action_distance_min": float(np.min(distance_arr)),
        "finite_branch_metrics": bool(
            np.isfinite(ceiling_arr).all()
            and np.isfinite(separation_arr).all()
            and np.isfinite(logp_delta_arr).all()
            and np.isfinite(distance_arr).all()
        ),
    }
    return summary, rows


def _temporal_base_metrics(base_summary_path: Path) -> dict[str, float]:
    summary = read_json(base_summary_path)
    names = (
        "weighted_total_loss",
        "weighted_normal_sequence_nll",
        "weighted_temporal_preference_loss",
        "weighted_logp_gap_mean",
        "temporal_logp_gap_p10",
    )
    return {name: float(summary[name]) for name in names}


def evaluate_temporal_metrics_for_checkpoints(
    *,
    base_checkpoint: Path,
    checkpoints: list[EvaluatedCheckpoint],
    corpus_path: Path,
    base_summary_path: Path,
    device: torch.device,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> list[dict[str, Any]]:
    base_model, _ = load_actor_critic_checkpoint(base_checkpoint, device=str(device))
    base_model.eval()
    base_state = clone_state_dict(base_model)
    corpus = load_corpus(corpus_path)
    tensors = tensors_from_corpus(corpus, device)
    with torch.no_grad():
        base_normal_logp = recurrent_logp_sums(base_model, tensors, "normal_hidden").detach()
    base_metrics = _temporal_base_metrics(base_summary_path)
    rows: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        model, _ = load_actor_critic_checkpoint(checkpoint.path, device=str(device))
        state = clone_state_dict(model)
        row = evaluate_state_exact(
            model=base_model,
            state=state,
            corpus=corpus,
            tensors=tensors,
            base_normal_logp=base_normal_logp,
            base_metrics=base_metrics,
            device=device,
            alpha=checkpoint.alpha,
            candidate=checkpoint.label,
            preference_margin=preference_margin,
            lambda_pref=lambda_pref,
            lambda_anchor=lambda_anchor,
        )
        if checkpoint.alpha is None:
            row["alpha"] = ""
        row["checkpoint"] = str(checkpoint.path)
        row["checkpoint_label"] = checkpoint.label
        rows.append(row)
    _ = base_state
    return rows


def classify_branch_preserving_evaluator(
    *,
    finite_metrics: bool,
    base_branch_near_zero: bool,
    proofwashing_candidates_active: bool,
    temporal_base_reproduced: bool,
    actor_parameters_changed: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_parameters_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "branch_preserving_temporal_repair_evaluator_contract_artifact"
    if not bool(finite_metrics):
        return "branch_preserving_temporal_repair_evaluator_nonfinite"
    if not bool(temporal_base_reproduced):
        return "branch_preserving_temporal_repair_evaluator_temporal_reproduction_failed"
    if not bool(base_branch_near_zero):
        return "branch_preserving_temporal_repair_evaluator_base_branch_not_safe"
    if not bool(proofwashing_candidates_active):
        return "branch_preserving_temporal_repair_evaluator_not_sensitive"
    return "branch_preserving_temporal_repair_evaluator_pass"


def failure_types_for_result_class(result_class: str) -> list[str]:
    if result_class.endswith("_pass"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_nonfinite"):
        return ["training_instability"]
    if result_class.endswith("_not_sensitive") or result_class.endswith("_temporal_reproduction_failed"):
        return ["metric_artifact"]
    if result_class.endswith("_base_branch_not_safe"):
        return ["objective_overfit"]
    return ["metric_artifact"]


def run_branch_preserving_temporal_repair_evaluator(
    *,
    base_checkpoint: Path,
    candidate_checkpoints_csv: Path,
    corpus_path: Path,
    base_summary_path: Path,
    m267_corpus_csv: Path,
    run_dir: Path,
    device: str,
    env_config_path: Path,
    active_rows: tuple[int, ...],
    max_continuation_steps: int,
    epsilon_logp: float,
    d_min_fraction: float,
    d_min_absolute: float,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
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
        epsilon_logp=epsilon_logp,
        d_min_fraction=d_min_fraction,
        d_min_absolute=d_min_absolute,
    )
    branch_summary_rows: list[dict[str, Any]] = []
    branch_detail_rows: list[dict[str, Any]] = []
    actor_parameters_changed = False
    for checkpoint in candidates:
        model, _ = load_actor_critic_checkpoint(checkpoint.path, device=str(resolved_device))
        model.eval()
        checksum_before = state_checksum(clone_state_dict(model))
        summary, rows = evaluate_branch_examples(
            model=model,
            checkpoint=checkpoint,
            examples=examples,
            device=resolved_device,
            epsilon_logp=epsilon_logp,
        )
        checksum_after = state_checksum(clone_state_dict(model))
        summary["actor_parameters_changed"] = bool(checksum_before != checksum_after)
        actor_parameters_changed = bool(actor_parameters_changed or checksum_before != checksum_after)
        branch_summary_rows.append(summary)
        branch_detail_rows.extend(rows)
    base_checksum_after = state_checksum(clone_state_dict(base_model))
    actor_parameters_changed = bool(actor_parameters_changed or base_checksum_before != base_checksum_after)
    temporal_rows = evaluate_temporal_metrics_for_checkpoints(
        base_checkpoint=base_checkpoint,
        checkpoints=candidates,
        corpus_path=corpus_path,
        base_summary_path=base_summary_path,
        device=resolved_device,
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    base_temporal = next(row for row in temporal_rows if row["checkpoint_label"] == "m974_base")
    base_summary = _temporal_base_metrics(base_summary_path)
    temporal_base_reproduced = bool(
        abs(float(base_temporal["weighted_total_loss"]) - base_summary["weighted_total_loss"]) <= 1e-5
        and abs(float(base_temporal["weighted_normal_sequence_nll"]) - base_summary["weighted_normal_sequence_nll"]) <= 1e-5
        and abs(float(base_temporal["weighted_temporal_preference_loss"]) - base_summary["weighted_temporal_preference_loss"])
        <= 1e-5
    )
    base_branch = next(row for row in branch_summary_rows if row["checkpoint_label"] == "m974_base")
    base_branch_near_zero = bool(
        float(base_branch["weighted_branch_ceiling_loss"]) <= 1e-12
        and float(base_branch["weighted_branch_separation_loss"]) <= 1e-12
    )
    active_by_label = {
        str(row["checkpoint_label"]): float(row["weighted_branch_total_loss"]) > 1e-10
        for row in branch_summary_rows
    }
    proofwashing_candidates_active = bool(active_by_label.get("alpha_0_01", False) and active_by_label.get("alpha_0_2", False))
    finite_metrics = bool(
        all(bool(row["finite_branch_metrics"]) for row in branch_summary_rows)
        and all(bool(row["exact_gate_pass"]) or row["checkpoint_label"] == "m974_base" for row in temporal_rows)
    )
    result_class = classify_branch_preserving_evaluator(
        finite_metrics=finite_metrics,
        base_branch_near_zero=base_branch_near_zero,
        proofwashing_candidates_active=proofwashing_candidates_active,
        temporal_base_reproduced=temporal_base_reproduced,
        actor_parameters_changed=actor_parameters_changed,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "branch_examples.csv", example_rows)
    write_csv_rows(run_dir / "branch_metric_summary.csv", branch_summary_rows)
    write_csv_rows(run_dir / "branch_metric_rows.csv", branch_detail_rows)
    write_csv_rows(run_dir / "temporal_metric_summary.csv", temporal_rows)
    summary = {
        "run_type": "branch_preserving_temporal_repair_evaluator",
        "base_checkpoint": base_checkpoint,
        "candidate_checkpoints_csv": candidate_checkpoints_csv,
        "corpus": corpus_path,
        "base_summary": base_summary_path,
        "m267_corpus": m267_corpus_csv,
        "env_config": env_config_path,
        "active_rows": list(active_rows),
        "primary_active_rows": list(PRIMARY_ACTIVE_ROWS),
        "secondary_active_rows": list(SECONDARY_ACTIVE_ROWS),
        "max_continuation_steps": int(max_continuation_steps),
        "epsilon_logp": float(epsilon_logp),
        "d_min_fraction": float(d_min_fraction),
        "d_min_absolute": float(d_min_absolute),
        "preference_margin": float(preference_margin),
        "lambda_pref": float(lambda_pref),
        "lambda_anchor": float(lambda_anchor),
        "evaluated_checkpoints": [row["checkpoint_label"] for row in branch_summary_rows],
        "branch_row_count": int(len(examples)),
        "finite_metrics": bool(finite_metrics),
        "temporal_base_reproduced": bool(temporal_base_reproduced),
        "base_branch_near_zero": bool(base_branch_near_zero),
        "proofwashing_candidates_active": bool(proofwashing_candidates_active),
        "alpha_0_01_branch_active": bool(active_by_label.get("alpha_0_01", False)),
        "alpha_0_2_branch_active": bool(active_by_label.get("alpha_0_2", False)),
        "base_weighted_branch_total_loss": float(base_branch["weighted_branch_total_loss"]),
        "alpha_0_01_weighted_branch_total_loss": next(
            float(row["weighted_branch_total_loss"]) for row in branch_summary_rows if row["checkpoint_label"] == "alpha_0_01"
        ),
        "alpha_0_2_weighted_branch_total_loss": next(
            float(row["weighted_branch_total_loss"]) for row in branch_summary_rows if row["checkpoint_label"] == "alpha_0_2"
        ),
        "actor_parameters_changed": bool(actor_parameters_changed),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_result_class(result_class),
        "next_blocker": (
            "branch-preserving temporal actor_mean repair update design"
            if result_class.endswith("_pass")
            else "branch-preserving temporal evaluator audit"
        ),
        "branch_examples_csv": run_dir / "branch_examples.csv",
        "branch_metric_summary_csv": run_dir / "branch_metric_summary.csv",
        "branch_metric_rows_csv": run_dir / "branch_metric_rows.csv",
        "temporal_metric_summary_csv": run_dir / "temporal_metric_summary.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_active_rows(text: str) -> tuple[int, ...]:
    rows = tuple(int(item.strip()) for item in str(text).split(",") if item.strip())
    if not rows:
        raise argparse.ArgumentTypeError("active rows must not be empty")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate branch-preserving temporal repair terms without updating actors.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoints", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINTS)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--base-summary", type=Path, default=DEFAULT_BASE_SUMMARY)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--active-rows", type=_parse_active_rows, default=",".join(str(row) for row in DEFAULT_ACTIVE_ROWS))
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--epsilon-logp", type=float, default=DEFAULT_EPSILON_LOGP)
    parser.add_argument("--d-min-fraction", type=float, default=DEFAULT_D_MIN_FRACTION)
    parser.add_argument("--d-min-absolute", type=float, default=DEFAULT_D_MIN_ABSOLUTE)
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    args = parser.parse_args()
    summary = run_branch_preserving_temporal_repair_evaluator(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoints_csv=args.candidate_checkpoints,
        corpus_path=args.corpus,
        base_summary_path=args.base_summary,
        m267_corpus_csv=args.m267_corpus,
        run_dir=args.run_dir,
        device=args.device,
        env_config_path=args.env_config,
        active_rows=tuple(args.active_rows),
        max_continuation_steps=args.max_continuation_steps,
        epsilon_logp=args.epsilon_logp,
        d_min_fraction=args.d_min_fraction,
        d_min_absolute=args.d_min_absolute,
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
    )
    print(f"result_class={summary['result_class']}")
    print(f"base_branch_near_zero={summary['base_branch_near_zero']}")
    print(f"proofwashing_candidates_active={summary['proofwashing_candidates_active']}")
    print(f"alpha_0_01_weighted_branch_total_loss={summary['alpha_0_01_weighted_branch_total_loss']}")
    print(f"alpha_0_2_weighted_branch_total_loss={summary['alpha_0_2_weighted_branch_total_loss']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
