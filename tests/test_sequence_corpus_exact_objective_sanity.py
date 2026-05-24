import numpy as np
import pandas as pd
import pytest

from autodrift.sequence_corpus_exact_objective_sanity import (
    REQUIRED_ARRAYS,
    compute_row_metrics,
    load_sequence_corpus_npz,
    run_sequence_corpus_exact_objective_sanity,
    source_weight_balance,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)


def _arrays() -> dict[str, np.ndarray]:
    observation = np.zeros((4, 72), dtype=np.float32)
    normal_hidden = np.zeros((4, 64), dtype=np.float32)
    variant_hidden = np.ones((4, 64), dtype=np.float32)
    base = np.zeros((4, 3, 3), dtype=np.float32)
    target = base.copy()
    target[0, :2, 0] = 0.10
    target[1, :3, 1] = -0.05
    target[2, :1, 2] = 0.20
    target[3, :2, :] = 0.03
    mask = np.array(
        [
            [1, 1, 0],
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 0],
        ],
        dtype=np.float32,
    )
    return {
        "observation": observation,
        "normal_hidden": normal_hidden,
        "variant_hidden": variant_hidden,
        "target_action_sequence": target,
        "normal_base_action_sequence": base,
        "sequence_mask": mask,
        "variant_base_action": np.zeros((4, 3), dtype=np.float32),
        "weight": np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float32),
        "row_id": np.arange(4, dtype=np.int64),
        "source_index": np.array([1, 1, 2, 2], dtype=np.int64),
        "sequence_length": np.array([2, 3, 1, 2], dtype=np.int64),
    }


def _metadata() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_index": [1, 1, 2, 2],
            "split": ["train", "train", "source_holdout_validation", "source_holdout_validation"],
            "surface": ["fresh", "fresh", "ood", "ood"],
            "target": ["yaw", "yaw", "braking", "braking"],
            "variant": ["delayed", "delayed", "wrong", "wrong"],
            "grid_name": ["g0", "g1", "g0", "g1"],
            "sequence_length": [2, 3, 1, 2],
            "corpus_weight": [0.25, 0.25, 0.25, 0.25],
        }
    )


def test_validate_sequence_corpus_contract_accepts_expected_arrays():
    contract = validate_sequence_corpus_contract(_arrays())

    assert contract.rows == 4
    assert contract.observation_dim == 72
    assert contract.hidden_dim == 64
    assert contract.max_sequence_length == 3
    assert contract.source_count == 2


def test_validate_sequence_corpus_contract_rejects_missing_and_bad_mask():
    arrays = _arrays()
    arrays.pop("weight")

    with pytest.raises(ValueError, match="missing arrays"):
        validate_sequence_corpus_contract(arrays)

    arrays = _arrays()
    arrays["sequence_mask"][0] = np.array([1.0, 0.0, 1.0], dtype=np.float32)
    with pytest.raises(ValueError, match="prefix mask"):
        validate_sequence_corpus_contract(arrays)


def test_load_sequence_corpus_npz_validates_required_arrays(tmp_path):
    path = tmp_path / "corpus.npz"
    np.savez_compressed(path, **_arrays())

    loaded = load_sequence_corpus_npz(path)

    assert set(REQUIRED_ARRAYS).issubset(loaded)


def test_validate_metadata_alignment_rejects_source_or_weight_mismatch():
    arrays = _arrays()
    metadata = _metadata()
    validate_metadata_alignment(arrays, metadata)

    bad_source = metadata.copy()
    bad_source.loc[0, "source_index"] = 99
    with pytest.raises(ValueError, match="source_index"):
        validate_metadata_alignment(arrays, bad_source)

    bad_weight = metadata.copy()
    bad_weight.loc[0, "corpus_weight"] = 0.5
    with pytest.raises(ValueError, match="corpus_weight"):
        validate_metadata_alignment(arrays, bad_weight)


def test_compute_row_metrics_and_source_balance_are_finite():
    rows = compute_row_metrics(_arrays(), _metadata())
    balance = source_weight_balance(rows)

    assert rows["sequence_mean_step_l2"].min() > 0.0
    assert rows["weighted_sequence_mse"].sum() > 0.0
    assert balance["source_weight_balanced"] is True
    assert balance["max_abs_source_weight_error"] == pytest.approx(0.0)


def test_run_sequence_corpus_exact_objective_sanity_writes_artifacts(tmp_path):
    corpus = tmp_path / "corpus.npz"
    metadata = tmp_path / "metadata.csv"
    run_dir = tmp_path / "run"
    np.savez_compressed(corpus, **_arrays())
    _metadata().to_csv(metadata, index=False)

    summary = run_sequence_corpus_exact_objective_sanity(
        corpus_npz=corpus,
        metadata_csv=metadata,
        run_dir=run_dir,
    )

    assert summary["rows"] == 4
    assert summary["all_rows_have_nonzero_target_delta"] is True
    assert summary["source_weight_balance"]["source_weight_balanced"] is True
    assert summary["training_started"] is False
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "row_objective_metrics.csv").exists()
    assert (run_dir / "source_objective_summary.csv").exists()
    assert (run_dir / "split_objective_summary.csv").exists()
    assert (run_dir / "target_objective_summary.csv").exists()
