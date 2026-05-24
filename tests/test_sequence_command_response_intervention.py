import numpy as np

from autodrift.sequence_command_response_intervention import (
    classify_sequence_result,
    corrupt_sequence_observation,
)


def test_corrupt_sequence_observation_zeroes_previous_commands_only_inside_horizon():
    obs = np.arange(72, dtype=np.float32)

    corrupted = corrupt_sequence_observation(
        obs,
        variant="zero_command_obs",
        step_index=1,
        horizon=2,
        raw_history=[obs],
        response_dim=9,
    )
    outside = corrupt_sequence_observation(
        obs,
        variant="zero_command_obs",
        step_index=2,
        horizon=2,
        raw_history=[obs],
        response_dim=9,
    )

    assert corrupted[9] == 0.0
    assert corrupted[10] == 0.0
    assert corrupted[11] == 0.0
    assert corrupted[8] == obs[8]
    assert outside[9] == obs[9]


def test_corrupt_sequence_observation_delays_response_stream():
    obs = np.arange(72, dtype=np.float32)
    previous = np.arange(100, 172, dtype=np.float32)

    corrupted = corrupt_sequence_observation(
        obs,
        variant="response_delay_obs",
        step_index=0,
        horizon=4,
        raw_history=[previous],
        response_dim=9,
    )

    assert np.array_equal(corrupted[:9], previous[:9])
    assert np.array_equal(corrupted[9:], obs[9:])


def test_classify_sequence_outcome_positive_requires_source_and_outcome_gates():
    result = classify_sequence_result(
        source_candidate_rows=512,
        sequence_action_critical_rows=500,
        sequence_outcome_critical_rows=30,
        unique_source_seeds=200,
        unique_source_preferred_fault_families=8,
        unique_source_fault_family_pairs=20,
        source_max_seed_dominance=0.01,
        source_max_preferred_family_dominance=0.20,
        source_sentinel_fraction=0.10,
        sentinel_false_positive_rate=0.0,
        normal_history_retention_pass=True,
        actor_parameters_changed=False,
        unique_sequence_action_seeds=80,
        unique_sequence_outcome_seeds=15,
        unique_sequence_outcome_fault_family_pairs=5,
        max_sequence_outcome_seed_dominance=0.10,
    )

    assert result == "sequence_outcome_positive"


def test_classify_sequence_source_balance_blocked_before_action_claim():
    result = classify_sequence_result(
        source_candidate_rows=512,
        sequence_action_critical_rows=500,
        sequence_outcome_critical_rows=0,
        unique_source_seeds=5,
        unique_source_preferred_fault_families=8,
        unique_source_fault_family_pairs=20,
        source_max_seed_dominance=0.40,
        source_max_preferred_family_dominance=0.20,
        source_sentinel_fraction=0.10,
        sentinel_false_positive_rate=0.0,
        normal_history_retention_pass=True,
        actor_parameters_changed=False,
        unique_sequence_action_seeds=80,
    )

    assert result == "sequence_source_balance_blocked"
