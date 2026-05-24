"""No-training source-balanced temporal command-response wave."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    NOMINAL_FAULT,
    FaultSpec,
    _feature_distance,
    find_cross_fault_match,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import _source_role
from autodrift.temporal_action_response_mismatch import (
    TemporalSnapshot,
    _group_summary,
    _load_low_alpha_fault_pairs,
    _row_for_variant,
    build_temporal_variant_hiddens,
    collect_temporal_snapshots,
    replay_temporal_variant,
)
from autodrift.train_ppo import resolve_device
from autodrift.trajectory_terminal_boundary_source_miner import assigned_split


TEMPORAL_WAVE_VARIANTS = (
    "normal",
    "reset_hidden",
    "cross_fault_wrong_hidden",
    "delayed_hidden_5",
    "delayed_hidden_10",
    "delayed_hidden_20",
    "pre_fault_stale_hidden",
    "mismatch_zero_command_history",
    "mismatch_command_shift_1",
    "mismatch_response_delay_5",
    "mismatch_response_delay_10",
)


@dataclass
class PairProposal:
    proposal_id: int
    snapshot: TemporalSnapshot
    wrong_snapshot: TemporalSnapshot
    match_distance: float
    pairing_rule: str
    source_pool: str

    def metadata(self) -> dict[str, Any]:
        preferred = self.snapshot
        wrong = self.wrong_snapshot
        step_bucket = int(preferred.step // 20)
        obstacle_distance = _finite_float(preferred.obstacle_distance)
        obstacle_bucket = int(obstacle_distance // 10) if np.isfinite(obstacle_distance) else -1
        return {
            "proposal_id": int(self.proposal_id),
            "seed": int(preferred.seed),
            "step": int(preferred.step),
            "preferred_snapshot_id": int(preferred.snapshot_id),
            "wrong_snapshot_id": int(wrong.snapshot_id),
            "preferred_fault": preferred.fault.name,
            "preferred_fault_family": preferred.fault.family,
            "preferred_fault_severity": preferred.fault.severity,
            "wrong_fault": wrong.fault.name,
            "wrong_fault_family": wrong.fault.family,
            "wrong_fault_severity": wrong.fault.severity,
            "fault_family_pair": f"{preferred.fault.family}->{wrong.fault.family}",
            "severity_pair": f"{preferred.fault.severity}->{wrong.fault.severity}",
            "pairing_rule": self.pairing_rule,
            "feature_distance": float(_feature_distance(preferred, wrong)),
            "match_distance": float(self.match_distance),
            "obstacle_distance": obstacle_distance,
            "obstacle_lateral_offset": _finite_float(preferred.obstacle_lateral_offset),
            "source_pool": self.source_pool,
            "assigned_split": assigned_split(int(preferred.seed), heldout_fraction=0.2),
            "step_bucket": int(step_bucket),
            "obstacle_distance_bucket": int(obstacle_bucket),
        }


def _dominance_fraction(values: list[Any]) -> float:
    if not values:
        return 0.0
    counts: dict[str, int] = {}
    for value in values:
        text = str(value)
        counts[text] = counts.get(text, 0) + 1
    return float(max(counts.values()) / max(len(values), 1))


def classify_source_balanced_temporal_wave(
    *,
    proposal_count: int,
    selected_pair_count: int,
    temporal_action_critical_rows: int,
    temporal_outcome_critical_rows: int,
    unique_selected_seeds: int,
    unique_preferred_fault_families: int,
    unique_fault_family_pairs: int,
    max_seed_dominance: float,
    max_preferred_family_dominance: float,
    sentinel_false_positive_rate: float,
    normal_history_retention_pass: bool,
    actor_parameters_changed: bool,
    min_selected_pairs: int = 3000,
    min_unique_selected_seeds: int = 128,
    min_unique_preferred_fault_families: int = 8,
    min_unique_fault_family_pairs: int = 24,
    max_allowed_seed_dominance: float = 0.02,
    max_allowed_family_dominance: float = 0.25,
    max_sentinel_false_positive_rate: float = 0.05,
    min_temporal_action_rows: int = 300,
    min_temporal_outcome_rows: int = 20,
) -> str:
    if int(proposal_count) <= 0 or bool(actor_parameters_changed):
        return "temporal_wave_artifact"
    if float(sentinel_false_positive_rate) > float(max_sentinel_false_positive_rate):
        return "temporal_wave_artifact"
    source_balanced = (
        int(selected_pair_count) >= int(min_selected_pairs)
        and int(unique_selected_seeds) >= int(min_unique_selected_seeds)
        and int(unique_preferred_fault_families) >= int(min_unique_preferred_fault_families)
        and int(unique_fault_family_pairs) >= int(min_unique_fault_family_pairs)
        and float(max_seed_dominance) <= float(max_allowed_seed_dominance)
        and float(max_preferred_family_dominance) <= float(max_allowed_family_dominance)
        and bool(normal_history_retention_pass)
    )
    if not source_balanced:
        return "source_balance_blocked"
    if int(temporal_outcome_critical_rows) >= int(min_temporal_outcome_rows):
        return "source_balanced_temporal_outcome_positive"
    if int(temporal_action_critical_rows) >= int(min_temporal_action_rows):
        return "source_balanced_temporal_action_only"
    return "source_balanced_temporal_sparse"


def _source_pool_for_pair(fault_family_pair: str, low_alpha_pairs: set[str]) -> str:
    return "m713_low_alpha_family" if fault_family_pair in low_alpha_pairs else "source_balanced_general"


def collect_pair_proposals(
    *,
    snapshots: list[TemporalSnapshot],
    pairing_rules: tuple[dict[str, Any], ...],
    low_alpha_pairs: set[str],
) -> list[PairProposal]:
    snapshots_by_seed: dict[int, list[TemporalSnapshot]] = {}
    for snapshot in snapshots:
        snapshots_by_seed.setdefault(int(snapshot.seed), []).append(snapshot)
    proposals: list[PairProposal] = []
    for seed, seed_snapshots in sorted(snapshots_by_seed.items()):
        fault_snapshots = [snapshot for snapshot in seed_snapshots if snapshot.fault.name != "nominal"]
        for snapshot in fault_snapshots:
            matched, match_distance, pairing_rule = find_cross_fault_match(snapshot, seed_snapshots, pairing_rules)
            if matched is None:
                continue
            pair_text = f"{snapshot.fault.family}->{matched.fault.family}"
            proposals.append(
                PairProposal(
                    proposal_id=len(proposals),
                    snapshot=snapshot,
                    wrong_snapshot=matched,
                    match_distance=float(match_distance),
                    pairing_rule=str(pairing_rule),
                    source_pool=_source_pool_for_pair(pair_text, low_alpha_pairs),
                )
            )
    return proposals


def select_balanced_proposals(
    proposals: list[PairProposal],
    *,
    selected_pair_count: int,
    per_seed_pair_cap: int,
    per_fault_family_pair_cap: int,
    per_preferred_family_cap: int,
    per_step_bucket_cap: int,
) -> list[PairProposal]:
    groups: dict[tuple[Any, ...], list[PairProposal]] = {}
    for proposal in proposals:
        meta = proposal.metadata()
        key = (
            meta["seed"],
            meta["preferred_fault_family"],
            meta["wrong_fault_family"],
            meta["preferred_fault_severity"],
            meta["wrong_fault_severity"],
            meta["step_bucket"],
            meta["source_pool"],
            meta["assigned_split"],
        )
        groups.setdefault(key, []).append(proposal)
    for rows in groups.values():
        rows.sort(key=lambda item: (item.match_distance, -_feature_distance(item.snapshot, item.wrong_snapshot), item.proposal_id))

    seed_counts: dict[int, int] = {}
    pair_counts: dict[str, int] = {}
    preferred_counts: dict[str, int] = {}
    step_counts: dict[int, int] = {}
    selected: list[PairProposal] = []
    keys = sorted(groups)
    offsets = {key: 0 for key in keys}
    while len(selected) < int(selected_pair_count):
        progressed = False
        for key in keys:
            rows = groups[key]
            offset = offsets[key]
            while offset < len(rows):
                proposal = rows[offset]
                offset += 1
                meta = proposal.metadata()
                seed = int(meta["seed"])
                pair = str(meta["fault_family_pair"])
                preferred_family = str(meta["preferred_fault_family"])
                step_bucket = int(meta["step_bucket"])
                if seed_counts.get(seed, 0) >= int(per_seed_pair_cap):
                    continue
                if pair_counts.get(pair, 0) >= int(per_fault_family_pair_cap):
                    continue
                if preferred_counts.get(preferred_family, 0) >= int(per_preferred_family_cap):
                    continue
                if step_counts.get(step_bucket, 0) >= int(per_step_bucket_cap):
                    continue
                selected.append(proposal)
                seed_counts[seed] = seed_counts.get(seed, 0) + 1
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
                preferred_counts[preferred_family] = preferred_counts.get(preferred_family, 0) + 1
                step_counts[step_bucket] = step_counts.get(step_bucket, 0) + 1
                progressed = True
                break
            offsets[key] = offset
            if len(selected) >= int(selected_pair_count):
                break
        if not progressed:
            break
    return selected


def _quota_summary(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return [{"quota_key": key, "quota_value": value, "rows": count} for value, count in sorted(counts.items())]


def _sentinel_candidate(row: dict[str, Any], min_action_l2_gap: float) -> bool:
    return _source_role(row, min_action_l2_gap) == "sentinel"


def run_source_balanced_temporal_wave(
    *,
    checkpoint_path: Path,
    config_path: Path,
    seed_start: int,
    seed_count: int,
    selected_pair_count: int,
    per_seed_pair_cap: int,
    device: str,
    run_dir: Path,
    per_fault_family_pair_cap: int = 256,
    per_preferred_family_cap: int = 640,
    per_step_bucket_cap: int = 1024,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    pairing_rules = tuple(config.get("pairing_rules", ()))
    if not pairing_rules:
        raise ValueError("source-balanced temporal wave requires config pairing_rules")
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("source-balanced temporal wave requires an online recurrent checkpoint")
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)

    max_steps = int(config.get("max_steps", 280))
    min_step = int(config.get("min_step", 30))
    snapshot_stride = int(config.get("snapshot_stride", 4))
    max_snapshots_per_scenario = int(config.get("max_snapshots_per_scenario", 5))
    obstacle_longitudinal_min = float(config.get("obstacle_longitudinal_min", -10.0))
    obstacle_longitudinal_max = float(config.get("obstacle_longitudinal_max", 95.0))
    max_continuation_steps = int(config.get("max_continuation_steps", 50))
    min_action_l2_gap = float(config.get("min_action_l2_gap", 0.015))
    min_history_margin_gap = float(config.get("min_history_margin_gap", 0.02))
    history_window_steps = int(config.get("temporal_history_window_steps", 30))
    low_alpha_pairs = _load_low_alpha_fault_pairs(Path("runs/m713_actor_head_history_signal_coupling/row_actor_head_coupling.csv"))

    faults: list[FaultSpec] = [NOMINAL_FAULT, *config["faults"]]
    snapshots: list[TemporalSnapshot] = []
    scenario_rows: list[dict[str, Any]] = []
    for seed in range(int(seed_start), int(seed_start) + int(seed_count)):
        for fault in faults:
            scenario_snapshots, scenario_row = collect_temporal_snapshots(
                model=model,
                env_config=env_config,
                fault=fault,
                seed=int(seed),
                start_snapshot_id=len(snapshots),
                min_step=min_step,
                max_steps=max_steps,
                snapshot_stride=snapshot_stride,
                max_snapshots_per_scenario=max_snapshots_per_scenario,
                obstacle_longitudinal_min=obstacle_longitudinal_min,
                obstacle_longitudinal_max=obstacle_longitudinal_max,
                history_window_steps=history_window_steps,
                device=resolved_device,
            )
            snapshots.extend(scenario_snapshots)
            scenario_rows.append(scenario_row)

    proposals = collect_pair_proposals(snapshots=snapshots, pairing_rules=pairing_rules, low_alpha_pairs=low_alpha_pairs)
    selected = select_balanced_proposals(
        proposals,
        selected_pair_count=selected_pair_count,
        per_seed_pair_cap=per_seed_pair_cap,
        per_fault_family_pair_cap=per_fault_family_pair_cap,
        per_preferred_family_cap=per_preferred_family_cap,
        per_step_bucket_cap=per_step_bucket_cap,
    )
    proposal_rows = [proposal.metadata() for proposal in proposals]
    selected_rows = [proposal.metadata() for proposal in selected]

    source_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    temporal_critical_rows: list[dict[str, Any]] = []
    sentinel_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for selected_index, proposal in enumerate(selected):
        meta = proposal.metadata()
        meta["selected_index"] = int(selected_index)
        variant_hiddens = build_temporal_variant_hiddens(
            model=model,
            snapshot=proposal.snapshot,
            wrong_snapshot=proposal.wrong_snapshot,
            response_dim=response_dim,
            device=resolved_device,
        )
        normal, normal_actions = replay_temporal_variant(
            model=model,
            snapshot=proposal.snapshot,
            env_config=env_config,
            variant="normal",
            variant_hidden=variant_hiddens["normal"],
            normal_first_action=None,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        normal_first_action = np.asarray(
            [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
            dtype=np.float32,
        )
        source_row = dict(meta)
        source_row.update(
            {
                "available_variant_count": int(len(variant_hiddens)),
                "available_variants": "|".join(sorted(variant_hiddens)),
                "normal_margin": _finite_float(normal.get("min_clearance_margin")),
                "normal_success": bool(normal.get("success", False)),
            }
        )
        source_rows.append(source_row)
        for variant in TEMPORAL_WAVE_VARIANTS:
            variant_hidden = variant_hiddens.get(variant)
            if variant_hidden is None:
                continue
            if variant == "normal":
                result = normal
            else:
                result, _ = replay_temporal_variant(
                    model=model,
                    snapshot=proposal.snapshot,
                    env_config=env_config,
                    variant=variant,
                    variant_hidden=variant_hidden,
                    normal_first_action=normal_first_action,
                    normal_actions=normal_actions,
                    max_continuation_steps=max_continuation_steps,
                    device=resolved_device,
                )
            row = _row_for_variant(
                pair_meta=meta,
                source_pool=str(meta.get("source_pool", "")),
                variant=variant,
                result=result,
                normal=normal,
                action_threshold=min_action_l2_gap,
                margin_threshold=min_history_margin_gap,
            )
            rollout_rows.append(row)
            if bool(row.get("temporal_action_critical", False)) or bool(row.get("temporal_outcome_critical", False)):
                temporal_critical_rows.append(row)
            if _sentinel_candidate(row, min_action_l2_gap):
                sentinel_rows.append(row)
        normal_margin = _finite_float(normal.get("min_clearance_margin"))
        if not (bool(normal.get("success", False)) or (np.isfinite(normal_margin) and normal_margin >= 0.0)):
            rejected_rows.append({**meta, "rejection_reason": "normal_history_failed"})

    temporal_action_rows = [row for row in rollout_rows if bool(row.get("temporal_action_critical", False))]
    temporal_outcome_rows = [row for row in rollout_rows if bool(row.get("temporal_outcome_critical", False))]
    sentinel_false_positive_rows = [
        row
        for row in sentinel_rows
        if bool(row.get("temporal_action_critical", False)) and bool(row.get("temporal_outcome_critical", False))
    ]
    normal_rows = [row for row in rollout_rows if row.get("variant") == "normal"]
    normal_history_retention_pass = bool(
        normal_rows and not any(str(row.get("terminal_reason", "")) == "artifact" for row in normal_rows)
    )
    selected_seeds = [int(row["seed"]) for row in selected_rows]
    selected_families = [str(row["preferred_fault_family"]) for row in selected_rows]
    selected_pairs = [str(row["fault_family_pair"]) for row in selected_rows]
    temporal_action_seeds = [int(row["seed"]) for row in temporal_action_rows]
    temporal_outcome_seeds = [int(row["seed"]) for row in temporal_outcome_rows]
    checksum_after = model_parameter_checksum(model)

    sentinel_false_positive_rate = float(len(sentinel_false_positive_rows) / max(len(sentinel_rows), 1))
    result_class = classify_source_balanced_temporal_wave(
        proposal_count=len(proposals),
        selected_pair_count=len(selected),
        temporal_action_critical_rows=len(temporal_action_rows),
        temporal_outcome_critical_rows=len(temporal_outcome_rows),
        unique_selected_seeds=len(set(selected_seeds)),
        unique_preferred_fault_families=len(set(selected_families)),
        unique_fault_family_pairs=len(set(selected_pairs)),
        max_seed_dominance=_dominance_fraction(selected_seeds),
        max_preferred_family_dominance=_dominance_fraction(selected_families),
        sentinel_false_positive_rate=sentinel_false_positive_rate,
        normal_history_retention_pass=normal_history_retention_pass,
        actor_parameters_changed=bool(checksum_before != checksum_after),
    )

    quota_rows = []
    for key in ("seed", "preferred_fault_family", "fault_family_pair", "step_bucket", "assigned_split", "source_pool"):
        quota_rows.extend(_quota_summary(selected_rows, key))
    write_csv_rows(run_dir / "scenario_summary.csv", scenario_rows)
    write_csv_rows(run_dir / "pair_proposals.csv", proposal_rows)
    write_csv_rows(run_dir / "selected_pair_proposals.csv", selected_rows)
    write_csv_rows(run_dir / "source_rows.csv", source_rows)
    write_csv_rows(run_dir / "intervention_rollouts.csv", rollout_rows)
    write_csv_rows(run_dir / "temporal_critical_rows.csv", temporal_critical_rows)
    write_csv_rows(run_dir / "sentinel_rows.csv", sentinel_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "quota_summary.csv", quota_rows)
    write_csv_rows(run_dir / "seed_summary.csv", _group_summary(rollout_rows, ("seed", "variant")))
    write_csv_rows(run_dir / "fault_family_summary.csv", _group_summary(rollout_rows, ("fault_family_pair", "variant")))
    write_csv_rows(run_dir / "variant_summary.csv", _group_summary(rollout_rows, ("variant",)))

    summary = {
        "run_type": "source_balanced_temporal_wave",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "env_config": config.get("env_config"),
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "fault_count": int(len(faults) - 1),
        "scenario_count": int(len(scenario_rows)),
        "snapshot_count": int(len(snapshots)),
        "proposal_count": int(len(proposals)),
        "selected_pair_count": int(len(selected)),
        "row_count": int(len(rollout_rows)),
        "temporal_action_critical_rows": int(len(temporal_action_rows)),
        "temporal_outcome_critical_rows": int(len(temporal_outcome_rows)),
        "sentinel_rows": int(len(sentinel_rows)),
        "sentinel_false_positive_rows": int(len(sentinel_false_positive_rows)),
        "sentinel_false_positive_rate": sentinel_false_positive_rate,
        "unique_selected_seeds": int(len(set(selected_seeds))),
        "unique_temporal_action_seeds": int(len(set(temporal_action_seeds))),
        "unique_temporal_outcome_seeds": int(len(set(temporal_outcome_seeds))),
        "unique_preferred_fault_families": int(len(set(selected_families))),
        "unique_fault_family_pairs": int(len(set(selected_pairs))),
        "max_seed_dominance": _dominance_fraction(selected_seeds),
        "max_preferred_family_dominance": _dominance_fraction(selected_families),
        "max_temporal_action_seed_dominance": _dominance_fraction(temporal_action_seeds),
        "normal_history_retention_pass": bool(normal_history_retention_pass),
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "thresholds": {
            "selected_pair_count": int(selected_pair_count),
            "per_seed_pair_cap": int(per_seed_pair_cap),
            "per_fault_family_pair_cap": int(per_fault_family_pair_cap),
            "per_preferred_family_cap": int(per_preferred_family_cap),
            "per_step_bucket_cap": int(per_step_bucket_cap),
            "min_action_l2_gap": float(min_action_l2_gap),
            "min_history_margin_gap": float(min_history_margin_gap),
        },
        "summary_json": run_dir / "summary.json",
        "pair_proposals_csv": run_dir / "pair_proposals.csv",
        "selected_pair_proposals_csv": run_dir / "selected_pair_proposals.csv",
        "source_rows_csv": run_dir / "source_rows.csv",
        "intervention_rollouts_csv": run_dir / "intervention_rollouts.csv",
        "temporal_critical_rows_csv": run_dir / "temporal_critical_rows.csv",
        "sentinel_rows_csv": run_dir / "sentinel_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a no-training source-balanced temporal wave.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=72000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--selected-pair-count", type=int, default=4096)
    parser.add_argument("--per-seed-pair-cap", type=int, default=8)
    parser.add_argument("--per-fault-family-pair-cap", type=int, default=256)
    parser.add_argument("--per-preferred-family-cap", type=int, default=640)
    parser.add_argument("--per-step-bucket-cap", type=int, default=1024)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="source_balanced_temporal_wave")
    summary = run_source_balanced_temporal_wave(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        selected_pair_count=args.selected_pair_count,
        per_seed_pair_cap=args.per_seed_pair_cap,
        per_fault_family_pair_cap=args.per_fault_family_pair_cap,
        per_preferred_family_cap=args.per_preferred_family_cap,
        per_step_bucket_cap=args.per_step_bucket_cap,
        device=args.device,
        run_dir=run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
