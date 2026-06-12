"""Price the next C1 admission interface after the M3233 pivot.

This is a read-only pricing pass over existing C1 artifacts. It does not run
rollouts, train a model, write checkpoints, or admit C2. The goal is to decide
whether a structured tail-family interface is worth a separate quick smoke
before any new C1 warm-start training.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from autodrift.artifacts import read_json, utc_timestamp, write_json  # noqa: E402


PREREG_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_admission_interface_pricing_prereg.json"
OUTPUT_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_admission_interface_pricing.json"
M3228_PREREG = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_prereg.json"
M3232_PREREG = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_v2_prereg.json"
M3228_SUMMARY = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart.json"
M3229_LOCALIZATION = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_failure_localization.json"
M3232_SUMMARY = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart_v2_quick.json"
M3233_SYNTHESIS = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_synthesis_repricing.json"

CLAIM_BOUNDARY = (
    "M3234 C1 admission-interface pricing only: read-only analysis of existing "
    "structured-oracle labels, failed direct-MLP warm-start artifacts, and M3233 "
    "synthesis. No rollout, no training, no checkpoint, no dataset, no incumbent "
    "mutation, no C2 admission, no driver-performance claim, no validation "
    "ranking, no promotion, no high-fidelity sufficiency claim, and no self-ID "
    "claim."
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


def _is_supported_structured_family(oracle_by: str) -> bool:
    name = oracle_by.removeprefix("structured:")
    if name == "full_brake":
        return True
    if re.fullmatch(r"brake_steer_[+-]\d(?:\.\d)?", name):
        return True
    if re.fullmatch(r"coast_steer_[+-]\d(?:\.\d)?", name):
        return True
    if re.fullmatch(r"swerve_[+-]\d_n\d+", name):
        return True
    return False


def family_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train = {str(row["oracle_by"]) for row in rows if row.get("bc_role") == "train"}
    heldout = {
        str(row["oracle_by"])
        for row in rows
        if row.get("bc_role") in {"selection", "validation"}
    }
    missing = sorted(heldout - train)
    supported = sorted({str(row["oracle_by"]) for row in rows if _is_supported_structured_family(str(row["oracle_by"]))})
    unsupported = sorted({str(row["oracle_by"]) for row in rows if not _is_supported_structured_family(str(row["oracle_by"]))})
    return {
        "train_families": sorted(train),
        "heldout_families": sorted(heldout),
        "heldout_family_count": len(heldout),
        "missing_train_support_for_heldout": missing,
        "heldout_family_train_coverage": _round((len(heldout) - len(missing)) / len(heldout) if heldout else 1.0),
        "supported_structured_families": supported,
        "unsupported_structured_families": unsupported,
        "all_families_supported_by_structured_library": len(unsupported) == 0,
    }


def tail_frame_summary(prereg: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    prereg_rows = {str(row["row_id"]): row for row in prereg.get("selected_rows", [])}
    demo_outcomes = summary.get("demo_outcomes", {})
    by_role = defaultdict(int)
    by_family = defaultdict(int)
    total = Counter()
    row_records: list[dict[str, Any]] = []
    for row_id, outcome in sorted(demo_outcomes.items()):
        row = prereg_rows[row_id]
        role = str(outcome["role"])
        family = str(row["oracle_by"])
        steps = int(outcome["steps"])
        reveal_step = int(row["reveal_step"])
        prefix_frames = min(steps, reveal_step)
        tail_frames = max(0, steps - reveal_step)
        total["rows"] += 1
        total["frames"] += steps
        total["prefix_frames"] += prefix_frames
        total["tail_frames"] += tail_frames
        by_role[role] += tail_frames
        by_family[family] += tail_frames
        row_records.append(
            {
                "row_id": row_id,
                "role": role,
                "oracle_by": family,
                "steps": steps,
                "reveal_step": reveal_step,
                "prefix_frames": prefix_frames,
                "tail_frames": tail_frames,
            }
        )
    return {
        "rows": int(total["rows"]),
        "frames": int(total["frames"]),
        "prefix_frames": int(total["prefix_frames"]),
        "tail_frames": int(total["tail_frames"]),
        "tail_frame_share": _round(total["tail_frames"] / total["frames"] if total["frames"] else 0.0),
        "tail_frames_by_role": dict(sorted(by_role.items())),
        "tail_frames_by_family": dict(sorted(by_family.items())),
        "row_records": row_records,
    }


def build_interface_price(
    prereg: dict[str, Any],
    m3228: dict[str, Any],
    m3229: dict[str, Any],
    m3232: dict[str, Any],
    m3233: dict[str, Any],
    v2_coverage: dict[str, Any],
) -> dict[str, Any]:
    thresholds = prereg["thresholds"]
    localization = m3229["recomputed_mse"]["by_segment_frame_mse"]
    direct_tail_mse = float(localization["validation:tail"])
    oracle_tail_mse = 0.0
    tail_mse_reduction = direct_tail_mse - oracle_tail_mse
    m3228_val = float(m3228["bc_training"]["validation_action_mse"])
    m3232_val = float(m3232["bc_training"]["validation_action_mse"])
    direct_floor = max(m3228_val, m3232_val)
    target_still_priced = bool(m3233["decision"]["target_still_priced"])
    branch_pivoted = bool(m3233["decision"]["local_branch_pivots"])
    coverage = float(v2_coverage["heldout_family_train_coverage"])
    no_unsupported = bool(v2_coverage["all_families_supported_by_structured_library"])
    positive = (
        target_still_priced
        and branch_pivoted
        and tail_mse_reduction >= float(thresholds["min_tail_mse_reduction"])
        and coverage >= float(thresholds["min_heldout_family_train_coverage"])
        and no_unsupported
        and direct_floor > float(thresholds["direct_action_mse_gate"])
    )
    return {
        "candidate_interface": "tail_family_conditioned_structured_action",
        "target_schema": {
            "prefix": "continuous action or existing reflex-prefix head before reveal_step",
            "tail": "discrete structured oracle family plus reveal-relative phase, decoded through the frozen structured action library",
            "admission_gate_to_price_next": (
                "family-conditioned tail-action reconstruction/action-MSE gate; outcome context remains non-admission"
            ),
        },
        "direct_action_mse_floor": {
            "m3228_full_validation_action_mse": _round(m3228_val),
            "m3232_v2_quick_validation_action_mse": _round(m3232_val),
            "floor_value": _round(direct_floor),
            "gate": thresholds["direct_action_mse_gate"],
        },
        "tail_interface_oracle_anchor": {
            "direct_mlp_validation_tail_mse": _round(direct_tail_mse),
            "structured_tail_family_oracle_mse": _round(oracle_tail_mse),
            "priced_tail_mse_reduction": _round(tail_mse_reduction),
            "threshold": thresholds["min_tail_mse_reduction"],
        },
        "coverage_gate": {
            "heldout_family_train_coverage": _round(coverage),
            "threshold": thresholds["min_heldout_family_train_coverage"],
            "missing_train_support_for_heldout": v2_coverage["missing_train_support_for_heldout"],
            "unsupported_structured_families": v2_coverage["unsupported_structured_families"],
        },
        "verdict": "interface_pricing_positive" if positive else "interface_pricing_negative",
        "positive": positive,
    }


def build_payload() -> dict[str, Any]:
    prereg = read_json(PREREG_JSON)
    m3228_prereg = read_json(M3228_PREREG)
    m3232_prereg = read_json(M3232_PREREG)
    m3228 = read_json(M3228_SUMMARY)
    m3229 = read_json(M3229_LOCALIZATION)
    m3232 = read_json(M3232_SUMMARY)
    m3233 = read_json(M3233_SYNTHESIS)
    m3228_coverage = family_coverage(m3228_prereg["selected_rows"])
    m3232_coverage = family_coverage(m3232_prereg["selected_rows"])
    m3228_tail = tail_frame_summary(m3228_prereg, m3228)
    m3232_tail = tail_frame_summary(m3232_prereg, m3232)
    price = build_interface_price(prereg, m3228, m3229, m3232, m3233, m3232_coverage)
    decision = {
        "c1_status": "open",
        "c2_admitted": False,
        "c3_admitted": False,
        "next_branch": (
            "c5prime_track_c_c1_tail_family_interface_smoke"
            if price["positive"]
            else "c5prime_track_c_c1_admission_interface_reprice"
        ),
        "next_training_admitted": False,
        "next_process_admitted": price["positive"],
        "recommended_next": (
            "Register a no-PPO C1 tail-family interface quick smoke with frozen family-coverage "
            "and tail-reconstruction gates before any full C1 training."
            if price["positive"]
            else "Do not train; re-price a different C1 admission interface or stop Track C."
        ),
        "reason": (
            "The direct MLP/action-MSE floor failed twice, while the structured tail-family "
            "oracle can represent the localized validation tail exactly and the v2 prereg "
            "contains train support for all held-out oracle families."
        ),
    }
    return {
        "protocol": "c5prime_c1_admission_interface_pricing",
        "generated_by": "scripts/feasibility_audit/c5prime_c1_admission_interface_pricing.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": _path_text(PREREG_JSON),
        "source_artifacts": prereg["source_artifacts"],
        "measured": {
            "m3233_decision": m3233["decision"],
            "m3228_family_coverage": m3228_coverage,
            "m3232_v2_family_coverage": m3232_coverage,
            "m3228_tail_frames": m3228_tail,
            "m3232_v2_quick_tail_frames": m3232_tail,
            "m3229_failure_localization": {
                "validation_prefix_mse": m3229["recomputed_mse"]["by_segment_frame_mse"]["validation:prefix"],
                "validation_tail_mse": m3229["recomputed_mse"]["by_segment_frame_mse"]["validation:tail"],
                "dominant_action_channel_mse": m3229["recomputed_mse"]["by_action_channel_frame_mse"],
                "diagnosis_flags": m3229["diagnosis_flags"],
            },
        },
        "priced_interface": price,
        "inferred": {
            "interpretation": (
                "The positive price is an admission-interface price, not a trained policy result. "
                "It says the next C1 smoke should test a structured tail-family interface rather "
                "than continue local direct-MLP action regression."
            )
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
    payload = build_payload()
    payload["elapsed_s"] = _round(time.time() - t0, digits=3)
    write_json(OUTPUT_JSON, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    payload = run()
    print(
        f"wrote {_path_text(OUTPUT_JSON)} verdict={payload['priced_interface']['verdict']} "
        f"next={payload['decision']['next_branch']}"
    )


if __name__ == "__main__":
    main()
