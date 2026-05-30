"""No-rollout executable workload materialization for controller-family profiles."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import env_config_to_dict
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.controller_family_rollout_protocol_preflight import stratum_membership
from autodrift.decisive_history_env_hooks import env_config_for_hook_spec
from autodrift.fresh_ambiguity_source_mining import FreshAmbiguitySourceSpec, default_source_specs


DEFAULT_TASK_SPECS = Path("runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json")
DEFAULT_WORKLOAD = Path("runs/m1683_controller_family_bounded_rollout_protocol_preflight/workload_matrix.csv")
DEFAULT_M1674_RUN_DIR = Path("runs/m1674_controller_family_one_seed_public_pilot")
DEFAULT_OUTPUT_DIR = Path("runs/m1690_controller_family_executable_workload_materialization_preflight")
TARGET_EXECUTABLE_SPECS = 72
TARGET_WORKLOAD_CELLS = TARGET_EXECUTABLE_SPECS * len(EXPECTED_PROFILE_NAMES)
FORBIDDEN_EXECUTABLE_KEY_FRAGMENTS = (
    "hidden_tensor",
    "action_tensor",
    "preferred_action",
    "rejected_action",
    "action_target",
    "actor_label",
)
DIRECT_EXECUTABLE_FAMILIES = {
    "t4_staged_warmup_capability",
    "t4_capability_step_temporal",
    "t4_actuator_delay_response",
    "t5_near_boundary_warmup",
    "t5_high_speed_close_obstacle",
    "t5_boundary_axis_retarget",
}
PROXY_ENV_TEMPLATE = {
    "capability_step_down": "t4_capability_step_temporal",
    "capability_step_up": "t4_capability_step_temporal",
    "actuator_delay_step": "t4_actuator_delay_response",
    "curved_boundary_obstacle": "t5_boundary_axis_retarget",
    "brake_fade_or_loss_proxy": "t5_near_boundary_warmup",
    "drive_loss_proxy": "t5_near_boundary_warmup",
    "grip_loss_proxy": "t5_near_boundary_warmup",
    "late_reveal_boundary": "t5_high_speed_close_obstacle",
}


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_spec_by_family() -> dict[str, FreshAmbiguitySourceSpec]:
    """Return public fresh/source metadata definitions keyed by source family."""

    return {spec.source_family: spec for spec in default_source_specs(seed=1680, seed_count=1)}


def source_family_task_map() -> dict[str, str]:
    return {family: spec.task_family for family, spec in source_spec_by_family().items()}


def choose_executable_source_family(spec: Mapping[str, Any], family_task: Mapping[str, str]) -> tuple[str, str]:
    """Choose the deterministic endpoint that should become executable."""

    task_family = str(spec["task_family"])
    endpoints = [str(spec["source_family_left"]), str(spec["source_family_right"])]
    for family in endpoints:
        if family_task.get(family) == task_family:
            return family, "task_family_matched_endpoint"
    for family in endpoints:
        if family in family_task:
            return family, "first_supported_endpoint"
    raise ValueError(f"no supported executable source endpoint for {spec['task_source_id']}: {endpoints}")


def _spec_index(spec: Mapping[str, Any]) -> int:
    seed = int(spec.get("generation_seed", 0))
    return abs(seed) % 9973


def source_attributes(source_family: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    """Derive deterministic capability/geometry/reveal metadata for one source."""

    source_specs = source_spec_by_family()
    if source_family not in source_specs:
        raise ValueError(f"unsupported source family: {source_family}")
    source_spec = source_specs[source_family]
    index = _spec_index(spec)
    pair_count = len(source_spec.hidden_capability_pairs)
    geometry_count = len(source_spec.geometry_keys)
    reveal_count = len(source_spec.reveal_steps)
    capability_pair = source_spec.hidden_capability_pairs[index % pair_count]
    geometry_key = source_spec.geometry_keys[(index // pair_count) % geometry_count]
    reveal_step = int(source_spec.reveal_steps[(index // (pair_count * geometry_count)) % reveal_count])
    decision_step = reveal_step + int(source_spec.decision_step_offset)
    executable_seed = int(spec.get("generation_seed", source_spec.seed_base + index))
    return {
        "executable_seed": executable_seed,
        "capability_pair": capability_pair,
        "geometry_key": geometry_key,
        "reveal_step": reveal_step,
        "decision_step": decision_step,
        "simulator_scope": source_spec.simulator_scope,
        "proxy_fault_family": bool(source_spec.proxy_fault_family),
    }


def env_template_family(source_family: str) -> tuple[str, str]:
    if source_family in DIRECT_EXECUTABLE_FAMILIES:
        return source_family, "direct_env_template"
    if source_family in PROXY_ENV_TEMPLATE:
        return PROXY_ENV_TEMPLATE[source_family], "proxy_env_template"
    raise ValueError(f"no env template for source family: {source_family}")


def forbidden_key_violations(rows: list[Mapping[str, Any]]) -> list[str]:
    violations: list[str] = []
    stack: list[tuple[str, Any]] = [(str(row.get("task_source_id", "unknown")), row) for row in rows]
    while stack:
        path, value = stack.pop()
        if isinstance(value, Mapping):
            for key, item in value.items():
                lowered = str(key).lower()
                if any(fragment in lowered for fragment in FORBIDDEN_EXECUTABLE_KEY_FRAGMENTS):
                    violations.append(f"{path}::{key}")
                stack.append((f"{path}.{key}", item))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                stack.append((f"{path}[{index}]", item))
    return sorted(violations)


def materialize_executable_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    family_task = source_family_task_map()
    source_family, endpoint_rule = choose_executable_source_family(spec, family_task)
    template_family, template_rule = env_template_family(source_family)
    attributes = source_attributes(source_family, spec)
    env_config = env_config_for_hook_spec(
        source_family=template_family,
        capability_pair=str(attributes["capability_pair"]),
        reveal_step=int(attributes["reveal_step"]),
    )
    assert_human_view_env_contract(env_config)
    env_dict = env_config_to_dict(env_config)
    contract_checks = {
        "history_length_is_one": int(env_config.history_length) == 1,
        "action_history_mode_full": env_config.action_history_mode == "full",
        "include_privileged_params_false": not bool(env_config.include_privileged_params),
        "wheel_observation_mode_none": env_config.wheel_observation_mode == "none",
        "obstacle_relative_velocity_mode_zero": env_config.obstacle_relative_velocity_mode == "zero",
    }
    return {
        "task_source_id": str(spec["task_source_id"]),
        "task_family": str(spec["task_family"]),
        "source_edge": str(spec["source_edge"]),
        "source_family_left": str(spec["source_family_left"]),
        "source_family_right": str(spec["source_family_right"]),
        "window_tag": str(spec["window_tag"]),
        "generation_seed": int(spec["generation_seed"]),
        "executable_source_family": source_family,
        "executable_seed": int(attributes["executable_seed"]),
        "capability_pair": str(attributes["capability_pair"]),
        "geometry_key": str(attributes["geometry_key"]),
        "reveal_step": int(attributes["reveal_step"]),
        "decision_step": int(attributes["decision_step"]),
        "simulator_scope": str(attributes["simulator_scope"]),
        "proxy_fault_family": bool(attributes["proxy_fault_family"]),
        "env_template_family": template_family,
        "materialization_rule": f"{endpoint_rule}+{template_rule}",
        "contract_checks": contract_checks,
        "contract_violation_count": sum(1 for value in contract_checks.values() if not bool(value)),
        "env_config": env_dict,
    }


def executable_spec_csv_row(spec: Mapping[str, Any]) -> dict[str, Any]:
    checks = dict(spec["contract_checks"])
    return {
        "task_source_id": spec["task_source_id"],
        "task_family": spec["task_family"],
        "source_edge": spec["source_edge"],
        "source_family_left": spec["source_family_left"],
        "source_family_right": spec["source_family_right"],
        "window_tag": spec["window_tag"],
        "generation_seed": spec["generation_seed"],
        "executable_source_family": spec["executable_source_family"],
        "executable_seed": spec["executable_seed"],
        "capability_pair": spec["capability_pair"],
        "geometry_key": spec["geometry_key"],
        "reveal_step": spec["reveal_step"],
        "decision_step": spec["decision_step"],
        "simulator_scope": spec["simulator_scope"],
        "proxy_fault_family": spec["proxy_fault_family"],
        "env_template_family": spec["env_template_family"],
        "materialization_rule": spec["materialization_rule"],
        "contract_violation_count": spec["contract_violation_count"],
        **checks,
    }


def profile_artifact_rows(
    *,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    profile_seed: int = 167400,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = Path(m1674_run_dir)
    for profile_name in EXPECTED_PROFILE_NAMES:
        config_path = root / "configs" / f"{profile_name}_seed{int(profile_seed)}.json"
        checkpoint_path = root / "profile_runs" / profile_name / f"seed_{int(profile_seed)}" / "checkpoint.pt"
        rows.append(
            {
                "profile_name": profile_name,
                "config_path": str(config_path),
                "checkpoint_path": str(checkpoint_path),
                "config_exists": config_path.exists(),
                "checkpoint_exists": checkpoint_path.exists(),
            }
        )
    return rows


def executable_workload_rows(
    executable_specs: list[Mapping[str, Any]],
    *,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
) -> list[dict[str, Any]]:
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in executable_specs:
        strata = ";".join(stratum_membership(spec))
        for profile in profile_rows:
            rows.append(
                {
                    "workload_id": f"{spec['task_source_id']}::{profile['profile_name']}",
                    "task_source_id": spec["task_source_id"],
                    "profile_name": profile["profile_name"],
                    "task_family": spec["task_family"],
                    "source_edge": spec["source_edge"],
                    "window_tag": spec["window_tag"],
                    "executable_source_family": spec["executable_source_family"],
                    "env_template_family": spec["env_template_family"],
                    "strata": strata,
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


def _counter_dict(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def run_materialization_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    task_specs_path: Path | str = DEFAULT_TASK_SPECS,
    workload_path: Path | str = DEFAULT_WORKLOAD,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    payload = read_json(task_specs_path)
    task_specs = list(payload["task_source_specs"])
    reference_workload = read_csv_rows(workload_path)

    executable_specs: list[dict[str, Any]] = []
    unmappable: list[dict[str, Any]] = []
    for spec in task_specs:
        try:
            executable_specs.append(materialize_executable_spec(spec))
        except Exception as exc:  # noqa: BLE001 - materialization preflight must record all blockers.
            unmappable.append(
                {
                    "task_source_id": str(spec.get("task_source_id", "unknown")),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )

    workload_rows = executable_workload_rows(executable_specs, m1674_run_dir=m1674_run_dir)
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    contract_violation_count = sum(int(spec["contract_violation_count"]) for spec in executable_specs)
    forbidden_key_hits = forbidden_key_violations(executable_specs)
    missing_profile_artifact_count = sum(
        1 for row in profile_rows if not bool(row["config_exists"]) or not bool(row["checkpoint_exists"])
    )
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
        len(executable_specs) == TARGET_EXECUTABLE_SPECS
        and len(workload_rows) == TARGET_WORKLOAD_CELLS
        and len(reference_workload) == TARGET_WORKLOAD_CELLS
        and not unmappable
        and contract_violation_count == 0
        and not forbidden_key_hits
        and missing_profile_artifact_count == 0
        and guardrail_violation_count == 0
    )

    executable_payload = {
        "protocol_name": "controller_family_executable_workload_materialization_preflight",
        "generated_at_utc": utc_timestamp(),
        "claim_scope": "no-rollout executable materialization only",
        "source_task_specs": str(task_specs_path),
        "source_workload_matrix": str(workload_path),
        "executable_task_specs": executable_specs,
    }
    summary = {
        "result_class": (
            "controller_family_executable_workload_materialization_preflight_pass"
            if passes
            else "controller_family_executable_workload_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "executable_spec_count": len(executable_specs),
        "target_executable_spec_count": TARGET_EXECUTABLE_SPECS,
        "source_task_spec_count": len(task_specs),
        "workload_cell_count": len(workload_rows),
        "target_workload_cell_count": TARGET_WORKLOAD_CELLS,
        "reference_workload_cell_count": len(reference_workload),
        "profile_count": len({row["profile_name"] for row in workload_rows}),
        "expected_profile_count": len(EXPECTED_PROFILE_NAMES),
        "task_family_counts": _counter_dict([str(spec["task_family"]) for spec in executable_specs]),
        "executable_source_family_counts": _counter_dict(
            [str(spec["executable_source_family"]) for spec in executable_specs]
        ),
        "env_template_family_counts": _counter_dict([str(spec["env_template_family"]) for spec in executable_specs]),
        "window_tag_counts": _counter_dict([str(spec["window_tag"]) for spec in executable_specs]),
        "unmappable_spec_count": len(unmappable),
        "unmappable_specs": unmappable,
        "contract_violation_count": contract_violation_count,
        "forbidden_key_violation_count": len(forbidden_key_hits),
        "forbidden_key_violations": forbidden_key_hits,
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
        "passes_public_smoke_gates": passes,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "executable_task_specs": str(output / "executable_task_specs.json"),
            "executable_task_specs_csv": str(output / "executable_task_specs.csv"),
            "executable_workload_matrix": str(output / "executable_workload_matrix.csv"),
            "profile_artifacts": str(output / "profile_artifacts.csv"),
            "unmappable_specs": str(output / "unmappable_specs.csv"),
        },
        "next_blocker": "m1691-paper-route-controller-family-executable-workload-materialization-result-audit",
    }

    write_json(output / "executable_task_specs.json", executable_payload)
    write_csv_rows(output / "executable_task_specs.csv", [executable_spec_csv_row(spec) for spec in executable_specs])
    write_csv_rows(output / "executable_workload_matrix.csv", workload_rows)
    write_csv_rows(output / "profile_artifacts.csv", profile_rows)
    write_csv_rows(output / "unmappable_specs.csv", unmappable)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-rollout executable workload materialization preflight.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--task-specs", type=Path, default=DEFAULT_TASK_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_WORKLOAD)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    args = parser.parse_args()

    summary = run_materialization_preflight(
        output_dir=args.output_dir,
        task_specs_path=args.task_specs,
        workload_path=args.workload,
        m1674_run_dir=args.m1674_run_dir,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"executable_spec_count={summary['executable_spec_count']}")
    print(f"workload_cell_count={summary['workload_cell_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
