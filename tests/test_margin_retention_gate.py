import numpy as np
import pandas as pd

from autodrift.margin_retention_gate import (
    apply_gate_checks,
    build_gate_summary,
    load_margin_deltas,
    summarize_candidates,
    summarize_sources,
    write_margin_retention_gate,
)


def _deltas_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source": "broad",
                "seed": 1,
                "baseline_policy": "base",
                "candidate_policy": "safe",
                "baseline_success": True,
                "candidate_success": True,
                "outcome": "unchanged_success",
                "critical_reason": "",
                "near_boundary": False,
                "margin_regressed": False,
                "near_margin_regressed": False,
                "baseline_min_clearance_margin": 0.20,
                "candidate_min_clearance_margin": 0.24,
                "min_clearance_margin_delta": 0.04,
            },
            {
                "source": "critical",
                "seed": 2,
                "baseline_policy": "base",
                "candidate_policy": "safe",
                "baseline_success": False,
                "candidate_success": True,
                "outcome": "improved",
                "critical_reason": "binary_outcome_changed;near_boundary;low_margin_success",
                "near_boundary": True,
                "margin_regressed": False,
                "near_margin_regressed": False,
                "baseline_min_clearance_margin": -0.01,
                "candidate_min_clearance_margin": 0.01,
                "min_clearance_margin_delta": 0.02,
            },
            {
                "source": "broad",
                "seed": 1,
                "baseline_policy": "base",
                "candidate_policy": "regressed",
                "baseline_success": True,
                "candidate_success": False,
                "outcome": "regressed",
                "critical_reason": "binary_outcome_changed;near_boundary;small_penetration_collision",
                "near_boundary": True,
                "margin_regressed": True,
                "near_margin_regressed": True,
                "baseline_min_clearance_margin": 0.01,
                "candidate_min_clearance_margin": -0.01,
                "min_clearance_margin_delta": -0.02,
            },
            {
                "source": "critical",
                "seed": 2,
                "baseline_policy": "base",
                "candidate_policy": "regressed",
                "baseline_success": False,
                "candidate_success": False,
                "outcome": "unchanged_failure",
                "critical_reason": "near_boundary;near_margin_regressed",
                "near_boundary": True,
                "margin_regressed": True,
                "near_margin_regressed": True,
                "baseline_min_clearance_margin": -0.01,
                "candidate_min_clearance_margin": -0.04,
                "min_clearance_margin_delta": -0.03,
            },
        ]
    )


def test_summarize_candidates_counts_success_and_margin_regressions():
    summary = summarize_candidates(_deltas_frame())
    safe = summary[summary["candidate_policy"] == "safe"].iloc[0]
    regressed = summary[summary["candidate_policy"] == "regressed"].iloc[0]

    assert int(safe["binary_regressed_seeds"]) == 0
    assert int(safe["near_margin_regressed_seeds"]) == 0
    assert np.isclose(safe["success_delta_rate"], 0.5)
    assert int(regressed["binary_regressed_seeds"]) == 1
    assert int(regressed["near_margin_regressed_seeds"]) == 2


def test_apply_gate_checks_marks_only_clean_candidate_as_passed():
    checked = apply_gate_checks(
        summarize_candidates(_deltas_frame()),
        min_success_delta=0.0,
        max_binary_regressed_seeds=0,
        max_near_margin_regressed_seeds=0,
        min_margin_delta_mean=0.0,
    )

    assert bool(checked.loc[checked["candidate_policy"] == "safe", "passed"].iloc[0])
    assert not bool(checked.loc[checked["candidate_policy"] == "regressed", "passed"].iloc[0])


def test_build_gate_summary_reports_passed_candidates():
    summary, candidate_summary, source_summary = build_gate_summary(
        _deltas_frame(),
        min_success_delta=0.0,
        max_binary_regressed_seeds=0,
        max_near_margin_regressed_seeds=0,
        min_margin_delta_mean=0.0,
    )

    assert summary["status"] == "passed"
    assert summary["passed_candidates"] == ["safe"]
    assert len(candidate_summary) == 2
    assert set(source_summary["source"]) == {"broad", "critical"}


def test_load_margin_deltas_parses_bool_columns(tmp_path):
    path = tmp_path / "deltas.csv"
    _deltas_frame().assign(baseline_success=lambda frame: frame["baseline_success"].astype(str)).to_csv(
        path,
        index=False,
    )

    loaded = load_margin_deltas(path)

    assert loaded["baseline_success"].dtype == bool


def test_write_margin_retention_gate_writes_artifacts(tmp_path):
    path = tmp_path / "deltas.csv"
    _deltas_frame().to_csv(path, index=False)

    manifest = write_margin_retention_gate(
        tmp_path / "gate",
        seed_delta_csv=path,
        min_success_delta=0.0,
        max_binary_regressed_seeds=0,
        max_near_margin_regressed_seeds=0,
        min_margin_delta_mean=0.0,
    )

    assert manifest["summary"]["status"] == "passed"
    assert (tmp_path / "gate" / "candidate_gate_summary.csv").exists()
    assert (tmp_path / "gate" / "source_gate_summary.csv").exists()
    assert (tmp_path / "gate" / "gate_summary.json").exists()
    assert (tmp_path / "gate" / "gate_report.md").exists()
