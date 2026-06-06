"""Read-only Route B capability-prediction panel inventory preflight.

M2884 inventories existing post-M2470 artifacts for a future L0/L1/L2/L3
capability-prediction panel. It does not reset, step, rollout, validate, train,
rank, promote, or claim finite-window-vs-GRU/self-ID evidence.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2884-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-preflight"
DEFAULT_NEXT_BLOCKER = "m2885-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-result-audit"
DEFAULT_OUTPUT_DIR = Path("runs/m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight")
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2885-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-result-audit.json"
)
DEFAULT_M1690_WORKLOAD = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv"
)
DEFAULT_M2877_DIR = Path("runs/m2877_engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight")
DEFAULT_M2868_DIR = Path(
    "runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "localized_response_prediction_candidate_closed_loop_delta_panel"
)
DEFAULT_M2838_DIR = Path("runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight")
DEFAULT_M2828_DIR = Path(
    "runs/m2828_engineering_controller_route_a_post_package_source_diverse_closed_loop_evidence_expansion_preflight"
)

REQUIRED_PROFILES = [
    "L0_current_masked",
    "L1_one_step",
    "L2_window_13",
    "L2_window_13_current_tiled",
    "L2_window_25",
    "L2_window_25_current_tiled",
    "L2_window_50",
    "L2_window_50_current_tiled",
    "L2_window_100",
    "L2_window_100_current_tiled",
    "L3_online_gru",
    "L3_reset_control_corrected",
]
TARGET_SPECS = [
    (
        "future_braking_deceleration_envelope",
        ["brake_scale", "speed_mean", "impact_speed_proxy", "delta_v_at_impact_mps"],
        "evaluator future braking target only; never actor input",
    ),
    (
        "future_yaw_authority",
        ["max_abs_yaw_rate", "post_event_yaw_rate_abs", "beta_abs_peak"],
        "evaluator yaw authority target only; never actor input",
    ),
    (
        "future_lateral_acceleration_response",
        ["lateral_peak", "lateral_rmse", "min_clearance_margin"],
        "evaluator lateral response target only; never actor input",
    ),
    (
        "actuator_response_lag_proxy",
        ["previous_command_norm_mean", "current_action_norm_mean", "action_trace_delta_mean"],
        "evaluator actuator lag proxy only; never actor input",
    ),
    (
        "recovery_margin_after_maneuver",
        ["recovery_time_proxy", "recoverability_window_success", "min_clearance_margin"],
        "evaluator recovery target only; never actor input",
    ),
    (
        "first_critical_action_quality",
        ["first_obstacle_pass_step", "plan_first_action_error_mean", "min_clearance_margin"],
        "evaluator first-critical-action target only; never actor input",
    ),
]

CLAIM_SCOPE = (
    "M2884 read-only capability-prediction panel inventory only. It reads repository-local "
    "workload and diagnostic artifacts and writes candidate inventory rows. It does not reset, "
    "step, rollout, replay, validate, train, run PPO, rank controllers, select a winner, promote "
    "a checkpoint, publish a package, or claim driver performance, paper evidence, "
    "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity validation, full-driver "
    "completion, or level3 self-ID."
)
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, checkpoint promotion, finite-window-vs-GRU verdict, "
    "paper result, current-sim verdict, validation readiness/result, high-fidelity validation, "
    "full-driver completion, or level3 self-identification"
)

CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "task_source_id",
    "task_family",
    "source_edge",
    "window_tag",
    "executable_source_family",
    "env_template_family",
    "profile_count",
    "required_profile_count",
    "required_profiles_present",
    "missing_required_profiles",
    "config_checkpoint_complete",
    "diagnostic_artifact_tags",
    "diagnostic_artifact_count",
    "candidate_artifact_count",
    "guard_artifact_count",
    "paired_delta_count",
    "source_family_tag_count",
    "deployable_history_features_available",
    "future_capability_targets_available",
    "classification",
    "classification_reason",
    "admitted_for_next_capability_prediction_design",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "evaluator_targets_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
    "forbidden_interpretation",
]
SOURCE_FIELDNAMES = [
    "source_inventory_id",
    "artifact_tag",
    "path",
    "path_exists",
    "row_count",
    "task_source_count",
    "candidate_row_count",
    "guard_row_count",
    "diagnostic_only",
    "claim_boundary",
]
TARGET_FIELDNAMES = [
    "target_id",
    "target_family",
    "required_columns",
    "available_columns",
    "status_pass",
    "actor_visible_allowed",
    "target_scope",
    "claim_boundary",
]
ACTOR_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible_allowed",
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
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "claim_allowed",
    "evidence_required_before_claim",
    "claim_boundary",
]

FALSE_CLAIM_FLAGS = {
    "dependency_mutation_performed": False,
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
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _split_tags(value: Any) -> set[str]:
    text = str(value or "").strip()
    if not text:
        return set()
    return {part.strip() for part in text.split("|") if part.strip()}


def _artifact_specs(m2877_dir: Path, m2868_dir: Path, m2838_dir: Path, m2828_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "tag": "m2877_fresh_candidate",
            "path": m2877_dir / "fresh_candidate_rows.csv",
            "kind": "candidate",
        },
        {
            "tag": "m2877_execution",
            "path": m2877_dir / "candidate_execution_rows.csv",
            "kind": "candidate",
        },
        {
            "tag": "m2877_prior_surface_guard",
            "path": m2877_dir / "prior_surface_exclusion_rows.csv",
            "kind": "guard",
        },
        {
            "tag": "m2877_package_limitation_guard",
            "path": m2877_dir / "package_limitation_guard_rows.csv",
            "kind": "guard_no_task",
        },
        {
            "tag": "m2868_paired_delta",
            "path": m2868_dir / "paired_delta_rows.csv",
            "kind": "candidate",
        },
        {
            "tag": "m2838_selected_candidate",
            "path": m2838_dir / "selected_candidate_rows.csv",
            "kind": "candidate",
        },
        {
            "tag": "m2838_prior_surface_guard",
            "path": m2838_dir / "prior_surface_exclusion_rows.csv",
            "kind": "guard",
        },
        {
            "tag": "m2828_post_package_candidate",
            "path": m2828_dir / "post_package_candidate_rows.csv",
            "kind": "candidate",
        },
        {
            "tag": "m2828_prior_surface_guard",
            "path": m2828_dir / "prior_surface_exclusion_rows.csv",
            "kind": "guard",
        },
        {
            "tag": "m2828_package_limitation_guard",
            "path": m2828_dir / "package_limitation_guard_rows.csv",
            "kind": "guard_no_task",
        },
    ]


def build_source_inventory_rows(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        path = Path(spec["path"])
        source_rows = _read_csv_rows(path)
        task_ids = {row.get("task_source_id", "") for row in source_rows if row.get("task_source_id", "")}
        kind = str(spec["kind"])
        rows.append(
            {
                "source_inventory_id": f"m2884-source-{index:04d}",
                "artifact_tag": spec["tag"],
                "path": str(path),
                "path_exists": path.exists(),
                "row_count": len(source_rows),
                "task_source_count": len(task_ids),
                "candidate_row_count": len(source_rows) if kind == "candidate" else 0,
                "guard_row_count": len(source_rows) if kind.startswith("guard") else 0,
                "diagnostic_only": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _artifact_maps(specs: list[dict[str, Any]]) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, Counter[str]], set[str]]:
    candidate_tags: dict[str, set[str]] = defaultdict(set)
    guard_tags: dict[str, set[str]] = defaultdict(set)
    source_family_tags: dict[str, Counter[str]] = defaultdict(Counter)
    execution_columns: set[str] = set()
    for spec in specs:
        path = Path(spec["path"])
        rows = _read_csv_rows(path)
        kind = str(spec["kind"])
        for row in rows:
            execution_columns.update(row.keys())
            task_source_id = row.get("task_source_id", "")
            if not task_source_id:
                continue
            if kind == "candidate":
                candidate_tags[task_source_id].add(str(spec["tag"]))
            elif kind.startswith("guard"):
                guard_tags[task_source_id].add(str(spec["tag"]))
            for key in ("source_family_tag", "executable_source_family", "scenario_role_primary"):
                value = row.get(key, "")
                if value:
                    source_family_tags[task_source_id][value] += 1
    return candidate_tags, guard_tags, source_family_tags, execution_columns


def build_target_inventory_rows(execution_columns: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target_id, required_columns, scope in TARGET_SPECS:
        available_columns = [column for column in required_columns if column in execution_columns]
        rows.append(
            {
                "target_id": f"m2884-target-{target_id}",
                "target_family": target_id,
                "required_columns": "|".join(required_columns),
                "available_columns": "|".join(available_columns),
                "status_pass": bool(available_columns),
                "actor_visible_allowed": False,
                "target_scope": scope,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _classification(
    *,
    profile_complete: bool,
    config_checkpoint_complete: bool,
    candidate_count: int,
    guard_count: int,
    source_family_tag_count: int,
    targets_available: bool,
) -> tuple[str, str, bool]:
    if not profile_complete or not config_checkpoint_complete or not targets_available:
        return (
            "missing-data",
            "missing complete profile matrix config/checkpoint coverage or evaluator-only target columns",
            False,
        )
    if candidate_count == 0 and guard_count > 0:
        return ("guard", "task appears only in prior-surface or package guard artifacts", False)
    if candidate_count == 0:
        return ("missing-data", "no recent diagnostic artifact coverage for this task_source_id", False)
    if source_family_tag_count <= 1 or candidate_count == 1:
        return (
            "source-singleton",
            "diagnostic coverage is too narrow for paper proof but can seed a later panel",
            False,
        )
    return (
        "usable",
        "complete profile matrix with recent diagnostic coverage and evaluator-only target columns",
        True,
    )


def build_candidate_panel_rows(
    *,
    workload_rows: list[dict[str, str]],
    candidate_tags: dict[str, set[str]],
    guard_tags: dict[str, set[str]],
    source_family_tags: dict[str, Counter[str]],
    targets_available: bool,
) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in workload_rows:
        task_source_id = row.get("task_source_id", "")
        if task_source_id:
            by_task[task_source_id].append(row)

    panel_rows: list[dict[str, Any]] = []
    for index, task_source_id in enumerate(sorted(by_task), start=1):
        rows = by_task[task_source_id]
        profiles = {row.get("profile_name", "") for row in rows}
        missing_profiles = [profile for profile in REQUIRED_PROFILES if profile not in profiles]
        profile_complete = not missing_profiles
        config_checkpoint_complete = all(_bool(row.get("config_exists")) and _bool(row.get("checkpoint_exists")) for row in rows)
        first = rows[0]
        task_candidate_tags = sorted(candidate_tags.get(task_source_id, set()))
        task_guard_tags = sorted(guard_tags.get(task_source_id, set()))
        family_counter = source_family_tags.get(task_source_id, Counter())
        if first.get("executable_source_family"):
            family_counter = family_counter.copy()
            family_counter[first["executable_source_family"]] += 1
        classification, reason, admitted = _classification(
            profile_complete=profile_complete,
            config_checkpoint_complete=config_checkpoint_complete,
            candidate_count=len(task_candidate_tags),
            guard_count=len(task_guard_tags),
            source_family_tag_count=len(family_counter),
            targets_available=targets_available,
        )
        panel_rows.append(
            {
                "candidate_id": f"m2884-panel-candidate-{index:04d}",
                "task_source_id": task_source_id,
                "task_family": first.get("task_family", ""),
                "source_edge": first.get("source_edge", ""),
                "window_tag": first.get("window_tag", ""),
                "executable_source_family": first.get("executable_source_family", ""),
                "env_template_family": first.get("env_template_family", ""),
                "profile_count": len(profiles),
                "required_profile_count": len(REQUIRED_PROFILES),
                "required_profiles_present": profile_complete,
                "missing_required_profiles": "|".join(missing_profiles),
                "config_checkpoint_complete": config_checkpoint_complete,
                "diagnostic_artifact_tags": "|".join(sorted(set(task_candidate_tags) | set(task_guard_tags))),
                "diagnostic_artifact_count": len(set(task_candidate_tags) | set(task_guard_tags)),
                "candidate_artifact_count": len(task_candidate_tags),
                "guard_artifact_count": len(task_guard_tags),
                "paired_delta_count": 1 if "m2868_paired_delta" in task_candidate_tags else 0,
                "source_family_tag_count": len(family_counter),
                "deployable_history_features_available": profile_complete,
                "future_capability_targets_available": targets_available,
                "classification": classification,
                "classification_reason": reason,
                "admitted_for_next_capability_prediction_design": admitted,
                "actor_contract_shape_72_action_3": True,
                "hidden_oracle_actor_input_required": False,
                "evaluator_targets_actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return panel_rows


def build_actor_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "guard_id": "m2884-actor-p0_observation_dim",
            "guard_family": "p0_observation_dim",
            "observed": P0_OBSERVATION_DIM,
            "expected": 72,
            "status_pass": P0_OBSERVATION_DIM == 72,
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "guard_id": "m2884-actor-action_dim",
            "guard_family": "action_dim",
            "observed": ACTION_DIM,
            "expected": 3,
            "status_pass": ACTION_DIM == 3,
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "guard_id": "m2884-actor-hidden_oracle_actor_input_required",
            "guard_family": "hidden_oracle_actor_input_required",
            "observed": False,
            "expected": False,
            "status_pass": True,
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "guard_id": "m2884-actor-evaluator_targets_actor_visible",
            "guard_family": "evaluator_targets_actor_visible",
            "observed": False,
            "expected": False,
            "status_pass": True,
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "guard_id": "m2884-actor-input_contract_changed",
            "guard_family": "actor_input_contract_changed",
            "observed": False,
            "expected": False,
            "status_pass": True,
            "actor_visible_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    claim_specs = [
        ("driver_performance", "driver performance", "validation and promotion evidence"),
        ("finite_window_vs_gru", "finite-window-vs-GRU verdict", "fair L0/L1/L2/L3 training or prediction comparison"),
        ("paper", "paper result", "paper route controller-family matrix and holdout protocol"),
        ("current_sim_verdict", "current-sim verdict", "current-sim benchmark pack and audit"),
        ("high_fidelity_validation", "high-fidelity validation", "source/build/reset/rollout validation gates"),
        ("full_driver", "full ideal driver completion", "full ideal driver gate"),
        ("level3_self_id", "level3 self-ID", "source-diverse intervention and terminal-boundary evidence"),
    ]
    return [
        {
            "claim_id": f"m2884-claim-{claim_id}",
            "claim_family": claim_family,
            "claim_made": False,
            "claim_allowed": False,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, claim_family, evidence in claim_specs
    ]


def build_gate_rows(
    *,
    workload_exists: bool,
    candidate_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    classification_counts = Counter(str(row["classification"]) for row in candidate_rows)
    usable_count = classification_counts.get("usable", 0)
    target_gate_pass = bool(target_rows) and all(
        _bool(row["status_pass"]) and not _bool(row["actor_visible_allowed"]) for row in target_rows
    )
    actor_gate_pass = bool(actor_rows) and all(_bool(row["status_pass"]) for row in actor_rows)
    claim_gate_pass = bool(claim_rows) and all(not _bool(row["claim_made"]) for row in claim_rows)
    return [
        {
            "gate_id": "m2884-workload-matrix-present",
            "gate_family": "input_artifact",
            "status_pass": workload_exists,
            "observed": workload_exists,
            "expected": True,
            "failure_type": "lineage_invalid" if not workload_exists else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2884-source-inventory-written",
            "gate_family": "artifact_completeness",
            "status_pass": bool(source_rows),
            "observed": len(source_rows),
            "expected": ">=1",
            "failure_type": "metric_artifact" if not source_rows else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2884-candidate-classification-complete",
            "gate_family": "artifact_completeness",
            "status_pass": bool(candidate_rows) and all(row.get("classification") for row in candidate_rows),
            "observed": len(candidate_rows),
            "expected": "classified candidate rows",
            "failure_type": "metric_artifact" if not candidate_rows else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2884-usable-candidate-exists",
            "gate_family": "panel_viability",
            "status_pass": usable_count > 0,
            "observed": usable_count,
            "expected": ">0",
            "failure_type": "scenario_sampling_failure" if usable_count == 0 else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2884-target-inventory-evaluator-only",
            "gate_family": "target_boundary",
            "status_pass": target_gate_pass,
            "observed": sum(_bool(row["status_pass"]) for row in target_rows),
            "expected": len(target_rows),
            "failure_type": "none"
            if target_gate_pass
            else (
                "contract_violation"
                if any(_bool(row["actor_visible_allowed"]) for row in target_rows)
                else "metric_artifact"
            ),
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2884-actor-contract-preserved",
            "gate_family": "actor_contract",
            "status_pass": actor_gate_pass,
            "observed": sum(_bool(row["status_pass"]) for row in actor_rows),
            "expected": len(actor_rows),
            "failure_type": "none" if actor_gate_pass else "contract_violation",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2884-no-claim-made",
            "gate_family": "claim_boundary",
            "status_pass": claim_gate_pass,
            "observed": sum(_bool(row["claim_made"]) for row in claim_rows),
            "expected": 0,
            "failure_type": "none" if claim_gate_pass else "proof_washout",
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_follow_up_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "hypothesis": "A bounded result audit can accept or reject the M2884 capability-prediction panel inventory before any training or controller-family verdict.",
        "lineage": {
            "parent_checkpoint": summary["baseline_checkpoints"],
            "parent_dataset": [
                summary["artifacts"]["summary"],
                summary["artifacts"]["candidate_panel_rows"],
                summary["artifacts"]["source_inventory_rows"],
                summary["artifacts"]["target_inventory_rows"],
                summary["artifacts"]["actor_contract_rows"],
                "docs/m2883-engineering-controller-route-c-hf3-chrono-next-dependency-gate-or-stop-design.md",
                "docs/self-id-go-no-go-paper-route-plan.md",
                "docs/paper-route-finite-window-vs-gru-plan.md",
            ],
            "parent_config": [
                "experiments/manifests/m2884-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-preflight.json"
            ],
            "parent_objective": [
                "audit whether M2884 produced a claim-safe candidate inventory for Route B capability prediction"
            ],
            "derived_from": [
                "m2884-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-preflight",
                "m2883-engineering-controller-route-c-hf3-chrono-next-dependency-gate-or-stop-design",
            ],
            "blocked_by": [
                "M2884 inventory must be audited before any capability-prediction training data design or controller-family comparison",
                "Route B must preserve actor boundaries and reject stale protected source-singleton proof rows",
            ],
            "supersedes": [
                "starting new PPO or controller-family ranking directly after M2883",
                "using M2884 inventory rows as self-ID or paper proof without audit",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2885 must audit M2884 summary candidate source target actor gate and claim rows",
            "M2885 must accept or reject the panel inventory classification and source-diversity boundaries",
            "M2885 must preserve evaluator-only future targets outside actor input",
            "M2885 must not claim driver performance finite-window-vs-GRU verdict current-sim verdict high-fidelity validation full-driver or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout validate train rank promote or publish a package",
            "do not change actor input or action contract",
            "do not convert inventory rows into paper proof",
            "do not claim driver performance paper current-sim high-fidelity full-driver or self-ID evidence",
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
            "branch": "paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory",
            "evidence_axis": "route_b_capability_prediction_before_policy_training_result_audit",
            "evidence_increment": "audits the M2884 candidate panel inventory before any next data or training design is admitted",
            "claim_scope": "Result audit only; no training validation ranking finite-window-vs-GRU verdict or self-ID claim",
            "stop_condition": [
                "stop if M2884 rows are missing incomplete stale protected source-singleton only or actor-unsafe",
                "stop if M2885 would interpret inventory rows as paper proof or driver performance",
            ],
            "fallback_plan": [
                "route to a negative inventory synthesis if the panel is insufficient",
                "route to bounded new data-panel design if gaps are concrete and actor-safe",
                "route to capability-prediction implementation only if inventory is accepted claim-safe",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2884 writes panel inventory artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "M2884 capability-prediction panel inventory result audit",
            "admission_evidence": [
                "M2884 wrote read-only panel inventory artifacts",
                "M2883 selected Route B capability-prediction inventory after stopping Chrono/HF3 under source_unavailable",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation training ranking promotion",
                "no hidden or oracle actor inputs",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "M2885 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if the audit selects a route",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "M2884 inventory is accepted or rejected",
                "one next Route B action or stop decision is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2885 audits inventory only and does not test history necessity.",
            "history_necessity_tests": [
                "None in M2885; later tests require accepted panel inventory and fair L0/L1/L2/L3 comparison."
            ],
            "temporal_evidence_window": "M2883-M2884 Route B capability-prediction inventory branch.",
            "negative_result_policy": "Preserve insufficient inventory as a negative result rather than weakening actor contract or source-diversity gates.",
            "allowed_claims": [
                "M2884 inventory accepted or rejected",
                "bounded follow-up route or stop decision",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "low",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0 if summary["usable_candidate_count"] else 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the newly materialized panel inventory",
            "paper_verdict_delta": "no verdict; may admit later capability-prediction design if accepted",
            "must_synthesize_if": [
                "M2885 cannot decide whether M2884 inventory is sufficient",
                "M2885 would claim self-ID finite-window-vs-GRU driver performance or current-sim verdict",
            ],
        },
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "audit accepts or rejects M2884 inventory completeness and claim safety",
            "audit selects exactly one bounded next route or stop decision",
        ],
        "failure_criteria": [
            "M2885 resets steps rolls out validates trains ranks promotes or executes policy action",
            "M2885 changes actor input or action contract",
            "M2885 claims driver performance finite-window-vs-GRU verdict paper current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "decision_rule": "Pass only if M2885 writes a claim-safe audit of M2884 inventory before any further Route B action.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{DEFAULT_NEXT_BLOCKER}.md", "type": "md"}],
        "baseline_checkpoints": summary["baseline_checkpoints"],
        "baseline_artifacts": [
            summary["artifacts"]["summary"],
            summary["artifacts"]["candidate_panel_rows"],
            summary["artifacts"]["source_inventory_rows"],
            summary["artifacts"]["target_inventory_rows"],
            summary["artifacts"]["actor_contract_rows"],
        ],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "m2886-paper-route-l0-l1-l2-l3-capability-prediction-panel-audit-synthesis-or-data-design",
    }


def write_preflight_artifacts(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
    m1690_workload: Path = DEFAULT_M1690_WORKLOAD,
    m2877_dir: Path = DEFAULT_M2877_DIR,
    m2868_dir: Path = DEFAULT_M2868_DIR,
    m2838_dir: Path = DEFAULT_M2838_DIR,
    m2828_dir: Path = DEFAULT_M2828_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    workload_rows = _read_csv_rows(m1690_workload)
    specs = _artifact_specs(m2877_dir, m2868_dir, m2838_dir, m2828_dir)
    source_rows = build_source_inventory_rows(specs)
    candidate_tags, guard_tags, source_family_tags, execution_columns = _artifact_maps(specs)
    target_rows = build_target_inventory_rows(execution_columns)
    targets_available = bool(target_rows) and all(_bool(row["status_pass"]) for row in target_rows)
    candidate_rows = build_candidate_panel_rows(
        workload_rows=workload_rows,
        candidate_tags=candidate_tags,
        guard_tags=guard_tags,
        source_family_tags=source_family_tags,
        targets_available=targets_available,
    )
    actor_rows = build_actor_contract_rows()
    claim_rows = build_claim_rows()
    gate_rows = build_gate_rows(
        workload_exists=m1690_workload.exists(),
        candidate_rows=candidate_rows,
        source_rows=source_rows,
        target_rows=target_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
    )
    classification_counts = Counter(str(row["classification"]) for row in candidate_rows)
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    usable_candidate_count = classification_counts.get("usable", 0)
    decision = (
        "panel_inventory_available_route_to_m2885_result_audit"
        if gate_matrix_pass and usable_candidate_count > 0
        else "panel_inventory_insufficient_route_to_m2885_result_audit"
    )
    artifacts = {
        "summary": output_dir / "summary.json",
        "candidate_panel_rows": output_dir / "candidate_panel_rows.csv",
        "source_inventory_rows": output_dir / "source_inventory_rows.csv",
        "target_inventory_rows": output_dir / "target_inventory_rows.csv",
        "actor_contract_rows": output_dir / "actor_contract_rows.csv",
        "gate_rows": output_dir / "gate_rows.csv",
        "claim_rows": output_dir / "claim_rows.csv",
        "run_state": output_dir / "run_state.json",
    }
    baseline_checkpoints = [
        "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
        "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
    ]
    summary: dict[str, Any] = {
        "milestone": DEFAULT_MILESTONE,
        "generated_at_utc": utc_timestamp(),
        "status_pass": gate_matrix_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": decision,
        "next_blocker": DEFAULT_NEXT_BLOCKER,
        "m1690_workload": str(m1690_workload),
        "m1690_workload_exists": m1690_workload.exists(),
        "workload_row_count": len(workload_rows),
        "candidate_panel_row_count": len(candidate_rows),
        "source_inventory_row_count": len(source_rows),
        "target_inventory_row_count": len(target_rows),
        "actor_contract_row_count": len(actor_rows),
        "gate_row_count": len(gate_rows),
        "claim_row_count": len(claim_rows),
        "usable_candidate_count": usable_candidate_count,
        "source_singleton_candidate_count": classification_counts.get("source-singleton", 0),
        "guard_candidate_count": classification_counts.get("guard", 0),
        "missing_data_candidate_count": classification_counts.get("missing-data", 0),
        "classification_counts": dict(sorted(classification_counts.items())),
        "profile_matrix_required_count": len(REQUIRED_PROFILES),
        "target_inventory_all_available": targets_available,
        "actor_contract_shape_72_action_3": all(_bool(row["status_pass"]) for row in actor_rows),
        "hidden_oracle_actor_input_required": False,
        "evaluator_targets_actor_visible": False,
        "false_claim_flags": FALSE_CLAIM_FLAGS.copy(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "baseline_checkpoints": baseline_checkpoints,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "follow_up_manifest": str(follow_up_manifest),
    }
    follow_up = build_follow_up_manifest(summary)
    follow_up_manifest.parent.mkdir(parents=True, exist_ok=True)
    write_json(follow_up_manifest, follow_up)
    summary["follow_up_manifest_exists"] = follow_up_manifest.exists()

    write_csv_rows(artifacts["candidate_panel_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(artifacts["source_inventory_rows"], source_rows, fieldnames=SOURCE_FIELDNAMES)
    write_csv_rows(artifacts["target_inventory_rows"], target_rows, fieldnames=TARGET_FIELDNAMES)
    write_csv_rows(artifacts["actor_contract_rows"], actor_rows, fieldnames=ACTOR_FIELDNAMES)
    write_csv_rows(artifacts["gate_rows"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_csv_rows(artifacts["claim_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(artifacts["run_state"], {"summary": summary, "follow_up_manifest": follow_up})
    write_json(artifacts["summary"], summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_M1690_WORKLOAD)
    parser.add_argument("--m2877-dir", type=Path, default=DEFAULT_M2877_DIR)
    parser.add_argument("--m2868-dir", type=Path, default=DEFAULT_M2868_DIR)
    parser.add_argument("--m2838-dir", type=Path, default=DEFAULT_M2838_DIR)
    parser.add_argument("--m2828-dir", type=Path, default=DEFAULT_M2828_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = write_preflight_artifacts(
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        m1690_workload=args.m1690_workload,
        m2877_dir=args.m2877_dir,
        m2868_dir=args.m2868_dir,
        m2838_dir=args.m2838_dir,
        m2828_dir=args.m2828_dir,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"decision={summary['decision']}")
    print(f"usable_candidate_count={summary['usable_candidate_count']}")


if __name__ == "__main__":
    main()
