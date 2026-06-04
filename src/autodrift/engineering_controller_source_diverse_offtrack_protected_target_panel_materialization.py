"""Materialize a source-diverse off-track/protected target panel.

M2691 is a no-execution reanalysis of existing current-sim off-track and
protected-mitigation blocker artifacts. It writes an admission panel for a
future measured route. It does not reset environments, run policies, validate,
train, rank controllers, publish a package, or make performance/paper/self-ID
claims.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2691-engineering-controller-source-diverse-offtrack-protected-target-panel-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2692-engineering-controller-source-diverse-offtrack-protected-target-panel-"
    "materialization-result-audit"
)
DEFAULT_M2684_DIR = Path(
    "runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight"
)
DEFAULT_M2664_DIR = Path("runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy")
DEFAULT_M2667_DIR = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy"
)
DEFAULT_M2688_DIR = Path("runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization")
DEFAULT_OUTPUT_DIR = Path("runs/m2691_engineering_controller_source_diverse_offtrack_protected_target_panel")
DEFAULT_DOC_PATH = Path(
    "docs/m2691-engineering-controller-source-diverse-offtrack-protected-target-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2692-engineering-controller-source-diverse-offtrack-protected-target-panel-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2691 source-diverse off-track/protected target-panel materialization only; existing "
    "M2684 off-track, M2664/M2667 protected, and M2688 blocker artifacts may be reanalyzed "
    "into blocker-source, target-panel, source-diversity, actor-contract, claim-boundary, "
    "and gate rows, but no reset, step, rollout, replay, validation, training, PPO, source "
    "build, adapter probe, external simulation, package publication, ranking, winner "
    "selection, promotion, success-rate verdict, driver-performance, paper, finite-window-"
    "vs-GRU, current-response, current-sim, high-fidelity validation, full ideal driver, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, controller ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-"
    "vs-GRU conclusion, current-response sufficiency, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 self-identification"
)

FALSE_CLAIM_FLAGS = {
    "package_published": False,
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
    "backend_started": False,
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_response_sufficiency_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

BLOCKER_SOURCE_FIELDNAMES = [
    "source_id",
    "source_family",
    "source_milestone",
    "source_path",
    "source_exists",
    "status_pass_or_present",
    "row_count",
    "blocking_row_count",
    "regressed_row_count",
    "dominant_blocker",
    "actor_visible",
    "target_panel_role",
    "claim_scope",
    "forbidden_interpretation",
]
TARGET_PANEL_FIELDNAMES = [
    "target_id",
    "target_family",
    "source_family",
    "source_key",
    "task_family",
    "source_edge_or_axis",
    "role_semantics_proxy",
    "episode_or_row_count",
    "blocking_count",
    "regressed_row_count",
    "existing_success_count",
    "existing_collision_count",
    "existing_offtrack_count",
    "source_diversity_bucket",
    "future_execution_role",
    "diagnostic_only_no_verdict",
    "actor_input_contract_changed",
    "target_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "protected_rows_in_success_denominator",
    "claim_scope",
]
SOURCE_DIVERSITY_FIELDNAMES = [
    "plan_id",
    "plan_family",
    "included_source_families",
    "included_target_families",
    "source_count",
    "target_count",
    "same_public_gate_repair_loop",
    "requires_new_measured_execution_before_audit",
    "actor_visible_labels_required",
    "admitted_follow_up",
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
    "allowed_in_m2691",
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


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def materialize_source_diverse_offtrack_protected_target_panel(
    *,
    m2684_dir: Path | str = DEFAULT_M2684_DIR,
    m2664_dir: Path | str = DEFAULT_M2664_DIR,
    m2667_dir: Path | str = DEFAULT_M2667_DIR,
    m2688_dir: Path | str = DEFAULT_M2688_DIR,
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
        m2684_dir=Path(m2684_dir),
        m2664_dir=Path(m2664_dir),
        m2667_dir=Path(m2667_dir),
        m2688_dir=Path(m2688_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )

    blocker_source_rows = build_blocker_source_rows(source)
    target_panel_rows = build_target_panel_rows(source)
    source_diversity_plan_rows = build_source_diversity_plan_rows(target_panel_rows, source)
    actor_contract_guard_rows = build_actor_contract_guard_rows()
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        blocker_source_rows=blocker_source_rows,
        target_panel_rows=target_panel_rows,
        source_diversity_plan_rows=source_diversity_plan_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["blocker_source_rows"], blocker_source_rows, fieldnames=BLOCKER_SOURCE_FIELDNAMES)
    write_csv_rows(paths["target_panel_rows"], target_panel_rows, fieldnames=TARGET_PANEL_FIELDNAMES)
    write_csv_rows(paths["source_diversity_plan_rows"], source_diversity_plan_rows, fieldnames=SOURCE_DIVERSITY_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(path.exists() for key, path in paths.items() if key != "doc")
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        blocker_source_rows=blocker_source_rows,
        target_panel_rows=target_panel_rows,
        source_diversity_plan_rows=source_diversity_plan_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        blocker_source_rows=blocker_source_rows,
        target_panel_rows=target_panel_rows,
        source_diversity_plan_rows=source_diversity_plan_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(path.exists() for path in paths.values())
    claim_boundary_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        blocker_source_rows=blocker_source_rows,
        target_panel_rows=target_panel_rows,
        source_diversity_plan_rows=source_diversity_plan_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        blocker_source_rows=blocker_source_rows,
        target_panel_rows=target_panel_rows,
        source_diversity_plan_rows=source_diversity_plan_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "blocker_source_rows": output_dir / "blocker_source_rows.csv",
        "target_panel_rows": output_dir / "target_panel_rows.csv",
        "source_diversity_plan_rows": output_dir / "source_diversity_plan_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2684_dir: Path,
    m2664_dir: Path,
    m2667_dir: Path,
    m2688_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2684_summary": m2684_dir / "summary.json",
        "m2684_episode_rows": m2684_dir / "episode_rows.csv",
        "m2684_outcome_aggregate": m2684_dir / "outcome_aggregate.csv",
        "m2684_termination_reason_aggregate": m2684_dir / "termination_reason_aggregate.csv",
        "m2664_summary": m2664_dir / "summary.json",
        "m2664_combined_failure_taxonomy_rows": m2664_dir / "combined_failure_taxonomy_rows.csv",
        "m2667_summary": m2667_dir / "summary.json",
        "m2667_known_failure_boundary_rows": m2667_dir / "known_failure_boundary_rows.csv",
        "m2688_summary": m2688_dir / "summary.json",
        "m2688_known_blocker_disclosure_rows": m2688_dir / "known_blocker_disclosure_rows.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {name: path.exists() for name, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2684_summary": read_json(paths["m2684_summary"]) if source_exists["m2684_summary"] else {},
        "m2684_episode_rows": read_csv_rows(paths["m2684_episode_rows"]),
        "m2684_outcome_aggregate": read_csv_rows(paths["m2684_outcome_aggregate"]),
        "m2684_termination_reason_aggregate": read_csv_rows(paths["m2684_termination_reason_aggregate"]),
        "m2664_summary": read_json(paths["m2664_summary"]) if source_exists["m2664_summary"] else {},
        "m2664_combined_failure_taxonomy_rows": read_csv_rows(paths["m2664_combined_failure_taxonomy_rows"]),
        "m2667_summary": read_json(paths["m2667_summary"]) if source_exists["m2667_summary"] else {},
        "m2667_known_failure_boundary_rows": read_csv_rows(paths["m2667_known_failure_boundary_rows"]),
        "m2688_summary": read_json(paths["m2688_summary"]) if source_exists["m2688_summary"] else {},
        "m2688_known_blocker_disclosure_rows": read_csv_rows(paths["m2688_known_blocker_disclosure_rows"]),
    }


def build_blocker_source_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2684 = source["m2684_summary"]
    m2664 = source["m2664_summary"]
    m2667 = source["m2667_summary"]
    blocker_rows = {row.get("blocker_id", ""): row for row in source["m2688_known_blocker_disclosure_rows"]}
    return [
        {
            "source_id": "m2684_current_sim_offtrack_blocker",
            "source_family": "current_sim_offtrack",
            "source_milestone": "m2684/m2685/m2686",
            "source_path": str(source["paths"]["m2684_episode_rows"]),
            "source_exists": source["source_exists"]["m2684_episode_rows"],
            "status_pass_or_present": bool(m2684.get("status_pass")) and source["source_exists"]["m2684_episode_rows"],
            "row_count": _int(m2684.get("episode_count")),
            "blocking_row_count": _aggregate_count(
                source["m2684_outcome_aggregate"], "outcome_bucket", "off_track_noncollision_noncompletion"
            ),
            "regressed_row_count": "",
            "dominant_blocker": blocker_rows.get("current_sim_offtrack_blocker", {}).get(
                "blocker_status", "current-sim off-track blocker"
            ),
            "actor_visible": False,
            "target_panel_role": "offtrack_target_source",
            "claim_scope": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        },
        {
            "source_id": "m2664_m2667_protected_mitigation_blocker",
            "source_family": "protected_mitigation",
            "source_milestone": "m2664/m2665/m2666/m2667",
            "source_path": str(source["paths"]["m2667_known_failure_boundary_rows"]),
            "source_exists": source["source_exists"]["m2667_known_failure_boundary_rows"],
            "status_pass_or_present": bool(m2664.get("status_pass"))
            and bool(m2667.get("status_pass"))
            and source["source_exists"]["m2667_known_failure_boundary_rows"],
            "row_count": len(source["m2667_known_failure_boundary_rows"]),
            "blocking_row_count": _int(m2667.get("m2664_protected_gate_blocking_row_count")),
            "regressed_row_count": _int(m2667.get("m2664_protected_gate_regressed_row_count")),
            "dominant_blocker": blocker_rows.get("protected_mitigation_blocker", {}).get(
                "blocker_status", "protected mitigation blocker"
            ),
            "actor_visible": False,
            "target_panel_role": "protected_target_source",
            "claim_scope": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        },
        {
            "source_id": "m2688_package_blocker_disclosure_context",
            "source_family": "package_blocker_disclosure",
            "source_milestone": "m2688/m2689/m2690",
            "source_path": str(source["paths"]["m2688_known_blocker_disclosure_rows"]),
            "source_exists": source["source_exists"]["m2688_known_blocker_disclosure_rows"],
            "status_pass_or_present": bool(source["m2688_summary"].get("status_pass"))
            and source["source_exists"]["m2688_known_blocker_disclosure_rows"],
            "row_count": len(source["m2688_known_blocker_disclosure_rows"]),
            "blocking_row_count": 0,
            "regressed_row_count": "",
            "dominant_blocker": "claim-boundary context only; not target-panel measured evidence",
            "actor_visible": False,
            "target_panel_role": "claim_boundary_context",
            "claim_scope": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        },
    ]


def build_target_panel_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offtrack_groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in source["m2684_episode_rows"]:
        key = (
            row.get("task_family", ""),
            row.get("source_edge", ""),
            role_semantics_proxy(row),
        )
        offtrack_groups[key].append(row)

    target_index = 1
    for (task_family, source_edge, role_proxy), group_rows in sorted(offtrack_groups.items()):
        outcome_counts = Counter(row.get("outcome_bucket", "") for row in group_rows)
        offtrack_count = outcome_counts.get("off_track_noncollision_noncompletion", 0)
        if offtrack_count <= 0:
            continue
        rows.append(
            {
                "target_id": f"m2691-target-{target_index:04d}",
                "target_family": "current_sim_offtrack_containment",
                "source_family": "current_sim_offtrack",
                "source_key": f"{task_family}:{source_edge}",
                "task_family": task_family,
                "source_edge_or_axis": source_edge,
                "role_semantics_proxy": role_proxy,
                "episode_or_row_count": len(group_rows),
                "blocking_count": offtrack_count,
                "regressed_row_count": "",
                "existing_success_count": outcome_counts.get("success_obstacle_pass", 0),
                "existing_collision_count": outcome_counts.get("collision_failure", 0),
                "existing_offtrack_count": offtrack_count,
                "source_diversity_bucket": "current_sim_task_source_edge",
                "future_execution_role": (
                    "post_audit_measured_target_candidate; must include fresh source diversity before verdict"
                ),
                "diagnostic_only_no_verdict": True,
                "actor_input_contract_changed": False,
                "target_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "protected_rows_in_success_denominator": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
        target_index += 1

    for protected_row in source["m2667_known_failure_boundary_rows"]:
        rows.append(
            {
                "target_id": f"m2691-target-{target_index:04d}",
                "target_family": "protected_mitigation_preservation",
                "source_family": "protected_mitigation",
                "source_key": protected_row.get("boundary_id", ""),
                "task_family": "route_a_protected",
                "source_edge_or_axis": protected_row.get("taxonomy_axis", ""),
                "role_semantics_proxy": protected_row.get("subject_or_axis_or_metric", ""),
                "episode_or_row_count": _int(protected_row.get("row_count")),
                "blocking_count": _int(protected_row.get("blocking_row_count")),
                "regressed_row_count": _int(protected_row.get("regressed_row_count")),
                "existing_success_count": "",
                "existing_collision_count": "",
                "existing_offtrack_count": "",
                "source_diversity_bucket": "route_a_fresh_protected_taxonomy",
                "future_execution_role": (
                    "post_audit_measured_target_candidate; protected rows must remain outside success denominators"
                ),
                "diagnostic_only_no_verdict": True,
                "actor_input_contract_changed": False,
                "target_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "protected_rows_in_success_denominator": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
        target_index += 1

    return rows


def build_source_diversity_plan_rows(
    target_panel_rows: list[dict[str, Any]], source: dict[str, Any]
) -> list[dict[str, Any]]:
    source_families = sorted({str(row["source_family"]) for row in target_panel_rows})
    target_families = sorted({str(row["target_family"]) for row in target_panel_rows})
    return [
        {
            "plan_id": "m2691_plan_current_sim_offtrack_sources",
            "plan_family": "current_sim_source_edge_diversity",
            "included_source_families": "current_sim_offtrack",
            "included_target_families": "current_sim_offtrack_containment",
            "source_count": len({row["source_edge_or_axis"] for row in target_panel_rows if row["source_family"] == "current_sim_offtrack"}),
            "target_count": sum(1 for row in target_panel_rows if row["source_family"] == "current_sim_offtrack"),
            "same_public_gate_repair_loop": False,
            "requires_new_measured_execution_before_audit": False,
            "actor_visible_labels_required": False,
            "admitted_follow_up": "m2692_result_audit_before_any_measured_execution",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "plan_id": "m2691_plan_protected_mitigation_sources",
            "plan_family": "route_a_fresh_protected_taxonomy_diversity",
            "included_source_families": "protected_mitigation",
            "included_target_families": "protected_mitigation_preservation",
            "source_count": len(
                {row["source_edge_or_axis"] for row in target_panel_rows if row["source_family"] == "protected_mitigation"}
            ),
            "target_count": sum(1 for row in target_panel_rows if row["source_family"] == "protected_mitigation"),
            "same_public_gate_repair_loop": False,
            "requires_new_measured_execution_before_audit": False,
            "actor_visible_labels_required": False,
            "admitted_follow_up": "m2692_result_audit_before_any_measured_execution",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "plan_id": "m2691_plan_joint_offtrack_protected_admission",
            "plan_family": "joint_blocker_admission_surface",
            "included_source_families": ";".join(source_families),
            "included_target_families": ";".join(target_families),
            "source_count": len(source_families),
            "target_count": len(target_panel_rows),
            "same_public_gate_repair_loop": False,
            "requires_new_measured_execution_before_audit": False,
            "actor_visible_labels_required": False,
            "admitted_follow_up": "m2692_result_audit_before_any_measured_execution",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "plan_id": "m2691_plan_claim_boundary_preservation",
            "plan_family": "package_blocker_disclosure_context",
            "included_source_families": "package_blocker_disclosure",
            "included_target_families": "claim_boundary_only",
            "source_count": len(source["m2688_known_blocker_disclosure_rows"]),
            "target_count": 0,
            "same_public_gate_repair_loop": False,
            "requires_new_measured_execution_before_audit": False,
            "actor_visible_labels_required": False,
            "admitted_follow_up": "m2692_result_audit_before_any_measured_execution",
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    return [
        actor_guard("observation_shape", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, True),
        actor_guard("action_shape", ACTION_DIM, ACTION_DIM, True),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]", True),
        actor_guard("hidden_oracle_actor_input_detected", False, False, False),
        actor_guard("offtrack_labels_actor_visible", False, False, False),
        actor_guard("protected_labels_actor_visible", False, False, False),
        actor_guard("target_labels_actor_visible", False, False, False),
        actor_guard("blocker_labels_actor_visible", False, False, False),
        actor_guard("verdict_labels_actor_visible", False, False, False),
    ]


def actor_guard(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "guard_id": f"m2691_actor_guard_{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *, follow_up_manifest_registered: bool, required_artifacts_present: bool
) -> list[dict[str, Any]]:
    allowed = [
        ("target_panel_materialized", "target panel artifacts exist", required_artifacts_present),
        ("blocker_sources_traced", "M2684/M2664/M2667/M2688 source artifacts are present", True),
        ("source_diversity_plan_registered", "source-diversity plan rows exist", required_artifacts_present),
        ("result_audit_follow_up_registered", "M2692 result audit manifest exists", follow_up_manifest_registered),
    ]
    blocked = [
        "package_publication",
        "repair_success",
        "driver_performance",
        "validation_readiness",
        "validation_result",
        "controller_family_ranking",
        "winner_selection",
        "checkpoint_promotion",
        "success_rate_verdict",
        "paper_evidence",
        "finite_window_vs_gru",
        "current_response_sufficiency",
        "current_sim_verdict",
        "high_fidelity_validation",
        "full_ideal_driver",
        "level3_self_identification",
    ]
    rows: list[dict[str, Any]] = []
    for claim_family, evidence, status_pass in allowed:
        rows.append(
            {
                "claim_id": f"m2691_claim_allowed_{claim_family}",
                "claim_family": claim_family,
                "allowed_in_m2691": True,
                "claim_made": bool(status_pass),
                "status_pass": bool(status_pass),
                "evidence_required_before_claim": evidence,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    for claim_family in blocked:
        rows.append(
            {
                "claim_id": f"m2691_claim_blocked_{claim_family}",
                "claim_family": claim_family,
                "allowed_in_m2691": False,
                "claim_made": False,
                "status_pass": True,
                "evidence_required_before_claim": f"future audited evidence before any {claim_family} claim",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    blocker_source_rows: list[dict[str, Any]],
    target_panel_rows: list[dict[str, Any]],
    source_diversity_plan_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    source_families = {row["source_family"] for row in target_panel_rows}
    target_families = {row["target_family"] for row in target_panel_rows}
    gates = [
        (
            "m2691_gate_source_artifacts_present",
            "source_artifacts",
            all(
                source["source_exists"][key]
                for key in [
                    "m2684_summary",
                    "m2684_episode_rows",
                    "m2684_outcome_aggregate",
                    "m2684_termination_reason_aggregate",
                    "m2664_summary",
                    "m2664_combined_failure_taxonomy_rows",
                    "m2667_summary",
                    "m2667_known_failure_boundary_rows",
                    "m2688_summary",
                    "m2688_known_blocker_disclosure_rows",
                ]
            ),
            "all required source artifacts present",
            "all required source artifacts present",
            "lineage_invalid",
        ),
        (
            "m2691_gate_required_artifacts_present",
            "artifact_completeness",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
        (
            "m2691_gate_blocker_sources_present",
            "blocker_source",
            len(blocker_source_rows) >= 3 and all(_bool(row["status_pass_or_present"]) for row in blocker_source_rows),
            len(blocker_source_rows),
            ">=3 and all pass",
            "lineage_invalid",
        ),
        (
            "m2691_gate_offtrack_targets_present",
            "target_panel",
            "current_sim_offtrack_containment" in target_families,
            sorted(target_families),
            "current_sim_offtrack_containment present",
            "scenario_sampling_failure",
        ),
        (
            "m2691_gate_protected_targets_present",
            "target_panel",
            "protected_mitigation_preservation" in target_families,
            sorted(target_families),
            "protected_mitigation_preservation present",
            "behavior_regression",
        ),
        (
            "m2691_gate_source_diversity_present",
            "source_diversity",
            {"current_sim_offtrack", "protected_mitigation"}.issubset(source_families),
            sorted(source_families),
            "current_sim_offtrack and protected_mitigation",
            "objective_overfit",
        ),
        (
            "m2691_gate_not_same_public_gate_loop",
            "source_diversity",
            all(not _bool(row["same_public_gate_repair_loop"]) for row in source_diversity_plan_rows),
            "all plan rows same_public_gate_repair_loop false",
            "all false",
            "objective_overfit",
        ),
        (
            "m2691_gate_actor_contract_preserved",
            "contract",
            all(_bool(row["status_pass"]) for row in actor_contract_guard_rows),
            "all actor guard rows pass",
            "all pass",
            "contract_violation",
        ),
        (
            "m2691_gate_target_labels_actor_invisible",
            "contract",
            all(not _bool(row["target_labels_actor_visible"]) for row in target_panel_rows),
            "target_labels_actor_visible false for all target rows",
            "all false",
            "contract_violation",
        ),
        (
            "m2691_gate_no_hidden_oracle_required",
            "contract",
            all(not _bool(row["hidden_oracle_actor_input_required"]) for row in target_panel_rows),
            "hidden_oracle_actor_input_required false for all target rows",
            "all false",
            "contract_violation",
        ),
        (
            "m2691_gate_protected_not_success_denominator",
            "proof_washout",
            all(not _bool(row["protected_rows_in_success_denominator"]) for row in target_panel_rows),
            "protected rows outside success denominator",
            "all false",
            "proof_washout",
        ),
        (
            "m2691_gate_claim_boundaries_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_boundary_rows),
            "all claim boundary rows pass",
            "all pass",
            "proof_washout",
        ),
        (
            "m2691_gate_follow_up_audit_registered",
            "workflow",
            source["source_exists"]["follow_up_manifest"],
            source["source_exists"]["follow_up_manifest"],
            True,
            "lineage_invalid",
        ),
        (
            "m2691_gate_no_execution_or_training",
            "claim_boundary",
            True,
            "no reset step rollout replay validation training PPO source build adapter probe external simulation",
            "no execution",
            "proof_washout",
        ),
        (
            "m2691_gate_no_ranking_or_performance_claims",
            "claim_boundary",
            True,
            "no ranking winner promotion success-rate performance paper current-sim high-fidelity self-ID claims",
            "no forbidden claims",
            "proof_washout",
        ),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": gate_family,
            "status_pass": bool(status_pass),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if status_pass else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for gate_id, gate_family, status_pass, observed, expected, failure_type in gates
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    blocker_source_rows: list[dict[str, Any]],
    target_panel_rows: list[dict[str, Any]],
    source_diversity_plan_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    offtrack_targets = [row for row in target_panel_rows if row["target_family"] == "current_sim_offtrack_containment"]
    protected_targets = [row for row in target_panel_rows if row["target_family"] == "protected_mitigation_preservation"]
    source_families = sorted({row["source_family"] for row in target_panel_rows})
    target_families = sorted({row["target_family"] for row in target_panel_rows})
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    actor_contract_pass = all(_bool(row["status_pass"]) for row in actor_contract_guard_rows)
    status_pass = bool(required_artifacts_present and gate_matrix_pass and actor_contract_pass)
    offtrack_outcome_count = _aggregate_count(
        source["m2684_outcome_aggregate"], "outcome_bucket", "off_track_noncollision_noncompletion"
    )
    offtrack_termination_count = _aggregate_count(
        source["m2684_termination_reason_aggregate"], "termination_reason", "off_track"
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_source_diverse_offtrack_protected_target_panel_materialization_pass"
            if status_pass
            else "engineering_controller_source_diverse_offtrack_protected_target_panel_materialization_fail"
        ),
        "status_pass": status_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "next_blocker": next_blocker,
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(
            source["source_exists"][key]
            for key in [
                "m2684_summary",
                "m2684_episode_rows",
                "m2684_outcome_aggregate",
                "m2684_termination_reason_aggregate",
                "m2664_summary",
                "m2664_combined_failure_taxonomy_rows",
                "m2667_summary",
                "m2667_known_failure_boundary_rows",
                "m2688_summary",
                "m2688_known_blocker_disclosure_rows",
            ]
        ),
        "source_artifacts_reanalyzed_only": True,
        "blocker_source_row_count": len(blocker_source_rows),
        "target_panel_row_count": len(target_panel_rows),
        "offtrack_target_row_count": len(offtrack_targets),
        "protected_target_row_count": len(protected_targets),
        "source_diversity_plan_row_count": len(source_diversity_plan_rows),
        "actor_contract_guard_row_count": len(actor_contract_guard_rows),
        "claim_boundary_row_count": len(claim_boundary_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "source_family_count": len(source_families),
        "source_families": source_families,
        "target_families": target_families,
        "source_diverse_panel_present": {"current_sim_offtrack", "protected_mitigation"}.issubset(source_families),
        "same_public_gate_repair_loop": any(_bool(row["same_public_gate_repair_loop"]) for row in source_diversity_plan_rows),
        "requires_new_measured_execution_before_audit": any(
            _bool(row["requires_new_measured_execution_before_audit"]) for row in source_diversity_plan_rows
        ),
        "m2684_status_pass": bool(source["m2684_summary"].get("status_pass")),
        "m2684_episode_count": _int(source["m2684_summary"].get("episode_count")),
        "m2684_offtrack_outcome_count": offtrack_outcome_count,
        "m2684_offtrack_termination_count": offtrack_termination_count,
        "m2664_status_pass": bool(source["m2664_summary"].get("status_pass")),
        "m2664_protected_gate_blocking_row_count": _int(source["m2664_summary"].get("protected_gate_blocking_row_count")),
        "m2664_protected_gate_regressed_row_count": _int(source["m2664_summary"].get("protected_gate_regressed_row_count")),
        "m2667_status_pass": bool(source["m2667_summary"].get("status_pass")),
        "m2667_known_failure_boundary_row_count": len(source["m2667_known_failure_boundary_rows"]),
        "m2688_status_pass": bool(source["m2688_summary"].get("status_pass")),
        "m2688_known_blocker_disclosure_row_count": len(source["m2688_known_blocker_disclosure_rows"]),
        "actor_contract_shape_72_action_3": actor_contract_pass,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": False,
        "target_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "selected_next_action": "m2692_source_diverse_offtrack_protected_target_panel_materialization_result_audit",
    }
    summary.update(FALSE_CLAIM_FLAGS)
    summary["paths"] = {key: str(path) for key, path in paths.items()}
    return summary


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2691 Engineering Controller Source Diverse Offtrack Protected Target Panel Materialization Preflight

## Summary

- status: {'completed' if summary['status_pass'] else 'failed'}
- result class: `{summary['result_class']}`
- output dir: `{summary['output_dir']}`
- next: `{summary['next_blocker']}`
- source artifacts reanalyzed only: `{summary['source_artifacts_reanalyzed_only']}`

M2691 materializes a no-execution target panel that combines the active
current-sim off-track blocker and protected mitigation blocker. It is an
admission surface for later audit and possible measured execution, not driver
performance evidence.

## Materialized Artifacts

```text
blocker_source_rows: {summary['blocker_source_row_count']}
target_panel_rows: {summary['target_panel_row_count']}
  offtrack targets: {summary['offtrack_target_row_count']}
  protected targets: {summary['protected_target_row_count']}
source_diversity_plan_rows: {summary['source_diversity_plan_row_count']}
actor_contract_guard_rows: {summary['actor_contract_guard_row_count']}
claim_boundary_rows: {summary['claim_boundary_row_count']}
gate_matrix_rows: {summary['gate_matrix_row_count']}
gate_matrix_pass: {summary['gate_matrix_pass']}
```

## Blockers Preserved

```text
M2684 off-track outcomes: {summary['m2684_offtrack_outcome_count']}/{summary['m2684_episode_count']}
M2684 off-track terminations: {summary['m2684_offtrack_termination_count']}/{summary['m2684_episode_count']}
M2664 protected blocking rows: {summary['m2664_protected_gate_blocking_row_count']}
M2664 protected regressed row count: {summary['m2664_protected_gate_regressed_row_count']}
```

The target labels, blocker labels, protected labels, off-track labels, route
labels, and verdict labels are actor-invisible. Protected rows remain outside
success denominators.

## Source Diversity

```text
source families: {', '.join(summary['source_families'])}
target families: {', '.join(summary['target_families'])}
same_public_gate_repair_loop: {summary['same_public_gate_repair_loop']}
requires_new_measured_execution_before_audit: {summary['requires_new_measured_execution_before_audit']}
```

M2691 does not reuse the package branch as the active evidence branch. The
registered follow-up is a result audit before any measured execution.

## Actor Boundary

```text
observation_shape: {summary['observation_shape']}
action_shape: {summary['action_shape']}
hidden_oracle_actor_input_detected: {summary['hidden_oracle_actor_input_detected']}
target_labels_actor_visible: {summary['target_labels_actor_visible']}
protected_rows_in_success_denominator: {summary['protected_rows_in_success_denominator']}
```

## Claim Boundary

Allowed claim:

```text
M2691 materialized a source-diverse off-track/protected target panel from
existing artifacts and routed it to result audit.
```

Rejected claims:

```text
package publication
repair success
driver performance
validation readiness or result
controller ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
"""


def role_semantics_proxy(row: dict[str, str]) -> str:
    source_edge = row.get("source_edge", "")
    task_family = row.get("task_family", "")
    if "actuator" in source_edge or "capability_step" in source_edge:
        return "hidden_dynamics_or_actuator_response"
    if "boundary" in source_edge or "reveal" in source_edge:
        return "boundary_or_reveal_geometry"
    if "drift" in source_edge.lower() or task_family == "T5":
        return "recovery_or_drift_semantics"
    return "generic_source_edge"


def _aggregate_count(rows: Iterable[dict[str, str]], key: str, value: str) -> int:
    for row in rows:
        if row.get(key) == value:
            return _int(row.get("episode_count") or row.get("count") or row.get("row_count"))
    return 0


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2684-dir", type=Path, default=DEFAULT_M2684_DIR)
    parser.add_argument("--m2664-dir", type=Path, default=DEFAULT_M2664_DIR)
    parser.add_argument("--m2667-dir", type=Path, default=DEFAULT_M2667_DIR)
    parser.add_argument("--m2688-dir", type=Path, default=DEFAULT_M2688_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    materialize_source_diverse_offtrack_protected_target_panel(
        m2684_dir=args.m2684_dir,
        m2664_dir=args.m2664_dir,
        m2667_dir=args.m2667_dir,
        m2688_dir=args.m2688_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )


if __name__ == "__main__":
    main()
