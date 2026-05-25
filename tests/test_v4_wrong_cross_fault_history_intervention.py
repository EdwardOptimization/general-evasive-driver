from autodrift.v4_wrong_cross_fault_history_intervention import (
    WRONG_HISTORY_VARIANT,
    accepted_wrong_history_rows_for_pair,
    build_pair_source_rows,
    classify_wrong_history_result,
)


def _plan(candidate_id: int, source_group_id: int, fault_family: str = "global_mu_drop"):
    return {
        "candidate_id": str(candidate_id),
        "source_group_id": str(source_group_id),
        "snapshot_uid": f"{source_group_id}:{source_group_id}:21",
        "step": "21",
        "horizon": "6",
        "target_obstacle_body_x": "12.0",
        "target_obstacle_body_y": "0.2",
        "target_obstacle_half_width": "0.8",
        "preferred_fault_family": fault_family,
    }


def _pair_row():
    return {
        "pair_id": "3",
        "left_candidate_id": "10",
        "right_candidate_id": "11",
        "left_seed": "100",
        "right_seed": "101",
        "left_fault_family": "global_mu_drop",
        "right_fault_family": "steering_fault",
        "left_fidelity_class": "current_model_fault",
        "right_fidelity_class": "current_model_fault",
        "left_warmup_mode": "brake_tap",
        "right_warmup_mode": "steer_pulse_left_right",
        "left_onset_bucket": "pre_emergency",
        "right_onset_bucket": "mid_maneuver",
        "ego_response_distance": "0.04",
        "obstacle_geometry_distance": "0.05",
        "first_action_l2": "0.05",
        "normal_margin_gap_abs": "0.1",
    }


def test_build_pair_source_rows_joins_plans_and_rejects_bad_pairs():
    selected, rejected = build_pair_source_rows(
        [_pair_row(), {**_pair_row(), "pair_id": "4", "right_candidate_id": "99"}],
        [_plan(10, 1), _plan(11, 2, "steering_fault")],
        max_pairs=8,
        max_ego_distance=0.08,
        max_obstacle_distance=0.08,
        min_first_action_l2=0.02,
    )
    assert len(selected) == 1
    assert selected[0]["left_source_group_id"] == 1
    assert selected[0]["right_source_group_id"] == 2
    assert rejected[0]["rejection_reason"] == "missing_plan_row"


def test_acceptance_requires_wrong_history_gap_action_and_closer_to_right():
    meta = {
        "pair_id": 1,
        "left_candidate_id": 10,
        "right_candidate_id": 11,
        "left_source_group_id": 1,
        "right_source_group_id": 2,
        "left_seed": 100,
        "right_seed": 101,
        "left_fault_family": "global_mu_drop",
        "right_fault_family": "steering_fault",
        "left_fidelity_class": "current_model_fault",
        "right_fidelity_class": "current_model_fault",
        "left_warmup_mode": "brake_tap",
        "right_warmup_mode": "steer_pulse_left_right",
        "left_onset_bucket": "pre_emergency",
        "right_onset_bucket": "mid_maneuver",
        "ego_response_distance": 0.04,
        "obstacle_geometry_distance": 0.05,
        "first_action_l2": 0.05,
        "normal_margin_gap_abs": 0.1,
    }
    normal = {
        **meta,
        "variant": "normal",
        "normal_success": True,
        "normal_collision": False,
        "normal_margin": 0.04,
        "variant_margin": 0.04,
    }
    wrong = {
        **meta,
        "variant": WRONG_HISTORY_VARIANT,
        "normal_success": True,
        "normal_collision": False,
        "normal_margin": 0.04,
        "variant_success": True,
        "variant_collision": False,
        "variant_margin": 0.02,
        "margin_gap_from_normal": 0.02,
        "first_action_l2_vs_normal": 0.03,
        "prefix_l2_mean_vs_normal": 0.02,
        "wrong_history_closer_to_right_action": True,
    }
    zero = {**meta, "variant": "zero_command_obs", "margin_gap_from_normal": 0.01}
    rows = accepted_wrong_history_rows_for_pair(
        [normal, wrong, zero],
        primary_margin_gap_threshold=0.01,
        mitigation_margin_gap_threshold=0.02,
        action_l2_threshold=0.014,
        require_closer_to_right=True,
    )
    assert {row["accepted_class"] for row in rows} == {"primary_wrong_history", "mitigation_wrong_history"}
    assert rows[0]["wrong_history_closer_to_right_action"] is True


def test_classify_wrong_history_result_distinguishes_zero_command_dominated_and_pass():
    accepted = []
    for idx in range(12):
        accepted.append(
            {
                "left_seed": idx,
                "right_seed": idx + 100,
                "left_fault_family": f"left{idx % 6}",
                "right_fault_family": f"right{idx % 6}",
                "left_warmup_mode": f"lw{idx % 3}",
                "right_warmup_mode": f"rw{idx % 3}",
                "left_onset_bucket": f"lo{idx % 4}",
                "right_onset_bucket": f"ro{idx % 4}",
                "left_fidelity_class": "current_model_fault",
                "right_fidelity_class": "current_model_proxy",
            }
        )
    assert (
        classify_wrong_history_result(
            actor_changed=False,
            residual_changed=False,
            reconstructed_pairs=10,
            selected_pairs=10,
            accepted_primary_rows=[],
            zero_command_accepted_like_rows=5,
            min_primary_rows=10,
            min_left_seeds=5,
            min_right_seeds=5,
            min_fault_pairs=4,
            min_warmup_pairs=3,
            min_onset_pairs=4,
            max_seed_dominance=0.5,
            max_fault_pair_dominance=0.5,
        )
        == "v4_wrong_cross_fault_history_intervention_zero_command_dominated"
    )
    assert (
        classify_wrong_history_result(
            actor_changed=False,
            residual_changed=False,
            reconstructed_pairs=12,
            selected_pairs=12,
            accepted_primary_rows=accepted,
            zero_command_accepted_like_rows=0,
            min_primary_rows=10,
            min_left_seeds=5,
            min_right_seeds=5,
            min_fault_pairs=4,
            min_warmup_pairs=3,
            min_onset_pairs=4,
            max_seed_dominance=0.5,
            max_fault_pair_dominance=0.5,
        )
        == "v4_wrong_cross_fault_history_intervention_pass"
    )
