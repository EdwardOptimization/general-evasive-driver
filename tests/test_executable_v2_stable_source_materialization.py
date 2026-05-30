from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import executable_v2_stable_source_materialization as materialization


def _need(
    *,
    target_id: str,
    source: str,
    label: str,
    hidden: str,
    road: str,
    timing: str,
    lateral: str,
) -> dict[str, object]:
    return {
        "topup_target_id": target_id,
        "source_scenario_spec_id": source,
        "v2_role_surface_id": "stable_avoidance_aes",
        "v2_task_label": label,
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": road,
        "obstacle_timing_bucket": timing,
        "obstacle_lateral_bucket": lateral,
        "missing_profile_count": 12,
        "candidate_count": 0,
        "requires_new_materialization": True,
        "reason": "no_observed_supported_direct_replacement",
    }


def _spec(
    *,
    bounded_id: str,
    labels: str,
    hidden: str,
    road: str,
    timing: str,
    lateral: str,
    require_aeb_infeasible: bool,
) -> dict[str, object]:
    return {
        "scenario_spec_id": bounded_id,
        "bounded_panel_spec_id": bounded_id,
        "source_scenario_spec_id": f"raw_{bounded_id}",
        "m1728_scenario_spec_id": f"raw_{bounded_id}",
        "role_panel_id": "stable_avoidance_aes",
        "role_panel_label": "Stable avoidance and AES",
        "allowed_labels_metadata_only": labels,
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": road,
        "obstacle_timing_bucket": timing,
        "obstacle_lateral_bucket": lateral,
        "sampling_repair_variant_id": "synthetic",
        "sampling_repair_source": "fixture",
        "labels_enter_actor_input": False,
        "ranking_eligible_after_audit": False,
        "diagnostic_only_no_ranking_claim": True,
        "env_config": {
            "obstacle": {
                "allowed_labels": labels.split(";"),
                "max_sample_attempts": 120,
                "require_aeb_infeasible": require_aeb_infeasible,
            }
        },
    }


def _candidate(
    *,
    target_id: str,
    candidate: str,
    candidate_class: str,
    status: str,
) -> dict[str, object]:
    return {
        "topup_target_id": target_id,
        "target_source_scenario_spec_id": "target",
        "target_v2_task_label": "aes_feasible",
        "candidate_bounded_panel_spec_id": candidate,
        "candidate_source_scenario_spec_id": f"raw_{candidate}",
        "candidate_class": candidate_class,
        "observed_reset_support_status": status,
    }


def _profile(name: str) -> dict[str, object]:
    return {
        "profile_name": name,
        "profile_config_path": f"configs/{name}.json",
        "checkpoint_path": f"checkpoints/{name}.pt",
        "config_exists": True,
        "checkpoint_exists": True,
        "evaluation_role": "benchmark",
        "primary_metric_family": "avoidance_success",
    }


def _write_fixture(tmp_path: Path, *, duplicate: bool = False) -> tuple[Path, Path, Path, Path]:
    needs = [
        _need(
            target_id="stable-topup-000",
            source="bp0",
            label="aes_feasible",
            hidden="nominal",
            road="nominal",
            timing="medium",
            lateral="center",
        ),
        _need(
            target_id="stable-topup-001",
            source="bp1",
            label="aes_feasible",
            hidden="friction_step",
            road="nominal",
            timing="late",
            lateral="center",
        ),
        _need(
            target_id="stable-topup-002",
            source="bp2",
            label="aeb_feasible",
            hidden="brake_variation",
            road="moderate",
            timing="late",
            lateral="wide_offset",
        ),
    ]
    if duplicate:
        needs.append(dict(needs[0], topup_target_id="stable-topup-003"))
    specs = [
        _spec(
            bounded_id="bp0",
            labels="aeb_feasible;aes_feasible",
            hidden="nominal",
            road="nominal",
            timing="medium",
            lateral="center",
            require_aeb_infeasible=False,
        ),
        _spec(
            bounded_id="bp1",
            labels="aeb_feasible;aes_feasible",
            hidden="friction_step",
            road="nominal",
            timing="late",
            lateral="center",
            require_aeb_infeasible=False,
        ),
        _spec(
            bounded_id="bp2",
            labels="aes_feasible",
            hidden="brake_variation",
            road="moderate",
            timing="late",
            lateral="wide_offset",
            require_aeb_infeasible=True,
        ),
    ]
    candidates = [
        _candidate(
            target_id="stable-topup-000",
            candidate="bp0",
            candidate_class="metadata_only_untrusted",
            status="unsupported_systematic",
        ),
        _candidate(
            target_id="stable-topup-000",
            candidate="near0",
            candidate_class="near_existing_candidate",
            status="unobserved",
        ),
    ]
    matrix = []
    for spec in specs:
        for profile in (_profile("L0"), _profile("L3")):
            matrix.append(
                {
                    "bounded_panel_spec_id": spec["bounded_panel_spec_id"],
                    "source_scenario_spec_id": spec["source_scenario_spec_id"],
                    **profile,
                }
            )
    needs_path = tmp_path / "needs.csv"
    candidates_path = tmp_path / "candidates.csv"
    specs_path = tmp_path / "specs.json"
    matrix_path = tmp_path / "matrix.csv"
    write_csv_rows(needs_path, needs)
    write_csv_rows(candidates_path, candidates)
    write_json(specs_path, {"bounded_panel_specs": specs})
    write_csv_rows(matrix_path, matrix)
    return needs_path, candidates_path, specs_path, matrix_path


def test_stable_source_materialization_writes_specs_and_matrix(tmp_path: Path) -> None:
    needs_path, candidates_path, specs_path, matrix_path = _write_fixture(tmp_path)

    summary = materialization.run_executable_v2_stable_source_materialization(
        new_materialization_needs_path=needs_path,
        topup_candidates_path=candidates_path,
        bounded_panel_specs_path=specs_path,
        bounded_panel_matrix_path=matrix_path,
        output_dir=tmp_path / "out",
        target_materialization_count=3,
        target_profile_count=2,
        id_prefix="test",
    )

    assert summary["result_class"] == "executable_v2_stable_source_materialization_pass"
    assert summary["stable_materialization_spec_count"] == 3
    assert summary["stable_materialization_matrix_row_count"] == 6
    assert summary["profile_control_count"] == 2
    assert summary["duplicate_key_count"] == 0
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["reset_validation_required_count"] == 3
    assert summary["measured_execution_admissible_count"] == 0
    assert summary["controller_family_ranking_admissible_count"] == 0

    specs = read_json(tmp_path / "out" / "stable_source_materialization_specs.json")[
        "stable_source_materialization_specs"
    ]
    assert [row["materialized_source_scenario_spec_id"] for row in specs] == [
        "test-stable-src-000",
        "test-stable-src-001",
        "test-stable-src-002",
    ]
    assert specs[0]["env_config"]["obstacle"]["allowed_labels"] == ["aes_feasible"]
    assert specs[0]["env_config"]["obstacle"]["require_aeb_infeasible"] is True
    assert specs[2]["env_config"]["obstacle"]["allowed_labels"] == ["aeb_feasible"]
    assert specs[2]["env_config"]["obstacle"]["require_aeb_infeasible"] is False
    assert specs[0]["source_basis_support_status"] == "unsupported_systematic"
    assert specs[0]["near_candidate_ids"] == "near0"

    matrix = (tmp_path / "out" / "stable_source_materialization_matrix.csv").read_text()
    assert "test-stable-bp-000::L0" in matrix
    assert "test-stable-bp-002::L3" in matrix
    claim_boundary = (tmp_path / "out" / "stable_source_materialization_claim_boundary.csv").read_text()
    assert "reset_feasibility_repaired,False" in claim_boundary


def test_stable_source_materialization_rejects_duplicate_keys(tmp_path: Path) -> None:
    needs_path, candidates_path, specs_path, matrix_path = _write_fixture(tmp_path, duplicate=True)

    summary = materialization.run_executable_v2_stable_source_materialization(
        new_materialization_needs_path=needs_path,
        topup_candidates_path=candidates_path,
        bounded_panel_specs_path=specs_path,
        bounded_panel_matrix_path=matrix_path,
        output_dir=tmp_path / "out",
        target_profile_count=2,
        id_prefix="test",
    )

    assert summary["result_class"] == "executable_v2_stable_source_materialization_fail"
    assert summary["duplicate_key_count"] == 1
    duplicates = (tmp_path / "out" / "stable_source_materialization_duplicate_keys.csv").read_text()
    assert "stable-topup-000;stable-topup-003" in duplicates
