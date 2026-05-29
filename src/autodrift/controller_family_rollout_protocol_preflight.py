"""No-rollout protocol preflight for bounded controller-family task sources."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_task_source_generation_preflight import key_violations


DEFAULT_SPECS = Path("runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json")
DEFAULT_OUTPUT_DIR = Path("runs/m1683_controller_family_bounded_rollout_protocol_preflight")
EXPECTED_SPEC_COUNT = 72
EXPECTED_PROFILE_COUNT = len(EXPECTED_PROFILE_NAMES)
EXPECTED_WORKLOAD_CELLS = EXPECTED_SPEC_COUNT * EXPECTED_PROFILE_COUNT

METRIC_COLUMNS = (
    "success_rate",
    "collision_rate",
    "road_departure_rate",
    "spin_rate",
    "clearance_margin_mean",
    "clearance_margin_p10",
    "termination_reason_histogram",
    "control_smoothness",
    "L2_normal_minus_current_tiled_success_delta",
    "L2_normal_minus_current_tiled_margin_delta",
    "L3_online_minus_reset_success_delta",
    "L3_online_minus_reset_margin_delta",
)


def load_specs(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    return list(payload["task_source_specs"])


def stratum_membership(spec: dict[str, Any]) -> list[str]:
    strata = ["all_72_specs"]
    if spec["window_tag"] == "mapping_window_unspecified":
        strata.append("mapping_window_unspecified")
    else:
        strata.append("explicit_window_subset")
    strata.append(f"task_family_{spec['task_family']}")
    return strata


def build_workload_matrix(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        strata = stratum_membership(spec)
        for profile in EXPECTED_PROFILE_NAMES:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile}",
                    "task_source_id": spec["task_source_id"],
                    "profile_name": profile,
                    "task_family": spec["task_family"],
                    "source_edge": spec["source_edge"],
                    "window_tag": spec["window_tag"],
                    "strata": ";".join(strata),
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                }
            )
    return rows


def build_strata_summary(specs: list[dict[str, Any]]) -> dict[str, Any]:
    stratum_counts: Counter[str] = Counter()
    task_counter: Counter[str] = Counter()
    window_counter: Counter[str] = Counter()
    for spec in specs:
        task_counter[str(spec["task_family"])] += 1
        window_counter[str(spec["window_tag"])] += 1
        for stratum in stratum_membership(spec):
            stratum_counts[stratum] += 1
    return {
        "stratum_counts": dict(sorted(stratum_counts.items())),
        "task_family_counts": dict(sorted(task_counter.items())),
        "window_tag_counts": dict(sorted(window_counter.items())),
        "all_72_specs_count": stratum_counts["all_72_specs"],
        "explicit_window_subset_count": stratum_counts["explicit_window_subset"],
        "mapping_window_unspecified_count": stratum_counts["mapping_window_unspecified"],
    }


def run_rollout_protocol_preflight(
    *,
    specs_path: Path | str = DEFAULT_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_specs(specs_path)
    workload = build_workload_matrix(specs)
    strata = build_strata_summary(specs)
    violations = key_violations(specs)
    profile_names = sorted({row["profile_name"] for row in workload})
    spec_ids = sorted({row["task_source_id"] for row in workload})

    protocol = {
        "protocol_name": "controller_family_bounded_rollout_protocol_preflight",
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "no-rollout protocol preflight only",
        "specs_source": str(specs_path),
        "controller_profiles": list(EXPECTED_PROFILE_NAMES),
        "strata": {
            "primary": "all_72_specs",
            "diagnostic": "explicit_window_subset",
            **strata,
        },
        "metric_columns": list(METRIC_COLUMNS),
        "workload_matrix": str(output / "workload_matrix.csv"),
        "execution_policy": {
            "environment_rollout_started": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
            "private_holdout_used": False,
            "profile_specific_tuning": False,
        },
    }
    write_json(output / "rollout_protocol.json", protocol)
    write_csv_rows(output / "workload_matrix.csv", workload)

    guardrail_flags = {
        "environment_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "hidden_action_target_key_used": bool(violations),
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    coverage_passes = {
        "spec_count": len(specs) == EXPECTED_SPEC_COUNT,
        "profile_count": len(profile_names) == EXPECTED_PROFILE_COUNT,
        "workload_cell_count": len(workload) == EXPECTED_WORKLOAD_CELLS,
        "all_72_specs_present": strata["all_72_specs_count"] == EXPECTED_SPEC_COUNT,
        "explicit_window_subset_present": strata["explicit_window_subset_count"] > 0,
        "mapping_window_unspecified_present": strata["mapping_window_unspecified_count"] > 0,
        "metric_columns_present": len(METRIC_COLUMNS) >= 10,
    }
    passes = all(coverage_passes.values()) and not violations and guardrail_violation_count == 0
    summary = {
        "result_class": (
            "controller_family_bounded_rollout_protocol_preflight_pass"
            if passes
            else "controller_family_bounded_rollout_protocol_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "rollout_protocol": str(output / "rollout_protocol.json"),
        "workload_matrix": str(output / "workload_matrix.csv"),
        "spec_count": len(specs),
        "profile_count": len(profile_names),
        "workload_cell_count": len(workload),
        "expected_workload_cell_count": EXPECTED_WORKLOAD_CELLS,
        "coverage_passes": coverage_passes,
        **strata,
        "metric_columns": list(METRIC_COLUMNS),
        "hidden_action_target_key_violation_count": len(violations),
        "hidden_action_target_key_violations": violations,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "passes_public_smoke_gates": passes,
        "environment_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "level3_self_id_claim_made": False,
        "profile_names": profile_names,
        "task_source_ids_seen": len(spec_ids),
        "next_blocker": (
            "audit_rollout_protocol_preflight_before_execution_design"
            if passes
            else "repair_rollout_protocol_preflight_before_execution_design"
        ),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs", type=Path, default=DEFAULT_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_rollout_protocol_preflight(specs_path=args.specs, output_dir=args.output_dir)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"rollout_protocol={args.output_dir / 'rollout_protocol.json'}")
    print(f"workload_matrix={args.output_dir / 'workload_matrix.csv'}")
    return 0 if summary["passes_public_smoke_gates"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
