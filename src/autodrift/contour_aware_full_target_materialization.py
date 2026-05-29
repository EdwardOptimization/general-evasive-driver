"""Full contour-aware policy-target materialization."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_tensor_capture_dry_run import (
    CapturedTensorRow,
    _all_tensor_values_finite,
    _arrays_from_captured,
    _rows_by_id,
    _sha256,
    _shape_rows,
    _variant_index,
    capture_target_tensors,
)
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


DEFAULT_CANDIDATE_RUN_DIR = Path("runs/m1615_contour_aware_candidate_corpus")
DEFAULT_REPLAY_RUN_DIR = Path("runs/m1609_diagnostic_complete_bounded_replay")
DEFAULT_RUN_DIR = Path("runs/m1630_contour_aware_full_target_materialization")
EXPECTED_POSITIVE_COUNT = 39
EXPECTED_DIAGNOSTIC_COUNT = 232
ACTION_L2_TOLERANCE = 1e-6
FORBIDDEN_GUARDRAILS = {
    "training_ready": False,
    "training_corpus_exported": False,
    "loss_constructed": False,
    "objective_constructed": False,
    "training_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


CaptureFunction = Callable[
    [Sequence[Mapping[str, Any]], Mapping[str, Mapping[str, Any]], Mapping[tuple[str, str], Mapping[str, Any]], Path, str],
    tuple[list[CapturedTensorRow], list[dict[str, Any]], list[dict[str, Any]]],
]


def _float(value: Any) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return output if math.isfinite(output) else float("nan")


def _with_full_role(rows: Sequence[Mapping[str, Any]], *, role: str, role_weight: float) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["corpus_role"] = role
        item["used_as_positive"] = role == POSITIVE_ROLE
        item["role_weight"] = float(role_weight)
        item["public_proof_artifact"] = True
        item["training_ready"] = False
        output.append(item)
    return output


def _split_captured(rows: Sequence[CapturedTensorRow]) -> tuple[list[CapturedTensorRow], list[CapturedTensorRow]]:
    positives: list[CapturedTensorRow] = []
    diagnostics: list[CapturedTensorRow] = []
    for row in rows:
        role = str(row.metadata.get("corpus_role", ""))
        if role == POSITIVE_ROLE:
            positives.append(row)
        elif role == DIAGNOSTIC_ROLE:
            diagnostics.append(row)
    return positives, diagnostics


def _shape_rows_for_group(group: str, arrays: Mapping[str, np.ndarray]) -> list[dict[str, Any]]:
    return [dict(row, corpus_role=group) for row in _shape_rows(arrays)]


def _source_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((str(row.get("corpus_role", "")), str(row.get("source_run", ""))) for row in rows)
    output: list[dict[str, Any]] = []
    for (role, source_run), count in sorted(counts.items()):
        total_for_role = sum(value for (item_role, _), value in counts.items() if item_role == role)
        output.append(
            {
                "corpus_role": role,
                "source_run": source_run,
                "row_count": count,
                "share": count / total_for_role if total_for_role else 0.0,
            }
        )
    return output


def _max_action_l2(rows: Sequence[Mapping[str, Any]]) -> float:
    values: list[float] = []
    for row in rows:
        for key in (
            "source_preferred_action_l2",
            "source_wrong_history_action_l2",
            "source_donor_plus_hidden_action_l2",
        ):
            value = _float(row.get(key))
            if math.isfinite(value):
                values.append(value)
    return max(values) if values else float("nan")


def _hidden_shapes_ok(arrays: Mapping[str, np.ndarray], *, expected_rows: int, hidden_dim: int) -> bool:
    return (
        hidden_dim > 0
        and list(arrays["correct_hidden"].shape) == [expected_rows, hidden_dim]
        and list(arrays["wrong_hidden"].shape) == [expected_rows, hidden_dim]
    )


def _guardrail_summary_rows() -> list[dict[str, Any]]:
    return [{"guardrail": key, "violated": value, "value": value} for key, value in FORBIDDEN_GUARDRAILS.items()]


def run_contour_aware_full_target_materialization(
    *,
    candidate_run_dir: Path | str,
    replay_run_dir: Path | str,
    checkpoint: Path | str,
    run_dir: Path | str,
    seed: int = 1901,
    seed_count: int = 6,
    max_source_specs: int = 480,
    max_anchor_candidates: int = 640,
    device: str = "cpu",
    expected_positive_count: int = EXPECTED_POSITIVE_COUNT,
    expected_diagnostic_count: int = EXPECTED_DIAGNOSTIC_COUNT,
    capture_fn: CaptureFunction | None = None,
) -> dict[str, Any]:
    """Materialize policy-side tensors for the full public contour-aware package."""

    candidate_dir = Path(candidate_run_dir)
    replay_dir = Path(replay_run_dir)
    checkpoint_path = Path(checkpoint)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    checksum_before = _sha256(checkpoint_path)

    positive_input_rows = _with_full_role(
        read_csv_rows(candidate_dir / "positive_candidate_rows.csv"),
        role=POSITIVE_ROLE,
        role_weight=1.0,
    )
    diagnostic_input_rows = _with_full_role(
        read_csv_rows(candidate_dir / "diagnostic_guardrail_rows.csv"),
        role=DIAGNOSTIC_ROLE,
        role_weight=0.0,
    )
    selected_rows = positive_input_rows + diagnostic_input_rows
    replay_rows = read_csv_rows(replay_dir / "replay_pair_rows.csv")
    intervention_rows = read_csv_rows(replay_dir / "intervention_rows.csv")
    replay_rows_by_id = _rows_by_id(replay_rows)
    variants_by_pair = _variant_index(intervention_rows)

    if capture_fn is None:
        captured, trace_rows, missing_rows = capture_target_tensors(
            selected_rows=selected_rows,
            replay_rows_by_id=replay_rows_by_id,
            intervention_rows_by_pair_variant=variants_by_pair,
            checkpoint=checkpoint_path,
            seed=seed,
            seed_count=seed_count,
            max_source_specs=max_source_specs,
            max_anchor_candidates=max_anchor_candidates,
            device=device,
        )
    else:
        captured, trace_rows, missing_rows = capture_fn(
            selected_rows,
            replay_rows_by_id,
            variants_by_pair,
            checkpoint_path,
            device,
        )

    positive_captured, diagnostic_captured = _split_captured(captured)
    positive_arrays = _arrays_from_captured(positive_captured)
    diagnostic_arrays = _arrays_from_captured(diagnostic_captured)
    positive_rows = [row.metadata for row in positive_captured]
    diagnostic_rows = [row.metadata for row in diagnostic_captured]
    all_metadata = positive_rows + diagnostic_rows

    checksum_after = _sha256(checkpoint_path)
    checkpoint_weights_mutated = checksum_before != checksum_after
    positive_hidden_dim = int(positive_arrays["correct_hidden"].shape[1]) if positive_arrays["correct_hidden"].ndim == 2 else 0
    diagnostic_hidden_dim = (
        int(diagnostic_arrays["correct_hidden"].shape[1]) if diagnostic_arrays["correct_hidden"].ndim == 2 else 0
    )
    hidden_dim = positive_hidden_dim if positive_hidden_dim == diagnostic_hidden_dim else 0
    diagnostic_positive_weight_sum = sum(_float(row.get("role_weight", 0.0)) for row in diagnostic_rows if bool(row.get("used_as_positive", False)))
    diagnostic_rows_used_as_positive = any(
        bool(row.get("used_as_positive", False)) or _float(row.get("role_weight", 0.0)) != 0.0
        for row in diagnostic_rows
    )
    positive_source_action_l2_max = _max_action_l2(positive_rows)
    diagnostic_source_action_l2_max = _max_action_l2(diagnostic_rows)
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    positive_all_finite = _all_tensor_values_finite(positive_arrays)
    diagnostic_all_finite = _all_tensor_values_finite(diagnostic_arrays)
    summary = {
        "result_class": "contour_aware_full_target_materialization",
        "candidate_run_dir": str(candidate_dir),
        "replay_run_dir": str(replay_dir),
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256_before": checksum_before,
        "checkpoint_sha256_after": checksum_after,
        "checkpoint_weights_mutated": bool(checkpoint_weights_mutated),
        "positive_input_row_count": len(positive_input_rows),
        "diagnostic_input_row_count": len(diagnostic_input_rows),
        "positive_policy_target_count": len(positive_captured),
        "diagnostic_policy_guardrail_count": len(diagnostic_captured),
        "missing_capture_row_count": len(missing_rows),
        "positive_observation_shape": list(positive_arrays["observation"].shape),
        "diagnostic_observation_shape": list(diagnostic_arrays["observation"].shape),
        "positive_preferred_action_shape": list(positive_arrays["preferred_action"].shape),
        "positive_wrong_history_action_shape": list(positive_arrays["wrong_history_action"].shape),
        "positive_donor_plus_hidden_action_shape": list(positive_arrays["donor_plus_hidden_action"].shape),
        "diagnostic_preferred_action_shape": list(diagnostic_arrays["preferred_action"].shape),
        "diagnostic_wrong_history_action_shape": list(diagnostic_arrays["wrong_history_action"].shape),
        "diagnostic_donor_plus_hidden_action_shape": list(diagnostic_arrays["donor_plus_hidden_action"].shape),
        "hidden_dim": hidden_dim,
        "positive_hidden_shapes_ok": _hidden_shapes_ok(
            positive_arrays,
            expected_rows=int(expected_positive_count),
            hidden_dim=hidden_dim,
        ),
        "diagnostic_hidden_shapes_ok": _hidden_shapes_ok(
            diagnostic_arrays,
            expected_rows=int(expected_diagnostic_count),
            hidden_dim=hidden_dim,
        ),
        "positive_all_tensor_values_finite": bool(positive_all_finite),
        "diagnostic_all_tensor_values_finite": bool(diagnostic_all_finite),
        "all_tensor_values_finite": bool(positive_all_finite and diagnostic_all_finite),
        "positive_source_action_l2_max": positive_source_action_l2_max,
        "diagnostic_source_action_l2_max": diagnostic_source_action_l2_max,
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "diagnostic_positive_weight_sum": diagnostic_positive_weight_sum,
        "policy_target_materialized": len(positive_captured) == int(expected_positive_count)
        and len(diagnostic_captured) == int(expected_diagnostic_count),
        "materialization_only": True,
        "guardrail_violation_count": int(guardrail_violation_count),
        **FORBIDDEN_GUARDRAILS,
    }
    positive_actions_ok = (
        list(summary["positive_preferred_action_shape"]) == [int(expected_positive_count), 3]
        and list(summary["positive_wrong_history_action_shape"]) == [int(expected_positive_count), 3]
        and list(summary["positive_donor_plus_hidden_action_shape"]) == [int(expected_positive_count), 3]
    )
    diagnostic_actions_ok = (
        list(summary["diagnostic_preferred_action_shape"]) == [int(expected_diagnostic_count), 3]
        and list(summary["diagnostic_wrong_history_action_shape"]) == [int(expected_diagnostic_count), 3]
        and list(summary["diagnostic_donor_plus_hidden_action_shape"]) == [int(expected_diagnostic_count), 3]
    )
    summary["passes_public_smoke_gates"] = (
        int(summary["positive_input_row_count"]) == int(expected_positive_count)
        and int(summary["diagnostic_input_row_count"]) == int(expected_diagnostic_count)
        and int(summary["positive_policy_target_count"]) == int(expected_positive_count)
        and int(summary["diagnostic_policy_guardrail_count"]) == int(expected_diagnostic_count)
        and list(summary["positive_observation_shape"]) == [int(expected_positive_count), HUMAN_VIEW_OBS_DIM]
        and list(summary["diagnostic_observation_shape"]) == [int(expected_diagnostic_count), HUMAN_VIEW_OBS_DIM]
        and positive_actions_ok
        and diagnostic_actions_ok
        and bool(summary["positive_hidden_shapes_ok"])
        and bool(summary["diagnostic_hidden_shapes_ok"])
        and int(summary["hidden_dim"]) > 0
        and bool(summary["all_tensor_values_finite"])
        and int(summary["missing_capture_row_count"]) == 0
        and float(summary["positive_source_action_l2_max"]) <= ACTION_L2_TOLERANCE
        and float(summary["diagnostic_source_action_l2_max"]) <= ACTION_L2_TOLERANCE
        and not bool(summary["diagnostic_rows_used_as_positive"])
        and float(summary["diagnostic_positive_weight_sum"]) == 0.0
        and not bool(summary["checkpoint_weights_mutated"])
        and bool(summary["policy_target_materialized"])
        and bool(summary["materialization_only"])
        and not bool(summary["training_ready"])
        and not bool(summary["training_corpus_exported"])
        and not bool(summary["loss_constructed"])
        and not bool(summary["objective_constructed"])
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
        and int(summary["guardrail_violation_count"]) == 0
    )
    if int(summary["missing_capture_row_count"]) > 0:
        null_class = "tensor_capture_missing_rows"
    elif int(summary["positive_policy_target_count"]) != int(expected_positive_count):
        null_class = "positive_target_count_mismatch"
    elif int(summary["diagnostic_policy_guardrail_count"]) != int(expected_diagnostic_count):
        null_class = "diagnostic_guardrail_count_mismatch"
    elif not bool(summary["all_tensor_values_finite"]):
        null_class = "nonfinite_tensor_failure"
    elif bool(summary["diagnostic_rows_used_as_positive"]):
        null_class = "diagnostic_positive_leakage"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_full_target_materialization_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class

    shape_rows = _shape_rows_for_group(POSITIVE_ROLE, positive_arrays) + _shape_rows_for_group(
        DIAGNOSTIC_ROLE,
        diagnostic_arrays,
    )
    write_csv_rows(output / "positive_policy_target_rows.csv", positive_rows)
    write_csv_rows(output / "diagnostic_policy_guardrail_rows.csv", diagnostic_rows)
    write_csv_rows(output / "capture_traceability_rows.csv", trace_rows)
    write_csv_rows(output / "shape_summary.csv", shape_rows)
    write_csv_rows(output / "source_summary.csv", _source_summary_rows(all_metadata))
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_summary_rows())
    write_csv_rows(
        output / "missing_capture_rows.csv",
        missing_rows,
        fieldnames=["pair_id", "corpus_role", "source_run", "missing_reasons"],
    )
    if bool(summary["passes_public_smoke_gates"]):
        np.savez_compressed(output / "positive_policy_targets.npz", **positive_arrays)
        np.savez_compressed(output / "diagnostic_policy_guardrails.npz", **diagnostic_arrays)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full contour-aware policy-target materialization.")
    parser.add_argument("--candidate-run-dir", type=Path, default=DEFAULT_CANDIDATE_RUN_DIR)
    parser.add_argument("--replay-run-dir", type=Path, default=DEFAULT_REPLAY_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--seed", type=int, default=1901)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=480)
    parser.add_argument("--max-anchor-candidates", type=int, default=640)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_contour_aware_full_target_materialization(
        candidate_run_dir=args.candidate_run_dir,
        replay_run_dir=args.replay_run_dir,
        checkpoint=args.checkpoint,
        run_dir=args.run_dir,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchor_candidates=int(args.max_anchor_candidates),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"positive_policy_target_count={summary['positive_policy_target_count']}")
    print(f"diagnostic_policy_guardrail_count={summary['diagnostic_policy_guardrail_count']}")
    print(f"hidden_dim={summary['hidden_dim']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
