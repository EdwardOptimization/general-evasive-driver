from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    idx: int,
    *,
    termination_reason: str = "off_track",
    success: bool = False,
    collision: bool = False,
    clearance: float = 5.0,
    overshoot: float = 0.05,
) -> dict[str, object]:
    return {
        "workload_id": f"workload_{idx}",
        "termination_reason": termination_reason,
        "outcome_bucket": "off_track_noncollision_noncompletion"
        if termination_reason == "off_track"
        else "success_obstacle_pass",
        "success": success,
        "role_success": success,
        "collision": collision,
        "min_clearance_margin": clearance,
        "max_off_track_overshoot": overshoot,
    }


def _write_source(path: Path, *, empty: bool = False) -> None:
    path.mkdir()
    write_json(path / "summary.json", {"result_class": "measured_pass"})
    rows: list[dict[str, object]] = []
    if not empty:
        rows.extend(
            [
                _episode(0, termination_reason="", success=True, overshoot=0.0),
                _episode(1, collision=True, clearance=2.0, overshoot=0.0),
                _episode(2, clearance=-0.1, overshoot=0.0),
                _episode(3, clearance=5.0, overshoot=0.05),
                _episode(4, clearance=50.0, overshoot=0.25),
            ]
        )
    write_csv_rows(path / "episode_rows.csv", rows)


def _write_sources(tmp_path: Path, *, empty_m2413: bool = False) -> tuple[Path, Path, Path]:
    m2362 = tmp_path / "m2362"
    m2397 = tmp_path / "m2397"
    m2413 = tmp_path / "m2413"
    _write_source(m2362)
    _write_source(m2397)
    _write_source(m2413, empty=empty_m2413)
    return m2362, m2397, m2413


def test_hard_soft_offtrack_metric_split_panel_preserves_success_and_classes(tmp_path: Path) -> None:
    m2362, m2397, m2413 = _write_sources(tmp_path)

    summary = runner.run_hard_soft_offtrack_metric_split_panel(
        m2362_dir=m2362,
        m2397_dir=m2397,
        m2413_dir=m2413,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["panel_row_count"] == 12
    assert summary["thresholds_m"] == [0.02, 0.05, 0.1, 0.2]
    assert summary["actual_success_preserved"] is True
    assert summary["actual_success_preservation_violation_count"] == 0
    assert summary["max_hard_offtrack_failure_rate_at_0_20m"] > 0.0
    assert summary["min_soft_offtrack_violation_rate_at_0_20m"] > 0.0
    assert summary["actual_success_improvement_claim_made"] is False
    assert summary["guardrail_violation_count"] == 0
    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == runner.RESULT_PASS


def test_hard_soft_offtrack_metric_split_panel_fails_closed_on_missing_source_rows(tmp_path: Path) -> None:
    m2362, m2397, m2413 = _write_sources(tmp_path, empty_m2413=True)

    summary = runner.run_hard_soft_offtrack_metric_split_panel(
        m2362_dir=m2362,
        m2397_dir=m2397,
        m2413_dir=m2413,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["source_episode_counts"]["m2413"] == 0
    assert "scenario_sampling_failure" in summary["failure_types_observed"]
