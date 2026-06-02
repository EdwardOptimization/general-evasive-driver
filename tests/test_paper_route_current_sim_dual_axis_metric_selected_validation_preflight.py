from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_dual_axis_metric_selected_validation_preflight as runner


def _spec(index: int) -> dict[str, object]:
    env_config = {
        "track_radius": 10.0 + index,
        "track_width": 2.0,
        "history_length": 1,
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
    }
    return {
        "reset_target_index": index,
        "reset_target_key": f"pack|scenario_{index}|orig{index}",
        "env_config_hash": f"orig{index}",
        "pack_id": "pack",
        "scenario_spec_id": f"scenario_{index}",
        "family_ids": "f1|f2",
        "family_count": 2,
        "effective_candidate_ids": "c1",
        "effective_candidate_count": 1,
        "scenario_reference_count": 3,
        "actor_contract_guardrail_pass": True,
        "env_config": env_config,
    }


def _selected(index: int) -> dict[str, object]:
    return {
        "matrix_id": f"profile::seed_{index}",
        "profile_name": "profile",
        "seed_id": str(index),
        "selected_checkpoint_path": f"checkpoint_{index}.pt",
        "selected_checkpoint_step": "1",
        "selected_checkpoint_kind": "test",
    }


def _source_rows(specs: list[dict[str, object]], selected: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for selected_index, _selected_row in enumerate(selected):
        for spec in specs:
            rows.append(
                {
                    "reset_target_key": spec["reset_target_key"],
                    "selected_checkpoint_index": selected_index,
                }
            )
    return rows


def test_metric_selected_validation_preflight_materializes_and_resets(tmp_path: Path) -> None:
    specs = [_spec(0), _spec(1)]
    selected = [_selected(0), _selected(1), _selected(2)]

    summary = runner.run_metric_selected_validation_preflight(
        reset_target_specs=specs,
        selected_rows=selected,
        source_episode_rows=_source_rows(specs, selected),
        output_dir=tmp_path / "out",
        target_reset_target_count=2,
        target_selected_checkpoint_count=3,
        target_episode_count=6,
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["workload_row_count"] == 6
    assert summary["reset_target_count"] == 2
    assert summary["environment_reset_success_count"] == 2
    assert summary["actor_observation_shape_changed_count"] == 0
    assert summary["policy_action_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "workload_rows.csv").exists()


def test_metric_selected_env_config_preserves_contract_fields() -> None:
    spec = _spec(0)
    source_config = spec["env_config"]

    metric_config = runner._metric_selected_env_config(source_config, soft_offtrack_tolerance_m=0.20)

    assert metric_config["soft_offtrack_metric_enabled"] is True
    assert metric_config["soft_offtrack_tolerance_m"] == 0.20
    assert metric_config["track_width"] == source_config["track_width"]
    assert metric_config["history_length"] == 1
    assert metric_config["include_privileged_params"] is False
    assert metric_config["wheel_observation_mode"] == "none"
    assert metric_config["obstacle_relative_velocity_mode"] == "zero"


def test_metric_selected_validation_preflight_fails_closed_on_source_gap(tmp_path: Path) -> None:
    specs = [_spec(0), _spec(1)]
    selected = [_selected(0), _selected(1), _selected(2)]
    source_rows = _source_rows(specs[:1], selected)

    summary = runner.run_metric_selected_validation_preflight(
        reset_target_specs=specs,
        selected_rows=selected,
        source_episode_rows=source_rows,
        output_dir=tmp_path / "out",
        target_reset_target_count=2,
        target_selected_checkpoint_count=3,
        target_episode_count=6,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["missing_source_target_count"] == 1
    assert "scenario_sampling_failure" in summary["failure_types_observed"]


def test_metric_selected_validation_preflight_fails_closed_on_missing_source_cell(tmp_path: Path) -> None:
    specs = [_spec(0), _spec(1)]
    selected = [_selected(0), _selected(1)]
    source_rows = _source_rows(specs, selected)
    source_rows[-1] = source_rows[0]

    summary = runner.run_metric_selected_validation_preflight(
        reset_target_specs=specs,
        selected_rows=selected,
        source_episode_rows=source_rows,
        output_dir=tmp_path / "out",
        target_reset_target_count=2,
        target_selected_checkpoint_count=2,
        target_episode_count=4,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["missing_source_cell_count"] == 1
    assert summary["source_m2413_duplicate_cell_count"] == 1
    assert "scenario_sampling_failure" in summary["failure_types_observed"]
