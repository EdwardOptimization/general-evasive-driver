"""Source-only HF0 role metric panel for engineering-controller diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from autodrift.artifacts import to_jsonable, utc_timestamp, write_csv_rows, write_json
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend, SourceOnlyRoleFixtureDynamicsSpec
from autodrift.hf0_source_only_closed_loop_fixture_pilot import (
    DEFAULT_HORIZON_STEPS,
    CheckpointAdmission,
    admit_actor_checkpoint,
)
from autodrift.hf0_source_only_fixture_smoke import admitted_source_only_fixture_rows
from autodrift.hf0_source_only_role_fixture_parameterization import build_source_only_role_fixture_specs
from autodrift.hf0_scenario_taxonomy_mapping import SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    validate_actor_action,
)
from autodrift.train_ppo import ActorCritic


DEFAULT_MILESTONE = "m2493-engineering-controller-source-only-role-metric-panel"
DEFAULT_NEXT_BLOCKER = "m2493-engineering-controller-source-only-role-metric-panel"
ROLE_FAMILIES = ("stable_aes", "drift_required_recovery", "unavoidable_mitigation")
TELEMETRY_FIELDNAMES = [
    "fixture_id",
    "surface_id",
    "role_family",
    "step_index",
    "observation_shape",
    "action_shape",
    "action_steer",
    "action_throttle",
    "action_brake",
    "action_finite",
    "action_within_bounds",
    "action_saturated",
    "backend_status",
    "terminated_by_backend",
    "truncated_by_backend",
    "diagnostic_wheel_force_count",
    "state_x",
    "state_y",
    "state_psi",
    "state_vx",
    "state_vy",
    "state_speed",
    "state_yaw_rate",
    "physical_steer",
    "physical_throttle",
    "physical_brake",
    "parameterized_fixture",
    "reset_observation_digest",
    "policy_action",
]
PANEL_FIELDNAMES = [
    "role_family",
    "fixture_count",
    "step_count",
    "backend_alive_fraction",
    "finite_action_fraction",
    "bounded_action_fraction",
    "saturated_action_fraction",
    "observation_shape_72_fraction",
    "action_shape_3_fraction",
    "wheel_count_4_fraction",
    "terminated_fraction",
    "truncated_fraction",
    "speed_min",
    "speed_max",
    "speed_mean",
    "y_min",
    "y_max",
    "abs_y_max",
    "yaw_rate_min",
    "yaw_rate_max",
    "abs_yaw_rate_max",
    "steer_min",
    "steer_max",
    "throttle_min",
    "throttle_max",
    "brake_min",
    "brake_max",
    "diagnostic_only",
    "success_rate_computed",
    "verdict_claim_made",
]


@dataclass(frozen=True)
class RoleTelemetryRow:
    fixture_id: str
    surface_id: str
    role_family: str
    step_index: int
    observation_shape: int
    action_shape: int
    action_steer: float
    action_throttle: float
    action_brake: float
    action_finite: bool
    action_within_bounds: bool
    action_saturated: bool
    backend_status: str
    terminated_by_backend: bool
    truncated_by_backend: bool
    diagnostic_wheel_force_count: int
    state_x: float
    state_y: float
    state_psi: float
    state_vx: float
    state_vy: float
    state_speed: float
    state_yaw_rate: float
    physical_steer: float
    physical_throttle: float
    physical_brake: float
    parameterized_fixture: bool
    reset_observation_digest: str
    policy_action: bool

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "surface_id": self.surface_id,
            "role_family": self.role_family,
            "step_index": self.step_index,
            "observation_shape": self.observation_shape,
            "action_shape": self.action_shape,
            "action_steer": self.action_steer,
            "action_throttle": self.action_throttle,
            "action_brake": self.action_brake,
            "action_finite": self.action_finite,
            "action_within_bounds": self.action_within_bounds,
            "action_saturated": self.action_saturated,
            "backend_status": self.backend_status,
            "terminated_by_backend": self.terminated_by_backend,
            "truncated_by_backend": self.truncated_by_backend,
            "diagnostic_wheel_force_count": self.diagnostic_wheel_force_count,
            "state_x": self.state_x,
            "state_y": self.state_y,
            "state_psi": self.state_psi,
            "state_vx": self.state_vx,
            "state_vy": self.state_vy,
            "state_speed": self.state_speed,
            "state_yaw_rate": self.state_yaw_rate,
            "physical_steer": self.physical_steer,
            "physical_throttle": self.physical_throttle,
            "physical_brake": self.physical_brake,
            "parameterized_fixture": self.parameterized_fixture,
            "reset_observation_digest": self.reset_observation_digest,
            "policy_action": self.policy_action,
        }


@dataclass(frozen=True)
class RoleMetricPanelRow:
    role_family: str
    fixture_count: int
    step_count: int
    backend_alive_fraction: float
    finite_action_fraction: float
    bounded_action_fraction: float
    saturated_action_fraction: float
    observation_shape_72_fraction: float
    action_shape_3_fraction: float
    wheel_count_4_fraction: float
    terminated_fraction: float
    truncated_fraction: float
    speed_min: float
    speed_max: float
    speed_mean: float
    y_min: float
    y_max: float
    abs_y_max: float
    yaw_rate_min: float
    yaw_rate_max: float
    abs_yaw_rate_max: float
    steer_min: float
    steer_max: float
    throttle_min: float
    throttle_max: float
    brake_min: float
    brake_max: float
    diagnostic_only: bool = True
    success_rate_computed: bool = False
    verdict_claim_made: bool = False

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "role_family": self.role_family,
            "fixture_count": self.fixture_count,
            "step_count": self.step_count,
            "backend_alive_fraction": self.backend_alive_fraction,
            "finite_action_fraction": self.finite_action_fraction,
            "bounded_action_fraction": self.bounded_action_fraction,
            "saturated_action_fraction": self.saturated_action_fraction,
            "observation_shape_72_fraction": self.observation_shape_72_fraction,
            "action_shape_3_fraction": self.action_shape_3_fraction,
            "wheel_count_4_fraction": self.wheel_count_4_fraction,
            "terminated_fraction": self.terminated_fraction,
            "truncated_fraction": self.truncated_fraction,
            "speed_min": self.speed_min,
            "speed_max": self.speed_max,
            "speed_mean": self.speed_mean,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "abs_y_max": self.abs_y_max,
            "yaw_rate_min": self.yaw_rate_min,
            "yaw_rate_max": self.yaw_rate_max,
            "abs_yaw_rate_max": self.abs_yaw_rate_max,
            "steer_min": self.steer_min,
            "steer_max": self.steer_max,
            "throttle_min": self.throttle_min,
            "throttle_max": self.throttle_max,
            "brake_min": self.brake_min,
            "brake_max": self.brake_max,
            "diagnostic_only": self.diagnostic_only,
            "success_rate_computed": self.success_rate_computed,
            "verdict_claim_made": self.verdict_claim_made,
        }


@dataclass(frozen=True)
class RoleFixtureRunItem:
    fixture_id: str
    surface_id: str
    role_family: str
    options: dict[str, Any]
    fixture_spec: SourceOnlyRoleFixtureDynamicsSpec | None


def _policy_action(model: ActorCritic, observation: np.ndarray, hidden: Any) -> tuple[np.ndarray, Any]:
    if not model.is_online_recurrent:
        raise RuntimeError("source-only role metric panel requires an online recurrent actor")
    action, _log_prob, _value, next_hidden = model.act_recurrent(
        observation,
        hidden,
        deterministic=True,
    )
    return action, next_hidden


def run_source_only_role_metric_panel(
    checkpoint_path: Path | str,
    *,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    use_parameterized_role_fixtures: bool = False,
) -> tuple[list[RoleTelemetryRow], list[RoleMetricPanelRow], dict[str, Any]]:
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    model, admission = admit_actor_checkpoint(checkpoint_path, device=device)
    if model is None:
        telemetry_rows: list[RoleTelemetryRow] = []
        panel_rows: list[RoleMetricPanelRow] = []
        return telemetry_rows, panel_rows, _summary_from_rows(
            telemetry_rows,
            panel_rows,
            admission=admission,
            horizon_steps=int(horizon_steps),
            use_parameterized_role_fixtures=bool(use_parameterized_role_fixtures),
        )

    extractor = P0ObservationExtractor()
    telemetry_rows: list[RoleTelemetryRow] = []
    reset_count = 0
    reset_observation_shapes: list[int] = []
    fixture_items = _role_fixture_run_items(bool(use_parameterized_role_fixtures))

    for fixture_index, fixture_item in enumerate(fixture_items):
        backend = FourWheelHF0Backend(fixture_spec=fixture_item.fixture_spec)
        hidden = None
        try:
            reset_result = backend.reset(
                BackendResetRequest(
                    seed=(2498 if use_parameterized_role_fixtures else 2493) + fixture_index,
                    scenario_spec_id=fixture_item.fixture_id,
                    role_family=fixture_item.role_family,
                    options=fixture_item.options,
                )
            )
            observation = extractor.extract(reset_result.actor_view)
            reset_observation_digest = _observation_digest(observation)
            reset_observation_shapes.append(int(observation.shape[0]))
            reset_count += 1

            for step_index in range(int(horizon_steps)):
                raw_action, hidden = _policy_action(model, observation, hidden)
                action_array = np.asarray(raw_action, dtype=np.float32)
                action_shape = int(action_array.shape[0]) if action_array.ndim == 1 else -1
                action_finite = bool(np.all(np.isfinite(action_array)))
                action_within_bounds = bool(
                    action_array.shape == (ACTION_DIM,)
                    and np.all(action_array >= -1.0)
                    and np.all(action_array <= 1.0)
                )
                action_saturated = bool(
                    action_array.shape == (ACTION_DIM,) and np.any(np.abs(action_array) >= 0.999)
                )
                action = validate_actor_action(action_array)
                step_result = backend.step(action)
                observation = extractor.extract(step_result.actor_view)
                state = dict(step_result.diagnostics.get("state", {}))
                physical_control = list(step_result.diagnostics.get("physical_control", [0.0, 0.0, 0.0]))
                state_vx = _float(state.get("vx", 0.0))
                state_vy = _float(state.get("vy", 0.0))

                telemetry_rows.append(
                    RoleTelemetryRow(
                        fixture_id=fixture_item.fixture_id,
                        surface_id=fixture_item.surface_id,
                        role_family=fixture_item.role_family,
                        step_index=step_index,
                        observation_shape=int(observation.shape[0]),
                        action_shape=action_shape,
                        action_steer=float(action[0]),
                        action_throttle=float(action[1]),
                        action_brake=float(action[2]),
                        action_finite=action_finite,
                        action_within_bounds=action_within_bounds,
                        action_saturated=action_saturated,
                        backend_status=step_result.backend_status,
                        terminated_by_backend=bool(step_result.terminated_by_backend),
                        truncated_by_backend=bool(step_result.truncated_by_backend),
                        diagnostic_wheel_force_count=len(step_result.diagnostics["wheel_forces"]),
                        state_x=_float(state.get("x", 0.0)),
                        state_y=_float(state.get("y", 0.0)),
                        state_psi=_float(state.get("psi", 0.0)),
                        state_vx=state_vx,
                        state_vy=state_vy,
                        state_speed=float(np.hypot(state_vx, state_vy)),
                        state_yaw_rate=_float(state.get("yaw_rate", 0.0)),
                        physical_steer=_physical_control_value(physical_control, 0),
                        physical_throttle=_physical_control_value(physical_control, 1),
                        physical_brake=_physical_control_value(physical_control, 2),
                        parameterized_fixture=bool(use_parameterized_role_fixtures),
                        reset_observation_digest=reset_observation_digest,
                        policy_action=True,
                    )
                )
        finally:
            backend.close()

    panel_rows = build_role_metric_panel_rows(telemetry_rows)
    summary = _summary_from_rows(
        telemetry_rows,
        panel_rows,
        admission=admission,
        horizon_steps=int(horizon_steps),
        reset_count=reset_count,
        reset_observation_shapes=reset_observation_shapes,
        use_parameterized_role_fixtures=bool(use_parameterized_role_fixtures),
    )
    return telemetry_rows, panel_rows, summary


def build_role_metric_panel_rows(telemetry_rows: Iterable[RoleTelemetryRow]) -> list[RoleMetricPanelRow]:
    rows_by_role: dict[str, list[RoleTelemetryRow]] = defaultdict(list)
    for row in telemetry_rows:
        rows_by_role[row.role_family].append(row)

    panel_rows: list[RoleMetricPanelRow] = []
    for role_family in sorted(rows_by_role):
        rows = rows_by_role[role_family]
        panel_rows.append(
            RoleMetricPanelRow(
                role_family=role_family,
                fixture_count=len({row.fixture_id for row in rows}),
                step_count=len(rows),
                backend_alive_fraction=_fraction(row.backend_status == "running" for row in rows),
                finite_action_fraction=_fraction(row.action_finite for row in rows),
                bounded_action_fraction=_fraction(row.action_within_bounds for row in rows),
                saturated_action_fraction=_fraction(row.action_saturated for row in rows),
                observation_shape_72_fraction=_fraction(
                    row.observation_shape == P0_OBSERVATION_DIM for row in rows
                ),
                action_shape_3_fraction=_fraction(row.action_shape == ACTION_DIM for row in rows),
                wheel_count_4_fraction=_fraction(row.diagnostic_wheel_force_count == 4 for row in rows),
                terminated_fraction=_fraction(row.terminated_by_backend for row in rows),
                truncated_fraction=_fraction(row.truncated_by_backend for row in rows),
                speed_min=_min(row.state_speed for row in rows),
                speed_max=_max(row.state_speed for row in rows),
                speed_mean=_mean(row.state_speed for row in rows),
                y_min=_min(row.state_y for row in rows),
                y_max=_max(row.state_y for row in rows),
                abs_y_max=_max(abs(row.state_y) for row in rows),
                yaw_rate_min=_min(row.state_yaw_rate for row in rows),
                yaw_rate_max=_max(row.state_yaw_rate for row in rows),
                abs_yaw_rate_max=_max(abs(row.state_yaw_rate) for row in rows),
                steer_min=_min(row.action_steer for row in rows),
                steer_max=_max(row.action_steer for row in rows),
                throttle_min=_min(row.action_throttle for row in rows),
                throttle_max=_max(row.action_throttle for row in rows),
                brake_min=_min(row.action_brake for row in rows),
                brake_max=_max(row.action_brake for row in rows),
            )
        )
    return panel_rows


def write_role_metric_panel(
    output_dir: Path,
    checkpoint_path: Path | str,
    *,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    use_parameterized_role_fixtures: bool = False,
) -> tuple[Path, Path, list[RoleTelemetryRow], list[RoleMetricPanelRow], dict[str, Any]]:
    telemetry_rows, panel_rows, summary = run_source_only_role_metric_panel(
        checkpoint_path,
        horizon_steps=horizon_steps,
        device=device,
        use_parameterized_role_fixtures=bool(use_parameterized_role_fixtures),
    )
    telemetry_path = output_dir / "telemetry_rows.csv"
    panel_path = output_dir / "role_metric_panel.csv"
    write_csv_rows(
        telemetry_path,
        [row.to_csv_row() for row in telemetry_rows],
        fieldnames=TELEMETRY_FIELDNAMES,
    )
    write_csv_rows(
        panel_path,
        [row.to_csv_row() for row in panel_rows],
        fieldnames=PANEL_FIELDNAMES,
    )
    return telemetry_path, panel_path, telemetry_rows, panel_rows, summary


def run_preflight(
    output_dir: Path,
    *,
    checkpoint_path: Path | str,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    use_parameterized_role_fixtures: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    telemetry_path, panel_path, _telemetry_rows, _panel_rows, summary = write_role_metric_panel(
        output_dir,
        checkpoint_path,
        horizon_steps=horizon_steps,
        device=device,
        use_parameterized_role_fixtures=bool(use_parameterized_role_fixtures),
    )
    summary.update(
        {
            "milestone": str(milestone),
            "generated_at_utc": utc_timestamp(),
            "telemetry_rows": str(telemetry_path),
            "role_metric_panel": str(panel_path),
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def _summary_from_rows(
    telemetry_rows: list[RoleTelemetryRow],
    panel_rows: list[RoleMetricPanelRow],
    *,
    admission: CheckpointAdmission,
    horizon_steps: int,
    reset_count: int = 0,
    reset_observation_shapes: list[int] | None = None,
    use_parameterized_role_fixtures: bool = False,
) -> dict[str, Any]:
    reset_shapes = reset_observation_shapes or []
    role_counts = Counter(row.role_family for row in telemetry_rows)
    fixture_ids = sorted({row.fixture_id for row in telemetry_rows})
    expected_steps = len(ROLE_FAMILIES) * int(horizon_steps)

    all_reset_observations_shape_72 = bool(reset_shapes) and all(
        shape == P0_OBSERVATION_DIM for shape in reset_shapes
    )
    all_step_observations_shape_72 = bool(telemetry_rows) and all(
        row.observation_shape == P0_OBSERVATION_DIM for row in telemetry_rows
    )
    all_action_shapes_3 = bool(telemetry_rows) and all(row.action_shape == ACTION_DIM for row in telemetry_rows)
    all_actions_finite = bool(telemetry_rows) and all(row.action_finite for row in telemetry_rows)
    all_actions_within_bounds = bool(telemetry_rows) and all(row.action_within_bounds for row in telemetry_rows)
    all_backend_statuses_running = bool(telemetry_rows) and all(
        row.backend_status == "running" for row in telemetry_rows
    )
    all_diagnostic_wheel_force_counts_4 = bool(telemetry_rows) and all(
        row.diagnostic_wheel_force_count == 4 for row in telemetry_rows
    )
    role_panel_covers_expected_roles = set(row.role_family for row in panel_rows) == set(ROLE_FAMILIES)
    panel_rows_are_diagnostic_only = bool(panel_rows) and all(row.diagnostic_only for row in panel_rows)
    no_success_rate_or_verdict_panel = bool(panel_rows) and all(
        not row.success_rate_computed and not row.verdict_claim_made for row in panel_rows
    )
    max_action_saturation_fraction = _max(
        row.saturated_action_fraction for row in panel_rows
    ) if panel_rows else 0.0
    min_backend_alive_fraction = _min(row.backend_alive_fraction for row in panel_rows) if panel_rows else 0.0
    min_bounded_action_fraction = _min(row.bounded_action_fraction for row in panel_rows) if panel_rows else 0.0
    max_abs_y_by_role = {
        row.role_family: row.abs_y_max
        for row in sorted(panel_rows, key=lambda item: item.role_family)
    }
    role_reset_observation_digests = {
        role: sorted({row.reset_observation_digest for row in rows})[0]
        for role, rows in _rows_by_role(telemetry_rows).items()
        if rows
    }
    unique_role_reset_observation_digest_count = len(set(role_reset_observation_digests.values()))
    role_reset_observation_digests_differentiated = (
        unique_role_reset_observation_digest_count == len(ROLE_FAMILIES)
    )
    all_rows_use_parameterized_fixtures = bool(telemetry_rows) and all(
        row.parameterized_fixture for row in telemetry_rows
    )
    no_rows_use_parameterized_fixtures = bool(telemetry_rows) and not any(
        row.parameterized_fixture for row in telemetry_rows
    )

    leak_flags = {
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
        admission.checkpoint_admitted
        and len(fixture_ids) == len(ROLE_FAMILIES)
        and int(reset_count) == len(ROLE_FAMILIES)
        and len(telemetry_rows) == expected_steps
        and set(role_counts) == set(ROLE_FAMILIES)
        and all(int(role_counts[role]) == int(horizon_steps) for role in ROLE_FAMILIES)
        and all_reset_observations_shape_72
        and all_step_observations_shape_72
        and all_action_shapes_3
        and all_actions_finite
        and all_actions_within_bounds
        and all_backend_statuses_running
        and all_diagnostic_wheel_force_counts_4
        and role_panel_covers_expected_roles
        and panel_rows_are_diagnostic_only
        and no_success_rate_or_verdict_panel
        and (
            (not use_parameterized_role_fixtures and no_rows_use_parameterized_fixtures)
            or (
                use_parameterized_role_fixtures
                and all_rows_use_parameterized_fixtures
                and role_reset_observation_digests_differentiated
            )
        )
        and not any(leak_flags.values())
    )
    return {
        "result_class": _result_class(
            status_pass=bool(status_pass),
            use_parameterized_role_fixtures=bool(use_parameterized_role_fixtures),
        ),
        "status_pass": bool(status_pass),
        "backend_id": SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
        "parameterized_role_fixtures": bool(use_parameterized_role_fixtures),
        "all_rows_use_parameterized_fixtures": bool(all_rows_use_parameterized_fixtures),
        "no_rows_use_parameterized_fixtures": bool(no_rows_use_parameterized_fixtures),
        "role_reset_observation_digests": dict(sorted(role_reset_observation_digests.items())),
        "unique_role_reset_observation_digest_count": int(unique_role_reset_observation_digest_count),
        "role_reset_observation_digests_differentiated": bool(
            role_reset_observation_digests_differentiated
        ),
        "horizon_steps_per_fixture": int(horizon_steps),
        "fixture_count": len(fixture_ids),
        "role_counts": dict(sorted(role_counts.items())),
        "reset_count": int(reset_count),
        "step_count": len(telemetry_rows),
        "expected_step_count": expected_steps,
        "role_metric_panel_row_count": len(panel_rows),
        "role_metric_panel_roles": sorted(row.role_family for row in panel_rows),
        "role_panel_covers_expected_roles": bool(role_panel_covers_expected_roles),
        "panel_rows_are_diagnostic_only": bool(panel_rows_are_diagnostic_only),
        "max_action_saturation_fraction": float(max_action_saturation_fraction),
        "min_backend_alive_fraction": float(min_backend_alive_fraction),
        "min_bounded_action_fraction": float(min_bounded_action_fraction),
        "max_abs_y_by_role": max_abs_y_by_role,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "reset_observation_shapes": reset_shapes,
        "all_reset_observations_shape_72": bool(all_reset_observations_shape_72),
        "all_step_observations_shape_72": bool(all_step_observations_shape_72),
        "all_action_shapes_3": bool(all_action_shapes_3),
        "all_actions_finite": bool(all_actions_finite),
        "all_actions_within_bounds": bool(all_actions_within_bounds),
        "all_backend_statuses_running": bool(all_backend_statuses_running),
        "all_diagnostic_wheel_force_counts_4": bool(all_diagnostic_wheel_force_counts_4),
        **admission.to_summary_fields(),
        **leak_flags,
        "external_high_fidelity_required": False,
        "external_high_fidelity_imported": False,
        "high_fidelity_simulation_run": False,
        "measured_validation_run": False,
        "diagnostic_only_panel": True,
        "policy_action": bool(telemetry_rows),
        "policy_rollout_run": bool(telemetry_rows),
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


def _role_fixture_run_items(use_parameterized_role_fixtures: bool) -> list[RoleFixtureRunItem]:
    if use_parameterized_role_fixtures:
        return [
            RoleFixtureRunItem(
                fixture_id=spec.fixture_id,
                surface_id=SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
                role_family=spec.role_family,
                options={
                    "fixture_id": spec.fixture_id,
                    "fixture_parameterized": True,
                },
                fixture_spec=spec,
            )
            for spec in build_source_only_role_fixture_specs()
        ]
    return [
        RoleFixtureRunItem(
            fixture_id=row.fixture_id,
            surface_id=row.surface_id,
            role_family=row.role_family,
            options={
                "fixture_id": row.fixture_id,
                "fixture_admission_status": row.fixture_admission_status,
                "fixture_parameterized": False,
            },
            fixture_spec=None,
        )
        for row in admitted_source_only_fixture_rows()
    ]


def _rows_by_role(rows: Iterable[RoleTelemetryRow]) -> dict[str, list[RoleTelemetryRow]]:
    rows_by_role: dict[str, list[RoleTelemetryRow]] = defaultdict(list)
    for row in rows:
        rows_by_role[row.role_family].append(row)
    return rows_by_role


def _result_class(*, status_pass: bool, use_parameterized_role_fixtures: bool) -> str:
    if use_parameterized_role_fixtures:
        return (
            "engineering_controller_parameterized_source_only_role_metric_panel_pass"
            if status_pass
            else "engineering_controller_parameterized_source_only_role_metric_panel_failed"
        )
    return (
        "engineering_controller_source_only_role_metric_panel_pass"
        if status_pass
        else "engineering_controller_source_only_role_metric_panel_failed"
    )


def _observation_digest(observation: np.ndarray) -> str:
    payload = json.dumps(
        to_jsonable(np.asarray(observation, dtype=np.float32).round(8).tolist()),
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _float(value: Any) -> float:
    return float(value)


def _physical_control_value(values: list[Any], index: int) -> float:
    try:
        return _float(values[index])
    except (IndexError, TypeError, ValueError):
        return 0.0


def _fraction(values: Iterable[bool]) -> float:
    bools = [bool(value) for value in values]
    if not bools:
        return 0.0
    return float(sum(bools)) / float(len(bools))


def _min(values: Iterable[float]) -> float:
    numbers = [float(value) for value in values]
    return min(numbers) if numbers else 0.0


def _max(values: Iterable[float]) -> float:
    numbers = [float(value) for value in values]
    return max(numbers) if numbers else 0.0


def _mean(values: Iterable[float]) -> float:
    numbers = [float(value) for value in values]
    if not numbers:
        return 0.0
    return float(sum(numbers)) / float(len(numbers))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run source-only HF0 role metric panel.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--use-parameterized-role-fixtures", action="store_true")
    args = parser.parse_args()

    summary = run_preflight(
        args.output_dir,
        checkpoint_path=args.checkpoint,
        horizon_steps=args.horizon_steps,
        device=args.device,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        use_parameterized_role_fixtures=bool(args.use_parameterized_role_fixtures),
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"fixture_count={summary['fixture_count']}")
    print(f"step_count={summary['step_count']}")
    print(f"role_metric_panel_row_count={summary['role_metric_panel_row_count']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
