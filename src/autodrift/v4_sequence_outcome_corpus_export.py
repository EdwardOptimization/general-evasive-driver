"""Export M752 v4 sequence-outcome rows as an auditable corpus."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.sequence_outcome_corpus_export import ROLLOUT_FIELDS


V4_EXTRA_FIELDS = [
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
    "source_kind",
    "claim_boundary_level",
]

V4_ENRICHED_FIELDS = [
    "preferred_fidelity_class",
    "wrong_fidelity_class",
    "preferred_fault_params_json",
    "wrong_fault_params_json",
]

V4_ROLLOUT_FIELDS = [
    *ROLLOUT_FIELDS,
    *[field for field in V4_EXTRA_FIELDS if field not in ROLLOUT_FIELDS],
    *V4_ENRICHED_FIELDS,
]

POSITIVE_FIELDS = ["contrast_group_id", "proof_positive", *V4_ROLLOUT_FIELDS]
CONTRAST_FIELDS = ["contrast_group_id", "contrast_role", "proof_positive", *V4_ROLLOUT_FIELDS]

REQUIRED_V4_FIELDS = [
    "pair_id",
    "pairing_rule",
    "reset_action_l2_gap",
    "reset_margin_gap",
    "history_margin_gap",
    "action_l2_gap",
    "match_distance",
    "feature_distance",
    "source_kind",
    "source_pool",
    "claim_boundary_level",
]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _normal_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("source_index", "")), str(row.get("horizon", "")))


def _identity_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("source_index", "")),
        str(row.get("seed", "")),
        str(row.get("step", "")),
        str(row.get("pair_id", "")),
        str(row.get("preferred_fault", "")),
        str(row.get("wrong_fault", "")),
        str(row.get("fault_family_pair", "")),
        str(row.get("variant", "")),
        str(row.get("horizon", "")),
    )


def _contrast_group_id(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("source_index", "")),
            str(row.get("horizon", "")),
            str(row.get("variant", "")),
            str(row.get("pair_id", "")),
        ]
    )


def _is_sentinel(row: dict[str, Any]) -> bool:
    return _bool(row.get("sentinel", False)) or str(row.get("source_role", "")) == "sentinel"


def _normal_viable(row: dict[str, Any]) -> bool:
    return _bool(row.get("normal_success", False)) or _float(row.get("normal_margin")) >= 0.0


def _is_positive_candidate(row: dict[str, Any]) -> bool:
    return bool(_bool(row.get("sequence_outcome_critical", False)) and _normal_viable(row))


def _is_hard_negative_candidate(row: dict[str, Any]) -> bool:
    return bool(
        not _is_sentinel(row)
        and str(row.get("variant", "")) != "normal"
        and _bool(row.get("sequence_action_critical", False))
        and not _bool(row.get("sequence_outcome_critical", False))
        and _normal_viable(row)
    )


def _json_compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _dominance_fraction(values: list[Any]) -> float:
    if not values:
        return 0.0
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return float(max(counts.values()) / max(len(values), 1))


def _mean(values: list[float]) -> float:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else float("nan")


def _max(values: list[float]) -> float:
    finite = [value for value in values if np.isfinite(value)]
    return float(max(finite)) if finite else float("nan")


def _load_fault_config(path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    config = read_json(path)
    faults = {str(item.get("name", "")): item for item in config.get("faults", [])}
    return config, faults


def _fault_counts(config: dict[str, Any]) -> dict[str, int]:
    counts = {"current_model_fault": 0, "current_model_proxy": 0, "unknown": 0}
    for fault in config.get("faults", []):
        fidelity = str(fault.get("fidelity_class", "unknown"))
        counts[fidelity] = counts.get(fidelity, 0) + 1
    return counts


def _enrich_row(row: dict[str, Any], fault_specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    preferred = fault_specs.get(str(row.get("preferred_fault", "")), {})
    wrong = fault_specs.get(str(row.get("wrong_fault", "")), {})
    enriched = {field: row.get(field, "") for field in V4_ROLLOUT_FIELDS}
    enriched.update(
        {
            "preferred_fidelity_class": preferred.get("fidelity_class", "unknown"),
            "wrong_fidelity_class": wrong.get("fidelity_class", "unknown"),
            "preferred_fault_params_json": _json_compact(preferred.get("params", {})),
            "wrong_fault_params_json": _json_compact(wrong.get("params", {})),
        }
    )
    return enriched


def _has_required_v4_metadata(row: dict[str, Any]) -> bool:
    return all(str(row.get(field, "")).strip() for field in REQUIRED_V4_FIELDS)


def _has_fidelity_metadata(row: dict[str, Any]) -> bool:
    return str(row.get("preferred_fidelity_class", "")) != "unknown" and str(
        row.get("wrong_fidelity_class", "")
    ) != "unknown"


def _with_contrast(row: dict[str, Any], *, group_id: str, role: str, proof_positive: bool) -> dict[str, Any]:
    output = {field: row.get(field, "") for field in V4_ROLLOUT_FIELDS}
    output.update(
        {
            "contrast_group_id": group_id,
            "contrast_role": role,
            "proof_positive": bool(proof_positive),
        }
    )
    return output


def _group_balance_rows(rows: list[dict[str, Any]], *, dimensions: tuple[str, ...]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    total = max(len(rows), 1)
    for dimension in dimensions:
        groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            groups.setdefault(str(row.get(dimension, "")), []).append(row)
        for value, group_rows in sorted(groups.items()):
            output.append(
                {
                    "dimension": dimension,
                    "value": value,
                    "positive_rows": int(len(group_rows)),
                    "positive_fraction": float(len(group_rows) / total),
                    "unique_positive_seeds": int(len({str(row.get("seed", "")) for row in group_rows})),
                    "unique_positive_fault_family_pairs": int(
                        len({str(row.get("fault_family_pair", "")) for row in group_rows})
                    ),
                    "margin_gap_mean": _mean([_float(row.get("margin_gap_from_normal")) for row in group_rows]),
                    "margin_gap_max": _max([_float(row.get("margin_gap_from_normal")) for row in group_rows]),
                    "prefix_l2_mean": _mean([_float(row.get("prefix_l2_mean")) for row in group_rows]),
                    "prefix_l2_max": _max([_float(row.get("prefix_l2_mean")) for row in group_rows]),
                }
            )
    return output


def _variant_horizon_balance_rows(
    positives: list[dict[str, Any]],
    hard_negatives: list[dict[str, Any]],
    normal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    keys = sorted(
        {
            (str(row.get("variant", "")), str(row.get("horizon", "")))
            for row in [*positives, *hard_negatives, *normal_rows]
        }
    )
    output: list[dict[str, Any]] = []
    for variant, horizon in keys:
        positive_group = [
            row for row in positives if str(row.get("variant", "")) == variant and str(row.get("horizon", "")) == horizon
        ]
        hard_group = [
            row
            for row in hard_negatives
            if str(row.get("variant", "")) == variant and str(row.get("horizon", "")) == horizon
        ]
        normal_group = [
            row for row in normal_rows if str(row.get("variant", "")) == variant and str(row.get("horizon", "")) == horizon
        ]
        output.append(
            {
                "variant": variant,
                "horizon": horizon,
                "positive_rows": int(len(positive_group)),
                "hard_negative_rows": int(len(hard_group)),
                "normal_rows": int(len(normal_group)),
                "unique_positive_seeds": int(len({str(row.get("seed", "")) for row in positive_group})),
                "margin_gap_mean": _mean([_float(row.get("margin_gap_from_normal")) for row in positive_group]),
                "margin_gap_max": _max([_float(row.get("margin_gap_from_normal")) for row in positive_group]),
                "prefix_l2_mean": _mean([_float(row.get("prefix_l2_mean")) for row in positive_group]),
                "prefix_l2_max": _max([_float(row.get("prefix_l2_mean")) for row in positive_group]),
            }
        )
    return output


def classify_v4_sequence_outcome_corpus(
    *,
    positive_rows: int,
    hard_negative_rows: int,
    positive_sentinel_rows: int,
    positive_source_role_sentinel_rows: int,
    duplicate_positive_keys: int,
    missing_normal_matches: int,
    positive_rows_missing_v4_metadata: int,
    positive_rows_missing_fidelity_metadata: int,
    unique_positive_seeds: int,
    unique_positive_fault_family_pairs: int,
    max_positive_seed_dominance: float,
    min_positive_rows: int = 1000,
    min_unique_positive_seeds: int = 24,
    min_unique_positive_fault_family_pairs: int = 16,
    max_allowed_positive_seed_dominance: float = 0.20,
) -> str:
    if (
        int(positive_sentinel_rows) > 0
        or int(positive_source_role_sentinel_rows) > 0
        or int(duplicate_positive_keys) > 0
        or int(missing_normal_matches) > 0
        or int(positive_rows_missing_v4_metadata) > 0
        or int(positive_rows_missing_fidelity_metadata) > 0
    ):
        return "v4_sequence_outcome_corpus_artifact"
    if int(positive_rows) < int(min_positive_rows):
        return "v4_sequence_outcome_corpus_sparse"
    if (
        int(unique_positive_seeds) < int(min_unique_positive_seeds)
        or int(unique_positive_fault_family_pairs) < int(min_unique_positive_fault_family_pairs)
        or float(max_positive_seed_dominance) > float(max_allowed_positive_seed_dominance)
    ):
        return "v4_sequence_outcome_corpus_unbalanced"
    if int(hard_negative_rows) < int(positive_rows):
        return "v4_sequence_outcome_corpus_hard_negative_sparse"
    return "v4_sequence_outcome_corpus_exported"


def export_v4_sequence_outcome_corpus(
    *,
    summary_path: Path,
    rollouts_path: Path,
    sequence_critical_rows_path: Path,
    sentinel_rows_path: Path,
    fault_config_path: Path,
    run_dir: Path,
    max_hard_negatives_per_positive: int = 2,
    min_positive_rows: int = 1000,
    min_unique_positive_seeds: int = 24,
    min_unique_positive_fault_family_pairs: int = 16,
    max_allowed_positive_seed_dominance: float = 0.20,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(summary_path)
    fault_config, fault_specs = _load_fault_config(fault_config_path)
    fault_counts = _fault_counts(fault_config)
    rollouts = [_enrich_row(row, fault_specs) for row in _read_csv_rows(rollouts_path)]
    sequence_input_rows = [_enrich_row(row, fault_specs) for row in _read_csv_rows(sequence_critical_rows_path)]
    sentinel_input_rows = [_enrich_row(row, fault_specs) for row in _read_csv_rows(sentinel_rows_path)]

    normal_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rollouts:
        if str(row.get("variant", "")) == "normal":
            normal_by_key.setdefault(_normal_key(row), row)

    raw_positive_candidates = [row for row in rollouts if _is_positive_candidate(row)]
    excluded_sentinel_rows = [row for row in raw_positive_candidates if _is_sentinel(row)]

    positives: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, ...]] = set()
    duplicate_positive_keys = 0
    missing_normal_matches = 0
    for row in raw_positive_candidates:
        identity = _identity_key(row)
        if identity in seen_keys:
            duplicate_positive_keys += 1
            rejected_rows.append({**row, "export_rejection_reason": "duplicate_positive_key"})
            continue
        seen_keys.add(identity)
        if _is_sentinel(row):
            rejected_rows.append({**row, "export_rejection_reason": "sentinel_positive_candidate"})
            continue
        if _normal_key(row) not in normal_by_key:
            missing_normal_matches += 1
            rejected_rows.append({**row, "export_rejection_reason": "missing_normal_match"})
            continue
        positives.append(row)

    positive_sentinel_rows = sum(1 for row in positives if _bool(row.get("sentinel", False)))
    positive_source_role_sentinel_rows = sum(1 for row in positives if str(row.get("source_role", "")) == "sentinel")
    positive_rows_missing_v4_metadata = sum(1 for row in positives if not _has_required_v4_metadata(row))
    positive_rows_missing_fidelity_metadata = sum(1 for row in positives if not _has_fidelity_metadata(row))

    hard_negative_rows: list[dict[str, Any]] = []
    matched_normal_rows: list[dict[str, Any]] = []
    contrast_rows: list[dict[str, Any]] = []
    positives_without_hard_negative = 0
    for positive in positives:
        group_id = _contrast_group_id(positive)
        normal = normal_by_key[_normal_key(positive)]
        matched_normal_rows.append(normal)
        contrast_rows.append(_with_contrast(normal, group_id=group_id, role="normal", proof_positive=False))
        contrast_rows.append(
            _with_contrast(positive, group_id=group_id, role="positive_intervention", proof_positive=True)
        )
        candidates = [
            row
            for row in rollouts
            if _normal_key(row) == _normal_key(positive)
            and _identity_key(row) != _identity_key(positive)
            and _is_hard_negative_candidate(row)
        ]
        candidates.sort(
            key=lambda item: (
                _float(item.get("prefix_l2_mean"), default=0.0),
                _float(item.get("margin_gap_from_normal"), default=0.0),
            ),
            reverse=True,
        )
        if not candidates:
            positives_without_hard_negative += 1
        for hard_negative in candidates[: max(0, int(max_hard_negatives_per_positive))]:
            hard_negative_rows.append(hard_negative)
            contrast_rows.append(
                _with_contrast(
                    hard_negative,
                    group_id=group_id,
                    role="hard_negative_action_only",
                    proof_positive=False,
                )
            )

    unique_positive_seeds = len({str(row.get("seed", "")) for row in positives})
    unique_positive_pairs = len({str(row.get("fault_family_pair", "")) for row in positives})
    max_positive_seed_dominance = _dominance_fraction([row.get("seed", "") for row in positives])
    max_positive_pair_dominance = _dominance_fraction([row.get("fault_family_pair", "") for row in positives])
    result_class = classify_v4_sequence_outcome_corpus(
        positive_rows=len(positives),
        hard_negative_rows=len(hard_negative_rows),
        positive_sentinel_rows=positive_sentinel_rows,
        positive_source_role_sentinel_rows=positive_source_role_sentinel_rows,
        duplicate_positive_keys=duplicate_positive_keys,
        missing_normal_matches=missing_normal_matches,
        positive_rows_missing_v4_metadata=positive_rows_missing_v4_metadata,
        positive_rows_missing_fidelity_metadata=positive_rows_missing_fidelity_metadata,
        unique_positive_seeds=unique_positive_seeds,
        unique_positive_fault_family_pairs=unique_positive_pairs,
        max_positive_seed_dominance=max_positive_seed_dominance,
        min_positive_rows=min_positive_rows,
        min_unique_positive_seeds=min_unique_positive_seeds,
        min_unique_positive_fault_family_pairs=min_unique_positive_fault_family_pairs,
        max_allowed_positive_seed_dominance=max_allowed_positive_seed_dominance,
    )

    positive_output_rows = [
        {
            **{field: row.get(field, "") for field in V4_ROLLOUT_FIELDS},
            "contrast_group_id": _contrast_group_id(row),
            "proof_positive": True,
        }
        for row in positives
    ]
    write_csv_rows(run_dir / "positive_sequence_outcomes.csv", positive_output_rows, fieldnames=POSITIVE_FIELDS)
    write_csv_rows(run_dir / "contrast_rows.csv", contrast_rows, fieldnames=CONTRAST_FIELDS)
    write_csv_rows(run_dir / "hard_negative_rows.csv", hard_negative_rows, fieldnames=V4_ROLLOUT_FIELDS)
    write_csv_rows(run_dir / "excluded_sentinel_rows.csv", excluded_sentinel_rows, fieldnames=V4_ROLLOUT_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(
        run_dir / "source_balance.csv",
        _group_balance_rows(
            positives,
            dimensions=(
                "seed",
                "source_kind",
                "source_pool",
                "claim_boundary_level",
                "source_role",
                "preferred_fault_family",
                "wrong_fault_family",
                "fault_family_pair",
                "variant",
                "horizon",
                "assigned_split",
            ),
        ),
    )
    write_csv_rows(
        run_dir / "variant_horizon_balance.csv",
        _variant_horizon_balance_rows(positives, hard_negative_rows, matched_normal_rows),
    )
    write_csv_rows(
        run_dir / "fault_family_balance.csv",
        _group_balance_rows(
            positives,
            dimensions=(
                "preferred_fault_family",
                "wrong_fault_family",
                "fault_family_pair",
                "preferred_fidelity_class",
                "wrong_fidelity_class",
            ),
        ),
    )

    hard_negative_complete = len(hard_negative_rows) >= len(positives)
    positive_corpus_gate_pass = result_class in {
        "v4_sequence_outcome_corpus_exported",
        "v4_sequence_outcome_corpus_hard_negative_sparse",
    }
    summary = {
        "run_type": "v4_sequence_outcome_corpus_export",
        "summary_input": summary_path,
        "rollouts_input": rollouts_path,
        "sequence_critical_rows_input": sequence_critical_rows_path,
        "sentinel_rows_input": sentinel_rows_path,
        "fault_config": fault_config_path,
        "fault_config_notes": fault_config.get("notes", ""),
        "claim_boundary": fault_config.get("claim_boundary", {}),
        "claim_boundary_level": sorted({str(row.get("claim_boundary_level", "")) for row in positives}),
        "future_only_fault_count": int(len(fault_config.get("future_only_faults", []))),
        "future_only_faults": list(fault_config.get("future_only_faults", [])),
        "current_model_fault_count": int(fault_counts.get("current_model_fault", 0)),
        "current_model_proxy_fault_count": int(fault_counts.get("current_model_proxy", 0)),
        "source_summary_result_class": source_summary.get("result_class"),
        "rollout_rows": int(len(rollouts)),
        "sequence_critical_input_rows": int(len(sequence_input_rows)),
        "sentinel_input_rows": int(len(sentinel_input_rows)),
        "raw_positive_candidates": int(len(raw_positive_candidates)),
        "sentinel_positive_candidates": int(len(excluded_sentinel_rows)),
        "positive_rows": int(len(positives)),
        "positive_sentinel_rows": int(positive_sentinel_rows),
        "positive_source_role_sentinel_rows": int(positive_source_role_sentinel_rows),
        "sentinel_false_positive_rows_exported_as_positive": int(
            positive_sentinel_rows + positive_source_role_sentinel_rows
        ),
        "excluded_sentinel_rows": int(len(excluded_sentinel_rows)),
        "duplicate_positive_keys": int(duplicate_positive_keys),
        "missing_normal_matches": int(missing_normal_matches),
        "positive_rows_missing_v4_metadata": int(positive_rows_missing_v4_metadata),
        "positive_rows_missing_fidelity_metadata": int(positive_rows_missing_fidelity_metadata),
        "unique_positive_seeds": int(unique_positive_seeds),
        "unique_positive_fault_family_pairs": int(unique_positive_pairs),
        "max_positive_seed_dominance": float(max_positive_seed_dominance),
        "max_positive_fault_family_pair_dominance": float(max_positive_pair_dominance),
        "positive_variants": sorted({str(row.get("variant", "")) for row in positives}),
        "positive_horizons": sorted({int(row.get("horizon", 0)) for row in positives}),
        "positive_source_kinds": sorted({str(row.get("source_kind", "")) for row in positives}),
        "positive_source_pools": sorted({str(row.get("source_pool", "")) for row in positives}),
        "positive_claim_boundary_levels": sorted({str(row.get("claim_boundary_level", "")) for row in positives}),
        "positive_preferred_fidelity_classes": sorted(
            {str(row.get("preferred_fidelity_class", "")) for row in positives}
        ),
        "positive_wrong_fidelity_classes": sorted({str(row.get("wrong_fidelity_class", "")) for row in positives}),
        "contrast_groups": int(len(positives)),
        "normal_rows": int(len(matched_normal_rows)),
        "positive_intervention_rows": int(len(positives)),
        "hard_negative_rows": int(len(hard_negative_rows)),
        "positives_without_hard_negative": int(positives_without_hard_negative),
        "hard_negative_complete": bool(hard_negative_complete),
        "hard_negative_rows_capped_by_positive": int(min(len(hard_negative_rows), len(positives))),
        "rejected_rows": int(len(rejected_rows)),
        "thresholds": {
            "min_positive_rows": int(min_positive_rows),
            "min_unique_positive_seeds": int(min_unique_positive_seeds),
            "min_unique_positive_fault_family_pairs": int(min_unique_positive_fault_family_pairs),
            "max_allowed_positive_seed_dominance": float(max_allowed_positive_seed_dominance),
            "max_hard_negatives_per_positive": int(max_hard_negatives_per_positive),
        },
        "positive_corpus_gate_pass": bool(positive_corpus_gate_pass),
        "v4_metadata_gate_pass": bool(
            positive_rows_missing_v4_metadata == 0 and positive_rows_missing_fidelity_metadata == 0
        ),
        "training_started": False,
        "optimizer_started": False,
        "checkpoint_loaded": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "positive_sequence_outcomes_csv": run_dir / "positive_sequence_outcomes.csv",
        "contrast_rows_csv": run_dir / "contrast_rows.csv",
        "hard_negative_rows_csv": run_dir / "hard_negative_rows.csv",
        "excluded_sentinel_rows_csv": run_dir / "excluded_sentinel_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "source_balance_csv": run_dir / "source_balance.csv",
        "variant_horizon_balance_csv": run_dir / "variant_horizon_balance.csv",
        "fault_family_balance_csv": run_dir / "fault_family_balance.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a sentinel-filtered v4 sequence-outcome corpus.")
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--rollouts", type=Path, required=True)
    parser.add_argument("--sequence-critical-rows", type=Path, required=True)
    parser.add_argument("--sentinel-rows", type=Path, required=True)
    parser.add_argument("--fault-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--max-hard-negatives-per-positive", type=int, default=2)
    args = parser.parse_args()
    summary = export_v4_sequence_outcome_corpus(
        summary_path=args.summary,
        rollouts_path=args.rollouts,
        sequence_critical_rows_path=args.sequence_critical_rows,
        sentinel_rows_path=args.sentinel_rows,
        fault_config_path=args.fault_config,
        run_dir=args.run_dir,
        max_hard_negatives_per_positive=args.max_hard_negatives_per_positive,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
