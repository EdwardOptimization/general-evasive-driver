"""No-training audit for source-history repeat failed offsets."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


COMPOSITION_DIMENSIONS = ("pair_id", "probe_template", "source_family_pair", "source_fault_pair")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _offset_pass(row: dict[str, Any]) -> bool:
    return bool(
        not _bool(row.get("forbidden_parameter_mutation_detected", False))
        and _finite_float(row.get("eval_group_all_rows_both_positive_fraction", 0.0)) >= 0.25
        and _finite_float(row.get("eval_both_directional_fraction", 0.0)) >= 0.25
        and int(float(row.get("full_group_all_rows_both_positive_count", 0))) > 15
        and int(float(row.get("full_both_positive_count", 0))) > 30
    )


def _first_history_frame_by_id(history_frame_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    first_by_id: dict[str, dict[str, str]] = {}
    for row in history_frame_rows:
        history_id = str(row.get("history_id", ""))
        if history_id and history_id not in first_by_id:
            first_by_id[history_id] = row
    return first_by_id


def _history_meta_by_intervention(history_run_dir: Path) -> dict[str, dict[str, Any]]:
    history_frames = _read_csv(history_run_dir / "history_frame_rows.csv")
    history_interventions = _read_csv(history_run_dir / "history_intervention_rows.csv")
    wrong_history_rows = _read_csv(history_run_dir / "wrong_history_pair_rows.csv")

    first_frame = _first_history_frame_by_id(history_frames)
    wrong_by_intervention = {str(row["history_intervention_id"]): row for row in wrong_history_rows}
    meta_by_intervention: dict[str, dict[str, Any]] = {}
    condition_meta_by_group: dict[tuple[str, str], dict[str, dict[str, str]]] = {}

    for row in history_interventions:
        history_intervention_id = str(row["history_intervention_id"])
        correct_history_id = str(row["correct_history_id"])
        wrong_history_id = str(wrong_by_intervention.get(history_intervention_id, {}).get("wrong_history_id", ""))
        correct_frame = first_frame.get(correct_history_id, {})
        wrong_frame = first_frame.get(wrong_history_id, {})
        pair_id = str(row["pair_id"])
        probe_template = str(row["probe_template"])
        condition = str(row["condition"])
        group_key = (pair_id, probe_template)
        condition_meta_by_group.setdefault(group_key, {})[condition] = correct_frame
        correct_fault_family = str(correct_frame.get("fault_family", "unknown"))
        wrong_fault_family = str(wrong_frame.get("fault_family", "unknown"))
        correct_fault_name = str(correct_frame.get("fault_name", "unknown"))
        wrong_fault_name = str(wrong_frame.get("fault_name", "unknown"))
        meta_by_intervention[history_intervention_id] = {
            "correct_history_id": correct_history_id,
            "wrong_history_id": wrong_history_id,
            "correct_fault_family": correct_fault_family,
            "wrong_fault_family": wrong_fault_family,
            "correct_fault_name": correct_fault_name,
            "wrong_fault_name": wrong_fault_name,
            "fault_family_pair": f"{correct_fault_family}->{wrong_fault_family}",
            "fault_name_pair": f"{correct_fault_name}->{wrong_fault_name}",
        }

    for row in history_interventions:
        history_intervention_id = str(row["history_intervention_id"])
        group_key = (str(row["pair_id"]), str(row["probe_template"]))
        group_meta = condition_meta_by_group.get(group_key, {})
        a_frame = group_meta.get("A", {})
        b_frame = group_meta.get("B", {})
        family_a = str(a_frame.get("fault_family", "unknown"))
        family_b = str(b_frame.get("fault_family", "unknown"))
        fault_a = str(a_frame.get("fault_name", "unknown"))
        fault_b = str(b_frame.get("fault_name", "unknown"))
        meta_by_intervention[history_intervention_id].update(
            {
                "source_family_pair": f"{family_a}->{family_b}",
                "source_fault_pair": f"{fault_a}->{fault_b}",
            }
        )
    return meta_by_intervention


def _offset_summary_rows(scope_rows: list[dict[str, str]], enriched_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups_by_offset: dict[int, list[dict[str, Any]]] = {}
    for row in enriched_groups:
        if str(row["split"]) == "eval":
            groups_by_offset.setdefault(int(row["split_offset"]), []).append(row)

    rows: list[dict[str, Any]] = []
    for row in sorted(scope_rows, key=lambda item: int(float(item["split_offset"]))):
        offset = int(float(row["split_offset"]))
        eval_groups = groups_by_offset.get(offset, [])
        failed_groups = [group for group in eval_groups if not _bool(group.get("all_rows_both_positive", False))]
        offset_pass = _offset_pass(row)
        rows.append(
            {
                "split_offset": offset,
                "offset_status": "pass" if offset_pass else "fail",
                "offset_pass": offset_pass,
                "eval_both_directional_fraction": _finite_float(row["eval_both_directional_fraction"]),
                "eval_group_all_rows_both_positive_fraction": _finite_float(
                    row["eval_group_all_rows_both_positive_fraction"]
                ),
                "full_both_positive_count": int(float(row["full_both_positive_count"])),
                "full_group_all_rows_both_positive_count": int(float(row["full_group_all_rows_both_positive_count"])),
                "eval_group_count": int(len(eval_groups)),
                "eval_failed_group_count": int(len(failed_groups)),
                "eval_failed_group_fraction": float(len(failed_groups) / len(eval_groups)) if eval_groups else 0.0,
                "eval_pair_count": int(len({str(group["pair_id"]) for group in eval_groups})),
                "eval_probe_template_count": int(len({str(group["probe_template"]) for group in eval_groups})),
                "eval_source_family_pair_count": int(len({str(group["source_family_pair"]) for group in eval_groups})),
                "eval_source_fault_pair_count": int(len({str(group["source_fault_pair"]) for group in eval_groups})),
                "eval_group_min_margin_mean": _mean([_finite_float(group["group_min_margin"]) for group in eval_groups]),
                "eval_failed_group_min_margin_mean": _mean(
                    [_finite_float(group["group_min_margin"]) for group in failed_groups]
                ),
            }
        )
    return rows


def _enrich_directional_rows(
    directional_rows: list[dict[str, str]],
    meta_by_intervention: dict[str, dict[str, Any]],
    offset_pass_by_offset: dict[int, bool],
    scope: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in directional_rows:
        if str(row.get("split", "")) != "eval":
            continue
        if str(row.get("init_name", scope)) != scope:
            continue
        offset = int(float(row["split_offset"]))
        meta = meta_by_intervention.get(str(row["history_intervention_id"]), {})
        correct_positive = _bool(row.get("correct_positive", False))
        wrong_positive = _bool(row.get("wrong_history_positive", False))
        if correct_positive and wrong_positive:
            directional_status = "both_positive"
        elif correct_positive or wrong_positive:
            directional_status = "mutually_exclusive"
        else:
            directional_status = "both_negative"
        rows.append(
            {
                "split_offset": offset,
                "split": "eval",
                "offset_status": "pass" if offset_pass_by_offset.get(offset, False) else "fail",
                "offset_pass": bool(offset_pass_by_offset.get(offset, False)),
                "history_intervention_id": int(float(row["history_intervention_id"])),
                "intervention_id": int(float(row["intervention_id"])),
                "pair_id": int(float(row["pair_id"])),
                "condition": str(row["condition"]),
                "probe_template": str(row["probe_template"]),
                "correct_history_id": int(float(row["correct_history_id"])),
                "wrong_history_id": str(meta.get("wrong_history_id", "")),
                "correct_fault_family": str(meta.get("correct_fault_family", "unknown")),
                "wrong_fault_family": str(meta.get("wrong_fault_family", "unknown")),
                "source_family_pair": str(meta.get("source_family_pair", "unknown->unknown")),
                "source_fault_pair": str(meta.get("source_fault_pair", "unknown->unknown")),
                "correct_preference_margin": _finite_float(row["correct_preference_margin"]),
                "wrong_history_preference_margin": _finite_float(row["wrong_history_preference_margin"]),
                "min_preference_margin": _finite_float(row["min_preference_margin"]),
                "correct_positive": correct_positive,
                "wrong_history_positive": wrong_positive,
                "both_positive": _bool(row.get("both_positive", False)),
                "mutually_exclusive": _bool(row.get("mutually_exclusive", False)),
                "directional_status": directional_status,
            }
        )
    return rows


def _enrich_group_rows(
    group_rows: list[dict[str, str]],
    meta_by_intervention: dict[str, dict[str, Any]],
    directional_eval_rows: list[dict[str, Any]],
    offset_pass_by_offset: dict[int, bool],
    scope: str,
) -> list[dict[str, Any]]:
    meta_by_group: dict[tuple[int, str], dict[str, str]] = {}
    for row in directional_eval_rows:
        key = (int(row["pair_id"]), str(row["probe_template"]))
        meta_by_group.setdefault(
            key,
            {
                "source_family_pair": str(row["source_family_pair"]),
                "source_fault_pair": str(row["source_fault_pair"]),
            },
        )

    rows: list[dict[str, Any]] = []
    for row in group_rows:
        if str(row.get("split", "")) != "eval":
            continue
        if str(row.get("scope", scope)) != scope:
            continue
        offset = int(float(row["split_offset"]))
        key = (int(float(row["pair_id"])), str(row["probe_template"]))
        meta = meta_by_group.get(key, {})
        rows.append(
            {
                "split_offset": offset,
                "split": "eval",
                "offset_status": "pass" if offset_pass_by_offset.get(offset, False) else "fail",
                "offset_pass": bool(offset_pass_by_offset.get(offset, False)),
                "pair_id": key[0],
                "probe_template": key[1],
                "row_count": int(float(row["row_count"])),
                "both_positive_count": int(float(row["both_positive_count"])),
                "all_rows_both_positive": _bool(row["all_rows_both_positive"]),
                "any_row_both_positive": _bool(row["any_row_both_positive"]),
                "group_min_margin": _finite_float(row["group_min_margin"]),
                "group_balance_loss": _finite_float(row["group_balance_loss"]),
                "source_family_pair": str(meta.get("source_family_pair", "unknown->unknown")),
                "source_fault_pair": str(meta.get("source_fault_pair", "unknown->unknown")),
            }
        )
    return rows


def _composition_summary(enriched_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for status in ("pass", "fail"):
        status_rows = [row for row in enriched_groups if str(row["offset_status"]) == status]
        for dimension in COMPOSITION_DIMENSIONS:
            counts: dict[str, dict[str, Any]] = {}
            for row in status_rows:
                value = str(row[dimension])
                bucket = counts.setdefault(value, {"group_count": 0, "failed_group_count": 0, "offsets": set()})
                bucket["group_count"] += 1
                bucket["failed_group_count"] += 0 if _bool(row["all_rows_both_positive"]) else 1
                bucket["offsets"].add(int(row["split_offset"]))
            total_failed = sum(int(bucket["failed_group_count"]) for bucket in counts.values())
            total_groups = sum(int(bucket["group_count"]) for bucket in counts.values())
            for value, bucket in sorted(counts.items(), key=lambda item: (-int(item[1]["failed_group_count"]), item[0])):
                failed_count = int(bucket["failed_group_count"])
                group_count = int(bucket["group_count"])
                summaries.append(
                    {
                        "offset_status": status,
                        "dimension": dimension,
                        "value": value,
                        "group_count": group_count,
                        "failed_group_count": failed_count,
                        "group_fraction_within_status": float(group_count / total_groups) if total_groups else 0.0,
                        "failed_group_share_within_status": (
                            float(failed_count / total_failed) if total_failed else 0.0
                        ),
                        "group_failure_fraction": float(failed_count / group_count) if group_count else 0.0,
                        "offset_count": int(len(bucket["offsets"])),
                        "offsets": "|".join(str(offset) for offset in sorted(bucket["offsets"])),
                    }
                )
    return summaries


def _top_failed_share(composition_rows: list[dict[str, Any]], dimension: str) -> tuple[str, float, int]:
    rows = [
        row
        for row in composition_rows
        if str(row["offset_status"]) == "fail"
        and str(row["dimension"]) == dimension
        and int(row["failed_group_count"]) > 0
    ]
    if not rows:
        return "", 0.0, 0
    top = max(rows, key=lambda row: (float(row["failed_group_share_within_status"]), int(row["failed_group_count"])))
    return str(top["value"]), float(top["failed_group_share_within_status"]), int(top["failed_group_count"])


def classify_failed_offset_audit(
    *,
    failing_offsets: list[int],
    composition_rows: list[dict[str, Any]],
) -> tuple[str, str]:
    if not failing_offsets:
        return "source_history_failed_offset_audit_no_failed_offsets", "route to repeat-result audit"
    concentration = {
        dimension: _top_failed_share(composition_rows, dimension)[1] for dimension in COMPOSITION_DIMENSIONS
    }
    if max(concentration.values(), default=0.0) >= 0.5:
        return (
            "source_history_failed_offset_audit_concentrated",
            "route to source-history corpus refresh or objective reweighting design",
        )
    return (
        "source_history_failed_offset_audit_diffuse",
        "route to objective redesign, sequence preference targets, or branch synthesis",
    )


def run_failed_offset_audit(
    *,
    repeat_run_dir: Path,
    history_run_dir: Path,
    run_dir: Path,
    scope: str = "fusion_head",
) -> dict[str, Any]:
    repeat_run_dir = Path(repeat_run_dir)
    history_run_dir = Path(history_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    scope_rows = [row for row in _read_csv(repeat_run_dir / "scope_summaries.csv") if str(row["scope"]) == scope]
    if not scope_rows:
        raise ValueError(f"missing scope rows for scope={scope}")
    offset_pass_by_offset = {int(float(row["split_offset"])): _offset_pass(row) for row in scope_rows}
    passing_offsets = sorted(offset for offset, passed in offset_pass_by_offset.items() if passed)
    failing_offsets = sorted(offset for offset, passed in offset_pass_by_offset.items() if not passed)
    meta_by_intervention = _history_meta_by_intervention(history_run_dir)

    directional_eval_rows = _enrich_directional_rows(
        _read_csv(repeat_run_dir / "directional_rows.csv"),
        meta_by_intervention=meta_by_intervention,
        offset_pass_by_offset=offset_pass_by_offset,
        scope=scope,
    )
    eval_group_rows = _enrich_group_rows(
        _read_csv(repeat_run_dir / "group_rows.csv"),
        meta_by_intervention=meta_by_intervention,
        directional_eval_rows=directional_eval_rows,
        offset_pass_by_offset=offset_pass_by_offset,
        scope=scope,
    )
    offset_rows = _offset_summary_rows(scope_rows, eval_group_rows)
    failed_eval_groups = [
        row
        for row in eval_group_rows
        if str(row["offset_status"]) == "fail" and not _bool(row["all_rows_both_positive"])
    ]
    composition_rows = _composition_summary(eval_group_rows)
    result_class, recommended_next_step = classify_failed_offset_audit(
        failing_offsets=failing_offsets,
        composition_rows=composition_rows,
    )

    top_values: dict[str, Any] = {}
    for dimension in COMPOSITION_DIMENSIONS:
        value, share, count = _top_failed_share(composition_rows, dimension)
        top_values[f"top_failed_{dimension}"] = value
        top_values[f"top_failed_{dimension}_share"] = share
        top_values[f"top_failed_{dimension}_count"] = count

    write_csv_rows(run_dir / "offset_summary.csv", offset_rows)
    write_csv_rows(run_dir / "eval_directional_rows.csv", directional_eval_rows)
    write_csv_rows(run_dir / "eval_group_rows.csv", eval_group_rows)
    write_csv_rows(run_dir / "failed_eval_groups.csv", failed_eval_groups)
    write_csv_rows(run_dir / "composition_summary.csv", composition_rows)

    failed_group_min_margins = [_finite_float(row["group_min_margin"]) for row in failed_eval_groups]
    summary = {
        "run_type": "source_history_repeat_failed_offset_audit",
        "repeat_run_dir": repeat_run_dir,
        "history_run_dir": history_run_dir,
        "scope": scope,
        "offset_count": int(len(offset_pass_by_offset)),
        "passing_offset_count": int(len(passing_offsets)),
        "failing_offset_count": int(len(failing_offsets)),
        "passing_offsets": "|".join(str(offset) for offset in passing_offsets),
        "failing_offsets": "|".join(str(offset) for offset in failing_offsets),
        "eval_directional_row_count": int(len(directional_eval_rows)),
        "eval_group_count": int(len(eval_group_rows)),
        "failed_eval_group_count": int(len(failed_eval_groups)),
        "failed_eval_group_fraction": (
            float(len(failed_eval_groups) / len(eval_group_rows)) if eval_group_rows else 0.0
        ),
        "failed_eval_group_min_margin_mean": _mean(failed_group_min_margins),
        "failed_eval_group_min_margin_min": min(failed_group_min_margins) if failed_group_min_margins else 0.0,
        "failed_eval_group_min_margin_max": max(failed_group_min_margins) if failed_group_min_margins else 0.0,
        **top_values,
        "result_class": result_class,
        "recommended_next_step": recommended_next_step,
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "offset_summary_csv": run_dir / "offset_summary.csv",
        "eval_directional_rows_csv": run_dir / "eval_directional_rows.csv",
        "eval_group_rows_csv": run_dir / "eval_group_rows.csv",
        "failed_eval_groups_csv": run_dir / "failed_eval_groups.csv",
        "composition_summary_csv": run_dir / "composition_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit source-history repeat failed offsets without training.")
    parser.add_argument("--repeat-run-dir", type=Path, required=True)
    parser.add_argument("--history-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--scope", type=str, default="fusion_head")
    args = parser.parse_args()
    summary = run_failed_offset_audit(
        repeat_run_dir=args.repeat_run_dir,
        history_run_dir=args.history_run_dir,
        run_dir=args.run_dir,
        scope=args.scope,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
