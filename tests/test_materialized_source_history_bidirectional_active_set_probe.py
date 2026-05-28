from __future__ import annotations

import csv

from autodrift.materialized_source_history_bidirectional_active_set_probe import (
    classify_bidirectional_probe,
    failure_types_for_result,
    _candidate_wrong_safe_rows,
)


def _summary(*, gate=True, normal=True, wrong=True):
    return {
        "gate_pass": gate,
        "normal_success_retention_pass": normal,
        "normal_margin_retention_pass": normal,
        "success_drop_count_retention_pass": wrong,
    }


def test_classify_bidirectional_probe_routes_failure_modes():
    assert (
        classify_bidirectional_probe(
            contract_failure=True,
            exact_improved=True,
            m267_summary=_summary(),
            m267_wrong_safe_required_rows=[],
            m183_summary=_summary(),
        )
        == "materialized_source_history_bidirectional_active_set_contract_artifact"
    )
    assert (
        classify_bidirectional_probe(
            contract_failure=False,
            exact_improved=False,
            m267_summary=_summary(),
            m267_wrong_safe_required_rows=[],
            m183_summary=_summary(),
        )
        == "materialized_source_history_bidirectional_active_set_no_exact_lift"
    )
    assert (
        classify_bidirectional_probe(
            contract_failure=False,
            exact_improved=True,
            m267_summary=_summary(gate=False, normal=False, wrong=True),
            m267_wrong_safe_required_rows=[],
            m183_summary=None,
        )
        == "materialized_source_history_bidirectional_active_set_normal_branch_proof_washout"
    )
    assert (
        classify_bidirectional_probe(
            contract_failure=False,
            exact_improved=True,
            m267_summary=_summary(gate=False, normal=True, wrong=False),
            m267_wrong_safe_required_rows=[6],
            m183_summary=None,
        )
        == "materialized_source_history_bidirectional_active_set_wrong_branch_proof_washout"
    )
    assert (
        classify_bidirectional_probe(
            contract_failure=False,
            exact_improved=True,
            m267_summary=_summary(),
            m267_wrong_safe_required_rows=[],
            m183_summary=_summary(gate=False, normal=False, wrong=True),
        )
        == "materialized_source_history_bidirectional_active_set_m183_normal_branch_proof_washout"
    )
    assert (
        classify_bidirectional_probe(
            contract_failure=False,
            exact_improved=True,
            m267_summary=_summary(),
            m267_wrong_safe_required_rows=[],
            m183_summary=_summary(),
        )
        == "materialized_source_history_bidirectional_active_set_probe_pass"
    )


def test_failure_types_for_result_are_taxonomy_labels():
    assert failure_types_for_result("materialized_source_history_bidirectional_active_set_probe_pass") == ["none"]
    assert failure_types_for_result("materialized_source_history_bidirectional_active_set_contract_artifact") == [
        "contract_violation"
    ]
    assert failure_types_for_result("materialized_source_history_bidirectional_active_set_no_exact_lift") == [
        "objective_overfit"
    ]
    assert failure_types_for_result("materialized_source_history_bidirectional_active_set_wrong_branch_proof_washout") == [
        "proof_washout"
    ]


def test_candidate_wrong_safe_rows_detects_lost_success_drop(tmp_path):
    path = tmp_path / "rows.csv"
    fieldnames = ["policy", "row_id", "success_drop"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"policy": "base", "row_id": 6, "success_drop": "True"})
        writer.writerow({"policy": "candidate", "row_id": 6, "success_drop": "False"})
        writer.writerow({"policy": "base", "row_id": 7, "success_drop": "True"})
        writer.writerow({"policy": "candidate", "row_id": 7, "success_drop": "True"})
    assert _candidate_wrong_safe_rows(path, baseline_policy="base", candidate_policy="candidate") == [6]
