"""Materialize preferred/rejected interventions from four-wheel source rows."""

from __future__ import annotations

import argparse
import ast
import csv
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.four_wheel_dynamics import FourWheelState
from autodrift.four_wheel_fault_source_shape import build_human_view_observation
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _parse_vector(value: str) -> list[float]:
    parsed = ast.literal_eval(str(value))
    if not isinstance(parsed, list):
        raise ValueError("candidate_vector must parse to a list")
    return [float(item) for item in parsed]


def _load_action_sequences(action_lattice_rows: list[dict[str, str]]) -> dict[int, np.ndarray]:
    sequences: dict[int, np.ndarray] = {}
    for row in action_lattice_rows:
        candidate_id = int(float(row["candidate_id"]))
        vector = _parse_vector(row["candidate_vector"])
        if len(vector) % 3 != 0:
            raise ValueError(f"candidate {candidate_id} vector length is not divisible by 3")
        sequences[candidate_id] = np.asarray(vector, dtype=np.float32).reshape((-1, 3))
    return sequences


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


def _build_subset_rows(corpus_run_dir: Path) -> list[dict[str, Any]]:
    near_rows = _read_csv(corpus_run_dir / "near_boundary_source_rows.csv")
    high_rows = _read_csv(corpus_run_dir / "high_regret_source_rows.csv")
    family_rows = _read_csv(corpus_run_dir / "family_balanced_source_rows.csv")

    by_pair: dict[str, dict[str, Any]] = {}
    near_ids = {str(row["pair_id"]) for row in near_rows}
    high_ids = {str(row["pair_id"]) for row in high_rows}
    for row in near_rows + high_rows:
        pair_id = str(row["pair_id"])
        if pair_id not in by_pair:
            by_pair[pair_id] = dict(row)
    subset_rows: list[dict[str, Any]] = []
    for pair_id in sorted(by_pair, key=lambda value: int(float(value))):
        row = dict(by_pair[pair_id])
        row["source_subset"] = "near_high_union"
        row["in_near_boundary_subset"] = pair_id in near_ids
        row["in_high_regret_subset"] = pair_id in high_ids
        subset_rows.append(row)

    for row in family_rows:
        selected = dict(row)
        selected["source_subset"] = "family_balanced"
        selected["in_near_boundary_subset"] = str(row["pair_id"]) in near_ids
        selected["in_high_regret_subset"] = str(row["pair_id"]) in high_ids
        subset_rows.append(selected)
    return subset_rows


def _rollout_index(rows: list[dict[str, str]]) -> dict[tuple[int, str, int], dict[str, str]]:
    indexed: dict[tuple[int, str, int], dict[str, str]] = {}
    for row in rows:
        indexed[(int(float(row["pair_id"])), str(row["condition"]), int(float(row["candidate_id"])))] = row
    return indexed


def _intervention_specs(row: dict[str, Any]) -> list[dict[str, Any]]:
    best_a = int(float(row["best_candidate_A"]))
    best_b = int(float(row["best_candidate_B"]))
    return [
        {
            "condition": "A",
            "fault_name": row["condition_A_fault"],
            "fault_family": row["condition_A_fault_family"],
            "preferred_candidate_id": best_a,
            "rejected_candidate_id": best_b,
            "preferred_margin": _finite_float(row.get("margin_A_best_A")),
            "rejected_margin": _finite_float(row.get("margin_A_best_B")),
            "preferred_success": _bool_text(row.get("best_A_success")),
            "rejected_success": _bool_text(row.get("A_using_B_success")),
        },
        {
            "condition": "B",
            "fault_name": row["condition_B_fault"],
            "fault_family": row["condition_B_fault_family"],
            "preferred_candidate_id": best_b,
            "rejected_candidate_id": best_a,
            "preferred_margin": _finite_float(row.get("margin_B_best_B")),
            "rejected_margin": _finite_float(row.get("margin_B_best_A")),
            "preferred_success": _bool_text(row.get("best_B_success")),
            "rejected_success": _bool_text(row.get("B_using_A_success")),
        },
    ]


def _write_limits(run_dir: Path) -> Path:
    output = run_dir / "materialization_limits.md"
    output.write_text(
        "\n".join(
            [
                "# M1277 Materialization Limits",
                "",
                "M1277 materializes source-corpus counterfactual artifacts only.",
                "",
                "Allowed claim: no-training preferred/rejected source intervention artifact construction.",
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
    return output


def materialize_four_wheel_source_interventions(
    *,
    source_run_dir: Path,
    corpus_run_dir: Path,
    run_dir: Path,
    min_margin_gap: float = 0.02,
) -> dict[str, Any]:
    source_run_dir = Path(source_run_dir)
    corpus_run_dir = Path(corpus_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(source_run_dir / "summary.json")
    corpus_summary = read_json(corpus_run_dir / "summary.json")
    scenario_rows = _read_csv(source_run_dir / "scenario_summary.csv")
    action_lattice_rows = _read_csv(source_run_dir / "action_lattice.csv")
    rollout_rows = _read_csv(source_run_dir / "action_rollouts.csv")
    scenarios_by_id = {str(row["scenario_id"]): row for row in scenario_rows}
    action_sequences = _load_action_sequences(action_lattice_rows)
    rollouts = _rollout_index(rollout_rows)

    source_pair_rows = _build_subset_rows(corpus_run_dir)
    intervention_rows: list[dict[str, Any]] = []
    observation_rows: list[dict[str, Any]] = []
    action_sequence_rows: list[dict[str, Any]] = []
    intervention_id = 0
    observation_all_finite = True

    for source_row in source_pair_rows:
        pair_id = int(float(source_row["pair_id"]))
        scenario = scenarios_by_id[str(source_row["scenario_id"])]
        obs = build_human_view_observation(
            state=_scenario_state(scenario),
            previous_action=(0.0, -1.0, 1.0),
            obstacle_body_x=_finite_float(scenario.get("obstacle_body_x")),
            obstacle_body_y=_finite_float(scenario.get("obstacle_body_y")),
            obstacle_half_width=_finite_float(scenario.get("obstacle_half_width")),
        )
        observation_all_finite = bool(observation_all_finite and np.all(np.isfinite(obs)))
        for spec in _intervention_specs(source_row):
            preferred_id = int(spec["preferred_candidate_id"])
            rejected_id = int(spec["rejected_candidate_id"])
            preferred_rollout = rollouts[(pair_id, str(spec["condition"]), preferred_id)]
            rejected_rollout = rollouts[(pair_id, str(spec["condition"]), rejected_id)]
            margin_gap = float(spec["preferred_margin"]) - float(spec["rejected_margin"])
            row = {
                "intervention_id": int(intervention_id),
                "pair_id": int(pair_id),
                "source_subset": source_row["source_subset"],
                "source_family": source_row.get("source_family", source_row.get("fault_family_pair", "")),
                "condition": spec["condition"],
                "fault_name": spec["fault_name"],
                "fault_family": spec["fault_family"],
                "scenario_id": source_row["scenario_id"],
                "seed": int(float(source_row["seed"])),
                "speed": _finite_float(source_row.get("speed")),
                "obstacle_body_x": _finite_float(source_row.get("obstacle_body_x")),
                "obstacle_body_y": _finite_float(source_row.get("obstacle_body_y")),
                "obstacle_half_width": _finite_float(source_row.get("obstacle_half_width")),
                "min_own_margin": _finite_float(source_row.get("min_own_margin")),
                "min_cross_regret": _finite_float(source_row.get("min_cross_regret")),
                "near_boundary_margin_le_0_20": _bool_text(source_row.get("near_boundary_margin_le_0_20")),
                "high_regret_ge_0_05": _bool_text(source_row.get("high_regret_ge_0_05")),
                "in_near_boundary_subset": bool(source_row.get("in_near_boundary_subset", False)),
                "in_high_regret_subset": bool(source_row.get("in_high_regret_subset", False)),
                "preferred_candidate_id": preferred_id,
                "rejected_candidate_id": rejected_id,
                "preferred_margin": float(spec["preferred_margin"]),
                "rejected_margin": float(spec["rejected_margin"]),
                "margin_gap": float(margin_gap),
                "preferred_success": bool(spec["preferred_success"]),
                "rejected_success": bool(spec["rejected_success"]),
                "preferred_terminal_reason": preferred_rollout.get("terminal_reason", ""),
                "rejected_terminal_reason": rejected_rollout.get("terminal_reason", ""),
                "preferred_action_l2_from_shared_base": _finite_float(
                    preferred_rollout.get("action_l2_from_shared_base")
                ),
                "rejected_action_l2_from_shared_base": _finite_float(
                    rejected_rollout.get("action_l2_from_shared_base")
                ),
                "best_action_l2": _finite_float(source_row.get("best_action_l2")),
            }
            intervention_rows.append(row)
            observation_rows.append(
                {"intervention_id": int(intervention_id)}
                | {f"obs_{index}": float(value) for index, value in enumerate(obs.tolist())}
            )
            for role, candidate_id in (("preferred", preferred_id), ("rejected", rejected_id)):
                sequence = action_sequences[candidate_id]
                for step, action in enumerate(sequence):
                    action_sequence_rows.append(
                        {
                            "intervention_id": int(intervention_id),
                            "role": role,
                            "candidate_id": int(candidate_id),
                            "step": int(step),
                            "steer": float(action[0]),
                            "throttle": float(action[1]),
                            "brake": float(action[2]),
                        }
                    )
            intervention_id += 1

    source_pair_output_rows = []
    for row in source_pair_rows:
        source_pair_output_rows.append(
            {
                "pair_id": int(float(row["pair_id"])),
                "source_subset": row["source_subset"],
                "source_family": row.get("source_family", row.get("fault_family_pair", "")),
                "scenario_id": row["scenario_id"],
                "speed": _finite_float(row.get("speed")),
                "obstacle_body_x": _finite_float(row.get("obstacle_body_x")),
                "obstacle_body_y": _finite_float(row.get("obstacle_body_y")),
                "obstacle_half_width": _finite_float(row.get("obstacle_half_width")),
                "min_own_margin": _finite_float(row.get("min_own_margin")),
                "min_cross_regret": _finite_float(row.get("min_cross_regret")),
                "in_near_boundary_subset": bool(row.get("in_near_boundary_subset", False)),
                "in_high_regret_subset": bool(row.get("in_high_regret_subset", False)),
            }
        )

    write_csv_rows(run_dir / "intervention_rows.csv", intervention_rows)
    write_csv_rows(run_dir / "intervention_observations.csv", observation_rows)
    write_csv_rows(run_dir / "intervention_action_sequences.csv", action_sequence_rows)
    write_csv_rows(run_dir / "source_pair_rows.csv", source_pair_output_rows)
    limits_path = _write_limits(run_dir)

    near_high_pairs = {int(row["pair_id"]) for row in source_pair_output_rows if row["source_subset"] == "near_high_union"}
    family_balanced_pairs = {
        int(row["pair_id"]) for row in source_pair_output_rows if row["source_subset"] == "family_balanced"
    }
    preferred_success_fail_count = sum(not bool(row["preferred_success"]) for row in intervention_rows)
    preferred_margin_negative_count = sum(_finite_float(row["preferred_margin"]) < 0.0 for row in intervention_rows)
    margin_gap_below_threshold_count = sum(
        _finite_float(row["margin_gap"]) < float(min_margin_gap) for row in intervention_rows
    )
    summary = {
        "run_type": "four_wheel_source_intervention_materialization",
        "source_run_dir": str(source_run_dir),
        "corpus_run_dir": str(corpus_run_dir),
        "source_scenario_profile": source_summary.get("scenario_profile", ""),
        "source_accepted_separable_pairs": int(source_summary.get("accepted_separable_pairs", 0)),
        "corpus_exported_accepted_rows": int(corpus_summary.get("exported_accepted_rows", 0)),
        "near_high_union_source_pairs": int(len(near_high_pairs)),
        "near_high_union_intervention_rows": int(
            sum(1 for row in intervention_rows if row["source_subset"] == "near_high_union")
        ),
        "family_balanced_source_pairs": int(len(family_balanced_pairs)),
        "family_balanced_intervention_rows": int(
            sum(1 for row in intervention_rows if row["source_subset"] == "family_balanced")
        ),
        "source_pair_rows": int(len(source_pair_output_rows)),
        "intervention_rows": int(len(intervention_rows)),
        "observation_rows": int(len(observation_rows)),
        "action_sequence_rows": int(len(action_sequence_rows)),
        "observation_dim": 72,
        "observation_all_finite": bool(observation_all_finite),
        "preferred_success_fail_count": int(preferred_success_fail_count),
        "preferred_margin_negative_count": int(preferred_margin_negative_count),
        "margin_gap_threshold": float(min_margin_gap),
        "margin_gap_below_threshold_count": int(margin_gap_below_threshold_count),
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "intervention_rows_csv": run_dir / "intervention_rows.csv",
        "intervention_observations_csv": run_dir / "intervention_observations.csv",
        "intervention_action_sequences_csv": run_dir / "intervention_action_sequences.csv",
        "source_pair_rows_csv": run_dir / "source_pair_rows.csv",
        "materialization_limits_md": limits_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize four-wheel source intervention artifacts.")
    parser.add_argument("--source-run-dir", type=Path, required=True)
    parser.add_argument("--corpus-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="four_wheel_source_intervention_materialization")
    summary = materialize_four_wheel_source_interventions(
        source_run_dir=args.source_run_dir,
        corpus_run_dir=args.corpus_run_dir,
        run_dir=run_dir,
        min_margin_gap=args.min_margin_gap,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
