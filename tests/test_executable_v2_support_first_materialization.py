from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.executable_v2_task_source_metadata_redesign import ROLE_STABLE_AES
from autodrift import executable_v2_support_first_materialization as materialization


def _template(source: str, *, speed: float = 20.0, mu: float = 1.0, surface: str = "steady_surface") -> dict[str, object]:
    return {
        "candidate_source_id": source,
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "source_role_semantics": ROLE_STABLE_AES,
        "source_required_label": "aes_feasible",
        "source_allowed_labels": "aes_feasible",
        "profile_name": "p0",
        "profile_group": ROLE_STABLE_AES,
        "source_family_id": surface,
        "surface_variant": surface,
        "speed_ref": speed,
        "mu": mu,
        "friction_step_enabled": False,
        "friction_step_at": "",
        "dt": 0.05,
        "min_time_after_friction_step": 0.0,
        "require_aeb_infeasible": True,
        "ego_half_width": 0.9,
        "safety_margin": 0.3,
        "brake_mu_fraction": 0.9,
        "conventional_lateral_mu_fraction": 0.42,
        "drift_lateral_mu_fraction": 0.85,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
    }


def _support(source: str, *, supported: bool = True, accepted: int = 5) -> dict[str, object]:
    return {
        "candidate_source_id": source,
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "source_role_semantics": ROLE_STABLE_AES,
        "source_required_label": "aes_feasible",
        "source_allowed_labels": "aes_feasible",
        "source_support_status": "supported" if supported else "unsupported",
        "materialization_admissible": supported,
        "source_support_accepted_cell_count_total": accepted,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
    }


def _cell(source: str, distance: float, half_width: float, threshold: float) -> dict[str, object]:
    return {
        "candidate_source_id": source,
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "source_role_semantics": ROLE_STABLE_AES,
        "profile_name": "p0",
        "profile_group": ROLE_STABLE_AES,
        "speed_ref": 20.0,
        "mu": 1.0,
        "obstacle_distance": distance,
        "obstacle_half_width": half_width,
        "threshold_score": threshold,
    }


def test_select_sources_uses_supported_rows_only_and_enforces_caps() -> None:
    templates = [_template("s0"), _template("s1"), _template("s2")]
    support = [_support("s0", accepted=5), _support("s1", accepted=10), _support("s2", supported=False)]

    selected = materialization.select_sources(
        support_rows=support,
        template_rows=templates,
        max_sources_per_role=1,
        max_sources_per_role_surface=1,
    )

    assert [row["candidate_source_id"] for row in selected] == ["s1"]


def test_cell_selection_picks_boundary_and_representative() -> None:
    source = _template("s0")
    cells = [
        _cell("s0", 10.0, 0.3, 0.5),
        _cell("s0", 20.0, 0.4, 0.1),
        _cell("s0", 30.0, 0.5, 0.4),
    ]

    selected = materialization.select_cells_for_source(source_row=source, accepted_cells=cells, max_cells_per_source=2)

    assert [row["cell_selection_kind"] for row in selected] == [
        "boundary_min_threshold",
        "representative_median_distance",
    ]
    assert selected[0]["obstacle_distance"] == 20.0


def test_materialized_row_keeps_labels_out_of_actor_input() -> None:
    source = _template("s0")
    cell = {**_cell("s0", 20.0, 0.4, 0.1), "cell_selection_kind": "boundary_min_threshold"}

    row = materialization.build_materialized_row(source_row=source, cell=cell, index=0)

    assert row["labels_enter_actor_input"] is False
    assert row["v2_ranking_admissible_by_default"] is False
    assert row["reset_validation_required"] is True
    assert row["measured_execution_required"] is False
    assert row["env_config"]["obstacle"]["allowed_labels"] == ["aes_feasible"]
    assert row["env_config"]["obstacle"]["distance_range"] == [20.0, 20.0]


def test_run_materialization_writes_bounded_artifacts(tmp_path: Path) -> None:
    templates = [_template("s0"), _template("s1")]
    support = [_support("s0", accepted=5), _support("s1", accepted=4)]
    cells = [
        _cell("s0", 10.0, 0.3, 0.5),
        _cell("s0", 20.0, 0.4, 0.1),
        _cell("s1", 12.0, 0.3, 0.2),
        _cell("s1", 24.0, 0.5, 0.3),
    ]

    summary = materialization.run_support_first_materialization(
        support_rows=support,
        accepted_cells=cells,
        template_rows=templates,
        output_dir=tmp_path / "out",
        max_sources_per_role=2,
        max_sources_per_role_surface=2,
        max_cells_per_source=2,
    )

    assert summary["selected_source_count"] == 2
    assert summary["materialized_spec_count"] == 4
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["guardrail_violation_count"] == 0

    payload = read_json(tmp_path / "out" / "support_first_materialized_executable_v2_panel_specs.json")
    assert len(payload["executable_v2_panel_specs"]) == 4
    assert read_json(tmp_path / "out" / "summary.json")["contract_id"] == materialization.MATERIALIZATION_CONTRACT_ID


def test_claim_boundary_blocks_reset_and_ranking_claims() -> None:
    rows = materialization.claim_boundary_rows()
    by_claim = {row["claim"]: row for row in rows}

    assert by_claim["support_first_materialization_helper"]["admissible"] is True
    assert by_claim["project_materialization_execution_result"]["admissible"] is False
    assert by_claim["reset_feasibility"]["admissible"] is False
    assert by_claim["controller_family_ranking"]["admissible"] is False
