"""Reset-only validator for dual-axis candidate config packs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
)
from autodrift.executable_v2_task_quality_reset_validation_preflight import (
    reset_task_quality_spec,
)


DEFAULT_CONFIG_PACK_MANIFEST = Path(
    "runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_pack_manifest.json"
)
DEFAULT_PATCH_ROWS = Path(
    "runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/scenario_spec_patch_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation")
DEFAULT_EVAL_SEED_BASE = 235300
TARGET_CONFIG_PACK_COUNT = 5
TARGET_SCENARIO_SPECS_PER_PACK = 72
EXPECTED_OBSERVATION_DIM = 72
RESULT_PASS = "current_sim_dual_axis_candidate_pack_reset_validation_pass"
RESULT_FAIL = "current_sim_dual_axis_candidate_pack_reset_validation_fail"
FORBIDDEN_GUARDRAILS = (
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "support_policy_ranking_claim_made",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed_claim_made",
    "reset_valid_scenario_pack_claim_made",
)
CONTRACT_FIELDNAMES = [
    "pack_id",
    "scenario_index",
    "scenario_spec_id",
    "history_length_is_one",
    "action_history_mode_full",
    "include_privileged_params_false",
    "wheel_observation_mode_none",
    "obstacle_relative_velocity_mode_zero",
    "labels_enter_actor_input_false",
    "diagnostic_only_no_ranking_claim_true",
    "env_config_supported_true",
    "execution_blocked_by_unsupported_capability_false",
    "contract_violation_count",
]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n", ""}:
            return False
    return default


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _scenario_spec_id(spec: Mapping[str, Any], index: int) -> str:
    value = spec.get("scenario_spec_id") or spec.get("task_source_id") or spec.get("candidate_source_id")
    return str(value) if value not in {None, ""} else f"scenario_{index:03d}"


def load_config_pack_manifest(path: Path | str = DEFAULT_CONFIG_PACK_MANIFEST) -> dict[str, Any]:
    payload = read_json(path)
    packs = payload.get("packs")
    if not isinstance(packs, list):
        raise ValueError("config pack manifest must contain packs")
    return dict(payload)


def load_config_packs(manifest_path: Path | str = DEFAULT_CONFIG_PACK_MANIFEST) -> list[dict[str, Any]]:
    manifest = load_config_pack_manifest(manifest_path)
    output: list[dict[str, Any]] = []
    for pack_meta in manifest["packs"]:
        pack_path = Path(str(pack_meta.get("pack_path", "")))
        pack = read_json(pack_path)
        specs = pack.get("scenario_specs")
        if not isinstance(specs, list):
            raise ValueError(f"config pack {pack_path} must contain scenario_specs")
        output.append(
            {
                **dict(pack_meta),
                "pack_path": str(pack_path),
                "scenario_specs": [dict(spec) for spec in specs],
            }
        )
    return output


def contract_row_for_pack_spec(
    *,
    pack_id: str,
    scenario_index: int,
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    env_config = dict(spec.get("env_config") or {})
    checks = {
        "history_length_is_one": int(env_config.get("history_length", spec.get("history_length", 0))) == 1,
        "action_history_mode_full": str(env_config.get("action_history_mode", "")) == "full",
        "include_privileged_params_false": not _bool(
            env_config.get("include_privileged_params", spec.get("include_privileged_params"))
        ),
        "wheel_observation_mode_none": str(
            env_config.get("wheel_observation_mode", spec.get("wheel_observation_mode", ""))
        )
        == "none",
        "obstacle_relative_velocity_mode_zero": str(
            env_config.get("obstacle_relative_velocity_mode", spec.get("obstacle_relative_velocity_mode", ""))
        )
        == "zero",
        "labels_enter_actor_input_false": not _bool(spec.get("labels_enter_actor_input")),
        "diagnostic_only_no_ranking_claim_true": _bool(
            spec.get("diagnostic_only_no_ranking_claim"), default=True
        ),
        "env_config_supported_true": _bool(spec.get("env_config_supported"), default=True),
        "execution_blocked_by_unsupported_capability_false": not _bool(
            spec.get("execution_blocked_by_unsupported_capability")
        ),
    }
    return {
        "pack_id": str(pack_id),
        "scenario_index": int(scenario_index),
        "scenario_spec_id": _scenario_spec_id(spec, scenario_index),
        **checks,
        "contract_violation_count": int(sum(not bool(value) for value in checks.values())),
    }


def reset_pack_spec(
    *,
    pack_id: str,
    pack_path: str,
    scenario_index: int,
    spec: Mapping[str, Any],
    eval_seed: int,
    expected_observation_dim: int | None,
) -> dict[str, Any]:
    reset_row = reset_task_quality_spec(
        spec=spec,
        eval_seed=int(eval_seed),
        expected_observation_dim=expected_observation_dim,
    )
    contract = contract_row_for_pack_spec(pack_id=pack_id, scenario_index=scenario_index, spec=spec)
    reset_row.update(
        {
            "pack_id": str(pack_id),
            "pack_path": str(pack_path),
            "scenario_index": int(scenario_index),
            "scenario_spec_id": contract["scenario_spec_id"],
            "eval_seed": int(eval_seed),
            "observation_dimension_matches_expected": _bool(
                reset_row.get("observation_dimension_matches")
            ),
            "contract_violation_count": int(contract["contract_violation_count"]),
            "support_policy_ranking_claim_made": False,
            "winner_selected": False,
            "finite_window_vs_gru_conclusion_made": False,
            "scenario_redesign_executed_claim_made": False,
            "reset_valid_scenario_pack_claim_made": False,
        }
    )
    for key, value in _guardrail_flags().items():
        reset_row.setdefault(key, value)
    return reset_row


def _metadata_caveat_rows(path: Path | str) -> list[dict[str, Any]]:
    return [dict(row) for row in _read_csv_rows(path)]


def _patch_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _unresolved_patch_count(rows: Iterable[Mapping[str, Any]]) -> int:
    return sum(str(row.get("patch_resolution", "")) == "unresolved" for row in rows)


def pack_summary_rows(
    *,
    packs: list[Mapping[str, Any]],
    reset_rows: list[Mapping[str, Any]],
    contract_rows: list[Mapping[str, Any]],
    metadata_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reset_by_pack: dict[str, list[Mapping[str, Any]]] = {}
    contract_by_pack: dict[str, list[Mapping[str, Any]]] = {}
    metadata_by_pack: dict[str, list[Mapping[str, Any]]] = {}
    for row in reset_rows:
        reset_by_pack.setdefault(str(row.get("pack_id", "")), []).append(row)
    for row in contract_rows:
        contract_by_pack.setdefault(str(row.get("pack_id", "")), []).append(row)
    for row in metadata_rows:
        metadata_by_pack.setdefault(str(row.get("pack_id", "")), []).append(row)

    output: list[dict[str, Any]] = []
    for pack in packs:
        pack_id = str(pack.get("pack_id", ""))
        pack_resets = reset_by_pack.get(pack_id, [])
        pack_contracts = contract_by_pack.get(pack_id, [])
        pack_metadata = metadata_by_pack.get(pack_id, [])
        output.append(
            {
                "pack_id": pack_id,
                "pack_path": str(pack.get("pack_path", "")),
                "selection_count": int(pack.get("selection_count", 0)),
                "scenario_spec_count": len(pack.get("scenario_specs", [])),
                "reset_attempt_count": len(pack_resets),
                "reset_success_count": sum(_bool(row.get("reset_success")) for row in pack_resets),
                "reset_failure_count": sum(not _bool(row.get("reset_success")) for row in pack_resets),
                "contract_violation_count": sum(
                    int(row.get("contract_violation_count", 0)) for row in pack_contracts
                ),
                "metadata_patch_row_count": len(pack_metadata),
                "env_config_patch_count": _patch_count(pack_metadata, "env_config_patch_applied"),
                "metadata_only_patch_count": _patch_count(pack_metadata, "metadata_only_patch"),
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "candidate_pack_reset_validation",
            "admissible": True,
            "reason": "M2353 may claim reset-validity only if all reset gates pass",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "reset validation does not execute measured scenario redesign or compare controllers",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "policy actions and rollout remain blocked",
        },
        {
            "claim": "support_policy_or_controller_ranking",
            "admissible": False,
            "reason": "reset validation is a scenario admissibility gate",
        },
        {
            "claim": "paper_level_benchmark_evidence",
            "admissible": False,
            "reason": "reset validation is not measured rollout evidence",
        },
        {
            "claim": "finite_window_vs_gru_or_level3_self_id",
            "admissible": False,
            "reason": "reset validation does not test history necessity",
        },
    ]


def run_candidate_pack_reset_validation(
    *,
    config_pack_manifest_path: Path | str = DEFAULT_CONFIG_PACK_MANIFEST,
    patch_rows_path: Path | str = DEFAULT_PATCH_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_pack_count: int | None = TARGET_CONFIG_PACK_COUNT,
    target_scenario_specs_per_pack: int | None = TARGET_SCENARIO_SPECS_PER_PACK,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
    next_blocker: str = "m2354-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    packs = load_config_packs(config_pack_manifest_path)
    metadata_rows = _metadata_caveat_rows(patch_rows_path)

    reset_rows: list[dict[str, Any]] = []
    contract_rows: list[dict[str, Any]] = []
    flat_specs: list[dict[str, Any]] = []
    seed_offset = 0
    for pack in packs:
        pack_id = str(pack.get("pack_id", ""))
        pack_path = str(pack.get("pack_path", ""))
        for index, spec in enumerate(pack["scenario_specs"]):
            spec_dict = dict(spec)
            flat_specs.append(spec_dict)
            contract_rows.append(contract_row_for_pack_spec(pack_id=pack_id, scenario_index=index, spec=spec_dict))
            reset_rows.append(
                reset_pack_spec(
                    pack_id=pack_id,
                    pack_path=pack_path,
                    scenario_index=index,
                    spec=spec_dict,
                    eval_seed=int(eval_seed_base) + seed_offset,
                    expected_observation_dim=expected_observation_dim,
                )
            )
            seed_offset += 1

    failure_rows = [dict(row) for row in reset_rows if not _bool(row.get("reset_success"))]
    pack_rows = pack_summary_rows(
        packs=packs,
        reset_rows=reset_rows,
        contract_rows=contract_rows,
        metadata_rows=metadata_rows,
    )
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    forbidden_key_hits = forbidden_key_violations(flat_specs)
    pack_count_matches = target_pack_count is None or len(packs) == int(target_pack_count)
    scenario_counts = {str(pack.get("pack_id", "")): len(pack.get("scenario_specs", [])) for pack in packs}
    scenario_specs_per_pack_count = (
        next(iter(set(scenario_counts.values()))) if len(set(scenario_counts.values())) == 1 else None
    )
    scenario_count_matches = (
        target_scenario_specs_per_pack is None
        or all(count == int(target_scenario_specs_per_pack) for count in scenario_counts.values())
    )
    expected_reset_attempt_count = (
        None
        if target_pack_count is None or target_scenario_specs_per_pack is None
        else int(target_pack_count) * int(target_scenario_specs_per_pack)
    )
    reset_success_count = sum(_bool(row.get("reset_success")) for row in reset_rows)
    observation_finite_count = sum(_bool(row.get("observation_finite")) for row in reset_rows)
    obstacle_initialized_count = sum(_bool(row.get("obstacle_initialized")) for row in reset_rows)
    observation_dimension_failure_count = sum(
        _bool(row.get("reset_success"))
        and not _bool(row.get("observation_dimension_matches_expected"))
        for row in reset_rows
    )
    contract_violation_count = sum(int(row.get("contract_violation_count", 0)) for row in contract_rows)
    metadata_only_patch_count = _patch_count(metadata_rows, "metadata_only_patch")
    env_config_patch_count = _patch_count(metadata_rows, "env_config_patch_applied")
    unresolved_patch_count = _unresolved_patch_count(metadata_rows)
    metadata_caveat_rows_preserved = (
        bool(metadata_rows)
        and len(metadata_rows) == env_config_patch_count
        and metadata_only_patch_count == 37
        and unresolved_patch_count == 0
    )
    reset_attempt_target_matches = (
        expected_reset_attempt_count is None or len(reset_rows) == int(expected_reset_attempt_count)
    )
    passes = (
        pack_count_matches
        and scenario_count_matches
        and reset_attempt_target_matches
        and reset_success_count == len(reset_rows)
        and not failure_rows
        and observation_finite_count == len(reset_rows)
        and observation_dimension_failure_count == 0
        and obstacle_initialized_count == len(reset_rows)
        and contract_violation_count == 0
        and not forbidden_key_hits
        and metadata_caveat_rows_preserved
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "reset_rows.csv", reset_rows)
    write_csv_rows(
        output / "reset_failure_rows.csv",
        failure_rows,
        fieldnames=list(reset_rows[0].keys()) if reset_rows else None,
    )
    write_csv_rows(output / "pack_summary_rows.csv", pack_rows)
    write_csv_rows(output / "contract_rows.csv", contract_rows, fieldnames=CONTRACT_FIELDNAMES)
    write_csv_rows(output / "metadata_caveat_rows.csv", metadata_rows)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "config_pack_manifest_path": str(config_pack_manifest_path),
        "patch_rows_path": str(patch_rows_path),
        "input_config_pack_count": len(packs),
        "target_config_pack_count": target_pack_count,
        "scenario_specs_per_pack_count": scenario_specs_per_pack_count,
        "target_scenario_specs_per_pack": target_scenario_specs_per_pack,
        "scenario_counts_by_pack": scenario_counts,
        "expected_reset_attempt_count": expected_reset_attempt_count,
        "reset_attempt_count": len(reset_rows),
        "reset_success_count": int(reset_success_count),
        "reset_failure_count": len(failure_rows),
        "observation_finite_count": int(observation_finite_count),
        "observation_dimension_failure_count": int(observation_dimension_failure_count),
        "obstacle_initialized_count": int(obstacle_initialized_count),
        "contract_violation_count": int(contract_violation_count),
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
        "metadata_caveat_row_count": len(metadata_rows),
        "env_config_patch_count": int(env_config_patch_count),
        "metadata_only_patch_count": int(metadata_only_patch_count),
        "unresolved_patch_count": int(unresolved_patch_count),
        "metadata_caveat_rows_preserved": bool(metadata_caveat_rows_preserved),
        "patch_resolution_counts": _count_by(metadata_rows, "patch_resolution"),
        "pack_reset_success_counts": {
            row["pack_id"]: int(row["reset_success_count"]) for row in pack_rows
        },
        "pack_metadata_only_patch_counts": {
            row["pack_id"]: int(row["metadata_only_patch_count"]) for row in pack_rows
        },
        "active_config_overwritten": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": int(guardrail_violation_count),
        "environment_reset_started": True,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "reset_valid_scenario_pack_claim_made": False,
        "passes_public_smoke_gates": bool(passes),
        "artifacts": {
            "summary": str(output / "summary.json"),
            "reset_rows": str(output / "reset_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "pack_summary_rows": str(output / "pack_summary_rows.csv"),
            "contract_rows": str(output / "contract_rows.csv"),
            "metadata_caveat_rows": str(output / "metadata_caveat_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-pack-manifest", type=Path, default=DEFAULT_CONFIG_PACK_MANIFEST)
    parser.add_argument("--patch-rows", type=Path, default=DEFAULT_PATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-pack-count", type=int, default=TARGET_CONFIG_PACK_COUNT)
    parser.add_argument("--target-scenario-specs-per-pack", type=int, default=TARGET_SCENARIO_SPECS_PER_PACK)
    parser.add_argument("--expected-observation-dim", type=int, default=EXPECTED_OBSERVATION_DIM)
    parser.add_argument(
        "--next-blocker",
        default="m2354-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-result-audit",
    )
    args = parser.parse_args()
    summary = run_candidate_pack_reset_validation(
        config_pack_manifest_path=args.config_pack_manifest,
        patch_rows_path=args.patch_rows,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        target_pack_count=int(args.target_pack_count),
        target_scenario_specs_per_pack=int(args.target_scenario_specs_per_pack),
        expected_observation_dim=int(args.expected_observation_dim),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"reset_attempt_count={summary['reset_attempt_count']}")
    print(f"reset_success_count={summary['reset_success_count']}")
    print(f"reset_failure_count={summary['reset_failure_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"metadata_only_patch_count={summary['metadata_only_patch_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
