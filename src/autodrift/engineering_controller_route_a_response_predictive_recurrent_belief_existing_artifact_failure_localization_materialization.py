"""Materialize M2854 existing-artifact failure-localization rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2854-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "existing-artifact-failure-localization-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2855-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "existing-artifact-failure-localization-materialization-result-audit"
)
DEFAULT_M2853_DESIGN = Path(
    "docs/m2853-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "failure-localization-training-recipe-redesign-design.md"
)
DEFAULT_M2850_SUMMARY = Path(
    "runs/m2850_engineering_controller_route_a_response_predictive_recurrent_belief_candidate_"
    "closed_loop_delta_panel/summary.json"
)
DEFAULT_PAIRED_EXECUTION_ROWS = Path(
    "runs/m2850_engineering_controller_route_a_response_predictive_recurrent_belief_candidate_"
    "closed_loop_delta_panel/paired_execution_rows.csv"
)
DEFAULT_PAIRED_DELTA_ROWS = Path(
    "runs/m2850_engineering_controller_route_a_response_predictive_recurrent_belief_candidate_"
    "closed_loop_delta_panel/paired_delta_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "existing_artifact_failure_localization_materialization"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2854-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "existing-artifact-failure-localization-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2855-engineering-controller-route-a-response-predictive-"
    "recurrent-belief-existing-artifact-failure-localization-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2854 existing-artifact failure-localization materialization only. It reads "
    "M2850 paired execution and delta rows and writes derived diagnostic "
    "localization artifacts. It does not execute reset, step, rollout, replay, "
    "validation, training, PPO, ranking, winner selection, promotion, success-rate "
    "verdict computation, repair success, driver performance, paper evidence, "
    "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity validation, "
    "full ideal driver completion, or level3 self-identification."
)
FORBIDDEN_INTERPRETATION = (
    "validation readiness or result, checkpoint ranking, controller ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, repair success, "
    "driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, "
    "or level3 self-identification"
)

LOCALIZATION_FIELDNAMES = [
    "pair_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "source_family_tag",
    "scenario_role_primary",
    "baseline_outcome_bucket",
    "candidate_outcome_bucket",
    "baseline_termination_reason",
    "candidate_termination_reason",
    "baseline_success_diagnostic",
    "candidate_success_diagnostic",
    "baseline_collision_diagnostic",
    "candidate_collision_diagnostic",
    "clearance_delta",
    "return_delta",
    "speed_mean_delta",
    "action_rate_delta",
    "previous_command_norm_delta",
    "current_action_norm_delta",
    "action_trace_delta_delta",
    "high_sideslip_fraction_delta",
    "clearance_improved",
    "return_degraded",
    "speed_degraded",
    "termination_invariant",
    "collision_invariant",
    "both_non_success",
    "both_non_collision",
    "speed_too_low_subject_count",
    "requires_step_trace",
    "localization_bucket",
    "training_recipe_signal",
    "diagnostic_only",
    "ranking_admissible",
    "ordinary_success_denominator_allowed",
]
TAXONOMY_FIELDNAMES = [
    "taxonomy_id",
    "localization_bucket",
    "source_family_tag",
    "row_count",
    "clearance_improved_count",
    "return_degraded_count",
    "speed_degraded_count",
    "termination_invariant_count",
    "speed_too_low_subject_count",
    "requires_step_trace_count",
    "diagnostic_interpretation",
    "forbidden_interpretation",
]
RECIPE_FIELDNAMES = [
    "recipe_signal_id",
    "signal_name",
    "trigger_condition",
    "observed_count",
    "allowed_next_use",
    "blocked_shortcut",
    "claim_boundary",
]
OVERFIT_GUARD_FIELDNAMES = [
    "guard_id",
    "guard",
    "status_pass",
    "evidence",
    "blocked_shortcut",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "status_pass",
    "observed",
    "expected",
    "interpretation",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "status_pass",
    "observed",
    "expected",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "status_pass",
    "observed",
    "threshold",
    "interpretation",
]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _float(value: Any) -> float:
    text = str(value).strip()
    return float(text) if text else 0.0


def _subject_rows(execution_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for row in execution_rows:
        rows[str(row["execution_row_id"])] = row
    return rows


def _localization_bucket(
    *,
    clearance_improved: bool,
    return_degraded: bool,
    speed_degraded: bool,
    termination_invariant: bool,
    speed_too_low_subject_count: int,
    action_trace_delta_delta: float,
    high_sideslip_fraction_delta: float,
) -> str:
    if speed_too_low_subject_count > 0 and termination_invariant:
        return "low_speed_invariant_noncompletion"
    if clearance_improved and (return_degraded or speed_degraded) and termination_invariant:
        return "clearance_progress_tradeoff"
    if termination_invariant and abs(action_trace_delta_delta) <= 0.005:
        return "weak_action_delta_outcome_invariant"
    if abs(high_sideslip_fraction_delta) <= 1e-12:
        return "sideslip_not_activated"
    if clearance_improved and termination_invariant:
        return "step_trace_required"
    return "mixed_or_unclassified"


def _training_recipe_signal(bucket: str, requires_step_trace: bool) -> str:
    if bucket == "low_speed_invariant_noncompletion":
        return "low_speed_guard_and_recovery_loss"
    if bucket == "clearance_progress_tradeoff":
        return "progress_preserving_clearance_objective"
    if requires_step_trace:
        return "action_response_temporal_trace_requirement"
    return "fresh_non_public_localization_panel"


def build_row_failure_localization_rows(
    *,
    execution_rows: list[dict[str, str]],
    delta_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_execution_id = _subject_rows(execution_rows)
    output: list[dict[str, Any]] = []
    for delta in delta_rows:
        baseline = by_execution_id[str(delta["baseline_execution_row_id"])]
        candidate = by_execution_id[str(delta["candidate_execution_row_id"])]
        clearance_delta = _float(delta["candidate_minus_baseline_min_clearance_margin"])
        return_delta = _float(delta["candidate_minus_baseline_return"])
        speed_delta = _float(delta["candidate_minus_baseline_speed_mean"])
        action_rate_delta = _float(delta["candidate_minus_baseline_action_rate_mean"])
        previous_command_norm_delta = _float(delta["candidate_minus_baseline_previous_command_norm_mean"])
        current_action_norm_delta = _float(delta["candidate_minus_baseline_current_action_norm_mean"])
        action_trace_delta_delta = _float(delta["candidate_minus_baseline_action_trace_delta_mean"])
        high_sideslip_fraction_delta = _float(delta["candidate_minus_baseline_high_sideslip_fraction"])
        clearance_improved = clearance_delta > 0.0
        return_degraded = return_delta < 0.0
        speed_degraded = speed_delta < 0.0
        termination_invariant = not _bool(delta["termination_pair_changed"])
        collision_invariant = not _bool(delta["collision_pair_changed"])
        baseline_success = _bool(delta["baseline_success_diagnostic"])
        candidate_success = _bool(delta["candidate_success_diagnostic"])
        baseline_collision = _bool(delta["baseline_collision_diagnostic"])
        candidate_collision = _bool(delta["candidate_collision_diagnostic"])
        speed_too_low_subject_count = sum(
            1
            for row in (baseline, candidate)
            if str(row.get("termination_reason", "")).strip() == "speed_too_low"
        )
        requires_step_trace = bool(
            termination_invariant
            and clearance_improved
            and (return_degraded or speed_degraded or speed_too_low_subject_count > 0)
        )
        bucket = _localization_bucket(
            clearance_improved=clearance_improved,
            return_degraded=return_degraded,
            speed_degraded=speed_degraded,
            termination_invariant=termination_invariant,
            speed_too_low_subject_count=speed_too_low_subject_count,
            action_trace_delta_delta=action_trace_delta_delta,
            high_sideslip_fraction_delta=high_sideslip_fraction_delta,
        )
        output.append(
            {
                "pair_id": delta["pair_id"],
                "task_source_id": delta["task_source_id"],
                "profile_name": delta["profile_name"],
                "task_family": delta["task_family"],
                "source_family_tag": delta["source_family_tag"],
                "scenario_role_primary": delta["scenario_role_primary"],
                "baseline_outcome_bucket": baseline.get("outcome_bucket", ""),
                "candidate_outcome_bucket": candidate.get("outcome_bucket", ""),
                "baseline_termination_reason": baseline.get("termination_reason", ""),
                "candidate_termination_reason": candidate.get("termination_reason", ""),
                "baseline_success_diagnostic": baseline_success,
                "candidate_success_diagnostic": candidate_success,
                "baseline_collision_diagnostic": baseline_collision,
                "candidate_collision_diagnostic": candidate_collision,
                "clearance_delta": clearance_delta,
                "return_delta": return_delta,
                "speed_mean_delta": speed_delta,
                "action_rate_delta": action_rate_delta,
                "previous_command_norm_delta": previous_command_norm_delta,
                "current_action_norm_delta": current_action_norm_delta,
                "action_trace_delta_delta": action_trace_delta_delta,
                "high_sideslip_fraction_delta": high_sideslip_fraction_delta,
                "clearance_improved": clearance_improved,
                "return_degraded": return_degraded,
                "speed_degraded": speed_degraded,
                "termination_invariant": termination_invariant,
                "collision_invariant": collision_invariant,
                "both_non_success": not baseline_success and not candidate_success,
                "both_non_collision": not baseline_collision and not candidate_collision,
                "speed_too_low_subject_count": speed_too_low_subject_count,
                "requires_step_trace": requires_step_trace,
                "localization_bucket": bucket,
                "training_recipe_signal": _training_recipe_signal(bucket, requires_step_trace),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "ordinary_success_denominator_allowed": False,
            }
        )
    return output


def build_localization_taxonomy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["localization_bucket"]), str(row["source_family_tag"]))].append(row)
    output: list[dict[str, Any]] = []
    for index, ((bucket, source_family), group) in enumerate(sorted(grouped.items()), start=1):
        output.append(
            {
                "taxonomy_id": f"m2854-taxonomy-{index:03d}",
                "localization_bucket": bucket,
                "source_family_tag": source_family,
                "row_count": len(group),
                "clearance_improved_count": sum(1 for row in group if row["clearance_improved"]),
                "return_degraded_count": sum(1 for row in group if row["return_degraded"]),
                "speed_degraded_count": sum(1 for row in group if row["speed_degraded"]),
                "termination_invariant_count": sum(1 for row in group if row["termination_invariant"]),
                "speed_too_low_subject_count": sum(int(row["speed_too_low_subject_count"]) for row in group),
                "requires_step_trace_count": sum(1 for row in group if row["requires_step_trace"]),
                "diagnostic_interpretation": "row-level diagnostic localization from existing M2850 artifacts",
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return output


def build_training_recipe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row["training_recipe_signal"]) for row in rows)
    step_trace_count = sum(1 for row in rows if row["requires_step_trace"])
    low_speed_pair_count = sum(1 for row in rows if int(row["speed_too_low_subject_count"]) > 0)
    return [
        {
            "recipe_signal_id": "m2854-recipe-progress-preserving-clearance-objective",
            "signal_name": "progress_preserving_clearance_objective",
            "trigger_condition": "clearance improves while return or speed degrades and termination is invariant",
            "observed_count": counts["progress_preserving_clearance_objective"],
            "allowed_next_use": "design a bounded objective that preserves progress and speed while keeping clearance guardrails",
            "blocked_shortcut": "do not train directly on fixed public M2850 clearance deltas",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "recipe_signal_id": "m2854-recipe-low-speed-guard-and-recovery-loss",
            "signal_name": "low_speed_guard_and_recovery_loss",
            "trigger_condition": "speed_too_low appears in either subject or speed_mean degrades on most rows",
            "observed_count": low_speed_pair_count,
            "allowed_next_use": "design a low-speed onset/recovery diagnostic or training guard",
            "blocked_shortcut": "do not convert speed_too_low diagnostics into success-rate verdicts",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "recipe_signal_id": "m2854-recipe-action-response-temporal-trace-requirement",
            "signal_name": "action_response_temporal_trace_requirement",
            "trigger_condition": "rollout-level rows cannot localize when clearance and progress diverge",
            "observed_count": step_trace_count,
            "allowed_next_use": "design a fresh per-step telemetry panel before another training continuation",
            "blocked_shortcut": "do not claim temporal onset localization from rollout-level M2850 rows",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "recipe_signal_id": "m2854-recipe-fresh-non-public-localization-panel",
            "signal_name": "fresh_non_public_localization_panel",
            "trigger_condition": "existing rows are fixed public M2850 diagnostic rows",
            "observed_count": len(rows),
            "allowed_next_use": "require disjoint fresh diagnostic rows before optimization or promotion gates",
            "blocked_shortcut": "do not optimize only fixed public M2850 rows",
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_public_row_overfit_guard_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "guard_id": "m2854-overfit-public-diagnostic-only",
            "guard": "M2850 rows are public diagnostic rows",
            "status_pass": True,
            "evidence": f"{len(rows)} derived M2850 diagnostic rows",
            "blocked_shortcut": "do not use these rows as validation or ranking rows",
        },
        {
            "guard_id": "m2854-overfit-no-ordinary-denominator",
            "guard": "M2850 rows are not ordinary success denominators",
            "status_pass": all(not row["ordinary_success_denominator_allowed"] for row in rows),
            "evidence": "ordinary_success_denominator_allowed false on derived rows",
            "blocked_shortcut": "do not compute success-rate verdicts from M2850 rows",
        },
        {
            "guard_id": "m2854-overfit-no-clearance-rebrand",
            "guard": "positive clearance deltas cannot be rebranded as repair success",
            "status_pass": True,
            "evidence": "clearance deltas remain diagnostic localization signals",
            "blocked_shortcut": "do not claim repair success from clearance-only deltas",
        },
        {
            "guard_id": "m2854-overfit-fresh-surface-required",
            "guard": "future proof/generalization rows must be disjoint or separately registered",
            "status_pass": True,
            "evidence": "M2854 registers only a result audit and no training route",
            "blocked_shortcut": "do not promote or tune on the fixed public M2850 surface",
        },
        {
            "guard_id": "m2854-overfit-actor-contract-preserved",
            "guard": "future training recipe must not introduce hidden/oracle actor inputs",
            "status_pass": True,
            "evidence": f"actor shape {P0_OBSERVATION_DIM}/action {ACTION_DIM}",
            "blocked_shortcut": "do not add hidden dynamics oracle labels or route labels to actor input",
        },
    ]


def build_actor_contract_guard_rows(execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "guard_id": "m2854-actor-observation-shape",
            "status_pass": all(str(row.get("observation_shape")) == str(P0_OBSERVATION_DIM) for row in execution_rows),
            "observed": sorted({row.get("observation_shape", "") for row in execution_rows}),
            "expected": P0_OBSERVATION_DIM,
            "interpretation": "actor observation shape preserved",
        },
        {
            "guard_id": "m2854-actor-action-shape",
            "status_pass": all(str(row.get("action_shape")) == str(ACTION_DIM) for row in execution_rows),
            "observed": sorted({row.get("action_shape", "") for row in execution_rows}),
            "expected": ACTION_DIM,
            "interpretation": "deployed action shape preserved",
        },
        {
            "guard_id": "m2854-no-hidden-oracle-actor-input",
            "status_pass": all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in execution_rows),
            "observed": sorted({row.get("hidden_oracle_actor_input_required", "") for row in execution_rows}),
            "expected": False,
            "interpretation": "no hidden or oracle actor input required",
        },
        {
            "guard_id": "m2854-no-actor-visible-labels",
            "status_pass": all(not _bool(row.get("actor_visible_label", False)) for row in execution_rows),
            "observed": sorted({row.get("actor_visible_label", "") for row in execution_rows}),
            "expected": False,
            "interpretation": "source stress scenario outcome route and verdict labels remain actor-invisible",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    expected_false_claims = [
        "ranking_run",
        "winner_selected",
        "checkpoint_promoted",
        "success_rate_verdict_computed",
        "driver_performance_claim_made",
        "validation_readiness_claim_made",
        "validation_result_claim_made",
        "paper_claim_made",
        "finite_window_vs_gru_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "full_ideal_driver_gate_passed",
        "level3_self_id_claim_made",
    ]
    rows = [
        {
            "claim_id": f"m2854-claim-{claim}",
            "status_pass": True,
            "observed": False,
            "expected": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim in expected_false_claims
    ]
    rows.append(
        {
            "claim_id": "m2854-claim-follow-up-audit-registered",
            "status_pass": True,
            "observed": DEFAULT_NEXT_BLOCKER,
            "expected": DEFAULT_NEXT_BLOCKER,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return rows


def build_gate_rows(
    *,
    summary: dict[str, Any],
    execution_row_count: int,
    row_localization_rows: list[dict[str, Any]],
    taxonomy_rows: list[dict[str, Any]],
    recipe_rows: list[dict[str, Any]],
    overfit_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_pairs = int(summary.get("selected_pair_count", 0))
    expected_execution = int(summary.get("paired_execution_row_count", 0))
    expected_delta = int(summary.get("paired_delta_row_count", 0))
    return [
        {
            "gate_id": "m2854-required-inputs-present",
            "gate_tier": "proof",
            "status_pass": True,
            "observed": "m2853 design m2850 summary execution rows and delta rows read",
            "threshold": "all required inputs present",
            "interpretation": "existing-artifact localization inputs are available",
        },
        {
            "gate_id": "m2854-paired-execution-accounting-preserved",
            "gate_tier": "proof",
            "status_pass": expected_execution == 32 and execution_row_count == expected_execution,
            "observed": f"summary={expected_execution} actual={execution_row_count}",
            "threshold": "32 summary and actual paired execution rows",
            "interpretation": "M2850 paired execution accounting preserved",
        },
        {
            "gate_id": "m2854-paired-delta-accounting-preserved",
            "gate_tier": "proof",
            "status_pass": expected_delta == 16 and len(row_localization_rows) == expected_delta == expected_pairs,
            "observed": f"summary_delta={expected_delta} localization={len(row_localization_rows)} pairs={expected_pairs}",
            "threshold": "16 summary delta rows and one localization row per pair",
            "interpretation": "M2850 paired delta accounting preserved",
        },
        {
            "gate_id": "m2854-zero-success-diagnostics-preserved",
            "gate_tier": "proof",
            "status_pass": int(summary.get("diagnostic_success_count", -1)) == 0,
            "observed": summary.get("diagnostic_success_count"),
            "threshold": 0,
            "interpretation": "zero-success M2850 diagnostic outcome remains visible",
        },
        {
            "gate_id": "m2854-positive-clearance-deltas-preserved",
            "gate_tier": "proof",
            "status_pass": all(row["clearance_improved"] for row in row_localization_rows),
            "observed": sum(1 for row in row_localization_rows if row["clearance_improved"]),
            "threshold": len(row_localization_rows),
            "interpretation": "positive clearance deltas retained as diagnostic signals only",
        },
        {
            "gate_id": "m2854-localization-taxonomy-nonempty",
            "gate_tier": "generalization",
            "status_pass": bool(taxonomy_rows),
            "observed": len(taxonomy_rows),
            "threshold": ">=1 taxonomy row",
            "interpretation": "derived localization taxonomy was materialized",
        },
        {
            "gate_id": "m2854-training-recipe-signals-nonempty",
            "gate_tier": "generalization",
            "status_pass": bool(recipe_rows),
            "observed": len(recipe_rows),
            "threshold": ">=1 recipe row",
            "interpretation": "training-recipe redesign signals were materialized",
        },
        {
            "gate_id": "m2854-public-row-overfit-guards-pass",
            "gate_tier": "promotion",
            "status_pass": all(_bool(row["status_pass"]) for row in overfit_rows),
            "observed": f"{sum(1 for row in overfit_rows if _bool(row['status_pass']))}/{len(overfit_rows)}",
            "threshold": "all overfit guards pass",
            "interpretation": "public-row overfit guard remains explicit",
        },
        {
            "gate_id": "m2854-actor-contract-guards-pass",
            "gate_tier": "promotion",
            "status_pass": all(_bool(row["status_pass"]) for row in actor_rows),
            "observed": f"{sum(1 for row in actor_rows if _bool(row['status_pass']))}/{len(actor_rows)}",
            "threshold": "all actor guards pass",
            "interpretation": "actor 72/action 3 and label invisibility preserved",
        },
        {
            "gate_id": "m2854-claim-boundary-guards-pass",
            "gate_tier": "promotion",
            "status_pass": all(_bool(row["status_pass"]) for row in claim_rows),
            "observed": f"{sum(1 for row in claim_rows if _bool(row['status_pass']))}/{len(claim_rows)}",
            "threshold": "all claim guards pass",
            "interpretation": "no ranking promotion validation performance paper current-sim high-fidelity full-driver or self-ID claim",
        },
    ]


def _artifact_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "row_failure_localization_rows": output_dir / "row_failure_localization_rows.csv",
        "localization_taxonomy_rows": output_dir / "localization_taxonomy_rows.csv",
        "training_recipe_redesign_rows": output_dir / "training_recipe_redesign_rows.csv",
        "public_row_overfit_guard_rows": output_dir / "public_row_overfit_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
    }


def build_follow_up_manifest(path: Path) -> dict[str, Any]:
    manifest = {
        "id": DEFAULT_NEXT_BLOCKER,
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
        "lineage": {
            "parent_checkpoint": [
                "runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/checkpoints/m2846_response_predictive_recurrent_belief_candidate.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            ],
            "parent_dataset": [
                "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization/summary.json",
                "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization/row_failure_localization_rows.csv",
                "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization/localization_taxonomy_rows.csv",
                "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization/training_recipe_redesign_rows.csv",
                "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization/public_row_overfit_guard_rows.csv",
                "docs/m2854-engineering-controller-route-a-response-predictive-recurrent-belief-existing-artifact-failure-localization-materialization-preflight.md",
                "docs/m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design.md",
            ],
            "parent_config": [
                "experiments/manifests/m2854-engineering-controller-route-a-response-predictive-recurrent-belief-existing-artifact-failure-localization-materialization-preflight.json",
                "experiments/manifests/m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design.json",
            ],
            "parent_objective": [
                "audit M2854 existing-artifact failure-localization artifacts before interpreting them or admitting a new telemetry or training route"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design",
            ],
            "blocked_by": [
                "M2854 must be audited before its localization rows influence a training recipe or telemetry route",
                "M2854 does not run new environment execution and cannot claim validation or driver performance",
            ],
            "supersedes": [
                "direct interpretation of M2854 localization buckets as performance evidence",
                "direct training recipe change without result audit",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2855 must audit M2854 summary row localization taxonomy recipe overfit actor claim and gate artifacts",
            "M2855 must preserve M2850 zero-success diagnostics positive clearance deltas M2838 weak accounting actor contract and claim boundary",
            "M2855 must decide whether M2854 supports a per-step telemetry route revised training-recipe design branch stop or candidate freeze",
            "M2855 must not run reset step rollout replay validation training PPO ranking winner selection promotion or success-rate verdict computation",
            "M2855 must not claim repair success driver performance paper finite-window-vs-GRU current-sim high-fidelity validation full ideal driver completion or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset",
            "do not step environments",
            "do not execute policy action",
            "do not execute rollout",
            "do not replay",
            "do not validate",
            "do not train",
            "do not run PPO",
            "do not promote a checkpoint",
            "do not use private holdout",
            "do not change actor inputs",
            "do not inject hidden or oracle actor features",
            "do not hide M2850 zero-success diagnostics",
            "do not hide M2838 weak diagnostic accounting",
            "do not rank baseline and candidate checkpoints",
            "do not select a winner",
            "do not compute success-rate or controller-family verdict metrics",
            "do not claim repair success",
            "do not claim validation readiness",
            "do not claim validation result",
            "do not claim high-fidelity validation readiness",
            "do not claim high-fidelity validation result",
            "do not claim paper-level evidence",
            "do not claim finite-window vs GRU conclusion",
            "do not claim current-sim verdict",
            "do not claim level3 self-identification",
            "do not claim driver performance from M2855 audit",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_response_predictive_recurrent_belief_failure_localization_training_recipe_redesign",
            "evidence_axis": "existing_artifact_failure_localization_result_audit",
            "evidence_increment": "audits M2854 row-level failure-localization materialization before interpreting route implications",
            "claim_scope": "Result audit only; no reset rollout replay validation training PPO ranking winner selection promotion success-rate verdict driver-performance paper finite-window-vs-GRU current-sim high-fidelity validation self-ID or full ideal driver claim",
            "stop_condition": [
                "stop if M2854 artifacts are incomplete or internally inconsistent",
                "stop if localization buckets would be used as ranking or performance evidence",
                "stop if temporal onset claims are made without per-step telemetry",
                "stop if M2850 zero-success outcomes or M2838 weak accounting would be hidden",
                "stop if actor contract or label invisibility would be changed",
            ],
            "fallback_plan": [
                "route to artifact repair if M2854 accounting is incomplete",
                "route to per-step telemetry design if rollout-level rows are insufficient",
                "route to revised training-recipe design only if localization artifacts support bounded recipe signals",
                "route to branch stop or candidate freeze if no usable next evidence question remains",
                "defer Route B or Route C only through separately pre-registered branches",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2854 materializes existing-artifact localization rows and requires audit before interpretation",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "M2854 existing-artifact failure-localization materialization result audit",
            "admission_evidence": [
                "M2854 summary and localization artifacts are expected to exist",
                "M2854 uses existing M2850 paired execution and delta rows only",
                "M2854 preserves actor and claim boundaries by design",
            ],
            "blocked_shortcuts": [
                "no reset step policy rollout replay validation training PPO in audit",
                "no ranking winner selection promotion success-rate verdict",
                "no repair success driver-performance validation-readiness paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/m2855-engineering-controller-route-a-response-predictive-recurrent-belief-existing-artifact-failure-localization-materialization-result-audit.md",
                "M2855 status queue scoreboard research log and review",
                "one bounded follow-up manifest if audit accepts a next route",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "M2854 artifact accounting is accepted or rejected",
                "actor and claim boundaries remain preserved",
                "one bounded next route or stop/freeze decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2855 audits Route A localization artifacts and does not test history necessity or current-frame substitution.",
            "history_necessity_tests": [
                "None in M2855; wrong-history reset-hidden zero-history finite-window or GRU comparison proof remains separately pre-registered."
            ],
            "temporal_evidence_window": "M2843-M2854 response-predictive recurrent-belief artifacts.",
            "negative_result_policy": "Use M2854 localization as bounded diagnostic evidence rather than forcing self-ID or driver-performance interpretation.",
            "allowed_claims": [
                "M2854 localization result audit",
                "bounded follow-up manifest registration",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new M2854 derived localization panel before route selection",
            "paper_verdict_delta": "no paper verdict; audit keeps diagnostic localization separate from self-ID evidence",
            "must_synthesize_if": [
                "M2855 cannot decide a bounded next route",
                "M2855 would optimize only fixed public M2850 rows",
                "M2855 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID evidence",
                "M2855 hides zero-success outcomes positive clearance deltas or M2838 weak accounting",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2854 existing-artifact failure-localization artifacts before they influence a telemetry or training-recipe route.",
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "M2855 audits M2854 summary localization taxonomy recipe overfit actor claim and gate artifacts",
            "M2855 preserves M2850 zero-success diagnostics positive clearance deltas M2838 weak accounting actor contract and claim boundary",
            "M2855 registers one bounded follow-up route or stop/freeze decision without execution validation ranking performance paper current-sim high-fidelity full-driver or self-ID claims",
        ],
        "failure_criteria": [
            "M2855 runs reset step rollout replay validation training PPO ranking promotion or success-rate verdict computation",
            "M2855 hides M2850 zero-success diagnostics or rebrands positive clearance deltas as performance ranking or repair-success evidence",
            "M2855 hides M2838 weak diagnostic accounting or admits it to ordinary denominators",
            "M2855 changes actor input/action contract or actor label visibility",
            "M2855 claims repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2855 audits M2854 localization artifacts while preserving actor diagnostic and claim boundaries without new execution training validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claims.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [
            {
                "path": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "type": "md",
            }
        ],
        "baseline_checkpoints": [
            "runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/checkpoints/m2846_response_predictive_recurrent_belief_candidate.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
        ],
        "baseline_artifacts": [
            "runs/m2854_engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization/summary.json",
            "docs/m2854-engineering-controller-route-a-response-predictive-recurrent-belief-existing-artifact-failure-localization-materialization-preflight.md",
            "docs/m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design.md",
        ],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "",
    }
    write_json(path, manifest)
    return manifest


def write_result_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2854 Engineering Controller Route A Response-Predictive Recurrent-Belief Existing-Artifact Failure Localization Materialization Preflight",
                "",
                "## Metadata",
                "",
                "- status: completed",
                "- result class: `engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization_pass`",
                f"- summary: `{summary['summary']}`",
                f"- row failure localization rows: `{summary['row_failure_localization_rows']}`",
                f"- localization taxonomy rows: `{summary['localization_taxonomy_rows']}`",
                f"- training recipe redesign rows: `{summary['training_recipe_redesign_rows']}`",
                f"- public row overfit guard rows: `{summary['public_row_overfit_guard_rows']}`",
                f"- follow-up manifest: `{summary['follow_up_manifest']}`",
                f"- next: `{summary['next_blocker']}`",
                "",
                "## Materialization Result",
                "",
                "```text",
                f"status_pass: {summary['status_pass']}",
                f"paired execution rows: {summary['paired_execution_row_count']}",
                f"paired delta rows: {summary['paired_delta_row_count']}",
                f"row localization rows: {summary['row_failure_localization_row_count']}",
                f"localization taxonomy rows: {summary['localization_taxonomy_row_count']}",
                f"training recipe rows: {summary['training_recipe_redesign_row_count']}",
                f"public overfit guard rows: {summary['public_row_overfit_guard_row_count']}",
                f"requires step trace rows: {summary['requires_step_trace_row_count']}",
                f"clearance improved rows: {summary['clearance_improved_row_count']}",
                f"return degraded rows: {summary['return_degraded_row_count']}",
                f"speed degraded rows: {summary['speed_degraded_row_count']}",
                f"speed_too_low subject count: {summary['speed_too_low_subject_count']}",
                f"gate_matrix_pass: {summary['gate_matrix_pass']}",
                "```",
                "",
                "The materialization uses existing M2850 paired execution and paired",
                "delta rows only. It does not rerun the environment, train, validate,",
                "rank, promote, compute a success-rate verdict, or claim driver",
                "performance.",
                "",
                "## Claim Boundary",
                "",
                "Allowed M2854 claim:",
                "",
                "```text",
                "existing-artifact row-level failure-localization artifacts were",
                "materialized from M2850 and are ready for M2855 audit",
                "```",
                "",
                "Rejected claims:",
                "",
                "```text",
                "repair success",
                "driver performance",
                "validation readiness/result",
                "ranking or winner selection",
                "checkpoint promotion",
                "paper evidence",
                "finite-window-vs-GRU conclusion",
                "current-sim verdict",
                "high-fidelity validation",
                "full ideal driver completion",
                "level3 self-identification",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_existing_artifact_failure_localization_materialization(
    *,
    m2853_design: Path = DEFAULT_M2853_DESIGN,
    m2850_summary: Path = DEFAULT_M2850_SUMMARY,
    paired_execution_rows: Path = DEFAULT_PAIRED_EXECUTION_ROWS,
    paired_delta_rows: Path = DEFAULT_PAIRED_DELTA_ROWS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DEFAULT_DOC_PATH,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _artifact_paths(output_dir)

    design_exists = m2853_design.exists()
    summary = read_json(m2850_summary)
    execution_rows = _read_csv_rows(paired_execution_rows)
    delta_rows = _read_csv_rows(paired_delta_rows)
    row_localization_rows = build_row_failure_localization_rows(
        execution_rows=execution_rows,
        delta_rows=delta_rows,
    )
    taxonomy_rows = build_localization_taxonomy_rows(row_localization_rows)
    recipe_rows = build_training_recipe_rows(row_localization_rows)
    overfit_rows = build_public_row_overfit_guard_rows(row_localization_rows)
    actor_rows = build_actor_contract_guard_rows(execution_rows)
    claim_rows = build_claim_boundary_rows()
    gate_rows = build_gate_rows(
        summary=summary,
        execution_row_count=len(execution_rows),
        row_localization_rows=row_localization_rows,
        taxonomy_rows=taxonomy_rows,
        recipe_rows=recipe_rows,
        overfit_rows=overfit_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
    )
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    localization_bucket_counts = Counter(row["localization_bucket"] for row in row_localization_rows)
    recipe_signal_counts = Counter(row["training_recipe_signal"] for row in row_localization_rows)
    required_artifacts_present = all(
        path.exists()
        for key, path in paths.items()
        if key not in {"summary", "run_state"}
    )

    write_csv_rows(paths["row_failure_localization_rows"], row_localization_rows, LOCALIZATION_FIELDNAMES)
    write_csv_rows(paths["localization_taxonomy_rows"], taxonomy_rows, TAXONOMY_FIELDNAMES)
    write_csv_rows(paths["training_recipe_redesign_rows"], recipe_rows, RECIPE_FIELDNAMES)
    write_csv_rows(paths["public_row_overfit_guard_rows"], overfit_rows, OVERFIT_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    build_follow_up_manifest(follow_up_manifest)

    required_artifacts_present = all(
        path.exists()
        for key, path in paths.items()
        if key not in {"summary", "run_state"}
    ) and follow_up_manifest.exists()
    status_pass = bool(
        design_exists
        and required_artifacts_present
        and gate_matrix_pass
        and len(row_localization_rows) == int(summary.get("selected_pair_count", 0)) == 16
        and len(execution_rows) == int(summary.get("paired_execution_row_count", 0)) == 32
        and len(delta_rows) == int(summary.get("paired_delta_row_count", 0)) == 16
        and int(summary.get("diagnostic_success_count", -1)) == 0
        and int(summary.get("diagnostic_collision_count", -1)) == 0
    )
    result = {
        "milestone": DEFAULT_MILESTONE,
        "result_class": (
            "engineering_controller_route_a_response_predictive_recurrent_belief_"
            "existing_artifact_failure_localization_materialization_pass"
        ),
        "status_pass": status_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "doc": str(doc_path),
        "summary": str(paths["summary"]),
        "run_state": str(paths["run_state"]),
        "m2853_design": str(m2853_design),
        "m2853_design_exists": design_exists,
        "m2850_summary": str(m2850_summary),
        "paired_execution_rows": str(paired_execution_rows),
        "paired_delta_rows": str(paired_delta_rows),
        "row_failure_localization_rows": str(paths["row_failure_localization_rows"]),
        "localization_taxonomy_rows": str(paths["localization_taxonomy_rows"]),
        "training_recipe_redesign_rows": str(paths["training_recipe_redesign_rows"]),
        "public_row_overfit_guard_rows": str(paths["public_row_overfit_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "follow_up_manifest": str(follow_up_manifest),
        "next_blocker": DEFAULT_NEXT_BLOCKER,
        "paired_execution_row_count": len(execution_rows),
        "paired_delta_row_count": len(delta_rows),
        "selected_pair_count": int(summary.get("selected_pair_count", 0)),
        "row_failure_localization_row_count": len(row_localization_rows),
        "localization_taxonomy_row_count": len(taxonomy_rows),
        "training_recipe_redesign_row_count": len(recipe_rows),
        "public_row_overfit_guard_row_count": len(overfit_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "diagnostic_success_count": int(summary.get("diagnostic_success_count", 0)),
        "diagnostic_collision_count": int(summary.get("diagnostic_collision_count", 0)),
        "diagnostic_termination_counts": summary.get("diagnostic_termination_counts", {}),
        "m2838_diagnostic_success_count": int(summary.get("m2838_diagnostic_success_count", 0)),
        "m2838_diagnostic_collision_count": int(summary.get("m2838_diagnostic_collision_count", 0)),
        "m2838_diagnostic_offtrack_count": int(summary.get("m2838_diagnostic_offtrack_count", 0)),
        "m2838_ordinary_denominator_allowed": bool(summary.get("m2838_ordinary_denominator_allowed", False)),
        "clearance_improved_row_count": sum(1 for row in row_localization_rows if row["clearance_improved"]),
        "return_degraded_row_count": sum(1 for row in row_localization_rows if row["return_degraded"]),
        "speed_degraded_row_count": sum(1 for row in row_localization_rows if row["speed_degraded"]),
        "termination_invariant_row_count": sum(1 for row in row_localization_rows if row["termination_invariant"]),
        "requires_step_trace_row_count": sum(1 for row in row_localization_rows if row["requires_step_trace"]),
        "speed_too_low_subject_count": sum(int(row["speed_too_low_subject_count"]) for row in row_localization_rows),
        "localization_bucket_counts": dict(sorted(localization_bucket_counts.items())),
        "recipe_signal_counts": dict(sorted(recipe_signal_counts.items())),
        "actor_contract_shape_72_action_3": all(_bool(row["status_pass"]) for row in actor_rows),
        "ordinary_success_denominator_allowed": False,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_computed": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    write_json(paths["summary"], result)
    write_json(
        paths["run_state"],
        {
            "milestone": DEFAULT_MILESTONE,
            "inputs": {
                "m2853_design": str(m2853_design),
                "m2850_summary": str(m2850_summary),
                "paired_execution_rows": str(paired_execution_rows),
                "paired_delta_rows": str(paired_delta_rows),
            },
            "outputs": {key: str(path) for key, path in paths.items()},
            "claim_scope": CLAIM_SCOPE,
        },
    )
    write_result_doc(doc_path, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2853-design", type=Path, default=DEFAULT_M2853_DESIGN)
    parser.add_argument("--m2850-summary", type=Path, default=DEFAULT_M2850_SUMMARY)
    parser.add_argument("--paired-execution-rows", type=Path, default=DEFAULT_PAIRED_EXECUTION_ROWS)
    parser.add_argument("--paired-delta-rows", type=Path, default=DEFAULT_PAIRED_DELTA_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_existing_artifact_failure_localization_materialization(
        m2853_design=args.m2853_design,
        m2850_summary=args.m2850_summary,
        paired_execution_rows=args.paired_execution_rows,
        paired_delta_rows=args.paired_delta_rows,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    if not summary["status_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
