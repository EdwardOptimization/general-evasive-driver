from autodrift.tail_action_replay_sufficiency_gate import (
    action_replay_variant_name,
    summarize_action_replay_proof,
)


def test_action_replay_variant_name_uses_hold_step_suffix():
    assert action_replay_variant_name(8) == "wrong_tail_action_replay_8"


def test_summarize_action_replay_proof_separates_action_replay_from_hidden_hold():
    rows = [
        {
            "variant": "wrong_tail_once",
            "variant_family": "wrong_tail_once",
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 1,
            "left_obstacle_label": "unavoidable",
            "target": "future_yaw_response",
        },
        {
            "variant": "wrong_tail_hidden_hold_8",
            "variant_family": "wrong_tail_hidden_hold",
            "proof_candidate": True,
            "success_drop": True,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 2,
            "left_obstacle_label": "unavoidable",
            "target": "future_yaw_response",
        },
        {
            "variant": "wrong_tail_action_replay_8",
            "variant_family": "wrong_tail_action_replay",
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": True,
            "obstacle_completion_drop": False,
            "probe_seed": 3,
            "left_obstacle_label": "drift_required",
            "target": "future_braking_deceleration",
        },
        {
            "variant": "wrong_tail_action_replay_8",
            "variant_family": "wrong_tail_action_replay",
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": True,
            "probe_seed": 4,
            "left_obstacle_label": "unavoidable",
            "target": "future_yaw_response",
        },
    ]

    summary = summarize_action_replay_proof(rows)

    assert summary["wrong_tail_once_total_proof_candidate_count"] == 1
    assert summary["wrong_tail_once_total_event_rows"] == 0
    assert summary["hidden_hold_total_proof_candidate_count"] == 1
    assert summary["hidden_hold_total_event_rows"] == 1
    assert summary["action_replay_total_proof_candidate_count"] == 2
    assert summary["action_replay_total_event_rows"] == 2
    assert summary["best_action_replay_variant"] == "wrong_tail_action_replay_8"
    assert summary["best_action_replay_event_rows"] == 2
    assert summary["best_action_replay_probe_seed_count"] == 2
    assert summary["best_action_replay_obstacle_label_count"] == 2
    assert summary["best_action_replay_target_count"] == 2
