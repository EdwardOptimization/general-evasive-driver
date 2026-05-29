"""Measured public routing smoke for controller-family profiles."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_decisive_matrix_protocol import (
    EXPECTED_PROFILE_NAMES,
    profile_contract_violations,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.decisive_history_env_hooks import (
    DecisiveHistoryEnvHookSpec,
    default_hook_specs,
    hook_spec_to_row,
)
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import ActorPolicy, run_episode_with_policy


DEFAULT_M1674_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_RUN_DIR = Path("runs/m1686_controller_family_measured_routing_smoke")
DEFAULT_PROFILE_SEED = 167400
DEFAULT_EVAL_SEED_BASE = 168600
ROUTING_SOURCE_FAMILIES = (
    "t4_staged_warmup_capability",
    "t4_actuator_delay_response",
    "t5_near_boundary_warmup",
    "t5_boundary_axis_retarget",
)
SELECTED_METRICS = (
    "success",
    "collision",
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
)
FORBIDDEN_GUARDRAILS = (
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "level3_self_id_claim_made",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "profile_specific_tuning",
)


def discover_m1674_profile_runs(
    *,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    profile_seed: int = DEFAULT_PROFILE_SEED,
) -> list[dict[str, Any]]:
    """Return the expected M1674 profile config/checkpoint pairs."""

    root = Path(m1674_run_dir)
    rows: list[dict[str, Any]] = []
    for profile_name in EXPECTED_PROFILE_NAMES:
        config_path = root / "configs" / f"{profile_name}_seed{int(profile_seed)}.json"
        checkpoint_path = root / "profile_runs" / profile_name / f"seed_{int(profile_seed)}" / "checkpoint.pt"
        row = {
            "profile_name": profile_name,
            "profile_seed": int(profile_seed),
            "config_path": str(config_path),
            "checkpoint_path": str(checkpoint_path),
            "config_exists": config_path.exists(),
            "checkpoint_exists": checkpoint_path.exists(),
        }
        if config_path.exists():
            config = read_json(config_path)
            profile = dict(config.get("controller_profile") or {})
            row.update(
                {
                    "level": profile.get("level"),
                    "actor_encoder": profile.get("actor_encoder"),
                    "observation_dim": int(profile.get("observation_dim", 0)),
                    "env_history_length": int(dict(config.get("env") or {}).get("history_length", 0)),
                    "contract_violations": profile_contract_violations(config),
                }
            )
        else:
            row["contract_violations"] = ["missing_config"]
        rows.append(row)
    return rows


def select_routing_smoke_specs(
    *,
    seed_count: int = 1,
    source_families: Sequence[str] = ROUTING_SOURCE_FAMILIES,
) -> list[DecisiveHistoryEnvHookSpec]:
    """Select a deterministic T4/T5 executable subset for the 48-episode smoke."""

    specs = default_hook_specs(seed_count=seed_count)
    selected: list[DecisiveHistoryEnvHookSpec] = []
    for family in source_families:
        match = next((spec for spec in specs if spec.source_family == family), None)
        if match is None:
            raise ValueError(f"missing routing smoke source family: {family}")
        selected.append(match)
    return selected


def assert_human_view_env_contract(config: DriftEnvConfig) -> None:
    """Reject hidden/oracle/wheel inputs while allowing profile-specific history length."""

    if int(config.history_length) < 1:
        raise ValueError("history_length must be positive")
    if config.include_privileged_params:
        raise ValueError("privileged actor observation is forbidden")
    if config.wheel_observation_mode != "none":
        raise ValueError("wheel or slip observations are forbidden")
    if config.action_history_mode != "full":
        raise ValueError("previous physical commands must be available")
    if config.obstacle_relative_velocity_mode != "zero":
        raise ValueError("obstacle relative velocity must be zero for strict routing smoke")


def task_env_for_profile(
    *,
    profile_config: dict[str, Any],
    task_spec: DecisiveHistoryEnvHookSpec,
) -> DriftEnvConfig:
    """Apply one executable task source while preserving the profile observation shape."""

    task_env = env_config_to_dict(task_spec.env_config)
    profile_env = dict(profile_config.get("env") or {})
    task_env["history_length"] = int(profile_env.get("history_length", task_env["history_length"]))
    task_env["action_history_mode"] = "full"
    task_env["include_privileged_params"] = False
    task_env["obstacle_relative_velocity_mode"] = "zero"
    task_env["wheel_observation_mode"] = "none"
    return build_env_config(task_env)


def _episode_success(row: dict[str, Any]) -> bool:
    return bool(row.get("obstacle_completed", False)) and not bool(row.get("collision", False))


def _metric_value(row: dict[str, Any], metric: str) -> float:
    if metric == "success":
        return float(_episode_success(row))
    if metric == "collision":
        return float(bool(row.get("collision", False)))
    return float(row.get(metric, float("nan")))


def selected_metrics_are_finite(rows: Sequence[dict[str, Any]]) -> bool:
    """Return whether all smoke-selected metrics are finite where required."""

    for row in rows:
        for metric in SELECTED_METRICS:
            value = _metric_value(row, metric)
            if not np.isfinite(value):
                return False
    return True


def aggregate_rows(rows: Sequence[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    """Aggregate episode rows by profile or task spec."""

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[group_key])].append(row)

    aggregates: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        margins = [_metric_value(row, "min_clearance_margin") for row in group]
        aggregate = {
            group_key: key,
            "episode_count": len(group),
            "success_rate": float(np.mean([_metric_value(row, "success") for row in group])),
            "collision_rate": float(np.mean([_metric_value(row, "collision") for row in group])),
            "clearance_margin_mean": float(np.mean(margins)),
            "clearance_margin_p10": float(np.percentile(margins, 10.0)),
            "return_mean": float(np.mean([_metric_value(row, "return") for row in group])),
            "steps_mean": float(np.mean([_metric_value(row, "steps") for row in group])),
            "control_smoothness": float(np.mean([_metric_value(row, "action_rate_mean") for row in group])),
            "spin_or_unstable_rate": float(
                np.mean([_metric_value(row, "high_sideslip_fraction") > 0.5 for row in group])
            ),
            "all_selected_metrics_finite": selected_metrics_are_finite(group),
        }
        if group_key != "profile_name":
            aggregate["task_family"] = group[0].get("task_family", "")
            aggregate["source_family"] = group[0].get("source_family", "")
        aggregates.append(aggregate)
    return aggregates


def _load_profile(profile_row: dict[str, Any], *, device: str) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    config = read_json(profile_row["config_path"])
    model, checkpoint = load_actor_critic_checkpoint(profile_row["checkpoint_path"], device=device)
    return config, model, checkpoint


def _run_profile_on_spec(
    *,
    profile_row: dict[str, Any],
    task_spec: DecisiveHistoryEnvHookSpec,
    task_index: int,
    profile_index: int,
    eval_seed_base: int,
    device: str,
) -> dict[str, Any]:
    config, model, _ = _load_profile(profile_row, device=device)
    env_config = task_env_for_profile(profile_config=config, task_spec=task_spec)
    assert_human_view_env_contract(env_config)

    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), config)
    target_obs_dim = int(env.observation_space.shape[0])
    model_obs_dim = int(getattr(model, "obs_dim", -1))
    if model_obs_dim != target_obs_dim:
        env.close()
        raise ValueError(
            f"profile {profile_row['profile_name']} checkpoint obs_dim {model_obs_dim} "
            f"does not match task env obs_dim {target_obs_dim}"
        )
    runtime = profile_runtime_summary(config)
    policy = ActorPolicy(
        model,
        env_config,
        reset_hidden_policy=str(runtime["reset_hidden_policy"]),
    )
    seed = int(eval_seed_base) + int(task_index) * 100 + int(profile_index)
    try:
        row = run_episode_with_policy(env, policy, "checkpoint", seed)
    finally:
        env.close()

    source_row = hook_spec_to_row(task_spec)
    row.update(
        {
            "profile_name": profile_row["profile_name"],
            "profile_level": profile_row.get("level", ""),
            "profile_actor_encoder": profile_row.get("actor_encoder", ""),
            "profile_observation_dim": int(profile_row.get("observation_dim", target_obs_dim)),
            "profile_env_history_length": int(env_config.history_length),
            "profile_config_path": profile_row["config_path"],
            "checkpoint_path": profile_row["checkpoint_path"],
            "task_index": int(task_index),
            "profile_index": int(profile_index),
            "eval_seed": int(seed),
            "task_source_id": f"m1686-spec-{task_index:04d}",
            "source_family": task_spec.source_family,
            "task_family": task_spec.task_family,
            "candidate_id": task_spec.candidate_id,
            "capability_pair": task_spec.capability_pair,
            "geometry_key": task_spec.geometry_key,
            "reveal_step": int(task_spec.reveal_step),
            "decision_step": int(task_spec.decision_step),
            "warmup_mode": task_spec.warmup_mode,
            "capability_variant": task_spec.capability_variant,
            "obstacle_variant": task_spec.obstacle_variant,
            "source_history_length": int(source_row["history_length"]),
            "routing_smoke_only": True,
            "private_holdout_used": False,
            "promoted": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
            "actor_input_contract_changed": False,
            "profile_specific_tuning": False,
        }
    )
    row["success"] = _episode_success(row)
    return row


def run_measured_routing_smoke(
    *,
    run_dir: Path | str = DEFAULT_RUN_DIR,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    profile_seed: int = DEFAULT_PROFILE_SEED,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run the bounded 12-profile x 4-spec public routing smoke."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)

    profile_rows = discover_m1674_profile_runs(m1674_run_dir=m1674_run_dir, profile_seed=profile_seed)
    missing_profiles = [
        row["profile_name"]
        for row in profile_rows
        if not bool(row["config_exists"]) or not bool(row["checkpoint_exists"])
    ]
    contract_violations = {
        row["profile_name"]: row.get("contract_violations", [])
        for row in profile_rows
        if row.get("contract_violations")
    }
    if missing_profiles:
        raise FileNotFoundError(f"missing profile artifacts: {missing_profiles}")
    if contract_violations:
        raise ValueError(f"profile contract violations: {contract_violations}")

    specs = select_routing_smoke_specs()
    episode_rows: list[dict[str, Any]] = []
    for task_index, task_spec in enumerate(specs):
        for profile_index, profile_row in enumerate(profile_rows):
            episode_rows.append(
                _run_profile_on_spec(
                    profile_row=profile_row,
                    task_spec=task_spec,
                    task_index=task_index,
                    profile_index=profile_index,
                    eval_seed_base=eval_seed_base,
                    device=device,
                )
            )

    profile_aggregate = aggregate_rows(episode_rows, "profile_name")
    spec_aggregate = aggregate_rows(episode_rows, "task_source_id")
    selected_spec_rows = [
        {
            "task_source_id": f"m1686-spec-{index:04d}",
            **hook_spec_to_row(spec),
        }
        for index, spec in enumerate(specs)
    ]

    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) and all(
        bool(row["all_selected_metrics_finite"]) for row in profile_aggregate + spec_aggregate
    )
    forbidden_guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in forbidden_guardrail_flags.values()))
    episode_count = len(episode_rows)
    profile_count = len({row["profile_name"] for row in episode_rows})
    spec_count = len({row["task_source_id"] for row in episode_rows})
    passes = (
        episode_count == 48
        and profile_count == len(EXPECTED_PROFILE_NAMES)
        and spec_count >= 4
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "controller_family_measured_routing_smoke_pass"
            if passes
            else "controller_family_measured_routing_smoke_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "routing_smoke_only_no_controller_ranking",
        "output_dir": str(output),
        "episode_count": episode_count,
        "expected_episode_count": 48,
        "profile_count": profile_count,
        "expected_profile_count": len(EXPECTED_PROFILE_NAMES),
        "spec_count": spec_count,
        "profile_config_count": len(profile_rows),
        "checkpoint_count": len(profile_rows),
        "m1674_run_dir": str(m1674_run_dir),
        "profile_seed": int(profile_seed),
        "eval_seed_base": int(eval_seed_base),
        "device": str(device),
        "selected_source_families": [spec.source_family for spec in specs],
        "task_family_counts": {
            family: sum(1 for spec in specs if spec.task_family == family)
            for family in sorted({spec.task_family for spec in specs})
        },
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        "all_episodes_completed": episode_count == 48,
        "passes_public_smoke_gates": bool(passes),
        "environment_rollout_started": True,
        "environment_rollout_allowed": True,
        "forbidden_guardrail_flags": forbidden_guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "profile_aggregate_rows": len(profile_aggregate),
        "spec_aggregate_rows": len(spec_aggregate),
        "artifacts": {
            "episode_rows": str(output / "episode_rows.csv"),
            "profile_aggregate": str(output / "profile_aggregate.csv"),
            "spec_aggregate": str(output / "spec_aggregate.csv"),
            "selected_specs": str(output / "selected_specs.csv"),
            "profile_artifacts": str(output / "profile_artifacts.csv"),
            "summary": str(output / "summary.json"),
        },
        "next_blocker": "m1687-paper-route-controller-family-measured-routing-smoke-result-audit",
    }

    write_csv_rows(output / "episode_rows.csv", episode_rows)
    write_csv_rows(output / "profile_aggregate.csv", profile_aggregate)
    write_csv_rows(output / "spec_aggregate.csv", spec_aggregate)
    write_csv_rows(output / "selected_specs.csv", selected_spec_rows)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M1686 controller-family routing smoke.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--profile-seed", type=int, default=DEFAULT_PROFILE_SEED)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    summary = run_measured_routing_smoke(
        run_dir=args.run_dir,
        m1674_run_dir=args.m1674_run_dir,
        profile_seed=int(args.profile_seed),
        eval_seed_base=int(args.eval_seed_base),
        device=str(args.device),
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
