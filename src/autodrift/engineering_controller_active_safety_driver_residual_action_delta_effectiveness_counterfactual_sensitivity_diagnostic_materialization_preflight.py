"""Materialize M3150 residual action-delta effectiveness sensitivity diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3150-engineering-controller-active-safety-driver-residual-action-delta-effectiveness-"
    "counterfactual-sensitivity-diagnostic-materialization-preflight"
)
NEXT_ID = (
    "m3151-engineering-controller-active-safety-driver-residual-action-delta-effectiveness-"
    "counterfactual-sensitivity-diagnostic-result-audit"
)
M3149_ID = "m3149-engineering-controller-active-safety-driver-speed-envelope-action-delta-effectiveness-and-saturation-synthesis"
M3147_ID = (
    "m3147-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-"
    "action-delta-coverage-diagnostic-materialization-preflight"
)

DEFAULT_M3149_SYNTHESIS = Path(f"docs/{M3149_ID}.md")
DEFAULT_M3147_DIR = Path(
    "runs/m3147_engineering_controller_active_safety_driver_residual_trajectory_timing_"
    "speed_envelope_action_delta_coverage_diagnostic_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3150_engineering_controller_active_safety_driver_residual_action_delta_effectiveness_"
    "counterfactual_sensitivity_diagnostic_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_RESIDUAL_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
CLAIM_SCOPE = (
    "M3150 Active Safety Driver residual action-delta effectiveness counterfactual "
    "sensitivity diagnostic only; M3147 trace artifacts may be reanalyzed without new "
    "environment reset step rollout validation ranking or repair implementation to write "
    "terminal-window authority headroom, delta-utilization, saturation, claim, gate, doc, "
    "and M3151 audit artifacts. No validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, driver-performance verdict, current-sim verdict, "
    "repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, high-fidelity validation readiness or result, "
    "paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or "
    "level3 self-identification"
)

EFFECTIVENESS_FIELDNAMES = [
    "effectiveness_row_id",
    "residual_failure_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "target_failure_kind",
    "terminal_termination_reason",
    "trace_step_count",
    "terminal_window_step_count",
    "terminal_window_start_step",
    "terminal_window_end_step",
    "final_mean_fallback_steer",
    "final_mean_fallback_throttle",
    "final_mean_fallback_brake",
    "final_mean_candidate_steer",
    "final_mean_candidate_throttle",
    "final_mean_candidate_brake",
    "final_mean_abs_delta_steer",
    "final_mean_delta_throttle",
    "final_mean_delta_brake",
    "final_max_delta_abs",
    "candidate_saturation_fraction",
    "fallback_saturation_fraction",
    "terminal_window_candidate_saturation_fraction",
    "candidate_brake_headroom_to_max_mean",
    "candidate_throttle_drop_headroom_mean",
    "candidate_steer_headroom_mean",
    "brake_delta_utilization_fraction",
    "throttle_drop_delta_utilization_fraction",
    "steer_delta_utilization_fraction",
    "terminal_window_min_clearance_margin_min",
    "terminal_window_speed_mean",
    "terminal_window_beta_abs_mean",
    "counterfactual_sensitivity_label",
    "counterfactual_sensitivity_interpretation",
    "recommended_next_audit_focus",
    "environment_reset_run",
    "environment_step_run",
    "policy_rollout_run",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
SUMMARY_FIELDNAMES = [
    "summary_row_id",
    "residual_effectiveness_row_count",
    "collision_row_count",
    "offtrack_row_count",
    "headroom_available_count",
    "saturation_limited_count",
    "terminal_delta_low_count",
    "delta_present_counterfactual_needed_count",
    "dominant_sensitivity_label",
    "mean_brake_headroom",
    "mean_throttle_drop_headroom",
    "mean_steer_headroom",
    "mean_candidate_saturation_fraction",
    "diagnostic_boundary",
    "environment_reset_run",
    "environment_step_run",
    "policy_rollout_run",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3150",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else ""


def _min(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.min(finite)) if finite else ""


def _max(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.max(finite)) if finite else ""


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "residual_delta_effectiveness_rows": output_dir / "residual_delta_effectiveness_rows.csv",
        "sensitivity_summary_rows": output_dir / "sensitivity_summary_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3149_synthesis: Path, m3147_dir: Path) -> dict[str, Any]:
    paths = {
        "m3149_synthesis": m3149_synthesis,
        "m3147_summary": m3147_dir / "summary.json",
        "m3147_step_rows": m3147_dir / "action_delta_step_trace_rows.csv",
        "m3147_coverage_rows": m3147_dir / "action_delta_coverage_rows.csv",
        "m3147_summary_rows": m3147_dir / "residual_overlay_coverage_summary_rows.csv",
        "m3147_gate_rows": m3147_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3149_synthesis_text": paths["m3149_synthesis"].read_text(encoding="utf-8") if exists["m3149_synthesis"] else "",
        "m3147_summary": read_json(paths["m3147_summary"]) if exists["m3147_summary"] else {},
        "m3147_step_rows": read_csv_rows(paths["m3147_step_rows"]),
        "m3147_coverage_rows": read_csv_rows(paths["m3147_coverage_rows"]),
        "m3147_summary_rows": read_csv_rows(paths["m3147_summary_rows"]),
        "m3147_gate_rows": read_csv_rows(paths["m3147_gate_rows"]),
    }


def _terminal_window(rows: list[dict[str, Any]], count: int = 10) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: int(_float(row.get("step_index"), 0.0)))
    return ordered[-count:] if len(ordered) > count else ordered


def _fraction(rows: list[dict[str, Any]], predicate: Any) -> float | str:
    if not rows:
        return ""
    return float(np.mean([1.0 if predicate(row) else 0.0 for row in rows]))


def _utilization(delta_used: float, remaining_headroom: float) -> float | str:
    used = abs(delta_used)
    headroom = max(remaining_headroom, 0.0)
    denom = used + headroom
    return float(used / denom) if denom > 1e-9 else ""


def _label_effectiveness(row: Mapping[str, Any]) -> tuple[str, str, str]:
    kind = str(row.get("target_failure_kind", ""))
    brake_delta = _float(row.get("final_mean_delta_brake"), 0.0)
    throttle_delta = _float(row.get("final_mean_delta_throttle"), 0.0)
    steer_delta = _float(row.get("final_mean_abs_delta_steer"), 0.0)
    brake_headroom = _float(row.get("candidate_brake_headroom_to_max_mean"), 0.0)
    throttle_headroom = _float(row.get("candidate_throttle_drop_headroom_mean"), 0.0)
    steer_headroom = _float(row.get("candidate_steer_headroom_mean"), 0.0)
    saturation = _float(row.get("candidate_saturation_fraction"), 0.0)

    if kind == "collision":
        if saturation >= 0.30:
            return (
                "collision_action_saturation_limited",
                "collision residual has frequent candidate action saturation in the full trace",
                "audit_saturation_limited_collision_rows_before_repair",
            )
        if brake_delta < 0.05 and throttle_delta > -0.05 and (brake_headroom > 0.20 or throttle_headroom > 0.20):
            return (
                "collision_terminal_delta_low_headroom_available",
                "terminal collision window still has brake or throttle-drop headroom while applied delta is low",
                "audit_terminal_deceleration_headroom_and_channel_mix",
            )
        return (
            "collision_delta_present_counterfactual_needed",
            "collision residual has active deltas but needs audited counterfactual sensitivity before repair",
            "audit_collision_delta_effectiveness_before_repair",
        )
    if kind == "offtrack":
        if steer_delta < 0.05 and steer_headroom > 0.20:
            return (
                "offtrack_steer_delta_low_headroom_available",
                "offtrack terminal window retains steering headroom while steer delta is low",
                "audit_lateral_authority_headroom_and_channel_mix",
            )
        return (
            "offtrack_delta_present_counterfactual_needed",
            "offtrack residual has active deltas but needs audited lateral sensitivity before repair",
            "audit_offtrack_delta_effectiveness_before_repair",
        )
    return (
        "non_target_failure_kind",
        "row is outside expected residual collision/offtrack target set",
        "audit_row_identity_before_repair",
    )


def effectiveness_row_from_trace(index: int, coverage: Mapping[str, Any], step_rows: list[dict[str, Any]]) -> dict[str, Any]:
    window = _terminal_window(step_rows)
    start_step = int(_float(window[0].get("step_index"), 0.0)) if window else ""
    end_step = int(_float(window[-1].get("step_index"), 0.0)) if window else ""
    final_candidate_steer = _mean(_float(row.get("candidate_steer")) for row in window)
    final_candidate_throttle = _mean(_float(row.get("candidate_throttle")) for row in window)
    final_candidate_brake = _mean(_float(row.get("candidate_brake")) for row in window)
    final_abs_candidate_steer = _mean(abs(_float(row.get("candidate_steer"), 0.0)) for row in window)
    final_delta_steer_abs = _mean(abs(_float(row.get("delta_steer"), 0.0)) for row in window)
    final_delta_throttle = _mean(_float(row.get("delta_throttle")) for row in window)
    final_delta_brake = _mean(_float(row.get("delta_brake")) for row in window)
    brake_headroom = _mean(1.0 - _float(row.get("candidate_brake"), 0.0) for row in window)
    throttle_headroom = _mean(_float(row.get("candidate_throttle"), 0.0) + 1.0 for row in window)
    steer_headroom = _mean(1.0 - abs(_float(row.get("candidate_steer"), 0.0)) for row in window)
    candidate_saturation = _float(coverage.get("candidate_saturation_fraction"), 0.0)
    row = {
        "effectiveness_row_id": f"m3150-residual-delta-effectiveness-{index:04d}",
        "residual_failure_id": coverage.get("residual_failure_id", ""),
        "source_measurement_episode_id": coverage.get("source_measurement_episode_id", ""),
        "fresh_panel_row_id": coverage.get("fresh_panel_row_id", ""),
        "axis_id": coverage.get("axis_id", ""),
        "binding_role": coverage.get("binding_role", ""),
        "target_failure_kind": coverage.get("target_failure_kind", ""),
        "terminal_termination_reason": coverage.get("terminal_termination_reason", ""),
        "trace_step_count": coverage.get("trace_step_count", ""),
        "terminal_window_step_count": len(window),
        "terminal_window_start_step": start_step,
        "terminal_window_end_step": end_step,
        "final_mean_fallback_steer": _mean(_float(row.get("fallback_steer")) for row in window),
        "final_mean_fallback_throttle": _mean(_float(row.get("fallback_throttle")) for row in window),
        "final_mean_fallback_brake": _mean(_float(row.get("fallback_brake")) for row in window),
        "final_mean_candidate_steer": final_candidate_steer,
        "final_mean_candidate_throttle": final_candidate_throttle,
        "final_mean_candidate_brake": final_candidate_brake,
        "final_mean_abs_delta_steer": final_delta_steer_abs,
        "final_mean_delta_throttle": final_delta_throttle,
        "final_mean_delta_brake": final_delta_brake,
        "final_max_delta_abs": _max(_float(row.get("delta_max_abs")) for row in window),
        "candidate_saturation_fraction": candidate_saturation,
        "fallback_saturation_fraction": _float(coverage.get("fallback_saturation_fraction"), 0.0),
        "terminal_window_candidate_saturation_fraction": _fraction(window, lambda row: _bool(row.get("candidate_action_saturated", False))),
        "candidate_brake_headroom_to_max_mean": brake_headroom,
        "candidate_throttle_drop_headroom_mean": throttle_headroom,
        "candidate_steer_headroom_mean": steer_headroom,
        "brake_delta_utilization_fraction": _utilization(_float(final_delta_brake, 0.0), _float(brake_headroom, 0.0)),
        "throttle_drop_delta_utilization_fraction": _utilization(_float(final_delta_throttle, 0.0), _float(throttle_headroom, 0.0)),
        "steer_delta_utilization_fraction": _utilization(_float(final_delta_steer_abs, 0.0), _float(steer_headroom, 0.0)),
        "terminal_window_min_clearance_margin_min": _min(_float(row.get("min_clearance_margin_m_after_step")) for row in window),
        "terminal_window_speed_mean": _mean(_float(row.get("speed_mps_after_step")) for row in window),
        "terminal_window_beta_abs_mean": _mean(abs(_float(row.get("beta_after_step"), 0.0)) for row in window),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "runtime_base_policy_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "repair_success_claim_made": False,
        "validation_run": False,
        "driver_performance_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }
    label, interpretation, focus = _label_effectiveness(row)
    row["counterfactual_sensitivity_label"] = label
    row["counterfactual_sensitivity_interpretation"] = interpretation
    row["recommended_next_audit_focus"] = focus
    del final_abs_candidate_steer
    return row


def residual_delta_effectiveness_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    steps_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source.get("m3147_step_rows", []):
        steps_by_source[str(row.get("source_measurement_episode_id", ""))].append(row)
    rows: list[dict[str, Any]] = []
    for index, coverage in enumerate(source.get("m3147_coverage_rows", []), start=1):
        source_id = str(coverage.get("source_measurement_episode_id", ""))
        rows.append(effectiveness_row_from_trace(index, coverage, steps_by_source.get(source_id, [])))
    return rows


def sensitivity_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = Counter(str(row.get("counterfactual_sensitivity_label", "")) for row in rows)
    dominant = labels.most_common(1)[0][0] if labels else ""
    return [
        {
            "summary_row_id": "m3150-sensitivity-summary-0001",
            "residual_effectiveness_row_count": len(rows),
            "collision_row_count": sum(1 for row in rows if str(row.get("target_failure_kind", "")) == "collision"),
            "offtrack_row_count": sum(1 for row in rows if str(row.get("target_failure_kind", "")) == "offtrack"),
            "headroom_available_count": sum(
                1
                for row in rows
                if _float(row.get("candidate_brake_headroom_to_max_mean"), 0.0) > 0.20
                or _float(row.get("candidate_throttle_drop_headroom_mean"), 0.0) > 0.20
                or _float(row.get("candidate_steer_headroom_mean"), 0.0) > 0.20
            ),
            "saturation_limited_count": sum(
                1 for row in rows if "saturation_limited" in str(row.get("counterfactual_sensitivity_label", ""))
            ),
            "terminal_delta_low_count": sum(
                1 for row in rows if "terminal_delta_low" in str(row.get("counterfactual_sensitivity_label", ""))
            ),
            "delta_present_counterfactual_needed_count": sum(
                1 for row in rows if "counterfactual_needed" in str(row.get("counterfactual_sensitivity_label", ""))
            ),
            "dominant_sensitivity_label": dominant,
            "mean_brake_headroom": _mean(_float(row.get("candidate_brake_headroom_to_max_mean")) for row in rows),
            "mean_throttle_drop_headroom": _mean(_float(row.get("candidate_throttle_drop_headroom_mean")) for row in rows),
            "mean_steer_headroom": _mean(_float(row.get("candidate_steer_headroom_mean")) for row in rows),
            "mean_candidate_saturation_fraction": _mean(_float(row.get("candidate_saturation_fraction")) for row in rows),
            "diagnostic_boundary": "no-new-execution action-delta sensitivity only; no repair-success or validation claim",
            "environment_reset_run": False,
            "environment_step_run": False,
            "policy_rollout_run": False,
            "repair_success_claim_made": False,
            "validation_run": False,
            "driver_performance_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31510,
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
        "hypothesis": "A bounded result audit can accept or reject the M3150 residual action-delta sensitivity diagnostics before any repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "residual_delta_effectiveness_rows.csv"),
                str(output_dir / "sensitivity_summary_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3150 residual action-delta sensitivity diagnostics"],
            "derived_from": [MILESTONE_ID, M3149_ID, M3147_ID],
            "blocked_by": [
                "M3150 diagnostic labels require audit before any repair route",
                "counterfactual sensitivity rows are not repair-success or performance evidence",
            ],
            "supersedes": ["direct interpretation of M3150 diagnostics without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3151 must audit M3150 row counts gates actor contract and claim boundaries",
            "M3151 must preserve no-new-execution diagnostic boundary",
            "M3151 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3151 must choose exactly one next route: synthesis, no-go, artifact repair, or bounded repair hypothesis",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run tune expand rank promote validate or mutate checkpoints",
            "do not convert M3150 sensitivity labels into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_action_delta_effectiveness_diagnostic",
            "evidence_axis": "residual_action_delta_sensitivity_result_audit",
            "evidence_increment": "audits terminal-window action headroom and sensitivity labels from M3150",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3150 artifacts are missing or gate matrix fails",
                "stop if no-new-execution or actor contracts were violated",
                "synthesize before any repair if labels are mixed or inconclusive",
            ],
            "fallback_plan": [
                "route to M3150 artifact repair if diagnostics are incomplete",
                "route to no-go if sensitivity cannot justify a bounded repair hypothesis",
                "route to synthesis if diagnostics identify an actor-visible channel gap",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3150 completes sensitivity diagnostic materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3150 residual action-delta sensitivity diagnostics",
            "admission_evidence": ["M3150 summary residual_delta_effectiveness rows gate matrix and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3151 status queue scoreboard research log and review",
                "one follow-up manifest only if M3151 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3151 accepts or rejects M3150 as complete and claim-safe",
                "M3151 selects synthesis no-go artifact repair or bounded repair route explicitly",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3151 audits engineering trace reanalysis artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3151; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3150 diagnostic artifacts only.",
            "negative_result_policy": "Preserve diagnostics and route to engineering synthesis or no-go rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3150 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits no-new-execution action-delta sensitivity diagnostics before any repair branch",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3151 audits engineering sensitivity evidence",
            "must_synthesize_if": [
                "M3151 cannot accept M3150 as complete and claim-safe",
                "M3151 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result feasibility-proof or self-ID evidence",
                "M3151 cannot select synthesis no-go artifact repair or bounded repair route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3151 audits M3150 rows gates no-new-execution boundary and claim boundaries",
            "M3151 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3151 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3151 hides M3150 missing rows or missing artifacts",
            "M3151 treats M3150 diagnostics as validation repair-success or performance verdict",
            "M3151 changes actor input or action contract",
            "M3151 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3151 audits M3150 artifacts and selects one next route while preserving no-new-execution and claim boundaries.",
        "commands": [{"name": "active_safety_driver_residual_action_delta_sensitivity_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("residual_delta_effectiveness_rows", "diagnostic_reanalysis", True, "residual_delta_effectiveness_rows.csv"),
        ("sensitivity_summary_rows", "diagnostic_summary", True, "sensitivity_summary_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3151 audit manifest"),
    ]
    blocked = [
        ("new_environment_execution", "execution", "future audited execution route"),
        ("repair_implementation", "repair", "future audited repair synthesis route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair measurement audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("feasibility_proof", "proof", "future feasibility proof route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
    ]
    rows = [
        {
            "claim_id": f"m3150-{claim_id}",
            "claim_family": family,
            "allowed_in_m3150": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3150-{claim_id}",
            "claim_family": family,
            "allowed_in_m3150": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3150-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def _forbidden_flags_clear(rows: list[dict[str, Any]]) -> bool:
    return not any(
        _bool(row.get(key, False))
        for row in rows
        for key in (
            "environment_reset_run",
            "environment_step_run",
            "policy_rollout_run",
            "runtime_base_policy_required",
            "hidden_oracle_actor_input_required",
            "ttc_actor_input_required",
            "repair_success_claim_made",
            "validation_run",
            "driver_performance_claim_made",
        )
    )


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    effectiveness_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    synthesis_text = str(source.get("m3149_synthesis_text", ""))
    source_ids = {str(row.get("source_measurement_episode_id", "")) for row in effectiveness_rows}
    step_source_ids = {str(row.get("source_measurement_episode_id", "")) for row in source.get("m3147_step_rows", [])}
    step_counts = Counter(str(row.get("source_measurement_episode_id", "")) for row in source.get("m3147_step_rows", []))
    kind_counts = Counter(str(row.get("target_failure_kind", "")) for row in effectiveness_rows)
    combined = effectiveness_rows + summary_rows
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3149_pivots_to_m3150", "lineage", "pivot_to_m3150_residual_action_delta_effectiveness_counterfactual_sensitivity_diagnostic" in synthesis_text, "pivot marker", "present", "lineage_invalid"),
        gate("m3147_status_pass", "lineage", _bool(source["m3147_summary"].get("status_pass", False)), source["m3147_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3147_gate_matrix_pass", "lineage", _bool(source["m3147_summary"].get("gate_matrix_pass", False)), source["m3147_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3147_step_rows_nonempty", "source", bool(source.get("m3147_step_rows", [])), len(source.get("m3147_step_rows", [])), "nonzero", "metric_artifact"),
        gate("m3147_coverage_rows", "source", len(source.get("m3147_coverage_rows", [])) == EXPECTED_RESIDUAL_ROWS, len(source.get("m3147_coverage_rows", [])), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("m3147_gate_rows_pass", "lineage", all(_bool(row.get("status_pass", False)) for row in source.get("m3147_gate_rows", [])), len(source.get("m3147_gate_rows", [])), "all pass", "lineage_invalid"),
        gate("effectiveness_row_count", "diagnostic", len(effectiveness_rows) == EXPECTED_RESIDUAL_ROWS, len(effectiveness_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("effectiveness_collision_count", "diagnostic", kind_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS, dict(sorted(kind_counts.items())), EXPECTED_COLLISION_ROWS, "scenario_sampling_failure"),
        gate("effectiveness_offtrack_count", "diagnostic", kind_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(kind_counts.items())), EXPECTED_OFFTRACK_ROWS, "scenario_sampling_failure"),
        gate("step_identity_complete", "diagnostic", source_ids == step_source_ids and all(step_counts[source_id] > 0 for source_id in source_ids), dict(sorted(step_counts.items())), "all residual rows have steps", "metric_artifact"),
        gate("terminal_windows_nonempty", "diagnostic", all(int(_float(row.get("terminal_window_step_count"), 0.0)) > 0 for row in effectiveness_rows), "all", "nonempty", "metric_artifact"),
        gate("sensitivity_summary_rows", "diagnostic", len(summary_rows) == 1, len(summary_rows), 1, "metric_artifact"),
        gate("no_new_execution_boundary", "claim", _forbidden_flags_clear(combined), "forbidden execution/claim flags", "clear", "contract_violation"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    label_counts = summary.get("counterfactual_sensitivity_label_counts", {})
    label_lines = [f"- {label}: {count}" for label, count in sorted(label_counts.items())]
    return "\n".join(
        [
            "# M3150 Residual Action-Delta Effectiveness Counterfactual Sensitivity Diagnostic",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- residual effectiveness rows: {summary['residual_delta_effectiveness_row_count']}/{summary['target_residual_row_count']}",
            f"- source M3147 step rows: {summary['m3147_step_row_count']}",
            f"- headroom available rows: {summary['headroom_available_count']}",
            f"- saturation-limited rows: {summary['saturation_limited_count']}",
            f"- terminal-delta-low rows: {summary['terminal_delta_low_count']}",
            f"- delta-present counterfactual-needed rows: {summary['delta_present_counterfactual_needed_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Sensitivity Labels",
            "",
            *(label_lines or ["- none: 0"]),
            "",
            "## Interpretation",
            "",
            "M3150 reanalyzes existing M3147 action-delta traces only. It estimates terminal-window action headroom, delta utilization, and saturation labels for the seven residual rows. These artifacts are diagnostic and no-new-execution. They are not repair implementation, validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, feasibility-proof, or self-ID evidence.",
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


def run_sensitivity_diagnostic_preflight(
    *,
    m3149_synthesis: Path,
    m3147_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3149_synthesis=m3149_synthesis, m3147_dir=m3147_dir)
    effectiveness_rows = residual_delta_effectiveness_rows(source)
    summary_rows = sensitivity_summary_rows(effectiveness_rows)

    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["residual_delta_effectiveness_rows"], effectiveness_rows, EFFECTIVENESS_FIELDNAMES),
        (paths["sensitivity_summary_rows"], summary_rows, SUMMARY_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        effectiveness_rows=effectiveness_rows,
        summary_rows=summary_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    labels = Counter(str(row.get("counterfactual_sensitivity_label", "")) for row in effectiveness_rows)
    summary_row = summary_rows[0] if summary_rows else {}
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_action_delta_sensitivity_diagnostic_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_action_delta_sensitivity_diagnostic_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "target_residual_row_count": EXPECTED_RESIDUAL_ROWS,
        "residual_delta_effectiveness_row_count": len(effectiveness_rows),
        "sensitivity_summary_row_count": len(summary_rows),
        "m3147_step_row_count": len(source.get("m3147_step_rows", [])),
        "m3147_coverage_row_count": len(source.get("m3147_coverage_rows", [])),
        "counterfactual_sensitivity_label_counts": dict(sorted(labels.items())),
        "headroom_available_count": summary_row.get("headroom_available_count", 0),
        "saturation_limited_count": summary_row.get("saturation_limited_count", 0),
        "terminal_delta_low_count": summary_row.get("terminal_delta_low_count", 0),
        "delta_present_counterfactual_needed_count": summary_row.get("delta_present_counterfactual_needed_count", 0),
        "mean_brake_headroom": summary_row.get("mean_brake_headroom", ""),
        "mean_throttle_drop_headroom": summary_row.get("mean_throttle_drop_headroom", ""),
        "mean_steer_headroom": summary_row.get("mean_steer_headroom", ""),
        "mean_candidate_saturation_fraction": summary_row.get("mean_candidate_saturation_fraction", ""),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3147_status_pass": _bool(source["m3147_summary"].get("status_pass", False)),
        "m3147_gate_matrix_pass": _bool(source["m3147_summary"].get("gate_matrix_pass", False)),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_materialization_run": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_action_delta_sensitivity_diagnostic_route_to_m3151_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "residual_delta_effectiveness_row_count": len(effectiveness_rows),
            "sensitivity_summary_row_count": len(summary_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3149-synthesis", type=Path, default=DEFAULT_M3149_SYNTHESIS)
    parser.add_argument("--m3147-dir", type=Path, default=DEFAULT_M3147_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_sensitivity_diagnostic_preflight(
        m3149_synthesis=args.m3149_synthesis,
        m3147_dir=args.m3147_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"residual_delta_effectiveness_rows={summary['residual_delta_effectiveness_row_count']}")
    print(f"m3147_step_rows={summary['m3147_step_row_count']}")
    print(f"headroom_available_count={summary['headroom_available_count']}")
    print(f"saturation_limited_count={summary['saturation_limited_count']}")
    print(f"terminal_delta_low_count={summary['terminal_delta_low_count']}")
    print(f"delta_present_counterfactual_needed_count={summary['delta_present_counterfactual_needed_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
