from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_calibrated_reset_validation_preflight as reset_preflight
from autodrift.artifacts import read_json, write_json


def _first_real_spec() -> dict[str, object]:
    payload = read_json("runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json")
    return dict(payload["executable_task_specs"][0])


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
    assert (output_dir / "reset_rows.csv").exists()
