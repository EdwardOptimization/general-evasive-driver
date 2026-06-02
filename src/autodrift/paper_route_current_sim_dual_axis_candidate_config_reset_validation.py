"""Static safety and reset-only validation for generated candidate configs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv


DEFAULT_SOURCE_DIR = Path("runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation")
DEFAULT_OUTPUT_DIR = Path("runs/m2388_paper_route_current_sim_dual_axis_candidate_config_reset_validation")
DEFAULT_TARGET_CANDIDATE_CONFIG_COUNT = 54
DEFAULT_EVAL_SEED_BASE = 238800
DEFAULT_NEXT_BLOCKER = "m2389-paper-route-current-sim-dual-axis-candidate-config-reset-validation-result-audit"
RESULT_PASS = "current_sim_dual_axis_candidate_config_reset_validation_pass"
RESULT_FAIL = "current_sim_dual_axis_candidate_config_reset_validation_fail"

STATIC_FIELDNAMES = [
    "candidate_id",
    "candidate_config_path",
    "path_exists",
    "inside_source_run_dir",
    "payload_candidate_id_matches",
    "matrix_candidate_id_present",
    "guardrail_candidate_id_present",
    "source_repair_spec_id_non_empty",
    "repair_family_non_empty",
    "reward_overlay_count",
    "curriculum_overlay_count",
    "guardrail_scope_id",
    "guardrail_patch_count",
    "mixed_collision_guardrail_required_matches",
    "claim_boundary_forbids_execution",
    "static_validation_pass",
    "failure_reasons",
]
EFFECTIVE_FIELDNAMES = [
    "candidate_id",
    "candidate_config_path",
    "effective_config_path",
    "effective_config_written",
    "effective_config_inside_run_dir",
    "schema_incomplete",
    "active_config_overwritten",
    "failure_reasons",
]
RESET_FIELDNAMES = [
    "candidate_id",
    "effective_config_path",
    "environment_load_attempted",
    "environment_reset_attempted",
    "environment_reset_success",
    "observation_length",
    "observation_finite",
    "environment_step_count",
    "policy_action_executed",
    "failure_reason",
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


def _int_value(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


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


def _claim_boundary_forbids_execution(payload: Mapping[str, Any]) -> bool:
    boundary = payload.get("claim_boundary")
    if not isinstance(boundary, Mapping):
        return False
    forbidden_true_keys = [
        "active_config_overwritten",
        "loaded_into_environment",
        "environment_reset_started",
        "repair_execution_started",
        "training_started",
        "ranking_admissible",
        "winner_selected",
    ]
    return not any(_bool(boundary.get(key)) for key in forbidden_true_keys)


def _candidate_json_path(row: Mapping[str, Any]) -> Path:
    return Path(str(row.get("candidate_config_path", "")))


def _effective_config_path(output_dir: Path, candidate_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in candidate_id).strip("_")
    return output_dir / "effective_configs" / f"{safe}.json"


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "candidate_config_static_safety_validation",
            "admissible": True,
            "reason": "M2388 may claim static safety validation if static gates pass",
        },
        {
            "claim": "candidate_config_reset_only_validation",
            "admissible": True,
            "reason": "M2388 may claim reset-only validation only if reset gates pass",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "M2388 does not step the environment or execute policy actions",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2388 does not execute repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2388 does not train or evaluate a repaired driver",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "reset validation is a scenario admissibility gate, not ranking",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2388 is a reset preflight, not paper-level evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2388 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2388 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2388 does not run measured validation needed for a verdict",
        },
    ]


def static_validation_row(
    *,
    source_dir: Path,
    candidate_row: Mapping[str, Any],
    matrix_by_candidate: Mapping[str, Mapping[str, Any]],
    guardrail_by_candidate: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    candidate_id = str(candidate_row.get("candidate_id", ""))
    path = _candidate_json_path(candidate_row)
    failures: list[str] = []
    path_exists = path.exists()
    inside = path_exists and _inside_dir(path, source_dir)
    payload: dict[str, Any] | None = None
    if path_exists:
        payload = dict(read_json(path))
    else:
        failures.append("missing_candidate_config")

    payload_candidate_id_matches = bool(payload and str(payload.get("candidate_id", "")) == candidate_id)
    matrix_present = candidate_id in matrix_by_candidate
    guardrail_present = candidate_id in guardrail_by_candidate
    source_repair_non_empty = bool(payload and str(payload.get("source_repair_spec_id", "")).strip())
    repair_family_non_empty = bool(payload and str(payload.get("repair_family", "")).strip())
    reward_count = len(payload.get("reward_overlay", [])) if payload else 0
    curriculum_count = len(payload.get("curriculum_overlay", [])) if payload else 0
    guardrail_overlay = payload.get("guardrail_overlay", {}) if payload else {}
    guardrail_scope_id = str(guardrail_overlay.get("scope_id", "")) if isinstance(guardrail_overlay, Mapping) else ""
    guardrail_patch_count = (
        _int_value(guardrail_overlay.get("guardrail_patch_count")) if isinstance(guardrail_overlay, Mapping) else 0
    )
    mixed_payload = payload.get("mixed_guarded_requirements", {}) if payload else {}
    mixed_payload_required = (
        _bool(mixed_payload.get("collision_guardrail_required")) if isinstance(mixed_payload, Mapping) else False
    )
    mixed_row_required = _bool(candidate_row.get("mixed_collision_guardrail_required"))
    claim_boundary_ok = bool(payload and _claim_boundary_forbids_execution(payload))

    if not inside:
        failures.append("path_outside_source_run_dir")
    if not payload_candidate_id_matches:
        failures.append("candidate_id_mismatch")
    if not matrix_present:
        failures.append("missing_patch_matrix_row")
    if not guardrail_present:
        failures.append("missing_guardrail_scope_row")
    if not source_repair_non_empty:
        failures.append("missing_source_repair_spec_id")
    if not repair_family_non_empty:
        failures.append("missing_repair_family")
    if reward_count != 3:
        failures.append("reward_overlay_count_not_3")
    if curriculum_count != 1:
        failures.append("curriculum_overlay_count_not_1")
    if guardrail_scope_id != "global_guardrail_scope":
        failures.append("guardrail_scope_not_global")
    if guardrail_patch_count != 284:
        failures.append("guardrail_patch_count_not_284")
    if mixed_payload_required != mixed_row_required:
        failures.append("mixed_collision_requirement_mismatch")
    if not claim_boundary_ok:
        failures.append("claim_boundary_allows_execution")

    row = {
        "candidate_id": candidate_id,
        "candidate_config_path": str(path),
        "path_exists": path_exists,
        "inside_source_run_dir": inside,
        "payload_candidate_id_matches": payload_candidate_id_matches,
        "matrix_candidate_id_present": matrix_present,
        "guardrail_candidate_id_present": guardrail_present,
        "source_repair_spec_id_non_empty": source_repair_non_empty,
        "repair_family_non_empty": repair_family_non_empty,
        "reward_overlay_count": reward_count,
        "curriculum_overlay_count": curriculum_count,
        "guardrail_scope_id": guardrail_scope_id,
        "guardrail_patch_count": guardrail_patch_count,
        "mixed_collision_guardrail_required_matches": mixed_payload_required == mixed_row_required,
        "claim_boundary_forbids_execution": claim_boundary_ok,
        "static_validation_pass": not failures,
        "failure_reasons": ";".join(failures),
    }
    return row, payload


def materialize_effective_config(
    *,
    output_dir: Path,
    static_row: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    candidate_id = str(static_row.get("candidate_id", ""))
    effective_path = _effective_config_path(output_dir, candidate_id)
    failures: list[str] = []
    schema_incomplete = not bool(payload and isinstance(payload.get("env_config"), Mapping))
    written = False
    inside = False
    if schema_incomplete:
        failures.append("missing_env_config_for_reset")
    else:
        effective_payload = {
            "candidate_id": candidate_id,
            "source_candidate_config_path": str(static_row.get("candidate_config_path", "")),
            "env_config": dict(payload.get("env_config", {})),
            "reward_overlay": payload.get("reward_overlay", []),
            "curriculum_overlay": payload.get("curriculum_overlay", []),
            "guardrail_overlay": payload.get("guardrail_overlay", {}),
            "claim_boundary": {
                "active_config_overwritten": False,
                "environment_step_count": 0,
                "policy_action_executed": False,
                "rollout_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            },
        }
        write_json(effective_path, effective_payload)
        written = True
        inside = _inside_dir(effective_path, output_dir)
        if not inside:
            failures.append("effective_config_outside_run_dir")

    return {
        "candidate_id": candidate_id,
        "candidate_config_path": str(static_row.get("candidate_config_path", "")),
        "effective_config_path": str(effective_path) if written else "",
        "effective_config_written": written,
        "effective_config_inside_run_dir": inside,
        "schema_incomplete": schema_incomplete,
        "active_config_overwritten": False,
        "failure_reasons": ";".join(failures),
    }


def reset_effective_config(*, effective_row: Mapping[str, Any], eval_seed: int) -> dict[str, Any]:
    candidate_id = str(effective_row.get("candidate_id", ""))
    path_text = str(effective_row.get("effective_config_path", ""))
    if not path_text:
        return {
            "candidate_id": candidate_id,
            "effective_config_path": "",
            "environment_load_attempted": False,
            "environment_reset_attempted": False,
            "environment_reset_success": False,
            "observation_length": 0,
            "observation_finite": False,
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": "missing_effective_config",
        }
    try:
        payload = read_json(path_text)
        config = build_env_config(dict(payload.get("env_config", {})))
        env = AutoDriftEnv(config)
        try:
            obs, _info = env.reset(seed=int(eval_seed))
        finally:
            close = getattr(env, "close", None)
            if callable(close):
                close()
        return {
            "candidate_id": candidate_id,
            "effective_config_path": path_text,
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
            "candidate_id": candidate_id,
            "effective_config_path": path_text,
            "environment_load_attempted": True,
            "environment_reset_attempted": True,
            "environment_reset_success": False,
            "observation_length": 0,
            "observation_finite": False,
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": str(exc),
        }


def run_candidate_config_reset_validation(
    *,
    source_dir: Path | str = DEFAULT_SOURCE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_candidate_config_count: int = DEFAULT_TARGET_CANDIDATE_CONFIG_COUNT,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(source_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(source / "summary.json")
    generation_manifest = read_json(source / "candidate_config_generation_manifest.json")
    candidate_rows = read_csv_rows(source / "candidate_config_rows.csv")
    matrix_rows = read_csv_rows(source / "candidate_patch_reference_matrix.csv")
    guardrail_rows = read_csv_rows(source / "candidate_guardrail_scope_rows.csv")
    active_config_safety = read_json(source / "active_config_safety_report.json")
    source_claim_rows = read_csv_rows(source / "claim_boundary.csv")
    matrix_by_candidate = {str(row.get("candidate_id", "")): row for row in matrix_rows}
    guardrail_by_candidate = {str(row.get("candidate_id", "")): row for row in guardrail_rows}

    static_rows: list[dict[str, Any]] = []
    payload_by_candidate: dict[str, dict[str, Any] | None] = {}
    for row in candidate_rows:
        static_row, payload = static_validation_row(
            source_dir=source,
            candidate_row=row,
            matrix_by_candidate=matrix_by_candidate,
            guardrail_by_candidate=guardrail_by_candidate,
        )
        static_rows.append(static_row)
        payload_by_candidate[str(static_row["candidate_id"])] = payload

    effective_rows = [
        materialize_effective_config(
            output_dir=output,
            static_row=row,
            payload=payload_by_candidate.get(str(row.get("candidate_id", ""))),
        )
        for row in static_rows
        if _bool(row.get("static_validation_pass"))
    ]
    reset_rows = [
        reset_effective_config(effective_row=row, eval_seed=int(eval_seed_base) + index)
        for index, row in enumerate(effective_rows)
        if _bool(row.get("effective_config_written")) and not _bool(row.get("schema_incomplete"))
    ]
    reset_failure_rows = [row for row in reset_rows if not _bool(row.get("environment_reset_success"))]
    claim_rows = claim_boundary_rows()

    source_candidate_config_count = len(candidate_rows)
    static_pass_count = sum(_bool(row.get("static_validation_pass")) for row in static_rows)
    static_failure_count = source_candidate_config_count - static_pass_count
    schema_incomplete_count = sum(_bool(row.get("schema_incomplete")) for row in effective_rows)
    effective_written_count = sum(_bool(row.get("effective_config_written")) for row in effective_rows)
    effective_outside_count = sum(
        _bool(row.get("effective_config_written")) and not _bool(row.get("effective_config_inside_run_dir"))
        for row in effective_rows
    )
    reset_attempt_count = sum(_bool(row.get("environment_reset_attempted")) for row in reset_rows)
    reset_success_count = sum(_bool(row.get("environment_reset_success")) for row in reset_rows)
    reset_failure_count = len(reset_failure_rows)
    environment_step_count = sum(_int_value(row.get("environment_step_count")) for row in reset_rows)
    policy_action_executed = any(_bool(row.get("policy_action_executed")) for row in reset_rows)
    active_config_overwrite_count = int(_bool(active_config_safety.get("active_config_overwritten")))
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
        "active_config_overwritten": bool(active_config_overwrite_count),
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
    passes = (
        source_summary.get("result_class") == "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"
        and generation_manifest.get("result_class")
        == "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"
        and source_candidate_config_count == int(target_candidate_config_count)
        and static_pass_count == int(target_candidate_config_count)
        and static_failure_count == 0
        and schema_incomplete_count == 0
        and effective_written_count == int(target_candidate_config_count)
        and effective_outside_count == 0
        and reset_attempt_count == int(target_candidate_config_count)
        and reset_success_count == int(target_candidate_config_count)
        and reset_failure_count == 0
        and environment_step_count == 0
        and active_config_overwrite_count == 0
        and guardrail_violation_count == 0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL

    write_csv_rows(output / "static_validation_rows.csv", static_rows, fieldnames=STATIC_FIELDNAMES)
    write_csv_rows(output / "effective_config_rows.csv", effective_rows, fieldnames=EFFECTIVE_FIELDNAMES)
    write_csv_rows(output / "reset_validation_rows.csv", reset_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", reset_failure_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "source_dir": str(source),
        "output_dir": str(output),
        "source_result_class": source_summary.get("result_class", ""),
        "source_candidate_config_count": source_candidate_config_count,
        "target_candidate_config_count": int(target_candidate_config_count),
        "candidate_repair_family_counts": _count_by(candidate_rows, "repair_family"),
        "source_claim_boundary_row_count": len(source_claim_rows),
        "static_validation_pass_count": static_pass_count,
        "static_validation_failure_count": static_failure_count,
        "schema_incomplete_candidate_count": schema_incomplete_count,
        "effective_config_written_count": effective_written_count,
        "effective_config_outside_run_dir_count": effective_outside_count,
        "environment_load_attempt_count": sum(_bool(row.get("environment_load_attempted")) for row in reset_rows),
        "environment_reset_attempt_count": reset_attempt_count,
        "environment_reset_success_count": reset_success_count,
        "environment_reset_failure_count": reset_failure_count,
        "sampler_incompatible_candidate_count": reset_failure_count,
        "environment_reset_started": reset_attempt_count > 0,
        "environment_step_count": environment_step_count,
        "policy_action_executed": policy_action_executed,
        "rollout_started": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "active_config_overwrite_count": active_config_overwrite_count,
        "active_config_overwritten": bool(active_config_overwrite_count),
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
        "failure_types_observed": [
            name
            for name, count in [
                ("static_schema_failure", static_failure_count),
                ("effective_config_materialization_failure", schema_incomplete_count),
                ("sampler_incompatible_candidate", reset_failure_count),
            ]
            if count
        ],
        "artifacts": {
            "summary": str(output / "summary.json"),
            "static_validation_rows": str(output / "static_validation_rows.csv"),
            "effective_config_rows": str(output / "effective_config_rows.csv"),
            "reset_validation_rows": str(output / "reset_validation_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "effective_config_dir": str(output / "effective_configs"),
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
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_candidate_config_reset_validation(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        target_candidate_config_count=int(args.target_candidate_config_count),
        eval_seed_base=int(args.eval_seed_base),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_candidate_config_count={summary['source_candidate_config_count']}")
    print(f"static_validation_pass_count={summary['static_validation_pass_count']}")
    print(f"schema_incomplete_candidate_count={summary['schema_incomplete_candidate_count']}")
    print(f"environment_reset_attempt_count={summary['environment_reset_attempt_count']}")
    print(f"environment_reset_success_count={summary['environment_reset_success_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
