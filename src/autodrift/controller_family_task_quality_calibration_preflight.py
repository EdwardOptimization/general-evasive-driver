"""No-rollout task-quality calibration matrix preflight."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    DEFAULT_OUTPUT_DIR as DEFAULT_M1690_OUTPUT_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract


DEFAULT_EXECUTABLE_SPECS = DEFAULT_M1690_OUTPUT_DIR / "executable_task_specs.json"
DEFAULT_OUTPUT_DIR = Path("runs/m1702_controller_family_task_quality_calibration_preflight")
TRACK_WIDTH_SCALES = (1.0, 1.5, 2.0)
FINISH_VARIANTS = ("original", "relaxed")
MAX_STEPS_SCALES = (1.0, 1.5)
EXPECTED_BASE_SPEC_COUNT = 72
EXPECTED_PROFILE_COUNT = 12


def load_executable_specs(path: Path | str = DEFAULT_EXECUTABLE_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return list(payload["executable_task_specs"])


def _relaxed_finish_pass_distance(value: float) -> float:
    return max(0.5, 0.5 * float(value))


def calibration_env_config(
    base_env_config: Mapping[str, Any],
    *,
    track_width_scale: float,
    finish_variant: str,
    max_steps_scale: float,
) -> dict[str, Any]:
    env = deepcopy(dict(base_env_config))
    env["track_width"] = float(env["track_width"]) * float(track_width_scale)
    env["max_steps"] = max(1, int(round(float(env["max_steps"]) * float(max_steps_scale))))
    obstacle = deepcopy(dict(env.get("obstacle") or {}))
    original_finish = float(obstacle.get("finish_pass_distance", 2.0))
    if finish_variant == "relaxed":
        obstacle["finish_pass_distance"] = _relaxed_finish_pass_distance(original_finish)
    elif finish_variant != "original":
        raise ValueError(f"unknown finish variant: {finish_variant}")
    env["obstacle"] = obstacle
    return env


def materialize_calibration_specs(
    executable_specs: list[Mapping[str, Any]],
    *,
    track_width_scales: tuple[float, ...] = TRACK_WIDTH_SCALES,
    finish_variants: tuple[str, ...] = FINISH_VARIANTS,
    max_steps_scales: tuple[float, ...] = MAX_STEPS_SCALES,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for spec in executable_specs:
        base_env = dict(spec["env_config"])
        for track_width_scale in track_width_scales:
            for finish_variant in finish_variants:
                for max_steps_scale in max_steps_scales:
                    env_config = calibration_env_config(
                        base_env,
                        track_width_scale=float(track_width_scale),
                        finish_variant=str(finish_variant),
                        max_steps_scale=float(max_steps_scale),
                    )
                    calibration_spec_id = (
                        f"{spec['task_source_id']}::tw{track_width_scale:g}"
                        f"::finish_{finish_variant}::max{max_steps_scale:g}"
                    )
                    violation_messages: list[str] = []
                    try:
                        assert_human_view_env_contract(build_env_config(env_config))
                    except Exception as exc:  # noqa: BLE001 - preflight must record all contract failures.
                        violation_messages.append(str(exc))
                    row = {
                        "calibration_spec_id": calibration_spec_id,
                        "base_task_source_id": str(spec["task_source_id"]),
                        "task_family": str(spec["task_family"]),
                        "source_edge": str(spec["source_edge"]),
                        "window_tag": str(spec["window_tag"]),
                        "executable_source_family": str(spec["executable_source_family"]),
                        "env_template_family": str(spec["env_template_family"]),
                        "track_width_scale": float(track_width_scale),
                        "finish_variant": str(finish_variant),
                        "max_steps_scale": float(max_steps_scale),
                        "track_width": float(env_config["track_width"]),
                        "finish_pass_distance": float(env_config["obstacle"]["finish_pass_distance"]),
                        "max_steps": int(env_config["max_steps"]),
                        "contract_violation_count": len(violation_messages),
                        "environment_rollout_scheduled": False,
                        "profile_specific_tuning": False,
                        "env_config": env_config,
                    }
                    rows.append(row)
                    for message in violation_messages:
                        violations.append(
                            {
                                "calibration_spec_id": calibration_spec_id,
                                "base_task_source_id": str(spec["task_source_id"]),
                                "violation": message,
                            }
                        )
    return rows, violations


def calibration_spec_csv_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "calibration_spec_id": row["calibration_spec_id"],
        "base_task_source_id": row["base_task_source_id"],
        "task_family": row["task_family"],
        "source_edge": row["source_edge"],
        "window_tag": row["window_tag"],
        "executable_source_family": row["executable_source_family"],
        "env_template_family": row["env_template_family"],
        "track_width_scale": row["track_width_scale"],
        "finish_variant": row["finish_variant"],
        "max_steps_scale": row["max_steps_scale"],
        "track_width": row["track_width"],
        "finish_pass_distance": row["finish_pass_distance"],
        "max_steps": row["max_steps"],
        "contract_violation_count": row["contract_violation_count"],
        "environment_rollout_scheduled": False,
        "profile_specific_tuning": False,
    }


def calibration_matrix_rows(
    calibration_specs: list[Mapping[str, Any]],
    *,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
) -> list[dict[str, Any]]:
    profiles = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in calibration_specs:
        for profile in profiles:
            rows.append(
                {
                    "calibration_workload_id": f"{spec['calibration_spec_id']}::{profile['profile_name']}",
                    "calibration_spec_id": spec["calibration_spec_id"],
                    "base_task_source_id": spec["base_task_source_id"],
                    "profile_name": profile["profile_name"],
                    "task_family": spec["task_family"],
                    "source_edge": spec["source_edge"],
                    "window_tag": spec["window_tag"],
                    "executable_source_family": spec["executable_source_family"],
                    "env_template_family": spec["env_template_family"],
                    "track_width_scale": spec["track_width_scale"],
                    "finish_variant": spec["finish_variant"],
                    "max_steps_scale": spec["max_steps_scale"],
                    "profile_config_path": profile["config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "config_exists": profile["config_exists"],
                    "checkpoint_exists": profile["checkpoint_exists"],
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                }
            )
    return rows


def run_calibration_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    executable_specs_path: Path | str = DEFAULT_EXECUTABLE_SPECS,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    executable_specs = load_executable_specs(executable_specs_path)
    calibration_specs, contract_violations = materialize_calibration_specs(executable_specs)
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    matrix_rows = calibration_matrix_rows(calibration_specs, m1674_run_dir=m1674_run_dir)
    missing_profile_artifact_count = sum(
        1 for row in profile_rows if not bool(row["config_exists"]) or not bool(row["checkpoint_exists"])
    )
    contract_violation_count = len(contract_violations)
    guardrail_flags = {
        "environment_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        len(executable_specs) == EXPECTED_BASE_SPEC_COUNT
        and len(profile_rows) == EXPECTED_PROFILE_COUNT
        and len(calibration_specs) == EXPECTED_BASE_SPEC_COUNT * len(TRACK_WIDTH_SCALES) * len(FINISH_VARIANTS) * len(MAX_STEPS_SCALES)
        and len(matrix_rows) == len(calibration_specs) * EXPECTED_PROFILE_COUNT
        and contract_violation_count == 0
        and missing_profile_artifact_count == 0
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "controller_family_task_quality_calibration_preflight_pass"
            if passes
            else "controller_family_task_quality_calibration_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "base_spec_count": len(executable_specs),
        "calibration_spec_count": len(calibration_specs),
        "profile_count": len(profile_rows),
        "calibration_matrix_cell_count": len(matrix_rows),
        "track_width_scales": list(TRACK_WIDTH_SCALES),
        "finish_variants": list(FINISH_VARIANTS),
        "max_steps_scales": list(MAX_STEPS_SCALES),
        "contract_violation_count": contract_violation_count,
        "missing_profile_artifact_count": missing_profile_artifact_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "passes_public_preflight_gates": bool(passes),
        "artifacts": {
            "summary": str(output / "summary.json"),
            "calibration_specs": str(output / "calibration_specs.json"),
            "calibration_specs_csv": str(output / "calibration_specs.csv"),
            "calibration_matrix": str(output / "calibration_matrix.csv"),
            "profile_artifacts": str(output / "profile_artifacts.csv"),
            "contract_violations": str(output / "contract_violations.csv"),
        },
        "next_blocker": "m1703-paper-route-controller-family-task-quality-calibration-preflight-result-audit",
    }
    write_json(
        output / "calibration_specs.json",
        {
            "generated_at_utc": summary["generated_at_utc"],
            "calibration_specs": calibration_specs,
        },
    )
    write_csv_rows(output / "calibration_specs.csv", [calibration_spec_csv_row(row) for row in calibration_specs])
    write_csv_rows(output / "calibration_matrix.csv", matrix_rows)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows)
    write_csv_rows(
        output / "contract_violations.csv",
        contract_violations,
        fieldnames=["calibration_spec_id", "base_task_source_id", "violation"],
    )
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-rollout controller-family calibration matrix.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    args = parser.parse_args()

    summary = run_calibration_preflight(
        output_dir=args.output_dir,
        executable_specs_path=args.executable_specs,
        m1674_run_dir=args.m1674_run_dir,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"calibration_spec_count={summary['calibration_spec_count']}")
    print(f"calibration_matrix_cell_count={summary['calibration_matrix_cell_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")


if __name__ == "__main__":
    main()
