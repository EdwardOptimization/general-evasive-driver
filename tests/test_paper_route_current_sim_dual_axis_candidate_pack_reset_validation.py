from __future__ import annotations

from pathlib import Path

import pytest

from autodrift import paper_route_current_sim_dual_axis_candidate_pack_reset_validation as reset_validation
from autodrift.artifacts import read_json, write_json


def _first_pack_spec() -> dict[str, object]:
    payload = read_json(
        "runs/m2350_paper_route_current_sim_dual_axis_candidate_config_materialization/config_packs/"
        "baseline_reference_pack.json"
    )
    return dict(payload["scenario_specs"][0])


def _write_pack(path: Path, *, pack_id: str, specs: list[dict[str, object]]) -> None:
    write_json(
        path,
        {
            "config_pack_id": pack_id,
            "scenario_specs": specs,
        },
    )


def _write_patch_rows(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "pack_id,scenario_spec_id,candidate_id,patch_resolution,hidden_dynamics_bucket_before,"
                "hidden_dynamics_bucket_after,timing_bucket_before,timing_bucket_after,lateral_bucket_before,"
                "lateral_bucket_after,env_config_patch_applied,metadata_only_patch,diagnostic_only,"
                "ranking_admissible,winner_selected,paper_level_claim_made,level3_self_id_claim_made,"
                "scenario_redesign_executed",
                "pack_a,spec_a,cand_a,mixed_env_and_metadata,low_mu,nominal_neighbor,mid,mid,"
                "centerline,centerline,True,True,True,False,False,False,False,False",
                "",
            ]
        ),
        encoding="utf-8",
    )


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

    monkeypatch.setattr(reset_validation, "reset_task_quality_spec", fake_reset_task_quality_spec)


def test_load_config_pack_manifest_preserves_pack_shape() -> None:
    packs = reset_validation.load_config_packs()

    assert len(packs) == 5
    assert [pack["pack_id"] for pack in packs] == [
        "baseline_reference_pack",
        "g_primary_pack",
        "h_primary_pack",
        "g_h_primary_pack",
        "gh_minimal_pack",
    ]
    assert {len(pack["scenario_specs"]) for pack in packs} == {72}


def test_contract_row_uses_scenario_spec_id() -> None:
    spec = _first_pack_spec()

    row = reset_validation.contract_row_for_pack_spec(
        pack_id="pack_a",
        scenario_index=0,
        spec=spec,
    )

    assert row["scenario_spec_id"] == spec["scenario_spec_id"]
    assert row["contract_violation_count"] == 0
    assert row["obstacle_relative_velocity_mode_zero"] is True


def test_run_candidate_pack_reset_validation_small_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_successful_reset(monkeypatch)
    spec = _first_pack_spec()
    pack_a = tmp_path / "pack_a.json"
    pack_b = tmp_path / "pack_b.json"
    _write_pack(pack_a, pack_id="pack_a", specs=[spec])
    _write_pack(pack_b, pack_id="pack_b", specs=[spec])
    manifest_path = tmp_path / "manifest.json"
    write_json(
        manifest_path,
        {
            "packs": [
                {
                    "pack_id": "pack_a",
                    "pack_path": str(pack_a),
                    "selection_count": 1,
                },
                {
                    "pack_id": "pack_b",
                    "pack_path": str(pack_b),
                    "selection_count": 0,
                },
            ]
        },
    )
    patch_rows = tmp_path / "patch_rows.csv"
    _write_patch_rows(patch_rows)
    output_dir = tmp_path / "reset"

    summary = reset_validation.run_candidate_pack_reset_validation(
        config_pack_manifest_path=manifest_path,
        patch_rows_path=patch_rows,
        output_dir=output_dir,
        eval_seed_base=235300,
        target_pack_count=2,
        target_scenario_specs_per_pack=1,
        expected_observation_dim=72,
    )

    assert summary["result_class"] == reset_validation.RESULT_FAIL
    assert summary["reset_attempt_count"] == 2
    assert summary["reset_success_count"] == 2
    assert summary["contract_violation_count"] == 0
    assert summary["metadata_only_patch_count"] == 1
    assert summary["metadata_caveat_rows_preserved"] is False
    assert (output_dir / "reset_rows.csv").exists()
    assert (output_dir / "metadata_caveat_rows.csv").exists()


def test_full_m2350_metadata_caveat_counts() -> None:
    rows = reset_validation._metadata_caveat_rows(reset_validation.DEFAULT_PATCH_ROWS)

    assert len(rows) == 78
    assert reset_validation._patch_count(rows, "metadata_only_patch") == 37
    assert reset_validation._unresolved_patch_count(rows) == 0
