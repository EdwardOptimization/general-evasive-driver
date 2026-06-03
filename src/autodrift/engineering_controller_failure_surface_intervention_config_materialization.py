"""Materialize immutable candidate config artifacts for failure-surface repair."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_PLAN_DIR = Path("runs/m2527_engineering_controller_failure_surface_intervention_plan")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2528_engineering_controller_failure_surface_intervention_config_materialization"
)
DEFAULT_MILESTONE = (
    "m2528-engineering-controller-failure-surface-intervention-config-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2529-engineering-controller-failure-surface-intervention-repair-smoke-preflight"
)
ACTOR_CONTRACT_ID = "P0_human_view_72_action_3_no_oracle"
CLAIM_BOUNDARY = (
    "candidate config materialization only; not ranking, success-rate, validation, "
    "driver performance, paper, finite-window-vs-GRU, current-sim verdict, "
    "high-fidelity validation, or self-ID"
)
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

CONFIG_PATCH_AUDIT_FIELDNAMES = [
    "patch_family",
    "target_metric",
    "source",
    "actor_input_changed",
    "allowed_by_intervention_spec",
    "candidate_config_file_written",
    "active_config_overwritten",
    "training_started",
    "policy_action_run",
    "claim_boundary",
]

PROTECTED_GATE_BINDING_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "protected_group",
    "metric",
    "protected_row_count",
    "primary_row_count",
    "reference_row_count",
    "source_gate_artifact",
    "source_rows_artifact",
    "binding_status",
    "claim_boundary",
]


def materialize_failure_surface_candidate_config(
    output_dir: Path,
    *,
    plan_dir: Path | str = DEFAULT_PLAN_DIR,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = Path(plan_dir)
    source = load_plan_artifacts(plan_path)
    candidate_config = build_candidate_config(source)
    patch_audit_rows = build_config_patch_audit_rows(source["patch_plan"])
    gate_bindings = build_protected_gate_bindings(
        source["gate_rows"],
        source["protected_rows"],
    )

    candidate_config_path = output_dir / "candidate_config.json"
    config_patch_audit_path = output_dir / "config_patch_audit.csv"
    protected_gate_bindings_path = output_dir / "protected_gate_bindings.csv"
    summary_path = output_dir / "summary.json"

    write_json(candidate_config_path, candidate_config)
    write_csv_rows(
        config_patch_audit_path,
        patch_audit_rows,
        fieldnames=CONFIG_PATCH_AUDIT_FIELDNAMES,
    )
    write_csv_rows(
        protected_gate_bindings_path,
        gate_bindings,
        fieldnames=PROTECTED_GATE_BINDING_FIELDNAMES,
    )

    summary = build_summary(
        output_dir=output_dir,
        plan_dir=plan_path,
        source=source,
        candidate_config=candidate_config,
        patch_audit_rows=patch_audit_rows,
        gate_bindings=gate_bindings,
        candidate_config_path=candidate_config_path,
        config_patch_audit_path=config_patch_audit_path,
        protected_gate_bindings_path=protected_gate_bindings_path,
        summary_path=summary_path,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(summary_path, summary)
    return summary


def load_plan_artifacts(plan_dir: Path) -> dict[str, Any]:
    return {
        "summary": read_json(plan_dir / "summary.json"),
        "intervention_spec": read_json(plan_dir / "intervention_spec.json"),
        "patch_plan": read_json(plan_dir / "candidate_config_patch_plan.json"),
        "gate_rows": _read_csv_rows(plan_dir / "implementation_gate_matrix.csv"),
        "protected_rows": _read_csv_rows(plan_dir / "protected_regression_rows.csv"),
        "source_exists": {
            str(plan_dir / "summary.json"): (plan_dir / "summary.json").exists(),
            str(plan_dir / "intervention_spec.json"): (plan_dir / "intervention_spec.json").exists(),
            str(plan_dir / "protected_regression_rows.csv"): (
                plan_dir / "protected_regression_rows.csv"
            ).exists(),
            str(plan_dir / "implementation_gate_matrix.csv"): (
                plan_dir / "implementation_gate_matrix.csv"
            ).exists(),
            str(plan_dir / "candidate_config_patch_plan.json"): (
                plan_dir / "candidate_config_patch_plan.json"
            ).exists(),
        },
    }


def build_candidate_config(source: dict[str, Any]) -> dict[str, Any]:
    spec = source["intervention_spec"]
    patch_plan = source["patch_plan"]
    protected_rows = source["protected_rows"]
    gate_rows = source["gate_rows"]
    return {
        "config_id": "m2528_failure_surface_intervention_candidate_v0",
        "immutable_candidate_config": True,
        "active_config_overwritten": False,
        "candidate_config_file_written": True,
        "training_started": False,
        "policy_action_run": False,
        "source_plan_id": patch_plan["plan_id"],
        "actor_contract": {
            "actor_contract_id": ACTOR_CONTRACT_ID,
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "actor_encoder": spec["actor_encoder"],
            "action_horizon": int(spec["action_horizon"]),
            "actor_input_contract_changed": False,
            "single_actor": True,
            "rule_switching_controller_modes_allowed": False,
        },
        "forbidden_actor_input_fields": spec["forbidden_actor_input_fields"],
        "allowed_actor_signal_families": spec["allowed_actor_signal_families"],
        "intervention_objectives": {
            "road_boundary": spec["road_boundary_objective"],
            "mitigation": spec["mitigation_objective"],
            "command_conflict": spec["command_conflict_objective"],
        },
        "candidate_patch_families": patch_plan["proposed_patch_families"],
        "candidate_coefficients": {
            "road_margin_reward_scale": 1.0,
            "road_departure_penalty_scale": 1.0,
            "mitigation_severity_penalty_scale": 0.5,
            "simultaneous_throttle_brake_penalty_scale": 0.25,
            "protected_seed_mix_probability": 0.35,
        },
        "protected_dataset": {
            "protected_row_count": len(protected_rows),
            "primary_protected_row_count": sum(
                row["row_role"] == "primary_protected" for row in protected_rows
            ),
            "reference_context_row_count": sum(
                row["row_role"] == "reference_context" for row in protected_rows
            ),
            "protected_roles": sorted({row["scenario_role"] for row in protected_rows}),
            "source_artifact": "runs/m2527_engineering_controller_failure_surface_intervention_plan/protected_regression_rows.csv",
        },
        "gate_matrix": {
            "gate_count": len(gate_rows),
            "gate_ids": [row["gate_id"] for row in gate_rows],
            "source_artifact": "runs/m2527_engineering_controller_failure_surface_intervention_plan/implementation_gate_matrix.csv",
        },
        "claim_boundary": CLAIM_BOUNDARY,
        "next_allowed_route": "source-only repair smoke preflight after config materialization audit",
    }


def build_config_patch_audit_rows(patch_plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for patch in patch_plan["proposed_patch_families"]:
        rows.append(
            {
                "patch_family": patch["patch_family"],
                "target_metric": patch["target_metric"],
                "source": patch["source"],
                "actor_input_changed": bool(patch["actor_input_changed"]),
                "allowed_by_intervention_spec": True,
                "candidate_config_file_written": True,
                "active_config_overwritten": False,
                "training_started": False,
                "policy_action_run": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_protected_gate_bindings(
    gate_rows: list[dict[str, str]],
    protected_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for gate in gate_rows:
        protected_group = gate["protected_group"]
        if protected_group in {"all", "future_fresh_source_only"}:
            bound_rows = protected_rows
        elif protected_group == "primary_protected":
            bound_rows = [row for row in protected_rows if row["row_role"] == "primary_protected"]
        else:
            bound_rows = [
                row for row in protected_rows if row["protection_group"] == protected_group
            ]
        bindings.append(
            {
                "gate_id": gate["gate_id"],
                "gate_tier": gate["gate_tier"],
                "protected_group": protected_group,
                "metric": gate["metric"],
                "protected_row_count": len(bound_rows),
                "primary_row_count": sum(
                    row["row_role"] == "primary_protected" for row in bound_rows
                ),
                "reference_row_count": sum(
                    row["row_role"] == "reference_context" for row in bound_rows
                ),
                "source_gate_artifact": "runs/m2527_engineering_controller_failure_surface_intervention_plan/implementation_gate_matrix.csv",
                "source_rows_artifact": "runs/m2527_engineering_controller_failure_surface_intervention_plan/protected_regression_rows.csv",
                "binding_status": "bound_to_m2527_plan_rows",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return bindings


def build_summary(
    *,
    output_dir: Path,
    plan_dir: Path,
    source: dict[str, Any],
    candidate_config: dict[str, Any],
    patch_audit_rows: list[dict[str, Any]],
    gate_bindings: list[dict[str, Any]],
    candidate_config_path: Path,
    config_patch_audit_path: Path,
    protected_gate_bindings_path: Path,
    summary_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    required_artifacts_present = (
        candidate_config_path.exists()
        and config_patch_audit_path.exists()
        and protected_gate_bindings_path.exists()
    )
    source_artifacts_exist = all(source["source_exists"].values())
    gate_binding_traceable = (
        len(gate_bindings) == len(source["gate_rows"])
        and {row["gate_id"] for row in gate_bindings}
        == {row["gate_id"] for row in source["gate_rows"]}
        and all(int(row["protected_row_count"]) > 0 for row in gate_bindings)
    )
    protected_rows_traceable = (
        candidate_config["protected_dataset"]["protected_row_count"]
        == len(source["protected_rows"])
        == int(source["summary"]["protected_regression_row_count"])
    )
    actor_contract_shape_72_action_3 = (
        candidate_config["actor_contract"]["observation_shape"] == P0_OBSERVATION_DIM
        and candidate_config["actor_contract"]["action_shape"] == ACTION_DIM
        and candidate_config["actor_contract"]["actor_input_contract_changed"] is False
    )
    no_patch_contract_violation = all(
        row["allowed_by_intervention_spec"] and not row["actor_input_changed"]
        for row in patch_audit_rows
    )
    active_config_overwritten = False
    candidate_config_file_written = candidate_config_path.exists()
    status_pass = (
        required_artifacts_present
        and source_artifacts_exist
        and candidate_config_file_written
        and not active_config_overwritten
        and gate_binding_traceable
        and protected_rows_traceable
        and actor_contract_shape_72_action_3
        and no_patch_contract_violation
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": (
            "engineering_controller_failure_surface_intervention_config_materialization_pass"
            if status_pass
            else "engineering_controller_failure_surface_intervention_config_materialization_failed"
        ),
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "plan_dir": str(plan_dir),
        "summary": str(summary_path),
        "candidate_config": str(candidate_config_path),
        "config_patch_audit": str(config_patch_audit_path),
        "protected_gate_bindings": str(protected_gate_bindings_path),
        "required_artifacts_present": bool(required_artifacts_present),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": [
            path for path, exists in source["source_exists"].items() if not exists
        ],
        "candidate_config_file_written": bool(candidate_config_file_written),
        "active_config_overwritten": bool(active_config_overwritten),
        "immutable_candidate_config": bool(candidate_config["immutable_candidate_config"]),
        "config_patch_audit_row_count": len(patch_audit_rows),
        "protected_gate_binding_row_count": len(gate_bindings),
        "protected_rows_traceable": bool(protected_rows_traceable),
        "gate_binding_traceable": bool(gate_binding_traceable),
        "actor_contract_id": ACTOR_CONTRACT_ID,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "actor_input_contract_changed": False,
        "hidden_or_oracle_actor_inputs_required": False,
        "rule_switching_controller_modes_allowed": False,
        "no_patch_contract_violation": bool(no_patch_contract_violation),
        "claim_boundary": CLAIM_BOUNDARY,
        **FALSE_CLAIM_FLAGS,
    }


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize failure-surface intervention candidate config artifacts."
    )
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_failure_surface_candidate_config(
        args.output_dir,
        plan_dir=args.plan_dir,
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
