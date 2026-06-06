"""Materialize M2861 response-prediction trace localization rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import json
from math import sqrt
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2861-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "response-prediction-trace-localization-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2862-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "response-prediction-trace-localization-materialization-result-audit"
)
DEFAULT_M2862_NEXT_BLOCKER = (
    "m2863-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "response-prediction-localization-branch-synthesis"
)
DEFAULT_M2860_AUDIT = Path(
    "docs/m2860-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "response-prediction-trace-instrumentation-repair-result-audit.md"
)
DEFAULT_M2859_SUMMARY = Path(
    "runs/m2859_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_instrumentation_repair/summary.json"
)
DEFAULT_TRACE_ROWS = Path(
    "runs/m2859_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_instrumentation_repair/response_prediction_trace_rows.csv"
)
DEFAULT_EPISODE_ROWS = Path(
    "runs/m2859_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_instrumentation_repair/response_prediction_episode_rows.csv"
)
DEFAULT_GAP_ROWS = Path(
    "runs/m2859_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_instrumentation_repair/instrumentation_gap_rows.csv"
)
DEFAULT_M2857_LOCALIZATION_ROWS = Path(
    "runs/m2857_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "per_step_telemetry_panel_materialization/telemetry_localization_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2861_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_localization_materialization"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2861-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "response-prediction-trace-localization-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2862-engineering-controller-route-a-response-predictive-"
    "recurrent-belief-response-prediction-trace-localization-materialization-result-audit.json"
)

RESPONSE_CHANNEL_NAMES = [
    "vx_norm",
    "vy_norm",
    "yaw_rate_norm",
    "ax_norm",
    "ay_norm",
    "steer_actuator_norm",
    "steer_rate_norm",
    "throttle_actuator",
    "brake_actuator",
]
ACTUATOR_CHANNELS = {
    "steer_actuator_norm",
    "steer_rate_norm",
    "throttle_actuator",
    "brake_actuator",
}
CLAIM_SCOPE = (
    "M2861 existing-artifact response-prediction trace localization only. It "
    "reads M2859 trace episode and gap rows plus M2857 localization rows and "
    "writes derived diagnostic localization artifacts. It does not rerun the "
    "environment, execute reset/step/rollout/replay, train, run PPO, validate, "
    "rank, select a winner, promote a checkpoint, compute success-rate verdicts, "
    "claim repair success, driver performance, paper evidence, finite-window-vs-GRU "
    "evidence, current-sim verdict, high-fidelity validation, full ideal driver "
    "completion, or level3 self-identification."
)
FORBIDDEN_INTERPRETATION = (
    "validation readiness or result, checkpoint ranking, controller ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, repair success, "
    "driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, "
    "or level3 self-identification"
)

LOCALIZATION_FIELDNAMES = [
    "surface_id",
    "pair_id",
    "task_source_id",
    "profile_name",
    "checkpoint_subject",
    "horizon_index",
    "response_channel_index",
    "response_channel_name",
    "valid_prediction_count",
    "gap_count",
    "total_trace_count",
    "gap_fraction",
    "error_abs_mean",
    "error_abs_max",
    "error_signed_mean",
    "error_rmse",
    "relative_error_rank",
    "localization_bucket",
    "m2857_per_step_localization_bucket",
    "m2857_training_recipe_signal",
    "recipe_signal",
    "requires_recipe_design",
    "diagnostic_only",
    "actor_visible_allowed",
    "future_label_actor_visible",
    "hidden_oracle_actor_input_required",
    "ranking_admissible",
    "ordinary_success_denominator_allowed",
]
CHANNEL_SUMMARY_FIELDNAMES = [
    "summary_id",
    "horizon_index",
    "response_channel_index",
    "response_channel_name",
    "localization_row_count",
    "valid_prediction_count",
    "gap_count",
    "error_abs_mean_mean",
    "error_abs_mean_max",
    "error_abs_max",
    "dominant_localization_bucket",
    "dominant_recipe_signal",
    "diagnostic_interpretation",
    "forbidden_interpretation",
]
RECIPE_SIGNAL_FIELDNAMES = [
    "recipe_signal_id",
    "signal_name",
    "observed_localization_row_count",
    "unique_pair_count",
    "valid_prediction_count",
    "gap_count",
    "allowed_next_use",
    "blocked_shortcut",
    "claim_boundary",
]
OVERFIT_GUARD_FIELDNAMES = [
    "guard_id",
    "guard",
    "status_pass",
    "observed",
    "expected",
    "blocked_shortcut",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "status_pass",
    "observed",
    "expected",
    "interpretation",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "status_pass",
    "observed",
    "expected",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "status_pass",
    "observed",
    "threshold",
    "interpretation",
]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _float(value: Any) -> float:
    text = str(value).strip()
    return float(text) if text else 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _max(values: list[float]) -> float:
    return max(values) if values else 0.0


def _json_float_array(value: str) -> list[float]:
    if not str(value).strip():
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError(f"expected JSON array, got {type(parsed).__name__}")
    return [float(item) for item in parsed]


def _channel_name(index: int) -> str:
    if 0 <= index < len(RESPONSE_CHANNEL_NAMES):
        return RESPONSE_CHANNEL_NAMES[index]
    return f"response_channel_{index}"


def _quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * fraction))
    return ordered[index]


def _m2857_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    lookup: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        lookup[(row.get("surface_id", ""), row.get("pair_id", ""), row.get("task_source_id", ""))] = row
    return lookup


def _empty_stats(row: dict[str, str], channel_index: int) -> dict[str, Any]:
    return {
        "surface_id": row.get("surface_id", ""),
        "pair_id": row.get("pair_id", ""),
        "task_source_id": row.get("task_source_id", ""),
        "profile_name": row.get("profile_name", ""),
        "checkpoint_subject": row.get("checkpoint_subject", ""),
        "horizon_index": int(row.get("horizon_index", 0) or 0),
        "response_channel_index": channel_index,
        "response_channel_name": _channel_name(channel_index),
        "abs_errors": [],
        "signed_errors": [],
        "squared_errors": [],
        "valid_prediction_count": 0,
        "gap_count": 0,
    }


def _stats_key(row: dict[str, str], channel_index: int) -> tuple[str, str, str, str, int, int]:
    return (
        row.get("surface_id", ""),
        row.get("pair_id", ""),
        row.get("task_source_id", ""),
        row.get("checkpoint_subject", ""),
        int(row.get("horizon_index", 0) or 0),
        channel_index,
    )


def _recipe_signal(channel_name: str, bucket: str) -> str:
    if bucket == "relative_high_response_error":
        if channel_name in ACTUATOR_CHANNELS:
            return "actuator_response_prediction_loss_weight_review"
        return "ego_response_prediction_loss_weight_review"
    if bucket == "no_valid_targets":
        return "trace_schema_or_horizon_repair_required"
    if bucket == "response_error_with_terminal_gap_accounted":
        return "horizon_boundary_masking_preserved"
    return "no_recipe_change_from_trace"


def build_response_prediction_localization_rows(
    *,
    trace_rows: list[dict[str, str]],
    m2857_localization_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Aggregate per-step vector traces to subject/horizon/channel rows."""

    stats_by_key: dict[tuple[str, str, str, str, int, int], dict[str, Any]] = {}
    max_dim = max((int(row.get("response_prediction_dim", 0) or 0) for row in trace_rows), default=0)
    for row in trace_rows:
        if _bool(row.get("target_available", False)) and _bool(row.get("response_prediction_available", False)):
            predicted = _json_float_array(row.get("predicted_values", ""))
            target = _json_float_array(row.get("target_values", ""))
            dim = min(len(predicted), len(target), max_dim)
            for channel_index in range(dim):
                key = _stats_key(row, channel_index)
                stats = stats_by_key.setdefault(key, _empty_stats(row, channel_index))
                signed = predicted[channel_index] - target[channel_index]
                stats["signed_errors"].append(signed)
                stats["abs_errors"].append(abs(signed))
                stats["squared_errors"].append(signed * signed)
                stats["valid_prediction_count"] += 1
            continue

        dim = int(row.get("response_prediction_dim", max_dim) or max_dim)
        for channel_index in range(dim):
            key = _stats_key(row, channel_index)
            stats = stats_by_key.setdefault(key, _empty_stats(row, channel_index))
            stats["gap_count"] += 1

    preliminary: list[dict[str, Any]] = []
    for stats in stats_by_key.values():
        valid_count = int(stats["valid_prediction_count"])
        gap_count = int(stats["gap_count"])
        total = valid_count + gap_count
        abs_errors = list(stats["abs_errors"])
        signed_errors = list(stats["signed_errors"])
        squared_errors = list(stats["squared_errors"])
        preliminary.append(
            {
                "surface_id": stats["surface_id"],
                "pair_id": stats["pair_id"],
                "task_source_id": stats["task_source_id"],
                "profile_name": stats["profile_name"],
                "checkpoint_subject": stats["checkpoint_subject"],
                "horizon_index": stats["horizon_index"],
                "response_channel_index": stats["response_channel_index"],
                "response_channel_name": stats["response_channel_name"],
                "valid_prediction_count": valid_count,
                "gap_count": gap_count,
                "total_trace_count": total,
                "gap_fraction": gap_count / total if total else 0.0,
                "error_abs_mean": _mean(abs_errors),
                "error_abs_max": _max(abs_errors),
                "error_signed_mean": _mean(signed_errors),
                "error_rmse": sqrt(_mean(squared_errors)) if squared_errors else 0.0,
            }
        )

    mean_abs_values = [float(row["error_abs_mean"]) for row in preliminary if int(row["valid_prediction_count"]) > 0]
    high_threshold = _quantile(mean_abs_values, 0.75)
    sorted_means = sorted(mean_abs_values, reverse=True)
    rank_by_mean = {value: index + 1 for index, value in enumerate(sorted_means)}
    lookup = _m2857_lookup(m2857_localization_rows)
    output: list[dict[str, Any]] = []
    for row in sorted(
        preliminary,
        key=lambda item: (
            str(item["surface_id"]),
            str(item["pair_id"]),
            str(item["checkpoint_subject"]),
            int(item["horizon_index"]),
            int(item["response_channel_index"]),
        ),
    ):
        mean_abs = float(row["error_abs_mean"])
        if int(row["valid_prediction_count"]) == 0:
            bucket = "no_valid_targets"
        elif mean_abs >= high_threshold and high_threshold > 0.0:
            bucket = "relative_high_response_error"
        elif int(row["gap_count"]) > 0:
            bucket = "response_error_with_terminal_gap_accounted"
        else:
            bucket = "response_error_accounted"
        source_key = (str(row["surface_id"]), str(row["pair_id"]), str(row["task_source_id"]))
        source_row = lookup.get(source_key, {})
        signal = _recipe_signal(str(row["response_channel_name"]), bucket)
        output.append(
            {
                **row,
                "relative_error_rank": rank_by_mean.get(mean_abs, ""),
                "localization_bucket": bucket,
                "m2857_per_step_localization_bucket": source_row.get("per_step_localization_bucket", ""),
                "m2857_training_recipe_signal": source_row.get("training_recipe_signal", ""),
                "recipe_signal": signal,
                "requires_recipe_design": signal != "no_recipe_change_from_trace",
                "diagnostic_only": True,
                "actor_visible_allowed": False,
                "future_label_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "ranking_admissible": False,
                "ordinary_success_denominator_allowed": False,
            }
        )
    return output


def build_channel_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                int(row["horizon_index"]),
                int(row["response_channel_index"]),
                str(row["response_channel_name"]),
            )
        ].append(row)

    output: list[dict[str, Any]] = []
    for index, ((horizon, channel_index, channel_name), group) in enumerate(sorted(grouped.items()), start=1):
        bucket_counts = Counter(str(row["localization_bucket"]) for row in group)
        signal_counts = Counter(str(row["recipe_signal"]) for row in group)
        output.append(
            {
                "summary_id": f"m2861-channel-summary-{index:03d}",
                "horizon_index": horizon,
                "response_channel_index": channel_index,
                "response_channel_name": channel_name,
                "localization_row_count": len(group),
                "valid_prediction_count": sum(int(row["valid_prediction_count"]) for row in group),
                "gap_count": sum(int(row["gap_count"]) for row in group),
                "error_abs_mean_mean": _mean([float(row["error_abs_mean"]) for row in group]),
                "error_abs_mean_max": _max([float(row["error_abs_mean"]) for row in group]),
                "error_abs_max": _max([float(row["error_abs_max"]) for row in group]),
                "dominant_localization_bucket": bucket_counts.most_common(1)[0][0],
                "dominant_recipe_signal": signal_counts.most_common(1)[0][0],
                "diagnostic_interpretation": "response-prediction channel/horizon diagnostic localization",
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return output


def _allowed_next_use(signal: str) -> str:
    if signal == "actuator_response_prediction_loss_weight_review":
        return "audit actuator-channel response-prediction loss weighting before any bounded recipe change"
    if signal == "ego_response_prediction_loss_weight_review":
        return "audit ego-response channel loss weighting and normalization before any bounded recipe change"
    if signal == "horizon_boundary_masking_preserved":
        return "keep horizon/terminal target masking explicit in any future training recipe"
    if signal == "trace_schema_or_horizon_repair_required":
        return "repair trace schema or horizon accounting before recipe interpretation"
    return "preserve as accounted diagnostic trace row"


def _blocked_shortcut(signal: str) -> str:
    if signal == "no_recipe_change_from_trace":
        return "do not treat accounted low-error rows as validation or promotion evidence"
    return "do not train rank or promote directly from M2859 public diagnostic trace rows"


def build_recipe_signal_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["recipe_signal"])].append(row)
    output: list[dict[str, Any]] = []
    for signal, group in sorted(grouped.items()):
        output.append(
            {
                "recipe_signal_id": f"m2861-recipe-{signal}",
                "signal_name": signal,
                "observed_localization_row_count": len(group),
                "unique_pair_count": len({row["pair_id"] for row in group}),
                "valid_prediction_count": sum(int(row["valid_prediction_count"]) for row in group),
                "gap_count": sum(int(row["gap_count"]) for row in group),
                "allowed_next_use": _allowed_next_use(signal),
                "blocked_shortcut": _blocked_shortcut(signal),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def build_public_row_overfit_guard_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pair_count = len({row["pair_id"] for row in rows})
    return [
        {
            "guard_id": "m2861-overfit-public-diagnostic-only",
            "guard": "M2850 explanatory rows remain diagnostic-only public rows",
            "status_pass": all(_bool(row["diagnostic_only"]) for row in rows),
            "observed": f"{pair_count} M2850-derived pairs",
            "expected": "diagnostic-only existing-artifact localization",
            "blocked_shortcut": "do not use these rows as validation ranking or optimization denominators",
        },
        {
            "guard_id": "m2861-overfit-no-ordinary-denominator",
            "guard": "M2861 rows are excluded from ordinary success denominators",
            "status_pass": all(not _bool(row["ordinary_success_denominator_allowed"]) for row in rows),
            "observed": sorted({row["ordinary_success_denominator_allowed"] for row in rows}),
            "expected": False,
            "blocked_shortcut": "do not compute success-rate verdicts from M2861 rows",
        },
        {
            "guard_id": "m2861-overfit-no-ranking",
            "guard": "M2861 rows cannot rank baseline versus candidate checkpoints",
            "status_pass": all(not _bool(row["ranking_admissible"]) for row in rows),
            "observed": sorted({row["ranking_admissible"] for row in rows}),
            "expected": False,
            "blocked_shortcut": "do not select a winner from response-prediction error localization",
        },
        {
            "guard_id": "m2861-overfit-existing-artifact-only",
            "guard": "M2861 materializes existing artifacts without new execution",
            "status_pass": True,
            "observed": "reads M2859/M2857 artifacts only",
            "expected": "no reset step rollout replay training validation",
            "blocked_shortcut": "do not hide current-surface public-row overfit risk",
        },
    ]


def build_actor_contract_guard_rows(
    *,
    summary: dict[str, Any],
    trace_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    return [
        {
            "guard_id": "m2861-actor-observation-action-shape",
            "status_pass": bool(summary.get("actor_contract_shape_72_action_3", False)),
            "observed": summary.get("actor_contract_shape_72_action_3", ""),
            "expected": f"actor {P0_OBSERVATION_DIM}/action {ACTION_DIM}",
            "interpretation": "M2859 actor contract summary is preserved",
        },
        {
            "guard_id": "m2861-no-future-label-actor-visible",
            "status_pass": all(not _bool(row.get("future_label_actor_visible", False)) for row in trace_rows + gap_rows),
            "observed": sorted({row.get("future_label_actor_visible", "") for row in trace_rows + gap_rows}),
            "expected": False,
            "interpretation": "future response targets remain evaluator-only labels",
        },
        {
            "guard_id": "m2861-no-hidden-oracle-actor-input",
            "status_pass": all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in trace_rows + gap_rows),
            "observed": sorted({row.get("hidden_oracle_actor_input_required", "") for row in trace_rows + gap_rows}),
            "expected": False,
            "interpretation": "no hidden dynamics oracle labels or route labels are actor-visible",
        },
        {
            "guard_id": "m2861-no-actor-visible-diagnostic-label",
            "status_pass": all(not _bool(row.get("actor_visible_allowed", False)) for row in trace_rows + gap_rows),
            "observed": sorted({row.get("actor_visible_allowed", "") for row in trace_rows + gap_rows}),
            "expected": False,
            "interpretation": "M2861 diagnostic labels are not admitted to actor input",
        },
    ]


def build_claim_boundary_rows(follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    expected_false_claims = [
        "environment_rerun",
        "training_run",
        "ppo_used",
        "validation_result_claim_made",
        "ranking_run",
        "winner_selected",
        "checkpoint_promoted",
        "success_rate_verdict_computed",
        "driver_performance_claim_made",
        "paper_claim_made",
        "finite_window_vs_gru_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "full_ideal_driver_gate_passed",
        "level3_self_id_claim_made",
    ]
    rows = [
        {
            "claim_id": f"m2861-claim-{claim}",
            "status_pass": True,
            "observed": False,
            "expected": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim in expected_false_claims
    ]
    rows.append(
        {
            "claim_id": "m2861-claim-follow-up-audit-registered",
            "status_pass": follow_up_manifest_registered,
            "observed": DEFAULT_NEXT_BLOCKER if follow_up_manifest_registered else "",
            "expected": DEFAULT_NEXT_BLOCKER,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return rows


def build_gate_rows(
    *,
    summary: dict[str, Any],
    trace_rows: list[dict[str, str]],
    episode_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    localization_rows: list[dict[str, Any]],
    channel_summary_rows: list[dict[str, Any]],
    recipe_signal_rows: list[dict[str, Any]],
    overfit_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    dim = int(summary.get("response_prediction_dim", 0))
    horizon = int(summary.get("response_prediction_horizon", 0))
    expected_localization = len(episode_rows) * dim * horizon
    valid_count = sum(1 for row in trace_rows if _bool(row.get("target_available", False)))
    return [
        {
            "gate_id": "m2861-required-inputs-present",
            "gate_tier": "proof",
            "status_pass": bool(trace_rows and episode_rows and gap_rows and summary.get("status_pass")),
            "observed": "M2859 summary trace episode gap rows read",
            "threshold": "all required inputs present",
            "interpretation": "existing response-prediction trace inputs are available",
        },
        {
            "gate_id": "m2861-trace-accounting-preserved",
            "gate_tier": "proof",
            "status_pass": len(trace_rows) == int(summary.get("response_prediction_trace_row_count", -1)),
            "observed": f"summary={summary.get('response_prediction_trace_row_count')} actual={len(trace_rows)}",
            "threshold": "actual trace row count equals M2859 summary",
            "interpretation": "M2859 trace accounting preserved",
        },
        {
            "gate_id": "m2861-valid-prediction-accounting-preserved",
            "gate_tier": "proof",
            "status_pass": valid_count == int(summary.get("valid_prediction_row_count", -1)),
            "observed": f"summary={summary.get('valid_prediction_row_count')} actual={valid_count}",
            "threshold": "actual valid prediction count equals M2859 summary",
            "interpretation": "valid prediction row accounting preserved",
        },
        {
            "gate_id": "m2861-gap-accounting-preserved",
            "gate_tier": "proof",
            "status_pass": len(gap_rows) == int(summary.get("instrumentation_gap_row_count", -1)),
            "observed": f"summary={summary.get('instrumentation_gap_row_count')} actual={len(gap_rows)}",
            "threshold": "actual gap row count equals M2859 summary",
            "interpretation": "horizon and terminal target gaps remain explicit",
        },
        {
            "gate_id": "m2861-localization-row-accounting",
            "gate_tier": "generalization",
            "status_pass": len(localization_rows) == expected_localization and expected_localization > 0,
            "observed": f"expected={expected_localization} actual={len(localization_rows)}",
            "threshold": "one row per episode subject horizon response channel",
            "interpretation": "response-prediction traces were localized by subject horizon and channel",
        },
        {
            "gate_id": "m2861-channel-summary-nonempty",
            "gate_tier": "generalization",
            "status_pass": bool(channel_summary_rows),
            "observed": len(channel_summary_rows),
            "threshold": ">=1 channel summary row",
            "interpretation": "channel/horizon summary was materialized",
        },
        {
            "gate_id": "m2861-recipe-signals-nonempty",
            "gate_tier": "generalization",
            "status_pass": bool(recipe_signal_rows),
            "observed": len(recipe_signal_rows),
            "threshold": ">=1 recipe signal row",
            "interpretation": "diagnostic recipe-signal rows were materialized",
        },
        {
            "gate_id": "m2861-public-row-overfit-guards-pass",
            "gate_tier": "promotion",
            "status_pass": all(_bool(row["status_pass"]) for row in overfit_rows),
            "observed": f"{sum(1 for row in overfit_rows if _bool(row['status_pass']))}/{len(overfit_rows)}",
            "threshold": "all overfit guards pass",
            "interpretation": "public diagnostic row boundary remains explicit",
        },
        {
            "gate_id": "m2861-actor-contract-guards-pass",
            "gate_tier": "promotion",
            "status_pass": all(_bool(row["status_pass"]) for row in actor_rows),
            "observed": f"{sum(1 for row in actor_rows if _bool(row['status_pass']))}/{len(actor_rows)}",
            "threshold": "all actor guards pass",
            "interpretation": "actor 72/action 3 and label invisibility are preserved",
        },
        {
            "gate_id": "m2861-claim-boundary-guards-pass",
            "gate_tier": "promotion",
            "status_pass": all(_bool(row["status_pass"]) for row in claim_rows),
            "observed": f"{sum(1 for row in claim_rows if _bool(row['status_pass']))}/{len(claim_rows)}",
            "threshold": "all claim guards pass",
            "interpretation": "no ranking promotion validation performance paper current-sim high-fidelity full-driver or self-ID claim",
        },
    ]


def _artifact_paths(output_dir: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "response_prediction_localization_rows": output_dir / "response_prediction_localization_rows.csv",
        "response_prediction_channel_summary_rows": output_dir / "response_prediction_channel_summary_rows.csv",
        "response_prediction_recipe_signal_rows": output_dir / "response_prediction_recipe_signal_rows.csv",
        "public_row_overfit_guard_rows": output_dir / "public_row_overfit_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def build_m2862_follow_up_manifest() -> dict[str, Any]:
    task_id = DEFAULT_NEXT_BLOCKER
    doc_path = f"docs/{task_id}.md"
    output_dir = str(DEFAULT_OUTPUT_DIR)
    return {
        "id": task_id,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/checkpoints/m2846_response_predictive_recurrent_belief_candidate.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            ],
            "parent_dataset": [
                f"{output_dir}/summary.json",
                f"{output_dir}/response_prediction_localization_rows.csv",
                f"{output_dir}/response_prediction_channel_summary_rows.csv",
                f"{output_dir}/response_prediction_recipe_signal_rows.csv",
                f"{output_dir}/public_row_overfit_guard_rows.csv",
                str(DEFAULT_M2859_SUMMARY),
                str(DEFAULT_TRACE_ROWS),
                str(DEFAULT_EPISODE_ROWS),
                str(DEFAULT_GAP_ROWS),
                str(DEFAULT_DOC_PATH),
            ],
            "parent_config": [
                "experiments/manifests/m2861-engineering-controller-route-a-response-predictive-recurrent-belief-response-prediction-trace-localization-materialization-preflight.json",
                "experiments/manifests/m2860-engineering-controller-route-a-response-predictive-recurrent-belief-response-prediction-trace-instrumentation-repair-result-audit.json",
            ],
            "parent_objective": [
                "audit M2861 response-prediction trace localization before recipe interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2862 must audit M2861 localized response-prediction recipe signals before training recipe changes",
                "M2862 must preserve actor-invisible future labels and public diagnostic row boundaries",
                "M2862 must reject validation ranking promotion performance paper current-sim high-fidelity full-driver and self-ID claims",
            ],
            "supersedes": [
                "unaudited M2861 response-prediction trace localization interpretation",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2862 must audit M2861 summary localization channel summary recipe signal overfit actor claim and gate artifacts",
            "M2862 must preserve actor 72/action 3 no hidden/oracle actor inputs future-label invisibility and diagnostic-only denominator boundaries",
            "M2862 must not run training validation ranking promotion or success-rate verdict computation",
            "M2862 must decide whether M2861 supports recipe design branch synthesis or instrumentation repair",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run training",
            "do not run validation",
            "do not rank baseline and candidate checkpoints",
            "do not select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not expose future labels to actor input",
            "do not claim repair success driver performance validation paper current-sim high-fidelity full ideal driver completion or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_response_predictive_recurrent_belief_failure_localization_training_recipe_redesign",
            "evidence_axis": "response_prediction_trace_localization_result_audit",
            "evidence_increment": "audits M2861 localized response-prediction trace and recipe-signal artifacts before deciding recipe or synthesis route",
            "claim_scope": "Result audit only; no training validation ranking winner promotion success-rate verdict repair-success driver-performance paper current-sim high-fidelity validation self-ID or full-driver claim",
            "stop_condition": [
                "stop if M2861 localization artifacts are incomplete",
                "stop if M2861 hides M2859 instrumentation gaps or actor-invisible label boundaries",
                "stop if localization rows are used as ranking validation or optimization evidence",
                "stop if M2861 recipe signals remain too diffuse to justify a bounded recipe design",
            ],
            "fallback_plan": [
                "route to branch synthesis if trace localization remains inconclusive",
                "route to bounded recipe design if M2861 localized recipe signals are accepted",
                "route to instrumentation repair if trace localization schema or accounting failed",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2861 has produced response-prediction localization artifacts requiring audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2861 response-prediction trace localization materialization",
            "admission_evidence": [
                "M2861 summary and localization artifacts are expected before M2862 runs",
                "M2861 recipe signal rows require audit before recipe interpretation",
            ],
            "blocked_shortcuts": [
                "no training PPO validation ranking promotion or success-rate verdict",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                doc_path,
                "M2862 status queue scoreboard and review",
                "one bounded follow-up manifest if audit accepts a next route",
            ],
            "next_stage_criteria": [
                "M2861 artifacts are accepted or rejected",
                "response-prediction localization recipe signals are preserved",
                "one bounded next route or stop/synthesis decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2862 audits Route A response-prediction localization and does not test history necessity or current-frame substitution.",
            "history_necessity_tests": [
                "M2861 response-prediction localization is not level3 self-identification evidence."
            ],
            "temporal_evidence_window": "M2843-M2861 response-predictive recurrent-belief branch.",
            "negative_result_policy": "If localization is inconclusive, preserve the result and route to synthesis rather than weakening gates.",
            "allowed_claims": [
                "M2861 response-prediction localization accepted or rejected",
                "bounded follow-up route registration",
                "no driver-performance verdict paper result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits new response-prediction localization panel",
            "paper_verdict_delta": "no paper verdict; audit governs Route A response-prediction localization interpretation before recipe changes",
            "must_synthesize_if": [
                "M2861 response-prediction localization artifacts are incomplete",
                "M2861 cannot localize beyond aggregate response-prediction errors",
                "M2861 exposes future labels or hidden/oracle inputs to actor input",
                "M2861 results are used as validation performance self-ID or paper evidence",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2861 response-prediction trace localization artifacts before recipe interpretation.",
        "success_criteria": [
            f"{doc_path} exists",
            "audit checks M2861 summary localization channel summary recipe signal actor claim and gate rows",
            "audit preserves actor 72/action 3 no hidden/oracle labels future-label invisibility and claim boundary",
            "audit registers one bounded follow-up route or stop decision",
        ],
        "failure_criteria": [
            "M2862 runs new training validation ranking promotion or success-rate verdict computation",
            "M2862 hides M2861 gate failures or weakens actor/claim boundaries",
            "M2862 claims repair success driver performance validation readiness/result high-fidelity validation paper current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2862 audits M2861 artifacts under unchanged actor and claim boundaries without new execution or overclaiming.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": doc_path, "type": "md"}],
        "baseline_checkpoints": [
            "runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight/checkpoints/m2846_response_predictive_recurrent_belief_candidate.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
        ],
        "baseline_artifacts": [f"{output_dir}/summary.json"],
        "scoreboard_checkpoint": doc_path,
        "next_blocker": DEFAULT_M2862_NEXT_BLOCKER,
    }


def render_result_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2861 Engineering Controller Route A Response-Predictive Recurrent-Belief Response-Prediction Trace Localization Materialization Preflight",
            "",
            "## Metadata",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- localization rows: {summary['response_prediction_localization_row_count']}",
            f"- channel summary rows: {summary['response_prediction_channel_summary_row_count']}",
            f"- recipe signal rows: {summary['response_prediction_recipe_signal_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- failed gates: {summary['failed_gate_ids'] or 'none'}",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next blocker: `{summary['next_blocker']}`",
            "",
            "## Materialization Result",
            "",
            "```text",
            f"M2859 trace rows: {summary['m2859_trace_row_count']}",
            f"M2859 valid prediction rows: {summary['m2859_valid_prediction_row_count']}",
            f"M2859 gap rows: {summary['m2859_gap_row_count']}",
            f"episode rows: {summary['m2859_episode_row_count']}",
            f"response prediction dim: {summary['response_prediction_dim']}",
            f"response prediction horizon: {summary['response_prediction_horizon']}",
            f"localized pairs: {summary['localized_pair_count']}",
            f"localized subject rows: {summary['localized_subject_count']}",
            f"high error localization rows: {summary['relative_high_error_row_count']}",
            f"terminal gap accounted rows: {summary['terminal_gap_accounted_row_count']}",
            "```",
            "",
            "M2861 uses existing M2859/M2857 artifacts only. It does not rerun the",
            "environment, train, validate, rank, promote, compute a success-rate verdict,",
            "or claim driver performance.",
            "",
            "## Claim Boundary",
            "",
            "Allowed M2861 claim:",
            "",
            "```text",
            "response-prediction trace localization artifacts were materialized from",
            "M2859 and are ready for M2862 audit",
            "```",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
        ]
    )


def run_response_prediction_trace_localization_materialization(
    *,
    m2860_audit: Path = DEFAULT_M2860_AUDIT,
    m2859_summary: Path = DEFAULT_M2859_SUMMARY,
    response_prediction_trace_rows: Path = DEFAULT_TRACE_ROWS,
    response_prediction_episode_rows: Path = DEFAULT_EPISODE_ROWS,
    instrumentation_gap_rows: Path = DEFAULT_GAP_ROWS,
    m2857_localization_rows: Path = DEFAULT_M2857_LOCALIZATION_ROWS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DEFAULT_DOC_PATH,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    summary = read_json(m2859_summary)
    trace_rows = _read_csv_rows(response_prediction_trace_rows)
    episode_rows = _read_csv_rows(response_prediction_episode_rows)
    gap_rows = _read_csv_rows(instrumentation_gap_rows)
    m2857_rows = _read_csv_rows(m2857_localization_rows)

    localization_rows = build_response_prediction_localization_rows(
        trace_rows=trace_rows,
        m2857_localization_rows=m2857_rows,
    )
    channel_summary_rows = build_channel_summary_rows(localization_rows)
    recipe_signal_rows = build_recipe_signal_rows(localization_rows)
    overfit_rows = build_public_row_overfit_guard_rows(localization_rows)
    actor_rows = build_actor_contract_guard_rows(summary=summary, trace_rows=trace_rows, gap_rows=gap_rows)
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=True)
    gate_rows = build_gate_rows(
        summary=summary,
        trace_rows=trace_rows,
        episode_rows=episode_rows,
        gap_rows=gap_rows,
        localization_rows=localization_rows,
        channel_summary_rows=channel_summary_rows,
        recipe_signal_rows=recipe_signal_rows,
        overfit_rows=overfit_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
    )

    write_csv_rows(paths["response_prediction_localization_rows"], localization_rows, LOCALIZATION_FIELDNAMES)
    write_csv_rows(
        paths["response_prediction_channel_summary_rows"],
        channel_summary_rows,
        CHANNEL_SUMMARY_FIELDNAMES,
    )
    write_csv_rows(paths["response_prediction_recipe_signal_rows"], recipe_signal_rows, RECIPE_SIGNAL_FIELDNAMES)
    write_csv_rows(paths["public_row_overfit_guard_rows"], overfit_rows, OVERFIT_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_m2862_follow_up_manifest())

    required_artifacts_present = all(
        paths[key].exists()
        for key in (
            "response_prediction_localization_rows",
            "response_prediction_channel_summary_rows",
            "response_prediction_recipe_signal_rows",
            "public_row_overfit_guard_rows",
            "actor_contract_guard_rows",
            "claim_boundary_rows",
            "gate_matrix",
            "follow_up_manifest",
        )
    )
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    signal_counts = Counter(str(row["recipe_signal"]) for row in localization_rows)
    bucket_counts = Counter(str(row["localization_bucket"]) for row in localization_rows)
    result = {
        "milestone": DEFAULT_MILESTONE,
        "result_class": (
            "engineering_controller_route_a_response_predictive_recurrent_belief_"
            "response_prediction_trace_localization_materialization_pass"
        ),
        "status_pass": bool(
            m2860_audit.exists()
            and required_artifacts_present
            and gate_matrix_pass
            and bool(localization_rows)
            and bool(channel_summary_rows)
            and bool(recipe_signal_rows)
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "doc": str(doc_path),
        "summary": str(paths["summary"]),
        "run_state": str(paths["run_state"]),
        "m2860_audit": str(m2860_audit),
        "m2860_audit_exists": m2860_audit.exists(),
        "m2859_summary": str(m2859_summary),
        "response_prediction_trace_rows": str(response_prediction_trace_rows),
        "response_prediction_episode_rows": str(response_prediction_episode_rows),
        "instrumentation_gap_rows": str(instrumentation_gap_rows),
        "m2857_localization_rows": str(m2857_localization_rows),
        "response_prediction_localization_rows": str(paths["response_prediction_localization_rows"]),
        "response_prediction_channel_summary_rows": str(paths["response_prediction_channel_summary_rows"]),
        "response_prediction_recipe_signal_rows": str(paths["response_prediction_recipe_signal_rows"]),
        "public_row_overfit_guard_rows": str(paths["public_row_overfit_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "follow_up_manifest": str(follow_up_manifest),
        "next_blocker": DEFAULT_NEXT_BLOCKER,
        "m2859_trace_row_count": len(trace_rows),
        "m2859_valid_prediction_row_count": sum(1 for row in trace_rows if _bool(row.get("target_available", False))),
        "m2859_episode_row_count": len(episode_rows),
        "m2859_gap_row_count": len(gap_rows),
        "response_prediction_dim": int(summary.get("response_prediction_dim", 0)),
        "response_prediction_horizon": int(summary.get("response_prediction_horizon", 0)),
        "response_prediction_localization_row_count": len(localization_rows),
        "response_prediction_channel_summary_row_count": len(channel_summary_rows),
        "response_prediction_recipe_signal_row_count": len(recipe_signal_rows),
        "localized_pair_count": len({row["pair_id"] for row in localization_rows}),
        "localized_subject_count": len({(row["pair_id"], row["checkpoint_subject"]) for row in localization_rows}),
        "relative_high_error_row_count": bucket_counts["relative_high_response_error"],
        "terminal_gap_accounted_row_count": bucket_counts["response_error_with_terminal_gap_accounted"],
        "recipe_signal_counts": dict(sorted(signal_counts.items())),
        "localization_bucket_counts": dict(sorted(bucket_counts.items())),
        "required_artifacts_present": required_artifacts_present,
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "failed_gate_ids": [row["gate_id"] for row in gate_rows if not _bool(row["status_pass"])],
        "actor_contract_shape_72_action_3": bool(summary.get("actor_contract_shape_72_action_3", False)),
        "future_label_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "ordinary_success_denominator_allowed": False,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "environment_rerun": False,
        "training_run": False,
        "ppo_used": False,
        "validation_result_claim_made": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_computed": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    write_json(paths["summary"], result)
    write_json(
        paths["run_state"],
        {
            "milestone": DEFAULT_MILESTONE,
            "inputs": {
                "m2860_audit": str(m2860_audit),
                "m2859_summary": str(m2859_summary),
                "response_prediction_trace_rows": str(response_prediction_trace_rows),
                "response_prediction_episode_rows": str(response_prediction_episode_rows),
                "instrumentation_gap_rows": str(instrumentation_gap_rows),
                "m2857_localization_rows": str(m2857_localization_rows),
            },
            "outputs": {key: str(path) for key, path in paths.items()},
            "claim_scope": CLAIM_SCOPE,
        },
    )
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_result_doc(result), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2860-audit", type=Path, default=DEFAULT_M2860_AUDIT)
    parser.add_argument("--m2859-summary", type=Path, default=DEFAULT_M2859_SUMMARY)
    parser.add_argument("--response-prediction-trace-rows", type=Path, default=DEFAULT_TRACE_ROWS)
    parser.add_argument("--response-prediction-episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--instrumentation-gap-rows", type=Path, default=DEFAULT_GAP_ROWS)
    parser.add_argument("--m2857-localization-rows", type=Path, default=DEFAULT_M2857_LOCALIZATION_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_response_prediction_trace_localization_materialization(
        m2860_audit=args.m2860_audit,
        m2859_summary=args.m2859_summary,
        response_prediction_trace_rows=args.response_prediction_trace_rows,
        response_prediction_episode_rows=args.response_prediction_episode_rows,
        instrumentation_gap_rows=args.instrumentation_gap_rows,
        m2857_localization_rows=args.m2857_localization_rows,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")
    if not summary["status_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
