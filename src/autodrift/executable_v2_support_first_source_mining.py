"""No-reset support-first source mining for executable v2 task sources."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.executable_v2_task_source_metadata_redesign import (
    BLOCK_NONE,
    BLOCK_UNSUPPORTED,
    CONTRACT_ID,
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
    SUPPORTED,
    UNSUPPORTED,
)
from autodrift.scenarios import ObstacleScenario, ObstacleScenarioConfig, classify_obstacle_scenario


ACCEPTED = "accepted"
REJECT_AEB_FEASIBLE = "aeb_feasible_rejected"
REJECT_LABEL = "label_not_allowed"
REJECT_THRESHOLD = "threshold_rejected"
REJECT_FRICTION_TIMING = "friction_timing_rejected"
REJECT_ROLE_CONTRACT = "role_contract_violation"
REJECT_RECOVERY_CONTRACT = "recovery_horizon_required_missing"
REJECT_MITIGATION_CONTRACT = "mitigation_metric_contract_missing"
FAIL_NONE = "none"
FAIL_NO_ACCEPTED = "no_accepted_cells"
FAIL_LABEL_ROLE_MISMATCH = "label_role_mismatch"
FAIL_THRESHOLD_FILTER_ONLY = "threshold_filter_only"
FAIL_FRICTION_TIMING_FILTER_ONLY = "friction_timing_filter_only"
FAIL_ROLE_CONTRACT = "role_contract_violation"
CLAIM_CONTEXTS = (
    "implementation_only",
    "project_artifact_execution",
    "result_audit",
    "branch_synthesis",
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
PROFILE_SUPPORT_FIELDS = [
    "candidate_source_id",
    "source_v1_bounded_panel_spec_id",
    "source_scenario_spec_id",
    "source_role_semantics",
    "profile_name",
    "profile_group",
    "speed_ref",
    "mu",
    "friction_step_enabled",
    "friction_step_at",
    "grid_cell_count",
    "accepted_cell_count",
    "min_accepted_cells",
    "source_support_status",
    "source_support_failure_reason",
    "accepted_distance_min",
    "accepted_distance_max",
    "accepted_half_width_min",
    "accepted_half_width_max",
    "dominant_label",
    "dominant_reject_reason",
    "label_counts",
    "reject_reason_counts",
]
ACCEPTED_CELL_FIELDS = [
    "candidate_source_id",
    "source_v1_bounded_panel_spec_id",
    "source_scenario_spec_id",
    "source_role_semantics",
    "profile_name",
    "profile_group",
    "speed_ref",
    "mu",
    "obstacle_distance",
    "obstacle_half_width",
    "label",
    "threshold_score",
    "time_to_obstacle",
    "time_after_friction_step",
    "friction_step_at",
    "accepted",
    "reject_reason",
]
MATERIALIZATION_FIELDS = [
    "support_contract_id",
    "candidate_source_id",
    "source_v1_bounded_panel_spec_id",
    "source_scenario_spec_id",
    "source_role_semantics",
    "source_required_label",
    "source_allowed_labels",
    "source_support_status",
    "source_support_evidence_artifact",
    "source_support_evidence_stage",
    "source_support_profile_count",
    "source_support_feasible_profile_count",
    "source_support_accepted_cell_count_total",
    "source_support_label_counts",
    "source_support_reject_reason_counts",
    "source_support_failure_reason",
    "materialization_admissible",
    "materialization_block_reason",
    "claim_boundary_context",
    "labels_enter_actor_input",
    "v2_ranking_admissible_by_default",
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


def _maybe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _json_counts(counts: Mapping[str, int]) -> str:
    return json.dumps(dict(sorted((str(key), int(value)) for key, value in counts.items())), sort_keys=True)


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _linspace(low: float, high: float, count: int) -> list[float]:
    count = int(count)
    if count <= 0:
        raise ValueError("grid count must be positive")
    low = float(low)
    high = float(high)
    if count == 1:
        return [low]
    if high < low:
        raise ValueError("grid range must be ordered")
    step = (high - low) / float(count - 1)
    return [low + step * index for index in range(count)]


def _source_key(row: Mapping[str, Any]) -> str:
    return str(
        row.get(
            "source_v1_bounded_panel_spec_id",
            row.get("candidate_source_id", row.get("source_scenario_spec_id", "")),
        )
    )


def _candidate_source_id(row: Mapping[str, Any]) -> str:
    return str(row.get("candidate_source_id", _source_key(row)))


def _profile_name(row: Mapping[str, Any]) -> str:
    return str(row.get("profile_name", row.get("candidate_profile_id", "profile_0")))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _dominant(counts: Mapping[str, int], *, exclude: set[str] | None = None) -> str:
    exclude = exclude or set()
    filtered = {key: value for key, value in counts.items() if key not in exclude}
    if not filtered:
        return ""
    return sorted(filtered.items(), key=lambda item: (-int(item[1]), str(item[0])))[0][0]


def _threshold_score(scenario: ObstacleScenario) -> float:
    required = max(float(scenario.required_lateral_offset), 1e-6)
    aes_margin = float(scenario.conventional_lateral_capacity - scenario.required_lateral_offset) / required
    drift_margin = float(scenario.drift_lateral_capacity - scenario.required_lateral_offset) / required
    return float(min(abs(aes_margin), abs(drift_margin)))


def _scenario_config(row: Mapping[str, Any]) -> ObstacleScenarioConfig:
    return ObstacleScenarioConfig(
        speed_range=(_float(row.get("speed_ref"), default=20.0), _float(row.get("speed_ref"), default=20.0)),
        mu_range=(_float(row.get("mu"), default=1.0), _float(row.get("mu"), default=1.0)),
        obstacle_distance_range=(
            _float(row.get("obstacle_distance_min"), default=16.0),
            _float(row.get("obstacle_distance_max"), default=55.0),
        ),
        obstacle_half_width_range=(
            _float(row.get("obstacle_half_width_min"), default=0.45),
            _float(row.get("obstacle_half_width_max"), default=1.15),
        ),
        ego_half_width=_float(row.get("ego_half_width"), default=0.90),
        safety_margin=_float(row.get("safety_margin"), default=0.30),
        brake_mu_fraction=_float(row.get("brake_mu_fraction"), default=0.90),
        conventional_lateral_mu_fraction=_float(row.get("conventional_lateral_mu_fraction"), default=0.42),
        drift_lateral_mu_fraction=_float(row.get("drift_lateral_mu_fraction"), default=0.85),
        gravity=_float(row.get("gravity"), default=9.81),
    )


def required_label_for_role(role: str) -> str:
    if role == ROLE_STABLE_AES:
        return "aes_feasible"
    if role == ROLE_STABLE_AEB:
        return "aeb_feasible"
    if role == ROLE_DRIFT_REQUIRED:
        return "drift_required"
    if role == ROLE_UNAVOIDABLE:
        return "unavoidable"
    return ""


def _allowed_labels_for_role(role: str) -> str:
    label = required_label_for_role(role)
    return label if label else ""


def _requires_all_profiles_supported(role: str) -> bool:
    return role in {ROLE_STABLE_AES, ROLE_STABLE_AEB}


def _role_contract_valid(row: Mapping[str, Any]) -> bool:
    role = str(row.get("source_role_semantics", ""))
    require_aeb_infeasible = _bool(row.get("require_aeb_infeasible"), default=(role == ROLE_STABLE_AES))
    if role == ROLE_STABLE_AES:
        return require_aeb_infeasible
    if role == ROLE_STABLE_AEB:
        return not require_aeb_infeasible
    if role in {ROLE_DRIFT_REQUIRED, ROLE_UNAVOIDABLE}:
        return True
    return False


def _time_after_friction_step(row: Mapping[str, Any], scenario: ObstacleScenario) -> float:
    if not _bool(row.get("friction_step_enabled"), default=False):
        return float("inf")
    friction_step_at = _maybe_float(row.get("friction_step_at"))
    if friction_step_at is None:
        return float("-inf")
    dt = _float(row.get("dt"), default=0.05)
    return float(scenario.time_to_obstacle - friction_step_at * dt)


def evaluate_candidate_cell(
    *,
    candidate: Mapping[str, Any],
    obstacle_distance: float,
    obstacle_half_width: float,
) -> dict[str, Any]:
    role = str(candidate.get("source_role_semantics", ""))
    required_label = required_label_for_role(role)
    speed_ref = _float(candidate.get("speed_ref"), default=20.0)
    mu = _float(candidate.get("mu"), default=1.0)
    scenario = classify_obstacle_scenario(
        speed=speed_ref,
        mu=mu,
        obstacle_distance=float(obstacle_distance),
        obstacle_half_width=float(obstacle_half_width),
        config=_scenario_config(candidate),
    )
    threshold_score = _threshold_score(scenario)
    max_threshold_score = _maybe_float(candidate.get("max_threshold_score"))
    is_near_threshold = max_threshold_score is None or threshold_score <= max_threshold_score
    time_after_step = _time_after_friction_step(candidate, scenario)
    min_time_after_step = _float(candidate.get("min_time_after_friction_step"), default=0.0)
    has_time_after_step = time_after_step >= min_time_after_step

    if not _role_contract_valid(candidate):
        reject_reason = REJECT_ROLE_CONTRACT
    elif scenario.label != required_label:
        if role == ROLE_STABLE_AES and scenario.label == "aeb_feasible":
            reject_reason = REJECT_AEB_FEASIBLE
        else:
            reject_reason = REJECT_LABEL
    elif not is_near_threshold:
        reject_reason = REJECT_THRESHOLD
    elif not has_time_after_step:
        reject_reason = REJECT_FRICTION_TIMING
    elif role == ROLE_DRIFT_REQUIRED and not _bool(candidate.get("recovery_horizon_required"), default=False):
        reject_reason = REJECT_RECOVERY_CONTRACT
    elif role == ROLE_UNAVOIDABLE and not _bool(candidate.get("mitigation_metric_contract_present"), default=False):
        reject_reason = REJECT_MITIGATION_CONTRACT
    else:
        reject_reason = ACCEPTED

    return {
        "speed_ref": speed_ref,
        "mu": mu,
        "obstacle_distance": float(obstacle_distance),
        "obstacle_half_width": float(obstacle_half_width),
        "label": scenario.label,
        "threshold_score": float(threshold_score),
        "time_to_obstacle": float(scenario.time_to_obstacle),
        "time_after_friction_step": float(time_after_step),
        "friction_step_at": candidate.get("friction_step_at", ""),
        "accepted": reject_reason == ACCEPTED,
        "reject_reason": reject_reason,
    }


def _failure_reason(
    *,
    accepted_count: int,
    label_counts: Mapping[str, int],
    reject_counts: Mapping[str, int],
    required_label: str,
) -> str:
    if int(accepted_count) > 0:
        return FAIL_NONE
    if int(label_counts.get(required_label, 0)) <= 0:
        return FAIL_LABEL_ROLE_MISMATCH
    if int(reject_counts.get(REJECT_THRESHOLD, 0)) > 0 and len(reject_counts) == 1:
        return FAIL_THRESHOLD_FILTER_ONLY
    if int(reject_counts.get(REJECT_FRICTION_TIMING, 0)) > 0 and len(reject_counts) == 1:
        return FAIL_FRICTION_TIMING_FILTER_ONLY
    if int(reject_counts.get(REJECT_ROLE_CONTRACT, 0)) > 0:
        return FAIL_ROLE_CONTRACT
    return FAIL_NO_ACCEPTED


def scan_candidate_profile(
    *,
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    role = str(candidate.get("source_role_semantics", ""))
    source = _source_key(candidate)
    candidate_id = _candidate_source_id(candidate)
    required_label = required_label_for_role(role)
    distance_values = _linspace(
        _float(candidate.get("obstacle_distance_min"), default=16.0),
        _float(candidate.get("obstacle_distance_max"), default=55.0),
        _int(candidate.get("obstacle_distance_count"), default=1),
    )
    half_width_values = _linspace(
        _float(candidate.get("obstacle_half_width_min"), default=0.45),
        _float(candidate.get("obstacle_half_width_max"), default=1.15),
        _int(candidate.get("obstacle_half_width_count"), default=1),
    )
    metadata = {
        "candidate_source_id": candidate_id,
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": candidate.get("source_scenario_spec_id", f"{source}_scenario"),
        "source_role_semantics": role,
        "profile_name": _profile_name(candidate),
        "profile_group": candidate.get("profile_group", ""),
        "speed_ref": _float(candidate.get("speed_ref"), default=20.0),
        "mu": _float(candidate.get("mu"), default=1.0),
        "friction_step_enabled": _bool(candidate.get("friction_step_enabled"), default=False),
        "friction_step_at": candidate.get("friction_step_at", ""),
    }
    min_accepted_cells = max(1, _int(candidate.get("min_accepted_cells"), default=1))
    label_counts: Counter[str] = Counter()
    reject_counts: Counter[str] = Counter()
    accepted_cells: list[dict[str, Any]] = []
    grid_cell_count = 0
    for distance in distance_values:
        for half_width in half_width_values:
            grid_cell_count += 1
            cell = evaluate_candidate_cell(
                candidate=candidate,
                obstacle_distance=float(distance),
                obstacle_half_width=float(half_width),
            )
            label_counts[str(cell["label"])] += 1
            reject_counts[str(cell["reject_reason"])] += 1
            if bool(cell["accepted"]):
                accepted_cells.append({**metadata, **cell})

    accepted_distance = [float(row["obstacle_distance"]) for row in accepted_cells]
    accepted_half_width = [float(row["obstacle_half_width"]) for row in accepted_cells]
    support_status = SUPPORTED if len(accepted_cells) >= min_accepted_cells else UNSUPPORTED
    failure = _failure_reason(
        accepted_count=len(accepted_cells),
        label_counts=label_counts,
        reject_counts=reject_counts,
        required_label=required_label,
    )
    profile_support = {
        **metadata,
        "grid_cell_count": int(grid_cell_count),
        "accepted_cell_count": len(accepted_cells),
        "min_accepted_cells": int(min_accepted_cells),
        "source_support_status": support_status,
        "source_support_failure_reason": failure,
        "accepted_distance_min": min(accepted_distance) if accepted_distance else "",
        "accepted_distance_max": max(accepted_distance) if accepted_distance else "",
        "accepted_half_width_min": min(accepted_half_width) if accepted_half_width else "",
        "accepted_half_width_max": max(accepted_half_width) if accepted_half_width else "",
        "dominant_label": _dominant(label_counts),
        "dominant_reject_reason": _dominant(reject_counts, exclude={ACCEPTED}),
        "label_counts": _json_counts(label_counts),
        "reject_reason_counts": _json_counts(reject_counts),
    }
    return {
        "profile_support": profile_support,
        "accepted_cells": accepted_cells,
        "label_counts": dict(label_counts),
        "reject_counts": dict(reject_counts),
    }


def build_materialization_rows(
    *,
    profile_support_rows: Iterable[Mapping[str, Any]],
    support_evidence_artifact: str,
    support_evidence_stage: str,
    claim_boundary_context: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in profile_support_rows:
        grouped[(_source_key(row), str(row.get("source_role_semantics", "")))].append(row)

    output: list[dict[str, Any]] = []
    for (source, role), rows in sorted(grouped.items()):
        feasible_profiles = sum(str(row.get("source_support_status", "")) == SUPPORTED for row in rows)
        profile_count = len(rows)
        accepted_total = sum(_int(row.get("accepted_cell_count")) for row in rows)
        label_counts: Counter[str] = Counter()
        reject_counts: Counter[str] = Counter()
        failures: Counter[str] = Counter()
        for row in rows:
            label_counts.update(json.loads(str(row.get("label_counts", "{}"))))
            reject_counts.update(json.loads(str(row.get("reject_reason_counts", "{}"))))
            failures[str(row.get("source_support_failure_reason", ""))] += 1
        source_supported = (
            feasible_profiles == profile_count
            if _requires_all_profiles_supported(role)
            else feasible_profiles > 0
        )
        failure = FAIL_NONE if source_supported else _dominant(failures, exclude={FAIL_NONE})
        output.append(
            {
                "support_contract_id": CONTRACT_ID,
                "candidate_source_id": rows[0].get("candidate_source_id", source),
                "source_v1_bounded_panel_spec_id": source,
                "source_scenario_spec_id": rows[0].get("source_scenario_spec_id", ""),
                "source_role_semantics": role,
                "source_required_label": required_label_for_role(role),
                "source_allowed_labels": _allowed_labels_for_role(role),
                "source_support_status": SUPPORTED if source_supported else UNSUPPORTED,
                "source_support_evidence_artifact": support_evidence_artifact,
                "source_support_evidence_stage": support_evidence_stage,
                "source_support_profile_count": int(profile_count),
                "source_support_feasible_profile_count": int(feasible_profiles),
                "source_support_accepted_cell_count_total": int(accepted_total),
                "source_support_label_counts": _json_counts(label_counts),
                "source_support_reject_reason_counts": _json_counts(reject_counts),
                "source_support_failure_reason": failure,
                "materialization_admissible": bool(source_supported),
                "materialization_block_reason": BLOCK_NONE if source_supported else BLOCK_UNSUPPORTED,
                "claim_boundary_context": claim_boundary_context,
                "labels_enter_actor_input": False,
                "v2_ranking_admissible_by_default": False,
            }
        )
    return output


def role_summary_rows(materialization_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in materialization_rows:
        grouped[str(row.get("source_role_semantics", ""))].append(row)
    rows: list[dict[str, Any]] = []
    for role, items in sorted(grouped.items()):
        rows.append(
            {
                "source_role_semantics": role,
                "candidate_source_count": len(items),
                "supported_source_count": sum(_bool(row.get("materialization_admissible")) for row in items),
                "blocked_source_count": sum(not _bool(row.get("materialization_admissible")) for row in items),
                "accepted_cell_count_total": sum(_int(row.get("source_support_accepted_cell_count_total")) for row in items),
            }
        )
    return rows


def claim_boundary_rows(context: str = "implementation_only") -> list[dict[str, Any]]:
    if context not in CLAIM_CONTEXTS:
        raise ValueError(f"unknown claim boundary context: {context}")
    project_execution = context == "project_artifact_execution"
    result_audit = context in {"result_audit", "branch_synthesis"}
    return [
        {
            "claim_context": context,
            "claim": "support_first_source_mining_helper",
            "admissible": context == "implementation_only",
            "reason": "helper implementation is admissible only in implementation context",
        },
        {
            "claim_context": context,
            "claim": "project_artifact_source_mining_result",
            "admissible": project_execution,
            "reason": "project artifact source mining requires an execution milestone",
        },
        {
            "claim_context": context,
            "claim": "result_audit",
            "admissible": result_audit,
            "reason": "result claims require audit or synthesis context",
        },
        {
            "claim_context": context,
            "claim": "materialized_executable_v2_rows_generated",
            "admissible": False,
            "reason": "source mining evidence must precede materialization",
        },
        {
            "claim_context": context,
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "source mining is task-quality infrastructure, not ranking evidence",
        },
    ]


def diversity_summary(candidate_rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(candidate_rows)
    source_families = Counter(str(row.get("source_family_id", "")) for row in rows)
    profile_groups = Counter(str(row.get("profile_group", "")) for row in rows)
    roles = Counter(str(row.get("source_role_semantics", "")) for row in rows)
    speeds = Counter(int(_float(row.get("speed_ref"), default=0.0) // 5.0) for row in rows)
    mus = Counter(int(_float(row.get("mu"), default=0.0) // 0.2) for row in rows)
    return {
        "source_family_count": len(source_families),
        "profile_group_count": len(profile_groups),
        "role_count": len(roles),
        "speed_bucket_count": len(speeds),
        "mu_bucket_count": len(mus),
        "max_source_family_share": max(source_families.values(), default=0) / max(1, len(rows)),
        "max_profile_group_share": max(profile_groups.values(), default=0) / max(1, len(rows)),
    }


def load_candidate_rows(path: Path | str) -> list[dict[str, Any]]:
    source = Path(path)
    if source.suffix.lower() == ".json":
        payload = read_json(source)
        if isinstance(payload, list):
            return [dict(row) for row in payload]
        return [dict(row) for row in payload.get("candidate_sources", [])]
    return _read_csv_rows(source)


def run_support_first_source_mining(
    *,
    candidate_rows: list[Mapping[str, Any]],
    output_dir: Path | str,
    support_evidence_artifact: str = "",
    support_evidence_stage: str = "pre_materialization_source_mining",
    claim_boundary_context: str = "implementation_only",
    next_blocker: str = "m1853-executable-v2-support-first-source-mining-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    profile_support_rows: list[dict[str, Any]] = []
    accepted_cells: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        scanned = scan_candidate_profile(candidate=candidate)
        profile_support_rows.append(scanned["profile_support"])
        accepted_cells.extend(scanned["accepted_cells"])

    materialization_rows = build_materialization_rows(
        profile_support_rows=profile_support_rows,
        support_evidence_artifact=support_evidence_artifact or str(output / "support_first_profile_support.csv"),
        support_evidence_stage=support_evidence_stage,
        claim_boundary_context=claim_boundary_context,
    )
    blocked_rows = [row for row in materialization_rows if not _bool(row.get("materialization_admissible"))]
    role_rows = role_summary_rows(materialization_rows)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    diversity = diversity_summary(candidate_rows)
    role_supported = {
        role: sum(
            _bool(row.get("materialization_admissible"))
            for row in materialization_rows
            if str(row.get("source_role_semantics", "")) == role
        )
        for role in (ROLE_STABLE_AES, ROLE_STABLE_AEB, ROLE_DRIFT_REQUIRED, ROLE_UNAVOIDABLE)
    }

    write_csv_rows(output / "support_first_source_candidates.csv", [dict(row) for row in candidate_rows])
    write_csv_rows(output / "support_first_profile_support.csv", profile_support_rows, fieldnames=PROFILE_SUPPORT_FIELDS)
    write_csv_rows(output / "support_first_accepted_cells.csv", accepted_cells, fieldnames=ACCEPTED_CELL_FIELDS)
    write_csv_rows(output / "support_first_blocked_candidates.csv", blocked_rows, fieldnames=MATERIALIZATION_FIELDS)
    write_csv_rows(output / "support_first_role_summary.csv", role_rows)
    write_csv_rows(
        output / "support_first_materialization_admissibility_input.csv",
        materialization_rows,
        fieldnames=MATERIALIZATION_FIELDS,
    )
    write_csv_rows(output / "support_first_claim_boundary.csv", claim_boundary_rows(claim_boundary_context))

    summary = {
        "contract_id": CONTRACT_ID,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "support_evidence_artifact": support_evidence_artifact,
        "support_evidence_stage": support_evidence_stage,
        "claim_boundary_context": claim_boundary_context,
        "candidate_source_count": len(materialization_rows),
        "candidate_profile_count": len(profile_support_rows),
        "role_count": len({str(row.get("source_role_semantics", "")) for row in materialization_rows}),
        "supported_source_count": sum(_bool(row.get("materialization_admissible")) for row in materialization_rows),
        "unsupported_source_count": len(blocked_rows),
        "blocked_candidate_count": len(blocked_rows),
        "accepted_cell_count_total": len(accepted_cells),
        "stable_aes_supported_source_count": int(role_supported.get(ROLE_STABLE_AES, 0)),
        "stable_aeb_supported_source_count": int(role_supported.get(ROLE_STABLE_AEB, 0)),
        "drift_required_supported_source_count": int(role_supported.get(ROLE_DRIFT_REQUIRED, 0)),
        "unavoidable_supported_source_count": int(role_supported.get(ROLE_UNAVOIDABLE, 0)),
        "labels_enter_actor_input_count": 0,
        "materialized_row_count": 0,
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
        "diversity": diversity,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "source_candidates": str(output / "support_first_source_candidates.csv"),
            "profile_support": str(output / "support_first_profile_support.csv"),
            "accepted_cells": str(output / "support_first_accepted_cells.csv"),
            "blocked_candidates": str(output / "support_first_blocked_candidates.csv"),
            "role_summary": str(output / "support_first_role_summary.csv"),
            "materialization_admissibility_input": str(
                output / "support_first_materialization_admissibility_input.csv"
            ),
            "claim_boundary": str(output / "support_first_claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def run_support_first_source_mining_from_paths(
    *,
    candidate_rows_path: Path | str,
    output_dir: Path | str,
    support_evidence_artifact: str = "",
    support_evidence_stage: str = "pre_materialization_source_mining",
    claim_boundary_context: str = "project_artifact_execution",
    next_blocker: str = "m1853-executable-v2-support-first-source-mining-execution-design",
) -> dict[str, Any]:
    return run_support_first_source_mining(
        candidate_rows=load_candidate_rows(candidate_rows_path),
        output_dir=output_dir,
        support_evidence_artifact=support_evidence_artifact,
        support_evidence_stage=support_evidence_stage,
        claim_boundary_context=claim_boundary_context,
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-rows", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--support-evidence-artifact", default="")
    parser.add_argument("--support-evidence-stage", default="pre_materialization_source_mining")
    parser.add_argument("--claim-boundary-context", default="project_artifact_execution")
    parser.add_argument("--next-blocker", default="m1853-executable-v2-support-first-source-mining-execution-design")
    args = parser.parse_args()
    summary = run_support_first_source_mining_from_paths(
        candidate_rows_path=args.candidate_rows,
        output_dir=args.output_dir,
        support_evidence_artifact=args.support_evidence_artifact,
        support_evidence_stage=str(args.support_evidence_stage),
        claim_boundary_context=str(args.claim_boundary_context),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"contract_id={summary['contract_id']}")
    print(f"candidate_source_count={summary['candidate_source_count']}")
    print(f"supported_source_count={summary['supported_source_count']}")
    print(f"materialized_row_count={summary['materialized_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
