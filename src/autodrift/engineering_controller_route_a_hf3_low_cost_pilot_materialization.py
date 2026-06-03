"""Route A HF3 low-cost pilot materialization preflight."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2560-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2561-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-result-audit"
DEFAULT_DOC_PATH = "docs/m2560-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization")
DEFAULT_HF2_SUMMARY = Path("runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/summary.json")
DEFAULT_HF2_BINDINGS = Path(
    "runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_surface_fixture_binding.csv"
)
DEFAULT_HF2_PILOT_GUARDS = Path(
    "runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_pilot_admission_guard_rows.csv"
)

SOURCE_ARTIFACTS = (
    "docs/m2559-engineering-controller-route-a-baseline-hf3-low-cost-pilot-design.md",
    "docs/m2558-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-result-synthesis.md",
    "docs/m2557-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-result-audit.md",
    "runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/summary.json",
    "runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_surface_fixture_binding.csv",
    "runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/hf2_pilot_admission_guard_rows.csv",
    "runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/materialization_gate_matrix.csv",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 low-cost pilot materialization preflight only; not external "
    "simulation, policy action, reset/rollout execution, ranking, validation, "
    "driver performance, paper, FW-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID"
)

HF3_ADMISSION_STATUS = "requires_m2560_reset_and_rollout_feasibility"
HF3_CANDIDATE_SCOPE = "hf3_preflight_design_only"

PILOT_CANDIDATE_SPECS = (
    {
        "candidate_id": "stable_avoidable_aeb_feasible_design_candidate",
        "route_role_id": "stable_avoidable_aeb_feasible",
        "route_role_label": "stable avoidable / AEB-feasible",
        "source_binding_id": "source_only_four_wheel_hf0:stable_avoidable",
    },
    {
        "candidate_id": "stable_aes_aeb_infeasible_design_candidate",
        "route_role_id": "stable_aes_aeb_infeasible",
        "route_role_label": "stable AES / AEB-infeasible",
        "source_binding_id": "source_only_four_wheel_hf0:stable_aes",
    },
)

EXTERNAL_BOUNDARY_CHECKS = (
    ("external_dependency_install", "external_simulator_dependency_install"),
    ("external_package_import", "external_simulator_package_import"),
    ("external_reset_execution", "external_simulator_reset_execution"),
    ("external_step_execution", "external_simulator_step_execution"),
    ("policy_action_execution", "policy_action_execution"),
    ("high_fidelity_validation_verdict", "high_fidelity_validation_verdict"),
)

CLAIM_CHECKS = (
    ("hf3_pilot_admission", "explicit reset and rollout feasibility execution audit"),
    ("reset_success", "measured reset feasibility execution artifact"),
    ("rollout_success", "measured rollout feasibility execution artifact"),
    ("high_fidelity_validation_readiness", "audited reset and rollout feasibility evidence"),
    ("controller_ranking_or_winner_selection", "controller-family comparison milestone"),
    ("driver_performance_claim", "measured validation with claim-boundary audit"),
    ("paper_fw_vs_gru_current_sim_or_self_id_claim", "separate paper-route evidence matrix"),
)

PILOT_CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "route_role_id",
    "route_role_label",
    "source_binding_id",
    "source_fixture_id",
    "source_binding_status",
    "actor_observation_shape",
    "action_shape",
    "hf3_candidate_scope",
    "hf3_admission_status",
    "reset_feasibility_required",
    "rollout_feasibility_required",
    "validation_claim_allowed",
    "status_pass",
    "claim_boundary",
]

RESET_FEASIBILITY_FIELDNAMES = [
    "reset_check_id",
    "candidate_id",
    "route_role_id",
    "required_source_binding_status",
    "external_backend_boundary",
    "reset_state_source",
    "policy_action_allowed_in_m2560",
    "environment_step_allowed_in_m2560",
    "reset_success_claim_allowed",
    "required_before_rollout",
    "status_pass",
    "claim_boundary",
]

ROLLOUT_FEASIBILITY_FIELDNAMES = [
    "rollout_check_id",
    "candidate_id",
    "route_role_id",
    "requires_reset_feasibility_artifact",
    "action_contract",
    "rollout_execution_allowed_in_m2560",
    "success_rate_claim_allowed",
    "controller_family_verdict_allowed",
    "required_before_validation",
    "status_pass",
    "claim_boundary",
]

EXTERNAL_BOUNDARY_FIELDNAMES = [
    "boundary_check_id",
    "backend_boundary",
    "install_allowed",
    "import_allowed",
    "simulation_run_allowed",
    "policy_action_allowed",
    "environment_step_allowed",
    "status_pass",
    "claim_boundary",
]

CLAIM_BOUNDARY_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2560",
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

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "external_high_fidelity_imported": False,
    "high_fidelity_simulation_run": False,
    "measured_validation_run": False,
    "policy_rollout_run": False,
    "policy_action_run": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "hf3_pilot_admission_claim_made": False,
    "reset_success_claim_made": False,
    "rollout_success_claim_made": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}


def materialize_route_a_hf3_low_cost_pilot_preflight(
    output_dir: Path,
    *,
    hf2_summary_path: Path = DEFAULT_HF2_SUMMARY,
    hf2_bindings_path: Path = DEFAULT_HF2_BINDINGS,
    hf2_pilot_guards_path: Path = DEFAULT_HF2_PILOT_GUARDS,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    hf2_summary = read_json(hf2_summary_path)
    binding_rows = _read_csv_rows(hf2_bindings_path)
    pilot_guard_rows = _read_csv_rows(hf2_pilot_guards_path)

    candidate_rows = build_pilot_candidate_rows(binding_rows)
    reset_rows = build_reset_feasibility_rows(candidate_rows)
    rollout_rows = build_rollout_feasibility_rows(candidate_rows)
    external_rows = build_external_backend_boundary_checks()
    claim_rows = build_claim_boundary_checks()
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        hf2_summary=hf2_summary,
        candidate_rows=candidate_rows,
        reset_rows=reset_rows,
        rollout_rows=rollout_rows,
        external_rows=external_rows,
        claim_rows=claim_rows,
        pilot_guard_rows=pilot_guard_rows,
    )

    candidate_path = output_dir / "hf3_pilot_candidate_rows.csv"
    reset_path = output_dir / "hf3_reset_feasibility_plan.csv"
    rollout_path = output_dir / "hf3_rollout_feasibility_plan.csv"
    external_path = output_dir / "hf3_external_backend_boundary_checks.csv"
    claim_path = output_dir / "hf3_claim_boundary_checks.csv"
    gate_path = output_dir / "materialization_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(candidate_path, candidate_rows, fieldnames=PILOT_CANDIDATE_FIELDNAMES)
    write_csv_rows(reset_path, reset_rows, fieldnames=RESET_FEASIBILITY_FIELDNAMES)
    write_csv_rows(rollout_path, rollout_rows, fieldnames=ROLLOUT_FEASIBILITY_FIELDNAMES)
    write_csv_rows(external_path, external_rows, fieldnames=EXTERNAL_BOUNDARY_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_BOUNDARY_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        hf2_summary=hf2_summary,
        candidate_rows=candidate_rows,
        reset_rows=reset_rows,
        rollout_rows=rollout_rows,
        external_rows=external_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        candidate_path=candidate_path,
        reset_path=reset_path,
        rollout_path=rollout_path,
        external_path=external_path,
        claim_path=claim_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_pilot_candidate_rows(binding_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    bindings_by_id = {row["binding_id"]: row for row in binding_rows}
    rows: list[dict[str, Any]] = []
    for spec in PILOT_CANDIDATE_SPECS:
        binding = bindings_by_id.get(spec["source_binding_id"], {})
        obs_shape = _int_value(binding.get("actor_observation_shape"), default=-1)
        action_shape = _int_value(binding.get("action_shape"), default=-1)
        binding_status = binding.get("binding_status", "missing_source_binding")
        source_fixture_id = binding.get("m2482_fixture_id", "")
        candidate_not_admitted = HF3_ADMISSION_STATUS == "requires_m2560_reset_and_rollout_feasibility"
        source_status_allowed = binding_status in {
            "baseline_reference_binding",
            "materialization_candidate_binding",
        }
        status_pass = bool(
            binding
            and source_status_allowed
            and obs_shape == P0_OBSERVATION_DIM
            and action_shape == ACTION_DIM
            and candidate_not_admitted
        )
        rows.append(
            {
                "candidate_id": spec["candidate_id"],
                "route_role_id": spec["route_role_id"],
                "route_role_label": spec["route_role_label"],
                "source_binding_id": spec["source_binding_id"],
                "source_fixture_id": source_fixture_id,
                "source_binding_status": binding_status,
                "actor_observation_shape": obs_shape,
                "action_shape": action_shape,
                "hf3_candidate_scope": HF3_CANDIDATE_SCOPE,
                "hf3_admission_status": HF3_ADMISSION_STATUS,
                "reset_feasibility_required": True,
                "rollout_feasibility_required": True,
                "validation_claim_allowed": False,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_reset_feasibility_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        row = {
            "reset_check_id": f"{candidate['candidate_id']}_reset_feasibility",
            "candidate_id": candidate["candidate_id"],
            "route_role_id": candidate["route_role_id"],
            "required_source_binding_status": candidate["source_binding_status"],
            "external_backend_boundary": "boundary_only_no_install_import_run",
            "reset_state_source": "hf3_candidate_source_binding_metadata_only",
            "policy_action_allowed_in_m2560": False,
            "environment_step_allowed_in_m2560": False,
            "reset_success_claim_allowed": False,
            "required_before_rollout": "measured_reset_feasibility_execution_artifact",
            "status_pass": bool(
                _row_passed(candidate)
                and not _boolish(candidate["validation_claim_allowed"])
            ),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        rows.append(row)
    return rows


def build_rollout_feasibility_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        row = {
            "rollout_check_id": f"{candidate['candidate_id']}_rollout_feasibility",
            "candidate_id": candidate["candidate_id"],
            "route_role_id": candidate["route_role_id"],
            "requires_reset_feasibility_artifact": "measured_reset_feasibility_execution_artifact",
            "action_contract": "[steer, throttle, brake]",
            "rollout_execution_allowed_in_m2560": False,
            "success_rate_claim_allowed": False,
            "controller_family_verdict_allowed": False,
            "required_before_validation": "measured_rollout_feasibility_execution_artifact",
            "status_pass": bool(
                _row_passed(candidate)
                and _int_value(candidate["action_shape"], default=-1) == ACTION_DIM
            ),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        rows.append(row)
    return rows


def build_external_backend_boundary_checks() -> list[dict[str, Any]]:
    return [
        {
            "boundary_check_id": check_id,
            "backend_boundary": boundary,
            "install_allowed": False,
            "import_allowed": False,
            "simulation_run_allowed": False,
            "policy_action_allowed": False,
            "environment_step_allowed": False,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for check_id, boundary in EXTERNAL_BOUNDARY_CHECKS
    ]


def build_claim_boundary_checks() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"{claim_family}_claim_boundary",
            "claim_family": claim_family,
            "claim_allowed_in_m2560": False,
            "evidence_required_before_claim": evidence_required,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for claim_family, evidence_required in CLAIM_CHECKS
    ]


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    hf2_summary: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    reset_rows: list[dict[str, Any]],
    rollout_rows: list[dict[str, Any]],
    external_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    pilot_guard_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    pilot_claims_from_hf2 = any(_boolish(row["pilot_admission_claim_made"]) for row in pilot_guard_rows)
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()) and bool(hf2_summary.get("status_pass")),
            f"missing={sum(1 for exists in source_exists.values() if not exists)};m2556_status={hf2_summary.get('status_pass')}",
            "missing=0;m2556_status=True",
            "lineage_invalid",
        ),
        (
            "pilot_candidates_complete",
            "scenario",
            len(candidate_rows) == 2 and _all_status_pass(candidate_rows),
            f"rows={len(candidate_rows)}",
            "rows=2",
            "scenario_sampling_failure",
        ),
        (
            "reset_feasibility_plan_complete",
            "scenario",
            len(reset_rows) == 2
            and _all_status_pass(reset_rows)
            and not any(_boolish(row["policy_action_allowed_in_m2560"]) for row in reset_rows)
            and not any(_boolish(row["environment_step_allowed_in_m2560"]) for row in reset_rows),
            f"rows={len(reset_rows)}",
            "rows=2;policy_action=false;environment_step=false",
            "scenario_sampling_failure",
        ),
        (
            "rollout_feasibility_plan_complete",
            "scenario",
            len(rollout_rows) == 2
            and _all_status_pass(rollout_rows)
            and not any(_boolish(row["rollout_execution_allowed_in_m2560"]) for row in rollout_rows),
            f"rows={len(rollout_rows)}",
            "rows=2;rollout_execution=false",
            "scenario_sampling_failure",
        ),
        (
            "external_backend_boundary_checks_pass",
            "contract",
            len(external_rows) == len(EXTERNAL_BOUNDARY_CHECKS)
            and _all_status_pass(external_rows)
            and not any(_boolish(row["install_allowed"]) for row in external_rows)
            and not any(_boolish(row["import_allowed"]) for row in external_rows)
            and not any(_boolish(row["simulation_run_allowed"]) for row in external_rows),
            f"rows={len(external_rows)}",
            f"rows={len(EXTERNAL_BOUNDARY_CHECKS)};install=false;import=false;run=false",
            "contract_violation",
        ),
        (
            "claim_boundary_checks_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and not any(_boolish(row["claim_allowed_in_m2560"]) for row in claim_rows)
            and not pilot_claims_from_hf2,
            f"rows={len(claim_rows)};hf2_pilot_claims={pilot_claims_from_hf2}",
            f"rows={len(CLAIM_CHECKS)};claims=false;hf2_pilot_claims=false",
            "objective_overfit",
        ),
        (
            "actor_action_contract_preserved",
            "contract",
            P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
            f"obs={P0_OBSERVATION_DIM};action={ACTION_DIM}",
            "obs=72;action=3",
            "contract_violation",
        ),
        (
            "no_false_claim_flags",
            "claim_boundary",
            not any(FALSE_CLAIM_FLAGS.values()),
            "all false",
            "all false",
            "objective_overfit",
        ),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": bool(passed),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if passed else failure_type,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for gate_id, family, passed, observed, expected, failure_type in checks
    ]


def build_summary(
    *,
    output_dir: Path,
    source_exists: dict[str, bool],
    hf2_summary: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    reset_rows: list[dict[str, Any]],
    rollout_rows: list[dict[str, Any]],
    external_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    candidate_path: Path,
    reset_path: Path,
    rollout_path: Path,
    external_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    candidate_admission_counts = Counter(str(row["hf3_admission_status"]) for row in candidate_rows)
    source_binding_counts = Counter(str(row["source_binding_status"]) for row in candidate_rows)
    status_pass = (
        all(source_exists.values())
        and bool(hf2_summary.get("status_pass"))
        and len(candidate_rows) == 2
        and _all_status_pass(candidate_rows)
        and len(reset_rows) == 2
        and _all_status_pass(reset_rows)
        and len(rollout_rows) == 2
        and _all_status_pass(rollout_rows)
        and len(external_rows) == len(EXTERNAL_BOUNDARY_CHECKS)
        and _all_status_pass(external_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    candidate_admitted = any(row["hf3_admission_status"] != HF3_ADMISSION_STATUS for row in candidate_rows)
    return {
        "result_class": "engineering_controller_route_a_hf3_low_cost_pilot_materialization_preflight_pass"
        if status_pass
        else "engineering_controller_route_a_hf3_low_cost_pilot_materialization_preflight_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_pilot_candidate_rows": str(candidate_path),
        "hf3_reset_feasibility_plan": str(reset_path),
        "hf3_rollout_feasibility_plan": str(rollout_path),
        "hf3_external_backend_boundary_checks": str(external_path),
        "hf3_claim_boundary_checks": str(claim_path),
        "materialization_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2556_status_pass": bool(hf2_summary.get("status_pass")),
        "m2556_pilot_admission_claim_made": bool(hf2_summary.get("pilot_admission_claim_made")),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "pilot_candidate_row_count": len(candidate_rows),
        "pilot_candidate_rows_all_pass": _all_status_pass(candidate_rows),
        "pilot_candidate_role_ids": sorted({str(row["route_role_id"]) for row in candidate_rows}),
        "candidate_admission_status_counts": dict(sorted(candidate_admission_counts.items())),
        "source_binding_status_counts": dict(sorted(source_binding_counts.items())),
        "candidate_rows_pilot_admitted": bool(candidate_admitted),
        "reset_feasibility_row_count": len(reset_rows),
        "reset_feasibility_rows_all_pass": _all_status_pass(reset_rows),
        "policy_action_allowed_in_m2560": any(
            _boolish(row["policy_action_allowed_in_m2560"]) for row in reset_rows
        ),
        "environment_step_allowed_in_m2560": any(
            _boolish(row["environment_step_allowed_in_m2560"]) for row in reset_rows
        ),
        "reset_success_claim_allowed": any(
            _boolish(row["reset_success_claim_allowed"]) for row in reset_rows
        ),
        "rollout_feasibility_row_count": len(rollout_rows),
        "rollout_feasibility_rows_all_pass": _all_status_pass(rollout_rows),
        "rollout_execution_allowed_in_m2560": any(
            _boolish(row["rollout_execution_allowed_in_m2560"]) for row in rollout_rows
        ),
        "success_rate_claim_allowed": any(
            _boolish(row["success_rate_claim_allowed"]) for row in rollout_rows
        ),
        "controller_family_verdict_allowed": any(
            _boolish(row["controller_family_verdict_allowed"]) for row in rollout_rows
        ),
        "external_boundary_check_count": len(external_rows),
        "external_boundary_checks_all_pass": _all_status_pass(external_rows),
        "external_install_allowed": any(_boolish(row["install_allowed"]) for row in external_rows),
        "external_import_allowed": any(_boolish(row["import_allowed"]) for row in external_rows),
        "external_simulation_run_allowed": any(
            _boolish(row["simulation_run_allowed"]) for row in external_rows
        ),
        "claim_boundary_check_count": len(claim_rows),
        "claim_boundary_checks_all_pass": _all_status_pass(claim_rows),
        "claim_allowed_in_m2560": any(
            _boolish(row["claim_allowed_in_m2560"]) for row in claim_rows
        ),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "hidden_oracle_actor_input_detected": False,
        "external_backend_boundary_only": True,
        **FALSE_CLAIM_FLAGS,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2560 Engineering Controller Route A Baseline HF3 Low-Cost Pilot Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2560-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_low_cost_pilot_materialization.py`",
                f"- summary: `{summary['summary']}`",
                f"- pilot candidates: `{summary['hf3_pilot_candidate_rows']}`",
                f"- reset-feasibility plan: `{summary['hf3_reset_feasibility_plan']}`",
                f"- rollout-feasibility plan: `{summary['hf3_rollout_feasibility_plan']}`",
                f"- external-boundary checks: `{summary['hf3_external_backend_boundary_checks']}`",
                f"- claim-boundary checks: `{summary['hf3_claim_boundary_checks']}`",
                f"- materialization gate matrix: `{summary['materialization_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- policy action/reset/step/rollout/training/ranking/validation claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2560 materializes Route A HF3 low-cost pilot preflight",
                "artifacts for exactly two candidates: stable avoidable/AEB-feasible",
                "and stable AES/AEB-infeasible. The rows define reset and rollout",
                "feasibility plans only. They do not execute either feasibility",
                "check and do not grant pilot admission.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"pilot_candidate_row_count: {summary['pilot_candidate_row_count']}",
                f"reset_feasibility_row_count: {summary['reset_feasibility_row_count']}",
                f"rollout_feasibility_row_count: {summary['rollout_feasibility_row_count']}",
                f"external_boundary_check_count: {summary['external_boundary_check_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"candidate_rows_pilot_admitted: {str(summary['candidate_rows_pilot_admitted']).lower()}",
                f"policy_action_allowed_in_m2560: {str(summary['policy_action_allowed_in_m2560']).lower()}",
                f"environment_step_allowed_in_m2560: {str(summary['environment_step_allowed_in_m2560']).lower()}",
                f"rollout_execution_allowed_in_m2560: {str(summary['rollout_execution_allowed_in_m2560']).lower()}",
                f"claim_allowed_in_m2560: {str(summary['claim_allowed_in_m2560']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2560 is a source-level HF3 preflight materialization. It does",
                "not install, import, or run an external simulator; does not",
                "execute policy actions, resets, steps, or rollouts; does not",
                "rank policies, select a winner, promote checkpoints, compute",
                "success rates, validate driver performance, or provide paper/",
                "FW-vs-GRU/current-sim/high-fidelity/self-ID evidence.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return all(_row_passed(row) for row in rows)


def _row_passed(row: dict[str, Any]) -> bool:
    return _boolish(row.get("status_pass"))


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--hf2-summary", type=Path, default=DEFAULT_HF2_SUMMARY)
    parser.add_argument("--hf2-bindings", type=Path, default=DEFAULT_HF2_BINDINGS)
    parser.add_argument("--hf2-pilot-guards", type=Path, default=DEFAULT_HF2_PILOT_GUARDS)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize_route_a_hf3_low_cost_pilot_preflight(
        args.output_dir,
        hf2_summary_path=args.hf2_summary,
        hf2_bindings_path=args.hf2_bindings,
        hf2_pilot_guards_path=args.hf2_pilot_guards,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "pilot_candidate_rows={pilot_candidate_row_count} "
        "reset_rows={reset_feasibility_row_count} "
        "rollout_rows={rollout_feasibility_row_count} "
        "summary={summary}".format(**summary)
    )


if __name__ == "__main__":
    main()
