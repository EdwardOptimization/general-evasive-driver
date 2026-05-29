"""Pair-expanded calibrated terminal-boundary history interventions."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_pair_expansion_planner import expanded_terminal_source_rows
from autodrift.calibrated_terminal_boundary_history_interventions import (
    CalibratedMeasuredPair,
    run_intervention_variant,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.fresh_ambiguity_history_interventions import (
    VARIANTS,
    build_pair_summary,
    build_variant_summary,
    finalize_rows,
)
from autodrift.terminal_boundary_task_sampling_calibration import (
    CalibrationSpec,
    build_calibration_specs,
)


DEFAULT_ACCEPTED_PAIR_ROWS = Path("runs/m1550_calibrated_pair_expansion_planner_smoke/accepted_pair_rows.csv")
DEFAULT_RUN_DIR = Path("runs/m1553_pair_expanded_calibrated_history_intervention_smoke")
TERMINAL_MARGIN_GAP_THRESHOLD = 0.02
CONTROL_TO_HISTORY_RATIO_MAX = 4.0
GUARDRAILS = {
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
HISTORY_VARIANTS = {
    "wrong_history_donor_hidden_at_anchor",
    "donor_response_action_plus_hidden_from_anchor",
}
CONTROL_VARIANTS = {
    "reset_hidden_once_at_anchor",
    "reset_hidden_every_step_from_anchor",
    "zero_current_response_from_anchor",
    "zero_action_history_from_anchor",
}


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _to_bool(value: Any) -> bool:
    return str(value).lower() == "true" if isinstance(value, str) else bool(value)


def _source_edge(left: str, right: str) -> str:
    return "|".join(sorted((str(left), str(right))))


def _endpoint_key(calibration_id: str, anchor_step: int) -> str:
    return f"{calibration_id}@{int(anchor_step)}"


def load_pair_expanded_pairs(path: Path | str = DEFAULT_ACCEPTED_PAIR_ROWS, *, max_pairs: int | None = None) -> list[CalibratedMeasuredPair]:
    """Load accepted M1550 pair-expanded calibrated pairs."""

    pairs: list[CalibratedMeasuredPair] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if "accepted" in row and not _to_bool(row.get("accepted")):
                continue
            pairs.append(
                CalibratedMeasuredPair(
                    pair_id=str(row["pair_id"]),
                    left_calibration_id=str(row["left_calibration_id"]),
                    right_calibration_id=str(row["right_calibration_id"]),
                    left_source_family=str(row["left_source_family"]),
                    right_source_family=str(row["right_source_family"]),
                    left_window_kind=str(row["left_window_kind"]),
                    right_window_kind=str(row["right_window_kind"]),
                    left_anchor_step=int(row["left_anchor_step"]),
                    right_anchor_step=int(row["right_anchor_step"]),
                    scene_context_distance=_to_float(row["scene_context_distance"]),
                    current_ego_distance=_to_float(row["current_ego_distance"]),
                    first_action_l2=_to_float(row["first_action_l2"]),
                    terminal_margin_gap=_to_float(row["terminal_margin_gap"]),
                    window_pair_kind=str(row["window_pair_kind"]),
                )
            )
            if max_pairs is not None and len(pairs) >= int(max_pairs):
                break
    return pairs


def reconstruct_specs_by_id(*, seed: int = 1843, seed_count: int = 3, max_base_rows: int = 24, max_calibration_specs: int = 240) -> dict[str, CalibrationSpec]:
    """Rebuild M1550 calibration specs by id."""

    source_rows = expanded_terminal_source_rows(seed=seed, seed_count=seed_count, max_base_rows=max_base_rows)
    specs = build_calibration_specs(source_rows, max_calibration_specs=max_calibration_specs)
    return {spec.artifact_row.calibration_id: spec for spec in specs}


def input_endpoint_counts(pairs: Sequence[CalibratedMeasuredPair]) -> Counter[str]:
    """Count endpoint reuse in accepted pair inputs."""

    counts: Counter[str] = Counter()
    for pair in pairs:
        counts[_endpoint_key(pair.left_calibration_id, pair.left_anchor_step)] += 1
        counts[_endpoint_key(pair.right_calibration_id, pair.right_anchor_step)] += 1
    return counts


def _pair_edge(pair: CalibratedMeasuredPair) -> str:
    return _source_edge(pair.left_source_family, pair.right_source_family)


def _row_edge(row: dict[str, Any]) -> str:
    target = str(row.get("target_source_family", ""))
    donor = str(row.get("donor_source_family", ""))
    return _source_edge(target, donor) if target and donor else target


def _pair_endpoint(pair: CalibratedMeasuredPair, side: str) -> str:
    if side == "left":
        return _endpoint_key(pair.left_calibration_id, pair.left_anchor_step)
    return _endpoint_key(pair.right_calibration_id, pair.right_anchor_step)


def _positive_history_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("variant", "")) in HISTORY_VARIANTS
        and float(row.get("terminal_margin_gap_from_normal") or 0.0) >= TERMINAL_MARGIN_GAP_THRESHOLD
    ]


def _positive_control_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("variant", "")) in CONTROL_VARIANTS
        and float(row.get("terminal_margin_gap_from_normal") or 0.0) >= TERMINAL_MARGIN_GAP_THRESHOLD
    ]


def _max_gap(rows: Sequence[dict[str, Any]], variants: set[str]) -> float:
    return max(
        (float(row.get("terminal_margin_gap_from_normal") or 0.0) for row in rows if str(row.get("variant", "")) in variants),
        default=0.0,
    )


def build_source_edge_summary(pairs: Sequence[CalibratedMeasuredPair], rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize pair and intervention effects by source-family edge."""

    pair_counts = Counter(_pair_edge(pair) for pair in pairs)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_row_edge(row)].append(row)
    result: list[dict[str, Any]] = []
    for edge in sorted(set(pair_counts) | set(grouped)):
        group = grouped.get(edge, [])
        history_positive = _positive_history_rows(group)
        control_positive = _positive_control_rows(group)
        result.append(
            {
                "source_family_edge": edge,
                "pair_count": pair_counts.get(edge, 0),
                "intervention_row_count": len(group),
                "history_positive_count": len(history_positive),
                "control_positive_count": len(control_positive),
                "success_drop_count": sum(1 for row in group if bool(row.get("success_drop_from_normal", False))),
                "max_history_margin_gap": _max_gap(group, HISTORY_VARIANTS),
                "max_control_margin_gap": _max_gap(group, CONTROL_VARIANTS),
            }
        )
    return result


def build_endpoint_summary(pairs: Sequence[CalibratedMeasuredPair], rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize input and positive endpoint concentration."""

    pair_by_id = {pair.pair_id: pair for pair in pairs}
    input_counts = input_endpoint_counts(pairs)
    target_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        pair = pair_by_id.get(str(row.get("pair_id", "")))
        if pair is None:
            continue
        endpoint = _pair_endpoint(pair, str(row.get("target_side", "")))
        target_rows[endpoint].append(row)
    result: list[dict[str, Any]] = []
    for endpoint in sorted(set(input_counts) | set(target_rows)):
        group = target_rows.get(endpoint, [])
        result.append(
            {
                "endpoint": endpoint,
                "pair_endpoint_count": input_counts.get(endpoint, 0),
                "target_row_count": len(group),
                "history_positive_count": len(_positive_history_rows(group)),
                "control_positive_count": len(_positive_control_rows(group)),
                "max_history_margin_gap": _max_gap(group, HISTORY_VARIANTS),
                "max_control_margin_gap": _max_gap(group, CONTROL_VARIANTS),
            }
        )
    return result


def build_window_bucket_summary(pairs: Sequence[CalibratedMeasuredPair], rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize pair and positive counts by window bucket."""

    pair_by_id = {pair.pair_id: pair for pair in pairs}
    pair_counts = Counter(pair.window_pair_kind for pair in pairs)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        pair = pair_by_id.get(str(row.get("pair_id", "")))
        if pair is not None:
            grouped[pair.window_pair_kind].append(row)
    result: list[dict[str, Any]] = []
    for bucket in sorted(set(pair_counts) | set(grouped)):
        group = grouped.get(bucket, [])
        result.append(
            {
                "window_pair_kind": bucket,
                "pair_count": pair_counts.get(bucket, 0),
                "intervention_row_count": len(group),
                "history_positive_count": len(_positive_history_rows(group)),
                "control_positive_count": len(_positive_control_rows(group)),
                "max_history_margin_gap": _max_gap(group, HISTORY_VARIANTS),
                "max_control_margin_gap": _max_gap(group, CONTROL_VARIANTS),
            }
        )
    return result


def _max_share(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return max((count / max(1, total) for count in counts.values()), default=0.0)


def _nonfinite_action_count(rows: Sequence[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        if row.get("target_replay_status") != "ok":
            continue
        values = [
            _to_float(row.get("first_action_steer")),
            _to_float(row.get("first_action_throttle")),
            _to_float(row.get("first_action_brake")),
        ]
        if not all(np.isfinite(value) for value in values):
            count += 1
    return count


def build_summary(*, pairs: Sequence[CalibratedMeasuredPair], rows: Sequence[dict[str, Any]], continuation_steps: int) -> dict[str, Any]:
    """Build pair-expanded calibrated intervention summary."""

    guardrails = dict(GUARDRAILS)
    edge_counts = Counter(_pair_edge(pair) for pair in pairs)
    endpoint_counts = input_endpoint_counts(pairs)
    window_counts = Counter(pair.window_pair_kind for pair in pairs)
    positive_history = _positive_history_rows(rows)
    positive_controls = _positive_control_rows(rows)
    positive_edge_counts = Counter(_row_edge(row) for row in positive_history)
    pair_by_id = {pair.pair_id: pair for pair in pairs}
    positive_endpoint_counts: Counter[str] = Counter()
    for row in positive_history:
        pair = pair_by_id.get(str(row.get("pair_id", "")))
        if pair is not None:
            positive_endpoint_counts[_pair_endpoint(pair, str(row.get("target_side", "")))] += 1
    history_max = _max_gap(rows, HISTORY_VARIANTS)
    control_max = _max_gap(rows, CONTROL_VARIANTS)
    ratio = None if history_max <= 0.0 else control_max / history_max
    failure_count = sum(1 for row in rows if row.get("target_replay_status") != "ok")
    expected_rows = len(pairs) * 2 * len(VARIANTS)
    success_drop_count = sum(1 for row in rows if str(row.get("variant", "")) in HISTORY_VARIANTS and bool(row.get("success_drop_from_normal", False)))
    summary = {
        "result_class": "pair_expanded_calibrated_history_intervention_smoke",
        "accepted_pair_count": len(pairs),
        "accepted_source_family_edge_count": len(edge_counts),
        "max_single_pair_source_edge_share": _max_share(edge_counts),
        "max_endpoint_share": _max_share(endpoint_counts),
        "accepted_window_bucket_count": len(window_counts),
        "target_side_count": len({(row.get("pair_id"), row.get("target_side")) for row in rows}),
        "variant_count": len(VARIANTS),
        "expected_intervention_row_count": expected_rows,
        "intervention_row_count": len(rows),
        "continuation_steps": int(continuation_steps),
        "anchor_replay_failure_count": failure_count,
        "anchor_replay_failure_rate": failure_count / max(1, len(rows)),
        "nonfinite_action_count": _nonfinite_action_count(rows),
        "terminal_wrong_history_positive_target_sides": sum(
            1 for row in positive_history if row.get("variant") == "wrong_history_donor_hidden_at_anchor"
        ),
        "terminal_donor_plus_hidden_positive_target_sides": sum(
            1 for row in positive_history if row.get("variant") == "donor_response_action_plus_hidden_from_anchor"
        ),
        "terminal_donor_stream_positive_target_sides": sum(
            1
            for row in rows
            if row.get("variant") == "donor_response_action_stream_from_anchor"
            and float(row.get("terminal_margin_gap_from_normal") or 0.0) >= TERMINAL_MARGIN_GAP_THRESHOLD
        ),
        "terminal_wrong_or_donor_success_drop_count": success_drop_count,
        "terminal_max_history_margin_gap": history_max,
        "terminal_max_control_margin_gap": control_max,
        "terminal_control_to_history_gap_ratio": ratio,
        "positive_history_count": len(positive_history),
        "positive_control_count": len(positive_controls),
        "positive_max_single_source_edge_share": _max_share(positive_edge_counts),
        "positive_max_single_endpoint_share": _max_share(positive_endpoint_counts),
        "source_family_edge_counts": dict(sorted(edge_counts.items())),
        "endpoint_counts": dict(sorted(endpoint_counts.items())),
        "window_pair_kind_counts": dict(sorted(window_counts.items())),
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        **guardrails,
    }
    summary["passes_input_pair_gates"] = (
        int(summary["accepted_pair_count"]) >= 16
        and int(summary["accepted_source_family_edge_count"]) >= 5
        and float(summary["max_single_pair_source_edge_share"]) <= 0.40
        and float(summary["max_endpoint_share"]) <= 0.20
        and int(summary["accepted_window_bucket_count"]) >= 3
    )
    summary["passes_replay_gates"] = (
        int(summary["intervention_row_count"]) >= 400
        and float(summary["anchor_replay_failure_rate"]) <= 0.05
        and int(summary["nonfinite_action_count"]) == 0
        and int(summary["guardrail_violation_count"]) == 0
    )
    summary["passes_history_positive_gates"] = (
        int(summary["terminal_wrong_history_positive_target_sides"])
        + int(summary["terminal_donor_plus_hidden_positive_target_sides"])
        >= 4
        or int(summary["terminal_wrong_or_donor_success_drop_count"]) >= 2
    )
    summary["passes_control_gate"] = ratio is None or ratio <= CONTROL_TO_HISTORY_RATIO_MAX
    summary["passes_concentration_gates"] = (
        len(positive_history) > 0
        and float(summary["positive_max_single_source_edge_share"]) <= 0.50
        and float(summary["positive_max_single_endpoint_share"]) <= 0.25
    )
    summary["passes_public_smoke_gates"] = bool(summary["passes_input_pair_gates"]) and bool(summary["passes_replay_gates"])
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and bool(summary["passes_history_positive_gates"])
        and bool(summary["passes_control_gate"])
        and bool(summary["passes_concentration_gates"])
    )
    return summary


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row) for row in rows]


def _guardrail_rows() -> list[dict[str, Any]]:
    return [{"guardrail": key, "violated": value} for key, value in GUARDRAILS.items()]


def run_pair_expanded_calibrated_history_intervention_smoke(
    output_dir: Path | str,
    *,
    accepted_pair_rows: Path | str = DEFAULT_ACCEPTED_PAIR_ROWS,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 3,
    max_base_rows: int = 24,
    max_calibration_specs: int = 240,
    max_pairs: int = 21,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded pair-expanded calibrated history intervention smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pairs = load_pair_expanded_pairs(accepted_pair_rows, max_pairs=max_pairs)
    spec_by_id = reconstruct_specs_by_id(
        seed=seed,
        seed_count=seed_count,
        max_base_rows=max_base_rows,
        max_calibration_specs=max_calibration_specs,
    )
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    intervention_rows: list[dict[str, Any]] = []
    missing_specs: list[dict[str, Any]] = []
    for pair in pairs:
        left_spec = spec_by_id.get(pair.left_calibration_id)
        right_spec = spec_by_id.get(pair.right_calibration_id)
        if left_spec is None or right_spec is None:
            missing_specs.append(
                {
                    "pair_id": pair.pair_id,
                    "left_calibration_id": pair.left_calibration_id,
                    "right_calibration_id": pair.right_calibration_id,
                    "left_missing": left_spec is None,
                    "right_missing": right_spec is None,
                }
            )
            continue
        for target_side, target_spec, target_anchor, donor_side, donor_spec, donor_anchor in (
            ("left", left_spec, pair.left_anchor_step, "right", right_spec, pair.right_anchor_step),
            ("right", right_spec, pair.right_anchor_step, "left", left_spec, pair.left_anchor_step),
        ):
            for variant in VARIANTS:
                intervention_rows.append(
                    run_intervention_variant(
                        pair=pair,
                        target_side=target_side,
                        target_spec=target_spec,
                        target_anchor_step=target_anchor,
                        donor_side=donor_side,
                        donor_spec=donor_spec,
                        donor_anchor_step=donor_anchor,
                        variant=variant,
                        model=model,
                        continuation_steps=continuation_steps,
                    )
                )
    finalized = finalize_rows(intervention_rows)
    pair_summary = build_pair_summary(finalized)
    variant_summary = build_variant_summary(finalized)
    source_edge_summary = build_source_edge_summary(pairs, finalized)
    endpoint_summary = build_endpoint_summary(pairs, finalized)
    window_summary = build_window_bucket_summary(pairs, finalized)
    summary = build_summary(pairs=pairs, rows=finalized, continuation_steps=continuation_steps)
    summary["missing_spec_count"] = len(missing_specs)
    summary["passes_spec_reconstruction_gate"] = len(missing_specs) == 0
    summary["passes_public_smoke_gates"] = bool(summary["passes_public_smoke_gates"]) and len(missing_specs) == 0
    summary["passes_evidence_quality_targets"] = bool(summary["passes_evidence_quality_targets"]) and len(missing_specs) == 0
    write_csv_rows(output / "accepted_pair_rows.csv", _asdict_rows(pairs))
    write_csv_rows(output / "missing_spec_rows.csv", missing_specs)
    write_csv_rows(output / "intervention_rows.csv", finalized)
    write_csv_rows(output / "pair_summary.csv", pair_summary)
    write_csv_rows(output / "variant_summary.csv", variant_summary)
    write_csv_rows(output / "source_edge_summary.csv", source_edge_summary)
    write_csv_rows(output / "endpoint_summary.csv", endpoint_summary)
    write_csv_rows(output / "window_bucket_summary.csv", window_summary)
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows())
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pair-expanded calibrated history intervention smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--accepted-pair-rows", type=Path, default=DEFAULT_ACCEPTED_PAIR_ROWS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=3)
    parser.add_argument("--max-base-rows", type=int, default=24)
    parser.add_argument("--max-calibration-specs", type=int, default=240)
    parser.add_argument("--max-pairs", type=int, default=21)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_pair_expanded_calibrated_history_intervention_smoke(
        args.output_dir,
        accepted_pair_rows=args.accepted_pair_rows,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_base_rows=int(args.max_base_rows),
        max_calibration_specs=int(args.max_calibration_specs),
        max_pairs=int(args.max_pairs),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"accepted_pair_count={summary['accepted_pair_count']}")
    print(f"intervention_row_count={summary['intervention_row_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"passes_evidence_quality_targets={summary['passes_evidence_quality_targets']}")


if __name__ == "__main__":
    main()
