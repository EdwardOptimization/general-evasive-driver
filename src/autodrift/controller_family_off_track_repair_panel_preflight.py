"""No-rollout off-track repair panel preflight."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_preflight import (
    DEFAULT_CALIBRATION_MATRIX_CSV,
    DEFAULT_CALIBRATION_SPECS_JSON,
    base_spec_rows,
    contract_violations_for_specs,
    load_calibration_specs,
    read_csv_rows,
)


DEFAULT_REPAIR_TARGETS = Path("runs/m1718_off_track_dominance_localization/repair_target_slices.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1721_off_track_repair_panel_preflight")
EXPECTED_TASK_FAMILY_COUNTS = {"T4": 12, "T5": 6}
EXPECTED_SELECTED_BASE_SPEC_COUNT = 18
EXPECTED_VARIANTS_PER_BASE_SPEC = 4
EXPECTED_PROFILE_COUNT = 12
EXPECTED_REPAIR_PANEL_SPEC_COUNT = 72
EXPECTED_REPAIR_PANEL_MATRIX_CELL_COUNT = 864
REPAIR_VARIANT_PANEL = (
    {
        "repair_variant_label": "original_axis_baseline",
        "track_width_scale": "1.0",
        "finish_variant": "original",
        "max_steps_scale": "1.0",
    },
    {
        "repair_variant_label": "best_off_track_variant",
        "track_width_scale": "2.0",
        "finish_variant": "original",
        "max_steps_scale": "1.5",
    },
    {
        "repair_variant_label": "collision_control_wide_relaxed",
        "track_width_scale": "2.0",
        "finish_variant": "relaxed",
        "max_steps_scale": "1.0",
    },
    {
        "repair_variant_label": "wide_relaxed_extended",
        "track_width_scale": "2.0",
        "finish_variant": "relaxed",
        "max_steps_scale": "1.5",
    },
)


def _counts_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[key]) for row in rows).items()))


def _axis_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row["track_width_scale"]),
        str(row["finish_variant"]),
        str(row["max_steps_scale"]),
    )


def _repair_variant_label_for(row: Mapping[str, Any]) -> str | None:
    row_key = _axis_key(row)
    for variant in REPAIR_VARIANT_PANEL:
        if row_key == _axis_key(variant):
            return str(variant["repair_variant_label"])
    return None


def _float_value(row: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _target_rows_by_source(repair_target_rows: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_source: dict[str, list[dict[str, Any]]] = {}
    for row in repair_target_rows:
        if str(row.get("slice_type", "")) not in {"variant_source_edge", "source_task_family"}:
            continue
        source_edge = str(row.get("source_edge", ""))
        if not source_edge:
            continue
        by_source.setdefault(source_edge, []).append(dict(row))
    return by_source


def _target_summary_for_base(base: Mapping[str, Any], target_rows_by_source: Mapping[str, list[Mapping[str, Any]]]) -> dict[str, Any] | None:
    source_edge = str(base["source_edge"])
    task_family = str(base["task_family"])
    matched = [
        row
        for row in target_rows_by_source.get(source_edge, [])
        if not str(row.get("task_family", "")) or str(row.get("task_family", "")) == task_family
    ]
    if not matched:
        return None
    exact_task_count = sum(1 for row in matched if str(row.get("task_family", "")) == task_family)
    return {
        "target_slice_count": len(matched),
        "exact_task_target_count": exact_task_count,
        "max_target_off_track_rate": max(_float_value(row, "off_track_noncollision_noncompletion_rate") for row in matched),
        "min_target_collision_rate": min(_float_value(row, "collision_failure_rate") for row in matched),
        "target_slice_ids": ";".join(sorted(str(row.get("slice_id", "")) for row in matched if row.get("slice_id"))),
    }


def _diversity_score(candidate: Mapping[str, Any], selected: list[Mapping[str, Any]]) -> int:
    used_source_edges = {str(row["source_edge"]) for row in selected}
    used_executable_sources = {str(row["executable_source_family"]) for row in selected}
    used_templates = {str(row["env_template_family"]) for row in selected}
    used_windows = {str(row["window_tag"]) for row in selected}
    return (
        8 * int(str(candidate["source_edge"]) not in used_source_edges)
        + 4 * int(str(candidate["executable_source_family"]) not in used_executable_sources)
        + 2 * int(str(candidate["env_template_family"]) not in used_templates)
        + int(str(candidate["window_tag"]) not in used_windows)
    )


def select_repair_base_specs(
    bases: list[Mapping[str, Any]],
    repair_target_rows: list[Mapping[str, Any]],
    *,
    target_counts: Mapping[str, int] = EXPECTED_TASK_FAMILY_COUNTS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target_rows_by_source = _target_rows_by_source(repair_target_rows)
    candidate_rows: list[dict[str, Any]] = []
    for base in bases:
        summary = _target_summary_for_base(base, target_rows_by_source)
        if summary is None:
            continue
        row = {**dict(base), **summary}
        row["selection_candidate_reason"] = "matched_m1718_non_profile_target_slice"
        candidate_rows.append(row)

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for task_family, target_count in target_counts.items():
        family_selected: list[dict[str, Any]] = []
        family_candidates = [dict(row) for row in candidate_rows if str(row["task_family"]) == str(task_family)]
        while len(family_selected) < int(target_count) and len(family_selected) < len(family_candidates):
            scored: list[tuple[int, float, float, int, int, str, dict[str, Any]]] = []
            for candidate in family_candidates:
                base_id = str(candidate["base_task_source_id"])
                if base_id in selected_ids:
                    continue
                scored.append(
                    (
                        -int(candidate["exact_task_target_count"]),
                        -float(candidate["max_target_off_track_rate"]),
                        float(candidate["min_target_collision_rate"]),
                        -_diversity_score(candidate, family_selected),
                        -int(candidate["target_slice_count"]),
                        base_id,
                        candidate,
                    )
                )
            if not scored:
                break
            *_unused, chosen = min(scored, key=lambda item: item[:-1])
            chosen = dict(chosen)
            chosen["selection_order"] = len(selected) + 1
            chosen["selection_reason"] = "off_track_target_source_greedy"
            selected.append(chosen)
            family_selected.append(chosen)
            selected_ids.add(str(chosen["base_task_source_id"]))

    rejected: list[dict[str, Any]] = []
    for row in candidate_rows:
        item = dict(row)
        if str(item["base_task_source_id"]) in selected_ids:
            continue
        item["rejection_reason"] = "repair_panel_budget_exhausted_or_task_family_quota"
        rejected.append(item)

    return selected, rejected


def repair_panel_specs(
    calibration_specs: list[Mapping[str, Any]],
    selected_base_ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in calibration_specs:
        if str(spec["base_task_source_id"]) not in selected_base_ids:
            continue
        variant_label = _repair_variant_label_for(spec)
        if variant_label is None:
            continue
        row = dict(spec)
        row["repair_variant_label"] = variant_label
        rows.append(row)
    return sorted(
        rows,
        key=lambda row: (
            str(row["base_task_source_id"]),
            str(row["repair_variant_label"]),
            str(row["calibration_spec_id"]),
        ),
    )


def repair_panel_spec_csv_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "calibration_spec_id": row["calibration_spec_id"],
        "repair_variant_label": row["repair_variant_label"],
        "base_task_source_id": row["base_task_source_id"],
        "task_family": row["task_family"],
        "source_edge": row["source_edge"],
        "window_tag": row["window_tag"],
        "executable_source_family": row["executable_source_family"],
        "env_template_family": row["env_template_family"],
        "track_width_scale": row["track_width_scale"],
        "finish_variant": row["finish_variant"],
        "max_steps_scale": row["max_steps_scale"],
        "track_width": row["track_width"],
        "finish_pass_distance": row["finish_pass_distance"],
        "max_steps": row["max_steps"],
        "contract_violation_count": row["contract_violation_count"],
        "environment_rollout_scheduled": False,
        "profile_specific_tuning": False,
    }


def repair_panel_matrix_rows(
    full_matrix_rows: list[Mapping[str, Any]],
    repair_spec_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    variant_by_spec = {str(row["calibration_spec_id"]): str(row["repair_variant_label"]) for row in repair_spec_rows}
    rows: list[dict[str, Any]] = []
    for row in full_matrix_rows:
        calibration_spec_id = str(row["calibration_spec_id"])
        if calibration_spec_id not in variant_by_spec:
            continue
        item = dict(row)
        item["repair_variant_label"] = variant_by_spec[calibration_spec_id]
        item["repair_panel_workload_id"] = str(item["calibration_workload_id"])
        rows.append(item)
    return rows


def run_off_track_repair_panel_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    calibration_specs_json: Path | str = DEFAULT_CALIBRATION_SPECS_JSON,
    calibration_matrix_csv: Path | str = DEFAULT_CALIBRATION_MATRIX_CSV,
    repair_targets_csv: Path | str = DEFAULT_REPAIR_TARGETS,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    calibration_specs = load_calibration_specs(calibration_specs_json)
    bases = base_spec_rows(calibration_specs)
    repair_targets = read_csv_rows(repair_targets_csv)
    selected_bases, rejected_targets = select_repair_base_specs(bases, repair_targets)
    selected_base_ids = {str(row["base_task_source_id"]) for row in selected_bases}
    selected_specs = repair_panel_specs(calibration_specs, selected_base_ids)
    full_matrix_rows = read_csv_rows(calibration_matrix_csv)
    matrix_rows = repair_panel_matrix_rows(full_matrix_rows, selected_specs)
    contract_violations = contract_violations_for_specs(selected_specs)

    task_family_counts = _counts_by_key(selected_bases, "task_family")
    variants_per_base = _counts_by_key(selected_specs, "base_task_source_id")
    profiles_per_spec = _counts_by_key(matrix_rows, "calibration_spec_id")
    variant_label_counts = _counts_by_key(selected_specs, "repair_variant_label")
    profile_counts = _counts_by_key(matrix_rows, "profile_name")
    missing_variant_count = sum(1 for count in variants_per_base.values() if count != EXPECTED_VARIANTS_PER_BASE_SPEC)
    missing_profile_count = sum(1 for count in profiles_per_spec.values() if count != EXPECTED_PROFILE_COUNT)
    matrix_rollout_scheduled_count = sum(row.get("environment_rollout_scheduled") == "True" for row in matrix_rows)
    matrix_training_scheduled_count = sum(row.get("training_scheduled") == "True" for row in matrix_rows)
    matrix_profile_tuning_count = sum(row.get("profile_specific_tuning") == "True" for row in matrix_rows)
    missing_config_count = sum(row.get("config_exists") != "True" for row in matrix_rows)
    missing_checkpoint_count = sum(row.get("checkpoint_exists") != "True" for row in matrix_rows)
    source_variant_counts = Counter(_repair_variant_label_for(spec) for spec in calibration_specs)
    wide_relaxed_extended_available = source_variant_counts.get("wide_relaxed_extended", 0) >= len(bases)
    guardrail_flags = {
        "environment_rollout_started": matrix_rollout_scheduled_count > 0,
        "training_started": matrix_training_scheduled_count > 0,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": matrix_profile_tuning_count > 0,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        len(selected_bases) == EXPECTED_SELECTED_BASE_SPEC_COUNT
        and task_family_counts == EXPECTED_TASK_FAMILY_COUNTS
        and len(selected_specs) == EXPECTED_REPAIR_PANEL_SPEC_COUNT
        and len(matrix_rows) == EXPECTED_REPAIR_PANEL_MATRIX_CELL_COUNT
        and set(variant_label_counts) == {str(variant["repair_variant_label"]) for variant in REPAIR_VARIANT_PANEL}
        and all(count == EXPECTED_SELECTED_BASE_SPEC_COUNT for count in variant_label_counts.values())
        and missing_variant_count == 0
        and missing_profile_count == 0
        and wide_relaxed_extended_available
        and len(contract_violations) == 0
        and missing_config_count == 0
        and missing_checkpoint_count == 0
        and guardrail_violation_count == 0
    )

    generated_at = utc_timestamp()
    artifacts = {
        "summary": str(output / "summary.json"),
        "selected_base_specs": str(output / "selected_base_specs.csv"),
        "rejected_target_sources": str(output / "rejected_target_sources.csv"),
        "repair_panel_specs": str(output / "repair_panel_specs.json"),
        "repair_panel_specs_csv": str(output / "repair_panel_specs.csv"),
        "repair_panel_matrix": str(output / "repair_panel_matrix.csv"),
        "contract_violations": str(output / "contract_violations.csv"),
    }
    summary = {
        "result_class": (
            "off_track_repair_panel_preflight_pass"
            if passes
            else "off_track_repair_panel_preflight_fail"
        ),
        "generated_at_utc": generated_at,
        "output_dir": str(output),
        "source_calibration_spec_count": len(calibration_specs),
        "source_matrix_cell_count": len(full_matrix_rows),
        "source_base_spec_count": len(bases),
        "repair_target_slice_count": len(repair_targets),
        "eligible_base_spec_count": len(selected_bases) + len(rejected_targets),
        "selected_base_spec_count": len(selected_bases),
        "rejected_target_source_count": len(rejected_targets),
        "selected_task_family_counts": task_family_counts,
        "selected_source_edge_count": len({str(row["source_edge"]) for row in selected_bases}),
        "selected_executable_source_family_count": len(
            {str(row["executable_source_family"]) for row in selected_bases}
        ),
        "selected_env_template_family_count": len({str(row["env_template_family"]) for row in selected_bases}),
        "selected_window_tag_count": len({str(row["window_tag"]) for row in selected_bases}),
        "selected_source_edge_counts": _counts_by_key(selected_bases, "source_edge"),
        "repair_panel_spec_count": len(selected_specs),
        "repair_panel_matrix_cell_count": len(matrix_rows),
        "profile_count": len(profile_counts),
        "variant_label_counts": variant_label_counts,
        "profile_counts": profile_counts,
        "variants_per_base_spec_min": min(variants_per_base.values()) if variants_per_base else 0,
        "variants_per_base_spec_max": max(variants_per_base.values()) if variants_per_base else 0,
        "profiles_per_calibration_spec_min": min(profiles_per_spec.values()) if profiles_per_spec else 0,
        "profiles_per_calibration_spec_max": max(profiles_per_spec.values()) if profiles_per_spec else 0,
        "missing_variant_count": missing_variant_count,
        "missing_profile_count": missing_profile_count,
        "wide_relaxed_extended_available": bool(wide_relaxed_extended_available),
        "wide_relaxed_extended_source_spec_count": int(source_variant_counts.get("wide_relaxed_extended", 0)),
        "contract_violation_count": len(contract_violations),
        "missing_config_count": missing_config_count,
        "missing_checkpoint_count": missing_checkpoint_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": guardrail_flags["environment_rollout_started"],
        "training_started": guardrail_flags["training_started"],
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": guardrail_flags["profile_specific_tuning"],
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "passes_public_preflight_gates": bool(passes),
        "artifacts": artifacts,
        "next_blocker": "m1722-paper-route-controller-family-off-track-repair-panel-preflight-result-audit",
    }

    write_csv_rows(output / "selected_base_specs.csv", selected_bases)
    write_csv_rows(output / "rejected_target_sources.csv", rejected_targets)
    write_json(
        output / "repair_panel_specs.json",
        {
            "generated_at_utc": generated_at,
            "repair_panel_specs": selected_specs,
        },
    )
    write_csv_rows(output / "repair_panel_specs.csv", [repair_panel_spec_csv_row(row) for row in selected_specs])
    write_csv_rows(output / "repair_panel_matrix.csv", matrix_rows)
    write_csv_rows(
        output / "contract_violations.csv",
        contract_violations,
        fieldnames=["calibration_spec_id", "base_task_source_id", "violation"],
    )
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-rollout off-track repair panel subset.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--calibration-specs", type=Path, default=DEFAULT_CALIBRATION_SPECS_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX_CSV)
    parser.add_argument("--repair-targets", type=Path, default=DEFAULT_REPAIR_TARGETS)
    args = parser.parse_args()

    summary = run_off_track_repair_panel_preflight(
        output_dir=args.output_dir,
        calibration_specs_json=args.calibration_specs,
        calibration_matrix_csv=args.calibration_matrix,
        repair_targets_csv=args.repair_targets,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"selected_base_spec_count={summary['selected_base_spec_count']}")
    print(f"repair_panel_spec_count={summary['repair_panel_spec_count']}")
    print(f"repair_panel_matrix_cell_count={summary['repair_panel_matrix_cell_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")


if __name__ == "__main__":
    main()
