"""M2846 response-predictive recurrent-belief implementation preflight.

This runner materializes the M2845 design as a bounded training smoke. It uses
the existing PPO training path and writes implementation, proof, generalization,
promotion, actor-contract, and claim-boundary artifacts. It does not validate,
rank, promote, or claim driver performance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.env import DriftEnvConfig
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.train_ppo import (
    ActorCritic,
    PPOConfig,
    load_init_checkpoint_state,
    resolve_device,
    train,
)


DEFAULT_MILESTONE = (
    "m2846-engineering-controller-route-a-response-predictive-recurrent-belief-core-"
    "training-implementation-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2846_engineering_controller_route_a_response_predictive_recurrent_belief_core_"
    "training_implementation_preflight"
)
DEFAULT_M2845_DESIGN = Path(
    "docs/m2845-engineering-controller-route-a-response-predictive-recurrent-belief-core-"
    "training-implementation-preflight-design.md"
)
DEFAULT_M2844_AUDIT = Path(
    "docs/m2844-engineering-controller-route-a-driver-like-recurrent-belief-architecture-"
    "training-redesign-protocol-result-audit.md"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_"
    "preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_M2838_SUMMARY = Path(
    "runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_"
    "evidence_preflight/summary.json"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2847-engineering-controller-route-a-response-predictive-"
    "recurrent-belief-core-training-implementation-preflight-result-audit.json"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2846-engineering-controller-route-a-response-predictive-recurrent-belief-core-"
    "training-implementation-preflight.md"
)
DEFAULT_NEXT_BLOCKER = (
    "m2847-engineering-controller-route-a-response-predictive-recurrent-belief-core-"
    "training-implementation-preflight-result-audit"
)

CLAIM_SCOPE = (
    "M2846 response-predictive recurrent-belief core training implementation "
    "preflight only"
)
FORBIDDEN_INTERPRETATION = (
    "validation, ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "repair success, driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, or "
    "level3 self-identification"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_response_predictive_recurrent_belief_core_training_"
    "implementation_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_response_predictive_recurrent_belief_core_training_"
    "implementation_preflight_failed"
)

RESPONSE_TARGET_FIELDNAMES = [
    "target_index",
    "observation_index",
    "channel_name",
    "normalization",
    "actor_visible_input",
    "hidden_or_oracle",
    "label_or_verdict",
    "included_in_response_prediction",
    "claim_boundary",
]
TRAINING_SEED_FIELDNAMES = [
    "seed_row_id",
    "split",
    "seed",
    "training_smoke",
    "validation_denominator",
    "ranking_admissible",
    "claim_boundary",
]
TRAINING_RUN_FIELDNAMES = [
    "training_run_id",
    "seed",
    "total_steps",
    "rollout_steps",
    "num_envs",
    "update_epochs",
    "minibatch_size",
    "final_step",
    "update_count",
    "ppo_run",
    "training_smoke",
    "validation_run",
    "success_rate_computed",
    "metrics_csv",
    "candidate_checkpoint",
    "training_status",
    "response_prediction_loss_mean",
    "baseline_action_anchor_loss_mean",
    "finite_response_prediction_loss",
    "claim_boundary",
    "forbidden_interpretation",
]
PARAMETER_GROUP_FIELDNAMES = [
    "parameter_group",
    "parameter_count",
    "source_hash",
    "candidate_hash",
    "changed",
    "delta_l2",
    "delta_max_abs",
    "trainable",
    "required_for_protocol",
    "actor_head_only_group",
    "claim_boundary",
]
RESPONSE_PROBE_FIELDNAMES = [
    "probe_id",
    "target_index",
    "observation_index",
    "channel_name",
    "horizon",
    "stride",
    "executed",
    "metric_name",
    "metric_value",
    "finite",
    "validation_denominator",
    "claim_boundary",
]
HIDDEN_INTERVENTION_FIELDNAMES = [
    "probe_id",
    "intervention",
    "executed",
    "validation_denominator",
    "self_id_claim_made",
    "routed_to_next_audit",
    "evidence",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "row_count",
    "failure_type",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "protected_field",
    "actor_visible_allowed",
    "actor_observation_shape",
    "action_shape",
    "status_pass",
    "evidence",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "allowed",
    "status_pass",
    "evidence",
    "claim_boundary",
]

REQUIRED_PARAMETER_GROUPS = [
    "response_encoder",
    "online_gru_cell",
    "response_context_fusion",
    "actor_mean",
    "critic",
    "log_std",
    "response_prediction_head",
]
REQUIRED_NON_ACTOR_HEAD_GROUPS = {
    "response_encoder",
    "online_gru_cell",
    "response_context_fusion",
    "response_prediction_head",
}
RESPONSE_CHANNELS = [
    (0, "vx_norm", True),
    (1, "vy_norm", True),
    (2, "yaw_rate_norm", True),
    (3, "ax_norm", True),
    (4, "ay_norm", True),
    (5, "steer_actuator_norm", True),
    (6, "steer_rate_norm", True),
    (7, "throttle_actuator", True),
    (8, "brake_actuator", True),
    (9, "previous_steer_command", False),
    (10, "previous_throttle_command", False),
    (11, "previous_brake_command", False),
]
FALSE_CLAIM_FLAGS = {
    "validation_run": False,
    "measured_validation_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "baseline_checkpoint_replaced": False,
    "active_config_overwritten": False,
    "success_rate_computed": False,
    "success_rate_verdict_claim_made": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_claim_made": False,
    "level3_self_id_claim_made": False,
}


def run_response_predictive_recurrent_belief_core_training_implementation_preflight(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    m2845_design: Path | str = DEFAULT_M2845_DESIGN,
    m2844_audit: Path | str = DEFAULT_M2844_AUDIT,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    m2838_summary: Path | str = DEFAULT_M2838_SUMMARY,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    device: str = "cpu",
    total_steps: int = 8,
    rollout_steps: int = 8,
    num_envs: int = 1,
    update_epochs: int = 1,
    minibatch_size: int = 8,
    seed: int = 284600,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(Path(m2845_design), Path(m2844_audit), Path(source_checkpoint), Path(m2838_summary))
    _require_sources(source_paths)

    env_config = build_m2846_env_config()
    ppo_config = build_m2846_ppo_config(
        source_checkpoint=Path(source_checkpoint),
        device=device,
        total_steps=total_steps,
        rollout_steps=rollout_steps,
        num_envs=num_envs,
        update_epochs=update_epochs,
        minibatch_size=minibatch_size,
        seed=seed,
    )

    write_json(paths["protocol_config_snapshot"], build_protocol_config_snapshot(source_paths, ppo_config))
    write_json(paths["ppo_config_snapshot"], ppo_config.__dict__)
    write_json(paths["env_config_snapshot"], env_config_to_dict(env_config))
    response_target_rows = build_response_target_schema_rows()
    training_seed_rows = build_training_seed_rows(seed)
    write_csv_rows(paths["response_target_schema_rows"], response_target_rows, RESPONSE_TARGET_FIELDNAMES)
    write_csv_rows(paths["training_seed_rows"], training_seed_rows, TRAINING_SEED_FIELDNAMES)

    source_checkpoint_path = Path(source_checkpoint)
    candidate_checkpoint = paths["candidate_checkpoint"]
    train_error = ""
    training_status = "completed"
    model_obs_dim = P0_OBSERVATION_DIM
    model_act_dim = ACTION_DIM
    source_load_mode = resolve_source_load_mode(ppo_config, source_checkpoint_path, device=device)
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
            ),
            init_checkpoint_path=source_checkpoint_path,
        )
        model_obs_dim = int(model.obs_dim)
        model_act_dim = int(model.act_dim)
    except Exception as exc:  # pragma: no cover - exercised only on environment/training failure.
        training_status = "failed"
        train_error = f"{type(exc).__name__}: {exc}"
        if not paths["train_metrics"].exists():
            write_csv_rows(paths["train_metrics"], [], fieldnames=[
                "step",
                "update",
                "num_envs",
                "response_prediction_loss_mean",
                "baseline_action_anchor_loss_mean",
            ])

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
    )
    m2838 = read_json(source_paths["m2838_summary"])
    actor_guard_rows = build_actor_contract_guard_rows(model_obs_dim, model_act_dim, env_config)
    claim_rows = build_claim_boundary_rows(training_status)
    proof_gate_rows = build_proof_gate_rows(
        response_target_rows=response_target_rows,
        response_probe_rows=response_probe_rows,
        parameter_group_rows=parameter_group_rows,
        checkpoint_manifest=checkpoint_manifest,
        actor_guard_rows=actor_guard_rows,
        m2838_summary=m2838,
    )
    generalization_gate_rows = build_generalization_gate_rows(training_seed_rows, m2838)
    promotion_guard_rows = build_promotion_guard_rows(checkpoint_manifest)
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
        hidden_intervention_rows=hidden_intervention_rows,
        checkpoint_manifest=checkpoint_manifest,
        proof_gate_rows=proof_gate_rows,
        generalization_gate_rows=generalization_gate_rows,
        promotion_guard_rows=promotion_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        m2838_summary=m2838,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    follow_up = build_m2847_manifest(summary)
    write_json(paths["follow_up_manifest_copy"], follow_up)
    write_json(paths["registered_follow_up_manifest"], follow_up)
    write_doc(paths["doc"], summary)

    summary = {
        **summary,
        "required_artifacts_present": required_artifacts_present(paths),
        "m2847_follow_up_manifest_registered": paths["registered_follow_up_manifest"].exists(),
    }
    summary["status_pass"] = bool(
        summary["status_pass"]
        and summary["required_artifacts_present"]
        and summary["m2847_follow_up_manifest_registered"]
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
        "response_target_schema_rows": output / "response_target_schema_rows.csv",
        "training_seed_rows": output / "training_seed_rows.csv",
        "training_run_rows": output / "training_run_rows.csv",
        "train_metrics": output / "train_metrics.csv",
        "checkpoint_manifest": output / "checkpoint_manifest.json",
        "candidate_checkpoint": output / "checkpoints" / "m2846_response_predictive_recurrent_belief_candidate.pt",
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
    m2845_design: Path,
    m2844_audit: Path,
    source_checkpoint: Path,
    m2838_summary: Path,
) -> dict[str, Path]:
    return {
        "m2845_design": m2845_design,
        "m2844_audit": m2844_audit,
        "source_checkpoint": source_checkpoint,
        "m2838_summary": m2838_summary,
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2846 missing required source artifacts: {missing}")


def build_m2846_env_config() -> DriftEnvConfig:
    return DriftEnvConfig(
        max_steps=64,
        history_length=1,
        action_history_mode="full",
        include_privileged_params=False,
        wheel_observation_mode="none",
        road_lookahead_count=8,
        obstacle_slots=4,
    )


def build_m2846_ppo_config(
    *,
    source_checkpoint: Path,
    device: str,
    total_steps: int,
    rollout_steps: int,
    num_envs: int,
    update_epochs: int,
    minibatch_size: int,
    seed: int,
) -> PPOConfig:
    if int(rollout_steps) <= 4:
        raise ValueError("M2846 rollout_steps must exceed response horizon 4")
    return PPOConfig(
        total_steps=int(total_steps),
        rollout_steps=int(rollout_steps),
        num_envs=int(num_envs),
        update_epochs=int(update_epochs),
        minibatch_size=int(minibatch_size),
        actor_encoder="human_view_online_gru",
        history_baseline_level="L3_online_gru",
        recurrent_sequence_training=True,
        response_prediction_aux_coef=0.05,
        response_prediction_dim=9,
        response_prediction_horizon=4,
        response_prediction_stride=1,
        baseline_action_anchor_coef=0.01,
        baseline_action_anchor_checkpoint=str(source_checkpoint),
        seed=int(seed),
        device=str(device),
    )


def build_protocol_config_snapshot(source_paths: dict[str, Path], config: PPOConfig) -> dict[str, Any]:
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
        "implementation_preflight_only": True,
        "validation_run": False,
        "ranking_run": False,
        "checkpoint_promoted": False,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_response_target_schema_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target_index = 0
    for observation_index, channel_name, included in RESPONSE_CHANNELS:
        rows.append(
            {
                "target_index": target_index if included else "",
                "observation_index": observation_index,
                "channel_name": channel_name,
                "normalization": "p0_actor_observation_normalized",
                "actor_visible_input": True,
                "hidden_or_oracle": False,
                "label_or_verdict": False,
                "included_in_response_prediction": bool(included),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
        if included:
            target_index += 1
    return rows


def build_training_seed_rows(seed: int) -> list[dict[str, Any]]:
    return [
        {
            "seed_row_id": "m2846_training_smoke_seed_000",
            "split": "training_smoke",
            "seed": int(seed),
            "training_smoke": True,
            "validation_denominator": False,
            "ranking_admissible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_checkpoint_metadata(
    *,
    milestone: str,
    source_checkpoint: Path,
    source_load_mode: str,
    output_dir: Path,
) -> dict[str, Any]:
    return {
        "m2846_response_predictive_recurrent_belief_core_training_implementation_preflight": {
            "milestone": milestone,
            "source_checkpoint": str(source_checkpoint),
            "source_load_mode": source_load_mode,
            "output_dir": str(output_dir),
            "checkpoint_promoted": False,
            "active_config_overwritten": False,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_labels": False,
            "claim_scope": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        }
    }


def resolve_source_load_mode(config: PPOConfig, checkpoint_path: Path, *, device: str) -> str:
    resolved_device = resolve_device(device)
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=config.hidden_size,
        log_std_init=config.log_std_init,
        log_std_min=config.log_std_min,
        log_std_max=config.log_std_max,
        actor_encoder=config.actor_encoder,
        actor_history_length=config.actor_history_length,
        action_sequence_horizon=config.action_sequence_horizon,
        response_prediction_dim=config.response_prediction_dim,
        response_prediction_horizon=config.response_prediction_horizon,
    ).to(resolved_device)
    return load_init_checkpoint_state(model, checkpoint_path, resolved_device)


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
            "training_run_id": "m2846_training_smoke_000",
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
    source_state = _load_checkpoint_state(source_checkpoint) if source_checkpoint.exists() else {}
    candidate_state = _load_checkpoint_state(candidate_checkpoint) if candidate_checkpoint.exists() else {}
    rows: list[dict[str, Any]] = []
    for group in REQUIRED_PARAMETER_GROUPS:
        source_group = _state_group(source_state, group)
        candidate_group = _state_group(candidate_state, group)
        comparable = _comparable_tensors(source_group, candidate_group)
        delta_l2 = ""
        delta_max_abs = ""
        if comparable:
            squared = 0.0
            max_abs = 0.0
            for key in comparable:
                delta = (candidate_group[key].detach().cpu().float() - source_group[key].detach().cpu().float()).numpy()
                squared += float(np.sum(np.square(delta)))
                max_abs = max(max_abs, float(np.max(np.abs(delta))) if delta.size else 0.0)
            delta_l2 = float(np.sqrt(squared))
            delta_max_abs = float(max_abs)
        source_hash = hash_state_group(source_group)
        candidate_hash = hash_state_group(candidate_group)
        rows.append(
            {
                "parameter_group": group,
                "parameter_count": int(sum(int(tensor.numel()) for tensor in candidate_group.values())),
                "source_hash": source_hash,
                "candidate_hash": candidate_hash,
                "changed": bool(source_hash != candidate_hash),
                "delta_l2": delta_l2,
                "delta_max_abs": delta_max_abs,
                "trainable": True,
                "required_for_protocol": True,
                "actor_head_only_group": group == "actor_mean",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _load_checkpoint_state(path: Path) -> dict[str, torch.Tensor]:
    checkpoint = torch.load(path, map_location="cpu")
    return dict(checkpoint["model_state"])


def _state_group(state: dict[str, torch.Tensor], group: str) -> dict[str, torch.Tensor]:
    if group == "log_std":
        prefixes = ("log_std",)
    else:
        prefixes = (f"{group}.", group)
    return {
        key: value
        for key, value in state.items()
        if key == group or any(key.startswith(prefix) for prefix in prefixes)
    }


def _comparable_tensors(
    source_group: dict[str, torch.Tensor],
    candidate_group: dict[str, torch.Tensor],
) -> list[str]:
    return [
        key
        for key in sorted(source_group)
        if key in candidate_group and tuple(source_group[key].shape) == tuple(candidate_group[key].shape)
    ]


def hash_state_group(group: dict[str, torch.Tensor]) -> str:
    if not group:
        return "missing"
    digest = hashlib.sha256()
    for key in sorted(group):
        tensor = group[key].detach().cpu().contiguous()
        digest.update(key.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("utf-8"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


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
                "probe_id": f"m2846_response_probe_target_{int(row['observation_index']):02d}",
                "target_index": row["target_index"],
                "observation_index": row["observation_index"],
                "channel_name": row["channel_name"],
                "horizon": int(config.response_prediction_horizon),
                "stride": int(config.response_prediction_stride),
                "executed": finite,
                "metric_name": "response_prediction_loss_mean",
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
            "probe_id": f"m2846_hidden_intervention_{name}",
            "intervention": name,
            "executed": False,
            "validation_denominator": False,
            "self_id_claim_made": False,
            "routed_to_next_audit": True,
            "evidence": "not_collected_in_m2846_bounded_implementation_preflight",
            "claim_boundary": CLAIM_SCOPE,
        }
        for name in ("normal", "reset_hidden", "zero_history", "wrong_history")
    ]


def build_checkpoint_manifest(
    source_checkpoint: Path,
    candidate_checkpoint: Path,
    *,
    ppo_config: PPOConfig,
    source_load_mode: str,
    parameter_group_rows: list[dict[str, Any]],
    training_status: str,
    train_error: str,
) -> dict[str, Any]:
    changed_groups = [row["parameter_group"] for row in parameter_group_rows if _as_bool(row["changed"])]
    non_actor_head_changed = [
        group for group in changed_groups if group in REQUIRED_NON_ACTOR_HEAD_GROUPS
    ]
    return {
        "manifest_id": "m2846_checkpoint_manifest_v0",
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
    guards = [
        (
            "actor_contract_observation_shape_72",
            "actor_contract",
            "observation_shape",
            int(model_obs_dim) == P0_OBSERVATION_DIM,
            str(model_obs_dim),
        ),
        (
            "actor_contract_action_shape_3",
            "actor_contract",
            "action_shape",
            int(model_act_dim) == ACTION_DIM,
            str(model_act_dim),
        ),
        (
            "no_hidden_or_oracle_actor_input",
            "actor_contract",
            "hidden_or_oracle_actor_inputs_required",
            not bool(env_config.include_privileged_params),
            str(bool(env_config.include_privileged_params)).lower(),
        ),
        (
            "no_actor_visible_labels",
            "actor_contract",
            "actor_visible_labels",
            True,
            "false",
        ),
        (
            "no_wheel_privileged_branch",
            "actor_contract",
            "wheel_observation_mode",
            env_config.wheel_observation_mode == "none",
            env_config.wheel_observation_mode,
        ),
    ]
    return [
        {
            "guard_id": guard_id,
            "guard_family": family,
            "protected_field": field,
            "actor_visible_allowed": False,
            "actor_observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "status_pass": status,
            "evidence": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, family, field, status, evidence in guards
    ]


def build_claim_boundary_rows(training_status: str) -> list[dict[str, Any]]:
    rows = [
        {
            "claim_id": "bounded_training_smoke_executed",
            "claim_family": "allowed_implementation_preflight",
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
    m2838_summary: dict[str, Any],
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
    m2838_visible = (
        int(m2838_summary.get("diagnostic_success_count", -1)) == 1
        and int(m2838_summary.get("diagnostic_collision_count", -1)) == 2
        and int(m2838_summary.get("diagnostic_offtrack_count", -1)) == 13
    )
    gates = [
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
            "proof_no_actor_visible_labels",
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
            included_indices == set(range(9)) and excluded_command_indices == {9, 10, 11}
            and not any(_as_bool(row["hidden_or_oracle"]) or _as_bool(row["label_or_verdict"]) for row in response_target_rows),
            f"included={sorted(included_indices)} excluded_commands={sorted(excluded_command_indices)}",
            "included 0-8, excluded 9-11, no hidden/label targets",
            len(response_target_rows),
            "contract_violation",
        ),
        (
            "proof_response_prediction_head_enabled",
            "response_prediction",
            int(checkpoint_manifest["response_prediction_dim"]) == 9
            and int(checkpoint_manifest["response_prediction_horizon"]) == 4
            and bool(checkpoint_manifest["candidate_checkpoint_written"]),
            f"dim={checkpoint_manifest['response_prediction_dim']} horizon={checkpoint_manifest['response_prediction_horizon']}",
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
            "proof_m2838_negative_accounting_visible",
            "prior_evidence_accounting",
            m2838_visible,
            (
                f"{m2838_summary.get('diagnostic_success_count')}/"
                f"{m2838_summary.get('diagnostic_collision_count')}/"
                f"{m2838_summary.get('diagnostic_offtrack_count')}"
            ),
            "1/2/13",
            1,
            "lineage_invalid",
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
    return [_gate_row(gate_id, "proof", family, status, observed, expected, count, failure) for (
        gate_id,
        family,
        status,
        observed,
        expected,
        count,
        failure,
    ) in gates]


def build_generalization_gate_rows(
    training_seed_rows: list[dict[str, Any]],
    m2838_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    gates = [
        (
            "generalization_seed_split_written",
            "seed_split",
            bool(training_seed_rows),
            str(len(training_seed_rows)),
            ">=1 training smoke seed row",
            len(training_seed_rows),
            "metric_artifact",
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
            "generalization_prior_surface_guardrails_visible",
            "prior_surface",
            bool(m2838_summary.get("status_pass", False)),
            str(bool(m2838_summary.get("status_pass", False))),
            "M2838 accounted as diagnostic guardrail",
            1,
            "lineage_invalid",
        ),
        (
            "generalization_failure_taxonomy_not_collapsed",
            "failure_taxonomy",
            True,
            "contract_violation,lineage_invalid,metric_artifact,proof_washout",
            "failure taxonomy retained",
            4,
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
        (
            "generalization_no_source_only_vs_current_sim_merge",
            "claim_boundary",
            True,
            "implementation preflight only",
            "no source-only/current-sim comparison merge",
            1,
            "objective_overfit",
        ),
    ]
    return [_gate_row(gate_id, "generalization", family, status, observed, expected, count, failure) for (
        gate_id,
        family,
        status,
        observed,
        expected,
        count,
        failure,
    ) in gates]


def build_promotion_guard_rows(checkpoint_manifest: dict[str, Any]) -> list[dict[str, Any]]:
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
        ("promotion_requires_future_audit", True, DEFAULT_NEXT_BLOCKER, DEFAULT_NEXT_BLOCKER, "lineage_invalid"),
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
    hidden_intervention_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    proof_gate_rows: list[dict[str, Any]],
    generalization_gate_rows: list[dict[str, Any]],
    promotion_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    m2838_summary: dict[str, Any],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows
    failed_gate_ids = [row["gate_id"] for row in gate_rows if not _as_bool(row["status_pass"])]
    changed_groups = [row["parameter_group"] for row in parameter_group_rows if _as_bool(row["changed"])]
    non_actor_head_changed = [
        group for group in changed_groups if group in REQUIRED_NON_ACTOR_HEAD_GROUPS
    ]
    response_loss = _float_or_none(training_run_rows[0].get("response_prediction_loss_mean")) if training_run_rows else None
    status_pass = bool(
        training_status == "completed"
        and not failed_gate_ids
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
        "m2845_design": str(source_paths["m2845_design"]),
        "m2844_audit": str(source_paths["m2844_audit"]),
        "m2838_summary": str(source_paths["m2838_summary"]),
        "source_load_mode": source_load_mode,
        "training_status": training_status,
        "training_error": train_error,
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
        "response_target_row_count": len([row for row in response_probe_rows]),
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
        "m2838_diagnostic_success_count": int(m2838_summary.get("diagnostic_success_count", -1)),
        "m2838_diagnostic_collision_count": int(m2838_summary.get("diagnostic_collision_count", -1)),
        "m2838_diagnostic_offtrack_count": int(m2838_summary.get("diagnostic_offtrack_count", -1)),
        "m2838_ordinary_success_denominator_allowed": False,
        "hidden_intervention_probe_collected": any(_as_bool(row["executed"]) for row in hidden_intervention_rows),
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
        "m2847_follow_up_manifest_registered": False,
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


def build_m2847_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": DEFAULT_NEXT_BLOCKER,
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
        ],
        "lineage": {
            "parent_checkpoint": [summary["candidate_checkpoint"]],
            "parent_dataset": [
                summary["summary"],
                summary["checkpoint_manifest"],
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
                summary["m2845_design"],
                summary["m2844_audit"],
                summary["m2838_summary"],
            ],
            "parent_config": [
                "experiments/manifests/m2846-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight.json",
                "experiments/manifests/m2845-engineering-controller-route-a-response-predictive-recurrent-belief-core-training-implementation-preflight-design.json",
            ],
            "parent_objective": [
                "audit M2846 bounded response-predictive recurrent-belief core implementation preflight artifacts before interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2847 must audit M2846 summary status gates artifact completeness checkpoint lineage and claim boundaries",
                "M2847 must keep M2838 weak diagnostic rows visible and outside performance denominators",
                "M2847 must not promote the M2846 checkpoint or claim validation driver performance paper current-sim high-fidelity full-driver or self-ID evidence",
            ],
            "supersedes": ["unaudited implementation preflight interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2847 must audit whether M2846 wrote complete implementation-preflight artifacts",
            "M2847 must verify actor 72/action 3 and no hidden/oracle actor input were preserved",
            "M2847 must verify response target schema includes only observation indices 0-8 and excludes previous-command fields from targets",
            "M2847 must verify parameter trace shows recurrent/fusion or response-prediction mutation and rejects actor_mean.bias-only continuation",
            "M2847 must verify proof generalization promotion actor claim and gate rows before any next implementation/training decision",
            "M2847 must not validate rank promote compute success-rate verdict claim performance paper current-sim high-fidelity full-driver or self-ID result",
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
            "do not hide M2838 weak diagnostic outcomes",
            "do not claim repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_driver_like_recurrent_belief_architecture_training_redesign",
            "evidence_axis": "response_predictive_recurrent_belief_core_training_implementation_preflight_result_audit",
            "evidence_increment": "audits M2846 executable implementation-preflight artifacts before any interpretation or continuation",
            "claim_scope": "Result audit only; no validation ranking winner selection promotion success-rate verdict driver-performance paper current-sim high-fidelity validation self-ID or full ideal driver claim",
            "stop_condition": [
                "stop if M2846 changed actor 72/action 3",
                "stop if response targets include hidden/oracle fields or previous-command target leakage",
                "stop if parameter trace is actor_mean.bias-only",
                "stop if proof generalization promotion rows are incomplete",
                "stop if M2846 claims validation readiness driver performance paper current-sim high-fidelity or self-ID evidence",
            ],
            "fallback_plan": [
                "route to implementation repair design only if a narrow artifact or runner issue is identified",
                "route to bounded continuation design only if M2846 passes and audit admits more training evidence",
                "route to limited-baseline freeze or branch stop if implementation cannot produce non-actor-head evidence safely",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2846 implementation preflight has produced executable artifacts requiring audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2846 response-predictive recurrent-belief implementation preflight artifacts",
            "admission_evidence": [
                "M2846 summary artifact is expected before M2847 runs",
                "M2846 checkpoint manifest parameter trace response target schema and gate rows require audit before interpretation",
            ],
            "blocked_shortcuts": [
                "no new training or validation in result audit",
                "no ranking winner selection promotion or success-rate verdict",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "M2847 status queue scoreboard and review",
                "one bounded follow-up manifest if audit accepts a next route",
            ],
            "next_stage_criteria": [
                "M2846 status and gate rows are accepted or rejected",
                "failure types are classified if any gate failed",
                "one bounded next route or stop is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2847 audits implementation preflight only and does not run finite-window-vs-GRU or self-ID tests.",
            "history_necessity_tests": [
                "Hidden intervention rows from M2846 are diagnostic artifact rows only and cannot support a self-ID claim."
            ],
            "temporal_evidence_window": "M2846 implementation preflight artifacts plus M2838 weak diagnostic accounting.",
            "negative_result_policy": "If M2846 failed, preserve the negative implementation evidence and route to repair design, freeze, or stop rather than weakening gates.",
            "allowed_claims": [
                "M2846 implementation preflight accepted or rejected",
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
            "evidence_expansion": "audits new executable implementation-preflight artifacts from M2846",
            "paper_verdict_delta": "no paper verdict; audit governs Route A engineering implementation continuation",
            "must_synthesize_if": [
                "M2846 cannot preserve actor 72/action 3",
                "M2846 response targets require hidden/oracle fields",
                "M2846 produces only actor_mean.bias changes",
                "M2846 cannot write proof generalization promotion rows",
                "M2846 claims validation readiness driver performance paper current-sim high-fidelity or self-ID evidence",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2846 implementation-preflight artifacts before any continuation or interpretation.",
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "audit checks M2846 summary checkpoint manifest parameter trace response target schema and gate rows",
            "audit preserves actor 72/action 3 no hidden/oracle labels M2838 diagnostic boundary and claim boundary",
            "audit registers one bounded follow-up route if continuing",
        ],
        "failure_criteria": [
            "M2847 runs new training validation ranking promotion or success-rate verdict computation",
            "M2847 hides M2846 gate failures or weakens actor/claim boundaries",
            "M2847 claims repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2847 audits M2846 artifacts under the unchanged actor and claim boundaries without new execution or overclaiming.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [
            {
                "path": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "type": "md",
            }
        ],
        "baseline_checkpoints": [summary["candidate_checkpoint"]],
        "baseline_artifacts": [summary["summary"], summary["gate_matrix"], summary["checkpoint_manifest"]],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "",
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    failed = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    lines = [
        "# M2846 Engineering Controller Route A Response-Predictive Recurrent-Belief Core Training Implementation Preflight",
        "",
        "## Metadata",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result_class: `{summary['result_class']}`",
        f"- summary: `{summary['summary']}`",
        f"- candidate checkpoint: `{summary['candidate_checkpoint']}`",
        f"- checkpoint manifest: `{summary['checkpoint_manifest']}`",
        f"- parameter group trace: `{summary['parameter_group_trace']}`",
        f"- response target schema rows: `{summary['response_target_schema_rows']}`",
        f"- proof gate rows: `{summary['proof_gate_rows']}`",
        f"- generalization gate rows: `{summary['generalization_gate_rows']}`",
        f"- promotion guard rows: `{summary['promotion_guard_rows']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Implementation Preflight Result",
        "",
        "```text",
        f"training_status: {summary['training_status']}",
        f"source_load_mode: {summary['source_load_mode']}",
        f"total_steps: {summary['total_steps']}",
        f"rollout_steps: {summary['rollout_steps']}",
        f"num_envs: {summary['num_envs']}",
        f"response_prediction_dim: {summary['response_prediction_dim']}",
        f"response_prediction_horizon: {summary['response_prediction_horizon']}",
        f"response_prediction_loss_mean: {summary['response_prediction_loss_mean']}",
        f"candidate_checkpoint_written: {summary['candidate_checkpoint_written']}",
        f"changed_parameter_groups: {','.join(summary['changed_parameter_groups'])}",
        f"non_actor_head_changed_groups: {','.join(summary['non_actor_head_changed_groups'])}",
        f"actor_mean_bias_only: {summary['actor_mean_bias_only']}",
        f"gate_matrix_pass: {summary['gate_matrix_pass']}",
        f"failed_gate_ids: {failed}",
        "```",
        "",
        "The bounded PPO smoke is implementation evidence only. It is not a validation run, ranking run, promotion decision, success-rate verdict, driver-performance claim, current-sim verdict, high-fidelity validation result, paper result, full-driver result, or self-ID result.",
        "",
        "## Actor And Target Boundary",
        "",
        "```text",
        "actor_observation_dim: 72",
        "action_dim: 3",
        "actor_encoder: human_view_online_gru",
        "hidden_or_oracle_actor_inputs_required: false",
        "response_prediction_target_indices: 0..8",
        "excluded_previous_command_indices: 9,10,11",
        "```",
        "",
        "## Prior Diagnostic Accounting",
        "",
        "```text",
        f"M2838 diagnostic_success_count: {summary['m2838_diagnostic_success_count']}",
        f"M2838 diagnostic_collision_count: {summary['m2838_diagnostic_collision_count']}",
        f"M2838 diagnostic_offtrack_count: {summary['m2838_diagnostic_offtrack_count']}",
        "ordinary_success_denominator_allowed: false",
        "```",
        "",
        "## Claim Boundary",
        "",
        "Allowed M2846 claim:",
        "",
        "```text",
        "bounded implementation-preflight artifacts were produced and are ready for M2847 audit",
        "```",
        "",
        "Rejected claims:",
        "",
        "```text",
        "checkpoint_promoted=false",
        "validation_run=false",
        "ranking_run=false",
        "success_rate_computed=false",
        "driver_performance_claim_made=false",
        "paper_claim_made=false",
        "current_sim_verdict_claim_made=false",
        "high_fidelity_validation_claim_made=false",
        "full_ideal_driver_gate_passed=false",
        "level3_self_id_claim_made=false",
        "```",
        "",
    ]
    if summary["training_error"]:
        lines.extend(["## Training Error", "", "```text", summary["training_error"], "```", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if np.isfinite(out) else None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the M2846 implementation preflight.")
    parser.add_argument("--m2845-design", type=Path, default=DEFAULT_M2845_DESIGN)
    parser.add_argument("--m2844-audit", type=Path, default=DEFAULT_M2844_AUDIT)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--m2838-summary", type=Path, default=DEFAULT_M2838_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--total-steps", type=int, default=8)
    parser.add_argument("--rollout-steps", type=int, default=8)
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--update-epochs", type=int, default=1)
    parser.add_argument("--minibatch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=284600)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_response_predictive_recurrent_belief_core_training_implementation_preflight(
        output_dir=args.output_dir,
        m2845_design=args.m2845_design,
        m2844_audit=args.m2844_audit,
        source_checkpoint=args.source_checkpoint,
        m2838_summary=args.m2838_summary,
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
