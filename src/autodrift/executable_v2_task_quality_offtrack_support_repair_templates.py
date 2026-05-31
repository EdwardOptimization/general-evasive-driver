"""Deterministic no-rollout templates for offtrack-support task repair."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_json


REPAIR_BRANCH_ID = "paper_route_task_quality_offtrack_support_repair"
TEMPLATE_ID = "executable_v2_task_quality_offtrack_support_repair_candidates_v0"
DEFAULT_SUCCESS_SOURCE_ROWS = Path("runs/m1942_executable_v2_task_quality_measured_outcome_localization/success_source_rows.csv")
DEFAULT_COMPARISON_SUPPORT_CANDIDATES = Path(
    "runs/m1942_executable_v2_task_quality_measured_outcome_localization/comparison_support_candidates.csv"
)
DEFAULT_OFFTRACK_DOMINANCE_ROWS = Path(
    "runs/m1942_executable_v2_task_quality_measured_outcome_localization/offtrack_dominance_rows.csv"
)
DEFAULT_OUTPUT = Path("configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json")
SOURCE_KIND_TARGETS = {
    "anchor_neighborhood": 64,
    "success_stabilizer": 48,
    "offtrack_boundary_relief": 32,
    "mitigation_isolation_check": 16,
}
SPLIT_TARGETS = {"public_debug": 96, "public_gate": 64}
FORBIDDEN_BOOL_FIELDS = (
    "labels_enter_actor_input",
    "v2_ranking_admissible_by_default",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
SPEED_RE = re.compile(r"_v(?P<speed>\d+(?:p\d+)?)_mu(?P<mu>\d+(?:p\d+)?)")


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


def _speed_mu_from_id(source_id: str, *, default_speed: float = 18.0, default_mu: float = 0.40) -> tuple[float, float]:
    match = SPEED_RE.search(source_id)
    if match is None:
        return default_speed, default_mu
    return _float(match.group("speed"), default_speed), _float(match.group("mu"), default_mu)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _cycle_pick(rows: Sequence[Mapping[str, Any]], index: int, *, description: str) -> Mapping[str, Any]:
    if not rows:
        raise ValueError(f"no rows available for {description}")
    return rows[index % len(rows)]


def _split_for_index(index: int) -> str:
    return "public_debug" if index < SPLIT_TARGETS["public_debug"] else "public_gate"


def _parent_source_id(row: Mapping[str, Any], fallback: str) -> str:
    for key in ("candidate_source_id", "parent_candidate_source_id", "task_source_id"):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return fallback


def _profile_from_support_row(row: Mapping[str, Any]) -> str:
    profiles = [item for item in str(row.get("profiles_with_success", "")).split(";") if item]
    return profiles[0] if profiles else str(row.get("profile_name", "slice_anchor"))


def _base_candidate(
    *,
    index: int,
    source_kind: str,
    parent: Mapping[str, Any],
    sequence_index: int,
    total_in_kind: int,
) -> dict[str, Any]:
    fallback_id = f"{source_kind}_{sequence_index:03d}"
    parent_source = _parent_source_id(parent, fallback_id)
    speed, mu = _speed_mu_from_id(parent_source)
    parent_profile = str(parent.get("profile_name", "")) or _profile_from_support_row(parent)
    tier = str(parent.get("feasibility_tier_id", ""))
    role = str(parent.get("source_role_semantics", ""))
    surface = str(parent.get("surface_variant", ""))
    label = str(parent.get("sampled_obstacle_label", ""))
    family_payload = {
        "source_kind": source_kind,
        "tier": tier,
        "role": role,
        "surface": surface,
        "label": label,
    }
    return {
        "template_id": TEMPLATE_ID,
        "repair_branch_id": REPAIR_BRANCH_ID,
        "repair_candidate_id": f"otsr_v0_{index:04d}_{source_kind}",
        "repair_source_family": _stable_hash(family_payload),
        "repair_source_kind": source_kind,
        "repair_sequence_index": int(sequence_index),
        "repair_kind_target_count": int(total_in_kind),
        "parent_candidate_source_id": parent_source,
        "parent_task_source_id": str(parent.get("task_source_id", parent_source)),
        "parent_profile_name": parent_profile,
        "parent_feasibility_tier_id": tier,
        "parent_source_role_semantics": role,
        "parent_surface_variant": surface,
        "parent_sampled_obstacle_label": label,
        "parent_outcome_bucket": str(parent.get("outcome_bucket", "")),
        "parent_termination_reason": str(parent.get("termination_reason", "")),
        "feasibility_tier_id": tier,
        "source_role_semantics": role,
        "surface_variant": surface,
        "sampled_obstacle_label": label,
        "source_split": _split_for_index(index),
        "paper_holdout_candidate": False,
        "speed_ref": speed,
        "mu": mu,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _anchor_neighborhood_rows(rows: Sequence[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    post_width = (0.25, 0.50, 0.75, 1.00)
    reaction = (2.0, 4.0, 6.0, 8.0)
    half_width = (0.0, -0.10)
    for local_index in range(SOURCE_KIND_TARGETS["anchor_neighborhood"]):
        parent = _cycle_pick(rows, local_index // 32, description="anchor_neighborhood")
        within_anchor = local_index % 32
        base = _base_candidate(
            index=start_index + local_index,
            source_kind="anchor_neighborhood",
            parent=parent,
            sequence_index=local_index,
            total_in_kind=SOURCE_KIND_TARGETS["anchor_neighborhood"],
        )
        base.update(
            {
                "obstacle_distance_delta": reaction[(within_anchor // 8) % len(reaction)],
                "reaction_distance_delta": reaction[(within_anchor // 8) % len(reaction)],
                "obstacle_half_width_delta": half_width[within_anchor % len(half_width)],
                "post_obstacle_track_width_delta": post_width[(within_anchor // 2) % len(post_width)],
                "recovery_corridor_profile": "bounded_anchor_relief",
                "offtrack_repair_mode": "anchor_neighborhood_geometry_relief",
            }
        )
        output.append(base)
    return output


def _success_stabilizer_rows(rows: Sequence[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if str(row.get("feasibility_tier_id", "")) in {
            "tier_b_feasible_emergency",
            "tier_c_boundary_near_miss",
            "tier_d_handling_limit_drift_required",
        }
    ]
    output: list[dict[str, Any]] = []
    for local_index in range(SOURCE_KIND_TARGETS["success_stabilizer"]):
        parent = _cycle_pick(eligible, local_index, description="success_stabilizer")
        base = _base_candidate(
            index=start_index + local_index,
            source_kind="success_stabilizer",
            parent=parent,
            sequence_index=local_index,
            total_in_kind=SOURCE_KIND_TARGETS["success_stabilizer"],
        )
        base.update(
            {
                "obstacle_distance_delta": (0.0, 2.0, 4.0)[local_index % 3],
                "reaction_distance_delta": (0.0, 2.0)[local_index % 2],
                "obstacle_half_width_delta": (0.0, -0.05)[(local_index // 2) % 2],
                "post_obstacle_track_width_delta": (0.0, 0.25, 0.50)[(local_index // 4) % 3],
                "recovery_corridor_profile": "preserve_existing_success",
                "offtrack_repair_mode": "success_stabilizer_neighborhood",
            }
        )
        output.append(base)
    return output


def _offtrack_boundary_relief_rows(rows: Sequence[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if _float(row.get("offtrack_outcome_rate", 0.0), 0.0) >= 0.80
        and _float(row.get("collision_rate", 1.0), 1.0) <= 0.20
        and str(row.get("source_role_semantics", "")) != ""
    ]
    output: list[dict[str, Any]] = []
    for local_index in range(SOURCE_KIND_TARGETS["offtrack_boundary_relief"]):
        parent = _cycle_pick(eligible, local_index, description="offtrack_boundary_relief")
        base = _base_candidate(
            index=start_index + local_index,
            source_kind="offtrack_boundary_relief",
            parent=parent,
            sequence_index=local_index,
            total_in_kind=SOURCE_KIND_TARGETS["offtrack_boundary_relief"],
        )
        base.update(
            {
                "obstacle_distance_delta": (4.0, 6.0, 8.0, 10.0)[local_index % 4],
                "reaction_distance_delta": (4.0, 6.0, 8.0, 10.0)[local_index % 4],
                "obstacle_half_width_delta": (-0.10, -0.20)[(local_index // 2) % 2],
                "post_obstacle_track_width_delta": (0.50, 0.75, 1.00)[(local_index // 4) % 3],
                "recovery_corridor_profile": "offtrack_boundary_relief",
                "offtrack_repair_mode": "reduce_offtrack_saturation",
            }
        )
        output.append(base)
    return output


def _mitigation_isolation_rows(rows: Sequence[Mapping[str, Any]], *, start_index: int) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if str(row.get("feasibility_tier_id", "")) == "tier_e_mitigation_only"
        or str(row.get("sampled_obstacle_label", "")) == "unavoidable"
    ]
    output: list[dict[str, Any]] = []
    for local_index in range(SOURCE_KIND_TARGETS["mitigation_isolation_check"]):
        parent = _cycle_pick(eligible, local_index, description="mitigation_isolation_check")
        base = _base_candidate(
            index=start_index + local_index,
            source_kind="mitigation_isolation_check",
            parent=parent,
            sequence_index=local_index,
            total_in_kind=SOURCE_KIND_TARGETS["mitigation_isolation_check"],
        )
        base.update(
            {
                "obstacle_distance_delta": (0.0, 2.0)[local_index % 2],
                "reaction_distance_delta": (0.0, 2.0)[local_index % 2],
                "obstacle_half_width_delta": 0.0,
                "post_obstacle_track_width_delta": (0.0, 0.25)[(local_index // 2) % 2],
                "recovery_corridor_profile": "mitigation_isolation",
                "offtrack_repair_mode": "isolate_mitigation_not_success_ranking",
            }
        )
        output.append(base)
    return output


def _summary(candidate_rows: list[dict[str, Any]], *, output_path: Path) -> dict[str, Any]:
    source_kind_counts = Counter(str(row["repair_source_kind"]) for row in candidate_rows)
    split_counts = Counter(str(row["source_split"]) for row in candidate_rows)
    guardrail_violation_count = sum(
        1
        for row in candidate_rows
        for field in FORBIDDEN_BOOL_FIELDS
        if _bool(row.get(field))
    )
    return {
        "result_class": (
            "task_quality_offtrack_support_repair_templates_pass"
            if len(candidate_rows) == 160
            and dict(source_kind_counts) == SOURCE_KIND_TARGETS
            and dict(split_counts) == SPLIT_TARGETS
            and guardrail_violation_count == 0
            else "task_quality_offtrack_support_repair_templates_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "template_id": TEMPLATE_ID,
        "repair_branch_id": REPAIR_BRANCH_ID,
        "output_path": str(output_path),
        "candidate_source_count": len(candidate_rows),
        "target_candidate_source_count": 160,
        "source_kind_counts": dict(sorted(source_kind_counts.items())),
        "target_source_kind_counts": SOURCE_KIND_TARGETS,
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
    }


def build_repair_template_artifact(
    *,
    success_source_rows_path: Path | str = DEFAULT_SUCCESS_SOURCE_ROWS,
    comparison_support_candidates_path: Path | str = DEFAULT_COMPARISON_SUPPORT_CANDIDATES,
    offtrack_dominance_rows_path: Path | str = DEFAULT_OFFTRACK_DOMINANCE_ROWS,
    output_path: Path | str = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    success_rows = read_csv_rows(success_source_rows_path)
    comparison_rows = read_csv_rows(comparison_support_candidates_path)
    offtrack_rows = read_csv_rows(offtrack_dominance_rows_path)

    rows: list[dict[str, Any]] = []
    rows.extend(_anchor_neighborhood_rows(comparison_rows, start_index=len(rows)))
    rows.extend(_success_stabilizer_rows(success_rows, start_index=len(rows)))
    rows.extend(_offtrack_boundary_relief_rows(offtrack_rows, start_index=len(rows)))
    rows.extend(_mitigation_isolation_rows(success_rows, start_index=len(rows)))

    ids = [str(row["repair_candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("repair_candidate_id values must be unique")

    output = Path(output_path)
    artifact = {
        "summary": _summary(rows, output_path=output),
        "repair_candidate_sources": rows,
    }
    write_json(output, artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--success-source-rows", type=Path, default=DEFAULT_SUCCESS_SOURCE_ROWS)
    parser.add_argument("--comparison-support-candidates", type=Path, default=DEFAULT_COMPARISON_SUPPORT_CANDIDATES)
    parser.add_argument("--offtrack-dominance-rows", type=Path, default=DEFAULT_OFFTRACK_DOMINANCE_ROWS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    artifact = build_repair_template_artifact(
        success_source_rows_path=args.success_source_rows,
        comparison_support_candidates_path=args.comparison_support_candidates,
        offtrack_dominance_rows_path=args.offtrack_dominance_rows,
        output_path=args.output,
    )
    summary = artifact["summary"]
    print(f"output={args.output}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_source_count={summary['candidate_source_count']}")
    print(f"source_kind_counts={summary['source_kind_counts']}")
    print(f"source_split_counts={summary['source_split_counts']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
