"""Export branch-split old-key hard guards for projected recovery repair."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.active_set_radius_anchor import old_key_case_id
from autodrift.artifacts import write_csv_rows, write_json
from autodrift.critical_key_replay_guard import CheckpointPolicy, parse_checkpoint_policy
from autodrift.old_key_replay_failure_trajectory_anchor import (
    export_old_key_replay_failure_trajectory_anchor,
)


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _load_npz_arrays(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    required = {"observation", "hidden", "reference_action", "source_index", "step_index", "weight"}
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"anchor npz missing fields: {missing}")
    arrays = {name: np.asarray(data[name]) for name in required}
    if "radius" in data.files:
        arrays["radius"] = np.asarray(data["radius"], dtype=np.float32)
    return arrays


def branch_for_failed_guard_row(row: pd.Series | dict[str, Any]) -> str:
    if _truthy(row.get("candidate_normal_success_regression", False)):
        return "normal"
    if _truthy(row.get("candidate_normal_success", False)) and float(row["candidate_wrong_history_margin"]) > 0.0:
        return "wrong_history"
    return "wrong_history"


def build_branch_split_failed_rows(
    *,
    guard_results_csv: Path,
    baseline_policy: str,
    candidate_policy: str,
) -> pd.DataFrame:
    frame = pd.read_csv(guard_results_csv)
    required = {
        "policy",
        "key",
        "accepted",
        "normal_success",
        "normal_margin",
        "wrong_history_margin",
        "source_condition",
        "source_step",
        "paired_step",
        "target_obstacle_distance",
        "relocated_obstacle_body_y",
        "relocated_obstacle_half_width",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"guard results missing columns: {missing}")
    base = frame[frame["policy"].astype(str).eq(str(baseline_policy))].copy()
    candidate = frame[frame["policy"].astype(str).eq(str(candidate_policy))].copy()
    if base.empty:
        raise ValueError(f"no baseline rows for policy {baseline_policy!r}")
    if candidate.empty:
        raise ValueError(f"no candidate rows for policy {candidate_policy!r}")
    join_keys = [
        "key",
        "source_condition",
        "source_step",
        "paired_step",
        "target_obstacle_distance",
        "relocated_obstacle_body_y",
        "relocated_obstacle_half_width",
    ]
    merged = candidate.merge(
        base[join_keys + ["normal_success"]].rename(columns={"normal_success": "baseline_normal_success"}),
        on=join_keys,
        how="left",
    )
    failed = merged[~merged["accepted"].map(_truthy)].copy()
    if failed.empty:
        raise ValueError("candidate has no failed old-key rows")
    failed["candidate_normal_success"] = failed["normal_success"].map(_truthy)
    failed["baseline_normal_success_bool"] = failed["baseline_normal_success"].map(_truthy)
    failed["candidate_normal_success_regression"] = (
        failed["baseline_normal_success_bool"] & ~failed["candidate_normal_success"]
    )
    failed["candidate_wrong_history_margin"] = failed["wrong_history_margin"].astype(float)
    failed["case_id"] = failed.apply(old_key_case_id, axis=1)
    failed["branch"] = failed.apply(branch_for_failed_guard_row, axis=1)
    return failed.reset_index(drop=True)


def save_branch_split_failed_rows(frame: pd.DataFrame, path: Path) -> None:
    rows = frame.to_dict(orient="records")
    write_csv_rows(path, rows)


def combine_base_and_branch_anchors(
    *,
    base_anchor_npz: Path,
    branch_anchor_npz: Path,
    branch_anchor_csv: Path,
    output_npz: Path,
    output_sources_csv: Path,
    branch_radius: float,
) -> dict[str, Any]:
    base = _load_npz_arrays(base_anchor_npz)
    branch = _load_npz_arrays(branch_anchor_npz)
    base_rows = int(base["observation"].shape[0])
    branch_rows = int(branch["observation"].shape[0])
    if branch_rows < 1:
        raise ValueError("branch anchor must contain at least one row")
    source_offset = int(np.max(base["source_index"])) + 1
    base_radius = np.asarray(base.get("radius", np.zeros(base_rows, dtype=np.float32)), dtype=np.float32)
    branch_radius_values = np.full(branch_rows, float(branch_radius), dtype=np.float32)
    arrays = {
        "observation": np.concatenate([base["observation"], branch["observation"]], axis=0).astype(np.float32),
        "hidden": np.concatenate([base["hidden"], branch["hidden"]], axis=0).astype(np.float32),
        "reference_action": np.concatenate([base["reference_action"], branch["reference_action"]], axis=0).astype(np.float32),
        "source_index": np.concatenate(
            [base["source_index"], branch["source_index"] + source_offset],
            axis=0,
        ).astype(np.int64),
        "step_index": np.concatenate([base["step_index"], branch["step_index"]], axis=0).astype(np.int64),
        "weight": np.concatenate([base["weight"], branch["weight"]], axis=0).astype(np.float32),
        "radius": np.concatenate([base_radius, branch_radius_values], axis=0).astype(np.float32),
    }
    output_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output_npz, **arrays)

    branch_rows_frame = pd.read_csv(branch_anchor_csv)
    source_rows: list[dict[str, Any]] = []
    for source_index in sorted(set(int(value) for value in base["source_index"].tolist())):
        mask = base["source_index"] == source_index
        source_rows.append(
            {
                "source_index": source_index,
                "source_label": "base_hard_guard",
                "case_id": "",
                "branch": "",
                "role": "existing_hard_guard",
                "rows": int(mask.sum()),
                "radius": float(np.max(base_radius[mask])),
                "weight_mean": float(np.mean(base["weight"][mask])),
            }
        )
    for source_index, group in branch_rows_frame.groupby("source_index", sort=True):
        shifted = int(source_index) + source_offset
        source_rows.append(
            {
                "source_index": shifted,
                "source_label": "old_key_branch_split",
                "case_id": str(group["case_id"].iloc[0]),
                "branch": str(group["branch"].iloc[0]),
                "role": "branch_split_hard_guard",
                "rows": int(len(group)),
                "radius": float(branch_radius),
                "weight_mean": float(group["weight"].astype(float).mean()),
            }
        )
    write_csv_rows(output_sources_csv, source_rows)
    return {
        "anchor_npz": output_npz,
        "source_summary_csv": output_sources_csv,
        "base_rows": base_rows,
        "branch_rows": branch_rows,
        "rows": int(arrays["observation"].shape[0]),
        "source_index_offset": source_offset,
        "branch_sources": int(branch_rows_frame["source_index"].nunique()),
        "branch_radius": float(branch_radius),
    }


def export_branch_split_old_key_guard(
    *,
    checkpoint_policy: CheckpointPolicy,
    reference_manifest: Path,
    guard_results_csv: Path,
    baseline_policy: str,
    candidate_policy: str,
    base_anchor_npz: Path,
    max_continuation_steps: int,
    wrong_history_weight: float,
    normal_weight: float,
    branch_radius: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    failed = build_branch_split_failed_rows(
        guard_results_csv=guard_results_csv,
        baseline_policy=baseline_policy,
        candidate_policy=candidate_policy,
    )
    failed_rows_csv = run_dir / "branch_split_failed_rows.csv"
    save_branch_split_failed_rows(failed, failed_rows_csv)
    branch_export = export_old_key_replay_failure_trajectory_anchor(
        checkpoint_policy=checkpoint_policy,
        reference_manifest=reference_manifest,
        failed_rows_csv=failed_rows_csv,
        max_continuation_steps=max_continuation_steps,
        wrong_history_weight=wrong_history_weight,
        normal_weight=normal_weight,
        device=device,
        run_dir=run_dir / "branch_trajectory_export",
    )
    combined = combine_base_and_branch_anchors(
        base_anchor_npz=base_anchor_npz,
        branch_anchor_npz=Path(branch_export["anchor_npz"]),
        branch_anchor_csv=Path(branch_export["anchor_csv"]),
        output_npz=run_dir / "branch_split_hard_guard_anchor.npz",
        output_sources_csv=run_dir / "branch_split_hard_guard_sources.csv",
        branch_radius=branch_radius,
    )
    branch_counts = failed["branch"].value_counts().to_dict()
    summary = {
        "run_type": "branch_split_old_key_guard_export",
        "checkpoint": asdict(checkpoint_policy),
        "reference_manifest": reference_manifest,
        "guard_results_csv": guard_results_csv,
        "baseline_policy": baseline_policy,
        "candidate_policy": candidate_policy,
        "base_anchor_npz": base_anchor_npz,
        "failed_rows_csv": failed_rows_csv,
        "failed_rows": int(len(failed)),
        "branch_counts": {str(key): int(value) for key, value in branch_counts.items()},
        **combined,
        "branch_export": branch_export,
        "ppo_or_actor_update_run": False,
        "checkpoint_promoted": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_policy, required=True)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--guard-results-csv", type=Path, required=True)
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--candidate-policy", required=True)
    parser.add_argument("--base-anchor-npz", type=Path, required=True)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--wrong-history-weight", type=float, default=75.0)
    parser.add_argument("--normal-weight", type=float, default=75.0)
    parser.add_argument("--branch-radius", type=float, default=0.0002)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = export_branch_split_old_key_guard(
        checkpoint_policy=args.checkpoint_policy,
        reference_manifest=args.reference_manifest,
        guard_results_csv=args.guard_results_csv,
        baseline_policy=args.baseline_policy,
        candidate_policy=args.candidate_policy,
        base_anchor_npz=args.base_anchor_npz,
        max_continuation_steps=args.max_continuation_steps,
        wrong_history_weight=args.wrong_history_weight,
        normal_weight=args.normal_weight,
        branch_radius=args.branch_radius,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(pd.Series({key: value for key, value in summary.items() if key != "branch_export"}).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
