from __future__ import annotations

import argparse

from autodrift.materialized_source_history_replay_aware_retention_probe import (
    classify_retention_probe,
    failure_types_for_result,
    parse_force_keys,
)


def test_parse_force_keys_accepts_empty_and_rows():
    assert parse_force_keys("") == set()
    assert parse_force_keys("m183_m170:1, m267_m264:16") == {
        ("m183_m170", 1),
        ("m267_m264", 16),
    }
    for text in ("m183_m170", ":1"):
        try:
            parse_force_keys(text)
        except (argparse.ArgumentTypeError, ValueError):
            pass
        else:
            raise AssertionError(f"parse_force_keys should reject {text!r}")


def test_classify_retention_probe_routes_failures_and_pass():
    assert (
        classify_retention_probe(
            contract_failure=True,
            exact_improved=True,
            m267_pass=True,
            m183_ran=True,
            m183_pass=True,
            beat_alpha005=True,
        )
        == "materialized_source_history_replay_aware_retention_contract_artifact"
    )
    assert (
        classify_retention_probe(
            contract_failure=False,
            exact_improved=False,
            m267_pass=True,
            m183_ran=True,
            m183_pass=True,
            beat_alpha005=True,
        )
        == "materialized_source_history_replay_aware_retention_no_exact_lift"
    )
    assert (
        classify_retention_probe(
            contract_failure=False,
            exact_improved=True,
            m267_pass=False,
            m183_ran=False,
            m183_pass=False,
            beat_alpha005=True,
        )
        == "materialized_source_history_replay_aware_retention_m267_proof_washout"
    )
    assert (
        classify_retention_probe(
            contract_failure=False,
            exact_improved=True,
            m267_pass=True,
            m183_ran=True,
            m183_pass=False,
            beat_alpha005=True,
        )
        == "materialized_source_history_replay_aware_retention_m183_proof_washout"
    )
    assert (
        classify_retention_probe(
            contract_failure=False,
            exact_improved=True,
            m267_pass=True,
            m183_ran=True,
            m183_pass=True,
            beat_alpha005=False,
        )
        == "materialized_source_history_replay_aware_retention_replay_pass_but_weak"
    )
    assert (
        classify_retention_probe(
            contract_failure=False,
            exact_improved=True,
            m267_pass=True,
            m183_ran=True,
            m183_pass=True,
            beat_alpha005=True,
        )
        == "materialized_source_history_replay_aware_retention_probe_pass"
    )


def test_failure_types_for_result_are_taxonomy_labels():
    assert failure_types_for_result("materialized_source_history_replay_aware_retention_probe_pass") == ["none"]
    assert failure_types_for_result("materialized_source_history_replay_aware_retention_contract_artifact") == [
        "contract_violation"
    ]
    assert failure_types_for_result("materialized_source_history_replay_aware_retention_no_exact_lift") == [
        "objective_overfit"
    ]
    assert failure_types_for_result("materialized_source_history_replay_aware_retention_replay_pass_but_weak") == [
        "objective_overfit"
    ]
    assert failure_types_for_result("materialized_source_history_replay_aware_retention_m183_proof_washout") == [
        "proof_washout"
    ]
