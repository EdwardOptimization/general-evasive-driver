"""Mine action-divergent wrong-history preferred/rejected sequence rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_smoke import freeze_actor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import (
    _finite_float,
    _hidden_array,
    parse_surface_config,
    risk_score,
    source_diversity_weights,
)
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.sequence_target_miner import parse_int_list
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device


def parse_surface_path(raw: str) -> tuple[str, Path]:
    if "=" not in str(raw):
        raise argparse.ArgumentTypeError(f"surface mapping must be SURFACE=PATH, got {raw!r}")
    surface, path = str(raw).split("=", 1)
    surface = surface.strip()
    if not surface:
        raise argparse.ArgumentTypeError(f"surface mapping has empty surface: {raw!r}")
    return surface, Path(path.strip())


def action_sequence_prefix(actions: list[np.ndarray], sequence_length: int) -> np.ndarray:
    if int(sequence_length) <= 0:
        raise ValueError("sequence_length must be positive")
    if not actions:
        raise ValueError("cannot build an action sequence from no actions")
    seq = [np.asarray(action, dtype=np.float32).reshape(3).copy() for action in actions[: int(sequence_length)]]
    while len(seq) < int(sequence_length):
        seq.append(seq[-1].copy())
    return np.asarray(seq, dtype=np.float32)


def action_sequence_distance(left: np.ndarray, right: np.ndarray) -> dict[str, float]:
    left_arr = np.asarray(left, dtype=np.float32)
    right_arr = np.asarray(right, dtype=np.float32)
    if left_arr.shape != right_arr.shape or left_arr.ndim != 2 or left_arr.shape[1] != 3:
        raise ValueError(f"expected matching (K, 3) sequences, got {left_arr.shape} and {right_arr.shape}")
    step_l2 = np.linalg.norm(left_arr.astype(np.float64) - right_arr.astype(np.float64), axis=1)
    return {
        "mean_l2": float(step_l2.mean()) if step_l2.size else 0.0,
        "max_l2": float(step_l2.max()) if step_l2.size else 0.0,
        "first_l2": float(step_l2[0]) if step_l2.size else 0.0,
    }


def rejection_reason_for_candidate(
    *,
    first_l2: float,
    sequence_mean_l2: float,
    preferred_rejected_mean_l2: float,
    margin_gap: float,
    normal_margin: float,
    wrong_margin: float,
    min_wrong_first_action_l2: float,
    min_wrong_action_sequence_mean_l2: float,
    min_preferred_rejected_action_mean_l2: float,
    min_margin_gap: float,
) -> str:
    reasons: list[str] = []
    if first_l2 < float(min_wrong_first_action_l2):
        reasons.append("wrong_first_action_l2_below_threshold")
    if sequence_mean_l2 < float(min_wrong_action_sequence_mean_l2):
        reasons.append("wrong_action_sequence_mean_l2_below_threshold")
    if preferred_rejected_mean_l2 < float(min_preferred_rejected_action_mean_l2):
        reasons.append("preferred_rejected_action_mean_l2_below_threshold")
    if not np.isfinite(margin_gap) or margin_gap < float(min_margin_gap):
        reasons.append("margin_gap_below_threshold")
    if not np.isfinite(normal_margin) or normal_margin < 0.0:
        reasons.append("normal_margin_negative_or_missing")
    if not np.isfinite(wrong_margin) or wrong_margin > normal_margin - float(min_margin_gap):
        reasons.append("wrong_margin_not_lower_than_preferred")
    return "accepted" if not reasons else ";".join(reasons)


def load_surface_pairs(surface_pairs: dict[str, Path]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for surface, path in surface_pairs.items():
        frame = pd.read_csv(path)
        if frame.empty:
            continue
        frame = frame.copy()
        frame["surface"] = surface
        frame["config"] = surface
        rows.append(frame)
    if not rows:
        return pd.DataFrame()
    combined = pd.concat(rows, ignore_index=True)
    source_keys = (
        combined["surface"].astype(str)
        + "|"
        + combined["target"].astype(str)
        + "|"
        + combined["left_seed"].astype(int).astype(str)
        + "|"
        + combined["right_seed"].astype(int).astype(str)
        + "|"
        + combined["left_step"].astype(int).astype(str)
        + "|"
        + combined["right_step"].astype(int).astype(str)
    )
    combined["source_index"] = pd.factorize(source_keys)[0].astype(int)
    combined["physical_pair_key"] = [
        f"{row.surface}:{int(row.left_seed)}:{int(row.right_seed)}"
        for row in combined.itertuples(index=False)
    ]
    return combined


def preferred_sequence_keys(preferred_sequences_csv: Path | None) -> set[tuple[str, str, int, int, int, int]]:
    if preferred_sequences_csv is None or not preferred_sequences_csv.exists():
        return set()
    frame = pd.read_csv(preferred_sequences_csv)
    required = {"surface", "target", "left_seed", "right_seed", "left_step", "right_step"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("preferred sequences missing columns: " + ", ".join(missing))
    return {
        (
            str(row.surface),
            str(row.target),
            int(row.left_seed),
            int(row.right_seed),
            int(row.left_step),
            int(row.right_step),
        )
        for row in frame.itertuples(index=False)
    }


def preferred_key_for_pair(pair: pd.Series) -> tuple[str, str, int, int, int, int]:
    return (
        str(pair["surface"]),
        str(pair["target"]),
        int(pair["left_seed"]),
        int(pair["right_seed"]),
        int(pair["left_step"]),
        int(pair["right_step"]),
    )


def snapshot_requests(pair_rows: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for row in pair_rows.itertuples(index=False):
        requests.setdefault(int(row.left_seed), set()).add(int(row.left_step))
        requests.setdefault(int(row.right_seed), set()).add(int(row.right_step))
    return requests


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot | None:
    return snapshots.get((int(seed), int(step)))


def _first_action(result: dict[str, Any]) -> np.ndarray:
    return np.asarray([result["first_steer"], result["first_throttle"], result["first_brake"]], dtype=np.float32)


def score_wrong_history_pair(
    *,
    pair: pd.Series,
    left: OutcomeSnapshot,
    right: OutcomeSnapshot,
    model: ActorCritic,
    env_config: Any,
    response_dim: int,
    sequence_lengths: tuple[int, ...],
    max_continuation_steps: int,
    min_wrong_first_action_l2: float,
    min_wrong_action_sequence_mean_l2: float,
    min_preferred_rejected_action_mean_l2: float,
    min_margin_gap: float,
    projected_preferred_keys: set[tuple[str, str, int, int, int, int]] | None,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, list[np.ndarray]]]:
    normal, normal_actions = replay_outcome_variant(
        model=model,
        snapshot=left,
        env_config=env_config,
        variant="normal",
        response_dim=response_dim,
        variant_hidden=None,
        normal_first_action=None,
        normal_actions=None,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    normal_first = _first_action(normal)
    wrong, wrong_actions = replay_outcome_variant(
        model=model,
        snapshot=left,
        env_config=env_config,
        variant="wrong_matched_history",
        response_dim=response_dim,
        variant_hidden=right.hidden,
        normal_first_action=normal_first,
        normal_actions=normal_actions,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    normal_margin = _finite_float(normal.get("min_clearance_margin"))
    wrong_margin = _finite_float(wrong.get("min_clearance_margin"))
    margin_gap = normal_margin - wrong_margin if np.isfinite(normal_margin) and np.isfinite(wrong_margin) else float("nan")
    normal_risk = risk_score(normal)
    wrong_risk = risk_score(wrong)
    risk_gap = wrong_risk - normal_risk
    first_l2 = _finite_float(wrong.get("first_action_distance"), 0.0)
    projected_preferred_available = bool(
        projected_preferred_keys is not None and preferred_key_for_pair(pair) in projected_preferred_keys
    )
    rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observation": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "preferred_action_sequence": [],
        "rejected_action_sequence": [],
        "normal_base_action_sequence": [],
        "variant_base_action_sequence": [],
    }
    for sequence_length in sequence_lengths:
        preferred_sequence = action_sequence_prefix(normal_actions, int(sequence_length))
        rejected_sequence = action_sequence_prefix(wrong_actions, int(sequence_length))
        distances = action_sequence_distance(preferred_sequence, rejected_sequence)
        accepted = bool(
            first_l2 >= float(min_wrong_first_action_l2)
            and distances["mean_l2"] >= float(min_wrong_action_sequence_mean_l2)
            and distances["mean_l2"] >= float(min_preferred_rejected_action_mean_l2)
            and np.isfinite(margin_gap)
            and margin_gap >= float(min_margin_gap)
            and np.isfinite(normal_margin)
            and normal_margin >= 0.0
            and np.isfinite(wrong_margin)
            and wrong_margin <= normal_margin - float(min_margin_gap)
        )
        rejection_reason = rejection_reason_for_candidate(
            first_l2=first_l2,
            sequence_mean_l2=distances["mean_l2"],
            preferred_rejected_mean_l2=distances["mean_l2"],
            margin_gap=margin_gap,
            normal_margin=normal_margin,
            wrong_margin=wrong_margin,
            min_wrong_first_action_l2=min_wrong_first_action_l2,
            min_wrong_action_sequence_mean_l2=min_wrong_action_sequence_mean_l2,
            min_preferred_rejected_action_mean_l2=min_preferred_rejected_action_mean_l2,
            min_margin_gap=min_margin_gap,
        )
        row = {
            "source_index": int(pair["source_index"]),
            "physical_pair_key": str(pair["physical_pair_key"]),
            "grid_name": "action_divergent_wrong_history",
            "surface": str(pair["surface"]),
            "target": str(pair["target"]),
            "variant": "wrong_matched_history",
            "split": "unassigned",
            "preferred_sequence_source": "normal_policy_base",
            "projected_preferred_sequence_available": projected_preferred_available,
            "left_seed": int(pair["left_seed"]),
            "right_seed": int(pair["right_seed"]),
            "left_step": int(pair["left_step"]),
            "right_step": int(pair["right_step"]),
            "sequence_length": int(sequence_length),
            "target_z_delta": _finite_float(pair.get("target_z_delta", float("nan"))),
            "visible_distance": _finite_float(pair.get("visible_distance", float("nan"))),
            "left_obstacle_label": str(pair.get("left_obstacle_label", "")),
            "right_obstacle_label": str(pair.get("right_obstacle_label", "")),
            "normal_success": bool(normal.get("success", False)),
            "wrong_success": bool(wrong.get("success", False)),
            "normal_collision": bool(normal.get("collision", False)),
            "wrong_collision": bool(wrong.get("collision", False)),
            "normal_terminal_reason": str(normal.get("terminal_reason", "")),
            "wrong_terminal_reason": str(wrong.get("terminal_reason", "")),
            "normal_margin": normal_margin,
            "wrong_margin": wrong_margin,
            "preferred_margin": normal_margin,
            "rejected_margin": wrong_margin,
            "normal_risk_score": normal_risk,
            "wrong_risk_score": wrong_risk,
            "preferred_risk_score": normal_risk,
            "rejected_risk_score": wrong_risk,
            "margin_gap": margin_gap,
            "risk_gap": risk_gap,
            "wrong_first_action_l2": first_l2,
            "wrong_action_sequence_mean_l2": distances["mean_l2"],
            "wrong_action_sequence_max_l2": distances["max_l2"],
            "preferred_vs_rejected_action_mean_l2": distances["mean_l2"],
            "preferred_vs_rejected_action_max_l2": distances["max_l2"],
            "accepted": accepted,
            "rejection_reason": rejection_reason,
        }
        rows.append(row)
        if accepted:
            corpus["observation"].append(np.asarray(left.observation, dtype=np.float32).copy())
            corpus["normal_hidden"].append(_hidden_array(left.hidden))
            corpus["variant_hidden"].append(_hidden_array(right.hidden))
            corpus["preferred_action_sequence"].append(preferred_sequence)
            corpus["rejected_action_sequence"].append(rejected_sequence)
            corpus["normal_base_action_sequence"].append(preferred_sequence)
            corpus["variant_base_action_sequence"].append(rejected_sequence)
    return rows, corpus


def _assign_splits(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    source_ids = sorted({int(row["source_index"]) for row in rows})
    heldout = {source for index, source in enumerate(source_ids) if index % 5 == 0}
    if len(source_ids) > 1 and len(heldout) == len(source_ids):
        heldout = {source_ids[-1]}
    for row in rows:
        row["split"] = "source_holdout_validation" if int(row["source_index"]) in heldout else "train"


def _pad_sequences(sequences: list[np.ndarray], max_len: int) -> tuple[np.ndarray, np.ndarray]:
    padded = np.zeros((len(sequences), int(max_len), 3), dtype=np.float32)
    mask = np.zeros((len(sequences), int(max_len)), dtype=np.float32)
    for index, sequence in enumerate(sequences):
        seq = np.asarray(sequence, dtype=np.float32)
        if seq.ndim != 2 or seq.shape[1] != 3:
            raise ValueError(f"expected (K, 3) sequence, got {seq.shape}")
        padded[index, : seq.shape[0]] = seq
        mask[index, : seq.shape[0]] = 1.0
    return padded, mask


def write_action_divergent_corpus(
    *,
    output_npz: Path,
    rows: list[dict[str, Any]],
    corpus: dict[str, list[np.ndarray]],
    obs_dim: int,
    hidden_dim: int,
    max_sequence_length: int,
) -> None:
    output_npz.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        np.savez_compressed(
            output_npz,
            observation=np.zeros((0, int(obs_dim)), dtype=np.float32),
            normal_hidden=np.zeros((0, int(hidden_dim)), dtype=np.float32),
            variant_hidden=np.zeros((0, int(hidden_dim)), dtype=np.float32),
            preferred_action_sequence=np.zeros((0, int(max_sequence_length), 3), dtype=np.float32),
            rejected_action_sequence=np.zeros((0, int(max_sequence_length), 3), dtype=np.float32),
            target_action_sequence=np.zeros((0, int(max_sequence_length), 3), dtype=np.float32),
            normal_base_action_sequence=np.zeros((0, int(max_sequence_length), 3), dtype=np.float32),
            variant_base_action_sequence=np.zeros((0, int(max_sequence_length), 3), dtype=np.float32),
            sequence_mask=np.zeros((0, int(max_sequence_length)), dtype=np.float32),
            variant_base_action=np.zeros((0, 3), dtype=np.float32),
            weight=np.zeros(0, dtype=np.float32),
            row_id=np.zeros(0, dtype=np.int64),
            source_index=np.zeros(0, dtype=np.int64),
            sequence_length=np.zeros(0, dtype=np.int64),
        )
        return
    preferred, mask = _pad_sequences(corpus["preferred_action_sequence"], max_sequence_length)
    rejected, _ = _pad_sequences(corpus["rejected_action_sequence"], max_sequence_length)
    normal_base, _ = _pad_sequences(corpus["normal_base_action_sequence"], max_sequence_length)
    variant_base, _ = _pad_sequences(corpus["variant_base_action_sequence"], max_sequence_length)
    np.savez_compressed(
        output_npz,
        observation=np.asarray(corpus["observation"], dtype=np.float32),
        normal_hidden=np.asarray(corpus["normal_hidden"], dtype=np.float32),
        variant_hidden=np.asarray(corpus["variant_hidden"], dtype=np.float32),
        preferred_action_sequence=preferred,
        rejected_action_sequence=rejected,
        target_action_sequence=preferred,
        normal_base_action_sequence=normal_base,
        variant_base_action_sequence=variant_base,
        sequence_mask=mask,
        variant_base_action=rejected[:, 0, :],
        weight=np.asarray([float(row["weight"]) for row in rows], dtype=np.float32),
        row_id=np.arange(len(rows), dtype=np.int64),
        source_index=np.asarray([int(row["source_index"]) for row in rows], dtype=np.int64),
        sequence_length=np.asarray([int(row["sequence_length"]) for row in rows], dtype=np.int64),
    )


def _summary_rows(frame: pd.DataFrame, group_column: str) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    rows: list[dict[str, Any]] = []
    for value, group in frame.groupby(group_column, observed=True):
        rows.append(
            {
                group_column: value,
                "rows": int(len(group)),
                "sources": int(group["source_index"].nunique()),
                "physical_pairs": int(group["physical_pair_key"].nunique()),
                "left_seeds": int(group["left_seed"].nunique()),
                "targets": int(group["target"].nunique()),
                "mean_wrong_first_action_l2": float(group["wrong_first_action_l2"].mean()),
                "mean_wrong_action_sequence_mean_l2": float(group["wrong_action_sequence_mean_l2"].mean()),
                "mean_preferred_rejected_action_mean_l2": float(group["preferred_vs_rejected_action_mean_l2"].mean()),
                "mean_margin_gap": float(group["margin_gap"].mean()),
            }
        )
    return rows


def _max_share(frame: pd.DataFrame, column: str) -> float:
    if frame.empty:
        return 0.0
    counts = frame[column].value_counts()
    return float(counts.max() / max(len(frame), 1))


def _candidate_distribution_summary(
    frame: pd.DataFrame,
    *,
    min_wrong_first_action_l2: float,
    min_wrong_action_sequence_mean_l2: float,
    min_preferred_rejected_action_mean_l2: float,
    min_margin_gap: float,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "candidate_projected_preferred_available_rows": 0,
            "candidate_normal_success_rate": float("nan"),
            "candidate_wrong_success_rate": float("nan"),
            "candidate_max_wrong_first_action_l2": float("nan"),
            "candidate_max_wrong_action_sequence_mean_l2": float("nan"),
            "candidate_max_preferred_rejected_action_mean_l2": float("nan"),
            "candidate_max_margin_gap": float("nan"),
            "candidate_wrong_first_action_threshold_rows": 0,
            "candidate_wrong_sequence_threshold_rows": 0,
            "candidate_preferred_rejected_threshold_rows": 0,
            "candidate_margin_threshold_rows": 0,
            "candidate_all_action_threshold_rows": 0,
            "candidate_all_action_and_margin_threshold_rows": 0,
            "candidate_rejection_reasons": {},
        }
    all_action = (
        (frame["wrong_first_action_l2"].astype(float) >= float(min_wrong_first_action_l2))
        & (frame["wrong_action_sequence_mean_l2"].astype(float) >= float(min_wrong_action_sequence_mean_l2))
        & (
            frame["preferred_vs_rejected_action_mean_l2"].astype(float)
            >= float(min_preferred_rejected_action_mean_l2)
        )
    )
    margin = frame["margin_gap"].astype(float) >= float(min_margin_gap)
    return {
        "candidate_projected_preferred_available_rows": int(
            frame["projected_preferred_sequence_available"].astype(bool).sum()
        )
        if "projected_preferred_sequence_available" in frame
        else 0,
        "candidate_normal_success_rate": float(frame["normal_success"].astype(bool).mean()),
        "candidate_wrong_success_rate": float(frame["wrong_success"].astype(bool).mean()),
        "candidate_max_wrong_first_action_l2": float(frame["wrong_first_action_l2"].astype(float).max()),
        "candidate_max_wrong_action_sequence_mean_l2": float(
            frame["wrong_action_sequence_mean_l2"].astype(float).max()
        ),
        "candidate_max_preferred_rejected_action_mean_l2": float(
            frame["preferred_vs_rejected_action_mean_l2"].astype(float).max()
        ),
        "candidate_max_margin_gap": float(frame["margin_gap"].astype(float).max()),
        "candidate_wrong_first_action_threshold_rows": int(
            (frame["wrong_first_action_l2"].astype(float) >= float(min_wrong_first_action_l2)).sum()
        ),
        "candidate_wrong_sequence_threshold_rows": int(
            (frame["wrong_action_sequence_mean_l2"].astype(float) >= float(min_wrong_action_sequence_mean_l2)).sum()
        ),
        "candidate_preferred_rejected_threshold_rows": int(
            (
                frame["preferred_vs_rejected_action_mean_l2"].astype(float)
                >= float(min_preferred_rejected_action_mean_l2)
            ).sum()
        ),
        "candidate_margin_threshold_rows": int(margin.sum()),
        "candidate_all_action_threshold_rows": int(all_action.sum()),
        "candidate_all_action_and_margin_threshold_rows": int((all_action & margin).sum()),
        "candidate_rejection_reasons": {
            str(key): int(value) for key, value in frame["rejection_reason"].value_counts().to_dict().items()
        },
    }


def run_action_divergent_wrong_history_corpus(
    *,
    checkpoint_path: Path,
    surface_pairs: dict[str, Path],
    surface_configs: dict[str, Path],
    preferred_sequences_csv: Path | None,
    sequence_lengths: tuple[int, ...],
    min_wrong_first_action_l2: float,
    min_wrong_action_sequence_mean_l2: float,
    min_preferred_rejected_action_mean_l2: float,
    min_margin_gap: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    freeze_actor(model)
    before_checksum = model_parameter_checksum(model)
    pairs = load_surface_pairs(surface_pairs)
    if pairs.empty:
        raise ValueError("no matched-current pairs loaded")
    missing_configs = sorted(set(pairs["surface"].astype(str)).difference(surface_configs))
    if missing_configs:
        raise ValueError(f"missing surface configs: {missing_configs}")
    preferred_sequence_count = 0
    projected_preferred_keys = preferred_sequence_keys(preferred_sequences_csv)
    if preferred_sequences_csv is not None and preferred_sequences_csv.exists():
        preferred_sequence_count = int(len(pd.read_csv(preferred_sequences_csv)))

    all_candidates: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observation": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "preferred_action_sequence": [],
        "rejected_action_sequence": [],
        "normal_base_action_sequence": [],
        "variant_base_action_sequence": [],
    }
    response_dim = len(model.response_feature_indices) if getattr(model, "response_feature_indices", ()) else 0
    max_len = max(int(length) for length in sequence_lengths)
    for surface, group in pairs.groupby("surface", observed=True):
        env_config = load_env_config(surface_configs[str(surface)])
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=snapshot_requests(group),
            device=resolved_device,
        )
        for _, pair in group.reset_index(drop=True).iterrows():
            left = _snapshot(snapshots, int(pair["left_seed"]), int(pair["left_step"]))
            right = _snapshot(snapshots, int(pair["right_seed"]), int(pair["right_step"]))
            if left is None or right is None:
                continue
            rows, row_corpus = score_wrong_history_pair(
                pair=pair,
                left=left,
                right=right,
                model=model,
                env_config=env_config,
                response_dim=response_dim,
                sequence_lengths=sequence_lengths,
                max_continuation_steps=max(int(max_continuation_steps), max_len),
                min_wrong_first_action_l2=min_wrong_first_action_l2,
                min_wrong_action_sequence_mean_l2=min_wrong_action_sequence_mean_l2,
                min_preferred_rejected_action_mean_l2=min_preferred_rejected_action_mean_l2,
                min_margin_gap=min_margin_gap,
                projected_preferred_keys=projected_preferred_keys,
                device=resolved_device,
            )
            all_candidates.extend(rows)
            for key, values in row_corpus.items():
                corpus[key].extend(values)
            accepted_rows.extend([row for row in rows if bool(row["accepted"])])
    _assign_splits(accepted_rows)
    weights = source_diversity_weights(accepted_rows)
    for row in accepted_rows:
        row["weight"] = float(weights.get(int(row["source_index"]), 1.0))
    candidate_frame = pd.DataFrame(all_candidates)
    accepted_frame = pd.DataFrame(accepted_rows)
    candidate_summary = _candidate_distribution_summary(
        candidate_frame,
        min_wrong_first_action_l2=min_wrong_first_action_l2,
        min_wrong_action_sequence_mean_l2=min_wrong_action_sequence_mean_l2,
        min_preferred_rejected_action_mean_l2=min_preferred_rejected_action_mean_l2,
        min_margin_gap=min_margin_gap,
    )
    write_csv_rows(run_dir / "candidate_scores.csv", all_candidates)
    write_csv_rows(run_dir / "action_divergent_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "source_summary.csv", _summary_rows(accepted_frame, "source_index"))
    write_csv_rows(run_dir / "split_summary.csv", _summary_rows(accepted_frame, "split"))
    write_csv_rows(run_dir / "target_summary.csv", _summary_rows(accepted_frame, "target"))
    write_action_divergent_corpus(
        output_npz=run_dir / "action_divergent_corpus.npz",
        rows=accepted_rows,
        corpus=corpus,
        obs_dim=int(model.obs_dim),
        hidden_dim=int(model.actor_mean.in_features),
        max_sequence_length=max_len,
    )
    after_checksum = model_parameter_checksum(model)
    accepted_rows_count = int(len(accepted_frame))
    physical_pairs = int(accepted_frame["physical_pair_key"].nunique()) if accepted_rows_count else 0
    left_seeds = int(accepted_frame["left_seed"].nunique()) if accepted_rows_count else 0
    targets = int(accepted_frame["target"].nunique()) if accepted_rows_count else 0
    heldout_nonempty = bool(accepted_rows_count and (accepted_frame["split"] == "source_holdout_validation").any())
    mean_action_l2 = (
        float(accepted_frame["preferred_vs_rejected_action_mean_l2"].mean()) if accepted_rows_count else float("nan")
    )
    mean_margin_gap = float(accepted_frame["margin_gap"].mean()) if accepted_rows_count else float("nan")
    projected_available_rows = (
        int(accepted_frame["projected_preferred_sequence_available"].astype(bool).sum())
        if accepted_rows_count
        else 0
    )
    corpus_passed = bool(
        accepted_rows_count >= 40
        and physical_pairs >= 8
        and left_seeds >= 6
        and targets >= 2
        and heldout_nonempty
        and np.isfinite(mean_action_l2)
        and mean_action_l2 >= 0.010
        and np.isfinite(mean_margin_gap)
        and mean_margin_gap >= 0.010
        and before_checksum == after_checksum
    )
    summary = {
        "run_type": "action_divergent_wrong_history_corpus",
        "checkpoint": checkpoint_path,
        "surface_pairs": surface_pairs,
        "surface_configs": surface_configs,
        "preferred_sequences_csv": preferred_sequences_csv,
        "preferred_sequence_count": preferred_sequence_count,
        "preferred_sequence_unique_keys": int(len(projected_preferred_keys)),
        "preferred_sequence_source": "normal_policy_base",
        "projected_preferred_available_rows": projected_available_rows,
        "normal_policy_preferred_rows": accepted_rows_count,
        **candidate_summary,
        "candidate_rows": int(len(candidate_frame)),
        "accepted_rows": accepted_rows_count,
        "accepted_physical_pairs": physical_pairs,
        "accepted_left_seeds": left_seeds,
        "accepted_targets": targets,
        "source_holdout_nonempty": heldout_nonempty,
        "max_physical_pair_share": _max_share(accepted_frame, "physical_pair_key"),
        "max_source_index_share": _max_share(accepted_frame, "source_index"),
        "mean_preferred_vs_rejected_action_mean_l2": mean_action_l2,
        "mean_margin_gap": mean_margin_gap,
        "sequence_lengths": sequence_lengths,
        "min_wrong_first_action_l2": float(min_wrong_first_action_l2),
        "min_wrong_action_sequence_mean_l2": float(min_wrong_action_sequence_mean_l2),
        "min_preferred_rejected_action_mean_l2": float(min_preferred_rejected_action_mean_l2),
        "min_margin_gap": float(min_margin_gap),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": bool(before_checksum != after_checksum),
        "actor_checkpoint_written": False,
        "corpus_passed": corpus_passed,
        "action_divergent_corpus_npz": run_dir / "action_divergent_corpus.npz",
        "action_divergent_rows_csv": run_dir / "action_divergent_rows.csv",
        "candidate_scores_csv": run_dir / "candidate_scores.csv",
        "source_summary_csv": run_dir / "source_summary.csv",
        "split_summary_csv": run_dir / "split_summary.csv",
        "target_summary_csv": run_dir / "target_summary.csv",
        "diagnostic_only": True,
        "training_started": False,
        "optimizer_started": False,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine an action-divergent wrong-history corpus without training.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--surface-pairs", type=parse_surface_path, action="append", required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--preferred-sequences", type=Path, default=None)
    parser.add_argument("--sequence-lengths", type=parse_int_list, default=(5, 7, 9))
    parser.add_argument("--min-wrong-first-action-l2", type=float, default=0.002)
    parser.add_argument("--min-wrong-action-sequence-mean-l2", type=float, default=0.006)
    parser.add_argument("--min-preferred-rejected-action-mean-l2", type=float, default=0.010)
    parser.add_argument("--min-margin-gap", type=float, default=0.010)
    parser.add_argument("--max-continuation-steps", type=int, default=9)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="action_divergent_wrong_history_corpus")
    summary = run_action_divergent_wrong_history_corpus(
        checkpoint_path=args.checkpoint,
        surface_pairs=dict(args.surface_pairs),
        surface_configs={item.surface: item.env_config_path for item in args.surface_config},
        preferred_sequences_csv=args.preferred_sequences,
        sequence_lengths=args.sequence_lengths,
        min_wrong_first_action_l2=args.min_wrong_first_action_l2,
        min_wrong_action_sequence_mean_l2=args.min_wrong_action_sequence_mean_l2,
        min_preferred_rejected_action_mean_l2=args.min_preferred_rejected_action_mean_l2,
        min_margin_gap=args.min_margin_gap,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=run_dir,
    )
    print(f"run_dir={run_dir}")
    print(f"corpus_passed={summary['corpus_passed']}")
    print(f"accepted_rows={summary['accepted_rows']}")
    print(f"summary={run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
