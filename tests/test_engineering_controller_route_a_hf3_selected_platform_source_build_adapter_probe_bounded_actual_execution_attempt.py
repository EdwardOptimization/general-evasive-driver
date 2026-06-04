import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt import (
    ACTION_DIM,
    ALLOWED_CLAIMS,
    CommandResult,
    P0_OBSERVATION_DIM,
    run_bounded_actual_execution_attempt,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _fake_runner(source_root: Path, seen: list[str]):
    def run(spec):
        seen.append(spec.command_id)
        returncode = 0
        stdout = f"{spec.command_id}\n"
        stderr = ""
        if spec.command_id == "source_root_directory_available":
            returncode = 0 if source_root.is_dir() else 1
        elif spec.command_id == "source_cmake_lists_available":
            returncode = 0 if (source_root / "CMakeLists.txt").is_file() else 1
        elif spec.command_id == "pychrono_projectchrono_package_discovery":
            stdout = "pychrono False\nprojectchrono False\n"
        result = CommandResult(returncode=returncode, timed_out=False, stdout=stdout, stderr=stderr)
        spec.stdout_path.parent.mkdir(parents=True, exist_ok=True)
        spec.stderr_path.parent.mkdir(parents=True, exist_ok=True)
        spec.stdout_path.write_text(stdout, encoding="utf-8")
        spec.stderr_path.write_text(stderr, encoding="utf-8")
        return result

    return run


def test_missing_source_records_blocker_and_skips_forward_commands(tmp_path):
    source_root = tmp_path / "missing_chrono_source"
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "docs" / "m2635.md"
    seen: list[str] = []

    summary = run_bounded_actual_execution_attempt(
        output_dir,
        source_root=source_root,
        doc_path=doc_path,
        repo_root=Path("."),
        command_runner=_fake_runner(source_root, seen),
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "dependency_source_unavailable_blocker_recorded"
    assert summary["availability_gate_executed"] is True
    assert summary["source_root_available"] is False
    assert summary["cmake_lists_available"] is False
    assert summary["toolchain_available"] is True
    assert summary["package_import_unavailable"] is True
    assert summary["configure_attempt_executed"] is False
    assert summary["compile_attempt_executed"] is False
    assert summary["repo_local_adapter_import_attempt_executed"] is False
    assert summary["repo_local_backend_metadata_probe_attempt_executed"] is False
    assert summary["backend_started"] is False
    assert summary["reset_executed"] is False
    assert summary["step_executed"] is False
    assert summary["validation_executed"] is False
    assert summary["driver_performance_claim_allowed"] is False
    assert summary["actor_observation_shape"] == P0_OBSERVATION_DIM
    assert summary["action_shape"] == ACTION_DIM

    assert "source_build_configure_attempt" not in seen
    assert "repo_local_adapter_import_metadata_attempt" not in seen

    command_rows = _read_csv(output_dir / "command_attempt_rows.csv")
    assert len(command_rows) == 4
    assert {row["executed"] for row in command_rows} == {"False"}
    assert {row["skipped"] for row in command_rows} == {"True"}
    assert {row["skip_reason"] for row in command_rows} == {
        "dependency_source_unavailable"
    }

    backend_trace = read_json(output_dir / "backend_probe_trace.json")
    assert backend_trace["trace_status"] == "skipped"
    assert backend_trace["external_simulator_imported"] is False
    assert backend_trace["backend_started"] is False
    assert backend_trace["reset_executed"] is False
    assert backend_trace["step_executed"] is False

    claim_rows = _read_csv(output_dir / "claim_boundary_checks.csv")
    allowed = {
        row["claim_family"]
        for row in claim_rows
        if row["claim_allowed_in_m2635"] == "True"
    }
    assert allowed == set(ALLOWED_CLAIMS)

    artifact_rows = _read_csv(output_dir / "artifact_manifest.csv")
    assert len(artifact_rows) == 11
    assert {row["exists"] for row in artifact_rows} == {"True"}
    assert doc_path.exists()


def test_available_source_executes_bounded_attempts_with_injected_runner(tmp_path):
    source_root = tmp_path / "chrono"
    source_root.mkdir()
    (source_root / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.20)\n", encoding="utf-8")
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "docs" / "m2635.md"
    seen: list[str] = []

    summary = run_bounded_actual_execution_attempt(
        output_dir,
        source_root=source_root,
        doc_path=doc_path,
        repo_root=Path("."),
        command_runner=_fake_runner(source_root, seen),
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "bounded_actual_execution_attempt_artifacts_written"
    assert summary["availability_blocker"] == "none"
    assert summary["source_root_available"] is True
    assert summary["cmake_lists_available"] is True
    assert summary["toolchain_available"] is True
    assert summary["configure_attempt_executed"] is True
    assert summary["compile_attempt_executed"] is True
    assert summary["repo_local_adapter_import_attempt_executed"] is True
    assert summary["repo_local_backend_metadata_probe_attempt_executed"] is True
    assert summary["external_simulator_imported"] is False
    assert summary["backend_started"] is False
    assert summary["reset_executed"] is False
    assert summary["validation_executed"] is False

    for command_id in {
        "source_build_configure_attempt",
        "source_build_compile_attempt",
        "repo_local_adapter_import_metadata_attempt",
        "repo_local_backend_metadata_probe_attempt",
    }:
        assert command_id in seen

    command_rows = _read_csv(output_dir / "command_attempt_rows.csv")
    assert {row["executed"] for row in command_rows} == {"True"}
    assert {row["skipped"] for row in command_rows} == {"False"}
    assert {row["blocker_classification"] for row in command_rows} == {"none"}

    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
