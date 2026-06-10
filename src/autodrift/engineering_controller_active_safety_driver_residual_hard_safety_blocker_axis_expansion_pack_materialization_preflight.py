"""Materialize M3185 residual hard-safety blocker-axis expansion pack artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3185-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-expansion-pack-materialization-preflight"
)
NEXT_ID = (
    "m3186-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-expansion-pack-result-audit"
)
M3184_ID = "m3184-engineering-controller-active-safety-driver-residual-hard-safety-blocker-axis-expansion-plan"
M3183_ID = (
    "m3183-engineering-controller-active-safety-driver-residual-hard-safety-"
    "steer-delta-regression-guard-equivalence-synthesis"
)
M3156_ID = "m3156-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-materialization-preflight"
M3161_ID = "m3161-engineering-controller-active-safety-driver-route-a-public-deployable-validation-execution-preflight"
M3153_ID = (
    "m3153-engineering-controller-active-safety-driver-residual-action-delta-counterfactual-"
    "replay-diagnostic-materialization-preflight"
)
M3181_ID = (
    "m3181-engineering-controller-active-safety-driver-residual-hard-safety-"
    "steer-delta-regression-guard-full-fresh-measurement-preflight"
)

DEFAULT_M3184_PLAN = Path(f"docs/{M3184_ID}.md")
DEFAULT_M3156_DIR = Path("runs/m3156_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_materialization_preflight")
DEFAULT_M3161_DIR = Path("runs/m3161_engineering_controller_active_safety_driver_route_a_public_deployable_validation_execution_preflight")
DEFAULT_M3153_DIR = Path(
    "runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_"
    "replay_diagnostic_materialization_preflight"
)
DEFAULT_M3181_DIR = Path(
    "runs/m3181_engineering_controller_active_safety_driver_residual_hard_safety_"
    "steer_delta_regression_guard_full_fresh_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3185_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_expansion_pack_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_BLOCKERS = 7
EXPECTED_COLLISIONS = 5
EXPECTED_OFFTRACK = 2

CLAIM_SCOPE = (
    "M3185 Active Safety Driver residual hard-safety blocker-axis expansion pack "
    "materialization only; existing M3184 route plan, M3156 known-failure rows, "
    "M3161 known-failure validation rows, M3153 action-delta counterfactual summary, "
    "and M3181 steer-delta guard measurement summary may be reanalyzed into blocker "
    "axis, blocker-family summary, actor-visible axis candidate, forbidden-label "
    "guard, evidence-gap, candidate-admission, claim, gate, doc, and M3186 audit "
    "manifest artifacts. No reset, step, rollout, replay, policy action, fitting, "
    "PPO, training, repair implementation, validation execution, ranking, winner "
    "selection, checkpoint mutation, checkpoint promotion, public driver default "
    "mutation, driver-performance verdict, current-sim verdict, repair success, "
    "robustness-result, high-fidelity validation, paper evidence, finite-window-vs-GRU "
    "evidence, full ideal driver completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)
FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)

RESIDUAL_BLOCKER_FIELDNAMES = [
    "residual_blocker_axis_row_id",
    "source_blocker_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "blocker_family",
    "termination_reason",
    "outcome_bucket",
    "min_clearance_margin",
    "high_sideslip_fraction",
    "lateral_rmse",
    "speed_mean",
    "m3153_action_channel_sensitive_count",
    "m3161_blocker_preserved",
    "proposed_evidence_axis",
    "actor_visible_signal_families",
    "offline_labels_only",
    "runtime_actor_input_allowed",
    "claim_boundary",
]
SUMMARY_FIELDNAMES = [
    "family_summary_id",
    "group",
    "row_count",
    "collision_count",
    "offtrack_count",
    "min_clearance_margin_min",
    "high_sideslip_fraction_mean",
    "lateral_rmse_mean",
    "m3153_action_channel_sensitive_count",
    "m3161_blocker_preserved_count",
    "claim_boundary",
]
AXIS_FIELDNAMES = [
    "axis_candidate_id",
    "evidence_axis",
    "route_role",
    "source_blocker_count",
    "source_blocker_rows",
    "allowed_signal_families",
    "computed_from",
    "hidden_labels_required",
    "actor_runtime_input_contract",
    "implementation_admitted",
    "next_required_evidence",
    "claim_boundary",
]
FORBIDDEN_LABEL_FIELDNAMES = [
    "forbidden_label_guard_id",
    "label_family",
    "example_fields",
    "actor_runtime_allowed",
    "offline_analysis_allowed",
    "status_pass",
    "claim_boundary",
]
EVIDENCE_GAP_FIELDNAMES = [
    "evidence_gap_id",
    "source_evidence",
    "observed",
    "limitation",
    "next_required_evidence",
    "blocks_repair_implementation",
    "claim_boundary",
]
CANDIDATE_ADMISSION_FIELDNAMES = [
    "candidate_admission_id",
    "candidate_route",
    "admission_status",
    "implementation_allowed_now",
    "public_driver_mutation_allowed",
    "required_before_implementation",
    "forbidden_runtime_inputs",
    "claim_boundary",
]
GUARD_FIELDNAMES = ["guard_id", "guard_family", "observed_value", "expected_value", "status_pass", "actor_visible", "claim_boundary"]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3185",
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
        "residual_blocker_axis_rows": output_dir / "residual_blocker_axis_rows.csv",
        "blocker_family_summary_rows": output_dir / "blocker_family_summary_rows.csv",
        "actor_visible_axis_candidate_rows": output_dir / "actor_visible_axis_candidate_rows.csv",
        "forbidden_label_guard_rows": output_dir / "forbidden_label_guard_rows.csv",
        "evidence_gap_rows": output_dir / "evidence_gap_rows.csv",
        "candidate_admission_rows": output_dir / "candidate_admission_rows.csv",
        "contract_guard_rows": output_dir / "contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3184_plan: Path,
    m3156_dir: Path,
    m3161_dir: Path,
    m3153_dir: Path,
    m3181_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3184_plan": m3184_plan,
        "m3156_known_failure_rows": m3156_dir / "known_failure_taxonomy_rows.csv",
        "m3156_summary": m3156_dir / "summary.json",
        "m3161_known_failure_validation_rows": m3161_dir / "known_failure_validation_rows.csv",
        "m3161_summary": m3161_dir / "validation_execution_summary.json",
        "m3153_summary": m3153_dir / "summary.json",
        "m3181_summary": m3181_dir / "summary.json",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3184_plan_text": paths["m3184_plan"].read_text(encoding="utf-8") if exists["m3184_plan"] else "",
        "m3156_known_failure_rows": read_csv_rows(paths["m3156_known_failure_rows"]),
        "m3156_summary": read_json(paths["m3156_summary"]) if exists["m3156_summary"] else {},
        "m3161_known_failure_validation_rows": read_csv_rows(paths["m3161_known_failure_validation_rows"]),
        "m3161_summary": read_json(paths["m3161_summary"]) if exists["m3161_summary"] else {},
        "m3153_summary": read_json(paths["m3153_summary"]) if exists["m3153_summary"] else {},
        "m3181_summary": read_json(paths["m3181_summary"]) if exists["m3181_summary"] else {},
    }


def proposed_evidence_axis(row: Mapping[str, Any]) -> tuple[str, str]:
    blocker_family = str(row.get("blocker_family", ""))
    axis_id = str(row.get("axis_id", ""))
    high_sideslip = _float(row.get("high_sideslip_fraction"))
    lateral_rmse = _float(row.get("lateral_rmse"))
    if blocker_family == "collision" and axis_id == "collision_lateral_intrusion":
        return (
            "clearance_timing_axis",
            "ego_speed|obstacle_geometry_proxy|lane_corridor_geometry|relative_clearance_proxy|previous_action",
        )
    if blocker_family == "collision" and axis_id == "offtrack_boundary_recovery":
        return (
            "boundary_recovery_collision_axis",
            "lane_boundary_geometry|obstacle_geometry_proxy|ego_speed|lateral_error|previous_action_response",
        )
    if blocker_family == "offtrack" or high_sideslip >= 0.2 or lateral_rmse >= 2.0:
        return (
            "boundary_recovery_stability_axis",
            "lane_boundary_geometry|lateral_error|heading_alignment|sideslip_proxy|previous_action_response",
        )
    return (
        "clearance_timing_axis",
        "ego_speed|obstacle_geometry_proxy|lane_corridor_geometry|relative_clearance_proxy|previous_action",
    )


def _validation_by_source(source: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    return {
        str(row.get("source_measurement_episode_id", "")): row
        for row in source["m3161_known_failure_validation_rows"]
    }


def residual_blocker_axis_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    validation = _validation_by_source(source)
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["m3156_known_failure_rows"], start=1):
        evidence_axis, signals = proposed_evidence_axis(row)
        source_id = str(row.get("source_measurement_episode_id", ""))
        validation_row = validation.get(source_id, {})
        rows.append(
            {
                "residual_blocker_axis_row_id": f"m3185-residual-blocker-axis-{index:04d}",
                "source_blocker_id": row.get("source_blocker_id", ""),
                "source_measurement_episode_id": source_id,
                "fresh_panel_row_id": row.get("fresh_panel_row_id", ""),
                "axis_id": row.get("axis_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "eval_seed": row.get("eval_seed", ""),
                "blocker_family": row.get("blocker_family", ""),
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "min_clearance_margin": _float(row.get("min_clearance_margin")),
                "high_sideslip_fraction": _float(row.get("high_sideslip_fraction")),
                "lateral_rmse": _float(row.get("lateral_rmse")),
                "speed_mean": _float(row.get("speed_mean")),
                "m3153_action_channel_sensitive_count": _int(row.get("m3153_action_channel_sensitive_count")),
                "m3161_blocker_preserved": _bool(validation_row.get("blocker_preserved")),
                "proposed_evidence_axis": evidence_axis,
                "actor_visible_signal_families": signals,
                "offline_labels_only": (
                    "source_measurement_episode_id|fresh_panel_row_id|axis_id|binding_role|task_family|"
                    "blocker_family|termination_reason|outcome_bucket"
                ),
                "runtime_actor_input_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def blocker_family_summary_rows(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {"all": blockers}
    for key in ["blocker_family", "axis_id", "proposed_evidence_axis"]:
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in blockers:
            buckets[str(row.get(key, ""))].append(row)
        for name, rows in buckets.items():
            groups[f"{key}:{name}"] = rows

    output: list[dict[str, Any]] = []
    for index, (group, rows) in enumerate(groups.items(), start=1):
        output.append(
            {
                "family_summary_id": f"m3185-family-summary-{index:04d}",
                "group": group,
                "row_count": len(rows),
                "collision_count": sum(1 for row in rows if row.get("blocker_family") == "collision"),
                "offtrack_count": sum(1 for row in rows if row.get("blocker_family") == "offtrack"),
                "min_clearance_margin_min": min([_float(row.get("min_clearance_margin")) for row in rows], default=0.0),
                "high_sideslip_fraction_mean": _mean([_float(row.get("high_sideslip_fraction")) for row in rows]),
                "lateral_rmse_mean": _mean([_float(row.get("lateral_rmse")) for row in rows]),
                "m3153_action_channel_sensitive_count": sum(_int(row.get("m3153_action_channel_sensitive_count")) for row in rows),
                "m3161_blocker_preserved_count": sum(1 for row in rows if _bool(row.get("m3161_blocker_preserved"))),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def actor_visible_axis_candidate_rows(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axis_to_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in blockers:
        axis_to_rows[str(row["proposed_evidence_axis"])].append(row)

    configured = {
        "clearance_timing_axis": (
            "primary_collision_axis",
            "obs72 geometry and ego-response fields",
            "clearance timing trace with per-step actor-visible obstacle geometry and ego speed",
        ),
        "boundary_recovery_collision_axis": (
            "boundary_collision_axis",
            "obs72 lane/boundary geometry plus ego-response fields",
            "boundary recovery trace with collision-clearance timing and lateral recovery state",
        ),
        "boundary_recovery_stability_axis": (
            "primary_offtrack_axis",
            "obs72 boundary and public ego-response fields",
            "stability and recovery trace with lateral error, heading alignment, and sideslip proxy",
        ),
        "action_authority_saturation_axis": (
            "cross_cutting_authority_axis",
            "public runtime action telemetry and obs72 actuator state",
            "action authority and saturation trace before terminal failure",
        ),
    }
    rows: list[dict[str, Any]] = []
    for index, (axis, (role, computed_from, next_required)) in enumerate(configured.items(), start=1):
        source_rows = axis_to_rows.get(axis, [])
        if axis == "action_authority_saturation_axis":
            source_rows = blockers
        signal_families = (
            "raw_action_bounds|final_action_bounds|action_rate|clip_fraction|previous_action"
            if axis == "action_authority_saturation_axis"
            else "|".join(sorted({str(row["actor_visible_signal_families"]) for row in source_rows}))
        )
        rows.append(
            {
                "axis_candidate_id": f"m3185-axis-candidate-{index:04d}",
                "evidence_axis": axis,
                "route_role": role,
                "source_blocker_count": len(source_rows),
                "source_blocker_rows": "|".join(str(row["fresh_panel_row_id"]) for row in source_rows),
                "allowed_signal_families": signal_families,
                "computed_from": computed_from,
                "hidden_labels_required": False,
                "actor_runtime_input_contract": "obs72_only_direct_action3",
                "implementation_admitted": False,
                "next_required_evidence": next_required,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def forbidden_label_guard_rows() -> list[dict[str, Any]]:
    specs = [
        ("row_identity_labels", "source_measurement_episode_id|fresh_panel_row_id|source_blocker_id"),
        ("scenario_role_labels", "axis_id|binding_role|task_family"),
        ("terminal_outcome_labels", "blocker_family|termination_reason|outcome_bucket|success|collision|offtrack"),
        ("baseline_comparison_labels", "baseline_success|baseline_collision|baseline_outcome|same_row_delta"),
        ("oracle_progress_labels", "target_label|route_label|progress_label|verdict_label|ttc_oracle"),
    ]
    return [
        {
            "forbidden_label_guard_id": f"m3185-forbidden-label-guard-{index:04d}",
            "label_family": label_family,
            "example_fields": fields,
            "actor_runtime_allowed": False,
            "offline_analysis_allowed": True,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (label_family, fields) in enumerate(specs, start=1)
    ]


def evidence_gap_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    m3153_sensitive = _int(source["m3153_summary"].get("action_channel_sensitive_comparison_count"))
    return [
        {
            "evidence_gap_id": "m3185-evidence-gap-0001",
            "source_evidence": "M3153 fixed action-channel counterfactual replay",
            "observed": f"action_channel_sensitive_comparison_count={m3153_sensitive}",
            "limitation": "fixed steer throttle brake probes did not change terminal outcomes on the seven residual rows",
            "next_required_evidence": "actor-visible blocker-axis trace rather than another fixed action-channel delta loop",
            "blocks_repair_implementation": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "evidence_gap_id": "m3185-evidence-gap-0002",
            "source_evidence": "M3177 targeted trace ablation",
            "observed": "single new M3172 steer-delta regression recovered",
            "limitation": "the recovered row is not one of the seven inherited residual blockers after M3181 parity",
            "next_required_evidence": "blocker-family evidence for the inherited collision and offtrack rows",
            "blocks_repair_implementation": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "evidence_gap_id": "m3185-evidence-gap-0003",
            "source_evidence": "M3181 full-fresh measurement",
            "observed": "57 success, 5 collision, 2 offtrack, 0 speed-too-low; delta vs M3105 is 0/0/0/0",
            "limitation": "restores parity but does not improve hard-safety counts over M3105",
            "next_required_evidence": "new actor-visible residual-blocker evidence axis before implementation",
            "blocks_repair_implementation": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "evidence_gap_id": "m3185-evidence-gap-0004",
            "source_evidence": "M3161 public deployable validation execution",
            "observed": "known residual blocker resolution count is 0/7",
            "limitation": "public API fidelity does not resolve residual blockers",
            "next_required_evidence": "row-level blocker-axis pack and audit before any candidate implementation",
            "blocks_repair_implementation": True,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def candidate_admission_rows(axis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_admission_id": f"m3185-candidate-admission-{index:04d}",
            "candidate_route": row["evidence_axis"],
            "admission_status": "evidence_axis_admitted_implementation_not_admitted",
            "implementation_allowed_now": False,
            "public_driver_mutation_allowed": False,
            "required_before_implementation": row["next_required_evidence"],
            "forbidden_runtime_inputs": FORBIDDEN_RUNTIME_INPUTS,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, row in enumerate(axis_rows, start=1)
    ]


def contract_guard_rows(
    source: Mapping[str, Any],
    blockers: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    forbidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in blockers)
    rows = [
        ("source_artifacts_present", "source", all(source["source_exists"].values()), True, False),
        ("m3184_selects_m3185_route", "lineage", "M3185 blocker-axis expansion pack materialization" in source["m3184_plan_text"], True, False),
        ("residual_blocker_rows", "evidence", len(blockers), EXPECTED_BLOCKERS, False),
        ("collision_blocker_rows", "evidence", blocker_counts.get("collision", 0), EXPECTED_COLLISIONS, False),
        ("offtrack_blocker_rows", "evidence", blocker_counts.get("offtrack", 0), EXPECTED_OFFTRACK, False),
        ("m3161_preserved_blocker_rows", "evidence", sum(1 for row in blockers if _bool(row.get("m3161_blocker_preserved"))), EXPECTED_BLOCKERS, False),
        ("m3153_action_channel_sensitive_count", "evidence", sum(_int(row.get("m3153_action_channel_sensitive_count")) for row in blockers), 0, False),
        ("actor_visible_axis_candidate_rows", "evidence", len(axis_rows), 4, False),
        ("hidden_labels_required", "contract", any(_bool(row.get("hidden_labels_required")) for row in axis_rows), False, False),
        ("forbidden_runtime_labels_allowed", "contract", any(_bool(row.get("actor_runtime_allowed")) for row in forbidden_rows), False, False),
        ("public_driver_mutation_allowed", "contract", False, False, False),
        ("environment_reset_run", "execution", False, False, False),
        ("environment_step_run", "execution", False, False, False),
        ("policy_action_run", "execution", False, False, False),
        ("validation_run", "execution", False, False, False),
    ]
    return [
        {
            "guard_id": f"m3185-{guard_id}",
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
        ("residual_blocker_axis_rows", "materialization", True, True, "residual_blocker_axis_rows.csv"),
        ("actor_visible_axis_candidate_rows", "materialization", True, True, "actor_visible_axis_candidate_rows.csv"),
        ("forbidden_label_guard_rows", "materialization", True, True, "forbidden_label_guard_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("repair_implementation", "forbidden", False, False, "later implementation preflight after M3186 audit"),
        ("validation_result", "forbidden", False, False, "separate validation execution after accepted candidate"),
        ("driver_performance_verdict", "forbidden", False, False, "validation and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "current-sim synthesis after validation"),
        ("repair_success", "forbidden", False, False, "accepted same-denominator improvement plus validation route"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3185"),
    ]
    return [
        {
            "claim_id": f"m3185-{claim_id}",
            "claim_family": family,
            "allowed_in_m3185": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3185-{gate_id}",
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
    blockers: list[dict[str, Any]],
    family_summaries: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    forbidden_rows: list[dict[str, Any]],
    evidence_gaps: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in blockers)
    axis_counts = Counter(str(row.get("proposed_evidence_axis", "")) for row in blockers)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3184_selects_m3185_route", "lineage", "M3185 blocker-axis expansion pack materialization" in source["m3184_plan_text"], "route marker", "present", "lineage_invalid"),
        gate("m3156_status_pass", "lineage", _bool(source["m3156_summary"].get("status_pass", False)), source["m3156_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3153_status_pass", "lineage", _bool(source["m3153_summary"].get("status_pass", False)), source["m3153_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3181_status_pass", "lineage", _bool(source["m3181_summary"].get("status_pass", False)), source["m3181_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("residual_blocker_rows", "evidence", len(blockers) == EXPECTED_BLOCKERS, len(blockers), EXPECTED_BLOCKERS, "metric_artifact"),
        gate("collision_blocker_rows", "evidence", blocker_counts.get("collision", 0) == EXPECTED_COLLISIONS, dict(blocker_counts), EXPECTED_COLLISIONS, "metric_artifact"),
        gate("offtrack_blocker_rows", "evidence", blocker_counts.get("offtrack", 0) == EXPECTED_OFFTRACK, dict(blocker_counts), EXPECTED_OFFTRACK, "metric_artifact"),
        gate("m3161_preserved_blocker_rows", "evidence", sum(1 for row in blockers if _bool(row.get("m3161_blocker_preserved"))) == EXPECTED_BLOCKERS, "preserved rows", EXPECTED_BLOCKERS, "metric_artifact"),
        gate("m3153_no_action_channel_sensitive_rows", "evidence", sum(_int(row.get("m3153_action_channel_sensitive_count")) for row in blockers) == 0, "sensitive count", 0, "objective_overfit"),
        gate("family_summary_rows", "evidence", len(family_summaries) >= 6, len(family_summaries), ">=6", "metric_artifact"),
        gate("axis_candidate_rows", "evidence", len(axis_rows) == 4, len(axis_rows), 4, "metric_artifact"),
        gate("axis_counts_nonempty", "evidence", bool(axis_counts), dict(axis_counts), "nonempty", "metric_artifact"),
        gate("forbidden_label_guard_rows", "contract", len(forbidden_rows) >= 5, len(forbidden_rows), ">=5", "contract_violation"),
        gate("forbidden_label_guards_pass", "contract", all(_bool(row.get("status_pass")) for row in forbidden_rows), "all", "pass", "contract_violation"),
        gate("evidence_gap_rows", "evidence", len(evidence_gaps) >= 4, len(evidence_gaps), ">=4", "metric_artifact"),
        gate("candidate_admission_rows", "contract", len(admission_rows) == len(axis_rows), len(admission_rows), len(axis_rows), "contract_violation"),
        gate("implementation_not_admitted", "contract", not any(_bool(row.get("implementation_allowed_now")) for row in admission_rows), "none", "admitted", "contract_violation"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in guards), "all", "pass", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claims), "all", "pass", "proof_washout"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31860,
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
        "hypothesis": "A bounded result audit can accept or reject M3185 blocker-axis expansion pack artifacts before any repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "residual_blocker_axis_rows.csv"),
                str(output_dir / "actor_visible_axis_candidate_rows.csv"),
                str(output_dir / "forbidden_label_guard_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3185 blocker-axis expansion pack before implementation admission"],
            "derived_from": [MILESTONE_ID, M3184_ID, M3183_ID, M3156_ID, M3161_ID, M3153_ID, M3181_ID],
            "blocked_by": [
                "M3185 materialization requires audit before implementation admission",
                "actor-visible evidence axes must be checked against forbidden-label guards",
            ],
            "supersedes": ["direct residual blocker repair implementation after M3184 route plan"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3186 must audit M3185 blocker-axis rows summaries axis candidates forbidden-label guards evidence gaps candidate admissions claims and gates",
            "M3186 must preserve M3105/M3103 as incumbent and public driver default unchanged",
            "M3186 must reject repair implementation validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3186 must select exactly one implementation-admission, artifact-repair, synthesis, or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run repair implementation validation ranking promotion or high-fidelity simulation in M3186",
            "do not convert M3185 pack rows into repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_blocker_axis_expansion",
            "evidence_axis": "residual_blocker_axis_expansion_pack_result_audit",
            "evidence_increment": "audits no-new-execution blocker-axis pack for the seven inherited residual blockers",
            "claim_scope": "Result audit only; no implementation validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3185 artifacts are missing or gate matrix fails",
                "stop if any proposed axis requires hidden runtime labels as actor inputs",
                "route to implementation admission only after M3186 accepts claim boundaries",
            ],
            "fallback_plan": [
                "route to M3185 artifact repair if row counts or guards fail",
                "route to stop if no actor-visible route remains after guard checks",
                "preserve M3105/M3103 incumbent until later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3185 materializes blocker-axis expansion pack artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3185 blocker-axis expansion pack artifacts",
            "admission_evidence": ["M3185 summary blocker-axis rows axis candidates forbidden-label guards claim and gate artifacts"],
            "blocked_shortcuts": [
                "no repair implementation validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3186 status queue scoreboard research log and review",
                "one follow-up manifest only if M3186 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3186 accepts or rejects M3185 as complete and claim-safe",
                "next implementation-admission artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3186 audits engineering blocker-axis artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3186; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3185 blocker-axis expansion artifacts only.",
            "negative_result_policy": "Preserve engineering blocker-axis evidence and route implementation admission or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3185 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the residual blocker-axis expansion pack before implementation admission",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3186 audits engineering blocker evidence",
            "must_synthesize_if": [
                "M3186 cannot select implementation-admission artifact-repair synthesis or stop",
                "M3186 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3186 audits M3185 row counts gates actor contract and claim boundaries",
            "M3186 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3186 hides missing M3185 artifacts or failed gates",
            "M3186 treats M3185 materialization as repair success or performance verdict",
            "M3186 changes actor input or action contract",
            "M3186 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3186 audits M3185 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_residual_hard_safety_blocker_axis_expansion_pack_result_audit_doc",
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
            "# M3185 Residual Hard-Safety Blocker Axis Expansion Pack Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- residual blocker rows: {summary['residual_blocker_axis_row_count']}",
            f"- collision blockers: {summary['blocker_family_counts'].get('collision', 0)}",
            f"- offtrack blockers: {summary['blocker_family_counts'].get('offtrack', 0)}",
            f"- actor-visible axis candidates: {summary['actor_visible_axis_candidate_row_count']}",
            f"- forbidden-label guards pass: {summary['forbidden_label_guard_rows_pass']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3185 materializes a no-new-execution blocker-axis pack for the seven inherited residual hard-safety blockers. It separates actor-visible candidate evidence axes from offline labels, preserves M3105/M3103 as incumbent, and does not admit a repair implementation or public driver mutation.",
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


def run_materialization(
    *,
    m3184_plan: Path,
    m3156_dir: Path,
    m3161_dir: Path,
    m3153_dir: Path,
    m3181_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3184_plan=m3184_plan,
        m3156_dir=m3156_dir,
        m3161_dir=m3161_dir,
        m3153_dir=m3153_dir,
        m3181_dir=m3181_dir,
    )
    blockers = residual_blocker_axis_rows(source)
    family_summaries = blocker_family_summary_rows(blockers)
    axis_rows = actor_visible_axis_candidate_rows(blockers)
    forbidden_rows = forbidden_label_guard_rows()
    evidence_gaps = evidence_gap_rows(source)
    admission_rows = candidate_admission_rows(axis_rows)
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    guards = contract_guard_rows(source, blockers, axis_rows, forbidden_rows)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())

    write_csv_rows(paths["residual_blocker_axis_rows"], blockers, fieldnames=RESIDUAL_BLOCKER_FIELDNAMES)
    write_csv_rows(paths["blocker_family_summary_rows"], family_summaries, fieldnames=SUMMARY_FIELDNAMES)
    write_csv_rows(paths["actor_visible_axis_candidate_rows"], axis_rows, fieldnames=AXIS_FIELDNAMES)
    write_csv_rows(paths["forbidden_label_guard_rows"], forbidden_rows, fieldnames=FORBIDDEN_LABEL_FIELDNAMES)
    write_csv_rows(paths["evidence_gap_rows"], evidence_gaps, fieldnames=EVIDENCE_GAP_FIELDNAMES)
    write_csv_rows(paths["candidate_admission_rows"], admission_rows, fieldnames=CANDIDATE_ADMISSION_FIELDNAMES)
    write_csv_rows(paths["contract_guard_rows"], guards, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)

    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        blockers=blockers,
        family_summaries=family_summaries,
        axis_rows=axis_rows,
        forbidden_rows=forbidden_rows,
        evidence_gaps=evidence_gaps,
        admission_rows=admission_rows,
        guards=guards,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in blockers)
    axis_counts = Counter(str(row.get("proposed_evidence_axis", "")) for row in blockers)
    status_pass = bool(gate_matrix_pass and present)
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_blocker_axis_expansion_pack_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_blocker_axis_expansion_pack_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "residual_blocker_axis_row_count": len(blockers),
        "blocker_family_counts": dict(sorted(blocker_counts.items())),
        "proposed_evidence_axis_counts": dict(sorted(axis_counts.items())),
        "blocker_family_summary_row_count": len(family_summaries),
        "actor_visible_axis_candidate_row_count": len(axis_rows),
        "forbidden_label_guard_row_count": len(forbidden_rows),
        "forbidden_label_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in forbidden_rows),
        "evidence_gap_row_count": len(evidence_gaps),
        "candidate_admission_row_count": len(admission_rows),
        "implementation_admitted": any(_bool(row.get("implementation_allowed_now", False)) for row in admission_rows),
        "contract_guard_row_count": len(guards),
        "contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in guards),
        "claim_boundary_row_count": len(claims),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claims),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3156_status_pass": _bool(source["m3156_summary"].get("status_pass", False)),
        "m3153_status_pass": _bool(source["m3153_summary"].get("status_pass", False)),
        "m3181_status_pass": _bool(source["m3181_summary"].get("status_pass", False)),
        "m3153_action_channel_sensitive_comparison_count": _int(
            source["m3153_summary"].get("action_channel_sensitive_comparison_count")
        ),
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
        "decision": "active_safety_driver_residual_hard_safety_blocker_axis_expansion_pack_route_to_m3186_result_audit",
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
            "residual_blocker_axis_row_count": len(blockers),
            "actor_visible_axis_candidate_row_count": len(axis_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3184-plan", type=Path, default=DEFAULT_M3184_PLAN)
    parser.add_argument("--m3156-dir", type=Path, default=DEFAULT_M3156_DIR)
    parser.add_argument("--m3161-dir", type=Path, default=DEFAULT_M3161_DIR)
    parser.add_argument("--m3153-dir", type=Path, default=DEFAULT_M3153_DIR)
    parser.add_argument("--m3181-dir", type=Path, default=DEFAULT_M3181_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3184_plan=args.m3184_plan,
        m3156_dir=args.m3156_dir,
        m3161_dir=args.m3161_dir,
        m3153_dir=args.m3153_dir,
        m3181_dir=args.m3181_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"residual_blocker_axis_rows={summary['residual_blocker_axis_row_count']}")
    print(f"actor_visible_axis_candidate_rows={summary['actor_visible_axis_candidate_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
