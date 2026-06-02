"""Reset-only validation adapter for effective candidate pack artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv


DEFAULT_SOURCE_DIR = Path("runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization")
DEFAULT_OUTPUT_DIR = Path("runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter")
DEFAULT_TARGET_CANDIDATE_CONFIG_COUNT = 54
DEFAULT_TARGET_CANDIDATE_SCENARIO_REFERENCE_COUNT = 2049
DEFAULT_TARGET_UNIQUE_RESET_TARGET_COUNT = 350
DEFAULT_EVAL_SEED_BASE = 239400
DEFAULT_NEXT_BLOCKER = "m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit"
RESULT_PASS = "current_sim_dual_axis_effective_candidate_reset_validation_adapter_pass"
RESULT_FAIL = "current_sim_dual_axis_effective_candidate_reset_validation_adapter_fail"
ACTOR_CONTRACT_ID = "P0_human_view_no_wheel_no_oracle"

STATIC_FIELDNAMES = [
    "candidate_id",
    "pack_id",
    "scenario_spec_id",
    "reset_target_key",
    "env_config_present",
    "actor_contract_guardrail_pass",
    "claim_boundary_forbids_execution",
    "static_validation_pass",
    "failure_reasons",
]
RESET_TARGET_FIELDNAMES = [
    "reset_target_key",
    "pack_id",
    "scenario_spec_id",
    "env_config_hash",
    "reference_count",
    "candidate_ids",
    "source_slice_axes",
    "scenario_family_id",
    "role_family",
]
RESET_FIELDNAMES = [
    "reset_target_key",
    "pack_id",
    "scenario_spec_id",
    "environment_load_attempted",
    "environment_reset_attempted",
    "environment_reset_success",
    "observation_length",
    "observation_finite",
    "environment_step_count",
    "policy_action_executed",
    "failure_reason",
]
CANDIDATE_SCENARIO_FIELDNAMES = [
    "candidate_id",
    "pack_id",
    "scenario_spec_id",
    "reset_target_key",
    "environment_reset_success",
    "candidate_scenario_reset_pass",
    "failure_reason",
]
CANDIDATE_SUMMARY_FIELDNAMES = [
    "candidate_id",
    "selected_scenario_reference_count",
    "unique_reset_target_count",
    "candidate_reset_pass",
    "candidate_reset_failure_count",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _json_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _reset_target_key(pack_id: str, scenario_spec_id: str) -> str:
    return f"{pack_id}|{scenario_spec_id}"


def _observation_length(obs: Any) -> int:
    array = np.asarray(obs, dtype=np.float64)
    if array.ndim == 0:
        return 0
    return int(array.size)


def _finite_observation(obs: Any) -> bool:
    try:
        array = np.asarray(obs, dtype=np.float64)
    except (TypeError, ValueError):
        return False
    return bool(array.size > 0 and np.all(np.isfinite(array)))


def _env_config(selected: Mapping[str, Any]) -> Mapping[str, Any] | None:
    env_config = selected.get("env_config")
    return env_config if isinstance(env_config, Mapping) else None


def _actor_contract_pass(selected: Mapping[str, Any]) -> bool:
    env_config = _env_config(selected)
    if env_config is None:
        return False
    return (
        str(selected.get("actor_contract_id", "")) == ACTOR_CONTRACT_ID
        and not _bool(env_config.get("include_privileged_params"))
        and str(env_config.get("wheel_observation_mode", "")) == "none"
        and str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero"
        and int(env_config.get("history_length", -1)) == 1
    )


def _claim_boundary_forbids_execution(payload: Mapping[str, Any]) -> bool:
    boundary = payload.get("claim_boundary")
    if not isinstance(boundary, Mapping):
        return False
    forbidden_true_keys = [
        "active_config_overwritten",
        "environment_step_count",
        "policy_action_executed",
        "rollout_started",
        "repair_execution_started",
        "training_started",
        "ranking_admissible",
        "winner_selected",
    ]
    return not any(_bool(boundary.get(key)) for key in forbidden_true_keys)


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "effective_candidate_reset_only_validation",
            "admissible": True,
            "reason": "M2394 may claim reset-only validation if reset gates pass",
        },
        {
            "claim": "environment_step_or_policy_action",
            "admissible": False,
            "reason": "M2394 must stop immediately after reset",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "M2394 does not roll out a policy",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2394 does not execute repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2394 does not train or evaluate a repaired driver",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "reset validation is an admissibility gate, not ranking",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2394 is a reset preflight, not paper-level evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2394 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2394 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2394 does not run measured validation needed for a verdict",
        },
    ]


def load_effective_candidates(source_dir: Path) -> list[dict[str, Any]]:
    rows = read_csv_rows(source_dir / "effective_candidate_config_rows.csv")
    candidates: list[dict[str, Any]] = []
    for row in rows:
        path = Path(str(row.get("effective_candidate_config_path", "")))
        payload = read_json(path)
        candidates.append({"row": row, "path": path, "payload": payload})
    return candidates


def build_static_and_targets(
    *, source_dir: Path, candidates: Sequence[Mapping[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Mapping[str, Any]]]:
    static_rows: list[dict[str, Any]] = []
    target_refs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    target_env_configs: dict[str, Mapping[str, Any]] = {}
    target_hashes: dict[str, str] = {}

    for candidate in candidates:
        path = Path(str(candidate.get("path", "")))
        payload = dict(candidate.get("payload", {}))
        candidate_id = str(payload.get("candidate_id", ""))
        claim_boundary_ok = _claim_boundary_forbids_execution(payload)
        path_inside = _inside_dir(path, source_dir)
        for selected in payload.get("selected_scenario_specs", []):
            pack_id = str(selected.get("pack_id", ""))
            scenario_spec_id = str(selected.get("scenario_spec_id", ""))
            key = _reset_target_key(pack_id, scenario_spec_id)
            env_config = _env_config(selected)
            env_hash = _json_hash(dict(env_config or {})) if env_config else ""
            failures: list[str] = []
            if not path_inside:
                failures.append("effective_candidate_config_path_outside_source_dir")
            if not env_config:
                failures.append("missing_env_config")
            if not _actor_contract_pass(selected):
                failures.append("actor_contract_guardrail_violation")
            if not claim_boundary_ok:
                failures.append("claim_boundary_allows_forbidden_execution")
            if key in target_hashes and env_hash and target_hashes[key] != env_hash:
                failures.append("duplicate_target_env_config_hash_mismatch")
            if env_config and key not in target_env_configs:
                target_env_configs[key] = dict(env_config)
                target_hashes[key] = env_hash
            ref = {
                "candidate_id": candidate_id,
                "pack_id": pack_id,
                "scenario_spec_id": scenario_spec_id,
                "reset_target_key": key,
                "env_config_hash": env_hash,
                "source_slice_axis": str(payload.get("source_slice_axis", "")),
                "scenario_family_id": str(selected.get("scenario_family_id", "")),
                "role_family": str(selected.get("role_family", "")),
            }
            target_refs[key].append(ref)
            static_rows.append(
                {
                    "candidate_id": candidate_id,
                    "pack_id": pack_id,
                    "scenario_spec_id": scenario_spec_id,
                    "reset_target_key": key,
                    "env_config_present": bool(env_config),
                    "actor_contract_guardrail_pass": _actor_contract_pass(selected),
                    "claim_boundary_forbids_execution": claim_boundary_ok,
                    "static_validation_pass": not failures,
                    "failure_reasons": ";".join(failures),
                }
            )

    target_rows: list[dict[str, Any]] = []
    for key, refs in sorted(target_refs.items()):
        first = refs[0]
        target_rows.append(
            {
                "reset_target_key": key,
                "pack_id": str(first.get("pack_id", "")),
                "scenario_spec_id": str(first.get("scenario_spec_id", "")),
                "env_config_hash": str(first.get("env_config_hash", "")),
                "reference_count": len(refs),
                "candidate_ids": "|".join(sorted({str(ref.get("candidate_id", "")) for ref in refs})),
                "source_slice_axes": "|".join(sorted({str(ref.get("source_slice_axis", "")) for ref in refs})),
                "scenario_family_id": str(first.get("scenario_family_id", "")),
                "role_family": str(first.get("role_family", "")),
            }
        )
    return static_rows, target_rows, target_env_configs


def reset_target(*, target_row: Mapping[str, Any], env_config: Mapping[str, Any], eval_seed: int) -> dict[str, Any]:
    key = str(target_row.get("reset_target_key", ""))
    try:
        config = build_env_config(dict(env_config))
        env = AutoDriftEnv(config)
        try:
            obs, _info = env.reset(seed=int(eval_seed))
        finally:
            close = getattr(env, "close", None)
            if callable(close):
                close()
        return {
            "reset_target_key": key,
            "pack_id": str(target_row.get("pack_id", "")),
            "scenario_spec_id": str(target_row.get("scenario_spec_id", "")),
            "environment_load_attempted": True,
            "environment_reset_attempted": True,
            "environment_reset_success": True,
            "observation_length": _observation_length(obs),
            "observation_finite": _finite_observation(obs),
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": "",
        }
    except Exception as exc:  # noqa: BLE001 - reset preflight records exact failure text.
        return {
            "reset_target_key": key,
            "pack_id": str(target_row.get("pack_id", "")),
            "scenario_spec_id": str(target_row.get("scenario_spec_id", "")),
            "environment_load_attempted": True,
            "environment_reset_attempted": True,
            "environment_reset_success": False,
            "observation_length": 0,
            "observation_finite": False,
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": str(exc),
        }


def map_candidate_results(
    *,
    static_rows: Sequence[Mapping[str, Any]],
    reset_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reset_by_key = {str(row.get("reset_target_key", "")): row for row in reset_rows}
    candidate_scenario_rows: list[dict[str, Any]] = []
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in static_rows:
        key = str(row.get("reset_target_key", ""))
        reset_row = reset_by_key.get(key, {})
        reset_success = _bool(reset_row.get("environment_reset_success")) and _bool(row.get("static_validation_pass"))
        mapped = {
            "candidate_id": str(row.get("candidate_id", "")),
            "pack_id": str(row.get("pack_id", "")),
            "scenario_spec_id": str(row.get("scenario_spec_id", "")),
            "reset_target_key": key,
            "environment_reset_success": _bool(reset_row.get("environment_reset_success")),
            "candidate_scenario_reset_pass": reset_success,
            "failure_reason": str(row.get("failure_reasons", "") or reset_row.get("failure_reason", "")),
        }
        candidate_scenario_rows.append(mapped)
        by_candidate[str(row.get("candidate_id", ""))].append(mapped)

    candidate_summary_rows: list[dict[str, Any]] = []
    for candidate_id, rows in sorted(by_candidate.items()):
        failure_count = sum(not _bool(row.get("candidate_scenario_reset_pass")) for row in rows)
        candidate_summary_rows.append(
            {
                "candidate_id": candidate_id,
                "selected_scenario_reference_count": len(rows),
                "unique_reset_target_count": len({str(row.get("reset_target_key", "")) for row in rows}),
                "candidate_reset_pass": failure_count == 0,
                "candidate_reset_failure_count": failure_count,
            }
        )
    return candidate_scenario_rows, candidate_summary_rows


def run_effective_candidate_reset_validation_adapter(
    *,
    source_dir: Path | str = DEFAULT_SOURCE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_candidate_config_count: int = DEFAULT_TARGET_CANDIDATE_CONFIG_COUNT,
    target_candidate_scenario_reference_count: int = DEFAULT_TARGET_CANDIDATE_SCENARIO_REFERENCE_COUNT,
    target_unique_reset_target_count: int = DEFAULT_TARGET_UNIQUE_RESET_TARGET_COUNT,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(source_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(source / "summary.json")
    source_scenario_rows = read_csv_rows(source / "effective_candidate_scenario_rows.csv")
    candidates = load_effective_candidates(source)
    static_rows, target_rows, target_env_configs = build_static_and_targets(source_dir=source, candidates=candidates)
    static_pass_count = sum(_bool(row.get("static_validation_pass")) for row in static_rows)
    static_failure_count = len(static_rows) - static_pass_count
    reset_rows: list[dict[str, Any]] = []
    if static_failure_count == 0:
        for index, target_row in enumerate(target_rows):
            env_config = target_env_configs.get(str(target_row.get("reset_target_key", "")), {})
            reset_rows.append(reset_target(target_row=target_row, env_config=env_config, eval_seed=int(eval_seed_base) + index))
    candidate_scenario_rows, candidate_summary_rows = map_candidate_results(
        static_rows=static_rows,
        reset_rows=reset_rows,
    )
    reset_failure_rows = [row for row in reset_rows if not _bool(row.get("environment_reset_success"))]
    claim_rows = claim_boundary_rows()

    source_candidate_count = len(candidates)
    candidate_scenario_reference_count = len(static_rows)
    unique_reset_target_count = len(target_rows)
    environment_load_attempt_count = sum(_bool(row.get("environment_load_attempted")) for row in reset_rows)
    environment_reset_attempt_count = sum(_bool(row.get("environment_reset_attempted")) for row in reset_rows)
    environment_reset_success_count = sum(_bool(row.get("environment_reset_success")) for row in reset_rows)
    environment_reset_failure_count = len(reset_failure_rows)
    environment_step_count = sum(int(row.get("environment_step_count", 0)) for row in reset_rows)
    policy_action_executed = any(_bool(row.get("policy_action_executed")) for row in reset_rows)
    candidate_reset_pass_count = sum(_bool(row.get("candidate_reset_pass")) for row in candidate_summary_rows)
    candidate_reset_failure_count = source_candidate_count - candidate_reset_pass_count
    active_config_overwrite_count = 0
    guardrail_flags = {
        "environment_rollout_started": False,
        "policy_action_executed": policy_action_executed,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    failure_types_observed = [
        name
        for name, count in [
            ("static_schema_failure", static_failure_count),
            ("scenario_sampling_failure", environment_reset_failure_count),
            ("forbidden_execution_failure", environment_step_count + int(policy_action_executed)),
        ]
        if count
    ]
    passes = (
        source_summary.get("result_class")
        == "current_sim_dual_axis_effective_config_schema_repair_materialization_pass"
        and source_candidate_count == int(target_candidate_config_count)
        and len(source_scenario_rows) == int(target_candidate_scenario_reference_count)
        and candidate_scenario_reference_count == int(target_candidate_scenario_reference_count)
        and unique_reset_target_count == int(target_unique_reset_target_count)
        and static_pass_count == int(target_candidate_scenario_reference_count)
        and static_failure_count == 0
        and environment_load_attempt_count == int(target_unique_reset_target_count)
        and environment_reset_attempt_count == int(target_unique_reset_target_count)
        and environment_reset_success_count == int(target_unique_reset_target_count)
        and environment_reset_failure_count == 0
        and candidate_reset_pass_count == int(target_candidate_config_count)
        and candidate_reset_failure_count == 0
        and environment_step_count == 0
        and not policy_action_executed
        and active_config_overwrite_count == 0
        and guardrail_violation_count == 0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL

    write_csv_rows(output / "static_validation_rows.csv", static_rows, fieldnames=STATIC_FIELDNAMES)
    write_csv_rows(output / "reset_target_rows.csv", target_rows, fieldnames=RESET_TARGET_FIELDNAMES)
    write_csv_rows(output / "reset_validation_rows.csv", reset_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "candidate_scenario_reset_rows.csv", candidate_scenario_rows, fieldnames=CANDIDATE_SCENARIO_FIELDNAMES)
    write_csv_rows(output / "effective_candidate_reset_summary_rows.csv", candidate_summary_rows, fieldnames=CANDIDATE_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", reset_failure_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "source_dir": str(source),
        "output_dir": str(output),
        "source_result_class": source_summary.get("result_class", ""),
        "source_candidate_config_count": source_candidate_count,
        "target_candidate_config_count": int(target_candidate_config_count),
        "source_effective_candidate_scenario_row_count": len(source_scenario_rows),
        "candidate_scenario_reference_count": candidate_scenario_reference_count,
        "target_candidate_scenario_reference_count": int(target_candidate_scenario_reference_count),
        "unique_reset_target_count": unique_reset_target_count,
        "target_unique_reset_target_count": int(target_unique_reset_target_count),
        "static_validation_pass_count": static_pass_count,
        "static_validation_failure_count": static_failure_count,
        "environment_load_attempt_count": environment_load_attempt_count,
        "environment_reset_attempt_count": environment_reset_attempt_count,
        "environment_reset_success_count": environment_reset_success_count,
        "environment_reset_failure_count": environment_reset_failure_count,
        "candidate_reset_pass_count": candidate_reset_pass_count,
        "candidate_reset_failure_count": candidate_reset_failure_count,
        "environment_reset_started": environment_reset_attempt_count > 0,
        "environment_step_count": environment_step_count,
        "policy_action_executed": policy_action_executed,
        "active_config_overwrite_count": active_config_overwrite_count,
        "active_config_overwritten": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "ranking_admissible_count": 0,
        "winner_selected_count": 0,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types_observed,
        "reset_target_counts_by_pack": _count_by(target_rows, "pack_id"),
        "candidate_reset_failure_rows": candidate_reset_failure_count,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "static_validation_rows": str(output / "static_validation_rows.csv"),
            "reset_target_rows": str(output / "reset_target_rows.csv"),
            "reset_validation_rows": str(output / "reset_validation_rows.csv"),
            "candidate_scenario_reset_rows": str(output / "candidate_scenario_reset_rows.csv"),
            "effective_candidate_reset_summary_rows": str(output / "effective_candidate_reset_summary_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-candidate-config-count", type=int, default=DEFAULT_TARGET_CANDIDATE_CONFIG_COUNT)
    parser.add_argument(
        "--target-candidate-scenario-reference-count",
        type=int,
        default=DEFAULT_TARGET_CANDIDATE_SCENARIO_REFERENCE_COUNT,
    )
    parser.add_argument("--target-unique-reset-target-count", type=int, default=DEFAULT_TARGET_UNIQUE_RESET_TARGET_COUNT)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_effective_candidate_reset_validation_adapter(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        target_candidate_config_count=int(args.target_candidate_config_count),
        target_candidate_scenario_reference_count=int(args.target_candidate_scenario_reference_count),
        target_unique_reset_target_count=int(args.target_unique_reset_target_count),
        eval_seed_base=int(args.eval_seed_base),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_candidate_config_count={summary['source_candidate_config_count']}")
    print(f"candidate_scenario_reference_count={summary['candidate_scenario_reference_count']}")
    print(f"unique_reset_target_count={summary['unique_reset_target_count']}")
    print(f"environment_reset_attempt_count={summary['environment_reset_attempt_count']}")
    print(f"environment_reset_success_count={summary['environment_reset_success_count']}")
    print(f"candidate_reset_pass_count={summary['candidate_reset_pass_count']}")
    print(f"environment_step_count={summary['environment_step_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
