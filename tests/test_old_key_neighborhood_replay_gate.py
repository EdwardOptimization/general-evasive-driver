from pathlib import Path

import pandas as pd
import pytest

from autodrift.artifacts import read_json
from autodrift.old_key_neighborhood_replay_gate import (
    compare_candidate_guard_results,
    infer_guard_results_from_compact,
    run_old_key_neighborhood_replay_gate,
    summarize_candidate_comparison,
)
from autodrift.old_key_neighborhood_gate import (
    CandidateThresholds,
    DiversityThresholds,
    OldKeyNeighborhoodThresholds,
)


def _thresholds() -> OldKeyNeighborhoodThresholds:
    diversity = DiversityThresholds(
        min_rows=4,
        max_rows=4,
        min_seed_blocks=2,
        min_physical_pairs_or_keys=4,
        min_source_steps=2,
        min_target_buckets=2,
        max_seed_block_dominance=0.5,
        max_physical_pair_dominance=0.5,
    )
    return OldKeyNeighborhoodThresholds(
        broad=diversity,
        compact=diversity,
        candidate=CandidateThresholds(
            max_selected_accepted_regressions=0,
            min_selected_gap_p10=-0.0005,
            min_selected_gap_min=-0.002,
            endpoint_repair_accepted_regressions=2,
            endpoint_repair_gap_p10=-0.001,
            endpoint_repair_gap_min=-0.01,
        ),
    )


def _compact_row(index: int, *, seed_block: str) -> dict:
    return {
        "record_type": "m341_mined_case",
        "seed_block": seed_block,
        "source_csv": "guard.csv",
        "case_id": f"{9900 + index}|perturbed|{20 + index}|{18 + index}|10.0|-1.0|0.{index}",
        "key": f"{9900 + index}|perturbed|{20 + index}|{18 + index}",
        "seed": 9900 + index,
        "source_condition": "perturbed",
        "source_step": 20 + (index % 2),
        "paired_step": 18 + index,
        "target_obstacle_distance": 9.5 + (index % 2),
        "relocated_obstacle_body_y": -1.2 + 0.2 * (index % 2),
        "relocated_obstacle_half_width": 0.7 + 0.1 * index,
        "old_key_9944": False,
    }


def _compact_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _compact_row(0, seed_block="A"),
            _compact_row(1, seed_block="A"),
            _compact_row(2, seed_block="B"),
            _compact_row(3, seed_block="B"),
        ]
    )


def _guard_row(compact_row: dict, *, policy: str, accepted: bool, gap_delta: float = 0.0) -> dict:
    return {
        "policy": policy,
        "key": compact_row["key"],
        "seed": compact_row["seed"],
        "source_condition": compact_row["source_condition"],
        "source_step": compact_row["source_step"],
        "paired_step": compact_row["paired_step"],
        "target_obstacle_distance": compact_row["target_obstacle_distance"],
        "relocated_obstacle_body_y": compact_row["relocated_obstacle_body_y"],
        "relocated_obstacle_half_width": compact_row["relocated_obstacle_half_width"],
        "accepted": accepted,
        "normal_success": accepted,
        "normal_margin": 0.02 + gap_delta,
        "wrong_history_margin": 0.01,
        "margin_gap": 0.01 + gap_delta,
    }


def _guard_frame(*, candidate_bad: bool = False) -> pd.DataFrame:
    rows: list[dict] = []
    for index, compact_row in enumerate(_compact_frame().to_dict("records")):
        rows.append(_guard_row(compact_row, policy="base", accepted=True))
        rows.append(
            _guard_row(
                compact_row,
                policy="candidate",
                accepted=not (candidate_bad and index in {1, 2}),
                gap_delta=-0.02 if candidate_bad and index == 1 else -0.00001 * index,
            )
        )
    return pd.DataFrame(rows)


def _candidate_pool_with_diagnostic(compact: pd.DataFrame) -> pd.DataFrame:
    diagnostic = compact.iloc[0].to_dict()
    diagnostic.update(
        {
            "record_type": "m133_diagnostic",
            "case_id": "9944|perturbed|28|28|11.000000|-1.000000|0.900000",
            "key": "9944|perturbed|28|28",
            "old_key_9944": True,
        }
    )
    return pd.DataFrame([*compact.to_dict("records"), diagnostic])


def test_compare_candidate_guard_results_builds_candidate_deltas():
    compact = _compact_frame()
    comparison = compare_candidate_guard_results(
        compact_frame=compact,
        guard_results=_guard_frame(),
        baseline_policy="base",
        candidate_policy="candidate",
    )

    assert len(comparison) == 4
    assert comparison["candidate_accepted_regression"].sum() == 0
    assert comparison["candidate_gap_delta"].min() < 0.0


def test_summarize_candidate_comparison_passes_for_small_regressions():
    comparison = compare_candidate_guard_results(
        compact_frame=_compact_frame(),
        guard_results=_guard_frame(),
        baseline_policy="base",
        candidate_policy="candidate",
    )

    metrics = summarize_candidate_comparison(comparison, thresholds=_thresholds())

    assert metrics["candidate_gate_pass"]
    assert metrics["candidate_accepted_regressions"] == 0
    assert metrics["passes_diversity_targets"]


def test_summarize_candidate_comparison_flags_bad_candidate():
    comparison = compare_candidate_guard_results(
        compact_frame=_compact_frame(),
        guard_results=_guard_frame(candidate_bad=True),
        baseline_policy="base",
        candidate_policy="candidate",
    )

    metrics = summarize_candidate_comparison(comparison, thresholds=_thresholds())

    assert not metrics["candidate_gate_pass"]
    assert metrics["candidate_repair_needed"]
    assert metrics["candidate_accepted_regressions"] == 2
    assert "candidate_accepted_regressions>0" in metrics["candidate_gate_failures"]


def test_run_replay_gate_writes_summary(tmp_path: Path):
    compact = _compact_frame()
    compact_csv = tmp_path / "compact.csv"
    guard_csv = tmp_path / "guard.csv"
    pool_csv = tmp_path / "pool.csv"
    compact.to_csv(compact_csv, index=False)
    _guard_frame().to_csv(guard_csv, index=False)
    _candidate_pool_with_diagnostic(compact).to_csv(pool_csv, index=False)

    result = run_old_key_neighborhood_replay_gate(
        compact_corpus_csv=compact_csv,
        guard_results_csvs=(guard_csv,),
        baseline_policy="base",
        candidate_policy="candidate",
        candidate_pool_csv=pool_csv,
        run_dir=tmp_path / "run",
        thresholds=_thresholds(),
    )

    assert result["overall_pass"]
    assert read_json(tmp_path / "run" / "summary.json")["m133_diagnostics"]["old_key_9944_included"]
    assert (tmp_path / "run" / "old_key_replay_comparison_rows.csv").exists()


def test_run_replay_gate_fails_when_diagnostic_missing(tmp_path: Path):
    compact = _compact_frame()
    compact_csv = tmp_path / "compact.csv"
    guard_csv = tmp_path / "guard.csv"
    compact.to_csv(compact_csv, index=False)
    _guard_frame().to_csv(guard_csv, index=False)

    result = run_old_key_neighborhood_replay_gate(
        compact_corpus_csv=compact_csv,
        guard_results_csvs=(guard_csv,),
        baseline_policy="base",
        candidate_policy="candidate",
        run_dir=tmp_path / "run",
        thresholds=_thresholds(),
    )

    assert not result["overall_pass"]
    assert "lineage_invalid" in result["failure_types"]


def test_infer_guard_results_from_compact_requires_source_csv():
    compact = _compact_frame()

    assert infer_guard_results_from_compact(compact) == (Path("guard.csv"),)

    with pytest.raises(ValueError, match="source_csv"):
        infer_guard_results_from_compact(compact.drop(columns=["source_csv"]))
