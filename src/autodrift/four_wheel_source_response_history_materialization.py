"""Materialize branch-specific response histories for source interventions."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.four_wheel_dynamics import FourWheelDriftModel, FourWheelState, FourWheelVehicleParams
from autodrift.four_wheel_fault_source_shape import build_fault_cases
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


HISTORY_ACTOR_VIEW_COLUMNS = (
    "cmd_steer",
    "cmd_throttle",
    "cmd_brake",
    "vx",
    "vy",
    "yaw_rate",
    "ax",
    "ay",
    "steer_state",
    "steer_rate",
    "drive_state",
    "brake_state",
    "prev_cmd_steer",
    "prev_cmd_throttle",
    "prev_cmd_brake",
)


PROBE_TEMPLATES: dict[str, tuple[float, float, float]] = {
    "left_brake_probe": (0.25, -1.0, 1.0),
    "right_brake_probe": (-0.25, -1.0, 1.0),
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _scenario_state(row: dict[str, str]) -> FourWheelState:
    return FourWheelState(
        x=0.0,
        y=0.0,
        psi=0.0,
        vx=_finite_float(row.get("vx")),
        vy=_finite_float(row.get("vy")),
        yaw_rate=_finite_float(row.get("yaw_rate")),
        steer=0.0,
        drive_force=_finite_float(row.get("drive_force")),
        brake_force=_finite_float(row.get("brake_force")),
    )


def _response_vector(frame: dict[str, Any]) -> np.ndarray:
    return np.asarray([_finite_float(frame.get(column)) for column in HISTORY_ACTOR_VIEW_COLUMNS], dtype=np.float64)


def _history_response_l2(frames_a: list[dict[str, Any]], frames_b: list[dict[str, Any]]) -> float:
    if len(frames_a) != len(frames_b) or not frames_a:
        return float("nan")
    diff = np.asarray([_response_vector(a) - _response_vector(b) for a, b in zip(frames_a, frames_b)], dtype=np.float64)
    return float(np.sqrt(np.mean(np.square(diff))))


def _same_pair_opposite_condition(condition: str) -> str:
    if condition == "A":
        return "B"
    if condition == "B":
        return "A"
    raise ValueError(f"unsupported condition {condition!r}")


def _rollout_history(
    *,
    history_id: int,
    pair_id: int,
    condition: str,
    fault_name: str,
    fault_family: str,
    probe_template: str,
    scenario: dict[str, str],
    action: tuple[float, float, float],
    history_length: int,
    dt: float,
    params: FourWheelVehicleParams,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    faults = {fault.name: fault for fault in build_fault_cases()}
    if fault_name not in faults:
        raise KeyError(f"unknown four-wheel fault {fault_name!r}")
    model = FourWheelDriftModel(params=params, fault_scales=faults[fault_name].scales)
    state = _scenario_state(scenario)
    command = np.asarray(action, dtype=np.float32)
    frames: list[dict[str, Any]] = []
    previous_command = tuple(float(value) for value in action)
    start_yaw_rate = state.yaw_rate
    final_ax = 0.0
    final_ay = 0.0
    for step in range(int(history_length)):
        previous_state = FourWheelState.from_array(state.as_array().copy())
        state, _forces = model.step(state, command, dt)
        ax = (state.vx - previous_state.vx) / float(dt)
        ay = (state.vy - previous_state.vy) / float(dt)
        steer_rate = (state.steer - previous_state.steer) / float(dt)
        final_ax = float(ax)
        final_ay = float(ay)
        frames.append(
            {
                "history_id": int(history_id),
                "pair_id": int(pair_id),
                "condition": condition,
                "fault_name": fault_name,
                "fault_family": fault_family,
                "probe_template": probe_template,
                "step": int(step),
                "cmd_steer": float(action[0]),
                "cmd_throttle": float(action[1]),
                "cmd_brake": float(action[2]),
                "vx": float(state.vx),
                "vy": float(state.vy),
                "yaw_rate": float(state.yaw_rate),
                "ax": float(ax),
                "ay": float(ay),
                "steer_state": float(state.steer),
                "steer_rate": float(steer_rate),
                "drive_state": float(state.drive_force),
                "brake_state": float(state.brake_force),
                "prev_cmd_steer": float(previous_command[0]),
                "prev_cmd_throttle": float(previous_command[1]),
                "prev_cmd_brake": float(previous_command[2]),
            }
        )
        previous_command = tuple(float(value) for value in action)

    prefix = {
        "history_id": int(history_id),
        "pair_id": int(pair_id),
        "condition": condition,
        "fault_name": fault_name,
        "fault_family": fault_family,
        "probe_template": probe_template,
        "history_length": int(history_length),
        "dt": float(dt),
        "final_vx": float(state.vx),
        "final_vy": float(state.vy),
        "final_yaw_rate": float(state.yaw_rate),
        "final_ax": float(final_ax),
        "final_ay": float(final_ay),
        "final_yaw_delta_from_start": float(state.yaw_rate - start_yaw_rate),
        "response_l2_from_opposite_branch": float("nan"),
        "final_yaw_rate_diff_from_opposite": float("nan"),
        "final_vy_diff_from_opposite": float("nan"),
    }
    return prefix, frames


def materialize_four_wheel_source_response_histories(
    *,
    source_run_dir: Path,
    intervention_run_dir: Path,
    run_dir: Path,
    history_length: int = 24,
    dt: float = 0.02,
) -> dict[str, Any]:
    source_run_dir = Path(source_run_dir)
    intervention_run_dir = Path(intervention_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(source_run_dir / "summary.json")
    intervention_summary = read_json(intervention_run_dir / "summary.json")
    scenario_rows = _read_csv(source_run_dir / "scenario_summary.csv")
    intervention_rows = [
        row for row in _read_csv(intervention_run_dir / "intervention_rows.csv") if row["source_subset"] == "near_high_union"
    ]
    scenarios_by_id = {str(row["scenario_id"]): row for row in scenario_rows}

    unique_histories: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in intervention_rows:
        pair_id = int(float(row["pair_id"]))
        condition = str(row["condition"])
        for template in PROBE_TEMPLATES:
            unique_histories[(pair_id, condition, template)] = row

    params = FourWheelVehicleParams()
    prefix_rows: list[dict[str, Any]] = []
    frame_rows: list[dict[str, Any]] = []
    frames_by_key: dict[tuple[int, str, str], list[dict[str, Any]]] = {}
    history_id_by_key: dict[tuple[int, str, str], int] = {}

    history_id = 0
    for key in sorted(unique_histories, key=lambda item: (item[0], item[1], item[2])):
        pair_id, condition, template = key
        source_row = unique_histories[key]
        prefix, frames = _rollout_history(
            history_id=history_id,
            pair_id=pair_id,
            condition=condition,
            fault_name=source_row["fault_name"],
            fault_family=source_row["fault_family"],
            probe_template=template,
            scenario=scenarios_by_id[source_row["scenario_id"]],
            action=PROBE_TEMPLATES[template],
            history_length=history_length,
            dt=dt,
            params=params,
        )
        prefix_rows.append(prefix)
        frame_rows.extend(frames)
        frames_by_key[key] = frames
        history_id_by_key[key] = history_id
        history_id += 1

    prefix_by_key = {
        (int(row["pair_id"]), str(row["condition"]), str(row["probe_template"])): row for row in prefix_rows
    }
    for key, prefix in prefix_by_key.items():
        pair_id, condition, template = key
        opposite = (pair_id, _same_pair_opposite_condition(condition), template)
        if opposite not in frames_by_key:
            continue
        response_l2 = _history_response_l2(frames_by_key[key], frames_by_key[opposite])
        opposite_prefix = prefix_by_key[opposite]
        prefix["response_l2_from_opposite_branch"] = response_l2
        prefix["final_yaw_rate_diff_from_opposite"] = abs(
            _finite_float(prefix.get("final_yaw_rate")) - _finite_float(opposite_prefix.get("final_yaw_rate"))
        )
        prefix["final_vy_diff_from_opposite"] = abs(
            _finite_float(prefix.get("final_vy")) - _finite_float(opposite_prefix.get("final_vy"))
        )

    history_intervention_rows: list[dict[str, Any]] = []
    wrong_history_rows: list[dict[str, Any]] = []
    history_intervention_id = 0
    for intervention in sorted(intervention_rows, key=lambda row: int(float(row["intervention_id"]))):
        pair_id = int(float(intervention["pair_id"]))
        condition = str(intervention["condition"])
        wrong_condition = _same_pair_opposite_condition(condition)
        for template in sorted(PROBE_TEMPLATES):
            correct_history_id = history_id_by_key[(pair_id, condition, template)]
            wrong_history_id = history_id_by_key[(pair_id, wrong_condition, template)]
            history_intervention_rows.append(
                {
                    "history_intervention_id": int(history_intervention_id),
                    "intervention_id": int(float(intervention["intervention_id"])),
                    "pair_id": int(pair_id),
                    "condition": condition,
                    "probe_template": template,
                    "correct_history_id": int(correct_history_id),
                    "preferred_candidate_id": int(float(intervention["preferred_candidate_id"])),
                    "rejected_candidate_id": int(float(intervention["rejected_candidate_id"])),
                    "preferred_margin": _finite_float(intervention.get("preferred_margin")),
                    "rejected_margin": _finite_float(intervention.get("rejected_margin")),
                    "margin_gap": _finite_float(intervention.get("margin_gap")),
                }
            )
            wrong_history_rows.append(
                {
                    "history_intervention_id": int(history_intervention_id),
                    "intervention_id": int(float(intervention["intervention_id"])),
                    "pair_id": int(pair_id),
                    "condition": condition,
                    "probe_template": template,
                    "correct_history_id": int(correct_history_id),
                    "wrong_history_id": int(wrong_history_id),
                    "wrong_condition": wrong_condition,
                    "same_pair_swap": True,
                    "opposite_condition_swap": True,
                    "preferred_candidate_id": int(float(intervention["preferred_candidate_id"])),
                    "rejected_candidate_id": int(float(intervention["rejected_candidate_id"])),
                    "margin_gap": _finite_float(intervention.get("margin_gap")),
                }
            )
            history_intervention_id += 1

    write_csv_rows(run_dir / "history_prefix_rows.csv", prefix_rows)
    write_csv_rows(run_dir / "history_frame_rows.csv", frame_rows)
    write_csv_rows(run_dir / "history_intervention_rows.csv", history_intervention_rows)
    write_csv_rows(run_dir / "wrong_history_pair_rows.csv", wrong_history_rows)
    actor_values = np.asarray(
        [[_finite_float(row.get(column)) for column in HISTORY_ACTOR_VIEW_COLUMNS] for row in frame_rows],
        dtype=np.float64,
    )
    actor_view_all_finite = bool(actor_values.size > 0 and np.all(np.isfinite(actor_values)))
    response_l2_values = [_finite_float(row.get("response_l2_from_opposite_branch")) for row in prefix_rows]
    yaw_diff_values = [_finite_float(row.get("final_yaw_rate_diff_from_opposite")) for row in prefix_rows]
    vy_diff_values = [_finite_float(row.get("final_vy_diff_from_opposite")) for row in prefix_rows]
    wrong_history_valid_count = sum(
        bool(row["same_pair_swap"]) and bool(row["opposite_condition_swap"]) for row in wrong_history_rows
    )
    forbidden_actor_view_columns = [
        column
        for column in HISTORY_ACTOR_VIEW_COLUMNS
        if any(token in column.lower() for token in ("fault", "condition", "label", "source", "success", "margin"))
    ]
    summary = {
        "run_type": "four_wheel_source_response_history_materialization",
        "source_run_dir": str(source_run_dir),
        "intervention_run_dir": str(intervention_run_dir),
        "source_scenario_profile": source_summary.get("scenario_profile", ""),
        "intervention_rows_source": int(intervention_summary.get("intervention_rows", 0)),
        "near_high_union_intervention_rows": int(len(intervention_rows)),
        "probe_templates": sorted(PROBE_TEMPLATES),
        "probe_template_count": int(len(PROBE_TEMPLATES)),
        "history_length": int(history_length),
        "dt": float(dt),
        "history_prefix_rows": int(len(prefix_rows)),
        "history_frame_rows": int(len(frame_rows)),
        "history_intervention_rows": int(len(history_intervention_rows)),
        "wrong_history_pair_rows": int(len(wrong_history_rows)),
        "wrong_history_valid_count": int(wrong_history_valid_count),
        "actor_view_history_columns": list(HISTORY_ACTOR_VIEW_COLUMNS),
        "actor_view_history_column_count": int(len(HISTORY_ACTOR_VIEW_COLUMNS)),
        "actor_view_history_all_finite": actor_view_all_finite,
        "forbidden_actor_view_history_columns": forbidden_actor_view_columns,
        "response_l2_mean": float(np.mean(response_l2_values)) if response_l2_values else float("nan"),
        "response_l2_min": float(np.min(response_l2_values)) if response_l2_values else float("nan"),
        "response_l2_ge_0_01_count": int(sum(value >= 0.01 for value in response_l2_values)),
        "final_yaw_rate_diff_ge_0_01_count": int(sum(value >= 0.01 for value in yaw_diff_values)),
        "final_vy_diff_ge_0_01_count": int(sum(value >= 0.01 for value in vy_diff_values)),
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "history_prefix_rows_csv": run_dir / "history_prefix_rows.csv",
        "history_frame_rows_csv": run_dir / "history_frame_rows.csv",
        "history_intervention_rows_csv": run_dir / "history_intervention_rows.csv",
        "wrong_history_pair_rows_csv": run_dir / "wrong_history_pair_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize four-wheel source response-history artifacts.")
    parser.add_argument("--source-run-dir", type=Path, required=True)
    parser.add_argument("--intervention-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--history-length", type=int, default=24)
    parser.add_argument("--dt", type=float, default=0.02)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="four_wheel_source_response_history_materialization")
    summary = materialize_four_wheel_source_response_histories(
        source_run_dir=args.source_run_dir,
        intervention_run_dir=args.intervention_run_dir,
        run_dir=run_dir,
        history_length=args.history_length,
        dt=args.dt,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
