"""Smoke the C1 structured tail-family admission interface.

This is a no-PPO interface smoke after M3234 priced the tail-family interface
positive. It replays the frozen v2 quick rows through the structured oracle,
encodes prefix/tail interface targets, and checks family coverage plus exact
tail reconstruction. It does not train a policy or write a policy checkpoint.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5prime_c1_admission_interface_pricing as pricing  # noqa: E402
import c5prime_c1_oracle_bc_warmstart as c1  # noqa: E402
from autodrift.artifacts import write_json, utc_timestamp  # noqa: E402


PREREG_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_tail_family_interface_smoke_prereg.json"
OUTPUT_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_tail_family_interface_smoke.json"
RUN_DIR = REPO / "runs" / "feasibility_audit" / "c5prime_c1_tail_family_interface_smoke" / "quick"
TARGETS_NPZ = RUN_DIR / "interface_targets.npz"
M3234_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_admission_interface_pricing.json"

CLAIM_BOUNDARY = (
    "M3235 C1 tail-family interface quick smoke only: structured-oracle demo "
    "replay and interface target encoding. No PPO, no behavior pretraining, no "
    "policy checkpoint, no incumbent mutation, no validation ranking, no C2 "
    "admission, no driver-performance claim, no high-fidelity sufficiency claim, "
    "and no self-ID claim."
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


def _role_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row["bc_role"]) for row in rows)
    return {role: int(counts.get(role, 0)) for role in ("train", "selection", "validation")}


def _family_vocab(rows: list[dict[str, Any]]) -> tuple[list[str], dict[str, int]]:
    families = sorted({str(row["oracle_by"]) for row in rows})
    return families, {family: idx for idx, family in enumerate(families)}


def encode_interface_targets(
    demos: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Encode prefix/tail interface targets and verify tail reconstruction."""

    row_by_id = {str(row["row_id"]): row for row in selected_rows}
    family_names, family_to_id = _family_vocab(selected_rows)
    obs_parts: list[np.ndarray] = []
    action_parts: list[np.ndarray] = []
    decoded_parts: list[np.ndarray] = []
    tail_mask_parts: list[np.ndarray] = []
    family_id_parts: list[np.ndarray] = []
    phase_parts: list[np.ndarray] = []
    role_parts: list[np.ndarray] = []
    row_id_parts: list[np.ndarray] = []
    per_row: list[dict[str, Any]] = []

    role_to_id = {"train": 0, "selection": 1, "validation": 2}
    for row_index, demo in enumerate(demos):
        row = row_by_id[str(demo["row_id"])]
        obs = np.asarray(demo["obs"], dtype=np.float32)
        actions = np.asarray(demo["actions"], dtype=np.float32)
        reveal_step = int(row["reveal_step"])
        oracle_by = str(row["oracle_by"])
        role = str(row["bc_role"])
        decoded = actions.copy()
        tail_mask = np.zeros((len(actions),), dtype=bool)
        family_ids = np.full((len(actions),), -1, dtype=np.int16)
        phases = np.full((len(actions),), -1, dtype=np.int16)
        for step in range(len(actions)):
            if step < reveal_step:
                continue
            rel_step = step - reveal_step
            tail_mask[step] = True
            family_ids[step] = family_to_id[oracle_by]
            phases[step] = rel_step
            decoded[step] = c1.structured_tail_action(oracle_by, rel_step)
        error = decoded[tail_mask] - actions[tail_mask]
        tail_mse = float(np.mean(np.square(error))) if np.any(tail_mask) else 0.0
        max_abs_error = float(np.max(np.abs(error))) if np.any(tail_mask) else 0.0
        per_row.append(
            {
                "row_id": row["row_id"],
                "role": role,
                "oracle_by": oracle_by,
                "steps": int(len(actions)),
                "reveal_step": reveal_step,
                "tail_frames": int(np.sum(tail_mask)),
                "tail_reconstruction_mse": _round(tail_mse, digits=12),
                "tail_max_abs_error": _round(max_abs_error, digits=12),
            }
        )
        obs_parts.append(obs)
        action_parts.append(actions)
        decoded_parts.append(decoded)
        tail_mask_parts.append(tail_mask.astype(np.int8))
        family_id_parts.append(family_ids)
        phase_parts.append(phases)
        role_parts.append(np.full((len(actions),), role_to_id[role], dtype=np.int8))
        row_id_parts.append(np.full((len(actions),), row_index, dtype=np.int16))

    obs_all = np.concatenate(obs_parts, axis=0)
    actions_all = np.concatenate(action_parts, axis=0)
    decoded_all = np.concatenate(decoded_parts, axis=0)
    tail_mask_all = np.concatenate(tail_mask_parts, axis=0).astype(bool)
    family_id_all = np.concatenate(family_id_parts, axis=0)
    phase_all = np.concatenate(phase_parts, axis=0)
    role_all = np.concatenate(role_parts, axis=0)
    row_id_all = np.concatenate(row_id_parts, axis=0)
    tail_error = decoded_all[tail_mask_all] - actions_all[tail_mask_all]
    tail_mse = float(np.mean(np.square(tail_error))) if np.any(tail_mask_all) else 0.0
    max_abs_error = float(np.max(np.abs(tail_error))) if np.any(tail_mask_all) else 0.0
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        TARGETS_NPZ,
        obs=obs_all.astype(np.float32),
        oracle_actions=actions_all.astype(np.float32),
        decoded_actions=decoded_all.astype(np.float32),
        tail_mask=tail_mask_all.astype(np.int8),
        family_id=family_id_all.astype(np.int16),
        tail_phase=phase_all.astype(np.int16),
        role_id=role_all.astype(np.int8),
        row_id=row_id_all.astype(np.int16),
        family_names=np.asarray(family_names),
    )
    return {
        "artifact": _path_text(TARGETS_NPZ),
        "family_names": family_names,
        "frames": int(len(obs_all)),
        "tail_frames": int(np.sum(tail_mask_all)),
        "tail_frame_share": _round(np.mean(tail_mask_all)),
        "tail_reconstruction_mse": _round(tail_mse, digits=12),
        "tail_max_abs_error": _round(max_abs_error, digits=12),
        "per_row": per_row,
    }


def run() -> dict[str, Any]:
    t0 = time.time()
    prereg = pricing.read_json(PREREG_JSON)
    m3234 = pricing.read_json(M3234_JSON)
    c1_prereg = c1.load_preregistration(revision=c1.REVISION_V2)
    selected_rows = c1._rows_for_mode(c1_prereg, quick=True)
    source_rows = c1._source_row_by_id()
    fixed_cfg = c1._fixed_star_cfg()
    demos = [c1.rollout_oracle_demo(source_rows[row["row_id"]], row, fixed_cfg) for row in selected_rows]
    demo_success = all(demo["outcome_bucket"] == "success_obstacle_pass" for demo in demos)
    family_coverage = pricing.family_coverage(c1_prereg["selected_rows"])
    encoded = encode_interface_targets(demos, selected_rows)
    rare_required = set(prereg["required_validation_probe_families"])
    validation_families = {
        str(row["oracle_by"])
        for row in selected_rows
        if row["bc_role"] == "validation"
    }
    gates = {
        "m3234_interface_pricing_positive": bool(m3234["priced_interface"]["positive"]),
        "demo_replay_all_success": demo_success,
        "heldout_family_train_coverage_passed": (
            float(family_coverage["heldout_family_train_coverage"])
            >= float(prereg["thresholds"]["min_heldout_family_train_coverage"])
        ),
        "all_structured_families_supported": bool(family_coverage["all_families_supported_by_structured_library"]),
        "required_validation_probes_present": rare_required <= validation_families,
        "tail_reconstruction_mse_passed": (
            float(encoded["tail_reconstruction_mse"]) <= float(prereg["thresholds"]["max_tail_reconstruction_mse"])
        ),
        "tail_max_abs_error_passed": (
            float(encoded["tail_max_abs_error"]) <= float(prereg["thresholds"]["max_tail_abs_error"])
        ),
        "tail_frames_gate_passed": int(encoded["tail_frames"]) >= int(prereg["thresholds"]["min_tail_frames"]),
        "interface_target_artifact_exists": TARGETS_NPZ.exists(),
        "no_policy_checkpoint_written": not any(RUN_DIR.rglob("*.pt")),
    }
    gates["all_passed"] = all(gates.values())
    decision = {
        "c1_status": "open",
        "c2_admitted": False,
        "c3_admitted": False,
        "quick_smoke_passed": bool(gates["all_passed"]),
        "next_training_admitted": False,
        "next_branch": (
            "c5prime_track_c_c1_tail_family_interface_pretrain_design"
            if gates["all_passed"]
            else "c5prime_track_c_c1_tail_family_interface_reprice"
        ),
        "recommended_next": (
            "Register a tail-family interface pretrain design/quick milestone with frozen "
            "family classification and tail reconstruction criteria; do not admit C2."
            if gates["all_passed"]
            else "Do not train; re-price or redesign the C1 admission interface."
        ),
    }
    payload = {
        "protocol": "c5prime_c1_tail_family_interface_smoke",
        "generated_by": "scripts/feasibility_audit/c5prime_c1_tail_family_interface_smoke.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": _path_text(PREREG_JSON),
        "source_artifacts": prereg["source_artifacts"],
        "selected_rows": [
            {
                "row_id": row["row_id"],
                "role": row["bc_role"],
                "oracle_by": row["oracle_by"],
                "selection_source": row.get("selection_source", ""),
                "reveal_step": int(row["reveal_step"]),
            }
            for row in selected_rows
        ],
        "role_counts": _role_counts(selected_rows),
        "family_coverage": family_coverage,
        "interface_targets": encoded,
        "demo_outcomes": {
            demo["row_id"]: {
                "role": demo["role"],
                "oracle_by": demo["oracle_by"],
                "outcome_bucket": demo["outcome_bucket"],
                "steps": int(demo["steps"]),
            }
            for demo in demos
        },
        "gates": gates,
        "decision": decision,
        "elapsed_s": _round(time.time() - t0, digits=3),
    }
    write_json(OUTPUT_JSON, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    payload = run()
    print(
        f"wrote {_path_text(OUTPUT_JSON)} all_passed={payload['gates']['all_passed']} "
        f"tail_mse={payload['interface_targets']['tail_reconstruction_mse']}"
    )


if __name__ == "__main__":
    main()
