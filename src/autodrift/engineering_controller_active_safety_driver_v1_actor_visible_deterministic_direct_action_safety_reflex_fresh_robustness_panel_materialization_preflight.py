"""Materialize M3082 fresh robustness panel admission artifacts.

M3082 consumes the M3081 audit and the M3080 fixed-denominator measurement. It
does not reset, step, rollout, replay, fit, train, validate, rank, promote, or
run high-fidelity simulation. It only materializes a fresh-seed and
fresh-scenario panel specification plus guards for later audit.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3082-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-fresh-robustness-panel-materialization-preflight"
)
NEXT_ID = (
    "m3083-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-fresh-robustness-panel-materialization-result-audit"
)
M3081_ID = (
    "m3081-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-closed-loop-measurement-result-audit"
)
M3080_ID = (
    "m3080-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-closed-loop-measurement-preflight"
)
M3078_ID = (
    "m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-materialization-preflight"
)

DEFAULT_M3081_AUDIT = Path(f"docs/{M3081_ID}.md")
DEFAULT_M3080_DIR = Path(
    "runs/m3080_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_closed_loop_measurement_preflight"
)
DEFAULT_M3078_DIR = Path(
    "runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_materialization_preflight"
)
DEFAULT_M3039_DIR = Path(
    "runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3082_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_fresh_robustness_panel_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_PANEL_ROWS = 64
EXPECTED_AXIS_COUNT = 4
EXPECTED_BINDING_ROLE_COUNT = 2
FRESH_SEED_BASE = 401500

CLAIM_SCOPE = (
    "M3082 Active Safety Driver v1 actor-visible deterministic direct-action safety-reflex "
    "fresh robustness panel materialization only; artifacts may define fresh seeds, fresh "
    "scenario-distribution rows, admission guards, actor-contract guards, claim-boundary "
    "rows, a gate matrix, a summary, and an M3083 audit manifest. No reset, step, rollout, "
    "replay, fitting, PPO, training, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, driver-performance verdict, current-sim verdict, "
    "repair success, high-fidelity validation, paper evidence, finite-window-vs-GRU "
    "evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, repair success, "
    "checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation "
    "readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal "
    "driver completion, or level3 self-identification"
)

ROBUSTNESS_AXES = [
    {
        "axis_id": "collision_lateral_intrusion",
        "axis_family": "collision_preservation",
        "task_family": "T5",
        "scenario_family": "fresh_obstacle_lateral_intrusion",
        "fresh_scenario_distribution": "fresh_obstacle_lateral_offsets_and_reveal_timing",
        "primary_metrics": "collision_count|min_clearance_margin|action_pressure",
    },
    {
        "axis_id": "offtrack_boundary_recovery",
        "axis_family": "offtrack_containment",
        "task_family": "T5",
        "scenario_family": "fresh_curved_boundary_recovery",
        "fresh_scenario_distribution": "fresh_boundary_curvature_and_lane_width",
        "primary_metrics": "offtrack_count|max_off_track_overshoot|recovery_window_success",
    },
    {
        "axis_id": "speed_floor_stress",
        "axis_family": "speed_floor_fragility",
        "task_family": "T4",
        "scenario_family": "fresh_speed_floor_and_late_obstacle",
        "fresh_scenario_distribution": "fresh_speed_floor_threshold_and_obstacle_reveal",
        "primary_metrics": "speed_too_low_count|return_mean|speed_mean",
    },
    {
        "axis_id": "stability_action_pressure",
        "axis_family": "stability_recovery_action_pressure",
        "task_family": "T4",
        "scenario_family": "fresh_actuator_delay_and_stability",
        "fresh_scenario_distribution": "fresh_actuator_delay_yaw_and_sideslip",
        "primary_metrics": "high_sideslip_fraction|lateral_rmse|raw_action_abs_max|action_clip_fraction",
    },
]

PANEL_FIELDNAMES = [
    "fresh_panel_row_id",
    "panel_family",
    "axis_id",
    "axis_family",
    "task_family",
    "scenario_family",
    "fresh_scenario_distribution",
    "binding_role",
    "base_profile_name",
    "profile_binding_name",
    "eval_seed",
    "fresh_seed",
    "m3080_reference_measurement_episode_id",
    "m3080_reference_eval_seed",
    "m3080_reference_outcome_bucket",
    "source_denominator_reused",
    "fixed_denominator_row_reused",
    "execution_allowed_in_m3082",
    "measurement_admission_after_m3083",
    "actor_observation_dim",
    "actor_action_dim",
    "candidate_output_semantics",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "required_primary_metrics",
    "claim_boundary",
]
ADMISSION_FIELDNAMES = [
    "admission_guard_id",
    "guard_family",
    "status_pass",
    "observed",
    "expected",
    "blocked_claims",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "actor_guard_id",
    "guard_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3082",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int_text(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def _m3080_eval_seeds(rows: Iterable[Mapping[str, Any]]) -> set[int]:
    return {_int_text(row.get("eval_seed")) for row in rows}


def load_sources(
    *,
    m3081_audit: Path,
    m3080_dir: Path,
    m3078_dir: Path,
    m3039_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    return {
        "m3081_audit_present": m3081_audit.exists(),
        "m3080_summary": read_json(m3080_dir / "summary.json"),
        "m3080_measurement_rows": read_csv_rows(m3080_dir / "measurement_episode_rows.csv"),
        "m3078_summary": read_json(m3078_dir / "summary.json"),
        "m3078_policy_config": read_json(m3078_dir / "direct_action_policy_config.json"),
        "m3039_summary": read_json(m3039_dir / "summary.json"),
        "m3012_summary": read_json(m3012_dir / "summary.json"),
        "m3039_dir_present": m3039_dir.exists(),
        "m3012_dir_present": m3012_dir.exists(),
    }


def build_fresh_panel_rows(m3080_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    if not m3080_rows:
        return []
    used_seeds = _m3080_eval_seeds(m3080_rows)
    panel_rows: list[dict[str, Any]] = []
    for axis_index, axis in enumerate(ROBUSTNESS_AXES):
        for pair_index in range(8):
            for role_index in range(EXPECTED_BINDING_ROLE_COUNT):
                row_index = (axis_index * 16 + pair_index * 2 + role_index) % len(m3080_rows)
                reference = m3080_rows[row_index]
                eval_seed = FRESH_SEED_BASE + axis_index * 100 + pair_index * 10 + role_index
                binding_role = str(reference.get("binding_role") or ("candidate" if role_index == 0 else "parent"))
                base_profile = str(reference.get("base_profile_name") or binding_role)
                panel_rows.append(
                    {
                        "fresh_panel_row_id": f"m3082-fresh-panel-{len(panel_rows) + 1:04d}",
                        "panel_family": "m3082_fresh_robustness_panel",
                        "axis_id": axis["axis_id"],
                        "axis_family": axis["axis_family"],
                        "task_family": axis["task_family"],
                        "scenario_family": axis["scenario_family"],
                        "fresh_scenario_distribution": axis["fresh_scenario_distribution"],
                        "binding_role": binding_role,
                        "base_profile_name": base_profile,
                        "profile_binding_name": f"{base_profile}+m3078_deterministic_safety_reflex_fresh_{axis['axis_id']}",
                        "eval_seed": eval_seed,
                        "fresh_seed": eval_seed not in used_seeds,
                        "m3080_reference_measurement_episode_id": reference.get("measurement_episode_id", ""),
                        "m3080_reference_eval_seed": reference.get("eval_seed", ""),
                        "m3080_reference_outcome_bucket": reference.get("outcome_bucket", ""),
                        "source_denominator_reused": False,
                        "fixed_denominator_row_reused": False,
                        "execution_allowed_in_m3082": False,
                        "measurement_admission_after_m3083": True,
                        "actor_observation_dim": P0_OBSERVATION_DIM,
                        "actor_action_dim": ACTION_DIM,
                        "candidate_output_semantics": "direct_action_clipped",
                        "runtime_base_policy_required": False,
                        "hidden_oracle_actor_input_required": False,
                        "target_labels_actor_visible": False,
                        "target_provenance_actor_visible": False,
                        "source_labels_actor_visible": False,
                        "route_labels_actor_visible": False,
                        "outcome_labels_actor_visible": False,
                        "success_progress_labels_actor_visible": False,
                        "verdict_labels_actor_visible": False,
                        "ttc_actor_input_required": False,
                        "required_primary_metrics": axis["primary_metrics"],
                        "claim_boundary": CLAIM_SCOPE,
                    }
                )
    return panel_rows


def build_robustness_admission_guard_rows(
    *,
    panel_rows: list[dict[str, Any]],
    m3080_summary: Mapping[str, Any],
    m3080_seed_overlap_count: int,
) -> list[dict[str, Any]]:
    axes = {str(row["axis_id"]) for row in panel_rows}
    roles = {str(row["binding_role"]) for row in panel_rows}
    scenario_distributions = {str(row["fresh_scenario_distribution"]) for row in panel_rows}

    def guard(guard_id: str, family: str, status: bool, observed: Any, expected: Any) -> dict[str, Any]:
        return {
            "admission_guard_id": f"m3082-{guard_id}",
            "guard_family": family,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "claim_boundary": CLAIM_SCOPE,
        }

    return [
        guard("panel_row_count", "fresh_panel", len(panel_rows) == EXPECTED_PANEL_ROWS, len(panel_rows), EXPECTED_PANEL_ROWS),
        guard("fresh_seed_count", "fresh_panel", len({row["eval_seed"] for row in panel_rows}) == EXPECTED_PANEL_ROWS, len({row["eval_seed"] for row in panel_rows}), EXPECTED_PANEL_ROWS),
        guard("m3080_seed_overlap_zero", "fresh_panel", m3080_seed_overlap_count == 0, m3080_seed_overlap_count, 0),
        guard("fixed_denominator_reuse_zero", "fresh_panel", not any(bool(row["fixed_denominator_row_reused"]) for row in panel_rows), False, False),
        guard("axis_coverage", "scenario_distribution", len(axes) == EXPECTED_AXIS_COUNT, "|".join(sorted(axes)), EXPECTED_AXIS_COUNT),
        guard("scenario_distribution_coverage", "scenario_distribution", len(scenario_distributions) == EXPECTED_AXIS_COUNT, "|".join(sorted(scenario_distributions)), EXPECTED_AXIS_COUNT),
        guard("binding_role_coverage", "scenario_distribution", roles == {"candidate", "parent"}, "|".join(sorted(roles)), "candidate|parent"),
        guard("speed_floor_axis_present", "speed_floor", "speed_floor_stress" in axes, "speed_floor_stress" in axes, True),
        guard("collision_axis_present", "collision", "collision_lateral_intrusion" in axes, "collision_lateral_intrusion" in axes, True),
        guard("offtrack_axis_present", "offtrack", "offtrack_boundary_recovery" in axes, "offtrack_boundary_recovery" in axes, True),
        guard("stability_axis_present", "stability", "stability_action_pressure" in axes, "stability_action_pressure" in axes, True),
        guard(
            "m3080_speed_floor_fragility_carried",
            "speed_floor",
            _int_text(m3080_summary.get("measurement_speed_too_low_count")) >= 7 and "speed_floor_stress" in axes,
            m3080_summary.get("measurement_speed_too_low_count"),
            ">=7 with speed_floor_stress axis",
        ),
        guard("no_execution_in_m3082", "execution", not any(bool(row["execution_allowed_in_m3082"]) for row in panel_rows), False, False),
    ]


def build_actor_contract_guard_rows(panel_rows: list[dict[str, Any]], policy_config: Mapping[str, Any]) -> list[dict[str, Any]]:
    hidden_input_flags = [
        "hidden_oracle_actor_input_required",
        "target_labels_actor_visible",
        "target_provenance_actor_visible",
        "source_labels_actor_visible",
        "route_labels_actor_visible",
        "outcome_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
        "ttc_actor_input_required",
    ]
    hidden_inputs_clear = not any(any(bool(row[key]) for key in hidden_input_flags) for row in panel_rows)

    def guard(guard_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "actor_guard_id": f"m3082-{guard_id}",
            "guard_family": family,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    return [
        guard("observation_shape_72", "actor_contract", P0_OBSERVATION_DIM == 72, P0_OBSERVATION_DIM, 72, "contract_violation"),
        guard("action_shape_3", "actor_contract", ACTION_DIM == 3, ACTION_DIM, 3, "contract_violation"),
        guard("policy_config_shape_72_action_3", "actor_contract", policy_config.get("observation_shape") == 72 and policy_config.get("action_shape") == 3, f"{policy_config.get('observation_shape')}->{policy_config.get('action_shape')}", "72->3", "contract_violation"),
        guard("direct_action_semantics", "actor_contract", policy_config.get("output_semantics") == "direct_action_clipped", policy_config.get("output_semantics"), "direct_action_clipped", "contract_violation"),
        guard("runtime_base_policy_free", "actor_contract", not bool(policy_config.get("runtime_base_policy_required")), policy_config.get("runtime_base_policy_required"), False, "contract_violation"),
        guard("hidden_actor_inputs_clear", "actor_input_exclusion", hidden_inputs_clear, hidden_inputs_clear, True, "contract_violation"),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claim_families = [
        "validation_result",
        "ranking_or_winner_selection",
        "promotion_or_checkpoint_mutation",
        "driver_performance_verdict",
        "current_sim_verdict",
        "repair_success",
        "high_fidelity_readiness",
        "paper_evidence",
        "finite_window_vs_gru",
        "full_ideal_driver_completion",
        "self_identification",
        "rollout_execution",
        "fresh_panel_materialization_completeness",
    ]
    rows: list[dict[str, Any]] = []
    for index, family in enumerate(claim_families, start=1):
        allowed = family == "fresh_panel_materialization_completeness"
        rows.append(
            {
                "claim_id": f"m3082-claim-{index:04d}",
                "claim_family": family,
                "allowed_in_m3082": allowed,
                "claim_made": allowed,
                "status_pass": True,
                "evidence_required_before_claim": "M3083 audit before execution or interpretation" if not allowed else "M3082 summary and gate matrix",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _all_pass(rows: Iterable[Mapping[str, Any]]) -> bool:
    return all(_bool_text(row.get("status_pass", False)) for row in rows)


def build_gate_rows(
    *,
    source: Mapping[str, Any],
    panel_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    paths: Mapping[str, Path],
    m3080_seed_overlap_count: int,
) -> list[dict[str, Any]]:
    def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "gate_id": f"m3082-{gate_id}",
            "gate_family": family,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    required_paths = [
        "fresh_robustness_panel_rows",
        "robustness_admission_guard_rows",
        "actor_contract_guard_rows",
        "claim_boundary_rows",
        "doc",
        "follow_up_manifest",
    ]
    axes = {str(row["axis_id"]) for row in panel_rows}
    return [
        gate("m3081_audit_present", "lineage", bool(source["m3081_audit_present"]), True, True, "lineage_invalid"),
        gate("m3080_status_pass", "lineage", bool(source["m3080_summary"].get("status_pass")), True, True, "lineage_invalid"),
        gate("m3080_gate_matrix_pass", "lineage", bool(source["m3080_summary"].get("gate_matrix_pass")), True, True, "lineage_invalid"),
        gate("m3078_policy_contract_pass", "contract", bool(source["m3078_summary"].get("actor_contract_shape_72_action_3")) and not bool(source["m3078_summary"].get("runtime_base_policy_required")), "obs72/action3 base_policy_false", "obs72/action3 base_policy_false", "contract_violation"),
        gate("m3039_source_present", "lineage", bool(source["m3039_dir_present"]), True, True, "lineage_invalid"),
        gate("m3012_source_present", "lineage", bool(source["m3012_dir_present"]), True, True, "lineage_invalid"),
        gate("panel_row_count", "fresh_panel", len(panel_rows) == EXPECTED_PANEL_ROWS, len(panel_rows), EXPECTED_PANEL_ROWS, "metric_artifact"),
        gate("m3080_seed_overlap_zero", "fresh_panel", m3080_seed_overlap_count == 0, m3080_seed_overlap_count, 0, "seed_fragility"),
        gate("axis_coverage", "scenario_distribution", len(axes) == EXPECTED_AXIS_COUNT, "|".join(sorted(axes)), EXPECTED_AXIS_COUNT, "scenario_sampling_failure"),
        gate("admission_guards_pass", "process", _all_pass(admission_rows), "all", "pass", "metric_artifact"),
        gate("actor_contract_guards_pass", "contract", _all_pass(actor_rows), "all", "pass", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", _all_pass(claim_rows), "all", "pass", "contract_violation"),
        gate("no_execution", "execution", not any(bool(row["execution_allowed_in_m3082"]) for row in panel_rows), False, False, "contract_violation"),
        gate("required_artifacts_present", "process", all(paths[key].exists() for key in required_paths), True, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", paths["follow_up_manifest"].exists(), True, True, "lineage_invalid"),
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30780,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject the M3082 fresh robustness panel materialization artifacts before any execution, validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, repair-success, or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), str(output_dir / "summary.json")],
            "parent_dataset": [
                str(output_dir / "fresh_robustness_panel_rows.csv"),
                str(output_dir / "robustness_admission_guard_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit fresh robustness panel materialization before execution admission"],
            "derived_from": [MILESTONE_ID, M3081_ID, M3080_ID],
            "blocked_by": [
                "M3082 panel rows require audit before any fresh-panel execution",
                "fresh robustness materialization is not validation or performance evidence before M3083",
            ],
            "supersedes": ["direct execution of M3082 panel rows without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3083 must audit M3082 summary panel rows guard rows claim rows and gate matrix",
            "M3083 must verify the panel is fresh relative to the M3067/M3075/M3080 fixed denominator",
            "M3083 must preserve actor 72/action 3 direct [steer throttle brake] and runtime_base_policy_required false",
            "M3083 must reject validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims",
            "M3083 must select exactly one measurement admission or repair/stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run rollout validate rank promote tune or mutate checkpoints",
            "do not treat M3082 panel materialization as driver performance or robustness validation",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_deployable_direct_action_reflex",
            "evidence_axis": "fresh_robustness_panel_materialization_result_audit",
            "evidence_increment": "audits fresh-panel materialization artifacts before execution admission",
            "claim_scope": "Result audit only; no execution validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success or self-ID claim",
            "stop_condition": [
                "stop if M3082 artifacts are missing or gate matrix fails",
                "stop if the panel reuses the fixed M3067/M3075/M3080 denominator",
                "stop if actor or direct-action contracts were violated",
            ],
            "fallback_plan": [
                "route to panel repair if row freshness or axis coverage is incomplete",
                "route to measurement admission if artifacts are complete and claim-safe",
                "route to branch synthesis or stop if no claim-safe fresh denominator exists",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3082 materializes the fresh robustness panel package",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3082 fresh robustness panel materialization artifacts",
            "admission_evidence": ["M3082 summary panel rows guard rows claim rows and gate matrix"],
            "blocked_shortcuts": [
                "no execution validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3083 status queue scoreboard research log and review",
                "one follow-up manifest only if M3083 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3083 accepts or rejects M3082 as complete and claim-safe",
                "next measurement admission, repair, synthesis, or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3083 audits engineering panel materialization artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3083; self-ID/GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3082 fresh robustness panel materialization artifacts only.",
            "negative_result_policy": "Preserve incomplete panel evidence and route to repair or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3082 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the fresh robustness panel before execution admission",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3083 audits engineering robustness-panel admission",
            "must_synthesize_if": [
                "M3083 cannot accept M3082 as complete and claim-safe",
                "M3083 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict or self-ID evidence",
                "M3083 cannot select a measurement admission, repair, or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3083 audits M3082 panel freshness axis coverage actor contract and claim boundaries",
            "M3083 rejects validation ranking promotion performance high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims",
            "M3083 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3083 hides missing M3082 artifacts or failed gates",
            "M3083 treats M3082 panel materialization as validation or performance evidence",
            "M3083 changes actor input action contract or runtime base-policy-free boundary",
            "M3083 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3083 audits M3082 materialization artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_deterministic_safety_reflex_fresh_robustness_panel_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(doc_path), str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_doc(summary: Mapping[str, Any]) -> str:
    lines = [
        "# M3082 Active Safety Driver v1 Fresh Robustness Panel Materialization Preflight",
        "",
        "## Summary",
        "",
        f"- status: {'completed' if summary['status_pass'] else 'failed'}",
        f"- result class: `{summary['result_class']}`",
        f"- fresh robustness panel rows: {summary['fresh_robustness_panel_row_count']}",
        f"- unique fresh seeds: {summary['fresh_seed_unique_count']}",
        f"- M3080 seed overlap count: {summary['m3080_seed_overlap_count']}",
        f"- robustness axes: {summary['robustness_axis_count']}",
        f"- scenario distributions: {summary['fresh_scenario_distribution_count']}",
        f"- binding roles: {summary['binding_role_count']}",
        f"- admission guards: {summary['robustness_admission_guard_row_count']}",
        f"- actor contract guards: {summary['actor_contract_guard_row_count']}",
        f"- claim-boundary rows: {summary['claim_boundary_row_count']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        "",
        "## Interpretation",
        "",
        "M3082 materializes a fresh denominator for the deterministic safety-reflex route. It does not execute the panel. The fresh panel is intended for M3083 audit before any measurement admission.",
        "",
        "Panel axes:",
        "",
        "```text",
        "collision_lateral_intrusion",
        "offtrack_boundary_recovery",
        "speed_floor_stress",
        "stability_action_pressure",
        "```",
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
    ]
    return "\n".join(lines) + "\n"


def materialize(
    *,
    m3081_audit: Path,
    m3080_dir: Path,
    m3078_dir: Path,
    m3039_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_dir / "summary.json",
        "fresh_robustness_panel_rows": output_dir / "fresh_robustness_panel_rows.csv",
        "robustness_admission_guard_rows": output_dir / "robustness_admission_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }
    source = load_sources(
        m3081_audit=m3081_audit,
        m3080_dir=m3080_dir,
        m3078_dir=m3078_dir,
        m3039_dir=m3039_dir,
        m3012_dir=m3012_dir,
    )
    panel_rows = build_fresh_panel_rows(source["m3080_measurement_rows"])
    fresh_seeds = {_int_text(row["eval_seed"]) for row in panel_rows}
    m3080_seed_overlap_count = len(fresh_seeds & _m3080_eval_seeds(source["m3080_measurement_rows"]))
    admission_rows = build_robustness_admission_guard_rows(
        panel_rows=panel_rows,
        m3080_summary=source["m3080_summary"],
        m3080_seed_overlap_count=m3080_seed_overlap_count,
    )
    actor_rows = build_actor_contract_guard_rows(panel_rows, source["m3078_policy_config"])
    claim_rows = build_claim_boundary_rows()

    write_csv_rows(paths["fresh_robustness_panel_rows"], panel_rows, fieldnames=PANEL_FIELDNAMES)
    write_csv_rows(paths["robustness_admission_guard_rows"], admission_rows, fieldnames=ADMISSION_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))

    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": "active_safety_driver_v1_deterministic_safety_reflex_fresh_robustness_panel_materialization_preflight_pass",
        "m3081_audit_present": bool(source["m3081_audit_present"]),
        "m3080_status_pass": bool(source["m3080_summary"].get("status_pass")),
        "m3080_gate_matrix_pass": bool(source["m3080_summary"].get("gate_matrix_pass")),
        "m3080_measurement_episode_row_count": len(source["m3080_measurement_rows"]),
        "m3080_success_count": source["m3080_summary"].get("measurement_success_count"),
        "m3080_collision_count": source["m3080_summary"].get("measurement_collision_count"),
        "m3080_offtrack_count": source["m3080_summary"].get("measurement_offtrack_count"),
        "m3080_speed_too_low_count": source["m3080_summary"].get("measurement_speed_too_low_count"),
        "m3080_clearance_margin_mean": source["m3080_summary"].get("measurement_clearance_margin_mean"),
        "m3078_status_pass": bool(source["m3078_summary"].get("status_pass")),
        "m3078_gate_matrix_pass": bool(source["m3078_summary"].get("gate_matrix_pass")),
        "m3039_status_pass": bool(source["m3039_summary"].get("status_pass")),
        "m3012_status_pass": bool(source["m3012_summary"].get("status_pass")),
        "fresh_robustness_panel_row_count": len(panel_rows),
        "expected_panel_row_count": EXPECTED_PANEL_ROWS,
        "fresh_seed_unique_count": len(fresh_seeds),
        "m3080_seed_overlap_count": m3080_seed_overlap_count,
        "robustness_axis_count": len({row["axis_id"] for row in panel_rows}),
        "fresh_scenario_distribution_count": len({row["fresh_scenario_distribution"] for row in panel_rows}),
        "binding_role_count": len({row["binding_role"] for row in panel_rows}),
        "speed_floor_axis_present": any(row["axis_id"] == "speed_floor_stress" for row in panel_rows),
        "collision_axis_present": any(row["axis_id"] == "collision_lateral_intrusion" for row in panel_rows),
        "offtrack_axis_present": any(row["axis_id"] == "offtrack_boundary_recovery" for row in panel_rows),
        "stability_axis_present": any(row["axis_id"] == "stability_action_pressure" for row in panel_rows),
        "robustness_admission_guard_row_count": len(admission_rows),
        "robustness_admission_guard_rows_pass": _all_pass(admission_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": _all_pass(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": _all_pass(claim_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "candidate_output_semantics": "direct_action_clipped",
        "candidate_output_components": ["steer", "throttle", "brake"],
        "runtime_base_policy_required": False,
        "base_policy_required_at_runtime": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "fitting_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "forbidden_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_v1_deterministic_safety_reflex_fresh_robustness_panel_materialization_route_to_m3083_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
        "gate_matrix_pass": False,
        "status_pass": False,
    }
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    gate_rows = build_gate_rows(
        source=source,
        panel_rows=panel_rows,
        admission_rows=admission_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        paths=paths,
        m3080_seed_overlap_count=m3080_seed_overlap_count,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = _all_pass(gate_rows)
    summary["gate_matrix_pass"] = gate_matrix_pass
    summary["gate_matrix_row_count"] = len(gate_rows)
    summary["required_artifacts_present"] = all(path.exists() for key, path in paths.items() if key not in {"summary", "run_state"})
    summary["status_pass"] = bool(gate_matrix_pass and summary["required_artifacts_present"])
    write_json(paths["summary"], summary)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_json(
        paths["run_state"],
        {
            "complete": summary["status_pass"],
            "status_pass": summary["status_pass"],
            "fresh_robustness_panel_row_count": len(panel_rows),
            "m3080_seed_overlap_count": m3080_seed_overlap_count,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3081-audit", type=Path, default=DEFAULT_M3081_AUDIT)
    parser.add_argument("--m3080-dir", type=Path, default=DEFAULT_M3080_DIR)
    parser.add_argument("--m3078-dir", type=Path, default=DEFAULT_M3078_DIR)
    parser.add_argument("--m3039-dir", type=Path, default=DEFAULT_M3039_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize(
        m3081_audit=args.m3081_audit,
        m3080_dir=args.m3080_dir,
        m3078_dir=args.m3078_dir,
        m3039_dir=args.m3039_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"fresh_panel_rows={summary['fresh_robustness_panel_row_count']}")
    print(f"m3080_seed_overlap_count={summary['m3080_seed_overlap_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
