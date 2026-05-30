"""No-rollout source-expanded calibrated scale-up preflight."""

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


DEFAULT_M1705_SELECTED_BASE_SPECS = Path(
    "runs/m1705_controller_family_bounded_calibration_smoke_preflight/selected_base_specs.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1712_controller_family_calibrated_scale_up_preflight")
EXPECTED_TASK_FAMILY_COUNTS = {"T4": 9, "T5": 9}
EXPECTED_SELECTED_BASE_SPEC_COUNT = 18
EXPECTED_VARIANTS_PER_BASE_SPEC = 4
EXPECTED_PROFILE_COUNT = 12
EXPECTED_SCALE_UP_CALIBRATION_SPEC_COUNT = 72
EXPECTED_SCALE_UP_MATRIX_CELL_COUNT = 864
VARIANT_PANEL = (
    {
        "scale_up_variant_label": "original_axis_baseline",
        "track_width_scale": "1.0",
        "finish_variant": "original",
        "max_steps_scale": "1.0",
    },
    {
        "scale_up_variant_label": "best_off_track_variant",
        "track_width_scale": "2.0",
        "finish_variant": "original",
        "max_steps_scale": "1.5",
    },
    {
        "scale_up_variant_label": "collision_control_wide_relaxed",
        "track_width_scale": "2.0",
        "finish_variant": "relaxed",
        "max_steps_scale": "1.0",
    },
    {
        "scale_up_variant_label": "mid_calibration_variant",
        "track_width_scale": "1.5",
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


def _variant_label_for(row: Mapping[str, Any]) -> str | None:
    row_key = _axis_key(row)
    for variant in VARIANT_PANEL:
        if row_key == _axis_key(variant):
            return str(variant["scale_up_variant_label"])
    return None


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


def select_scale_up_base_specs(
    bases: list[Mapping[str, Any]],
    anchor_rows: list[Mapping[str, Any]],
    *,
    target_counts: Mapping[str, int] = EXPECTED_TASK_FAMILY_COUNTS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    base_by_id = {str(row["base_task_source_id"]): dict(row) for row in bases}
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for anchor in anchor_rows:
        base_id = str(anchor["base_task_source_id"])
        if base_id not in base_by_id or base_id in selected_ids:
            continue
        row = dict(base_by_id[base_id])
        row["selection_order"] = len(selected) + 1
        row["selection_reason"] = "m1705_anchor"
        selected.append(row)
        selected_ids.add(base_id)

    for task_family, target_count in target_counts.items():
        family_selected = [row for row in selected if str(row["task_family"]) == str(task_family)]
        family_candidates = [dict(row) for row in bases if str(row["task_family"]) == str(task_family)]
        while len(family_selected) < int(target_count) and len(family_selected) < len(family_candidates):
            scored: list[tuple[int, str, dict[str, Any]]] = []
            for candidate in family_candidates:
                base_id = str(candidate["base_task_source_id"])
                if base_id in selected_ids:
                    continue
                scored.append((-_diversity_score(candidate, family_selected), base_id, candidate))
            if not scored:
                break
            _score, _base_id, chosen = min(scored, key=lambda item: (item[0], item[1]))
            chosen = dict(chosen)
            chosen["selection_order"] = len(selected) + 1
            chosen["selection_reason"] = "source_diverse_scale_up_greedy"
            selected.append(chosen)
            family_selected.append(chosen)
            selected_ids.add(str(chosen["base_task_source_id"]))

    rejected: list[dict[str, Any]] = []
    for row in bases:
        row = dict(row)
        if str(row["base_task_source_id"]) in selected_ids:
            continue
        row["rejection_reason"] = "source_diverse_scale_up_budget_exhausted"
        rejected.append(row)

    return selected, rejected


def scale_up_specs(
    calibration_specs: list[Mapping[str, Any]],
    selected_base_ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in calibration_specs:
        if str(spec["base_task_source_id"]) not in selected_base_ids:
            continue
        variant_label = _variant_label_for(spec)
        if variant_label is None:
            continue
        row = dict(spec)
        row["scale_up_variant_label"] = variant_label
        rows.append(row)
    return sorted(
        rows,
        key=lambda row: (
            str(row["base_task_source_id"]),
            str(row["scale_up_variant_label"]),
            str(row["calibration_spec_id"]),
        ),
    )


def scale_up_spec_csv_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "calibration_spec_id": row["calibration_spec_id"],
        "scale_up_variant_label": row["scale_up_variant_label"],
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


def scale_up_matrix_rows(full_matrix_rows: list[Mapping[str, Any]], scale_up_spec_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    variant_by_spec = {str(row["calibration_spec_id"]): str(row["scale_up_variant_label"]) for row in scale_up_spec_rows}
    rows: list[dict[str, Any]] = []
    for row in full_matrix_rows:
        calibration_spec_id = str(row["calibration_spec_id"])
        if calibration_spec_id not in variant_by_spec:
            continue
        item = dict(row)
        item["scale_up_variant_label"] = variant_by_spec[calibration_spec_id]
        item["scale_up_workload_id"] = str(item["calibration_workload_id"])
        rows.append(item)
    return rows


def run_calibrated_scale_up_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    calibration_specs_json: Path | str = DEFAULT_CALIBRATION_SPECS_JSON,
    calibration_matrix_csv: Path | str = DEFAULT_CALIBRATION_MATRIX_CSV,
    anchor_base_specs_csv: Path | str = DEFAULT_M1705_SELECTED_BASE_SPECS,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    calibration_specs = load_calibration_specs(calibration_specs_json)
    bases = base_spec_rows(calibration_specs)
    anchors = read_csv_rows(anchor_base_specs_csv)
    selected_bases, rejected_bases = select_scale_up_base_specs(bases, anchors)
    selected_base_ids = {str(row["base_task_source_id"]) for row in selected_bases}
    selected_specs = scale_up_specs(calibration_specs, selected_base_ids)
    matrix_rows = scale_up_matrix_rows(read_csv_rows(calibration_matrix_csv), selected_specs)
    contract_violations = contract_violations_for_specs(selected_specs)

    task_family_counts = _counts_by_key(selected_bases, "task_family")
    variants_per_base = _counts_by_key(selected_specs, "base_task_source_id")
    profiles_per_spec = _counts_by_key(matrix_rows, "calibration_spec_id")
    variant_label_counts = _counts_by_key(selected_specs, "scale_up_variant_label")
    profile_counts = _counts_by_key(matrix_rows, "profile_name")
    missing_variant_count = sum(1 for count in variants_per_base.values() if count != EXPECTED_VARIANTS_PER_BASE_SPEC)
    missing_profile_count = sum(1 for count in profiles_per_spec.values() if count != EXPECTED_PROFILE_COUNT)
    matrix_rollout_scheduled_count = sum(row.get("environment_rollout_scheduled") == "True" for row in matrix_rows)
    matrix_training_scheduled_count = sum(row.get("training_scheduled") == "True" for row in matrix_rows)
    matrix_profile_tuning_count = sum(row.get("profile_specific_tuning") == "True" for row in matrix_rows)
    missing_config_count = sum(row.get("config_exists") != "True" for row in matrix_rows)
    missing_checkpoint_count = sum(row.get("checkpoint_exists") != "True" for row in matrix_rows)
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
        and len(selected_specs) == EXPECTED_SCALE_UP_CALIBRATION_SPEC_COUNT
        and len(matrix_rows) == EXPECTED_SCALE_UP_MATRIX_CELL_COUNT
        and set(variant_label_counts) == {str(variant["scale_up_variant_label"]) for variant in VARIANT_PANEL}
        and all(count == EXPECTED_SELECTED_BASE_SPEC_COUNT for count in variant_label_counts.values())
        and missing_variant_count == 0
        and missing_profile_count == 0
        and len(contract_violations) == 0
        and missing_config_count == 0
        and missing_checkpoint_count == 0
        and guardrail_violation_count == 0
    )

    generated_at = utc_timestamp()
    artifacts = {
        "summary": str(output / "summary.json"),
        "selected_base_specs": str(output / "selected_base_specs.csv"),
        "rejected_base_specs": str(output / "rejected_base_specs.csv"),
        "scale_up_calibration_specs": str(output / "scale_up_calibration_specs.json"),
        "scale_up_calibration_specs_csv": str(output / "scale_up_calibration_specs.csv"),
        "scale_up_matrix": str(output / "scale_up_matrix.csv"),
        "contract_violations": str(output / "contract_violations.csv"),
    }
    summary = {
        "result_class": (
            "controller_family_calibrated_scale_up_preflight_pass"
            if passes
            else "controller_family_calibrated_scale_up_preflight_fail"
        ),
        "generated_at_utc": generated_at,
        "output_dir": str(output),
        "source_calibration_spec_count": len(calibration_specs),
        "source_matrix_cell_count": len(read_csv_rows(calibration_matrix_csv)),
        "base_spec_count": len(bases),
        "anchor_base_spec_count": len(anchors),
        "selected_base_spec_count": len(selected_bases),
        "rejected_base_spec_count": len(rejected_bases),
        "selected_task_family_counts": task_family_counts,
        "scale_up_calibration_spec_count": len(selected_specs),
        "scale_up_matrix_cell_count": len(matrix_rows),
        "profile_count": len(profile_counts),
        "variant_label_counts": variant_label_counts,
        "profile_counts": profile_counts,
        "variants_per_base_spec_min": min(variants_per_base.values()) if variants_per_base else 0,
        "variants_per_base_spec_max": max(variants_per_base.values()) if variants_per_base else 0,
        "profiles_per_calibration_spec_min": min(profiles_per_spec.values()) if profiles_per_spec else 0,
        "profiles_per_calibration_spec_max": max(profiles_per_spec.values()) if profiles_per_spec else 0,
        "missing_variant_count": missing_variant_count,
        "missing_profile_count": missing_profile_count,
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
        "next_blocker": "m1713-paper-route-controller-family-calibrated-scale-up-preflight-result-audit",
    }

    write_csv_rows(output / "selected_base_specs.csv", selected_bases)
    write_csv_rows(output / "rejected_base_specs.csv", rejected_bases)
    write_json(
        output / "scale_up_calibration_specs.json",
        {
            "generated_at_utc": generated_at,
            "scale_up_calibration_specs": selected_specs,
        },
    )
    write_csv_rows(output / "scale_up_calibration_specs.csv", [scale_up_spec_csv_row(row) for row in selected_specs])
    write_csv_rows(output / "scale_up_matrix.csv", matrix_rows)
    write_csv_rows(
        output / "contract_violations.csv",
        contract_violations,
        fieldnames=["calibration_spec_id", "base_task_source_id", "violation"],
    )
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-rollout calibrated scale-up subset.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--calibration-specs", type=Path, default=DEFAULT_CALIBRATION_SPECS_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX_CSV)
    parser.add_argument("--anchor-base-specs", type=Path, default=DEFAULT_M1705_SELECTED_BASE_SPECS)
    args = parser.parse_args()

    summary = run_calibrated_scale_up_preflight(
        output_dir=args.output_dir,
        calibration_specs_json=args.calibration_specs,
        calibration_matrix_csv=args.calibration_matrix,
        anchor_base_specs_csv=args.anchor_base_specs,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"selected_base_spec_count={summary['selected_base_spec_count']}")
    print(f"scale_up_calibration_spec_count={summary['scale_up_calibration_spec_count']}")
    print(f"scale_up_matrix_cell_count={summary['scale_up_matrix_cell_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")


if __name__ == "__main__":
    main()
