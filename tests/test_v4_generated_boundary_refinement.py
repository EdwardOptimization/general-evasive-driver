from __future__ import annotations

from autodrift.v4_generated_boundary_refinement import (
    build_bracket_seed_rows,
    classify_generated_boundary_refinement_result,
)


def _generated(
    group: int,
    *,
    parameter: float,
    margin: float,
    generation_id: int,
    success: bool = True,
    collision: bool = False,
    axis: str = "obstacle_lateral_offset",
) -> dict[str, str]:
    return {
        "generation_id": str(generation_id),
        "source_group_id": str(group),
        "seed": str(78048 + group),
        "step": "21",
        "snapshot_uid": f"{group}:0:21",
        "source_index": str(group),
        "warmup_mode": "brake_tap",
        "preferred_fault": "steering_fault_extreme",
        "preferred_fault_family": "steering_fault",
        "preferred_fault_severity": "extreme",
        "preferred_fidelity_class": "current_model_fault",
        "wrong_fault": "nominal",
        "wrong_fault_family": "nominal",
        "wrong_fidelity_class": "current_model_fault",
        "fault_family_pair": "steering_fault->nominal",
        "fault_onset_bucket": "pre_emergency",
        "source_axis": "warmup_probe_mode",
        "source_target_class": "new_underrepresented_boundary",
        "boundary_source_status": "boundary_new_to_m844",
        "trace_role": "primary_boundary_new_to_m844",
        "trace_cause_class": "all_safe_wide",
        "generation_family": "all_safe_closer_obstacle",
        "boundary_axis": axis,
        "parameter_value": str(parameter),
        "target_obstacle_body_x": "12.0",
        "target_obstacle_body_y": str(parameter),
        "target_obstacle_half_width": "0.8",
        "success": str(success),
        "collision": str(collision),
        "min_clearance_margin": str(margin),
    }


def test_build_bracket_seed_rows_prioritizes_no_m860_boundary_brackets() -> None:
    generated = [
        _generated(1, parameter=-1.0, margin=0.12, generation_id=1),
        _generated(1, parameter=-0.8, margin=-0.02, generation_id=2, success=False, collision=True),
        _generated(2, parameter=-1.2, margin=0.03, generation_id=3),
        _generated(2, parameter=-1.0, margin=-0.03, generation_id=4, success=False, collision=True),
    ]
    accepted = [_generated(2, parameter=-1.2, margin=0.03, generation_id=3)]

    rows = build_bracket_seed_rows(
        generated,
        accepted,
        boundary_margin_threshold=0.05,
        max_brackets=8,
    )

    assert len(rows) == 2
    assert rows[0]["source_group_id"] == 1
    assert rows[0]["bracket_source_class"] == "no_m860_boundary"
    assert rows[1]["source_group_id"] == 2
    assert rows[1]["bracket_source_class"] == "m860_boundary_already_present"
    assert rows[0]["negative_parameter"] == -0.8
    assert rows[0]["positive_parameter"] == -1.0


def test_classify_generated_boundary_refinement_result_sparse_and_all_weak() -> None:
    accepted = []
    for index in range(8):
        accepted.append(
            {
                "source_group_id": str(index),
                "seed": str(78048 + index % 5),
                "preferred_fault_family": f"fault_{index % 4}",
                "boundary_source_status": "boundary_new_to_m844",
            }
        )
    combined = []
    for index in range(32):
        combined.append(
            {
                "source_group_id": str(index % 20),
                "seed": str(78048 + index % 5),
                "preferred_fault_family": f"fault_{index % 8}",
                "boundary_source_status": "boundary_new_to_m844",
            }
        )
    pairability = [{"pairability_tier": "primary_0_10"} for _ in range(40)]
    common = {
        "actor_changed": False,
        "residual_changed": False,
        "bracket_seed_rows": 13,
        "no_m860_boundary_bracket_seed_rows": 10,
        "unique_bracket_source_group_count": 13,
        "unique_bracket_seed_count": 3,
        "min_bracket_seed_rows": 10,
        "min_no_m860_bracket_seed_rows": 10,
        "min_bracket_source_groups": 10,
        "min_bracket_seeds": 3,
        "min_refined_rows": 8,
        "min_no_m860_refined_rows": 6,
        "min_refined_source_groups": 6,
        "sparse_combined_rows": 32,
        "sparse_combined_boundary_new_rows": 24,
        "sparse_combined_source_groups": 20,
        "sparse_combined_seeds": 5,
        "sparse_combined_fault_families": 8,
        "sparse_pairability_rows": 40,
        "strong_combined_rows": 60,
        "strong_combined_boundary_new_rows": 48,
        "strong_combined_source_groups": 32,
        "strong_combined_seeds": 8,
        "strong_combined_fault_families": 8,
        "strong_pairability_rows": 100,
    }

    assert (
        classify_generated_boundary_refinement_result(
            **common,
            accepted_refined_rows=accepted,
            accepted_no_m860_rows=accepted[:6],
            combined_rows=combined,
            pairability_rows=pairability,
        )
        == "v4_generated_boundary_refinement_sparse_useful"
    )
    assert (
        classify_generated_boundary_refinement_result(
            **common,
            accepted_refined_rows=accepted[:4],
            accepted_no_m860_rows=accepted[:4],
            combined_rows=combined,
            pairability_rows=pairability,
        )
        == "v4_generated_boundary_refinement_all_weak"
    )
    assert (
        classify_generated_boundary_refinement_result(
            **{**common, "actor_changed": True},
            accepted_refined_rows=accepted,
            accepted_no_m860_rows=accepted[:6],
            combined_rows=combined,
            pairability_rows=pairability,
        )
        == "v4_generated_boundary_refinement_contract_violation"
    )
