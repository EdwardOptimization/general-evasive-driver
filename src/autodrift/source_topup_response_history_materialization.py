"""Materialize response histories for the merged source top-up corpus."""

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.four_wheel_dynamics import FourWheelDriftModel, FourWheelState, FourWheelVehicleParams
from autodrift.four_wheel_fault_source_shape import FourWheelFaultCase, build_fault_cases
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


PROBE_TEMPLATES: dict[str, tuple[float, float, float]] = {
    "left_brake_probe": (0.25, -1.0, 1.0),
    "right_brake_probe": (-0.25, -1.0, 1.0),
}

ACTOR_VIEW_HISTORY_COLUMNS = (
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


def _params_for_fault(params: FourWheelVehicleParams, fault: FourWheelFaultCase) -> FourWheelVehicleParams:
    if not fault.params_override:
        return params
    return replace(params, **{key: value for key, value in fault.params_override})


def _response_vector(frame: dict[str, Any]) -> np.ndarray:
    return np.asarray([_finite_float(frame.get(column)) for column in ACTOR_VIEW_HISTORY_COLUMNS], dtype=np.float64)


def _history_response_l2(frames_a: list[dict[str, Any]], frames_b: list[dict[str, Any]]) -> float:
    if len(frames_a) != len(frames_b) or not frames_a:
        return float("nan")
    diff = np.asarray([_response_vector(a) - _response_vector(b) for a, b in zip(frames_a, frames_b)])
    return float(np.sqrt(np.mean(np.square(diff))))


def _opposite_condition(condition: str) -> str:
    if condition == "A":
        return "B"
    if condition == "B":
        return "A"
    raise ValueError(f"unsupported condition {condition!r}")


def _source_identity(row: dict[str, Any]) -> str:
    return f"{row.get('source_run_id', '')}:{row.get('source_row_id', '')}"


def _source_specs(
    *,
    merged_summary: dict[str, Any],
    base_source_run_dir: Path,
    topup_source_run_dir: Path,
) -> dict[str, dict[str, Any]]:
    base_export_id = Path(str(merged_summary.get("base_export_run_dir", "m1322_source_repair_corpus_export"))).name
    topup_id = Path(str(merged_summary.get("topup_source_run_dir", topup_source_run_dir.name))).name
    return {
        base_export_id: {
            "source_run_id": base_export_id,
            "source_run_dir": Path(base_source_run_dir),
            "fault_profile": "source_repair_v1",
        },
        topup_id: {
            "source_run_id": topup_id,
            "source_run_dir": Path(topup_source_run_dir),
            "fault_profile": "source_topup_v1",
        },
    }


def _scenario_index(specs: dict[str, dict[str, Any]]) -> dict[tuple[str, str], dict[str, str]]:
    scenarios: dict[tuple[str, str], dict[str, str]] = {}
    for source_run_id, spec in specs.items():
        for row in _read_csv(Path(spec["source_run_dir"]) / "scenario_summary.csv"):
            scenarios[(source_run_id, str(row["scenario_id"]))] = row
    return scenarios


def _fault_index(specs: dict[str, dict[str, Any]]) -> dict[tuple[str, str], FourWheelFaultCase]:
    faults: dict[tuple[str, str], FourWheelFaultCase] = {}
    for source_run_id, spec in specs.items():
        for fault in build_fault_cases(str(spec["fault_profile"])):
            faults[(source_run_id, fault.name)] = fault
    return faults


def _planned_rows_by_pair(plan_run_dir: Path) -> dict[int, dict[str, str]]:
    rows = _read_csv(Path(plan_run_dir) / "planned_source_pairs.csv")
    return {int(float(row["pair_id"])): row for row in rows}


def _rollout_history(
    *,
    history_id: int,
    source_row: dict[str, str],
    planned_row: dict[str, str],
    condition: str,
    fault: FourWheelFaultCase,
    scenario: dict[str, str],
    probe_template: str,
    action: tuple[float, float, float],
    history_length: int,
    dt: float,
    params: FourWheelVehicleParams,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pair_id = int(float(source_row["pair_id"]))
    source_run_id = str(source_row["source_run_id"])
    source_row_id = str(source_row["source_row_id"])
    original_pair_id = str(source_row["original_pair_id"])
    source_identity = str(source_row.get("source_identity") or _source_identity(source_row))
    model = FourWheelDriftModel(params=_params_for_fault(params, fault), fault_scales=fault.scales)
    state = _scenario_state(scenario)
    command = np.asarray(action, dtype=np.float32)
    previous_command = tuple(float(value) for value in action)
    start_yaw_rate = float(state.yaw_rate)
    frames: list[dict[str, Any]] = []
    final_ax = 0.0
    final_ay = 0.0
    for step in range(int(history_length)):
        previous_state = FourWheelState.from_array(state.as_array().copy())
        state, _forces = model.step(state, command, float(dt))
        ax = (state.vx - previous_state.vx) / float(dt)
        ay = (state.vy - previous_state.vy) / float(dt)
        steer_rate = (state.steer - previous_state.steer) / float(dt)
        final_ax = float(ax)
        final_ay = float(ay)
        frames.append(
            {
                "history_id": int(history_id),
                "pair_id": int(pair_id),
                "source_run_id": source_run_id,
                "source_row_id": source_row_id,
                "original_pair_id": original_pair_id,
                "source_identity": source_identity,
                "condition": condition,
                "fault_name": fault.name,
                "fault_family": fault.family,
                "probe_template": probe_template,
                "fold": int(float(planned_row.get("fold", 0))),
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
        "source_run_id": source_run_id,
        "source_row_id": source_row_id,
        "original_pair_id": original_pair_id,
        "source_identity": source_identity,
        "condition": condition,
        "fault_name": fault.name,
        "fault_family": fault.family,
        "source_family": source_row.get("source_family", source_row.get("fault_family_pair", "")),
        "probe_template": probe_template,
        "fold": int(float(planned_row.get("fold", 0))),
        "margin_bucket": planned_row.get("margin_bucket", ""),
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


def _condition_spec(row: dict[str, str], condition: str) -> dict[str, Any]:
    if condition == "A":
        preferred_candidate = int(float(row["best_candidate_A"]))
        rejected_candidate = int(float(row["best_candidate_B"]))
        return {
            "condition": "A",
            "fault_name": row["condition_A_fault"],
            "fault_family": row["condition_A_fault_family"],
            "preferred_candidate_id": preferred_candidate,
            "rejected_candidate_id": rejected_candidate,
            "preferred_margin": _finite_float(row.get("margin_A_best_A")),
            "rejected_margin": _finite_float(row.get("margin_A_best_B")),
            "preferred_success": _bool_text(row.get("best_A_success")),
            "rejected_success": _bool_text(row.get("A_using_B_success")),
            "preferred_steer": _finite_float(row.get("best_A_steer")),
            "preferred_throttle": _finite_float(row.get("best_A_throttle")),
            "preferred_brake": _finite_float(row.get("best_A_brake")),
            "rejected_steer": _finite_float(row.get("best_B_steer")),
            "rejected_throttle": _finite_float(row.get("best_B_throttle")),
            "rejected_brake": _finite_float(row.get("best_B_brake")),
        }
    if condition == "B":
        preferred_candidate = int(float(row["best_candidate_B"]))
        rejected_candidate = int(float(row["best_candidate_A"]))
        return {
            "condition": "B",
            "fault_name": row["condition_B_fault"],
            "fault_family": row["condition_B_fault_family"],
            "preferred_candidate_id": preferred_candidate,
            "rejected_candidate_id": rejected_candidate,
            "preferred_margin": _finite_float(row.get("margin_B_best_B")),
            "rejected_margin": _finite_float(row.get("margin_B_best_A")),
            "preferred_success": _bool_text(row.get("best_B_success")),
            "rejected_success": _bool_text(row.get("B_using_A_success")),
            "preferred_steer": _finite_float(row.get("best_B_steer")),
            "preferred_throttle": _finite_float(row.get("best_B_throttle")),
            "preferred_brake": _finite_float(row.get("best_B_brake")),
            "rejected_steer": _finite_float(row.get("best_A_steer")),
            "rejected_throttle": _finite_float(row.get("best_A_throttle")),
            "rejected_brake": _finite_float(row.get("best_A_brake")),
        }
    raise ValueError(f"unsupported condition {condition!r}")


def _source_pair_output(row: dict[str, str], planned_row: dict[str, str]) -> dict[str, Any]:
    return {
        "pair_id": int(float(row["pair_id"])),
        "source_run_id": str(row["source_run_id"]),
        "source_row_id": str(row["source_row_id"]),
        "original_pair_id": str(row["original_pair_id"]),
        "source_identity": str(row.get("source_identity") or _source_identity(row)),
        "scenario_id": str(row["scenario_id"]),
        "seed": int(float(row["seed"])),
        "fold": int(float(planned_row.get("fold", 0))),
        "fault_family_pair": str(row["fault_family_pair"]),
        "source_family": str(row.get("source_family", row["fault_family_pair"])),
        "condition_A_fault": str(row["condition_A_fault"]),
        "condition_B_fault": str(row["condition_B_fault"]),
        "margin_bucket": str(planned_row.get("margin_bucket", "")),
        "min_own_margin": _finite_float(row.get("min_own_margin")),
        "min_cross_regret": _finite_float(row.get("min_cross_regret")),
        "near_boundary_margin_le_0_20": _bool_text(row.get("near_boundary_margin_le_0_20")),
        "high_regret_ge_0_05": _bool_text(row.get("high_regret_ge_0_05")),
    }


def _write_limits(run_dir: Path) -> Path:
    path = Path(run_dir) / "materialization_limits.md"
    path.write_text(
        "\n".join(
            [
                "# M1333 Materialization Limits",
                "",
                "M1333 materializes no-policy command-response history artifacts.",
                "",
                "Allowed claim: source-identity-preserving response-history artifact construction.",
                "",
                "Blocked claims:",
                "",
                "- actor or Gym integration",
                "- policy training or PPO",
                "- checkpoint promotion",
                "- self-identification evidence",
                "- driver performance",
                "- high-fidelity or real-vehicle validation",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def materialize_source_topup_response_histories(
    *,
    merged_source_run_dir: Path,
    expansion_plan_run_dir: Path,
    base_source_run_dir: Path,
    topup_source_run_dir: Path,
    run_dir: Path,
    history_length: int = 24,
    dt: float = 0.02,
) -> dict[str, Any]:
    merged_source_run_dir = Path(merged_source_run_dir)
    expansion_plan_run_dir = Path(expansion_plan_run_dir)
    base_source_run_dir = Path(base_source_run_dir)
    topup_source_run_dir = Path(topup_source_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    merged_summary = read_json(merged_source_run_dir / "summary.json")
    plan_summary = read_json(expansion_plan_run_dir / "summary.json")
    source_rows = _read_csv(merged_source_run_dir / "all_accepted_source_rows.csv")
    planned_by_pair = _planned_rows_by_pair(expansion_plan_run_dir)
    specs = _source_specs(
        merged_summary=merged_summary,
        base_source_run_dir=base_source_run_dir,
        topup_source_run_dir=topup_source_run_dir,
    )
    scenarios = _scenario_index(specs)
    faults = _fault_index(specs)
    params = FourWheelVehicleParams()

    source_pair_rows: list[dict[str, Any]] = []
    prefix_rows: list[dict[str, Any]] = []
    frame_rows: list[dict[str, Any]] = []
    history_intervention_rows: list[dict[str, Any]] = []
    wrong_history_rows: list[dict[str, Any]] = []
    frames_by_key: dict[tuple[int, str, str], list[dict[str, Any]]] = {}
    history_id_by_key: dict[tuple[int, str, str], int] = {}
    spec_by_key: dict[tuple[int, str], dict[str, Any]] = {}

    scenario_lookup_missing: list[str] = []
    fault_lookup_missing: list[str] = []
    plan_lookup_missing: list[int] = []

    history_id = 0
    for row in sorted(source_rows, key=lambda item: int(float(item["pair_id"]))):
        pair_id = int(float(row["pair_id"]))
        source_run_id = str(row["source_run_id"])
        planned_row = planned_by_pair.get(pair_id)
        if planned_row is None:
            plan_lookup_missing.append(pair_id)
            continue
        source_pair_rows.append(_source_pair_output(row, planned_row))
        scenario_key = (source_run_id, str(row["scenario_id"]))
        scenario = scenarios.get(scenario_key)
        if scenario is None:
            scenario_lookup_missing.append(f"{source_run_id}:{row['scenario_id']}")
            continue
        for condition in ("A", "B"):
            spec = _condition_spec(row, condition)
            fault_key = (source_run_id, str(spec["fault_name"]))
            fault = faults.get(fault_key)
            if fault is None:
                fault_lookup_missing.append(f"{source_run_id}:{spec['fault_name']}")
                continue
            spec_by_key[(pair_id, condition)] = spec
            for probe_template, action in PROBE_TEMPLATES.items():
                prefix, frames = _rollout_history(
                    history_id=history_id,
                    source_row=row,
                    planned_row=planned_row,
                    condition=condition,
                    fault=fault,
                    scenario=scenario,
                    probe_template=probe_template,
                    action=action,
                    history_length=history_length,
                    dt=dt,
                    params=params,
                )
                prefix_rows.append(prefix)
                frame_rows.extend(frames)
                key = (pair_id, condition, probe_template)
                frames_by_key[key] = frames
                history_id_by_key[key] = history_id
                history_id += 1

    prefix_by_key = {
        (int(row["pair_id"]), str(row["condition"]), str(row["probe_template"])): row for row in prefix_rows
    }
    for key, prefix in prefix_by_key.items():
        pair_id, condition, probe_template = key
        opposite_key = (pair_id, _opposite_condition(condition), probe_template)
        if opposite_key not in frames_by_key:
            continue
        opposite_prefix = prefix_by_key[opposite_key]
        prefix["response_l2_from_opposite_branch"] = _history_response_l2(frames_by_key[key], frames_by_key[opposite_key])
        prefix["final_yaw_rate_diff_from_opposite"] = abs(
            _finite_float(prefix.get("final_yaw_rate")) - _finite_float(opposite_prefix.get("final_yaw_rate"))
        )
        prefix["final_vy_diff_from_opposite"] = abs(
            _finite_float(prefix.get("final_vy")) - _finite_float(opposite_prefix.get("final_vy"))
        )

    source_row_by_pair = {int(float(row["pair_id"])): row for row in source_rows}
    history_intervention_id = 0
    for pair_id in sorted(source_row_by_pair):
        source_row = source_row_by_pair[pair_id]
        source_identity = str(source_row.get("source_identity") or _source_identity(source_row))
        for condition in ("A", "B"):
            wrong_condition = _opposite_condition(condition)
            spec = spec_by_key.get((pair_id, condition))
            if spec is None:
                continue
            for probe_template in sorted(PROBE_TEMPLATES):
                key = (pair_id, condition, probe_template)
                wrong_key = (pair_id, wrong_condition, probe_template)
                if key not in history_id_by_key or wrong_key not in history_id_by_key:
                    continue
                correct_history_id = history_id_by_key[key]
                wrong_history_id = history_id_by_key[wrong_key]
                margin_gap = float(spec["preferred_margin"]) - float(spec["rejected_margin"])
                common = {
                    "history_intervention_id": int(history_intervention_id),
                    "pair_id": int(pair_id),
                    "source_run_id": str(source_row["source_run_id"]),
                    "source_row_id": str(source_row["source_row_id"]),
                    "original_pair_id": str(source_row["original_pair_id"]),
                    "source_identity": source_identity,
                    "condition": condition,
                    "probe_template": probe_template,
                    "correct_history_id": int(correct_history_id),
                    "preferred_candidate_id": int(spec["preferred_candidate_id"]),
                    "rejected_candidate_id": int(spec["rejected_candidate_id"]),
                    "preferred_margin": float(spec["preferred_margin"]),
                    "rejected_margin": float(spec["rejected_margin"]),
                    "margin_gap": float(margin_gap),
                    "preferred_success": bool(spec["preferred_success"]),
                    "rejected_success": bool(spec["rejected_success"]),
                    "preferred_steer": float(spec["preferred_steer"]),
                    "preferred_throttle": float(spec["preferred_throttle"]),
                    "preferred_brake": float(spec["preferred_brake"]),
                    "rejected_steer": float(spec["rejected_steer"]),
                    "rejected_throttle": float(spec["rejected_throttle"]),
                    "rejected_brake": float(spec["rejected_brake"]),
                }
                history_intervention_rows.append(common)
                wrong_history_rows.append(
                    common
                    | {
                        "wrong_history_id": int(wrong_history_id),
                        "wrong_condition": wrong_condition,
                        "same_pair_swap": True,
                        "opposite_condition_swap": True,
                        "same_source_identity_swap": True,
                    }
                )
                history_intervention_id += 1

    source_lineage_rows = [
        {
            "source_run_id": source_run_id,
            "source_run_dir": str(spec["source_run_dir"]),
            "fault_profile": str(spec["fault_profile"]),
            "scenario_rows": int(
                sum(1 for key in scenarios if key[0] == source_run_id)
            ),
            "fault_rows": int(sum(1 for key in faults if key[0] == source_run_id)),
        }
        for source_run_id, spec in sorted(specs.items())
    ]

    write_csv_rows(run_dir / "source_pair_rows.csv", source_pair_rows)
    write_csv_rows(run_dir / "history_prefix_rows.csv", prefix_rows)
    write_csv_rows(run_dir / "history_frame_rows.csv", frame_rows)
    write_csv_rows(run_dir / "history_intervention_rows.csv", history_intervention_rows)
    write_csv_rows(run_dir / "wrong_history_pair_rows.csv", wrong_history_rows)
    write_csv_rows(run_dir / "source_lineage_rows.csv", source_lineage_rows)
    limits_path = _write_limits(run_dir)

    actor_values = np.asarray(
        [[_finite_float(row.get(column)) for column in ACTOR_VIEW_HISTORY_COLUMNS] for row in frame_rows],
        dtype=np.float64,
    )
    actor_view_all_finite = bool(actor_values.size > 0 and np.all(np.isfinite(actor_values)))
    forbidden_actor_view_columns = [
        column
        for column in ACTOR_VIEW_HISTORY_COLUMNS
        if any(
            token in column.lower()
            for token in ("fault", "condition", "label", "source", "success", "margin", "pair", "candidate")
        )
    ]
    identities = [str(row.get("source_identity", "")) for row in source_pair_rows]
    source_identity_duplicate_count = int(len(identities) - len(set(identities)))
    response_l2_values = [_finite_float(row.get("response_l2_from_opposite_branch")) for row in prefix_rows]
    yaw_diff_values = [_finite_float(row.get("final_yaw_rate_diff_from_opposite")) for row in prefix_rows]
    vy_diff_values = [_finite_float(row.get("final_vy_diff_from_opposite")) for row in prefix_rows]
    wrong_history_valid_count = int(
        sum(
            bool(row["same_pair_swap"]) and bool(row["opposite_condition_swap"]) and bool(row["same_source_identity_swap"])
            for row in wrong_history_rows
        )
    )
    source_identity_metadata_preserved = bool(
        all(str(row.get("source_identity", "")) for row in source_pair_rows)
        and all(str(row.get("source_identity", "")) for row in prefix_rows)
        and all(str(row.get("source_identity", "")) for row in frame_rows)
        and all(str(row.get("source_identity", "")) for row in history_intervention_rows)
        and all(str(row.get("source_identity", "")) for row in wrong_history_rows)
    )

    expected_source_pairs = int(plan_summary.get("planned_source_pairs", len(source_rows)))
    expected_pair_probe_groups = int(plan_summary.get("planned_pair_probe_groups", 0))
    expected_prefix_rows = expected_pair_probe_groups * 2
    expected_frame_rows = expected_prefix_rows * int(history_length)
    global_friction_missing = bool(merged_summary.get("global_friction_missing", False))
    halfshaft_undercovered = bool(merged_summary.get("halfshaft_undercovered", False))
    result_class = (
        "source_topup_response_history_materialization_pass"
        if len(source_pair_rows) == expected_source_pairs
        and len(prefix_rows) == expected_prefix_rows
        and len(frame_rows) == expected_frame_rows
        and len(history_intervention_rows) == expected_prefix_rows
        and len(wrong_history_rows) == expected_prefix_rows
        and not scenario_lookup_missing
        and not fault_lookup_missing
        and not plan_lookup_missing
        and source_identity_duplicate_count == 0
        and source_identity_metadata_preserved
        and wrong_history_valid_count == expected_prefix_rows
        and actor_view_all_finite
        and not forbidden_actor_view_columns
        else "source_topup_response_history_materialization_gap_reported"
    )
    summary = {
        "run_type": "source_topup_response_history_materialization",
        "result_class": result_class,
        "merged_source_run_dir": str(merged_source_run_dir),
        "expansion_plan_run_dir": str(expansion_plan_run_dir),
        "base_source_run_dir": str(base_source_run_dir),
        "topup_source_run_dir": str(topup_source_run_dir),
        "expected_source_pairs": int(expected_source_pairs),
        "expected_pair_probe_groups": int(expected_pair_probe_groups),
        "expected_history_prefix_rows": int(expected_prefix_rows),
        "expected_history_frame_rows": int(expected_frame_rows),
        "source_pair_rows": int(len(source_pair_rows)),
        "history_prefix_rows": int(len(prefix_rows)),
        "history_frame_rows": int(len(frame_rows)),
        "history_intervention_rows": int(len(history_intervention_rows)),
        "wrong_history_pair_rows": int(len(wrong_history_rows)),
        "history_length": int(history_length),
        "dt": float(dt),
        "probe_templates": sorted(PROBE_TEMPLATES),
        "source_identity_duplicate_count": int(source_identity_duplicate_count),
        "source_identity_metadata_preserved": bool(source_identity_metadata_preserved),
        "scenario_lookup_missing_count": int(len(set(scenario_lookup_missing))),
        "fault_lookup_missing_count": int(len(set(fault_lookup_missing))),
        "plan_lookup_missing_count": int(len(set(plan_lookup_missing))),
        "wrong_history_valid_count": int(wrong_history_valid_count),
        "actor_view_history_columns": list(ACTOR_VIEW_HISTORY_COLUMNS),
        "actor_view_history_column_count": int(len(ACTOR_VIEW_HISTORY_COLUMNS)),
        "actor_view_history_all_finite": bool(actor_view_all_finite),
        "forbidden_actor_view_history_columns": forbidden_actor_view_columns,
        "response_l2_mean": float(np.mean(response_l2_values)) if response_l2_values else float("nan"),
        "response_l2_min": float(np.min(response_l2_values)) if response_l2_values else float("nan"),
        "response_l2_ge_0_01_count": int(sum(value >= 0.01 for value in response_l2_values)),
        "final_yaw_rate_diff_ge_0_01_count": int(sum(value >= 0.01 for value in yaw_diff_values)),
        "final_vy_diff_ge_0_01_count": int(sum(value >= 0.01 for value in vy_diff_values)),
        "global_friction_missing": bool(global_friction_missing),
        "halfshaft_undercovered": bool(halfshaft_undercovered),
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "source_pair_rows_csv": run_dir / "source_pair_rows.csv",
        "history_prefix_rows_csv": run_dir / "history_prefix_rows.csv",
        "history_frame_rows_csv": run_dir / "history_frame_rows.csv",
        "history_intervention_rows_csv": run_dir / "history_intervention_rows.csv",
        "wrong_history_pair_rows_csv": run_dir / "wrong_history_pair_rows.csv",
        "source_lineage_rows_csv": run_dir / "source_lineage_rows.csv",
        "materialization_limits_md": limits_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merged-source-run-dir", type=Path, required=True)
    parser.add_argument("--expansion-plan-run-dir", type=Path, required=True)
    parser.add_argument("--base-source-run-dir", type=Path, required=True)
    parser.add_argument("--topup-source-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--history-length", type=int, default=24)
    parser.add_argument("--dt", type=float, default=0.02)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="source_topup_response_history_materialization")
    summary = materialize_source_topup_response_histories(
        merged_source_run_dir=args.merged_source_run_dir,
        expansion_plan_run_dir=args.expansion_plan_run_dir,
        base_source_run_dir=args.base_source_run_dir,
        topup_source_run_dir=args.topup_source_run_dir,
        run_dir=run_dir,
        history_length=args.history_length,
        dt=args.dt,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
