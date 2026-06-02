from __future__ import annotations

import math
from pathlib import Path

from autodrift import paper_route_current_sim_scenario_task_family_feasibility_calibration as calibration
from autodrift import paper_route_current_sim_scenario_task_family_measured_execution as measured
from autodrift.artifacts import write_csv_rows
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.outcome_metric_instrumentation import (
    OUTCOME_METRIC_FIELDS,
    R4_MITIGATION_CANONICAL_FIELDS,
    compute_episode_outcome_metrics,
)


def test_r4_mitigation_aliases_are_logging_only_and_availability_bounded() -> None:
    metrics = compute_episode_outcome_metrics(
        [
            {
                "step": 1,
                "dt": 0.1,
                "track_width": 6.0,
                "speed": 9.0,
                "beta": 0.1,
                "yaw_rate": 0.2,
                "lateral_error": 0.0,
                "collision": False,
                "min_clearance_margin": 1.0,
            },
            {
                "step": 2,
                "dt": 0.1,
                "track_width": 6.0,
                "speed": 7.5,
                "beta": -0.3,
                "yaw_rate": 1.4,
                "lateral_error": 0.2,
                "collision": True,
                "min_clearance_margin": -0.2,
                "active_obstacle_body_x": 3.0,
                "active_obstacle_body_y": -0.4,
                "termination_reason": "obstacle_collision",
            },
        ],
        default_dt=0.1,
        default_track_width=6.0,
    )

    assert metrics["impact_speed_proxy"] == 7.5
    assert metrics["impact_speed_mps"] == 7.5
    assert metrics["impact_speed_mps_available"] is True
    assert metrics["time_to_collision_s"] == 0.2
    assert metrics["time_to_collision_s_available"] is True
    assert metrics["collision_side_proxy"] == "front"
    assert metrics["collision_angle_or_side"] == ""
    assert metrics["collision_angle_or_side_available"] is False
    assert math.isnan(metrics["delta_v_at_impact_mps"])
    assert metrics["delta_v_at_impact_mps_available"] is False
    assert metrics["post_event_speed_mps_available"] is False
    assert metrics["recoverability_window_success"] is False
    assert metrics["recoverability_window_success_available"] is False


def test_scenario_task_family_fieldnames_preserve_r4_mitigation_fields() -> None:
    for field in R4_MITIGATION_CANONICAL_FIELDS:
        assert field in OUTCOME_METRIC_FIELDS
        assert field in measured.EPISODE_FIELDNAMES
        assert field in calibration.EPISODE_FIELDNAMES
    assert len(measured.EPISODE_FIELDNAMES) == len(set(measured.EPISODE_FIELDNAMES))
    assert len(calibration.EPISODE_FIELDNAMES) == len(set(calibration.EPISODE_FIELDNAMES))


def test_scenario_task_family_csv_headers_keep_r4_mitigation_fields(tmp_path: Path) -> None:
    row = {field: "" for field in measured.EPISODE_FIELDNAMES}
    row.update(
        {
            "workload_id": "workload",
            "impact_speed_mps": 4.2,
            "impact_speed_mps_available": True,
            "time_to_collision_s": 0.8,
            "time_to_collision_s_available": True,
            "delta_v_at_impact_mps_available": False,
            "recoverability_window_success_available": False,
        }
    )
    output = tmp_path / "episode_rows.csv"
    write_csv_rows(output, [row], fieldnames=measured.EPISODE_FIELDNAMES)
    rows = read_csv_rows(output)
    assert rows[0]["impact_speed_mps"] == "4.2"
    assert rows[0]["impact_speed_mps_available"] == "True"
    assert rows[0]["time_to_collision_s"] == "0.8"
    assert rows[0]["delta_v_at_impact_mps_available"] == "False"
