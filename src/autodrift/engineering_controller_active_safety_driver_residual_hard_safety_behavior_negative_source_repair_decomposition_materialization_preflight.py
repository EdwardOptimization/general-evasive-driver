"""Materialize M3175 behavior-negative source repair decomposition artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3175-engineering-controller-active-safety-driver-residual-hard-safety-"
    "behavior-negative-source-repair-decomposition-materialization-preflight"
)
NEXT_ID = (
    "m3176-engineering-controller-active-safety-driver-residual-hard-safety-"
    "behavior-negative-source-repair-decomposition-result-audit"
)
M3174_ID = (
    "m3174-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-negative-measurement-synthesis"
)
M3173_ID = (
    "m3173-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-full-fresh-measurement-result-audit"
)
M3172_ID = (
    "m3172-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-full-fresh-measurement-preflight"
)
M3170_ID = (
    "m3170-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-implementation-materialization-preflight"
)
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-"
    "direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3174_SYNTHESIS = Path(f"docs/{M3174_ID}.md")
DEFAULT_M3173_AUDIT = Path(f"docs/{M3173_ID}.md")
DEFAULT_M3172_DIR = Path(
    "runs/m3172_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localized_repair_implementation_full_fresh_measurement_preflight"
)
DEFAULT_M3170_DIR = Path(
    "runs/m3170_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localized_repair_implementation_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3175_engineering_controller_active_safety_driver_residual_hard_safety_"
    "behavior_negative_source_repair_decomposition_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_FULL_ROWS = 64
EXPECTED_REGRESSION_ROWS = 1
EXPECTED_M3172_COLLISION_ROWS = 6
EXPECTED_M3172_OFFTRACK_ROWS = 2
EXPECTED_INHERITED_BLOCKER_ROWS = 7

CLAIM_SCOPE = (
    "M3175 Active Safety Driver residual hard-safety behavior-negative source repair "
    "decomposition materialization only; M3174 synthesis, M3173 audit, M3172 full-fresh "
    "measurement rows, M3172 same-row comparison rows, M3170 candidate rule rows, and "
    "M3105 incumbent rows may be reanalyzed into regression, blocker-context, "
    "repair-decomposition, contract-guard, claim-boundary, gate, doc, and M3176 audit "
    "artifacts. No reset, step, rollout, replay, policy action, fitting, PPO, training, "
    "repair implementation, validation execution, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, public driver default mutation, driver-performance "
    "verdict, current-sim verdict, repair success, robustness-result, high-fidelity "
    "validation, paper evidence, finite-window-vs-GRU evidence, full ideal driver "
    "completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)

REGRESSION_FIELDNAMES = [
    "regression_row_id",
    "measurement_episode_id",
    "baseline_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "regression_family",
    "m3172_success",
    "m3105_success",
    "success_delta_vs_m3105",
    "m3172_collision",
    "m3105_collision",
    "collision_delta_vs_m3105",
    "m3172_offtrack",
    "m3105_offtrack",
    "offtrack_delta_vs_m3105",
    "m3172_min_clearance_margin",
    "m3105_min_clearance_margin",
    "clearance_margin_delta_vs_m3105",
    "m3172_speed_mean",
    "m3105_speed_mean",
    "speed_mean_delta_vs_m3105",
    "m3172_return",
    "m3105_return",
    "return_delta_vs_m3105",
    "actor_visible_repair_hypothesis_required",
    "runtime_label_inputs_allowed",
    "decomposition_label",
    "claim_boundary",
]
BLOCKER_CONTEXT_FIELDNAMES = [
    "blocker_context_row_id",
    "measurement_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "m3172_collision",
    "m3172_offtrack",
    "m3172_termination_reason",
    "m3172_min_clearance_margin",
    "m3172_speed_mean",
    "m3105_success",
    "m3105_collision",
    "m3105_offtrack",
    "m3105_termination_reason",
    "same_row_relation_to_m3105",
    "blocker_family",
    "decomposition_need",
    "claim_boundary",
]
REPAIR_DECOMPOSITION_FIELDNAMES = [
    "repair_decomposition_row_id",
    "route_name",
    "route_role",
    "source_row_count",
    "source_rows",
    "hard_safety_focus",
    "incumbent_status",
    "admission_decision",
    "next_required_evidence",
    "actor_visible_candidate_feature_families",
    "forbidden_runtime_inputs",
    "public_driver_mutation_allowed",
    "repair_success_claim_made",
    "claim_boundary",
]
CONTRACT_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3175",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "regression_rows": output_dir / "regression_rows.csv",
        "blocker_context_rows": output_dir / "blocker_context_rows.csv",
        "repair_decomposition_rows": output_dir / "repair_decomposition_rows.csv",
        "contract_guard_rows": output_dir / "contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3174_synthesis: Path,
    m3173_audit: Path,
    m3172_dir: Path,
    m3170_dir: Path,
    m3105_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3174_synthesis": m3174_synthesis,
        "m3173_audit": m3173_audit,
        "m3172_summary": m3172_dir / "summary.json",
        "m3172_measurement_rows": m3172_dir / "measurement_episode_rows.csv",
        "m3172_same_row_comparison_rows": m3172_dir / "same_row_comparison_rows.csv",
        "m3172_gate_rows": m3172_dir / "gate_matrix.csv",
        "m3170_summary": m3170_dir / "summary.json",
        "m3170_source_localized_rule_rows": m3170_dir / "source_localized_rule_rows.csv",
        "m3170_gate_rows": m3170_dir / "gate_matrix.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_measurement_rows": m3105_dir / "measurement_episode_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3174_synthesis_text": paths["m3174_synthesis"].read_text(encoding="utf-8")
        if exists["m3174_synthesis"]
        else "",
        "m3173_audit_text": paths["m3173_audit"].read_text(encoding="utf-8") if exists["m3173_audit"] else "",
        "m3172_summary": read_json(paths["m3172_summary"]) if exists["m3172_summary"] else {},
        "m3172_measurement_rows": read_csv_rows(paths["m3172_measurement_rows"]),
        "m3172_same_row_comparison_rows": read_csv_rows(paths["m3172_same_row_comparison_rows"]),
        "m3172_gate_rows": read_csv_rows(paths["m3172_gate_rows"]),
        "m3170_summary": read_json(paths["m3170_summary"]) if exists["m3170_summary"] else {},
        "m3170_source_localized_rule_rows": read_csv_rows(paths["m3170_source_localized_rule_rows"]),
        "m3170_gate_rows": read_csv_rows(paths["m3170_gate_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_measurement_rows": read_csv_rows(paths["m3105_measurement_rows"]),
    }


def _m3105_by_source(source: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    return {str(row.get("source_measurement_episode_id", "")): row for row in source["m3105_measurement_rows"]}


def _same_row_m3105(row: Mapping[str, Any]) -> bool:
    return str(row.get("baseline_id", "")) == "m3105"


def _regression_against_m3105(row: Mapping[str, Any]) -> bool:
    return _same_row_m3105(row) and (
        _int(row.get("success_delta"), 0) < 0
        or _int(row.get("collision_delta"), 0) > 0
        or _int(row.get("offtrack_delta"), 0) > 0
        or _int(row.get("speed_too_low_delta"), 0) > 0
    )


def regression_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        [item for item in source["m3172_same_row_comparison_rows"] if _regression_against_m3105(item)],
        start=1,
    ):
        regression_family = "mixed_hard_safety_regression"
        if _int(row.get("collision_delta"), 0) > 0:
            regression_family = "new_collision_regression_vs_m3105"
        elif _int(row.get("offtrack_delta"), 0) > 0:
            regression_family = "new_offtrack_regression_vs_m3105"
        elif _int(row.get("success_delta"), 0) < 0:
            regression_family = "success_regression_vs_m3105"
        rows.append(
            {
                "regression_row_id": f"m3175-regression-row-{index:04d}",
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "baseline_episode_id": row.get("baseline_episode_id", ""),
                "source_measurement_episode_id": row.get("source_measurement_episode_id", ""),
                "fresh_panel_row_id": row.get("fresh_panel_row_id", ""),
                "axis_id": row.get("axis_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "eval_seed": row.get("eval_seed", ""),
                "regression_family": regression_family,
                "m3172_success": _bool(row.get("m3172_success", False)),
                "m3105_success": _bool(row.get("baseline_success", False)),
                "success_delta_vs_m3105": _int(row.get("success_delta"), 0),
                "m3172_collision": _bool(row.get("m3172_collision", False)),
                "m3105_collision": _bool(row.get("baseline_collision", False)),
                "collision_delta_vs_m3105": _int(row.get("collision_delta"), 0),
                "m3172_offtrack": _bool(row.get("m3172_offtrack", False)),
                "m3105_offtrack": _bool(row.get("baseline_offtrack", False)),
                "offtrack_delta_vs_m3105": _int(row.get("offtrack_delta"), 0),
                "m3172_min_clearance_margin": _float(row.get("m3172_min_clearance_margin")),
                "m3105_min_clearance_margin": _float(row.get("baseline_min_clearance_margin")),
                "clearance_margin_delta_vs_m3105": _float(row.get("clearance_margin_delta")),
                "m3172_speed_mean": _float(row.get("m3172_speed_mean")),
                "m3105_speed_mean": _float(row.get("baseline_speed_mean")),
                "speed_mean_delta_vs_m3105": _float(row.get("speed_mean_delta")),
                "m3172_return": _float(row.get("m3172_return")),
                "m3105_return": _float(row.get("baseline_return")),
                "return_delta_vs_m3105": _float(row.get("return_delta")),
                "actor_visible_repair_hypothesis_required": True,
                "runtime_label_inputs_allowed": False,
                "decomposition_label": (
                    "boundary_recovery_parent_low_speed_new_collision_requires_actor_visible_ablation_trace"
                    if row.get("axis_id") == "offtrack_boundary_recovery"
                    else "new_hard_safety_regression_requires_actor_visible_ablation_trace"
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def blocker_context_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    baseline_by_source = _m3105_by_source(source)
    rows: list[dict[str, Any]] = []
    for row in source["m3172_measurement_rows"]:
        is_collision = _bool(row.get("collision", False))
        is_offtrack = str(row.get("termination_reason", "")) == "off_track"
        if not is_collision and not is_offtrack:
            continue
        baseline = baseline_by_source.get(str(row.get("source_measurement_episode_id", "")), {})
        baseline_success = _bool(baseline.get("success", False))
        baseline_collision = _bool(baseline.get("collision", False))
        baseline_offtrack = str(baseline.get("termination_reason", "")) == "off_track"
        if baseline_success and is_collision:
            relation = "new_collision_regression_vs_m3105"
        elif baseline_success and is_offtrack:
            relation = "new_offtrack_regression_vs_m3105"
        elif baseline_collision or baseline_offtrack:
            relation = "inherited_incumbent_hard_safety_blocker"
        else:
            relation = "changed_non_success_hard_safety_blocker"
        blocker_family = "collision" if is_collision else "offtrack"
        rows.append(
            {
                "blocker_context_row_id": f"m3175-blocker-context-row-{len(rows) + 1:04d}",
                "measurement_episode_id": row.get("runtime_smoke_episode_id", ""),
                "source_measurement_episode_id": row.get("source_measurement_episode_id", ""),
                "fresh_panel_row_id": row.get("fresh_panel_row_id", ""),
                "axis_id": row.get("axis_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "eval_seed": row.get("eval_seed", ""),
                "m3172_collision": is_collision,
                "m3172_offtrack": is_offtrack,
                "m3172_termination_reason": row.get("termination_reason", ""),
                "m3172_min_clearance_margin": _float(row.get("min_clearance_margin")),
                "m3172_speed_mean": _float(row.get("speed_mean")),
                "m3105_success": baseline_success,
                "m3105_collision": baseline_collision,
                "m3105_offtrack": baseline_offtrack,
                "m3105_termination_reason": baseline.get("termination_reason", ""),
                "same_row_relation_to_m3105": relation,
                "blocker_family": blocker_family,
                "decomposition_need": (
                    "new_regression_actor_visible_trace_ablation"
                    if relation.startswith("new_")
                    else "inherited_blocker_preserve_incumbent_context"
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def repair_decomposition_rows(
    *,
    regression: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    regression_ids = "|".join(str(row["fresh_panel_row_id"]) for row in regression)
    inherited_collision = [
        row for row in blockers if row["blocker_family"] == "collision" and row["same_row_relation_to_m3105"] == "inherited_incumbent_hard_safety_blocker"
    ]
    inherited_offtrack = [
        row for row in blockers if row["blocker_family"] == "offtrack" and row["same_row_relation_to_m3105"] == "inherited_incumbent_hard_safety_blocker"
    ]
    forbidden = "row_label|baseline_outcome|source_label|route_label|outcome_label|progress_label|verdict_label|ttc_oracle"
    return [
        {
            "repair_decomposition_row_id": "m3175-repair-decomposition-row-0001",
            "route_name": "new_collision_regression_actor_visible_ablation_trace",
            "route_role": "primary_next_evidence",
            "source_row_count": len(regression),
            "source_rows": regression_ids,
            "hard_safety_focus": "new_collision_regression_vs_m3105",
            "incumbent_status": "preserve_m3105_m3103",
            "admission_decision": "decomposition_admitted_repair_not_admitted",
            "next_required_evidence": "per-step actor-visible feature and action-delta ablation trace on the new regression row before implementation",
            "actor_visible_candidate_feature_families": "speed|obstacle_clearance_proxy|edge_urgency_proxy|steer_damping|throttle_drop|brake_add",
            "forbidden_runtime_inputs": forbidden,
            "public_driver_mutation_allowed": False,
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "repair_decomposition_row_id": "m3175-repair-decomposition-row-0002",
            "route_name": "inherited_collision_blocker_context",
            "route_role": "preserve_context",
            "source_row_count": len(inherited_collision),
            "source_rows": "|".join(str(row["fresh_panel_row_id"]) for row in inherited_collision),
            "hard_safety_focus": "inherited_collision_blockers",
            "incumbent_status": "preserve_m3105_m3103",
            "admission_decision": "context_admitted_not_primary_repair",
            "next_required_evidence": "do not optimize inherited blockers until the new regression is neutralized or guarded",
            "actor_visible_candidate_feature_families": "none_selected_in_m3175",
            "forbidden_runtime_inputs": forbidden,
            "public_driver_mutation_allowed": False,
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "repair_decomposition_row_id": "m3175-repair-decomposition-row-0003",
            "route_name": "inherited_offtrack_blocker_context",
            "route_role": "preserve_context",
            "source_row_count": len(inherited_offtrack),
            "source_rows": "|".join(str(row["fresh_panel_row_id"]) for row in inherited_offtrack),
            "hard_safety_focus": "inherited_offtrack_blockers",
            "incumbent_status": "preserve_m3105_m3103",
            "admission_decision": "context_admitted_not_primary_repair",
            "next_required_evidence": "do not optimize inherited offtrack blockers until new collision regression is neutralized or guarded",
            "actor_visible_candidate_feature_families": "none_selected_in_m3175",
            "forbidden_runtime_inputs": forbidden,
            "public_driver_mutation_allowed": False,
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "repair_decomposition_row_id": "m3175-repair-decomposition-row-0004",
            "route_name": "direct_public_driver_mutation",
            "route_role": "blocked_shortcut",
            "source_row_count": len(blockers),
            "source_rows": "all_m3172_hard_safety_blockers",
            "hard_safety_focus": "all",
            "incumbent_status": "preserve_m3105_m3103",
            "admission_decision": "blocked_until_actor_visible_ablation_trace_and_audit",
            "next_required_evidence": "M3176 audit and a later targeted trace or ablation preflight",
            "actor_visible_candidate_feature_families": "not_applicable",
            "forbidden_runtime_inputs": forbidden,
            "public_driver_mutation_allowed": False,
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def contract_guard_rows(source: Mapping[str, Any], regression: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = source["m3172_summary"]
    rows = [
        ("m3174_synthesis_route_marker", "lineage", "pivot_to_m3175_behavior_negative_source_repair_decomposition_materialization" in source["m3174_synthesis_text"], True, False),
        ("m3173_negative_audit_marker", "lineage", "behavior-negative" in source["m3173_audit_text"], True, False),
        ("m3172_runtime_base_policy_required", "contract", summary.get("runtime_base_policy_required"), False, False),
        ("m3172_validation_result_claim_made", "claim", summary.get("validation_result_claim_made"), False, False),
        ("m3172_repair_success_claim_made", "claim", summary.get("repair_success_claim_made"), False, False),
        ("m3172_driver_performance_claim_made", "claim", summary.get("driver_performance_claim_made"), False, False),
        ("regression_runtime_label_inputs_allowed", "contract", any(row["runtime_label_inputs_allowed"] for row in regression), False, False),
        ("blocker_context_actor_visible", "contract", False, False, False),
        ("public_driver_mutation_allowed", "contract", False, False, False),
        ("environment_reset_run", "execution", False, False, False),
        ("environment_step_run", "execution", False, False, False),
        ("policy_action_run", "execution", False, False, False),
        ("m3172_blocker_context_rows", "evidence", len(blockers), EXPECTED_M3172_COLLISION_ROWS + EXPECTED_M3172_OFFTRACK_ROWS, False),
    ]
    return [
        {
            "guard_id": f"m3175-{guard_id}",
            "guard_family": family,
            "observed_value": observed,
            "expected_value": expected,
            "status_pass": str(observed) == str(expected),
            "actor_visible": actor_visible,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, family, observed, expected, actor_visible in rows
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("regression_rows", "decomposition", True, True, "regression_rows.csv"),
        ("blocker_context_rows", "decomposition", True, True, "blocker_context_rows.csv"),
        ("repair_decomposition_rows", "decomposition", True, True, "repair_decomposition_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("repair_implementation", "forbidden", False, False, "actor-visible trace and later implementation preflight"),
        ("validation_result", "forbidden", False, False, "separate validation execution after accepted deployable candidate"),
        ("driver_performance_verdict", "forbidden", False, False, "validation and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "current-sim result synthesis after validation"),
        ("repair_success", "forbidden", False, False, "accepted full-fresh improvement plus validation path"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3175"),
    ]
    return [
        {
            "claim_id": f"m3175-{claim_id}",
            "claim_family": family,
            "allowed_in_m3175": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3175-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    regression: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    decomposition: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    relation_counts = Counter(str(row.get("same_row_relation_to_m3105", "")) for row in blockers)
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in blockers)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate(
            "m3174_selects_m3175_route",
            "lineage",
            "pivot_to_m3175_behavior_negative_source_repair_decomposition_materialization" in source["m3174_synthesis_text"],
            "route marker",
            "present",
            "lineage_invalid",
        ),
        gate("m3172_status_pass", "lineage", _bool(source["m3172_summary"].get("status_pass", False)), source["m3172_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3172_gate_matrix_pass", "lineage", _bool(source["m3172_summary"].get("gate_matrix_pass", False)), source["m3172_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3170_status_pass", "lineage", _bool(source["m3170_summary"].get("status_pass", False)), source["m3170_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3172_full_fresh_rows", "evidence", int(source["m3172_summary"].get("measurement_episode_row_count", 0)) == EXPECTED_FULL_ROWS, source["m3172_summary"].get("measurement_episode_row_count"), EXPECTED_FULL_ROWS, "metric_artifact"),
        gate("m3172_same_row_comparison_rows", "evidence", int(source["m3172_summary"].get("same_row_comparison_row_count", 0)) == EXPECTED_FULL_ROWS * 4, source["m3172_summary"].get("same_row_comparison_row_count"), EXPECTED_FULL_ROWS * 4, "metric_artifact"),
        gate("new_regression_rows_vs_m3105", "evidence", len(regression) == EXPECTED_REGRESSION_ROWS, len(regression), EXPECTED_REGRESSION_ROWS, "behavior_regression"),
        gate("new_collision_regression_rows", "evidence", sum(1 for row in regression if row["regression_family"] == "new_collision_regression_vs_m3105") == 1, Counter(row["regression_family"] for row in regression), "one new collision regression", "behavior_regression"),
        gate("blocker_context_rows", "evidence", len(blockers) == EXPECTED_M3172_COLLISION_ROWS + EXPECTED_M3172_OFFTRACK_ROWS, len(blockers), EXPECTED_M3172_COLLISION_ROWS + EXPECTED_M3172_OFFTRACK_ROWS, "metric_artifact"),
        gate("m3172_collision_context_rows", "evidence", blocker_counts.get("collision", 0) == EXPECTED_M3172_COLLISION_ROWS, dict(blocker_counts), EXPECTED_M3172_COLLISION_ROWS, "metric_artifact"),
        gate("m3172_offtrack_context_rows", "evidence", blocker_counts.get("offtrack", 0) == EXPECTED_M3172_OFFTRACK_ROWS, dict(blocker_counts), EXPECTED_M3172_OFFTRACK_ROWS, "metric_artifact"),
        gate("inherited_blocker_context_rows", "evidence", relation_counts.get("inherited_incumbent_hard_safety_blocker", 0) == EXPECTED_INHERITED_BLOCKER_ROWS, dict(relation_counts), EXPECTED_INHERITED_BLOCKER_ROWS, "metric_artifact"),
        gate("repair_decomposition_rows", "decomposition", len(decomposition) >= 4, len(decomposition), ">=4", "metric_artifact"),
        gate(
            "primary_route_requires_trace_not_driver_mutation",
            "contract",
            any(
                row["route_name"] == "new_collision_regression_actor_visible_ablation_trace"
                and row["admission_decision"] == "decomposition_admitted_repair_not_admitted"
                and not _bool(row["public_driver_mutation_allowed"])
                for row in decomposition
            ),
            "primary route",
            "trace required and mutation blocked",
            "contract_violation",
        ),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in guards), "all", "pass", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claims), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31760,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject M3175 behavior-negative source repair decomposition artifacts before any trace ablation repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "regression_rows.csv"),
                str(output_dir / "blocker_context_rows.csv"),
                str(output_dir / "repair_decomposition_rows.csv"),
                str(output_dir / "contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3175 behavior-negative decomposition before targeted trace or ablation"],
            "derived_from": [MILESTONE_ID, M3174_ID, M3173_ID, M3172_ID, M3170_ID, M3105_ID],
            "blocked_by": [
                "M3175 decomposition rows require audit before targeted trace or repair implementation",
                "the regression route must preserve actor-visible-only runtime inputs",
            ],
            "supersedes": ["direct repair implementation after M3174 negative synthesis"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3176 must audit M3175 regression blocker context repair-decomposition guard claim and gate artifacts",
            "M3176 must preserve M3105/M3103 as incumbent and public driver default unchanged",
            "M3176 must reject trace ablation repair implementation validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3176 must select exactly one targeted trace-ablation, artifact-repair, synthesis, or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run trace ablation repair implementation validation ranking promotion or high-fidelity simulation in M3176",
            "do not convert M3175 decomposition rows into repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_behavior_negative_source_repair_decomposition",
            "evidence_axis": "behavior_negative_source_repair_decomposition_result_audit",
            "evidence_increment": "audits no-new-execution decomposition rows for the single M3172 collision regression and inherited blockers",
            "claim_scope": "Result audit only; no trace ablation implementation validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3175 artifacts are missing or gate matrix fails",
                "stop if decomposition requires hidden runtime labels as actor inputs",
                "route to targeted trace only after M3176 accepts claim boundaries",
            ],
            "fallback_plan": [
                "route to M3175 artifact repair if row counts or guards fail",
                "route to stop if no actor-visible route can target the new regression",
                "preserve M3105/M3103 incumbent until a later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3175 materializes behavior-negative source repair decomposition artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3175 behavior-negative source repair decomposition artifacts",
            "admission_evidence": ["M3175 summary regression blocker context repair decomposition guard claim and gate artifacts"],
            "blocked_shortcuts": [
                "no trace ablation repair implementation validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3176 status queue scoreboard research log and review",
                "one follow-up manifest only if M3176 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3176 accepts or rejects M3175 as complete and claim-safe",
                "next targeted trace-ablation artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3176 audits engineering decomposition artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3176; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3175 decomposition artifacts only.",
            "negative_result_policy": "Preserve engineering decomposition evidence and route targeted trace or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3175 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new behavior-negative decomposition panel before a targeted trace-ablation route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3176 audits engineering decomposition evidence",
            "must_synthesize_if": [
                "M3176 cannot select targeted trace-ablation artifact-repair synthesis or stop",
                "M3176 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3176 audits M3175 row counts gates actor contract and claim boundaries",
            "M3176 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3176 hides missing M3175 artifacts or failed gates",
            "M3176 treats M3175 decomposition as repair success or performance verdict",
            "M3176 changes actor input or action contract",
            "M3176 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3176 audits M3175 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_behavior_negative_source_repair_decomposition_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3175 Behavior-Negative Source Repair Decomposition Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- regression rows vs M3105: {summary['regression_row_count']}",
            f"- new collision regression rows: {summary['new_collision_regression_row_count']}",
            f"- blocker context rows: {summary['blocker_context_row_count']}",
            f"- inherited blocker rows: {summary['inherited_blocker_context_row_count']}",
            f"- repair decomposition rows: {summary['repair_decomposition_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3175 decomposes the M3172 negative full-fresh measurement into a single new collision regression versus M3105 plus inherited incumbent blockers. The selected next evidence is a targeted actor-visible trace or ablation route for the new regression row. M3175 does not implement a repair, mutate the public driver, run an environment, or claim repair success.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
        ]
    )


def run_decomposition_preflight(
    *,
    m3174_synthesis: Path,
    m3173_audit: Path,
    m3172_dir: Path,
    m3170_dir: Path,
    m3105_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3174_synthesis=m3174_synthesis,
        m3173_audit=m3173_audit,
        m3172_dir=m3172_dir,
        m3170_dir=m3170_dir,
        m3105_dir=m3105_dir,
    )
    regression = regression_rows(source)
    blockers = blocker_context_rows(source)
    decomposition = repair_decomposition_rows(regression=regression, blockers=blockers)
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    guards = contract_guard_rows(source, regression, blockers)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())

    write_csv_rows(paths["regression_rows"], regression, fieldnames=REGRESSION_FIELDNAMES)
    write_csv_rows(paths["blocker_context_rows"], blockers, fieldnames=BLOCKER_CONTEXT_FIELDNAMES)
    write_csv_rows(paths["repair_decomposition_rows"], decomposition, fieldnames=REPAIR_DECOMPOSITION_FIELDNAMES)
    write_csv_rows(paths["contract_guard_rows"], guards, fieldnames=CONTRACT_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)

    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        regression=regression,
        blockers=blockers,
        decomposition=decomposition,
        guards=guards,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    relation_counts = Counter(str(row.get("same_row_relation_to_m3105", "")) for row in blockers)
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in blockers)
    status_pass = bool(gate_matrix_pass and present)
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_behavior_negative_source_repair_decomposition_materialization_pass"
            if status_pass
            else "active_safety_driver_behavior_negative_source_repair_decomposition_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "regression_row_count": len(regression),
        "new_collision_regression_row_count": sum(
            1 for row in regression if row["regression_family"] == "new_collision_regression_vs_m3105"
        ),
        "blocker_context_row_count": len(blockers),
        "blocker_context_family_counts": dict(sorted(blocker_counts.items())),
        "blocker_context_relation_counts": dict(sorted(relation_counts.items())),
        "inherited_blocker_context_row_count": int(relation_counts.get("inherited_incumbent_hard_safety_blocker", 0)),
        "repair_decomposition_row_count": len(decomposition),
        "contract_guard_row_count": len(guards),
        "contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in guards),
        "claim_boundary_row_count": len(claims),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claims),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3172_status_pass": _bool(source["m3172_summary"].get("status_pass", False)),
        "m3172_gate_matrix_pass": _bool(source["m3172_summary"].get("gate_matrix_pass", False)),
        "m3170_status_pass": _bool(source["m3170_summary"].get("status_pass", False)),
        "m3105_status_pass": _bool(source["m3105_summary"].get("status_pass", False)),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "public_driver_default_mutated": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_behavior_negative_source_repair_decomposition_route_to_m3176_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "regression_row_count": len(regression),
            "blocker_context_row_count": len(blockers),
            "repair_decomposition_row_count": len(decomposition),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3174-synthesis", type=Path, default=DEFAULT_M3174_SYNTHESIS)
    parser.add_argument("--m3173-audit", type=Path, default=DEFAULT_M3173_AUDIT)
    parser.add_argument("--m3172-dir", type=Path, default=DEFAULT_M3172_DIR)
    parser.add_argument("--m3170-dir", type=Path, default=DEFAULT_M3170_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_decomposition_preflight(
        m3174_synthesis=args.m3174_synthesis,
        m3173_audit=args.m3173_audit,
        m3172_dir=args.m3172_dir,
        m3170_dir=args.m3170_dir,
        m3105_dir=args.m3105_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"regression_rows={summary['regression_row_count']}")
    print(f"new_collision_regression_rows={summary['new_collision_regression_row_count']}")
    print(f"blocker_context_rows={summary['blocker_context_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
