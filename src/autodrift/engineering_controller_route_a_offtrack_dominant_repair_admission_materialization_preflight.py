"""Materialize M2928 offtrack-dominant repair-admission rows.

M2928 consumes accepted M2925/M2926/M2927 Route A offtrack-localization
artifacts. It performs no environment, policy, dependency, validation,
training, replay, ranking, or promotion work. Its only job is to turn the
M2927 repair-admission decision into machine-checkable repair-hypothesis,
coverage-constraint, shortcut-exclusion, actor-contract, claim-boundary, and
gate artifacts for a later result audit.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = "m2928-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-preflight"
NEXT_ID = "m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit"
DEFAULT_M2925_DIR = Path(
    "runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight"
)
DEFAULT_M2926_AUDIT = Path(
    "docs/m2926-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-result-audit.md"
)
DEFAULT_M2927_SYNTHESIS = Path(
    "docs/m2927-engineering-controller-route-a-offtrack-dominant-localization-branch-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2928_engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2928-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit.json"
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
EXPECTED_GUARDRAIL_CONTEXT_ROW_COUNT = 46

CLAIM_SCOPE = (
    "M2928 Route A offtrack-dominant repair-admission materialization only; "
    "M2925 offtrack and non-offtrack context rows may be converted into "
    "repair-hypothesis, coverage-constraint, shortcut-exclusion, actor-guard, "
    "claim-boundary, and gate rows. M2877 fixed weak diagnostic rows, Route B "
    "source-family insufficiency, and Route C source_unavailable remain "
    "guardrails or context only. No reset, step, rollout, replay, validation, "
    "training, PPO, dependency work, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "source/task/checkpoint/environment/window/severity/time-band ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

REPAIR_HYPOTHESIS_FIELDNAMES = [
    "repair_hypothesis_id",
    "repair_family",
    "repair_surface",
    "admitted_for_materialization",
    "coverage_constraint_count",
    "offtrack_rows_preserved",
    "non_offtrack_context_rows_preserved",
    "guardrails_preserved",
    "execution_scheduled",
    "validation_scheduled",
    "training_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "source_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "m2928_execution_performed",
    "required_follow_up",
    "claim_boundary",
]
COVERAGE_CONSTRAINT_FIELDNAMES = [
    "coverage_constraint_id",
    "coverage_family",
    "coverage_value",
    "observed_row_count",
    "expected_row_count",
    "source_scope",
    "coverage_constraint_status_pass",
    "ranking_claim_made",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SHORTCUT_EXCLUSION_FIELDNAMES = [
    "shortcut_exclusion_id",
    "shortcut_family",
    "excluded_signal_or_claim",
    "exclusion_reason",
    "actor_visible",
    "execution_scheduled",
    "validation_scheduled",
    "training_scheduled",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "claim_made",
    "status_pass",
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
    "allowed_in_m2928",
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
    "repair_hypothesis_rows",
    "coverage_constraint_rows",
    "shortcut_exclusion_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]
REQUIRED_SHORTCUT_FAMILIES = {
    "hidden_oracle_future_target_actor_input",
    "hidden_dynamics_parameters",
    "controller_route_labels",
    "map_or_oracle_progress_metrics",
    "rank_winner_shortcut",
    "overclaim_shortcut",
    "execution_training_shortcut",
}


def run_offtrack_dominant_repair_admission_materialization_preflight(
    *,
    m2925_dir: Path | str = DEFAULT_M2925_DIR,
    m2926_audit: Path | str = DEFAULT_M2926_AUDIT,
    m2927_synthesis: Path | str = DEFAULT_M2927_SYNTHESIS,
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
        m2925_dir=Path(m2925_dir),
        m2926_audit=Path(m2926_audit),
        m2927_synthesis=Path(m2927_synthesis),
        follow_up_manifest=Path(follow_up_manifest),
    )

    offtrack_rows = source["offtrack_slice_rows"]
    context_rows = source["non_offtrack_context_rows"]
    guardrail_rows = source["guardrail_context_rows"]
    coverage_rows = build_coverage_constraint_rows(
        summary=source["m2925_summary"],
        offtrack_rows=offtrack_rows,
        context_rows=context_rows,
        guardrail_rows=guardrail_rows,
    )
    repair_rows = build_repair_hypothesis_rows(
        coverage_constraint_count=len(coverage_rows),
        offtrack_count=len(offtrack_rows),
        context_count=len(context_rows),
        guardrails_preserved=guardrails_preserved(guardrail_rows),
    )
    shortcut_rows = build_shortcut_exclusion_rows()

    write_csv_rows(paths["repair_hypothesis_rows"], repair_rows, fieldnames=REPAIR_HYPOTHESIS_FIELDNAMES)
    write_csv_rows(paths["coverage_constraint_rows"], coverage_rows, fieldnames=COVERAGE_CONSTRAINT_FIELDNAMES)
    write_csv_rows(paths["shortcut_exclusion_rows"], shortcut_rows, fieldnames=SHORTCUT_EXCLUSION_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "repair_hypothesis_row_count": len(repair_rows),
            "coverage_constraint_row_count": len(coverage_rows),
            "shortcut_exclusion_row_count": len(shortcut_rows),
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
        repair_rows=repair_rows,
        coverage_rows=coverage_rows,
        shortcut_rows=shortcut_rows,
        guardrail_rows=guardrail_rows,
    )
    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_without_summary_doc,
        repair_rows_present=bool(repair_rows),
        coverage_rows_present=bool(coverage_rows),
        shortcut_rows_present=bool(shortcut_rows),
        guardrails_preserved=guardrails_preserved(guardrail_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        repair_rows=repair_rows,
        coverage_rows=coverage_rows,
        shortcut_rows=shortcut_rows,
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
        repair_rows=repair_rows,
        coverage_rows=coverage_rows,
        shortcut_rows=shortcut_rows,
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
        repair_rows_present=bool(repair_rows),
        coverage_rows_present=bool(coverage_rows),
        shortcut_rows_present=bool(shortcut_rows),
        guardrails_preserved=guardrails_preserved(guardrail_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        repair_rows=repair_rows,
        coverage_rows=coverage_rows,
        shortcut_rows=shortcut_rows,
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
        repair_rows=repair_rows,
        coverage_rows=coverage_rows,
        shortcut_rows=shortcut_rows,
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
            "repair_hypothesis_row_count": len(repair_rows),
            "coverage_constraint_row_count": len(coverage_rows),
            "shortcut_exclusion_row_count": len(shortcut_rows),
            "actor_contract_guard_row_count": len(actor_rows),
            "claim_boundary_row_count": len(claim_rows),
            "gate_matrix_row_count": len(gate_rows),
            "offtrack_row_count": len(source["offtrack_slice_rows"]),
            "non_offtrack_context_row_count": len(source["non_offtrack_context_rows"]),
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
        "repair_hypothesis_rows": output_dir / "repair_hypothesis_rows.csv",
        "coverage_constraint_rows": output_dir / "coverage_constraint_rows.csv",
        "shortcut_exclusion_rows": output_dir / "shortcut_exclusion_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2925_dir: Path,
    m2926_audit: Path,
    m2927_synthesis: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2926_audit": m2926_audit,
        "m2927_synthesis": m2927_synthesis,
        "m2925_summary": m2925_dir / "summary.json",
        "offtrack_slice_rows": m2925_dir / "offtrack_slice_rows.csv",
        "non_offtrack_context_rows": m2925_dir / "non_offtrack_context_rows.csv",
        "guardrail_context_rows": m2925_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": m2925_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2925_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2925_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2926_audit_text": paths["m2926_audit"].read_text(encoding="utf-8")
        if source_exists["m2926_audit"]
        else "",
        "m2927_synthesis_text": paths["m2927_synthesis"].read_text(encoding="utf-8")
        if source_exists["m2927_synthesis"]
        else "",
        "m2925_summary": read_json(paths["m2925_summary"]) if source_exists["m2925_summary"] else {},
        "offtrack_slice_rows": read_csv_rows(paths["offtrack_slice_rows"]),
        "non_offtrack_context_rows": read_csv_rows(paths["non_offtrack_context_rows"]),
        "guardrail_context_rows": read_csv_rows(paths["guardrail_context_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
    }


def build_coverage_constraint_rows(
    *,
    summary: Mapping[str, Any],
    offtrack_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
    guardrail_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    observed_source_counts = int_count_map(summary.get("offtrack_source_counts")) or count_by(offtrack_rows, "source_milestone")
    observed_task_counts = int_count_map(summary.get("offtrack_task_counts")) or count_by(offtrack_rows, "task_family")
    observed_checkpoint_counts = int_count_map(summary.get("offtrack_checkpoint_context_counts")) or count_by(
        offtrack_rows, "checkpoint_context"
    )
    observed_environment_counts = int_count_map(summary.get("offtrack_environment_counts")) or count_by(
        offtrack_rows, "env_template_family"
    )
    observed_window_counts = int_count_map(summary.get("offtrack_window_counts")) or count_by(offtrack_rows, "window_tag")
    observed_overshoot_counts = int_count_map(summary.get("offtrack_overshoot_band_counts")) or count_by(
        offtrack_rows, "offtrack_severity_band"
    )
    observed_time_counts = int_count_map(summary.get("offtrack_time_band_counts")) or count_by(
        offtrack_rows, "time_to_offtrack_band"
    )
    rows: list[dict[str, Any]] = []

    def add(
        coverage_family: str,
        coverage_value: str,
        observed: int,
        expected: int,
        source_scope: str,
    ) -> None:
        rows.append(
            {
                "coverage_constraint_id": f"m2928-coverage-{len(rows) + 1:04d}",
                "coverage_family": coverage_family,
                "coverage_value": coverage_value,
                "observed_row_count": int(observed),
                "expected_row_count": int(expected),
                "source_scope": source_scope,
                "coverage_constraint_status_pass": int(observed) == int(expected),
                "ranking_claim_made": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )

    add(
        "denominator",
        "total_m2925_rows",
        len(offtrack_rows) + len(context_rows),
        EXPECTED_TOTAL_ROW_COUNT,
        "m2925_offtrack_plus_context_rows",
    )
    add("denominator", "offtrack_rows", len(offtrack_rows), EXPECTED_OFFTRACK_COUNT, "m2925_offtrack_slice_rows")
    add(
        "denominator",
        "non_offtrack_context_rows",
        len(context_rows),
        EXPECTED_NON_OFFTRACK_CONTEXT_COUNT,
        "m2925_non_offtrack_context_rows",
    )
    for value, expected in EXPECTED_OFFTRACK_SOURCE_COUNTS.items():
        add("source_milestone", value, observed_source_counts.get(value, 0), expected, "m2925_offtrack_slice_rows")
    for value, expected in EXPECTED_OFFTRACK_TASK_COUNTS.items():
        add("task_family", value, observed_task_counts.get(value, 0), expected, "m2925_offtrack_slice_rows")
    for value, expected in EXPECTED_CHECKPOINT_CONTEXT_COUNTS.items():
        add("checkpoint_context", value, observed_checkpoint_counts.get(value, 0), expected, "m2925_offtrack_slice_rows")
    for value, expected in EXPECTED_ENVIRONMENT_COUNTS.items():
        add("env_template_family", value, observed_environment_counts.get(value, 0), expected, "m2925_offtrack_slice_rows")
    for value, expected in EXPECTED_WINDOW_COUNTS.items():
        add("window_tag", value, observed_window_counts.get(value, 0), expected, "m2925_offtrack_slice_rows")
    for value, expected in EXPECTED_OVERSHOOT_BAND_COUNTS.items():
        add("overshoot_band", value, observed_overshoot_counts.get(value, 0), expected, "m2925_offtrack_slice_rows")
    for value, expected in EXPECTED_TIME_BAND_COUNTS.items():
        add("time_to_offtrack_band", value, observed_time_counts.get(value, 0), expected, "m2925_offtrack_slice_rows")
    expected_guardrail_count = int(summary.get("guardrail_context_row_count", EXPECTED_GUARDRAIL_CONTEXT_ROW_COUNT))
    add(
        "guardrail_context",
        "m2877_route_b_route_c_context_rows",
        len(guardrail_rows),
        expected_guardrail_count,
        "m2925_guardrail_context_rows",
    )
    return rows


def build_repair_hypothesis_rows(
    *,
    coverage_constraint_count: int,
    offtrack_count: int,
    context_count: int,
    guardrails_preserved: bool,
) -> list[dict[str, Any]]:
    specs = [
        (
            "history_response_offtrack_stability_repair_admission",
            "history_response_stability",
            "Future repair may adjust recurrent or belief-state training surfaces using deployable history and response signals only.",
            "M2929 result audit before any execution design",
        ),
        (
            "coverage_preserving_offtrack_replay_panel_admission",
            "coverage_preserving_panel",
            "Future execution panel must preserve source task checkpoint environment window severity and time-band coverage constraints.",
            "M2929 result audit before any bounded execution manifest",
        ),
        (
            "actor_contract_guarded_repair_smoke_admission",
            "actor_contract_guarded_smoke",
            "Future smoke must enforce observation 72 action 3 and actor-visible human-view fields only.",
            "M2929 actor and shortcut audit",
        ),
        (
            "no_shortcut_boundary_repair_admission",
            "shortcut_exclusion_boundary",
            "Future repair must block oracle dynamics route labels progress labels winner ranking and overclaim shortcuts.",
            "M2929 shortcut-exclusion audit",
        ),
    ]
    rows = []
    for index, (repair_id, family, surface, follow_up) in enumerate(specs, start=1):
        row = {
            "repair_hypothesis_id": f"m2928-{repair_id}-{index:04d}",
            "repair_family": family,
            "repair_surface": surface,
            "admitted_for_materialization": True,
            "coverage_constraint_count": coverage_constraint_count,
            "offtrack_rows_preserved": offtrack_count,
            "non_offtrack_context_rows_preserved": context_count,
            "guardrails_preserved": guardrails_preserved,
            "required_follow_up": follow_up,
            "claim_boundary": CLAIM_SCOPE,
        }
        row.update(no_execution_contract_flags())
        rows.append(row)
    return rows


def build_shortcut_exclusion_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "hidden_oracle_future_target_actor_input",
            "hidden dynamics oracle labels future targets route labels source labels diagnostic labels success progress labels verdict labels",
            "Actor input must remain deployable human-view observation only.",
        ),
        (
            "hidden_dynamics_parameters",
            "mu mass tire stiffness brake scale actuator tau slip tire force hidden dynamics",
            "Repair admission cannot rely on privileged simulator parameters.",
        ),
        (
            "controller_route_labels",
            "AEB AES drift controller mode route family source family labels",
            "Controller or route labels are evaluator-side metadata only.",
        ),
        (
            "map_or_oracle_progress_metrics",
            "speed_ref path_error heading_error path_curvature TTC required_clearance oracle_stopping_distance",
            "Progress and clearance metrics cannot become actor inputs or repair shortcuts.",
        ),
        (
            "rank_winner_shortcut",
            "source task checkpoint environment window overshoot time rank winner",
            "M2928 coverage rows are constraints, not rankings.",
        ),
        (
            "overclaim_shortcut",
            "validation performance repair_success paper current_sim high_fidelity finite_window_vs_gru full_driver self_id",
            "M2928 cannot make verdict or paper-level claims.",
        ),
        (
            "execution_training_shortcut",
            "reset step rollout replay validation training PPO dependency source_build adapter_probe",
            "M2928 is a no-execution materialization preflight.",
        ),
    ]
    rows = []
    for index, (family, excluded, reason) in enumerate(specs, start=1):
        rows.append(
            {
                "shortcut_exclusion_id": f"m2928-shortcut-exclusion-{index:04d}",
                "shortcut_family": family,
                "excluded_signal_or_claim": excluded,
                "exclusion_reason": reason,
                "actor_visible": False,
                "execution_scheduled": False,
                "validation_scheduled": False,
                "training_scheduled": False,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "claim_made": False,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    repair_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized_rows = repair_rows + coverage_rows + shortcut_rows
    combined = materialized_rows + guardrail_rows
    return [
        actor_guard("observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("m2928_execution_performed", any_flag(materialized_rows, "m2928_execution_performed"), False),
        actor_guard("execution_scheduled", any_flag(materialized_rows, "execution_scheduled"), False),
        actor_guard("validation_scheduled", any_flag(materialized_rows, "validation_scheduled"), False),
        actor_guard("training_scheduled", any_flag(materialized_rows, "training_scheduled"), False),
        actor_guard("ranking_allowed", any_flag(materialized_rows, "ranking_allowed"), False),
        actor_guard("winner_selection_allowed", any_flag(materialized_rows, "winner_selection_allowed"), False),
        actor_guard("promotion_allowed", any_flag(materialized_rows, "promotion_allowed"), False),
        actor_guard("actor_input_contract_changed", any_flag(materialized_rows, "actor_input_contract_changed"), False),
        actor_guard("hidden_oracle_actor_input_required", any_flag(combined, "hidden_oracle_actor_input_required"), False),
        actor_guard("future_target_actor_input_required", any_flag(combined, "future_target_actor_input_required"), False),
        actor_guard("source_labels_actor_visible", any_flag(combined, "source_labels_actor_visible"), False),
        actor_guard("diagnostic_labels_actor_visible", any_flag(combined, "diagnostic_labels_actor_visible"), False),
        actor_guard("success_progress_labels_actor_visible", any_flag(combined, "success_progress_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", any_flag(combined, "verdict_labels_actor_visible"), False),
        actor_guard("coverage_constraints_actor_visible", any_flag(coverage_rows, "actor_visible"), False),
        actor_guard("shortcut_exclusions_actor_visible", any_flag(shortcut_rows, "actor_visible"), False),
        actor_guard("guardrail_execution", any_flag(guardrail_rows, "execution_run"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2928-actor-guard-{field}",
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
    repair_rows_present: bool,
    coverage_rows_present: bool,
    shortcut_rows_present: bool,
    guardrails_preserved: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("repair_hypothesis_rows_materialized", "artifact", repair_rows_present, "repair_hypothesis_rows.csv"),
        ("coverage_constraint_rows_materialized", "artifact", coverage_rows_present, "coverage_constraint_rows.csv"),
        ("shortcut_exclusion_rows_materialized", "artifact", shortcut_rows_present, "shortcut_exclusion_rows.csv"),
        ("guardrail_context_preserved", "guardrail", guardrails_preserved, "M2877 Route B Route C guardrails"),
        ("actor_guard_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("summary_doc_materialized", "artifact", artifacts_present, "summary.json and milestone doc"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2929 audit manifest"),
    ]
    blocked = [
        ("reset_step_rollout_replay", "execution", "future bounded execution manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("dependency_execution", "execution", "future dependency route"),
        ("source_task_checkpoint_band_ranking", "ranking", "future audited comparison route"),
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
        "claim_id": f"m2928_{claim_id}",
        "claim_family": family,
        "allowed_in_m2928": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    repair_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2928"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2928"])]
    materialized_rows = repair_rows + coverage_rows + shortcut_rows + guardrail_rows
    shortcut_families = {str(row.get("shortcut_family", "")) for row in shortcut_rows}
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2925/M2926/M2927/follow-up artifacts present",
            "lineage_invalid",
        ),
        (
            "m2925_status_pass",
            "lineage",
            _bool(source["m2925_summary"].get("status_pass", False))
            and _bool(source["m2925_summary"].get("gate_matrix_pass", False)),
            {
                "status_pass": source["m2925_summary"].get("status_pass"),
                "gate_matrix_pass": source["m2925_summary"].get("gate_matrix_pass"),
            },
            "both true",
            "lineage_invalid",
        ),
        (
            "m2926_accepts_m2925",
            "lineage",
            "accepts M2925" in source["m2926_audit_text"],
            "accepts M2925" in source["m2926_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2927_admits_m2928",
            "lineage",
            MILESTONE_ID in source["m2927_synthesis_text"] and "synthesis decision: `continue`" in source["m2927_synthesis_text"],
            {
                "m2928_id_present": MILESTONE_ID in source["m2927_synthesis_text"],
                "continue_decision_present": "synthesis decision: `continue`" in source["m2927_synthesis_text"],
            },
            "M2927 continue decision names M2928",
            "lineage_invalid",
        ),
        (
            "total_denominator_preserved",
            "coverage",
            len(source["offtrack_slice_rows"]) + len(source["non_offtrack_context_rows"]) == EXPECTED_TOTAL_ROW_COUNT,
            len(source["offtrack_slice_rows"]) + len(source["non_offtrack_context_rows"]),
            EXPECTED_TOTAL_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "offtrack_rows_preserved",
            "coverage",
            len(source["offtrack_slice_rows"]) == EXPECTED_OFFTRACK_COUNT,
            len(source["offtrack_slice_rows"]),
            EXPECTED_OFFTRACK_COUNT,
            "metric_artifact",
        ),
        (
            "non_offtrack_context_rows_preserved",
            "coverage",
            len(source["non_offtrack_context_rows"]) == EXPECTED_NON_OFFTRACK_CONTEXT_COUNT,
            len(source["non_offtrack_context_rows"]),
            EXPECTED_NON_OFFTRACK_CONTEXT_COUNT,
            "metric_artifact",
        ),
        (
            "coverage_constraints_match_expected_counts",
            "coverage",
            all(_bool(row.get("coverage_constraint_status_pass", False)) for row in coverage_rows),
            f"rows={len(coverage_rows)} pass={sum(_bool(row.get('coverage_constraint_status_pass', False)) for row in coverage_rows)}",
            "all coverage constraints pass",
            "metric_artifact",
        ),
        (
            "coverage_constraints_not_rankings",
            "claim_boundary",
            not any_flag(coverage_rows, "ranking_claim_made")
            and not any_flag(coverage_rows, "validation_denominator_allowed")
            and not any_flag(coverage_rows, "paper_denominator_allowed")
            and not any_flag(coverage_rows, "actor_visible"),
            "coverage constraints are diagnostic-only and actor-invisible",
            "no ranking validation paper or actor-visible coverage rows",
            "objective_overfit",
        ),
        (
            "repair_hypotheses_materialized_no_execution",
            "claim_boundary",
            len(repair_rows) >= 4
            and not any_flag(repair_rows, "execution_scheduled")
            and not any_flag(repair_rows, "validation_scheduled")
            and not any_flag(repair_rows, "training_scheduled")
            and not any_flag(repair_rows, "ranking_allowed")
            and not any_flag(repair_rows, "winner_selection_allowed")
            and not any_flag(repair_rows, "promotion_allowed"),
            f"repair_rows={len(repair_rows)} no execution/training/ranking/promotion flags",
            "at least 4 repair hypotheses and all forbidden flags false",
            "objective_overfit",
        ),
        (
            "shortcut_exclusions_cover_required_families",
            "shortcut",
            REQUIRED_SHORTCUT_FAMILIES.issubset(shortcut_families),
            sorted(shortcut_families),
            sorted(REQUIRED_SHORTCUT_FAMILIES),
            "proof_washout",
        ),
        (
            "guardrails_preserved",
            "guardrail",
            guardrails_preserved(guardrail_rows),
            guardrail_presence(guardrail_rows),
            "route_b route_c m2877 present and not executed",
            "proof_washout",
        ),
        (
            "actor_contract_guards_pass",
            "contract",
            all(_bool(row.get("status_pass", False)) for row in actor_rows),
            f"rows={len(actor_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in actor_rows)}",
            "all actor guards pass",
            "contract_violation",
        ),
        (
            "no_forbidden_execution_or_overclaim",
            "execution_guardrail",
            not any(forbidden_execution_flag(row) for row in materialized_rows),
            "no execution/ranking/promotion/overclaim flags",
            "all false",
            "objective_overfit",
        ),
        (
            "claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in allowed_claims)
            and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims),
            f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}",
            "allowed pass and blocked not made",
            "proof_washout",
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
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2928_{gate_id}",
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
    repair_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    m2925_summary = source["m2925_summary"]
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2925_status_pass": _bool(m2925_summary.get("status_pass", False)),
        "m2925_gate_matrix_pass": _bool(m2925_summary.get("gate_matrix_pass", False)),
        "offtrack_row_count": len(source["offtrack_slice_rows"]),
        "non_offtrack_context_row_count": len(source["non_offtrack_context_rows"]),
        "denominator_total_row_count": len(source["offtrack_slice_rows"]) + len(source["non_offtrack_context_rows"]),
        "offtrack_source_counts": int_count_map(m2925_summary.get("offtrack_source_counts")),
        "offtrack_task_counts": int_count_map(m2925_summary.get("offtrack_task_counts")),
        "offtrack_checkpoint_context_counts": int_count_map(m2925_summary.get("offtrack_checkpoint_context_counts")),
        "offtrack_environment_counts": int_count_map(m2925_summary.get("offtrack_environment_counts")),
        "offtrack_window_counts": int_count_map(m2925_summary.get("offtrack_window_counts")),
        "offtrack_overshoot_band_counts": int_count_map(m2925_summary.get("offtrack_overshoot_band_counts")),
        "offtrack_time_band_counts": int_count_map(m2925_summary.get("offtrack_time_band_counts")),
        "repair_hypothesis_row_count": len(repair_rows),
        "coverage_constraint_row_count": len(coverage_rows),
        "coverage_constraint_rows_pass": all(_bool(row.get("coverage_constraint_status_pass", False)) for row in coverage_rows),
        "shortcut_exclusion_row_count": len(shortcut_rows),
        "shortcut_exclusion_families": sorted({str(row.get("shortcut_family", "")) for row in shortcut_rows}),
        "guardrail_context_row_count": len(guardrail_rows),
        "guardrails_preserved": guardrails_preserved(guardrail_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
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
            "# M2928 Engineering Controller Route A Offtrack-Dominant Repair Admission Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- denominator rows preserved: {summary['denominator_total_row_count']}",
            f"- offtrack rows preserved: {summary['offtrack_row_count']}",
            f"- non-offtrack context rows preserved: {summary['non_offtrack_context_row_count']}",
            f"- repair hypothesis rows: {summary['repair_hypothesis_row_count']}",
            f"- coverage constraint rows: {summary['coverage_constraint_row_count']}",
            f"- shortcut exclusion rows: {summary['shortcut_exclusion_row_count']}",
            f"- guardrails preserved: {summary['guardrails_preserved']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Coverage Constraints",
            "",
            f"- source counts: {summary['offtrack_source_counts']}",
            f"- task counts: {summary['offtrack_task_counts']}",
            f"- checkpoint context counts: {summary['offtrack_checkpoint_context_counts']}",
            f"- environment counts: {summary['offtrack_environment_counts']}",
            f"- window counts: {summary['offtrack_window_counts']}",
            f"- overshoot bands: {summary['offtrack_overshoot_band_counts']}",
            f"- time bands: {summary['offtrack_time_band_counts']}",
            "",
            "## Boundary",
            "",
            "M2928 materializes repair-admission rows only. Coverage rows are constraints, not rankings. It does not rerun environments, train, validate, rank, promote, or claim repair success.",
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
        "hypothesis": "A bounded result audit can accept or reject the M2928 repair-admission materialization before any repair execution validation ranking promotion performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "repair_hypothesis_rows.csv"),
                str(output_dir / "coverage_constraint_rows.csv"),
                str(output_dir / "shortcut_exclusion_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "run_state.json"),
                str(doc_path),
                "docs/m2927-engineering-controller-route-a-offtrack-dominant-localization-branch-synthesis.md",
                "docs/m2926-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-result-audit.md",
                "runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight/summary.json",
            ],
            "parent_config": [
                "experiments/manifests/m2928-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-preflight.json",
                "experiments/manifests/m2927-engineering-controller-route-a-offtrack-dominant-localization-branch-synthesis.json",
            ],
            "parent_objective": ["audit M2928 repair-admission materialization artifacts before any repair execution design"],
            "derived_from": [
                MILESTONE_ID,
                "m2927-engineering-controller-route-a-offtrack-dominant-localization-branch-synthesis",
                "m2926-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-result-audit",
                "m2925-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-preflight",
            ],
            "blocked_by": [
                "M2928 materialization requires a result audit before any repair execution design",
                "offtrack repair-admission rows are planning artifacts rather than validation or performance evidence",
            ],
            "supersedes": ["direct repair execution from M2927 without M2928 result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2929 must audit M2928 summary gate matrix actor and claim boundaries",
            "M2929 must preserve the 38 offtrack and 18 non-offtrack coverage constraints",
            "M2929 must preserve M2877 Route B Route C guardrail exclusions",
            "M2929 must not claim validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M2929 must select exactly one next route or stop state",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun reset rollout replay validate rank promote publish select a winner or execute dependency work",
            "do not fit train or run PPO",
            "do not change actor input or action contract",
            "do not convert M2928 repair-admission rows into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_repair_admission_result_audit",
            "evidence_increment": "audits repair-admission materialization artifacts from M2928",
            "claim_scope": "Result audit only; no repair execution validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2928 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if offtrack or non-offtrack coverage accounting changed",
            ],
            "fallback_plan": [
                "route to artifact repair if accounting failed",
                "route to branch synthesis if repair admission is complete but no execution route is viable",
                "route to a bounded execution design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2928 completes offtrack-dominant repair-admission materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2928 offtrack-dominant repair-admission materialization artifacts",
            "admission_evidence": [
                "M2928 summary and gate matrix",
                "M2928 repair hypothesis coverage shortcut actor claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no training replay PPO or checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2929 status queue scoreboard research log and review",
                "one follow-up manifest only if M2929 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2929 audit accepts or rejects M2928 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2929 audits Route A repair-admission materialization and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2929; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2928 Route A offtrack-dominant repair-admission materialization only.",
            "negative_result_policy": "Preserve negative or insufficient diagnostics and route to synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2928 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized offtrack-dominant repair-admission rows",
            "paper_verdict_delta": "no paper verdict; audit may admit one bounded Route A repair execution design only",
            "must_synthesize_if": [
                "M2929 cannot accept M2928 as complete and claim-safe",
                "M2929 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
                "M2929 would continue static design without new materialized evidence or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2929 audits M2928 artifacts row counts gates actor and claim boundaries",
            "M2929 selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2929 hides M2928 failures or missing artifacts",
            "M2929 treats M2928 repair admission as validation readiness or performance verdict",
            "M2929 changes actor input or action contract",
            "M2929 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2929 audits M2928 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "repair_hypothesis_rows.csv"),
            str(output_dir / "coverage_constraint_rows.csv"),
            str(output_dir / "shortcut_exclusion_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def no_execution_contract_flags() -> dict[str, Any]:
    return {
        "execution_scheduled": False,
        "validation_scheduled": False,
        "training_scheduled": False,
        "ranking_allowed": False,
        "winner_selection_allowed": False,
        "promotion_allowed": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "m2928_execution_performed": False,
    }


def guardrail_presence(guardrail_rows: Iterable[Mapping[str, Any]]) -> dict[str, bool]:
    families = [str(row.get("guardrail_family", "")) for row in guardrail_rows]
    return {
        "route_b_context": any("route_b" in family or "source_family_insufficiency" in family for family in families),
        "route_c_context": any("route_c" in family or "source_unavailable" in family for family in families),
        "m2877_context": any("m2877" in family for family in families),
        "guardrail_execution": any_flag(guardrail_rows, "execution_run"),
    }


def guardrails_preserved(guardrail_rows: Iterable[Mapping[str, Any]]) -> bool:
    presence = guardrail_presence(guardrail_rows)
    return (
        presence["route_b_context"]
        and presence["route_c_context"]
        and presence["m2877_context"]
        and not presence["guardrail_execution"]
    )


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "m2928_execution_performed",
            "environment_reset_run",
            "environment_step_run",
            "policy_action_run",
            "policy_rollout_run",
            "measured_validation_run",
            "validation_scheduled",
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
            "repair_success_claim_made",
            "validation_readiness_claim_made",
            "validation_result_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "full_ideal_driver_gate_passed",
            "full_ideal_driver_completion_claim_made",
            "level3_self_id_claim_made",
            "claim_made",
        )
    )


def count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = str(row.get(key, ""))
        if value:
            counter[value] += 1
    return dict(counter)


def int_count_map(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, int] = {}
    for key, item in value.items():
        try:
            out[str(key)] = int(item)
        except (TypeError, ValueError):
            continue
    return out


def any_flag(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


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
    parser.add_argument("--m2925-dir", type=Path, default=DEFAULT_M2925_DIR)
    parser.add_argument("--m2926-audit", type=Path, default=DEFAULT_M2926_AUDIT)
    parser.add_argument("--m2927-synthesis", type=Path, default=DEFAULT_M2927_SYNTHESIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_offtrack_dominant_repair_admission_materialization_preflight(
        m2925_dir=args.m2925_dir,
        m2926_audit=args.m2926_audit,
        m2927_synthesis=args.m2927_synthesis,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")
    print(f"repair_hypothesis_rows={summary['repair_hypothesis_row_count']}")
    print(f"coverage_constraint_rows={summary['coverage_constraint_row_count']}")
    print(f"shortcut_exclusion_rows={summary['shortcut_exclusion_row_count']}")
    print(f"summary={summary['paths']['summary']}")


if __name__ == "__main__":
    main()
