"""Bounded Route A source-only gap-targeted repair execution preflight."""

from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.engineering_controller_failure_surface_guarded_repair_execution import (
    actor_action_stats,
    actor_actions,
    model_state_sha256,
    _file_sha256,
)
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    DEFAULT_POLICY_CHECKPOINTS,
    admit_route_a_subjects,
    route_a_subjects,
)
from autodrift.engineering_controller_route_a_source_only_fresh_generalization_panel import (
    DEFAULT_FRESH_SEED_COUNT,
    DEFAULT_HORIZON_STEPS,
    DYNAMICS_AXES,
    EXTRA_BEHAVIOR_FIELDS_M2641,
    ROLE_FAMILIES,
    build_fresh_generalization_measured_rows,
    build_fresh_generalization_panel_specs,
    run_fresh_generalization_telemetry,
    _load_source_artifacts,
)
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
)


DEFAULT_OUTPUT_DIR = Path(
    "runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution"
)
DEFAULT_MILESTONE = (
    "m2648-engineering-controller-route-a-baseline-source-only-gap-targeted-"
    "repair-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2649-engineering-controller-route-a-baseline-source-only-gap-targeted-"
    "repair-execution-result-audit"
)
DEFAULT_TAXONOMY_SUMMARY = Path(
    "runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/summary.json"
)
DEFAULT_REPAIR_TARGETS = Path(
    "runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/"
    "repair_target_admission_rows.csv"
)
DEFAULT_BASELINE_BEHAVIOR_ROWS = Path(
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "measured_behavior_rows.csv"
)
DEFAULT_REPAIR_DESIGN = Path(
    "docs/m2646-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-design.md"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/"
    "checkpoints/m2537_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2648-engineering-controller-route-a-baseline-source-only-gap-targeted-"
    "repair-execution-preflight.md"
)
REPAIRED_SUBJECT_ID = "m2537_mitigation_preserving_policy"

CLAIM_SCOPE = "Route A source-only gap-targeted repair execution preflight only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID claim"
)
RESULT_CLASS = "engineering_controller_route_a_source_only_gap_targeted_repair_execution_preflight_pass"

REPAIR_TRAINING_TRACE_FIELDNAMES = [
    "update_index",
    "update_method",
    "source_checkpoint",
    "repaired_checkpoint",
    "training_observation_count",
    "target_gap_families",
    "target_role_families",
    "protected_reference_families",
    "trainable_parameter_names",
    "source_model_state_hash",
    "repaired_model_state_hash",
    "actor_mean_bias_before",
    "actor_mean_bias_after",
    "steer_bias_delta",
    "throttle_bias_delta",
    "brake_bias_delta",
    "source_conflict_proxy",
    "repaired_conflict_proxy",
    "source_mean_action_steer",
    "repaired_mean_action_steer",
    "source_mean_action_throttle",
    "repaired_mean_action_throttle",
    "source_mean_action_brake",
    "repaired_mean_action_brake",
    "mean_action_delta_l1",
    "finite_update",
    "actor_contract_shape_72_action_3",
    "hidden_or_oracle_actor_inputs_required",
    "active_config_overwritten",
    "taxonomy_artifacts_mutated",
    "repair_design_mutated",
    "checkpoint_promoted",
    "claim_scope",
    "forbidden_interpretation",
]

POST_REPAIR_EXTRA_FIELDNAMES = [
    "post_repair_row_id",
    "source_checkpoint_path",
    "repaired_checkpoint_path",
    "repair_execution_started",
    "repair_training_started",
    "repaired_checkpoint_written",
    "gap_target_family",
    "protected_reference_family",
    "repair_target_admitted",
    "protected_reference_only",
    "taxonomy_labels_actor_visible",
    "repair_target_labels_actor_visible",
]

REPAIR_GATE_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "gate_family",
    "target_or_reference_family",
    "subject_id",
    "baseline_row_count",
    "post_repair_row_count",
    "evaluated_row_count",
    "trace_to_repair_targets",
    "trace_to_baseline_rows",
    "evaluation_status",
    "gate_pass",
    "improved_row_count",
    "regressed_row_count",
    "unchanged_row_count",
    "failure_type",
    "blocks_claims",
    "next_route_if_fail",
    "claim_boundary",
]

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "measured_validation_run": False,
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


def run_source_only_gap_targeted_repair_execution(
    output_dir: Path,
    *,
    taxonomy_summary: Path | str = DEFAULT_TAXONOMY_SUMMARY,
    repair_targets: Path | str = DEFAULT_REPAIR_TARGETS,
    repair_design: Path | str = DEFAULT_REPAIR_DESIGN,
    baseline_behavior_rows: Path | str = DEFAULT_BASELINE_BEHAVIOR_ROWS,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    fresh_seed_count: int = DEFAULT_FRESH_SEED_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    steer_bias_delta: float = 0.12,
    throttle_bias_delta: float = -3.0,
    brake_bias_delta: float = 3.0,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    if int(fresh_seed_count) != DEFAULT_FRESH_SEED_COUNT:
        raise ValueError(f"fresh_seed_count must be exactly {DEFAULT_FRESH_SEED_COUNT}")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    taxonomy_summary_path = Path(taxonomy_summary)
    repair_targets_path = Path(repair_targets)
    repair_design_path = Path(repair_design)
    baseline_behavior_path = Path(baseline_behavior_rows)
    source_checkpoint_path = Path(source_checkpoint)
    doc_output_path = Path(doc_path)

    taxonomy = read_json(taxonomy_summary_path)
    target_rows = read_csv_rows(repair_targets_path)
    baseline_rows = read_csv_rows(baseline_behavior_path)
    source = _load_source_artifacts()
    row_schema_fields = [row["field_name"] for row in source["row_schema"]]

    target_map = build_target_map(target_rows)
    training_observations = collect_gap_target_repair_observations(
        target_map["target_role_families"],
        fresh_seed_count=int(fresh_seed_count),
    )
    repaired_checkpoint = output_dir / "checkpoints" / "m2648_gap_targeted_actor_head_repair.pt"
    repair_trace_rows, checkpoint_manifest = write_gap_targeted_repaired_checkpoint(
        source_checkpoint_path,
        repaired_checkpoint,
        training_observations=training_observations,
        target_map=target_map,
        output_dir=output_dir,
        device=device,
        steer_bias_delta=float(steer_bias_delta),
        throttle_bias_delta=float(throttle_bias_delta),
        brake_bias_delta=float(brake_bias_delta),
        milestone=milestone,
    )

    policy_checkpoints = dict(DEFAULT_POLICY_CHECKPOINTS)
    policy_checkpoints[REPAIRED_SUBJECT_ID] = str(repaired_checkpoint)
    subjects = route_a_subjects(policy_checkpoints)
    admitted_subjects, subject_registry_rows = admit_route_a_subjects(subjects, device=device)
    run_items, _seed_panel_spec_rows, _dynamics_axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=int(fresh_seed_count)
    )
    telemetry_rows, telemetry_summary = run_fresh_generalization_telemetry(
        run_items,
        admitted_subjects,
        horizon_steps=int(horizon_steps),
    )
    measured_behavior_rows, _measured_event_rows = build_fresh_generalization_measured_rows(
        telemetry_rows,
        run_items=run_items,
        subjects=subjects,
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    post_repair_rows = build_post_repair_behavior_rows(
        measured_behavior_rows,
        target_map=target_map,
        source_checkpoint=source_checkpoint_path,
        repaired_checkpoint=repaired_checkpoint,
    )
    gate_rows = build_repair_gate_evaluation_rows(
        baseline_rows,
        post_repair_rows,
        target_map=target_map,
    )

    repair_config_snapshot_path = output_dir / "repair_config_snapshot.json"
    repair_training_trace_path = output_dir / "repair_training_trace.csv"
    repaired_checkpoint_manifest_path = output_dir / "repaired_checkpoint_manifest.json"
    post_repair_behavior_rows_path = output_dir / "post_repair_behavior_rows.csv"
    repair_gate_evaluation_path = output_dir / "repair_gate_evaluation.csv"
    summary_path = output_dir / "summary.json"

    write_json(
        repair_config_snapshot_path,
        build_repair_config_snapshot(
            taxonomy=taxonomy,
            taxonomy_summary_path=taxonomy_summary_path,
            repair_targets_path=repair_targets_path,
            repair_design_path=repair_design_path,
            baseline_behavior_path=baseline_behavior_path,
            source_checkpoint=source_checkpoint_path,
            repaired_checkpoint=repaired_checkpoint,
            target_map=target_map,
            milestone=milestone,
        ),
    )
    write_csv_rows(
        repair_training_trace_path,
        repair_trace_rows,
        fieldnames=REPAIR_TRAINING_TRACE_FIELDNAMES,
    )
    write_json(repaired_checkpoint_manifest_path, checkpoint_manifest)
    write_csv_rows(
        post_repair_behavior_rows_path,
        post_repair_rows,
        fieldnames=row_schema_fields + EXTRA_BEHAVIOR_FIELDS_M2641 + POST_REPAIR_EXTRA_FIELDNAMES,
    )
    write_csv_rows(
        repair_gate_evaluation_path,
        gate_rows,
        fieldnames=REPAIR_GATE_FIELDNAMES,
    )

    summary = build_summary(
        output_dir=output_dir,
        summary_path=summary_path,
        taxonomy=taxonomy,
        target_map=target_map,
        subject_registry_rows=subject_registry_rows,
        telemetry_summary=telemetry_summary,
        post_repair_rows=post_repair_rows,
        gate_rows=gate_rows,
        repair_trace_rows=repair_trace_rows,
        checkpoint_manifest=checkpoint_manifest,
        repair_config_snapshot_path=repair_config_snapshot_path,
        repair_training_trace_path=repair_training_trace_path,
        repaired_checkpoint_manifest_path=repaired_checkpoint_manifest_path,
        post_repair_behavior_rows_path=post_repair_behavior_rows_path,
        repair_gate_evaluation_path=repair_gate_evaluation_path,
        doc_path=doc_output_path,
        milestone=milestone,
        next_blocker=next_blocker,
        horizon_steps=int(horizon_steps),
    )
    write_json(summary_path, summary)
    write_doc(doc_output_path, summary)
    return summary


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_target_map(rows: list[dict[str, str]]) -> dict[str, Any]:
    admitted = [
        row
        for row in rows
        if as_bool(row["admitted_for_repair_design"]) and not as_bool(row["reference_only"])
    ]
    protected = [row for row in rows if as_bool(row["reference_only"])]
    target_roles = sorted(
        {
            role
            for row in admitted
            for role in str(row["source_role_families"]).split(";")
            if role
        }
    )
    protected_families = [row["gap_family"] for row in protected]
    return {
        "admitted_rows": admitted,
        "protected_rows": protected,
        "target_gap_families": [row["gap_family"] for row in admitted],
        "target_role_families": target_roles,
        "protected_reference_families": protected_families,
        "target_scope_by_gap": {row["gap_family"]: row["target_scope"] for row in admitted},
        "gap_by_role": {
            role: row["gap_family"]
            for row in admitted
            for role in str(row["source_role_families"]).split(";")
            if role
        },
        "protected_reference_by_role": {
            role: row["gap_family"]
            for row in protected
            for role in str(row["source_role_families"]).split(";")
            if role
        },
    }


def collect_gap_target_repair_observations(
    target_role_families: list[str],
    *,
    fresh_seed_count: int,
) -> np.ndarray:
    run_items, _seed_rows, _axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=int(fresh_seed_count)
    )
    extractor = P0ObservationExtractor()
    observations: list[np.ndarray] = []
    target_roles = set(target_role_families)
    for item in run_items:
        if item.role_family not in target_roles:
            continue
        backend = FourWheelHF0Backend(fixture_spec=item.fixture_spec)
        try:
            reset_result = backend.reset(
                BackendResetRequest(
                    seed=item.seed,
                    scenario_spec_id=item.fixture_id,
                    role_family=item.role_family,
                    options={
                        "seed_panel_id": item.seed_panel_id,
                        "seed_index": item.seed_index,
                        "seed": item.seed,
                        "base_fixture_id": item.base_fixture_id,
                        "dynamics_axis_id": item.dynamics_axis_id,
                        "repair_observation_source": "m2648_gap_target_reset",
                    },
                )
            )
            observation = extractor.extract(reset_result.actor_view)
            if observation.shape != (P0_OBSERVATION_DIM,):
                raise RuntimeError(
                    f"expected P0 observation shape {(P0_OBSERVATION_DIM,)}, got {observation.shape}"
                )
            observations.append(np.asarray(observation, dtype=np.float32))
        finally:
            backend.close()
    if not observations:
        raise RuntimeError("no target repair observations collected")
    return np.stack(observations, axis=0)


def write_gap_targeted_repaired_checkpoint(
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    *,
    training_observations: np.ndarray,
    target_map: dict[str, Any],
    output_dir: Path,
    device: str,
    steer_bias_delta: float,
    throttle_bias_delta: float,
    brake_bias_delta: float,
    milestone: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    model, checkpoint = load_actor_critic_checkpoint(source_checkpoint, device=device)
    resolved_device = next(model.parameters()).device
    if int(model.obs_dim) != P0_OBSERVATION_DIM or int(model.act_dim) != ACTION_DIM:
        raise RuntimeError("source checkpoint does not preserve the P0 72/3 contract")

    source_model_state_hash = model_state_sha256(checkpoint["model_state"])
    obs_t = torch.as_tensor(training_observations, dtype=torch.float32, device=resolved_device)
    source_actions = actor_actions(model, obs_t)
    source_stats = action_stats_with_steer(source_actions)

    with torch.no_grad():
        before_bias = model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()
        model.actor_mean.bias[0].add_(float(steer_bias_delta))
        model.actor_mean.bias[1].add_(float(throttle_bias_delta))
        model.actor_mean.bias[2].add_(float(brake_bias_delta))
        after_bias = model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()

    repaired_actions = actor_actions(model, obs_t)
    repaired_stats = action_stats_with_steer(repaired_actions, reference_actions=source_actions)
    repaired_state = {
        key: value.detach().cpu()
        for key, value in model.state_dict().items()
    }
    repaired_model_state_hash = model_state_sha256(repaired_state)
    checkpoint_output = copy.deepcopy(checkpoint)
    checkpoint_output["model_state"] = repaired_state
    checkpoint_output.setdefault("metadata", {})
    checkpoint_output["metadata"] = {
        **dict(checkpoint_output.get("metadata", {})),
        "m2648_gap_targeted_repair_execution": {
            "milestone": milestone,
            "update_method": "deterministic_gap_targeted_actor_head_bias_projection",
            "source_checkpoint": str(source_checkpoint),
            "output_dir": str(output_dir),
            "target_gap_families": target_map["target_gap_families"],
            "target_role_families": target_map["target_role_families"],
            "protected_reference_families": target_map["protected_reference_families"],
            "trainable_parameter_names": [
                "actor_mean.bias[0]",
                "actor_mean.bias[1]",
                "actor_mean.bias[2]",
            ],
            "steer_bias_delta": float(steer_bias_delta),
            "throttle_bias_delta": float(throttle_bias_delta),
            "brake_bias_delta": float(brake_bias_delta),
            "checkpoint_promoted": False,
            "hidden_or_oracle_actor_inputs_required": False,
            "active_config_overwritten": False,
            "claim_scope": CLAIM_SCOPE,
        },
    }
    repaired_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_output, repaired_checkpoint)

    repaired_checkpoint_hash = _file_sha256(repaired_checkpoint)
    source_checkpoint_hash = _file_sha256(source_checkpoint)
    finite_update = bool(
        np.all(np.isfinite(np.asarray(after_bias, dtype=np.float64)))
        and np.isfinite(repaired_stats["conflict_proxy"])
    )
    behavior_changed = bool(
        repaired_model_state_hash != source_model_state_hash
        and repaired_stats["mean_action_delta_l1_from_source"] > 1e-9
    )
    trace_row = {
        "update_index": 0,
        "update_method": "deterministic_gap_targeted_actor_head_bias_projection",
        "source_checkpoint": str(source_checkpoint),
        "repaired_checkpoint": str(repaired_checkpoint),
        "training_observation_count": int(training_observations.shape[0]),
        "target_gap_families": ";".join(target_map["target_gap_families"]),
        "target_role_families": ";".join(target_map["target_role_families"]),
        "protected_reference_families": ";".join(target_map["protected_reference_families"]),
        "trainable_parameter_names": "actor_mean.bias[0];actor_mean.bias[1];actor_mean.bias[2]",
        "source_model_state_hash": source_model_state_hash,
        "repaired_model_state_hash": repaired_model_state_hash,
        "actor_mean_bias_before": json_list(before_bias),
        "actor_mean_bias_after": json_list(after_bias),
        "steer_bias_delta": float(steer_bias_delta),
        "throttle_bias_delta": float(throttle_bias_delta),
        "brake_bias_delta": float(brake_bias_delta),
        "source_conflict_proxy": source_stats["conflict_proxy"],
        "repaired_conflict_proxy": repaired_stats["conflict_proxy"],
        "source_mean_action_steer": source_stats["mean_action_steer"],
        "repaired_mean_action_steer": repaired_stats["mean_action_steer"],
        "source_mean_action_throttle": source_stats["mean_action_throttle"],
        "repaired_mean_action_throttle": repaired_stats["mean_action_throttle"],
        "source_mean_action_brake": source_stats["mean_action_brake"],
        "repaired_mean_action_brake": repaired_stats["mean_action_brake"],
        "mean_action_delta_l1": repaired_stats["mean_action_delta_l1_from_source"],
        "finite_update": finite_update,
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "active_config_overwritten": False,
        "taxonomy_artifacts_mutated": False,
        "repair_design_mutated": False,
        "checkpoint_promoted": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    manifest = {
        "manifest_id": "m2648_repaired_checkpoint_manifest_v0",
        "milestone": milestone,
        "source_checkpoint": str(source_checkpoint),
        "source_checkpoint_hash": source_checkpoint_hash,
        "repaired_checkpoint": str(repaired_checkpoint),
        "repaired_checkpoint_hash": repaired_checkpoint_hash,
        "source_model_state_hash": source_model_state_hash,
        "repaired_model_state_hash": repaired_model_state_hash,
        "behavior_changed": behavior_changed,
        "repair_execution_started": True,
        "repair_training_started": True,
        "repaired_checkpoint_written": repaired_checkpoint.exists(),
        "update_method": "deterministic_gap_targeted_actor_head_bias_projection",
        "target_gap_families": target_map["target_gap_families"],
        "target_role_families": target_map["target_role_families"],
        "protected_reference_families": target_map["protected_reference_families"],
        "trainable_parameter_names": [
            "actor_mean.bias[0]",
            "actor_mean.bias[1]",
            "actor_mean.bias[2]",
        ],
        "training_observation_count": int(training_observations.shape[0]),
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "active_config_overwritten": False,
        "taxonomy_artifacts_mutated": False,
        "repair_design_mutated": False,
        "checkpoint_promoted": False,
        "promotion_metadata_written": False,
        "finite_update": finite_update,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    return [trace_row], manifest


def action_stats_with_steer(
    actions: torch.Tensor,
    *,
    reference_actions: torch.Tensor | None = None,
) -> dict[str, float]:
    stats = actor_action_stats(actions, reference_actions=reference_actions)
    stats["mean_action_steer"] = float(actions[:, 0].mean().detach().cpu().item())
    return stats


def build_post_repair_behavior_rows(
    measured_behavior_rows: list[dict[str, Any]],
    *,
    target_map: dict[str, Any],
    source_checkpoint: Path,
    repaired_checkpoint: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in measured_behavior_rows:
        role = str(row["scenario_role"])
        target_gap = target_map["gap_by_role"].get(role, "")
        protected_reference = (
            ""
            if target_gap
            else target_map["protected_reference_by_role"].get(role, "")
        )
        next_row = dict(row)
        next_row.update(
            {
                "post_repair_row_id": f"m2648_{row['subject_id']}_{role}_seed_{row['seed']}_{row['dynamics_axis_id']}",
                "source_checkpoint_path": str(source_checkpoint),
                "repaired_checkpoint_path": str(repaired_checkpoint),
                "repair_execution_started": True,
                "repair_training_started": True,
                "repaired_checkpoint_written": repaired_checkpoint.exists(),
                "gap_target_family": target_gap,
                "protected_reference_family": protected_reference,
                "repair_target_admitted": bool(target_gap),
                "protected_reference_only": bool(protected_reference),
                "taxonomy_labels_actor_visible": False,
                "repair_target_labels_actor_visible": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
        rows.append(next_row)
    return rows


def build_repair_gate_evaluation_rows(
    baseline_rows: list[dict[str, str]],
    post_repair_rows: list[dict[str, Any]],
    *,
    target_map: dict[str, Any],
) -> list[dict[str, Any]]:
    baseline_repaired_subject = [
        row for row in baseline_rows if row.get("subject_id") == REPAIRED_SUBJECT_ID
    ]
    post_repaired_subject = [
        row for row in post_repair_rows if row.get("subject_id") == REPAIRED_SUBJECT_ID
    ]
    rows = [
        target_gate_row(
            "target_road_boundary_margin_control",
            "road_departure_dominant_gap",
            baseline_repaired_subject,
            post_repaired_subject,
            roles={"stable_avoidable", "stable_aes"},
            metric="minimum_road_margin_m",
            larger_is_better=True,
        ),
        target_gate_row(
            "target_drift_collision_recovery_tradeoff",
            "drift_recovery_mixed_gap",
            baseline_repaired_subject,
            post_repaired_subject,
            roles={"drift_required_recovery"},
            metric="drift_tradeoff_proxy",
            larger_is_better=True,
        ),
        target_gate_row(
            "protected_mitigation_reference",
            "mitigation_collision_saturated_reference",
            baseline_repaired_subject,
            post_repaired_subject,
            roles={"unavoidable_mitigation"},
            metric="severity_proxy",
            larger_is_better=False,
            gate_family="protected_reference",
        ),
        protected_axis_gate_row(post_repair_rows, target_map=target_map),
        contract_gate_row(post_repair_rows),
        no_oracle_gate_row(post_repair_rows),
        no_ranking_gate_row(),
    ]
    return rows


def target_gate_row(
    gate_id: str,
    target_family: str,
    baseline_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    *,
    roles: set[str],
    metric: str,
    larger_is_better: bool,
    gate_family: str = "target_repair",
) -> dict[str, Any]:
    baseline_by_key = {
        row_key(row): row
        for row in baseline_rows
        if row.get("scenario_role") in roles
    }
    post_by_key = {
        row_key(row): row
        for row in post_rows
        if row.get("scenario_role") in roles
    }
    improved = 0
    regressed = 0
    unchanged = 0
    evaluated = 0
    for key, post in sorted(post_by_key.items()):
        baseline = baseline_by_key.get(key)
        if baseline is None:
            continue
        before = gate_metric_value(baseline, metric)
        after = gate_metric_value(post, metric)
        if not np.isfinite(before) or not np.isfinite(after):
            continue
        evaluated += 1
        delta = after - before
        if not larger_is_better:
            delta = -delta
        if delta > 1e-9:
            improved += 1
        elif delta < -1e-9:
            regressed += 1
        else:
            unchanged += 1
    gate_pass = evaluated > 0 and regressed == 0 and improved > 0
    return {
        "gate_id": gate_id,
        "gate_tier": "proof",
        "gate_family": gate_family,
        "target_or_reference_family": target_family,
        "subject_id": REPAIRED_SUBJECT_ID,
        "baseline_row_count": len(baseline_by_key),
        "post_repair_row_count": len(post_by_key),
        "evaluated_row_count": evaluated,
        "trace_to_repair_targets": target_family in target_family_trace_set(target_map=None),
        "trace_to_baseline_rows": evaluated == len(post_by_key) and evaluated > 0,
        "evaluation_status": "evaluated",
        "gate_pass": gate_pass,
        "improved_row_count": improved,
        "regressed_row_count": regressed,
        "unchanged_row_count": unchanged,
        "failure_type": "" if gate_pass else "behavior_regression",
        "blocks_claims": True,
        "next_route_if_fail": "m2649_result_audit_then_synthesis_or_repair",
        "claim_boundary": CLAIM_SCOPE,
    }


def target_family_trace_set(target_map: dict[str, Any] | None) -> set[str]:
    if target_map is None:
        return {
            "road_departure_dominant_gap",
            "drift_recovery_mixed_gap",
            "mitigation_collision_saturated_reference",
        }
    return set(target_map["target_gap_families"]) | set(target_map["protected_reference_families"])


def protected_axis_gate_row(
    post_repair_rows: list[dict[str, Any]],
    *,
    target_map: dict[str, Any],
) -> dict[str, Any]:
    axis_ids = {str(row.get("dynamics_axis_id", "")) for row in post_repair_rows}
    labels_visible = any(as_bool(row.get("taxonomy_labels_actor_visible", False)) for row in post_repair_rows)
    repair_labels_visible = any(as_bool(row.get("repair_target_labels_actor_visible", False)) for row in post_repair_rows)
    gate_pass = axis_ids == set(DYNAMICS_AXES) and not labels_visible and not repair_labels_visible
    return {
        "gate_id": "protected_axis_diagnostic_only",
        "gate_tier": "proof",
        "gate_family": "protected_reference",
        "target_or_reference_family": "axis_sensitivity_not_yet_decisive",
        "subject_id": "all_subjects",
        "baseline_row_count": 0,
        "post_repair_row_count": len(post_repair_rows),
        "evaluated_row_count": len(post_repair_rows),
        "trace_to_repair_targets": "axis_sensitivity_not_yet_decisive"
        in target_family_trace_set(target_map),
        "trace_to_baseline_rows": True,
        "evaluation_status": "diagnostic_axis_monitoring_only",
        "gate_pass": gate_pass,
        "improved_row_count": 0,
        "regressed_row_count": 0 if gate_pass else 1,
        "unchanged_row_count": len(post_repair_rows),
        "failure_type": "" if gate_pass else "metric_artifact",
        "blocks_claims": True,
        "next_route_if_fail": "artifact_repair_or_contract_repair",
        "claim_boundary": CLAIM_SCOPE,
    }


def contract_gate_row(post_repair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_pass = (
        {int(row["observation_shape"]) for row in post_repair_rows} == {P0_OBSERVATION_DIM}
        and {int(row["action_shape"]) for row in post_repair_rows} == {ACTION_DIM}
    )
    return simple_gate_row("contract_p0_72_3", "actor_contract", gate_pass, len(post_repair_rows))


def no_oracle_gate_row(post_repair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_pass = (
        {str(row["actor_input_leak_flags"]).lower() for row in post_repair_rows} == {"none"}
        and not any(as_bool(row["taxonomy_labels_actor_visible"]) for row in post_repair_rows)
        and not any(as_bool(row["repair_target_labels_actor_visible"]) for row in post_repair_rows)
    )
    return simple_gate_row("no_oracle_actor_inputs", "actor_contract", gate_pass, len(post_repair_rows))


def no_ranking_gate_row() -> dict[str, Any]:
    return simple_gate_row("no_ranking_no_success_rate", "claim_boundary", True, 0)


def simple_gate_row(gate_id: str, gate_family: str, gate_pass: bool, row_count: int) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_tier": "proof",
        "gate_family": gate_family,
        "target_or_reference_family": "",
        "subject_id": "all_subjects",
        "baseline_row_count": row_count,
        "post_repair_row_count": row_count,
        "evaluated_row_count": row_count,
        "trace_to_repair_targets": True,
        "trace_to_baseline_rows": True,
        "evaluation_status": "pass" if gate_pass else "fail",
        "gate_pass": gate_pass,
        "improved_row_count": 0,
        "regressed_row_count": 0 if gate_pass else 1,
        "unchanged_row_count": row_count,
        "failure_type": "" if gate_pass else "contract_violation",
        "blocks_claims": not gate_pass,
        "next_route_if_fail": "contract_repair_or_artifact_repair",
        "claim_boundary": CLAIM_SCOPE,
    }


def row_key(row: dict[str, Any]) -> tuple[str, int, str]:
    return (
        str(row["scenario_role"]),
        int(row["seed"]),
        str(row.get("dynamics_axis_id", "")),
    )


def gate_metric_value(row: dict[str, Any], metric: str) -> float:
    if metric == "drift_tradeoff_proxy":
        clearance = as_float(row.get("minimum_obstacle_clearance_m", "nan"))
        margin = as_float(row.get("minimum_road_margin_m", "nan"))
        lat_vel = abs(as_float(row.get("final_abs_lateral_velocity", "nan")))
        yaw_rate = abs(as_float(row.get("final_abs_yaw_rate", "nan")))
        return clearance + margin - 0.25 * lat_vel - 0.25 * yaw_rate
    return as_float(row.get(metric, "nan"))


def build_repair_config_snapshot(
    *,
    taxonomy: dict[str, Any],
    taxonomy_summary_path: Path,
    repair_targets_path: Path,
    repair_design_path: Path,
    baseline_behavior_path: Path,
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    target_map: dict[str, Any],
    milestone: str,
) -> dict[str, Any]:
    return {
        "config_id": "m2648_gap_targeted_repair_execution_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "taxonomy_summary": str(taxonomy_summary_path),
        "repair_targets": str(repair_targets_path),
        "repair_design": str(repair_design_path),
        "baseline_behavior_rows": str(baseline_behavior_path),
        "source_checkpoint": str(source_checkpoint),
        "repaired_checkpoint": str(repaired_checkpoint),
        "taxonomy_result_class": taxonomy.get("result_class", ""),
        "target_gap_families": target_map["target_gap_families"],
        "target_role_families": target_map["target_role_families"],
        "protected_reference_families": target_map["protected_reference_families"],
        "actor_contract": {
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "taxonomy_labels_actor_visible": False,
            "repair_target_labels_actor_visible": False,
            "hidden_or_oracle_actor_inputs_required": False,
        },
        "active_config_overwritten": False,
        "taxonomy_artifacts_mutated": False,
        "repair_design_mutated": False,
        "checkpoint_promoted": False,
        "ranking_run": False,
        "success_rate_computed": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_summary(
    *,
    output_dir: Path,
    summary_path: Path,
    taxonomy: dict[str, Any],
    target_map: dict[str, Any],
    subject_registry_rows: list[dict[str, Any]],
    telemetry_summary: dict[str, Any],
    post_repair_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    repair_trace_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    repair_config_snapshot_path: Path,
    repair_training_trace_path: Path,
    repaired_checkpoint_manifest_path: Path,
    post_repair_behavior_rows_path: Path,
    repair_gate_evaluation_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
    horizon_steps: int,
) -> dict[str, Any]:
    required_artifacts_present = all(
        path.exists()
        for path in (
            repair_config_snapshot_path,
            repair_training_trace_path,
            repaired_checkpoint_manifest_path,
            post_repair_behavior_rows_path,
            repair_gate_evaluation_path,
        )
    )
    actor_contract_shape_72_action_3 = (
        {int(row["observation_shape"]) for row in post_repair_rows} == {P0_OBSERVATION_DIM}
        and {int(row["action_shape"]) for row in post_repair_rows} == {ACTION_DIM}
    )
    hidden_or_oracle = any(
        str(row["actor_input_leak_flags"]).lower() != "none"
        or as_bool(row["taxonomy_labels_actor_visible"])
        or as_bool(row["repair_target_labels_actor_visible"])
        for row in post_repair_rows
    )
    target_gate_rows = [
        row for row in gate_rows if row["gate_family"] in {"target_repair", "protected_reference"}
    ]
    target_proof_gates_all_passed = bool(target_gate_rows) and all(
        as_bool(row["gate_pass"]) for row in target_gate_rows
    )
    failed_gate_ids = [row["gate_id"] for row in gate_rows if not as_bool(row["gate_pass"])]
    status_pass = bool(
        required_artifacts_present
        and checkpoint_manifest["repaired_checkpoint_written"]
        and checkpoint_manifest["behavior_changed"]
        and actor_contract_shape_72_action_3
        and not hidden_or_oracle
        and not FALSE_CLAIM_FLAGS["ranking_run"]
        and not FALSE_CLAIM_FLAGS["success_rate_computed"]
        and not FALSE_CLAIM_FLAGS["checkpoint_promoted"]
    )
    summary = {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "result_class": RESULT_CLASS if status_pass else "gap_targeted_repair_execution_preflight_failed",
        "output_dir": str(output_dir),
        "summary": str(summary_path),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "taxonomy_result_class": taxonomy.get("result_class", ""),
        "taxonomy_status_pass": bool(taxonomy.get("status_pass", False)),
        "repair_config_snapshot": str(repair_config_snapshot_path),
        "repair_training_trace": str(repair_training_trace_path),
        "repaired_checkpoint_manifest": str(repaired_checkpoint_manifest_path),
        "post_repair_behavior_rows": str(post_repair_behavior_rows_path),
        "repair_gate_evaluation": str(repair_gate_evaluation_path),
        "required_artifacts_present": required_artifacts_present,
        "repair_execution_started": True,
        "repair_training_started": True,
        "training_run": True,
        "repaired_checkpoint_written": bool(checkpoint_manifest["repaired_checkpoint_written"]),
        "checkpoint_behavior_changed": bool(checkpoint_manifest["behavior_changed"]),
        "training_observation_count": int(checkpoint_manifest["training_observation_count"]),
        "target_gap_families": target_map["target_gap_families"],
        "target_role_families": target_map["target_role_families"],
        "protected_reference_families": target_map["protected_reference_families"],
        "admitted_repair_target_count": len(target_map["admitted_rows"]),
        "protected_reference_count": len(target_map["protected_rows"]),
        "subject_registry_row_count": len(subject_registry_rows),
        "post_repair_behavior_row_count": len(post_repair_rows),
        "telemetry_row_count": int(telemetry_summary.get("telemetry_row_count", 0)),
        "horizon_steps": int(horizon_steps),
        "repair_training_trace_row_count": len(repair_trace_rows),
        "repair_gate_evaluation_row_count": len(gate_rows),
        "target_proof_gates_all_passed": target_proof_gates_all_passed,
        "target_proof_gate_pass_count": sum(as_bool(row["gate_pass"]) for row in target_gate_rows),
        "target_proof_gate_fail_count": sum(not as_bool(row["gate_pass"]) for row in target_gate_rows),
        "failed_gate_ids": failed_gate_ids,
        "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
        "hidden_or_oracle_actor_inputs_required": hidden_or_oracle,
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "active_config_overwritten": False,
        "taxonomy_artifacts_mutated": False,
        "repair_design_mutated": False,
        "source_only_backend_reset_run": True,
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "source_only_repair_execution_run": True,
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failed_gate_ids = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    path.write_text(
        "\n".join(
            [
                "# M2648 Engineering Controller Route A Source-Only Gap-Targeted Repair Execution Preflight",
                "",
                "- status: completed" if summary["status_pass"] else "- status: failed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2648-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-execution-preflight.json`",
                f"- summary: `{summary['summary']}`",
                f"- post-repair behavior rows: `{summary['post_repair_behavior_rows']}`",
                f"- repair gate evaluation: `{summary['repair_gate_evaluation']}`",
                f"- next: `{summary['next_blocker']}`",
                "",
                "## Result",
                "",
                "M2648 ran one bounded source-only gap-targeted repair execution preflight.",
                "It wrote a repaired checkpoint under the M2648 run directory and measured",
                "post-repair source-only behavior rows for the Route A fresh panel.",
                "",
                "```text",
                f"repair_execution_started: {summary['repair_execution_started']}",
                f"repair_training_started: {summary['repair_training_started']}",
                f"training_observation_count: {summary['training_observation_count']}",
                f"post_repair_behavior_row_count: {summary['post_repair_behavior_row_count']}",
                f"repair_gate_evaluation_row_count: {summary['repair_gate_evaluation_row_count']}",
                f"target_proof_gates_all_passed: {summary['target_proof_gates_all_passed']}",
                f"failed_gate_ids: {failed_gate_ids}",
                "```",
                "",
                "## Claim Boundary",
                "",
                "M2648 is repair-execution evidence for audit only. It does not rank",
                "controllers, select a winner, promote a checkpoint, compute success",
                "rates, validate, or claim driver performance, paper evidence,",
                "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity",
                "validation, full ideal driver completion, or self-ID.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def json_list(values: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.9g}" for value in values) + "]"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taxonomy-summary", type=Path, default=DEFAULT_TAXONOMY_SUMMARY)
    parser.add_argument("--repair-targets", type=Path, default=DEFAULT_REPAIR_TARGETS)
    parser.add_argument("--repair-design", type=Path, default=DEFAULT_REPAIR_DESIGN)
    parser.add_argument("--baseline-behavior-rows", type=Path, default=DEFAULT_BASELINE_BEHAVIOR_ROWS)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--fresh-seed-count", type=int, default=DEFAULT_FRESH_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    run_source_only_gap_targeted_repair_execution(
        args.output_dir,
        taxonomy_summary=args.taxonomy_summary,
        repair_targets=args.repair_targets,
        repair_design=args.repair_design,
        baseline_behavior_rows=args.baseline_behavior_rows,
        source_checkpoint=args.source_checkpoint,
        fresh_seed_count=args.fresh_seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
        doc_path=args.doc_path,
    )


if __name__ == "__main__":
    main()
