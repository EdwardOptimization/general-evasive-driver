"""Materialize M3159 Route A deployable benchmark validation specifications."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3159-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-"
    "validation-spec-materialization-preflight"
)
NEXT_ID = "m3160-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-validation-spec-result-audit"
M3158_ID = "m3158-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-validation-prep-plan"
M3157_ID = "m3157-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-result-audit"
M3156_ID = "m3156-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-materialization-preflight"

DEFAULT_M3158_PLAN = Path(f"docs/{M3158_ID}.md")
DEFAULT_M3156_DIR = Path(
    "runs/m3156_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_"
    "materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3159_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_"
    "validation_spec_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_EPISODE_ROWS = 64
EXPECTED_SUCCESS_ROWS = 57
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
EXPECTED_RESIDUAL_BLOCKERS = 7
EXPECTED_M3153_COMPARISONS = 21

CLAIM_SCOPE = (
    "M3159 Active Safety Driver Route A validation specification materialization only; "
    "M3158 plan and M3156 benchmark-pack artifacts may be converted into denominator, "
    "gate-spec, reporting, claim-boundary, audit-route, and documentation artifacts. "
    "No reset, step, rollout, replay, fitting, PPO, training, validation execution, "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, driver-performance "
    "verdict, current-sim verdict, repair success, robustness-result, high-fidelity validation, "
    "paper evidence, finite-window-vs-GRU evidence, full ideal driver completion, feasibility "
    "proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal "
    "driver completion, feasibility proof, or level3 self-identification"
)

DENOMINATOR_FIELDNAMES = [
    "denominator_id",
    "denominator_family",
    "source_artifact",
    "source_row_count",
    "required_for_validation",
    "execution_in_m3159",
    "actor_contract",
    "coverage_role",
    "included_axes",
    "known_blocker_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "claim_boundary",
]
GATE_SPEC_FIELDNAMES = [
    "gate_spec_id",
    "gate_family",
    "gate_name",
    "operator",
    "threshold",
    "source_artifact",
    "required_before_claim",
    "execution_in_m3159",
    "failure_type",
    "claim_boundary",
]
REPORTING_FIELDNAMES = [
    "reporting_artifact_id",
    "artifact_name",
    "artifact_type",
    "required_fields",
    "required_before_claim",
    "execution_in_m3159",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3159",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "validation_denominator_rows": output_dir / "validation_denominator_rows.csv",
        "validation_gate_spec_rows": output_dir / "validation_gate_spec_rows.csv",
        "validation_reporting_artifact_rows": output_dir / "validation_reporting_artifact_rows.csv",
        "validation_claim_boundary_rows": output_dir / "validation_claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3158_plan: Path, m3156_dir: Path) -> dict[str, Any]:
    paths = {
        "m3158_plan": m3158_plan,
        "m3156_summary": m3156_dir / "summary.json",
        "m3156_contract_snapshot": m3156_dir / "deployable_driver_contract_snapshot.json",
        "m3156_pack_manifest": m3156_dir / "deployable_benchmark_pack_manifest.json",
        "m3156_metric_rows": m3156_dir / "benchmark_metric_rows.csv",
        "m3156_failure_rows": m3156_dir / "known_failure_taxonomy_rows.csv",
        "m3156_gate_rows": m3156_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3158_plan_text": paths["m3158_plan"].read_text(encoding="utf-8") if exists["m3158_plan"] else "",
        "m3156_summary": read_json(paths["m3156_summary"]) if exists["m3156_summary"] else {},
        "m3156_contract_snapshot": read_json(paths["m3156_contract_snapshot"]) if exists["m3156_contract_snapshot"] else {},
        "m3156_pack_manifest": read_json(paths["m3156_pack_manifest"]) if exists["m3156_pack_manifest"] else {},
        "m3156_metric_rows": read_csv_rows(paths["m3156_metric_rows"]),
        "m3156_failure_rows": read_csv_rows(paths["m3156_failure_rows"]),
        "m3156_gate_rows": read_csv_rows(paths["m3156_gate_rows"]),
    }


def _metric_value(rows: list[dict[str, str]], name: str, default: int = 0) -> int:
    for row in rows:
        if row.get("metric_name") == name:
            try:
                return int(float(row.get("value", default)))
            except (TypeError, ValueError):
                return default
    return default


def validation_denominator_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    summary = source.get("m3156_summary", {})
    metric_rows = list(source.get("m3156_metric_rows", []))
    failure_rows = list(source.get("m3156_failure_rows", []))
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in failure_rows)
    episode_count = int(summary.get("m3105_measurement_episode_row_count", _metric_value(metric_rows, "measurement_episode_count")))
    comparison_count = int(summary.get("m3153_comparison_count", _metric_value(metric_rows, "m3153_comparison_count")))
    sensitive_count = int(summary.get("m3153_action_channel_sensitive_comparison_count", _metric_value(metric_rows, "m3153_action_channel_sensitive_count")))
    actor_contract = "actor_visible_obs72_to_direct_action3"
    return [
        {
            "denominator_id": "m3159-contract-probe-surface",
            "denominator_family": "runtime_contract",
            "source_artifact": "runs/m3156/deployable_driver_contract_snapshot.json",
            "source_row_count": 1,
            "required_for_validation": True,
            "execution_in_m3159": False,
            "actor_contract": actor_contract,
            "coverage_role": "contract parity and no-hidden-input gate",
            "included_axes": "obs72|action3|finite_bounded_action|no_hidden_inputs",
            "known_blocker_count": 0,
            "collision_count": 0,
            "offtrack_count": 0,
            "speed_too_low_count": 0,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "denominator_id": "m3159-m3105-full-fresh-current-sim-denominator",
            "denominator_family": "same_case_current_sim",
            "source_artifact": "runs/m3156/benchmark_metric_rows.csv",
            "source_row_count": episode_count,
            "required_for_validation": True,
            "execution_in_m3159": False,
            "actor_contract": actor_contract,
            "coverage_role": "incumbent baseline denominator for future same-case validation",
            "included_axes": "collision_lateral_intrusion|offtrack_boundary_recovery|speed_floor_stress|stability_action_pressure",
            "known_blocker_count": len(failure_rows),
            "collision_count": int(summary.get("m3105_collision_count", _metric_value(metric_rows, "collision_count"))),
            "offtrack_count": int(summary.get("m3105_offtrack_count", _metric_value(metric_rows, "offtrack_count"))),
            "speed_too_low_count": int(summary.get("m3105_speed_too_low_count", _metric_value(metric_rows, "speed_too_low_count"))),
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "denominator_id": "m3159-known-residual-failure-taxonomy",
            "denominator_family": "known_failures",
            "source_artifact": "runs/m3156/known_failure_taxonomy_rows.csv",
            "source_row_count": len(failure_rows),
            "required_for_validation": True,
            "execution_in_m3159": False,
            "actor_contract": actor_contract,
            "coverage_role": "residual blocker disclosure and row-level validation accountability",
            "included_axes": "|".join(sorted({str(row.get("axis_id", "")) for row in failure_rows if row.get("axis_id")})),
            "known_blocker_count": len(failure_rows),
            "collision_count": blocker_counts.get("collision", 0),
            "offtrack_count": blocker_counts.get("offtrack", 0),
            "speed_too_low_count": blocker_counts.get("speed_too_low", 0),
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "denominator_id": "m3159-m3153-negative-replay-diagnostic",
            "denominator_family": "negative_replay_diagnostic",
            "source_artifact": "runs/m3156/benchmark_metric_rows.csv",
            "source_row_count": comparison_count,
            "required_for_validation": True,
            "execution_in_m3159": False,
            "actor_contract": actor_contract,
            "coverage_role": "diagnostic-only action-channel sensitivity disclosure",
            "included_axes": f"action_channel_sensitive={sensitive_count}",
            "known_blocker_count": len(failure_rows),
            "collision_count": blocker_counts.get("collision", 0),
            "offtrack_count": blocker_counts.get("offtrack", 0),
            "speed_too_low_count": blocker_counts.get("speed_too_low", 0),
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "denominator_id": "m3159-future-high-fidelity-parity-hook",
            "denominator_family": "high_fidelity_prep",
            "source_artifact": "docs/post-m2470-route-plan.md",
            "source_row_count": 0,
            "required_for_validation": False,
            "execution_in_m3159": False,
            "actor_contract": actor_contract,
            "coverage_role": "future high-fidelity interface parity requirement only",
            "included_axes": "HF0|HF1|obs72_action3_parity|actuator_latency|status_taxonomy",
            "known_blocker_count": 0,
            "collision_count": 0,
            "offtrack_count": 0,
            "speed_too_low_count": 0,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def validation_gate_spec_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    summary = source.get("m3156_summary", {})
    contract = source.get("m3156_contract_snapshot", {})
    rows = [
        ("contract", "obs72_input_shape", "==", P0_OBSERVATION_DIM, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "action3_output_shape", "==", ACTION_DIM, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "direct_action_components", "==", "steer|throttle|brake", "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "sample_action_finite", "==", True, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "sample_action_bounded", "==", True, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "runtime_base_policy_required", "==", False, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "checkpoint_model_required", "==", False, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "recurrent_hidden_state_required", "==", False, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "hidden_oracle_actor_input_required", "==", False, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("contract", "ttc_actor_input_required", "==", False, "runs/m3156/deployable_driver_contract_snapshot.json", "contract_violation"),
        ("denominator", "m3105_full_fresh_rows", "==", EXPECTED_EPISODE_ROWS, "runs/m3156/benchmark_metric_rows.csv", "metric_artifact"),
        ("denominator", "m3105_success_count_baseline", "==", EXPECTED_SUCCESS_ROWS, "runs/m3156/benchmark_metric_rows.csv", "metric_artifact"),
        ("known_failures", "m3105_collision_blockers_disclosed", "==", EXPECTED_COLLISION_ROWS, "runs/m3156/known_failure_taxonomy_rows.csv", "metric_artifact"),
        ("known_failures", "m3105_offtrack_blockers_disclosed", "==", EXPECTED_OFFTRACK_ROWS, "runs/m3156/known_failure_taxonomy_rows.csv", "metric_artifact"),
        ("known_failures", "m3105_speed_too_low_blockers_disclosed", "==", EXPECTED_SPEED_TOO_LOW_ROWS, "runs/m3156/known_failure_taxonomy_rows.csv", "metric_artifact"),
        ("known_failures", "known_residual_blocker_rows", "==", EXPECTED_RESIDUAL_BLOCKERS, "runs/m3156/known_failure_taxonomy_rows.csv", "metric_artifact"),
        ("negative_replay", "m3153_comparison_rows", "==", EXPECTED_M3153_COMPARISONS, "runs/m3156/benchmark_metric_rows.csv", "metric_artifact"),
        ("negative_replay", "m3153_action_channel_sensitive_rows", "==", 0, "runs/m3156/benchmark_metric_rows.csv", "metric_artifact"),
        ("comparison", "same_case_comparison_required_before_candidate_claim", "==", True, "docs/m3158-validation-prep-plan", "proof_washout"),
        ("claim", "validation_result_claim_blocked_in_m3159", "==", True, "validation_claim_boundary_rows.csv", "contract_violation"),
        ("claim", "repair_success_claim_blocked_in_m3159", "==", True, "validation_claim_boundary_rows.csv", "contract_violation"),
        ("claim", "driver_performance_claim_blocked_in_m3159", "==", True, "validation_claim_boundary_rows.csv", "contract_violation"),
    ]
    output = []
    for index, (family, name, operator, threshold, artifact, failure_type) in enumerate(rows, start=1):
        output.append(
            {
                "gate_spec_id": f"m3159-validation-gate-spec-{index:04d}",
                "gate_family": family,
                "gate_name": name,
                "operator": operator,
                "threshold": threshold,
                "source_artifact": artifact,
                "required_before_claim": True,
                "execution_in_m3159": False,
                "failure_type": failure_type,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    # Keep the live source variables referenced in tests and future readers.
    _ = summary, contract
    return output


def validation_reporting_artifact_rows() -> list[dict[str, Any]]:
    specs = [
        ("validation_execution_summary.json", "json", "status_pass|gate_matrix_pass|episode_row_count|claim_flags"),
        ("validation_episode_rows.csv", "csv", "episode_id|fresh_panel_row_id|seed|success|collision|offtrack|speed_too_low|clearance|stability|recovery"),
        ("same_case_comparison_rows.csv", "csv", "episode_id|candidate_id|baseline_id|success_delta|collision_delta|offtrack_delta|clearance_delta"),
        ("known_failure_validation_rows.csv", "csv", "source_blocker_id|candidate_terminal|baseline_terminal|blocker_preserved|blocker_resolved"),
        ("runtime_contract_probe_rows.csv", "csv", "probe_id|observation_shape|action_shape|finite|bounded|runtime_ms"),
        ("validation_claim_boundary_rows.csv", "csv", "claim_id|allowed|claim_made|evidence_required"),
        ("gate_matrix.csv", "csv", "gate_id|gate_family|status_pass|observed|expected|failure_type"),
    ]
    return [
        {
            "reporting_artifact_id": f"m3159-reporting-artifact-{index:04d}",
            "artifact_name": name,
            "artifact_type": artifact_type,
            "required_fields": fields,
            "required_before_claim": True,
            "execution_in_m3159": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, artifact_type, fields) in enumerate(specs, start=1)
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("validation_denominator_specs", "validation_prep", True, "validation_denominator_rows.csv"),
        ("validation_gate_specs", "validation_prep", True, "validation_gate_spec_rows.csv"),
        ("validation_reporting_specs", "validation_prep", True, "validation_reporting_artifact_rows.csv"),
        ("claim_boundary_guards", "guard", True, "validation_claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3160 audit manifest"),
    ]
    blocked = [
        ("environment_reset", "execution", "future pre-registered validation execution route"),
        ("environment_step", "execution", "future pre-registered validation execution route"),
        ("policy_rollout", "execution", "future pre-registered validation execution route"),
        ("validation_result", "validation", "future executed validation plus audit"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("robustness_result", "verdict", "future robustness verification execution"),
        ("repair_success", "verdict", "future repair measurement audit"),
        ("checkpoint_ranking", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("high_fidelity_validation", "validation", "future Route C HF validation"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("feasibility_proof", "proof", "future feasibility proof route"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
    ]
    rows = [
        {
            "claim_id": f"m3159-{claim_id}",
            "claim_family": family,
            "allowed_in_m3159": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3159-{claim_id}",
            "claim_family": family,
            "allowed_in_m3159": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31600,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
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
        "hypothesis": "A bounded result audit can accept or reject the M3159 Route A validation specification artifacts before any validation execution ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "validation_denominator_rows.csv"),
                str(output_dir / "validation_gate_spec_rows.csv"),
                str(output_dir / "validation_reporting_artifact_rows.csv"),
                str(output_dir / "validation_claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit Route A validation specification materialization"],
            "derived_from": [MILESTONE_ID, M3158_ID, M3157_ID, M3156_ID],
            "blocked_by": [
                "M3159 validation specs require audit before validation execution planning can proceed",
                "validation specs are not validation results or performance verdict evidence",
            ],
            "supersedes": ["using M3156 benchmark pack without materialized validation denominators and gates"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3160 must audit M3159 denominator gate reporting claim and boundary specs",
            "M3160 must preserve obs72/action3 direct [steer throttle brake] contract and residual blocker disclosure",
            "M3160 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3160 must select exactly one next route: validation execution preflight artifact repair synthesis or stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun expand tune rank promote validate or mutate checkpoints",
            "do not convert M3159 specs into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_route_a_deployable_benchmark_pack",
            "evidence_axis": "route_a_deployable_benchmark_pack_validation_spec_result_audit",
            "evidence_increment": "audits the validation denominator gate reporting and claim-boundary specs materialized by M3159",
            "claim_scope": "Result audit only; no validation execution ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3159 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize if M3160 cannot select validation execution preflight artifact repair synthesis or stop",
            ],
            "fallback_plan": [
                "route to M3159 artifact repair if specs are incomplete",
                "accept validation specs if M3159 is complete and claim-safe",
                "route to validation execution preflight only after specs are accepted",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3159 completes Route A validation specification materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3159 Route A validation specification artifacts",
            "admission_evidence": ["M3159 validation denominator gate reporting claim and gate artifacts"],
            "blocked_shortcuts": [
                "no validation execution ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3160 status queue scoreboard research log and review",
                "one follow-up manifest only if M3160 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3160 accepts or rejects M3159 as complete and claim-safe",
                "M3160 selects validation execution preflight artifact repair synthesis or stop explicitly",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3160 audits engineering validation specs and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3160; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3159 validation specification artifacts only.",
            "negative_result_policy": "Preserve residual blocker evidence and route to engineering validation rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3159 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "low",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits validation specification materialization rather than another residual repair loop",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3160 audits engineering validation prep",
            "must_synthesize_if": [
                "M3160 cannot accept M3159 as complete and claim-safe",
                "M3160 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result feasibility-proof or self-ID evidence",
                "M3160 cannot select validation execution preflight artifact repair synthesis or stop",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3160 audits M3159 denominator gate reporting claim and gate artifacts",
            "M3160 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3160 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3160 hides M3159 missing rows or missing artifacts",
            "M3160 treats M3159 validation specs as validation repair-success or performance verdict",
            "M3160 changes actor input or action contract",
            "M3160 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3160 audits M3159 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_route_a_deployable_benchmark_pack_validation_spec_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3159-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    denominator_rows: list[dict[str, Any]],
    gate_spec_rows: list[dict[str, Any]],
    reporting_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    plan_text = str(source.get("m3158_plan_text", ""))
    summary = source.get("m3156_summary", {})
    contract = source.get("m3156_contract_snapshot", {})
    driver_contract = contract.get("driver_contract", {})
    failure_rows = list(source.get("m3156_failure_rows", []))
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in failure_rows)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3158_routes_to_m3159", "lineage", "route_to_m3159_validation_spec_materialization_preflight" in plan_text, "route marker", "present", "lineage_invalid"),
        gate("m3156_status_pass", "lineage", _bool(summary.get("status_pass", False)), summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3156_gate_matrix_pass", "lineage", _bool(summary.get("gate_matrix_pass", False)), summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("contract_shape", "contract", driver_contract.get("observation_shape") == P0_OBSERVATION_DIM and driver_contract.get("action_shape") == ACTION_DIM, (driver_contract.get("observation_shape"), driver_contract.get("action_shape")), (P0_OBSERVATION_DIM, ACTION_DIM), "contract_violation"),
        gate("contract_components", "contract", "|".join(driver_contract.get("action_components", [])) == "steer|throttle|brake", driver_contract.get("action_components", []), "steer|throttle|brake", "contract_violation"),
        gate("runtime_base_policy_not_required", "contract", driver_contract.get("runtime_base_policy_required") is False, driver_contract.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("denominator_rows", "validation_prep", len(denominator_rows) == 5, len(denominator_rows), 5, "metric_artifact"),
        gate("gate_spec_rows", "validation_prep", len(gate_spec_rows) >= 20, len(gate_spec_rows), ">=20", "metric_artifact"),
        gate("reporting_artifact_rows", "validation_prep", len(reporting_rows) >= 7, len(reporting_rows), ">=7", "metric_artifact"),
        gate("m3105_episode_denominator", "validation_prep", int(summary.get("m3105_measurement_episode_row_count", 0)) == EXPECTED_EPISODE_ROWS, summary.get("m3105_measurement_episode_row_count"), EXPECTED_EPISODE_ROWS, "metric_artifact"),
        gate("m3105_success_count", "validation_prep", int(summary.get("m3105_success_count", 0)) == EXPECTED_SUCCESS_ROWS, summary.get("m3105_success_count"), EXPECTED_SUCCESS_ROWS, "metric_artifact"),
        gate("known_residual_blocker_rows", "known_failures", len(failure_rows) == EXPECTED_RESIDUAL_BLOCKERS, len(failure_rows), EXPECTED_RESIDUAL_BLOCKERS, "metric_artifact"),
        gate("collision_blocker_disclosure", "known_failures", blocker_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("offtrack_blocker_disclosure", "known_failures", blocker_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("m3153_negative_replay_disclosure", "negative_replay", int(summary.get("m3153_comparison_count", 0)) == EXPECTED_M3153_COMPARISONS and int(summary.get("m3153_action_channel_sensitive_comparison_count", -1)) == 0, (summary.get("m3153_comparison_count"), summary.get("m3153_action_channel_sensitive_comparison_count")), (EXPECTED_M3153_COMPARISONS, 0), "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("no_execution_in_m3159", "claim", not any(_bool(row.get("execution_in_m3159", False)) for row in denominator_rows + gate_spec_rows + reporting_rows), "all rows", "execution_in_m3159 false", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3159 Route A Deployable Benchmark Pack Validation Spec Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- validation denominator rows: {summary['validation_denominator_row_count']}",
            f"- validation gate spec rows: {summary['validation_gate_spec_row_count']}",
            f"- validation reporting artifact rows: {summary['validation_reporting_artifact_row_count']}",
            f"- validation claim boundary rows: {summary['validation_claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3159 converts the accepted M3158 validation-prep plan and M3156 Route A benchmark pack into machine-readable validation denominator, gate, reporting, and claim-boundary specifications. It preserves the M3105/M3103 obs72-to-action3 direct-action contract, the 64-row M3105 denominator, the seven known residual blockers, and the M3153 negative replay diagnostic boundary.",
            "",
            "M3159 does not execute validation, reset or step the environment, replay rollouts, tune a policy, rank a driver, promote a checkpoint, or make validation, repair-success, robustness, driver-performance, current-sim, high-fidelity, paper, full-driver, feasibility-proof, or self-ID claims.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
        ]
    )


def run_validation_spec_materialization_preflight(
    *,
    m3158_plan: Path,
    m3156_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3158_plan=m3158_plan, m3156_dir=m3156_dir)
    denominator_rows = validation_denominator_rows(source)
    gate_spec_rows = validation_gate_spec_rows(source)
    reporting_rows = validation_reporting_artifact_rows()
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["validation_denominator_rows"], denominator_rows, DENOMINATOR_FIELDNAMES),
        (paths["validation_gate_spec_rows"], gate_spec_rows, GATE_SPEC_FIELDNAMES),
        (paths["validation_reporting_artifact_rows"], reporting_rows, REPORTING_FIELDNAMES),
        (paths["validation_claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        denominator_rows=denominator_rows,
        gate_spec_rows=gate_spec_rows,
        reporting_rows=reporting_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    source_summary = source.get("m3156_summary", {})
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_route_a_validation_spec_materialization_pass"
            if status_pass
            else "active_safety_driver_route_a_validation_spec_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "validation_denominator_row_count": len(denominator_rows),
        "validation_gate_spec_row_count": len(gate_spec_rows),
        "validation_reporting_artifact_row_count": len(reporting_rows),
        "validation_claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3105_measurement_episode_row_count": int(source_summary.get("m3105_measurement_episode_row_count", 0)),
        "m3105_success_count": int(source_summary.get("m3105_success_count", 0)),
        "m3105_collision_count": int(source_summary.get("m3105_collision_count", 0)),
        "m3105_offtrack_count": int(source_summary.get("m3105_offtrack_count", 0)),
        "m3105_speed_too_low_count": int(source_summary.get("m3105_speed_too_low_count", 0)),
        "known_residual_blocker_count": int(source_summary.get("known_failure_taxonomy_row_count", 0)),
        "m3153_comparison_count": int(source_summary.get("m3153_comparison_count", 0)),
        "m3153_action_channel_sensitive_comparison_count": int(source_summary.get("m3153_action_channel_sensitive_comparison_count", 0)),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_route_a_validation_spec_materialization_route_to_m3160_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "validation_denominator_row_count": len(denominator_rows),
            "validation_gate_spec_row_count": len(gate_spec_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3158-plan", type=Path, default=DEFAULT_M3158_PLAN)
    parser.add_argument("--m3156-dir", type=Path, default=DEFAULT_M3156_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_validation_spec_materialization_preflight(
        m3158_plan=args.m3158_plan,
        m3156_dir=args.m3156_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"validation_denominator_rows={summary['validation_denominator_row_count']}")
    print(f"validation_gate_spec_rows={summary['validation_gate_spec_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
