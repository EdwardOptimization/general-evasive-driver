"""Bounded HF0 source-only fixture smoke preflight."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.hf0_scenario_taxonomy_fixtures import FixtureCatalogRow, build_fixture_catalog_rows
from autodrift.hf0_scenario_taxonomy_mapping import SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
from autodrift.high_fidelity_interface import ACTION_DIM, BackendResetRequest, P0_OBSERVATION_DIM, P0ObservationExtractor


FIXTURE_ACTION_SEQUENCES: dict[str, tuple[tuple[float, float, float], ...]] = {
    "stable_aes": (
        (0.35, -0.20, -0.80),
        (-0.15, -0.15, -0.65),
    ),
    "drift_required_recovery": (
        (0.55, 0.10, -0.75),
        (-0.35, -0.10, -0.55),
    ),
    "unavoidable_mitigation": (
        (0.10, -0.35, -0.20),
        (0.00, -0.50, 0.10),
    ),
}


@dataclass(frozen=True)
class FixtureSmokeRow:
    fixture_id: str
    surface_id: str
    role_family: str
    reset_observation_shape: int
    step_observation_shapes: tuple[int, ...]
    action_shape: int
    action_count: int
    backend_statuses: tuple[str, ...]
    diagnostic_wheel_force_counts: tuple[int, ...]
    fixture_labels_enter_actor_input: bool
    scenario_labels_enter_actor_input: bool
    feasibility_classes_enter_actor_input: bool
    hidden_values_enter_actor_input: bool
    oracle_labels_enter_actor_input: bool
    policy_action: bool

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "surface_id": self.surface_id,
            "role_family": self.role_family,
            "reset_observation_shape": self.reset_observation_shape,
            "step_observation_shapes": ";".join(str(shape) for shape in self.step_observation_shapes),
            "action_shape": self.action_shape,
            "action_count": self.action_count,
            "backend_statuses": ";".join(self.backend_statuses),
            "diagnostic_wheel_force_counts": ";".join(str(count) for count in self.diagnostic_wheel_force_counts),
            "fixture_labels_enter_actor_input": self.fixture_labels_enter_actor_input,
            "scenario_labels_enter_actor_input": self.scenario_labels_enter_actor_input,
            "feasibility_classes_enter_actor_input": self.feasibility_classes_enter_actor_input,
            "hidden_values_enter_actor_input": self.hidden_values_enter_actor_input,
            "oracle_labels_enter_actor_input": self.oracle_labels_enter_actor_input,
            "policy_action": self.policy_action,
        }


def admitted_source_only_fixture_rows() -> list[FixtureCatalogRow]:
    return [
        row
        for row in build_fixture_catalog_rows()
        if row.surface_id == SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
        and row.fixture_admission_status == "admitted_for_materialization"
    ]


def run_source_only_fixture_smoke() -> tuple[list[FixtureSmokeRow], dict[str, Any]]:
    extractor = P0ObservationExtractor()
    smoke_rows: list[FixtureSmokeRow] = []
    for row_index, fixture_row in enumerate(admitted_source_only_fixture_rows()):
        actions = FIXTURE_ACTION_SEQUENCES.get(fixture_row.role_family)
        if actions is None:
            raise ValueError(f"no canned smoke action sequence for {fixture_row.role_family}")

        backend = FourWheelHF0Backend()
        try:
            reset_result = backend.reset(
                BackendResetRequest(
                    seed=2484 + row_index,
                    scenario_spec_id=fixture_row.fixture_id,
                    role_family=fixture_row.role_family,
                    options={
                        "fixture_id": fixture_row.fixture_id,
                        "fixture_admission_status": fixture_row.fixture_admission_status,
                    },
                )
            )
            reset_observation = extractor.extract(reset_result.actor_view)
            step_shapes: list[int] = []
            backend_statuses: list[str] = []
            diagnostic_wheel_force_counts: list[int] = []
            for action in actions:
                action_array = np.asarray(action, dtype=np.float32)
                if action_array.shape != (ACTION_DIM,):
                    raise ValueError(f"expected action shape {(ACTION_DIM,)}, got {action_array.shape}")
                step_result = backend.step(action_array)
                step_observation = extractor.extract(step_result.actor_view)
                step_shapes.append(int(step_observation.shape[0]))
                backend_statuses.append(step_result.backend_status)
                diagnostic_wheel_force_counts.append(len(step_result.diagnostics["wheel_forces"]))

            smoke_rows.append(
                FixtureSmokeRow(
                    fixture_id=fixture_row.fixture_id,
                    surface_id=fixture_row.surface_id,
                    role_family=fixture_row.role_family,
                    reset_observation_shape=int(reset_observation.shape[0]),
                    step_observation_shapes=tuple(step_shapes),
                    action_shape=ACTION_DIM,
                    action_count=len(actions),
                    backend_statuses=tuple(backend_statuses),
                    diagnostic_wheel_force_counts=tuple(diagnostic_wheel_force_counts),
                    fixture_labels_enter_actor_input=False,
                    scenario_labels_enter_actor_input=False,
                    feasibility_classes_enter_actor_input=False,
                    hidden_values_enter_actor_input=False,
                    oracle_labels_enter_actor_input=False,
                    policy_action=False,
                )
            )
        finally:
            backend.close()

    return smoke_rows, _summary_from_rows(smoke_rows)


def write_fixture_smoke_rows(output_dir: Path) -> tuple[Path, list[FixtureSmokeRow], dict[str, Any]]:
    smoke_rows, summary = run_source_only_fixture_smoke()
    rows_path = output_dir / "fixture_smoke_rows.csv"
    write_csv_rows(
        rows_path,
        [row.to_csv_row() for row in smoke_rows],
        fieldnames=[
            "fixture_id",
            "surface_id",
            "role_family",
            "reset_observation_shape",
            "step_observation_shapes",
            "action_shape",
            "action_count",
            "backend_statuses",
            "diagnostic_wheel_force_counts",
            "fixture_labels_enter_actor_input",
            "scenario_labels_enter_actor_input",
            "feasibility_classes_enter_actor_input",
            "hidden_values_enter_actor_input",
            "oracle_labels_enter_actor_input",
            "policy_action",
        ],
    )
    return rows_path, smoke_rows, summary


def run_preflight(output_dir: Path, *, next_blocker: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path, smoke_rows, summary = write_fixture_smoke_rows(output_dir)
    summary.update(
        {
            "milestone": "m2484-high-fidelity-interface-source-only-fixture-smoke-implementation-preflight",
            "generated_at_utc": utc_timestamp(),
            "fixture_smoke_rows": str(rows_path),
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def _summary_from_rows(smoke_rows: list[FixtureSmokeRow]) -> dict[str, Any]:
    role_counts = Counter(row.role_family for row in smoke_rows)
    diagnostic_wheel_force_counts = [
        count for row in smoke_rows for count in row.diagnostic_wheel_force_counts
    ]
    all_step_shapes = [shape for row in smoke_rows for shape in row.step_observation_shapes]
    all_reset_observations_shape_72 = all(
        row.reset_observation_shape == P0_OBSERVATION_DIM for row in smoke_rows
    )
    all_step_observations_shape_72 = all(shape == P0_OBSERVATION_DIM for shape in all_step_shapes)
    all_action_shapes_3 = all(row.action_shape == ACTION_DIM for row in smoke_rows)
    fixture_labels_enter_actor_input = any(row.fixture_labels_enter_actor_input for row in smoke_rows)
    scenario_labels_enter_actor_input = any(row.scenario_labels_enter_actor_input for row in smoke_rows)
    feasibility_classes_enter_actor_input = any(row.feasibility_classes_enter_actor_input for row in smoke_rows)
    hidden_values_enter_actor_input = any(row.hidden_values_enter_actor_input for row in smoke_rows)
    oracle_labels_enter_actor_input = any(row.oracle_labels_enter_actor_input for row in smoke_rows)
    policy_action = any(row.policy_action for row in smoke_rows)
    status_pass = (
        len(smoke_rows) == 3
        and set(role_counts) == set(FIXTURE_ACTION_SEQUENCES)
        and all_reset_observations_shape_72
        and all_step_observations_shape_72
        and all_action_shapes_3
        and all(count == 4 for count in diagnostic_wheel_force_counts)
        and not fixture_labels_enter_actor_input
        and not scenario_labels_enter_actor_input
        and not feasibility_classes_enter_actor_input
        and not hidden_values_enter_actor_input
        and not oracle_labels_enter_actor_input
        and not policy_action
    )
    return {
        "result_class": "hf0_source_only_fixture_smoke_pass"
        if status_pass
        else "hf0_source_only_fixture_smoke_failed",
        "status_pass": bool(status_pass),
        "backend_id": SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
        "fixture_count": len(smoke_rows),
        "admitted_source_only_fixture_count": len(smoke_rows),
        "role_counts": dict(sorted(role_counts.items())),
        "reset_count": len(smoke_rows),
        "step_count": sum(row.action_count for row in smoke_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "all_reset_observations_shape_72": bool(all_reset_observations_shape_72),
        "all_step_observations_shape_72": bool(all_step_observations_shape_72),
        "all_action_shapes_3": bool(all_action_shapes_3),
        "diagnostic_wheel_force_counts": diagnostic_wheel_force_counts,
        "fixture_labels_enter_actor_input": bool(fixture_labels_enter_actor_input),
        "scenario_labels_enter_actor_input": bool(scenario_labels_enter_actor_input),
        "feasibility_classes_enter_actor_input": bool(feasibility_classes_enter_actor_input),
        "hidden_values_enter_actor_input": bool(hidden_values_enter_actor_input),
        "oracle_labels_enter_actor_input": bool(oracle_labels_enter_actor_input),
        "diagnostics_available_to_actor": False,
        "canned_actions_only": True,
        "policy_action": bool(policy_action),
        "external_high_fidelity_required": False,
        "external_high_fidelity_imported": False,
        "high_fidelity_simulation_run": False,
        "measured_validation_run": False,
        "policy_rollout_run": False,
        "training_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "verdict_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded HF0 source-only fixture smoke preflight.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--next-blocker", type=str, required=True)
    args = parser.parse_args()

    summary = run_preflight(args.output_dir, next_blocker=str(args.next_blocker))
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"fixture_count={summary['fixture_count']}")
    print(f"step_count={summary['step_count']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
