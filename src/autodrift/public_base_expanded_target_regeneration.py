"""No-training expanded-source target regeneration for the M399 public base."""

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
from autodrift.public_base_target_regeneration import (
    LOW_TAIL_DEFICIT_THRESHOLD,
    LOW_TAIL_GAP_THRESHOLD,
    _as_float,
    _key,
    action_delta_set,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_sequence_objective_probe import _load_probe_samples, _metadata_missing, _read_csv_rows


NEAR_BASE_ALPHA = 0.02
NEAR_TAIL_DEFICIT_THRESHOLD = 0.012
NEAR_TAIL_GAP_THRESHOLD = 0.030
MAX_ROWS = 256
PER_FAULT_PAIR_CAP = 24
PER_SEED_SOFT_CAP = 8
MIN_STRICT_LOW_TAIL_ROWS = 60


def near_base_objective_rows(rows: list[dict[str, str]], *, near_base_alpha: float = NEAR_BASE_ALPHA) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if math.isclose(_as_float(row.get("alpha")), float(near_base_alpha), rel_tol=0.0, abs_tol=1e-9)
    ]


def build_expanded_source_candidates(
    *,
    objective_rows: list[dict[str, str]],
    low_tail_rows: list[dict[str, str]],
    near_base_alpha: float = NEAR_BASE_ALPHA,
    near_tail_deficit_threshold: float = NEAR_TAIL_DEFICIT_THRESHOLD,
    near_tail_gap_threshold: float = NEAR_TAIL_GAP_THRESHOLD,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    low_tail_keys = {_key(row) for row in low_tail_rows}
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in near_base_objective_rows(objective_rows, near_base_alpha=near_base_alpha):
        key = _key(row)
        if key in seen:
            continue
        seen.add(key)
        gap = _as_float(row.get("normal_intervention_gap"))
        deficit = _as_float(row.get("gap_deficit"))
        strict_low_tail = key in low_tail_keys
        near_tail = deficit >= float(near_tail_deficit_threshold) or gap <= float(near_tail_gap_threshold)
        enriched = {
            **row,
            "strict_low_tail": strict_low_tail,
            "near_tail_candidate": near_tail,
            "source_label": "strict_low_tail" if strict_low_tail else "near_tail_coverage",
            "near_base_alpha": float(near_base_alpha),
        }
        if strict_low_tail or near_tail:
            candidates.append(enriched)
        else:
            rejected.append({**enriched, "source_rejection_reason": "not_strict_or_near_tail"})
    return candidates, rejected


def _source_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        not bool(row.get("strict_low_tail", False)),
        -_as_float(row.get("gap_deficit")),
        _as_float(row.get("normal_intervention_gap")),
        str(row.get("fault_family_pair", "")),
        str(row.get("seed", "")),
        str(row.get("contrast_group_id", "")),
    )


def select_expanded_source_rows(
    candidates: list[dict[str, Any]],
    *,
    max_rows: int = MAX_ROWS,
    per_fault_pair_cap: int = PER_FAULT_PAIR_CAP,
    per_seed_soft_cap: int = PER_SEED_SOFT_CAP,
    min_strict_low_tail_rows: int = MIN_STRICT_LOW_TAIL_ROWS,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    pair_counts: Counter[str] = Counter()
    seed_counts: Counter[str] = Counter()

    def add(row: dict[str, Any]) -> bool:
        if len(selected) >= int(max_rows):
            return False
        key = _key(row)
        if key in seen:
            return False
        pair = str(row.get("fault_family_pair", ""))
        seed = str(row.get("seed", ""))
        if pair_counts[pair] >= int(per_fault_pair_cap):
            return False
        if seed_counts[seed] >= int(per_seed_soft_cap):
            return False
        selected.append(row)
        seen.add(key)
        pair_counts[pair] += 1
        seed_counts[seed] += 1
        return True

    by_seed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_seed[str(row.get("seed", ""))].append(row)
    seed_representatives = [sorted(rows, key=_source_sort_key)[0] for rows in by_seed.values()]
    for row in sorted(seed_representatives, key=_source_sort_key):
        add(row)

    strict_rows = sorted([row for row in candidates if bool(row.get("strict_low_tail", False))], key=_source_sort_key)
    for row in strict_rows:
        if sum(1 for selected_row in selected if bool(selected_row.get("strict_low_tail", False))) >= int(
            min_strict_low_tail_rows
        ):
            break
        add(row)

    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_pair[str(row.get("fault_family_pair", ""))].append(row)
    pair_representatives = [sorted(rows, key=_source_sort_key)[0] for rows in by_pair.values()]
    for row in sorted(pair_representatives, key=_source_sort_key):
        add(row)

    for row in sorted(candidates, key=_source_sort_key):
        add(row)
        if len(selected) >= int(max_rows):
            break
    return selected


def _expanded_candidate_metrics(
    *,
    base_action: np.ndarray,
    intervention_action: np.ndarray,
    target_gap: float,
    delta_name: str,
    delta: np.ndarray,
    source_label: str,
) -> dict[str, Any]:
    target_action = np.clip(base_action + delta, -1.0, 1.0).astype(np.float32)
    gap_before = float(np.linalg.norm(base_action - intervention_action))
    gap_after = float(np.linalg.norm(target_action - intervention_action))
    deficit_before = max(float(target_gap) - gap_before, 0.0)
    deficit_after = max(float(target_gap) - gap_after, 0.0)
    low_tail_after = bool(gap_after < LOW_TAIL_GAP_THRESHOLD or deficit_after > LOW_TAIL_DEFICIT_THRESHOLD)
    action_l2 = float(np.linalg.norm(target_action - base_action))
    if source_label == "strict_low_tail":
        accepted = (
            action_l2 <= 0.0800001
            and deficit_after <= deficit_before - 0.004
            and gap_after >= gap_before + 0.004
            and not low_tail_after
        )
    else:
        accepted = (
            action_l2 <= 0.0800001
            and deficit_after <= deficit_before + 1e-9
            and gap_after >= gap_before + 0.004
            and not low_tail_after
        )
    return {
        "delta_name": delta_name,
        "source_label": source_label,
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
        "acceptance_class": "expanded_primary" if accepted else "",
        "accepted": bool(accepted),
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
    total = max(len(accepted_rows), 1)
    out: list[dict[str, Any]] = []
    for pair, rows in groups.items():
        out.append(
            {
                "fault_family_pair": pair,
                "accepted_targets": len(rows),
                "accepted_fraction": float(len(rows) / total),
                "strict_low_tail_accepted_targets": sum(
                    1 for row in rows if str(row.get("source_label", "")) == "strict_low_tail"
                ),
                "near_tail_accepted_targets": sum(
                    1 for row in rows if str(row.get("source_label", "")) == "near_tail_coverage"
                ),
                "distinct_seeds": len({str(row.get("seed", "")) for row in rows}),
                "horizon_values": ",".join(sorted({str(row.get("horizon", "")) for row in rows})),
                "action_l2_mean": float(np.mean([_as_float(row.get("action_l2_from_base")) for row in rows])),
                "gap_delta_mean": float(np.mean([_as_float(row.get("gap_delta")) for row in rows])),
                "deficit_delta_mean": float(np.mean([_as_float(row.get("gap_deficit_delta")) for row in rows])),
            }
        )
    return sorted(out, key=lambda row: (-int(row["accepted_targets"]), str(row["fault_family_pair"])))


def classify_expanded_target_regeneration(
    *,
    actor_parameters_changed: bool,
    accepted_targets: int,
    strict_low_tail_accepted_targets: int,
    distinct_fault_family_pairs: int,
    distinct_seeds: int,
    max_fault_family_pair_fraction: float,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_parameters_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "public_base_expanded_target_regeneration_contract_artifact"
    if int(accepted_targets) < 96:
        return "public_base_expanded_target_regeneration_too_few_targets"
    if int(strict_low_tail_accepted_targets) < 60:
        return "public_base_expanded_target_regeneration_strict_low_tail_sparse"
    if int(distinct_fault_family_pairs) < 10 or int(distinct_seeds) < 24:
        return "public_base_expanded_target_regeneration_diversity_failure"
    if float(max_fault_family_pair_fraction) > 0.25:
        return "public_base_expanded_target_regeneration_source_concentrated"
    return "public_base_expanded_target_regeneration_pass"


def run_public_base_expanded_target_regeneration(
    *,
    checkpoint_path: Path,
    scenario_config_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    objective_rows_path: Path,
    low_tail_rows_path: Path,
    run_dir: Path,
    device: str,
    max_rows: int = MAX_ROWS,
    per_fault_pair_cap: int = PER_FAULT_PAIR_CAP,
    per_seed_soft_cap: int = PER_SEED_SOFT_CAP,
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
    objective_rows = _read_csv_rows(objective_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    source_candidates, rejected_source_candidates = build_expanded_source_candidates(
        objective_rows=objective_rows,
        low_tail_rows=low_tail_rows,
    )
    selected_rows = select_expanded_source_rows(
        source_candidates,
        max_rows=max_rows,
        per_fault_pair_cap=per_fault_pair_cap,
        per_seed_soft_cap=per_seed_soft_cap,
    )
    selected_by_key = {_key(row): row for row in selected_rows}
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
        selected_source = selected_by_key.get(key)
        if selected_source is None:
            continue
        matched_keys.add(key)
        source_label = str(selected_source.get("source_label", "near_tail_coverage"))
        selected_source_rows.append({**meta, **{k: v for k, v in selected_source.items() if k not in meta}})
        per_candidate: list[dict[str, Any]] = []
        for delta_name, delta in deltas:
            metrics = _expanded_candidate_metrics(
                base_action=normal_actions[index],
                intervention_action=intervention_actions[index],
                target_gap=float(target_gaps[index]),
                delta_name=delta_name,
                delta=delta,
                source_label=source_label,
            )
            row = {**meta, **{k: v for k, v in selected_source.items() if k not in meta}, **metrics}
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
                    **{k: v for k, v in selected_source.items() if k not in meta},
                    "rejection_reason": "no_candidate_passed_acceptance",
                    "gap_before": base_gap,
                    "target_gap": float(target_gaps[index]),
                    "gap_deficit_before": max(float(target_gaps[index]) - base_gap, 0.0),
                }
            )
    missing_selected = set(selected_by_key) - matched_keys
    for key in sorted(missing_selected):
        rejected_target_rows.append({"rejection_reason": "selected_source_not_reconstructed", "key": str(key)})

    group_rows = _group_summary(accepted_rows)
    pair_counts = Counter(str(row.get("fault_family_pair", "")) for row in accepted_rows)
    accepted_count = len(accepted_rows)
    strict_accepted = sum(1 for row in accepted_rows if str(row.get("source_label", "")) == "strict_low_tail")
    near_tail_accepted = sum(1 for row in accepted_rows if str(row.get("source_label", "")) == "near_tail_coverage")
    max_pair_fraction = float(max(pair_counts.values()) / accepted_count) if accepted_count else 0.0
    distinct_pairs = len({str(row.get("fault_family_pair", "")) for row in accepted_rows if str(row.get("fault_family_pair", ""))})
    distinct_seeds = len({str(row.get("seed", "")) for row in accepted_rows if str(row.get("seed", ""))})
    horizon_values = sorted({str(row.get("horizon", "")) for row in accepted_rows if str(row.get("horizon", ""))})
    checksum_after = model_parameter_checksum(model)
    result_class = classify_expanded_target_regeneration(
        actor_parameters_changed=bool(checksum_before != checksum_after),
        accepted_targets=accepted_count,
        strict_low_tail_accepted_targets=strict_accepted,
        distinct_fault_family_pairs=distinct_pairs,
        distinct_seeds=distinct_seeds,
        max_fault_family_pair_fraction=max_pair_fraction,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    summary = {
        "run_type": "public_base_expanded_target_regeneration",
        "checkpoint": checkpoint_path,
        "scenario_config": scenario_config_path,
        "positive_rows": positive_rows_path,
        "contrast_rows": contrast_rows_path,
        "objective_rows": objective_rows_path,
        "low_tail_rows": low_tail_rows_path,
        "near_base_alpha": NEAR_BASE_ALPHA,
        "near_tail_deficit_threshold": NEAR_TAIL_DEFICIT_THRESHOLD,
        "near_tail_gap_threshold": NEAR_TAIL_GAP_THRESHOLD,
        "max_rows": int(max_rows),
        "per_fault_pair_cap": int(per_fault_pair_cap),
        "per_seed_soft_cap": int(per_seed_soft_cap),
        "strict_low_tail_input_rows": int(len(low_tail_rows)),
        "source_candidate_rows": int(len(source_candidates)),
        "rejected_source_candidate_rows": int(len(rejected_source_candidates)),
        "selected_sources": int(len(selected_rows)),
        "selected_strict_low_tail_sources": int(
            sum(1 for row in selected_rows if bool(row.get("strict_low_tail", False)))
        ),
        "selected_near_tail_sources": int(
            sum(1 for row in selected_rows if str(row.get("source_label", "")) == "near_tail_coverage")
        ),
        "selected_sources_reconstructed": int(len(matched_keys)),
        "selected_sources_missing": int(len(missing_selected)),
        "candidate_actions": int(len(candidate_rows)),
        "accepted_targets": accepted_count,
        "strict_low_tail_accepted_targets": strict_accepted,
        "near_tail_accepted_targets": near_tail_accepted,
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
        "source_candidate_rows_csv": run_dir / "source_candidate_rows.csv",
        "rejected_source_candidate_rows_csv": run_dir / "rejected_source_candidate_rows.csv",
        "selected_source_rows_csv": run_dir / "selected_source_rows.csv",
        "candidate_action_rows_csv": run_dir / "candidate_action_rows.csv",
        "accepted_target_rows_csv": run_dir / "accepted_target_rows.csv",
        "rejected_target_rows_csv": run_dir / "rejected_target_rows.csv",
        "group_acceptance_summary_csv": run_dir / "group_acceptance_summary.csv",
    }
    write_csv_rows(run_dir / "source_candidate_rows.csv", source_candidates)
    write_csv_rows(run_dir / "rejected_source_candidate_rows.csv", rejected_source_candidates)
    write_csv_rows(run_dir / "selected_source_rows.csv", selected_source_rows)
    write_csv_rows(run_dir / "candidate_action_rows.csv", candidate_rows)
    write_csv_rows(run_dir / "accepted_target_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "rejected_target_rows.csv", rejected_target_rows)
    write_csv_rows(run_dir / "group_acceptance_summary.csv", group_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training expanded public-base target regeneration.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--objective-rows", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--max-rows", type=int, default=MAX_ROWS)
    parser.add_argument("--per-fault-family-pair-cap", type=int, default=PER_FAULT_PAIR_CAP)
    parser.add_argument("--per-seed-soft-cap", type=int, default=PER_SEED_SOFT_CAP)
    args = parser.parse_args()
    summary = run_public_base_expanded_target_regeneration(
        checkpoint_path=args.checkpoint,
        scenario_config_path=args.scenario_config,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        objective_rows_path=args.objective_rows,
        low_tail_rows_path=args.low_tail_rows,
        run_dir=args.run_dir,
        device=args.device,
        max_rows=args.max_rows,
        per_fault_pair_cap=args.per_fault_family_pair_cap,
        per_seed_soft_cap=args.per_seed_soft_cap,
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
