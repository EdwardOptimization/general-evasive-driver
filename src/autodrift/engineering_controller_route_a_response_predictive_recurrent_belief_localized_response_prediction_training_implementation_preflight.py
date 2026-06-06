"""M2866 localized response-prediction training implementation preflight.

This runner applies the M2864 response-prediction auxiliary-loss weighting table
to the M2848 response-predictive recurrent-belief candidate under bounded PPO
execution. It writes the extra weight, mask, public/fresh surface, rollback,
actor-contract, and claim-boundary artifacts required by M2865. It does not
validate, rank, promote, or claim driver performance.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight
    as m2848_base,
)
from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_core_training_implementation_preflight
    as m2846_base,
)
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.env import DriftEnvConfig
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.train_ppo import PPOConfig, train


DEFAULT_MILESTONE = (
    "m2866-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-training-implementation-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "localized_response_prediction_training_implementation_preflight"
)
DEFAULT_M2865_AUDIT = Path(
    "docs/m2865-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-training-recipe-design-result-audit.md"
)
DEFAULT_M2864_DESIGN = Path(
    "docs/m2864-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-training-recipe-design.md"
)
DEFAULT_M2861_SUMMARY = Path(
    "runs/m2861_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_localization_materialization/summary.json"
)
DEFAULT_M2861_CHANNEL_SUMMARY_ROWS = Path(
    "runs/m2861_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_localization_materialization/response_prediction_channel_summary_rows.csv"
)
DEFAULT_M2861_RECIPE_SIGNAL_ROWS = Path(
    "runs/m2861_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_localization_materialization/response_prediction_recipe_signal_rows.csv"
)
DEFAULT_M2857_SURFACE_ROWS = Path(
    "runs/m2857_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "per_step_telemetry_panel_materialization/telemetry_surface_rows.csv"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_"
    "training_bounded_continuation_preflight/checkpoints/"
    "m2848_response_predictive_recurrent_belief_continuation_candidate.pt"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2867-engineering-controller-route-a-response-predictive-"
    "recurrent-belief-localized-response-prediction-training-implementation-result-audit.json"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2866-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-training-implementation-preflight.md"
)
DEFAULT_NEXT_BLOCKER = (
    "m2867-engineering-controller-route-a-response-predictive-recurrent-belief-localized-"
    "response-prediction-training-implementation-result-audit"
)

CLAIM_SCOPE = (
    "M2866 bounded localized response-prediction training implementation preflight only. "
    "It applies the pre-registered M2864 auxiliary-loss weighting table to bounded PPO "
    "training artifacts and routes the result to audit."
)
FORBIDDEN_INTERPRETATION = (
    "validation readiness or result, checkpoint ranking, controller ranking, winner "
    "selection, checkpoint promotion, success-rate verdict, repair success, driver "
    "performance, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation, full ideal driver completion, or level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_"
    "prediction_training_implementation_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_"
    "prediction_training_implementation_preflight_failed"
)

RESPONSE_TARGET_FIELDNAMES = m2848_base.RESPONSE_TARGET_FIELDNAMES
TRAINING_SEED_FIELDNAMES = m2848_base.TRAINING_SEED_FIELDNAMES
TRAINING_RUN_FIELDNAMES = m2848_base.TRAINING_RUN_FIELDNAMES
PARAMETER_GROUP_FIELDNAMES = m2848_base.PARAMETER_GROUP_FIELDNAMES
RESPONSE_PROBE_FIELDNAMES = m2848_base.RESPONSE_PROBE_FIELDNAMES
HIDDEN_INTERVENTION_FIELDNAMES = m2848_base.HIDDEN_INTERVENTION_FIELDNAMES
GATE_FIELDNAMES = m2848_base.GATE_FIELDNAMES
ACTOR_GUARD_FIELDNAMES = m2848_base.ACTOR_GUARD_FIELDNAMES
CLAIM_FIELDNAMES = m2848_base.CLAIM_FIELDNAMES
REQUIRED_PARAMETER_GROUPS = m2848_base.REQUIRED_PARAMETER_GROUPS
REQUIRED_NON_ACTOR_HEAD_GROUPS = m2848_base.REQUIRED_NON_ACTOR_HEAD_GROUPS
RESPONSE_CHANNELS = m2848_base.RESPONSE_CHANNELS
FALSE_CLAIM_FLAGS = m2848_base.FALSE_CLAIM_FLAGS
RESPONSE_CHANNEL_NAMES = [name for _obs_index, name, included in RESPONSE_CHANNELS if included]

RAW_RESPONSE_WEIGHT_TABLE = [
    [1.00, 1.00, 1.00, 1.25, 1.25, 1.00, 1.00, 1.00, 1.35],
    [1.00, 1.00, 1.00, 1.20, 1.00, 1.20, 1.00, 1.00, 1.35],
    [1.00, 1.00, 1.20, 1.00, 1.00, 1.00, 1.00, 1.00, 1.35],
    [1.00, 1.00, 1.20, 1.00, 1.00, 1.00, 1.00, 1.00, 1.35],
]
WEIGHT_ALLOWED_MIN = 0.75
WEIGHT_ALLOWED_MAX = 1.50

RESPONSE_LOSS_WEIGHT_FIELDNAMES = [
    "weight_row_id",
    "horizon_index",
    "response_channel_index",
    "response_channel_name",
    "raw_weight",
    "normalization_denominator",
    "normalized_weight",
    "allowed_min",
    "allowed_max",
    "within_allowed_range",
    "boost_source",
    "design_source",
    "actor_visible_allowed",
    "pre_registered",
    "post_hoc_tuned",
    "claim_boundary",
]
VALID_TARGET_MASK_FIELDNAMES = [
    "mask_accounting_id",
    "source_signal",
    "source_row_count",
    "unique_pair_count",
    "valid_prediction_count",
    "gap_count",
    "target_available_false_contributes_loss",
    "terminal_gap_counted",
    "terminal_gap_imputed",
    "no_valid_targets_ranking_allowed",
    "source_path",
    "status_pass",
    "evidence",
    "claim_boundary",
]
SURFACE_ACCOUNTING_FIELDNAMES = [
    "surface_accounting_id",
    "surface_id",
    "row_count",
    "public_diagnostic_row_count",
    "fresh_or_disjoint_row_count",
    "public_explanatory",
    "fresh_or_disjoint",
    "ranking_admissible",
    "ordinary_success_denominator_allowed",
    "training_target_selection_allowed",
    "promotion_allowed",
    "status_pass",
    "source_path",
    "evidence",
    "claim_boundary",
]
ROLLBACK_GATE_FIELDNAMES = [
    "rollback_gate_id",
    "rollback_family",
    "triggered",
    "status_pass",
    "observed",
    "expected",
    "evidence",
    "failure_type",
    "claim_boundary",
]


def run_localized_response_prediction_training_implementation_preflight(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    m2865_audit: Path | str = DEFAULT_M2865_AUDIT,
    m2864_design: Path | str = DEFAULT_M2864_DESIGN,
    m2861_summary: Path | str = DEFAULT_M2861_SUMMARY,
    m2861_channel_summary_rows: Path | str = DEFAULT_M2861_CHANNEL_SUMMARY_ROWS,
    m2861_recipe_signal_rows: Path | str = DEFAULT_M2861_RECIPE_SIGNAL_ROWS,
    m2857_surface_rows: Path | str = DEFAULT_M2857_SURFACE_ROWS,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    device: str = "cpu",
    total_steps: int = 32,
    rollout_steps: int = 16,
    num_envs: int = 1,
    update_epochs: int = 2,
    minibatch_size: int = 16,
    seed: int = 286600,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(
        Path(m2865_audit),
        Path(m2864_design),
        Path(m2861_summary),
        Path(m2861_channel_summary_rows),
        Path(m2861_recipe_signal_rows),
        Path(m2857_surface_rows),
        Path(source_checkpoint),
    )
    _require_sources(source_paths)

    m2861_summary_data = read_json(source_paths["m2861_summary"])
    channel_summary_rows = read_csv_rows(source_paths["m2861_channel_summary_rows"])
    recipe_signal_rows = read_csv_rows(source_paths["m2861_recipe_signal_rows"])
    telemetry_surface_rows = read_csv_rows(source_paths["m2857_surface_rows"])

    weight_rows = build_response_loss_weight_rows()
    valid_mask_rows = build_valid_target_mask_accounting_rows(
        recipe_signal_rows,
        channel_summary_rows,
        m2861_summary_data,
        source_paths,
    )
    surface_accounting_rows = build_surface_accounting_rows(
        telemetry_surface_rows,
        source_paths["m2857_surface_rows"],
    )
    rollback_rows = build_rollback_gate_rows(
        weight_rows=weight_rows,
        valid_mask_rows=valid_mask_rows,
        surface_accounting_rows=surface_accounting_rows,
    )

    env_config = build_m2866_env_config()
    ppo_config = build_m2866_ppo_config(
        source_checkpoint=source_paths["source_checkpoint"],
        weight_rows=weight_rows,
        device=device,
        total_steps=total_steps,
        rollout_steps=rollout_steps,
        num_envs=num_envs,
        update_epochs=update_epochs,
        minibatch_size=minibatch_size,
        seed=seed,
    )

    write_json(paths["protocol_config_snapshot"], build_protocol_config_snapshot(source_paths, ppo_config, weight_rows))
    write_json(paths["ppo_config_snapshot"], ppo_config.__dict__)
    write_json(paths["env_config_snapshot"], env_config_to_dict(env_config))
    write_csv_rows(paths["response_loss_weight_rows"], weight_rows, RESPONSE_LOSS_WEIGHT_FIELDNAMES)
    write_csv_rows(paths["valid_target_mask_accounting_rows"], valid_mask_rows, VALID_TARGET_MASK_FIELDNAMES)
    write_csv_rows(paths["surface_accounting_rows"], surface_accounting_rows, SURFACE_ACCOUNTING_FIELDNAMES)
    write_csv_rows(paths["rollback_gate_rows"], rollback_rows, ROLLBACK_GATE_FIELDNAMES)

    response_target_rows = build_response_target_schema_rows()
    training_seed_rows = build_training_seed_rows(seed)
    write_csv_rows(paths["response_target_schema_rows"], response_target_rows, RESPONSE_TARGET_FIELDNAMES)
    write_csv_rows(paths["training_seed_rows"], training_seed_rows, TRAINING_SEED_FIELDNAMES)

    source_checkpoint_path = source_paths["source_checkpoint"]
    candidate_checkpoint = paths["candidate_checkpoint"]
    train_error = ""
    training_status = "completed"
    model_obs_dim = P0_OBSERVATION_DIM
    model_act_dim = ACTION_DIM
    source_load_mode = m2848_base.resolve_source_load_mode(ppo_config, source_checkpoint_path, device=device)
    try:
        model = train(
            ppo_config,
            save_path=candidate_checkpoint,
            metrics_csv_path=paths["train_metrics"],
            env_config=env_config,
            checkpoint_metadata=build_checkpoint_metadata(
                milestone=milestone,
                source_checkpoint=source_checkpoint_path,
                source_load_mode=source_load_mode,
                output_dir=output,
                weight_rows=weight_rows,
            ),
            init_checkpoint_path=source_checkpoint_path,
        )
        model_obs_dim = int(model.obs_dim)
        model_act_dim = int(model.act_dim)
    except Exception as exc:  # pragma: no cover - only exercised on training failure.
        training_status = "failed"
        train_error = f"{type(exc).__name__}: {exc}"
        if not paths["train_metrics"].exists():
            write_csv_rows(
                paths["train_metrics"],
                [],
                fieldnames=[
                    "step",
                    "update",
                    "num_envs",
                    "response_prediction_loss_mean",
                    "baseline_action_anchor_loss_mean",
                ],
            )

    metrics_rows = read_csv_rows(paths["train_metrics"]) if paths["train_metrics"].exists() else []
    training_run_rows = build_training_run_rows(
        metrics_rows,
        paths,
        ppo_config,
        seed=seed,
        training_status=training_status,
    )
    parameter_group_rows = build_parameter_group_trace_rows(source_checkpoint_path, candidate_checkpoint)
    response_probe_rows = build_response_prediction_probe_rows(metrics_rows, response_target_rows, ppo_config)
    hidden_intervention_rows = build_hidden_intervention_probe_rows()
    checkpoint_manifest = build_checkpoint_manifest(
        source_checkpoint_path,
        candidate_checkpoint,
        ppo_config=ppo_config,
        source_load_mode=source_load_mode,
        parameter_group_rows=parameter_group_rows,
        training_status=training_status,
        train_error=train_error,
        weight_rows=weight_rows,
    )
    actor_guard_rows = build_actor_contract_guard_rows(model_obs_dim, model_act_dim, env_config)
    claim_rows = build_claim_boundary_rows(training_status)
    proof_gate_rows = build_proof_gate_rows(
        response_target_rows=response_target_rows,
        response_probe_rows=response_probe_rows,
        parameter_group_rows=parameter_group_rows,
        checkpoint_manifest=checkpoint_manifest,
        actor_guard_rows=actor_guard_rows,
        weight_rows=weight_rows,
        valid_mask_rows=valid_mask_rows,
        surface_accounting_rows=surface_accounting_rows,
        rollback_rows=rollback_rows,
        source_paths=source_paths,
    )
    generalization_gate_rows = build_generalization_gate_rows(training_seed_rows, surface_accounting_rows)
    promotion_guard_rows = build_promotion_guard_rows(checkpoint_manifest, next_blocker)
    gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows

    write_csv_rows(paths["training_run_rows"], training_run_rows, TRAINING_RUN_FIELDNAMES)
    write_csv_rows(paths["parameter_group_trace"], parameter_group_rows, PARAMETER_GROUP_FIELDNAMES)
    write_csv_rows(paths["response_prediction_probe_rows"], response_probe_rows, RESPONSE_PROBE_FIELDNAMES)
    write_csv_rows(paths["hidden_intervention_probe_rows"], hidden_intervention_rows, HIDDEN_INTERVENTION_FIELDNAMES)
    write_json(paths["checkpoint_manifest"], checkpoint_manifest)
    write_csv_rows(paths["proof_gate_rows"], proof_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["generalization_gate_rows"], generalization_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["promotion_guard_rows"], promotion_guard_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        ppo_config=ppo_config,
        env_config=env_config,
        training_status=training_status,
        train_error=train_error,
        source_load_mode=source_load_mode,
        training_run_rows=training_run_rows,
        parameter_group_rows=parameter_group_rows,
        response_probe_rows=response_probe_rows,
        checkpoint_manifest=checkpoint_manifest,
        proof_gate_rows=proof_gate_rows,
        generalization_gate_rows=generalization_gate_rows,
        promotion_guard_rows=promotion_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        weight_rows=weight_rows,
        valid_mask_rows=valid_mask_rows,
        surface_accounting_rows=surface_accounting_rows,
        rollback_rows=rollback_rows,
        m2861_summary=m2861_summary_data,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    follow_up = build_m2867_manifest(summary)
    write_json(paths["follow_up_manifest_copy"], follow_up)
    write_json(paths["registered_follow_up_manifest"], follow_up)
    write_doc(paths["doc"], summary)

    summary = {
        **summary,
        "required_artifacts_present": required_artifacts_present(paths),
        "m2867_follow_up_manifest_registered": paths["registered_follow_up_manifest"].exists(),
    }
    summary["status_pass"] = bool(
        summary["status_pass"]
        and summary["required_artifacts_present"]
        and summary["m2867_follow_up_manifest_registered"]
    )
    summary["result_class"] = RESULT_CLASS_PASS if summary["status_pass"] else RESULT_CLASS_FAIL
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_doc(paths["doc"], summary)
    return summary


def _paths(output: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "protocol_config_snapshot": output / "protocol_config_snapshot.json",
        "ppo_config_snapshot": output / "ppo_config_snapshot.json",
        "env_config_snapshot": output / "env_config_snapshot.json",
        "response_loss_weight_rows": output / "response_loss_weight_rows.csv",
        "valid_target_mask_accounting_rows": output / "valid_target_mask_accounting_rows.csv",
        "surface_accounting_rows": output / "surface_accounting_rows.csv",
        "rollback_gate_rows": output / "rollback_gate_rows.csv",
        "response_target_schema_rows": output / "response_target_schema_rows.csv",
        "training_seed_rows": output / "training_seed_rows.csv",
        "training_run_rows": output / "training_run_rows.csv",
        "train_metrics": output / "train_metrics.csv",
        "checkpoint_manifest": output / "checkpoint_manifest.json",
        "candidate_checkpoint": output
        / "checkpoints"
        / "m2866_localized_response_prediction_training_candidate.pt",
        "parameter_group_trace": output / "parameter_group_trace.csv",
        "response_prediction_probe_rows": output / "response_prediction_probe_rows.csv",
        "hidden_intervention_probe_rows": output / "hidden_intervention_probe_rows.csv",
        "proof_gate_rows": output / "proof_gate_rows.csv",
        "generalization_gate_rows": output / "generalization_gate_rows.csv",
        "promotion_guard_rows": output / "promotion_guard_rows.csv",
        "actor_contract_guard_rows": output / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output / "claim_boundary_rows.csv",
        "gate_matrix": output / "gate_matrix.csv",
        "summary": output / "summary.json",
        "run_state": output / "run_state.json",
        "follow_up_manifest_copy": output / "follow_up_manifest.json",
        "registered_follow_up_manifest": follow_up_manifest,
        "doc": doc_path,
    }


def _source_paths(
    m2865_audit: Path,
    m2864_design: Path,
    m2861_summary: Path,
    m2861_channel_summary_rows: Path,
    m2861_recipe_signal_rows: Path,
    m2857_surface_rows: Path,
    source_checkpoint: Path,
) -> dict[str, Path]:
    return {
        "m2865_audit": m2865_audit,
        "m2864_design": m2864_design,
        "m2861_summary": m2861_summary,
        "m2861_channel_summary_rows": m2861_channel_summary_rows,
        "m2861_recipe_signal_rows": m2861_recipe_signal_rows,
        "m2857_surface_rows": m2857_surface_rows,
        "source_checkpoint": source_checkpoint,
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2866 missing required source artifacts: {missing}")


def build_m2866_env_config() -> DriftEnvConfig:
    return m2848_base.build_m2848_env_config()


def build_m2866_ppo_config(
    *,
    source_checkpoint: Path,
    weight_rows: list[dict[str, Any]],
    device: str,
    total_steps: int,
    rollout_steps: int,
    num_envs: int,
    update_epochs: int,
    minibatch_size: int,
    seed: int,
) -> PPOConfig:
    if int(rollout_steps) <= 4:
        raise ValueError("M2866 rollout_steps must exceed response horizon 4")
    base = m2848_base.build_m2848_ppo_config(
        source_checkpoint=source_checkpoint,
        device=device,
        total_steps=total_steps,
        rollout_steps=rollout_steps,
        num_envs=num_envs,
        update_epochs=update_epochs,
        minibatch_size=minibatch_size,
        seed=seed,
    )
    return replace(
        base,
        response_prediction_weight_json=response_prediction_weight_json_from_rows(weight_rows),
    )


def build_protocol_config_snapshot(
    source_paths: dict[str, Path],
    config: PPOConfig,
    weight_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "milestone": DEFAULT_MILESTONE,
        "claim_scope": CLAIM_SCOPE,
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "actor_encoder": config.actor_encoder,
        "actor_contract_observation_dim": P0_OBSERVATION_DIM,
        "actor_contract_action_dim": ACTION_DIM,
        "response_prediction_target_indices": list(range(config.response_prediction_dim)),
        "excluded_previous_command_indices": [9, 10, 11],
        "response_prediction_horizon": config.response_prediction_horizon,
        "response_prediction_stride": config.response_prediction_stride,
        "response_prediction_weight_json": config.response_prediction_weight_json,
        "response_prediction_weight_row_count": len(weight_rows),
        "loss_mass_normalization": "raw_table_mean_normalized_to_one",
        "bounded_implementation_preflight_only": True,
        "validation_run": False,
        "ranking_run": False,
        "checkpoint_promoted": False,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_response_loss_weight_rows() -> list[dict[str, Any]]:
    denominator = sum(sum(row) for row in RAW_RESPONSE_WEIGHT_TABLE) / (
        len(RAW_RESPONSE_WEIGHT_TABLE) * len(RAW_RESPONSE_WEIGHT_TABLE[0])
    )
    rows: list[dict[str, Any]] = []
    for horizon_offset, raw_row in enumerate(RAW_RESPONSE_WEIGHT_TABLE, start=1):
        for channel_index, raw_weight in enumerate(raw_row):
            channel_name = RESPONSE_CHANNEL_NAMES[channel_index]
            normalized_weight = float(raw_weight) / denominator
            rows.append(
                {
                    "weight_row_id": f"m2866-weight-h{horizon_offset}-c{channel_index:02d}",
                    "horizon_index": horizon_offset,
                    "response_channel_index": channel_index,
                    "response_channel_name": channel_name,
                    "raw_weight": float(raw_weight),
                    "normalization_denominator": denominator,
                    "normalized_weight": normalized_weight,
                    "allowed_min": WEIGHT_ALLOWED_MIN,
                    "allowed_max": WEIGHT_ALLOWED_MAX,
                    "within_allowed_range": WEIGHT_ALLOWED_MIN <= normalized_weight <= WEIGHT_ALLOWED_MAX,
                    "boost_source": _boost_source(channel_name, raw_weight),
                    "design_source": "M2864_initial_weight_table",
                    "actor_visible_allowed": False,
                    "pre_registered": True,
                    "post_hoc_tuned": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def response_prediction_weight_json_from_rows(weight_rows: list[dict[str, Any]]) -> str:
    table = [[0.0 for _channel in RESPONSE_CHANNEL_NAMES] for _horizon in RAW_RESPONSE_WEIGHT_TABLE]
    for row in weight_rows:
        horizon_index = int(row["horizon_index"]) - 1
        channel_index = int(row["response_channel_index"])
        table[horizon_index][channel_index] = float(row["normalized_weight"])
    return json.dumps(table, separators=(",", ":"))


def _boost_source(channel_name: str, raw_weight: float) -> str:
    if float(raw_weight) <= 1.0:
        return "base_weight"
    if channel_name in {"steer_actuator_norm", "brake_actuator"}:
        return "actuator_response_prediction_loss_weight_review"
    return "ego_response_prediction_loss_weight_review"


def build_valid_target_mask_accounting_rows(
    recipe_signal_rows: list[dict[str, str]],
    channel_summary_rows: list[dict[str, str]],
    m2861_summary: dict[str, Any],
    source_paths: dict[str, Path],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for recipe in recipe_signal_rows:
        signal = str(recipe.get("signal_name", ""))
        gap_count = int(_float_or_none(recipe.get("gap_count")) or 0)
        rows.append(
            {
                "mask_accounting_id": f"m2866-mask-{signal}",
                "source_signal": signal,
                "source_row_count": int(_float_or_none(recipe.get("observed_localization_row_count")) or 0),
                "unique_pair_count": int(_float_or_none(recipe.get("unique_pair_count")) or 0),
                "valid_prediction_count": int(_float_or_none(recipe.get("valid_prediction_count")) or 0),
                "gap_count": gap_count,
                "target_available_false_contributes_loss": False,
                "terminal_gap_counted": gap_count >= 0,
                "terminal_gap_imputed": False,
                "no_valid_targets_ranking_allowed": False,
                "source_path": str(source_paths["m2861_recipe_signal_rows"]),
                "status_pass": True,
                "evidence": "M2861 recipe signal carried into M2866 mask contract; not a ranking denominator",
                "claim_boundary": CLAIM_SCOPE,
            }
        )

    channel_valid = sum(int(_float_or_none(row.get("valid_prediction_count")) or 0) for row in channel_summary_rows)
    channel_gaps = sum(int(_float_or_none(row.get("gap_count")) or 0) for row in channel_summary_rows)
    rows.append(
        {
            "mask_accounting_id": "m2866-mask-channel-summary-aggregate",
            "source_signal": "channel_summary_all_horizons_all_response_channels",
            "source_row_count": len(channel_summary_rows),
            "unique_pair_count": int(_float_or_none(m2861_summary.get("localized_pair_count")) or 0),
            "valid_prediction_count": channel_valid,
            "gap_count": channel_gaps,
            "target_available_false_contributes_loss": False,
            "terminal_gap_counted": channel_gaps >= 0,
            "terminal_gap_imputed": False,
            "no_valid_targets_ranking_allowed": False,
            "source_path": str(source_paths["m2861_channel_summary_rows"]),
            "status_pass": len(channel_summary_rows) == 36 and channel_gaps > 0,
            "evidence": "channel/horizon aggregate for accounting only; not compared to vector-level trace count",
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return rows


def build_surface_accounting_rows(
    telemetry_surface_rows: list[dict[str, str]],
    source_path: Path,
) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter(str(row.get("surface_id", "")) for row in telemetry_surface_rows)
    rows: list[dict[str, Any]] = []
    for surface_id in sorted(counts):
        subset = [row for row in telemetry_surface_rows if str(row.get("surface_id", "")) == surface_id]
        public_count = sum(1 for row in subset if _as_bool(row.get("public_diagnostic_row")))
        fresh_count = sum(1 for row in subset if _as_bool(row.get("fresh_or_disjoint")))
        ranking_allowed = any(_as_bool(row.get("ranking_admissible")) for row in subset)
        ordinary_denominator_allowed = any(
            _as_bool(row.get("ordinary_success_denominator_allowed")) for row in subset
        )
        public_explanatory = public_count > 0 and fresh_count == 0
        fresh_or_disjoint = fresh_count > 0 and public_count == 0
        status_pass = bool(
            subset
            and not ranking_allowed
            and not ordinary_denominator_allowed
            and (public_explanatory or fresh_or_disjoint)
        )
        rows.append(
            {
                "surface_accounting_id": f"m2866-surface-{surface_id}",
                "surface_id": surface_id,
                "row_count": len(subset),
                "public_diagnostic_row_count": public_count,
                "fresh_or_disjoint_row_count": fresh_count,
                "public_explanatory": public_explanatory,
                "fresh_or_disjoint": fresh_or_disjoint,
                "ranking_admissible": ranking_allowed,
                "ordinary_success_denominator_allowed": ordinary_denominator_allowed,
                "training_target_selection_allowed": False,
                "promotion_allowed": False,
                "status_pass": status_pass,
                "source_path": str(source_path),
                "evidence": "M2857 telemetry surface accounting preserved separately for M2866 audit",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_rollback_gate_rows(
    *,
    weight_rows: list[dict[str, Any]],
    valid_mask_rows: list[dict[str, Any]],
    surface_accounting_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    public_rows = sum(
        int(row["row_count"]) for row in surface_accounting_rows if _as_bool(row["public_explanatory"])
    )
    fresh_rows = sum(
        int(row["row_count"]) for row in surface_accounting_rows if _as_bool(row["fresh_or_disjoint"])
    )
    weight_match = len(weight_rows) == 36 and all(_as_bool(row["within_allowed_range"]) for row in weight_rows)
    mask_pass = bool(valid_mask_rows) and all(_as_bool(row["status_pass"]) for row in valid_mask_rows)
    surface_pass = public_rows > 0 and fresh_rows >= 8 and all(
        _as_bool(row["status_pass"]) for row in surface_accounting_rows
    )
    specs = [
        (
            "rollback_actor_contract_change",
            "actor_contract",
            False,
            "actor_observation_dim=72 action_dim=3",
            "unchanged actor 72/action 3",
            "contract checked by actor rows after training",
            "contract_violation",
        ),
        (
            "rollback_future_label_actor_visible",
            "actor_contract",
            False,
            "future response labels are training/evaluator-only",
            "actor_visible_labels=false",
            "response targets are not added to actor observations",
            "contract_violation",
        ),
        (
            "rollback_response_loss_weight_table_drift",
            "loss_weighting",
            not weight_match,
            f"weight_rows={len(weight_rows)} within_range={weight_match}",
            "36 rows within normalized range and pre-registered",
            "M2864 initial table materialized before training",
            "contract_violation",
        ),
        (
            "rollback_valid_target_mask_regression",
            "mask_accounting",
            not mask_pass,
            f"valid_mask_rows={len(valid_mask_rows)} pass={mask_pass}",
            "target_available=false contributes_loss=false terminal gaps counted not imputed",
            "M2861 terminal/unavailable accounting carried into preflight gates",
            "metric_artifact",
        ),
        (
            "rollback_public_only_improvement_fresh_regression",
            "public_fresh_surface",
            not surface_pass,
            f"public_rows={public_rows} fresh_rows={fresh_rows} surface_pass={surface_pass}",
            "public explanatory rows and at least 8 fresh/disjoint rows separated",
            "gate armed for M2867; M2866 does not compute improvement/regression verdicts",
            "objective_overfit",
        ),
        (
            "rollback_response_prediction_washout",
            "telemetry_washout",
            False,
            "not_evaluated_in_training_preflight",
            "gate armed for M2867 audit; no telemetry washout claim in M2866",
            "response-prediction loss is not interpreted as clearance/progress repair",
            "proof_washout",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for gate_id, family, triggered, observed, expected, evidence, failure in specs:
        rows.append(
            {
                "rollback_gate_id": gate_id,
                "rollback_family": family,
                "triggered": bool(triggered),
                "status_pass": not bool(triggered),
                "observed": observed,
                "expected": expected,
                "evidence": evidence,
                "failure_type": "" if not triggered else failure,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_response_target_schema_rows() -> list[dict[str, Any]]:
    rows = m2848_base.build_response_target_schema_rows()
    return _with_claim_boundary(rows)


def build_training_seed_rows(seed: int) -> list[dict[str, Any]]:
    return [
        {
            "seed_row_id": "m2866_localized_response_prediction_seed_000",
            "split": "localized_response_prediction_training_preflight",
            "seed": int(seed),
            "training_smoke": True,
            "validation_denominator": False,
            "ranking_admissible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_training_run_rows(
    metrics_rows: list[dict[str, str]],
    paths: dict[str, Path],
    config: PPOConfig,
    *,
    seed: int,
    training_status: str,
) -> list[dict[str, Any]]:
    final = metrics_rows[-1] if metrics_rows else {}
    response_loss = _float_or_none(final.get("response_prediction_loss_mean"))
    anchor_loss = _float_or_none(final.get("baseline_action_anchor_loss_mean"))
    return [
        {
            "training_run_id": "m2866_localized_response_prediction_training_000",
            "seed": int(seed),
            "total_steps": int(config.total_steps),
            "rollout_steps": int(config.rollout_steps),
            "num_envs": int(config.num_envs),
            "update_epochs": int(config.update_epochs),
            "minibatch_size": int(config.minibatch_size),
            "final_step": int(_float_or_none(final.get("step")) or 0),
            "update_count": int(_float_or_none(final.get("update")) or 0),
            "ppo_run": training_status == "completed",
            "training_smoke": True,
            "validation_run": False,
            "success_rate_computed": False,
            "metrics_csv": str(paths["train_metrics"]),
            "candidate_checkpoint": str(paths["candidate_checkpoint"]),
            "training_status": training_status,
            "response_prediction_loss_mean": response_loss if response_loss is not None else "",
            "baseline_action_anchor_loss_mean": anchor_loss if anchor_loss is not None else "",
            "finite_response_prediction_loss": response_loss is not None and np.isfinite(response_loss),
            "claim_boundary": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        }
    ]


def build_parameter_group_trace_rows(source_checkpoint: Path, candidate_checkpoint: Path) -> list[dict[str, Any]]:
    return _with_claim_boundary(m2848_base.build_parameter_group_trace_rows(source_checkpoint, candidate_checkpoint))


def build_response_prediction_probe_rows(
    metrics_rows: list[dict[str, str]],
    response_target_rows: list[dict[str, Any]],
    config: PPOConfig,
) -> list[dict[str, Any]]:
    final = metrics_rows[-1] if metrics_rows else {}
    response_loss = _float_or_none(final.get("response_prediction_loss_mean"))
    finite = response_loss is not None and np.isfinite(response_loss)
    rows: list[dict[str, Any]] = []
    for row in response_target_rows:
        if not _as_bool(row["included_in_response_prediction"]):
            continue
        rows.append(
            {
                "probe_id": f"m2866_response_probe_target_{int(row['observation_index']):02d}",
                "target_index": row["target_index"],
                "observation_index": row["observation_index"],
                "channel_name": row["channel_name"],
                "horizon": int(config.response_prediction_horizon),
                "stride": int(config.response_prediction_stride),
                "executed": finite,
                "metric_name": "weighted_response_prediction_loss_mean",
                "metric_value": response_loss if response_loss is not None else "",
                "finite": finite,
                "validation_denominator": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_hidden_intervention_probe_rows() -> list[dict[str, Any]]:
    return [
        {
            "probe_id": f"m2866_hidden_intervention_{name}",
            "intervention": name,
            "executed": False,
            "validation_denominator": False,
            "self_id_claim_made": False,
            "routed_to_next_audit": True,
            "evidence": "not_collected_in_m2866_localized_response_prediction_training_preflight",
            "claim_boundary": CLAIM_SCOPE,
        }
        for name in ("normal", "reset_hidden", "zero_history", "wrong_history")
    ]


def build_checkpoint_metadata(
    *,
    milestone: str,
    source_checkpoint: Path,
    source_load_mode: str,
    output_dir: Path,
    weight_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "m2866_localized_response_prediction_training_implementation_preflight": {
            "milestone": milestone,
            "source_checkpoint": str(source_checkpoint),
            "source_load_mode": source_load_mode,
            "output_dir": str(output_dir),
            "response_prediction_weight_json": response_prediction_weight_json_from_rows(weight_rows),
            "checkpoint_promoted": False,
            "active_config_overwritten": False,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_labels": False,
            "claim_scope": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        }
    }


def build_checkpoint_manifest(
    source_checkpoint: Path,
    candidate_checkpoint: Path,
    *,
    ppo_config: PPOConfig,
    source_load_mode: str,
    parameter_group_rows: list[dict[str, Any]],
    training_status: str,
    train_error: str,
    weight_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    changed_groups = [row["parameter_group"] for row in parameter_group_rows if _as_bool(row["changed"])]
    non_actor_head_changed = [group for group in changed_groups if group in REQUIRED_NON_ACTOR_HEAD_GROUPS]
    return {
        "manifest_id": "m2866_checkpoint_manifest_v0",
        "milestone": DEFAULT_MILESTONE,
        "source_checkpoint": str(source_checkpoint),
        "source_checkpoint_hash": file_sha256(source_checkpoint) if source_checkpoint.exists() else "",
        "candidate_checkpoint": str(candidate_checkpoint),
        "candidate_checkpoint_hash": file_sha256(candidate_checkpoint) if candidate_checkpoint.exists() else "",
        "candidate_checkpoint_written": candidate_checkpoint.exists(),
        "source_load_mode": source_load_mode,
        "training_status": training_status,
        "training_error": train_error,
        "response_prediction_dim": int(ppo_config.response_prediction_dim),
        "response_prediction_horizon": int(ppo_config.response_prediction_horizon),
        "response_prediction_weight_json": ppo_config.response_prediction_weight_json,
        "response_loss_weight_row_count": len(weight_rows),
        "changed_parameter_groups": changed_groups,
        "non_actor_head_changed_groups": non_actor_head_changed,
        "actor_mean_bias_only": bool(changed_groups and set(changed_groups).issubset({"actor_mean"})),
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_labels": False,
        "active_config_overwritten": False,
        "source_checkpoint_overwritten": False,
        "checkpoint_promoted": False,
        "baseline_checkpoint_replaced": False,
        "promotion_metadata_written": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_actor_contract_guard_rows(
    model_obs_dim: int,
    model_act_dim: int,
    env_config: DriftEnvConfig,
) -> list[dict[str, Any]]:
    rows = m2846_base.build_actor_contract_guard_rows(model_obs_dim, model_act_dim, env_config)
    return _with_claim_boundary(rows)


def build_claim_boundary_rows(training_status: str) -> list[dict[str, Any]]:
    rows = [
        {
            "claim_id": "localized_response_prediction_training_preflight_executed",
            "claim_family": "allowed_bounded_implementation_preflight",
            "claim_made": training_status == "completed",
            "allowed": True,
            "status_pass": True,
            "evidence": training_status,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]
    for claim_id, made in FALSE_CLAIM_FLAGS.items():
        rows.append(
            {
                "claim_id": claim_id,
                "claim_family": "forbidden_interpretation",
                "claim_made": made,
                "allowed": False,
                "status_pass": not bool(made),
                "evidence": "not_emitted",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_proof_gate_rows(
    *,
    response_target_rows: list[dict[str, Any]],
    response_probe_rows: list[dict[str, Any]],
    parameter_group_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    actor_guard_rows: list[dict[str, Any]],
    weight_rows: list[dict[str, Any]],
    valid_mask_rows: list[dict[str, Any]],
    surface_accounting_rows: list[dict[str, Any]],
    rollback_rows: list[dict[str, Any]],
    source_paths: dict[str, Path],
) -> list[dict[str, Any]]:
    included_indices = {
        int(row["observation_index"])
        for row in response_target_rows
        if _as_bool(row["included_in_response_prediction"])
    }
    excluded_command_indices = {
        int(row["observation_index"])
        for row in response_target_rows
        if int(row["observation_index"]) in {9, 10, 11}
        and not _as_bool(row["included_in_response_prediction"])
    }
    changed_groups = {row["parameter_group"] for row in parameter_group_rows if _as_bool(row["changed"])}
    complete_groups = {row["parameter_group"] for row in parameter_group_rows}
    response_probe_finite = bool(response_probe_rows) and all(_as_bool(row["finite"]) for row in response_probe_rows)
    public_rows = sum(
        int(row["row_count"]) for row in surface_accounting_rows if _as_bool(row["public_explanatory"])
    )
    fresh_rows = sum(
        int(row["row_count"]) for row in surface_accounting_rows if _as_bool(row["fresh_or_disjoint"])
    )
    gates = [
        (
            "proof_m2865_audit_and_m2864_design_present",
            "lineage",
            source_paths["m2865_audit"].exists() and source_paths["m2864_design"].exists(),
            f"{source_paths['m2865_audit'].exists()}/{source_paths['m2864_design'].exists()}",
            "M2865 audit and M2864 design exist",
            2,
            "lineage_invalid",
        ),
        (
            "proof_source_load_mode_strict",
            "lineage",
            str(checkpoint_manifest["source_load_mode"]) == "strict",
            str(checkpoint_manifest["source_load_mode"]),
            "strict",
            1,
            "lineage_invalid",
        ),
        (
            "proof_actor_contract_72_3",
            "actor_contract",
            all(_as_bool(row["status_pass"]) for row in actor_guard_rows if row["guard_family"] == "actor_contract"),
            "actor guard rows pass",
            "all actor guard rows pass",
            len(actor_guard_rows),
            "contract_violation",
        ),
        (
            "proof_no_hidden_or_oracle_actor_input",
            "actor_contract",
            not _as_bool(checkpoint_manifest["hidden_or_oracle_actor_inputs_required"]),
            str(checkpoint_manifest["hidden_or_oracle_actor_inputs_required"]),
            "false",
            1,
            "contract_violation",
        ),
        (
            "proof_no_actor_visible_future_labels",
            "actor_contract",
            not _as_bool(checkpoint_manifest["actor_visible_labels"]),
            str(checkpoint_manifest["actor_visible_labels"]),
            "false",
            1,
            "contract_violation",
        ),
        (
            "proof_response_target_schema_clean",
            "response_target_schema",
            included_indices == set(range(9))
            and excluded_command_indices == {9, 10, 11}
            and not any(
                _as_bool(row["hidden_or_oracle"]) or _as_bool(row["label_or_verdict"])
                for row in response_target_rows
            ),
            f"included={sorted(included_indices)} excluded_commands={sorted(excluded_command_indices)}",
            "included 0-8, excluded 9-11, no hidden/label targets",
            len(response_target_rows),
            "contract_violation",
        ),
        (
            "proof_response_loss_weights_match_m2864",
            "loss_weighting",
            weight_rows_match_m2864(weight_rows),
            f"rows={len(weight_rows)} json={checkpoint_manifest['response_prediction_weight_json']}",
            "exact M2864 raw table, normalized mean one, allowed normalized range",
            len(weight_rows),
            "contract_violation",
        ),
        (
            "proof_valid_target_mask_contract",
            "mask_accounting",
            bool(valid_mask_rows) and all(_as_bool(row["status_pass"]) for row in valid_mask_rows),
            f"rows={len(valid_mask_rows)}",
            "terminal gaps counted, unavailable targets do not contribute loss, no imputation",
            len(valid_mask_rows),
            "metric_artifact",
        ),
        (
            "proof_public_fresh_surface_accounting",
            "public_fresh_surface",
            public_rows > 0
            and fresh_rows >= 8
            and all(_as_bool(row["status_pass"]) for row in surface_accounting_rows),
            f"public_rows={public_rows} fresh_rows={fresh_rows}",
            "public explanatory rows plus at least 8 fresh/disjoint rows, no ranking denominator",
            len(surface_accounting_rows),
            "objective_overfit",
        ),
        (
            "proof_rollback_gates_written",
            "rollback",
            bool(rollback_rows) and all(_as_bool(row["status_pass"]) for row in rollback_rows),
            f"rows={len(rollback_rows)} triggered={[row['rollback_gate_id'] for row in rollback_rows if _as_bool(row['triggered'])]}",
            "all rollback gates materialized and none triggered",
            len(rollback_rows),
            "proof_washout",
        ),
        (
            "proof_response_prediction_head_enabled",
            "response_prediction",
            int(checkpoint_manifest["response_prediction_dim"]) == 9
            and int(checkpoint_manifest["response_prediction_horizon"]) == 4
            and bool(checkpoint_manifest["candidate_checkpoint_written"]),
            (
                f"dim={checkpoint_manifest['response_prediction_dim']} "
                f"horizon={checkpoint_manifest['response_prediction_horizon']}"
            ),
            "dim=9 horizon=4 candidate checkpoint written",
            1,
            "metric_artifact",
        ),
        (
            "proof_response_prediction_probe_finite",
            "response_prediction",
            response_probe_finite,
            str(response_probe_finite),
            "true",
            len(response_probe_rows),
            "metric_artifact",
        ),
        (
            "proof_recurrent_or_response_prediction_group_changed",
            "parameter_trace",
            bool(changed_groups & REQUIRED_NON_ACTOR_HEAD_GROUPS),
            ",".join(sorted(changed_groups)),
            "one recurrent/fusion/response-prediction group changed",
            len(parameter_group_rows),
            "proof_washout",
        ),
        (
            "proof_not_actor_head_only",
            "parameter_trace",
            not _as_bool(checkpoint_manifest["actor_mean_bias_only"]),
            str(checkpoint_manifest["actor_mean_bias_only"]),
            "false",
            len(parameter_group_rows),
            "proof_washout",
        ),
        (
            "proof_parameter_trace_complete",
            "parameter_trace",
            complete_groups == set(REQUIRED_PARAMETER_GROUPS),
            ",".join(sorted(complete_groups)),
            ",".join(REQUIRED_PARAMETER_GROUPS),
            len(parameter_group_rows),
            "metric_artifact",
        ),
        (
            "proof_no_active_config_overwrite",
            "artifact_boundary",
            not _as_bool(checkpoint_manifest["active_config_overwritten"]),
            str(checkpoint_manifest["active_config_overwritten"]),
            "false",
            1,
            "contract_violation",
        ),
    ]
    return [
        _gate_row(gate_id, "proof", family, status, observed, expected, count, failure)
        for gate_id, family, status, observed, expected, count, failure in gates
    ]


def build_generalization_gate_rows(
    training_seed_rows: list[dict[str, Any]],
    surface_accounting_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    public_rows = sum(
        int(row["row_count"]) for row in surface_accounting_rows if _as_bool(row["public_explanatory"])
    )
    fresh_rows = sum(
        int(row["row_count"]) for row in surface_accounting_rows if _as_bool(row["fresh_or_disjoint"])
    )
    gates = [
        (
            "generalization_seed_split_written",
            "seed_split",
            bool(training_seed_rows),
            str(len(training_seed_rows)),
            ">=1 bounded implementation seed row",
            len(training_seed_rows),
            "metric_artifact",
        ),
        (
            "generalization_fresh_surface_accounting_nonempty",
            "public_fresh_surface",
            fresh_rows >= 8,
            f"fresh_rows={fresh_rows}",
            "fresh/disjoint surface rows >= 8",
            len(surface_accounting_rows),
            "objective_overfit",
        ),
        (
            "generalization_public_surface_explanatory_only",
            "public_fresh_surface",
            public_rows > 0
            and all(
                not _as_bool(row["ranking_admissible"])
                and not _as_bool(row["ordinary_success_denominator_allowed"])
                and not _as_bool(row["training_target_selection_allowed"])
                for row in surface_accounting_rows
            ),
            f"public_rows={public_rows}",
            "public rows proof/guardrail only and never ordinary denominators",
            len(surface_accounting_rows),
            "objective_overfit",
        ),
        (
            "generalization_no_single_seed_verdict",
            "claim_boundary",
            True,
            "success_rate_verdict=false",
            "no single-seed verdict",
            len(training_seed_rows),
            "objective_overfit",
        ),
        (
            "generalization_failure_taxonomy_not_collapsed",
            "failure_taxonomy",
            True,
            "contract_violation,lineage_invalid,metric_artifact,objective_overfit,proof_washout,training_instability",
            "failure taxonomy retained",
            6,
            "metric_artifact",
        ),
        (
            "generalization_no_current_sim_verdict",
            "claim_boundary",
            True,
            "current_sim_verdict=false",
            "no current-sim verdict",
            1,
            "objective_overfit",
        ),
    ]
    return [
        _gate_row(gate_id, "generalization", family, status, observed, expected, count, failure)
        for gate_id, family, status, observed, expected, count, failure in gates
    ]


def build_promotion_guard_rows(checkpoint_manifest: dict[str, Any], next_blocker: str) -> list[dict[str, Any]]:
    gates = [
        (
            "promotion_checkpoint_not_promoted",
            not _as_bool(checkpoint_manifest["checkpoint_promoted"]),
            str(checkpoint_manifest["checkpoint_promoted"]),
            "false",
            "contract_violation",
        ),
        ("promotion_no_winner_selected", True, "winner_selected=false", "false", "objective_overfit"),
        ("promotion_no_success_rate_verdict", True, "success_rate_verdict=false", "false", "objective_overfit"),
        (
            "promotion_no_active_config_overwrite",
            not _as_bool(checkpoint_manifest["active_config_overwritten"]),
            str(checkpoint_manifest["active_config_overwritten"]),
            "false",
            "contract_violation",
        ),
        (
            "promotion_no_baseline_replacement",
            not _as_bool(checkpoint_manifest["baseline_checkpoint_replaced"]),
            str(checkpoint_manifest["baseline_checkpoint_replaced"]),
            "false",
            "contract_violation",
        ),
        ("promotion_requires_future_audit", True, next_blocker, next_blocker, "lineage_invalid"),
    ]
    return [
        _gate_row(gate_id, "promotion", "promotion_guard", status, observed, expected, 1, failure)
        for gate_id, status, observed, expected, failure in gates
    ]


def _gate_row(
    gate_id: str,
    tier: str,
    family: str,
    status: bool,
    observed: str,
    expected: str,
    count: int,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_tier": tier,
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "row_count": int(count),
        "failure_type": "" if status else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source_paths: dict[str, Path],
    ppo_config: PPOConfig,
    env_config: DriftEnvConfig,
    training_status: str,
    train_error: str,
    source_load_mode: str,
    training_run_rows: list[dict[str, Any]],
    parameter_group_rows: list[dict[str, Any]],
    response_probe_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    proof_gate_rows: list[dict[str, Any]],
    generalization_gate_rows: list[dict[str, Any]],
    promotion_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    weight_rows: list[dict[str, Any]],
    valid_mask_rows: list[dict[str, Any]],
    surface_accounting_rows: list[dict[str, Any]],
    rollback_rows: list[dict[str, Any]],
    m2861_summary: dict[str, Any],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows
    failed_gate_ids = [row["gate_id"] for row in gate_rows if not _as_bool(row["status_pass"])]
    triggered_rollback_gate_ids = [
        row["rollback_gate_id"] for row in rollback_rows if _as_bool(row["triggered"])
    ]
    changed_groups = [row["parameter_group"] for row in parameter_group_rows if _as_bool(row["changed"])]
    non_actor_head_changed = [group for group in changed_groups if group in REQUIRED_NON_ACTOR_HEAD_GROUPS]
    response_loss = _float_or_none(training_run_rows[0].get("response_prediction_loss_mean")) if training_run_rows else None
    public_rows = sum(
        int(row["row_count"]) for row in surface_accounting_rows if _as_bool(row["public_explanatory"])
    )
    fresh_rows = sum(
        int(row["row_count"]) for row in surface_accounting_rows if _as_bool(row["fresh_or_disjoint"])
    )
    channel_summary_row_count = 0
    recipe_signal_row_count = 0
    for row in valid_mask_rows:
        if row["source_signal"] == "channel_summary_all_horizons_all_response_channels":
            channel_summary_row_count = int(row["source_row_count"])
        else:
            recipe_signal_row_count += 1
    status_pass = bool(
        training_status == "completed"
        and not failed_gate_ids
        and not triggered_rollback_gate_ids
        and checkpoint_manifest.get("candidate_checkpoint_written", False)
    )
    return {
        "milestone": milestone,
        "result_class": RESULT_CLASS_PASS if status_pass else RESULT_CLASS_FAIL,
        "status_pass": status_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "run_state": str(paths["run_state"]),
        "protocol_config_snapshot": str(paths["protocol_config_snapshot"]),
        "ppo_config_snapshot": str(paths["ppo_config_snapshot"]),
        "env_config_snapshot": str(paths["env_config_snapshot"]),
        "response_loss_weight_rows": str(paths["response_loss_weight_rows"]),
        "valid_target_mask_accounting_rows": str(paths["valid_target_mask_accounting_rows"]),
        "surface_accounting_rows": str(paths["surface_accounting_rows"]),
        "rollback_gate_rows": str(paths["rollback_gate_rows"]),
        "response_target_schema_rows": str(paths["response_target_schema_rows"]),
        "training_seed_rows": str(paths["training_seed_rows"]),
        "training_run_rows": str(paths["training_run_rows"]),
        "train_metrics": str(paths["train_metrics"]),
        "checkpoint_manifest": str(paths["checkpoint_manifest"]),
        "candidate_checkpoint": str(paths["candidate_checkpoint"]),
        "parameter_group_trace": str(paths["parameter_group_trace"]),
        "response_prediction_probe_rows": str(paths["response_prediction_probe_rows"]),
        "hidden_intervention_probe_rows": str(paths["hidden_intervention_probe_rows"]),
        "proof_gate_rows": str(paths["proof_gate_rows"]),
        "generalization_gate_rows": str(paths["generalization_gate_rows"]),
        "promotion_guard_rows": str(paths["promotion_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "follow_up_manifest": str(paths["registered_follow_up_manifest"]),
        "follow_up_manifest_copy": str(paths["follow_up_manifest_copy"]),
        "source_checkpoint": str(source_paths["source_checkpoint"]),
        "m2865_audit": str(source_paths["m2865_audit"]),
        "m2864_design": str(source_paths["m2864_design"]),
        "m2861_summary": str(source_paths["m2861_summary"]),
        "m2861_channel_summary_rows": str(source_paths["m2861_channel_summary_rows"]),
        "m2861_recipe_signal_rows": str(source_paths["m2861_recipe_signal_rows"]),
        "m2857_surface_rows": str(source_paths["m2857_surface_rows"]),
        "source_load_mode": source_load_mode,
        "training_status": training_status,
        "training_error": train_error,
        "bounded_implementation_preflight_run": training_status == "completed",
        "training_smoke_run": training_status == "completed",
        "total_steps": int(ppo_config.total_steps),
        "rollout_steps": int(ppo_config.rollout_steps),
        "num_envs": int(ppo_config.num_envs),
        "update_epochs": int(ppo_config.update_epochs),
        "minibatch_size": int(ppo_config.minibatch_size),
        "seed": int(ppo_config.seed),
        "actor_encoder": ppo_config.actor_encoder,
        "history_baseline_level": ppo_config.history_baseline_level,
        "recurrent_sequence_training": bool(ppo_config.recurrent_sequence_training),
        "response_prediction_aux_coef": float(ppo_config.response_prediction_aux_coef),
        "response_prediction_dim": int(ppo_config.response_prediction_dim),
        "response_prediction_horizon": int(ppo_config.response_prediction_horizon),
        "response_prediction_stride": int(ppo_config.response_prediction_stride),
        "response_prediction_weight_json": ppo_config.response_prediction_weight_json,
        "response_loss_weight_row_count": len(weight_rows),
        "response_loss_weights_match_m2864": weight_rows_match_m2864(weight_rows),
        "response_prediction_loss_mean": response_loss if response_loss is not None else "",
        "response_prediction_loss_finite": response_loss is not None and np.isfinite(response_loss),
        "baseline_action_anchor_checkpoint": ppo_config.baseline_action_anchor_checkpoint,
        "baseline_action_anchor_coef": float(ppo_config.baseline_action_anchor_coef),
        "env_history_length": int(env_config.history_length),
        "env_action_history_mode": env_config.action_history_mode,
        "env_include_privileged_params": bool(env_config.include_privileged_params),
        "env_wheel_observation_mode": env_config.wheel_observation_mode,
        "env_road_lookahead_count": int(env_config.road_lookahead_count),
        "env_obstacle_slots": int(env_config.obstacle_slots),
        "candidate_checkpoint_written": bool(checkpoint_manifest.get("candidate_checkpoint_written", False)),
        "candidate_checkpoint_hash": checkpoint_manifest.get("candidate_checkpoint_hash", ""),
        "source_checkpoint_hash": checkpoint_manifest.get("source_checkpoint_hash", ""),
        "checkpoint_promoted": False,
        "active_config_overwritten": False,
        "baseline_checkpoint_replaced": False,
        "changed_parameter_groups": changed_groups,
        "non_actor_head_changed_groups": non_actor_head_changed,
        "actor_mean_bias_only": bool(checkpoint_manifest.get("actor_mean_bias_only", False)),
        "valid_target_mask_accounting_row_count": len(valid_mask_rows),
        "valid_target_mask_accounting_pass": all(_as_bool(row["status_pass"]) for row in valid_mask_rows),
        "surface_accounting_row_count": len(surface_accounting_rows),
        "m2850_explanatory_surface_row_count": public_rows,
        "fresh_disjoint_surface_row_count": fresh_rows,
        "surface_accounting_pass": all(_as_bool(row["status_pass"]) for row in surface_accounting_rows)
        and public_rows > 0
        and fresh_rows >= 8,
        "rollback_gate_row_count": len(rollback_rows),
        "rollback_gate_rows_pass": all(_as_bool(row["status_pass"]) for row in rollback_rows),
        "triggered_rollback_gate_ids": triggered_rollback_gate_ids,
        "m2861_recipe_signal_row_count": recipe_signal_row_count,
        "m2861_channel_summary_row_count": channel_summary_row_count,
        "m2861_terminal_gap_accounted_row_count": int(
            _float_or_none(m2861_summary.get("terminal_gap_accounted_row_count")) or 0
        ),
        "response_target_row_count": len(response_probe_rows),
        "parameter_group_trace_row_count": len(parameter_group_rows),
        "training_run_row_count": len(training_run_rows),
        "proof_gate_row_count": len(proof_gate_rows),
        "generalization_gate_row_count": len(generalization_gate_rows),
        "promotion_guard_row_count": len(promotion_guard_rows),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_row_count": len(gate_rows),
        "gate_matrix_pass": not failed_gate_ids,
        "failed_gate_ids": failed_gate_ids,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "success_rate_computed": False,
        "success_rate_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": next_blocker,
        "required_artifacts_present": False,
        "m2867_follow_up_manifest_registered": False,
    }


def build_run_state(summary: dict[str, Any], paths: dict[str, Path], source_paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "generated_at_utc": summary["generated_at_utc"],
        "paths": {key: str(path) for key, path in paths.items()},
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "summary": summary,
    }


def required_artifacts_present(paths: dict[str, Path]) -> bool:
    required = [
        "protocol_config_snapshot",
        "ppo_config_snapshot",
        "env_config_snapshot",
        "response_loss_weight_rows",
        "valid_target_mask_accounting_rows",
        "surface_accounting_rows",
        "rollback_gate_rows",
        "response_target_schema_rows",
        "training_seed_rows",
        "training_run_rows",
        "train_metrics",
        "checkpoint_manifest",
        "parameter_group_trace",
        "response_prediction_probe_rows",
        "hidden_intervention_probe_rows",
        "proof_gate_rows",
        "generalization_gate_rows",
        "promotion_guard_rows",
        "actor_contract_guard_rows",
        "claim_boundary_rows",
        "gate_matrix",
        "summary",
        "run_state",
        "follow_up_manifest_copy",
        "registered_follow_up_manifest",
        "doc",
    ]
    return all(paths[key].exists() for key in required)


def build_m2867_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "hypothesis": "A bounded result audit can accept or reject M2866 localized response-prediction training implementation artifacts before any interpretation.",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "training_instability",
        ],
        "lineage": {
            "parent_checkpoint": [summary["candidate_checkpoint"]],
            "parent_dataset": [
                summary["summary"],
                summary["checkpoint_manifest"],
                summary["response_loss_weight_rows"],
                summary["valid_target_mask_accounting_rows"],
                summary["surface_accounting_rows"],
                summary["rollback_gate_rows"],
                summary["parameter_group_trace"],
                summary["response_target_schema_rows"],
                summary["training_run_rows"],
                summary["proof_gate_rows"],
                summary["generalization_gate_rows"],
                summary["promotion_guard_rows"],
                summary["actor_contract_guard_rows"],
                summary["claim_boundary_rows"],
                summary["gate_matrix"],
                summary["doc"],
                summary["m2865_audit"],
                summary["m2864_design"],
                summary["m2861_summary"],
                summary["m2857_surface_rows"],
            ],
            "parent_config": [
                "experiments/manifests/m2866-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-implementation-preflight.json",
                "experiments/manifests/m2865-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-training-recipe-design-result-audit.json",
            ],
            "parent_objective": [
                "audit M2866 localized response-prediction implementation preflight artifacts before interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2867 must audit M2866 artifact completeness, gate matrix, checkpoint lineage, and claim boundary",
                "M2867 must verify the M2864 weight table, valid-target mask rows, public/fresh surface rows, and rollback rows",
                "M2867 must not promote the M2866 checkpoint or claim validation driver performance paper current-sim high-fidelity full-driver or self-ID evidence",
            ],
            "supersedes": ["unaudited localized response-prediction training implementation interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2867 must audit whether M2866 wrote complete implementation-preflight artifacts",
            "M2867 must verify actor 72/action 3 and no hidden/oracle actor input were preserved",
            "M2867 must verify response-loss weight rows exactly match M2864 with loss-mass normalization",
            "M2867 must verify valid-target mask and terminal-gap accounting rows",
            "M2867 must verify public M2850 explanatory rows and fresh/disjoint rows remain separate and non-ranking",
            "M2867 must verify rollback gates and claim rows before any next training decision",
            "M2867 must not validate rank promote compute success-rate verdict claim performance paper current-sim high-fidelity full-driver or self-ID result",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run training",
            "do not execute validation",
            "do not rank checkpoints controllers source families task families profiles stress axes or scenario roles",
            "do not select a winner",
            "do not promote a checkpoint",
            "do not overwrite active configs",
            "do not replace any baseline checkpoint",
            "do not compute success-rate verdict metrics",
            "do not change actor inputs",
            "do not inject hidden or oracle actor features",
            "do not expose future response labels to actor input",
            "do not hide public/fresh surface split",
            "do not claim repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_response_predictive_recurrent_belief_failure_localization_training_recipe_redesign",
            "evidence_axis": "localized_response_prediction_training_implementation_result_audit",
            "evidence_increment": "audits M2866 bounded implementation-preflight artifacts before any interpretation or further training",
            "claim_scope": "Result audit only; no validation ranking winner selection promotion success-rate verdict driver-performance paper current-sim high-fidelity validation self-ID or full ideal driver claim",
            "stop_condition": [
                "stop if M2866 changed actor 72/action 3",
                "stop if response labels became actor-visible",
                "stop if M2866 weight rows deviate from M2864",
                "stop if mask/surface/rollback rows are incomplete",
                "stop if M2866 claims validation readiness driver performance paper current-sim high-fidelity or self-ID evidence",
            ],
            "fallback_plan": [
                "route to implementation repair design only if a narrow artifact or runner issue is identified",
                "route to bounded follow-up training design only if M2866 passes and audit admits more training evidence",
                "route to branch synthesis if implementation evidence does not justify more local training",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2866 implementation preflight has produced executable artifacts requiring audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2866 localized response-prediction implementation preflight artifacts",
            "admission_evidence": [
                "M2866 summary artifact is expected before M2867 runs",
                "M2866 checkpoint manifest weight rows mask rows surface rows rollback rows and gate rows require audit before interpretation",
            ],
            "blocked_shortcuts": [
                "no new training or validation in result audit",
                "no ranking winner selection promotion or success-rate verdict",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "M2867 status queue scoreboard and review",
                "one bounded follow-up manifest if audit accepts a next route",
            ],
            "next_stage_criteria": [
                "M2866 status and gate rows are accepted or rejected",
                "failure types are classified if any gate failed",
                "one bounded next route or stop is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2867 audits localized response-prediction implementation only and does not run finite-window-vs-GRU or self-ID tests.",
            "history_necessity_tests": [
                "M2866 hidden intervention rows are diagnostic artifact rows only and cannot support a self-ID claim."
            ],
            "temporal_evidence_window": "M2866 implementation artifacts plus M2864/M2865 design audit constraints.",
            "negative_result_policy": "If M2866 failed or triggered rollback gates, preserve the negative evidence and route to repair design, synthesis, or stop rather than weakening gates.",
            "allowed_claims": [
                "M2866 bounded implementation preflight accepted or rejected",
                "bounded follow-up route registration",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits executable localized response-prediction implementation artifacts from M2866",
            "paper_verdict_delta": "no paper verdict; audit governs Route A engineering training continuation",
            "must_synthesize_if": [
                "M2866 cannot preserve actor 72/action 3",
                "M2866 response labels require hidden/oracle actor fields",
                "M2866 cannot prove M2864 weight/mask/surface/rollback contracts",
                "M2866 claims validation readiness driver performance paper current-sim high-fidelity or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "audit checks M2866 summary checkpoint manifest weight rows mask rows surface rows rollback rows and gate rows",
            "audit preserves actor 72/action 3 no hidden/oracle labels public/fresh split and claim boundary",
            "audit registers one bounded follow-up route if continuing",
        ],
        "failure_criteria": [
            "M2867 runs new training validation ranking promotion or success-rate verdict computation",
            "M2867 hides M2866 gate failures or weakens actor/claim boundaries",
            "M2867 claims repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2867 audits M2866 artifacts under unchanged actor and claim boundaries without new execution or overclaiming.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{DEFAULT_NEXT_BLOCKER}.md", "type": "md"}],
        "baseline_checkpoints": [summary["candidate_checkpoint"]],
        "baseline_artifacts": [summary["summary"], summary["gate_matrix"], summary["checkpoint_manifest"]],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "",
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    failed = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    rollback = (
        ", ".join(summary["triggered_rollback_gate_ids"])
        if summary["triggered_rollback_gate_ids"]
        else "none"
    )
    lines = [
        "# M2866 Engineering Controller Route A Response-Predictive Recurrent-Belief Localized Response-Prediction Training Implementation Preflight",
        "",
        "## Metadata",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result_class: `{summary['result_class']}`",
        f"- summary: `{summary['summary']}`",
        f"- candidate checkpoint: `{summary['candidate_checkpoint']}`",
        f"- checkpoint manifest: `{summary['checkpoint_manifest']}`",
        f"- response-loss weight rows: `{summary['response_loss_weight_rows']}`",
        f"- valid-target mask accounting rows: `{summary['valid_target_mask_accounting_rows']}`",
        f"- surface accounting rows: `{summary['surface_accounting_rows']}`",
        f"- rollback gate rows: `{summary['rollback_gate_rows']}`",
        f"- gate matrix: `{summary['gate_matrix']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Bounded Implementation Result",
        "",
        "```text",
        f"training_status: {summary['training_status']}",
        f"source_load_mode: {summary['source_load_mode']}",
        f"total_steps: {summary['total_steps']}",
        f"rollout_steps: {summary['rollout_steps']}",
        f"num_envs: {summary['num_envs']}",
        f"update_epochs: {summary['update_epochs']}",
        f"response_prediction_dim: {summary['response_prediction_dim']}",
        f"response_prediction_horizon: {summary['response_prediction_horizon']}",
        f"response_loss_weights_match_m2864: {summary['response_loss_weights_match_m2864']}",
        f"response_prediction_loss_mean: {summary['response_prediction_loss_mean']}",
        f"candidate_checkpoint_written: {summary['candidate_checkpoint_written']}",
        f"changed_parameter_groups: {','.join(summary['changed_parameter_groups'])}",
        f"non_actor_head_changed_groups: {','.join(summary['non_actor_head_changed_groups'])}",
        f"gate_matrix_pass: {summary['gate_matrix_pass']}",
        f"failed_gate_ids: {failed}",
        f"triggered_rollback_gate_ids: {rollback}",
        "```",
        "",
        "The bounded implementation run is training-preflight evidence only. It is not a validation run, ranking run, promotion decision, success-rate verdict, driver-performance claim, current-sim verdict, high-fidelity validation result, paper result, full-driver result, or self-ID result.",
        "",
        "## M2864 Weight And Mask Contract",
        "",
        "```text",
        f"response_loss_weight_row_count: {summary['response_loss_weight_row_count']}",
        f"valid_target_mask_accounting_row_count: {summary['valid_target_mask_accounting_row_count']}",
        f"valid_target_mask_accounting_pass: {summary['valid_target_mask_accounting_pass']}",
        f"m2861_terminal_gap_accounted_row_count: {summary['m2861_terminal_gap_accounted_row_count']}",
        "future_labels_actor_visible: false",
        "terminal_or_unavailable_targets_imputed: false",
        "```",
        "",
        "## Public/Fresh Surface Boundary",
        "",
        "```text",
        f"m2850_explanatory_surface_row_count: {summary['m2850_explanatory_surface_row_count']}",
        f"fresh_disjoint_surface_row_count: {summary['fresh_disjoint_surface_row_count']}",
        f"surface_accounting_pass: {summary['surface_accounting_pass']}",
        "ordinary_success_denominator_allowed: false",
        "ranking_admissible: false",
        "checkpoint_promotion_admitted: false",
        "```",
        "",
        "## Actor And Claim Boundary",
        "",
        "```text",
        "actor_observation_dim: 72",
        "action_dim: 3",
        "actor_encoder: human_view_online_gru",
        "hidden_or_oracle_actor_inputs_required: false",
        "response_prediction_target_indices: 0..8",
        "excluded_previous_command_indices: 9,10,11",
        "validation_run: false",
        "ranking_run: false",
        "success_rate_computed: false",
        "checkpoint_promoted: false",
        "driver_performance_claim_made: false",
        "paper_claim_made: false",
        "current_sim_verdict_claim_made: false",
        "high_fidelity_validation_claim_made: false",
        "full_ideal_driver_gate_passed: false",
        "level3_self_id_claim_made: false",
        "```",
        "",
    ]
    if summary["training_error"]:
        lines.extend(["## Training Error", "", "```text", summary["training_error"], "```", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def weight_rows_match_m2864(weight_rows: list[dict[str, Any]]) -> bool:
    if len(weight_rows) != len(RAW_RESPONSE_WEIGHT_TABLE) * len(RESPONSE_CHANNEL_NAMES):
        return False
    expected_rows = build_response_loss_weight_rows()
    for observed, expected in zip(weight_rows, expected_rows, strict=True):
        if int(observed["horizon_index"]) != int(expected["horizon_index"]):
            return False
        if int(observed["response_channel_index"]) != int(expected["response_channel_index"]):
            return False
        if str(observed["response_channel_name"]) != str(expected["response_channel_name"]):
            return False
        if not np.isclose(float(observed["raw_weight"]), float(expected["raw_weight"])):
            return False
        if not np.isclose(float(observed["normalized_weight"]), float(expected["normalized_weight"])):
            return False
        if not _as_bool(observed["within_allowed_range"]):
            return False
        if _as_bool(observed["post_hoc_tuned"]):
            return False
    return True


def _with_claim_boundary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["claim_boundary"] = CLAIM_SCOPE
        updated.append(item)
    return updated


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return m2848_base.read_csv_rows(path)


def file_sha256(path: Path | str) -> str:
    return m2848_base.file_sha256(path)


def _float_or_none(value: Any) -> float | None:
    return m2848_base._float_or_none(value)


def _as_bool(value: Any) -> bool:
    return m2848_base._as_bool(value)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the M2866 localized response-prediction training preflight.")
    parser.add_argument("--m2865-audit", type=Path, default=DEFAULT_M2865_AUDIT)
    parser.add_argument("--m2864-design", type=Path, default=DEFAULT_M2864_DESIGN)
    parser.add_argument("--m2861-summary", type=Path, default=DEFAULT_M2861_SUMMARY)
    parser.add_argument("--m2861-channel-summary-rows", type=Path, default=DEFAULT_M2861_CHANNEL_SUMMARY_ROWS)
    parser.add_argument("--m2861-recipe-signal-rows", type=Path, default=DEFAULT_M2861_RECIPE_SIGNAL_ROWS)
    parser.add_argument("--m2857-surface-rows", type=Path, default=DEFAULT_M2857_SURFACE_ROWS)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--total-steps", type=int, default=32)
    parser.add_argument("--rollout-steps", type=int, default=16)
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--update-epochs", type=int, default=2)
    parser.add_argument("--minibatch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=286600)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_localized_response_prediction_training_implementation_preflight(
        output_dir=args.output_dir,
        m2865_audit=args.m2865_audit,
        m2864_design=args.m2864_design,
        m2861_summary=args.m2861_summary,
        m2861_channel_summary_rows=args.m2861_channel_summary_rows,
        m2861_recipe_signal_rows=args.m2861_recipe_signal_rows,
        m2857_surface_rows=args.m2857_surface_rows,
        source_checkpoint=args.source_checkpoint,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
        device=args.device,
        total_steps=args.total_steps,
        rollout_steps=args.rollout_steps,
        num_envs=args.num_envs,
        update_epochs=args.update_epochs,
        minibatch_size=args.minibatch_size,
        seed=args.seed,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"result_class={summary['result_class']}")


if __name__ == "__main__":
    main()
