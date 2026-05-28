from __future__ import annotations

import argparse

import pytest

from autodrift.materialized_source_history_public_base_promotion_generalization_gate import (
    BASE_POLICY_LABEL,
    CANDIDATE_POLICY_LABEL,
    classify_public_base_promotion_gate,
    compare_behavior_rows,
    compare_generalization_rows,
    failure_types_for_result_class,
    next_blocker_for_result_class,
    parse_seed_tuple,
)


def _classification_kwargs(**overrides):
    kwargs = {
        "actor_inputs_changed": False,
        "forbidden_parameter_mutation_detected": False,
        "log_std_l2": 0.0,
        "exact_pass": True,
        "proof_pass": True,
        "source_diverse_pass": True,
        "generalization_pass": True,
        "behavior_pass": True,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
    }
    kwargs.update(overrides)
    return kwargs


def test_parse_seed_tuple_rejects_empty_and_duplicates() -> None:
    assert parse_seed_tuple("1,2,3") == (1, 2, 3)
    with pytest.raises(argparse.ArgumentTypeError):
        parse_seed_tuple("")
    with pytest.raises(argparse.ArgumentTypeError):
        parse_seed_tuple("1,2,1")


def test_classify_public_base_promotion_gate_orders_failures() -> None:
    assert classify_public_base_promotion_gate(**_classification_kwargs()).endswith("_candidate")
    assert classify_public_base_promotion_gate(
        **_classification_kwargs(actor_inputs_changed=True, exact_pass=False)
    ).endswith("_contract_artifact")
    assert classify_public_base_promotion_gate(**_classification_kwargs(exact_pass=False)).endswith(
        "_exact_retention_failed"
    )
    assert classify_public_base_promotion_gate(**_classification_kwargs(source_diverse_pass=False)).endswith(
        "_proof_washout"
    )
    assert classify_public_base_promotion_gate(**_classification_kwargs(generalization_pass=False)).endswith(
        "_generalization_regression"
    )
    assert classify_public_base_promotion_gate(**_classification_kwargs(behavior_pass=False)).endswith(
        "_behavior_regression"
    )


def test_failure_types_and_next_blocker_follow_result_class() -> None:
    candidate = "materialized_source_history_public_base_promotion_gate_candidate"
    assert failure_types_for_result_class(candidate) == ["none"]
    assert next_blocker_for_result_class(candidate) == "m1370-paper-route-public-base-promotion-audit"
    assert failure_types_for_result_class(
        "materialized_source_history_public_base_promotion_gate_generalization_regression"
    ) == ["scenario_sampling_failure"]
    assert next_blocker_for_result_class(
        "materialized_source_history_public_base_promotion_gate_behavior_regression"
    ) == "m1370-paper-route-public-base-behavior-regression-audit"


def test_compare_generalization_rows_applies_tolerances() -> None:
    rows = [
        {
            "distribution": "fresh_public",
            "seed": 1,
            "policy_label": BASE_POLICY_LABEL,
            "ablation": "none",
            "success_rate": 0.90,
            "termination_rate": 0.10,
            "min_clearance_margin_mean": 1.0,
            "collision_rate": 0.05,
        },
        {
            "distribution": "fresh_public",
            "seed": 1,
            "policy_label": CANDIDATE_POLICY_LABEL,
            "ablation": "none",
            "success_rate": 0.891,
            "termination_rate": 0.109,
            "min_clearance_margin_mean": 0.996,
            "collision_rate": 0.059,
        },
        {
            "distribution": "moderate_ood",
            "seed": 2,
            "policy_label": BASE_POLICY_LABEL,
            "ablation": "none",
            "success_rate": 0.70,
            "termination_rate": 0.30,
            "min_clearance_margin_mean": 0.8,
            "collision_rate": 0.12,
        },
        {
            "distribution": "moderate_ood",
            "seed": 2,
            "policy_label": CANDIDATE_POLICY_LABEL,
            "ablation": "none",
            "success_rate": 0.68,
            "termination_rate": 0.32,
            "min_clearance_margin_mean": 0.79,
            "collision_rate": 0.12,
        },
    ]
    comparisons = compare_generalization_rows(rows)
    assert [row["generalization_pass"] for row in comparisons] == [True, False]


def test_compare_behavior_rows_requires_ordering() -> None:
    rows = []
    for label, ablation, success, termination in (
        (BASE_POLICY_LABEL, "none", 0.80, 0.20),
        (CANDIDATE_POLICY_LABEL, "none", 0.80, 0.20),
        (CANDIDATE_POLICY_LABEL, "reset_recurrent_state", 0.78, 0.22),
        (CANDIDATE_POLICY_LABEL, "zero_all_response", 0.70, 0.30),
    ):
        rows.append(
            {
                "seed": 1,
                "policy_label": label,
                "ablation": ablation,
                "success_rate": success,
                "termination_rate": termination,
            }
        )
    assert compare_behavior_rows(rows)[0]["behavior_pass"] is True

    rows[-1]["success_rate"] = 0.79
    assert compare_behavior_rows(rows)[0]["behavior_pass"] is False
