from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import executable_v2_stable_source_label_topup_preflight as topup


def _need(
    *,
    source: str,
    label: str,
    hidden: str,
    road: str,
    timing: str,
    lateral: str,
) -> dict[str, object]:
    return {
        "source_scenario_spec_id": source,
        "v2_role_surface_id": "stable_avoidance_aes",
        "v2_task_label": label,
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": road,
        "obstacle_timing_bucket": timing,
        "obstacle_lateral_bucket": lateral,
        "support_status": "unsupported_systematic",
        "missing_profile_count": 12,
        "reason": "unsupported_systematic",
        "recommended_next_action": "find_or_materialize_alternate_source_with_observed_label_support",
    }


def _source(
    *,
    bounded_id: str,
    labels: str,
    hidden: str,
    road: str,
    timing: str,
    lateral: str,
) -> dict[str, object]:
    return {
        "scenario_spec_id": bounded_id,
        "bounded_panel_spec_id": bounded_id,
        "source_scenario_spec_id": f"raw_{bounded_id}",
        "role_panel_id": "stable_avoidance_aes",
        "allowed_labels_metadata_only": labels,
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": road,
        "obstacle_timing_bucket": timing,
        "obstacle_lateral_bucket": lateral,
        "sampling_repair_variant_id": "synthetic",
    }


def _support(
    *,
    source: str,
    label: str,
    hidden: str,
    road: str,
    timing: str,
    lateral: str,
    status: str,
) -> dict[str, object]:
    return {
        "source_label_group_id": f"{source}|stable_avoidance_aes|{label}|{hidden}|{road}|{timing}|{lateral}",
        "source_scenario_spec_id": source,
        "v2_role_surface_id": "stable_avoidance_aes",
        "v2_task_label": label,
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": road,
        "obstacle_timing_bucket": timing,
        "obstacle_lateral_bucket": lateral,
        "profile_count": 12,
        "reset_success_count": 12 if status == "supported_observed" else 0,
        "sampling_failure_count": 0 if status == "supported_observed" else 12,
        "support_status": status,
    }


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    needs = [
        _need(source="target_exact", label="aes_feasible", hidden="nominal", road="nominal", timing="medium", lateral="center"),
        _need(source="target_untrusted", label="aes_feasible", hidden="friction_step", road="nominal", timing="late", lateral="center"),
        _need(source="target_near", label="aes_feasible", hidden="low_mu", road="wide", timing="close", lateral="center"),
        _need(source="target_new", label="aeb_feasible", hidden="brake_variation", road="moderate", timing="late", lateral="wide_offset"),
    ]
    sources = [
        _source(bounded_id="candidate_exact", labels="aes_feasible", hidden="nominal", road="nominal", timing="medium", lateral="center"),
        _source(bounded_id="candidate_untrusted", labels="aes_feasible", hidden="friction_step", road="nominal", timing="late", lateral="center"),
        _source(bounded_id="candidate_near", labels="aes_feasible", hidden="low_mu", road="moderate", timing="late", lateral="mild_offset"),
    ]
    support = [
        _support(source="candidate_exact", label="aes_feasible", hidden="nominal", road="nominal", timing="medium", lateral="center", status="supported_observed"),
        _support(source="candidate_untrusted", label="aes_feasible", hidden="friction_step", road="nominal", timing="late", lateral="center", status="unsupported_systematic"),
    ]
    needs_path = tmp_path / "needs.csv"
    support_path = tmp_path / "support.csv"
    sources_path = tmp_path / "sources.json"
    write_csv_rows(needs_path, needs)
    write_csv_rows(support_path, support)
    write_json(sources_path, {"bounded_panel_specs": sources})
    return needs_path, support_path, sources_path


def test_stable_source_label_topup_preflight_classifies_candidate_classes(tmp_path: Path) -> None:
    needs_path, support_path, sources_path = _write_fixture(tmp_path)

    summary = topup.run_executable_v2_stable_source_label_topup_preflight(
        replacement_needs_path=needs_path,
        source_label_support_path=support_path,
        bounded_panel_specs_path=sources_path,
        output_dir=tmp_path / "out",
        target_topup_count=4,
    )

    assert summary["result_class"] == "executable_v2_stable_source_label_topup_preflight_pass"
    assert summary["stable_topup_target_count"] == 4
    assert summary["target_missing_profile_count_total"] == 48
    assert summary["direct_replacement_count"] == 1
    assert summary["new_materialization_need_count"] == 3
    assert summary["candidate_class_counts"] == {
        "exact_existing_candidate": 1,
        "metadata_only_untrusted": 1,
        "near_existing_candidate": 1,
    }
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["measured_execution_admissible"] is False
    assert summary["controller_family_ranking_admissible"] is False

    candidates = (tmp_path / "out" / "stable_topup_candidate_rows.csv").read_text()
    assert "exact_existing_candidate" in candidates
    assert "metadata_only_untrusted" in candidates
    assert "near_existing_candidate" in candidates
    assert "candidate_exact" in candidates
    assert "candidate_untrusted" in candidates
    assert "candidate_near" in candidates
    new_needs = (tmp_path / "out" / "stable_new_materialization_need_rows.csv").read_text()
    assert "target_untrusted" in new_needs
    assert "target_near" in new_needs
    assert "target_new" in new_needs
    assert "target_exact" not in new_needs
    claim_boundary = (tmp_path / "out" / "stable_topup_claim_boundary.csv").read_text()
    assert "direct_replacement_without_reset_probe" in claim_boundary
    assert "False" in claim_boundary


def test_stable_source_label_topup_preflight_preserves_empty_candidates(tmp_path: Path) -> None:
    needs_path, support_path, sources_path = _write_fixture(tmp_path)
    write_json(sources_path, {"bounded_panel_specs": []})

    summary = topup.run_executable_v2_stable_source_label_topup_preflight(
        replacement_needs_path=needs_path,
        source_label_support_path=support_path,
        bounded_panel_specs_path=sources_path,
        output_dir=tmp_path / "out",
        target_topup_count=4,
    )

    assert summary["stable_candidate_source_count"] == 0
    assert summary["candidate_row_count"] == 0
    assert summary["new_materialization_need_count"] == 4
    targets = (tmp_path / "out" / "stable_topup_targets.csv").read_text()
    assert "target_new" in targets
