"""Exact no-update evaluator for materialized source-history objective rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.materialized_source_history_objective_corpus_export import (
    GLOBAL_FRICTION_FAMILY,
    HALFSHAFT_FAMILY,
)
from autodrift.source_history_policy_gate import (
    _action_scores,
    _checkpoint_contract,
    _l2,
    _quantile,
    project_history_frame,
)
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_CORRECT_MARGIN = 0.05
DEFAULT_WRONG_MARGIN = 0.05
DEFAULT_WRONG_COEF = 1.0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _int_text(value: Any) -> int:
    return int(float(value))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _softplus(value: float) -> float:
    return float(np.logaddexp(0.0, float(value)))


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return float(np.mean(finite)) if finite else float("nan")


def _fraction(flags: list[bool]) -> float:
    return float(sum(bool(flag) for flag in flags) / len(flags)) if flags else 0.0


def _all_finite(values: list[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def _history_frames_by_id(rows: list[dict[str, str]]) -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_int_text(row["history_id"])].append(row)
    for frames in grouped.values():
        frames.sort(key=lambda item: _int_text(item["step"]))
    return dict(grouped)


def _source_pair_by_id(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    return {_int_text(row["pair_id"]): row for row in rows}


def _replay_hidden(
    model: ActorCritic,
    frames: list[dict[str, str]],
    *,
    device: torch.device,
) -> torch.Tensor:
    hidden = model.initial_hidden(1, device)
    with torch.no_grad():
        for row in frames:
            projected = project_history_frame(row)
            obs = torch.as_tensor(projected, dtype=torch.float32, device=device).view(1, -1)
            _features, hidden = model.recurrent_features_tensor(obs, hidden)
    return hidden.detach()


def _action_from_row(row: dict[str, str], prefix: str) -> np.ndarray:
    return np.asarray(
        [
            _finite_float(row[f"{prefix}_steer"]),
            _finite_float(row[f"{prefix}_throttle"]),
            _finite_float(row[f"{prefix}_brake"]),
        ],
        dtype=np.float32,
    )


def _valid_wrong_pair(row: dict[str, str]) -> bool:
    return (
        _bool_text(row.get("same_pair_swap"))
        and _bool_text(row.get("opposite_condition_swap"))
        and _bool_text(row.get("same_source_identity_swap", "true"))
    )


def _source_identity_duplicate_count(rows: list[dict[str, str]]) -> int:
    identities = [str(row.get("source_identity", "")) for row in rows]
    return int(len(identities) - len(set(identities)))


def _quarantine_rows_used(rows: list[dict[str, Any]]) -> int:
    return int(
        sum(
            str(row.get("source_family", "")) in {HALFSHAFT_FAMILY, GLOBAL_FRICTION_FAMILY}
            for row in rows
        )
    )


def _family_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_family", ""))].append(row)
    output: list[dict[str, Any]] = []
    for family, values in sorted(grouped.items()):
        both = [bool(row["both_directional"]) for row in values]
        distance_both = [bool(row["both_distance_directional"]) for row in values]
        output.append(
            {
                "source_family": family,
                "row_count": int(len(values)),
                "combined_loss_mean": _mean([float(row["combined_loss"]) for row in values]),
                "both_directional_fraction": _fraction(both),
                "both_distance_directional_fraction": _fraction(distance_both),
                "history_action_l2_mean": _mean([float(row["history_action_l2"]) for row in values]),
            }
        )
    return output


def _fold_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row.get("fold", -1))].append(row)
    output: list[dict[str, Any]] = []
    for fold, values in sorted(grouped.items()):
        families = Counter(str(row.get("source_family", "")) for row in values)
        top_count = max(families.values()) if families else 0
        output.append(
            {
                "fold": int(fold),
                "row_count": int(len(values)),
                "source_family_count": int(len(families)),
                "top_source_family": max(families, key=families.get) if families else "",
                "top_source_family_share": float(top_count / len(values)) if values else 0.0,
                "combined_loss_mean": _mean([float(row["combined_loss"]) for row in values]),
                "both_directional_fraction": _fraction([bool(row["both_directional"]) for row in values]),
                "both_distance_directional_fraction": _fraction(
                    [bool(row["both_distance_directional"]) for row in values]
                ),
            }
        )
    return output


def _projection_row(
    *,
    row: dict[str, str],
    correct_frames: list[dict[str, str]],
    wrong_frames: list[dict[str, str]],
    source_observation: np.ndarray,
) -> dict[str, Any]:
    correct_projected = np.asarray([project_history_frame(frame) for frame in correct_frames], dtype=np.float32)
    wrong_projected = np.asarray([project_history_frame(frame) for frame in wrong_frames], dtype=np.float32)
    projected = np.concatenate([correct_projected.reshape(-1), wrong_projected.reshape(-1), source_observation.reshape(-1)])
    return {
        "history_intervention_id": _int_text(row["history_intervention_id"]),
        "correct_history_id": _int_text(row["correct_history_id"]),
        "wrong_history_id": _int_text(row["wrong_history_id"]),
        "correct_frame_count": int(len(correct_frames)),
        "wrong_frame_count": int(len(wrong_frames)),
        "source_observation_context_zero": bool(np.allclose(source_observation[12:], 0.0)),
        "all_projected_finite": bool(np.all(np.isfinite(projected))),
        "max_abs_response_value": float(
            max(
                np.max(np.abs(correct_projected[:, :12])) if len(correct_projected) else 0.0,
                np.max(np.abs(wrong_projected[:, :12])) if len(wrong_projected) else 0.0,
            )
        ),
    }


def evaluate_materialized_source_history_objective(
    *,
    checkpoint_path: Path,
    corpus_run_dir: Path,
    run_dir: Path,
    device: str = "auto",
    correct_margin: float = DEFAULT_CORRECT_MARGIN,
    wrong_margin: float = DEFAULT_WRONG_MARGIN,
    wrong_coef: float = DEFAULT_WRONG_COEF,
) -> dict[str, Any]:
    checkpoint_path = Path(checkpoint_path)
    corpus_run_dir = Path(corpus_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    source_rows = _read_csv(corpus_run_dir / "active_source_pair_rows.csv")
    frame_rows = _read_csv(corpus_run_dir / "active_history_frame_rows.csv")
    intervention_rows = _read_csv(corpus_run_dir / "active_history_intervention_rows.csv")
    wrong_rows = _read_csv(corpus_run_dir / "active_wrong_history_pair_rows.csv")

    resolved_device = resolve_device(device)
    checksum_before = _sha256(checkpoint_path)
    model, checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    contract_ok, contract_reason = _checkpoint_contract(model, checkpoint)
    if not contract_ok:
        summary = {
            "run_type": "materialized_source_history_objective_evaluator",
            "result_class": "materialized_source_history_objective_evaluator_contract_failure",
            "checkpoint": str(checkpoint_path),
            "checkpoint_contract": contract_reason,
            "checkpoint_sha256_before": checksum_before,
            "checkpoint_sha256_after": checksum_before,
            "checkpoint_weights_mutated": False,
            "training_started": False,
            "ppo_used": False,
            "promoted": False,
            "private_holdout_used": False,
            "actor_input_contract_changed": False,
            "labels_enter_actor_input": False,
        }
        write_json(run_dir / "summary.json", summary)
        return summary
    model.eval()

    source_by_pair = _source_pair_by_id(source_rows)
    frames_by_id = _history_frames_by_id(frame_rows)
    wrong_by_intervention = {
        _int_text(row["history_intervention_id"]): row
        for row in wrong_rows
        if _valid_wrong_pair(row)
    }

    row_outputs: list[dict[str, Any]] = []
    projection_rows: list[dict[str, Any]] = []
    for row in intervention_rows:
        history_intervention_id = _int_text(row["history_intervention_id"])
        pair_id = _int_text(row["pair_id"])
        source_pair = source_by_pair.get(pair_id)
        wrong_row = wrong_by_intervention.get(history_intervention_id)
        if source_pair is None:
            raise ValueError(f"missing source pair for pair_id={pair_id}")
        if wrong_row is None:
            raise ValueError(f"missing valid wrong-history pair for history_intervention_id={history_intervention_id}")
        correct_history_id = _int_text(row["correct_history_id"])
        wrong_history_id = _int_text(wrong_row["wrong_history_id"])
        if _int_text(wrong_row["correct_history_id"]) != correct_history_id:
            raise ValueError(f"correct-history mismatch for history_intervention_id={history_intervention_id}")
        correct_frames = frames_by_id.get(correct_history_id, [])
        wrong_frames = frames_by_id.get(wrong_history_id, [])
        if not correct_frames:
            raise ValueError(f"missing correct frames for history_id={correct_history_id}")
        if not wrong_frames:
            raise ValueError(f"missing wrong frames for history_id={wrong_history_id}")
        if str(row.get("source_identity", "")) != str(wrong_row.get("source_identity", "")):
            raise ValueError(f"source identity mismatch for history_intervention_id={history_intervention_id}")

        source_observation = project_history_frame(correct_frames[-1])
        correct_hidden = _replay_hidden(model, correct_frames, device=resolved_device)
        wrong_hidden = _replay_hidden(model, wrong_frames, device=resolved_device)
        preferred_action = _action_from_row(row, "preferred")
        rejected_action = _action_from_row(row, "rejected")
        correct_scores = _action_scores(
            model,
            source_observation,
            correct_hidden,
            preferred_action,
            rejected_action,
            device=resolved_device,
        )
        wrong_scores = _action_scores(
            model,
            source_observation,
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
        correct_loss = _softplus(logp_cr - logp_cp + float(correct_margin))
        wrong_loss = _softplus(logp_wp - logp_wr + float(wrong_margin))
        combined_loss = float(correct_loss + float(wrong_coef) * wrong_loss)
        history_action_l2 = _l2(mean_correct, mean_wrong)
        correct_distance_to_preferred = _l2(mean_correct, preferred_action)
        correct_distance_to_rejected = _l2(mean_correct, rejected_action)
        wrong_distance_to_preferred = _l2(mean_wrong, preferred_action)
        wrong_distance_to_rejected = _l2(mean_wrong, rejected_action)
        correct_closer = bool(correct_distance_to_preferred < correct_distance_to_rejected)
        wrong_closer = bool(wrong_distance_to_rejected < wrong_distance_to_preferred)
        finite_values = [
            logp_cp,
            logp_cr,
            logp_wp,
            logp_wr,
            correct_preference_margin,
            wrong_history_preference_margin,
            preferred_hidden_margin,
            rejected_hidden_margin,
            correct_loss,
            wrong_loss,
            combined_loss,
            history_action_l2,
            correct_distance_to_preferred,
            correct_distance_to_rejected,
            wrong_distance_to_preferred,
            wrong_distance_to_rejected,
        ]
        finite = _all_finite(finite_values)
        row_outputs.append(
            {
                "history_intervention_id": int(history_intervention_id),
                "pair_id": int(pair_id),
                "source_run_id": str(row.get("source_run_id", "")),
                "source_row_id": str(row.get("source_row_id", "")),
                "original_pair_id": str(row.get("original_pair_id", "")),
                "source_identity": str(row.get("source_identity", "")),
                "source_family": str(source_pair.get("source_family", source_pair.get("fault_family_pair", ""))),
                "fold": _int_text(source_pair.get("fold", 0)),
                "condition": str(row.get("condition", "")),
                "probe_template": str(row.get("probe_template", "")),
                "correct_history_id": int(correct_history_id),
                "wrong_history_id": int(wrong_history_id),
                "preferred_candidate_id": _int_text(row.get("preferred_candidate_id", -1)),
                "rejected_candidate_id": _int_text(row.get("rejected_candidate_id", -1)),
                "preferred_steer": float(preferred_action[0]),
                "preferred_throttle": float(preferred_action[1]),
                "preferred_brake": float(preferred_action[2]),
                "rejected_steer": float(rejected_action[0]),
                "rejected_throttle": float(rejected_action[1]),
                "rejected_brake": float(rejected_action[2]),
                "logp_cp": logp_cp,
                "logp_cr": logp_cr,
                "logp_wp": logp_wp,
                "logp_wr": logp_wr,
                "correct_preference_margin": correct_preference_margin,
                "wrong_history_preference_margin": wrong_history_preference_margin,
                "preferred_hidden_margin": preferred_hidden_margin,
                "rejected_hidden_margin": rejected_hidden_margin,
                "correct_preference_loss": correct_loss,
                "wrong_history_preference_loss": wrong_loss,
                "combined_loss": combined_loss,
                "history_action_l2": history_action_l2,
                "correct_distance_to_preferred": correct_distance_to_preferred,
                "correct_distance_to_rejected": correct_distance_to_rejected,
                "wrong_distance_to_preferred": wrong_distance_to_preferred,
                "wrong_distance_to_rejected": wrong_distance_to_rejected,
                "correct_closer_to_preferred": correct_closer,
                "wrong_closer_to_rejected": wrong_closer,
                "both_directional": bool(correct_preference_margin > 0.0 and wrong_history_preference_margin > 0.0),
                "both_distance_directional": bool(correct_closer and wrong_closer),
                "finite": bool(finite),
            }
        )
        projection_rows.append(
            _projection_row(
                row=dict(row) | {"wrong_history_id": str(wrong_history_id)},
                correct_frames=correct_frames,
                wrong_frames=wrong_frames,
                source_observation=source_observation,
            )
        )

    checkpoint_after = _sha256(checkpoint_path)
    checkpoint_weights_mutated = checksum_before != checkpoint_after
    family_rows = _family_summary(row_outputs)
    fold_rows = _fold_summary(row_outputs)
    write_csv_rows(run_dir / "materialized_source_history_objective_rows.csv", row_outputs)
    write_csv_rows(run_dir / "history_projection_audit.csv", projection_rows)
    write_csv_rows(run_dir / "family_summary.csv", family_rows)
    write_csv_rows(run_dir / "fold_summary.csv", fold_rows)

    row_count = len(row_outputs)
    finite_row_count = sum(bool(row["finite"]) for row in row_outputs)
    projection_valid_count = sum(
        bool(row["all_projected_finite"]) and bool(row["source_observation_context_zero"])
        for row in projection_rows
    )
    wrong_history_valid_count = len(wrong_by_intervention)
    active_quarantine_rows_used = _quarantine_rows_used(row_outputs)
    exact_objective_finite = bool(
        finite_row_count == row_count
        and row_count > 0
        and _all_finite([float(row["combined_loss"]) for row in row_outputs])
    )
    history_action_l2_values = [float(row["history_action_l2"]) for row in row_outputs]
    both_directional_flags = [bool(row["both_directional"]) for row in row_outputs]
    both_distance_flags = [bool(row["both_distance_directional"]) for row in row_outputs]
    correct_closer_flags = [bool(row["correct_closer_to_preferred"]) for row in row_outputs]
    wrong_closer_flags = [bool(row["wrong_closer_to_rejected"]) for row in row_outputs]
    result_class = "materialized_source_history_objective_evaluator_pass"
    if checkpoint_weights_mutated:
        result_class = "materialized_source_history_objective_evaluator_mutation_failure"
    elif not exact_objective_finite:
        result_class = "materialized_source_history_objective_evaluator_nonfinite"
    elif active_quarantine_rows_used != 0:
        result_class = "materialized_source_history_objective_evaluator_join_failure"
    elif wrong_history_valid_count != row_count or projection_valid_count != row_count:
        result_class = "materialized_source_history_objective_evaluator_join_failure"

    worst_family = min(
        (float(row["both_directional_fraction"]) for row in family_rows),
        default=float("nan"),
    )
    worst_fold = min(
        (float(row["both_directional_fraction"]) for row in fold_rows),
        default=float("nan"),
    )
    summary = {
        "run_type": "materialized_source_history_objective_evaluator",
        "result_class": result_class,
        "checkpoint": str(checkpoint_path),
        "checkpoint_actor_encoder": str(checkpoint.get("config", {}).get("actor_encoder", "")),
        "checkpoint_contract": contract_reason,
        "checkpoint_sha256_before": checksum_before,
        "checkpoint_sha256_after": checkpoint_after,
        "checkpoint_weights_mutated": bool(checkpoint_weights_mutated),
        "corpus_run_dir": str(corpus_run_dir),
        "device": str(resolved_device),
        "correct_margin": float(correct_margin),
        "wrong_margin": float(wrong_margin),
        "wrong_coef": float(wrong_coef),
        "row_count": int(row_count),
        "finite_row_count": int(finite_row_count),
        "projection_valid_count": int(projection_valid_count),
        "wrong_history_valid_count": int(wrong_history_valid_count),
        "source_identity_duplicate_count": _source_identity_duplicate_count(source_rows),
        "active_quarantine_rows_used": int(active_quarantine_rows_used),
        "exact_objective_finite": bool(exact_objective_finite),
        "correct_preference_loss_mean": _mean([float(row["correct_preference_loss"]) for row in row_outputs]),
        "wrong_history_preference_loss_mean": _mean([float(row["wrong_history_preference_loss"]) for row in row_outputs]),
        "combined_loss_mean": _mean([float(row["combined_loss"]) for row in row_outputs]),
        "correct_preference_positive_fraction": _fraction(
            [float(row["correct_preference_margin"]) > 0.0 for row in row_outputs]
        ),
        "wrong_history_preference_positive_fraction": _fraction(
            [float(row["wrong_history_preference_margin"]) > 0.0 for row in row_outputs]
        ),
        "both_directional_fraction": _fraction(both_directional_flags),
        "correct_closer_to_preferred_fraction": _fraction(correct_closer_flags),
        "wrong_closer_to_rejected_fraction": _fraction(wrong_closer_flags),
        "both_distance_directional_fraction": _fraction(both_distance_flags),
        "history_action_l2_mean": _mean(history_action_l2_values),
        "history_action_l2_p10": _quantile(history_action_l2_values, 0.10),
        "history_action_l2_p50": _quantile(history_action_l2_values, 0.50),
        "history_action_l2_p90": _quantile(history_action_l2_values, 0.90),
        "family_count": int(len(family_rows)),
        "fold_count": int(len(fold_rows)),
        "worst_family_both_directional_fraction": float(worst_family),
        "worst_fold_both_directional_fraction": float(worst_fold),
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_update_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "materialized_source_history_objective_rows_csv": run_dir / "materialized_source_history_objective_rows.csv",
        "history_projection_audit_csv": run_dir / "history_projection_audit.csv",
        "family_summary_csv": run_dir / "family_summary.csv",
        "fold_summary_csv": run_dir / "fold_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--correct-margin", type=float, default=DEFAULT_CORRECT_MARGIN)
    parser.add_argument("--wrong-margin", type=float, default=DEFAULT_WRONG_MARGIN)
    parser.add_argument("--wrong-coef", type=float, default=DEFAULT_WRONG_COEF)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="materialized_source_history_objective_evaluator")
    summary = evaluate_materialized_source_history_objective(
        checkpoint_path=args.checkpoint,
        corpus_run_dir=args.corpus_run_dir,
        run_dir=run_dir,
        device=args.device,
        correct_margin=args.correct_margin,
        wrong_margin=args.wrong_margin,
        wrong_coef=args.wrong_coef,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
