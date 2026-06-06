"""Materialize M2925 offtrack-dominant failure-slice rows.

M2925 consumes accepted M2922/M2923/M2924 Route A artifacts and the already
recorded M2919 bounded diagnostic rows. It performs no environment, policy,
training, dependency, ranking, validation, or promotion work. Its only job is
to turn the 38 off_track rows and 18 non-offtrack context rows into
machine-checkable slice artifacts for a later result audit.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, selected_metrics_are_finite, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = "m2925-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-preflight"
NEXT_ID = "m2926-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-result-audit"
DEFAULT_M2922_DIR = Path(
    "runs/m2922_engineering_controller_route_a_dependency_facing_failure_localization_materialization_preflight"
)
DEFAULT_M2919_DIR = Path(
    "runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight"
)
DEFAULT_M2923_AUDIT = Path(
    "docs/m2923-engineering-controller-route-a-dependency-facing-failure-localization-materialization-result-audit.md"
)
DEFAULT_M2924_DESIGN = Path(
    "docs/m2924-engineering-controller-route-a-offtrack-dominant-failure-slice-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2925-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2926-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-result-audit.json"
)

EXPECTED_TOTAL_ROW_COUNT = 56
EXPECTED_OFFTRACK_COUNT = 38
EXPECTED_NON_OFFTRACK_CONTEXT_COUNT = 18
EXPECTED_OFFTRACK_SOURCE_COUNTS = {"m2737": 12, "m2746": 10, "m2807": 8, "m2816": 8}
EXPECTED_OFFTRACK_TASK_COUNTS = {"T4": 21, "T5": 17}
EXPECTED_CHECKPOINT_CONTEXT_COUNTS = {
    "public_pilot_l3_checkpoint": 28,
    "m2655_mitigation_preserving_checkpoint": 10,
}
EXPECTED_ENVIRONMENT_COUNTS = {
    "t5_near_boundary_warmup": 12,
    "t4_capability_step_temporal": 9,
    "t4_actuator_delay_response": 8,
    "t5_boundary_axis_retarget": 5,
    "t4_staged_warmup_capability": 4,
}
EXPECTED_WINDOW_COUNTS = {
    "mapping_window_unspecified": 20,
    "reveal_plus_4": 9,
    "decision_minus_32": 5,
    "decision_minus_24": 4,
}
EXPECTED_OVERSHOOT_BAND_COUNTS = {
    "low_overshoot_le_0p02": 5,
    "medium_overshoot_le_0p08": 20,
    "high_overshoot_gt_0p08": 13,
}
EXPECTED_TIME_BAND_COUNTS = {
    "early_le_1p75s": 9,
    "mid_le_2p5s": 20,
    "late_gt_2p5s": 9,
}

CLAIM_SCOPE = (
    "M2925 Route A offtrack-dominant failure-slice materialization only; "
    "already-recorded M2919 diagnostic rows may be grouped into offtrack, "
    "source, task, checkpoint, environment, window, severity, time, and "
    "non-offtrack context rows. M2877 fixed weak diagnostic rows, Route B "
    "source-family insufficiency, and Route C source_unavailable remain "
    "guardrails or context only. No reset, step, rollout, replay, validation, "
    "training, PPO, dependency work, ranking, winner selection, promotion, "
    "success-rate verdict, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "source/task/checkpoint/environment/window/severity/time-band ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

OFFTRACK_SLICE_FIELDNAMES = [
    "offtrack_slice_id",
    "source_milestone",
    "source_family",
    "source_edge",
    "source_row_id",
    "task_family",
    "task_source_id",
    "workload_id",
    "profile_name",
    "checkpoint_context",
    "checkpoint_path",
    "env_template_family",
    "window_tag",
    "profile_env_history_length",
    "offtrack_overshoot",
    "offtrack_severity_band",
    "time_to_first_off_track_s",
    "time_to_offtrack_band",
    "min_clearance_margin",
    "return",
    "lateral_rmse",
    "speed_mean",
    "high_sideslip_fraction",
    "execution_candidate_id",
    "resolution_id",
    "m2925_execution_performed",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SLICE_AGGREGATE_FIELDNAMES = [
    "slice_id",
    "slice_family",
    "slice_value",
    "row_count",
    "source_milestone_count",
    "task_family_count",
    "checkpoint_context_count",
    "offtrack_overshoot_mean",
    "time_to_first_off_track_mean",
    "min_clearance_margin_mean",
    "return_mean",
    "all_selected_metrics_finite",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
NON_OFFTRACK_CONTEXT_FIELDNAMES = [
    "context_row_id",
    "outcome_family",
    "termination_reason",
    "success",
    "collision",
    "source_milestone",
    "task_family",
    "checkpoint_context",
    "checkpoint_path",
    "env_template_family",
    "window_tag",
    "source_row_id",
    "execution_candidate_id",
    "resolution_id",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "m2925_execution_performed",
    "ranking_claim_made",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "guardrail_context_id",
    "guardrail_source",
    "guardrail_family",
    "source_milestone",
    "source_row_id",
    "guardrail_reason",
    "row_count",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "ordinary_engineering_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_visible",
    "diagnostic_only_no_verdict",
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
    "allowed_in_m2925",
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
    "offtrack_slice_rows",
    "offtrack_source_slice_rows",
    "offtrack_task_slice_rows",
    "offtrack_checkpoint_slice_rows",
    "offtrack_environment_slice_rows",
    "offtrack_window_slice_rows",
    "offtrack_severity_slice_rows",
    "non_offtrack_context_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_offtrack_dominant_failure_slice_materialization_preflight(
    *,
    m2922_dir: Path | str = DEFAULT_M2922_DIR,
    m2919_dir: Path | str = DEFAULT_M2919_DIR,
    m2923_audit: Path | str = DEFAULT_M2923_AUDIT,
    m2924_design: Path | str = DEFAULT_M2924_DESIGN,
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
        m2922_dir=Path(m2922_dir),
        m2919_dir=Path(m2919_dir),
        m2923_audit=Path(m2923_audit),
        m2924_design=Path(m2924_design),
        follow_up_manifest=Path(follow_up_manifest),
    )

    execution_rows = source["bounded_execution_rows"]
    offtrack_execution_rows = [row for row in execution_rows if outcome_family(row) == "off_track"]
    non_offtrack_execution_rows = [row for row in execution_rows if outcome_family(row) != "off_track"]

    offtrack_rows = build_offtrack_slice_rows(offtrack_execution_rows)
    source_rows = build_slice_aggregate_rows(offtrack_execution_rows, slice_family="source_milestone", key="source_milestone")
    task_rows = build_slice_aggregate_rows(offtrack_execution_rows, slice_family="task_family", key="task_family")
    checkpoint_rows = build_slice_aggregate_rows(
        offtrack_execution_rows,
        slice_family="checkpoint_context",
        value_fn=checkpoint_context,
    )
    environment_rows = build_slice_aggregate_rows(
        offtrack_execution_rows,
        slice_family="env_template_family",
        key="env_template_family",
    )
    window_rows = build_slice_aggregate_rows(offtrack_execution_rows, slice_family="window_tag", key="window_tag")
    severity_rows = build_severity_slice_rows(offtrack_execution_rows)
    context_rows = build_non_offtrack_context_rows(non_offtrack_execution_rows)
    guardrail_rows = build_guardrail_context_rows(source["m2922_guardrail_context_rows"])

    write_csv_rows(paths["offtrack_slice_rows"], offtrack_rows, fieldnames=OFFTRACK_SLICE_FIELDNAMES)
    write_csv_rows(paths["offtrack_source_slice_rows"], source_rows, fieldnames=SLICE_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["offtrack_task_slice_rows"], task_rows, fieldnames=SLICE_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["offtrack_checkpoint_slice_rows"], checkpoint_rows, fieldnames=SLICE_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["offtrack_environment_slice_rows"], environment_rows, fieldnames=SLICE_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["offtrack_window_slice_rows"], window_rows, fieldnames=SLICE_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["offtrack_severity_slice_rows"], severity_rows, fieldnames=SLICE_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["non_offtrack_context_rows"], context_rows, fieldnames=NON_OFFTRACK_CONTEXT_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "offtrack_row_count": len(offtrack_rows),
            "non_offtrack_context_row_count": len(context_rows),
            "execution_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(
        offtrack_rows=offtrack_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        slice_rows_present=bool(offtrack_rows and source_rows and task_rows and checkpoint_rows),
        context_rows_present=bool(context_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        offtrack_rows=offtrack_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
        environment_rows=environment_rows,
        window_rows=window_rows,
        severity_rows=severity_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_derived_outputs(paths, actor_rows, claim_rows, gate_rows)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        offtrack_rows=offtrack_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
        environment_rows=environment_rows,
        window_rows=window_rows,
        severity_rows=severity_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
        actor_rows=actor_rows,
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

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        slice_rows_present=bool(offtrack_rows and source_rows and task_rows and checkpoint_rows),
        context_rows_present=bool(context_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        offtrack_rows=offtrack_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
        environment_rows=environment_rows,
        window_rows=window_rows,
        severity_rows=severity_rows,
        context_rows=context_rows,
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
        offtrack_rows=offtrack_rows,
        source_rows=source_rows,
        task_rows=task_rows,
        checkpoint_rows=checkpoint_rows,
        environment_rows=environment_rows,
        window_rows=window_rows,
        severity_rows=severity_rows,
        context_rows=context_rows,
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
    write_run_state(
        paths["run_state"],
        {
            "offtrack_row_count": len(offtrack_rows),
            "non_offtrack_context_row_count": len(context_rows),
            "source_slice_row_count": len(source_rows),
            "task_slice_row_count": len(task_rows),
            "checkpoint_slice_row_count": len(checkpoint_rows),
            "environment_slice_row_count": len(environment_rows),
            "window_slice_row_count": len(window_rows),
            "severity_slice_row_count": len(severity_rows),
            "execution_performed": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "offtrack_slice_rows": output_dir / "offtrack_slice_rows.csv",
        "offtrack_source_slice_rows": output_dir / "offtrack_source_slice_rows.csv",
        "offtrack_task_slice_rows": output_dir / "offtrack_task_slice_rows.csv",
        "offtrack_checkpoint_slice_rows": output_dir / "offtrack_checkpoint_slice_rows.csv",
        "offtrack_environment_slice_rows": output_dir / "offtrack_environment_slice_rows.csv",
        "offtrack_window_slice_rows": output_dir / "offtrack_window_slice_rows.csv",
        "offtrack_severity_slice_rows": output_dir / "offtrack_severity_slice_rows.csv",
        "non_offtrack_context_rows": output_dir / "non_offtrack_context_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2922_dir: Path,
    m2919_dir: Path,
    m2923_audit: Path,
    m2924_design: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2923_audit": m2923_audit,
        "m2924_design": m2924_design,
        "m2922_summary": m2922_dir / "summary.json",
        "m2922_guardrail_context_rows": m2922_dir / "guardrail_context_rows.csv",
        "m2922_actor_contract_guard_rows": m2922_dir / "actor_contract_guard_rows.csv",
        "m2922_claim_boundary_rows": m2922_dir / "claim_boundary_rows.csv",
        "m2922_gate_matrix": m2922_dir / "gate_matrix.csv",
        "bounded_execution_rows": m2919_dir / "bounded_execution_rows.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2923_audit_text": paths["m2923_audit"].read_text(encoding="utf-8")
        if source_exists["m2923_audit"]
        else "",
        "m2924_design_text": paths["m2924_design"].read_text(encoding="utf-8")
        if source_exists["m2924_design"]
        else "",
        "m2922_summary": read_json(paths["m2922_summary"]) if source_exists["m2922_summary"] else {},
        "m2922_guardrail_context_rows": read_csv_rows(paths["m2922_guardrail_context_rows"]),
        "m2922_actor_contract_guard_rows": read_csv_rows(paths["m2922_actor_contract_guard_rows"]),
        "m2922_claim_boundary_rows": read_csv_rows(paths["m2922_claim_boundary_rows"]),
        "m2922_gate_matrix": read_csv_rows(paths["m2922_gate_matrix"]),
        "bounded_execution_rows": read_csv_rows(paths["bounded_execution_rows"]),
    }


def outcome_family(row: Mapping[str, Any]) -> str:
    termination = str(row.get("termination_reason", "")).strip()
    if _bool(row.get("success", False)):
        return "diagnostic_success"
    if _bool(row.get("collision", False)) or termination == "obstacle_collision":
        return "collision"
    if termination == "off_track":
        return "off_track"
    if termination == "speed_too_low":
        return "speed_too_low"
    return "other_non_success"


def build_offtrack_slice_rows(offtrack_execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(offtrack_execution_rows, start=1):
        rows.append(
            {
                "offtrack_slice_id": f"m2925-offtrack-slice-{index:04d}",
                "source_milestone": row.get("source_milestone", ""),
                "source_family": row.get("source_family", ""),
                "source_edge": row.get("source_edge", ""),
                "source_row_id": row.get("source_row_id", ""),
                "task_family": row.get("task_family", ""),
                "task_source_id": row.get("task_source_id", ""),
                "workload_id": row.get("workload_id", ""),
                "profile_name": row.get("profile_name", ""),
                "checkpoint_context": checkpoint_context(row),
                "checkpoint_path": row.get("checkpoint_path", ""),
                "env_template_family": row.get("env_template_family", ""),
                "window_tag": row.get("window_tag", ""),
                "profile_env_history_length": row.get("profile_env_history_length", ""),
                "offtrack_overshoot": _float_or_blank(row.get("off_track_severity_proxy") or row.get("max_off_track_overshoot")),
                "offtrack_severity_band": offtrack_severity_band(row),
                "time_to_first_off_track_s": _float_or_blank(row.get("time_to_first_off_track_s")),
                "time_to_offtrack_band": time_to_offtrack_band(row),
                "min_clearance_margin": _float_or_blank(row.get("min_clearance_margin")),
                "return": _float_or_blank(row.get("return")),
                "lateral_rmse": _float_or_blank(row.get("lateral_rmse")),
                "speed_mean": _float_or_blank(row.get("speed_mean")),
                "high_sideslip_fraction": _float_or_blank(row.get("high_sideslip_fraction")),
                "execution_candidate_id": row.get("execution_candidate_id", ""),
                "resolution_id": row.get("resolution_id", ""),
                "m2925_execution_performed": False,
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_slice_aggregate_rows(
    offtrack_execution_rows: list[dict[str, str]],
    *,
    slice_family: str,
    key: str | None = None,
    value_fn: Any | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in offtrack_execution_rows:
        value = value_fn(row) if value_fn else str(row.get(key or "", ""))
        grouped[value].append(row)
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(sorted(value for value in grouped if value), start=1):
        group = grouped[value]
        rows.append(slice_aggregate_row(index, slice_family=slice_family, slice_value=value, group=group))
    return rows


def build_severity_slice_rows(offtrack_execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    specs = [
        ("overshoot_band", offtrack_severity_band),
        ("time_to_offtrack_band", time_to_offtrack_band),
    ]
    rows: list[dict[str, Any]] = []
    index = 1
    for family, fn in specs:
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in offtrack_execution_rows:
            grouped[fn(row)].append(row)
        for value in sorted(value for value in grouped if value):
            rows.append(slice_aggregate_row(index, slice_family=family, slice_value=value, group=grouped[value]))
            index += 1
    return rows


def slice_aggregate_row(
    index: int,
    *,
    slice_family: str,
    slice_value: str,
    group: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "slice_id": f"m2925-{slice_family}-slice-{index:04d}",
        "slice_family": slice_family,
        "slice_value": slice_value,
        "row_count": len(group),
        "source_milestone_count": len({str(row.get("source_milestone", "")) for row in group if row.get("source_milestone")}),
        "task_family_count": len({str(row.get("task_family", "")) for row in group if row.get("task_family")}),
        "checkpoint_context_count": len({checkpoint_context(row) for row in group if row.get("checkpoint_path")}),
        "offtrack_overshoot_mean": mean_float(group, "off_track_severity_proxy"),
        "time_to_first_off_track_mean": mean_float(group, "time_to_first_off_track_s"),
        "min_clearance_margin_mean": mean_float(group, "min_clearance_margin"),
        "return_mean": mean_float(group, "return"),
        "all_selected_metrics_finite": selected_metrics_are_finite(group),
        "ranking_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_non_offtrack_context_rows(non_offtrack_execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(non_offtrack_execution_rows, start=1):
        rows.append(
            {
                "context_row_id": f"m2925-non-offtrack-context-{index:04d}",
                "outcome_family": outcome_family(row),
                "termination_reason": row.get("termination_reason", ""),
                "success": _bool(row.get("success", False)),
                "collision": _bool(row.get("collision", False)),
                "source_milestone": row.get("source_milestone", ""),
                "task_family": row.get("task_family", ""),
                "checkpoint_context": checkpoint_context(row),
                "checkpoint_path": row.get("checkpoint_path", ""),
                "env_template_family": row.get("env_template_family", ""),
                "window_tag": row.get("window_tag", ""),
                "source_row_id": row.get("source_row_id", ""),
                "execution_candidate_id": row.get("execution_candidate_id", ""),
                "resolution_id": row.get("resolution_id", ""),
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "m2925_execution_performed": False,
                "ranking_claim_made": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_guardrail_context_rows(guardrail_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(guardrail_rows, start=1):
        rows.append(
            {
                "guardrail_context_id": f"m2925-guardrail-context-{index:04d}",
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_family": row.get("guardrail_family", ""),
                "source_milestone": row.get("source_milestone", ""),
                "source_row_id": row.get("source_row_id", ""),
                "guardrail_reason": row.get("guardrail_reason", ""),
                "row_count": row.get("row_count", 1),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_engineering_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def checkpoint_context(row: Mapping[str, Any]) -> str:
    path = str(row.get("checkpoint_path", ""))
    if "m2655" in path:
        return "m2655_mitigation_preserving_checkpoint"
    if "m1674" in path or "profile_runs/L3_online_gru" in path:
        return "public_pilot_l3_checkpoint"
    if not path:
        return ""
    return Path(path).name


def offtrack_severity_band(row: Mapping[str, Any]) -> str:
    value = _float_value(row.get("off_track_severity_proxy") or row.get("max_off_track_overshoot"))
    if not np.isfinite(value):
        return "unknown_overshoot"
    if value <= 0.02:
        return "low_overshoot_le_0p02"
    if value <= 0.08:
        return "medium_overshoot_le_0p08"
    return "high_overshoot_gt_0p08"


def time_to_offtrack_band(row: Mapping[str, Any]) -> str:
    value = _float_value(row.get("time_to_first_off_track_s"))
    if not np.isfinite(value):
        return "unknown_time_to_offtrack"
    if value <= 1.75:
        return "early_le_1p75s"
    if value <= 2.5:
        return "mid_le_2p5s"
    return "late_gt_2p5s"


def build_actor_contract_guard_rows(
    *,
    offtrack_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = offtrack_rows + context_rows + guardrail_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("environment_execution_performed_by_m2925", any_flag(combined, "m2925_execution_performed"), False),
        actor_guard("training_scheduled", any_flag(combined, "training_scheduled"), False),
        actor_guard("ranking_claim_made", any_flag(combined, "ranking_claim_made"), False),
        actor_guard("winner_selection_allowed", any_flag(combined, "winner_selection_allowed"), False),
        actor_guard("promotion_allowed", any_flag(combined, "promotion_allowed"), False),
        actor_guard("hidden_oracle_actor_input_required", any_flag(combined, "hidden_oracle_actor_input_required"), False),
        actor_guard("future_target_actor_input_required", any_flag(combined, "future_target_actor_input_required"), False),
        actor_guard("route_labels_actor_visible", any_flag(combined, "route_labels_actor_visible"), False),
        actor_guard("source_labels_actor_visible", any_flag(combined, "source_labels_actor_visible"), False),
        actor_guard("diagnostic_labels_actor_visible", any_flag(combined, "diagnostic_labels_actor_visible"), False),
        actor_guard("success_progress_labels_actor_visible", any_flag(combined, "success_progress_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", any_flag(combined, "verdict_labels_actor_visible"), False),
        actor_guard("guardrail_execution", any_flag(guardrail_rows, "execution_run"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2925-actor-guard-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    slice_rows_present: bool,
    context_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("offtrack_slice_materialization", "artifact", slice_rows_present, "M2925 offtrack slice rows"),
        ("source_slice_rows_materialized", "artifact", artifacts_present, "offtrack_source_slice_rows.csv"),
        ("task_slice_rows_materialized", "artifact", artifacts_present, "offtrack_task_slice_rows.csv"),
        ("checkpoint_slice_rows_materialized", "artifact", artifacts_present, "offtrack_checkpoint_slice_rows.csv"),
        ("environment_slice_rows_materialized", "artifact", artifacts_present, "offtrack_environment_slice_rows.csv"),
        ("window_slice_rows_materialized", "artifact", artifacts_present, "offtrack_window_slice_rows.csv"),
        ("severity_slice_rows_materialized", "artifact", artifacts_present, "offtrack_severity_slice_rows.csv"),
        ("non_offtrack_context_materialized", "artifact", context_rows_present, "non_offtrack_context_rows.csv"),
        ("guardrail_context_materialized", "artifact", artifacts_present, "guardrail_context_rows.csv"),
        ("actor_guard_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2926 audit manifest"),
    ]
    blocked = [
        ("reset_step_rollout_execution", "execution", "no execution in M2925"),
        ("training_or_ppo", "execution", "future manifest"),
        ("dependency_execution", "execution", "future dependency route"),
        ("slice_or_checkpoint_ranking", "ranking", "future audited comparison route"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2925_{claim_id}",
        "claim_family": family,
        "allowed_in_m2925": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    offtrack_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    environment_rows: list[dict[str, Any]],
    window_rows: list[dict[str, Any]],
    severity_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    execution_rows = source["bounded_execution_rows"]
    offtrack_source_counts = {row["slice_value"]: int(row["row_count"]) for row in source_rows}
    offtrack_task_counts = {row["slice_value"]: int(row["row_count"]) for row in task_rows}
    checkpoint_counts = {row["slice_value"]: int(row["row_count"]) for row in checkpoint_rows}
    environment_counts = {row["slice_value"]: int(row["row_count"]) for row in environment_rows}
    window_counts = {row["slice_value"]: int(row["row_count"]) for row in window_rows}
    overshoot_counts = {
        row["slice_value"]: int(row["row_count"])
        for row in severity_rows
        if row["slice_family"] == "overshoot_band"
    }
    time_counts = {
        row["slice_value"]: int(row["row_count"])
        for row in severity_rows
        if row["slice_family"] == "time_to_offtrack_band"
    }
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2925"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2925"])]
    route_b_context = any("route_b" in str(row.get("guardrail_family", "")) for row in guardrail_rows)
    route_c_context = any("route_c" in str(row.get("guardrail_family", "")) for row in guardrail_rows)
    m2877_context = any("m2877" in str(row.get("guardrail_family", "")) for row in guardrail_rows)
    materialized_rows = (
        offtrack_rows
        + source_rows
        + task_rows
        + checkpoint_rows
        + environment_rows
        + window_rows
        + severity_rows
        + context_rows
        + guardrail_rows
    )
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "M2919/M2922/M2923/M2924/follow-up artifacts present", "lineage_invalid"),
        ("m2922_status_pass", "lineage", _bool(source["m2922_summary"].get("status_pass", False)) and _bool(source["m2922_summary"].get("gate_matrix_pass", False)), {"status_pass": source["m2922_summary"].get("status_pass"), "gate_matrix_pass": source["m2922_summary"].get("gate_matrix_pass")}, "both true", "lineage_invalid"),
        ("m2923_accepts_m2922", "lineage", "accepts M2922" in source["m2923_audit_text"], "accepts M2922" in source["m2923_audit_text"], True, "lineage_invalid"),
        ("m2924_admits_m2925", "lineage", MILESTONE_ID in source["m2924_design_text"], MILESTONE_ID in source["m2924_design_text"], True, "lineage_invalid"),
        ("execution_rows_loaded", "localization", len(execution_rows) == EXPECTED_TOTAL_ROW_COUNT, len(execution_rows), EXPECTED_TOTAL_ROW_COUNT, "metric_artifact"),
        ("offtrack_rows_accounted", "localization", len(offtrack_rows) == EXPECTED_OFFTRACK_COUNT, len(offtrack_rows), EXPECTED_OFFTRACK_COUNT, "metric_artifact"),
        ("non_offtrack_context_rows_accounted", "localization", len(context_rows) == EXPECTED_NON_OFFTRACK_CONTEXT_COUNT, len(context_rows), EXPECTED_NON_OFFTRACK_CONTEXT_COUNT, "metric_artifact"),
        ("source_slice_counts_match_design", "localization", offtrack_source_counts == EXPECTED_OFFTRACK_SOURCE_COUNTS, offtrack_source_counts, EXPECTED_OFFTRACK_SOURCE_COUNTS, "metric_artifact"),
        ("task_slice_counts_match_design", "localization", offtrack_task_counts == EXPECTED_OFFTRACK_TASK_COUNTS, offtrack_task_counts, EXPECTED_OFFTRACK_TASK_COUNTS, "metric_artifact"),
        ("checkpoint_slice_counts_match_design", "localization", checkpoint_counts == EXPECTED_CHECKPOINT_CONTEXT_COUNTS, checkpoint_counts, EXPECTED_CHECKPOINT_CONTEXT_COUNTS, "metric_artifact"),
        ("environment_slice_counts_match_design", "localization", environment_counts == EXPECTED_ENVIRONMENT_COUNTS, environment_counts, EXPECTED_ENVIRONMENT_COUNTS, "metric_artifact"),
        ("window_slice_counts_match_design", "localization", window_counts == EXPECTED_WINDOW_COUNTS, window_counts, EXPECTED_WINDOW_COUNTS, "metric_artifact"),
        ("overshoot_band_counts_match_design", "localization", overshoot_counts == EXPECTED_OVERSHOOT_BAND_COUNTS, overshoot_counts, EXPECTED_OVERSHOOT_BAND_COUNTS, "metric_artifact"),
        ("time_band_counts_match_design", "localization", time_counts == EXPECTED_TIME_BAND_COUNTS, time_counts, EXPECTED_TIME_BAND_COUNTS, "metric_artifact"),
        ("all_offtrack_slices_diagnostic_only", "claim_boundary", all(_bool(row.get("diagnostic_only_no_verdict", False)) for row in offtrack_rows), "all diagnostic-only", "all diagnostic-only", "proof_washout"),
        ("non_offtrack_context_has_no_offtrack", "localization", all(row.get("outcome_family") != "off_track" for row in context_rows), "no offtrack in context rows", "no offtrack in context rows", "metric_artifact"),
        ("guardrails_preserved", "guardrail", route_b_context and route_c_context and m2877_context and not any_flag(guardrail_rows, "execution_run"), {"route_b_context": route_b_context, "route_c_context": route_c_context, "m2877_context": m2877_context}, "all present and not executed", "proof_washout"),
        ("actor_contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in actor_rows), f"rows={len(actor_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in actor_rows)}", "all actor guards pass", "contract_violation"),
        ("no_forbidden_execution_or_overclaim", "execution_guardrail", not any(forbidden_execution_flag(row) for row in materialized_rows), "no execution/ranking/promotion/overclaim flags", "all false", "objective_overfit"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(_bool(row["status_pass"]) for row in allowed_claims) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed pass and blocked not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2925_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def write_derived_outputs(
    paths: dict[str, Path],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    offtrack_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    environment_rows: list[dict[str, Any]],
    window_rows: list[dict[str, Any]],
    severity_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    execution_rows = source["bounded_execution_rows"]
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2922_status_pass": _bool(source["m2922_summary"].get("status_pass", False)),
        "m2922_gate_matrix_pass": _bool(source["m2922_summary"].get("gate_matrix_pass", False)),
        "execution_row_count": len(execution_rows),
        "offtrack_row_count": len(offtrack_rows),
        "non_offtrack_context_row_count": len(context_rows),
        "offtrack_source_counts": {row["slice_value"]: int(row["row_count"]) for row in source_rows},
        "offtrack_task_counts": {row["slice_value"]: int(row["row_count"]) for row in task_rows},
        "offtrack_checkpoint_context_counts": {row["slice_value"]: int(row["row_count"]) for row in checkpoint_rows},
        "offtrack_environment_counts": {row["slice_value"]: int(row["row_count"]) for row in environment_rows},
        "offtrack_window_counts": {row["slice_value"]: int(row["row_count"]) for row in window_rows},
        "offtrack_overshoot_band_counts": {
            row["slice_value"]: int(row["row_count"])
            for row in severity_rows
            if row["slice_family"] == "overshoot_band"
        },
        "offtrack_time_band_counts": {
            row["slice_value"]: int(row["row_count"])
            for row in severity_rows
            if row["slice_family"] == "time_to_offtrack_band"
        },
        "source_slice_row_count": len(source_rows),
        "task_slice_row_count": len(task_rows),
        "checkpoint_slice_row_count": len(checkpoint_rows),
        "environment_slice_row_count": len(environment_rows),
        "window_slice_row_count": len(window_rows),
        "severity_slice_row_count": len(severity_rows),
        "guardrail_context_row_count": len(guardrail_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "all_selected_metrics_finite": selected_metrics_are_finite(execution_rows) if execution_rows else False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "dependency_execution_performed": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_simulation_run": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2925 Engineering Controller Route A Offtrack-Dominant Failure Slice Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- execution rows read: {summary['execution_row_count']}",
            f"- offtrack rows materialized: {summary['offtrack_row_count']}",
            f"- non-offtrack context rows preserved: {summary['non_offtrack_context_row_count']}",
            f"- source counts: {summary['offtrack_source_counts']}",
            f"- task counts: {summary['offtrack_task_counts']}",
            f"- checkpoint context counts: {summary['offtrack_checkpoint_context_counts']}",
            f"- environment counts: {summary['offtrack_environment_counts']}",
            f"- window counts: {summary['offtrack_window_counts']}",
            f"- overshoot bands: {summary['offtrack_overshoot_band_counts']}",
            f"- time bands: {summary['offtrack_time_band_counts']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2925 materializes no-execution offtrack failure-slice rows from already-recorded M2919 diagnostics. It does not rerun environments, train, rank, promote, or claim performance.",
            "",
            "Rejected claims:",
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
        "hypothesis": "A bounded result audit can accept or reject the M2925 offtrack-dominant failure-slice materialization before any repair execution validation ranking promotion performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "offtrack_slice_rows.csv"),
                str(output_dir / "offtrack_source_slice_rows.csv"),
                str(output_dir / "offtrack_task_slice_rows.csv"),
                str(output_dir / "offtrack_checkpoint_slice_rows.csv"),
                str(output_dir / "offtrack_environment_slice_rows.csv"),
                str(output_dir / "offtrack_window_slice_rows.csv"),
                str(output_dir / "offtrack_severity_slice_rows.csv"),
                str(output_dir / "non_offtrack_context_rows.csv"),
                str(output_dir / "guardrail_context_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2924-engineering-controller-route-a-offtrack-dominant-failure-slice-design.md",
            ],
            "parent_config": [
                "experiments/manifests/m2925-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-preflight.json",
                "experiments/manifests/m2924-engineering-controller-route-a-offtrack-dominant-failure-slice-design.json",
            ],
            "parent_objective": ["audit M2925 offtrack-slice materialization artifacts before any interpretation"],
            "derived_from": [MILESTONE_ID, "m2924-engineering-controller-route-a-offtrack-dominant-failure-slice-design"],
            "blocked_by": [
                "M2925 materialization requires a result audit before any repair design or route interpretation",
                "offtrack slice rows are localization rows rather than validation or performance evidence",
            ],
            "supersedes": ["direct interpretation of M2925 slice rows without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2926 must audit M2925 summary gate matrix actor and claim boundaries",
            "M2926 must preserve the 38 offtrack and 18 non-offtrack accounting",
            "M2926 must preserve M2877 Route B Route C guardrail exclusions",
            "M2926 must not claim validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M2926 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert M2925 slice rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_failure_slice_result_audit",
            "evidence_increment": "audits offtrack-dominant failure-slice materialization artifacts from M2925",
            "claim_scope": "Result audit only; no validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2925 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if offtrack or non-offtrack accounting changed",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if localization is complete but no route candidate is viable",
                "route to a bounded design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2925 completes offtrack-dominant failure-slice materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2925 offtrack-dominant failure-slice materialization artifacts",
            "admission_evidence": [
                "M2925 summary and gate matrix",
                "M2925 offtrack slice context guard actor claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2926 status queue scoreboard research log and review",
                "one follow-up manifest only if M2926 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2926 audit accepts or rejects M2925 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2926 audits Route A offtrack slice materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2926; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2925 Route A offtrack-dominant failure slice materialization only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2925 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized offtrack-dominant failure-slice rows",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A engineering continuation only",
            "must_synthesize_if": [
                "M2926 cannot accept M2925 as complete and claim-safe",
                "M2926 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2926 would continue static design without new materialized evidence or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2926 audits M2925 artifacts row counts gates actor and claim boundaries",
            "M2926 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2926 hides M2925 failures or missing artifacts",
            "M2926 treats M2925 localization as validation readiness or performance verdict",
            "M2926 changes actor input or action contract",
            "M2926 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2926 audits M2925 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "offtrack_slice_rows.csv"),
            str(output_dir / "offtrack_severity_slice_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "m2925_execution_performed",
            "environment_reset_run",
            "environment_step_run",
            "policy_action_run",
            "policy_rollout_run",
            "measured_validation_run",
            "training_started",
            "training_scheduled",
            "training_run",
            "replay_started",
            "replay_run",
            "ppo_used",
            "ppo_run",
            "source_build_run",
            "adapter_probe_run",
            "external_simulation_run",
            "dependency_execution_performed",
            "private_holdout_used",
            "ranking_allowed",
            "ranking_run",
            "ranking_claim_made",
            "winner_selection_allowed",
            "winner_selected",
            "promotion_allowed",
            "checkpoint_promoted",
            "actor_input_contract_changed",
            "hidden_oracle_actor_input_required",
            "future_target_actor_input_required",
            "route_labels_actor_visible",
            "source_labels_actor_visible",
            "diagnostic_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
            "success_rate_verdict_claim_made",
            "driver_performance_claim_made",
            "validation_readiness_claim_made",
            "validation_result_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "full_ideal_driver_gate_passed",
            "full_ideal_driver_completion_claim_made",
            "level3_self_id_claim_made",
        )
    )


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def mean_float(rows: Iterable[Mapping[str, Any]], key: str) -> float | str:
    values = []
    for row in rows:
        value = _float_value(row.get(key, float("nan")))
        if np.isfinite(value):
            values.append(value)
    if not values:
        return ""
    return float(sum(values) / len(values))


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _float_or_blank(value: Any) -> float | str:
    number = _float_value(value)
    if not np.isfinite(number):
        return ""
    return number


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2922-dir", type=Path, default=DEFAULT_M2922_DIR)
    parser.add_argument("--m2919-dir", type=Path, default=DEFAULT_M2919_DIR)
    parser.add_argument("--m2923-audit", type=Path, default=DEFAULT_M2923_AUDIT)
    parser.add_argument("--m2924-design", type=Path, default=DEFAULT_M2924_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_offtrack_dominant_failure_slice_materialization_preflight(
        m2922_dir=args.m2922_dir,
        m2919_dir=args.m2919_dir,
        m2923_audit=args.m2923_audit,
        m2924_design=args.m2924_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"offtrack_rows={summary['offtrack_row_count']}")
    print(f"non_offtrack_context_rows={summary['non_offtrack_context_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
