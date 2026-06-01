"""No-rerun checkpoint-quality audit for current-sim recurrent-profile blocker."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_CHECKPOINT_MATERIALIZATION_DIR = Path("runs/m2171_paper_route_current_sim_checkpoint_profile_materialization")
DEFAULT_FAILURE_METRICS = Path(
    "runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/profile_failure_metric_summary.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2224_paper_route_current_sim_recurrent_profile_checkpoint_quality_audit")
DEFAULT_NEXT_BLOCKER = "m2225-paper-route-current-sim-recurrent-profile-checkpoint-quality-result-audit"
PROFILE_ROWS = "profile_checkpoint_rows.csv"
SMOKE_SCALE_STEP_THRESHOLD = 2048
WEAK_EVAL_TERMINATION_THRESHOLD = 0.5
WEAK_EVAL_LATERAL_RMSE_THRESHOLD = 1.0
WEAK_TRAIN_TERMINATION_THRESHOLD = 0.5


QUALITY_FIELDNAMES = [
    "profile_name",
    "profile_level",
    "actor_encoder",
    "actor_history_length",
    "env_history_length",
    "observation_dim",
    "checkpoint_path",
    "checkpoint_exists",
    "checkpoint_materialization_mode",
    "checkpoint_source_profile_name",
    "quality_metric_source_profile_name",
    "quality_metric_source_mode",
    "training_enabled",
    "training_started_for_profile",
    "training_returncode",
    "total_train_steps",
    "final_rollout_return_mean",
    "final_reward_mean",
    "final_episode_count",
    "final_episode_length_mean",
    "final_train_termination_rate",
    "eval_return_mean",
    "eval_steps_mean",
    "eval_termination_rate",
    "eval_lateral_rmse_mean",
    "eval_beta_abs_error_mean",
    "smoke_scale_training",
    "weak_eval_flag",
    "weak_train_flag",
    "input_contract",
    "uses_hidden_oracle_actor_inputs",
    "uses_wheel_or_slip_inputs",
    "uses_reference_or_ttc_inputs",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

JOIN_FIELDNAMES = [
    "profile_name",
    "profile_metric_row_count",
    "diagnostic_episode_count",
    "diagnostic_success_count",
    "diagnostic_collision_count",
    "diagnostic_offtrack_count",
    "diagnostic_success_rate",
    "diagnostic_collision_rate",
    "diagnostic_offtrack_rate",
    "failure_mode_counts",
    "total_train_steps",
    "eval_return_mean",
    "eval_termination_rate",
    "eval_lateral_rmse_mean",
    "final_train_termination_rate",
    "smoke_scale_training",
    "weak_eval_flag",
    "weak_train_flag",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "finite_window_vs_gru_conclusion_made",
]

CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


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
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    parsed = _float_or_none(value)
    if parsed is None:
        return None
    return int(parsed)


def _last_train_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv_rows(path)
    if not rows:
        return {}
    return rows[-1]


def _eval_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = read_json(path)
    if not isinstance(data, dict):
        return {}
    return data


def _quality_row(materialization_dir: Path, row: Mapping[str, Any]) -> dict[str, Any]:
    profile = str(row.get("profile_name", ""))
    source_profile = str(row.get("checkpoint_source_profile_name", profile) or profile)
    profile_dir = materialization_dir / "profiles" / profile
    metric_profile = profile
    metric_mode = "own_profile_metrics"
    if not (profile_dir / "train_metrics.csv").exists() and source_profile and source_profile != profile:
        profile_dir = materialization_dir / "profiles" / source_profile
        metric_profile = source_profile
        metric_mode = "inherited_checkpoint_source_metrics"
    train_tail = _last_train_row(profile_dir / "train_metrics.csv")
    eval_summary = _eval_summary(profile_dir / "eval_summary.json")
    total_train_steps = _int_or_none(train_tail.get("step"))
    eval_termination = _float_or_none(eval_summary.get("termination_rate"))
    eval_lateral_rmse = _float_or_none(eval_summary.get("lateral_rmse_mean"))
    final_train_termination = _float_or_none(train_tail.get("termination_rate"))
    smoke_scale_training = total_train_steps is not None and total_train_steps <= SMOKE_SCALE_STEP_THRESHOLD
    weak_eval_flag = bool(
        (eval_termination is not None and eval_termination >= WEAK_EVAL_TERMINATION_THRESHOLD)
        or (eval_lateral_rmse is not None and eval_lateral_rmse >= WEAK_EVAL_LATERAL_RMSE_THRESHOLD)
    )
    weak_train_flag = bool(
        final_train_termination is not None and final_train_termination >= WEAK_TRAIN_TERMINATION_THRESHOLD
    )
    return {
        "profile_name": profile,
        "profile_level": row.get("profile_level", ""),
        "actor_encoder": row.get("actor_encoder", ""),
        "actor_history_length": _int_or_none(row.get("actor_history_length")),
        "env_history_length": _int_or_none(row.get("env_history_length")),
        "observation_dim": _int_or_none(row.get("observation_dim")),
        "checkpoint_path": row.get("checkpoint_path", ""),
        "checkpoint_exists": _bool(row.get("checkpoint_exists")),
        "checkpoint_materialization_mode": row.get("checkpoint_materialization_mode", ""),
        "checkpoint_source_profile_name": row.get("checkpoint_source_profile_name", ""),
        "quality_metric_source_profile_name": metric_profile,
        "quality_metric_source_mode": metric_mode,
        "training_enabled": _bool(row.get("training_enabled")),
        "training_started_for_profile": _bool(row.get("training_started_for_profile")),
        "training_returncode": _int_or_none(row.get("training_returncode")),
        "total_train_steps": total_train_steps,
        "final_rollout_return_mean": _float_or_none(train_tail.get("rollout_return_mean")),
        "final_reward_mean": _float_or_none(train_tail.get("reward_mean")),
        "final_episode_count": _int_or_none(train_tail.get("episode_count")),
        "final_episode_length_mean": _float_or_none(train_tail.get("episode_length_mean")),
        "final_train_termination_rate": final_train_termination,
        "eval_return_mean": _float_or_none(eval_summary.get("return_mean")),
        "eval_steps_mean": _float_or_none(eval_summary.get("steps_mean")),
        "eval_termination_rate": eval_termination,
        "eval_lateral_rmse_mean": eval_lateral_rmse,
        "eval_beta_abs_error_mean": _float_or_none(eval_summary.get("beta_abs_error_mean")),
        "smoke_scale_training": smoke_scale_training,
        "weak_eval_flag": weak_eval_flag,
        "weak_train_flag": weak_train_flag,
        "input_contract": row.get("input_contract", ""),
        "uses_hidden_oracle_actor_inputs": _bool(row.get("uses_hidden_oracle_actor_inputs")),
        "uses_wheel_or_slip_inputs": _bool(row.get("uses_wheel_or_slip_inputs")),
        "uses_reference_or_ttc_inputs": _bool(row.get("uses_reference_or_ttc_inputs")),
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _rate(numerator: int, denominator: int) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _failure_aggregates(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    by_profile: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "profile_metric_row_count": 0,
            "diagnostic_episode_count": 0,
            "diagnostic_success_count": 0,
            "diagnostic_collision_count": 0,
            "diagnostic_offtrack_count": 0,
            "failure_mode_counts": Counter(),
        }
    )
    for row in rows:
        profile = str(row.get("group_name", ""))
        if not profile:
            continue
        item = by_profile[profile]
        item["profile_metric_row_count"] += 1
        item["diagnostic_episode_count"] += int(_int_or_none(row.get("episode_count")) or 0)
        item["diagnostic_success_count"] += int(_int_or_none(row.get("success_count")) or 0)
        item["diagnostic_collision_count"] += int(_int_or_none(row.get("collision_count")) or 0)
        item["diagnostic_offtrack_count"] += int(_int_or_none(row.get("offtrack_count")) or 0)
        item["failure_mode_counts"][str(row.get("failure_mode_label", ""))] += 1
    output: dict[str, dict[str, Any]] = {}
    for profile, item in by_profile.items():
        total = int(item["diagnostic_episode_count"])
        success = int(item["diagnostic_success_count"])
        collision = int(item["diagnostic_collision_count"])
        offtrack = int(item["diagnostic_offtrack_count"])
        output[profile] = {
            **item,
            "failure_mode_counts": ";".join(
                f"{key}:{value}" for key, value in sorted(item["failure_mode_counts"].items()) if key
            ),
            "diagnostic_success_rate": _rate(success, total),
            "diagnostic_collision_rate": _rate(collision, total),
            "diagnostic_offtrack_rate": _rate(offtrack, total),
        }
    return output


def _join_rows(quality_rows: list[Mapping[str, Any]], failure_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    failures = _failure_aggregates(failure_rows)
    output: list[dict[str, Any]] = []
    for quality in quality_rows:
        profile = str(quality["profile_name"])
        failure = failures.get(profile, {})
        output.append(
            {
                "profile_name": profile,
                "profile_metric_row_count": int(failure.get("profile_metric_row_count", 0)),
                "diagnostic_episode_count": int(failure.get("diagnostic_episode_count", 0)),
                "diagnostic_success_count": int(failure.get("diagnostic_success_count", 0)),
                "diagnostic_collision_count": int(failure.get("diagnostic_collision_count", 0)),
                "diagnostic_offtrack_count": int(failure.get("diagnostic_offtrack_count", 0)),
                "diagnostic_success_rate": float(failure.get("diagnostic_success_rate", 0.0)),
                "diagnostic_collision_rate": float(failure.get("diagnostic_collision_rate", 0.0)),
                "diagnostic_offtrack_rate": float(failure.get("diagnostic_offtrack_rate", 0.0)),
                "failure_mode_counts": failure.get("failure_mode_counts", ""),
                "total_train_steps": quality.get("total_train_steps"),
                "eval_return_mean": quality.get("eval_return_mean"),
                "eval_termination_rate": quality.get("eval_termination_rate"),
                "eval_lateral_rmse_mean": quality.get("eval_lateral_rmse_mean"),
                "final_train_termination_rate": quality.get("final_train_termination_rate"),
                "smoke_scale_training": quality.get("smoke_scale_training"),
                "weak_eval_flag": quality.get("weak_eval_flag"),
                "weak_train_flag": quality.get("weak_train_flag"),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "finite_window_vs_gru_conclusion_made": False,
            }
        )
    return output


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {"claim": "checkpoint_quality_failure_metric_audit", "admissible": True, "reason": "M2224 uses existing train/eval/failure artifacts"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "M2224 forces ranking_admissible false"},
        {"claim": "winner_selection", "admissible": False, "reason": "M2224 does not select a profile"},
        {"claim": "finite_window_vs_gru_conclusion", "admissible": False, "reason": "M2224 is diagnostic only"},
        {"claim": "paper_level_benchmark_result", "admissible": False, "reason": "M2224 is no-rerun artifact-quality evidence"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2224 runs no history intervention"},
    ]


def _by_profile(rows: list[Mapping[str, Any]], profile: str) -> Mapping[str, Any]:
    for row in rows:
        if str(row.get("profile_name", "")) == profile:
            return row
    return {}


def run_checkpoint_quality_audit(
    *,
    checkpoint_materialization_dir: Path | str = DEFAULT_CHECKPOINT_MATERIALIZATION_DIR,
    failure_metrics: Path | str = DEFAULT_FAILURE_METRICS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    materialization = Path(checkpoint_materialization_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    profile_rows = read_csv_rows(materialization / PROFILE_ROWS)
    failure_rows = read_csv_rows(failure_metrics)
    quality_rows = [_quality_row(materialization, row) for row in profile_rows]
    join_rows = _join_rows(quality_rows, failure_rows)
    l3_online_quality = _by_profile(quality_rows, "L3_online_gru")
    l3_reset_quality = _by_profile(quality_rows, "L3_reset_control")
    l3_online_join = _by_profile(join_rows, "L3_online_gru")
    l3_reset_join = _by_profile(join_rows, "L3_reset_control")
    l2_25_join = _by_profile(join_rows, "L2_window_25")
    l3_weak_checkpoint_plausible = bool(
        l3_online_join
        and int(l3_online_join.get("diagnostic_success_count", 0)) == 0
        and (_bool(l3_online_quality.get("weak_eval_flag")) or _bool(l3_online_quality.get("weak_train_flag")))
    )
    matched_budget_training_needed = bool(
        l3_weak_checkpoint_plausible
        and l2_25_join
        and int(l2_25_join.get("diagnostic_success_count", 0)) > 0
    )
    ranking_admissible_count = 0
    winner_selected = False
    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": winner_selected,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    result_class = (
        "current_sim_recurrent_profile_checkpoint_quality_audit_pass"
        if profile_rows and quality_rows and join_rows and guardrail_violation_count == 0
        else "current_sim_recurrent_profile_checkpoint_quality_audit_fail"
    )

    write_csv_rows(output / "checkpoint_quality_summary.csv", quality_rows, fieldnames=QUALITY_FIELDNAMES)
    write_csv_rows(output / "profile_failure_quality_join.csv", join_rows, fieldnames=JOIN_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "checkpoint_materialization_dir": str(checkpoint_materialization_dir),
        "failure_metrics": str(failure_metrics),
        "profile_count": len(quality_rows),
        "join_row_count": len(join_rows),
        "l3_online_total_train_steps": l3_online_quality.get("total_train_steps"),
        "l3_online_eval_return_mean": l3_online_quality.get("eval_return_mean"),
        "l3_online_eval_termination_rate": l3_online_quality.get("eval_termination_rate"),
        "l3_online_eval_lateral_rmse_mean": l3_online_quality.get("eval_lateral_rmse_mean"),
        "l3_online_final_train_termination_rate": l3_online_quality.get("final_train_termination_rate"),
        "l3_online_weak_eval_flag": l3_online_quality.get("weak_eval_flag"),
        "l3_online_weak_train_flag": l3_online_quality.get("weak_train_flag"),
        "l3_online_diagnostic_success_count": l3_online_join.get("diagnostic_success_count", 0),
        "l3_reset_checkpoint_source_profile_name": l3_reset_quality.get("checkpoint_source_profile_name"),
        "l3_reset_aliases_online_checkpoint": bool(
            l3_reset_quality
            and l3_online_quality
            and l3_reset_quality.get("checkpoint_path") == l3_online_quality.get("checkpoint_path")
        ),
        "l3_reset_diagnostic_success_count": l3_reset_join.get("diagnostic_success_count", 0),
        "l2_window_25_diagnostic_success_count": l2_25_join.get("diagnostic_success_count", 0),
        "l3_weak_checkpoint_plausible": l3_weak_checkpoint_plausible,
        "matched_budget_training_needed": matched_budget_training_needed,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected": winner_selected,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "checkpoint_quality_summary": str(output / "checkpoint_quality_summary.csv"),
            "profile_failure_quality_join": str(output / "profile_failure_quality_join.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2224-paper-route-current-sim-recurrent-profile-checkpoint-quality-audit",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-materialization-dir", type=Path, default=DEFAULT_CHECKPOINT_MATERIALIZATION_DIR)
    parser.add_argument("--failure-metrics", type=Path, default=DEFAULT_FAILURE_METRICS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_checkpoint_quality_audit(
        checkpoint_materialization_dir=args.checkpoint_materialization_dir,
        failure_metrics=args.failure_metrics,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"profile_count={summary['profile_count']}")
    print(f"l3_online_diagnostic_success_count={summary['l3_online_diagnostic_success_count']}")
    print(f"l3_weak_checkpoint_plausible={summary['l3_weak_checkpoint_plausible']}")
    print(f"matched_budget_training_needed={summary['matched_budget_training_needed']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
