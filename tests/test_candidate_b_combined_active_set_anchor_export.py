import numpy as np
import pytest

from autodrift.candidate_b_combined_active_set_anchor_export import (
    build_combined_anchor_arrays,
    export_combined_active_set_anchors,
    normalize_family_weights,
    save_anchor_npz,
)


def _anchor(rows: int, *, source_index: np.ndarray, weight: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "observation": np.zeros((rows, 72), dtype=np.float32),
        "hidden": np.zeros((rows, 128), dtype=np.float32),
        "reference_action": np.zeros((rows, 3), dtype=np.float32),
        "source_index": np.asarray(source_index, dtype=np.int64),
        "step_index": np.arange(rows, dtype=np.int64),
        "weight": np.asarray(weight, dtype=np.float32),
    }


def test_normalize_family_weights_preserves_relative_weights() -> None:
    weights = normalize_family_weights(np.asarray([2.0, 6.0], dtype=np.float32), family_total=4.0)

    np.testing.assert_allclose(weights, np.asarray([1.0, 3.0], dtype=np.float32))
    assert float(weights.sum()) == pytest.approx(4.0)

    with pytest.raises(ValueError):
        normalize_family_weights(np.asarray([0.0, 0.0], dtype=np.float32), family_total=1.0)


def test_build_combined_anchor_arrays_namespaces_and_normalizes() -> None:
    m267 = _anchor(2, source_index=np.asarray([0, 1]), weight=np.asarray([2.0, 6.0]))
    m183 = _anchor(2, source_index=np.asarray([0, 0]), weight=np.asarray([1.0, 3.0]))

    combined = build_combined_anchor_arrays(
        m267_rejected=m267,
        m183_row16_normal=m183,
        m183_source_offset=100,
        m267_family_total=1.0,
        m183_family_total=4.0,
    )

    assert combined["observation"].shape == (4, 72)
    assert combined["hidden"].shape == (4, 128)
    assert combined["reference_action"].shape == (4, 3)
    assert combined["source_index"].tolist() == [0, 1, 100, 100]
    assert combined["family_id"].tolist() == [0, 0, 1, 1]
    assert float(combined["weight"][:2].sum()) == pytest.approx(1.0)
    assert float(combined["weight"][2:].sum()) == pytest.approx(4.0)

    with pytest.raises(ValueError):
        build_combined_anchor_arrays(
            m267_rejected=m267,
            m183_row16_normal=m183,
            m183_source_offset=0,
            m267_family_total=1.0,
            m183_family_total=4.0,
        )


def test_export_combined_active_set_anchors_writes_variants(tmp_path) -> None:
    m267_path = tmp_path / "m267.npz"
    m183_path = tmp_path / "m183.npz"
    save_anchor_npz(m267_path, _anchor(2, source_index=np.asarray([0, 1]), weight=np.asarray([2.0, 6.0])))
    save_anchor_npz(m183_path, _anchor(3, source_index=np.asarray([0, 0, 0]), weight=np.asarray([1.0, 1.0, 2.0])))

    summary = export_combined_active_set_anchors(
        m267_rejected_anchor_npz=m267_path,
        m183_row16_normal_anchor_npz=m183_path,
        m183_source_offset=1000,
        run_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "candidate_b_combined_active_set_anchor_export_pass"
    assert summary["combined_rows_expected"] == 5
    assert summary["variant_count"] == 3
    assert summary["all_variants_loadable"] is True
    assert summary["all_source_namespaced"] is True
    assert summary["all_family_weights_match"] is True
    assert summary["all_row_counts_match"] is True
    assert (tmp_path / "run" / "combined_active_set_anchor_balanced.npz").exists()
    assert (tmp_path / "run" / "combined_active_set_anchor_row16x4.npz").exists()
    assert (tmp_path / "run" / "combined_active_set_anchor_row16x8.npz").exists()
    assert (tmp_path / "run" / "combined_active_set_anchor_summary.csv").exists()
    assert (tmp_path / "run" / "summary.json").exists()
