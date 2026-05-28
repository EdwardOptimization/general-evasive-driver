from __future__ import annotations

import argparse
from pathlib import Path

from autodrift.materialized_source_history_interpolation_preflight import (
    _classify_result,
    _failure_types,
    _next_blocker,
    parse_alphas,
)


def test_parse_alphas_sorts_and_rejects_invalid():
    assert parse_alphas("0.02,0.005,0.1") == (0.005, 0.02, 0.1)
    for text in ("", "0", "-0.1", "0.1,0.1", "1.1"):
        try:
            parse_alphas(text)
        except argparse.ArgumentTypeError:
            pass
        else:
            raise AssertionError(f"parse_alphas should reject {text!r}")


def test_classify_result_routes_contract_exact_and_replay_failures():
    assert (
        _classify_result(
            exact_candidate_count=1,
            m267_pass_count=1,
            selected_alpha=0.02,
            contract_failure=False,
        )
        == "materialized_source_history_interpolation_preflight_pass"
    )
    assert (
        _classify_result(
            exact_candidate_count=0,
            m267_pass_count=0,
            selected_alpha=None,
            contract_failure=False,
        )
        == "materialized_source_history_interpolation_preflight_no_exact_candidate"
    )
    assert (
        _classify_result(
            exact_candidate_count=2,
            m267_pass_count=0,
            selected_alpha=None,
            contract_failure=False,
        )
        == "materialized_source_history_interpolation_preflight_m267_proof_washout"
    )
    assert (
        _classify_result(
            exact_candidate_count=2,
            m267_pass_count=1,
            selected_alpha=None,
            contract_failure=False,
        )
        == "materialized_source_history_interpolation_preflight_m183_proof_washout"
    )
    assert (
        _classify_result(
            exact_candidate_count=2,
            m267_pass_count=1,
            selected_alpha=0.01,
            contract_failure=True,
        )
        == "materialized_source_history_interpolation_preflight_contract_artifact"
    )


def test_failure_types_and_next_blocker_are_structured():
    assert _failure_types("materialized_source_history_interpolation_preflight_pass") == ["none"]
    assert _failure_types("materialized_source_history_interpolation_preflight_contract_artifact") == [
        "contract_violation"
    ]
    assert _failure_types("materialized_source_history_interpolation_preflight_no_exact_candidate") == [
        "objective_overfit"
    ]
    assert _failure_types("materialized_source_history_interpolation_preflight_m267_proof_washout") == [
        "proof_washout"
    ]
    assert "active-set" in _next_blocker("materialized_source_history_interpolation_preflight_m267_proof_washout")
    assert "boundary-cliff" in _next_blocker("materialized_source_history_interpolation_preflight_m183_proof_washout")
