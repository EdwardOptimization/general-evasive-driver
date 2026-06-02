from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence as runner


def _env_config() -> dict[str, object]:
    return {
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "history_length": 1,
    }


def _write_sources(root: Path, *, matching: bool = True) -> tuple[Path, Path]:
    overlay_dir = root / "overlay"
    effective_dir = root / "effective"
    overlay_dir.mkdir(parents=True)
    effective_dir.mkdir(parents=True)
    write_json(
        overlay_dir / "summary.json",
        {"result_class": "current_sim_dual_axis_offtrack_containment_repair_candidate_materialization_pass"},
    )
    overlay_path = overlay_dir / "repair_candidate_overlays" / "c01.json"
    source_key = "hidden_dynamics_bucket:low_mu" if matching else "hidden_dynamics_bucket:missing"
    write_json(
        overlay_path,
        {
            "candidate_id": "c01",
            "candidate_family": "hidden_dynamics_response_containment",
            "source_row_keys": [source_key],
            "ranking_admissible": False,
            "winner_selected": False,
            "repair_execution_allowed": False,
            "training_allowed": False,
        },
    )
    write_csv_rows(
        overlay_dir / "repair_candidate_overlays.csv",
        [
            {
                "candidate_id": "c01",
                "candidate_family": "hidden_dynamics_response_containment",
                "overlay_path": str(overlay_path),
            }
        ],
        fieldnames=["candidate_id", "candidate_family", "overlay_path"],
    )
    write_json(
        effective_dir / "summary.json",
        {"result_class": "current_sim_dual_axis_effective_config_schema_repair_materialization_pass"},
    )
    effective_path = effective_dir / "effective_candidate_configs" / "e01.json"
    write_json(
        effective_path,
        {
            "candidate_id": "e01",
            "claim_boundary": {
                "active_config_overwritten": False,
                "environment_step_count": 0,
                "policy_action_executed": False,
                "rollout_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            },
            "selected_scenario_specs": [
                {
                    "actor_contract_id": runner.ACTOR_CONTRACT_ID,
                    "env_config": _env_config(),
                    "pack_id": "pack_a",
                    "scenario_spec_id": "spec_0",
                    "scenario_family_id": "R5",
                    "role_family": "R5_hidden_dynamics_robustness",
                }
            ],
        },
    )
    write_csv_rows(
        effective_dir / "effective_candidate_config_rows.csv",
        [
            {
                "candidate_id": "e01",
                "source_slice_axis": "hidden_dynamics_bucket",
                "source_slice_value": "low_mu",
                "effective_candidate_config_path": str(effective_path),
            }
        ],
        fieldnames=["candidate_id", "source_slice_axis", "source_slice_value", "effective_candidate_config_path"],
    )
    return overlay_dir, effective_dir


def test_source_linked_reset_evidence_passes_with_matched_family(
    tmp_path: Path, monkeypatch
) -> None:
    overlay_dir, effective_dir = _write_sources(tmp_path)

    def fake_reset_target(*, target_row, env_config, eval_seed):  # noqa: ANN001
        return {
            "reset_target_key": target_row["reset_target_key"],
            "environment_load_attempted": True,
            "environment_reset_attempted": True,
            "environment_reset_success": True,
            "observation_length": 72,
            "observation_finite": True,
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": "",
        }

    monkeypatch.setattr(runner, "reset_target", fake_reset_target)
    summary = runner.run_source_linked_offtrack_containment_reset_evidence(
        source_overlay_dir=overlay_dir,
        source_effective_dir=effective_dir,
        output_dir=tmp_path / "out",
        target_family_count=1,
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["matched_family_count"] == 1
    assert summary["source_linked_scenario_reference_count"] == 1
    assert summary["unique_reset_target_count"] == 1
    assert summary["environment_reset_success_count"] == 1
    assert summary["environment_step_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == runner.RESULT_PASS


def test_source_linked_reset_evidence_fails_closed_on_unmatched_family(tmp_path: Path) -> None:
    overlay_dir, effective_dir = _write_sources(tmp_path, matching=False)
    summary = runner.run_source_linked_offtrack_containment_reset_evidence(
        source_overlay_dir=overlay_dir,
        source_effective_dir=effective_dir,
        output_dir=tmp_path / "out",
        target_family_count=1,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["matched_family_count"] == 0
    assert summary["family_without_match_count"] == 1
    assert summary["source_linked_scenario_reference_count"] == 0
    assert "family_source_link_failure" in summary["failure_types_observed"]
