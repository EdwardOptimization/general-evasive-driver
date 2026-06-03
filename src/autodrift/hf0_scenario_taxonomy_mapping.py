"""HF0 scenario taxonomy mapping materialization.

This module builds a machine-readable mapping between HF0 adapter surfaces and
scenario role families. It intentionally does not import or run any external
simulator and does not execute policy rollouts.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


CURRENT_SIM_SURFACE_ID = "current_sim_autodrift_hf0"
SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID = "source_only_four_wheel_hf0"

ROLE_FAMILIES = (
    "stable_avoidable",
    "stable_aes",
    "drift_required_recovery",
    "hidden_dynamics_robustness",
    "unavoidable_mitigation",
)

SUPPORT_STATUSES = frozenset({"supported", "limited_fixture", "blocked"})

ACTOR_VISIBLE_INPUTS = (
    "ego_kinematics_and_imu_like_response",
    "steering_throttle_brake_actuator_state",
    "previous_physical_commands",
    "ego_frame_road_boundary_geometry",
    "ego_frame_obstacle_geometry_and_relative_motion",
)

CURRENT_SIM_METADATA_ONLY_FIELDS = (
    "scenario_role_label",
    "feasibility_class",
    "obstacle_label",
    "friction_step_timing",
    "mu",
    "mass",
    "cg_shift",
    "tire_brake_drive_actuator_scales",
    "speed_ref",
    "beta_target",
    "path_error",
    "heading_error",
    "curvature",
    "ttc_or_stopping_clearance",
    "reward_terms",
    "success_or_termination_labels",
)

FOUR_WHEEL_METADATA_ONLY_FIELDS = (
    "scenario_role_label",
    "feasibility_class",
    "source_model_state",
    "vehicle_params",
    "fault_scales",
    "per_wheel_forces",
    "slip_load_like_force_details",
    "drag_and_rolling_forces",
    "fixture_role_labels",
    "reward_terms",
    "success_or_termination_labels",
)

FORBIDDEN_ACTOR_INPUT_TOKENS = frozenset(
    {
        "scenario_role_label",
        "role_family",
        "feasibility_class",
        "aeb_feasible",
        "aes_feasible",
        "unavoidable",
        "mu",
        "mass",
        "cg_shift",
        "tire_stiffness",
        "brake_scale",
        "drive_scale",
        "actuator_tau",
        "wheel_force",
        "slip",
        "load",
        "fault_scale",
        "speed_ref",
        "beta_target",
        "path_error",
        "heading_error",
        "curvature",
        "ttc",
        "stopping_distance",
        "required_clearance",
        "reward_terms",
        "success_label",
        "termination_label",
        "oracle",
    }
)


@dataclass(frozen=True)
class SurfaceRoleRow:
    surface_id: str
    role_family: str
    support_status: str
    actor_observation_shape: int
    action_shape: int
    actor_visible_inputs: tuple[str, ...]
    metadata_only_fields: tuple[str, ...]
    blocked_reason: str
    next_fixture_requirement: str

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "role_family": self.role_family,
            "support_status": self.support_status,
            "actor_observation_shape": self.actor_observation_shape,
            "action_shape": self.action_shape,
            "actor_visible_inputs": ";".join(self.actor_visible_inputs),
            "metadata_only_fields": ";".join(self.metadata_only_fields),
            "blocked_reason": self.blocked_reason,
            "next_fixture_requirement": self.next_fixture_requirement,
        }


def build_surface_role_rows() -> list[SurfaceRoleRow]:
    """Return the M2480 HF0 surface-role matrix rows."""

    rows: list[SurfaceRoleRow] = []
    current_sim_status = {
        "stable_avoidable": (
            "supported",
            "",
            "reuse current-sim stable avoidable fixtures as baseline safety-control rows",
        ),
        "stable_aes": (
            "limited_fixture",
            "stable-AES reset-ready support remains partial in current-sim distribution evidence",
            "keep stable-AES rows as bounded fixtures until reset-readiness is synthesis-approved",
        ),
        "drift_required_recovery": (
            "supported",
            "",
            "map existing handling-limit current-sim tasks into drift-required recovery metadata",
        ),
        "hidden_dynamics_robustness": (
            "supported",
            "",
            "map hidden-parameter variants as diagnostics-only robustness metadata",
        ),
        "unavoidable_mitigation": (
            "limited_fixture",
            "unavoidable verdict is oracle metadata and cannot be inferred by the actor",
            "design mitigation fixtures with metadata-only feasibility labels before any pilot",
        ),
    }
    four_wheel_status = {
        "stable_avoidable": (
            "supported",
            "",
            "reuse deterministic obstacle fixture with P0 actor extraction",
        ),
        "stable_aes": (
            "limited_fixture",
            "source-only four-wheel adapter has deterministic road and obstacle fixtures only",
            "add bounded evasive-steering fixture rows without exposing feasibility labels",
        ),
        "drift_required_recovery": (
            "limited_fixture",
            "source-only four-wheel model exposes richer dynamics but lacks role-specific recovery fixtures",
            "add recovery fixture families using diagnostics-only wheel force evidence",
        ),
        "hidden_dynamics_robustness": (
            "supported",
            "",
            "vary fault scales and vehicle params as diagnostics-only hidden dynamics metadata",
        ),
        "unavoidable_mitigation": (
            "limited_fixture",
            "source-only four-wheel adapter lacks mitigation-specific scenario fixtures",
            "add mitigation fixture rows with oracle feasibility kept out of actor input",
        ),
    }

    for role in ROLE_FAMILIES:
        status, reason, requirement = current_sim_status[role]
        rows.append(
            SurfaceRoleRow(
                surface_id=CURRENT_SIM_SURFACE_ID,
                role_family=role,
                support_status=status,
                actor_observation_shape=P0_OBSERVATION_DIM,
                action_shape=ACTION_DIM,
                actor_visible_inputs=ACTOR_VISIBLE_INPUTS,
                metadata_only_fields=CURRENT_SIM_METADATA_ONLY_FIELDS,
                blocked_reason=reason,
                next_fixture_requirement=requirement,
            )
        )

    for role in ROLE_FAMILIES:
        status, reason, requirement = four_wheel_status[role]
        rows.append(
            SurfaceRoleRow(
                surface_id=SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
                role_family=role,
                support_status=status,
                actor_observation_shape=P0_OBSERVATION_DIM,
                action_shape=ACTION_DIM,
                actor_visible_inputs=ACTOR_VISIBLE_INPUTS,
                metadata_only_fields=FOUR_WHEEL_METADATA_ONLY_FIELDS,
                blocked_reason=reason,
                next_fixture_requirement=requirement,
            )
        )

    validate_surface_role_rows(rows)
    return rows


def validate_surface_role_rows(rows: list[SurfaceRoleRow]) -> None:
    if not rows:
        raise ValueError("surface role matrix is empty")

    seen_by_surface: dict[str, set[str]] = {}
    for row in rows:
        if row.surface_id not in {CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID}:
            raise ValueError(f"unknown surface_id {row.surface_id}")
        if row.role_family not in ROLE_FAMILIES:
            raise ValueError(f"unknown role_family {row.role_family}")
        if row.support_status not in SUPPORT_STATUSES:
            raise ValueError(f"unknown support_status {row.support_status}")
        if row.actor_observation_shape != P0_OBSERVATION_DIM:
            raise ValueError(
                f"{row.surface_id}/{row.role_family} changed observation shape to "
                f"{row.actor_observation_shape}"
            )
        if row.action_shape != ACTION_DIM:
            raise ValueError(f"{row.surface_id}/{row.role_family} changed action shape to {row.action_shape}")

        actor_tokens = set(row.actor_visible_inputs)
        leaked = sorted(actor_tokens.intersection(FORBIDDEN_ACTOR_INPUT_TOKENS))
        if leaked:
            raise ValueError(f"{row.surface_id}/{row.role_family} leaks metadata to actor inputs: {leaked}")

        metadata_tokens = set(row.metadata_only_fields)
        for required in ("scenario_role_label", "feasibility_class"):
            if required not in metadata_tokens:
                raise ValueError(f"{row.surface_id}/{row.role_family} missing metadata-only {required}")

        seen_by_surface.setdefault(row.surface_id, set()).add(row.role_family)

    expected_roles = set(ROLE_FAMILIES)
    for surface_id in (CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID):
        missing = sorted(expected_roles - seen_by_surface.get(surface_id, set()))
        if missing:
            raise ValueError(f"{surface_id} missing role rows: {missing}")


def write_surface_role_matrix(output_dir: Path) -> tuple[Path, list[SurfaceRoleRow]]:
    rows = build_surface_role_rows()
    matrix_path = output_dir / "surface_role_matrix.csv"
    write_csv_rows(
        matrix_path,
        [row.to_csv_row() for row in rows],
        fieldnames=[
            "surface_id",
            "role_family",
            "support_status",
            "actor_observation_shape",
            "action_shape",
            "actor_visible_inputs",
            "metadata_only_fields",
            "blocked_reason",
            "next_fixture_requirement",
        ],
    )
    return matrix_path, rows


def run_mapping_preflight(output_dir: Path, *, next_blocker: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_path, rows = write_surface_role_matrix(output_dir)
    support_counts = Counter(row.support_status for row in rows)
    surfaces = sorted({row.surface_id for row in rows})
    actor_metadata_leaks = _actor_metadata_leaks(rows)
    all_rows_preserve_observation_shape = all(row.actor_observation_shape == P0_OBSERVATION_DIM for row in rows)
    all_rows_preserve_action_shape = all(row.action_shape == ACTION_DIM for row in rows)
    scenario_labels_enter_actor_input = any("scenario_role_label" in row.actor_visible_inputs for row in rows)
    feasibility_classes_enter_actor_input = any("feasibility_class" in row.actor_visible_inputs for row in rows)
    hidden_values_enter_actor_input = any(actor_metadata_leaks.values())
    oracle_labels_enter_actor_input = any(
        token in actor_token
        for row in rows
        for actor_token in row.actor_visible_inputs
        for token in ("oracle", "unavoidable", "required_clearance", "ttc")
    )
    status_pass = (
        len(rows) == 10
        and surfaces == [CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID]
        and set(ROLE_FAMILIES) == {row.role_family for row in rows}
        and all_rows_preserve_observation_shape
        and all_rows_preserve_action_shape
        and not scenario_labels_enter_actor_input
        and not feasibility_classes_enter_actor_input
        and not hidden_values_enter_actor_input
        and not oracle_labels_enter_actor_input
    )

    summary = {
        "milestone": "m2480-high-fidelity-interface-scenario-taxonomy-mapping-materialization-preflight",
        "generated_at_utc": utc_timestamp(),
        "result_class": "hf0_scenario_taxonomy_mapping_materialization_pass"
        if status_pass
        else "hf0_scenario_taxonomy_mapping_materialization_failed",
        "status_pass": bool(status_pass),
        "surface_count": len(surfaces),
        "surfaces": surfaces,
        "role_count": len(ROLE_FAMILIES),
        "roles": list(ROLE_FAMILIES),
        "row_count": len(rows),
        "support_status_counts": dict(sorted(support_counts.items())),
        "actor_observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "all_rows_preserve_observation_shape": bool(all_rows_preserve_observation_shape),
        "all_rows_preserve_action_shape": bool(all_rows_preserve_action_shape),
        "scenario_labels_enter_actor_input": bool(scenario_labels_enter_actor_input),
        "feasibility_classes_enter_actor_input": bool(feasibility_classes_enter_actor_input),
        "hidden_values_enter_actor_input": bool(hidden_values_enter_actor_input),
        "oracle_labels_enter_actor_input": bool(oracle_labels_enter_actor_input),
        "actor_metadata_leaks": actor_metadata_leaks,
        "metadata_only_fields_checked": sorted(
            {field for row in rows for field in row.metadata_only_fields}
        ),
        "surface_role_matrix": str(matrix_path),
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
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def _actor_metadata_leaks(rows: list[SurfaceRoleRow]) -> dict[str, list[str]]:
    leaks: dict[str, list[str]] = {}
    for row in rows:
        actor_tokens = set(row.actor_visible_inputs)
        leaked_tokens = sorted(actor_tokens.intersection(FORBIDDEN_ACTOR_INPUT_TOKENS))
        if leaked_tokens:
            leaks[f"{row.surface_id}:{row.role_family}"] = leaked_tokens
    return leaks


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize HF0 scenario taxonomy mapping.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--next-blocker", type=str, required=True)
    args = parser.parse_args()

    summary = run_mapping_preflight(args.output_dir, next_blocker=str(args.next_blocker))
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"row_count={summary['row_count']}")
    print(f"surface_role_matrix={summary['surface_role_matrix']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
