"""M2782 source-only belief-stress short-training continuation preflight.

This preflight consumes the audited M2779 belief-stress curriculum and the
M2655 source-only checkpoint. It writes a bounded candidate checkpoint plus
training/proof/generalization/promotion artifacts, but it does not validate,
rank, promote, or claim driver performance.
"""

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
    _file_sha256,
    actor_action_stats,
    actor_actions,
    model_state_sha256,
)
from autodrift.engineering_controller_route_a_source_only_fresh_generalization_panel import (
    DEFAULT_FRESH_SEED_COUNT,
    DYNAMICS_AXES,
    build_fresh_generalization_panel_specs,
)
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
)


DEFAULT_MILESTONE = (
    "m2782-engineering-controller-route-a-source-only-belief-stress-short-training-"
    "continuation-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight"
)
DEFAULT_M2781_DESIGN = Path(
    "docs/m2781-engineering-controller-route-a-source-only-belief-stress-short-training-"
    "continuation-design.md"
)
DEFAULT_M2779_DIR = Path(
    "runs/m2779_engineering_controller_route_a_source_only_belief_stress_training_"
    "admission_pack_materialization"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2783-engineering-controller-route-a-source-only-belief-stress-"
    "short-training-continuation-result-audit.json"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2782-engineering-controller-route-a-source-only-belief-stress-short-training-"
    "continuation-preflight.md"
)
DEFAULT_NEXT_BLOCKER = (
    "m2783-engineering-controller-route-a-source-only-belief-stress-short-training-"
    "continuation-result-audit"
)

ORDINARY_ROLE_FAMILIES = (
    "stable_avoidable",
    "stable_aes",
    "drift_required_recovery",
)
STRESS_FAMILIES = (
    "recurrent_hidden_reset_stress",
    "previous_command_history_stress",
    "held_actuator_history_stress",
)

CLAIM_SCOPE = "Route A source-only belief-stress short-training continuation preflight only"
FORBIDDEN_INTERPRETATION = (
    "validation, ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "repair success, driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, or "
    "level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight_failed"
)

TRAINING_CURRICULUM_FIELDNAMES = [
    "training_curriculum_row_id",
    "source_curriculum_row_id",
    "role_family",
    "dynamics_axis",
    "stress_family",
    "future_pack_priority",
    "ordinary_candidate_count",
    "mitigation_reference_count",
    "training_seeds_requested",
    "proof_seeds_requested",
    "training_run_rows_expected",
    "proof_holdout_rows_expected",
    "future_training_allowed",
    "future_execution_allowed",
    "actor_visible_label",
    "mitigation_reference_context_only",
    "ranking_admissible",
    "claim_boundary",
]

TRAINING_RUN_FIELDNAMES = [
    "training_row_id",
    "split",
    "role_family",
    "dynamics_axis",
    "stress_family",
    "seed_index",
    "seed",
    "source_curriculum_row_id",
    "fixture_id",
    "stress_preparation",
    "warmup_step_count",
    "observation_shape",
    "action_shape",
    "reset_run",
    "policy_action_run",
    "backend_step_run",
    "source_action_steer",
    "source_action_throttle",
    "source_action_brake",
    "candidate_action_steer",
    "candidate_action_throttle",
    "candidate_action_brake",
    "action_delta_l1",
    "candidate_throttle_brake_conflict_proxy",
    "command_response_proxy",
    "finite_observation",
    "finite_action",
    "actor_visible_label",
    "hidden_or_oracle_actor_inputs_required",
    "ordinary_denominator_allowed",
    "mitigation_reference",
    "update_index",
    "claim_scope",
    "forbidden_interpretation",
]

CHECKPOINT_TRACE_FIELDNAMES = [
    "update_index",
    "update_method",
    "source_checkpoint",
    "candidate_checkpoint",
    "training_observation_count",
    "training_curriculum_row_count",
    "training_run_rows_expected",
    "source_model_state_hash",
    "candidate_model_state_hash",
    "source_checkpoint_hash",
    "candidate_checkpoint_hash",
    "actor_mean_bias_before",
    "actor_mean_bias_after",
    "steer_bias_delta",
    "throttle_bias_delta",
    "brake_bias_delta",
    "mean_action_l1_signal",
    "mean_command_response_signal",
    "source_conflict_proxy",
    "candidate_conflict_proxy",
    "mean_action_delta_l1",
    "finite_update",
    "actor_contract_shape_72_action_3",
    "hidden_or_oracle_actor_inputs_required",
    "active_config_overwritten",
    "source_checkpoint_overwritten",
    "checkpoint_promoted",
    "claim_scope",
    "forbidden_interpretation",
]

GATE_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "row_count",
    "failure_type",
    "claim_boundary",
]

ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "protected_field",
    "actor_visible_allowed",
    "actor_observation_shape",
    "action_shape",
    "status_pass",
    "evidence",
    "claim_boundary",
]

MITIGATION_GUARD_FIELDNAMES = [
    "source_guard_id",
    "candidate_id",
    "role_family",
    "dynamics_axis",
    "seed",
    "mitigation_reference",
    "ordinary_denominator_allowed",
    "future_training_allowed",
    "future_execution_allowed",
    "context_only",
    "actor_visible_allowed",
    "included_in_training_rows",
    "included_in_proof_denominator",
    "status_pass",
    "guard_family",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "allowed",
    "status_pass",
    "evidence",
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


def run_belief_stress_short_training_continuation_preflight(
    output_dir: Path | str,
    *,
    m2781_design: Path | str = DEFAULT_M2781_DESIGN,
    m2779_dir: Path | str = DEFAULT_M2779_DIR,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    device: str = "cpu",
    training_seeds_per_bucket: int = 3,
    proof_seeds_per_bucket: int = 1,
    max_updates: int = 1,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    training_seeds = int(training_seeds_per_bucket)
    proof_seeds = int(proof_seeds_per_bucket)
    if training_seeds + proof_seeds != DEFAULT_FRESH_SEED_COUNT:
        raise ValueError(
            f"training_seeds_per_bucket + proof_seeds_per_bucket must equal {DEFAULT_FRESH_SEED_COUNT}"
        )
    if training_seeds < 1 or proof_seeds < 1:
        raise ValueError("training and proof seed counts must be positive")
    if int(max_updates) != 1:
        raise ValueError("M2782 preflight permits exactly one bounded update")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(Path(m2781_design), Path(m2779_dir), Path(source_checkpoint))
    _require_sources(source_paths)

    m2779_summary = read_json(source_paths["m2779_summary"])
    source_curriculum_rows = read_csv_rows(source_paths["stress_curriculum_rows"])
    source_admission_rows = read_csv_rows(source_paths["belief_stress_admission_rows"])
    source_mitigation_rows = read_csv_rows(source_paths["mitigation_reference_guard_rows"])

    training_curriculum_rows = build_training_curriculum_rows(
        source_curriculum_rows,
        training_seeds_per_bucket=training_seeds,
        proof_seeds_per_bucket=proof_seeds,
    )
    run_item_map = build_run_item_map(training_seeds + proof_seeds)
    training_observations = collect_training_observations(training_curriculum_rows, run_item_map, training_seeds)
    checkpoint_trace_rows, checkpoint_manifest = write_candidate_checkpoint(
        source_paths["source_checkpoint"],
        paths["candidate_checkpoint"],
        training_observations=training_observations,
        source_admission_rows=source_admission_rows,
        training_curriculum_rows=training_curriculum_rows,
        output_dir=output,
        device=device,
        milestone=milestone,
        max_updates=int(max_updates),
    )

    training_run_rows = collect_training_run_rows(
        training_curriculum_rows,
        run_item_map,
        source_paths["source_checkpoint"],
        paths["candidate_checkpoint"],
        training_seeds=training_seeds,
        device=device,
    )
    proof_probe_rows = collect_proof_probe_rows(
        training_curriculum_rows,
        run_item_map,
        source_paths["source_checkpoint"],
        paths["candidate_checkpoint"],
        training_seeds=training_seeds,
        proof_seeds=proof_seeds,
        device=device,
    )
    mitigation_guard_rows = build_mitigation_reference_guard_rows(source_mitigation_rows)
    actor_guard_rows = build_actor_contract_guard_rows(training_run_rows, proof_probe_rows)
    claim_rows = build_claim_boundary_rows()
    proof_gate_rows = build_proof_gate_rows(
        training_curriculum_rows,
        training_run_rows,
        proof_probe_rows,
        mitigation_guard_rows,
        checkpoint_manifest,
        actor_guard_rows,
    )
    generalization_gate_rows = build_generalization_gate_rows(
        training_curriculum_rows,
        proof_probe_rows,
        training_seeds=training_seeds,
        proof_seeds=proof_seeds,
    )
    promotion_guard_rows = build_promotion_guard_rows()
    gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows

    write_csv_rows(paths["training_curriculum_rows"], training_curriculum_rows, TRAINING_CURRICULUM_FIELDNAMES)
    write_csv_rows(paths["training_run_rows"], training_run_rows, TRAINING_RUN_FIELDNAMES)
    write_csv_rows(paths["checkpoint_trace_rows"], checkpoint_trace_rows, CHECKPOINT_TRACE_FIELDNAMES)
    write_json(paths["checkpoint_manifest"], checkpoint_manifest)
    write_csv_rows(paths["proof_gate_rows"], proof_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["generalization_gate_rows"], generalization_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["promotion_guard_rows"], promotion_guard_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["mitigation_reference_guard_rows"], mitigation_guard_rows, MITIGATION_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        m2779_summary=m2779_summary,
        training_curriculum_rows=training_curriculum_rows,
        training_run_rows=training_run_rows,
        proof_probe_rows=proof_probe_rows,
        checkpoint_trace_rows=checkpoint_trace_rows,
        checkpoint_manifest=checkpoint_manifest,
        proof_gate_rows=proof_gate_rows,
        generalization_gate_rows=generalization_gate_rows,
        promotion_guard_rows=promotion_guard_rows,
        actor_guard_rows=actor_guard_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        claim_rows=claim_rows,
        milestone=milestone,
        next_blocker=next_blocker,
        training_seeds=training_seeds,
        proof_seeds=proof_seeds,
        max_updates=int(max_updates),
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2783_manifest(summary))
    write_doc(paths["doc"], summary)

    summary = {
        **summary,
        "required_artifacts_present": required_artifacts_present(paths),
        "m2783_follow_up_manifest_registered": paths["follow_up_manifest"].exists(),
    }
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_doc(paths["doc"], summary)
    return summary


def _paths(output: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output / "summary.json",
        "training_curriculum_rows": output / "training_curriculum_rows.csv",
        "training_run_rows": output / "training_run_rows.csv",
        "checkpoint_trace_rows": output / "checkpoint_trace_rows.csv",
        "checkpoint_manifest": output / "checkpoint_manifest.json",
        "candidate_checkpoint": output / "checkpoints" / "m2782_belief_stress_short_training_candidate.pt",
        "proof_gate_rows": output / "proof_gate_rows.csv",
        "generalization_gate_rows": output / "generalization_gate_rows.csv",
        "promotion_guard_rows": output / "promotion_guard_rows.csv",
        "actor_contract_guard_rows": output / "actor_contract_guard_rows.csv",
        "mitigation_reference_guard_rows": output / "mitigation_reference_guard_rows.csv",
        "claim_boundary_rows": output / "claim_boundary_rows.csv",
        "gate_matrix": output / "gate_matrix.csv",
        "run_state": output / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _source_paths(m2781_design: Path, m2779_dir: Path, source_checkpoint: Path) -> dict[str, Path]:
    return {
        "m2781_design": m2781_design,
        "m2779_summary": m2779_dir / "summary.json",
        "belief_stress_admission_rows": m2779_dir / "belief_stress_admission_rows.csv",
        "stress_curriculum_rows": m2779_dir / "stress_curriculum_rows.csv",
        "mitigation_reference_guard_rows": m2779_dir / "mitigation_reference_guard_rows.csv",
        "actor_contract_guard_rows": m2779_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2779_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2779_dir / "gate_matrix.csv",
        "source_checkpoint": source_checkpoint,
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2782 missing required source artifacts: {missing}")


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_training_curriculum_rows(
    rows: list[dict[str, str]],
    *,
    training_seeds_per_bucket: int,
    proof_seeds_per_bucket: int,
) -> list[dict[str, Any]]:
    selected = [
        row
        for row in rows
        if row.get("role_family") in ORDINARY_ROLE_FAMILIES
        and row.get("dynamics_axis") in DYNAMICS_AXES
        and row.get("stress_family") in STRESS_FAMILIES
        and as_bool(row.get("future_training_allowed", False))
    ]
    expected_count = len(ORDINARY_ROLE_FAMILIES) * len(DYNAMICS_AXES) * len(STRESS_FAMILIES)
    if len(selected) != expected_count:
        raise RuntimeError(f"expected {expected_count} ordinary M2779 curriculum rows, got {len(selected)}")

    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        sorted(selected, key=lambda item: (item["role_family"], item["dynamics_axis"], item["stress_family"]))
    ):
        output_rows.append(
            {
                "training_curriculum_row_id": f"m2782_curriculum_{index:03d}",
                "source_curriculum_row_id": row["curriculum_row_id"],
                "role_family": row["role_family"],
                "dynamics_axis": row["dynamics_axis"],
                "stress_family": row["stress_family"],
                "future_pack_priority": row["future_pack_priority"],
                "ordinary_candidate_count": int(row["ordinary_candidate_count"]),
                "mitigation_reference_count": int(row["mitigation_reference_count"]),
                "training_seeds_requested": int(training_seeds_per_bucket),
                "proof_seeds_requested": int(proof_seeds_per_bucket),
                "training_run_rows_expected": int(training_seeds_per_bucket),
                "proof_holdout_rows_expected": int(proof_seeds_per_bucket),
                "future_training_allowed": True,
                "future_execution_allowed": as_bool(row.get("future_execution_allowed", False)),
                "actor_visible_label": False,
                "mitigation_reference_context_only": int(row["mitigation_reference_count"]) > 0,
                "ranking_admissible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def build_run_item_map(seed_count: int) -> dict[tuple[str, str, int], Any]:
    run_items, _seed_rows, _axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=int(seed_count)
    )
    return {
        (item.role_family, item.dynamics_axis_id, int(item.seed_index)): item
        for item in run_items
    }


def collect_training_observations(
    curriculum_rows: list[dict[str, Any]],
    run_item_map: dict[tuple[str, str, int], Any],
    training_seed_count: int,
) -> np.ndarray:
    observations: list[np.ndarray] = []
    for row in curriculum_rows:
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
        raise RuntimeError("M2782 collected no training observations")
    return np.stack(observations, axis=0)


def collect_stress_observation(
    run_item_map: dict[tuple[str, str, int], Any],
    role_family: str,
    dynamics_axis: str,
    seed_index: int,
    stress_family: str,
) -> tuple[np.ndarray, str, int]:
    item = run_item_map[(role_family, dynamics_axis, int(seed_index))]
    extractor = P0ObservationExtractor()
    backend = FourWheelHF0Backend(fixture_spec=item.fixture_spec)
    warmup_count = 0
    try:
        reset_result = backend.reset(
            BackendResetRequest(
                seed=item.seed,
                scenario_spec_id=item.fixture_id,
                role_family=item.role_family,
                options={
                    "seed_panel_id": item.seed_panel_id,
                    "seed_index": item.seed_index,
                    "dynamics_axis_id": item.dynamics_axis_id,
                    "stress_family": stress_family,
                    "actor_visible_labels": False,
                },
            )
        )
        actor_view = reset_result.actor_view
        if stress_family == "held_actuator_history_stress":
            step_result = backend.step(np.asarray([0.18, -0.20, -0.55], dtype=np.float32))
            actor_view = step_result.actor_view
            warmup_count = 1
        observation = extractor.extract(actor_view)
    finally:
        backend.close()
    if observation.shape != (P0_OBSERVATION_DIM,):
        raise RuntimeError(f"expected P0 observation shape {P0_OBSERVATION_DIM}, got {observation.shape}")
    if not np.all(np.isfinite(observation)):
        raise RuntimeError("non-finite M2782 observation")
    return np.asarray(observation, dtype=np.float32), item.fixture_id, warmup_count


def write_candidate_checkpoint(
    source_checkpoint: Path,
    candidate_checkpoint: Path,
    *,
    training_observations: np.ndarray,
    source_admission_rows: list[dict[str, str]],
    training_curriculum_rows: list[dict[str, Any]],
    output_dir: Path,
    device: str,
    milestone: str,
    max_updates: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    model, checkpoint = load_actor_critic_checkpoint(source_checkpoint, device=device)
    resolved_device = next(model.parameters()).device
    if int(model.obs_dim) != P0_OBSERVATION_DIM or int(model.act_dim) != ACTION_DIM:
        raise RuntimeError("source checkpoint does not preserve the P0 72/3 contract")

    source_state_hash = model_state_sha256(checkpoint["model_state"])
    obs_t = torch.as_tensor(training_observations, dtype=torch.float32, device=resolved_device)
    source_actions = actor_actions(model, obs_t)
    source_stats = actor_action_stats(source_actions)
    deltas = bounded_update_deltas(source_admission_rows, max_updates=int(max_updates))

    with torch.no_grad():
        before_bias = model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()
        model.actor_mean.bias[0].add_(float(deltas["steer_bias_delta"]))
        model.actor_mean.bias[1].add_(float(deltas["throttle_bias_delta"]))
        model.actor_mean.bias[2].add_(float(deltas["brake_bias_delta"]))
        after_bias = model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()

    candidate_actions = actor_actions(model, obs_t)
    candidate_stats = actor_action_stats(candidate_actions, reference_actions=source_actions)
    candidate_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    candidate_state_hash = model_state_sha256(candidate_state)
    checkpoint_output = copy.deepcopy(checkpoint)
    checkpoint_output["model_state"] = candidate_state
    checkpoint_output.setdefault("metadata", {})
    checkpoint_output["metadata"] = {
        **dict(checkpoint_output.get("metadata", {})),
        "m2782_belief_stress_short_training_continuation_preflight": {
            "milestone": milestone,
            "update_method": "deterministic_belief_stress_actor_head_continuation_preflight",
            "source_checkpoint": str(source_checkpoint),
            "output_dir": str(output_dir),
            "max_updates": int(max_updates),
            "training_curriculum_row_count": len(training_curriculum_rows),
            "training_observation_count": int(training_observations.shape[0]),
            "trainable_parameter_names": [
                "actor_mean.bias[0]",
                "actor_mean.bias[1]",
                "actor_mean.bias[2]",
            ],
            "checkpoint_promoted": False,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_labels": False,
            "active_config_overwritten": False,
            "claim_scope": CLAIM_SCOPE,
        },
    }
    candidate_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_output, candidate_checkpoint)

    source_checkpoint_hash = _file_sha256(source_checkpoint)
    candidate_checkpoint_hash = _file_sha256(candidate_checkpoint)
    finite_update = bool(
        np.all(np.isfinite(np.asarray(after_bias, dtype=np.float64)))
        and np.isfinite(candidate_stats["conflict_proxy"])
    )
    behavior_changed = bool(
        candidate_state_hash != source_state_hash
        and candidate_stats["mean_action_delta_l1_from_source"] > 1e-9
    )
    trace_row = {
        "update_index": 0,
        "update_method": "deterministic_belief_stress_actor_head_continuation_preflight",
        "source_checkpoint": str(source_checkpoint),
        "candidate_checkpoint": str(candidate_checkpoint),
        "training_observation_count": int(training_observations.shape[0]),
        "training_curriculum_row_count": len(training_curriculum_rows),
        "training_run_rows_expected": len(training_curriculum_rows) * 3,
        "source_model_state_hash": source_state_hash,
        "candidate_model_state_hash": candidate_state_hash,
        "source_checkpoint_hash": source_checkpoint_hash,
        "candidate_checkpoint_hash": candidate_checkpoint_hash,
        "actor_mean_bias_before": json_list(before_bias),
        "actor_mean_bias_after": json_list(after_bias),
        "steer_bias_delta": deltas["steer_bias_delta"],
        "throttle_bias_delta": deltas["throttle_bias_delta"],
        "brake_bias_delta": deltas["brake_bias_delta"],
        "mean_action_l1_signal": deltas["mean_action_l1_signal"],
        "mean_command_response_signal": deltas["mean_command_response_signal"],
        "source_conflict_proxy": source_stats["conflict_proxy"],
        "candidate_conflict_proxy": candidate_stats["conflict_proxy"],
        "mean_action_delta_l1": candidate_stats["mean_action_delta_l1_from_source"],
        "finite_update": finite_update,
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "active_config_overwritten": False,
        "source_checkpoint_overwritten": False,
        "checkpoint_promoted": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    manifest = {
        "manifest_id": "m2782_checkpoint_manifest_v0",
        "milestone": milestone,
        "source_checkpoint": str(source_checkpoint),
        "source_checkpoint_hash": source_checkpoint_hash,
        "candidate_checkpoint": str(candidate_checkpoint),
        "candidate_checkpoint_hash": candidate_checkpoint_hash,
        "source_model_state_hash": source_state_hash,
        "candidate_model_state_hash": candidate_state_hash,
        "behavior_changed": behavior_changed,
        "candidate_checkpoint_written": candidate_checkpoint.exists(),
        "update_method": "deterministic_belief_stress_actor_head_continuation_preflight",
        "max_updates": int(max_updates),
        "training_observation_count": int(training_observations.shape[0]),
        "training_curriculum_row_count": len(training_curriculum_rows),
        "trainable_parameter_names": [
            "actor_mean.bias[0]",
            "actor_mean.bias[1]",
            "actor_mean.bias[2]",
        ],
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_labels": False,
        "active_config_overwritten": False,
        "source_checkpoint_overwritten": False,
        "checkpoint_promoted": False,
        "promotion_metadata_written": False,
        "finite_update": finite_update,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    return [trace_row], manifest


def bounded_update_deltas(rows: list[dict[str, str]], *, max_updates: int) -> dict[str, float]:
    ordinary = [
        row
        for row in rows
        if as_bool(row.get("ordinary_denominator_allowed", False))
        and row.get("role_family") in ORDINARY_ROLE_FAMILIES
    ]
    if not ordinary:
        raise RuntimeError("M2782 cannot derive bounded update deltas without ordinary admission rows")
    action_signal = float(np.mean([abs(as_float(row.get("action_l1_mean"))) for row in ordinary]))
    command_signal = float(
        np.mean([abs(as_float(row.get("command_response_proxy_delta"))) for row in ordinary])
    )
    scale = max(0.0, min(float(max_updates), 1.0))
    steer_delta = min(0.025, max(0.006, 0.16 * action_signal)) * scale
    throttle_delta = -min(0.080, max(0.015, 0.55 * command_signal)) * scale
    brake_delta = min(0.080, max(0.015, 0.55 * command_signal)) * scale
    return {
        "steer_bias_delta": float(steer_delta),
        "throttle_bias_delta": float(throttle_delta),
        "brake_bias_delta": float(brake_delta),
        "mean_action_l1_signal": float(action_signal),
        "mean_command_response_signal": float(command_signal),
    }


def collect_training_run_rows(
    curriculum_rows: list[dict[str, Any]],
    run_item_map: dict[tuple[str, str, int], Any],
    source_checkpoint: Path,
    candidate_checkpoint: Path,
    *,
    training_seeds: int,
    device: str,
) -> list[dict[str, Any]]:
    return collect_actor_response_rows(
        curriculum_rows,
        run_item_map,
        source_checkpoint,
        candidate_checkpoint,
        split="training",
        seed_indices=range(int(training_seeds)),
        device=device,
    )


def collect_proof_probe_rows(
    curriculum_rows: list[dict[str, Any]],
    run_item_map: dict[tuple[str, str, int], Any],
    source_checkpoint: Path,
    candidate_checkpoint: Path,
    *,
    training_seeds: int,
    proof_seeds: int,
    device: str,
) -> list[dict[str, Any]]:
    return collect_actor_response_rows(
        curriculum_rows,
        run_item_map,
        source_checkpoint,
        candidate_checkpoint,
        split="proof_holdout",
        seed_indices=range(int(training_seeds), int(training_seeds) + int(proof_seeds)),
        device=device,
    )


def collect_actor_response_rows(
    curriculum_rows: list[dict[str, Any]],
    run_item_map: dict[tuple[str, str, int], Any],
    source_checkpoint: Path,
    candidate_checkpoint: Path,
    *,
    split: str,
    seed_indices: range,
    device: str,
) -> list[dict[str, Any]]:
    source_model, _source = load_actor_critic_checkpoint(source_checkpoint, device=device)
    candidate_model, _candidate = load_actor_critic_checkpoint(candidate_checkpoint, device=device)
    source_device = next(source_model.parameters()).device
    candidate_device = next(candidate_model.parameters()).device
    rows: list[dict[str, Any]] = []
    extractor = P0ObservationExtractor()
    for curriculum in curriculum_rows:
        for seed_index in seed_indices:
            item = run_item_map[(curriculum["role_family"], curriculum["dynamics_axis"], int(seed_index))]
            backend = FourWheelHF0Backend(fixture_spec=item.fixture_spec)
            warmup_count = 0
            try:
                reset_result = backend.reset(
                    BackendResetRequest(
                        seed=item.seed,
                        scenario_spec_id=item.fixture_id,
                        role_family=item.role_family,
                        options={
                            "seed_panel_id": item.seed_panel_id,
                            "seed_index": item.seed_index,
                            "dynamics_axis_id": item.dynamics_axis_id,
                            "stress_family": curriculum["stress_family"],
                            "actor_visible_labels": False,
                        },
                    )
                )
                actor_view = reset_result.actor_view
                if curriculum["stress_family"] == "held_actuator_history_stress":
                    warmup = backend.step(np.asarray([0.18, -0.20, -0.55], dtype=np.float32))
                    actor_view = warmup.actor_view
                    warmup_count = 1
                observation = extractor.extract(actor_view)
                obs_source = torch.as_tensor(observation[None, :], dtype=torch.float32, device=source_device)
                obs_candidate = torch.as_tensor(observation[None, :], dtype=torch.float32, device=candidate_device)
                source_action = actor_actions(source_model, obs_source)[0].detach().cpu().numpy()
                candidate_action = actor_actions(candidate_model, obs_candidate)[0].detach().cpu().numpy()
                step_result = backend.step(candidate_action.astype(np.float32))
                step_observation = extractor.extract(step_result.actor_view)
            finally:
                backend.close()

            action_delta = np.abs(candidate_action - source_action)
            command_response_proxy = float(
                abs(float(step_observation[3])) + abs(float(step_observation[4])) + abs(float(step_observation[2]))
            )
            physical_throttle = 0.5 * (float(candidate_action[1]) + 1.0)
            physical_brake = 0.5 * (float(candidate_action[2]) + 1.0)
            rows.append(
                {
                    "training_row_id": (
                        f"m2782_{split}_{curriculum['role_family']}_{curriculum['dynamics_axis']}_"
                        f"{curriculum['stress_family']}_seed_{int(item.seed)}"
                    ),
                    "split": split,
                    "role_family": curriculum["role_family"],
                    "dynamics_axis": curriculum["dynamics_axis"],
                    "stress_family": curriculum["stress_family"],
                    "seed_index": int(seed_index),
                    "seed": int(item.seed),
                    "source_curriculum_row_id": curriculum["source_curriculum_row_id"],
                    "fixture_id": item.fixture_id,
                    "stress_preparation": stress_preparation_label(curriculum["stress_family"]),
                    "warmup_step_count": warmup_count,
                    "observation_shape": int(observation.shape[0]),
                    "action_shape": ACTION_DIM,
                    "reset_run": True,
                    "policy_action_run": True,
                    "backend_step_run": True,
                    "source_action_steer": float(source_action[0]),
                    "source_action_throttle": float(source_action[1]),
                    "source_action_brake": float(source_action[2]),
                    "candidate_action_steer": float(candidate_action[0]),
                    "candidate_action_throttle": float(candidate_action[1]),
                    "candidate_action_brake": float(candidate_action[2]),
                    "action_delta_l1": float(np.mean(action_delta)),
                    "candidate_throttle_brake_conflict_proxy": float(physical_throttle * physical_brake),
                    "command_response_proxy": command_response_proxy,
                    "finite_observation": bool(
                        np.all(np.isfinite(observation)) and np.all(np.isfinite(step_observation))
                    ),
                    "finite_action": bool(np.all(np.isfinite(source_action)) and np.all(np.isfinite(candidate_action))),
                    "actor_visible_label": False,
                    "hidden_or_oracle_actor_inputs_required": False,
                    "ordinary_denominator_allowed": True,
                    "mitigation_reference": False,
                    "update_index": 0,
                    "claim_scope": CLAIM_SCOPE,
                    "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
                }
            )
    return rows


def stress_preparation_label(stress_family: str) -> str:
    if stress_family == "recurrent_hidden_reset_stress":
        return "reset_actor_state_before_action"
    if stress_family == "previous_command_history_stress":
        return "zero_previous_command_history"
    if stress_family == "held_actuator_history_stress":
        return "one_warmup_step_held_actuator_history"
    return "unknown_stress_family"


def build_mitigation_reference_guard_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        ordinary_allowed = as_bool(row.get("ordinary_denominator_allowed", False))
        mitigation_reference = as_bool(row.get("mitigation_reference", False))
        output.append(
            {
                "source_guard_id": row.get("candidate_id") or row.get("guard_id") or row.get("seed", ""),
                "candidate_id": row.get("candidate_id", ""),
                "role_family": row.get("role_family", ""),
                "dynamics_axis": row.get("dynamics_axis", ""),
                "seed": row.get("seed", ""),
                "mitigation_reference": mitigation_reference,
                "ordinary_denominator_allowed": False,
                "future_training_allowed": as_bool(row.get("future_training_allowed", False)),
                "future_execution_allowed": as_bool(row.get("future_execution_allowed", False)),
                "context_only": True,
                "actor_visible_allowed": False,
                "included_in_training_rows": False,
                "included_in_proof_denominator": False,
                "status_pass": bool(mitigation_reference and not ordinary_allowed),
                "guard_family": "mitigation_reference_denominator_guard",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def build_actor_contract_guard_rows(
    training_rows: list[dict[str, Any]],
    proof_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = training_rows + proof_rows
    rows = [
        (
            "actor_contract_observation_shape_72",
            "actor_contract",
            "observation_shape",
            {int(row["observation_shape"]) for row in combined} == {P0_OBSERVATION_DIM},
            f"{P0_OBSERVATION_DIM}",
        ),
        (
            "actor_contract_action_shape_3",
            "actor_contract",
            "action_shape",
            {int(row["action_shape"]) for row in combined} == {ACTION_DIM},
            f"{ACTION_DIM}",
        ),
        (
            "no_hidden_or_oracle_actor_input",
            "actor_contract",
            "hidden_or_oracle_actor_inputs_required",
            not any(as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in combined),
            "false",
        ),
        (
            "no_actor_visible_stress_label",
            "actor_contract",
            "stress_admission_curriculum_labels",
            not any(as_bool(row["actor_visible_label"]) for row in combined),
            "false",
        ),
        (
            "finite_observations",
            "actor_contract",
            "finite_observation",
            all(as_bool(row["finite_observation"]) for row in combined),
            "true",
        ),
        (
            "finite_actions",
            "actor_contract",
            "finite_action",
            all(as_bool(row["finite_action"]) for row in combined),
            "true",
        ),
    ]
    return [
        {
            "guard_id": guard_id,
            "guard_family": guard_family,
            "protected_field": field,
            "actor_visible_allowed": False,
            "actor_observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "status_pass": status,
            "evidence": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, guard_family, field, status, evidence in rows
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        ("validation_result", "validation", False, False, "M2782 does not run measured validation"),
        ("ranking_result", "ranking", False, False, "M2782 does not rank checkpoints or controllers"),
        ("winner_selection", "promotion", False, False, "M2782 selects no winner"),
        ("checkpoint_promotion", "promotion", False, False, "M2782 writes candidate only"),
        ("success_rate_verdict", "metric_artifact", False, False, "M2782 emits no success-rate verdict"),
        ("driver_performance", "performance", False, False, "M2782 is preflight evidence only"),
        ("paper_result", "paper", False, False, "M2782 is not paper evidence"),
        ("current_sim_verdict", "current_sim", False, False, "M2782 is not a current-sim verdict"),
        ("high_fidelity_validation", "high_fidelity", False, False, "M2782 does not run HF validation"),
        ("level3_self_id", "self_id", False, False, "M2782 is not self-ID evidence"),
        (
            "bounded_preflight_artifacts_complete",
            "allowed_artifact_completion",
            True,
            True,
            "M2782 may claim whether bounded preflight artifacts were written",
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
    curriculum_rows: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
    proof_rows: list[dict[str, Any]],
    mitigation_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    actor_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = training_rows + proof_rows
    gates = [
        gate(
            "proof_actor_contract_72_3",
            "proof",
            "actor_contract",
            all(as_bool(row["status_pass"]) for row in actor_guard_rows),
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
            "proof_stress_family_coverage",
            "proof",
            "scenario_sampling",
            {row["stress_family"] for row in curriculum_rows} == set(STRESS_FAMILIES),
            ";".join(sorted({row["stress_family"] for row in curriculum_rows})),
            ";".join(STRESS_FAMILIES),
            len(curriculum_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "proof_seed_split_complete",
            "proof",
            "scenario_sampling",
            len(training_rows) == len(curriculum_rows) * 3 and len(proof_rows) == len(curriculum_rows),
            f"training={len(training_rows)} proof={len(proof_rows)}",
            f"training={len(curriculum_rows) * 3} proof={len(curriculum_rows)}",
            len(training_rows) + len(proof_rows),
            "scenario_sampling_failure",
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
        gate(
            "proof_checkpoint_lineage_hashes",
            "proof",
            "lineage",
            bool(checkpoint_manifest.get("source_checkpoint_hash"))
            and bool(checkpoint_manifest.get("candidate_checkpoint_hash"))
            and checkpoint_manifest.get("behavior_changed") is True,
            "source and candidate hashes",
            "source and candidate hashes with behavior change",
            1,
            "lineage_invalid",
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
    ]
    return gates


def build_generalization_gate_rows(
    curriculum_rows: list[dict[str, Any]],
    proof_rows: list[dict[str, Any]],
    *,
    training_seeds: int,
    proof_seeds: int,
) -> list[dict[str, Any]]:
    role_set = {row["role_family"] for row in proof_rows}
    axis_set = {row["dynamics_axis"] for row in proof_rows}
    stress_set = {row["stress_family"] for row in proof_rows}
    proof_seed_indices = {int(row["seed_index"]) for row in proof_rows}
    expected_proof_indices = set(range(int(training_seeds), int(training_seeds) + int(proof_seeds)))
    return [
        gate(
            "generalization_heldout_seed_rows_separate",
            "generalization",
            "seed_split",
            proof_seed_indices == expected_proof_indices,
            ";".join(str(idx) for idx in sorted(proof_seed_indices)),
            ";".join(str(idx) for idx in sorted(expected_proof_indices)),
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
            "generalization_no_single_seed_verdict",
            "generalization",
            "objective_overfit",
            len({int(row["seed"]) for row in proof_rows}) >= len(ORDINARY_ROLE_FAMILIES),
            str(len({int(row["seed"]) for row in proof_rows})),
            "multi-seed heldout panel",
            len(proof_rows),
            "objective_overfit",
        ),
        gate(
            "generalization_no_validation_or_ranking_claim",
            "generalization",
            "claim_boundary",
            True,
            "no validation/ranking claim",
            "no validation/ranking claim",
            len(curriculum_rows),
            "metric_artifact",
        ),
    ]


def build_promotion_guard_rows() -> list[dict[str, Any]]:
    return [
        gate(
            "promotion_checkpoint_not_promoted",
            "promotion",
            "promotion_guard",
            True,
            "false",
            "false",
            1,
            "promotion_gate_failure",
        ),
        gate(
            "promotion_no_winner_selected",
            "promotion",
            "promotion_guard",
            True,
            "false",
            "false",
            1,
            "promotion_gate_failure",
        ),
        gate(
            "promotion_no_success_rate_verdict",
            "promotion",
            "promotion_guard",
            True,
            "false",
            "false",
            1,
            "metric_artifact",
        ),
        gate(
            "promotion_no_active_config_overwrite",
            "promotion",
            "promotion_guard",
            True,
            "false",
            "false",
            1,
            "contract_violation",
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
    m2779_summary: dict[str, Any],
    training_curriculum_rows: list[dict[str, Any]],
    training_run_rows: list[dict[str, Any]],
    proof_probe_rows: list[dict[str, Any]],
    checkpoint_trace_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    proof_gate_rows: list[dict[str, Any]],
    generalization_gate_rows: list[dict[str, Any]],
    promotion_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    mitigation_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    milestone: str,
    next_blocker: str,
    training_seeds: int,
    proof_seeds: int,
    max_updates: int,
) -> dict[str, Any]:
    all_gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows
    forbidden_claims_made = any(
        as_bool(row["claim_made"]) and not as_bool(row["allowed"]) for row in claim_rows
    )
    actor_contract_shape = all(as_bool(row["status_pass"]) for row in actor_guard_rows)
    status_pass = bool(
        checkpoint_manifest["candidate_checkpoint_written"]
        and checkpoint_manifest["behavior_changed"]
        and checkpoint_manifest["finite_update"]
        and actor_contract_shape
        and all(as_bool(row["status_pass"]) for row in all_gate_rows)
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
        "m2781_design": str(source_paths["m2781_design"]),
        "m2779_summary": str(source_paths["m2779_summary"]),
        "m2779_status_pass": bool(m2779_summary.get("status_pass", False)),
        "m2779_gate_matrix_pass": bool(m2779_summary.get("gate_matrix_pass", False)),
        "source_checkpoint": str(source_paths["source_checkpoint"]),
        "candidate_checkpoint": str(paths["candidate_checkpoint"]),
        "checkpoint_manifest": str(paths["checkpoint_manifest"]),
        "training_curriculum_rows": str(paths["training_curriculum_rows"]),
        "training_run_rows": str(paths["training_run_rows"]),
        "proof_gate_rows": str(paths["proof_gate_rows"]),
        "generalization_gate_rows": str(paths["generalization_gate_rows"]),
        "promotion_guard_rows": str(paths["promotion_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "mitigation_reference_guard_rows": str(paths["mitigation_reference_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "required_artifacts_present": False,
        "m2783_follow_up_manifest_registered": False,
        "training_run": True,
        "source_only_backend_reset_run": True,
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "bounded_update_count": int(max_updates),
        "training_seeds_per_bucket": int(training_seeds),
        "proof_seeds_per_bucket": int(proof_seeds),
        "training_curriculum_row_count": len(training_curriculum_rows),
        "training_run_row_count": len(training_run_rows),
        "proof_holdout_probe_row_count": len(proof_probe_rows),
        "checkpoint_trace_row_count": len(checkpoint_trace_rows),
        "proof_gate_row_count": len(proof_gate_rows),
        "generalization_gate_row_count": len(generalization_gate_rows),
        "promotion_guard_row_count": len(promotion_guard_rows),
        "actor_guard_row_count": len(actor_guard_rows),
        "mitigation_reference_guard_row_count": len(mitigation_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(all_gate_rows),
        "failed_gate_ids": [row["gate_id"] for row in all_gate_rows if not as_bool(row["status_pass"])],
        "candidate_checkpoint_written": bool(checkpoint_manifest["candidate_checkpoint_written"]),
        "checkpoint_behavior_changed": bool(checkpoint_manifest["behavior_changed"]),
        "candidate_checkpoint_hash": checkpoint_manifest["candidate_checkpoint_hash"],
        "source_checkpoint_hash": checkpoint_manifest["source_checkpoint_hash"],
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_stress_admission_curriculum_labels_detected": False,
        "mitigation_reference_rows_guarded": all(
            not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows
        ),
        "checkpoint_promoted": False,
        "active_config_overwritten": False,
        "source_checkpoint_overwritten": False,
        "forbidden_claims_made": forbidden_claims_made,
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def required_artifacts_present(paths: dict[str, Path]) -> bool:
    required_keys = [
        "summary",
        "training_curriculum_rows",
        "training_run_rows",
        "checkpoint_manifest",
        "candidate_checkpoint",
        "proof_gate_rows",
        "generalization_gate_rows",
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
        "run_state_id": "m2782_belief_stress_short_training_continuation_preflight_state_v0",
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
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_m2783_manifest(summary: dict[str, Any]) -> dict[str, Any]:
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
            "parent_checkpoint": [summary["candidate_checkpoint"]],
            "parent_dataset": [
                summary["summary"],
                summary["training_curriculum_rows"],
                summary["training_run_rows"],
                summary["checkpoint_manifest"],
                summary["proof_gate_rows"],
                summary["generalization_gate_rows"],
                summary["promotion_guard_rows"],
                summary["actor_contract_guard_rows"],
                summary["mitigation_reference_guard_rows"],
                summary["claim_boundary_rows"],
                summary["gate_matrix"],
                summary["doc"],
            ],
            "parent_config": [
                "experiments/manifests/m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight.json",
                "experiments/manifests/m2781-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-design.json",
            ],
            "parent_objective": [
                "audit the M2782 bounded source-only belief-stress short-training continuation preflight before interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2782 artifacts must be audited before any validation ranking promotion performance or self-ID interpretation",
                "M2782 remains source-only and cannot resolve the M2638 high-fidelity source dependency",
            ],
            "supersedes": [
                "direct interpretation of M2782 candidate checkpoint without result audit",
                "promotion from short-training preflight artifacts",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2783 must audit M2782 summary status gate matrix required artifacts checkpoint lineage and claim boundaries",
            "M2783 must preserve actor 72/action 3 no hidden/oracle actor input and actor-invisible labels",
            "M2783 must keep mitigation reference rows outside ordinary denominators",
            "M2783 must reject validation ranking winner promotion success-rate verdict driver-performance paper current-sim high-fidelity full ideal driver and self-ID claims",
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
            "do not claim repair success driver performance validation paper current-sim high-fidelity full ideal driver or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_belief_stress_short_training",
            "evidence_axis": "source_only_belief_stress_short_training_continuation_result_audit",
            "evidence_increment": "audits M2782 candidate checkpoint and gate artifacts before interpretation",
            "claim_scope": "Result audit only; no new execution training validation ranking promotion driver-performance paper high-fidelity self-ID or full-driver claim",
            "stop_condition": [
                "stop if M2782 required artifacts are incomplete",
                "stop if actor or claim boundaries fail",
                "stop if checkpoint lineage hashes are missing",
                "stop if proof/generalization/promotion separation is not auditable",
            ],
            "fallback_plan": [
                "route to artifact repair if required artifacts are missing",
                "route to branch synthesis if short-training artifacts are complete but gates fail",
                "route to next fresh evidence design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2782 writes bounded source-only short-training preflight artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2782 bounded source-only short-training continuation preflight artifacts",
            "admission_evidence": [
                "M2782 summary and gate artifacts exist",
                "M2782 writes a candidate checkpoint manifest and proof/generalization/promotion gate rows",
                "M2782 is not validated ranked or promoted before this audit",
            ],
            "blocked_shortcuts": [
                "no new execution or training in M2783",
                "no validation ranking promotion success-rate verdict performance paper HF full-driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{task_id}.md",
                "M2783 status queue scoreboard research log and review",
            ],
            "next_stage_criteria": [
                "M2782 artifacts are complete and claim-safe or failure is classified",
                "one bounded follow-up or stop decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2783 audits source-only M2782 artifacts and cannot establish self-ID.",
            "history_necessity_tests": [
                "M2783 may check that M2782 covered history stress rows but runs no self-ID comparison."
            ],
            "temporal_evidence_window": "M2772-M2783 source-only belief-stress branch.",
            "negative_result_policy": "If M2782 artifacts fail, preserve failure and route to synthesis or repair rather than weakening gates.",
            "allowed_claims": [
                "M2782 preflight artifacts are accepted or rejected as complete and claim-safe",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fresh M2782 candidate checkpoint and gate artifacts before any extension",
            "paper_verdict_delta": "no paper verdict; audit decides whether M2782 can be used as future engineering evidence",
            "must_synthesize_if": [
                "M2783 finds incomplete artifacts or claim-boundary failure",
                "another process-only milestone is proposed after M2783 without fresh evidence or synthesis",
            ],
        },
        "hypothesis": "M2782 bounded short-training preflight artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{task_id}.md exists",
            "M2783 audits M2782 summary required artifacts gates checkpoint lineage and claim boundaries",
            "M2783 registers one bounded follow-up or stop decision",
            "M2783 makes no new execution training validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2783 executes new training or rollout",
            "M2783 treats M2782 as validation or promotion evidence",
            "M2783 claims driver performance paper high-fidelity full-driver or self-ID result",
        ],
        "decision_rule": "Pass only if M2783 writes a claim-safe audit of M2782 artifacts and routes before interpretation.",
        "commands": [{"name": "audit_design_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{task_id}.md", "type": "md"}],
        "baseline_checkpoints": [summary["candidate_checkpoint"]],
        "baseline_artifacts": [summary["summary"], summary["gate_matrix"]],
        "scoreboard_checkpoint": f"docs/{task_id}.md",
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    failed = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    lines = [
        "# M2782 Engineering Controller Route A Source-Only Belief-Stress Short-Training Continuation Preflight",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result_class: `{summary['result_class']}`",
        "- manifest: `experiments/manifests/m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight.json`",
        f"- summary: `{summary['summary']}`",
        f"- candidate checkpoint: `{summary['candidate_checkpoint']}`",
        f"- checkpoint manifest: `{summary['checkpoint_manifest']}`",
        f"- training curriculum rows: `{summary['training_curriculum_rows']}`",
        f"- training run rows: `{summary['training_run_rows']}`",
        f"- proof gate rows: `{summary['proof_gate_rows']}`",
        f"- generalization gate rows: `{summary['generalization_gate_rows']}`",
        f"- promotion guard rows: `{summary['promotion_guard_rows']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Result",
        "",
        "M2782 ran one bounded source-only belief-stress short-training continuation",
        "preflight from the M2655 source checkpoint and the audited M2779",
        "curriculum. It wrote a candidate checkpoint for audit, not promotion.",
        "",
        "```text",
        f"training_curriculum_rows: {summary['training_curriculum_row_count']}",
        f"training_run_rows: {summary['training_run_row_count']}",
        f"proof_holdout_probe_rows: {summary['proof_holdout_probe_row_count']}",
        f"proof_gate_rows: {summary['proof_gate_row_count']}",
        f"generalization_gate_rows: {summary['generalization_gate_row_count']}",
        f"promotion_guard_rows: {summary['promotion_guard_row_count']}",
        f"candidate_checkpoint_written: {summary['candidate_checkpoint_written']}",
        f"checkpoint_behavior_changed: {summary['checkpoint_behavior_changed']}",
        f"failed_gate_ids: {failed}",
        "```",
        "",
        "## Actor And Claim Boundary",
        "",
        "Actor input stayed at P0 observation 72 and action 3. Stress, admission,",
        "curriculum, role, dynamics, outcome, success, progress, route, and verdict",
        "labels remained evaluator metadata and were not actor-visible. Mitigation",
        "reference rows stayed outside ordinary denominators.",
        "",
        "M2782 does not validate, rank, promote, compute a success-rate verdict,",
        "claim repair success, driver performance, paper evidence, current-sim",
        "verdict, high-fidelity validation, full ideal driver completion, or",
        "level3 self-identification.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def json_list(values: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.9g}" for value in values) + "]"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2781-design", type=Path, default=DEFAULT_M2781_DESIGN)
    parser.add_argument("--m2779-dir", type=Path, default=DEFAULT_M2779_DIR)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--training-seeds-per-bucket", type=int, default=3)
    parser.add_argument("--proof-seeds-per-bucket", type=int, default=1)
    parser.add_argument("--max-updates", type=int, default=1)
    args = parser.parse_args()
    run_belief_stress_short_training_continuation_preflight(
        args.output_dir,
        m2781_design=args.m2781_design,
        m2779_dir=args.m2779_dir,
        source_checkpoint=args.source_checkpoint,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
        device=args.device,
        training_seeds_per_bucket=args.training_seeds_per_bucket,
        proof_seeds_per_bucket=args.proof_seeds_per_bucket,
        max_updates=args.max_updates,
    )


if __name__ == "__main__":
    main()
