from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_scenario_task_quality_support_audit as audit
from autodrift.artifacts import read_json, write_csv_rows


def _episode(label: str, *, profile: str = "L0_current_masked", seed_id: int = 1) -> dict[str, object]:
    return {
        "obstacle_label": label,
        "profile_name": profile,
        "seed_id": seed_id,
        "episode_seed": seed_id + 100,
        "outcome_bucket": "success_obstacle_pass",
        "obstacle_completed": True,
        "collision": False,
        "termination_reason": "",
        "min_clearance_margin": 1.2,
        "high_sideslip_fraction": 0.0,
        "max_abs_beta": 0.1,
        "max_abs_yaw_rate": 0.2,
        "impact_speed_proxy": 0.0,
        "collision_mitigation_score": 0.0,
        "recovery_success": False,
        "controlled_drift_recovery_success": False,
        "action_rate_mean": 0.01,
        "speed_mean": 12.0,
        "track_width": 8.0,
        "left_curve_steps": 5,
        "right_curve_steps": 5,
        "near_zero_steps": 20,
        "initial_mu": 0.6,
        "mu": 0.8,
        "brake_scale": 1.0,
        "steer_tau_scale": 1.2,
        "drive_tau_scale": 1.0,
        "mass_scale": 1.0,
        "inertia_scale": 1.0,
        "mass": 1450.0,
        "first_recovery_time_s": "",
        "recovery_time_proxy": 0.0,
        "time_to_first_off_track_s": "",
        "max_off_track_overshoot": 0.0,
        "off_track_severity_proxy": 0.0,
        "selected_readiness_floor_pass": False,
    }


def _matrix_row(profile: str = "L0_current_masked", seed_id: int = 1) -> dict[str, object]:
    return {
        "matrix_id": f"{profile}::seed_{seed_id}",
        "profile_name": profile,
        "seed_id": seed_id,
        "uses_hidden_oracle_actor_inputs": False,
        "uses_wheel_or_slip_inputs": False,
        "uses_reference_or_ttc_inputs": False,
        "training_started": False,
        "policy_action_executed": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def test_support_audit_routes_to_scenario_generation_when_roles_missing(tmp_path: Path) -> None:
    episode_path = tmp_path / "m2244_episode_rows.csv"
    matrix_path = tmp_path / "training_matrix.csv"
    rows = (
        [_episode("aes_feasible", seed_id=index) for index in range(70)]
        + [_episode("drift_required", seed_id=100 + index) for index in range(70)]
        + [_episode("unavoidable", seed_id=200 + index) for index in range(70)]
    )
    write_csv_rows(episode_path, rows)
    write_csv_rows(matrix_path, [_matrix_row(seed_id=index) for index in range(3)])

    summary = audit.run_support_audit(
        episode_rows=[episode_path],
        training_matrices=[matrix_path],
        output_dir=tmp_path / "out",
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_quality_support_audit_pass"
    assert summary["episode_row_count"] == 210
    assert summary["explicit_role_family_count"] == 3
    assert summary["role_missing_count"] == 2
    assert summary["primary_route"] == "scenario_task_family_generation_design"
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected"] is False
    assert (tmp_path / "out" / "role_support.csv").exists()
    assert (tmp_path / "out" / "scenario_axis_support.csv").exists()
    assert read_json(tmp_path / "out" / "summary.json")["next_blocker"] == "next"


def test_support_audit_detects_missing_input(tmp_path: Path) -> None:
    episode_path = tmp_path / "m2244_episode_rows.csv"
    write_csv_rows(episode_path, [_episode("aes_feasible")])

    summary = audit.run_support_audit(
        episode_rows=[episode_path],
        training_matrices=[tmp_path / "missing_matrix.csv"],
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_scenario_task_quality_support_audit_fail"
    assert summary["missing_input_count"] == 1
