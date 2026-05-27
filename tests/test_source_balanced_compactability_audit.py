import json

import pandas as pd

from autodrift.source_balanced_compactability_audit import (
    choose_recommended_conversion_mode,
    compactability_metrics,
    run_compactability_audit,
    select_compactability_rows,
)


def _row(
    *,
    checkpoint_label: str,
    pair_index: int,
    target: str = "future_yaw_response",
    duplicate_geometry_index: int | None = None,
    margin_gap: float = 0.03,
    accepted: bool = True,
) -> dict[str, object]:
    geometry_index = pair_index if duplicate_geometry_index is None else duplicate_geometry_index
    return {
        "variant": "wrong_matched_history",
        "accepted": accepted,
        "checkpoint_label": checkpoint_label,
        "target": target,
        "left_seed": 1000 + pair_index,
        "right_seed": 2000 + pair_index,
        "left_step": 10 + pair_index,
        "right_step": 20 + pair_index,
        "relocated_obstacle_body_x": 25.0 + geometry_index,
        "relocated_obstacle_body_y": -1.0 + 0.1 * geometry_index,
        "relocated_obstacle_half_width": 1.5,
        "normal_margin": 0.002 + 0.001 * (pair_index % 3),
        "variant_margin": 0.002 + 0.001 * (pair_index % 3) - margin_gap,
        "normal_success": True,
        "variant_success": False,
        "success_drop": True,
        "margin_gap": margin_gap,
        "normal_first_steer": 0.1,
        "normal_first_throttle": 0.0,
        "normal_first_brake": 0.2,
    }


def test_select_compactability_rows_filters_deduplicates_and_caps():
    rows = [
        _row(checkpoint_label="a", pair_index=1, margin_gap=0.05),
        _row(checkpoint_label="a", pair_index=1, margin_gap=0.04),
        _row(checkpoint_label="a", pair_index=2, margin_gap=0.01),
        _row(checkpoint_label="a", pair_index=3, margin_gap=0.001),
        _row(checkpoint_label="b", pair_index=4, margin_gap=0.05),
    ]

    selected = select_compactability_rows(
        pd.DataFrame(rows),
        checkpoint_label="a",
        min_margin_gap=0.005,
        max_rows_per_physical_pair=1,
        deduplicate_geometry=True,
    )

    assert len(selected) == 2
    assert set(selected["left_seed"]) == {1001, 1002}
    assert selected["margin_gap"].tolist() == [0.05, 0.01]


def test_compactability_metrics_reports_threshold_pass():
    rows = pd.DataFrame(
        [
            _row(checkpoint_label="a", pair_index=1, target="future_yaw_response"),
            _row(checkpoint_label="a", pair_index=2, target="future_braking_deceleration"),
        ]
    )
    selected = select_compactability_rows(
        rows,
        checkpoint_label="a",
        min_margin_gap=0.0,
        max_rows_per_physical_pair=0,
        deduplicate_geometry=True,
    )

    metrics = compactability_metrics(
        selected,
        mode="per_checkpoint",
        selection_kind="compact_dedup",
        checkpoint_label="a",
        min_margin_gap=0.0,
        max_rows_per_physical_pair=0,
        margin_bucket_width=0.001,
        min_rows=2,
        min_physical_pairs=2,
        min_left_steps=1,
        min_checkpoints=1,
        min_targets=2,
        min_margin_buckets=1,
        min_success_drop_fraction=1.0,
        max_rows_per_physical_pair_fraction=0.60,
    )

    assert metrics["threshold_pass"]
    assert metrics["conversion_ready"]
    assert metrics["rows"] == 2
    assert metrics["physical_pairs"] == 2
    assert metrics["targets"] == 2


def test_recommendation_prefers_raw_aggregate_when_per_checkpoint_and_compact_are_sparse(tmp_path):
    rows = []
    for pair_index in range(3):
        rows.append(_row(checkpoint_label="a", pair_index=pair_index, duplicate_geometry_index=pair_index))
        rows.append(_row(checkpoint_label="b", pair_index=pair_index, duplicate_geometry_index=pair_index))
    source_csv = tmp_path / "accepted.csv"
    pd.DataFrame(rows).to_csv(source_csv, index=False)

    summary = run_compactability_audit(
        accepted_rows_csv=source_csv,
        run_dir=tmp_path / "audit",
        max_rows_per_physical_pair_candidates=(0,),
        min_margin_gap_candidates=(0.0,),
        margin_bucket_width=0.001,
        min_per_checkpoint_rows=4,
        min_per_checkpoint_physical_pairs=3,
        min_per_checkpoint_targets=1,
        min_aggregate_rows=5,
        min_aggregate_physical_pairs=3,
        min_aggregate_left_steps=3,
        min_aggregate_checkpoints=2,
        min_aggregate_targets=1,
        min_aggregate_margin_buckets=1,
        max_rows_per_physical_pair_fraction=0.50,
    )

    recommendation = summary["recommendation"]
    assert recommendation["recommended_mode"] == "family_aggregate"
    assert recommendation["recommended_selection_kind"] == "raw_retained"
    assert recommendation["requires_new_conversion_path"]
    assert recommendation["requires_replay_before_objective_conversion"]

    aggregate = pd.read_csv(tmp_path / "audit" / "aggregate_compactability.csv")
    compact = aggregate[aggregate["selection_kind"] == "compact_dedup"].iloc[0]
    raw = aggregate[aggregate["selection_kind"] == "raw_retained"].iloc[0]
    assert int(compact["rows"]) == 3
    assert int(raw["rows"]) == 6


def test_run_compactability_audit_writes_required_artifacts_and_safety_flags(tmp_path):
    rows = []
    for pair_index in range(4):
        rows.append(_row(checkpoint_label="a", pair_index=pair_index))
        rows.append(_row(checkpoint_label="b", pair_index=10 + pair_index))
    source_csv = tmp_path / "accepted.csv"
    pd.DataFrame(rows).to_csv(source_csv, index=False)
    run_dir = tmp_path / "audit"

    summary = run_compactability_audit(
        accepted_rows_csv=source_csv,
        run_dir=run_dir,
        max_rows_per_physical_pair_candidates=(0, 2),
        min_margin_gap_candidates=(0.0,),
        min_per_checkpoint_rows=2,
        min_per_checkpoint_physical_pairs=2,
        min_per_checkpoint_targets=1,
        min_aggregate_rows=4,
        min_aggregate_physical_pairs=4,
        min_aggregate_left_steps=4,
        min_aggregate_checkpoints=2,
        min_aggregate_targets=1,
        min_aggregate_margin_buckets=1,
    )

    assert (run_dir / "per_checkpoint_compactability.csv").exists()
    assert (run_dir / "aggregate_compactability.csv").exists()
    assert (run_dir / "recommended_conversion_mode.json").exists()
    assert (run_dir / "summary.json").exists()
    loaded = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert loaded["training_started"] is False
    assert loaded["ppo_used"] is False
    assert loaded["promoted"] is False
    assert loaded["private_holdout_used"] is False
    assert summary["audit_completed"]


def test_choose_recommended_conversion_mode_returns_no_ready_when_all_sparse():
    per_rows = [
        {
            "mode": "per_checkpoint",
            "selection_kind": "compact_dedup",
            "checkpoint_label": "a",
            "conversion_ready": False,
            "min_margin_gap": 0.0,
            "max_rows_per_physical_pair": 2,
            "rows": 1,
            "physical_pairs": 1,
        }
    ]
    aggregate_rows = [
        {
            "mode": "family_aggregate",
            "selection_kind": "compact_dedup",
            "checkpoint_label": "all",
            "conversion_ready": False,
            "min_margin_gap": 0.0,
            "max_rows_per_physical_pair": 2,
            "rows": 1,
            "physical_pairs": 1,
        }
    ]

    recommendation = choose_recommended_conversion_mode(
        per_checkpoint_rows=per_rows,
        aggregate_rows=aggregate_rows,
        checkpoint_labels=("a",),
    )

    assert recommendation["recommended_mode"] == "no_conversion_ready"
