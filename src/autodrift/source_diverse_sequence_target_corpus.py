"""Build a source-balanced sequence target corpus from accepted candidates."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_conditioned_grounded_target_miner import _diversity, load_boundary_source_rows
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.combined_shape_source_diversity_expansion import default_shape_grid_specs
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import (
    SurfaceConfig,
    _hidden_array,
    parse_surface_config,
    request_steps_for_target_rows,
    variant_hidden_for_row,
)
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import _snapshot, collect_requested_outcome_snapshots
from autodrift.sequence_target_miner import collect_base_action_sequence, write_sequence_target_corpus
from autodrift.train_ppo import resolve_device
from autodrift.trust_projected_sequence_shape import build_projected_sequence_candidates


TRAIN_SOURCE_IDS = frozenset({13, 14, 5, 30, 0, 8})
SOURCE_HOLDOUT_VALIDATION_IDS = frozenset({20, 32, 7})


def split_for_source(source_index: int) -> str:
    source_id = int(source_index)
    if source_id in TRAIN_SOURCE_IDS:
        return "train"
    if source_id in SOURCE_HOLDOUT_VALIDATION_IDS:
        return "source_holdout_validation"
    return "unassigned"


def _candidate_sort_key(row: pd.Series) -> tuple[float, float, float, float, float]:
    return (
        -float(row["margin_improvement"]),
        -float(row["risk_improvement"]),
        float(row["sequence_mean_l2"]),
        float(row["sequence_max_l2"]),
        float(row["max_delta_delta_l2"]),
    )


def select_balanced_candidates(
    accepted_candidates: pd.DataFrame,
    *,
    max_rows_per_source: int,
    max_rows_per_source_grid: int,
    max_rows_per_source_family: int,
    max_rows_per_source_sequence_length: int,
) -> pd.DataFrame:
    required = {
        "source_index",
        "grid_name",
        "family",
        "sequence_length",
        "margin_improvement",
        "risk_improvement",
        "sequence_mean_l2",
        "sequence_max_l2",
        "max_delta_delta_l2",
    }
    missing = sorted(required.difference(accepted_candidates.columns))
    if missing:
        raise ValueError("accepted candidates missing columns: " + ", ".join(missing))

    selected_rows: list[dict[str, Any]] = []
    for source_index, source_frame in accepted_candidates.groupby("source_index", observed=True):
        source_rows = source_frame.copy()
        source_rows["_rank_key"] = source_rows.apply(_candidate_sort_key, axis=1)
        source_rows = source_rows.sort_values("_rank_key").drop(columns=["_rank_key"])
        grid_counts: dict[str, int] = defaultdict(int)
        family_counts: dict[str, int] = defaultdict(int)
        length_counts: dict[int, int] = defaultdict(int)
        source_selected = 0
        for _, row in source_rows.iterrows():
            grid = str(row["grid_name"])
            family = str(row["family"])
            length = int(row["sequence_length"])
            if source_selected >= int(max_rows_per_source):
                break
            if grid_counts[grid] >= int(max_rows_per_source_grid):
                continue
            if family_counts[family] >= int(max_rows_per_source_family):
                continue
            if length_counts[length] >= int(max_rows_per_source_sequence_length):
                continue
            output = dict(row)
            output["split"] = split_for_source(int(source_index))
            selected_rows.append(output)
            source_selected += 1
            grid_counts[grid] += 1
            family_counts[family] += 1
            length_counts[length] += 1
    selected = pd.DataFrame(selected_rows)
    if selected.empty:
        raise ValueError("balanced selection produced no rows")
    return selected.sort_values(["source_index", "split", "grid_name", "margin_improvement"], ascending=[True, True, True, False]).reset_index(drop=True)


def add_source_balanced_weights(selected: pd.DataFrame) -> pd.DataFrame:
    output = selected.copy()
    source_count = int(output["source_index"].nunique())
    if source_count <= 0:
        raise ValueError("cannot weight empty source set")
    source_weights = {int(source): 1.0 / source_count for source in output["source_index"].astype(int).unique()}
    counts = output["source_index"].astype(int).value_counts().to_dict()
    output["corpus_weight"] = [
        float(source_weights[int(source)] / counts[int(source)])
        for source in output["source_index"].astype(int).tolist()
    ]
    return output


def _source_rows_for_selection(source_rows: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    source_ids = set(selected["source_index"].astype(int).tolist())
    rows = source_rows[source_rows["source_index"].astype(int).isin(source_ids)].copy()
    return rows.drop_duplicates("source_index").reset_index(drop=True)


def source_balance_summary(selected: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_index, group in selected.groupby("source_index", observed=True):
        rows.append(
            {
                "source_index": int(source_index),
                "split": str(group["split"].iloc[0]),
                "rows": int(len(group)),
                "weight_sum": float(group["corpus_weight"].sum()),
                "grid_names": ";".join(sorted(group["grid_name"].astype(str).unique())),
                "families": ";".join(sorted(group["family"].astype(str).unique())),
                "sequence_lengths": ";".join(str(int(value)) for value in sorted(group["sequence_length"].astype(int).unique())),
                "target": str(group["target"].iloc[0]),
                "surface": str(group["surface"].iloc[0]),
                "variant": str(group["variant"].iloc[0]),
            }
        )
    return rows


def _grid_spec_by_name() -> dict[str, Any]:
    return {spec.name: spec for spec in default_shape_grid_specs()}


def materialize_candidate_sequence(row: pd.Series, base_sequence: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    specs = _grid_spec_by_name()
    grid_name = str(row["grid_name"])
    if grid_name not in specs:
        raise ValueError(f"unknown grid_name: {grid_name}")
    spec = specs[grid_name]
    target_candidate_id = int(row["candidate_id"])
    candidate_id_offset = 0
    for sequence_length in spec.sequence_lengths:
        base = np.asarray(base_sequence[: int(sequence_length)], dtype=np.float32)
        candidates = build_projected_sequence_candidates(
            base,
            steer_deltas=spec.steer_deltas,
            throttle_deltas=spec.throttle_deltas,
            brake_deltas=spec.brake_deltas,
            families=spec.families,
            per_step_action_l2=0.10,
            sequence_mean_l2_limit=0.08,
            sequence_max_l2_limit=0.10,
            max_delta_delta_l2_limit=0.08,
        )
        for projected in candidates:
            candidate = projected.candidate
            candidate_id = int(candidate_id_offset + candidate.candidate_id)
            if (
                candidate_id == target_candidate_id
                and int(candidate.sequence_length) == int(row["sequence_length"])
                and str(candidate.family) == str(row["family"])
            ):
                return candidate.action_sequence.copy(), base.copy()
        candidate_id_offset += len(candidates)
    raise ValueError(
        f"could not materialize candidate source={row['source_index']} grid={grid_name} "
        f"candidate_id={target_candidate_id}"
    )


def _selected_source_rows_with_metadata(source_rows: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    keys = ["source_index", "coupling_row_index", "surface", "target", "variant", "left_seed", "left_step", "right_seed", "right_step"]
    selected_keys = selected[keys].drop_duplicates()
    merged = selected_keys.merge(source_rows, on=keys, how="left", suffixes=("", "_source"))
    if merged["capability_z_distance"].isna().any():
        missing = merged[merged["capability_z_distance"].isna()]["source_index"].astype(int).tolist()
        raise ValueError(f"missing source metadata for selected sources: {missing}")
    return merged


def materialize_balanced_corpus(
    *,
    model: Any,
    selected: pd.DataFrame,
    source_rows: pd.DataFrame,
    surface_configs: tuple[SurfaceConfig, ...],
    delay_steps: int,
    device: Any,
) -> dict[str, list[Any]]:
    selected_sources = _selected_source_rows_with_metadata(source_rows, selected)
    selected_by_source = {int(row["source_index"]): row for _, row in selected_sources.iterrows()}
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = sorted(set(selected_sources["surface"].astype(str)).difference(surface_config_by_name))
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    source_context: dict[int, dict[str, Any]] = {}
    for surface, surface_rows in selected_sources.groupby("surface", observed=True):
        env_config = load_env_config(surface_config_by_name[str(surface)])
        max_len_by_source = selected.groupby("source_index")["sequence_length"].max().astype(int).to_dict()
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=request_steps_for_target_rows(surface_rows.reset_index(drop=True), delay_steps=delay_steps),
            device=device,
        )
        for _, source_row in surface_rows.reset_index(drop=True).iterrows():
            source_index = int(source_row["source_index"])
            left = _snapshot(snapshots, int(source_row["left_seed"]), int(source_row["left_step"]))
            variant_hidden = variant_hidden_for_row(row=source_row, snapshots=snapshots, delay_steps=delay_steps).detach().clone()
            variant_base_action, _ = deterministic_action_from_hidden(model, left.observation, variant_hidden, device)
            base_sequence = collect_base_action_sequence(
                model=model,
                snapshot=left,
                sequence_length=int(max_len_by_source[source_index]),
                device=device,
            )
            source_context[source_index] = {
                "observation": np.asarray(left.observation, dtype=np.float32).copy(),
                "normal_hidden": _hidden_array(left.hidden.detach().clone()),
                "variant_hidden": _hidden_array(variant_hidden),
                "variant_base_action": np.asarray(variant_base_action, dtype=np.float32).copy(),
                "base_sequence": base_sequence,
            }

    corpus: dict[str, list[Any]] = {
        "observations": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "target_action_sequences": [],
        "normal_base_action_sequences": [],
        "variant_base_actions": [],
        "weights": [],
        "row_ids": [],
        "source_indices": [],
        "sequence_lengths": [],
    }
    for row_id, row in selected.reset_index(drop=True).iterrows():
        source_index = int(row["source_index"])
        _ = selected_by_source[source_index]
        context = source_context[source_index]
        target_sequence, base_sequence = materialize_candidate_sequence(row, context["base_sequence"])
        corpus["observations"].append(context["observation"])
        corpus["normal_hidden"].append(context["normal_hidden"])
        corpus["variant_hidden"].append(context["variant_hidden"])
        corpus["target_action_sequences"].append(target_sequence)
        corpus["normal_base_action_sequences"].append(base_sequence)
        corpus["variant_base_actions"].append(context["variant_base_action"])
        corpus["weights"].append(float(row["corpus_weight"]))
        corpus["row_ids"].append(int(row_id))
        corpus["source_indices"].append(source_index)
        corpus["sequence_lengths"].append(int(row["sequence_length"]))
    return corpus


def run_source_diverse_sequence_target_corpus(
    *,
    accepted_sequences_csv: Path,
    checkpoint_path: Path,
    source_table_csv: Path,
    surface_configs: tuple[SurfaceConfig, ...],
    max_rows_per_source: int,
    max_rows_per_source_grid: int,
    max_rows_per_source_family: int,
    max_rows_per_source_sequence_length: int,
    delay_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    accepted = pd.read_csv(accepted_sequences_csv)
    selected = select_balanced_candidates(
        accepted,
        max_rows_per_source=max_rows_per_source,
        max_rows_per_source_grid=max_rows_per_source_grid,
        max_rows_per_source_family=max_rows_per_source_family,
        max_rows_per_source_sequence_length=max_rows_per_source_sequence_length,
    )
    selected = add_source_balanced_weights(selected)
    source_rows = load_boundary_source_rows(source_table_csv)
    selected_source_rows = _source_rows_for_selection(source_rows, selected)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    corpus = materialize_balanced_corpus(
        model=model,
        selected=selected,
        source_rows=source_rows,
        surface_configs=surface_configs,
        delay_steps=delay_steps,
        device=resolved_device,
    )

    npz_path = run_dir / "balanced_sequence_target_corpus.npz"
    write_sequence_target_corpus(
        output_npz=npz_path,
        observations=corpus["observations"],
        normal_hidden=corpus["normal_hidden"],
        variant_hidden=corpus["variant_hidden"],
        target_action_sequences=corpus["target_action_sequences"],
        normal_base_action_sequences=corpus["normal_base_action_sequences"],
        variant_base_actions=corpus["variant_base_actions"],
        weights=corpus["weights"],
        row_ids=corpus["row_ids"],
        source_indices=corpus["source_indices"],
        sequence_lengths=corpus["sequence_lengths"],
    )

    selected_rows = selected.to_dict(orient="records")
    top1 = (
        selected.sort_values(["source_index", "margin_improvement"], ascending=[True, False])
        .groupby("source_index", observed=True)
        .head(1)
        .to_dict(orient="records")
    )
    topk = (
        selected.sort_values(["source_index", "margin_improvement"], ascending=[True, False])
        .groupby("source_index", observed=True)
        .head(5)
        .to_dict(orient="records")
    )
    balance = source_balance_summary(selected)
    write_csv_rows(run_dir / "balanced_sequence_targets.csv", selected_rows)
    write_csv_rows(run_dir / "top1_per_source.csv", top1)
    write_csv_rows(run_dir / "topk_per_source.csv", topk)
    write_csv_rows(run_dir / "source_balance_summary.csv", balance)

    selected_diversity = _diversity(selected_source_rows)
    summary = {
        "run_type": "source_diverse_sequence_target_corpus",
        "accepted_sequences_csv": accepted_sequences_csv,
        "checkpoint": checkpoint_path,
        "source_table_csv": source_table_csv,
        "selected_rows": int(len(selected)),
        "selected_sources": int(selected_diversity["rows"]),
        "selected_physical_pairs": int(selected_diversity["unique_physical_pairs"]),
        "selected_left_seeds": int(selected_diversity["unique_left_seeds"]),
        "selected_surfaces": int(selected_diversity["surfaces"]),
        "selected_targets": int(selected_diversity["targets"]),
        "selected_variants": int(selected_diversity["variants"]),
        "rows_by_source": {str(k): int(v) for k, v in selected["source_index"].value_counts().to_dict().items()},
        "rows_by_grid": {str(k): int(v) for k, v in selected["grid_name"].value_counts().to_dict().items()},
        "rows_by_split": {str(k): int(v) for k, v in selected["split"].value_counts().to_dict().items()},
        "max_rows_per_source": int(selected["source_index"].value_counts().max()),
        "max_rows_per_source_grid": int(selected.groupby(["source_index", "grid_name"], observed=True).size().max()),
        "source_balanced_weights": bool(np.allclose(selected.groupby("source_index")["corpus_weight"].sum(), 1.0 / selected["source_index"].nunique())),
        "sequence_npz_written": npz_path.exists(),
        "balanced_sequence_targets_csv": run_dir / "balanced_sequence_targets.csv",
        "balanced_sequence_target_corpus_npz": npz_path,
        "source_balance_summary_csv": run_dir / "source_balance_summary.csv",
        "diagnostic_only": True,
        "training_started": False,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build source-diverse balanced sequence target corpus.")
    parser.add_argument("--accepted-sequences", type=Path, required=True)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--source-table", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--max-rows-per-source", type=int, default=64)
    parser.add_argument("--max-rows-per-source-grid", type=int, default=32)
    parser.add_argument("--max-rows-per-source-family", type=int, default=16)
    parser.add_argument("--max-rows-per-source-sequence-length", type=int, default=24)
    parser.add_argument("--delay-steps", type=int, default=2)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="source_diverse_sequence_target_corpus")
    summary = run_source_diverse_sequence_target_corpus(
        accepted_sequences_csv=args.accepted_sequences,
        checkpoint_path=args.checkpoint_policy.path,
        source_table_csv=args.source_table,
        surface_configs=tuple(args.surface_config),
        max_rows_per_source=args.max_rows_per_source,
        max_rows_per_source_grid=args.max_rows_per_source_grid,
        max_rows_per_source_family=args.max_rows_per_source_family,
        max_rows_per_source_sequence_length=args.max_rows_per_source_sequence_length,
        delay_steps=args.delay_steps,
        device=args.device,
        run_dir=run_dir,
    )
    print(f"run_dir={run_dir}")
    print(f"selected_rows={summary['selected_rows']}")
    print(f"sequence_npz_written={summary['sequence_npz_written']}")


if __name__ == "__main__":
    main()
