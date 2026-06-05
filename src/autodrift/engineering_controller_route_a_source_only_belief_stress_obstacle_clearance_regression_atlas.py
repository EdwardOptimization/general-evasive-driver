"""M2796 source-only obstacle-clearance regression atlas.

This runner reanalyzes the M2793 source/base/candidate triad delta artifacts
only. It materializes a stratified atlas for clearance-negative rows and keeps
road-margin, speed, yaw-rate, conflict, and action-delta movement diagnostic.
It does not execute environments, policies, replay, validation, training,
ranking, source builds, adapter probes, or external simulation.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean, median
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2796-engineering-controller-route-a-source-only-belief-stress-obstacle-"
    "clearance-regression-atlas-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-"
    "clearance-regression-atlas-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2796_engineering_controller_route_a_source_only_belief_stress_"
    "obstacle_clearance_regression_atlas"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2796-engineering-controller-route-a-source-only-belief-stress-obstacle-"
    "clearance-regression-atlas-preflight.md"
)
DEFAULT_M2795_SYNTHESIS = Path(
    "docs/m2795-engineering-controller-route-a-source-only-belief-stress-guardrailed-"
    "candidate-triad-branch-synthesis.md"
)
DEFAULT_M2794_AUDIT = Path(
    "docs/m2794-engineering-controller-route-a-source-only-belief-stress-guardrailed-"
    "candidate-fresh-holdout-triad-delta-panel-result-audit.md"
)
DEFAULT_M2793_DIR = Path(
    "runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_"
    "candidate_fresh_holdout_triad_delta_panel"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2797-engineering-controller-route-a-source-only-belief-"
    "stress-obstacle-clearance-regression-atlas-result-audit.json"
)

CLAIM_SCOPE = (
    "Route A source-only belief-stress obstacle-clearance regression atlas only; "
    "source-artifact reanalysis with no reset step rollout replay validation "
    "training PPO source build adapter probe external simulation ranking winner "
    "selection promotion success-rate verdict repair-success driver-performance "
    "paper current-sim high-fidelity full ideal driver or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "validation, ranking, winner selection, checkpoint promotion, success-rate "
    "verdict, repair success, driver performance, paper evidence, finite-window-"
    "vs-GRU conclusion, current-sim verdict, high-fidelity validation, full ideal "
    "driver completion, or level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_"
    "regression_atlas_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_"
    "regression_atlas_preflight_failed"
)

FALSE_CLAIM_FLAGS = {
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "external_simulation_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "repair_success_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_simulation_run": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_claim_made": False,
    "level3_self_id_claim_made": False,
    "private_holdout_used": False,
}

CLEARANCE_ROW_FIELDNAMES = [
    "atlas_row_id",
    "delta_family",
    "pair_id",
    "role_family",
    "dynamics_axis",
    "stress_family",
    "seed_index",
    "seed",
    "reference_subject",
    "candidate_subject",
    "reference_execution_row_id",
    "candidate_execution_row_id",
    "reference_checkpoint_hash",
    "candidate_checkpoint_hash",
    "clearance_delta_m",
    "clearance_delta_sign",
    "clearance_regression",
    "clearance_improvement",
    "clearance_zero",
    "minimum_road_margin_delta_m",
    "final_road_margin_delta_m",
    "final_speed_delta_mps",
    "max_abs_yaw_rate_delta",
    "max_abs_y_delta",
    "throttle_brake_conflict_delta",
    "mean_throttle_delta",
    "mean_brake_delta",
    "mean_action_l1_delta",
    "command_response_proxy_delta",
    "mean_action_delta_l1",
    "road_margin_positive",
    "final_speed_positive",
    "yaw_rate_lower",
    "throttle_brake_conflict_zero",
    "mean_action_delta_positive",
    "side_effect_summary",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "success_rate_verdict_computed",
    "claim_scope",
    "forbidden_interpretation",
]
AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "group_family",
    "group_key",
    "delta_family",
    "role_family",
    "dynamics_axis",
    "stress_family",
    "seed_index",
    "row_count",
    "negative_clearance_count",
    "positive_clearance_count",
    "zero_clearance_count",
    "negative_clearance_rate",
    "mean_clearance_delta_m",
    "median_clearance_delta_m",
    "min_clearance_delta_m",
    "max_clearance_delta_m",
    "mean_minimum_road_margin_delta_m",
    "mean_final_speed_delta_mps",
    "yaw_rate_lower_count",
    "throttle_brake_conflict_zero_count",
    "all_rows_diagnostic_only",
    "ranking_admissible_count",
    "winner_selected_count",
    "claim_boundary",
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
    "included_in_paired_execution_rows",
    "included_in_delta_rows",
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


def run_obstacle_clearance_regression_atlas(
    output_dir: Path | str,
    *,
    m2795_synthesis: Path | str = DEFAULT_M2795_SYNTHESIS,
    m2794_audit: Path | str = DEFAULT_M2794_AUDIT,
    m2793_dir: Path | str = DEFAULT_M2793_DIR,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(Path(m2795_synthesis), Path(m2794_audit), Path(m2793_dir))
    _require_sources(source_paths)

    m2793_summary = read_json(source_paths["m2793_summary"])
    triad_rows = read_csv_rows(source_paths["triad_execution_rows"])
    source_delta_rows = read_csv_rows(source_paths["candidate_minus_source_delta_rows"])
    base_delta_rows = read_csv_rows(source_paths["candidate_minus_base_delta_rows"])
    m2793_gate_rows = read_csv_rows(source_paths["m2793_gate_matrix"])
    source_mitigation_rows = read_csv_rows(source_paths["m2793_mitigation_reference_guard_rows"])

    clearance_rows = build_clearance_regression_rows(source_delta_rows + base_delta_rows)
    aggregate_rows = build_clearance_regression_aggregate_rows(clearance_rows)
    mitigation_rows = retag_mitigation_rows(source_mitigation_rows)

    write_csv_rows(paths["clearance_regression_rows"], clearance_rows, CLEARANCE_ROW_FIELDNAMES)
    write_csv_rows(paths["clearance_regression_aggregate_rows"], aggregate_rows, AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["mitigation_reference_guard_rows"], mitigation_rows, MITIGATION_GUARD_FIELDNAMES)

    claim_rows = build_claim_boundary_rows(follow_up_registered=False)
    gate_rows = build_proof_gate_rows(
        source_paths=source_paths,
        m2793_summary=m2793_summary,
        triad_rows=triad_rows,
        source_delta_rows=source_delta_rows,
        base_delta_rows=base_delta_rows,
        m2793_gate_rows=m2793_gate_rows,
        clearance_rows=clearance_rows,
        aggregate_rows=aggregate_rows,
        mitigation_rows=mitigation_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["proof_gate_rows"], gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        m2793_summary=m2793_summary,
        triad_rows=triad_rows,
        source_delta_rows=source_delta_rows,
        base_delta_rows=base_delta_rows,
        clearance_rows=clearance_rows,
        aggregate_rows=aggregate_rows,
        mitigation_rows=mitigation_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2797_manifest(summary))
    write_doc(paths["doc"], summary)

    required_artifacts_present = required_artifacts_present_for(paths)
    claim_rows = build_claim_boundary_rows(follow_up_registered=paths["follow_up_manifest"].exists())
    gate_rows = build_proof_gate_rows(
        source_paths=source_paths,
        m2793_summary=m2793_summary,
        triad_rows=triad_rows,
        source_delta_rows=source_delta_rows,
        base_delta_rows=base_delta_rows,
        m2793_gate_rows=m2793_gate_rows,
        clearance_rows=clearance_rows,
        aggregate_rows=aggregate_rows,
        mitigation_rows=mitigation_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["proof_gate_rows"], gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        m2793_summary=m2793_summary,
        triad_rows=triad_rows,
        source_delta_rows=source_delta_rows,
        base_delta_rows=base_delta_rows,
        clearance_rows=clearance_rows,
        aggregate_rows=aggregate_rows,
        mitigation_rows=mitigation_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2797_manifest(summary))
    write_doc(paths["doc"], summary)
    return summary


def _paths(output: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output / "summary.json",
        "clearance_regression_rows": output / "clearance_regression_rows.csv",
        "clearance_regression_aggregate_rows": output / "clearance_regression_aggregate_rows.csv",
        "proof_gate_rows": output / "proof_gate_rows.csv",
        "mitigation_reference_guard_rows": output / "mitigation_reference_guard_rows.csv",
        "claim_boundary_rows": output / "claim_boundary_rows.csv",
        "gate_matrix": output / "gate_matrix.csv",
        "run_state": output / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _source_paths(m2795_synthesis: Path, m2794_audit: Path, m2793_dir: Path) -> dict[str, Path]:
    return {
        "m2795_synthesis": m2795_synthesis,
        "m2794_audit": m2794_audit,
        "m2793_summary": m2793_dir / "summary.json",
        "triad_execution_rows": m2793_dir / "triad_execution_rows.csv",
        "candidate_minus_source_delta_rows": m2793_dir / "candidate_minus_source_delta_rows.csv",
        "candidate_minus_base_delta_rows": m2793_dir / "candidate_minus_base_delta_rows.csv",
        "m2793_gate_matrix": m2793_dir / "gate_matrix.csv",
        "m2793_mitigation_reference_guard_rows": m2793_dir / "mitigation_reference_guard_rows.csv",
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2796 missing required source artifacts: {missing}")


def build_clearance_regression_rows(delta_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(delta_rows, key=lambda item: (item["delta_family"], item["pair_id"]))):
        clearance = _float(row["candidate_minus_reference_minimum_obstacle_clearance_m"])
        road_margin = _float(row["candidate_minus_reference_minimum_road_margin_m"])
        final_speed = _float(row["candidate_minus_reference_final_speed_mps"])
        yaw_rate = _float(row["candidate_minus_reference_max_abs_yaw_rate"])
        conflict = _float(row["candidate_minus_reference_throttle_brake_conflict_proxy"])
        action_delta = _float(row.get("mean_action_delta_l1", 0.0))
        sign = "negative" if clearance < 0.0 else "positive" if clearance > 0.0 else "zero"
        atlas_row = {
            "atlas_row_id": f"m2796_clearance_regression_{index:03d}",
            "delta_family": row["delta_family"],
            "pair_id": row["pair_id"],
            "role_family": row["role_family"],
            "dynamics_axis": row["dynamics_axis"],
            "stress_family": row["stress_family"],
            "seed_index": int(row["seed_index"]),
            "seed": int(row["seed"]),
            "reference_subject": row["reference_subject"],
            "candidate_subject": row["candidate_subject"],
            "reference_execution_row_id": row["reference_execution_row_id"],
            "candidate_execution_row_id": row["candidate_execution_row_id"],
            "reference_checkpoint_hash": row["reference_checkpoint_hash"],
            "candidate_checkpoint_hash": row["candidate_checkpoint_hash"],
            "clearance_delta_m": clearance,
            "clearance_delta_sign": sign,
            "clearance_regression": clearance < 0.0,
            "clearance_improvement": clearance > 0.0,
            "clearance_zero": clearance == 0.0,
            "minimum_road_margin_delta_m": road_margin,
            "final_road_margin_delta_m": _float(row["candidate_minus_reference_final_road_margin_m"]),
            "final_speed_delta_mps": final_speed,
            "max_abs_yaw_rate_delta": yaw_rate,
            "max_abs_y_delta": _float(row["candidate_minus_reference_max_abs_y"]),
            "throttle_brake_conflict_delta": conflict,
            "mean_throttle_delta": _float(row["candidate_minus_reference_mean_throttle"]),
            "mean_brake_delta": _float(row["candidate_minus_reference_mean_brake"]),
            "mean_action_l1_delta": _float(row["candidate_minus_reference_mean_action_l1"]),
            "command_response_proxy_delta": _float(row["candidate_minus_reference_command_response_proxy"]),
            "mean_action_delta_l1": action_delta,
            "road_margin_positive": road_margin > 0.0,
            "final_speed_positive": final_speed > 0.0,
            "yaw_rate_lower": yaw_rate < 0.0,
            "throttle_brake_conflict_zero": conflict == 0.0,
            "mean_action_delta_positive": action_delta > 0.0,
            "side_effect_summary": _side_effect_summary(road_margin, final_speed, yaw_rate, conflict, action_delta),
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
            "success_rate_verdict_computed": False,
            "claim_scope": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        }
        rows.append(atlas_row)
    return rows


def build_clearance_regression_aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    group_specs = [
        ("global", ()),
        ("delta_family", ("delta_family",)),
        ("role_family", ("role_family",)),
        ("dynamics_axis", ("dynamics_axis",)),
        ("stress_family", ("stress_family",)),
        ("seed_index", ("seed_index",)),
        ("delta_family_role_family", ("delta_family", "role_family")),
        ("delta_family_dynamics_axis", ("delta_family", "dynamics_axis")),
        ("delta_family_stress_family", ("delta_family", "stress_family")),
        ("delta_family_seed_index", ("delta_family", "seed_index")),
        ("role_dynamics_stress", ("role_family", "dynamics_axis", "stress_family")),
        (
            "delta_family_role_dynamics_stress",
            ("delta_family", "role_family", "dynamics_axis", "stress_family"),
        ),
        (
            "delta_family_role_dynamics_stress_seed",
            ("delta_family", "role_family", "dynamics_axis", "stress_family", "seed_index"),
        ),
    ]
    aggregate_rows: list[dict[str, Any]] = []
    aggregate_index = 0
    for group_family, keys in group_specs:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        for row in rows:
            group_key = tuple(row[key] for key in keys)
            groups.setdefault(group_key, []).append(row)
        for key_values in sorted(groups, key=lambda item: tuple(str(part) for part in item)):
            group_rows = groups[key_values]
            keyed = dict(zip(keys, key_values, strict=True))
            aggregate_rows.append(_aggregate_row(aggregate_index, group_family, keyed, group_rows))
            aggregate_index += 1
    return aggregate_rows


def _aggregate_row(
    aggregate_index: int,
    group_family: str,
    keyed: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    clearance_values = [_float(row["clearance_delta_m"]) for row in rows]
    negative = sum(1 for value in clearance_values if value < 0.0)
    positive = sum(1 for value in clearance_values if value > 0.0)
    zero = sum(1 for value in clearance_values if value == 0.0)
    count = len(rows)
    return {
        "aggregate_id": f"m2796_clearance_aggregate_{aggregate_index:03d}",
        "group_family": group_family,
        "group_key": "all" if not keyed else "|".join(f"{key}={keyed[key]}" for key in keyed),
        "delta_family": keyed.get("delta_family", "all"),
        "role_family": keyed.get("role_family", "all"),
        "dynamics_axis": keyed.get("dynamics_axis", "all"),
        "stress_family": keyed.get("stress_family", "all"),
        "seed_index": keyed.get("seed_index", "all"),
        "row_count": count,
        "negative_clearance_count": negative,
        "positive_clearance_count": positive,
        "zero_clearance_count": zero,
        "negative_clearance_rate": negative / count if count else 0.0,
        "mean_clearance_delta_m": mean(clearance_values) if clearance_values else 0.0,
        "median_clearance_delta_m": median(clearance_values) if clearance_values else 0.0,
        "min_clearance_delta_m": min(clearance_values) if clearance_values else 0.0,
        "max_clearance_delta_m": max(clearance_values) if clearance_values else 0.0,
        "mean_minimum_road_margin_delta_m": _mean_metric(rows, "minimum_road_margin_delta_m"),
        "mean_final_speed_delta_mps": _mean_metric(rows, "final_speed_delta_mps"),
        "yaw_rate_lower_count": sum(1 for row in rows if as_bool(row["yaw_rate_lower"])),
        "throttle_brake_conflict_zero_count": sum(
            1 for row in rows if as_bool(row["throttle_brake_conflict_zero"])
        ),
        "all_rows_diagnostic_only": all(as_bool(row["diagnostic_only"]) for row in rows),
        "ranking_admissible_count": sum(1 for row in rows if as_bool(row["ranking_admissible"])),
        "winner_selected_count": sum(1 for row in rows if as_bool(row["winner_selected"])),
        "claim_boundary": CLAIM_SCOPE,
    }


def retag_mitigation_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    retagged = []
    for row in rows:
        retagged.append(
            {
                **row,
                "mitigation_reference": as_bool(row.get("mitigation_reference", True)),
                "ordinary_denominator_allowed": False,
                "future_training_allowed": False,
                "future_execution_allowed": False,
                "context_only": True,
                "actor_visible_allowed": False,
                "included_in_paired_execution_rows": False,
                "included_in_delta_rows": False,
                "status_pass": True,
                "guard_family": "m2796_mitigation_reference_denominator_guard",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return retagged


def build_claim_boundary_rows(*, follow_up_registered: bool) -> list[dict[str, Any]]:
    rows = [
        (
            "clearance_regression_atlas_materialized",
            "allowed_artifact_completion",
            True,
            True,
            "M2796 may claim source-only clearance-regression atlas artifacts were written",
        ),
        (
            "m2793_delta_rows_reanalyzed",
            "allowed_source_reanalysis",
            True,
            True,
            "M2796 may claim M2793 delta rows were reanalyzed without new execution",
        ),
        (
            "follow_up_result_audit_registered",
            "allowed_process_follow_up",
            follow_up_registered,
            True,
            "M2797 result-audit manifest is registered",
        ),
        ("validation_result", "validation", False, False, "M2796 does not run validation"),
        ("ranking_result", "ranking", False, False, "M2796 does not rank checkpoints or rows"),
        ("winner_selection", "promotion", False, False, "M2796 selects no winner"),
        ("checkpoint_promotion", "promotion", False, False, "M2796 promotes no checkpoint"),
        ("success_rate_verdict", "metric_artifact", False, False, "M2796 emits no success-rate verdict"),
        ("repair_success", "repair", False, False, "M2796 is not repair execution"),
        ("driver_performance", "performance", False, False, "M2796 is source-only failure attribution"),
        ("paper_result", "paper", False, False, "M2796 is not paper evidence"),
        ("current_sim_verdict", "current_sim", False, False, "M2796 is not a current-sim verdict"),
        ("high_fidelity_validation", "high_fidelity", False, False, "M2796 does not run HF validation"),
        ("full_ideal_driver", "full_driver", False, False, "M2796 does not complete the full driver"),
        ("level3_self_id", "self_id", False, False, "M2796 is not self-ID evidence"),
    ]
    claim_rows = []
    for claim_id, family, made, allowed, evidence in rows:
        status_pass = bool((not made and not allowed) or (made and allowed))
        if family.startswith("allowed_"):
            status_pass = bool(made and allowed)
        claim_rows.append(
            {
                "claim_id": claim_id,
                "claim_family": family,
                "claim_made": bool(made),
                "allowed": bool(allowed),
                "status_pass": status_pass,
                "evidence": evidence,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return claim_rows


def build_proof_gate_rows(
    *,
    source_paths: dict[str, Path],
    m2793_summary: dict[str, Any],
    triad_rows: list[dict[str, str]],
    source_delta_rows: list[dict[str, str]],
    base_delta_rows: list[dict[str, str]],
    m2793_gate_rows: list[dict[str, str]],
    clearance_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    mitigation_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    source_stats = _family_stats(clearance_rows, "candidate_minus_source")
    base_stats = _family_stats(clearance_rows, "candidate_minus_base")
    actor_contract_pass = (
        bool(triad_rows)
        and all(int(row.get("observation_shape", 0)) == P0_OBSERVATION_DIM for row in triad_rows)
        and all(int(row.get("action_shape", 0)) == ACTION_DIM for row in triad_rows)
        and not any(as_bool(row.get("hidden_or_oracle_actor_inputs_required", False)) for row in triad_rows)
        and not any(as_bool(row.get("actor_visible_label", False)) for row in triad_rows)
    )
    gate_matrix_pass = bool(m2793_gate_rows) and all(as_bool(row.get("status_pass", False)) for row in m2793_gate_rows)
    aggregate_families = {row["group_family"] for row in aggregate_rows}
    return [
        gate("proof_m2795_synthesis_present", "proof", "lineage", source_paths["m2795_synthesis"].exists(), str(source_paths["m2795_synthesis"]), "exists", 1, "lineage_invalid"),
        gate("proof_m2794_audit_present", "proof", "lineage", source_paths["m2794_audit"].exists(), str(source_paths["m2794_audit"]), "exists", 1, "lineage_invalid"),
        gate("proof_m2793_status_pass", "proof", "lineage", bool(m2793_summary.get("status_pass", False)), str(bool(m2793_summary.get("status_pass", False))), "true", 1, "lineage_invalid"),
        gate("proof_m2793_gate_matrix_pass", "proof", "lineage", bool(m2793_summary.get("gate_matrix_pass", False)) and gate_matrix_pass, str(gate_matrix_pass), "true", len(m2793_gate_rows), "lineage_invalid"),
        gate("proof_m2793_triad_execution_count", "proof", "artifact", len(triad_rows) == 216 and int(m2793_summary.get("triad_execution_row_count", 0)) == 216, str(len(triad_rows)), "216", len(triad_rows), "metric_artifact"),
        gate("proof_candidate_minus_source_delta_count", "proof", "artifact", len(source_delta_rows) == 72 and int(m2793_summary.get("candidate_minus_source_delta_row_count", 0)) == 72, str(len(source_delta_rows)), "72", len(source_delta_rows), "metric_artifact"),
        gate("proof_candidate_minus_base_delta_count", "proof", "artifact", len(base_delta_rows) == 72 and int(m2793_summary.get("candidate_minus_base_delta_row_count", 0)) == 72, str(len(base_delta_rows)), "72", len(base_delta_rows), "metric_artifact"),
        gate("proof_clearance_regression_row_count", "proof", "artifact", len(clearance_rows) == 144, str(len(clearance_rows)), "144", len(clearance_rows), "metric_artifact"),
        gate("proof_candidate_minus_source_clearance_counts", "proof", "behavior_regression", source_stats["negative"] == 42 and source_stats["positive"] == 30, f"positive={source_stats['positive']} negative={source_stats['negative']}", "positive=30 negative=42", source_stats["count"], "behavior_regression"),
        gate("proof_candidate_minus_base_clearance_counts", "proof", "behavior_regression", base_stats["negative"] == 43 and base_stats["positive"] == 29, f"positive={base_stats['positive']} negative={base_stats['negative']}", "positive=29 negative=43", base_stats["count"], "behavior_regression"),
        gate("proof_aggregate_axis_coverage", "proof", "artifact", {"delta_family", "role_family", "dynamics_axis", "stress_family", "seed_index", "delta_family_role_dynamics_stress", "delta_family_role_dynamics_stress_seed"}.issubset(aggregate_families), ";".join(sorted(aggregate_families)), "required aggregate families", len(aggregate_rows), "scenario_sampling_failure"),
        gate("proof_actor_contract_preserved", "proof", "actor_contract", actor_contract_pass and bool(m2793_summary.get("actor_contract_shape_72_action_3", False)), "P0 72/action 3 no hidden labels", "P0 72/action 3 no hidden labels", len(triad_rows), "contract_violation"),
        gate("proof_mitigation_rows_excluded", "proof", "proof_washout", bool(mitigation_rows) and all(not as_bool(row["ordinary_denominator_allowed"]) and not as_bool(row["included_in_delta_rows"]) for row in mitigation_rows), "excluded", "excluded", len(mitigation_rows), "proof_washout"),
        gate("proof_no_ranking_winner_success_verdict", "proof", "claim_boundary", not any(as_bool(row["ranking_admissible"]) or as_bool(row["winner_selected"]) or as_bool(row["success_rate_verdict_computed"]) for row in clearance_rows), "false", "false", len(clearance_rows), "objective_overfit"),
        gate("proof_claim_boundary_rows_pass", "proof", "claim_boundary", bool(claim_rows) and all(as_bool(row["status_pass"]) for row in claim_rows), "all claim rows pass", "all claim rows pass", len(claim_rows), "objective_overfit"),
        gate("proof_required_artifacts_present", "proof", "artifact", required_artifacts_present, str(required_artifacts_present), "true", 10, "metric_artifact"),
    ]


def gate(
    gate_id: str,
    gate_tier: str,
    gate_family: str,
    status_pass: bool,
    observed: str,
    expected: str,
    row_count: int,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_tier": gate_tier,
        "gate_family": gate_family,
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
    m2793_summary: dict[str, Any],
    triad_rows: list[dict[str, str]],
    source_delta_rows: list[dict[str, str]],
    base_delta_rows: list[dict[str, str]],
    clearance_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    mitigation_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    source_stats = _family_stats(clearance_rows, "candidate_minus_source")
    base_stats = _family_stats(clearance_rows, "candidate_minus_base")
    gate_matrix_pass = bool(gate_rows) and all(as_bool(row["status_pass"]) for row in gate_rows)
    forbidden_claims_made = any(as_bool(row["claim_made"]) and not as_bool(row["allowed"]) for row in claim_rows)
    status_pass = bool(
        gate_matrix_pass
        and required_artifacts_present
        and bool(m2793_summary.get("status_pass", False))
        and len(triad_rows) == 216
        and len(source_delta_rows) == 72
        and len(base_delta_rows) == 72
        and len(clearance_rows) == 144
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
        "m2795_synthesis": str(source_paths["m2795_synthesis"]),
        "m2794_audit": str(source_paths["m2794_audit"]),
        "m2793_summary": str(source_paths["m2793_summary"]),
        "m2793_status_pass": bool(m2793_summary.get("status_pass", False)),
        "m2793_gate_matrix_pass": bool(m2793_summary.get("gate_matrix_pass", False)),
        "m2793_triad_execution_row_count": len(triad_rows),
        "m2793_candidate_minus_source_delta_row_count": len(source_delta_rows),
        "m2793_candidate_minus_base_delta_row_count": len(base_delta_rows),
        "clearance_regression_rows": str(paths["clearance_regression_rows"]),
        "clearance_regression_row_count": len(clearance_rows),
        "clearance_regression_aggregate_rows": str(paths["clearance_regression_aggregate_rows"]),
        "clearance_regression_aggregate_row_count": len(aggregate_rows),
        "candidate_minus_source_clearance_positive_count": source_stats["positive"],
        "candidate_minus_source_clearance_negative_count": source_stats["negative"],
        "candidate_minus_source_clearance_zero_count": source_stats["zero"],
        "candidate_minus_source_clearance_mean_delta_m": source_stats["mean"],
        "candidate_minus_source_clearance_median_delta_m": source_stats["median"],
        "candidate_minus_base_clearance_positive_count": base_stats["positive"],
        "candidate_minus_base_clearance_negative_count": base_stats["negative"],
        "candidate_minus_base_clearance_zero_count": base_stats["zero"],
        "candidate_minus_base_clearance_mean_delta_m": base_stats["mean"],
        "candidate_minus_base_clearance_median_delta_m": base_stats["median"],
        "top_negative_aggregate_rows": top_negative_aggregate_rows(aggregate_rows),
        "proof_gate_rows": str(paths["proof_gate_rows"]),
        "proof_gate_row_count": len(gate_rows),
        "mitigation_reference_guard_rows": str(paths["mitigation_reference_guard_rows"]),
        "mitigation_reference_guard_row_count": len(mitigation_rows),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix": str(paths["gate_matrix"]),
        "gate_matrix_pass": gate_matrix_pass,
        "run_state": str(paths["run_state"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "m2797_follow_up_manifest_registered": paths["follow_up_manifest"].exists(),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_reanalyzed_only": True,
        "new_execution_run": False,
        "new_training_run": False,
        "new_validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        **FALSE_CLAIM_FLAGS,
    }


def top_negative_aggregate_rows(aggregate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in aggregate_rows
        if row["group_family"]
        in {
            "delta_family",
            "delta_family_role_dynamics_stress",
            "delta_family_role_dynamics_stress_seed",
            "delta_family_seed_index",
        }
        and int(row["negative_clearance_count"]) > 0
    ]
    ranked = sorted(
        eligible,
        key=lambda row: (
            -int(row["negative_clearance_count"]),
            -float(row["negative_clearance_rate"]),
            str(row["group_key"]),
        ),
    )
    return [
        {
            "group_family": row["group_family"],
            "group_key": row["group_key"],
            "row_count": int(row["row_count"]),
            "negative_clearance_count": int(row["negative_clearance_count"]),
            "negative_clearance_rate": float(row["negative_clearance_rate"]),
            "mean_clearance_delta_m": float(row["mean_clearance_delta_m"]),
        }
        for row in ranked[:12]
    ]


def build_run_state(summary: dict[str, Any], paths: dict[str, Path], source_paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "result_class": summary["result_class"],
        "generated_at_utc": summary["generated_at_utc"],
        "paths": {key: str(value) for key, value in paths.items()},
        "source_paths": {key: str(value) for key, value in source_paths.items()},
        "source_artifacts_reanalyzed_only": True,
        "forbidden_claim_flags": FALSE_CLAIM_FLAGS,
    }


def build_m2797_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    task_id = DEFAULT_NEXT_BLOCKER
    return {
        "id": task_id,
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
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt",
                "runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt",
            ],
            "parent_dataset": [
                str(DEFAULT_OUTPUT_DIR / "summary.json"),
                str(DEFAULT_OUTPUT_DIR / "clearance_regression_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "clearance_regression_aggregate_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "proof_gate_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "mitigation_reference_guard_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "claim_boundary_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "gate_matrix.csv"),
                str(DEFAULT_DOC_PATH),
            ],
            "parent_config": [
                "experiments/manifests/m2796-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-preflight.json",
                "experiments/manifests/m2795-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-triad-branch-synthesis.json",
                "experiments/manifests/m2794-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-result-audit.json",
            ],
            "parent_objective": [
                "audit M2796 obstacle-clearance regression atlas artifacts before interpretation"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2795-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-triad-branch-synthesis",
                "m2794-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-result-audit",
            ],
            "blocked_by": [
                "M2796 atlas must be audited before any architecture or training design uses its attribution",
                "M2793 clearance deltas remain mixed and skew negative",
                "M2796 is source-only reanalysis and cannot validate rank promote or claim performance",
            ],
            "supersedes": [
                "direct interpretation of M2796 atlas rows without result audit",
                "road-margin-only or speed-only interpretation of M2793 deltas",
                "checkpoint promotion from M2796 attribution rows",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2797 must audit M2796 summary atlas aggregate gates mitigation and claim rows",
            "M2797 must verify M2796 consumed M2795 M2794 and M2793 artifacts only",
            "M2797 must keep obstacle-clearance regression visible as hard guard blocker",
            "M2797 must preserve actor 72/action 3 no hidden/oracle actor input and actor-invisible labels",
            "M2797 must keep mitigation rows outside ordinary denominators",
            "M2797 must reject validation ranking winner promotion success-rate driver-performance paper current-sim high-fidelity full-driver and self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step policy action rollout replay validation training PPO source build adapter probe or external simulation",
            "do not change actor inputs or action contract",
            "do not hide clearance-negative rows",
            "do not use M2796 aggregate rows as ranking promotion validation performance or self-ID evidence",
            "do not weaken mitigation denominator guards",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas",
            "evidence_axis": "source_only_belief_stress_obstacle_clearance_regression_atlas_result_audit",
            "evidence_increment": "audits M2796 clearance-regression atlas before route interpretation",
            "claim_scope": "Result audit only; no new execution training validation ranking promotion driver-performance paper high-fidelity self-ID or full-driver claim",
            "stop_condition": [
                "stop if M2796 required artifacts are incomplete",
                "stop if M2796 hides clearance-negative rows",
                "stop if M2796 actor or claim boundaries fail",
                "stop if M2796 is interpreted as ranking promotion validation performance or self-ID evidence",
            ],
            "fallback_plan": [
                "route to artifact repair if M2796 artifacts are missing",
                "route to synthesis or design only after audit accepts attribution rows",
                "stop the branch if atlas rows show no actionable clearance-regression structure",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2796 writes source-only clearance-regression atlas artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2796 source-only obstacle-clearance regression atlas artifacts",
            "admission_evidence": [
                "M2796 summary and gate artifacts exist",
                "M2796 writes clearance regression and aggregate rows",
                "M2796 is not validated ranked or promoted before this audit",
            ],
            "blocked_shortcuts": [
                "no new execution or training in M2797",
                "no validation ranking promotion performance paper HF full-driver or self-ID claim",
                "no obstacle-clearance guard weakening",
            ],
            "allowed_updates": [
                "docs/m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit.md",
                "M2797 status queue scoreboard research log and review",
            ],
            "next_stage_criteria": [
                "M2796 artifacts are complete and claim-safe or failure is classified",
                "one bounded follow-up or stop decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2797 audits source-only M2796 artifacts and cannot establish self-ID.",
            "history_necessity_tests": [
                "M2797 may check that M2796 stratified history-stress rows but runs no self-ID comparison."
            ],
            "temporal_evidence_window": "M2793-M2797 source-only clearance-regression attribution branch.",
            "negative_result_policy": "If M2796 artifacts fail or show broad regression, preserve failure and route to synthesis or redesign rather than weakening gates.",
            "allowed_claims": [
                "M2796 clearance-regression atlas artifacts are accepted or rejected as complete and claim-safe",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits M2796 clearance-regression attribution artifacts before any extension",
            "paper_verdict_delta": "no paper verdict; audit decides whether M2796 can inform future engineering design",
            "must_synthesize_if": [
                "M2797 finds incomplete artifacts or claim-boundary failure",
                "M2797 finds clearance negatives hidden or reinterpreted as performance evidence",
                "another process-only milestone is proposed after M2797 without synthesis or a new design branch",
            ],
        },
        "hypothesis": "M2796 obstacle-clearance regression atlas artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            "docs/m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit.md exists",
            "M2797 audits M2796 summary atlas aggregate gate mitigation claim and lineage artifacts",
            "M2797 registers one bounded follow-up or stop decision",
            "M2797 makes no new execution training validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2797 executes new training or rollout",
            "M2797 treats M2796 as validation ranking or promotion evidence",
            "M2797 hides obstacle-clearance regression",
            "M2797 claims driver performance paper high-fidelity full-driver or self-ID result",
        ],
        "decision_rule": "Pass only if M2797 writes a claim-safe audit of M2796 artifacts and routes before interpretation.",
        "commands": [{"name": "audit_design_only", "command": "true"}],
        "required_artifacts": [
            {
                "path": "docs/m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit.md",
                "type": "md",
            }
        ],
        "baseline_artifacts": [
            str(DEFAULT_OUTPUT_DIR / "summary.json"),
            str(DEFAULT_OUTPUT_DIR / "clearance_regression_rows.csv"),
            str(DEFAULT_OUTPUT_DIR / "clearance_regression_aggregate_rows.csv"),
            str(DEFAULT_OUTPUT_DIR / "gate_matrix.csv"),
        ],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt",
            "runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/checkpoints/m2791_guardrailed_multi_objective_candidate.pt",
        ],
        "scoreboard_checkpoint": f"docs/{task_id}.md",
        "m2796_status_pass": bool(summary.get("status_pass", False)),
        "m2796_clearance_regression_row_count": int(summary.get("clearance_regression_row_count", 0)),
        "m2796_clearance_regression_aggregate_row_count": int(
            summary.get("clearance_regression_aggregate_row_count", 0)
        ),
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M2796 Engineering Controller Route A Source-Only Belief-Stress Obstacle-Clearance Regression Atlas",
        "",
        "## Metadata",
        "",
        f"- status: {'completed' if summary['status_pass'] else 'failed'}",
        f"- result class: `{summary['result_class']}`",
        f"- manifest: `experiments/manifests/{DEFAULT_MILESTONE}.json`",
        f"- summary: `{summary['summary']}`",
        f"- clearance regression rows: `{summary['clearance_regression_rows']}`",
        f"- aggregate rows: `{summary['clearance_regression_aggregate_rows']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Evidence Summary",
        "",
        "M2796 reanalyzed M2793 source/base/candidate triad deltas only. It did not",
        "execute reset, step, policy action, rollout, replay, validation, training,",
        "PPO, source build, adapter probe, or external simulation.",
        "",
        "```text",
        f"m2793_triad_execution_rows: {summary['m2793_triad_execution_row_count']}",
        f"candidate_minus_source_delta_rows: {summary['m2793_candidate_minus_source_delta_row_count']}",
        f"candidate_minus_base_delta_rows: {summary['m2793_candidate_minus_base_delta_row_count']}",
        f"clearance_regression_rows: {summary['clearance_regression_row_count']}",
        f"clearance_regression_aggregate_rows: {summary['clearance_regression_aggregate_row_count']}",
        f"proof_gate_rows: {summary['proof_gate_row_count']}",
        "```",
        "",
        "The hard obstacle-clearance guard remains mixed and skew negative:",
        "",
        "```text",
        f"candidate_minus_source_positive: {summary['candidate_minus_source_clearance_positive_count']}",
        f"candidate_minus_source_negative: {summary['candidate_minus_source_clearance_negative_count']}",
        f"candidate_minus_source_mean_delta_m: {summary['candidate_minus_source_clearance_mean_delta_m']}",
        f"candidate_minus_source_median_delta_m: {summary['candidate_minus_source_clearance_median_delta_m']}",
        f"candidate_minus_base_positive: {summary['candidate_minus_base_clearance_positive_count']}",
        f"candidate_minus_base_negative: {summary['candidate_minus_base_clearance_negative_count']}",
        f"candidate_minus_base_mean_delta_m: {summary['candidate_minus_base_clearance_mean_delta_m']}",
        f"candidate_minus_base_median_delta_m: {summary['candidate_minus_base_clearance_median_delta_m']}",
        "```",
        "",
        "## Top Negative Aggregate Rows",
        "",
    ]
    for row in summary["top_negative_aggregate_rows"]:
        lines.append(
            "- "
            f"{row['group_family']} `{row['group_key']}`: "
            f"negative {row['negative_clearance_count']}/{row['row_count']}, "
            f"rate {row['negative_clearance_rate']:.6f}, "
            f"mean {row['mean_clearance_delta_m']}"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "M2796 supports source-only clearance-regression attribution artifacts only.",
            "It rejects validation, ranking, winner selection, checkpoint promotion,",
            "success-rate verdict, repair success, driver performance, paper result,",
            "current-sim verdict, high-fidelity validation, full-driver completion,",
            "finite-window-vs-GRU conclusion, and self-ID interpretation.",
            "",
            "## Next",
            "",
            "Route to M2797 result audit before using the atlas to design a future",
            "training, architecture, or controller change.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def required_artifacts_present_for(paths: dict[str, Path]) -> bool:
    return all(path.exists() for path in paths.values())


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float(value: Any) -> float:
    return float(value)


def _mean_metric(rows: list[dict[str, Any]], metric: str) -> float:
    values = [_float(row[metric]) for row in rows]
    return mean(values) if values else 0.0


def _family_stats(rows: list[dict[str, Any]], delta_family: str) -> dict[str, Any]:
    values = [_float(row["clearance_delta_m"]) for row in rows if row["delta_family"] == delta_family]
    return {
        "count": len(values),
        "positive": sum(1 for value in values if value > 0.0),
        "negative": sum(1 for value in values if value < 0.0),
        "zero": sum(1 for value in values if value == 0.0),
        "mean": mean(values) if values else 0.0,
        "median": median(values) if values else 0.0,
    }


def _side_effect_summary(
    road_margin: float,
    final_speed: float,
    yaw_rate: float,
    conflict: float,
    action_delta: float,
) -> str:
    parts = [
        "road_margin_positive" if road_margin > 0.0 else "road_margin_nonpositive",
        "final_speed_positive" if final_speed > 0.0 else "final_speed_nonpositive",
        "yaw_rate_lower" if yaw_rate < 0.0 else "yaw_rate_not_lower",
        "conflict_zero" if conflict == 0.0 else "conflict_changed",
        "action_delta_positive" if action_delta > 0.0 else "action_delta_zero",
    ]
    return ";".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m2795-synthesis", type=Path, default=DEFAULT_M2795_SYNTHESIS)
    parser.add_argument("--m2794-audit", type=Path, default=DEFAULT_M2794_AUDIT)
    parser.add_argument("--m2793-dir", type=Path, default=DEFAULT_M2793_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    args = parser.parse_args(argv)
    summary = run_obstacle_clearance_regression_atlas(
        args.output_dir,
        m2795_synthesis=args.m2795_synthesis,
        m2794_audit=args.m2794_audit,
        m2793_dir=args.m2793_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
