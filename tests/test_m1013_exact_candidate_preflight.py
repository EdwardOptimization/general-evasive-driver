import argparse

from autodrift.m1013_exact_candidate_preflight import (
    classify_m1013_preflight,
    failure_types_for_result_class,
    parse_candidate_spec,
)


def test_parse_candidate_spec_requires_three_parts() -> None:
    spec = parse_candidate_spec("cand:runs/raw.pt:0.2")
    assert spec.name == "cand"
    assert str(spec.raw_checkpoint) == "runs/raw.pt"
    assert spec.alpha == 0.2

    try:
        parse_candidate_spec("bad")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("invalid candidate spec should fail")


def test_preflight_classifier_routes_candidate_a_pass() -> None:
    result = classify_m1013_preflight(
        materialization_contract_pass=True,
        candidate_a_pass=True,
        any_candidate_pass=True,
        b_or_c_pass_without_a=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "m1013_exact_candidate_preflight_candidate_a_pass_trust_threshold_conservative"
    assert failure_types_for_result_class(result) == ["none"]


def test_preflight_classifier_flags_metric_ordering_artifact() -> None:
    result = classify_m1013_preflight(
        materialization_contract_pass=True,
        candidate_a_pass=False,
        any_candidate_pass=True,
        b_or_c_pass_without_a=True,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "m1013_exact_candidate_preflight_metric_ordering_artifact"
    assert failure_types_for_result_class(result) == ["metric_artifact"]


def test_preflight_classifier_flags_all_selected_fail() -> None:
    result = classify_m1013_preflight(
        materialization_contract_pass=True,
        candidate_a_pass=False,
        any_candidate_pass=False,
        b_or_c_pass_without_a=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "m1013_exact_candidate_preflight_all_selected_fail_trust_threshold_supported"
    assert failure_types_for_result_class(result) == ["proof_washout"]
