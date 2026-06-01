from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis as diagnosis
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    role_family: str = "R0_stable_avoidable",
    label: str = "aeb_feasible",
    timing: str = "early_far",
    lateral: str = "centerline",
    hidden: str = "nominal",
    outcome: str = "success_obstacle_pass",
    termination: str = "",
    collision: bool = False,
) -> dict[str, object]:
    return {
        "role_family": role_family,
        "sampled_obstacle_label": label,
        "obstacle_longitudinal_timing_bucket": timing,
        "obstacle_lateral_offset_bucket": lateral,
        "hidden_dynamics_bucket": hidden,
        "outcome_bucket": outcome,
        "termination_reason": termination,
        "collision": collision,
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    baseline_rows = [
        _episode(outcome="off_track_noncollision_noncompletion", termination="off_track"),
        _episode(outcome="off_track_noncollision_noncompletion", termination="off_track"),
        _episode(
            role_family="R4_unavoidable_mitigation",
            label="unavoidable",
            outcome="collision_failure",
            termination="obstacle_collision",
            collision=True,
        ),
        _episode(hidden="low_mu"),
    ]
    candidate_rows = [
        _episode(outcome="off_track_noncollision_noncompletion", termination="off_track"),
        _episode(
            role_family="R4_unavoidable_mitigation",
            label="unavoidable",
            outcome="collision_failure",
            termination="obstacle_collision",
            collision=True,
        ),
        _episode(
            role_family="R4_unavoidable_mitigation",
            label="unavoidable",
            hidden="low_mu",
            outcome="collision_failure",
            termination="obstacle_collision",
            collision=True,
        ),
        _episode(hidden="low_mu"),
    ]
    spec = {
        "offtrack_target_policy": {
            "reduce_global_offtrack_count": True,
            "reduce_or_hold_target_slice_offtrack_count": True,
            "target_slice_count": 3,
            "target_slices": [
                {"axis": "role_family", "group_key": "R0_stable_avoidable"},
                {"axis": "outcome_bucket", "group_key": "off_track_noncollision_noncompletion"},
                {"axis": "termination_reason", "group_key": "off_track"},
            ],
        },
        "collision_guardrail_policy": {
            "do_not_increase_global_collision_count": True,
            "do_not_increase_guardrail_slice_collision_count": True,
            "guardrail_slice_count": 3,
            "guardrail_slices": [
                {"axis": "role_family", "group_key": "R4_unavoidable_mitigation"},
                {"axis": "hidden_dynamics_bucket", "group_key": "low_mu"},
                {"axis": "termination_reason", "group_key": "obstacle_collision"},
            ],
        },
    }
    baseline = tmp_path / "baseline.csv"
    candidate = tmp_path / "candidate.csv"
    gate = tmp_path / "gate.json"
    write_csv_rows(baseline, baseline_rows)
    write_csv_rows(candidate, candidate_rows)
    write_json(gate, spec)
    return baseline, candidate, gate


def test_slice_diagnosis_materializes_target_and_guardrail_deltas(tmp_path: Path) -> None:
    baseline, candidate, gate = _write_inputs(tmp_path)

    summary = diagnosis.run_slice_diagnosis(
        baseline_episode_rows=baseline,
        candidate_episode_rows=candidate,
        repair_gate_spec=gate,
        output_dir=tmp_path / "out",
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_guarded_repair_slice_diagnosis_pass"
    assert summary["input_episode_count_baseline"] == 4
    assert summary["input_episode_count_candidate"] == 4
    assert summary["offtrack_target_slice_count"] == 3
    assert summary["collision_guardrail_slice_count"] == 3
    assert summary["slice_delta_row_count"] == 6
    assert summary["global_offtrack_delta"] == -1
    assert summary["global_collision_delta"] == 1
    assert summary["global_offtrack_policy_pass"] is True
    assert summary["global_collision_policy_pass"] is False
    assert summary["repair_gate_pass"] is False
    assert summary["guardrail_violation_count"] == 0

    rows_path = tmp_path / "out" / "slice_delta_rows.csv"
    rows = rows_path.read_text(encoding="utf-8")
    assert "offtrack_target,offtrack_count,outcome_bucket,off_track_noncollision_noncompletion,2,1,2,1,-1,True" in rows
    assert "collision_guardrail,collision_count,termination_reason,obstacle_collision,1,2,1,2,1,False" in rows
    assert read_json(tmp_path / "out" / "summary.json")["next_blocker"] == "next"


def test_slice_diagnosis_fails_when_spec_slice_is_missing(tmp_path: Path) -> None:
    baseline, candidate, gate = _write_inputs(tmp_path)
    spec = read_json(gate)
    spec["offtrack_target_policy"]["target_slice_count"] = 4
    write_json(gate, spec)

    summary = diagnosis.run_slice_diagnosis(
        baseline_episode_rows=baseline,
        candidate_episode_rows=candidate,
        repair_gate_spec=gate,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_guarded_repair_slice_diagnosis_fail"
