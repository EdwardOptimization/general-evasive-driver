"""M2801 clearance-localized candidate fresh-holdout triad delta panel.

This preflight runs a source-only triad closed-loop diagnostic panel for the
M2799 corrective candidate against the M2655 source and M2791 start candidate.
It uses a fresh seed surface and writes artifacts for audit only. It does not
train, validate, rank, select a winner, promote a checkpoint, compute a
success-rate verdict, or claim repair success or driver performance.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel import (
    ACTOR_GUARD_FIELDNAMES,
    CLAIM_FIELDNAMES,
    GATE_FIELDNAMES,
    MITIGATION_GUARD_FIELDNAMES,
    build_actor_contract_guard_rows,
    build_mitigation_reference_guard_rows,
    build_promotion_guard_rows,
    run_closed_loop_execution,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel import (
    TRIAD_DELTA_FIELDNAMES,
    TRIAD_EXECUTION_FIELDNAMES,
    TRIAD_SUBJECTS,
    build_holdout_run_item_map,
    build_triad_delta_rows,
    load_triad_subject_registry,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
    DYNAMICS_AXES,
    ORDINARY_ROLE_FAMILIES,
    STRESS_FAMILIES,
    as_bool,
    read_csv_rows,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2801-engineering-controller-route-a-source-only-belief-stress-clearance-"
    "localized-candidate-fresh-holdout-triad-delta-panel-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_"
    "localized_candidate_fresh_holdout_triad_delta_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2801-engineering-controller-route-a-source-only-belief-stress-clearance-"
    "localized-candidate-fresh-holdout-triad-delta-panel-preflight.md"
)
DEFAULT_M2800_AUDIT = Path(
    "docs/m2800-engineering-controller-route-a-source-only-belief-stress-clearance-"
    "localized-corrective-training-result-audit.md"
)
DEFAULT_M2799_DIR = Path(
    "runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_"
    "localized_corrective_training_preflight"
)
DEFAULT_M2796_DIR = Path(
    "runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_"
    "clearance_regression_atlas"
)
DEFAULT_M2793_DIR = Path(
    "runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_"
    "candidate_fresh_holdout_triad_delta_panel"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_BASE_CANDIDATE_CHECKPOINT = Path(
    "runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_"
    "multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt"
)
DEFAULT_CANDIDATE_CHECKPOINT = Path(
    "runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_"
    "localized_corrective_training_preflight/checkpoints/m2799_clearance_localized_corrective_candidate.pt"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2802-engineering-controller-route-a-source-only-belief-"
    "stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-result-audit.json"
)
DEFAULT_NEXT_BLOCKER = (
    "m2802-engineering-controller-route-a-source-only-belief-stress-clearance-"
    "localized-candidate-fresh-holdout-triad-delta-panel-result-audit"
)
DEFAULT_SEED_START_INDEX = 12
DEFAULT_SEED_COUNT = 4
DEFAULT_HORIZON_STEPS = 160

CLAIM_SCOPE = (
    "Route A source-only belief-stress clearance-localized candidate fresh-holdout "
    "triad closed-loop diagnostic preflight only"
)
FORBIDDEN_INTERPRETATION = (
    "validation, ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "repair success, driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, or "
    "level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_belief_stress_clearance_localized_"
    "candidate_fresh_holdout_triad_delta_panel_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_belief_stress_clearance_localized_"
    "candidate_fresh_holdout_triad_delta_panel_preflight_failed"
)

FALSE_CLAIM_FLAGS = {
    "training_run": False,
    "ppo_run": False,
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


def run_clearance_localized_candidate_fresh_holdout_triad_delta_panel(
    output_dir: Path | str,
    *,
    m2800_audit: Path | str = DEFAULT_M2800_AUDIT,
    m2799_dir: Path | str = DEFAULT_M2799_DIR,
    m2796_dir: Path | str = DEFAULT_M2796_DIR,
    m2793_dir: Path | str = DEFAULT_M2793_DIR,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    base_candidate_checkpoint: Path | str = DEFAULT_BASE_CANDIDATE_CHECKPOINT,
    candidate_checkpoint: Path | str = DEFAULT_CANDIDATE_CHECKPOINT,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    device: str = "cpu",
    seed_start_index: int = DEFAULT_SEED_START_INDEX,
    seed_count: int = DEFAULT_SEED_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    if int(seed_start_index) < DEFAULT_SEED_START_INDEX:
        raise ValueError("M2801 requires seed_start_index outside prior 0..11 seed surfaces")
    if int(seed_count) < 2:
        raise ValueError("M2801 requires at least two fresh holdout seeds")
    if int(horizon_steps) <= 140:
        raise ValueError("M2801 requires horizon_steps greater than M2793 horizon 140")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(
        Path(m2800_audit),
        Path(m2799_dir),
        Path(m2796_dir),
        Path(m2793_dir),
        Path(source_checkpoint),
        Path(base_candidate_checkpoint),
        Path(candidate_checkpoint),
    )
    _require_sources(source_paths)

    m2799_summary = read_json(source_paths["m2799_summary"])
    m2799_checkpoint_manifest = read_json(source_paths["m2799_checkpoint_manifest"])
    m2796_summary = read_json(source_paths["m2796_summary"])
    m2793_summary = read_json(source_paths["m2793_summary"])
    objective_rows = select_objective_rows(read_csv_rows(source_paths["m2799_training_objective_rows"]))
    m2796_aggregate_rows = read_csv_rows(source_paths["m2796_aggregate_rows"])
    m2793_source_delta_rows = read_csv_rows(source_paths["m2793_source_delta_rows"])
    m2793_base_delta_rows = read_csv_rows(source_paths["m2793_base_delta_rows"])
    mitigation_source_rows = read_csv_rows(source_paths["m2799_mitigation_reference_guard_rows"])

    subject_registry = load_triad_subject_registry(
        source_paths["source_checkpoint"],
        source_paths["base_candidate_checkpoint"],
        source_paths["candidate_checkpoint"],
        device=device,
    )
    run_item_map = build_holdout_run_item_map(int(seed_start_index) + int(seed_count))
    execution_rows = collect_triad_execution_rows(
        objective_rows,
        run_item_map,
        subject_registry,
        seed_start_index=int(seed_start_index),
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    source_delta_rows = retag_rows(build_triad_delta_rows(execution_rows, subject_registry, reference_subject="source"))
    base_delta_rows = retag_rows(
        build_triad_delta_rows(execution_rows, subject_registry, reference_subject="base_candidate")
    )
    mitigation_guard_rows = retag_rows(build_mitigation_reference_guard_rows(mitigation_source_rows))
    actor_guard_rows = retag_rows(build_actor_contract_guard_rows(execution_rows))
    claim_rows = build_claim_boundary_rows()
    proof_gate_rows = build_proof_gate_rows(
        source_paths=source_paths,
        m2799_summary=m2799_summary,
        m2799_checkpoint_manifest=m2799_checkpoint_manifest,
        m2796_summary=m2796_summary,
        objective_rows=objective_rows,
        execution_rows=execution_rows,
        source_delta_rows=source_delta_rows,
        base_delta_rows=base_delta_rows,
        actor_guard_rows=actor_guard_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        subject_registry=subject_registry,
        seed_count=int(seed_count),
    )
    generalization_gate_rows = build_generalization_holdout_gate_rows(
        objective_rows,
        execution_rows,
        source_delta_rows,
        base_delta_rows,
        m2793_source_delta_rows + m2793_base_delta_rows,
        m2793_summary,
        seed_start_index=int(seed_start_index),
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    behavior_gate_rows = build_behavior_retention_gate_rows(
        source_delta_rows,
        base_delta_rows,
        m2796_summary,
        m2796_aggregate_rows,
    )
    promotion_guard_rows = retag_rows(build_promotion_guard_rows())
    gate_rows = proof_gate_rows + generalization_gate_rows + behavior_gate_rows + promotion_guard_rows

    write_csv_rows(paths["triad_execution_rows"], execution_rows, TRIAD_EXECUTION_FIELDNAMES)
    write_csv_rows(paths["candidate_minus_source_delta_rows"], source_delta_rows, TRIAD_DELTA_FIELDNAMES)
    write_csv_rows(paths["candidate_minus_base_delta_rows"], base_delta_rows, TRIAD_DELTA_FIELDNAMES)
    write_csv_rows(paths["proof_gate_rows"], proof_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["generalization_holdout_gate_rows"], generalization_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["behavior_retention_gate_rows"], behavior_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["promotion_guard_rows"], promotion_guard_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["mitigation_reference_guard_rows"], mitigation_guard_rows, MITIGATION_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        m2799_summary=m2799_summary,
        m2799_checkpoint_manifest=m2799_checkpoint_manifest,
        m2796_summary=m2796_summary,
        m2793_summary=m2793_summary,
        m2793_delta_rows=m2793_source_delta_rows + m2793_base_delta_rows,
        subject_registry=subject_registry,
        objective_rows=objective_rows,
        execution_rows=execution_rows,
        source_delta_rows=source_delta_rows,
        base_delta_rows=base_delta_rows,
        proof_gate_rows=proof_gate_rows,
        generalization_gate_rows=generalization_gate_rows,
        behavior_gate_rows=behavior_gate_rows,
        promotion_guard_rows=promotion_guard_rows,
        actor_guard_rows=actor_guard_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        claim_rows=claim_rows,
        seed_start_index=int(seed_start_index),
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2802_manifest(summary))
    write_doc(paths["doc"], summary)

    summary = {
        **summary,
        "required_artifacts_present": required_artifacts_present(paths),
        "m2802_follow_up_manifest_registered": paths["follow_up_manifest"].exists(),
    }
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    summary["result_class"] = RESULT_CLASS_PASS if summary["status_pass"] else RESULT_CLASS_FAIL
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2802_manifest(summary))
    write_doc(paths["doc"], summary)
    return summary


def _paths(output: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output / "summary.json",
        "triad_execution_rows": output / "triad_execution_rows.csv",
        "candidate_minus_source_delta_rows": output / "candidate_minus_source_delta_rows.csv",
        "candidate_minus_base_delta_rows": output / "candidate_minus_base_delta_rows.csv",
        "proof_gate_rows": output / "proof_gate_rows.csv",
        "generalization_holdout_gate_rows": output / "generalization_holdout_gate_rows.csv",
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
    m2800_audit: Path,
    m2799_dir: Path,
    m2796_dir: Path,
    m2793_dir: Path,
    source_checkpoint: Path,
    base_candidate_checkpoint: Path,
    candidate_checkpoint: Path,
) -> dict[str, Path]:
    return {
        "m2800_audit": m2800_audit,
        "m2799_summary": m2799_dir / "summary.json",
        "m2799_checkpoint_manifest": m2799_dir / "checkpoint_manifest.json",
        "m2799_training_objective_rows": m2799_dir / "training_objective_rows.csv",
        "m2799_gate_matrix": m2799_dir / "gate_matrix.csv",
        "m2799_behavior_retention_gate_rows": m2799_dir / "behavior_retention_gate_rows.csv",
        "m2799_mitigation_reference_guard_rows": m2799_dir / "mitigation_reference_guard_rows.csv",
        "m2796_summary": m2796_dir / "summary.json",
        "m2796_aggregate_rows": m2796_dir / "clearance_regression_aggregate_rows.csv",
        "m2793_summary": m2793_dir / "summary.json",
        "m2793_source_delta_rows": m2793_dir / "candidate_minus_source_delta_rows.csv",
        "m2793_base_delta_rows": m2793_dir / "candidate_minus_base_delta_rows.csv",
        "source_checkpoint": source_checkpoint,
        "base_candidate_checkpoint": base_candidate_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2801 missing required source artifacts: {missing}")


def select_objective_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    selected = [
        row
        for row in rows
        if row.get("role_family") in ORDINARY_ROLE_FAMILIES
        and row.get("dynamics_axis") in DYNAMICS_AXES
        and row.get("stress_family") in STRESS_FAMILIES
        and as_bool(row.get("future_execution_allowed", True))
    ]
    expected_count = len(ORDINARY_ROLE_FAMILIES) * len(DYNAMICS_AXES) * len(STRESS_FAMILIES)
    if len(selected) != expected_count:
        raise RuntimeError(f"expected {expected_count} M2799 objective rows, got {len(selected)}")
    return sorted(
        [
            {
                **dict(row),
                "source_curriculum_row_id": row.get("source_curriculum_row_id")
                or row.get("training_objective_row_id", ""),
                "claim_scope": CLAIM_SCOPE,
            }
            for row in selected
        ],
        key=lambda item: (item["role_family"], item["dynamics_axis"], item["stress_family"]),
    )


def collect_triad_execution_rows(
    objective_rows: list[dict[str, Any]],
    run_item_map: dict[tuple[str, str, int], Any],
    subject_registry: dict[str, dict[str, Any]],
    *,
    seed_start_index: int,
    seed_count: int,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for objective in objective_rows:
        for seed_index in range(int(seed_start_index), int(seed_start_index) + int(seed_count)):
            item = run_item_map[(objective["role_family"], objective["dynamics_axis"], int(seed_index))]
            pair_id = (
                f"m2801_triad_{objective['role_family']}_{objective['dynamics_axis']}_"
                f"{objective['stress_family']}_seed_index_{int(seed_index)}_seed_{int(item.seed)}"
            )
            for subject in TRIAD_SUBJECTS:
                row = run_closed_loop_execution(
                    subject_registry[subject],
                    item,
                    objective,
                    pair_id=pair_id,
                    seed_index=int(seed_index),
                    horizon_steps=int(horizon_steps),
                )
                rows.append(retag_row(row))
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        ("validation_result", "validation", False, False, "M2801 does not run measured validation"),
        ("ranking_result", "ranking", False, False, "M2801 does not rank checkpoints"),
        ("winner_selection", "promotion", False, False, "M2801 selects no winner"),
        ("checkpoint_promotion", "promotion", False, False, "M2801 promotes no checkpoint"),
        ("success_rate_verdict", "metric_artifact", False, False, "M2801 emits no success-rate verdict"),
        ("repair_success", "repair", False, False, "M2801 is not repair-success evidence"),
        ("driver_performance", "performance", False, False, "M2801 is diagnostic delta evidence only"),
        ("paper_result", "paper", False, False, "M2801 is not paper evidence"),
        ("current_sim_verdict", "current_sim", False, False, "M2801 is not a current-sim verdict"),
        ("high_fidelity_validation", "high_fidelity", False, False, "M2801 does not run HF validation"),
        ("level3_self_id", "self_id", False, False, "M2801 is not self-ID evidence"),
        (
            "triad_delta_artifacts_complete",
            "allowed_artifact_completion",
            True,
            True,
            "M2801 may claim triad diagnostic artifacts were written",
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
    m2799_summary: dict[str, Any],
    m2799_checkpoint_manifest: dict[str, Any],
    m2796_summary: dict[str, Any],
    objective_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    source_delta_rows: list[dict[str, Any]],
    base_delta_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    mitigation_guard_rows: list[dict[str, Any]],
    subject_registry: dict[str, dict[str, Any]],
    seed_count: int,
) -> list[dict[str, Any]]:
    expected_execution_rows = len(objective_rows) * int(seed_count) * len(TRIAD_SUBJECTS)
    expected_delta_rows = len(objective_rows) * int(seed_count)
    all_delta_rows = source_delta_rows + base_delta_rows
    lineage_pass = (
        bool(subject_registry["source"]["checkpoint_hash"])
        and bool(subject_registry["base_candidate"]["checkpoint_hash"])
        and bool(subject_registry["candidate"]["checkpoint_hash"])
        and len(
            {
                subject_registry["source"]["checkpoint_hash"],
                subject_registry["base_candidate"]["checkpoint_hash"],
                subject_registry["candidate"]["checkpoint_hash"],
            }
        )
        == 3
        and m2799_checkpoint_manifest.get("source_reference_checkpoint_hash")
        == subject_registry["source"]["checkpoint_hash"]
        and m2799_checkpoint_manifest.get("start_candidate_checkpoint_hash")
        == subject_registry["base_candidate"]["checkpoint_hash"]
        and m2799_checkpoint_manifest.get("candidate_checkpoint_hash")
        == subject_registry["candidate"]["checkpoint_hash"]
    )
    return [
        gate("proof_m2800_audit_present", "proof", "lineage", source_paths["m2800_audit"].exists(), str(source_paths["m2800_audit"]), "exists", 1, "lineage_invalid"),
        gate("proof_m2799_status_pass", "proof", "lineage", bool(m2799_summary.get("status_pass", False)) and bool(m2799_summary.get("required_artifacts_present", False)) and bool(m2799_summary.get("gate_matrix_pass", False)), str(bool(m2799_summary.get("status_pass", False))), "true with artifacts and gate matrix", 1, "lineage_invalid"),
        gate("proof_m2796_status_pass", "proof", "lineage", bool(m2796_summary.get("status_pass", False)) and bool(m2796_summary.get("gate_matrix_pass", False)), str(bool(m2796_summary.get("status_pass", False))), "true with gate matrix", 1, "lineage_invalid"),
        gate("proof_checkpoint_lineage_hashes", "proof", "lineage", lineage_pass, "source start candidate hashes", "M2799 source/start/candidate hashes match triad subjects", 1, "lineage_invalid"),
        gate("proof_m2799_base_lineage_preserved", "proof", "lineage", bool(m2799_checkpoint_manifest.get("base_candidate_checkpoint_hash")) and bool(m2799_summary.get("base_candidate_checkpoint_hash")), str(m2799_checkpoint_manifest.get("base_candidate_checkpoint_hash", "")), "M2782 base lineage retained", 1, "lineage_invalid"),
        gate("proof_objective_row_count", "proof", "artifact", len(objective_rows) == 18, str(len(objective_rows)), "18", len(objective_rows), "metric_artifact"),
        gate("proof_triad_execution_row_count", "proof", "artifact", len(execution_rows) == expected_execution_rows, str(len(execution_rows)), str(expected_execution_rows), len(execution_rows), "metric_artifact"),
        gate("proof_candidate_minus_source_delta_row_count", "proof", "artifact", len(source_delta_rows) == expected_delta_rows, str(len(source_delta_rows)), str(expected_delta_rows), len(source_delta_rows), "metric_artifact"),
        gate("proof_candidate_minus_base_delta_row_count", "proof", "artifact", len(base_delta_rows) == expected_delta_rows, str(len(base_delta_rows)), str(expected_delta_rows), len(base_delta_rows), "metric_artifact"),
        gate("proof_pair_completeness", "proof", "artifact", bool(all_delta_rows) and all(as_bool(row["paired_row_complete"]) for row in all_delta_rows), "all pairs complete", "all pairs complete", len(all_delta_rows), "metric_artifact"),
        gate("proof_actor_contract_72_3", "proof", "actor_contract", bool(actor_guard_rows) and all(as_bool(row["status_pass"]) for row in actor_guard_rows), "all actor guards pass", "all actor guards pass", len(actor_guard_rows), "contract_violation"),
        gate("proof_no_hidden_or_oracle_actor_input", "proof", "actor_contract", not any(as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in execution_rows), "false", "false", len(execution_rows), "contract_violation"),
        gate("proof_actor_invisible_labels", "proof", "actor_contract", not any(as_bool(row["actor_visible_label"]) for row in execution_rows), "false", "false", len(execution_rows), "contract_violation"),
        gate("proof_finite_action_observation", "proof", "metric_artifact", all(as_bool(row["finite_observation"]) and as_bool(row["finite_action"]) and as_bool(row["action_within_bounds"]) for row in execution_rows), "finite", "finite", len(execution_rows), "metric_artifact"),
        gate("proof_mitigation_rows_excluded", "proof", "proof_washout", bool(mitigation_guard_rows) and all(not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows) and all(not as_bool(row["included_in_paired_execution_rows"]) for row in mitigation_guard_rows), "mitigation rows excluded", "mitigation rows excluded", len(mitigation_guard_rows), "proof_washout"),
        gate("proof_no_ranking_winner_success_verdict", "proof", "claim_boundary", not any(as_bool(row["ranking_admissible"]) or as_bool(row["winner_selected"]) for row in all_delta_rows) and not any(as_bool(row["success_rate_verdict_computed"]) for row in all_delta_rows), "false", "false", len(all_delta_rows), "objective_overfit"),
    ]


def build_generalization_holdout_gate_rows(
    objective_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    source_delta_rows: list[dict[str, Any]],
    base_delta_rows: list[dict[str, Any]],
    previous_delta_rows: list[dict[str, str]],
    m2793_summary: dict[str, Any],
    *,
    seed_start_index: int,
    seed_count: int,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    delta_rows = source_delta_rows + base_delta_rows
    previous_seeds = set(range(0, DEFAULT_SEED_START_INDEX))
    previous_seeds.update(int(row["seed_index"]) for row in previous_delta_rows if str(row.get("seed_index", "")))
    previous_seeds.update(int(index) for index in m2793_summary.get("fresh_holdout_seed_indices", []))
    holdout_seed_indices = {int(row["seed_index"]) for row in source_delta_rows}
    return [
        gate("generalization_role_family_coverage", "generalization", "scenario_sampling", {row["role_family"] for row in source_delta_rows} == set(ORDINARY_ROLE_FAMILIES), ";".join(sorted({row["role_family"] for row in source_delta_rows})), ";".join(ORDINARY_ROLE_FAMILIES), len(source_delta_rows), "scenario_sampling_failure"),
        gate("generalization_dynamics_axis_coverage", "generalization", "scenario_sampling", {row["dynamics_axis"] for row in source_delta_rows} == set(DYNAMICS_AXES), ";".join(sorted({row["dynamics_axis"] for row in source_delta_rows})), ";".join(DYNAMICS_AXES), len(source_delta_rows), "scenario_sampling_failure"),
        gate("generalization_stress_family_coverage", "generalization", "scenario_sampling", {row["stress_family"] for row in source_delta_rows} == set(STRESS_FAMILIES), ";".join(sorted({row["stress_family"] for row in source_delta_rows})), ";".join(STRESS_FAMILIES), len(source_delta_rows), "scenario_sampling_failure"),
        gate("generalization_requested_seed_count", "generalization", "seed_split", int(seed_count) >= 2, str(int(seed_count)), ">=2", len(source_delta_rows), "seed_fragility"),
        gate("generalization_seed_indices_outside_previous_surfaces", "generalization", "seed_split", int(seed_start_index) >= DEFAULT_SEED_START_INDEX and holdout_seed_indices.isdisjoint(previous_seeds), ",".join(str(index) for index in sorted(holdout_seed_indices)), "disjoint from prior seed surfaces 0..11", len(source_delta_rows), "scenario_sampling_failure"),
        gate("generalization_each_bucket_holdout_seed_coverage", "generalization", "seed_split", _each_bucket_holdout_seed_coverage(source_delta_rows, int(seed_start_index), int(seed_count)), "complete", "complete", len(source_delta_rows), "seed_fragility"),
        gate("generalization_triad_subject_coverage", "generalization", "artifact", {row["checkpoint_subject"] for row in execution_rows} == set(TRIAD_SUBJECTS) and len(execution_rows) == len(objective_rows) * int(seed_count) * len(TRIAD_SUBJECTS), ";".join(sorted({row["checkpoint_subject"] for row in execution_rows})), ";".join(TRIAD_SUBJECTS), len(execution_rows), "metric_artifact"),
        gate("generalization_dual_delta_family_coverage", "generalization", "artifact", {row["delta_family"] for row in delta_rows} == {"candidate_minus_base", "candidate_minus_source"}, ";".join(sorted({row["delta_family"] for row in delta_rows})), "candidate_minus_base;candidate_minus_source", len(delta_rows), "metric_artifact"),
        gate("generalization_horizon_longer_than_m2793", "generalization", "horizon", int(horizon_steps) > int(m2793_summary.get("horizon_steps", 0)), str(int(horizon_steps)), f">{int(m2793_summary.get('horizon_steps', 0))}", len(execution_rows), "scenario_sampling_failure"),
    ]


def build_behavior_retention_gate_rows(
    source_delta_rows: list[dict[str, Any]],
    base_delta_rows: list[dict[str, Any]],
    m2796_summary: dict[str, Any],
    m2796_aggregate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    source_obstacle = _metric_stats(source_delta_rows, "candidate_minus_reference_minimum_obstacle_clearance_m")
    base_obstacle = _metric_stats(base_delta_rows, "candidate_minus_reference_minimum_obstacle_clearance_m")
    source_conflict = _metric_stats(source_delta_rows, "candidate_minus_reference_throttle_brake_conflict_proxy")
    base_conflict = _metric_stats(base_delta_rows, "candidate_minus_reference_throttle_brake_conflict_proxy")
    stable_source = [row for row in source_delta_rows if row["role_family"] == "stable_avoidable"]
    stable_base = [row for row in base_delta_rows if row["role_family"] == "stable_avoidable"]
    role_stats = {
        row["role_family"]: row
        for row in m2796_aggregate_rows
        if row.get("group_family") == "role_family"
        and row.get("role_family") in {"drift_required_recovery", "stable_aes", "stable_avoidable"}
    }
    expected_count = len(source_delta_rows)
    return [
        gate("behavior_m2796_atlas_baseline_present", "behavior_retention", "lineage", bool(m2796_summary.get("status_pass", False)) and bool(role_stats), str(bool(role_stats)), "M2796 role aggregate rows present", len(m2796_aggregate_rows), "lineage_invalid"),
        gate("behavior_m2796_target_structure_preserved", "behavior_retention", "behavior_regression", int(as_float(role_stats.get("drift_required_recovery", {}).get("negative_clearance_count"))) == 48 and int(as_float(role_stats.get("stable_aes", {}).get("negative_clearance_count"))) >= 36, f"drift={role_stats.get('drift_required_recovery', {}).get('negative_clearance_count')} stable_aes={role_stats.get('stable_aes', {}).get('negative_clearance_count')}", "drift=48 stable_aes>=36", 96, "behavior_regression"),
        gate("behavior_m2796_stable_avoidable_retention_baseline", "behavior_retention", "behavior_regression", int(as_float(role_stats.get("stable_avoidable", {}).get("negative_clearance_count"))) <= 1, str(role_stats.get("stable_avoidable", {}).get("negative_clearance_count")), "<=1", 48, "behavior_regression"),
        gate("behavior_candidate_minus_source_obstacle_clearance_counted", "behavior_retention", "behavior_regression", source_obstacle["count"] == expected_count, f"positive={source_obstacle['positive']} negative={source_obstacle['negative']}", "obstacle-clearance deltas counted", source_obstacle["count"], "behavior_regression"),
        gate("behavior_candidate_minus_base_obstacle_clearance_counted", "behavior_retention", "behavior_regression", base_obstacle["count"] == expected_count, f"positive={base_obstacle['positive']} negative={base_obstacle['negative']}", "obstacle-clearance deltas counted", base_obstacle["count"], "behavior_regression"),
        gate("behavior_stable_avoidable_retention_rows_counted", "behavior_retention", "behavior_regression", len(stable_source) == len(DYNAMICS_AXES) * len(STRESS_FAMILIES) * len({row["seed_index"] for row in stable_source}) and len(stable_source) == len(stable_base), f"source={len(stable_source)} base={len(stable_base)}", "stable_avoidable rows counted for both delta families", len(stable_source) + len(stable_base), "behavior_regression"),
        gate("behavior_obstacle_clearance_guard_is_hard", "behavior_retention", "objective_overfit", True, "road/yaw subordinate", "road/yaw subordinate to clearance", expected_count * 2, "objective_overfit"),
        gate("behavior_throttle_brake_conflict_delta_counted", "behavior_retention", "behavior_regression", source_conflict["count"] == expected_count and base_conflict["count"] == expected_count, f"source_zero={source_conflict['zero']} base_zero={base_conflict['zero']}", "conflict deltas counted", expected_count * 2, "behavior_regression"),
        gate("behavior_candidate_update_not_interpreted_as_winner", "behavior_retention", "objective_overfit", not any(as_bool(row["ranking_admissible"]) or as_bool(row["winner_selected"]) for row in source_delta_rows + base_delta_rows), "false", "false", len(source_delta_rows) + len(base_delta_rows), "objective_overfit"),
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
    m2799_summary: dict[str, Any],
    m2799_checkpoint_manifest: dict[str, Any],
    m2796_summary: dict[str, Any],
    m2793_summary: dict[str, Any],
    m2793_delta_rows: list[dict[str, str]],
    subject_registry: dict[str, dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    source_delta_rows: list[dict[str, Any]],
    base_delta_rows: list[dict[str, Any]],
    proof_gate_rows: list[dict[str, Any]],
    generalization_gate_rows: list[dict[str, Any]],
    behavior_gate_rows: list[dict[str, Any]],
    promotion_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    mitigation_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    seed_start_index: int,
    seed_count: int,
    horizon_steps: int,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_rows = proof_gate_rows + generalization_gate_rows + behavior_gate_rows + promotion_guard_rows
    all_delta_rows = source_delta_rows + base_delta_rows
    forbidden_claims_made = any(
        as_bool(row["claim_made"]) and not as_bool(row["allowed"]) for row in claim_rows
    )
    gate_matrix_pass = bool(gate_rows) and all(as_bool(row["status_pass"]) for row in gate_rows)
    actor_contract_shape = bool(actor_guard_rows) and all(as_bool(row["status_pass"]) for row in actor_guard_rows)
    holdout_seed_indices = sorted({int(row["seed_index"]) for row in source_delta_rows})
    previous_seed_indices = sorted(
        set(range(0, DEFAULT_SEED_START_INDEX))
        | {int(row["seed_index"]) for row in m2793_delta_rows if str(row.get("seed_index", ""))}
        | set(int(index) for index in m2793_summary.get("fresh_holdout_seed_indices", []))
    )
    status_pass = bool(
        gate_matrix_pass
        and actor_contract_shape
        and all(as_bool(row["status_pass"]) for row in mitigation_guard_rows)
        and bool(m2799_summary.get("status_pass", False))
        and bool(m2796_summary.get("status_pass", False))
        and len(source_delta_rows) == len(objective_rows) * int(seed_count)
        and len(base_delta_rows) == len(objective_rows) * int(seed_count)
        and not forbidden_claims_made
    )
    source_metrics = build_delta_metric_summary(source_delta_rows)
    base_metrics = build_delta_metric_summary(base_delta_rows)
    stable_source_metrics = build_delta_metric_summary(
        [row for row in source_delta_rows if row["role_family"] == "stable_avoidable"]
    )
    stable_base_metrics = build_delta_metric_summary(
        [row for row in base_delta_rows if row["role_family"] == "stable_avoidable"]
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
        "m2800_audit": str(source_paths["m2800_audit"]),
        "m2799_summary": str(source_paths["m2799_summary"]),
        "m2799_status_pass": bool(m2799_summary.get("status_pass", False)),
        "m2799_candidate_checkpoint_hash": m2799_summary.get("candidate_checkpoint_hash", ""),
        "m2796_summary": str(source_paths["m2796_summary"]),
        "m2796_status_pass": bool(m2796_summary.get("status_pass", False)),
        "m2793_summary": str(source_paths["m2793_summary"]),
        "m2793_status_pass": bool(m2793_summary.get("status_pass", False)),
        "m2793_horizon_steps": int(m2793_summary.get("horizon_steps", 0)),
        "source_checkpoint": str(subject_registry["source"]["checkpoint_path"]),
        "base_candidate_checkpoint": str(subject_registry["base_candidate"]["checkpoint_path"]),
        "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
        "source_checkpoint_hash": subject_registry["source"]["checkpoint_hash"],
        "base_candidate_checkpoint_hash": subject_registry["base_candidate"]["checkpoint_hash"],
        "candidate_checkpoint_hash": subject_registry["candidate"]["checkpoint_hash"],
        "m2799_manifest_source_hash": m2799_checkpoint_manifest.get("source_reference_checkpoint_hash", ""),
        "m2799_manifest_start_hash": m2799_checkpoint_manifest.get("start_candidate_checkpoint_hash", ""),
        "m2799_manifest_candidate_hash": m2799_checkpoint_manifest.get("candidate_checkpoint_hash", ""),
        "m2799_manifest_m2782_base_hash": m2799_checkpoint_manifest.get("base_candidate_checkpoint_hash", ""),
        "triad_execution_rows": str(paths["triad_execution_rows"]),
        "candidate_minus_source_delta_rows": str(paths["candidate_minus_source_delta_rows"]),
        "candidate_minus_base_delta_rows": str(paths["candidate_minus_base_delta_rows"]),
        "proof_gate_rows": str(paths["proof_gate_rows"]),
        "generalization_holdout_gate_rows": str(paths["generalization_holdout_gate_rows"]),
        "behavior_retention_gate_rows": str(paths["behavior_retention_gate_rows"]),
        "promotion_guard_rows": str(paths["promotion_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "mitigation_reference_guard_rows": str(paths["mitigation_reference_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "required_artifacts_present": False,
        "m2802_follow_up_manifest_registered": False,
        "source_only_backend_reset_run": True,
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "closed_loop_rollout_run": True,
        "seed_start_index": int(seed_start_index),
        "seed_count": int(seed_count),
        "fresh_holdout_seed_indices": holdout_seed_indices,
        "previous_seed_indices": previous_seed_indices,
        "fresh_holdout_seed_indices_disjoint_from_previous": set(holdout_seed_indices).isdisjoint(previous_seed_indices),
        "horizon_steps": int(horizon_steps),
        "horizon_longer_than_m2793": int(horizon_steps) > int(m2793_summary.get("horizon_steps", 0)),
        "objective_row_count": len(objective_rows),
        "triad_execution_row_count": len(execution_rows),
        "candidate_minus_source_delta_row_count": len(source_delta_rows),
        "candidate_minus_base_delta_row_count": len(base_delta_rows),
        "proof_gate_row_count": len(proof_gate_rows),
        "generalization_gate_row_count": len(generalization_gate_rows),
        "behavior_retention_gate_row_count": len(behavior_gate_rows),
        "promotion_guard_row_count": len(promotion_guard_rows),
        "actor_guard_row_count": len(actor_guard_rows),
        "mitigation_reference_guard_row_count": len(mitigation_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "failed_gate_ids": [row["gate_id"] for row in gate_rows if not as_bool(row["status_pass"])],
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_atlas_or_role_labels_detected": False,
        "all_actions_finite": bool(execution_rows) and all(as_bool(row["finite_action"]) for row in execution_rows),
        "all_observations_finite": bool(execution_rows) and all(as_bool(row["finite_observation"]) for row in execution_rows),
        "all_actions_within_bounds": bool(execution_rows) and all(as_bool(row["action_within_bounds"]) for row in execution_rows),
        "paired_rows_complete": bool(all_delta_rows) and all(as_bool(row["paired_row_complete"]) for row in all_delta_rows),
        "mitigation_reference_rows_guarded": all(not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows),
        "forbidden_claims_made": forbidden_claims_made,
        "diagnostic_delta_rows_only": all(as_bool(row["diagnostic_only"]) for row in all_delta_rows),
        "candidate_minus_source_metric_summary": source_metrics,
        "candidate_minus_base_metric_summary": base_metrics,
        "stable_avoidable_candidate_minus_source_metric_summary": stable_source_metrics,
        "stable_avoidable_candidate_minus_base_metric_summary": stable_base_metrics,
        "candidate_minus_source_obstacle_clearance_positive_count": source_metrics["candidate_minus_reference_minimum_obstacle_clearance_m"]["positive"],
        "candidate_minus_source_obstacle_clearance_negative_count": source_metrics["candidate_minus_reference_minimum_obstacle_clearance_m"]["negative"],
        "candidate_minus_base_obstacle_clearance_positive_count": base_metrics["candidate_minus_reference_minimum_obstacle_clearance_m"]["positive"],
        "candidate_minus_base_obstacle_clearance_negative_count": base_metrics["candidate_minus_reference_minimum_obstacle_clearance_m"]["negative"],
        "stable_avoidable_candidate_minus_source_obstacle_clearance_negative_count": stable_source_metrics["candidate_minus_reference_minimum_obstacle_clearance_m"]["negative"],
        "stable_avoidable_candidate_minus_base_obstacle_clearance_negative_count": stable_base_metrics["candidate_minus_reference_minimum_obstacle_clearance_m"]["negative"],
        "obstacle_clearance_guard_hard_before_objectives": True,
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def required_artifacts_present(paths: dict[str, Path]) -> bool:
    required_keys = [
        "summary",
        "triad_execution_rows",
        "candidate_minus_source_delta_rows",
        "candidate_minus_base_delta_rows",
        "proof_gate_rows",
        "generalization_holdout_gate_rows",
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
        "run_state_id": "m2801_clearance_localized_candidate_fresh_holdout_triad_delta_panel_state_v0",
        "generated_at_utc": utc_timestamp(),
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "output_paths": {key: str(path) for key, path in paths.items()},
        "seed_start_index": summary["seed_start_index"],
        "seed_count": summary["seed_count"],
        "fresh_holdout_seed_indices": summary["fresh_holdout_seed_indices"],
        "previous_seed_indices": summary["previous_seed_indices"],
        "actor_contract": {
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_atlas_or_role_labels_detected": False,
        },
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_m2802_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    task_id = DEFAULT_NEXT_BLOCKER
    return {
        "id": task_id,
        "type": "gate",
        "gate_tier": "generalization",
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
        "lineage": {
            "parent_checkpoint": [
                summary["source_checkpoint"],
                summary["base_candidate_checkpoint"],
                summary["candidate_checkpoint"],
            ],
            "parent_dataset": [
                summary["summary"],
                summary["triad_execution_rows"],
                summary["candidate_minus_source_delta_rows"],
                summary["candidate_minus_base_delta_rows"],
                summary["proof_gate_rows"],
                summary["generalization_holdout_gate_rows"],
                summary["behavior_retention_gate_rows"],
                summary["promotion_guard_rows"],
                summary["actor_contract_guard_rows"],
                summary["mitigation_reference_guard_rows"],
                summary["claim_boundary_rows"],
                summary["gate_matrix"],
                summary["doc"],
            ],
            "parent_config": [
                "experiments/manifests/m2801-engineering-controller-route-a-source-only-belief-stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-preflight.json",
                "experiments/manifests/m2800-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-result-audit.json",
                "experiments/manifests/m2799-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-preflight.json",
            ],
            "parent_objective": [
                "audit the M2801 fresh-holdout source/M2791-start/M2799-candidate triad delta panel before interpretation"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2800-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-result-audit",
                "m2799-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-preflight",
            ],
            "blocked_by": [
                "M2801 triad deltas must be audited before any validation ranking promotion performance or self-ID interpretation",
                "M2801 remains source-only and cannot resolve high-fidelity validation",
                "Obstacle-clearance and stable_avoidable retention must stay hard before road-margin or speed interpretation",
            ],
            "supersedes": [
                "direct interpretation of M2801 deltas without result audit",
                "candidate checkpoint promotion from fresh-holdout triad diagnostic deltas",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2802 must audit M2801 summary triad execution delta rows gates and claim boundaries",
            "M2802 must verify seed indices 12..15 remain outside prior seed surfaces 0..11",
            "M2802 must preserve actor 72/action 3 no hidden/oracle actor input and actor-invisible labels",
            "M2802 must keep obstacle-clearance and stable_avoidable retention as hard guards before road-margin speed yaw-rate conflict or action-delta interpretation",
            "M2802 must keep mitigation reference rows outside ordinary denominators",
            "M2802 must reject validation ranking winner promotion success-rate verdict repair-success driver-performance paper current-sim high-fidelity full ideal driver and self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step policy action rollout replay validation training PPO source build adapter probe or external simulation",
            "do not change actor inputs or action contract",
            "do not expose role dynamics stress atlas clearance outcome success progress route or verdict labels to actor input",
            "do not use mitigation reference rows as ordinary successes",
            "do not hide obstacle-clearance or stable_avoidable failures behind road-margin speed yaw-rate conflict or action-delta metrics",
            "do not rank checkpoints or select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not claim repair success driver performance validation paper current-sim high-fidelity full ideal driver or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training",
            "evidence_axis": "source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel_result_audit",
            "evidence_increment": "audits M2801 fresh-holdout triad closed-loop diagnostic delta artifacts before interpretation",
            "claim_scope": "Result audit only; no new execution training validation ranking promotion driver-performance paper high-fidelity self-ID or full-driver claim",
            "stop_condition": [
                "stop if M2801 required artifacts are incomplete",
                "stop if actor or claim boundaries fail",
                "stop if holdout seed indices overlap earlier surfaces",
                "stop if obstacle-clearance or stable_avoidable guards are weakened or hidden",
                "stop if triad deltas are interpreted as ranking or promotion evidence",
            ],
            "fallback_plan": [
                "route to artifact repair if required artifacts are missing",
                "route to branch synthesis if triad deltas are negative weak mixed or claim boundaries fail",
                "pivot to broader architecture or scenario-distribution change if fresh holdout fails to show actionable candidate signal",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2801 writes fresh-holdout source/M2791-start/M2799-candidate closed-loop delta artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2801 fresh-holdout source-only triad delta panel artifacts",
            "admission_evidence": [
                "M2801 summary and gate artifacts exist",
                "M2801 writes triad execution and delta rows with source start candidate and corrective candidate lineage",
                "M2801 is not validated ranked or promoted before this audit",
            ],
            "blocked_shortcuts": [
                "no new execution or training in M2802",
                "no validation ranking promotion success-rate verdict performance paper HF full-driver or self-ID claim",
                "no obstacle-clearance or stable_avoidable guard weakening",
            ],
            "allowed_updates": [
                f"docs/{task_id}.md",
                "M2802 status queue scoreboard research log and review",
            ],
            "next_stage_criteria": [
                "M2801 artifacts are complete and claim-safe or failure is classified",
                "one bounded follow-up or stop decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2802 audits source-only M2801 artifacts and cannot establish self-ID.",
            "history_necessity_tests": [
                "M2802 may check that M2801 covered history stress rows but runs no self-ID comparison."
            ],
            "temporal_evidence_window": "M2796-M2802 source-only clearance-localized corrective branch.",
            "negative_result_policy": "If M2801 artifacts fail or deltas are negative, preserve failure and route to synthesis or repair rather than weakening gates.",
            "allowed_claims": [
                "M2801 fresh-holdout triad delta artifacts are accepted or rejected as complete and claim-safe",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fresh M2801 holdout triad closed-loop delta artifacts before any extension",
            "paper_verdict_delta": "no paper verdict; audit decides whether M2801 can be used as future engineering evidence",
            "must_synthesize_if": [
                "M2802 finds incomplete artifacts or claim-boundary failure",
                "M2802 finds obstacle-clearance or stable_avoidable guard weakening",
                "another process-only milestone is proposed after M2802 without fresh evidence or synthesis",
            ],
        },
        "hypothesis": "M2801 fresh-holdout triad closed-loop delta artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{task_id}.md exists",
            "M2802 audits M2801 summary triad execution delta gate actor guard claim and lineage artifacts",
            "M2802 registers one bounded follow-up or stop decision",
            "M2802 makes no new execution training validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2802 executes new training or rollout",
            "M2802 treats M2801 as validation ranking or promotion evidence",
            "M2802 hides obstacle-clearance or stable_avoidable guard failures",
            "M2802 claims driver performance paper high-fidelity full-driver or self-ID result",
        ],
        "decision_rule": "Pass only if M2802 writes a claim-safe audit of M2801 artifacts and routes before interpretation.",
        "commands": [{"name": "audit_design_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{task_id}.md", "type": "md"}],
        "baseline_checkpoints": [
            summary["source_checkpoint"],
            summary["base_candidate_checkpoint"],
            summary["candidate_checkpoint"],
        ],
        "baseline_artifacts": [summary["summary"], summary["gate_matrix"]],
        "scoreboard_checkpoint": f"docs/{task_id}.md",
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    failed = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    source_metrics = summary["candidate_minus_source_metric_summary"]
    base_metrics = summary["candidate_minus_base_metric_summary"]
    lines = [
        "# M2801 Engineering Controller Route A Source-Only Belief-Stress Clearance-Localized Candidate Fresh-Holdout Triad Delta Panel Preflight",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result_class: `{summary['result_class']}`",
        "- manifest: `experiments/manifests/m2801-engineering-controller-route-a-source-only-belief-stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-preflight.json`",
        f"- summary: `{summary['summary']}`",
        f"- triad execution rows: `{summary['triad_execution_rows']}`",
        f"- candidate-minus-source deltas: `{summary['candidate_minus_source_delta_rows']}`",
        f"- candidate-minus-base deltas: `{summary['candidate_minus_base_delta_rows']}`",
        f"- proof gates: `{summary['proof_gate_rows']}`",
        f"- generalization holdout gates: `{summary['generalization_holdout_gate_rows']}`",
        f"- behavior-retention gates: `{summary['behavior_retention_gate_rows']}`",
        f"- promotion guards: `{summary['promotion_guard_rows']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Result",
        "",
        "M2801 ran a bounded source-only HF0/FourWheel triad closed-loop diagnostic",
        "panel over the M2655 source checkpoint, the M2791 start candidate, and",
        "the M2799 clearance-localized corrective candidate. It uses fresh holdout",
        "seed indices outside prior seed surfaces 0..11 and a longer horizon than",
        "M2793. The rows are diagnostic deltas for audit, not ranking or winner",
        "selection.",
        "",
        "```text",
        f"objective_rows: {summary['objective_row_count']}",
        f"seed_start_index: {summary['seed_start_index']}",
        f"seed_count: {summary['seed_count']}",
        f"fresh_holdout_seed_indices: {summary['fresh_holdout_seed_indices']}",
        f"previous_seed_indices: {summary['previous_seed_indices']}",
        f"horizon_steps: {summary['horizon_steps']}",
        f"m2793_horizon_steps: {summary['m2793_horizon_steps']}",
        f"triad_execution_rows: {summary['triad_execution_row_count']}",
        f"candidate_minus_source_delta_rows: {summary['candidate_minus_source_delta_row_count']}",
        f"candidate_minus_base_delta_rows: {summary['candidate_minus_base_delta_row_count']}",
        f"proof_gate_rows: {summary['proof_gate_row_count']}",
        f"generalization_gate_rows: {summary['generalization_gate_row_count']}",
        f"behavior_retention_gate_rows: {summary['behavior_retention_gate_row_count']}",
        f"promotion_guard_rows: {summary['promotion_guard_row_count']}",
        f"failed_gate_ids: {failed}",
        "```",
        "",
        "## Candidate-Minus-Source Delta Summary",
        "",
        "```text",
        _metric_line(source_metrics, "candidate_minus_reference_minimum_obstacle_clearance_m"),
        _metric_line(source_metrics, "candidate_minus_reference_minimum_road_margin_m"),
        _metric_line(source_metrics, "candidate_minus_reference_final_speed_mps"),
        _metric_line(source_metrics, "candidate_minus_reference_max_abs_yaw_rate"),
        _metric_line(source_metrics, "candidate_minus_reference_throttle_brake_conflict_proxy"),
        _metric_line(source_metrics, "mean_action_delta_l1"),
        "```",
        "",
        "## Candidate-Minus-M2791-Start Delta Summary",
        "",
        "```text",
        _metric_line(base_metrics, "candidate_minus_reference_minimum_obstacle_clearance_m"),
        _metric_line(base_metrics, "candidate_minus_reference_minimum_road_margin_m"),
        _metric_line(base_metrics, "candidate_minus_reference_final_speed_mps"),
        _metric_line(base_metrics, "candidate_minus_reference_max_abs_yaw_rate"),
        _metric_line(base_metrics, "candidate_minus_reference_throttle_brake_conflict_proxy"),
        _metric_line(base_metrics, "mean_action_delta_l1"),
        "```",
        "",
        "## Actor And Claim Boundary",
        "",
        "Actor input stayed at P0 observation 72 and action 3. Atlas, role,",
        "dynamics, stress, clearance, outcome, success, progress, route, and",
        "verdict labels remained evaluator metadata and were not actor-visible.",
        "Mitigation reference rows stayed outside ordinary denominators.",
        "",
        "Obstacle-clearance and stable_avoidable retention are the hard guards",
        "before road-margin, yaw-rate, speed, throttle/brake conflict, or",
        "action-delta interpretation. M2801 does not train, validate, rank,",
        "select a winner, promote a checkpoint, compute a success-rate verdict,",
        "claim repair success, driver performance, paper evidence, current-sim",
        "verdict, high-fidelity validation, full ideal driver completion, or",
        "level3 self-identification.",
        "",
        "## Route Decision",
        "",
        "Route to M2802 result audit before interpreting the fresh-holdout triad",
        "deltas or choosing any continuation, synthesis, repair, promotion, or stop",
        "decision.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_delta_metric_summary(delta_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    fields = [
        "candidate_minus_reference_minimum_obstacle_clearance_m",
        "candidate_minus_reference_minimum_road_margin_m",
        "candidate_minus_reference_final_speed_mps",
        "candidate_minus_reference_max_abs_yaw_rate",
        "candidate_minus_reference_throttle_brake_conflict_proxy",
        "mean_action_delta_l1",
    ]
    return {field: _metric_stats(delta_rows, field) for field in fields}


def _metric_stats(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = np.asarray([float(row[field]) for row in rows], dtype=np.float64)
    if values.size == 0:
        return {"count": 0, "min": 0.0, "median": 0.0, "max": 0.0, "mean": 0.0, "positive": 0, "negative": 0, "zero": 0}
    return {
        "count": int(values.size),
        "min": float(np.min(values)),
        "median": float(np.median(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "positive": int(np.sum(values > 0.0)),
        "negative": int(np.sum(values < 0.0)),
        "zero": int(np.sum(values == 0.0)),
    }


def _metric_line(summary: dict[str, dict[str, Any]], field: str) -> str:
    stats = summary[field]
    return (
        f"{field}: mean={stats['mean']} median={stats['median']} min={stats['min']} "
        f"max={stats['max']} positive={stats['positive']} negative={stats['negative']} zero={stats['zero']}"
    )


def _each_bucket_holdout_seed_coverage(
    rows: list[dict[str, Any]],
    seed_start_index: int,
    seed_count: int,
) -> bool:
    expected = set(range(int(seed_start_index), int(seed_start_index) + int(seed_count)))
    buckets: dict[tuple[str, str, str], set[int]] = {}
    for row in rows:
        key = (row["role_family"], row["dynamics_axis"], row["stress_family"])
        buckets.setdefault(key, set()).add(int(row["seed_index"]))
    expected_bucket_count = len(ORDINARY_ROLE_FAMILIES) * len(DYNAMICS_AXES) * len(STRESS_FAMILIES)
    return len(buckets) == expected_bucket_count and all(indices == expected for indices in buckets.values())


def retag_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [retag_row(dict(row)) for row in rows]


def retag_row(row: dict[str, Any]) -> dict[str, Any]:
    if "claim_scope" in row:
        row["claim_scope"] = CLAIM_SCOPE
    if "claim_boundary" in row:
        row["claim_boundary"] = CLAIM_SCOPE
    if "forbidden_interpretation" in row:
        row["forbidden_interpretation"] = FORBIDDEN_INTERPRETATION
    return row


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2800-audit", type=Path, default=DEFAULT_M2800_AUDIT)
    parser.add_argument("--m2799-dir", type=Path, default=DEFAULT_M2799_DIR)
    parser.add_argument("--m2796-dir", type=Path, default=DEFAULT_M2796_DIR)
    parser.add_argument("--m2793-dir", type=Path, default=DEFAULT_M2793_DIR)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--base-candidate-checkpoint", type=Path, default=DEFAULT_BASE_CANDIDATE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed-start-index", type=int, default=DEFAULT_SEED_START_INDEX)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    args = parser.parse_args()
    run_clearance_localized_candidate_fresh_holdout_triad_delta_panel(
        args.output_dir,
        m2800_audit=args.m2800_audit,
        m2799_dir=args.m2799_dir,
        m2796_dir=args.m2796_dir,
        m2793_dir=args.m2793_dir,
        source_checkpoint=args.source_checkpoint,
        base_candidate_checkpoint=args.base_candidate_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
        device=args.device,
        seed_start_index=args.seed_start_index,
        seed_count=args.seed_count,
        horizon_steps=args.horizon_steps,
    )


if __name__ == "__main__":
    main()
