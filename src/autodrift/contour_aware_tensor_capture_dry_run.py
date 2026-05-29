"""Four-row tensor-capture dry run for contour-aware policy targets."""

from __future__ import annotations

import argparse
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_terminal_boundary_history_interventions import AnchorReplayState, replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_policy_target_traceability_preflight import SOURCE_RUN_DIRS
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.history_pairability_source_miner import build_pairability_anchor_candidates, pairability_source_specs
from autodrift.source_diverse_flip_anchor_history_interventions import DonorPair, _inject_donor_response
from autodrift.temporal_active_set_anchor_sensitivity_miner import AnchorCandidate
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


DEFAULT_CANDIDATE_RUN_DIR = Path("runs/m1615_contour_aware_candidate_corpus")
DEFAULT_REPLAY_RUN_DIR = Path("runs/m1609_diagnostic_complete_bounded_replay")
DEFAULT_RUN_DIR = Path("runs/m1626_contour_aware_tensor_capture_dry_run")
DRY_RUN_POSITIVE_IDS = (
    "m1592_clean_repair::selected-0000|left_target",
    "m1595_balanced_repair::selected-0000|left_target",
)
DRY_RUN_DIAGNOSTIC_IDS = (
    "m1588_selector::selected-0020|left_target",
    "m1595_balanced_repair::selected-0004|left_target",
)
REQUIRED_VARIANTS = (
    "normal",
    "wrong_history_hidden",
    "donor_response_action_plus_hidden",
)
FORBIDDEN_GUARDRAILS = {
    "full_target_corpus_materialized": False,
    "loss_constructed": False,
    "objective_constructed": False,
    "training_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


@dataclass(frozen=True)
class CapturedTensorRow:
    """One captured target row plus policy-side tensors."""

    metadata: dict[str, Any]
    observation: np.ndarray
    correct_hidden: np.ndarray
    wrong_hidden: np.ndarray
    preferred_action: np.ndarray
    wrong_history_action: np.ndarray
    donor_plus_hidden_action: np.ndarray


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _float(value: Any) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return output if math.isfinite(output) else float("nan")


def _action_from_row(row: Mapping[str, Any] | None) -> np.ndarray | None:
    if row is None:
        return None
    try:
        return np.asarray(
            [
                float(row.get("first_action_steer", "")),
                float(row.get("first_action_throttle", "")),
                float(row.get("first_action_brake", "")),
            ],
            dtype=np.float32,
        )
    except (TypeError, ValueError):
        return None


def _action_l2(left: np.ndarray, right: np.ndarray | None) -> float:
    if right is None:
        return float("nan")
    return float(np.linalg.norm(np.asarray(left, dtype=np.float64) - np.asarray(right, dtype=np.float64)))


def _tensor_from_hidden(hidden: torch.Tensor | None) -> np.ndarray | None:
    if hidden is None:
        return None
    return hidden.detach().cpu().numpy().astype(np.float32, copy=True).reshape(-1)


def _predict_action(model: Any, observation: np.ndarray, hidden: np.ndarray) -> np.ndarray:
    device = next(model.parameters()).device
    hidden_t = torch.as_tensor(hidden, dtype=torch.float32, device=device).reshape(1, -1)
    action, _, _, _ = model.act_recurrent(np.asarray(observation, dtype=np.float32), hidden_t, deterministic=True)
    return np.asarray(action, dtype=np.float32).reshape(3)


def _source_dir(source_run: str) -> Path | None:
    return SOURCE_RUN_DIRS.get(source_run)


def _rows_by_id(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("pair_id", "")): dict(row) for row in rows}


def _select_rows(
    positive_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    positive_by_id = _rows_by_id(positive_rows)
    diagnostic_by_id = _rows_by_id(diagnostic_rows)
    selected: list[dict[str, Any]] = []
    for pair_id in DRY_RUN_POSITIVE_IDS:
        row = dict(positive_by_id[pair_id])
        row["corpus_role"] = POSITIVE_ROLE
        row["used_as_positive"] = True
        row["role_weight"] = 1.0
        selected.append(row)
    for pair_id in DRY_RUN_DIAGNOSTIC_IDS:
        row = dict(diagnostic_by_id[pair_id])
        row["corpus_role"] = DIAGNOSTIC_ROLE
        row["used_as_positive"] = False
        row["role_weight"] = 0.0
        selected.append(row)
    return selected


def _variant_index(intervention_rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("pair_id", "")), str(row.get("variant", ""))): dict(row)
        for row in intervention_rows
    }


def _pair_from_replay_row(row: Mapping[str, Any]) -> DonorPair:
    return DonorPair(
        pair_id=str(row.get("pair_id", "")),
        target_anchor_id=str(row.get("target_anchor_id", "")),
        donor_anchor_id=str(row.get("donor_anchor_id", "")),
        target_source_family=str(row.get("target_source_family", "")),
        donor_source_family=str(row.get("donor_source_family", "")),
        target_anchor_window=str(row.get("target_anchor_window", "")),
        donor_anchor_window=str(row.get("donor_anchor_window", "")),
        target_anchor_step=int(float(row.get("target_anchor_step") or 0)),
        donor_anchor_step=int(float(row.get("donor_anchor_step") or 0)),
        same_window=_truthy(row.get("same_window", False)),
        step_distance=int(float(row.get("step_distance") or 0)),
        contrasting_normal_outcome=_truthy(row.get("contrasting_normal_outcome", False)),
        diagnostic_late_reveal=_truthy(row.get("diagnostic_late_reveal", False)),
        donor_rank=int(float(row.get("donor_rank") or 0)),
    )


def _replay_anchors_for_pairs(
    pairs: Sequence[DonorPair],
    *,
    checkpoint: Path | str,
    seed: int,
    seed_count: int,
    max_source_specs: int,
    max_anchor_candidates: int,
    device: str,
) -> tuple[Any, dict[str, AnchorReplayState]]:
    specs = pairability_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    candidates = build_pairability_anchor_candidates(specs, max_anchors=max_anchor_candidates)
    specs_by_id = {str(spec.artifact_row.calibration_id): spec for spec in specs}
    candidates_by_id: dict[str, AnchorCandidate] = {candidate.anchor_id: candidate for candidate in candidates}
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    needed_anchor_ids = {pair.target_anchor_id for pair in pairs} | {pair.donor_anchor_id for pair in pairs}
    replays: dict[str, AnchorReplayState] = {}
    for anchor_id in sorted(needed_anchor_ids):
        candidate = candidates_by_id.get(anchor_id)
        if candidate is None:
            continue
        spec = specs_by_id.get(candidate.calibration_id)
        if spec is None:
            continue
        replays[anchor_id] = replay_to_anchor(
            pair_id=anchor_id,
            side="anchor",
            spec=spec,
            anchor_step=int(candidate.anchor_step),
            model=model,
        )
    return model, replays


def capture_target_tensors(
    *,
    selected_rows: Sequence[Mapping[str, Any]],
    replay_rows_by_id: Mapping[str, Mapping[str, Any]],
    intervention_rows_by_pair_variant: Mapping[tuple[str, str], Mapping[str, Any]],
    checkpoint: Path | str,
    seed: int = 1901,
    seed_count: int = 6,
    max_source_specs: int = 480,
    max_anchor_candidates: int = 640,
    device: str = "cpu",
) -> tuple[list[CapturedTensorRow], list[dict[str, Any]], list[dict[str, Any]]]:
    """Capture target tensors for the selected dry-run rows."""

    pairs: list[DonorPair] = []
    missing_rows: list[dict[str, Any]] = []
    for row in selected_rows:
        pair_id = str(row.get("pair_id", ""))
        replay_row = replay_rows_by_id.get(pair_id)
        if replay_row is None:
            missing_rows.append({"pair_id": pair_id, "missing_reasons": "replay_pair_missing"})
            continue
        pairs.append(_pair_from_replay_row(replay_row))

    model, replays = _replay_anchors_for_pairs(
        pairs,
        checkpoint=checkpoint,
        seed=seed,
        seed_count=seed_count,
        max_source_specs=max_source_specs,
        max_anchor_candidates=max_anchor_candidates,
        device=device,
    )
    pair_by_id = {pair.pair_id: pair for pair in pairs}
    captured: list[CapturedTensorRow] = []
    trace_rows: list[dict[str, Any]] = []
    for tensor_index, row in enumerate(selected_rows):
        pair_id = str(row.get("pair_id", ""))
        pair = pair_by_id.get(pair_id)
        replay_row = replay_rows_by_id.get(pair_id)
        reasons: list[str] = []
        variant_rows = {
            variant: intervention_rows_by_pair_variant.get((pair_id, variant))
            for variant in REQUIRED_VARIANTS
        }
        for variant, variant_row in variant_rows.items():
            if variant_row is None:
                reasons.append(f"{variant}_variant_missing")
        target = replays.get(pair.target_anchor_id) if pair is not None else None
        donor = replays.get(pair.donor_anchor_id) if pair is not None else None
        if target is None:
            reasons.append("target_anchor_replay_missing")
        elif not target.reached_anchor:
            reasons.append(f"target_anchor_replay_{target.first_failure}")
        if donor is None:
            reasons.append("donor_anchor_replay_missing")
        elif not donor.reached_anchor:
            reasons.append(f"donor_anchor_replay_{donor.first_failure}")
        if target is None or donor is None or not target.reached_anchor or not donor.reached_anchor or target.observation is None:
            missing_rows.append(
                {
                    "pair_id": pair_id,
                    "corpus_role": row.get("corpus_role", ""),
                    "source_run": row.get("source_run", ""),
                    "missing_reasons": "|".join(reasons) if reasons else "capture_unavailable",
                }
            )
            continue
        observation = np.asarray(target.observation, dtype=np.float32).reshape(-1)
        correct_hidden = _tensor_from_hidden(target.hidden)
        wrong_hidden = _tensor_from_hidden(donor.hidden)
        if observation.shape != (HUMAN_VIEW_OBS_DIM,):
            reasons.append(f"observation_shape_{observation.shape}")
        if correct_hidden is None:
            reasons.append("correct_hidden_missing")
        if wrong_hidden is None:
            reasons.append("wrong_hidden_missing")
        if correct_hidden is None or wrong_hidden is None or reasons:
            missing_rows.append(
                {
                    "pair_id": pair_id,
                    "corpus_role": row.get("corpus_role", ""),
                    "source_run": row.get("source_run", ""),
                    "missing_reasons": "|".join(reasons) if reasons else "capture_unavailable",
                }
            )
            continue
        donor_plus_observation = _inject_donor_response(observation, donor)
        preferred_action = _predict_action(model, observation, correct_hidden)
        wrong_history_action = _predict_action(model, observation, wrong_hidden)
        donor_plus_hidden_action = _predict_action(model, donor_plus_observation, wrong_hidden)
        source_run = str(row.get("source_run", ""))
        source_dir = _source_dir(source_run)
        role = str(row.get("corpus_role", ""))
        metadata = {
            "target_id": pair_id,
            "pair_id": pair_id,
            "corpus_role": role,
            "source_run": source_run,
            "source_run_dir": str(source_dir) if source_dir is not None else "",
            "source_edge": str(row.get("source_edge", "")),
            "target_anchor_id": str(row.get("target_anchor_id", "")),
            "donor_anchor_id": str(row.get("donor_anchor_id", "")),
            "selected_pair_id": str(row.get("selected_pair_id", "")),
            "original_pair_id": str(row.get("original_pair_id", "")),
            "normal_variant_found": variant_rows["normal"] is not None,
            "wrong_history_variant_found": variant_rows["wrong_history_hidden"] is not None,
            "donor_plus_hidden_variant_found": variant_rows["donor_response_action_plus_hidden"] is not None,
            "tensor_index": tensor_index,
            "used_as_positive": bool(row.get("used_as_positive", False)),
            "role_weight": _float(row.get("role_weight", 0.0)),
            "public_proof_artifact": True,
            "training_ready": False,
            "target_replay_status": "ok",
            "donor_replay_status": "ok",
            "observation_dim": int(observation.shape[0]),
            "hidden_dim": int(correct_hidden.shape[0]),
            "target_hidden_norm": float(np.linalg.norm(correct_hidden.astype(np.float64))),
            "donor_hidden_norm": float(np.linalg.norm(wrong_hidden.astype(np.float64))),
            "target_donor_hidden_l2": float(np.linalg.norm(correct_hidden.astype(np.float64) - wrong_hidden.astype(np.float64))),
            "target_donor_response_action_l2": float(
                np.linalg.norm(
                    np.asarray(target.response_action_frame, dtype=np.float64)
                    - np.asarray(donor.response_action_frame, dtype=np.float64)
                )
            )
            if target.response_action_frame is not None and donor.response_action_frame is not None
            else float("nan"),
            "preferred_action_steer": float(preferred_action[0]),
            "preferred_action_throttle": float(preferred_action[1]),
            "preferred_action_brake": float(preferred_action[2]),
            "wrong_history_action_steer": float(wrong_history_action[0]),
            "wrong_history_action_throttle": float(wrong_history_action[1]),
            "wrong_history_action_brake": float(wrong_history_action[2]),
            "donor_plus_hidden_action_steer": float(donor_plus_hidden_action[0]),
            "donor_plus_hidden_action_throttle": float(donor_plus_hidden_action[1]),
            "donor_plus_hidden_action_brake": float(donor_plus_hidden_action[2]),
            "source_preferred_action_l2": _action_l2(preferred_action, _action_from_row(variant_rows["normal"])),
            "source_wrong_history_action_l2": _action_l2(
                wrong_history_action,
                _action_from_row(variant_rows["wrong_history_hidden"]),
            ),
            "source_donor_plus_hidden_action_l2": _action_l2(
                donor_plus_hidden_action,
                _action_from_row(variant_rows["donor_response_action_plus_hidden"]),
            ),
        }
        if replay_row is not None:
            metadata["replay_pair_match"] = True
            metadata["replay_rule_bucket"] = str(replay_row.get("rule_bucket", ""))
            metadata["replay_rule_reason"] = str(replay_row.get("rule_reason", ""))
        captured.append(
            CapturedTensorRow(
                metadata=metadata,
                observation=observation,
                correct_hidden=correct_hidden,
                wrong_hidden=wrong_hidden,
                preferred_action=preferred_action,
                wrong_history_action=wrong_history_action,
                donor_plus_hidden_action=donor_plus_hidden_action,
            )
        )
        for variant, action in (
            ("normal", preferred_action),
            ("wrong_history_hidden", wrong_history_action),
            ("donor_response_action_plus_hidden", donor_plus_hidden_action),
        ):
            source_action = _action_from_row(variant_rows[variant])
            trace_rows.append(
                {
                    "pair_id": pair_id,
                    "corpus_role": role,
                    "variant": variant,
                    "variant_found": variant_rows[variant] is not None,
                    "capture_status": "ok",
                    "captured_action_steer": float(action[0]),
                    "captured_action_throttle": float(action[1]),
                    "captured_action_brake": float(action[2]),
                    "source_action_l2": _action_l2(action, source_action),
                }
            )
    return captured, trace_rows, missing_rows


def _stack(rows: Sequence[CapturedTensorRow], attr: str) -> np.ndarray:
    return np.stack([getattr(row, attr) for row in rows], axis=0).astype(np.float32)


def _shape_rows(arrays: Mapping[str, np.ndarray]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for name, array in arrays.items():
        output.append(
            {
                "array": name,
                "dtype": str(array.dtype),
                "shape": "x".join(str(dim) for dim in array.shape),
                "finite": bool(np.all(np.isfinite(array))),
            }
        )
    return output


def _all_tensor_values_finite(arrays: Mapping[str, np.ndarray]) -> bool:
    return all(bool(np.all(np.isfinite(array))) for array in arrays.values())


def _empty_arrays() -> dict[str, np.ndarray]:
    return {
        "observation": np.zeros((0, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
        "correct_hidden": np.zeros((0, 0), dtype=np.float32),
        "wrong_hidden": np.zeros((0, 0), dtype=np.float32),
        "preferred_action": np.zeros((0, 3), dtype=np.float32),
        "wrong_history_action": np.zeros((0, 3), dtype=np.float32),
        "donor_plus_hidden_action": np.zeros((0, 3), dtype=np.float32),
    }


def _arrays_from_captured(rows: Sequence[CapturedTensorRow]) -> dict[str, np.ndarray]:
    if not rows:
        return _empty_arrays()
    return {
        "observation": _stack(rows, "observation"),
        "correct_hidden": _stack(rows, "correct_hidden"),
        "wrong_hidden": _stack(rows, "wrong_hidden"),
        "preferred_action": _stack(rows, "preferred_action"),
        "wrong_history_action": _stack(rows, "wrong_history_action"),
        "donor_plus_hidden_action": _stack(rows, "donor_plus_hidden_action"),
    }


def _guardrail_summary_rows() -> list[dict[str, Any]]:
    return [{"guardrail": key, "violated": value, "value": value} for key, value in FORBIDDEN_GUARDRAILS.items()]


CaptureFunction = Callable[
    [Sequence[Mapping[str, Any]], Mapping[str, Mapping[str, Any]], Mapping[tuple[str, str], Mapping[str, Any]], Path, str],
    tuple[list[CapturedTensorRow], list[dict[str, Any]], list[dict[str, Any]]],
]


def run_contour_aware_tensor_capture_dry_run(
    *,
    candidate_run_dir: Path | str,
    replay_run_dir: Path | str,
    checkpoint: Path | str,
    run_dir: Path | str,
    seed: int = 1901,
    seed_count: int = 6,
    max_source_specs: int = 480,
    max_anchor_candidates: int = 640,
    device: str = "cpu",
    capture_fn: CaptureFunction | None = None,
) -> dict[str, Any]:
    """Run the M1626 four-row tensor-capture dry run."""

    candidate_dir = Path(candidate_run_dir)
    replay_dir = Path(replay_run_dir)
    checkpoint_path = Path(checkpoint)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    checksum_before = _sha256(checkpoint_path)

    positive_rows = read_csv_rows(candidate_dir / "positive_candidate_rows.csv")
    diagnostic_rows = read_csv_rows(candidate_dir / "diagnostic_guardrail_rows.csv")
    selected_rows = _select_rows(positive_rows, diagnostic_rows)
    replay_rows = read_csv_rows(replay_dir / "replay_pair_rows.csv")
    intervention_rows = read_csv_rows(replay_dir / "intervention_rows.csv")
    replay_rows_by_id = _rows_by_id(replay_rows)
    variants_by_pair = _variant_index(intervention_rows)

    if capture_fn is None:
        captured, trace_rows, missing_rows = capture_target_tensors(
            selected_rows=selected_rows,
            replay_rows_by_id=replay_rows_by_id,
            intervention_rows_by_pair_variant=variants_by_pair,
            checkpoint=checkpoint_path,
            seed=seed,
            seed_count=seed_count,
            max_source_specs=max_source_specs,
            max_anchor_candidates=max_anchor_candidates,
            device=device,
        )
    else:
        captured, trace_rows, missing_rows = capture_fn(
            selected_rows,
            replay_rows_by_id,
            variants_by_pair,
            checkpoint_path,
            device,
        )

    arrays = _arrays_from_captured(captured)
    checksum_after = _sha256(checkpoint_path)
    checkpoint_weights_mutated = checksum_before != checksum_after
    captured_metadata = [row.metadata for row in captured]
    positive_capture_count = sum(str(row.get("corpus_role", "")) == POSITIVE_ROLE for row in captured_metadata)
    diagnostic_capture_count = sum(str(row.get("corpus_role", "")) == DIAGNOSTIC_ROLE for row in captured_metadata)
    diagnostic_rows_used_as_positive = any(
        str(row.get("corpus_role", "")) == DIAGNOSTIC_ROLE
        and (bool(row.get("used_as_positive", False)) or _float(row.get("role_weight", 0.0)) != 0.0)
        for row in captured_metadata
    )
    normal_variant_match_count = sum(bool(row.get("normal_variant_found", False)) for row in captured_metadata)
    wrong_history_variant_match_count = sum(bool(row.get("wrong_history_variant_found", False)) for row in captured_metadata)
    donor_plus_hidden_variant_match_count = sum(bool(row.get("donor_plus_hidden_variant_found", False)) for row in captured_metadata)
    hidden_dim = int(arrays["correct_hidden"].shape[1]) if arrays["correct_hidden"].ndim == 2 else 0
    observation_shape = list(arrays["observation"].shape)
    preferred_action_shape = list(arrays["preferred_action"].shape)
    wrong_history_action_shape = list(arrays["wrong_history_action"].shape)
    donor_plus_hidden_action_shape = list(arrays["donor_plus_hidden_action"].shape)
    all_tensor_values_finite = _all_tensor_values_finite(arrays)
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))

    summary = {
        "result_class": "contour_aware_tensor_capture_dry_run",
        "candidate_run_dir": str(candidate_dir),
        "replay_run_dir": str(replay_dir),
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256_before": checksum_before,
        "checkpoint_sha256_after": checksum_after,
        "checkpoint_weights_mutated": bool(checkpoint_weights_mutated),
        "dry_run_row_count": len(captured),
        "positive_capture_count": int(positive_capture_count),
        "diagnostic_capture_count": int(diagnostic_capture_count),
        "normal_variant_match_count": int(normal_variant_match_count),
        "wrong_history_variant_match_count": int(wrong_history_variant_match_count),
        "donor_plus_hidden_variant_match_count": int(donor_plus_hidden_variant_match_count),
        "missing_capture_row_count": len(missing_rows),
        "observation_shape": observation_shape,
        "preferred_action_shape": preferred_action_shape,
        "wrong_history_action_shape": wrong_history_action_shape,
        "donor_plus_hidden_action_shape": donor_plus_hidden_action_shape,
        "hidden_dim": hidden_dim,
        "correct_hidden_shape_ok": list(arrays["correct_hidden"].shape) == [4, hidden_dim] and hidden_dim > 0,
        "wrong_hidden_shape_ok": list(arrays["wrong_hidden"].shape) == [4, hidden_dim] and hidden_dim > 0,
        "all_tensor_values_finite": bool(all_tensor_values_finite),
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "guardrail_violation_count": int(guardrail_violation_count),
        "dry_run_tensor_capture_written": len(captured) == 4,
        "training_ready": False,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["dry_run_row_count"]) == 4
        and int(summary["positive_capture_count"]) == 2
        and int(summary["diagnostic_capture_count"]) == 2
        and int(summary["normal_variant_match_count"]) == 4
        and int(summary["wrong_history_variant_match_count"]) == 4
        and int(summary["donor_plus_hidden_variant_match_count"]) == 4
        and list(summary["observation_shape"]) == [4, HUMAN_VIEW_OBS_DIM]
        and list(summary["preferred_action_shape"]) == [4, 3]
        and list(summary["wrong_history_action_shape"]) == [4, 3]
        and list(summary["donor_plus_hidden_action_shape"]) == [4, 3]
        and int(summary["hidden_dim"]) > 0
        and bool(summary["correct_hidden_shape_ok"])
        and bool(summary["wrong_hidden_shape_ok"])
        and bool(summary["all_tensor_values_finite"])
        and not bool(summary["diagnostic_rows_used_as_positive"])
        and not bool(summary["full_target_corpus_materialized"])
        and not bool(summary["loss_constructed"])
        and not bool(summary["objective_constructed"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
        and not bool(summary["checkpoint_weights_mutated"])
        and int(summary["guardrail_violation_count"]) == 0
    )
    if len(missing_rows) > 0:
        null_class = "tensor_capture_missing_rows"
    elif list(summary["observation_shape"]) != [4, HUMAN_VIEW_OBS_DIM]:
        null_class = "canonical_observation_shape_failure"
    elif not bool(summary["correct_hidden_shape_ok"]) or not bool(summary["wrong_hidden_shape_ok"]):
        null_class = "hidden_shape_failure"
    elif not bool(summary["all_tensor_values_finite"]):
        null_class = "nonfinite_tensor_failure"
    elif bool(summary["diagnostic_rows_used_as_positive"]):
        null_class = "diagnostic_positive_leakage"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_tensor_capture_dry_run_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class

    write_csv_rows(output / "captured_target_rows.csv", captured_metadata)
    write_csv_rows(output / "capture_traceability_rows.csv", trace_rows)
    write_csv_rows(
        output / "missing_capture_rows.csv",
        missing_rows,
        fieldnames=["pair_id", "corpus_role", "source_run", "missing_reasons"],
    )
    write_csv_rows(output / "shape_summary.csv", _shape_rows(arrays))
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_summary_rows())
    if len(captured) == 4 and not missing_rows:
        np.savez_compressed(output / "captured_targets.npz", **arrays)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run four-row contour-aware tensor-capture dry run.")
    parser.add_argument("--candidate-run-dir", type=Path, default=DEFAULT_CANDIDATE_RUN_DIR)
    parser.add_argument("--replay-run-dir", type=Path, default=DEFAULT_REPLAY_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--seed", type=int, default=1901)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=480)
    parser.add_argument("--max-anchor-candidates", type=int, default=640)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_contour_aware_tensor_capture_dry_run(
        candidate_run_dir=args.candidate_run_dir,
        replay_run_dir=args.replay_run_dir,
        checkpoint=args.checkpoint,
        run_dir=args.run_dir,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchor_candidates=int(args.max_anchor_candidates),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"dry_run_row_count={summary['dry_run_row_count']}")
    print(f"observation_shape={summary['observation_shape']}")
    print(f"hidden_dim={summary['hidden_dim']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
