import numpy as np
import pandas as pd

from autodrift.branch_split_old_key_guard import (
    branch_for_failed_guard_row,
    build_branch_split_failed_rows,
    combine_base_and_branch_anchors,
)


def test_branch_for_failed_guard_row_splits_normal_and_wrong_history():
    normal = {
        "candidate_normal_success_regression": True,
        "candidate_normal_success": False,
        "candidate_wrong_history_margin": -0.1,
    }
    wrong = {
        "candidate_normal_success_regression": False,
        "candidate_normal_success": True,
        "candidate_wrong_history_margin": 0.1,
    }

    assert branch_for_failed_guard_row(normal) == "normal"
    assert branch_for_failed_guard_row(wrong) == "wrong_history"


def test_build_branch_split_failed_rows_classifies_candidate_failures(tmp_path):
    rows = [
        {
            "policy": "base",
            "key": "10004|perturbed|31|31",
            "accepted": True,
            "normal_success": True,
            "normal_margin": 0.1,
            "wrong_history_margin": -0.1,
            "source_condition": "perturbed",
            "source_step": 31,
            "paired_step": 31,
            "target_obstacle_distance": 9.5,
            "relocated_obstacle_body_y": -1.0,
            "relocated_obstacle_half_width": 0.8,
        },
        {
            "policy": "candidate",
            "key": "10004|perturbed|31|31",
            "accepted": False,
            "normal_success": True,
            "normal_margin": 0.2,
            "wrong_history_margin": 0.01,
            "source_condition": "perturbed",
            "source_step": 31,
            "paired_step": 31,
            "target_obstacle_distance": 9.5,
            "relocated_obstacle_body_y": -1.0,
            "relocated_obstacle_half_width": 0.8,
        },
        {
            "policy": "base",
            "key": "9872|perturbed|21|18",
            "accepted": True,
            "normal_success": True,
            "normal_margin": 0.1,
            "wrong_history_margin": -0.1,
            "source_condition": "perturbed",
            "source_step": 21,
            "paired_step": 18,
            "target_obstacle_distance": 12.0,
            "relocated_obstacle_body_y": -1.2,
            "relocated_obstacle_half_width": 1.2,
        },
        {
            "policy": "candidate",
            "key": "9872|perturbed|21|18",
            "accepted": False,
            "normal_success": False,
            "normal_margin": -0.01,
            "wrong_history_margin": -0.2,
            "source_condition": "perturbed",
            "source_step": 21,
            "paired_step": 18,
            "target_obstacle_distance": 12.0,
            "relocated_obstacle_body_y": -1.2,
            "relocated_obstacle_half_width": 1.2,
        },
    ]
    path = tmp_path / "guard_results.csv"
    pd.DataFrame(rows).to_csv(path, index=False)

    failed = build_branch_split_failed_rows(
        guard_results_csv=path,
        baseline_policy="base",
        candidate_policy="candidate",
    )

    assert failed["branch"].tolist() == ["wrong_history", "normal"]
    assert failed["candidate_normal_success_regression"].tolist() == [False, True]
    assert failed["case_id"].tolist() == [
        "10004|perturbed|31|31|9.500000|-1.000000|0.800000",
        "9872|perturbed|21|18|12.000000|-1.200000|1.200000",
    ]


def test_combine_base_and_branch_anchors_offsets_sources(tmp_path):
    base_npz = tmp_path / "base.npz"
    branch_npz = tmp_path / "branch.npz"
    branch_csv = tmp_path / "branch.csv"
    output_npz = tmp_path / "combined.npz"
    output_sources = tmp_path / "sources.csv"
    np.savez(
        base_npz,
        observation=np.zeros((2, 72), dtype=np.float32),
        hidden=np.zeros((2, 4), dtype=np.float32),
        reference_action=np.zeros((2, 3), dtype=np.float32),
        source_index=np.asarray([0, 4], dtype=np.int64),
        step_index=np.asarray([0, 0], dtype=np.int64),
        weight=np.asarray([75.0, 75.0], dtype=np.float32),
        radius=np.asarray([0.0003, 0.0002], dtype=np.float32),
    )
    np.savez(
        branch_npz,
        observation=np.ones((3, 72), dtype=np.float32),
        hidden=np.ones((3, 4), dtype=np.float32),
        reference_action=np.ones((3, 3), dtype=np.float32) * 0.5,
        source_index=np.asarray([0, 0, 1], dtype=np.int64),
        step_index=np.asarray([0, 1, 0], dtype=np.int64),
        weight=np.asarray([75.0, 75.0, 100.0], dtype=np.float32),
    )
    pd.DataFrame(
        [
            {"source_index": 0, "case_id": "10004", "branch": "wrong_history", "weight": 75.0},
            {"source_index": 0, "case_id": "10004", "branch": "wrong_history", "weight": 75.0},
            {"source_index": 1, "case_id": "9872", "branch": "normal", "weight": 100.0},
        ]
    ).to_csv(branch_csv, index=False)

    summary = combine_base_and_branch_anchors(
        base_anchor_npz=base_npz,
        branch_anchor_npz=branch_npz,
        branch_anchor_csv=branch_csv,
        output_npz=output_npz,
        output_sources_csv=output_sources,
        branch_radius=0.0002,
    )

    combined = np.load(output_npz)
    sources = pd.read_csv(output_sources)
    assert summary["rows"] == 5
    assert combined["source_index"].tolist() == [0, 4, 5, 5, 6]
    assert np.allclose(combined["radius"], [0.0003, 0.0002, 0.0002, 0.0002, 0.0002])
    assert set(sources["branch"].dropna().astype(str)) == {"wrong_history", "normal"}
