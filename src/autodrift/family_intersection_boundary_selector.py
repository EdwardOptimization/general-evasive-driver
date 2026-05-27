"""Family-intersection selector for boundary outcome proof rows."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.boundary_outcome_corpus_objective import (
    boundary_geometry_key,
    physical_pair_key,
    validate_boundary_row_frame,
)
from autodrift.boundary_outcome_replay_gate import replay_boundary_rows_for_policy
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec


FAMILY_COLUMNS = (
    "family_policy_count",
    "family_success_drop_count",
    "family_all_normal_success",
    "family_all_wrong_history_fail",
    "family_all_success_drop",
    "family_min_wrong_history_margin",
    "family_max_wrong_history_margin",
    "family_min_margin_gap",
    "family_policy_failures",
)


def boundary_rows_to_replay_corpus_frame(
    boundary_frame: pd.DataFrame,
    *,
    accepted_only: bool = True,
) -> pd.DataFrame:
    """Convert raw boundary rows into replay-gate-compatible rows.

    ``boundary_outcome_replay_gate`` consumes compact corpus metadata, not the
    raw boundary mining table.  This adapter preserves the original row
    position as ``row_id`` so family replay metrics can be joined back onto the
    source rows without relying on regenerated compact corpus row numbers.
    """

    validate_boundary_row_frame(boundary_frame)
    frame = boundary_frame.copy()
    frame["source_row_index"] = np.arange(len(frame), dtype=np.int64)
    frame = frame[frame["variant"].astype(str) == "wrong_matched_history"].copy()
    if accepted_only:
        frame = frame[frame["accepted"].astype(bool)].copy()
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "row_id",
                "target",
                "physical_pair_key",
                "left_seed",
                "right_seed",
                "left_step",
                "right_step",
                "relocated_obstacle_body_x",
                "relocated_obstacle_body_y",
                "relocated_obstacle_half_width",
            ]
        )
    if "physical_pair_key" not in frame.columns:
        frame["physical_pair_key"] = [physical_pair_key(row) for _, row in frame.iterrows()]
    replay = pd.DataFrame(
        {
            "row_id": frame["source_row_index"].astype(int),
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
    return replay.reset_index(drop=True)


def score_family_intersection_rows(
    *,
    boundary_frame: pd.DataFrame,
    replay_rows: pd.DataFrame,
    family_policies: tuple[str, ...],
) -> pd.DataFrame:
    """Add per-row all-family replay proof metrics to boundary rows."""

    validate_boundary_row_frame(boundary_frame)
    if "row_id" not in replay_rows.columns or "policy" not in replay_rows.columns:
        raise ValueError("replay rows must contain row_id and policy columns")

    scored = boundary_frame.copy()
    scored["source_row_index"] = np.arange(len(scored), dtype=np.int64)
    if "physical_pair_key" not in scored.columns:
        scored["physical_pair_key"] = [physical_pair_key(row) for _, row in scored.iterrows()]
    if "boundary_geometry_key" not in scored.columns:
        scored["boundary_geometry_key"] = [boundary_geometry_key(row) for _, row in scored.iterrows()]

    policy_names = tuple(str(policy) for policy in family_policies)
    if not policy_names:
        raise ValueError("at least one family policy is required")

    metrics_by_row: dict[int, dict[str, Any]] = {}
    for row_id, group in replay_rows.groupby("row_id", observed=True):
        by_policy = {str(row["policy"]): row for _, row in group.iterrows()}
        failures: list[str] = []
        success_drop_count = 0
        normal_success_values: list[bool] = []
        wrong_fail_values: list[bool] = []
        wrong_margins: list[float] = []
        margin_gaps: list[float] = []
        for policy in policy_names:
            replay = by_policy.get(policy)
            if replay is None:
                failures.append(f"{policy}:missing")
                continue
            normal_success = bool(replay["normal_success"])
            wrong_fail = not bool(replay["wrong_history_success"])
            success_drop = bool(replay["success_drop"])
            if not normal_success:
                failures.append(f"{policy}:normal_failed")
            if not wrong_fail:
                failures.append(f"{policy}:wrong_history_succeeded")
            if not success_drop:
                failures.append(f"{policy}:no_success_drop")
            normal_success_values.append(normal_success)
            wrong_fail_values.append(wrong_fail)
            success_drop_count += int(success_drop)
            wrong_margins.append(float(replay["wrong_history_margin"]))
            margin_gaps.append(float(replay["margin_gap"]))
        row_metrics = {
            "family_policy_count": int(sum(policy in by_policy for policy in policy_names)),
            "family_success_drop_count": int(success_drop_count),
            "family_all_normal_success": bool(
                len(normal_success_values) == len(policy_names) and all(normal_success_values)
            ),
            "family_all_wrong_history_fail": bool(
                len(wrong_fail_values) == len(policy_names) and all(wrong_fail_values)
            ),
            "family_all_success_drop": bool(success_drop_count == len(policy_names)),
            "family_min_wrong_history_margin": _finite_min(wrong_margins),
            "family_max_wrong_history_margin": _finite_max(wrong_margins),
            "family_min_margin_gap": _finite_min(margin_gaps),
            "family_policy_failures": ";".join(failures),
        }
        metrics_by_row[int(row_id)] = row_metrics

    metric_rows = []
    for row_id in scored["source_row_index"].astype(int):
        metric_rows.append(
            metrics_by_row.get(
                int(row_id),
                {
                    "family_policy_count": 0,
                    "family_success_drop_count": 0,
                    "family_all_normal_success": False,
                    "family_all_wrong_history_fail": False,
                    "family_all_success_drop": False,
                    "family_min_wrong_history_margin": float("nan"),
                    "family_max_wrong_history_margin": float("nan"),
                    "family_min_margin_gap": float("nan"),
                    "family_policy_failures": "all:missing",
                },
            )
        )
    metrics = pd.DataFrame(metric_rows, index=scored.index)
    return pd.concat([scored, metrics], axis=1)


def family_intersection_candidates(
    scored_rows: pd.DataFrame,
    *,
    min_family_success_drop_count: int,
) -> pd.DataFrame:
    missing = [column for column in FAMILY_COLUMNS if column not in scored_rows.columns]
    if missing:
        raise ValueError("scored rows are missing family columns: " + ", ".join(missing))
    candidates = scored_rows[
        (scored_rows["variant"].astype(str) == "wrong_matched_history")
        & (scored_rows["accepted"].astype(bool))
        & (scored_rows["family_policy_count"].astype(int) >= int(min_family_success_drop_count))
        & (scored_rows["family_success_drop_count"].astype(int) >= int(min_family_success_drop_count))
        & (scored_rows["family_all_normal_success"].astype(bool))
        & (scored_rows["family_all_wrong_history_fail"].astype(bool))
        & (scored_rows["family_all_success_drop"].astype(bool))
    ].copy()
    return candidates.reset_index(drop=True)


def select_compact_family_intersection_rows(
    candidates: pd.DataFrame,
    *,
    source_labels: tuple[str, ...],
    max_rows_per_physical_pair: int,
    min_rows_per_source: int,
    min_physical_pairs_per_source: int,
    min_targets_per_source: int,
    strict_wrong_history_margin_max: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Select compact source-specific rows from all-family-valid candidates."""

    required = ["checkpoint_label", "target", "physical_pair_key", "family_min_margin_gap", "family_max_wrong_history_margin"]
    missing = [column for column in required if column not in candidates.columns]
    if missing:
        raise ValueError("candidate rows are missing columns: " + ", ".join(missing))
    labels = tuple(str(label) for label in source_labels)
    selected_groups: list[pd.DataFrame] = []
    source_summaries: list[dict[str, Any]] = []
    for label in labels:
        source_pool = candidates[candidates["checkpoint_label"].astype(str) == label].copy()
        strict_pool = source_pool[source_pool["family_max_wrong_history_margin"].astype(float) <= float(strict_wrong_history_margin_max)].copy()
        strict_sufficient = _selection_sufficient(
            strict_pool,
            min_rows=min_rows_per_source,
            min_physical_pairs=min_physical_pairs_per_source,
            min_targets=min_targets_per_source,
        )
        pool = strict_pool if strict_sufficient else source_pool
        mode = "strict_family_margin" if strict_sufficient else "family_intersection"
        compact = _select_for_source(
            pool,
            max_rows_per_physical_pair=max_rows_per_physical_pair,
            min_targets=min_targets_per_source,
        )
        compact["family_selection_mode"] = mode
        compact["family_selection_source_label"] = label
        selected_groups.append(compact)
        source_summaries.append(
            {
                "checkpoint_label": label,
                "candidate_rows": int(len(source_pool)),
                "strict_candidate_rows": int(len(strict_pool)),
                "strict_sufficient": bool(strict_sufficient),
                "selection_mode": mode,
                "selected_rows": int(len(compact)),
                "physical_pairs": int(compact["physical_pair_key"].nunique()) if not compact.empty else 0,
                "targets": int(compact["target"].nunique()) if not compact.empty else 0,
                "selection_pass": bool(
                    _selection_sufficient(
                        compact,
                        min_rows=min_rows_per_source,
                        min_physical_pairs=min_physical_pairs_per_source,
                        min_targets=min_targets_per_source,
                    )
                ),
            }
        )
    selected = pd.concat(selected_groups, ignore_index=True) if selected_groups else candidates.iloc[0:0].copy()
    summary = {
        "source_summaries": source_summaries,
        "all_sources_pass": bool(source_summaries and all(row["selection_pass"] for row in source_summaries)),
        "selected_rows": int(len(selected)),
        "selected_physical_pairs": int(selected["physical_pair_key"].nunique()) if not selected.empty else 0,
        "selected_targets": int(selected["target"].nunique()) if not selected.empty else 0,
    }
    return selected.reset_index(drop=True), summary


def _select_for_source(
    pool: pd.DataFrame,
    *,
    max_rows_per_physical_pair: int,
    min_targets: int,
) -> pd.DataFrame:
    if pool.empty:
        return pool.copy()
    ranked = _rank_rows(pool)
    selected_indices: list[int] = []
    pair_counts: defaultdict[str, int] = defaultdict(int)
    geometry_keys: set[str] = set()

    # Seed target diversity before filling by global rank.
    for target in ranked["target"].astype(str).drop_duplicates().tolist():
        if len({str(ranked.loc[index, "target"]) for index in selected_indices}) >= int(min_targets):
            break
        target_rows = ranked[ranked["target"].astype(str) == target]
        _append_first_available(
            target_rows,
            selected_indices,
            pair_counts,
            geometry_keys,
            max_rows_per_physical_pair,
        )

    _append_available(ranked, selected_indices, pair_counts, geometry_keys, max_rows_per_physical_pair)
    selected = ranked.loc[selected_indices].copy()
    return selected.reset_index(drop=True)


def _rank_rows(rows: pd.DataFrame) -> pd.DataFrame:
    ranked = rows.copy()
    ranked["_rank_family_wrong_margin"] = ranked["family_min_wrong_history_margin"].astype(float)
    ranked["_rank_family_margin_gap"] = ranked["family_min_margin_gap"].astype(float)
    ranked["_rank_normal_margin"] = ranked["normal_margin"].astype(float)
    ranked["_rank_source_row"] = ranked["source_row_index"].astype(int)
    ranked = ranked.sort_values(
        [
            "_rank_family_wrong_margin",
            "_rank_family_margin_gap",
            "_rank_normal_margin",
            "_rank_source_row",
        ],
        ascending=[True, False, True, True],
    )
    return ranked.drop(
        columns=[
            "_rank_family_wrong_margin",
            "_rank_family_margin_gap",
            "_rank_normal_margin",
            "_rank_source_row",
        ]
    )


def _append_first_available(
    rows: pd.DataFrame,
    selected_indices: list[int],
    pair_counts: defaultdict[str, int],
    geometry_keys: set[str],
    max_rows_per_physical_pair: int,
) -> None:
    for index, row in rows.iterrows():
        pair = str(row["physical_pair_key"])
        geometry = str(row["boundary_geometry_key"])
        if index in selected_indices:
            continue
        if geometry in geometry_keys:
            continue
        if max_rows_per_physical_pair > 0 and pair_counts[pair] >= int(max_rows_per_physical_pair):
            continue
        selected_indices.append(index)
        pair_counts[pair] += 1
        geometry_keys.add(geometry)
        return


def _append_available(
    rows: pd.DataFrame,
    selected_indices: list[int],
    pair_counts: defaultdict[str, int],
    geometry_keys: set[str],
    max_rows_per_physical_pair: int,
) -> None:
    for index, row in rows.iterrows():
        pair = str(row["physical_pair_key"])
        geometry = str(row["boundary_geometry_key"])
        if index in selected_indices:
            continue
        if geometry in geometry_keys:
            continue
        if max_rows_per_physical_pair > 0 and pair_counts[pair] >= int(max_rows_per_physical_pair):
            continue
        selected_indices.append(index)
        pair_counts[pair] += 1
        geometry_keys.add(geometry)


def _selection_sufficient(
    rows: pd.DataFrame,
    *,
    min_rows: int,
    min_physical_pairs: int,
    min_targets: int,
) -> bool:
    return bool(
        len(rows) >= int(min_rows)
        and int(rows["physical_pair_key"].nunique()) >= int(min_physical_pairs)
        and int(rows["target"].nunique()) >= int(min_targets)
    )


def _finite_min(values: list[float]) -> float:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return float(min(finite)) if finite else float("nan")


def _finite_max(values: list[float]) -> float:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return float(max(finite)) if finite else float("nan")


def run_family_intersection_selector(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    boundary_rows_csv: Path,
    env_config_path: Path,
    max_continuation_steps: int,
    max_source_rows: int,
    max_rows_per_physical_pair: int,
    min_rows_per_source: int,
    min_physical_pairs_per_source: int,
    min_targets_per_source: int,
    min_family_success_drop_count: int,
    strict_wrong_history_margin_max: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    boundary_frame = pd.read_csv(boundary_rows_csv)
    validate_boundary_row_frame(boundary_frame)
    replay_corpus = boundary_rows_to_replay_corpus_frame(boundary_frame, accepted_only=True)
    if max_source_rows > 0:
        replay_corpus = replay_corpus.sort_values("row_id").head(int(max_source_rows)).reset_index(drop=True)
        boundary_frame = boundary_frame.iloc[replay_corpus["row_id"].astype(int).tolist()].reset_index(drop=True)
        replay_corpus["row_id"] = np.arange(len(replay_corpus), dtype=np.int64)

    replay_rows: list[dict[str, Any]] = []
    for checkpoint_spec in checkpoint_specs:
        replay_rows.extend(
            replay_boundary_rows_for_policy(
                checkpoint_spec=checkpoint_spec,
                corpus_frame=replay_corpus,
                env_config_path=env_config_path,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
        )
    replay_frame = pd.DataFrame(replay_rows)
    family_policies = tuple(spec.label for spec in checkpoint_specs)
    scored = score_family_intersection_rows(
        boundary_frame=boundary_frame,
        replay_rows=replay_frame,
        family_policies=family_policies,
    )
    candidates = family_intersection_candidates(
        scored,
        min_family_success_drop_count=min_family_success_drop_count,
    )
    selected, selection_summary = select_compact_family_intersection_rows(
        candidates,
        source_labels=tuple(sorted(scored["checkpoint_label"].astype(str).unique())),
        max_rows_per_physical_pair=max_rows_per_physical_pair,
        min_rows_per_source=min_rows_per_source,
        min_physical_pairs_per_source=min_physical_pairs_per_source,
        min_targets_per_source=min_targets_per_source,
        strict_wrong_history_margin_max=strict_wrong_history_margin_max,
    )

    replay_corpus.to_csv(run_dir / "family_replay_corpus.csv", index=False)
    replay_frame.to_csv(run_dir / "family_replay_rows.csv", index=False)
    scored.to_csv(run_dir / "family_scored_boundary_rows.csv", index=False)
    candidates.to_csv(run_dir / "family_intersection_candidates.csv", index=False)
    selected.to_csv(run_dir / "family_intersection_selected_rows.csv", index=False)

    summary = {
        "run_type": "family_intersection_boundary_selector",
        "boundary_rows_csv": boundary_rows_csv,
        "env_config": env_config_path,
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "max_continuation_steps": int(max_continuation_steps),
        "max_source_rows": int(max_source_rows),
        "source_rows": int(len(boundary_frame)),
        "family_policy_count": int(len(checkpoint_specs)),
        "family_policies": list(family_policies),
        "family_replay_rows": int(len(replay_frame)),
        "family_intersection_candidates": int(len(candidates)),
        "candidate_physical_pairs": int(candidates["physical_pair_key"].nunique()) if not candidates.empty else 0,
        "candidate_targets": int(candidates["target"].nunique()) if not candidates.empty else 0,
        "max_rows_per_physical_pair": int(max_rows_per_physical_pair),
        "min_rows_per_source": int(min_rows_per_source),
        "min_physical_pairs_per_source": int(min_physical_pairs_per_source),
        "min_targets_per_source": int(min_targets_per_source),
        "min_family_success_drop_count": int(min_family_success_drop_count),
        "strict_wrong_history_margin_max": float(strict_wrong_history_margin_max),
        **selection_summary,
        "selection_pass": bool(selection_summary["all_sources_pass"]),
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "artifacts": {
            "family_replay_corpus_csv": run_dir / "family_replay_corpus.csv",
            "family_replay_rows_csv": run_dir / "family_replay_rows.csv",
            "family_scored_boundary_rows_csv": run_dir / "family_scored_boundary_rows.csv",
            "family_intersection_candidates_csv": run_dir / "family_intersection_candidates.csv",
            "family_intersection_selected_rows_csv": run_dir / "family_intersection_selected_rows.csv",
            "summary_json": run_dir / "summary.json",
        },
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select family-intersection boundary proof rows.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--boundary-rows-csv", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--max-source-rows", type=int, default=0)
    parser.add_argument("--max-rows-per-physical-pair", type=int, default=2)
    parser.add_argument("--min-rows-per-source", type=int, default=20)
    parser.add_argument("--min-physical-pairs-per-source", type=int, default=10)
    parser.add_argument("--min-targets-per-source", type=int, default=2)
    parser.add_argument("--min-family-success-drop-count", type=int, default=0)
    parser.add_argument("--strict-wrong-history-margin-max", type=float, default=-1e-4)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    family_count = len(args.checkpoint_policy)
    min_family_success_drop_count = (
        int(args.min_family_success_drop_count)
        if int(args.min_family_success_drop_count) > 0
        else family_count
    )
    run_dir = args.run_dir or make_run_dir(prefix="family_intersection_boundary_selector")
    summary = run_family_intersection_selector(
        checkpoint_specs=tuple(args.checkpoint_policy),
        boundary_rows_csv=args.boundary_rows_csv,
        env_config_path=args.env_config,
        max_continuation_steps=args.max_continuation_steps,
        max_source_rows=args.max_source_rows,
        max_rows_per_physical_pair=args.max_rows_per_physical_pair,
        min_rows_per_source=args.min_rows_per_source,
        min_physical_pairs_per_source=args.min_physical_pairs_per_source,
        min_targets_per_source=args.min_targets_per_source,
        min_family_success_drop_count=min_family_success_drop_count,
        strict_wrong_history_margin_max=args.strict_wrong_history_margin_max,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
