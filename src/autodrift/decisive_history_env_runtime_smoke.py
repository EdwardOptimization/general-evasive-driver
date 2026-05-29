"""Reset-only runtime smoke for decisive-history env-hook specs."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.decisive_history_env_hooks import DecisiveHistoryEnvHookSpec, default_hook_specs
from autodrift.env import AutoDriftEnv


@dataclass(frozen=True)
class RuntimeSmokeRow:
    """One reset-only runtime result."""

    source_family: str
    task_family: str
    seed: int
    candidate_id: str
    reset_success: bool
    failure_type: str
    error_type: str
    error_message: str
    observation_dim: int
    expected_observation_dim: int
    obstacle_enabled: bool
    obstacle_label: str
    obstacle_perception_visible: bool
    warmup_gate_enabled: bool
    warmup_gate_visible: bool
    friction_step_enabled: bool
    friction_step_at: int | None
    actor_input_contract_changed: bool = False
    labels_enter_actor_input: bool = False
    candidate_materialized: bool = False
    policy_replay_started: bool = False
    replay_started: bool = False
    training_started: bool = False
    ppo_used: bool = False
    promoted: bool = False
    private_holdout_used: bool = False
    training_corpus_exported: bool = False
    level3_self_id_claim_made: bool = False


def _failure_type(exc: BaseException) -> str:
    message = str(exc)
    if "failed to sample an obstacle scenario" in message:
        return "scenario_sampling_failure"
    if "privileged" in message or "actor" in message:
        return "contract_violation"
    return "training_instability"


def reset_hook_spec(spec: DecisiveHistoryEnvHookSpec) -> RuntimeSmokeRow:
    """Instantiate env and call reset only. No step, policy, replay, or training."""

    try:
        env = AutoDriftEnv(spec.env_config)
        observation, info = env.reset(seed=int(spec.seed))
    except Exception as exc:  # pragma: no cover - covered through failure classification tests.
        return RuntimeSmokeRow(
            source_family=spec.source_family,
            task_family=spec.task_family,
            seed=spec.seed,
            candidate_id=spec.candidate_id,
            reset_success=False,
            failure_type=_failure_type(exc),
            error_type=type(exc).__name__,
            error_message=str(exc),
            observation_dim=0,
            expected_observation_dim=0,
            obstacle_enabled=spec.env_config.obstacle.enabled,
            obstacle_label="",
            obstacle_perception_visible=False,
            warmup_gate_enabled=spec.env_config.warmup_gate.enabled,
            warmup_gate_visible=False,
            friction_step_enabled=spec.env_config.friction_step.enabled,
            friction_step_at=None,
        )
    return RuntimeSmokeRow(
        source_family=spec.source_family,
        task_family=spec.task_family,
        seed=spec.seed,
        candidate_id=spec.candidate_id,
        reset_success=True,
        failure_type="none",
        error_type="",
        error_message="",
        observation_dim=int(observation.shape[0]),
        expected_observation_dim=int(env.observation_space.shape[0]),
        obstacle_enabled=bool(info.get("obstacle_enabled", False)),
        obstacle_label=str(info.get("obstacle_label", "")),
        obstacle_perception_visible=bool(info.get("obstacle_perception_visible", False)),
        warmup_gate_enabled=bool(info.get("warmup_gate_enabled", False)),
        warmup_gate_visible=bool(info.get("warmup_gate_visible", False)),
        friction_step_enabled=bool(spec.env_config.friction_step.enabled),
        friction_step_at=info.get("friction_step_at"),
    )


def _row_dict(row: RuntimeSmokeRow) -> dict[str, Any]:
    return dict(row.__dict__)


def _source_family_summary(rows: Sequence[RuntimeSmokeRow]) -> list[dict[str, Any]]:
    by_family: dict[str, list[RuntimeSmokeRow]] = {}
    for row in rows:
        by_family.setdefault(row.source_family, []).append(row)
    summary_rows: list[dict[str, Any]] = []
    for family, family_rows in sorted(by_family.items()):
        failures = [row for row in family_rows if not row.reset_success]
        failure_counts = Counter(row.failure_type for row in failures)
        summary_rows.append(
            {
                "source_family": family,
                "rows": len(family_rows),
                "reset_success_count": sum(1 for row in family_rows if row.reset_success),
                "reset_failure_count": len(failures),
                "failure_types": "|".join(sorted(failure_counts)) if failure_counts else "none",
                "task_family": family_rows[0].task_family if family_rows else "",
                "unique_seeds": len({row.seed for row in family_rows}),
                "obstacle_labels": "|".join(sorted({row.obstacle_label for row in family_rows if row.obstacle_label})),
            }
        )
    return summary_rows


def _guardrail_rows(rows: Sequence[RuntimeSmokeRow]) -> list[dict[str, Any]]:
    checks = {
        "actor_input_contract_changed": any(row.actor_input_contract_changed for row in rows),
        "labels_enter_actor_input": any(row.labels_enter_actor_input for row in rows),
        "candidate_materialized": any(row.candidate_materialized for row in rows),
        "policy_replay_started": any(row.policy_replay_started for row in rows),
        "replay_started": any(row.replay_started for row in rows),
        "training_started": any(row.training_started for row in rows),
        "ppo_used": any(row.ppo_used for row in rows),
        "promoted": any(row.promoted for row in rows),
        "private_holdout_used": any(row.private_holdout_used for row in rows),
        "training_corpus_exported": any(row.training_corpus_exported for row in rows),
        "level3_self_id_claim_made": any(row.level3_self_id_claim_made for row in rows),
    }
    return [{"guardrail": key, "violated": bool(value)} for key, value in sorted(checks.items())]


def build_runtime_smoke_summary(rows: Sequence[RuntimeSmokeRow]) -> dict[str, Any]:
    """Summarize reset-only runtime smoke rows."""

    row_list = list(rows)
    guardrails = _guardrail_rows(row_list)
    failures = [row for row in row_list if not row.reset_success]
    return {
        "result_class": "decisive_history_env_hook_runtime_smoke",
        "runtime_scope": "reset_only",
        "hook_spec_count": len(row_list),
        "source_family_count": len({row.source_family for row in row_list}),
        "reset_success_count": sum(1 for row in row_list if row.reset_success),
        "reset_failure_count": len(failures),
        "failure_type_counts": dict(sorted(Counter(row.failure_type for row in failures).items())),
        "source_families_with_reset_success": sorted({row.source_family for row in row_list if row.reset_success}),
        "all_source_families_reset": len({row.source_family for row in row_list if row.reset_success}) == 6,
        "guardrail_violation_count": sum(1 for row in guardrails if row["violated"]),
        "env_reset_called": True,
        "env_step_called": False,
        "candidate_materialized": any(row.candidate_materialized for row in row_list),
        "policy_replay_started": any(row.policy_replay_started for row in row_list),
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


def run_env_hook_runtime_smoke(run_dir: Path | str, *, seed_count: int = 1) -> dict[str, Any]:
    """Run reset-only current-sim smoke for hook specs."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = default_hook_specs(seed_count=seed_count)
    rows = [reset_hook_spec(spec) for spec in specs]
    summary = build_runtime_smoke_summary(rows)
    write_csv_rows(output / "runtime_rows.csv", [_row_dict(row) for row in rows])
    write_csv_rows(output / "runtime_source_family_summary.csv", _source_family_summary(rows))
    write_csv_rows(output / "runtime_guardrail_summary.csv", _guardrail_rows(rows))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reset-only decisive-history env-hook runtime smoke.")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/m1506_decisive_history_env_hook_runtime_smoke"))
    parser.add_argument("--seed-count", type=int, default=1)
    args = parser.parse_args()
    summary = run_env_hook_runtime_smoke(args.run_dir, seed_count=int(args.seed_count))
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"reset_success_count={summary['reset_success_count']}")
    print(f"reset_failure_count={summary['reset_failure_count']}")


if __name__ == "__main__":
    main()
