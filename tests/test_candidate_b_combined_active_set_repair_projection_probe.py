from autodrift.candidate_b_combined_active_set_repair_projection_probe import (
    classify_combined_active_set_probe,
    failure_types_for_combined_probe,
    next_blocker_for_combined_probe,
    parse_alphas,
)


def test_parse_alphas_validates_range() -> None:
    assert parse_alphas("0.05,0.1,1.0") == (0.05, 0.1, 1.0)

    try:
        parse_alphas("1.5")
    except Exception as exc:
        assert "alphas must be in [0, 1]" in str(exc)
    else:
        raise AssertionError("expected invalid alpha to raise")


def test_classify_combined_active_set_probe_maps_temporal_projection_results() -> None:
    assert (
        classify_combined_active_set_probe(
            projection_result_class="candidate_b_temporal_safe_projection_first_replay_candidate",
            actor_inputs_changed=False,
            ppo_used=False,
            promoted=False,
        )
        == "candidate_b_combined_active_set_projection_first_replay_candidate"
    )
    assert (
        classify_combined_active_set_probe(
            projection_result_class="candidate_b_temporal_safe_projection_no_temporal_candidate",
            actor_inputs_changed=False,
            ppo_used=False,
            promoted=False,
        )
        == "candidate_b_combined_active_set_repair_temporal_regression"
    )
    assert (
        classify_combined_active_set_probe(
            projection_result_class="candidate_b_temporal_safe_projection_proof_washout",
            actor_inputs_changed=False,
            ppo_used=False,
            promoted=False,
        )
        == "candidate_b_combined_active_set_projection_proof_washout"
    )
    assert (
        classify_combined_active_set_probe(
            projection_result_class="candidate_b_temporal_safe_projection_first_replay_candidate",
            actor_inputs_changed=True,
            ppo_used=False,
            promoted=False,
        )
        == "candidate_b_combined_active_set_repair_contract_artifact"
    )


def test_failure_types_and_next_blocker_for_combined_probe() -> None:
    assert failure_types_for_combined_probe("candidate_b_combined_active_set_projection_first_replay_candidate") == [
        "none"
    ]
    assert failure_types_for_combined_probe("candidate_b_combined_active_set_repair_temporal_regression") == [
        "proof_washout"
    ]
    assert (
        next_blocker_for_combined_probe("candidate_b_combined_active_set_repair_temporal_regression")
        == "candidate_b_combined_active_set_temporal_objective_integration_design"
    )
    assert (
        next_blocker_for_combined_probe("candidate_b_combined_active_set_projection_proof_washout")
        == "candidate_b_combined_active_set_first_replay_failure_audit"
    )
