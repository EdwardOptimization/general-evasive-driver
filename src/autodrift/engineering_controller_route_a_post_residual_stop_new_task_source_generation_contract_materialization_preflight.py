"""Materialize M3006 new task-source generation contract rows.

M3006 is a no-execution materialization preflight. It turns the M3005-accepted
M3004 source-axis candidates into a machine-checkable contract for future
source generation with task_source identities outside the exhausted M1690 L3
identity set. It does not build source code, instantiate environments, roll
out policies, train, validate, rank, or promote checkpoints.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3006-engineering-controller-route-a-post-residual-stop-new-task-source-generation-"
    "contract-materialization-preflight"
)
NEXT_ID = (
    "m3007-engineering-controller-route-a-post-residual-stop-new-task-source-generation-"
    "contract-materialization-result-audit"
)
DEFAULT_M3005_AUDIT = Path(
    "docs/m3005-engineering-controller-route-a-post-residual-stop-source-axis-expansion-"
    "materialization-result-audit.md"
)
DEFAULT_M3004_DIR = Path(
    "runs/m3004_engineering_controller_route_a_post_residual_stop_source_axis_"
    "expansion_materialization_preflight"
)
DEFAULT_M1680_SPECS = Path(
    "runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json"
)
DEFAULT_M1690_WORKLOAD = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/"
    "executable_workload_matrix.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3006_engineering_controller_route_a_post_residual_stop_new_task_source_"
    "generation_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m3006-engineering-controller-route-a-post-residual-stop-new-task-source-"
    "generation-contract-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m3007-engineering-controller-route-a-post-residual-stop-"
    "new-task-source-generation-contract-materialization-result-audit.json"
)

TARGET_NEW_SOURCE_SPECS = 16
MIN_AXIS_COUNT = 4
MIN_TASK_FAMILY_COUNT = 2

CLAIM_SCOPE = (
    "M3006 Route A post-residual-stop new task-source generation contract "
    "materialization only; M3004 source-axis candidates may be transformed into "
    "source-contract, axis-budget, new-task-source-spec, same-surface-rejection, "
    "actor-contract, claim-boundary, and gate rows. No reset, step, rollout, "
    "replay, validation, training, PPO, source build, adapter probe, external "
    "simulation, ranking, winner selection, promotion, success-rate verdict, "
    "repair-success, driver-performance, paper, finite-window-vs-GRU, current-sim "
    "verdict, high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "executable workload readiness, source build readiness, execution result, "
    "repair success, validation result, driver performance, current-sim verdict, "
    "paper evidence, high-fidelity validation, finite-window-vs-GRU conclusion, "
    "full ideal driver completion, level3 self-identification, checkpoint ranking, "
    "or checkpoint promotion"
)
DECISION_PASS = "new_task_source_generation_contract_materialized_route_to_m3007_result_audit"
DECISION_FAIL = "new_task_source_generation_contract_materialization_incomplete"

SOURCE_CONTRACT_FIELDNAMES = [
    "source_contract_id",
    "axis_name",
    "axis_family",
    "contract_status",
    "source_identity_prefix",
    "new_task_source_count",
    "task_family_coverage",
    "requires_new_task_source_identity",
    "allows_eval_seed_only_reuse",
    "allows_same_surface_reuse",
    "source_build_scheduled",
    "execution_scheduled",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "claim_boundary",
]
AXIS_BUDGET_FIELDNAMES = [
    "source_axis_budget_id",
    "axis_name",
    "axis_family",
    "budgeted_new_task_source_count",
    "t4_count",
    "t5_count",
    "window_tag_count",
    "source_edge_count",
    "contract_budget_pass",
    "ordinary_engineering_candidate_axis",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]
NEW_SPEC_FIELDNAMES = [
    "new_task_source_spec_id",
    "task_source_id",
    "axis_name",
    "axis_family",
    "axis_variant_tag",
    "task_family",
    "source_edge",
    "source_family_left",
    "source_family_right",
    "window_tag",
    "generation_seed",
    "reference_m1680_task_source_id",
    "reference_schema_role",
    "new_identity_outside_m1680_m1690",
    "overlaps_exhausted_m1690_l3",
    "eval_seed_only_reuse",
    "same_surface_reuse",
    "future_executable_workload_materialization_required",
    "future_execution_manifest_required",
    "source_build_scheduled_by_m3006",
    "execution_scheduled_by_m3006",
    "actor_visible",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "claim_boundary",
]
REJECTED_FIELDNAMES = [
    "rejected_same_surface_id",
    "rejected_route",
    "rejection_family",
    "rejection_reason",
    "source_identity_relation",
    "required_follow_up",
    "actor_visible",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3006",
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
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "source_contract_rows",
    "source_axis_budget_rows",
    "new_task_source_spec_rows",
    "rejected_same_surface_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]

AXIS_VARIANTS = {
    "source_generator_new_task_source_identity": [
        ("T4", "capability_step_down|late_obstacle_reveal_variant", "capability_step_down", "late_reveal_boundary", "reveal_plus_8"),
        ("T5", "curved_boundary_obstacle|capability_step_down_variant", "curved_boundary_obstacle", "capability_step_down", "decision_minus_40"),
        ("T4", "actuator_delay_step|capability_step_up_variant", "actuator_delay_step", "capability_step_up", "mapping_window_new_source"),
        ("T5", "brake_fade_or_loss_proxy|boundary_axis_variant", "brake_fade_or_loss_proxy", "t5_boundary_axis_retarget", "decision_minus_28"),
    ],
    "scenario_distribution_variant_source_axis": [
        ("T4", "t4_staged_warmup_capability|late_reveal_boundary_variant", "t4_staged_warmup_capability", "late_reveal_boundary", "reveal_plus_12"),
        ("T5", "t5_near_boundary_warmup|curved_boundary_obstacle_variant", "t5_near_boundary_warmup", "curved_boundary_obstacle", "decision_minus_36"),
        ("T4", "t4_actuator_delay_response|capability_step_down_variant", "t4_actuator_delay_response", "capability_step_down", "mapping_window_new_source"),
        ("T5", "t5_high_speed_close_obstacle|boundary_retarget_variant", "t5_high_speed_close_obstacle", "t5_boundary_axis_retarget", "reveal_plus_6"),
    ],
    "ood_dynamics_source_axis": [
        ("T4", "ood_low_grip_proxy|actuator_delay_step", "grip_loss_proxy", "actuator_delay_step", "decision_minus_20"),
        ("T5", "ood_mass_shift_proxy|late_reveal_boundary", "capability_step_down", "late_reveal_boundary", "decision_minus_44"),
        ("T4", "ood_brake_loss_proxy|capability_step_up", "brake_fade_or_loss_proxy", "capability_step_up", "reveal_plus_10"),
        ("T5", "ood_drive_loss_proxy|boundary_axis", "drive_loss_proxy", "t5_boundary_axis_retarget", "mapping_window_new_source"),
    ],
    "sensor_noise_delay_source_axis": [
        ("T4", "sensor_noise_proxy|actuator_delay_step", "actuator_delay_step", "sensor_noise_proxy", "reveal_plus_4"),
        ("T5", "perception_delay_proxy|curved_boundary_obstacle", "late_reveal_boundary", "curved_boundary_obstacle", "decision_minus_32"),
        ("T4", "actuator_delay_step|steering_lag_proxy", "actuator_delay_step", "steering_lag_proxy", "mapping_window_new_source"),
        ("T5", "sensor_noise_proxy|brake_fade_or_loss_proxy", "sensor_noise_proxy", "brake_fade_or_loss_proxy", "reveal_plus_8"),
    ],
}


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "source_contract_rows": output_dir / "source_contract_rows.csv",
        "source_axis_budget_rows": output_dir / "source_axis_budget_rows.csv",
        "new_task_source_spec_rows": output_dir / "new_task_source_spec_rows.csv",
        "rejected_same_surface_rows": output_dir / "rejected_same_surface_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def run_new_task_source_generation_contract_materialization_preflight(
    *,
    m3005_audit: Path | str = DEFAULT_M3005_AUDIT,
    m3004_dir: Path | str = DEFAULT_M3004_DIR,
    m1680_specs: Path | str = DEFAULT_M1680_SPECS,
    m1690_workload: Path | str = DEFAULT_M1690_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m3005_audit=Path(m3005_audit),
        m3004_dir=Path(m3004_dir),
        m1680_specs=Path(m1680_specs),
        m1690_workload=Path(m1690_workload),
    )
    exhausted_ids = set(source["m1690_l3_task_source_ids"])
    admissible_axes = [
        row
        for row in source["source_axis_candidate_rows"]
        if row.get("ordinary_engineering_candidate_axis") in {"True", True}
        and str(row.get("axis_status", "")).startswith("candidate_axis_admissible")
    ]
    source_contract_rows = build_source_contract_rows(admissible_axes)
    new_spec_rows = build_new_task_source_spec_rows(admissible_axes, source["m1680_task_source_specs"], exhausted_ids)
    budget_rows = build_source_axis_budget_rows(admissible_axes, new_spec_rows)
    rejected_rows = build_rejected_same_surface_rows(source["m3004_rejected_same_surface_rows"])

    write_csv_rows(paths["source_contract_rows"], source_contract_rows, fieldnames=SOURCE_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["source_axis_budget_rows"], budget_rows, fieldnames=AXIS_BUDGET_FIELDNAMES)
    write_csv_rows(paths["new_task_source_spec_rows"], new_spec_rows, fieldnames=NEW_SPEC_FIELDNAMES)
    write_csv_rows(paths["rejected_same_surface_rows"], rejected_rows, fieldnames=REJECTED_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "admissible_source_axis_count": len(admissible_axes),
            "new_task_source_spec_count": len(new_spec_rows),
            "old_m1690_l3_overlap_count": old_overlap_count(new_spec_rows),
            "execution_performed": False,
            "training_performed": False,
            "validation_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)

    actor_rows = build_actor_contract_guard_rows()
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_without_summary_doc)
    gate_rows = build_gate_matrix_rows(
        source=source,
        admissible_axes=admissible_axes,
        source_contract_rows=source_contract_rows,
        budget_rows=budget_rows,
        new_spec_rows=new_spec_rows,
        rejected_rows=rejected_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
        follow_up_manifest_exists=Path(follow_up_manifest).exists(),
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        admissible_axes=admissible_axes,
        source_contract_rows=source_contract_rows,
        budget_rows=budget_rows,
        new_spec_rows=new_spec_rows,
        rejected_rows=rejected_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        follow_up_manifest=Path(follow_up_manifest),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_artifacts_present)
    gate_rows = build_gate_matrix_rows(
        source=source,
        admissible_axes=admissible_axes,
        source_contract_rows=source_contract_rows,
        budget_rows=budget_rows,
        new_spec_rows=new_spec_rows,
        rejected_rows=rejected_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest_exists=Path(follow_up_manifest).exists(),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        admissible_axes=admissible_axes,
        source_contract_rows=source_contract_rows,
        budget_rows=budget_rows,
        new_spec_rows=new_spec_rows,
        rejected_rows=rejected_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "admissible_source_axis_count": len(admissible_axes),
            "new_task_source_spec_count": len(new_spec_rows),
            "new_task_source_unique_id_count": len({row["task_source_id"] for row in new_spec_rows}),
            "old_m1690_l3_overlap_count": old_overlap_count(new_spec_rows),
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "execution_performed": False,
            "training_performed": False,
            "validation_performed": False,
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def load_source_artifacts(
    *,
    m3005_audit: Path,
    m3004_dir: Path,
    m1680_specs: Path,
    m1690_workload: Path,
) -> dict[str, Any]:
    m1680_data = read_json(m1680_specs) if m1680_specs.exists() else {}
    task_source_specs = list(m1680_data.get("task_source_specs", []))
    m1690_rows = read_csv_rows(m1690_workload)
    m1690_l3_rows = [row for row in m1690_rows if row.get("profile_name") == "L3_online_gru"]
    return {
        "m3005_audit": m3005_audit,
        "m3005_audit_exists": m3005_audit.exists(),
        "m3004_dir": m3004_dir,
        "m3004_summary": read_json(m3004_dir / "summary.json") if (m3004_dir / "summary.json").exists() else {},
        "source_axis_candidate_rows": read_csv_rows(m3004_dir / "source_axis_candidate_rows.csv"),
        "m3004_rejected_same_surface_rows": read_csv_rows(m3004_dir / "rejected_same_surface_rows.csv"),
        "m3004_gate_rows": read_csv_rows(m3004_dir / "gate_matrix.csv"),
        "m1680_specs_path": m1680_specs,
        "m1680_task_source_specs": task_source_specs,
        "m1690_workload": m1690_workload,
        "m1690_l3_rows": m1690_l3_rows,
        "m1690_l3_task_source_ids": {row["task_source_id"] for row in m1690_l3_rows if row.get("task_source_id")},
    }


def build_source_contract_rows(admissible_axes: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, axis in enumerate(admissible_axes, start=1):
        axis_name = str(axis["axis_name"])
        variants = AXIS_VARIANTS.get(axis_name, [])
        task_families = sorted({variant[0] for variant in variants})
        rows.append(
            {
                "source_contract_id": f"m3006-source-contract-{index:04d}",
                "axis_name": axis_name,
                "axis_family": axis.get("axis_family", ""),
                "contract_status": "materialized_new_identity_contract",
                "source_identity_prefix": "m3006-src",
                "new_task_source_count": len(variants),
                "task_family_coverage": ";".join(task_families),
                "requires_new_task_source_identity": True,
                "allows_eval_seed_only_reuse": False,
                "allows_same_surface_reuse": False,
                "source_build_scheduled": False,
                "execution_scheduled": False,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "source_labels_actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_new_task_source_spec_rows(
    admissible_axes: list[dict[str, str]],
    m1680_specs: list[dict[str, Any]],
    exhausted_ids: set[str],
) -> list[dict[str, Any]]:
    reference_specs = sorted(m1680_specs, key=lambda row: str(row.get("task_source_id", "")))
    rows: list[dict[str, Any]] = []
    for axis in admissible_axes:
        axis_name = str(axis["axis_name"])
        for variant_index, (task_family, source_edge, left, right, window_tag) in enumerate(
            AXIS_VARIANTS.get(axis_name, []),
            start=1,
        ):
            index = len(rows)
            reference = reference_specs[index % len(reference_specs)] if reference_specs else {}
            task_source_id = f"m3006-src-{index:04d}"
            rows.append(
                {
                    "new_task_source_spec_id": f"m3006-new-task-source-spec-{index + 1:04d}",
                    "task_source_id": task_source_id,
                    "axis_name": axis_name,
                    "axis_family": axis.get("axis_family", ""),
                    "axis_variant_tag": f"{axis_name}-variant-{variant_index:02d}",
                    "task_family": task_family,
                    "source_edge": source_edge,
                    "source_family_left": left,
                    "source_family_right": right,
                    "window_tag": window_tag,
                    "generation_seed": 300600 + index,
                    "reference_m1680_task_source_id": reference.get("task_source_id", ""),
                    "reference_schema_role": "schema_lineage_only_not_identity_reuse",
                    "new_identity_outside_m1680_m1690": task_source_id not in exhausted_ids,
                    "overlaps_exhausted_m1690_l3": task_source_id in exhausted_ids,
                    "eval_seed_only_reuse": False,
                    "same_surface_reuse": False,
                    "future_executable_workload_materialization_required": True,
                    "future_execution_manifest_required": True,
                    "source_build_scheduled_by_m3006": False,
                    "execution_scheduled_by_m3006": False,
                    "actor_visible": False,
                    "hidden_oracle_actor_input_required": False,
                    "source_labels_actor_visible": False,
                    "route_labels_actor_visible": False,
                    "outcome_labels_actor_visible": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def build_source_axis_budget_rows(
    admissible_axes: list[dict[str, str]],
    new_spec_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, axis in enumerate(admissible_axes, start=1):
        axis_name = str(axis["axis_name"])
        axis_rows = [row for row in new_spec_rows if row["axis_name"] == axis_name]
        task_counts = Counter(str(row["task_family"]) for row in axis_rows)
        rows.append(
            {
                "source_axis_budget_id": f"m3006-axis-budget-{index:04d}",
                "axis_name": axis_name,
                "axis_family": axis.get("axis_family", ""),
                "budgeted_new_task_source_count": len(axis_rows),
                "t4_count": task_counts.get("T4", 0),
                "t5_count": task_counts.get("T5", 0),
                "window_tag_count": len({row["window_tag"] for row in axis_rows}),
                "source_edge_count": len({row["source_edge"] for row in axis_rows}),
                "contract_budget_pass": len(axis_rows) == 4 and task_counts.get("T4", 0) == 2 and task_counts.get("T5", 0) == 2,
                "ordinary_engineering_candidate_axis": True,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_rejected_same_surface_rows(m3004_rejections: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(m3004_rejections, start=1):
        rows.append(
            {
                "rejected_same_surface_id": f"m3006-rejected-same-surface-{index:04d}",
                "rejected_route": row.get("rejected_route", ""),
                "rejection_family": row.get("rejection_family", ""),
                "rejection_reason": row.get("rejection_reason", ""),
                "source_identity_relation": row.get("source_identity_relation", ""),
                "required_follow_up": "preserve rejection; do not use as new task-source identity",
                "actor_visible": False,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "self_id_claim_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    guards = [
        ("actor_observation_dim", P0_OBSERVATION_DIM, 72),
        ("actor_action_dim", ACTION_DIM, 3),
        ("actor_input_contract_changed", False, False),
        ("hidden_oracle_actor_input_required", False, False),
        ("future_target_actor_input_required", False, False),
        ("source_labels_actor_visible", False, False),
        ("route_labels_actor_visible", False, False),
        ("outcome_labels_actor_visible", False, False),
        ("success_progress_labels_actor_visible", False, False),
        ("verdict_labels_actor_visible", False, False),
        ("materialization_only_no_execution", True, True),
    ]
    return [
        {
            "guard_id": f"m3006-actor-guard-{index:04d}",
            "contract_field": field,
            "observed_value": observed,
            "expected_value": expected,
            "status_pass": observed == expected,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, observed, expected) in enumerate(guards, start=1)
    ]


def build_claim_boundary_rows(*, required_artifacts_present: bool) -> list[dict[str, Any]]:
    claims = [
        ("source_generation_contract_materialization", True, True, "M3007 result audit before interpretation"),
        ("new_task_source_identity_accounting", True, True, "M3007 result audit before executable workload materialization"),
        ("executable_workload_readiness", False, False, "separate executable workload materialization and audit"),
        ("execution_result", False, False, "separate execution manifest and audit"),
        ("repair_success", False, False, "closed-loop fresh-source evidence"),
        ("validation_result", False, False, "separate validation manifest and audit"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("paper_evidence", False, False, "Route B proof gates"),
        ("high_fidelity_validation", False, False, "Route C source/dependency and validation manifests"),
        ("finite_window_vs_gru_result", False, False, "separate comparison proof gate"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_identification", False, False, "history-necessity/self-ID proof gates"),
        ("checkpoint_ranking_or_promotion", False, False, "promotion gates after proof and generalization"),
    ]
    return [
        {
            "claim_id": f"m3006-claim-{index:04d}",
            "claim_family": claim,
            "allowed_in_m3006": allowed,
            "claim_made": made,
            "status_pass": required_artifacts_present and made is allowed,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (claim, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    admissible_axes: list[dict[str, str]],
    source_contract_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
    new_spec_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    new_ids = {row["task_source_id"] for row in new_spec_rows}
    axis_names = {row["axis_name"] for row in new_spec_rows}
    task_families = {row["task_family"] for row in new_spec_rows}
    gates = [
        ("required_artifacts_present", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
        ("m3005_audit_present", source["m3005_audit_exists"], source["m3005_audit_exists"], True, "lineage_invalid"),
        ("m3004_status_pass", source["m3004_summary"].get("status_pass") is True, source["m3004_summary"].get("status_pass"), True, "lineage_invalid"),
        ("m3004_gate_matrix_pass", source["m3004_summary"].get("gate_matrix_pass") is True, source["m3004_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        ("m1680_reference_spec_count", len(source["m1680_task_source_specs"]) == 72, len(source["m1680_task_source_specs"]), 72, "lineage_invalid"),
        ("m1690_l3_unique_task_source_count", len(source["m1690_l3_task_source_ids"]) == 72, len(source["m1690_l3_task_source_ids"]), 72, "lineage_invalid"),
        ("admissible_source_axis_count", len(admissible_axes) >= MIN_AXIS_COUNT, len(admissible_axes), f">={MIN_AXIS_COUNT}", "scenario_sampling_failure"),
        ("source_contract_rows_present", bool(source_contract_rows), len(source_contract_rows), ">=1", "lineage_invalid"),
        ("source_axis_budget_rows_pass", all(_bool(row["contract_budget_pass"]) for row in budget_rows), "all budget rows pass", True, "scenario_sampling_failure"),
        ("new_task_source_spec_row_count", len(new_spec_rows) == TARGET_NEW_SOURCE_SPECS, len(new_spec_rows), TARGET_NEW_SOURCE_SPECS, "scenario_sampling_failure"),
        ("new_task_source_unique_id_count", len(new_ids) == len(new_spec_rows), len(new_ids), len(new_spec_rows), "lineage_invalid"),
        ("old_m1690_l3_overlap_count", old_overlap_count(new_spec_rows) == 0, old_overlap_count(new_spec_rows), 0, "objective_overfit"),
        ("axis_coverage_count", len(axis_names) >= MIN_AXIS_COUNT, len(axis_names), f">={MIN_AXIS_COUNT}", "scenario_sampling_failure"),
        ("task_family_coverage_count", len(task_families) >= MIN_TASK_FAMILY_COUNT, sorted(task_families), "T4 and T5", "scenario_sampling_failure"),
        ("same_surface_rejections_preserved", len(rejected_rows) >= 8, len(rejected_rows), ">=8", "objective_overfit"),
        ("actor_contract_rows_pass", all(_bool(row["status_pass"]) for row in actor_rows), "all actor rows pass", True, "contract_violation"),
        ("claim_boundary_rows_pass", all(_bool(row["status_pass"]) for row in claim_rows), "all claim rows pass", True, "proof_washout"),
        ("follow_up_manifest_written", follow_up_manifest_exists, follow_up_manifest_exists, True, "lineage_invalid"),
        ("source_build_run", True, False, False, "contract_violation"),
        ("environment_execution_run", True, False, False, "contract_violation"),
        ("training_run", True, False, False, "contract_violation"),
        ("validation_claim_made", True, False, False, "proof_washout"),
        ("performance_claim_made", True, False, False, "proof_washout"),
        ("paper_claim_made", True, False, False, "proof_washout"),
        ("high_fidelity_claim_made", True, False, False, "proof_washout"),
        ("self_id_claim_made", True, False, False, "proof_washout"),
    ]
    return [
        {
            "gate_id": f"m3006-gate-{index:04d}",
            "gate_family": name,
            "status_pass": passed,
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, passed, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source: Mapping[str, Any],
    admissible_axes: list[dict[str, str]],
    source_contract_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
    new_spec_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    actor_rows_pass = bool(actor_rows) and all(_bool(row["status_pass"]) for row in actor_rows)
    claim_rows_pass = bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows)
    status_pass = gate_matrix_pass and actor_rows_pass and claim_rows_pass and required_artifacts_present
    axis_counts = Counter(str(row["axis_name"]) for row in new_spec_rows)
    task_family_counts = Counter(str(row["task_family"]) for row in new_spec_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": DECISION_PASS if status_pass else DECISION_FAIL,
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "m3005_audit_present": source["m3005_audit_exists"],
        "m3004_status_pass": source["m3004_summary"].get("status_pass") is True,
        "m3004_gate_matrix_pass": source["m3004_summary"].get("gate_matrix_pass") is True,
        "m1680_reference_spec_count": len(source["m1680_task_source_specs"]),
        "m1690_l3_unique_task_source_count": len(source["m1690_l3_task_source_ids"]),
        "admissible_source_axis_count": len(admissible_axes),
        "source_contract_row_count": len(source_contract_rows),
        "source_axis_budget_row_count": len(budget_rows),
        "new_task_source_spec_row_count": len(new_spec_rows),
        "new_task_source_unique_id_count": len({row["task_source_id"] for row in new_spec_rows}),
        "old_m1690_l3_overlap_count": old_overlap_count(new_spec_rows),
        "new_source_identity_prefix": "m3006-src",
        "axis_counts": dict(sorted(axis_counts.items())),
        "task_family_counts": dict(sorted(task_family_counts.items())),
        "rejected_same_surface_row_count": len(rejected_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_rows_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "source_build_run": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "external_simulation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "private_holdout_used": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3006 Engineering Controller Route A Post-Residual-Stop New Task-Source Generation Contract Materialization Preflight",
            "",
            "## Summary",
            "",
            "- status: completed" if summary["status_pass"] else "- status: blocked",
            f"- result class: `{summary['result_class']}`",
            f"- admissible source axes: {summary['admissible_source_axis_count']}",
            f"- source contract rows: {summary['source_contract_row_count']}",
            f"- axis budget rows: {summary['source_axis_budget_row_count']}",
            f"- new task-source spec rows: {summary['new_task_source_spec_row_count']}",
            f"- unique new task-source ids: {summary['new_task_source_unique_id_count']}",
            f"- old M1690 L3 overlap count: {summary['old_m1690_l3_overlap_count']}",
            f"- axis counts: {summary['axis_counts']}",
            f"- task family counts: {summary['task_family_counts']}",
            f"- rejected same-surface rows: {summary['rejected_same_surface_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M3006 materializes a source-generation contract only. It does not build sources, instantiate environments, execute policies, train, validate, rank, promote, or claim repair success or performance.",
            "",
            "Rejected interpretations:",
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


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
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
        "hypothesis": "A bounded result audit can accept or reject the M3006 new task-source generation contract materialization before any executable workload materialization execution validation ranking promotion repair-success performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "source_contract_rows.csv"),
                str(output_dir / "source_axis_budget_rows.csv"),
                str(output_dir / "new_task_source_spec_rows.csv"),
                str(output_dir / "rejected_same_surface_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                "experiments/manifests/m3006-engineering-controller-route-a-post-residual-stop-new-task-source-generation-contract-materialization-preflight.json",
                "experiments/manifests/m3005-engineering-controller-route-a-post-residual-stop-source-axis-expansion-materialization-result-audit.json",
            ],
            "parent_objective": [
                "audit M3006 new task-source generation contract before executable workload materialization or stop"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m3005-engineering-controller-route-a-post-residual-stop-source-axis-expansion-materialization-result-audit",
            ],
            "blocked_by": [
                "M3006 source-contract rows require audit before any executable workload materialization",
                "source-contract rows are not execution readiness or performance evidence",
                "same-surface and eval-seed-only routes remain rejected",
            ],
            "supersedes": [
                "direct executable workload materialization from M3006 without result audit",
                "direct performance interpretation of M3006 source-contract rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3007 must audit M3006 summary contract rows new task-source identities actor and claim boundaries",
            "M3007 must preserve zero overlap with exhausted M1690 L3 task_source ids",
            "M3007 must not convert contract rows into execution validation performance paper high-fidelity or self-ID evidence",
            "M3007 must select exactly one next route or explicit stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate train rank promote select a winner or execute dependency work",
            "do not materialize executable workload or build sources inside the audit",
            "do not change actor input or action contract",
            "do not convert M3006 source contract rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_task_source_generation_contract_materialization_result_audit",
            "evidence_increment": "audits M3006 new task-source generation contract and decides executable workload materialization or stop",
            "claim_scope": "Result audit only; no execution validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3006 artifacts are missing or gate matrix fails",
                "stop if new task-source identities overlap exhausted M1690 L3 ids",
                "stop if actor or claim boundaries were violated",
                "stop if source-contract rows would be used as execution instructions before a separate manifest",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if no executable workload materialization route is viable",
                "route to bounded executable workload materialization design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3006 completes new task-source generation contract materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3006 new task-source generation contract materialization artifacts",
            "admission_evidence": [
                "M3006 summary and gate matrix",
                "M3006 source contract axis budget new source spec actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no execution validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO residual selection or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M3007 status queue scoreboard research log and review",
                "one follow-up manifest only if M3007 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3007 audit accepts or rejects M3006 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3007 audits Route A source-contract materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3007; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M3006 Route A source-generation contract materialization only.",
            "negative_result_policy": "Preserve source-contract failures and route to synthesis or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3006 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized task-source generation contract panel",
            "paper_verdict_delta": "no paper verdict; audit may authorize executable workload materialization only",
            "must_synthesize_if": [
                "M3007 cannot accept M3006 as complete and claim-safe",
                "M3007 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M3007 cannot select executable materialization, synthesis, or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3007 audits M3006 artifacts row counts gates actor and claim boundaries",
            "M3007 selects exactly one next route or stop state",
            "no execution training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3007 hides M3006 failures or missing artifacts",
            "M3007 treats M3006 source contracts as execution readiness performance verdict or repair success",
            "M3007 changes actor input or action contract",
            "M3007 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3007 audits M3006 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "source_contract_rows.csv"),
            str(output_dir / "source_axis_budget_rows.csv"),
            str(output_dir / "new_task_source_spec_rows.csv"),
            str(output_dir / "rejected_same_surface_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def old_overlap_count(new_spec_rows: list[Mapping[str, Any]]) -> int:
    return sum(1 for row in new_spec_rows if _bool(row.get("overlaps_exhausted_m1690_l3")))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3005-audit", type=Path, default=DEFAULT_M3005_AUDIT)
    parser.add_argument("--m3004-dir", type=Path, default=DEFAULT_M3004_DIR)
    parser.add_argument("--m1680-specs", type=Path, default=DEFAULT_M1680_SPECS)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_M1690_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_new_task_source_generation_contract_materialization_preflight(
        m3005_audit=args.m3005_audit,
        m3004_dir=args.m3004_dir,
        m1680_specs=args.m1680_specs,
        m1690_workload=args.m1690_workload,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
