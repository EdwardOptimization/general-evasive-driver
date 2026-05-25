from __future__ import annotations

from autodrift.v4_pair_delta_boundary_expansion import (
    build_pairability_projection_rows,
    classify_pair_delta_boundary_expansion,
    select_target_source_rows,
)


def _source_row(group: int, *, seed: int, fault: str, warmup: str = "brake_tap") -> dict[str, str]:
    return {
        "source_group_id": str(group),
        "seed": str(seed),
        "warmup_mode": warmup,
        "preferred_fault": f"{fault}_fault",
        "preferred_fault_family": fault,
        "preferred_fault_severity": "extreme",
        "wrong_fault": "nominal",
        "wrong_fault_family": "nominal",
        "fault_family_pair": f"{fault}->nominal",
        "source_axis": "warmup_probe_mode",
        "preferred_fidelity_class": "current_model_fault",
        "wrong_fidelity_class": "current_model_fault",
        "success": "True",
        "collision": "False",
    }


def _plan_row(group: int, *, seed: int, step: int = 21) -> dict[str, str]:
    return {
        "source_group_id": str(group),
        "snapshot_uid": f"{group}:0:{step}",
        "source_index": str(group),
        "seed": str(seed),
        "step": str(step),
        "source_obstacle_body_x": "14.0",
        "source_obstacle_body_y": "-1.0",
        "source_obstacle_half_width": "0.8",
        "fault_onset_bucket": "pre_emergency",
        "candidate_id": str(group),
    }


def test_select_target_source_rows_prioritizes_non_active_sources() -> None:
    sources = [
        _source_row(1, seed=78048, fault="brake_authority_drop"),
        _source_row(2, seed=78049, fault="steering_fault"),
        _source_row(35, seed=78059, fault="mass_cg_shift"),
    ]
    plans = [_plan_row(1, seed=78048), _plan_row(2, seed=78049), _plan_row(35, seed=78059)]
    balanced = [
        {
            "left_source_group_id": "35",
            "left_seed": "78059",
            "left_fault_family": "mass_cg_shift",
        }
    ]

    selected = select_target_source_rows(
        sources,
        plans,
        balanced,
        existing_boundary_rows=[{"source_group_id": "2"}],
        max_targets=8,
        max_targets_per_seed=8,
        max_targets_per_fault_family=8,
        max_targets_per_warmup_mode=8,
        max_targets_per_source_group=1,
        active_control_budget=0,
    )

    assert {row["source_group_id"] for row in selected} == {1, 2}
    assert selected[0]["source_group_id"] == 2
    assert {row["source_target_class"] for row in selected} == {"new_underrepresented_boundary"}
    assert {row["boundary_source_status"] for row in selected} == {"boundary_new_to_m844", "existing_boundary_recovered"}


def _boundary_row(
    candidate_id: int,
    *,
    source: int,
    seed: int,
    fault: str,
    steer: float,
    margin: float = 0.01,
    body_y: float = -1.0,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source_group_id": source,
        "seed": seed,
        "preferred_fault_family": fault,
        "boundary_axis": "obstacle_lateral_offset",
        "source_target_class": "new_underrepresented_boundary",
        "boundary_source_status": "boundary_new_to_m844",
        "target_obstacle_body_x": 14.0,
        "target_obstacle_body_y": body_y,
        "target_obstacle_half_width": 0.8,
        "first_steer": steer,
        "first_throttle": 0.0,
        "first_brake": 0.1,
        "success": True,
        "collision": False,
        "min_clearance_margin": margin,
    }


def test_build_pairability_projection_rows_filters_action_and_geometry() -> None:
    rows = [
        _boundary_row(1, source=1, seed=78048, fault="brake_authority_drop", steer=0.10, body_y=-1.0),
        _boundary_row(2, source=2, seed=78049, fault="steering_fault", steer=0.13, body_y=-1.1),
        _boundary_row(3, source=3, seed=78050, fault="combined_fault", steer=0.11, body_y=4.0),
    ]

    projections = build_pairability_projection_rows(
        rows,
        min_first_action_l2=0.014,
        max_obstacle_distance=0.10,
        diagnostic_max_obstacle_distance=0.20,
    )

    assert len(projections) == 1
    assert projections[0]["left_source_group_id"] == 1
    assert projections[0]["right_source_group_id"] == 2
    assert projections[0]["pairability_tier"] == "primary_0_10"


def test_classify_pair_delta_boundary_expansion_sparse_and_all_weak() -> None:
    accepted = []
    for index in range(50):
        accepted.append(
            {
                "source_group_id": str(index % 20),
                "seed": str(78048 + index % 6),
                "preferred_fault_family": f"fault_{index % 6}",
                "boundary_axis": ["obstacle_lateral_offset", "obstacle_timing", "obstacle_half_width"][index % 3],
                "source_target_class": "new_underrepresented_boundary",
            }
        )
    pairability = [
        {"pairability_tier": "primary_0_10", "left_source_group_id": str(index % 20)}
        for index in range(80)
    ]

    assert (
        classify_pair_delta_boundary_expansion(
            actor_changed=False,
            residual_changed=False,
            accepted_rows=accepted,
            pairability_rows=pairability,
            strong_min_rows=80,
            sparse_min_rows=50,
            min_new_underrepresented_rows=40,
            sparse_min_new_underrepresented_rows=24,
            min_source_groups=32,
            sparse_min_source_groups=20,
            min_seeds=8,
            sparse_min_seeds=6,
            min_fault_families=8,
            sparse_min_fault_families=6,
            min_boundary_axes=3,
            max_source_group_dominance=0.08,
            max_seed_dominance=0.20,
            min_pairability_rows=160,
            sparse_min_pairability_rows=80,
            min_projected_pairable_source_groups=16,
        )
        == "v4_pair_delta_boundary_expansion_sparse_useful"
    )

    assert (
        classify_pair_delta_boundary_expansion(
            actor_changed=False,
            residual_changed=False,
            accepted_rows=accepted[:10],
            pairability_rows=[],
            strong_min_rows=80,
            sparse_min_rows=50,
            min_new_underrepresented_rows=40,
            sparse_min_new_underrepresented_rows=24,
            min_source_groups=32,
            sparse_min_source_groups=20,
            min_seeds=8,
            sparse_min_seeds=6,
            min_fault_families=8,
            sparse_min_fault_families=6,
            min_boundary_axes=3,
            max_source_group_dominance=0.08,
            max_seed_dominance=0.20,
            min_pairability_rows=160,
            sparse_min_pairability_rows=80,
            min_projected_pairable_source_groups=16,
        )
        == "v4_pair_delta_boundary_expansion_all_weak"
    )
