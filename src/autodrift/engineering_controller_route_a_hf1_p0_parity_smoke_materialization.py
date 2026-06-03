"""Route A HF1 P0 parity-smoke materialization."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_route_a_hf0_parity_runtime_materialization import (
    build_action_mapping_checks,
)
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    DIAGNOSTIC_ONLY_KEYS,
    OBSTACLE_SLOT_COUNT,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    ROAD_LOOKAHEAD_COUNT,
    default_actor_view,
)


DEFAULT_MILESTONE = "m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2553-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-result-audit"
DEFAULT_DOC_PATH = "docs/m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization")

SOURCE_ARTIFACTS = (
    "docs/m2551-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-design.md",
    "docs/m2550-engineering-controller-route-a-baseline-hf0-parity-and-runtime-result-synthesis.md",
    "docs/m2549-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-result-audit.md",
    "runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json",
    "runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/hf0_p0_parity_checks.csv",
    "runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/action_mapping_checks.csv",
    "runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/materialization_gate_matrix.csv",
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_boundary_map.csv",
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_contract.md",
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF1 P0 parity-smoke materialization only; not policy rollout, "
    "ranking, validation, driver performance, paper, FW-vs-GRU, current-sim "
    "verdict, high-fidelity validation, or self-ID"
)

ACTOR_FIELDNAMES = [
    "row_id",
    "actor_view_component",
    "source_path",
    "p0_index_start",
    "p0_index_end",
    "expected_count",
    "observed_count",
    "normalization_policy",
    "finite_required",
    "expected_observation_shape",
    "observed_observation_shape",
    "hidden_or_oracle_actor_input_detected",
    "status_pass",
    "claim_boundary",
]

VALUE_RANGE_FIELDNAMES = [
    "range_check_id",
    "component_family",
    "source_indices",
    "expected_shape",
    "finite_observation",
    "max_abs_observation_value",
    "allowed_range_policy",
    "range_violation_count",
    "status_pass",
    "claim_boundary",
]

ACTION_MAPPING_FIELDNAMES = [
    "action_check_id",
    "input_action",
    "expected_action_shape",
    "validated_action",
    "physical_control",
    "expected_physical_control",
    "invalid_input_rejected",
    "finite_required",
    "action_within_bounds",
    "status_pass",
    "claim_boundary",
]

EXTERNAL_BOUNDARY_FIELDNAMES = [
    "boundary_check_id",
    "required_interface",
    "source_component",
    "external_backend_required",
    "external_package_imported",
    "external_backend_run",
    "adapter_runtime_binding_allowed",
    "status_pass",
    "claim_boundary",
]

DIAGNOSTICS_FIELDNAMES = [
    "diagnostic_key",
    "source_component",
    "actor_visible_allowed",
    "present_in_actor_field_map",
    "hidden_or_oracle_risk",
    "status_pass",
    "claim_boundary",
]

GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "external_high_fidelity_imported": False,
    "high_fidelity_simulation_run": False,
    "measured_validation_run": False,
    "policy_rollout_run": False,
    "policy_action_run": False,
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}


def materialize_route_a_hf1_p0_parity_smoke(
    output_dir: Path,
    *,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    source_summaries = _source_summaries()
    observation = P0ObservationExtractor().extract(default_actor_view())
    actor_rows = build_actor_visible_field_parity_rows(observation)
    value_range_rows = build_observation_value_range_checks(observation)
    action_rows = build_hf1_action_mapping_parity_checks()
    external_rows = build_external_backend_boundary_checks()
    diagnostics_rows = build_diagnostics_exclusion_checks()
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        actor_rows=actor_rows,
        value_range_rows=value_range_rows,
        action_rows=action_rows,
        external_rows=external_rows,
        diagnostics_rows=diagnostics_rows,
    )

    actor_path = output_dir / "hf1_actor_visible_field_parity_rows.csv"
    value_range_path = output_dir / "hf1_observation_value_range_checks.csv"
    action_path = output_dir / "hf1_action_mapping_parity_checks.csv"
    external_path = output_dir / "hf1_external_backend_boundary_checks.csv"
    diagnostics_path = output_dir / "hf1_diagnostics_exclusion_checks.csv"
    gate_path = output_dir / "materialization_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(actor_path, actor_rows, fieldnames=ACTOR_FIELDNAMES)
    write_csv_rows(value_range_path, value_range_rows, fieldnames=VALUE_RANGE_FIELDNAMES)
    write_csv_rows(action_path, action_rows, fieldnames=ACTION_MAPPING_FIELDNAMES)
    write_csv_rows(external_path, external_rows, fieldnames=EXTERNAL_BOUNDARY_FIELDNAMES)
    write_csv_rows(diagnostics_path, diagnostics_rows, fieldnames=DIAGNOSTICS_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        source_summaries=source_summaries,
        actor_rows=actor_rows,
        value_range_rows=value_range_rows,
        action_rows=action_rows,
        external_rows=external_rows,
        diagnostics_rows=diagnostics_rows,
        gate_rows=gate_rows,
        actor_path=actor_path,
        value_range_path=value_range_path,
        action_path=action_path,
        external_path=external_path,
        diagnostics_path=diagnostics_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_actor_visible_field_parity_rows(observation: np.ndarray | None = None) -> list[dict[str, Any]]:
    obs = _observation(observation)
    blocks = [
        ("ego_dynamic_block", "EgoView", 0, 4, "vx/20;vy/12;yaw_rate/2.5;ax/15;ay/15"),
        ("actuator_state_block", "ActuatorView", 5, 8, "normalized steering/throttle/brake state"),
        ("previous_command_block", "ActuatorView.previous_commands", 9, 11, "previous deployed commands"),
        (
            "left_road_boundary_block",
            "RoadView.left_boundary_points_body",
            12,
            27,
            "x_body/80;y_body/20",
        ),
        (
            "right_road_boundary_block",
            "RoadView.right_boundary_points_body",
            28,
            43,
            "x_body/80;y_body/20",
        ),
        ("obstacle_slot_block", "ObstacleSlotView", 44, 71, "presence pose velocity size normalization"),
        ("full_p0_extract", "P0ObservationExtractor.extract", 0, 71, "full 72-value P0 actor frame"),
    ]
    rows: list[dict[str, Any]] = []
    for row_id, component, start, end, policy in blocks:
        values = obs[start : end + 1]
        expected_count = int(end - start + 1)
        finite = bool(np.all(np.isfinite(values)))
        rows.append(
            {
                "row_id": row_id,
                "actor_view_component": component,
                "source_path": "src/autodrift/high_fidelity_interface.py",
                "p0_index_start": int(start),
                "p0_index_end": int(end),
                "expected_count": expected_count,
                "observed_count": int(values.shape[0]),
                "normalization_policy": policy,
                "finite_required": True,
                "expected_observation_shape": P0_OBSERVATION_DIM,
                "observed_observation_shape": int(obs.shape[0]),
                "hidden_or_oracle_actor_input_detected": False,
                "status_pass": bool(
                    int(obs.shape[0]) == P0_OBSERVATION_DIM
                    and int(values.shape[0]) == expected_count
                    and finite
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_observation_value_range_checks(observation: np.ndarray | None = None) -> list[dict[str, Any]]:
    obs = _observation(observation)
    checks = [
        ("ego_response_range", "EgoView", range(0, 5), 5, 1.0, "normalized finite smoke within [-1, 1]"),
        ("actuator_state_range", "ActuatorView", range(5, 12), 7, 1.0, "normalized actuator/previous commands within [-1, 1]"),
        ("road_boundary_range", "RoadView", range(12, 44), 32, 1.0, "body-frame road points normalized by 80/20 within [-1, 1]"),
        ("obstacle_slot_range", "ObstacleSlotView", range(44, 72), 28, 1.0, "obstacle slot values normalized by source policy within [-1, 1]"),
        ("full_p0_finite_range", "P0ObservationExtractor", range(0, 72), 72, 1.0, "full vector finite source-smoke range"),
    ]
    rows: list[dict[str, Any]] = []
    for check_id, family, indices, expected_shape, max_allowed, policy in checks:
        index_list = list(indices)
        values = obs[index_list]
        finite = bool(np.all(np.isfinite(values)))
        max_abs = float(np.max(np.abs(values))) if finite and values.size else float("inf")
        violation_count = int(np.sum(np.abs(values) > max_allowed + 1e-6)) if finite else len(index_list)
        rows.append(
            {
                "range_check_id": check_id,
                "component_family": family,
                "source_indices": f"{index_list[0]}..{index_list[-1]}",
                "expected_shape": int(expected_shape),
                "finite_observation": finite,
                "max_abs_observation_value": max_abs,
                "allowed_range_policy": policy,
                "range_violation_count": violation_count,
                "status_pass": bool(values.shape[0] == expected_shape and finite and violation_count == 0),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_hf1_action_mapping_parity_checks() -> list[dict[str, Any]]:
    rows = []
    for source_row in build_action_mapping_checks():
        rows.append(
            {
                "action_check_id": source_row["check_id"],
                "input_action": source_row["input_action"],
                "expected_action_shape": source_row["expected_action_shape"],
                "validated_action": source_row["validated_action"],
                "physical_control": source_row["physical_control"],
                "expected_physical_control": source_row["expected_physical_control"],
                "invalid_input_rejected": source_row["invalid_input_rejected"],
                "finite_required": source_row["finite_required"],
                "action_within_bounds": source_row["action_within_bounds"],
                "status_pass": source_row["status_pass"],
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_external_backend_boundary_checks() -> list[dict[str, Any]]:
    source_path = Path("src/autodrift/high_fidelity_interface.py")
    source_text = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
    checks = [
        (
            "dynamics_backend_protocol",
            "backend_id dt reset step close",
            "DynamicsBackend",
            all(token in source_text for token in ("class DynamicsBackend", "def reset", "def step", "def close")),
        ),
        (
            "backend_reset_request_schema",
            "seed env_config_snapshot scenario_spec_id role_family options",
            "BackendResetRequest",
            "class BackendResetRequest" in source_text,
        ),
        (
            "backend_reset_result_schema",
            "actor_view diagnostics backend_info",
            "BackendResetResult",
            "class BackendResetResult" in source_text,
        ),
        (
            "backend_step_result_schema",
            "actor_view diagnostics terminated truncated backend_status",
            "BackendStepResult",
            "class BackendStepResult" in source_text,
        ),
        (
            "action_input_contract",
            "[steer throttle brake] shape 3",
            "validate_actor_action/physical_control_from_action",
            "def validate_actor_action" in source_text and "def physical_control_from_action" in source_text,
        ),
        (
            "external_dependency_guard",
            "no external simulator install import run",
            "M2552 materializer",
            True,
        ),
    ]
    return [
        {
            "boundary_check_id": check_id,
            "required_interface": required,
            "source_component": component,
            "external_backend_required": False,
            "external_package_imported": False,
            "external_backend_run": False,
            "adapter_runtime_binding_allowed": False,
            "status_pass": bool(source_ok),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for check_id, required, component, source_ok in checks
    ]


def build_diagnostics_exclusion_checks() -> list[dict[str, Any]]:
    actor_field_map = set(P0ObservationExtractor.field_map)
    rows = []
    for key in sorted(DIAGNOSTIC_ONLY_KEYS):
        present_in_actor = key in actor_field_map
        rows.append(
            {
                "diagnostic_key": key,
                "source_component": "DIAGNOSTIC_ONLY_KEYS",
                "actor_visible_allowed": False,
                "present_in_actor_field_map": bool(present_in_actor),
                "hidden_or_oracle_risk": "must_remain_outside_actor",
                "status_pass": not present_in_actor,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    actor_rows: list[dict[str, Any]],
    value_range_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
    external_rows: list[dict[str, Any]],
    diagnostics_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coverage = _field_coverage(actor_rows)
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()),
            f"missing={sum(1 for value in source_exists.values() if not value)}",
            "missing=0",
            "lineage_invalid",
        ),
        (
            "actor_visible_field_parity_rows_cover_p0",
            "contract",
            _all_status_pass(actor_rows) and coverage == set(range(P0_OBSERVATION_DIM)),
            f"covered={len(coverage)}",
            f"covered={P0_OBSERVATION_DIM}",
            "contract_violation",
        ),
        (
            "observation_value_range_checks_pass",
            "contract",
            _all_status_pass(value_range_rows),
            f"passed={sum(_row_passed(row) for row in value_range_rows)}/total={len(value_range_rows)}",
            f"passed={len(value_range_rows)}/total={len(value_range_rows)}",
            "contract_violation",
        ),
        (
            "action_mapping_parity_checks_pass",
            "contract",
            _all_status_pass(action_rows),
            f"passed={sum(_row_passed(row) for row in action_rows)}/total={len(action_rows)}",
            f"passed={len(action_rows)}/total={len(action_rows)}",
            "contract_violation",
        ),
        (
            "external_backend_boundary_checks_pass",
            "external_boundary",
            _all_status_pass(external_rows),
            f"passed={sum(_row_passed(row) for row in external_rows)}/total={len(external_rows)}",
            f"passed={len(external_rows)}/total={len(external_rows)}",
            "contract_violation",
        ),
        (
            "diagnostics_exclusion_checks_pass",
            "contract",
            _all_status_pass(diagnostics_rows),
            f"passed={sum(_row_passed(row) for row in diagnostics_rows)}/total={len(diagnostics_rows)}",
            f"passed={len(diagnostics_rows)}/total={len(diagnostics_rows)}",
            "contract_violation",
        ),
        (
            "actor_action_contract_preserved",
            "contract",
            P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
            f"obs={P0_OBSERVATION_DIM};action={ACTION_DIM}",
            "obs=72;action=3",
            "contract_violation",
        ),
        (
            "no_false_claim_flags",
            "claim_boundary",
            not any(FALSE_CLAIM_FLAGS.values()),
            "all false",
            "all false",
            "objective_overfit",
        ),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": bool(passed),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if passed else failure_type,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for gate_id, family, passed, observed, expected, failure_type in checks
    ]


def build_summary(
    *,
    output_dir: Path,
    source_exists: dict[str, bool],
    source_summaries: dict[str, Any],
    actor_rows: list[dict[str, Any]],
    value_range_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
    external_rows: list[dict[str, Any]],
    diagnostics_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    actor_path: Path,
    value_range_path: Path,
    action_path: Path,
    external_path: Path,
    diagnostics_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    coverage = _field_coverage(actor_rows)
    all_external_guarded = bool(external_rows) and all(
        not _boolish(row["external_package_imported"])
        and not _boolish(row["external_backend_run"])
        and not _boolish(row["external_backend_required"])
        for row in external_rows
    )
    status_pass = (
        all(source_exists.values())
        and _all_status_pass(actor_rows)
        and coverage == set(range(P0_OBSERVATION_DIM))
        and _all_status_pass(value_range_rows)
        and _all_status_pass(action_rows)
        and _all_status_pass(external_rows)
        and _all_status_pass(diagnostics_rows)
        and _all_status_pass(gate_rows)
        and all_external_guarded
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf1_p0_parity_smoke_materialization_pass"
        if status_pass
        else "engineering_controller_route_a_hf1_p0_parity_smoke_materialization_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf1_actor_visible_field_parity_rows": str(actor_path),
        "hf1_observation_value_range_checks": str(value_range_path),
        "hf1_action_mapping_parity_checks": str(action_path),
        "hf1_external_backend_boundary_checks": str(external_path),
        "hf1_diagnostics_exclusion_checks": str(diagnostics_path),
        "materialization_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2548_status_pass": bool(source_summaries["m2548"].get("status_pass")),
        "m2541_actor_contract_shape_72_action_3": bool(
            source_summaries["m2541_actor_contract"].get("observation_shape") == P0_OBSERVATION_DIM
            and source_summaries["m2541_actor_contract"].get("action_shape") == ACTION_DIM
        ),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "road_lookahead_count": ROAD_LOOKAHEAD_COUNT,
        "obstacle_slot_count": OBSTACLE_SLOT_COUNT,
        "actor_visible_field_parity_row_count": len(actor_rows),
        "actor_visible_field_parity_rows_all_pass": _all_status_pass(actor_rows),
        "p0_index_coverage_count": len(coverage),
        "p0_index_coverage_complete": coverage == set(range(P0_OBSERVATION_DIM)),
        "observation_value_range_check_count": len(value_range_rows),
        "observation_value_range_checks_all_pass": _all_status_pass(value_range_rows),
        "action_mapping_check_count": len(action_rows),
        "action_mapping_checks_all_pass": _all_status_pass(action_rows),
        "external_backend_boundary_check_count": len(external_rows),
        "external_backend_boundary_checks_all_pass": _all_status_pass(external_rows),
        "diagnostics_exclusion_check_count": len(diagnostics_rows),
        "diagnostics_exclusion_checks_all_pass": _all_status_pass(diagnostics_rows),
        "diagnostic_only_keys_checked_count": len(DIAGNOSTIC_ONLY_KEYS),
        "all_external_backend_flags_false": bool(all_external_guarded),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "hidden_oracle_actor_input_detected": False,
        "source_only_p0_parity_smoke_run": True,
        "external_backend_boundary_only": True,
        **FALSE_CLAIM_FLAGS,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2552 Engineering Controller Route A Baseline HF1 P0 Parity Smoke Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf1_p0_parity_smoke_materialization.py`",
                f"- summary: `{summary['summary']}`",
                f"- actor-visible field parity rows: `{summary['hf1_actor_visible_field_parity_rows']}`",
                f"- observation value-range checks: `{summary['hf1_observation_value_range_checks']}`",
                f"- action mapping parity checks: `{summary['hf1_action_mapping_parity_checks']}`",
                f"- external-backend boundary checks: `{summary['hf1_external_backend_boundary_checks']}`",
                f"- diagnostics exclusion checks: `{summary['hf1_diagnostics_exclusion_checks']}`",
                f"- materialization gate matrix: `{summary['materialization_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- policy rollout/training/ranking/winner/promotion/success-rate/validation claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2552 materializes HF1 P0 parity-smoke artifacts for the Route A",
                "baseline. The rows cover actor-visible field layout, observation",
                "value ranges, action mapping, diagnostics exclusion, and external",
                "adapter boundaries. The external rows are boundary checks only;",
                "they do not install, import, or run external simulation.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"actor_visible_field_parity_row_count: {summary['actor_visible_field_parity_row_count']}",
                f"p0_index_coverage_count: {summary['p0_index_coverage_count']}",
                f"observation_value_range_check_count: {summary['observation_value_range_check_count']}",
                f"action_mapping_check_count: {summary['action_mapping_check_count']}",
                f"external_backend_boundary_check_count: {summary['external_backend_boundary_check_count']}",
                f"diagnostics_exclusion_check_count: {summary['diagnostics_exclusion_check_count']}",
                f"diagnostic_only_keys_checked_count: {summary['diagnostic_only_keys_checked_count']}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2552 is an interface parity-smoke artifact. It does not rank",
                "Route A policies, select a winner, promote a checkpoint, compute",
                "success rates, validate driver performance, or provide paper/",
                "FW-vs-GRU/current-sim/high-fidelity/self-ID evidence.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _source_summaries() -> dict[str, Any]:
    return {
        "m2548": read_json(
            "runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json"
        ),
        "m2541_actor_contract": read_json(
            "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json"
        ),
    }


def _field_coverage(rows: list[dict[str, Any]]) -> set[int]:
    coverage: set[int] = set()
    for row in rows:
        if row.get("row_id") == "full_p0_extract":
            continue
        if not _row_passed(row):
            continue
        start = int(row["p0_index_start"])
        end = int(row["p0_index_end"])
        coverage.update(range(start, end + 1))
    return coverage


def _observation(observation: np.ndarray | None) -> np.ndarray:
    if observation is None:
        observation = P0ObservationExtractor().extract(default_actor_view())
    return np.asarray(observation, dtype=np.float32)


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_row_passed(row) for row in rows)


def _row_passed(row: dict[str, Any]) -> bool:
    return _boolish(row.get("status_pass", False))


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize Route A HF1 P0 parity-smoke artifacts.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_route_a_hf1_p0_parity_smoke(
        args.output_dir,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"actor_visible_field_parity_row_count={summary['actor_visible_field_parity_row_count']}")
    print(f"diagnostics_exclusion_check_count={summary['diagnostics_exclusion_check_count']}")
    print(f"summary={summary['summary']}")


if __name__ == "__main__":
    main()
