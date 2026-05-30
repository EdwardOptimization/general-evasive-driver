from pathlib import Path

from autodrift.artifacts import read_json, write_json
from autodrift import executable_v2_reset_feasibility_preflight as v2_reset


class _FakeEnv:
    def __init__(self, config):
        self.config = config

    def reset(self, seed: int):
        if self.config.get("raise_on_reset"):
            raise RuntimeError("synthetic reset failure")
        return [], {
            "obstacle_label": self.config.get("label", "aes_feasible"),
            "initial_mu": 0.8,
            "speed_ref": 12.0,
            "obstacle_distance": 20.0,
            "active_obstacle_half_width": 0.8,
            "obstacle_threshold_score": 1.0,
            "obstacle_time_after_friction_step": 0.0,
        }

    def close(self) -> None:
        return None


def _write_inputs(tmp_path: Path, *, fail_one: bool = False) -> Path:
    specs = []
    for surface_index, surface in enumerate(("stable_avoidance_aes", "unavoidable_mitigation")):
        label = "aes_feasible" if surface == "stable_avoidance_aes" else "unavoidable"
        for profile_index in range(2):
            profile_name = f"profile_{profile_index}"
            config_path = tmp_path / f"{profile_name}.json"
            if not config_path.exists():
                write_json(config_path, {"profile_name": profile_name, "env": {"history_length": 1}})
            spec_index = len(specs)
            specs.append(
                {
                    "v2_panel_spec_id": f"v2_{spec_index}",
                    "source_v1_bounded_panel_spec_id": f"source_{surface_index}",
                    "source_v1_role_panel_id": surface,
                    "source_scenario_spec_id": f"scenario_{surface_index}",
                    "v2_role_surface_id": surface,
                    "role_panel_id": surface,
                    "profile_name": profile_name,
                    "profile_config_path": str(config_path),
                    "checkpoint_path": "unused.pt",
                    "config_exists": True,
                    "checkpoint_exists": True,
                    "v2_task_label": label,
                    "allowed_labels_metadata_only": label,
                    "labels_enter_actor_input": False,
                    "hidden_dynamics_bucket": "nominal" if surface_index == 0 else "low_mu",
                    "road_boundary_bucket": "moderate",
                    "obstacle_timing_bucket": "close",
                    "obstacle_lateral_bucket": "center",
                    "v2_primary_metric": (
                        "admissible_obstacle_pass_rate"
                        if surface == "stable_avoidance_aes"
                        else "impact_severity_proxy_mean"
                    ),
                    "v2_primary_metric_direction": "higher" if surface_index == 0 else "lower",
                    "v2_supporting_metrics": "collision_failure_rate",
                    "v2_admissibility_gate": (
                        "collision_rate_low_and_off_track_rate_low"
                        if surface == "stable_avoidance_aes"
                        else "mitigation_surface_only_no_avoidance_ranking"
                    ),
                    "env_config": {"history_length": 1, "label": label, "raise_on_reset": fail_one and spec_index == 1},
                    "reset_ready_spec": True,
                    "diagnostic_only_no_ranking_claim": True,
                    "v2_ranking_admissible_by_default": False,
                    "environment_reset_scheduled": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                }
            )
    path = tmp_path / "v2_specs.json"
    write_json(path, {"executable_v2_panel_specs": specs})
    return path


def test_executable_v2_reset_feasibility_adapter_smoke(tmp_path: Path, monkeypatch) -> None:
    specs_path = _write_inputs(tmp_path)
    monkeypatch.setattr(v2_reset, "AutoDriftEnv", _FakeEnv)
    monkeypatch.setattr(
        v2_reset,
        "env_config_for_executable_profile",
        lambda executable_spec, profile_config: dict(executable_spec["env_config"]),
    )

    summary = v2_reset.run_executable_v2_reset_feasibility_preflight(
        executable_v2_panel_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_spec_count=4,
        target_profile_count=2,
        target_role_surface_count=2,
    )

    assert summary["result_class"] == "executable_v2_reset_feasibility_preflight_pass"
    assert summary["attempted_spec_count"] == 4
    assert summary["reset_success_count"] == 4
    assert summary["sampling_failure_count"] == 0
    assert summary["profile_count"] == 2
    assert summary["role_surface_count"] == 2
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    rows = (tmp_path / "out" / "reset_stress_rows.csv").read_text()
    assert "v2_panel_spec_id" in rows
    assert "stable_avoidance_aes" in rows
    assert (tmp_path / "out" / "label_distribution_by_surface.csv").exists()


def test_executable_v2_reset_feasibility_adapter_preserves_failures(tmp_path: Path, monkeypatch) -> None:
    specs_path = _write_inputs(tmp_path, fail_one=True)
    monkeypatch.setattr(v2_reset, "AutoDriftEnv", _FakeEnv)
    monkeypatch.setattr(
        v2_reset,
        "env_config_for_executable_profile",
        lambda executable_spec, profile_config: dict(executable_spec["env_config"]),
    )

    summary = v2_reset.run_executable_v2_reset_feasibility_preflight(
        executable_v2_panel_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_spec_count=4,
        target_profile_count=2,
        target_role_surface_count=2,
    )

    assert summary["result_class"] == "executable_v2_reset_feasibility_preflight_fail"
    assert summary["reset_success_count"] == 3
    assert summary["sampling_failure_count"] == 1
    failure_rows = (tmp_path / "out" / "sampling_failure_rows.csv").read_text()
    assert "v2_1" in failure_rows
    assert "synthetic reset failure" in failure_rows
    summary_json = read_json(tmp_path / "out" / "summary.json")
    assert summary_json["policy_action_executed"] is False
