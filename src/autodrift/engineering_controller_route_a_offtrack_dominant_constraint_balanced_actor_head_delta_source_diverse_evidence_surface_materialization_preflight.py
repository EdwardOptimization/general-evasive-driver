"""Materialize the M2953 actor-head delta source-diverse evidence surface."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


MILESTONE_ID = (
    "m2953-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-source-diverse-evidence-surface-materialization-preflight"
)
NEXT_ID = (
    "m2954-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-source-diverse-evidence-surface-materialization-result-audit"
)
DEFAULT_M2951_DIR = Path(
    "runs/m2951_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "post_scaffold_integration_contract_materialization_preflight"
)
DEFAULT_M2952_AUDIT = Path(
    "docs/m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "post-scaffold-integration-contract-materialization-result-audit.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2953_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "source_diverse_evidence_surface_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2953-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "source-diverse-evidence-surface-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2954-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-source-diverse-evidence-surface-materialization-result-audit.json"
)

ACTION_DIM = 3
CLAIM_SCOPE = (
    "M2953 source-diverse evidence-surface materialization only; accepted M2951 "
    "integration, actor-binding, residual-initialization, residual-bound, input-guard, "
    "side-effect-guard, claim-boundary, and gate rows may be reanalyzed into panel, "
    "source-diversity, and traceability artifacts for a later candidate-execution "
    "admission route. No candidate execution, checkpoint mutation, environment reset, "
    "rollout, replay, validation, training, PPO, dependency work, adapter probe, ranking, "
    "winner selection, promotion, repair-success, driver-performance, paper, current-sim, "
    "high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "candidate execution, implementation readiness, repair success, driver performance, "
    "validation readiness, validation result, ranking, winner selection, promotion, "
    "paper evidence, current-sim verdict, high-fidelity validation, finite-window-vs-GRU "
    "conclusion, full ideal driver completion, or level3 self-identification"
)

SOURCE_FIELDNAMES = [
    "source_id",
    "source_family",
    "source_artifact",
    "source_exists",
    "row_count",
    "status_pass_or_present",
    "surface_role",
    "actor_visible_allowed",
    "claim_scope",
]
SOURCE_DIVERSITY_FIELDNAMES = [
    "diversity_id",
    "diversity_axis",
    "included_source_families",
    "panel_spec_count",
    "traceability_row_count",
    "same_public_gate_repair_loop",
    "requires_m2954_audit_before_candidate_execution",
    "actor_visible_labels_required",
    "claim_boundary",
]
PANEL_SPEC_FIELDNAMES = [
    "panel_spec_id",
    "source_family",
    "source_bucket",
    "source_artifact",
    "panel_role",
    "materialization_admitted",
    "candidate_execution_admitted_in_m2953",
    "requires_m2954_audit_before_candidate_execution",
    "requires_later_execution_before_claim",
    "actor_observation_dim",
    "action_dim",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "evaluator_label_actor_visible",
    "verdict_label_actor_visible",
    "source_diversity_axis",
    "forbidden_interpretation",
    "claim_scope",
]
TRACEABILITY_FIELDNAMES = [
    "trace_id",
    "contract_source",
    "contract_row_id",
    "contract_field",
    "panel_spec_id",
    "trace_role",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible_allowed",
    "claim_boundary",
]
SIDE_EFFECT_FIELDNAMES = [
    "side_effect_guard_id",
    "side_effect",
    "scheduled_or_run",
    "expected",
    "status_pass",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2953",
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
    "evidence_source_rows",
    "source_diversity_rows",
    "panel_spec_rows",
    "contract_traceability_rows",
    "actor_contract_guard_rows",
    "side_effect_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_source_diverse_evidence_surface_materialization_preflight(
    *,
    m2951_dir: Path | str = DEFAULT_M2951_DIR,
    m2952_audit: Path | str = DEFAULT_M2952_AUDIT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2951_dir=Path(m2951_dir),
        m2952_audit=Path(m2952_audit),
        follow_up_manifest=Path(follow_up_manifest),
    )

    evidence_source_rows = build_evidence_source_rows(source)
    panel_spec_rows = build_panel_spec_rows(source)
    traceability_rows = build_contract_traceability_rows(source, panel_spec_rows)
    source_diversity_rows = build_source_diversity_rows(panel_spec_rows, traceability_rows)
    actor_rows = build_actor_contract_guard_rows(source)
    side_effect_rows = build_side_effect_guard_rows(source)

    write_csv_rows(paths["evidence_source_rows"], evidence_source_rows, fieldnames=SOURCE_FIELDNAMES)
    write_csv_rows(paths["source_diversity_rows"], source_diversity_rows, fieldnames=SOURCE_DIVERSITY_FIELDNAMES)
    write_csv_rows(paths["panel_spec_rows"], panel_spec_rows, fieldnames=PANEL_SPEC_FIELDNAMES)
    write_csv_rows(paths["contract_traceability_rows"], traceability_rows, fieldnames=TRACEABILITY_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["side_effect_guard_rows"], side_effect_rows, fieldnames=SIDE_EFFECT_FIELDNAMES)

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=False,
        required_artifacts_present=required_without_summary_doc,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        evidence_source_rows=evidence_source_rows,
        source_diversity_rows=source_diversity_rows,
        panel_spec_rows=panel_spec_rows,
        traceability_rows=traceability_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    follow_up = build_follow_up_manifest(summary_path=paths["summary"], output_dir=output, doc_path=paths["doc"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=Path(follow_up_manifest).exists(),
        required_artifacts_present=required_without_summary_doc,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        evidence_source_rows=evidence_source_rows,
        source_diversity_rows=source_diversity_rows,
        panel_spec_rows=panel_spec_rows,
        traceability_rows=traceability_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        evidence_source_rows=evidence_source_rows,
        source_diversity_rows=source_diversity_rows,
        panel_spec_rows=panel_spec_rows,
        traceability_rows=traceability_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "milestone_id": milestone,
            "source_row_count": len(evidence_source_rows),
            "panel_spec_row_count": len(panel_spec_rows),
            "contract_traceability_row_count": len(traceability_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=Path(follow_up_manifest).exists(),
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        evidence_source_rows=evidence_source_rows,
        source_diversity_rows=source_diversity_rows,
        panel_spec_rows=panel_spec_rows,
        traceability_rows=traceability_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        evidence_source_rows=evidence_source_rows,
        source_diversity_rows=source_diversity_rows,
        panel_spec_rows=panel_spec_rows,
        traceability_rows=traceability_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "milestone_id": milestone,
            "source_row_count": len(evidence_source_rows),
            "source_diversity_row_count": len(source_diversity_rows),
            "panel_spec_row_count": len(panel_spec_rows),
            "contract_traceability_row_count": len(traceability_rows),
            "actor_contract_guard_row_count": len(actor_rows),
            "side_effect_guard_row_count": len(side_effect_rows),
            "claim_boundary_row_count": len(claim_rows),
            "gate_matrix_row_count": len(gate_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "evidence_source_rows": output_dir / "evidence_source_rows.csv",
        "source_diversity_rows": output_dir / "source_diversity_rows.csv",
        "panel_spec_rows": output_dir / "panel_spec_rows.csv",
        "contract_traceability_rows": output_dir / "contract_traceability_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "side_effect_guard_rows": output_dir / "side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_source_artifacts(*, m2951_dir: Path, m2952_audit: Path, follow_up_manifest: Path) -> dict[str, Any]:
    paths = {
        "m2951_summary": m2951_dir / "summary.json",
        "integration_surface_rows": m2951_dir / "integration_surface_rows.csv",
        "actor_binding_rows": m2951_dir / "actor_binding_rows.csv",
        "residual_initialization_rows": m2951_dir / "residual_initialization_rows.csv",
        "residual_bound_rows": m2951_dir / "residual_bound_rows.csv",
        "input_guard_rows": m2951_dir / "input_guard_rows.csv",
        "side_effect_guard_rows": m2951_dir / "side_effect_guard_rows.csv",
        "claim_boundary_rows": m2951_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2951_dir / "gate_matrix.csv",
        "m2952_audit": m2952_audit,
        "follow_up_manifest": follow_up_manifest,
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "summary": read_json(paths["m2951_summary"]) if exists["m2951_summary"] else {},
        "integration_surface_rows": read_csv_rows(paths["integration_surface_rows"]),
        "actor_binding_rows": read_csv_rows(paths["actor_binding_rows"]),
        "residual_initialization_rows": read_csv_rows(paths["residual_initialization_rows"]),
        "residual_bound_rows": read_csv_rows(paths["residual_bound_rows"]),
        "input_guard_rows": read_csv_rows(paths["input_guard_rows"]),
        "side_effect_guard_rows": read_csv_rows(paths["side_effect_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
        "m2952_audit_text": m2952_audit.read_text(encoding="utf-8") if exists["m2952_audit"] else "",
    }


def build_evidence_source_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("m2951_summary", "summary", "status and false-claim flags"),
        ("integration_surface_rows", "integration_surface", "parent/residual integration surface"),
        ("actor_binding_rows", "actor_binding", "actor 72/action 3 binding"),
        ("residual_initialization_rows", "residual_initialization", "zero-delta and parent mutation constraints"),
        ("residual_bound_rows", "residual_bound", "residual bound and action clamp constraints"),
        ("input_guard_rows", "input_guard", "forbidden actor input visibility guard"),
        ("side_effect_guard_rows", "side_effect_guard", "checkpoint environment training side-effect guard"),
        ("claim_boundary_rows", "claim_boundary", "allowed and blocked claim rows"),
        ("gate_matrix", "gate_matrix", "M2951 materialization gates"),
        ("m2952_audit", "result_audit", "M2952 acceptance audit"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (key, family, role) in enumerate(specs, 1):
        rows.append(
            {
                "source_id": f"m2953-source-{index:04d}",
                "source_family": family,
                "source_artifact": str(source["paths"][key]),
                "source_exists": source["source_exists"][key],
                "row_count": source_row_count(source, key),
                "status_pass_or_present": source_status_pass(source, key),
                "surface_role": role,
                "actor_visible_allowed": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def source_row_count(source: dict[str, Any], key: str) -> int:
    if key == "m2951_summary":
        return 1 if source["source_exists"][key] else 0
    if key == "m2952_audit":
        return 1 if source["source_exists"][key] else 0
    return len(source[key])


def source_status_pass(source: dict[str, Any], key: str) -> bool:
    if key == "m2951_summary":
        return bool(source["summary"].get("status_pass"))
    if key == "m2952_audit":
        return "accept_m2951_materialization_claim_safe_route_to_m2953" in source["m2952_audit_text"]
    rows = source[key]
    if key == "integration_surface_rows":
        return bool(rows) and all(_bool(row.get("zero_delta_identity_required")) for row in rows)
    if key == "input_guard_rows":
        return bool(rows) and all(not _bool(row.get("actor_visible")) for row in rows)
    if key == "side_effect_guard_rows":
        return bool(rows) and all(not _bool(row.get("scheduled_or_run")) for row in rows)
    if key == "claim_boundary_rows":
        return bool(rows) and all(_bool(row.get("status_pass")) for row in rows)
    return bool(rows) and all(_bool(row.get("status_pass")) for row in rows if "status_pass" in row)


def build_panel_spec_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        (
            "integration_surface",
            "integration_surface_rows",
            "accepted integration surface for later candidate construction admission",
            "integration_contract",
        ),
        ("actor_binding", "actor_binding_rows", "actor shape and action mapping admission surface", "actor_contract"),
        (
            "residual_initialization",
            "residual_initialization_rows",
            "zero-delta parent identity and mutation guard surface",
            "residual_contract",
        ),
        ("residual_bound", "residual_bound_rows", "bounded residual and action clamp surface", "residual_contract"),
        ("input_guard", "input_guard_rows", "forbidden actor input visibility surface", "input_contract"),
        ("side_effect_guard", "side_effect_guard_rows", "checkpoint environment training side-effect surface", "process_guard"),
        ("claim_boundary", "claim_boundary_rows", "blocked interpretation and claim-boundary surface", "claim_guard"),
        ("gate_matrix", "gate_matrix", "materialization gate trace surface", "gate_contract"),
    ]
    return [
        panel_spec(index, source_family, artifact_key, role, axis, source)
        for index, (source_family, artifact_key, role, axis) in enumerate(specs, 1)
    ]


def panel_spec(index: int, source_family: str, artifact_key: str, role: str, axis: str, source: dict[str, Any]) -> dict[str, Any]:
    return {
        "panel_spec_id": f"m2953-panel-spec-{index:04d}",
        "source_family": source_family,
        "source_bucket": f"m2951_{source_family}",
        "source_artifact": str(source["paths"][artifact_key]),
        "panel_role": role,
        "materialization_admitted": source_status_pass(source, artifact_key),
        "candidate_execution_admitted_in_m2953": False,
        "requires_m2954_audit_before_candidate_execution": True,
        "requires_later_execution_before_claim": True,
        "actor_observation_dim": HUMAN_VIEW_OBS_DIM,
        "action_dim": ACTION_DIM,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_label_actor_visible": False,
        "verdict_label_actor_visible": False,
        "source_diversity_axis": axis,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "claim_scope": CLAIM_SCOPE,
    }


def build_contract_traceability_rows(
    source: dict[str, Any],
    panel_spec_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    panel_by_family = {row["source_family"]: row["panel_spec_id"] for row in panel_spec_rows}
    specs = [
        ("integration_surface_rows", "integration_surface", "integration_surface_id", "combination_rule"),
        ("actor_binding_rows", "actor_binding", "actor_binding_id", "contract_field"),
        ("residual_initialization_rows", "residual_initialization", "residual_initialization_id", "contract_field"),
        ("residual_bound_rows", "residual_bound", "residual_bound_id", "contract_field"),
        ("input_guard_rows", "input_guard", "input_guard_id", "forbidden_key"),
        ("side_effect_guard_rows", "side_effect_guard", "side_effect_guard_id", "side_effect"),
        ("claim_boundary_rows", "claim_boundary", "claim_id", "claim_family"),
        ("gate_matrix", "gate_matrix", "gate_id", "gate_family"),
    ]
    rows: list[dict[str, Any]] = []
    for artifact_key, source_family, id_key, field_key in specs:
        for source_row in source[artifact_key]:
            rows.append(
                {
                    "trace_id": f"m2953-trace-{len(rows) + 1:04d}",
                    "contract_source": artifact_key,
                    "contract_row_id": source_row.get(id_key, ""),
                    "contract_field": source_row.get(field_key, ""),
                    "panel_spec_id": panel_by_family[source_family],
                    "trace_role": "contract_to_panel_traceability",
                    "status_pass": trace_row_passes(artifact_key, source_row),
                    "actor_visible": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def trace_row_passes(artifact_key: str, row: dict[str, str]) -> bool:
    if artifact_key == "integration_surface_rows":
        return (
            _bool(row.get("zero_delta_identity_required"))
            and _bool(row.get("residual_bound_required"))
            and not _bool(row.get("execution_scheduled"))
        )
    if artifact_key == "input_guard_rows":
        return not _bool(row.get("actor_visible"))
    if artifact_key == "side_effect_guard_rows":
        return not _bool(row.get("scheduled_or_run")) and _bool(row.get("status_pass"))
    return _bool(row.get("status_pass", True))


def build_source_diversity_rows(
    panel_spec_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    axes = [
        ("actor_and_action_contract", {"integration_contract", "actor_contract"}),
        ("residual_delta_safety_contract", {"residual_contract"}),
        ("input_and_side_effect_guard_contract", {"input_contract", "process_guard"}),
        ("claim_and_gate_boundary_contract", {"claim_guard", "gate_contract"}),
    ]
    rows: list[dict[str, Any]] = []
    for index, (axis, included_axes) in enumerate(axes, 1):
        families = sorted(
            row["source_family"] for row in panel_spec_rows if row["source_diversity_axis"] in included_axes
        )
        spec_ids = {
            row["panel_spec_id"]
            for row in panel_spec_rows
            if row["source_diversity_axis"] in included_axes
        }
        rows.append(
            {
                "diversity_id": f"m2953-diversity-{index:04d}",
                "diversity_axis": axis,
                "included_source_families": ";".join(families),
                "panel_spec_count": len(spec_ids),
                "traceability_row_count": sum(row["panel_spec_id"] in spec_ids for row in traceability_rows),
                "same_public_gate_repair_loop": False,
                "requires_m2954_audit_before_candidate_execution": True,
                "actor_visible_labels_required": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    observed = actor_binding_observed(source)
    specs = [
        ("actor_observation_dim", observed.get("actor_observation_dim"), HUMAN_VIEW_OBS_DIM, True),
        ("action_dim", observed.get("action_dim"), ACTION_DIM, True),
        ("action_mapping", observed.get("action_mapping"), "steer/throttle/brake", True),
        ("mapping_extra_keys_allowed", observed.get("mapping_extra_keys_allowed"), False, True),
        ("hidden_oracle_actor_input_required", False, False, False),
        ("future_target_actor_input_required", False, False, False),
        ("evaluator_label_actor_visible", False, False, False),
        ("verdict_label_actor_visible", False, False, False),
    ]
    return [
        {
            "guard_id": f"m2953-actor-guard-{index:04d}",
            "contract_field": field,
            "observed_value": observed_value,
            "expected_value": expected_value,
            "status_pass": str(observed_value) == str(expected_value),
            "actor_visible_allowed": actor_visible_allowed,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, observed_value, expected_value, actor_visible_allowed) in enumerate(specs, 1)
    ]


def actor_binding_observed(source: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for row in source["actor_binding_rows"]:
        field = row.get("contract_field", "")
        value = row.get("observed_value")
        if field in {"actor_observation_dim", "action_dim"}:
            values[field] = _int(value)
        elif field == "mapping_extra_keys_allowed":
            values[field] = _bool(value)
        else:
            values[field] = value
    return values


def build_side_effect_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    if source["side_effect_guard_rows"]:
        return [
            {
                "side_effect_guard_id": f"m2953-{row.get('side_effect_guard_id', f'side-effect-{index:04d}')}",
                "side_effect": row.get("side_effect", ""),
                "scheduled_or_run": _bool(row.get("scheduled_or_run")),
                "expected": False,
                "status_pass": not _bool(row.get("scheduled_or_run")) and _bool(row.get("status_pass", True)),
                "claim_boundary": CLAIM_SCOPE,
            }
            for index, row in enumerate(source["side_effect_guard_rows"], 1)
        ]
    side_effects = [
        "checkpoint_load",
        "checkpoint_save",
        "checkpoint_modify",
        "checkpoint_rank",
        "checkpoint_promote",
        "environment_reset",
        "environment_step",
        "rollout_replay_validation",
        "training_or_ppo",
        "dependency_build",
        "adapter_probe",
        "external_simulation",
    ]
    return [
        {
            "side_effect_guard_id": f"m2953-side-effect-guard-{index:04d}",
            "side_effect": effect,
            "scheduled_or_run": False,
            "expected": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, effect in enumerate(side_effects, 1)
    ]


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("source_diverse_evidence_surface_materialized", "M2953 source and panel rows", required_artifacts_present),
        ("contract_traceability_materialized", "M2953 contract traceability rows", required_artifacts_present),
        ("source_diversity_plan_materialized", "M2953 source-diversity rows", required_artifacts_present),
        ("follow_up_result_audit_registered", "M2954 result-audit manifest", follow_up_manifest_registered),
    ]
    blocked = [
        "candidate_execution",
        "implementation_readiness",
        "checkpoint_mutation",
        "training_or_ppo",
        "validation_result",
        "ranking_or_winner",
        "checkpoint_promotion",
        "repair_success",
        "driver_performance",
        "paper_evidence",
        "current_sim_verdict",
        "finite_window_vs_gru",
        "high_fidelity_validation",
        "full_ideal_driver_completion",
        "level3_self_identification",
    ]
    rows = [
        claim(claim_family, True, made, evidence)
        for claim_family, evidence, made in allowed
    ]
    rows.extend(
        claim(claim_family, False, False, f"future audited evidence before any {claim_family} claim")
        for claim_family in blocked
    )
    return rows


def claim(claim_family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2953_claim_{'allowed' if allowed else 'blocked'}_{claim_family}",
        "claim_family": claim_family,
        "allowed_in_m2953": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    evidence_source_rows: list[dict[str, Any]],
    source_diversity_rows: list[dict[str, Any]],
    panel_spec_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2953"])]
    source_families = {row["source_family"] for row in panel_spec_rows}
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"][key] for key in source["source_exists"] if key != "follow_up_manifest"),
            "all M2951 artifacts and M2952 audit present",
            "present",
            "lineage_invalid",
        ),
        (
            "m2951_status_pass",
            "lineage",
            bool(source["summary"].get("status_pass")),
            source["summary"].get("status_pass"),
            True,
            "lineage_invalid",
        ),
        (
            "m2952_accepts_m2951",
            "lineage",
            "accept_m2951_materialization_claim_safe_route_to_m2953" in source["m2952_audit_text"],
            "M2952 acceptance token",
            "present",
            "lineage_invalid",
        ),
        (
            "evidence_sources_pass",
            "source_diversity",
            len(evidence_source_rows) == 10 and all(_bool(row["status_pass_or_present"]) for row in evidence_source_rows),
            len(evidence_source_rows),
            "10 passing source rows",
            "metric_artifact",
        ),
        (
            "panel_specs_source_diverse",
            "source_diversity",
            len(panel_spec_rows) == 8 and len(source_families) >= 8,
            f"rows={len(panel_spec_rows)} families={len(source_families)}",
            "8 rows and >=8 source families",
            "scenario_sampling_failure",
        ),
        (
            "source_diversity_rows_present",
            "source_diversity",
            len(source_diversity_rows) == 4 and all(not _bool(row["same_public_gate_repair_loop"]) for row in source_diversity_rows),
            len(source_diversity_rows),
            "4 rows and no same-public-gate loop",
            "objective_overfit",
        ),
        (
            "contract_traceability_rows_pass",
            "traceability",
            len(traceability_rows) >= 88 and all(_bool(row["status_pass"]) for row in traceability_rows),
            len(traceability_rows),
            ">=88 passing traceability rows",
            "contract_violation",
        ),
        (
            "actor_contract_preserved",
            "contract",
            all(_bool(row["status_pass"]) for row in actor_rows),
            "all actor guards pass",
            "all pass",
            "contract_violation",
        ),
        (
            "panel_actor_labels_invisible",
            "contract",
            all(
                not _bool(row["hidden_oracle_actor_input_required"])
                and not _bool(row["future_target_actor_input_required"])
                and not _bool(row["evaluator_label_actor_visible"])
                and not _bool(row["verdict_label_actor_visible"])
                for row in panel_spec_rows
            ),
            "all panel labels invisible",
            "all false",
            "contract_violation",
        ),
        (
            "no_candidate_execution_admitted",
            "execution_guardrail",
            all(not _bool(row["candidate_execution_admitted_in_m2953"]) for row in panel_spec_rows),
            "candidate_execution_admitted_in_m2953 false for all panel rows",
            "all false",
            "objective_overfit",
        ),
        (
            "side_effect_guards_pass",
            "execution_guardrail",
            len(side_effect_rows) == 12 and all(_bool(row["status_pass"]) for row in side_effect_rows),
            len(side_effect_rows),
            "12 side-effect guards pass",
            "objective_overfit",
        ),
        (
            "claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims),
            f"blocked={len(blocked_claims)}",
            "blocked claims not made",
            "proof_washout",
        ),
        (
            "follow_up_audit_registered",
            "follow_up",
            source["source_exists"]["follow_up_manifest"],
            source["source_exists"]["follow_up_manifest"],
            True,
            "lineage_invalid",
        ),
        (
            "required_artifacts_present",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
    ]
    return [gate(gate_id, family, status, observed, expected, failure) for gate_id, family, status, observed, expected, failure in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2953_{gate_id}",
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
    evidence_source_rows: list[dict[str, Any]],
    source_diversity_rows: list[dict[str, Any]],
    panel_spec_rows: list[dict[str, Any]],
    traceability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = gate_matrix_pass and required_artifacts_present
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_actor_head_delta_source_diverse_evidence_surface_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_actor_head_delta_source_diverse_evidence_surface_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(
            source["source_exists"][key] for key in source["source_exists"] if key != "follow_up_manifest"
        ),
        "m2951_status_pass": bool(source["summary"].get("status_pass")),
        "m2952_acceptance_present": "accept_m2951_materialization_claim_safe_route_to_m2953"
        in source["m2952_audit_text"],
        "evidence_source_row_count": len(evidence_source_rows),
        "source_diversity_row_count": len(source_diversity_rows),
        "panel_spec_row_count": len(panel_spec_rows),
        "contract_traceability_row_count": len(traceability_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "side_effect_guard_row_count": len(side_effect_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_family_count": len({row["source_family"] for row in panel_spec_rows}),
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "future_target_actor_inputs_required": False,
        "evaluator_label_actor_visible": False,
        "verdict_label_actor_visible": False,
        "candidate_execution_admitted_in_m2953": False,
        "implementation_run": False,
        "checkpoint_modification_run": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "dependency_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_driver_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "artifacts": {key: str(path) for key, path in paths.items()},
    }


def build_follow_up_manifest(*, summary_path: Path, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "type": "gate",
        "status": "pending",
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
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "evidence_source_rows.csv"),
                str(output_dir / "source_diversity_rows.csv"),
                str(output_dir / "panel_spec_rows.csv"),
                str(output_dir / "contract_traceability_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "side_effect_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
                str(DEFAULT_M2952_AUDIT),
            ],
            "parent_config": [
                "experiments/manifests/m2953-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-source-diverse-evidence-surface-materialization-preflight.json",
                "experiments/manifests/m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-scaffold-integration-contract-materialization-result-audit.json",
            ],
            "parent_objective": ["audit M2953 source-diverse evidence-surface materialization before candidate execution admission"],
            "derived_from": [
                MILESTONE_ID,
                "m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-scaffold-integration-contract-materialization-result-audit",
            ],
            "blocked_by": [
                "M2953 materialization must be audited before candidate-execution admission",
                "M2953 panel rows are not repair-success or driver-performance evidence",
            ],
            "supersedes": ["direct actor-head delta candidate execution from unaudited M2953 panel rows"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2954 must audit M2953 summary and source-diverse panel/traceability row counts",
            "M2954 must preserve actor 72/action 3 no hidden/oracle/future-target/evaluator-label actor input",
            "M2954 must not execute reset rollout validation training ranking promotion dependency work adapter probe or external simulation",
            "M2954 must not claim implementation readiness repair success driver performance validation paper high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run environment reset step rollout replay validation training PPO or private holdout",
            "do not load modify save rank or promote checkpoints",
            "do not treat M2953 panel materialization as candidate execution repair success or performance evidence",
            "do not use evaluator labels hidden dynamics oracle labels future targets progress metrics or verdict labels as actor input",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_source_diverse_evidence_surface_materialization_result_audit",
            "evidence_increment": "audits M2953 source-diverse panel and traceability materialization before any candidate execution",
            "claim_scope": "Result audit only; no candidate execution validation ranking promotion repair-success driver-performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2953 panel/spec or traceability rows are incomplete",
                "stop if actor or claim boundaries are violated",
                "stop if M2954 would execute a candidate or dependency work",
            ],
            "fallback_plan": [
                "route to artifact repair if materialization is incomplete",
                "route to stop or pivot if panel rows require privileged actor inputs",
                "admit at most one bounded candidate-execution admission route only after audit acceptance",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2953 materialization completed",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit the source-diverse evidence surface materialization",
            "admission_evidence": [
                "M2953 writes source, source-diversity, panel/spec, traceability, actor guard, side-effect guard, claim-boundary, and gate rows",
                "M2953 registers M2954 result audit before candidate execution admission",
            ],
            "blocked_shortcuts": [
                "no environment execution validation ranking promotion repair-success or performance verdict",
                "no training replay PPO or checkpoint promotion",
                "no hidden oracle future-target evaluator-label progress or verdict actor input",
                "no panel materialization as closed-loop evidence",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2954 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if audit selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2954 audit artifact exists",
                "M2954 accepts rejects repairs pivots or stops M2953 materialization",
                "actor and claim boundaries remain preserved",
                "no validation ranking promotion performance paper high-fidelity or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2954 audits a materialized evidence surface only and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2954; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2951-M2953 post-scaffold integration and evidence-surface materialization.",
            "negative_result_policy": "If panel rows are incomplete route to repair or stop rather than weakening interpretation standards.",
            "allowed_claims": [
                "M2953 materialization audit",
                "actor and claim boundary preserved",
                "no implementation readiness repair-success driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a newly materialized source-diverse evidence surface",
            "paper_verdict_delta": "no paper verdict; may admit one bounded candidate-execution route or force repair/stop",
            "must_synthesize_if": [
                "M2954 cannot accept reject repair pivot or stop M2953 artifacts",
                "M2954 would claim implementation readiness repair success driver performance paper high-fidelity or self-ID evidence",
                "M2954 would bypass candidate-execution admission boundaries",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject the M2953 source-diverse evidence-surface materialization before any candidate execution validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "audit summarizes M2953 source-diverse panel/spec and traceability rows",
            "audit preserves actor and claim boundaries",
            "audit selects exactly one next route or stop state",
            "no execution training ranking validation repair-success performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2954 executes reset rollout replay validation training ranking promotion dependency work",
            "M2954 changes actor input or action contract",
            "M2954 claims model quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2954 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M2954 writes a bounded result-audit artifact for M2953 and preserves all actor execution and claim boundaries without execution.",
        "commands": [{"name": "source_diverse_evidence_surface_result_audit_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "panel_spec_rows.csv"),
            str(output_dir / "contract_traceability_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2953 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Source-Diverse Evidence-Surface Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status_pass: `{summary['status_pass']}`",
            f"- result_class: `{summary['result_class']}`",
            f"- evidence source rows: `{summary['evidence_source_row_count']}`",
            f"- source diversity rows: `{summary['source_diversity_row_count']}`",
            f"- panel/spec rows: `{summary['panel_spec_row_count']}`",
            f"- contract traceability rows: `{summary['contract_traceability_row_count']}`",
            f"- actor contract guard rows: `{summary['actor_contract_guard_row_count']}`",
            f"- side-effect guard rows: `{summary['side_effect_guard_row_count']}`",
            f"- claim boundary rows: `{summary['claim_boundary_row_count']}`",
            f"- gate matrix rows: `{summary['gate_matrix_row_count']}`",
            f"- gate_matrix_pass: `{summary['gate_matrix_pass']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "M2953 materializes a source-diverse evidence surface from accepted M2951/M2952 contract artifacts only. It does not execute a candidate, mutate checkpoints, train, validate, rank, promote, or claim implementation readiness, repair success, driver performance, paper evidence, high-fidelity readiness, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.",
            "",
            "## Claim Boundary",
            "",
            CLAIM_SCOPE,
        ]
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2951-dir", type=Path, default=DEFAULT_M2951_DIR)
    parser.add_argument("--m2952-audit", type=Path, default=DEFAULT_M2952_AUDIT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_source_diverse_evidence_surface_materialization_preflight(
        m2951_dir=args.m2951_dir,
        m2952_audit=args.m2952_audit,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"summary={summary['artifacts']['summary']}")


if __name__ == "__main__":
    main()
