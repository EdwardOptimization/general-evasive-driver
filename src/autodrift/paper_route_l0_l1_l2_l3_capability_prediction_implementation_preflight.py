"""Implementation preflight for Route B capability prediction.

M2893 turns the accepted M2891/M2892 modeling contract into code-level schema,
loader, target-mask, and model-head shape smoke artifacts. It intentionally
does not fit, train, validate, rank, promote, or claim prediction quality.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import REQUIRED_PROFILES


DEFAULT_MILESTONE = "m2893-paper-route-l0-l1-l2-l3-capability-prediction-implementation-preflight"
DEFAULT_NEXT_BLOCKER = "m2894-paper-route-l0-l1-l2-l3-capability-prediction-implementation-result-audit"
DEFAULT_OUTPUT_DIR = Path("runs/m2893_paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight")
DEFAULT_M2891_DIR = Path("runs/m2891_paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract_materialization_preflight")
DEFAULT_M2892_AUDIT = Path(
    "docs/m2892-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-result-audit.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2894-paper-route-l0-l1-l2-l3-capability-prediction-implementation-result-audit.json"
)

CLAIM_SCOPE = (
    "M2893 capability-prediction implementation preflight only. It reads accepted "
    "M2891/M2892 contract artifacts and writes schema, loader smoke, target-mask, "
    "model-head shape, gate, and claim rows. It does not reset, step, rollout, "
    "replay, validate, fit a model, train, run PPO, run an optimizer step, persist "
    "fitted weights, rank controllers, select a winner, promote a checkpoint, "
    "publish a package, or claim model quality, driver performance, paper evidence, "
    "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity validation, "
    "full-driver completion, or level3 self-ID."
)
FORBIDDEN_INTERPRETATION = (
    "model quality, driver performance, controller-family ranking, profile ranking, "
    "checkpoint promotion, finite-window-vs-GRU verdict, paper result, current-sim "
    "verdict, validation readiness/result, high-fidelity validation, full-driver "
    "completion, or level3 self-identification"
)

FALSE_CLAIM_FLAGS = {
    "dependency_mutation_performed": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "validation_run": False,
    "model_fitting_run": False,
    "optimizer_step_run": False,
    "fitted_weights_persisted": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "package_published": False,
    "model_quality_claim_made": False,
    "driver_performance_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

SCHEMA_FIELDNAMES = [
    "schema_row_id",
    "schema_family",
    "source_contract_id",
    "profile_name",
    "profile_level",
    "target_family",
    "feature_family",
    "input_shape",
    "feature_scalar_dim",
    "sequence_length",
    "target_columns",
    "target_scalar_dim",
    "availability_mask_required",
    "actor_visible_allowed",
    "hidden_oracle_input_allowed",
    "future_target_input_allowed",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
LOADER_FIELDNAMES = [
    "loader_smoke_id",
    "profile_name",
    "profile_level",
    "sample_count",
    "input_shape",
    "feature_scalar_dim",
    "target_family_count",
    "target_scalar_dim",
    "availability_mask_shape",
    "paper_holdout_admitted",
    "preflight_only_split",
    "actor_visible_target_fields",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "optimizer_step_scheduled",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
MODEL_HEAD_FIELDNAMES = [
    "model_head_smoke_id",
    "profile_name",
    "profile_level",
    "feature_family",
    "model_head_kind",
    "input_shape",
    "output_shape",
    "target_scalar_dim",
    "shape_contract_materialized",
    "optimizer_step_run",
    "fitted_weights_persisted",
    "training_scheduled",
    "validation_scheduled",
    "status_pass",
    "failure_type",
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


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _pipe_items(value: str) -> list[str]:
    return [item for item in str(value).split("|") if item]


def _parse_expected_shape(shape: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for token in str(shape).split(";"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        parts[key.strip()] = value.strip()
    return parts


def _int_part(parts: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(parts.get(key, default))
    except (TypeError, ValueError):
        return default


def _feature_shape(row: dict[str, str]) -> dict[str, Any]:
    parts = _parse_expected_shape(row.get("expected_shape", ""))
    obs_dim = _int_part(parts, "obs")
    window = _int_part(parts, "window", 1)
    hidden = parts.get("hidden", "")
    if hidden:
        input_shape = f"batch,obs={obs_dim};hidden={hidden}"
        sequence_length = 1
        feature_scalar_dim = obs_dim
    elif window > 1:
        input_shape = f"batch,window={window},obs={obs_dim}"
        sequence_length = window
        feature_scalar_dim = obs_dim * window
    else:
        input_shape = f"batch,obs={obs_dim}"
        sequence_length = 1
        feature_scalar_dim = obs_dim
    return {
        "input_shape": input_shape,
        "feature_scalar_dim": feature_scalar_dim,
        "sequence_length": sequence_length,
        "obs_dim": obs_dim,
        "hidden": hidden,
    }


def _target_dim(label_rows: list[dict[str, str]]) -> int:
    return sum(len(_pipe_items(row.get("required_columns", ""))) for row in label_rows)


def _model_head_kind(feature_family: str) -> str:
    if feature_family == "recurrent_hidden_state":
        return "recurrent_state_readout_shape_contract"
    if feature_family in {"finite_window_command_response_history", "current_tiled_history_control"}:
        return "temporal_pool_or_flatten_shape_contract"
    return "mlp_readout_shape_contract"


def build_schema_rows(
    feature_contract_rows: list[dict[str, str]],
    label_contract_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(feature_contract_rows, start=1):
        shape = _feature_shape(row)
        status_pass = (
            _bool(row.get("status_pass"))
            and _bool(row.get("actor_visible_allowed"))
            and not _bool(row.get("hidden_oracle_input_allowed"))
            and not _bool(row.get("future_target_input_allowed"))
            and shape["obs_dim"] == P0_OBSERVATION_DIM
        )
        rows.append(
            {
                "schema_row_id": f"m2893-feature-schema-{index:04d}",
                "schema_family": "actor_feature_schema",
                "source_contract_id": row.get("feature_contract_id", ""),
                "profile_name": row.get("profile_name", ""),
                "profile_level": row.get("profile_level", ""),
                "target_family": "",
                "feature_family": row.get("feature_family", ""),
                "input_shape": shape["input_shape"],
                "feature_scalar_dim": shape["feature_scalar_dim"],
                "sequence_length": shape["sequence_length"],
                "target_columns": "",
                "target_scalar_dim": "",
                "availability_mask_required": "",
                "actor_visible_allowed": _bool(row.get("actor_visible_allowed")),
                "hidden_oracle_input_allowed": _bool(row.get("hidden_oracle_input_allowed")),
                "future_target_input_allowed": _bool(row.get("future_target_input_allowed")),
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )

    for index, row in enumerate(label_contract_rows, start=1):
        target_columns = _pipe_items(row.get("required_columns", ""))
        status_pass = (
            _bool(row.get("status_pass"))
            and not _bool(row.get("actor_visible_allowed"))
            and row.get("target_visibility") == "evaluator_only_actor_invisible"
            and bool(target_columns)
        )
        rows.append(
            {
                "schema_row_id": f"m2893-label-schema-{index:04d}",
                "schema_family": "evaluator_label_schema",
                "source_contract_id": row.get("label_contract_id", ""),
                "profile_name": "",
                "profile_level": "",
                "target_family": row.get("target_family", ""),
                "feature_family": "",
                "input_shape": "",
                "feature_scalar_dim": "",
                "sequence_length": "",
                "target_columns": "|".join(target_columns),
                "target_scalar_dim": len(target_columns),
                "availability_mask_required": True,
                "actor_visible_allowed": _bool(row.get("actor_visible_allowed")),
                "hidden_oracle_input_allowed": False,
                "future_target_input_allowed": False,
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_loader_smoke_rows(
    feature_contract_rows: list[dict[str, str]],
    label_contract_rows: list[dict[str, str]],
    baseline_contract_rows: list[dict[str, str]],
    split_contract_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    features_by_profile = {row.get("profile_name", ""): row for row in feature_contract_rows}
    feature_schema_by_profile = {row["profile_name"]: row for row in build_schema_rows(feature_contract_rows, [])}
    target_scalar_dim = _target_dim(label_contract_rows)
    target_family_count = len(label_contract_rows)
    paper_holdout_admitted = any(_bool(row.get("paper_holdout_admitted")) for row in split_contract_rows)
    preflight_only_split = bool(split_contract_rows) and all(_bool(row.get("preflight_only")) for row in split_contract_rows)
    labels_actor_visible = any(_bool(row.get("actor_visible_allowed")) for row in label_contract_rows)

    rows: list[dict[str, Any]] = []
    for index, row in enumerate(baseline_contract_rows, start=1):
        profile = row.get("profile_name", "")
        feature_row = features_by_profile.get(profile, {})
        schema_row = feature_schema_by_profile.get(profile, {})
        sample_count = int(row.get("profile_task_count", 0) or 0)
        hidden_oracle = _bool(feature_row.get("hidden_oracle_input_allowed"))
        future_target = _bool(feature_row.get("future_target_input_allowed"))
        status_pass = (
            _bool(row.get("status_pass"))
            and _bool(feature_row.get("status_pass"))
            and sample_count > 0
            and target_scalar_dim > 0
            and not labels_actor_visible
            and not hidden_oracle
            and not future_target
            and not paper_holdout_admitted
            and preflight_only_split
            and not _bool(row.get("training_scheduled"))
            and not _bool(row.get("environment_rollout_scheduled"))
            and not _bool(row.get("profile_specific_tuning"))
        )
        rows.append(
            {
                "loader_smoke_id": f"m2893-loader-smoke-{index:04d}",
                "profile_name": profile,
                "profile_level": row.get("profile_level", ""),
                "sample_count": sample_count,
                "input_shape": schema_row.get("input_shape", ""),
                "feature_scalar_dim": schema_row.get("feature_scalar_dim", ""),
                "target_family_count": target_family_count,
                "target_scalar_dim": target_scalar_dim,
                "availability_mask_shape": f"batch={sample_count};target_dim={target_scalar_dim}",
                "paper_holdout_admitted": paper_holdout_admitted,
                "preflight_only_split": preflight_only_split,
                "actor_visible_target_fields": labels_actor_visible,
                "hidden_oracle_actor_input_required": hidden_oracle,
                "future_target_actor_input_required": future_target,
                "optimizer_step_scheduled": False,
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_model_head_smoke_rows(
    feature_contract_rows: list[dict[str, str]],
    loader_smoke_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    feature_by_profile = {row.get("profile_name", ""): row for row in feature_contract_rows}
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(loader_smoke_rows, start=1):
        profile = row.get("profile_name", "")
        feature_row = feature_by_profile.get(str(profile), {})
        target_scalar_dim = int(row.get("target_scalar_dim", 0) or 0)
        feature_family = feature_row.get("feature_family", "")
        status_pass = (
            _bool(row.get("status_pass"))
            and target_scalar_dim > 0
            and not _bool(row.get("optimizer_step_scheduled"))
            and not _bool(feature_row.get("hidden_oracle_input_allowed"))
            and not _bool(feature_row.get("future_target_input_allowed"))
        )
        rows.append(
            {
                "model_head_smoke_id": f"m2893-model-head-smoke-{index:04d}",
                "profile_name": profile,
                "profile_level": row.get("profile_level", ""),
                "feature_family": feature_family,
                "model_head_kind": _model_head_kind(feature_family),
                "input_shape": row.get("input_shape", ""),
                "output_shape": f"batch,target_dim={target_scalar_dim}",
                "target_scalar_dim": target_scalar_dim,
                "shape_contract_materialized": True,
                "optimizer_step_run": False,
                "fitted_weights_persisted": False,
                "training_scheduled": False,
                "validation_scheduled": False,
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_claim_rows() -> list[dict[str, Any]]:
    allowed_specs = [
        ("implementation_preflight", "implementation preflight completeness", "M2893 summary and row artifacts"),
        ("schema_rows_materialized", "schema rows materialized", "schema_rows.csv"),
        ("loader_smoke_rows_materialized", "loader smoke rows materialized", "loader_smoke_rows.csv"),
        ("target_masks_materialized", "target availability masks materialized", "loader_smoke_rows.csv"),
        ("model_head_shape_rows_materialized", "model-head shape smoke rows materialized", "model_head_smoke_rows.csv"),
        ("bounded_audit_handoff", "bounded result-audit handoff", "M2894 manifest"),
    ]
    blocked_specs = [
        ("optimizer_step", "optimizer step", "separate fitting or training manifest"),
        ("fitted_weights", "fitted weights", "separate fitting or training manifest"),
        ("model_fitting", "model fitting", "separate fitting or training manifest"),
        ("training", "training", "separate training manifest with holdout policy"),
        ("validation", "validation", "separate evaluation manifest"),
        ("controller_ranking", "controller-family ranking", "fair comparison evidence and audit"),
        ("model_quality", "model quality", "accepted training and validation evidence"),
        ("driver_performance", "driver performance", "closed-loop validation and promotion evidence"),
        ("finite_window_vs_gru", "finite-window-vs-GRU verdict", "separate fair L0/L1/L2/L3 comparison"),
        ("paper", "paper result", "paper-route audit and holdout evidence"),
        ("self_id", "level3 self-ID", "source-diverse history-necessity intervention evidence"),
    ]
    rows = [
        {
            "claim_id": f"m2893-claim-{claim_id}",
            "claim_family": claim_family,
            "claim_made": True,
            "claim_allowed": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, claim_family, evidence in allowed_specs
    ]
    rows.extend(
        {
            "claim_id": f"m2893-claim-{claim_id}",
            "claim_family": claim_family,
            "claim_made": False,
            "claim_allowed": False,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, claim_family, evidence in blocked_specs
    )
    return rows


def build_gate_rows(
    *,
    m2891_summary: dict[str, Any],
    m2892_audit_exists: bool,
    artifact_exists: dict[str, bool],
    feature_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
    split_rows: list[dict[str, str]],
    baseline_rows: list[dict[str, str]],
    schema_rows: list[dict[str, Any]],
    loader_rows: list[dict[str, Any]],
    model_head_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    feature_schema_rows = [row for row in schema_rows if row["schema_family"] == "actor_feature_schema"]
    label_schema_rows = [row for row in schema_rows if row["schema_family"] == "evaluator_label_schema"]
    paper_holdout_admitted = any(_bool(row.get("paper_holdout_admitted")) for row in split_rows)
    preflight_only_split = bool(split_rows) and all(_bool(row.get("preflight_only")) for row in split_rows)
    hidden_oracle_required = any(_bool(row.get("hidden_oracle_input_allowed")) for row in feature_rows)
    future_target_required = any(_bool(row.get("future_target_input_allowed")) for row in feature_rows)
    labels_actor_visible = any(_bool(row.get("actor_visible_allowed")) for row in label_rows)
    blocked_claim_gate_pass = all(_bool(row["claim_allowed"]) or not _bool(row["claim_made"]) for row in claim_rows)

    def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": status,
            "observed": observed,
            "expected": expected,
            "failure_type": "none" if status else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    return [
        gate(
            "m2893-parent-contract-accepted",
            "lineage",
            _bool(m2891_summary.get("status_pass")) and _bool(m2891_summary.get("gate_matrix_pass")) and m2892_audit_exists,
            f"m2891_status={m2891_summary.get('status_pass')};m2891_gates={m2891_summary.get('gate_matrix_pass')};m2892_audit_exists={m2892_audit_exists}",
            "m2891_status=True;m2891_gates=True;m2892_audit_exists=True",
            "lineage_invalid",
        ),
        gate(
            "m2893-contract-artifacts-read",
            "artifact_completeness",
            all(artifact_exists.values()) and all([feature_rows, label_rows, split_rows, baseline_rows]),
            ";".join(f"{name}={exists}" for name, exists in sorted(artifact_exists.items())),
            "all_required_contract_artifacts=True",
            "lineage_invalid",
        ),
        gate(
            "m2893-schema-rows-pass",
            "schema_contract",
            bool(schema_rows) and all(_bool(row["status_pass"]) for row in schema_rows),
            f"feature_schema={len(feature_schema_rows)};label_schema={len(label_schema_rows)}",
            "feature_schema=12;label_schema>=1",
            "contract_violation",
        ),
        gate(
            "m2893-loader-smoke-rows-pass",
            "loader_smoke",
            bool(loader_rows) and all(_bool(row["status_pass"]) for row in loader_rows),
            len(loader_rows),
            len(baseline_rows),
            "contract_violation",
        ),
        gate(
            "m2893-model-head-shape-smoke-rows-pass",
            "model_head_smoke",
            bool(model_head_rows) and all(_bool(row["status_pass"]) for row in model_head_rows),
            len(model_head_rows),
            len(baseline_rows),
            "contract_violation",
        ),
        gate(
            "m2893-actor-target-boundary-preserved",
            "actor_contract",
            P0_OBSERVATION_DIM == 72
            and ACTION_DIM == 3
            and not hidden_oracle_required
            and not future_target_required
            and not labels_actor_visible,
            f"obs={P0_OBSERVATION_DIM};action={ACTION_DIM};hidden_oracle={hidden_oracle_required};future_target={future_target_required};labels_actor_visible={labels_actor_visible}",
            "obs=72;action=3;hidden_oracle=False;future_target=False;labels_actor_visible=False",
            "contract_violation",
        ),
        gate(
            "m2893-exclusions-and-holdout-preserved",
            "proof_boundary",
            not paper_holdout_admitted
            and preflight_only_split
            and not _bool(m2891_summary.get("source_singleton_rows_paper_proof_allowed"))
            and not _bool(m2891_summary.get("guard_rows_ordinary_success_denominator_allowed")),
            f"paper_holdout={paper_holdout_admitted};preflight_only={preflight_only_split};source_singleton_proof={m2891_summary.get('source_singleton_rows_paper_proof_allowed')};guard_denominator={m2891_summary.get('guard_rows_ordinary_success_denominator_allowed')}",
            "paper_holdout=False;preflight_only=True;source_singleton_proof=False;guard_denominator=False",
            "proof_washout",
        ),
        gate(
            "m2893-no-fitting-training-validation-ranking",
            "claim_boundary",
            not any(FALSE_CLAIM_FLAGS.values()) and blocked_claim_gate_pass,
            sum(_bool(row["claim_made"]) and not _bool(row["claim_allowed"]) for row in claim_rows),
            0,
            "contract_violation",
        ),
        gate(
            "m2893-follow-up-manifest-registered",
            "handoff",
            follow_up_manifest.exists(),
            follow_up_manifest.exists(),
            True,
            "lineage_invalid",
        ),
    ]


def build_follow_up_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "hypothesis": "A bounded result audit can accept or reject the M2893 capability-prediction implementation preflight before any fitting training validation ranking or model-quality claim.",
        "lineage": {
            "parent_checkpoint": summary["baseline_checkpoints"],
            "parent_dataset": [
                summary["artifacts"]["summary"],
                summary["artifacts"]["schema_rows"],
                summary["artifacts"]["loader_smoke_rows"],
                summary["artifacts"]["model_head_smoke_rows"],
                summary["artifacts"]["gate_rows"],
                summary["artifacts"]["claim_rows"],
                summary.get("m2892_audit", str(DEFAULT_M2892_AUDIT)),
                summary.get("m2891_summary", str(DEFAULT_M2891_DIR / "summary.json")),
            ],
            "parent_config": [
                f"experiments/manifests/{DEFAULT_MILESTONE}.json",
                "experiments/manifests/m2892-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-result-audit.json",
                "experiments/manifests/m2891-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-preflight.json",
            ],
            "parent_objective": [
                "audit whether M2893 materialized actor-safe implementation preflight smoke artifacts"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2892-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-result-audit",
                "m2891-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-preflight",
            ],
            "blocked_by": [
                "M2893 must be audited before any fitting training validation ranking or model-quality claim",
                "schema loader and model-head smoke artifacts remain preflight evidence only",
                "17 usable rows remain public and preflight-only",
            ],
            "supersedes": [
                "starting capability-prediction fitting without implementation-preflight audit",
                "treating schema loader or model-head shape smoke as model quality evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2894 must audit M2893 summary schema loader smoke model-head gate and claim rows",
            "M2894 must accept or reject actor-safe implementation-preflight completeness",
            "M2894 must preserve no optimizer fitting training validation ranking promotion or model-quality claims",
            "M2894 must preserve actor target exclusion holdout and preflight-only split boundaries",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout replay validate fit a model train rank promote or publish a package",
            "do not run optimizer steps or persist fitted weights",
            "do not convert implementation-preflight smoke into model-quality paper or controller-family ranking claims",
            "do not claim driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
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
            "branch": "paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract",
            "evidence_axis": "route_b_capability_prediction_implementation_result_audit",
            "evidence_increment": "audits code-level schema loader and model-head smoke artifacts before any fitting",
            "claim_scope": "Result audit only; no fitting training validation ranking model quality finite-window-vs-GRU verdict driver performance paper current-sim high-fidelity full-driver or self-ID claim",
            "stop_condition": [
                "stop if schema loader target masks or model-head smoke rows are incomplete",
                "stop if actor or evaluator-only target boundaries fail",
                "stop if M2894 would claim model quality driver performance or self-ID evidence",
            ],
            "fallback_plan": [
                "route to implementation repair if smoke artifacts are incomplete but actor-safe",
                "route to contract repair if M2891 rows are insufficient",
                "route to synthesis or fresh/source-diverse panel design if the branch is becoming public-row overfit",
                "route to fitting/training design only if audit accepts implementation completeness and boundaries",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2893 writes implementation-preflight smoke artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "M2893 capability-prediction implementation-preflight result audit",
            "admission_evidence": [
                "M2893 wrote implementation-preflight smoke artifacts",
                "M2892 admitted implementation preflight only before fitting or training",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation model fitting training ranking promotion",
                "no optimizer step and no fitted weights",
                "no hidden or oracle actor inputs",
                "no source-singleton or guard rows as paper proof",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "M2894 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if the audit selects a route",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "M2893 implementation preflight is accepted or rejected",
                "one next Route B action or stop decision is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2894 audits implementation preflight only and does not test history necessity.",
            "history_necessity_tests": [
                "None in M2894; later tests require accepted fitting/training and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": "M2887-M2893 Route B dataset modeling-contract and implementation-preflight artifacts.",
            "negative_result_policy": "Preserve insufficient implementation or boundary failure as a negative result rather than weakening actor contract.",
            "allowed_claims": [
                "M2893 implementation preflight accepted or rejected",
                "bounded follow-up route or stop decision",
                "no model-quality driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "low",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0 if summary["status_pass"] else 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the newly materialized implementation-preflight smoke artifacts",
            "paper_verdict_delta": "no verdict; may admit later fitting or training design if accepted",
            "must_synthesize_if": [
                "M2894 cannot decide whether M2893 implementation preflight is sufficient",
                "M2894 would claim self-ID finite-window-vs-GRU driver performance model quality or current-sim verdict",
            ],
        },
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "audit accepts or rejects M2893 implementation-preflight completeness and claim safety",
            "audit selects exactly one bounded next route or stop decision",
        ],
        "failure_criteria": [
            "M2894 resets steps rolls out validates fits trains ranks promotes or executes policy action",
            "M2894 changes actor input or action contract",
            "M2894 claims model quality driver performance finite-window-vs-GRU verdict paper current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "decision_rule": "Pass only if M2894 writes a claim-safe audit of M2893 implementation preflight before any fitting training validation ranking or verdict claim.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{DEFAULT_NEXT_BLOCKER}.md", "type": "md"}],
        "baseline_checkpoints": summary["baseline_checkpoints"],
        "baseline_artifacts": [
            summary["artifacts"]["summary"],
            summary["artifacts"]["schema_rows"],
            summary["artifacts"]["loader_smoke_rows"],
            summary["artifacts"]["model_head_smoke_rows"],
            summary["artifacts"]["gate_rows"],
            summary["artifacts"]["claim_rows"],
        ],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "m2895-paper-route-l0-l1-l2-l3-capability-prediction-selected-implementation-follow-up",
    }


def write_preflight_artifacts(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
    m2891_dir: Path = DEFAULT_M2891_DIR,
    m2892_audit: Path = DEFAULT_M2892_AUDIT,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": m2891_dir / "summary.json",
        "feature_contract_rows": m2891_dir / "feature_contract_rows.csv",
        "label_contract_rows": m2891_dir / "label_contract_rows.csv",
        "split_contract_rows": m2891_dir / "split_contract_rows.csv",
        "loss_metric_contract_rows": m2891_dir / "loss_metric_contract_rows.csv",
        "baseline_contract_rows": m2891_dir / "baseline_contract_rows.csv",
        "modeling_gate_rows": m2891_dir / "modeling_gate_rows.csv",
        "claim_rows": m2891_dir / "claim_rows.csv",
    }
    artifact_exists = {key: path.exists() for key, path in paths.items()}

    m2891_summary = read_json(paths["summary"]) if paths["summary"].exists() else {}
    feature_rows = _read_csv_rows(paths["feature_contract_rows"])
    label_rows = _read_csv_rows(paths["label_contract_rows"])
    split_rows = _read_csv_rows(paths["split_contract_rows"])
    _loss_metric_rows = _read_csv_rows(paths["loss_metric_contract_rows"])
    baseline_rows = _read_csv_rows(paths["baseline_contract_rows"])
    _modeling_gate_rows = _read_csv_rows(paths["modeling_gate_rows"])
    _parent_claim_rows = _read_csv_rows(paths["claim_rows"])

    schema_rows = build_schema_rows(feature_rows, label_rows)
    loader_rows = build_loader_smoke_rows(feature_rows, label_rows, baseline_rows, split_rows)
    model_head_rows = build_model_head_smoke_rows(feature_rows, loader_rows)
    claim_rows = build_claim_rows()

    artifacts = {
        "summary": output_dir / "summary.json",
        "schema_rows": output_dir / "schema_rows.csv",
        "loader_smoke_rows": output_dir / "loader_smoke_rows.csv",
        "model_head_smoke_rows": output_dir / "model_head_smoke_rows.csv",
        "gate_rows": output_dir / "gate_rows.csv",
        "claim_rows": output_dir / "claim_rows.csv",
        "run_state": output_dir / "run_state.json",
    }

    baseline_checkpoints = list(m2891_summary.get("baseline_checkpoints", [])) or [
        "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
        "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
    ]

    summary_stub = {
        "baseline_checkpoints": baseline_checkpoints,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "status_pass": False,
        "m2891_summary": str(paths["summary"]),
        "m2892_audit": str(m2892_audit),
    }
    follow_up_manifest.parent.mkdir(parents=True, exist_ok=True)
    write_json(follow_up_manifest, build_follow_up_manifest(summary_stub))

    gate_rows = build_gate_rows(
        m2891_summary=m2891_summary,
        m2892_audit_exists=m2892_audit.exists(),
        artifact_exists=artifact_exists,
        feature_rows=feature_rows,
        label_rows=label_rows,
        split_rows=split_rows,
        baseline_rows=baseline_rows,
        schema_rows=schema_rows,
        loader_rows=loader_rows,
        model_head_rows=model_head_rows,
        claim_rows=claim_rows,
        follow_up_manifest=follow_up_manifest,
    )
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    feature_schema_rows = [row for row in schema_rows if row["schema_family"] == "actor_feature_schema"]
    label_schema_rows = [row for row in schema_rows if row["schema_family"] == "evaluator_label_schema"]
    profile_level_counts = Counter(row.get("profile_level", "") for row in baseline_rows)
    target_scalar_dim = _target_dim(label_rows)
    decision = (
        "implementation_preflight_pass_route_to_m2894_result_audit"
        if gate_matrix_pass
        else "implementation_preflight_incomplete_route_to_m2894_result_audit"
    )

    summary: dict[str, Any] = {
        "milestone": DEFAULT_MILESTONE,
        "generated_at_utc": utc_timestamp(),
        "status_pass": gate_matrix_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": decision,
        "next_blocker": DEFAULT_NEXT_BLOCKER,
        "m2891_dir": str(m2891_dir),
        "m2891_summary": str(paths["summary"]),
        "m2891_summary_exists": paths["summary"].exists(),
        "m2891_summary_status_pass": _bool(m2891_summary.get("status_pass")),
        "m2891_gate_matrix_pass": _bool(m2891_summary.get("gate_matrix_pass")),
        "m2892_audit": str(m2892_audit),
        "m2892_audit_exists": m2892_audit.exists(),
        "feature_contract_row_count": len(feature_rows),
        "label_contract_row_count": len(label_rows),
        "split_contract_row_count": len(split_rows),
        "baseline_contract_row_count": len(baseline_rows),
        "schema_row_count": len(schema_rows),
        "feature_schema_row_count": len(feature_schema_rows),
        "label_schema_row_count": len(label_schema_rows),
        "loader_smoke_row_count": len(loader_rows),
        "model_head_smoke_row_count": len(model_head_rows),
        "gate_row_count": len(gate_rows),
        "claim_row_count": len(claim_rows),
        "target_family_count": len(label_rows),
        "target_scalar_dim": target_scalar_dim,
        "profile_level_counts": dict(sorted(profile_level_counts.items())),
        "required_profile_count": len(REQUIRED_PROFILES),
        "required_profiles": REQUIRED_PROFILES,
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "hidden_oracle_actor_input_required": any(_bool(row.get("hidden_oracle_input_allowed")) for row in feature_rows),
        "future_target_actor_input_required": any(_bool(row.get("future_target_input_allowed")) for row in feature_rows),
        "evaluator_targets_actor_visible": any(_bool(row.get("actor_visible_allowed")) for row in label_rows),
        "paper_holdout_admitted": any(_bool(row.get("paper_holdout_admitted")) for row in split_rows),
        "preflight_only_split": bool(split_rows) and all(_bool(row.get("preflight_only")) for row in split_rows),
        "source_singleton_rows_paper_proof_allowed": _bool(
            m2891_summary.get("source_singleton_rows_paper_proof_allowed")
        ),
        "guard_rows_ordinary_success_denominator_allowed": _bool(
            m2891_summary.get("guard_rows_ordinary_success_denominator_allowed")
        ),
        "schema_rows_all_pass": bool(schema_rows) and all(_bool(row["status_pass"]) for row in schema_rows),
        "loader_smoke_rows_all_pass": bool(loader_rows) and all(_bool(row["status_pass"]) for row in loader_rows),
        "model_head_smoke_rows_all_pass": bool(model_head_rows)
        and all(_bool(row["status_pass"]) for row in model_head_rows),
        "optimizer_step_run": False,
        "fitted_weights_persisted": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "model_quality_claim_made": False,
        "false_claim_flags": FALSE_CLAIM_FLAGS.copy(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "baseline_checkpoints": baseline_checkpoints,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "input_artifacts": {key: str(value) for key, value in paths.items()},
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
    }

    write_csv_rows(artifacts["schema_rows"], schema_rows, fieldnames=SCHEMA_FIELDNAMES)
    write_csv_rows(artifacts["loader_smoke_rows"], loader_rows, fieldnames=LOADER_FIELDNAMES)
    write_csv_rows(artifacts["model_head_smoke_rows"], model_head_rows, fieldnames=MODEL_HEAD_FIELDNAMES)
    write_csv_rows(artifacts["gate_rows"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_csv_rows(artifacts["claim_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(artifacts["run_state"], {"summary": summary, "follow_up_manifest": build_follow_up_manifest(summary)})
    write_json(artifacts["summary"], summary)
    write_json(follow_up_manifest, build_follow_up_manifest(summary))
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--m2891-dir", type=Path, default=DEFAULT_M2891_DIR)
    parser.add_argument("--m2892-audit", type=Path, default=DEFAULT_M2892_AUDIT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = write_preflight_artifacts(
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        m2891_dir=args.m2891_dir,
        m2892_audit=args.m2892_audit,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"decision={summary['decision']}")
    print(f"schema_row_count={summary['schema_row_count']}")
    print(f"loader_smoke_row_count={summary['loader_smoke_row_count']}")
    print(f"model_head_smoke_row_count={summary['model_head_smoke_row_count']}")


if __name__ == "__main__":
    main()
