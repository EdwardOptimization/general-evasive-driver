"""No-training source-diverse sequence-effective corpus refresh."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_extreme_hidden_dynamics_data_route import IdentityResidualGate
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool, parse_float_list
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_near_boundary_wrong_history_pair_mining import BOUNDARY_REPLAY_FIELDS
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    _as_float,
    _as_int,
    read_csv_rows,
    reconstruct_snapshots,
)
from autodrift.v4_full_wrong_history_response_intervention import PAIR_FIELDS, _snapshot_requests
from autodrift.v4_near_boundary_sequence_effectiveness_probe import (
    ACCEPTED_FIELDS,
    DIRECTION_HOLD_SUMMARY_FIELDS,
    SEQUENCE_EFFECTIVENESS_FIELDS,
    accepted_sequence_effective_rows_for_pair,
    classify_sequence_effectiveness_result,
    replay_sequence_effectiveness_pair,
    _best_sequence_by_pair,
    _direction_hold_summary,
    _sequence_diversity,
)


SPLIT_FIELDS = [*ACCEPTED_FIELDS, "split"]


def build_self_pair_rows_from_boundary(boundary_rows: list[dict[str, str]], *, max_boundary_rows: int) -> list[dict[str, Any]]:
    """Build source-diverse self-pair rows from accepted boundary rows.

    Self-pairs intentionally make pair-delta unavailable while preserving all
    component sequence directions. This broadens source coverage before the next
    paired corpus miner is designed.
    """

    ordered = sorted(
        boundary_rows,
        key=lambda row: (
            str(row.get("preferred_fault_family", "")),
            str(row.get("seed", "")),
            _as_int(row.get("source_group_id")),
            _finite_float(row.get("min_clearance_margin")),
            _as_int(row.get("candidate_id")),
        ),
    )
    pairs: list[dict[str, Any]] = []
    for row in ordered:
        if len(pairs) >= int(max_boundary_rows):
            break
        if not parse_bool(row.get("success", False)) or parse_bool(row.get("collision", False)):
            continue
        margin = _finite_float(row.get("min_clearance_margin"))
        if not np.isfinite(margin):
            continue
        pair_id = _as_int(row.get("candidate_id"), len(pairs))
        source_group_id = _as_int(row.get("source_group_id"))
        seed = _as_int(row.get("seed"))
        fault_family = str(row.get("preferred_fault_family", ""))
        fidelity = str(row.get("preferred_fidelity_class", ""))
        warmup = str(row.get("warmup_mode", ""))
        onset = str(row.get("fault_onset_bucket", ""))
        pair = {
            "pair_id": pair_id,
            "left_candidate_id": _as_int(row.get("candidate_id"), pair_id),
            "right_candidate_id": _as_int(row.get("candidate_id"), pair_id),
            "left_source_group_id": source_group_id,
            "right_source_group_id": source_group_id,
            "left_seed": seed,
            "right_seed": seed,
            "left_fault_family": fault_family,
            "right_fault_family": fault_family,
            "left_fidelity_class": fidelity,
            "right_fidelity_class": fidelity,
            "left_warmup_mode": warmup,
            "right_warmup_mode": warmup,
            "left_onset_bucket": onset,
            "right_onset_bucket": onset,
            "ego_response_distance": 0.0,
            "obstacle_geometry_distance": 0.0,
            "first_action_l2": 0.0,
            "normal_margin_gap_abs": 0.0,
            "left_normal_margin": margin,
            "right_normal_margin": margin,
            "left_boundary_axis": str(row.get("boundary_axis", "")),
            "right_boundary_axis": str(row.get("boundary_axis", "")),
            "left_margin_band": str(row.get("margin_band", "")),
            "right_margin_band": str(row.get("margin_band", "")),
            "pair_rank_score": f"self_boundary:{pair_id}",
            "left_step": _as_int(row.get("step")),
            "right_step": _as_int(row.get("step")),
            "left_plan": row,
            "right_plan": row,
        }
        pairs.append(pair)
    return pairs


def split_source_aware(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Deterministically split accepted rows by left source group."""

    groups = sorted({str(row.get("left_source_group_id", "")) for row in rows})
    if not groups:
        return [], [], []
    train_groups: set[str] = set()
    eval_groups: set[str] = set()
    holdout_groups: set[str] = set()
    for index, group in enumerate(groups):
        if len(groups) >= 5 and index % 5 == 0:
            holdout_groups.add(group)
        elif len(groups) >= 3 and index % 5 == 1:
            eval_groups.add(group)
        else:
            train_groups.add(group)
    if not train_groups and groups:
        train_groups.add(groups[-1])
        eval_groups.discard(groups[-1])
        holdout_groups.discard(groups[-1])

    def tagged(subset: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
        return [{**row, "split": split} for row in subset]

    train = [row for row in rows if str(row.get("left_source_group_id", "")) in train_groups]
    eval_rows = [row for row in rows if str(row.get("left_source_group_id", "")) in eval_groups]
    holdout = [row for row in rows if str(row.get("left_source_group_id", "")) in holdout_groups]
    return tagged(train, "train_public"), tagged(eval_rows, "eval_public"), tagged(holdout, "source_holdout_public")


def classify_source_diverse_corpus(
    *,
    actor_changed: bool,
    residual_changed: bool,
    accepted_rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    margin_delta_threshold: float,
    strong_min_rows: int,
    sparse_min_rows: int,
    min_left_sources: int,
    min_left_seeds: int,
    min_left_fault_families: int,
    min_fault_pairs: int,
    min_warmup_pairs: int,
    min_onset_pairs: int,
    min_hold_steps: int,
    min_direction_families: int,
    max_left_source_dominance: float,
    max_left_seed_dominance: float,
    max_direction_family_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_source_diverse_sequence_effective_corpus_contract_violation"
    metrics = _sequence_diversity(accepted_rows)
    strong = bool(
        len(accepted_rows) >= int(strong_min_rows)
        and metrics["unique_left_source_group_count"] >= int(min_left_sources)
        and metrics["unique_left_seed_count"] >= int(min_left_seeds)
        and metrics["unique_left_fault_family_count"] >= int(min_left_fault_families)
        and metrics["unique_fault_family_pair_count"] >= int(min_fault_pairs)
        and metrics["unique_warmup_pair_count"] >= int(min_warmup_pairs)
        and metrics["unique_onset_pair_count"] >= int(min_onset_pairs)
        and metrics["unique_hold_steps_count"] >= int(min_hold_steps)
        and metrics["unique_direction_family_count"] >= int(min_direction_families)
        and metrics["max_left_source_group_dominance"] <= float(max_left_source_dominance)
        and metrics["max_left_seed_dominance"] <= float(max_left_seed_dominance)
        and metrics["max_direction_family_dominance"] <= float(max_direction_family_dominance)
    )
    if strong:
        return "v4_source_diverse_sequence_effective_corpus_pass"
    sparse = bool(
        len(accepted_rows) >= int(sparse_min_rows)
        and metrics["unique_left_source_group_count"] >= 6
        and metrics["unique_fault_family_pair_count"] >= 5
    )
    if sparse:
        return "v4_source_diverse_sequence_effective_corpus_sparse_positive"
    max_abs = max(
        (_finite_float(row.get("abs_margin_delta")) for row in all_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    flips = sum(1 for row in all_rows if parse_bool(row.get("success_flip", False)) or parse_bool(row.get("collision_flip", False)))
    if len(accepted_rows) < int(sparse_min_rows) or ((not np.isfinite(max_abs) or max_abs < float(margin_delta_threshold)) and flips <= 0):
        return "v4_source_diverse_sequence_effective_corpus_all_weak"
    return "v4_source_diverse_sequence_effective_corpus_source_limited"


def _source_gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate_name": "actor_checksum_unchanged",
            "value": not bool(summary["actor_backbone_changed"]),
            "threshold": "true",
            "passed": not bool(summary["actor_backbone_changed"]),
            "notes": "no actor training allowed",
        },
        {
            "gate_name": "residual_head_checksum_unchanged",
            "value": not bool(summary["residual_head_changed"]),
            "threshold": "true",
            "passed": not bool(summary["residual_head_changed"]),
            "notes": "no residual-head training allowed",
        },
        {
            "gate_name": "primary_sequence_effective_rows",
            "value": summary["accepted_primary_sequence_effective_rows"],
            "threshold": summary["strong_min_rows"],
            "passed": int(summary["accepted_primary_sequence_effective_rows"]) >= int(summary["strong_min_rows"]),
            "notes": "direct sequence override evidence is controllability only",
        },
        {
            "gate_name": "source_diversity",
            "value": summary["unique_left_source_group_count"],
            "threshold": summary["min_left_sources"],
            "passed": int(summary["unique_left_source_group_count"]) >= int(summary["min_left_sources"]),
            "notes": "M844 target is broader source coverage than M841",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M844 cannot promote",
        },
    ]


def run_source_diverse_sequence_effective_corpus(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    accepted_boundary_rows_path: Path,
    seed_sequence_positive_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_boundary_rows: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_snapshots_per_group: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    max_continuation_steps: int,
    epsilon_grid: tuple[float, ...],
    hold_steps_grid: tuple[int, ...],
    boundary_margin_threshold: float,
    margin_delta_threshold: float,
    action_l2_threshold: float,
    strong_min_rows: int,
    sparse_min_rows: int,
    min_left_sources: int,
    min_left_seeds: int,
    min_left_fault_families: int,
    min_fault_pairs: int,
    min_warmup_pairs: int,
    min_onset_pairs: int,
    min_hold_steps: int,
    min_direction_families: int,
    max_left_source_dominance: float,
    max_left_seed_dominance: float,
    max_direction_family_dominance: float,
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()

    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("M844 corpus refresh requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    actor_checksum_before = model_parameter_checksum(model)
    residual_head = _load_residual_head(
        residual_head_path,
        expected_feature_dim=int(model.actor_mean.in_features),
        device=resolved_device,
    )
    residual_head.eval()
    for parameter in residual_head.parameters():
        parameter.requires_grad_(False)
    residual_checksum_before = model_parameter_checksum(residual_head)
    identity_gate = IdentityResidualGate().to(resolved_device)

    accepted_boundary_rows_raw = read_csv_rows(accepted_boundary_rows_path)
    seed_sequence_positive_rows = read_csv_rows(seed_sequence_positive_rows_path)
    candidate_plan_rows = read_csv_rows(candidate_plan_rows_path)
    source_rows = read_csv_rows(source_rows_path)
    boundary_rows = [
        row
        for row in accepted_boundary_rows_raw
        if parse_bool(row.get("accepted_primary", True))
        and parse_bool(row.get("success", False))
        and not parse_bool(row.get("collision", False))
        and _finite_float(row.get("min_clearance_margin")) <= float(boundary_margin_threshold)
    ]
    pair_rows = build_self_pair_rows_from_boundary(boundary_rows, max_boundary_rows=int(max_boundary_rows))
    requests = _snapshot_requests(pair_rows)
    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=requests,
        source_rows=source_rows,
        fault_by_name=fault_by_name,
        model=model,
        residual_head=residual_head,
        env_config=env_config,
        scenario_config=scenario_config,
        alpha=float(alpha),
        min_step=int(min_step),
        max_steps=int(max_steps),
        snapshot_stride=int(snapshot_stride),
        max_snapshots_per_group=int(max_snapshots_per_group),
        warmup_steps=int(warmup_steps),
        steer_amplitude=float(steer_amplitude),
        brake_amplitude=float(brake_amplitude),
        warmup_period_steps=int(warmup_period_steps),
        device=resolved_device,
    )

    replay_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    for pair in pair_rows:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        try:
            rows = replay_sequence_effectiveness_pair(
                pair=pair,
                left_snapshot=left_snapshot,
                right_snapshot=right_snapshot,
                model=model,
                residual_head=residual_head,
                identity_gate=identity_gate,
                env_config=env_config,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                epsilon_grid=tuple(float(value) for value in epsilon_grid),
                hold_steps_grid=tuple(int(value) for value in hold_steps_grid),
                directions=(
                    "steer_positive",
                    "steer_negative",
                    "throttle_positive",
                    "throttle_negative",
                    "brake_positive",
                    "brake_negative",
                ),
                device=resolved_device,
            )
        except Exception as exc:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": f"replay_error:{type(exc).__name__}"})
            continue
        replay_rows.extend(rows)
        accepted_rows.extend(
            accepted_sequence_effective_rows_for_pair(
                rows,
                boundary_margin_threshold=float(boundary_margin_threshold),
                margin_delta_threshold=float(margin_delta_threshold),
                action_l2_threshold=float(action_l2_threshold),
            )
        )
        _append_progress(progress_path, {"stage": "source_diverse_sequence_replay", "pair_id": int(pair["pair_id"]), "rows": len(rows)})

    train_rows, eval_rows, holdout_rows = split_source_aware(accepted_rows)
    accepted_degradation = [row for row in accepted_rows if row.get("accepted_class") == "directional_degradation"]
    accepted_improvement = [row for row in accepted_rows if row.get("accepted_class") == "directional_improvement"]
    success_flip_rows = [row for row in replay_rows if parse_bool(row.get("success_flip", False))]
    collision_flip_rows = [row for row in replay_rows if parse_bool(row.get("collision_flip", False))]
    max_abs_margin_delta = max(
        (_finite_float(row.get("abs_margin_delta")) for row in replay_rows if np.isfinite(_finite_float(row.get("abs_margin_delta")))),
        default=float("nan"),
    )
    max_degradation_margin_delta = max(
        (
            _finite_float(row.get("degradation_margin_delta"), default=0.0)
            for row in replay_rows
            if np.isfinite(_finite_float(row.get("degradation_margin_delta"), default=float("nan")))
        ),
        default=float("nan"),
    )
    max_improvement_margin_delta = max(
        (
            _finite_float(row.get("improvement_margin_delta"), default=0.0)
            for row in replay_rows
            if np.isfinite(_finite_float(row.get("improvement_margin_delta"), default=float("nan")))
        ),
        default=float("nan"),
    )
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_source_diverse_corpus(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        accepted_rows=accepted_rows,
        all_rows=replay_rows,
        margin_delta_threshold=float(margin_delta_threshold),
        strong_min_rows=int(strong_min_rows),
        sparse_min_rows=int(sparse_min_rows),
        min_left_sources=int(min_left_sources),
        min_left_seeds=int(min_left_seeds),
        min_left_fault_families=int(min_left_fault_families),
        min_fault_pairs=int(min_fault_pairs),
        min_warmup_pairs=int(min_warmup_pairs),
        min_onset_pairs=int(min_onset_pairs),
        min_hold_steps=int(min_hold_steps),
        min_direction_families=int(min_direction_families),
        max_left_source_dominance=float(max_left_source_dominance),
        max_left_seed_dominance=float(max_left_seed_dominance),
        max_direction_family_dominance=float(max_direction_family_dominance),
    )
    diversity_summary = {
        "boundary_rows": _sequence_diversity(pair_rows),
        "accepted_primary_sequence_effective": _sequence_diversity(accepted_rows),
        "accepted_directional_degradation": _sequence_diversity(accepted_degradation),
        "accepted_directional_improvement": _sequence_diversity(accepted_improvement),
        "train_public": _sequence_diversity(train_rows),
        "eval_public": _sequence_diversity(eval_rows),
        "source_holdout_public": _sequence_diversity(holdout_rows),
        "m841_seed_positive_rows": _sequence_diversity(seed_sequence_positive_rows),
    }
    all_rejections = [*snapshot_rejections, *replay_rejections]
    direction_hold_summary = _direction_hold_summary(replay_rows, accepted_rows, tuple(int(value) for value in hold_steps_grid))
    best_rows = _best_sequence_by_pair(replay_rows)

    write_csv_rows(run_dir / "candidate_source_rows.csv", boundary_rows, fieldnames=BOUNDARY_REPLAY_FIELDS)
    write_csv_rows(run_dir / "boundary_rows.csv", boundary_rows, fieldnames=BOUNDARY_REPLAY_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "sequence_effective_rows.csv", replay_rows, fieldnames=SEQUENCE_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "accepted_sequence_effective_rows.csv", accepted_rows, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "best_sequence_by_pair.csv", best_rows, fieldnames=SEQUENCE_EFFECTIVENESS_FIELDS)
    write_csv_rows(run_dir / "direction_hold_summary.csv", direction_hold_summary, fieldnames=DIRECTION_HOLD_SUMMARY_FIELDS)
    write_csv_rows(run_dir / "train_public_rows.csv", train_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "eval_public_rows.csv", eval_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "source_holdout_public_rows.csv", holdout_rows, fieldnames=SPLIT_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", all_rejections)
    write_json(run_dir / "diversity_summary.json", diversity_summary)

    accepted_metrics = diversity_summary["accepted_primary_sequence_effective"]
    summary = {
        "run_type": "v4_source_diverse_sequence_effective_corpus",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "accepted_boundary_rows": accepted_boundary_rows_path,
        "seed_sequence_positive_rows": seed_sequence_positive_rows_path,
        "alpha": float(alpha),
        "epsilon_l2_grid": list(float(value) for value in epsilon_grid),
        "hold_steps_grid": list(int(value) for value in hold_steps_grid),
        "source_rows_count": int(len(source_rows)),
        "candidate_plan_rows_count": int(len(candidate_plan_rows)),
        "seed_sequence_positive_rows_count": int(len(seed_sequence_positive_rows)),
        "candidate_source_rows": int(len(boundary_rows)),
        "boundary_rows": int(len(boundary_rows)),
        "reconstructed_snapshot_rows": int(len(snapshot_rows)),
        "sequence_effective_rows": int(len(replay_rows)),
        "accepted_primary_sequence_effective_rows": int(len(accepted_rows)),
        "accepted_directional_degradation_rows": int(len(accepted_degradation)),
        "accepted_directional_improvement_rows": int(len(accepted_improvement)),
        "success_flip_rows": int(len(success_flip_rows)),
        "collision_flip_rows": int(len(collision_flip_rows)),
        "train_public_rows": int(len(train_rows)),
        "eval_public_rows": int(len(eval_rows)),
        "source_holdout_public_rows": int(len(holdout_rows)),
        "unique_left_source_group_count": int(accepted_metrics["unique_left_source_group_count"]),
        "unique_left_seed_count": int(accepted_metrics["unique_left_seed_count"]),
        "unique_left_fault_family_count": int(accepted_metrics["unique_left_fault_family_count"]),
        "unique_fault_family_pair_count": int(accepted_metrics["unique_fault_family_pair_count"]),
        "max_left_source_group_dominance": float(accepted_metrics["max_left_source_group_dominance"]),
        "max_left_seed_dominance": float(accepted_metrics["max_left_seed_dominance"]),
        "max_direction_family_dominance": float(accepted_metrics["max_direction_family_dominance"]),
        "max_abs_margin_delta": max_abs_margin_delta,
        "max_degradation_margin_delta": max_degradation_margin_delta,
        "max_improvement_margin_delta": max_improvement_margin_delta,
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "margin_delta_threshold": float(margin_delta_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "strong_min_rows": int(strong_min_rows),
        "sparse_min_rows": int(sparse_min_rows),
        "min_left_sources": int(min_left_sources),
        "min_left_seeds": int(min_left_seeds),
        "min_left_fault_families": int(min_left_fault_families),
        "min_fault_pairs": int(min_fault_pairs),
        "min_warmup_pairs": int(min_warmup_pairs),
        "min_onset_pairs": int(min_onset_pairs),
        "min_hold_steps": int(min_hold_steps),
        "min_direction_families": int(min_direction_families),
        "max_left_source_dominance_threshold": float(max_left_source_dominance),
        "max_left_seed_dominance_threshold": float(max_left_seed_dominance),
        "max_direction_family_dominance_threshold": float(max_direction_family_dominance),
        "diversity_summary_json": run_dir / "diversity_summary.json",
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "residual_head_changed": bool(residual_checksum_before != residual_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "residual_head_checksum_before": residual_checksum_before,
        "residual_head_checksum_after": residual_checksum_after,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "summary_json": run_dir / "summary.json",
        "candidate_source_rows_csv": run_dir / "candidate_source_rows.csv",
        "boundary_rows_csv": run_dir / "boundary_rows.csv",
        "sequence_effective_rows_csv": run_dir / "sequence_effective_rows.csv",
        "accepted_sequence_effective_rows_csv": run_dir / "accepted_sequence_effective_rows.csv",
        "train_public_rows_csv": run_dir / "train_public_rows.csv",
        "eval_public_rows_csv": run_dir / "eval_public_rows.csv",
        "source_holdout_public_rows_csv": run_dir / "source_holdout_public_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _source_gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 source-diverse sequence-effective corpus refresh.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--accepted-boundary-rows", type=Path, required=True)
    parser.add_argument("--seed-sequence-positive-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-boundary-rows", type=int, default=256)
    parser.add_argument("--max-base-faults", type=int, default=10)
    parser.add_argument("--max-fault-specs", type=int, default=18)
    parser.add_argument("--max-snapshots-per-group", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=24)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    parser.add_argument("--max-continuation-steps", type=int, default=None)
    parser.add_argument("--epsilon-l2-grid", type=str, default="0.025,0.05,0.075")
    parser.add_argument("--hold-steps-grid", type=str, default="4,6")
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.05)
    parser.add_argument("--margin-delta-threshold", type=float, default=0.01)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--strong-min-rows", type=int, default=120)
    parser.add_argument("--sparse-min-rows", type=int, default=40)
    parser.add_argument("--min-left-sources", type=int, default=10)
    parser.add_argument("--min-left-seeds", type=int, default=4)
    parser.add_argument("--min-left-fault-families", type=int, default=5)
    parser.add_argument("--min-fault-pairs", type=int, default=8)
    parser.add_argument("--min-warmup-pairs", type=int, default=3)
    parser.add_argument("--min-onset-pairs", type=int, default=5)
    parser.add_argument("--min-hold-steps", type=int, default=2)
    parser.add_argument("--min-direction-families", type=int, default=3)
    parser.add_argument("--max-left-source-dominance", type=float, default=0.30)
    parser.add_argument("--max-left-seed-dominance", type=float, default=0.35)
    parser.add_argument("--max-direction-family-dominance", type=float, default=0.55)
    args = parser.parse_args()

    scenario_config = load_scenario_config(args.scenario_config)
    max_steps = int(args.max_steps) if args.max_steps is not None else int(scenario_config.get("max_steps", 340))
    min_step = int(args.min_step) if args.min_step is not None else int(scenario_config.get("min_step", 20))
    snapshot_stride = int(args.snapshot_stride) if args.snapshot_stride is not None else int(scenario_config.get("snapshot_stride", 3))
    max_continuation_steps = (
        int(args.max_continuation_steps)
        if args.max_continuation_steps is not None
        else int(scenario_config.get("max_continuation_steps", 70))
    )
    summary = run_source_diverse_sequence_effective_corpus(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        accepted_boundary_rows_path=args.accepted_boundary_rows,
        seed_sequence_positive_rows_path=args.seed_sequence_positive_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_boundary_rows=int(args.max_boundary_rows),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_steps=max_steps,
        min_step=min_step,
        snapshot_stride=snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
        max_continuation_steps=max_continuation_steps,
        epsilon_grid=tuple(parse_float_list(args.epsilon_l2_grid)),
        hold_steps_grid=tuple(int(value) for value in parse_float_list(args.hold_steps_grid)),
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        margin_delta_threshold=float(args.margin_delta_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        strong_min_rows=int(args.strong_min_rows),
        sparse_min_rows=int(args.sparse_min_rows),
        min_left_sources=int(args.min_left_sources),
        min_left_seeds=int(args.min_left_seeds),
        min_left_fault_families=int(args.min_left_fault_families),
        min_fault_pairs=int(args.min_fault_pairs),
        min_warmup_pairs=int(args.min_warmup_pairs),
        min_onset_pairs=int(args.min_onset_pairs),
        min_hold_steps=int(args.min_hold_steps),
        min_direction_families=int(args.min_direction_families),
        max_left_source_dominance=float(args.max_left_source_dominance),
        max_left_seed_dominance=float(args.max_left_seed_dominance),
        max_direction_family_dominance=float(args.max_direction_family_dominance),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
