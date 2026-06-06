from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_existing_artifact_failure_localization_materialization as m2854,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path, row_count: int = 2) -> dict[str, Path]:
    design = root / "m2853.md"
    design.write_text("M2853 design\n", encoding="utf-8")
    summary = root / "m2850-summary.json"
    write_json(
        summary,
        {
            "selected_pair_count": row_count,
            "paired_execution_row_count": row_count * 2,
            "paired_delta_row_count": row_count,
            "diagnostic_success_count": 0,
            "diagnostic_collision_count": 0,
            "diagnostic_termination_counts": {"": 3, "speed_too_low": 1},
            "m2838_diagnostic_success_count": 1,
            "m2838_diagnostic_collision_count": 2,
            "m2838_diagnostic_offtrack_count": 13,
            "m2838_ordinary_denominator_allowed": False,
        },
    )
    execution_rows = []
    for index in range(1, row_count + 1):
        for subject in ("baseline", "candidate"):
            speed_low = index == 2 and subject == "candidate"
            execution_rows.append(
                {
                    "execution_row_id": f"pair-{index}-{subject}",
                    "pair_id": f"pair-{index}",
                    "checkpoint_subject": subject,
                    "observation_shape": "72",
                    "action_shape": "3",
                    "hidden_oracle_actor_input_required": "False",
                    "actor_visible_label": "False",
                    "outcome_bucket": "speed_too_low" if speed_low else "max_steps_noncompletion",
                    "termination_reason": "speed_too_low" if speed_low else "",
                }
            )
    execution_path = root / "paired_execution_rows.csv"
    write_csv_rows(execution_path, execution_rows)
    delta_rows = []
    for index in range(1, row_count + 1):
        delta_rows.append(
            {
                "pair_id": f"pair-{index}",
                "task_source_id": f"task-{index}",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_family_tag": "source-a",
                "scenario_role_primary": "capability_step_down",
                "baseline_execution_row_id": f"pair-{index}-baseline",
                "candidate_execution_row_id": f"pair-{index}-candidate",
                "baseline_success_diagnostic": "False",
                "candidate_success_diagnostic": "False",
                "baseline_collision_diagnostic": "False",
                "candidate_collision_diagnostic": "False",
                "termination_pair_changed": "False",
                "collision_pair_changed": "False",
                "candidate_minus_baseline_min_clearance_margin": "0.03" if index == 2 else "0.05",
                "candidate_minus_baseline_return": "-0.5" if index == 2 else "-1.0",
                "candidate_minus_baseline_speed_mean": "-0.2" if index == 2 else "-0.02",
                "candidate_minus_baseline_action_rate_mean": "0.002",
                "candidate_minus_baseline_previous_command_norm_mean": "0.02",
                "candidate_minus_baseline_current_action_norm_mean": "0.02",
                "candidate_minus_baseline_action_trace_delta_mean": "0.002",
                "candidate_minus_baseline_high_sideslip_fraction": "0.0",
            }
        )
    delta_path = root / "paired_delta_rows.csv"
    write_csv_rows(delta_path, delta_rows)
    return {
        "design": design,
        "summary": summary,
        "execution": execution_path,
        "delta": delta_path,
    }


def test_m2854_materializes_localization_rows_and_blocks_overclaims(tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path, row_count=2)
    output_dir = tmp_path / "m2854"
    doc_path = tmp_path / "m2854.md"
    follow_up = tmp_path / "m2855.json"

    summary = m2854.run_existing_artifact_failure_localization_materialization(
        m2853_design=paths["design"],
        m2850_summary=paths["summary"],
        paired_execution_rows=paths["execution"],
        paired_delta_rows=paths["delta"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is False
    assert summary["row_failure_localization_row_count"] == 2
    assert summary["clearance_improved_row_count"] == 2
    assert summary["return_degraded_row_count"] == 2
    assert summary["speed_degraded_row_count"] == 2
    assert summary["requires_step_trace_row_count"] == 2
    assert summary["speed_too_low_subject_count"] == 1
    assert summary["ordinary_success_denominator_allowed"] is False
    assert summary["ranking_admissible"] is False
    assert summary["winner_selected"] is False
    assert summary["driver_performance_claim_made"] is False
    assert follow_up.exists()
    assert doc_path.exists()

    rows = _read_csv(output_dir / "row_failure_localization_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    assert [row["localization_bucket"] for row in rows] == [
        "clearance_progress_tradeoff",
        "low_speed_invariant_noncompletion",
    ]
    assert all(row["diagnostic_only"] == "True" for row in rows)
    assert all(row["ranking_admissible"] == "False" for row in rows)
    assert any(row["claim_id"] == "m2854-claim-follow-up-audit-registered" for row in claim_rows)


def test_m2854_summary_passes_for_live_m2850_shape_when_accounting_matches(tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path, row_count=16)
    summary = m2854.run_existing_artifact_failure_localization_materialization(
        m2853_design=paths["design"],
        m2850_summary=paths["summary"],
        paired_execution_rows=paths["execution"],
        paired_delta_rows=paths["delta"],
        output_dir=tmp_path / "m2854",
        doc_path=tmp_path / "m2854.md",
        follow_up_manifest=tmp_path / "m2855.json",
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
