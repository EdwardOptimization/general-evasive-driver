"""Read-only Chrono source availability preflight for Route C/HF3.

M2881 checks only local metadata for the fixed Chrono source path. It does not
fetch, configure, build, import, start a backend, reset, step, or run policy
actions.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Any

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json


DEFAULT_MILESTONE = "m2881-engineering-controller-route-c-hf3-chrono-source-availability-preflight"
DEFAULT_NEXT_BLOCKER = "m2882-engineering-controller-route-c-hf3-chrono-source-availability-result-audit"
DEFAULT_OUTPUT_DIR = Path("runs/m2881_engineering_controller_route_c_hf3_chrono_source_availability_preflight")
DEFAULT_M2880_DESIGN = Path(
    "docs/m2880-engineering-controller-route-c-hf3-chrono-dependency-acquisition-manifest-design.md"
)
DEFAULT_SOURCE_ROOT = Path("/home/quyaonan/workspace/hf_backends/chrono/10.0.0/source")
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2882-engineering-controller-route-c-hf3-chrono-source-availability-result-audit.json"
)
DEFAULT_EXPECTED_TAG = "10.0.0"
DEFAULT_EXPECTED_COMMIT_PREFIX = "9faf13d"

SOURCE_FIELDNAMES = [
    "row_id",
    "check_family",
    "path",
    "exists",
    "status",
    "observed",
    "expected",
    "source_available",
    "failure_type",
    "claim_scope",
    "blocked_interpretation",
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
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "claim_allowed",
    "evidence_required_before_claim",
    "claim_boundary",
]

CLAIM_SCOPE = (
    "Read-only Route C HF3 Chrono source availability preflight only; no network fetch, clone, "
    "package install, configure, build, install, import, link probe, backend start, reset, step, "
    "policy action, rollout, replay, validation, training, ranking, promotion, package publication, "
    "driver-performance, paper, current-sim, high-fidelity validation, full-driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "dependency execution readiness, source-build readiness, configure success, build success, "
    "install success, import/link success, backend availability, reset feasibility, rollout "
    "feasibility, validation readiness/result, driver performance, paper evidence, current-sim "
    "verdict, high-fidelity validation, full-driver completion, or self-ID evidence"
)

FALSE_CLAIM_FLAGS = {
    "external_directory_created": False,
    "external_dependency_mutation_performed": False,
    "external_source_fetched": False,
    "network_access_used": False,
    "apt_install_run": False,
    "pip_install_run": False,
    "system_python_modified": False,
    "chrono_configure_run": False,
    "chrono_build_run": False,
    "chrono_install_run": False,
    "chrono_import_run": False,
    "cpp_link_probe_run": False,
    "backend_started": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "package_published": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "full_ideal_driver_completion_claim_made": False,
}


def _resolve_no_create(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _run_git(source_root: Path, args: list[str]) -> tuple[bool, str]:
    process = subprocess.run(
        ["git", "-C", str(source_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        return False, (process.stderr or process.stdout).strip()
    return True, process.stdout.strip()


def _toolchain_status() -> dict[str, Any]:
    compiler_candidates = ["c++", "g++", "clang++"]
    compiler_paths = {candidate: shutil.which(candidate) for candidate in compiler_candidates}
    selected_compiler = next((path for path in compiler_paths.values() if path), None)
    return {
        "cmake_path": shutil.which("cmake"),
        "compiler_candidates": compiler_paths,
        "selected_compiler": selected_compiler,
        "cmake_command_available": shutil.which("cmake") is not None,
        "cxx_command_available": selected_compiler is not None,
    }


def _check_source(
    *,
    source_root: Path,
    repo_root: Path,
    expected_tag: str,
    expected_commit_prefix: str,
) -> dict[str, Any]:
    resolved_source = _resolve_no_create(source_root)
    resolved_repo = _resolve_no_create(repo_root)
    source_exists = source_root.exists()
    source_is_dir = source_root.is_dir()
    source_inside_repo = _is_relative_to(resolved_source, resolved_repo)
    cmake_lists = source_root / "CMakeLists.txt"
    cmake_lists_exists = cmake_lists.exists()
    git_metadata_exists = (source_root / ".git").exists()

    git_head: str | None = None
    git_head_error: str | None = None
    git_commit_prefix_matches: bool | None = None
    git_tags: list[str] = []
    git_tag_matches: bool | None = None
    if source_exists and source_is_dir and git_metadata_exists:
        ok, output = _run_git(source_root, ["rev-parse", "HEAD"])
        if ok:
            git_head = output
            git_commit_prefix_matches = output.startswith(expected_commit_prefix)
        else:
            git_head_error = output
            git_commit_prefix_matches = False
        ok, output = _run_git(source_root, ["tag", "--points-at", "HEAD"])
        if ok:
            git_tags = [line.strip() for line in output.splitlines() if line.strip()]
            git_tag_matches = expected_tag in git_tags
        else:
            git_tag_matches = False

    source_available = (
        source_exists
        and source_is_dir
        and cmake_lists_exists
        and not source_inside_repo
        and (git_commit_prefix_matches is not False)
        and (git_tag_matches is not False)
    )
    if source_available:
        outcome = "source_available_claim_safe"
        failure_type = "none"
    else:
        outcome = "source_unavailable_claim_safe"
        failure_type = "source_unavailable"

    return {
        "source_root": str(source_root),
        "resolved_source_root": str(resolved_source),
        "repo_root": str(repo_root),
        "resolved_repo_root": str(resolved_repo),
        "source_exists": source_exists,
        "source_is_dir": source_is_dir,
        "source_inside_repo": source_inside_repo,
        "cmake_lists_path": str(cmake_lists),
        "cmake_lists_exists": cmake_lists_exists,
        "git_metadata_exists": git_metadata_exists,
        "git_head": git_head,
        "git_head_error": git_head_error,
        "git_commit_prefix_matches": git_commit_prefix_matches,
        "git_tags": git_tags,
        "git_tag_matches": git_tag_matches,
        "expected_tag": expected_tag,
        "expected_commit_prefix": expected_commit_prefix,
        "source_available": source_available,
        "outcome": outcome,
        "failure_type": failure_type,
    }


def _source_row(
    row_id: str,
    check_family: str,
    path: str,
    exists: bool | None,
    status: str,
    observed: Any,
    expected: Any,
    source_available: bool,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "check_family": check_family,
        "path": path,
        "exists": "" if exists is None else bool(exists),
        "status": status,
        "observed": observed,
        "expected": expected,
        "source_available": bool(source_available),
        "failure_type": failure_type,
        "claim_scope": CLAIM_SCOPE,
        "blocked_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_source_availability_rows(source: dict[str, Any], toolchain: dict[str, Any]) -> list[dict[str, Any]]:
    source_available = bool(source["source_available"])
    failure_type = str(source["failure_type"])
    return [
        _source_row(
            "m2881_source_root_exists",
            "source_root",
            str(source["source_root"]),
            bool(source["source_exists"]),
            "present" if source["source_exists"] else "missing",
            bool(source["source_exists"]),
            True,
            source_available,
            failure_type if not source["source_exists"] else "none",
        ),
        _source_row(
            "m2881_source_root_is_directory",
            "source_root",
            str(source["source_root"]),
            bool(source["source_is_dir"]) if source["source_exists"] else None,
            "directory" if source["source_is_dir"] else "not_directory_or_missing",
            bool(source["source_is_dir"]),
            True,
            source_available,
            failure_type if not source["source_is_dir"] else "none",
        ),
        _source_row(
            "m2881_cmake_lists_exists",
            "source_file",
            str(source["cmake_lists_path"]),
            bool(source["cmake_lists_exists"]),
            "present" if source["cmake_lists_exists"] else "missing",
            bool(source["cmake_lists_exists"]),
            True,
            source_available,
            failure_type if not source["cmake_lists_exists"] else "none",
        ),
        _source_row(
            "m2881_source_outside_repo",
            "path_boundary",
            str(source["resolved_source_root"]),
            None,
            "outside_repo" if not source["source_inside_repo"] else "inside_repo",
            not source["source_inside_repo"],
            True,
            source_available,
            failure_type if source["source_inside_repo"] else "none",
        ),
        _source_row(
            "m2881_git_metadata",
            "optional_git_metadata",
            str(Path(str(source["source_root"])) / ".git"),
            bool(source["git_metadata_exists"]),
            "available" if source["git_metadata_exists"] else "not_available",
            bool(source["git_metadata_exists"]),
            "optional",
            source_available,
            "none" if not source["git_metadata_exists"] else failure_type,
        ),
        _source_row(
            "m2881_git_head_prefix",
            "optional_git_metadata",
            str(source["source_root"]),
            bool(source["git_head"] is not None),
            _git_prefix_status(source),
            source["git_head"] or source["git_head_error"] or "",
            source["expected_commit_prefix"],
            source_available,
            "none" if source["git_commit_prefix_matches"] is not False else failure_type,
        ),
        _source_row(
            "m2881_git_tag_points_at_head",
            "optional_git_metadata",
            str(source["source_root"]),
            bool(source["git_metadata_exists"]),
            _git_tag_status(source),
            " ".join(source["git_tags"]),
            source["expected_tag"],
            source_available,
            "none" if source["git_tag_matches"] is not False else failure_type,
        ),
        _source_row(
            "m2881_cmake_command_available",
            "toolchain_metadata",
            "cmake",
            toolchain["cmake_command_available"],
            "available" if toolchain["cmake_command_available"] else "missing",
            toolchain["cmake_path"] or "",
            "available",
            source_available,
            "none" if toolchain["cmake_command_available"] else "toolchain_missing",
        ),
        _source_row(
            "m2881_cxx_command_available",
            "toolchain_metadata",
            "c++|g++|clang++",
            toolchain["cxx_command_available"],
            "available" if toolchain["cxx_command_available"] else "missing",
            toolchain["selected_compiler"] or "",
            "available",
            source_available,
            "none" if toolchain["cxx_command_available"] else "toolchain_missing",
        ),
        _source_row(
            "m2881_external_mutation_guard",
            "mutation_boundary",
            str(Path(str(source["source_root"])).parent),
            None,
            "not_mutated",
            False,
            False,
            source_available,
            "none",
        ),
    ]


def _git_prefix_status(source: dict[str, Any]) -> str:
    if not source["git_metadata_exists"]:
        return "not_checked_no_git_metadata"
    if source["git_commit_prefix_matches"] is True:
        return "matches_expected_prefix"
    if source["git_commit_prefix_matches"] is False:
        return "mismatch_or_unreadable"
    return "unknown"


def _git_tag_status(source: dict[str, Any]) -> str:
    if not source["git_metadata_exists"]:
        return "not_checked_no_git_metadata"
    if source["git_tag_matches"] is True:
        return "tag_points_at_head"
    if source["git_tag_matches"] is False:
        return "tag_missing_or_unreadable"
    return "unknown"


def build_gate_rows(
    *,
    source: dict[str, Any],
    toolchain: dict[str, Any],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    rows = [
        _gate_row(
            "m2881_gate_design_doc_present",
            "lineage",
            True,
            "read",
            "read",
            "none",
        ),
        _gate_row(
            "m2881_gate_source_root_accounted",
            "source_availability",
            True,
            source["source_exists"],
            "accounted",
            "none",
        ),
        _gate_row(
            "m2881_gate_cmake_lists_accounted",
            "source_availability",
            True,
            source["cmake_lists_exists"],
            "accounted",
            "none",
        ),
        _gate_row(
            "m2881_gate_repo_boundary_accounted",
            "path_boundary",
            True,
            "outside_repo" if not source["source_inside_repo"] else "inside_repo",
            "accounted",
            "none" if not source["source_inside_repo"] else "source_unavailable",
        ),
        _gate_row(
            "m2881_gate_git_metadata_accounted",
            "optional_git_metadata",
            True,
            _git_prefix_status(source),
            "accounted_if_available",
            "none" if source["git_commit_prefix_matches"] is not False else "source_unavailable",
        ),
        _gate_row(
            "m2881_gate_toolchain_metadata_accounted",
            "toolchain_metadata",
            True,
            {
                "cmake": toolchain["cmake_command_available"],
                "cxx": toolchain["cxx_command_available"],
            },
            "accounted",
            "none",
        ),
        _gate_row(
            "m2881_gate_no_external_mutation",
            "mutation_boundary",
            True,
            False,
            False,
            "none",
        ),
        _gate_row(
            "m2881_gate_no_forbidden_execution",
            "claim_boundary",
            True,
            False,
            False,
            "none",
        ),
        _gate_row(
            "m2881_gate_follow_up_audit_manifest_registered",
            "process",
            follow_up_manifest.exists(),
            str(follow_up_manifest),
            "present",
            "lineage_invalid" if not follow_up_manifest.exists() else "none",
        ),
    ]
    return rows


def _gate_row(
    gate_id: str,
    gate_family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": gate_family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    allowed = {
        "source_availability_outcome": True,
        "result_audit_admission": True,
    }
    blocked = {
        "dependency_execution_readiness": "accepted source availability audit plus later configure/build/install/link/reset gates",
        "source_build_readiness": "accepted source availability audit and explicit configure manifest",
        "adapter_probe_readiness": "accepted install/link audit",
        "reset_feasibility": "accepted adapter/link audit and reset manifest",
        "rollout_feasibility": "accepted reset and manual step audits",
        "validation_readiness": "accepted policy smoke and validation manifest",
        "driver_performance": "measured validation and promotion evidence",
        "paper_evidence": "Route B controller-family comparison evidence",
        "high_fidelity_validation": "HF3 validation pilot after source/build/reset/step/policy smoke gates",
        "self_id": "Route B self-ID proof gates",
    }
    for claim, claim_allowed in allowed.items():
        rows.append(
            {
                "claim_id": f"m2881_claim_{claim}",
                "claim_family": claim,
                "claim_made": True,
                "claim_allowed": claim_allowed,
                "evidence_required_before_claim": "M2881 summary and source availability rows",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    for claim, required in blocked.items():
        rows.append(
            {
                "claim_id": f"m2881_claim_{claim}",
                "claim_family": claim,
                "claim_made": False,
                "claim_allowed": False,
                "evidence_required_before_claim": required,
                "claim_boundary": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_summary(
    *,
    source: dict[str, Any],
    toolchain: dict[str, Any],
    source_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    output_dir: Path,
    follow_up_manifest: Path,
    m2880_design: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and not any(FALSE_CLAIM_FLAGS.values()))
    toolchain_failure_type = (
        "none"
        if toolchain["cmake_command_available"] and toolchain["cxx_command_available"]
        else "toolchain_missing"
    )
    return {
        "milestone": DEFAULT_MILESTONE,
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "decision": "route_to_m2882_chrono_source_availability_result_audit",
        "outcome": source["outcome"] if status_pass else "preflight_failed_claim_safe",
        "source_available": bool(source["source_available"]),
        "source_failure_type": source["failure_type"],
        "toolchain_failure_type": toolchain_failure_type,
        "source_root": source["source_root"],
        "resolved_source_root": source["resolved_source_root"],
        "source_root_exists": source["source_exists"],
        "source_root_is_dir": source["source_is_dir"],
        "source_root_inside_repo": source["source_inside_repo"],
        "cmake_lists_exists": source["cmake_lists_exists"],
        "git_metadata_exists": source["git_metadata_exists"],
        "git_head": source["git_head"],
        "git_head_error": source["git_head_error"],
        "expected_commit_prefix": source["expected_commit_prefix"],
        "git_commit_prefix_matches": source["git_commit_prefix_matches"],
        "expected_tag": source["expected_tag"],
        "git_tags": source["git_tags"],
        "git_tag_matches": source["git_tag_matches"],
        "cmake_command_available": toolchain["cmake_command_available"],
        "cmake_path": toolchain["cmake_path"],
        "cxx_command_available": toolchain["cxx_command_available"],
        "selected_compiler": toolchain["selected_compiler"],
        "source_availability_row_count": len(source_rows),
        "gate_row_count": len(gate_rows),
        "claim_row_count": len(claim_rows),
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "m2880_design": str(m2880_design),
        "artifacts": {
            "summary": str(output_dir / "summary.json"),
            "source_availability_rows": str(output_dir / "source_availability_rows.csv"),
            "gate_rows": str(output_dir / "gate_rows.csv"),
            "claim_rows": str(output_dir / "claim_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
        },
        "false_claim_flags": FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_run_state(source: dict[str, Any], toolchain: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "milestone": DEFAULT_MILESTONE,
        "read_only_checks": [
            "source_root_exists",
            "cmake_lists_exists",
            "repo_boundary",
            "optional_git_metadata",
            "toolchain_command_availability",
        ],
        "forbidden_actions_executed": FALSE_CLAIM_FLAGS,
        "source": source,
        "toolchain": toolchain,
        "summary": summary,
    }


def build_follow_up_manifest(
    *,
    output_dir: Path,
    m2880_design: Path,
    source_root: Path,
    expected_tag: str,
    expected_commit_prefix: str,
) -> dict[str, Any]:
    summary_path = output_dir / "summary.json"
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "hypothesis": (
            "A bounded result audit can accept or reject the M2881 read-only Chrono source "
            "availability artifact before any configure build install link/import reset or validation gate."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "source_availability_rows.csv"),
                str(output_dir / "gate_rows.csv"),
                str(m2880_design),
                "docs/m2879-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-result-synthesis.md",
                "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md",
                "docs/m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit.md",
            ],
            "parent_config": [
                "experiments/manifests/m2881-engineering-controller-route-c-hf3-chrono-source-availability-preflight.json",
                "experiments/manifests/m2880-engineering-controller-route-c-hf3-chrono-dependency-acquisition-manifest-design.json",
            ],
            "parent_objective": [
                "audit the claim safety and completeness of the read-only Chrono source availability artifact"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2880-engineering-controller-route-c-hf3-chrono-dependency-acquisition-manifest-design",
            ],
            "blocked_by": [
                "M2881 source availability outcome must be audited before any configure build install link/import reset manual step policy smoke or validation gate",
                "M2638/M2836 still forbid selected-platform HF3 execution until source dependency evidence is accepted as claim-safe",
            ],
            "supersedes": [
                "direct configure/build/install route without source availability audit",
                "interpreting M2881 source rows as high-fidelity validation or driver-performance evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2882 must audit M2881 summary source availability rows gate rows and claim rows",
            "M2882 must classify the outcome as source_available_claim_safe source_unavailable_claim_safe or preflight_failed_claim_safe",
            f"M2882 must preserve fixed source root {source_root} expected tag {expected_tag} and expected commit prefix {expected_commit_prefix}",
            "M2882 must preserve no external dependency mutation and no forbidden Chrono configure build install import reset step rollout or validation",
            "M2882 must not claim dependency execution readiness source-build readiness adapter-probe readiness reset feasibility validation readiness driver performance high-fidelity validation paper current-sim full-driver or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not fetch or clone Chrono source",
            "do not create external dependency directories",
            "do not install packages",
            "do not configure Chrono",
            "do not build Chrono",
            "do not install Chrono",
            "do not import pychrono or projectchrono",
            "do not run a C++ link probe",
            "do not start a backend",
            "do not reset step rollout replay validate train rank promote or publish a package",
            "do not change actor input or action contract",
            "do not claim high-fidelity validation driver performance paper current-sim full-driver or self-ID evidence",
        ],
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_c_hf3_chrono_source_availability_preflight",
            "evidence_axis": "route_c_hf3_chrono_source_availability_result_audit",
            "evidence_increment": "audits the first read-only source availability artifact before any later dependency gate is admitted",
            "claim_scope": "Result audit only; no dependency acquisition execution source build import reset rollout validation performance paper high-fidelity full-driver or self-ID claim",
            "stop_condition": [
                "stop if M2881 artifact is missing incomplete or mutates external dependency directories",
                "stop if M2882 would admit configure without source availability and claim-boundary acceptance",
                "stop if source rows are interpreted as validation performance high-fidelity or self-ID evidence",
            ],
            "fallback_plan": [
                "keep Route C/HF3 stopped if source is unavailable or artifact incomplete",
                "route to a bounded configure design only if source availability is accepted claim-safe",
                "route away from Route C if dependency acquisition cannot remain bounded and claim-safe",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2881 writes read-only source availability artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "M2881 source availability result audit",
            "admission_evidence": [
                "M2881 summary and source availability rows exist",
                "M2880 admits only ordered source availability before later dependency gates",
                "M2638/M2836 require accepted source/dependency evidence before selected-platform HF3 execution",
            ],
            "blocked_shortcuts": [
                "no network fetch clone configure build install import reset step rollout validation",
                "no policy action training replay PPO ranking winner selection or promotion",
                "no actor input expansion or action contract change",
                "no high-fidelity validation driver-performance paper current-sim full-driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "M2882 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if audit admits it",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "M2881 outcome and claim boundaries are accepted or rejected",
                "one next route is selected: configure design, keep stopped, or route away",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2882 audits source availability only and does not test history necessity or current-frame substitution.",
            "history_necessity_tests": [
                "None in M2882; Route B finite-window GRU and self-ID proof gates remain separate."
            ],
            "temporal_evidence_window": "M2880-M2881 Route C Chrono dependency manifest and source availability gate.",
            "negative_result_policy": "Preserve missing or incompatible source as a dependency blocker rather than weakening HF3 gates.",
            "allowed_claims": [
                "M2881 source availability result audit",
                "bounded follow-up route or stop decision",
                "no driver-performance paper current-sim high-fidelity validation full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "low",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new read-only source availability artifact before allowing another dependency-process step",
            "paper_verdict_delta": "no paper verdict; Route B evidence remains separate",
            "must_synthesize_if": [
                "M2882 cannot classify M2881 outcome",
                "M2882 would admit configure/build/import/reset without source-availability acceptance",
                "M2882 would claim high-fidelity validation driver performance paper current-sim full-driver or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "audit accepts or rejects M2881 artifact completeness and claim safety",
            "audit preserves source availability as dependency-process evidence only",
            "audit selects exactly one bounded next route or keeps Route C/HF3 stopped",
        ],
        "failure_criteria": [
            "M2882 fetches clones installs configures builds imports resets steps rolls out validates trains ranks promotes or mutates dependencies",
            "M2882 changes actor input or action contract",
            "M2882 weakens M2638/M2836 or hides M2877/M2878 diagnostic-only boundaries",
            "M2882 claims validation readiness/result high-fidelity validation driver performance paper current-sim full-driver or self-ID evidence",
        ],
        "decision_rule": (
            "Pass only if M2882 writes a claim-safe audit of M2881 source availability and selects one bounded next route "
            "without dependency execution or high-fidelity validation claims."
        ),
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{DEFAULT_NEXT_BLOCKER}.md", "type": "md"}],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(m2880_design),
            "docs/m2879-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-result-synthesis.md",
            "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md",
            "docs/m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit.md",
        ],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "m2883-engineering-controller-route-c-hf3-chrono-next-dependency-gate-or-stop-design",
    }


def write_preflight_artifacts(
    *,
    m2880_design: Path,
    source_root: Path,
    expected_tag: str,
    expected_commit_prefix: str,
    output_dir: Path,
    follow_up_manifest: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo = repo_root or Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not m2880_design.exists():
        raise FileNotFoundError(f"missing M2880 design: {m2880_design}")

    source = _check_source(
        source_root=source_root,
        repo_root=repo,
        expected_tag=expected_tag,
        expected_commit_prefix=expected_commit_prefix,
    )
    toolchain = _toolchain_status()
    write_json(
        follow_up_manifest,
        build_follow_up_manifest(
            output_dir=output_dir,
            m2880_design=m2880_design,
            source_root=source_root,
            expected_tag=expected_tag,
            expected_commit_prefix=expected_commit_prefix,
        ),
    )

    source_rows = build_source_availability_rows(source, toolchain)
    claim_rows = build_claim_rows()
    gate_rows = build_gate_rows(source=source, toolchain=toolchain, follow_up_manifest=follow_up_manifest)
    summary = build_summary(
        source=source,
        toolchain=toolchain,
        source_rows=source_rows,
        gate_rows=gate_rows,
        claim_rows=claim_rows,
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        m2880_design=m2880_design,
    )

    write_csv_rows(output_dir / "source_availability_rows.csv", source_rows, SOURCE_FIELDNAMES)
    write_csv_rows(output_dir / "gate_rows.csv", gate_rows, GATE_FIELDNAMES)
    write_csv_rows(output_dir / "claim_rows.csv", claim_rows, CLAIM_FIELDNAMES)
    write_json(output_dir / "run_state.json", build_run_state(source, toolchain, summary))
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2880-design", type=Path, default=DEFAULT_M2880_DESIGN)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--expected-tag", default=DEFAULT_EXPECTED_TAG)
    parser.add_argument("--expected-commit-prefix", default=DEFAULT_EXPECTED_COMMIT_PREFIX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()

    summary = write_preflight_artifacts(
        m2880_design=args.m2880_design,
        source_root=args.source_root,
        expected_tag=args.expected_tag,
        expected_commit_prefix=args.expected_commit_prefix,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"outcome={summary['outcome']}")
    print(f"source_available={summary['source_available']}")


if __name__ == "__main__":
    main()
