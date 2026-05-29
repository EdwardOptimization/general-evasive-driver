"""No-training planner for fresh ambiguity source mining.

This module intentionally stays at source-spec and metadata-smoke level. It does
not run the simulator, materialize DecisiveHistoryTaskCandidate rows, export a
training corpus, train, replay, run PPO, promote checkpoints, or change actor
inputs.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from autodrift.artifacts import write_csv_rows, write_json


ASYMMETRIC_FAULT_TOKENS = (
    "one_wheel",
    "one-wheel",
    "split_mu",
    "split-mu",
    "half_shaft",
    "half-shaft",
    "tire_blowout",
    "blowout",
    "individual_wheel",
)

SNAPSHOT_ANCHORS = (
    "reveal",
    "reveal_plus_4",
    "decision_minus_8",
    "decision",
    "post_decision_plus_8",
)


@dataclass(frozen=True)
class FreshAmbiguityThresholds:
    """Public development thresholds for fresh ambiguity source planning."""

    max_scene_context_distance: float = 0.08
    max_current_ego_distance: float = 0.08
    max_recent_window_distance: float = 0.08
    min_older_evidence_distance: float = 0.12
    min_hidden_capability_distance: float = 0.15
    min_first_action_l2: float = 0.04
    min_prefix_action_l2: float = 0.08
    min_terminal_margin_gap: float = 0.02
    near_boundary_margin_min: float = -0.02
    near_boundary_margin_max: float = 0.10
    max_closed_t5_subset_share: float = 0.20
    max_single_source_family_share: float = 0.30
    min_proxy_fault_family_count: int = 3


@dataclass(frozen=True)
class FreshAmbiguitySourceSpec:
    """Public source-family spec for fresh ambiguity mining."""

    source_family: str
    task_family: str
    seed_base: int
    seed_count: int
    hidden_capability_pairs: tuple[str, ...]
    geometry_keys: tuple[str, ...]
    reveal_steps: tuple[int, ...]
    simulator_scope: str = "existing_public_source"
    proxy_fault_family: bool = False
    closed_t5_subset: bool = False
    decision_step_offset: int = 8
    scene_context_distance: float = 0.04
    current_ego_distance: float = 0.04
    recent_window_distance: float = 0.05
    older_evidence_distance: float = 0.20
    hidden_capability_distance: float = 0.25
    first_action_l2: float = 0.06
    prefix_action_l2: float = 0.12
    terminal_margin_gap: float = 0.03
    normal_margin: float = 0.04
    labels_enter_actor_input: bool = False
    actor_input_contract_changed: bool = False


@dataclass(frozen=True)
class FreshAmbiguitySourceRow:
    """Expanded metadata row from one source spec and one public seed."""

    source_family: str
    task_family: str
    source_index: int
    seed: int
    hidden_capability_pair: str
    geometry_key: str
    reveal_step: int
    decision_step: int
    simulator_scope: str
    proxy_fault_family: bool
    closed_t5_subset: bool
    scene_context_distance: float
    current_ego_distance: float
    recent_window_distance: float
    older_evidence_distance: float
    hidden_capability_distance: float
    first_action_l2: float
    prefix_action_l2: float
    terminal_margin_gap: float
    normal_margin: float
    labels_enter_actor_input: bool = False
    actor_input_contract_changed: bool = False
    candidate_materialized: bool = False
    training_corpus_exported: bool = False


@dataclass(frozen=True)
class FreshAmbiguityClassification:
    """Acceptance result for one expanded fresh ambiguity source row."""

    row_id: str
    accepted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class FreshAmbiguityPlannerConfig:
    """Configuration for a no-training source-planner smoke."""

    source_specs: tuple[FreshAmbiguitySourceSpec, ...]
    thresholds: FreshAmbiguityThresholds = field(default_factory=FreshAmbiguityThresholds)
    private_holdout_used: bool = False
    training_started: bool = False
    evaluation_started: bool = False
    replay_started: bool = False
    ppo_used: bool = False
    promoted: bool = False
    training_corpus_exported: bool = False


def default_source_specs(*, seed: int = 1528, seed_count: int = 8) -> tuple[FreshAmbiguitySourceSpec, ...]:
    """Return the bounded public fresh-ambiguity source grid."""

    base = int(seed) * 100
    return (
        FreshAmbiguitySourceSpec(
            source_family="t4_staged_warmup_capability",
            task_family="T4",
            seed_base=base + 0,
            seed_count=seed_count,
            hidden_capability_pairs=("low_mu|high_mu", "brake_low|brake_high"),
            geometry_keys=("warmup_left", "warmup_right", "warmup_curve"),
            reveal_steps=(24, 32, 40),
            older_evidence_distance=0.24,
            hidden_capability_distance=0.30,
        ),
        FreshAmbiguitySourceSpec(
            source_family="t4_capability_step_temporal",
            task_family="T4",
            seed_base=base + 100,
            seed_count=seed_count,
            hidden_capability_pairs=("drive_low|drive_high", "tire_soft|tire_stiff"),
            geometry_keys=("temporal_left", "temporal_right", "temporal_s"),
            reveal_steps=(28, 36, 44),
            terminal_margin_gap=0.028,
        ),
        FreshAmbiguitySourceSpec(
            source_family="t4_actuator_delay_response",
            task_family="T4",
            seed_base=base + 200,
            seed_count=seed_count,
            hidden_capability_pairs=("tau_fast|tau_slow", "steer_fast|steer_slow"),
            geometry_keys=("delay_left", "delay_right", "delay_curve"),
            reveal_steps=(30, 38, 46),
            simulator_scope="single_track_symmetric_proxy",
            proxy_fault_family=True,
            first_action_l2=0.055,
            prefix_action_l2=0.13,
        ),
        FreshAmbiguitySourceSpec(
            source_family="t5_near_boundary_warmup",
            task_family="T5",
            seed_base=base + 300,
            seed_count=seed_count,
            hidden_capability_pairs=("low_mu|high_mu", "brake_low|brake_high"),
            geometry_keys=("near_left", "near_right", "near_curve"),
            reveal_steps=(34, 42, 50),
            normal_margin=0.018,
            terminal_margin_gap=0.035,
        ),
        FreshAmbiguitySourceSpec(
            source_family="t5_high_speed_close_obstacle",
            task_family="T5",
            seed_base=base + 400,
            seed_count=seed_count,
            hidden_capability_pairs=("speed_high_low_mu|speed_high_high_mu", "brake_low|brake_high"),
            geometry_keys=("fresh_high_speed_left", "fresh_high_speed_right", "fresh_high_speed_curve"),
            reveal_steps=(18, 22, 26),
            normal_margin=0.022,
            terminal_margin_gap=0.032,
            closed_t5_subset=False,
        ),
        FreshAmbiguitySourceSpec(
            source_family="t5_boundary_axis_retarget",
            task_family="T5",
            seed_base=base + 500,
            seed_count=seed_count,
            hidden_capability_pairs=("understeer|oversteer", "tau_fast|tau_slow"),
            geometry_keys=("boundary_left", "boundary_right", "boundary_curve"),
            reveal_steps=(40, 48, 56),
            normal_margin=0.014,
            terminal_margin_gap=0.030,
        ),
        FreshAmbiguitySourceSpec(
            source_family="capability_step_down",
            task_family="T4",
            seed_base=base + 600,
            seed_count=seed_count,
            hidden_capability_pairs=("mu_nominal|mu_drop", "brake_nominal|brake_drop"),
            geometry_keys=("step_down_left", "step_down_right", "step_down_curve"),
            reveal_steps=(26, 34, 42),
            simulator_scope="single_track_symmetric_proxy",
            proxy_fault_family=True,
            older_evidence_distance=0.30,
            hidden_capability_distance=0.38,
            first_action_l2=0.075,
            prefix_action_l2=0.16,
            terminal_margin_gap=0.045,
        ),
        FreshAmbiguitySourceSpec(
            source_family="capability_step_up",
            task_family="T4",
            seed_base=base + 700,
            seed_count=seed_count,
            hidden_capability_pairs=("mu_recover|mu_low", "brake_recover|brake_low"),
            geometry_keys=("step_up_left", "step_up_right", "step_up_curve"),
            reveal_steps=(26, 34, 42),
            simulator_scope="single_track_symmetric_proxy",
            proxy_fault_family=True,
            older_evidence_distance=0.26,
            hidden_capability_distance=0.34,
            first_action_l2=0.065,
            prefix_action_l2=0.14,
            terminal_margin_gap=0.038,
        ),
        FreshAmbiguitySourceSpec(
            source_family="actuator_delay_step",
            task_family="T4",
            seed_base=base + 800,
            seed_count=seed_count,
            hidden_capability_pairs=("fast_brake|slow_brake", "fast_steer|slow_steer"),
            geometry_keys=("actuator_step_left", "actuator_step_right", "actuator_step_curve"),
            reveal_steps=(30, 38, 46),
            simulator_scope="single_track_symmetric_proxy",
            proxy_fault_family=True,
            prefix_action_l2=0.15,
        ),
        FreshAmbiguitySourceSpec(
            source_family="brake_fade_or_loss_proxy",
            task_family="T5",
            seed_base=base + 900,
            seed_count=seed_count,
            hidden_capability_pairs=("brake_ok|brake_fade", "brake_ok|brake_loss_proxy"),
            geometry_keys=("brake_fade_left", "brake_fade_right", "brake_fade_curve"),
            reveal_steps=(20, 28, 36),
            simulator_scope="single_track_symmetric_proxy",
            proxy_fault_family=True,
            normal_margin=0.012,
            terminal_margin_gap=0.050,
        ),
        FreshAmbiguitySourceSpec(
            source_family="drive_loss_proxy",
            task_family="T5",
            seed_base=base + 1000,
            seed_count=seed_count,
            hidden_capability_pairs=("drive_ok|drive_drop", "drive_ok|drive_cut_proxy"),
            geometry_keys=("drive_loss_left", "drive_loss_right", "drive_loss_curve"),
            reveal_steps=(32, 40, 48),
            simulator_scope="single_track_symmetric_proxy",
            proxy_fault_family=True,
            normal_margin=0.026,
            terminal_margin_gap=0.026,
        ),
        FreshAmbiguitySourceSpec(
            source_family="grip_loss_proxy",
            task_family="T5",
            seed_base=base + 1100,
            seed_count=seed_count,
            hidden_capability_pairs=("grip_ok|grip_drop", "lat_stiff_ok|lat_stiff_drop"),
            geometry_keys=("grip_loss_left", "grip_loss_right", "grip_loss_curve"),
            reveal_steps=(24, 32, 40),
            simulator_scope="single_track_symmetric_proxy",
            proxy_fault_family=True,
            normal_margin=0.016,
            terminal_margin_gap=0.044,
        ),
        FreshAmbiguitySourceSpec(
            source_family="late_reveal_boundary",
            task_family="T5",
            seed_base=base + 1200,
            seed_count=seed_count,
            hidden_capability_pairs=("late_low_mu|late_high_mu", "late_brake_low|late_brake_high"),
            geometry_keys=("late_boundary_left", "late_boundary_right", "late_boundary_curve"),
            reveal_steps=(14, 18, 22),
            normal_margin=0.010,
            terminal_margin_gap=0.040,
        ),
        FreshAmbiguitySourceSpec(
            source_family="curved_boundary_obstacle",
            task_family="T5",
            seed_base=base + 1300,
            seed_count=seed_count,
            hidden_capability_pairs=("yaw_weak|yaw_strong", "understeer|neutral"),
            geometry_keys=("curved_obstacle_left", "curved_obstacle_right", "curved_obstacle_s"),
            reveal_steps=(36, 44, 52),
            normal_margin=0.020,
            first_action_l2=0.070,
            prefix_action_l2=0.17,
            terminal_margin_gap=0.036,
        ),
    )


def _contains_asymmetric_fault_claim(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in ASYMMETRIC_FAULT_TOKENS)


def validate_source_spec(spec: FreshAmbiguitySourceSpec) -> list[str]:
    """Validate one source spec without running simulator or policy code."""

    errors: list[str] = []
    if not spec.source_family:
        errors.append("missing_source_family")
    if spec.task_family not in {"T4", "T5"}:
        errors.append("unknown_task_family")
    if int(spec.seed_base) < 0:
        errors.append("negative_seed_base")
    if int(spec.seed_count) <= 0:
        errors.append("nonpositive_seed_count")
    if not spec.hidden_capability_pairs:
        errors.append("missing_hidden_capability_pairs")
    if not spec.geometry_keys:
        errors.append("missing_geometry_keys")
    if not spec.reveal_steps:
        errors.append("missing_reveal_steps")
    if int(spec.decision_step_offset) <= 0:
        errors.append("nonpositive_decision_step_offset")
    if spec.labels_enter_actor_input:
        errors.append("labels_enter_actor_input")
    if spec.actor_input_contract_changed:
        errors.append("actor_input_contract_changed")
    if spec.proxy_fault_family and spec.simulator_scope != "single_track_symmetric_proxy":
        errors.append("proxy_fault_missing_symmetric_scope")
    if _contains_asymmetric_fault_claim(spec.source_family):
        errors.append("asymmetric_fault_claim_in_source_family")
    for value in (*spec.hidden_capability_pairs, *spec.geometry_keys):
        if _contains_asymmetric_fault_claim(value):
            errors.append("asymmetric_fault_claim_in_source_values")
            break
    return errors


def source_spec_to_row(spec: FreshAmbiguitySourceSpec) -> dict[str, object]:
    """Flatten one source-family spec for artifact CSVs."""

    return {
        "source_family": spec.source_family,
        "task_family": spec.task_family,
        "seed_base": spec.seed_base,
        "seed_count": spec.seed_count,
        "hidden_capability_pairs": "|".join(spec.hidden_capability_pairs),
        "geometry_keys": "|".join(spec.geometry_keys),
        "reveal_steps": "|".join(str(step) for step in spec.reveal_steps),
        "simulator_scope": spec.simulator_scope,
        "proxy_fault_family": spec.proxy_fault_family,
        "closed_t5_subset": spec.closed_t5_subset,
        "labels_enter_actor_input": spec.labels_enter_actor_input,
        "actor_input_contract_changed": spec.actor_input_contract_changed,
    }


def expand_source_spec(spec: FreshAmbiguitySourceSpec) -> list[FreshAmbiguitySourceRow]:
    """Expand a source spec into deterministic public pair-candidate rows."""

    errors = validate_source_spec(spec)
    if errors:
        raise ValueError(f"invalid source spec {spec.source_family!r}: {', '.join(errors)}")
    rows: list[FreshAmbiguitySourceRow] = []
    for index in range(int(spec.seed_count)):
        seed = int(spec.seed_base) + index
        pair = spec.hidden_capability_pairs[index % len(spec.hidden_capability_pairs)]
        geometry_key = spec.geometry_keys[index % len(spec.geometry_keys)]
        reveal_step = int(spec.reveal_steps[index % len(spec.reveal_steps)])
        rows.append(
            FreshAmbiguitySourceRow(
                source_family=spec.source_family,
                task_family=spec.task_family,
                source_index=index,
                seed=seed,
                hidden_capability_pair=pair,
                geometry_key=geometry_key,
                reveal_step=reveal_step,
                decision_step=reveal_step + int(spec.decision_step_offset),
                simulator_scope=spec.simulator_scope,
                proxy_fault_family=bool(spec.proxy_fault_family),
                closed_t5_subset=bool(spec.closed_t5_subset),
                scene_context_distance=float(spec.scene_context_distance),
                current_ego_distance=float(spec.current_ego_distance),
                recent_window_distance=float(spec.recent_window_distance),
                older_evidence_distance=float(spec.older_evidence_distance),
                hidden_capability_distance=float(spec.hidden_capability_distance),
                first_action_l2=float(spec.first_action_l2),
                prefix_action_l2=float(spec.prefix_action_l2),
                terminal_margin_gap=float(spec.terminal_margin_gap),
                normal_margin=float(spec.normal_margin),
                labels_enter_actor_input=bool(spec.labels_enter_actor_input),
                actor_input_contract_changed=bool(spec.actor_input_contract_changed),
            )
        )
    return rows


def expand_source_specs(specs: Sequence[FreshAmbiguitySourceSpec]) -> list[FreshAmbiguitySourceRow]:
    """Expand all source specs into deterministic public pair-candidate rows."""

    rows: list[FreshAmbiguitySourceRow] = []
    for spec in specs:
        rows.extend(expand_source_spec(spec))
    return rows


def row_id(row: FreshAmbiguitySourceRow) -> str:
    """Return stable row identifier for review and rejected-row artifacts."""

    return f"{row.source_family}|{row.seed}|{row.hidden_capability_pair}|{row.geometry_key}|{row.reveal_step}"


def classify_source_row(
    row: FreshAmbiguitySourceRow,
    thresholds: FreshAmbiguityThresholds | None = None,
) -> FreshAmbiguityClassification:
    """Classify one source row under public source-mining thresholds."""

    thresholds = thresholds or FreshAmbiguityThresholds()
    reasons: list[str] = []
    if row.labels_enter_actor_input:
        reasons.append("labels_enter_actor_input")
    if row.actor_input_contract_changed:
        reasons.append("actor_input_contract_changed")
    if row.candidate_materialized:
        reasons.append("candidate_materialized")
    if row.training_corpus_exported:
        reasons.append("training_corpus_exported")
    if float(row.scene_context_distance) > thresholds.max_scene_context_distance:
        reasons.append("scene_context_distance_too_large")
    if float(row.current_ego_distance) > thresholds.max_current_ego_distance:
        reasons.append("current_ego_distance_too_large")
    if float(row.recent_window_distance) > thresholds.max_recent_window_distance:
        reasons.append("recent_window_distance_too_large")
    if float(row.older_evidence_distance) < thresholds.min_older_evidence_distance:
        reasons.append("older_evidence_distance_too_small")
    if float(row.hidden_capability_distance) < thresholds.min_hidden_capability_distance:
        reasons.append("hidden_capability_distance_too_small")
    if float(row.first_action_l2) < thresholds.min_first_action_l2:
        reasons.append("first_action_l2_too_small")
    if float(row.prefix_action_l2) < thresholds.min_prefix_action_l2:
        reasons.append("prefix_action_l2_too_small")
    if float(row.terminal_margin_gap) < thresholds.min_terminal_margin_gap:
        reasons.append("terminal_margin_gap_too_small")
    if float(row.normal_margin) < thresholds.near_boundary_margin_min:
        reasons.append("normal_margin_below_window")
    if float(row.normal_margin) > thresholds.near_boundary_margin_max:
        reasons.append("normal_margin_above_window")
    return FreshAmbiguityClassification(row_id=row_id(row), accepted=not reasons, reasons=tuple(reasons))


def source_row_to_dict(
    row: FreshAmbiguitySourceRow,
    classification: FreshAmbiguityClassification | None = None,
) -> dict[str, object]:
    """Flatten one expanded row for CSV artifacts."""

    result = {
        "row_id": row_id(row),
        "source_family": row.source_family,
        "task_family": row.task_family,
        "source_index": row.source_index,
        "seed": row.seed,
        "hidden_capability_pair": row.hidden_capability_pair,
        "geometry_key": row.geometry_key,
        "reveal_step": row.reveal_step,
        "decision_step": row.decision_step,
        "simulator_scope": row.simulator_scope,
        "proxy_fault_family": row.proxy_fault_family,
        "closed_t5_subset": row.closed_t5_subset,
        "scene_context_distance": row.scene_context_distance,
        "current_ego_distance": row.current_ego_distance,
        "recent_window_distance": row.recent_window_distance,
        "older_evidence_distance": row.older_evidence_distance,
        "hidden_capability_distance": row.hidden_capability_distance,
        "first_action_l2": row.first_action_l2,
        "prefix_action_l2": row.prefix_action_l2,
        "terminal_margin_gap": row.terminal_margin_gap,
        "normal_margin": row.normal_margin,
        "labels_enter_actor_input": row.labels_enter_actor_input,
        "actor_input_contract_changed": row.actor_input_contract_changed,
        "candidate_materialized": row.candidate_materialized,
        "training_corpus_exported": row.training_corpus_exported,
    }
    if classification is not None:
        result["accepted"] = classification.accepted
        result["reasons"] = "|".join(classification.reasons)
    return result


def _source_family_summary(
    rows: Sequence[FreshAmbiguitySourceRow],
    classifications: Sequence[FreshAmbiguityClassification],
) -> list[dict[str, object]]:
    by_family: dict[str, list[tuple[FreshAmbiguitySourceRow, FreshAmbiguityClassification]]] = {}
    for row, classification in zip(rows, classifications):
        by_family.setdefault(row.source_family, []).append((row, classification))
    result: list[dict[str, object]] = []
    for family, family_rows in sorted(by_family.items()):
        row_values = [item[0] for item in family_rows]
        class_values = [item[1] for item in family_rows]
        result.append(
            {
                "source_family": family,
                "row_count": len(row_values),
                "accepted_count": sum(1 for item in class_values if item.accepted),
                "task_family": row_values[0].task_family if row_values else "",
                "proxy_fault_family": any(row.proxy_fault_family for row in row_values),
                "closed_t5_subset": any(row.closed_t5_subset for row in row_values),
                "simulator_scope": row_values[0].simulator_scope if row_values else "",
                "unique_seeds": len({row.seed for row in row_values}),
                "unique_hidden_capability_pairs": len({row.hidden_capability_pair for row in row_values}),
                "unique_geometry_keys": len({row.geometry_key for row in row_values}),
                "unique_decision_steps": len({row.decision_step for row in row_values}),
            }
        )
    return result


def build_guardrail_summary(config: FreshAmbiguityPlannerConfig, rows: Sequence[FreshAmbiguitySourceRow]) -> dict[str, object]:
    """Summarize no-materialization and no-training guardrails."""

    return {
        "private_holdout_used": bool(config.private_holdout_used),
        "training_started": bool(config.training_started),
        "evaluation_started": bool(config.evaluation_started),
        "replay_started": bool(config.replay_started),
        "ppo_used": bool(config.ppo_used),
        "promoted": bool(config.promoted),
        "training_corpus_exported": bool(config.training_corpus_exported)
        or any(row.training_corpus_exported for row in rows),
        "candidate_materialized": any(row.candidate_materialized for row in rows),
        "labels_enter_actor_input": any(row.labels_enter_actor_input for row in rows),
        "actor_input_contract_changed": any(row.actor_input_contract_changed for row in rows),
        "level3_self_id_claim_made": False,
    }


def build_source_planner_summary(
    config: FreshAmbiguityPlannerConfig,
    rows: Sequence[FreshAmbiguitySourceRow],
    classifications: Sequence[FreshAmbiguityClassification],
) -> dict[str, object]:
    """Build summary for the bounded fresh ambiguity planner smoke."""

    accepted_rows = [row for row, classification in zip(rows, classifications) if classification.accepted]
    family_counts = Counter(row.source_family for row in rows)
    accepted_family_counts = Counter(row.source_family for row in accepted_rows)
    total_rows = len(rows)
    closed_t5_rows = sum(1 for row in rows if row.closed_t5_subset)
    max_family_rows = max(family_counts.values(), default=0)
    proxy_fault_families = {row.source_family for row in rows if row.proxy_fault_family}
    guardrails = build_guardrail_summary(config, rows)
    guardrail_violation_count = sum(1 for value in guardrails.values() if bool(value))

    return {
        "result_class": "fresh_ambiguity_source_planner_summary",
        "source_plan_count": len(config.source_specs),
        "generated_source_specs": total_rows,
        "accepted_pair_candidates": len(accepted_rows),
        "source_families": [spec.source_family for spec in config.source_specs],
        "unique_source_families": len(family_counts),
        "unique_hidden_capability_pairs": len({row.hidden_capability_pair for row in rows}),
        "unique_geometry_keys": len({row.geometry_key for row in rows}),
        "unique_decision_steps": len({row.decision_step for row in rows}),
        "source_family_candidate_counts": dict(sorted(family_counts.items())),
        "accepted_source_family_counts": dict(sorted(accepted_family_counts.items())),
        "max_single_source_family_share": float(max_family_rows / total_rows) if total_rows else 0.0,
        "closed_t5_subset_rows": closed_t5_rows,
        "max_closed_t5_subset_share": float(closed_t5_rows / total_rows) if total_rows else 0.0,
        "proxy_fault_family_count": len(proxy_fault_families),
        "proxy_fault_families": sorted(proxy_fault_families),
        "symmetric_proxy_fault_only": all(
            (not row.proxy_fault_family) or row.simulator_scope == "single_track_symmetric_proxy" for row in rows
        ),
        "guardrails": guardrails,
        "guardrail_violation_count": guardrail_violation_count,
        "candidate_materialized": guardrails["candidate_materialized"],
        "training_started": guardrails["training_started"],
        "evaluation_started": guardrails["evaluation_started"],
        "replay_started": guardrails["replay_started"],
        "ppo_used": guardrails["ppo_used"],
        "promoted": guardrails["promoted"],
        "private_holdout_used": guardrails["private_holdout_used"],
        "actor_input_contract_changed": guardrails["actor_input_contract_changed"],
        "training_corpus_exported": guardrails["training_corpus_exported"],
        "labels_enter_actor_input": guardrails["labels_enter_actor_input"],
        "level3_self_id_claim_made": False,
        "passes_public_dry_gates": (
            total_rows >= 96
            and len(accepted_rows) >= 24
            and len(family_counts) >= 8
            and len(proxy_fault_families) >= config.thresholds.min_proxy_fault_family_count
            and (float(max_family_rows / total_rows) if total_rows else 1.0)
            <= config.thresholds.max_single_source_family_share
            and (float(closed_t5_rows / total_rows) if total_rows else 1.0)
            <= config.thresholds.max_closed_t5_subset_share
            and guardrail_violation_count == 0
        ),
    }


def _trace_snapshot_rows(rows: Sequence[FreshAmbiguitySourceRow]) -> list[dict[str, object]]:
    snapshots: list[dict[str, object]] = []
    for row in rows:
        for anchor in SNAPSHOT_ANCHORS:
            offset = {
                "reveal": 0,
                "reveal_plus_4": 4,
                "decision_minus_8": row.decision_step - row.reveal_step - 8,
                "decision": row.decision_step - row.reveal_step,
                "post_decision_plus_8": row.decision_step - row.reveal_step + 8,
            }[anchor]
            snapshots.append(
                {
                    "row_id": row_id(row),
                    "source_family": row.source_family,
                    "anchor": anchor,
                    "planned_step": row.reveal_step + int(offset),
                    "measured_rollout": False,
                }
            )
    return snapshots


def run_source_planner_smoke(
    output_dir: Path | str,
    *,
    seed: int = 1528,
    seed_count: int = 8,
) -> dict[str, object]:
    """Run the bounded no-training fresh ambiguity source-planner smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    config = FreshAmbiguityPlannerConfig(source_specs=default_source_specs(seed=seed, seed_count=seed_count))
    rows = expand_source_specs(config.source_specs)
    classifications = [classify_source_row(row, thresholds=config.thresholds) for row in rows]
    row_dicts = [source_row_to_dict(row, classification) for row, classification in zip(rows, classifications)]
    rejected_rows = [row for row in row_dicts if not row.get("accepted")]
    divergence_rows = [
        {
            "row_id": row_id(row),
            "source_family": row.source_family,
            "first_action_l2": row.first_action_l2,
            "prefix_action_l2": row.prefix_action_l2,
            "terminal_margin_gap": row.terminal_margin_gap,
            "normal_margin": row.normal_margin,
            "measured_rollout": False,
        }
        for row in rows
    ]
    family_rows = _source_family_summary(rows, classifications)
    guardrail_summary = build_guardrail_summary(config, rows)
    summary = build_source_planner_summary(config, rows, classifications)

    write_csv_rows(output / "fresh_ambiguity_source_specs.csv", [source_spec_to_row(spec) for spec in config.source_specs])
    write_csv_rows(output / "fresh_ambiguity_pair_candidates.csv", row_dicts)
    write_csv_rows(output / "fresh_ambiguity_action_divergence.csv", divergence_rows)
    write_csv_rows(output / "fresh_ambiguity_rejected_pairs.csv", rejected_rows)
    write_csv_rows(output / "fresh_ambiguity_source_family_summary.csv", family_rows)
    write_csv_rows(output / "fresh_ambiguity_guardrail_summary.csv", [guardrail_summary])
    write_csv_rows(output / "fresh_ambiguity_trace_snapshots.csv", _trace_snapshot_rows(rows))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training fresh ambiguity source-planner smoke.")
    parser.add_argument("--output-dir", type=Path, default=Path("runs/m1528_fresh_ambiguity_source_planner_smoke"))
    parser.add_argument("--seed", type=int, default=1528)
    parser.add_argument("--seed-count", type=int, default=8)
    args = parser.parse_args()
    summary = run_source_planner_smoke(args.output_dir, seed=int(args.seed), seed_count=int(args.seed_count))
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"generated_source_specs={summary['generated_source_specs']}")
    print(f"accepted_pair_candidates={summary['accepted_pair_candidates']}")
    print(f"passes_public_dry_gates={summary['passes_public_dry_gates']}")


if __name__ == "__main__":
    main()
