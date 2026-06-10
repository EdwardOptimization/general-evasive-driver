"""Materialize M3156 Route A deployable benchmark pack artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = "m3156-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-materialization-preflight"
NEXT_ID = "m3157-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-result-audit"
M3155_ID = "m3155-engineering-controller-active-safety-driver-residual-action-delta-negative-counterfactual-replay-synthesis"
M3153_ID = (
    "m3153-engineering-controller-active-safety-driver-residual-action-delta-"
    "counterfactual-replay-diagnostic-materialization-preflight"
)
M3139_ID = "m3139-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-materialization-preflight"
M3105_ID = (
    "m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-"
    "hard-safety-direct-action-repair-full-fresh-measurement-preflight"
)

DEFAULT_M3155_SYNTHESIS = Path(f"docs/{M3155_ID}.md")
DEFAULT_M3139_DIR = Path(
    "runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_"
    "reflex_interface_materialization_preflight"
)
DEFAULT_M3105_DIR = Path(
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3153_DIR = Path(
    "runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_"
    "replay_diagnostic_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3156_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_"
    "materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_MEASUREMENT_ROWS = 64
EXPECTED_SUCCESS_ROWS = 57
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
EXPECTED_RESIDUAL_BLOCKERS = 7
EXPECTED_M3153_COMPARISONS = 21
CLAIM_SCOPE = (
    "M3156 Active Safety Driver Route A deployable benchmark pack materialization only; "
    "existing M3105/M3139/M3153 artifacts may be packaged into contract, benchmark metric, "
    "known-failure taxonomy, claim, gate, doc, and M3157 audit artifacts. No reset, step, "
    "rollout, replay, fitting, PPO, training, validation, ranking, winner selection, "
    "checkpoint mutation, checkpoint promotion, driver-performance verdict, current-sim "
    "verdict, repair success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility proof, or "
    "self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, robustness-result, "
    "repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal "
    "driver completion, feasibility proof, or level3 self-identification"
)

BENCHMARK_FIELDNAMES = [
    "metric_row_id",
    "metric_family",
    "metric_name",
    "value",
    "numerator",
    "denominator",
    "unit",
    "source_artifact",
    "included_in_route_a_pack",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
FAILURE_TAXONOMY_FIELDNAMES = [
    "failure_taxonomy_row_id",
    "source_blocker_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "blocker_family",
    "collision",
    "offtrack",
    "speed_too_low",
    "termination_reason",
    "outcome_bucket",
    "min_clearance_margin",
    "high_sideslip_fraction",
    "lateral_rmse",
    "return",
    "speed_mean",
    "m3153_comparison_count",
    "m3153_action_channel_sensitive_count",
    "m3153_dominant_counterfactual_label",
    "m3153_terminal_invariant",
    "known_failure_status",
    "claim_boundary",
]
CONTRACT_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed_value",
    "expected_value",
    "status_pass",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3156",
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


def _float(value: Any, default: float = float("nan")) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else ""


def _rate(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else 0.0


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "deployable_driver_contract_snapshot": output_dir / "deployable_driver_contract_snapshot.json",
        "deployable_benchmark_pack_manifest": output_dir / "deployable_benchmark_pack_manifest.json",
        "benchmark_metric_rows": output_dir / "benchmark_metric_rows.csv",
        "known_failure_taxonomy_rows": output_dir / "known_failure_taxonomy_rows.csv",
        "contract_guard_rows": output_dir / "contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3155_synthesis: Path, m3139_dir: Path, m3105_dir: Path, m3153_dir: Path) -> dict[str, Any]:
    paths = {
        "m3155_synthesis": m3155_synthesis,
        "m3139_summary": m3139_dir / "summary.json",
        "m3139_contract": m3139_dir / "deployable_contract.json",
        "m3139_action_probe_rows": m3139_dir / "action_probe_rows.csv",
        "m3139_residual_blocker_rows": m3139_dir / "residual_blocker_rows.csv",
        "m3139_gate_rows": m3139_dir / "gate_matrix.csv",
        "m3105_summary": m3105_dir / "summary.json",
        "m3105_measurement_rows": m3105_dir / "measurement_episode_rows.csv",
        "m3105_gate_rows": m3105_dir / "gate_matrix.csv",
        "m3153_summary": m3153_dir / "summary.json",
        "m3153_comparison_rows": m3153_dir / "counterfactual_replay_comparison_rows.csv",
        "m3153_gate_rows": m3153_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3155_synthesis_text": paths["m3155_synthesis"].read_text(encoding="utf-8") if exists["m3155_synthesis"] else "",
        "m3139_summary": read_json(paths["m3139_summary"]) if exists["m3139_summary"] else {},
        "m3139_contract": read_json(paths["m3139_contract"]) if exists["m3139_contract"] else {},
        "m3139_action_probe_rows": read_csv_rows(paths["m3139_action_probe_rows"]),
        "m3139_residual_blocker_rows": read_csv_rows(paths["m3139_residual_blocker_rows"]),
        "m3139_gate_rows": read_csv_rows(paths["m3139_gate_rows"]),
        "m3105_summary": read_json(paths["m3105_summary"]) if exists["m3105_summary"] else {},
        "m3105_measurement_rows": read_csv_rows(paths["m3105_measurement_rows"]),
        "m3105_gate_rows": read_csv_rows(paths["m3105_gate_rows"]),
        "m3153_summary": read_json(paths["m3153_summary"]) if exists["m3153_summary"] else {},
        "m3153_comparison_rows": read_csv_rows(paths["m3153_comparison_rows"]),
        "m3153_gate_rows": read_csv_rows(paths["m3153_gate_rows"]),
    }


def deployable_driver_contract_snapshot(source: Mapping[str, Any]) -> dict[str, Any]:
    driver = ActiveSafetyReflexDriver()
    contract = driver.contract_dict()
    sample_action = driver.act(np.zeros(P0_OBSERVATION_DIM, dtype=np.float32))
    return {
        "snapshot_id": "m3156-deployable-driver-contract-snapshot-0001",
        "driver_contract": contract,
        "source_m3139_contract": source.get("m3139_contract", {}),
        "sample_zero_observation_action": [float(value) for value in sample_action],
        "sample_action_finite": bool(np.all(np.isfinite(sample_action))),
        "sample_action_bounded": bool(float(np.max(np.abs(sample_action))) <= 1.0),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "validation_run": False,
        "driver_performance_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def _metric(
    rows: list[dict[str, Any]],
    family: str,
    name: str,
    value: Any,
    *,
    numerator: Any = "",
    denominator: Any = "",
    unit: str = "count",
    source_artifact: str,
) -> None:
    rows.append(
        {
            "metric_row_id": f"m3156-benchmark-metric-{len(rows) + 1:04d}",
            "metric_family": family,
            "metric_name": name,
            "value": value,
            "numerator": numerator,
            "denominator": denominator,
            "unit": unit,
            "source_artifact": source_artifact,
            "included_in_route_a_pack": True,
            "validation_run": False,
            "driver_performance_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    )


def benchmark_metric_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    summary = source.get("m3105_summary", {})
    m3153 = source.get("m3153_summary", {})
    measurement_rows = source.get("m3105_measurement_rows", [])
    residual_rows = source.get("m3139_residual_blocker_rows", [])
    episode_count = int(summary.get("measurement_episode_row_count", len(measurement_rows)) or 0)
    success_count = int(summary.get("measurement_success_count", sum(1 for row in measurement_rows if _bool(row.get("success", False)))) or 0)
    collision_count = int(summary.get("measurement_collision_count", sum(1 for row in measurement_rows if _bool(row.get("collision", False)))) or 0)
    offtrack_count = int(summary.get("measurement_offtrack_count", sum(1 for row in measurement_rows if str(row.get("termination_reason", "")) == "off_track")) or 0)
    speed_too_low_count = int(summary.get("measurement_speed_too_low_count", sum(1 for row in measurement_rows if str(row.get("termination_reason", "")) == "speed_too_low")) or 0)
    rows: list[dict[str, Any]] = []
    source_m3105 = "runs/m3105/summary_and_measurement_episode_rows"
    source_m3139 = "runs/m3139/residual_blocker_rows"
    source_m3153 = "runs/m3153/summary_and_counterfactual_replay_comparison_rows"
    _metric(rows, "denominator", "measurement_episode_count", episode_count, source_artifact=source_m3105)
    _metric(rows, "safety_outcome", "success_count", success_count, numerator=success_count, denominator=episode_count, source_artifact=source_m3105)
    _metric(rows, "safety_outcome", "success_rate", _rate(success_count, episode_count), numerator=success_count, denominator=episode_count, unit="rate", source_artifact=source_m3105)
    _metric(rows, "safety_outcome", "collision_count", collision_count, numerator=collision_count, denominator=episode_count, source_artifact=source_m3105)
    _metric(rows, "safety_outcome", "collision_rate", _rate(collision_count, episode_count), numerator=collision_count, denominator=episode_count, unit="rate", source_artifact=source_m3105)
    _metric(rows, "safety_outcome", "offtrack_count", offtrack_count, numerator=offtrack_count, denominator=episode_count, source_artifact=source_m3105)
    _metric(rows, "safety_outcome", "offtrack_rate", _rate(offtrack_count, episode_count), numerator=offtrack_count, denominator=episode_count, unit="rate", source_artifact=source_m3105)
    _metric(rows, "safety_outcome", "speed_too_low_count", speed_too_low_count, numerator=speed_too_low_count, denominator=episode_count, source_artifact=source_m3105)
    _metric(rows, "clearance", "clearance_margin_mean", summary.get("measurement_clearance_margin_mean", ""), unit="meters", source_artifact=source_m3105)
    _metric(rows, "stability", "high_sideslip_fraction_mean", summary.get("measurement_high_sideslip_fraction_mean", ""), unit="fraction", source_artifact=source_m3105)
    _metric(rows, "stability", "lateral_rmse_mean", summary.get("measurement_lateral_rmse_mean", ""), unit="meters", source_artifact=source_m3105)
    _metric(rows, "actuation", "action_clip_fraction_mean", summary.get("measurement_action_clip_fraction_mean", ""), unit="fraction", source_artifact=source_m3105)
    _metric(rows, "actuation", "raw_action_abs_max", summary.get("measurement_raw_action_abs_max", ""), unit="normalized_action", source_artifact=source_m3105)
    _metric(rows, "known_failures", "residual_blocker_count", len(residual_rows), numerator=len(residual_rows), denominator=episode_count, source_artifact=source_m3139)
    _metric(rows, "known_failures", "residual_collision_blocker_count", sum(1 for row in residual_rows if str(row.get("blocker_family", "")) == "collision"), source_artifact=source_m3139)
    _metric(rows, "known_failures", "residual_offtrack_blocker_count", sum(1 for row in residual_rows if str(row.get("blocker_family", "")) == "offtrack"), source_artifact=source_m3139)
    _metric(rows, "negative_replay", "m3153_comparison_count", m3153.get("counterfactual_replay_comparison_row_count", ""), source_artifact=source_m3153)
    _metric(rows, "negative_replay", "m3153_action_channel_sensitive_count", m3153.get("action_channel_sensitive_comparison_count", ""), source_artifact=source_m3153)
    return rows


def known_failure_taxonomy_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    comparisons_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source.get("m3153_comparison_rows", []):
        comparisons_by_source[str(row.get("source_measurement_episode_id", ""))].append(row)
    rows: list[dict[str, Any]] = []
    for index, blocker in enumerate(source.get("m3139_residual_blocker_rows", []), start=1):
        comparisons = comparisons_by_source.get(str(blocker.get("source_measurement_episode_id", "")), [])
        labels = Counter(str(row.get("counterfactual_diagnostic_label", "")) for row in comparisons)
        sensitive_count = sum(1 for row in comparisons if _bool(row.get("action_channel_sensitive_diagnostic", False)))
        dominant = labels.most_common(1)[0][0] if labels else ""
        rows.append(
            {
                "failure_taxonomy_row_id": f"m3156-known-failure-taxonomy-{index:04d}",
                "source_blocker_id": blocker.get("blocker_id", ""),
                "source_measurement_episode_id": blocker.get("source_measurement_episode_id", ""),
                "fresh_panel_row_id": blocker.get("fresh_panel_row_id", ""),
                "axis_id": blocker.get("axis_id", ""),
                "binding_role": blocker.get("binding_role", ""),
                "task_family": blocker.get("task_family", ""),
                "eval_seed": blocker.get("eval_seed", ""),
                "blocker_family": blocker.get("blocker_family", ""),
                "collision": _bool(blocker.get("collision", False)),
                "offtrack": _bool(blocker.get("offtrack", False)),
                "speed_too_low": _bool(blocker.get("speed_too_low", False)),
                "termination_reason": blocker.get("termination_reason", ""),
                "outcome_bucket": blocker.get("outcome_bucket", ""),
                "min_clearance_margin": blocker.get("min_clearance_margin", ""),
                "high_sideslip_fraction": blocker.get("high_sideslip_fraction", ""),
                "lateral_rmse": blocker.get("lateral_rmse", ""),
                "return": blocker.get("return", ""),
                "speed_mean": blocker.get("speed_mean", ""),
                "m3153_comparison_count": len(comparisons),
                "m3153_action_channel_sensitive_count": sensitive_count,
                "m3153_dominant_counterfactual_label": dominant,
                "m3153_terminal_invariant": bool(comparisons and sensitive_count == 0),
                "known_failure_status": "known_residual_blocker_preserved_for_route_a_pack",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def guard(guard_id: str, family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3156-{guard_id}",
        "guard_family": family,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "claim_boundary": CLAIM_SCOPE,
    }


def contract_guard_rows(contract_snapshot: Mapping[str, Any], source: Mapping[str, Any]) -> list[dict[str, Any]]:
    contract = contract_snapshot.get("driver_contract", {})
    residual_rows = source.get("m3139_residual_blocker_rows", [])
    return [
        guard("observation_shape", "contract", contract.get("observation_shape"), P0_OBSERVATION_DIM),
        guard("action_shape", "contract", contract.get("action_shape"), ACTION_DIM),
        guard("action_components", "contract", "|".join(contract.get("action_components", [])), "steer|throttle|brake"),
        guard("output_semantics", "contract", contract.get("output_semantics"), "direct_action_clipped"),
        guard("runtime_base_policy_required", "contract", contract.get("runtime_base_policy_required"), False),
        guard("checkpoint_model_required", "contract", contract.get("checkpoint_model_required"), False),
        guard("recurrent_hidden_state_required", "contract", contract.get("recurrent_hidden_state_required"), False),
        guard("sample_action_finite", "runtime_api", contract_snapshot.get("sample_action_finite"), True),
        guard("sample_action_bounded", "runtime_api", contract_snapshot.get("sample_action_bounded"), True),
        guard("m3139_status_pass", "lineage", _bool(source.get("m3139_summary", {}).get("status_pass", False)), True),
        guard("m3105_status_pass", "lineage", _bool(source.get("m3105_summary", {}).get("status_pass", False)), True),
        guard("m3153_status_pass", "lineage", _bool(source.get("m3153_summary", {}).get("status_pass", False)), True),
        guard("residual_blocker_count", "known_failures", len(residual_rows), EXPECTED_RESIDUAL_BLOCKERS),
    ]


def build_pack_manifest(
    *,
    output_dir: Path,
    contract_snapshot: Mapping[str, Any],
    metric_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "pack_id": "m3156-route-a-deployable-benchmark-pack",
        "created_at_utc": utc_timestamp(),
        "driver_id": contract_snapshot.get("driver_contract", {}).get("driver_id", ""),
        "incumbent_policy_id": contract_snapshot.get("driver_contract", {}).get("incumbent_policy_id", ""),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "action_components": ["steer", "throttle", "brake"],
        "artifact_paths": {
            "contract_snapshot": str(output_dir / "deployable_driver_contract_snapshot.json"),
            "benchmark_metric_rows": str(output_dir / "benchmark_metric_rows.csv"),
            "known_failure_taxonomy_rows": str(output_dir / "known_failure_taxonomy_rows.csv"),
        },
        "benchmark_metric_row_count": len(metric_rows),
        "known_failure_taxonomy_row_count": len(failure_rows),
        "known_failure_counts": dict(sorted(Counter(str(row.get("blocker_family", "")) for row in failure_rows).items())),
        "validation_run": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("deployable_driver_contract_snapshot", "contract", True, "deployable_driver_contract_snapshot.json"),
        ("benchmark_metric_rows", "benchmark_pack", True, "benchmark_metric_rows.csv"),
        ("known_failure_taxonomy_rows", "benchmark_pack", True, "known_failure_taxonomy_rows.csv"),
        ("deployable_benchmark_pack_manifest", "benchmark_pack", True, "deployable_benchmark_pack_manifest.json"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3157 audit manifest"),
    ]
    blocked = [
        ("new_environment_execution", "execution", "future pre-registered measurement route"),
        ("repair_implementation", "repair", "future audited repair synthesis route"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair measurement audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("feasibility_proof", "proof", "future feasibility proof route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
    ]
    rows = [
        {
            "claim_id": f"m3156-{claim_id}",
            "claim_family": family,
            "allowed_in_m3156": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3156-{claim_id}",
            "claim_family": family,
            "allowed_in_m3156": False,
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
        "priority": 31570,
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
        "hypothesis": "A bounded result audit can accept or reject the M3156 Route A deployable benchmark pack artifacts before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "deployable_driver_contract_snapshot.json"),
                str(output_dir / "deployable_benchmark_pack_manifest.json"),
                str(output_dir / "benchmark_metric_rows.csv"),
                str(output_dir / "known_failure_taxonomy_rows.csv"),
                str(output_dir / "contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit Route A deployable benchmark pack materialization"],
            "derived_from": [MILESTONE_ID, M3155_ID, M3153_ID, M3139_ID, M3105_ID],
            "blocked_by": [
                "M3156 benchmark pack requires audit before any external use",
                "packaged metrics are not validation, repair-success, or performance verdict evidence",
            ],
            "supersedes": ["direct use of unpackaged M3105/M3139/M3153 artifacts without Route A audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3157 must audit M3156 contract metrics known-failure taxonomy gates and claim boundaries",
            "M3157 must preserve obs72/action3 direct [steer throttle brake] contract and residual blocker disclosure",
            "M3157 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3157 must select exactly one next route: artifact repair, benchmark-pack acceptance, validation prep, or stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun expand tune rank promote validate or mutate checkpoints",
            "do not convert M3156 benchmark pack rows into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_route_a_deployable_benchmark_pack",
            "evidence_axis": "route_a_deployable_benchmark_pack_result_audit",
            "evidence_increment": "audits the deployable benchmark pack and known-failure taxonomy materialized by M3156",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3156 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize if M3157 cannot select artifact repair benchmark acceptance validation prep or stop",
            ],
            "fallback_plan": [
                "route to M3156 artifact repair if packaging is incomplete",
                "accept benchmark pack if M3156 is complete and claim-safe",
                "route to validation prep only after pack audit accepts residual blocker disclosure",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3156 completes Route A deployable benchmark pack materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3156 Route A deployable benchmark pack artifacts",
            "admission_evidence": ["M3156 summary contract metric failure taxonomy claim and gate artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3157 status queue scoreboard research log and review",
                "one follow-up manifest only if M3157 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3157 accepts or rejects M3156 as complete and claim-safe",
                "M3157 selects artifact repair benchmark-pack acceptance validation prep or stop explicitly",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3157 audits engineering benchmark-pack artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3157; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3156 Route A benchmark pack artifacts only.",
            "negative_result_policy": "Preserve residual blocker evidence and route to engineering verification rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3156 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "low",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits Route A deployable benchmark pack materialization rather than another residual repair loop",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3157 audits engineering verification packaging",
            "must_synthesize_if": [
                "M3157 cannot accept M3156 as complete and claim-safe",
                "M3157 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result feasibility-proof or self-ID evidence",
                "M3157 cannot select artifact repair benchmark acceptance validation prep or stop",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3157 audits M3156 contract metrics known-failure taxonomy gates and claim boundaries",
            "M3157 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3157 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3157 hides M3156 missing rows or missing artifacts",
            "M3157 treats M3156 benchmark pack as validation repair-success or performance verdict",
            "M3157 changes actor input or action contract",
            "M3157 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3157 audits M3156 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_route_a_deployable_benchmark_pack_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3156-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _all_forbidden_flags_clear(rows: list[dict[str, Any]]) -> bool:
    return not any(
        _bool(row.get(key, False))
        for row in rows
        for key in (
            "validation_run",
            "driver_performance_claim_made",
            "repair_success_claim_made",
            "hidden_oracle_actor_input_required",
            "ttc_actor_input_required",
        )
    )


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    contract_snapshot: Mapping[str, Any],
    metric_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    text = str(source.get("m3155_synthesis_text", ""))
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in failure_rows)
    combined = metric_rows + failure_rows + claim_rows
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3155_pivots_to_m3156", "lineage", "pivot_to_m3156_route_a_deployable_benchmark_pack_materialization" in text, "pivot marker", "present", "lineage_invalid"),
        gate("m3139_status_pass", "lineage", _bool(source["m3139_summary"].get("status_pass", False)), source["m3139_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3139_gate_matrix_pass", "lineage", _bool(source["m3139_summary"].get("gate_matrix_pass", False)), source["m3139_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3105_status_pass", "lineage", _bool(source["m3105_summary"].get("status_pass", False)), source["m3105_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3105_gate_matrix_pass", "lineage", _bool(source["m3105_summary"].get("gate_matrix_pass", False)), source["m3105_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3153_status_pass", "lineage", _bool(source["m3153_summary"].get("status_pass", False)), source["m3153_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3153_gate_matrix_pass", "lineage", _bool(source["m3153_summary"].get("gate_matrix_pass", False)), source["m3153_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("contract_snapshot_shape", "contract", contract_snapshot.get("observation_shape") == P0_OBSERVATION_DIM and contract_snapshot.get("action_shape") == ACTION_DIM, (contract_snapshot.get("observation_shape"), contract_snapshot.get("action_shape")), (P0_OBSERVATION_DIM, ACTION_DIM), "contract_violation"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass", False)) for row in guard_rows), "all", "pass", "contract_violation"),
        gate("measurement_episode_rows", "benchmark", int(source["m3105_summary"].get("measurement_episode_row_count", 0)) == EXPECTED_MEASUREMENT_ROWS, source["m3105_summary"].get("measurement_episode_row_count"), EXPECTED_MEASUREMENT_ROWS, "metric_artifact"),
        gate("measurement_success_count", "benchmark", int(source["m3105_summary"].get("measurement_success_count", 0)) == EXPECTED_SUCCESS_ROWS, source["m3105_summary"].get("measurement_success_count"), EXPECTED_SUCCESS_ROWS, "metric_artifact"),
        gate("measurement_collision_count", "known_failures", int(source["m3105_summary"].get("measurement_collision_count", 0)) == EXPECTED_COLLISION_ROWS, source["m3105_summary"].get("measurement_collision_count"), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("measurement_offtrack_count", "known_failures", int(source["m3105_summary"].get("measurement_offtrack_count", 0)) == EXPECTED_OFFTRACK_ROWS, source["m3105_summary"].get("measurement_offtrack_count"), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("measurement_speed_too_low_count", "known_failures", int(source["m3105_summary"].get("measurement_speed_too_low_count", 0)) == EXPECTED_SPEED_TOO_LOW_ROWS, source["m3105_summary"].get("measurement_speed_too_low_count"), EXPECTED_SPEED_TOO_LOW_ROWS, "metric_artifact"),
        gate("residual_blocker_rows", "known_failures", len(failure_rows) == EXPECTED_RESIDUAL_BLOCKERS, len(failure_rows), EXPECTED_RESIDUAL_BLOCKERS, "metric_artifact"),
        gate("residual_collision_blockers", "known_failures", blocker_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("residual_offtrack_blockers", "known_failures", blocker_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("m3153_negative_comparison_count", "negative_replay", int(source["m3153_summary"].get("counterfactual_replay_comparison_row_count", 0)) == EXPECTED_M3153_COMPARISONS, source["m3153_summary"].get("counterfactual_replay_comparison_row_count"), EXPECTED_M3153_COMPARISONS, "metric_artifact"),
        gate("m3153_action_channel_sensitive_zero", "negative_replay", int(source["m3153_summary"].get("action_channel_sensitive_comparison_count", -1)) == 0, source["m3153_summary"].get("action_channel_sensitive_comparison_count"), 0, "metric_artifact"),
        gate("benchmark_metric_rows_nonempty", "benchmark", len(metric_rows) >= 12, len(metric_rows), ">=12", "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("forbidden_flags_clear", "claim", _all_forbidden_flags_clear(combined), "forbidden claim flags", "clear", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3156 Route A Deployable Benchmark Pack Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- benchmark metric rows: {summary['benchmark_metric_row_count']}",
            f"- known failure taxonomy rows: {summary['known_failure_taxonomy_row_count']}",
            f"- M3105 success/collision/offtrack/speed-too-low: {summary['m3105_success_count']}/{summary['m3105_collision_count']}/{summary['m3105_offtrack_count']}/{summary['m3105_speed_too_low_count']}",
            f"- M3153 action-channel-sensitive comparisons: {summary['m3153_action_channel_sensitive_comparison_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3156 packages the current M3105/M3103 deployable active-safety reflex baseline into a Route A benchmark pack. It preserves the public obs72-to-action3 runtime contract, M3105 denominator metrics, seven known residual blockers, and the negative M3153 fixed-variant replay diagnostics. It does not run a new environment, tune a policy, rank a driver, promote a checkpoint, or claim validation, repair success, robustness, driver performance, current-sim verdict, high-fidelity, paper, full-driver, feasibility-proof, or self-ID evidence.",
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


def run_benchmark_pack_materialization_preflight(
    *,
    m3155_synthesis: Path,
    m3139_dir: Path,
    m3105_dir: Path,
    m3153_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3155_synthesis=m3155_synthesis, m3139_dir=m3139_dir, m3105_dir=m3105_dir, m3153_dir=m3153_dir)
    contract_snapshot = deployable_driver_contract_snapshot(source)
    metric_rows = benchmark_metric_rows(source)
    failure_rows = known_failure_taxonomy_rows(source)
    guard_rows = contract_guard_rows(contract_snapshot, source)
    pack_manifest = build_pack_manifest(output_dir=output_dir, contract_snapshot=contract_snapshot, metric_rows=metric_rows, failure_rows=failure_rows)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_json(paths["deployable_driver_contract_snapshot"], contract_snapshot)
    write_json(paths["deployable_benchmark_pack_manifest"], pack_manifest)
    for path, rows, fieldnames in (
        (paths["benchmark_metric_rows"], metric_rows, BENCHMARK_FIELDNAMES),
        (paths["known_failure_taxonomy_rows"], failure_rows, FAILURE_TAXONOMY_FIELDNAMES),
        (paths["contract_guard_rows"], guard_rows, CONTRACT_GUARD_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        contract_snapshot=contract_snapshot,
        metric_rows=metric_rows,
        failure_rows=failure_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    m3105_summary = source["m3105_summary"]
    m3153_summary = source["m3153_summary"]
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_route_a_deployable_benchmark_pack_materialization_pass"
            if status_pass
            else "active_safety_driver_route_a_deployable_benchmark_pack_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "driver_id": contract_snapshot.get("driver_contract", {}).get("driver_id", ""),
        "incumbent_policy_id": contract_snapshot.get("driver_contract", {}).get("incumbent_policy_id", ""),
        "benchmark_metric_row_count": len(metric_rows),
        "known_failure_taxonomy_row_count": len(failure_rows),
        "contract_guard_row_count": len(guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3105_measurement_episode_row_count": int(m3105_summary.get("measurement_episode_row_count", 0)),
        "m3105_success_count": int(m3105_summary.get("measurement_success_count", 0)),
        "m3105_collision_count": int(m3105_summary.get("measurement_collision_count", 0)),
        "m3105_offtrack_count": int(m3105_summary.get("measurement_offtrack_count", 0)),
        "m3105_speed_too_low_count": int(m3105_summary.get("measurement_speed_too_low_count", 0)),
        "m3105_clearance_margin_mean": m3105_summary.get("measurement_clearance_margin_mean", ""),
        "m3105_high_sideslip_fraction_mean": m3105_summary.get("measurement_high_sideslip_fraction_mean", ""),
        "m3153_comparison_count": int(m3153_summary.get("counterfactual_replay_comparison_row_count", 0)),
        "m3153_action_channel_sensitive_comparison_count": int(m3153_summary.get("action_channel_sensitive_comparison_count", 0)),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
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
        "decision": "active_safety_driver_route_a_deployable_benchmark_pack_materialization_route_to_m3157_result_audit",
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
            "benchmark_metric_row_count": len(metric_rows),
            "known_failure_taxonomy_row_count": len(failure_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3155-synthesis", type=Path, default=DEFAULT_M3155_SYNTHESIS)
    parser.add_argument("--m3139-dir", type=Path, default=DEFAULT_M3139_DIR)
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3153-dir", type=Path, default=DEFAULT_M3153_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_benchmark_pack_materialization_preflight(
        m3155_synthesis=args.m3155_synthesis,
        m3139_dir=args.m3139_dir,
        m3105_dir=args.m3105_dir,
        m3153_dir=args.m3153_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"benchmark_metric_rows={summary['benchmark_metric_row_count']}")
    print(f"known_failure_taxonomy_rows={summary['known_failure_taxonomy_row_count']}")
    print(f"m3105_success_collision_offtrack_speed_too_low={summary['m3105_success_count']}/{summary['m3105_collision_count']}/{summary['m3105_offtrack_count']}/{summary['m3105_speed_too_low_count']}")
    print(f"m3153_action_channel_sensitive_comparisons={summary['m3153_action_channel_sensitive_comparison_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
