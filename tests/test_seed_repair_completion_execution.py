import pytest

from autodrift.artifacts import write_csv_rows
import autodrift.seed_repair_completion_execution as execution


def _write_minimal_sources(tmp_path):
    source_run = tmp_path / "source"
    write_csv_rows(source_run / "episode_rows.csv", [{"workload_id": "w0", "profile_name": "p0"}])
    write_csv_rows(
        source_run / "failure_rows.csv",
        [
            {
                "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
                "error_type": "RuntimeError",
                "error_message": "failed to sample an obstacle scenario matching the configured filters",
            }
        ],
    )
    probe_rows = tmp_path / "probe_rows.csv"
    write_csv_rows(
        probe_rows,
        [
            {
                "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
                "seed_role": "neighbor",
                "eval_seed": 175760,
                "seed_offset": -1,
                "reset_success": True,
                "sampled_obstacle_label": "unavoidable",
            }
        ],
    )
    return source_run, probe_rows


def test_run_seed_repair_completion_execution_wires_fixed_inputs_without_real_policy(monkeypatch, tmp_path) -> None:
    source_run, probe_rows = _write_minimal_sources(tmp_path)
    captured = {}

    monkeypatch.setattr(
        execution,
        "scenario_taxonomy_workload_rows",
        lambda **_: [
            {
                "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
                "scenario_spec_id": "m1728-s4-02",
                "profile_name": "L2_window_13_current_tiled",
            }
        ],
    )
    monkeypatch.setattr(execution, "load_scenario_specs", lambda _path: [{"scenario_spec_id": "m1728-s4-02"}])
    monkeypatch.setattr(execution, "_load_required_profile", lambda *_args, **_kwargs: ({}, object(), {"profile_name": "L2_window_13_current_tiled"}))

    def fake_run_cell(**kwargs):
        captured["eval_seed"] = kwargs["eval_seed"]
        return {
            "workload_id": "m1728-s4-02::L2_window_13_current_tiled",
            "sampled_obstacle_label": "unavoidable",
        }

    def fake_write_outputs(**kwargs):
        captured["source_episode_count"] = len(kwargs["source_episode_rows"])
        captured["source_failure_count"] = len(kwargs["source_failure_rows"])
        captured["repaired_workload_id"] = kwargs["repaired_row"]["workload_id"]
        captured["replacement_eval_seed"] = kwargs["plan"].replacement_eval_seed
        return {"result_class": "synthetic_pass", "episode_count": 2, "failure_count": 0}

    monkeypatch.setattr(execution, "_run_scenario_workload_cell", fake_run_cell)
    monkeypatch.setattr(execution, "write_seed_repair_completion_outputs", fake_write_outputs)

    summary = execution.run_seed_repair_completion_execution(
        output_dir=tmp_path / "out",
        source_run_dir=source_run,
        probe_rows_path=probe_rows,
        scenario_specs_path=tmp_path / "unused_semantics.json",
        executable_scenario_specs_path=tmp_path / "unused_exec.json",
        workload_path=tmp_path / "unused_workload.csv",
        unsupported_features_path=tmp_path / "unused_unsupported.csv",
        m1674_run_dir=tmp_path / "unused_profiles",
        device="cpu",
    )

    assert summary["result_class"] == "synthetic_pass"
    assert captured["eval_seed"] == 175760
    assert captured["source_episode_count"] == 1
    assert captured["source_failure_count"] == 1
    assert captured["repaired_workload_id"] == "m1728-s4-02::L2_window_13_current_tiled"
    assert captured["replacement_eval_seed"] == 175760


def test_run_seed_repair_completion_execution_rejects_replacement_seed_mismatch(tmp_path) -> None:
    source_run, probe_rows = _write_minimal_sources(tmp_path)

    with pytest.raises(ValueError, match="replacement seed mismatch"):
        execution.run_seed_repair_completion_execution(
            output_dir=tmp_path / "out",
            source_run_dir=source_run,
            probe_rows_path=probe_rows,
            replacement_eval_seed=175762,
        )
