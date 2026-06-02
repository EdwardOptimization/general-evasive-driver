from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_current_sim_dual_axis_candidate_pack_sampling_repair import (
    RESULT_PASS,
    run_candidate_pack_sampling_repair_materialization,
)


def test_sampling_repair_materializer_repairs_m2353_failures(tmp_path: Path) -> None:
    output_dir = tmp_path / "repair"

    summary = run_candidate_pack_sampling_repair_materialization(output_dir=output_dir)

    assert summary["result_class"] == RESULT_PASS
    assert summary["output_config_pack_count"] == 5
    assert summary["scenario_specs_per_pack_count"] == 72
    assert summary["input_reset_failure_count"] == 32
    assert summary["baseline_env_config_fallback_count"] == 32
    assert summary["timing_related_repair_count"] == 27
    assert summary["hidden_only_repair_count"] == 3
    assert summary["lateral_hidden_repair_count"] == 2
    assert summary["repair_missing_field_count"] == 0
    assert summary["metadata_caveat_rows_preserved"] is True
    assert summary["environment_reset_started"] is False
    assert summary["guardrail_violation_count"] == 0

    manifest = read_json(output_dir / "repaired_config_pack_manifest.json")
    assert manifest["config_pack_count"] == 5
    repaired_g = read_json(output_dir / "config_packs" / "g_primary_pack.json")
    repaired_spec = next(spec for spec in repaired_g["scenario_specs"] if spec["scenario_spec_id"] == "m2277_r2_02")
    baseline = read_json(
        "runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/"
        "baseline_reference_pack.json"
    )
    baseline_spec = next(spec for spec in baseline["scenario_specs"] if spec["scenario_spec_id"] == "m2277_r2_02")
    assert repaired_spec["sampling_repair_applied"] is True
    assert repaired_spec["env_config"] == baseline_spec["env_config"]


def test_sampling_repair_preserves_unfailed_modified_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "repair"

    run_candidate_pack_sampling_repair_materialization(output_dir=output_dir)

    repaired_g = read_json(output_dir / "config_packs" / "g_primary_pack.json")
    original_g = read_json(
        "runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/"
        "g_primary_pack.json"
    )
    repaired_spec = next(spec for spec in repaired_g["scenario_specs"] if spec["scenario_spec_id"] == "m2277_r2_06")
    original_spec = next(spec for spec in original_g["scenario_specs"] if spec["scenario_spec_id"] == "m2277_r2_06")
    assert repaired_spec["sampling_repair_applied"] is False
    assert repaired_spec["env_config"] == original_spec["env_config"]
