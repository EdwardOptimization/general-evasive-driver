from __future__ import annotations

from autodrift.executable_v2_reset_time_aes_sampler_diagnostic import (
    ACCEPTED,
    REJECT_AEB_FEASIBLE,
    TARGET_LABEL,
    claim_boundary_rows,
    evaluate_obstacle_candidate,
    failed_aes_target_ids,
    replay_reset_time_obstacle_attempts,
    summarize_attempts,
)


def _base_env_config() -> dict:
    return {
        "track_kind": "circle",
        "track_radius": 18.0,
        "speed_range": [20.0, 20.0],
        "friction_limited_speed": False,
        "randomization": {
            "mu_range": [1.0, 1.0],
            "mass_scale_range": [1.0, 1.0],
            "cg_shift_range": [0.0, 0.0],
            "inertia_scale_range": [1.0, 1.0],
            "tire_stiffness_scale_range": [1.0, 1.0],
            "drive_scale_range": [1.0, 1.0],
            "brake_scale_range": [1.0, 1.0],
            "actuator_tau_scale_range": [1.0, 1.0],
        },
        "obstacle": {
            "enabled": True,
            "allowed_labels": ["aes_feasible"],
            "require_aeb_infeasible": True,
            "distance_range": [18.0, 18.0],
            "half_width_range": [0.3, 0.3],
            "max_sample_attempts": 3,
        },
    }


def test_evaluate_candidate_accepts_aes_case() -> None:
    row = evaluate_obstacle_candidate(
        env_config=_base_env_config(),
        speed_ref=20.0,
        mu=1.0,
        obstacle_distance=18.0,
        obstacle_half_width=0.3,
    )

    assert row["label"] == TARGET_LABEL
    assert row["accepted"] is True
    assert row["reject_reason"] == ACCEPTED


def test_replay_obstacle_attempts_counts_aeb_gate_rejections() -> None:
    config = _base_env_config()
    config["obstacle"]["distance_range"] = [80.0, 80.0]
    config["obstacle"]["half_width_range"] = [0.3, 0.3]
    rows = replay_reset_time_obstacle_attempts(env_config=config, seed=7, max_attempts=4)
    summary = summarize_attempts(rows)

    assert summary["attempt_count"] == 4
    assert summary["accepted_count"] == 0
    assert summary["dominant_reject_reason"] == REJECT_AEB_FEASIBLE
    assert summary["reject_reason_counts"][REJECT_AEB_FEASIBLE] == 4


def test_failed_aes_target_ids_ignores_successes_and_non_aes_rows() -> None:
    rows = [
        {"v2_panel_spec_id": "aes-fail", "v2_task_label": "aes_feasible", "reset_success": "False"},
        {"v2_panel_spec_id": "aes-pass", "v2_task_label": "aes_feasible", "reset_success": "True"},
        {"v2_panel_spec_id": "aeb-fail", "v2_task_label": "aeb_feasible", "reset_success": "False"},
    ]

    assert failed_aes_target_ids(rows) == {"aes-fail"}


def test_claim_boundary_blocks_ranking_and_reset_repair_claims() -> None:
    rows = claim_boundary_rows()
    by_claim = {row["claim"]: row for row in rows}

    assert by_claim["reset_time_sampler_diagnostic_plan"]["admissible"] is True
    assert by_claim["reset_feasibility_repaired"]["admissible"] is False
    assert by_claim["controller_family_ranking"]["admissible"] is False
