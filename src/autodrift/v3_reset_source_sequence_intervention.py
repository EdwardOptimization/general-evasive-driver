"""Sequence-level interventions over M740 v3 reset-sensitive source rows."""

from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.sequence_command_response_intervention import (
    SEQUENCE_VARIANTS,
    _dominance_fraction,
    _parse_int_list,
    _row_for_sequence_variant,
    _sequence_group_summary,
    classify_sequence_result,
    replay_sequence_variant,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import _collect_seed_snapshots, _find_snapshot, _source_summary
from autodrift.train_ppo import resolve_device


V3_EXTRA_SOURCE_FIELDS = (
    "pair_id",
    "pairing_rule",
    "reset_action_l2_gap",
    "reset_margin_gap",
    "history_margin_gap",
    "action_l2_gap",
    "match_distance",
    "feature_distance",
    "acceptance_reason",
    "rejection_reason",
)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not Path(path).exists():
        return []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bucket_float(value: Any, *, width: float, missing: str = "missing") -> str:
    number = _finite_float(value)
    if not np.isfinite(number):
        return missing
    return str(int(np.floor(float(number) / float(width))))


def _fault_pair(row: dict[str, Any]) -> str:
    raw = str(row.get("fault_family_pair", "")).strip()
    if raw:
        return raw
    return f"{row.get('preferred_fault_family', '')}->{row.get('wrong_fault_family', '')}"


def _severity_pair(row: dict[str, Any]) -> str:
    raw = str(row.get("severity_pair", "")).strip()
    if raw:
        return raw
    return f"{row.get('preferred_fault_severity', '')}->{row.get('wrong_fault_severity', '')}"


def _within_seed_window(row: dict[str, Any], *, seed_start: int, seed_count: int) -> bool:
    seed = int(row.get("seed", -1))
    return int(seed_start) <= seed < int(seed_start) + int(seed_count)


def _primary_candidate(row: dict[str, Any], *, min_action_l2_gap: float) -> bool:
    normal_margin = _finite_float(row.get("normal_margin"))
    return bool(
        _parse_bool(row.get("reset_history_action_critical", False))
        and np.isfinite(normal_margin)
        and normal_margin >= 0.0
        and _finite_float(row.get("reset_action_l2_gap"), default=0.0) >= float(min_action_l2_gap)
    )


def _sentinel_candidate(row: dict[str, Any]) -> bool:
    normal_margin = _finite_float(row.get("normal_margin"))
    return bool(
        str(row.get("rejection_reason", "")) == "history_insensitive_too_mild"
        and np.isfinite(normal_margin)
        and normal_margin > 0.5
        and _finite_float(row.get("action_l2_gap"), default=1.0) < 0.005
        and _finite_float(row.get("reset_margin_gap"), default=1.0) < 0.01
        and _finite_float(row.get("reset_action_l2_gap"), default=1.0) < 0.019
    )


def _source_row(raw: dict[str, Any], *, role: str, source_pool: str) -> dict[str, Any]:
    row = dict(raw)
    row["source_role"] = role
    row["proposal_id"] = str(row.get("pair_id", ""))
    row["selected_index"] = str(row.get("selected_index", ""))
    row["fault_family_pair"] = _fault_pair(row)
    row["severity_pair"] = _severity_pair(row)
    row["source_pool"] = source_pool
    row["step_bucket"] = str(row.get("step_bucket", "")).strip() or str(int(int(row.get("step", 0)) // 20))
    row["obstacle_distance_bucket"] = str(row.get("obstacle_distance_bucket", "")).strip() or "missing"
    if "acceptance_reason" not in row:
        row["acceptance_reason"] = ""
    if "rejection_reason" not in row:
        row["rejection_reason"] = ""
    return row


def _selection_score(row: dict[str, Any]) -> float:
    reset_action = _finite_float(row.get("reset_action_l2_gap"), default=0.0)
    reset_margin = _finite_float(row.get("reset_margin_gap"), default=0.0)
    normal_margin = _finite_float(row.get("normal_margin"), default=0.0)
    return float(reset_action + 0.25 * max(reset_margin, 0.0) - 0.0005 * max(normal_margin, 0.0))


def _sentinel_score(row: dict[str, Any]) -> float:
    reset_action = _finite_float(row.get("reset_action_l2_gap"), default=1.0)
    reset_margin = abs(_finite_float(row.get("reset_margin_gap"), default=1.0))
    normal_margin = _finite_float(row.get("normal_margin"), default=0.0)
    return float(-reset_action - reset_margin + 0.0001 * max(normal_margin, 0.0))


def _source_key(row: dict[str, Any]) -> tuple[str, ...]:
    normal_margin = _finite_float(row.get("normal_margin"), default=0.0)
    return (
        str(row.get("source_role", "")),
        str(row.get("seed", "")),
        str(row.get("preferred_fault_family", "")),
        str(row.get("wrong_fault_family", "")),
        str(row.get("fault_family_pair", "")),
        str(row.get("preferred_fault_severity", "")),
        str(row.get("wrong_fault_severity", "")),
        str(row.get("assigned_split", "")),
        str(row.get("step_bucket", "")),
        _bucket_float(normal_margin, width=0.10),
        _bucket_float(row.get("reset_action_l2_gap"), width=0.005),
        _bucket_float(row.get("reset_margin_gap"), width=0.005),
        str(row.get("pairing_rule", "")),
    )


def _balanced_group_order(keys: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    dimensions = (0, 2, 3, 4, 1, 5, 6, 7, 8, 9, 10, 11, 12)

    def order(items: list[tuple[str, ...]], dims: tuple[int, ...]) -> list[tuple[str, ...]]:
        if len(items) <= 1 or not dims:
            return sorted(items)
        dim = dims[0]
        grouped: dict[str, list[tuple[str, ...]]] = {}
        for item in items:
            grouped.setdefault(str(item[dim] if dim < len(item) else ""), []).append(item)
        ordered_groups = [order(grouped[value], dims[1:]) for value in sorted(grouped)]
        output: list[tuple[str, ...]] = []
        while ordered_groups:
            next_groups: list[list[tuple[str, ...]]] = []
            for group in ordered_groups:
                if not group:
                    continue
                output.append(group[0])
                if len(group) > 1:
                    next_groups.append(group[1:])
            ordered_groups = next_groups
        return output

    return order(keys, dimensions)


def _round_robin_take(groups: dict[tuple[str, ...], list[dict[str, Any]]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    keys = _balanced_group_order(list(groups))
    cursor = {key: 0 for key in keys}
    while len(selected) < int(limit):
        progressed = False
        for key in keys:
            offset = cursor[key]
            rows = groups[key]
            if offset >= len(rows):
                continue
            selected.append(rows[offset])
            cursor[key] = offset + 1
            progressed = True
            if len(selected) >= int(limit):
                break
        if not progressed:
            break
    return selected


def _group_source_candidates(rows: list[dict[str, Any]], *, sentinel: bool) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(_source_key(row), []).append(row)
    for key, group_rows in groups.items():
        group_rows.sort(key=_sentinel_score if sentinel else _selection_score, reverse=True)
    return groups


def load_v3_reset_source_rows(
    *,
    reset_rows_path: Path,
    rejected_rows_path: Path,
    seed_start: int,
    seed_count: int,
    max_source_rows: int,
    min_action_l2_gap: float = 0.015,
    sentinel_fraction: float = 0.10,
) -> list[dict[str, Any]]:
    primary_candidates = [
        _source_row(row, role="primary", source_pool="m740_reset_only")
        for row in _read_csv_rows(reset_rows_path)
        if _within_seed_window(row, seed_start=seed_start, seed_count=seed_count)
        and _primary_candidate(row, min_action_l2_gap=min_action_l2_gap)
    ]
    sentinel_candidates = [
        _source_row(row, role="sentinel", source_pool="m740_history_insensitive")
        for row in _read_csv_rows(rejected_rows_path)
        if _within_seed_window(row, seed_start=seed_start, seed_count=seed_count) and _sentinel_candidate(row)
    ]
    sentinel_target = (
        max(1, int(round(float(max_source_rows) * float(sentinel_fraction)))) if sentinel_candidates else 0
    )
    primary_target = max(0, int(max_source_rows) - int(sentinel_target))
    selected = _round_robin_take(_group_source_candidates(primary_candidates, sentinel=False), primary_target)
    selected.extend(_round_robin_take(_group_source_candidates(sentinel_candidates, sentinel=True), sentinel_target))
    for index, row in enumerate(selected):
        row["source_index"] = int(index)
        row["selected_index"] = int(index)
    return selected


def _v3_source_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = _source_summary(rows)
    wrong_families = [str(row.get("wrong_fault_family", "")) for row in rows]
    severities = [str(row.get("preferred_fault_severity", "")) for row in rows]
    reset_rows = [row for row in rows if str(row.get("source_role", "")) != "sentinel"]
    sentinel_rows = [row for row in rows if str(row.get("source_role", "")) == "sentinel"]
    return {
        **base,
        "source_unique_wrong_fault_families": int(len(set(wrong_families))),
        "source_unique_preferred_severities": int(len(set(severities))),
        "source_reset_rows": int(len(reset_rows)),
        "source_sentinel_rows": int(len(sentinel_rows)),
    }


def _row_for_v3_sequence_variant(
    *,
    source: dict[str, Any],
    variant: str,
    horizon: int,
    result: dict[str, Any],
    normal: dict[str, Any],
    action_threshold: float,
    margin_threshold: float,
) -> dict[str, Any]:
    row = _row_for_sequence_variant(
        source=source,
        variant=variant,
        horizon=horizon,
        result=result,
        normal=normal,
        action_threshold=action_threshold,
        margin_threshold=margin_threshold,
    )
    for key in V3_EXTRA_SOURCE_FIELDS:
        row[key] = source.get(key, "")
    row["source_kind"] = "v3_reset_source"
    return row


def classify_v3_reset_sequence_result(
    *,
    result_class: str,
) -> str:
    mapping = {
        "sequence_outcome_positive": "v3_reset_sequence_outcome_positive",
        "sequence_action_only": "v3_reset_sequence_action_only",
        "sequence_source_balance_blocked": "v3_reset_source_balance_blocked",
        "sequence_artifact": "v3_reset_sequence_artifact",
        "sequence_neutral": "v3_reset_sequence_neutral",
    }
    return mapping.get(str(result_class), f"v3_reset_{result_class}")


def run_v3_reset_source_sequence_intervention(
    *,
    checkpoint_path: Path,
    config_path: Path,
    reset_rows_path: Path,
    rejected_rows_path: Path,
    seed_start: int,
    seed_count: int,
    max_source_rows: int,
    horizons: tuple[int, ...],
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("v3 reset-source sequence intervention requires an online recurrent checkpoint")
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    min_action_l2_gap = float(config.get("min_action_l2_gap", 0.015))
    min_history_margin_gap = float(config.get("min_history_margin_gap", 0.02))
    max_continuation_steps = int(config.get("max_continuation_steps", 60))
    source_rows = load_v3_reset_source_rows(
        reset_rows_path=reset_rows_path,
        rejected_rows_path=rejected_rows_path,
        seed_start=seed_start,
        seed_count=seed_count,
        max_source_rows=max_source_rows,
        min_action_l2_gap=min_action_l2_gap,
    )
    source_balance = _v3_source_summary(source_rows)
    faults = [NOMINAL_FAULT, *config["faults"]]
    snapshots_by_seed: dict[int, list[Any]] = {}
    for seed in sorted({int(row["seed"]) for row in source_rows}):
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=seed,
            config=config,
            device=resolved_device,
        )

    source_output_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for source in source_rows:
        source_record = dict(source)
        source_output_rows.append(source_record)
        snapshot = _find_snapshot(
            snapshots_by_seed.get(int(source_record["seed"]), []),
            fault_name=str(source_record["preferred_fault"]),
            step=int(source_record["step"]),
        )
        if snapshot is None:
            rejected_rows.append({**source_record, "rejection_reason": "source_snapshot_missing"})
            continue
        normal, normal_actions = replay_sequence_variant(
            model=model,
            snapshot=snapshot,
            env_config=env_config,
            variant="normal",
            horizon=max(horizons),
            response_dim=response_dim,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        normal_margin = _finite_float(normal.get("min_clearance_margin"))
        normal_ok = bool(normal.get("success", False) or (np.isfinite(normal_margin) and normal_margin >= 0.0))
        for horizon in horizons:
            rollout_rows.append(
                _row_for_v3_sequence_variant(
                    source=source_record,
                    variant="normal",
                    horizon=int(horizon),
                    result=normal,
                    normal=normal,
                    action_threshold=min_action_l2_gap,
                    margin_threshold=min_history_margin_gap,
                )
            )
            for variant in SEQUENCE_VARIANTS:
                result, _ = replay_sequence_variant(
                    model=model,
                    snapshot=snapshot,
                    env_config=env_config,
                    variant=variant,
                    horizon=int(horizon),
                    response_dim=response_dim,
                    normal_actions=normal_actions,
                    max_continuation_steps=max_continuation_steps,
                    device=resolved_device,
                )
                rollout_rows.append(
                    _row_for_v3_sequence_variant(
                        source=source_record,
                        variant=variant,
                        horizon=int(horizon),
                        result=result,
                        normal=normal,
                        action_threshold=min_action_l2_gap,
                        margin_threshold=min_history_margin_gap,
                    )
                )
        if not normal_ok:
            rejected_rows.append({**source_record, "rejection_reason": "normal_history_failed"})

    sequence_action_rows = [row for row in rollout_rows if bool(row.get("sequence_action_critical", False))]
    sequence_outcome_rows = [row for row in rollout_rows if bool(row.get("sequence_outcome_critical", False))]
    sentinel_rows = [row for row in rollout_rows if bool(row.get("sentinel", False))]
    sentinel_false_positive_rows = [
        row
        for row in sentinel_rows
        if bool(row.get("sequence_action_critical", False)) and bool(row.get("sequence_outcome_critical", False))
    ]
    normal_rows = [row for row in rollout_rows if row.get("variant") == "normal"]
    normal_failed_rejected = [row for row in rejected_rows if row.get("rejection_reason") == "normal_history_failed"]
    normal_history_retention_pass = bool(
        normal_rows
        and not any(str(row.get("terminal_reason", "")) == "artifact" for row in normal_rows)
        and len(normal_failed_rejected) <= max(1, len(source_rows) // 2)
    )
    sentinel_false_positive_rate = float(len(sentinel_false_positive_rows) / max(len(sentinel_rows), 1))
    outcome_seeds = [int(row.get("seed", -1)) for row in sequence_outcome_rows]
    outcome_pairs = [str(row.get("fault_family_pair", "")) for row in sequence_outcome_rows]
    action_seeds = [int(row.get("seed", -1)) for row in sequence_action_rows]
    checksum_after = model_parameter_checksum(model)
    base_result = classify_sequence_result(
        source_candidate_rows=len(source_rows),
        sequence_action_critical_rows=len(sequence_action_rows),
        sequence_outcome_critical_rows=len(sequence_outcome_rows),
        unique_source_seeds=int(source_balance["source_unique_seeds"]),
        unique_source_preferred_fault_families=int(source_balance["source_unique_preferred_fault_families"]),
        unique_source_fault_family_pairs=int(source_balance["source_unique_fault_family_pairs"]),
        source_max_seed_dominance=float(source_balance["source_max_seed_dominance"]),
        source_max_preferred_family_dominance=float(source_balance["source_max_preferred_family_dominance"]),
        source_sentinel_fraction=float(source_balance["source_sentinel_fraction"]),
        sentinel_false_positive_rate=sentinel_false_positive_rate,
        normal_history_retention_pass=normal_history_retention_pass,
        actor_parameters_changed=bool(checksum_before != checksum_after),
        unique_sequence_action_seeds=len(set(action_seeds)),
        unique_sequence_outcome_seeds=len(set(outcome_seeds)),
        unique_sequence_outcome_fault_family_pairs=len(set(outcome_pairs)),
        max_sequence_outcome_seed_dominance=_dominance_fraction(outcome_seeds),
        min_source_rows=min(512, int(max_source_rows)),
        min_source_seeds=16,
        min_source_families=7,
        min_source_pairs=16,
        max_source_seed_dominance=0.16,
        max_source_family_dominance=0.25,
        min_sequence_action_rows=300,
        min_sequence_action_seeds=10,
        min_sequence_outcome_rows=20,
        min_sequence_outcome_seeds=8,
        min_sequence_outcome_pairs=4,
        max_sequence_outcome_dominance=0.25,
    )
    result_class = classify_v3_reset_sequence_result(result_class=base_result)

    write_csv_rows(run_dir / "source_rows.csv", source_output_rows)
    write_csv_rows(run_dir / "intervention_rollouts.csv", rollout_rows)
    write_csv_rows(
        run_dir / "sequence_critical_rows.csv",
        [row for row in rollout_rows if bool(row.get("sequence_action_critical", False)) or bool(row.get("sequence_outcome_critical", False))],
    )
    write_csv_rows(run_dir / "sentinel_rows.csv", sentinel_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "variant_summary.csv", _sequence_group_summary(rollout_rows, ("variant",)))
    write_csv_rows(run_dir / "horizon_summary.csv", _sequence_group_summary(rollout_rows, ("horizon",)))
    write_csv_rows(run_dir / "fault_family_summary.csv", _sequence_group_summary(rollout_rows, ("fault_family_pair", "variant")))

    summary = {
        "run_type": "v3_reset_source_sequence_intervention",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "reset_rows": reset_rows_path,
        "rejected_rows_input": rejected_rows_path,
        "env_config": config.get("env_config"),
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "fault_count": int(len(faults) - 1),
        "source_candidate_rows": int(len(source_rows)),
        **source_balance,
        "horizons": [int(item) for item in horizons],
        "rollout_rows": int(len(rollout_rows)),
        "sequence_action_critical_rows": int(len(sequence_action_rows)),
        "sequence_outcome_critical_rows": int(len(sequence_outcome_rows)),
        "unique_sequence_action_seeds": int(len(set(action_seeds))),
        "unique_sequence_outcome_seeds": int(len(set(outcome_seeds))),
        "unique_sequence_outcome_fault_family_pairs": int(len(set(outcome_pairs))),
        "max_sequence_outcome_seed_dominance": float(_dominance_fraction(outcome_seeds)),
        "normal_failed_rejected": int(len(normal_failed_rejected)),
        "sentinel_rows": int(len(sentinel_rows)),
        "sentinel_false_positive_rows": int(len(sentinel_false_positive_rows)),
        "sentinel_false_positive_rate": float(sentinel_false_positive_rate),
        "normal_history_retention_pass": bool(normal_history_retention_pass),
        "source_role_counts": {
            role: int(sum(1 for row in source_output_rows if str(row.get("source_role", "")) == role))
            for role in sorted({str(row.get("source_role", "")) for row in source_output_rows})
        },
        "thresholds": {
            "min_action_l2_gap": min_action_l2_gap,
            "min_history_margin_gap": min_history_margin_gap,
            "max_source_rows": int(max_source_rows),
        },
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "base_result_class": base_result,
        "result_class": result_class,
        "sequence_outcome_positive": bool(result_class == "v3_reset_sequence_outcome_positive"),
        "summary_json": run_dir / "summary.json",
        "source_rows_csv": run_dir / "source_rows.csv",
        "intervention_rollouts_csv": run_dir / "intervention_rollouts.csv",
        "sequence_critical_rows_csv": run_dir / "sequence_critical_rows.csv",
        "sentinel_rows_csv": run_dir / "sentinel_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "horizon_summary_csv": run_dir / "horizon_summary.csv",
        "fault_family_summary_csv": run_dir / "fault_family_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v3 reset-source sequence interventions.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--reset-rows", type=Path, required=True)
    parser.add_argument("--rejected-rows", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=73000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--max-source-rows", type=int, default=512)
    parser.add_argument("--horizons", type=_parse_int_list, default=(2, 4, 6, 8))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="v3_reset_source_sequence_intervention")
    summary = run_v3_reset_source_sequence_intervention(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        reset_rows_path=args.reset_rows,
        rejected_rows_path=args.rejected_rows,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        max_source_rows=args.max_source_rows,
        horizons=tuple(args.horizons),
        device=args.device,
        run_dir=run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
