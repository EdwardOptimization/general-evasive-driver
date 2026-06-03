"""Route A HF2 scenario taxonomy mapping materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.hf0_scenario_taxonomy_mapping import (
    ACTOR_VISIBLE_INPUTS,
    ACTION_DIM,
    CURRENT_SIM_SURFACE_ID,
    FORBIDDEN_ACTOR_INPUT_TOKENS,
    P0_OBSERVATION_DIM,
    ROLE_FAMILIES,
    SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
)


DEFAULT_MILESTONE = "m2556-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2557-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-result-audit"
DEFAULT_DOC_PATH = "docs/m2556-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-preflight.md"
DEFAULT_OUTPUT_DIR = Path("runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping")
DEFAULT_M2480_MATRIX = Path("runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv")
DEFAULT_M2482_CATALOG = Path("runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv")

SOURCE_ARTIFACTS = (
    "docs/m2555-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-design.md",
    "docs/m2554-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-result-synthesis.md",
    "runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/summary.json",
    "runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json",
    "runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv",
    "runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/summary.json",
    "runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF2 scenario taxonomy mapping materialization only; not policy "
    "rollout, ranking, validation, driver performance, paper, FW-vs-GRU, "
    "current-sim verdict, high-fidelity validation, or self-ID"
)

ROUTE_ROLE_DEFS = (
    ("stable_avoidable_aeb_feasible", "stable avoidable / AEB-feasible", "stable_avoidable"),
    ("stable_aes_aeb_infeasible", "stable AES / AEB-infeasible", "stable_aes"),
    ("drift_required_recovery", "drift-required recovery", "drift_required_recovery"),
    ("hidden_dynamics_robustness", "hidden-dynamics robustness", "hidden_dynamics_robustness"),
    ("unavoidable_mitigation", "unavoidable mitigation", "unavoidable_mitigation"),
)

METADATA_FAMILY_DEFS = (
    ("scenario_role_labels", ("scenario_role_label", "role_family", "route_role_id")),
    ("feasibility_labels", ("feasibility_class", "aeb_feasible", "aes_feasible", "unavoidable")),
    ("aeb_aes_feasibility_labels", ("AEB-feasible", "AEB-infeasible", "stable-AES")),
    ("current_sim_hidden_task_fields", ("mu", "mass", "cg_shift", "speed_ref", "beta_target", "ttc_or_stopping_clearance")),
    ("source_only_four_wheel_hidden_dynamics", ("vehicle_params", "fault_scales", "per_wheel_forces", "slip_load_like_force_details")),
    ("fixture_admission_labels", ("fixture_admission_status", "pilot_candidate_status", "binding_status")),
    ("success_reward_termination_labels", ("reward_terms", "success_or_termination_labels", "termination_label")),
)

ROUTE_ROLE_FIELDNAMES = [
    "route_role_id",
    "route_role_label",
    "m2480_role_family",
    "route_c_family",
    "actor_observation_shape",
    "action_shape",
    "actor_visible_allowed_fields",
    "metadata_only_labels",
    "feasibility_label_actor_visible",
    "pilot_admission_allowed_by_mapping",
    "status_pass",
    "claim_boundary",
]

BINDING_FIELDNAMES = [
    "binding_id",
    "route_role_id",
    "surface_id",
    "m2480_role_family",
    "m2480_support_status",
    "m2482_fixture_id",
    "m2482_fixture_admission_status",
    "actor_observation_shape",
    "action_shape",
    "binding_status",
    "support_status_preserved",
    "limited_or_reference_upgraded",
    "status_pass",
    "claim_boundary",
]

METADATA_FIELDNAMES = [
    "metadata_family",
    "example_fields",
    "source_artifact",
    "actor_visible_allowed",
    "present_in_actor_field_map",
    "hidden_or_oracle_risk",
    "status_pass",
    "claim_boundary",
]

PILOT_GUARD_FIELDNAMES = [
    "guard_id",
    "route_role_id",
    "source_binding_status",
    "pilot_candidate_status",
    "required_before_hf3",
    "pilot_admission_claim_made",
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
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}


def materialize_route_a_hf2_scenario_taxonomy_mapping(
    output_dir: Path,
    *,
    m2480_matrix_path: Path = DEFAULT_M2480_MATRIX,
    m2482_catalog_path: Path = DEFAULT_M2482_CATALOG,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    source_summaries = _source_summaries()
    matrix_rows = _read_csv_rows(m2480_matrix_path)
    fixture_rows = _read_csv_rows(m2482_catalog_path)
    route_rows = build_route_role_mapping_rows()
    binding_rows = build_surface_fixture_binding_rows(matrix_rows, fixture_rows)
    metadata_rows = build_metadata_boundary_checks()
    pilot_rows = build_pilot_admission_guard_rows(binding_rows)
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        route_rows=route_rows,
        binding_rows=binding_rows,
        metadata_rows=metadata_rows,
        pilot_rows=pilot_rows,
        source_matrix_rows=matrix_rows,
        source_fixture_rows=fixture_rows,
    )

    route_path = output_dir / "hf2_route_role_mapping.csv"
    binding_path = output_dir / "hf2_surface_fixture_binding.csv"
    metadata_path = output_dir / "hf2_metadata_boundary_checks.csv"
    pilot_path = output_dir / "hf2_pilot_admission_guard_rows.csv"
    gate_path = output_dir / "materialization_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(route_path, route_rows, fieldnames=ROUTE_ROLE_FIELDNAMES)
    write_csv_rows(binding_path, binding_rows, fieldnames=BINDING_FIELDNAMES)
    write_csv_rows(metadata_path, metadata_rows, fieldnames=METADATA_FIELDNAMES)
    write_csv_rows(pilot_path, pilot_rows, fieldnames=PILOT_GUARD_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        source_summaries=source_summaries,
        matrix_rows=matrix_rows,
        fixture_rows=fixture_rows,
        route_rows=route_rows,
        binding_rows=binding_rows,
        metadata_rows=metadata_rows,
        pilot_rows=pilot_rows,
        gate_rows=gate_rows,
        route_path=route_path,
        binding_path=binding_path,
        metadata_path=metadata_path,
        pilot_path=pilot_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_route_role_mapping_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    actor_fields = ";".join(ACTOR_VISIBLE_INPUTS)
    metadata_labels = "scenario_role_label;feasibility_class;aeb_aes_feasibility;route_role_id;pilot_candidate_status"
    for route_role_id, route_label, role_family in ROUTE_ROLE_DEFS:
        role_known = role_family in ROLE_FAMILIES
        rows.append(
            {
                "route_role_id": route_role_id,
                "route_role_label": route_label,
                "m2480_role_family": role_family,
                "route_c_family": route_label,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "actor_visible_allowed_fields": actor_fields,
                "metadata_only_labels": metadata_labels,
                "feasibility_label_actor_visible": False,
                "pilot_admission_allowed_by_mapping": False,
                "status_pass": bool(
                    role_known
                    and P0_OBSERVATION_DIM == 72
                    and ACTION_DIM == 3
                    and not _actor_tokens_leak(ACTOR_VISIBLE_INPUTS)
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_surface_fixture_binding_rows(
    matrix_rows: list[dict[str, str]],
    fixture_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    fixture_by_surface_role = {
        (row["surface_id"], row["role_family"]): row
        for row in fixture_rows
    }
    route_by_role = {
        role_family: route_role_id
        for route_role_id, _route_label, role_family in ROUTE_ROLE_DEFS
    }
    rows: list[dict[str, Any]] = []
    for source_row in matrix_rows:
        surface_id = source_row["surface_id"]
        role_family = source_row["role_family"]
        fixture = fixture_by_surface_role.get((surface_id, role_family), {})
        admission_status = fixture.get("fixture_admission_status", "missing_fixture")
        binding_status = _binding_status(source_row.get("support_status", ""), admission_status)
        limited_or_reference_upgraded = binding_status == "pilot_ready_binding"
        support_status_preserved = bool(
            fixture and fixture.get("source_support_status") == source_row.get("support_status")
        )
        obs_shape = int(source_row.get("actor_observation_shape", -1))
        action_shape = int(source_row.get("action_shape", -1))
        rows.append(
            {
                "binding_id": f"{surface_id}:{role_family}",
                "route_role_id": route_by_role.get(role_family, "unknown_route_role"),
                "surface_id": surface_id,
                "m2480_role_family": role_family,
                "m2480_support_status": source_row.get("support_status", ""),
                "m2482_fixture_id": fixture.get("fixture_id", ""),
                "m2482_fixture_admission_status": admission_status,
                "actor_observation_shape": obs_shape,
                "action_shape": action_shape,
                "binding_status": binding_status,
                "support_status_preserved": support_status_preserved,
                "limited_or_reference_upgraded": bool(limited_or_reference_upgraded),
                "status_pass": bool(
                    route_by_role.get(role_family)
                    and surface_id in {CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID}
                    and obs_shape == P0_OBSERVATION_DIM
                    and action_shape == ACTION_DIM
                    and support_status_preserved
                    and not limited_or_reference_upgraded
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_metadata_boundary_checks() -> list[dict[str, Any]]:
    actor_tokens = set(ACTOR_VISIBLE_INPUTS)
    rows = []
    for family, fields in METADATA_FAMILY_DEFS:
        present = any(field in actor_tokens for field in fields)
        rows.append(
            {
                "metadata_family": family,
                "example_fields": ";".join(fields),
                "source_artifact": "M2480/M2482 metadata fields plus M2555 route-role labels",
                "actor_visible_allowed": False,
                "present_in_actor_field_map": bool(present),
                "hidden_or_oracle_risk": "must_remain_metadata_only",
                "status_pass": not present,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_pilot_admission_guard_rows(binding_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for route_role_id, _route_label, role_family in ROUTE_ROLE_DEFS:
        role_bindings = [row for row in binding_rows if row["m2480_role_family"] == role_family]
        binding_counts = Counter(str(row["binding_status"]) for row in role_bindings)
        guard_id = f"{route_role_id}_pilot_guard"
        rows.append(
            {
                "guard_id": guard_id,
                "route_role_id": route_role_id,
                "source_binding_status": ";".join(
                    f"{status}={count}" for status, count in sorted(binding_counts.items())
                ),
                "pilot_candidate_status": "not_admitted_by_taxonomy_mapping",
                "required_before_hf3": "M2557 audit plus explicit HF3 reset/rollout feasibility design",
                "pilot_admission_claim_made": False,
                "status_pass": bool(role_bindings),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    route_rows: list[dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    metadata_rows: list[dict[str, Any]],
    pilot_rows: list[dict[str, Any]],
    source_matrix_rows: list[dict[str, str]],
    source_fixture_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()),
            f"missing={sum(1 for exists in source_exists.values() if not exists)}",
            "missing=0",
            "lineage_invalid",
        ),
        (
            "route_role_mapping_complete",
            "taxonomy",
            len(route_rows) == 5 and _all_status_pass(route_rows),
            f"rows={len(route_rows)}",
            "rows=5",
            "scenario_sampling_failure",
        ),
        (
            "surface_fixture_bindings_complete",
            "taxonomy",
            len(binding_rows) == len(source_matrix_rows) == 10 and _all_status_pass(binding_rows),
            f"bindings={len(binding_rows)};source_rows={len(source_matrix_rows)};fixtures={len(source_fixture_rows)}",
            "bindings=10;source_rows=10;fixtures=10",
            "scenario_sampling_failure",
        ),
        (
            "metadata_boundary_checks_pass",
            "contract",
            _all_status_pass(metadata_rows),
            f"passed={sum(_row_passed(row) for row in metadata_rows)}/total={len(metadata_rows)}",
            f"passed={len(metadata_rows)}/total={len(metadata_rows)}",
            "contract_violation",
        ),
        (
            "pilot_admission_guards_pass",
            "claim_boundary",
            _all_status_pass(pilot_rows)
            and not any(_boolish(row["pilot_admission_claim_made"]) for row in pilot_rows),
            f"passed={sum(_row_passed(row) for row in pilot_rows)}/total={len(pilot_rows)}",
            f"passed={len(pilot_rows)}/total={len(pilot_rows)};pilot_claims=0",
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
    source_summaries: dict[str, Any],
    matrix_rows: list[dict[str, str]],
    fixture_rows: list[dict[str, str]],
    route_rows: list[dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    metadata_rows: list[dict[str, Any]],
    pilot_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    route_path: Path,
    binding_path: Path,
    metadata_path: Path,
    pilot_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    binding_counts = Counter(str(row["binding_status"]) for row in binding_rows)
    source_support_counts = Counter(str(row.get("support_status", "")) for row in matrix_rows)
    fixture_admission_counts = Counter(str(row.get("fixture_admission_status", "")) for row in fixture_rows)
    status_pass = (
        all(source_exists.values())
        and bool(source_summaries["m2552"].get("status_pass"))
        and bool(source_summaries["m2480"].get("status_pass"))
        and bool(source_summaries["m2482"].get("status_pass"))
        and len(route_rows) == 5
        and _all_status_pass(route_rows)
        and len(binding_rows) == len(matrix_rows) == 10
        and _all_status_pass(binding_rows)
        and _all_status_pass(metadata_rows)
        and _all_status_pass(pilot_rows)
        and _all_status_pass(gate_rows)
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf2_scenario_taxonomy_mapping_materialization_pass"
        if status_pass
        else "engineering_controller_route_a_hf2_scenario_taxonomy_mapping_materialization_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf2_route_role_mapping": str(route_path),
        "hf2_surface_fixture_binding": str(binding_path),
        "hf2_metadata_boundary_checks": str(metadata_path),
        "hf2_pilot_admission_guard_rows": str(pilot_path),
        "materialization_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2552_status_pass": bool(source_summaries["m2552"].get("status_pass")),
        "m2480_status_pass": bool(source_summaries["m2480"].get("status_pass")),
        "m2482_status_pass": bool(source_summaries["m2482"].get("status_pass")),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "route_role_mapping_row_count": len(route_rows),
        "route_role_mapping_all_pass": _all_status_pass(route_rows),
        "route_role_family_count": len({row["m2480_role_family"] for row in route_rows}),
        "source_surface_role_row_count": len(matrix_rows),
        "source_fixture_catalog_row_count": len(fixture_rows),
        "surface_fixture_binding_row_count": len(binding_rows),
        "surface_fixture_bindings_all_pass": _all_status_pass(binding_rows),
        "source_support_status_counts": dict(sorted(source_support_counts.items())),
        "fixture_admission_status_counts": dict(sorted(fixture_admission_counts.items())),
        "binding_status_counts": dict(sorted(binding_counts.items())),
        "limited_or_reference_upgraded": any(
            _boolish(row["limited_or_reference_upgraded"]) for row in binding_rows
        ),
        "metadata_boundary_check_count": len(metadata_rows),
        "metadata_boundary_checks_all_pass": _all_status_pass(metadata_rows),
        "metadata_labels_enter_actor_input": any(
            _boolish(row["present_in_actor_field_map"]) for row in metadata_rows
        ),
        "pilot_admission_guard_count": len(pilot_rows),
        "pilot_admission_guards_all_pass": _all_status_pass(pilot_rows),
        "pilot_admission_claim_made": any(
            _boolish(row["pilot_admission_claim_made"]) for row in pilot_rows
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
                "# M2556 Engineering Controller Route A Baseline HF2 Scenario Taxonomy Mapping Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2556-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf2_scenario_taxonomy_mapping_materialization.py`",
                f"- summary: `{summary['summary']}`",
                f"- route-role mapping: `{summary['hf2_route_role_mapping']}`",
                f"- surface/fixture binding: `{summary['hf2_surface_fixture_binding']}`",
                f"- metadata-boundary checks: `{summary['hf2_metadata_boundary_checks']}`",
                f"- pilot-admission guard rows: `{summary['hf2_pilot_admission_guard_rows']}`",
                f"- materialization gate matrix: `{summary['materialization_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- policy rollout/training/ranking/winner/promotion/success-rate/validation claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2556 materializes Route A HF2 taxonomy mapping artifacts.",
                "The rows bind Route C role families to existing M2480/M2482",
                "surface and fixture metadata under the accepted M2552/M2553",
                "HF1 boundary. They do not admit any HF3 pilot or validation.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"route_role_mapping_row_count: {summary['route_role_mapping_row_count']}",
                f"surface_fixture_binding_row_count: {summary['surface_fixture_binding_row_count']}",
                f"metadata_boundary_check_count: {summary['metadata_boundary_check_count']}",
                f"pilot_admission_guard_count: {summary['pilot_admission_guard_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"limited_or_reference_upgraded: {str(summary['limited_or_reference_upgraded']).lower()}",
                f"metadata_labels_enter_actor_input: {str(summary['metadata_labels_enter_actor_input']).lower()}",
                f"pilot_admission_claim_made: {str(summary['pilot_admission_claim_made']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2556 is a taxonomy mapping artifact. It does not rank Route A",
                "policies, select a winner, promote a checkpoint, compute success",
                "rates, validate driver performance, or provide paper/FW-vs-GRU/",
                "current-sim/high-fidelity/self-ID evidence.",
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


def _binding_status(source_support_status: str, fixture_admission_status: str) -> str:
    if fixture_admission_status == "missing_fixture":
        return "blocked_binding"
    if fixture_admission_status == "admitted_for_materialization":
        return "materialization_candidate_binding"
    if fixture_admission_status == "baseline_reference":
        return "baseline_reference_binding"
    if fixture_admission_status == "diagnostic_reference_only":
        return "diagnostic_reference_binding"
    if source_support_status == "supported":
        return "reference_binding"
    return "blocked_binding"


def _source_summaries() -> dict[str, Any]:
    return {
        "m2552": read_json(
            "runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/summary.json"
        ),
        "m2480": read_json(
            "runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json"
        ),
        "m2482": read_json(
            "runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/summary.json"
        ),
    }


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _actor_tokens_leak(tokens: tuple[str, ...]) -> bool:
    return bool(set(tokens).intersection(FORBIDDEN_ACTOR_INPUT_TOKENS))


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_row_passed(row) for row in rows)


def _row_passed(row: dict[str, Any]) -> bool:
    return _boolish(row.get("status_pass", False))


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize Route A HF2 taxonomy mapping artifacts.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    parser.add_argument("--m2480-matrix", type=Path, default=DEFAULT_M2480_MATRIX)
    parser.add_argument("--m2482-catalog", type=Path, default=DEFAULT_M2482_CATALOG)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_route_a_hf2_scenario_taxonomy_mapping(
        args.output_dir,
        m2480_matrix_path=args.m2480_matrix,
        m2482_catalog_path=args.m2482_catalog,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"route_role_mapping_row_count={summary['route_role_mapping_row_count']}")
    print(f"surface_fixture_binding_row_count={summary['surface_fixture_binding_row_count']}")
    print(f"summary={summary['summary']}")


if __name__ == "__main__":
    main()
