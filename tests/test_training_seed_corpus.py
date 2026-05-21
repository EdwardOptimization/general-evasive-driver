import pandas as pd

from autodrift.training_seed_corpus import build_seed_sequence, summarize_sources, write_training_seed_corpus


def _corpus_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "seed": 11,
                "source": "m38",
                "candidate_policy": "a",
                "critical_reason": "near_boundary",
                "margin_critical_score": 3.0,
            },
            {
                "seed": 11,
                "source": "m38",
                "candidate_policy": "b",
                "critical_reason": "near_boundary",
                "margin_critical_score": 5.0,
            },
            {
                "seed": 12,
                "source": "fresh",
                "candidate_policy": "a",
                "critical_reason": "binary_outcome_changed",
                "margin_critical_score": 8.0,
            },
        ]
    )


def test_build_seed_sequence_deduplicates_and_sorts_by_score():
    sequence = build_seed_sequence(_corpus_frame())

    assert sequence["seed"].tolist() == [12, 11]
    assert int(sequence.loc[sequence["seed"] == 11, "row_count"].iloc[0]) == 2
    assert sequence.loc[sequence["seed"] == 11, "candidate_policies"].iloc[0] == "a;b"
    assert sequence.loc[sequence["seed"] == 11, "sources"].iloc[0] == "m38"


def test_summarize_sources_counts_unique_seed_mentions():
    sequence = build_seed_sequence(_corpus_frame())
    summary = summarize_sources(sequence)

    assert dict(zip(summary["source"], summary["seeds"], strict=True)) == {"fresh": 1, "m38": 1}


def test_write_training_seed_corpus_writes_outputs(tmp_path):
    corpus_csv = tmp_path / "corpus.csv"
    _corpus_frame().to_csv(corpus_csv, index=False)

    manifest = write_training_seed_corpus(tmp_path / "out", corpus_csv=corpus_csv)

    assert manifest["summary"]["input_rows"] == 3
    assert manifest["summary"]["unique_seeds"] == 2
    assert (tmp_path / "out" / "seed_sequence.csv").exists()
    assert (tmp_path / "out" / "source_summary.csv").exists()
