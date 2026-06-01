"""No-rollout current-sim task-quality/offtrack support repair candidates."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_ORIGINAL_EPISODES = Path("runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/episode_rows.csv")
DEFAULT_REPEAT_EPISODES = Path("runs/m2184_paper_route_current_sim_repeat_measured_execution/episode_rows.csv")
DEFAULT_EXECUTABLE_TASK_SPECS = Path(
    "runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2190_paper_route_current_sim_task_quality_offtrack_support_repair_candidates")
DEFAULT_CANDIDATE_CONFIG = Path("configs/paper_route_current_sim_task_quality_offtrack_support_repair_candidates_v0.json")
REPAIR_BRANCH_ID = "m2190_current_sim_task_quality_offtrack_support_repair_v0"
AXIS_QUOTAS = {
    "offtrack_saturation_relief": 96,
    "terminal_boundary_support_ladder": 64,
    "older_history_ambiguity_support_ladder": 64,
    "diagnostic_warmup_support_ladder": 32,
    "positive_support_preservation": 32,
}
EXPECTED_SPLITS = {"public_debug": 176, "public_gate": 112}
CLAIM_FLAGS = (
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)
BOOLEAN_GUARDRAILS = (
    "ranking_admissible_by_default",
    "profile_specific_tuning",
    "actor_input_contract_changed",
    "environment_reset_started",
    "environment_rollout_started",
    "training_started",
    *CLAIM_FLAGS,
)
FIELDNAMES = [
    "repair_branch_id",
    "repair_candidate_id",
    "repair_axis",
    "repair_variant_id",
    "repair_split",
    "parent_task_source_id",
    "parent_task_family",
    "parent_source_family_template",
    "parent_capability_pair",
    "parent_claim_level_target",
    "parent_support_class",
    "parent_episode_count",
    "parent_success_count",
    "parent_collision_count",
    "parent_offtrack_count",
    "parent_success_rate",
    "parent_offtrack_rate",
    "delta_track_width",
    "delta_track_radius",
    "delta_obstacle_distance_min",
    "delta_obstacle_distance_max",
    "delta_obstacle_half_width_min",
    "delta_obstacle_half_width_max",
    "delta_reveal_step",
    "delta_speed_min",
    "delta_speed_max",
    "preserve_history_semantics",
    "ranking_admissible_by_default",
    "profile_specific_tuning",
    "actor_input_contract_changed",
    "environment_reset_started",
    "environment_rollout_started",
    "training_started",
    *CLAIM_FLAGS,
]


VARIANTS = {
    "offtrack_saturation_relief": [
        {"id": "road_wide_075", "tw": 0.75, "tr": 0.0, "dmin": 0.0, "dmax": 0.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "road_wide_150", "tw": 1.50, "tr": 0.0, "dmin": 0.0, "dmax": 0.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "radius_plus_4", "tw": 0.75, "tr": 4.0, "dmin": 0.0, "dmax": 0.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "distance_plus_4", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 4.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "half_width_minus_010", "tw": 0.0, "tr": 0.0, "dmin": 2.0, "dmax": 4.0, "hwmin": -0.05, "hwmax": -0.10, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "reveal_earlier_8", "tw": 0.75, "tr": 2.0, "dmin": 2.0, "dmax": 4.0, "hwmin": -0.05, "hwmax": -0.10, "reveal": -8, "vmin": 0.0, "vmax": 0.0},
    ],
    "terminal_boundary_support_ladder": [
        {"id": "t5_distance_4", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 4.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t5_distance_8", "tw": 0.0, "tr": 0.0, "dmin": 8.0, "dmax": 8.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t5_width_minus_010", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 6.0, "hwmin": -0.05, "hwmax": -0.10, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t5_width_minus_020", "tw": 0.0, "tr": 0.0, "dmin": 6.0, "dmax": 8.0, "hwmin": -0.10, "hwmax": -0.20, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t5_speed_minus_1", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 6.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": -1.0, "vmax": -1.0},
        {"id": "t5_speed_minus_2", "tw": 0.0, "tr": 0.0, "dmin": 6.0, "dmax": 8.0, "hwmin": -0.05, "hwmax": -0.10, "reveal": 0, "vmin": -1.0, "vmax": -2.0},
        {"id": "t5_reveal_earlier_8", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 6.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": -8, "vmin": 0.0, "vmax": 0.0},
        {"id": "t5_balanced_relief", "tw": 0.75, "tr": 2.0, "dmin": 6.0, "dmax": 8.0, "hwmin": -0.05, "hwmax": -0.10, "reveal": -8, "vmin": -1.0, "vmax": -1.0},
    ],
    "older_history_ambiguity_support_ladder": [
        {"id": "t4_road_wide_075", "tw": 0.75, "tr": 0.0, "dmin": 0.0, "dmax": 0.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t4_radius_plus_4", "tw": 0.75, "tr": 4.0, "dmin": 0.0, "dmax": 0.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t4_distance_plus_4", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 4.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t4_distance_plus_8", "tw": 0.0, "tr": 0.0, "dmin": 8.0, "dmax": 8.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t4_reveal_earlier_8", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 4.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": -8, "vmin": 0.0, "vmax": 0.0},
        {"id": "t4_reveal_earlier_16", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 8.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": -16, "vmin": 0.0, "vmax": 0.0},
        {"id": "t4_half_width_minus_010", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 4.0, "hwmin": -0.05, "hwmax": -0.10, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t4_balanced_relief", "tw": 0.75, "tr": 4.0, "dmin": 4.0, "dmax": 8.0, "hwmin": -0.05, "hwmax": -0.10, "reveal": -8, "vmin": 0.0, "vmax": 0.0},
    ],
    "diagnostic_warmup_support_ladder": [
        {"id": "t3_road_wide_075", "tw": 0.75, "tr": 0.0, "dmin": 0.0, "dmax": 0.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t3_distance_plus_4", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 4.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "t3_reveal_earlier_8", "tw": 0.0, "tr": 0.0, "dmin": 4.0, "dmax": 4.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": -8, "vmin": 0.0, "vmax": 0.0},
        {"id": "t3_balanced_relief", "tw": 0.75, "tr": 2.0, "dmin": 4.0, "dmax": 6.0, "hwmin": -0.05, "hwmax": -0.10, "reveal": -8, "vmin": 0.0, "vmax": 0.0},
    ],
    "positive_support_preservation": [
        {"id": "support_mild_road", "tw": 0.50, "tr": 0.0, "dmin": 0.0, "dmax": 0.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "support_mild_distance", "tw": 0.0, "tr": 0.0, "dmin": 2.0, "dmax": 2.0, "hwmin": 0.0, "hwmax": 0.0, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "support_mild_width", "tw": 0.0, "tr": 0.0, "dmin": 2.0, "dmax": 2.0, "hwmin": -0.05, "hwmax": -0.05, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
        {"id": "support_balanced", "tw": 0.50, "tr": 2.0, "dmin": 2.0, "dmax": 4.0, "hwmin": -0.05, "hwmax": -0.05, "reveal": 0, "vmin": 0.0, "vmax": 0.0},
    ],
}


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _is_success(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "success_obstacle_pass"


def _is_collision(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "collision_failure"


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "off_track_noncollision_noncompletion"


def load_executable_specs(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("executable_task_specs")
    if not isinstance(rows, list):
        raise ValueError("candidate generator expected executable_task_specs list")
    return [dict(row) for row in rows]


def aggregate_task_support(
    *,
    original_episodes: Path | str,
    repeat_episodes: Path | str,
    executable_task_specs: Path | str,
) -> list[dict[str, Any]]:
    rows = [*read_csv_rows(original_episodes), *read_csv_rows(repeat_episodes)]
    specs_by_id = {str(spec.get("task_source_id", "")): spec for spec in load_executable_specs(executable_task_specs)}
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("task_source_id", ""))].append(row)
    output: list[dict[str, Any]] = []
    for task_source_id, task_rows in sorted(grouped.items()):
        spec = specs_by_id.get(task_source_id, {})
        episode_count = len(task_rows)
        success_count = sum(1 for row in task_rows if _is_success(row))
        collision_count = sum(1 for row in task_rows if _is_collision(row))
        offtrack_count = sum(1 for row in task_rows if _is_offtrack(row))
        success_rate = float(success_count / episode_count) if episode_count else 0.0
        offtrack_rate = float(offtrack_count / episode_count) if episode_count else 0.0
        if success_count == 0 and offtrack_count > 0:
            support_class = "zero_success_offtrack"
        elif success_count <= 1 and offtrack_rate >= 0.75:
            support_class = "near_zero_offtrack"
        elif success_rate >= 0.25:
            support_class = "positive_support"
        else:
            support_class = "mixed_support"
        output.append(
            {
                "task_source_id": task_source_id,
                "task_family": str(spec.get("task_family", task_rows[0].get("task_family", ""))),
                "source_family_template": str(spec.get("source_family_template", task_rows[0].get("source_family_template", ""))),
                "capability_pair": str(spec.get("capability_pair", task_rows[0].get("capability_pair", ""))),
                "claim_level_target": str(spec.get("claim_level_target", task_rows[0].get("claim_level_target", ""))),
                "episode_count": episode_count,
                "success_count": success_count,
                "collision_count": collision_count,
                "offtrack_count": offtrack_count,
                "success_rate": success_rate,
                "offtrack_rate": offtrack_rate,
                "support_class": support_class,
            }
        )
    return output


def _sorted_offtrack(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(tasks, key=lambda row: (-int(row["offtrack_count"]), int(row["success_count"]), str(row["task_source_id"])))


def _sorted_support(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(tasks, key=lambda row: (-int(row["success_count"]), int(row["offtrack_count"]), str(row["task_source_id"])))


def select_anchors(axis: str, tasks: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if axis == "terminal_boundary_support_ladder":
        candidates = _sorted_offtrack([row for row in tasks if row["task_family"] == "T5_terminal_boundary_near_constraint"])
    elif axis == "older_history_ambiguity_support_ladder":
        candidates = _sorted_offtrack([row for row in tasks if row["task_family"] == "T4_same_current_different_older_history"])
    elif axis == "diagnostic_warmup_support_ladder":
        candidates = _sorted_offtrack([row for row in tasks if row["task_family"] == "T3_diagnostic_warmup_obstacle_reveal"])
    elif axis == "positive_support_preservation":
        candidates = _sorted_support(tasks)
    else:
        candidates = _sorted_offtrack(tasks)
    if not candidates:
        raise ValueError(f"no anchors available for {axis}")
    return [candidates[index % len(candidates)] for index in range(count)]


def _split_for_index(index: int) -> str:
    return "public_debug" if index < EXPECTED_SPLITS["public_debug"] else "public_gate"


def build_candidates(tasks: list[dict[str, Any]], *, axis_quotas: Mapping[str, int] | None = None) -> list[dict[str, Any]]:
    quotas = dict(axis_quotas or AXIS_QUOTAS)
    candidates: list[dict[str, Any]] = []
    for axis, quota in quotas.items():
        variants = VARIANTS[axis]
        anchor_count = int(quota) // len(variants)
        if anchor_count * len(variants) != int(quota):
            raise ValueError(f"quota for {axis} must be divisible by {len(variants)}")
        anchors = select_anchors(axis, tasks, anchor_count)
        for anchor_index, anchor in enumerate(anchors):
            for variant in variants:
                candidate_index = len(candidates)
                candidates.append(
                    {
                        "repair_branch_id": REPAIR_BRANCH_ID,
                        "repair_candidate_id": f"m2190-current-sim-repair-{candidate_index:04d}",
                        "repair_axis": axis,
                        "repair_variant_id": variant["id"],
                        "repair_split": _split_for_index(candidate_index),
                        "parent_task_source_id": anchor["task_source_id"],
                        "parent_task_family": anchor["task_family"],
                        "parent_source_family_template": anchor["source_family_template"],
                        "parent_capability_pair": anchor["capability_pair"],
                        "parent_claim_level_target": anchor["claim_level_target"],
                        "parent_support_class": anchor["support_class"],
                        "parent_episode_count": int(anchor["episode_count"]),
                        "parent_success_count": int(anchor["success_count"]),
                        "parent_collision_count": int(anchor["collision_count"]),
                        "parent_offtrack_count": int(anchor["offtrack_count"]),
                        "parent_success_rate": float(anchor["success_rate"]),
                        "parent_offtrack_rate": float(anchor["offtrack_rate"]),
                        "delta_track_width": float(variant["tw"]),
                        "delta_track_radius": float(variant["tr"]),
                        "delta_obstacle_distance_min": float(variant["dmin"]),
                        "delta_obstacle_distance_max": float(variant["dmax"]),
                        "delta_obstacle_half_width_min": float(variant["hwmin"]),
                        "delta_obstacle_half_width_max": float(variant["hwmax"]),
                        "delta_reveal_step": int(variant["reveal"]),
                        "delta_speed_min": float(variant["vmin"]),
                        "delta_speed_max": float(variant["vmax"]),
                        "preserve_history_semantics": True,
                        "ranking_admissible_by_default": False,
                        "profile_specific_tuning": False,
                        "actor_input_contract_changed": False,
                        "environment_reset_started": False,
                        "environment_rollout_started": False,
                        "training_started": False,
                        "controller_family_ranking_claim_made": False,
                        "finite_window_vs_gru_conclusion_made": False,
                        "paper_level_claim_made": False,
                        "level3_self_id_claim_made": False,
                        "_anchor_index": anchor_index,
                    }
                )
    return [{key: value for key, value in row.items() if key != "_anchor_index"} for row in candidates]


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _guardrail_count(rows: list[Mapping[str, Any]], fields: Iterable[str]) -> int:
    count = 0
    for row in rows:
        for field in fields:
            if str(row.get(field, "")).strip().lower() in {"1", "true", "yes"}:
                count += 1
    return count


def run_candidate_generation(
    *,
    original_episodes: Path | str = DEFAULT_ORIGINAL_EPISODES,
    repeat_episodes: Path | str = DEFAULT_REPEAT_EPISODES,
    executable_task_specs: Path | str = DEFAULT_EXECUTABLE_TASK_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    candidate_config: Path | str = DEFAULT_CANDIDATE_CONFIG,
    axis_quotas: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    quotas = dict(axis_quotas or AXIS_QUOTAS)
    tasks = aggregate_task_support(
        original_episodes=original_episodes,
        repeat_episodes=repeat_episodes,
        executable_task_specs=executable_task_specs,
    )
    candidates = build_candidates(tasks, axis_quotas=quotas)
    axis_counts = _count_by(candidates, "repair_axis")
    split_counts = _count_by(candidates, "repair_split")
    candidate_ids = [str(row["repair_candidate_id"]) for row in candidates]
    duplicate_candidate_id_count = len(candidate_ids) - len(set(candidate_ids))
    boolean_guardrail_violation_count = _guardrail_count(candidates, BOOLEAN_GUARDRAILS)
    exact_axis_quota_pass = axis_counts == dict(sorted(quotas.items()))
    exact_split_quota_pass = split_counts == EXPECTED_SPLITS
    candidate_count = len(candidates)
    result_pass = (
        candidate_count == sum(quotas.values())
        and exact_axis_quota_pass
        and exact_split_quota_pass
        and duplicate_candidate_id_count == 0
        and boolean_guardrail_violation_count == 0
    )
    task_support_path = output / "parent_task_support_rows.csv"
    candidate_rows_path = output / "repair_candidate_rows.csv"
    write_csv_rows(task_support_path, tasks)
    write_csv_rows(candidate_rows_path, candidates, fieldnames=FIELDNAMES)
    config = {
        "repair_branch_id": REPAIR_BRANCH_ID,
        "generated_at_utc": utc_timestamp(),
        "candidate_count": candidate_count,
        "axis_quotas": quotas,
        "split_quotas": EXPECTED_SPLITS,
        "candidates": candidates,
    }
    write_json(candidate_config, config)
    summary = {
        "result_class": (
            "current_sim_task_quality_offtrack_support_repair_candidate_generation_pass"
            if result_pass
            else "current_sim_task_quality_offtrack_support_repair_candidate_generation_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "candidate_config": str(candidate_config),
        "candidate_count": candidate_count,
        "expected_candidate_count": sum(quotas.values()),
        "axis_counts": axis_counts,
        "expected_axis_counts": dict(sorted(quotas.items())),
        "exact_axis_quota_pass": exact_axis_quota_pass,
        "split_counts": split_counts,
        "expected_split_counts": EXPECTED_SPLITS,
        "exact_split_quota_pass": exact_split_quota_pass,
        "duplicate_candidate_id_count": duplicate_candidate_id_count,
        "boolean_guardrail_violation_count": boolean_guardrail_violation_count,
        "profile_specific_candidate_count": _guardrail_count(candidates, ("profile_specific_tuning",)),
        "actor_input_contract_change_count": _guardrail_count(candidates, ("actor_input_contract_changed",)),
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "training_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repair_candidate_rows": str(candidate_rows_path),
            "parent_task_support_rows": str(task_support_path),
            "candidate_config": str(candidate_config),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": "m2191-paper-route-current-sim-task-quality-offtrack-support-repair-candidate-generation-result-audit",
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {"complete": bool(result_pass), "candidate_count": candidate_count, "result_class": summary["result_class"]},
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-episodes", type=Path, default=DEFAULT_ORIGINAL_EPISODES)
    parser.add_argument("--repeat-episodes", type=Path, default=DEFAULT_REPEAT_EPISODES)
    parser.add_argument("--executable-task-specs", type=Path, default=DEFAULT_EXECUTABLE_TASK_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--candidate-config", type=Path, default=DEFAULT_CANDIDATE_CONFIG)
    args = parser.parse_args()
    summary = run_candidate_generation(
        original_episodes=args.original_episodes,
        repeat_episodes=args.repeat_episodes,
        executable_task_specs=args.executable_task_specs,
        output_dir=args.output_dir,
        candidate_config=args.candidate_config,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"candidate_config={args.candidate_config}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"boolean_guardrail_violation_count={summary['boolean_guardrail_violation_count']}")


if __name__ == "__main__":
    main()
