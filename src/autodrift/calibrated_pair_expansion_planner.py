"""Pairability-first calibrated terminal-boundary source expansion."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_terminal_boundary_history_interventions import (
    DEFAULT_ACCEPTED_CALIBRATED_ROWS,
    AcceptedCalibratedSource,
    CalibratedMeasuredSnapshot,
    CalibratedMeasuredTraceAttempt,
    run_calibrated_measured_trace,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.evaluate import ActorPolicy
from autodrift.terminal_boundary_task_sampling_calibration import (
    CalibrationSpec,
    build_calibration_specs,
    terminal_calibration_source_rows,
)


DEFAULT_RUN_DIR = Path("runs/m1550_calibrated_pair_expansion_planner_smoke")
GUARDRAILS = {
    "candidate_materialized": False,
    "training_started": False,
    "evaluation_started": False,
    "replay_started": False,
    "history_interventions_executed": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "training_corpus_exported": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


@dataclass(frozen=True)
class PairExpansionCandidate:
    """One calibrated measured pair candidate before diversity selection."""

    pair_id: str
    left_calibration_id: str
    right_calibration_id: str
    left_source_family: str
    right_source_family: str
    left_mode_name: str
    right_mode_name: str
    left_window_kind: str
    right_window_kind: str
    left_anchor_step: int
    right_anchor_step: int
    source_family_edge: str
    window_pair_kind: str
    scene_context_distance: float
    current_ego_distance: float
    anchor_window_distance: int
    first_action_l2: float
    terminal_margin_gap: float
    pairability_score: float
    accepted: bool = False
    rejection_reason: str = ""


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row) for row in rows]


def _vector_distance(left: Sequence[float], right: Sequence[float]) -> float:
    left_arr = np.asarray(left, dtype=np.float64)
    right_arr = np.asarray(right, dtype=np.float64)
    if left_arr.size == 0 or right_arr.size == 0 or left_arr.shape != right_arr.shape:
        return float("inf")
    return float(np.linalg.norm(left_arr - right_arr) / np.sqrt(float(left_arr.size)))


def _action_distance(left: Sequence[float], right: Sequence[float]) -> float:
    return float(np.linalg.norm(np.asarray(left, dtype=np.float64) - np.asarray(right, dtype=np.float64)))


def _source_edge(left: str, right: str) -> str:
    return "|".join(sorted((str(left), str(right))))


def _window_pair(left: str, right: str) -> str:
    return "|".join(sorted((str(left), str(right))))


def _pseudo_accepted_source(spec: CalibrationSpec) -> AcceptedCalibratedSource:
    row = spec.artifact_row
    return AcceptedCalibratedSource(
        calibration_id=row.calibration_id,
        trace_id="",
        source_row_id=row.source_row_id,
        source_family=row.source_family,
        seed=int(row.seed),
        mode_name=row.mode_name,
        window_kind="planner",
        decision_margin=float("nan"),
        post_decision_margin=float("nan"),
        terminal_margin=float("nan"),
        decision_window_hit=False,
        post_decision_window_hit=False,
        terminal_reason="planner",
        collision=False,
        obstacle_completed=False,
    )


def expanded_terminal_source_rows(*, seed: int, seed_count: int, max_base_rows: int) -> list[Any]:
    """Return up to max_base_rows terminal rows after upstream over-sampling."""

    rows = terminal_calibration_source_rows(
        seed=seed,
        seed_count=seed_count,
        max_base_rows=max(int(max_base_rows) * 4, int(max_base_rows)),
    )
    return rows[: max(0, int(max_base_rows))]


def pairability_score(
    *,
    scene_context_distance: float,
    current_ego_distance: float,
    anchor_window_distance: int,
    first_action_l2: float,
    terminal_margin_gap: float,
    edge_seen_count: int = 0,
    window_seen_count: int = 0,
) -> float:
    """Deterministic score for ranking calibrated pair candidates."""

    return float(
        4.0 * first_action_l2
        + 2.5 * terminal_margin_gap
        + 0.20 / (1.0 + float(edge_seen_count))
        + 0.10 / (1.0 + float(window_seen_count))
        - 2.0 * scene_context_distance
        - 2.0 * current_ego_distance
        - 0.01 * abs(int(anchor_window_distance))
    )


def build_pair_candidates(
    snapshots: Sequence[CalibratedMeasuredSnapshot],
    specs_by_id: dict[str, CalibrationSpec],
    *,
    max_pair_candidates: int = 256,
    max_scene_context_distance: float = 0.18,
    max_current_ego_distance: float = 0.18,
    min_first_action_l2: float = 0.035,
    min_terminal_margin_gap: float = 0.015,
) -> list[PairExpansionCandidate]:
    """Build scored calibrated pair candidates without diversity filtering."""

    rows: list[PairExpansionCandidate] = []
    edge_counts: Counter[str] = Counter()
    window_counts: Counter[str] = Counter()
    for left_index, left in enumerate(snapshots):
        for right in snapshots[left_index + 1 :]:
            if left.calibration_id == right.calibration_id:
                continue
            if left.source_family == right.source_family:
                continue
            left_spec = specs_by_id.get(left.calibration_id)
            right_spec = specs_by_id.get(right.calibration_id)
            if left_spec is None or right_spec is None:
                continue
            scene_distance = _vector_distance(left.context_vector, right.context_vector)
            current_distance = _vector_distance(left.response_vector, right.response_vector)
            action_l2 = _action_distance(left.action_vector, right.action_vector)
            margin_gap = abs(float(left.min_clearance_margin) - float(right.min_clearance_margin))
            if scene_distance > max_scene_context_distance:
                continue
            if current_distance > max_current_ego_distance:
                continue
            if action_l2 < min_first_action_l2:
                continue
            if margin_gap < min_terminal_margin_gap:
                continue
            edge = _source_edge(left.source_family, right.source_family)
            window_pair = _window_pair(left.window_kind, right.window_kind)
            anchor_delta = abs(int(left.anchor_step) - int(right.anchor_step))
            score = pairability_score(
                scene_context_distance=scene_distance,
                current_ego_distance=current_distance,
                anchor_window_distance=anchor_delta,
                first_action_l2=action_l2,
                terminal_margin_gap=margin_gap,
                edge_seen_count=edge_counts[edge],
                window_seen_count=window_counts[window_pair],
            )
            edge_counts[edge] += 1
            window_counts[window_pair] += 1
            rows.append(
                PairExpansionCandidate(
                    pair_id=f"candidate-{len(rows):04d}",
                    left_calibration_id=left.calibration_id,
                    right_calibration_id=right.calibration_id,
                    left_source_family=left.source_family,
                    right_source_family=right.source_family,
                    left_mode_name=left_spec.artifact_row.mode_name,
                    right_mode_name=right_spec.artifact_row.mode_name,
                    left_window_kind=left.window_kind,
                    right_window_kind=right.window_kind,
                    left_anchor_step=int(left.anchor_step),
                    right_anchor_step=int(right.anchor_step),
                    source_family_edge=edge,
                    window_pair_kind=window_pair,
                    scene_context_distance=scene_distance,
                    current_ego_distance=current_distance,
                    anchor_window_distance=anchor_delta,
                    first_action_l2=action_l2,
                    terminal_margin_gap=margin_gap,
                    pairability_score=score,
                )
            )
    rows.sort(key=lambda row: row.pairability_score, reverse=True)
    return rows[: max(0, int(max_pair_candidates))]


def select_diverse_pairs(
    candidates: Sequence[PairExpansionCandidate],
    *,
    max_accepted_pairs: int = 64,
) -> list[PairExpansionCandidate]:
    """Select accepted pairs with source-edge round-robin diversity."""

    grouped: dict[str, list[PairExpansionCandidate]] = defaultdict(list)
    for row in candidates:
        grouped[row.source_family_edge].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: row.pairability_score, reverse=True)

    accepted: list[PairExpansionCandidate] = []
    used_keys: set[tuple[str, str, int, int]] = set()
    edge_order = sorted(grouped, key=lambda edge: grouped[edge][0].pairability_score if grouped[edge] else -float("inf"), reverse=True)
    while edge_order and len(accepted) < int(max_accepted_pairs):
        progressed = False
        for edge in list(edge_order):
            rows = grouped[edge]
            while rows:
                row = rows.pop(0)
                key = tuple(sorted((row.left_calibration_id, row.right_calibration_id))) + tuple(
                    sorted((row.left_anchor_step, row.right_anchor_step))
                )
                if key in used_keys:
                    continue
                used_keys.add(key)
                accepted.append(
                    PairExpansionCandidate(
                        **{
                            **asdict(row),
                            "pair_id": f"pair-{len(accepted):04d}",
                            "accepted": True,
                            "rejection_reason": "",
                        }
                    )
                )
                progressed = True
                break
            if not rows:
                edge_order.remove(edge)
            if len(accepted) >= int(max_accepted_pairs):
                break
        if not progressed:
            break
    return accepted


def build_pair_family_summary(pairs: Sequence[PairExpansionCandidate]) -> list[dict[str, Any]]:
    """Summarize accepted pairs by source-family edge."""

    grouped: dict[str, list[PairExpansionCandidate]] = defaultdict(list)
    for pair in pairs:
        grouped[pair.source_family_edge].append(pair)
    rows: list[dict[str, Any]] = []
    for edge, edge_pairs in sorted(grouped.items()):
        rows.append(
            {
                "source_family_edge": edge,
                "accepted_pair_count": len(edge_pairs),
                "window_pair_counts": dict(sorted(Counter(pair.window_pair_kind for pair in edge_pairs).items())),
                "min_scene_context_distance": min(pair.scene_context_distance for pair in edge_pairs),
                "max_scene_context_distance": max(pair.scene_context_distance for pair in edge_pairs),
                "min_current_ego_distance": min(pair.current_ego_distance for pair in edge_pairs),
                "max_current_ego_distance": max(pair.current_ego_distance for pair in edge_pairs),
                "max_first_action_l2": max(pair.first_action_l2 for pair in edge_pairs),
                "max_terminal_margin_gap": max(pair.terminal_margin_gap for pair in edge_pairs),
            }
        )
    return rows


def build_summary(
    *,
    source_rows: Sequence[Any],
    specs: Sequence[CalibrationSpec],
    attempts: Sequence[CalibratedMeasuredTraceAttempt],
    snapshots: Sequence[CalibratedMeasuredSnapshot],
    candidates: Sequence[PairExpansionCandidate],
    accepted_pairs: Sequence[PairExpansionCandidate],
    max_pair_candidates: int,
) -> dict[str, Any]:
    """Build pair-expansion planner smoke summary."""

    guardrails = dict(GUARDRAILS)
    edge_counts = Counter(pair.source_family_edge for pair in accepted_pairs)
    max_edge_share = max((count / max(1, len(accepted_pairs)) for count in edge_counts.values()), default=0.0)
    accepted_families = {
        family
        for pair in accepted_pairs
        for family in (pair.left_source_family, pair.right_source_family)
    }
    family_count = len(accepted_families)
    window_count = len({pair.window_pair_kind for pair in accepted_pairs})
    summary = {
        "result_class": "calibrated_pair_expansion_planner_smoke",
        "terminal_base_source_rows": len(source_rows),
        "calibration_spec_count": len(specs),
        "measured_trace_count": len(attempts),
        "measured_snapshot_count": len(snapshots),
        "measured_trace_family_count": len({row.source_family for row in attempts}),
        "pair_candidate_count": len(candidates),
        "accepted_pair_count": len(accepted_pairs),
        "accepted_source_family_edge_count": len(edge_counts),
        "max_single_pair_source_edge_share": max_edge_share,
        "accepted_terminal_family_count": family_count,
        "accepted_window_bucket_count": window_count,
        "max_pair_candidates": int(max_pair_candidates),
        "rollout_failure_count": sum(1 for row in attempts if row.failure_type != "none"),
        "failure_type_counts": dict(sorted(Counter(row.failure_type for row in attempts).items())),
        "source_family_counts": dict(sorted(Counter(row.source_family for row in snapshots).items())),
        "source_family_edge_counts": dict(sorted(edge_counts.items())),
        "window_pair_kind_counts": dict(sorted(Counter(pair.window_pair_kind for pair in accepted_pairs).items())),
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        **guardrails,
    }
    summary["passes_trace_gates"] = (
        int(summary["terminal_base_source_rows"]) >= 10
        and int(summary["calibration_spec_count"]) >= 40
        and int(summary["measured_trace_count"]) >= 20
        and int(summary["measured_snapshot_count"]) >= 24
        and int(summary["measured_trace_family_count"]) >= 4
        and int(summary["guardrail_violation_count"]) == 0
    )
    summary["passes_pair_gates"] = (
        int(summary["pair_candidate_count"]) >= 16
        and int(summary["accepted_pair_count"]) >= 8
        and int(summary["accepted_source_family_edge_count"]) >= 5
        and float(summary["max_single_pair_source_edge_share"]) <= 0.40
        and int(summary["accepted_terminal_family_count"]) >= 4
        and int(summary["accepted_window_bucket_count"]) >= 2
    )
    summary["passes_public_smoke_gates"] = bool(summary["passes_trace_gates"]) and bool(summary["passes_pair_gates"])
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and int(summary["accepted_pair_count"]) >= 12
        and int(summary["accepted_source_family_edge_count"]) >= 6
        and float(summary["max_single_pair_source_edge_share"]) <= 0.30
    )
    return summary


def run_calibrated_pair_expansion_planner_smoke(
    output_dir: Path | str,
    *,
    accepted_calibrated_rows: Path | str = DEFAULT_ACCEPTED_CALIBRATED_ROWS,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 3,
    max_base_rows: int = 24,
    max_calibration_specs: int = 240,
    max_pair_candidates: int = 256,
    max_rollout_steps: int = 128,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded no-training calibrated pair-expansion planner smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    # The accepted rows are an admission artifact for branch lineage. M1550
    # expands beyond their ids, but keeps the input visible in artifacts.
    admitted_rows = []
    if Path(accepted_calibrated_rows).exists():
        from autodrift.calibrated_terminal_boundary_history_interventions import load_accepted_calibrated_sources

        admitted_rows = load_accepted_calibrated_sources(accepted_calibrated_rows)
    source_rows = expanded_terminal_source_rows(seed=seed, seed_count=seed_count, max_base_rows=max_base_rows)
    specs = build_calibration_specs(source_rows, max_calibration_specs=max_calibration_specs)
    specs_by_id = {spec.artifact_row.calibration_id: spec for spec in specs}
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    policy = ActorPolicy(model, specs[0].hook_spec.env_config) if specs else None
    trace_rows: list[dict[str, Any]] = []
    snapshots: list[CalibratedMeasuredSnapshot] = []
    attempts: list[CalibratedMeasuredTraceAttempt] = []
    if policy is not None:
        for spec in specs:
            pseudo = _pseudo_accepted_source(spec)
            rows, snapshot_rows, attempt = run_calibrated_measured_trace(
                pseudo,
                spec,
                policy,
                max_rollout_steps=max_rollout_steps,
            )
            trace_rows.extend(rows)
            snapshots.extend(snapshot_rows)
            attempts.append(attempt)
    candidates = build_pair_candidates(
        snapshots,
        specs_by_id,
        max_pair_candidates=max_pair_candidates,
    )
    accepted_pairs = select_diverse_pairs(candidates)
    candidate_rows = _asdict_rows(candidates)
    accepted_keys = {
        (
            row.left_calibration_id,
            row.right_calibration_id,
            row.left_anchor_step,
            row.right_anchor_step,
        )
        for row in accepted_pairs
    }
    for row in candidate_rows:
        row["accepted"] = (
            row["left_calibration_id"],
            row["right_calibration_id"],
            row["left_anchor_step"],
            row["right_anchor_step"],
        ) in accepted_keys
        row["rejection_reason"] = "" if row["accepted"] else "not_selected_by_diversity_round_robin"
    summary = build_summary(
        source_rows=source_rows,
        specs=specs,
        attempts=attempts,
        snapshots=snapshots,
        candidates=candidates,
        accepted_pairs=accepted_pairs,
        max_pair_candidates=max_pair_candidates,
    )
    write_csv_rows(output / "admitted_calibrated_rows.csv", _asdict_rows(admitted_rows))
    write_csv_rows(output / "source_spec_rows.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "measured_trace_rows.csv", trace_rows)
    write_csv_rows(output / "measured_snapshot_rows.csv", _asdict_rows(snapshots))
    write_csv_rows(output / "measured_trace_attempt_rows.csv", _asdict_rows(attempts))
    write_csv_rows(output / "pair_candidate_rows.csv", candidate_rows)
    write_csv_rows(output / "accepted_pair_rows.csv", _asdict_rows(accepted_pairs))
    write_csv_rows(output / "pair_family_summary.csv", build_pair_family_summary(accepted_pairs))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run calibrated pair-expansion planner smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--accepted-calibrated-rows", type=Path, default=DEFAULT_ACCEPTED_CALIBRATED_ROWS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=3)
    parser.add_argument("--max-base-rows", type=int, default=24)
    parser.add_argument("--max-calibration-specs", type=int, default=240)
    parser.add_argument("--max-pair-candidates", type=int, default=256)
    parser.add_argument("--max-rollout-steps", type=int, default=128)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_calibrated_pair_expansion_planner_smoke(
        args.output_dir,
        accepted_calibrated_rows=args.accepted_calibrated_rows,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_base_rows=int(args.max_base_rows),
        max_calibration_specs=int(args.max_calibration_specs),
        max_pair_candidates=int(args.max_pair_candidates),
        max_rollout_steps=int(args.max_rollout_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"accepted_pair_count={summary['accepted_pair_count']}")
    print(f"accepted_source_family_edge_count={summary['accepted_source_family_edge_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
