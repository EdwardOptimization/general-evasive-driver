"""No-training protocol preflight for the controller-family decisive matrix."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_json
from autodrift.corrected_profile_pilot import corrected_profile_config_paths


DEFAULT_OUTPUT_DIR = Path("runs/m1671_controller_family_decisive_matrix_protocol")
EXPECTED_PROFILE_NAMES = (
    "L0_current_masked",
    "L1_one_step",
    "L2_window_13",
    "L2_window_13_current_tiled",
    "L2_window_25",
    "L2_window_25_current_tiled",
    "L2_window_50",
    "L2_window_50_current_tiled",
    "L2_window_100",
    "L2_window_100_current_tiled",
    "L3_online_gru",
    "L3_reset_control_corrected",
)
STANDARD_SUMMARY = Path("runs/m1497_go_no_go_profile_three_seed_public_pilot/summary.json")
STANDARD_AGGREGATE = Path("runs/m1497_go_no_go_profile_three_seed_public_pilot/profile_aggregate.csv")
CLEAN_PACKAGE_SUMMARY = Path("runs/m1615_contour_aware_candidate_corpus/summary.json")
ARTIFACT_FAILURE_SUMMARY = Path("runs/m1666_fusion_actor_artifact_replay_first_check/summary.json")


def profile_contract_violations(config: dict[str, Any]) -> list[str]:
    profile = dict(config.get("controller_profile") or {})
    env = dict(config.get("env") or {})
    violations: list[str] = []

    if profile.get("input_contract") != "P0_human_view_no_wheel_no_oracle":
        violations.append("input_contract_not_p0")
    for key in (
        "uses_hidden_oracle_actor_inputs",
        "uses_reference_or_ttc_inputs",
        "uses_wheel_or_slip_inputs",
        "private_holdout_used",
        "config_generation_only",
    ):
        if bool(profile.get(key, False)):
            violations.append(f"profile_{key}_true")
    if not bool(profile.get("corrected_profile_config", False)):
        violations.append("not_corrected_profile_config")
    if bool(env.get("include_privileged_params", False)):
        violations.append("env_include_privileged_params_true")
    if env.get("wheel_observation_mode") != "none":
        violations.append("env_wheel_observation_mode_not_none")
    if env.get("obstacle_relative_velocity_mode") != "zero":
        violations.append("obstacle_relative_velocity_mode_not_zero")
    return violations


def read_profile_aggregates(path: Path | str = STANDARD_AGGREGATE) -> list[dict[str, Any]]:
    aggregate_path = Path(path)
    if not aggregate_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with aggregate_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "profile_name": row["profile_name"],
                    "success": float(row["eval_success_rate_mean"]),
                    "collision": float(row["eval_collision_rate_mean"]),
                    "mean_margin": float(row["eval_clearance_margin_mean_mean"]),
                    "parameter_count": float(row["parameter_count_mean"]),
                    "is_main_profile": row["is_main_profile"] == "True",
                }
            )
    return rows


def build_controller_rows(config_dir: Path | str, config_glob: str) -> tuple[list[dict[str, Any]], list[str]]:
    paths = corrected_profile_config_paths(config_dir=config_dir, config_glob=config_glob)
    rows: list[dict[str, Any]] = []
    present_names: set[str] = set()
    for path in paths:
        config = read_json(path)
        profile = dict(config["controller_profile"])
        name = str(profile["name"])
        present_names.add(name)
        rows.append(
            {
                "profile_name": name,
                "config_path": str(path),
                "level": profile.get("level"),
                "actor_encoder": profile.get("actor_encoder"),
                "observation_dim": profile.get("observation_dim"),
                "window_steps": profile.get("window_steps"),
                "window_seconds": profile.get("window_seconds"),
                "uses_finite_window": bool(profile.get("uses_finite_window")),
                "uses_recurrent_hidden": bool(profile.get("uses_recurrent_hidden")),
                "current_tiled_history_control": bool(profile.get("current_tiled_history_control")),
                "corrected_reset_control": bool(profile.get("corrected_reset_control")),
                "reset_hidden_policy": profile.get("reset_hidden_policy"),
                "contract_violations": profile_contract_violations(config),
            }
        )
    missing = sorted(set(EXPECTED_PROFILE_NAMES) - present_names)
    return sorted(rows, key=lambda row: EXPECTED_PROFILE_NAMES.index(row["profile_name"])), missing


def build_matrix_protocol(
    *,
    controller_rows: list[dict[str, Any]],
    standard_summary: dict[str, Any],
    clean_summary: dict[str, Any],
    artifact_failure_summary: dict[str, Any],
    standard_aggregates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "protocol_name": "controller_family_decisive_evidence_matrix",
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "public protocol preflight only",
        "controller_families": controller_rows,
        "evidence_layers": {
            "standard_profile_baseline": {
                "source": str(STANDARD_SUMMARY),
                "aggregate_csv": str(STANDARD_AGGREGATE),
                "completed_seed_runs": standard_summary.get("completed_seed_runs"),
                "profile_count": standard_summary.get("profile_count"),
                "private_holdout_used": standard_summary.get("private_holdout_used"),
                "profile_specific_tuning": standard_summary.get("profile_specific_tuning"),
                "profile_aggregates": standard_aggregates,
            },
            "clean_active_set_package": {
                "source": str(CLEAN_PACKAGE_SUMMARY),
                "positive_candidate_count": clean_summary.get("positive_candidate_count"),
                "diagnostic_guardrail_count": clean_summary.get("diagnostic_guardrail_count"),
                "passes_public_smoke_gates": clean_summary.get("passes_public_smoke_gates"),
                "passes_evidence_quality_targets": clean_summary.get("passes_evidence_quality_targets"),
            },
            "artifact_route_regression_guardrail": {
                "source": str(ARTIFACT_FAILURE_SUMMARY),
                "first_check_pass": artifact_failure_summary.get("first_check_pass"),
                "m183_m170_first_check_pass": artifact_failure_summary.get("m183_m170_first_check_pass"),
                "m267_m264_first_check_pass": artifact_failure_summary.get("m267_m264_first_check_pass"),
                "proof_washout_count": artifact_failure_summary.get("proof_washout_count"),
                "behavior_regression_count": artifact_failure_summary.get("behavior_regression_count"),
            },
        },
        "stage_plan": [
            "stage0_protocol_preflight",
            "stage1_one_seed_public_plumbing_pilot",
            "stage2_three_seed_public_decisive_matrix",
            "stage3_source_diverse_holdout_design",
        ],
        "history_specific_comparisons": [
            "L2_normal_minus_L2_current_tiled",
            "L3_online_minus_L3_reset_control",
            "L3_online_minus_best_L2_normal",
            "L1_current_response_minus_history_families",
            "normal_history_minus_wrong_or_delayed_history_where_applicable",
        ],
        "claim_rules": {
            "reactive_negative": "C1 matches C2/C3 on decisive tasks",
            "finite_window_positive": "C2 normal beats current-tiled and matches or beats C3",
            "recurrent_advantage": "C3 beats best C2 and C3 reset on source-diverse decisive tasks",
            "strong_self_id": "source-diverse wrong/delayed history interventions degrade terminal outcomes",
        },
    }


def run_protocol_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    config_dir: Path | str = "configs/paper_route_corrected_profiles",
    config_glob: str = "m1207_*.json",
    standard_summary_path: Path | str = STANDARD_SUMMARY,
    clean_package_summary_path: Path | str = CLEAN_PACKAGE_SUMMARY,
    artifact_failure_summary_path: Path | str = ARTIFACT_FAILURE_SUMMARY,
    standard_aggregate_path: Path | str = STANDARD_AGGREGATE,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    controller_rows, missing_profiles = build_controller_rows(config_dir, config_glob)
    standard_summary = read_json(standard_summary_path)
    clean_summary = read_json(clean_package_summary_path)
    artifact_failure_summary = read_json(artifact_failure_summary_path)
    standard_aggregates = read_profile_aggregates(standard_aggregate_path)
    contract_violation_count = sum(len(row["contract_violations"]) for row in controller_rows)

    guardrail_flags = {
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "artifact_repair_started": False,
        "profile_specific_tuning_admitted": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        not missing_profiles
        and contract_violation_count == 0
        and bool(standard_summary.get("all_selected_profile_seed_runs_complete"))
        and bool(standard_summary.get("all_eval_metrics_finite"))
        and not bool(standard_summary.get("private_holdout_used"))
        and not bool(standard_summary.get("profile_specific_tuning"))
        and bool(clean_summary.get("passes_public_smoke_gates"))
        and bool(clean_summary.get("passes_evidence_quality_targets"))
        and bool(artifact_failure_summary.get("checkpoint_sanity_pass"))
        and not bool(artifact_failure_summary.get("first_check_pass"))
        and guardrail_violation_count == 0
    )

    protocol = build_matrix_protocol(
        controller_rows=controller_rows,
        standard_summary=standard_summary,
        clean_summary=clean_summary,
        artifact_failure_summary=artifact_failure_summary,
        standard_aggregates=standard_aggregates,
    )
    protocol.update({"missing_profiles": missing_profiles, "guardrail_flags": guardrail_flags})
    write_json(output / "matrix_protocol.json", protocol)

    summary = {
        "result_class": (
            "controller_family_decisive_matrix_protocol_preflight_pass"
            if passes
            else "controller_family_decisive_matrix_protocol_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "matrix_protocol": str(output / "matrix_protocol.json"),
        "profile_config_count": len(controller_rows),
        "expected_profile_count": len(EXPECTED_PROFILE_NAMES),
        "missing_profile_names": missing_profiles,
        "contract_violation_count": contract_violation_count,
        "standard_summary_readable": True,
        "standard_completed_seed_runs": standard_summary.get("completed_seed_runs"),
        "standard_profile_count": standard_summary.get("profile_count"),
        "standard_private_holdout_used": standard_summary.get("private_holdout_used"),
        "standard_profile_specific_tuning": standard_summary.get("profile_specific_tuning"),
        "clean_package_summary_readable": True,
        "clean_positive_candidate_count": clean_summary.get("positive_candidate_count"),
        "clean_diagnostic_guardrail_count": clean_summary.get("diagnostic_guardrail_count"),
        "artifact_failure_summary_readable": True,
        "artifact_first_check_pass": artifact_failure_summary.get("first_check_pass"),
        "artifact_proof_washout_count": artifact_failure_summary.get("proof_washout_count"),
        "artifact_behavior_regression_count": artifact_failure_summary.get("behavior_regression_count"),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "passes_public_smoke_gates": passes,
        "private_holdout_used": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "next_blocker": (
            "audit_protocol_preflight_before_one_seed_pilot"
            if passes
            else "repair_protocol_inputs_before_matrix_pilot"
        ),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--config-dir", type=Path, default=Path("configs/paper_route_corrected_profiles"))
    parser.add_argument("--config-glob", default="m1207_*.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_protocol_preflight(
        output_dir=args.output_dir,
        config_dir=args.config_dir,
        config_glob=args.config_glob,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"matrix_protocol={args.output_dir / 'matrix_protocol.json'}")
    return 0 if summary["passes_public_smoke_gates"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
