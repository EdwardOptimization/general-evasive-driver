"""Export combined active-set trajectory anchors for Candidate B repair."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.intervention_objectives import load_trajectory_action_anchor


DEFAULT_M267_REJECTED_ANCHOR = Path(
    "runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz"
)
DEFAULT_M183_ROW16_NORMAL_ANCHOR = Path(
    "runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.npz"
)
DEFAULT_RUN_DIR = Path("runs/m1037_candidate_b_combined_active_set_anchor_export")
DEFAULT_M183_SOURCE_OFFSET = 1_000_000

REQUIRED_FIELDS = (
    "observation",
    "hidden",
    "reference_action",
    "source_index",
    "step_index",
    "weight",
)

VARIANT_TOTALS: tuple[tuple[str, float, float], ...] = (
    ("balanced", 1.0, 1.0),
    ("row16x4", 1.0, 4.0),
    ("row16x8", 1.0, 8.0),
)


def load_anchor_arrays(path: Path | str) -> dict[str, np.ndarray]:
    data = np.load(Path(path))
    missing = sorted(set(REQUIRED_FIELDS).difference(data.files))
    if missing:
        raise ValueError(f"anchor npz missing fields: {missing}")
    arrays = {
        "observation": np.asarray(data["observation"], dtype=np.float32),
        "hidden": np.asarray(data["hidden"], dtype=np.float32),
        "reference_action": np.asarray(data["reference_action"], dtype=np.float32),
        "source_index": np.asarray(data["source_index"], dtype=np.int64),
        "step_index": np.asarray(data["step_index"], dtype=np.int64),
        "weight": np.asarray(data["weight"], dtype=np.float32),
    }
    validate_anchor_arrays(arrays, label=str(path))
    return arrays


def validate_anchor_arrays(arrays: dict[str, np.ndarray], *, label: str) -> None:
    observation = arrays["observation"]
    hidden = arrays["hidden"]
    reference_action = arrays["reference_action"]
    source_index = arrays["source_index"]
    step_index = arrays["step_index"]
    weight = arrays["weight"]
    if observation.ndim != 2:
        raise ValueError(f"{label} observation must be 2D, got {observation.shape}")
    if hidden.ndim != 2:
        raise ValueError(f"{label} hidden must be 2D, got {hidden.shape}")
    if reference_action.ndim != 2:
        raise ValueError(f"{label} reference_action must be 2D, got {reference_action.shape}")
    rows = int(observation.shape[0])
    if rows < 1:
        raise ValueError(f"{label} anchor must contain at least one row")
    for name, value in (
        ("hidden", hidden),
        ("reference_action", reference_action),
        ("source_index", source_index),
        ("step_index", step_index),
        ("weight", weight),
    ):
        if int(value.shape[0]) != rows:
            raise ValueError(f"{label} {name} row count {value.shape[0]} does not match {rows}")
    for name, value in (
        ("observation", observation),
        ("hidden", hidden),
        ("reference_action", reference_action),
        ("weight", weight),
    ):
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{label} {name} must be finite")
    if float(np.sum(np.clip(weight, 0.0, None), dtype=np.float64)) <= 0.0:
        raise ValueError(f"{label} anchor must have positive total weight")


def normalize_family_weights(weights: np.ndarray, *, family_total: float) -> np.ndarray:
    if not np.isfinite(float(family_total)) or float(family_total) <= 0.0:
        raise ValueError("family_total must be positive and finite")
    clipped = np.clip(np.asarray(weights, dtype=np.float64), 0.0, None)
    total = float(clipped.sum(dtype=np.float64))
    if total <= 0.0:
        raise ValueError("cannot normalize a zero-weight family")
    return (clipped / total * float(family_total)).astype(np.float32)


def build_combined_anchor_arrays(
    *,
    m267_rejected: dict[str, np.ndarray],
    m183_row16_normal: dict[str, np.ndarray],
    m183_source_offset: int,
    m267_family_total: float,
    m183_family_total: float,
) -> dict[str, np.ndarray]:
    if m267_rejected["observation"].shape[1] != m183_row16_normal["observation"].shape[1]:
        raise ValueError("observation dimensions do not match")
    if m267_rejected["hidden"].shape[1] != m183_row16_normal["hidden"].shape[1]:
        raise ValueError("hidden dimensions do not match")
    if m267_rejected["reference_action"].shape[1] != m183_row16_normal["reference_action"].shape[1]:
        raise ValueError("reference_action dimensions do not match")

    m267_sources = np.asarray(m267_rejected["source_index"], dtype=np.int64)
    m183_sources = np.asarray(m183_row16_normal["source_index"], dtype=np.int64) + int(m183_source_offset)
    if set(m267_sources.tolist()).intersection(set(m183_sources.tolist())):
        raise ValueError("combined anchor source_index collision after offset")

    m267_rows = int(m267_rejected["observation"].shape[0])
    m183_rows = int(m183_row16_normal["observation"].shape[0])
    arrays = {
        "observation": np.concatenate(
            [m267_rejected["observation"], m183_row16_normal["observation"]],
            axis=0,
        ).astype(np.float32),
        "hidden": np.concatenate([m267_rejected["hidden"], m183_row16_normal["hidden"]], axis=0).astype(np.float32),
        "reference_action": np.concatenate(
            [m267_rejected["reference_action"], m183_row16_normal["reference_action"]],
            axis=0,
        ).astype(np.float32),
        "source_index": np.concatenate([m267_sources, m183_sources], axis=0).astype(np.int64),
        "step_index": np.concatenate(
            [m267_rejected["step_index"], m183_row16_normal["step_index"]],
            axis=0,
        ).astype(np.int64),
        "weight": np.concatenate(
            [
                normalize_family_weights(m267_rejected["weight"], family_total=m267_family_total),
                normalize_family_weights(m183_row16_normal["weight"], family_total=m183_family_total),
            ],
            axis=0,
        ).astype(np.float32),
        "family_id": np.concatenate(
            [
                np.zeros((m267_rows,), dtype=np.int64),
                np.ones((m183_rows,), dtype=np.int64),
            ],
            axis=0,
        ),
        "family_weight_total": np.concatenate(
            [
                np.full((m267_rows,), float(m267_family_total), dtype=np.float32),
                np.full((m183_rows,), float(m183_family_total), dtype=np.float32),
            ],
            axis=0,
        ),
    }
    validate_anchor_arrays(arrays, label="combined")
    return arrays


def save_anchor_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def _family_weight_sum(arrays: dict[str, np.ndarray], family_id: int) -> float:
    mask = np.asarray(arrays["family_id"], dtype=np.int64) == int(family_id)
    return float(np.asarray(arrays["weight"], dtype=np.float64)[mask].sum(dtype=np.float64))


def _variant_row(
    *,
    variant: str,
    path: Path,
    arrays: dict[str, np.ndarray],
    m267_family_total: float,
    m183_family_total: float,
    m183_source_offset: int,
) -> dict[str, Any]:
    source_values = np.asarray(arrays["source_index"], dtype=np.int64)
    family_id = np.asarray(arrays["family_id"], dtype=np.int64)
    m267_sources = source_values[family_id == 0]
    m183_sources = source_values[family_id == 1]
    source_collision = bool(set(m267_sources.tolist()).intersection(set(m183_sources.tolist())))
    return {
        "variant": variant,
        "path": path,
        "rows": int(arrays["observation"].shape[0]),
        "obs_dim": int(arrays["observation"].shape[1]),
        "hidden_size": int(arrays["hidden"].shape[1]),
        "act_dim": int(arrays["reference_action"].shape[1]),
        "m267_rows": int(np.sum(family_id == 0)),
        "m183_rows": int(np.sum(family_id == 1)),
        "m267_source_min": int(np.min(m267_sources)),
        "m267_source_max": int(np.max(m267_sources)),
        "m183_source_min": int(np.min(m183_sources)),
        "m183_source_max": int(np.max(m183_sources)),
        "m183_source_offset": int(m183_source_offset),
        "source_collision": source_collision,
        "m267_family_total_expected": float(m267_family_total),
        "m183_family_total_expected": float(m183_family_total),
        "m267_family_weight_sum": _family_weight_sum(arrays, 0),
        "m183_family_weight_sum": _family_weight_sum(arrays, 1),
        "weight_sum": float(np.asarray(arrays["weight"], dtype=np.float64).sum(dtype=np.float64)),
    }


def export_combined_active_set_anchors(
    *,
    m267_rejected_anchor_npz: Path,
    m183_row16_normal_anchor_npz: Path,
    run_dir: Path,
    m183_source_offset: int = DEFAULT_M183_SOURCE_OFFSET,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    m267_rejected = load_anchor_arrays(m267_rejected_anchor_npz)
    m183_row16_normal = load_anchor_arrays(m183_row16_normal_anchor_npz)
    rows: list[dict[str, Any]] = []
    variant_paths: dict[str, Path] = {}
    all_valid = True
    for variant, m267_family_total, m183_family_total in VARIANT_TOTALS:
        arrays = build_combined_anchor_arrays(
            m267_rejected=m267_rejected,
            m183_row16_normal=m183_row16_normal,
            m183_source_offset=m183_source_offset,
            m267_family_total=m267_family_total,
            m183_family_total=m183_family_total,
        )
        path = run_dir / f"combined_active_set_anchor_{variant}.npz"
        save_anchor_npz(path, arrays)
        loaded = load_trajectory_action_anchor(
            path,
            device=torch.device("cpu"),
            obs_dim=int(arrays["observation"].shape[1]),
            hidden_size=int(arrays["hidden"].shape[1]),
            act_dim=int(arrays["reference_action"].shape[1]),
        )
        row = _variant_row(
            variant=variant,
            path=path,
            arrays=arrays,
            m267_family_total=m267_family_total,
            m183_family_total=m183_family_total,
            m183_source_offset=m183_source_offset,
        )
        row["loaded_rows"] = int(loaded.size)
        row["loadable"] = True
        row["m267_family_weight_match"] = bool(
            np.isclose(row["m267_family_weight_sum"], m267_family_total, rtol=1e-6, atol=1e-6)
        )
        row["m183_family_weight_match"] = bool(
            np.isclose(row["m183_family_weight_sum"], m183_family_total, rtol=1e-6, atol=1e-6)
        )
        row["row_count_expected"] = int(m267_rejected["observation"].shape[0] + m183_row16_normal["observation"].shape[0])
        row["row_count_match"] = bool(row["rows"] == row["row_count_expected"])
        all_valid = all_valid and not row["source_collision"] and row["m267_family_weight_match"] and row[
            "m183_family_weight_match"
        ] and row["row_count_match"]
        rows.append(row)
        variant_paths[variant] = path

    summary_csv = run_dir / "combined_active_set_anchor_summary.csv"
    write_csv_rows(summary_csv, rows)
    expected_rows = int(m267_rejected["observation"].shape[0] + m183_row16_normal["observation"].shape[0])
    summary = {
        "run_type": "candidate_b_combined_active_set_anchor_export",
        "m267_rejected_anchor_npz": m267_rejected_anchor_npz,
        "m183_row16_normal_anchor_npz": m183_row16_normal_anchor_npz,
        "m183_source_offset": int(m183_source_offset),
        "m267_rows": int(m267_rejected["observation"].shape[0]),
        "m183_rows": int(m183_row16_normal["observation"].shape[0]),
        "combined_rows_expected": expected_rows,
        "variant_count": len(rows),
        "variants": rows,
        "variant_paths": variant_paths,
        "summary_csv": summary_csv,
        "all_variants_loadable": all(bool(row["loadable"]) for row in rows),
        "all_source_namespaced": all(not bool(row["source_collision"]) for row in rows),
        "all_family_weights_match": all(
            bool(row["m267_family_weight_match"]) and bool(row["m183_family_weight_match"]) for row in rows
        ),
        "all_row_counts_match": all(bool(row["row_count_match"]) for row in rows),
        "actor_inputs_changed": False,
        "training_started": False,
        "optimizer_started": False,
        "repair_used": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": "candidate_b_combined_active_set_anchor_export_pass"
        if all_valid
        else "candidate_b_combined_active_set_anchor_export_invalid",
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Candidate B combined active-set trajectory anchors.")
    parser.add_argument("--m267-rejected-anchor-npz", type=Path, default=DEFAULT_M267_REJECTED_ANCHOR)
    parser.add_argument("--m183-row16-normal-anchor-npz", type=Path, default=DEFAULT_M183_ROW16_NORMAL_ANCHOR)
    parser.add_argument("--m183-source-offset", type=int, default=DEFAULT_M183_SOURCE_OFFSET)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    summary = export_combined_active_set_anchors(
        m267_rejected_anchor_npz=args.m267_rejected_anchor_npz,
        m183_row16_normal_anchor_npz=args.m183_row16_normal_anchor_npz,
        m183_source_offset=args.m183_source_offset,
        run_dir=args.run_dir,
    )
    print(f"result_class={summary['result_class']}")
    print(f"variant_count={summary['variant_count']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
