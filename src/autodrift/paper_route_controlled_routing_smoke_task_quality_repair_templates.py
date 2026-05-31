"""Deterministic no-rollout repair templates for routing-smoke task quality."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_json


REPAIR_BRANCH_ID = "paper_route_controlled_routing_smoke_task_quality_repair"
TEMPLATE_ID = "paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0"
DEFAULT_LOCALIZATION_SUMMARY = Path("runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/summary.json")
DEFAULT_OUTPUT = Path("configs/paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0.json")
DEFAULT_NEXT_BLOCKER = "m2046-paper-route-controlled-routing-smoke-task-quality-repair-template-result-audit"

REPAIR_AXIS_TARGETS = {
    "l2_offtrack_relief": 64,
    "family_offtrack_relief": 48,
    "zero_success_source_kind_relief": 40,
    "success_neighborhood_expansion": 24,
    "generated_proxy_support_check": 16,
}
SPLIT_TARGETS = {"public_debug": 112, "public_gate": 80}
FORBIDDEN_BOOL_FIELDS = (
    "labels_enter_actor_input",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
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


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return int(default)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return float(default)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


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


def _cycle_pick(rows: Sequence[Mapping[str, Any]], index: int, *, description: str) -> Mapping[str, Any]:
    if not rows:
        raise ValueError(f"no rows available for {description}")
    return rows[index % len(rows)]


def _split_for_index(index: int) -> str:
    return "public_debug" if index < SPLIT_TARGETS["public_debug"] else "public_gate"


def _axis_delta(repair_axis: str, local_index: int) -> dict[str, Any]:
    if repair_axis == "l2_offtrack_relief":
        return {
            "obstacle_distance_delta_m": (4.0, 6.0, 8.0, 10.0)[local_index % 4],
            "obstacle_half_width_delta_m": (0.0, -0.05, -0.10, -0.15)[(local_index // 4) % 4],
            "track_width_delta_m": (0.5, 0.75, 1.0, 1.25)[(local_index // 8) % 4],
            "warmup_reveal_step_delta": (-8, -12, -16, -20)[local_index % 4],
            "max_steps_delta": 0,
            "repair_intent": "keep_l2_profiles_on_road_long_enough_for_diagnostic_signal",
        }
    if repair_axis == "family_offtrack_relief":
        return {
            "obstacle_distance_delta_m": (3.0, 5.0, 7.0, 9.0)[local_index % 4],
            "obstacle_half_width_delta_m": (0.0, -0.05, -0.10)[(local_index // 4) % 3],
            "track_width_delta_m": (0.5, 1.0, 1.5)[(local_index // 12) % 3],
            "warmup_reveal_step_delta": -8,
            "max_steps_delta": 20 if local_index % 5 == 0 else 0,
            "repair_intent": "reduce_family_wide_offtrack_dominance",
        }
    if repair_axis == "zero_success_source_kind_relief":
        return {
            "obstacle_distance_delta_m": (5.0, 8.0, 11.0, 14.0)[local_index % 4],
            "obstacle_half_width_delta_m": (-0.05, -0.10, -0.15, -0.20)[(local_index // 4) % 4],
            "track_width_delta_m": (0.75, 1.25)[(local_index // 8) % 2],
            "warmup_reveal_step_delta": -12,
            "max_steps_delta": 20,
            "repair_intent": "turn_zero_success_source_kinds_into_reset_and_rollout_diagnostic_candidates",
        }
    if repair_axis == "success_neighborhood_expansion":
        return {
            "obstacle_distance_delta_m": (-1.0, 0.0, 1.0, 2.0)[local_index % 4],
            "obstacle_half_width_delta_m": (-0.05, 0.0, 0.05)[(local_index // 4) % 3],
            "track_width_delta_m": (0.0, 0.5)[(local_index // 12) % 2],
            "warmup_reveal_step_delta": 0,
            "max_steps_delta": 0,
            "repair_intent": "expand_near_existing_success_rows_without_making_them_ranking_admissible",
        }
    if repair_axis == "generated_proxy_support_check":
        return {
            "obstacle_distance_delta_m": (4.0, 8.0, 12.0, 16.0)[local_index % 4],
            "obstacle_half_width_delta_m": (-0.05, -0.10)[(local_index // 4) % 2],
            "track_width_delta_m": (0.5, 1.0)[(local_index // 8) % 2],
            "warmup_reveal_step_delta": -16,
            "max_steps_delta": 20,
            "repair_intent": "check_generated_smoke_proxy_support_without_paper_validity_claim",
        }
    raise ValueError(f"unknown repair axis {repair_axis}")


def _base_candidate(
    *,
    global_index: int,
    local_index: int,
    repair_axis: str,
    parent: Mapping[str, Any],
) -> dict[str, Any]:
    parent_task_source = _field(parent, "task_source_id", "sources_with_success", default=f"{repair_axis}_slice")
    parent_profile = _field(parent, "profile_name", "profiles_with_success", default="slice_level")
    parent_family = _field(parent, "panel_task_family", default="")
    parent_kind = _field(parent, "source_kind", default="")
    parent_template = _field(parent, "proxy_template_family", default="")
    parent_generated = _bool(_field(parent, "generated_source_row", default="false"))
    parent_paper_claim = _bool(_field(parent, "paper_validity_claim", default="false"))
    parent_payload = {
        "repair_axis": repair_axis,
        "parent_task_source": parent_task_source,
        "parent_profile": parent_profile,
        "parent_family": parent_family,
        "parent_kind": parent_kind,
        "parent_template": parent_template,
        "local_index": local_index,
    }
    return {
        "template_id": TEMPLATE_ID,
        "repair_branch_id": REPAIR_BRANCH_ID,
        "repair_candidate_id": f"crsr_v0_{global_index:04d}_{repair_axis}",
        "repair_axis": repair_axis,
        "repair_sequence_index": int(local_index),
        "repair_axis_target_count": int(REPAIR_AXIS_TARGETS[repair_axis]),
        "repair_source_family": _stable_hash(parent_payload),
        "source_split": _split_for_index(global_index),
        "paper_holdout_candidate": False,
        "parent_task_source_id": parent_task_source,
        "parent_panel_source_id": _field(parent, "panel_source_id", default=parent_task_source),
        "parent_profile_name": parent_profile,
        "parent_slice_kind": _field(parent, "slice_kind", default="success_row"),
        "parent_panel_task_family": parent_family,
        "parent_source_kind": parent_kind,
        "parent_proxy_template_family": parent_template,
        "parent_generated_source_row": parent_generated,
        "parent_materialization_semantics": _field(parent, "materialization_semantics", default="smoke_proxy"),
        "parent_paper_validity_claim": parent_paper_claim,
        "parent_outcome_bucket": _field(parent, "outcome_bucket", default=""),
        "parent_termination_reason": _field(parent, "termination_reason", default=""),
        "parent_success_count": _int(parent.get("success_count", 1 if _field(parent, "outcome_bucket") == "success_obstacle_pass" else 0)),
        "parent_collision_count": _int(parent.get("collision_count", 0)),
        "parent_offtrack_outcome_count": _int(parent.get("offtrack_outcome_count", 0)),
        "parent_episode_count": _int(parent.get("episode_count", 1)),
        "parent_offtrack_rate": _float(parent.get("offtrack_outcome_rate", 0.0)),
        "target_materialization_semantics": "smoke_proxy",
        "target_generated_source_row": parent_generated,
        "target_paper_validity_claim": False,
        "labels_enter_actor_input": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    } | _axis_delta(repair_axis, local_index)


def _eligible_rows(
    *,
    repair_axis: str,
    offtrack_rows: Sequence[Mapping[str, Any]],
    success_rows: Sequence[Mapping[str, Any]],
    generated_proxy_rows: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    if repair_axis == "l2_offtrack_relief":
        return [
            row
            for row in offtrack_rows
            if _field(row, "slice_kind") == "outcome_by_profile" and _field(row, "profile_name").startswith("L2_")
        ]
    if repair_axis == "family_offtrack_relief":
        return [row for row in offtrack_rows if _field(row, "slice_kind") == "outcome_by_family"]
    if repair_axis == "zero_success_source_kind_relief":
        return [
            row
            for row in offtrack_rows
            if _field(row, "slice_kind") == "outcome_by_source_kind" and _int(row.get("success_count", 0)) == 0
        ]
    if repair_axis == "success_neighborhood_expansion":
        return list(success_rows)
    if repair_axis == "generated_proxy_support_check":
        generated_rows = [
            row
            for row in generated_proxy_rows
            if _bool(_field(row, "generated_source_row", default="false"))
            and _field(row, "materialization_semantics", default="smoke_proxy") == "smoke_proxy"
        ]
        return generated_rows or [row for row in success_rows if _bool(_field(row, "generated_source_row", default="false"))]
    raise ValueError(f"unknown repair axis {repair_axis}")


def generate_routing_smoke_task_quality_repair_templates(
    *,
    localization_summary_path: Path | str = DEFAULT_LOCALIZATION_SUMMARY,
    output_path: Path | str = DEFAULT_OUTPUT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_summary = read_json(localization_summary_path)
    if source_summary.get("result_class") != "controlled_routing_smoke_outcome_localization_pass":
        raise ValueError("localization summary must be controlled_routing_smoke_outcome_localization_pass")
    offtrack_rows = read_csv_rows(_artifact_path(source_summary, "offtrack_dominance_slices"))
    success_rows = read_csv_rows(_artifact_path(source_summary, "success_rows"))
    generated_proxy_rows = read_csv_rows(_artifact_path(source_summary, "outcome_by_generated_proxy"))

    candidates: list[dict[str, Any]] = []
    for repair_axis, target_count in REPAIR_AXIS_TARGETS.items():
        eligible = _eligible_rows(
            repair_axis=repair_axis,
            offtrack_rows=offtrack_rows,
            success_rows=success_rows,
            generated_proxy_rows=generated_proxy_rows,
        )
        for local_index in range(target_count):
            parent = _cycle_pick(eligible, local_index, description=repair_axis)
            candidates.append(
                _base_candidate(
                    global_index=len(candidates),
                    local_index=local_index,
                    repair_axis=repair_axis,
                    parent=parent,
                )
            )

    repair_axis_counts = dict(sorted(Counter(str(row["repair_axis"]) for row in candidates).items()))
    split_counts = dict(sorted(Counter(str(row["source_split"]) for row in candidates).items()))
    forbidden_true_counts = {
        field: sum(1 for row in candidates if _bool(row.get(field, False))) for field in FORBIDDEN_BOOL_FIELDS
    }
    generated_proxy_paper_claim_count = sum(
        1
        for row in candidates
        if _bool(row.get("target_generated_source_row", False)) and _bool(row.get("target_paper_validity_claim", False))
    )
    quota_pass = repair_axis_counts == REPAIR_AXIS_TARGETS and split_counts == SPLIT_TARGETS
    guardrail_violation_count = sum(forbidden_true_counts.values()) + generated_proxy_paper_claim_count
    result_passes = len(candidates) == sum(REPAIR_AXIS_TARGETS.values()) and quota_pass and guardrail_violation_count == 0

    payload = {
        "result_class": (
            "controlled_routing_smoke_task_quality_repair_templates_pass"
            if result_passes
            else "controlled_routing_smoke_task_quality_repair_templates_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "template_id": TEMPLATE_ID,
        "repair_branch_id": REPAIR_BRANCH_ID,
        "source_localization_summary": str(localization_summary_path),
        "candidate_source_count": len(candidates),
        "expected_candidate_source_count": sum(REPAIR_AXIS_TARGETS.values()),
        "repair_axis_counts": repair_axis_counts,
        "expected_repair_axis_counts": REPAIR_AXIS_TARGETS,
        "source_split_counts": split_counts,
        "expected_source_split_counts": SPLIT_TARGETS,
        "quota_pass": quota_pass,
        "forbidden_true_counts": forbidden_true_counts,
        "generated_proxy_paper_claim_count": generated_proxy_paper_claim_count,
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
        "profile_specific_tuning_count": forbidden_true_counts["profile_specific_tuning"],
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "next_blocker": str(next_blocker),
        "candidates": candidates,
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--localization-summary", type=Path, default=DEFAULT_LOCALIZATION_SUMMARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    payload = generate_routing_smoke_task_quality_repair_templates(
        localization_summary_path=args.localization_summary,
        output_path=args.output,
        next_blocker=str(args.next_blocker),
    )
    print(f"output={args.output}")
    print(f"result_class={payload['result_class']}")
    print(f"candidate_source_count={payload['candidate_source_count']}")
    print(f"quota_pass={payload['quota_pass']}")
    print(f"guardrail_violation_count={payload['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
