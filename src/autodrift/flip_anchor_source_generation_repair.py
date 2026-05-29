"""Bounded source-generation repair for distinct flip anchors."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.recoverable_active_set_generator import (
    GUARDRAILS as BASE_GUARDRAILS,
    LOCAL_OVERRIDES,
    PREDECISION_WINDOWS,
    anchor_result_row,
    build_anchor_candidates,
    local_hold_row,
    recoverable_active_anchor_rows,
    run_hold_continuation,
    source_specs,
)
from autodrift.calibrated_terminal_boundary_history_interventions import replay_to_anchor
from autodrift.temporal_active_set_anchor_sensitivity_miner import _asdict_rows, _finite_float


DEFAULT_RUN_DIR = Path("runs/m1566_flip_anchor_source_generation_repair_smoke")
REPAIR_HOLD_STEPS = (1, 4, 8, 12, 16)
REPAIR_LOCAL_OVERRIDES = (
    *LOCAL_OVERRIDES,
    "full_brake_release_throttle",
    "steer_left_full_brake",
    "steer_right_full_brake",
)
GUARDRAILS = {
    **BASE_GUARDRAILS,
    "simulator_rerun_started": True,
}


def apply_repair_override(action: Sequence[float], override: str, *, steer_delta: float = 0.30, brake_delta: float = 0.45) -> np.ndarray:
    """Apply local diagnostic overrides, including stronger flip-anchor probes."""

    from autodrift.recoverable_active_set_generator import apply_local_override

    if override in LOCAL_OVERRIDES:
        return apply_local_override(action, override, steer_delta=steer_delta, brake_delta=brake_delta)
    result = np.asarray(action, dtype=np.float64).copy()
    if result.shape != (3,):
        raise ValueError(f"expected action shape (3,), got {result.shape}")
    if override == "full_brake_release_throttle":
        result[1] = -1.0
        result[2] = 1.0
    elif override == "steer_left_full_brake":
        result[0] += steer_delta
        result[1] = -1.0
        result[2] = 1.0
    elif override == "steer_right_full_brake":
        result[0] -= steer_delta
        result[1] = -1.0
        result[2] = 1.0
    else:
        raise ValueError(f"unknown repair override: {override}")
    return np.clip(result, -1.0, 1.0).astype(np.float32)


def _max_share(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return max((count / max(1, total) for count in counts.values()), default=0.0)


def _flip_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if int(row.get("success_flip_count") or 0) > 0 or int(row.get("collision_flip_count") or 0) > 0
    ]


def _group_summary(rows: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    result: list[dict[str, Any]] = []
    for value, group in sorted(grouped.items()):
        result.append(
            {
                key: value,
                "anchor_count": len(group),
                "recoverable_boundary_anchor_count": sum(1 for row in group if bool(row.get("recoverable_boundary", False))),
                "strong_recoverable_boundary_anchor_count": sum(1 for row in group if bool(row.get("strong_recoverable_boundary", False))),
                "collision_flip_anchor_count": sum(1 for row in group if int(row.get("collision_flip_count") or 0) > 0),
                "success_flip_anchor_count": sum(1 for row in group if int(row.get("success_flip_count") or 0) > 0),
                "collision_flip_variant_count": sum(int(row.get("collision_flip_count") or 0) for row in group),
                "success_flip_variant_count": sum(int(row.get("success_flip_count") or 0) for row in group),
                "max_abs_terminal_margin_gap": max(
                    (_finite_float(row.get("max_abs_terminal_margin_gap")) for row in group),
                    default=0.0,
                ),
            }
        )
    return result


def build_flip_anchor_summary(
    *,
    specs: Sequence[Any],
    anchor_rows: Sequence[Mapping[str, Any]],
    local_rows: Sequence[Mapping[str, Any]],
    triage_rows: Sequence[Mapping[str, Any]],
    max_source_specs: int,
    max_anchors: int,
    continuation_steps: int,
) -> dict[str, Any]:
    """Build repair summary with distinct flip-anchor gates."""

    replay_ok = [row for row in anchor_rows if row.get("normal_replay_status") == "ok"]
    recoverable_rows = [row for row in triage_rows if bool(row.get("recoverable_boundary", False))]
    strong_rows = [row for row in triage_rows if bool(row.get("strong_recoverable_boundary", False))]
    predecision_rows = [row for row in recoverable_rows if str(row.get("anchor_window", "")) in PREDECISION_WINDOWS]
    flip_rows = _flip_rows(recoverable_rows)
    collision_flip_rows = [row for row in recoverable_rows if int(row.get("collision_flip_count") or 0) > 0]
    success_flip_rows = [row for row in recoverable_rows if int(row.get("success_flip_count") or 0) > 0]
    active_family_counts = Counter(str(row.get("source_family", "")) for row in recoverable_rows)
    active_window_counts = Counter(str(row.get("anchor_window", "")) for row in recoverable_rows)
    flip_family_counts = Counter(str(row.get("source_family", "")) for row in flip_rows)
    flip_window_counts = Counter(str(row.get("anchor_window", "")) for row in flip_rows)
    local_ok = [row for row in local_rows if row.get("replay_status") == "ok"]
    forbidden_guardrails = {key: value for key, value in GUARDRAILS.items() if key != "simulator_rerun_started"}
    summary = {
        "result_class": "flip_anchor_source_generation_repair_smoke",
        "source_spec_count": len(specs),
        "max_source_specs": int(max_source_specs),
        "anchor_candidate_count": len(anchor_rows),
        "max_anchors": int(max_anchors),
        "replay_ok_anchor_count": len(replay_ok),
        "local_hold_row_count": len(local_rows),
        "local_hold_failure_count": len(local_rows) - len(local_ok),
        "override_count": len(REPAIR_LOCAL_OVERRIDES),
        "hold_step_count": len(REPAIR_HOLD_STEPS),
        "continuation_steps": int(continuation_steps),
        "recoverable_boundary_anchor_count": len(recoverable_rows),
        "strong_recoverable_boundary_anchor_count": len(strong_rows),
        "predecision_recoverable_anchor_count": len(predecision_rows),
        "active_source_family_count": len(active_family_counts),
        "active_window_count": len(active_window_counts),
        "max_single_active_family_share": _max_share(active_family_counts),
        "max_single_active_window_share": _max_share(active_window_counts),
        "distinct_collision_flip_anchor_count": len(collision_flip_rows),
        "distinct_success_flip_anchor_count": len(success_flip_rows),
        "distinct_any_flip_anchor_count": len(flip_rows),
        "flip_anchor_source_family_count": len(flip_family_counts),
        "flip_anchor_window_count": len(flip_window_counts),
        "max_single_flip_source_family_share": _max_share(flip_family_counts),
        "max_single_flip_window_share": _max_share(flip_window_counts),
        "collision_flip_variant_count": sum(int(row.get("collision_flip_count") or 0) for row in recoverable_rows),
        "success_flip_variant_count": sum(int(row.get("success_flip_count") or 0) for row in recoverable_rows),
        "active_source_family_counts": dict(sorted(active_family_counts.items())),
        "active_window_counts": dict(sorted(active_window_counts.items())),
        "flip_source_family_counts": dict(sorted(flip_family_counts.items())),
        "flip_window_counts": dict(sorted(flip_window_counts.items())),
        "triage_label_counts": dict(sorted(Counter(str(row.get("triage_label", "")) for row in triage_rows).items())),
        "guardrail_violation_count": sum(1 for value in forbidden_guardrails.values() if bool(value)),
        **GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["source_spec_count"]) >= 200
        and int(summary["anchor_candidate_count"]) >= 300
        and int(summary["replay_ok_anchor_count"]) >= 160
        and int(summary["recoverable_boundary_anchor_count"]) >= 48
        and int(summary["strong_recoverable_boundary_anchor_count"]) >= 16
        and int(summary["predecision_recoverable_anchor_count"]) >= 24
        and int(summary["active_source_family_count"]) >= 5
        and int(summary["active_window_count"]) >= 5
        and float(summary["max_single_active_family_share"]) <= 0.40
        and int(summary["distinct_collision_flip_anchor_count"]) >= 8
        and int(summary["distinct_success_flip_anchor_count"]) >= 8
        and int(summary["flip_anchor_source_family_count"]) >= 3
        and int(summary["flip_anchor_window_count"]) >= 3
        and float(summary["max_single_flip_source_family_share"]) <= 0.60
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["history_interventions_executed"])
        and not bool(summary["training_corpus_exported"])
        and not bool(summary["candidate_materialized"])
    )
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and int(summary["distinct_collision_flip_anchor_count"]) >= 12
        and int(summary["distinct_success_flip_anchor_count"]) >= 12
        and int(summary["flip_anchor_source_family_count"]) >= 4
        and int(summary["flip_anchor_window_count"]) >= 4
        and float(summary["max_single_flip_source_family_share"]) <= 0.45
        and int(summary["recoverable_boundary_anchor_count"]) >= 40
        and int(summary["strong_recoverable_boundary_anchor_count"]) >= 24
        and int(summary["active_source_family_count"]) >= 5
        and int(summary["active_window_count"]) >= 5
    )
    return summary


def run_flip_anchor_source_generation_repair_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 6,
    max_source_specs: int = 320,
    max_anchors: int = 320,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run the bounded public source-generation repair smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    specs_by_id = {spec.artifact_row.calibration_id: spec for spec in specs}
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    candidates = build_anchor_candidates(specs, max_anchors=max_anchors)
    anchor_rows: list[dict[str, Any]] = []
    local_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        spec = specs_by_id[candidate.calibration_id]
        replay = replay_to_anchor(
            pair_id=candidate.anchor_id,
            side="target",
            spec=spec,
            anchor_step=int(candidate.anchor_step),
            model=model,
        )
        normal = run_hold_continuation(
            replay=replay,
            spec=spec,
            model=model,
            continuation_steps=continuation_steps,
        )
        anchor_rows.append(anchor_result_row(candidate, normal))
        for override in REPAIR_LOCAL_OVERRIDES:
            for hold_steps in REPAIR_HOLD_STEPS:
                result = run_hold_continuation(
                    replay=replay,
                    spec=spec,
                    model=model,
                    continuation_steps=continuation_steps,
                    override=override,
                    hold_steps=int(hold_steps),
                    override_fn=apply_repair_override,
                )
                local_rows.append(
                    local_hold_row(
                        candidate,
                        normal,
                        override=override,
                        hold_steps=int(hold_steps),
                        result=result,
                    )
                )

    triage_rows = recoverable_active_anchor_rows(anchor_rows, local_rows)
    recoverable_rows = [row for row in triage_rows if bool(row.get("recoverable_boundary", False))]
    flip_rows = _flip_rows(recoverable_rows)
    summary = build_flip_anchor_summary(
        specs=specs,
        anchor_rows=anchor_rows,
        local_rows=local_rows,
        triage_rows=triage_rows,
        max_source_specs=max_source_specs,
        max_anchors=max_anchors,
        continuation_steps=continuation_steps,
    )
    write_csv_rows(output / "source_spec_rows.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "anchor_candidate_rows.csv", anchor_rows)
    write_csv_rows(output / "local_hold_rows.csv", local_rows)
    write_csv_rows(output / "recoverable_active_anchor_rows.csv", recoverable_rows)
    write_csv_rows(output / "flip_anchor_rows.csv", flip_rows)
    write_csv_rows(output / "source_family_summary.csv", _group_summary(triage_rows, "source_family"))
    write_csv_rows(output / "window_summary.csv", _group_summary(triage_rows, "anchor_window"))
    write_csv_rows(output / "flip_source_summary.csv", _group_summary(flip_rows, "source_family"))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run flip-anchor source-generation repair smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=320)
    parser.add_argument("--max-anchors", type=int, default=320)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_flip_anchor_source_generation_repair_smoke(
        args.output_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchors=int(args.max_anchors),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"recoverable_boundary_anchor_count={summary['recoverable_boundary_anchor_count']}")
    print(f"distinct_collision_flip_anchor_count={summary['distinct_collision_flip_anchor_count']}")
    print(f"distinct_success_flip_anchor_count={summary['distinct_success_flip_anchor_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
