"""No-rollout adapter for support-first repaired measured smoke workloads."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config


DEFAULT_REPAIR_MATRIX = Path(
    "runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/"
    "repair_variant_matrix.csv"
)
DEFAULT_MEASURED_EXECUTABLE_SPECS = Path(
    "runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/"
    "support_first_measured_executable_specs.json"
)
DEFAULT_EPISODE_ROWS = Path("runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1887_executable_v2_support_first_repaired_runner_adapter")

IMPORT_VARIANTS = ("original", "semantics_only")
ROLLOUT_VARIANTS = ("finish_extended", "road_relaxed", "road_relaxed_finish_extended")
ALLOWED_DELTA_KEYS = {
    "success_semantics",
    "max_steps_multiplier",
    "track_width_multiplier",
    "offtrack_overshoot_tolerance_m",
    "finish_rule",
}
DEFAULT_TRACK_WIDTH = 5.0
DEFAULT_MAX_STEPS = 800
DEFAULT_SOURCES_PER_ROLE_SURFACE = 2
TARGET_ROLE_SURFACE_COUNT = 8
TARGET_CONTROLLER_PROFILE_COUNT = 12
TARGET_SELECTED_SOURCE_SPEC_COUNT = 16
TARGET_EXECUTABLE_SPEC_COUNT = TARGET_SELECTED_SOURCE_SPEC_COUNT * len(ROLLOUT_VARIANTS)
TARGET_ROLLOUT_WORKLOAD_CELL_COUNT = TARGET_SELECTED_SOURCE_SPEC_COUNT * TARGET_CONTROLLER_PROFILE_COUNT * len(
    ROLLOUT_VARIANTS
)
TARGET_IMPORT_ROW_COUNT = TARGET_SELECTED_SOURCE_SPEC_COUNT * TARGET_CONTROLLER_PROFILE_COUNT * len(IMPORT_VARIANTS)
TARGET_TOTAL_PANEL_ROW_COUNT = TARGET_ROLLOUT_WORKLOAD_CELL_COUNT + TARGET_IMPORT_ROW_COUNT

FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "measured_rollout_started",
    "policy_action_executed",
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


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "nan", "none"}:
        return False
    return default


def _json_string(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _unique_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return len({str(row.get(key, "")) for row in rows})


def load_repair_matrix(path: Path | str = DEFAULT_REPAIR_MATRIX) -> list[dict[str, str]]:
    return _read_csv_rows(path)


def load_measured_specs(path: Path | str = DEFAULT_MEASURED_EXECUTABLE_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("support_first_measured_executable_specs")
    if not isinstance(rows, list):
        raise ValueError("measured executable specs must contain support_first_measured_executable_specs")
    return [dict(row) for row in rows]


def base_specs_by_task_source(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("task_source_id", ""))
        if key:
            specs[key] = dict(row)
    return specs


def parse_config_delta(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        delta = dict(value)
    else:
        text = str(value or "").strip()
        delta = json.loads(text or "{}")
    unknown = sorted(set(delta) - ALLOWED_DELTA_KEYS)
    if unknown:
        raise ValueError(f"unknown repair config delta keys: {', '.join(unknown)}")
    return delta


def apply_config_delta(base_env_config: Mapping[str, Any], delta: Mapping[str, Any]) -> dict[str, Any]:
    parsed = parse_config_delta(dict(delta))
    patched = deepcopy(dict(base_env_config))
    if "track_width_multiplier" in parsed:
        current_width = float(patched.get("track_width", DEFAULT_TRACK_WIDTH))
        patched["track_width"] = current_width * float(parsed["track_width_multiplier"])
    if "max_steps_multiplier" in parsed:
        current_max_steps = int(patched.get("max_steps", DEFAULT_MAX_STEPS))
        patched["max_steps"] = int(math.ceil(current_max_steps * float(parsed["max_steps_multiplier"])))

    # These keys are intentionally metric/protocol metadata at this stage.
    # They do not change env_config or actor observation schema.
    build_env_config(patched)
    return patched


def _source_signature(row: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("hidden_dynamics_bucket", "")),
        str(row.get("road_boundary_bucket", "")),
        str(row.get("obstacle_timing_bucket", "")),
        str(row.get("obstacle_lateral_bucket", "")),
        str(row.get("support_first_v2_panel_spec_id", "")),
    )


def selected_source_spec_ids(
    repair_rows: Iterable[Mapping[str, Any]],
    *,
    sources_per_role_surface: int = DEFAULT_SOURCES_PER_ROLE_SURFACE,
) -> list[str]:
    by_surface: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in repair_rows:
        if str(row.get("repair_variant_id", "")) != "original":
            continue
        spec_id = str(row.get("support_first_v2_panel_spec_id", ""))
        surface = str(row.get("v2_role_surface_id", ""))
        if spec_id and surface and spec_id not in by_surface[surface]:
            by_surface[surface][spec_id] = row

    selected: list[str] = []
    for surface in sorted(by_surface):
        candidates = sorted(by_surface[surface].values(), key=_source_signature)
        chosen: list[Mapping[str, Any]] = []
        used_signatures: set[tuple[str, str, str, str]] = set()
        for row in candidates:
            signature = _source_signature(row)[:4]
            if signature in used_signatures:
                continue
            chosen.append(row)
            used_signatures.add(signature)
            if len(chosen) >= sources_per_role_surface:
                break
        if len(chosen) < sources_per_role_surface:
            chosen_ids = {str(row.get("support_first_v2_panel_spec_id", "")) for row in chosen}
            for row in candidates:
                spec_id = str(row.get("support_first_v2_panel_spec_id", ""))
                if spec_id in chosen_ids:
                    continue
                chosen.append(row)
                if len(chosen) >= sources_per_role_surface:
                    break
        selected.extend(str(row.get("support_first_v2_panel_spec_id", "")) for row in chosen)
    return selected


def _repaired_spec_id(row: Mapping[str, Any]) -> str:
    return f"{row['support_first_v2_panel_spec_id']}__repair_{row['repair_variant_id']}"


def repaired_executable_specs(
    *,
    selected_rows: Iterable[Mapping[str, Any]],
    base_specs: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for row in selected_rows:
        variant = str(row.get("repair_variant_id", ""))
        if variant not in ROLLOUT_VARIANTS:
            continue
        base_task_id = str(row.get("task_source_id", ""))
        base = base_specs.get(base_task_id)
        spec_id = _repaired_spec_id(row)
        if base is None:
            failures.append(
                {
                    "row_id": str(row.get("repair_row_id", "")),
                    "repair_variant_id": variant,
                    "failure_type": "missing_base_spec",
                    "message": base_task_id,
                }
            )
            continue
        if spec_id in specs:
            continue
        try:
            delta = parse_config_delta(row.get("config_delta_json", "{}"))
            env_config = apply_config_delta(dict(base.get("env_config", {})), delta)
        except Exception as exc:  # noqa: BLE001 - preflight must persist row-level config failures.
            failures.append(
                {
                    "row_id": str(row.get("repair_row_id", "")),
                    "repair_variant_id": variant,
                    "failure_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            continue
        spec = deepcopy(dict(base))
        spec.update(
            {
                "task_source_id": spec_id,
                "support_first_v2_panel_spec_id": spec_id,
                "support_first_materialized_v2_panel_spec_id": spec_id,
                "base_task_source_id": base_task_id,
                "base_support_first_v2_panel_spec_id": str(row.get("support_first_v2_panel_spec_id", "")),
                "repair_variant_id": variant,
                "repair_variant_kind": str(row.get("repair_variant_kind", "")),
                "geometry_variant_id": str(row.get("geometry_variant_id", "")),
                "success_semantics_variant_id": str(row.get("success_semantics_variant_id", "")),
                "role_semantics_id": str(row.get("role_semantics_id", "")),
                "repair_config_delta_json": str(row.get("config_delta_json", "{}")),
                "diagnostic_only_no_ranking_claim": True,
                "labels_enter_actor_input": False,
                "v2_ranking_admissible_by_default": False,
                "env_config": env_config,
            }
        )
        specs[spec_id] = spec
    return [specs[key] for key in sorted(specs)], failures


def repaired_rollout_workload_rows(selected_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in selected_rows:
        variant = str(row.get("repair_variant_id", ""))
        if variant not in ROLLOUT_VARIANTS:
            continue
        spec_id = _repaired_spec_id(row)
        workload_id = f"{spec_id}::{row.get('controller_profile_name', '')}"
        output = dict(row)
        output.update(
            {
                "workload_id": workload_id,
                "repaired_workload_id": workload_id,
                "base_workload_id": str(row.get("workload_id", "")),
                "base_support_first_workload_id": str(row.get("support_first_workload_id", "")),
                "task_source_id": spec_id,
                "support_first_v2_panel_spec_id": spec_id,
                "support_first_materialized_v2_panel_spec_id": spec_id,
                "base_task_source_id": str(row.get("task_source_id", "")),
                "base_support_first_v2_panel_spec_id": str(row.get("support_first_v2_panel_spec_id", "")),
                "execution_row_kind": "rollout_geometry_variant",
                "environment_rollout_scheduled": "True",
                "training_scheduled": "False",
                "profile_specific_tuning": "False",
                "controller_family_ranking_claim_made": "False",
                "paper_level_claim_made": "False",
                "level3_self_id_claim_made": "False",
            }
        )
        rows.append(output)
    return sorted(rows, key=lambda item: str(item["workload_id"]))


def repaired_import_rows(
    *,
    selected_rows: Iterable[Mapping[str, Any]],
    episode_rows: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    episode_by_workload = {str(row.get("workload_id", "")): dict(row) for row in episode_rows}
    imports: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for row in selected_rows:
        variant = str(row.get("repair_variant_id", ""))
        if variant not in IMPORT_VARIANTS:
            continue
        base_workload_id = str(row.get("workload_id", ""))
        if base_workload_id not in episode_by_workload:
            missing.append(
                {
                    "repair_row_id": str(row.get("repair_row_id", "")),
                    "repair_variant_id": variant,
                    "base_workload_id": base_workload_id,
                }
            )
        output = dict(row)
        output.update(
            {
                "repaired_import_row_id": str(row.get("repair_row_id", "")),
                "base_workload_id": base_workload_id,
                "import_source_episode_workload_id": base_workload_id,
                "execution_row_kind": "import_existing_episode",
                "semantic_recompute_required": str(variant == "semantics_only"),
                "environment_rollout_scheduled": "False",
                "training_scheduled": "False",
                "profile_specific_tuning": "False",
                "controller_family_ranking_claim_made": "False",
                "paper_level_claim_made": "False",
                "level3_self_id_claim_made": "False",
            }
        )
        imports.append(output)
    return sorted(imports, key=lambda item: str(item["repair_row_id"])), missing


def duplicate_rows(rows: Iterable[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    counts = Counter(str(row.get(key, "")) for row in rows)
    return [{"key": key, "value": value, "duplicate_count": count} for value, count in sorted(counts.items()) if count > 1]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "repaired_runner_adapter_ready",
            "admissible": True,
            "reason": "adapter can emit no-rollout repaired executable specs, geometry workload rows, and import rows",
        },
        {
            "claim": "repaired_measured_execution",
            "admissible": False,
            "reason": "adapter implementation does not run environment reset or rollout",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "ranking remains blocked until repaired execution and post-execution audit",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "adapter does not test history necessity",
        },
    ]


def run_repaired_runner_adapter(
    *,
    repair_matrix_path: Path | str = DEFAULT_REPAIR_MATRIX,
    measured_specs_path: Path | str = DEFAULT_MEASURED_EXECUTABLE_SPECS,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    sources_per_role_surface: int = DEFAULT_SOURCES_PER_ROLE_SURFACE,
    target_role_surface_count: int | None = TARGET_ROLE_SURFACE_COUNT,
    target_controller_profile_count: int | None = TARGET_CONTROLLER_PROFILE_COUNT,
    target_selected_source_spec_count: int | None = TARGET_SELECTED_SOURCE_SPEC_COUNT,
    target_executable_spec_count: int | None = TARGET_EXECUTABLE_SPEC_COUNT,
    target_rollout_workload_cell_count: int | None = TARGET_ROLLOUT_WORKLOAD_CELL_COUNT,
    target_import_row_count: int | None = TARGET_IMPORT_ROW_COUNT,
    target_total_panel_row_count: int | None = TARGET_TOTAL_PANEL_ROW_COUNT,
    next_blocker: str = "m1888-executable-v2-support-first-repaired-runner-adapter-preflight-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    repair_rows = load_repair_matrix(repair_matrix_path)
    base_specs = base_specs_by_task_source(load_measured_specs(measured_specs_path))
    episode_rows = _read_csv_rows(episode_rows_path)
    selected_ids = set(selected_source_spec_ids(repair_rows, sources_per_role_surface=sources_per_role_surface))
    selected_rows = [row for row in repair_rows if str(row.get("support_first_v2_panel_spec_id", "")) in selected_ids]
    executable_specs, config_failure_rows = repaired_executable_specs(selected_rows=selected_rows, base_specs=base_specs)
    rollout_rows = repaired_rollout_workload_rows(selected_rows)
    import_rows, missing_import_rows = repaired_import_rows(selected_rows=selected_rows, episode_rows=episode_rows)
    duplicate_spec_rows = duplicate_rows(executable_specs, "task_source_id")
    duplicate_workload_rows = duplicate_rows(rollout_rows, "workload_id")
    profile_alias_mismatch_count = sum(
        1 for row in selected_rows if str(row.get("controller_profile_name", "")) != str(row.get("profile_name", ""))
    )
    controller_profile_count = _unique_count(selected_rows, "controller_profile_name")
    role_surface_count = _unique_count(selected_rows, "v2_role_surface_id")
    selected_source_spec_count = len(selected_ids)
    total_panel_row_count = len(rollout_rows) + len(import_rows)
    guardrail_violation_count = 0

    target_passes = [
        target_role_surface_count is None or role_surface_count == target_role_surface_count,
        target_controller_profile_count is None or controller_profile_count == target_controller_profile_count,
        target_selected_source_spec_count is None or selected_source_spec_count == target_selected_source_spec_count,
        target_executable_spec_count is None or len(executable_specs) == target_executable_spec_count,
        target_rollout_workload_cell_count is None or len(rollout_rows) == target_rollout_workload_cell_count,
        target_import_row_count is None or len(import_rows) == target_import_row_count,
        target_total_panel_row_count is None or total_panel_row_count == target_total_panel_row_count,
    ]
    result_passes = (
        all(target_passes)
        and not config_failure_rows
        and not missing_import_rows
        and not duplicate_spec_rows
        and not duplicate_workload_rows
        and profile_alias_mismatch_count == 0
        and guardrail_violation_count == 0
    )

    selection_rows = [
        {
            "support_first_v2_panel_spec_id": spec_id,
            "selected": True,
        }
        for spec_id in sorted(selected_ids)
    ]
    role_surface_counts = _count_by(selected_rows, "v2_role_surface_id")

    write_json(
        output / "repaired_measured_executable_specs.json",
        {
            "generated_at_utc": utc_timestamp(),
            "repair_matrix_path": str(repair_matrix_path),
            "measured_specs_path": str(measured_specs_path),
            "sources_per_role_surface": int(sources_per_role_surface),
            "support_first_repaired_measured_executable_specs": executable_specs,
        },
    )
    write_csv_rows(output / "repaired_measured_executable_specs.csv", executable_specs)
    write_csv_rows(output / "repaired_measured_workload_matrix.csv", rollout_rows)
    write_csv_rows(output / "repaired_measured_import_rows.csv", import_rows)
    write_csv_rows(output / "repaired_measured_selection.csv", selection_rows)
    write_csv_rows(output / "repaired_adapter_config_failure_rows.csv", config_failure_rows)
    write_csv_rows(output / "repaired_adapter_missing_import_rows.csv", missing_import_rows)
    write_csv_rows(output / "repaired_adapter_duplicate_spec_rows.csv", duplicate_spec_rows)
    write_csv_rows(output / "repaired_adapter_duplicate_workload_rows.csv", duplicate_workload_rows)
    write_csv_rows(
        output / "repaired_role_surface_counts.csv",
        [{"group": key, "count": value} for key, value in role_surface_counts.items()],
    )
    write_csv_rows(output / "repaired_measured_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "support_first_repaired_runner_adapter_pass"
            if result_passes
            else "support_first_repaired_runner_adapter_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "repair_matrix_path": str(repair_matrix_path),
        "measured_specs_path": str(measured_specs_path),
        "episode_rows_path": str(episode_rows_path),
        "sources_per_role_surface": int(sources_per_role_surface),
        "selected_source_spec_count": selected_source_spec_count,
        "target_selected_source_spec_count": target_selected_source_spec_count,
        "role_surface_count": role_surface_count,
        "target_role_surface_count": target_role_surface_count,
        "controller_profile_count": controller_profile_count,
        "target_controller_profile_count": target_controller_profile_count,
        "executable_spec_count": len(executable_specs),
        "target_executable_spec_count": target_executable_spec_count,
        "rollout_workload_cell_count": len(rollout_rows),
        "target_rollout_workload_cell_count": target_rollout_workload_cell_count,
        "import_row_count": len(import_rows),
        "target_import_row_count": target_import_row_count,
        "total_panel_row_count": total_panel_row_count,
        "target_total_panel_row_count": target_total_panel_row_count,
        "rollout_variant_counts": _count_by(rollout_rows, "repair_variant_id"),
        "import_variant_counts": _count_by(import_rows, "repair_variant_id"),
        "role_surface_counts": role_surface_counts,
        "controller_profile_counts": _count_by(selected_rows, "controller_profile_name"),
        "config_failure_count": len(config_failure_rows),
        "missing_import_row_count": len(missing_import_rows),
        "duplicate_spec_count": len(duplicate_spec_rows),
        "duplicate_workload_count": len(duplicate_workload_rows),
        "profile_alias_mismatch_count": profile_alias_mismatch_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "policy_action_executed": False,
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
        "guardrail_violation_count": guardrail_violation_count,
        "real_m1884_matrix_executed": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repaired_measured_executable_specs": str(output / "repaired_measured_executable_specs.json"),
            "repaired_measured_workload_matrix": str(output / "repaired_measured_workload_matrix.csv"),
            "repaired_measured_import_rows": str(output / "repaired_measured_import_rows.csv"),
            "repaired_measured_selection": str(output / "repaired_measured_selection.csv"),
            "repaired_measured_claim_boundary": str(output / "repaired_measured_claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-matrix", type=Path, default=DEFAULT_REPAIR_MATRIX)
    parser.add_argument("--measured-specs", type=Path, default=DEFAULT_MEASURED_EXECUTABLE_SPECS)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sources-per-role-surface", type=int, default=DEFAULT_SOURCES_PER_ROLE_SURFACE)
    parser.add_argument("--target-role-surface-count", type=int, default=TARGET_ROLE_SURFACE_COUNT)
    parser.add_argument("--target-controller-profile-count", type=int, default=TARGET_CONTROLLER_PROFILE_COUNT)
    parser.add_argument("--target-selected-source-spec-count", type=int, default=TARGET_SELECTED_SOURCE_SPEC_COUNT)
    parser.add_argument("--target-executable-spec-count", type=int, default=TARGET_EXECUTABLE_SPEC_COUNT)
    parser.add_argument("--target-rollout-workload-cell-count", type=int, default=TARGET_ROLLOUT_WORKLOAD_CELL_COUNT)
    parser.add_argument("--target-import-row-count", type=int, default=TARGET_IMPORT_ROW_COUNT)
    parser.add_argument("--target-total-panel-row-count", type=int, default=TARGET_TOTAL_PANEL_ROW_COUNT)
    parser.add_argument(
        "--next-blocker",
        default="m1888-executable-v2-support-first-repaired-runner-adapter-preflight-design",
    )
    args = parser.parse_args()
    summary = run_repaired_runner_adapter(
        repair_matrix_path=args.repair_matrix,
        measured_specs_path=args.measured_specs,
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        sources_per_role_surface=int(args.sources_per_role_surface),
        target_role_surface_count=int(args.target_role_surface_count),
        target_controller_profile_count=int(args.target_controller_profile_count),
        target_selected_source_spec_count=int(args.target_selected_source_spec_count),
        target_executable_spec_count=int(args.target_executable_spec_count),
        target_rollout_workload_cell_count=int(args.target_rollout_workload_cell_count),
        target_import_row_count=int(args.target_import_row_count),
        target_total_panel_row_count=int(args.target_total_panel_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"selected_source_spec_count={summary['selected_source_spec_count']}")
    print(f"executable_spec_count={summary['executable_spec_count']}")
    print(f"rollout_workload_cell_count={summary['rollout_workload_cell_count']}")
    print(f"import_row_count={summary['import_row_count']}")
    print(f"total_panel_row_count={summary['total_panel_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
