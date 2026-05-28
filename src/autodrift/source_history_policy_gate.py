"""Eval-only policy gate for source response histories.

The gate projects M1280 source-history rows into the canonical 72-value
human-view frame, replays correct and wrong histories through a recurrent actor,
and scores preferred/rejected source-intervention actions. It does not train.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.four_wheel_dynamics import FourWheelVehicleParams
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM, HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS, ActorCritic, resolve_device


POSITIVE_BOTH_DIRECTIONAL_FRACTION = 0.60
POSITIVE_PREFERRED_HIDDEN_FRACTION = 0.60
POSITIVE_HISTORY_ACTION_L2_MEAN = 0.02


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _quantile(values: list[float], q: float) -> float:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return float("nan")
    index = (len(finite) - 1) * float(q)
    lo = int(math.floor(index))
    hi = int(math.ceil(index))
    if lo == hi:
        return finite[lo]
    return float(finite[lo] * (hi - index) + finite[hi] * (index - lo))


def project_history_frame(
    row: dict[str, Any],
    *,
    context: np.ndarray | None = None,
    params: FourWheelVehicleParams | None = None,
) -> np.ndarray:
    """Project one source-history frame into the canonical 72-value actor frame."""

    vehicle = params or FourWheelVehicleParams()
    frame = np.zeros(HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    if context is not None:
        context_arr = np.asarray(context, dtype=np.float32).reshape(-1)
        if context_arr.shape != (HUMAN_VIEW_OBS_DIM,):
            raise ValueError(f"context must have shape (72,), got {context_arr.shape}")
        frame[12:] = context_arr[12:]

    frame[0] = float(_finite_float(row.get("vx"))) / 20.0
    frame[1] = float(_finite_float(row.get("vy"))) / 12.0
    frame[2] = float(_finite_float(row.get("yaw_rate"))) / 2.5
    frame[3] = float(_finite_float(row.get("ax"))) / 15.0
    frame[4] = float(_finite_float(row.get("ay"))) / 15.0
    frame[5] = float(_finite_float(row.get("steer_state"))) / max(float(vehicle.max_steer), 1e-6)
    frame[6] = float(_finite_float(row.get("steer_rate"))) / max(float(vehicle.max_steer_rate), 1e-6)
    frame[7] = float(np.clip(_finite_float(row.get("drive_state")) / max(float(vehicle.max_drive_force), 1e-6), 0.0, 1.0))
    frame[8] = float(np.clip(_finite_float(row.get("brake_state")) / max(float(vehicle.max_brake_force), 1e-6), 0.0, 1.0))
    frame[9] = float(np.clip(_finite_float(row.get("prev_cmd_steer")), -1.0, 1.0))
    frame[10] = float(np.clip(0.5 * (_finite_float(row.get("prev_cmd_throttle")) + 1.0), 0.0, 1.0))
    frame[11] = float(np.clip(0.5 * (_finite_float(row.get("prev_cmd_brake")) + 1.0), 0.0, 1.0))
    return frame


def _history_frames_by_id(rows: list[dict[str, str]]) -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(int(float(row["history_id"])), []).append(row)
    for frames in grouped.values():
        frames.sort(key=lambda item: int(float(item["step"])))
    return grouped


def _load_intervention_observations(path: Path) -> dict[int, np.ndarray]:
    observations: dict[int, np.ndarray] = {}
    for row in _read_csv(path):
        intervention_id = int(float(row["intervention_id"]))
        values = [float(row[f"obs_{index}"]) for index in range(HUMAN_VIEW_OBS_DIM)]
        observation = np.asarray(values, dtype=np.float32)
        if observation.shape != (HUMAN_VIEW_OBS_DIM,):
            raise ValueError(f"intervention {intervention_id}: expected 72-value observation")
        observations[intervention_id] = observation
    return observations


def _load_step0_actions(path: Path) -> dict[tuple[int, str], tuple[int, np.ndarray]]:
    actions: dict[tuple[int, str], tuple[int, np.ndarray]] = {}
    for row in _read_csv(path):
        if int(float(row["step"])) != 0:
            continue
        intervention_id = int(float(row["intervention_id"]))
        role = str(row["role"])
        candidate_id = int(float(row["candidate_id"]))
        action = np.asarray(
            [
                float(row["steer"]),
                float(row["throttle"]),
                float(row["brake"]),
            ],
            dtype=np.float32,
        )
        actions[(intervention_id, role)] = (candidate_id, action)
    return actions


def _replay_hidden(
    model: ActorCritic,
    frames: list[dict[str, str]],
    *,
    device: torch.device,
    context: np.ndarray | None = None,
) -> torch.Tensor:
    hidden = model.initial_hidden(1, device)
    with torch.no_grad():
        for row in frames:
            obs = torch.as_tensor(project_history_frame(row, context=context), dtype=torch.float32, device=device).view(1, -1)
            _features, hidden = model.recurrent_features_tensor(obs, hidden)
    return hidden.detach()


def _action_scores(
    model: ActorCritic,
    observation: np.ndarray,
    hidden: torch.Tensor,
    preferred_action: np.ndarray,
    rejected_action: np.ndarray,
    *,
    device: torch.device,
) -> dict[str, float | np.ndarray]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).view(1, -1)
    preferred_t = torch.as_tensor(preferred_action, dtype=torch.float32, device=device).view(1, -1)
    rejected_t = torch.as_tensor(rejected_action, dtype=torch.float32, device=device).view(1, -1)
    with torch.no_grad():
        dist, _value, _next_hidden = model.forward_recurrent(obs_t, hidden)
        logp_preferred = dist.log_prob(preferred_t).sum(dim=-1)
        logp_rejected = dist.log_prob(rejected_t).sum(dim=-1)
        mean = dist.mean.detach().cpu().numpy().reshape(-1)
    return {
        "logp_preferred": float(logp_preferred.detach().cpu().item()),
        "logp_rejected": float(logp_rejected.detach().cpu().item()),
        "mean": mean.astype(np.float64),
    }


def _l2(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(left, dtype=np.float64) - np.asarray(right, dtype=np.float64)))


def _checkpoint_contract(model: ActorCritic, checkpoint: dict[str, Any]) -> tuple[bool, str]:
    actor_encoder = str(checkpoint.get("config", {}).get("actor_encoder", ""))
    if actor_encoder not in HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS:
        return False, f"unsupported_actor_encoder:{actor_encoder}"
    if int(model.obs_dim) != HUMAN_VIEW_OBS_DIM:
        return False, f"unsupported_obs_dim:{model.obs_dim}"
    if tuple(model.response_feature_indices) != tuple(range(12)):
        return False, "unexpected_response_feature_indices"
    if tuple(model.context_feature_indices) != tuple(range(12, HUMAN_VIEW_OBS_DIM)):
        return False, "unexpected_context_feature_indices"
    return True, "canonical_72_human_view_online_recurrent"


def run_source_history_policy_gate(
    *,
    checkpoint_path: Path,
    history_run_dir: Path,
    intervention_run_dir: Path,
    run_dir: Path,
    device: str = "auto",
) -> dict[str, Any]:
    checkpoint_path = Path(checkpoint_path)
    history_run_dir = Path(history_run_dir)
    intervention_run_dir = Path(intervention_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    resolved_device = resolve_device(device)
    model, checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    contract_ok, contract_reason = _checkpoint_contract(model, checkpoint)
    if not contract_ok:
        raise ValueError(f"checkpoint contract violation: {contract_reason}")
    model.eval()

    history_summary = read_json(history_run_dir / "summary.json")
    history_rows = _read_csv(history_run_dir / "history_frame_rows.csv")
    history_intervention_rows = _read_csv(history_run_dir / "history_intervention_rows.csv")
    wrong_history_rows = _read_csv(history_run_dir / "wrong_history_pair_rows.csv")
    observations = _load_intervention_observations(intervention_run_dir / "intervention_observations.csv")
    actions = _load_step0_actions(intervention_run_dir / "intervention_action_sequences.csv")
    frames_by_id = _history_frames_by_id(history_rows)

    valid_wrong_pairs: dict[int, dict[str, str]] = {}
    for row in wrong_history_rows:
        if _bool_text(row.get("same_pair_swap")) and _bool_text(row.get("opposite_condition_swap")):
            valid_wrong_pairs[int(float(row["history_intervention_id"]))] = row

    policy_rows: list[dict[str, Any]] = []
    projection_rows: list[dict[str, Any]] = []
    history_context_by_id: dict[int, np.ndarray] = {}
    for row in history_intervention_rows:
        history_context_by_id[int(float(row["correct_history_id"]))] = observations[int(float(row["intervention_id"]))]

    for history_id, frames in sorted(frames_by_id.items()):
        context = history_context_by_id.get(history_id)
        zero_hidden = _replay_hidden(model, frames, device=resolved_device, context=None)
        context_hidden = _replay_hidden(model, frames, device=resolved_device, context=context)
        projected = np.asarray([project_history_frame(frame) for frame in frames], dtype=np.float32)
        projection_rows.append(
            {
                "history_id": int(history_id),
                "frame_count": int(len(frames)),
                "all_projected_finite": bool(np.all(np.isfinite(projected))),
                "max_abs_response_value": float(np.max(np.abs(projected[:, :12])) if len(projected) else float("nan")),
                "drive_state_min": float(np.min(projected[:, 7]) if len(projected) else float("nan")),
                "drive_state_max": float(np.max(projected[:, 7]) if len(projected) else float("nan")),
                "brake_state_min": float(np.min(projected[:, 8]) if len(projected) else float("nan")),
                "brake_state_max": float(np.max(projected[:, 8]) if len(projected) else float("nan")),
                "prev_throttle_min": float(np.min(projected[:, 10]) if len(projected) else float("nan")),
                "prev_throttle_max": float(np.max(projected[:, 10]) if len(projected) else float("nan")),
                "prev_brake_min": float(np.min(projected[:, 11]) if len(projected) else float("nan")),
                "prev_brake_max": float(np.max(projected[:, 11]) if len(projected) else float("nan")),
                "zero_context_hidden_matches_current_context": bool(torch.allclose(zero_hidden, context_hidden, atol=1e-6, rtol=1e-6)),
            }
        )

    for row in history_intervention_rows:
        history_intervention_id = int(float(row["history_intervention_id"]))
        intervention_id = int(float(row["intervention_id"]))
        correct_history_id = int(float(row["correct_history_id"]))
        wrong_pair_row = valid_wrong_pairs.get(history_intervention_id)
        if wrong_pair_row is None:
            raise ValueError(f"invalid wrong-history pair for history_intervention_id={history_intervention_id}")
        if int(float(wrong_pair_row["correct_history_id"])) != correct_history_id:
            raise ValueError(f"correct-history mismatch for history_intervention_id={history_intervention_id}")
        wrong_history_id = int(float(wrong_pair_row["wrong_history_id"]))
        observation = observations[intervention_id]
        preferred_candidate_id, preferred_action = actions[(intervention_id, "preferred")]
        rejected_candidate_id, rejected_action = actions[(intervention_id, "rejected")]
        correct_hidden = _replay_hidden(model, frames_by_id[correct_history_id], device=resolved_device, context=None)
        wrong_hidden = _replay_hidden(model, frames_by_id[wrong_history_id], device=resolved_device, context=None)
        correct_scores = _action_scores(
            model,
            observation,
            correct_hidden,
            preferred_action,
            rejected_action,
            device=resolved_device,
        )
        wrong_scores = _action_scores(
            model,
            observation,
            wrong_hidden,
            preferred_action,
            rejected_action,
            device=resolved_device,
        )
        mean_correct = np.asarray(correct_scores["mean"], dtype=np.float64)
        mean_wrong = np.asarray(wrong_scores["mean"], dtype=np.float64)
        logp_cp = float(correct_scores["logp_preferred"])
        logp_cr = float(correct_scores["logp_rejected"])
        logp_wp = float(wrong_scores["logp_preferred"])
        logp_wr = float(wrong_scores["logp_rejected"])
        correct_preference_margin = float(logp_cp - logp_cr)
        wrong_history_preference_margin = float(logp_wr - logp_wp)
        preferred_hidden_margin = float(logp_cp - logp_wp)
        rejected_hidden_margin = float(logp_wr - logp_cr)
        history_action_l2 = _l2(mean_correct, mean_wrong)
        correct_closer = bool(_l2(mean_correct, preferred_action) < _l2(mean_correct, rejected_action))
        wrong_closer = bool(_l2(mean_wrong, rejected_action) < _l2(mean_wrong, preferred_action))
        finite = bool(
            all(
                math.isfinite(value)
                for value in (
                    logp_cp,
                    logp_cr,
                    logp_wp,
                    logp_wr,
                    correct_preference_margin,
                    wrong_history_preference_margin,
                    preferred_hidden_margin,
                    rejected_hidden_margin,
                    history_action_l2,
                )
            )
        )
        policy_rows.append(
            {
                "history_intervention_id": int(history_intervention_id),
                "intervention_id": int(intervention_id),
                "pair_id": int(float(row["pair_id"])),
                "condition": str(row["condition"]),
                "probe_template": str(row["probe_template"]),
                "correct_history_id": int(correct_history_id),
                "wrong_history_id": int(wrong_history_id),
                "preferred_candidate_id": int(preferred_candidate_id),
                "rejected_candidate_id": int(rejected_candidate_id),
                "logp_cp": logp_cp,
                "logp_cr": logp_cr,
                "logp_wp": logp_wp,
                "logp_wr": logp_wr,
                "correct_preference_margin": correct_preference_margin,
                "wrong_history_preference_margin": wrong_history_preference_margin,
                "preferred_hidden_margin": preferred_hidden_margin,
                "rejected_hidden_margin": rejected_hidden_margin,
                "history_action_l2": history_action_l2,
                "correct_closer_to_preferred": correct_closer,
                "wrong_closer_to_rejected": wrong_closer,
                "finite": finite,
            }
        )

    row_count = len(policy_rows)
    finite_row_count = sum(bool(row["finite"]) for row in policy_rows)
    correct_positive = sum(_finite_float(row["correct_preference_margin"]) > 0.0 for row in policy_rows)
    wrong_positive = sum(_finite_float(row["wrong_history_preference_margin"]) > 0.0 for row in policy_rows)
    both_directional = sum(
        _finite_float(row["correct_preference_margin"]) > 0.0
        and _finite_float(row["wrong_history_preference_margin"]) > 0.0
        for row in policy_rows
    )
    preferred_hidden_positive = sum(_finite_float(row["preferred_hidden_margin"]) > 0.0 for row in policy_rows)
    rejected_hidden_positive = sum(_finite_float(row["rejected_hidden_margin"]) > 0.0 for row in policy_rows)
    history_l2_values = [_finite_float(row["history_action_l2"]) for row in policy_rows]
    projection_valid_count = sum(
        bool(row["all_projected_finite"]) and bool(row["zero_context_hidden_matches_current_context"])
        for row in projection_rows
    )
    wrong_history_valid_count = len(valid_wrong_pairs)
    both_directional_fraction = float(both_directional / row_count) if row_count else 0.0
    preferred_hidden_margin_positive_fraction = float(preferred_hidden_positive / row_count) if row_count else 0.0
    history_action_l2_mean = float(np.mean(history_l2_values)) if history_l2_values else float("nan")
    signal_positive = bool(
        both_directional_fraction >= POSITIVE_BOTH_DIRECTIONAL_FRACTION
        and preferred_hidden_margin_positive_fraction >= POSITIVE_PREFERRED_HIDDEN_FRACTION
        and history_action_l2_mean >= POSITIVE_HISTORY_ACTION_L2_MEAN
    )
    result_class = "action_level_history_signal_positive" if signal_positive else "action_level_history_signal_weak"

    write_csv_rows(run_dir / "policy_gate_rows.csv", policy_rows)
    write_csv_rows(run_dir / "history_projection_audit.csv", projection_rows)
    summary = {
        "run_type": "source_history_policy_gate",
        "checkpoint": str(checkpoint_path),
        "checkpoint_actor_encoder": str(checkpoint.get("config", {}).get("actor_encoder", "")),
        "checkpoint_contract": contract_reason,
        "history_run_dir": str(history_run_dir),
        "intervention_run_dir": str(intervention_run_dir),
        "source_history_summary": str(history_run_dir / "summary.json"),
        "source_history_prefix_rows": int(history_summary.get("history_prefix_rows", 0)),
        "row_count": int(row_count),
        "finite_row_count": int(finite_row_count),
        "projection_rows": int(len(projection_rows)),
        "projection_valid_count": int(projection_valid_count),
        "wrong_history_valid_count": int(wrong_history_valid_count),
        "correct_preference_positive_count": int(correct_positive),
        "wrong_history_preference_positive_count": int(wrong_positive),
        "both_directional_count": int(both_directional),
        "preferred_hidden_margin_positive_count": int(preferred_hidden_positive),
        "rejected_hidden_margin_positive_count": int(rejected_hidden_positive),
        "both_directional_fraction": both_directional_fraction,
        "preferred_hidden_margin_positive_fraction": preferred_hidden_margin_positive_fraction,
        "history_action_l2_mean": history_action_l2_mean,
        "history_action_l2_min": float(min(history_l2_values)) if history_l2_values else float("nan"),
        "history_action_l2_p10": _quantile(history_l2_values, 0.10),
        "history_action_l2_median": _quantile(history_l2_values, 0.50),
        "history_action_l2_p90": _quantile(history_l2_values, 0.90),
        "result_class": result_class,
        "positive_both_directional_fraction_threshold": POSITIVE_BOTH_DIRECTIONAL_FRACTION,
        "positive_preferred_hidden_fraction_threshold": POSITIVE_PREFERRED_HIDDEN_FRACTION,
        "positive_history_action_l2_mean_threshold": POSITIVE_HISTORY_ACTION_L2_MEAN,
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "policy_gate_rows_csv": run_dir / "policy_gate_rows.csv",
        "history_projection_audit_csv": run_dir / "history_projection_audit.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the eval-only source-history policy gate.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--history-run-dir", type=Path, required=True)
    parser.add_argument("--intervention-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()
    summary = run_source_history_policy_gate(
        checkpoint_path=args.checkpoint,
        history_run_dir=args.history_run_dir,
        intervention_run_dir=args.intervention_run_dir,
        run_dir=args.run_dir,
        device=args.device,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
