from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from autodrift import paper_route_current_sim_dual_axis_effective_candidate_measured_validation as runner
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
    candidate_id: str,
    pack_id: str,
    spec_id: str,
    *,
    role: str = "R0_stable_avoidable",
    label: str = "aeb_feasible",
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "pack_id": pack_id,
        "pack_path": f"packs/{pack_id}.json",
        "scenario_spec_id": spec_id,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "role_family": role,
        "sampled_obstacle_label": label,
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "actor_contract_guardrail_pass": True,
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "history_length": 1,
        "env_config": _env_config(label),
    }


def _write_candidate(
    source_dir: Path,
    rows: list[dict[str, Any]],
    *,
    candidate_id: str,
    source_repair_spec_id: str,
    repair_family: str,
    source_slice_axis: str,
    source_slice_value: str,
    specs: list[dict[str, Any]],
) -> None:
    config_path = source_dir / "effective_candidate_configs" / f"{candidate_id}.json"
    write_json(
        config_path,
        {
            "candidate_id": candidate_id,
            "priority_tier": "P0",
            "repair_family": repair_family,
            "selected_scenario_specs": specs,
        },
    )
    rows.append(
        {
            "candidate_id": candidate_id,
            "source_repair_spec_id": source_repair_spec_id,
            "repair_family": repair_family,
            "source_slice_axis": source_slice_axis,
            "source_slice_value": source_slice_value,
            "source_candidate_config_path": str(source_dir / "source" / f"{candidate_id}.json"),
            "effective_candidate_config_path": str(config_path),
            "selected_scenario_count": len(specs),
            "selected_base_pack_count": len({spec["pack_id"] for spec in specs}),
        }
    )


def _write_inputs(tmp_path: Path, *, ranking_flag: bool = False) -> tuple[Path, Path, Path]:
    source_dir = tmp_path / "source"
    configs_dir = source_dir / "effective_candidate_configs"
    configs_dir.mkdir(parents=True)
    candidate_rows: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []

    cand_a = "candidate_a"
    cand_b = "candidate_b"
    specs_a = [
        _scenario(cand_a, "baseline_reference_pack", "spec_a"),
        _scenario(cand_a, "g_primary_pack", "spec_b", role="R1_aeb_infeasible_stable_aes", label="aes_feasible"),
    ]
    specs_b = [_scenario(cand_b, "baseline_reference_pack", "spec_a")]
    _write_candidate(
        source_dir,
        candidate_rows,
        candidate_id=cand_a,
        source_repair_spec_id="repair_a",
        repair_family="offtrack_containment_repair",
        source_slice_axis="role_family",
        source_slice_value="R0_stable_avoidable",
        specs=specs_a,
    )
    _write_candidate(
        source_dir,
        candidate_rows,
        candidate_id=cand_b,
        source_repair_spec_id="repair_b",
        repair_family="collision_guardrail_repair",
        source_slice_axis="sampled_obstacle_label",
        source_slice_value="aeb_feasible",
        specs=specs_b,
    )
    for spec in [*specs_a, *specs_b]:
        scenario_rows.append(
            {
                "candidate_id": spec["candidate_id"],
                "pack_id": spec["pack_id"],
                "pack_path": spec["pack_path"],
                "scenario_spec_id": spec["scenario_spec_id"],
                "scenario_family_id": spec["scenario_family_id"],
                "role_family": spec["role_family"],
                "source_slice_axis": "role_family",
                "source_slice_value": "R0_stable_avoidable",
                "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
                "include_privileged_params": False,
                "wheel_observation_mode": "none",
                "obstacle_relative_velocity_mode": "zero",
                "history_length": 1,
                "env_config_present": True,
                "actor_contract_guardrail_pass": True,
            }
        )
    write_csv_rows(source_dir / "effective_candidate_config_rows.csv", candidate_rows)
    write_csv_rows(source_dir / "effective_candidate_scenario_rows.csv", scenario_rows)

    reset_dir = tmp_path / "reset"
    write_json(reset_dir / "summary.json", {"result_class": "current_sim_dual_axis_effective_candidate_reset_validation_adapter_pass"})

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
    return source_dir, reset_dir, selected_path


def _fake_rollout(workload_row: Mapping[str, Any], scenario_spec: Mapping[str, Any], eval_seed: int) -> dict[str, Any]:
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
        "obstacle_label": scenario_spec["sampled_obstacle_label"],
        "workload_marker": workload_row["workload_id"],
    }


def test_effective_candidate_measured_validation_preserves_candidate_metadata(tmp_path: Path) -> None:
    source_dir, reset_dir, selected_path = _write_inputs(tmp_path)

    summary = runner.run_effective_candidate_measured_validation(
        source_dir=source_dir,
        reset_validation_dir=reset_dir,
        selected_rows_path=selected_path,
        config_root=tmp_path / "configs",
        output_dir=tmp_path / "out",
        eval_seed_base=700,
        target_candidate_count=2,
        target_candidate_scenario_reference_count=3,
        target_selected_checkpoint_count=2,
        target_episode_count=6,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["episode_count"] == 6
    assert summary["source_candidate_count"] == 2
    assert summary["candidate_scenario_reference_count"] == 3
    assert summary["unique_pack_scenario_count"] == 2
    assert summary["selected_checkpoint_count"] == 2
    assert summary["failure_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["metric_completeness_failure_count"] == 0
    assert summary["actor_contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["support_policy_ranking_claim_made"] is False
    assert summary["winner_selected"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["candidate_counts"] == {"candidate_a": 4, "candidate_b": 2}
    assert summary["profile_counts"] == {"L0_current_masked": 3, "L3_online_gru": 3}

    episode_rows = runner.read_csv_rows(tmp_path / "out" / "episode_rows.csv")
    assert [int(row["eval_seed"]) for row in episode_rows] == [700, 701, 702, 100700, 100701, 100702]
    assert {row["candidate_id"] for row in episode_rows} == {"candidate_a", "candidate_b"}
    assert {row["pack_id"] for row in episode_rows} == {"baseline_reference_pack", "g_primary_pack"}
    assert {row["effective_candidate_measured_validation"] for row in episode_rows} == {"True"}
    assert (tmp_path / "out" / "aggregate_by_candidate.csv").exists()
    assert (tmp_path / "out" / "aggregate_by_candidate_profile.csv").exists()
    assert (tmp_path / "out" / "aggregate_by_candidate_pack.csv").exists()


def test_effective_candidate_measured_validation_fails_closed_on_contract_gap(tmp_path: Path) -> None:
    source_dir, reset_dir, selected_path = _write_inputs(tmp_path)
    payload = read_json(source_dir / "effective_candidate_configs" / "candidate_a.json")
    payload["selected_scenario_specs"][0]["env_config"]["wheel_observation_mode"] = "raw"
    write_json(source_dir / "effective_candidate_configs" / "candidate_a.json", payload)

    summary = runner.run_effective_candidate_measured_validation(
        source_dir=source_dir,
        reset_validation_dir=reset_dir,
        selected_rows_path=selected_path,
        config_root=tmp_path / "configs",
        output_dir=tmp_path / "out",
        eval_seed_base=700,
        target_candidate_count=2,
        target_candidate_scenario_reference_count=3,
        target_selected_checkpoint_count=2,
        target_episode_count=6,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["episode_count"] == 0
    assert summary["validation_failure_count"] > 0
    assert summary["actor_contract_violation_count"] > 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "wheel_observation_mode" in validation_rows


def test_effective_candidate_measured_validation_fails_closed_on_ranking_flag(tmp_path: Path) -> None:
    source_dir, reset_dir, selected_path = _write_inputs(tmp_path, ranking_flag=True)

    summary = runner.run_effective_candidate_measured_validation(
        source_dir=source_dir,
        reset_validation_dir=reset_dir,
        selected_rows_path=selected_path,
        config_root=tmp_path / "configs",
        output_dir=tmp_path / "out",
        eval_seed_base=700,
        target_candidate_count=2,
        target_candidate_scenario_reference_count=3,
        target_selected_checkpoint_count=2,
        target_episode_count=6,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["episode_count"] == 0
    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "guardrail_violation" in validation_rows
    assert "selected_row_ranking" in validation_rows
