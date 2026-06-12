"""Localize the failed M3228 C1 BC warm-start gate.

This script performs no new training. It reloads the failed C1 checkpoint,
replays the frozen structured-oracle labels, and decomposes the action-MSE
failure by role, level, oracle action, segment, and action channel.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5prime_c1_oracle_bc_warmstart as c1  # noqa: E402
from autodrift.artifacts import write_json  # noqa: E402
from autodrift.train_ppo import ActorCritic  # noqa: E402


SUMMARY_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart.json"
OUTPUT_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_failure_localization.json"

CLAIM_BOUNDARY = (
    "M3229 C1 failure localization only: reanalysis of the failed M3228 "
    "warm-start artifact and frozen oracle labels. No new training, no criterion "
    "change, no driver mutation, no validation ranking, no promotion, no "
    "driver-performance claim, and no self-ID claim."
)


def _load_model(checkpoint_path: Path) -> ActorCritic:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    cfg = checkpoint["model_config"]
    model = ActorCritic(
        int(cfg["obs_dim"]),
        int(cfg["act_dim"]),
        hidden_size=int(cfg["hidden_size"]),
        actor_encoder=str(cfg["actor_encoder"]),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def _pred_actions(model: ActorCritic, obs: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        obs_t = torch.as_tensor(obs, dtype=torch.float32)
        pred = torch.tanh(model.actor_mean(model.features_tensor(obs_t)))
    return pred.cpu().numpy().astype(np.float32)


def _bucket(values: dict[str, list[float]], key: str, items: np.ndarray) -> None:
    values[key].extend(float(item) for item in items.reshape(-1))


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def _round(value: float) -> float | None:
    return round(value, 6) if np.isfinite(value) else None


def run() -> dict[str, Any]:
    torch.set_num_threads(1)
    t0 = time.time()
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    checkpoint_path = Path(summary["bc_training"]["checkpoint"])
    if not checkpoint_path.exists():
        raise FileNotFoundError(checkpoint_path)
    model = _load_model(checkpoint_path)
    prereg = c1.load_preregistration()
    source_rows = c1._source_row_by_id()
    fixed_cfg = c1._fixed_star_cfg()

    selected_rows = list(prereg["selected_rows"])
    per_row: list[dict[str, Any]] = []
    by_role: dict[str, list[float]] = defaultdict(list)
    by_level: dict[str, list[float]] = defaultdict(list)
    by_oracle: dict[str, list[float]] = defaultdict(list)
    by_segment: dict[str, list[float]] = defaultdict(list)
    by_channel: dict[str, list[float]] = defaultdict(list)

    for selected in selected_rows:
        demo = c1.rollout_oracle_demo(source_rows[selected["row_id"]], selected, fixed_cfg)
        obs = demo["obs"]
        target = demo["actions"]
        pred = _pred_actions(model, obs)
        sq = np.square(pred - target)
        row_mse = float(np.mean(sq))
        role = str(selected["bc_role"])
        level = str(selected["level"])
        oracle_by = str(selected["oracle_by"])
        reveal = int(selected["reveal_step"])
        steps = np.arange(len(obs))
        prefix_mask = steps < reveal
        tail_mask = ~prefix_mask

        _bucket(by_role, role, sq)
        _bucket(by_level, level, sq)
        _bucket(by_oracle, oracle_by, sq)
        if np.any(prefix_mask):
            _bucket(by_segment, f"{role}:prefix", sq[prefix_mask])
        if np.any(tail_mask):
            _bucket(by_segment, f"{role}:tail", sq[tail_mask])
        for idx, name in enumerate(("steer", "throttle", "brake")):
            by_channel[name].extend(float(item) for item in sq[:, idx])

        per_row.append(
            {
                "row_id": selected["row_id"],
                "role": role,
                "level": level,
                "instance": int(selected["instance"]),
                "oracle_by": oracle_by,
                "gap_row": bool(selected.get("gap_row")),
                "steps": int(len(obs)),
                "mse": round(row_mse, 6),
                "prefix_mse": _round(float(np.mean(sq[prefix_mask])) if np.any(prefix_mask) else float("nan")),
                "tail_mse": _round(float(np.mean(sq[tail_mask])) if np.any(tail_mask) else float("nan")),
            }
        )

    validation_rows = [row for row in per_row if row["role"] == "validation"]
    validation_mse = _mean([float(item) for row in validation_rows for item in [row["mse"]]])
    selection_mse = _mean([float(row["mse"]) for row in per_row if row["role"] == "selection"])
    train_mse = _mean([float(row["mse"]) for row in per_row if row["role"] == "train"])
    val_rollouts = summary["bc_training"].get("validation_bc_rollouts", [])
    validation_success_rate = (
        sum(row.get("outcome_bucket") == "success_obstacle_pass" for row in val_rollouts)
        / max(len(val_rollouts), 1)
    )

    diagnosis = []
    if validation_mse > 2.0 * max(selection_mse, 1e-9):
        diagnosis.append("selection_validation_mse_gap")
    tail_validation = by_segment.get("validation:tail", [])
    prefix_validation = by_segment.get("validation:prefix", [])
    if _mean(tail_validation) > _mean(prefix_validation):
        diagnosis.append("tail_action_generalization_dominates")
    if validation_success_rate >= 0.5 and summary["bc_training"].get("validation_mse_gate_passed") is False:
        diagnosis.append("rollout_context_better_than_action_mse_gate")

    payload = {
        "protocol": "c5prime_c1_failure_localization",
        "generated_by": "scripts/feasibility_audit/c5prime_c1_failure_localization.py",
        "claim_boundary": CLAIM_BOUNDARY,
        "source_summary": str(SUMMARY_JSON),
        "source_checkpoint": str(checkpoint_path),
        "m3228_gate": {
            "validation_action_mse": summary["bc_training"]["validation_action_mse"],
            "zero_action_baseline_mse": summary["bc_training"]["validation_zero_action_baseline_mse"],
            "validation_mse_gate_passed": summary["bc_training"]["validation_mse_gate_passed"],
            "validation_bc_success_rate_context": summary["bc_training"]["validation_bc_success_rate_context"],
        },
        "recomputed_mse": {
            "train_row_mean_mse": _round(train_mse),
            "selection_row_mean_mse": _round(selection_mse),
            "validation_row_mean_mse": _round(validation_mse),
            "by_role_frame_mse": {key: _round(_mean(values)) for key, values in sorted(by_role.items())},
            "by_level_frame_mse": {key: _round(_mean(values)) for key, values in sorted(by_level.items())},
            "by_oracle_frame_mse": {key: _round(_mean(values)) for key, values in sorted(by_oracle.items())},
            "by_segment_frame_mse": {key: _round(_mean(values)) for key, values in sorted(by_segment.items())},
            "by_action_channel_frame_mse": {key: _round(_mean(values)) for key, values in sorted(by_channel.items())},
        },
        "per_row": sorted(per_row, key=lambda row: (row["role"], -float(row["mse"]), row["row_id"])),
        "diagnosis_flags": diagnosis,
        "decision": {
            "m3228_result": "failed_preregistered_bc_action_mse_gate",
            "c1_status": "open",
            "recommended_next": (
                "Do not mark C1 complete from M3228. Register a revised C1 warm-start design "
                "only after freezing a new preregistration that addresses the selection/validation "
                "gap and tail-action generalization failure."
            ),
        },
        "elapsed_s": round(time.time() - t0, 3),
    }
    write_json(OUTPUT_JSON, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    payload = run()
    print(
        f"wrote {OUTPUT_JSON} flags={','.join(payload['diagnosis_flags'])} "
        f"val_mse={payload['recomputed_mse']['validation_row_mean_mse']}"
    )


if __name__ == "__main__":
    main()
