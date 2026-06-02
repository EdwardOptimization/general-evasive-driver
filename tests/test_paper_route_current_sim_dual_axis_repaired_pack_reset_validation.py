from __future__ import annotations

from pathlib import Path

import pytest

from autodrift import paper_route_current_sim_dual_axis_repaired_pack_reset_validation as reset_validation
from autodrift.artifacts import read_json, write_json


def _first_repaired_spec() -> dict[str, object]:
    payload = read_json(
        "runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/config_packs/"
        "g_primary_pack.json"
    )
    for spec in payload["scenario_specs"]:
        if spec.get("sampling_repair_applied"):
            return dict(spec)
    raise AssertionError("fixture pack must contain at least one repaired scenario spec")


def _write_pack(path: Path, *, pack_id: str, specs: list[dict[str, object]]) -> None:
    write_json(
        path,
        {
            "config_pack_id": pack_id,
            "scenario_specs": specs,
        },
    )


def _write_csv(path: Path, header: str, row: str) -> None:
    path.write_text("\n".join([header, row, ""]), encoding="utf-8")


def _install_successful_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_reset_task_quality_spec(
        *,
        spec: dict[str, object],
        eval_seed: int,
        expected_observation_dim: int | None,
    ) -> dict[str, object]:
        del spec
        return {
            "eval_seed": int(eval_seed),
            "reset_success": True,
            "error_type": "",
            "error_message": "",
            "observation_length": int(expected_observation_dim or 72),
            "expected_observation_length": int(expected_observation_dim or 72),
            "observation_dimension_matches": True,
            "observation_finite": True,
            "obstacle_initialized": True,
            "sampled_obstacle_label": "aeb_feasible",
            "initial_mu": "",
            "speed_ref": "",
            "obstacle_distance": "",
            "obstacle_half_width": "",
            "environment_reset_started": True,
            "environment_rollout_started": False,
            "policy_action_executed": False,
            "measured_rollout_started": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
            "promoted": False,
            "private_holdout_used": False,
            "actor_input_contract_changed": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }

    monkeypatch.setattr(
        reset_validation.candidate_reset,
        "reset_task_quality_spec",
        fake_reset_task_quality_spec,
    )


def test_load_repaired_config_packs_preserves_pack_shape() -> None:
    packs = reset_validation.load_repaired_config_packs()

    assert len(packs) == 5
    assert [pack["pack_id"] for pack in packs] == [
        "baseline_reference_pack",
        "g_primary_pack",
        "h_primary_pack",
        "g_h_primary_pack",
        "gh_minimal_pack",
    ]
    assert {len(pack["scenario_specs"]) for pack in packs} == {72}
    assert sum(int(pack.get("sampling_repair_fallback_count", 0)) for pack in packs) == 32


def test_full_m2356_repair_metadata_counts() -> None:
    repair_rows = reset_validation._read_csv_rows(reset_validation.DEFAULT_REPAIR_ACTION_ROWS)
    patch_rows = reset_validation._read_csv_rows(reset_validation.DEFAULT_REPAIRED_PATCH_ROWS)
    effective_rows = reset_validation._read_csv_rows(reset_validation.DEFAULT_EFFECTIVE_PACK_SUMMARY_ROWS)

    assert len(repair_rows) == 32
    assert reset_validation._count_by(repair_rows, "repair_class") == {
        "hidden_only": 3,
        "lateral_hidden": 2,
        "timing_related": 27,
    }
    assert len(patch_rows) == 78
    assert reset_validation._patch_count(patch_rows, "metadata_only_patch") == 37
    assert reset_validation._metadata_caveat_rows_preserved(
        repaired_patch_rows=patch_rows,
        expected_metadata_row_count=78,
        expected_metadata_only_patch_count=37,
    )
    assert reset_validation._effective_selection_summary(effective_rows)["g_h_primary_pack"][
        "effective_selection_count"
    ] == 16


def test_run_repaired_pack_reset_validation_small_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_successful_reset(monkeypatch)
    spec = _first_repaired_spec()
    pack_path = tmp_path / "pack.json"
    _write_pack(pack_path, pack_id="pack_a", specs=[spec])
    manifest_path = tmp_path / "manifest.json"
    write_json(
        manifest_path,
        {
            "packs": [
                {
                    "pack_id": "pack_a",
                    "pack_path": str(pack_path),
                    "selection_count": 1,
                    "sampling_repair_fallback_count": 1,
                    "effective_selection_count": 0,
                }
            ]
        },
    )
    scenario_spec_id = str(spec["scenario_spec_id"])
    repair_rows_path = tmp_path / "repair_action_rows.csv"
    _write_csv(
        repair_rows_path,
        "pack_id,scenario_spec_id,repair_action,repair_class,candidate_id",
        f"pack_a,{scenario_spec_id},baseline_env_config_fallback,"
        f"{spec['sampling_repair_class']},{spec['sampling_repair_source_candidate_id']}",
    )
    patch_rows_path = tmp_path / "patch_rows.csv"
    _write_csv(
        patch_rows_path,
        "pack_id,scenario_spec_id,patch_resolution,env_config_patch_applied,metadata_only_patch,"
        "sampling_repair_applied,sampling_repair_action",
        f"pack_a,{scenario_spec_id},env_config_patch,True,False,True,baseline_env_config_fallback",
    )
    effective_rows_path = tmp_path / "effective_rows.csv"
    _write_csv(
        effective_rows_path,
        "pack_id,scenario_spec_count,original_selection_count,baseline_env_config_fallback_count,"
        "effective_selection_count,timing_related_repair_count,hidden_only_repair_count,"
        "lateral_hidden_repair_count",
        "pack_a,1,1,1,0,1,0,0",
    )
    output_dir = tmp_path / "reset"

    summary = reset_validation.run_repaired_pack_reset_validation(
        repaired_config_pack_manifest_path=manifest_path,
        repair_action_rows_path=repair_rows_path,
        repaired_patch_rows_path=patch_rows_path,
        effective_pack_summary_rows_path=effective_rows_path,
        output_dir=output_dir,
        eval_seed_base=235900,
        target_pack_count=1,
        target_scenario_specs_per_pack=1,
        expected_observation_dim=72,
        expected_baseline_fallback_count=1,
        expected_metadata_row_count=1,
        expected_metadata_only_patch_count=0,
    )

    assert summary["result_class"] == reset_validation.RESULT_PASS
    assert summary["reset_attempt_count"] == 1
    assert summary["reset_success_count"] == 1
    assert summary["contract_violation_count"] == 0
    assert summary["baseline_env_config_fallback_count"] == 1
    assert summary["repair_action_rows_preserved"] is True
    assert summary["metadata_caveat_rows_preserved"] is True
    assert (output_dir / "reset_rows.csv").exists()
    assert (output_dir / "repair_action_reset_rows.csv").exists()
