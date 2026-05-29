"""Bounded terminal-boundary repair planner for history-positive probes."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import assert_p0_model_contract
from autodrift.fresh_ambiguity_history_interventions import (
    AcceptedMeasuredPair,
    VARIANTS,
    build_pair_summary,
    build_variant_summary,
    finalize_rows,
    run_intervention_variant,
    source_row_key,
)
from autodrift.fresh_ambiguity_measured_mining import (
    DEFAULT_CHECKPOINT,
    DEFAULT_MAX_ROLLOUT_STEPS,
    SourceAttemptRow,
    build_pair_candidates,
    run_measured_trace,
)
from autodrift.fresh_ambiguity_source_mining import (
    FreshAmbiguitySourceRow,
    default_source_specs,
    expand_source_specs,
)
from autodrift.env import DriftEnvConfig
from autodrift.evaluate import ActorPolicy


DEFAULT_RUN_DIR = Path("runs/m1541_terminal_boundary_source_repair_smoke")
TERMINAL_TARGET_FAMILIES = (
    "t5_near_boundary_warmup",
    "t5_high_speed_close_obstacle",
    "t5_boundary_axis_retarget",
    "late_reveal_boundary",
    "curved_boundary_obstacle",
)
TERMINAL_SUPPORT_FAMILIES = (
    "brake_fade_or_loss_proxy",
    "grip_loss_proxy",
    "actuator_delay_step",
    "capability_step_down",
    "capability_step_up",
)
REPAIR_ANCHORS = ("decision", "decision_minus_8", "decision_minus_16", "reveal_plus_4")
NEAR_BOUNDARY_MARGIN_MIN = -0.03
NEAR_BOUNDARY_MARGIN_MAX = 0.12
TERMINAL_MARGIN_GAP_THRESHOLD = 0.02
TERMINAL_CONTROL_TO_HISTORY_RATIO_MAX = 4.0


def terminal_repair_source_rows(
    *,
    seed: int = 1731,
    seed_count: int = 3,
    max_repair_source_specs: int = 72,
) -> list[FreshAmbiguitySourceRow]:
    """Return bounded public source rows for terminal-boundary repair."""

    allowed = set(TERMINAL_TARGET_FAMILIES) | set(TERMINAL_SUPPORT_FAMILIES)
    rows = [
        row
        for row in expand_source_specs(default_source_specs(seed=seed, seed_count=seed_count))
        if row.source_family in allowed
    ]
    target_count = sum(1 for row in rows if is_terminal_target_family(row.source_family))
    extra_round = 0
    while len(rows) < int(max_repair_source_specs) and target_count < 20:
        extra_seed = int(seed) + 1000 + extra_round
        for row in expand_source_specs(default_source_specs(seed=extra_seed, seed_count=1)):
            if len(rows) >= int(max_repair_source_specs) or target_count >= 20:
                break
            if not is_terminal_target_family(row.source_family):
                continue
            rows.append(row)
            target_count += 1
        extra_round += 1
    return rows[: max(0, int(max_repair_source_specs))]


def is_terminal_target_family(source_family: str) -> bool:
    return source_family in set(TERMINAL_TARGET_FAMILIES)


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row) for row in rows]


def _guardrails() -> dict[str, bool]:
    return {
        "candidate_materialized": False,
        "training_started": False,
        "evaluation_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "training_corpus_exported": False,
        "labels_enter_actor_input": False,
        "level3_self_id_claim_made": False,
    }


def _accepted_pair_from_candidate(pair: Any) -> AcceptedMeasuredPair:
    return AcceptedMeasuredPair(
        pair_id=str(pair.pair_id),
        left_trace_id=str(pair.left_trace_id),
        right_trace_id=str(pair.right_trace_id),
        left_source_family=str(pair.left_source_family),
        right_source_family=str(pair.right_source_family),
        task_family=str(pair.task_family),
        scene_context_distance=float(pair.scene_context_distance),
        current_ego_distance=float(pair.current_ego_distance),
        first_action_l2=float(pair.first_action_l2),
        terminal_margin_gap=float(pair.terminal_margin_gap),
    )


def select_terminal_pairs(pair_candidates: Sequence[Any], *, max_intervention_pairs: int = 24) -> list[AcceptedMeasuredPair]:
    """Select accepted pairs with at least one terminal-boundary side."""

    selected: list[AcceptedMeasuredPair] = []
    for pair in pair_candidates:
        if not bool(pair.accepted):
            continue
        if not (is_terminal_target_family(pair.left_source_family) or is_terminal_target_family(pair.right_source_family)):
            continue
        selected.append(_accepted_pair_from_candidate(pair))
        if len(selected) >= int(max_intervention_pairs):
            break
    return selected


def _near_boundary_attempt_count(snapshots: Sequence[Any]) -> int:
    return sum(
        1
        for row in snapshots
        if row.snapshot_kind == "decision"
        and is_terminal_target_family(row.source_family)
        and NEAR_BOUNDARY_MARGIN_MIN <= float(row.min_clearance_margin) <= NEAR_BOUNDARY_MARGIN_MAX
    )


def _target_trace_count(attempts: Sequence[SourceAttemptRow]) -> int:
    return sum(1 for row in attempts if is_terminal_target_family(row.source_family) and row.reached_decision)


def _source_edge_count(pairs: Sequence[AcceptedMeasuredPair]) -> int:
    return len({(pair.left_source_family, pair.right_source_family) for pair in pairs})


def _positive_count(rows: Sequence[dict[str, Any]], *, variant: str | None = None, prefix: str | None = None) -> int:
    count = 0
    for row in rows:
        if not is_terminal_target_family(str(row.get("target_source_family", ""))):
            continue
        row_variant = str(row.get("variant", ""))
        if variant is not None and row_variant != variant:
            continue
        if prefix is not None and not row_variant.startswith(prefix):
            continue
        if float(row.get("terminal_margin_gap_from_normal") or 0.0) >= TERMINAL_MARGIN_GAP_THRESHOLD:
            count += 1
    return count


def _success_drop_count(rows: Sequence[dict[str, Any]]) -> int:
    variants = {"wrong_history_donor_hidden_at_anchor", "donor_response_action_plus_hidden_from_anchor"}
    return sum(
        1
        for row in rows
        if is_terminal_target_family(str(row.get("target_source_family", "")))
        and str(row.get("variant", "")) in variants
        and bool(row.get("success_drop_from_normal", False))
    )


def _max_gap(rows: Sequence[dict[str, Any]], variants: set[str]) -> float:
    return max(
        (
            float(row.get("terminal_margin_gap_from_normal") or 0.0)
            for row in rows
            if is_terminal_target_family(str(row.get("target_source_family", "")))
            and str(row.get("variant", "")) in variants
        ),
        default=0.0,
    )


def build_terminal_summary(
    *,
    source_rows: Sequence[FreshAmbiguitySourceRow],
    attempts: Sequence[SourceAttemptRow],
    snapshots: Sequence[Any],
    pairs: Sequence[AcceptedMeasuredPair],
    rows: Sequence[dict[str, Any]],
    max_intervention_pairs: int,
    continuation_steps: int,
) -> dict[str, Any]:
    guardrails = _guardrails()
    target_rows = [row for row in source_rows if is_terminal_target_family(row.source_family)]
    terminal_history_max = max(
        _max_gap(rows, {"wrong_history_donor_hidden_at_anchor", "donor_response_action_plus_hidden_from_anchor"}),
        0.0,
    )
    terminal_control_max = _max_gap(
        rows,
        {
            "reset_hidden_once_at_anchor",
            "reset_hidden_every_step_from_anchor",
            "zero_current_response_from_anchor",
            "zero_action_history_from_anchor",
        },
    )
    ratio = None if terminal_history_max <= 0.0 else terminal_control_max / terminal_history_max
    terminal_wrong = _positive_count(rows, variant="wrong_history_donor_hidden_at_anchor")
    terminal_donor_plus = _positive_count(rows, variant="donor_response_action_plus_hidden_from_anchor")
    terminal_drop = _success_drop_count(rows)
    summary = {
        "result_class": "terminal_boundary_source_repair_smoke",
        "terminal_source_spec_count": len(source_rows),
        "terminal_target_source_spec_count": len(target_rows),
        "terminal_target_trace_count": _target_trace_count(attempts),
        "terminal_target_near_boundary_count": _near_boundary_attempt_count(snapshots),
        "accepted_terminal_pair_count": len(pairs),
        "accepted_terminal_source_edge_count": _source_edge_count(pairs),
        "intervention_row_count": len(rows),
        "target_side_count": len({(row.get("pair_id"), row.get("target_side"), row.get("anchor_name")) for row in rows}),
        "variant_count": len(VARIANTS),
        "anchor_count": len(REPAIR_ANCHORS),
        "max_intervention_pairs": int(max_intervention_pairs),
        "continuation_steps": int(continuation_steps),
        "terminal_wrong_history_positive_target_sides": terminal_wrong,
        "terminal_donor_plus_hidden_positive_target_sides": terminal_donor_plus,
        "terminal_donor_stream_positive_target_sides": _positive_count(rows, variant="donor_response_action_stream_from_anchor"),
        "terminal_wrong_or_donor_success_drop_count": terminal_drop,
        "terminal_max_history_margin_gap": terminal_history_max,
        "terminal_max_control_margin_gap": terminal_control_max,
        "terminal_control_to_history_gap_ratio": ratio,
        "anchor_replay_failure_count": sum(1 for row in rows if row.get("target_replay_status") != "ok"),
        "source_family_counts": dict(sorted(Counter(row.source_family for row in source_rows).items())),
        "passes_terminal_source_gates": (
            len(source_rows) >= 30
            and _target_trace_count(attempts) >= 20
            and _near_boundary_attempt_count(snapshots) >= 8
            and len(pairs) >= 4
            and _source_edge_count(pairs) >= 3
        ),
        "passes_terminal_history_gates": (
            terminal_wrong >= 2
            or terminal_donor_plus >= 2
            or terminal_drop >= 1
        ),
        "passes_control_gate": ratio is None or ratio <= TERMINAL_CONTROL_TO_HISTORY_RATIO_MAX,
        "guardrails": guardrails,
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        **guardrails,
    }
    summary["passes_public_smoke_gates"] = (
        bool(summary["passes_terminal_source_gates"])
        and int(summary["anchor_replay_failure_count"]) <= max(1, int(len(rows) * 0.05))
        and int(summary["guardrail_violation_count"]) == 0
    )
    summary["passes_evidence_quality_targets"] = bool(summary["passes_terminal_history_gates"])
    return summary


def run_terminal_boundary_source_repair_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1731,
    seed_count: int = 3,
    max_repair_source_specs: int = 72,
    max_pair_candidates: int = 128,
    max_intervention_pairs: int = 24,
    max_rollout_steps: int = DEFAULT_MAX_ROLLOUT_STEPS,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run a bounded terminal-boundary repair smoke without materialization."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_rows = terminal_repair_source_rows(
        seed=seed,
        seed_count=seed_count,
        max_repair_source_specs=max_repair_source_specs,
    )
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    policy = ActorPolicy(model, DriftEnvConfig())

    traces: list[Any] = []
    snapshots: list[Any] = []
    attempts: list[SourceAttemptRow] = []
    for row in source_rows:
        trace_rows, snapshot_rows, attempt = run_measured_trace(row, policy, max_rollout_steps=max_rollout_steps)
        traces.extend(trace_rows)
        snapshots.extend(snapshot_rows)
        attempts.append(attempt)

    pair_candidates = build_pair_candidates(snapshots, max_pairs=max_pair_candidates)
    accepted_pairs = select_terminal_pairs(pair_candidates, max_intervention_pairs=max_intervention_pairs)
    rows_by_trace = {source_row_key(row): row for row in source_rows}
    intervention_rows: list[dict[str, Any]] = []
    for pair in accepted_pairs:
        left_row = rows_by_trace[pair.left_trace_id]
        right_row = rows_by_trace[pair.right_trace_id]
        for anchor in REPAIR_ANCHORS:
            for target_side, target_row, donor_side, donor_row in (
                ("left", left_row, "right", right_row),
                ("right", right_row, "left", left_row),
            ):
                for variant in VARIANTS:
                    intervention_rows.append(
                        run_intervention_variant(
                            pair=pair,
                            target_side=target_side,
                            target_row=target_row,
                            donor_side=donor_side,
                            donor_row=donor_row,
                            anchor_name=anchor,
                            variant=variant,
                            model=model,
                            continuation_steps=continuation_steps,
                        )
                    )
    finalized = finalize_rows(intervention_rows)
    pair_summary = build_pair_summary(finalized)
    variant_summary = build_variant_summary(finalized)
    summary = build_terminal_summary(
        source_rows=source_rows,
        attempts=attempts,
        snapshots=snapshots,
        pairs=accepted_pairs,
        rows=finalized,
        max_intervention_pairs=max_intervention_pairs,
        continuation_steps=continuation_steps,
    )

    write_csv_rows(output / "terminal_source_rows.csv", _asdict_rows(source_rows))
    write_csv_rows(output / "terminal_trace_rows.csv", _asdict_rows(traces))
    write_csv_rows(output / "terminal_snapshot_rows.csv", _asdict_rows(snapshots))
    write_csv_rows(output / "terminal_source_attempt_rows.csv", _asdict_rows(attempts))
    write_csv_rows(output / "terminal_pair_candidates.csv", _asdict_rows(pair_candidates))
    write_csv_rows(output / "accepted_terminal_pair_rows.csv", _asdict_rows(accepted_pairs))
    write_csv_rows(output / "terminal_intervention_rows.csv", finalized)
    write_csv_rows(output / "terminal_pair_summary.csv", pair_summary)
    write_csv_rows(output / "terminal_variant_summary.csv", variant_summary)
    write_csv_rows(output / "guardrail_summary.csv", [_guardrails()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded terminal-boundary source repair smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1731)
    parser.add_argument("--seed-count", type=int, default=3)
    parser.add_argument("--max-repair-source-specs", type=int, default=72)
    parser.add_argument("--max-pair-candidates", type=int, default=128)
    parser.add_argument("--max-intervention-pairs", type=int, default=24)
    parser.add_argument("--max-rollout-steps", type=int, default=DEFAULT_MAX_ROLLOUT_STEPS)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_terminal_boundary_source_repair_smoke(
        args.output_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_repair_source_specs=int(args.max_repair_source_specs),
        max_pair_candidates=int(args.max_pair_candidates),
        max_intervention_pairs=int(args.max_intervention_pairs),
        max_rollout_steps=int(args.max_rollout_steps),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"accepted_terminal_pair_count={summary['accepted_terminal_pair_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
