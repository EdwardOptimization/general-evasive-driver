from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_scenario_redesign_templates as templates
from autodrift.artifacts import read_json
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
)


def test_redesign_template_has_expected_first_wave_counts() -> None:
    rows = templates.generate_v0_candidate_rows()
    summary = templates.summarize_candidate_rows(rows)

    assert len(rows) == 640
    assert summary["candidate_row_count"] == 640
    assert len(summary["feasibility_tier_counts"]) == 5
    assert len(summary["role_counts"]) == 4
    assert len(summary["surface_counts"]) == 2
    assert len(summary["speed_counts"]) == 4
    assert len(summary["mu_counts"]) == 4
    assert all(count == 128 for count in summary["feasibility_tier_counts"].values())
    assert all(count == 160 for count in summary["role_counts"].values())
    assert summary["surface_counts"] == {"post_friction_step": 320, "steady_surface": 320}


def test_redesign_template_preserves_role_contracts_and_splits() -> None:
    rows = templates.generate_v0_candidate_rows()
    by_role = {role: [row for row in rows if row["source_role_semantics"] == role] for role in templates.ROLE_SETTINGS}
    summary = templates.summarize_candidate_rows(rows)

    assert all(row["source_required_label"] == "aeb_feasible" for row in by_role[ROLE_STABLE_AEB])
    assert all(row["require_aeb_infeasible"] is False for row in by_role[ROLE_STABLE_AEB])
    assert all(row["source_required_label"] == "aes_feasible" for row in by_role[ROLE_STABLE_AES])
    assert all(row["require_aeb_infeasible"] is True for row in by_role[ROLE_STABLE_AES])
    assert all(row["source_required_label"] == "drift_required" for row in by_role[ROLE_DRIFT_REQUIRED])
    assert all(row["recovery_horizon_required"] is True for row in by_role[ROLE_DRIFT_REQUIRED])
    assert all(row["source_required_label"] == "unavoidable" for row in by_role[ROLE_UNAVOIDABLE])
    assert all(row["mitigation_metric_contract_present"] is True for row in by_role[ROLE_UNAVOIDABLE])
    assert summary["source_split_counts"] == {
        "paper_holdout_candidate": 64,
        "public_debug": 384,
        "public_gate": 192,
    }


def test_redesign_template_blocks_actor_label_and_ranking_shortcuts() -> None:
    rows = templates.generate_v0_candidate_rows()
    summary = templates.summarize_candidate_rows(rows)

    assert summary["positive_support_gate_required_count"] == 512
    assert summary["paper_holdout_candidate_count"] == 64
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert all(row["labels_enter_actor_input"] is False for row in rows)
    assert all(row["v2_ranking_admissible_by_default"] is False for row in rows)
    assert all(row["scenario_quality_branch_id"] == templates.SCENARIO_QUALITY_BRANCH_ID for row in rows)

    hashes = [row["profile_control_hash"] for row in rows]
    assert len(hashes) == len(set(hashes))


def test_write_redesign_template_round_trips_json(tmp_path: Path) -> None:
    output = tmp_path / "template.json"
    payload = templates.write_v0_template(output)
    loaded = read_json(output)

    assert loaded["template_id"] == templates.TEMPLATE_ID
    assert loaded["summary"]["candidate_row_count"] == 640
    assert loaded["summary"]["source_mining_execution_started"] is False
    assert loaded["summary"]["materialized_row_count"] == 0
    assert loaded["candidate_sources"][0]["profile_control_hash"]
    assert loaded["summary"] == payload["summary"]
