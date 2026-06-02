from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization import (
    read_csv_rows,
    run_effective_config_schema_repair_materialization,
)


CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "repair_family",
    "candidate_config_path",
    "reward_patch_count",
    "curriculum_patch_count",
    "guardrail_patch_scope",
    "guardrail_patch_count",
    "mixed_collision_guardrail_required",
    "inside_run_dir",
    "active_config_overwritten",
    "loaded_into_environment",
    "environment_reset_started",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]


def _candidate_payload(candidate_id: str, axis: str, value: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source_repair_spec_id": f"{candidate_id}_spec",
        "repair_family": "offtrack_containment_repair",
        "source_slice_axis": axis,
        "source_slice_value": value,
        "priority_tier": "P1",
        "reward_overlay": [
            {"patch_id": f"{candidate_id}_reward_{index}", "target_key": f"reward.{index}", "delta_value": "0.1"}
            for index in range(3)
        ],
        "curriculum_overlay": [
            {"patch_id": f"{candidate_id}_curriculum_0", "target_key": "curriculum.0", "delta_value": "1.0"}
        ],
        "guardrail_overlay": {"scope_id": "global_guardrail_scope", "guardrail_patch_count": 284},
        "mixed_guarded_requirements": {"collision_guardrail_required": False},
        "claim_boundary": {
            "active_config_overwritten": False,
            "loaded_into_environment": False,
            "environment_reset_started": False,
            "repair_execution_started": False,
            "training_started": False,
            "ranking_admissible": False,
            "winner_selected": False,
        },
    }


def _env_config() -> dict[str, object]:
    return {
        "history_length": 1,
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "track_kind": "circle",
        "track_width": 6.0,
    }


def _scenario(spec_id: str, role: str, hidden: str) -> dict[str, object]:
    return {
        "scenario_spec_id": spec_id,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "role_family": role,
        "sampled_obstacle_label": "aes_feasible",
        "hidden_dynamics_bucket": hidden,
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "history_length": 1,
        "env_config": _env_config(),
    }


def _write_source_dir(tmp_path: Path, *, unmatched: bool = False) -> Path:
    source = tmp_path / "source"
    config_dir = source / "candidate_configs"
    config_dir.mkdir(parents=True)
    value = "R9_missing_role" if unmatched else "R0_stable_avoidable"
    payloads = [
        _candidate_payload("candidate_role", "role_family", value),
        _candidate_payload(
            "candidate_composite",
            "role_family+hidden_dynamics_bucket",
            "R5_hidden_dynamics_robustness|weak_brake",
        ),
    ]
    rows = []
    for payload in payloads:
        candidate_id = str(payload["candidate_id"])
        path = config_dir / f"{candidate_id}.json"
        write_json(path, payload)
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_repair_spec_id": payload["source_repair_spec_id"],
                "repair_family": payload["repair_family"],
                "candidate_config_path": str(path),
                "reward_patch_count": 3,
                "curriculum_patch_count": 1,
                "guardrail_patch_scope": "global_guardrail_scope",
                "guardrail_patch_count": 284,
                "mixed_collision_guardrail_required": False,
                "inside_run_dir": True,
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "environment_reset_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    write_json(source / "summary.json", {"result_class": "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"})
    write_json(
        source / "candidate_config_generation_manifest.json",
        {"result_class": "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"},
    )
    write_csv_rows(source / "candidate_config_rows.csv", rows, fieldnames=CANDIDATE_FIELDNAMES)
    return source


def _write_base_pack_manifest(tmp_path: Path) -> Path:
    pack_dir = tmp_path / "packs"
    pack_dir.mkdir()
    pack_paths = []
    for index in range(2):
        pack_path = pack_dir / f"pack_{index}.json"
        pack_paths.append(pack_path)
        write_json(
            pack_path,
            {
                "config_pack_id": f"pack_{index}",
                "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
                "scenario_specs": [
                    _scenario(f"r0_{index}", "R0_stable_avoidable", "nominal"),
                    _scenario(f"r5_{index}", "R5_hidden_dynamics_robustness", "weak_brake"),
                ],
            },
        )
    manifest_path = tmp_path / "repaired_config_pack_manifest.json"
    write_json(
        manifest_path,
        {
            "active_config_overwritten": False,
            "packs": [
                {"pack_id": f"pack_{index}", "pack_path": str(path), "active_config_overwritten": False}
                for index, path in enumerate(pack_paths)
            ],
        },
    )
    return manifest_path


def test_effective_config_materialization_writes_pack_artifacts_without_env_load(tmp_path: Path) -> None:
    source = _write_source_dir(tmp_path)
    base_manifest = _write_base_pack_manifest(tmp_path)

    summary = run_effective_config_schema_repair_materialization(
        candidate_source_dir=source,
        base_pack_manifest_path=base_manifest,
        output_dir=tmp_path / "out",
        target_candidate_config_count=2,
        target_base_pack_count=2,
        target_base_scenario_specs_per_pack=2,
    )

    assert summary["result_class"] == "current_sim_dual_axis_effective_config_schema_repair_materialization_pass"
    assert summary["source_candidate_config_count"] == 2
    assert summary["effective_candidate_config_written_count"] == 2
    assert summary["candidate_without_matching_scenarios_count"] == 0
    assert summary["selected_scenario_reference_count"] == 4
    assert summary["environment_load_attempt_count"] == 0
    assert summary["environment_reset_attempt_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["guardrail_violation_count"] == 0

    rows = read_csv_rows(tmp_path / "out" / "effective_candidate_config_rows.csv")
    assert {row["effective_candidate_config_inside_run_dir"] for row in rows} == {"True"}
    scenario_rows = read_csv_rows(tmp_path / "out" / "effective_candidate_scenario_rows.csv")
    assert len(scenario_rows) == 4
    assert {row["actor_contract_guardrail_pass"] for row in scenario_rows} == {"True"}
    payload = read_json(tmp_path / "out" / "effective_candidate_configs" / "candidate_composite.json")
    assert payload["matching_rule"]["actor_input_used_for_matching"] is False
    assert payload["selected_scenario_count"] == 2
    assert payload["claim_boundary"]["loaded_into_environment"] is False


def test_effective_config_materialization_fails_closed_when_candidate_has_no_match(tmp_path: Path) -> None:
    source = _write_source_dir(tmp_path, unmatched=True)
    base_manifest = _write_base_pack_manifest(tmp_path)

    summary = run_effective_config_schema_repair_materialization(
        candidate_source_dir=source,
        base_pack_manifest_path=base_manifest,
        output_dir=tmp_path / "out",
        target_candidate_config_count=2,
        target_base_pack_count=2,
        target_base_scenario_specs_per_pack=2,
    )

    assert summary["result_class"] == "current_sim_dual_axis_effective_config_schema_repair_materialization_fail"
    assert summary["candidate_without_matching_scenarios_count"] == 1
    assert summary["effective_candidate_config_written_count"] == 1
    assert summary["environment_load_attempt_count"] == 0
    assert summary["environment_reset_attempt_count"] == 0
    assert summary["active_config_overwritten"] is False
    rows = read_csv_rows(tmp_path / "out" / "effective_candidate_config_rows.csv")
    failed = [row for row in rows if row["candidate_id"] == "candidate_role"][0]
    assert failed["failure_reasons"] == "no_matching_scenario_specs"
