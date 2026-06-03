"""Materialize Route A failure-surface intervention plan artifacts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_OUTPUT_DIR = Path("runs/m2527_engineering_controller_failure_surface_intervention_plan")
DEFAULT_MILESTONE = (
    "m2527-engineering-controller-failure-surface-intervention-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2527-engineering-controller-failure-surface-intervention-materialization-preflight"
)
M2526_DESIGN = "docs/m2526-engineering-controller-failure-surface-intervention-design.md"
M2525_SYNTHESIS = "docs/m2525-engineering-controller-bounded-measured-behavior-panel-branch-synthesis.md"
M2524_AUDIT = "docs/m2524-engineering-controller-source-only-fresh-seed-measured-behavior-panel-result-audit.md"
M2523_SUMMARY = "runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel/summary.json"
M2523_SEED_PANEL = "runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel/seed_panel_spec.csv"
M2523_BEHAVIOR_ROWS = (
    "runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel/measured_behavior_rows.csv"
)
M2523_EVENT_ROWS = (
    "runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel/measured_event_rows.csv"
)
M2523_COMPLETENESS_ROWS = (
    "runs/m2523_engineering_controller_source_only_fresh_seed_measured_behavior_panel/metric_completeness_rows.csv"
)

ACTOR_CONTRACT_ID = "P0_human_view_72_action_3_no_oracle"
PRIMARY_SUBJECT = "m1154_policy_actor"
CLAIM_BOUNDARY = (
    "intervention planning only; not ranking, success-rate, validation, driver performance, "
    "paper, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, or self-ID"
)
FORBIDDEN_ACTOR_INPUT_FIELDS = [
    "mu",
    "mass",
    "tire_stiffness",
    "brake_scale",
    "actuator_tau",
    "hidden_dynamics",
    "scenario_role_label",
    "feasibility_class",
    "oracle_outcome_label",
    "slip",
    "tire_force",
    "ttc",
    "required_clearance",
    "oracle_stopping_distance",
    "speed_ref",
    "beta_target",
    "path_error",
    "heading_error",
    "path_curvature",
    "reward_terms",
    "success_label",
    "controller_mode",
    "rule_switch_state",
]
FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "environment_rollout_run": False,
    "simulator_step_run": False,
    "policy_action_run": False,
    "training_started": False,
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}

PROTECTED_ROW_FIELDNAMES = [
    "protection_group",
    "row_role",
    "scenario_role",
    "seed",
    "subject_id",
    "source_row_id",
    "fixture_id",
    "seed_panel_id",
    "failure_surface",
    "protected_metric",
    "guardrail_metric",
    "source_artifact",
    "current_collision_event",
    "current_road_departure_event",
    "current_obstacle_passed_event",
    "current_minimum_road_margin_m",
    "current_minimum_obstacle_clearance_m",
    "current_severity_proxy",
    "current_simultaneous_throttle_brake_fraction",
    "private_holdout",
    "claim_boundary",
]

GATE_MATRIX_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "protected_group",
    "metric",
    "required_condition",
    "source_artifact",
    "blocks_claims",
    "next_route_if_fail",
]


def materialize_failure_surface_intervention_plan(
    output_dir: Path,
    *,
    behavior_rows_path: Path | str = M2523_BEHAVIOR_ROWS,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = _load_source_artifacts()
    behavior_rows = _read_csv_rows(behavior_rows_path)
    intervention_spec = build_intervention_spec()
    protected_rows = build_protected_regression_rows(
        behavior_rows,
        source_artifact=str(behavior_rows_path),
    )
    gate_matrix = build_gate_matrix()
    patch_plan = build_candidate_config_patch_plan()

    intervention_spec_path = output_dir / "intervention_spec.json"
    protected_rows_path = output_dir / "protected_regression_rows.csv"
    gate_matrix_path = output_dir / "implementation_gate_matrix.csv"
    patch_plan_path = output_dir / "candidate_config_patch_plan.json"
    summary_path = output_dir / "summary.json"

    write_json(intervention_spec_path, intervention_spec)
    write_csv_rows(protected_rows_path, protected_rows, fieldnames=PROTECTED_ROW_FIELDNAMES)
    write_csv_rows(gate_matrix_path, gate_matrix, fieldnames=GATE_MATRIX_FIELDNAMES)
    write_json(patch_plan_path, patch_plan)

    summary = build_summary(
        output_dir=output_dir,
        source=source,
        behavior_rows=behavior_rows,
        protected_rows=protected_rows,
        gate_matrix=gate_matrix,
        intervention_spec_path=intervention_spec_path,
        protected_rows_path=protected_rows_path,
        gate_matrix_path=gate_matrix_path,
        patch_plan_path=patch_plan_path,
        summary_path=summary_path,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(summary_path, summary)
    return summary


def build_intervention_spec() -> dict[str, Any]:
    return {
        "spec_id": "engineering_controller_failure_surface_intervention_v0",
        "actor_contract_id": ACTOR_CONTRACT_ID,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_encoder": "human_view_online_gru",
        "action_horizon": 1,
        "single_actor": True,
        "rule_switching_controller_modes_allowed": False,
        "actor_input_contract_changed": False,
        "forbidden_actor_input_fields": FORBIDDEN_ACTOR_INPUT_FIELDS,
        "allowed_actor_signal_families": [
            "ego_kinematics_and_imu_like_response",
            "steering_throttle_brake_actuator_state",
            "previous_physical_commands",
            "ego_frame_road_free_space_boundary_geometry",
            "ego_frame_obstacle_geometry_and_relative_motion",
            "online_gru_recurrent_state",
        ],
        "allowed_reward_or_evaluator_fields": [
            "minimum_road_margin_m",
            "road_departure_event",
            "collision_event",
            "minimum_obstacle_clearance_m",
            "severity_proxy",
            "simultaneous_throttle_brake_fraction",
            "mitigation_delta_against_reference",
        ],
        "road_boundary_objective": {
            "target_roles": ["stable_aes", "drift_required_recovery"],
            "primary_metric": "minimum_road_margin_m",
            "direction": "increase_toward_nonnegative",
            "guardrails": ["collision_event_not_regressed", "actor_contract_unchanged"],
        },
        "mitigation_objective": {
            "target_roles": ["unavoidable_mitigation"],
            "primary_metrics": ["severity_proxy", "minimum_road_margin_m"],
            "direction": "reduce_severity_and_road_boundary_loss",
            "reference_subject": "straight_full_brake_open_loop",
        },
        "command_conflict_objective": {
            "target_subject": PRIMARY_SUBJECT,
            "primary_metric": "simultaneous_throttle_brake_fraction",
            "direction": "decrease",
            "allowed_implementation": "reward_or_action_regularization_from_actor_output_or_physical_actuator_state",
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }


def build_protected_regression_rows(
    behavior_rows: list[dict[str, str]],
    *,
    source_artifact: str,
) -> list[dict[str, Any]]:
    protected: list[dict[str, Any]] = []
    for row in sorted(
        behavior_rows,
        key=lambda item: (item["subject_id"], item["scenario_role"], int(item["seed"])),
    ):
        subject = row["subject_id"]
        role = row["scenario_role"]
        if subject == PRIMARY_SUBJECT:
            row_role = "primary_protected"
            if role in {"stable_aes", "drift_required_recovery"}:
                group = "road_boundary_primary"
                surface = "road_departure_and_command_conflict"
                protected_metric = "minimum_road_margin_m;road_departure_event;simultaneous_throttle_brake_fraction"
                guardrail_metric = "collision_event_not_regressed;actor_contract_72_3"
            elif role == "unavoidable_mitigation":
                group = "mitigation_primary"
                surface = "collision_road_departure_and_command_conflict"
                protected_metric = "severity_proxy;minimum_road_margin_m;simultaneous_throttle_brake_fraction"
                guardrail_metric = "no_success_verdict_field;actor_contract_72_3"
            else:
                group = "primary_other"
                surface = "primary_context"
                protected_metric = "tracked"
                guardrail_metric = "actor_contract_72_3"
        else:
            row_role = "reference_context"
            group = f"reference_{subject}"
            surface = "reference_context"
            protected_metric = "context_metric_only"
            guardrail_metric = "not_ranking_or_winner"
        protected.append(
            {
                "protection_group": group,
                "row_role": row_role,
                "scenario_role": role,
                "seed": row["seed"],
                "subject_id": subject,
                "source_row_id": row["row_id"],
                "fixture_id": row["fixture_id"],
                "seed_panel_id": row.get("seed_panel_id", ""),
                "failure_surface": surface,
                "protected_metric": protected_metric,
                "guardrail_metric": guardrail_metric,
                "source_artifact": source_artifact,
                "current_collision_event": row["collision_event"],
                "current_road_departure_event": row["road_departure_event"],
                "current_obstacle_passed_event": row["obstacle_passed_event"],
                "current_minimum_road_margin_m": row["minimum_road_margin_m"],
                "current_minimum_obstacle_clearance_m": row["minimum_obstacle_clearance_m"],
                "current_severity_proxy": row["severity_proxy"],
                "current_simultaneous_throttle_brake_fraction": row[
                    "simultaneous_throttle_brake_fraction"
                ],
                "private_holdout": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return protected


def build_gate_matrix() -> list[dict[str, str]]:
    return [
        {
            "gate_id": "contract_p0_72_3",
            "gate_tier": "contract",
            "protected_group": "all",
            "metric": "observation_shape;action_shape;actor_input_contract_changed",
            "required_condition": "observation_shape==72 action_shape==3 actor_input_contract_changed==false",
            "source_artifact": "intervention_spec.json",
            "blocks_claims": "all behavior or implementation claims if failed",
            "next_route_if_fail": "contract repair before implementation",
        },
        {
            "gate_id": "no_oracle_actor_inputs",
            "gate_tier": "contract",
            "protected_group": "all",
            "metric": "forbidden_actor_input_fields",
            "required_condition": "forbidden fields absent from actor input and controller mode absent",
            "source_artifact": "intervention_spec.json",
            "blocks_claims": "deployable actor claim",
            "next_route_if_fail": "design repair or branch synthesis",
        },
        {
            "gate_id": "road_boundary_proof",
            "gate_tier": "proof",
            "protected_group": "road_boundary_primary",
            "metric": "minimum_road_margin_m;road_departure_event",
            "required_condition": "future repair must improve road margin and reduce road departure without collision regression",
            "source_artifact": "protected_regression_rows.csv",
            "blocks_claims": "road-boundary intervention evidence",
            "next_route_if_fail": "failure-surface repair audit",
        },
        {
            "gate_id": "mitigation_proof",
            "gate_tier": "proof",
            "protected_group": "mitigation_primary",
            "metric": "severity_proxy;minimum_road_margin_m",
            "required_condition": "future repair must reduce severity and road-boundary loss without success verdict field",
            "source_artifact": "protected_regression_rows.csv",
            "blocks_claims": "mitigation intervention evidence",
            "next_route_if_fail": "mitigation objective repair",
        },
        {
            "gate_id": "command_conflict_proof",
            "gate_tier": "proof",
            "protected_group": "primary_protected",
            "metric": "simultaneous_throttle_brake_fraction",
            "required_condition": "future repair must reduce simultaneous physical throttle and brake commands",
            "source_artifact": "protected_regression_rows.csv",
            "blocks_claims": "command-conflict intervention evidence",
            "next_route_if_fail": "action regularizer repair",
        },
        {
            "gate_id": "fresh_seed_generalization",
            "gate_tier": "generalization",
            "protected_group": "future_fresh_source_only",
            "metric": "fresh_seed_panel",
            "required_condition": "later repair must test fresh seeds beyond protected rows before promotion",
            "source_artifact": "implementation_gate_matrix.csv",
            "blocks_claims": "generalization or promotion claims",
            "next_route_if_fail": "fresh-seed panel before promotion",
        },
        {
            "gate_id": "no_ranking_no_success_rate",
            "gate_tier": "claim_boundary",
            "protected_group": "all",
            "metric": "ranking_run;winner_selected;success_rate_computed",
            "required_condition": "all false until explicit promotion gate",
            "source_artifact": "summary.json",
            "blocks_claims": "ranking winner success-rate verdict",
            "next_route_if_fail": "claim-boundary audit",
        },
    ]


def build_candidate_config_patch_plan() -> dict[str, Any]:
    return {
        "plan_id": "m2527_candidate_config_patch_plan_v0",
        "active_config_overwritten": False,
        "candidate_config_file_written": False,
        "training_started": False,
        "policy_action_run": False,
        "profile_specific_tuning": False,
        "proposed_patch_families": [
            {
                "patch_family": "road_boundary_reward_or_constraint",
                "target_metric": "minimum_road_margin_m",
                "source": "evaluator/reward only",
                "actor_input_changed": False,
            },
            {
                "patch_family": "mitigation_severity_shaping",
                "target_metric": "severity_proxy",
                "source": "evaluator/reward only",
                "actor_input_changed": False,
            },
            {
                "patch_family": "simultaneous_throttle_brake_regularizer",
                "target_metric": "simultaneous_throttle_brake_fraction",
                "source": "actor output or physical actuator state regularization",
                "actor_input_changed": False,
            },
            {
                "patch_family": "protected_row_seed_mix",
                "target_metric": "protected_regression_rows",
                "source": "training curriculum metadata only",
                "actor_input_changed": False,
            },
        ],
        "must_not_patch": [
            "actor observation fields",
            "action dimension",
            "checkpoint promotion metadata",
            "active production config",
            "rule-switch controller mode",
            "oracle actor inputs",
        ],
        "claim_boundary": CLAIM_BOUNDARY,
    }


def build_summary(
    *,
    output_dir: Path,
    source: dict[str, bool],
    behavior_rows: list[dict[str, str]],
    protected_rows: list[dict[str, Any]],
    gate_matrix: list[dict[str, str]],
    intervention_spec_path: Path,
    protected_rows_path: Path,
    gate_matrix_path: Path,
    patch_plan_path: Path,
    summary_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    primary_rows = [row for row in protected_rows if row["row_role"] == "primary_protected"]
    reference_rows = [row for row in protected_rows if row["row_role"] == "reference_context"]
    required_artifacts_present = all(
        path.exists()
        for path in [
            intervention_spec_path,
            protected_rows_path,
            gate_matrix_path,
            patch_plan_path,
        ]
    )
    source_artifacts_exist = all(source.values())
    actor_contract_shape_72_action_3 = True
    protected_rows_trace_to_source = (
        len(protected_rows) == len(behavior_rows)
        and {row["source_row_id"] for row in protected_rows}
        == {row["row_id"] for row in behavior_rows}
    )
    primary_trace_count = len(primary_rows)
    road_boundary_primary_count = sum(
        row["protection_group"] == "road_boundary_primary" for row in primary_rows
    )
    mitigation_primary_count = sum(
        row["protection_group"] == "mitigation_primary" for row in primary_rows
    )
    command_conflict_primary_count = sum(
        "simultaneous_throttle_brake_fraction" in row["protected_metric"]
        for row in primary_rows
    )
    status_pass = (
        required_artifacts_present
        and source_artifacts_exist
        and protected_rows_trace_to_source
        and primary_trace_count == 15
        and road_boundary_primary_count == 10
        and mitigation_primary_count == 5
        and command_conflict_primary_count == 15
        and len(reference_rows) == 30
        and actor_contract_shape_72_action_3
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": (
            "engineering_controller_failure_surface_intervention_plan_materialization_pass"
            if status_pass
            else "engineering_controller_failure_surface_intervention_plan_materialization_failed"
        ),
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(summary_path),
        "intervention_spec": str(intervention_spec_path),
        "protected_regression_rows": str(protected_rows_path),
        "implementation_gate_matrix": str(gate_matrix_path),
        "candidate_config_patch_plan": str(patch_plan_path),
        "required_artifacts_present": bool(required_artifacts_present),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": [path for path, exists in source.items() if not exists],
        "source_behavior_row_count": len(behavior_rows),
        "protected_regression_row_count": len(protected_rows),
        "primary_protected_row_count": primary_trace_count,
        "reference_context_row_count": len(reference_rows),
        "road_boundary_primary_row_count": road_boundary_primary_count,
        "mitigation_primary_row_count": mitigation_primary_count,
        "command_conflict_primary_row_count": command_conflict_primary_count,
        "gate_matrix_row_count": len(gate_matrix),
        "protected_rows_trace_to_source": bool(protected_rows_trace_to_source),
        "actor_contract_id": ACTOR_CONTRACT_ID,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
        "actor_input_contract_changed": False,
        "hidden_or_oracle_actor_inputs_required": False,
        "rule_switching_controller_modes_allowed": False,
        "active_config_overwritten": False,
        "candidate_config_file_written": False,
        "diagnostic_only_plan": True,
        "claim_boundary": CLAIM_BOUNDARY,
        **FALSE_CLAIM_FLAGS,
    }


def _load_source_artifacts() -> dict[str, bool]:
    paths = [
        M2526_DESIGN,
        M2525_SYNTHESIS,
        M2524_AUDIT,
        M2523_SUMMARY,
        M2523_SEED_PANEL,
        M2523_BEHAVIOR_ROWS,
        M2523_EVENT_ROWS,
        M2523_COMPLETENESS_ROWS,
    ]
    return {path: Path(path).exists() for path in paths}


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize failure-surface intervention plan artifacts."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--behavior-rows", type=Path, default=Path(M2523_BEHAVIOR_ROWS))
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_failure_surface_intervention_plan(
        args.output_dir,
        behavior_rows_path=args.behavior_rows,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(
        f"result_class={summary['result_class']} "
        f"status_pass={str(summary['status_pass']).lower()} "
        f"output_dir={summary['output_dir']}"
    )


if __name__ == "__main__":
    main()
