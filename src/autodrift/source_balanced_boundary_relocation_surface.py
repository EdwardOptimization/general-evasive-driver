"""Source-balanced helpers for wrong-history boundary relocation exports."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_wrong_history_surface_robustness import (
    PHYSICAL_PAIR_COLUMNS,
    build_gate_rows,
    decision_from_gates,
    summarize_surface,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import requested_snapshot_steps
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import (
    DEFAULT_REPORT_VARIANTS,
    DEFAULT_TARGET_NORMAL_MARGINS,
    build_boundary_relocation_rows,
    parse_float_list,
    parse_variants,
    summarize_boundary_relocation_rows,
)


DEFAULT_ROBUSTNESS_THRESHOLDS = {
    "min_accepted_wrong_rows": 80,
    "min_physical_pairs": 10,
    "min_left_steps": 5,
    "min_checkpoints": 3,
    "min_targets": 2,
    "min_margin_buckets": 2,
    "min_success_drop_fraction": 1.0,
    "max_rows_per_pair_fraction": 0.25,
    "max_control_accepted_rows": 0,
}


@dataclass(frozen=True)
class SourceBalanceQuotas:
    max_candidates: int
    max_candidates_per_physical_pair: int = 8
    max_candidates_per_checkpoint_target: int = 64
    max_accepted_rows_per_physical_pair: int = 20
    target_min_physical_pairs: int = 10
    target_min_left_steps: int = 5
    target_min_targets: int = 2
    max_rows_per_pair_fraction: float = 0.25


def _as_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if np.isfinite(result) else float(default)


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"cannot convert {value!r} to int") from exc


def _bool_value(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(float(value) != 0.0)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _format_bucket(value: float, width: float) -> str:
    if width <= 0.0:
        raise ValueError("bucket width must be positive")
    if not np.isfinite(value):
        return "nan"
    start = math.floor(float(value) / float(width)) * float(width)
    return f"{start:.3f}-{start + float(width):.3f}"


def physical_pair_key(row: pd.Series | dict[str, Any]) -> str:
    """Return the exact physical-pair key used by the robustness gate."""

    missing = [column for column in PHYSICAL_PAIR_COLUMNS if column not in row]
    if missing:
        raise ValueError(f"row missing physical pair columns: {missing}")
    return ":".join(str(_as_int(row[column])) for column in PHYSICAL_PAIR_COLUMNS)


def _first_present_float(row: pd.Series | dict[str, Any], columns: tuple[str, ...]) -> float:
    for column in columns:
        if column in row:
            value = _as_float(row[column])
            if np.isfinite(value):
                return value
    return float("nan")


def source_obstacle_bucket(
    row: pd.Series | dict[str, Any],
    *,
    distance_bucket_width: float,
    lateral_bucket_width: float,
) -> str:
    """Bucket source obstacle geometry without changing robustness semantics."""

    distance = _first_present_float(
        row,
        (
            "source_obstacle_body_x",
            "obstacle_distance",
            "relocated_obstacle_body_x",
            "source_obstacle_distance",
        ),
    )
    lateral = _first_present_float(
        row,
        (
            "source_obstacle_body_y",
            "obstacle_lateral_offset",
            "relocated_obstacle_body_y",
            "source_obstacle_lateral_offset",
        ),
    )
    return (
        f"x={_format_bucket(distance, distance_bucket_width)}|"
        f"y={_format_bucket(lateral, lateral_bucket_width)}"
    )


def add_source_balance_keys(
    frame: pd.DataFrame,
    *,
    distance_bucket_width: float,
    lateral_bucket_width: float,
) -> pd.DataFrame:
    missing = [column for column in PHYSICAL_PAIR_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"rows missing physical pair columns: {missing}")
    keyed = frame.copy()
    keyed["physical_pair_key"] = [physical_pair_key(row) for _, row in keyed.iterrows()]
    keyed["source_obstacle_bucket"] = [
        source_obstacle_bucket(
            row,
            distance_bucket_width=distance_bucket_width,
            lateral_bucket_width=lateral_bucket_width,
        )
        for _, row in keyed.iterrows()
    ]
    return keyed


def wrong_history_candidate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if "variant" not in frame.columns:
        return frame.copy().reset_index(drop=True)
    return frame[frame["variant"].astype(str) == "wrong_matched_history"].copy().reset_index(drop=True)


def build_source_budget(
    frame: pd.DataFrame,
    *,
    distance_bucket_width: float = 5.0,
    lateral_bucket_width: float = 1.0,
    min_eligible_physical_pairs: int = 10,
    max_candidate_pair_fraction: float = 0.25,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidates = add_source_balance_keys(
        wrong_history_candidate_frame(frame),
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
    )
    if candidates.empty:
        summary = {
            "candidate_wrong_history_rows": 0,
            "eligible_physical_pairs": 0,
            "eligible_left_steps": 0,
            "eligible_checkpoints": 0,
            "eligible_targets": 0,
            "eligible_source_obstacle_buckets": 0,
            "max_candidate_pair_rows": 0,
            "max_candidate_pair_fraction": 0.0,
            "min_eligible_physical_pairs": int(min_eligible_physical_pairs),
            "max_allowed_candidate_pair_fraction": float(max_candidate_pair_fraction),
            "source_budget_ready": False,
            "decision": "source_budget_empty",
        }
        return summary, []

    counts = candidates.groupby("physical_pair_key", observed=True).size()
    max_rows = int(counts.max()) if len(counts) else 0
    max_fraction = float(max_rows / max(len(candidates), 1))
    source_budget_ready = bool(
        int(candidates["physical_pair_key"].nunique()) >= int(min_eligible_physical_pairs)
        and max_fraction <= float(max_candidate_pair_fraction)
    )
    summary = {
        "candidate_wrong_history_rows": int(len(candidates)),
        "eligible_physical_pairs": int(candidates["physical_pair_key"].nunique()),
        "eligible_left_steps": int(candidates["left_step"].nunique()),
        "eligible_checkpoints": int(candidates["checkpoint_label"].astype(str).nunique())
        if "checkpoint_label" in candidates
        else 0,
        "eligible_targets": int(candidates["target"].astype(str).nunique()) if "target" in candidates else 0,
        "eligible_source_obstacle_buckets": int(candidates["source_obstacle_bucket"].astype(str).nunique()),
        "max_candidate_pair_rows": max_rows,
        "max_candidate_pair_fraction": max_fraction,
        "min_eligible_physical_pairs": int(min_eligible_physical_pairs),
        "max_allowed_candidate_pair_fraction": float(max_candidate_pair_fraction),
        "source_budget_ready": source_budget_ready,
        "decision": "source_budget_ready"
        if source_budget_ready
        else "source_budget_insufficient_or_dominated",
    }

    budget_rows: list[dict[str, Any]] = []
    for key, group in candidates.groupby("physical_pair_key", observed=True):
        budget_rows.append(
            {
                "physical_pair_key": str(key),
                "row_count": int(len(group)),
                "left_seed": int(group["left_seed"].iloc[0]),
                "left_step": int(group["left_step"].iloc[0]),
                "right_seed": int(group["right_seed"].iloc[0]),
                "right_step": int(group["right_step"].iloc[0]),
                "checkpoints": ",".join(sorted(group["checkpoint_label"].astype(str).unique()))
                if "checkpoint_label" in group
                else "",
                "targets": ",".join(sorted(group["target"].astype(str).unique())) if "target" in group else "",
                "source_obstacle_buckets": ",".join(sorted(group["source_obstacle_bucket"].astype(str).unique())),
                "margin_gap_max": float(pd.to_numeric(group.get("margin_gap", pd.Series(dtype=float)), errors="coerce").max()),
                "first_action_distance_max": float(
                    pd.to_numeric(group.get("first_action_distance", pd.Series(dtype=float)), errors="coerce").max()
                ),
            }
        )
    budget_rows.sort(key=lambda row: (-int(row["row_count"]), str(row["physical_pair_key"])))
    return summary, budget_rows


def _candidate_sort_key(row: pd.Series | dict[str, Any]) -> tuple[Any, ...]:
    visible = _as_float(row.get("visible_distance", float("inf")), default=float("inf"))
    return (
        -_as_float(row.get("margin_gap"), default=-float("inf")),
        -_as_float(row.get("first_action_distance"), default=-float("inf")),
        visible,
        str(row.get("checkpoint_label", "")),
        str(row.get("target", "")),
        _as_int(row.get("left_seed", 0)),
        _as_int(row.get("left_step", 0)),
        _as_int(row.get("right_seed", 0)),
        _as_int(row.get("right_step", 0)),
    )


def select_source_balanced_candidates(
    frame: pd.DataFrame,
    *,
    quotas: SourceBalanceQuotas,
    distance_bucket_width: float = 5.0,
    lateral_bucket_width: float = 1.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Select relocation candidates by physical-pair round robin."""

    candidates = add_source_balance_keys(
        wrong_history_candidate_frame(frame),
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
    )
    if candidates.empty:
        return candidates.copy(), candidates.copy(), {
            "candidate_rows": 0,
            "selected_rows": 0,
            "rejected_rows": 0,
            "selected_physical_pairs": 0,
            "decision": "source_balanced_candidate_empty",
        }

    groups: dict[str, list[pd.Series]] = {}
    for key, group in candidates.groupby("physical_pair_key", observed=True):
        rows = [row for _, row in group.iterrows()]
        rows.sort(key=_candidate_sort_key)
        groups[str(key)] = rows

    group_order = sorted(
        groups,
        key=lambda key: (_candidate_sort_key(groups[key][0]), key),
    )
    offsets = {key: 0 for key in group_order}
    pair_counts: dict[str, int] = {}
    checkpoint_target_counts: dict[str, int] = {}
    selected_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []

    while len(selected_rows) < int(quotas.max_candidates):
        progressed = False
        for key in group_order:
            rows = groups[key]
            offset = offsets[key]
            while offset < len(rows):
                row = rows[offset]
                offset += 1
                base = row.to_dict()
                checkpoint_target = f"{base.get('checkpoint_label', '')}|{base.get('target', '')}"
                if pair_counts.get(key, 0) >= int(quotas.max_candidates_per_physical_pair):
                    rejected_rows.append({**base, "balance_rejection_reason": "physical_pair_candidate_cap"})
                    continue
                if checkpoint_target_counts.get(checkpoint_target, 0) >= int(quotas.max_candidates_per_checkpoint_target):
                    rejected_rows.append({**base, "balance_rejection_reason": "checkpoint_target_candidate_cap"})
                    continue
                selected_rows.append({**base, "selected_balance_rank": len(selected_rows)})
                pair_counts[key] = pair_counts.get(key, 0) + 1
                checkpoint_target_counts[checkpoint_target] = checkpoint_target_counts.get(checkpoint_target, 0) + 1
                progressed = True
                break
            offsets[key] = offset
            if len(selected_rows) >= int(quotas.max_candidates):
                break
        if not progressed:
            break

    selected = pd.DataFrame(selected_rows)
    rejected = pd.DataFrame(rejected_rows)
    selected_count = int(len(selected))
    max_rows_per_pair = int(selected["physical_pair_key"].value_counts().max()) if selected_count else 0
    selected_left_steps = int(selected["left_step"].nunique()) if selected_count else 0
    selected_targets = int(selected["target"].astype(str).nunique()) if selected_count and "target" in selected else 0
    summary = {
        "candidate_rows": int(len(candidates)),
        "selected_rows": selected_count,
        "rejected_rows": int(len(rejected)),
        "selected_physical_pairs": int(selected["physical_pair_key"].nunique()) if selected_count else 0,
        "selected_left_steps": selected_left_steps,
        "selected_targets": selected_targets,
        "max_selected_rows_per_physical_pair": max_rows_per_pair,
        "max_selected_pair_fraction": float(max_rows_per_pair / max(selected_count, 1)) if selected_count else 0.0,
        "target_min_physical_pairs": int(quotas.target_min_physical_pairs),
        "target_min_left_steps": int(quotas.target_min_left_steps),
        "target_min_targets": int(quotas.target_min_targets),
        "decision": "source_balanced_candidates_ready"
        if selected_count
        and int(selected["physical_pair_key"].nunique()) >= int(quotas.target_min_physical_pairs)
        and selected_left_steps >= int(quotas.target_min_left_steps)
        and selected_targets >= int(quotas.target_min_targets)
        and float(max_rows_per_pair / max(selected_count, 1)) <= float(quotas.max_rows_per_pair_fraction)
        else "source_balanced_candidates_source_limited",
    }
    return selected, rejected, summary


def mark_balanced_export_rows(
    boundary_rows: pd.DataFrame,
    *,
    quotas: SourceBalanceQuotas,
    margin_bucket_width: float = 0.005,
    control_checkpoint_label: str = "none",
) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    """Mark accepted wrong-history rows eligible for balanced corpus export."""

    keyed = boundary_rows.copy()
    keyed["balanced_exportable"] = False
    keyed["balance_rejection_reason"] = "not_accepted_wrong_history"
    if keyed.empty:
        summary = {
            "row_count": 0,
            "wrong_history_row_count": 0,
            "accepted_wrong_rows": 0,
            "accepted_wrong_physical_pairs": 0,
            "accepted_wrong_left_steps": 0,
            "accepted_wrong_right_steps": 0,
            "accepted_wrong_checkpoints": 0,
            "accepted_wrong_targets": 0,
            "accepted_wrong_normal_margin_buckets": 0,
            "accepted_wrong_success_drop_fraction": 0.0,
            "accepted_wrong_margin_gap_mean": float("nan"),
            "accepted_wrong_margin_gap_max": float("nan"),
            "accepted_wrong_normal_margin_mean": float("nan"),
            "accepted_wrong_normal_margin_min": float("nan"),
            "accepted_wrong_normal_margin_max": float("nan"),
            "max_rows_per_physical_pair": 0,
            "max_rows_per_physical_pair_fraction": 0.0,
            "control_checkpoint_label": str(control_checkpoint_label),
            "control_accepted_wrong_rows": 0,
            "accepted_reset_rows": 0,
            "accepted_zero_current_rows": 0,
            "wrong_to_reset_accepted_ratio": float("nan"),
            "wrong_to_zero_current_accepted_ratio": float("nan"),
        }
        gates = build_gate_rows(summary, **DEFAULT_ROBUSTNESS_THRESHOLDS)
        return keyed, {**summary, "decision": decision_from_gates(gates), "passed": False}, gates

    keyed["physical_pair_key"] = [physical_pair_key(row) for _, row in keyed.iterrows()]
    accepted_mask = (
        (keyed["variant"].astype(str) == "wrong_matched_history")
        & keyed["accepted"].map(_bool_value)
    )
    accepted = keyed[accepted_mask].copy()
    accepted["_accepted_order"] = range(len(accepted))
    selected_indices: list[Any] = []
    pair_counts: dict[str, int] = {}
    for key, group in accepted.groupby("physical_pair_key", observed=True):
        ordered = group.sort_values(
            ["success_drop", "margin_gap", "normal_margin", "_accepted_order"],
            ascending=[False, False, True, True],
        )
        for index, _row in ordered.iterrows():
            if pair_counts.get(str(key), 0) >= int(quotas.max_accepted_rows_per_physical_pair):
                keyed.loc[index, "balance_rejection_reason"] = "physical_pair_accepted_cap"
                continue
            selected_indices.append(index)
            pair_counts[str(key)] = pair_counts.get(str(key), 0) + 1
    keyed.loc[selected_indices, "balanced_exportable"] = True
    keyed.loc[selected_indices, "balance_rejection_reason"] = ""

    balanced = keyed[keyed["balanced_exportable"]].copy()
    summary = summarize_surface(
        balanced,
        margin_bucket_width=margin_bucket_width,
        control_checkpoint_label=control_checkpoint_label,
    )
    thresholds = {
        **DEFAULT_ROBUSTNESS_THRESHOLDS,
        "max_rows_per_pair_fraction": float(quotas.max_rows_per_pair_fraction),
    }
    gates = build_gate_rows(summary, **thresholds)
    decision = decision_from_gates(gates)
    if decision == "admit_boundary_wrong_history_objective":
        decision = "source_balanced_boundary_export_pass"
    summary = {
        **summary,
        "decision": decision,
        "passed": bool(decision == "source_balanced_boundary_export_pass"),
        "balanced_exportable_rows": int(len(balanced)),
        "raw_rows": int(len(keyed)),
    }
    return keyed, summary, gates


def write_source_balance_artifacts(
    *,
    run_dir: Path,
    source_budget_summary: dict[str, Any],
    source_budget_rows: list[dict[str, Any]],
    selected_candidates: pd.DataFrame,
    rejected_candidates: pd.DataFrame,
    marked_boundary_rows: pd.DataFrame,
    balanced_summary: dict[str, Any],
    robustness_gates: list[dict[str, Any]],
    surface_summary_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    balanced = marked_boundary_rows[marked_boundary_rows["balanced_exportable"].map(_bool_value)].copy()
    if {"variant", "accepted", "balanced_exportable"}.issubset(marked_boundary_rows.columns):
        rejected = marked_boundary_rows[
            (marked_boundary_rows["variant"].astype(str) == "wrong_matched_history")
            & marked_boundary_rows["accepted"].map(_bool_value)
            & ~marked_boundary_rows["balanced_exportable"].map(_bool_value)
        ].copy()
    else:
        rejected = marked_boundary_rows.head(0).copy()
    write_json(run_dir / "source_budget_summary.json", source_budget_summary)
    write_csv_rows(run_dir / "source_budget_rows.csv", source_budget_rows)
    write_csv_rows(run_dir / "balanced_candidate_rows.csv", selected_candidates.to_dict("records"))
    write_csv_rows(run_dir / "candidate_balance_rejection_rows.csv", rejected_candidates.to_dict("records"))
    write_csv_rows(run_dir / "boundary_relocation_rows.csv", marked_boundary_rows.to_dict("records"))
    write_csv_rows(run_dir / "balanced_accepted_wrong_history_rows.csv", balanced.to_dict("records"))
    write_csv_rows(run_dir / "balance_rejection_rows.csv", rejected.to_dict("records"))
    write_csv_rows(run_dir / "robustness_gates.csv", robustness_gates)
    if surface_summary_rows is not None:
        write_csv_rows(run_dir / "surface_summary.csv", surface_summary_rows)
    summary = {
        "run_type": "source_balanced_boundary_relocation_surface",
        "source_budget": source_budget_summary,
        "balanced_summary": balanced_summary,
        "source_budget_summary_json": run_dir / "source_budget_summary.json",
        "source_budget_rows_csv": run_dir / "source_budget_rows.csv",
        "balanced_candidate_rows_csv": run_dir / "balanced_candidate_rows.csv",
        "candidate_balance_rejection_rows_csv": run_dir / "candidate_balance_rejection_rows.csv",
        "boundary_relocation_rows_csv": run_dir / "boundary_relocation_rows.csv",
        "balanced_accepted_wrong_history_rows_csv": run_dir / "balanced_accepted_wrong_history_rows.csv",
        "balance_rejection_rows_csv": run_dir / "balance_rejection_rows.csv",
        "robustness_gates_csv": run_dir / "robustness_gates.csv",
        "surface_summary_csv": run_dir / "surface_summary.csv" if surface_summary_rows is not None else None,
        "decision": balanced_summary.get("decision", ""),
        "passed": bool(balanced_summary.get("passed", False)),
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _empty_balanced_summary(
    *,
    decision: str,
    margin_bucket_width: float,
    control_checkpoint_label: str,
) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    marked, summary, gates = mark_balanced_export_rows(
        pd.DataFrame(),
        quotas=SourceBalanceQuotas(max_candidates=0),
        margin_bucket_width=margin_bucket_width,
        control_checkpoint_label=control_checkpoint_label,
    )
    summary = {**summary, "decision": decision, "passed": False}
    return marked, summary, gates


def run_source_balanced_boundary_artifact_smoke(
    *,
    candidate_csv: Path,
    boundary_rows_csv: Path,
    run_dir: Path,
    quotas: SourceBalanceQuotas,
    distance_bucket_width: float = 5.0,
    lateral_bucket_width: float = 1.0,
    min_eligible_physical_pairs: int = 10,
    max_candidate_pair_fraction: float = 0.25,
    margin_bucket_width: float = 0.005,
    control_checkpoint_label: str = "none",
) -> dict[str, Any]:
    """Run source-balance accounting on existing artifacts only."""

    candidate_frame = pd.read_csv(candidate_csv)
    boundary_frame = pd.read_csv(boundary_rows_csv)
    source_budget_summary, source_budget_rows = build_source_budget(
        candidate_frame,
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
        min_eligible_physical_pairs=min_eligible_physical_pairs,
        max_candidate_pair_fraction=max_candidate_pair_fraction,
    )
    selected_candidates, rejected_candidates, candidate_selection_summary = select_source_balanced_candidates(
        candidate_frame,
        quotas=quotas,
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
    )
    marked_boundary_rows, balanced_summary, robustness_gates = mark_balanced_export_rows(
        boundary_frame,
        quotas=quotas,
        margin_bucket_width=margin_bucket_width,
        control_checkpoint_label=control_checkpoint_label,
    )
    summary = write_source_balance_artifacts(
        run_dir=run_dir,
        source_budget_summary=source_budget_summary,
        source_budget_rows=source_budget_rows,
        selected_candidates=selected_candidates,
        rejected_candidates=rejected_candidates,
        marked_boundary_rows=marked_boundary_rows,
        balanced_summary=balanced_summary,
        robustness_gates=robustness_gates,
    )
    summary.update(
        {
            "candidate_csv": candidate_csv,
            "boundary_rows_csv": boundary_rows_csv,
            "candidate_selection_summary": candidate_selection_summary,
            "full_new_mining_run": False,
        }
    )
    write_json(run_dir / "summary.json", summary)
    return summary


def run_source_balanced_boundary_relocation_surface(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    outcome_csv: Path,
    run_dir: Path,
    quotas: SourceBalanceQuotas,
    delay_steps: int,
    max_continuation_steps: int,
    target_normal_margins: tuple[float, ...],
    half_width_inflations: tuple[float, ...],
    body_longitudinals: tuple[float, ...] | None,
    body_laterals: tuple[float, ...] | None,
    body_longitudinal_offsets: tuple[float, ...] | None,
    body_lateral_offsets: tuple[float, ...] | None,
    min_half_width: float,
    max_half_width: float,
    min_normal_margin: float,
    max_normal_margin: float,
    min_margin_gap: float,
    report_variants: tuple[str, ...],
    device: str,
    distance_bucket_width: float = 5.0,
    lateral_bucket_width: float = 1.0,
    min_eligible_physical_pairs: int = 10,
    max_candidate_pair_fraction: float = 0.25,
    margin_bucket_width: float = 0.005,
    control_checkpoint_label: str = "none",
) -> dict[str, Any]:
    """Run relocation replay from source-balanced selected candidates."""

    run_dir.mkdir(parents=True, exist_ok=True)
    outcome_frame = pd.read_csv(outcome_csv)
    source_budget_summary, source_budget_rows = build_source_budget(
        outcome_frame,
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
        min_eligible_physical_pairs=min_eligible_physical_pairs,
        max_candidate_pair_fraction=max_candidate_pair_fraction,
    )
    selected_candidates, rejected_candidates, candidate_selection_summary = select_source_balanced_candidates(
        outcome_frame,
        quotas=quotas,
        distance_bucket_width=distance_bucket_width,
        lateral_bucket_width=lateral_bucket_width,
    )

    all_rows: list[dict[str, Any]] = []
    relocation_replay_started = False
    fail_closed_decision = ""
    if not bool(source_budget_summary.get("source_budget_ready", False)):
        fail_closed_decision = "source_budget_not_ready"
    elif candidate_selection_summary.get("decision") != "source_balanced_candidates_ready":
        fail_closed_decision = "source_balanced_candidates_not_ready"
    else:
        resolved_device = resolve_device(device)
        env_config = load_env_config(env_config_path)
        for checkpoint_spec in checkpoint_specs:
            checkpoint_candidates = selected_candidates[
                selected_candidates["checkpoint_label"].astype(str) == checkpoint_spec.label
            ]
            if checkpoint_candidates.empty:
                continue
            relocation_replay_started = True
            model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
            model.eval()
            response_dim = response_feature_dim_for_model(model)
            snapshots = collect_requested_source_balanced_snapshots(
                model=model,
                env_config=env_config,
                candidate_rows=checkpoint_candidates,
                delay_steps=delay_steps,
                device=resolved_device,
            )
            all_rows.extend(
                build_boundary_relocation_rows(
                    candidate_rows=checkpoint_candidates,
                    snapshots=snapshots,
                    model=model,
                    env_config=env_config,
                    response_dim=response_dim,
                    delay_steps=delay_steps,
                    max_continuation_steps=max_continuation_steps,
                    target_normal_margins=target_normal_margins,
                    half_width_inflations=half_width_inflations,
                    body_longitudinals=body_longitudinals,
                    body_laterals=body_laterals,
                    body_longitudinal_offsets=body_longitudinal_offsets,
                    body_lateral_offsets=body_lateral_offsets,
                    min_half_width=min_half_width,
                    max_half_width=max_half_width,
                    min_normal_margin=min_normal_margin,
                    max_normal_margin=max_normal_margin,
                    min_margin_gap=min_margin_gap,
                    report_variants=report_variants,
                    device=resolved_device,
                )
            )

    if fail_closed_decision:
        marked_boundary_rows, balanced_summary, robustness_gates = _empty_balanced_summary(
            decision=fail_closed_decision,
            margin_bucket_width=margin_bucket_width,
            control_checkpoint_label=control_checkpoint_label,
        )
        surface_summary_rows = summarize_boundary_relocation_rows([], min_accepted_wrong_rows=80)
    else:
        boundary_frame = pd.DataFrame(all_rows)
        marked_boundary_rows, balanced_summary, robustness_gates = mark_balanced_export_rows(
            boundary_frame,
            quotas=quotas,
            margin_bucket_width=margin_bucket_width,
            control_checkpoint_label=control_checkpoint_label,
        )
        surface_summary_rows = summarize_boundary_relocation_rows(
            all_rows,
            min_accepted_wrong_rows=int(DEFAULT_ROBUSTNESS_THRESHOLDS["min_accepted_wrong_rows"]),
        )

    summary = write_source_balance_artifacts(
        run_dir=run_dir,
        source_budget_summary=source_budget_summary,
        source_budget_rows=source_budget_rows,
        selected_candidates=selected_candidates,
        rejected_candidates=rejected_candidates,
        marked_boundary_rows=marked_boundary_rows,
        balanced_summary=balanced_summary,
        robustness_gates=robustness_gates,
        surface_summary_rows=surface_summary_rows,
    )
    summary.update(
        {
            "checkpoint_policies": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
            "env_config": env_config_path,
            "outcome_csv": outcome_csv,
            "candidate_selection_summary": candidate_selection_summary,
            "relocation_replay_started": bool(relocation_replay_started),
            "full_new_mining_run": False,
        }
    )
    write_json(run_dir / "summary.json", summary)
    return summary


def collect_requested_source_balanced_snapshots(
    *,
    model: Any,
    env_config: Any,
    candidate_rows: pd.DataFrame,
    delay_steps: int,
    device: Any,
) -> dict[tuple[int, int], Any]:
    from autodrift.matched_history_outcome_gate import collect_requested_outcome_snapshots

    return collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=requested_snapshot_steps(candidate_rows, delay_steps=delay_steps),
        device=device,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run source-balanced boundary relocation or account over existing CSV artifacts."
    )
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, default=[])
    parser.add_argument("--env-config", type=Path, default=None)
    parser.add_argument("--outcome-csv", type=Path, default=None)
    parser.add_argument("--candidate-csv", type=Path, default=None)
    parser.add_argument("--boundary-rows-csv", type=Path, default=None)
    parser.add_argument("--delay-steps", type=int, default=10)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--max-candidates", type=int, default=512)
    parser.add_argument("--max-candidates-per-physical-pair", type=int, default=8)
    parser.add_argument("--max-candidates-per-checkpoint-target", type=int, default=64)
    parser.add_argument("--max-accepted-rows-per-physical-pair", type=int, default=20)
    parser.add_argument("--target-min-physical-pairs", type=int, default=10)
    parser.add_argument("--target-min-left-steps", type=int, default=5)
    parser.add_argument("--target-min-targets", type=int, default=2)
    parser.add_argument("--max-rows-per-pair-fraction", type=float, default=0.25)
    parser.add_argument("--min-eligible-physical-pairs", type=int, default=10)
    parser.add_argument("--max-candidate-pair-fraction", type=float, default=0.25)
    parser.add_argument("--source-obstacle-distance-bucket-width", type=float, default=5.0)
    parser.add_argument("--source-obstacle-lateral-bucket-width", type=float, default=1.0)
    parser.add_argument("--target-normal-margins", type=parse_float_list, default=DEFAULT_TARGET_NORMAL_MARGINS)
    parser.add_argument("--half-width-inflations", type=parse_float_list, default=(0.0,))
    parser.add_argument("--body-longitudinals", type=parse_float_list, default=None)
    parser.add_argument("--body-laterals", type=parse_float_list, default=None)
    parser.add_argument("--body-longitudinal-offsets", type=parse_float_list, default=None)
    parser.add_argument("--body-lateral-offsets", type=parse_float_list, default=None)
    parser.add_argument("--min-half-width", type=float, default=0.3)
    parser.add_argument("--max-half-width", type=float, default=2.5)
    parser.add_argument("--min-normal-margin", type=float, default=0.0)
    parser.add_argument("--max-normal-margin", type=float, default=0.20)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--report-variants", type=parse_variants, default=DEFAULT_REPORT_VARIANTS)
    parser.add_argument("--margin-bucket-width", type=float, default=0.005)
    parser.add_argument("--control-checkpoint-label", type=str, default="none")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="source_balanced_boundary_relocation_surface")
    quotas = SourceBalanceQuotas(
        max_candidates=args.max_candidates,
        max_candidates_per_physical_pair=args.max_candidates_per_physical_pair,
        max_candidates_per_checkpoint_target=args.max_candidates_per_checkpoint_target,
        max_accepted_rows_per_physical_pair=args.max_accepted_rows_per_physical_pair,
        target_min_physical_pairs=args.target_min_physical_pairs,
        target_min_left_steps=args.target_min_left_steps,
        target_min_targets=args.target_min_targets,
        max_rows_per_pair_fraction=args.max_rows_per_pair_fraction,
    )
    if args.boundary_rows_csv is not None:
        if args.candidate_csv is None:
            raise SystemExit("--candidate-csv is required when --boundary-rows-csv is provided")
        summary = run_source_balanced_boundary_artifact_smoke(
            candidate_csv=args.candidate_csv,
            boundary_rows_csv=args.boundary_rows_csv,
            run_dir=run_dir,
            quotas=quotas,
            distance_bucket_width=args.source_obstacle_distance_bucket_width,
            lateral_bucket_width=args.source_obstacle_lateral_bucket_width,
            min_eligible_physical_pairs=args.min_eligible_physical_pairs,
            max_candidate_pair_fraction=args.max_candidate_pair_fraction,
            margin_bucket_width=args.margin_bucket_width,
            control_checkpoint_label=args.control_checkpoint_label,
        )
    else:
        if not args.checkpoint_policy or args.env_config is None or args.outcome_csv is None:
            raise SystemExit(
                "full relocation mode requires --checkpoint-policy, --env-config, and --outcome-csv"
            )
        summary = run_source_balanced_boundary_relocation_surface(
            checkpoint_specs=tuple(args.checkpoint_policy),
            env_config_path=args.env_config,
            outcome_csv=args.outcome_csv,
            run_dir=run_dir,
            quotas=quotas,
            delay_steps=args.delay_steps,
            max_continuation_steps=args.max_continuation_steps,
            target_normal_margins=args.target_normal_margins,
            half_width_inflations=args.half_width_inflations,
            body_longitudinals=args.body_longitudinals,
            body_laterals=args.body_laterals,
            body_longitudinal_offsets=args.body_longitudinal_offsets,
            body_lateral_offsets=args.body_lateral_offsets,
            min_half_width=args.min_half_width,
            max_half_width=args.max_half_width,
            min_normal_margin=args.min_normal_margin,
            max_normal_margin=args.max_normal_margin,
            min_margin_gap=args.min_margin_gap,
            report_variants=args.report_variants,
            device=args.device,
            distance_bucket_width=args.source_obstacle_distance_bucket_width,
            lateral_bucket_width=args.source_obstacle_lateral_bucket_width,
            min_eligible_physical_pairs=args.min_eligible_physical_pairs,
            max_candidate_pair_fraction=args.max_candidate_pair_fraction,
            margin_bucket_width=args.margin_bucket_width,
            control_checkpoint_label=args.control_checkpoint_label,
        )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
