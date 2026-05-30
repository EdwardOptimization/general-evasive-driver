from autodrift.controller_family_off_track_dominance_localization import (
    _repair_targets_from_aggregate,
    localize_off_track_dominance,
)


def test_repair_targets_preserve_non_profile_slice_identity() -> None:
    aggregate_rows = [
        {
            "scale_up_variant_label": "best_off_track_variant",
            "source_edge": "edge_a",
            "episode_count": 24,
            "success_obstacle_pass_rate": 0.1,
            "collision_failure_rate": 0.05,
            "off_track_noncollision_noncompletion_rate": 0.85,
            "clearance_margin_mean": 1.0,
        },
        {
            "scale_up_variant_label": "best_off_track_variant",
            "source_edge": "edge_b",
            "episode_count": 24,
            "success_obstacle_pass_rate": 0.5,
            "collision_failure_rate": 0.05,
            "off_track_noncollision_noncompletion_rate": 0.45,
            "clearance_margin_mean": 2.0,
        },
    ]

    [target] = _repair_targets_from_aggregate(
        aggregate_rows,
        slice_type="variant_source_edge",
        slice_keys=("scale_up_variant_label", "source_edge"),
    )

    assert target["slice_id"] == "best_off_track_variant::edge_a"
    assert target["repair_reason"] == "off_track>=0.8 and collision<=0.1"
    assert target["diagnostic_only_no_ranking_claim"] is True


def test_localization_smoke_writes_required_artifacts(tmp_path) -> None:
    summary = localize_off_track_dominance(output_dir=tmp_path)

    assert summary["episode_count"] == 864
    assert summary["result_class"] == "off_track_dominance_localization_pass"
    assert summary["variant_source_edge_aggregate_rows"] > 0
    assert summary["variant_task_family_aggregate_rows"] > 0
    assert summary["variant_profile_aggregate_rows"] > 0
    assert summary["source_task_family_aggregate_rows"] > 0
    assert summary["repair_target_slice_count"] > 0
    assert (tmp_path / "variant_source_edge_aggregate.csv").exists()
    assert (tmp_path / "repair_target_slices.csv").exists()
