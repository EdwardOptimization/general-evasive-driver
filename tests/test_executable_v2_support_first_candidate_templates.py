from __future__ import annotations

from collections import Counter
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
)
from autodrift import executable_v2_support_first_candidate_templates as templates


def test_v0_template_has_expected_counts_and_grid_scale() -> None:
    rows = templates.generate_v0_candidate_rows()
    summary = templates.summarize_candidate_rows(rows)

    assert len(rows) == 288
    assert summary["candidate_row_count"] == 288
    assert summary["grid_cell_count_total"] == 465264
    assert set(summary["role_counts"]) == {
        ROLE_STABLE_AEB,
        ROLE_STABLE_AES,
        ROLE_DRIFT_REQUIRED,
        ROLE_UNAVOIDABLE,
    }
    assert set(summary["surface_counts"]) == {"post_friction_step", "steady_surface"}
    assert len(summary["speed_counts"]) == 6
    assert len(summary["mu_counts"]) == 6


def test_v0_role_settings_preserve_role_separation() -> None:
    rows = templates.generate_v0_candidate_rows()
    by_role = {role: [row for row in rows if row["source_role_semantics"] == role] for role in templates.ROLE_SETTINGS}

    assert all(row["source_required_label"] == "aeb_feasible" for row in by_role[ROLE_STABLE_AEB])
    assert all(row["require_aeb_infeasible"] is False for row in by_role[ROLE_STABLE_AEB])
    assert all(row["source_required_label"] == "aes_feasible" for row in by_role[ROLE_STABLE_AES])
    assert all(row["require_aeb_infeasible"] is True for row in by_role[ROLE_STABLE_AES])
    assert all(row["source_required_label"] == "drift_required" for row in by_role[ROLE_DRIFT_REQUIRED])
    assert all(row["recovery_horizon_required"] is True for row in by_role[ROLE_DRIFT_REQUIRED])
    assert all(row["source_required_label"] == "unavoidable" for row in by_role[ROLE_UNAVOIDABLE])
    assert all(row["mitigation_metric_contract_present"] is True for row in by_role[ROLE_UNAVOIDABLE])


def test_v0_template_never_marks_labels_as_actor_inputs_or_ranking_defaults() -> None:
    rows = templates.generate_v0_candidate_rows()

    assert all(row["labels_enter_actor_input"] is False for row in rows)
    assert all(row["v2_ranking_admissible_by_default"] is False for row in rows)

    hashes = [row["profile_control_hash"] for row in rows]
    assert len(hashes) == len(set(hashes))


def test_v0_template_surface_and_bucket_distribution() -> None:
    rows = templates.generate_v0_candidate_rows()
    surfaces = Counter(row["surface_variant"] for row in rows)
    speeds = Counter(row["speed_ref"] for row in rows)
    mus = Counter(row["mu"] for row in rows)

    assert surfaces == {"steady_surface": 144, "post_friction_step": 144}
    assert set(speeds) == {10.0, 14.0, 18.0, 22.0, 26.0, 30.0}
    assert set(mus) == {0.25, 0.40, 0.60, 0.80, 1.00, 1.15}
    assert all(count == 48 for count in speeds.values())
    assert all(count == 48 for count in mus.values())


def test_write_v0_template_round_trips_json(tmp_path: Path) -> None:
    output = tmp_path / "template.json"
    payload = templates.write_v0_template(output)
    loaded = read_json(output)

    assert loaded["template_id"] == templates.TEMPLATE_ID
    assert loaded["summary"]["candidate_row_count"] == 288
    assert loaded["summary"]["project_artifact_source_mining_run"] is False
    assert loaded["summary"]["materialized_row_count"] == 0
    assert loaded["candidate_sources"][0]["profile_control_hash"]
    assert loaded["summary"] == payload["summary"]
