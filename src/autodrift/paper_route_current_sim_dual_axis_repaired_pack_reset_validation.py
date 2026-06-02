"""Reset-only validator for sampling-repaired dual-axis candidate config packs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift import paper_route_current_sim_dual_axis_candidate_pack_reset_validation as candidate_reset
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_executable_workload_materialization_preflight import (
    forbidden_key_violations,
)


DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST = Path(
    "runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/"
    "repaired_config_pack_manifest.json"
)
DEFAULT_REPAIR_ACTION_ROWS = Path(
    "runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repair_action_rows.csv"
)
DEFAULT_REPAIRED_PATCH_ROWS = Path(
    "runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/"
    "repaired_scenario_spec_patch_rows.csv"
)
DEFAULT_EFFECTIVE_PACK_SUMMARY_ROWS = Path(
    "runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/"
    "effective_pack_summary_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation"
)
DEFAULT_EVAL_SEED_BASE = 235900
TARGET_CONFIG_PACK_COUNT = 5
TARGET_SCENARIO_SPECS_PER_PACK = 72
EXPECTED_OBSERVATION_DIM = 72
EXPECTED_BASELINE_FALLBACK_COUNT = 32
EXPECTED_METADATA_CAVEAT_ROW_COUNT = 78
EXPECTED_METADATA_ONLY_PATCH_COUNT = 37
RESULT_PASS = "current_sim_dual_axis_repaired_pack_reset_validation_pass"
RESULT_FAIL = "current_sim_dual_axis_repaired_pack_reset_validation_fail"
REPAIR_ACTION_RESET_FIELDNAMES = [
    "pack_id",
    "pack_path",
    "scenario_index",
    "scenario_spec_id",
    "repair_action",
    "repair_class",
    "candidate_id",
    "sampling_repair_source_candidate_id",
    "reset_success",
    "error_type",
    "error_message",
    "observation_finite",
    "obstacle_initialized",
    "contract_violation_count",
]


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return candidate_reset._read_csv_rows(path)


def _bool(value: Any, *, default: bool = False) -> bool:
    return candidate_reset._bool(value, default=default)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return candidate_reset._count_by(rows, key)


def _patch_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return candidate_reset._patch_count(rows, key)


def _unresolved_patch_count(rows: Iterable[Mapping[str, Any]]) -> int:
    return candidate_reset._unresolved_patch_count(rows)


def _row_by_pack_spec(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("pack_id", "")), str(row.get("scenario_spec_id", ""))): dict(row)
        for row in rows
    }


def load_repaired_config_pack_manifest(
    path: Path | str = DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST,
) -> dict[str, Any]:
    payload = read_json(path)
    packs = payload.get("packs")
    if not isinstance(packs, list):
        raise ValueError("repaired config pack manifest must contain packs")
    return dict(payload)


def load_repaired_config_packs(
    manifest_path: Path | str = DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST,
) -> list[dict[str, Any]]:
    manifest = load_repaired_config_pack_manifest(manifest_path)
    output: list[dict[str, Any]] = []
    for pack_meta in manifest["packs"]:
        pack_path = Path(str(pack_meta.get("pack_path", "")))
        pack = read_json(pack_path)
        specs = pack.get("scenario_specs")
        if not isinstance(specs, list):
            raise ValueError(f"repaired config pack {pack_path} must contain scenario_specs")
        output.append(
            {
                **dict(pack_meta),
                "pack_path": str(pack_path),
                "scenario_specs": [dict(spec) for spec in specs],
            }
        )
    return output


def _repair_metadata_for_spec(
    *,
    pack_id: str,
    scenario_spec_id: str,
    spec: Mapping[str, Any],
    repair_action_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    action_row = repair_action_by_key.get((pack_id, scenario_spec_id), {})
    repair_applied = _bool(
        spec.get(
            "sampling_repair_applied",
            action_row.get("repair_action") == "baseline_env_config_fallback",
        )
    )
    repair_action = str(
        spec.get("sampling_repair_action")
        or action_row.get("repair_action")
        or ("baseline_env_config_fallback" if repair_applied else "")
    )
    repair_class = str(spec.get("sampling_repair_class") or action_row.get("repair_class") or "")
    candidate_id = str(
        spec.get("sampling_repair_source_candidate_id") or action_row.get("candidate_id") or ""
    )
    return {
        "sampling_repair_applied": bool(repair_applied),
        "sampling_repair_action": repair_action,
        "sampling_repair_class": repair_class,
        "sampling_repair_source_candidate_id": candidate_id,
    }


def _reset_repaired_pack_spec(
    *,
    pack_id: str,
    pack_path: str,
    scenario_index: int,
    spec: Mapping[str, Any],
    eval_seed: int,
    expected_observation_dim: int | None,
    repair_action_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    scenario_spec_id = candidate_reset._scenario_spec_id(spec, scenario_index)
    reset_row = candidate_reset.reset_pack_spec(
        pack_id=pack_id,
        pack_path=pack_path,
        scenario_index=scenario_index,
        spec=spec,
        eval_seed=eval_seed,
        expected_observation_dim=expected_observation_dim,
    )
    reset_row.update(
        _repair_metadata_for_spec(
            pack_id=pack_id,
            scenario_spec_id=scenario_spec_id,
            spec=spec,
            repair_action_by_key=repair_action_by_key,
        )
    )
    return reset_row


def _repair_action_reset_rows(
    *,
    reset_rows: Iterable[Mapping[str, Any]],
    repair_action_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reset_by_key = _row_by_pack_spec(reset_rows)
    output: list[dict[str, Any]] = []
    for action in repair_action_rows:
        key = (str(action.get("pack_id", "")), str(action.get("scenario_spec_id", "")))
        reset = reset_by_key.get(key, {})
        output.append(
            {
                "pack_id": key[0],
                "pack_path": str(reset.get("pack_path", "")),
                "scenario_index": reset.get("scenario_index", ""),
                "scenario_spec_id": key[1],
                "repair_action": str(action.get("repair_action", "")),
                "repair_class": str(action.get("repair_class", "")),
                "candidate_id": str(action.get("candidate_id", "")),
                "sampling_repair_source_candidate_id": str(
                    reset.get("sampling_repair_source_candidate_id", "")
                ),
                "reset_success": _bool(reset.get("reset_success")),
                "error_type": str(reset.get("error_type", "")),
                "error_message": str(reset.get("error_message", "")),
                "observation_finite": _bool(reset.get("observation_finite")),
                "obstacle_initialized": _bool(reset.get("obstacle_initialized")),
                "contract_violation_count": int(reset.get("contract_violation_count", 0) or 0),
            }
        )
    return output


def _repair_action_rows_preserved(
    *,
    reset_rows: Iterable[Mapping[str, Any]],
    repair_action_rows: Iterable[Mapping[str, Any]],
) -> bool:
    reset_by_key = _row_by_pack_spec(reset_rows)
    for action in repair_action_rows:
        key = (str(action.get("pack_id", "")), str(action.get("scenario_spec_id", "")))
        reset = reset_by_key.get(key)
        if reset is None:
            return False
        if not _bool(reset.get("sampling_repair_applied")):
            return False
        if str(reset.get("sampling_repair_action", "")) != str(action.get("repair_action", "")):
            return False
        if str(reset.get("sampling_repair_class", "")) != str(action.get("repair_class", "")):
            return False
        if str(reset.get("sampling_repair_source_candidate_id", "")) != str(
            action.get("candidate_id", "")
        ):
            return False
    return True


def _metadata_caveat_rows_preserved(
    *,
    repaired_patch_rows: list[Mapping[str, Any]],
    expected_metadata_row_count: int | None,
    expected_metadata_only_patch_count: int | None,
) -> bool:
    metadata_only_patch_count = _patch_count(repaired_patch_rows, "metadata_only_patch")
    unresolved_patch_count = _unresolved_patch_count(repaired_patch_rows)
    row_count_matches = expected_metadata_row_count is None or len(repaired_patch_rows) == int(
        expected_metadata_row_count
    )
    metadata_only_matches = (
        expected_metadata_only_patch_count is None
        or metadata_only_patch_count == int(expected_metadata_only_patch_count)
    )
    return bool(repaired_patch_rows) and row_count_matches and metadata_only_matches and unresolved_patch_count == 0


def _effective_selection_summary(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for row in rows:
        pack_id = str(row.get("pack_id", ""))
        output[pack_id] = {
            "original_selection_count": int(row.get("original_selection_count", 0) or 0),
            "baseline_env_config_fallback_count": int(
                row.get("baseline_env_config_fallback_count", 0) or 0
            ),
            "effective_selection_count": int(row.get("effective_selection_count", 0) or 0),
            "timing_related_repair_count": int(row.get("timing_related_repair_count", 0) or 0),
            "hidden_only_repair_count": int(row.get("hidden_only_repair_count", 0) or 0),
            "lateral_hidden_repair_count": int(row.get("lateral_hidden_repair_count", 0) or 0),
        }
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "repaired_pack_reset_validation",
            "admissible": True,
            "made": True,
            "reason": "M2359 may claim only reset validity for M2356 repaired config packs if all reset gates pass",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "made": False,
            "reason": "reset validation does not execute measured scenario redesign or compare controllers",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "made": False,
            "reason": "policy actions and rollout remain blocked",
        },
        {
            "claim": "support_policy_or_controller_ranking",
            "admissible": False,
            "made": False,
            "reason": "reset validation is a task-quality admissibility gate",
        },
        {
            "claim": "finite_window_vs_gru_or_level3_self_id",
            "admissible": False,
            "made": False,
            "reason": "reset validation does not test history necessity",
        },
    ]


def run_repaired_pack_reset_validation(
    *,
    repaired_config_pack_manifest_path: Path | str = DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST,
    repair_action_rows_path: Path | str = DEFAULT_REPAIR_ACTION_ROWS,
    repaired_patch_rows_path: Path | str = DEFAULT_REPAIRED_PATCH_ROWS,
    effective_pack_summary_rows_path: Path | str = DEFAULT_EFFECTIVE_PACK_SUMMARY_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    target_pack_count: int | None = TARGET_CONFIG_PACK_COUNT,
    target_scenario_specs_per_pack: int | None = TARGET_SCENARIO_SPECS_PER_PACK,
    expected_observation_dim: int | None = EXPECTED_OBSERVATION_DIM,
    expected_baseline_fallback_count: int | None = EXPECTED_BASELINE_FALLBACK_COUNT,
    expected_metadata_row_count: int | None = EXPECTED_METADATA_CAVEAT_ROW_COUNT,
    expected_metadata_only_patch_count: int | None = EXPECTED_METADATA_ONLY_PATCH_COUNT,
    next_blocker: str = "m2360-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    packs = load_repaired_config_packs(repaired_config_pack_manifest_path)
    repair_action_rows = _read_csv_rows(repair_action_rows_path)
    repaired_patch_rows = _read_csv_rows(repaired_patch_rows_path)
    effective_pack_summary_rows = _read_csv_rows(effective_pack_summary_rows_path)
    repair_action_by_key = _row_by_pack_spec(repair_action_rows)

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
            contract_rows.append(
                candidate_reset.contract_row_for_pack_spec(
                    pack_id=pack_id,
                    scenario_index=index,
                    spec=spec_dict,
                )
            )
            reset_rows.append(
                _reset_repaired_pack_spec(
                    pack_id=pack_id,
                    pack_path=pack_path,
                    scenario_index=index,
                    spec=spec_dict,
                    eval_seed=int(eval_seed_base) + seed_offset,
                    expected_observation_dim=expected_observation_dim,
                    repair_action_by_key=repair_action_by_key,
                )
            )
            seed_offset += 1

    failure_rows = [dict(row) for row in reset_rows if not _bool(row.get("reset_success"))]
    repair_reset_rows = _repair_action_reset_rows(
        reset_rows=reset_rows,
        repair_action_rows=repair_action_rows,
    )
    pack_rows = candidate_reset.pack_summary_rows(
        packs=packs,
        reset_rows=reset_rows,
        contract_rows=contract_rows,
        metadata_rows=repaired_patch_rows,
    )
    guardrail_flags = candidate_reset._guardrail_flags()
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
    reset_attempt_target_matches = (
        expected_reset_attempt_count is None or len(reset_rows) == int(expected_reset_attempt_count)
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
    baseline_env_config_fallback_count = len(repair_action_rows)
    repair_action_rows_preserved = _repair_action_rows_preserved(
        reset_rows=reset_rows,
        repair_action_rows=repair_action_rows,
    )
    metadata_only_patch_count = _patch_count(repaired_patch_rows, "metadata_only_patch")
    env_config_patch_count = _patch_count(repaired_patch_rows, "env_config_patch_applied")
    unresolved_patch_count = _unresolved_patch_count(repaired_patch_rows)
    metadata_caveat_rows_preserved = _metadata_caveat_rows_preserved(
        repaired_patch_rows=repaired_patch_rows,
        expected_metadata_row_count=expected_metadata_row_count,
        expected_metadata_only_patch_count=expected_metadata_only_patch_count,
    )
    effective_summary = _effective_selection_summary(effective_pack_summary_rows)
    expected_fallback_count_matches = (
        expected_baseline_fallback_count is None
        or baseline_env_config_fallback_count == int(expected_baseline_fallback_count)
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
        and expected_fallback_count_matches
        and repair_action_rows_preserved
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
    write_csv_rows(
        output / "repair_action_reset_rows.csv",
        repair_reset_rows,
        fieldnames=REPAIR_ACTION_RESET_FIELDNAMES,
    )
    write_csv_rows(
        output / "contract_rows.csv",
        contract_rows,
        fieldnames=candidate_reset.CONTRACT_FIELDNAMES,
    )
    write_csv_rows(output / "metadata_caveat_rows.csv", repaired_patch_rows)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "repaired_config_pack_manifest_path": str(repaired_config_pack_manifest_path),
        "repair_action_rows_path": str(repair_action_rows_path),
        "repaired_patch_rows_path": str(repaired_patch_rows_path),
        "effective_pack_summary_rows_path": str(effective_pack_summary_rows_path),
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
        "baseline_env_config_fallback_count": int(baseline_env_config_fallback_count),
        "expected_baseline_env_config_fallback_count": expected_baseline_fallback_count,
        "repair_action_row_count": len(repair_action_rows),
        "repair_action_reset_row_count": len(repair_reset_rows),
        "repair_action_rows_preserved": bool(repair_action_rows_preserved),
        "repair_class_counts": _count_by(repair_action_rows, "repair_class"),
        "metadata_caveat_row_count": len(repaired_patch_rows),
        "expected_metadata_caveat_row_count": expected_metadata_row_count,
        "env_config_patch_count": int(env_config_patch_count),
        "metadata_only_patch_count": int(metadata_only_patch_count),
        "expected_metadata_only_patch_count": expected_metadata_only_patch_count,
        "unresolved_patch_count": int(unresolved_patch_count),
        "metadata_caveat_rows_preserved": bool(metadata_caveat_rows_preserved),
        "patch_resolution_counts": _count_by(repaired_patch_rows, "patch_resolution"),
        "effective_selection_summary_by_pack": effective_summary,
        "effective_selection_counts_by_pack": {
            pack_id: row["effective_selection_count"] for pack_id, row in effective_summary.items()
        },
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
            "repair_action_reset_rows": str(output / "repair_action_reset_rows.csv"),
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
    parser.add_argument(
        "--repaired-config-pack-manifest",
        type=Path,
        default=DEFAULT_REPAIRED_CONFIG_PACK_MANIFEST,
    )
    parser.add_argument("--repair-action-rows", type=Path, default=DEFAULT_REPAIR_ACTION_ROWS)
    parser.add_argument("--repaired-patch-rows", type=Path, default=DEFAULT_REPAIRED_PATCH_ROWS)
    parser.add_argument(
        "--effective-pack-summary-rows",
        type=Path,
        default=DEFAULT_EFFECTIVE_PACK_SUMMARY_ROWS,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--target-pack-count", type=int, default=TARGET_CONFIG_PACK_COUNT)
    parser.add_argument("--target-scenario-specs-per-pack", type=int, default=TARGET_SCENARIO_SPECS_PER_PACK)
    parser.add_argument("--expected-observation-dim", type=int, default=EXPECTED_OBSERVATION_DIM)
    parser.add_argument(
        "--next-blocker",
        default="m2360-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-result-audit",
    )
    args = parser.parse_args()
    summary = run_repaired_pack_reset_validation(
        repaired_config_pack_manifest_path=args.repaired_config_pack_manifest,
        repair_action_rows_path=args.repair_action_rows,
        repaired_patch_rows_path=args.repaired_patch_rows,
        effective_pack_summary_rows_path=args.effective_pack_summary_rows,
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
    print(f"baseline_env_config_fallback_count={summary['baseline_env_config_fallback_count']}")
    print(f"repair_action_rows_preserved={summary['repair_action_rows_preserved']}")
    print(f"metadata_caveat_rows_preserved={summary['metadata_caveat_rows_preserved']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
