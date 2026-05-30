"""No-rollout bounded calibration smoke subset preflight."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.controller_family_task_quality_calibration_preflight import DEFAULT_OUTPUT_DIR as DEFAULT_M1702_OUTPUT_DIR


DEFAULT_OUTPUT_DIR = Path("runs/m1705_controller_family_bounded_calibration_smoke_preflight")
DEFAULT_CALIBRATION_SPECS_JSON = DEFAULT_M1702_OUTPUT_DIR / "calibration_specs.json"
DEFAULT_CALIBRATION_MATRIX_CSV = DEFAULT_M1702_OUTPUT_DIR / "calibration_matrix.csv"
SELECTED_BASE_SPECS_PER_TASK_FAMILY = 3
EXPECTED_TASK_FAMILY_COUNTS = {"T4": 3, "T5": 3}
EXPECTED_CALIBRATION_VARIANTS_PER_BASE_SPEC = 12
EXPECTED_PROFILE_COUNT = 12
EXPECTED_BOUNDED_CALIBRATION_SPEC_COUNT = 72
EXPECTED_BOUNDED_SMOKE_CELL_COUNT = 864


def load_calibration_specs(path: Path | str = DEFAULT_CALIBRATION_SPECS_JSON) -> list[dict[str, Any]]:
    payload = read_json(path)
    return list(payload["calibration_specs"])


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def base_spec_rows(calibration_specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_base: dict[str, dict[str, Any]] = {}
    for spec in calibration_specs:
        base_id = str(spec["base_task_source_id"])
        by_base.setdefault(
            base_id,
            {
                "base_task_source_id": base_id,
                "task_family": str(spec["task_family"]),
                "source_edge": str(spec["source_edge"]),
                "window_tag": str(spec["window_tag"]),
                "executable_source_family": str(spec["executable_source_family"]),
                "env_template_family": str(spec["env_template_family"]),
            },
        )
    return sorted(by_base.values(), key=lambda row: str(row["base_task_source_id"]))


def _diversity_score(candidate: Mapping[str, Any], selected: list[Mapping[str, Any]]) -> int:
    used_source_edges = {str(row["source_edge"]) for row in selected}
    used_executable_sources = {str(row["executable_source_family"]) for row in selected}
    used_templates = {str(row["env_template_family"]) for row in selected}
    used_windows = {str(row["window_tag"]) for row in selected}
    return (
        8 * int(str(candidate["source_edge"]) not in used_source_edges)
        + 4 * int(str(candidate["executable_source_family"]) not in used_executable_sources)
        + 2 * int(str(candidate["env_template_family"]) not in used_templates)
        + int(str(candidate["window_tag"]) not in used_windows)
    )


def select_source_diverse_base_specs(
    bases: list[Mapping[str, Any]],
    *,
    per_task_family: int = SELECTED_BASE_SPECS_PER_TASK_FAMILY,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for task_family in ("T4", "T5"):
        family_candidates = [dict(row) for row in bases if str(row["task_family"]) == task_family]
        family_selected: list[dict[str, Any]] = []
        while len(family_selected) < per_task_family and len(family_selected) < len(family_candidates):
            scored: list[tuple[int, str, dict[str, Any]]] = []
            for candidate in family_candidates:
                base_id = str(candidate["base_task_source_id"])
                if base_id in selected_ids:
                    continue
                scored.append((-_diversity_score(candidate, family_selected), base_id, candidate))
            if not scored:
                break
            _score, _base_id, chosen = min(scored, key=lambda item: (item[0], item[1]))
            chosen = dict(chosen)
            chosen["selection_order"] = len(selected) + 1
            chosen["selection_reason"] = "source_diverse_greedy"
            family_selected.append(chosen)
            selected.append(chosen)
            selected_ids.add(str(chosen["base_task_source_id"]))

    for row in bases:
        row = dict(row)
        base_id = str(row["base_task_source_id"])
        if base_id in selected_ids:
            continue
        row["rejection_reason"] = "source_diverse_budget_exhausted"
        rejected.append(row)

    return selected, rejected


def _spec_csv_row(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "calibration_spec_id": spec["calibration_spec_id"],
        "base_task_source_id": spec["base_task_source_id"],
        "task_family": spec["task_family"],
        "source_edge": spec["source_edge"],
        "window_tag": spec["window_tag"],
        "executable_source_family": spec["executable_source_family"],
        "env_template_family": spec["env_template_family"],
        "track_width_scale": spec["track_width_scale"],
        "finish_variant": spec["finish_variant"],
        "max_steps_scale": spec["max_steps_scale"],
        "track_width": spec["track_width"],
        "finish_pass_distance": spec["finish_pass_distance"],
        "max_steps": spec["max_steps"],
        "contract_violation_count": spec["contract_violation_count"],
        "environment_rollout_scheduled": False,
        "profile_specific_tuning": False,
    }


def contract_violations_for_specs(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for spec in specs:
        messages: list[str] = []
        try:
            assert_human_view_env_contract(build_env_config(spec["env_config"]))
        except Exception as exc:  # noqa: BLE001 - preflight must record all contract failures.
            messages.append(str(exc))
        for message in messages:
            violations.append(
                {
                    "calibration_spec_id": str(spec["calibration_spec_id"]),
                    "base_task_source_id": str(spec["base_task_source_id"]),
                    "violation": message,
                }
            )
    return violations


def _counts_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[key]) for row in rows).items()))


def run_bounded_calibration_smoke_preflight(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    calibration_specs_json: Path | str = DEFAULT_CALIBRATION_SPECS_JSON,
    calibration_matrix_csv: Path | str = DEFAULT_CALIBRATION_MATRIX_CSV,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    calibration_specs = load_calibration_specs(calibration_specs_json)
    bases = base_spec_rows(calibration_specs)
    selected_bases, rejected_bases = select_source_diverse_base_specs(bases)
    selected_base_ids = {str(row["base_task_source_id"]) for row in selected_bases}
    bounded_specs = [dict(spec) for spec in calibration_specs if str(spec["base_task_source_id"]) in selected_base_ids]
    bounded_spec_ids = {str(spec["calibration_spec_id"]) for spec in bounded_specs}
    full_matrix_rows = read_csv_rows(calibration_matrix_csv)
    bounded_matrix_rows = [row for row in full_matrix_rows if str(row["calibration_spec_id"]) in bounded_spec_ids]
    contract_violations = contract_violations_for_specs(bounded_specs)

    task_family_counts = _counts_by_key(selected_bases, "task_family")
    variants_per_base = _counts_by_key(bounded_specs, "base_task_source_id")
    profiles_per_spec = _counts_by_key(bounded_matrix_rows, "calibration_spec_id")
    missing_profile_count = sum(1 for count in profiles_per_spec.values() if count != EXPECTED_PROFILE_COUNT)
    missing_variant_count = sum(1 for count in variants_per_base.values() if count != EXPECTED_CALIBRATION_VARIANTS_PER_BASE_SPEC)
    matrix_rollout_scheduled_count = sum(row.get("environment_rollout_scheduled") == "True" for row in bounded_matrix_rows)
    matrix_training_scheduled_count = sum(row.get("training_scheduled") == "True" for row in bounded_matrix_rows)
    matrix_profile_tuning_count = sum(row.get("profile_specific_tuning") == "True" for row in bounded_matrix_rows)
    missing_config_count = sum(row.get("config_exists") != "True" for row in bounded_matrix_rows)
    missing_checkpoint_count = sum(row.get("checkpoint_exists") != "True" for row in bounded_matrix_rows)
    guardrail_flags = {
        "environment_rollout_started": matrix_rollout_scheduled_count > 0,
        "training_started": matrix_training_scheduled_count > 0,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": matrix_profile_tuning_count > 0,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        len(selected_bases) == sum(EXPECTED_TASK_FAMILY_COUNTS.values())
        and task_family_counts == EXPECTED_TASK_FAMILY_COUNTS
        and len(bounded_specs) == EXPECTED_BOUNDED_CALIBRATION_SPEC_COUNT
        and len(bounded_matrix_rows) == EXPECTED_BOUNDED_SMOKE_CELL_COUNT
        and missing_variant_count == 0
        and missing_profile_count == 0
        and len(contract_violations) == 0
        and missing_config_count == 0
        and missing_checkpoint_count == 0
        and guardrail_violation_count == 0
    )

    generated_at = utc_timestamp()
    artifacts = {
        "summary": str(output / "summary.json"),
        "selected_base_specs": str(output / "selected_base_specs.csv"),
        "rejected_base_specs": str(output / "rejected_base_specs.csv"),
        "bounded_calibration_specs": str(output / "bounded_calibration_specs.json"),
        "bounded_calibration_specs_csv": str(output / "bounded_calibration_specs.csv"),
        "bounded_smoke_matrix": str(output / "bounded_smoke_matrix.csv"),
        "contract_violations": str(output / "contract_violations.csv"),
    }
    summary = {
        "result_class": (
            "controller_family_bounded_calibration_smoke_preflight_pass"
            if passes
            else "controller_family_bounded_calibration_smoke_preflight_fail"
        ),
        "generated_at_utc": generated_at,
        "output_dir": str(output),
        "source_calibration_spec_count": len(calibration_specs),
        "source_matrix_cell_count": len(full_matrix_rows),
        "base_spec_count": len(bases),
        "selected_base_spec_count": len(selected_bases),
        "rejected_base_spec_count": len(rejected_bases),
        "selected_task_family_counts": task_family_counts,
        "bounded_calibration_spec_count": len(bounded_specs),
        "bounded_smoke_matrix_cell_count": len(bounded_matrix_rows),
        "profile_count": len({row["profile_name"] for row in bounded_matrix_rows}),
        "track_width_scale_counts": _counts_by_key(bounded_specs, "track_width_scale"),
        "finish_variant_counts": _counts_by_key(bounded_specs, "finish_variant"),
        "max_steps_scale_counts": _counts_by_key(bounded_specs, "max_steps_scale"),
        "profile_counts": _counts_by_key(bounded_matrix_rows, "profile_name"),
        "variants_per_base_spec_min": min(variants_per_base.values()) if variants_per_base else 0,
        "variants_per_base_spec_max": max(variants_per_base.values()) if variants_per_base else 0,
        "profiles_per_calibration_spec_min": min(profiles_per_spec.values()) if profiles_per_spec else 0,
        "profiles_per_calibration_spec_max": max(profiles_per_spec.values()) if profiles_per_spec else 0,
        "missing_variant_count": missing_variant_count,
        "missing_profile_count": missing_profile_count,
        "contract_violation_count": len(contract_violations),
        "missing_config_count": missing_config_count,
        "missing_checkpoint_count": missing_checkpoint_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": guardrail_flags["environment_rollout_started"],
        "training_started": guardrail_flags["training_started"],
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": guardrail_flags["profile_specific_tuning"],
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "passes_public_preflight_gates": bool(passes),
        "artifacts": artifacts,
        "next_blocker": "m1706-paper-route-controller-family-bounded-calibration-smoke-preflight-result-audit",
    }

    write_csv_rows(output / "selected_base_specs.csv", selected_bases)
    write_csv_rows(output / "rejected_base_specs.csv", rejected_bases)
    write_json(
        output / "bounded_calibration_specs.json",
        {
            "generated_at_utc": generated_at,
            "bounded_calibration_specs": bounded_specs,
        },
    )
    write_csv_rows(output / "bounded_calibration_specs.csv", [_spec_csv_row(row) for row in bounded_specs])
    write_csv_rows(output / "bounded_smoke_matrix.csv", bounded_matrix_rows)
    write_csv_rows(
        output / "contract_violations.csv",
        contract_violations,
        fieldnames=["calibration_spec_id", "base_task_source_id", "violation"],
    )
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-rollout bounded calibration smoke subset.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--calibration-specs", type=Path, default=DEFAULT_CALIBRATION_SPECS_JSON)
    parser.add_argument("--calibration-matrix", type=Path, default=DEFAULT_CALIBRATION_MATRIX_CSV)
    args = parser.parse_args()

    summary = run_bounded_calibration_smoke_preflight(
        output_dir=args.output_dir,
        calibration_specs_json=args.calibration_specs,
        calibration_matrix_csv=args.calibration_matrix,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"selected_base_spec_count={summary['selected_base_spec_count']}")
    print(f"bounded_calibration_spec_count={summary['bounded_calibration_spec_count']}")
    print(f"bounded_smoke_matrix_cell_count={summary['bounded_smoke_matrix_cell_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")


if __name__ == "__main__":
    main()
