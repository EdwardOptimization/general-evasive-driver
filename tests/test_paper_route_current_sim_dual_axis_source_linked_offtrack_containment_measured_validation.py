from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pytest

from autodrift import (
    paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation as runner,
)
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _env_config(label: str = "aeb_feasible") -> dict[str, Any]:
    return {
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "speed_range": [8.0, 8.0],
        "track_radius": 80.0,
        "track_width": 6.0,
        "obstacle": {"allowed_labels": [label]},
    }


def _scenario(
    pack_id: str,
    spec_id: str,
    *,
    role: str = "R0_stable_avoidable",
    label: str = "aeb_feasible",
) -> dict[str, Any]:
    return {
        "pack_id": pack_id,
        "pack_path": f"packs/{pack_id}.json",
        "scenario_spec_id": spec_id,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "role_family": role,
        "sampled_obstacle_label": label,
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "actor_contract_id": runner.ACTOR_CONTRACT_ID,
        "actor_contract_guardrail_pass": True,
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "history_length": 1,
        "env_config": _env_config(label),
    }


def _write_effective_candidate(
    source_dir: Path,
    rows: list[dict[str, Any]],
    *,
    candidate_id: str,
    specs: list[dict[str, Any]],
) -> None:
    config_path = source_dir / "effective_candidate_configs" / f"{candidate_id}.json"
    write_json(
        config_path,
        {
            "candidate_id": candidate_id,
            "priority_tier": "P0",
            "repair_family": "offtrack_containment_repair",
            "selected_scenario_specs": specs,
        },
    )
    rows.append(
        {
            "candidate_id": candidate_id,
            "source_repair_spec_id": f"repair_{candidate_id}",
            "repair_family": "offtrack_containment_repair",
            "source_slice_axis": "role_family",
            "source_slice_value": "R0_stable_avoidable",
            "source_candidate_config_path": str(source_dir / "source" / f"{candidate_id}.json"),
            "effective_candidate_config_path": str(config_path),
            "selected_scenario_count": len(specs),
            "selected_base_pack_count": len({spec["pack_id"] for spec in specs}),
        }
    )


def _reset_row(
    spec: Mapping[str, Any],
    *,
    family_ids: str,
    effective_candidate_ids: str,
    scenario_reference_count: int,
) -> dict[str, Any]:
    env_config = spec["env_config"]
    reset_target_key = runner._reset_target_key(str(spec["pack_id"]), str(spec["scenario_spec_id"]), env_config)
    return {
        "reset_target_key": reset_target_key,
        "env_config_hash": runner._json_hash(env_config)[:16],
        "pack_id": spec["pack_id"],
        "scenario_spec_id": spec["scenario_spec_id"],
        "family_ids": family_ids,
        "effective_candidate_ids": effective_candidate_ids,
        "scenario_reference_count": scenario_reference_count,
    }


def _write_inputs(tmp_path: Path, *, ranking_flag: bool = False) -> tuple[Path, Path, Path]:
    source_effective_dir = tmp_path / "effective"
    (source_effective_dir / "effective_candidate_configs").mkdir(parents=True)
    candidate_rows: list[dict[str, Any]] = []

    spec_a = _scenario("baseline_reference_pack", "spec_a")
    spec_b = _scenario("g_primary_pack", "spec_b", role="R1_aeb_infeasible_stable_aes", label="aes_feasible")
    _write_effective_candidate(
        source_effective_dir,
        candidate_rows,
        candidate_id="candidate_a",
        specs=[spec_a, spec_b],
    )
    _write_effective_candidate(
        source_effective_dir,
        candidate_rows,
        candidate_id="candidate_b",
        specs=[spec_a],
    )
    write_csv_rows(source_effective_dir / "effective_candidate_config_rows.csv", candidate_rows)

    source_reset_dir = tmp_path / "reset"
    write_json(source_reset_dir / "summary.json", {"result_class": "source_linked_reset_evidence_pass"})
    write_csv_rows(
        source_reset_dir / "reset_target_rows.csv",
        [
            _reset_row(
                spec_a,
                family_ids="c01_geometry_timing_containment|c02_hidden_dynamics_response_containment",
                effective_candidate_ids="candidate_a|candidate_b",
                scenario_reference_count=3,
            ),
            _reset_row(
                spec_b,
                family_ids="c03_general_offtrack_boundary_containment",
                effective_candidate_ids="candidate_a",
                scenario_reference_count=1,
            ),
        ],
    )

    config_root = tmp_path / "configs"
    selected_rows: list[dict[str, Any]] = []
    for profile, seed in (("L0_current_masked", 101), ("L3_online_gru", 102)):
        write_json(
            config_root / profile / f"seed_{seed}" / "config.json",
            {
                "env": {"history_length": 1, "action_history_mode": "full"},
                "controller_profile": {
                    "name": profile,
                    "observation_mask": "none",
                    "previous_command_mask_indices": [],
                    "history_transform": "none",
                    "reset_hidden_policy": "episode_persistent",
                },
            },
        )
        selected_rows.append(
            {
                "matrix_id": f"{profile}::seed_{seed}",
                "profile_name": profile,
                "seed_id": seed,
                "selected_checkpoint_path": str(tmp_path / "checkpoints" / profile / f"seed_{seed}" / "checkpoint.pt"),
                "selected_checkpoint_step": 2048,
                "selected_checkpoint_kind": "periodic",
                "selected_readiness_floor_pass": False,
                "diagnostic_only": True,
                "ranking_admissible": ranking_flag,
                "winner_selected": False,
            }
        )
    selected_path = tmp_path / "selected_checkpoint_rows.csv"
    write_csv_rows(selected_path, selected_rows)
    return source_reset_dir, source_effective_dir, selected_path


def _fake_rollout(workload_row: Mapping[str, Any], reset_target_spec: Mapping[str, Any], eval_seed: int) -> dict[str, Any]:
    return {
        "seed": eval_seed,
        "policy": "checkpoint",
        "steps": 40,
        "terminated": True,
        "truncated": False,
        "collision": False,
        "obstacle_completed": True,
        "termination_reason": "obstacle_completed",
        "outcome_bucket": "success_obstacle_pass",
        "return": 12.0,
        "min_clearance_margin": 0.42,
        "max_off_track_overshoot": 0.0,
        "time_to_first_off_track_s": 0.0,
        "high_sideslip_fraction": 0.0,
        "action_rate_mean": 0.05,
        "obstacle_label": reset_target_spec["sampled_obstacle_label"],
        "workload_marker": workload_row["workload_id"],
    }


def test_source_linked_measured_validation_preserves_reset_and_family_metadata(tmp_path: Path) -> None:
    source_reset_dir, source_effective_dir, selected_path = _write_inputs(tmp_path)

    summary = runner.run_source_linked_offtrack_containment_measured_validation(
        source_reset_dir=source_reset_dir,
        source_effective_dir=source_effective_dir,
        selected_rows_path=selected_path,
        config_root=tmp_path / "configs",
        output_dir=tmp_path / "out",
        eval_seed_base=900,
        target_reset_target_count=2,
        target_selected_checkpoint_count=2,
        target_episode_count=4,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["episode_count"] == 4
    assert summary["source_reset_target_count"] == 2
    assert summary["selected_checkpoint_count"] == 2
    assert summary["failure_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["metric_completeness_failure_count"] == 0
    assert summary["actor_contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["family_membership_row_count"] == 6
    assert summary["family_membership_counts"] == {
        "c01_geometry_timing_containment": 2,
        "c02_hidden_dynamics_response_containment": 2,
        "c03_general_offtrack_boundary_containment": 2,
    }

    episode_rows = runner.read_csv_rows(tmp_path / "out" / "episode_rows.csv")
    assert [int(row["eval_seed"]) for row in episode_rows] == [900, 901, 100900, 100901]
    assert {row["source_linked_measured_validation"] for row in episode_rows} == {"True"}
    assert {row["candidate_family_ranking_claim_made"] for row in episode_rows} == {"False"}
    membership_rows = runner.read_csv_rows(tmp_path / "out" / "episode_family_membership_rows.csv")
    assert len(membership_rows) == 6
    assert (tmp_path / "out" / "aggregate_by_reset_target.csv").exists()
    assert (tmp_path / "out" / "aggregate_by_family_membership.csv").exists()
    assert (tmp_path / "out" / "aggregate_by_family_profile.csv").exists()
    assert (tmp_path / "out" / "aggregate_by_family_pack.csv").exists()


def test_source_linked_measured_validation_fails_closed_on_contract_gap(tmp_path: Path) -> None:
    source_reset_dir, source_effective_dir, selected_path = _write_inputs(tmp_path)
    payload = read_json(source_effective_dir / "effective_candidate_configs" / "candidate_a.json")
    payload["selected_scenario_specs"][0]["actor_contract_id"] = "P0_bad_contract"
    payload_b = read_json(source_effective_dir / "effective_candidate_configs" / "candidate_b.json")
    payload_b["selected_scenario_specs"][0]["actor_contract_id"] = "P0_bad_contract"
    write_json(source_effective_dir / "effective_candidate_configs" / "candidate_a.json", payload)
    write_json(source_effective_dir / "effective_candidate_configs" / "candidate_b.json", payload_b)

    summary = runner.run_source_linked_offtrack_containment_measured_validation(
        source_reset_dir=source_reset_dir,
        source_effective_dir=source_effective_dir,
        selected_rows_path=selected_path,
        config_root=tmp_path / "configs",
        output_dir=tmp_path / "out",
        eval_seed_base=900,
        target_reset_target_count=2,
        target_selected_checkpoint_count=2,
        target_episode_count=4,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["episode_count"] == 0
    assert summary["validation_failure_count"] > 0
    assert summary["actor_contract_violation_count"] > 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "actor_contract_id" in validation_rows


def test_source_linked_measured_validation_fails_closed_on_ranking_flag(tmp_path: Path) -> None:
    source_reset_dir, source_effective_dir, selected_path = _write_inputs(tmp_path, ranking_flag=True)

    summary = runner.run_source_linked_offtrack_containment_measured_validation(
        source_reset_dir=source_reset_dir,
        source_effective_dir=source_effective_dir,
        selected_rows_path=selected_path,
        config_root=tmp_path / "configs",
        output_dir=tmp_path / "out",
        eval_seed_base=900,
        target_reset_target_count=2,
        target_selected_checkpoint_count=2,
        target_episode_count=4,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["episode_count"] == 0
    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "guardrail_violation" in validation_rows
    assert "selected_row_ranking" in validation_rows


def test_source_linked_measured_validation_fails_closed_on_unmatched_reset_target(tmp_path: Path) -> None:
    source_reset_dir, source_effective_dir, _selected_path = _write_inputs(tmp_path)
    reset_rows = runner.read_csv_rows(source_reset_dir / "reset_target_rows.csv")
    reset_rows[0]["reset_target_key"] = "missing_pack|missing_spec|0000000000000000"
    write_csv_rows(source_reset_dir / "reset_target_rows.csv", reset_rows)

    with pytest.raises(ValueError, match="missing env_config for reset target"):
        runner.load_source_linked_reset_target_specs(
            source_reset_dir=source_reset_dir,
            source_effective_dir=source_effective_dir,
        )
