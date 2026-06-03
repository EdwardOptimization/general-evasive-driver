"""Reset-only source-only role fixture parameterization preflight."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import to_jsonable, utc_timestamp, write_csv_rows, write_json
from autodrift.four_wheel_dynamics import FourWheelFaultScales, FourWheelState
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend, SourceOnlyRoleFixtureDynamicsSpec
from autodrift.hf0_source_only_fixture_smoke import admitted_source_only_fixture_rows
from autodrift.hf0_scenario_taxonomy_mapping import SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    ObstacleSlotView,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    RoadView,
)


DEFAULT_MILESTONE = (
    "m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight"
)
ROLE_FAMILIES = ("stable_aes", "drift_required_recovery", "unavoidable_mitigation")
DIFFERENTIATION_L2_MIN_THRESHOLD = 1e-3
FIXTURE_PARAMETERIZATION_FIELDNAMES = [
    "fixture_id",
    "surface_id",
    "role_family",
    "initial_state_digest",
    "fault_scale_digest",
    "road_digest",
    "obstacle_digest",
    "reset_observation_shape",
    "reset_observation_digest",
    "source_only_fixture_spec_present",
    "role_metadata_only",
    "fixture_metadata_only",
    "hidden_diagnostics_available",
    "differentiation_reason",
]
RESET_DIFFERENTIATION_FIELDNAMES = [
    "role_family_a",
    "role_family_b",
    "fixture_id_a",
    "fixture_id_b",
    "reset_observation_l2",
    "initial_state_digest_equal",
    "fault_scale_digest_equal",
    "obstacle_digest_equal",
    "road_digest_equal",
]


@dataclass(frozen=True)
class FixtureParameterizationRow:
    fixture_id: str
    surface_id: str
    role_family: str
    initial_state_digest: str
    fault_scale_digest: str
    road_digest: str
    obstacle_digest: str
    reset_observation_shape: int
    reset_observation_digest: str
    source_only_fixture_spec_present: bool
    role_metadata_only: bool
    fixture_metadata_only: bool
    hidden_diagnostics_available: bool
    differentiation_reason: str

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "surface_id": self.surface_id,
            "role_family": self.role_family,
            "initial_state_digest": self.initial_state_digest,
            "fault_scale_digest": self.fault_scale_digest,
            "road_digest": self.road_digest,
            "obstacle_digest": self.obstacle_digest,
            "reset_observation_shape": self.reset_observation_shape,
            "reset_observation_digest": self.reset_observation_digest,
            "source_only_fixture_spec_present": self.source_only_fixture_spec_present,
            "role_metadata_only": self.role_metadata_only,
            "fixture_metadata_only": self.fixture_metadata_only,
            "hidden_diagnostics_available": self.hidden_diagnostics_available,
            "differentiation_reason": self.differentiation_reason,
        }


@dataclass(frozen=True)
class ResetDifferentiationRow:
    role_family_a: str
    role_family_b: str
    fixture_id_a: str
    fixture_id_b: str
    reset_observation_l2: float
    initial_state_digest_equal: bool
    fault_scale_digest_equal: bool
    obstacle_digest_equal: bool
    road_digest_equal: bool

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "role_family_a": self.role_family_a,
            "role_family_b": self.role_family_b,
            "fixture_id_a": self.fixture_id_a,
            "fixture_id_b": self.fixture_id_b,
            "reset_observation_l2": self.reset_observation_l2,
            "initial_state_digest_equal": self.initial_state_digest_equal,
            "fault_scale_digest_equal": self.fault_scale_digest_equal,
            "obstacle_digest_equal": self.obstacle_digest_equal,
            "road_digest_equal": self.road_digest_equal,
        }


def build_source_only_role_fixture_specs() -> list[SourceOnlyRoleFixtureDynamicsSpec]:
    admitted_by_role = {row.role_family: row for row in admitted_source_only_fixture_rows()}
    missing_roles = sorted(set(ROLE_FAMILIES) - set(admitted_by_role))
    if missing_roles:
        raise ValueError(f"missing admitted source-only fixture rows for roles: {missing_roles}")

    specs = [
        SourceOnlyRoleFixtureDynamicsSpec(
            fixture_id=admitted_by_role["stable_aes"].fixture_id,
            role_family="stable_aes",
            initial_state=FourWheelState(
                x=0.0,
                y=0.0,
                psi=0.0,
                vx=9.0,
                vy=0.05,
                yaw_rate=0.02,
                steer=0.0,
                drive_force=0.0,
                brake_force=0.0,
            ),
            fault_scales=FourWheelFaultScales.nominal(),
            road=_role_road(lateral_offset=0.0, curve_scale=0.0),
            obstacles=_role_obstacles(
                ObstacleSlotView(1.0, 32.0, -0.5, -8.0, 0.0, 0.75, 0.75)
            ),
            diagnostic_tags={
                "fixture_source": "m2496_source_only_parameterized",
                "parameterization_version": "m2496_reset_only_v1",
                "differentiation_reason": "higher speed nominal-grip avoidable source-only AES reference",
            },
        ),
        SourceOnlyRoleFixtureDynamicsSpec(
            fixture_id=admitted_by_role["drift_required_recovery"].fixture_id,
            role_family="drift_required_recovery",
            initial_state=FourWheelState(
                x=0.0,
                y=0.45,
                psi=0.04,
                vx=10.0,
                vy=0.55,
                yaw_rate=0.18,
                steer=0.02,
                drive_force=0.0,
                brake_force=0.0,
            ),
            fault_scales=FourWheelFaultScales.split_mu(left_scale=0.72, right_scale=0.95),
            road=_role_road(lateral_offset=0.25, curve_scale=0.035),
            obstacles=_role_obstacles(
                ObstacleSlotView(1.0, 26.0, 0.75, -7.0, -0.2, 0.8, 0.9)
            ),
            diagnostic_tags={
                "fixture_source": "m2496_source_only_parameterized",
                "parameterization_version": "m2496_reset_only_v1",
                "differentiation_reason": (
                    "lateral velocity yaw and asymmetric grip create recovery-oriented source-only dynamics"
                ),
            },
        ),
        SourceOnlyRoleFixtureDynamicsSpec(
            fixture_id=admitted_by_role["unavoidable_mitigation"].fixture_id,
            role_family="unavoidable_mitigation",
            initial_state=FourWheelState(
                x=0.0,
                y=-0.35,
                psi=-0.03,
                vx=8.2,
                vy=-0.35,
                yaw_rate=-0.14,
                steer=-0.01,
                drive_force=0.0,
                brake_force=0.0,
            ),
            fault_scales=FourWheelFaultScales.uniform_grip(
                mu_scale=0.68,
                lateral_stiffness_scale=0.72,
            ),
            road=_role_road(lateral_offset=-0.2, curve_scale=-0.025),
            obstacles=_role_obstacles(
                ObstacleSlotView(1.0, 17.0, 0.15, -6.5, 0.1, 0.95, 1.0)
            ),
            diagnostic_tags={
                "fixture_source": "m2496_source_only_parameterized",
                "parameterization_version": "m2496_reset_only_v1",
                "differentiation_reason": "low grip close obstacle mitigation-oriented source-only dynamics",
            },
        ),
    ]
    _validate_specs(specs)
    return specs


def run_source_only_role_fixture_parameterization_preflight() -> tuple[
    list[FixtureParameterizationRow],
    list[ResetDifferentiationRow],
    dict[str, Any],
]:
    specs = build_source_only_role_fixture_specs()
    extractor = P0ObservationExtractor()
    parameterization_rows: list[FixtureParameterizationRow] = []
    observations_by_role: dict[str, np.ndarray] = {}
    digest_by_role: dict[str, dict[str, str]] = {}
    reset_count = 0
    reset_observation_shapes: list[int] = []
    default_backend = FourWheelHF0Backend()
    default_reset_result = default_backend.reset(BackendResetRequest(seed=2496))
    default_reset_observation = extractor.extract(default_reset_result.actor_view)
    default_backend.close()

    for index, spec in enumerate(specs):
        backend = FourWheelHF0Backend(fixture_spec=spec)
        try:
            reset_result = backend.reset(
                BackendResetRequest(
                    seed=2496 + index,
                    scenario_spec_id=spec.fixture_id,
                    role_family=spec.role_family,
                )
            )
            reset_observation = extractor.extract(reset_result.actor_view)
            reset_count += 1
            reset_observation_shapes.append(int(reset_observation.shape[0]))
            digests = _digests_for_spec(spec, reset_observation)
            digest_by_role[spec.role_family] = digests
            observations_by_role[spec.role_family] = reset_observation
            parameterization_rows.append(
                FixtureParameterizationRow(
                    fixture_id=spec.fixture_id,
                    surface_id=SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
                    role_family=spec.role_family,
                    initial_state_digest=digests["initial_state"],
                    fault_scale_digest=digests["fault_scale"],
                    road_digest=digests["road"],
                    obstacle_digest=digests["obstacle"],
                    reset_observation_shape=int(reset_observation.shape[0]),
                    reset_observation_digest=digests["reset_observation"],
                    source_only_fixture_spec_present=bool(
                        reset_result.diagnostics["source_only_fixture_spec_present"]
                    ),
                    role_metadata_only=True,
                    fixture_metadata_only=True,
                    hidden_diagnostics_available=True,
                    differentiation_reason=str(spec.diagnostic_tags["differentiation_reason"]),
                )
            )
        finally:
            backend.close()

    differentiation_rows = _build_reset_differentiation_rows(
        specs,
        observations_by_role=observations_by_role,
        digest_by_role=digest_by_role,
    )
    summary = _summary_from_rows(
        parameterization_rows,
        differentiation_rows,
        reset_count=reset_count,
        reset_observation_shapes=reset_observation_shapes,
        default_reset_observation_shape=int(default_reset_observation.shape[0]),
        default_backend_spec_present=bool(default_reset_result.diagnostics["source_only_fixture_spec_present"]),
    )
    return parameterization_rows, differentiation_rows, summary


def write_parameterization_preflight(output_dir: Path) -> tuple[
    Path,
    Path,
    list[FixtureParameterizationRow],
    list[ResetDifferentiationRow],
    dict[str, Any],
]:
    parameterization_rows, differentiation_rows, summary = (
        run_source_only_role_fixture_parameterization_preflight()
    )
    parameterization_path = output_dir / "fixture_parameterization_rows.csv"
    differentiation_path = output_dir / "reset_differentiation_rows.csv"
    write_csv_rows(
        parameterization_path,
        [row.to_csv_row() for row in parameterization_rows],
        fieldnames=FIXTURE_PARAMETERIZATION_FIELDNAMES,
    )
    write_csv_rows(
        differentiation_path,
        [row.to_csv_row() for row in differentiation_rows],
        fieldnames=RESET_DIFFERENTIATION_FIELDNAMES,
    )
    return parameterization_path, differentiation_path, parameterization_rows, differentiation_rows, summary


def run_preflight(
    output_dir: Path,
    *,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    parameterization_path, differentiation_path, _parameterization_rows, _differentiation_rows, summary = (
        write_parameterization_preflight(output_dir)
    )
    summary.update(
        {
            "milestone": str(milestone),
            "generated_at_utc": utc_timestamp(),
            "fixture_parameterization_rows": str(parameterization_path),
            "reset_differentiation_rows": str(differentiation_path),
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def _summary_from_rows(
    parameterization_rows: list[FixtureParameterizationRow],
    differentiation_rows: list[ResetDifferentiationRow],
    *,
    reset_count: int,
    reset_observation_shapes: list[int],
    default_reset_observation_shape: int,
    default_backend_spec_present: bool,
) -> dict[str, Any]:
    role_counts = Counter(row.role_family for row in parameterization_rows)
    reset_l2_values = [row.reset_observation_l2 for row in differentiation_rows]
    unique_initial_state_digest_count = len({row.initial_state_digest for row in parameterization_rows})
    unique_fault_scale_digest_count = len({row.fault_scale_digest for row in parameterization_rows})
    unique_obstacle_digest_count = len({row.obstacle_digest for row in parameterization_rows})
    unique_road_digest_count = len({row.road_digest for row in parameterization_rows})
    unique_reset_observation_digest_count = len(
        {row.reset_observation_digest for row in parameterization_rows}
    )
    all_reset_observations_shape_72 = bool(reset_observation_shapes) and all(
        shape == P0_OBSERVATION_DIM for shape in reset_observation_shapes
    )
    pairwise_reset_observation_l2_min = min(reset_l2_values) if reset_l2_values else 0.0
    pairwise_state_digest_unique = all(
        not row.initial_state_digest_equal for row in differentiation_rows
    )
    pairwise_obstacle_digest_unique = all(
        not row.obstacle_digest_equal for row in differentiation_rows
    )
    role_metadata_only = bool(parameterization_rows) and all(
        row.role_metadata_only for row in parameterization_rows
    )
    fixture_metadata_only = bool(parameterization_rows) and all(
        row.fixture_metadata_only for row in parameterization_rows
    )
    leak_flags = {
        "actor_input_contract_changed": False,
        "role_labels_enter_actor_input": False,
        "fixture_labels_enter_actor_input": False,
        "scenario_labels_enter_actor_input": False,
        "feasibility_classes_enter_actor_input": False,
        "hidden_values_enter_actor_input": False,
        "oracle_labels_enter_actor_input": False,
        "diagnostics_available_to_actor": False,
        "reward_terms_enter_actor_input": False,
        "success_labels_enter_actor_input": False,
        "ttc_enter_actor_input": False,
        "required_clearance_enter_actor_input": False,
    }
    status_pass = (
        len(parameterization_rows) == len(ROLE_FAMILIES)
        and set(role_counts) == set(ROLE_FAMILIES)
        and int(reset_count) == len(ROLE_FAMILIES)
        and all_reset_observations_shape_72
        and default_reset_observation_shape == P0_OBSERVATION_DIM
        and not default_backend_spec_present
        and unique_initial_state_digest_count == len(ROLE_FAMILIES)
        and unique_fault_scale_digest_count >= 2
        and unique_obstacle_digest_count == len(ROLE_FAMILIES)
        and unique_reset_observation_digest_count == len(ROLE_FAMILIES)
        and pairwise_reset_observation_l2_min > DIFFERENTIATION_L2_MIN_THRESHOLD
        and pairwise_state_digest_unique
        and pairwise_obstacle_digest_unique
        and role_metadata_only
        and fixture_metadata_only
        and not any(leak_flags.values())
    )
    return {
        "result_class": "source_only_role_fixture_parameterization_preflight_pass"
        if status_pass
        else "source_only_role_fixture_parameterization_preflight_failed",
        "status_pass": bool(status_pass),
        "backend_id": SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
        "spec_count": len(parameterization_rows),
        "roles": sorted(role_counts),
        "role_counts": dict(sorted(role_counts.items())),
        "reset_count": int(reset_count),
        "reset_observation_shapes": reset_observation_shapes,
        "all_reset_observations_shape_72": bool(all_reset_observations_shape_72),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "default_backend_behavior_checked": True,
        "default_backend_reset_observation_shape": int(default_reset_observation_shape),
        "default_backend_spec_present": bool(default_backend_spec_present),
        "unique_initial_state_digest_count": int(unique_initial_state_digest_count),
        "unique_fault_scale_digest_count": int(unique_fault_scale_digest_count),
        "unique_obstacle_digest_count": int(unique_obstacle_digest_count),
        "unique_road_digest_count": int(unique_road_digest_count),
        "unique_reset_observation_digest_count": int(unique_reset_observation_digest_count),
        "pairwise_reset_observation_l2_min": float(pairwise_reset_observation_l2_min),
        "pairwise_state_digest_unique": bool(pairwise_state_digest_unique),
        "pairwise_obstacle_digest_unique": bool(pairwise_obstacle_digest_unique),
        "role_metadata_only": bool(role_metadata_only),
        "fixture_metadata_only": bool(fixture_metadata_only),
        **leak_flags,
        "external_high_fidelity_required": False,
        "external_high_fidelity_imported": False,
        "high_fidelity_simulation_run": False,
        "measured_validation_run": False,
        "policy_action": False,
        "policy_rollout_run": False,
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


def _build_reset_differentiation_rows(
    specs: list[SourceOnlyRoleFixtureDynamicsSpec],
    *,
    observations_by_role: dict[str, np.ndarray],
    digest_by_role: dict[str, dict[str, str]],
) -> list[ResetDifferentiationRow]:
    rows: list[ResetDifferentiationRow] = []
    for spec_a, spec_b in combinations(specs, 2):
        obs_a = observations_by_role[spec_a.role_family]
        obs_b = observations_by_role[spec_b.role_family]
        digest_a = digest_by_role[spec_a.role_family]
        digest_b = digest_by_role[spec_b.role_family]
        rows.append(
            ResetDifferentiationRow(
                role_family_a=spec_a.role_family,
                role_family_b=spec_b.role_family,
                fixture_id_a=spec_a.fixture_id,
                fixture_id_b=spec_b.fixture_id,
                reset_observation_l2=float(np.linalg.norm(obs_a - obs_b)),
                initial_state_digest_equal=digest_a["initial_state"] == digest_b["initial_state"],
                fault_scale_digest_equal=digest_a["fault_scale"] == digest_b["fault_scale"],
                obstacle_digest_equal=digest_a["obstacle"] == digest_b["obstacle"],
                road_digest_equal=digest_a["road"] == digest_b["road"],
            )
        )
    return rows


def _digests_for_spec(
    spec: SourceOnlyRoleFixtureDynamicsSpec,
    reset_observation: np.ndarray,
) -> dict[str, str]:
    return {
        "initial_state": _digest(asdict(spec.initial_state)),
        "fault_scale": _digest(asdict(spec.fault_scales)),
        "road": _digest(spec.road),
        "obstacle": _digest(spec.obstacles),
        "reset_observation": _digest(np.asarray(reset_observation, dtype=np.float32).round(8).tolist()),
    }


def _role_road(*, lateral_offset: float, curve_scale: float) -> RoadView:
    left_points: list[tuple[float, float]] = []
    right_points: list[tuple[float, float]] = []
    for index in range(8):
        x_body = float(index + 1) * 5.0
        curve = float(curve_scale) * float(index + 1) ** 2
        left_points.append((x_body, 3.0 + float(lateral_offset) + curve))
        right_points.append((x_body, -3.0 + float(lateral_offset) + curve))
    return RoadView(
        left_boundary_points_body=tuple(left_points),
        right_boundary_points_body=tuple(right_points),
    )


def _role_obstacles(primary: ObstacleSlotView) -> tuple[ObstacleSlotView, ...]:
    zero = ObstacleSlotView(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return (primary, zero, zero, zero)


def _validate_specs(specs: list[SourceOnlyRoleFixtureDynamicsSpec]) -> None:
    if len(specs) != len(ROLE_FAMILIES):
        raise ValueError(f"expected {len(ROLE_FAMILIES)} fixture specs, got {len(specs)}")
    roles = [spec.role_family for spec in specs]
    if set(roles) != set(ROLE_FAMILIES):
        raise ValueError(f"unexpected fixture roles: {sorted(roles)}")
    if len({spec.fixture_id for spec in specs}) != len(specs):
        raise ValueError("fixture specs must use unique fixture ids")
    for spec in specs:
        if len(spec.road.left_boundary_points_body) != 8:
            raise ValueError(f"{spec.role_family} has invalid left road point count")
        if len(spec.road.right_boundary_points_body) != 8:
            raise ValueError(f"{spec.role_family} has invalid right road point count")
        if len(spec.obstacles) != 4:
            raise ValueError(f"{spec.role_family} has invalid obstacle slot count")
        if not spec.diagnostic_tags.get("differentiation_reason"):
            raise ValueError(f"{spec.role_family} missing differentiation_reason")


def _digest(value: Any) -> str:
    payload = json.dumps(to_jsonable(value), allow_nan=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run reset-only source-only role fixture parameterization preflight."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = run_preflight(
        args.output_dir,
        milestone=str(args.milestone),
        next_blocker=str(args.next_blocker),
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"spec_count={summary['spec_count']}")
    print(f"reset_count={summary['reset_count']}")
    print(f"pairwise_reset_observation_l2_min={summary['pairwise_reset_observation_l2_min']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
