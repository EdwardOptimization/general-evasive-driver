"""Synthesize/reprice the C1 warm-start branch after two action-MSE failures.

This script performs no training and no rollout. It reads the frozen C5-prime
pricing artifacts plus the M3228/M3229/M3232 C1 warm-start evidence and emits
a machine-readable M3233 synthesis decision.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from autodrift.artifacts import read_json, utc_timestamp, write_json  # noqa: E402


PREREG_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_synthesis_repricing_prereg.json"
M3228_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart.json"
M3229_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_failure_localization.json"
M3232_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart_v2_quick.json"
A3_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_target_consolidation.json"
D1B_JSON = REPO / "experiments" / "feasibility_audit" / "chrono_native_oracle_pricing.json"
OUTPUT_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_synthesis_repricing.json"

CLAIM_BOUNDARY = (
    "M3233 C1 synthesis/repricing only: reanalysis of existing C5-prime "
    "pricing and C1 warm-start artifacts. No new rollout, no training, no "
    "criterion relaxation, no driver mutation, no validation ranking, no "
    "promotion, no driver-performance claim, no high-fidelity sufficiency "
    "claim, and no self-ID claim."
)


def _round(value: float | int | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _path_text(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _gate_bool(gates: dict[str, Any], key: str) -> bool:
    return bool(gates.get(key, False))


def summarize_attempt(
    *,
    milestone: str,
    mode: str,
    revision: str,
    summary: dict[str, Any],
    action_mse_threshold: float,
) -> dict[str, Any]:
    """Extract comparable C1 warm-start readouts from a summary artifact."""

    bc = summary["bc_training"]
    gates = summary.get("gates", {})
    validation_mse = float(bc["validation_action_mse"])
    zero_baseline = float(bc["validation_zero_action_baseline_mse"])
    improvement_vs_zero = 1.0 - validation_mse / zero_baseline if zero_baseline > 0 else 0.0
    final = bc.get("final", {})
    validation_rollouts = bc.get("validation_bc_rollouts", [])
    success_count = sum(row.get("outcome_bucket") == "success_obstacle_pass" for row in validation_rollouts)
    return {
        "milestone": milestone,
        "mode": mode,
        "revision": revision,
        "quick_mode": bool(summary.get("quick_mode", False)),
        "role_counts": summary.get("role_counts", {}),
        "demo_frame_counts": summary.get("demo_frame_counts", {}),
        "selected_row_count": len(summary.get("selected_rows", [])),
        "validation_action_mse": _round(validation_mse),
        "action_mse_threshold": _round(action_mse_threshold),
        "validation_mse_gate_passed": bool(bc.get("validation_mse_gate_passed", False)),
        "zero_action_baseline_mse": _round(zero_baseline),
        "relative_improvement_vs_zero_baseline": _round(improvement_vs_zero),
        "selection_mse_at_selected_epoch": _round(final.get("best_selection_mse")),
        "train_mse_at_selected_epoch": _round(final.get("best_train_mse")),
        "selected_epoch": final.get("best_epoch"),
        "validation_rollout_success_count": int(success_count),
        "validation_rollout_count": int(len(validation_rollouts)),
        "validation_bc_success_rate_context": _round(
            bc.get("validation_bc_success_rate_context", 0.0),
            digits=4,
        ),
        "artifact_gates": {
            "demo_replay_all_success": _gate_bool(gates, "demo_replay_all_success"),
            "checkpoint_exists": _gate_bool(gates, "checkpoint_exists"),
            "dataset_exists": _gate_bool(gates, "dataset_exists"),
            "all_passed": _gate_bool(gates, "all_passed"),
        },
    }


def summarize_localization(localization: dict[str, Any]) -> dict[str, Any]:
    recomputed = localization.get("recomputed_mse", {})
    segment = recomputed.get("by_segment_frame_mse", {})
    channels = recomputed.get("by_action_channel_frame_mse", {})
    prefix = float(segment.get("validation:prefix", 0.0))
    tail = float(segment.get("validation:tail", 0.0))
    dominant_channel = max(channels, key=lambda key: float(channels[key])) if channels else None
    channel_total = sum(float(value) for value in channels.values()) if channels else 0.0
    return {
        "diagnosis_flags": localization.get("diagnosis_flags", []),
        "validation_prefix_mse": _round(prefix),
        "validation_tail_mse": _round(tail),
        "validation_tail_minus_prefix_mse": _round(tail - prefix),
        "validation_tail_prefix_ratio": _round(tail / prefix if prefix > 0 else None),
        "dominant_action_channel": dominant_channel,
        "dominant_action_channel_mse": _round(channels.get(dominant_channel) if dominant_channel else None),
        "dominant_action_channel_share": _round(
            float(channels[dominant_channel]) / channel_total
            if dominant_channel is not None and channel_total > 0
            else None
        ),
        "by_action_channel_frame_mse": channels,
        "by_level_frame_mse": recomputed.get("by_level_frame_mse", {}),
        "by_oracle_frame_mse": recomputed.get("by_oracle_frame_mse", {}),
    }


def summarize_a3_target(a3: dict[str, Any]) -> dict[str, Any]:
    decision = a3.get("c5prime_decision", {})
    cells = a3.get("cells", {})
    structural_gaps: dict[str, dict[str, Any]] = {}
    for cell, payload in sorted(cells.items()):
        gap = payload.get("readouts_unfiltered", {}).get("structural_gap_oracle_minus_pertuned")
        if gap is not None:
            structural_gaps[cell] = {
                "value": _round(gap.get("value")),
                "paired_bootstrap_ci95": gap.get("paired_bootstrap_ci95"),
            }
    qualifying = list(decision.get("qualifying_target_cells", []))
    qualified_values = [
        float(structural_gaps[cell]["value"])
        for cell in qualifying
        if cell in structural_gaps and structural_gaps[cell]["value"] is not None
    ]
    return {
        "c5prime_target_confirmed": bool(decision.get("c5prime_target_confirmed", False)),
        "qualifying_target_cells": qualifying,
        "qualified_cell_count": len(qualifying),
        "structural_gap_oracle_minus_pertuned": structural_gaps,
        "min_qualified_gap": _round(min(qualified_values) if qualified_values else None),
        "rule": decision.get("rule", ""),
    }


def summarize_d1b(d1b: dict[str, Any]) -> dict[str, Any]:
    per_vehicle = d1b.get("per_vehicle", {})
    variants = {}
    for variant, payload in sorted(per_vehicle.items()):
        variants[variant] = {
            "direction_delta_native_oracle_minus_pertuned": _round(
                payload.get("direction_delta_native_oracle_minus_pertuned")
            ),
            "direction_verdict": payload.get("direction_verdict"),
            "arm_success_counts": payload.get("arm_success_counts", {}),
            "arm_n": payload.get("arm_n", {}),
            "candidate_attempts": payload.get("candidate_attempts"),
        }
    return {
        "d1b_direction_positive_all_variants": bool(
            d1b.get("decision", {}).get("d1b_direction_positive_all_variants", False)
        ),
        "variant_verdicts": variants,
        "absolute_numbers_are_claims": bool(d1b.get("decision", {}).get("absolute_numbers_are_claims", True)),
    }


def synthesize_decision(
    prereg: dict[str, Any],
    attempts: list[dict[str, Any]],
    localization: dict[str, Any],
    a3_summary: dict[str, Any],
    d1b_summary: dict[str, Any],
) -> dict[str, Any]:
    thresholds = prereg["thresholds"]
    failed_action_mse_count = sum(not attempt["validation_mse_gate_passed"] for attempt in attempts)
    artifacts_healthy = all(
        attempt["artifact_gates"]["demo_replay_all_success"]
        and attempt["artifact_gates"]["checkpoint_exists"]
        and attempt["artifact_gates"]["dataset_exists"]
        for attempt in attempts
    )
    first_mse = float(attempts[0]["validation_action_mse"])
    latest_mse = float(attempts[-1]["validation_action_mse"])
    validation_mse_improvement = first_mse - latest_mse
    target_still_priced = bool(a3_summary["c5prime_target_confirmed"]) and bool(
        d1b_summary["d1b_direction_positive_all_variants"]
    )
    tail_dominates = "tail_action_generalization_dominates" in localization.get("diagnosis_flags", [])
    local_branch_pivots = (
        failed_action_mse_count >= int(thresholds["max_action_mse_gate_failures_before_synthesis"])
        and artifacts_healthy
        and validation_mse_improvement < float(thresholds["minimum_validation_mse_improvement_for_local_repair"])
        and tail_dominates
    )

    if not target_still_priced:
        synthesis_decision = "stop"
        next_branch = None
        recommended_next = "Stop Track C until the C5-prime target is re-priced."
    elif local_branch_pivots:
        synthesis_decision = "pivot"
        next_branch = "c5prime_track_c_c1_admission_interface_pricing"
        recommended_next = (
            "Register a C1b process/pricing milestone for admission-interface design before any "
            "new warm-start training: keep the priced C5-prime target, but compare a new "
            "tail-action-family or mixture interface against the direct MLP action-MSE floor "
            "with frozen criteria."
        )
    else:
        synthesis_decision = "continue"
        next_branch = "c5prime_track_c_c1_warmstart"
        recommended_next = "Continue C1 only under a newly pre-registered design."

    return {
        "synthesis_decision": synthesis_decision,
        "closed_branch": "c5prime_track_c_c1_warmstart" if synthesis_decision == "pivot" else None,
        "next_branch": next_branch,
        "c1_status": "open" if target_still_priced else "blocked_pending_repricing",
        "c2_admitted": False,
        "c3_admitted": False,
        "full_v2_admitted": False,
        "another_local_mlp_bc_repair_admitted": False if local_branch_pivots else None,
        "target_still_priced": target_still_priced,
        "local_branch_pivots": local_branch_pivots,
        "failed_action_mse_gate_count": failed_action_mse_count,
        "artifact_path_healthy": artifacts_healthy,
        "validation_mse_improvement_m3228_minus_m3232": _round(validation_mse_improvement),
        "minimum_improvement_for_local_repair": thresholds["minimum_validation_mse_improvement_for_local_repair"],
        "recommended_next": recommended_next,
        "reason": (
            "A3 and D1b keep the C5-prime structural target priced, but two C1 direct "
            "MLP/action-MSE warm-start attempts failed the unchanged gate; the v2 quick "
            "attempt worsened validation MSE while artifact and demo gates stayed healthy, "
            "and M3229 localized the error to validation tail actions."
        ),
    }


def build_payload(
    prereg: dict[str, Any],
    m3228: dict[str, Any],
    m3229: dict[str, Any],
    m3232: dict[str, Any],
    a3: dict[str, Any],
    d1b: dict[str, Any],
) -> dict[str, Any]:
    threshold = float(prereg["thresholds"]["validation_action_mse_gate"])
    attempts = [
        summarize_attempt(
            milestone="M3228",
            mode="full",
            revision="v1_structured_oracle_bc",
            summary=m3228,
            action_mse_threshold=threshold,
        ),
        summarize_attempt(
            milestone="M3232",
            mode="quick",
            revision="v2_tail_balanced",
            summary=m3232,
            action_mse_threshold=threshold,
        ),
    ]
    localization = summarize_localization(m3229)
    a3_summary = summarize_a3_target(a3)
    d1b_summary = summarize_d1b(d1b)
    decision = synthesize_decision(prereg, attempts, localization, a3_summary, d1b_summary)
    return {
        "protocol": "c5prime_c1_synthesis_repricing",
        "generated_by": "scripts/feasibility_audit/c5prime_c1_synthesis_repricing.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": _path_text(PREREG_JSON),
        "source_artifacts": prereg["source_artifacts"],
        "measured": {
            "priced_target": {
                "a3_current_sim": a3_summary,
                "d1b_chrono_native_direction": d1b_summary,
            },
            "warmstart_attempts": attempts,
            "failure_localization": localization,
        },
        "inferred": {
            "action_mse_gate_context": (
                "The rollout success contexts are informative but cannot override the frozen "
                "action-MSE gate; no replacement gate is priced in this milestone."
            ),
            "failure_mode": (
                "Direct MLP imitation learns prefix/selection behavior but does not generalize "
                "the held-out tail action families at the current admission gate."
            ),
        },
        "decision": decision,
    }


def run() -> dict[str, Any]:
    t0 = time.time()
    prereg = read_json(PREREG_JSON)
    for artifact in prereg["source_artifacts"].values():
        artifact_path = REPO / artifact if not Path(artifact).is_absolute() else Path(artifact)
        if not artifact_path.exists():
            raise FileNotFoundError(artifact_path)
    payload = build_payload(
        prereg=prereg,
        m3228=read_json(M3228_JSON),
        m3229=read_json(M3229_JSON),
        m3232=read_json(M3232_JSON),
        a3=read_json(A3_JSON),
        d1b=read_json(D1B_JSON),
    )
    payload["elapsed_s"] = _round(time.time() - t0, digits=3)
    write_json(OUTPUT_JSON, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    payload = run()
    decision = payload["decision"]
    print(
        f"wrote {_path_text(OUTPUT_JSON)} decision={decision['synthesis_decision']} "
        f"c1_status={decision['c1_status']} c2_admitted={decision['c2_admitted']}"
    )


if __name__ == "__main__":
    main()
