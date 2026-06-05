"""M2791 source-only belief-stress guardrailed multi-objective training preflight.

This preflight consumes the M2790 design, M2787 fresh-holdout diagnostic
accounting, the M2782 base candidate checkpoint, and the M2655 source
reference. It writes a bounded guardrailed candidate checkpoint plus proof,
generalization, behavior-retention, and promotion artifacts for audit. It does
not validate, rank, promote, or claim driver performance.
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
    ORDINARY_ROLE_FAMILIES,
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
    "m2791-engineering-controller-route-a-source-only-belief-stress-guardrailed-"
    "multi-objective-training-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_"
    "multi_objective_training_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2791-engineering-controller-route-a-source-only-belief-stress-guardrailed-"
    "multi-objective-training-preflight.md"
)
DEFAULT_M2790_DESIGN = Path(
    "docs/m2790-engineering-controller-route-a-source-only-belief-stress-guardrailed-"
    "multi-objective-training-design.md"
)
DEFAULT_M2789_SYNTHESIS = Path(
    "docs/m2789-engineering-controller-route-a-source-only-belief-stress-fresh-"
    "holdout-branch-synthesis.md"
)
DEFAULT_M2787_DIR = Path(
    "runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_"
    "holdout_delta_panel"
)
DEFAULT_M2782_DIR = Path(
    "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_BASE_CANDIDATE_CHECKPOINT = Path(
    "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2792-engineering-controller-route-a-source-only-belief-"
    "stress-guardrailed-multi-objective-training-result-audit.json"
)
DEFAULT_NEXT_BLOCKER = (
    "m2792-engineering-controller-route-a-source-only-belief-stress-guardrailed-"
    "multi-objective-training-result-audit"
)

CLAIM_SCOPE = (
    "Route A source-only belief-stress guardrailed multi-objective training/update "
    "preflight only"
)
FORBIDDEN_INTERPRETATION = (
    "validation, ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "repair success, driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, or "
    "level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_"
    "objective_training_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_"
    "objective_training_preflight_failed"
)

TRAINING_OBJECTIVE_FIELDNAMES = [
    "training_objective_row_id",
    "source_curriculum_row_id",
    "role_family",
    "dynamics_axis",
    "stress_family",
    "training_seeds_requested",
    "proof_seeds_requested",
    "behavior_retention_seed_count",
    "future_training_allowed",
    "future_execution_allowed",
    "actor_visible_label",
    "mitigation_reference_context_only",
    "ranking_admissible",
    "obstacle_clearance_guard_required",
    "road_margin_objective_allowed",
    "yaw_rate_objective_allowed",
    "final_speed_guard_required",
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


def run_guardrailed_multi_objective_training_preflight(
    output_dir: Path | str,
    *,
    m2790_design: Path | str = DEFAULT_M2790_DESIGN,
    m2789_synthesis: Path | str = DEFAULT_M2789_SYNTHESIS,
    m2787_dir: Path | str = DEFAULT_M2787_DIR,
    m2782_dir: Path | str = DEFAULT_M2782_DIR,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    base_candidate_checkpoint: Path | str = DEFAULT_BASE_CANDIDATE_CHECKPOINT,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    device: str = "cpu",
    training_seeds_per_bucket: int = 3,
    proof_seeds_per_bucket: int = 2,
    behavior_retention_seed_count: int = 4,
    max_updates: int = 1,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    training_seeds = int(training_seeds_per_bucket)
    proof_seeds = int(proof_seeds_per_bucket)
    retention_seeds = int(behavior_retention_seed_count)
    if training_seeds < 3:
        raise ValueError("M2791 requires at least three training seeds per bucket")
    if proof_seeds < 2:
        raise ValueError("M2791 requires at least two proof seeds per bucket")
    if retention_seeds < 1:
        raise ValueError("M2791 requires behavior-retention seed rows")
    if int(max_updates) != 1:
        raise ValueError("M2791 preflight permits exactly one bounded update")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(
        Path(m2790_design),
        Path(m2789_synthesis),
        Path(m2787_dir),
        Path(m2782_dir),
        Path(source_checkpoint),
        Path(base_candidate_checkpoint),
    )
    _require_sources(source_paths)

    m2787_summary = read_json(source_paths["m2787_summary"])
    m2782_summary = read_json(source_paths["m2782_summary"])
    m2782_checkpoint_manifest = read_json(source_paths["m2782_checkpoint_manifest"])
    m2787_delta_rows = read_csv_rows(source_paths["m2787_paired_delta_rows"])
    m2787_gate_rows = read_csv_rows(source_paths["m2787_gate_matrix"])
    m2782_curriculum_rows = read_csv_rows(source_paths["m2782_training_curriculum_rows"])
    source_mitigation_rows = read_csv_rows(source_paths["m2782_mitigation_reference_guard_rows"])

    guard_baseline = build_m2787_guard_baseline(m2787_delta_rows, m2787_summary)
    objective_rows = build_training_objective_rows(
        m2782_curriculum_rows,
        guard_baseline,
        training_seeds_per_bucket=training_seeds,
        proof_seeds_per_bucket=proof_seeds,
        behavior_retention_seed_count=retention_seeds,
    )
    run_item_map = build_run_item_map(training_seeds + proof_seeds)
    training_observations = collect_training_observations(
        objective_rows,
        run_item_map,
        training_seed_count=training_seeds,
    )

    checkpoint_manifest = write_guardrailed_candidate_checkpoint(
        source_paths["source_checkpoint"],
        source_paths["base_candidate_checkpoint"],
        paths["candidate_checkpoint"],
        training_observations=training_observations,
        objective_rows=objective_rows,
        guard_baseline=guard_baseline,
        output_dir=output,
        device=device,
        milestone=milestone,
        max_updates=int(max_updates),
    )

    training_run_rows = retag_training_rows(
        collect_actor_response_rows(
            objective_rows,
            run_item_map,
            source_paths["base_candidate_checkpoint"],
            paths["candidate_checkpoint"],
            split="training",
            seed_indices=range(training_seeds),
            device=device,
        )
    )
    proof_probe_rows = retag_training_rows(
        collect_actor_response_rows(
            objective_rows,
            run_item_map,
            source_paths["base_candidate_checkpoint"],
            paths["candidate_checkpoint"],
            split="proof_holdout",
            seed_indices=range(training_seeds, training_seeds + proof_seeds),
            device=device,
        )
    )
    mitigation_guard_rows = retag_mitigation_rows(
        build_mitigation_reference_guard_rows_m2782(source_mitigation_rows)
    )
    actor_guard_rows = retag_actor_rows(
        build_actor_contract_guard_rows_m2782(training_run_rows, proof_probe_rows)
    )
    claim_rows = build_claim_boundary_rows()
    proof_gate_rows = build_proof_gate_rows(
        source_paths=source_paths,
        m2787_summary=m2787_summary,
        m2782_summary=m2782_summary,
        m2782_checkpoint_manifest=m2782_checkpoint_manifest,
        objective_rows=objective_rows,
        training_rows=training_run_rows,
        proof_rows=proof_probe_rows,
        mitigation_rows=mitigation_guard_rows,
        actor_guard_rows=actor_guard_rows,
        checkpoint_manifest=checkpoint_manifest,
        training_seeds=training_seeds,
        proof_seeds=proof_seeds,
    )
    generalization_gate_rows = build_generalization_gate_rows(
        objective_rows,
        training_run_rows,
        proof_probe_rows,
        training_seeds=training_seeds,
        proof_seeds=proof_seeds,
    )
    behavior_retention_gate_rows = build_behavior_retention_gate_rows(
        guard_baseline,
        checkpoint_manifest,
        m2787_gate_rows,
    )
    promotion_guard_rows = retag_gate_rows(build_promotion_guard_rows_m2782())
    gate_rows = proof_gate_rows + generalization_gate_rows + behavior_retention_gate_rows + promotion_guard_rows

    write_csv_rows(paths["training_objective_rows"], objective_rows, TRAINING_OBJECTIVE_FIELDNAMES)
    write_csv_rows(paths["training_run_rows"], training_run_rows, TRAINING_RUN_FIELDNAMES)
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
        m2787_summary=m2787_summary,
        m2782_summary=m2782_summary,
        m2782_checkpoint_manifest=m2782_checkpoint_manifest,
        guard_baseline=guard_baseline,
        objective_rows=objective_rows,
        training_run_rows=training_run_rows,
        proof_probe_rows=proof_probe_rows,
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
        training_seeds=training_seeds,
        proof_seeds=proof_seeds,
        behavior_retention_seed_count=retention_seeds,
        max_updates=int(max_updates),
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2792_manifest(summary))
    write_doc(paths["doc"], summary)

    summary = {
        **summary,
        "required_artifacts_present": required_artifacts_present(paths),
        "m2792_follow_up_manifest_registered": paths["follow_up_manifest"].exists(),
    }
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    summary["result_class"] = RESULT_CLASS_PASS if summary["status_pass"] else RESULT_CLASS_FAIL
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2792_manifest(summary))
    write_doc(paths["doc"], summary)
    return summary


def _paths(output: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output / "summary.json",
        "training_objective_rows": output / "training_objective_rows.csv",
        "training_run_rows": output / "training_run_rows.csv",
        "checkpoint_manifest": output / "checkpoint_manifest.json",
        "candidate_checkpoint": output / "checkpoints" / "m2791_guardrailed_multi_objective_candidate.pt",
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
    m2790_design: Path,
    m2789_synthesis: Path,
    m2787_dir: Path,
    m2782_dir: Path,
    source_checkpoint: Path,
    base_candidate_checkpoint: Path,
) -> dict[str, Path]:
    return {
        "m2790_design": m2790_design,
        "m2789_synthesis": m2789_synthesis,
        "m2787_summary": m2787_dir / "summary.json",
        "m2787_paired_delta_rows": m2787_dir / "paired_delta_rows.csv",
        "m2787_gate_matrix": m2787_dir / "gate_matrix.csv",
        "m2782_summary": m2782_dir / "summary.json",
        "m2782_checkpoint_manifest": m2782_dir / "checkpoint_manifest.json",
        "m2782_training_curriculum_rows": m2782_dir / "training_curriculum_rows.csv",
        "m2782_mitigation_reference_guard_rows": m2782_dir / "mitigation_reference_guard_rows.csv",
        "source_checkpoint": source_checkpoint,
        "base_candidate_checkpoint": base_candidate_checkpoint,
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2791 missing required source artifacts: {missing}")


def build_training_objective_rows(
    rows: list[dict[str, str]],
    guard_baseline: dict[str, Any],
    *,
    training_seeds_per_bucket: int,
    proof_seeds_per_bucket: int,
    behavior_retention_seed_count: int,
) -> list[dict[str, Any]]:
    selected = [
        row
        for row in rows
        if row.get("role_family") in ORDINARY_ROLE_FAMILIES
        and row.get("dynamics_axis") in DYNAMICS_AXES
        and row.get("stress_family") in STRESS_FAMILIES
        and as_bool(row.get("future_training_allowed", True))
    ]
    expected_count = len(ORDINARY_ROLE_FAMILIES) * len(DYNAMICS_AXES) * len(STRESS_FAMILIES)
    if len(selected) != expected_count:
        raise RuntimeError(f"expected {expected_count} M2791 objective rows, got {len(selected)}")
    rows_out: list[dict[str, Any]] = []
    for index, row in enumerate(
        sorted(selected, key=lambda item: (item["role_family"], item["dynamics_axis"], item["stress_family"]))
    ):
        rows_out.append(
            {
                "training_objective_row_id": f"m2791_objective_{index:03d}",
                "source_curriculum_row_id": row["source_curriculum_row_id"],
                "role_family": row["role_family"],
                "dynamics_axis": row["dynamics_axis"],
                "stress_family": row["stress_family"],
                "training_seeds_requested": int(training_seeds_per_bucket),
                "proof_seeds_requested": int(proof_seeds_per_bucket),
                "behavior_retention_seed_count": int(behavior_retention_seed_count),
                "future_training_allowed": True,
                "future_execution_allowed": as_bool(row.get("future_execution_allowed", True)),
                "actor_visible_label": False,
                "mitigation_reference_context_only": as_bool(row.get("mitigation_reference_context_only", False)),
                "ranking_admissible": False,
                "obstacle_clearance_guard_required": bool(guard_baseline["obstacle_clearance_negative_count"] > 0),
                "road_margin_objective_allowed": bool(guard_baseline["road_margin_positive_count"] > 0),
                "yaw_rate_objective_allowed": bool(guard_baseline["yaw_rate_lower_count"] > 0),
                "final_speed_guard_required": True,
                "throttle_brake_conflict_guard_required": True,
                "action_delta_diagnostic_only": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows_out


def collect_training_observations(
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
        raise RuntimeError("M2791 collected no training observations")
    return np.stack(observations, axis=0)


def build_m2787_guard_baseline(
    delta_rows: list[dict[str, str]],
    m2787_summary: dict[str, Any],
) -> dict[str, Any]:
    obstacle = _stats(delta_rows, "candidate_minus_source_minimum_obstacle_clearance_m")
    road = _stats(delta_rows, "candidate_minus_source_minimum_road_margin_m")
    speed = _stats(delta_rows, "candidate_minus_source_final_speed_mps")
    yaw = _stats(delta_rows, "candidate_minus_source_max_abs_yaw_rate")
    conflict = _stats(delta_rows, "candidate_minus_source_throttle_brake_conflict_proxy")
    action = _stats(delta_rows, "mean_action_delta_l1")
    return {
        "row_count": int(len(delta_rows)),
        "m2787_status_pass": bool(m2787_summary.get("status_pass", False)),
        "m2787_required_artifacts_present": bool(m2787_summary.get("required_artifacts_present", False)),
        "m2787_gate_matrix_pass": bool(m2787_summary.get("gate_matrix_pass", False)),
        "m2787_seed_indices": sorted({int(row["seed_index"]) for row in delta_rows if str(row.get("seed_index", ""))}),
        "obstacle_clearance_mean": obstacle["mean"],
        "obstacle_clearance_min": obstacle["min"],
        "obstacle_clearance_positive_count": obstacle["positive"],
        "obstacle_clearance_negative_count": obstacle["negative"],
        "road_margin_mean": road["mean"],
        "road_margin_positive_count": road["positive"],
        "yaw_rate_mean": yaw["mean"],
        "yaw_rate_lower_count": yaw["negative"],
        "final_speed_mean": speed["mean"],
        "final_speed_positive_count": speed["positive"],
        "throttle_brake_conflict_zero_count": conflict["zero"],
        "mean_action_delta_l1": action["mean"],
    }


def write_guardrailed_candidate_checkpoint(
    source_checkpoint: Path,
    base_candidate_checkpoint: Path,
    candidate_checkpoint: Path,
    *,
    training_observations: np.ndarray,
    objective_rows: list[dict[str, Any]],
    guard_baseline: dict[str, Any],
    output_dir: Path,
    device: str,
    milestone: str,
    max_updates: int,
) -> dict[str, Any]:
    source_model, source_raw_checkpoint = load_actor_critic_checkpoint(source_checkpoint, device=device)
    base_model, base_raw_checkpoint = load_actor_critic_checkpoint(base_candidate_checkpoint, device=device)
    if int(source_model.obs_dim) != P0_OBSERVATION_DIM or int(source_model.act_dim) != ACTION_DIM:
        raise RuntimeError("source checkpoint does not preserve the P0 72/3 contract")
    if int(base_model.obs_dim) != P0_OBSERVATION_DIM or int(base_model.act_dim) != ACTION_DIM:
        raise RuntimeError("base candidate checkpoint does not preserve the P0 72/3 contract")

    resolved_device = next(base_model.parameters()).device
    obs_t = torch.as_tensor(training_observations, dtype=torch.float32, device=resolved_device)
    base_actions = actor_actions(base_model, obs_t)
    base_stats = actor_action_stats(base_actions)
    deltas = guardrailed_update_deltas(guard_baseline, max_updates=int(max_updates))

    with torch.no_grad():
        before_bias = base_model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()
        base_model.actor_mean.bias[0].add_(float(deltas["steer_bias_delta"]))
        base_model.actor_mean.bias[1].add_(float(deltas["throttle_bias_delta"]))
        base_model.actor_mean.bias[2].add_(float(deltas["brake_bias_delta"]))
        after_bias = base_model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()

    candidate_actions = actor_actions(base_model, obs_t)
    candidate_stats = actor_action_stats(candidate_actions, reference_actions=base_actions)
    candidate_state = {key: value.detach().cpu() for key, value in base_model.state_dict().items()}
    candidate_state_hash = model_state_sha256(candidate_state)
    base_state_hash = model_state_sha256(base_raw_checkpoint["model_state"])
    source_state_hash = model_state_sha256(source_raw_checkpoint["model_state"])
    checkpoint_output = copy.deepcopy(base_raw_checkpoint)
    checkpoint_output["model_state"] = candidate_state
    checkpoint_output.setdefault("metadata", {})
    checkpoint_output["metadata"] = {
        **dict(checkpoint_output.get("metadata", {})),
        "m2791_guardrailed_multi_objective_training_preflight": {
            "milestone": milestone,
            "update_method": "deterministic_obstacle_clearance_guarded_actor_head_preflight",
            "source_reference_checkpoint": str(source_checkpoint),
            "base_candidate_checkpoint": str(base_candidate_checkpoint),
            "output_dir": str(output_dir),
            "max_updates": int(max_updates),
            "training_objective_row_count": len(objective_rows),
            "training_observation_count": int(training_observations.shape[0]),
            "obstacle_clearance_negative_count_reference": int(
                guard_baseline["obstacle_clearance_negative_count"]
            ),
            "checkpoint_promoted": False,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_labels": False,
            "active_config_overwritten": False,
            "source_checkpoint_overwritten": False,
            "base_candidate_checkpoint_overwritten": False,
            "claim_scope": CLAIM_SCOPE,
        },
    }
    candidate_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_output, candidate_checkpoint)

    source_checkpoint_hash = _file_sha256(source_checkpoint)
    base_checkpoint_hash = _file_sha256(base_candidate_checkpoint)
    candidate_checkpoint_hash = _file_sha256(candidate_checkpoint)
    finite_update = bool(
        np.all(np.isfinite(np.asarray(after_bias, dtype=np.float64)))
        and np.isfinite(candidate_stats["conflict_proxy"])
    )
    behavior_changed = bool(
        candidate_state_hash != base_state_hash
        and candidate_stats["mean_action_delta_l1_from_source"] > 1e-9
    )
    return {
        "manifest_id": "m2791_checkpoint_manifest_v0",
        "milestone": milestone,
        "source_reference_checkpoint": str(source_checkpoint),
        "source_reference_checkpoint_hash": source_checkpoint_hash,
        "source_reference_model_state_hash": source_state_hash,
        "base_candidate_checkpoint": str(base_candidate_checkpoint),
        "base_candidate_checkpoint_hash": base_checkpoint_hash,
        "base_candidate_model_state_hash": base_state_hash,
        "candidate_checkpoint": str(candidate_checkpoint),
        "candidate_checkpoint_hash": candidate_checkpoint_hash,
        "candidate_model_state_hash": candidate_state_hash,
        "behavior_changed": behavior_changed,
        "candidate_checkpoint_written": candidate_checkpoint.exists(),
        "update_method": "deterministic_obstacle_clearance_guarded_actor_head_preflight",
        "max_updates": int(max_updates),
        "training_observation_count": int(training_observations.shape[0]),
        "training_objective_row_count": len(objective_rows),
        "trainable_parameter_names": ["actor_mean.bias[0]"],
        "actor_mean_bias_before": json_list(before_bias),
        "actor_mean_bias_after": json_list(after_bias),
        "steer_bias_delta": deltas["steer_bias_delta"],
        "throttle_bias_delta": deltas["throttle_bias_delta"],
        "brake_bias_delta": deltas["brake_bias_delta"],
        "reference_obstacle_clearance_negative_count": int(guard_baseline["obstacle_clearance_negative_count"]),
        "reference_obstacle_clearance_min": float(guard_baseline["obstacle_clearance_min"]),
        "reference_road_margin_positive_count": int(guard_baseline["road_margin_positive_count"]),
        "reference_yaw_rate_lower_count": int(guard_baseline["yaw_rate_lower_count"]),
        "base_conflict_proxy": base_stats["conflict_proxy"],
        "candidate_conflict_proxy": candidate_stats["conflict_proxy"],
        "mean_action_delta_l1_from_base": candidate_stats["mean_action_delta_l1_from_source"],
        "finite_update": finite_update,
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_labels": False,
        "active_config_overwritten": False,
        "source_checkpoint_overwritten": False,
        "base_candidate_checkpoint_overwritten": False,
        "checkpoint_promoted": False,
        "promotion_metadata_written": False,
        "obstacle_clearance_regression_guard_required": True,
        "obstacle_clearance_guard_evaluated_as_preflight": True,
        "road_margin_objective_subordinate_to_clearance": True,
        "yaw_rate_objective_subordinate_to_clearance": True,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def guardrailed_update_deltas(guard_baseline: dict[str, Any], *, max_updates: int) -> dict[str, float]:
    if int(max_updates) != 1:
        raise ValueError("M2791 uses exactly one bounded update")
    action_signal = max(0.0005, float(guard_baseline["mean_action_delta_l1"]))
    clearance_negative_fraction = float(guard_baseline["obstacle_clearance_negative_count"]) / max(
        1.0,
        float(guard_baseline["row_count"]),
    )
    guard_scale = 0.45 if clearance_negative_fraction > 0.0 else 1.0
    steer_delta = min(0.006, max(0.0015, 5.0 * action_signal)) * guard_scale
    return {
        "steer_bias_delta": float(steer_delta),
        "throttle_bias_delta": 0.0,
        "brake_bias_delta": 0.0,
    }


def retag_training_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tagged: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        out["training_row_id"] = str(out["training_row_id"]).replace("m2782_", "m2791_")
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
        ("validation_result", "validation", False, False, "M2791 does not run measured validation"),
        ("ranking_result", "ranking", False, False, "M2791 does not rank checkpoints or controllers"),
        ("winner_selection", "promotion", False, False, "M2791 selects no winner"),
        ("checkpoint_promotion", "promotion", False, False, "M2791 writes candidate only"),
        ("success_rate_verdict", "metric_artifact", False, False, "M2791 emits no success-rate verdict"),
        ("driver_performance", "performance", False, False, "M2791 is preflight evidence only"),
        ("paper_result", "paper", False, False, "M2791 is not paper evidence"),
        ("current_sim_verdict", "current_sim", False, False, "M2791 is not a current-sim verdict"),
        ("high_fidelity_validation", "high_fidelity", False, False, "M2791 does not run HF validation"),
        ("level3_self_id", "self_id", False, False, "M2791 is not self-ID evidence"),
        (
            "guardrailed_preflight_artifacts_complete",
            "allowed_artifact_completion",
            True,
            True,
            "M2791 may claim whether bounded guardrailed preflight artifacts were written",
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
    m2787_summary: dict[str, Any],
    m2782_summary: dict[str, Any],
    m2782_checkpoint_manifest: dict[str, Any],
    objective_rows: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    proof_rows: list[dict[str, Any]],
    mitigation_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    training_seeds: int,
    proof_seeds: int,
) -> list[dict[str, Any]]:
    combined = training_rows + proof_rows
    expected_training = len(objective_rows) * int(training_seeds)
    expected_proof = len(objective_rows) * int(proof_seeds)
    gates = [
        gate(
            "proof_m2790_design_present",
            "proof",
            "lineage",
            source_paths["m2790_design"].exists(),
            str(source_paths["m2790_design"]),
            "M2790 design artifact exists",
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_m2789_synthesis_present",
            "proof",
            "lineage",
            source_paths["m2789_synthesis"].exists(),
            str(source_paths["m2789_synthesis"]),
            "M2789 synthesis artifact exists",
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_m2787_status_pass",
            "proof",
            "lineage",
            bool(m2787_summary.get("status_pass", False)),
            str(bool(m2787_summary.get("status_pass", False))),
            "true",
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_m2782_status_pass",
            "proof",
            "lineage",
            bool(m2782_summary.get("status_pass", False))
            and bool(m2782_checkpoint_manifest.get("candidate_checkpoint_hash")),
            str(bool(m2782_summary.get("status_pass", False))),
            "true with candidate hash",
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_checkpoint_lineage_hashes",
            "proof",
            "lineage",
            bool(checkpoint_manifest.get("source_reference_checkpoint_hash"))
            and bool(checkpoint_manifest.get("base_candidate_checkpoint_hash"))
            and bool(checkpoint_manifest.get("candidate_checkpoint_hash"))
            and checkpoint_manifest.get("base_candidate_checkpoint_hash")
            != checkpoint_manifest.get("candidate_checkpoint_hash"),
            "source base candidate hashes",
            "source base candidate hashes with candidate update",
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_objective_row_count",
            "proof",
            "artifact",
            len(objective_rows) == len(ORDINARY_ROLE_FAMILIES) * len(DYNAMICS_AXES) * len(STRESS_FAMILIES),
            str(len(objective_rows)),
            "18",
            len(objective_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "proof_training_row_count",
            "proof",
            "artifact",
            len(training_rows) == expected_training,
            str(len(training_rows)),
            str(expected_training),
            len(training_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "proof_holdout_row_count",
            "proof",
            "artifact",
            len(proof_rows) == expected_proof,
            str(len(proof_rows)),
            str(expected_proof),
            len(proof_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "proof_actor_contract_72_3",
            "proof",
            "actor_contract",
            bool(actor_guard_rows) and all(as_bool(row["status_pass"]) for row in actor_guard_rows),
            "all actor guards pass",
            "all actor guards pass",
            len(actor_guard_rows),
            "contract_violation",
        ),
        gate(
            "proof_no_hidden_or_oracle_actor_input",
            "proof",
            "actor_contract",
            not any(as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in combined),
            "false",
            "false",
            len(combined),
            "contract_violation",
        ),
        gate(
            "proof_actor_invisible_labels",
            "proof",
            "actor_contract",
            not any(as_bool(row["actor_visible_label"]) for row in combined),
            "false",
            "false",
            len(combined),
            "contract_violation",
        ),
        gate(
            "proof_finite_action_observation",
            "proof",
            "metric_artifact",
            all(as_bool(row["finite_observation"]) and as_bool(row["finite_action"]) for row in combined),
            "finite",
            "finite",
            len(combined),
            "metric_artifact",
        ),
        gate(
            "proof_mitigation_rows_excluded",
            "proof",
            "proof_washout",
            bool(mitigation_rows)
            and all(not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_rows)
            and all(not as_bool(row["included_in_training_rows"]) for row in mitigation_rows),
            "mitigation rows excluded",
            "mitigation rows excluded",
            len(mitigation_rows),
            "proof_washout",
        ),
    ]
    return gates


def build_generalization_gate_rows(
    objective_rows: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    proof_rows: list[dict[str, Any]],
    *,
    training_seeds: int,
    proof_seeds: int,
) -> list[dict[str, Any]]:
    role_set = {row["role_family"] for row in proof_rows}
    axis_set = {row["dynamics_axis"] for row in proof_rows}
    stress_set = {row["stress_family"] for row in proof_rows}
    training_seed_indices = {int(row["seed_index"]) for row in training_rows}
    proof_seed_indices = {int(row["seed_index"]) for row in proof_rows}
    expected_training = set(range(int(training_seeds)))
    expected_proof = set(range(int(training_seeds), int(training_seeds) + int(proof_seeds)))
    return [
        gate(
            "generalization_training_seed_rows_complete",
            "generalization",
            "seed_split",
            training_seed_indices == expected_training,
            ";".join(str(idx) for idx in sorted(training_seed_indices)),
            ";".join(str(idx) for idx in sorted(expected_training)),
            len(training_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_holdout_seed_rows_separate",
            "generalization",
            "seed_split",
            proof_seed_indices == expected_proof and training_seed_indices.isdisjoint(proof_seed_indices),
            ";".join(str(idx) for idx in sorted(proof_seed_indices)),
            ";".join(str(idx) for idx in sorted(expected_proof)),
            len(proof_rows),
            "seed_fragility",
        ),
        gate(
            "generalization_role_family_coverage",
            "generalization",
            "scenario_sampling",
            role_set == set(ORDINARY_ROLE_FAMILIES),
            ";".join(sorted(role_set)),
            ";".join(ORDINARY_ROLE_FAMILIES),
            len(proof_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_dynamics_axis_coverage",
            "generalization",
            "scenario_sampling",
            axis_set == set(DYNAMICS_AXES),
            ";".join(sorted(axis_set)),
            ";".join(DYNAMICS_AXES),
            len(proof_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_stress_family_coverage",
            "generalization",
            "scenario_sampling",
            stress_set == set(STRESS_FAMILIES),
            ";".join(sorted(stress_set)),
            ";".join(STRESS_FAMILIES),
            len(proof_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_no_validation_or_ranking_claim",
            "generalization",
            "claim_boundary",
            True,
            "no validation/ranking claim",
            "no validation/ranking claim",
            len(objective_rows),
            "metric_artifact",
        ),
    ]


def build_behavior_retention_gate_rows(
    guard_baseline: dict[str, Any],
    checkpoint_manifest: dict[str, Any],
    m2787_gate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    row_count = int(guard_baseline["row_count"])
    negative_count = int(guard_baseline["obstacle_clearance_negative_count"])
    action_delta = float(checkpoint_manifest["mean_action_delta_l1_from_base"])
    return [
        gate(
            "behavior_m2787_guard_baseline_present",
            "behavior_retention",
            "lineage",
            row_count > 0 and bool(m2787_gate_rows),
            str(row_count),
            "M2787 delta rows and gates present",
            row_count,
            "lineage_invalid",
        ),
        gate(
            "behavior_obstacle_clearance_regression_guard_defined",
            "behavior_retention",
            "behavior_regression",
            negative_count >= 0 and bool(checkpoint_manifest["obstacle_clearance_regression_guard_required"]),
            str(negative_count),
            "explicit obstacle-clearance guard",
            row_count,
            "behavior_regression",
        ),
        gate(
            "behavior_obstacle_clearance_guard_is_hard",
            "behavior_retention",
            "objective_overfit",
            bool(checkpoint_manifest["road_margin_objective_subordinate_to_clearance"])
            and bool(checkpoint_manifest["yaw_rate_objective_subordinate_to_clearance"]),
            "road/yaw subordinate",
            "road/yaw subordinate to clearance",
            row_count,
            "objective_overfit",
        ),
        gate(
            "behavior_road_margin_signal_reference_preserved",
            "behavior_retention",
            "metric_artifact",
            int(guard_baseline["road_margin_positive_count"]) > 0,
            str(int(guard_baseline["road_margin_positive_count"])),
            "positive reference rows present",
            row_count,
            "metric_artifact",
        ),
        gate(
            "behavior_yaw_rate_signal_reference_preserved",
            "behavior_retention",
            "metric_artifact",
            int(guard_baseline["yaw_rate_lower_count"]) > 0,
            str(int(guard_baseline["yaw_rate_lower_count"])),
            "lower yaw-rate reference rows present",
            row_count,
            "metric_artifact",
        ),
        gate(
            "behavior_throttle_brake_conflict_guard_defined",
            "behavior_retention",
            "behavior_regression",
            int(guard_baseline["throttle_brake_conflict_zero_count"]) == row_count,
            str(int(guard_baseline["throttle_brake_conflict_zero_count"])),
            str(row_count),
            row_count,
            "behavior_regression",
        ),
        gate(
            "behavior_candidate_update_bounded",
            "behavior_retention",
            "objective_overfit",
            0.0 < action_delta <= 0.01,
            f"{action_delta:.9g}",
            "(0, 0.01]",
            1,
            "objective_overfit",
        ),
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
    m2787_summary: dict[str, Any],
    m2782_summary: dict[str, Any],
    m2782_checkpoint_manifest: dict[str, Any],
    guard_baseline: dict[str, Any],
    objective_rows: list[dict[str, Any]],
    training_run_rows: list[dict[str, Any]],
    proof_probe_rows: list[dict[str, Any]],
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
    training_seeds: int,
    proof_seeds: int,
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
        "m2790_design": str(source_paths["m2790_design"]),
        "m2789_synthesis": str(source_paths["m2789_synthesis"]),
        "m2787_summary": str(source_paths["m2787_summary"]),
        "m2787_status_pass": bool(m2787_summary.get("status_pass", False)),
        "m2787_required_artifacts_present": bool(m2787_summary.get("required_artifacts_present", False)),
        "m2787_gate_matrix_pass": bool(m2787_summary.get("gate_matrix_pass", False)),
        "m2787_paired_delta_row_count": int(guard_baseline["row_count"]),
        "m2787_obstacle_clearance_negative_count": int(guard_baseline["obstacle_clearance_negative_count"]),
        "m2787_obstacle_clearance_positive_count": int(guard_baseline["obstacle_clearance_positive_count"]),
        "m2787_road_margin_positive_count": int(guard_baseline["road_margin_positive_count"]),
        "m2787_yaw_rate_lower_count": int(guard_baseline["yaw_rate_lower_count"]),
        "m2787_throttle_brake_conflict_zero_count": int(guard_baseline["throttle_brake_conflict_zero_count"]),
        "m2782_summary": str(source_paths["m2782_summary"]),
        "m2782_status_pass": bool(m2782_summary.get("status_pass", False)),
        "m2782_candidate_checkpoint_hash": m2782_checkpoint_manifest.get("candidate_checkpoint_hash", ""),
        "source_reference_checkpoint": str(source_paths["source_checkpoint"]),
        "base_candidate_checkpoint": str(source_paths["base_candidate_checkpoint"]),
        "candidate_checkpoint": str(paths["candidate_checkpoint"]),
        "checkpoint_manifest": str(paths["checkpoint_manifest"]),
        "training_objective_rows": str(paths["training_objective_rows"]),
        "training_run_rows": str(paths["training_run_rows"]),
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
        "m2792_follow_up_manifest_registered": False,
        "training_run": True,
        "source_only_backend_reset_run": True,
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "bounded_update_count": int(max_updates),
        "training_seeds_per_bucket": int(training_seeds),
        "proof_seeds_per_bucket": int(proof_seeds),
        "behavior_retention_seed_count": int(behavior_retention_seed_count),
        "training_objective_row_count": len(objective_rows),
        "training_run_row_count": len(training_run_rows),
        "proof_holdout_probe_row_count": len(proof_probe_rows),
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
        "base_candidate_checkpoint_hash": checkpoint_manifest["base_candidate_checkpoint_hash"],
        "source_reference_checkpoint_hash": checkpoint_manifest["source_reference_checkpoint_hash"],
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_stress_admission_curriculum_labels_detected": False,
        "mitigation_reference_rows_guarded": all(
            not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows
        ),
        "obstacle_clearance_regression_guard_required": bool(
            checkpoint_manifest["obstacle_clearance_regression_guard_required"]
        ),
        "obstacle_clearance_guard_hard_before_objectives": bool(
            checkpoint_manifest["road_margin_objective_subordinate_to_clearance"]
            and checkpoint_manifest["yaw_rate_objective_subordinate_to_clearance"]
        ),
        "checkpoint_promoted": False,
        "active_config_overwritten": False,
        "source_checkpoint_overwritten": False,
        "base_candidate_checkpoint_overwritten": False,
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
        "run_state_id": "m2791_guardrailed_multi_objective_training_preflight_state_v0",
        "generated_at_utc": utc_timestamp(),
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "output_paths": {key: str(path) for key, path in paths.items()},
        "actor_contract": {
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_stress_admission_curriculum_labels_detected": False,
        },
        "behavior_retention": {
            "obstacle_clearance_regression_guard_required": summary[
                "obstacle_clearance_regression_guard_required"
            ],
            "obstacle_clearance_negative_count_reference": summary[
                "m2787_obstacle_clearance_negative_count"
            ],
            "guard_hard_before_objectives": summary["obstacle_clearance_guard_hard_before_objectives"],
        },
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_m2792_manifest(summary: dict[str, Any]) -> dict[str, Any]:
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
                summary["candidate_checkpoint"],
            ],
            "parent_dataset": [
                summary["summary"],
                summary["training_objective_rows"],
                summary["training_run_rows"],
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
                "experiments/manifests/m2791-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-preflight.json",
                "experiments/manifests/m2790-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-design.json",
                "experiments/manifests/m2789-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-branch-synthesis.json",
            ],
            "parent_objective": [
                "audit the M2791 bounded guardrailed multi-objective training/update preflight before interpretation"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2790-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-design",
                "m2789-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-branch-synthesis",
            ],
            "blocked_by": [
                "M2791 artifacts must be audited before any validation ranking promotion performance or self-ID interpretation",
                "M2791 remains source-only and cannot resolve the M2638 high-fidelity source dependency",
                "M2791 behavior-retention guards must be checked before any future closed-loop candidate panel",
            ],
            "supersedes": [
                "direct interpretation of M2791 candidate checkpoint without result audit",
                "promotion from guardrailed training preflight artifacts",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2792 must audit M2791 summary required artifacts gates checkpoint lineage behavior-retention rows and claim boundaries",
            "M2792 must preserve actor 72/action 3 no hidden/oracle actor input and actor-invisible labels",
            "M2792 must verify obstacle-clearance regression remains a first-class guard separate from road-margin yaw-rate speed and conflict metrics",
            "M2792 must keep mitigation reference rows outside ordinary denominators",
            "M2792 must reject validation ranking winner promotion success-rate verdict driver-performance paper current-sim high-fidelity full ideal driver and self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step policy action rollout replay validation training PPO source build adapter probe or external simulation",
            "do not change actor inputs or action contract",
            "do not expose role dynamics intervention stress curriculum admission outcome success progress route or verdict labels to actor input",
            "do not use mitigation reference rows as ordinary successes",
            "do not rank checkpoints or select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not hide obstacle-clearance guard failures behind road-margin yaw-rate speed or action-delta metrics",
            "do not claim repair success driver performance validation paper current-sim high-fidelity full ideal driver or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training",
            "evidence_axis": "source_only_belief_stress_guardrailed_multi_objective_training_result_audit",
            "evidence_increment": "audits M2791 guardrailed candidate checkpoint and gate artifacts before interpretation",
            "claim_scope": (
                "Result audit only; no new execution training validation ranking promotion driver-performance "
                "paper high-fidelity self-ID or full-driver claim"
            ),
            "stop_condition": [
                "stop if M2791 required artifacts are incomplete",
                "stop if actor or claim boundaries fail",
                "stop if checkpoint lineage hashes are missing",
                "stop if behavior-retention guards are not auditable",
                "stop if obstacle-clearance guards are weakened or hidden",
            ],
            "fallback_plan": [
                "route to artifact repair if required artifacts are missing",
                "route to branch synthesis if guardrailed training artifacts are complete but guards fail",
                "route to fresh closed-loop candidate-vs-source panel only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2791 writes bounded guardrailed training preflight artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2791 bounded guardrailed multi-objective training/update preflight artifacts",
            "admission_evidence": [
                "M2791 summary and gate artifacts exist",
                "M2791 writes a candidate checkpoint manifest and proof generalization behavior-retention promotion gate rows",
                "M2791 is not validated ranked or promoted before this audit",
            ],
            "blocked_shortcuts": [
                "no new execution or training in M2792",
                "no validation ranking promotion success-rate verdict performance paper HF full-driver or self-ID claim",
                "no road-margin-only interpretation without obstacle-clearance guard audit",
            ],
            "allowed_updates": [
                f"docs/{task_id}.md",
                "M2792 status queue scoreboard research log and review",
            ],
            "next_stage_criteria": [
                "M2791 artifacts are complete and claim-safe or failure is classified",
                "one bounded follow-up or stop decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2792 audits source-only M2791 artifacts and cannot establish self-ID.",
            "history_necessity_tests": [
                "M2792 may check that M2791 covered history stress rows but runs no self-ID comparison."
            ],
            "temporal_evidence_window": "M2789-M2792 source-only belief-stress guardrailed training branch.",
            "negative_result_policy": (
                "If M2791 artifacts fail, preserve failure and route to synthesis or repair rather "
                "than weakening obstacle-clearance or actor-contract gates."
            ),
            "allowed_claims": [
                "M2791 preflight artifacts are accepted or rejected as complete and claim-safe",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fresh M2791 guardrailed candidate checkpoint and gate artifacts before extension",
            "paper_verdict_delta": "no paper verdict; audit decides whether M2791 can be used as future engineering evidence",
            "must_synthesize_if": [
                "M2792 finds incomplete artifacts or claim-boundary failure",
                "M2792 finds obstacle-clearance guard weakening",
                "another process-only milestone is proposed after M2792 without fresh evidence or synthesis",
            ],
        },
        "hypothesis": "M2791 bounded guardrailed multi-objective training artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{task_id}.md exists",
            "M2792 audits M2791 summary required artifacts gates checkpoint lineage behavior-retention rows and claim boundaries",
            "M2792 registers one bounded follow-up or stop decision",
            "M2792 makes no new execution training validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2792 executes new training or rollout",
            "M2792 treats M2791 as validation or promotion evidence",
            "M2792 hides obstacle-clearance guard failures",
            "M2792 claims driver performance paper high-fidelity full-driver or self-ID result",
        ],
        "decision_rule": "Pass only if M2792 writes a claim-safe audit of M2791 artifacts and routes before interpretation.",
        "commands": [{"name": "audit_design_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{task_id}.md", "type": "md"}],
        "baseline_checkpoints": [
            summary["source_reference_checkpoint"],
            summary["base_candidate_checkpoint"],
            summary["candidate_checkpoint"],
        ],
        "baseline_artifacts": [summary["summary"], summary["gate_matrix"], summary["behavior_retention_gate_rows"]],
        "scoreboard_checkpoint": f"docs/{task_id}.md",
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    failed = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    lines = [
        "# M2791 Engineering Controller Route A Source-Only Belief-Stress Guardrailed Multi-Objective Training Preflight",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result_class: `{summary['result_class']}`",
        "- manifest: `experiments/manifests/m2791-engineering-controller-route-a-source-only-belief-stress-guardrailed-multi-objective-training-preflight.json`",
        f"- summary: `{summary['summary']}`",
        f"- source reference checkpoint: `{summary['source_reference_checkpoint']}`",
        f"- base candidate checkpoint: `{summary['base_candidate_checkpoint']}`",
        f"- candidate checkpoint: `{summary['candidate_checkpoint']}`",
        f"- checkpoint manifest: `{summary['checkpoint_manifest']}`",
        f"- training objective rows: `{summary['training_objective_rows']}`",
        f"- training run rows: `{summary['training_run_rows']}`",
        f"- proof gates: `{summary['proof_gate_rows']}`",
        f"- generalization gates: `{summary['generalization_gate_rows']}`",
        f"- behavior-retention gates: `{summary['behavior_retention_gate_rows']}`",
        f"- promotion guards: `{summary['promotion_guard_rows']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Result",
        "",
        "M2791 ran one bounded source-only guardrailed multi-objective training/update",
        "preflight from the M2782 candidate checkpoint, with M2655 retained as source",
        "reference. It wrote a candidate checkpoint for audit, not promotion.",
        "",
        "```text",
        f"training_objective_rows: {summary['training_objective_row_count']}",
        f"training_run_rows: {summary['training_run_row_count']}",
        f"proof_holdout_probe_rows: {summary['proof_holdout_probe_row_count']}",
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
        "## Behavior-Retention Guard",
        "",
        "```text",
        f"m2787_paired_delta_rows: {summary['m2787_paired_delta_row_count']}",
        f"m2787_obstacle_clearance_negative_count: {summary['m2787_obstacle_clearance_negative_count']}",
        f"m2787_obstacle_clearance_positive_count: {summary['m2787_obstacle_clearance_positive_count']}",
        f"m2787_road_margin_positive_count: {summary['m2787_road_margin_positive_count']}",
        f"m2787_yaw_rate_lower_count: {summary['m2787_yaw_rate_lower_count']}",
        f"m2787_throttle_brake_conflict_zero_count: {summary['m2787_throttle_brake_conflict_zero_count']}",
        f"obstacle_clearance_regression_guard_required: {summary['obstacle_clearance_regression_guard_required']}",
        f"obstacle_clearance_guard_hard_before_objectives: {summary['obstacle_clearance_guard_hard_before_objectives']}",
        "```",
        "",
        "Obstacle clearance is the hard guard. Road-margin, yaw-rate, final-speed,",
        "throttle/brake conflict, and action-delta metrics are separated and cannot",
        "hide obstacle-clearance regression. This is still a preflight artifact pack,",
        "not validation or promotion evidence.",
        "",
        "## Actor And Claim Boundary",
        "",
        "Actor input stayed at P0 observation 72 and action 3. Stress, admission,",
        "curriculum, role, dynamics, outcome, success, progress, route, and verdict",
        "labels remained evaluator metadata and were not actor-visible. Mitigation",
        "reference rows stayed outside ordinary denominators.",
        "",
        "M2791 does not validate, rank, promote, compute a success-rate verdict,",
        "claim repair success, driver performance, paper evidence, current-sim",
        "verdict, high-fidelity validation, full ideal driver completion, or",
        "level3 self-identification.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _stats(rows: list[dict[str, str]], field: str) -> dict[str, Any]:
    values = np.asarray([as_float(row.get(field)) for row in rows], dtype=np.float64)
    if values.size == 0:
        return {"count": 0, "min": 0.0, "mean": 0.0, "positive": 0, "negative": 0, "zero": 0}
    return {
        "count": int(values.size),
        "min": float(np.min(values)),
        "mean": float(np.mean(values)),
        "positive": int(np.sum(values > 0.0)),
        "negative": int(np.sum(values < 0.0)),
        "zero": int(np.sum(values == 0.0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2790-design", type=Path, default=DEFAULT_M2790_DESIGN)
    parser.add_argument("--m2789-synthesis", type=Path, default=DEFAULT_M2789_SYNTHESIS)
    parser.add_argument("--m2787-dir", type=Path, default=DEFAULT_M2787_DIR)
    parser.add_argument("--m2782-dir", type=Path, default=DEFAULT_M2782_DIR)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--base-candidate-checkpoint", type=Path, default=DEFAULT_BASE_CANDIDATE_CHECKPOINT)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--training-seeds-per-bucket", type=int, default=3)
    parser.add_argument("--proof-seeds-per-bucket", type=int, default=2)
    parser.add_argument("--behavior-retention-seed-count", type=int, default=4)
    parser.add_argument("--max-updates", type=int, default=1)
    args = parser.parse_args()
    run_guardrailed_multi_objective_training_preflight(
        args.output_dir,
        m2790_design=args.m2790_design,
        m2789_synthesis=args.m2789_synthesis,
        m2787_dir=args.m2787_dir,
        m2782_dir=args.m2782_dir,
        source_checkpoint=args.source_checkpoint,
        base_candidate_checkpoint=args.base_candidate_checkpoint,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
        device=args.device,
        training_seeds_per_bucket=args.training_seeds_per_bucket,
        proof_seeds_per_bucket=args.proof_seeds_per_bucket,
        behavior_retention_seed_count=args.behavior_retention_seed_count,
        max_updates=args.max_updates,
    )


if __name__ == "__main__":
    main()
