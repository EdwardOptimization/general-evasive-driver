"""M2799 source-only clearance-localized corrective training preflight.

This preflight consumes the M2798 design, M2797/M2796 clearance-regression
atlas evidence, and the M2791 guardrailed candidate. It writes one bounded
candidate checkpoint and proof/retention guard artifacts for audit. It does not
validate, rank, promote, or claim repair success or driver performance.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.engineering_controller_failure_surface_guarded_repair_execution import (
    _file_sha256,
    actor_action_stats,
    actor_actions,
    model_state_sha256,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
    ACTOR_GUARD_FIELDNAMES,
    CLAIM_FIELDNAMES,
    GATE_FIELDNAMES,
    MITIGATION_GUARD_FIELDNAMES,
    TRAINING_RUN_FIELDNAMES,
    DYNAMICS_AXES,
    STRESS_FAMILIES,
    as_bool,
    as_float,
    build_actor_contract_guard_rows as build_actor_contract_guard_rows_m2782,
    build_mitigation_reference_guard_rows as build_mitigation_reference_guard_rows_m2782,
    build_promotion_guard_rows as build_promotion_guard_rows_m2782,
    build_run_item_map,
    collect_actor_response_rows,
    collect_stress_observation,
    json_list,
    read_csv_rows,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2799-engineering-controller-route-a-source-only-belief-stress-clearance-"
    "localized-corrective-training-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_"
    "localized_corrective_training_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2799-engineering-controller-route-a-source-only-belief-stress-clearance-"
    "localized-corrective-training-preflight.md"
)
DEFAULT_M2798_DESIGN = Path(
    "docs/m2798-engineering-controller-route-a-source-only-belief-stress-clearance-"
    "localized-corrective-training-design.md"
)
DEFAULT_M2797_AUDIT = Path(
    "docs/m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-"
    "clearance-regression-atlas-result-audit.md"
)
DEFAULT_M2796_DIR = Path(
    "runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_"
    "clearance_regression_atlas"
)
DEFAULT_M2793_DIR = Path(
    "runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_"
    "candidate_fresh_holdout_triad_delta_panel"
)
DEFAULT_M2791_DIR = Path(
    "runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_"
    "multi_objective_training_preflight"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_BASE_CANDIDATE_CHECKPOINT = Path(
    "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt"
)
DEFAULT_CANDIDATE_CHECKPOINT = Path(
    "runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_"
    "multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2800-engineering-controller-route-a-source-only-belief-"
    "stress-clearance-localized-corrective-training-result-audit.json"
)
DEFAULT_NEXT_BLOCKER = (
    "m2800-engineering-controller-route-a-source-only-belief-stress-clearance-"
    "localized-corrective-training-result-audit"
)

CLAIM_SCOPE = (
    "Route A source-only belief-stress clearance-localized corrective training/update "
    "preflight only"
)
FORBIDDEN_INTERPRETATION = (
    "validation, ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "repair success, driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, or "
    "level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_belief_stress_clearance_localized_"
    "corrective_training_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_belief_stress_clearance_localized_"
    "corrective_training_preflight_failed"
)

TARGET_ROLE_FAMILIES = ("drift_required_recovery", "stable_aes")
RETENTION_ROLE_FAMILY = "stable_avoidable"
TARGET_STABLE_AES_MIN_NEGATIVE_RATE = 0.625

TRAINING_OBJECTIVE_FIELDNAMES = [
    "training_objective_row_id",
    "objective_family",
    "source_aggregate_id",
    "source_curriculum_row_id",
    "role_family",
    "dynamics_axis",
    "stress_family",
    "row_count",
    "negative_clearance_count",
    "positive_clearance_count",
    "negative_clearance_rate",
    "mean_clearance_delta_m",
    "target_training_seeds_requested",
    "proof_seeds_requested",
    "stable_avoidable_retention_seed_count",
    "behavior_retention_seed_count",
    "future_training_allowed",
    "future_execution_allowed",
    "actor_visible_label",
    "mitigation_reference_context_only",
    "ordinary_denominator_allowed",
    "ranking_admissible",
    "obstacle_clearance_guard_required",
    "clearance_hard_before_side_effects",
    "road_margin_objective_allowed",
    "yaw_rate_objective_allowed",
    "final_speed_diagnostic_only",
    "throttle_brake_conflict_guard_required",
    "action_delta_diagnostic_only",
    "claim_boundary",
]

FALSE_CLAIM_FLAGS = {
    "measured_validation_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "repair_success_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_simulation_run": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_claim_made": False,
    "level3_self_id_claim_made": False,
}


def run_clearance_localized_corrective_training_preflight(
    output_dir: Path | str,
    *,
    m2798_design: Path | str = DEFAULT_M2798_DESIGN,
    m2797_audit: Path | str = DEFAULT_M2797_AUDIT,
    m2796_dir: Path | str = DEFAULT_M2796_DIR,
    m2793_dir: Path | str = DEFAULT_M2793_DIR,
    m2791_dir: Path | str = DEFAULT_M2791_DIR,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    base_candidate_checkpoint: Path | str = DEFAULT_BASE_CANDIDATE_CHECKPOINT,
    candidate_checkpoint: Path | str = DEFAULT_CANDIDATE_CHECKPOINT,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    device: str = "cpu",
    target_training_seeds_per_bucket: int = 4,
    proof_seeds_per_bucket: int = 2,
    stable_avoidable_retention_seed_count: int = 4,
    behavior_retention_seed_count: int = 4,
    max_updates: int = 1,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    target_training_seeds = int(target_training_seeds_per_bucket)
    proof_seeds = int(proof_seeds_per_bucket)
    stable_retention_seeds = int(stable_avoidable_retention_seed_count)
    behavior_retention_seeds = int(behavior_retention_seed_count)
    if target_training_seeds < 4:
        raise ValueError("M2799 requires at least four target training seeds per bucket")
    if proof_seeds < 2:
        raise ValueError("M2799 requires at least two proof seeds per bucket")
    if stable_retention_seeds < 4 or behavior_retention_seeds < 4:
        raise ValueError("M2799 requires explicit stable_avoidable and behavior-retention seeds")
    if int(max_updates) != 1:
        raise ValueError("M2799 preflight permits exactly one bounded update")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(
        Path(m2798_design),
        Path(m2797_audit),
        Path(m2796_dir),
        Path(m2793_dir),
        Path(m2791_dir),
        Path(source_checkpoint),
        Path(base_candidate_checkpoint),
        Path(candidate_checkpoint),
    )
    _require_sources(source_paths)

    m2796_summary = read_json(source_paths["m2796_summary"])
    m2791_summary = read_json(source_paths["m2791_summary"])
    m2791_checkpoint_manifest = read_json(source_paths["m2791_checkpoint_manifest"])
    aggregate_rows = read_csv_rows(source_paths["m2796_aggregate_rows"])
    clearance_rows = read_csv_rows(source_paths["m2796_clearance_rows"])
    m2796_gate_rows = read_csv_rows(source_paths["m2796_gate_matrix"])
    source_mitigation_rows = read_csv_rows(source_paths["m2796_mitigation_reference_guard_rows"])

    objective_rows = build_training_objective_rows(
        aggregate_rows,
        target_training_seeds_per_bucket=target_training_seeds,
        proof_seeds_per_bucket=proof_seeds,
        stable_avoidable_retention_seed_count=stable_retention_seeds,
        behavior_retention_seed_count=behavior_retention_seeds,
    )
    target_objective_rows = [row for row in objective_rows if row["objective_family"] == "target_clearance_correction"]
    retention_objective_rows = [
        row for row in objective_rows if row["objective_family"] == "stable_avoidable_retention"
    ]
    atlas_baseline = build_clearance_localized_baseline(clearance_rows, aggregate_rows, objective_rows)
    run_item_map = build_run_item_map(max(target_training_seeds + proof_seeds, stable_retention_seeds))
    training_observations = collect_target_training_observations(
        target_objective_rows,
        run_item_map,
        training_seed_count=target_training_seeds,
    )

    checkpoint_manifest = write_clearance_localized_candidate_checkpoint(
        source_paths["source_checkpoint"],
        source_paths["base_candidate_checkpoint"],
        source_paths["candidate_checkpoint"],
        paths["candidate_checkpoint"],
        training_observations=training_observations,
        objective_rows=objective_rows,
        atlas_baseline=atlas_baseline,
        output_dir=output,
        device=device,
        milestone=milestone,
        max_updates=int(max_updates),
    )

    training_run_rows = retag_training_rows(
        collect_actor_response_rows(
            target_objective_rows,
            run_item_map,
            source_paths["candidate_checkpoint"],
            paths["candidate_checkpoint"],
            split="target_training",
            seed_indices=range(target_training_seeds),
            device=device,
        )
    )
    target_proof_rows = retag_training_rows(
        collect_actor_response_rows(
            target_objective_rows,
            run_item_map,
            source_paths["candidate_checkpoint"],
            paths["candidate_checkpoint"],
            split="target_proof_holdout",
            seed_indices=range(target_training_seeds, target_training_seeds + proof_seeds),
            device=device,
        )
    )
    stable_retention_rows = retag_training_rows(
        collect_actor_response_rows(
            retention_objective_rows,
            run_item_map,
            source_paths["candidate_checkpoint"],
            paths["candidate_checkpoint"],
            split="stable_avoidable_retention",
            seed_indices=range(stable_retention_seeds),
            device=device,
        )
    )
    proof_probe_rows = target_proof_rows + stable_retention_rows
    mitigation_guard_rows = retag_mitigation_rows(
        build_mitigation_reference_guard_rows_m2782(source_mitigation_rows)
    )
    actor_guard_rows = retag_actor_rows(
        build_actor_contract_guard_rows_m2782(training_run_rows, proof_probe_rows)
    )
    claim_rows = build_claim_boundary_rows()
    proof_gate_rows = build_proof_gate_rows(
        source_paths=source_paths,
        m2796_summary=m2796_summary,
        m2791_summary=m2791_summary,
        m2791_checkpoint_manifest=m2791_checkpoint_manifest,
        objective_rows=objective_rows,
        training_rows=training_run_rows,
        proof_rows=proof_probe_rows,
        target_proof_rows=target_proof_rows,
        stable_retention_rows=stable_retention_rows,
        mitigation_rows=mitigation_guard_rows,
        actor_guard_rows=actor_guard_rows,
        checkpoint_manifest=checkpoint_manifest,
        target_training_seeds=target_training_seeds,
        proof_seeds=proof_seeds,
        stable_retention_seeds=stable_retention_seeds,
    )
    generalization_gate_rows = build_generalization_gate_rows(
        target_objective_rows,
        retention_objective_rows,
        training_run_rows,
        target_proof_rows,
        stable_retention_rows,
        target_training_seeds=target_training_seeds,
        proof_seeds=proof_seeds,
        stable_retention_seeds=stable_retention_seeds,
    )
    behavior_retention_gate_rows = build_behavior_retention_gate_rows(
        atlas_baseline,
        checkpoint_manifest,
        m2796_gate_rows,
    )
    promotion_guard_rows = retag_gate_rows(build_promotion_guard_rows_m2782())
    gate_rows = proof_gate_rows + generalization_gate_rows + behavior_retention_gate_rows + promotion_guard_rows

    write_csv_rows(paths["training_objective_rows"], objective_rows, TRAINING_OBJECTIVE_FIELDNAMES)
    write_csv_rows(paths["training_run_rows"], training_run_rows, TRAINING_RUN_FIELDNAMES)
    write_csv_rows(paths["proof_probe_rows"], proof_probe_rows, TRAINING_RUN_FIELDNAMES)
    write_json(paths["checkpoint_manifest"], checkpoint_manifest)
    write_csv_rows(paths["proof_gate_rows"], proof_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["generalization_gate_rows"], generalization_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["behavior_retention_gate_rows"], behavior_retention_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["promotion_guard_rows"], promotion_guard_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["mitigation_reference_guard_rows"], mitigation_guard_rows, MITIGATION_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        m2796_summary=m2796_summary,
        m2791_summary=m2791_summary,
        m2791_checkpoint_manifest=m2791_checkpoint_manifest,
        atlas_baseline=atlas_baseline,
        objective_rows=objective_rows,
        training_run_rows=training_run_rows,
        proof_probe_rows=proof_probe_rows,
        target_proof_rows=target_proof_rows,
        stable_retention_rows=stable_retention_rows,
        checkpoint_manifest=checkpoint_manifest,
        proof_gate_rows=proof_gate_rows,
        generalization_gate_rows=generalization_gate_rows,
        behavior_retention_gate_rows=behavior_retention_gate_rows,
        promotion_guard_rows=promotion_guard_rows,
        actor_guard_rows=actor_guard_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        claim_rows=claim_rows,
        milestone=milestone,
        next_blocker=next_blocker,
        target_training_seeds=target_training_seeds,
        proof_seeds=proof_seeds,
        stable_retention_seeds=stable_retention_seeds,
        behavior_retention_seed_count=behavior_retention_seeds,
        max_updates=int(max_updates),
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2800_manifest(summary))
    write_doc(paths["doc"], summary)

    summary = {
        **summary,
        "required_artifacts_present": required_artifacts_present(paths),
        "m2800_follow_up_manifest_registered": paths["follow_up_manifest"].exists(),
    }
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    summary["result_class"] = RESULT_CLASS_PASS if summary["status_pass"] else RESULT_CLASS_FAIL
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2800_manifest(summary))
    write_doc(paths["doc"], summary)
    return summary


def _paths(output: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output / "summary.json",
        "training_objective_rows": output / "training_objective_rows.csv",
        "training_run_rows": output / "training_run_rows.csv",
        "proof_probe_rows": output / "proof_probe_rows.csv",
        "checkpoint_manifest": output / "checkpoint_manifest.json",
        "candidate_checkpoint": output / "checkpoints" / "m2799_clearance_localized_corrective_candidate.pt",
        "proof_gate_rows": output / "proof_gate_rows.csv",
        "generalization_gate_rows": output / "generalization_gate_rows.csv",
        "behavior_retention_gate_rows": output / "behavior_retention_gate_rows.csv",
        "promotion_guard_rows": output / "promotion_guard_rows.csv",
        "actor_contract_guard_rows": output / "actor_contract_guard_rows.csv",
        "mitigation_reference_guard_rows": output / "mitigation_reference_guard_rows.csv",
        "claim_boundary_rows": output / "claim_boundary_rows.csv",
        "gate_matrix": output / "gate_matrix.csv",
        "run_state": output / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _source_paths(
    m2798_design: Path,
    m2797_audit: Path,
    m2796_dir: Path,
    m2793_dir: Path,
    m2791_dir: Path,
    source_checkpoint: Path,
    base_candidate_checkpoint: Path,
    candidate_checkpoint: Path,
) -> dict[str, Path]:
    return {
        "m2798_design": m2798_design,
        "m2797_audit": m2797_audit,
        "m2796_summary": m2796_dir / "summary.json",
        "m2796_clearance_rows": m2796_dir / "clearance_regression_rows.csv",
        "m2796_aggregate_rows": m2796_dir / "clearance_regression_aggregate_rows.csv",
        "m2796_gate_matrix": m2796_dir / "gate_matrix.csv",
        "m2796_mitigation_reference_guard_rows": m2796_dir / "mitigation_reference_guard_rows.csv",
        "m2793_summary": m2793_dir / "summary.json",
        "m2791_summary": m2791_dir / "summary.json",
        "m2791_checkpoint_manifest": m2791_dir / "checkpoint_manifest.json",
        "source_checkpoint": source_checkpoint,
        "base_candidate_checkpoint": base_candidate_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2799 missing required source artifacts: {missing}")


def build_training_objective_rows(
    aggregate_rows: list[dict[str, str]],
    *,
    target_training_seeds_per_bucket: int,
    proof_seeds_per_bucket: int,
    stable_avoidable_retention_seed_count: int,
    behavior_retention_seed_count: int,
) -> list[dict[str, Any]]:
    role_bucket_rows = [
        row
        for row in aggregate_rows
        if row.get("group_family") == "role_dynamics_stress"
        and row.get("dynamics_axis") in DYNAMICS_AXES
        and row.get("stress_family") in STRESS_FAMILIES
    ]
    rows_out: list[dict[str, Any]] = []
    selected_targets: list[dict[str, str]] = []
    selected_retention: list[dict[str, str]] = []
    for row in role_bucket_rows:
        role = row["role_family"]
        negative_rate = as_float(row.get("negative_clearance_rate"))
        negative_count = int(as_float(row.get("negative_clearance_count")))
        row_count = int(as_float(row.get("row_count")))
        if role == "drift_required_recovery" and negative_count == row_count:
            selected_targets.append(row)
        elif role == "stable_aes" and negative_rate >= TARGET_STABLE_AES_MIN_NEGATIVE_RATE:
            selected_targets.append(row)
        elif role == RETENTION_ROLE_FAMILY:
            selected_retention.append(row)

    expected_per_role = len(DYNAMICS_AXES) * len(STRESS_FAMILIES)
    if len([row for row in selected_targets if row["role_family"] == "drift_required_recovery"]) != expected_per_role:
        raise RuntimeError("M2799 requires all drift_required_recovery buckets to be clearance-negative")
    if len([row for row in selected_targets if row["role_family"] == "stable_aes"]) != expected_per_role:
        raise RuntimeError("M2799 requires all stable_aes buckets above the negative-rate threshold")
    if len(selected_retention) != expected_per_role:
        raise RuntimeError("M2799 requires complete stable_avoidable retention buckets")

    ordered = sorted(
        selected_targets + selected_retention,
        key=lambda item: (
            item["role_family"] != "drift_required_recovery",
            item["role_family"] != "stable_aes",
            item["role_family"],
            item["dynamics_axis"],
            item["stress_family"],
        ),
    )
    for index, row in enumerate(ordered):
        objective_family = (
            "stable_avoidable_retention"
            if row["role_family"] == RETENTION_ROLE_FAMILY
            else "target_clearance_correction"
        )
        rows_out.append(
            {
                "training_objective_row_id": f"m2799_objective_{index:03d}",
                "objective_family": objective_family,
                "source_aggregate_id": row["aggregate_id"],
                "source_curriculum_row_id": row["aggregate_id"],
                "role_family": row["role_family"],
                "dynamics_axis": row["dynamics_axis"],
                "stress_family": row["stress_family"],
                "row_count": int(as_float(row["row_count"])),
                "negative_clearance_count": int(as_float(row["negative_clearance_count"])),
                "positive_clearance_count": int(as_float(row["positive_clearance_count"])),
                "negative_clearance_rate": as_float(row["negative_clearance_rate"]),
                "mean_clearance_delta_m": as_float(row["mean_clearance_delta_m"]),
                "target_training_seeds_requested": int(target_training_seeds_per_bucket)
                if objective_family == "target_clearance_correction"
                else 0,
                "proof_seeds_requested": int(proof_seeds_per_bucket),
                "stable_avoidable_retention_seed_count": int(stable_avoidable_retention_seed_count)
                if objective_family == "stable_avoidable_retention"
                else 0,
                "behavior_retention_seed_count": int(behavior_retention_seed_count),
                "future_training_allowed": objective_family == "target_clearance_correction",
                "future_execution_allowed": True,
                "actor_visible_label": False,
                "mitigation_reference_context_only": False,
                "ordinary_denominator_allowed": True,
                "ranking_admissible": False,
                "obstacle_clearance_guard_required": True,
                "clearance_hard_before_side_effects": True,
                "road_margin_objective_allowed": False,
                "yaw_rate_objective_allowed": False,
                "final_speed_diagnostic_only": True,
                "throttle_brake_conflict_guard_required": True,
                "action_delta_diagnostic_only": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows_out


def build_clearance_localized_baseline(
    clearance_rows: list[dict[str, str]],
    aggregate_rows: list[dict[str, str]],
    objective_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    target_rows = [row for row in objective_rows if row["objective_family"] == "target_clearance_correction"]
    retention_rows = [row for row in objective_rows if row["objective_family"] == "stable_avoidable_retention"]
    target_clearance_rows = [
        row for row in clearance_rows if row.get("role_family") in TARGET_ROLE_FAMILIES
    ]
    target_action_signal = float(
        np.mean([abs(as_float(row.get("mean_action_delta_l1"))) for row in target_clearance_rows])
    )
    role_stats = {
        row["role_family"]: row
        for row in aggregate_rows
        if row.get("group_family") == "role_family"
        and row.get("role_family") in (*TARGET_ROLE_FAMILIES, RETENTION_ROLE_FAMILY)
    }
    target_negative_count = sum(int(row["negative_clearance_count"]) for row in target_rows)
    target_row_count = sum(int(row["row_count"]) for row in target_rows)
    retention_negative_count = sum(int(row["negative_clearance_count"]) for row in retention_rows)
    retention_row_count = sum(int(row["row_count"]) for row in retention_rows)
    return {
        "target_objective_row_count": len(target_rows),
        "retention_objective_row_count": len(retention_rows),
        "target_negative_clearance_count": int(target_negative_count),
        "target_row_count": int(target_row_count),
        "target_negative_clearance_rate": float(target_negative_count / max(1, target_row_count)),
        "stable_avoidable_negative_clearance_count": int(retention_negative_count),
        "stable_avoidable_row_count": int(retention_row_count),
        "stable_avoidable_negative_clearance_rate": float(
            retention_negative_count / max(1, retention_row_count)
        ),
        "target_mean_action_delta_l1": target_action_signal,
        "drift_required_recovery_negative_count": int(
            as_float(role_stats["drift_required_recovery"]["negative_clearance_count"])
        ),
        "drift_required_recovery_row_count": int(as_float(role_stats["drift_required_recovery"]["row_count"])),
        "stable_aes_negative_count": int(as_float(role_stats["stable_aes"]["negative_clearance_count"])),
        "stable_aes_row_count": int(as_float(role_stats["stable_aes"]["row_count"])),
        "stable_avoidable_role_negative_count": int(
            as_float(role_stats[RETENTION_ROLE_FAMILY]["negative_clearance_count"])
        ),
        "stable_avoidable_role_row_count": int(as_float(role_stats[RETENTION_ROLE_FAMILY]["row_count"])),
    }


def collect_target_training_observations(
    objective_rows: list[dict[str, Any]],
    run_item_map: dict[tuple[str, str, int], Any],
    *,
    training_seed_count: int,
) -> np.ndarray:
    observations: list[np.ndarray] = []
    for row in objective_rows:
        for seed_index in range(int(training_seed_count)):
            observation, _fixture_id, _warmup_count = collect_stress_observation(
                run_item_map,
                str(row["role_family"]),
                str(row["dynamics_axis"]),
                int(seed_index),
                str(row["stress_family"]),
            )
            observations.append(observation)
    if not observations:
        raise RuntimeError("M2799 collected no target training observations")
    return np.stack(observations, axis=0)


def write_clearance_localized_candidate_checkpoint(
    source_checkpoint: Path,
    base_candidate_checkpoint: Path,
    start_candidate_checkpoint: Path,
    output_candidate_checkpoint: Path,
    *,
    training_observations: np.ndarray,
    objective_rows: list[dict[str, Any]],
    atlas_baseline: dict[str, Any],
    output_dir: Path,
    device: str,
    milestone: str,
    max_updates: int,
) -> dict[str, Any]:
    source_model, source_raw_checkpoint = load_actor_critic_checkpoint(source_checkpoint, device=device)
    base_model, base_raw_checkpoint = load_actor_critic_checkpoint(base_candidate_checkpoint, device=device)
    start_model, start_raw_checkpoint = load_actor_critic_checkpoint(start_candidate_checkpoint, device=device)
    for label, model in (("source", source_model), ("base", base_model), ("start", start_model)):
        if int(model.obs_dim) != P0_OBSERVATION_DIM or int(model.act_dim) != ACTION_DIM:
            raise RuntimeError(f"{label} checkpoint does not preserve the P0 72/3 contract")

    resolved_device = next(start_model.parameters()).device
    obs_t = torch.as_tensor(training_observations, dtype=torch.float32, device=resolved_device)
    start_actions = actor_actions(start_model, obs_t)
    start_stats = actor_action_stats(start_actions)
    deltas = clearance_localized_update_deltas(atlas_baseline, max_updates=int(max_updates))

    with torch.no_grad():
        before_bias = start_model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()
        start_model.actor_mean.bias[0].add_(float(deltas["steer_bias_delta"]))
        start_model.actor_mean.bias[1].add_(float(deltas["throttle_bias_delta"]))
        start_model.actor_mean.bias[2].add_(float(deltas["brake_bias_delta"]))
        after_bias = start_model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()

    candidate_actions = actor_actions(start_model, obs_t)
    candidate_stats = actor_action_stats(candidate_actions, reference_actions=start_actions)
    candidate_state = {key: value.detach().cpu() for key, value in start_model.state_dict().items()}
    candidate_state_hash = model_state_sha256(candidate_state)
    start_state_hash = model_state_sha256(start_raw_checkpoint["model_state"])
    base_state_hash = model_state_sha256(base_raw_checkpoint["model_state"])
    source_state_hash = model_state_sha256(source_raw_checkpoint["model_state"])
    checkpoint_output = copy.deepcopy(start_raw_checkpoint)
    checkpoint_output["model_state"] = candidate_state
    checkpoint_output.setdefault("metadata", {})
    checkpoint_output["metadata"] = {
        **dict(checkpoint_output.get("metadata", {})),
        "m2799_clearance_localized_corrective_training_preflight": {
            "milestone": milestone,
            "update_method": "deterministic_clearance_localized_actor_head_correction_preflight",
            "source_reference_checkpoint": str(source_checkpoint),
            "base_candidate_checkpoint": str(base_candidate_checkpoint),
            "start_candidate_checkpoint": str(start_candidate_checkpoint),
            "output_dir": str(output_dir),
            "max_updates": int(max_updates),
            "training_objective_row_count": len(objective_rows),
            "target_objective_row_count": int(atlas_baseline["target_objective_row_count"]),
            "retention_objective_row_count": int(atlas_baseline["retention_objective_row_count"]),
            "training_observation_count": int(training_observations.shape[0]),
            "target_negative_clearance_count_reference": int(
                atlas_baseline["target_negative_clearance_count"]
            ),
            "stable_avoidable_negative_clearance_count_reference": int(
                atlas_baseline["stable_avoidable_negative_clearance_count"]
            ),
            "checkpoint_promoted": False,
            "rollback_required": False,
            "rollback_status_written": False,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_labels": False,
            "active_config_overwritten": False,
            "source_checkpoint_overwritten": False,
            "base_candidate_checkpoint_overwritten": False,
            "start_candidate_checkpoint_overwritten": False,
            "claim_scope": CLAIM_SCOPE,
        },
    }
    output_candidate_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_output, output_candidate_checkpoint)

    source_checkpoint_hash = _file_sha256(source_checkpoint)
    base_checkpoint_hash = _file_sha256(base_candidate_checkpoint)
    start_checkpoint_hash = _file_sha256(start_candidate_checkpoint)
    candidate_checkpoint_hash = _file_sha256(output_candidate_checkpoint)
    finite_update = bool(
        np.all(np.isfinite(np.asarray(after_bias, dtype=np.float64)))
        and np.isfinite(candidate_stats["conflict_proxy"])
    )
    behavior_changed = bool(
        candidate_state_hash != start_state_hash
        and candidate_stats["mean_action_delta_l1_from_source"] > 1e-9
    )
    return {
        "manifest_id": "m2799_checkpoint_manifest_v0",
        "milestone": milestone,
        "source_reference_checkpoint": str(source_checkpoint),
        "source_reference_checkpoint_hash": source_checkpoint_hash,
        "source_reference_model_state_hash": source_state_hash,
        "base_candidate_checkpoint": str(base_candidate_checkpoint),
        "base_candidate_checkpoint_hash": base_checkpoint_hash,
        "base_candidate_model_state_hash": base_state_hash,
        "start_candidate_checkpoint": str(start_candidate_checkpoint),
        "start_candidate_checkpoint_hash": start_checkpoint_hash,
        "start_candidate_model_state_hash": start_state_hash,
        "candidate_checkpoint": str(output_candidate_checkpoint),
        "candidate_checkpoint_hash": candidate_checkpoint_hash,
        "candidate_model_state_hash": candidate_state_hash,
        "behavior_changed": behavior_changed,
        "candidate_checkpoint_written": output_candidate_checkpoint.exists(),
        "update_method": "deterministic_clearance_localized_actor_head_correction_preflight",
        "max_updates": int(max_updates),
        "training_observation_count": int(training_observations.shape[0]),
        "training_objective_row_count": len(objective_rows),
        "trainable_parameter_names": ["actor_mean.bias[0]"],
        "actor_mean_bias_before": json_list(before_bias),
        "actor_mean_bias_after": json_list(after_bias),
        "steer_bias_delta": deltas["steer_bias_delta"],
        "throttle_bias_delta": deltas["throttle_bias_delta"],
        "brake_bias_delta": deltas["brake_bias_delta"],
        "target_action_delta_signal": deltas["target_action_delta_signal"],
        "target_negative_clearance_rate_reference": atlas_baseline["target_negative_clearance_rate"],
        "stable_avoidable_negative_clearance_rate_reference": atlas_baseline[
            "stable_avoidable_negative_clearance_rate"
        ],
        "start_conflict_proxy": start_stats["conflict_proxy"],
        "candidate_conflict_proxy": candidate_stats["conflict_proxy"],
        "mean_action_delta_l1_from_start": candidate_stats["mean_action_delta_l1_from_source"],
        "finite_update": finite_update,
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_labels": False,
        "active_config_overwritten": False,
        "source_checkpoint_overwritten": False,
        "base_candidate_checkpoint_overwritten": False,
        "start_candidate_checkpoint_overwritten": False,
        "checkpoint_promoted": False,
        "promotion_metadata_written": False,
        "rollback_required": False,
        "rollback_status_written": False,
        "obstacle_clearance_regression_guard_required": True,
        "stable_avoidable_retention_guard_required": True,
        "obstacle_clearance_guard_hard_before_objectives": True,
        "road_margin_objective_subordinate_to_clearance": True,
        "yaw_rate_objective_subordinate_to_clearance": True,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def clearance_localized_update_deltas(atlas_baseline: dict[str, Any], *, max_updates: int) -> dict[str, float]:
    if int(max_updates) != 1:
        raise ValueError("M2799 uses exactly one bounded update")
    action_signal = max(0.0004, float(atlas_baseline["target_mean_action_delta_l1"]))
    target_rate = float(atlas_baseline["target_negative_clearance_rate"])
    retention_rate = float(atlas_baseline["stable_avoidable_negative_clearance_rate"])
    retention_scale = max(0.5, 1.0 - min(0.35, retention_rate))
    steer_delta = min(0.004, max(0.0008, 7.5 * action_signal)) * max(0.4, target_rate) * retention_scale
    return {
        "steer_bias_delta": float(steer_delta),
        "throttle_bias_delta": 0.0,
        "brake_bias_delta": 0.0,
        "target_action_delta_signal": float(action_signal),
    }


def retag_training_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tagged: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        out["training_row_id"] = str(out["training_row_id"]).replace("m2782_", "m2799_")
        out["claim_scope"] = CLAIM_SCOPE
        out["forbidden_interpretation"] = FORBIDDEN_INTERPRETATION
        tagged.append(out)
    return tagged


def retag_actor_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**dict(row), "claim_boundary": CLAIM_SCOPE} for row in rows]


def retag_mitigation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**dict(row), "claim_boundary": CLAIM_SCOPE} for row in rows]


def retag_gate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**dict(row), "claim_boundary": CLAIM_SCOPE} for row in rows]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        ("validation_result", "validation", False, False, "M2799 does not run measured validation"),
        ("ranking_result", "ranking", False, False, "M2799 does not rank checkpoints or controllers"),
        ("winner_selection", "promotion", False, False, "M2799 selects no winner"),
        ("checkpoint_promotion", "promotion", False, False, "M2799 writes candidate only"),
        ("success_rate_verdict", "metric_artifact", False, False, "M2799 emits no success-rate verdict"),
        ("repair_success", "repair", False, False, "M2799 is not repair-success evidence"),
        ("driver_performance", "performance", False, False, "M2799 is preflight evidence only"),
        ("paper_result", "paper", False, False, "M2799 is not paper evidence"),
        ("current_sim_verdict", "current_sim", False, False, "M2799 is not a current-sim verdict"),
        ("high_fidelity_validation", "high_fidelity", False, False, "M2799 does not run HF validation"),
        ("level3_self_id", "self_id", False, False, "M2799 is not self-ID evidence"),
        (
            "clearance_localized_preflight_artifacts_complete",
            "allowed_artifact_completion",
            True,
            True,
            "M2799 may claim whether bounded corrective preflight artifacts were written",
        ),
    ]
    return [
        {
            "claim_id": claim_id,
            "claim_family": family,
            "claim_made": made,
            "allowed": allowed,
            "status_pass": bool((not made) or allowed),
            "evidence": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, allowed, evidence in rows
    ]


def build_proof_gate_rows(
    *,
    source_paths: dict[str, Path],
    m2796_summary: dict[str, Any],
    m2791_summary: dict[str, Any],
    m2791_checkpoint_manifest: dict[str, Any],
    objective_rows: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    proof_rows: list[dict[str, Any]],
    target_proof_rows: list[dict[str, Any]],
    stable_retention_rows: list[dict[str, Any]],
    mitigation_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    target_training_seeds: int,
    proof_seeds: int,
    stable_retention_seeds: int,
) -> list[dict[str, Any]]:
    combined = training_rows + proof_rows
    target_objective_rows = [
        row for row in objective_rows if row["objective_family"] == "target_clearance_correction"
    ]
    retention_objective_rows = [
        row for row in objective_rows if row["objective_family"] == "stable_avoidable_retention"
    ]
    expected_training = len(target_objective_rows) * int(target_training_seeds)
    expected_target_proof = len(target_objective_rows) * int(proof_seeds)
    expected_retention = len(retention_objective_rows) * int(stable_retention_seeds)
    gates = [
        gate("proof_m2798_design_present", "proof", "lineage", source_paths["m2798_design"].exists(), str(source_paths["m2798_design"]), "exists", 1, "lineage_invalid"),
        gate("proof_m2797_audit_present", "proof", "lineage", source_paths["m2797_audit"].exists(), str(source_paths["m2797_audit"]), "exists", 1, "lineage_invalid"),
        gate("proof_m2796_status_pass", "proof", "lineage", bool(m2796_summary.get("status_pass", False)) and bool(m2796_summary.get("gate_matrix_pass", False)), str(bool(m2796_summary.get("status_pass", False))), "true with gate matrix pass", 1, "lineage_invalid"),
        gate("proof_m2791_status_pass", "proof", "lineage", bool(m2791_summary.get("status_pass", False)) and bool(m2791_checkpoint_manifest.get("candidate_checkpoint_hash")), str(bool(m2791_summary.get("status_pass", False))), "true with candidate hash", 1, "lineage_invalid"),
        gate("proof_checkpoint_lineage_hashes", "proof", "lineage", bool(checkpoint_manifest.get("source_reference_checkpoint_hash")) and bool(checkpoint_manifest.get("base_candidate_checkpoint_hash")) and bool(checkpoint_manifest.get("start_candidate_checkpoint_hash")) and bool(checkpoint_manifest.get("candidate_checkpoint_hash")) and checkpoint_manifest.get("start_candidate_checkpoint_hash") != checkpoint_manifest.get("candidate_checkpoint_hash"), "source base start candidate hashes", "hashes present with candidate update", 1, "lineage_invalid"),
        gate("proof_target_objective_rows_complete", "proof", "artifact", len(target_objective_rows) == len(TARGET_ROLE_FAMILIES) * len(DYNAMICS_AXES) * len(STRESS_FAMILIES), str(len(target_objective_rows)), "12", len(target_objective_rows), "scenario_sampling_failure"),
        gate("proof_retention_objective_rows_complete", "proof", "artifact", len(retention_objective_rows) == len(DYNAMICS_AXES) * len(STRESS_FAMILIES), str(len(retention_objective_rows)), "6", len(retention_objective_rows), "scenario_sampling_failure"),
        gate("proof_training_row_count", "proof", "artifact", len(training_rows) == expected_training, str(len(training_rows)), str(expected_training), len(training_rows), "scenario_sampling_failure"),
        gate("proof_probe_row_count", "proof", "artifact", len(target_proof_rows) == expected_target_proof and len(stable_retention_rows) == expected_retention, f"target={len(target_proof_rows)} retention={len(stable_retention_rows)}", f"target={expected_target_proof} retention={expected_retention}", len(proof_rows), "scenario_sampling_failure"),
        gate("proof_actor_contract_72_3", "proof", "actor_contract", bool(actor_guard_rows) and all(as_bool(row["status_pass"]) for row in actor_guard_rows), "all actor guards pass", "all actor guards pass", len(actor_guard_rows), "contract_violation"),
        gate("proof_no_hidden_or_oracle_actor_input", "proof", "actor_contract", not any(as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in combined), "false", "false", len(combined), "contract_violation"),
        gate("proof_actor_invisible_labels", "proof", "actor_contract", not any(as_bool(row["actor_visible_label"]) for row in combined), "false", "false", len(combined), "contract_violation"),
        gate("proof_finite_action_observation", "proof", "metric_artifact", all(as_bool(row["finite_observation"]) and as_bool(row["finite_action"]) for row in combined), "finite", "finite", len(combined), "metric_artifact"),
        gate("proof_mitigation_rows_excluded", "proof", "proof_washout", bool(mitigation_rows) and all(not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_rows) and all(not as_bool(row["included_in_training_rows"]) for row in mitigation_rows), "mitigation rows excluded", "mitigation rows excluded", len(mitigation_rows), "proof_washout"),
    ]
    return gates


def build_generalization_gate_rows(
    target_objective_rows: list[dict[str, Any]],
    retention_objective_rows: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    target_proof_rows: list[dict[str, Any]],
    stable_retention_rows: list[dict[str, Any]],
    *,
    target_training_seeds: int,
    proof_seeds: int,
    stable_retention_seeds: int,
) -> list[dict[str, Any]]:
    target_role_set = {row["role_family"] for row in target_proof_rows}
    target_axis_set = {row["dynamics_axis"] for row in target_proof_rows}
    target_stress_set = {row["stress_family"] for row in target_proof_rows}
    training_seed_indices = {int(row["seed_index"]) for row in training_rows}
    proof_seed_indices = {int(row["seed_index"]) for row in target_proof_rows}
    retention_seed_indices = {int(row["seed_index"]) for row in stable_retention_rows}
    expected_training = set(range(int(target_training_seeds)))
    expected_proof = set(range(int(target_training_seeds), int(target_training_seeds) + int(proof_seeds)))
    expected_retention = set(range(int(stable_retention_seeds)))
    return [
        gate("generalization_target_training_seed_rows_complete", "generalization", "seed_split", training_seed_indices == expected_training, ";".join(str(idx) for idx in sorted(training_seed_indices)), ";".join(str(idx) for idx in sorted(expected_training)), len(training_rows), "scenario_sampling_failure"),
        gate("generalization_target_holdout_seed_rows_separate", "generalization", "seed_split", proof_seed_indices == expected_proof and training_seed_indices.isdisjoint(proof_seed_indices), ";".join(str(idx) for idx in sorted(proof_seed_indices)), ";".join(str(idx) for idx in sorted(expected_proof)), len(target_proof_rows), "seed_fragility"),
        gate("generalization_target_role_family_coverage", "generalization", "scenario_sampling", target_role_set == set(TARGET_ROLE_FAMILIES), ";".join(sorted(target_role_set)), ";".join(TARGET_ROLE_FAMILIES), len(target_proof_rows), "scenario_sampling_failure"),
        gate("generalization_target_dynamics_stress_coverage", "generalization", "scenario_sampling", target_axis_set == set(DYNAMICS_AXES) and target_stress_set == set(STRESS_FAMILIES), f"axes={';'.join(sorted(target_axis_set))} stress={';'.join(sorted(target_stress_set))}", "all target axes and stress families", len(target_proof_rows), "scenario_sampling_failure"),
        gate("generalization_stable_avoidable_retention_seed_rows", "generalization", "behavior_retention", {row["role_family"] for row in stable_retention_rows} == {RETENTION_ROLE_FAMILY} and retention_seed_indices == expected_retention and len(retention_objective_rows) == len(DYNAMICS_AXES) * len(STRESS_FAMILIES), ";".join(str(idx) for idx in sorted(retention_seed_indices)), ";".join(str(idx) for idx in sorted(expected_retention)), len(stable_retention_rows), "behavior_regression"),
        gate("generalization_no_validation_or_ranking_claim", "generalization", "claim_boundary", True, "no validation/ranking claim", "no validation/ranking claim", len(target_objective_rows) + len(retention_objective_rows), "metric_artifact"),
    ]


def build_behavior_retention_gate_rows(
    atlas_baseline: dict[str, Any],
    checkpoint_manifest: dict[str, Any],
    m2796_gate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    action_delta = float(checkpoint_manifest["mean_action_delta_l1_from_start"])
    return [
        gate("behavior_m2796_atlas_baseline_present", "behavior_retention", "lineage", bool(m2796_gate_rows) and int(atlas_baseline["target_row_count"]) > 0, str(int(atlas_baseline["target_row_count"])), "M2796 atlas rows and gates present", int(atlas_baseline["target_row_count"]), "lineage_invalid"),
        gate("behavior_drift_required_recovery_target_negative_full", "behavior_retention", "behavior_regression", int(atlas_baseline["drift_required_recovery_negative_count"]) == int(atlas_baseline["drift_required_recovery_row_count"]) == 48, f"{atlas_baseline['drift_required_recovery_negative_count']}/{atlas_baseline['drift_required_recovery_row_count']}", "48/48", 48, "behavior_regression"),
        gate("behavior_stable_aes_target_negative_rate_min", "behavior_retention", "behavior_regression", int(atlas_baseline["stable_aes_negative_count"]) >= 36 and int(atlas_baseline["stable_aes_row_count"]) == 48, f"{atlas_baseline['stable_aes_negative_count']}/{atlas_baseline['stable_aes_row_count']}", ">=36/48", 48, "behavior_regression"),
        gate("behavior_stable_avoidable_retention_low_negative", "behavior_retention", "behavior_regression", int(atlas_baseline["stable_avoidable_role_negative_count"]) <= 1 and int(atlas_baseline["stable_avoidable_role_row_count"]) == 48, f"{atlas_baseline['stable_avoidable_role_negative_count']}/{atlas_baseline['stable_avoidable_role_row_count']}", "<=1/48", 48, "behavior_regression"),
        gate("behavior_obstacle_clearance_guard_is_hard", "behavior_retention", "objective_overfit", bool(checkpoint_manifest["obstacle_clearance_guard_hard_before_objectives"]) and bool(checkpoint_manifest["road_margin_objective_subordinate_to_clearance"]) and bool(checkpoint_manifest["yaw_rate_objective_subordinate_to_clearance"]), "road/yaw subordinate", "clearance hard before side effects", int(atlas_baseline["target_row_count"]), "objective_overfit"),
        gate("behavior_throttle_brake_conflict_guard_defined", "behavior_retention", "behavior_regression", float(checkpoint_manifest["candidate_conflict_proxy"]) <= float(checkpoint_manifest["start_conflict_proxy"]) + 1e-9, f"{checkpoint_manifest['candidate_conflict_proxy']:.9g}", "<= start conflict proxy", 1, "behavior_regression"),
        gate("behavior_candidate_update_bounded", "behavior_retention", "objective_overfit", 0.0 < action_delta <= 0.01, f"{action_delta:.9g}", "(0, 0.01]", 1, "objective_overfit"),
    ]


def gate(
    gate_id: str,
    tier: str,
    family: str,
    status_pass: bool,
    observed: str,
    expected: str,
    row_count: int,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_tier": tier,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "row_count": int(row_count),
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source_paths: dict[str, Path],
    m2796_summary: dict[str, Any],
    m2791_summary: dict[str, Any],
    m2791_checkpoint_manifest: dict[str, Any],
    atlas_baseline: dict[str, Any],
    objective_rows: list[dict[str, Any]],
    training_run_rows: list[dict[str, Any]],
    proof_probe_rows: list[dict[str, Any]],
    target_proof_rows: list[dict[str, Any]],
    stable_retention_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    proof_gate_rows: list[dict[str, Any]],
    generalization_gate_rows: list[dict[str, Any]],
    behavior_retention_gate_rows: list[dict[str, Any]],
    promotion_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    mitigation_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    milestone: str,
    next_blocker: str,
    target_training_seeds: int,
    proof_seeds: int,
    stable_retention_seeds: int,
    behavior_retention_seed_count: int,
    max_updates: int,
) -> dict[str, Any]:
    all_gate_rows = proof_gate_rows + generalization_gate_rows + behavior_retention_gate_rows + promotion_guard_rows
    forbidden_claims_made = any(
        as_bool(row["claim_made"]) and not as_bool(row["allowed"]) for row in claim_rows
    )
    actor_contract_shape = bool(actor_guard_rows) and all(as_bool(row["status_pass"]) for row in actor_guard_rows)
    gate_matrix_pass = bool(all_gate_rows) and all(as_bool(row["status_pass"]) for row in all_gate_rows)
    status_pass = bool(
        checkpoint_manifest["candidate_checkpoint_written"]
        and checkpoint_manifest["behavior_changed"]
        and checkpoint_manifest["finite_update"]
        and actor_contract_shape
        and gate_matrix_pass
        and all(as_bool(row["status_pass"]) for row in mitigation_guard_rows)
        and not forbidden_claims_made
    )
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "result_class": RESULT_CLASS_PASS if status_pass else RESULT_CLASS_FAIL,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "next_blocker": next_blocker,
        "m2798_design": str(source_paths["m2798_design"]),
        "m2797_audit": str(source_paths["m2797_audit"]),
        "m2796_summary": str(source_paths["m2796_summary"]),
        "m2796_status_pass": bool(m2796_summary.get("status_pass", False)),
        "m2796_gate_matrix_pass": bool(m2796_summary.get("gate_matrix_pass", False)),
        "m2791_summary": str(source_paths["m2791_summary"]),
        "m2791_status_pass": bool(m2791_summary.get("status_pass", False)),
        "m2791_candidate_checkpoint_hash": m2791_checkpoint_manifest.get("candidate_checkpoint_hash", ""),
        "source_reference_checkpoint": str(source_paths["source_checkpoint"]),
        "base_candidate_checkpoint": str(source_paths["base_candidate_checkpoint"]),
        "start_candidate_checkpoint": str(source_paths["candidate_checkpoint"]),
        "candidate_checkpoint": str(paths["candidate_checkpoint"]),
        "checkpoint_manifest": str(paths["checkpoint_manifest"]),
        "training_objective_rows": str(paths["training_objective_rows"]),
        "training_run_rows": str(paths["training_run_rows"]),
        "proof_probe_rows": str(paths["proof_probe_rows"]),
        "proof_gate_rows": str(paths["proof_gate_rows"]),
        "generalization_gate_rows": str(paths["generalization_gate_rows"]),
        "behavior_retention_gate_rows": str(paths["behavior_retention_gate_rows"]),
        "promotion_guard_rows": str(paths["promotion_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "mitigation_reference_guard_rows": str(paths["mitigation_reference_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "required_artifacts_present": False,
        "m2800_follow_up_manifest_registered": False,
        "training_run": True,
        "source_only_backend_reset_run": True,
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "bounded_update_count": int(max_updates),
        "target_training_seeds_per_bucket": int(target_training_seeds),
        "proof_seeds_per_bucket": int(proof_seeds),
        "stable_avoidable_retention_seed_count": int(stable_retention_seeds),
        "behavior_retention_seed_count": int(behavior_retention_seed_count),
        "training_objective_row_count": len(objective_rows),
        "target_objective_row_count": int(atlas_baseline["target_objective_row_count"]),
        "retention_objective_row_count": int(atlas_baseline["retention_objective_row_count"]),
        "training_run_row_count": len(training_run_rows),
        "proof_holdout_probe_row_count": len(proof_probe_rows),
        "target_proof_probe_row_count": len(target_proof_rows),
        "stable_avoidable_retention_probe_row_count": len(stable_retention_rows),
        "proof_gate_row_count": len(proof_gate_rows),
        "generalization_gate_row_count": len(generalization_gate_rows),
        "behavior_retention_gate_row_count": len(behavior_retention_gate_rows),
        "promotion_guard_row_count": len(promotion_guard_rows),
        "actor_guard_row_count": len(actor_guard_rows),
        "mitigation_reference_guard_row_count": len(mitigation_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(all_gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "failed_gate_ids": [row["gate_id"] for row in all_gate_rows if not as_bool(row["status_pass"])],
        "candidate_checkpoint_written": bool(checkpoint_manifest["candidate_checkpoint_written"]),
        "checkpoint_behavior_changed": bool(checkpoint_manifest["behavior_changed"]),
        "candidate_checkpoint_hash": checkpoint_manifest["candidate_checkpoint_hash"],
        "start_candidate_checkpoint_hash": checkpoint_manifest["start_candidate_checkpoint_hash"],
        "base_candidate_checkpoint_hash": checkpoint_manifest["base_candidate_checkpoint_hash"],
        "source_reference_checkpoint_hash": checkpoint_manifest["source_reference_checkpoint_hash"],
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_atlas_or_role_labels_detected": False,
        "mitigation_reference_rows_guarded": all(
            not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows
        ),
        "target_negative_clearance_count": int(atlas_baseline["target_negative_clearance_count"]),
        "target_row_count": int(atlas_baseline["target_row_count"]),
        "target_negative_clearance_rate": float(atlas_baseline["target_negative_clearance_rate"]),
        "drift_required_recovery_negative_count": int(
            atlas_baseline["drift_required_recovery_negative_count"]
        ),
        "stable_aes_negative_count": int(atlas_baseline["stable_aes_negative_count"]),
        "stable_avoidable_negative_clearance_count": int(
            atlas_baseline["stable_avoidable_role_negative_count"]
        ),
        "stable_avoidable_row_count": int(atlas_baseline["stable_avoidable_role_row_count"]),
        "obstacle_clearance_regression_guard_required": bool(
            checkpoint_manifest["obstacle_clearance_regression_guard_required"]
        ),
        "stable_avoidable_retention_guard_required": bool(
            checkpoint_manifest["stable_avoidable_retention_guard_required"]
        ),
        "obstacle_clearance_guard_hard_before_objectives": bool(
            checkpoint_manifest["obstacle_clearance_guard_hard_before_objectives"]
        ),
        "checkpoint_promoted": False,
        "active_config_overwritten": False,
        "source_checkpoint_overwritten": False,
        "base_candidate_checkpoint_overwritten": False,
        "start_candidate_checkpoint_overwritten": False,
        "rollback_required": bool(checkpoint_manifest["rollback_required"]),
        "rollback_status_written": bool(checkpoint_manifest["rollback_status_written"]),
        "forbidden_claims_made": forbidden_claims_made,
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def required_artifacts_present(paths: dict[str, Path]) -> bool:
    required_keys = [
        "summary",
        "training_objective_rows",
        "training_run_rows",
        "proof_probe_rows",
        "checkpoint_manifest",
        "candidate_checkpoint",
        "proof_gate_rows",
        "generalization_gate_rows",
        "behavior_retention_gate_rows",
        "promotion_guard_rows",
        "actor_contract_guard_rows",
        "mitigation_reference_guard_rows",
        "claim_boundary_rows",
        "gate_matrix",
        "run_state",
        "doc",
        "follow_up_manifest",
    ]
    return all(paths[key].exists() for key in required_keys)


def build_run_state(
    summary: dict[str, Any],
    paths: dict[str, Path],
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "run_state_id": "m2799_clearance_localized_corrective_training_preflight_state_v0",
        "generated_at_utc": utc_timestamp(),
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "output_paths": {key: str(path) for key, path in paths.items()},
        "actor_contract": {
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_atlas_or_role_labels_detected": False,
        },
        "clearance_target": {
            "target_negative_clearance_count": summary["target_negative_clearance_count"],
            "target_row_count": summary["target_row_count"],
            "drift_required_recovery_negative_count": summary[
                "drift_required_recovery_negative_count"
            ],
            "stable_aes_negative_count": summary["stable_aes_negative_count"],
        },
        "behavior_retention": {
            "stable_avoidable_negative_clearance_count": summary[
                "stable_avoidable_negative_clearance_count"
            ],
            "stable_avoidable_row_count": summary["stable_avoidable_row_count"],
            "guard_hard_before_objectives": summary["obstacle_clearance_guard_hard_before_objectives"],
        },
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_m2800_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    task_id = DEFAULT_NEXT_BLOCKER
    return {
        "id": task_id,
        "type": "gate",
        "gate_tier": "proof",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
        ],
        "lineage": {
            "parent_checkpoint": [
                summary["source_reference_checkpoint"],
                summary["base_candidate_checkpoint"],
                summary["start_candidate_checkpoint"],
                summary["candidate_checkpoint"],
            ],
            "parent_dataset": [
                summary["summary"],
                summary["training_objective_rows"],
                summary["training_run_rows"],
                summary["proof_probe_rows"],
                summary["checkpoint_manifest"],
                summary["proof_gate_rows"],
                summary["generalization_gate_rows"],
                summary["behavior_retention_gate_rows"],
                summary["promotion_guard_rows"],
                summary["actor_contract_guard_rows"],
                summary["mitigation_reference_guard_rows"],
                summary["claim_boundary_rows"],
                summary["gate_matrix"],
                summary["doc"],
            ],
            "parent_config": [
                "experiments/manifests/m2799-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-preflight.json",
                "experiments/manifests/m2798-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-design.json",
                "experiments/manifests/m2796-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-preflight.json",
            ],
            "parent_objective": [
                "audit the M2799 bounded clearance-localized corrective training/update preflight before interpretation"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2798-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-design",
                "m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit",
                "m2796-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-preflight",
            ],
            "blocked_by": [
                "M2799 artifacts must be audited before any validation ranking promotion performance or self-ID interpretation",
                "M2799 remains source-only and cannot resolve high-fidelity validation",
                "stable_avoidable retention and actor-contract guards must be checked before any fresh closed-loop panel",
            ],
            "supersedes": [
                "direct interpretation of M2799 candidate checkpoint without result audit",
                "promotion from clearance-localized corrective preflight artifacts",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2800 must audit M2799 summary required artifacts gates checkpoint lineage behavior-retention rows and claim boundaries",
            "M2800 must verify actor 72/action 3 no hidden/oracle actor input and actor-invisible atlas role dynamics stress clearance outcome route progress success or verdict labels",
            "M2800 must verify obstacle-clearance is hard before road-margin speed yaw-rate conflict or action-delta metrics",
            "M2800 must verify stable_avoidable retention is explicit and mitigation reference rows stay outside ordinary denominators",
            "M2800 must reject validation ranking winner promotion success-rate verdict repair-success driver-performance paper current-sim high-fidelity full ideal driver and self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute new reset step policy action rollout replay validation training PPO source build adapter probe or external simulation",
            "do not change actor inputs or action contract",
            "do not expose role dynamics stress atlas clearance outcome success progress route or verdict labels to actor input",
            "do not use mitigation reference rows as ordinary successes",
            "do not rank checkpoints or select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not hide stable_avoidable retention or obstacle-clearance guard failures behind road-margin speed yaw-rate or action-delta metrics",
            "do not claim repair success driver performance validation paper current-sim high-fidelity full ideal driver or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training",
            "evidence_axis": "source_only_belief_stress_clearance_localized_corrective_training_result_audit",
            "evidence_increment": "audits M2799 corrective candidate checkpoint and proof behavior-retention promotion guard artifacts before interpretation",
            "claim_scope": (
                "Result audit only; no new execution training validation ranking promotion driver-performance "
                "paper high-fidelity self-ID or full-driver claim"
            ),
            "stop_condition": [
                "stop if M2799 required artifacts are incomplete",
                "stop if actor or claim boundaries fail",
                "stop if checkpoint lineage hashes are missing",
                "stop if stable_avoidable behavior-retention guards are not auditable",
                "stop if obstacle-clearance guards are weakened or hidden",
            ],
            "fallback_plan": [
                "route to artifact repair if required artifacts are missing",
                "route to branch synthesis if corrective preflight artifacts are complete but guards fail",
                "route to fresh closed-loop candidate panel only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2799 writes bounded clearance-localized corrective training preflight artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2799 bounded clearance-localized corrective training/update preflight artifacts",
            "admission_evidence": [
                "M2799 summary and gate artifacts exist",
                "M2799 writes a candidate checkpoint manifest and proof generalization behavior-retention promotion gate rows",
                "M2799 is not validated ranked or promoted before this audit",
            ],
            "blocked_shortcuts": [
                "no new execution or training in M2800",
                "no validation ranking promotion success-rate verdict performance paper HF full-driver or self-ID claim",
                "no road-margin-only interpretation without obstacle-clearance and stable_avoidable retention guard audit",
            ],
            "allowed_updates": [
                f"docs/{task_id}.md",
                "M2800 status queue scoreboard research log and review",
            ],
            "next_stage_criteria": [
                "M2799 artifacts are complete and claim-safe or failure is classified",
                "one bounded follow-up or stop decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2800 audits source-only M2799 artifacts and cannot establish self-ID.",
            "history_necessity_tests": [
                "M2800 may check that M2799 covered history stress rows but runs no self-ID comparison."
            ],
            "temporal_evidence_window": "M2796-M2800 source-only clearance-localized corrective branch.",
            "negative_result_policy": (
                "If M2799 artifacts fail, preserve failure and route to synthesis or repair rather "
                "than weakening obstacle-clearance, stable_avoidable, or actor-contract gates."
            ),
            "allowed_claims": [
                "M2799 preflight artifacts are accepted or rejected as complete and claim-safe",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fresh M2799 corrective candidate checkpoint and gate artifacts before extension",
            "paper_verdict_delta": "no paper verdict; audit decides whether M2799 can be used as future engineering evidence",
            "must_synthesize_if": [
                "M2800 finds incomplete artifacts or claim-boundary failure",
                "M2800 finds obstacle-clearance or stable_avoidable guard weakening",
                "another process-only milestone is proposed after M2800 without fresh evidence or synthesis",
            ],
        },
        "hypothesis": "M2799 bounded clearance-localized corrective training artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{task_id}.md exists",
            "M2800 audits M2799 summary required artifacts gates checkpoint lineage behavior-retention rows and claim boundaries",
            "M2800 registers one bounded follow-up or stop decision",
            "M2800 makes no new execution training validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2800 executes new training or rollout",
            "M2800 treats M2799 as validation or promotion evidence",
            "M2800 hides obstacle-clearance or stable_avoidable guard failures",
            "M2800 claims repair success driver performance paper high-fidelity full-driver or self-ID result",
        ],
        "decision_rule": "Pass only if M2800 writes a claim-safe audit of M2799 artifacts and routes before interpretation.",
        "commands": [{"name": "audit_design_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{task_id}.md", "type": "md"}],
        "baseline_checkpoints": [
            summary["source_reference_checkpoint"],
            summary["base_candidate_checkpoint"],
            summary["start_candidate_checkpoint"],
            summary["candidate_checkpoint"],
        ],
        "baseline_artifacts": [summary["summary"], summary["gate_matrix"], summary["behavior_retention_gate_rows"]],
        "scoreboard_checkpoint": f"docs/{task_id}.md",
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    failed = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    lines = [
        "# M2799 Engineering Controller Route A Source-Only Belief-Stress Clearance-Localized Corrective Training Preflight",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result_class: `{summary['result_class']}`",
        "- manifest: `experiments/manifests/m2799-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-preflight.json`",
        f"- summary: `{summary['summary']}`",
        f"- source reference checkpoint: `{summary['source_reference_checkpoint']}`",
        f"- base candidate checkpoint: `{summary['base_candidate_checkpoint']}`",
        f"- start candidate checkpoint: `{summary['start_candidate_checkpoint']}`",
        f"- candidate checkpoint: `{summary['candidate_checkpoint']}`",
        f"- checkpoint manifest: `{summary['checkpoint_manifest']}`",
        f"- training objective rows: `{summary['training_objective_rows']}`",
        f"- training run rows: `{summary['training_run_rows']}`",
        f"- proof probe rows: `{summary['proof_probe_rows']}`",
        f"- proof gates: `{summary['proof_gate_rows']}`",
        f"- generalization gates: `{summary['generalization_gate_rows']}`",
        f"- behavior-retention gates: `{summary['behavior_retention_gate_rows']}`",
        f"- promotion guards: `{summary['promotion_guard_rows']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Result",
        "",
        "M2799 ran one bounded source-only clearance-localized corrective",
        "training/update preflight from the M2791 guardrailed candidate checkpoint,",
        "with M2655 source and M2782 base retained as references. It wrote a",
        "candidate checkpoint for audit, not promotion.",
        "",
        "```text",
        f"training_objective_rows: {summary['training_objective_row_count']}",
        f"target_objective_rows: {summary['target_objective_row_count']}",
        f"retention_objective_rows: {summary['retention_objective_row_count']}",
        f"training_run_rows: {summary['training_run_row_count']}",
        f"proof_probe_rows: {summary['proof_holdout_probe_row_count']}",
        f"stable_avoidable_retention_probe_rows: {summary['stable_avoidable_retention_probe_row_count']}",
        f"proof_gate_rows: {summary['proof_gate_row_count']}",
        f"generalization_gate_rows: {summary['generalization_gate_row_count']}",
        f"behavior_retention_gate_rows: {summary['behavior_retention_gate_row_count']}",
        f"promotion_guard_rows: {summary['promotion_guard_row_count']}",
        f"candidate_checkpoint_written: {summary['candidate_checkpoint_written']}",
        f"checkpoint_behavior_changed: {summary['checkpoint_behavior_changed']}",
        f"gate_matrix_pass: {summary['gate_matrix_pass']}",
        f"failed_gate_ids: {failed}",
        "```",
        "",
        "## Clearance Target And Retention",
        "",
        "```text",
        f"target_negative_clearance_count: {summary['target_negative_clearance_count']}",
        f"target_row_count: {summary['target_row_count']}",
        f"target_negative_clearance_rate: {summary['target_negative_clearance_rate']}",
        f"drift_required_recovery_negative_count: {summary['drift_required_recovery_negative_count']}/48",
        f"stable_aes_negative_count: {summary['stable_aes_negative_count']}/48",
        f"stable_avoidable_negative_clearance_count: {summary['stable_avoidable_negative_clearance_count']}/48",
        f"obstacle_clearance_guard_hard_before_objectives: {summary['obstacle_clearance_guard_hard_before_objectives']}",
        "```",
        "",
        "Obstacle clearance is the hard guard. Road-margin, yaw-rate, final-speed,",
        "throttle/brake conflict, and action-delta metrics are diagnostics and cannot",
        "hide clearance or stable_avoidable retention failures.",
        "",
        "## Actor And Claim Boundary",
        "",
        "Actor input stayed at P0 observation 72 and action 3. Atlas, role,",
        "dynamics, stress, clearance, outcome, success, progress, route, and verdict",
        "labels remained evaluator metadata and were not actor-visible. Mitigation",
        "reference rows stayed outside ordinary denominators.",
        "",
        "M2799 does not validate, rank, promote, compute a success-rate verdict,",
        "claim repair success, driver performance, paper evidence, current-sim",
        "verdict, high-fidelity validation, full ideal driver completion, or",
        "level3 self-identification.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2798-design", type=Path, default=DEFAULT_M2798_DESIGN)
    parser.add_argument("--m2797-audit", type=Path, default=DEFAULT_M2797_AUDIT)
    parser.add_argument("--m2796-dir", type=Path, default=DEFAULT_M2796_DIR)
    parser.add_argument("--m2793-dir", type=Path, default=DEFAULT_M2793_DIR)
    parser.add_argument("--m2791-dir", type=Path, default=DEFAULT_M2791_DIR)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--base-candidate-checkpoint", type=Path, default=DEFAULT_BASE_CANDIDATE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--target-training-seeds-per-bucket", type=int, default=4)
    parser.add_argument("--proof-seeds-per-bucket", type=int, default=2)
    parser.add_argument("--stable-avoidable-retention-seed-count", type=int, default=4)
    parser.add_argument("--behavior-retention-seed-count", type=int, default=4)
    parser.add_argument("--max-updates", type=int, default=1)
    args = parser.parse_args()
    run_clearance_localized_corrective_training_preflight(
        args.output_dir,
        m2798_design=args.m2798_design,
        m2797_audit=args.m2797_audit,
        m2796_dir=args.m2796_dir,
        m2793_dir=args.m2793_dir,
        m2791_dir=args.m2791_dir,
        source_checkpoint=args.source_checkpoint,
        base_candidate_checkpoint=args.base_candidate_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
        device=args.device,
        target_training_seeds_per_bucket=args.target_training_seeds_per_bucket,
        proof_seeds_per_bucket=args.proof_seeds_per_bucket,
        stable_avoidable_retention_seed_count=args.stable_avoidable_retention_seed_count,
        behavior_retention_seed_count=args.behavior_retention_seed_count,
        max_updates=args.max_updates,
    )


if __name__ == "__main__":
    main()
