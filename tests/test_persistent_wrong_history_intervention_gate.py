import math

from autodrift.persistent_wrong_history_intervention_gate import (
    PersistentVariantSpec,
    persistent_variant_specs,
    summarize_persistent_outcomes,
    summarize_proof_candidates,
    variant_injects_at_step,
)


def test_variant_injection_window_for_hold_and_late_variants():
    hold = PersistentVariantSpec(
        name="wrong_hold_4",
        family="wrong_hold",
        injection_start_step=0,
        hold_steps=4,
        clamp_hidden=True,
    )
    assert [variant_injects_at_step(hold, step) for step in range(6)] == [
        True,
        True,
        True,
        True,
        False,
        False,
    ]

    late = PersistentVariantSpec(
        name="wrong_late_4_hold_4",
        family="wrong_late",
        injection_start_step=4,
        hold_steps=4,
        clamp_hidden=True,
    )
    assert [variant_injects_at_step(late, step) for step in range(10)] == [
        False,
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        False,
        False,
    ]


def test_default_variants_include_baseline_hold_late_and_reseed():
    specs = {spec.name: spec for spec in persistent_variant_specs()}
    assert specs["normal"].family == "baseline"
    assert specs["wrong_once"].hold_steps == 1
    assert specs["wrong_hold_8"].clamp_hidden is True
    assert specs["wrong_late_8_hold_4"].injection_start_step == 8
    assert specs["wrong_late_4_once"].hold_steps == 1
    assert specs["wrong_late_4_once"].clamp_hidden is False
    assert specs["wrong_late_4_once"].family == "wrong_late_once"
    assert specs["wrong_reseed_4"].clamp_hidden is False
    assert specs["reset_hidden"].reset_hidden is True
    assert specs["zero_current_response"].zero_current_response is True


def test_late_once_variant_injects_for_one_step_only():
    spec = PersistentVariantSpec(
        name="wrong_late_8_once",
        family="wrong_late_once",
        injection_start_step=8,
        hold_steps=1,
        clamp_hidden=False,
    )
    assert [variant_injects_at_step(spec, step) for step in range(11)] == [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
    ]


def test_summarize_persistent_outcomes_counts_proof_rows():
    rows = [
        {
            "checkpoint_label": "m399",
            "target": "future_yaw_response",
            "variant": "wrong_hold_4",
            "variant_family": "wrong_hold",
            "normal_success": True,
            "variant_success": False,
            "success_drop": True,
            "collision_gap": True,
            "obstacle_completion_drop": False,
            "proof_margin_gap": False,
            "proof_candidate": True,
            "normal_margin": 0.1,
            "variant_margin": -0.1,
            "margin_gap": 0.2,
            "first_action_distance": 0.3,
            "action_trajectory_distance_mean": 0.4,
            "action_trajectory_distance_max": 0.5,
            "injection_count": 4,
        },
        {
            "checkpoint_label": "m399",
            "target": "future_yaw_response",
            "variant": "wrong_hold_4",
            "variant_family": "wrong_hold",
            "normal_success": True,
            "variant_success": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "proof_margin_gap": True,
            "proof_candidate": True,
            "normal_margin": 0.3,
            "variant_margin": 0.2,
            "margin_gap": 0.1,
            "first_action_distance": 0.1,
            "action_trajectory_distance_mean": 0.2,
            "action_trajectory_distance_max": 0.3,
            "injection_count": 4,
        },
    ]

    summary = summarize_persistent_outcomes(rows)
    assert len(summary) == 1
    row = summary[0]
    assert row["success_drop_count"] == 1
    assert row["collision_gap_count"] == 1
    assert row["proof_margin_gap_count"] == 1
    assert row["proof_candidate_count"] == 2
    assert math.isclose(row["trajectory_distance_mean"], 0.3)


def test_summarize_proof_candidates_reports_best_variant_source_diversity():
    rows = []
    for index, seed in enumerate([1, 2, 3]):
        rows.append(
            {
                "variant": "wrong_hold_4",
                "variant_family": "wrong_hold",
                "proof_candidate": True,
                "success_drop": index == 0,
                "collision_gap": index == 1,
                "obstacle_completion_drop": index == 2,
                "probe_seed": seed,
                "left_obstacle_label": "drift_required" if index < 2 else "unavoidable",
                "target": "future_yaw_response" if index < 2 else "future_braking_deceleration",
            }
        )
    rows.append(
        {
            "variant": "wrong_once",
            "variant_family": "wrong_once",
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 1,
            "left_obstacle_label": "drift_required",
            "target": "future_yaw_response",
        }
    )

    summary = summarize_proof_candidates(rows)
    assert summary["best_variant"] == "wrong_hold_4"
    assert summary["best_variant_proof_candidate_count"] == 3
    assert summary["best_variant_success_or_collision_or_completion_rows"] == 3
    assert summary["best_variant_probe_seed_count"] == 3
    assert summary["best_variant_obstacle_label_count"] == 2
    assert summary["best_variant_target_count"] == 2
