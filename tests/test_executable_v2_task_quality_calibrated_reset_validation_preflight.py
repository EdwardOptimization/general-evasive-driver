from __future__ import annotations

from pathlib import Path

import pytest

from autodrift import executable_v2_task_quality_calibrated_reset_validation_preflight as reset_preflight
from autodrift.artifacts import read_json, write_json


def _first_real_spec() -> dict[str, object]:
    payload = read_json("runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json")
    return dict(payload["executable_task_specs"][0])


def _spec_with_metadata(
    *,
    task_source_id: str,
    repair_source_kind: str,
    source_role_semantics: str,
    normalized_surface_variant: str,
) -> dict[str, object]:
    spec = _first_real_spec()
    spec.update(
        {
            "task_source_id": task_source_id,
            "candidate_source_id": task_source_id,
            "repair_candidate_id": task_source_id,
            "repair_source_kind": repair_source_kind,
            "source_role_semantics": source_role_semantics,
            "normalized_surface_variant": normalized_surface_variant,
        }
    )
    return spec


def _install_successful_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_reset_task_quality_spec(
        *,
        spec: dict[str, object],
        eval_seed: int,
        expected_observation_dim: int | None,
    ) -> dict[str, object]:
        del eval_seed
        return {
            "task_source_id": str(spec["task_source_id"]),
            "reset_success": True,
            "error_type": "",
            "error_message": "",
            "observation_length": int(expected_observation_dim or 72),
            "expected_observation_length": int(expected_observation_dim or 72),
            "observation_dimension_matches": True,
            "observation_finite": True,
            "obstacle_initialized": True,
            "sampled_obstacle_label": str(spec.get("sampled_obstacle_label", "")),
            "initial_mu": "",
            "speed_ref": "",
            "obstacle_distance": "",
            "obstacle_half_width": "",
        }

    monkeypatch.setattr(reset_preflight, "reset_task_quality_spec", fake_reset_task_quality_spec)


def test_contract_row_preserves_calibrated_metadata() -> None:
    spec = _first_real_spec()

    row = reset_preflight.contract_row_for_spec(spec)

    assert row["repair_source_kind"] == spec["repair_source_kind"]
    assert row["selection_quota_name"] == spec["selection_quota_name"]
    assert row["normalized_surface_variant"] == spec["normalized_surface_variant"]
    assert row["contract_violation_count"] == 0


def test_run_calibrated_reset_validation_one_spec(tmp_path: Path) -> None:
    spec = _first_real_spec()
    specs_path = tmp_path / "specs.json"
    output_dir = tmp_path / "reset"
    write_json(
        specs_path,
        {
            "executable_task_specs": [spec],
        },
    )

    summary = reset_preflight.run_calibrated_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=196000,
        target_spec_count=1,
        expected_observation_dim=72,
    )

    assert summary["reset_attempt_count"] == 1
    assert summary["reset_success_count"] == 1
    assert summary["reset_failure_count"] == 0
    assert summary["contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["expected_quota_source"] == "executable_task_specs"
    assert summary["expected_source_kind_counts"] == summary["source_kind_counts"]
    assert summary["expected_role_surface_counts"] == summary["role_surface_counts"]
    assert summary["quota_metadata_missing_count"] == 0
    assert (output_dir / "reset_rows.csv").exists()


def test_artifact_driven_quota_accepts_repaired_distribution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_successful_reset(monkeypatch)
    specs = [
        _spec_with_metadata(
            task_source_id="anchor_0",
            repair_source_kind="anchor_neighborhood",
            source_role_semantics="stable_aeb",
            normalized_surface_variant="post_friction_step",
        ),
        _spec_with_metadata(
            task_source_id="anchor_1",
            repair_source_kind="anchor_neighborhood",
            source_role_semantics="stable_aeb",
            normalized_surface_variant="post_friction_step",
        ),
        _spec_with_metadata(
            task_source_id="offtrack_0",
            repair_source_kind="offtrack_boundary_relief",
            source_role_semantics="stable_aes_only",
            normalized_surface_variant="relief_surface_unspecified",
        ),
        _spec_with_metadata(
            task_source_id="mitigation_0",
            repair_source_kind="mitigation_isolation_check",
            source_role_semantics="unavoidable_mitigation",
            normalized_surface_variant="steady_surface",
        ),
    ]
    specs_path = tmp_path / "specs.json"
    output_dir = tmp_path / "reset"
    write_json(specs_path, {"executable_task_specs": specs})

    summary = reset_preflight.run_calibrated_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=199300,
        target_spec_count=4,
        expected_observation_dim=72,
    )

    assert summary["result_class"] == "task_quality_calibrated_reset_validation_preflight_pass"
    assert summary["source_kind_quota_pass"] is True
    assert summary["role_surface_quota_pass"] is True
    assert summary["expected_source_kind_counts"] == {
        "anchor_neighborhood": 2,
        "mitigation_isolation_check": 1,
        "offtrack_boundary_relief": 1,
    }
    assert summary["quota_metadata_missing_count"] == 0


def test_missing_quota_metadata_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_successful_reset(monkeypatch)
    spec = _spec_with_metadata(
        task_source_id="missing_role",
        repair_source_kind="anchor_neighborhood",
        source_role_semantics="",
        normalized_surface_variant="post_friction_step",
    )
    specs_path = tmp_path / "specs.json"
    output_dir = tmp_path / "reset"
    write_json(specs_path, {"executable_task_specs": [spec]})

    summary = reset_preflight.run_calibrated_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=199300,
        target_spec_count=1,
        expected_observation_dim=72,
    )

    assert summary["result_class"] == "task_quality_calibrated_reset_validation_preflight_fail"
    assert summary["reset_success_count"] == 1
    assert summary["source_kind_quota_pass"] is True
    assert summary["role_surface_quota_pass"] is True
    assert summary["quota_metadata_missing_count"] == 1
    assert (output_dir / "quota_metadata_missing_rows.csv").exists()
