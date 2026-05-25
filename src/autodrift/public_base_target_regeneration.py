"""No-training M399-rooted target regeneration for low-tail sequence states."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import math
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_sequence_objective_probe import _load_probe_samples, _metadata_missing, _read_csv_rows


LOW_TAIL_GAP_THRESHOLD = 0.021141
LOW_TAIL_DEFICIT_THRESHOLD = 0.02
MAX_ROWS = 256
PER_FAULT_PAIR_CAP = 24
PER_SEED_CAP = 4


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def _key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("contrast_group_id", "")),
        str(row.get("source_index", "")),
        str(row.get("variant", "")),
        str(row.get("horizon", "")),
    )


def action_delta_set() -> list[tuple[str, np.ndarray]]:
    deltas: list[tuple[str, np.ndarray]] = []
    for value in (-0.08, -0.04, 0.04, 0.08):
        deltas.append((f"steer_{value:+.2f}", np.asarray([value, 0.0, 0.0], dtype=np.float32)))
    for value in (0.04, 0.08):
        deltas.append((f"brake_{value:+.2f}", np.asarray([0.0, 0.0, value], dtype=np.float32)))
    for value in (-0.08, -0.04, 0.04):
        deltas.append((f"throttle_{value:+.2f}", np.asarray([0.0, value, 0.0], dtype=np.float32)))
    for steer, brake in ((-0.04, 0.04), (0.04, 0.04), (-0.08, 0.08), (0.08, 0.08)):
        deltas.append((f"steer_{steer:+.2f}_brake_{brake:+.2f}", np.asarray([steer, 0.0, brake], dtype=np.float32)))
    return deltas


def select_source_rows(
    low_tail_rows: list[dict[str, str]],
    *,
    max_rows: int = MAX_ROWS,
    per_fault_pair_cap: int = PER_FAULT_PAIR_CAP,
    per_seed_cap: int = PER_SEED_CAP,
) -> list[dict[str, str]]:
    ordered = sorted(
        low_tail_rows,
        key=lambda row: (
            -_as_float(row.get("gap_deficit")),
            _as_float(row.get("normal_intervention_gap")),
            str(row.get("fault_family_pair", "")),
            str(row.get("seed", "")),
        ),
    )
    pair_counts: Counter[str] = Counter()
    seed_counts: Counter[str] = Counter()
    selected: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in ordered:
        key = _key(row)
        if key in seen:
            continue
        pair = str(row.get("fault_family_pair", ""))
        seed = str(row.get("seed", ""))
        if pair_counts[pair] >= int(per_fault_pair_cap):
            continue
        if seed_counts[seed] >= int(per_seed_cap):
            continue
        selected.append(row)
        seen.add(key)
        pair_counts[pair] += 1
        seed_counts[seed] += 1
        if len(selected) >= int(max_rows):
            break
    return selected


def _candidate_metrics(
    *,
    base_action: np.ndarray,
    intervention_action: np.ndarray,
    target_gap: float,
    delta_name: str,
    delta: np.ndarray,
) -> dict[str, Any]:
    target_action = np.clip(base_action + delta, -1.0, 1.0).astype(np.float32)
    gap_before = float(np.linalg.norm(base_action - intervention_action))
    gap_after = float(np.linalg.norm(target_action - intervention_action))
    deficit_before = max(float(target_gap) - gap_before, 0.0)
    deficit_after = max(float(target_gap) - gap_after, 0.0)
    low_tail_after = bool(gap_after < LOW_TAIL_GAP_THRESHOLD or deficit_after > LOW_TAIL_DEFICIT_THRESHOLD)
    action_l2 = float(np.linalg.norm(target_action - base_action))
    primary_accept = (
        action_l2 <= 0.0800001
        and deficit_after <= deficit_before - 0.004
        and gap_after >= gap_before + 0.004
        and not low_tail_after
    )
    return {
        "delta_name": delta_name,
        "base_steer": float(base_action[0]),
        "base_throttle": float(base_action[1]),
        "base_brake": float(base_action[2]),
        "target_steer": float(target_action[0]),
        "target_throttle": float(target_action[1]),
        "target_brake": float(target_action[2]),
        "action_l2_from_base": action_l2,
        "gap_before": gap_before,
        "gap_after": gap_after,
        "gap_delta": gap_after - gap_before,
        "gap_deficit_before": deficit_before,
        "gap_deficit_after": deficit_after,
        "gap_deficit_delta": deficit_after - deficit_before,
        "low_tail_after": low_tail_after,
        "acceptance_class": "primary" if primary_accept else "",
        "accepted": bool(primary_accept),
        "rollout_available": False,
    }


def _select_best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in rows if bool(row.get("accepted", False))]
    if not accepted:
        return None
    return sorted(
        accepted,
        key=lambda row: (
            _as_float(row.get("action_l2_from_base")),
            _as_float(row.get("gap_deficit_after")),
            -_as_float(row.get("gap_delta")),
        ),
    )[0]


def _group_summary(accepted_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted_rows:
        groups[str(row.get("fault_family_pair", ""))].append(row)
    out: list[dict[str, Any]] = []
    total = max(len(accepted_rows), 1)
    for pair, rows in groups.items():
        out.append(
            {
                "fault_family_pair": pair,
                "accepted_targets": len(rows),
                "accepted_fraction": float(len(rows) / total),
                "distinct_seeds": len({str(row.get("seed", "")) for row in rows}),
                "horizon_values": ",".join(sorted({str(row.get("horizon", "")) for row in rows})),
                "action_l2_mean": float(np.mean([_as_float(row.get("action_l2_from_base")) for row in rows])),
                "gap_delta_mean": float(np.mean([_as_float(row.get("gap_delta")) for row in rows])),
                "deficit_delta_mean": float(np.mean([_as_float(row.get("gap_deficit_delta")) for row in rows])),
            }
        )
    return sorted(out, key=lambda row: (-int(row["accepted_targets"]), str(row["fault_family_pair"])))


def classify_target_regeneration(
    *,
    actor_parameters_changed: bool,
    accepted_targets: int,
    distinct_fault_family_pairs: int,
    distinct_seeds: int,
    max_fault_family_pair_fraction: float,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_parameters_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "public_base_target_regeneration_contract_artifact"
    if int(accepted_targets) < 80:
        return "public_base_target_regeneration_too_few_targets"
    if int(distinct_fault_family_pairs) < 8 or int(distinct_seeds) < 24:
        return "public_base_target_regeneration_diversity_failure"
    if float(max_fault_family_pair_fraction) > 0.25:
        return "public_base_target_regeneration_source_concentrated"
    return "public_base_target_regeneration_pass"


def run_public_base_target_regeneration(
    *,
    checkpoint_path: Path,
    scenario_config_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    low_tail_rows_path: Path,
    group_deficit_summary_path: Path,
    run_dir: Path,
    device: str,
    max_rows: int = MAX_ROWS,
    per_fault_pair_cap: int = PER_FAULT_PAIR_CAP,
    per_seed_cap: int = PER_SEED_CAP,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    checksum_before = model_parameter_checksum(model)
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    selected_rows = select_source_rows(
        low_tail_rows,
        max_rows=max_rows,
        per_fault_pair_cap=per_fault_pair_cap,
        per_seed_cap=per_seed_cap,
    )
    selected_keys = {_key(row) for row in selected_rows}
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    samples, meta_rows, rejected_reconstruction = _load_probe_samples(
        model=model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    normal_actions = samples["normal_actions"].detach().cpu().numpy()
    intervention_actions = samples["intervention_actions"].detach().cpu().numpy()
    target_gaps = samples["target_gaps"].detach().cpu().numpy()
    selected_source_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_target_rows: list[dict[str, Any]] = []
    deltas = action_delta_set()
    matched_keys: set[tuple[str, str, str, str]] = set()
    for index, meta in enumerate(meta_rows):
        key = _key(meta)
        if key not in selected_keys:
            continue
        matched_keys.add(key)
        selected_source_rows.append({**meta})
        per_candidate: list[dict[str, Any]] = []
        for delta_name, delta in deltas:
            metrics = _candidate_metrics(
                base_action=normal_actions[index],
                intervention_action=intervention_actions[index],
                target_gap=float(target_gaps[index]),
                delta_name=delta_name,
                delta=delta,
            )
            row = {**meta, **metrics}
            candidate_rows.append(row)
            per_candidate.append(row)
        best = _select_best_candidate(per_candidate)
        if best is not None:
            accepted_rows.append(best)
        else:
            base_gap = float(np.linalg.norm(normal_actions[index] - intervention_actions[index]))
            rejected_target_rows.append(
                {
                    **meta,
                    "rejection_reason": "no_candidate_passed_acceptance",
                    "gap_before": base_gap,
                    "target_gap": float(target_gaps[index]),
                    "gap_deficit_before": max(float(target_gaps[index]) - base_gap, 0.0),
                }
            )
    missing_selected = selected_keys - matched_keys
    for key in sorted(missing_selected):
        rejected_target_rows.append({"rejection_reason": "selected_source_not_reconstructed", "key": str(key)})
    group_rows = _group_summary(accepted_rows)
    pair_counts = Counter(str(row.get("fault_family_pair", "")) for row in accepted_rows)
    accepted_count = len(accepted_rows)
    max_pair_fraction = float(max(pair_counts.values()) / accepted_count) if accepted_count else 0.0
    distinct_pairs = len({str(row.get("fault_family_pair", "")) for row in accepted_rows if str(row.get("fault_family_pair", ""))})
    distinct_seeds = len({str(row.get("seed", "")) for row in accepted_rows if str(row.get("seed", ""))})
    horizon_values = sorted({str(row.get("horizon", "")) for row in accepted_rows if str(row.get("horizon", ""))})
    checksum_after = model_parameter_checksum(model)
    result_class = classify_target_regeneration(
        actor_parameters_changed=bool(checksum_before != checksum_after),
        accepted_targets=accepted_count,
        distinct_fault_family_pairs=distinct_pairs,
        distinct_seeds=distinct_seeds,
        max_fault_family_pair_fraction=max_pair_fraction,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    summary = {
        "run_type": "public_base_target_regeneration",
        "checkpoint": checkpoint_path,
        "scenario_config": scenario_config_path,
        "positive_rows": positive_rows_path,
        "contrast_rows": contrast_rows_path,
        "low_tail_rows": low_tail_rows_path,
        "group_deficit_summary": group_deficit_summary_path,
        "max_rows": int(max_rows),
        "per_fault_pair_cap": int(per_fault_pair_cap),
        "per_seed_cap": int(per_seed_cap),
        "low_tail_rows_input_count": int(len(low_tail_rows)),
        "selected_sources": int(len(selected_rows)),
        "selected_sources_reconstructed": int(len(matched_keys)),
        "selected_sources_missing": int(len(missing_selected)),
        "candidate_actions": int(len(candidate_rows)),
        "accepted_targets": accepted_count,
        "rejected_targets": int(len(rejected_target_rows)),
        "distinct_fault_family_pairs": distinct_pairs,
        "distinct_seeds": distinct_seeds,
        "accepted_horizon_values": horizon_values,
        "max_fault_family_pair_fraction": max_pair_fraction,
        "metadata_missing_rows": int(metadata_missing_rows),
        "reconstruction_rejections": int(len(rejected_reconstruction)),
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "actor_checksum_before": checksum_before,
        "actor_checksum_after": checksum_after,
        "training_started": False,
        "target_generation_started": True,
        "m880_exact_used": False,
        "replay_used": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "selected_source_rows_csv": run_dir / "selected_source_rows.csv",
        "candidate_action_rows_csv": run_dir / "candidate_action_rows.csv",
        "accepted_target_rows_csv": run_dir / "accepted_target_rows.csv",
        "rejected_target_rows_csv": run_dir / "rejected_target_rows.csv",
        "group_acceptance_summary_csv": run_dir / "group_acceptance_summary.csv",
    }
    write_csv_rows(run_dir / "selected_source_rows.csv", selected_source_rows)
    write_csv_rows(run_dir / "candidate_action_rows.csv", candidate_rows)
    write_csv_rows(run_dir / "accepted_target_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "rejected_target_rows.csv", rejected_target_rows)
    write_csv_rows(run_dir / "group_acceptance_summary.csv", group_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training public-base target regeneration.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--group-deficit-summary", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--max-rows", type=int, default=MAX_ROWS)
    parser.add_argument("--per-fault-family-pair-cap", type=int, default=PER_FAULT_PAIR_CAP)
    parser.add_argument("--per-seed-cap", type=int, default=PER_SEED_CAP)
    args = parser.parse_args()
    summary = run_public_base_target_regeneration(
        checkpoint_path=args.checkpoint,
        scenario_config_path=args.scenario_config,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        low_tail_rows_path=args.low_tail_rows,
        group_deficit_summary_path=args.group_deficit_summary,
        run_dir=args.run_dir,
        device=args.device,
        max_rows=args.max_rows,
        per_fault_pair_cap=args.per_fault_family_pair_cap,
        per_seed_cap=args.per_seed_cap,
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
