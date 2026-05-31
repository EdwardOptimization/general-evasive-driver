"""No-rollout calibration for stable-AEB anchor fallback geometry."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.executable_v2_support_first_source_mining import (
    ACCEPTED,
    SUPPORTED,
    evaluate_candidate_cell,
    required_label_for_role,
    scan_candidate_profile,
)
from autodrift.executable_v2_task_quality_offtrack_support_repair_source_mining import (
    BLOCKED_ROW_FIELDS,
    DEFAULT_REPAIR_TEMPLATES,
    REPAIR_METADATA_FIELDS,
    SOURCE_ROW_FIELDS,
    template_to_source_candidate,
)


DEFAULT_BLOCKED_ROWS = Path(
    "runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/repair_blocked_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration"
)
DEFAULT_NEXT_BLOCKER = "m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design"
ANCHOR_KIND = "anchor_neighborhood"
TARGET_ROLE = "stable_aeb"
TARGET_LABEL = "aeb_feasible"
OLD_OBSTACLE_DISTANCE = 28.0
OLD_OBSTACLE_HALF_WIDTH = 0.80
DEFAULT_TRACK_WIDTH = 5.75
DISTANCE_GRID = tuple(float(value) for value in range(36, 81, 4))
HALF_WIDTH_GRID = (0.30, 0.45, 0.60, 0.75, 0.90, 1.00)
SURFACE_ORDER = ("post_friction_step", "steady_surface")
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
SUMMARY_ARTIFACTS = {
    "summary": "summary.json",
    "anchor_fallback_candidates": "anchor_fallback_candidates.csv",
    "anchor_calibration_source_rows": "anchor_calibration_source_rows.csv",
    "anchor_calibration_accepted_cells": "anchor_calibration_accepted_cells.csv",
    "anchor_calibration_blocked_rows": "anchor_calibration_blocked_rows.csv",
    "selected_anchor_fallback_geometry": "selected_anchor_fallback_geometry.json",
    "claim_boundary": "claim_boundary.csv",
}


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_templates(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("repair_candidate_sources")
    if not isinstance(rows, list):
        raise ValueError("repair template artifact must contain repair_candidate_sources")
    return [dict(row) for row in rows]


def _is_anchor_template(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("repair_source_kind", "")) == ANCHOR_KIND
        and str(row.get("source_role_semantics", "")) == TARGET_ROLE
        and str(row.get("sampled_obstacle_label", "")) == TARGET_LABEL
    )


def _is_blocked_anchor(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("repair_source_kind", "")) == ANCHOR_KIND
        and str(row.get("source_role_semantics", "")) == TARGET_ROLE
        and str(row.get("source_support_failure_reason", "")) == "label_role_mismatch"
        and str(row.get("dominant_label", "")) == "aes_feasible"
    )


def _surface(row: Mapping[str, Any]) -> str:
    return str(row.get("surface_variant") or row.get("parent_surface_variant") or "")


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _patched_anchor_candidate(row: Mapping[str, Any], *, obstacle_distance: float, obstacle_half_width: float) -> dict[str, Any]:
    candidate = template_to_source_candidate(row, specs_by_id={})
    distance_center = float(obstacle_distance) + _float(row.get("obstacle_distance_delta"), 0.0)
    half_width_center = max(0.10, float(obstacle_half_width) + _float(row.get("obstacle_half_width_delta"), 0.0))
    candidate.update(
        {
            "base_geometry_source": "calibrated_anchor_fallback",
            "obstacle_distance_min": max(1.0, distance_center - 4.0),
            "obstacle_distance_max": max(1.0, distance_center + 4.0),
            "obstacle_distance_count": 9,
            "obstacle_half_width_min": max(0.10, half_width_center - 0.15),
            "obstacle_half_width_max": max(0.10, half_width_center + 0.15),
            "obstacle_half_width_count": 7,
            "post_obstacle_track_width": DEFAULT_TRACK_WIDTH + _float(row.get("post_obstacle_track_width_delta"), 0.0),
            "source_required_label": required_label_for_role(str(row.get("source_role_semantics", ""))),
            "source_allowed_labels": required_label_for_role(str(row.get("source_role_semantics", ""))),
            "labels_enter_actor_input": False,
            "v2_ranking_admissible_by_default": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }
    )
    return candidate


def _center_label(row: Mapping[str, Any], *, obstacle_distance: float, obstacle_half_width: float) -> str:
    candidate = _patched_anchor_candidate(row, obstacle_distance=obstacle_distance, obstacle_half_width=obstacle_half_width)
    cell = evaluate_candidate_cell(
        candidate=candidate,
        obstacle_distance=float(obstacle_distance),
        obstacle_half_width=float(obstacle_half_width),
    )
    return str(cell["label"])


def _scan_surface_fallback(
    *,
    rows: list[dict[str, Any]],
    surface: str,
    obstacle_distance: float,
    obstacle_half_width: float,
) -> dict[str, Any]:
    source_rows: list[dict[str, Any]] = []
    accepted_cells: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    reject_counts: Counter[str] = Counter()
    required_label = required_label_for_role(TARGET_ROLE)
    center_label = _center_label(rows[0], obstacle_distance=obstacle_distance, obstacle_half_width=obstacle_half_width)

    for row in rows:
        candidate = _patched_anchor_candidate(row, obstacle_distance=obstacle_distance, obstacle_half_width=obstacle_half_width)
        scanned = scan_candidate_profile(candidate=candidate)
        label_counts.update({str(key): int(value) for key, value in scanned["label_counts"].items()})
        reject_counts.update({str(key): int(value) for key, value in scanned["reject_counts"].items()})
        support_row = {
            **{field: candidate.get(field, "") for field in REPAIR_METADATA_FIELDS},
            **scanned["profile_support"],
            "post_obstacle_track_width": candidate.get("post_obstacle_track_width", ""),
            "base_geometry_source": candidate.get("base_geometry_source", ""),
            "labels_enter_actor_input": False,
            "v2_ranking_admissible_by_default": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
            "calibrated_base_obstacle_distance": float(obstacle_distance),
            "calibrated_base_obstacle_half_width": float(obstacle_half_width),
            "calibrated_surface_variant": surface,
            "center_label": center_label,
        }
        source_rows.append(support_row)
        for cell in scanned["accepted_cells"]:
            accepted_cells.append(
                {
                    **{field: candidate.get(field, "") for field in REPAIR_METADATA_FIELDS},
                    **cell,
                    "post_obstacle_track_width": candidate.get("post_obstacle_track_width", ""),
                    "calibrated_base_obstacle_distance": float(obstacle_distance),
                    "calibrated_base_obstacle_half_width": float(obstacle_half_width),
                    "calibrated_surface_variant": surface,
                }
            )
        if str(support_row.get("source_support_status", "")) != SUPPORTED:
            blocked_rows.append({field: support_row.get(field, "") for field in BLOCKED_ROW_FIELDS})

    supported = sum(str(row.get("source_support_status", "")) == SUPPORTED for row in source_rows)
    accepted_count = len(accepted_cells)
    distance_from_old = abs(float(obstacle_distance) - OLD_OBSTACLE_DISTANCE) + abs(float(obstacle_half_width) - OLD_OBSTACLE_HALF_WIDTH)
    return {
        "surface_variant": surface,
        "obstacle_distance": float(obstacle_distance),
        "obstacle_half_width": float(obstacle_half_width),
        "base_track_width": DEFAULT_TRACK_WIDTH,
        "required_label": required_label,
        "center_label": center_label,
        "source_row_count": len(source_rows),
        "supported_anchor_count": supported,
        "accepted_cell_count_total": accepted_count,
        "label_correct_source_count": sum(str(row.get("dominant_label", "")) == required_label for row in source_rows),
        "distance_from_old_default": float(distance_from_old),
        "label_counts": dict(sorted(label_counts.items())),
        "reject_reason_counts": dict(sorted(reject_counts.items())),
        "source_rows": source_rows,
        "accepted_cells": accepted_cells,
        "blocked_rows": blocked_rows,
    }


def _candidate_summary(scan: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_variant": scan["surface_variant"],
        "obstacle_distance": scan["obstacle_distance"],
        "obstacle_half_width": scan["obstacle_half_width"],
        "base_track_width": scan["base_track_width"],
        "required_label": scan["required_label"],
        "center_label": scan["center_label"],
        "source_row_count": scan["source_row_count"],
        "supported_anchor_count": scan["supported_anchor_count"],
        "accepted_cell_count_total": scan["accepted_cell_count_total"],
        "label_correct_source_count": scan["label_correct_source_count"],
        "distance_from_old_default": scan["distance_from_old_default"],
        "label_counts": scan["label_counts"],
        "reject_reason_counts": scan["reject_reason_counts"],
    }


def _select_surface_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible = [
        candidate
        for candidate in candidates
        if str(candidate["center_label"]) == TARGET_LABEL and int(candidate["supported_anchor_count"]) >= 16
    ]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda candidate: (
            -int(candidate["supported_anchor_count"]),
            -int(candidate["accepted_cell_count_total"]),
            float(candidate["distance_from_old_default"]),
            float(candidate["obstacle_distance"]),
            float(candidate["obstacle_half_width"]),
        ),
    )[0]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "anchor_fallback_geometry_calibration_completed",
            "admissible": True,
            "reason": "calibration is a no-rollout source-geometry artifact",
        },
        {
            "claim": "source_mining_repaired",
            "admissible": False,
            "reason": "calibrated fallback must be applied in a later source-mining rerun",
        },
        {
            "claim": "reset_validity",
            "admissible": False,
            "reason": "calibration does not reset environments",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "calibration is not a controller comparison",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "calibration is not paper-level evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "calibration does not test history necessity",
        },
    ]


def run_anchor_fallback_geometry_calibration(
    *,
    repair_templates_path: Path | str = DEFAULT_REPAIR_TEMPLATES,
    blocked_rows_path: Path | str = DEFAULT_BLOCKED_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    template_rows = [row for row in _load_templates(repair_templates_path) if _is_anchor_template(row)]
    blocked_anchor_rows = [row for row in _read_csv_rows(blocked_rows_path) if _is_blocked_anchor(row)]

    rows_by_surface: dict[str, list[dict[str, Any]]] = {surface: [] for surface in SURFACE_ORDER}
    for row in template_rows:
        surface = _surface(row)
        if surface in rows_by_surface:
            rows_by_surface[surface].append(row)

    all_candidate_summaries: list[dict[str, Any]] = []
    selected_by_surface: dict[str, dict[str, Any]] = {}
    selected_source_rows: list[dict[str, Any]] = []
    selected_accepted_cells: list[dict[str, Any]] = []
    selected_blocked_rows: list[dict[str, Any]] = []

    for surface in SURFACE_ORDER:
        surface_rows = rows_by_surface[surface]
        surface_candidates: list[dict[str, Any]] = []
        if surface_rows:
            for distance in DISTANCE_GRID:
                for half_width in HALF_WIDTH_GRID:
                    scan = _scan_surface_fallback(
                        rows=surface_rows,
                        surface=surface,
                        obstacle_distance=float(distance),
                        obstacle_half_width=float(half_width),
                    )
                    surface_candidates.append(scan)
                    all_candidate_summaries.append(_candidate_summary(scan))
        selected = _select_surface_candidate(surface_candidates)
        if selected is not None:
            selected_by_surface[surface] = selected
            selected_source_rows.extend(selected["source_rows"])
            selected_accepted_cells.extend(selected["accepted_cells"])
            selected_blocked_rows.extend(selected["blocked_rows"])

    selected_geometry = {
        f"tier_c_boundary_near_miss::stable_aeb::aeb_feasible::{surface}": {
            "speed_ref": 18.0,
            "mu": 0.40,
            "obstacle_distance": selected["obstacle_distance"],
            "obstacle_half_width": selected["obstacle_half_width"],
            "base_track_width": selected["base_track_width"],
            "surface_variant": surface,
            "source_role_semantics": TARGET_ROLE,
            "required_label": selected["required_label"],
            "center_label": selected["center_label"],
            "supported_anchor_count": selected["supported_anchor_count"],
            "accepted_cell_count_total": selected["accepted_cell_count_total"],
            "distance_from_old_default": selected["distance_from_old_default"],
        }
        for surface, selected in selected_by_surface.items()
    }
    selected_surface_count = len(selected_by_surface)
    selected_supported_by_surface = {
        surface: int(selected_by_surface.get(surface, {}).get("supported_anchor_count", 0)) for surface in SURFACE_ORDER
    }
    selected_supported_total = sum(selected_supported_by_surface.values())
    selected_center_labels = {
        surface: str(selected_by_surface.get(surface, {}).get("center_label", "")) for surface in SURFACE_ORDER
    }
    selected_required_labels = {
        surface: str(selected_by_surface.get(surface, {}).get("required_label", "")) for surface in SURFACE_ORDER
    }
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)
    result_passes = (
        len(template_rows) == 64
        and len(blocked_anchor_rows) == 64
        and selected_surface_count == 2
        and set(selected_by_surface) == set(SURFACE_ORDER)
        and all(label == TARGET_LABEL for label in selected_required_labels.values())
        and all(label == TARGET_LABEL for label in selected_center_labels.values())
        and selected_supported_total >= 32
        and all(int(count) >= 16 for count in selected_supported_by_surface.values())
        and len(selected_accepted_cells) > 0
        and guardrail_violation_count == 0
    )

    artifacts = {name: str(output / filename) for name, filename in SUMMARY_ARTIFACTS.items()}
    write_csv_rows(output / "anchor_fallback_candidates.csv", all_candidate_summaries)
    write_csv_rows(output / "anchor_calibration_source_rows.csv", selected_source_rows, fieldnames=[*SOURCE_ROW_FIELDS, "calibrated_base_obstacle_distance", "calibrated_base_obstacle_half_width", "calibrated_surface_variant", "center_label"])
    write_csv_rows(output / "anchor_calibration_accepted_cells.csv", selected_accepted_cells)
    write_csv_rows(output / "anchor_calibration_blocked_rows.csv", selected_blocked_rows, fieldnames=BLOCKED_ROW_FIELDS)
    write_json(output / "selected_anchor_fallback_geometry.json", selected_geometry)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "task_quality_anchor_fallback_geometry_calibration_pass"
            if result_passes
            else "task_quality_anchor_fallback_geometry_calibration_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "repair_templates_path": str(repair_templates_path),
        "blocked_rows_path": str(blocked_rows_path),
        "input_anchor_template_count": len(template_rows),
        "blocked_anchor_row_count": len(blocked_anchor_rows),
        "candidate_fallback_count": len(all_candidate_summaries),
        "selected_surface_count": selected_surface_count,
        "selected_surfaces": sorted(selected_by_surface),
        "target_selected_surfaces": list(SURFACE_ORDER),
        "selected_required_labels": selected_required_labels,
        "selected_center_labels": selected_center_labels,
        "selected_supported_anchor_count_total": selected_supported_total,
        "selected_supported_anchor_count_by_surface": selected_supported_by_surface,
        "selected_accepted_cell_count_total": len(selected_accepted_cells),
        "labels_enter_actor_input_count": 0,
        "profile_specific_tuning_count": 0,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-templates", type=Path, default=DEFAULT_REPAIR_TEMPLATES)
    parser.add_argument("--blocked-rows", type=Path, default=DEFAULT_BLOCKED_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = run_anchor_fallback_geometry_calibration(
        repair_templates_path=args.repair_templates,
        blocked_rows_path=args.blocked_rows,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_anchor_template_count={summary['input_anchor_template_count']}")
    print(f"blocked_anchor_row_count={summary['blocked_anchor_row_count']}")
    print(f"selected_surface_count={summary['selected_surface_count']}")
    print(f"selected_supported_anchor_count_total={summary['selected_supported_anchor_count_total']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
