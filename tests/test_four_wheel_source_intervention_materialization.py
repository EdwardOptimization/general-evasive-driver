from __future__ import annotations

import csv
import json

from autodrift.four_wheel_source_intervention_materialization import (
    materialize_four_wheel_source_interventions,
)


def _write_csv(path, rows):
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _candidate_row(candidate_id, vector):
    return {
        "candidate_id": str(candidate_id),
        "template": f"c{candidate_id}",
        "candidate_vector": str(vector),
        "sequence_length": "2",
        "action_l2_from_shared_base": "1.0",
    }


def _rollout(pair_id, condition, candidate_id, margin, success):
    return {
        "pair_id": str(pair_id),
        "condition": condition,
        "candidate_id": str(candidate_id),
        "terminal_reason": "obstacle_completed" if success else "collision",
        "action_l2_from_shared_base": "1.0",
        "min_clearance_margin": str(margin),
    }


def _source_row(pair_id, scenario_id, subset_flags=None):
    flags = subset_flags or {}
    return {
        "pair_id": str(pair_id),
        "scenario_id": scenario_id,
        "seed": "10",
        "condition_A_fault": "fault_a",
        "condition_A_fault_family": "family",
        "condition_B_fault": "fault_b",
        "condition_B_fault_family": "family",
        "fault_family_pair": "family->family",
        "source_family": "family->family",
        "obstacle_body_x": "12.0",
        "obstacle_body_y": "0.0",
        "obstacle_half_width": "0.65",
        "best_candidate_A": "1",
        "best_candidate_B": "2",
        "best_action_l2": "1.5",
        "margin_A_best_A": "0.20",
        "margin_A_best_B": "0.10",
        "margin_B_best_B": "0.30",
        "margin_B_best_A": "0.25",
        "cross_regret_A": "0.10",
        "cross_regret_B": "0.05",
        "best_A_success": "True",
        "best_B_success": "True",
        "A_using_B_success": "False",
        "B_using_A_success": "True",
        "min_own_margin": "0.20",
        "min_cross_regret": "0.05",
        "near_boundary_margin_le_0_20": str(flags.get("near", True)),
        "high_regret_ge_0_05": str(flags.get("high", True)),
        "speed": "14.0",
    }


def test_materialize_four_wheel_source_interventions_writes_clean_artifacts(tmp_path):
    source = tmp_path / "source"
    corpus = tmp_path / "corpus"
    run = tmp_path / "run"
    source.mkdir()
    corpus.mkdir()
    (source / "summary.json").write_text(
        json.dumps({"scenario_profile": "viability_calibration", "accepted_separable_pairs": 2}),
        encoding="utf-8",
    )
    (corpus / "summary.json").write_text(json.dumps({"exported_accepted_rows": 2}), encoding="utf-8")
    _write_csv(
        source / "scenario_summary.csv",
        [
            {
                "scenario_id": "s0",
                "seed": "10",
                "vx": "14.0",
                "vy": "0.0",
                "yaw_rate": "0.0",
                "brake_force": "6000.0",
                "drive_force": "0.0",
                "obstacle_body_x": "12.0",
                "obstacle_body_y": "0.0",
                "obstacle_half_width": "0.65",
            },
            {
                "scenario_id": "s1",
                "seed": "11",
                "vx": "15.0",
                "vy": "0.0",
                "yaw_rate": "0.0",
                "brake_force": "6000.0",
                "drive_force": "0.0",
                "obstacle_body_x": "14.0",
                "obstacle_body_y": "0.0",
                "obstacle_half_width": "0.55",
            },
        ],
    )
    _write_csv(
        source / "action_lattice.csv",
        [
            _candidate_row(1, [0.75, -1.0, 1.0, 0.75, -1.0, 1.0]),
            _candidate_row(2, [-0.75, -1.0, 1.0, -0.75, -1.0, 1.0]),
        ],
    )
    _write_csv(
        source / "action_rollouts.csv",
        [
            _rollout(0, "A", 1, 0.20, True),
            _rollout(0, "A", 2, 0.10, False),
            _rollout(0, "B", 1, 0.25, True),
            _rollout(0, "B", 2, 0.30, True),
            _rollout(1, "A", 1, 0.20, True),
            _rollout(1, "A", 2, 0.10, False),
            _rollout(1, "B", 1, 0.25, True),
            _rollout(1, "B", 2, 0.30, True),
        ],
    )
    _write_csv(corpus / "near_boundary_source_rows.csv", [_source_row(0, "s0")])
    _write_csv(corpus / "high_regret_source_rows.csv", [_source_row(0, "s0")])
    _write_csv(corpus / "family_balanced_source_rows.csv", [_source_row(1, "s1")])

    summary = materialize_four_wheel_source_interventions(
        source_run_dir=source,
        corpus_run_dir=corpus,
        run_dir=run,
    )

    assert summary["near_high_union_source_pairs"] == 1
    assert summary["near_high_union_intervention_rows"] == 2
    assert summary["family_balanced_source_pairs"] == 1
    assert summary["family_balanced_intervention_rows"] == 2
    assert summary["intervention_rows"] == 4
    assert summary["observation_rows"] == 4
    assert summary["action_sequence_rows"] == 16
    assert summary["observation_dim"] == 72
    assert summary["observation_all_finite"] is True
    assert summary["preferred_success_fail_count"] == 0
    assert summary["preferred_margin_negative_count"] == 0
    assert summary["margin_gap_below_threshold_count"] == 0
    assert summary["labels_enter_actor_input"] is False
    assert (run / "intervention_rows.csv").exists()
    assert (run / "intervention_observations.csv").exists()
    assert (run / "intervention_action_sequences.csv").exists()
    assert (run / "source_pair_rows.csv").exists()
