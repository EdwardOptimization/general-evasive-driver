"""Bounded materialization helper for support-first executable v2 sources."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.executable_v2_task_source_metadata_redesign import CONTRACT_ID


MATERIALIZATION_CONTRACT_ID = "support_first_materialization_v0"
DEFAULT_OUTPUT_DIR = Path("runs/m1861_executable_v2_support_first_materialization")
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
MATERIALIZED_FIELDS = [
    "materialized_v2_panel_spec_id",
    "support_contract_id",
    "materialization_contract_id",
    "candidate_source_id",
    "source_v1_bounded_panel_spec_id",
    "source_scenario_spec_id",
    "source_role_semantics",
    "v2_task_label",
    "profile_name",
    "profile_group",
    "source_family_id",
    "surface_variant",
    "speed_ref",
    "mu",
    "friction_step_enabled",
    "friction_step_at",
    "dt",
    "min_time_after_friction_step",
    "obstacle_distance",
    "obstacle_half_width",
    "threshold_score",
    "cell_selection_kind",
    "labels_enter_actor_input",
    "v2_ranking_admissible_by_default",
    "reset_validation_required",
    "measured_execution_required",
]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"true", "1", "yes", "y"}:
            return True
        if stripped in {"false", "0", "no", "n", ""}:
            return False
    return default


def _float(value: Any, *, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    return float(value)


def _int(value: Any, *, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    return int(float(value))


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _source_key(row: Mapping[str, Any]) -> str:
    return str(row.get("source_v1_bounded_panel_spec_id", row.get("candidate_source_id", "")))


def load_template_rows(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    return [dict(row) for row in payload.get("candidate_sources", [])]


def supported_source_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if str(row.get("source_support_status", "")) == "supported"
        and _bool(row.get("materialization_admissible"))
        and not _bool(row.get("labels_enter_actor_input"))
        and not _bool(row.get("v2_ranking_admissible_by_default"))
    ]


def _round_robin_strata(rows: list[dict[str, Any]], *, cap: int) -> list[dict[str, Any]]:
    strata: dict[tuple[float, float], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        strata[(_float(row.get("speed_ref")), _float(row.get("mu")))].append(row)
    for items in strata.values():
        items.sort(
            key=lambda row: (
                -_int(row.get("source_support_accepted_cell_count_total")),
                str(row.get("candidate_source_id", _source_key(row))),
            )
        )
    selected: list[dict[str, Any]] = []
    keys = sorted(strata)
    while len(selected) < int(cap) and any(strata[key] for key in keys):
        for key in keys:
            if strata[key]:
                selected.append(strata[key].pop(0))
                if len(selected) >= int(cap):
                    break
    return selected


def select_sources(
    *,
    support_rows: Iterable[Mapping[str, Any]],
    template_rows: Iterable[Mapping[str, Any]],
    max_sources_per_role: int = 24,
    max_sources_per_role_surface: int = 12,
) -> list[dict[str, Any]]:
    templates = {_source_key(row): dict(row) for row in template_rows}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in supported_source_rows(support_rows):
        source = _source_key(row)
        template = templates.get(source)
        if template is None:
            continue
        merged = {**template, **dict(row)}
        grouped[(str(merged.get("source_role_semantics", "")), str(merged.get("surface_variant", "")))].append(merged)

    selected: list[dict[str, Any]] = []
    per_role_count: Counter[str] = Counter()
    for (role, _surface), rows in sorted(grouped.items()):
        remaining_role = max(0, int(max_sources_per_role) - int(per_role_count[role]))
        cap = min(int(max_sources_per_role_surface), remaining_role)
        if cap <= 0:
            continue
        chosen = _round_robin_strata(rows, cap=cap)
        selected.extend(chosen)
        per_role_count[role] += len(chosen)
    return sorted(selected, key=lambda row: (str(row["source_role_semantics"]), str(row["surface_variant"]), str(_source_key(row))))


def _cell_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("source_v1_bounded_panel_spec_id", "")),
        str(row.get("obstacle_distance", "")),
        str(row.get("obstacle_half_width", "")),
    )


def select_cells_for_source(
    *,
    source_row: Mapping[str, Any],
    accepted_cells: Iterable[Mapping[str, Any]],
    max_cells_per_source: int = 2,
) -> list[dict[str, Any]]:
    source = _source_key(source_row)
    cells = [dict(row) for row in accepted_cells if _source_key(row) == source]
    if not cells:
        return []
    boundary = min(
        cells,
        key=lambda row: (
            _float(row.get("threshold_score")),
            _float(row.get("obstacle_distance")),
            -_float(row.get("obstacle_half_width")),
        ),
    )
    distances = sorted(_float(row.get("obstacle_distance")) for row in cells)
    median_distance = median(distances)
    representative_candidates = [row for row in cells if _cell_key(row) != _cell_key(boundary)] or cells
    representative = min(
        representative_candidates,
        key=lambda row: (
            abs(_float(row.get("obstacle_distance")) - median_distance),
            _float(row.get("threshold_score")),
            _float(row.get("obstacle_half_width")),
        ),
    )
    selected: list[dict[str, Any]] = []
    for kind, row in (("boundary_min_threshold", boundary), ("representative_median_distance", representative)):
        candidate = {**dict(row), "cell_selection_kind": kind}
        if _cell_key(candidate) not in {_cell_key(item) for item in selected}:
            selected.append(candidate)
        if len(selected) >= int(max_cells_per_source):
            break
    return selected


def _env_config(*, source_row: Mapping[str, Any], cell: Mapping[str, Any]) -> dict[str, Any]:
    speed = _float(source_row.get("speed_ref"))
    mu = _float(source_row.get("mu"))
    label = str(source_row.get("source_required_label", source_row.get("v2_task_label", "")))
    friction_enabled = _bool(source_row.get("friction_step_enabled"))
    friction_step_at = _int(source_row.get("friction_step_at"), default=20)
    return {
        "track_kind": "circle",
        "track_radius": 18.0,
        "speed_range": [speed, speed],
        "friction_limited_speed": False,
        "randomization": {
            "mu_range": [mu, mu],
            "mass_scale_range": [1.0, 1.0],
            "cg_shift_range": [0.0, 0.0],
            "inertia_scale_range": [1.0, 1.0],
            "tire_stiffness_scale_range": [1.0, 1.0],
            "drive_scale_range": [1.0, 1.0],
            "brake_scale_range": [1.0, 1.0],
            "actuator_tau_scale_range": [1.0, 1.0],
        },
        "friction_step": {
            "enabled": friction_enabled,
            "step_range": [friction_step_at, friction_step_at],
            "mu_range": [mu, mu],
            "resample_speed_ref": False,
        },
        "obstacle": {
            "enabled": True,
            "allowed_labels": [label],
            "require_aeb_infeasible": _bool(source_row.get("require_aeb_infeasible")),
            "distance_range": [_float(cell.get("obstacle_distance")), _float(cell.get("obstacle_distance"))],
            "half_width_range": [_float(cell.get("obstacle_half_width")), _float(cell.get("obstacle_half_width"))],
            "ego_half_width": _float(source_row.get("ego_half_width"), default=0.90),
            "safety_margin": _float(source_row.get("safety_margin"), default=0.30),
            "brake_mu_fraction": _float(source_row.get("brake_mu_fraction"), default=0.90),
            "conventional_lateral_mu_fraction": _float(
                source_row.get("conventional_lateral_mu_fraction"), default=0.42
            ),
            "drift_lateral_mu_fraction": _float(source_row.get("drift_lateral_mu_fraction"), default=0.85),
            "min_time_after_friction_step": _float(source_row.get("min_time_after_friction_step")),
            "max_sample_attempts": 1,
        },
    }


def build_materialized_row(
    *,
    source_row: Mapping[str, Any],
    cell: Mapping[str, Any],
    index: int,
) -> dict[str, Any]:
    source = _source_key(source_row)
    label = str(source_row.get("source_required_label", ""))
    kind = str(cell.get("cell_selection_kind", "cell"))
    row = {
        "materialized_v2_panel_spec_id": f"sfm_mat_v0_{index:04d}_{kind}_{source}",
        "support_contract_id": CONTRACT_ID,
        "materialization_contract_id": MATERIALIZATION_CONTRACT_ID,
        "candidate_source_id": source_row.get("candidate_source_id", source),
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": source_row.get("source_scenario_spec_id", ""),
        "source_role_semantics": source_row.get("source_role_semantics", ""),
        "v2_task_label": label,
        "profile_name": source_row.get("profile_name", ""),
        "profile_group": source_row.get("profile_group", ""),
        "source_family_id": source_row.get("source_family_id", ""),
        "surface_variant": source_row.get("surface_variant", ""),
        "speed_ref": _float(source_row.get("speed_ref")),
        "mu": _float(source_row.get("mu")),
        "friction_step_enabled": _bool(source_row.get("friction_step_enabled")),
        "friction_step_at": source_row.get("friction_step_at", ""),
        "dt": _float(source_row.get("dt"), default=0.05),
        "min_time_after_friction_step": _float(source_row.get("min_time_after_friction_step")),
        "obstacle_distance": _float(cell.get("obstacle_distance")),
        "obstacle_half_width": _float(cell.get("obstacle_half_width")),
        "threshold_score": _float(cell.get("threshold_score")),
        "cell_selection_kind": kind,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "reset_validation_required": True,
        "measured_execution_required": False,
    }
    row["env_config"] = _env_config(source_row=source_row, cell=cell)
    return row


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "support_first_materialization_helper",
            "admissible": True,
            "reason": "helper implementation can create bounded materialization artifacts",
        },
        {
            "claim": "project_materialization_execution_result",
            "admissible": False,
            "reason": "project materialization requires a later execution milestone",
        },
        {
            "claim": "reset_feasibility",
            "admissible": False,
            "reason": "materialization does not reset the environment",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "materialization is task-quality infrastructure, not ranking evidence",
        },
    ]


def run_support_first_materialization(
    *,
    support_rows: list[Mapping[str, Any]],
    accepted_cells: list[Mapping[str, Any]],
    template_rows: list[Mapping[str, Any]],
    output_dir: Path | str,
    max_sources_per_role: int = 24,
    max_sources_per_role_surface: int = 12,
    max_cells_per_source: int = 2,
    next_blocker: str = "m1860-executable-v2-support-first-materialization-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    selected_sources = select_sources(
        support_rows=support_rows,
        template_rows=template_rows,
        max_sources_per_role=max_sources_per_role,
        max_sources_per_role_surface=max_sources_per_role_surface,
    )
    selected_cells: list[dict[str, Any]] = []
    materialized_rows: list[dict[str, Any]] = []
    for source in selected_sources:
        cells = select_cells_for_source(
            source_row=source,
            accepted_cells=accepted_cells,
            max_cells_per_source=max_cells_per_source,
        )
        selected_cells.extend(cells)
        for cell in cells:
            materialized_rows.append(build_materialized_row(source_row=source, cell=cell, index=len(materialized_rows)))

    duplicate_ids = [
        item for item, count in Counter(str(row["materialized_v2_panel_spec_id"]) for row in materialized_rows).items()
        if count > 1
    ]
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    role_counts = dict(sorted(Counter(str(row["source_role_semantics"]) for row in materialized_rows).items()))
    surface_counts = dict(sorted(Counter(str(row["surface_variant"]) for row in materialized_rows).items()))
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in materialized_rows)
    ranking_count = sum(_bool(row.get("v2_ranking_admissible_by_default")) for row in materialized_rows)

    matrix_rows = [
        {
            "materialized_v2_panel_spec_id": row["materialized_v2_panel_spec_id"],
            "candidate_source_id": row["candidate_source_id"],
            "source_role_semantics": row["source_role_semantics"],
            "cell_selection_kind": row["cell_selection_kind"],
            "reset_validation_required": row["reset_validation_required"],
        }
        for row in materialized_rows
    ]
    json_specs = {"executable_v2_panel_specs": materialized_rows}

    write_csv_rows(output / "support_first_materialized_source_selection.csv", selected_sources)
    write_csv_rows(output / "support_first_materialized_cell_selection.csv", selected_cells)
    write_csv_rows(
        output / "support_first_materialized_executable_v2_panel_specs.csv",
        materialized_rows,
        fieldnames=[*MATERIALIZED_FIELDS, "env_config"],
    )
    write_json(output / "support_first_materialized_executable_v2_panel_specs.json", json_specs)
    write_csv_rows(output / "support_first_materialization_matrix.csv", matrix_rows)
    write_csv_rows(output / "support_first_materialization_blocked_sources.csv", [])
    write_csv_rows(output / "support_first_materialization_duplicate_keys.csv", [{"key": key} for key in duplicate_ids])
    write_csv_rows(output / "support_first_materialization_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "contract_id": MATERIALIZATION_CONTRACT_ID,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "input_supported_source_count": len(supported_source_rows(support_rows)),
        "selected_source_count": len(selected_sources),
        "selected_cell_count": len(selected_cells),
        "materialized_spec_count": len(materialized_rows),
        "materialization_matrix_row_count": len(matrix_rows),
        "max_sources_per_role": int(max_sources_per_role),
        "max_sources_per_role_surface": int(max_sources_per_role_surface),
        "max_cells_per_source": int(max_cells_per_source),
        "role_counts": role_counts,
        "surface_counts": surface_counts,
        "speed_count": len({float(row["speed_ref"]) for row in materialized_rows}),
        "mu_count": len({float(row["mu"]) for row in materialized_rows}),
        "duplicate_key_count": len(duplicate_ids),
        "labels_enter_actor_input_count": int(labels_enter_actor_input_count),
        "ranking_admissible_by_default_count": int(ranking_count),
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
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "source_selection": str(output / "support_first_materialized_source_selection.csv"),
            "cell_selection": str(output / "support_first_materialized_cell_selection.csv"),
            "panel_specs_csv": str(output / "support_first_materialized_executable_v2_panel_specs.csv"),
            "panel_specs_json": str(output / "support_first_materialized_executable_v2_panel_specs.json"),
            "matrix": str(output / "support_first_materialization_matrix.csv"),
            "blocked_sources": str(output / "support_first_materialization_blocked_sources.csv"),
            "duplicate_keys": str(output / "support_first_materialization_duplicate_keys.csv"),
            "claim_boundary": str(output / "support_first_materialization_claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def run_support_first_materialization_from_paths(
    *,
    support_rows_path: Path | str,
    accepted_cells_path: Path | str,
    template_path: Path | str,
    output_dir: Path | str,
    max_sources_per_role: int = 24,
    max_sources_per_role_surface: int = 12,
    max_cells_per_source: int = 2,
    next_blocker: str = "m1860-executable-v2-support-first-materialization-execution-design",
) -> dict[str, Any]:
    return run_support_first_materialization(
        support_rows=_read_csv_rows(support_rows_path),
        accepted_cells=_read_csv_rows(accepted_cells_path),
        template_rows=load_template_rows(template_path),
        output_dir=output_dir,
        max_sources_per_role=max_sources_per_role,
        max_sources_per_role_surface=max_sources_per_role_surface,
        max_cells_per_source=max_cells_per_source,
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-rows", type=Path, required=True)
    parser.add_argument("--accepted-cells", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-sources-per-role", type=int, default=24)
    parser.add_argument("--max-sources-per-role-surface", type=int, default=12)
    parser.add_argument("--max-cells-per-source", type=int, default=2)
    parser.add_argument("--next-blocker", default="m1860-executable-v2-support-first-materialization-execution-design")
    args = parser.parse_args()
    summary = run_support_first_materialization_from_paths(
        support_rows_path=args.support_rows,
        accepted_cells_path=args.accepted_cells,
        template_path=args.template,
        output_dir=args.output_dir,
        max_sources_per_role=args.max_sources_per_role,
        max_sources_per_role_surface=args.max_sources_per_role_surface,
        max_cells_per_source=args.max_cells_per_source,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"contract_id={summary['contract_id']}")
    print(f"selected_source_count={summary['selected_source_count']}")
    print(f"materialized_spec_count={summary['materialized_spec_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
