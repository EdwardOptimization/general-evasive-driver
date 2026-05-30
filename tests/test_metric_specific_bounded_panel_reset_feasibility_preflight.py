from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import metric_specific_bounded_panel_reset_feasibility_preflight as reset_panel


class _FakeEnv:
    def __init__(self, config):
        self.config = config

    def reset(self, seed: int):
        return [], {
            "obstacle_label": "aes_feasible",
            "initial_mu": 0.8,
            "speed_ref": 12.0,
            "obstacle_distance": 20.0,
            "active_obstacle_half_width": 0.8,
            "obstacle_threshold_score": 1.0,
            "obstacle_time_after_friction_step": 0.0,
        }

    def close(self) -> None:
        return None


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    specs = []
    matrix = []
    for role_index in range(4):
        role = f"role_{role_index}"
        for spec_index in range(6):
            spec_id = f"spec_{role_index}_{spec_index}"
            specs.append(
                {
                    "bounded_panel_spec_id": spec_id,
                    "scenario_spec_id": spec_id,
                    "env_config": {"history_length": 1},
                }
            )
            for profile_index in range(12):
                profile_name = f"profile_{profile_index}"
                config_path = tmp_path / f"{profile_name}.json"
                if not config_path.exists():
                    write_json(config_path, {"profile_name": profile_name})
                matrix.append(
                    {
                        "bounded_panel_workload_id": f"{spec_id}::{profile_name}",
                        "scenario_workload_id": f"{spec_id}::{profile_name}",
                        "scenario_spec_id": spec_id,
                        "bounded_panel_spec_id": spec_id,
                        "source_scenario_spec_id": f"source_{spec_id}",
                        "m1728_scenario_spec_id": f"source_{spec_id}",
                        "role_panel_id": role,
                        "role_panel_label": role,
                        "scenario_family_id": f"S{role_index}",
                        "scenario_family": f"family_{role_index}",
                        "scenario_role": "test",
                        "profile_name": profile_name,
                        "profile_config_path": str(config_path),
                        "evaluation_role": "benchmark",
                        "primary_metric_family": "avoidance_success",
                        "panel_evaluation_role": "benchmark",
                        "panel_primary_metric_family": "avoidance_success",
                        "allowed_labels_metadata_only": "aes_feasible",
                        "labels_enter_actor_input": False,
                        "hidden_dynamics_bucket": "nominal",
                        "road_boundary_bucket": "moderate",
                        "obstacle_timing_bucket": "close",
                        "obstacle_lateral_bucket": "center",
                        "sampling_repair_source": "test",
                        "sampling_repair_variant_id": "none",
                        "sampling_repair_applied": False,
                    }
                )
    specs_path = tmp_path / "specs.json"
    matrix_path = tmp_path / "matrix.csv"
    write_json(specs_path, {"bounded_panel_specs": specs})
    write_csv_rows(matrix_path, matrix)
    return specs_path, matrix_path


def test_bounded_panel_reset_feasibility_preflight_smoke(tmp_path: Path, monkeypatch) -> None:
    specs_path, matrix_path = _write_inputs(tmp_path)
    monkeypatch.setattr(reset_panel, "AutoDriftEnv", _FakeEnv)
    monkeypatch.setattr(reset_panel, "env_config_for_executable_profile", lambda executable_spec, profile_config: {})

    summary = reset_panel.run_metric_specific_bounded_panel_reset_feasibility_preflight(
        bounded_panel_specs_path=specs_path,
        bounded_panel_matrix_path=matrix_path,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "metric_specific_bounded_panel_reset_feasibility_preflight_pass"
    assert summary["attempted_cell_count"] == 288
    assert summary["reset_success_count"] == 288
    assert summary["sampling_failure_count"] == 0
    assert summary["profile_count"] == 12
    assert summary["role_panel_count"] == 4
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "reset_stress_rows.csv").exists()
    assert (tmp_path / "out" / "sampling_failure_rows.csv").exists()
