from __future__ import annotations

import json

import pandas as pd

from autodrift.terminal_boundary_candidate_export import (
    build_terminal_boundary_candidate_pool,
    export_terminal_boundary_candidates,
    physical_pair_key,
    source_obstacle_bucket,
    summarize_source_diversity,
)


def _row(
    *,
    index: int,
    variant: str = "wrong_matched_history",
    normal_success: bool = True,
    normal_margin: float = 0.25,
    first_action: float = 0.01,
    wrong_sequence: float = 0.02,
    preferred_rejected: float = 0.03,
    target: str = "avoidable",
) -> dict[str, object]:
    return {
        "source_index": index,
        "physical_pair_key": f"legacy:{100 + index}:{200 + index}",
        "grid_name": "action_critical_wrong_history",
        "surface": "l3_current",
        "target": target,
        "variant": variant,
        "split": "unassigned",
        "preferred_sequence_source": "normal_policy_base",
        "left_seed": 100 + index,
        "right_seed": 200 + index,
        "left_step": index,
        "right_step": index + 1,
        "sequence_length": 5,
        "left_obstacle_label": target,
        "right_obstacle_label": target,
        "left_obstacle_distance": 10.0 + index,
        "right_obstacle_distance": 12.0 + index,
        "left_obstacle_x_m": 10.0 + index,
        "right_obstacle_x_m": 12.0 + index,
        "left_obstacle_y_m": -1.0 + 0.1 * index,
        "right_obstacle_y_m": -0.5 + 0.1 * index,
        "context_distance": 0.01,
        "response_distance": 0.02,
        "obstacle_x_abs_delta": 2.0,
        "obstacle_y_abs_delta": 0.5,
        "step_abs_delta": 1,
        "hidden_distance": 0.1,
        "normal_success": normal_success,
        "wrong_success": True,
        "success_drop": False,
        "normal_collision": False,
        "wrong_collision": False,
        "normal_terminal_reason": "continuation_limit",
        "wrong_terminal_reason": "continuation_limit",
        "normal_margin": normal_margin,
        "wrong_margin": normal_margin - 0.001,
        "preferred_margin": normal_margin,
        "rejected_margin": normal_margin - 0.001,
        "normal_risk_score": -normal_margin,
        "wrong_risk_score": -(normal_margin - 0.001),
        "preferred_risk_score": -normal_margin,
        "rejected_risk_score": -(normal_margin - 0.001),
        "margin_gap": 0.001,
        "risk_gap": 0.001,
        "wrong_first_action_l2": first_action,
        "wrong_action_sequence_mean_l2": wrong_sequence,
        "wrong_action_sequence_max_l2": wrong_sequence,
        "preferred_vs_rejected_action_mean_l2": preferred_rejected,
        "preferred_vs_rejected_action_max_l2": preferred_rejected,
        "accepted": False,
        "rejection_reason": "no_success_drop_or_margin_gap",
    }


def test_build_terminal_boundary_candidate_pool_maps_m1222_fields() -> None:
    frame = pd.DataFrame(
        [
            _row(index=1),
            _row(index=2, variant="reset_hidden"),
            _row(index=3, first_action=0.0001),
            _row(index=4, normal_success=False),
        ]
    )

    selected, rejected = build_terminal_boundary_candidate_pool(frame, checkpoint_label="l3_s111602")

    assert len(selected) == 1
    row = selected.iloc[0]
    assert row["checkpoint_label"] == "l3_s111602"
    assert row["variant"] == "wrong_matched_history"
    assert bool(row["variant_success"]) is True
    assert abs(float(row["variant_margin"]) - 0.249) < 1e-12
    assert row["first_action_distance"] == 0.01
    assert row["action_trajectory_distance_mean"] == 0.03
    assert row["source_obstacle_body_x"] == 11.0
    assert row["source_obstacle_lateral_offset"] == -0.9
    assert row["physical_pair_key"] == "101:1:201:2"
    assert row["source_obstacle_bucket"] == "x=10.000-15.000|y=-1.000-0.000"
    assert row["_candidate_export_index"] == 0
    assert len(rejected) == 3
    assert "first_action_l2_below_threshold" in set(";".join(rejected["export_rejection_reason"]).split(";"))


def test_source_diversity_summary_enforces_registered_gates() -> None:
    selected = pd.DataFrame(
        [
            {
                "physical_pair_key": f"{index}:1:{index + 100}:2",
                "left_seed": index,
                "right_seed": index + 100,
                "left_step": index % 4,
                "target": "a" if index % 2 else "b",
                "source_obstacle_bucket": f"x={index}:y=0",
            }
            for index in range(8)
        ]
    )

    summary = summarize_source_diversity(
        selected,
        min_selected_rows=8,
        min_physical_pairs=8,
        min_left_seeds=8,
        min_right_seeds=8,
        min_left_steps=4,
        min_targets=2,
        min_source_obstacle_buckets=4,
        max_rows_per_physical_pair_fraction=0.20,
        max_left_seed_share=0.20,
        max_target_share=0.60,
    )

    assert summary["passed"] is True
    assert summary["selected_rows"] == 8
    assert summary["selected_physical_pairs"] == 8
    assert summary["decision"] == "terminal_boundary_candidates_source_diverse"


def test_export_terminal_boundary_candidates_writes_artifacts(tmp_path) -> None:
    source_indices = [1, 2, 6, 7, 11, 12, 16, 17]
    rows = [_row(index=index, target="a" if offset % 2 else "b") for offset, index in enumerate(source_indices)]
    rows.append(_row(index=99, first_action=0.0001))
    candidate_scores = tmp_path / "candidate_scores.csv"
    pd.DataFrame(rows).to_csv(candidate_scores, index=False)

    summary = export_terminal_boundary_candidates(
        candidate_scores=candidate_scores,
        checkpoint_label="l3_s111602",
        run_dir=tmp_path / "run",
        min_selected_rows=8,
        min_physical_pairs=8,
        min_left_seeds=8,
        min_right_seeds=8,
        min_left_steps=4,
        min_targets=2,
        min_source_obstacle_buckets=4,
        max_rows_per_physical_pair_fraction=0.20,
        max_left_seed_share=0.20,
        max_target_share=0.60,
    )

    summary_path = tmp_path / "run" / "summary.json"
    outcomes_csv = tmp_path / "run" / "candidate_outcomes.csv"
    pool_csv = tmp_path / "run" / "candidate_pool.csv"
    rejected_csv = tmp_path / "run" / "rejected_candidates.csv"
    assert summary_path.exists()
    assert outcomes_csv.exists()
    assert pool_csv.exists()
    assert rejected_csv.exists()
    persisted = json.loads(summary_path.read_text())
    assert persisted["selection_passed"] is True
    assert persisted["source_diversity"]["selected_rows"] == 8
    assert persisted["relocation_replay_started"] is False
    assert persisted["training_started"] is False
    exported = pd.read_csv(outcomes_csv)
    assert len(exported) == summary["source_diversity"]["selected_rows"]
    assert set(exported["checkpoint_label"]) == {"l3_s111602"}
    assert set(exported["variant"]) == {"wrong_matched_history"}
    assert "physical_pair_key" in exported.columns
    assert len(pd.read_csv(rejected_csv)) == 1


def test_export_helpers_match_relocation_key_format() -> None:
    row = {
        "left_seed": 10,
        "left_step": 20,
        "right_seed": 30,
        "right_step": 40,
        "source_obstacle_body_x": 24.9,
        "source_obstacle_body_y": -0.1,
    }

    assert physical_pair_key(row) == "10:20:30:40"
    assert source_obstacle_bucket(row, distance_bucket_width=5.0, lateral_bucket_width=1.0) == (
        "x=20.000-25.000|y=-1.000-0.000"
    )
