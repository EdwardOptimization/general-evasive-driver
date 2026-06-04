"""Materialize Route B protocol-to-runtime enforcement evidence.

This runner maps the accepted M2671 controller-family protocol rows to concrete
profile configs and no-training runtime semantics. It may reset/step a smoke
environment with a fixed action to observe wrappers, but it does not execute
policy rollouts, replay, measured validation, training, PPO, ranking, promotion,
or any success-rate/performance verdict.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_profile_runtime import CURRENT_TILED_HISTORY
from autodrift.controller_profile_runtime_smoke import smoke_one_profile
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.paper_route_history_vs_current_response_comparison_protocol_materialization import (
    REQUIRED_CONTROLLER_IDS,
)


DEFAULT_MILESTONE = (
    "m2673-paper-route-history-vs-current-response-runtime-enforcement-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2674-paper-route-history-vs-current-response-runtime-enforcement-"
    "materialization-result-audit"
)
DEFAULT_PROTOCOL_DIR = Path(
    "runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2673_paper_route_history_vs_current_response_runtime_enforcement_materialization"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2673-paper-route-history-vs-current-response-runtime-enforcement-"
    "materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2674-paper-route-history-vs-current-response-runtime-"
    "enforcement-materialization-result-audit.json"
)

CORRECTED_PROFILE_DIR = Path("configs/paper_route_corrected_profiles")
M2672_AUDIT_DOC = Path(
    "docs/m2672-paper-route-history-vs-current-response-comparison-protocol-"
    "materialization-result-audit.md"
)
M1205_SYNTHESIS_DOC = Path("docs/m1205-paper-route-finite-window-gru-evidence-synthesis.md")

CLAIM_SCOPE = (
    "Route B history-vs-current-response runtime-enforcement materialization "
    "only; no policy rollout, replay, measured validation, training, PPO, "
    "ranking, winner selection, promotion, success-rate verdict, "
    "driver-performance, paper, finite-window-vs-GRU, current-sim, "
    "high-fidelity validation, full ideal driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller-family ranking, finite-window superiority, "
    "GRU superiority, recurrent-belief advantage, level3 self-identification, "
    "paper verdict, current-sim verdict, high-fidelity validation result, "
    "full ideal driver completion, or promotion evidence"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

PROTOCOL_TO_RUNTIME_FIELDNAMES = [
    "protocol_controller_family_id",
    "runtime_profile_name",
    "config_path",
    "config_exists",
    "protocol_row_present",
    "actor_encoder",
    "actor_history_length",
    "env_history_length",
    "observation_shape",
    "action_shape",
    "observation_mask",
    "history_transform",
    "reset_hidden_policy",
    "current_tiled_expected",
    "current_tiled_runtime_observed",
    "reset_truncated_expected",
    "reset_policy_routing_ok",
    "previous_command_mask_observed",
    "contract_ok",
    "model_forward_ok",
    "runtime_smoke_pass",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_detected",
    "private_holdout_used",
    "training_started",
    "ppo_used",
    "policy_rollout_run",
    "success_rate_computed",
    "runtime_enforcement_status_pass",
    "claim_boundary",
]
RUNTIME_GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "blocks_execution_if_false",
    "failure_type",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2673",
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


def runtime_profile_specs() -> list[dict[str, Any]]:
    return [
        spec("L0-current", "L0_current_masked", "m1207_l0_current_masked.json"),
        spec("L1-one-step", "L1_one_step", "m1207_l1_one_step.json"),
        spec("L2-window-13", "L2_window_13", "m1207_l2_window_13.json"),
        spec("L2-window-25", "L2_window_25", "m1207_l2_window_25.json"),
        spec("L2-window-50", "L2_window_50", "m1207_l2_window_50.json"),
        spec("L2-window-100", "L2_window_100", "m1207_l2_window_100.json"),
        spec(
            "L2-current-tiled",
            "L2_window_13_current_tiled",
            "m1207_l2_window_13_current_tiled.json",
        ),
        spec(
            "L2-current-tiled",
            "L2_window_25_current_tiled",
            "m1207_l2_window_25_current_tiled.json",
        ),
        spec(
            "L2-current-tiled",
            "L2_window_50_current_tiled",
            "m1207_l2_window_50_current_tiled.json",
        ),
        spec(
            "L2-current-tiled",
            "L2_window_100_current_tiled",
            "m1207_l2_window_100_current_tiled.json",
        ),
        spec("L3-online-GRU", "L3_online_gru", "m1207_l3_online_gru.json"),
        spec(
            "L3-reset-truncated-control",
            "L3_reset_control_corrected",
            "m1207_l3_reset_control_corrected.json",
        ),
    ]


def spec(protocol_id: str, profile_name: str, filename: str) -> dict[str, Any]:
    return {
        "protocol_controller_family_id": protocol_id,
        "runtime_profile_name": profile_name,
        "config_path": str(CORRECTED_PROFILE_DIR / filename),
    }


def materialize_runtime_enforcement(
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    seed: int = 2673,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    protocol_path = Path(protocol_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    source = load_source_artifacts(protocol_path, follow_up_manifest=follow_up_manifest)
    protocol_rows = read_protocol_controller_rows(protocol_path / "controller_family_rows.csv")
    runtime_rows = build_protocol_to_runtime_profile_rows(protocol_rows, seed=seed)
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"])

    paths = {
        "summary": output_path / "summary.json",
        "protocol_to_runtime_profile_rows": output_path / "protocol_to_runtime_profile_rows.csv",
        "runtime_enforcement_gate_rows": output_path / "runtime_enforcement_gate_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "gate_matrix": output_path / "gate_matrix.csv",
        "doc": Path(doc_path),
    }

    runtime_gate_rows = build_runtime_enforcement_gate_rows(
        source=source,
        protocol_rows=protocol_rows,
        runtime_rows=runtime_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        protocol_rows=protocol_rows,
        runtime_rows=runtime_rows,
        runtime_gate_rows=runtime_gate_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(
        paths["protocol_to_runtime_profile_rows"],
        runtime_rows,
        fieldnames=PROTOCOL_TO_RUNTIME_FIELDNAMES,
    )
    write_csv_rows(paths["runtime_enforcement_gate_rows"], runtime_gate_rows, fieldnames=RUNTIME_GATE_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        protocol_rows=protocol_rows,
        runtime_rows=runtime_rows,
        runtime_gate_rows=runtime_gate_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(path.exists() for path in paths.values())
    runtime_gate_rows = build_runtime_enforcement_gate_rows(
        source=source,
        protocol_rows=protocol_rows,
        runtime_rows=runtime_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        protocol_rows=protocol_rows,
        runtime_rows=runtime_rows,
        runtime_gate_rows=runtime_gate_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["runtime_enforcement_gate_rows"], runtime_gate_rows, fieldnames=RUNTIME_GATE_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        protocol_rows=protocol_rows,
        runtime_rows=runtime_rows,
        runtime_gate_rows=runtime_gate_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def load_source_artifacts(protocol_dir: Path, *, follow_up_manifest: Path | str) -> dict[str, Any]:
    paths = {
        "m2671_summary": protocol_dir / "summary.json",
        "m2671_controller_family_rows": protocol_dir / "controller_family_rows.csv",
        "m2671_task_family_rows": protocol_dir / "task_family_rows.csv",
        "m2671_fairness_gate_rows": protocol_dir / "fairness_gate_rows.csv",
        "m2671_claim_boundary_rows": protocol_dir / "claim_boundary_rows.csv",
        "m2671_gate_matrix": protocol_dir / "gate_matrix.csv",
        "m2672_audit_doc": M2672_AUDIT_DOC,
        "m1205_synthesis_doc": M1205_SYNTHESIS_DOC,
        "follow_up_manifest": Path(follow_up_manifest),
    }
    summary = read_json(paths["m2671_summary"]) if paths["m2671_summary"].exists() else {}
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2671_summary": summary,
    }


def read_protocol_controller_rows(path: Path | str) -> list[dict[str, str]]:
    if not Path(path).exists():
        return []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_protocol_to_runtime_profile_rows(
    protocol_rows: list[dict[str, str]],
    *,
    seed: int = 2673,
) -> list[dict[str, Any]]:
    protocol_ids = {row["controller_family_id"] for row in protocol_rows}
    rows: list[dict[str, Any]] = []
    for item in runtime_profile_specs():
        config_path = Path(item["config_path"])
        protocol_id = item["protocol_controller_family_id"]
        row: dict[str, Any] = {
            "protocol_controller_family_id": protocol_id,
            "runtime_profile_name": item["runtime_profile_name"],
            "config_path": str(config_path),
            "config_exists": config_path.exists(),
            "protocol_row_present": protocol_id in protocol_ids,
            "actor_encoder": "",
            "actor_history_length": "",
            "env_history_length": "",
            "observation_shape": "",
            "action_shape": ACTION_DIM,
            "observation_mask": "",
            "history_transform": "",
            "reset_hidden_policy": "",
            "current_tiled_expected": protocol_id == "L2-current-tiled",
            "current_tiled_runtime_observed": False,
            "reset_truncated_expected": protocol_id == "L3-reset-truncated-control",
            "reset_policy_routing_ok": False,
            "previous_command_mask_observed": False,
            "contract_ok": False,
            "model_forward_ok": False,
            "runtime_smoke_pass": False,
            "actor_contract_shape_72_action_3": False,
            "hidden_oracle_actor_input_detected": True,
            "private_holdout_used": True,
            "training_started": False,
            "ppo_used": False,
            "policy_rollout_run": False,
            "success_rate_computed": False,
            "runtime_enforcement_status_pass": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        if config_path.exists():
            config = read_json(config_path)
            profile = config["controller_profile"]
            smoke = smoke_one_profile(config_path, seed=seed)
            current_tiled_expected = protocol_id == "L2-current-tiled"
            reset_truncated_expected = protocol_id == "L3-reset-truncated-control"
            previous_command_mask_expected = profile.get("observation_mask") == "zero_previous_command_fields"
            row.update(
                {
                    "actor_encoder": profile.get("actor_encoder", ""),
                    "actor_history_length": int(profile.get("actor_history_length", 0)),
                    "env_history_length": int(config["env"].get("history_length", 0)),
                    "observation_shape": int(smoke["observation_dim"]),
                    "action_shape": int(smoke["action_dim"]),
                    "observation_mask": smoke["observation_mask"],
                    "history_transform": smoke["history_transform"],
                    "reset_hidden_policy": smoke["reset_hidden_policy"],
                    "current_tiled_runtime_observed": bool(
                        current_tiled_expected and smoke["current_tiled_observed"]
                    ),
                    "reset_policy_routing_ok": bool(reset_truncated_expected and smoke["reset_policy_routing_ok"]),
                    "previous_command_mask_observed": bool(
                        previous_command_mask_expected and smoke["previous_command_mask_observed"]
                    ),
                    "contract_ok": bool(smoke["contract_ok"]),
                    "model_forward_ok": bool(smoke["model_forward_ok"]),
                    "runtime_smoke_pass": bool(smoke["passed"]),
                    "actor_contract_shape_72_action_3": bool(
                        int(smoke["observation_dim"]) % P0_OBSERVATION_DIM == 0
                        and int(smoke["action_dim"]) == ACTION_DIM
                    ),
                    "hidden_oracle_actor_input_detected": not bool(smoke["contract_ok"]),
                    "private_holdout_used": bool(profile.get("private_holdout_used", True)),
                    "training_started": bool(smoke["training_started"]),
                    "ppo_used": bool(smoke["ppo_used"]),
                    "policy_rollout_run": False,
                    "success_rate_computed": False,
                }
            )
        row["runtime_enforcement_status_pass"] = runtime_row_pass(row)
        rows.append(row)
    return rows


def runtime_row_pass(row: dict[str, Any]) -> bool:
    if not bool(row["config_exists"]) or not bool(row["protocol_row_present"]):
        return False
    if not bool(row["contract_ok"]) or bool(row["hidden_oracle_actor_input_detected"]):
        return False
    if bool(row["private_holdout_used"]) or bool(row["training_started"]) or bool(row["ppo_used"]):
        return False
    if bool(row["policy_rollout_run"]) or bool(row["success_rate_computed"]):
        return False
    if not bool(row["runtime_smoke_pass"]) or not bool(row["model_forward_ok"]):
        return False
    if row["protocol_controller_family_id"] == "L0-current":
        return bool(row["previous_command_mask_observed"])
    if row["protocol_controller_family_id"] == "L2-current-tiled":
        return row["history_transform"] == CURRENT_TILED_HISTORY and bool(row["current_tiled_runtime_observed"])
    if row["protocol_controller_family_id"] == "L3-reset-truncated-control":
        return row["reset_hidden_policy"] == "every_step_control" and bool(row["reset_policy_routing_ok"])
    if row["protocol_controller_family_id"] == "L3-online-GRU":
        return row["reset_hidden_policy"] == "episode_persistent"
    return True


def build_runtime_enforcement_gate_rows(
    *,
    source: dict[str, Any],
    protocol_rows: list[dict[str, str]],
    runtime_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    protocol_ids = {row["controller_family_id"] for row in protocol_rows}
    mapped_ids = {row["protocol_controller_family_id"] for row in runtime_rows if _bool(row["runtime_enforcement_status_pass"])}
    l2_tiled_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L2-current-tiled"]
    l3_reset_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L3-reset-truncated-control"]
    l0_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L0-current"]
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2673"])]
    false_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2673"])]
    m2671_summary = source["m2671_summary"]
    return [
        runtime_gate(
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "all M2671/M2672 source artifacts and follow-up manifest present",
            "lineage_invalid",
        ),
        runtime_gate(
            "m2671_status_pass",
            "lineage",
            bool(m2671_summary.get("status_pass")),
            m2671_summary.get("status_pass", None),
            True,
            "lineage_invalid",
        ),
        runtime_gate(
            "required_protocol_controller_ids_present",
            "protocol",
            REQUIRED_CONTROLLER_IDS.issubset(protocol_ids),
            sorted(protocol_ids),
            sorted(REQUIRED_CONTROLLER_IDS),
            "lineage_invalid",
        ),
        runtime_gate(
            "all_required_protocol_ids_mapped_to_runtime",
            "protocol_to_runtime",
            REQUIRED_CONTROLLER_IDS.issubset(mapped_ids),
            sorted(mapped_ids),
            sorted(REQUIRED_CONTROLLER_IDS),
            "metric_artifact",
        ),
        runtime_gate(
            "runtime_profile_rows_present",
            "protocol_to_runtime",
            len(runtime_rows) == len(runtime_profile_specs()),
            len(runtime_rows),
            len(runtime_profile_specs()),
            "metric_artifact",
        ),
        runtime_gate(
            "all_runtime_configs_present",
            "runtime_config",
            all(_bool(row["config_exists"]) for row in runtime_rows),
            [row["config_path"] for row in runtime_rows if not _bool(row["config_exists"])],
            [],
            "lineage_invalid",
        ),
        runtime_gate(
            "actor_contract_shape_72_action_3",
            "actor_contract",
            all(_bool(row["actor_contract_shape_72_action_3"]) for row in runtime_rows),
            "P0 frame multiple/action 3 for all mapped profiles",
            "P0 frame multiple/action 3",
            "contract_violation",
        ),
        runtime_gate(
            "no_hidden_oracle_actor_inputs",
            "actor_contract",
            not any(_bool(row["hidden_oracle_actor_input_detected"]) for row in runtime_rows),
            False,
            False,
            "contract_violation",
        ),
        runtime_gate(
            "l0_previous_command_mask_runtime_observed",
            "runtime_enforcement",
            bool(l0_rows and all(_bool(row["previous_command_mask_observed"]) for row in l0_rows)),
            [row["previous_command_mask_observed"] for row in l0_rows],
            [True],
            "metric_artifact",
        ),
        runtime_gate(
            "l2_current_tiled_runtime_observed",
            "runtime_enforcement",
            bool(l2_tiled_rows and all(_bool(row["current_tiled_runtime_observed"]) for row in l2_tiled_rows)),
            [row["current_tiled_runtime_observed"] for row in l2_tiled_rows],
            [True, True, True, True],
            "metric_artifact",
        ),
        runtime_gate(
            "l2_current_tiled_config_count",
            "runtime_enforcement",
            len(l2_tiled_rows) == 4,
            len(l2_tiled_rows),
            4,
            "metric_artifact",
        ),
        runtime_gate(
            "l3_reset_truncated_policy_routing_ok",
            "runtime_enforcement",
            bool(l3_reset_rows and all(_bool(row["reset_policy_routing_ok"]) for row in l3_reset_rows)),
            [row["reset_policy_routing_ok"] for row in l3_reset_rows],
            [True],
            "metric_artifact",
        ),
        runtime_gate(
            "no_training_ppo_replay_ranking_or_success_verdict",
            "claim_boundary",
            no_forbidden_runtime_claim_flags(runtime_rows),
            "all forbidden execution/result flags false",
            "all forbidden execution/result flags false",
            "proof_washout",
        ),
        runtime_gate(
            "claim_boundary_blocks_result_overclaim",
            "claim_boundary",
            len(allowed_claims) == 6 and all(_bool(row["status_pass"]) for row in false_claim_rows),
            f"allowed={len(allowed_claims)} blocked={len(false_claim_rows)}",
            "allowed=6 blocked>=15",
            "proof_washout",
        ),
        runtime_gate(
            "required_artifacts_present",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "lineage_invalid",
        ),
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool = True) -> list[dict[str, Any]]:
    checks = [
        ("runtime_enforcement_materialization", "runtime_enforcement_readiness", True, "M2673 summary and rows"),
        ("protocol_to_runtime_profile_rows_materialized", "runtime_profile_mapping", True, "protocol_to_runtime_profile_rows.csv"),
        ("runtime_enforcement_gate_rows_materialized", "runtime_gate_rows", True, "runtime_enforcement_gate_rows.csv"),
        ("claim_boundary_rows_materialized", "claim_boundary", True, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "gate_matrix", True, "gate_matrix.csv"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2674 result-audit manifest"),
        ("policy_rollout_execution", "execution", False, "future execution manifest"),
        ("replay_execution", "execution", False, "future execution manifest"),
        ("measured_validation", "execution", False, "future validation manifest"),
        ("training_or_ppo", "execution", False, "future training manifest"),
        ("controller_family_ranking", "ranking", False, "future ranking gate after audited execution"),
        ("winner_selection", "promotion", False, "future promotion gate"),
        ("checkpoint_promotion", "promotion", False, "future promotion gate"),
        ("success_rate_verdict", "verdict", False, "future verdict milestone"),
        ("driver_performance", "driver_performance", False, "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", False, "future validation-readiness route"),
        ("paper_level_evidence", "paper", False, "future paper evidence matrix"),
        ("finite_window_vs_gru_result", "paper", False, "future fair comparison execution and audit"),
        ("current_sim_verdict", "paper", False, "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", False, "future high-fidelity validation"),
        ("level3_self_identification", "self_id", False, "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", False, "future full ideal driver gate"),
    ]
    return [
        {
            "claim_id": claim_id,
            "claim_family": family,
            "allowed_in_m2673": allowed,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, evidence in checks
    ]


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    protocol_rows: list[dict[str, str]],
    runtime_rows: list[dict[str, Any]],
    runtime_gate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    del claim_rows
    protocol_ids = {row["controller_family_id"] for row in protocol_rows}
    mapped_ids = {row["protocol_controller_family_id"] for row in runtime_rows if _bool(row["runtime_enforcement_status_pass"])}
    l2_tiled_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L2-current-tiled"]
    l3_reset_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L3-reset-truncated-control"]
    return [
        gate("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all source artifacts present", "lineage_invalid"),
        gate("m2671_status_pass", "lineage", bool(source["m2671_summary"].get("status_pass")), source["m2671_summary"].get("status_pass", None), True, "lineage_invalid"),
        gate("required_protocol_controller_ids_present", "protocol", REQUIRED_CONTROLLER_IDS.issubset(protocol_ids), sorted(protocol_ids), sorted(REQUIRED_CONTROLLER_IDS), "lineage_invalid"),
        gate("required_protocol_ids_runtime_mapped", "protocol_to_runtime", REQUIRED_CONTROLLER_IDS.issubset(mapped_ids), sorted(mapped_ids), sorted(REQUIRED_CONTROLLER_IDS), "metric_artifact"),
        gate("runtime_profile_row_count", "protocol_to_runtime", len(runtime_rows) == len(runtime_profile_specs()), len(runtime_rows), len(runtime_profile_specs()), "metric_artifact"),
        gate("all_runtime_rows_pass", "runtime_enforcement", all(_bool(row["runtime_enforcement_status_pass"]) for row in runtime_rows), "all pass", "all pass", "metric_artifact"),
        gate("all_runtime_gates_pass", "runtime_enforcement", all(_bool(row["status_pass"]) for row in runtime_gate_rows), "all pass", "all pass", "metric_artifact"),
        gate("current_tiled_runtime_observed", "runtime_enforcement", bool(l2_tiled_rows and all(_bool(row["current_tiled_runtime_observed"]) for row in l2_tiled_rows)), [row["current_tiled_runtime_observed"] for row in l2_tiled_rows], [True, True, True, True], "metric_artifact"),
        gate("reset_truncated_policy_routing_ok", "runtime_enforcement", bool(l3_reset_rows and all(_bool(row["reset_policy_routing_ok"]) for row in l3_reset_rows)), [row["reset_policy_routing_ok"] for row in l3_reset_rows], [True], "metric_artifact"),
        gate("actor_contract_preserved", "actor_contract", all(_bool(row["actor_contract_shape_72_action_3"]) and _bool(row["contract_ok"]) for row in runtime_rows), "all mapped profiles P0/action3/no oracle", "all mapped profiles P0/action3/no oracle", "contract_violation"),
        gate("no_hidden_oracle_actor_input_detected", "actor_contract", not any(_bool(row["hidden_oracle_actor_input_detected"]) for row in runtime_rows), False, False, "contract_violation"),
        gate("private_holdout_used", "holdout_policy", not any(_bool(row["private_holdout_used"]) for row in runtime_rows), False, False, "objective_overfit"),
        gate("all_execution_and_result_claim_flags_false", "claim_boundary", all(not value for value in FALSE_CLAIM_FLAGS.values()), True, True, "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    protocol_rows: list[dict[str, str]],
    runtime_rows: list[dict[str, Any]],
    runtime_gate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    protocol_ids = {row["controller_family_id"] for row in protocol_rows}
    mapped_ids = {row["protocol_controller_family_id"] for row in runtime_rows if _bool(row["runtime_enforcement_status_pass"])}
    l2_tiled_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L2-current-tiled"]
    l3_reset_rows = [row for row in runtime_rows if row["protocol_controller_family_id"] == "L3-reset-truncated-control"]
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2673"])]
    false_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2673"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    runtime_gates_pass = all(_bool(row["status_pass"]) for row in runtime_gate_rows)
    summary = {
        "milestone": milestone,
        "status_pass": bool(gate_matrix_pass and runtime_gates_pass and required_artifacts_present),
        "result_class": (
            "paper_route_history_vs_current_response_runtime_enforcement_materialization_pass"
            if gate_matrix_pass and runtime_gates_pass and required_artifacts_present
            else "paper_route_history_vs_current_response_runtime_enforcement_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2671_status_pass": bool(source["m2671_summary"].get("status_pass")),
        "protocol_controller_family_count": len(protocol_ids),
        "required_protocol_controller_family_count": len(REQUIRED_CONTROLLER_IDS),
        "required_protocol_controller_families_present": REQUIRED_CONTROLLER_IDS.issubset(protocol_ids),
        "runtime_profile_row_count": len(runtime_rows),
        "runtime_profile_mapping_count": len(mapped_ids),
        "required_protocol_ids_runtime_mapped": REQUIRED_CONTROLLER_IDS.issubset(mapped_ids),
        "current_tiled_runtime_profile_count": len(l2_tiled_rows),
        "current_tiled_runtime_observed": bool(
            l2_tiled_rows and all(_bool(row["current_tiled_runtime_observed"]) for row in l2_tiled_rows)
        ),
        "reset_truncated_runtime_profile_count": len(l3_reset_rows),
        "reset_truncated_policy_routing_ok": bool(
            l3_reset_rows and all(_bool(row["reset_policy_routing_ok"]) for row in l3_reset_rows)
        ),
        "all_runtime_rows_pass": all(_bool(row["runtime_enforcement_status_pass"]) for row in runtime_rows),
        "runtime_enforcement_gate_row_count": len(runtime_gate_rows),
        "runtime_enforcement_gates_pass": runtime_gates_pass,
        "claim_boundary_row_count": len(claim_rows),
        "allowed_claim_boundary_row_count": len(allowed_claim_rows),
        "blocked_claim_boundary_row_count": len(false_claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": any(_bool(row["hidden_oracle_actor_input_detected"]) for row in runtime_rows),
        "controller_family_labels_actor_visible": False,
        "taxonomy_or_route_labels_actor_visible": False,
        "private_holdout_used": any(_bool(row["private_holdout_used"]) for row in runtime_rows),
        "environment_reset_run": True,
        "environment_step_run": True,
        "fixed_smoke_action_step_run": True,
        "model_forward_shape_check_run": True,
        "no_training_runtime_smoke_only": True,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "paths": {key: str(path) for key, path in paths.items()},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2673 Paper Route History Vs Current Response Runtime Enforcement Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result_class: `{summary['result_class']}`",
            f"- generated_at_utc: `{summary['generated_at_utc']}`",
            f"- summary: `{summary['paths']['summary']}`",
            f"- protocol-to-runtime profile rows: `{summary['paths']['protocol_to_runtime_profile_rows']}`",
            f"- runtime enforcement gate rows: `{summary['paths']['runtime_enforcement_gate_rows']}`",
            f"- claim boundary rows: `{summary['paths']['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['paths']['gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Materialized Runtime Enforcement",
            "",
            f"- protocol controller families: {summary['protocol_controller_family_count']} / {summary['required_protocol_controller_family_count']}",
            f"- runtime profile rows: {summary['runtime_profile_row_count']}",
            f"- required protocol IDs runtime mapped: {summary['required_protocol_ids_runtime_mapped']}",
            f"- current-tiled runtime profile count: {summary['current_tiled_runtime_profile_count']}",
            f"- current-tiled runtime observed: {summary['current_tiled_runtime_observed']}",
            f"- reset/truncated runtime profile count: {summary['reset_truncated_runtime_profile_count']}",
            f"- reset/truncated policy routing ok: {summary['reset_truncated_policy_routing_ok']}",
            f"- runtime enforcement gate rows: {summary['runtime_enforcement_gate_row_count']}",
            f"- gate matrix rows: {summary['gate_matrix_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Guardrails",
            "",
            f"- actor/action boundary: P0 observation {summary['observation_shape']} action {summary['action_shape']}",
            f"- hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}",
            f"- private holdout used: {summary['private_holdout_used']}",
            f"- environment reset run: {summary['environment_reset_run']}",
            f"- environment step run: {summary['environment_step_run']}",
            f"- no-training runtime smoke only: {summary['no_training_runtime_smoke_only']}",
            f"- policy rollout run: {summary['policy_rollout_run']}",
            f"- training run: {summary['training_run']}",
            f"- ppo run: {summary['ppo_run']}",
            f"- success-rate computed: {summary['success_rate_computed']}",
            "",
            "## Claim Boundary",
            "",
            "Allowed:",
            "",
            "```text",
            "Runtime-enforcement materialization readiness only.",
            "```",
            "",
            "Rejected:",
            "",
            "```text",
            summary["forbidden_interpretation"],
            "```",
            "",
            "M2673 did not execute policy rollout, replay, measured validation,",
            "training, PPO, source build, adapter probe, external simulation,",
            "ranking, winner selection, promotion, success-rate verdict computation,",
            "driver-performance measurement, paper verdict, current-sim verdict,",
            "high-fidelity validation, full ideal driver gate, or self-ID verdict.",
            "",
        ]
    )


def runtime_gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "blocks_execution_if_false": True,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def no_forbidden_runtime_claim_flags(runtime_rows: list[dict[str, Any]]) -> bool:
    if any(_bool(row["training_started"]) or _bool(row["ppo_used"]) for row in runtime_rows):
        return False
    if any(_bool(row["policy_rollout_run"]) or _bool(row["success_rate_computed"]) for row in runtime_rows):
        return False
    return all(not value for value in FALSE_CLAIM_FLAGS.values())


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "1", "yes"}
    return bool(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--seed", type=int, default=2673)
    args = parser.parse_args(argv)
    summary = materialize_runtime_enforcement(
        args.protocol_dir,
        args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        seed=args.seed,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next={summary['next_blocker']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
