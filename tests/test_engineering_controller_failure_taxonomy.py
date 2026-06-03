import csv

from autodrift.engineering_controller_failure_taxonomy import (
    FIELDNAMES,
    materialize_known_failure_taxonomy,
)


FALSE_CLAIM_FLAGS = [
    "environment_rollout_run",
    "simulator_step_run",
    "external_high_fidelity_simulation_included",
    "policy_action_run",
    "policy_rollout_run",
    "measured_validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "success_rate_computed",
    "controller_family_verdict_computed",
    "driver_performance_claim_made",
    "verdict_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "level3_self_id_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
]


def test_materialize_known_failure_taxonomy_writes_structured_limitations(tmp_path):
    summary = materialize_known_failure_taxonomy(
        tmp_path / "run",
        milestone="m2510-test",
        next_blocker="m2511-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_known_failure_taxonomy_materialization_pass"
    )
    assert summary["taxonomy_row_count"] >= 8
    assert summary["expected_min_taxonomy_row_count"] == 8
    assert summary["required_fields"] == FIELDNAMES
    assert summary["required_fields_present"] is True
    assert summary["source_artifacts_exist"] is True
    assert summary["missing_source_artifacts"] == []
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["source_only_diagnostic_scope"] is True
    assert {"high", "medium", "low"}.issubset(set(summary["severity_counts"]))

    for flag in FALSE_CLAIM_FLAGS:
        assert summary[flag] is False

    with (tmp_path / "run" / "failure_taxonomy.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == summary["taxonomy_row_count"]
    assert set(rows[0]) == set(FIELDNAMES)
    assert {row["source_exists"] for row in rows} == {"True"}
    assert {
        "validation_boundary",
        "metric_artifact",
        "self_id_evidence_gap",
        "deployability_scope",
        "behavior_regression",
        "scenario_sampling_failure",
    }.issubset({row["failure_category"] for row in rows})
    assert "driver performance or success-rate benchmark" in {
        row["forbidden_interpretation"] for row in rows
    }
    assert (tmp_path / "run" / "summary.json").exists()
