from __future__ import annotations

from autodrift.v4_closer_obstacle_source_generation import (
    build_generation_plan_rows,
    classify_closer_obstacle_generation_result,
)


def _axis_summary(
    group: int,
    *,
    axis: str,
    cause: str,
    seed: int = 78048,
    step: int = 21,
) -> dict[str, str]:
    return {
        "source_group_id": str(group),
        "seed": str(seed),
        "step": str(step),
        "boundary_axis": axis,
        "trace_role": "primary_boundary_new_to_m844",
        "cause_class": cause,
        "closest_margin_abs": "0.08",
        "preferred_fault_family": "steering_fault",
        "warmup_mode": "brake_tap",
    }


def _trace(
    group: int,
    *,
    axis: str,
    parameter: float,
    margin: float,
    outcome: str,
    step: int = 21,
) -> dict[str, str]:
    return {
        "source_group_id": str(group),
        "step": str(step),
        "boundary_axis": axis,
        "parameter_value": str(parameter),
        "min_clearance_margin": str(margin),
        "outcome_class": outcome,
    }


def _target(group: int, *, seed: int = 78048, step: int = 21) -> dict[str, str]:
    return {
        "source_group_id": str(group),
        "seed": str(seed),
        "step": str(step),
        "snapshot_uid": f"{group}:0:{step}",
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
    }


def _plan(group: int) -> dict[str, str]:
    return {
        "candidate_id": str(group),
        "source_group_id": str(group),
        "step": "21",
        "seed": "78048",
        "source_obstacle_body_x": "14.0",
        "source_obstacle_body_y": "-1.0",
        "source_obstacle_half_width": "0.8",
    }


def test_build_generation_plan_rows_moves_safe_wide_toward_lower_margin() -> None:
    rows = build_generation_plan_rows(
        [_axis_summary(1, axis="obstacle_lateral_offset", cause="all_safe_wide")],
        [
            _trace(1, axis="obstacle_lateral_offset", parameter=-0.4, margin=0.20, outcome="safe_wide"),
            _trace(1, axis="obstacle_lateral_offset", parameter=0.0, margin=0.09, outcome="safe_wide"),
            _trace(1, axis="obstacle_lateral_offset", parameter=0.4, margin=0.12, outcome="safe_wide"),
        ],
        [_target(1)],
        [_plan(1)],
        max_source_axes=8,
        safe_wide_deltas=(0.15, 0.30),
        safe_wide_timing_deltas=(0.5,),
        safe_wide_half_width_deltas=(0.05,),
        collision_side_deltas=(0.1,),
        collision_timing_deltas=(0.25,),
        collision_half_width_deltas=(0.03,),
    )

    assert [row["generated_parameter"] for row in rows] == [0.15, 0.30]
    assert {row["generation_family"] for row in rows} == {"all_safe_closer_obstacle"}
    assert {row["trace_role"] for row in rows} == {"primary_boundary_new_to_m844"}
    assert rows[0]["base_trace_parameter"] == 0.0
    assert rows[0]["base_trace_margin"] == 0.09


def test_build_generation_plan_rows_moves_collision_back_toward_source() -> None:
    rows = build_generation_plan_rows(
        [_axis_summary(2, axis="obstacle_timing", cause="all_collision_or_negative")],
        [
            _trace(2, axis="obstacle_timing", parameter=9.0, margin=-0.40, outcome="negative"),
            _trace(2, axis="obstacle_timing", parameter=11.0, margin=-0.05, outcome="negative"),
        ],
        [_target(2)],
        [{**_plan(2), "source_obstacle_body_x": "14.0"}],
        max_source_axes=8,
        safe_wide_deltas=(0.15,),
        safe_wide_timing_deltas=(0.5,),
        safe_wide_half_width_deltas=(0.05,),
        collision_side_deltas=(0.1,),
        collision_timing_deltas=(0.25, 0.50),
        collision_half_width_deltas=(0.03,),
    )

    assert [row["generated_parameter"] for row in rows] == [11.25, 11.5]
    assert {row["generation_family"] for row in rows} == {"all_collision_safer_side"}
    assert rows[0]["generation_direction"] == 1.0


def test_classify_closer_obstacle_generation_result_contract_sparse_and_all_weak() -> None:
    accepted = []
    for index in range(32):
        accepted.append(
            {
                "source_group_id": str(index % 10),
                "seed": str(78048 + index % 5),
                "preferred_fault_family": f"fault_{index % 4}",
                "boundary_axis": ["obstacle_lateral_offset", "obstacle_timing", "obstacle_half_width"][index % 3],
            }
        )
    pairability = [{"pairability_tier": "primary_0_10"} for _ in range(40)]

    common = {
        "actor_changed": False,
        "residual_changed": False,
        "generation_plan_rows": 300,
        "primary_source_groups_planned": 32,
        "primary_seed_count_planned": 8,
        "primary_fault_family_count_planned": 6,
        "min_plan_rows": 300,
        "min_planned_sources": 32,
        "min_planned_seeds": 8,
        "min_planned_fault_families": 6,
        "strong_min_rows": 80,
        "sparse_min_rows": 32,
        "strong_min_primary_rows": 60,
        "sparse_min_primary_rows": 24,
        "min_source_groups": 24,
        "sparse_min_source_groups": 10,
        "min_seeds": 8,
        "sparse_min_seeds": 5,
        "min_fault_families": 6,
        "sparse_min_fault_families": 4,
        "min_boundary_axes": 3,
        "max_source_group_dominance": 0.10,
        "max_seed_dominance": 0.25,
        "min_pairability_rows": 120,
        "sparse_min_pairability_rows": 40,
    }

    assert (
        classify_closer_obstacle_generation_result(
            **common,
            accepted_rows=accepted,
            primary_accepted_rows=accepted,
            pairability_rows=pairability,
        )
        == "v4_closer_obstacle_source_generation_sparse_useful"
    )
    assert (
        classify_closer_obstacle_generation_result(
            **common,
            accepted_rows=accepted[:10],
            primary_accepted_rows=accepted[:10],
            pairability_rows=[],
        )
        == "v4_closer_obstacle_source_generation_all_weak"
    )
    assert (
        classify_closer_obstacle_generation_result(
            **{**common, "actor_changed": True},
            accepted_rows=accepted,
            primary_accepted_rows=accepted,
            pairability_rows=pairability,
        )
        == "v4_closer_obstacle_source_generation_contract_violation"
    )
