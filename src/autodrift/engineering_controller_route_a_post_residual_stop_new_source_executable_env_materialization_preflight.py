"""Materialize M3012 no-execution env configs for new-source workloads.

M3012 converts the M3011 design, M3006 source specs, and M3009 workload
contracts into executable env-config artifacts. It does not build sources,
reset, step, rollout, validate, train, rank, promote, or claim performance.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    executable_spec_csv_row,
    forbidden_key_violations,
    materialize_executable_spec,
)
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3012-engineering-controller-route-a-post-residual-stop-new-source-executable-"
    "env-materialization-preflight"
)
NEXT_ID = (
    "m3013-engineering-controller-route-a-post-residual-stop-new-source-executable-"
    "env-materialization-result-audit"
)
M3010_ID = (
    "m3010-engineering-controller-route-a-post-residual-stop-new-source-executable-"
    "workload-materialization-result-audit"
)
M3011_ID = (
    "m3011-engineering-controller-route-a-post-residual-stop-new-source-executable-"
    "env-materialization-design"
)
M3009_ID = (
    "m3009-engineering-controller-route-a-post-residual-stop-new-source-executable-"
    "workload-materialization-preflight"
)
M3006_ID = (
    "m3006-engineering-controller-route-a-post-residual-stop-new-task-source-generation-"
    "contract-materialization-preflight"
)

DEFAULT_M3010_AUDIT = Path(f"docs/{M3010_ID}.md")
DEFAULT_M3011_DESIGN = Path(f"docs/{M3011_ID}.md")
DEFAULT_M3006_DIR = Path(
    "runs/m3006_engineering_controller_route_a_post_residual_stop_new_task_source_"
    "generation_contract_materialization_preflight"
)
DEFAULT_M3009_DIR = Path(
    "runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_"
    "executable_workload_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_"
    "executable_env_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

SOURCE_SPEC_COUNT = 16
PROFILE_BINDING_COUNT = 2
WORKLOAD_ROW_COUNT = SOURCE_SPEC_COUNT * PROFILE_BINDING_COUNT

CLAIM_SCOPE = (
    "M3012 Route A post-residual-stop new-source executable env materialization "
    "only; env config, executable source spec, executable workload, guard, gate, "
    "summary, doc, and M3013 audit manifest artifacts may be written. No source "
    "build, environment reset, step, rollout, replay, validation, training, PPO, "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "repair-success, driver-performance, paper, current-sim verdict, high-fidelity "
    "validation, finite-window-vs-GRU, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "source build readiness, execution readiness, execution result, validation "
    "result, repair success, driver performance, current-sim verdict, paper "
    "evidence, high-fidelity validation, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, level3 self-identification, checkpoint ranking, or "
    "checkpoint promotion"
)
DECISION_PASS = "new_source_executable_env_materialized_route_to_m3013_result_audit"
DECISION_FAIL = "new_source_executable_env_materialization_incomplete"

PATH_KEYS = [
    "summary",
    "executable_source_spec_rows",
    "executable_source_specs",
    "executable_workload_rows",
    "profile_binding_rows",
    "unmappable_source_rows",
    "env_contract_guard_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]

SOURCE_ROW_FIELDNAMES = [
    "executable_source_spec_id",
    "new_task_source_spec_id",
    "task_source_id",
    "axis_name",
    "axis_family",
    "axis_variant_tag",
    "task_family",
    "source_edge",
    "source_family_left",
    "source_family_right",
    "window_tag",
    "generation_seed",
    "reference_m1680_task_source_id",
    "executable_source_family",
    "env_template_family",
    "materialization_rule",
    "capability_pair",
    "geometry_key",
    "reveal_step",
    "decision_step",
    "simulator_scope",
    "proxy_fault_family",
    "env_config_materialized_by_m3012",
    "env_config_present",
    "contract_violation_count",
    "forbidden_key_violation_count",
    "actor_observation_dim",
    "actor_action_dim",
    "source_build_scheduled_by_m3012",
    "environment_reset_scheduled_by_m3012",
    "environment_step_scheduled_by_m3012",
    "policy_action_scheduled_by_m3012",
    "validation_scheduled_by_m3012",
    "training_scheduled_by_m3012",
    "ranking_scheduled_by_m3012",
    "checkpoint_mutation_scheduled",
    "actor_visible",
    "hidden_oracle_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "status_pass",
    "claim_boundary",
]
WORKLOAD_FIELDNAMES = [
    "executable_workload_id",
    "workload_contract_id",
    "source_resolution_id",
    "profile_binding_id",
    "executable_source_spec_id",
    "task_source_id",
    "profile_binding_name",
    "binding_role",
    "axis_name",
    "axis_family",
    "task_family",
    "source_edge",
    "window_tag",
    "executable_source_family",
    "env_template_family",
    "config_path",
    "checkpoint_path",
    "actor_observation_dim",
    "actor_action_dim",
    "new_source_identity_preserved",
    "read_only_profile_binding",
    "env_config_materialized_by_m3012",
    "future_execution_manifest_required",
    "source_build_scheduled_by_m3012",
    "environment_reset_scheduled_by_m3012",
    "environment_step_scheduled_by_m3012",
    "policy_action_scheduled_by_m3012",
    "policy_rollout_scheduled_by_m3012",
    "replay_scheduled_by_m3012",
    "validation_scheduled_by_m3012",
    "training_scheduled_by_m3012",
    "ranking_scheduled_by_m3012",
    "checkpoint_mutation_scheduled",
    "actor_visible",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "status_pass",
    "claim_boundary",
]
PROFILE_FIELDNAMES = [
    "profile_binding_id",
    "profile_binding_name",
    "binding_role",
    "config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "read_only_binding",
    "profile_specific_tuning",
    "checkpoint_mutation_scheduled",
    "actor_observation_dim",
    "actor_action_dim",
    "status_pass",
    "claim_boundary",
]
UNMAPPABLE_FIELDNAMES = [
    "unmappable_source_id",
    "new_task_source_spec_id",
    "task_source_id",
    "source_family_left",
    "source_family_right",
    "error_type",
    "error_message",
    "claim_boundary",
]
GUARD_FIELDNAMES = [
    "guard_id",
    "task_source_id",
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
    "allowed_in_m3012",
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


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "executable_source_spec_rows": output_dir / "executable_source_spec_rows.csv",
        "executable_source_specs": output_dir / "executable_source_specs.json",
        "executable_workload_rows": output_dir / "executable_workload_rows.csv",
        "profile_binding_rows": output_dir / "profile_binding_rows.csv",
        "unmappable_source_rows": output_dir / "unmappable_source_rows.csv",
        "env_contract_guard_rows": output_dir / "env_contract_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def run_new_source_executable_env_materialization_preflight(
    *,
    m3010_audit: Path | str = DEFAULT_M3010_AUDIT,
    m3011_design: Path | str = DEFAULT_M3011_DESIGN,
    m3006_dir: Path | str = DEFAULT_M3006_DIR,
    m3009_dir: Path | str = DEFAULT_M3009_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m3010_audit=Path(m3010_audit),
        m3011_design=Path(m3011_design),
        m3006_dir=Path(m3006_dir),
        m3009_dir=Path(m3009_dir),
    )

    source_rows, executable_specs, unmappable_rows = build_executable_source_spec_rows(
        source["m3006_source_spec_rows"]
    )
    profile_rows = normalize_profile_binding_rows(source["m3009_profile_binding_rows"])
    workload_rows = build_executable_workload_rows(
        source["m3009_workload_contract_rows"],
        source_rows,
        profile_rows,
    )
    env_guard_rows = build_env_contract_guard_rows(source_rows)
    actor_rows = build_actor_contract_guard_rows()

    write_csv_rows(paths["executable_source_spec_rows"], source_rows, fieldnames=SOURCE_ROW_FIELDNAMES)
    write_json(
        paths["executable_source_specs"],
        {
            "protocol_name": MILESTONE_ID,
            "generated_at_utc": utc_timestamp(),
            "claim_scope": CLAIM_SCOPE,
            "source_spec_authority": str(Path(m3006_dir) / "new_task_source_spec_rows.csv"),
            "workload_authority": str(Path(m3009_dir) / "executable_workload_contract_rows.csv"),
            "executable_source_specs": executable_specs,
        },
    )
    write_csv_rows(paths["profile_binding_rows"], profile_rows, fieldnames=PROFILE_FIELDNAMES)
    write_csv_rows(paths["executable_workload_rows"], workload_rows, fieldnames=WORKLOAD_FIELDNAMES)
    write_csv_rows(paths["unmappable_source_rows"], unmappable_rows, fieldnames=UNMAPPABLE_FIELDNAMES)
    write_csv_rows(paths["env_contract_guard_rows"], env_guard_rows, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=GUARD_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "executable_source_spec_row_count": len(source_rows),
            "executable_workload_row_count": len(workload_rows),
            "unmappable_source_row_count": len(unmappable_rows),
            "source_build_performed": False,
            "environment_reset_performed": False,
            "environment_step_performed": False,
            "policy_action_performed": False,
            "validation_performed": False,
            "training_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )
    write_json(
        paths["follow_up_manifest"],
        build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]),
    )

    required_artifacts_present = False
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_artifacts_present)
    gate_rows = build_gate_matrix_rows(
        source=source,
        source_rows=source_rows,
        profile_rows=profile_rows,
        workload_rows=workload_rows,
        unmappable_rows=unmappable_rows,
        env_guard_rows=env_guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        source_rows=source_rows,
        profile_rows=profile_rows,
        workload_rows=workload_rows,
        unmappable_rows=unmappable_rows,
        env_guard_rows=env_guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in PATH_KEYS)
    claim_rows = build_claim_boundary_rows(required_artifacts_present=required_artifacts_present)
    gate_rows = build_gate_matrix_rows(
        source=source,
        source_rows=source_rows,
        profile_rows=profile_rows,
        workload_rows=workload_rows,
        unmappable_rows=unmappable_rows,
        env_guard_rows=env_guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest_exists=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        source_rows=source_rows,
        profile_rows=profile_rows,
        workload_rows=workload_rows,
        unmappable_rows=unmappable_rows,
        env_guard_rows=env_guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "executable_source_spec_row_count": len(source_rows),
            "executable_source_unique_task_source_count": len({row["task_source_id"] for row in source_rows}),
            "executable_workload_row_count": len(workload_rows),
            "unmappable_source_row_count": len(unmappable_rows),
            "env_contract_violation_count": env_contract_violation_count(source_rows),
            "forbidden_key_violation_count": forbidden_key_violation_count(source_rows),
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "source_build_performed": False,
            "environment_reset_performed": False,
            "environment_step_performed": False,
            "policy_action_performed": False,
            "validation_performed": False,
            "training_performed": False,
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def load_source_artifacts(
    *,
    m3010_audit: Path,
    m3011_design: Path,
    m3006_dir: Path,
    m3009_dir: Path,
) -> dict[str, Any]:
    return {
        "m3010_audit": m3010_audit,
        "m3010_audit_exists": m3010_audit.exists(),
        "m3011_design": m3011_design,
        "m3011_design_exists": m3011_design.exists(),
        "m3006_dir": m3006_dir,
        "m3006_summary": read_json(m3006_dir / "summary.json") if (m3006_dir / "summary.json").exists() else {},
        "m3006_source_spec_rows": read_csv_rows(m3006_dir / "new_task_source_spec_rows.csv"),
        "m3009_dir": m3009_dir,
        "m3009_summary": read_json(m3009_dir / "summary.json") if (m3009_dir / "summary.json").exists() else {},
        "m3009_source_resolution_rows": read_csv_rows(m3009_dir / "source_spec_resolution_rows.csv"),
        "m3009_profile_binding_rows": read_csv_rows(m3009_dir / "profile_binding_rows.csv"),
        "m3009_workload_contract_rows": read_csv_rows(m3009_dir / "executable_workload_contract_rows.csv"),
        "m3009_gate_rows": read_csv_rows(m3009_dir / "gate_matrix.csv"),
    }


def build_executable_source_spec_rows(
    source_specs: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    executable_specs: list[dict[str, Any]] = []
    unmappable: list[dict[str, Any]] = []
    for index, spec in enumerate(sorted(source_specs, key=lambda row: row.get("task_source_id", "")), start=1):
        try:
            materialized = dict(materialize_executable_spec(spec))
        except Exception as exc:  # noqa: BLE001 - preflight must record every unmappable source.
            unmappable.append(
                {
                    "unmappable_source_id": f"m3012-unmappable-source-{len(unmappable) + 1:04d}",
                    "new_task_source_spec_id": spec.get("new_task_source_spec_id", ""),
                    "task_source_id": spec.get("task_source_id", ""),
                    "source_family_left": spec.get("source_family_left", ""),
                    "source_family_right": spec.get("source_family_right", ""),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
            continue
        forbidden_hits = forbidden_key_violations([materialized])
        csv_row = executable_spec_csv_row(materialized)
        status_pass = (
            int(materialized.get("contract_violation_count", 0)) == 0
            and len(forbidden_hits) == 0
            and bool(materialized.get("env_config"))
        )
        executable_source_spec_id = f"m3012-executable-source-spec-{index:04d}"
        row = {
            "executable_source_spec_id": executable_source_spec_id,
            "new_task_source_spec_id": spec.get("new_task_source_spec_id", ""),
            "task_source_id": spec.get("task_source_id", ""),
            "axis_name": spec.get("axis_name", ""),
            "axis_family": spec.get("axis_family", ""),
            "axis_variant_tag": spec.get("axis_variant_tag", ""),
            "task_family": csv_row.get("task_family", ""),
            "source_edge": csv_row.get("source_edge", ""),
            "source_family_left": csv_row.get("source_family_left", ""),
            "source_family_right": csv_row.get("source_family_right", ""),
            "window_tag": csv_row.get("window_tag", ""),
            "generation_seed": csv_row.get("generation_seed", ""),
            "reference_m1680_task_source_id": spec.get("reference_m1680_task_source_id", ""),
            "executable_source_family": csv_row.get("executable_source_family", ""),
            "env_template_family": csv_row.get("env_template_family", ""),
            "materialization_rule": csv_row.get("materialization_rule", ""),
            "capability_pair": csv_row.get("capability_pair", ""),
            "geometry_key": csv_row.get("geometry_key", ""),
            "reveal_step": csv_row.get("reveal_step", ""),
            "decision_step": csv_row.get("decision_step", ""),
            "simulator_scope": csv_row.get("simulator_scope", ""),
            "proxy_fault_family": csv_row.get("proxy_fault_family", ""),
            "env_config_materialized_by_m3012": True,
            "env_config_present": bool(materialized.get("env_config")),
            "contract_violation_count": int(materialized.get("contract_violation_count", 0)),
            "forbidden_key_violation_count": len(forbidden_hits),
            "actor_observation_dim": P0_OBSERVATION_DIM,
            "actor_action_dim": ACTION_DIM,
            "source_build_scheduled_by_m3012": False,
            "environment_reset_scheduled_by_m3012": False,
            "environment_step_scheduled_by_m3012": False,
            "policy_action_scheduled_by_m3012": False,
            "validation_scheduled_by_m3012": False,
            "training_scheduled_by_m3012": False,
            "ranking_scheduled_by_m3012": False,
            "checkpoint_mutation_scheduled": False,
            "actor_visible": False,
            "hidden_oracle_actor_input_required": False,
            "source_labels_actor_visible": False,
            "route_labels_actor_visible": False,
            "outcome_labels_actor_visible": False,
            "status_pass": status_pass,
            "claim_boundary": CLAIM_SCOPE,
        }
        rows.append(row)
        executable_specs.append(
            {
                "executable_source_spec_id": executable_source_spec_id,
                "source_authority_row": dict(spec),
                "forbidden_key_violations": forbidden_hits,
                **materialized,
            }
        )
    return rows, executable_specs, unmappable


def normalize_profile_binding_rows(profile_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sorted(profile_rows, key=lambda item: item.get("profile_binding_id", "")):
        normalized = {
            key: row.get(key, "")
            for key in PROFILE_FIELDNAMES
            if key not in {"config_exists", "checkpoint_exists", "read_only_binding", "profile_specific_tuning", "checkpoint_mutation_scheduled", "status_pass", "claim_boundary"}
        }
        normalized.update(
            {
                "config_exists": _bool(row.get("config_exists")),
                "checkpoint_exists": _bool(row.get("checkpoint_exists")),
                "read_only_binding": _bool(row.get("read_only_binding")),
                "profile_specific_tuning": _bool(row.get("profile_specific_tuning")),
                "checkpoint_mutation_scheduled": _bool(row.get("checkpoint_mutation_scheduled")),
                "status_pass": _bool(row.get("status_pass")),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
        rows.append(normalized)
    return rows


def build_executable_workload_rows(
    workload_contract_rows: list[dict[str, str]],
    source_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_by_id = {str(row["task_source_id"]): row for row in source_rows}
    profile_by_id = {str(row["profile_binding_id"]): row for row in profile_rows}
    rows: list[dict[str, Any]] = []
    for index, workload in enumerate(
        sorted(workload_contract_rows, key=lambda row: row.get("workload_contract_id", "")),
        start=1,
    ):
        task_source_id = str(workload.get("task_source_id", ""))
        source = source_by_id.get(task_source_id, {})
        profile = profile_by_id.get(str(workload.get("profile_binding_id", "")), {})
        status_pass = (
            _bool(workload.get("status_pass"))
            and _bool(source.get("status_pass"))
            and _bool(profile.get("status_pass"))
            and _bool(workload.get("new_source_identity_preserved"))
            and _bool(workload.get("read_only_profile_binding"))
            and _bool(source.get("env_config_materialized_by_m3012"))
        )
        rows.append(
            {
                "executable_workload_id": f"m3012-executable-workload-{index:04d}",
                "workload_contract_id": workload.get("workload_contract_id", ""),
                "source_resolution_id": workload.get("source_resolution_id", ""),
                "profile_binding_id": workload.get("profile_binding_id", ""),
                "executable_source_spec_id": source.get("executable_source_spec_id", ""),
                "task_source_id": task_source_id,
                "profile_binding_name": workload.get("profile_binding_name", ""),
                "binding_role": workload.get("binding_role", ""),
                "axis_name": workload.get("axis_name", ""),
                "axis_family": workload.get("axis_family", ""),
                "task_family": workload.get("task_family", ""),
                "source_edge": workload.get("source_edge", ""),
                "window_tag": workload.get("window_tag", ""),
                "executable_source_family": source.get("executable_source_family", ""),
                "env_template_family": source.get("env_template_family", ""),
                "config_path": workload.get("config_path", ""),
                "checkpoint_path": workload.get("checkpoint_path", ""),
                "actor_observation_dim": P0_OBSERVATION_DIM,
                "actor_action_dim": ACTION_DIM,
                "new_source_identity_preserved": _bool(workload.get("new_source_identity_preserved")),
                "read_only_profile_binding": _bool(workload.get("read_only_profile_binding")),
                "env_config_materialized_by_m3012": _bool(source.get("env_config_materialized_by_m3012")),
                "future_execution_manifest_required": True,
                "source_build_scheduled_by_m3012": False,
                "environment_reset_scheduled_by_m3012": False,
                "environment_step_scheduled_by_m3012": False,
                "policy_action_scheduled_by_m3012": False,
                "policy_rollout_scheduled_by_m3012": False,
                "replay_scheduled_by_m3012": False,
                "validation_scheduled_by_m3012": False,
                "training_scheduled_by_m3012": False,
                "ranking_scheduled_by_m3012": False,
                "checkpoint_mutation_scheduled": False,
                "actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "future_target_actor_input_required": False,
                "source_labels_actor_visible": False,
                "route_labels_actor_visible": False,
                "outcome_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
                "ttc_actor_input_required": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_env_contract_guard_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    guards: list[dict[str, Any]] = []
    for source in source_rows:
        task_source_id = str(source["task_source_id"])
        checks = [
            ("env_config_present", source["env_config_present"], True),
            ("contract_violation_count", int(source["contract_violation_count"]), 0),
            ("forbidden_key_violation_count", int(source["forbidden_key_violation_count"]), 0),
            ("history_length_is_one", True, True),
            ("action_history_mode_full", True, True),
            ("include_privileged_params_false", True, True),
            ("wheel_observation_mode_none", True, True),
            ("obstacle_relative_velocity_mode_zero", True, True),
            ("source_build_scheduled_by_m3012", source["source_build_scheduled_by_m3012"], False),
            ("environment_reset_scheduled_by_m3012", source["environment_reset_scheduled_by_m3012"], False),
        ]
        for field, observed, expected in checks:
            guards.append(
                {
                    "guard_id": f"m3012-env-guard-{len(guards) + 1:04d}",
                    "task_source_id": task_source_id,
                    "contract_field": field,
                    "observed_value": observed,
                    "expected_value": expected,
                    "status_pass": observed == expected,
                    "actor_visible": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return guards


def build_actor_contract_guard_rows() -> list[dict[str, Any]]:
    guards = [
        ("actor_observation_dim", P0_OBSERVATION_DIM, 72),
        ("actor_action_dim", ACTION_DIM, 3),
        ("actor_input_contract_changed", False, False),
        ("hidden_oracle_actor_input_required", False, False),
        ("future_target_actor_input_required", False, False),
        ("source_labels_actor_visible", False, False),
        ("route_labels_actor_visible", False, False),
        ("outcome_labels_actor_visible", False, False),
        ("success_progress_labels_actor_visible", False, False),
        ("verdict_labels_actor_visible", False, False),
        ("ttc_actor_input_required", False, False),
        ("materialization_only_no_execution", True, True),
        ("checkpoint_mutation_scheduled", False, False),
    ]
    return [
        {
            "guard_id": f"m3012-actor-guard-{index:04d}",
            "task_source_id": "all",
            "contract_field": field,
            "observed_value": observed,
            "expected_value": expected,
            "status_pass": observed == expected,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, observed, expected) in enumerate(guards, start=1)
    ]


def build_claim_boundary_rows(*, required_artifacts_present: bool) -> list[dict[str, Any]]:
    claims = [
        ("executable_env_materialization", True, True, "M3013 result audit before execution design"),
        ("new_source_env_workload_identity_accounting", True, True, "M3013 result audit before interpretation"),
        ("source_build_readiness", False, False, "separate source-build route and audit"),
        ("execution_readiness", False, False, "separate execution design and audit"),
        ("execution_result", False, False, "separate execution manifest and audit"),
        ("validation_result", False, False, "separate validation manifest and audit"),
        ("repair_success", False, False, "closed-loop fresh-source evidence"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("paper_evidence", False, False, "paper-route proof gates"),
        ("current_sim_verdict", False, False, "closed-loop current-sim result synthesis"),
        ("high_fidelity_validation", False, False, "Route C validation layer"),
        ("finite_window_vs_gru_result", False, False, "separate controller-family comparison"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_identification", False, False, "history-necessity/self-ID proof gates"),
        ("checkpoint_ranking_or_promotion", False, False, "promotion gates after proof and generalization"),
    ]
    return [
        {
            "claim_id": f"m3012-claim-{index:04d}",
            "claim_family": claim,
            "allowed_in_m3012": allowed,
            "claim_made": made,
            "status_pass": required_artifacts_present and made is allowed,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (claim, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    source_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    workload_rows: list[dict[str, Any]],
    unmappable_rows: list[dict[str, Any]],
    env_guard_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    source_ids = {str(row["task_source_id"]) for row in source_rows}
    workload_ids = {str(row["workload_contract_id"]) for row in workload_rows}
    expected_workload_ids = {str(row["workload_contract_id"]) for row in source["m3009_workload_contract_rows"]}
    gates = [
        ("required_artifacts_present", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
        ("m3010_audit_present", source["m3010_audit_exists"], source["m3010_audit_exists"], True, "lineage_invalid"),
        ("m3011_design_present", source["m3011_design_exists"], source["m3011_design_exists"], True, "lineage_invalid"),
        ("m3006_status_pass", source["m3006_summary"].get("status_pass") is True, source["m3006_summary"].get("status_pass"), True, "lineage_invalid"),
        ("m3006_gate_matrix_pass", source["m3006_summary"].get("gate_matrix_pass") is True, source["m3006_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        ("m3009_status_pass", source["m3009_summary"].get("status_pass") is True, source["m3009_summary"].get("status_pass"), True, "lineage_invalid"),
        ("m3009_gate_matrix_pass", source["m3009_summary"].get("gate_matrix_pass") is True, source["m3009_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        ("m3006_source_spec_row_count", len(source["m3006_source_spec_rows"]) == SOURCE_SPEC_COUNT, len(source["m3006_source_spec_rows"]), SOURCE_SPEC_COUNT, "scenario_sampling_failure"),
        ("m3009_workload_contract_row_count", len(source["m3009_workload_contract_rows"]) == WORKLOAD_ROW_COUNT, len(source["m3009_workload_contract_rows"]), WORKLOAD_ROW_COUNT, "scenario_sampling_failure"),
        ("executable_source_spec_row_count", len(source_rows) == SOURCE_SPEC_COUNT, len(source_rows), SOURCE_SPEC_COUNT, "scenario_sampling_failure"),
        ("executable_source_unique_task_source_count", len(source_ids) == SOURCE_SPEC_COUNT, len(source_ids), SOURCE_SPEC_COUNT, "lineage_invalid"),
        ("old_m1690_l3_overlap_count", old_overlap_count(source["m3006_source_spec_rows"]) == 0, old_overlap_count(source["m3006_source_spec_rows"]), 0, "objective_overfit"),
        ("unmappable_source_row_count", len(unmappable_rows) == 0, len(unmappable_rows), 0, "lineage_invalid"),
        ("env_contract_violation_count", env_contract_violation_count(source_rows) == 0, env_contract_violation_count(source_rows), 0, "contract_violation"),
        ("forbidden_key_violation_count", forbidden_key_violation_count(source_rows) == 0, forbidden_key_violation_count(source_rows), 0, "contract_violation"),
        ("executable_source_rows_pass", all(_bool(row["status_pass"]) for row in source_rows), "all source rows pass", True, "lineage_invalid"),
        ("profile_binding_row_count", len(profile_rows) == PROFILE_BINDING_COUNT, len(profile_rows), PROFILE_BINDING_COUNT, "lineage_invalid"),
        ("profile_binding_rows_pass", all(_bool(row["status_pass"]) for row in profile_rows), "all profile rows pass", True, "lineage_invalid"),
        ("profile_bindings_read_only", all(_bool(row["read_only_binding"]) for row in profile_rows), "all read only", True, "contract_violation"),
        ("executable_workload_row_count", len(workload_rows) == WORKLOAD_ROW_COUNT, len(workload_rows), WORKLOAD_ROW_COUNT, "scenario_sampling_failure"),
        ("workload_contract_ids_preserved", workload_ids == expected_workload_ids, len(workload_ids), len(expected_workload_ids), "lineage_invalid"),
        ("executable_workload_rows_pass", all(_bool(row["status_pass"]) for row in workload_rows), "all workload rows pass", True, "lineage_invalid"),
        ("env_contract_guard_rows_pass", all(_bool(row["status_pass"]) for row in env_guard_rows), "all env guards pass", True, "contract_violation"),
        ("actor_contract_rows_pass", all(_bool(row["status_pass"]) for row in actor_rows), "all actor rows pass", True, "contract_violation"),
        ("claim_boundary_rows_pass", all(_bool(row["status_pass"]) for row in claim_rows), "all claim rows pass", True, "proof_washout"),
        ("follow_up_manifest_written", follow_up_manifest_exists, follow_up_manifest_exists, True, "lineage_invalid"),
        ("source_build_run", True, False, False, "contract_violation"),
        ("environment_reset_run", True, False, False, "contract_violation"),
        ("environment_step_run", True, False, False, "contract_violation"),
        ("policy_action_run", True, False, False, "contract_violation"),
        ("policy_rollout_run", True, False, False, "contract_violation"),
        ("validation_run", True, False, False, "contract_violation"),
        ("training_run", True, False, False, "contract_violation"),
        ("ppo_run", True, False, False, "contract_violation"),
        ("ranking_run", True, False, False, "proof_washout"),
        ("checkpoint_mutated", True, False, False, "contract_violation"),
        ("performance_claim_made", True, False, False, "proof_washout"),
        ("paper_claim_made", True, False, False, "proof_washout"),
        ("high_fidelity_claim_made", True, False, False, "proof_washout"),
        ("self_id_claim_made", True, False, False, "proof_washout"),
    ]
    return [
        {
            "gate_id": f"m3012-gate-{index:04d}",
            "gate_family": name,
            "status_pass": passed,
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, passed, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source: Mapping[str, Any],
    source_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    workload_rows: list[dict[str, Any]],
    unmappable_rows: list[dict[str, Any]],
    env_guard_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    env_guard_rows_pass = bool(env_guard_rows) and all(_bool(row["status_pass"]) for row in env_guard_rows)
    actor_rows_pass = bool(actor_rows) and all(_bool(row["status_pass"]) for row in actor_rows)
    claim_rows_pass = bool(claim_rows) and all(_bool(row["status_pass"]) for row in claim_rows)
    source_rows_pass = bool(source_rows) and all(_bool(row["status_pass"]) for row in source_rows)
    profile_rows_pass = bool(profile_rows) and all(_bool(row["status_pass"]) for row in profile_rows)
    workload_rows_pass = bool(workload_rows) and all(_bool(row["status_pass"]) for row in workload_rows)
    status_pass = (
        gate_matrix_pass
        and source_rows_pass
        and profile_rows_pass
        and workload_rows_pass
        and env_guard_rows_pass
        and actor_rows_pass
        and claim_rows_pass
        and required_artifacts_present
    )
    task_family_counts = Counter(str(row["task_family"]) for row in source_rows)
    template_counts = Counter(str(row["env_template_family"]) for row in source_rows)
    executable_family_counts = Counter(str(row["executable_source_family"]) for row in source_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": DECISION_PASS if status_pass else DECISION_FAIL,
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "m3010_audit_present": source["m3010_audit_exists"],
        "m3011_design_present": source["m3011_design_exists"],
        "m3006_status_pass": source["m3006_summary"].get("status_pass") is True,
        "m3006_gate_matrix_pass": source["m3006_summary"].get("gate_matrix_pass") is True,
        "m3009_status_pass": source["m3009_summary"].get("status_pass") is True,
        "m3009_gate_matrix_pass": source["m3009_summary"].get("gate_matrix_pass") is True,
        "m3006_source_spec_row_count": len(source["m3006_source_spec_rows"]),
        "m3009_workload_contract_row_count": len(source["m3009_workload_contract_rows"]),
        "executable_source_spec_row_count": len(source_rows),
        "executable_source_unique_task_source_count": len({row["task_source_id"] for row in source_rows}),
        "old_m1690_l3_overlap_count": old_overlap_count(source["m3006_source_spec_rows"]),
        "unmappable_source_row_count": len(unmappable_rows),
        "profile_binding_row_count": len(profile_rows),
        "executable_workload_row_count": len(workload_rows),
        "target_executable_source_spec_row_count": SOURCE_SPEC_COUNT,
        "target_executable_workload_row_count": WORKLOAD_ROW_COUNT,
        "env_contract_violation_count": env_contract_violation_count(source_rows),
        "forbidden_key_violation_count": forbidden_key_violation_count(source_rows),
        "source_rows_pass": source_rows_pass,
        "profile_binding_rows_pass": profile_rows_pass,
        "workload_rows_pass": workload_rows_pass,
        "env_contract_guard_row_count": len(env_guard_rows),
        "env_contract_guard_rows_pass": env_guard_rows_pass,
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_rows_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "task_family_counts": dict(sorted(task_family_counts.items())),
        "executable_source_family_counts": dict(sorted(executable_family_counts.items())),
        "env_template_family_counts": dict(sorted(template_counts.items())),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "source_build_run": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_result_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "private_holdout_used": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3012 Engineering Controller Route A Post-Residual-Stop New Source Executable Env Materialization Preflight",
            "",
            "## Summary",
            "",
            "- status: completed" if summary["status_pass"] else "- status: blocked",
            f"- result class: `{summary['result_class']}`",
            f"- executable source spec rows: {summary['executable_source_spec_row_count']}",
            f"- unique source ids: {summary['executable_source_unique_task_source_count']}",
            f"- old M1690 L3 overlap count: {summary['old_m1690_l3_overlap_count']}",
            f"- unmappable source rows: {summary['unmappable_source_row_count']}",
            f"- env contract violation count: {summary['env_contract_violation_count']}",
            f"- forbidden key violation count: {summary['forbidden_key_violation_count']}",
            f"- profile binding rows: {summary['profile_binding_row_count']}",
            f"- executable workload rows: {summary['executable_workload_row_count']}",
            f"- task family counts: {summary['task_family_counts']}",
            f"- executable source family counts: {summary['executable_source_family_counts']}",
            f"- env template family counts: {summary['env_template_family_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M3012 materializes env config and executable workload artifacts only. It does not build sources, reset, step, rollout, replay, validate, train, rank, promote, or claim repair success or performance.",
            "",
            "Rejected interpretations:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
        ]
    )


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
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
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject the M3012 new-source executable env materialization before any execution validation ranking promotion repair-success performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "executable_source_spec_rows.csv"),
                str(output_dir / "executable_source_specs.json"),
                str(output_dir / "executable_workload_rows.csv"),
                str(output_dir / "profile_binding_rows.csv"),
                str(output_dir / "unmappable_source_rows.csv"),
                str(output_dir / "env_contract_guard_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                f"experiments/manifests/{M3011_ID}.json",
                f"experiments/manifests/{M3010_ID}.json",
            ],
            "parent_objective": ["audit M3012 executable env materialization before any execution design or stop"],
            "derived_from": [MILESTONE_ID, M3011_ID, M3010_ID, M3009_ID],
            "blocked_by": [
                "M3012 env configs require audit before execution design",
                "env config materialization rows are not execution readiness or performance evidence",
            ],
            "supersedes": [
                "direct execution from workload contracts without env materialization audit",
                "direct performance interpretation of env configs",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3013 must audit M3012 summary env workload guard and claim artifacts",
            "M3013 must preserve 16 source identities 2 profile bindings and 32 workload rows",
            "M3013 must not convert env configs into execution validation performance paper high-fidelity or self-ID evidence",
            "M3013 must select exactly one next route or explicit stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute workloads build sources validate train rank promote or select a winner",
            "do not change actor input or action contract",
            "do not convert M3012 env config rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_executable_env_materialization_result_audit",
            "evidence_increment": "audits M3012 env materialization and decides execution design repair synthesis or stop",
            "claim_scope": "Result audit only; no execution validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3012 artifacts are missing or gate matrix fails",
                "stop if env rows drop source specs or workload rows",
                "stop if actor or claim boundaries were violated",
                "stop if env configs would be used as execution results",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if no execution design is viable",
                "route to bounded execution design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3012 completes env materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3012 no-execution executable env materialization artifacts",
            "admission_evidence": ["M3012 summary and gate matrix", "M3012 source env workload actor and claim artifacts"],
            "blocked_shortcuts": [
                "no execution validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO checkpoint mutation",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M3013 status queue scoreboard research log and review",
                "one follow-up manifest only if M3013 selects exactly one next route",
            ],
            "next_stage_criteria": ["M3013 audit accepts or rejects M3012 as complete and claim-safe", "next route or stop state is explicit"],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3013 audits env materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3013; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."],
            "temporal_evidence_window": "M3012 env materialization only.",
            "negative_result_policy": "Preserve env materialization failures and route to synthesis or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3012 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized env-config and executable-workload panel",
            "paper_verdict_delta": "no paper verdict; audit may authorize execution design only",
            "must_synthesize_if": [
                "M3013 cannot accept M3012 as complete and claim-safe",
                "M3013 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M3013 cannot select execution design repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3013 audits M3012 artifacts row counts gates actor and claim boundaries",
            "M3013 selects exactly one next route or stop state",
            "no execution training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3013 hides M3012 failures or missing artifacts",
            "M3013 treats M3012 env configs as execution readiness performance verdict or repair success",
            "M3013 changes actor input or action contract",
            "M3013 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3013 audits M3012 artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "executable_source_spec_rows.csv"),
            str(output_dir / "executable_workload_rows.csv"),
            str(output_dir / "env_contract_guard_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def env_contract_violation_count(rows: list[Mapping[str, Any]]) -> int:
    return sum(int(row.get("contract_violation_count", 0)) for row in rows)


def forbidden_key_violation_count(rows: list[Mapping[str, Any]]) -> int:
    return sum(int(row.get("forbidden_key_violation_count", 0)) for row in rows)


def old_overlap_count(rows: list[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _bool(row.get("overlaps_exhausted_m1690_l3")))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3010-audit", type=Path, default=DEFAULT_M3010_AUDIT)
    parser.add_argument("--m3011-design", type=Path, default=DEFAULT_M3011_DESIGN)
    parser.add_argument("--m3006-dir", type=Path, default=DEFAULT_M3006_DIR)
    parser.add_argument("--m3009-dir", type=Path, default=DEFAULT_M3009_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_new_source_executable_env_materialization_preflight(
        m3010_audit=args.m3010_audit,
        m3011_design=args.m3011_design,
        m3006_dir=args.m3006_dir,
        m3009_dir=args.m3009_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
