"""Export materialized failed wrong-history retention artifacts for M1115."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.candidate_b_combined_active_set_anchor_export import (
    load_anchor_arrays,
    normalize_family_weights,
    save_anchor_npz,
    validate_anchor_arrays,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, collect_requested_outcome_snapshots
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


DEFAULT_BASE_CHECKPOINT = Path(
    "runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/"
    "m1031_base_row16x4_s40_a1.pt"
)
DEFAULT_FULL_GATE_RUN_DIR = Path("runs/m1112_materialized_actor_update_full_public_gate")
DEFAULT_BASE_COMBINED_ANCHOR = Path(
    "runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz"
)
DEFAULT_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_RUN_DIR = Path("runs/m1115_materialized_failed_wrong_history_retention_export")

REQUIRED_EVENT_COUNT = 47
DEFAULT_TARGET_SOURCE_INDEX_OFFSET = 2_000_000
DEFAULT_TARGET_FAMILY_ID = 2
DEFAULT_TARGET_FAMILY_TOTAL = 4.0

EVENT_FIELDNAMES = [
    "event_index",
    "surface_label",
    "surface_tier",
    "target_class",
    "corpus_csv",
    "replay_gate_dir",
    "row_id",
    "target",
    "physical_pair_key",
    "baseline_policy",
    "candidate_policy",
    "baseline_checkpoint",
    "candidate_checkpoint",
    "normal_lost",
    "wrong_history_safe",
    "baseline_success_drop",
    "candidate_success_drop",
    "base_normal_margin",
    "candidate_normal_margin",
    "base_wrong_history_margin",
    "candidate_wrong_history_margin",
    "base_margin_gap",
    "candidate_margin_gap",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "relocated_obstacle_body_x",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
]


def _as_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return bool(int(value))
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    raise ValueError(f"cannot parse boolean value: {value!r}")


def _norm_path_text(value: Any) -> str:
    return str(Path(str(value)))


def _same_path(lhs: Any, rhs: Any) -> bool:
    return _norm_path_text(lhs) == _norm_path_text(rhs)


def replay_gate_dirs(full_gate_run_dir: Path) -> list[tuple[str, str, Path]]:
    """Return known public replay gate dirs in deterministic M1115 order."""

    roots = [
        ("old_public", full_gate_run_dir / "full_gates"),
        ("family_intersection", full_gate_run_dir / "family_intersection_public_gate" / "replay_gates"),
        ("source_diverse", full_gate_run_dir / "source_diverse_protected_diagnostic" / "replay_gates"),
    ]
    dirs: list[tuple[str, str, Path]] = []
    for tier, root in roots:
        if not root.exists():
            raise FileNotFoundError(f"missing replay gate root: {root}")
        for replay_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            summary = replay_dir / "summary.json"
            rows = replay_dir / "boundary_replay_rows.csv"
            if summary.exists() and rows.exists():
                label = replay_dir.name
                if tier == "old_public" and label.endswith("_replay"):
                    label = label[: -len("_replay")]
                dirs.append((tier, label, replay_dir))
    return dirs


def _target_class_for_event(
    *,
    surface_tier: str,
    baseline_policy: str,
    baseline_checkpoint: str,
    base_checkpoint: Path,
) -> str:
    if str(surface_tier) == "family_intersection" or str(baseline_policy).startswith("short"):
        return "family_source"
    if baseline_policy in {"m399_base", "proof_current"} or _same_path(baseline_checkpoint, base_checkpoint):
        return "target_base"
    return "target_base"


def failed_events_from_replay_dir(
    *,
    replay_dir: Path,
    surface_label: str,
    surface_tier: str,
    base_checkpoint: Path,
) -> list[dict[str, Any]]:
    summary = pd.read_json(replay_dir / "summary.json", typ="series").to_dict()
    rows = pd.read_csv(replay_dir / "boundary_replay_rows.csv")
    baseline_policy = str(summary["baseline_policy"])
    candidate_policy = str(summary["candidate_policy"])
    baseline = rows[rows["policy"].astype(str) == baseline_policy].copy()
    candidate = rows[rows["policy"].astype(str) == candidate_policy].copy()
    if baseline.empty or candidate.empty:
        raise ValueError(f"{replay_dir} must contain baseline and candidate rows")
    merged = baseline.merge(
        candidate,
        on="row_id",
        suffixes=("_baseline", "_candidate"),
        validate="one_to_one",
    )
    events: list[dict[str, Any]] = []
    for _, row in merged.sort_values("row_id").iterrows():
        baseline_success_drop = _as_bool(row["success_drop_baseline"])
        candidate_success_drop = _as_bool(row["success_drop_candidate"])
        if not baseline_success_drop or candidate_success_drop:
            continue
        normal_lost = not _as_bool(row["normal_success_candidate"])
        wrong_history_safe = _as_bool(row["wrong_history_success_candidate"])
        baseline_checkpoint = str(row["checkpoint_baseline"])
        candidate_checkpoint = str(row["checkpoint_candidate"])
        target_class = _target_class_for_event(
            surface_tier=surface_tier,
            baseline_policy=baseline_policy,
            baseline_checkpoint=baseline_checkpoint,
            base_checkpoint=base_checkpoint,
        )
        events.append(
            {
                "surface_label": str(surface_label),
                "surface_tier": str(surface_tier),
                "target_class": target_class,
                "corpus_csv": str(summary.get("corpus_csv", "")),
                "replay_gate_dir": str(replay_dir),
                "row_id": int(row["row_id"]),
                "target": str(row["target_baseline"]),
                "physical_pair_key": str(row["physical_pair_key_baseline"]),
                "baseline_policy": baseline_policy,
                "candidate_policy": candidate_policy,
                "baseline_checkpoint": baseline_checkpoint,
                "candidate_checkpoint": candidate_checkpoint,
                "normal_lost": bool(normal_lost),
                "wrong_history_safe": bool(wrong_history_safe),
                "baseline_success_drop": bool(baseline_success_drop),
                "candidate_success_drop": bool(candidate_success_drop),
                "base_normal_margin": float(row["normal_margin_baseline"]),
                "candidate_normal_margin": float(row["normal_margin_candidate"]),
                "base_wrong_history_margin": float(row["wrong_history_margin_baseline"]),
                "candidate_wrong_history_margin": float(row["wrong_history_margin_candidate"]),
                "base_margin_gap": float(row["margin_gap_baseline"]),
                "candidate_margin_gap": float(row["margin_gap_candidate"]),
                "left_seed": int(row["left_seed_baseline"]),
                "right_seed": int(row["right_seed_baseline"]),
                "left_step": int(row["left_step_baseline"]),
                "right_step": int(row["right_step_baseline"]),
                "relocated_obstacle_body_x": float(row["relocated_obstacle_body_x_baseline"]),
                "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y_baseline"]),
                "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width_baseline"]),
            }
        )
    return events


def collect_failed_events(*, full_gate_run_dir: Path, base_checkpoint: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for surface_tier, surface_label, replay_dir in replay_gate_dirs(full_gate_run_dir):
        events.extend(
            failed_events_from_replay_dir(
                replay_dir=replay_dir,
                surface_label=surface_label,
                surface_tier=surface_tier,
                base_checkpoint=base_checkpoint,
            )
        )
    for index, event in enumerate(events):
        event["event_index"] = int(index)
    return events


def validate_failed_event_registry(events: list[dict[str, Any]], *, expected_event_count: int) -> dict[str, int]:
    normal_lost_events = sum(1 for event in events if bool(event["normal_lost"]))
    wrong_history_safe_events = sum(1 for event in events if bool(event["wrong_history_safe"]))
    if len(events) != int(expected_event_count):
        raise ValueError(f"failed event count mismatch: expected {expected_event_count}, got {len(events)}")
    if normal_lost_events != 0:
        raise ValueError(f"normal_lost count must be 0, got {normal_lost_events}")
    if wrong_history_safe_events != len(events):
        raise ValueError(
            f"wrong_history_safe count must equal failed event count, got {wrong_history_safe_events}/{len(events)}"
        )
    return {
        "failed_event_count": int(len(events)),
        "normal_lost_events": int(normal_lost_events),
        "wrong_history_safe_events": int(wrong_history_safe_events),
    }


def _requests(rows: list[dict[str, Any]]) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for row in rows:
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
        requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
    return requests


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed snapshot seed={seed} step={step}")
    return snapshots[key]


def _record_action_trajectory(
    *,
    model: torch.nn.Module,
    snapshot: OutcomeSnapshot,
    rejected_hidden: torch.Tensor,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    obs = snapshot.observation.copy()
    hidden = rejected_hidden.detach().clone()
    env = snapshot.env
    observations: list[np.ndarray] = []
    hidden_states: list[np.ndarray] = []
    reference_actions: list[np.ndarray] = []
    terminated = False
    truncated = False
    for _ in range(max(1, int(max_continuation_steps))):
        observations.append(np.asarray(obs, dtype=np.float32).copy())
        hidden_states.append(hidden.detach().cpu().numpy().reshape(-1).astype(np.float32))
        action, next_hidden = deterministic_action_from_hidden(
            model,
            np.asarray(obs, dtype=np.float32),
            hidden,
            device,
        )
        reference_actions.append(np.asarray(action, dtype=np.float32).copy())
        obs, _, terminated, truncated, _ = env.step(action)
        hidden = next_hidden
        if terminated or truncated:
            break
    return observations, hidden_states, reference_actions


def save_anchor_arrays(path: Path, arrays: dict[str, np.ndarray]) -> None:
    validate_anchor_arrays(arrays, label=str(path))
    save_anchor_npz(path, arrays)


def export_target_base_rejected_trajectory_anchor(
    *,
    target_base_rows: list[dict[str, Any]],
    base_checkpoint: Path,
    env_config_path: Path,
    max_continuation_steps: int,
    failed_row_weight: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    if not target_base_rows:
        raise ValueError("target-base failed row export requires at least one row")
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    model, _ = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    model.eval()
    response_feature_dim_for_model(model)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(target_base_rows),
        device=resolved_device,
    )

    observations: list[np.ndarray] = []
    hidden_states: list[np.ndarray] = []
    reference_actions: list[np.ndarray] = []
    source_indices: list[int] = []
    step_indices: list[int] = []
    weights: list[float] = []
    trajectory_rows: list[dict[str, Any]] = []

    for source_index, row in enumerate(target_base_rows):
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        right = _snapshot(snapshots, int(row["right_seed"]), int(row["right_step"]))
        relocated = relocate_outcome_snapshot(
            left,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        obs_seq, hidden_seq, action_seq = _record_action_trajectory(
            model=model,
            snapshot=relocated,
            rejected_hidden=right.hidden,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        for step_index, (obs, hidden, action) in enumerate(zip(obs_seq, hidden_seq, action_seq)):
            observations.append(obs)
            hidden_states.append(hidden)
            reference_actions.append(action)
            source_indices.append(int(source_index))
            step_indices.append(int(step_index))
            weights.append(float(failed_row_weight))
            trajectory_rows.append(
                {
                    "event_index": int(row["event_index"]),
                    "source_index": int(source_index),
                    "step_index": int(step_index),
                    "weight": float(failed_row_weight),
                    "surface_label": str(row["surface_label"]),
                    "surface_tier": str(row["surface_tier"]),
                    "row_id": int(row["row_id"]),
                    "target": str(row["target"]),
                    "physical_pair_key": str(row["physical_pair_key"]),
                    "left_seed": int(row["left_seed"]),
                    "right_seed": int(row["right_seed"]),
                    "left_step": int(row["left_step"]),
                    "right_step": int(row["right_step"]),
                    "reference_steer": float(action[0]),
                    "reference_throttle": float(action[1]),
                    "reference_brake": float(action[2]),
                }
            )

    arrays = {
        "observation": np.asarray(observations, dtype=np.float32),
        "hidden": np.asarray(hidden_states, dtype=np.float32),
        "reference_action": np.asarray(reference_actions, dtype=np.float32),
        "source_index": np.asarray(source_indices, dtype=np.int64),
        "step_index": np.asarray(step_indices, dtype=np.int64),
        "weight": np.asarray(weights, dtype=np.float32),
    }
    anchor_npz = run_dir / "target_base_rejected_trajectory_anchor.npz"
    anchor_csv = run_dir / "target_base_rejected_trajectory_anchor.csv"
    save_anchor_arrays(anchor_npz, arrays)
    write_csv_rows(anchor_csv, trajectory_rows)
    loaded = load_trajectory_action_anchor(
        anchor_npz,
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )
    return {
        "target_anchor_npz": anchor_npz,
        "target_anchor_csv": anchor_csv,
        "target_anchor_rows": int(loaded.size),
        "target_anchor_shape": {
            "observation": list(loaded.observation.shape),
            "hidden": list(loaded.hidden.shape),
            "reference_action": list(loaded.reference_action.shape),
        },
        "obs_dim": int(model.obs_dim),
        "hidden_size": int(model.actor_mean.in_features),
        "act_dim": int(model.act_dim),
        "rows_per_event": {str(key): int(value) for key, value in pd.DataFrame(trajectory_rows).groupby("event_index").size().to_dict().items()},
    }


def build_combined_target_base_rejected_anchor(
    *,
    base_combined_anchor_npz: Path,
    target_anchor_npz: Path,
    output_npz: Path,
    target_source_index_offset: int,
    target_family_id: int,
    target_family_total: float,
) -> dict[str, Any]:
    base = load_anchor_arrays(base_combined_anchor_npz)
    target = load_anchor_arrays(target_anchor_npz)
    if base["observation"].shape[1] != target["observation"].shape[1]:
        raise ValueError("observation dimensions do not match")
    if base["hidden"].shape[1] != target["hidden"].shape[1]:
        raise ValueError("hidden dimensions do not match")
    if base["reference_action"].shape[1] != target["reference_action"].shape[1]:
        raise ValueError("reference action dimensions do not match")
    base_sources = np.asarray(base["source_index"], dtype=np.int64)
    target_sources = np.asarray(target["source_index"], dtype=np.int64) + int(target_source_index_offset)
    if set(base_sources.tolist()).intersection(set(target_sources.tolist())):
        raise ValueError("target source_index namespace collides with base anchor")
    base_raw = np.load(base_combined_anchor_npz)
    base_family_id = (
        np.asarray(base_raw["family_id"], dtype=np.int64)
        if "family_id" in base_raw.files
        else np.zeros((base["observation"].shape[0],), dtype=np.int64)
    )
    base_family_weight_total = (
        np.asarray(base_raw["family_weight_total"], dtype=np.float32)
        if "family_weight_total" in base_raw.files
        else np.full((base["observation"].shape[0],), float(np.sum(base["weight"])), dtype=np.float32)
    )
    if int(base_family_id.shape[0]) != int(base["observation"].shape[0]):
        raise ValueError("base family_id row count does not match base anchor")
    if int(base_family_weight_total.shape[0]) != int(base["observation"].shape[0]):
        raise ValueError("base family_weight_total row count does not match base anchor")
    if int(target_family_id) in set(base_family_id.astype(int).tolist()):
        raise ValueError("target family_id collides with base anchor family ids")
    arrays = {
        "observation": np.concatenate([base["observation"], target["observation"]], axis=0).astype(np.float32),
        "hidden": np.concatenate([base["hidden"], target["hidden"]], axis=0).astype(np.float32),
        "reference_action": np.concatenate([base["reference_action"], target["reference_action"]], axis=0).astype(np.float32),
        "source_index": np.concatenate([base_sources, target_sources], axis=0).astype(np.int64),
        "step_index": np.concatenate([base["step_index"], target["step_index"]], axis=0).astype(np.int64),
        "weight": np.concatenate(
            [
                base["weight"],
                normalize_family_weights(target["weight"], family_total=target_family_total),
            ],
            axis=0,
        ).astype(np.float32),
        "family_id": np.concatenate(
            [
                np.asarray(base_family_id, dtype=np.int64),
                np.full((target["observation"].shape[0],), int(target_family_id), dtype=np.int64),
            ],
            axis=0,
        ),
        "family_weight_total": np.concatenate(
            [
                np.asarray(base_family_weight_total, dtype=np.float32),
                np.full((target["observation"].shape[0],), float(target_family_total), dtype=np.float32),
            ],
            axis=0,
        ).astype(np.float32),
    }
    save_anchor_npz(output_npz, arrays)
    validate_anchor_arrays(arrays, label=str(output_npz))
    target_family_weight_sum = float(
        np.asarray(arrays["weight"], dtype=np.float64)[arrays["family_id"] == int(target_family_id)].sum(dtype=np.float64)
    )
    return {
        "combined_anchor_npz": output_npz,
        "base_rows": int(base["observation"].shape[0]),
        "target_rows": int(target["observation"].shape[0]),
        "combined_rows": int(arrays["observation"].shape[0]),
        "target_source_index_offset": int(target_source_index_offset),
        "target_source_min": int(np.min(target_sources)),
        "target_source_max": int(np.max(target_sources)),
        "source_collision": False,
        "target_family_id": int(target_family_id),
        "target_family_total": float(target_family_total),
        "target_family_weight_sum": target_family_weight_sum,
        "target_family_weight_match": bool(
            np.isclose(target_family_weight_sum, float(target_family_total), rtol=1e-6, atol=1e-6)
        ),
    }


def export_materialized_failed_wrong_history_retention(
    *,
    base_checkpoint: Path,
    full_gate_run_dir: Path,
    base_combined_anchor_npz: Path,
    env_config_path: Path,
    max_continuation_steps: int,
    failed_row_weight: float,
    target_source_index_offset: int,
    target_family_id: int,
    target_family_total: float,
    expected_event_count: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    events = collect_failed_events(full_gate_run_dir=full_gate_run_dir, base_checkpoint=base_checkpoint)
    counts = validate_failed_event_registry(events, expected_event_count=expected_event_count)
    target_base_rows = [event for event in events if event["target_class"] == "target_base"]
    family_source_rows = [event for event in events if event["target_class"] == "family_source"]
    write_csv_rows(run_dir / "failed_wrong_history_events.csv", events, fieldnames=EVENT_FIELDNAMES)
    write_csv_rows(run_dir / "target_base_failed_rows.csv", target_base_rows, fieldnames=EVENT_FIELDNAMES)
    write_csv_rows(run_dir / "family_source_failed_rows.csv", family_source_rows, fieldnames=EVENT_FIELDNAMES)

    target_anchor_summary = export_target_base_rejected_trajectory_anchor(
        target_base_rows=target_base_rows,
        base_checkpoint=base_checkpoint,
        env_config_path=env_config_path,
        max_continuation_steps=max_continuation_steps,
        failed_row_weight=failed_row_weight,
        device=device,
        run_dir=run_dir,
    )
    combined_summary = build_combined_target_base_rejected_anchor(
        base_combined_anchor_npz=base_combined_anchor_npz,
        target_anchor_npz=Path(target_anchor_summary["target_anchor_npz"]),
        output_npz=run_dir / "combined_target_base_rejected_anchor.npz",
        target_source_index_offset=target_source_index_offset,
        target_family_id=target_family_id,
        target_family_total=target_family_total,
    )
    loaded_combined = load_trajectory_action_anchor(
        Path(combined_summary["combined_anchor_npz"]),
        device=torch.device("cpu"),
        obs_dim=int(target_anchor_summary["obs_dim"]),
        hidden_size=int(target_anchor_summary["hidden_size"]),
        act_dim=int(target_anchor_summary["act_dim"]),
    )
    short_family_rows_in_training_anchor = any(row["target_class"] == "family_source" for row in target_base_rows)
    by_surface = [
        {
            "surface_tier": str(surface_tier),
            "surface_label": str(surface_label),
            "failed_events": int(len(group)),
            "target_base_events": int((group["target_class"].astype(str) == "target_base").sum()),
            "family_source_events": int((group["target_class"].astype(str) == "family_source").sum()),
            "normal_lost_events": int(group["normal_lost"].astype(bool).sum()),
            "wrong_history_safe_events": int(group["wrong_history_safe"].astype(bool).sum()),
        }
        for (surface_tier, surface_label), group in pd.DataFrame(events).groupby(
            ["surface_tier", "surface_label"], observed=True
        )
    ]
    write_csv_rows(run_dir / "surface_failure_summary.csv", by_surface)
    pass_all = bool(
        counts["failed_event_count"] == int(expected_event_count)
        and counts["normal_lost_events"] == 0
        and counts["wrong_history_safe_events"] == int(expected_event_count)
        and len(target_base_rows) > 0
        and len(family_source_rows) > 0
        and not short_family_rows_in_training_anchor
        and int(loaded_combined.size) == int(combined_summary["combined_rows"])
        and bool(combined_summary["target_family_weight_match"])
    )
    summary = {
        "run_type": "materialized_failed_wrong_history_retention_export",
        "result_class": "materialized_failed_wrong_history_retention_export_pass"
        if pass_all
        else "materialized_failed_wrong_history_retention_export_invalid",
        "base_checkpoint": base_checkpoint,
        "full_gate_run_dir": full_gate_run_dir,
        "base_combined_anchor_npz": base_combined_anchor_npz,
        "env_config": env_config_path,
        "max_continuation_steps": int(max_continuation_steps),
        "failed_row_weight": float(failed_row_weight),
        "target_source_index_offset": int(target_source_index_offset),
        "target_family_id": int(target_family_id),
        "target_family_total": float(target_family_total),
        **counts,
        "target_base_failed_events": int(len(target_base_rows)),
        "family_source_failed_events": int(len(family_source_rows)),
        "short_family_rows_in_training_anchor": bool(short_family_rows_in_training_anchor),
        "target_anchor": target_anchor_summary,
        "combined_anchor": combined_summary,
        "combined_anchor_loaded_rows": int(loaded_combined.size),
        "by_surface": by_surface,
        "failed_events_csv": run_dir / "failed_wrong_history_events.csv",
        "target_base_failed_rows_csv": run_dir / "target_base_failed_rows.csv",
        "family_source_failed_rows_csv": run_dir / "family_source_failed_rows.csv",
        "surface_failure_summary_csv": run_dir / "surface_failure_summary.csv",
        "actor_inputs_changed": False,
        "training_started": False,
        "optimizer_started": False,
        "actor_update_started": False,
        "ppo_used": False,
        "replay_started": False,
        "mining_started": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    if not pass_all:
        raise ValueError(f"M1115 export failed gates; see {run_dir / 'summary.json'}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--full-gate-run-dir", type=Path, default=DEFAULT_FULL_GATE_RUN_DIR)
    parser.add_argument("--base-combined-anchor-npz", type=Path, default=DEFAULT_BASE_COMBINED_ANCHOR)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--failed-row-weight", type=float, default=50.0)
    parser.add_argument("--target-source-index-offset", type=int, default=DEFAULT_TARGET_SOURCE_INDEX_OFFSET)
    parser.add_argument("--target-family-id", type=int, default=DEFAULT_TARGET_FAMILY_ID)
    parser.add_argument("--target-family-total", type=float, default=DEFAULT_TARGET_FAMILY_TOTAL)
    parser.add_argument("--expected-event-count", type=int, default=REQUIRED_EVENT_COUNT)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    summary = export_materialized_failed_wrong_history_retention(
        base_checkpoint=args.base_checkpoint,
        full_gate_run_dir=args.full_gate_run_dir,
        base_combined_anchor_npz=args.base_combined_anchor_npz,
        env_config_path=args.env_config,
        max_continuation_steps=args.max_continuation_steps,
        failed_row_weight=args.failed_row_weight,
        target_source_index_offset=args.target_source_index_offset,
        target_family_id=args.target_family_id,
        target_family_total=args.target_family_total,
        expected_event_count=args.expected_event_count,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(f"result_class={summary['result_class']}")
    print(f"failed_event_count={summary['failed_event_count']}")
    print(f"target_base_failed_events={summary['target_base_failed_events']}")
    print(f"family_source_failed_events={summary['family_source_failed_events']}")
    print(f"target_anchor_rows={summary['target_anchor']['target_anchor_rows']}")
    print(f"combined_anchor_rows={summary['combined_anchor']['combined_rows']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
