from pathlib import Path

import pandas as pd

from autodrift.artifacts import read_json
from autodrift.old_key_neighborhood_gate import (
    CandidateThresholds,
    DiversityThresholds,
    OldKeyNeighborhoodThresholds,
    evaluate_candidate_metrics,
    run_old_key_neighborhood_gate,
    summarize_diagnostics,
    summarize_old_key_surface,
)


def _thresholds(*, compact_max_seed_block_dominance: float = 0.75) -> OldKeyNeighborhoodThresholds:
    diversity = DiversityThresholds(
        min_rows=4,
        min_seed_blocks=2,
        min_physical_pairs_or_keys=4,
        min_source_steps=2,
        min_target_buckets=2,
        max_seed_block_dominance=0.75,
        max_physical_pair_dominance=0.50,
    )
    compact = DiversityThresholds(
        min_rows=4,
        max_rows=6,
        min_seed_blocks=2,
        min_physical_pairs_or_keys=4,
        min_source_steps=2,
        min_target_buckets=2,
        max_seed_block_dominance=compact_max_seed_block_dominance,
        max_physical_pair_dominance=0.50,
    )
    return OldKeyNeighborhoodThresholds(
        broad=diversity,
        compact=compact,
        candidate=CandidateThresholds(
            max_selected_accepted_regressions=0,
            min_selected_gap_p10=-0.0005,
            min_selected_gap_min=-0.002,
            endpoint_repair_accepted_regressions=2,
            endpoint_repair_gap_p10=-0.001,
            endpoint_repair_gap_min=-0.01,
        ),
    )


def _mined_row(index: int, *, seed_block: str, selected_regression: bool = False) -> dict:
    return {
        "record_type": "m341_mined_case",
        "seed_block": seed_block,
        "source_csv": f"source_{seed_block}.csv",
        "case_id": f"{1000 + index}|perturbed|{20 + index}|{18 + index}|10.0|-1.0|0.{index}",
        "key": f"{1000 + index}|perturbed|{20 + index}|{18 + index}",
        "seed": 1000 + index,
        "source_condition": "perturbed",
        "source_step": 20 + (index % 2),
        "paired_step": 18 + index,
        "target_obstacle_distance": 9.5 + (index % 2),
        "relocated_obstacle_body_y": -1.2 + 0.2 * (index % 2),
        "relocated_obstacle_half_width": 0.7 + 0.1 * index,
        "selected_accepted_regression": selected_regression,
        "selected_gap_delta": -0.00001 * index,
        "endpoint_accepted_regression": index in {1, 2},
        "endpoint_gap_delta": -0.02 if index == 1 else -0.0005 * index,
        "old_key_9944": False,
    }


def _diagnostic_row() -> dict:
    row = _mined_row(44, seed_block="M133")
    row.update(
        {
            "record_type": "m133_diagnostic",
            "case_id": "9944|perturbed|28|28|11.000000|-1.000000|0.900000",
            "key": "9944|perturbed|28|28",
            "old_key_9944": True,
            "selected_accepted_regression": False,
            "endpoint_accepted_regression": False,
        }
    )
    return row


def _surface_frame(*, selected_regression: bool = False, dominant: bool = False) -> pd.DataFrame:
    rows = [
        _mined_row(0, seed_block="A"),
        _mined_row(1, seed_block="A", selected_regression=selected_regression),
        _mined_row(2, seed_block="A" if dominant else "B"),
        _mined_row(3, seed_block="B"),
    ]
    return pd.DataFrame(rows)


def test_summarize_old_key_surface_computes_diversity_and_candidate_metrics():
    thresholds = _thresholds().compact
    metrics = summarize_old_key_surface(_surface_frame(), thresholds=thresholds)
    metrics.update(evaluate_candidate_metrics(metrics, _thresholds().candidate))

    assert metrics["rows"] == 4
    assert metrics["seed_blocks"] == 2
    assert metrics["physical_pairs_or_keys"] == 4
    assert metrics["source_steps"] == 2
    assert metrics["target_buckets"] == 4
    assert metrics["passes_diversity_targets"]
    assert metrics["selected_alpha_passes"]
    assert metrics["endpoint_repair_needed"]
    assert "endpoint_accepted_regressions>=2" in metrics["endpoint_repair_reasons"]


def test_summarize_diagnostics_requires_old_key_9944_visibility():
    diagnostics = summarize_diagnostics(
        pd.DataFrame([*_surface_frame().to_dict("records"), _diagnostic_row()]),
        require_old_key_9944=True,
    )

    assert diagnostics["rows"] == 1
    assert diagnostics["old_key_9944_included"]
    assert diagnostics["visible"]


def test_run_old_key_neighborhood_gate_writes_pass_summary(tmp_path: Path):
    candidate_csv = tmp_path / "candidate.csv"
    compact_csv = tmp_path / "compact.csv"
    candidate = pd.DataFrame([*_surface_frame().to_dict("records"), _diagnostic_row()])
    compact = _surface_frame()
    candidate.to_csv(candidate_csv, index=False)
    compact.to_csv(compact_csv, index=False)

    result = run_old_key_neighborhood_gate(
        candidate_pool_csv=candidate_csv,
        compact_corpus_csv=compact_csv,
        run_dir=tmp_path / "gate",
        thresholds=_thresholds(),
    )

    assert result["overall_pass"]
    assert result["replacement_gate_ready"]
    summary = read_json(tmp_path / "gate" / "summary.json")
    assert summary["decision"] == "admit_m343_old_key_neighborhood_gate_probe"
    assert (tmp_path / "gate" / "broad_metrics.csv").exists()
    assert (tmp_path / "gate" / "compact_metrics.csv").exists()
    assert (tmp_path / "gate" / "diagnostic_summary.csv").exists()


def test_gate_fails_when_compact_source_dominance_is_too_high(tmp_path: Path):
    candidate_csv = tmp_path / "candidate.csv"
    compact_csv = tmp_path / "compact.csv"
    pd.DataFrame([*_surface_frame().to_dict("records"), _diagnostic_row()]).to_csv(candidate_csv, index=False)
    _surface_frame(dominant=True).to_csv(compact_csv, index=False)

    result = run_old_key_neighborhood_gate(
        candidate_pool_csv=candidate_csv,
        compact_corpus_csv=compact_csv,
        run_dir=tmp_path / "gate",
        thresholds=_thresholds(compact_max_seed_block_dominance=0.50),
    )

    assert not result["overall_pass"]
    assert "lineage_invalid" in result["failure_types"]
    assert "max_seed_block_dominance>0.5" in result["compact_corpus"]["diversity_failures"]


def test_gate_fails_when_selected_alpha_regresses(tmp_path: Path):
    candidate_csv = tmp_path / "candidate.csv"
    compact_csv = tmp_path / "compact.csv"
    candidate = pd.DataFrame([*_surface_frame(selected_regression=True).to_dict("records"), _diagnostic_row()])
    compact = _surface_frame(selected_regression=True)
    candidate.to_csv(candidate_csv, index=False)
    compact.to_csv(compact_csv, index=False)

    result = run_old_key_neighborhood_gate(
        candidate_pool_csv=candidate_csv,
        compact_corpus_csv=compact_csv,
        run_dir=tmp_path / "gate",
        thresholds=_thresholds(),
    )

    assert not result["overall_pass"]
    assert "protected_key_window_failure" in result["failure_types"]
    assert "selected_accepted_regressions>0" in result["compact_corpus"]["selected_alpha_failures"]
