"""Materialize the current Route A baseline evidence index."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_OUTPUT_DIR = Path("runs/m2639_engineering_controller_route_a_baseline_evidence_index_refresh")
DEFAULT_DOC_PATH = Path(
    "docs/m2639-engineering-controller-route-a-baseline-evidence-index-refresh-materialization-preflight.md"
)
DEFAULT_MILESTONE = "m2639-engineering-controller-route-a-baseline-evidence-index-refresh-materialization-preflight"
DEFAULT_NEXT_BLOCKER = (
    "m2640-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-design"
)
CLAIM_SCOPE = (
    "Route A baseline evidence index refresh only; no ranking validation performance paper "
    "finite-window-vs-GRU current-sim high-fidelity validation or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, promotion, success-rate verdict, "
    "validation result, paper evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID claim"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "training_run": False,
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
    "full_ideal_driver_gate_passed": False,
}

EVIDENCE_FIELDNAMES = [
    "evidence_id",
    "source_milestone",
    "artifact_path",
    "evidence_family",
    "evidence_status",
    "row_count",
    "actor_contract_shape_72_action_3",
    "action_shape_3",
    "hidden_oracle_actor_input_detected",
    "claim_scope",
    "gap_or_limit",
    "next_use",
    "source_exists",
    "forbidden_interpretation",
]

GAP_FIELDNAMES = [
    "gap_id",
    "route",
    "evidence_family",
    "current_status",
    "blocker",
    "required_next_evidence",
    "admission_to_next_action",
    "evidence_expansion_value",
    "forbidden_shortcut",
]

NEXT_ACTION_FIELDNAMES = [
    "candidate_action_id",
    "route",
    "admission_status",
    "reason",
    "required_before_execution",
    "evidence_expansion",
    "claim_scope",
    "forbidden_interpretation",
]

ARTIFACT_FIELDNAMES = [
    "artifact_id",
    "path",
    "artifact_type",
    "created_by_m2639",
    "exists",
    "claim_scope",
]


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _exists(path: str | Path) -> bool:
    return Path(path).exists()


def _true(value: Any) -> bool:
    return bool(value) is True


def run_route_a_baseline_evidence_index_refresh(
    output_dir: Path,
    *,
    doc_path: Path = DEFAULT_DOC_PATH,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    source = load_source_artifacts()
    evidence_rows = build_evidence_index_rows(source)
    gap_rows = build_gap_matrix_rows(source)
    next_action_rows = build_next_action_admission_rows()

    paths = {
        "evidence_index": output_dir / "evidence_index.csv",
        "gap_matrix": output_dir / "gap_matrix.csv",
        "next_action_admission": output_dir / "next_action_admission.csv",
        "artifact_manifest": output_dir / "artifact_manifest.csv",
        "summary": output_dir / "summary.json",
        "doc": doc_path,
    }
    artifact_rows = build_artifact_manifest_rows(paths)

    write_csv_rows(paths["evidence_index"], evidence_rows, fieldnames=EVIDENCE_FIELDNAMES)
    write_csv_rows(paths["gap_matrix"], gap_rows, fieldnames=GAP_FIELDNAMES)
    write_csv_rows(paths["next_action_admission"], next_action_rows, fieldnames=NEXT_ACTION_FIELDNAMES)
    write_csv_rows(paths["artifact_manifest"], artifact_rows, fieldnames=ARTIFACT_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        doc_path=doc_path,
        paths=paths,
        source=source,
        evidence_rows=evidence_rows,
        gap_rows=gap_rows,
        next_action_rows=next_action_rows,
        artifact_rows=artifact_rows,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    doc_path.write_text(render_milestone_doc(summary, evidence_rows, gap_rows, next_action_rows), encoding="utf-8")
    artifact_rows = build_artifact_manifest_rows(paths)
    write_csv_rows(paths["artifact_manifest"], artifact_rows, fieldnames=ARTIFACT_FIELDNAMES)
    summary["artifact_manifest_rows"] = len(artifact_rows)
    summary["artifact_manifest"] = str(paths["artifact_manifest"])
    summary["required_artifacts_present"] = all(bool(row["exists"]) for row in artifact_rows)
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    write_json(paths["summary"], summary)
    return summary


def load_source_artifacts() -> dict[str, Any]:
    return {
        "m2541": read_json("runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json"),
        "m2541_baseline_rows": _read_csv_rows(
            "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/baseline_checkpoint_list.csv"
        ),
        "m2541_artifact_rows": _read_csv_rows(
            "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/route_a_artifact_map.csv"
        ),
        "m2544": read_json(
            "runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/summary.json"
        ),
        "m2544_subject_rows": _read_csv_rows(
            "runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/subject_registry.csv"
        ),
        "m2505": read_json("public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json"),
        "m2548": read_json(
            "runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json"
        ),
        "m2635": read_json(
            "runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/summary.json"
        ),
        "m2638_doc_exists": _exists(
            "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md"
        ),
    }


def build_evidence_index_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2541 = source["m2541"]
    m2544 = source["m2544"]
    m2505 = source["m2505"]
    m2548 = source["m2548"]
    m2635 = source["m2635"]
    return [
        evidence_row(
            "m2541_baseline_checkpoint_list",
            "m2541",
            str(m2541["baseline_checkpoint_list"]),
            "baseline_checkpoint_lineage",
            "materialized",
            m2541["baseline_checkpoint_count"],
            m2541["actor_contract_shape_72_action_3"],
            True,
            False,
            "lineage is diagnostic not ranking",
            "reuse as baseline subject registry",
        ),
        evidence_row(
            "m2541_route_a_artifact_map",
            "m2541",
            str(m2541["route_a_artifact_map"]),
            "route_a_artifact_lineage",
            "materialized",
            m2541["route_a_artifact_map_row_count"],
            m2541["actor_contract_shape_72_action_3"],
            True,
            False,
            "artifact map is not a performance score",
            "reuse as source artifact inventory",
        ),
        evidence_row(
            "m2544_source_only_readiness_panel",
            "m2544",
            str(m2544["summary"]),
            "source_only_closed_loop_diagnostics",
            "materialized",
            m2544["measured_behavior_row_count"],
            m2544["actor_contract_shape_72_action_3"],
            True,
            False,
            "source-only diagnostic panel is not a controller-family verdict",
            "identify fresh generalization panel inputs",
        ),
        evidence_row(
            "m2544_source_only_telemetry",
            "m2544",
            str(m2544["telemetry_rows"]),
            "source_only_telemetry",
            "materialized",
            m2544["telemetry_row_count"],
            m2544["actor_contract_shape_72_action_3"],
            True,
            False,
            "telemetry is diagnostic not paper evidence",
            "reuse schema for next source-only panel",
        ),
        evidence_row(
            "m2505_public_benchmark_pack",
            "m2505",
            str(m2505["pack_dir"]),
            "public_diagnostic_pack",
            "materialized",
            m2505["artifact_manifest_rows"],
            m2505["actor_contract_shape_72_action_3"],
            True,
            False,
            "public pack is source-only diagnostic and not validation",
            "refresh public-facing artifact boundary after M2638",
        ),
        evidence_row(
            "m2548_hf0_parity_runtime",
            "m2548",
            str(m2548["summary"]),
            "hf0_parity_and_actor_runtime",
            "materialized",
            m2548["actor_inference_cost_row_count"],
            m2548["m2541_actor_contract_shape_72_action_3"],
            m2548["all_runtime_action_shape_3"],
            m2548["hidden_oracle_actor_input_detected"],
            "actor runtime is not simulator throughput or behavior quality",
            "reuse as deployable runtime cost evidence",
        ),
        evidence_row(
            "m2638_hf3_source_dependency_blocker",
            "m2638",
            "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md",
            "hf3_dependency_blocker",
            "blocked_until_source_supplied",
            1,
            m2635["actor_observation_shape"] == P0_OBSERVATION_DIM,
            m2635["action_shape"] == ACTION_DIM,
            m2635["hidden_oracle_actor_input_detected"],
            "source blocker is not high-fidelity validation evidence",
            "keep HF3 paused and route to Route A evidence expansion",
        ),
    ]


def evidence_row(
    evidence_id: str,
    source_milestone: str,
    artifact_path: str,
    evidence_family: str,
    evidence_status: str,
    row_count: int,
    actor_contract_shape_72_action_3: bool,
    action_shape_3: bool,
    hidden_oracle_actor_input_detected: bool,
    gap_or_limit: str,
    next_use: str,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "source_milestone": source_milestone,
        "artifact_path": artifact_path,
        "evidence_family": evidence_family,
        "evidence_status": evidence_status,
        "row_count": row_count,
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "action_shape_3": bool(action_shape_3),
        "hidden_oracle_actor_input_detected": bool(hidden_oracle_actor_input_detected),
        "claim_scope": CLAIM_SCOPE,
        "gap_or_limit": gap_or_limit,
        "next_use": next_use,
        "source_exists": _exists(artifact_path),
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_gap_matrix_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2635 = source["m2635"]
    return [
        gap_row(
            "hf3_selected_platform_source_dependency",
            "Route C HF3",
            "high_fidelity_backend_dependency",
            "blocked",
            m2635["availability_blocker"],
            "user-supplied source root or approved package route",
            "not_admitted_until_source_supplied",
            "prevents fake HF3 validation progress from missing source",
            "do not add more selected-platform build/probe static prep",
        ),
        gap_row(
            "route_a_fresh_generalization_panel",
            "Route A",
            "source_only_closed_loop_generalization",
            "missing_current_fresh_panel_after_hf3_blocker",
            "none",
            "fresh source-only panel design spanning role families and unseen dynamics ranges",
            "admitted_after_m2639",
            "moves from artifact inventory to measured source-only evidence",
            "do not rank or select a winner before admission gates",
        ),
        gap_row(
            "route_a_public_pack_currentness",
            "Route A",
            "public_benchmark_pack",
            "stale_relative_to_m2638_handoff",
            "none",
            "pack refresh or addendum after next measured evidence action",
            "defer_until_new_evidence",
            "keeps public export aligned with current route boundary",
            "do not publish HF3 blocker as driver capability",
        ),
        gap_row(
            "route_a_training_or_repair_admission",
            "Route A",
            "training_repair_action",
            "not_admitted",
            "needs evidence gap selection",
            "fresh panel or synthesis before PPO or repair",
            "not_admitted",
            "prevents training from targeting stale public proof rows",
            "do not train from static index",
        ),
        gap_row(
            "paper_self_id_verdict",
            "Route B",
            "paper_self_identification",
            "not_supported",
            "no fair L0/L1/L2/L3 matrix in M2639",
            "separate paper-route comparison panel",
            "not_admitted",
            "keeps engineering Route A from overclaiming paper evidence",
            "do not claim finite-window-vs-GRU or level3 self-ID",
        ),
    ]


def gap_row(
    gap_id: str,
    route: str,
    evidence_family: str,
    current_status: str,
    blocker: str,
    required_next_evidence: str,
    admission_to_next_action: str,
    evidence_expansion_value: str,
    forbidden_shortcut: str,
) -> dict[str, Any]:
    return {
        "gap_id": gap_id,
        "route": route,
        "evidence_family": evidence_family,
        "current_status": current_status,
        "blocker": blocker,
        "required_next_evidence": required_next_evidence,
        "admission_to_next_action": admission_to_next_action,
        "evidence_expansion_value": evidence_expansion_value,
        "forbidden_shortcut": forbidden_shortcut,
    }


def build_next_action_admission_rows() -> list[dict[str, Any]]:
    return [
        next_action_row(
            "m2640_route_a_source_only_fresh_generalization_panel_design",
            "Route A",
            "admitted",
            "M2544 has source-only measured panel evidence but current route needs a fresh generalization design after HF3 blocker handoff",
            "M2639 evidence index pass",
            "design a measured source-only panel without ranking or validation claims",
        ),
        next_action_row(
            "hf3_renewed_selected_platform_availability_preflight",
            "Route C HF3",
            "not_admitted",
            "M2638 requires user-supplied source root or approved package route first",
            "explicit source dependency supplied",
            "renew local/no-network availability gate only",
        ),
        next_action_row(
            "route_a_training_or_repair_execution",
            "Route A",
            "not_admitted",
            "training or repair needs a fresh evidence panel or synthesis target before PPO",
            "fresh panel evidence and manifest",
            "targeted training or repair only after gates",
        ),
        next_action_row(
            "controller_ranking_or_winner_selection",
            "Route A",
            "not_admitted",
            "current evidence is diagnostic and mixed-scope",
            "proof and generalization gates plus promotion manifest",
            "ranking remains forbidden",
        ),
    ]


def next_action_row(
    candidate_action_id: str,
    route: str,
    admission_status: str,
    reason: str,
    required_before_execution: str,
    evidence_expansion: str,
) -> dict[str, Any]:
    return {
        "candidate_action_id": candidate_action_id,
        "route": route,
        "admission_status": admission_status,
        "reason": reason,
        "required_before_execution": required_before_execution,
        "evidence_expansion": evidence_expansion,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_artifact_manifest_rows(paths: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": str(path),
            "artifact_type": path.suffix.lstrip(".") or "directory",
            "created_by_m2639": True,
            "exists": path.exists(),
            "claim_scope": CLAIM_SCOPE,
        }
        for artifact_id, path in paths.items()
    ]


def build_summary(
    *,
    output_dir: Path,
    doc_path: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    next_action_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    m2541 = source["m2541"]
    m2544 = source["m2544"]
    m2505 = source["m2505"]
    m2548 = source["m2548"]
    m2635 = source["m2635"]
    source_artifacts_present = all(
        [
            _true(m2541.get("status_pass")),
            _true(m2544.get("status_pass")),
            _true(m2505.get("status_pass")),
            _true(m2548.get("status_pass")),
            _true(m2635.get("status_pass")),
            source["m2638_doc_exists"],
        ]
    )
    actor_contract_preserved = (
        m2541.get("observation_shape") == P0_OBSERVATION_DIM
        and m2541.get("action_shape") == ACTION_DIM
        and _true(m2544.get("actor_contract_shape_72_action_3"))
        and _true(m2505.get("actor_contract_shape_72_action_3"))
        and _true(m2548.get("m2541_actor_contract_shape_72_action_3"))
        and m2635.get("actor_observation_shape") == P0_OBSERVATION_DIM
        and m2635.get("action_shape") == ACTION_DIM
    )
    hidden_oracle_clean = not any(
        [
            m2541.get("hidden_or_oracle_actor_inputs_required"),
            not m2544.get("no_hidden_oracle_actor_inputs_encoded"),
            m2548.get("hidden_oracle_actor_input_detected"),
            m2635.get("hidden_oracle_actor_input_detected"),
        ]
    )
    hf3_source_dependency_paused = (
        m2635.get("availability_blocker") == "dependency_source_unavailable"
        and m2635.get("source_root_available") is False
        and m2635.get("cmake_lists_available") is False
    )
    admitted_next_actions = [
        row["candidate_action_id"] for row in next_action_rows if row["admission_status"] == "admitted"
    ]
    no_claim_boundary_violation = not any(FALSE_CLAIM_FLAGS.values())
    status_pass = (
        source_artifacts_present
        and actor_contract_preserved
        and hidden_oracle_clean
        and hf3_source_dependency_paused
        and len(admitted_next_actions) == 1
        and no_claim_boundary_violation
    )
    return {
        "result_class": (
            "engineering_controller_route_a_baseline_evidence_index_refresh_pass"
            if status_pass
            else "engineering_controller_route_a_baseline_evidence_index_refresh_failed"
        ),
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "doc": str(doc_path),
        "summary": str(paths["summary"]),
        "evidence_index": str(paths["evidence_index"]),
        "gap_matrix": str(paths["gap_matrix"]),
        "next_action_admission": str(paths["next_action_admission"]),
        "artifact_manifest": str(paths["artifact_manifest"]),
        "required_artifacts_present": all(bool(row["exists"]) for row in artifact_rows),
        "source_artifacts_present": bool(source_artifacts_present),
        "evidence_index_row_count": len(evidence_rows),
        "gap_matrix_row_count": len(gap_rows),
        "next_action_admission_row_count": len(next_action_rows),
        "artifact_manifest_rows": len(artifact_rows),
        "admitted_next_action_count": len(admitted_next_actions),
        "selected_next_action": admitted_next_actions[0] if admitted_next_actions else "",
        "actor_contract_shape_72_action_3": bool(actor_contract_preserved),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": not hidden_oracle_clean,
        "hf3_source_dependency_paused": bool(hf3_source_dependency_paused),
        "hf3_availability_blocker": m2635.get("availability_blocker"),
        "hf3_source_root_available": bool(m2635.get("source_root_available")),
        "hf3_cmake_lists_available": bool(m2635.get("cmake_lists_available")),
        "m2541_baseline_checkpoint_count": m2541.get("baseline_checkpoint_count"),
        "m2544_measured_behavior_row_count": m2544.get("measured_behavior_row_count"),
        "m2544_telemetry_row_count": m2544.get("telemetry_row_count"),
        "m2505_artifact_manifest_rows": m2505.get("artifact_manifest_rows"),
        "m2548_actor_inference_cost_row_count": m2548.get("actor_inference_cost_row_count"),
        "claim_boundary": CLAIM_SCOPE,
        "source_artifacts_include_prior_policy_action": bool(m2544.get("policy_action_run")),
        "source_artifacts_include_prior_policy_rollout": bool(m2544.get("policy_rollout_run")),
        **FALSE_CLAIM_FLAGS,
    }


def render_milestone_doc(
    summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    next_action_rows: list[dict[str, Any]],
) -> str:
    evidence_lines = "\n".join(
        f"- {row['evidence_id']}: {row['evidence_status']} rows={row['row_count']} source={row['artifact_path']}"
        for row in evidence_rows
    )
    gap_lines = "\n".join(
        f"- {row['gap_id']}: {row['current_status']} -> {row['admission_to_next_action']}"
        for row in gap_rows
    )
    next_lines = "\n".join(
        f"- {row['candidate_action_id']}: {row['admission_status']} ({row['reason']})"
        for row in next_action_rows
    )
    return f"""# M2639 Engineering Controller Route A Baseline Evidence Index Refresh Materialization Preflight

- status: completed
- result_class: `{summary['result_class']}`
- summary: `{summary['summary']}`
- evidence index: `{summary['evidence_index']}`
- gap matrix: `{summary['gap_matrix']}`
- next action admission: `{summary['next_action_admission']}`
- follow-up manifest: `experiments/manifests/{summary['next_blocker']}.json`
- next: `{summary['next_blocker']}`

## Materialized Evidence Index

{evidence_lines}

## Gap Matrix

{gap_lines}

## Next Action Admission

{next_lines}

M2639 admits only `m2640_route_a_source_only_fresh_generalization_panel_design`.
HF3 selected-platform availability preflight remains blocked until a source
dependency is explicitly supplied.

## Boundary

M2639 did not execute policy actions, rollouts, replay, validation, training,
source builds, adapter probes, backend starts, ranking, winner selection,
checkpoint promotion, success-rate computation, or performance interpretation.
The P0 actor contract remains observation shape 72 and action shape 3 with no
hidden/oracle actor input.
"""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    args = parser.parse_args(argv)
    summary = run_route_a_baseline_evidence_index_refresh(args.output_dir, doc_path=args.doc_path)
    print(f"summary={summary['summary']}")
    print(f"doc={summary['doc']}")
    print(f"status_pass={summary['status_pass']}")


if __name__ == "__main__":
    main()
