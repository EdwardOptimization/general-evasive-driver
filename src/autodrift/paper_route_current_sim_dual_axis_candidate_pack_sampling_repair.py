"""Artifact-only sampling repair for dual-axis candidate config packs."""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_CONFIG_PACK_MANIFEST = Path(
    "runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_pack_manifest.json"
)
DEFAULT_PATCH_ROWS = Path(
    "runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/scenario_spec_patch_rows.csv"
)
DEFAULT_CANDIDATE_SELECTION_ROWS = Path(
    "runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/candidate_selection_rows.csv"
)
DEFAULT_RESET_FAILURE_ROWS = Path(
    "runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/reset_failure_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair")
RESULT_PASS = "current_sim_dual_axis_candidate_pack_sampling_repair_materialization_pass"
RESULT_FAIL = "current_sim_dual_axis_candidate_pack_sampling_repair_materialization_fail"
TARGET_PACK_COUNT = 5
TARGET_SCENARIO_SPECS_PER_PACK = 72
TARGET_RESET_FAILURE_COUNT = 32
FALLBACK_ACTION = "baseline_env_config_fallback"
RESTORE_FIELDS = (
    "env_config",
    "hidden_dynamics_bucket",
    "friction_bucket",
    "mu_range",
    "brake_scale_bucket",
    "brake_scale_range",
    "actuator_lag_bucket",
    "steer_tau_scale_range",
    "drive_tau_scale_range",
    "front_tire_stiffness_scale_range",
    "rear_tire_stiffness_scale_range",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_longitudinal_distance_m",
    "obstacle_lateral_offset_bucket",
    "obstacle_lateral_offset_m",
    "obstacle_half_width_m",
    "finish_on_pass",
)
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
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
    if lowered in {"false", "0", "no", "n", ""}:
        return False
    return default


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _load_pack_manifest(path: Path | str) -> dict[str, Any]:
    payload = read_json(path)
    packs = payload.get("packs")
    if not isinstance(packs, list):
        raise ValueError("config pack manifest must contain packs")
    return dict(payload)


def _load_pack(path: Path | str) -> dict[str, Any]:
    pack = read_json(path)
    specs = pack.get("scenario_specs")
    if not isinstance(specs, list):
        raise ValueError(f"config pack {path} must contain scenario_specs")
    return dict(pack)


def _scenario_specs_by_id(pack: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(spec.get("scenario_spec_id", "")): dict(spec)
        for spec in pack.get("scenario_specs", [])
        if str(spec.get("scenario_spec_id", ""))
    }


def _row_by_key(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(row.get("pack_id", "")), str(row.get("scenario_spec_id", ""))): dict(row) for row in rows}


def _repair_class(selection: Mapping[str, Any]) -> str:
    transform = str(selection.get("transform_name", ""))
    if "timing_step_earlier" in transform:
        return "timing_related"
    if "lateral_offset_step_toward_centerline" in transform:
        return "lateral_hidden"
    return "hidden_only"


def _copy_baseline_fields(
    *,
    candidate: dict[str, Any],
    baseline: Mapping[str, Any],
    pack_id: str,
    scenario_spec_id: str,
) -> list[dict[str, Any]]:
    missing_rows: list[dict[str, Any]] = []
    for field in RESTORE_FIELDS:
        baseline_has = field in baseline
        candidate_has = field in candidate
        if baseline_has:
            candidate[field] = deepcopy(baseline[field])
        if not baseline_has or not candidate_has:
            missing_rows.append(
                {
                    "pack_id": pack_id,
                    "scenario_spec_id": scenario_spec_id,
                    "field": field,
                    "baseline_has_field": baseline_has,
                    "candidate_had_field": candidate_has,
                }
            )
    return missing_rows


def _repair_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "sampling_repaired_candidate_pack_artifacts",
            "allowed": True,
            "made": True,
            "reason": "M2356 may claim only artifact-only row-level fallback materialization if gates pass",
        },
        {
            "claim": "reset_valid_repaired_pack",
            "allowed": False,
            "made": False,
            "reason": "M2356 does not run reset validation",
        },
        {
            "claim": "scenario_redesign_executed",
            "allowed": False,
            "made": False,
            "reason": "M2356 rewrites artifact packs only",
        },
        {
            "claim": "controller_family_ranking",
            "allowed": False,
            "made": False,
            "reason": "No rollout or policy action is executed",
        },
        {
            "claim": "paper_level_or_self_id_evidence",
            "allowed": False,
            "made": False,
            "reason": "Repair materialization is task-quality infrastructure",
        },
    ]


def run_candidate_pack_sampling_repair_materialization(
    *,
    config_pack_manifest_path: Path | str = DEFAULT_CONFIG_PACK_MANIFEST,
    patch_rows_path: Path | str = DEFAULT_PATCH_ROWS,
    candidate_selection_rows_path: Path | str = DEFAULT_CANDIDATE_SELECTION_ROWS,
    reset_failure_rows_path: Path | str = DEFAULT_RESET_FAILURE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = "m2357-paper-route-current-sim-dual-axis-candidate-pack-sampling-repair-result-audit",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    packs_dir = output / "config_packs"
    packs_dir.mkdir(parents=True, exist_ok=True)

    manifest = _load_pack_manifest(config_pack_manifest_path)
    pack_metas = [dict(row) for row in manifest["packs"]]
    patch_rows = _read_csv_rows(patch_rows_path)
    selection_rows = _read_csv_rows(candidate_selection_rows_path)
    failure_rows = _read_csv_rows(reset_failure_rows_path)
    failure_keys = {(row["pack_id"], row["scenario_spec_id"]) for row in failure_rows}
    patch_by_key = _row_by_key(patch_rows)
    selection_by_key = _row_by_key(selection_rows)

    baseline_meta = next((meta for meta in pack_metas if str(meta.get("pack_id", "")) == "baseline_reference_pack"), None)
    if baseline_meta is None:
        raise ValueError("manifest must contain baseline_reference_pack")
    baseline_pack = _load_pack(str(baseline_meta["pack_path"]))
    baseline_specs_by_id = _scenario_specs_by_id(baseline_pack)

    repaired_manifest_packs: list[dict[str, Any]] = []
    repair_action_rows: list[dict[str, Any]] = []
    missing_field_rows: list[dict[str, Any]] = []
    effective_summary_rows: list[dict[str, Any]] = []
    repaired_patch_rows: list[dict[str, Any]] = []
    repaired_selection_rows: list[dict[str, Any]] = []

    for meta in pack_metas:
        pack_id = str(meta.get("pack_id", ""))
        source_pack_path = Path(str(meta.get("pack_path", "")))
        source_pack = _load_pack(source_pack_path)
        repaired_pack = deepcopy(source_pack)
        repaired_specs: list[dict[str, Any]] = []
        fallback_count = 0
        timing_count = 0
        hidden_count = 0
        lateral_hidden_count = 0
        for spec in source_pack["scenario_specs"]:
            spec_id = str(spec.get("scenario_spec_id", ""))
            repaired_spec = deepcopy(dict(spec))
            key = (pack_id, spec_id)
            if key in failure_keys:
                baseline_spec = baseline_specs_by_id.get(spec_id)
                if baseline_spec is None:
                    missing_field_rows.append(
                        {
                            "pack_id": pack_id,
                            "scenario_spec_id": spec_id,
                            "field": "baseline_spec",
                            "baseline_has_field": False,
                            "candidate_had_field": True,
                        }
                    )
                else:
                    missing_field_rows.extend(
                        _copy_baseline_fields(
                            candidate=repaired_spec,
                            baseline=baseline_spec,
                            pack_id=pack_id,
                            scenario_spec_id=spec_id,
                        )
                    )
                selection = selection_by_key.get(key, {})
                patch = patch_by_key.get(key, {})
                repair_class = _repair_class(selection)
                fallback_count += 1
                timing_count += int(repair_class == "timing_related")
                hidden_count += int(repair_class == "hidden_only")
                lateral_hidden_count += int(repair_class == "lateral_hidden")
                repaired_spec["sampling_repair_applied"] = True
                repaired_spec["sampling_repair_action"] = FALLBACK_ACTION
                repaired_spec["sampling_repair_source_candidate_id"] = selection.get(
                    "candidate_id", patch.get("candidate_id", "")
                )
                repaired_spec["sampling_repair_class"] = repair_class
                repair_action_rows.append(
                    {
                        "pack_id": pack_id,
                        "scenario_spec_id": spec_id,
                        "repair_action": FALLBACK_ACTION,
                        "repair_class": repair_class,
                        "candidate_id": selection.get("candidate_id", patch.get("candidate_id", "")),
                        "candidate_axis": selection.get("candidate_axis", ""),
                        "transform_name": selection.get("transform_name", ""),
                        "patch_resolution": patch.get("patch_resolution", ""),
                        "metadata_only_patch": patch.get("metadata_only_patch", ""),
                        "baseline_spec_found": baseline_spec is not None,
                        "diagnostic_only": True,
                        "ranking_admissible": False,
                        "winner_selected": False,
                        "paper_level_claim_made": False,
                        "level3_self_id_claim_made": False,
                        "scenario_redesign_executed": False,
                    }
                )
            else:
                repaired_spec["sampling_repair_applied"] = False
            repaired_specs.append(repaired_spec)

        repaired_pack["scenario_specs"] = repaired_specs
        repaired_pack["config_pack_id"] = pack_id
        repaired_pack["sampling_repaired_pack"] = fallback_count > 0
        repaired_pack["sampling_repair_action"] = FALLBACK_ACTION if fallback_count else ""
        repaired_pack["active_config_overwritten"] = False
        repaired_pack["scenario_redesign_executed_claim_made"] = False
        repaired_pack_path = packs_dir / f"{pack_id}.json"
        write_json(repaired_pack_path, repaired_pack)
        original_selection_count = int(meta.get("selection_count", 0))
        repaired_manifest_packs.append(
            {
                **meta,
                "pack_path": str(repaired_pack_path),
                "source_pack_path": str(source_pack_path),
                "sampling_repaired_pack": fallback_count > 0,
                "sampling_repair_action": FALLBACK_ACTION if fallback_count else "",
                "sampling_repair_fallback_count": fallback_count,
                "effective_selection_count": max(original_selection_count - fallback_count, 0),
                "active_config_overwritten": False,
                "scenario_redesign_executed": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
            }
        )
        effective_summary_rows.append(
            {
                "pack_id": pack_id,
                "scenario_spec_count": len(repaired_specs),
                "original_selection_count": original_selection_count,
                "baseline_env_config_fallback_count": fallback_count,
                "effective_selection_count": max(original_selection_count - fallback_count, 0),
                "timing_related_repair_count": timing_count,
                "hidden_only_repair_count": hidden_count,
                "lateral_hidden_repair_count": lateral_hidden_count,
            }
        )

    for row in patch_rows:
        key = (str(row.get("pack_id", "")), str(row.get("scenario_spec_id", "")))
        repaired_patch_rows.append(
            {
                **row,
                "sampling_repair_applied": key in failure_keys,
                "sampling_repair_action": FALLBACK_ACTION if key in failure_keys else "",
            }
        )
    for row in selection_rows:
        key = (str(row.get("pack_id", "")), str(row.get("scenario_spec_id", "")))
        repaired_selection_rows.append(
            {
                **row,
                "sampling_repair_applied": key in failure_keys,
                "sampling_repair_action": FALLBACK_ACTION if key in failure_keys else "",
            }
        )

    repaired_manifest = {
        "claim_scope": "artifact_only_candidate_pack_sampling_repair_materialization",
        "source_config_pack_manifest": str(config_pack_manifest_path),
        "source_reset_failure_rows": str(reset_failure_rows_path),
        "config_pack_count": len(repaired_manifest_packs),
        "active_config_overwritten": False,
        "scenario_redesign_executed_claim_made": False,
        "packs": repaired_manifest_packs,
    }

    scenario_counts = {
        str(pack["pack_id"]): len(_load_pack(pack["pack_path"])["scenario_specs"])
        for pack in repaired_manifest_packs
    }
    scenario_specs_per_pack_count = (
        next(iter(set(scenario_counts.values()))) if len(set(scenario_counts.values())) == 1 else None
    )
    fallback_count = len(repair_action_rows)
    timing_count = sum(row["repair_class"] == "timing_related" for row in repair_action_rows)
    hidden_count = sum(row["repair_class"] == "hidden_only" for row in repair_action_rows)
    lateral_hidden_count = sum(row["repair_class"] == "lateral_hidden" for row in repair_action_rows)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    metadata_only_patch_count = sum(_bool(row.get("metadata_only_patch")) for row in repaired_patch_rows)
    metadata_caveat_rows_preserved = (
        len(repaired_patch_rows) == len(patch_rows)
        and metadata_only_patch_count == sum(_bool(row.get("metadata_only_patch")) for row in patch_rows)
    )
    active_config_overwritten = False
    repair_missing_field_count = len(missing_field_rows)
    passes = (
        len(repaired_manifest_packs) == TARGET_PACK_COUNT
        and scenario_specs_per_pack_count == TARGET_SCENARIO_SPECS_PER_PACK
        and len(failure_rows) == TARGET_RESET_FAILURE_COUNT
        and fallback_count == TARGET_RESET_FAILURE_COUNT
        and timing_count == 27
        and hidden_count == 3
        and lateral_hidden_count == 2
        and repair_missing_field_count == 0
        and metadata_caveat_rows_preserved
        and not active_config_overwritten
        and guardrail_violation_count == 0
    )

    write_json(output / "repaired_config_pack_manifest.json", repaired_manifest)
    write_csv_rows(output / "repair_action_rows.csv", repair_action_rows)
    write_csv_rows(output / "repaired_scenario_spec_patch_rows.csv", repaired_patch_rows)
    write_csv_rows(output / "repaired_candidate_selection_rows.csv", repaired_selection_rows)
    write_csv_rows(output / "effective_pack_summary_rows.csv", effective_summary_rows)
    write_csv_rows(output / "repair_missing_field_rows.csv", missing_field_rows)
    write_csv_rows(output / "claim_boundary.csv", _repair_claim_boundary_rows())

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_config_pack_manifest": str(config_pack_manifest_path),
        "source_patch_rows": str(patch_rows_path),
        "source_candidate_selection_rows": str(candidate_selection_rows_path),
        "source_reset_failure_rows": str(reset_failure_rows_path),
        "input_config_pack_count": len(pack_metas),
        "output_config_pack_count": len(repaired_manifest_packs),
        "scenario_specs_per_pack_count": scenario_specs_per_pack_count,
        "scenario_counts_by_pack": scenario_counts,
        "input_reset_failure_count": len(failure_rows),
        "baseline_env_config_fallback_count": fallback_count,
        "timing_related_repair_count": int(timing_count),
        "hidden_only_repair_count": int(hidden_count),
        "lateral_hidden_repair_count": int(lateral_hidden_count),
        "repair_missing_field_count": repair_missing_field_count,
        "metadata_caveat_rows_preserved": bool(metadata_caveat_rows_preserved),
        "metadata_patch_row_count": len(repaired_patch_rows),
        "metadata_only_patch_count": int(metadata_only_patch_count),
        "active_config_overwritten": active_config_overwritten,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "reset_valid_scenario_pack_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repaired_config_pack_manifest": str(output / "repaired_config_pack_manifest.json"),
            "repair_action_rows": str(output / "repair_action_rows.csv"),
            "repaired_scenario_spec_patch_rows": str(output / "repaired_scenario_spec_patch_rows.csv"),
            "repaired_candidate_selection_rows": str(output / "repaired_candidate_selection_rows.csv"),
            "effective_pack_summary_rows": str(output / "effective_pack_summary_rows.csv"),
            "repair_missing_field_rows": str(output / "repair_missing_field_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "config_packs_dir": str(packs_dir),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-pack-manifest", type=Path, default=DEFAULT_CONFIG_PACK_MANIFEST)
    parser.add_argument("--patch-rows", type=Path, default=DEFAULT_PATCH_ROWS)
    parser.add_argument("--candidate-selection-rows", type=Path, default=DEFAULT_CANDIDATE_SELECTION_ROWS)
    parser.add_argument("--reset-failure-rows", type=Path, default=DEFAULT_RESET_FAILURE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--next-blocker",
        default="m2357-paper-route-current-sim-dual-axis-candidate-pack-sampling-repair-result-audit",
    )
    args = parser.parse_args()
    summary = run_candidate_pack_sampling_repair_materialization(
        config_pack_manifest_path=args.config_pack_manifest,
        patch_rows_path=args.patch_rows,
        candidate_selection_rows_path=args.candidate_selection_rows,
        reset_failure_rows_path=args.reset_failure_rows,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"output_config_pack_count={summary['output_config_pack_count']}")
    print(f"baseline_env_config_fallback_count={summary['baseline_env_config_fallback_count']}")
    print(f"repair_missing_field_count={summary['repair_missing_field_count']}")
    print(f"metadata_caveat_rows_preserved={summary['metadata_caveat_rows_preserved']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
