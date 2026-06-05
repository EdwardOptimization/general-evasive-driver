"""Materialize M2724 offtrack repair candidates without execution.

M2725 converts the accepted M2724 design into source-bound candidate artifacts.
It does not overwrite active configs, execute environments, train, rank
profiles, or claim repair success.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2725-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-candidate-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2726-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-candidate-materialization-result-audit"
)
DEFAULT_M2724_DESIGN = Path(
    "docs/m2724-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-design-preflight.md"
)
DEFAULT_M2721_DIR = Path(
    "runs/m2721_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2725-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2726-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-result-audit.json"
)

EXPECTED_TARGET_COUNT = 31
EXPECTED_COLLISION_GUARDRAIL_COUNT = 2
EXPECTED_SUCCESS_CONTEXT_COUNT = 3
EXPECTED_PROTECTED_EXCLUSION_COUNT = 12

CLAIM_SCOPE = (
    "M2725 Route A current-M1690 exact-executable reentry offtrack repair "
    "candidate materialization only; no reset, step, rollout, replay, validation, "
    "training, PPO, private holdout, active config overwrite, profile-specific "
    "tuning, ranking, winner selection, promotion, success-rate verdict, "
    "repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-response, current-sim, high-fidelity validation, full ideal driver, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-response sufficiency, current-sim verdict, high-fidelity validation "
    "readiness or result, full ideal driver completion, or level3 self-identification"
)

SOURCE_FIELDNAMES = [
    "source_id",
    "source_family",
    "path",
    "present",
    "row_count",
    "status_pass",
    "claim_boundary",
]
CANDIDATE_FIELDNAMES = [
    "candidate_row_id",
    "source_panel_row_id",
    "source_candidate_id",
    "anchor_task_source_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "target_family",
    "repair_overlay_id",
    "guardrail_overlay_id",
    "target_accounted",
    "active_config_overwritten",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "target_labels_actor_visible",
    "profile_specific_tuning",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
    "claim_boundary",
]
OVERLAY_FIELDNAMES = [
    "overlay_row_id",
    "overlay_id",
    "overlay_family",
    "target_namespace",
    "target_key",
    "proposed_value",
    "preserves_parent_geometry",
    "active_config_overwritten",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "profile_specific_tuning",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "guardrail_row_id",
    "guardrail_family",
    "source_panel_row_id",
    "source_candidate_id",
    "profile_name",
    "task_family",
    "taxonomy_family",
    "target_panel_admitted",
    "execution_scheduled",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "claim_boundary",
]
ACTOR_FIELDNAMES = [
    "contract_row_id",
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
    "allowed_in_m2725",
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
    "source_accounting_rows",
    "candidate_target_rows",
    "shared_repair_overlay_rows",
    "guardrail_rows",
    "actor_contract_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]

REPAIR_OVERLAY_FIELDS = [
    ("road_containment", "env", "track_cost_scale", "2.8", True),
    ("road_containment", "env", "heading_cost_scale", "0.25", True),
    ("road_containment", "env", "road_margin_cost_scale", "1.2", True),
    ("road_containment", "env", "road_margin_warning_fraction", "0.65", True),
    ("road_containment", "env", "off_track_penalty", "6.0", True),
    ("road_containment", "env", "termination_penalty", "8.0", True),
    ("collision_clearance_guardrail", "env.obstacle", "collision_penalty", "25.0", True),
    ("collision_clearance_guardrail", "env.obstacle", "dense_clearance_margin_reward_scale", "0.5", True),
    ("collision_clearance_guardrail", "env.obstacle", "dense_clearance_margin_reward_window", "10.0", True),
    ("collision_clearance_guardrail", "env.obstacle", "dense_clearance_margin_reward_clip", "0.25", True),
    ("collision_clearance_guardrail", "env.obstacle", "clearance_margin_reward_scale", "1.0", True),
    ("collision_clearance_guardrail", "env.obstacle", "clearance_margin_reward_clip", "0.25", True),
    ("geometry_guardrail", "env", "track_width", "preserve_parent_value", True),
    ("geometry_guardrail", "env.obstacle", "distance_range", "preserve_parent_value", True),
    ("geometry_guardrail", "env.obstacle", "half_width_range", "preserve_parent_value", True),
]


def materialize_offtrack_repair_candidates(
    *,
    m2724_design: Path | str = DEFAULT_M2724_DESIGN,
    m2721_dir: Path | str = DEFAULT_M2721_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2724_design=Path(m2724_design),
        m2721_dir=Path(m2721_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )

    source_rows = build_source_accounting_rows(source=source)
    candidate_rows = build_candidate_rows(source["offtrack_target_rows"])
    overlay_rows = build_shared_repair_overlay_rows()
    guardrail_rows = build_guardrail_rows(
        collision_rows=source["collision_caution_rows"],
        success_rows=source["diagnostic_success_context_rows"],
        protected_rows=source["protected_exclusion_rows"],
    )
    actor_rows = build_actor_contract_rows(candidate_rows, overlay_rows, guardrail_rows)
    claim_rows = build_claim_boundary_rows(
        candidate_rows_present=bool(candidate_rows),
        overlay_rows_present=bool(overlay_rows),
        guardrail_rows_present=bool(guardrail_rows),
        actor_contract_pass=all(bool_value(row["status_pass"]) for row in actor_rows),
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["source_accounting_rows"], source_rows, fieldnames=SOURCE_FIELDNAMES)
    write_csv_rows(paths["candidate_target_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["shared_repair_overlay_rows"], overlay_rows, fieldnames=OVERLAY_FIELDNAMES)
    write_csv_rows(paths["guardrail_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_rows"], actor_rows, fieldnames=ACTOR_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(
        candidate_rows_present=bool(candidate_rows),
        overlay_rows_present=bool(overlay_rows),
        guardrail_rows_present=bool(guardrail_rows),
        actor_contract_pass=all(bool_value(row["status_pass"]) for row in actor_rows),
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "source_accounting_rows": output_dir / "source_accounting_rows.csv",
        "candidate_target_rows": output_dir / "candidate_target_rows.csv",
        "shared_repair_overlay_rows": output_dir / "shared_repair_overlay_rows.csv",
        "guardrail_rows": output_dir / "guardrail_rows.csv",
        "actor_contract_rows": output_dir / "actor_contract_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(*, m2724_design: Path, m2721_dir: Path, follow_up_manifest: Path) -> dict[str, Any]:
    paths = {
        "m2724_design_doc": m2724_design,
        "m2721_summary": m2721_dir / "summary.json",
        "m2721_offtrack_target_rows": m2721_dir / "offtrack_target_rows.csv",
        "m2721_collision_caution_rows": m2721_dir / "collision_caution_rows.csv",
        "m2721_diagnostic_success_context_rows": m2721_dir / "diagnostic_success_context_rows.csv",
        "m2721_protected_exclusion_rows": m2721_dir / "protected_exclusion_rows.csv",
        "m2721_actor_contract_join_rows": m2721_dir / "actor_contract_join_rows.csv",
        "m2721_claim_boundary_rows": m2721_dir / "claim_boundary_rows.csv",
        "m2721_gate_matrix": m2721_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2724_design_text": paths["m2724_design_doc"].read_text(encoding="utf-8")
        if source_exists["m2724_design_doc"]
        else "",
        "m2721_summary": read_json(paths["m2721_summary"]) if source_exists["m2721_summary"] else {},
        "offtrack_target_rows": read_csv_rows(paths["m2721_offtrack_target_rows"]),
        "collision_caution_rows": read_csv_rows(paths["m2721_collision_caution_rows"]),
        "diagnostic_success_context_rows": read_csv_rows(paths["m2721_diagnostic_success_context_rows"]),
        "protected_exclusion_rows": read_csv_rows(paths["m2721_protected_exclusion_rows"]),
        "actor_contract_join_rows": read_csv_rows(paths["m2721_actor_contract_join_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["m2721_claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["m2721_gate_matrix"]),
    }


def build_source_accounting_rows(*, source: dict[str, Any]) -> list[dict[str, Any]]:
    row_counts = {
        "m2721_offtrack_target_rows": len(source["offtrack_target_rows"]),
        "m2721_collision_caution_rows": len(source["collision_caution_rows"]),
        "m2721_diagnostic_success_context_rows": len(source["diagnostic_success_context_rows"]),
        "m2721_protected_exclusion_rows": len(source["protected_exclusion_rows"]),
        "m2721_actor_contract_join_rows": len(source["actor_contract_join_rows"]),
        "m2721_claim_boundary_rows": len(source["claim_boundary_rows"]),
        "m2721_gate_matrix": len(source["gate_matrix"]),
    }
    rows = []
    for index, (key, path) in enumerate(source["paths"].items(), start=1):
        rows.append(
            {
                "source_id": f"m2725-source-{index:04d}",
                "source_family": key,
                "path": str(path),
                "present": bool(source["source_exists"].get(key, False)),
                "row_count": row_counts.get(key, ""),
                "status_pass": bool(source["source_exists"].get(key, False)),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_candidate_rows(offtrack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(offtrack_rows, start=1):
        rows.append(
            {
                "candidate_row_id": f"m2725-candidate-target-{index:04d}",
                "source_panel_row_id": row.get("panel_row_id", ""),
                "source_candidate_id": row.get("candidate_id", ""),
                "anchor_task_source_id": row.get("anchor_task_source_id", ""),
                "workload_id": row.get("workload_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "task_family": row.get("task_family", ""),
                "target_family": "offtrack_repair_target",
                "repair_overlay_id": "m2725-shared-road-containment-overlay",
                "guardrail_overlay_id": "m2725-shared-collision-clearance-guardrail",
                "target_accounted": True,
                "active_config_overwritten": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "target_labels_actor_visible": False,
                "profile_specific_tuning": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_shared_repair_overlay_rows() -> list[dict[str, Any]]:
    rows = []
    for index, (family, namespace, key, value, preserves_geometry) in enumerate(REPAIR_OVERLAY_FIELDS, start=1):
        rows.append(
            {
                "overlay_row_id": f"m2725-overlay-{index:04d}",
                "overlay_id": f"m2725-shared-{family}-overlay",
                "overlay_family": family,
                "target_namespace": namespace,
                "target_key": key,
                "proposed_value": value,
                "preserves_parent_geometry": preserves_geometry,
                "active_config_overwritten": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "profile_specific_tuning": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_rows(
    *,
    collision_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    protected_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for family, source_rows in [
        ("collision_caution_guardrail", collision_rows),
        ("diagnostic_success_context", success_rows),
        ("protected_exclusion_guardrail", protected_rows),
    ]:
        for index, row in enumerate(source_rows, start=1):
            rows.append(
                {
                    "guardrail_row_id": f"m2725-{family}-{index:04d}",
                    "guardrail_family": family,
                    "source_panel_row_id": row.get("panel_row_id", ""),
                    "source_candidate_id": row.get("candidate_id", ""),
                    "profile_name": row.get("profile_name", ""),
                    "task_family": row.get("task_family", ""),
                    "taxonomy_family": row.get("taxonomy_family", ""),
                    "target_panel_admitted": False,
                    "execution_scheduled": False,
                    "protected_rows_in_success_denominator": False,
                    "diagnostic_only_no_verdict": True,
                    "actor_input_change": False,
                    "hidden_oracle_feature_injection": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def build_actor_contract_rows(
    candidate_rows: list[dict[str, Any]],
    overlay_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_rows = candidate_rows + overlay_rows + guardrail_rows
    return [
        actor_row("observation_shape", P0_OBSERVATION_DIM, 72, False),
        actor_row("action_shape", ACTION_DIM, 3, False),
        actor_row("hidden_oracle_actor_input_detected", any_bool(all_rows, "hidden_oracle_feature_injection"), False, False),
        actor_row("actor_input_change", any_bool(all_rows, "actor_input_change"), False, False),
        actor_row("target_labels_actor_visible", any_bool(candidate_rows, "target_labels_actor_visible"), False, False),
        actor_row("active_config_overwritten", any_bool(candidate_rows + overlay_rows, "active_config_overwritten"), False, False),
        actor_row("repair_execution_started", any_bool(all_rows, "repair_execution_started"), False, False),
        actor_row("training_started", any_bool(all_rows, "training_started"), False, False),
        actor_row("ranking_admissible", any_bool(candidate_rows + overlay_rows, "ranking_admissible"), False, False),
    ]


def actor_row(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "contract_row_id": f"m2725-actor-contract-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    candidate_rows_present: bool,
    overlay_rows_present: bool,
    guardrail_rows_present: bool,
    actor_contract_pass: bool,
    follow_up_manifest_registered: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("candidate_targets_materialized", "artifact", candidate_rows_present, "candidate_target_rows.csv"),
        ("shared_overlay_materialized", "artifact", overlay_rows_present, "shared_repair_overlay_rows.csv"),
        ("guardrails_materialized", "artifact", guardrail_rows_present, "guardrail_rows.csv"),
        ("actor_contract_preserved", "contract", actor_contract_pass, "actor_contract_rows.csv"),
        ("required_artifacts_present", "artifact", required_artifacts_present, "M2725 artifacts"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2726 result-audit manifest"),
    ]
    blocked = [
        ("environment_execution", "execution", "future execution manifest"),
        ("active_config_overwrite", "configuration", "future audited config application"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2725_{claim_id}",
        "claim_family": family,
        "allowed_in_m2725": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    overlay_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed_claims = [row for row in claim_rows if bool_value(row["allowed_in_m2725"])]
    blocked_claims = [row for row in claim_rows if not bool_value(row["allowed_in_m2725"])]
    guardrail_counts = count_by(guardrail_rows, "guardrail_family")
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2721/M2724/follow-up artifacts present", "lineage_invalid"),
        ("m2724_admits_materialization", "lineage", "admit_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization" in source["m2724_design_text"], "decision present", "decision present", "lineage_invalid"),
        ("m2721_status_pass", "lineage", bool_value(source["m2721_summary"].get("status_pass", False)), source["m2721_summary"].get("status_pass"), True, "lineage_invalid"),
        ("candidate_target_count", "artifact", len(candidate_rows) == EXPECTED_TARGET_COUNT, len(candidate_rows), EXPECTED_TARGET_COUNT, "metric_artifact"),
        ("overlay_rows_present", "artifact", bool(overlay_rows), len(overlay_rows), ">0", "metric_artifact"),
        ("collision_guardrail_count", "artifact", guardrail_counts.get("collision_caution_guardrail", 0) == EXPECTED_COLLISION_GUARDRAIL_COUNT, guardrail_counts.get("collision_caution_guardrail", 0), EXPECTED_COLLISION_GUARDRAIL_COUNT, "behavior_regression"),
        ("success_context_count", "artifact", guardrail_counts.get("diagnostic_success_context", 0) == EXPECTED_SUCCESS_CONTEXT_COUNT, guardrail_counts.get("diagnostic_success_context", 0), EXPECTED_SUCCESS_CONTEXT_COUNT, "metric_artifact"),
        ("protected_guardrail_count", "artifact", guardrail_counts.get("protected_exclusion_guardrail", 0) == EXPECTED_PROTECTED_EXCLUSION_COUNT, guardrail_counts.get("protected_exclusion_guardrail", 0), EXPECTED_PROTECTED_EXCLUSION_COUNT, "behavior_regression"),
        ("target_rows_accounted", "artifact", all(bool_value(row["target_accounted"]) for row in candidate_rows), "all accounted", "all true", "metric_artifact"),
        ("no_active_config_overwrite", "configuration", not any_bool(candidate_rows + overlay_rows, "active_config_overwritten"), "no active overwrite", "all false", "objective_overfit"),
        ("no_execution_or_training_started", "execution_guardrail", not any_bool(candidate_rows + overlay_rows + guardrail_rows, "repair_execution_started") and not any_bool(candidate_rows + overlay_rows, "training_started"), "no execution or training", "all false", "objective_overfit"),
        ("no_actor_input_change", "contract", not any_bool(candidate_rows + overlay_rows + guardrail_rows, "actor_input_change"), "actor input unchanged", "all false", "contract_violation"),
        ("target_labels_actor_invisible", "contract", not any_bool(candidate_rows, "target_labels_actor_visible"), "target labels actor-invisible", "all false", "contract_violation"),
        ("overlay_preserves_geometry", "contract", all(bool_value(row["preserves_parent_geometry"]) for row in overlay_rows), "geometry preserved", "all true", "contract_violation"),
        ("actor_contract_preserved", "contract", all(bool_value(row["status_pass"]) for row in actor_rows), f"rows={len(actor_rows)} pass={sum(bool_value(row['status_pass']) for row in actor_rows)}", "all actor rows pass", "contract_violation"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(bool_value(row["status_pass"]) for row in allowed_claims) and all(not bool_value(row["claim_made"]) and bool_value(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [gate(gate_id, family, status, observed, expected, failure_type) for gate_id, family, status, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2725_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    overlay_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    guardrail_counts = count_by(guardrail_rows, "guardrail_family")
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization_pass"
            if status_pass
            else "engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2721_status_pass": bool_value(source["m2721_summary"].get("status_pass", False)),
        "candidate_target_row_count": len(candidate_rows),
        "shared_repair_overlay_row_count": len(overlay_rows),
        "guardrail_row_count": len(guardrail_rows),
        "collision_guardrail_row_count": guardrail_counts.get("collision_caution_guardrail", 0),
        "diagnostic_success_context_guardrail_row_count": guardrail_counts.get("diagnostic_success_context", 0),
        "protected_exclusion_guardrail_row_count": guardrail_counts.get("protected_exclusion_guardrail", 0),
        "actor_contract_row_count": len(actor_rows),
        "actor_contract_rows_pass": all(bool_value(row["status_pass"]) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "active_config_overwritten": any_bool(candidate_rows + overlay_rows, "active_config_overwritten"),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "repair_execution_started": any_bool(candidate_rows + overlay_rows + guardrail_rows, "repair_execution_started"),
        "profile_specific_tuning": any_bool(candidate_rows + overlay_rows, "profile_specific_tuning"),
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": any_bool(candidate_rows + overlay_rows + guardrail_rows, "hidden_oracle_feature_injection"),
        "actor_input_change": any_bool(candidate_rows + overlay_rows + guardrail_rows, "actor_input_change"),
        "target_labels_actor_visible": any_bool(candidate_rows, "target_labels_actor_visible"),
        "profile_ranking_allowed": any_bool(candidate_rows + overlay_rows, "ranking_admissible"),
        "winner_selected": any_bool(candidate_rows + overlay_rows, "winner_selected"),
        "checkpoint_promoted": False,
        "protected_rows_in_success_denominator": any_bool(guardrail_rows, "protected_rows_in_success_denominator"),
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_response_sufficiency_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2725 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Candidate Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- candidate target rows: {summary['candidate_target_row_count']}",
            f"- shared repair overlay rows: {summary['shared_repair_overlay_row_count']}",
            f"- guardrail rows: {summary['guardrail_row_count']}",
            f"- actor contract rows: {summary['actor_contract_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2725 materializes repair candidates only. It does not overwrite active configs or execute environments.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Artifacts",
            "",
            *[f"- {key}: `{value}`" for key, value in summary["paths"].items()],
            "",
            "## Next",
            "",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
        ]
    )


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def any_bool(rows: list[dict[str, Any]], key: str) -> bool:
    return any(bool_value(row.get(key, False)) for row in rows)


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2724-design", type=Path, default=DEFAULT_M2724_DESIGN)
    parser.add_argument("--m2721-dir", type=Path, default=DEFAULT_M2721_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args(argv)

    summary = materialize_offtrack_repair_candidates(
        m2724_design=args.m2724_design,
        m2721_dir=args.m2721_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"candidate_target_row_count={summary['candidate_target_row_count']}")
    print(f"guardrail_row_count={summary['guardrail_row_count']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
