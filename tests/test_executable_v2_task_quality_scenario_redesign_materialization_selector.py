from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_scenario_redesign_materialization_selector as selector
from autodrift.artifacts import read_json, write_csv_rows


def _row(
    candidate_id: str,
    *,
    tier: str,
    role: str,
    surface: str,
    split: str = "public_gate",
    admissible: bool = True,
) -> dict[str, object]:
    return {
        "candidate_source_id": candidate_id,
        "source_v1_bounded_panel_spec_id": candidate_id,
        "source_scenario_spec_id": f"{candidate_id}_scenario",
        "feasibility_tier_id": tier,
        "source_role_semantics": role,
        "source_split": split,
        "surface_variant": surface,
        "speed_ref": 18.0,
        "mu": 0.4,
        "target_support_mode": "joint_positive_support",
        "target_boundary_mode": "test",
        "source_support_status": "supported" if admissible else "unsupported",
        "materialization_admissible": admissible,
        "source_support_accepted_cell_count_total": 3 if admissible else 0,
        "source_support_feasible_profile_count": 1 if admissible else 0,
        "source_support_profile_count": 1,
        "paper_holdout_candidate": split == "paper_holdout_candidate",
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "diagnostic_only_no_ranking_claim": True,
    }


def _complete_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for tier in selector.TIERS:
        for role in selector.ROLES:
            for surface in selector.SURFACES:
                rows.append(_row(f"{tier}_{role}_{surface}_gate_a", tier=tier, role=role, surface=surface))
                rows.append(_row(f"{tier}_{role}_{surface}_gate_b", tier=tier, role=role, surface=surface))
                rows.append(
                    _row(
                        f"{tier}_{role}_{surface}_debug_extra",
                        tier=tier,
                        role=role,
                        surface=surface,
                        split="public_debug",
                    )
                )
                rows.append(
                    _row(
                        f"{tier}_{role}_{surface}_holdout",
                        tier=tier,
                        role=role,
                        surface=surface,
                        split="paper_holdout_candidate",
                    )
                )
    return rows


def test_selector_balances_tier_role_and_surface_without_holdout() -> None:
    selected, failures = selector.select_materialization_sources(_complete_rows())

    assert not failures
    assert len(selected) == 80
    assert {row["source_split"] for row in selected} == {"public_gate"}
    assert sum(row["surface_variant"] == "steady_surface" for row in selected) == 40
    assert sum(row["surface_variant"] == "post_friction_step" for row in selected) == 40
    assert not any(row["paper_holdout_candidate"] for row in selected)


def test_materialize_source_subset_writes_config_and_summary(tmp_path: Path) -> None:
    joined = tmp_path / "joined.csv"
    output_config = tmp_path / "subset.json"
    output_dir = tmp_path / "run"
    write_csv_rows(joined, _complete_rows())

    summary = selector.materialize_source_subset(
        joined_source_support_path=joined,
        output_config_path=output_config,
        output_dir=output_dir,
    )

    assert summary["result_class"] == "task_quality_scenario_materialization_selector_pass"
    assert summary["selected_source_count"] == 80
    assert summary["expected_planned_workload_cell_count"] == 960
    assert summary["paper_holdout_selected_count"] == 0
    assert summary["tier_role_balance_pass"] is True
    assert summary["surface_balance_pass"] is True
    assert (output_dir / "selected_sources.csv").exists()
    persisted = read_json(output_config)
    assert persisted["selected_source_count"] == 80
    assert persisted["selection_summary"]["recommended_next_route"] == "route_to_materialization_command_design"
