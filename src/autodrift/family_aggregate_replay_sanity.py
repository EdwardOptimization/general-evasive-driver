"""Source-aware replay sanity for family-aggregate boundary rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import replay_boundary_rows_for_policy
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec


FAMILY_REQUIRED_COLUMNS = (
    "family_row_id",
    "source_checkpoint_label",
    "source_checkpoint_path",
    "physical_pair_key",
    "boundary_geometry_key",
    "duplicate_geometry_group_id",
    "target",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "relocated_obstacle_body_x",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
)


def validate_family_rows(frame: pd.DataFrame) -> None:
    missing = [column for column in FAMILY_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("family aggregate rows missing columns: " + ", ".join(missing))
    if frame["family_row_id"].duplicated().any():
        raise ValueError("family_row_id values must be unique")


def family_rows_to_replay_frame(frame: pd.DataFrame) -> pd.DataFrame:
    validate_family_rows(frame)
    return pd.DataFrame(
        {
            "row_id": frame["family_row_id"].astype(int),
            "target": frame["target"].astype(str),
            "physical_pair_key": frame["physical_pair_key"].astype(str),
            "left_seed": frame["left_seed"].astype(int),
            "right_seed": frame["right_seed"].astype(int),
            "left_step": frame["left_step"].astype(int),
            "right_step": frame["right_step"].astype(int),
            "relocated_obstacle_body_x": frame["relocated_obstacle_body_x"].astype(float),
            "relocated_obstacle_body_y": frame["relocated_obstacle_body_y"].astype(float),
            "relocated_obstacle_half_width": frame["relocated_obstacle_half_width"].astype(float),
        }
    )


def _metadata_frame(frame: pd.DataFrame) -> pd.DataFrame:
    metadata_columns = [
        "family_row_id",
        "source_row_index",
        "source_checkpoint_label",
        "source_checkpoint_path",
        "source_checkpoint_family",
        "boundary_geometry_key",
        "duplicate_geometry_group_id",
        "duplicate_geometry_group_size",
        "duplicate_geometry_source_labels",
    ]
    present = [column for column in metadata_columns if column in frame.columns]
    return frame[present].copy()


def attach_family_metadata(replay_rows: list[dict[str, Any]], family_frame: pd.DataFrame) -> pd.DataFrame:
    replay = pd.DataFrame(replay_rows)
    if replay.empty:
        return replay
    metadata = _metadata_frame(family_frame)
    merged = replay.merge(
        metadata,
        left_on="row_id",
        right_on="family_row_id",
        how="left",
        validate="many_to_one",
    )
    if merged["source_checkpoint_label"].isna().any():
        raise ValueError("replay rows contain row_id values missing from family metadata")
    return merged


def _finite_count(values: pd.Series) -> int:
    numeric = pd.to_numeric(values, errors="coerce").astype(float)
    return int(np.isfinite(numeric).sum())


def build_source_policy_gate_summary(
    *,
    replay_frame: pd.DataFrame,
    family_frame: pd.DataFrame,
    source_labels: tuple[str, ...],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in source_labels:
        source_rows = family_frame[family_frame["source_checkpoint_label"].astype(str) == str(label)].copy()
        source_replay = replay_frame[
            (replay_frame["policy"].astype(str) == str(label))
            & (replay_frame["source_checkpoint_label"].astype(str) == str(label))
        ].copy()
        source_row_ids = set(source_rows["family_row_id"].astype(int))
        replay_row_ids = set(source_replay["row_id"].astype(int)) if not source_replay.empty else set()
        missing_row_ids = sorted(source_row_ids - replay_row_ids)
        normal_success_count = int(source_replay["normal_success"].astype(bool).sum()) if not source_replay.empty else 0
        wrong_success_count = (
            int(source_replay["wrong_history_success"].astype(bool).sum()) if not source_replay.empty else 0
        )
        success_drop_count = int(source_replay["success_drop"].astype(bool).sum()) if not source_replay.empty else 0
        finite_margin_gap_count = _finite_count(source_replay["margin_gap"]) if not source_replay.empty else 0
        source_count = int(len(source_rows))
        gate_pass = bool(
            len(missing_row_ids) == 0
            and int(len(source_replay)) == source_count
            and normal_success_count == source_count
            and wrong_success_count == 0
            and success_drop_count == source_count
            and finite_margin_gap_count == source_count
        )
        rows.append(
            {
                "source_checkpoint_label": str(label),
                "source_row_count": source_count,
                "replay_row_count": int(len(source_replay)),
                "missing_row_count": int(len(missing_row_ids)),
                "missing_family_row_ids": ",".join(str(row_id) for row_id in missing_row_ids),
                "normal_success_count": normal_success_count,
                "wrong_history_success_count": wrong_success_count,
                "success_drop_count": success_drop_count,
                "finite_margin_gap_count": finite_margin_gap_count,
                "normal_success_rate": float(normal_success_count / source_count) if source_count else 0.0,
                "wrong_history_success_rate": float(wrong_success_count / source_count) if source_count else 0.0,
                "success_drop_rate": float(success_drop_count / source_count) if source_count else 0.0,
                "gate_pass": gate_pass,
            }
        )
    return rows


def build_aggregate_source_gate(source_replay: pd.DataFrame, source_gate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_count = int(sum(int(row["source_row_count"]) for row in source_gate_rows))
    replay_row_count = int(len(source_replay))
    normal_success_count = int(source_replay["normal_success"].astype(bool).sum()) if replay_row_count else 0
    wrong_success_count = int(source_replay["wrong_history_success"].astype(bool).sum()) if replay_row_count else 0
    success_drop_count = int(source_replay["success_drop"].astype(bool).sum()) if replay_row_count else 0
    physical_pairs = int(source_replay["physical_pair_key"].astype(str).nunique()) if replay_row_count else 0
    checkpoints = int(source_replay["source_checkpoint_label"].astype(str).nunique()) if replay_row_count else 0
    targets = int(source_replay["target"].astype(str).nunique()) if replay_row_count else 0
    gate_pass = bool(
        row_count > 0
        and replay_row_count == row_count
        and normal_success_count == row_count
        and wrong_success_count == 0
        and success_drop_count == row_count
        and physical_pairs >= 10
        and checkpoints >= 3
        and targets >= 2
        and all(bool(row["gate_pass"]) for row in source_gate_rows)
    )
    return {
        "source_row_count": row_count,
        "source_replay_row_count": replay_row_count,
        "normal_success_count": normal_success_count,
        "wrong_history_success_count": wrong_success_count,
        "success_drop_count": success_drop_count,
        "normal_success_rate": float(normal_success_count / row_count) if row_count else 0.0,
        "wrong_history_success_rate": float(wrong_success_count / row_count) if row_count else 0.0,
        "success_drop_rate": float(success_drop_count / row_count) if row_count else 0.0,
        "physical_pairs": physical_pairs,
        "checkpoints": checkpoints,
        "targets": targets,
        "gate_pass": gate_pass,
    }


def build_cross_family_policy_summary(replay_frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if replay_frame.empty:
        return rows
    group_columns = ["policy", "source_checkpoint_label", "target"]
    for keys, group in replay_frame.groupby(group_columns, observed=True):
        policy, source_label, target = (str(value) for value in keys)
        margin_gap = pd.to_numeric(group["margin_gap"], errors="coerce").astype(float)
        finite_gap = margin_gap[np.isfinite(margin_gap)]
        failed = group[
            (~group["normal_success"].astype(bool))
            | (group["wrong_history_success"].astype(bool))
            | (~group["success_drop"].astype(bool))
        ]
        rows.append(
            {
                "policy": policy,
                "source_checkpoint_label": source_label,
                "target": target,
                "rows": int(len(group)),
                "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
                "wrong_history_success_rate": float(group["wrong_history_success"].astype(bool).mean()),
                "success_drop_count": int(group["success_drop"].astype(bool).sum()),
                "normal_margin_mean": float(pd.to_numeric(group["normal_margin"], errors="coerce").mean()),
                "wrong_history_margin_mean": float(
                    pd.to_numeric(group["wrong_history_margin"], errors="coerce").mean()
                ),
                "margin_gap_mean": float(finite_gap.mean()) if len(finite_gap) else float("nan"),
                "margin_gap_min": float(finite_gap.min()) if len(finite_gap) else float("nan"),
                "failed_family_row_ids": ",".join(str(int(value)) for value in failed["family_row_id"]),
            }
        )
    return rows


def build_duplicate_geometry_replay_summary(replay_frame: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    if replay_frame.empty:
        return rows, failed_rows
    for keys, group in replay_frame.groupby(
        ["duplicate_geometry_group_id", "source_checkpoint_label", "policy"],
        observed=True,
    ):
        group_id, source_label, policy = (str(value) for value in keys)
        failed = group[
            (~group["normal_success"].astype(bool))
            | (group["wrong_history_success"].astype(bool))
            | (~group["success_drop"].astype(bool))
        ]
        row = {
            "duplicate_geometry_group_id": group_id,
            "source_checkpoint_label": source_label,
            "policy": policy,
            "rows": int(len(group)),
            "physical_pair_key": str(group["physical_pair_key"].iloc[0]),
            "target": str(group["target"].iloc[0]),
            "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
            "wrong_history_success_rate": float(group["wrong_history_success"].astype(bool).mean()),
            "success_drop_count": int(group["success_drop"].astype(bool).sum()),
            "failed_rows": int(len(failed)),
            "failed_family_row_ids": ",".join(str(int(value)) for value in failed["family_row_id"]),
        }
        rows.append(row)
        if len(failed):
            failed_rows.append(row)
    rows.sort(key=lambda row: (-int(row["failed_rows"]), str(row["duplicate_geometry_group_id"]), str(row["policy"])))
    failed_rows.sort(key=lambda row: (-int(row["failed_rows"]), str(row["duplicate_geometry_group_id"]), str(row["policy"])))
    return rows, failed_rows


def run_family_aggregate_replay_sanity(
    *,
    family_rows_csv: Path,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    run_dir: Path,
    max_rows: int = 0,
    max_continuation_steps: int = 60,
    device: str = "cpu",
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    family_frame = pd.read_csv(family_rows_csv)
    validate_family_rows(family_frame)
    if max_rows > 0:
        family_frame = family_frame.sort_values("family_row_id").head(int(max_rows)).reset_index(drop=True)
    source_labels = tuple(sorted(family_frame["source_checkpoint_label"].astype(str).unique()))
    policy_labels = tuple(str(spec.label) for spec in checkpoint_specs)
    missing_source_policies = sorted(set(source_labels) - set(policy_labels))
    if missing_source_policies:
        raise ValueError("checkpoint specs missing source labels: " + ", ".join(missing_source_policies))

    replay_frame = family_rows_to_replay_frame(family_frame)
    replay_rows: list[dict[str, Any]] = []
    for checkpoint_spec in checkpoint_specs:
        replay_rows.extend(
            replay_boundary_rows_for_policy(
                checkpoint_spec=checkpoint_spec,
                corpus_frame=replay_frame,
                env_config_path=env_config_path,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
        )
    replay_with_metadata = attach_family_metadata(replay_rows, family_frame)
    source_policy_replay = replay_with_metadata[
        replay_with_metadata["policy"].astype(str) == replay_with_metadata["source_checkpoint_label"].astype(str)
    ].copy()
    source_gate_rows = build_source_policy_gate_summary(
        replay_frame=replay_with_metadata,
        family_frame=family_frame,
        source_labels=source_labels,
    )
    aggregate_gate = build_aggregate_source_gate(source_policy_replay, source_gate_rows)
    cross_summary = build_cross_family_policy_summary(replay_with_metadata)
    duplicate_summary, failed_duplicate = build_duplicate_geometry_replay_summary(replay_with_metadata)

    write_csv_rows(run_dir / "source_policy_source_rows_replay.csv", source_policy_replay.to_dict("records"))
    write_csv_rows(run_dir / "source_policy_gate_summary.csv", source_gate_rows)
    write_csv_rows(run_dir / "cross_family_replay_rows.csv", replay_with_metadata.to_dict("records"))
    write_csv_rows(run_dir / "cross_family_policy_summary.csv", cross_summary)
    write_csv_rows(run_dir / "duplicate_geometry_replay_summary.csv", duplicate_summary)
    write_csv_rows(run_dir / "failed_duplicate_geometry_groups.csv", failed_duplicate)
    decision = (
        "family_aggregate_replay_sanity_source_gate_pass"
        if aggregate_gate["gate_pass"]
        else "family_aggregate_replay_sanity_source_gate_fail"
    )
    summary = {
        "run_type": "family_aggregate_replay_sanity",
        "family_rows_csv": family_rows_csv,
        "env_config": env_config_path,
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "max_rows": int(max_rows),
        "max_continuation_steps": int(max_continuation_steps),
        "family_rows": int(len(family_frame)),
        "replay_rows": int(len(replay_with_metadata)),
        "source_policy_replay_rows": int(len(source_policy_replay)),
        "source_policy_gate_summary": source_gate_rows,
        "aggregate_source_gate": aggregate_gate,
        "cross_family_summary_rows": int(len(cross_summary)),
        "duplicate_geometry_summary_rows": int(len(duplicate_summary)),
        "failed_duplicate_geometry_groups": int(len(failed_duplicate)),
        "decision": decision,
        "passed": bool(aggregate_gate["gate_pass"]),
        "source_policy_source_rows_replay_csv": run_dir / "source_policy_source_rows_replay.csv",
        "source_policy_gate_summary_csv": run_dir / "source_policy_gate_summary.csv",
        "cross_family_replay_rows_csv": run_dir / "cross_family_replay_rows.csv",
        "cross_family_policy_summary_csv": run_dir / "cross_family_policy_summary.csv",
        "duplicate_geometry_replay_summary_csv": run_dir / "duplicate_geometry_replay_summary.csv",
        "failed_duplicate_geometry_groups_csv": run_dir / "failed_duplicate_geometry_groups.csv",
        "training_started": False,
        "ppo_used": False,
        "objective_optimization_started": False,
        "mining_started": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run source-aware family aggregate replay sanity.")
    parser.add_argument("--family-rows-csv", type=Path, required=True)
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    summary = run_family_aggregate_replay_sanity(
        family_rows_csv=args.family_rows_csv,
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        run_dir=args.run_dir,
        max_rows=args.max_rows,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
