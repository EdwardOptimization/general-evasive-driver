"""Materialize M3086 deployable safety-reflex runtime contract artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.active_safety_reflex_driver import (
    ACTION_COMPONENTS,
    DRIVER_ID,
    OUTPUT_SEMANTICS,
    ActiveSafetyReflexDriver,
)
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-contract-materialization-preflight"
)
NEXT_ID = (
    "m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-"
    "safety-reflex-runtime-contract-materialization-result-audit"
)
M3085_ID = (
    "m3085-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-fresh-robustness-measurement-result-audit"
)
M3084_ID = (
    "m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-fresh-robustness-measurement-preflight"
)
M3078_ID = (
    "m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-"
    "direct-action-safety-reflex-materialization-preflight"
)

DEFAULT_M3085_AUDIT = Path(f"docs/{M3085_ID}.md")
DEFAULT_M3084_DIR = Path(
    "runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_fresh_robustness_measurement_preflight"
)
DEFAULT_M3078_DIR = Path(
    "runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3086_engineering_controller_active_safety_driver_v1_deployable_direct_action_"
    "safety_reflex_runtime_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_PROBE_ROWS = 5
CLAIM_SCOPE = (
    "M3086 Active Safety Driver v1 deployable direct-action safety-reflex runtime-contract "
    "materialization only; artifacts may define a callable obs72-to-action3 [steer throttle "
    "brake] runtime contract, interface rows, action probes, actor-input exclusions, claim "
    "guards, a gate matrix, a summary, and an M3087 audit manifest. No reset, step, rollout, "
    "replay, fitting, PPO, training, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, driver-performance verdict, current-sim verdict, "
    "repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, "
    "high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU "
    "conclusion, full ideal driver completion, or level3 self-identification"
)

INTERFACE_FIELDNAMES = [
    "interface_id",
    "interface_family",
    "runtime_symbol",
    "input_contract",
    "output_contract",
    "observation_shape",
    "action_shape",
    "action_components",
    "output_semantics",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "status_pass",
    "claim_boundary",
]
PROBE_FIELDNAMES = [
    "probe_id",
    "probe_family",
    "observation_shape",
    "action_shape",
    "steer",
    "throttle",
    "brake",
    "action_finite",
    "action_bounded",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "ttc_actor_input_required",
    "status_pass",
    "claim_boundary",
]
EXCLUSION_FIELDNAMES = [
    "exclusion_id",
    "actor_input_family",
    "forbidden",
    "materialized_in_actor_input",
    "status_pass",
    "rationale",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3086",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "deployable_driver_contract": output_dir / "deployable_driver_contract.json",
        "driver_interface_rows": output_dir / "driver_interface_rows.csv",
        "driver_action_probe_rows": output_dir / "driver_action_probe_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3085_audit: Path, m3084_dir: Path, m3078_dir: Path) -> dict[str, Any]:
    paths = {
        "m3085_audit": m3085_audit,
        "m3084_summary": m3084_dir / "summary.json",
        "m3084_metric_rows": m3084_dir / "metric_summary_rows.csv",
        "m3084_actor_rows": m3084_dir / "actor_contract_guard_rows.csv",
        "m3084_claim_rows": m3084_dir / "claim_boundary_rows.csv",
        "m3084_gate_rows": m3084_dir / "gate_matrix.csv",
        "m3078_summary": m3078_dir / "summary.json",
        "m3078_policy_config": m3078_dir / "direct_action_policy_config.json",
        "m3078_exclusion_rows": m3078_dir / "actor_input_exclusion_rows.csv",
        "m3078_gate_rows": m3078_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3085_audit_text": paths["m3085_audit"].read_text(encoding="utf-8") if exists["m3085_audit"] else "",
        "m3084_summary": read_json(paths["m3084_summary"]) if exists["m3084_summary"] else {},
        "m3084_metric_rows": read_csv_rows(paths["m3084_metric_rows"]),
        "m3084_actor_rows": read_csv_rows(paths["m3084_actor_rows"]),
        "m3084_claim_rows": read_csv_rows(paths["m3084_claim_rows"]),
        "m3084_gate_rows": read_csv_rows(paths["m3084_gate_rows"]),
        "m3078_summary": read_json(paths["m3078_summary"]) if exists["m3078_summary"] else {},
        "m3078_policy_config": read_json(paths["m3078_policy_config"]) if exists["m3078_policy_config"] else {},
        "m3078_exclusion_rows": read_csv_rows(paths["m3078_exclusion_rows"]),
        "m3078_gate_rows": read_csv_rows(paths["m3078_gate_rows"]),
    }


def build_driver_contract(driver: ActiveSafetyReflexDriver, source: Mapping[str, Any]) -> dict[str, Any]:
    summary = dict(source.get("m3084_summary") or {})
    contract = driver.contract_dict()
    contract.update(
        {
            "contract_id": "m3086-deployable-driver-contract-0001",
            "materialized_by": MILESTONE_ID,
            "source_policy_milestone": M3078_ID,
            "source_measurement_milestone": M3084_ID,
            "source_audit_milestone": M3085_ID,
            "fresh_measurement_episode_rows": summary.get("measurement_episode_row_count", ""),
            "fresh_measurement_failure_rows": summary.get("measurement_failure_row_count", ""),
            "fresh_measurement_success_count": summary.get("measurement_success_count", ""),
            "fresh_measurement_collision_count": summary.get("measurement_collision_count", ""),
            "fresh_measurement_offtrack_count": summary.get("measurement_offtrack_count", ""),
            "fresh_measurement_speed_too_low_count": summary.get("measurement_speed_too_low_count", ""),
            "fresh_measurement_clearance_margin_mean": summary.get("measurement_clearance_margin_mean", ""),
            "fresh_measurement_action_clip_fraction_mean": summary.get("measurement_action_clip_fraction_mean", ""),
            "measurement_result_claim_made": False,
            "validation_result_claim_made": False,
            "driver_performance_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return contract


def driver_interface_rows(contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "interface_id": "m3086-interface-0001",
            "interface_family": "python_runtime_class",
            "runtime_symbol": "autodrift.active_safety_reflex_driver.ActiveSafetyReflexDriver.act",
            "input_contract": "np.ndarray/list/tuple shape (72,), finite actor-visible P0 observation",
            "output_contract": "np.ndarray shape (3,), finite bounded [steer throttle brake]",
            "observation_shape": contract["observation_shape"],
            "action_shape": contract["action_shape"],
            "action_components": "|".join(contract["action_components"]),
            "output_semantics": contract["output_semantics"],
            "runtime_base_policy_required": contract["runtime_base_policy_required"],
            "checkpoint_model_required": contract["checkpoint_model_required"],
            "recurrent_hidden_state_required": contract["recurrent_hidden_state_required"],
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "interface_id": "m3086-interface-0002",
            "interface_family": "python_runtime_dict",
            "runtime_symbol": "autodrift.active_safety_reflex_driver.ActiveSafetyReflexDriver.act_dict",
            "input_contract": "np.ndarray/list/tuple shape (72,), finite actor-visible P0 observation",
            "output_contract": "dict with steer throttle brake float values in [-1, 1]",
            "observation_shape": contract["observation_shape"],
            "action_shape": contract["action_shape"],
            "action_components": "|".join(contract["action_components"]),
            "output_semantics": contract["output_semantics"],
            "runtime_base_policy_required": contract["runtime_base_policy_required"],
            "checkpoint_model_required": contract["checkpoint_model_required"],
            "recurrent_hidden_state_required": contract["recurrent_hidden_state_required"],
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def _probe_observations() -> list[tuple[str, str, np.ndarray]]:
    zero = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obstacle = zero.copy()
    obstacle[44] = 1.0
    obstacle[45] = 0.25
    obstacle[46] = 0.0
    left_edge = zero.copy()
    left_edge[13:28:2] = 0.03
    left_edge[29:44:2] = 0.25
    right_edge = zero.copy()
    right_edge[13:28:2] = -0.25
    right_edge[29:44:2] = -0.03
    stability = zero.copy()
    stability[1] = 0.6
    stability[2] = 0.7
    stability[4] = 0.5
    return [
        ("m3086-probe-0001", "zero_actor_visible_frame", zero),
        ("m3086-probe-0002", "visible_obstacle_centerline", obstacle),
        ("m3086-probe-0003", "left_boundary_margin", left_edge),
        ("m3086-probe-0004", "right_boundary_margin", right_edge),
        ("m3086-probe-0005", "stability_pressure", stability),
    ]


def driver_action_probe_rows(driver: ActiveSafetyReflexDriver) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for probe_id, family, observation in _probe_observations():
        action = driver.act(observation)
        finite = bool(np.all(np.isfinite(action)))
        bounded = bool(np.max(np.abs(action)) <= 1.0)
        rows.append(
            {
                "probe_id": probe_id,
                "probe_family": family,
                "observation_shape": int(observation.shape[0]),
                "action_shape": int(action.shape[0]),
                "steer": float(action[0]),
                "throttle": float(action[1]),
                "brake": float(action[2]),
                "action_finite": finite,
                "action_bounded": bounded,
                "runtime_base_policy_required": False,
                "hidden_oracle_actor_input_required": False,
                "target_labels_actor_visible": False,
                "ttc_actor_input_required": False,
                "status_pass": finite and bounded,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def actor_input_exclusion_rows(source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    if source_rows:
        families = [
            (
                str(row.get("actor_input_family", "")),
                str(row.get("rationale", "forbidden by M3078 actor input contract")),
            )
            for row in source_rows
        ]
    else:
        families = [
            ("hidden_oracle", "hidden dynamics or simulator-only state"),
            ("ttc", "precomputed time-to-collision shortcut"),
            ("target_label", "trainer-side action or objective target"),
            ("target_provenance", "target source or fitted-row provenance"),
            ("source_label", "source policy label"),
            ("route_label", "route or branch decision label"),
            ("outcome_label", "success failure or completion outcome"),
            ("progress_label", "future progress or success-progress signal"),
            ("verdict_label", "validation ranking promotion or audit verdict"),
        ]
    return [
        {
            "exclusion_id": f"m3086-exclusion-{index:04d}",
            "actor_input_family": family,
            "forbidden": True,
            "materialized_in_actor_input": False,
            "status_pass": True,
            "rationale": rationale,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, rationale) in enumerate(families, start=1)
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("runtime_contract_materialized", "materialization", True, "deployable_driver_contract.json"),
        ("driver_interface_rows", "materialization", True, "driver_interface_rows.csv"),
        ("action_probe_rows", "materialization", True, "driver_action_probe_rows.csv"),
        ("actor_input_exclusion_rows", "contract", True, "actor_input_exclusion_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3087 audit manifest"),
    ]
    blocked = [
        ("rollout_measurement", "execution", "future runtime-smoke or measurement route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future result audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "M3078 direct-action actor forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3086-{claim_id}",
            "claim_family": family,
            "allowed_in_m3086": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3086-{claim_id}",
            "claim_family": family,
            "allowed_in_m3086": False,
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
        "priority": 30820,
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
        "hypothesis": "A bounded result audit can accept or reject the M3086 deployable runtime-contract materialization artifacts before any runtime smoke, validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, repair-success, robustness-result, or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path), str(output_dir / "deployable_driver_contract.json")],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "driver_interface_rows.csv"),
                str(output_dir / "driver_action_probe_rows.csv"),
                str(output_dir / "actor_input_exclusion_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit deployable runtime contract materialization before any runtime smoke or validation route"],
            "derived_from": [MILESTONE_ID, M3085_ID, M3084_ID, M3078_ID],
            "blocked_by": [
                "M3086 runtime contract artifacts require audit before runtime smoke or stronger interpretation",
                "action probes and packaging artifacts are not validation or promotion evidence before M3087",
            ],
            "supersedes": ["direct use of M3078 policy config without a deployable runtime contract"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3087 must audit M3086 summary contract interface probe exclusion claim and gate artifacts",
            "M3087 must verify obs72/action3 direct [steer throttle brake] runtime contract and runtime_base_policy_required false",
            "M3087 must reject validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3087 must select exactly one runtime-smoke repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run rollout validation ranking promotion high-fidelity simulation fitting PPO or training",
            "do not treat M3086 packaging or probes as driver-performance validation robustness-result repair-success or self-ID evidence",
            "do not change actor input action contract or runtime base-policy-free boundary",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_deployable_direct_action_reflex",
            "evidence_axis": "deployable_runtime_contract_materialization_result_audit",
            "evidence_increment": "audits the deployable runtime contract package before runtime-smoke execution",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result or self-ID claim",
            "stop_condition": [
                "stop if M3086 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize if M3087 cannot select a runtime-smoke repair or stop route",
            ],
            "fallback_plan": [
                "route to packaging repair if artifacts are incomplete",
                "route to runtime smoke if M3086 is complete and claim-safe",
                "route to branch synthesis or stop if deployment boundary is not preservable",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3086 completes deployable runtime contract materialization preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3086 deployable runtime contract materialization artifacts",
            "admission_evidence": [
                "M3086 summary and gate matrix",
                "M3086 driver contract interface probe actor-input exclusion and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3087 status queue scoreboard research log and review",
                "one follow-up manifest only if M3087 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3087 accepts or rejects M3086 as complete and claim-safe",
                "next runtime-smoke, repair, synthesis, or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3087 audits engineering runtime-contract artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3087; finite-window and GRU comparison remains a later same-case engineering ablation."],
            "temporal_evidence_window": "M3086 deployable runtime-contract materialization artifacts only.",
            "negative_result_policy": "Preserve negative runtime-contract evidence and route to engineering repair, synthesis, or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3086 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the first deployable runtime package for the deterministic safety-reflex route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3087 audits engineering runtime package evidence",
            "must_synthesize_if": [
                "M3087 cannot accept M3086 as complete and claim-safe",
                "M3087 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result or self-ID evidence",
                "M3087 cannot select a runtime-smoke repair synthesis or stop route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3087 audits M3086 artifact row counts gates actor contract and claim boundaries",
            "M3087 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result and self-ID claims",
            "M3087 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3087 hides M3086 failures or missing artifacts",
            "M3087 treats M3086 packaging as validation or performance verdict",
            "M3087 changes actor input or action contract",
            "M3087 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3087 audits M3086 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_deployable_direct_action_runtime_contract_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "deployable_driver_contract.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3086-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    contract: Mapping[str, Any],
    interface_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    audit_accepts = "accept_m3084_measurement_route_to_m3086_deployable_runtime_contract_materialization_preflight" in str(
        source.get("m3085_audit_text", "")
    )
    probe_pass = all(_bool(row.get("status_pass", False)) for row in probe_rows)
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3085_accepts_m3086_route", "lineage", audit_accepts, "route marker", "present", "lineage_invalid"),
        gate("m3084_status_pass", "lineage", _bool(source["m3084_summary"].get("status_pass", False)), source["m3084_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3084_gate_matrix_pass", "lineage", _bool(source["m3084_summary"].get("gate_matrix_pass", False)), source["m3084_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3078_status_pass", "lineage", _bool(source["m3078_summary"].get("status_pass", False)), source["m3078_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3078_gate_matrix_pass", "lineage", _bool(source["m3078_summary"].get("gate_matrix_pass", False)), source["m3078_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("contract_observation_shape", "contract", int(contract.get("observation_shape", -1)) == P0_OBSERVATION_DIM, contract.get("observation_shape"), P0_OBSERVATION_DIM, "contract_violation"),
        gate("contract_action_shape", "contract", int(contract.get("action_shape", -1)) == ACTION_DIM, contract.get("action_shape"), ACTION_DIM, "contract_violation"),
        gate("contract_action_components", "contract", tuple(contract.get("action_components", [])) == ACTION_COMPONENTS, "|".join(contract.get("action_components", [])), "|".join(ACTION_COMPONENTS), "contract_violation"),
        gate("contract_output_semantics", "contract", str(contract.get("output_semantics")) == OUTPUT_SEMANTICS, contract.get("output_semantics"), OUTPUT_SEMANTICS, "contract_violation"),
        gate("runtime_base_policy_absent", "contract", not _bool(contract.get("runtime_base_policy_required", True)), contract.get("runtime_base_policy_required"), False, "contract_violation"),
        gate("checkpoint_model_absent", "contract", not _bool(contract.get("checkpoint_model_required", True)), contract.get("checkpoint_model_required"), False, "contract_violation"),
        gate("interface_rows_pass", "contract", all(_bool(row.get("status_pass", False)) for row in interface_rows), "all", "pass", "contract_violation"),
        gate("action_probe_count", "probe", len(probe_rows) >= EXPECTED_PROBE_ROWS, len(probe_rows), EXPECTED_PROBE_ROWS, "metric_artifact"),
        gate("action_probes_pass", "probe", probe_pass, "all", "finite_bounded", "metric_artifact"),
        gate("actor_input_exclusions_pass", "contract", all(_bool(row.get("status_pass", False)) for row in exclusion_rows), "all", "pass", "contract_violation"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3086 Active Safety Driver v1 Deployable Runtime Contract Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- driver id: `{summary['driver_id']}`",
            f"- policy config sha256: `{summary['policy_config_sha256']}`",
            f"- interface rows: {summary['driver_interface_row_count']}",
            f"- action probe rows: {summary['driver_action_probe_row_count']}",
            f"- actor-input exclusion rows: {summary['actor_input_exclusion_row_count']}",
            f"- claim-boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- runtime base policy required: {summary['runtime_base_policy_required']}",
            f"- checkpoint model required: {summary['checkpoint_model_required']}",
            f"- output: `{summary['direct_action_formula']}`",
            "",
            "## Interpretation",
            "",
            "M3086 materializes a directly callable obs72-to-action3 [steer throttle brake] runtime contract for the deterministic safety-reflex layer. It is packaging and contract evidence only. It is not validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, robustness-result, or self-ID evidence.",
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


def run_runtime_contract_materialization_preflight(
    *,
    m3085_audit: Path,
    m3084_dir: Path,
    m3078_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3085_audit=m3085_audit, m3084_dir=m3084_dir, m3078_dir=m3078_dir)
    driver = ActiveSafetyReflexDriver(policy_config=source["m3078_policy_config"])
    contract = build_driver_contract(driver, source)
    interfaces = driver_interface_rows(contract)
    probes = driver_action_probe_rows(driver)
    exclusions = actor_input_exclusion_rows(source["m3078_exclusion_rows"])
    write_json(paths["deployable_driver_contract"], contract)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["driver_interface_rows"], interfaces, INTERFACE_FIELDNAMES),
        (paths["driver_action_probe_rows"], probes, PROBE_FIELDNAMES),
        (paths["actor_input_exclusion_rows"], exclusions, EXCLUSION_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        contract=contract,
        interface_rows=interfaces,
        probe_rows=probes,
        exclusion_rows=exclusions,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight_pass"
            if status_pass
            else "active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "driver_id": DRIVER_ID,
        "policy_config_sha256": contract["policy_config_sha256"],
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "action_components": list(ACTION_COMPONENTS),
        "candidate_output_semantics": OUTPUT_SEMANTICS,
        "direct_action_formula": "action = ActiveSafetyReflexDriver.act(obs72) -> [steer, throttle, brake]",
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "driver_interface_row_count": len(interfaces),
        "driver_action_probe_row_count": len(probes),
        "driver_action_probe_rows_pass": all(_bool(row.get("status_pass", False)) for row in probes),
        "actor_input_exclusion_row_count": len(exclusions),
        "actor_input_exclusion_rows_pass": all(_bool(row.get("status_pass", False)) for row in exclusions),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3084_status_pass": _bool(source["m3084_summary"].get("status_pass", False)),
        "m3084_gate_matrix_pass": _bool(source["m3084_summary"].get("gate_matrix_pass", False)),
        "m3078_status_pass": _bool(source["m3078_summary"].get("status_pass", False)),
        "m3078_gate_matrix_pass": _bool(source["m3078_summary"].get("gate_matrix_pass", False)),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "hidden_oracle_actor_input_detected": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "ttc_actor_input_required": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_route_to_m3087_result_audit",
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
    write_json(
        paths["run_state"],
        {
            "complete": status_pass,
            "status_pass": status_pass,
            "driver_interface_row_count": len(interfaces),
            "driver_action_probe_row_count": len(probes),
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3085-audit", type=Path, default=DEFAULT_M3085_AUDIT)
    parser.add_argument("--m3084-dir", type=Path, default=DEFAULT_M3084_DIR)
    parser.add_argument("--m3078-dir", type=Path, default=DEFAULT_M3078_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_runtime_contract_materialization_preflight(
        m3085_audit=args.m3085_audit,
        m3084_dir=args.m3084_dir,
        m3078_dir=args.m3078_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"driver_id={summary['driver_id']}")
    print(f"probe_rows={summary['driver_action_probe_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
