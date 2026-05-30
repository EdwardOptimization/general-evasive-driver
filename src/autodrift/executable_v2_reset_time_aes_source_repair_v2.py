"""No-reset reset-time AES source repair v2 helper."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.executable_v2_reset_time_aes_sampler_diagnostic import (
    ACCEPTED,
    REJECT_AEB_FEASIBLE,
    TARGET_LABEL,
    replay_reset_time_obstacle_attempts,
    summarize_attempts,
)
from autodrift.executable_v2_stable_source_targeted_reset_sampler_repair import label_density


DEFAULT_REPAIRED_SPECS = Path(
    "runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/"
    "repaired_targeted_reset_executable_v2_panel_specs.json"
)
DEFAULT_RESET_ROWS = Path(
    "runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m1837_executable_v2_reset_time_aes_source_repair_v2")
MAIN_ATTEMPT_BUDGET = 10000
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"true", "1", "yes", "y"}:
            return True
        if stripped in {"false", "0", "no", "n", ""}:
            return False
    return default


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _sum_count_rows(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(row.get(key, ""))] += int(row.get("count", 0) or 0)
    return dict(sorted(counts.items()))


def _json_counts(counts: Mapping[str, int]) -> str:
    return json.dumps(dict(sorted((str(k), int(v)) for k, v in counts.items())), sort_keys=True)


def _range(value: Any, default: tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (float(value[0]), float(value[1]))
    return default


def _source_key(row: Mapping[str, Any]) -> str:
    return str(
        row.get(
            "source_v1_bounded_panel_spec_id",
            row.get(
                "materialized_bounded_panel_spec_id",
                row.get("source_scenario_spec_id", ""),
            ),
        )
    )


def _copy_obstacle_with_candidate(
    *,
    base: Mapping[str, Any],
    candidate_name: str,
    distance_range: tuple[float, float],
    half_width_range: tuple[float, float],
    max_attempts: int,
) -> dict[str, Any]:
    obstacle = deepcopy(dict(base))
    obstacle["repair_candidate_name"] = candidate_name
    obstacle["allowed_labels"] = [TARGET_LABEL]
    obstacle["require_aeb_infeasible"] = True
    obstacle["distance_range"] = [float(distance_range[0]), float(distance_range[1])]
    obstacle["half_width_range"] = [float(half_width_range[0]), float(half_width_range[1])]
    obstacle["max_sample_attempts"] = int(max_attempts)
    return obstacle


def candidate_obstacles(env_config: Mapping[str, Any], *, main_attempt_budget: int = MAIN_ATTEMPT_BUDGET) -> list[dict[str, Any]]:
    base = deepcopy(dict(env_config.get("obstacle", {})))
    original_distance = _range(base.get("distance_range"), (16.0, 55.0))
    original_half = _range(base.get("half_width_range"), (0.45, 1.15))
    attempts = int(main_attempt_budget)
    candidates = [
        _copy_obstacle_with_candidate(
            base=base,
            candidate_name="original_reset_replay",
            distance_range=original_distance,
            half_width_range=original_half,
            max_attempts=attempts,
        ),
        _copy_obstacle_with_candidate(
            base=base,
            candidate_name="aes_reset_close_band",
            distance_range=(14.0, 24.0),
            half_width_range=(0.30, 0.75),
            max_attempts=attempts,
        ),
        _copy_obstacle_with_candidate(
            base=base,
            candidate_name="aes_reset_close_medium_band",
            distance_range=(16.0, 30.0),
            half_width_range=(0.30, 0.95),
            max_attempts=attempts,
        ),
        _copy_obstacle_with_candidate(
            base=base,
            candidate_name="aes_reset_threshold_band",
            distance_range=(18.0, 24.0),
            half_width_range=(0.30, 0.90),
            max_attempts=attempts,
        ),
        _copy_obstacle_with_candidate(
            base=base,
            candidate_name="aes_reset_wide_search_band",
            distance_range=(10.0, 36.0),
            half_width_range=(0.30, 1.10),
            max_attempts=attempts,
        ),
    ]
    return candidates


def _apply_candidate_env_config(env_config: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    patched = deepcopy(dict(env_config))
    obstacle = {key: value for key, value in dict(candidate).items() if key != "repair_candidate_name"}
    patched["obstacle"] = obstacle
    return patched


def _range_movement(env_config: Mapping[str, Any], candidate: Mapping[str, Any]) -> float:
    base = dict(env_config.get("obstacle", {}))
    base_distance = _range(base.get("distance_range"), (16.0, 55.0))
    base_half = _range(base.get("half_width_range"), (0.45, 1.15))
    cand_distance = _range(candidate.get("distance_range"), base_distance)
    cand_half = _range(candidate.get("half_width_range"), base_half)
    return float(
        abs(base_distance[0] - cand_distance[0])
        + abs(base_distance[1] - cand_distance[1])
        + abs(base_half[0] - cand_half[0])
        + abs(base_half[1] - cand_half[1])
    )


def load_repaired_specs(path: Path | str = DEFAULT_REPAIRED_SPECS) -> list[dict[str, Any]]:
    payload = read_json(path)
    return sorted([dict(row) for row in payload["executable_v2_panel_specs"]], key=lambda row: str(row["v2_panel_spec_id"]))


def load_reset_rows(path: Path | str = DEFAULT_RESET_ROWS) -> list[dict[str, Any]]:
    return sorted(_read_csv_rows(path), key=lambda row: str(row.get("v2_panel_spec_id", "")))


def failed_aes_source_groups(
    *,
    repaired_specs: Iterable[Mapping[str, Any]],
    reset_rows: Iterable[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    specs_by_id = {str(row["v2_panel_spec_id"]): dict(row) for row in repaired_specs}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for reset_row in reset_rows:
        spec_id = str(reset_row.get("v2_panel_spec_id", ""))
        if spec_id not in specs_by_id:
            continue
        if str(reset_row.get("v2_task_label", "")) != TARGET_LABEL:
            continue
        if _bool(reset_row.get("reset_success"), default=False):
            continue
        spec = specs_by_id[spec_id]
        row = deepcopy(spec)
        row["reset_row"] = dict(reset_row)
        groups[_source_key(spec)].append(row)
    return {key: sorted(rows, key=lambda row: str(row["v2_panel_spec_id"])) for key, rows in sorted(groups.items())}


def score_candidate_for_source(
    *,
    source_key: str,
    specs: list[Mapping[str, Any]],
    candidate: Mapping[str, Any],
    main_attempt_budget: int = MAIN_ATTEMPT_BUDGET,
) -> dict[str, Any]:
    label_count_rows: list[dict[str, Any]] = []
    reject_count_rows: list[dict[str, Any]] = []
    attempt_count_total = 0
    accepted_count_total = 0
    accepted_profile_count = 0
    accepted_attempt_slacks: list[int] = []
    profile_count = len(specs)
    base_env_config = dict(specs[0]["env_config"]) if specs else {}
    candidate_env_config = _apply_candidate_env_config(base_env_config, candidate)
    for spec in specs:
        reset_row = dict(spec.get("reset_row", {}))
        eval_seed = int(reset_row.get("eval_seed", 0) or 0)
        attempts = replay_reset_time_obstacle_attempts(
            env_config=candidate_env_config,
            seed=eval_seed,
            max_attempts=int(main_attempt_budget),
        )
        summary = summarize_attempts(attempts)
        attempt_count_total += int(summary["attempt_count"])
        accepted_count = int(summary["accepted_count"])
        accepted_count_total += accepted_count
        if accepted_count > 0:
            accepted_profile_count += 1
            accepted_attempt_slacks.append(int(main_attempt_budget) - int(summary["attempt_count"]))
        for label, count in summary["label_counts"].items():
            label_count_rows.append({"label": label, "count": count})
        for reason, count in summary["reject_reason_counts"].items():
            reject_count_rows.append({"reject_reason": reason, "count": count})
    attempt_count_by_label = _sum_count_rows(label_count_rows, "label")
    attempt_count_by_reject_reason = _sum_count_rows(reject_count_rows, "reject_reason")
    dominant_reject_reason = ""
    nonaccepted = {key: value for key, value in attempt_count_by_reject_reason.items() if key != ACCEPTED}
    if nonaccepted:
        dominant_reject_reason = sorted(nonaccepted.items(), key=lambda item: (-item[1], item[0]))[0][0]
    try:
        offline_density = label_density(
            env_config=base_env_config,
            obstacle=candidate,
            target_label=TARGET_LABEL,
        )
    except Exception:
        offline_density = 0.0
    return {
        "source_v1_bounded_panel_spec_id": source_key,
        "source_scenario_spec_id": specs[0].get("source_scenario_spec_id", "") if specs else "",
        "candidate_name": str(candidate.get("repair_candidate_name", "")),
        "distance_range": list(_range(candidate.get("distance_range"), (0.0, 0.0))),
        "half_width_range": list(_range(candidate.get("half_width_range"), (0.0, 0.0))),
        "max_sample_attempts": int(candidate.get("max_sample_attempts", main_attempt_budget)),
        "profile_count": profile_count,
        "accepted_profile_count": accepted_profile_count,
        "attempt_count_total": attempt_count_total,
        "accepted_count_total": accepted_count_total,
        "attempt_count_by_label": attempt_count_by_label,
        "attempt_count_by_reject_reason": attempt_count_by_reject_reason,
        "dominant_reject_reason": dominant_reject_reason,
        "offline_density": float(offline_density),
        "range_movement": _range_movement(base_env_config, candidate),
        "min_acceptance_attempt_slack": min(accepted_attempt_slacks) if accepted_attempt_slacks else -1,
        "selected": False,
        "selection_reason": "",
    }


def _score_sort_key(row: Mapping[str, Any]) -> tuple[int, int, int, int, float, str]:
    return (
        int(row.get("accepted_profile_count", 0)),
        int(row.get("accepted_count_total", 0)),
        int(row.get("min_acceptance_attempt_slack", -1)),
        -int(row.get("attempt_count_total", 0)),
        -float(row.get("range_movement", 0.0)),
        str(row.get("candidate_name", "")),
    )


def select_source_candidate(
    *,
    source_key: str,
    specs: list[Mapping[str, Any]],
    main_attempt_budget: int = MAIN_ATTEMPT_BUDGET,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidates = candidate_obstacles(dict(specs[0]["env_config"]), main_attempt_budget=main_attempt_budget)
    scored = [
        score_candidate_for_source(
            source_key=source_key,
            specs=specs,
            candidate=candidate,
            main_attempt_budget=main_attempt_budget,
        )
        for candidate in candidates
    ]
    scored.sort(key=_score_sort_key, reverse=True)
    selected = deepcopy(scored[0])
    full_acceptance = int(selected["accepted_profile_count"]) == int(selected["profile_count"])
    selected["selected"] = True
    selected["selection_reason"] = "full_reset_time_aes_acceptance" if full_acceptance else "best_available_but_incomplete"
    for row in scored:
        if row["candidate_name"] == selected["candidate_name"]:
            row["selected"] = True
            row["selection_reason"] = selected["selection_reason"]
    return selected, scored


def _csv_score_row(row: Mapping[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["distance_range"] = json.dumps(output.get("distance_range", []), sort_keys=True)
    output["half_width_range"] = json.dumps(output.get("half_width_range", []), sort_keys=True)
    output["attempt_count_by_label"] = _json_counts(output.get("attempt_count_by_label", {}))
    output["attempt_count_by_reject_reason"] = _json_counts(output.get("attempt_count_by_reject_reason", {}))
    return output


def _patch_spec_with_selected_candidate(
    *,
    spec: Mapping[str, Any],
    selected: Mapping[str, Any],
    main_attempt_budget: int,
) -> dict[str, Any]:
    row = deepcopy(dict(spec))
    env_config = deepcopy(dict(row["env_config"]))
    obstacle = deepcopy(dict(env_config.get("obstacle", {})))
    obstacle["allowed_labels"] = [TARGET_LABEL]
    obstacle["require_aeb_infeasible"] = True
    obstacle["distance_range"] = list(selected["distance_range"])
    obstacle["half_width_range"] = list(selected["half_width_range"])
    obstacle["max_sample_attempts"] = int(main_attempt_budget)
    env_config["obstacle"] = obstacle
    row["env_config"] = env_config
    row["reset_time_aes_source_repair_applied"] = True
    row["reset_time_aes_source_repair_candidate"] = str(selected["candidate_name"])
    row["reset_time_aes_source_repair_selection_reason"] = str(selected["selection_reason"])
    row["reset_time_aes_source_repair_accepted_profile_count"] = int(selected["accepted_profile_count"])
    row["reset_time_aes_source_repair_profile_count"] = int(selected["profile_count"])
    row["reset_ready_spec"] = True
    row["reset_validation_required"] = True
    row["labels_enter_actor_input"] = False
    row["v2_ranking_admissible_by_default"] = False
    return row


def repaired_specs_from_selected_sources(
    *,
    repaired_specs: list[Mapping[str, Any]],
    selected_by_source: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    for spec in repaired_specs:
        source_key = _source_key(spec)
        selected = selected_by_source.get(source_key)
        if selected is None:
            row = deepcopy(dict(spec))
            row["reset_time_aes_source_repair_applied"] = False
            repaired.append(row)
            continue
        repaired.append(
            _patch_spec_with_selected_candidate(
                spec=spec,
                selected=selected,
                main_attempt_budget=int(selected.get("max_sample_attempts", MAIN_ATTEMPT_BUDGET)),
            )
        )
    return sorted(repaired, key=lambda row: str(row["v2_panel_spec_id"]))


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "reset_time_aes_source_repair_plan",
            "admissible": True,
            "reason": "no-reset repaired payload can guide later reset preflight",
        },
        {
            "claim": "reset_feasibility_repaired",
            "admissible": False,
            "reason": "repaired payload still requires reset-only validation",
        },
        {
            "claim": "measured_execution",
            "admissible": False,
            "reason": "measured execution remains blocked until reset support is observed",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "source repair is task-quality infrastructure, not ranking evidence",
        },
    ]


def run_reset_time_aes_source_repair_v2(
    *,
    repaired_specs_path: Path | str = DEFAULT_REPAIRED_SPECS,
    reset_rows_path: Path | str = DEFAULT_RESET_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_source_count: int | None = 2,
    target_profile_count: int | None = 12,
    target_repaired_spec_count: int | None = 36,
    main_attempt_budget: int = MAIN_ATTEMPT_BUDGET,
    next_blocker: str = "m1837-executable-v2-reset-time-aes-source-repair-v2-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    repaired_specs = load_repaired_specs(repaired_specs_path)
    reset_rows = load_reset_rows(reset_rows_path)
    groups = failed_aes_source_groups(repaired_specs=repaired_specs, reset_rows=reset_rows)

    selected_by_source: dict[str, dict[str, Any]] = {}
    candidate_score_rows: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []
    for source_key, specs in groups.items():
        selected, scored = select_source_candidate(
            source_key=source_key,
            specs=specs,
            main_attempt_budget=main_attempt_budget,
        )
        selected_by_source[source_key] = selected
        candidate_score_rows.extend(scored)
        target_rows.append(
            {
                "source_v1_bounded_panel_spec_id": source_key,
                "source_scenario_spec_id": specs[0].get("source_scenario_spec_id", "") if specs else "",
                "profile_count": len(specs),
                "selected_candidate": selected["candidate_name"],
                "accepted_profile_count": selected["accepted_profile_count"],
                "selection_reason": selected["selection_reason"],
            }
        )

    repaired = repaired_specs_from_selected_sources(repaired_specs=repaired_specs, selected_by_source=selected_by_source)
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in repaired)
    ranking_admissible_by_default_count = sum(_bool(row.get("v2_ranking_admissible_by_default")) for row in repaired)
    reset_ready_spec_count = sum(_bool(row.get("reset_ready_spec")) for row in repaired)
    unchanged_non_target_count = sum(not _bool(row.get("reset_time_aes_source_repair_applied")) for row in repaired)
    accepted_source_count = sum(int(row["accepted_profile_count"]) == int(row["profile_count"]) for row in target_rows)
    accepted_profile_count_total = sum(int(row["accepted_profile_count"]) for row in target_rows)
    target_profile_count_total = sum(int(row["profile_count"]) for row in target_rows)
    attempt_count_total = sum(int(row["attempt_count_total"]) for row in candidate_score_rows if _bool(row.get("selected")))
    selected_label_rows: list[dict[str, Any]] = []
    selected_reject_rows: list[dict[str, Any]] = []
    for row in candidate_score_rows:
        if not _bool(row.get("selected")):
            continue
        for label, count in dict(row.get("attempt_count_by_label", {})).items():
            selected_label_rows.append({"label": label, "count": int(count)})
        for reason, count in dict(row.get("attempt_count_by_reject_reason", {})).items():
            selected_reject_rows.append({"reject_reason": reason, "count": int(count)})

    attempt_count_by_label = _sum_count_rows(selected_label_rows, "label")
    attempt_count_by_reject_reason = _sum_count_rows(selected_reject_rows, "reject_reason")
    row_count_by_label = _count_by_key(selected_label_rows, "label")
    row_count_by_reject_reason = _count_by_key(selected_reject_rows, "reject_reason")
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    target_source_matches = target_source_count is None or len(groups) == int(target_source_count)
    profile_matches = target_profile_count is None or all(len(rows) == int(target_profile_count) for rows in groups.values())
    repaired_spec_matches = target_repaired_spec_count is None or len(repaired) == int(target_repaired_spec_count)
    all_sources_accepted = len(groups) > 0 and accepted_source_count == len(groups)
    result_passes = (
        target_source_matches
        and profile_matches
        and repaired_spec_matches
        and all_sources_accepted
        and labels_enter_actor_input_count == 0
        and ranking_admissible_by_default_count == 0
        and reset_ready_spec_count == len(repaired)
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "reset_time_aes_source_repair_targets.csv", target_rows)
    write_csv_rows(output / "reset_time_aes_source_repair_candidate_scores.csv", [_csv_score_row(row) for row in candidate_score_rows])
    write_json(output / "reset_time_aes_source_repair_specs.json", {"reset_time_aes_source_repair_specs": repaired})
    write_csv_rows(output / "reset_time_aes_source_repair_specs.csv", repaired)
    write_json(
        output / "repaired_targeted_reset_executable_v2_panel_specs.json",
        {"generated_at_utc": utc_timestamp(), "executable_v2_panel_specs": repaired},
    )
    write_csv_rows(output / "reset_time_aes_source_repair_claim_boundary.csv", claim_boundary_rows())

    summary = {
        "result_class": "reset_time_aes_source_repair_v2_pass" if result_passes else "reset_time_aes_source_repair_v2_fail",
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "repaired_specs_path": str(repaired_specs_path),
        "reset_rows_path": str(reset_rows_path),
        "target_source_count": len(groups),
        "expected_target_source_count": target_source_count,
        "target_profile_count": target_profile_count,
        "target_profile_count_total": target_profile_count_total,
        "accepted_source_count": int(accepted_source_count),
        "accepted_profile_count_total": int(accepted_profile_count_total),
        "selected_source_count": len(selected_by_source),
        "repaired_spec_count": len(repaired),
        "expected_repaired_spec_count": target_repaired_spec_count,
        "unchanged_non_target_count": int(unchanged_non_target_count),
        "reset_ready_spec_count": int(reset_ready_spec_count),
        "labels_enter_actor_input_count": int(labels_enter_actor_input_count),
        "ranking_admissible_by_default_count": int(ranking_admissible_by_default_count),
        "attempt_count_total": int(attempt_count_total),
        "attempt_count_by_label": attempt_count_by_label,
        "attempt_count_by_reject_reason": attempt_count_by_reject_reason,
        "row_count_by_label": row_count_by_label,
        "row_count_by_reject_reason": row_count_by_reject_reason,
        "summary_aggregation_version": "row_and_attempt_counts_v1",
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "reset_time_aes_source_repair_targets": str(output / "reset_time_aes_source_repair_targets.csv"),
            "reset_time_aes_source_repair_candidate_scores": str(
                output / "reset_time_aes_source_repair_candidate_scores.csv"
            ),
            "reset_time_aes_source_repair_specs": str(output / "reset_time_aes_source_repair_specs.json"),
            "repaired_targeted_reset_executable_v2_panel_specs": str(
                output / "repaired_targeted_reset_executable_v2_panel_specs.json"
            ),
            "reset_time_aes_source_repair_claim_boundary": str(
                output / "reset_time_aes_source_repair_claim_boundary.csv"
            ),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repaired-specs", type=Path, default=DEFAULT_REPAIRED_SPECS)
    parser.add_argument("--reset-rows", type=Path, default=DEFAULT_RESET_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-source-count", type=int, default=2)
    parser.add_argument("--target-profile-count", type=int, default=12)
    parser.add_argument("--target-repaired-spec-count", type=int, default=36)
    parser.add_argument("--main-attempt-budget", type=int, default=MAIN_ATTEMPT_BUDGET)
    parser.add_argument(
        "--next-blocker",
        default="m1837-executable-v2-reset-time-aes-source-repair-v2-execution-design",
    )
    args = parser.parse_args()
    summary = run_reset_time_aes_source_repair_v2(
        repaired_specs_path=args.repaired_specs,
        reset_rows_path=args.reset_rows,
        output_dir=args.output_dir,
        target_source_count=args.target_source_count,
        target_profile_count=args.target_profile_count,
        target_repaired_spec_count=args.target_repaired_spec_count,
        main_attempt_budget=args.main_attempt_budget,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    print(f"target_source_count={summary['target_source_count']}")
    print(f"accepted_profile_count_total={summary['accepted_profile_count_total']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
