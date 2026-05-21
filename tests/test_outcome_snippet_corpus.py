import json

import numpy as np
import pandas as pd
import pytest

from autodrift.outcome_snippet_corpus import combine_outcome_snippet_runs


def _write_snippet_run(
    run_dir,
    *,
    observations,
    weights,
    only_accepted=True,
    seeds=None,
):
    run_dir.mkdir(parents=True)
    rows = len(observations)
    seeds = seeds or list(range(100, 100 + rows))
    np.savez_compressed(
        run_dir / "outcome_intervention_snippets.npz",
        observation=np.asarray(observations, dtype=np.float32),
        preferred_hidden=np.zeros((rows, 4), dtype=np.float32),
        rejected_hidden=np.ones((rows, 4), dtype=np.float32),
        preferred_action=np.zeros((rows, 3), dtype=np.float32),
        weight=np.asarray(weights, dtype=np.float32),
    )
    pd.DataFrame(
        [
            {
                "seed": int(seeds[index]),
                "source_condition": "perturbed",
                "source_step": 10 + index,
                "paired_step": 9 + index,
                "normal_margin": 0.10 + 0.01 * index,
                "wrong_history_margin": 0.05 + 0.01 * index,
                "margin_gap": 0.05,
                "weight": float(weights[index]),
            }
            for index in range(rows)
        ]
    ).to_csv(run_dir / "outcome_intervention_snippets.csv", index=False)
    (run_dir / "manifest.json").write_text(
        json.dumps({"outcome_export": {"only_accepted_outcomes": only_accepted}}),
        encoding="utf-8",
    )


def test_combine_outcome_snippet_runs_preserves_source_metadata_and_deduplicates(tmp_path):
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    _write_snippet_run(
        run_a,
        observations=[[1.0, 0.0], [2.0, 0.0]],
        weights=[0.1, 0.2],
        seeds=[11, 12],
    )
    _write_snippet_run(
        run_b,
        observations=[[2.0, 0.0], [3.0, 0.0]],
        weights=[0.2, 0.3],
        seeds=[12, 13],
    )

    manifest = combine_outcome_snippet_runs(
        [run_a, run_b],
        run_dir=tmp_path / "combined",
        deduplicate=True,
    )

    data = np.load(tmp_path / "combined" / "outcome_intervention_snippets.npz")
    metadata = pd.read_csv(tmp_path / "combined" / "outcome_intervention_snippets.csv")
    assert data["observation"].shape == (3, 2)
    assert len(metadata) == 3
    assert int(manifest["summary"]["input_rows"]) == 4
    assert int(manifest["summary"]["output_rows"]) == 3
    assert int(manifest["summary"]["duplicate_rows_removed"]) == 1
    duplicate_row = metadata.loc[metadata["seed"] == 12].iloc[0]
    assert "run_a" in duplicate_row["source_runs"]
    assert "run_b" in duplicate_row["source_runs"]
    assert int(duplicate_row["source_run_count"]) == 2


def test_combine_outcome_snippet_runs_rejects_csv_npz_count_mismatch(tmp_path):
    run_dir = tmp_path / "bad_run"
    _write_snippet_run(run_dir, observations=[[1.0], [2.0]], weights=[0.1, 0.2])
    pd.read_csv(run_dir / "outcome_intervention_snippets.csv").iloc[:1].to_csv(
        run_dir / "outcome_intervention_snippets.csv",
        index=False,
    )

    with pytest.raises(ValueError, match="metadata row count"):
        combine_outcome_snippet_runs([run_dir], run_dir=tmp_path / "combined")


def test_combine_outcome_snippet_runs_requires_accepted_only_manifest(tmp_path):
    run_dir = tmp_path / "raw_run"
    _write_snippet_run(run_dir, observations=[[1.0]], weights=[0.1], only_accepted=False)

    with pytest.raises(ValueError, match="only_accepted_outcomes"):
        combine_outcome_snippet_runs([run_dir], run_dir=tmp_path / "combined")
