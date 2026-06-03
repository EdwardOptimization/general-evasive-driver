"""No-rollout materialization of engineering-controller behavior/outcome protocol."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


PROTOCOL_VERSION = "engineering_controller_behavior_outcome_v0"
DEFAULT_MILESTONE = "m2514-engineering-controller-behavior-outcome-protocol-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2515-engineering-controller-behavior-outcome-protocol-materialization-result-audit"

M2513_DESIGN = "docs/m2513-engineering-controller-behavior-outcome-protocol-design.md"
M2512_SYNTHESIS = "docs/m2512-engineering-controller-route-a-artifact-set-branch-synthesis.md"
M2510_SUMMARY = "runs/m2510_engineering_controller_known_failure_taxonomy/summary.json"
M2510_TAXONOMY = "runs/m2510_engineering_controller_known_failure_taxonomy/failure_taxonomy.csv"
M2505_SUMMARY = "public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json"
OBSERVATION_CONTRACT = "docs/observation-contract.md"
POST_M2470_ROUTE_PLAN = "docs/post-m2470-route-plan.md"

ROW_SCHEMA_FIELDNAMES = [
    "field_name",
    "field_family",
    "dtype",
    "required",
    "nullable",
    "actor_visible",
    "allowed_values",
    "claim_boundary",
    "description",
]
METRIC_REGISTRY_FIELDNAMES = [
    "metric_name",
    "metric_family",
    "dtype",
    "actor_visible",
    "aggregation_allowed_initially",
    "requires_future_manifest_for_claim",
    "forbidden_as_claim",
    "description",
]
AUDIT_GATE_FIELDNAMES = [
    "gate_id",
    "gate_stage",
    "required_before",
    "failure_type",
    "pass_condition",
    "forbidden_interpretation",
]
LAYER_REGISTRY_FIELDNAMES = [
    "evidence_layer",
    "purpose",
    "allowed_claim_scope",
    "permitted_now",
    "requires_future_manifest",
    "forbidden_interpretation",
]
FORBIDDEN_REGISTRY_FIELDNAMES = [
    "item_id",
    "category",
    "forbidden_signal_or_shortcut",
    "forbidden_context",
    "reason",
]

REQUIRED_LAYERS = [
    "source_only_diagnostic",
    "current_sim_diagnostic_mining",
    "future_high_fidelity_validation",
]
SCENARIO_ROLES = [
    "stable_avoidable",
    "stable_aes",
    "drift_required_recovery",
    "hidden_dynamics_robustness",
    "unavoidable_mitigation",
]
ACTOR_CONTRACT = {
    "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
    "observation_shape": 72,
    "action_shape": 3,
    "actor_encoder": "human_view_online_gru",
    "action_horizon": 1,
    "action": "[steering_command, throttle_command, brake_command]",
    "no_hidden_oracle_actor_inputs": True,
}


def materialize_behavior_outcome_protocol(
    output_dir: Path,
    *,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = _load_source_artifacts()

    row_schema = build_row_schema()
    metric_registry = build_metric_registry()
    audit_gate_registry = build_audit_gate_registry()
    layer_registry = build_layer_registry()
    forbidden_registry = build_forbidden_registry()
    protocol_schema = build_protocol_schema(
        row_schema=row_schema,
        metric_registry=metric_registry,
        audit_gate_registry=audit_gate_registry,
        layer_registry=layer_registry,
        forbidden_registry=forbidden_registry,
    )

    row_schema_path = output_dir / "row_schema.csv"
    metric_registry_path = output_dir / "metric_registry.csv"
    audit_gate_registry_path = output_dir / "audit_gate_registry.csv"
    layer_registry_path = output_dir / "layer_registry.csv"
    forbidden_registry_path = output_dir / "forbidden_registry.csv"
    protocol_schema_path = output_dir / "protocol_schema.json"

    write_csv_rows(row_schema_path, row_schema, fieldnames=ROW_SCHEMA_FIELDNAMES)
    write_csv_rows(metric_registry_path, metric_registry, fieldnames=METRIC_REGISTRY_FIELDNAMES)
    write_csv_rows(audit_gate_registry_path, audit_gate_registry, fieldnames=AUDIT_GATE_FIELDNAMES)
    write_csv_rows(layer_registry_path, layer_registry, fieldnames=LAYER_REGISTRY_FIELDNAMES)
    write_csv_rows(forbidden_registry_path, forbidden_registry, fieldnames=FORBIDDEN_REGISTRY_FIELDNAMES)
    write_json(protocol_schema_path, protocol_schema)

    summary = _summary(
        output_dir=output_dir,
        source=source,
        row_schema=row_schema,
        metric_registry=metric_registry,
        audit_gate_registry=audit_gate_registry,
        layer_registry=layer_registry,
        forbidden_registry=forbidden_registry,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def _load_source_artifacts() -> dict[str, Any]:
    return {
        "m2510_summary": read_json(M2510_SUMMARY),
        "m2510_taxonomy_rows": _read_csv_rows(M2510_TAXONOMY),
        "m2505_summary": read_json(M2505_SUMMARY),
        "source_exists": {
            M2513_DESIGN: Path(M2513_DESIGN).exists(),
            M2512_SYNTHESIS: Path(M2512_SYNTHESIS).exists(),
            M2510_SUMMARY: Path(M2510_SUMMARY).exists(),
            M2510_TAXONOMY: Path(M2510_TAXONOMY).exists(),
            M2505_SUMMARY: Path(M2505_SUMMARY).exists(),
            OBSERVATION_CONTRACT: Path(OBSERVATION_CONTRACT).exists(),
            POST_M2470_ROUTE_PLAN: Path(POST_M2470_ROUTE_PLAN).exists(),
        },
    }


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_protocol_schema(
    *,
    row_schema: list[dict[str, Any]],
    metric_registry: list[dict[str, Any]],
    audit_gate_registry: list[dict[str, Any]],
    layer_registry: list[dict[str, Any]],
    forbidden_registry: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "claim_scope": "no-rollout engineering-controller behavior/outcome protocol materialization",
        "actor_contract": dict(ACTOR_CONTRACT),
        "scenario_roles": list(SCENARIO_ROLES),
        "evidence_layers": [row["evidence_layer"] for row in layer_registry],
        "row_schema_fields": [row["field_name"] for row in row_schema],
        "metric_names": [row["metric_name"] for row in metric_registry],
        "audit_gate_ids": [row["gate_id"] for row in audit_gate_registry],
        "forbidden_items": [row["item_id"] for row in forbidden_registry],
        "source_artifacts": [
            M2513_DESIGN,
            M2512_SYNTHESIS,
            M2510_SUMMARY,
            M2510_TAXONOMY,
            M2505_SUMMARY,
            OBSERVATION_CONTRACT,
            POST_M2470_ROUTE_PLAN,
        ],
        "allowed_initial_operations": [
            "schema_materialization",
            "registry_materialization",
            "row_completeness_preflight",
            "diagnostic_no_ranking_summary",
        ],
        "forbidden_initial_operations": [
            "environment_rollout",
            "simulator_step",
            "policy_action_execution",
            "training",
            "replay",
            "ppo",
            "controller_ranking",
            "winner_selection",
            "success_rate_verdict",
            "driver_performance_claim",
            "high_fidelity_validation_claim",
            "paper_claim",
            "finite_window_vs_gru_claim",
            "level3_self_identification_claim",
        ],
    }


def build_row_schema() -> list[dict[str, Any]]:
    rows = [
        _row("protocol_version", "identity", "string", False, "", "protocol registry version"),
        _row("milestone_id", "identity", "string", False, "", "emitting milestone id"),
        _row("run_id", "identity", "string", False, "", "run or artifact id"),
        _row("row_id", "identity", "string", False, "", "stable row id"),
        _row("evidence_layer", "layer", "enum", False, "|".join(REQUIRED_LAYERS), "protocol evidence layer"),
        _row("surface_id", "layer", "string", False, "", "source surface or backend id"),
        _row("scenario_role", "metadata", "enum", False, "|".join(SCENARIO_ROLES), "metadata role, never actor input"),
        _row("fixture_id", "metadata", "string", True, "", "fixture id when applicable"),
        _row("seed", "metadata", "integer", True, "", "seed when applicable"),
        _row("subject_id", "metadata", "string", False, "", "policy or diagnostic reference id"),
        _row("checkpoint_path", "metadata", "string", True, "", "checkpoint path when applicable"),
        _row("actor_contract_id", "contract", "string", False, ACTOR_CONTRACT["actor_contract_id"], "actor contract id"),
        _row("observation_shape", "contract", "integer", False, "72", "P0 observation shape"),
        _row("action_shape", "contract", "integer", False, "3", "deployed action shape"),
        _row("actor_encoder", "contract", "string", False, "human_view_online_gru", "actor encoder"),
        _row("action_horizon", "contract", "integer", False, "1", "executed action horizon"),
        _row("actor_input_leak_flags", "contract", "string", False, "", "serialized leak flags; empty means none"),
        _row("reset_status", "episode_status", "string", False, "", "reset status"),
        _row("backend_status", "episode_status", "string", False, "", "backend status"),
        _row("episode_started", "episode_status", "boolean", False, "true|false", "whether episode started"),
        _row("episode_completed", "episode_status", "boolean", False, "true|false", "whether episode completed"),
        _row("step_count", "episode_status", "integer", False, "", "attempted step count"),
        _row("terminal_status", "episode_status", "string", True, "", "terminal status if any"),
        _row("action_finite", "contract", "boolean", False, "true|false", "all action values finite"),
        _row("action_within_bounds", "contract", "boolean", False, "true|false", "all action values within bounds"),
        _row("collision_event", "avoidance_boundary", "boolean", True, "true|false", "collision event"),
        _row("obstacle_passed_event", "avoidance_boundary", "boolean", True, "true|false", "obstacle passed event"),
        _row("road_departure_event", "avoidance_boundary", "boolean", True, "true|false", "road departure event"),
        _row("minimum_obstacle_clearance_m", "avoidance_boundary", "float", True, "", "posthoc logged clearance, not actor input"),
        _row("minimum_road_margin_m", "avoidance_boundary", "float", True, "", "posthoc road margin"),
        _row("final_road_margin_m", "avoidance_boundary", "float", True, "", "final road margin"),
        _row("maximum_abs_lateral_velocity", "response_recovery", "float", True, "", "maximum absolute lateral velocity"),
        _row("maximum_abs_yaw_rate", "response_recovery", "float", True, "", "maximum absolute yaw rate"),
        _row("maximum_abs_lateral_position", "response_recovery", "float", True, "", "maximum absolute lateral position"),
        _row("final_abs_lateral_velocity", "response_recovery", "float", True, "", "final absolute lateral velocity"),
        _row("final_abs_yaw_rate", "response_recovery", "float", True, "", "final absolute yaw rate"),
        _row("recovery_time_proxy_s", "response_recovery", "float", True, "", "logged recovery proxy, no path-error oracle"),
        _row("steering_saturation_fraction", "actuator_smoothness", "float", True, "", "steering saturation fraction"),
        _row("throttle_saturation_fraction", "actuator_smoothness", "float", True, "", "throttle saturation fraction"),
        _row("brake_saturation_fraction", "actuator_smoothness", "float", True, "", "brake saturation fraction"),
        _row("command_delta_l1_mean", "actuator_smoothness", "float", True, "", "mean command delta L1"),
        _row("simultaneous_throttle_brake_fraction", "actuator_smoothness", "float", True, "", "simultaneous pedal fraction"),
        _row("collision_speed_proxy", "mitigation", "float", True, "", "collision speed proxy"),
        _row("impact_angle_proxy", "mitigation", "float", True, "", "impact angle proxy"),
        _row("severity_proxy", "mitigation", "float", True, "", "mitigation severity proxy"),
        _row("mitigation_delta_against_reference", "mitigation", "float", True, "", "pre-registered diagnostic reference delta only"),
        _row("metric_completeness_flags", "metadata_completeness", "string", False, "", "explicit missing metric flags"),
        _row("diagnostic_only_no_ranking_claim", "claim_boundary", "boolean", False, "true", "must remain true before ranking admission"),
        _row("claim_scope", "claim_boundary", "string", False, "", "row-level claim scope"),
        _row("forbidden_interpretation", "claim_boundary", "string", False, "", "forbidden interpretation"),
        _row("source_artifact", "lineage", "string", False, "", "source artifact path"),
    ]
    return rows


def _row(
    field_name: str,
    family: str,
    dtype: str,
    nullable: bool,
    allowed_values: str,
    description: str,
) -> dict[str, Any]:
    return {
        "field_name": field_name,
        "field_family": family,
        "dtype": dtype,
        "required": True,
        "nullable": bool(nullable),
        "actor_visible": False,
        "allowed_values": allowed_values,
        "claim_boundary": "evaluator_side_only_not_actor_input",
        "description": description,
    }


def build_metric_registry() -> list[dict[str, Any]]:
    metric_specs = [
        ("observation_shape", "contract", "integer", "required actor contract check"),
        ("action_shape", "contract", "integer", "required action contract check"),
        ("actor_contract_id", "contract", "string", "contract lineage id"),
        ("actor_input_leak_flags", "contract", "string", "no hidden/oracle actor input flags"),
        ("action_finite", "contract", "boolean", "finite action check"),
        ("action_within_bounds", "contract", "boolean", "bounded action check"),
        ("episode_started", "episode_status", "boolean", "episode started flag"),
        ("episode_completed", "episode_status", "boolean", "episode completed flag"),
        ("terminal_status", "episode_status", "string", "terminal status"),
        ("step_count", "episode_status", "integer", "attempted step count"),
        ("reset_status", "episode_status", "string", "reset status"),
        ("backend_status", "episode_status", "string", "backend status"),
        ("collision_event", "avoidance_boundary", "boolean", "collision event"),
        ("obstacle_passed_event", "avoidance_boundary", "boolean", "obstacle passed event"),
        ("road_departure_event", "avoidance_boundary", "boolean", "road departure event"),
        ("minimum_obstacle_clearance_m", "avoidance_boundary", "float", "posthoc clearance"),
        ("minimum_road_margin_m", "avoidance_boundary", "float", "road margin"),
        ("final_road_margin_m", "avoidance_boundary", "float", "final road margin"),
        ("maximum_abs_lateral_velocity", "response_recovery", "float", "response envelope"),
        ("maximum_abs_yaw_rate", "response_recovery", "float", "response envelope"),
        ("maximum_abs_lateral_position", "response_recovery", "float", "response envelope"),
        ("final_abs_lateral_velocity", "response_recovery", "float", "recovery proxy"),
        ("final_abs_yaw_rate", "response_recovery", "float", "recovery proxy"),
        ("recovery_time_proxy_s", "response_recovery", "float", "recovery timing proxy"),
        ("steering_saturation_fraction", "actuator_smoothness", "float", "steering saturation"),
        ("throttle_saturation_fraction", "actuator_smoothness", "float", "throttle saturation"),
        ("brake_saturation_fraction", "actuator_smoothness", "float", "brake saturation"),
        ("command_delta_l1_mean", "actuator_smoothness", "float", "command smoothness"),
        ("simultaneous_throttle_brake_fraction", "actuator_smoothness", "float", "pedal conflict diagnostic"),
        ("collision_speed_proxy", "mitigation", "float", "mitigation proxy"),
        ("impact_angle_proxy", "mitigation", "float", "mitigation proxy"),
        ("severity_proxy", "mitigation", "float", "mitigation proxy"),
        ("mitigation_delta_against_reference", "mitigation", "float", "diagnostic reference delta"),
        ("evidence_layer", "metadata_completeness", "enum", "layer id"),
        ("scenario_role", "metadata_completeness", "enum", "metadata role"),
        ("subject_id", "metadata_completeness", "string", "subject id"),
        ("fixture_id", "metadata_completeness", "string", "fixture id"),
        ("seed", "metadata_completeness", "integer", "seed id"),
        ("metric_completeness_flags", "metadata_completeness", "string", "explicit missing metrics"),
        ("diagnostic_only_no_ranking_claim", "metadata_completeness", "boolean", "claim boundary flag"),
    ]
    return [
        {
            "metric_name": name,
            "metric_family": family,
            "dtype": dtype,
            "actor_visible": False,
            "aggregation_allowed_initially": family in {"contract", "episode_status", "metadata_completeness"},
            "requires_future_manifest_for_claim": True,
            "forbidden_as_claim": name in {"diagnostic_only_no_ranking_claim"} or family != "contract",
            "description": description,
        }
        for name, family, dtype, description in metric_specs
    ]


def build_audit_gate_registry() -> list[dict[str, Any]]:
    return [
        _gate("actor_contract_72_3", "pre_execution", "any_materialized_row", "contract_violation", "observation_shape == 72 and action_shape == 3", "changed actor/action contract"),
        _gate("no_hidden_oracle_actor_inputs", "pre_execution", "any_materialized_row", "contract_violation", "actor_input_leak_flags empty or false", "hidden/oracle actor features"),
        _gate("protocol_layer_present", "pre_execution", "any_materialized_row", "lineage_invalid", "evidence_layer in registered layers", "unregistered evidence layer"),
        _gate("scenario_role_metadata_only", "pre_execution", "any_materialized_row", "contract_violation", "scenario_role present only as metadata", "scenario role as actor input"),
        _gate("row_schema_complete", "pre_execution", "materialization", "metric_artifact", "all required row fields emitted", "partial schema without completeness flags"),
        _gate("metric_registry_complete", "pre_execution", "materialization", "metric_artifact", "all metric families registered", "unregistered metric interpretation"),
        _gate("forbidden_registry_complete", "pre_execution", "materialization", "metric_artifact", "forbidden actor inputs and outcome shortcuts registered", "silent oracle or ranking shortcut"),
        _gate("layer_separation_preserved", "pre_execution", "materialization", "validation_boundary", "source-only current-sim and HF layers remain separate", "source-only row as HF validation"),
        _gate("all_attempted_rows_retained", "future_execution", "measured_behavior_claim", "lineage_invalid", "attempted rows include failures and resets", "denominator pruning"),
        _gate("reset_vs_behavior_failure_split", "future_execution", "measured_behavior_claim", "scenario_sampling_failure", "reset failures separated from behavior failures", "sampler artifact as behavior failure"),
        _gate("metric_completeness_per_row", "future_execution", "measured_behavior_claim", "metric_artifact", "metric_completeness_flags populated", "missing metric silently dropped"),
        _gate("same_case_denominators", "future_execution", "comparison_claim", "objective_overfit", "same-case denominators preserved", "case-mismatched comparison"),
        _gate("no_ranking_or_winner_fields", "future_execution", "any_behavior_artifact", "metric_artifact", "ranking_run false and winner_selected false", "controller ranking or winner"),
        _gate("source_only_diagnostic_claim_only", "claim", "source_only_diagnostic_rows", "validation_boundary", "claim_scope diagnostic only", "source-only performance or validation claim"),
        _gate("hf_validation_requires_later_audit", "claim", "future_high_fidelity_validation_rows", "validation_boundary", "separate HF validation audit exists", "HF validation readiness from protocol materialization"),
    ]


def _gate(
    gate_id: str,
    stage: str,
    required_before: str,
    failure_type: str,
    pass_condition: str,
    forbidden_interpretation: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_stage": stage,
        "required_before": required_before,
        "failure_type": failure_type,
        "pass_condition": pass_condition,
        "forbidden_interpretation": forbidden_interpretation,
    }


def build_layer_registry() -> list[dict[str, Any]]:
    return [
        {
            "evidence_layer": "source_only_diagnostic",
            "purpose": "debug schema completeness and behavior instrumentation on source-only artifacts",
            "allowed_claim_scope": "diagnostic behavior instrumentation only",
            "permitted_now": True,
            "requires_future_manifest": False,
            "forbidden_interpretation": "driver performance or scenario generalization",
        },
        {
            "evidence_layer": "current_sim_diagnostic_mining",
            "purpose": "fast diagnostic/mining layer after explicit admission",
            "allowed_claim_scope": "diagnostic/mining evidence only",
            "permitted_now": False,
            "requires_future_manifest": True,
            "forbidden_interpretation": "current-sim benchmark readiness",
        },
        {
            "evidence_layer": "future_high_fidelity_validation",
            "purpose": "external high-fidelity validation after parity and admission gates",
            "allowed_claim_scope": "validation evidence only after later validation audit",
            "permitted_now": False,
            "requires_future_manifest": True,
            "forbidden_interpretation": "high-fidelity validation readiness",
        },
    ]


def build_forbidden_registry() -> list[dict[str, Any]]:
    actor_forbidden = [
        "mu",
        "mass",
        "inertia",
        "cg_shift",
        "tire_stiffness",
        "brake_scale",
        "drive_scale",
        "actuator_tau",
        "slip",
        "tire_force",
        "tire_saturation_label",
        "controller_mode",
        "scenario_role",
        "speed_ref",
        "beta_target",
        "path_error",
        "heading_error",
        "path_curvature",
        "ttc",
        "required_clearance",
        "oracle_stopping_distance",
        "oracle_feasibility",
        "aeb_aes_drift_labels",
        "reward_terms",
        "progress_counters",
        "collision_labels",
        "success_labels",
    ]
    outcome_forbidden = [
        "single_scalar_driver_score",
        "mixed_role_success_rate_aggregate",
        "controller_ranking",
        "winner_selection",
        "scenario_generalization_from_fixed_public_fixtures",
        "current_sim_benchmark_verdict_from_source_only_rows",
        "high_fidelity_validation_readiness_from_source_only_rows",
        "paper_level_claim_from_engineering_diagnostics",
        "finite_window_vs_gru_conclusion",
        "level3_self_identification_conclusion",
        "manual_rule_switch_labels_as_acceptance",
        "precomputed_avoidance_progress_labels_as_success",
    ]
    rows: list[dict[str, Any]] = []
    for item in actor_forbidden:
        rows.append(
            {
                "item_id": f"actor_forbidden_{item}",
                "category": "forbidden_actor_input",
                "forbidden_signal_or_shortcut": item,
                "forbidden_context": "actor_input",
                "reason": "not deployable human-view input or is an oracle/teacher signal",
            }
        )
    for item in outcome_forbidden:
        rows.append(
            {
                "item_id": f"outcome_forbidden_{item}",
                "category": "forbidden_outcome_shortcut",
                "forbidden_signal_or_shortcut": item,
                "forbidden_context": "claim_or_aggregation",
                "reason": "would convert diagnostic outcome rows into an unsupported verdict",
            }
        )
    return rows


def _summary(
    *,
    output_dir: Path,
    source: dict[str, Any],
    row_schema: list[dict[str, Any]],
    metric_registry: list[dict[str, Any]],
    audit_gate_registry: list[dict[str, Any]],
    layer_registry: list[dict[str, Any]],
    forbidden_registry: list[dict[str, Any]],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    paths = {
        "summary": output_dir / "summary.json",
        "protocol_schema": output_dir / "protocol_schema.json",
        "row_schema": output_dir / "row_schema.csv",
        "metric_registry": output_dir / "metric_registry.csv",
        "audit_gate_registry": output_dir / "audit_gate_registry.csv",
        "layer_registry": output_dir / "layer_registry.csv",
        "forbidden_registry": output_dir / "forbidden_registry.csv",
    }
    required_paths = [path for key, path in paths.items() if key != "summary"]
    required_artifacts_present = all(path.exists() for path in required_paths)
    row_fields = {row["field_name"] for row in row_schema}
    metric_names = {row["metric_name"] for row in metric_registry}
    layer_names = {row["evidence_layer"] for row in layer_registry}
    forbidden_categories = {row["category"] for row in forbidden_registry}
    source_artifacts_exist = all(bool(value) for value in source["source_exists"].values())
    missing_source_artifacts = [
        path for path, exists in source["source_exists"].items() if not bool(exists)
    ]
    m2510_summary = source["m2510_summary"]
    m2505_summary = source["m2505_summary"]
    actor_contract_shape_72_action_3 = (
        ACTOR_CONTRACT["observation_shape"] == 72
        and ACTOR_CONTRACT["action_shape"] == 3
        and bool(m2510_summary.get("actor_contract_shape_72_action_3"))
        and bool(m2505_summary.get("actor_contract_shape_72_action_3"))
    )
    false_flags = _false_claim_flags()
    status_pass = (
        required_artifacts_present
        and source_artifacts_exist
        and actor_contract_shape_72_action_3
        and set(REQUIRED_LAYERS).issubset(layer_names)
        and set(SCENARIO_ROLES)
        and len(row_schema) >= 45
        and len(metric_registry) >= 35
        and len(audit_gate_registry) >= 12
        and {"forbidden_actor_input", "forbidden_outcome_shortcut"}.issubset(
            forbidden_categories
        )
        and {"diagnostic_only_no_ranking_claim", "metric_completeness_flags"}.issubset(
            row_fields
        )
        and "mixed_role_success_rate_aggregate"
        in {row["forbidden_signal_or_shortcut"] for row in forbidden_registry}
        and "minimum_obstacle_clearance_m" in metric_names
        and not any(false_flags.values())
    )
    return {
        "result_class": (
            "engineering_controller_behavior_outcome_protocol_materialization_pass"
            if status_pass
            else "engineering_controller_behavior_outcome_protocol_materialization_failed"
        ),
        "status_pass": bool(status_pass),
        "protocol_version": PROTOCOL_VERSION,
        "milestone": str(milestone),
        "generated_at_utc": utc_timestamp(),
        "next_blocker": str(next_blocker),
        "protocol_schema": str(paths["protocol_schema"]),
        "row_schema": str(paths["row_schema"]),
        "metric_registry": str(paths["metric_registry"]),
        "audit_gate_registry": str(paths["audit_gate_registry"]),
        "layer_registry": str(paths["layer_registry"]),
        "forbidden_registry": str(paths["forbidden_registry"]),
        "required_artifacts_present": bool(required_artifacts_present),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": missing_source_artifacts,
        "row_schema_field_count": len(row_schema),
        "metric_registry_row_count": len(metric_registry),
        "audit_gate_count": len(audit_gate_registry),
        "layer_registry_count": len(layer_registry),
        "forbidden_registry_row_count": len(forbidden_registry),
        "required_layers": list(REQUIRED_LAYERS),
        "layer_registry_contains_required_layers": set(REQUIRED_LAYERS).issubset(layer_names),
        "scenario_roles": list(SCENARIO_ROLES),
        "actor_contract": dict(ACTOR_CONTRACT),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "no_hidden_oracle_actor_inputs_encoded": bool(
            ACTOR_CONTRACT["no_hidden_oracle_actor_inputs"]
            and "forbidden_actor_input" in forbidden_categories
        ),
        "forbidden_actor_inputs_encoded": "forbidden_actor_input" in forbidden_categories,
        "forbidden_outcome_shortcuts_encoded": "forbidden_outcome_shortcut" in forbidden_categories,
        "claim_boundary_encoded": "diagnostic_only_no_ranking_claim" in row_fields,
        "ranking_or_winner_fields_emitted": False,
        "success_rate_verdict_field_emitted": False,
        "no_rollout_scope": True,
        "source_only_layer_separated_from_validation": bool(
            "source_only_diagnostic" in layer_names
            and "future_high_fidelity_validation" in layer_names
        ),
        "taxonomy_row_count": len(source["m2510_taxonomy_rows"]),
        **false_flags,
    }


def _false_claim_flags() -> dict[str, bool]:
    return {
        "environment_rollout_run": False,
        "simulator_step_run": False,
        "external_high_fidelity_simulation_included": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "controller_family_verdict_computed": False,
        "driver_performance_claim_made": False,
        "verdict_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize engineering-controller behavior/outcome protocol."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = materialize_behavior_outcome_protocol(
        args.output_dir,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"protocol_version={summary['protocol_version']}")
    print(f"row_schema_field_count={summary['row_schema_field_count']}")
    print(f"metric_registry_row_count={summary['metric_registry_row_count']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
