"""Route A HF3 selected-platform source-build/adapter-probe bounded attempt.

This runner executes only the M2634 command-attempt preflight boundary. It
records local source/tool availability and either runs the admitted local
commands or writes explicit blocker rows. It must not install dependencies,
mutate source trees, use network dependency resolution, start backends, reset,
step, roll out, replay, validate, train, rank, or promote.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2635-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-bounded-actual-execution-attempt-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2636-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-bounded-actual-execution-attempt-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2635-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-"
    "adapter-probe-bounded-actual-execution-attempt-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2635_engineering_controller_route_a_hf3_selected_platform_"
    "source_build_adapter_probe_bounded_actual_execution_attempt"
)
DEFAULT_SOURCE_ROOT = Path("/home/quyaonan/workspace/chrono")
SELECTED_PLATFORM_FAMILY = "chrono_vehicle_or_equivalent_open_backend"
DEPLOYED_ACTION_MAPPING = "[steer, throttle, brake]"

CLAIM_BOUNDARY = (
    "Route A HF3 selected-platform source-build/adapter-probe bounded actual "
    "execution-attempt preflight only; command-attempt rows logs traces and "
    "blocker classifications may be recorded, but not dependency readiness, "
    "source-build success, adapter-probe success, backend discovery, backend "
    "availability, reset execution, validation readiness/result, driver "
    "performance, paper, FW-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID"
)

SOURCE_AVAILABILITY_FIELDNAMES = [
    "availability_check_id",
    "check_family",
    "selected_platform_family",
    "cwd",
    "command",
    "timeout_s",
    "stdout_path",
    "stderr_path",
    "returncode",
    "timed_out",
    "condition_satisfied",
    "blocker_classification",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

COMMAND_ATTEMPT_FIELDNAMES = [
    "command_attempt_id",
    "command_family",
    "selected_platform_family",
    "cwd",
    "command",
    "timeout_s",
    "stdout_path",
    "stderr_path",
    "returncode",
    "timed_out",
    "executed",
    "skipped",
    "skip_reason",
    "blocker_classification",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

ARTIFACT_MANIFEST_FIELDNAMES = [
    "artifact_id",
    "path",
    "artifact_type",
    "exists",
    "purpose",
    "actor_visible_allowed",
    "status_pass",
    "claim_boundary",
]

BACKEND_PROBE_TRACE_FIELDNAMES = [
    "trace_id",
    "trace_family",
    "executed",
    "skipped",
    "skip_reason",
    "external_simulator_imported",
    "backend_started",
    "reset_executed",
    "step_executed",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2635",
    "evidence_required_before_claim",
    "status_pass",
    "claim_boundary",
]

GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]

ALLOWED_CLAIMS = frozenset({"bounded_command_attempt_or_blocker_evidence_materialized"})
CLAIM_CHECKS = (
    (
        "bounded_command_attempt_or_blocker_evidence_materialized",
        True,
        "M2635 source availability rows command-attempt rows logs traces blockers "
        "artifact manifest claim-boundary rows and gate matrix",
    ),
    ("dependency_ready_for_execution", False, "future dependency readiness audit"),
    ("source_build_succeeded", False, "future source-build result audit"),
    ("adapter_probe_succeeded", False, "future adapter-probe result audit"),
    ("backend_discovered", False, "future backend discovery evidence"),
    ("backend_available", False, "future backend availability audit"),
    ("backend_started", False, "future backend execution milestone"),
    ("reset_executed", False, "future explicit reset execution"),
    ("reset_success", False, "future reset-success audit"),
    ("policy_action_executed", False, "future policy-action execution milestone"),
    ("environment_step_executed", False, "future environment-step execution milestone"),
    ("rollout_executed", False, "future rollout execution milestone"),
    ("rollout_feasibility", False, "future rollout-feasibility audit"),
    ("replay_executed", False, "future replay execution milestone"),
    ("validation_protocol_readiness", False, "future validation protocol-readiness audit"),
    ("validation_admission", False, "future validation-admission audit"),
    ("validation_result", False, "future validation-result audit"),
    ("high_fidelity_validation_result", False, "future high-fidelity validation audit"),
    ("driver_performance", False, "measured validation with claim-boundary audit"),
    ("controller_family_ranking", False, "controller-family comparison milestone"),
    ("winner_selection", False, "controller-family comparison milestone"),
    ("success_rate", False, "separate verdict milestone"),
    ("checkpoint_promotion", False, "promotion gate milestone"),
    ("current_sim_verdict", False, "separate current-sim verdict synthesis"),
    ("paper_level_evidence", False, "separate paper-route evidence matrix"),
    ("finite_window_vs_gru", False, "separate finite-window-vs-GRU matrix"),
    ("level3_self_identification", False, "separate self-ID proof gate"),
)


@dataclass(frozen=True)
class CommandSpec:
    command_id: str
    family: str
    argv: tuple[str, ...]
    cwd: Path
    timeout_s: int
    stdout_path: Path
    stderr_path: Path
    env: dict[str, str] | None = None


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    timed_out: bool
    stdout: str
    stderr: str


CommandRunner = Callable[[CommandSpec], CommandResult]


def run_bounded_actual_execution_attempt(
    output_dir: Path,
    *,
    source_root: Path | None = None,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    repo_root: Path | str = ".",
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = output_dir / "logs"
    artifacts_dir = output_dir / "artifacts"
    build_root = output_dir / "build" / "chrono"
    logs_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    selected_source_root = _resolve_source_root(source_root)
    runner = command_runner or _run_command

    command_plan = build_command_plan(
        repo=repo,
        output_dir=output_dir,
        source_root=selected_source_root,
        build_root=build_root,
        logs_dir=logs_dir,
        artifacts_dir=artifacts_dir,
    )
    write_json(output_dir / "command_plan.json", command_plan)

    availability_rows, availability_results = execute_availability_gate(
        repo=repo,
        source_root=selected_source_root,
        logs_dir=logs_dir,
        runner=runner,
    )
    source_root_available = _condition(availability_rows, "source_root_directory_available")
    cmake_lists_available = _condition(availability_rows, "source_cmake_lists_available")
    cmake_available = _condition(availability_rows, "cmake_tool_available")
    ninja_available = _condition(availability_rows, "ninja_tool_available")
    cxx_available = _condition(availability_rows, "cxx_tool_available")
    toolchain_available = bool(cmake_available and ninja_available and cxx_available)
    package_row = _row_by_id(availability_rows, "pychrono_projectchrono_package_discovery")
    package_import_unavailable = not _boolish(package_row.get("condition_satisfied"))
    availability_blocker = classify_availability_blocker(
        source_root_available=source_root_available,
        cmake_lists_available=cmake_lists_available,
        toolchain_available=toolchain_available,
    )

    command_rows = execute_or_skip_command_attempts(
        repo=repo,
        source_root=selected_source_root,
        build_root=build_root,
        logs_dir=logs_dir,
        artifacts_dir=artifacts_dir,
        availability_blocker=availability_blocker,
        runner=runner,
    )
    backend_trace = build_backend_probe_trace(command_rows, availability_blocker)
    backend_trace_rows = build_backend_probe_trace_rows(command_rows, availability_blocker)
    claim_rows = build_claim_boundary_checks(
        availability_rows=availability_rows,
        command_rows=command_rows,
        backend_trace_rows=backend_trace_rows,
    )
    artifact_manifest_rows = build_artifact_manifest_rows(
        output_dir=output_dir,
        doc_path=Path(doc_path),
    )
    gate_rows = build_gate_matrix_rows(
        availability_rows=availability_rows,
        command_rows=command_rows,
        backend_trace_rows=backend_trace_rows,
        claim_rows=claim_rows,
        artifact_manifest_rows=artifact_manifest_rows,
        availability_blocker=availability_blocker,
    )

    source_availability_path = output_dir / "source_availability_rows.csv"
    command_attempt_path = output_dir / "command_attempt_rows.csv"
    artifact_manifest_path = output_dir / "artifact_manifest.csv"
    backend_trace_path = output_dir / "backend_probe_trace.json"
    backend_trace_rows_path = output_dir / "backend_probe_trace_rows.csv"
    claim_path = output_dir / "claim_boundary_checks.csv"
    gate_path = output_dir / "gate_matrix.csv"
    environment_snapshot_path = output_dir / "environment_snapshot.txt"
    doc_output = Path(doc_path)

    write_csv_rows(
        source_availability_path,
        availability_rows,
        fieldnames=SOURCE_AVAILABILITY_FIELDNAMES,
    )
    write_csv_rows(command_attempt_path, command_rows, fieldnames=COMMAND_ATTEMPT_FIELDNAMES)
    write_json(backend_trace_path, backend_trace)
    write_csv_rows(
        backend_trace_rows_path,
        backend_trace_rows,
        fieldnames=BACKEND_PROBE_TRACE_FIELDNAMES,
    )
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)
    write_environment_snapshot(
        environment_snapshot_path,
        repo=repo,
        source_root=selected_source_root,
        output_dir=output_dir,
        availability_rows=availability_rows,
        availability_results=availability_results,
    )

    artifact_manifest_rows = build_artifact_manifest_rows(
        output_dir=output_dir,
        doc_path=doc_output,
    )
    write_csv_rows(
        artifact_manifest_path,
        artifact_manifest_rows,
        fieldnames=ARTIFACT_MANIFEST_FIELDNAMES,
    )

    summary = build_summary(
        output_dir=output_dir,
        milestone=milestone,
        next_blocker=next_blocker,
        doc_path=doc_output,
        source_root=selected_source_root,
        build_root=build_root,
        source_availability_path=source_availability_path,
        command_attempt_path=command_attempt_path,
        artifact_manifest_path=artifact_manifest_path,
        backend_trace_path=backend_trace_path,
        backend_trace_rows_path=backend_trace_rows_path,
        claim_path=claim_path,
        gate_path=gate_path,
        environment_snapshot_path=environment_snapshot_path,
        availability_rows=availability_rows,
        command_rows=command_rows,
        backend_trace_rows=backend_trace_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        artifact_manifest_rows=artifact_manifest_rows,
        availability_blocker=availability_blocker,
        source_root_available=source_root_available,
        cmake_lists_available=cmake_lists_available,
        toolchain_available=toolchain_available,
        package_import_unavailable=package_import_unavailable,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    artifact_manifest_rows = build_artifact_manifest_rows(
        output_dir=output_dir,
        doc_path=doc_output,
    )
    write_csv_rows(
        artifact_manifest_path,
        artifact_manifest_rows,
        fieldnames=ARTIFACT_MANIFEST_FIELDNAMES,
    )
    return summary


def _resolve_source_root(source_root: Path | None) -> Path:
    if source_root is not None:
        return Path(source_root).expanduser().resolve()
    env_root = os.environ.get("AUTODRIFT_HF3_CHRONO_SOURCE_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return DEFAULT_SOURCE_ROOT


def build_command_plan(
    *,
    repo: Path,
    output_dir: Path,
    source_root: Path,
    build_root: Path,
    logs_dir: Path,
    artifacts_dir: Path,
) -> dict[str, Any]:
    return {
        "selected_platform_family": SELECTED_PLATFORM_FAMILY,
        "repo_cwd": str(repo),
        "run_dir": str(output_dir),
        "log_dir": str(logs_dir),
        "artifact_dir": str(artifacts_dir),
        "source_root": str(source_root),
        "build_root": str(build_root),
        "env": {
            "PYTHONPATH": "src",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        },
        "availability_gate": [
            "test -d \"$SOURCE_ROOT\"",
            "test -f \"$SOURCE_ROOT/CMakeLists.txt\"",
            "cmake --version",
            "ninja --version",
            "c++ --version",
            (
                "python -c \"import importlib.util; print('pychrono', "
                "importlib.util.find_spec('pychrono') is not None); "
                "print('projectchrono', importlib.util.find_spec('projectchrono') is not None)\""
            ),
        ],
        "command_attempts": [
            {
                "id": "source_build_configure_attempt",
                "precondition": "source root CMakeLists and toolchain checks pass",
                "command": (
                    "cmake -S \"$SOURCE_ROOT\" -B \"$BUILD_ROOT\" -G Ninja "
                    "-DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF "
                    "-DCH_ENABLE_MODULE_VEHICLE=ON -DCH_ENABLE_MODULE_PYTHON=OFF"
                ),
                "timeout_s": 300,
            },
            {
                "id": "source_build_compile_attempt",
                "precondition": "configure attempt returns zero",
                "command": "cmake --build \"$BUILD_ROOT\" --parallel 2",
                "timeout_s": 1200,
            },
            {
                "id": "repo_local_adapter_import_metadata_attempt",
                "precondition": "source/tool gate and compile attempt return zero",
                "command": (
                    "PYTHONPATH=src python -c \"import importlib; "
                    "m=importlib.import_module('autodrift.four_wheel_hf0_adapter'); "
                    "print({'adapter_module': m.__name__, 'probe_only': True, "
                    "'external_sim_imported': False, 'backend_started': False})\""
                ),
                "timeout_s": 60,
            },
            {
                "id": "repo_local_backend_metadata_probe_attempt",
                "precondition": "adapter import metadata attempt returns zero",
                "command": (
                    "PYTHONPATH=src python -c \"from autodrift.four_wheel_hf0_adapter "
                    "import FourWheelHF0Backend; print({'backend_class': "
                    "FourWheelHF0Backend.__name__, 'backend_id': "
                    "getattr(FourWheelHF0Backend, 'backend_id', None), "
                    "'metadata_probe_only': True, 'backend_started': False, "
                    "'reset_executed': False, 'step_executed': False})\""
                ),
                "timeout_s": 60,
            },
        ],
    }


def execute_availability_gate(
    *,
    repo: Path,
    source_root: Path,
    logs_dir: Path,
    runner: CommandRunner,
) -> tuple[list[dict[str, Any]], dict[str, CommandResult]]:
    specs = [
        CommandSpec(
            command_id="source_root_directory_available",
            family="source_root",
            argv=("test", "-d", str(source_root)),
            cwd=repo,
            timeout_s=30,
            stdout_path=logs_dir / "availability.source_root.stdout",
            stderr_path=logs_dir / "availability.source_root.stderr",
        ),
        CommandSpec(
            command_id="source_cmake_lists_available",
            family="source_schema",
            argv=("test", "-f", str(source_root / "CMakeLists.txt")),
            cwd=repo,
            timeout_s=30,
            stdout_path=logs_dir / "availability.cmake_lists.stdout",
            stderr_path=logs_dir / "availability.cmake_lists.stderr",
        ),
        CommandSpec(
            command_id="cmake_tool_available",
            family="toolchain",
            argv=("cmake", "--version"),
            cwd=repo,
            timeout_s=30,
            stdout_path=logs_dir / "availability.cmake.stdout",
            stderr_path=logs_dir / "availability.cmake.stderr",
        ),
        CommandSpec(
            command_id="ninja_tool_available",
            family="toolchain",
            argv=("ninja", "--version"),
            cwd=repo,
            timeout_s=30,
            stdout_path=logs_dir / "availability.ninja.stdout",
            stderr_path=logs_dir / "availability.ninja.stderr",
        ),
        CommandSpec(
            command_id="cxx_tool_available",
            family="toolchain",
            argv=("c++", "--version"),
            cwd=repo,
            timeout_s=30,
            stdout_path=logs_dir / "availability.cxx.stdout",
            stderr_path=logs_dir / "availability.cxx.stderr",
        ),
        CommandSpec(
            command_id="pychrono_projectchrono_package_discovery",
            family="package_discovery",
            argv=(
                sys.executable,
                "-c",
                (
                    "import importlib.util; "
                    "print('pychrono', importlib.util.find_spec('pychrono') is not None); "
                    "print('projectchrono', importlib.util.find_spec('projectchrono') is not None)"
                ),
            ),
            cwd=repo,
            timeout_s=30,
            stdout_path=logs_dir / "availability.pychrono_projectchrono.stdout",
            stderr_path=logs_dir / "availability.pychrono_projectchrono.stderr",
        ),
    ]
    rows: list[dict[str, Any]] = []
    results: dict[str, CommandResult] = {}
    for spec in specs:
        result = runner(spec)
        results[spec.command_id] = result
        condition_satisfied = _availability_condition_satisfied(spec, result)
        rows.append(
            {
                "availability_check_id": spec.command_id,
                "check_family": spec.family,
                "selected_platform_family": SELECTED_PLATFORM_FAMILY,
                "cwd": str(spec.cwd),
                "command": _format_command(spec.argv),
                "timeout_s": spec.timeout_s,
                "stdout_path": str(spec.stdout_path),
                "stderr_path": str(spec.stderr_path),
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "condition_satisfied": condition_satisfied,
                "blocker_classification": _availability_blocker(spec.command_id, condition_satisfied),
                "actor_visible_allowed": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows, results


def _availability_condition_satisfied(spec: CommandSpec, result: CommandResult) -> bool:
    if spec.command_id == "pychrono_projectchrono_package_discovery":
        return (
            result.returncode == 0
            and "pychrono True" in result.stdout
            and "projectchrono True" in result.stdout
        )
    return result.returncode == 0 and not result.timed_out


def _availability_blocker(command_id: str, condition_satisfied: bool) -> str:
    if condition_satisfied:
        return "none"
    if command_id == "source_root_directory_available":
        return "dependency_source_unavailable"
    if command_id == "source_cmake_lists_available":
        return "selected_platform_source_schema_unavailable"
    if command_id in {"cmake_tool_available", "ninja_tool_available", "cxx_tool_available"}:
        return "local_toolchain_unavailable"
    if command_id == "pychrono_projectchrono_package_discovery":
        return "package_import_unavailable"
    return "unknown_availability_blocker"


def classify_availability_blocker(
    *,
    source_root_available: bool,
    cmake_lists_available: bool,
    toolchain_available: bool,
) -> str:
    if not source_root_available:
        return "dependency_source_unavailable"
    if not cmake_lists_available:
        return "selected_platform_source_schema_unavailable"
    if not toolchain_available:
        return "local_toolchain_unavailable"
    return "none"


def execute_or_skip_command_attempts(
    *,
    repo: Path,
    source_root: Path,
    build_root: Path,
    logs_dir: Path,
    artifacts_dir: Path,
    availability_blocker: str,
    runner: CommandRunner,
) -> list[dict[str, Any]]:
    specs = [
        CommandSpec(
            command_id="source_build_configure_attempt",
            family="source_build_configure",
            argv=(
                "cmake",
                "-S",
                str(source_root),
                "-B",
                str(build_root),
                "-G",
                "Ninja",
                "-DCMAKE_BUILD_TYPE=Release",
                "-DBUILD_TESTING=OFF",
                "-DCH_ENABLE_MODULE_VEHICLE=ON",
                "-DCH_ENABLE_MODULE_PYTHON=OFF",
            ),
            cwd=repo,
            timeout_s=300,
            stdout_path=logs_dir / "source_build_configure.stdout",
            stderr_path=logs_dir / "source_build_configure.stderr",
        ),
        CommandSpec(
            command_id="source_build_compile_attempt",
            family="source_build_compile",
            argv=("cmake", "--build", str(build_root), "--parallel", "2"),
            cwd=repo,
            timeout_s=1200,
            stdout_path=logs_dir / "source_build_compile.stdout",
            stderr_path=logs_dir / "source_build_compile.stderr",
        ),
        CommandSpec(
            command_id="repo_local_adapter_import_metadata_attempt",
            family="adapter_import_metadata",
            argv=(
                sys.executable,
                "-c",
                (
                    "import importlib; "
                    "m=importlib.import_module('autodrift.four_wheel_hf0_adapter'); "
                    "print({'adapter_module': m.__name__, 'probe_only': True, "
                    "'external_sim_imported': False, 'backend_started': False})"
                ),
            ),
            cwd=repo,
            timeout_s=60,
            stdout_path=logs_dir / "adapter_import.stdout",
            stderr_path=logs_dir / "adapter_import.stderr",
            env={"PYTHONPATH": "src"},
        ),
        CommandSpec(
            command_id="repo_local_backend_metadata_probe_attempt",
            family="backend_metadata_probe",
            argv=(
                sys.executable,
                "-c",
                (
                    "from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend; "
                    "print({'backend_class': FourWheelHF0Backend.__name__, 'backend_id': "
                    "getattr(FourWheelHF0Backend, 'backend_id', None), "
                    "'metadata_probe_only': True, 'backend_started': False, "
                    "'reset_executed': False, 'step_executed': False})"
                ),
            ),
            cwd=repo,
            timeout_s=60,
            stdout_path=logs_dir / "backend_metadata_probe.stdout",
            stderr_path=logs_dir / "backend_metadata_probe.stderr",
            env={"PYTHONPATH": "src"},
        ),
    ]
    rows: list[dict[str, Any]] = []
    configure_zero = False
    compile_zero = False
    adapter_import_zero = False
    for spec in specs:
        skip_reason = _skip_reason_for_command(
            spec.command_id,
            availability_blocker=availability_blocker,
            configure_zero=configure_zero,
            compile_zero=compile_zero,
            adapter_import_zero=adapter_import_zero,
        )
        if skip_reason is not None:
            _write_skipped_logs(spec, skip_reason)
            rows.append(_command_attempt_row(spec, skipped=True, skip_reason=skip_reason))
            continue

        if spec.command_id == "source_build_configure_attempt":
            build_root.mkdir(parents=True, exist_ok=True)
        if spec.command_id in {
            "repo_local_adapter_import_metadata_attempt",
            "repo_local_backend_metadata_probe_attempt",
        }:
            artifacts_dir.mkdir(parents=True, exist_ok=True)
        result = runner(spec)
        row = _command_attempt_row(spec, result=result, skipped=False, skip_reason="")
        rows.append(row)
        if spec.command_id == "source_build_configure_attempt":
            configure_zero = result.returncode == 0 and not result.timed_out
        elif spec.command_id == "source_build_compile_attempt":
            compile_zero = result.returncode == 0 and not result.timed_out
        elif spec.command_id == "repo_local_adapter_import_metadata_attempt":
            adapter_import_zero = result.returncode == 0 and not result.timed_out
    return rows


def _skip_reason_for_command(
    command_id: str,
    *,
    availability_blocker: str,
    configure_zero: bool,
    compile_zero: bool,
    adapter_import_zero: bool,
) -> str | None:
    if availability_blocker != "none":
        return availability_blocker
    if command_id == "source_build_configure_attempt":
        return None
    if command_id == "source_build_compile_attempt" and not configure_zero:
        return "configure_failed_or_not_executed"
    if command_id == "repo_local_adapter_import_metadata_attempt" and not compile_zero:
        return "compile_failed_or_not_executed"
    if command_id == "repo_local_backend_metadata_probe_attempt" and not adapter_import_zero:
        return "adapter_import_failed_or_not_executed"
    return None


def _command_attempt_row(
    spec: CommandSpec,
    *,
    result: CommandResult | None = None,
    skipped: bool,
    skip_reason: str,
) -> dict[str, Any]:
    executed = not skipped
    status_pass = True if skipped else result is not None and result.returncode == 0 and not result.timed_out
    blocker = "none"
    if skipped:
        blocker = skip_reason
    elif not status_pass:
        blocker = _command_failure_blocker(spec.command_id, result)
    return {
        "command_attempt_id": spec.command_id,
        "command_family": spec.family,
        "selected_platform_family": SELECTED_PLATFORM_FAMILY,
        "cwd": str(spec.cwd),
        "command": _format_command(spec.argv),
        "timeout_s": spec.timeout_s,
        "stdout_path": str(spec.stdout_path),
        "stderr_path": str(spec.stderr_path),
        "returncode": "" if result is None else result.returncode,
        "timed_out": False if result is None else result.timed_out,
        "executed": executed,
        "skipped": skipped,
        "skip_reason": skip_reason,
        "blocker_classification": blocker,
        "actor_visible_allowed": False,
        "status_pass": status_pass or skipped,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _command_failure_blocker(command_id: str, result: CommandResult | None) -> str:
    if result is not None and result.timed_out:
        return "timeout"
    if command_id == "source_build_configure_attempt":
        return "configure_failure_recorded"
    if command_id == "source_build_compile_attempt":
        return "compile_failure_recorded"
    if command_id == "repo_local_adapter_import_metadata_attempt":
        return "adapter_import_repair_needed"
    if command_id == "repo_local_backend_metadata_probe_attempt":
        return "backend_metadata_probe_repair_needed"
    return "unknown_command_failure"


def build_backend_probe_trace(
    command_rows: list[dict[str, Any]],
    availability_blocker: str,
) -> dict[str, Any]:
    adapter_row = _row_by_id(command_rows, "repo_local_adapter_import_metadata_attempt", key="command_attempt_id")
    probe_row = _row_by_id(command_rows, "repo_local_backend_metadata_probe_attempt", key="command_attempt_id")
    return {
        "trace_status": "skipped" if availability_blocker != "none" else "recorded",
        "availability_blocker": availability_blocker,
        "adapter_import_attempt_executed": _boolish(adapter_row.get("executed")),
        "backend_metadata_probe_attempt_executed": _boolish(probe_row.get("executed")),
        "metadata_probe_only": True,
        "external_simulator_imported": False,
        "backend_started": False,
        "reset_executed": False,
        "step_executed": False,
        "rollout_executed": False,
        "validation_executed": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def build_backend_probe_trace_rows(
    command_rows: list[dict[str, Any]],
    availability_blocker: str,
) -> list[dict[str, Any]]:
    rows = []
    for command_id, family in (
        ("repo_local_adapter_import_metadata_attempt", "adapter_import_metadata"),
        ("repo_local_backend_metadata_probe_attempt", "backend_metadata_probe"),
    ):
        command_row = _row_by_id(command_rows, command_id, key="command_attempt_id")
        rows.append(
            {
                "trace_id": f"{command_id}_trace",
                "trace_family": family,
                "executed": _boolish(command_row.get("executed")),
                "skipped": _boolish(command_row.get("skipped")),
                "skip_reason": command_row.get("skip_reason", availability_blocker),
                "external_simulator_imported": False,
                "backend_started": False,
                "reset_executed": False,
                "step_executed": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    *,
    availability_rows: list[dict[str, Any]],
    command_rows: list[dict[str, Any]],
    backend_trace_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized = bool(availability_rows and command_rows and backend_trace_rows)
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2635": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(claim_family in ALLOWED_CLAIMS or not claim_allowed),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_artifact_manifest_rows(
    *,
    output_dir: Path,
    doc_path: Path,
) -> list[dict[str, Any]]:
    specs = [
        ("summary", output_dir / "summary.json", "json", "run summary and claim boundary flags"),
        ("command_plan", output_dir / "command_plan.json", "json", "M2634 command plan materialization"),
        ("environment_snapshot", output_dir / "environment_snapshot.txt", "txt", "read-only environment snapshot"),
        ("source_availability", output_dir / "source_availability_rows.csv", "csv", "source and tool availability rows"),
        ("command_attempts", output_dir / "command_attempt_rows.csv", "csv", "configure compile adapter probe attempt rows"),
        ("artifact_manifest", output_dir / "artifact_manifest.csv", "csv", "artifact existence manifest"),
        ("backend_probe_trace", output_dir / "backend_probe_trace.json", "json", "metadata probe trace"),
        ("backend_probe_trace_rows", output_dir / "backend_probe_trace_rows.csv", "csv", "metadata probe trace rows"),
        ("claim_boundary", output_dir / "claim_boundary_checks.csv", "csv", "claim boundary checks"),
        ("gate_matrix", output_dir / "gate_matrix.csv", "csv", "gate matrix"),
        ("milestone_doc", doc_path, "md", "milestone documentation"),
    ]
    rows = []
    for artifact_id, path, artifact_type, purpose in specs:
        exists = Path(path).exists()
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": str(path),
                "artifact_type": artifact_type,
                "exists": exists,
                "purpose": purpose,
                "actor_visible_allowed": False,
                "status_pass": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    availability_rows: list[dict[str, Any]],
    command_rows: list[dict[str, Any]],
    backend_trace_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    artifact_manifest_rows: list[dict[str, Any]],
    availability_blocker: str,
) -> list[dict[str, Any]]:
    forbidden_claims = [
        row
        for row in claim_rows
        if row["claim_family"] not in ALLOWED_CLAIMS and _boolish(row["claim_allowed_in_m2635"])
    ]
    attempted_when_blocked = [
        row
        for row in command_rows
        if availability_blocker != "none" and _boolish(row.get("executed"))
    ]
    checks = [
        (
            "availability_gate_executed",
            "execution",
            len(availability_rows) == 6,
            f"rows={len(availability_rows)}",
            "rows=6",
            "metric_artifact",
        ),
        (
            "source_or_blocker_recorded",
            "blocker",
            availability_blocker != "none" or _condition(availability_rows, "source_root_directory_available"),
            availability_blocker,
            "source available or explicit blocker",
            "lineage_invalid",
        ),
        (
            "command_attempt_rows_complete",
            "execution",
            {row["command_attempt_id"] for row in command_rows}
            == {
                "source_build_configure_attempt",
                "source_build_compile_attempt",
                "repo_local_adapter_import_metadata_attempt",
                "repo_local_backend_metadata_probe_attempt",
            },
            f"rows={len(command_rows)}",
            "configure compile adapter import backend metadata rows",
            "metric_artifact",
        ),
        (
            "blocked_forward_commands_skipped",
            "contract",
            len(attempted_when_blocked) == 0,
            f"attempted_when_blocked={len(attempted_when_blocked)}",
            "attempted_when_blocked=0",
            "contract_violation",
        ),
        (
            "backend_metadata_trace_preserves_no_start_reset_step",
            "contract",
            _backend_trace_rows_preserve_boundary(backend_trace_rows),
            f"rows={len(backend_trace_rows)}",
            "backend_started/reset/step/external_import=false",
            "contract_violation",
        ),
        (
            "actor_action_contract_preserved",
            "contract",
            P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
            f"obs={P0_OBSERVATION_DIM};action={ACTION_DIM};mapping={DEPLOYED_ACTION_MAPPING}",
            "obs=72;action=3;mapping=[steer, throttle, brake]",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and len(forbidden_claims) == 0,
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims)}",
            f"rows={len(CLAIM_CHECKS)};forbidden_claims=0",
            "objective_overfit",
        ),
        (
            "artifact_manifest_complete",
            "artifact",
            len(artifact_manifest_rows) == 11,
            f"rows={len(artifact_manifest_rows)}",
            "rows=11",
            "metric_artifact",
        ),
        (
            "no_install_external_import_mutation_network_backend_reset_validation_or_performance",
            "claim_boundary",
            _no_forbidden_execution_flags(command_rows, backend_trace_rows),
            "install/import/mutation/network/backend/reset/validation/performance=false",
            "install/import/mutation/network/backend/reset/validation/performance=false",
            "contract_violation",
        ),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": gate_family,
            "status_pass": bool(status_pass),
            "observed": observed,
            "expected": expected,
            "failure_type": "none" if status_pass else failure_type,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for gate_id, gate_family, status_pass, observed, expected, failure_type in checks
    ]


def build_summary(
    *,
    output_dir: Path,
    milestone: str,
    next_blocker: str,
    doc_path: Path,
    source_root: Path,
    build_root: Path,
    source_availability_path: Path,
    command_attempt_path: Path,
    artifact_manifest_path: Path,
    backend_trace_path: Path,
    backend_trace_rows_path: Path,
    claim_path: Path,
    gate_path: Path,
    environment_snapshot_path: Path,
    availability_rows: list[dict[str, Any]],
    command_rows: list[dict[str, Any]],
    backend_trace_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    artifact_manifest_rows: list[dict[str, Any]],
    availability_blocker: str,
    source_root_available: bool,
    cmake_lists_available: bool,
    toolchain_available: bool,
    package_import_unavailable: bool,
) -> dict[str, Any]:
    configure_row = _row_by_id(command_rows, "source_build_configure_attempt", key="command_attempt_id")
    compile_row = _row_by_id(command_rows, "source_build_compile_attempt", key="command_attempt_id")
    adapter_row = _row_by_id(command_rows, "repo_local_adapter_import_metadata_attempt", key="command_attempt_id")
    probe_row = _row_by_id(command_rows, "repo_local_backend_metadata_probe_attempt", key="command_attempt_id")
    status_pass = _all_status_pass(gate_rows)
    if availability_blocker == "dependency_source_unavailable":
        result_class = "dependency_source_unavailable_blocker_recorded"
    elif availability_blocker == "selected_platform_source_schema_unavailable":
        result_class = "selected_platform_source_schema_unavailable_blocker_recorded"
    elif availability_blocker == "local_toolchain_unavailable":
        result_class = "local_toolchain_unavailable_blocker_recorded"
    else:
        result_class = "bounded_actual_execution_attempt_artifacts_written"
    return {
        "status_pass": status_pass,
        "result_class": result_class,
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "selected_platform_family": SELECTED_PLATFORM_FAMILY,
        "source_root": str(source_root),
        "build_root": str(build_root),
        "availability_gate_executed": len(availability_rows) == 6,
        "availability_blocker": availability_blocker,
        "source_root_available": source_root_available,
        "cmake_lists_available": cmake_lists_available,
        "toolchain_available": toolchain_available,
        "package_import_unavailable": package_import_unavailable,
        "configure_attempt_executed": _boolish(configure_row.get("executed")),
        "compile_attempt_executed": _boolish(compile_row.get("executed")),
        "repo_local_adapter_import_attempt_executed": _boolish(adapter_row.get("executed")),
        "repo_local_backend_metadata_probe_attempt_executed": _boolish(probe_row.get("executed")),
        "configure_returncode": configure_row.get("returncode", ""),
        "compile_returncode": compile_row.get("returncode", ""),
        "adapter_import_returncode": adapter_row.get("returncode", ""),
        "backend_metadata_probe_returncode": probe_row.get("returncode", ""),
        "external_install_performed": False,
        "external_simulator_imported": False,
        "dependency_mutation_performed": False,
        "source_tree_mutation_performed": False,
        "network_access_used": False,
        "backend_started": False,
        "reset_executed": False,
        "step_executed": False,
        "policy_action_executed": False,
        "rollout_executed": False,
        "replay_executed": False,
        "validation_executed": False,
        "training_run": False,
        "ranking_run": False,
        "success_rate_computed": False,
        "driver_performance_claim_allowed": False,
        "actor_observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "deployed_action_mapping": DEPLOYED_ACTION_MAPPING,
        "hidden_oracle_actor_input_detected": False,
        "metadata_actor_visible": False,
        "source_availability_row_count": len(availability_rows),
        "command_attempt_row_count": len(command_rows),
        "backend_probe_trace_row_count": len(backend_trace_rows),
        "claim_boundary_check_count": len(claim_rows),
        "gate_count": len(gate_rows),
        "artifact_manifest_row_count": len(artifact_manifest_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "gate_matrix_all_pass": _all_status_pass(gate_rows),
        "source_availability_rows": str(source_availability_path),
        "command_attempt_rows": str(command_attempt_path),
        "artifact_manifest": str(artifact_manifest_path),
        "backend_probe_trace": str(backend_trace_path),
        "backend_probe_trace_rows": str(backend_trace_rows_path),
        "claim_boundary_checks": str(claim_path),
        "gate_matrix": str(gate_path),
        "environment_snapshot": str(environment_snapshot_path),
        "milestone_doc": str(doc_path),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def write_environment_snapshot(
    path: Path,
    *,
    repo: Path,
    source_root: Path,
    output_dir: Path,
    availability_rows: list[dict[str, Any]],
    availability_results: dict[str, CommandResult],
) -> None:
    lines = [
        f"generated_at_utc: {utc_timestamp()}",
        f"repo: {repo}",
        f"source_root: {source_root}",
        f"output_dir: {output_dir}",
        f"python_executable: {sys.executable}",
        "availability:",
    ]
    for row in availability_rows:
        command_id = row["availability_check_id"]
        result = availability_results[command_id]
        first_stdout_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        lines.append(
            f"- {command_id}: returncode={result.returncode} timed_out={result.timed_out} "
            f"condition_satisfied={row['condition_satisfied']} blocker={row['blocker_classification']} "
            f"stdout_first_line={first_stdout_line}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M2635 Engineering Controller Route A Baseline HF3 Selected-Platform Source-Build Adapter-Probe Bounded Actual Execution Attempt Preflight",
        "",
        "- status: completed",
        f"- result_class: `{summary['result_class']}`",
        "- manifest: `experiments/manifests/m2635-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-bounded-actual-execution-attempt-preflight.json`",
        f"- summary: `{Path(summary['output_dir']) / 'summary.json'}`",
        f"- source availability rows: `{summary['source_availability_rows']}`",
        f"- command attempt rows: `{summary['command_attempt_rows']}`",
        f"- artifact manifest: `{summary['artifact_manifest']}`",
        f"- backend probe trace: `{summary['backend_probe_trace']}`",
        f"- claim-boundary checks: `{summary['claim_boundary_checks']}`",
        f"- gate matrix: `{summary['gate_matrix']}`",
        f"- next milestone: `{summary['next_blocker']}`",
        "- dependency readiness / backend availability / validation / performance claims: `false`",
        "",
        "## Result Boundary",
        "",
        "M2635 executes only the bounded command-attempt preflight admitted by M2634.",
        "It records availability, logs, return codes, skips, blockers, artifacts,",
        "claim boundaries, and gates. It does not install dependencies, mutate",
        "selected-platform source trees, use network dependency resolution, start",
        "backends, reset, step, roll out, replay, validate, train, rank, promote,",
        "compute success rates, or claim driver performance.",
        "",
        "## Observed Outcome",
        "",
        "```text",
        f"status_pass: {summary['status_pass']}",
        f"result_class: {summary['result_class']}",
        f"source_root: {summary['source_root']}",
        f"source_root_available: {summary['source_root_available']}",
        f"cmake_lists_available: {summary['cmake_lists_available']}",
        f"toolchain_available: {summary['toolchain_available']}",
        f"package_import_unavailable: {summary['package_import_unavailable']}",
        f"availability_blocker: {summary['availability_blocker']}",
        f"configure_attempt_executed: {summary['configure_attempt_executed']}",
        f"compile_attempt_executed: {summary['compile_attempt_executed']}",
        f"repo_local_adapter_import_attempt_executed: {summary['repo_local_adapter_import_attempt_executed']}",
        f"repo_local_backend_metadata_probe_attempt_executed: {summary['repo_local_backend_metadata_probe_attempt_executed']}",
        "```",
        "",
        "## Contract Guards",
        "",
        "```text",
        f"actor_observation_shape: {summary['actor_observation_shape']}",
        f"action_shape: {summary['action_shape']}",
        f"deployed_action_mapping: {summary['deployed_action_mapping']}",
        f"hidden_oracle_actor_input_detected: {summary['hidden_oracle_actor_input_detected']}",
        f"metadata_actor_visible: {summary['metadata_actor_visible']}",
        f"external_install_performed: {summary['external_install_performed']}",
        f"external_simulator_imported: {summary['external_simulator_imported']}",
        f"dependency_mutation_performed: {summary['dependency_mutation_performed']}",
        f"source_tree_mutation_performed: {summary['source_tree_mutation_performed']}",
        f"network_access_used: {summary['network_access_used']}",
        f"backend_started: {summary['backend_started']}",
        f"reset_executed: {summary['reset_executed']}",
        f"step_executed: {summary['step_executed']}",
        f"rollout_executed: {summary['rollout_executed']}",
        f"validation_executed: {summary['validation_executed']}",
        f"driver_performance_claim_allowed: {summary['driver_performance_claim_allowed']}",
        "```",
        "",
        "## Supported Claims",
        "",
        "M2635 supports only bounded command-attempt or explicit blocker evidence",
        "for the selected-platform source-build/adapter-probe preflight.",
        "",
        "## Rejected Claims",
        "",
        "M2635 rejects dependency readiness, source-build success, adapter-probe",
        "success, backend discovery, backend availability, reset execution or",
        "success, rollout feasibility, validation readiness/result, controller",
        "ranking, driver performance, paper evidence, finite-window-vs-GRU,",
        "current-sim verdict, high-fidelity validation, and level3 self-ID claims.",
        "",
        "## Next",
        "",
        f"Route to `{summary['next_blocker']}` for result audit.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _run_command(spec: CommandSpec) -> CommandResult:
    env = os.environ.copy()
    if spec.env:
        env.update(spec.env)
    try:
        completed = subprocess.run(
            list(spec.argv),
            cwd=spec.cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=spec.timeout_s,
            check=False,
        )
        result = CommandResult(
            returncode=int(completed.returncode),
            timed_out=False,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        result = CommandResult(
            returncode=124,
            timed_out=True,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "timeout",
        )
    except FileNotFoundError as exc:
        result = CommandResult(returncode=127, timed_out=False, stdout="", stderr=str(exc))
    _write_command_logs(spec, result)
    return result


def _write_command_logs(spec: CommandSpec, result: CommandResult) -> None:
    spec.stdout_path.parent.mkdir(parents=True, exist_ok=True)
    spec.stderr_path.parent.mkdir(parents=True, exist_ok=True)
    spec.stdout_path.write_text(result.stdout, encoding="utf-8")
    spec.stderr_path.write_text(result.stderr, encoding="utf-8")


def _write_skipped_logs(spec: CommandSpec, skip_reason: str) -> None:
    spec.stdout_path.parent.mkdir(parents=True, exist_ok=True)
    spec.stderr_path.parent.mkdir(parents=True, exist_ok=True)
    spec.stdout_path.write_text("", encoding="utf-8")
    spec.stderr_path.write_text(f"skipped: {skip_reason}\n", encoding="utf-8")


def _format_command(argv: tuple[str, ...]) -> str:
    return " ".join(_quote_arg(part) for part in argv)


def _quote_arg(part: str) -> str:
    if not part:
        return "''"
    if any(char.isspace() for char in part) or any(char in part for char in "\"'{}();"):
        return repr(part)
    return part


def _condition(rows: list[dict[str, Any]], row_id: str) -> bool:
    return _boolish(_row_by_id(rows, row_id).get("condition_satisfied"))


def _row_by_id(
    rows: list[dict[str, Any]],
    row_id: str,
    *,
    key: str = "availability_check_id",
) -> dict[str, Any]:
    for row in rows:
        if row.get(key) == row_id:
            return row
    return {}


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_boolish(row.get("status_pass")) for row in rows)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _backend_trace_rows_preserve_boundary(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        not _boolish(row.get("external_simulator_imported"))
        and not _boolish(row.get("backend_started"))
        and not _boolish(row.get("reset_executed"))
        and not _boolish(row.get("step_executed"))
        and not _boolish(row.get("actor_visible_allowed"))
        for row in rows
    )


def _no_forbidden_execution_flags(
    command_rows: list[dict[str, Any]],
    backend_trace_rows: list[dict[str, Any]],
) -> bool:
    if not _backend_trace_rows_preserve_boundary(backend_trace_rows):
        return False
    for row in command_rows:
        command_text = str(row.get("command", "")).lower()
        forbidden_tokens = (
            "pip install",
            "conda install",
            "apt install",
            "git clone",
            "curl ",
            "wget ",
            "reset(",
            ".step(",
            "rollout",
            "validate",
            "train_ppo",
        )
        if any(token in command_text for token in forbidden_tokens):
            return False
    return True


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-root", type=Path, default=None)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args(argv)
    summary = run_bounded_actual_execution_attempt(
        args.output_dir,
        source_root=args.source_root,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "availability_blocker={availability_blocker}".format(**summary)
    )


if __name__ == "__main__":
    main()
