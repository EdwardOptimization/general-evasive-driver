from __future__ import annotations

import json

import pandas as pd

from autodrift.action_divergent_candidate_export import (
    action_divergent_candidate_pool,
    export_action_divergent_candidates,
    select_score_balanced_candidates,
)
from autodrift.source_balanced_boundary_relocation_surface import SourceBalanceQuotas


def _row(
    *,
    pair: int,
    checkpoint: str = "ckpt",
    target: str = "future_yaw_response",
    variant: str = "wrong_matched_history",
    margin_gap: float = 0.003,
    first_action: float = 0.16,
    trajectory: float = 0.02,
) -> dict[str, object]:
    return {
        "variant": variant,
        "checkpoint_label": checkpoint,
        "target": target,
        "left_seed": 100 + pair,
        "left_step": pair,
        "right_seed": 200 + pair,
        "right_step": pair + 1,
        "target_z_delta": 2.0,
        "visible_distance": 0.2,
        "margin_gap": margin_gap,
        "first_action_distance": first_action,
        "action_trajectory_distance_mean": trajectory,
    }


def test_action_divergent_candidate_pool_filters_and_scores() -> None:
    frame = pd.DataFrame(
        [
            _row(pair=1, margin_gap=0.003, first_action=0.16, trajectory=0.01),
            _row(pair=2, margin_gap=0.003, first_action=0.01, trajectory=0.07),
            _row(pair=3, margin_gap=0.001, first_action=0.50, trajectory=0.50),
            _row(pair=4, variant="reset_hidden", margin_gap=1.0, first_action=1.0, trajectory=1.0),
        ]
    )

    pool = action_divergent_candidate_pool(frame)

    assert len(pool) == 2
    assert set(pool["physical_pair_key"]) == {"101:1:201:2", "102:2:202:3"}
    assert "action_divergent_score" in pool.columns
    assert pool["action_divergent_score"].notna().all()


def test_select_score_balanced_candidates_round_robins_by_pair() -> None:
    frame = pd.DataFrame(
        [
            _row(pair=1, checkpoint="a", margin_gap=0.010, first_action=0.20),
            _row(pair=1, checkpoint="b", margin_gap=0.009, first_action=0.19),
            _row(pair=2, checkpoint="a", margin_gap=0.008, first_action=0.18),
            _row(pair=3, checkpoint="a", margin_gap=0.007, first_action=0.17),
        ]
    )
    pool = action_divergent_candidate_pool(frame)

    selected, rejected, summary = select_score_balanced_candidates(
        pool,
        quotas=SourceBalanceQuotas(
            max_candidates=3,
            max_candidates_per_physical_pair=1,
            target_min_physical_pairs=3,
            target_min_left_steps=3,
            target_min_targets=1,
            max_rows_per_pair_fraction=0.5,
        ),
    )

    assert len(selected) == 3
    assert selected["physical_pair_key"].nunique() == 3
    assert len(rejected) == 1
    assert summary["decision"] == "action_divergent_candidates_ready"
    assert summary["passed"] is True


def test_export_action_divergent_candidates_writes_artifacts(tmp_path) -> None:
    rows = []
    for pair in range(1, 5):
        rows.append(_row(pair=pair, checkpoint="a", target="future_yaw_response"))
        rows.append(_row(pair=pair, checkpoint="b", target="future_lateral_accel_response", trajectory=0.07))
    rows.append(_row(pair=99, variant="normal", margin_gap=1.0, first_action=1.0, trajectory=1.0))
    outcome_csv = tmp_path / "outcomes.csv"
    pd.DataFrame(rows).to_csv(outcome_csv, index=False)

    summary = export_action_divergent_candidates(
        outcome_csv=outcome_csv,
        run_dir=tmp_path / "run",
        quotas=SourceBalanceQuotas(
            max_candidates=6,
            max_candidates_per_physical_pair=2,
            target_min_physical_pairs=3,
            target_min_left_steps=3,
            target_min_targets=2,
            max_rows_per_pair_fraction=0.5,
        ),
    )

    summary_path = tmp_path / "run" / "summary.json"
    exported_csv = tmp_path / "run" / "candidate_outcomes.csv"
    assert summary_path.exists()
    assert exported_csv.exists()
    persisted = json.loads(summary_path.read_text())
    assert persisted["selection"]["selected_rows"] == 6
    assert persisted["selection"]["selected_physical_pairs"] >= 3
    assert persisted["selection"]["passed"] is True
    exported = pd.read_csv(exported_csv)
    assert len(exported) == summary["selection"]["selected_rows"]
    assert set(exported["variant"]) == {"wrong_matched_history"}
    assert "action_divergent_score" in exported.columns
