"""R4-only metric-instrumented support diagnostic rerun wrapper."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_scenario_task_family_feasibility_calibration import (
    DEFAULT_SUPPORT_POLICIES,
    RolloutFunction,
    run_feasibility_calibration,
)


DEFAULT_BASE_CONFIG = Path("configs/paper_route_current_sim_scenario_task_family_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun")
DEFAULT_EVAL_SEED_BASE = 233000
DEFAULT_SEED_REPEATS = 5
DEFAULT_TARGET_SCENARIO_SPEC_COUNT = 12
DEFAULT_TARGET_SUPPORT_POLICY_COUNT = 3
DEFAULT_TARGET_EPISODE_COUNT = 180
DEFAULT_NEXT_BLOCKER = (
    "m2331-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-result-audit"
)
R4_ROLE_FAMILY = "R4_unavoidable_mitigation"
REQUIRED_R4_EXPORT_FIELDS = (
    "impact_speed_mps",
    "impact_speed_mps_available",
    "time_to_collision_s",
    "time_to_collision_s_available",
    "collision_side_proxy",
    "delta_v_at_impact_mps_available",
    "post_event_speed_mps_available",
    "recoverability_window_success_available",
    "impact_speed_proxy",
    "impact_beta_abs",
    "impact_yaw_rate_abs",
    "impact_severity_proxy",
    "collision_mitigation_score",
)
FIELD_COMPLETENESS_FIELDNAMES = [
    "field",
    "present_in_episode_rows",
    "nonempty_count",
    "true_count",
    "finite_count",
    "episode_count",
]


def read_csv_table(path: Path | str) -> tuple[list[dict[str, str]], list[str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return [], []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def _finite_value(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return bool(np.isfinite(number))


def materialize_r4_only_config(
    *,
    base_config: Path | str = DEFAULT_BASE_CONFIG,
    output_config: Path | str,
    target_scenario_spec_count: int = DEFAULT_TARGET_SCENARIO_SPEC_COUNT,
) -> dict[str, Any]:
    payload = read_json(base_config)
    specs = [dict(spec) for spec in payload.get("scenario_specs", [])]
    r4_specs = [spec for spec in specs if str(spec.get("role_family", "")) == R4_ROLE_FAMILY]
    if len(r4_specs) != int(target_scenario_spec_count):
        raise ValueError(f"expected {target_scenario_spec_count} R4 specs, got {len(r4_specs)}")
    output_payload = dict(payload)
    output_payload["scenario_specs"] = r4_specs
    output_payload["diagnostic_subset_role_family"] = R4_ROLE_FAMILY
    output_payload["diagnostic_only"] = True
    output_path = Path(output_config)
    write_json(output_path, output_payload)
    return {
        "base_scenario_spec_count": len(specs),
        "r4_scenario_spec_count": len(r4_specs),
        "r4_scenario_spec_ids": [str(spec.get("scenario_spec_id", "")) for spec in r4_specs],
        "r4_config": str(output_path),
    }


def metric_field_completeness_rows(
    *,
    episode_rows: Sequence[Mapping[str, Any]],
    episode_fieldnames: Sequence[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fieldset = set(episode_fieldnames)
    for field in REQUIRED_R4_EXPORT_FIELDS:
        values = [row.get(field, "") for row in episode_rows]
        rows.append(
            {
                "field": field,
                "present_in_episode_rows": field in fieldset,
                "nonempty_count": sum(str(value).strip() not in {"", "nan", "None"} for value in values),
                "true_count": sum(_bool_value(value) for value in values),
                "finite_count": sum(_finite_value(value) for value in values),
                "episode_count": len(episode_rows),
            }
        )
    return rows


def run_r4_metric_instrumented_support_diagnostic_rerun(
    *,
    base_config: Path | str = DEFAULT_BASE_CONFIG,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    support_policies: Sequence[str] = DEFAULT_SUPPORT_POLICIES,
    seed_repeats: int = DEFAULT_SEED_REPEATS,
    target_scenario_spec_count: int = DEFAULT_TARGET_SCENARIO_SPEC_COUNT,
    target_support_policy_count: int = DEFAULT_TARGET_SUPPORT_POLICY_COUNT,
    target_episode_count: int = DEFAULT_TARGET_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    rollout_fn: RolloutFunction | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    materialized = materialize_r4_only_config(
        base_config=base_config,
        output_config=output / "r4_only_config.json",
        target_scenario_spec_count=int(target_scenario_spec_count),
    )
    summary = dict(
        run_feasibility_calibration(
            config_path=output / "r4_only_config.json",
            output_dir=output,
            eval_seed_base=int(eval_seed_base),
            support_policies=tuple(str(policy) for policy in support_policies),
            seed_repeats=int(seed_repeats),
            target_scenario_spec_count=int(target_scenario_spec_count),
            target_support_policy_count=int(target_support_policy_count),
            target_episode_count=int(target_episode_count),
            next_blocker=str(next_blocker),
            rollout_fn=rollout_fn,
        )
    )
    episode_rows, episode_fieldnames = read_csv_table(output / "episode_rows.csv")
    field_rows = metric_field_completeness_rows(
        episode_rows=episode_rows,
        episode_fieldnames=episode_fieldnames,
    )
    write_csv_rows(output / "r4_metric_field_completeness.csv", field_rows, fieldnames=FIELD_COMPLETENESS_FIELDNAMES)
    missing_fields = [row["field"] for row in field_rows if not bool(row["present_in_episode_rows"])]
    non_r4_role_count = sum(str(row.get("role_family", "")) != R4_ROLE_FAMILY for row in episode_rows)
    base_result_class = str(summary.get("result_class", ""))
    guardrail_violation_count = int(summary.get("guardrail_violation_count", 0) or 0)
    wrapper_passes = (
        base_result_class.endswith("_pass")
        and len(episode_rows) == int(target_episode_count)
        and not missing_fields
        and non_r4_role_count == 0
        and guardrail_violation_count == 0
    )
    artifacts = dict(summary.get("artifacts", {}))
    artifacts.update(
        {
            "r4_only_config": str(output / "r4_only_config.json"),
            "r4_metric_field_completeness": str(output / "r4_metric_field_completeness.csv"),
        }
    )
    summary.update(
        {
            "result_class": (
                "current_sim_r4_metric_instrumented_support_diagnostic_rerun_pass"
                if wrapper_passes
                else "current_sim_r4_metric_instrumented_support_diagnostic_rerun_incomplete_or_fail"
            ),
            "base_result_class": base_result_class,
            "base_scenario_spec_count": int(materialized["base_scenario_spec_count"]),
            "r4_scenario_spec_count": int(materialized["r4_scenario_spec_count"]),
            "r4_scenario_spec_ids": materialized["r4_scenario_spec_ids"],
            "non_r4_role_count": int(non_r4_role_count),
            "required_r4_export_field_count": len(REQUIRED_R4_EXPORT_FIELDS),
            "required_r4_export_missing_field_count": len(missing_fields),
            "required_r4_export_missing_fields": missing_fields,
            "r4_metric_field_completeness_rows": len(field_rows),
            "support_policy_ranking_claim_made": False,
            "controller_family_ranking_claim_made": False,
            "winner_selected": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
            "residual_support_solved_claim_made": False,
            "mitigation_performance_claim_made": False,
            "artifacts": artifacts,
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-config", type=Path, default=DEFAULT_BASE_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--support-policies", nargs="+", default=list(DEFAULT_SUPPORT_POLICIES))
    parser.add_argument("--seed-repeats", type=int, default=DEFAULT_SEED_REPEATS)
    parser.add_argument("--target-scenario-spec-count", type=int, default=DEFAULT_TARGET_SCENARIO_SPEC_COUNT)
    parser.add_argument("--target-support-policy-count", type=int, default=DEFAULT_TARGET_SUPPORT_POLICY_COUNT)
    parser.add_argument("--target-episode-count", type=int, default=DEFAULT_TARGET_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_r4_metric_instrumented_support_diagnostic_rerun(
        base_config=args.base_config,
        output_dir=args.output_dir,
        eval_seed_base=int(args.eval_seed_base),
        support_policies=tuple(str(policy) for policy in args.support_policies),
        seed_repeats=int(args.seed_repeats),
        target_scenario_spec_count=int(args.target_scenario_spec_count),
        target_support_policy_count=int(args.target_support_policy_count),
        target_episode_count=int(args.target_episode_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"required_r4_export_missing_field_count={summary['required_r4_export_missing_field_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
