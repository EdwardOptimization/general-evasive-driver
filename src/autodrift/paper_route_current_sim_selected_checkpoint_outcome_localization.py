"""Episode-level outcome localization for M2241 selected checkpoints."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.controller_profile_runtime import ControllerProfileObservationWrapper, mask_spec_from_config
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy, run_episode_with_policy


DEFAULT_SELECTED_ROWS = Path(
    "runs/m2241_paper_route_current_sim_training_stability_repair_execution/selected_checkpoint_rows.csv"
)
DEFAULT_CONFIG_ROOT = Path("runs/m2241_paper_route_current_sim_training_stability_repair_execution/configs")
DEFAULT_OUTPUT_DIR = Path("runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization")
DEFAULT_TASK_ID = "m2244-paper-route-current-sim-selected-checkpoint-outcome-localization-implementation"
DEFAULT_NEXT_BLOCKER = "m2245-paper-route-current-sim-selected-checkpoint-outcome-localization-result-audit"
EPISODES_PER_SELECTED_CHECKPOINT = 32
EXPECTED_SELECTED_CHECKPOINT_COUNT = 15
EXPECTED_EPISODE_ROW_COUNT = EXPECTED_SELECTED_CHECKPOINT_COUNT * EPISODES_PER_SELECTED_CHECKPOINT

AGGREGATE_FIELDNAMES = [
    "group_axis",
    "group_key",
    "group_value",
    "episode_count",
    "success_count",
    "success_rate",
    "collision_count",
    "collision_rate",
    "offtrack_count",
    "offtrack_rate",
    "max_step_noncompletion_count",
    "max_step_noncompletion_rate",
    "other_failure_count",
    "other_failure_rate",
    "mean_return",
    "mean_steps",
    "mean_min_clearance_margin",
    "min_min_clearance_margin",
    "mean_max_off_track_overshoot",
    "mean_time_to_first_off_track_s",
    "mean_high_sideslip_fraction",
    "mean_action_rate",
    "dominant_failure_mode",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

REPAIR_ROUTE_FIELDNAMES = [
    "route",
    "admitted",
    "dominant_failure_mode",
    "episode_count",
    "success_rate",
    "offtrack_rate",
    "collision_rate",
    "max_step_noncompletion_rate",
    "reason",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

EpisodeRunner = Callable[[Path, Mapping[str, Any], Mapping[str, Any], int, str], dict[str, Any]]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(parsed):
        return None
    return parsed


def _mean(values: Sequence[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    if not finite:
        return None
    return float(np.mean(finite))


def _min(values: Sequence[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    if not finite:
        return None
    return float(np.min(finite))


def _default_episode_runner(
    checkpoint_path: Path,
    config: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    episode_seed: int,
    device: str,
) -> dict[str, Any]:
    del selected_row
    env_config = build_env_config(config.get("env", {}))
    mask_spec = mask_spec_from_config(dict(config))
    env = AutoDriftEnv(env_config)
    if mask_spec.enabled:
        env = ControllerProfileObservationWrapper(env, mask_spec)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
    target_obs_dim = int(env.observation_space.shape[0])
    if model.obs_dim != target_obs_dim:
        model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device, obs_dim=target_obs_dim)
    policy = ActorPolicy(
        model,
        env_config,
        reset_hidden_policy=mask_spec.reset_hidden_policy,
    )
    return run_episode_with_policy(env, policy, "checkpoint", int(episode_seed))


def _config_path(config_root: Path, profile_name: str, seed_id: int) -> Path:
    return config_root / profile_name / f"seed_{int(seed_id)}" / "config.json"


def _failure_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        bucket = str(row.get("outcome_bucket", ""))
        termination_reason = str(row.get("termination_reason", ""))
        if bucket == "success_obstacle_pass" or (_bool(row.get("obstacle_completed")) and not _bool(row.get("collision"))):
            counts["success"] += 1
        elif bucket == "collision_failure" or _bool(row.get("collision")):
            counts["collision"] += 1
        elif bucket == "off_track_noncollision_noncompletion" or termination_reason == "off_track":
            counts["offtrack"] += 1
        elif bucket == "max_steps_noncompletion" or _bool(row.get("truncated")):
            counts["max_step_noncompletion"] += 1
        else:
            counts["other_failure"] += 1
    return dict(counts)


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _dominant_failure_mode(rows: Sequence[Mapping[str, Any]], *, expected_count: int | None = None) -> str:
    total = len(rows)
    if expected_count is not None and total != expected_count:
        return "low_support_or_incomplete"
    counts = _failure_counts(rows)
    success = counts.get("success", 0)
    if total and _rate(success, total) >= 2.0 / 3.0:
        return "success_supported"
    failures = max(1, total - success)
    buckets = (
        ("offtrack_dominated_failure", counts.get("offtrack", 0)),
        ("collision_dominated_failure", counts.get("collision", 0)),
        ("max_step_noncompletion_dominated_failure", counts.get("max_step_noncompletion", 0)),
        ("mixed_failure", counts.get("other_failure", 0)),
    )
    for label, count in buckets[:-1]:
        if count / failures >= 0.5:
            return label
    return "mixed_failure"


def _aggregate_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_axis: str,
    group_key: str,
    group_value: str,
    expected_count: int | None = None,
) -> dict[str, Any]:
    counts = _failure_counts(rows)
    total = len(rows)
    return {
        "group_axis": group_axis,
        "group_key": group_key,
        "group_value": group_value,
        "episode_count": total,
        "success_count": counts.get("success", 0),
        "success_rate": _rate(counts.get("success", 0), total),
        "collision_count": counts.get("collision", 0),
        "collision_rate": _rate(counts.get("collision", 0), total),
        "offtrack_count": counts.get("offtrack", 0),
        "offtrack_rate": _rate(counts.get("offtrack", 0), total),
        "max_step_noncompletion_count": counts.get("max_step_noncompletion", 0),
        "max_step_noncompletion_rate": _rate(counts.get("max_step_noncompletion", 0), total),
        "other_failure_count": counts.get("other_failure", 0),
        "other_failure_rate": _rate(counts.get("other_failure", 0), total),
        "mean_return": _mean([_float_or_none(row.get("return")) for row in rows]),
        "mean_steps": _mean([_float_or_none(row.get("steps")) for row in rows]),
        "mean_min_clearance_margin": _mean([_float_or_none(row.get("min_clearance_margin")) for row in rows]),
        "min_min_clearance_margin": _min([_float_or_none(row.get("min_clearance_margin")) for row in rows]),
        "mean_max_off_track_overshoot": _mean(
            [_float_or_none(row.get("max_off_track_overshoot")) for row in rows]
        ),
        "mean_time_to_first_off_track_s": _mean(
            [_float_or_none(row.get("time_to_first_off_track_s")) for row in rows]
        ),
        "mean_high_sideslip_fraction": _mean([_float_or_none(row.get("high_sideslip_fraction")) for row in rows]),
        "mean_action_rate": _mean([_float_or_none(row.get("action_rate_mean")) for row in rows]),
        "dominant_failure_mode": _dominant_failure_mode(rows, expected_count=expected_count),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _group_rows(rows: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> dict[tuple[str, ...], list[Mapping[str, Any]]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(key, "")) for key in keys)].append(row)
    return grouped


def _profile_seed_aggregates(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for key, group in sorted(_group_rows(rows, ("profile_name", "seed_id")).items()):
        output.append(
            _aggregate_row(
                group,
                group_axis="profile_seed",
                group_key="profile_name|seed_id",
                group_value="|".join(key),
                expected_count=EPISODES_PER_SELECTED_CHECKPOINT,
            )
        )
    return output


def _single_key_aggregates(rows: Sequence[Mapping[str, Any]], *, key: str, expected_count: int | None = None) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for value, group in sorted(_group_rows(rows, (key,)).items()):
        output.append(
            _aggregate_row(
                group,
                group_axis=key,
                group_key=key,
                group_value=value[0],
                expected_count=expected_count,
            )
        )
    return output


def _repair_route(global_row: Mapping[str, Any]) -> list[dict[str, Any]]:
    mode = str(global_row.get("dominant_failure_mode", ""))
    route_by_mode = {
        "offtrack_dominated_failure": "offtrack_recovery_reward_and_corridor_repair_design",
        "collision_dominated_failure": "obstacle_timing_clearance_collision_penalty_repair_design",
        "max_step_noncompletion_dominated_failure": "progress_completion_reward_repair_design",
        "mixed_failure": "task_curriculum_stratification_design",
        "success_supported": "readiness_floor_or_validation_audit",
        "low_support_or_incomplete": "outcome_localization_runner_repair",
    }
    route = route_by_mode.get(mode, "task_curriculum_stratification_design")
    return [
        {
            "route": route,
            "admitted": True,
            "dominant_failure_mode": mode,
            "episode_count": global_row.get("episode_count", 0),
            "success_rate": global_row.get("success_rate", 0.0),
            "offtrack_rate": global_row.get("offtrack_rate", 0.0),
            "collision_rate": global_row.get("collision_rate", 0.0),
            "max_step_noncompletion_rate": global_row.get("max_step_noncompletion_rate", 0.0),
            "reason": f"global dominant failure mode is {mode}",
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
        }
    ]


def run_selected_checkpoint_outcome_localization(
    *,
    selected_rows_path: Path | str = DEFAULT_SELECTED_ROWS,
    config_root: Path | str = DEFAULT_CONFIG_ROOT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    episodes_per_selected_checkpoint: int = EPISODES_PER_SELECTED_CHECKPOINT,
    device: str = "cpu",
    episode_runner: EpisodeRunner = _default_episode_runner,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    selected_rows = read_csv_rows(selected_rows_path)
    configs = Path(config_root)
    episode_rows: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    for selected in selected_rows:
        profile_name = str(selected.get("profile_name", ""))
        seed_id = int(selected.get("seed_id", -1))
        checkpoint_path = Path(str(selected.get("selected_checkpoint_path", "")))
        config_path = _config_path(configs, profile_name, seed_id)
        if not checkpoint_path.exists():
            missing_inputs.append(str(checkpoint_path))
            continue
        if not config_path.exists():
            missing_inputs.append(str(config_path))
            continue
        config = read_json(config_path)
        for episode_index in range(int(episodes_per_selected_checkpoint)):
            episode_seed = seed_id + 10_000 + episode_index
            row = episode_runner(checkpoint_path, config, selected, episode_seed, device)
            row.update(
                {
                    "profile_name": profile_name,
                    "seed_id": seed_id,
                    "selected_checkpoint_step": int(float(selected.get("selected_checkpoint_step", -1))),
                    "selected_checkpoint_path": str(checkpoint_path),
                    "selected_readiness_floor_pass": _bool(selected.get("selected_readiness_floor_pass")),
                    "episode_seed": episode_seed,
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
            episode_rows.append(row)

    global_row = _aggregate_row(
        episode_rows,
        group_axis="global",
        group_key="global",
        group_value="all",
        expected_count=EXPECTED_EPISODE_ROW_COUNT,
    )
    profile_seed_rows = _profile_seed_aggregates(episode_rows)
    profile_rows = _single_key_aggregates(
        episode_rows,
        key="profile_name",
        expected_count=EPISODES_PER_SELECTED_CHECKPOINT * len({row.get("seed_id") for row in episode_rows}),
    )
    outcome_rows = _single_key_aggregates(episode_rows, key="outcome_bucket")
    termination_rows = _single_key_aggregates(episode_rows, key="termination_reason")
    route_rows = _repair_route(global_row)

    write_csv_rows(output / "episode_rows.csv", episode_rows)
    write_csv_rows(output / "profile_seed_aggregate.csv", profile_seed_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "profile_aggregate.csv", profile_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "outcome_aggregate.csv", outcome_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "termination_aggregate.csv", termination_rows, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "repair_route_candidates.csv", route_rows, fieldnames=REPAIR_ROUTE_FIELDNAMES)

    profile_seed_complete = all(
        int(row.get("episode_count", 0)) == int(episodes_per_selected_checkpoint) for row in profile_seed_rows
    )
    guardrail_flags = {
        "private_holdout_used": False,
        "winner_selected": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "actor_input_contract_changed": False,
        "training_started": False,
        "ppo_started": False,
        "replay_started": False,
        "promoted": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    result_class = (
        "current_sim_selected_checkpoint_outcome_localization_pass"
        if (
            not missing_inputs
            and len(selected_rows) == EXPECTED_SELECTED_CHECKPOINT_COUNT
            and len(episode_rows) == EXPECTED_EPISODE_ROW_COUNT
            and profile_seed_complete
            and len(route_rows) >= 1
            and guardrail_violation_count == 0
        )
        else "current_sim_selected_checkpoint_outcome_localization_fail"
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "selected_rows_path": str(selected_rows_path),
        "config_root": str(config_root),
        "output_dir": str(output),
        "selected_checkpoint_count": len(selected_rows),
        "expected_selected_checkpoint_count": EXPECTED_SELECTED_CHECKPOINT_COUNT,
        "episodes_per_selected_checkpoint": int(episodes_per_selected_checkpoint),
        "episode_row_count": len(episode_rows),
        "expected_episode_row_count": EXPECTED_EPISODE_ROW_COUNT,
        "profile_seed_group_count": len(profile_seed_rows),
        "profile_seed_groups_complete": profile_seed_complete,
        "missing_input_count": len(missing_inputs),
        "missing_inputs": missing_inputs,
        "global_outcome": global_row,
        "primary_repair_route": route_rows[0]["route"] if route_rows else "",
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "episode_rows": str(output / "episode_rows.csv"),
            "profile_seed_aggregate": str(output / "profile_seed_aggregate.csv"),
            "profile_aggregate": str(output / "profile_aggregate.csv"),
            "outcome_aggregate": str(output / "outcome_aggregate.csv"),
            "termination_aggregate": str(output / "termination_aggregate.csv"),
            "repair_route_candidates": str(output / "repair_route_candidates.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": DEFAULT_TASK_ID,
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected-rows", type=Path, default=DEFAULT_SELECTED_ROWS)
    parser.add_argument("--config-root", type=Path, default=DEFAULT_CONFIG_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--episodes-per-selected-checkpoint", type=int, default=EPISODES_PER_SELECTED_CHECKPOINT)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_selected_checkpoint_outcome_localization(
        selected_rows_path=args.selected_rows,
        config_root=args.config_root,
        output_dir=args.output_dir,
        episodes_per_selected_checkpoint=int(args.episodes_per_selected_checkpoint),
        device=str(args.device),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"episode_rows={Path(args.output_dir) / 'episode_rows.csv'}")
    print(f"repair_route={summary['primary_repair_route']}")
    print(f"result_class={summary['result_class']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
