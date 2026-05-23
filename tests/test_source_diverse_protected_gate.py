from pathlib import Path

import pandas as pd
import pytest

from autodrift.source_diverse_protected_gate import (
    aggregate_results,
    ingest_diagnostic_csv,
    parse_diagnostic_csv_spec,
    parse_replay_gate_spec,
)


def test_parse_replay_gate_spec_requires_name_corpus_and_policies():
    spec = parse_replay_gate_spec("current=corpus.csv,base,candidate")

    assert spec.label == "current"
    assert spec.corpus_csv == Path("corpus.csv")
    assert spec.baseline_policy == "base"
    assert spec.candidate_policy == "candidate"

    with pytest.raises(ValueError, match="NAME=CORPUS"):
        parse_replay_gate_spec("bad")

    with pytest.raises(ValueError, match="NAME=CORPUS"):
        parse_replay_gate_spec("bad=only,two")


def test_parse_diagnostic_csv_spec_requires_name_and_path():
    spec = parse_diagnostic_csv_spec("key=guard_results.csv")

    assert spec.label == "key"
    assert spec.csv_path == Path("guard_results.csv")

    with pytest.raises(ValueError, match="NAME=PATH"):
        parse_diagnostic_csv_spec("missing_path=")


def test_ingest_diagnostic_csv_summarizes_optional_columns(tmp_path: Path):
    csv_path = tmp_path / "guard.csv"
    pd.DataFrame(
        [
            {"policy": "base", "accepted": True, "normal_margin": 0.1, "margin_gap": 0.05},
            {"policy": "candidate", "accepted": False, "normal_margin": 0.2, "margin_gap": 0.01},
        ]
    ).to_csv(csv_path, index=False)

    summary = ingest_diagnostic_csv(parse_diagnostic_csv_spec(f"key={csv_path}"))

    assert summary["label"] == "key"
    assert summary["rows"] == 2
    assert summary["accepted_rows"] == 1
    assert summary["accepted_fraction"] == pytest.approx(0.5)
    assert summary["normal_margin_max"] == pytest.approx(0.2)
    assert summary["margin_gap_min"] == pytest.approx(0.01)
    assert summary["policies"] == ["base", "candidate"]


def test_aggregate_results_reports_proof_washout_on_replay_failure():
    aggregate = aggregate_results(
        [
            {"label": "current", "gate_pass": True},
            {"label": "previous", "gate_pass": False},
        ],
        [{"label": "key"}],
    )

    assert not aggregate["overall_pass"]
    assert aggregate["failed_replay_gates"] == ["previous"]
    assert aggregate["failure_types"] == ["proof_washout"]


def test_aggregate_results_passes_when_all_replay_gates_pass():
    aggregate = aggregate_results(
        [
            {"label": "current", "gate_pass": True},
            {"label": "previous", "gate_pass": True},
        ],
        [],
    )

    assert aggregate["overall_pass"]
    assert aggregate["failure_types"] == ["none"]
