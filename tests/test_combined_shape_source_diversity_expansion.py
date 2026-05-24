import pandas as pd

from autodrift.combined_shape_source_diversity_expansion import (
    admission_metrics,
    default_shape_grid_specs,
    select_trust_primary_non_collision_sources,
    source_diversity_summary,
)


def test_default_shape_grid_specs_keep_named_m636_styles():
    specs = {spec.name: spec for spec in default_shape_grid_specs()}

    assert "source8_recovery_style" in specs
    assert "source7_preservation_style" in specs
    assert 0.08 in specs["source7_preservation_style"].steer_deltas
    assert -0.06 in specs["source8_recovery_style"].throttle_deltas


def test_select_trust_primary_non_collision_sources_excludes_collision_rows():
    near = pd.DataFrame(
        [
            _near_source(8, primary="mean_l2_excess", collision=False, trust=True),
            _near_source(1, primary="candidate_collision", collision=True, trust=True),
            _near_source(2, primary="mean_l2_excess", collision=True, trust=True),
            _near_source(3, primary="insufficient_margin", collision=False, trust=False),
        ]
    )
    sources = pd.DataFrame(
        [
            {"source_index": 1, "left_seed": 1, "right_seed": 2, "left_step": 3, "right_step": 3},
            {"source_index": 8, "left_seed": 8, "right_seed": 9, "left_step": 3, "right_step": 3},
            {"source_index": 2, "left_seed": 2, "right_seed": 3, "left_step": 3, "right_step": 3},
        ]
    )

    selected = select_trust_primary_non_collision_sources(near, sources)

    assert selected["source_index"].tolist() == [8]
    assert selected["source_diversity_expansion_focus"].tolist() == [True]


def test_source_diversity_summary_counts_accepted_source_rows_not_candidates():
    sources = pd.DataFrame(
        [
            _source_row(8, 100, 101, "ood", "future_yaw_response"),
            _source_row(0, 102, 103, "ood", "future_braking_deceleration"),
            _source_row(7, 104, 105, "fresh", "future_braking_deceleration"),
        ]
    )
    source_summary = [
        {"source_index": 8, "accepted_after_projection": 25},
        {"source_index": 0, "accepted_after_projection": 10},
        {"source_index": 7, "accepted_after_projection": 0},
    ]

    rows = source_diversity_summary(selected_source_rows=sources, source_summary_rows=source_summary)
    by_set = {row["set"]: row for row in rows}

    assert by_set["selected_sources"]["rows"] == 3
    assert by_set["accepted_sources"]["rows"] == 2
    assert by_set["accepted_sources"]["unique_left_seeds"] == 2


def test_admission_metrics_require_source_diversity_thresholds():
    sources = pd.DataFrame(
        [
            _source_row(10 + idx, 100 + idx, 200 + idx, "fresh" if idx < 4 else "ood", target)
            for idx, target in enumerate(
                [
                    "future_yaw_response",
                    "future_braking_deceleration",
                    "future_yaw_response",
                    "future_lateral_accel_response",
                    "future_yaw_response",
                    "future_braking_deceleration",
                    "future_yaw_response",
                    "future_braking_deceleration",
                ]
            )
        ]
    )
    source_summary = [
        {"source_index": int(source_index), "accepted_after_projection": 1}
        for source_index in sources["source_index"]
    ]

    metrics = admission_metrics(
        selected_source_rows=sources,
        source_summary_rows=source_summary,
        trust_limits_preserved=True,
    )

    assert metrics["accepted_source_rows"] == 8
    assert metrics["accepted_unique_physical_pairs"] == 8
    assert metrics["accepted_unique_left_seeds"] == 8
    assert metrics["accepted_surfaces"] == 2
    assert metrics["accepted_targets"] == 3
    assert metrics["target_corpus_admission_candidate"] is True

    failed = admission_metrics(
        selected_source_rows=sources,
        source_summary_rows=source_summary[:5],
        trust_limits_preserved=True,
    )
    assert failed["target_corpus_admission_candidate"] is False


def _near_source(source_index: int, *, primary: str, collision: bool, trust: bool) -> dict[str, object]:
    return {
        "source_index": source_index,
        "best_primary_failure": primary,
        "has_collision_near_miss": collision,
        "has_trust_near_miss": trust,
    }


def _source_row(source_index: int, left_seed: int, right_seed: int, surface: str, target: str) -> dict[str, object]:
    return {
        "source_index": source_index,
        "left_seed": left_seed,
        "right_seed": right_seed,
        "left_step": 3,
        "right_step": 3,
        "surface": surface,
        "target": target,
        "variant": "delayed_history",
    }
