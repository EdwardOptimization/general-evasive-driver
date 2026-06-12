"""Synthesize/reprice the C1 tail-family interface after M3236.

This script performs no rollout and no training. It reads M3234-M3236 plus the
C5-prime target-pricing artifacts and decides whether the local tail-family
interface pretraining branch can continue, must pivot, or should stop.
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


PREREG_JSON = (
    REPO
    / "experiments"
    / "feasibility_audit"
    / "c5prime_c1_tail_family_interface_synthesis_repricing_prereg.json"
)
OUTPUT_JSON = (
    REPO
    / "experiments"
    / "feasibility_audit"
    / "c5prime_c1_tail_family_interface_synthesis_repricing.json"
)
M3234_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_admission_interface_pricing.json"
M3235_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_tail_family_interface_smoke.json"
M3236_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_tail_family_interface_pretrain_quick.json"
A3_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_target_consolidation.json"
D1B_JSON = REPO / "experiments" / "feasibility_audit" / "chrono_native_oracle_pricing.json"

CLAIM_BOUNDARY = (
    "M3237 C1 tail-family interface synthesis/repricing only: read-only "
    "analysis of M3234-M3236 and existing C5-prime pricing artifacts. No new "
    "rollout, no training, no checkpoint, no incumbent mutation, no validation "
    "ranking, no driver-performance claim, no high-fidelity sufficiency claim, "
    "no C2 admission, and no self-ID claim."
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


def summarize_target_status(m3234: dict[str, Any], a3: dict[str, Any], d1b: dict[str, Any]) -> dict[str, Any]:
    priced = m3234["priced_interface"]
    a3_decision = a3.get("c5prime_decision", {})
    d1b_decision = d1b.get("decision", {})
    return {
        "a3_c5prime_target_confirmed": bool(a3_decision.get("c5prime_target_confirmed", False)),
        "a3_qualifying_target_cells": a3_decision.get("qualifying_target_cells", []),
        "d1b_direction_positive_all_variants": bool(
            d1b_decision.get("d1b_direction_positive_all_variants", False)
        ),
        "m3234_interface_pricing_positive": bool(priced.get("positive", False)),
        "m3234_priced_tail_mse_reduction": _round(
            priced.get("tail_interface_oracle_anchor", {}).get("priced_tail_mse_reduction")
        ),
        "m3234_tail_mse_reduction_threshold": priced.get("tail_interface_oracle_anchor", {}).get("threshold"),
        "heldout_family_train_coverage": _round(
            priced.get("coverage_gate", {}).get("heldout_family_train_coverage")
        ),
    }


def summarize_representation_status(m3235: dict[str, Any], m3236: dict[str, Any]) -> dict[str, Any]:
    return {
        "m3235_target_path_smoke_passed": bool(m3235.get("gates", {}).get("all_passed", False)),
        "m3235_tail_reconstruction_mse": _round(
            m3235.get("interface_targets", {}).get("tail_reconstruction_mse"),
            digits=12,
        ),
        "m3235_tail_frames": int(m3235.get("interface_targets", {}).get("tail_frames", 0)),
        "m3236_true_family_validation_reconstruction_mse": _round(
            m3236.get("metrics", {}).get("validation_true_family_reconstruction_mse"),
            digits=12,
        ),
        "m3236_predicted_family_validation_reconstruction_mse": _round(
            m3236.get("metrics", {}).get("validation_predicted_family_reconstruction_mse")
        ),
        "representationally_valid_if_family_known": (
            bool(m3235.get("gates", {}).get("all_passed", False))
            and float(m3236.get("metrics", {}).get("validation_true_family_reconstruction_mse", 1.0)) == 0.0
        ),
    }


def summarize_pretrain_failure(m3236: dict[str, Any]) -> dict[str, Any]:
    metrics = m3236["metrics"]
    floors = metrics["floors"]
    validation_floor = max(
        float(floors["validation_train_majority_accuracy"]),
        float(floors["validation_centroid_accuracy"]),
    )
    validation_accuracy = float(metrics["accuracy_by_role"]["validation"])
    family_metrics = metrics["validation_family_metrics"]
    worst_family = min(family_metrics, key=lambda family: float(family_metrics[family]["accuracy"]))
    failed_gates = sorted(key for key, value in m3236["gates"].items() if not value)
    return {
        "quick_pretrain_passed": bool(m3236["decision"]["quick_pretrain_passed"]),
        "failed_gates": failed_gates,
        "selection_accuracy": _round(metrics["accuracy_by_role"]["selection"]),
        "validation_accuracy": _round(validation_accuracy),
        "validation_best_simple_floor": _round(validation_floor),
        "validation_accuracy_over_best_floor": _round(validation_accuracy - validation_floor),
        "aggregate_validation_would_mislead": (
            validation_accuracy - validation_floor >= 0.15
            and not bool(m3236["gates"]["validation_family_min_gate_passed"])
        ),
        "worst_validation_family": worst_family,
        "worst_validation_family_accuracy": _round(family_metrics[worst_family]["accuracy"]),
        "worst_validation_family_frames": int(family_metrics[worst_family]["frames"]),
        "worst_validation_family_predicted_counts": family_metrics[worst_family]["predicted_counts"],
        "validation_family_metrics": family_metrics,
    }


def synthesize_decision(
    prereg: dict[str, Any],
    target_status: dict[str, Any],
    representation: dict[str, Any],
    pretrain: dict[str, Any],
) -> dict[str, Any]:
    thresholds = prereg["thresholds"]
    target_still_priced = (
        target_status["a3_c5prime_target_confirmed"]
        and target_status["d1b_direction_positive_all_variants"]
        and target_status["m3234_interface_pricing_positive"]
        and float(target_status["m3234_priced_tail_mse_reduction"]) >= float(thresholds["min_priced_tail_mse_reduction"])
    )
    representation_alive = (
        representation["representationally_valid_if_family_known"]
        and float(representation["m3236_true_family_validation_reconstruction_mse"])
        <= float(thresholds["max_true_family_reconstruction_mse"])
    )
    local_pretrain_failed = (
        not pretrain["quick_pretrain_passed"]
        and float(pretrain["worst_validation_family_accuracy"])
        < float(thresholds["min_required_rare_validation_family_accuracy"])
        and "predicted_family_reconstruction_gate_passed" in pretrain["failed_gates"]
    )
    aggregate_masked_failure = bool(pretrain["aggregate_validation_would_mislead"])

    if not target_still_priced:
        synthesis_decision = "stop_track_c_pending_target_reprice"
        next_branch = "c5prime_track_c_target_reprice"
        recommended_next = "Re-price the C5-prime target before any C1 work."
    elif representation_alive and local_pretrain_failed:
        synthesis_decision = "pivot_to_family_selector_repricing"
        next_branch = "c5prime_track_c_c1_family_selector_repricing"
        recommended_next = (
            "Register a read-only family-selector/separability repricing milestone. "
            "Do not continue local frame-wise interface pretraining or controlled "
            "rollout design until that pricing says the rare-family selector is "
            "learnable and worth training."
        )
    elif representation_alive:
        synthesis_decision = "continue_with_new_preregistration"
        next_branch = "c5prime_track_c_c1_tail_family_interface_controlled_rollout_design"
        recommended_next = "Register a controlled rollout design/quick milestone; C2 remains blocked."
    else:
        synthesis_decision = "stop_interface_branch"
        next_branch = "c5prime_track_c_c1_reprice"
        recommended_next = "Stop the tail-family interface branch and re-price C1 from the A3/D1b target."

    return {
        "synthesis_decision": synthesis_decision,
        "closed_branch": (
            "c5prime_track_c_c1_tail_family_interface_pretrain_design"
            if local_pretrain_failed
            else None
        ),
        "next_branch": next_branch,
        "c1_status": "open" if target_still_priced else "blocked_pending_target_reprice",
        "c2_admitted": False,
        "c3_admitted": False,
        "target_still_priced": target_still_priced,
        "representation_alive_if_family_known": representation_alive,
        "local_framewise_pretraining_closed": local_pretrain_failed,
        "aggregate_metric_masked_rare_family_failure": aggregate_masked_failure,
        "next_process_admitted": synthesis_decision == "pivot_to_family_selector_repricing",
        "next_training_admitted": False,
        "controlled_rollout_design_admitted": False,
        "more_local_interface_pretraining_admitted": False if local_pretrain_failed else None,
        "recommended_next": recommended_next,
        "reason": (
            "M3234/M3235 show the structured tail-family interface can represent the tail "
            "target, and A3/D1b keep the C5-prime prize priced. M3236 shows the local "
            "frame-wise supervised selector is not sufficient: aggregate validation accuracy "
            "beats simple floors, but a rare coast-steer family collapses and the decoded "
            "predicted-family action fails reconstruction."
        ),
    }


def run() -> dict[str, Any]:
    t0 = time.time()
    prereg = read_json(PREREG_JSON)
    for artifact in prereg["source_artifacts"].values():
        artifact_path = REPO / artifact if not Path(artifact).is_absolute() else Path(artifact)
        if not artifact_path.exists():
            raise FileNotFoundError(artifact_path)
    m3234 = read_json(M3234_JSON)
    m3235 = read_json(M3235_JSON)
    m3236 = read_json(M3236_JSON)
    a3 = read_json(A3_JSON)
    d1b = read_json(D1B_JSON)
    target_status = summarize_target_status(m3234, a3, d1b)
    representation = summarize_representation_status(m3235, m3236)
    pretrain = summarize_pretrain_failure(m3236)
    decision = synthesize_decision(prereg, target_status, representation, pretrain)
    payload = {
        "protocol": "c5prime_c1_tail_family_interface_synthesis_repricing",
        "generated_by": "scripts/feasibility_audit/c5prime_c1_tail_family_interface_synthesis_repricing.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": _path_text(PREREG_JSON),
        "source_artifacts": prereg["source_artifacts"],
        "measured": {
            "target_status": target_status,
            "representation_status": representation,
            "pretrain_failure": pretrain,
        },
        "inferred": {
            "representation_vs_learning": (
                "The structured decoder remains exact when the family is known; the failed "
                "component is the local frame-wise family selector, not the representation itself."
            ),
            "aggregate_metric_warning": (
                "Aggregate validation accuracy is not a safe admission criterion here because it "
                "can pass while a required rare family fails completely."
            ),
        },
        "decision": decision,
        "elapsed_s": _round(time.time() - t0, digits=3),
    }
    write_json(OUTPUT_JSON, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    payload = run()
    decision = payload["decision"]
    print(
        f"wrote {_path_text(OUTPUT_JSON)} decision={decision['synthesis_decision']} "
        f"next_branch={decision['next_branch']} c2_admitted={decision['c2_admitted']}"
    )


if __name__ == "__main__":
    main()
