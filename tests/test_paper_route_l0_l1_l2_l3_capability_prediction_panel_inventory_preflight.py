import csv

from autodrift.artifacts import read_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import (
    REQUIRED_PROFILES,
    write_preflight_artifacts,
)


def _write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _workload_rows(task_source_id, *, complete=True):
    profiles = REQUIRED_PROFILES if complete else REQUIRED_PROFILES[:2]
    return [
        {
            "workload_id": f"{task_source_id}::{profile}",
            "task_source_id": task_source_id,
            "profile_name": profile,
            "task_family": "T4",
            "source_edge": "actuator_delay_step|capability_step_up",
            "window_tag": "reveal_plus_4",
            "executable_source_family": "capability_step_up",
            "env_template_family": "t4_capability_step_temporal",
            "strata": "test",
            "profile_config_path": f"configs/{profile}.json",
            "checkpoint_path": f"checkpoints/{profile}.pt",
            "config_exists": "True",
            "checkpoint_exists": "True",
            "environment_rollout_scheduled": "False",
            "training_scheduled": "False",
            "profile_specific_tuning": "False",
        }
        for profile in profiles
    ]


def test_inventory_classifies_usable_and_missing_rows(tmp_path):
    workload = tmp_path / "runs" / "m1690" / "executable_workload_matrix.csv"
    _write_rows(workload, _workload_rows("m1680-spec-0001") + _workload_rows("m1680-spec-0002", complete=False))
    m2877 = tmp_path / "runs" / "m2877"
    m2838 = tmp_path / "runs" / "m2838"
    m2868 = tmp_path / "runs" / "m2868"
    m2828 = tmp_path / "runs" / "m2828"
    candidate_row = {
        "candidate_id": "candidate-1",
        "task_source_id": "m1680-spec-0001",
        "source_family_tag": "capability_step_up",
        "scenario_role_primary": "capability_step_up",
    }
    _write_rows(m2877 / "fresh_candidate_rows.csv", [candidate_row])
    _write_rows(m2838 / "selected_candidate_rows.csv", [{**candidate_row, "source_family_tag": "actuator_delay_step"}])
    _write_rows(
        m2877 / "candidate_execution_rows.csv",
        [
            {
                "task_source_id": "m1680-spec-0001",
                "brake_scale": "1.0",
                "speed_mean": "8.0",
                "max_abs_yaw_rate": "0.3",
                "lateral_peak": "1.2",
                "previous_command_norm_mean": "0.1",
                "recovery_time_proxy": "1.4",
                "min_clearance_margin": "2.0",
                "first_obstacle_pass_step": "50",
            }
        ],
    )
    _write_rows(m2877 / "prior_surface_exclusion_rows.csv", [{"task_source_id": "m1680-spec-0002"}])

    output_dir = tmp_path / "runs" / "m2884"
    follow_up = tmp_path / "experiments" / "manifests" / "m2885.json"
    summary = write_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=follow_up,
        m1690_workload=workload,
        m2877_dir=m2877,
        m2868_dir=m2868,
        m2838_dir=m2838,
        m2828_dir=m2828,
    )

    assert summary["status_pass"] is True
    assert summary["usable_candidate_count"] == 1
    assert summary["missing_data_candidate_count"] == 1
    assert summary["false_claim_flags"]["training_run"] is False
    assert follow_up.exists()
    assert (output_dir / "candidate_panel_rows.csv").exists()
    assert read_json(output_dir / "summary.json")["decision"] == "panel_inventory_available_route_to_m2885_result_audit"


def test_inventory_reports_insufficient_when_targets_are_missing(tmp_path):
    workload = tmp_path / "runs" / "m1690" / "executable_workload_matrix.csv"
    _write_rows(workload, _workload_rows("m1680-spec-0001"))
    m2877 = tmp_path / "runs" / "m2877"
    _write_rows(
        m2877 / "fresh_candidate_rows.csv",
        [{"candidate_id": "candidate-1", "task_source_id": "m1680-spec-0001", "source_family_tag": "capability_step_up"}],
    )

    output_dir = tmp_path / "runs" / "m2884"
    follow_up = tmp_path / "experiments" / "manifests" / "m2885.json"
    summary = write_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=follow_up,
        m1690_workload=workload,
        m2877_dir=m2877,
        m2868_dir=tmp_path / "missing_m2868",
        m2838_dir=tmp_path / "missing_m2838",
        m2828_dir=tmp_path / "missing_m2828",
    )

    assert summary["status_pass"] is False
    assert summary["usable_candidate_count"] == 0
    assert summary["target_inventory_all_available"] is False
    assert follow_up.exists()
