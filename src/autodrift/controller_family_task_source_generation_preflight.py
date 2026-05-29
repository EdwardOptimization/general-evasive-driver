"""No-training bounded task-source spec generation preflight."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from math import floor
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_task_source_mapping_preflight import (
    FORBIDDEN_MAPPING_KEY_FRAGMENTS,
)


DEFAULT_MAPPING = Path("runs/m1677_controller_family_decisive_task_source_mapping_preflight/task_source_mapping.json")
DEFAULT_OUTPUT_DIR = Path("runs/m1680_controller_family_bounded_task_source_generation_preflight")

TARGET_TOTAL_SPECS = 72
MAX_TOTAL_SPECS = 96
MIN_TASK_FAMILY_SHARE = 0.40
MIN_SOURCE_FAMILY_COUNT = 8
MIN_SOURCE_EDGE_COUNT = 10
MIN_WINDOW_TAG_COUNT = 3
MAX_SINGLE_SOURCE_FAMILY_SHARE = 0.30
MAX_SINGLE_SOURCE_EDGE_SHARE = 0.20
MAX_SINGLE_METADATA_ROLE_SHARE = 0.55
GENERATION_SEED_BASE = 168000


def _task_rows(mapping: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in mapping.get("candidate_rows", [])
        if row.get("mapping_status") != "aggregate_inventory_only"
    ]


def _round_robin_by_edge(
    rows: list[dict[str, Any]],
    *,
    target_count: int,
    edge_cap: int,
    role_counts: Counter[str],
    role_cap: int,
) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[str(row["source_edge"])].append(row)
    edge_order = sorted(buckets)
    selected: list[dict[str, Any]] = []
    edge_counts: Counter[str] = Counter()
    cursor: dict[str, int] = defaultdict(int)

    while len(selected) < target_count:
        progressed = False
        for edge in edge_order:
            if len(selected) >= target_count:
                break
            if edge_counts[edge] >= edge_cap:
                continue
            bucket = buckets[edge]
            if not bucket:
                continue
            row: dict[str, Any] | None = None
            for _ in range(len(bucket)):
                candidate = bucket[cursor[edge] % len(bucket)]
                cursor[edge] += 1
                role = str(candidate["metadata_source_role"])
                if role_counts[role] < role_cap:
                    row = candidate
                    break
            if row is None:
                continue
            selected.append(row)
            edge_counts[edge] += 1
            role_counts[str(row["metadata_source_role"])] += 1
            progressed = True
        if not progressed:
            break
    return selected


def select_source_rows(
    mapping: dict[str, Any],
    *,
    target_total: int = TARGET_TOTAL_SPECS,
    max_edge_share: float = MAX_SINGLE_SOURCE_EDGE_SHARE,
) -> list[dict[str, Any]]:
    rows_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _task_rows(mapping):
        rows_by_task[str(row["task_family"])].append(row)

    per_family_target = target_total // 2
    edge_cap = max(1, floor(target_total * max_edge_share))
    role_cap = max(1, floor(target_total * MAX_SINGLE_METADATA_ROLE_SHARE))
    selected: list[dict[str, Any]] = []
    role_counts: Counter[str] = Counter()
    for task_family in ("T4", "T5"):
        selected.extend(
            _round_robin_by_edge(
                sorted(rows_by_task.get(task_family, []), key=lambda row: (row["source_edge"], row["mapping_id"])),
                target_count=per_family_target,
                edge_cap=edge_cap,
                role_counts=role_counts,
                role_cap=role_cap,
            )
        )
    return selected[:target_total]


def build_task_source_specs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        window_tags = list(row.get("window_tags") or ["mapping_window_unspecified"])
        primary_window = window_tags[0]
        specs.append(
            {
                "task_source_id": f"m1680-spec-{index:04d}",
                "task_family": row["task_family"],
                "source_edge": row["source_edge"],
                "source_family_left": row["source_family_left"],
                "source_family_right": row["source_family_right"],
                "window_tag": primary_window,
                "seed_namespace_source": list(row.get("seed_namespaces") or []),
                "generation_seed": GENERATION_SEED_BASE + index,
                "source_metadata_roles": [row["metadata_source_role"]],
                "controller_profiles_required": list(EXPECTED_PROFILE_NAMES),
                "controls_required": [
                    "L1_one_step",
                    "L2_normal_windows",
                    "matched_L2_current_tiled_windows",
                    "L3_online_gru",
                    "L3_reset_control_corrected",
                ],
                "mapping_lineage": {
                    "source_mapping_id": row["mapping_id"],
                    "metadata_source_role": row["metadata_source_role"],
                    "metadata_source": row["metadata_source"],
                    "fresh_generation_required": True,
                    "direct_benchmark_row": False,
                },
            }
        )
    return specs


def key_violations(specs: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    stack: list[tuple[str, Any]] = [(spec.get("task_source_id", "unknown"), spec) for spec in specs]
    while stack:
        path, value = stack.pop()
        if isinstance(value, dict):
            for key, item in value.items():
                lowered = key.lower()
                if any(fragment in lowered for fragment in FORBIDDEN_MAPPING_KEY_FRAGMENTS):
                    violations.append(f"{path}::{key}")
                stack.append((f"{path}.{key}", item))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                stack.append((f"{path}[{index}]", item))
    return sorted(violations)


def budget_summary(specs: list[dict[str, Any]]) -> dict[str, Any]:
    task_counter = Counter(str(spec["task_family"]) for spec in specs)
    edge_counter = Counter(str(spec["source_edge"]) for spec in specs)
    role_counter: Counter[str] = Counter()
    family_counter: Counter[str] = Counter()
    window_counter = Counter(str(spec["window_tag"]) for spec in specs)
    for spec in specs:
        family_counter[str(spec["source_family_left"])] += 1
        family_counter[str(spec["source_family_right"])] += 1
        for role in spec["source_metadata_roles"]:
            role_counter[str(role)] += 1

    spec_count = len(specs)
    endpoint_total = sum(family_counter.values())
    min_task_share = (min(task_counter.values()) / spec_count) if task_counter else 0.0
    max_family_share = (max(family_counter.values()) / endpoint_total) if endpoint_total else 0.0
    max_edge_share = (max(edge_counter.values()) / spec_count) if spec_count else 0.0
    max_role_share = (max(role_counter.values()) / spec_count) if spec_count else 0.0
    cap_passes = {
        "spec_count": 0 < spec_count <= MAX_TOTAL_SPECS,
        "target_total_specs": spec_count == TARGET_TOTAL_SPECS,
        "min_task_family_share": min_task_share >= MIN_TASK_FAMILY_SHARE,
        "min_source_family_count": len(family_counter) >= MIN_SOURCE_FAMILY_COUNT,
        "min_source_edge_count": len(edge_counter) >= MIN_SOURCE_EDGE_COUNT,
        "min_window_tag_count": len(window_counter) >= MIN_WINDOW_TAG_COUNT,
        "max_single_source_family_share": max_family_share <= MAX_SINGLE_SOURCE_FAMILY_SHARE,
        "max_single_source_edge_share": max_edge_share <= MAX_SINGLE_SOURCE_EDGE_SHARE,
        "max_single_metadata_role_share": max_role_share <= MAX_SINGLE_METADATA_ROLE_SHARE,
    }
    return {
        "spec_count": spec_count,
        "task_family_counts": dict(sorted(task_counter.items())),
        "source_family_counts": dict(sorted(family_counter.items())),
        "source_edge_counts": dict(sorted(edge_counter.items())),
        "window_tag_counts": dict(sorted(window_counter.items())),
        "metadata_role_counts": dict(sorted(role_counter.items())),
        "min_task_family_share": min_task_share,
        "source_family_count": len(family_counter),
        "source_edge_count": len(edge_counter),
        "window_tag_count": len(window_counter),
        "max_single_source_family_share": max_family_share,
        "max_single_source_edge_share": max_edge_share,
        "max_single_metadata_role_share": max_role_share,
        "cap_passes": cap_passes,
        "all_caps_pass": all(cap_passes.values()),
    }


def budget_summary_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"metric": "spec_count", "value": summary["spec_count"], "passed": summary["cap_passes"]["spec_count"]},
        {
            "metric": "target_total_specs",
            "value": summary["spec_count"],
            "threshold": TARGET_TOTAL_SPECS,
            "passed": summary["cap_passes"]["target_total_specs"],
        },
        {
            "metric": "min_task_family_share",
            "value": summary["min_task_family_share"],
            "threshold": MIN_TASK_FAMILY_SHARE,
            "passed": summary["cap_passes"]["min_task_family_share"],
        },
        {
            "metric": "source_family_count",
            "value": summary["source_family_count"],
            "threshold": MIN_SOURCE_FAMILY_COUNT,
            "passed": summary["cap_passes"]["min_source_family_count"],
        },
        {
            "metric": "source_edge_count",
            "value": summary["source_edge_count"],
            "threshold": MIN_SOURCE_EDGE_COUNT,
            "passed": summary["cap_passes"]["min_source_edge_count"],
        },
        {
            "metric": "window_tag_count",
            "value": summary["window_tag_count"],
            "threshold": MIN_WINDOW_TAG_COUNT,
            "passed": summary["cap_passes"]["min_window_tag_count"],
        },
        {
            "metric": "max_single_source_family_share",
            "value": summary["max_single_source_family_share"],
            "threshold": MAX_SINGLE_SOURCE_FAMILY_SHARE,
            "passed": summary["cap_passes"]["max_single_source_family_share"],
        },
        {
            "metric": "max_single_source_edge_share",
            "value": summary["max_single_source_edge_share"],
            "threshold": MAX_SINGLE_SOURCE_EDGE_SHARE,
            "passed": summary["cap_passes"]["max_single_source_edge_share"],
        },
        {
            "metric": "max_single_metadata_role_share",
            "value": summary["max_single_metadata_role_share"],
            "threshold": MAX_SINGLE_METADATA_ROLE_SHARE,
            "passed": summary["cap_passes"]["max_single_metadata_role_share"],
        },
    ]
    return rows


def run_generation_preflight(
    *,
    mapping_path: Path | str = DEFAULT_MAPPING,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    mapping = read_json(mapping_path)
    selected_rows = select_source_rows(mapping)
    specs = build_task_source_specs(selected_rows)
    budget = budget_summary(specs)
    violations = key_violations(specs)

    write_json(
        output / "task_source_specs.json",
        {
            "protocol_name": "controller_family_bounded_task_source_generation_preflight",
            "generated_at_utc": utc_timestamp(),
            "claim_scope": "task-source spec preflight only",
            "mapping_source": str(mapping_path),
            "task_source_specs": specs,
        },
    )
    write_csv_rows(output / "source_budget_summary.csv", budget_summary_rows(budget))

    guardrail_flags = {
        "environment_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "hidden_action_target_key_used": bool(violations),
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_controller_profiles_covered = all(
        spec["controller_profiles_required"] == list(EXPECTED_PROFILE_NAMES) for spec in specs
    )
    passes = (
        budget["all_caps_pass"]
        and not violations
        and all_controller_profiles_covered
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "controller_family_bounded_task_source_generation_preflight_pass"
            if passes
            else "controller_family_bounded_task_source_generation_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "mapping_source": str(mapping_path),
        "task_source_specs": str(output / "task_source_specs.json"),
        "source_budget_summary": str(output / "source_budget_summary.csv"),
        **budget,
        "hidden_action_target_key_violation_count": len(violations),
        "hidden_action_target_key_violations": violations,
        "all_controller_profiles_covered": all_controller_profiles_covered,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "passes_public_smoke_gates": passes,
        "environment_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "level3_self_id_claim_made": False,
        "next_blocker": (
            "audit_task_source_generation_preflight_before_rollout_design"
            if passes
            else "repair_task_source_generation_budget_or_leakage_before_rollout"
        ),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_generation_preflight(mapping_path=args.mapping, output_dir=args.output_dir)
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"task_source_specs={args.output_dir / 'task_source_specs.json'}")
    print(f"source_budget_summary={args.output_dir / 'source_budget_summary.csv'}")
    return 0 if summary["passes_public_smoke_gates"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
