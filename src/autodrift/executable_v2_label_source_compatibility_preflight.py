"""No-reset compatibility preflight for executable v2 source-label pairs."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_EXECUTABLE_V2_PANEL_SPECS = Path(
    "runs/m1790_executable_v2_panel_spec_materialization_preflight/executable_v2_panel_specs.json"
)
DEFAULT_RESET_ROWS = Path("runs/m1794_executable_v2_reset_feasibility_preflight/reset_stress_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1798_executable_v2_label_source_compatibility_preflight")
GROUP_KEYS = (
    "source_scenario_spec_id",
    "v2_role_surface_id",
    "v2_task_label",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
)
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


def _read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_executable_v2_panel_specs(path: Path | str = DEFAULT_EXECUTABLE_V2_PANEL_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return sorted(
        [dict(row) for row in payload["executable_v2_panel_specs"]],
        key=lambda row: str(row["v2_panel_spec_id"]),
    )


def load_reset_rows(path: Path | str = DEFAULT_RESET_ROWS) -> list[dict[str, Any]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row["v2_panel_spec_id"]))


def source_label_group_id(row: Mapping[str, Any]) -> str:
    return "|".join(str(row.get(key, "")) for key in GROUP_KEYS)


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _group_status(success_count: int, failure_count: int) -> str:
    if success_count > 0 and failure_count == 0:
        return "supported_observed"
    if success_count == 0 and failure_count > 0:
        return "unsupported_systematic"
    if success_count > 0 and failure_count > 0:
        return "sparse_fragile"
    return "unobserved"


def source_label_support_rows(reset_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in reset_rows:
        grouped[source_label_group_id(row)].append(row)

    support_rows: list[dict[str, Any]] = []
    for group_id in sorted(grouped):
        rows = grouped[group_id]
        success_rows = [row for row in rows if _bool(row.get("reset_success"))]
        failure_rows = [row for row in rows if not _bool(row.get("reset_success"))]
        first = rows[0]
        status = _group_status(len(success_rows), len(failure_rows))
        support_rows.append(
            {
                "source_label_group_id": group_id,
                **{key: str(first.get(key, "")) for key in GROUP_KEYS},
                "profile_count": len({str(row.get("profile_name", "")) for row in rows}),
                "reset_success_count": len(success_rows),
                "sampling_failure_count": len(failure_rows),
                "success_profile_names": ";".join(sorted({str(row.get("profile_name", "")) for row in success_rows})),
                "failure_profile_names": ";".join(sorted({str(row.get("profile_name", "")) for row in failure_rows})),
                "support_status": status,
                "systematic_failure": status == "unsupported_systematic",
                "sparse_failure": status == "sparse_fragile",
                "replacement_required": status in {"unsupported_systematic", "sparse_fragile"},
                "ranking_admissible_by_default": False,
                "labels_enter_actor_input": any(_bool(row.get("labels_enter_actor_input")) for row in rows),
            }
        )
    return support_rows


def _support_by_group(reset_rows: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["source_label_group_id"]: row for row in source_label_support_rows(reset_rows)}


def _reset_by_spec_id(reset_rows: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row["v2_panel_spec_id"]): row for row in reset_rows}


def _compatible_spec(spec: Mapping[str, Any], reset_row: Mapping[str, Any], support_row: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(spec)
    row.update(
        {
            "source_label_group_id": support_row["source_label_group_id"],
            "source_label_support_status": support_row["support_status"],
            "compatible_for_reset_rerun": True,
            "replacement_required": bool(support_row["replacement_required"]),
            "measured_execution_admissible": False,
            "controller_family_ranking_admissible": False,
            "reset_success_observed": _bool(reset_row.get("reset_success")),
        }
    )
    return row


def classify_compatibility(
    *,
    executable_specs: list[Mapping[str, Any]],
    reset_rows: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    support_by_group = _support_by_group(reset_rows)
    reset_by_id = _reset_by_spec_id(reset_rows)
    compatible_specs: list[dict[str, Any]] = []
    violation_rows: list[dict[str, Any]] = []
    sparse_rows: list[dict[str, Any]] = []
    unobserved_rows: list[dict[str, Any]] = []

    for spec in executable_specs:
        spec_id = str(spec["v2_panel_spec_id"])
        reset_row = reset_by_id.get(spec_id)
        group_id = source_label_group_id(spec)
        support_row = support_by_group.get(group_id)
        if reset_row is None or support_row is None:
            unobserved_rows.append(
                {
                    **{key: str(spec.get(key, "")) for key in GROUP_KEYS},
                    "v2_panel_spec_id": spec_id,
                    "profile_name": str(spec.get("profile_name", "")),
                    "source_label_group_id": group_id,
                    "support_status": "unobserved",
                    "reason": "missing reset row for executable v2 spec",
                    "replacement_required": True,
                }
            )
            continue
        status = str(support_row["support_status"])
        if _bool(reset_row.get("reset_success")):
            compatible_specs.append(_compatible_spec(spec, reset_row, support_row))
            continue
        base = {
            **{key: str(reset_row.get(key, spec.get(key, ""))) for key in GROUP_KEYS},
            "v2_panel_spec_id": spec_id,
            "profile_name": str(reset_row.get("profile_name", spec.get("profile_name", ""))),
            "source_label_group_id": group_id,
            "support_status": status,
            "error_type": str(reset_row.get("error_type", "")),
            "error_message": str(reset_row.get("error_message", "")),
            "replacement_required": True,
            "compatible_for_reset_rerun": False,
            "measured_execution_admissible": False,
            "controller_family_ranking_admissible": False,
        }
        if status == "unsupported_systematic":
            violation_rows.append({**base, "violation_type": "unsupported_systematic"})
        elif status == "sparse_fragile":
            sparse_rows.append({**base, "violation_type": "sparse_fragile"})
        else:
            violation_rows.append({**base, "violation_type": "unsupported_unclassified"})

    replacement_rows = replacement_need_rows(violation_rows=violation_rows, sparse_rows=sparse_rows, unobserved_rows=unobserved_rows)
    return compatible_specs, violation_rows, sparse_rows, unobserved_rows, replacement_rows


def replacement_need_rows(
    *,
    violation_rows: list[Mapping[str, Any]],
    sparse_rows: list[Mapping[str, Any]],
    unobserved_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in [*violation_rows, *sparse_rows, *unobserved_rows]:
        key = tuple(str(row.get(item, "")) for item in GROUP_KEYS + ("support_status",))
        grouped[key].append(row)

    rows: list[dict[str, Any]] = []
    for key in sorted(grouped):
        group_rows = grouped[key]
        first = group_rows[0]
        status = str(first.get("support_status", ""))
        if status == "sparse_fragile":
            action = "run_seed_fragility_or_tight_filter_probe_after_systematic_repair"
        elif status == "unobserved":
            action = "materialize_or_probe_missing_source_label_evidence"
        else:
            action = "find_or_materialize_alternate_source_with_observed_label_support"
        rows.append(
            {
                **{item: str(first.get(item, "")) for item in GROUP_KEYS},
                "support_status": status,
                "missing_profile_count": len({str(row.get("profile_name", "")) for row in group_rows}),
                "reason": str(first.get("violation_type", first.get("reason", status))),
                "recommended_next_action": action,
            }
        )
    return rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "compatible_reset_rerun_subset",
            "admissible": True,
            "reason": "reset-success rows may be rerun in a later reset-only milestone",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "source-label replacements and sparse-failure probes remain unresolved",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "compatibility preflight is public task-quality infrastructure, not ranking evidence",
        },
        {
            "claim": "paper_level_result",
            "admissible": False,
            "reason": "no rollout or private holdout evidence is produced",
        },
    ]


def run_executable_v2_label_source_compatibility_preflight(
    *,
    executable_v2_panel_specs_path: Path | str = DEFAULT_EXECUTABLE_V2_PANEL_SPECS,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_input_spec_count: int | None = None,
    target_profile_count: int | None = None,
    next_blocker: str = "m1799-executable-v2-label-source-compatibility-preflight-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_executable_v2_panel_specs(executable_v2_panel_specs_path)
    reset_rows = load_reset_rows(reset_rows_path)
    support_rows = source_label_support_rows(reset_rows)
    compatible_specs, violation_rows, sparse_rows, unobserved_rows, replacement_rows = classify_compatibility(
        executable_specs=executable_specs,
        reset_rows=reset_rows,
    )

    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in executable_specs)
    ranking_admissible_by_default_count = sum(_bool(row.get("v2_ranking_admissible_by_default")) for row in executable_specs)
    profile_count = len({str(row.get("profile_name", "")) for row in executable_specs})
    role_surface_count = len({str(row.get("v2_role_surface_id", "")) for row in executable_specs})
    target_spec_matches = target_input_spec_count is None or len(executable_specs) == int(target_input_spec_count)
    target_profile_matches = target_profile_count is None or profile_count == int(target_profile_count)
    result_passes = (
        target_spec_matches
        and target_profile_matches
        and len(reset_rows) <= len(executable_specs)
        and labels_enter_actor_input_count == 0
        and ranking_admissible_by_default_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "source_label_support.csv", support_rows)
    write_csv_rows(output / "compatibility_violation_rows.csv", violation_rows)
    write_csv_rows(output / "sparse_failure_rows.csv", sparse_rows)
    write_csv_rows(output / "unobserved_rows.csv", unobserved_rows)
    write_csv_rows(output / "replacement_need_rows.csv", replacement_rows)
    write_csv_rows(output / "compatible_executable_v2_panel_specs.csv", compatible_specs)
    write_json(
        output / "compatible_executable_v2_panel_specs.json",
        {
            "generated_at_utc": utc_timestamp(),
            "executable_v2_panel_specs": compatible_specs,
        },
    )
    write_csv_rows(
        output / "compatible_executable_v2_panel_matrix.csv",
        [
            {
                "v2_panel_spec_id": row["v2_panel_spec_id"],
                "source_scenario_spec_id": row.get("source_scenario_spec_id", ""),
                "v2_role_surface_id": row.get("v2_role_surface_id", ""),
                "profile_name": row.get("profile_name", ""),
                "v2_task_label": row.get("v2_task_label", ""),
                "hidden_dynamics_bucket": row.get("hidden_dynamics_bucket", ""),
                "source_label_support_status": row.get("source_label_support_status", ""),
                "compatible_for_reset_rerun": row.get("compatible_for_reset_rerun", False),
                "replacement_required": row.get("replacement_required", False),
                "measured_execution_admissible": False,
                "controller_family_ranking_admissible": False,
            }
            for row in compatible_specs
        ],
    )
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "executable_v2_label_source_compatibility_preflight_pass"
            if result_passes
            else "executable_v2_label_source_compatibility_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "executable_v2_panel_specs_path": str(executable_v2_panel_specs_path),
        "reset_rows_path": str(reset_rows_path),
        "input_spec_count": len(executable_specs),
        "target_input_spec_count": target_input_spec_count,
        "input_reset_row_count": len(reset_rows),
        "compatible_spec_count": len(compatible_specs),
        "compatibility_violation_count": len(violation_rows),
        "sparse_failure_count": len(sparse_rows),
        "unobserved_count": len(unobserved_rows),
        "replacement_need_count": len(replacement_rows),
        "profile_control_count": profile_count,
        "target_profile_count": target_profile_count,
        "role_surface_count": role_surface_count,
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "ranking_admissible_by_default_count": ranking_admissible_by_default_count,
        "support_status_counts": _count_by_key(support_rows, "support_status"),
        "compatible_role_surface_counts": _count_by_key(compatible_specs, "v2_role_surface_id"),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "compatible_reset_rerun_admissible": len(compatible_specs) > 0 and labels_enter_actor_input_count == 0,
        "measured_execution_admissible": False,
        "controller_family_ranking_admissible": False,
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
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build no-reset executable v2 source-label compatibility artifacts.")
    parser.add_argument("--executable-v2-panel-specs", type=Path, default=DEFAULT_EXECUTABLE_V2_PANEL_SPECS)
    parser.add_argument("--reset-rows", type=Path, default=DEFAULT_RESET_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-input-spec-count", type=int, default=None)
    parser.add_argument("--target-profile-count", type=int, default=None)
    parser.add_argument("--next-blocker", default="m1799-executable-v2-label-source-compatibility-preflight-execution-design")
    args = parser.parse_args()

    summary = run_executable_v2_label_source_compatibility_preflight(
        executable_v2_panel_specs_path=args.executable_v2_panel_specs,
        reset_rows_path=args.reset_rows,
        output_dir=args.output_dir,
        target_input_spec_count=args.target_input_spec_count,
        target_profile_count=args.target_profile_count,
        next_blocker=args.next_blocker,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_spec_count={summary['input_spec_count']}")
    print(f"compatible_spec_count={summary['compatible_spec_count']}")
    print(f"compatibility_violation_count={summary['compatibility_violation_count']}")
    print(f"sparse_failure_count={summary['sparse_failure_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
