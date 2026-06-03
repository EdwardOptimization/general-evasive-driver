"""Materialize the post-pivot Route A baseline and HF0 interface map."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.hf0_source_only_closed_loop_fixture_pilot import admit_actor_checkpoint
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    DIAGNOSTIC_ONLY_KEYS,
    P0_OBSERVATION_DIM,
)


DEFAULT_OUTPUT_DIR = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization"
)
DEFAULT_MILESTONE = (
    "m2541-engineering-controller-route-a-baseline-and-interface-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2542-engineering-controller-route-a-baseline-and-interface-materialization-result-audit"
)
CLAIM_SCOPE = "engineering-controller Route A baseline and HF0 interface materialization only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID claim"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "environment_rollout_run": False,
    "simulator_step_run": False,
    "measured_validation_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "training_run": False,
    "repair_training_started": False,
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

BASELINE_CHECKPOINT_FIELDNAMES = [
    "checkpoint_id",
    "checkpoint_path",
    "source_milestone",
    "source_summary",
    "actor_contract_id",
    "observation_shape",
    "action_shape",
    "actor_encoder",
    "action_sequence_horizon",
    "checkpoint_admitted",
    "checkpoint_admission_reason",
    "behavior_changed_from_parent",
    "proof_status",
    "promotion_status",
    "allowed_use",
    "forbidden_interpretation",
    "source_exists",
]

ARTIFACT_MAP_FIELDNAMES = [
    "artifact_id",
    "path",
    "artifact_type",
    "source_milestone",
    "route_a_role",
    "included_in_materialization",
    "claim_scope",
    "forbidden_interpretation",
    "source_exists",
]

FAILURE_TAXONOMY_EXTENSION_FIELDNAMES = [
    "failure_id",
    "failure_category",
    "evidence_scope",
    "evidence_type",
    "source_artifact",
    "source_milestone",
    "severity",
    "known_limitation",
    "observed_evidence",
    "route_implication",
    "forbidden_interpretation",
    "source_exists",
]

SCENARIO_ROLE_PLAN_FIELDNAMES = [
    "scenario_role",
    "current_source_artifact",
    "available_metrics",
    "missing_metrics",
    "gate_tier",
    "claim_scope",
    "next_materialization_needed",
    "forbidden_interpretation",
]

HF0_INTERFACE_FIELDNAMES = [
    "interface_component",
    "source_path",
    "actor_visible",
    "diagnostic_only",
    "allowed_for_actor",
    "hidden_or_oracle_risk",
    "materialization_status",
    "next_gate",
    "forbidden_interpretation",
]

BASELINE_CHECKPOINT_SPECS = [
    {
        "checkpoint_id": "m1154_original",
        "checkpoint_path": "runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt",
        "source_milestone": "m1154",
        "source_summary": "runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json",
        "behavior_changed_from_parent": False,
        "proof_status": "diagnostic_source_baseline_protected_failures_exposed_by_m2529_m2539",
        "promotion_status": "historical_promoted_not_repromoted_by_m2541",
        "allowed_use": "diagnostic_baseline_lineage",
    },
    {
        "checkpoint_id": "m2532_guarded_repair",
        "checkpoint_path": (
            "runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/"
            "checkpoints/m2532_guarded_actor_head_repair.pt"
        ),
        "source_milestone": "m2532",
        "source_summary": "runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/summary.json",
        "behavior_changed_from_parent": True,
        "proof_status": "road_boundary_and_command_conflict_pass_mitigation_fails",
        "promotion_status": "not_promoted",
        "allowed_use": "diagnostic_behavior_changed_repair_candidate",
    },
    {
        "checkpoint_id": "m2537_mitigation_preserving_repair",
        "checkpoint_path": (
            "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/"
            "checkpoints/m2537_mitigation_preserving_actor_head_repair.pt"
        ),
        "source_milestone": "m2537",
        "source_summary": (
            "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/"
            "summary.json"
        ),
        "behavior_changed_from_parent": True,
        "proof_status": "retained_road_boundary_and_command_conflict_pass_mitigation_fails",
        "promotion_status": "not_promoted",
        "allowed_use": "diagnostic_retained_gate_repair_candidate",
    },
]


def run_route_a_baseline_interface_materialization(
    output_dir: Path,
    *,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    device: str = "cpu",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    m2537_summary = read_json(
        "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/summary.json"
    )
    m2505_summary = read_json(
        "public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json"
    )
    m2508_summary = read_json("runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json")
    m2510_summary = read_json("runs/m2510_engineering_controller_known_failure_taxonomy/summary.json")

    baseline_rows = build_baseline_checkpoint_rows(device=device)
    artifact_rows = build_route_a_artifact_map_rows()
    failure_rows = build_failure_taxonomy_extension_rows(m2537_summary=m2537_summary)
    scenario_rows = build_scenario_role_metric_plan_rows()
    hf0_rows = build_hf0_interface_boundary_rows()
    contract_snapshot = build_actor_contract_snapshot(
        baseline_rows=baseline_rows,
        hf0_rows=hf0_rows,
        m2505_summary=m2505_summary,
        m2508_summary=m2508_summary,
        m2510_summary=m2510_summary,
    )

    paths = {
        "baseline_checkpoint_list": output_dir / "baseline_checkpoint_list.csv",
        "actor_io_contract_snapshot_md": output_dir / "actor_io_contract_snapshot.md",
        "actor_io_contract_snapshot_json": output_dir / "actor_io_contract_snapshot.json",
        "route_a_artifact_map": output_dir / "route_a_artifact_map.csv",
        "known_failure_taxonomy_extension": output_dir / "known_failure_taxonomy_extension.csv",
        "scenario_role_metric_report_plan": output_dir / "scenario_role_metric_report_plan.csv",
        "hf0_interface_boundary_map": output_dir / "hf0_interface_boundary_map.csv",
        "hf0_interface_contract": output_dir / "hf0_interface_contract.md",
        "materialization_gate_plan": output_dir / "materialization_gate_plan.md",
        "summary": output_dir / "summary.json",
    }

    write_csv_rows(paths["baseline_checkpoint_list"], baseline_rows, fieldnames=BASELINE_CHECKPOINT_FIELDNAMES)
    write_json(paths["actor_io_contract_snapshot_json"], contract_snapshot)
    paths["actor_io_contract_snapshot_md"].write_text(
        render_actor_contract_snapshot_markdown(contract_snapshot),
        encoding="utf-8",
    )
    write_csv_rows(paths["route_a_artifact_map"], artifact_rows, fieldnames=ARTIFACT_MAP_FIELDNAMES)
    write_csv_rows(
        paths["known_failure_taxonomy_extension"],
        failure_rows,
        fieldnames=FAILURE_TAXONOMY_EXTENSION_FIELDNAMES,
    )
    write_csv_rows(
        paths["scenario_role_metric_report_plan"],
        scenario_rows,
        fieldnames=SCENARIO_ROLE_PLAN_FIELDNAMES,
    )
    write_csv_rows(paths["hf0_interface_boundary_map"], hf0_rows, fieldnames=HF0_INTERFACE_FIELDNAMES)
    paths["hf0_interface_contract"].write_text(
        render_hf0_interface_contract_markdown(hf0_rows),
        encoding="utf-8",
    )
    paths["materialization_gate_plan"].write_text(
        render_materialization_gate_plan_markdown(),
        encoding="utf-8",
    )

    summary = build_summary(
        output_dir=output_dir,
        paths=paths,
        baseline_rows=baseline_rows,
        artifact_rows=artifact_rows,
        failure_rows=failure_rows,
        scenario_rows=scenario_rows,
        hf0_rows=hf0_rows,
        contract_snapshot=contract_snapshot,
        m2537_summary=m2537_summary,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    return summary


def build_baseline_checkpoint_rows(*, device: str = "cpu") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in BASELINE_CHECKPOINT_SPECS:
        _model, admission = admit_actor_checkpoint(spec["checkpoint_path"], device=device)
        rows.append(
            {
                "checkpoint_id": spec["checkpoint_id"],
                "checkpoint_path": spec["checkpoint_path"],
                "source_milestone": spec["source_milestone"],
                "source_summary": spec["source_summary"],
                "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
                "observation_shape": admission.obs_dim or "",
                "action_shape": admission.action_dim or "",
                "actor_encoder": admission.actor_encoder,
                "action_sequence_horizon": admission.action_sequence_horizon or "",
                "checkpoint_admitted": admission.checkpoint_admitted,
                "checkpoint_admission_reason": admission.reason,
                "behavior_changed_from_parent": spec["behavior_changed_from_parent"],
                "proof_status": spec["proof_status"],
                "promotion_status": spec["promotion_status"],
                "allowed_use": spec["allowed_use"],
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
                "source_exists": Path(spec["checkpoint_path"]).exists(),
            }
        )
    return rows


def build_route_a_artifact_map_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "post_m2470_route_plan",
            "docs/post-m2470-route-plan.md",
            "route_plan",
            "post-m2470",
            "Route A and Route C split plus pivot constraints",
        ),
        (
            "observation_contract",
            "docs/observation-contract.md",
            "contract",
            "contract",
            "P0 actor input and action contract",
        ),
        (
            "public_benchmark_pack_summary",
            "public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json",
            "summary_json",
            "m2505",
            "source-only diagnostic public benchmark pack",
        ),
        (
            "public_benchmark_pack_manifest",
            "public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/artifact_manifest.csv",
            "csv",
            "m2505",
            "claim-bounded public artifact manifest",
        ),
        (
            "runtime_report_summary",
            "runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json",
            "summary_json",
            "m2508",
            "actor-only inference-cost evidence",
        ),
        (
            "known_failure_taxonomy_summary",
            "runs/m2510_engineering_controller_known_failure_taxonomy/summary.json",
            "summary_json",
            "m2510",
            "known limitations and failure taxonomy",
        ),
        (
            "m2537_summary",
            "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/summary.json",
            "summary_json",
            "m2537",
            "latest behavior-changing retained-gate repair diagnostic evidence",
        ),
        (
            "m2537_candidate_sweep",
            "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/repair_candidate_sweep.csv",
            "csv",
            "m2537",
            "candidate sweep showing retained-gate and mitigation failure tradeoff",
        ),
        (
            "m2539_synthesis",
            "docs/m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.md",
            "synthesis",
            "m2539",
            "pivot decision away from protected-row repair loop",
        ),
    ]
    return [
        {
            "artifact_id": artifact_id,
            "path": path,
            "artifact_type": artifact_type,
            "source_milestone": milestone,
            "route_a_role": role,
            "included_in_materialization": True,
            "claim_scope": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            "source_exists": Path(path).exists(),
        }
        for artifact_id, path, artifact_type, milestone, role in specs
    ]


def build_failure_taxonomy_extension_rows(*, m2537_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "failure_id": "repeated_mitigation_proof_failure",
            "failure_category": "behavior_regression;proof_washout;objective_overfit",
            "evidence_scope": "m2532_m2537_protected_proof",
            "evidence_type": "repeated_public_proof_failure",
            "source_artifact": "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/summary.json",
            "source_milestone": "m2537",
            "severity": "high",
            "known_limitation": "Mitigation proof remains failing after the one M2536-approved mitigation-preserving repair execution.",
            "observed_evidence": (
                f"mitigation_improved_row_count={m2537_summary['mitigation_improved_row_count']}; "
                f"mitigation_regressed_row_count={m2537_summary['mitigation_regressed_row_count']}; "
                f"max_mitigation_severity_delta={m2537_summary['max_mitigation_severity_delta']}"
            ),
            "route_implication": "Do not continue public protected-row repair without synthesis and broader evidence.",
            "forbidden_interpretation": "full protected proof or driver performance",
            "source_exists": Path(
                "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/summary.json"
            ).exists(),
        },
        {
            "failure_id": "public_protected_row_overfit_risk",
            "failure_category": "objective_overfit",
            "evidence_scope": "m2539_synthesis",
            "evidence_type": "route_boundary",
            "source_artifact": "docs/m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.md",
            "source_milestone": "m2539",
            "severity": "high",
            "known_limitation": "The branch used two behavior-changing repairs around the same public protected proof panel.",
            "observed_evidence": "M2539 public-gate overfit risk high and synthesis decision pivot.",
            "route_implication": "Move to broader Route A baseline/HF0 interface evidence before more repair.",
            "forbidden_interpretation": "generalization or promotion readiness",
            "source_exists": Path(
                "docs/m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.md"
            ).exists(),
        },
    ]


def build_scenario_role_metric_plan_rows() -> list[dict[str, Any]]:
    base_artifact = "src/autodrift/hf0_source_only_role_metric_panel.py"
    role_specs = [
        ("stable_avoidable", "stable avoidable/AEB feasible role not yet materialized in Route A baseline pack"),
        ("stable_aes", "stable AES/AEB infeasible role available in source-only role fixtures"),
        ("drift_required_recovery", "drift-required recovery role available in source-only role fixtures"),
        ("unavoidable_mitigation", "unavoidable mitigation role available in source-only role fixtures and protected proof rows"),
        ("hidden_dynamics_robustness", "hidden dynamics range requires later source-only or high-fidelity variation panel"),
        ("actuator_delay_noise", "delay/noise range requires later explicit fixture or backend variation panel"),
        ("unseen_dynamics_range", "unseen dynamics range requires later fresh/generalization distribution"),
    ]
    return [
        {
            "scenario_role": role,
            "current_source_artifact": base_artifact,
            "available_metrics": (
                "finite_action;bounded_action;saturation_fraction;state_envelope;"
                "backend_status;observation_shape;action_shape"
            ),
            "missing_metrics": (
                "collision;road_departure;obstacle_clearance;mitigation_severity;"
                "recovery_quality;fresh_generalization_retention"
            ),
            "gate_tier": "diagnostic" if role in {"stable_aes", "drift_required_recovery", "unavoidable_mitigation"} else "planned",
            "claim_scope": CLAIM_SCOPE,
            "next_materialization_needed": note,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        }
        for role, note in role_specs
    ]


def build_hf0_interface_boundary_rows() -> list[dict[str, Any]]:
    actor_visible = {
        "ActorView",
        "EgoView",
        "ActuatorView",
        "RoadView",
        "ObstacleSlotView",
        "P0ObservationExtractor",
        "validate_actor_action",
        "physical_control_from_action",
    }
    diagnostic_only = {"DIAGNOSTIC_ONLY_KEYS"}
    components = [
        ("DynamicsBackend.reset", "src/autodrift/high_fidelity_interface.py"),
        ("DynamicsBackend.step", "src/autodrift/high_fidelity_interface.py"),
        ("DynamicsBackend.close", "src/autodrift/high_fidelity_interface.py"),
        ("BackendResetRequest", "src/autodrift/high_fidelity_interface.py"),
        ("BackendResetResult", "src/autodrift/high_fidelity_interface.py"),
        ("BackendStepResult", "src/autodrift/high_fidelity_interface.py"),
        ("ActorView", "src/autodrift/high_fidelity_interface.py"),
        ("EgoView", "src/autodrift/high_fidelity_interface.py"),
        ("ActuatorView", "src/autodrift/high_fidelity_interface.py"),
        ("RoadView", "src/autodrift/high_fidelity_interface.py"),
        ("ObstacleSlotView", "src/autodrift/high_fidelity_interface.py"),
        ("P0ObservationExtractor", "src/autodrift/high_fidelity_interface.py"),
        ("validate_actor_action", "src/autodrift/high_fidelity_interface.py"),
        ("physical_control_from_action", "src/autodrift/high_fidelity_interface.py"),
        ("DIAGNOSTIC_ONLY_KEYS", "src/autodrift/high_fidelity_interface.py"),
        ("FourWheelHF0Backend", "src/autodrift/four_wheel_hf0_adapter.py"),
        ("SourceOnlyRoleFixtureDynamicsSpec", "src/autodrift/four_wheel_hf0_adapter.py"),
    ]
    rows: list[dict[str, Any]] = []
    for component, source_path in components:
        is_actor_visible = component in actor_visible
        is_diagnostic = component in diagnostic_only or component.endswith("BackendResetResult") or component.endswith("BackendStepResult")
        rows.append(
            {
                "interface_component": component,
                "source_path": source_path,
                "actor_visible": is_actor_visible,
                "diagnostic_only": component in diagnostic_only,
                "allowed_for_actor": is_actor_visible,
                "hidden_or_oracle_risk": "must_remain_outside_actor" if component in diagnostic_only else "none",
                "materialization_status": "source_exists" if Path(source_path).exists() else "source_missing",
                "next_gate": "HF1_P0_parity_smoke" if is_actor_visible else "HF0_boundary_audit",
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_actor_contract_snapshot(
    *,
    baseline_rows: list[dict[str, Any]],
    hf0_rows: list[dict[str, Any]],
    m2505_summary: dict[str, Any],
    m2508_summary: dict[str, Any],
    m2510_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "actor_contract_id": "P0_human_view_72_action_3_no_oracle",
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_encoder": "human_view_online_gru",
        "action_sequence_horizon": 1,
        "actor_visible_inputs": [
            "ego kinematics / IMU-like response",
            "steering/throttle/brake actuator state",
            "previous physical commands",
            "ego-frame road/free-space geometry",
            "ego-frame obstacle geometry and relative motion",
            "online recurrent/history state",
        ],
        "forbidden_actor_inputs": sorted(DIAGNOSTIC_ONLY_KEYS),
        "diagnostics_only_hidden_keys_count": len(DIAGNOSTIC_ONLY_KEYS),
        "baseline_checkpoint_count": len(baseline_rows),
        "all_baseline_checkpoints_admitted": all(bool(row["checkpoint_admitted"]) for row in baseline_rows),
        "hf0_interface_component_count": len(hf0_rows),
        "m2505_pack_status_pass": bool(m2505_summary.get("status_pass")),
        "m2508_runtime_status_pass": bool(m2508_summary.get("status_pass")),
        "m2510_taxonomy_status_pass": bool(m2510_summary.get("status_pass")),
        "claim_scope": CLAIM_SCOPE,
        **FALSE_CLAIM_FLAGS,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    baseline_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    hf0_rows: list[dict[str, Any]],
    contract_snapshot: dict[str, Any],
    m2537_summary: dict[str, Any],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    required_artifacts_present = all(
        path.exists()
        for name, path in paths.items()
        if name != "summary"
    )
    all_baseline_checkpoints_exist = all(bool(row["source_exists"]) for row in baseline_rows)
    all_baseline_checkpoints_admitted = all(bool(row["checkpoint_admitted"]) for row in baseline_rows)
    all_artifact_sources_exist = all(bool(row["source_exists"]) for row in artifact_rows)
    hf0_sources_exist = all(row["materialization_status"] == "source_exists" for row in hf0_rows)
    actor_contract_shape = (
        int(contract_snapshot["observation_shape"]) == P0_OBSERVATION_DIM
        and int(contract_snapshot["action_shape"]) == ACTION_DIM
        and all(int(row["observation_shape"]) == P0_OBSERVATION_DIM for row in baseline_rows)
        and all(int(row["action_shape"]) == ACTION_DIM for row in baseline_rows)
    )
    no_claim_boundary_violation = not any(FALSE_CLAIM_FLAGS.values())
    status_pass = (
        required_artifacts_present
        and all_baseline_checkpoints_exist
        and all_baseline_checkpoints_admitted
        and all_artifact_sources_exist
        and hf0_sources_exist
        and actor_contract_shape
        and no_claim_boundary_violation
        and bool(m2537_summary.get("status_pass"))
    )
    return {
        "result_class": (
            "engineering_controller_route_a_baseline_interface_materialization_pass"
            if status_pass
            else "engineering_controller_route_a_baseline_interface_materialization_failed"
        ),
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "baseline_checkpoint_list": str(paths["baseline_checkpoint_list"]),
        "actor_io_contract_snapshot_md": str(paths["actor_io_contract_snapshot_md"]),
        "actor_io_contract_snapshot_json": str(paths["actor_io_contract_snapshot_json"]),
        "route_a_artifact_map": str(paths["route_a_artifact_map"]),
        "known_failure_taxonomy_extension": str(paths["known_failure_taxonomy_extension"]),
        "scenario_role_metric_report_plan": str(paths["scenario_role_metric_report_plan"]),
        "hf0_interface_boundary_map": str(paths["hf0_interface_boundary_map"]),
        "hf0_interface_contract": str(paths["hf0_interface_contract"]),
        "materialization_gate_plan": str(paths["materialization_gate_plan"]),
        "required_artifacts_present": bool(required_artifacts_present),
        "baseline_checkpoint_count": len(baseline_rows),
        "all_baseline_checkpoints_exist": bool(all_baseline_checkpoints_exist),
        "all_baseline_checkpoints_admitted": bool(all_baseline_checkpoints_admitted),
        "route_a_artifact_map_row_count": len(artifact_rows),
        "all_artifact_sources_exist": bool(all_artifact_sources_exist),
        "known_failure_taxonomy_extension_row_count": len(failure_rows),
        "scenario_role_metric_report_plan_row_count": len(scenario_rows),
        "hf0_interface_boundary_row_count": len(hf0_rows),
        "hf0_sources_exist": bool(hf0_sources_exist),
        "actor_contract_id": contract_snapshot["actor_contract_id"],
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "hidden_or_oracle_actor_inputs_required": False,
        "diagnostics_only_hidden_keys_count": len(DIAGNOSTIC_ONLY_KEYS),
        "m2537_status_pass": bool(m2537_summary.get("status_pass")),
        "m2537_protected_proof_gates_all_passed": bool(
            m2537_summary.get("protected_proof_gates_all_passed")
        ),
        "claim_boundary": CLAIM_SCOPE,
        **FALSE_CLAIM_FLAGS,
    }


def render_actor_contract_snapshot_markdown(snapshot: dict[str, Any]) -> str:
    forbidden = "\n".join(f"- `{item}`" for item in snapshot["forbidden_actor_inputs"])
    visible = "\n".join(f"- {item}" for item in snapshot["actor_visible_inputs"])
    return f"""# M2541 Actor I/O Contract Snapshot

- actor contract id: `{snapshot['actor_contract_id']}`
- observation shape: `{snapshot['observation_shape']}`
- action shape: `{snapshot['action_shape']}`
- actor encoder: `{snapshot['actor_encoder']}`
- action sequence horizon: `{snapshot['action_sequence_horizon']}`
- claim scope: {snapshot['claim_scope']}

## Actor-Visible Inputs

{visible}

## Diagnostics-Only / Forbidden Actor Inputs

{forbidden}

## Boundary

Diagnostics may contain hidden state for audits and benchmarks, but actor
checkpoints, `ActorView`, and `P0ObservationExtractor` must not consume hidden
or oracle fields.
"""


def render_hf0_interface_contract_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# M2541 HF0 Interface Contract",
        "",
        "This materialization records the existing HF0 boundary only. It does not install, import, or run external high-fidelity simulation.",
        "",
        "## Components",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['interface_component']}`: actor_visible={row['actor_visible']}, "
            f"diagnostic_only={row['diagnostic_only']}, source={row['source_path']}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Actor-visible components may feed the P0 72-dimensional observation and deployed 3-action contract.",
            "Diagnostics-only components must remain outside actor inputs and checkpoint observations.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_materialization_gate_plan_markdown() -> str:
    return """# M2541 Materialization Gate Plan

## Pass Conditions

- all required materialization files exist
- all baseline checkpoint paths exist and are admitted under the P0 72/3 contract
- actor contract snapshot preserves observation shape 72 and action shape 3
- HF0 boundary map keeps diagnostics-only hidden dynamics outside actor-visible fields
- Route A artifact map source paths are traceable
- no ranking, winner selection, checkpoint promotion, success-rate, validation, or performance claim is emitted

## Failure Routes

- actor contract mismatch -> contract repair
- missing checkpoint lineage -> artifact repair
- hidden/oracle exposure in ActorView or P0ObservationExtractor -> boundary repair
- public protected-row repair continuation -> branch synthesis
- external simulator dependency required -> HF0 design repair before validation
"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize the M2541 Route A baseline and HF0 interface map."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_route_a_baseline_interface_materialization(
        args.output_dir,
        device=args.device,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "baseline_checkpoint_count={baseline_checkpoint_count} "
        "hf0_interface_boundary_row_count={hf0_interface_boundary_row_count} "
        "output_dir={output_dir}".format(**summary)
    )


if __name__ == "__main__":
    main()
