"""Deterministic no-rollout templates for calibrated outcome-support repair."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_json


REPAIR_BRANCH_ID = "paper_route_task_quality_calibrated_repaired_outcome_support_repair"
TEMPLATE_ID = "executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0"
DEFAULT_LOCALIZATION_SUMMARY = Path(
    "runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/summary.json"
)
DEFAULT_OUTPUT = Path("configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json")
REPAIR_AXIS_TARGETS = {
    "offtrack_anchor_relief": 64,
    "offtrack_boundary_relief_extension": 32,
    "success_support_expansion": 48,
    "collision_mitigation_relief": 32,
    "mitigation_metric_isolation": 16,
}
SPLIT_TARGETS = {"public_debug": 112, "public_gate": 80}
FORBIDDEN_BOOL_FIELDS = (
    "labels_enter_actor_input",
    "v2_ranking_admissible_by_default",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float) -> float:
    try:
        return float(str(value).replace("p", "."))
    except (TypeError, ValueError):
        return float(default)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _cycle_pick(rows: Sequence[Mapping[str, Any]], index: int, *, description: str) -> Mapping[str, Any]:
    if not rows:
        raise ValueError(f"no rows available for {description}")
    return rows[index % len(rows)]


def _split_for_index(index: int) -> str:
    return "public_debug" if index < SPLIT_TARGETS["public_debug"] else "public_gate"


def _artifact_path(summary: Mapping[str, Any], name: str) -> Path:
    artifacts = summary.get("artifacts", {})
    if not isinstance(artifacts, Mapping) or name not in artifacts:
        raise ValueError(f"localization summary missing artifact path for {name}")
    return Path(str(artifacts[name]))


def _field(row: Mapping[str, Any], *names: str, default: str = "") -> str:
    for name in names:
        value = str(row.get(name, "")).strip()
        if value:
            return value
    return default


def _parent_source_id(row: Mapping[str, Any], fallback: str) -> str:
    return _field(row, "candidate_source_id", "parent_candidate_source_id", "task_source_id", default=fallback)


def _base_candidate(
    *,
    index: int,
    repair_axis: str,
    repair_source_kind: str,
    parent: Mapping[str, Any],
    sequence_index: int,
    total_in_axis: int,
) -> dict[str, Any]:
    fallback_id = f"{repair_axis}_{sequence_index:03d}"
    parent_source = _parent_source_id(parent, fallback_id)
    parent_role = _field(parent, "source_role_semantics", "parent_source_role_semantics", default="unknown_role")
    parent_tier = _field(parent, "parent_feasibility_tier_id", "feasibility_tier_id", default="unknown_tier")
    parent_surface = _field(parent, "parent_surface_variant", "surface_variant", default="")
    parent_normalized_surface = _field(
        parent,
        "normalized_surface_variant",
        "parent_normalized_surface_variant",
        "surface_variant",
        default="unknown_surface",
    )
    parent_label = _field(parent, "sampled_obstacle_label", "parent_sampled_obstacle_label", default="unknown_label")
    parent_repair_source_kind = _field(parent, "repair_source_kind", "parent_repair_source_kind", default=repair_source_kind)
    parent_selection_quota = _field(parent, "selection_quota_name", "parent_selection_quota_name", default="")
    parent_profile = _field(parent, "profile_name", "parent_profile_name", default="slice_anchor")
    parent_base_geometry = _field(parent, "base_geometry_source", "parent_base_geometry_source", default="")
    parent_outcome = _field(parent, "outcome_bucket", "parent_outcome_bucket", default="")
    parent_termination = _field(parent, "termination_reason", "parent_termination_reason", default="")
    if parent_repair_source_kind == "anchor_neighborhood":
        parent_role = "stable_aeb" if parent_role == "unknown_role" else parent_role
        parent_tier = "tier_c_boundary_near_miss" if parent_tier == "unknown_tier" else parent_tier
        parent_normalized_surface = (
            "post_friction_step" if parent_normalized_surface == "unknown_surface" else parent_normalized_surface
        )
        parent_label = "aeb_feasible" if parent_label == "unknown_label" else parent_label
    if parent_repair_source_kind == "offtrack_boundary_relief":
        parent_role = "stable_aes_only" if parent_role == "unknown_role" else parent_role
        parent_tier = (
            "tier_not_applicable_offtrack_boundary_relief"
            if parent_tier == "unknown_tier"
            else parent_tier
        )
        parent_normalized_surface = (
            "relief_surface_unspecified"
            if parent_normalized_surface == "unknown_surface"
            else parent_normalized_surface
        )
        parent_label = "aes_feasible" if parent_label == "unknown_label" else parent_label
    if parent_repair_source_kind == "mitigation_isolation_check":
        parent_role = "unavoidable_mitigation" if parent_role == "unknown_role" else parent_role
        parent_tier = "tier_d_handling_limit_drift_required" if parent_tier == "unknown_tier" else parent_tier
        parent_normalized_surface = "steady_surface" if parent_normalized_surface == "unknown_surface" else parent_normalized_surface
        parent_label = "unavoidable" if parent_label == "unknown_label" else parent_label
    if parent_role == "unavoidable_mitigation":
        parent_tier = "tier_d_handling_limit_drift_required" if parent_tier == "unknown_tier" else parent_tier
        parent_label = "unavoidable" if parent_label == "unknown_label" else parent_label
    family_payload = {
        "repair_axis": repair_axis,
        "repair_source_kind": repair_source_kind,
        "tier": parent_tier,
        "role": parent_role,
        "surface": parent_normalized_surface,
        "label": parent_label,
    }
    return {
        "template_id": TEMPLATE_ID,
        "repair_branch_id": REPAIR_BRANCH_ID,
        "repair_candidate_id": f"cosr_v0_{index:04d}_{repair_axis}",
        "repair_axis": repair_axis,
        "repair_source_kind": repair_source_kind,
        "repair_source_family": _stable_hash(family_payload),
        "repair_sequence_index": int(sequence_index),
        "repair_axis_target_count": int(total_in_axis),
        "parent_candidate_source_id": parent_source,
        "parent_task_source_id": _field(parent, "task_source_id", default=parent_source),
        "parent_profile_name": parent_profile,
        "parent_repair_source_kind": parent_repair_source_kind,
        "parent_selection_quota_name": parent_selection_quota,
        "parent_feasibility_tier_id": parent_tier,
        "parent_source_role_semantics": parent_role,
        "parent_surface_variant": parent_surface,
        "parent_normalized_surface_variant": parent_normalized_surface,
        "parent_sampled_obstacle_label": parent_label,
        "parent_base_geometry_source": parent_base_geometry,
        "parent_outcome_bucket": parent_outcome,
        "parent_termination_reason": parent_termination,
        "target_feasibility_tier_id": parent_tier,
        "target_source_role_semantics": parent_role,
        "target_surface_variant": parent_surface or parent_normalized_surface,
        "target_normalized_surface_variant": parent_normalized_surface,
        "target_sampled_obstacle_label": parent_label,
        "source_split": _split_for_index(index),
        "paper_holdout_candidate": False,
        "speed_ref": _float(parent.get("speed_ref", 18.0), 18.0),
        "mu": _float(parent.get("mu", 0.40), 0.40),
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _offtrack_anchor_relief_rows(rows: Sequence[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    eligible = [row for row in rows if _field(row, "repair_source_kind") == "anchor_neighborhood"]
    output: list[dict[str, Any]] = []
    for local_index in range(REPAIR_AXIS_TARGETS["offtrack_anchor_relief"]):
        parent = _cycle_pick(eligible, local_index, description="offtrack_anchor_relief")
        base = _base_candidate(
            index=start_index + local_index,
            repair_axis="offtrack_anchor_relief",
            repair_source_kind="anchor_neighborhood",
            parent=parent,
            sequence_index=local_index,
            total_in_axis=REPAIR_AXIS_TARGETS["offtrack_anchor_relief"],
        )
        base.update(
            {
                "obstacle_distance_delta": (2.0, 4.0, 6.0, 8.0)[local_index % 4],
                "obstacle_half_width_delta": (0.0, -0.05, -0.10, -0.15)[(local_index // 4) % 4],
                "post_obstacle_track_width_delta": (0.50, 0.75, 1.00, 1.25)[(local_index // 8) % 4],
                "reaction_distance_delta": (2.0, 4.0, 6.0, 8.0)[local_index % 4],
                "recovery_corridor_profile": "anchor_offtrack_relief",
                "collision_severity_relief_delta": 0.0,
                "mitigation_metric_mode": "not_mitigation",
            }
        )
        output.append(base)
    return output


def _offtrack_boundary_relief_extension_rows(
    rows: Sequence[Mapping[str, Any]], *, start_index: int
) -> list[dict[str, Any]]:
    eligible = [row for row in rows if _field(row, "repair_source_kind") == "offtrack_boundary_relief"]
    output: list[dict[str, Any]] = []
    for local_index in range(REPAIR_AXIS_TARGETS["offtrack_boundary_relief_extension"]):
        parent = _cycle_pick(eligible, local_index, description="offtrack_boundary_relief_extension")
        base = _base_candidate(
            index=start_index + local_index,
            repair_axis="offtrack_boundary_relief_extension",
            repair_source_kind="offtrack_boundary_relief",
            parent=parent,
            sequence_index=local_index,
            total_in_axis=REPAIR_AXIS_TARGETS["offtrack_boundary_relief_extension"],
        )
        base.update(
            {
                "obstacle_distance_delta": (4.0, 6.0, 8.0, 10.0)[local_index % 4],
                "obstacle_half_width_delta": (-0.10, -0.20)[(local_index // 2) % 2],
                "post_obstacle_track_width_delta": (0.75, 1.00, 1.25, 1.50)[(local_index // 4) % 4],
                "reaction_distance_delta": (4.0, 6.0, 8.0, 10.0)[local_index % 4],
                "recovery_corridor_profile": "offtrack_boundary_relief_extension",
                "collision_severity_relief_delta": 0.0,
                "mitigation_metric_mode": "not_mitigation",
            }
        )
        output.append(base)
    return output


def _success_support_expansion_rows(rows: Sequence[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for local_index in range(REPAIR_AXIS_TARGETS["success_support_expansion"]):
        parent = _cycle_pick(rows, local_index, description="success_support_expansion")
        base = _base_candidate(
            index=start_index + local_index,
            repair_axis="success_support_expansion",
            repair_source_kind="success_stabilizer",
            parent=parent,
            sequence_index=local_index,
            total_in_axis=REPAIR_AXIS_TARGETS["success_support_expansion"],
        )
        base.update(
            {
                "obstacle_distance_delta": (0.0, 2.0, 4.0)[local_index % 3],
                "obstacle_half_width_delta": (0.0, -0.05)[(local_index // 3) % 2],
                "post_obstacle_track_width_delta": (0.0, 0.25, 0.50)[(local_index // 6) % 3],
                "reaction_distance_delta": (0.0, 2.0, 4.0)[local_index % 3],
                "recovery_corridor_profile": "success_support_expansion",
                "collision_severity_relief_delta": 0.0,
                "mitigation_metric_mode": "not_mitigation",
            }
        )
        output.append(base)
    return output


def _collision_mitigation_relief_rows(rows: Sequence[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if _field(row, "repair_source_kind") == "mitigation_isolation_check"
        or _field(row, "source_role_semantics") == "unavoidable_mitigation"
        or _field(row, "sampled_obstacle_label") == "unavoidable"
    ]
    output: list[dict[str, Any]] = []
    for local_index in range(REPAIR_AXIS_TARGETS["collision_mitigation_relief"]):
        parent = _cycle_pick(eligible, local_index, description="collision_mitigation_relief")
        base = _base_candidate(
            index=start_index + local_index,
            repair_axis="collision_mitigation_relief",
            repair_source_kind="mitigation_isolation_check",
            parent=parent,
            sequence_index=local_index,
            total_in_axis=REPAIR_AXIS_TARGETS["collision_mitigation_relief"],
        )
        base.update(
            {
                "obstacle_distance_delta": (2.0, 4.0, 6.0, 8.0)[local_index % 4],
                "obstacle_half_width_delta": (-0.05, -0.10, -0.15, -0.20)[(local_index // 4) % 4],
                "post_obstacle_track_width_delta": (0.0, 0.25)[(local_index // 2) % 2],
                "reaction_distance_delta": (2.0, 4.0, 6.0, 8.0)[local_index % 4],
                "recovery_corridor_profile": "collision_mitigation_relief",
                "collision_severity_relief_delta": (0.05, 0.10, 0.15, 0.20)[(local_index // 4) % 4],
                "mitigation_metric_mode": "severity_band",
            }
        )
        output.append(base)
    return output


def _mitigation_metric_isolation_rows(rows: Sequence[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if _field(row, "repair_source_kind") == "mitigation_isolation_check"
        or _field(row, "source_role_semantics") == "unavoidable_mitigation"
        or _field(row, "sampled_obstacle_label") == "unavoidable"
    ]
    output: list[dict[str, Any]] = []
    for local_index in range(REPAIR_AXIS_TARGETS["mitigation_metric_isolation"]):
        parent = _cycle_pick(eligible, local_index, description="mitigation_metric_isolation")
        base = _base_candidate(
            index=start_index + local_index,
            repair_axis="mitigation_metric_isolation",
            repair_source_kind="mitigation_isolation_check",
            parent=parent,
            sequence_index=local_index,
            total_in_axis=REPAIR_AXIS_TARGETS["mitigation_metric_isolation"],
        )
        base.update(
            {
                "obstacle_distance_delta": (0.0, 2.0)[local_index % 2],
                "obstacle_half_width_delta": 0.0,
                "post_obstacle_track_width_delta": 0.0,
                "reaction_distance_delta": (0.0, 2.0)[local_index % 2],
                "recovery_corridor_profile": "mitigation_metric_isolation",
                "collision_severity_relief_delta": 0.0,
                "mitigation_metric_mode": "diagnostic_only",
            }
        )
        output.append(base)
    return output


def _summary(candidate_rows: list[dict[str, Any]], *, output_path: Path, next_blocker: str) -> dict[str, Any]:
    axis_counts = Counter(str(row["repair_axis"]) for row in candidate_rows)
    split_counts = Counter(str(row["source_split"]) for row in candidate_rows)
    guardrail_violation_count = sum(
        1 for row in candidate_rows for field in FORBIDDEN_BOOL_FIELDS if _bool(row.get(field))
    )
    result_passes = (
        len(candidate_rows) == 192
        and dict(axis_counts) == REPAIR_AXIS_TARGETS
        and dict(split_counts) == SPLIT_TARGETS
        and guardrail_violation_count == 0
    )
    return {
        "result_class": (
            "task_quality_calibrated_outcome_support_repair_templates_pass"
            if result_passes
            else "task_quality_calibrated_outcome_support_repair_templates_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "template_id": TEMPLATE_ID,
        "repair_branch_id": REPAIR_BRANCH_ID,
        "output_path": str(output_path),
        "candidate_source_count": len(candidate_rows),
        "target_candidate_source_count": 192,
        "repair_axis_counts": dict(sorted(axis_counts.items())),
        "target_repair_axis_counts": REPAIR_AXIS_TARGETS,
        "source_split_counts": dict(sorted(split_counts.items())),
        "target_source_split_counts": SPLIT_TARGETS,
        "paper_holdout_candidate_count": sum(1 for row in candidate_rows if _bool(row.get("paper_holdout_candidate"))),
        "labels_enter_actor_input_count": sum(1 for row in candidate_rows if _bool(row.get("labels_enter_actor_input"))),
        "v2_ranking_admissible_by_default_count": sum(
            1 for row in candidate_rows if _bool(row.get("v2_ranking_admissible_by_default"))
        ),
        "profile_specific_tuning_count": sum(1 for row in candidate_rows if _bool(row.get("profile_specific_tuning"))),
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
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
        "guardrail_violation_count": guardrail_violation_count,
        "next_blocker": next_blocker,
    }


def build_repair_template_artifact(
    *,
    localization_summary_path: Path | str = DEFAULT_LOCALIZATION_SUMMARY,
    output_path: Path | str = DEFAULT_OUTPUT,
    next_blocker: str = "m1981-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-result-audit",
) -> dict[str, Any]:
    localization_summary = read_json(localization_summary_path)
    success_rows = read_csv_rows(_artifact_path(localization_summary, "success_source_rows"))
    offtrack_rows = read_csv_rows(_artifact_path(localization_summary, "offtrack_dominance_rows"))
    collision_rows = read_csv_rows(_artifact_path(localization_summary, "collision_dominance_rows"))

    rows: list[dict[str, Any]] = []
    rows.extend(_offtrack_anchor_relief_rows(offtrack_rows, start_index=len(rows)))
    rows.extend(_offtrack_boundary_relief_extension_rows(offtrack_rows, start_index=len(rows)))
    rows.extend(_success_support_expansion_rows(success_rows, start_index=len(rows)))
    rows.extend(_collision_mitigation_relief_rows(collision_rows, start_index=len(rows)))
    rows.extend(_mitigation_metric_isolation_rows(collision_rows, start_index=len(rows)))

    ids = [str(row["repair_candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("repair_candidate_id values must be unique")

    output = Path(output_path)
    artifact = {
        "summary": _summary(rows, output_path=output, next_blocker=next_blocker),
        "repair_candidate_sources": rows,
    }
    write_json(output, artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--localization-summary", type=Path, default=DEFAULT_LOCALIZATION_SUMMARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--next-blocker",
        default="m1981-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-result-audit",
    )
    args = parser.parse_args()
    artifact = build_repair_template_artifact(
        localization_summary_path=args.localization_summary,
        output_path=args.output,
        next_blocker=str(args.next_blocker),
    )
    summary = artifact["summary"]
    print(f"output={args.output}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_source_count={summary['candidate_source_count']}")
    print(f"repair_axis_counts={summary['repair_axis_counts']}")
    print(f"source_split_counts={summary['source_split_counts']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
