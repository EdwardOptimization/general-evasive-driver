from autodrift.v4_adaptive_boundary_bracketing import (
    accepted_primary,
    axis_expansion_values,
    axis_initial_values,
    classify_adaptive_bracketing_result,
    find_adjacent_margin_bracket,
    select_adaptive_balanced_rows,
)


def _row(parameter, margin, *, success=True, collision=False, reconstructed=True):
    return {
        "parameter_value": parameter,
        "min_clearance_margin": margin,
        "success": success,
        "collision": collision,
        "reconstructed": reconstructed,
    }


def test_axis_initial_values_are_sorted_unique_and_clipped():
    timing = axis_initial_values(
        "obstacle_timing",
        body_x=1.1,
        body_y=0.0,
        half_width=0.8,
        timing_deltas=(-0.5, 0.5, 0.5),
        lateral_deltas=(-0.2, 0.2),
        half_width_deltas=(-1.0, 0.2),
    )
    assert timing == sorted(timing)
    assert len(timing) == len(set(timing))
    assert min(timing) >= 1.0

    half_width = axis_initial_values(
        "obstacle_half_width",
        body_x=10.0,
        body_y=0.0,
        half_width=0.06,
        timing_deltas=(-0.5, 0.5),
        lateral_deltas=(-0.2, 0.2),
        half_width_deltas=(-1.0, 0.2),
    )
    assert min(half_width) >= 0.05


def test_axis_expansion_values_cover_both_sides():
    lateral = axis_expansion_values(
        "obstacle_lateral_offset",
        body_x=10.0,
        body_y=0.2,
        half_width=0.8,
        max_expansion_attempts=3,
    )
    assert min(lateral) < 0.2
    assert max(lateral) > 0.2
    assert len(lateral) == len(set(lateral))


def test_find_adjacent_margin_bracket_selects_sign_change_pair():
    rows = [
        _row(-0.4, 0.2),
        _row(-0.2, 0.1),
        _row(0.0, -0.02, success=False, collision=True),
        _row(0.2, 0.04),
        _row(0.4, 0.3),
    ]
    bracket = find_adjacent_margin_bracket(rows)
    assert bracket is not None
    negative, positive = bracket
    assert negative["parameter_value"] == 0.0
    assert positive["parameter_value"] == 0.2


def test_accepted_primary_requires_success_and_margin_window():
    assert accepted_primary(_row(0.0, 0.00002), primary_margin_threshold=0.00005)
    assert not accepted_primary(_row(0.0, 0.0002), primary_margin_threshold=0.00005)
    assert not accepted_primary(_row(0.0, -0.00001, success=False, collision=True), primary_margin_threshold=0.00005)


def test_classify_adaptive_bracketing_result_pass_and_axis_concentration():
    rows = []
    for idx in range(30):
        rows.append(
            {
                "seed": idx % 10,
                "source_group_id": idx % 15,
                "source_index": idx,
                "fault_family_pair": f"pair{idx % 5}",
                "warmup_mode": "natural_policy" if idx % 2 == 0 else "brake_tap",
                "boundary_axis": ["obstacle_timing", "obstacle_lateral_offset", "obstacle_half_width"][idx % 3],
            }
        )
    assert (
        classify_adaptive_bracketing_result(
            actor_changed=False,
            residual_changed=False,
            warmup_artifact_rows=0,
            replay_errors=0,
            brackets_valid=12,
            bracket_nonmonotone_count=0,
            accepted_rows=rows,
            min_rows=30,
            min_seeds=8,
            min_source_groups=10,
            min_source_indices=30,
            min_fault_pairs=5,
            min_warmup_modes=2,
            min_boundary_axes=3,
            max_seed_dominance=0.2,
            max_source_group_dominance=0.2,
            max_fault_pair_dominance=0.3,
            max_boundary_axis_dominance=0.6,
        )
        == "v4_adaptive_boundary_bracketing_pass"
    )

    concentrated = [{**row, "boundary_axis": "obstacle_timing"} for row in rows]
    assert (
        classify_adaptive_bracketing_result(
            actor_changed=False,
            residual_changed=False,
            warmup_artifact_rows=0,
            replay_errors=0,
            brackets_valid=12,
            bracket_nonmonotone_count=0,
            accepted_rows=concentrated,
            min_rows=30,
            min_seeds=8,
            min_source_groups=10,
            min_source_indices=30,
            min_fault_pairs=5,
            min_warmup_modes=2,
            min_boundary_axes=3,
            max_seed_dominance=0.2,
            max_source_group_dominance=0.2,
            max_fault_pair_dominance=0.3,
            max_boundary_axis_dominance=0.6,
        )
        == "v4_adaptive_boundary_bracketing_axis_concentrated"
    )


def test_select_adaptive_balanced_rows_prioritizes_underrepresented_axes():
    rows = []
    for idx in range(12):
        rows.append(
            {
                "candidate_id": idx,
                "seed": idx % 4,
                "source_group_id": idx,
                "fault_family_pair": f"pair{idx % 3}",
                "boundary_axis": "obstacle_lateral_offset",
                "min_clearance_margin": 0.00002,
            }
        )
    for idx in range(12, 18):
        rows.append(
            {
                "candidate_id": idx,
                "seed": idx % 4,
                "source_group_id": idx,
                "fault_family_pair": f"pair{idx % 3}",
                "boundary_axis": "obstacle_timing",
                "min_clearance_margin": 0.00002,
            }
        )
    for idx in range(18, 24):
        rows.append(
            {
                "candidate_id": idx,
                "seed": idx % 4,
                "source_group_id": idx,
                "fault_family_pair": f"pair{idx % 3}",
                "boundary_axis": "obstacle_half_width",
                "min_clearance_margin": 0.00002,
            }
        )

    selected = select_adaptive_balanced_rows(
        rows,
        max_rows_per_seed=8,
        max_rows_per_source_group=2,
        max_rows_per_fault_pair=10,
        max_rows_per_boundary_axis=6,
    )
    axis_counts = {}
    for row in selected:
        axis_counts[row["boundary_axis"]] = axis_counts.get(row["boundary_axis"], 0) + 1
    assert len(selected) == 18
    assert axis_counts == {
        "obstacle_half_width": 6,
        "obstacle_lateral_offset": 6,
        "obstacle_timing": 6,
    }
