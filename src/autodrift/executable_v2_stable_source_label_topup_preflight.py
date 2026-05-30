"""No-reset planner for stable executable v2 source-label top-up."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_REPLACEMENT_NEEDS = Path("runs/m1800_executable_v2_label_source_compatibility_preflight/replacement_need_rows.csv")
DEFAULT_SOURCE_LABEL_SUPPORT = Path("runs/m1800_executable_v2_label_source_compatibility_preflight/source_label_support.csv")
DEFAULT_BOUNDED_PANEL_SPECS = Path("runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json")
DEFAULT_OUTPUT_DIR = Path("runs/m1803_executable_v2_stable_source_label_topup_preflight")
STABLE_SURFACE = "stable_avoidance_aes"
GROUP_KEYS = (
    "source_scenario_spec_id",
    "v2_role_surface_id",
    "v2_task_label",
    "hidden_dynamics_bucket",
    "road_boundary_bucket",
    "obstacle_timing_bucket",
    "obstacle_lateral_bucket",
)
BUCKET_KEYS = (
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


def _read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def _labels(value: Any) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip() for item in value if str(item).strip()}
    return {part.strip() for part in str(value).replace(",", ";").split(";") if part.strip()}


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def load_replacement_need_rows(path: Path | str = DEFAULT_REPLACEMENT_NEEDS) -> list[dict[str, Any]]:
    rows = _read_csv_rows(path)
    return [
        dict(row)
        for row in rows
        if str(row.get("v2_role_surface_id", "")) == STABLE_SURFACE
        and str(row.get("support_status", "")) == "unsupported_systematic"
    ]


def load_source_label_support(path: Path | str = DEFAULT_SOURCE_LABEL_SUPPORT) -> list[dict[str, Any]]:
    return _read_csv_rows(path)


def load_stable_source_pool(path: Path | str = DEFAULT_BOUNDED_PANEL_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return [
        dict(row)
        for row in payload["bounded_panel_specs"]
        if str(row.get("role_panel_id", "")) == STABLE_SURFACE
    ]


def source_label_key(row: Mapping[str, Any], *, source_key: str = "source_scenario_spec_id", label_key: str = "v2_task_label") -> str:
    return "|".join(
        (
            str(row.get(source_key, "")),
            STABLE_SURFACE,
            str(row.get(label_key, "")),
            str(row.get("hidden_dynamics_bucket", "")),
            str(row.get("road_boundary_bucket", "")),
            str(row.get("obstacle_timing_bucket", "")),
            str(row.get("obstacle_lateral_bucket", "")),
        )
    )


def topup_targets(replacement_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for index, row in enumerate(replacement_rows):
        target = {
            "topup_target_id": f"stable-topup-{index:03d}",
            **{key: str(row.get(key, "")) for key in GROUP_KEYS},
            "missing_profile_count": int(row.get("missing_profile_count", 0) or 0),
            "required_profile_controls": str(row.get("failure_profile_names", "")) or "all_profile_controls_from_missing_profile_count",
            "recommended_next_action": str(row.get("recommended_next_action", "")),
        }
        targets.append(target)
    return targets


def _observed_support_status(
    *,
    source_label_support_rows: list[Mapping[str, Any]],
    source_id: str,
    label: str,
    hidden: str,
    road: str,
    timing: str,
    lateral: str,
) -> str:
    for row in source_label_support_rows:
        if (
            str(row.get("source_scenario_spec_id", "")) == source_id
            and str(row.get("v2_role_surface_id", "")) == STABLE_SURFACE
            and str(row.get("v2_task_label", "")) == label
            and str(row.get("hidden_dynamics_bucket", "")) == hidden
            and str(row.get("road_boundary_bucket", "")) == road
            and str(row.get("obstacle_timing_bucket", "")) == timing
            and str(row.get("obstacle_lateral_bucket", "")) == lateral
        ):
            return str(row.get("support_status", ""))
    return "unobserved"


def candidate_source_pool_rows(stable_source_pool: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in stable_source_pool:
        rows.append(
            {
                "candidate_bounded_panel_spec_id": str(source.get("bounded_panel_spec_id", source.get("scenario_spec_id", ""))),
                "candidate_source_scenario_spec_id": str(source.get("source_scenario_spec_id", "")),
                "metadata_labels": str(source.get("allowed_labels_metadata_only", "")),
                "hidden_dynamics_bucket": str(source.get("hidden_dynamics_bucket", "")),
                "road_boundary_bucket": str(source.get("road_boundary_bucket", "")),
                "obstacle_timing_bucket": str(source.get("obstacle_timing_bucket", "")),
                "obstacle_lateral_bucket": str(source.get("obstacle_lateral_bucket", "")),
                "sampling_repair_variant_id": str(source.get("sampling_repair_variant_id", "")),
                "labels_enter_actor_input": False,
            }
        )
    return rows


def _candidate_class(
    *,
    label_supported: bool,
    exact_bucket_match: bool,
    hidden_match: bool,
    observed_support_status: str,
) -> str | None:
    if not label_supported:
        return None
    if exact_bucket_match and observed_support_status == "unsupported_systematic":
        return "metadata_only_untrusted"
    if exact_bucket_match:
        return "exact_existing_candidate"
    if hidden_match:
        return "near_existing_candidate"
    return None


def topup_candidate_rows(
    *,
    targets: list[Mapping[str, Any]],
    stable_source_pool: list[Mapping[str, Any]],
    source_label_support_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        label = str(target["v2_task_label"])
        for source in stable_source_pool:
            candidate_labels = _labels(source.get("allowed_labels_metadata_only", ""))
            label_supported = label in candidate_labels
            matches = {key: str(source.get(key, "")) == str(target.get(key, "")) for key in BUCKET_KEYS}
            exact_bucket_match = all(matches.values())
            observed = _observed_support_status(
                source_label_support_rows=source_label_support_rows,
                source_id=str(source.get("bounded_panel_spec_id", source.get("scenario_spec_id", ""))),
                label=label,
                hidden=str(source.get("hidden_dynamics_bucket", "")),
                road=str(source.get("road_boundary_bucket", "")),
                timing=str(source.get("obstacle_timing_bucket", "")),
                lateral=str(source.get("obstacle_lateral_bucket", "")),
            )
            candidate_class = _candidate_class(
                label_supported=label_supported,
                exact_bucket_match=exact_bucket_match,
                hidden_match=matches["hidden_dynamics_bucket"],
                observed_support_status=observed,
            )
            if candidate_class is None:
                continue
            bucket_match_score = sum(1 for value in matches.values() if value)
            direct = candidate_class == "exact_existing_candidate" and observed == "supported_observed"
            rows.append(
                {
                    "topup_target_id": str(target["topup_target_id"]),
                    "target_source_scenario_spec_id": str(target["source_scenario_spec_id"]),
                    "target_v2_task_label": label,
                    "candidate_bounded_panel_spec_id": str(source.get("bounded_panel_spec_id", source.get("scenario_spec_id", ""))),
                    "candidate_source_scenario_spec_id": str(source.get("source_scenario_spec_id", "")),
                    "candidate_class": candidate_class,
                    "candidate_label_support": label_supported,
                    "hidden_match": matches["hidden_dynamics_bucket"],
                    "road_match": matches["road_boundary_bucket"],
                    "timing_match": matches["obstacle_timing_bucket"],
                    "lateral_match": matches["obstacle_lateral_bucket"],
                    "bucket_match_score": bucket_match_score,
                    "observed_reset_support_status": observed,
                    "requires_reset_probe": not direct,
                    "requires_new_materialization": False,
                    "admissible_as_direct_replacement": direct,
                    "measured_execution_admissible": False,
                    "controller_family_ranking_admissible": False,
                }
            )
    return rows


def new_materialization_need_rows(
    *,
    targets: list[Mapping[str, Any]],
    candidate_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_target: dict[str, list[Mapping[str, Any]]] = {}
    for row in candidate_rows:
        candidates_by_target.setdefault(str(row["topup_target_id"]), []).append(row)
    rows: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target["topup_target_id"])
        direct = [row for row in candidates_by_target.get(target_id, []) if _bool(row.get("admissible_as_direct_replacement"))]
        if direct:
            continue
        rows.append(
            {
                "topup_target_id": target_id,
                **{key: str(target.get(key, "")) for key in GROUP_KEYS},
                "missing_profile_count": int(target.get("missing_profile_count", 0) or 0),
                "candidate_count": len(candidates_by_target.get(target_id, [])),
                "requires_new_materialization": True,
                "reason": "no_observed_supported_direct_replacement",
                "recommended_next_action": "materialize_or_probe_new_stable_source_label_candidate",
            }
        )
    return rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "candidate_source_plan",
            "admissible": True,
            "reason": "no-reset source metadata plan can guide later top-up materialization",
        },
        {
            "claim": "direct_replacement_without_reset_probe",
            "admissible": False,
            "reason": "metadata-only candidates must not replace unsupported rows without observed reset support",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "top-up candidates still require reset support",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "source top-up planning is task-quality infrastructure, not ranking evidence",
        },
    ]


def run_executable_v2_stable_source_label_topup_preflight(
    *,
    replacement_needs_path: Path | str = DEFAULT_REPLACEMENT_NEEDS,
    source_label_support_path: Path | str = DEFAULT_SOURCE_LABEL_SUPPORT,
    bounded_panel_specs_path: Path | str = DEFAULT_BOUNDED_PANEL_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_topup_count: int | None = None,
    next_blocker: str = "m1804-executable-v2-stable-source-label-topup-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    replacement_rows = load_replacement_need_rows(replacement_needs_path)
    support_rows = load_source_label_support(source_label_support_path)
    stable_source_pool = load_stable_source_pool(bounded_panel_specs_path)
    targets = topup_targets(replacement_rows)
    source_pool_rows = candidate_source_pool_rows(stable_source_pool)
    candidates = topup_candidate_rows(
        targets=targets,
        stable_source_pool=stable_source_pool,
        source_label_support_rows=support_rows,
    )
    new_needs = new_materialization_need_rows(targets=targets, candidate_rows=candidates)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    target_matches = target_topup_count is None or len(targets) == int(target_topup_count)
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in source_pool_rows)
    direct_replacement_count = sum(_bool(row.get("admissible_as_direct_replacement")) for row in candidates)
    result_passes = target_matches and labels_enter_actor_input_count == 0 and guardrail_violation_count == 0

    write_csv_rows(output / "stable_topup_targets.csv", targets)
    write_csv_rows(output / "stable_candidate_source_pool.csv", source_pool_rows)
    write_csv_rows(output / "stable_topup_candidate_rows.csv", candidates)
    write_csv_rows(output / "stable_new_materialization_need_rows.csv", new_needs)
    write_csv_rows(output / "stable_topup_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": (
            "executable_v2_stable_source_label_topup_preflight_pass"
            if result_passes
            else "executable_v2_stable_source_label_topup_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "replacement_needs_path": str(replacement_needs_path),
        "source_label_support_path": str(source_label_support_path),
        "bounded_panel_specs_path": str(bounded_panel_specs_path),
        "stable_topup_target_count": len(targets),
        "target_topup_count": target_topup_count,
        "target_missing_profile_count_total": sum(int(row.get("missing_profile_count", 0) or 0) for row in targets),
        "stable_candidate_source_count": len(source_pool_rows),
        "candidate_row_count": len(candidates),
        "candidate_class_counts": _count_by_key(candidates, "candidate_class"),
        "direct_replacement_count": direct_replacement_count,
        "new_materialization_need_count": len(new_needs),
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "measured_execution_admissible": False,
        "controller_family_ranking_admissible": False,
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
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build no-reset stable source-label top-up planning artifacts.")
    parser.add_argument("--replacement-needs", type=Path, default=DEFAULT_REPLACEMENT_NEEDS)
    parser.add_argument("--source-label-support", type=Path, default=DEFAULT_SOURCE_LABEL_SUPPORT)
    parser.add_argument("--bounded-panel-specs", type=Path, default=DEFAULT_BOUNDED_PANEL_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-topup-count", type=int, default=None)
    parser.add_argument("--next-blocker", default="m1804-executable-v2-stable-source-label-topup-execution-design")
    args = parser.parse_args()

    summary = run_executable_v2_stable_source_label_topup_preflight(
        replacement_needs_path=args.replacement_needs,
        source_label_support_path=args.source_label_support,
        bounded_panel_specs_path=args.bounded_panel_specs,
        output_dir=args.output_dir,
        target_topup_count=args.target_topup_count,
        next_blocker=args.next_blocker,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"stable_topup_target_count={summary['stable_topup_target_count']}")
    print(f"candidate_row_count={summary['candidate_row_count']}")
    print(f"new_materialization_need_count={summary['new_materialization_need_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
