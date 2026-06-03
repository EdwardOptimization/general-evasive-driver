import csv
import json

from autodrift.engineering_controller_source_only_outcome_events import (
    FILLED_METRICS,
    GAP_DELTA_FIELDNAMES,
    OUTCOME_EVENT_FIELDNAMES,
    REMAINING_UNSUPPORTED_METRICS,
    materialize_source_only_outcome_events,
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


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materialize_source_only_outcome_events_writes_event_rows(tmp_path):
    out = tmp_path / "run"
    doc = tmp_path / "m2518.md"

    summary = materialize_source_only_outcome_events(
        out,
        milestone="m2518-test",
        next_blocker="m2519-test",
        doc_path=doc,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_source_only_outcome_event_instrumentation_pass"
    )
    assert summary["source_behavior_row_count"] == 12
    assert summary["outcome_event_row_count"] == 12
    assert summary["metric_gap_delta_row_count"] == 40
    assert summary["m2516_unsupported_metric_count"] == 12
    assert summary["filled_m2516_unsupported_metric_count"] == len(FILLED_METRICS)
    assert set(summary["filled_m2516_unsupported_metrics"]) == FILLED_METRICS
    assert set(summary["remaining_unsupported_metrics"]) == REMAINING_UNSUPPORTED_METRICS
    assert summary["all_rows_source_only_diagnostic"] is True
    assert summary["all_rows_diagnostic_only_no_ranking_claim"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["new_policy_action_run"] is False
    assert summary["ranking_or_winner_fields_emitted"] is False
    assert summary["success_rate_verdict_field_emitted"] is False

    for flag in FALSE_CLAIM_FLAGS:
        assert summary[flag] is False

    rows = _read_csv(out / "outcome_event_rows.csv")
    assert len(rows) == 12
    assert set(rows[0]) == set(OUTCOME_EVENT_FIELDNAMES)
    assert {row["evidence_layer"] for row in rows} == {"source_only_diagnostic"}
    assert {row["diagnostic_only_no_ranking_claim"] for row in rows} == {"true"}
    assert {row["observation_shape"] for row in rows} == {"72"}
    assert {row["action_shape"] for row in rows} == {"3"}
    assert all(row["primary_obstacle_present"] == "true" for row in rows)
    assert all(float(row["minimum_obstacle_clearance_m"]) == float(row["minimum_obstacle_clearance_m"]) for row in rows)
    assert all("driver performance" in row["forbidden_interpretation"] for row in rows)

    summary_on_disk = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary_on_disk == summary
    assert doc.exists()


def test_outcome_metric_gap_delta_marks_filled_and_remaining_metrics(tmp_path):
    out = tmp_path / "run"
    summary = materialize_source_only_outcome_events(out, doc_path=tmp_path / "m2518.md")

    gap_delta = _read_csv(out / "outcome_metric_gap_delta.csv")
    assert len(gap_delta) == summary["metric_gap_delta_row_count"]
    assert set(gap_delta[0]) == set(GAP_DELTA_FIELDNAMES)
    delta_by_metric = {row["metric_name"]: row for row in gap_delta}

    for metric_name in FILLED_METRICS:
        assert delta_by_metric[metric_name]["m2518_support_status"] == (
            "filled_by_m2518_event_instrumentation"
        )
        assert delta_by_metric[metric_name]["m2518_supported_row_count"] == "12"
        assert delta_by_metric[metric_name]["m2518_missing_row_count"] == "0"
        assert delta_by_metric[metric_name]["filled_by_m2518"] == "True"
        assert delta_by_metric[metric_name]["remaining_unsupported"] == "False"

    for metric_name in REMAINING_UNSUPPORTED_METRICS:
        assert delta_by_metric[metric_name]["m2518_support_status"] == (
            "still_unsupported_after_m2518"
        )
        assert delta_by_metric[metric_name]["m2518_supported_row_count"] == "0"
        assert delta_by_metric[metric_name]["m2518_missing_row_count"] == "12"
        assert delta_by_metric[metric_name]["filled_by_m2518"] == "False"
        assert delta_by_metric[metric_name]["remaining_unsupported"] == "True"
