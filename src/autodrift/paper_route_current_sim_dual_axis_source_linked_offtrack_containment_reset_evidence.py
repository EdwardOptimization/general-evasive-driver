"""Source-linked reset evidence for offtrack containment candidate families."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv


DEFAULT_SOURCE_OVERLAY_DIR = Path(
    "runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization"
)
DEFAULT_SOURCE_EFFECTIVE_DIR = Path(
    "runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence"
)
DEFAULT_TARGET_FAMILY_COUNT = 4
DEFAULT_EVAL_SEED_BASE = 241000
DEFAULT_NEXT_BLOCKER = (
    "m2411-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-result-audit"
)
RESULT_PASS = "current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence_pass"
RESULT_FAIL = "current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence_incomplete_or_fail"
ACTOR_CONTRACT_ID = "P0_human_view_no_wheel_no_oracle"

FAMILY_FIELDNAMES = [
    "candidate_id",
    "candidate_family",
    "source_key_count",
    "matched_source_key_count",
    "unmatched_source_key_count",
    "matched_effective_candidate_count",
    "source_linked_scenario_reference_count",
    "unique_reset_target_count",
    "family_static_validation_pass",
    "family_reset_pass",
    "family_reset_failure_count",
    "ranking_admissible",
    "winner_selected",
]
SCENARIO_FIELDNAMES = [
    "candidate_id",
    "candidate_family",
    "effective_candidate_id",
    "matched_source_keys",
    "pack_id",
    "scenario_spec_id",
    "reset_target_key",
    "scenario_family_id",
    "role_family",
    "source_slice_axis",
    "source_slice_value",
    "actor_contract_id",
    "include_privileged_params",
    "wheel_observation_mode",
    "obstacle_relative_velocity_mode",
    "history_length",
    "env_config_present",
    "actor_contract_guardrail_pass",
    "claim_boundary_forbids_execution",
    "static_validation_pass",
    "failure_reasons",
]
UNMATCHED_FIELDNAMES = ["candidate_id", "candidate_family", "source_row_key"]
RESET_TARGET_FIELDNAMES = [
    "reset_target_key",
    "env_config_hash",
    "pack_id",
    "scenario_spec_id",
    "family_ids",
    "effective_candidate_ids",
    "scenario_reference_count",
]
RESET_FIELDNAMES = [
    "reset_target_key",
    "environment_load_attempted",
    "environment_reset_attempted",
    "environment_reset_success",
    "observation_length",
    "observation_finite",
    "environment_step_count",
    "policy_action_executed",
    "failure_reason",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _json_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _observation_length(obs: Any) -> int:
    array = np.asarray(obs, dtype=np.float64)
    if array.ndim == 0:
        return 0
    return int(array.size)


def _finite_observation(obs: Any) -> bool:
    try:
        array = np.asarray(obs, dtype=np.float64)
    except (TypeError, ValueError):
        return False
    return bool(array.size > 0 and np.all(np.isfinite(array)))


def _claim_boundary_forbids_execution(payload: Mapping[str, Any]) -> bool:
    boundary = payload.get("claim_boundary")
    if not isinstance(boundary, Mapping):
        return False
    forbidden_true_keys = [
        "active_config_overwritten",
        "environment_step_count",
        "policy_action_executed",
        "rollout_started",
        "repair_execution_started",
        "training_started",
        "ranking_admissible",
        "winner_selected",
    ]
    return not any(_bool(boundary.get(key)) for key in forbidden_true_keys)


def _env_config(selected: Mapping[str, Any]) -> Mapping[str, Any] | None:
    env_config = selected.get("env_config")
    return env_config if isinstance(env_config, Mapping) else None


def _actor_contract_pass(selected: Mapping[str, Any]) -> bool:
    env_config = _env_config(selected)
    if env_config is None:
        return False
    return (
        str(selected.get("actor_contract_id", "")) == ACTOR_CONTRACT_ID
        and not _bool(env_config.get("include_privileged_params"))
        and str(env_config.get("wheel_observation_mode", "")) == "none"
        and str(env_config.get("obstacle_relative_velocity_mode", "")) == "zero"
        and int(env_config.get("history_length", -1)) == 1
    )


def _source_keys_for_effective_row(row: Mapping[str, Any]) -> set[str]:
    axis = str(row.get("source_slice_axis", ""))
    value = str(row.get("source_slice_value", ""))
    keys = {f"{axis}:{value}"}
    if axis and value:
        keys.add(f"source_slice_axis+source_slice_value:{axis}|{value}")
    return keys


def _reset_target_key(pack_id: str, scenario_spec_id: str, env_config: Mapping[str, Any]) -> str:
    return f"{pack_id}|{scenario_spec_id}|{_json_hash(env_config)[:16]}"


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "source_linked_family_reset_evidence",
            "admissible": True,
            "reason": "M2410 may claim reset-only source-linked evidence if all reset gates pass",
        },
        {
            "claim": "environment_step_or_policy_action",
            "admissible": False,
            "reason": "M2410 stops immediately after reset",
        },
        {
            "claim": "measured_controller_performance",
            "admissible": False,
            "reason": "M2410 does not roll out a policy",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2410 does not execute M2406 repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2410 does not train or evaluate a repaired driver",
        },
        {
            "claim": "candidate_family_ranking",
            "admissible": False,
            "reason": "source-linked reset evidence is an admissibility gate, not ranking",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2410 is reset preflight evidence, not paper-level evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2410 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2410 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2410 does not run measured validation needed for a verdict",
        },
    ]


def load_family_overlays(source_overlay_dir: Path) -> list[dict[str, Any]]:
    rows = read_csv_rows(source_overlay_dir / "repair_candidate_overlays.csv")
    loaded: list[dict[str, Any]] = []
    for row in rows:
        path = Path(str(row.get("overlay_path", "")))
        payload = read_json(path)
        loaded.append({"row": row, "path": path, "payload": payload})
    return loaded


def load_effective_candidates(source_effective_dir: Path) -> list[dict[str, Any]]:
    rows = read_csv_rows(source_effective_dir / "effective_candidate_config_rows.csv")
    loaded: list[dict[str, Any]] = []
    for row in rows:
        path = Path(str(row.get("effective_candidate_config_path", "")))
        payload = read_json(path)
        loaded.append(
            {
                "row": row,
                "path": path,
                "payload": payload,
                "source_keys": _source_keys_for_effective_row(row),
            }
        )
    return loaded


def build_source_linked_rows(
    *,
    source_overlay_dir: Path,
    source_effective_dir: Path,
    families: Sequence[Mapping[str, Any]],
    effective_candidates: Sequence[Mapping[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Mapping[str, Any]],
]:
    scenario_rows: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, Any]] = []
    target_refs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    target_env_configs: dict[str, Mapping[str, Any]] = {}
    family_partial: dict[str, dict[str, Any]] = {}

    for family in families:
        payload = dict(family.get("payload", {}))
        family_path = Path(str(family.get("path", "")))
        candidate_id = str(payload.get("candidate_id", ""))
        candidate_family = str(payload.get("candidate_family", ""))
        source_keys = {str(key) for key in payload.get("source_row_keys", [])}
        family_ok = (
            _inside_dir(family_path, source_overlay_dir)
            and not _bool(payload.get("ranking_admissible"))
            and not _bool(payload.get("winner_selected"))
            and not _bool(payload.get("repair_execution_allowed"))
            and not _bool(payload.get("training_allowed"))
        )
        matched: list[Mapping[str, Any]] = []
        matched_source_keys: set[str] = set()
        for effective in effective_candidates:
            overlap = source_keys & set(effective.get("source_keys", set()))
            if overlap:
                matched.append(effective)
                matched_source_keys.update(overlap)

        for source_key in sorted(source_keys - matched_source_keys):
            unmatched_rows.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_family": candidate_family,
                    "source_row_key": source_key,
                }
            )

        family_partial[candidate_id] = {
            "candidate_id": candidate_id,
            "candidate_family": candidate_family,
            "source_key_count": len(source_keys),
            "matched_source_key_count": len(matched_source_keys),
            "unmatched_source_key_count": len(source_keys - matched_source_keys),
            "matched_effective_candidate_count": len({str(item.get("row", {}).get("candidate_id", "")) for item in matched}),
            "ranking_admissible": False,
            "winner_selected": False,
            "family_ok": family_ok,
        }

        for effective in matched:
            effective_row = dict(effective.get("row", {}))
            effective_payload = dict(effective.get("payload", {}))
            effective_candidate_id = str(effective_payload.get("candidate_id", effective_row.get("candidate_id", "")))
            claim_boundary_ok = _claim_boundary_forbids_execution(effective_payload)
            matched_keys = sorted(source_keys & set(effective.get("source_keys", set())))
            for selected in effective_payload.get("selected_scenario_specs", []):
                env_config = _env_config(selected)
                failures: list[str] = []
                if not family_ok:
                    failures.append("family_overlay_guardrail_failure")
                if not env_config:
                    failures.append("missing_env_config")
                if not _actor_contract_pass(selected):
                    failures.append("actor_contract_guardrail_violation")
                if not claim_boundary_ok:
                    failures.append("claim_boundary_allows_forbidden_execution")
                pack_id = str(selected.get("pack_id", ""))
                scenario_spec_id = str(selected.get("scenario_spec_id", ""))
                reset_key = _reset_target_key(pack_id, scenario_spec_id, dict(env_config or {})) if env_config else ""
                row = {
                    "candidate_id": candidate_id,
                    "candidate_family": candidate_family,
                    "effective_candidate_id": effective_candidate_id,
                    "matched_source_keys": "|".join(matched_keys),
                    "pack_id": pack_id,
                    "scenario_spec_id": scenario_spec_id,
                    "reset_target_key": reset_key,
                    "scenario_family_id": str(selected.get("scenario_family_id", "")),
                    "role_family": str(selected.get("role_family", "")),
                    "source_slice_axis": str(effective_row.get("source_slice_axis", "")),
                    "source_slice_value": str(effective_row.get("source_slice_value", "")),
                    "actor_contract_id": str(selected.get("actor_contract_id", "")),
                    "include_privileged_params": _bool((env_config or {}).get("include_privileged_params")),
                    "wheel_observation_mode": str((env_config or {}).get("wheel_observation_mode", "")),
                    "obstacle_relative_velocity_mode": str((env_config or {}).get("obstacle_relative_velocity_mode", "")),
                    "history_length": int((env_config or {}).get("history_length", -1)),
                    "env_config_present": bool(env_config),
                    "actor_contract_guardrail_pass": _actor_contract_pass(selected),
                    "claim_boundary_forbids_execution": claim_boundary_ok,
                    "static_validation_pass": not failures,
                    "failure_reasons": ";".join(failures),
                }
                scenario_rows.append(row)
                if env_config and reset_key:
                    target_env_configs.setdefault(reset_key, dict(env_config))
                    target_refs[reset_key].append(row)

    target_rows: list[dict[str, Any]] = []
    for reset_key, refs in sorted(target_refs.items()):
        first = refs[0]
        target_rows.append(
            {
                "reset_target_key": reset_key,
                "env_config_hash": reset_key.split("|")[-1],
                "pack_id": str(first.get("pack_id", "")),
                "scenario_spec_id": str(first.get("scenario_spec_id", "")),
                "family_ids": "|".join(sorted({str(ref.get("candidate_id", "")) for ref in refs})),
                "effective_candidate_ids": "|".join(sorted({str(ref.get("effective_candidate_id", "")) for ref in refs})),
                "scenario_reference_count": len(refs),
            }
        )

    scenario_count_by_family = Counter(str(row.get("candidate_id", "")) for row in scenario_rows)
    unique_reset_by_family: dict[str, set[str]] = defaultdict(set)
    for row in scenario_rows:
        unique_reset_by_family[str(row.get("candidate_id", ""))].add(str(row.get("reset_target_key", "")))
    family_rows: list[dict[str, Any]] = []
    for candidate_id, row in sorted(family_partial.items()):
        family_rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_family": row["candidate_family"],
                "source_key_count": row["source_key_count"],
                "matched_source_key_count": row["matched_source_key_count"],
                "unmatched_source_key_count": row["unmatched_source_key_count"],
                "matched_effective_candidate_count": row["matched_effective_candidate_count"],
                "source_linked_scenario_reference_count": scenario_count_by_family[candidate_id],
                "unique_reset_target_count": len(unique_reset_by_family[candidate_id] - {""}),
                "family_static_validation_pass": bool(row["family_ok"]),
                "family_reset_pass": False,
                "family_reset_failure_count": 0,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )

    return family_rows, scenario_rows, unmatched_rows, target_rows, target_env_configs


def reset_target(*, target_row: Mapping[str, Any], env_config: Mapping[str, Any], eval_seed: int) -> dict[str, Any]:
    key = str(target_row.get("reset_target_key", ""))
    try:
        config = build_env_config(dict(env_config))
        env = AutoDriftEnv(config)
        try:
            obs, _info = env.reset(seed=int(eval_seed))
        finally:
            close = getattr(env, "close", None)
            if callable(close):
                close()
        return {
            "reset_target_key": key,
            "environment_load_attempted": True,
            "environment_reset_attempted": True,
            "environment_reset_success": True,
            "observation_length": _observation_length(obs),
            "observation_finite": _finite_observation(obs),
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": "",
        }
    except Exception as exc:  # noqa: BLE001 - reset preflight records exact failure text.
        return {
            "reset_target_key": key,
            "environment_load_attempted": True,
            "environment_reset_attempted": True,
            "environment_reset_success": False,
            "observation_length": 0,
            "observation_finite": False,
            "environment_step_count": 0,
            "policy_action_executed": False,
            "failure_reason": str(exc),
        }


def attach_family_reset_results(
    *,
    family_rows: Sequence[Mapping[str, Any]],
    scenario_rows: Sequence[Mapping[str, Any]],
    reset_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reset_by_key = {str(row.get("reset_target_key", "")): row for row in reset_rows}
    scenario_by_family: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in scenario_rows:
        scenario_by_family[str(row.get("candidate_id", ""))].append(row)

    updated: list[dict[str, Any]] = []
    for family in family_rows:
        row = dict(family)
        failures = 0
        for scenario in scenario_by_family[str(row.get("candidate_id", ""))]:
            reset_row = reset_by_key.get(str(scenario.get("reset_target_key", "")), {})
            if not (_bool(scenario.get("static_validation_pass")) and _bool(reset_row.get("environment_reset_success"))):
                failures += 1
        row["family_static_validation_pass"] = failures == 0 and int(row.get("source_linked_scenario_reference_count", 0)) > 0
        row["family_reset_pass"] = row["family_static_validation_pass"] and failures == 0
        row["family_reset_failure_count"] = failures
        updated.append(row)
    return updated


def run_source_linked_offtrack_containment_reset_evidence(
    *,
    source_overlay_dir: Path | str = DEFAULT_SOURCE_OVERLAY_DIR,
    source_effective_dir: Path | str = DEFAULT_SOURCE_EFFECTIVE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_family_count: int = DEFAULT_TARGET_FAMILY_COUNT,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_overlay = Path(source_overlay_dir)
    source_effective = Path(source_effective_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_overlay_summary = read_json(source_overlay / "summary.json")
    source_effective_summary = read_json(source_effective / "summary.json")
    families = load_family_overlays(source_overlay)
    effective_candidates = load_effective_candidates(source_effective)

    family_rows, scenario_rows, unmatched_rows, target_rows, target_env_configs = build_source_linked_rows(
        source_overlay_dir=source_overlay,
        source_effective_dir=source_effective,
        families=families,
        effective_candidates=effective_candidates,
    )
    static_failure_count = sum(not _bool(row.get("static_validation_pass")) for row in scenario_rows)
    reset_rows: list[dict[str, Any]] = []
    if static_failure_count == 0:
        for index, target_row in enumerate(target_rows):
            env_config = target_env_configs.get(str(target_row.get("reset_target_key", "")), {})
            reset_rows.append(reset_target(target_row=target_row, env_config=env_config, eval_seed=int(eval_seed_base) + index))
    family_rows = attach_family_reset_results(
        family_rows=family_rows,
        scenario_rows=scenario_rows,
        reset_rows=reset_rows,
    )

    reset_failure_rows = [row for row in reset_rows if not _bool(row.get("environment_reset_success"))]
    claim_rows = claim_boundary_rows()
    family_count = len(family_rows)
    matched_family_count = sum(int(row.get("matched_effective_candidate_count", 0)) > 0 for row in family_rows)
    family_without_match_count = family_count - matched_family_count
    family_reset_pass_count = sum(_bool(row.get("family_reset_pass")) for row in family_rows)
    family_reset_failure_count = family_count - family_reset_pass_count
    environment_load_attempt_count = sum(_bool(row.get("environment_load_attempted")) for row in reset_rows)
    environment_reset_attempt_count = sum(_bool(row.get("environment_reset_attempted")) for row in reset_rows)
    environment_reset_success_count = sum(_bool(row.get("environment_reset_success")) for row in reset_rows)
    environment_step_count = sum(int(row.get("environment_step_count", 0)) for row in reset_rows)
    policy_action_executed = any(_bool(row.get("policy_action_executed")) for row in reset_rows)
    ranking_admissible_count = 0
    winner_selected_count = 0
    active_config_overwrite_count = 0
    guardrail_flags = {
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "policy_action_executed": policy_action_executed,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "candidate_family_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    failure_types_observed = [
        name
        for name, count in [
            ("family_source_link_failure", family_without_match_count),
            ("static_schema_failure", static_failure_count),
            ("scenario_sampling_failure", len(reset_failure_rows)),
            ("forbidden_execution_failure", environment_step_count + int(policy_action_executed)),
        ]
        if count
    ]
    passes = (
        source_overlay_summary.get("result_class")
        == "current_sim_dual_axis_offtrack_containment_repair_candidate_materialization_pass"
        and source_effective_summary.get("result_class")
        == "current_sim_dual_axis_effective_config_schema_repair_materialization_pass"
        and family_count == int(target_family_count)
        and matched_family_count == int(target_family_count)
        and family_without_match_count == 0
        and len(scenario_rows) > 0
        and len(target_rows) > 0
        and static_failure_count == 0
        and environment_load_attempt_count == len(target_rows)
        and environment_reset_attempt_count == len(target_rows)
        and environment_reset_success_count == len(target_rows)
        and not reset_failure_rows
        and family_reset_pass_count == int(target_family_count)
        and family_reset_failure_count == 0
        and environment_step_count == 0
        and not policy_action_executed
        and active_config_overwrite_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL

    write_csv_rows(output / "source_linked_family_rows.csv", family_rows, fieldnames=FAMILY_FIELDNAMES)
    write_csv_rows(output / "source_linked_scenario_rows.csv", scenario_rows, fieldnames=SCENARIO_FIELDNAMES)
    write_csv_rows(output / "unmatched_source_key_rows.csv", unmatched_rows, fieldnames=UNMATCHED_FIELDNAMES)
    write_csv_rows(output / "reset_target_rows.csv", target_rows, fieldnames=RESET_TARGET_FIELDNAMES)
    write_csv_rows(output / "reset_validation_rows.csv", reset_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", reset_failure_rows, fieldnames=RESET_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "source_overlay_dir": str(source_overlay),
        "source_effective_dir": str(source_effective),
        "output_dir": str(output),
        "source_overlay_result_class": source_overlay_summary.get("result_class", ""),
        "source_effective_result_class": source_effective_summary.get("result_class", ""),
        "candidate_family_count": family_count,
        "target_family_count": int(target_family_count),
        "matched_family_count": matched_family_count,
        "family_without_match_count": family_without_match_count,
        "source_effective_candidate_count": len(effective_candidates),
        "matched_effective_candidate_count": len(
            {str(row.get("effective_candidate_id", "")) for row in scenario_rows}
        ),
        "source_linked_scenario_reference_count": len(scenario_rows),
        "unique_reset_target_count": len(target_rows),
        "unmatched_source_key_count": len(unmatched_rows),
        "static_validation_failure_count": static_failure_count,
        "environment_load_attempt_count": environment_load_attempt_count,
        "environment_reset_attempt_count": environment_reset_attempt_count,
        "environment_reset_success_count": environment_reset_success_count,
        "environment_reset_failure_count": len(reset_failure_rows),
        "environment_reset_started": environment_reset_attempt_count > 0,
        "environment_step_count": environment_step_count,
        "policy_action_executed": policy_action_executed,
        "family_reset_pass_count": family_reset_pass_count,
        "family_reset_failure_count": family_reset_failure_count,
        "active_config_overwrite_count": active_config_overwrite_count,
        "active_config_overwritten": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "candidate_family_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types_observed,
        "matched_effective_candidates_by_family": {
            str(row.get("candidate_id", "")): int(row.get("matched_effective_candidate_count", 0))
            for row in family_rows
        },
        "source_linked_scenarios_by_family": {
            str(row.get("candidate_id", "")): int(row.get("source_linked_scenario_reference_count", 0))
            for row in family_rows
        },
        "unique_reset_targets_by_family": {
            str(row.get("candidate_id", "")): int(row.get("unique_reset_target_count", 0))
            for row in family_rows
        },
        "unmatched_source_keys_by_family": {
            str(row.get("candidate_id", "")): int(row.get("unmatched_source_key_count", 0))
            for row in family_rows
        },
        "reset_target_counts_by_pack": _count_by(target_rows, "pack_id"),
        "artifacts": {
            "summary": str(output / "summary.json"),
            "source_linked_family_rows": str(output / "source_linked_family_rows.csv"),
            "source_linked_scenario_rows": str(output / "source_linked_scenario_rows.csv"),
            "unmatched_source_key_rows": str(output / "unmatched_source_key_rows.csv"),
            "reset_target_rows": str(output / "reset_target_rows.csv"),
            "reset_validation_rows": str(output / "reset_validation_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-overlay-dir", type=Path, default=DEFAULT_SOURCE_OVERLAY_DIR)
    parser.add_argument("--source-effective-dir", type=Path, default=DEFAULT_SOURCE_EFFECTIVE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-family-count", type=int, default=DEFAULT_TARGET_FAMILY_COUNT)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_source_linked_offtrack_containment_reset_evidence(
        source_overlay_dir=args.source_overlay_dir,
        source_effective_dir=args.source_effective_dir,
        output_dir=args.output_dir,
        target_family_count=int(args.target_family_count),
        eval_seed_base=int(args.eval_seed_base),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_family_count={summary['candidate_family_count']}")
    print(f"matched_family_count={summary['matched_family_count']}")
    print(f"source_linked_scenario_reference_count={summary['source_linked_scenario_reference_count']}")
    print(f"unique_reset_target_count={summary['unique_reset_target_count']}")
    print(f"environment_reset_attempt_count={summary['environment_reset_attempt_count']}")
    print(f"environment_reset_success_count={summary['environment_reset_success_count']}")
    print(f"family_reset_pass_count={summary['family_reset_pass_count']}")
    print(f"unmatched_source_key_count={summary['unmatched_source_key_count']}")
    print(f"environment_step_count={summary['environment_step_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
