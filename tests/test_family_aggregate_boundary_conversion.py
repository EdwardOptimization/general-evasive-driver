import json

import pandas as pd
import pytest

from autodrift.family_aggregate_boundary_conversion import (
    add_family_metadata,
    load_source_policy_map,
    run_family_aggregate_conversion,
    select_raw_retained_rows,
)


def _row(
    *,
    checkpoint_label: str,
    pair_index: int,
    geometry_index: int | None = None,
    target: str = "future_yaw_response",
    margin_gap: float = 0.03,
) -> dict[str, object]:
    geometry = pair_index if geometry_index is None else geometry_index
    return {
        "variant": "wrong_matched_history",
        "accepted": True,
        "checkpoint_label": checkpoint_label,
        "target": target,
        "left_seed": 1000 + pair_index,
        "right_seed": 2000 + pair_index,
        "left_step": 10 + pair_index,
        "right_step": 20 + pair_index,
        "relocated_obstacle_body_x": 25.0 + geometry,
        "relocated_obstacle_body_y": 0.1 * geometry,
        "relocated_obstacle_half_width": 1.5,
        "normal_margin": 0.002 + 0.001 * (pair_index % 4),
        "variant_margin": 0.002 + 0.001 * (pair_index % 4) - margin_gap,
        "normal_success": True,
        "variant_success": False,
        "success_drop": True,
        "margin_gap": margin_gap,
        "normal_first_steer": 0.1,
        "normal_first_throttle": 0.0,
        "normal_first_brake": 0.2,
        "variant_first_steer": -0.1,
        "variant_first_throttle": 0.0,
        "variant_first_brake": 0.1,
    }


def test_add_family_metadata_preserves_raw_duplicate_geometry():
    rows = pd.DataFrame(
        [
            _row(checkpoint_label="a", pair_index=1, geometry_index=99),
            _row(checkpoint_label="b", pair_index=1, geometry_index=99),
            _row(checkpoint_label="a", pair_index=2),
        ]
    )
    selected = select_raw_retained_rows(rows, min_margin_gap=0.0)
    converted = add_family_metadata(
        selected,
        source_policy_map={"a": "a.pt", "b": "b.pt"},
        source_family="family",
    )

    assert len(converted) == 3
    duplicate_groups = converted[converted["duplicate_geometry_group_size"] == 2]
    assert len(duplicate_groups) == 2
    assert set(duplicate_groups["source_checkpoint_label"]) == {"a", "b"}
    assert set(duplicate_groups["duplicate_geometry_source_labels"]) == {"a,b"}


def test_add_family_metadata_fails_closed_for_unmapped_label():
    rows = pd.DataFrame([_row(checkpoint_label="missing", pair_index=1)])
    selected = select_raw_retained_rows(rows, min_margin_gap=0.0)

    with pytest.raises(ValueError, match="missing labels"):
        add_family_metadata(selected, source_policy_map={"a": "a.pt"}, source_family="family")


def test_run_family_aggregate_conversion_writes_export_and_safety_artifacts(tmp_path):
    rows = []
    for pair_index in range(4):
        rows.append(_row(checkpoint_label="a", pair_index=pair_index, target="future_yaw_response"))
        rows.append(_row(checkpoint_label="b", pair_index=10 + pair_index, target="future_braking_deceleration"))
    source_csv = tmp_path / "accepted.csv"
    pd.DataFrame(rows).to_csv(source_csv, index=False)
    run_dir = tmp_path / "conversion"

    summary = run_family_aggregate_conversion(
        accepted_rows_csv=source_csv,
        run_dir=run_dir,
        source_policy_map={"a": "a.pt", "b": "b.pt"},
        min_rows=8,
        min_physical_pairs=8,
        min_left_steps=8,
        min_checkpoints=2,
        min_targets=2,
        min_margin_buckets=1,
    )

    assert summary["passed"]
    assert summary["replay_started"] is False
    assert summary["objective_optimization_started"] is False
    assert summary["mixed_source_objective_npz_written"] is False
    assert (run_dir / "family_aggregate_boundary_rows.csv").exists()
    assert (run_dir / "source_policy_map.json").exists()
    assert (run_dir / "source_summary.csv").exists()
    assert (run_dir / "duplicate_geometry_summary.csv").exists()
    assert (run_dir / "replay_plan.json").exists()
    replay_plan = json.loads((run_dir / "replay_plan.json").read_text(encoding="utf-8"))
    assert replay_plan["replay_started"] is False
    assert replay_plan["mixed_source_objective_npz_allowed"] is False


def test_run_family_aggregate_conversion_rejects_when_thresholds_fail(tmp_path):
    source_csv = tmp_path / "accepted.csv"
    pd.DataFrame([_row(checkpoint_label="a", pair_index=1)]).to_csv(source_csv, index=False)

    summary = run_family_aggregate_conversion(
        accepted_rows_csv=source_csv,
        run_dir=tmp_path / "conversion",
        source_policy_map={"a": "a.pt"},
        min_rows=2,
        min_physical_pairs=2,
        min_left_steps=2,
        min_checkpoints=1,
        min_targets=1,
        min_margin_buckets=1,
    )

    assert not summary["passed"]
    assert summary["decision"] == "family_aggregate_conversion_export_reject"


def test_load_source_policy_map_combines_json_and_specs(tmp_path):
    source_map = tmp_path / "source_policy_map.json"
    source_map.write_text(json.dumps({"a": "a.pt"}), encoding="utf-8")

    result = load_source_policy_map(
        source_policy_map_json=source_map,
        source_policy_specs=(),
    )

    assert result == {"a": "a.pt"}
