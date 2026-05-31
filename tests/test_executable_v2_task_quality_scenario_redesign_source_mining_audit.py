from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_scenario_redesign_source_mining_audit as audit
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _template_row(candidate_id: str, tier: str, split: str, role: str = "stable_aes_only") -> dict[str, object]:
    return {
        "candidate_source_id": candidate_id,
        "source_v1_bounded_panel_spec_id": candidate_id,
        "source_scenario_spec_id": f"{candidate_id}_scenario",
        "feasibility_tier_id": tier,
        "source_split": split,
        "source_role_semantics": role,
        "surface_variant": "steady_surface",
        "speed_ref": 18.0,
        "mu": 0.4,
        "target_support_mode": "joint_positive_support",
        "target_boundary_mode": "test",
        "expected_joint_support": tier in {audit.TIER_A, audit.TIER_B},
        "expected_near_miss_support": tier in {audit.TIER_C, audit.TIER_D},
        "mitigation_only": tier == audit.TIER_E,
        "positive_support_gate_required": tier != audit.TIER_E,
        "paper_holdout_candidate": split == "paper_holdout_candidate",
    }


def _support_row(candidate_id: str, supported: bool, accepted: int) -> dict[str, object]:
    return {
        "candidate_source_id": candidate_id,
        "source_v1_bounded_panel_spec_id": candidate_id,
        "source_scenario_spec_id": f"{candidate_id}_scenario",
        "source_support_status": "supported" if supported else "unsupported",
        "materialization_admissible": supported,
        "source_support_accepted_cell_count_total": accepted,
        "source_support_feasible_profile_count": 1 if supported else 0,
        "source_support_profile_count": 1,
        "source_support_failure_reason": "none" if supported else "no_accepted_cells",
        "source_support_label_counts": "{}",
        "source_support_reject_reason_counts": "{}",
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
    }


def test_join_support_rows_detects_missing_template() -> None:
    joined, missing = audit.join_support_rows(
        template_rows=[_template_row("a", audit.TIER_A, "public_debug")],
        materialization_rows=[_support_row("a", True, 3), _support_row("missing", False, 0)],
    )

    assert len(joined) == 1
    assert len(missing) == 1
    assert joined[0]["feasibility_tier_id"] == audit.TIER_A
    assert joined[0]["materialization_admissible"] is True


def test_source_mining_audit_writes_joined_aggregates(tmp_path: Path) -> None:
    template_rows = [
        _template_row("a", audit.TIER_A, "public_debug"),
        _template_row("b", audit.TIER_B, "public_gate"),
        _template_row("c", audit.TIER_C, "paper_holdout_candidate"),
        _template_row("d", audit.TIER_D, "public_debug"),
        _template_row("e", audit.TIER_E, "public_gate"),
    ]
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    write_json(source_dir / "summary.json", {"supported_source_count": 5, "accepted_cell_count_total": 15})
    write_csv_rows(
        source_dir / "support_first_materialization_admissibility_input.csv",
        [_support_row(row["candidate_source_id"], True, 3) for row in template_rows],
    )
    template = tmp_path / "template.json"
    write_json(template, {"candidate_sources": template_rows})

    summary = audit.audit_scenario_redesign_source_mining(
        template_path=template,
        source_mining_dir=source_dir,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "task_quality_scenario_source_mining_result_audit_incomplete_or_fail"
    assert summary["joined_source_count"] == 5
    assert summary["template_join_missing_count"] == 0
    assert summary["tier_a_b_positive_support_pass"] is True
    assert summary["tier_c_d_near_miss_support_pass"] is True
    assert summary["split_support_pass"] is True
    assert summary["supported_source_count"] == 5
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "tier_support_aggregate.csv").exists()
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["joined_source_support_rows"] == 5
