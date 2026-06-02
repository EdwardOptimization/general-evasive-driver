from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_dual_axis_task_quality_decision_panel as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _summary(path: Path, *, success: float = 0.06, offtrack: float = 0.80) -> None:
    path.mkdir(parents=True)
    write_json(
        path / "summary.json",
        {
            "result_class": "source_pass",
            "global_outcome": {
                "episode_count": 100,
                "success_rate": success,
                "collision_rate": 0.10,
                "offtrack_rate": offtrack,
                "max_step_noncompletion_rate": 0.01,
                "other_failure_rate": 0.0,
                "dominant_failure_mode": "offtrack_dominated_failure"
                if offtrack >= 0.70
                else "collision_dominated_failure",
            },
        },
    )


def _write_sources(tmp_path: Path, *, mixed: bool = False) -> tuple[Path, Path, Path, Path, Path]:
    m2362 = tmp_path / "m2362"
    m2397 = tmp_path / "m2397"
    m2413 = tmp_path / "m2413"
    m2426 = tmp_path / "m2426"
    m2428 = tmp_path / "m2428"
    _summary(m2362)
    _summary(m2397, success=0.04, offtrack=0.84)
    _summary(m2413, success=0.07, offtrack=0.74)
    m2426.mkdir()
    m2428.mkdir()
    write_json(m2426 / "summary.json", {"result_class": "reset_fail_closed"})
    write_json(
        m2428 / "summary.json",
        {
            "result_class": "reindex_pass",
            "c04_included_as_measured": False,
            "excluded_candidate_count": 1,
        },
    )
    rows = [
        {
            "group_value": "c01",
            "episode_count": 100,
            "success_rate": 0.06,
            "collision_rate": 0.12,
            "offtrack_rate": 0.76,
            "max_step_noncompletion_rate": 0.0,
            "other_failure_rate": 0.0,
            "dominant_failure_mode": "offtrack_dominated_failure",
        },
        {
            "group_value": "c02",
            "episode_count": 100,
            "success_rate": 0.06,
            "collision_rate": 0.09,
            "offtrack_rate": 0.83,
            "max_step_noncompletion_rate": 0.0,
            "other_failure_rate": 0.0,
            "dominant_failure_mode": "offtrack_dominated_failure",
        },
        {
            "group_value": "c03",
            "episode_count": 100,
            "success_rate": 0.08 if not mixed else 0.60,
            "collision_rate": 0.09,
            "offtrack_rate": 0.81 if not mixed else 0.20,
            "max_step_noncompletion_rate": 0.0,
            "other_failure_rate": 0.0,
            "dominant_failure_mode": "offtrack_dominated_failure"
            if not mixed
            else "success_dominated",
        },
    ]
    write_csv_rows(m2428 / "aggregate_by_candidate.csv", rows)
    return m2362, m2397, m2413, m2426, m2428


def test_task_quality_decision_panel_passes_on_repeated_offtrack_dominance(tmp_path: Path) -> None:
    m2362, m2397, m2413, m2426, m2428 = _write_sources(tmp_path)

    summary = runner.run_task_quality_decision_panel(
        m2362_dir=m2362,
        m2397_dir=m2397,
        m2413_dir=m2413,
        m2426_dir=m2426,
        m2428_dir=m2428,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["measured_panel_count"] == 6
    assert summary["offtrack_dominated_panel_count"] == 6
    assert summary["c04_source_coverage_gap_observed"] is True
    assert summary["route_recommendation"] == runner.ROUTE_RECOMMENDATION
    assert summary["guardrail_violation_count"] == 0
    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == runner.RESULT_PASS


def test_task_quality_decision_panel_fails_closed_on_mixed_outcomes(tmp_path: Path) -> None:
    m2362, m2397, m2413, m2426, m2428 = _write_sources(tmp_path, mixed=True)

    summary = runner.run_task_quality_decision_panel(
        m2362_dir=m2362,
        m2397_dir=m2397,
        m2413_dir=m2413,
        m2426_dir=m2426,
        m2428_dir=m2428,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["offtrack_dominated_panel_count"] == 5
    assert "metric_artifact" in summary["failure_types_observed"]
