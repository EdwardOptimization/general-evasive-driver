from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_dual_axis_boundary_threshold_sensitivity_panel as runner
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


def _write_source(path: Path, *, low_sensitivity: bool = False) -> None:
    path.mkdir()
    write_json(path / "summary.json", {"result_class": "measured_pass"})
    rows: list[dict[str, object]] = []
    if low_sensitivity:
        for idx in range(10):
            rows.append(_episode(idx, clearance=-0.1, overshoot=0.5))
    else:
        for idx in range(8):
            rows.append(_episode(idx, clearance=4.0, overshoot=0.05))
        for idx in range(8, 10):
            rows.append(_episode(idx, clearance=4.0, overshoot=0.15))
    for idx in range(10, 12):
        rows.append(_episode(idx, termination_reason="", success=True))
    write_csv_rows(path / "episode_rows.csv", rows)


def _write_sources(tmp_path: Path, *, low_sensitivity: bool = False) -> tuple[Path, Path, Path]:
    m2362 = tmp_path / "m2362"
    m2397 = tmp_path / "m2397"
    m2413 = tmp_path / "m2413"
    _write_source(m2362)
    _write_source(m2397)
    _write_source(m2413, low_sensitivity=low_sensitivity)
    return m2362, m2397, m2413


def test_boundary_threshold_sensitivity_panel_passes_on_high_soft_success_gain(tmp_path: Path) -> None:
    m2362, m2397, m2413 = _write_sources(tmp_path)

    summary = runner.run_boundary_threshold_sensitivity_panel(
        m2362_dir=m2362,
        m2397_dir=m2397,
        m2413_dir=m2413,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["panel_row_count"] == 12
    assert summary["thresholds_m"] == [0.02, 0.05, 0.1, 0.2]
    assert summary["min_soft_success_gain_at_0_20m"] > 0.50
    assert summary["actual_success_improvement_claim_made"] is False
    assert summary["guardrail_violation_count"] == 0
    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == runner.RESULT_PASS


def test_boundary_threshold_sensitivity_panel_fails_closed_on_low_sensitivity(tmp_path: Path) -> None:
    m2362, m2397, m2413 = _write_sources(tmp_path, low_sensitivity=True)

    summary = runner.run_boundary_threshold_sensitivity_panel(
        m2362_dir=m2362,
        m2397_dir=m2397,
        m2413_dir=m2413,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["min_soft_success_gain_at_0_20m"] < 0.50
    assert "metric_artifact" in summary["failure_types_observed"]
