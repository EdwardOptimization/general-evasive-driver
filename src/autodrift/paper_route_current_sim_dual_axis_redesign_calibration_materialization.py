"""Artifact-only dual-axis redesign calibration materializer."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json


DEFAULT_INPUT_DIR = Path("runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation")
DEFAULT_CONFIG = Path("configs/paper_route_current_sim_scenario_task_family_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization")
DEFAULT_TARGET_REDESIGN_ROW_COUNT = 26
DEFAULT_TARGET_GEOMETRY_ROW_COUNT = 13
DEFAULT_TARGET_HIDDEN_ROW_COUNT = 13
DEFAULT_TARGET_SECONDARY_COVERAGE_ROW_COUNT = 9
DEFAULT_NEXT_BLOCKER = "m2348-paper-route-current-sim-dual-axis-redesign-calibration-materialization-result-audit"

ACTOR_CONTRACT_ID = "P0_human_view_no_wheel_no_oracle"
GEOMETRY_ROUTE = "geometry_timing_rebalance_candidate"
HIDDEN_ROUTE = "hidden_dynamics_range_rebalance_candidate"
STRESS_HIDDEN_BUCKETS = {"low_mu", "weak_brake", "slow_steer_actuator", "tire_stiffness_shift"}

CANDIDATE_FIELDNAMES = [
    "scenario_spec_id",
    "candidate_id",
    "candidate_axis",
    "source_recommended_route",
    "role_family",
    "scenario_family_id",
    "same_scene_group_id",
    "hidden_dynamics_bucket_before",
    "hidden_dynamics_bucket_after",
    "timing_bucket_before",
    "timing_bucket_after",
    "lateral_bucket_before",
    "lateral_bucket_after",
    "initial_speed_mps_before",
    "initial_speed_mps_after",
    "track_width_m_before",
    "track_width_m_after",
    "track_radius_m_before",
    "track_radius_m_after",
    "transform_name",
    "transform_reason",
    "combined_candidate_reason",
    "active_for_materialization",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]

SECONDARY_FIELDNAMES = [
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "sampled_obstacle_label",
    "same_scene_group_id",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "initial_speed_mps",
    "track_radius_m",
    "track_width_m",
    "actor_contract_id",
    "recommended_next_route",
    "active_for_calibration",
    "blocked_by",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]

CLAIM_FIELDNAMES = ["claim", "allowed", "made", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_scenario_specs(config_path: Path | str) -> list[dict[str, Any]]:
    payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
    specs = payload.get("scenario_specs")
    if not isinstance(specs, list):
        raise ValueError("scenario task-family config must contain scenario_specs")
    return [dict(spec) for spec in specs]


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _float_value(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _format_number(value: float | str | None) -> Any:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return int(value) if float(value).is_integer() else round(float(value), 6)


class ReferenceBuckets:
    def __init__(self, specs: Sequence[Mapping[str, Any]]) -> None:
        self.speeds_by_role: dict[str, list[float]] = {}
        self.widths_by_role: dict[str, list[float]] = {}
        self.radii_by_role: dict[str, list[float]] = {}
        role_groups: dict[str, list[Mapping[str, Any]]] = {}
        for spec in specs:
            role_groups.setdefault(str(spec.get("role_family", "")), []).append(spec)
        for role, rows in role_groups.items():
            self.speeds_by_role[role] = sorted(
                {value for value in (_float_value(row.get("initial_speed_mps")) for row in rows) if value is not None}
            )
            self.widths_by_role[role] = sorted(
                {value for value in (_float_value(row.get("track_width_m")) for row in rows) if value is not None}
            )
            self.radii_by_role[role] = sorted(
                {value for value in (_float_value(row.get("track_radius_m")) for row in rows) if value is not None}
            )

    def previous_speed(self, role: str, current: Any) -> float | None:
        value = _float_value(current)
        if value is None:
            return None
        lower = [candidate for candidate in self.speeds_by_role.get(role, []) if candidate < value]
        return lower[-1] if lower else None

    def next_width(self, role: str, current: Any) -> float | None:
        value = _float_value(current)
        if value is None:
            return None
        higher = [candidate for candidate in self.widths_by_role.get(role, []) if candidate > value]
        return higher[0] if higher else None

    def next_radius(self, role: str, current: Any) -> float | None:
        value = _float_value(current)
        if value is None:
            return None
        higher = [candidate for candidate in self.radii_by_role.get(role, []) if candidate > value]
        return higher[0] if higher else None


def _candidate_base(
    row: Mapping[str, Any],
    *,
    axis: str,
    transform_name: str,
    transform_reason: str,
    combined_candidate_reason: str = "",
) -> dict[str, Any]:
    return {
        "scenario_spec_id": row.get("scenario_spec_id", ""),
        "candidate_id": "",
        "candidate_axis": axis,
        "source_recommended_route": row.get("recommended_redesign_route", ""),
        "role_family": row.get("role_family", ""),
        "scenario_family_id": row.get("scenario_family_id", ""),
        "same_scene_group_id": row.get("same_scene_group_id", ""),
        "hidden_dynamics_bucket_before": row.get("hidden_dynamics_bucket", ""),
        "hidden_dynamics_bucket_after": row.get("hidden_dynamics_bucket", ""),
        "timing_bucket_before": row.get("obstacle_longitudinal_timing_bucket", ""),
        "timing_bucket_after": row.get("obstacle_longitudinal_timing_bucket", ""),
        "lateral_bucket_before": row.get("obstacle_lateral_offset_bucket", ""),
        "lateral_bucket_after": row.get("obstacle_lateral_offset_bucket", ""),
        "initial_speed_mps_before": row.get("initial_speed_mps", ""),
        "initial_speed_mps_after": row.get("initial_speed_mps", ""),
        "track_width_m_before": row.get("track_width_m", ""),
        "track_width_m_after": row.get("track_width_m", ""),
        "track_radius_m_before": row.get("track_radius_m", ""),
        "track_radius_m_after": row.get("track_radius_m", ""),
        "transform_name": transform_name,
        "transform_reason": transform_reason,
        "combined_candidate_reason": combined_candidate_reason,
        "active_for_materialization": True,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def geometry_candidates(row: Mapping[str, Any], reference: ReferenceBuckets) -> list[dict[str, Any]]:
    role = str(row.get("role_family", ""))
    timing = str(row.get("obstacle_longitudinal_timing_bucket", ""))
    lateral = str(row.get("obstacle_lateral_offset_bucket", ""))
    failure = str(row.get("dominant_failure_mode", ""))
    theme = str(row.get("redesign_theme", ""))
    candidates: list[dict[str, Any]] = []

    if timing == "late_close":
        candidate = _candidate_base(
            row,
            axis="G",
            transform_name="timing_step_earlier",
            transform_reason="late_close row receives a one-bucket earlier timing candidate",
        )
        candidate["timing_bucket_after"] = "mid"
        candidates.append(candidate)
    elif timing == "mid" and failure == "collision_dominated_failure" and lateral == "centerline":
        candidate = _candidate_base(
            row,
            axis="G",
            transform_name="timing_step_earlier",
            transform_reason="mid centerline collision row receives an early_far timing candidate",
        )
        candidate["timing_bucket_after"] = "early_far"
        candidates.append(candidate)

    if lateral in {"left_offset", "right_offset"}:
        candidate = _candidate_base(
            row,
            axis="G",
            transform_name="lateral_offset_step_toward_centerline",
            transform_reason="lateral-offset row receives a centerline-neighbor candidate",
        )
        candidate["lateral_bucket_after"] = "centerline"
        candidates.append(candidate)

    lower_speed = reference.previous_speed(role, row.get("initial_speed_mps"))
    if lower_speed is not None and (theme == "collision_timing_pressure" or timing == "late_close"):
        candidate = _candidate_base(
            row,
            axis="G",
            transform_name="speed_step_down",
            transform_reason="collision/timing pressure row receives one existing-pack lower speed candidate",
        )
        candidate["initial_speed_mps_after"] = _format_number(lower_speed)
        candidates.append(candidate)

    wider = reference.next_width(role, row.get("track_width_m"))
    if wider is not None and (theme == "offtrack_geometry_pressure" or failure == "offtrack_dominated_failure"):
        candidate = _candidate_base(
            row,
            axis="G",
            transform_name="track_width_step_up",
            transform_reason="offtrack pressure row receives the next existing broader track-width candidate",
        )
        candidate["track_width_m_after"] = _format_number(wider)
        candidates.append(candidate)

    larger_radius = reference.next_radius(role, row.get("track_radius_m"))
    if larger_radius is not None and theme == "offtrack_geometry_pressure":
        candidate = _candidate_base(
            row,
            axis="G",
            transform_name="radius_step_up",
            transform_reason="offtrack pressure row receives the next existing larger-radius candidate",
        )
        candidate["track_radius_m_after"] = _format_number(larger_radius)
        candidates.append(candidate)

    return candidates


def hidden_candidates(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    hidden = str(row.get("hidden_dynamics_bucket", ""))
    transform_by_hidden = {
        "low_mu": ("low_mu_step_toward_nominal", "nominal_neighbor"),
        "weak_brake": ("weak_brake_step_toward_nominal", "nominal_neighbor"),
        "slow_steer_actuator": ("slow_steer_actuator_step_toward_nominal", "nominal_neighbor"),
        "tire_stiffness_shift": ("tire_stiffness_step_toward_nominal", "nominal_neighbor"),
    }
    if hidden in transform_by_hidden:
        transform_name, hidden_after = transform_by_hidden[hidden]
        candidate = _candidate_base(
            row,
            axis="H",
            transform_name=transform_name,
            transform_reason="stress hidden-dynamics bucket receives a one-step range calibration candidate",
        )
        candidate["hidden_dynamics_bucket_after"] = hidden_after
        return [candidate]

    if str(row.get("role_family", "")).startswith("R5_"):
        candidate = _candidate_base(
            row,
            axis="H",
            transform_name="same_scene_hidden_balance",
            transform_reason="R5 same-scene hidden-dynamics row receives a balanced-panel metadata candidate",
        )
        candidate["hidden_dynamics_bucket_after"] = "same_scene_balanced_panel"
        return [candidate]

    return []


def _gh_eligible(row: Mapping[str, Any]) -> bool:
    route = str(row.get("recommended_redesign_route", ""))
    hidden = str(row.get("hidden_dynamics_bucket", ""))
    timing = str(row.get("obstacle_longitudinal_timing_bucket", ""))
    theme = str(row.get("redesign_theme", ""))
    failure = str(row.get("dominant_failure_mode", ""))
    if route == GEOMETRY_ROUTE:
        return hidden in STRESS_HIDDEN_BUCKETS and theme in {"collision_timing_pressure", "offtrack_geometry_pressure"}
    return route == HIDDEN_ROUTE and timing == "late_close" and failure == "collision_dominated_failure"


def combined_candidate(row: Mapping[str, Any], reference: ReferenceBuckets) -> dict[str, Any] | None:
    if not _gh_eligible(row):
        return None
    g_candidates = geometry_candidates(row, reference)
    h_candidates = hidden_candidates(row)
    if not g_candidates or not h_candidates:
        return None
    candidate = dict(g_candidates[0])
    hidden = h_candidates[0]
    candidate["candidate_axis"] = "GH"
    candidate["transform_name"] = f"{candidate['transform_name']}+{hidden['transform_name']}"
    candidate["transform_reason"] = "minimal combined one-step geometry/timing and hidden-range candidate"
    candidate["hidden_dynamics_bucket_after"] = hidden["hidden_dynamics_bucket_after"]
    candidate["combined_candidate_reason"] = "row carries both geometry/timing and hidden-dynamics stress signals"
    return candidate


def assign_candidate_ids(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    scenario_counts: Counter[str] = Counter()
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        row = dict(candidate)
        scenario_id = str(row.get("scenario_spec_id", ""))
        scenario_counts[scenario_id] += 1
        row["candidate_id"] = f"{scenario_id}::{row.get('candidate_axis', '')}{scenario_counts[scenario_id]:02d}"
        output.append(row)
    return output


def build_candidates(
    rows: Sequence[Mapping[str, Any]],
    *,
    reference: ReferenceBuckets,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    geometry: list[dict[str, Any]] = []
    hidden: list[dict[str, Any]] = []
    combined: list[dict[str, Any]] = []
    for row in rows:
        route = str(row.get("recommended_redesign_route", ""))
        if route == GEOMETRY_ROUTE:
            geometry.extend(geometry_candidates(row, reference))
        elif route == HIDDEN_ROUTE:
            hidden.extend(hidden_candidates(row))
        gh = combined_candidate(row, reference)
        if gh is not None:
            combined.append(gh)
    all_candidates = assign_candidate_ids([*geometry, *hidden, *combined])
    geometry_ids = {id(candidate) for candidate in geometry}
    hidden_ids = {id(candidate) for candidate in hidden}
    combined_ids = {id(candidate) for candidate in combined}
    assigned_geometry = [candidate for original, candidate in zip([*geometry, *hidden, *combined], all_candidates) if id(original) in geometry_ids]
    assigned_hidden = [candidate for original, candidate in zip([*geometry, *hidden, *combined], all_candidates) if id(original) in hidden_ids]
    assigned_combined = [candidate for original, candidate in zip([*geometry, *hidden, *combined], all_candidates) if id(original) in combined_ids]
    return all_candidates, assigned_geometry, assigned_hidden, assigned_combined


def secondary_coverage_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        output.append(
            {
                "scenario_spec_id": row.get("scenario_spec_id", ""),
                "scenario_family_id": row.get("scenario_family_id", ""),
                "role_family": row.get("role_family", ""),
                "sampled_obstacle_label": row.get("sampled_obstacle_label", ""),
                "same_scene_group_id": row.get("same_scene_group_id", ""),
                "hidden_dynamics_bucket": row.get("hidden_dynamics_bucket", ""),
                "obstacle_longitudinal_timing_bucket": row.get("obstacle_longitudinal_timing_bucket", ""),
                "obstacle_lateral_offset_bucket": row.get("obstacle_lateral_offset_bucket", ""),
                "initial_speed_mps": row.get("initial_speed_mps", ""),
                "track_radius_m": row.get("track_radius_m", ""),
                "track_width_m": row.get("track_width_m", ""),
                "actor_contract_id": row.get("actor_contract_id", ""),
                "recommended_next_route": row.get("recommended_next_route", ""),
                "active_for_calibration": False,
                "blocked_by": "dual_axis_redesign_calibration_not_materialized",
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
            }
        )
    return output


def calibration_config_candidates(candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "claim_scope": "artifact_only_candidate_patch_plan",
        "active_config_overwritten": False,
        "candidate_count": len(candidates),
        "candidates": [
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "source_scenario_spec_id": candidate.get("scenario_spec_id", ""),
                "candidate_axis": candidate.get("candidate_axis", ""),
                "transform_name": candidate.get("transform_name", ""),
                "patch_metadata": {
                    "hidden_dynamics_bucket": candidate.get("hidden_dynamics_bucket_after", ""),
                    "obstacle_longitudinal_timing_bucket": candidate.get("timing_bucket_after", ""),
                    "obstacle_lateral_offset_bucket": candidate.get("lateral_bucket_after", ""),
                    "initial_speed_mps": candidate.get("initial_speed_mps_after", ""),
                    "track_width_m": candidate.get("track_width_m_after", ""),
                    "track_radius_m": candidate.get("track_radius_m_after", ""),
                },
                "diagnostic_only": True,
                "ranking_admissible": False,
                "scenario_redesign_executed": False,
            }
            for candidate in candidates
        ],
    }


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_dual_axis_calibration_materialization",
            "allowed": True,
            "made": True,
            "reason": "M2347 only materializes candidate artifacts from M2346 design.",
        },
        {
            "claim": "scenario_redesign_executed",
            "allowed": False,
            "made": False,
            "reason": "The active scenario config is not overwritten and no rollout is run.",
        },
        {
            "claim": "support_policy_ranking",
            "allowed": False,
            "made": False,
            "reason": "Secondary coverage rows are tracked inactive and no support policies are compared.",
        },
        {
            "claim": "controller_family_ranking",
            "allowed": False,
            "made": False,
            "reason": "Candidate materialization is not controller evaluation.",
        },
        {
            "claim": "paper_level_evidence",
            "allowed": False,
            "made": False,
            "reason": "No validation, holdout, or controller comparison is produced.",
        },
        {
            "claim": "level3_self_identification",
            "allowed": False,
            "made": False,
            "reason": "No history intervention or self-ID test is run.",
        },
    ]


def _guardrail_violation_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(
        int(_bool_value(row.get("ranking_admissible", False)))
        + int(_bool_value(row.get("winner_selected", False)))
        + int(_bool_value(row.get("paper_level_claim_made", False)))
        + int(_bool_value(row.get("level3_self_id_claim_made", False)))
        for row in rows
    )


def run_dual_axis_redesign_calibration_materialization(
    *,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
    config: Path | str = DEFAULT_CONFIG,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_redesign_row_count: int = DEFAULT_TARGET_REDESIGN_ROW_COUNT,
    target_geometry_row_count: int = DEFAULT_TARGET_GEOMETRY_ROW_COUNT,
    target_hidden_row_count: int = DEFAULT_TARGET_HIDDEN_ROW_COUNT,
    target_secondary_coverage_row_count: int = DEFAULT_TARGET_SECONDARY_COVERAGE_ROW_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    input_path = Path(input_dir)
    config_path = Path(config)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rows = read_csv_rows(input_path / "consolidated_redesign_rows.csv")
    secondary_source = read_csv_rows(input_path / "secondary_coverage_materialization_rows.csv")
    specs = load_scenario_specs(config_path)
    reference = ReferenceBuckets(specs)

    all_candidates, geometry, hidden, combined = build_candidates(rows, reference=reference)
    secondary = secondary_coverage_rows(secondary_source)
    claims = claim_boundary_rows()

    write_csv_rows(output / "calibration_candidate_rows.csv", all_candidates, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(output / "geometry_timing_candidate_rows.csv", geometry, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(output / "hidden_range_candidate_rows.csv", hidden, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(output / "combined_axis_candidate_rows.csv", combined, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(output / "secondary_coverage_rows.csv", secondary, fieldnames=SECONDARY_FIELDNAMES)
    write_json(output / "calibration_config_candidates.json", calibration_config_candidates(all_candidates))
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)

    route_counts = Counter(str(row.get("recommended_redesign_route", "")) for row in rows)
    rows_with_candidates = {str(candidate.get("scenario_spec_id", "")) for candidate in all_candidates}
    rows_without_candidate_count = sum(1 for row in rows if str(row.get("scenario_spec_id", "")) not in rows_with_candidates)
    actor_contract_violation_count = sum(
        1 for row in rows if str(row.get("actor_contract_id", "")) != ACTOR_CONTRACT_ID
    )
    inactive_secondary_violation_count = sum(_bool_value(row.get("active_for_calibration", False)) for row in secondary)
    candidate_guardrails = _guardrail_violation_count(all_candidates)
    secondary_guardrails = _guardrail_violation_count(secondary)
    claim_guardrails = sum(
        1 for claim in claims if not _bool_value(claim.get("allowed", False)) and _bool_value(claim.get("made", False))
    )
    guardrail_violation_count = (
        actor_contract_violation_count
        + inactive_secondary_violation_count
        + candidate_guardrails
        + secondary_guardrails
        + claim_guardrails
    )
    result_passes = (
        len(rows) == int(target_redesign_row_count)
        and route_counts[GEOMETRY_ROUTE] == int(target_geometry_row_count)
        and route_counts[HIDDEN_ROUTE] == int(target_hidden_row_count)
        and len(secondary_source) == int(target_secondary_coverage_row_count)
        and len(secondary) == int(target_secondary_coverage_row_count)
        and rows_without_candidate_count == 0
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_dual_axis_redesign_calibration_materialization_pass"
            if result_passes
            else "current_sim_dual_axis_redesign_calibration_materialization_incomplete_or_fail"
        ),
        "input_dir": str(input_path),
        "config": str(config_path),
        "output_dir": str(output),
        "input_redesign_row_count": len(rows),
        "target_redesign_row_count": int(target_redesign_row_count),
        "geometry_timing_input_row_count": route_counts[GEOMETRY_ROUTE],
        "target_geometry_timing_input_row_count": int(target_geometry_row_count),
        "hidden_range_input_row_count": route_counts[HIDDEN_ROUTE],
        "target_hidden_range_input_row_count": int(target_hidden_row_count),
        "secondary_coverage_input_row_count": len(secondary_source),
        "target_secondary_coverage_input_row_count": int(target_secondary_coverage_row_count),
        "geometry_timing_candidate_count": len(geometry),
        "hidden_range_candidate_count": len(hidden),
        "combined_axis_candidate_count": len(combined),
        "calibration_candidate_count": len(all_candidates),
        "secondary_coverage_tracked_count": len(secondary),
        "rows_without_candidate_count": rows_without_candidate_count,
        "actor_contract_violation_count": actor_contract_violation_count,
        "inactive_secondary_violation_count": inactive_secondary_violation_count,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "support_policy_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "residual_support_solved_claim_made": False,
        "controller_comparison_ready_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "artifacts": {
            "calibration_candidate_rows": str(output / "calibration_candidate_rows.csv"),
            "geometry_timing_candidate_rows": str(output / "geometry_timing_candidate_rows.csv"),
            "hidden_range_candidate_rows": str(output / "hidden_range_candidate_rows.csv"),
            "combined_axis_candidate_rows": str(output / "combined_axis_candidate_rows.csv"),
            "secondary_coverage_rows": str(output / "secondary_coverage_rows.csv"),
            "calibration_config_candidates": str(output / "calibration_config_candidates.json"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "summary": str(output / "summary.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-redesign-row-count", type=int, default=DEFAULT_TARGET_REDESIGN_ROW_COUNT)
    parser.add_argument("--target-geometry-row-count", type=int, default=DEFAULT_TARGET_GEOMETRY_ROW_COUNT)
    parser.add_argument("--target-hidden-row-count", type=int, default=DEFAULT_TARGET_HIDDEN_ROW_COUNT)
    parser.add_argument(
        "--target-secondary-coverage-row-count",
        type=int,
        default=DEFAULT_TARGET_SECONDARY_COVERAGE_ROW_COUNT,
    )
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_dual_axis_redesign_calibration_materialization(
        input_dir=args.input_dir,
        config=args.config,
        output_dir=args.output_dir,
        target_redesign_row_count=int(args.target_redesign_row_count),
        target_geometry_row_count=int(args.target_geometry_row_count),
        target_hidden_row_count=int(args.target_hidden_row_count),
        target_secondary_coverage_row_count=int(args.target_secondary_coverage_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_redesign_row_count={summary['input_redesign_row_count']}")
    print(f"geometry_timing_input_row_count={summary['geometry_timing_input_row_count']}")
    print(f"hidden_range_input_row_count={summary['hidden_range_input_row_count']}")
    print(f"secondary_coverage_tracked_count={summary['secondary_coverage_tracked_count']}")
    print(f"rows_without_candidate_count={summary['rows_without_candidate_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
