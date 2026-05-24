from autodrift.dynamics import VehicleParams
from autodrift.extreme_dynamics_scenario_corpus import (
    FaultSpec,
    apply_fault_params,
    classify_cross_fault_result,
    classify_extreme_result,
    fault_from_dict,
    pairing_rule_from_dict,
)


def test_fault_from_dict_requires_supported_family():
    fault = fault_from_dict(
        {
            "name": "brake_fade",
            "family": "brake_authority_drop",
            "severity": "severe",
            "activation_step": 12,
            "params": {"max_brake_force_scale": 0.5},
        }
    )

    assert fault.name == "brake_fade"
    assert fault.activation_step == 12
    assert fault.params["max_brake_force_scale"] == 0.5


def test_apply_fault_params_preserves_single_track_shape():
    params = VehicleParams()
    fault = FaultSpec(
        name="combo",
        family="combined_fault",
        severity="severe",
        activation_step=0,
        params={"mu_scale": 0.5, "max_brake_force_scale": 0.4, "steer_tau_scale": 2.0, "cg_shift": 0.1},
    )

    updated = apply_fault_params(params, fault)

    assert updated.mu == params.mu * 0.5
    assert updated.max_brake_force == params.max_brake_force * 0.4
    assert updated.steer_tau == params.steer_tau * 2.0
    assert updated.wheelbase == params.wheelbase
    assert updated.lf > params.lf


def test_classify_extreme_result_positive_requires_diversity():
    result = classify_extreme_result(
        matched_pair_count=100,
        accepted_rows=90,
        history_action_critical_rows=40,
        wrong_history_action_critical_rows=40,
        reset_history_action_critical_rows=40,
        unique_fault_families=4,
        unique_severities=2,
        unique_seeds=30,
        normal_failed_rejected=0,
        history_insensitive_rejected=10,
        model_fidelity_blocked=5,
        min_accepted_rows=80,
        min_history_rows=30,
        min_unique_fault_families=4,
        min_unique_severities=2,
        min_unique_seeds=30,
    )

    assert result == "extreme_source_positive"


def test_classify_extreme_result_history_insensitive():
    result = classify_extreme_result(
        matched_pair_count=100,
        accepted_rows=0,
        history_action_critical_rows=0,
        wrong_history_action_critical_rows=0,
        reset_history_action_critical_rows=0,
        unique_fault_families=0,
        unique_severities=0,
        unique_seeds=0,
        normal_failed_rejected=5,
        history_insensitive_rejected=95,
        model_fidelity_blocked=5,
        min_accepted_rows=80,
        min_history_rows=30,
        min_unique_fault_families=4,
        min_unique_severities=2,
        min_unique_seeds=30,
    )

    assert result == "history_insensitive_too_mild"


def test_classify_extreme_result_matched_empty_before_sparse():
    result = classify_extreme_result(
        matched_pair_count=0,
        accepted_rows=0,
        history_action_critical_rows=0,
        wrong_history_action_critical_rows=0,
        reset_history_action_critical_rows=0,
        unique_fault_families=0,
        unique_severities=0,
        unique_seeds=0,
        normal_failed_rejected=0,
        history_insensitive_rejected=0,
        model_fidelity_blocked=0,
        min_accepted_rows=80,
        min_history_rows=30,
        min_unique_fault_families=4,
        min_unique_severities=2,
        min_unique_seeds=30,
    )

    assert result == "matched_state_empty"


def test_classify_extreme_result_separates_reset_only_sparse_rows():
    result = classify_extreme_result(
        matched_pair_count=100,
        accepted_rows=20,
        history_action_critical_rows=20,
        wrong_history_action_critical_rows=0,
        reset_history_action_critical_rows=20,
        unique_fault_families=4,
        unique_severities=2,
        unique_seeds=10,
        normal_failed_rejected=5,
        history_insensitive_rejected=75,
        model_fidelity_blocked=5,
        min_accepted_rows=80,
        min_history_rows=30,
        min_unique_fault_families=4,
        min_unique_severities=2,
        min_unique_seeds=30,
    )

    assert result == "extreme_reset_sparse"


def test_pairing_rule_from_dict_parses_optional_severities():
    rule = pairing_rule_from_dict(
        {
            "preferred_family": "global_mu_drop",
            "wrong_family": "brake_authority_drop",
            "preferred_severities": ["moderate", "severe"],
            "wrong_severities": ["severe"],
        }
    )

    assert rule.preferred_family == "global_mu_drop"
    assert rule.wrong_family == "brake_authority_drop"
    assert rule.preferred_severities == ("moderate", "severe")
    assert rule.wrong_severities == ("severe",)


def test_classify_cross_fault_result_requires_wrong_history_rows():
    result = classify_cross_fault_result(
        matched_pair_count=100,
        wrong_history_action_critical_rows=0,
        reset_history_action_critical_rows=40,
        normal_failed_rejected=0,
        history_insensitive_rejected=60,
        unique_preferred_fault_families=4,
        unique_wrong_fault_families=4,
        unique_severities=2,
        unique_seeds=30,
        min_accepted_rows=80,
        min_history_rows=30,
        min_unique_fault_families=4,
        min_unique_severities=2,
        min_unique_seeds=30,
    )

    assert result == "cross_fault_reset_only"


def test_classify_cross_fault_result_positive_requires_source_diversity():
    result = classify_cross_fault_result(
        matched_pair_count=120,
        wrong_history_action_critical_rows=90,
        reset_history_action_critical_rows=10,
        normal_failed_rejected=0,
        history_insensitive_rejected=20,
        unique_preferred_fault_families=4,
        unique_wrong_fault_families=4,
        unique_severities=2,
        unique_seeds=30,
        min_accepted_rows=80,
        min_history_rows=30,
        min_unique_fault_families=4,
        min_unique_severities=2,
        min_unique_seeds=30,
    )

    assert result == "cross_fault_wrong_positive"
