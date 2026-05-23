"""Build differentiable old-key preference corpora for exact repair."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, read_json, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.old_key_neighborhood_targeted_replay import (
    COMPACT_REQUIRED_COLUMNS,
    _probe_config,
    _randomization,
    _requests_by_condition,
    _snapshot,
    _tuple_range,
    collect_targeted_probe_snapshots,
)
from autodrift.outcome_sensitive_corpus import obstacle_override_config, relocate_obstacle_snapshot
from autodrift.paired_perturbation_gate import condition_config
from autodrift.train_ppo import ActorCritic, resolve_device


REQUIRED_ARRAYS = (
    "observation",
    "preferred_hidden",
    "rejected_hidden",
    "preferred_action",
    "rejected_action",
    "preferred_score",
    "rejected_score",
    "score_delta",
    "normal_margin",
    "wrong_history_margin",
    "margin_floor",
    "weight",
    "row_id",
    "group_index",
    "target_index",
)
OPTIONAL_ARRAYS = (
    "hard_row",
    "gap_tail_row",
    "preferred_branch_weight",
    "wrong_branch_weight",
)
STUDENT_INPUT_ARRAYS = ("observation", "preferred_hidden", "rejected_hidden")

OVERLAY_REQUIRED_COLUMNS = ("case_id",)


@dataclass(frozen=True)
class OldKeyPreferenceCorpusContract:
    rows: int
    obs_dim: int
    hidden_dim: int
    act_dim: int
    groups: int
    targets: int
    student_input_arrays: tuple[str, ...]


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], *, label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing columns: {', '.join(missing)}")


def _hidden_array(model: ActorCritic, hidden: torch.Tensor | None, device: torch.device) -> np.ndarray:
    hidden_t = hidden if hidden is not None else model.initial_hidden(1, device)
    return hidden_t.detach().cpu().numpy().reshape(-1).astype(np.float32)


def _outcome_score(success: bool, margin: float, *, success_bonus: float = 1.0, margin_clip: float = 0.25) -> float:
    margin_value = float(margin)
    if not np.isfinite(margin_value):
        margin_value = -float(margin_clip)
    clipped = float(np.clip(margin_value, -float(margin_clip), float(margin_clip)))
    return (float(success_bonus) if bool(success) else 0.0) + clipped


def old_key_preference_weight(
    *,
    reference_margin_gap: float,
    reference_normal_margin: float,
    direct_candidate_regression: bool = False,
    alpha_0005_regression: bool = False,
) -> float:
    """Deterministic training-only weight for old-key repair rows."""

    gap_term = float(np.clip(abs(float(reference_margin_gap)), 0.0, 0.05) / 0.05)
    boundary_term = 0.0
    if np.isfinite(reference_normal_margin):
        boundary_term = float(np.clip(0.01 - float(reference_normal_margin), 0.0, 0.01) / 0.01)
    return float(
        1.0
        + 4.0 * float(bool(direct_candidate_regression))
        + 2.0 * float(bool(alpha_0005_regression))
        + gap_term
        + boundary_term
    )


def _target_key(row: pd.Series) -> str:
    return "{distance:.6f}:{lateral:.6f}:{half_width:.6f}".format(
        distance=float(row["target_obstacle_distance"]),
        lateral=float(row["relocated_obstacle_body_y"]),
        half_width=float(row["relocated_obstacle_half_width"]),
    )


def old_key_case_id(row: pd.Series | dict[str, Any]) -> str:
    return "{key}|{distance:.6f}|{lateral:.6f}|{half_width:.6f}".format(
        key=str(row["key"]),
        distance=float(row["target_obstacle_distance"]),
        lateral=float(row["relocated_obstacle_body_y"]),
        half_width=float(row["relocated_obstacle_half_width"]),
    )


def _bool_value(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_value(row: pd.Series, name: str, default: float) -> float:
    if name not in row.index or pd.isna(row[name]):
        return float(default)
    return float(row[name])


def _string_value(row: pd.Series, name: str, default: str = "") -> str:
    if name not in row.index or pd.isna(row[name]):
        return default
    return str(row[name])


def load_hard_row_overlay(path: Path | str | None) -> dict[str, dict[str, Any]]:
    """Load optional old-key feedback keyed by old-key case id."""

    if path is None:
        return {}
    frame = pd.read_csv(path)
    _require_columns(frame, OVERLAY_REQUIRED_COLUMNS, label="old-key feedback overlay")
    overlay: dict[str, dict[str, Any]] = {}
    for _, row in frame.iterrows():
        case_id = str(row["case_id"])
        if not case_id:
            raise ValueError("old-key feedback overlay contains an empty case_id")
        if case_id in overlay:
            raise ValueError(f"old-key feedback overlay contains duplicate case_id {case_id!r}")
        hard_weight = _float_value(row, "hard_weight_multiplier", 1.0)
        gap_weight = _float_value(row, "gap_weight_multiplier", 1.0)
        wrong_weight = _float_value(row, "wrong_branch_weight_multiplier", 1.0)
        preferred_weight = _float_value(
            row,
            "preferred_branch_weight_multiplier",
            _float_value(row, "normal_branch_weight_multiplier", 1.0),
        )
        if hard_weight < 0.0 or gap_weight < 0.0 or wrong_weight < 0.0 or preferred_weight < 0.0:
            raise ValueError("old-key feedback overlay multipliers must be non-negative")
        overlay[case_id] = {
            "case_id": case_id,
            "hard_row": _bool_value(row["hard_row"]) if "hard_row" in row.index else False,
            "hard_row_reason": _string_value(row, "hard_row_reason"),
            "hard_weight_multiplier": hard_weight,
            "gap_tail_row": _bool_value(row["gap_tail_row"]) if "gap_tail_row" in row.index else False,
            "gap_tail_reason": _string_value(row, "gap_tail_reason"),
            "gap_weight_multiplier": gap_weight,
            "wrong_branch_weight_multiplier": wrong_weight,
            "preferred_branch_weight_multiplier": preferred_weight,
            "normal_branch_weight_multiplier": preferred_weight,
            "reference_wrong_history_margin": _float_value(row, "reference_wrong_history_margin", float("nan")),
            "candidate_wrong_history_margin": _float_value(row, "candidate_wrong_history_margin", float("nan")),
            "candidate_accepted_regression": (
                _bool_value(row["candidate_accepted_regression"])
                if "candidate_accepted_regression" in frame.columns
                else False
            ),
            "reference_policy": _string_value(row, "reference_policy"),
            "candidate_policy": _string_value(row, "candidate_policy"),
            "reference_margin_gap": _float_value(row, "reference_margin_gap", float("nan")),
            "candidate_margin_gap": _float_value(row, "candidate_margin_gap", float("nan")),
            "candidate_gap_delta": _float_value(row, "candidate_gap_delta", float("nan")),
            "candidate_normal_delta": _float_value(row, "candidate_normal_delta", float("nan")),
            "candidate_wrong_delta": _float_value(row, "candidate_wrong_delta", float("nan")),
            "target_gap_delta_floor": _float_value(row, "target_gap_delta_floor", float("nan")),
            "target_gap_delta_buffer": _float_value(row, "target_gap_delta_buffer", float("nan")),
            "candidate_gap_p10_regression": (
                _bool_value(row["candidate_gap_p10_regression"])
                if "candidate_gap_p10_regression" in frame.columns
                else False
            ),
        }
    return overlay


def build_old_key_preference_examples(
    *,
    model: ActorCritic,
    compact: pd.DataFrame,
    manifest: dict[str, Any],
    device: torch.device,
    hard_row_overlay: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build old-key preference examples from compact rows and reconstructed snapshots."""

    _require_columns(compact, tuple(COMPACT_REQUIRED_COLUMNS), label="compact corpus")
    if "record_type" in compact:
        compact = compact[compact["record_type"].astype(str).eq("m341_mined_case")].copy()
    if compact.empty:
        raise ValueError("compact corpus has no mined old-key rows")

    base_config = obstacle_override_config(
        load_env_config(Path(manifest["env_config"])),
        distance_range=None,
        half_width_range=None,
        perception_reveal_step=manifest.get("obstacle_perception_reveal_step"),
        perception_reveal_distance=manifest.get("obstacle_perception_reveal_distance"),
    )
    configs = {
        "nominal": condition_config(
            base_config,
            _tuple_range(manifest["nominal_friction_mu_range"]),
            _randomization(manifest.get("nominal_randomization")),
        ),
        "perturbed": condition_config(
            base_config,
            _tuple_range(manifest["perturbed_friction_mu_range"]),
            _randomization(manifest.get("perturbed_randomization")),
        ),
    }
    probe = _probe_config(manifest.get("probe", {}))
    requests = _requests_by_condition(compact)
    snapshots: dict[str, dict[int, dict[int, Any]]] = {"nominal": {}, "perturbed": {}}
    for condition, seed_requests in requests.items():
        for seed, steps in seed_requests.items():
            snapshots[condition][int(seed)] = collect_targeted_probe_snapshots(
                model=model,
                env_config=configs[condition],
                condition=condition,
                seed=int(seed),
                requested_steps=set(int(step) for step in steps),
                max_probe_steps=int(manifest["max_probe_steps"]),
                probe_config=probe,
            )

    target_to_index = {key: index for index, key in enumerate(sorted({_target_key(row) for _, row in compact.iterrows()}))}
    overlay = hard_row_overlay or {}
    examples: list[dict[str, Any]] = []
    for row_id, row in compact.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        source = str(row["source_condition"])
        paired = "perturbed" if source == "nominal" else "nominal"
        source_snapshot = _snapshot(snapshots, source, seed, int(row["source_step"]))
        paired_snapshot = _snapshot(snapshots, paired, seed, int(row["paired_step"]))
        if source_snapshot is None or paired_snapshot is None:
            raise ValueError(f"missing old-key snapshots for row {row_id}")
        relocated = relocate_obstacle_snapshot(
            source_snapshot,
            body_longitudinal=float(row["target_obstacle_distance"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        preferred_hidden = source_snapshot.hidden if source_snapshot.hidden is not None else model.initial_hidden(1, device)
        rejected_hidden = paired_snapshot.hidden if paired_snapshot.hidden is not None else model.initial_hidden(1, device)
        preferred_action, _ = deterministic_action_from_hidden(
            model,
            np.asarray(relocated.observation, dtype=np.float32),
            preferred_hidden,
            device,
        )
        rejected_action, _ = deterministic_action_from_hidden(
            model,
            np.asarray(relocated.observation, dtype=np.float32),
            rejected_hidden,
            device,
        )
        normal_margin = float(row["reference_normal_margin"])
        wrong_margin = float(row["reference_wrong_history_margin"])
        margin_gap = float(row["reference_margin_gap"])
        normal_success = bool(normal_margin > 0.0)
        wrong_success = bool(wrong_margin > 0.0)
        target_key = _target_key(row)
        case_id = old_key_case_id(row)
        hard = overlay.get(case_id, {})
        hard_row = bool(hard.get("hard_row", False))
        gap_tail_row = bool(hard.get("gap_tail_row", False))
        hard_weight_multiplier = float(hard.get("hard_weight_multiplier", 1.0))
        gap_weight_multiplier = float(hard.get("gap_weight_multiplier", 1.0))
        preferred_branch_weight = float(hard.get("preferred_branch_weight_multiplier", 1.0))
        wrong_branch_weight = float(hard.get("wrong_branch_weight_multiplier", 1.0))
        examples.append(
            {
                "row_id": int(row_id),
                "case_id": case_id,
                "key": str(row["key"]),
                "seed": seed,
                "source_condition": source,
                "source_step": int(row["source_step"]),
                "paired_step": int(row["paired_step"]),
                "target_obstacle_distance": float(row["target_obstacle_distance"]),
                "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
                "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
                "target_key": target_key,
                "target_index": int(target_to_index[target_key]),
                "group_index": int(row_id),
                "normal_margin": normal_margin,
                "wrong_history_margin": wrong_margin,
                "margin_floor": min(normal_margin, wrong_margin),
                "preferred_score": _outcome_score(normal_success, normal_margin),
                "rejected_score": _outcome_score(wrong_success, wrong_margin),
                "score_delta": _outcome_score(normal_success, normal_margin)
                - _outcome_score(wrong_success, wrong_margin),
                "weight": old_key_preference_weight(
                    reference_margin_gap=margin_gap,
                    reference_normal_margin=normal_margin,
                )
                * hard_weight_multiplier
                * gap_weight_multiplier,
                "hard_row": hard_row,
                "hard_row_reason": str(hard.get("hard_row_reason", "")),
                "hard_weight_multiplier": hard_weight_multiplier,
                "gap_tail_row": gap_tail_row,
                "gap_tail_reason": str(hard.get("gap_tail_reason", "")),
                "gap_weight_multiplier": gap_weight_multiplier,
                "preferred_branch_weight_multiplier": preferred_branch_weight,
                "normal_branch_weight_multiplier": preferred_branch_weight,
                "wrong_branch_weight_multiplier": wrong_branch_weight,
                "reference_wrong_history_margin": float(
                    hard.get("reference_wrong_history_margin", wrong_margin)
                ),
                "candidate_wrong_history_margin": float(
                    hard.get("candidate_wrong_history_margin", float("nan"))
                ),
                "candidate_accepted_regression": bool(hard.get("candidate_accepted_regression", False)),
                "reference_policy": str(hard.get("reference_policy", "")),
                "candidate_policy": str(hard.get("candidate_policy", "")),
                "reference_margin_gap": float(hard.get("reference_margin_gap", margin_gap)),
                "candidate_margin_gap": float(hard.get("candidate_margin_gap", float("nan"))),
                "candidate_gap_delta": float(hard.get("candidate_gap_delta", float("nan"))),
                "candidate_normal_delta": float(hard.get("candidate_normal_delta", float("nan"))),
                "candidate_wrong_delta": float(hard.get("candidate_wrong_delta", float("nan"))),
                "target_gap_delta_floor": float(hard.get("target_gap_delta_floor", float("nan"))),
                "target_gap_delta_buffer": float(hard.get("target_gap_delta_buffer", float("nan"))),
                "candidate_gap_p10_regression": bool(hard.get("candidate_gap_p10_regression", False)),
                "student_input_contract": "observation plus deployable recurrent hidden states",
                "observation": np.asarray(relocated.observation, dtype=np.float32).copy(),
                "preferred_hidden": _hidden_array(model, preferred_hidden, device),
                "rejected_hidden": _hidden_array(model, rejected_hidden, device),
                "preferred_action": np.asarray(preferred_action, dtype=np.float32).copy(),
                "rejected_action": np.asarray(rejected_action, dtype=np.float32).copy(),
            }
        )
    return examples


def old_key_preference_arrays(examples: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    if not examples:
        return {}
    arrays = {
        "observation": np.stack([example["observation"] for example in examples]).astype(np.float32),
        "preferred_hidden": np.stack([example["preferred_hidden"] for example in examples]).astype(np.float32),
        "rejected_hidden": np.stack([example["rejected_hidden"] for example in examples]).astype(np.float32),
        "preferred_action": np.stack([example["preferred_action"] for example in examples]).astype(np.float32),
        "rejected_action": np.stack([example["rejected_action"] for example in examples]).astype(np.float32),
        "preferred_score": np.asarray([example["preferred_score"] for example in examples], dtype=np.float32),
        "rejected_score": np.asarray([example["rejected_score"] for example in examples], dtype=np.float32),
        "score_delta": np.asarray([example["score_delta"] for example in examples], dtype=np.float32),
        "normal_margin": np.asarray([example["normal_margin"] for example in examples], dtype=np.float32),
        "wrong_history_margin": np.asarray([example["wrong_history_margin"] for example in examples], dtype=np.float32),
        "margin_floor": np.asarray([example["margin_floor"] for example in examples], dtype=np.float32),
        "weight": np.asarray([example["weight"] for example in examples], dtype=np.float32),
        "row_id": np.asarray([example["row_id"] for example in examples], dtype=np.int64),
        "group_index": np.asarray([example["group_index"] for example in examples], dtype=np.int64),
        "target_index": np.asarray([example["target_index"] for example in examples], dtype=np.int64),
    }
    uses_branch_weights = any(
        bool(example.get("hard_row", False))
        or bool(example.get("gap_tail_row", False))
        or float(example.get("preferred_branch_weight_multiplier", 1.0)) != 1.0
        or float(example.get("wrong_branch_weight_multiplier", 1.0)) != 1.0
        for example in examples
    )
    if uses_branch_weights:
        arrays.update(
            {
                "hard_row": np.asarray([bool(example.get("hard_row", False)) for example in examples], dtype=np.int64),
                "gap_tail_row": np.asarray(
                    [bool(example.get("gap_tail_row", False)) for example in examples], dtype=np.int64
                ),
                "preferred_branch_weight": np.asarray(
                    [example.get("preferred_branch_weight_multiplier", 1.0) for example in examples],
                    dtype=np.float32,
                ),
                "wrong_branch_weight": np.asarray(
                    [example.get("wrong_branch_weight_multiplier", 1.0) for example in examples],
                    dtype=np.float32,
                ),
            }
        )
    return arrays


def old_key_preference_metadata(examples: list[dict[str, Any]]) -> pd.DataFrame:
    tensor_keys = {"observation", "preferred_hidden", "rejected_hidden", "preferred_action", "rejected_action"}
    return pd.DataFrame([{key: value for key, value in example.items() if key not in tensor_keys} for example in examples])


def validate_old_key_preference_arrays(
    arrays: dict[str, np.ndarray],
    *,
    obs_dim: int | None = None,
    hidden_dim: int | None = None,
    act_dim: int | None = None,
) -> OldKeyPreferenceCorpusContract:
    missing = [key for key in REQUIRED_ARRAYS if key not in arrays]
    if missing:
        raise ValueError("old-key preference corpus is missing arrays: " + ", ".join(missing))
    observation = np.asarray(arrays["observation"], dtype=np.float32)
    preferred_hidden = np.asarray(arrays["preferred_hidden"], dtype=np.float32)
    rejected_hidden = np.asarray(arrays["rejected_hidden"], dtype=np.float32)
    preferred_action = np.asarray(arrays["preferred_action"], dtype=np.float32)
    rejected_action = np.asarray(arrays["rejected_action"], dtype=np.float32)
    rows = int(observation.shape[0])
    if rows < 1:
        raise ValueError("old-key preference corpus requires at least one row")
    if observation.ndim != 2 or (obs_dim is not None and observation.shape[1] != int(obs_dim)):
        raise ValueError(f"observation must have shape (N, {obs_dim}), got {observation.shape}")
    if preferred_hidden.shape != rejected_hidden.shape or preferred_hidden.ndim != 2:
        raise ValueError("preferred_hidden and rejected_hidden must be matching 2D arrays")
    if hidden_dim is not None and preferred_hidden.shape[1] != int(hidden_dim):
        raise ValueError(f"hidden arrays must have width {hidden_dim}, got {preferred_hidden.shape[1]}")
    if preferred_action.shape != rejected_action.shape or preferred_action.ndim != 2:
        raise ValueError("preferred_action and rejected_action must be matching 2D arrays")
    if act_dim is not None and preferred_action.shape[1] != int(act_dim):
        raise ValueError(f"action arrays must have width {act_dim}, got {preferred_action.shape[1]}")
    for name in REQUIRED_ARRAYS:
        value = np.asarray(arrays[name])
        if value.shape[0] != rows:
            raise ValueError(f"{name} row count {value.shape[0]} does not match {rows}")
        if name not in {"row_id", "group_index", "target_index"} and not np.all(np.isfinite(value)):
            raise ValueError(f"{name} must be finite")
    for name in OPTIONAL_ARRAYS:
        if name not in arrays:
            continue
        value = np.asarray(arrays[name])
        if value.shape != (rows,):
            raise ValueError(f"{name} must have shape ({rows},), got {value.shape}")
        if name not in {"hard_row", "gap_tail_row"} and not np.all(np.isfinite(value)):
            raise ValueError(f"{name} must be finite")
        if name not in {"hard_row", "gap_tail_row"} and np.any(value < 0.0):
            raise ValueError(f"{name} must be non-negative")
    weight = np.asarray(arrays["weight"], dtype=np.float32)
    if np.any(weight < 0.0) or float(np.max(weight)) <= 0.0:
        raise ValueError("old-key preference weights must contain at least one positive non-negative value")
    groups = int(np.unique(np.asarray(arrays["group_index"], dtype=np.int64)).size)
    targets = int(np.unique(np.asarray(arrays["target_index"], dtype=np.int64)).size)
    return OldKeyPreferenceCorpusContract(
        rows=rows,
        obs_dim=int(observation.shape[1]),
        hidden_dim=int(preferred_hidden.shape[1]),
        act_dim=int(preferred_action.shape[1]),
        groups=groups,
        targets=targets,
        student_input_arrays=STUDENT_INPUT_ARRAYS,
    )


def write_old_key_preference_corpus(
    *,
    examples: list[dict[str, Any]],
    run_dir: Path,
    obs_dim: int | None = None,
    hidden_dim: int | None = None,
    act_dim: int | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = old_key_preference_arrays(examples)
    contract = validate_old_key_preference_arrays(
        arrays,
        obs_dim=obs_dim,
        hidden_dim=hidden_dim,
        act_dim=act_dim,
    )
    npz_path = run_dir / "old_key_preference_corpus.npz"
    metadata_path = run_dir / "old_key_preference_corpus.csv"
    np.savez_compressed(npz_path, **arrays)
    old_key_preference_metadata(examples).to_csv(metadata_path, index=False)
    summary = {
        "run_type": "old_key_preference_corpus",
        "old_key_preference_corpus_npz": npz_path,
        "old_key_preference_corpus_csv": metadata_path,
        "contract": asdict(contract),
        "hard_rows": int(np.asarray(arrays.get("hard_row", np.zeros(contract.rows, dtype=np.int64))).sum()),
        "gap_tail_rows": int(np.asarray(arrays.get("gap_tail_row", np.zeros(contract.rows, dtype=np.int64))).sum()),
        "actor_inputs_changed": False,
        "ppo_or_actor_update_run": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def export_old_key_preference_corpus(
    *,
    reference_manifest: Path,
    compact_corpus_csv: Path,
    base_checkpoint: Path,
    hard_row_overlay_csv: Path | None,
    run_dir: Path,
    device: str,
) -> dict[str, Any]:
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    model.eval()
    compact = pd.read_csv(compact_corpus_csv)
    manifest = read_json(reference_manifest)
    examples = build_old_key_preference_examples(
        model=model,
        compact=compact,
        manifest=manifest,
        device=resolved_device,
        hard_row_overlay=load_hard_row_overlay(hard_row_overlay_csv),
    )
    summary = write_old_key_preference_corpus(
        examples=examples,
        run_dir=run_dir,
        obs_dim=model.obs_dim,
        hidden_dim=model.actor_mean.in_features,
        act_dim=model.act_dim,
    )
    summary.update(
        {
            "reference_manifest": reference_manifest,
            "compact_corpus_csv": compact_corpus_csv,
            "hard_row_overlay_csv": hard_row_overlay_csv,
            "base_checkpoint": base_checkpoint,
            "device": str(resolved_device),
        }
    )
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--compact-corpus-csv", type=Path, required=True)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--hard-row-overlay-csv", "--old-key-overlay-csv", dest="hard_row_overlay_csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="old_key_preference_corpus")
    summary = export_old_key_preference_corpus(
        reference_manifest=args.reference_manifest,
        compact_corpus_csv=args.compact_corpus_csv,
        base_checkpoint=args.base_checkpoint,
        hard_row_overlay_csv=args.hard_row_overlay_csv,
        device=args.device,
        run_dir=run_dir,
    )
    print(f"rows={summary['contract']['rows']}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
