from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_response_prediction_trace_localization_materialization as m2861,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    audit = root / "m2860.md"
    audit.write_text("M2860 accepts M2859\n", encoding="utf-8")
    summary = root / "m2859-summary.json"
    write_json(
        summary,
        {
            "status_pass": True,
            "actor_contract_shape_72_action_3": True,
            "response_prediction_trace_row_count": 8,
            "valid_prediction_row_count": 6,
            "instrumentation_gap_row_count": 2,
            "response_prediction_dim": 2,
            "response_prediction_horizon": 2,
        },
    )
    trace_rows = [
        {
            "surface_id": "m2850_explanatory",
            "pair_id": "pair-1",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "checkpoint_subject": "baseline",
            "horizon_index": "1",
            "response_prediction_dim": "2",
            "response_prediction_available": "True",
            "target_available": "True",
            "predicted_values": "[1.0, 2.0]",
            "target_values": "[0.0, 2.5]",
            "future_label_actor_visible": "False",
            "actor_visible_allowed": "False",
            "hidden_oracle_actor_input_required": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "surface_id": "m2850_explanatory",
            "pair_id": "pair-1",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "checkpoint_subject": "baseline",
            "horizon_index": "1",
            "response_prediction_dim": "2",
            "response_prediction_available": "True",
            "target_available": "True",
            "predicted_values": "[1.5, 2.2]",
            "target_values": "[0.0, 2.6]",
            "future_label_actor_visible": "False",
            "actor_visible_allowed": "False",
            "hidden_oracle_actor_input_required": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "surface_id": "m2850_explanatory",
            "pair_id": "pair-1",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "checkpoint_subject": "baseline",
            "horizon_index": "2",
            "response_prediction_dim": "2",
            "response_prediction_available": "True",
            "target_available": "True",
            "predicted_values": "[0.1, 0.2]",
            "target_values": "[0.0, 0.0]",
            "future_label_actor_visible": "False",
            "actor_visible_allowed": "False",
            "hidden_oracle_actor_input_required": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "surface_id": "m2850_explanatory",
            "pair_id": "pair-1",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "checkpoint_subject": "baseline",
            "horizon_index": "2",
            "response_prediction_dim": "2",
            "response_prediction_available": "True",
            "target_available": "False",
            "predicted_values": "",
            "target_values": "",
            "future_label_actor_visible": "False",
            "actor_visible_allowed": "False",
            "hidden_oracle_actor_input_required": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "surface_id": "m2850_explanatory",
            "pair_id": "pair-1",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "checkpoint_subject": "candidate",
            "horizon_index": "1",
            "response_prediction_dim": "2",
            "response_prediction_available": "True",
            "target_available": "True",
            "predicted_values": "[0.2, 0.5]",
            "target_values": "[0.0, 0.0]",
            "future_label_actor_visible": "False",
            "actor_visible_allowed": "False",
            "hidden_oracle_actor_input_required": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "surface_id": "m2850_explanatory",
            "pair_id": "pair-1",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "checkpoint_subject": "candidate",
            "horizon_index": "1",
            "response_prediction_dim": "2",
            "response_prediction_available": "True",
            "target_available": "True",
            "predicted_values": "[0.3, 0.4]",
            "target_values": "[0.0, 0.0]",
            "future_label_actor_visible": "False",
            "actor_visible_allowed": "False",
            "hidden_oracle_actor_input_required": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "surface_id": "m2850_explanatory",
            "pair_id": "pair-1",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "checkpoint_subject": "candidate",
            "horizon_index": "2",
            "response_prediction_dim": "2",
            "response_prediction_available": "True",
            "target_available": "True",
            "predicted_values": "[0.0, 0.1]",
            "target_values": "[0.0, 0.0]",
            "future_label_actor_visible": "False",
            "actor_visible_allowed": "False",
            "hidden_oracle_actor_input_required": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "surface_id": "m2850_explanatory",
            "pair_id": "pair-1",
            "task_source_id": "task-1",
            "profile_name": "L3_online_gru",
            "checkpoint_subject": "candidate",
            "horizon_index": "2",
            "response_prediction_dim": "2",
            "response_prediction_available": "True",
            "target_available": "False",
            "predicted_values": "",
            "target_values": "",
            "future_label_actor_visible": "False",
            "actor_visible_allowed": "False",
            "hidden_oracle_actor_input_required": "False",
            "ranking_admissible": "False",
            "ordinary_success_denominator_allowed": "False",
        },
    ]
    trace_path = root / "trace.csv"
    write_csv_rows(trace_path, trace_rows)
    episode_path = root / "episode.csv"
    write_csv_rows(
        episode_path,
        [
            {"surface_id": "m2850_explanatory", "pair_id": "pair-1", "task_source_id": "task-1", "checkpoint_subject": "baseline"},
            {"surface_id": "m2850_explanatory", "pair_id": "pair-1", "task_source_id": "task-1", "checkpoint_subject": "candidate"},
        ],
    )
    gap_path = root / "gap.csv"
    write_csv_rows(
        gap_path,
        [
            {
                "surface_id": "m2850_explanatory",
                "pair_id": "pair-1",
                "task_source_id": "task-1",
                "checkpoint_subject": "baseline",
                "horizon_index": "2",
                "future_label_actor_visible": "False",
                "actor_visible_allowed": "False",
                "hidden_oracle_actor_input_required": "False",
            },
            {
                "surface_id": "m2850_explanatory",
                "pair_id": "pair-1",
                "task_source_id": "task-1",
                "checkpoint_subject": "candidate",
                "horizon_index": "2",
                "future_label_actor_visible": "False",
                "actor_visible_allowed": "False",
                "hidden_oracle_actor_input_required": "False",
            },
        ],
    )
    m2857_path = root / "m2857.csv"
    write_csv_rows(
        m2857_path,
        [
            {
                "surface_id": "m2850_explanatory",
                "pair_id": "pair-1",
                "task_source_id": "task-1",
                "per_step_localization_bucket": "response_prediction_timing_unresolved",
                "training_recipe_signal": "progress_preserving_clearance_objective",
            }
        ],
    )
    return {
        "audit": audit,
        "summary": summary,
        "trace": trace_path,
        "episode": episode_path,
        "gap": gap_path,
        "m2857": m2857_path,
    }


def test_build_localization_rows_groups_by_subject_horizon_and_channel(tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    trace_rows = _read_csv(paths["trace"])
    m2857_rows = _read_csv(paths["m2857"])

    rows = m2861.build_response_prediction_localization_rows(
        trace_rows=trace_rows,
        m2857_localization_rows=m2857_rows,
    )

    assert len(rows) == 8
    assert any(row["localization_bucket"] == "relative_high_response_error" for row in rows)
    assert any(row["recipe_signal"] == "ego_response_prediction_loss_weight_review" for row in rows)
    assert all(row["future_label_actor_visible"] is False for row in rows)
    assert all(row["ranking_admissible"] is False for row in rows)
    assert all(row["m2857_training_recipe_signal"] == "progress_preserving_clearance_objective" for row in rows)


def test_m2861_runner_writes_artifacts_and_blocks_overclaims(tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2861"
    doc_path = tmp_path / "m2861.md"
    follow_up = tmp_path / "m2862.json"

    summary = m2861.run_response_prediction_trace_localization_materialization(
        m2860_audit=paths["audit"],
        m2859_summary=paths["summary"],
        response_prediction_trace_rows=paths["trace"],
        response_prediction_episode_rows=paths["episode"],
        instrumentation_gap_rows=paths["gap"],
        m2857_localization_rows=paths["m2857"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["response_prediction_localization_row_count"] == 8
    assert summary["response_prediction_channel_summary_row_count"] == 4
    assert summary["m2859_valid_prediction_row_count"] == 6
    assert summary["m2859_gap_row_count"] == 2
    assert summary["environment_rerun"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_verdict_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert follow_up.exists()
    assert doc_path.exists()
    assert read_json(follow_up)["next_blocker"] == (
        "m2863-engineering-controller-route-a-response-predictive-recurrent-belief-"
        "response-prediction-localization-branch-synthesis"
    )

    localization_rows = _read_csv(output_dir / "response_prediction_localization_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert localization_rows
    assert all(row["future_label_actor_visible"] == "False" for row in localization_rows)
    assert all(row["ordinary_success_denominator_allowed"] == "False" for row in localization_rows)
    assert any(row["claim_id"] == "m2861-claim-follow-up-audit-registered" for row in claim_rows)
    assert all(row["status_pass"] == "True" for row in gate_rows)
