"""M2787 source-only belief-stress fresh-holdout delta panel.

This preflight runs a bounded paired source-vs-candidate diagnostic panel over
fresh holdout seed indices outside the M2784 seed surface. It writes execution
and delta artifacts for audit only. It does not train, validate, rank, select a
winner, promote a checkpoint, compute a success-rate verdict, or claim driver
performance.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel import (
    ACTOR_GUARD_FIELDNAMES,
    CHECKPOINT_SUBJECTS,
    CLAIM_FIELDNAMES,
    GATE_FIELDNAMES,
    MITIGATION_GUARD_FIELDNAMES,
    PAIRED_DELTA_FIELDNAMES,
    PAIRED_EXECUTION_FIELDNAMES,
    build_actor_contract_guard_rows,
    build_mitigation_reference_guard_rows,
    build_paired_delta_rows,
    build_promotion_guard_rows,
    gate,
    load_subject_registry,
    run_closed_loop_execution,
    select_curriculum_rows,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
    DYNAMICS_AXES,
    ORDINARY_ROLE_FAMILIES,
    STRESS_FAMILIES,
    as_bool,
    read_csv_rows,
)
from autodrift.engineering_controller_route_a_source_only_fresh_generalization_panel import (
    build_fresh_generalization_panel_specs,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2787-engineering-controller-route-a-source-only-belief-stress-fresh-"
    "holdout-delta-panel-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_"
    "holdout_delta_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2787-engineering-controller-route-a-source-only-belief-stress-fresh-"
    "holdout-delta-panel-preflight.md"
)
DEFAULT_M2786_SYNTHESIS = Path(
    "docs/m2786-engineering-controller-route-a-source-only-belief-stress-short-"
    "training-branch-synthesis.md"
)
DEFAULT_M2785_AUDIT = Path(
    "docs/m2785-engineering-controller-route-a-source-only-belief-stress-candidate-"
    "closed-loop-delta-panel-result-audit.md"
)
DEFAULT_M2784_DIR = Path(
    "runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_"
    "closed_loop_delta_panel"
)
DEFAULT_M2782_DIR = Path(
    "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_CANDIDATE_CHECKPOINT = Path(
    "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2788-engineering-controller-route-a-source-only-belief-"
    "stress-fresh-holdout-delta-panel-result-audit.json"
)
DEFAULT_NEXT_BLOCKER = (
    "m2788-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-"
    "delta-panel-result-audit"
)
DEFAULT_SEED_START_INDEX = 4
DEFAULT_SEED_COUNT = 4
DEFAULT_HORIZON_STEPS = 120

CLAIM_SCOPE = "Route A source-only belief-stress fresh-holdout paired delta diagnostic preflight only"
FORBIDDEN_INTERPRETATION = (
    "validation, ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "repair success, driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, or "
    "level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_"
    "panel_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_"
    "panel_preflight_failed"
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


def run_belief_stress_fresh_holdout_delta_panel(
    output_dir: Path | str,
    *,
    m2786_synthesis: Path | str = DEFAULT_M2786_SYNTHESIS,
    m2785_audit: Path | str = DEFAULT_M2785_AUDIT,
    m2784_dir: Path | str = DEFAULT_M2784_DIR,
    m2782_dir: Path | str = DEFAULT_M2782_DIR,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
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
        raise ValueError("M2787 requires seed_start_index outside M2784 seed_index 0..3")
    if int(seed_count) < 2:
        raise ValueError("M2787 requires at least two fresh holdout seeds")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(
        Path(m2786_synthesis),
        Path(m2785_audit),
        Path(m2784_dir),
        Path(m2782_dir),
        Path(source_checkpoint),
        Path(candidate_checkpoint),
    )
    _require_sources(source_paths)

    m2784_summary = read_json(source_paths["m2784_summary"])
    m2782_summary = read_json(source_paths["m2782_summary"])
    checkpoint_manifest = read_json(source_paths["checkpoint_manifest"])
    m2784_delta_rows = read_csv_rows(source_paths["m2784_paired_delta_rows"])
    curriculum_rows = read_csv_rows(source_paths["training_curriculum_rows"])
    source_mitigation_rows = read_csv_rows(source_paths["mitigation_reference_guard_rows"])
    selected_curriculum = select_curriculum_rows(curriculum_rows)
    if int(horizon_steps) <= int(m2784_summary.get("horizon_steps", 0)):
        raise ValueError("M2787 horizon_steps must be longer than the M2784 horizon")

    subject_registry = load_subject_registry(
        source_paths["source_checkpoint"],
        source_paths["candidate_checkpoint"],
        device=device,
    )
    run_item_map = build_holdout_run_item_map(int(seed_start_index) + int(seed_count))
    execution_rows = collect_fresh_holdout_paired_execution_rows(
        selected_curriculum,
        run_item_map,
        subject_registry,
        seed_start_index=int(seed_start_index),
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    delta_rows = retag_rows(build_paired_delta_rows(execution_rows, subject_registry))
    mitigation_guard_rows = retag_rows(build_mitigation_reference_guard_rows(source_mitigation_rows))
    actor_guard_rows = retag_rows(build_actor_contract_guard_rows(execution_rows))
    claim_rows = build_claim_boundary_rows()
    proof_gate_rows = build_proof_gate_rows(
        source_paths=source_paths,
        m2784_summary=m2784_summary,
        m2782_summary=m2782_summary,
        checkpoint_manifest=checkpoint_manifest,
        curriculum_rows=selected_curriculum,
        execution_rows=execution_rows,
        delta_rows=delta_rows,
        actor_guard_rows=actor_guard_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        subject_registry=subject_registry,
        seed_count=int(seed_count),
    )
    generalization_gate_rows = build_generalization_holdout_gate_rows(
        selected_curriculum,
        execution_rows,
        delta_rows,
        m2784_delta_rows,
        m2784_summary,
        seed_start_index=int(seed_start_index),
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    promotion_guard_rows = retag_rows(build_promotion_guard_rows())
    gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows

    write_csv_rows(paths["paired_execution_rows"], execution_rows, PAIRED_EXECUTION_FIELDNAMES)
    write_csv_rows(paths["paired_delta_rows"], delta_rows, PAIRED_DELTA_FIELDNAMES)
    write_csv_rows(paths["proof_retention_gate_rows"], proof_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["generalization_holdout_gate_rows"], generalization_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["promotion_guard_rows"], promotion_guard_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["mitigation_reference_guard_rows"], mitigation_guard_rows, MITIGATION_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        m2784_summary=m2784_summary,
        m2782_summary=m2782_summary,
        checkpoint_manifest=checkpoint_manifest,
        m2784_delta_rows=m2784_delta_rows,
        subject_registry=subject_registry,
        curriculum_rows=selected_curriculum,
        execution_rows=execution_rows,
        delta_rows=delta_rows,
        proof_gate_rows=proof_gate_rows,
        generalization_gate_rows=generalization_gate_rows,
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
    write_json(paths["follow_up_manifest"], build_m2788_manifest(summary))
    write_doc(paths["doc"], summary)

    summary = {
        **summary,
        "required_artifacts_present": required_artifacts_present(paths),
        "m2788_follow_up_manifest_registered": paths["follow_up_manifest"].exists(),
    }
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    summary["result_class"] = RESULT_CLASS_PASS if summary["status_pass"] else RESULT_CLASS_FAIL
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2788_manifest(summary))
    write_doc(paths["doc"], summary)
    return summary


def _paths(output: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output / "summary.json",
        "paired_execution_rows": output / "paired_execution_rows.csv",
        "paired_delta_rows": output / "paired_delta_rows.csv",
        "proof_retention_gate_rows": output / "proof_retention_gate_rows.csv",
        "generalization_holdout_gate_rows": output / "generalization_holdout_gate_rows.csv",
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
    m2786_synthesis: Path,
    m2785_audit: Path,
    m2784_dir: Path,
    m2782_dir: Path,
    source_checkpoint: Path,
    candidate_checkpoint: Path,
) -> dict[str, Path]:
    return {
        "m2786_synthesis": m2786_synthesis,
        "m2785_audit": m2785_audit,
        "m2784_summary": m2784_dir / "summary.json",
        "m2784_paired_delta_rows": m2784_dir / "paired_delta_rows.csv",
        "m2784_gate_matrix": m2784_dir / "gate_matrix.csv",
        "m2782_summary": m2782_dir / "summary.json",
        "checkpoint_manifest": m2782_dir / "checkpoint_manifest.json",
        "training_curriculum_rows": m2782_dir / "training_curriculum_rows.csv",
        "mitigation_reference_guard_rows": m2782_dir / "mitigation_reference_guard_rows.csv",
        "source_checkpoint": source_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2787 missing required source artifacts: {missing}")


def build_holdout_run_item_map(seed_count: int) -> dict[tuple[str, str, int], Any]:
    run_items, _seed_rows, _axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=int(seed_count)
    )
    return {
        (item.role_family, item.dynamics_axis_id, int(item.seed_index)): item
        for item in run_items
    }


def collect_fresh_holdout_paired_execution_rows(
    curriculum_rows: list[dict[str, Any]],
    run_item_map: dict[tuple[str, str, int], Any],
    subject_registry: dict[str, dict[str, Any]],
    *,
    seed_start_index: int,
    seed_count: int,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for curriculum in curriculum_rows:
        for seed_index in range(int(seed_start_index), int(seed_start_index) + int(seed_count)):
            item = run_item_map[(curriculum["role_family"], curriculum["dynamics_axis"], int(seed_index))]
            pair_id = (
                f"m2787_holdout_pair_{curriculum['role_family']}_{curriculum['dynamics_axis']}_"
                f"{curriculum['stress_family']}_seed_index_{int(seed_index)}_seed_{int(item.seed)}"
            )
            for subject in CHECKPOINT_SUBJECTS:
                row = run_closed_loop_execution(
                    subject_registry[subject],
                    item,
                    curriculum,
                    pair_id=pair_id,
                    seed_index=int(seed_index),
                    horizon_steps=int(horizon_steps),
                )
                rows.append(retag_row(row))
    return rows


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


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        ("validation_result", "validation", False, False, "M2787 does not run measured validation"),
        ("ranking_result", "ranking", False, False, "M2787 does not rank checkpoints"),
        ("winner_selection", "promotion", False, False, "M2787 selects no winner"),
        ("checkpoint_promotion", "promotion", False, False, "M2787 promotes no checkpoint"),
        ("success_rate_verdict", "metric_artifact", False, False, "M2787 emits no success-rate verdict"),
        ("driver_performance", "performance", False, False, "M2787 is fresh-holdout diagnostic evidence only"),
        ("paper_result", "paper", False, False, "M2787 is not paper evidence"),
        ("current_sim_verdict", "current_sim", False, False, "M2787 is not a current-sim verdict"),
        ("high_fidelity_validation", "high_fidelity", False, False, "M2787 does not run HF validation"),
        ("level3_self_id", "self_id", False, False, "M2787 is not self-ID evidence"),
        (
            "fresh_holdout_delta_artifacts_complete",
            "allowed_artifact_completion",
            True,
            True,
            "M2787 may claim fresh-holdout paired diagnostic artifacts were written",
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
    m2784_summary: dict[str, Any],
    m2782_summary: dict[str, Any],
    checkpoint_manifest: dict[str, Any],
    curriculum_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    mitigation_guard_rows: list[dict[str, Any]],
    subject_registry: dict[str, dict[str, Any]],
    seed_count: int,
) -> list[dict[str, Any]]:
    expected_execution_rows = len(curriculum_rows) * int(seed_count) * len(CHECKPOINT_SUBJECTS)
    expected_delta_rows = len(curriculum_rows) * int(seed_count)
    return retag_rows(
        [
            gate(
                "proof_m2786_synthesis_present",
                "proof",
                "lineage",
                source_paths["m2786_synthesis"].exists(),
                str(source_paths["m2786_synthesis"]),
                "M2786 synthesis artifact exists",
                1,
                "lineage_invalid",
            ),
            gate(
                "proof_m2785_audit_present",
                "proof",
                "lineage",
                source_paths["m2785_audit"].exists(),
                str(source_paths["m2785_audit"]),
                "M2785 audit artifact exists",
                1,
                "lineage_invalid",
            ),
            gate(
                "proof_m2784_status_pass",
                "proof",
                "lineage",
                bool(m2784_summary.get("status_pass", False)),
                str(bool(m2784_summary.get("status_pass", False))),
                "true",
                1,
                "lineage_invalid",
            ),
            gate(
                "proof_m2782_status_pass",
                "proof",
                "lineage",
                bool(m2782_summary.get("status_pass", False)),
                str(bool(m2782_summary.get("status_pass", False))),
                "true",
                1,
                "lineage_invalid",
            ),
            gate(
                "proof_checkpoint_lineage_hashes",
                "proof",
                "lineage",
                bool(subject_registry["source"]["checkpoint_hash"])
                and bool(subject_registry["candidate"]["checkpoint_hash"])
                and subject_registry["source"]["checkpoint_hash"] != subject_registry["candidate"]["checkpoint_hash"]
                and bool(checkpoint_manifest.get("candidate_checkpoint_hash")),
                "source and candidate hashes",
                "source and candidate hashes with candidate lineage",
                1,
                "lineage_invalid",
            ),
            gate(
                "proof_paired_execution_row_count",
                "proof",
                "artifact",
                len(execution_rows) == expected_execution_rows,
                str(len(execution_rows)),
                str(expected_execution_rows),
                len(execution_rows),
                "metric_artifact",
            ),
            gate(
                "proof_paired_delta_row_count",
                "proof",
                "artifact",
                len(delta_rows) == expected_delta_rows,
                str(len(delta_rows)),
                str(expected_delta_rows),
                len(delta_rows),
                "metric_artifact",
            ),
            gate(
                "proof_pair_completeness",
                "proof",
                "artifact",
                bool(delta_rows) and all(as_bool(row["paired_row_complete"]) for row in delta_rows),
                "all pairs complete",
                "all pairs complete",
                len(delta_rows),
                "metric_artifact",
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
                not any(as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in execution_rows),
                "false",
                "false",
                len(execution_rows),
                "contract_violation",
            ),
            gate(
                "proof_actor_invisible_labels",
                "proof",
                "actor_contract",
                not any(as_bool(row["actor_visible_label"]) for row in execution_rows),
                "false",
                "false",
                len(execution_rows),
                "contract_violation",
            ),
            gate(
                "proof_mitigation_rows_excluded",
                "proof",
                "proof_washout",
                bool(mitigation_guard_rows)
                and all(not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows)
                and all(not as_bool(row["included_in_paired_execution_rows"]) for row in mitigation_guard_rows),
                "mitigation rows excluded",
                "mitigation rows excluded",
                len(mitigation_guard_rows),
                "proof_washout",
            ),
            gate(
                "proof_no_ranking_winner_success_verdict",
                "proof",
                "claim_boundary",
                not any(as_bool(row["ranking_admissible"]) or as_bool(row["winner_selected"]) for row in delta_rows)
                and not any(as_bool(row["success_rate_verdict_computed"]) for row in delta_rows),
                "false",
                "false",
                len(delta_rows),
                "objective_overfit",
            ),
        ]
    )


def build_generalization_holdout_gate_rows(
    curriculum_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    m2784_delta_rows: list[dict[str, str]],
    m2784_summary: dict[str, Any],
    *,
    seed_start_index: int,
    seed_count: int,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    m2784_seed_indices = {int(row["seed_index"]) for row in m2784_delta_rows if str(row.get("seed_index", ""))}
    holdout_seed_indices = {int(row["seed_index"]) for row in delta_rows}
    return retag_rows(
        [
            gate(
                "generalization_role_family_coverage",
                "generalization",
                "scenario_sampling",
                {row["role_family"] for row in delta_rows} == set(ORDINARY_ROLE_FAMILIES),
                ";".join(sorted({row["role_family"] for row in delta_rows})),
                ";".join(ORDINARY_ROLE_FAMILIES),
                len(delta_rows),
                "scenario_sampling_failure",
            ),
            gate(
                "generalization_dynamics_axis_coverage",
                "generalization",
                "scenario_sampling",
                {row["dynamics_axis"] for row in delta_rows} == set(DYNAMICS_AXES),
                ";".join(sorted({row["dynamics_axis"] for row in delta_rows})),
                ";".join(DYNAMICS_AXES),
                len(delta_rows),
                "scenario_sampling_failure",
            ),
            gate(
                "generalization_stress_family_coverage",
                "generalization",
                "scenario_sampling",
                {row["stress_family"] for row in delta_rows} == set(STRESS_FAMILIES),
                ";".join(sorted({row["stress_family"] for row in delta_rows})),
                ";".join(STRESS_FAMILIES),
                len(delta_rows),
                "scenario_sampling_failure",
            ),
            gate(
                "generalization_requested_seed_count",
                "generalization",
                "seed_split",
                int(seed_count) >= 2,
                str(int(seed_count)),
                ">=2",
                len(delta_rows),
                "seed_fragility",
            ),
            gate(
                "generalization_seed_indices_outside_m2784",
                "generalization",
                "seed_split",
                int(seed_start_index) >= int(m2784_summary.get("seed_count", DEFAULT_SEED_START_INDEX))
                and holdout_seed_indices.isdisjoint(m2784_seed_indices),
                ",".join(str(index) for index in sorted(holdout_seed_indices)),
                "disjoint from M2784 seed indices",
                len(delta_rows),
                "scenario_sampling_failure",
            ),
            gate(
                "generalization_each_bucket_holdout_seed_coverage",
                "generalization",
                "seed_split",
                _each_bucket_holdout_seed_coverage(delta_rows, int(seed_start_index), int(seed_count)),
                "complete",
                "complete",
                len(delta_rows),
                "seed_fragility",
            ),
            gate(
                "generalization_pair_subject_coverage",
                "generalization",
                "artifact",
                {row["checkpoint_subject"] for row in execution_rows} == set(CHECKPOINT_SUBJECTS)
                and len(execution_rows) == len(curriculum_rows) * int(seed_count) * len(CHECKPOINT_SUBJECTS),
                ";".join(sorted({row["checkpoint_subject"] for row in execution_rows})),
                ";".join(CHECKPOINT_SUBJECTS),
                len(execution_rows),
                "metric_artifact",
            ),
            gate(
                "generalization_horizon_longer_than_m2784",
                "generalization",
                "horizon",
                int(horizon_steps) > int(m2784_summary.get("horizon_steps", 0)),
                str(int(horizon_steps)),
                f">{int(m2784_summary.get('horizon_steps', 0))}",
                len(execution_rows),
                "scenario_sampling_failure",
            ),
        ]
    )


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source_paths: dict[str, Path],
    m2784_summary: dict[str, Any],
    m2782_summary: dict[str, Any],
    checkpoint_manifest: dict[str, Any],
    m2784_delta_rows: list[dict[str, str]],
    subject_registry: dict[str, dict[str, Any]],
    curriculum_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    proof_gate_rows: list[dict[str, Any]],
    generalization_gate_rows: list[dict[str, Any]],
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
    gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows
    forbidden_claims_made = any(
        as_bool(row["claim_made"]) and not as_bool(row["allowed"]) for row in claim_rows
    )
    gate_matrix_pass = bool(gate_rows) and all(as_bool(row["status_pass"]) for row in gate_rows)
    actor_contract_shape = bool(actor_guard_rows) and all(as_bool(row["status_pass"]) for row in actor_guard_rows)
    holdout_seed_indices = sorted({int(row["seed_index"]) for row in delta_rows})
    m2784_seed_indices = sorted({int(row["seed_index"]) for row in m2784_delta_rows if str(row.get("seed_index", ""))})
    status_pass = bool(
        gate_matrix_pass
        and actor_contract_shape
        and all(as_bool(row["status_pass"]) for row in mitigation_guard_rows)
        and bool(m2784_summary.get("status_pass", False))
        and bool(m2782_summary.get("status_pass", False))
        and len(delta_rows) == len(curriculum_rows) * int(seed_count)
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
        "m2786_synthesis": str(source_paths["m2786_synthesis"]),
        "m2785_audit": str(source_paths["m2785_audit"]),
        "m2784_summary": str(source_paths["m2784_summary"]),
        "m2784_status_pass": bool(m2784_summary.get("status_pass", False)),
        "m2784_seed_count": int(m2784_summary.get("seed_count", 0)),
        "m2784_horizon_steps": int(m2784_summary.get("horizon_steps", 0)),
        "m2784_paired_delta_row_count": int(m2784_summary.get("paired_delta_row_count", len(m2784_delta_rows))),
        "m2782_summary": str(source_paths["m2782_summary"]),
        "m2782_status_pass": bool(m2782_summary.get("status_pass", False)),
        "m2782_gate_matrix_pass": bool(m2782_summary.get("gate_matrix_pass", True)),
        "m2782_candidate_checkpoint_hash": checkpoint_manifest.get("candidate_checkpoint_hash", ""),
        "source_checkpoint": str(subject_registry["source"]["checkpoint_path"]),
        "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
        "source_checkpoint_hash": subject_registry["source"]["checkpoint_hash"],
        "candidate_checkpoint_hash": subject_registry["candidate"]["checkpoint_hash"],
        "source_model_state_hash": subject_registry["source"]["model_state_hash"],
        "candidate_model_state_hash": subject_registry["candidate"]["model_state_hash"],
        "paired_execution_rows": str(paths["paired_execution_rows"]),
        "paired_delta_rows": str(paths["paired_delta_rows"]),
        "proof_retention_gate_rows": str(paths["proof_retention_gate_rows"]),
        "generalization_holdout_gate_rows": str(paths["generalization_holdout_gate_rows"]),
        "promotion_guard_rows": str(paths["promotion_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "mitigation_reference_guard_rows": str(paths["mitigation_reference_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "required_artifacts_present": False,
        "m2788_follow_up_manifest_registered": False,
        "source_only_backend_reset_run": True,
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "closed_loop_rollout_run": True,
        "seed_start_index": int(seed_start_index),
        "seed_count": int(seed_count),
        "fresh_holdout_seed_indices": holdout_seed_indices,
        "m2784_seed_indices": m2784_seed_indices,
        "fresh_holdout_seed_indices_disjoint_from_m2784": set(holdout_seed_indices).isdisjoint(m2784_seed_indices),
        "horizon_steps": int(horizon_steps),
        "horizon_longer_than_m2784": int(horizon_steps) > int(m2784_summary.get("horizon_steps", 0)),
        "curriculum_row_count": len(curriculum_rows),
        "paired_execution_row_count": len(execution_rows),
        "paired_delta_row_count": len(delta_rows),
        "proof_gate_row_count": len(proof_gate_rows),
        "generalization_gate_row_count": len(generalization_gate_rows),
        "promotion_guard_row_count": len(promotion_guard_rows),
        "actor_guard_row_count": len(actor_guard_rows),
        "mitigation_reference_guard_row_count": len(mitigation_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "failed_gate_ids": [row["gate_id"] for row in gate_rows if not as_bool(row["status_pass"])],
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_stress_admission_curriculum_labels_detected": False,
        "all_actions_finite": bool(execution_rows) and all(as_bool(row["finite_action"]) for row in execution_rows),
        "all_observations_finite": bool(execution_rows)
        and all(as_bool(row["finite_observation"]) for row in execution_rows),
        "all_actions_within_bounds": bool(execution_rows)
        and all(as_bool(row["action_within_bounds"]) for row in execution_rows),
        "paired_rows_complete": bool(delta_rows) and all(as_bool(row["paired_row_complete"]) for row in delta_rows),
        "mitigation_reference_rows_guarded": all(
            not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows
        ),
        "forbidden_claims_made": forbidden_claims_made,
        "diagnostic_delta_rows_only": all(as_bool(row["diagnostic_only"]) for row in delta_rows),
        "delta_metric_summary": build_delta_metric_summary(delta_rows),
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def required_artifacts_present(paths: dict[str, Path]) -> bool:
    required_keys = [
        "summary",
        "paired_execution_rows",
        "paired_delta_rows",
        "proof_retention_gate_rows",
        "generalization_holdout_gate_rows",
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
        "run_state_id": "m2787_belief_stress_fresh_holdout_delta_panel_state_v0",
        "generated_at_utc": utc_timestamp(),
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "output_paths": {key: str(path) for key, path in paths.items()},
        "seed_start_index": summary["seed_start_index"],
        "seed_count": summary["seed_count"],
        "fresh_holdout_seed_indices": summary["fresh_holdout_seed_indices"],
        "actor_contract": {
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_stress_admission_curriculum_labels_detected": False,
        },
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_m2788_manifest(summary: dict[str, Any]) -> dict[str, Any]:
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
        ],
        "lineage": {
            "parent_checkpoint": [summary["source_checkpoint"], summary["candidate_checkpoint"]],
            "parent_dataset": [
                summary["summary"],
                summary["paired_execution_rows"],
                summary["paired_delta_rows"],
                summary["proof_retention_gate_rows"],
                summary["generalization_holdout_gate_rows"],
                summary["promotion_guard_rows"],
                summary["actor_contract_guard_rows"],
                summary["mitigation_reference_guard_rows"],
                summary["claim_boundary_rows"],
                summary["gate_matrix"],
                summary["doc"],
            ],
            "parent_config": [
                "experiments/manifests/m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight.json",
                "experiments/manifests/m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis.json",
                "experiments/manifests/m2785-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-result-audit.json",
                "experiments/manifests/m2784-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-preflight.json",
            ],
            "parent_objective": [
                "audit the M2787 fresh-holdout source-only paired delta panel before interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE, "m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis"],
            "blocked_by": [
                "M2787 fresh-holdout deltas must be audited before any validation ranking promotion performance or self-ID interpretation",
                "M2787 remains source-only and cannot resolve the M2638 high-fidelity source dependency",
            ],
            "supersedes": [
                "direct interpretation of M2787 deltas without result audit",
                "candidate checkpoint promotion from fresh-holdout diagnostic deltas",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2788 must audit M2787 summary paired execution rows paired delta rows gates and claim boundaries",
            "M2788 must verify fresh holdout seed indices remain outside M2784 seed_index 0..3",
            "M2788 must preserve actor 72/action 3 no hidden/oracle actor input and actor-invisible labels",
            "M2788 must keep mitigation reference rows outside ordinary denominators",
            "M2788 must reject validation ranking winner promotion success-rate verdict driver-performance paper current-sim high-fidelity full ideal driver and self-ID claims",
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
            "branch": "engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel",
            "evidence_axis": "source_only_belief_stress_fresh_holdout_delta_panel_result_audit",
            "evidence_increment": "audits M2787 fresh-holdout paired closed-loop diagnostic delta artifacts before interpretation",
            "claim_scope": (
                "Result audit only; no new execution training validation ranking promotion driver-performance "
                "paper high-fidelity self-ID or full-driver claim"
            ),
            "stop_condition": [
                "stop if M2787 required artifacts are incomplete",
                "stop if actor or claim boundaries fail",
                "stop if holdout seed indices overlap M2784 seed_index 0..3",
                "stop if paired deltas are interpreted as ranking or promotion evidence",
            ],
            "fallback_plan": [
                "route to artifact repair if required artifacts are missing",
                "route to branch synthesis if fresh-holdout deltas are negative weak mixed or claim boundaries fail",
                "route to broader architecture or scenario-distribution change if fresh holdout fails to show robust candidate signal",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2787 writes fresh-holdout paired source-vs-candidate closed-loop delta artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2787 fresh-holdout source-only paired delta panel artifacts",
            "admission_evidence": [
                "M2787 summary and gate artifacts exist",
                "M2787 writes paired execution and delta rows with source/candidate lineage",
                "M2787 is not validated ranked or promoted before this audit",
            ],
            "blocked_shortcuts": [
                "no new execution or training in M2788",
                "no validation ranking promotion success-rate verdict performance paper HF full-driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{task_id}.md",
                "M2788 status queue scoreboard research log and review",
            ],
            "next_stage_criteria": [
                "M2787 artifacts are complete and claim-safe or failure is classified",
                "one bounded follow-up or stop decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2788 audits source-only M2787 artifacts and cannot establish self-ID.",
            "history_necessity_tests": [
                "M2788 may check that M2787 covered history stress rows but runs no self-ID comparison."
            ],
            "temporal_evidence_window": "M2786-M2788 source-only fresh-holdout belief-stress branch.",
            "negative_result_policy": (
                "If M2787 artifacts fail or deltas are negative, preserve failure and route to "
                "synthesis or repair rather than weakening gates."
            ),
            "allowed_claims": [
                "M2787 fresh-holdout paired delta artifacts are accepted or rejected as complete and claim-safe",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fresh M2787 holdout paired closed-loop delta artifacts before any extension",
            "paper_verdict_delta": "no paper verdict; audit decides whether M2787 can be used as future engineering evidence",
            "must_synthesize_if": [
                "M2788 finds incomplete artifacts or claim-boundary failure",
                "another process-only milestone is proposed after M2788 without fresh evidence or synthesis",
            ],
        },
        "hypothesis": "M2787 fresh-holdout paired closed-loop delta artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{task_id}.md exists",
            "M2788 audits M2787 summary paired execution paired delta gate actor guard claim and lineage artifacts",
            "M2788 registers one bounded follow-up or stop decision",
            "M2788 makes no new execution training validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2788 executes new training or rollout",
            "M2788 treats M2787 as validation ranking or promotion evidence",
            "M2788 claims driver performance paper high-fidelity full-driver or self-ID result",
        ],
        "decision_rule": "Pass only if M2788 writes a claim-safe audit of M2787 artifacts and routes before interpretation.",
        "commands": [{"name": "audit_design_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{task_id}.md", "type": "md"}],
        "baseline_checkpoints": [summary["source_checkpoint"], summary["candidate_checkpoint"]],
        "baseline_artifacts": [summary["summary"], summary["gate_matrix"]],
        "scoreboard_checkpoint": f"docs/{task_id}.md",
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    failed = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    deltas = summary["delta_metric_summary"]
    lines = [
        "# M2787 Engineering Controller Route A Source-Only Belief-Stress Fresh-Holdout Delta Panel Preflight",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result_class: `{summary['result_class']}`",
        "- manifest: `experiments/manifests/m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight.json`",
        f"- summary: `{summary['summary']}`",
        f"- paired execution rows: `{summary['paired_execution_rows']}`",
        f"- paired delta rows: `{summary['paired_delta_rows']}`",
        f"- proof retention gates: `{summary['proof_retention_gate_rows']}`",
        f"- generalization holdout gates: `{summary['generalization_holdout_gate_rows']}`",
        f"- promotion guards: `{summary['promotion_guard_rows']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Result",
        "",
        "M2787 ran a bounded source-only HF0/FourWheel paired closed-loop diagnostic",
        "panel over the M2655 source checkpoint and the M2782 candidate checkpoint.",
        "It uses fresh holdout seed indices outside M2784 seed_index 0..3 and a",
        "longer horizon than M2784. The rows are candidate-vs-source deltas for",
        "audit, not a ranking or winner selection.",
        "",
        "```text",
        f"curriculum_rows: {summary['curriculum_row_count']}",
        f"seed_start_index: {summary['seed_start_index']}",
        f"seed_count: {summary['seed_count']}",
        f"fresh_holdout_seed_indices: {summary['fresh_holdout_seed_indices']}",
        f"m2784_seed_indices: {summary['m2784_seed_indices']}",
        f"horizon_steps: {summary['horizon_steps']}",
        f"m2784_horizon_steps: {summary['m2784_horizon_steps']}",
        f"paired_execution_rows: {summary['paired_execution_row_count']}",
        f"paired_delta_rows: {summary['paired_delta_row_count']}",
        f"proof_gate_rows: {summary['proof_gate_row_count']}",
        f"generalization_gate_rows: {summary['generalization_gate_row_count']}",
        f"promotion_guard_rows: {summary['promotion_guard_row_count']}",
        f"failed_gate_ids: {failed}",
        "```",
        "",
        "## Delta Summary",
        "",
        "```text",
        _metric_line(deltas, "candidate_minus_source_minimum_obstacle_clearance_m"),
        _metric_line(deltas, "candidate_minus_source_minimum_road_margin_m"),
        _metric_line(deltas, "candidate_minus_source_final_speed_mps"),
        _metric_line(deltas, "candidate_minus_source_max_abs_yaw_rate"),
        _metric_line(deltas, "candidate_minus_source_throttle_brake_conflict_proxy"),
        _metric_line(deltas, "mean_action_delta_l1"),
        "```",
        "",
        "## Actor And Claim Boundary",
        "",
        "Actor input stayed at P0 observation 72 and action 3. Stress, admission,",
        "curriculum, role, dynamics, outcome, success, progress, route, and verdict",
        "labels remained evaluator metadata and were not actor-visible. Mitigation",
        "reference rows stayed outside ordinary denominators.",
        "",
        "M2787 does not train, validate, rank, select a winner, promote a checkpoint,",
        "compute a success-rate verdict, claim repair success, driver performance,",
        "paper evidence, current-sim verdict, high-fidelity validation, full ideal",
        "driver completion, or level3 self-identification.",
        "",
        "## Route Decision",
        "",
        "Route to M2788 result audit before interpreting the fresh-holdout paired",
        "deltas or choosing any continuation, synthesis, repair, or stop decision.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_delta_metric_summary(delta_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    fields = [
        "candidate_minus_source_minimum_obstacle_clearance_m",
        "candidate_minus_source_minimum_road_margin_m",
        "candidate_minus_source_final_speed_mps",
        "candidate_minus_source_max_abs_yaw_rate",
        "candidate_minus_source_throttle_brake_conflict_proxy",
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2786-synthesis", type=Path, default=DEFAULT_M2786_SYNTHESIS)
    parser.add_argument("--m2785-audit", type=Path, default=DEFAULT_M2785_AUDIT)
    parser.add_argument("--m2784-dir", type=Path, default=DEFAULT_M2784_DIR)
    parser.add_argument("--m2782-dir", type=Path, default=DEFAULT_M2782_DIR)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed-start-index", type=int, default=DEFAULT_SEED_START_INDEX)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    args = parser.parse_args()
    run_belief_stress_fresh_holdout_delta_panel(
        args.output_dir,
        m2786_synthesis=args.m2786_synthesis,
        m2785_audit=args.m2785_audit,
        m2784_dir=args.m2784_dir,
        m2782_dir=args.m2782_dir,
        source_checkpoint=args.source_checkpoint,
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
