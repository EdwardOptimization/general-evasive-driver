from pathlib import Path

import pandas as pd

from autodrift.near_miss_trust_geometry import (
    classify_candidate,
    near_miss_candidates,
    run_near_miss_trust_geometry,
    source_summary,
)


def test_classify_candidate_reports_trust_and_safety_failures():
    classified = classify_candidate(
        {
            "sequence_mean_l2": 0.09,
            "sequence_max_l2": 0.11,
            "max_delta_delta_l2": 0.01,
            "candidate_collision": False,
        },
        mean_l2_limit=0.08,
        max_l2_limit=0.10,
        delta_delta_l2_limit=0.08,
    )

    assert classified["fails_mean_l2"] is True
    assert classified["fails_max_l2"] is True
    assert classified["fails_delta_delta_l2"] is False
    assert classified["primary_failure"] == "mean_l2_excess"

    collision = classify_candidate(
        {
            "sequence_mean_l2": 0.09,
            "sequence_max_l2": 0.11,
            "max_delta_delta_l2": 0.01,
            "candidate_collision": True,
        },
        mean_l2_limit=0.08,
        max_l2_limit=0.10,
        delta_delta_l2_limit=0.08,
    )
    assert collision["primary_failure"] == "candidate_collision"


def test_near_miss_candidates_filters_unaccepted_utility_rows():
    frame = pd.DataFrame(
        [
            _candidate(0, accepted=False, margin=0.03, mean=0.09),
            _candidate(0, accepted=True, margin=0.04, mean=0.09),
            _candidate(1, accepted=False, margin=0.01, risk=0.01, mean=0.09),
            _candidate(2, accepted=False, margin=0.0, risk=0.06, mean=0.09),
        ]
    )

    near = near_miss_candidates(
        frame,
        mean_l2_limit=0.08,
        max_l2_limit=0.10,
        delta_delta_l2_limit=0.08,
        min_margin_improvement=0.02,
        min_risk_improvement=0.05,
    )

    assert near["source_index"].tolist() == [0, 2]
    assert near["primary_failure"].tolist() == ["mean_l2_excess", "mean_l2_excess"]


def test_source_summary_aggregates_near_misses_by_source():
    all_candidates = pd.DataFrame(
        [
            _candidate(0, accepted=False, margin=0.03, mean=0.09),
            _candidate(0, accepted=True, margin=0.04, mean=0.07),
            _candidate(1, accepted=False, margin=0.04, mean=0.12, source_tier="support_boundary"),
        ]
    )
    near = near_miss_candidates(
        all_candidates,
        mean_l2_limit=0.08,
        max_l2_limit=0.10,
        delta_delta_l2_limit=0.08,
        min_margin_improvement=0.02,
        min_risk_improvement=0.05,
    )

    sources = source_summary(all_candidates, near)

    assert len(sources) == 2
    first = sources[sources["source_index"] == 0].iloc[0]
    assert first["candidate_count"] == 2
    assert first["accepted_candidate_count"] == 1
    assert first["near_miss_count"] == 1
    assert bool(first["has_trust_near_miss"]) is True


def test_run_near_miss_trust_geometry_writes_outputs(tmp_path: Path):
    candidates = pd.DataFrame(
        [
            _candidate(0, accepted=False, margin=0.03, mean=0.09),
            _candidate(0, accepted=True, margin=0.04, mean=0.07),
            _candidate(1, accepted=False, margin=0.01, risk=0.01, mean=0.09),
        ]
    )
    candidates_csv = tmp_path / "candidates.csv"
    unaccepted_csv = tmp_path / "unaccepted.csv"
    candidates.to_csv(candidates_csv, index=False)
    pd.DataFrame([{"source_index": 0}, {"source_index": 1}]).to_csv(unaccepted_csv, index=False)

    summary = run_near_miss_trust_geometry(
        sequence_candidates_csv=candidates_csv,
        unaccepted_rows_csv=unaccepted_csv,
        mean_l2_limit=0.08,
        max_l2_limit=0.10,
        delta_delta_l2_limit=0.08,
        min_margin_improvement=0.02,
        min_risk_improvement=0.05,
        run_dir=tmp_path / "run",
    )

    assert summary["near_miss_candidates"] == 1
    assert summary["near_miss_sources"] == 1
    assert summary["primary_failure_counts"] == {"mean_l2_excess": 1}
    assert summary["trust_regions_changed"] is False
    assert (tmp_path / "run" / "near_miss_candidates.csv").exists()
    assert (tmp_path / "run" / "near_miss_sources.csv").exists()
    assert (tmp_path / "run" / "summary.json").exists()


def _candidate(
    source_index: int,
    *,
    accepted: bool,
    margin: float,
    mean: float,
    risk: float = 0.0,
    max_l2: float | None = None,
    delta_delta: float = 0.0,
    source_tier: str = "core_boundary",
) -> dict[str, object]:
    max_l2 = mean if max_l2 is None else max_l2
    return {
        "source_index": source_index,
        "candidate_id": source_index * 10,
        "family": "constant_delta",
        "sequence_length": 7,
        "source_tier": source_tier,
        "expansion_reason": "test",
        "surface": "fresh",
        "target": "future_yaw_response",
        "variant": "delayed_history",
        "left_seed": 100 + source_index,
        "right_seed": 200 + source_index,
        "left_step": 3,
        "right_step": 3,
        "accepted": accepted,
        "margin_improvement": margin,
        "risk_improvement": risk,
        "sequence_mean_l2": mean,
        "sequence_max_l2": max_l2,
        "max_delta_delta_l2": delta_delta,
        "candidate_collision": False,
        "candidate_off_road": False,
        "candidate_spin_out": False,
    }
