"""Export source-labeled M1069 failed-row projection corpus."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.current_family_conflict_corpus import conflict_row_weight
from autodrift.intervention_objectives import load_current_family_conflict_snippets
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.train_ppo import resolve_device


BASE_CHECKPOINT = Path("runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt")
RAW_CHECKPOINT = Path("runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt")
SHORT_61050_CHECKPOINT = Path("runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt")
SHORT_61051_CHECKPOINT = Path("runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt")
DEFAULT_RUN_DIR = Path("runs/m1072_medium_ppo_failed_row_projection_corpus")
DEFAULT_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")


@dataclass(frozen=True)
class FailedRowSource:
    surface: str
    source_policy: str
    source_checkpoint: Path
    boundary_npz: Path
    boundary_csv: Path
    replay_rows_csv: Path
    row_ids: tuple[int, ...]


FAILED_ROW_SOURCES: tuple[FailedRowSource, ...] = (
    FailedRowSource(
        surface="m183_m168",
        source_policy="m399_base",
        source_checkpoint=BASE_CHECKPOINT,
        boundary_npz=Path("runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz"),
        boundary_csv=Path("runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv"),
        replay_rows_csv=Path(
            "runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/full_gates/"
            "m183_m168_replay/boundary_replay_rows.csv"
        ),
        row_ids=(9, 10),
    ),
    FailedRowSource(
        surface="m183_m170",
        source_policy="m399_base",
        source_checkpoint=BASE_CHECKPOINT,
        boundary_npz=Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz"),
        boundary_csv=Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv"),
        replay_rows_csv=Path(
            "runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/full_gates/"
            "m183_m170_replay/boundary_replay_rows.csv"
        ),
        row_ids=(10,),
    ),
    FailedRowSource(
        surface="m267_m264",
        source_policy="m399_base",
        source_checkpoint=BASE_CHECKPOINT,
        boundary_npz=Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz"),
        boundary_csv=Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv"),
        replay_rows_csv=Path(
            "runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/full_gates/"
            "m267_m264_replay/boundary_replay_rows.csv"
        ),
        row_ids=(15,),
    ),
    FailedRowSource(
        surface="short61049_family_intersection",
        source_policy="short61049",
        source_checkpoint=BASE_CHECKPOINT,
        boundary_npz=Path("runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.npz"),
        boundary_csv=Path("runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv"),
        replay_rows_csv=Path(
            "runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/family_intersection_public_gate/"
            "replay_gates/short61049_to_m964_direction_target_a0_15/boundary_replay_rows.csv"
        ),
        row_ids=(16, 22, 23, 24),
    ),
    FailedRowSource(
        surface="short61050_family_intersection",
        source_policy="short61050",
        source_checkpoint=SHORT_61050_CHECKPOINT,
        boundary_npz=Path("runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.npz"),
        boundary_csv=Path("runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv"),
        replay_rows_csv=Path(
            "runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/family_intersection_public_gate/"
            "replay_gates/short61050_to_m964_direction_target_a0_15/boundary_replay_rows.csv"
        ),
        row_ids=(16, 17, 23, 24, 25, 26),
    ),
    FailedRowSource(
        surface="short61051_family_intersection",
        source_policy="short61051",
        source_checkpoint=SHORT_61051_CHECKPOINT,
        boundary_npz=Path("runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.npz"),
        boundary_csv=Path("runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv"),
        replay_rows_csv=Path(
            "runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/family_intersection_public_gate/"
            "replay_gates/short61051_to_m964_direction_target_a0_15/boundary_replay_rows.csv"
        ),
        row_ids=(16, 17, 23, 24, 25, 26),
    ),
    FailedRowSource(
        surface="m317_continuity_surface",
        source_policy="m399_base",
        source_checkpoint=BASE_CHECKPOINT,
        boundary_npz=Path("runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.npz"),
        boundary_csv=Path("runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv"),
        replay_rows_csv=Path(
            "runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/"
            "source_diverse_protected_diagnostic/replay_gates/m317_continuity_surface/boundary_replay_rows.csv"
        ),
        row_ids=(15,),
    ),
    FailedRowSource(
        surface="m314_continuity_surface",
        source_policy="m399_base",
        source_checkpoint=BASE_CHECKPOINT,
        boundary_npz=Path("runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.npz"),
        boundary_csv=Path("runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv"),
        replay_rows_csv=Path(
            "runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/"
            "source_diverse_protected_diagnostic/replay_gates/m314_continuity_surface/boundary_replay_rows.csv"
        ),
        row_ids=(15,),
    ),
)


def _action_array(action: np.ndarray) -> np.ndarray:
    value = np.asarray(action, dtype=np.float32).reshape(-1)
    if value.shape != (3,):
        raise ValueError(f"action must have shape (3,), got {value.shape}")
    return np.clip(value, -1.0, 1.0).astype(np.float32)


def _replay_row(frame: pd.DataFrame, *, checkpoint: Path, row_id: int) -> pd.Series:
    rows = frame[
        frame["checkpoint"].astype(str).eq(str(checkpoint))
        & frame["row_id"].astype(int).eq(int(row_id))
    ]
    if len(rows) != 1:
        raise ValueError(f"expected one replay row for checkpoint={checkpoint} row_id={row_id}, got {len(rows)}")
    return rows.iloc[0]


def _boundary_index(frame: pd.DataFrame, *, row_id: int) -> int:
    matches = frame.index[frame["row_id"].astype(int).eq(int(row_id))].tolist()
    if len(matches) != 1:
        raise ValueError(f"expected one boundary row for row_id={row_id}, got {len(matches)}")
    return int(matches[0])


def _csv_bool(value: Any) -> bool:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise ValueError(f"cannot parse boolean value {value!r}")


def export_failed_row_projection_corpus(
    *,
    run_dir: Path,
    device: str,
    margin_floor: float,
    max_weight: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)

    observations: list[np.ndarray] = []
    preferred_hiddens: list[np.ndarray] = []
    rejected_hiddens: list[np.ndarray] = []
    preferred_actions: list[np.ndarray] = []
    rejected_actions: list[np.ndarray] = []
    weights: list[float] = []
    row_ids: list[int] = []
    boundary_margins: list[float] = []
    source_indices: list[int] = []
    surface_indices: list[int] = []
    map_rows: list[dict[str, Any]] = []
    model_cache: dict[str, Any] = {}

    for surface_index, source in enumerate(FAILED_ROW_SOURCES):
        data = np.load(source.boundary_npz)
        frame = pd.read_csv(source.boundary_csv)
        replay = pd.read_csv(source.replay_rows_csv)
        model_key = str(source.source_checkpoint)
        if model_key not in model_cache:
            model, _ = load_actor_critic_checkpoint(source.source_checkpoint, device=str(resolved_device))
            model.eval()
            model_cache[model_key] = model
        model = model_cache[model_key]

        for row_id in source.row_ids:
            index = _boundary_index(frame, row_id=row_id)
            source_replay_row = _replay_row(replay, checkpoint=source.source_checkpoint, row_id=row_id)
            raw_replay_row = _replay_row(replay, checkpoint=RAW_CHECKPOINT, row_id=row_id)
            observation = np.asarray(data["observation"][index], dtype=np.float32)
            preferred_hidden = np.asarray(data["preferred_hidden"][index], dtype=np.float32)
            rejected_hidden = np.asarray(data["rejected_hidden"][index], dtype=np.float32)
            preferred_action, _ = deterministic_action_from_hidden(
                model,
                observation,
                torch.as_tensor(preferred_hidden, dtype=torch.float32, device=resolved_device).unsqueeze(0),
                resolved_device,
            )
            rejected_action, _ = deterministic_action_from_hidden(
                model,
                observation,
                torch.as_tensor(rejected_hidden, dtype=torch.float32, device=resolved_device).unsqueeze(0),
                resolved_device,
            )
            source_weight = float(np.asarray(data["weight"], dtype=np.float32)[index])
            raw_wrong_margin = float(raw_replay_row["wrong_history_margin"])
            source_wrong_margin = float(source_replay_row["wrong_history_margin"])
            weight = conflict_row_weight(
                boundary_margin=raw_wrong_margin,
                source_weight=source_weight,
                margin_floor=margin_floor,
                max_weight=max_weight,
            )
            global_row_id = len(row_ids)
            observations.append(observation.copy())
            preferred_hiddens.append(preferred_hidden.copy())
            rejected_hiddens.append(rejected_hidden.copy())
            preferred_actions.append(_action_array(preferred_action))
            rejected_actions.append(_action_array(rejected_action))
            weights.append(float(weight))
            row_ids.append(int(row_id))
            boundary_margins.append(float(raw_wrong_margin))
            source_indices.append(int(global_row_id))
            surface_indices.append(int(surface_index))
            source_row = frame.iloc[index]
            map_rows.append(
                {
                    "global_row_id": int(global_row_id),
                    "surface_index": int(surface_index),
                    "surface": source.surface,
                    "source_policy": source.source_policy,
                    "source_checkpoint": str(source.source_checkpoint),
                    "boundary_npz": str(source.boundary_npz),
                    "boundary_csv": str(source.boundary_csv),
                    "replay_rows_csv": str(source.replay_rows_csv),
                    "row_id": int(row_id),
                    "source_index": int(index),
                    "target": str(source_row.get("target", "")),
                    "physical_pair_key": str(source_row.get("physical_pair_key", "")),
                    "left_step": int(source_row.get("left_step", -1)),
                    "right_step": int(source_row.get("right_step", -1)),
                    "source_wrong_history_success": _csv_bool(source_replay_row["wrong_history_success"]),
                    "source_wrong_history_margin": source_wrong_margin,
                    "raw_wrong_history_success": _csv_bool(raw_replay_row["wrong_history_success"]),
                    "raw_wrong_history_margin": raw_wrong_margin,
                    "raw_normal_success": _csv_bool(raw_replay_row["normal_success"]),
                    "raw_normal_margin": float(raw_replay_row["normal_margin"]),
                    "source_weight": source_weight,
                    "weight": float(weight),
                    "preferred_anchor_steer": float(preferred_action[0]),
                    "preferred_anchor_throttle": float(preferred_action[1]),
                    "preferred_anchor_brake": float(preferred_action[2]),
                    "rejected_anchor_steer": float(rejected_action[0]),
                    "rejected_anchor_throttle": float(rejected_action[1]),
                    "rejected_anchor_brake": float(rejected_action[2]),
                }
            )

    corpus_npz = run_dir / "current_family_conflict_corpus.npz"
    np.savez_compressed(
        corpus_npz,
        observation=np.asarray(observations, dtype=np.float32),
        preferred_hidden=np.asarray(preferred_hiddens, dtype=np.float32),
        rejected_hidden=np.asarray(rejected_hiddens, dtype=np.float32),
        preferred_anchor_action=np.asarray(preferred_actions, dtype=np.float32),
        rejected_boundary_action=np.asarray(rejected_actions, dtype=np.float32),
        weight=np.asarray(weights, dtype=np.float32),
        row_id=np.asarray(row_ids, dtype=np.int64),
        boundary_margin=np.asarray(boundary_margins, dtype=np.float32),
        source_index=np.asarray(source_indices, dtype=np.int64),
        surface_index=np.asarray(surface_indices, dtype=np.int64),
    )
    loaded = load_current_family_conflict_snippets(
        corpus_npz,
        device=resolved_device,
        obs_dim=int(model_cache[str(BASE_CHECKPOINT)].obs_dim),
        hidden_size=int(model_cache[str(BASE_CHECKPOINT)].actor_mean.in_features),
        act_dim=int(model_cache[str(BASE_CHECKPOINT)].act_dim),
    )
    failed_row_map_csv = run_dir / "failed_row_map.csv"
    write_csv_rows(failed_row_map_csv, map_rows)
    surface_counts: dict[str, int] = {}
    for row in map_rows:
        surface = str(row["surface"])
        surface_counts[surface] = surface_counts.get(surface, 0) + 1
    summary = {
        "run_type": "medium_ppo_failed_row_projection_corpus",
        "rows": int(loaded.size),
        "surface_count": int(len(surface_counts)),
        "surface_counts": surface_counts,
        "source_policy_count": int(len({row["source_policy"] for row in map_rows})),
        "source_checkpoint_count": int(len({row["source_checkpoint"] for row in map_rows})),
        "corpus_npz": corpus_npz,
        "failed_row_map_csv": failed_row_map_csv,
        "margin_floor": float(margin_floor),
        "max_weight": float(max_weight),
        "weight_sum": float(sum(weights)),
        "raw_wrong_margin_min": float(min(boundary_margins)),
        "raw_wrong_margin_max": float(max(boundary_margins)),
        "contract": {
            "rows": int(loaded.size),
            "obs_dim": int(model_cache[str(BASE_CHECKPOINT)].obs_dim),
            "hidden_dim": int(model_cache[str(BASE_CHECKPOINT)].actor_mean.in_features),
            "act_dim": int(model_cache[str(BASE_CHECKPOINT)].act_dim),
        },
        "actor_inputs_changed": False,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "result_class": "medium_ppo_failed_row_projection_corpus_pass",
        "failure_types": ["none"],
        "next_blocker": "medium_ppo_repair_projection_probe_design",
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--margin-floor", type=float, default=1.0e-4)
    parser.add_argument("--max-weight", type=float, default=20.0)
    args = parser.parse_args()
    summary = export_failed_row_projection_corpus(
        run_dir=args.run_dir,
        device=args.device,
        margin_floor=args.margin_floor,
        max_weight=args.max_weight,
    )
    print(f"result_class={summary['result_class']}")
    print(f"rows={summary['rows']} surfaces={summary['surface_count']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
